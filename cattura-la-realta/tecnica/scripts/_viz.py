"""Funzioni di visualizzazione (matplotlib) per compare_pairs.py.

Modulo separato perché matplotlib è una dipendenza opzionale: se non è installato,
compare_pairs.py importa questo modulo in modo lazy e ricade su una versione
no-op che ritorna lista vuota. L'Excel rimane comunque generato.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from compare_pairs import Coppia, Punto


def genera_grafici_png(
    coppie,
    fraz,
    coll,
    out_dir: Path,
    tol_pf: float,
    tol_det: float,
    tol_mista: float,
) -> list[Path]:
    """Salva 3 PNG in <out_dir>/grafici/. Se matplotlib manca, ritorna []."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "[avviso] matplotlib non installato: salto la generazione dei PNG. "
            "Per averli: pip install matplotlib",
            file=sys.stderr,
        )
        return []

    grafici_dir = out_dir / "grafici"
    grafici_dir.mkdir(parents=True, exist_ok=True)
    salvati: list[Path] = []

    # 1) Bar chart |Δ| per coppia con linee soglia
    fig, ax = plt.subplots(figsize=(11, 6))
    coppie_ord = sorted(coppie, key=lambda c: -c.delta)
    labels = [f"{c.nome_a}\n{c.nome_b}" for c in coppie_ord]
    deltas = [c.delta for c in coppie_ord]
    colors = ["#5B9A3E" if c.esito == "OK" else "#C0392B" for c in coppie_ord]
    ax.bar(range(len(coppie_ord)), deltas, color=colors, edgecolor="white")
    ax.set_xticks(range(len(coppie_ord)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.axhline(tol_pf, ls="--", color="#1F4E79", lw=1.2,
               label=f"Soglia PF / mista ({tol_pf:.2f} m)")
    if abs(tol_det - tol_pf) > 1e-6:
        ax.axhline(tol_det, ls=":", color="#7F1D1D", lw=1.2,
                   label=f"Soglia Dettaglio ({tol_det:.2f} m)")
    ax.set_ylabel("|Delta| (m)")
    ax.set_title("Differenza fra mutue distanze - frazionamento vs collaudo")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, axis="y", ls="--", alpha=0.4)
    fig.tight_layout()
    p1 = grafici_dir / "delta_per_coppia.png"
    fig.savefig(p1, dpi=180)
    plt.close(fig)
    salvati.append(p1)

    # 2) Scatter dei punti su piano Est-Nord
    fig, ax = plt.subplots(figsize=(8, 8))
    fx = [p.est for p in fraz]
    fy = [p.nord for p in fraz]
    cx = [p.est for p in coll]
    cy = [p.nord for p in coll]
    ax.scatter(fx, fy, marker="o", s=110, label="Frazionamento",
               facecolor="#1F4E79", edgecolor="white", lw=1.4, zorder=3)
    ax.scatter(cx, cy, marker="x", s=110, label="Collaudo",
               c="#C0392B", lw=2.2, zorder=4)
    nomi_visti = set()
    for p in fraz:
        if p.nome in nomi_visti:
            continue
        nomi_visti.add(p.nome)
        ax.annotate(p.nome, (p.est, p.nord), xytext=(7, 7),
                    textcoords="offset points", fontsize=8,
                    color="#444", zorder=5)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("Est (m)")
    ax.set_ylabel("Nord (m)")
    ax.set_title("Geometria del rilievo - punti omologhi")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, ls="--", alpha=0.4)
    fig.tight_layout()
    p2 = grafici_dir / "mappa_punti.png"
    fig.savefig(p2, dpi=180)
    plt.close(fig)
    salvati.append(p2)

    # 3) Bar chart orizzontale % conformita per tipo
    tipi_ord = ["PF-PF", "PF-Det", "Det-Det"]
    label_tipi = ["PF - PF", "PF - Dettaglio", "Dettaglio - Dettaglio"]
    pcts: list[float] = []
    presenti: list[str] = []
    for t, lbl in zip(tipi_ord, label_tipi):
        sub = [c for c in coppie if c.tipo == t]
        if not sub:
            continue
        pct = sum(1 for c in sub if c.esito == "OK") / len(sub) * 100
        pcts.append(pct)
        presenti.append(lbl)

    fig, ax = plt.subplots(figsize=(8, max(3, 1 + 0.7 * len(presenti))))
    bar_colors = ["#5B9A3E" if v >= 99.99 else ("#E67E22" if v >= 80 else "#C0392B") for v in pcts]
    bars = ax.barh(presenti, pcts, color=bar_colors)
    for bar, pct in zip(bars, pcts):
        ax.text(min(pct + 1.5, 102), bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%", va="center", fontsize=10, color="#333")
    ax.set_xlim(0, 110)
    ax.set_xlabel("% conformita")
    ax.set_title("Conformita per tipo di coppia")
    ax.grid(True, axis="x", ls="--", alpha=0.4)
    fig.tight_layout()
    p3 = grafici_dir / "conformita_per_tipo.png"
    fig.savefig(p3, dpi=180)
    plt.close(fig)
    salvati.append(p3)

    return salvati
