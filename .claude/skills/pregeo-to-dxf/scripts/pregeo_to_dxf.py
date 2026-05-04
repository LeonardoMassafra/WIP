"""
Convertitore Libretto Pregeo -> DXF
Supporta rilievi GPS, celerimetrici e misti.

Input accettati:
  - File .dat (libretto nativo Pregeo)
  - File .pdf (Tipo Mappale/Frazionamento completo: estrae solo le pagine "Libretto delle misure")

Logica di conversione:
  - Riga 1 con 3 coord virgola -> stazione GPS base geocentrica (WGS84-ETRF2000)
  - Riga 2 con 3 coord virgola -> punto GPS (vettore geocentrico dalla base)
    -> trasformato in ENU locale sulla base
  - Riga 1 senza coord -> stazione celerimetrica
  - Riga 2 angolo|distanza|h_prisma -> battuta celerimetrica (angolo centesimali)
    -> calcolata dalla stazione (se gia' collocata in ENU usa quella, altrimenti origine locale)
  - Riga 7 -> polilinee (contorni)
  - Riga 8 id|X|Y|cod|desc -> punti con coord cartografiche Cassini-Soldner

Se tra i punti GPS e i punti riga-8 ci sono PF in comune (>=2), viene calcolata una
rototraslazione Helmert 4 parametri e tutti i punti vengono portati nel sistema catastale.

Uso:
    python pregeo_to_dxf.py <input.dat|.pdf> [output.dxf]
"""

import sys
import re
import math
from pathlib import Path

import ezdxf


# =========================================================================
# Estrazione righe libretto
# =========================================================================

RIGA_RE = re.compile(r'^([0-9])\|')

def _reunite_wrapped(raw_lines):
    """Ricostruisce righe del libretto spezzate dal rendering PDF.
    Una riga parte quando il testo inizia con 'N|' (N in 0..9).
    Le righe successive che non iniziano con N| vengono accodate se sembrano
    una continuazione (iniziano con cifra, punto, virgola o pipe).
    """
    out = []
    buf = None
    for line in raw_lines:
        s = line.strip()
        if not s:
            continue
        m = RIGA_RE.match(s)
        if m:
            if buf is not None:
                out.append(buf)
            buf = s
        elif buf is not None:
            # Continuazione probabile: inizia con cifra, punto, virgola, pipe, segno,
            # oppure parole tecniche tipiche (PDOP, RTK, WGS84, Spig., ecc.)
            if re.match(r'^[\d\.,\|\-\+]', s) or \
               any(s.startswith(k) for k in ('PDOP', 'RTK', 'WGS', 'Spig', 'PUNTO',
                                              'SPIGOLO', 'SPIG', 'A TERRA', 'Punto',
                                              '[WGS')):
                buf = buf + s
            else:
                # Probabile intestazione pagina / rumore -> chiudi la riga corrente
                out.append(buf)
                buf = None
    if buf is not None:
        out.append(buf)
    return out


def extract_lines_from_pdf(pdf_path):
    """Estrae le righe del libretto da un PDF Pregeo.
    Processa tutte le pagine e filtra via il boilerplate basandosi sul prefisso N|.
    Le entita' non-libretto (righe 7/8 di 'estratto di mappa', se presenti) fanno
    riferimento a punti che non esistono nelle misure, e vengono scartate a valle.
    """
    import fitz  # pymupdf
    doc = fitz.open(pdf_path)
    raw = []
    for page in doc:
        raw.extend(page.get_text("text").splitlines())
    doc.close()
    return _reunite_wrapped(raw)


def extract_lines_from_dat(dat_path):
    with open(dat_path, 'r', encoding='utf-8', errors='replace') as f:
        raw = [l.rstrip('\n') for l in f]
    return _reunite_wrapped(raw)


# =========================================================================
# Parser
# =========================================================================

class Libretto:
    def __init__(self):
        self.header = None
        self.tipologia = None
        self.stazioni_gps = []   # [{id,X,Y,Z,h_ant,desc}]
        self.stazioni_cel = []   # [{id,h_staz}]
        self.punti_gps = []      # [{id,base_idx,dX,dY,dZ,h_ant,desc}]
        self.battute_cel = []    # [{id,staz_idx,angolo,dist,h_prisma,desc}]
        self.punti_fissi = []    # [{id,X,Y,codice,desc}]
        self.collegamenti = []   # [{count,ids,tipo,extra}]
        self.allineamenti = []   # [{id,P1,P2,ascissa_cm,ordinata_m}]
        self._pending_riga4 = None

    def summary(self):
        return (f"  stazioni GPS base .... {len(self.stazioni_gps)}\n"
                f"  stazioni celerim. .... {len(self.stazioni_cel)}\n"
                f"  punti GPS rilevati ... {len(self.punti_gps)}\n"
                f"  battute celerim. ..... {len(self.battute_cel)}\n"
                f"  allineamenti/squadri . {len(self.allineamenti)}\n"
                f"  polilinee riga-7 ..... {len(self.collegamenti)}")


