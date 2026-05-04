#!/usr/bin/env python3
"""
parse_valori_dichiarati.py

Legge tutti i file HTML salvati dal servizio AdE "Consultazione Valori
Immobiliari Dichiarati" presenti in una cartella, estrae le schede-atto e
le unifica in un DataFrame pandas.

Uso da riga di comando:
    python parse_valori_dichiarati.py /path/to/cartella_html/ /path/to/output.xlsx

Uso come modulo:
    from parse_valori_dichiarati import parse_folder
    df = parse_folder("/path/to/cartella_html/")

Testato su output reali del portale AdE (aprile 2026).
Encoding gestito: Windows-1252 (default salvataggio Ctrl+S su Windows IT)
                  e UTF-8 come fallback.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def detect_encoding(filepath: Path) -> str:
    """Rileva l'encoding del file HTML."""
    try:
        import chardet
        with open(filepath, "rb") as f:
            raw = f.read(10000)
        result = chardet.detect(raw)
        if result["confidence"] > 0.8:
            return result["encoding"]
    except ImportError:
        pass
    try:
        with open(filepath, "r", encoding="windows-1252") as f:
            f.read(1000)
        return "windows-1252"
    except UnicodeDecodeError:
        return "utf-8"


def clean_text(s: str) -> str:
    """Normalizza spazi bianchi (incluso nbsp) in un testo."""
    if not s:
        return ""
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def eur_to_int(s: str) -> int:
    """Converte '208.000' o '208.000,50' in intero 208000."""
    if not s:
        return None
    cleaned = s.replace("€", "").replace(" ", "").replace(".", "").split(",")[0]
    try:
        return int(cleaned)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Parser principale
# ---------------------------------------------------------------------------

RE_HEADER = re.compile(
    r"(Residenziale(?:\s+misto)?|Pertinenze|Terziario\s*[-–]\s*Commerciale|"
    r"Produttivo|Non\s+residenziale\s+misto|Immobili\s+agricoli)"
    r"(?:\s*\(T\))?\s*-\s*(\w+)\s+(\d{4})",
    re.IGNORECASE,
)

RE_NUM_IMMOBILI = re.compile(r"Numero immobili:\s*(\d+)")
RE_CORRISPETTIVO = re.compile(r"Corrispettivo dichiarato:\s*([\d\.\,]+)\s*€")

RE_IMMOBILE = re.compile(
    r"Comune di\s+([A-Z][A-Z\s']+?)\s+"
    r"Zona OMI:\s+(\S+)\s+"
    r"Immobile:\s+(\S+)\s+(\S+)\s+"          # SETTORE CATEGORIA
    r"([\d\.,]+)\s*"                          # CONSISTENZA/SUPERFICIE
    r"(m\s*[²2]|vani|m\s*[³3])\s+"            # UNITÀ MISURA
    r"Quota trasferita\s+(\d+)\s*%",
    re.IGNORECASE,
)


def parse_scheda(scheda_div) -> dict:
    """Estrae tutti i campi di una singola scheda-atto."""
    testo = clean_text(scheda_div.get_text(" ", strip=True))

    m_header = RE_HEADER.search(testo)
    m_num = RE_NUM_IMMOBILI.search(testo)
    m_corr = RE_CORRISPETTIVO.search(testo)

    immobili = []
    for m in RE_IMMOBILE.finditer(testo):
        immobili.append({
            "comune": clean_text(m.group(1)),
            "zona_omi": m.group(2),
            "settore": m.group(3),
            "categoria": m.group(4),
            "consistenza": m.group(5),
            "unita": re.sub(r"\s+", "", m.group(6)).replace("2", "²").replace("3", "³"),
            "quota": f"{m.group(7)}%",
        })

    return {
        "tipologia": m_header.group(1) if m_header else None,
        "mese": m_header.group(2) if m_header else None,
        "anno": m_header.group(3) if m_header else None,
        "numero_immobili": int(m_num.group(1)) if m_num else None,
        "corrispettivo_eur": eur_to_int(m_corr.group(1)) if m_corr else None,
        "immobili": immobili,
    }


def parse_html_file(filepath: Path) -> list[dict]:
    """Estrae tutte le schede-atto da un singolo file HTML."""
    encoding = detect_encoding(filepath)
    with open(filepath, "r", encoding=encoding, errors="replace") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    schede_div = soup.find_all("div", class_="card card-default")
    return [parse_scheda(s) for s in schede_div]


