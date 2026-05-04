#!/usr/bin/env python3
"""
merge_to_kml.py - Unisce PF da più DXF (Gauss-Boaga e/o UTM 32N) in un KML unico.

Rileva automaticamente il sistema di coordinate di ogni DXF.
Applica la correzione GPS calcolata su un PF di riferimento a tutti i fogli.

Uso:
  python merge_to_kml.py \
    --dxf foglio4.dxf foglio_utm.dxf foglio5.dxf \
    --ref-dxf foglio4.dxf \
    --ref-pf "PF 3" \
    --ref-lat 45.330688 \
    --ref-lon 11.007967 \
    --output merged_pf.kml
"""

import argparse
import math
import re
import sys
from pathlib import Path

# Forza UTF-8 sul terminale Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ─── WGS84 ────────────────────────────────────────────────────────────────────
A_WGS = 6378137.0
F_WGS = 1.0 / 298.257223563
E2_WGS = 2 * F_WGS - F_WGS ** 2

# ─── Hayford (Roma40 / Gauss-Boaga) ───────────────────────────────────────────
A_HAY = 6378388.0
F_HAY = 1.0 / 297.0
E2_HAY = 2 * F_HAY - F_HAY ** 2

# ─── Gauss-Boaga Ovest ────────────────────────────────────────────────────────
GB_K0   = 0.9996
GB_LON0 = math.radians(9.0)
GB_FE   = 1_500_000.0

# ─── Helmert Roma40 -> WGS84 (EPSG:1074) ──────────────────────────────────────
H_DX, H_DY, H_DZ = -104.1, -49.1, -9.9
H_RX = math.radians(0.886 / 3600)
H_RY = math.radians(-0.539 / 3600)
H_RZ = math.radians(0.679 / 3600)
H_S  = -1.052e-6

# ─── UTM 32N ──────────────────────────────────────────────────────────────────
UTM_K0   = 0.9996
UTM_LON0 = math.radians(9.0)
UTM_FE   = 500_000.0
UTM_FN   = 0.0


# ══════════════════════════════════════════════════════════════════════════════
# CONVERSIONI
# ══════════════════════════════════════════════════════════════════════════════

def _tm_inverse(east, north, a, e2, k0, lon0, fe, fn):
    """Inversa Transverse Mercator generica -> (lat_rad, lon_rad) sull'ellissoide dato."""
    x = east - fe
    y = north - fn
    M = y / k0
    mu = M / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu
            + (3*e1/2 - 27*e1**3/32)    * math.sin(2*mu)
            + (21*e1**2/16 - 55*e1**4/32) * math.sin(4*mu)
            + (151*e1**3/96)             * math.sin(6*mu)
            + (1097*e1**4/512)           * math.sin(8*mu))
    sp1, cp1, tp1 = math.sin(phi1), math.cos(phi1), math.tan(phi1)
    N1 = a / math.sqrt(1 - e2 * sp1**2)
    T1 = tp1**2
    C1 = (e2 / (1 - e2)) * cp1**2
    R1 = a * (1 - e2) / (1 - e2 * sp1**2)**1.5
    D  = x / (N1 * k0)
    lat = (phi1
           - (N1 * tp1 / R1) * (
               D**2/2
               - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*e2/(1-e2)) * D**4/24
               + (61 + 90*T1 + 298*C1 + 45*T1**2
                  - 252*e2/(1-e2) - 3*C1**2) * D**6/720))
    lon = lon0 + (D
                  - (1 + 2*T1 + C1) * D**3/6
                  + (5 - 2*C1 + 28*T1 - 3*C1**2
                     + 8*e2/(1-e2) + 24*T1**2) * D**5/120) / cp1
    return lat, lon


