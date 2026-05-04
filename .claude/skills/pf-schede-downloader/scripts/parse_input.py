#!/usr/bin/env python3
"""
parse_input.py — Estrae informazioni da KML e nome file DXF catastale.

Uso:
  # Tutti i PF del foglio
  python3 parse_input.py <file.kml> [<file.dxf>]

  # Solo i PF che racchiudono la particella indicata
  python3 parse_input.py <file.kml> <file.dxf> --mappale 245

Output JSON:
  {
    "codice_belfiore": "L949",
    "foglio": "16",
    "foglio_raw": "0016",
    "pf_numbers": [1, 4, 7],
    "pf_names": ["PF 1", "PF 4", "PF 7"],
    "dxf_filename": "L949_001600.dxf",
    "mappale": "245",                      # solo se --mappale usato
    "centroide_mappale": [1659123.4, 5021456.7],  # coordinate Gauss-Boaga
    "pf_tutti": [1, 2, 4, 7, 9]           # tutti i PF del foglio (prima del filtro)
  }
"""
import argparse
import math
import re
import sys
import os
import json


# ─── KML ──────────────────────────────────────────────────────────────────────

def parse_kml(kml_path: str) -> list[int]:
    """Estrae i numeri PF da un file KML prodotto da dxf-pf-extractor."""
    with open(kml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    names = re.findall(r'<name>\s*(PF\s*\d+)[^<]*</name>', content, re.IGNORECASE)
    numbers = []
    for name in names:
        m = re.search(r'(\d+)', name)
        if m:
            numbers.append(int(m.group(1)))
    return sorted(set(numbers))


# ─── DXF filename ─────────────────────────────────────────────────────────────

def parse_dxf_filename(filename: str) -> dict:
    """
    Estrae codice belfiore e numero foglio dal nome file DXF catastale.

    Formati supportati:
      LXXX_YYYYZZ.dxf    es. L949_001600.dxf → belfiore=L949, foglio=0016
      LXXX_YYYY.dxf      es. L949_0016.dxf   → belfiore=L949, foglio=0016
    """
    basename = os.path.basename(filename)
    basename_no_ext = os.path.splitext(basename)[0]

    m = re.match(r'^([A-Z]\d{3})_(\d{4,})', basename_no_ext, re.IGNORECASE)
    if not m:
        return {"codice_belfiore": None, "foglio": None, "foglio_raw": None}

    codice = m.group(1).upper()
    foglio_raw = m.group(2)[:4]
    foglio = str(int(foglio_raw))

    return {
        "codice_belfiore": codice,
        "foglio": foglio,
        "foglio_raw": foglio_raw,
    }


# ─── DXF content parsing ──────────────────────────────────────────────────────

def parse_dxf_entities(dxf_path: str) -> list[dict]:
    """
    Legge il DXF e restituisce tutte le entità TEXT/MTEXT con:
      layer, text, x, y
    """
    with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    entities = []
    in_entities = False
    i = 0

    while i < len(lines):
        code = lines[i].strip()
        value = lines[i + 1].strip() if i + 1 < len(lines) else ''

        if code == '0' and value == 'SECTION':
            if i + 3 < len(lines) and lines[i + 2].strip() == '2' and lines[i + 3].strip() == 'ENTITIES':
                in_entities = True
            i += 2
            continue

        if code == '0' and value == 'ENDSEC':
            in_entities = False
            i += 2
            continue

        if not in_entities:
            i += 2
            continue

        if code == '0' and value in ('TEXT', 'MTEXT'):
            entity = {'layer': '', 'x': None, 'y': None, 'text': ''}
            i += 2
            while i < len(lines):
                c = lines[i].strip()
                v = lines[i + 1].strip() if i + 1 < len(lines) else ''
                if c == '0':
                    break
                if c == '8':
                    entity['layer'] = v
                elif c == '10':
                    try:
                        entity['x'] = float(v)
                    except ValueError:
                        pass
                elif c == '20':
                    try:
                        entity['y'] = float(v)
                    except ValueError:
                        pass
                elif c == '1':
                    entity['text'] = v
                elif c == '3':
                    entity['text'] += v
                i += 2
            if entity['x'] is not None and entity['text']:
                entities.append(entity)
        else:
            i += 2

    return entities


def find_mappale_centroid(dxf_path: str, mappale: str) -> tuple[float, float] | None:
    """
    Cerca il testo del mappale nel layer PARTICELLE del DXF.
    Restituisce (x, y) in coordinate Gauss-Boaga, o None se non trovato.
    """
    entities = parse_dxf_entities(dxf_path)

    # Normalizza il mappale cercato: rimuovi zeri iniziali e spazi
    mappale_norm = mappale.strip().lstrip('0') or '0'

    candidates = []
    for ent in entities:
        if 'PARTICELLE' not in ent['layer'].upper():
            continue

        text = ent['text'].strip()
        # Normalizza il testo trovato nel DXF (potrebbe avere zeri es. "0245")
        text_norm = text.lstrip('0') or '0'
        # Rimuovi eventuale suffisso di sezione (es. "245A" → "245")
        text_base = re.sub(r'[A-Za-z/].*$', '', text_norm).strip()

        if text_base == mappale_norm or text_norm == mappale_norm:
            candidates.append((ent['x'], ent['y'], text))

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0][0], candidates[0][1]

    # Se ci sono più testi corrispondenti (es. particella con sotto-particelle),
    # prendi il centroide medio
    xs = [c[0] for c in candidates]
    ys = [c[1] for c in candidates]
    return sum(xs) / len(xs), sum(ys) / len(ys)


# ─── Algoritmo di copertura angolare ──────────────────────────────────────────

