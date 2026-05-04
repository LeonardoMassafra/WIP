---
name: dxf-pf-extractor
description: >
  Usa questa skill ogni volta che l'utente carica o menziona un file DXF di una
  mappa catastale italiana e vuole ottenere un file KML con le coordinate GPS dei
  Punti Fiduciali (PF) per navigare con Google Maps.
  La skill estrae automaticamente i PF dal layer FIDUCIALI del DXF, converte le
  coordinate da Gauss-Boaga Ovest (EPSG:3003) a WGS84, e produce un KML pronto
  per Google My Maps.
  ATTIVA questa skill ogni volta che l'utente menziona: DXF catastale, punti
  fiduciali da DXF, mappa catastale DXF, PF da DXF, coordinate PF, KML da
  catasto DXF, o carica un file .dxf dell'Agenzia delle Entrate.
---

# Estrattore Punti Fiduciali da DXF Catastale

## Contesto

I file DXF distribuiti dall'Agenzia delle Entrate (Catasto Nazionale) contengono
un layer chiamato `FIDUCIALI` con i Punti Fiduciali (PF) del foglio catastale.
Le coordinate sono in **Gauss-Boaga Ovest (EPSG:3003)**, non in WGS84.

L'obiettivo è produrre un file KML con coordinate WGS84 utilizzabili in
Google My Maps per navigare fisicamente fino ai PF sul campo.

---

## Pipeline

### Step 1 — Individua il file DXF

Il file DXF può essere:
- Caricato dall'utente nella cartella di lavoro
- Già presente nella cartella selezionata (es. `/sessions/.../mnt/...`)

Il nome del file tipicamente ha il formato `LXXX_YYYYZZ.dxf`:
- `LXXX` = codice ISTAT del Comune (es. `L949` = Villafranca di Verona)
- `YYYY` = numero foglio (es. `0016`)

### Step 2 — Esegui lo script di conversione (Passo 1: Helmert ~100m)

Prima individua il percorso dello script (varia in base alla sessione):

```bash
SCRIPT=$(find /sessions /home -name "dxf_to_kml.py" -path "*/dxf-pf-extractor/*" 2>/dev/null | head -1)
echo "Script trovato: $SCRIPT"
```

Poi eseguilo:

```bash
python3 "$SCRIPT" \
    "<percorso_file.dxf>" \
    --output "<percorso_output.kml>"
```

Lo script:
1. Legge il layer `FIDUCIALI` del DXF
2. Estrae nome e coordinate Gauss-Boaga di ogni PF
3. Converte in WGS84 con parametri Helmert 7 parametri (errore atteso ~100m)
4. Salva il KML

Mostra all'utente i PF trovati e le loro coordinate WGS84 approssimative.

### Step 3 — Chiedi il punto di riferimento GPS

Spiega all'utente:

> "Ho trovato N Punti Fiduciali e generato un KML con precisione ~100m,
> sufficiente per trovare la zona. Per arrivare a ~5m di precisione,
> dimmi le coordinate Google Maps di **uno solo** dei PF che hai già
> rilevato sul campo (o che sai dove si trova con certezza).
>
> Per trovare le coordinate su Google Maps: tieni premuto sul punto
> esatto → compare un segnaposto con le coordinate in basso.
>
> Quale PF vuoi usare come riferimento? E quali sono le sue coordinate?"

Se l'utente non ha ancora rilevato nessun PF fisicamente, puoi consegnare
il KML con precisione ~100m e ricordare che può migliorarla in seguito
con il comando del Passo 4.

### Step 4 — Applica la correzione GPS (se l'utente fornisce il riferimento)

Quando l'utente fornisce nome e coordinate GPS di un PF:

```bash
python3 "$SCRIPT" \
    "<percorso_file.dxf>" \
    --output "<percorso_output_corretto.kml>" \
    --ref-pf "PF 4" \
    --ref-lat 45.361801 \
    --ref-lon 10.836778
```

Lo script calcola l'offset tra la posizione Helmert del PF di riferimento
e le coordinate GPS reali, poi lo applica a tutti gli altri PF.
Precisione risultante: **~2-5m**.

### Step 5 — Consegna il KML

Salva il file KML nella cartella di lavoro dell'utente e presentalo con
`mcp__cowork__present_files` o con un link `computer://`.

Ricorda all'utente:
1. Aprire Google My Maps
2. Cliccare **Importa** nel layer desiderato
3. Caricare il file `.kml`

---

## Formato output KML

Il KML prodotto dallo script è già corretto. Ogni Placemark ha:
- **name**: `PF 1`, `PF 4`, ecc.
- **description**: coordinate Gauss-Boaga originali + WGS84 + nota sulla precisione
- **coordinates**: `longitudine,latitudine,0` (formato KML standard)

---

## Errori comuni e soluzioni

**"Nessun PF trovato nel layer FIDUCIALI"**
→ Il DXF potrebbe usare un nome layer diverso. Esegui questo snippet Python
per vedere tutti i layer presenti:
```python
with open('file.dxf', 'r', errors='replace') as f:
    content = f.read()
import re
layers = set(re.findall(r'(?<=\n 8\n)[^\n]+', content))
print(sorted(layers))
```
Adatta il filtro `'FIDUCIALI'` nel codice con il nome layer trovato.

**"PF di riferimento non trovato"**
→ Verifica che il nome corrisponda esattamente a quello mostrato dallo
script al Passo 2 (es. `"PF 4"` non `"PF4"` o `"pf4"`).

**Coordinate sembrano fuori dall'Italia**
→ Il DXF potrebbe essere in Gauss-Boaga Est (EPSG:3004, meridiano 15°E)
invece che Ovest. I valori East sarebbero ~2.5xx.xxx invece di ~1.6xx.xxx.
In questo caso modifica nel script: `LON0 = math.radians(15.0)` e `FE = 2_520_000.0`.

---

## Note tecniche

- **Sistema coordinate input**: Gauss-Boaga Ovest (EPSG:3003)
  - Ellissoide Hayford (a=6378388, f=1/297), Datum Roma40
  - Meridiano centrale 9°E, False Easting 1.500.000m, k0=0.9996
- **Trasformazione**: Helmert 7 parametri (EPSG:1074)
  - dx=-104.1, dy=-49.1, dz=-9.9m
  - rx=0.886", ry=-0.539", rz=0.679", s=-1.052ppm
- **Errore Helmert**: ~100m (per 10m serve griglia NTv2 IGM, non disponibile offline)
- **Errore con punto GPS**: ~2-5m (offset costante entro il foglio 2×2km)
