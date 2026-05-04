# Coefficienti di Omogeneizzazione per Calcolo Superficie Commerciale

La **superficie commerciale** è la superficie convenzionale usata nella pratica estimativa italiana per esprimere il valore unitario €/m². Non coincide con la superficie catastale (DPR 138/98 allegato C) né con la superficie utile netta.

**Fonte:** Tecnoborsa — "Codice delle Valutazioni Immobiliari" italiano, versione più recente. Compatibile con IVS e prassi Borse Immobiliari delle Camere di Commercio.

**Leonardo può modificare liberamente questi valori in base all'esperienza locale.** Le modifiche saranno effettive dalla prossima esecuzione della skill.

---

## Tabella dei coefficienti standard

### Superfici principali

| Elemento | Coefficiente | Note |
|----------|--------------|------|
| Superficie interna principale (vani abitativi) | 100% | Riferimento |
| Muri perimetrali ed esterni | 100% se comuni / 50% se divisori | Inclusi se si parte dalla superficie catastale lorda |
| Muri divisori interni | 100% | Di norma già nella superficie lorda |

### Balconi, logge, terrazzi

| Elemento | Fino a 25 m² | Oltre 25 m² |
|----------|-------------|------------|
| Balconi aperti | 25% | 10% |
| Logge (aperte su un lato) | 35% | 10% |
| Logge coperte (aperte su due lati) | 30% | 10% |
| Verande chiuse | 60% | 35% |
| Terrazzi a livello di proprietà esclusiva | 35% | 10% |
| Terrazzi su copertura (attico) | 50% | 25% |
| Patio interno (scoperto, a quota del piano) | 35% | 15% |

### Spazi esterni

| Elemento | Fino a 25 m² | Oltre 25 m² |
|----------|-------------|------------|
| Giardino privato esclusivo | 15% | 10% |
| Cortile pavimentato privato esclusivo | 20% | 10% |
| Posto auto scoperto di proprietà | 20% | — |

### Pertinenze coperte

| Elemento | Coefficiente | Note |
|----------|--------------|------|
| Box auto singolo (C/6) | 50% | Standard |
| Box auto doppio o grande (>25 m²) | 35% | |
| Autorimessa comune (posto numerato) | 30% | |
| Cantina C/2 fino a 10 m² | 50% | |
| Cantina C/2 oltre 10 m² | 25% | |
| Soffitta praticabile (altezza >1,80 m) | 35% | |
| Soffitta non praticabile (altezza 1,20-1,80 m) | 15% | |
| Tettoie (C/7) | 30% | |

### Elementi speciali

| Elemento | Coefficiente | Note |
|----------|--------------|------|
| Seminterrato abitabile con agibilità | 60% | |
| Seminterrato accessorio (non abitabile) | 30% | |
| Piano terra con doppia altezza | 110-120% | La quota eccedente l'altezza standard |
| Mezzanino o soppalco abitabile | 70% | |

---

## Esempio di calcolo

**Immobile:** appartamento A/2 a Bovolone.

| Elemento | Superficie (m²) | Coefficiente | Superficie equivalente (m²) |
|----------|----------------|--------------|----------------------------|
| Interno principale | 105 | 100% | 105,00 |
| Balcone 1 | 8 | 25% | 2,00 |
| Balcone 2 | 6 | 25% | 1,50 |
| Terrazzo | 18 | 35% | 6,30 |
| Giardino (25 m² × 15% + 15 m² × 10%) | 40 | — | 5,25 |
| Box auto C/6 | 18 | 50% | 9,00 |
| Cantina C/2 | 6 | 50% | 3,00 |
| **TOTALE** | | | **132,05 m²** |

Superficie commerciale adottata: **132 m²**.

---

## Logica applicata dalla skill

1. Identifica gli elementi dichiarati nel file `04_caratteristiche/`
2. Applica i coefficienti della tabella, gestendo automaticamente le soglie (es. balcone 30 m² = 25 m² × 25% + 5 m² × 10%)
3. Somma tutte le superfici equivalenti
4. Nel report mostra la tabella di calcolo completa per garantire difendibilità della perizia

---

## Quando NON usare questi coefficienti

- **Uffici e commerciali (A/10, C/1, D/8):** si usa la "superficie lorda commerciale" (SLC) includendo i muri. La skill segnala e chiede conferma.
- **Capannoni e industriali (D/1, D/7):** superficie coperta lorda al 100%, spazi esterni a parte.
- **Agricoli (D/10):** valutazione reddituale — vedi nota in `coefficienti_merito.md`.

---

## Riferimenti normativi

- DPR 138/1998 allegato C — Superficie catastale
- Tecnoborsa — Codice delle Valutazioni Immobiliari
- IVS 105 Paragraph 80 — Measurement of property
- UNI 10750 — Prestazioni degli agenti immobiliari
- Linee guida ABI per perizie di mutuo
