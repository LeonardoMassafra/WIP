#!/usr/bin/env python3
"""
dxf_to_kml.py — Estrattore Punti Fiduciali da DXF catastale italiano

Uso:
    # Passo 1: estrai PF con conversione Helmert approssimativa (~100m)
    python dxf_to_kml.py input.dxf --output pf.kml

    # Passo 2: correggi con un punto GPS di riferimento
    python dxf_to_kml.py input.dxf --output pf_corretto.kml \
        --ref-pf "PF 4" --ref-lat 45.361801 --ref-lon 10.836778

Il sistema di coordinate del catasto italiano è Gauss-Boaga Ovest (EPSG:3003):
    - Ellissoide: Hayford/International (a=6378388, f=1/297)
    - Datum: Roma40
    - Meridiano centrale: 9°E, False Easting: 1500000m
    - Fattore di scala: k0=0.9996

Trasformazione verso WGS84 con parametri Helmert 7 parametri (EPSG:1074):
    dx=-104.1, dy=-49.1, dz=-9.9
    rx=0.886", ry=-0.539", rz=0.679", s=-1.052 ppm
Errore residuo atteso: ~100m (per 10m serve griglia NTv2 IGM)
Con punto di riferimento GPS: ~2-5m
"""

import sys
import math
import json
import argparse
from pathlib import Path


# ─── Costanti ellissoide Hayford (Roma40 / Gauss-Boaga) ───────────────────────
A_HAY = 6378388.0          # semiasse maggiore
F_HAY = 1.0 / 297.0        # schiacciamento
B_HAY = A_HAY * (1 - F_HAY)
E2_HAY = 2 * F_HAY - F_HAY**2
E_HAY = math.sqrt(E2_HAY)

# ─── Parametri proiezione Gauss-Boaga Ovest ────────────────────────────────────
K0 = 0.9996
LON0 = math.radians(9.0)   # meridiano centrale 9°E
FE = 1_500_000.0            # False Easting
FN = 0.0                    # False Northing

# ─── Helmert 7 parametri Roma40 → WGS84 (EPSG:1074) ──────────────────────────
DX, DY, DZ = -104.1, -49.1, -9.9
RX = math.radians(0.886 / 3600)
RY = math.radians(-0.539 / 3600)
RZ = math.radians(0.679 / 3600)
S_PPM = -1.052e-6

# ─── Costanti ellissoide WGS84 ────────────────────────────────────────────────
A_WGS = 6378137.0
F_WGS = 1.0 / 298.257223563
B_WGS = A_WGS * (1 - F_WGS)
E2_WGS = 2 * F_WGS - F_WGS**2


def gb_ovest_to_wgs84(east, north):
    """Converte coordinate Gauss-Boaga Ovest → WGS84 (lat, lon gradi decimali)."""

    # 1. Inversa Transverse Mercator → lat/lon su Roma40 (radianti)
    x = east - FE
    y = north - FN

    M = y / K0
    mu = M / (A_HAY * (1 - E2_HAY/4 - 3*E2_HAY**2/64 - 5*E2_HAY**3/256))

    e1 = (1 - math.sqrt(1 - E2_HAY)) / (1 + math.sqrt(1 - E2_HAY))
    phi1 = (mu
            + (3*e1/2 - 27*e1**3/32) * math.sin(2*mu)
            + (21*e1**2/16 - 55*e1**4/32) * math.sin(4*mu)
            + (151*e1**3/96) * math.sin(6*mu)
            + (1097*e1**4/512) * math.sin(8*mu))

    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)
    tan_phi1 = math.tan(phi1)

    N1 = A_HAY / math.sqrt(1 - E2_HAY * sin_phi1**2)
    T1 = tan_phi1**2
    C1 = (E2_HAY / (1 - E2_HAY)) * cos_phi1**2
    R1 = A_HAY * (1 - E2_HAY) / (1 - E2_HAY * sin_phi1**2)**1.5
    D = x / (N1 * K0)

    lat_r = (phi1
             - (N1 * tan_phi1 / R1) * (
                 D**2/2
                 - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*E2_HAY/(1-E2_HAY)) * D**4/24
                 + (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*E2_HAY/(1-E2_HAY) - 3*C1**2) * D**6/720
             ))
    lon_r = LON0 + (
        D
        - (1 + 2*T1 + C1) * D**3/6
        + (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*E2_HAY/(1-E2_HAY) + 24*T1**2) * D**5/120
    ) / cos_phi1

    # 2. Geodetiche Roma40 → cartesiane geocentriche (Hayford)
    sin_lat = math.sin(lat_r)
    cos_lat = math.cos(lat_r)
    sin_lon = math.sin(lon_r)
    cos_lon = math.cos(lon_r)
    N_hay = A_HAY / math.sqrt(1 - E2_HAY * sin_lat**2)

    Xr = N_hay * cos_lat * cos_lon
    Yr = N_hay * cos_lat * sin_lon
    Zr = N_hay * (1 - E2_HAY) * sin_lat

    # 3. Helmert 7 parametri
    Xw = DX + (1 + S_PPM) * (Xr + RZ*Yr - RY*Zr)
    Yw = DY + (1 + S_PPM) * (-RZ*Xr + Yr + RX*Zr)
    Zw = DZ + (1 + S_PPM) * (RY*Xr - RX*Yr + Zr)

    # 4. Cartesiane WGS84 → geodetiche WGS84 (iterazione Bowring)
    p = math.sqrt(Xw**2 + Yw**2)
    lon_wgs = math.atan2(Yw, Xw)
    lat_wgs = math.atan2(Zw, p * (1 - E2_WGS))
    for _ in range(10):
        sin_l = math.sin(lat_wgs)
        N_wgs = A_WGS / math.sqrt(1 - E2_WGS * sin_l**2)
        lat_wgs = math.atan2(Zw + E2_WGS * N_wgs * sin_l, p)

    return math.degrees(lat_wgs), math.degrees(lon_wgs)


