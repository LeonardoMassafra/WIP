#!/usr/bin/env python3
"""
genera_checklist_pdf.py
=======================

Produce Checklist_collaudo_NNN.pdf — checklist A4 verticale (1 pagina) con:
- Sezione A: lista PF da collaudare (con box di spunta)
- Sezione B: lista punti di dettaglio da collaudare (con box di spunta)
- Spazio per Note di campagna

Tutti i punti vengono letti da dati_atto.md (prodotto da estrai-dati-atto-pregeo).

Esempio:
    python genera_checklist_pdf.py --dati-atto 03_OUTPUT/dati_atto.md \
        --id 121 --out 02_RILIEVO/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_dati_atto(md_path: Path) -> dict:
    out = {"pf": [], "dettaglio": [], "comune": "", "foglio": "", "particelle": ""}
    if not md_path.exists():
        return out
    text = md_path.read_text(encoding="utf-8", errors="replace")

    def grab(label: str) -> str:
        m = re.search(rf"^- {re.escape(label)}:\s*(.+)$", text, re.MULTILINE)
        if not m:
            return ""
        v = m.group(1).strip()
        return "" if v.upper() in ("N.D.", "N.A.") else v

    out["comune"]     = grab("Comune")
    out["foglio"]     = grab("Foglio")
    out["particelle"] = grab("Particelle oggetto")

    pf_str = grab("PF rilevati")
    if pf_str:
        out["pf"] = [p.strip() for p in pf_str.split(",") if p.strip()]

    det_str = grab("Punti di dettaglio")
    if det_str:
        out["dettaglio"] = [p.strip() for p in det_str.split(",") if p.strip()]

    return out


def costruisci_pdf(out_path: Path, atto_id: str, info: dict) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except ImportError:
        sys.exit("Serve reportlab (pip install reportlab).")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    W, H = A4
    c = canvas.Canvas(str(out_path), pagesize=A4)
    margin = 18 * mm

    # ----- Header -----
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, H - margin - 4*mm, f"CHECKLIST COLLAUDO  -  Atto {atto_id}")
    # Sottotitolo con dati catastali
    sub_parts = []
    if info.get("comune"):     sub_parts.append(f"Comune: {info['comune']}")
    if info.get("foglio"):     sub_parts.append(f"Foglio: {info['foglio']}")
    if info.get("particelle"): sub_parts.append(f"Particelle: {info['particelle']}")
    if sub_parts:
        c.setFont("Helvetica", 10); c.setFillColor(colors.grey)
        c.drawString(margin, H - margin - 11*mm, "  -  ".join(sub_parts))
        c.setFillColor(colors.black)

    # Linea separatrice
    c.setStrokeColor(colors.black); c.setLineWidth(0.6)
    c.line(margin, H - margin - 16*mm, W - margin, H - margin - 16*mm)

    y = H - margin - 24*mm

    # ----- Sezione A: PF -----
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "A. Punti Fiduciali")
    y -= 9*mm

    c.setFont("Helvetica", 12)
    box = 5*mm
    line_h = 9*mm
    pf_list = info.get("pf", []) or ["(nessun PF estratto da dati_atto.md)"]
    for nome in pf_list:
        c.setLineWidth(0.8)
        c.rect(margin, y - box + 1, box, box, stroke=1, fill=0)
        c.drawString(margin + box + 4*mm, y - box + 2.5*mm, nome)
        y -= line_h

    y -= 3*mm

    # ----- Sezione B: punti di dettaglio -----
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "B. Punti di dettaglio")
    y -= 9*mm

    c.setFont("Helvetica", 12)
    det_list = info.get("dettaglio", []) or ["(nessun punto di dettaglio estratto)"]
    for nome in det_list:
        c.setLineWidth(0.8)
        c.rect(margin, y - box + 1, box, box, stroke=1, fill=0)
        c.drawString(margin + box + 4*mm, y - box + 2.5*mm, nome)
        y -= line_h

    y -= 6*mm

    # ----- Sezione Note di campagna -----
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Note di campagna")
    y -= 8*mm

    # Righe orizzontali fino a ~25 mm dal fondo
    c.setStrokeColor(colors.lightgrey); c.setLineWidth(0.4)
    line_spacing = 9*mm
    while y > 25*mm:
        c.line(margin, y, W - margin, y)
        y -= line_spacing

    # Footer firma
    c.setFont("Helvetica", 9); c.setFillColor(colors.grey)
    c.drawString(margin, 14*mm,
                 "Firma tecnico collaudatore: ________________________________   "
                 "Data: ____ / ____ / ________")

    c.save()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Genera checklist collaudo PDF per la campagna.")
    ap.add_argument("--dati-atto", type=Path, default=None)
    ap.add_argument("--id", required=True)
    ap.add_argument("--out", type=Path, default=Path("."))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    info = parse_dati_atto(args.dati_atto) if args.dati_atto else {}
    out_path = args.out / f"Checklist_collaudo_{args.id}.pdf"
    costruisci_pdf(out_path, args.id, info)

    if not args.quiet:
        print(f"Checklist generata: {out_path}")
        print(f"  PF: {len(info.get('pf', []))}, dettaglio: {len(info.get('dettaglio', []))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
