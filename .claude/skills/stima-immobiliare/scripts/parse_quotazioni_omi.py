#!/usr/bin/env python3
"""
parse_quotazioni_omi.py

Legge il CSV delle Quotazioni OMI scaricato dal servizio "Forniture dati OMI"
dell'Agenzia delle Entrate, e filtra per comune/zona/tipologia.

Colonne tipiche:
    Area_territoriale, Regione, Prov, Comune_ISTAT, Comune_cat, Sez,
    Comune_amm, Comune_descrizione, Fascia, Zona, LinkZona,
    Cod_Tip, Descr_Tipologia, Stato, Stato_prev,
    Compr_min, Compr_max, Sup_NL_compr,
    Loc_min, Loc_max, Sup_NL_loc

Uso da riga di comando:
    python parse_quotazioni_omi.py /path/to/quotazioni.csv --comune BOVOLONE --zona B1
    python parse_quotazioni_omi.py /path/to/quotazioni.csv --comune BOVOLONE --zona B1 --tipologia 20
    python parse_quotazioni_omi.py /path/to/quotazioni.csv --comune BOVOLONE --out filtrato.xlsx

Codici tipologia principali:
    20 = Abitazioni civili
    21 = Abitazioni di tipo economico
    1  = Ville e villini
    5  = Negozi
    6  = Uffici
    8  = Capannoni industriali
    14 = Posti auto coperti
    16 = Autorimesse

Encoding gestito automaticamente (Windows-1252, UTF-8, ISO-8859-1).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def detect_csv_encoding_and_separator(filepath: Path) -> tuple[str, str]:
    """Rileva encoding e separatore di un CSV OMI."""
    for enc in ("utf-8", "windows-1252", "iso-8859-1"):
        try:
            with open(filepath, "r", encoding=enc) as f:
                first_lines = "".join(f.readline() for _ in range(3))
            if first_lines.count(";") > first_lines.count(","):
                return enc, ";"
            return enc, ","
        except UnicodeDecodeError:
            continue
    return "utf-8", ";"


def carica_csv_omi(filepath: str | Path) -> pd.DataFrame:
    """Carica il CSV OMI con gestione automatica dell'encoding.
    Funziona sia per il file VALORI sia per il file ZONE."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File non trovato: {filepath}")

    encoding, sep = detect_csv_encoding_and_separator(filepath)

    df = pd.read_csv(filepath, encoding=encoding, sep=sep, low_memory=False)

    is_valori = {"Compr_min", "Compr_max"}.issubset(df.columns)
    is_zone = "Zona_Descr" in df.columns

    if not (is_valori or is_zone):
        # Forse c'è una riga spuria prima del header
        df = pd.read_csv(filepath, encoding=encoding, sep=sep, skiprows=1, low_memory=False)
        is_valori = {"Compr_min", "Compr_max"}.issubset(df.columns)
        is_zone = "Zona_Descr" in df.columns
        if not (is_valori or is_zone):
            raise ValueError(
                f"Il file non sembra un CSV OMI valido. "
                f"Colonne presenti: {list(df.columns)}"
            )

    return df


def classifica_file_csv(filepath: str | Path) -> str:
    """Restituisce 'VALORI' o 'ZONE' in base alle colonne del CSV."""
    df = carica_csv_omi(filepath)
    if {"Compr_min", "Compr_max"}.issubset(df.columns):
        return "VALORI"
    if "Zona_Descr" in df.columns:
        return "ZONE"
    return "SCONOSCIUTO"


def leggi_descrizione_zona(
    csv_zone_path: str | Path,
    comune: str,
    zona: str,
) -> dict:
    """Estrae da un CSV ZONE la descrizione testuale di una specifica zona OMI.

    Restituisce un dict con:
    - zona_descr: descrizione estesa della zona
    - fascia: codice fascia (B=Centro, C=Semicentro, D=Periferia, R=Rurale, E=Extraurbana)
    - fascia_descr: descrizione fascia in italiano
    - tipologia_prevalente: tipologia edilizia prevalente della zona
    """
    df = carica_csv_omi(csv_zone_path)
    filtrato = df[
        (df["Comune_descrizione"].str.upper() == comune.upper())
        & (df["Zona"].str.upper() == zona.upper())
    ]
    if filtrato.empty:
        return {
            "zona_descr": None,
            "fascia": None,
            "fascia_descr": None,
            "tipologia_prevalente": None,
            "messaggio": f"Zona {zona} non trovata nel comune {comune}",
        }

    r = filtrato.iloc[0]

    fascia_map = {
        "B": "Centro urbano",
        "C": "Semicentro",
        "D": "Periferia",
        "R": "Zona rurale",
        "E": "Zona extraurbana",
        "Z": "Zona particolare",
    }
    fascia_cod = r.get("Fascia", "").strip() if isinstance(r.get("Fascia"), str) else None

    return {
        "zona_descr": r.get("Zona_Descr", None),
        "fascia": fascia_cod,
        "fascia_descr": fascia_map.get(fascia_cod, "Non specificata"),
        "tipologia_prevalente": r.get("Descr_tip_prev", None),
    }


