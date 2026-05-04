---
name: pf-schede-downloader
description: >
  Usa questa skill ogni volta che l'utente vuole scaricare le schede monografiche
  dei Punti Fiduciali (PF) dal portale dell'Agenzia delle Entrate, a partire da
  file DXF catastali (anche di sistemi di coordinate diversi) e/o KML.
  La skill gestisce DXF in Gauss-Boaga Ovest (EPSG:3003) e UTM 32N (EPSG:32632),
  applica la correzione GPS da un punto di riferimento, filtra automaticamente
  i PF di primo perimetro rispetto alla particella di interesse, e scarica
  le schede monografiche PDF dal portale AdE in sequenza automatica.
  ATTIVA questa skill quando l'utente menziona: schede monografiche PF, download
  schede AdE, portale AdE punti fiduciali, monografiche catasto, scarica schede PF,
  primo perimetro, o quando ha DXF catastali e vuole le schede dei PF vicini a
  una particella.
---

# Scaricatore Schede Monografiche PF — Portale Agenzia delle Entrate

## Portale di riferimento

URL servizio: `https://www1.agenziaentrate.gov.it/servizi/Monografie/ricerca.php`

Il portale usa un cascade server-side: Provincia → Comune → Foglio → Lista PF → PDF.
Non è richiesto login.

---

## Script disponibili

| Script | Funzione |
|--------|----------|
| `scripts/merge_to_kml.py` | Unisce più DXF (Gauss-Boaga + UTM 32N), applica GPS offset, filtra per mappale |
| `scripts/download_from_kml.py` | Legge il KML, risolve Belfiore → Comune/Provincia, scarica le schede |
| `scripts/parse_input.py` | Estrae foglio e PF da KML + DXF (con filtro --mappale) |
| `scripts/download_schede.py` | Download singolo foglio (parametri manuali) |

---

## Flusso completo Claude Code

### Caso standard: più DXF + filtro particella

```bash
# Step 1 — Unisci i DXF e filtra i PF di primo perimetro della particella 206
python scripts/merge_to_kml.py \
  --dxf foglio4_gauss.dxf foglio_utm.dxf foglio5_gauss.dxf \
  --ref-dxf foglio4_gauss.dxf \
  --ref-pf "PF 3" \
  --ref-lat 45.330688 \
  --ref-lon 11.007967 \
  --mappale 206 \
  --output pf_p206.kml

# Step 2 — Scarica le schede (si apre il browser per ogni foglio)
python scripts/download_from_kml.py pf_p206.kml \
  --output ./schede_pf/
```

### Caso semplice: DXF singolo + tutti i PF

```bash
# Senza --mappale: produce KML con tutti i PF del foglio
python scripts/merge_to_kml.py \
  --dxf foglio.dxf \
  --ref-dxf foglio.dxf \
  --ref-pf "PF 3" \
  --ref-lat 45.330688 --ref-lon 11.007967 \
  --output tutti_pf.kml

python scripts/download_from_kml.py tutti_pf.kml --output ./schede/
```

### Verifica piano senza scaricare

```bash
python scripts/download_from_kml.py pf_p206.kml --dry-run
```

---

## Come funziona `merge_to_kml.py`

1. **Legge i DXF**: estrae PF dal layer FIDUCIALI di ogni file
2. **Rileva il sistema di coordinate** automaticamente dal valore dell'easting:
   - X > 1.400.000 → Gauss-Boaga Ovest (EPSG:3003) con Helmert → WGS84
   - X > 400.000 → UTM 32N (EPSG:32632) → WGS84
3. **Calcola l'offset GPS** dal PF di riferimento (correzione da ~100m a ~2-5m)
4. **Applica l'offset** identico a tutti i fogli (valido perché adiacenti)
5. **Filtro `--mappale`**: trova il testo del mappale nel layer PARTICELLE del DXF,
   poi usa l'algoritmo di copertura angolare per trovare i PF di primo perimetro
   (aggiunge PF dal più vicino in poi finché il gap angolare scende sotto 180°)
6. **Produce un KML unico** con tutti i PF selezionati, nome foglio incluso

## Come funziona `download_from_kml.py`

1. **Legge il KML**: estrae PF raggruppati per foglio (da nomi tipo "PF 3 (E349_000400)")
2. **Risolve il codice Belfiore** → Comune + Provincia (dataset comuni con cache locale)
3. **Per ogni gruppo**: apre il browser, naviga al portale AdE `www1`, esegue il cascade
   Provincia → Comune → Foglio → scarica i PDF
4. **Salva i PDF** come `scheda_PF{n}_fg{foglio}.pdf`

---

## Note operative

- `--ref-pf`, `--ref-lat`, `--ref-lon`: obbligatori per la correzione GPS
- `--provincia` e `--comune` NON servono: vengono risolti automaticamente dal Belfiore
- Il browser si apre in modalità visibile (default) — aggiungi `--headless` per nasconderlo
- Aggiungi `--slow 500` per rallentare e seguire il processo passo passo
- Il database comuni (7904 voci) viene scaricato una volta e salvato in cache:
  `references/codici_belfiore.json`
- I file di output NON vengono lasciati nel workspace — trasferire sul server e cancellare

---

## Gestione errori comuni

| Problema | Soluzione |
|----------|-----------|
| Mappale non trovato | Verifica il numero: potrebbe avere zeri iniziali nel DXF (es. "0206") |
| PF non disponibile nel portale | Il PF non ha scheda nell'archivio AdE — normale per PF vecchi |
| Timeout portale | Aumenta `--timeout 30` o riprova più tardi |
| Foglio non trovato nel dropdown | Il foglio potrebbe avere formato diverso (es. "4" vs "0004") |
| Download 0 schede | Controlla `debug_*.png` nella cartella output per vedere lo stato del browser |