def _clean_parts(line):
    parts = line.split('|')
    # rimuovi eventuale campo vuoto finale dovuto al | di chiusura
    while parts and parts[-1] == '':
        parts.pop()
    return parts


def _try_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def parse_libretto(raw_lines):
    lib = Libretto()
    cur_base_idx = None
    cur_staz_idx = None

    for ln in raw_lines:
        parts = _clean_parts(ln)
        if not parts:
            continue
        tag = parts[0]

        if tag == '0':
            lib.header = parts[1:]

        elif tag == '9':
            lib.tipologia = parts[1:]

        elif tag == '1':
            if len(parts) < 3:
                continue
            id_ = parts[1]
            field2 = parts[2]
            # GPS base se 3 valori float separati da virgola
            if ',' in field2:
                nums = [_try_float(x) for x in field2.split(',')]
                if len(nums) == 3 and all(n is not None for n in nums):
                    X, Y, Z = nums
                    h_ant = _try_float(parts[3]) if len(parts) > 3 else None
                    lib.stazioni_gps.append({
                        'id': id_, 'X': X, 'Y': Y, 'Z': Z,
                        'h_ant': h_ant if h_ant is not None else 0.0,
                        'desc': parts[4] if len(parts) > 4 else '',
                    })
                    cur_base_idx = len(lib.stazioni_gps) - 1
                    continue
            # Stazione celerimetrica: solo se field2 e' numerico (altezza strumento)
            h_staz = _try_float(field2)
            if h_staz is None:
                continue
            lib.stazioni_cel.append({'id': id_, 'h_staz': h_staz})
            cur_staz_idx = len(lib.stazioni_cel) - 1

        elif tag == '2':
            if len(parts) < 3:
                continue
            id_ = parts[1]
            field2 = parts[2]
            # GPS: vettore geocentrico (3 valori separati da virgola nel campo 2)
            if ',' in field2:
                nums = [_try_float(x) for x in field2.split(',')]
                if len(nums) == 3 and all(n is not None for n in nums):
                    dX, dY, dZ = nums
                    h_ant = _try_float(parts[5]) if len(parts) > 5 else None
                    desc = parts[6] if len(parts) > 6 else ''
                    lib.punti_gps.append({
                        'id': id_, 'base_idx': cur_base_idx,
                        'dX': dX, 'dY': dY, 'dZ': dZ,
                        'h_ant': h_ant if h_ant is not None else 0.0,
                        'desc': desc,
                    })
                    continue
            # Celerimetrica: conta quanti campi numerici consecutivi partono da parts[2]
            numeric = []
            for p in parts[2:]:
                v = _try_float(p)
                if v is None:
                    break
                numeric.append(v)
            if not numeric:
                continue
            ang = numeric[0]
            zen = 100.0  # default orizzontale (grad centesimali)
            hp = 0.0
            if len(numeric) >= 4:
                # Forma lunga: az | zen | dist_inclinata | h_prisma
                zen = numeric[1]
                dist = numeric[2]
                hp = numeric[3]
                desc_idx = 6
            elif len(numeric) == 3:
                # Ambiguo: az|zen|dist (zen ~100) oppure az|dist|h_prisma
                # Heuristica: se numeric[1] tra 80-120 grad -> zenit
                if 80.0 <= numeric[1] <= 120.0:
                    zen = numeric[1]
                    dist = numeric[2]
                else:
                    dist = numeric[1]
                    hp = numeric[2]
                desc_idx = 5
            elif len(numeric) == 2:
                # Forma corta: az | dist_orizz
                dist = numeric[1]
                desc_idx = 4
            else:
                continue
            # Se zen != 100, riduci a distanza orizzontale
            if abs(zen - 100.0) > 0.01:
                dist_horiz = dist * math.sin(zen * math.pi / 200.0)
            else:
                dist_horiz = dist
            desc = parts[desc_idx] if len(parts) > desc_idx else ''
            lib.battute_cel.append({
                'id': id_, 'staz_idx': cur_staz_idx,
                'angolo': ang, 'dist': dist_horiz,
                'dist_incl': dist, 'zen': zen,
                'h_prisma': hp, 'desc': desc,
            })

        elif tag == '4':
            # Due forme:
            #  Lunga (allineamento-squadro): 4|P1|P2|DISLIVELLO_CM|*S*|
            #    DISLIVELLO = altezza dello spigolo rispetto al terreno (usato in 3D),
            #    IGNORATO per il DXF 2D.
            #  Corta (solo dislivello): 4|P|h|   -> ignorata.
            # La riga successiva (riga 5) fornisce la distanza RADIALE dal punto P1.
            if len(parts) >= 5:
                lib._pending_riga4 = {
                    'P1': parts[1], 'P2': parts[2],
                }
            else:
                lib._pending_riga4 = None

        elif tag == '5':
            # 5|ID|DISTANZA_M|DH|
            # DISTANZA = distanza radiale in metri dal punto P1 della riga 4.
            # Per determinare il punto in 2D serve la trilaterazione con due misure
            # reciproche (una da P1 verso P2, una da P2 verso P1).
            pending = lib._pending_riga4
            lib._pending_riga4 = None
            if pending is None or len(parts) < 3:
                continue
            pid = parts[1]
            dist = _try_float(parts[2])
            if dist is None or dist <= 0:
                continue
            lib.allineamenti.append({
                'id': pid,
                'P_ref': pending['P1'],  # punto dal quale si misura la distanza radiale
                'P_alt': pending['P2'],  # altro estremo del segmento di allineamento
                'distanza_m': dist,
            })

        elif tag == '7':
            # Polilinea: 7|N|p1|...|pk|TIPO|extra|
            # N = conteggio totale della polilinea (anche su piu' righe).
            # Una riga con N=0 continua la polilinea precedente.
            # La fine della lista di ID e' marcata da un TIPO alfabetico (RC/NC/RT/NT/...).
            if len(parts) < 3:
                continue
            n_claimed = _try_float(parts[1])
            if n_claimed is None:
                continue
            n_claimed = int(n_claimed)
            # Trova il TIPO: primo campo alfanumerico tutto maiuscolo (es. RC, NC, RT)
            tipo_idx = None
            for i in range(2, len(parts)):
                p = parts[i]
                if 1 <= len(p) <= 4 and p.isalpha() and p.isupper():
                    tipo_idx = i
                    break
            if tipo_idx is not None:
                ids_here = parts[2:tipo_idx]
                tipo = parts[tipo_idx]
                extra = parts[tipo_idx + 1:]
            else:
                # Continuazione senza TIPO: tutti dopo il count sono ID
                ids_here = parts[2:]
                tipo = ''
                extra = []
            if n_claimed == 0 and lib.collegamenti:
                # Continua la polilinea precedente
                lib.collegamenti[-1]['ids'].extend(ids_here)
                if tipo:
                    lib.collegamenti[-1]['tipo'] = tipo
                if extra:
                    lib.collegamenti[-1]['extra'] = extra
            else:
                lib.collegamenti.append({
                    'count': n_claimed,
                    'ids': list(ids_here),
                    'tipo': tipo,
                    'extra': extra,
                })

        # Riga 8: coordinate Cassini pre-calcolate dei PF.
        # IGNORATA di proposito: il DXF del libretto resta nel sistema locale ENU
        # del rilievo, senza rototraslazioni verso il sistema catastale.

    return lib