def filtra(
    df: pd.DataFrame,
    comune: str | None = None,
    provincia: str | None = None,
    zona: str | None = None,
    tipologia_cod: int | None = None,
    tipologia_descr: str | None = None,
    stato: str | None = None,
) -> pd.DataFrame:
    """Filtra il DataFrame OMI secondo i criteri forniti."""
    result = df.copy()

    if comune:
        result = result[result["Comune_descrizione"].str.upper() == comune.upper()]
    if provincia:
        result = result[result["Prov"].str.upper() == provincia.upper()]
    if zona:
        result = result[result["Zona"].str.upper() == zona.upper()]
    if tipologia_cod is not None:
        result = result[result["Cod_Tip"] == tipologia_cod]
    if tipologia_descr:
        result = result[result["Descr_Tipologia"].str.contains(tipologia_descr, case=False, na=False)]
    if stato:
        result = result[result["Stato"].str.upper() == stato.upper()]

    return result.reset_index(drop=True)


def formatta_output(df: pd.DataFrame) -> pd.DataFrame:
    """Seleziona le colonne più utili per un report di stima."""
    cols = [
        "Comune_descrizione", "Prov", "Fascia", "Zona",
        "Cod_Tip", "Descr_Tipologia", "Stato",
        "Compr_min", "Compr_max", "Sup_NL_compr",
        "Loc_min", "Loc_max", "Sup_NL_loc",
    ]
    cols_esistenti = [c for c in cols if c in df.columns]
    return df[cols_esistenti]


def statistiche_zona(df: pd.DataFrame) -> dict:
    """Calcola statistiche di sintesi sul range €/m² della zona."""
    if df.empty:
        return {"messaggio": "Nessun dato disponibile per i criteri indicati"}

    return {
        "numero_record": len(df),
        "tipologie_presenti": df["Descr_Tipologia"].unique().tolist(),
        "compravendita_eur_m2": {
            "min_assoluto": float(df["Compr_min"].min()) if "Compr_min" in df else None,
            "max_assoluto": float(df["Compr_max"].max()) if "Compr_max" in df else None,
            "media_min": round(float(df["Compr_min"].mean()), 2) if "Compr_min" in df else None,
            "media_max": round(float(df["Compr_max"].mean()), 2) if "Compr_max" in df else None,
            "centrale": round(float((df["Compr_min"].mean() + df["Compr_max"].mean()) / 2), 2)
                        if "Compr_min" in df else None,
        },
        "locazione_eur_m2_mensili": {
            "min_assoluto": float(df["Loc_min"].min()) if "Loc_min" in df else None,
            "max_assoluto": float(df["Loc_max"].max()) if "Loc_max" in df else None,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Filtro CSV Quotazioni OMI")
    parser.add_argument("csv_path", help="Path del CSV Quotazioni OMI scaricato")
    parser.add_argument("--comune", help="Nome del comune (es. BOVOLONE)")
    parser.add_argument("--provincia", help="Sigla provincia (es. VR)")
    parser.add_argument("--zona", help="Codice zona OMI (es. B1, D2, R1)")
    parser.add_argument("--tipologia", type=int, help="Codice tipologia (es. 20 per abitazioni civili)")
    parser.add_argument("--tipologia-descr", help="Descrizione tipologia (es. 'abitazioni civili')")
    parser.add_argument("--stato", help="Stato conservativo (OTTIMO, NORMALE, SCADENTE)")
    parser.add_argument("--out", help="Salva il filtrato come Excel")
    args = parser.parse_args()

    df = carica_csv_omi(args.csv_path)
    print(f"CSV caricato: {len(df)} righe totali")

    filtrato = filtra(
        df,
        comune=args.comune,
        provincia=args.provincia,
        zona=args.zona,
        tipologia_cod=args.tipologia,
        tipologia_descr=args.tipologia_descr,
        stato=args.stato,
    )
    filtrato = formatta_output(filtrato)

    print(f"Righe dopo filtro: {len(filtrato)}")
    if not filtrato.empty:
        print()
        print(filtrato.to_string(index=False))

    import json
    print("\n=== STATISTICHE ZONA ===")
    print(json.dumps(statistiche_zona(filtrato), indent=2, ensure_ascii=False))

    if args.out:
        filtrato.to_excel(args.out, index=False)
        print(f"\nSalvato in: {args.out}")


if __name__ == "__main__":
    main()
