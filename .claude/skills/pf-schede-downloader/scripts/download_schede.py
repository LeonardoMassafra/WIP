#!/usr/bin/env python3
"""
download_schede.py — Scarica schede monografiche PF dal portale AdE con Playwright.

Dipendenze:
  pip install playwright
  playwright install chromium

Uso:
  # Parametri diretti
  python download_schede.py \
      --provincia "VERONA" --comune "VILLAFRANCA DI VERONA" \
      --foglio "16" --pf 1 4 7 \
      --output ./schede/

  # Da JSON prodotto da parse_input.py (ancora richiede --provincia e --comune)
  python download_schede.py \
      --json parsed.json \
      --provincia "VERONA" --comune "VILLAFRANCA DI VERONA" \
      --output ./schede/

  # Modalità headless (nessuna finestra browser)
  python download_schede.py ... --headless

Flag utili:
  --headless     Esegui senza finestra browser (default: con finestra)
  --timeout N    Timeout in secondi per ogni operazione (default: 15)
  --slow N       Rallenta ogni azione di N ms, utile per debug (default: 0)
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

URL_ADE = (
    "https://www.agenziaentrate.gov.it/portale/schede/fabbricatiterreni/"
    "punti-fiduciali/interrogazione-schede-monografiche-punti-fiduciali-mon-"
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def log(msg):
    print(f"  {msg}", flush=True)


def err(msg):
    print(f"  ERRORE: {msg}", file=sys.stderr, flush=True)


def screenshot_on_error(page, label="errore"):
    try:
        path = Path(f"screenshot_{label}.png")
        page.screenshot(path=str(path))
        log(f"Screenshot salvato: {path.resolve()}")
    except Exception:
        pass


def accept_cookies(page, timeout=5000):
    """Chiude il banner cookie se presente."""
    selectors = [
        "button:has-text('Accetta solo i necessari')",
        "button:has-text('Rifiuta')",
        "button:has-text('Accetta i necessari')",
        "button:has-text('Accetta tutti')",
        "#acceptBtn",
        ".cookie-accept",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=timeout):
                btn.click()
                log(f"Cookie banner chiuso ({sel})")
                page.wait_for_timeout(800)
                return
        except Exception:
            continue


def find_select(page, hints: list[str]):
    """
    Trova un elemento <select> cercando:
    1. select con id/name che contiene uno degli hint
    2. select preceduto da un label con testo corrispondente
    3. Posizione nella pagina (fallback)
    """
    for hint in hints:
        hint_l = hint.lower()
        # Per id/name
        for attr in ("id", "name"):
            try:
                sel = page.locator(f'select[{attr}*="{hint_l}" i]')
                if sel.count() > 0:
                    return sel.first
            except Exception:
                pass
        # Per label adiacente
        try:
            label = page.locator(f'label:has-text("{hint}")').first
            sel = page.locator('xpath=following::select[1]').nth(0)
            # Verifica che sia vicina
            if label.count() > 0:
                following = label.page.locator(f'label:has-text("{hint}") ~ select, '
                                               f'label:has-text("{hint}") + select')
                if following.count() > 0:
                    return following.first
        except Exception:
            pass
    return None


def try_select_option(select_el, value: str, timeout=8000):
    """
    Prova a selezionare un'opzione per label (case-insensitive),
    poi per value, poi per testo parziale.
    """
    # Leggi le opzioni disponibili
    options = select_el.locator("option").all()
    option_texts = []
    for opt in options:
        try:
            option_texts.append(opt.inner_text().strip())
        except Exception:
            pass

    # Cerca corrispondenza case-insensitive
    value_lower = value.lower()
    match = next((t for t in option_texts if t.lower() == value_lower), None)
    if not match:
        # Corrispondenza parziale
        match = next((t for t in option_texts if value_lower in t.lower()), None)

    if match:
        select_el.select_option(label=match, timeout=timeout)
        return match
    else:
        available = ", ".join(option_texts[:10])
        raise ValueError(
            f"Valore '{value}' non trovato. Opzioni disponibili: {available}..."
        )


# ─── Pipeline principale ───────────────────────────────────────────────────────

def download_schede(provincia, comune, foglio, pf_numbers, output_dir,
                    headless=False, timeout_s=15, slow_ms=0):
    """
    Apre il portale AdE e scarica le schede monografiche per i PF indicati.
    Restituisce lista di path dei PDF scaricati.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    timeout_ms = timeout_s * 1000
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []

    print(f"\n{'='*55}")
    print(f"  Downloader Schede Monografiche PF — Portale AdE")
    print(f"{'='*55}")
    print(f"  Provincia : {provincia}")
    print(f"  Comune    : {comune}")
    print(f"  Foglio    : {foglio}")
    print(f"  PF        : {', '.join(f'PF {n}' for n in pf_numbers)}")
    print(f"  Output    : {output_dir.resolve()}")
    print(f"{'='*55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_ms)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # ── Step 1: Apri portale ─────────────────────────────────────────────
        log("[1/5] Apertura portale AdE...")
        try:
            page.goto(URL_ADE, timeout=timeout_ms * 2, wait_until="domcontentloaded")
        except PWTimeout:
            err("Timeout apertura portale. Verifica la connessione.")
            browser.close()
            return []

        accept_cookies(page)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)

        # ── Step 2: Selezione Provincia ──────────────────────────────────────
        log("[2/5] Selezione Provincia...")
        sel_provincia = find_select(page, ["provincia", "prov", "region"])
        if not sel_provincia:
            # Fallback: primo select della pagina
            all_selects = page.locator("select").all()
            if all_selects:
                sel_provincia = page.locator("select").first
            else:
                screenshot_on_error(page, "no_select")
                err("Nessun dropdown trovato nella pagina. Struttura portale cambiata?")
                browser.close()
                return []

        try:
            chosen = try_select_option(sel_provincia, provincia, timeout_ms)
            log(f"  Provincia selezionata: '{chosen}'")
        except ValueError as e:
            screenshot_on_error(page, "provincia")
            err(str(e))
            browser.close()
            return []

        # Attendi che il dropdown Comune si popoli
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)

        # ── Step 3: Selezione Comune ─────────────────────────────────────────
        log("[3/5] Selezione Comune...")
        sel_comune = find_select(page, ["comune", "munic", "city"])
        if not sel_comune:
            all_selects = page.locator("select").all()
            if len(all_selects) >= 2:
                sel_comune = page.locator("select").nth(1)
            else:
                screenshot_on_error(page, "comune")
                err("Dropdown Comune non trovato dopo selezione Provincia.")
                browser.close()
                return []

        try:
            chosen = try_select_option(sel_comune, comune, timeout_ms)
            log(f"  Comune selezionato: '{chosen}'")
        except ValueError as e:
            screenshot_on_error(page, "comune")
            err(str(e))
            browser.close()
            return []

        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)

        # ── Step 4: Selezione Foglio ─────────────────────────────────────────
        log("[4/5] Selezione Foglio...")
        sel_foglio = find_select(page, ["foglio", "sheet", "fg"])
        if not sel_foglio:
            all_selects = page.locator("select").all()
            if len(all_selects) >= 3:
                sel_foglio = page.locator("select").nth(2)
            else:
                screenshot_on_error(page, "foglio")
                err("Dropdown Foglio non trovato.")
                browser.close()
                return []

        # Prova il foglio nei formati: "16", "0016", "16/0"
        foglio_variants = [foglio, foglio.zfill(4), f"{foglio}/0", f"0{foglio}"]
        foglio_selezionato = False
        for variant in foglio_variants:
            try:
                chosen = try_select_option(sel_foglio, variant, timeout_ms)
                log(f"  Foglio selezionato: '{chosen}'")
                foglio_selezionato = True
                break
            except ValueError:
                continue

        if not foglio_selezionato:
            screenshot_on_error(page, "foglio")
            err(f"Foglio '{foglio}' non trovato nel dropdown. Prova le varianti: {foglio_variants}")
            browser.close()
            return []

        page.wait_for_timeout(800)

        # Clicca il pulsante di ricerca
        btn_cerca = None
        for sel in ["button:has-text('Cerca')", "button:has-text('Ricerca')",
                    "button:has-text('Visualizza')", "input[type=submit]",
                    "button[type=submit]"]:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn_cerca = btn
                    break
            except Exception:
                continue

        if btn_cerca:
            btn_cerca.click()
            log("  Ricerca avviata.")
        else:
            # Prova invio form
            sel_foglio.press("Enter")
            log("  Ricerca avviata (Enter).")

        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        page.wait_for_timeout(1000)

        # ── Step 5: Download PDF per ogni PF ─────────────────────────────────
        log(f"[5/5] Download schede ({len(pf_numbers)} PF)...")

        for pf_num in pf_numbers:
            pf_name = f"PF {pf_num}"
            log(f"  Cercando {pf_name}...")

            # Cerca link con testo PF N
            link = None
            for pattern in [f"PF {pf_num}", f"PF{pf_num}", str(pf_num)]:
                candidates = [
                    page.locator(f'a:has-text("{pattern}")'),
                    page.locator(f'td:has-text("{pattern}") a'),
                    page.locator(f'tr:has-text("{pattern}") a'),
                ]
                for cand in candidates:
                    try:
                        if cand.count() > 0 and cand.first.is_visible(timeout=2000):
                            link = cand.first
                            break
                    except Exception:
                        continue
                if link:
                    break

            if not link:
                log(f"  AVVISO: {pf_name} non trovato nella lista — potrebbe non avere scheda.")
                continue

            # Scarica il PDF
            output_file = output_dir / f"scheda_PF{pf_num}_fg{foglio.zfill(4)}.pdf"
            try:
                with page.expect_download(timeout=timeout_ms * 2) as dl_info:
                    link.click()
                dl = dl_info.value
                dl.save_as(str(output_file))
                downloaded.append(output_file)
                log(f"  ✓ {output_file.name}")
            except PWTimeout:
                # Il click potrebbe aprire una nuova tab con il PDF
                pages_before = len(context.pages)
                link.click()
                page.wait_for_timeout(2000)
                if len(context.pages) > pages_before:
                    new_page = context.pages[-1]
                    pdf_url = new_page.url
                    if pdf_url.endswith(".pdf") or "pdf" in pdf_url.lower():
                        # Scarica il PDF via richiesta HTTP
                        response = page.request.get(pdf_url)
                        output_file.write_bytes(response.body())
                        downloaded.append(output_file)
                        log(f"  ✓ {output_file.name} (da nuova tab)")
                        new_page.close()
                    else:
                        log(f"  AVVISO: {pf_name} — download non riuscito (tab aperta: {pdf_url})")
                        new_page.close()
                else:
                    log(f"  AVVISO: {pf_name} — download non riuscito (timeout).")

            time.sleep(1.5)  # Pausa tra download per non sovraccaricare il portale

        browser.close()

    print(f"\n{'='*55}")
    print(f"  Completato: {len(downloaded)}/{len(pf_numbers)} schede scaricate")
    for f in downloaded:
        print(f"    ✓ {f.name}")
    print(f"  Cartella: {output_dir.resolve()}")
    print(f"{'='*55}\n")

    return downloaded


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scarica schede monografiche PF dal portale AdE"
    )
    parser.add_argument("--provincia", required=True,
                        help='Provincia per esteso, es. "VERONA"')
    parser.add_argument("--comune", required=True,
                        help='Comune per esteso, es. "VILLAFRANCA DI VERONA"')
    parser.add_argument("--foglio", help='Numero foglio, es. "16"')
    parser.add_argument("--pf", nargs="+", type=int,
                        help="Numeri PF da scaricare, es. 1 4 7")
    parser.add_argument("--json", dest="json_file",
                        help="JSON prodotto da parse_input.py (fornisce foglio e pf)")
    parser.add_argument("--output", default="./schede_pf",
                        help="Cartella di output (default: ./schede_pf)")
    parser.add_argument("--headless", action="store_true",
                        help="Esegui senza finestra browser")
    parser.add_argument("--timeout", type=int, default=15,
                        help="Timeout in secondi per ogni operazione (default: 15)")
    parser.add_argument("--slow", type=int, default=0,
                        help="Rallenta ogni azione di N ms (default: 0)")
    args = parser.parse_args()

    # Carica da JSON se fornito
    foglio = args.foglio
    pf_numbers = args.pf or []

    if args.json_file:
        with open(args.json_file) as f:
            data = json.load(f)
        if not foglio:
            foglio = data.get("foglio")
        if not pf_numbers:
            pf_numbers = data.get("pf_numbers", [])

    if not foglio:
        err("--foglio è obbligatorio (o usa --json con un file che lo contiene)")
        sys.exit(1)
    if not pf_numbers:
        err("--pf è obbligatorio (o usa --json con un file che li contiene)")
        sys.exit(1)

    download_schede(
        provincia=args.provincia,
        comune=args.comune,
        foglio=foglio,
        pf_numbers=pf_numbers,
        output_dir=args.output,
        headless=args.headless,
        timeout_s=args.timeout,
        slow_ms=args.slow,
    )


if __name__ == "__main__":
    main()