def parse_dxf(dxf_path):
    """
    Legge un file DXF e restituisce i PF dal layer FIDUCIALI.
    Restituisce lista di dict: {'name': 'PF 4', 'east': ..., 'north': ...}
    """
    with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    # Raccogli tutte le entità TEXT nel layer FIDUCIALI
    pf_points = {}  # chiave: (east, north) arrotondate → nome PF

    in_entities = False
    i = 0
    while i < len(lines):
        code = lines[i].strip()
        if i + 1 < len(lines):
            value = lines[i+1].strip()
        else:
            value = ''

        if code == '0' and value == 'SECTION':
            # controlla se è ENTITIES
            if i+3 < len(lines) and lines[i+2].strip() == '2' and lines[i+3].strip() == 'ENTITIES':
                in_entities = True
            i += 2
            continue

        if code == '0' and value == 'ENDSEC':
            if in_entities:
                in_entities = False
            i += 2
            continue

        if not in_entities:
            i += 2
            continue

        # Nuova entità
        if code == '0' and value in ('TEXT', 'MTEXT', 'INSERT'):
            entity_type = value
            entity = {'type': entity_type, 'layer': '', 'x': None, 'y': None, 'text': ''}
            i += 2

            # Leggi i gruppi dell'entità finché non troviamo un nuovo '0'
            while i < len(lines):
                c = lines[i].strip()
                v = lines[i+1].strip() if i+1 < len(lines) else ''

                if c == '0':
                    break  # nuova entità o fine sezione

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
                    entity['text'] += v  # MTEXT multiriga

                i += 2

            # Filtra: solo layer FIDUCIALI
            if 'FIDUCIALI' not in entity['layer'].upper():
                continue

            # Entità TEXT: raccoglie nome PF
            if entity['type'] in ('TEXT', 'MTEXT') and entity['text'] and entity['x'] is not None:
                # Normalizza: "1" → "PF 1", "PF1" → "PF 1"
                t = entity['text'].strip()
                if t.upper().startswith('PF'):
                    num = t[2:].strip()
                else:
                    num = t
                name = f"PF {num}"
                key = (round(entity['x'], 1), round(entity['y'], 1))
                pf_points[key] = name

            # Entità INSERT: marca la posizione con coordinate
            elif entity['type'] == 'INSERT' and entity['x'] is not None:
                key = (round(entity['x'], 1), round(entity['y'], 1))
                if key not in pf_points:
                    pf_points[key] = None  # placeholder, verrà associato al TEXT

        else:
            i += 2

    # Costruisci lista finale associando nome e coordinate
    result = []
    for (ex, no), name in pf_points.items():
        if name:
            result.append({'name': name, 'east': ex, 'north': no})

    # Ordina per numero PF
    def sort_key(p):
        try:
            return int(p['name'].split()[-1])
        except ValueError:
            return 0

    result.sort(key=sort_key)
    return result


def apply_offset(pf_list, ref_name, ref_lat, ref_lon):
    """
    Calcola l'offset tra la posizione Helmert di un PF di riferimento
    e le coordinate GPS reali fornite dall'utente, poi corregge tutti i PF.
    """
    ref_pf = next((p for p in pf_list if p['name'].strip().lower() == ref_name.strip().lower()), None)
    if ref_pf is None:
        raise ValueError(f"PF di riferimento '{ref_name}' non trovato nel DXF. "
                         f"PF disponibili: {[p['name'] for p in pf_list]}")

    d_lat = ref_lat - ref_pf['lat_helmert']
    d_lon = ref_lon - ref_pf['lon_helmert']

    m_per_deg_lat = 111320
    m_per_deg_lon = 111320 * math.cos(math.radians(ref_lat))
    dist_m = math.sqrt((d_lat * m_per_deg_lat)**2 + (d_lon * m_per_deg_lon)**2)

    print(f"\n  Offset calcolato da {ref_name}:")
    print(f"    Δlat = {d_lat*m_per_deg_lat:+.1f}m N  ({d_lat:+.6f}°)")
    print(f"    Δlon = {d_lon*m_per_deg_lon:+.1f}m E  ({d_lon:+.6f}°)")
    print(f"    Distanza totale: {dist_m:.1f}m")

    for pf in pf_list:
        pf['lat'] = pf['lat_helmert'] + d_lat
        pf['lon'] = pf['lon_helmert'] + d_lon

    return pf_list


