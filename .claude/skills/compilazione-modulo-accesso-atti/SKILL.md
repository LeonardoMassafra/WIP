---
name: compilazione-modulo-accesso-atti
description: >
  Compila automaticamente il modulo di richiesta accesso agli atti comunali per lo studio
  "Cattura la Realtà" di Leonardo Massafra. Legge i dati estratti da dati_estratti.md
  (proprietario, atto notarile, immobile) e li inserisce nel template .docx
  RICHIESTA_ACCESSO_ATTI.docx. Usa questa skill quando l'utente dice "compila il modulo
  accesso atti", "richiesta accesso atti", "prepara la richiesta al comune",
  "compila la delega accesso atti", o quando è presente il file dati_estratti.md.
---

# Skill: compilazione-modulo-accesso-atti

Compila il modulo di richiesta accesso agli atti comunali partendo dai dati estratti,
producendo un .docx pronto per la firma e la consegna al comune.

---

## Flusso operativo

### Step 1 — Lettura dati

Leggi il file `OUTPUTS/dati_estratti.md` nella cartella di lavoro corrente.
Estrai i seguenti campi:
- **Proprietario/i:** nome, cognome, codice fiscale, indirizzo di residenza
- **Atto notarile:** numero repertorio, data, notaio, comune di rogito
- **Immobile:** comune, via/piazza, numero civico, foglio, mappale/particella, subalterno (se presente)

### Step 2 — Selezione proprietario (se multipli)

Se i dati_estratti.md contengono più proprietari (comproprietà):
- Elenca i proprietari trovati
- Chiedi all'utente quale usare come richiedente principale
- Attendi conferma prima di procedere

Se c'è un solo proprietario, prosegui direttamente.

### Step 3 — Apertura template

Apri il file `TEMPLATES/RICHIESTA_ACCESSO_ATTI.docx` con `python-docx`.

**VINCOLO ASSOLUTO:** NON creare un documento nuovo. Aprire sempre e solo il template esistente.
NON modificare font, dimensioni, struttura o formattazione del template.

### Step 4 — Compilazione campi

Compila i seguenti campi nel documento, cercando i segnaposto ([PLACEHOLDER]) e sostituendoli:

| Campo | Valore |
|-------|--------|
| Richiedente | Nome Cognome del proprietario scelto |
| Codice fiscale richiedente | CF del proprietario |
| Residenza richiedente | Indirizzo di residenza del proprietario |
| Atto notarile | "Rep. N° [numero], del [data], Notaio [nome notaio], [comune rogito]" |
| Immobile | "Comune di [comune], [via/piazza] [n. civico], fg. [foglio] mapp. [mappale/particella]" |
| Sezione CHIEDE | Precompilata: "copia degli atti relativi all'immobile sopra descritto" |
| Modalità ritiro | Da chiedere all'utente se non specificato (sportello / posta / PEC) |
| Delegato | **SEMPRE:** "Geom. Massafra Leonardo, tel. 3332702096" |
| Motivazioni | "per l'esercizio della professione di geometra — rilievo topografico e/o pratica catastale" |
| Data | Data odierna nel formato "Bovolone, lì [gg/mm/aaaa]" |

### Step 5 — Verifica campi vuoti

Prima di salvare, verifica che tutti i segnaposto siano stati sostituiti.
Se rimangono campi [PLACEHOLDER] non compilati, segnala quali sono e chiedi i valori mancanti.

### Step 6 — Salvataggio

Salva il documento compilato come:
`OUTPUTS/RICHIESTA_ACCESSO_ATTI_[COGNOME_PROPRIETARIO].docx`

dove `[COGNOME_PROPRIETARIO]` è il cognome del richiedente in MAIUSCOLO senza spazi o caratteri speciali.

### Step 7 — Conferma

Rispondi con:
- Percorso del file generato
- Riepilogo in 2-3 righe: richiedente, immobile, delegato
- Avviso se la firma è ancora da apporre fisicamente

---

## Vincoli

- **NON** creare un documento nuovo — aprire sempre il template
- **NON** modificare font, struttura o layout del template
- Il delegato è **SEMPRE** "Geom. Massafra Leonardo, tel. 3332702096" — non chiedere all'utente
- Il file di output va **SEMPRE** in `OUTPUTS/`, mai altrove
- Se `dati_estratti.md` non esiste, avvisa l'utente e suggerisci di eseguire prima la skill `estrai-dati-atto-pregeo`

---

## Struttura cartelle attesa

```
[cartella commessa]/
├── OUTPUTS/
│   ├── dati_estratti.md          ← input
│   └── RICHIESTA_ACCESSO_ATTI_COGNOME.docx  ← output generato
└── TEMPLATES/
    └── RICHIESTA_ACCESSO_ATTI.docx  ← template (non modificare)
```

---

## Dipendenze

- `python-docx` per la manipolazione del .docx
- Il file `dati_estratti.md` viene tipicamente prodotto dalla skill `estrai-dati-atto-pregeo`
