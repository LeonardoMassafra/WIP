---
name: pregeo-to-dxf
description: Converte un Libretto Pregeo (Libretto delle Misure dell'Agenzia delle Entrate) in un file DXF nel sistema locale ENU del rilievo. Gestisce rilievi GPS puri, celerimetrici puri e misti (stazione totale appoggiata su punti GPS). Supporta tutti i formati di riga Pregeo (0, 1, 2, 4, 5, 6, 7, 9) inclusa la trilaterazione per punti da allineamento-squadro. Input accettato come file .dat (libretto nativo) o .pdf (Tipo Mappale, Frazionamento, Copia Libretto di Campagna - estrae automaticamente la sezione libretto da qualsiasi PDF AdE). Usa questa skill ogni volta che l'utente menziona libretto Pregeo, tipo mappale, frazionamento, file .dat Pregeo, rilievo GPS+celerimetrica da convertire in dxf, "libretto delle misure", "converti libretto in dxf", "da Pregeo a dxf", atto di aggiornamento cartografico, o carica un PDF con codice file PREGEO.
version: 1.0.0
---

# Convertitore Libretto Pregeo → DXF

Converte un libretto Pregeo (formato AdE) in file DXF nel sistema di riferimento locale ENU del rilievo.

## Attivazione

Questa skill si attiva quando l'utente:
- Chiede di convertire un libretto Pregeo in DXF
- Menziona "libretto delle misure", "tipo mappale", "frazionamento", "atto di aggiornamento"
- Fornisce un file `.dat` (libretto nativo Pregeo) o un `.pdf` AdE con "Codice file PREGEO"
- Parla di rilievi GPS/celerimetrici da trasformare in disegno CAD
- Menziona righe 1/2/4/5/7 di un libretto Pregeo

## Comportamento

### Input accettati
- **File `.dat`**: libretto nativo Pregeo (testo, righe che iniziano con `N|`)
- **File `.pdf`**: qualsiasi documento AdE che contiene il libretto (Tipo Mappale, Frazionamento, Copia Libretto di Campagna). Lo script estrae automaticamente le righe `N|` ignorando il boilerplate del PDF.

### Tipologie di rilievo supportate
1. **GPS puro**: base WGS84-ETRF2000 (riga 1 geocentrica) + vettori ΔX/ΔY/ΔZ in riga 2, trasformati in ENU locale sulla base.
2. **Celerimetrico puro**: stazioni (riga 1) + battute angolo/distanza in centesimali (riga 2, formato corto o lungo con zenit e h_prisma). Se non c'è riferimento GPS, la stazione va all'origine con orientamento Nord assunto.
3. **Misto**: stazioni totali appoggiate su punti GPS. L'orientamento (α) si calcola automaticamente usando la battuta più lunga verso un punto GPS noto.

### Righe 4/5 (allineamento-squadro / trilaterazione)
- Riga 4: `4|P1|P2|dislivello_cm|*S*|` — informazione 3D, ignorata per DXF 2D.
- Riga 5: `5|ID|distanza_radiale_m|DH|` — distanza dal punto P1 al punto nuovo.
- Con due misure reciproche (da P1 e da P2) → **trilaterazione 2D**.
- Lato corretto scelto automaticamente via contesto polilinea (riga 7): il punto deve creare una svolta concava coerente con l'orientamento CW/CCW del contorno.

### Output DXF
- Layer separati: `PREGEO_BASE_GPS`, `PREGEO_PUNTI_GPS`, `PREGEO_PUNTI_CEL`, `PREGEO_PUNTI_PF`, `PREGEO_PUNTI_ALL` (trilaterazione), `PREGEO_STAZIONI`, `PREGEO_CONTORNI`, `PREGEO_ETICHETTE`, `PREGEO_VETTORI_GPS`, `PREGEO_BATTUTE_CEL`.
- Sistema di riferimento: ENU locale (X=Est, Y=Nord, origine = stazione GPS base). Nessuna rototraslazione nel sistema catastale — le coordinate catastali di riga 8 sono ignorate intenzionalmente per evitare approssimazioni.
- Polilinee di contorno (riga 7): gestite anche le continuazioni su più righe (`7|N|...` + `7|0|...`).

## Come eseguire

Lo script principale è in `scripts/pregeo_to_dxf.py`.

Esecuzione da shell:
```bash
python "C:/Users/globalgeo/.claude/skills/pregeo-to-dxf/scripts/pregeo_to_dxf.py" <input.dat|.pdf> [output.dxf]
```

Se l'output non è specificato, viene salvato accanto al file di input con estensione `.dxf`.

Dipendenze Python (già installate nell'ambiente dell'utente):
- `ezdxf` — scrittura DXF
- `pymupdf` (importato come `fitz`) — estrazione testo da PDF

## Flusso consigliato

1. Identificare il file di input nel percorso indicato dall'utente (di solito cartella attuale o Desktop).
2. Eseguire lo script Python con il path del file come argomento.
3. Riportare all'utente:
   - Numero di punti calcolati (GPS, celerimetrici, allineamento-squadro)
   - Numero di polilinee di contorno
   - Eventuali avvisi (stazioni senza riferimento GPS, allineamenti con basi mancanti)
   - Path del DXF prodotto

## Note tecniche

- Per il rilievo misto, l'orientamento della stazione totale viene calcolato dalla battuta più lunga verso un punto GPS: `α = true_bearing(station→GPS_point) - measured_azimuth`.
- Per i punti da trilaterazione (righe 4/5), il lato LEFT/RIGHT della soluzione si sceglie in base all'orientamento della polilinea riga 7 che li contiene. Se il punto non è in nessuna polilinea, default LEFT.
- La base GPS geocentrica viene convertita in lat/lon via formula di Bowring (ECEF → geodetiche → ENU).
