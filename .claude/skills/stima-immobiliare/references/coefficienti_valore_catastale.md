# Coefficienti Moltiplicatori per Calcolo Valore Catastale Teorico

Necessari per rilevare sospetti errori di compilazione del regime prezzo/valore (art. 1 c. 497 L. 266/2005).

## Formula base

```
Valore Catastale Teorico = Rendita Catastale × 1,05 × Coefficiente Categoria
```

- **Rendita Catastale**: valore iscritto in visura (€)
- **1,05**: rivalutazione 5% (L. 662/96 art. 3 c. 48)
- **Coefficiente Categoria**: varia per categoria e tipo acquirente

---

## Tabella dei coefficienti

### Prima casa (con benefici "prima casa")

| Categoria | Coefficiente |
|-----------|--------------|
| A (tranne A/10) — abitazioni | 110 |
| C/2, C/6, C/7 — pertinenze prima casa | 110 |

### Seconda casa o altri residenziali (senza agevolazioni)

| Categoria | Coefficiente |
|-----------|--------------|
| A (tranne A/10) — abitazioni | 120 |
| C/2, C/6, C/7 — pertinenze | 120 |

### Uffici

| Categoria | Coefficiente |
|-----------|--------------|
| A/10 | 60 |

### Negozi e laboratori

| Categoria | Coefficiente |
|-----------|--------------|
| C/1 — negozi | 40,8 |
| C/3 — laboratori artigianali | 120 |

### Immobili produttivi e industriali

| Categoria | Coefficiente |
|-----------|--------------|
| B (tutte tranne B/4) | 140 |
| D (tutti tranne D/5) | 60 |
| D/5 — istituti di credito | 60 |

### Altri

| Categoria | Coefficiente |
|-----------|--------------|
| E — immobili speciali | 34 |
| Terreni agricoli | 112,5 (su reddito dominicale rivalutato 25%) |
| Terreni edificabili | valore venale (no catastale) |

---

## Esempio di calcolo

Appartamento A/2, rendita 750 €, acquisto seconda casa:

```
Valore Catastale Teorico = 750 × 1,05 × 120 = 94.500 €
```

Se il corrispettivo dichiarato = 95.000 € → probabile errore (catastale inserito invece del reale). **FLAG 🔴**

---

## Logica del flag rosso

La skill applica FLAG 🔴 quando:

```
|corrispettivo_dichiarato − valore_catastale_teorico| / valore_catastale_teorico ≤ 0,10
```

Se entro ±10% dal catastale → sospetto. La skill non esclude mai automaticamente l'atto: segnala e lascia decidere al perito.

---

## Quando NON si applica

Il regime prezzo/valore vale solo per:
- Acquirenti **persone fisiche** non in esercizio d'impresa
- Immobili **residenziali** e pertinenze
- Transazioni **non soggette a IVA**

Per acquirenti società, immobili commerciali o transazioni IVA → flag disattivato automaticamente.

---

## Riferimenti normativi

- Art. 1 c. 497 L. 266/2005 — regime prezzo/valore
- L. 662/1996 art. 3 c. 48 — rivalutazione rendite 5%
- D.L. 223/2006 conv. L. 248/2006 — estensione regime
- Circolare AdE n. 6/E/2007 — chiarimenti applicativi
- Cassazione sent. 20501/2013 — irrilevanza errori formali
