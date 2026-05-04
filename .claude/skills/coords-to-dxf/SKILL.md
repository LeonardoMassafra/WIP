---
name: coords-to-dxf
description: Converte un file di coordinate topografiche (CSV, TXT, XLSX) in un file DXF con simbolo a crocetta su layer PUNTI, etichetta del nome su layer NOMI, e valore Z su layer QUOTE. Rileva automaticamente il separatore di colonna (virgola/punto e virgola/tab/spazio) e il separatore decimale (virgola italiana o punto). Riconosce header con nomi colonna tipo "Nome, Nord, Est, Quota" oppure "Nome, X, Y, Z" mappando correttamente le convenzioni topografica (Y=Nord) e matematica (X=Est). Se non c'è header, assume l'ordine Nome,X,Y,Z con avviso. Usa questa skill ogni volta che l'utente chiede di convertire un file di coordinate in dxf, o menziona: file csv di punti, file txt con coordinate, xlsx punti topografici, "converti le coordinate in dxf", "importa i punti in dxf", "nord est quota", rilievo in coordinate piane, picchetti, capisaldi, punti quotati, esportare punti per CAD. NON usare per libretti Pregeo (usare pregeo-to-dxf).
version: 1.0.0
---

# Convertitore File Coordinate → DXF

Converte un file di coordinate (piane 2D o 2D+quota) in un file DXF con simboli a crocetta, nomi e quote su layer separati.

## Attivazione

Questa skill si attiva quando l'utente:
- Fornisce un file `.csv`, `.txt`, `.xls` o `.xlsx` contenente coordinate topografiche
- Chiede di "convertire coordinate in dxf", "importare punti in dxf", "creare dxf da file di punti"
- Menziona colonne tipo "Nord, Est, Quota" o "X, Y, Z" da disegnare
- Vuole trasformare un elenco di punti quotati in disegno CAD

**Non** attivare per libretti Pregeo (usa `pregeo-to-dxf`).

## Comportamento

### Input accettati
- **CSV/TXT**: separatore colonna auto-rilevato fra `;`, `,`, tab, spazi.
- **XLSX/XLS**: legge la prima sheet.
- Separatore decimale auto-rilevato (punto oppure virgola italiana).

### Struttura colonne riconosciute
- Con header: mappa keyword → ruolo colonna
  - `Nome`, `Name`, `ID`, `Punto`, `Pt`, `Num` → NOME
  - `Nord`, `Northing`, `N`, `Y` → Y
  - `Est`, `Easting`, `E`, `X` → X
  - `Quota`, `Z`, `H`, `Elev`, `Altitude` → Z
  - Gestisce sia convenzione topografica italiana (Nord/Est) sia matematica (X/Y)
- Senza header: assume ordine `Nome, X, Y, Z` (con avviso esplicito in output)
- Z è opzionale (3 colonne è sufficiente per 2D)

### Output DXF
- **Layer `PUNTI`** (colore giallo): INSERT del blocco `CROCE` (cerchio + crocetta al centro) in ogni posizione punto
- **Layer `NOMI`** (bianco): etichetta testuale col nome del punto
- **Layer `QUOTE`** (verde): valore Z come testo, solo per punti quotati
- Dimensione simboli auto-dimensionata in base al bbox (range 0.1-1.0 m di raggio)

## Come eseguire

Script in `scripts/coords_to_dxf.py`.

Esecuzione da shell:
```bash
python "C:/Users/globalgeo/.claude/skills/coords-to-dxf/scripts/coords_to_dxf.py" <input.csv|.txt|.xlsx> [output.dxf]
```

Se l'output non è specificato, esce con estensione `.dxf` accanto all'input.

Dipendenze Python (installate):
- `ezdxf` — scrittura DXF
- `openpyxl` — lettura XLSX

## Flusso consigliato

1. Identificare il file di input indicato dall'utente.
2. Eseguire lo script.
3. Riportare in modo conciso:
   - Formato rilevato (separatore colonna, decimale)
   - Se l'header è stato riconosciuto (e mapping colonna → ruolo)
   - Numero di punti importati, range X/Y/Z
   - Path del DXF prodotto

## Esempi di file accettati

**CSV italiano** (separatore `;`, decimali virgola, header Nord/Est/Quota):
```
Nome;Nord;Est;Quota
P1;10000,123;5000,456;125,30
P2;10015,877;5002,120;125,42
```

**TXT senza header** (separatore spazio, decimali punto):
```
P1 5000.456 10000.123 125.30
P2 5002.120 10015.877 125.42
```

**XLSX** con colonne X/Y/Z (quota opzionale per alcuni punti).

## Note

- Il simbolo CROCE è un blocco DXF riutilizzabile (non linee indipendenti): può essere selezionato/spostato/scalato come singola entità in CAD.
- I punti senza quota appaiono solo su layer PUNTI e NOMI, non su QUOTE (coerente con "Z su layer separato" richiesto dall'utente).
