#!/usr/bin/env python3
"""
extract_atto.py
===============

Estrae i dati strutturati da un PDF di atto di aggiornamento catastale
(Tipo Mappale, Frazionamento, Particellare) prodotto dall'Agenzia delle Entrate
attraverso Pregeo. Output: <out_dir>/dati_atto.md.

Esempio d'uso:
    python extract_atto.py --pdf 121_modulistica.pdf --id 121 --out 03_OUTPUT/
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# --------------------------------------------------------------------------- #
# Estrazione testo dal PDF
# --------------------------------------------------------------------------- #

def estrai_testo(pdf_path: Path) -> tuple[str, int]:
    """Restituisce (testo_completo, n_pagine). Solleva eccezione se il PDF
    è una scansione senza testo selezionabile."""
    try:
        import pypdf
    except ImportError:
        sys.exit("Serve pypdf: pip install pypdf")

    r = pypdf.PdfReader(str(pdf_path))
    pages = []
    for p in r.pages:
        pages.append(p.extract_text() or "")
    full = "\n".join(pages)
    if not full.strip():
        sys.exit(f"PDF '{pdf_path}' senza testo selezionabile (probabile scansione). "
                 f"Per ora la skill non gestisce OCR.")
    return full, len(r.pages)


# --------------------------------------------------------------------------- #
# Modello dati
# --------------------------------------------------------------------------- #

@dataclass
class DatiAtto:
    # Identificazione
    tipo_atto: str = "N.D."           # "TIPO MAPPALE" | "TIPO FRAZIONAMENTO" | "TIPO PARTICELLARE"
    codice_pregeo: str = "N.D."
    numero_atto: str = "N.D."         # progressivo dalla riga 0 del libretto
    data_redazione: str = "N.D."
    ufficio_provinciale: str = "N.D."
    protocollo_ade: str = "N.D."

    # Catasto
    comune: str = "N.D."
    codice_comune: str = "N.D."       # es. F442
    foglio: str = "N.D."
    sezione_censuaria: str = "N.D."
    particelle_oggetto: list[str] = field(default_factory=list)

    # Estratto di mappa
    em_protocollo: str = "N.D."
    em_data: str = "N.D."
    em_codice_riscontro: str = "N.D."

    # Operazioni catastali (modello censuario)
    operazioni: list[dict] = field(default_factory=list)
    # Ciascuna: {operazione: O|S|C|V, foglio, particella, sub, identif, ha, a, ca, lotto}

    # Soggetti
    intestatari: list[str] = field(default_factory=list)
    firmatari: list[str] = field(default_factory=list)

    # Tecnico
    tec_qualifica: str = "N.D."
    tec_nome: str = "N.D."
    tec_iscrizione: str = "N.D."
    tec_ordine: str = "N.D."
    tec_cf: str = "N.D."

    # Rilievo
    rilievo_strumento: str = "N.D."
    rilievo_tipo: str = "N.D."
    pf_rilevati: list[str] = field(default_factory=list)
    punti_dettaglio: list[str] = field(default_factory=list)

    # Geometria
    linee_dividenti: list[str] = field(default_factory=list)  # "101 -> 102 (RC)"
    punti_vertice: list[str] = field(default_factory=list)

    # Parametri
    distorsione: str = "N.D."
    scala_originaria: str = "N.D."
    zona: str = "N.D."

    # Note
    relazione_tecnica: str = ""

    # File origine
    nome_file: str = ""
    n_pagine: int = 0


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

def _first_match(pattern: str, text: str, group: int = 1, flags: int = 0) -> str:
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else "N.D."


def parsa_identificazione(text: str, d: DatiAtto) -> None:
    if "TIPO MAPPALE" in text.upper():
        d.tipo_atto = "TIPO MAPPALE"
    elif "TIPO FRAZIONAMENTO" in text.upper():
        d.tipo_atto = "TIPO FRAZIONAMENTO"
    elif "TIPO PARTICELLARE" in text.upper():
        d.tipo_atto = "TIPO PARTICELLARE"
    elif "ATTO DI AGGIORNAMENTO" in text.upper():
        d.tipo_atto = "ATTO DI AGGIORNAMENTO"

    d.codice_pregeo = _first_match(r"Codice file PREGEO:\s*([0-9.]+)", text)
    d.ufficio_provinciale = _first_match(r"Ufficio provinciale di:\s*([A-Z\s]+?)(?:\n|Protocollo)", text)
    proto = _first_match(r"Protocollo n:\s*(\S+)", text)
    if proto and proto != "N.D." and proto.lower() != "data":
        d.protocollo_ade = proto


def parsa_catasto(text: str, d: DatiAtto) -> None:
    d.comune = _first_match(r"Comune:\s*([A-Z][A-Z\s''\-]+?)(?:\n|Foglio)", text)
    d.foglio = _first_match(r"Foglio:\s*(\d+)", text)
    sez = _first_match(r"Sez\.\s*Censuaria:\s*(\S+)", text)
    if sez and sez != "N.D." and sez.lower() != "particelle:":
        d.sezione_censuaria = sez

    m = re.search(r"Particelle:\s*([0-9,\s]+)", text)
    if m:
        ps = [p.strip() for p in m.group(1).split(",") if p.strip().isdigit()]
        d.particelle_oggetto = ps


def parsa_estratto_mappa(text: str, d: DatiAtto) -> None:
    m = re.search(r"Estratto di mappa.*?Protocollo:\s*(\S+)\s*Data:\s*(\S+)\s*Codice Riscontro:\s*(\S+)",
                  text, re.DOTALL)
    if m:
        d.em_protocollo = m.group(1)
        d.em_data = m.group(2)
        d.em_codice_riscontro = m.group(3)


def parsa_operazioni(text: str, d: DatiAtto) -> None:
    """Estrae le righe di operazioni dal blocco 'Modello censuario'.

    Le righe possono avere formati misti (numero di campi superficie variabile):
        O 0220 397 000 00000 16 64 SN 202     (a=16 ca=64, manca ha)
        S 0220 397 000 00000 00 00 000        (3 numeri: 00 00 000)
        C 0220 000 a AAA 00000 11 74 SN 202   (a=11 ca=74)
    Per robustezza parsifico ogni riga token per token.
    """
    sezione = re.search(r"Modello censuario(.+?)(?:Informazioni Complementari|Pag\.|$)",
                        text, re.DOTALL)
    if not sezione:
        return
    blocco = sezione.group(1)

    orig_part = None
    for m in re.finditer(r"^[OS]\s+\d{4}\s+(\d{3,4})\s", blocco, re.MULTILINE):
        candidate = m.group(1)
        if candidate not in ("000", "0000"):
            orig_part = candidate.lstrip("0") or candidate
            break

    op_label_map = {"O": "Originale", "S": "Soppressa",
                    "C": "Costituita", "V": "Variata"}

    for line in blocco.splitlines():
        line = line.strip()
        if not re.match(r"^[OSCV]\s", line):
            continue
        tokens = line.split()
        if len(tokens) < 5:
            continue
        op_codice = tokens[0]
        foglio = tokens[1]
        part = tokens[2]
        sub = tokens[3]
        identif = tokens[4]
        rest = tokens[5:]

        if rest and rest[0] == "00000":
            rest = rest[1:]

        nums: list[int] = []
        idx = 0
        while idx < len(rest) and rest[idx].isdigit() and len(nums) < 3:
            nums.append(int(rest[idx]))
            idx += 1
        coda = rest[idx:]

        lotto = ""
        if len(nums) == 3 and rest[2:3] and len(rest[2]) == 3:
            lotto = rest[2]
            nums = nums[:2]

        if not lotto:
            for t in reversed(coda):
                if t.isdigit() and len(t) == 3:
                    lotto = t
                    break

        ha = a = ca = 0
        if len(nums) == 2:
            a, ca = nums
        elif len(nums) >= 3:
            ha, a, ca = nums[:3]

        if sub.isalpha() and len(sub) == 1:
            base = orig_part if part in ("000", "0000") else (part.lstrip("0") or part)
            part_disp = f"{base}/{sub}"
            sub_disp = sub
        else:
            part_disp = part.lstrip("0") or part
            sub_disp = sub if sub.isdigit() and sub != "000" else ""

        d.operazioni.append({
            "operazione": op_label_map.get(op_codice, op_codice),
            "foglio": foglio,
            "particella": part_disp,
            "sub": sub_disp,
            "identif": identif if identif != "00000" else "",
            "superficie": f"{ha}-{a:02d}-{ca:02d}",
            "lotto": lotto,
        })


def parsa_intestatari_firmatari(text: str, d: DatiAtto) -> None:
    """Intestatari = blocco DITTA del libretto (riga 6|DITTA|...).
       Firmatari = la pagina 'Firma delle parti o loro delegati'."""
    for m in re.finditer(r"6\|DITTA\|[^|]*\|([^|]+)\|(\d{11,16})\|([^|]+)\|", text):
        ragione, piva, quota = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        d.intestatari.append(f"{ragione} — P.IVA/CF {piva} — {quota}")

    sez = re.search(r"Firma delle parti.*?(?=Tecnico redattore|Pag\.\s*\d+|$)", text, re.DOTALL)
    if sez:
        sez_text = sez.group(0)
        piva_intestatari = set()
        for x in d.intestatari:
            mm = re.search(r"(\d{11,16})", x)
            if mm:
                piva_intestatari.add(mm.group(1))

        for m in re.finditer(
            r"([A-Z][A-Z\s\.'\-]{3,}?(?:S\.?P\.?A\.?|S\.R\.L\.?|SOC\.|SOCIETA|CONSORZIO)[A-Z\s\.'\-]*)"
            r",\s*([A-Z][A-Z\s'\-]+?)\s*\(([A-Z]{2})\)[\s,]*(\d{11,16})",
            sez_text,
        ):
            rag, com, prov, ident = (s.strip() for s in m.groups())
            if ident in piva_intestatari:
                continue
            entry = f"{rag} — {com} ({prov}) — P.IVA/CF {ident}"
            if entry not in d.firmatari:
                d.firmatari.append(entry)

        for m in re.finditer(r"FIRMA\s+([A-Z][A-Z\s']+?),\s*([A-Z0-9]{16})", sez_text):
            nome = m.group(1).strip()
            cf = m.group(2).strip()
            tail = sez_text[m.end():m.end() + 250]
            qm = re.search(r"(IN QUALITA[^\n]+?)(?:Firma|\n|$)", tail)
            qualifica = qm.group(1).strip() if qm else ""
            qualifica = re.sub(r"Firma\s*$", "", qualifica).strip()
            if qualifica:
                d.firmatari.append(f"{nome} (CF {cf}) — {qualifica}")
            else:
                d.firmatari.append(f"{nome} (CF {cf})")


def parsa_tecnico(text: str, d: DatiAtto) -> None:
    d.tec_nome = _first_match(r"Tecnico:\s*([A-Z][A-Z\s']+?)(?:\n|Provincia)", text)
    m = re.search(r"Provincia:\s*([A-Z\s]+?)Qualifica:\s*([A-Z]+(?: [A-Z]+)*)", text)
    if m:
        d.tec_ordine = m.group(1).strip()
        d.tec_qualifica = m.group(2).strip()
    else:
        d.tec_ordine = _first_match(r"Provincia:\s*([A-Z\s]+?)(?:\n|N\.\s*iscrizione)", text)
        d.tec_qualifica = _first_match(r"Qualifica:\s*([A-Z]+(?:\s+[A-Z]+)*)", text)
    d.tec_iscrizione = _first_match(r"N\.\s*iscrizione:\s*(\d+)", text)
    d.tec_cf = _first_match(r"Cod\.\s*Fisc\.:\s*([A-Z0-9]{16})", text)


def parsa_libretto(text: str, d: DatiAtto) -> None:
    """Parsa le righe del libretto delle misure (formato Pregeo)."""
    m = re.search(r"^0\|(\d{8})\|(\S+)\|([A-Z]\d{3})\|(\d{4})\|", text, re.MULTILINE)
    if m:
        date_raw, numero, fcat, foglio = m.groups()
        d.data_redazione = f"{date_raw[0:2]}/{date_raw[2:4]}/{date_raw[4:8]}"
        d.numero_atto = numero
        d.codice_comune = fcat

    m = re.search(r"^9\|.*?\|.*?\|([A-Z]+)\|([^|]+)\|", text, re.MULTILINE)
    if m:
        d.rilievo_strumento = m.group(2).replace("RILIEVO ESEGUITO CON ", "").strip()

    text_upper = text.upper()
    if "GPS" in d.rilievo_strumento.upper() or re.search(r"6\|L2\|.*?RTK", text):
        d.rilievo_tipo = "GPS RTK"
    elif "STAZIONE" in text_upper or "CELERIMETRIC" in text_upper:
        d.rilievo_tipo = "Celerimetrico"

    pf_set: set[str] = set()
    det_set: set[str] = set()
    for m in re.finditer(r"^2\|([^|]+)\|([\d\.\-,\s]+)\|", text, re.MULTILINE):
        nome = m.group(1).strip()
        if re.match(r"^PF\d+/\d+/[A-Z]\d+$", nome):
            pf_set.add(nome)
        else:
            det_set.add(nome)
    d.pf_rilevati = sorted(pf_set)
    d.punti_dettaglio = sorted(det_set, key=lambda s: (len(s), s))

    sezione_ld = re.search(r"6\|LINEE DIVIDENTI\|(.+?)(?:6\||\Z)", text, re.DOTALL)
    if sezione_ld:
        for m in re.finditer(r"^7\|\d+\|(\d+)\|(\d+)\|(RC|PV)\|", sezione_ld.group(1), re.MULTILINE):
            d.linee_dividenti.append(f"{m.group(1)} -> {m.group(2)} ({m.group(3)})")

    sezione_pv = re.search(r"6\|PUNTI VERTICE\|(.+?)(?:6\||\Z)", text, re.DOTALL)
    if sezione_pv:
        for m in re.finditer(r"^7\|\d+\|(\S+?)\|PV\|", sezione_pv.group(1), re.MULTILINE):
            d.punti_vertice.append(m.group(1))


def parsa_parametri(text: str, d: DatiAtto) -> None:
    d.distorsione = _first_match(r"6\|DISTORSIONE\|([\d\.]+)\|", text)
    d.scala_originaria = _first_match(r"6\|SCALAORIGINARIA\|(\d+)\|", text)
    zona = _first_match(r"6\|ZONA\|([^|]+)\|", text)
    if zona and zona != "N.D.":
        d.zona = zona


def parsa_relazione_tecnica(text: str, d: DatiAtto) -> None:
    """Cattura il testo libero della Relazione Tecnica."""
    m = re.search(r"DICHIARAZIONI TECNICHE\s*(.+?)(?:Pag\.\s*\d+|Schema del rilievo|Sviluppo|\Z)",
                  text, re.DOTALL)
    if m:
        rel = m.group(1)
        rel = re.sub(r"Pag\.\s*\d+\s*di\s*\d+", "", rel)
        rel = re.sub(r"TIPO\s+(MAPPALE|FRAZIONAMENTO|PARTICELLARE).*?Codice file PREGEO:\s*[\d\.]+",
                     "", rel, flags=re.DOTALL)
        rel = re.sub(r"Dati generali del tipo.*?N\.\s*iscrizione:\s*\d+", "", rel, flags=re.DOTALL)
        rel = re.sub(r"\s+", " ", rel).strip()
        d.relazione_tecnica = rel


# --------------------------------------------------------------------------- #
# Generazione Markdown
# --------------------------------------------------------------------------- #

def to_markdown(d: DatiAtto, atto_id: str) -> str:
    L: list[str] = []
    A = L.append
    A(f"# Atto di aggiornamento - {atto_id}")
    A("")
    A("## Identificazione")
    A(f"- Tipo atto: {d.tipo_atto}")
    A(f"- Codice file PREGEO: {d.codice_pregeo}")
    A(f"- Numero progressivo (atto): {d.numero_atto}")
    A(f"- Data redazione: {d.data_redazione}")
    A(f"- Ufficio provinciale: {d.ufficio_provinciale}")
    A(f"- Protocollo AdE: {d.protocollo_ade}")
    A("")
    A("## Dati catastali")
    A(f"- Comune: {d.comune}")
    A(f"- Codice catastale comune: {d.codice_comune}")
    A(f"- Foglio: {d.foglio}")
    A(f"- Sezione censuaria: {d.sezione_censuaria}")
    A(f"- Particelle oggetto: {', '.join(d.particelle_oggetto) if d.particelle_oggetto else 'N.D.'}")
    A("")
    A("## Estratto di mappa")
    A(f"- Protocollo: {d.em_protocollo}")
    A(f"- Data: {d.em_data}")
    A(f"- Codice riscontro: {d.em_codice_riscontro}")
    A("")
    A("## Operazioni catastali")
    if d.operazioni:
        A("| Operazione | Foglio | Particella | Sub | Identif. | Superficie (ha-a-ca) | Lotto |")
        A("|---|---|---|---|---|---|---|")
        for op in d.operazioni:
            A(f"| {op['operazione']} | {op['foglio']} | {op['particella']} | "
              f"{op['sub']} | {op['identif']} | {op['superficie']} | {op['lotto']} |")
    else:
        A("- Nessuna operazione estratta (verificare manualmente).")
    A("")
    A("## Intestatari")
    if d.intestatari:
        for x in d.intestatari:
            A(f"- {x}")
    else:
        A("- N.D.")
    A("")
    A("## Firmatari")
    if d.firmatari:
        for x in d.firmatari:
            A(f"- {x}")
    else:
        A("- N.D.")
    A("")
    A("## Tecnico redattore")
    A(f"- Nome: {d.tec_nome}")
    A(f"- Qualifica: {d.tec_qualifica}")
    A(f"- N. iscrizione albo: {d.tec_iscrizione}")
    A(f"- Ordine/Provincia: {d.tec_ordine}")
    A(f"- Codice fiscale: {d.tec_cf}")
    A("")
    A("## Rilievo")
    A(f"- Strumento: {d.rilievo_strumento}")
    A(f"- Tipo rilievo: {d.rilievo_tipo}")
    A(f"- N. PF rilevati: {len(d.pf_rilevati)}")
    A(f"- PF rilevati: {', '.join(d.pf_rilevati) if d.pf_rilevati else 'N.D.'}")
    A(f"- N. punti di dettaglio: {len(d.punti_dettaglio)}")
    A(f"- Punti di dettaglio: {', '.join(d.punti_dettaglio) if d.punti_dettaglio else 'N.D.'}")
    A("")
    A("## Geometria del frazionamento")
    A(f"- Linee dividenti: {', '.join(d.linee_dividenti) if d.linee_dividenti else 'N.D.'}")
    A(f"- Punti vertice (PV): {', '.join(d.punti_vertice) if d.punti_vertice else 'N.D.'}")
    A("")
    A("## Parametri di rappresentazione")
    A(f"- Distorsione: {d.distorsione}")
    A(f"- Scala originaria mappa: 1:{d.scala_originaria}" if d.scala_originaria != "N.D."
      else "- Scala originaria mappa: N.D.")
    A(f"- Zona: {d.zona}")
    A("")
    A("## Note dalla relazione tecnica")
    if d.relazione_tecnica:
        for frase in re.split(r"(?<=[\.;])\s+", d.relazione_tecnica):
            frase = frase.strip().lstrip("-").strip()
            if frase:
                A(f"- {frase}")
    else:
        A("- N.D.")
    A("")
    A("## File di origine")
    A(f"- Nome file PDF: {d.nome_file}")
    A(f"- N. pagine: {d.n_pagine}")
    A("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Estrai dati da PDF di atto di aggiornamento Pregeo.")
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--id", default=None,
                    help="Identificativo dell'atto (es. 121). Se omesso usa il nome file.")
    ap.add_argument("--out", type=Path, default=Path("."),
                    help="Cartella di output. Default: cartella corrente.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    atto_id = args.id or args.pdf.stem

    text, npages = estrai_testo(args.pdf)
    d = DatiAtto(nome_file=args.pdf.name, n_pagine=npages)

    parsa_identificazione(text, d)
    parsa_catasto(text, d)
    parsa_estratto_mappa(text, d)
    parsa_operazioni(text, d)
    parsa_intestatari_firmatari(text, d)
    parsa_tecnico(text, d)
    parsa_libretto(text, d)
    parsa_parametri(text, d)
    parsa_relazione_tecnica(text, d)

    md_path = args.out / "dati_atto.md"
    md_path.write_text(to_markdown(d, atto_id), encoding="utf-8")

    if not args.quiet:
        print(f"Tipo atto: {d.tipo_atto}")
        print(f"Codice PREGEO: {d.codice_pregeo}")
        print(f"Comune/Foglio/Particelle: {d.comune} / {d.foglio} / {', '.join(d.particelle_oggetto) or 'N.D.'}")
        print(f"PF rilevati: {len(d.pf_rilevati)}")
        print(f"Punti di dettaglio: {len(d.punti_dettaglio)}")
        nd_count = sum(1 for v in vars(d).values() if v == "N.D.")
        if nd_count:
            print(f"Campi N.D. (verificare): {nd_count}")
        print(f"\nOutput: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