def _ecef_to_wgs84(X, Y, Z):
    """Cartesiane geocentriche -> lat/lon WGS84 (radianti)."""
    p   = math.sqrt(X**2 + Y**2)
    lon = math.atan2(Y, X)
    lat = math.atan2(Z, p * (1 - E2_WGS))
    for _ in range(10):
        sl  = math.sin(lat)
        N   = A_WGS / math.sqrt(1 - E2_WGS * sl**2)
        lat = math.atan2(Z + E2_WGS * N * sl, p)
    return lat, lon


def gb_to_wgs84(east, north):
    """Gauss-Boaga Ovest (EPSG:3003) -> WGS84 gradi decimali."""
    lat_r, lon_r = _tm_inverse(east, north, A_HAY, E2_HAY,
                                GB_K0, GB_LON0, GB_FE, 0.0)
    sl, cl = math.sin(lat_r), math.cos(lat_r)
    sl2, cl2 = math.sin(lon_r), math.cos(lon_r)
    N = A_HAY / math.sqrt(1 - E2_HAY * sl**2)
    Xr = N * cl * cl2
    Yr = N * cl * sl2
    Zr = N * (1 - E2_HAY) * sl
    Xw = H_DX + (1 + H_S) * ( Xr + H_RZ*Yr - H_RY*Zr)
    Yw = H_DY + (1 + H_S) * (-H_RZ*Xr + Yr  + H_RX*Zr)
    Zw = H_DZ + (1 + H_S) * ( H_RY*Xr - H_RX*Yr + Zr)
    lat, lon = _ecef_to_wgs84(Xw, Yw, Zw)
    return math.degrees(lat), math.degrees(lon)


def utm32n_to_wgs84(east, north):
    """UTM Zone 32N (EPSG:32632) -> WGS84 gradi decimali (diretta su WGS84)."""
    lat_r, lon_r = _tm_inverse(east, north, A_WGS, E2_WGS,
                                UTM_K0, UTM_LON0, UTM_FE, UTM_FN)
    return math.degrees(lat_r), math.degrees(lon_r)


def detect_crs(east):
    """Rileva il sistema di coordinate dal valore dell'easting."""
    if east > 1_400_000:
        return "gauss_boaga"   # ~1,600,000-1,750,000
    elif east > 400_000:
        return "utm32n"        # ~600,000-750,000
    else:
        return "unknown"


def to_wgs84(east, north, crs):
    if crs == "gauss_boaga":
        return gb_to_wgs84(east, north)
    elif crs == "utm32n":
        return utm32n_to_wgs84(east, north)
    else:
        raise ValueError(f"Sistema di coordinate non riconosciuto (east={east})")


# ══════════════════════════════════════════════════════════════════════════════
# PARSING DXF
# ══════════════════════════════════════════════════════════════════════════════

def parse_pf_from_dxf(dxf_path):
    """
    Estrae i PF dal layer FIDUCIALI di un DXF catastale.
    Restituisce lista di {'name', 'number', 'east', 'north'}.
    """
    with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f]

    pf_map = {}
    in_entities = False
    i = 0

    while i < len(lines):
        code  = lines[i].strip()
        value = lines[i+1].strip() if i+1 < len(lines) else ''

        if code == '0' and value == 'SECTION':
            if i+3 < len(lines) and lines[i+2].strip() == '2' and lines[i+3].strip() == 'ENTITIES':
                in_entities = True
            i += 2; continue

        if code == '0' and value == 'ENDSEC':
            in_entities = False
            i += 2; continue

        if not in_entities:
            i += 2; continue

        if code == '0' and value in ('TEXT', 'MTEXT'):
            ent = {'layer': '', 'x': None, 'y': None, 'text': ''}
            i += 2
            while i < len(lines):
                c = lines[i].strip()
                v = lines[i+1].strip() if i+1 < len(lines) else ''
                if c == '0': break
                if   c == '8':  ent['layer']  = v
                elif c == '10':
                    try: ent['x'] = float(v)
                    except ValueError: pass
                elif c == '20':
                    try: ent['y'] = float(v)
                    except ValueError: pass
                elif c == '1':  ent['text']   = v
                elif c == '3':  ent['text']  += v
                i += 2

            if 'FIDUCIALI' not in ent['layer'].upper():
                continue
            if ent['x'] is None or not ent['text']:
                continue

            t = ent['text'].strip()
            num_str = t[2:].strip() if t.upper().startswith('PF') else re.sub(r'[^\d]', '', t)
            if not num_str.isdigit():
                continue

            num = int(num_str)
            key = (round(ent['x'], 1), round(ent['y'], 1))
            pf_map[key] = {'name': f'PF {num}', 'number': num,
                           'east': ent['x'], 'north': ent['y']}
        else:
            i += 2

    return sorted(pf_map.values(), key=lambda p: p['number'])


