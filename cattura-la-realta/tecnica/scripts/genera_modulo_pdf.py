#!/usr/bin/env python3
"""
genera_modulo_pdf.py
====================

Produce un Modulo_Sopralluogo_NNN_CAMPAGNA.pdf — versione cartacea
stampabile A4 orizzontale, pensata per essere compilata a penna in
cantiere e poi trasferita nel modulo Excel al rientro in studio.

Esempio:
    python genera_modulo_pdf.py --dati-atto 03_OUTPUT/dati_atto.md \
        --id 121 --out 02_RILIEVO/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_STRUMENTO = "Ricevitore GNSS marca e-Survey modello E300-Pro"
DEFAULT_TIPO_RILIEVO = "GPS RTK"


def parse_dati_atto(md_path: Path) -> dict:
    out = {"comune": "", "foglio": "", "particelle": "",
           "tipo_atto": "", "codice_pregeo": ""}
    if not md_path.exists():
        return out
    text = md_path.read_text(encoding="utf-8", errors="replace")

    def grab(label: str) -> str:
        m = re.search(rf"^- {re.escape(label)}:\s*(.+)$", text, re.MULTILINE)
        if not m:
            return ""
        v = m.group(1).strip()
        return "" if v.upper() in ("N.D.", "N.A.") else v

    out["comune"]        = grab("Comune")
    out["foglio"]        = grab("Foglio")
    out["particelle"]    = grab("Particelle oggetto")
    out["tipo_atto"]     = grab("Tipo atto")
    out["codice_pregeo"] = grab("Codice file PREGEO")
    return out


def costruisci_pdf(out_path: Path, atto_id: str, info: dict) -> None:
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except ImportError:
        sys.exit("Serve reportlab (pip install reportlab).")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    W, H = landscape(A4)  # orizzontale ~ 297x210
    c = canvas.Canvas(str(out_path), pagesize=landscape(A4))

    margin = 12 * mm

    # ---------- Pagina 1 ----------
    # Titolo
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, H - margin - 4*mm, f"MODULO SOPRALLUOGO  -  Atto {atto_id}")
    c.setFont("Helvetica", 9)
    c.drawString(margin, H - margin - 9*mm,
                 "Compila a penna durante il sopralluogo. Trasferisci poi nel modulo Excel al rientro.")

    # Riquadro Identificazione (precompilato)
    y = H - margin - 18*mm
    box_h = 30*mm
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    c.rect(margin, y - box_h, W - 2*margin, box_h, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, y - 5*mm, "IDENTIFICAZIONE ATTO  (precompilato)")

    # 4 colonne per dati identificativi
    col_w = (W - 2*margin) / 4
    rows_id = [
        ("Numero atto", atto_id),
        ("Tipo atto", info.get("tipo_atto") or "-"),
        ("Codice PREGEO", info.get("codice_pregeo") or "-"),
        ("Foglio", info.get("foglio") or "-"),
    ]
    for i, (label, val) in enumerate(rows_id):
        x = margin + i * col_w + 2*mm
        c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
        c.drawString(x, y - 11*mm, label)
        c.setFont("Helvetica-Bold", 11); c.setFillColor(colors.black)
        c.drawString(x, y - 17*mm, str(val))

    rows_id2 = [("Comune", info.get("comune") or "-"),
                ("Particelle oggetto", info.get("particelle") or "-")]
    for i, (label, val) in enumerate(rows_id2):
        x = margin + i * col_w * 2 + 2*mm
        c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
        c.drawString(x, y - 22*mm, label)
        c.setFont("Helvetica-Bold", 11); c.setFillColor(colors.black)
        c.drawString(x, y - 28*mm, str(val))

    # Riquadro Sopralluogo (da compilare)
    y2 = y - box_h - 4*mm
    box_h2 = 22*mm
    c.rect(margin, y2 - box_h2, W - 2*margin, box_h2, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, y2 - 5*mm, "SOPRALLUOGO  (compila a penna)")

    label_y = y2 - 11*mm
    line_y  = y2 - 18*mm
    fields = [("Data", 50*mm), ("Ora inizio", 35*mm),
              ("Ora fine", 35*mm), ("Esito sintetico", W - 2*margin - 50 - 35 - 35 - 4)]
    cx = margin + 2*mm
    for label, w in fields:
        c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
        c.drawString(cx, label_y, label)
        c.setStrokeColor(colors.grey); c.setLineWidth(0.4)
        c.line(cx, line_y, cx + w*mm if isinstance(w, int) and w < 1000 else cx + w, line_y)
        cx += (w*mm if isinstance(w, int) and w < 1000 else w) + 5*mm

    # Riquadro Strumentazione (precompilato con default)
    y3 = y2 - box_h2 - 4*mm
    box_h3 = 16*mm
    c.setFillColor(colors.HexColor("#FFF7D6"))
    c.rect(margin, y3 - box_h3, W - 2*margin, box_h3, stroke=1, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, y3 - 5*mm,
                 "STRUMENTAZIONE E TIPO RILIEVO  (default: barra e modifica se diverso)")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 2*mm, y3 - 11*mm, f"Strumentazione: {DEFAULT_STRUMENTO}")
    c.drawString(margin + 2*mm, y3 - 15*mm, f"Tipo rilievo: {DEFAULT_TIPO_RILIEVO}")

    # Riquadro Partecipanti (5 righe scrivibili)
    y4 = y3 - box_h3 - 4*mm
    n_rows_p = 5
    row_h = 8*mm
    box_h4 = (n_rows_p + 1) * row_h
    c.rect(margin, y4 - box_h4, W - 2*margin, box_h4, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, y4 - 5*mm, "PARTECIPANTI")
    # header
    col_p_w = [(W - 2*margin) * 0.35, (W - 2*margin) * 0.30, (W - 2*margin) * 0.35]
    headers = ["Cognome e nome", "Ruolo", "Organizzazione"]
    cy = y4 - row_h
    cx = margin
    c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.grey)
    for i, h in enumerate(headers):
        c.drawString(cx + 2*mm, cy - 3*mm, h)
        cx += col_p_w[i]
    c.setFillColor(colors.black)
    # righe
    for r in range(n_rows_p):
        ry = cy - (r+1) * row_h
        c.setStrokeColor(colors.lightgrey); c.setLineWidth(0.3)
        c.line(margin, ry, W - margin, ry)
        cx = margin
        for w in col_p_w[:-1]:
            cx += w
            c.line(cx, ry, cx, ry + row_h)

    c.showPage()

    # ---------- Pagina 2 ----------
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, H - margin - 4*mm, f"EVIDENZE EMERSE  -  Atto {atto_id}")

    # Tabella evidenze (8 righe)
    n_rows_e = 8
    row_h_e = 18*mm
    col_e_w = [(W - 2*margin) * 0.30, (W - 2*margin) * 0.70]
    headers_e = ["Argomento", "Principali evidenze e azione conseguente"]
    ye = H - margin - 14*mm
    cx = margin
    c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.grey)
    for i, h in enumerate(headers_e):
        c.drawString(cx + 2*mm, ye - 5*mm, h)
        cx += col_e_w[i]
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black); c.setLineWidth(0.5)
    c.line(margin, ye, W - margin, ye)

    for r in range(n_rows_e):
        ry = ye - (r+1) * row_h_e
        c.setStrokeColor(colors.lightgrey); c.setLineWidth(0.3)
        c.line(margin, ry, W - margin, ry)
        c.line(margin + col_e_w[0], ry, margin + col_e_w[0], ry + row_h_e)

    # Box Note generali
    yn = ye - n_rows_e * row_h_e - 4*mm
    box_note_h = H - margin - yn - n_rows_e * row_h_e - 14*mm - 4*mm
    box_note_h = max(box_note_h, 20*mm)
    c.setStrokeColor(colors.black); c.setLineWidth(0.5)
    c.rect(margin, yn - box_note_h, W - 2*margin, box_note_h, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, yn - 5*mm, "NOTE GENERALI")

    c.save()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Genera modulo sopralluogo PDF stampabile.")
    ap.add_argument("--dati-atto", type=Path, default=None)
    ap.add_argument("--id", required=True)
    ap.add_argument("--out", type=Path, default=Path("."))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    info = parse_dati_atto(args.dati_atto) if args.dati_atto else {}
    out_path = args.out / f"Modulo_Sopralluogo_{args.id}_CAMPAGNA.pdf"
    costruisci_pdf(out_path, args.id, info)

    if not args.quiet:
        print(f"PDF campagna generato: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
