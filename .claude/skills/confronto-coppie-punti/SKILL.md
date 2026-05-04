---
name: confronto-coppie-punti
description: >
  Confronta le mutue distanze fra coppie omologhe di punti partendo da due file di coordinate
  (CSV/TXT/XLSX) — tipicamente rilievo del frazionamento approvato e contro-rilievo di collaudo.
  Riconosce i Punti Fiduciali (pattern PFnn/nnnn/Xnnn), applica le tolleranze (20 cm fra PF,
  5 cm fra dettaglio, 20 cm coppie miste) e produce un Excel con evidenziazione coppie fuori
  tolleranza + Markdown per la skill di compilazione report. Attivati quando l'utente chiede
  di confrontare coordinate fra due rilievi, calcolare mutue distanze, verificare il 10% dei
  punti di dettaglio, collaudare un atto di aggiornamento, o menziona "misure omologhe",
  "mutue distanze", "collaudo frazionamento", "controllo PF", "tolleranza catastale 20 cm".
---

# Confronto Coppie di Punti

## Scopo

Verifichi la correttezza di un atto di aggiornamento catastale (tipo mappale, frazionamento)
confrontando le mutue distanze fra coppie di punti calcolate dal rilievo di frazionamento
approvato e quelle calcolate dal rilievo di collaudo eseguito dallo studio.

Il protocollo prevede 3 PF + almeno 2 punti significativi dell'oggetto del rilievo
(stabilmente materializzati): la skill genera tutte le combinazioni a coppie e segnala
quali superano la tolleranza ammessa.

---

## Output prodotti da `scripts/compare_pairs.py`

1. **`Confronto_misurate_<nome_lavoro>.xlsx`** — archivio interno con quattro fogli:
   - **Coppie** — tabella completa con esiti, righe colorate verde/rosso
   - **Calcoli** — formule Excel live (ΔE/ΔN, dist=√(ΔE²+ΔN²), |Δ|, IF esito)
   - **Sintesi** — tolleranze applicate, riepilogo per tipo, totale e punti senza omologo
   - **Grafici** — bar |Δ| per coppia con soglie + bar % conformità per tipo

2. **`confronto_misurate.md`** — Markdown strutturato consumabile dalla skill di compilazione report

3. **`grafici/*.png`** — tre grafici a 180 dpi:
   - `delta_per_coppia.png` — bar chart |Δ| per coppia con linee soglie (verde/rosso OK/NOK)
   - `mappa_punti.png` — scatter Est/Nord con frazionamento (cerchi blu) e collaudo (croci rosse)
   - `conformita_per_tipo.png` — bar chart orizzontale % conformità per tipo coppia

---

## Quando attivarsi

Attivati quando l'utente:
- Carica due file di coordinate (CSV/TXT/XLSX) e chiede un confronto
- Menziona "misure omologhe", "mutue distanze", "verifica 10% punti di dettaglio"
- Menziona "collaudo frazionamento", "controllo atto di aggiornamento"
- Chiede esplicitamente la skill

**Non attivarti per:**
- Conversione singolo file coordinate → DXF (usa `coords-to-dxf`)
- Conversione libretto Pregeo (usa `pregeo-to-dxf`)
- Estrazione PF dal DXF catastale (usa `dxf-pf-extractor`)

---

## Input attesi

Due file di coordinate con quattro colonne: **Nome, Est, Nord, Quota**

- **File A** = rilievo del frazionamento approvato (chiamalo "frazionamento" nei report)
- **File B** = rilievo di collaudo eseguito dallo studio (chiamalo "collaudo")

Lo script auto-rileva:
- Separatore di colonna (`, ; tab spazio`)
- Separatore decimale (virgola italiana o punto)
- Presenza/assenza dell'header (alias riconosciuti: Nome|Punto|ID, Est|X|E, Nord|Y|N, Quota|Z|Q)

**Se non viene specificato quale file è il frazionamento e quale il collaudo, chiedi sempre conferma prima di lanciare — invertirli scambia le colonne nel report.**

---

## Tolleranze

| Tipologia coppia | Soglia | Razionale |
|-----------------|--------|-----------|
| PF ↔ PF | 0.20 m | Tolleranza planimetrica Istruzioni Pregeo / AdE per PF |
| Dettaglio ↔ Dettaglio | 0.05 m | Precisione attesa fra punti di dettaglio con stazione totale |
| PF ↔ Dettaglio (mista) | 0.20 m | Conservativa: incertezza PF si riverbera sulla mutua (configurabile via `--tol-mista`) |

---

## Flusso operativo

### Step 1 — Conferma input

Mostra i due file ricevuti e chiedi quale è il frazionamento approvato e quale è il collaudo.
Aspetta la conferma. Se il numero di punti differisce, mostra quanti punti hai trovato in ciascun file.

### Step 2 — Lancia lo script

```bash
python compare_pairs.py --file-a <frazionamento.csv> --file-b <collaudo.csv> \
    --nome <nome_lavoro> --out 03_OUTPUT/
```

Lo script:
1. Legge i due file e abbina i punti omologhi per nome esatto (case-insensitive)
2. Per ciascun file genera tutte le coppie n·(n−1)/2 e calcola la distanza planimetrica 2D
3. **La quota non è oggetto di collaudo catastale** — viene letta solo per validare la struttura, poi ignorata. Non comparirà nell'Excel né nel Markdown
4. Per ogni coppia calcola `|Δd| = |dist_frazionamento − dist_collaudo|` e applica la soglia
5. Riconosce un punto come PF se il nome rispetta `^PF\d+/\d+/[A-Z]\d+$` (es. `PF03/0050/F442`)
6. Se i nomi PF non rispettano il pattern, avvisa e propone `--pf-list` con lista esplicita
7. Salva Excel, Markdown e PNG nella cartella di output

### Step 3 — Riassumi e mostra l'output

Mostra una tabella sintetica:
- Numero coppie totali per tipo
- Numero NOK per tipo
- Max |Δ| per tipo
- Percentuale conformità complessiva

Linka i file prodotti. Se ci sono coppie NOK, riportale fattualmente — sarà il tecnico a
decidere se accettarle, scartarle o richiedere un nuovo rilievo.

### Step 4 — Scartati e avvisi

Se ci sono punti presenti in un solo file, elencali in "Punti senza omologo" e ricorda
che il calcolo li ha esclusi.

---

## Riferimenti

- `scripts/compare_pairs.py` — orchestratore principale: legge CSV, calcola coppie, scrive Markdown, invoca i moduli affiancati
- `scripts/_excel.py` — genera l'Excel con i 4 fogli
- `scripts/_viz.py` — genera i 3 PNG con matplotlib (dipendenza opzionale)

> ⚠️ **Testo originale troncato** — la sezione Riferimenti era incompleta. Se hai la versione
> completa in Cowork, aggiorna questo file con la parte mancante (note su matplotlib opzionale, ecc.).
