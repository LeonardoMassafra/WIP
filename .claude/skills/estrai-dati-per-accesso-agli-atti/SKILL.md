---
name: estrai-dati-per-accesso-agli-atti
description: >
  Estrae dati strutturati da visure catastali, atti notarili e documenti di identità
  presenti nella cartella PROJECTS, per le pratiche di accesso agli atti dello studio
  "Cattura la Realtà" di Leonardo Massafra. Supporta PDF nativi e scansioni (OCR).
  Usa questa skill quando l'utente dice "estrai i dati", "leggi i documenti della pratica",
  "prepara dati_estratti.md", "analizza i documenti in PROJECTS", oppure quando si deve
  compilare una richiesta accesso atti e i dati non sono ancora stati estratti.
---

# Skill: estrai-dati-per-accesso-agli-atti

Legge tutti i documenti nella cartella PROJECTS ed estrae i dati strutturati necessari
per la pratica, salvandoli in `OUTPUTS/dati_estratti.md`.

---

## Flusso operativo

### Step 1 — Identifica i documenti

Apri la cartella `PROJECTS` e individua:

- **Visura catastale** — file con "visura" nel nome o con contenuto catastale (foglio, mappale, rendita)
- **Atto notarile** — file con "atto", "rogito", "notarile" nel nome, o contenente repertorio e notaio
- **Documento di identità** — carta d'identità o patente del proprietario

Se non trovi un documento atteso, segnalalo prima di procedere.

### Step 2 — Estrai i dati

**Da visura catastale:**
- Comune
- Foglio
- Mappale (o Particella)
- Subalterno (se presente)
- Indirizzo unità immobiliare (se presente)

**Da atto notarile:**
- Nome e cognome del Notaio
- Numero di Repertorio
- Data dell'atto
- Estremi della registrazione (ufficio, data, numero)

**Da documento di identità:**
- Nome
- Cognome
- Data di nascita
- Luogo di nascita
- Indirizzo di residenza
- Codice Fiscale

### Step 3 — Gestione scansioni

Se il PDF non ha testo selezionabile, usa le capacità di visione per leggere il contenuto
dall'immagine (OCR visivo).

- Se un dato non è leggibile: scrivi `NON LEGGIBILE` nel campo corrispondente
- Segnala sempre i campi non leggibili nel riepilogo finale

### Step 4 — Salva l'output

Crea o sovrascrivi il file `OUTPUTS/dati_estratti.md` con questa struttura:

```markdown
# Dati estratti — [nome pratica] — [data]

## Dati catastali

Comune:
Foglio:
Mappale:
Subalterno:
Indirizzo:

## Dati atto notarile

Notaio:
Repertorio:
Data atto:
Registrazione:

## Dati proprietario

Nome:
Cognome:
Data di nascita:
Luogo di nascita:
Residenza:
Codice Fiscale:
```

Se ci sono più proprietari (comproprietà), aggiungi una sezione `## Dati proprietario 2`, ecc.

---

## Regole

- **NON inventare** dati non presenti nei documenti
- Se un campo non esiste nel documento, lascialo **vuoto** (non scrivere "N/A" o simili)
- Segnala sempre i dati illeggibili con `NON LEGGIBILE`
- Non salvare dati sensibili fuori dalla cartella `OUTPUTS`
- Dopo aver salvato `dati_estratti.md`, suggerisci di eseguire la skill `compilazione-modulo-accesso-atti` per compilare la richiesta

---

## Struttura cartelle attesa

```
[cartella commessa]/
├── PROJECTS/
│   ├── visura_catastale.pdf
│   ├── atto_notarile.pdf
│   └── documento_identita.pdf
└── OUTPUTS/
    └── dati_estratti.md   ← generato da questa skill
```
