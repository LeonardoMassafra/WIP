# Cost Approach — Costi di ricostruzione e deprezzamento

Riferimento per il calcolo del valore con approccio al costo (Cost Approach — IVS 105 §60-80).

**Leonardo può aggiornare i costi con i dati del Prezzario Regionale Veneto** (annuale). I valori sono indicativi di letteratura, da calibrare sul mercato locale.

---

## Formula generale

```
V_cost = V_terreno + (C_ricostruzione × S_lorda × K_deprezzamento)
```

- **V_terreno** = valore del suolo edificabile (da OMI terreni o dichiarazione perito)
- **C_ricostruzione** = costo di ricostruzione a nuovo al m² lordo (incluse spese tecniche, oneri, IVA)
- **S_lorda** = superficie lorda (comprensiva di muri perimetrali)
- **K_deprezzamento** = coefficiente residuo (da 0 a 1, dove 1 = nuovo)

---

## Costi di ricostruzione a nuovo (€/m² lordo)

Valori inclusi strutture, finiture, impianti, spese tecniche (10%), oneri e allacciamenti. IVA esclusa.
**Aggiornamento: 2025. Fonte: DEI, Prezzari Regionali, ISTAT.**

### Residenziale

| Tipologia | Fascia bassa | Fascia media | Fascia alta | Note |
|-----------|-------------|-------------|------------|------|
| Economico (A/3, A/4) | 900 | 1.100 | 1.300 | Finiture standard |
| Civile (A/2) | 1.100 | 1.350 | 1.600 | Finiture medie |
| Signorile (A/1) | 1.400 | 1.700 | 2.100 | Finiture di pregio |
| Villini (A/7) | 1.200 | 1.500 | 1.800 | Include sistemazioni esterne |
| Ville (A/8) | 1.500 | 1.900 | 2.500 | Parco, finiture pregio |
| Rurale (A/6) | 700 | 900 | 1.100 | Struttura semplice |

### Commerciale e terziario

| Tipologia | Fascia bassa | Fascia media | Fascia alta |
|-----------|-------------|-------------|------------|
| Negozi (C/1) | 800 | 1.050 | 1.300 |
| Uffici (A/10) | 1.000 | 1.250 | 1.500 |
| Laboratori (C/3) | 600 | 800 | 1.000 |
| Alberghi (D/2) | 1.200 | 1.600 | 2.200 |

### Produttivo e industriale

| Tipologia | Fascia bassa | Fascia media | Fascia alta | Note |
|-----------|-------------|-------------|------------|------|
| Capannone prefabbricato (D/7) | 350 | 500 | 700 | Struttura prefab. mono-piano |
| Capannone tradizionale (D/1, D/7) | 500 | 700 | 950 | Struttura c.a./acciaio |
| Opificio con uffici integrati (D/1) | 700 | 900 | 1.200 | Parte produttiva + direzionale |

### Agricolo

| Tipologia | Fascia bassa | Fascia media | Fascia alta |
|-----------|-------------|-------------|------------|
| Fabbricato rurale (D/10) | 300 | 500 | 700 |
| Stalla/rimessa agricola | 250 | 400 | 550 |

### Pertinenze

| Tipologia | Fascia bassa | Fascia media | Fascia alta |
|-----------|-------------|-------------|------------|
| Box auto (C/6) | 400 | 550 | 750 |
| Cantina/magazzino (C/2) | 300 | 450 | 600 |

---

## Scelta della fascia

| Situazione | Fascia |
|-----------|--------|
| Classe 1-2 (bassa) + stato mediocre/da ristrutturare | Bassa |
| Classe 3-4 (media) + stato buono | Media |
| Classe 5+ (alta) + stato ottimo/nuovo | Alta |
| Mancano classe o stato | Media (default) |

---

## Deprezzamento — Metodo Ross-Heidecke

### 1. Deprezzamento per età (formula di Ross)

```
D_età = 0,5 × (a/n + (a/n)²)
```