def angular_gap(centroid: tuple, pf_list: list[dict]) -> float:
    """
    Calcola il gap angolare massimo (in gradi) tra i PF intorno al centroide.
    Se il gap massimo < 180° → il centroide è racchiuso.
    """
    cx, cy = centroid
    angles = sorted(
        math.degrees(math.atan2(pf['north'] - cy, pf['east'] - cx)) % 360
        for pf in pf_list
    )
    if not angles:
        return 360.0

    gaps = []
    for i in range(len(angles)):
        gap = angles[(i + 1) % len(angles)] - angles[i]
        if gap <= 0:
            gap += 360
        gaps.append(gap)

    return max(gaps)


def find_enclosing_pfs(centroid: tuple, all_pfs: list[dict]) -> list[dict]:
    """
    Trova il set minimo di PF che racchiude il centroide della particella.

    Algoritmo:
    1. Ordina i PF per distanza dal centroide (più vicino prima)
    2. Aggiunge PF uno alla volta
    3. Si ferma quando il gap angolare massimo scende sotto 180°
       (= il centroide è racchiuso da tutti i lati)
    """
    cx, cy = centroid

    pfs_sorted = sorted(
        all_pfs,
        key=lambda p: math.sqrt((p['east'] - cx) ** 2 + (p['north'] - cy) ** 2)
    )

    selected = []
    for pf in pfs_sorted:
        selected.append(pf)
        if len(selected) >= 3:
            gap = angular_gap(centroid, selected)
            if gap < 180.0:
                return selected

    # Fallback: restituisce tutti i PF disponibili se non si riesce a racchiudere
    return pfs_sorted


def pf_positions_from_dxf(dxf_path: str) -> list[dict]:
    """
    Estrae le posizioni dei PF dal layer FIDUCIALI del DXF.
    Restituisce lista di {'name': 'PF 4', 'east': ..., 'north': ..., 'number': 4}
    """
    entities = parse_dxf_entities(dxf_path)
    pf_map = {}

    for ent in entities:
        if 'FIDUCIALI' not in ent['layer'].upper():
            continue
        text = ent['text'].strip()
        if text.upper().startswith('PF'):
            num_str = text[2:].strip()
        else:
            num_str = re.sub(r'[^\d]', '', text)

        if not num_str.isdigit():
            continue

        num = int(num_str)
        key = (round(ent['x'], 1), round(ent['y'], 1))
        pf_map[key] = {'name': f'PF {num}', 'number': num,
                       'east': ent['x'], 'north': ent['y']}

    return sorted(pf_map.values(), key=lambda p: p['number'])


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Estrae PF da KML/DXF catastale, con filtro per mappale.'
    )
    parser.add_argument('kml', help='File KML prodotto da dxf-pf-extractor')
    parser.add_argument('dxf', nargs='?', help='File DXF catastale (opzionale)')
    parser.add_argument('--mappale', '-m',
                        help='Numero mappale della particella da racchiudere (es. 245)')
    args = parser.parse_args()

    result = {}

    # ── KML: tutti i PF del foglio ───────────────────────────────────────────
    if not os.path.exists(args.kml):
        print(f"ERRORE: File KML non trovato: {args.kml}", file=sys.stderr)
        sys.exit(1)

    all_pf_numbers = parse_kml(args.kml)
    result['pf_tutti'] = all_pf_numbers

    # ── DXF filename: belfiore + foglio ──────────────────────────────────────
    dxf_path = args.dxf
    if dxf_path:
        dxf_info = parse_dxf_filename(dxf_path)
        result.update(dxf_info)
        result['dxf_filename'] = os.path.basename(dxf_path)
    else:
        kml_info = parse_dxf_filename(args.kml)
        result.update(kml_info)
        result['dxf_filename'] = None

    # ── Filtro per mappale ────────────────────────────────────────────────────
    if args.mappale and dxf_path:
        if not os.path.exists(dxf_path):
            print(f"ERRORE: File DXF non trovato: {dxf_path}", file=sys.stderr)
            sys.exit(1)

        centroid = find_mappale_centroid(dxf_path, args.mappale)
        if centroid is None:
            print(f"ERRORE: Mappale '{args.mappale}' non trovato nel layer PARTICELLE del DXF.",
                  file=sys.stderr)
            print("  Suggerimento: prova varianti (es. con zeri: 0245) o verifica il numero.",
                  file=sys.stderr)
            sys.exit(1)

        print(f"  Mappale {args.mappale}: centroide a E={centroid[0]:.1f}, N={centroid[1]:.1f}",
              file=sys.stderr)

        # Leggi posizioni PF dal DXF per l'algoritmo geometrico
        pf_positions = pf_positions_from_dxf(dxf_path)
        if not pf_positions:
            print("ERRORE: Nessun PF trovato nel layer FIDUCIALI del DXF.", file=sys.stderr)
            sys.exit(1)

        enclosing = find_enclosing_pfs(centroid, pf_positions)
        gap = angular_gap(centroid, enclosing)

        print(f"  Gap angolare con {len(enclosing)} PF: {gap:.1f}° "
              f"({'racchiuso ✓' if gap < 180 else 'non racchiuso — tutti i PF disponibili'})",
              file=sys.stderr)

        selected_numbers = sorted(p['number'] for p in enclosing)
        result['pf_numbers'] = selected_numbers
        result['pf_names'] = [f'PF {n}' for n in selected_numbers]
        result['mappale'] = args.mappale
        result['centroide_mappale'] = list(centroid)
        result['gap_angolare'] = round(gap, 1)

    else:
        # Nessun filtro: restituisce tutti i PF
        result['pf_numbers'] = all_pf_numbers
        result['pf_names'] = [f'PF {n}' for n in all_pf_numbers]
        if args.mappale and not dxf_path:
            print("AVVISO: --mappale richiede anche il file DXF.", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