def parse_folder(folder: str | Path) -> pd.DataFrame:
    """Legge tutti gli HTML in una cartella, aggrega le schede-atto,
    le espande a livello di singolo immobile e restituisce un DataFrame."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Cartella non trovata: {folder}")

    html_files = sorted(folder.glob("*.html"))
    if not html_files:
        raise FileNotFoundError(f"Nessun file .html trovato in {folder}")

    tutte_schede = []
    for i, filepath in enumerate(html_files, start=1):
        try:
            schede = parse_html_file(filepath)
            for j, s in enumerate(schede, start=1):
                s["file_origine"] = filepath.name
                s["scheda_progressivo"] = f"{i:02d}_{j:02d}"
                tutte_schede.append(s)
        except Exception as e:
            print(f"ERRORE in {filepath.name}: {e}", file=sys.stderr)

    rows = []
    for s in tutte_schede:
        if not s["immobili"]:
            rows.append({
                "scheda": s["scheda_progressivo"],
                "file_origine": s["file_origine"],
                "tipologia_atto": s["tipologia"],
                "mese": s["mese"],
                "anno": s["anno"],
                "numero_immobili": s["numero_immobili"],
                "corrispettivo_eur": s["corrispettivo_eur"],
                "comune": None, "zona_omi": None, "settore": None,
                "categoria": None, "consistenza": None, "unita": None, "quota": None,
            })
        else:
            for imm in s["immobili"]:
                rows.append({
                    "scheda": s["scheda_progressivo"],
                    "file_origine": s["file_origine"],
                    "tipologia_atto": s["tipologia"],
                    "mese": s["mese"],
                    "anno": s["anno"],
                    "numero_immobili": s["numero_immobili"],
                    "corrispettivo_eur": s["corrispettivo_eur"],
                    "comune": imm["comune"],
                    "zona_omi": imm["zona_omi"],
                    "settore": imm["settore"],
                    "categoria": imm["categoria"],
                    "consistenza": imm["consistenza"],
                    "unita": imm["unita"],
                    "quota": imm["quota"],
                })

    return pd.DataFrame(rows)


def calcola_eur_per_m2(
    df: pd.DataFrame,
    coeff_pertinenze: dict | None = None,
) -> pd.DataFrame:
    """Aggiunge la colonna EUR_per_m2 calcolata sulla SUPERFICIE EQUIVALENTE dell'atto.

    Principio metodologico:
    Il corrispettivo è il prezzo complessivo di TUTTI gli immobili dell'atto.
    Per un €/m² corretto, la superficie al denominatore deve essere quella
    COMMERCIALE EQUIVALENTE (ogni componente pesata per settore OMI).

    Esempio:
    - 53 m² RES + 35 m² PER (box) a 105.000 €
    - Corretto: 105.000 / (53×1,00 + 35×0,50) = 105.000 / 70,5 = 1.489 €/m²
    - Sbagliato: 105.000 / 53 = 1.981 €/m²  (gonfia il €/m²)

    Coefficienti per settore:
    - RES: 1,00 | PER: 0,50 | TCO: 1,00 | PRO: 1,00 | AGR: 1,00 | ALT: 0,30
    """
    df = df.copy()
    df["EUR_per_m2"] = None
    df["Sup_equivalente_m2"] = None

    COEFF_DEFAULT = {
        "RES": 1.00, "PER": 0.50, "TCO": 1.00,
        "PRO": 1.00, "AGR": 1.00, "ALT": 0.30,
    }
    coeff = coeff_pertinenze or COEFF_DEFAULT

    for scheda_id, gruppo in df.groupby("scheda", sort=False):
        corrispettivo = gruppo["corrispettivo_eur"].iloc[0]
        if corrispettivo is None:
            continue

        sup_equivalente = 0.0
        for _, riga in gruppo.iterrows():
            if riga["unita"] != "m²":
                continue
            try:
                sup = float(str(riga["consistenza"]).replace(",", "."))
            except (ValueError, TypeError):
                continue
            c = coeff.get(riga["settore"], 1.00)
            sup_equivalente += sup * c

        if sup_equivalente <= 0:
            continue

        eur_m2 = round(corrispettivo / sup_equivalente, 1)
        df.loc[df["scheda"] == scheda_id, "EUR_per_m2"] = eur_m2
        df.loc[df["scheda"] == scheda_id, "Sup_equivalente_m2"] = round(sup_equivalente, 2)

    # Pulisce NaN in colonne Flag e Note_Flag per evitare "nan" nel report Word
    for col in ["Flag", "Note_Flag"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).replace("nan", "")

    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Parsing HTML Valori Immobiliari Dichiarati")
    parser.add_argument("input_folder", help="Cartella contenente i file HTML salvati dal portale AdE")
    parser.add_argument("output_xlsx", nargs="?", help="Path del file Excel di output (opzionale)")
    parser.add_argument("--json", action="store_true", help="Stampa anche output JSON su stdout")
    args = parser.parse_args()

    df = parse_folder(args.input_folder)
    df = calcola_eur_per_m2(df)

    print(f"Schede-atto estratte: {df['scheda'].nunique()}")
    print(f"Righe immobili totali: {len(df)}")
    print(f"Comuni trovati: {df['comune'].dropna().unique().tolist()}")
    print(f"Zone OMI trovate: {df['zona_omi'].dropna().unique().tolist()}")

    if args.output_xlsx:
        df.to_excel(args.output_xlsx, index=False)
        print(f"\nSalvato in: {args.output_xlsx}")

    if args.json:
        print(json.dumps(df.to_dict(orient="records"), indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