# ══════════════════════════════════════════════════════════════════════════════
# FILTRO PRIMO PERIMETRO
# ══════════════════════════════════════════════════════════════════════════════

def find_mappale_centroid_wgs84(dxf_path, mappale, crs, d_lat, d_lon):
    """
    Cerca il testo del mappale nel layer PARTICELLE del DXF.
    Restituisce (lat, lon) WGS84 corretto con l'offset GPS, o None.
    """
    with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f]

    mappale_norm = mappale.strip().lstrip('0') or '0'
    candidates = []
    in_entities = False
    i = 0

    while i < len(lines):
        code  = lines[i].strip()
        value = lines[i+1].strip() if i+1 < len(lines) else ''

        if code == '0' and value == 'SECTION':
            if i+3 < len(lines) and lines[i+2].strip() == '2' and lines[i+3].strip() == 'ENTITIES':
                in_entities = True
            i += 2; continue
        if code == '0' and value == 'ENDSEC':
            in_entities = False; i += 2; continue
        if not in_entities:
            i += 2; continue

        if code == '0' and value in ('TEXT', 'MTEXT'):
            ent = {'layer': '', 'x': None, 'y': None, 'text': ''}
            i += 2
            while i < len(lines):
                c = lines[i].strip()
                v = lines[i+1].strip() if i+1 < len(lines) else ''
                if c == '0': break
                if   c == '8':  ent['layer']  = v
                elif c == '10':
                    try: ent['x'] = float(v)
                    except ValueError: pass
                elif c == '20':
                    try: ent['y'] = float(v)
                    except ValueError: pass
                elif c == '1':  ent['text']   = v
                elif c == '3':  ent['text']  += v
                i += 2

            if 'PARTICELLE' not in ent['layer'].upper(): continue
            if ent['x'] is None or not ent['text']: continue

            text_norm = re.sub(r'[A-Za-z/].*$', '', ent['text'].strip()).lstrip('0') or '0'
            if text_norm == mappale_norm:
                candidates.append((ent['x'], ent['y']))
        else:
            i += 2

    if not candidates:
        return None

    cx = sum(c[0] for c in candidates) / len(candidates)
    cy = sum(c[1] for c in candidates) / len(candidates)

    lat_approx, lon_approx = to_wgs84(cx, cy, crs)
    return lat_approx + d_lat, lon_approx + d_lon


def angular_gap(centroid_lat, centroid_lon, pf_list):
    """Restituisce il gap angolare massimo (gradi) tra i PF intorno al centroide."""
    cos_lat = math.cos(math.radians(centroid_lat))
    angles = sorted(
        math.degrees(math.atan2(
            pf['lat'] - centroid_lat,
            (pf['lon'] - centroid_lon) * cos_lat
        )) % 360
        for pf in pf_list
    )
    if not angles:
        return 360.0
    gaps = []
    for i in range(len(angles)):
        gap = angles[(i+1) % len(angles)] - angles[i]
        if gap <= 0: gap += 360
        gaps.append(gap)
    return max(gaps)