# =========================================================================
# Coordinate: ECEF -> geodetiche -> ENU locale
# =========================================================================

WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = 2 * WGS84_F - WGS84_F * WGS84_F


def ecef_to_geodetic(X, Y, Z):
    lon = math.atan2(Y, X)
    p = math.hypot(X, Y)
    lat = math.atan2(Z, p * (1 - WGS84_E2))
    for _ in range(10):
        sin_lat = math.sin(lat)
        N = WGS84_A / math.sqrt(1 - WGS84_E2 * sin_lat * sin_lat)
        h = p / math.cos(lat) - N
        lat_new = math.atan2(Z, p * (1 - WGS84_E2 * N / (N + h)))
        if abs(lat_new - lat) < 1e-12:
            lat = lat_new
            break
        lat = lat_new
    sin_lat = math.sin(lat)
    N = WGS84_A / math.sqrt(1 - WGS84_E2 * sin_lat * sin_lat)
    h = p / math.cos(lat) - N
    return lat, lon, h


def ecef_delta_to_enu(dX, dY, dZ, lat, lon):
    sl, cl = math.sin(lon), math.cos(lon)
    sp, cp = math.sin(lat), math.cos(lat)
    E = -sl * dX + cl * dY
    N = -sp * cl * dX - sp * sl * dY + cp * dZ
    U = cp * cl * dX + cp * sl * dY + sp * dZ
    return E, N, U