def generate_kml(pf_list, output_path, dxf_name, corrected=False):
    """Genera il file KML da una lista di PF con coordinate lat/lon."""
    acc_note = "Corretto con punto GPS di riferimento (~2-5m)" if corrected else "Conversione Helmert approssimativa (~100m)"

    placemarks = ""
    for pf in pf_list:
        lat = pf.get('lat', pf['lat_helmert'])
        lon = pf.get('lon', pf['lon_helmert'])
        placemarks += f"""    <Placemark>
      <name>{pf['name']}</name>
      <description>Gauss-Boaga Ovest: E={pf['east']:.3f}, N={pf['north']:.3f}
WGS84: {lat:.6f}°N, {lon:.6f}°E
{acc_note}</description>
      <styleUrl>#pf_style</styleUrl>
      <Point>
        <coordinates>{lon:.6f},{lat:.6f},0</coordinates>
      </Point>
    </Placemark>\n"""

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Punti Fiduciali - {dxf_name}</name>
    <description>{acc_note}</description>
    <Style id="pf_style">
      <IconStyle>
        <color>ff0000ff</color>
        <scale>1.2</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>1.2</scale>
      </LabelStyle>
    </Style>
{placemarks}  </Document>
</kml>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(kml)

    return output_path


def main():
    parser = argparse.ArgumentParser(description='Estrattore PF da DXF catastale italiano')
    parser.add_argument('dxf', help='File DXF da elaborare')
    parser.add_argument('--output', '-o', help='File KML di output (default: nome_dxf.kml)')
    parser.add_argument('--ref-pf', help='Nome del PF di riferimento (es: "PF 4")')
    parser.add_argument('--ref-lat', type=float, help='Latitudine WGS84 del PF di riferimento (da Google Maps)')
    parser.add_argument('--ref-lon', type=float, help='Longitudine WGS84 del PF di riferimento (da Google Maps)')
    parser.add_argument('--json-out', help='Salva anche i dati PF in formato JSON')
    args = parser.parse_args()

    dxf_path = Path(args.dxf)
    if not dxf_path.exists():
        print(f"ERRORE: File non trovato: {dxf_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else dxf_path.with_suffix('.kml')
    dxf_name = dxf_path.stem

    print(f"\n{'='*55}")
    print(f"  Estrattore Punti Fiduciali — {dxf_name}")
    print(f"{'='*55}")

    # 1. Parsing DXF
    print(f"\n[1/3] Analisi file DXF...")
    pf_list = parse_dxf(dxf_path)

    if not pf_list:
        print("  ATTENZIONE: Nessun PF trovato nel layer FIDUCIALI.")
        print("  Verifica che il file DXF provenga dall'Agenzia delle Entrate")
        print("  e contenga il layer 'FIDUCIALI'.")
        sys.exit(1)

    print(f"  Trovati {len(pf_list)} Punti Fiduciali:")
    for pf in pf_list:
        print(f"    {pf['name']}: E={pf['east']:.3f}, N={pf['north']:.3f}")

    # 2. Conversione Helmert
    print(f"\n[2/3] Conversione Gauss-Boaga → WGS84 (Helmert, ~100m)...")
    for pf in pf_list:
        lat, lon = gb_ovest_to_wgs84(pf['east'], pf['north'])
        pf['lat_helmert'] = lat
        pf['lon_helmert'] = lon
        print(f"    {pf['name']}: {lat:.6f}°N, {lon:.6f}°E")

    # 3. Correzione GPS (opzionale)
    corrected = False
    if args.ref_pf and args.ref_lat and args.ref_lon:
        print(f"\n[3/3] Correzione con punto GPS di riferimento...")
        pf_list = apply_offset(pf_list, args.ref_pf, args.ref_lat, args.ref_lon)
        corrected = True
        print(f"\n  Coordinate corrette (~2-5m):")
        for pf in pf_list:
            print(f"    {pf['name']}: {pf['lat']:.6f}°N, {pf['lon']:.6f}°E")
    else:
        print(f"\n[3/3] Nessun punto GPS fornito — KML con precisione ~100m")
        print(f"  Per correggere, riesegui con:")
        print(f"    --ref-pf \"PF X\" --ref-lat <lat> --ref-lon <lon>")

    # 4. Generazione KML
    generate_kml(pf_list, output_path, dxf_name, corrected)
    print(f"\n  ✓ KML salvato: {output_path}")

    # 5. JSON opzionale
    if args.json_out:
        with open(args.json_out, 'w') as f:
            json.dump(pf_list, f, indent=2)
        print(f"  ✓ JSON salvato: {args.json_out}")

    print(f"\n{'='*55}\n")
    return pf_list


if __name__ == '__main__':
    main()
