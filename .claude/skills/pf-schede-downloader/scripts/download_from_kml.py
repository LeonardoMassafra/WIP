#!/usr/bin/env python3
"""
download_from_kml.py — Scarica schede monografiche PF a partire da un KML.

Legge un KML prodotto da merge_to_kml.py, raggruppa i PF per foglio,
risolve automaticamente il codice Belfiore in Comune e Provincia,
e scarica le schede monografiche dal portale AdE in sequenza.

Uso:
  python download_from_kml.py pf_p206.kml --output ./schede/

  # Modalita' headless (nessuna finestra browser)
  python download_from_kml.py pf_p206.kml --output ./schede/ --headless

  # Solo visualizza i gruppi senza scaricare
  python download_from_kml.py pf_p206.kml --dry-run
"""

import argparse
import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cache locale del dataset comuni
SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_PATH = SCRIPT_DIR.parent / "references" / "codici_belfiore.json"

# Dataset pubblico: comuni italiani con codice catastale (Belfiore), nome, sigla provincia
COMUNI_JSON_URL = (
    "https://raw.githubusercontent.com/matteocontrini/comuni-json/master/comuni.json"
)

URL_ADE_INFO = (
    "https://www.agenziaentrate.gov.it/portale/schede/fabbricatiterreni/"
    "punti-fiduciali/interrogazione-schede-monografiche-punti-fiduciali-mon-"
)
URL_ADE = "https://www1.agenziaentrate.gov.it/servizi/Monografie/ricerca.php"


# ══════════════════════════════════════════════════════════════════════════════
# LOOKUP BELFIORE -> COMUNE / PROVINCIA
# ══════════════════════════════════════════════════════════════════════════════

def load_comuni_db():
    """
    Carica il database comuni dal cache locale o lo scarica da GitHub.
    Restituisce dict {codice_belfiore: {'nome': ..., 'provincia': ..., 'sigla': ...}}
    """
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding='utf-8') as f:
            return json.load(f)

    print("  Download database comuni italiani (una tantum)...")
    try:
        with urllib.request.urlopen(COMUNI_JSON_URL, timeout=15) as r:
            raw = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        print(f"  ERRORE download database comuni: {e}", file=sys.stderr)
        print("  Verifica la connessione internet e riprova.", file=sys.stderr)
        sys.exit(1)

    # Costruisci indice per codice catastale
    db = {}
    for comune in raw:
        codice = comune.get('codiceCatastale', '').strip().upper()
        if codice:
            db[codice] = {
                'nome':     comune.get('nome', ''),
                'sigla':    comune.get('sigla', ''),
                'provincia': comune.get('provincia', {}).get('nome', '')
            }

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"  Database salvato: {CACHE_PATH} ({len(db)} comuni)")
    return db


def resolve_belfiore(code, db):
    """Risolve un codice Belfiore in (nome_comune, sigla_provincia)."""
    entry = db.get(code.upper())
    if not entry:
        return None, None
    return entry['nome'], entry['sigla']


# ══════════════════════════════════════════════════════════════════════════════
# PARSING KML
# ══════════════════════════════════════════════════════════════════════════════

def parse_kml_groups(kml_path):
    """
    Legge il KML prodotto da merge_to_kml.py e raggruppa i PF per foglio.

    Formato atteso del nome Placemark: "PF N (BELFIORE_FOGLIORAW)"
    es. "PF 3 (E349_000400)", "PF 2 (B304_002000)"

    Restituisce dict:
      {
        (belfiore, foglio_str): {
          'belfiore': 'E349',
          'foglio_raw': '0004',
          'foglio': '4',
          'pf_numbers': [3, 7],
        },
        ...
      }
    """
    content = Path(kml_path).read_text(encoding='utf-8', errors='replace')

    # Estrai tutti i nomi dei Placemark
    names = re.findall(r'<name>(PF\s+\d+\s+\([^)]+\))</name>', content)

    groups = {}
    pattern = re.compile(
        r'PF\s+(\d+)\s+\(([A-Z]\d{3})_(\d{4,})\)', re.IGNORECASE
    )

    for name in names:
        m = pattern.search(name)
        if not m:
            continue
        pf_num    = int(m.group(1))
        belfiore  = m.group(2).upper()
        foglio_raw = m.group(3)[:4]
        foglio    = str(int(foglio_raw))

        key = (belfiore, foglio)
        if key not in groups:
            groups[key] = {
                'belfiore':   belfiore,
                'foglio_raw': foglio_raw,
                'foglio':     foglio,
                'pf_numbers': []
            }
        if pf_num not in groups[key]['pf_numbers']:
            groups[key]['pf_numbers'].append(pf_num)

    for g in groups.values():
        g['pf_numbers'].sort()

    return groups


# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD (Playwright)
# ══════════════════════════════════════════════════════════════════════════════