- **a** = età in anni (anno corrente − anno costruzione, o − anno ultima ristrutturazione integrale)
- **n** = vita utile economica (vedi tabella)

### 2. Vita utile economica per tipologia

| Tipologia | Vita utile (anni) |
|-----------|------------------|
| Residenziale civile (A/2, A/3) | 80 |
| Residenziale signorile (A/1, A/7, A/8) | 100 |
| Residenziale economico/popolare (A/4, A/5) | 60 |
| Negozi e uffici (A/10, C/1) | 60 |
| Capannoni prefabbricati (D/7 prefab) | 40 |
| Capannoni tradizionali (D/1, D/7 c.a.) | 50 |
| Agricoli (D/10) | 40 |
| Box auto e pertinenze (C/6, C/2) | 60 |

### 3. Coefficiente di stato (Heidecke)

| Grado | Stato | Fattore Heidecke |
|-------|-------|-----------------|
| 1 | Nuovo / ristrutturato integralmente recente | 0,00 |
| 1,5 | Ottimo, ben mantenuto | 0,032 |
| 2 | Buono, normale manutenzione | 0,052 |
| 2,5 | Regolare, qualche difetto minore | 0,088 |
| 3 | Mediocre, interventi necessari | 0,182 |
| 3,5 | Cattivo, interventi urgenti | 0,264 |
| 4 | Pessimo, da ristrutturare | 0,346 |
| 4,5 | Inagibile, degrado grave | 0,520 |
| 5 | Rudere / demolire | 0,700 |

### 4. Formula complessiva

```
K_deprezzamento = (1 - D_età) × (1 - Heidecke)
```

### 5. Esempio completo

**Appartamento A/2, costruito 1980, stato buono (grado 2), anno valutazione 2026:**

```
Età: 46 anni | Vita utile: 80 anni
D_età = 0,5 × (0,575 + 0,331) = 0,453
Heidecke (grado 2) = 0,052
K = (1 − 0,453) × (1 − 0,052) = 0,547 × 0,948 = 0,519

Costo ricostruzione (fascia media): 1.350 €/m²
Superficie lorda (catastale +15%): 95 m²
Fabbricato deprezzato: 1.350 × 95 × 0,519 = 66.550 €
Terreno: 25.000 €
VALORE COST APPROACH: 91.550 €
```

---

## Valore del terreno

Ordine di preferenza:

1. **Quotazioni OMI terreni edificabili** (dal CSV Quotazioni, se disponibili)
2. **Incidenza % sul valore Market Approach** (default se mancano dati migliori):
   - Centro (fascia B): 30-40%
   - Semicentro (fascia C): 20-30%
   - Periferia (fascia D): 15-25%
   - Rurale (fascia R): 10-15%
   - Industriale: 15-25%
3. **Dichiarazione del perito** nel file caratteristiche

---

## Quando il Cost Approach è PRIMARIO

La skill riconosce automaticamente questi casi:

| Situazione | Motivazione |
|-----------|-------------|
| D/1, D/7 con <5 comparables | Comparables insufficienti |
| D/10 (agricolo) | Mercato illiquido |
| Gruppo E, B (speciali) | Nessun comparabile possibile |
| Stato "da ristrutturare" o "rudere" | Valore = Cost post-ristrut. − costo lavori |
| Nuova costruzione (<5 anni) | Cost è il cross-check più affidabile |

In questi casi il report dichiara esplicitamente perché il Cost Approach è primario.

---

## Note per Leonardo

I valori sono medi nazionali. Per il Veneto/bassa veronese, aggiorna con:
- **Prezzario Regionale del Veneto** (annuale, sito Regione Veneto)
- **Camera di Commercio di Verona** — rilevazioni costi di costruzione
- **DEI — Tipografia del Genio Civile** — pubblicazione annuale

Modifica direttamente questa tabella. Le modifiche saranno effettive dalla prossima esecuzione della skill.