# =========================================================================
# Trasformazione affine 6 parametri (ENU -> foglio catastale Cassini-Soldner)
# In Pregeo la convenzione del "sistema foglio" ha X = Nord, Y = Est (riflessa).
# Un'affine 6 parametri gestisce sia Helmert puro sia swap/reflessione.
# =========================================================================

def _solve_linear(A, b):
    """Gauss-Jordan su AT A x = AT b (normali)."""
    n = len(A[0])  # incognite
    AtA = [[0.0] * n for _ in range(n)]
    Atb = [0.0] * n
    for row, bi in zip(A, b):
        for i in range(n):
            for j in range(n):
                AtA[i][j] += row[i] * row[j]
            Atb[i] += row[i] * bi
    M = [AtA[i][:] + [Atb[i]] for i in range(n)]
    for i in range(n):
        piv = i
        for r in range(i + 1, n):
            if abs(M[r][i]) > abs(M[piv][i]):
                piv = r
        M[i], M[piv] = M[piv], M[i]
        if abs(M[i][i]) < 1e-15:
            raise ValueError("Matrice singolare")
        inv = 1.0 / M[i][i]
        for c in range(n + 1):
            M[i][c] *= inv
        for r in range(n):
            if r == i:
                continue
            fac = M[r][i]
            for c in range(n + 1):
                M[r][c] -= fac * M[i][c]
    return [M[i][n] for i in range(n)]


def compute_affine(src_pts, dst_pts):
    """Affine 6-par: X' = a11*x + a12*y + tx ; Y' = a21*x + a22*y + ty.
    Minimi quadrati. Richiede almeno 3 punti.
    """
    if len(src_pts) < 3:
        raise ValueError("Servono almeno 3 punti in comune per l'affine")
    A = []
    bX = []
    bY = []
    for (x, y), (X, Y) in zip(src_pts, dst_pts):
        A.append([x, y, 1.0])
        bX.append(X)
        bY.append(Y)
    a11, a12, tx = _solve_linear(A, bX)
    a21, a22, ty = _solve_linear(A, bY)
    return (a11, a12, a21, a22, tx, ty)


def apply_affine(params, x, y):
    a11, a12, a21, a22, tx, ty = params
    return (a11 * x + a12 * y + tx, a21 * x + a22 * y + ty)


def affine_metrics(params):
    a11, a12, a21, a22, tx, ty = params
    det = a11 * a22 - a12 * a21
    # Singular value decomposition approx: scale = sqrt(|det|), shear ~ dev from orthogonality
    sx = math.hypot(a11, a21)
    sy = math.hypot(a12, a22)
    # angolo tra i due vettori colonna
    cos_th = (a11 * a12 + a21 * a22) / (sx * sy) if sx * sy > 0 else 0
    non_ortho = math.degrees(math.acos(max(-1, min(1, abs(cos_th)))))
    rotation = math.degrees(math.atan2(a21, a11))
    return {
        'det': det,
        'scala_x': sx, 'scala_y': sy,
        'rotazione_deg': rotation,
        'non_ortogonalita_deg': non_ortho,
        'riflessione': det < 0,
    }


# =========================================================================
# Calcolo coordinate finali di tutti i punti
# =========================================================================