def find_enclosing_pfs(centroid_lat, centroid_lon, all_pfs):
    """
    Restituisce il set minimo di PF che racchiude il centroide.
    Aggiunge PF dal piu' vicino in poi finche' gap angolare < 180 gradi.
    """
    cos_lat = math.cos(math.radians(centroid_lat))
    m_lat = 111320
    m_lon = 111320 * cos_lat

    pfs_sorted = sorted(
        all_pfs,
        key=lambda p: math.sqrt(
            ((p['lat'] - centroid_lat) * m_lat) ** 2 +
            ((p['lon'] - centroid_lon) * m_lon) ** 2
        )
    )

    selected = []
    for pf in pfs_sorted:
        selected.append(pf)
        if len(selected) >= 3 and angular_gap(centroid_lat, centroid_lon, selected) < 180.0:
            return selected

    return pfs_sorted


# ══════════════════════════════════════════════════════════════════════════════
# KML
# ══════════════════════════════════════════════════════════════════════════════

def generate_kml(pf_list, output_path, title="Punti Fiduciali"):
    placemarks = ""
    for pf in pf_list:
        placemarks += f"""  <Placemark>
    <name>{pf['name']} ({pf['foglio']})</name>
    <description>Foglio: {pf['foglio']}
Sistema orig.: {pf['crs']}
Coord. orig.: E={pf['east']:.3f}, N={pf['north']:.3f}
WGS84 corretto: {pf['lat']:.6f} gradiN, {pf['lon']:.6f} gradiE</description>
    <styleUrl>#pf_style</styleUrl>
    <Point>
      <coordinates>{pf['lon']:.6f},{pf['lat']:.6f},0</coordinates>
    </Point>
  </Placemark>\n"""

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>{title}</name>
  <Style id="pf_style">
    <IconStyle>
      <color>ff0000ff</color>
      <scale>1.2</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LabelStyle><scale>1.2</scale></LabelStyle>
  </Style>
{placemarks}</Document>
</kml>"""

    Path(output_path).write_text(kml, encoding='utf-8')


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Unisce PF da più DXF (Gauss-Boaga/UTM 32N) in un KML unico con correzione GPS.'
    )
    parser.add_argument('--dxf', nargs='+', required=True,
                        help='Uno o più file DXF da elaborare')
    parser.add_argument('--ref-dxf', required=True,
                        help='DXF contenente il PF di riferimento GPS')
    parser.add_argument('--ref-pf', required=True,
                        help='Nome del PF di riferimento (es. "PF 3")')
    parser.add_argument('--ref-lat', type=float, required=True,
                        help='Latitudine GPS del PF di riferimento')
    parser.add_argument('--ref-lon', type=float, required=True,
                        help='Longitudine GPS del PF di riferimento')
    parser.add_argument('--output', default='merged_pf.kml',
                        help='File KML di output (default: merged_pf.kml)')
    parser.add_argument('--mappale', '-m',
                        help='Numero mappale: filtra solo i PF di primo perimetro (es. 206)')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Merge PF - {len(args.dxf)} DXF -> KML unico")
    print(f"{'='*60}")

    # ── Step 1: Leggi tutti i DXF ─────────────────────────────────────────────
    all_pfs = []
    ref_pf_approx = None

    for dxf_path in args.dxf:
        path = Path(dxf_path)
        if not path.exists():
            print(f"  ERRORE: file non trovato: {dxf_path}", file=sys.stderr)
            sys.exit(1)

        pfs = parse_pf_from_dxf(dxf_path)
        if not pfs:
            print(f"  AVVISO: nessun PF trovato in {path.name}")
            continue

        # Rileva CRS dal primo PF
        crs = detect_crs(pfs[0]['east'])
        foglio = path.stem  # usa il nome file come identificativo foglio

        print(f"\n  {path.name}: {len(pfs)} PF trovati - sistema: {crs.upper()}")

        for pf in pfs:
            pf['crs'] = crs
            pf['foglio'] = foglio
            try:
                lat_approx, lon_approx = to_wgs84(pf['east'], pf['north'], crs)
            except ValueError as e:
                print(f"    AVVISO: {e}")
                continue
            pf['lat_approx'] = lat_approx
            pf['lon_approx'] = lon_approx
            print(f"    {pf['name']}: {lat_approx:.5f} gradiN, {lon_approx:.5f} gradiE (approx)")

            # Cerca il PF di riferimento nel DXF di riferimento
            if (Path(dxf_path).resolve() == Path(args.ref_dxf).resolve()
                    and pf['name'].strip().lower() == args.ref_pf.strip().lower()):
                ref_pf_approx = pf

            all_pfs.append(pf)

    if not all_pfs:
        print("\n  ERRORE: nessun PF trovato in nessun DXF.", file=sys.stderr)
        sys.exit(1)

    # ── Step 2: Calcola offset GPS ────────────────────────────────────────────
    if ref_pf_approx is None:
        print(f"\n  ERRORE: '{args.ref_pf}' non trovato in {args.ref_dxf}.", file=sys.stderr)
        print(f"  PF disponibili in quel file: "
              f"{[p['name'] for p in all_pfs if Path(p.get('foglio','')+'.dxf').stem == Path(args.ref_dxf).stem]}",
              file=sys.stderr)
        sys.exit(1)

    d_lat = args.ref_lat - ref_pf_approx['lat_approx']
    d_lon = args.ref_lon - ref_pf_approx['lon_approx']
    m_lat = 111320
    m_lon = 111320 * math.cos(math.radians(args.ref_lat))

    print(f"\n  Offset GPS calcolato da {args.ref_pf} ({Path(args.ref_dxf).name}):")
    print(f"    dLat = {d_lat * m_lat:+.1f} m  ({d_lat:+.6f} gradi)")
    print(f"    dLon = {d_lon * m_lon:+.1f} m  ({d_lon:+.6f} gradi)")
    print(f"    Distanza: {math.sqrt((d_lat*m_lat)**2 + (d_lon*m_lon)**2):.1f} m")

    # ── Step 3: Applica offset a tutti i PF ──────────────────────────────────
    for pf in all_pfs:
        pf['lat'] = pf['lat_approx'] + d_lat
        pf['lon'] = pf['lon_approx'] + d_lon

    # ── Step 4: Filtro primo perimetro (opzionale) ───────────────────────────
    pfs_output = all_pfs
    kml_title = "Punti Fiduciali - Fogli unificati"

    if args.mappale:
        print(f"\n  Ricerca mappale {args.mappale} nei DXF...")
        centroid = None

        for dxf_path in args.dxf:
            path = Path(dxf_path)
            crs = detect_crs(parse_pf_from_dxf(dxf_path)[0]['east']) if parse_pf_from_dxf(dxf_path) else None
            if not crs:
                continue
            result = find_mappale_centroid_wgs84(dxf_path, args.mappale, crs, d_lat, d_lon)
            if result:
                centroid = result
                print(f"  Mappale {args.mappale} trovato in {path.name}: "
                      f"{centroid[0]:.5f}N, {centroid[1]:.5f}E")
                break

        if centroid is None:
            print(f"  AVVISO: mappale {args.mappale} non trovato nel layer PARTICELLE. "
                  f"Includo tutti i PF.")
        else:
            pfs_output = find_enclosing_pfs(centroid[0], centroid[1], all_pfs)
            gap = angular_gap(centroid[0], centroid[1], pfs_output)
            print(f"  PF di primo perimetro: {len(pfs_output)} "
                  f"({', '.join(p['name'] for p in pfs_output)}) — "
                  f"gap angolare: {gap:.1f} gradi")
            kml_title = f"PF primo perimetro - Mappale {args.mappale}"

    # ── Step 5: Genera KML ────────────────────────────────────────────────────
    output = Path(args.output)
    generate_kml(pfs_output, output, title=kml_title)

    print(f"\n  ✓ KML salvato: {output.resolve()}")
    print(f"  Tot. PF nel KML: {len(pfs_output)}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
