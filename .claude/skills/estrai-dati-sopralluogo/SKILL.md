---
name: estrai-dati-sopralluogo
description: >
  Gestisce il modulo di sopralluogo nel flusso di collaudo. Due modalità:
  GENERAZIONE (produce kit campagna: Excel precompilato + PDF stampabile + checklist PF)
  ed ESTRAZIONE (legge il modulo compilato e produce dati_sopralluogo.md).
  Attivati quando l'utente chiede "modulo sopralluogo", "kit campagna per l'atto N",
  "prepara il modulo per il 121", "estrai i dati del sopralluogo", o carica un file
  Modulo_Sopralluogo_*.xlsx.
---

# Estrai Dati Sopralluogo

## Scopo

Gestisci il modulo di sopralluogo nel flusso di collaudo. Quattro funzioni:

1. **Generazione modulo Excel** — produce `Modulo_Sopralluogo_NNN.xlsx` precompilato con i campi catastali letti da `dati_atto.md`, le sezioni vuote da compilare al rientro, e il default di strumentazione.
2. **Generazione PDF stampabile** — produce `Modulo_Sopralluogo_NNN_CAMPAGNA.pdf` (A4 orizzontale, 2 pagine) per essere stampato e compilato a penna in cantiere.
3. **Generazione checklist personalizzata** — produce `Checklist_collaudo_NNN.pdf` (A4 verticale, 1 pagina) con la lista esatta dei PF e dei punti di dettaglio da collaudare per quell'atto, letti dal `dati_atto.md`. Box di spunta per ciascuno e ampio spazio per Note di campagna.
4. **Estrazione dati** — quando l'utente ha compilato il modulo Excel al rientro, lo legge e produce `dati_sopralluogo.md` strutturato — fonte di verità per le skill di compilazione verbale e report.

**Quando l'utente chiede "preparami il modulo per il NNN" o "kit campagna per il NNN", la skill produce SEMPRE i tre file 1+2+3 (Excel + PDF modulo + checklist).**

---

## Quando attivarsi

| Trigger | Modalità |
|---------|----------|
| "preparami il modulo di sopralluogo per l'atto N" | GENERAZIONE (Excel + PDF + checklist) |
| "genera il modulo per il 121" / "kit campagna" | GENERAZIONE completa |
| "modulo da campagna" / "PDF stampabile" / "modulo cartaceo" | Solo PDF stampabile |
| "estrai i dati del sopralluogo" / "leggi il modulo compilato" | ESTRAZIONE |
| "il sopralluogo è pronto" | ESTRAZIONE |
| Carica file `Modulo_Sopralluogo_*.xlsx` | ESTRAZIONE automatica |

Se non riesci a inferire la modalità, chiedi:
> "Vuoi generare il modulo o estrarre i dati da uno già compilato?"

---

## Struttura del modulo Excel

### Foglio "DATI"
Tabella a due colonne (Campo / Valore):

| Campo | Compilazione |
|-------|-------------|
| Numero atto | Precompilato da CLI/cartella |
| Comune | Precompilato da `dati_atto.md` |
| Foglio | Precompilato da `dati_atto.md` |
| Particella oggetto | Precompilato da `dati_atto.md` |
| Data sopralluogo | Vuoto |
| Ora inizio | Vuoto |
| Ora fine | Vuoto |
| Strumentazione collaudo | Default: "Ricevitore GNSS marca e-Survey modello E300-Pro" |
| Tipo rilievo collaudo | Default: "GPS RTK" |
| Esito sintetico | Vuoto (scelta: Conforme / Non conforme / Da verificare) |
| Note generali | Vuoto, testo libero |

### Foglio "PARTECIPANTI"
Tre colonne, righe ripetibili: **Cognome e nome / Ruolo / Organizzazione**
Tutto vuoto — l'utente compilerà manualmente.

### Foglio "EVIDENZE"
Due colonne, righe ripetibili: **Argomento / Principali evidenze e azione conseguente**
Vuoto — il tecnico riempie un argomento per ogni questione emersa in cantiere.

---

## Flusso operativo

### Modalità GENERAZIONE

Esegui `scripts/genera_modulo.py`:

```bash
python genera_modulo.py --dati-atto 03_OUTPUT/dati_atto.md --id 121 --out 02_RILIEVO/
```

Lo script:
1. Parsifica `dati_atto.md` (regex su sezioni note) per estrarre Comune/Foglio/Particella
2. Crea il workbook con i 3 fogli, riempie i campi catastali nel foglio DATI
3. Mette i default su Strumentazione e Tipo rilievo
4. Salva `Modulo_Sopralluogo_NNN.xlsx` in `02_RILIEVO/`

### Modalità ESTRAZIONE

Esegui `scripts/extract_sopralluogo.py`:

```bash
python extract_sopralluogo.py --modulo 02_RILIEVO/Modulo_Sopralluogo_121.xlsx --out 03_OUTPUT/
```

Lo script:
1. Apre il workbook con `openpyxl`
2. Legge il foglio DATI come dizionario campo→valore
3. Legge PARTECIPANTI ed EVIDENZE come liste di dict
4. Genera `dati_sopralluogo.md` con sezioni: Identificazione, Sopralluogo, Strumentazione e rilievo, Partecipanti, Evidenze emerse, Note generali, File di origine
5. Per ogni campo vuoto scrive `N.D.` — non inventa, non integra

---

## Output — dati_sopralluogo.md

```markdown
# Dati Sopralluogo — Atto NNN

## Identificazione
- Numero atto: NNN
- Comune: [valore]
- Foglio: [valore]
- Particella: [valore]

## Sopralluogo
- Data: [valore]
- Ora inizio: [valore]
- Ora fine: [valore]
- Esito sintetico: [Conforme / Non conforme / Da verificare]

## Strumentazione e rilievo
- Strumentazione: [valore]
- Tipo rilievo: [valore]

## Partecipanti
| Cognome e nome | Ruolo | Organizzazione |
|----------------|-------|----------------|
| [...]          | [...] | [...]          |

## Evidenze emerse
| Argomento | Principali evidenze e azione conseguente |
|-----------|------------------------------------------|
| [...]     | [...]                                    |

## Note generali
[valore o N.D.]

## File di origine
- Modulo: Modulo_Sopralluogo_NNN.xlsx
```

---

## Note

> ⚠️ **Testo originale incompleto** — la skill è stata importata con il testo troncato
> alla fine della sezione Estrazione. Se hai la versione completa in Cowork, aggiorna
> questo file con la parte mancante (regole N.D., gestione errori, ecc.).