def compute_coordinates(lib):
    coords = {}  # id -> {'x','y','z','source','desc'}

    # --- 1) GPS: vettori geocentrici -> ENU sul primo base ---
    if lib.stazioni_gps:
        base0 = lib.stazioni_gps[0]
        lat0, lon0, _ = ecef_to_geodetic(base0['X'], base0['Y'], base0['Z'])

        # Posizione base0 in ENU = (0,0,0) per definizione
        coords[base0['id']] = {'x': 0.0, 'y': 0.0, 'z': 0.0,
                               'source': 'BASE', 'desc': base0.get('desc', '')}

        for pt in lib.punti_gps:
            if pt['base_idx'] is not None and pt['base_idx'] < len(lib.stazioni_gps):
                base = lib.stazioni_gps[pt['base_idx']]
            else:
                base = base0
            dX_glob = (base['X'] - base0['X']) + pt['dX']
            dY_glob = (base['Y'] - base0['Y']) + pt['dY']
            dZ_glob = (base['Z'] - base0['Z']) + pt['dZ']
            E, N, U = ecef_delta_to_enu(dX_glob, dY_glob, dZ_glob, lat0, lon0)
            coords[pt['id']] = {'x': E, 'y': N, 'z': U,
                                'source': 'GPS', 'desc': pt.get('desc', '')}

    # --- 2) Celerimetrica ---
    # Per ogni stazione totale calcoliamo la correzione di orientamento alpha
    # usando una battuta verso un punto GPS gia' collocato (tipico rilievo misto:
    # stazione appoggiata su chiodo GPS, prima battuta su un altro chiodo GPS).
    # Nel celerimetrico puro alpha=0 (orientamento Nord assunto).
    orient_info = []
    for staz_idx, staz in enumerate(lib.stazioni_cel):
        # Coordinate della stazione
        if staz['id'] in coords:
            xs, ys = coords[staz['id']]['x'], coords[staz['id']]['y']
            station_known = True
        else:
            xs, ys = 0.0, 0.0
            station_known = False
            coords.setdefault(staz['id'], {'x': 0.0, 'y': 0.0, 'z': 0.0,
                                           'source': 'STAZ', 'desc': ''})

        shots = [b for b in lib.battute_cel if b['staz_idx'] == staz_idx]

        # Calcolo alpha: scegli la battuta piu' lunga verso un punto GPS noto
        alpha = 0.0
        alpha_ref = None
        best_dist = 0.0
        for sh in shots:
            tid = sh['id']
            if tid not in coords:
                continue
            if coords[tid].get('source') not in ('GPS', 'BASE'):
                continue
            tx, ty = coords[tid]['x'], coords[tid]['y']
            dx, dy = tx - xs, ty - ys
            true_d = math.hypot(dx, dy)
            if true_d < 0.5:
                continue
            true_bearing = math.atan2(dx, dy) * 200.0 / math.pi
            if true_bearing < 0:
                true_bearing += 400.0
            measured_az = sh['angolo'] % 400.0
            a_cand = (true_bearing - measured_az) % 400.0
            if true_d > best_dist:
                best_dist = true_d
                alpha = a_cand
                alpha_ref = tid

        orient_info.append({
            'stazione': staz['id'],
            'staz_gps': station_known,
            'alpha_grad': alpha,
            'ref': alpha_ref,
            'ref_dist': best_dist,
            'n_battute': len(shots),
        })

        # Applica alpha e calcola le coordinate dei punti non noti
        for sh in shots:
            if sh['id'] in coords and coords[sh['id']].get('source') in ('GPS', 'BASE'):
                continue  # punto gia' collocato dal GPS
            az_corr = (sh['angolo'] + alpha) % 400.0
            ang_rad = az_corr * math.pi / 200.0
            xp = xs + sh['dist'] * math.sin(ang_rad)
            yp = ys + sh['dist'] * math.cos(ang_rad)
            coords[sh['id']] = {
                'x': xp, 'y': yp, 'z': 0.0,
                'source': 'CEL', 'desc': sh.get('desc', ''),
                'from_station': staz['id'],
            }

    # --- 3) Punti da allineamento-squadro (righe 4/5) ---
    # Interpretazione Pregeo (verificata su PF12 del libretto Bovolone, scarto 6 mm):
    #   Ogni coppia riga 4 + riga 5 fornisce la DISTANZA RADIALE (in metri, riga 5)
    #   dal punto P1 della riga 4 al punto nuovo da calcolare.
    #   Due misure reciproche (da P1 e da P2 dello stesso segmento) consentono la
    #   TRILATERAZIONE in 2D -> 2 soluzioni simmetriche rispetto alla linea.
    # Per scegliere il lato corretto (LEFT/RIGHT) usiamo il contesto della polilinea
    # in cui il nuovo punto e' incluso: la svolta al punto X deve essere CONCAVA
    # (LEFT turn per polilinea CW, RIGHT turn per polilinea CCW). I punti calcolati
    # da allineamento-squadro sono tipicamente indentazioni (corner interne).
    def _trilatera(Pa, Pb, ra, rb):
        dx, dy = Pb[0] - Pa[0], Pb[1] - Pa[1]
        d = math.hypot(dx, dy)
        if d < 1e-9:
            return None, None
        if ra + rb < d - 1e-6 or abs(ra - rb) > d + 1e-6:
            return None, None
        ux, uy = dx / d, dy / d
        x = (ra * ra - rb * rb + d * d) / (2.0 * d)
        y2 = ra * ra - x * x
        if y2 < 0:
            y2 = 0.0
        y = math.sqrt(y2)
        pxL, pyL = -uy, ux
        left = (Pa[0] + x * ux + y * pxL, Pa[1] + x * uy + y * pyL)
        right = (Pa[0] + x * ux - y * pxL, Pa[1] + x * uy - y * pyL)
        return left, right

    def _signed_area(verts):
        """Area con segno (Shoelace). Positiva = CCW, negativa = CW."""
        s = 0.0
        n = len(verts)
        for i in range(n):
            xi, yi = verts[i]
            xj, yj = verts[(i + 1) % n]
            s += xi * yj - xj * yi
        return s / 2.0

    def _find_polyline_neighbors(pid):
        """Per ogni polilinea riga-7 che contiene pid, ritorna (ids_sequence, index_of_pid)."""
        results = []
        for coll in lib.collegamenti:
            ids = coll['ids']
            if pid in ids:
                results.append((ids, ids.index(pid)))
        return results

    def _pick_side(pid, left, right):
        """Sceglie LEFT o RIGHT in base al contesto della polilinea."""
        contexts = _find_polyline_neighbors(pid)
        for ids, idx in contexts:
            # Determina i vicini (ciclico se chiusa, altrimenti lineare)
            n = len(ids)
            prev_id = ids[(idx - 1) % n] if n > 1 else None
            next_id = ids[(idx + 1) % n] if n > 1 else None
            # Se prev/next sono noti in coords (escludendo nuovi punti ALL):
            if prev_id in coords and next_id in coords:
                A = (coords[prev_id]['x'], coords[prev_id]['y'])
                B = (coords[next_id]['x'], coords[next_id]['y'])
                # Orientamento globale della polilinea (usando solo vertici noti)
                known_verts = [(coords[q]['x'], coords[q]['y'])
                               for q in ids if q in coords]
                if len(known_verts) < 3:
                    continue
                area_sign = _signed_area(known_verts)
                # Svolta locale a X: cross((X-A), (B-X))
                def turn_cross(X):
                    ax, ay = X[0] - A[0], X[1] - A[1]
                    bx, by = B[0] - X[0], B[1] - X[1]
                    return ax * by - ay * bx
                cL = turn_cross(left)
                cR = turn_cross(right)
                # Per polilinea CW (area_sign < 0), una indentazione concava = LEFT turn (cross > 0)
                # Per polilinea CCW (area_sign > 0), indentazione concava = RIGHT turn (cross < 0)
                want_positive = (area_sign < 0)
                if (cL > 0) == want_positive and (cR > 0) != want_positive:
                    return left, f"polilinea {ids[0]}.. (concava)"
                if (cR > 0) == want_positive and (cL > 0) != want_positive:
                    return right, f"polilinea {ids[0]}.. (concava)"
                # Se entrambi o nessuno soddisfa il criterio, scegli la svolta piu' accentuata
                if want_positive:
                    return (left, "polilinea fallback L") if cL > cR else (right, "polilinea fallback R")
                else:
                    return (left, "polilinea fallback L") if cL < cR else (right, "polilinea fallback R")
        # Nessun contesto polilinea: default LEFT
        return left, "default LEFT"

    by_id = {}
    for a in lib.allineamenti:
        by_id.setdefault(a['id'], []).append(a)

    all_count_ok = 0
    all_count_missing_base = 0
    all_count_insufficient = 0
    for pid, group in by_id.items():
        if pid in coords:
            continue  # gia' noto (GPS/CEL): la riga 4/5 e' misura di controllo
        usable = [a for a in group
                  if a['P_ref'] in coords and a['P_alt'] in coords]
        if not usable:
            all_count_missing_base += 1
            continue
        # Trova coppia reciproca
        chosen = None
        for i, a1 in enumerate(usable):
            for a2 in usable[i + 1:]:
                if a1['P_ref'] == a2['P_alt'] and a1['P_alt'] == a2['P_ref']:
                    chosen = (a1, a2)
                    break
            if chosen:
                break
        if not chosen:
            seen = set()
            picks = []
            for a in usable:
                if a['P_ref'] not in seen:
                    picks.append(a)
                    seen.add(a['P_ref'])
                if len(picks) == 2:
                    break
            if len(picks) == 2:
                chosen = (picks[0], picks[1])
        if not chosen:
            all_count_insufficient += 1
            continue
        a1, a2 = chosen
        if a1['P_ref'] > a2['P_ref']:
            a1, a2 = a2, a1
        Pa = (coords[a1['P_ref']]['x'], coords[a1['P_ref']]['y'])
        Pb = (coords[a2['P_ref']]['x'], coords[a2['P_ref']]['y'])
        left, right = _trilatera(Pa, Pb, a1['distanza_m'], a2['distanza_m'])
        if left is None:
            all_count_insufficient += 1
            continue
        chosen_pt, side_reason = _pick_side(pid, left, right)
        coords[pid] = {
            'x': chosen_pt[0], 'y': chosen_pt[1], 'z': 0.0,
            'source': 'ALL',
            'desc': f"trilaterazione {a1['P_ref']}-{a2['P_ref']} [{side_reason}]",
        }
        all_count_ok += 1

    info = {'orient_info': orient_info} if orient_info else {}
    info['allineamenti_ok'] = all_count_ok
    info['allineamenti_no_base'] = all_count_missing_base
    info['allineamenti_insufficient'] = all_count_insufficient
    return coords, False, info if info else None