def download_group(comune, provincia, sigla, foglio, pf_numbers, output_dir,
                   headless=False, timeout_s=15, slow_ms=0):
    """
    Scarica le schede PF per un singolo foglio dal portale AdE.
    Riusa la logica di download_schede.py.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    timeout_ms = timeout_s * 1000
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []

    def try_select(select_el, value):
        options = select_el.locator("option").all()
        texts = []
        for opt in options:
            try: texts.append(opt.inner_text().strip())
            except Exception: pass
        v_lower = value.lower()
        match = next((t for t in texts if t.lower() == v_lower), None)
        if not match:
            match = next((t for t in texts if v_lower in t.lower()), None)
        if match:
            select_el.select_option(label=match, timeout=timeout_ms)
            return match
        raise ValueError(f"'{value}' non trovato. Opzioni: {', '.join(texts[:8])}...")

    def close_popups(page):
        """Chiude cookie banner e qualsiasi popup/modal presente."""
        selectors = [
            # Cookie banner
            "button:has-text('Accetta solo i necessari')",
            "button:has-text('Rifiuta')",
            "button:has-text('Accetta tutti')",
            # Popup dichiarazione precompilata e simili
            "a:has-text('Chiudi')",
            "button:has-text('Chiudi')",
            "[aria-label='Chiudi']",
            ".modal .close",
            ".popup-close",
        ]
        for sel in selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    page.wait_for_timeout(600)
            except Exception:
                continue

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_ms)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Naviga direttamente al servizio PHP (cascade server-side)
        page.goto(URL_ADE, timeout=timeout_ms * 2, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        page.wait_for_timeout(800)

        # Attendi che il dropdown provincia abbia opzioni reali
        page.wait_for_timeout(2000)
        selects = page.locator("select")

        # Diagnostico: mostra le opzioni disponibili nel primo select
        opts = selects.nth(0).locator("option").all()
        opt_texts = []
        for o in opts:
            try: opt_texts.append(o.inner_text().strip())
            except Exception: pass
        print(f"    Opzioni provincia disponibili: {opt_texts[:8]}")

        # Provincia — prova nome esteso, maiuscolo, sigla
        prov_ok = False
        for prov_variant in [provincia, provincia.upper(), sigla, sigla.upper()]:
            try:
                chosen = try_select(selects.nth(0), prov_variant)
                print(f"    Provincia: {chosen}")
                prov_ok = True
                break
            except ValueError:
                continue
        if not prov_ok:
            page.screenshot(path=str(output_dir / "debug_provincia.png"))
            print(f"    ERRORE: provincia '{provincia}' non trovata. "
                  f"Screenshot: debug_provincia.png", file=sys.stderr)
            browser.close()
            return []

        # Submit del form PHP che contiene i select (cascade server-side)
        def submit_form(p):
            # Cerca il form che contiene il select (evita il search form dell'header)
            try:
                p.evaluate("""
                    var sel = document.querySelector('select');
                    if (sel) {
                        var form = sel.closest('form');
                        if (form) { form.submit(); }
                    }
                """)
                return True
            except Exception:
                pass
            # Fallback: input submit visibile dentro un form con select
            for sel in ["form:has(select) input[type=submit]",
                        "form:has(select) button[type=submit]"]:
                try:
                    btn = p.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        return True
                except Exception:
                    continue
            return False

        submit_form(page)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(output_dir / "debug_dopo_cerca1.png"), full_page=True)

        # Comune — dopo il submit la Provincia sparisce, rimane solo il select Comune
        try:
            chosen = try_select(page.locator("select").nth(0), comune)
            print(f"    Comune: {chosen}")
        except ValueError as e:
            opts = page.locator("select").nth(0).locator("option").all()
            opt_texts = [o.inner_text().strip() for o in opts if o.inner_text().strip()]
            print(f"    Opzioni comune disponibili: {opt_texts[:10]}")
            print(f"    ERRORE: {e}", file=sys.stderr)
            page.screenshot(path=str(output_dir / "debug_comune.png"), full_page=True)
            browser.close()
            return []

        # Submit per far comparire il dropdown Foglio
        submit_form(page)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        page.wait_for_timeout(1000)

        # Foglio — dopo il submit rimane solo il select Foglio
        foglio_variants = [foglio, foglio.zfill(4), f"{foglio}/0"]
        foglio_ok = False
        for variant in foglio_variants:
            try:
                chosen = try_select(page.locator("select").nth(0), variant)
                print(f"    Foglio: {chosen}")
                foglio_ok = True
                break
            except ValueError:
                continue
        if not foglio_ok:
            opts = page.locator("select").nth(0).locator("option").all()
            opt_texts = [o.inner_text().strip() for o in opts]
            print(f"    Opzioni foglio disponibili: {opt_texts[:10]}")
            print(f"    ERRORE: foglio '{foglio}' non trovato.", file=sys.stderr)
            browser.close()
            return []

        # Submit per ottenere la lista dei PF
        submit_form(page)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(output_dir / "debug_lista_pf.png"), full_page=True)

        # Download PF
        for pf_num in pf_numbers:
            link = None
            for pattern in [f"PF {pf_num}", f"PF{pf_num}", str(pf_num)]:
                for locator in [
                    page.locator(f'a:has-text("{pattern}")'),
                    page.locator(f'td:has-text("{pattern}") a'),
                    page.locator(f'tr:has-text("{pattern}") a'),
                ]:
                    try:
                        if locator.count() > 0 and locator.first.is_visible(timeout=2000):
                            link = locator.first
                            break
                    except Exception:
                        continue
                if link:
                    break

            if not link:
                print(f"    AVVISO: PF {pf_num} non disponibile nel portale.")
                continue

            out_file = output_dir / f"scheda_PF{pf_num}_fg{foglio.zfill(4)}.pdf"
            try:
                with page.expect_download(timeout=timeout_ms * 2) as dl_info:
                    link.click()
                dl_info.value.save_as(str(out_file))
                downloaded.append(out_file)
                print(f"    OK  scheda_PF{pf_num}_fg{foglio.zfill(4)}.pdf")
            except PWTimeout:
                pages_before = len(context.pages)
                link.click()
                page.wait_for_timeout(2000)
                if len(context.pages) > pages_before:
                    new_page = context.pages[-1]
                    pdf_url = new_page.url
                    if 'pdf' in pdf_url.lower():
                        response = page.request.get(pdf_url)
                        out_file.write_bytes(response.body())
                        downloaded.append(out_file)
                        print(f"    OK  scheda_PF{pf_num}_fg{foglio.zfill(4)}.pdf (tab)")
                    new_page.close()
                else:
                    print(f"    AVVISO: PF {pf_num} download fallito.")

            time.sleep(1.5)

        browser.close()

    return downloaded


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Scarica schede PF da portale AdE a partire da un KML.'
    )
    parser.add_argument('kml', help='KML prodotto da merge_to_kml.py')
    parser.add_argument('--output', default='./schede_pf',
                        help='Cartella di output (default: ./schede_pf)')
    parser.add_argument('--headless', action='store_true',
                        help='Esegui senza finestra browser')
    parser.add_argument('--timeout', type=int, default=15,
                        help='Timeout in secondi per ogni operazione (default: 15)')
    parser.add_argument('--slow', type=int, default=0,
                        help='Rallenta ogni azione di N ms (default: 0)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostra i gruppi senza scaricare')
    args = parser.parse_args()

    kml_path = Path(args.kml)
    if not kml_path.exists():
        print(f"ERRORE: KML non trovato: {kml_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Download schede PF da KML")
    print(f"  Input : {kml_path.name}")
    print(f"  Output: {Path(args.output).resolve()}")
    print(f"{'='*60}\n")

    # Parsing KML
    groups = parse_kml_groups(kml_path)
    if not groups:
        print("ERRORE: nessun PF trovato nel KML (formato atteso: 'PF N (BELFIORE_FOGLIO)').",
              file=sys.stderr)
        sys.exit(1)

    # Lookup Belfiore
    db = load_comuni_db()

    # Risolvi e stampa piano di download
    plan = []
    for (belfiore, foglio), group in sorted(groups.items()):
        nome, sigla = resolve_belfiore(belfiore, db)
        if not nome:
            print(f"  AVVISO: codice '{belfiore}' non trovato nel database comuni.")
            nome  = f"COMUNE_{belfiore}"
            sigla = "??"
        entry = db.get(belfiore.upper(), {})
        provincia_nome = entry.get('provincia', sigla)
        plan.append({
            'belfiore':       belfiore,
            'foglio':         foglio,
            'foglio_raw':     group['foglio_raw'],
            'comune':         nome,
            'provincia':      provincia_nome,   # nome esteso es. "Verona"
            'sigla':          sigla,            # es. "VR"
            'pf_numbers':     group['pf_numbers'],
        })
        print(f"  Foglio {foglio:>3}  |  {belfiore}  |  {nome} ({sigla})"
              f"  |  PF: {', '.join(str(n) for n in group['pf_numbers'])}")

    print()

    if args.dry_run:
        print("  [dry-run] Nessun download eseguito.")
        return

    # Download per ogni gruppo
    all_downloaded = []
    for i, item in enumerate(plan, 1):
        print(f"  [{i}/{len(plan)}] {item['comune']} - Foglio {item['foglio']} "
              f"({', '.join(f'PF {n}' for n in item['pf_numbers'])})")
        files = download_group(
            comune     = item['comune'],
            provincia  = item['provincia'],
            sigla      = item['sigla'],
            foglio     = item['foglio'],
            pf_numbers = item['pf_numbers'],
            output_dir = args.output,
            headless   = args.headless,
            timeout_s  = args.timeout,
            slow_ms    = args.slow,
        )
        all_downloaded.extend(files)
        if i < len(plan):
            print("  Pausa tra sessioni...")
            time.sleep(2)

    print(f"\n{'='*60}")
    print(f"  Completato: {len(all_downloaded)} schede scaricate")
    for f in all_downloaded:
        print(f"    {f.name}")
    print(f"  Cartella: {Path(args.output).resolve()}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