# =========================================================================
# Scrittura DXF
# =========================================================================

LAYER_COLORS = {
    'PREGEO_BASE_GPS':     6,   # magenta
    'PREGEO_PUNTI_GPS':    3,   # verde
    'PREGEO_PUNTI_CEL':    5,   # blu
    'PREGEO_PUNTI_FISSI':  1,   # rosso
    'PREGEO_PUNTI_PF':     1,   # rosso
    'PREGEO_PUNTI_ALL':    6,   # magenta (allineamento-squadro)
    'PREGEO_STAZIONI':     2,   # giallo
    'PREGEO_CONTORNI':     4,   # ciano
    'PREGEO_ETICHETTE':    7,   # bianco
    'PREGEO_VETTORI_GPS':  8,   # grigio
    'PREGEO_BATTUTE_CEL':  9,   # grigio chiaro
}


def _choose_symbol_size(coords):
    """Dimensiona simboli/etichette in base ai punti del rilievo (escludendo BASE)."""
    filtered = [p for p in coords.values() if p.get('source') != 'BASE']
    if not filtered:
        return 0.3, 0.6
    xs = [p['x'] for p in filtered]
    ys = [p['y'] for p in filtered]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    diag = max(math.hypot(w, h), 1.0)
    # Simboli piccoli: adatti alle scale cadastrali 1:500..1:2000
    r = min(max(diag * 0.0015, 0.10), 0.5)
    t = min(max(diag * 0.003, 0.20), 1.0)
    return r, t


def write_dxf(lib, coords, cad_frame, helmert_info, output_path):
    doc = ezdxf.new('R2010', setup=True)
    msp = doc.modelspace()

    for name, color in LAYER_COLORS.items():
        if name not in doc.layers:
            doc.layers.add(name=name, color=color)

    r_sym, h_txt = _choose_symbol_size(coords)

    def pick_layer(p, pid):
        src = p.get('source', '')
        if pid.startswith('PF'):
            return 'PREGEO_PUNTI_PF'
        if src == 'BASE':
            return 'PREGEO_BASE_GPS'
        if src == 'FIX':
            return 'PREGEO_PUNTI_FISSI'
        if src == 'CEL':
            return 'PREGEO_PUNTI_CEL'
        if src == 'STAZ':
            return 'PREGEO_STAZIONI'
        if src == 'ALL':
            return 'PREGEO_PUNTI_ALL'
        return 'PREGEO_PUNTI_GPS'

    # --- Punti ---
    for pid, p in coords.items():
        layer = pick_layer(p, pid)
        x, y = p['x'], p['y']
        msp.add_point((x, y), dxfattribs={'layer': layer})
        msp.add_circle((x, y), radius=r_sym, dxfattribs={'layer': layer})
        msp.add_text(
            pid, height=h_txt,
            dxfattribs={'layer': 'PREGEO_ETICHETTE'},
        ).set_placement((x + r_sym * 1.5, y + r_sym * 1.5))

    # --- Vettori GPS dalla base (solo se siamo in ENU, non catastale) ---
    if lib.stazioni_gps and not cad_frame:
        base_id = lib.stazioni_gps[0]['id']
        if base_id in coords:
            bx, by = coords[base_id]['x'], coords[base_id]['y']
            for pt in lib.punti_gps:
                if pt['id'] in coords:
                    p = coords[pt['id']]
                    msp.add_line((bx, by), (p['x'], p['y']),
                                 dxfattribs={'layer': 'PREGEO_VETTORI_GPS'})

    # --- Raggi celerimetrici dalla stazione ---
    for bat in lib.battute_cel:
        if bat['staz_idx'] is None:
            continue
        staz = lib.stazioni_cel[bat['staz_idx']]
        if staz['id'] in coords and bat['id'] in coords:
            s = coords[staz['id']]
            p = coords[bat['id']]
            msp.add_line((s['x'], s['y']), (p['x'], p['y']),
                         dxfattribs={'layer': 'PREGEO_BATTUTE_CEL'})

    # --- Polilinee (riga 7) ---
    for coll in lib.collegamenti:
        pts = [(coords[pid]['x'], coords[pid]['y'])
               for pid in coll['ids'] if pid in coords]
        if len(pts) >= 2:
            # chiusa se primo==ultimo
            closed = (len(pts) >= 3 and pts[0] == pts[-1])
            msp.add_lwpolyline(
                pts, close=closed,
                dxfattribs={'layer': 'PREGEO_CONTORNI'},
            )

    # --- Info nel DXF come testo (riquadro info) ---
    info_lines = []
    info_lines.append("LIBRETTO PREGEO -> DXF")
    if lib.tipologia:
        info_lines.append(f"Tipologia: {'|'.join(lib.tipologia)}")
    info_lines.append("Sistema: ENU locale (X=Est, Y=Nord, origine=base GPS)")
    # In alto a sinistra rispetto al bbox
    if coords:
        xs = [p['x'] for p in coords.values()]
        ys = [p['y'] for p in coords.values()]
        x0 = min(xs)
        y0 = max(ys) + h_txt * 3
        for i, line in enumerate(info_lines):
            msp.add_text(
                line, height=h_txt,
                dxfattribs={'layer': 'PREGEO_ETICHETTE'},
            ).set_placement((x0, y0 + i * h_txt * 1.8))

    doc.saveas(output_path)


# =========================================================================
# Main
# =========================================================================

def main(argv):
    if len(argv) < 2:
        print(__doc__)
        print("ERRORE: specifica il file di input.")
        sys.exit(1)

    input_path = Path(argv[1])
    if not input_path.exists():
        print(f"ERRORE: file non trovato: {input_path}")
        sys.exit(1)

    output_path = Path(argv[2]) if len(argv) > 2 else input_path.with_suffix('.dxf')

    print(f"Input:  {input_path.name}")
    ext = input_path.suffix.lower()
    if ext == '.pdf':
        raw = extract_lines_from_pdf(str(input_path))
    else:
        raw = extract_lines_from_dat(str(input_path))
    print(f"Righe libretto estratte: {len(raw)}")

    lib = parse_libretto(raw)
    print("Parsing:")
    print(lib.summary())

    coords, cad_frame, hinfo = compute_coordinates(lib)
    print(f"Punti calcolati: {len(coords)}")
    print("Sistema di riferimento: ENU locale (X=Est, Y=Nord, origine=base GPS)")
    if hinfo and hinfo.get('orient_info'):
        for o in hinfo['orient_info']:
            ref = f"ref={o['ref']} a {o['ref_dist']:.1f}m" if o['ref'] else "nessun riferimento GPS"
            staz_k = "GPS-nota" if o['staz_gps'] else "origine arbitraria"
            print(f"  Staz {o['stazione']:8s}  ({staz_k})  alpha={o['alpha_grad']:.4f} grad  {ref}  battute={o['n_battute']}")
    if hinfo and hinfo.get('allineamenti_ok', 0) + hinfo.get('allineamenti_no_base', 0) + hinfo.get('allineamenti_insufficient', 0) > 0:
        print(f"  Punti da allineamento-squadro: {hinfo.get('allineamenti_ok', 0)} calcolati, "
              f"{hinfo.get('allineamenti_no_base', 0)} senza basi, "
              f"{hinfo.get('allineamenti_insufficient', 0)} misure insufficienti")

    write_dxf(lib, coords, cad_frame, hinfo, str(output_path))
    print(f"Output: {output_path.name}  OK ({output_path.stat().st_size} bytes)")


if __name__ == '__main__':
    main(sys.argv)
