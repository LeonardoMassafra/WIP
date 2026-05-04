---
name: estrai-dati-atto-pregeo
description: >
  Estrae i dati strutturati da un PDF di atto di aggiornamento catastale italiano
  (Tipo Mappale, Frazionamento, Particellare) prodotto dall'Agenzia delle Entrate via Pregeo.
  Produce dati_atto.md con identificazione, dati catastali, intestatari, firmatari, tecnico
  redattore, rilievo (strumento, PF, punti dettaglio), geometria e note. È il primo step
  della pipeline di collaudo CEPAV/IRICAV/A4 Holding. Attivati quando l'utente carica un
  PDF AdE con codice PREGEO o diciture TIPO MAPPALE / TIPO FRAZIONAMENTO / TIPO PARTICELLARE,
  o menziona "estrai dati atto", "leggi PDF Pregeo", "dati catastali da atto di aggiornamento",
  o inizia un nuovo collaudo.
---

# Estrai Dati Atto Pregeo

## Scopo

Trasformi un PDF di atto di aggiornamento catastale (rilasciato dall'Agenzia delle Entrate
dopo la lavorazione Pregeo) in un Markdown strutturato `dati_atto.md` che le skill successive
useranno come fonte unica di verità per il singolo atto.

**Output:** `<out_dir>/dati_atto.md` — file Markdown con sezioni fisse:
Identificazione, Dati catastali, Estratto di mappa, Operazioni catastali, Intestatari,
Firmatari, Tecnico redattore, Rilievo, Geometria del frazionamento, Parametri di
rappresentazione, Note dalla relazione tecnica, File di origine.

---

## Quando attivarsi

Attivati ogni volta che l'utente:
- Carica un PDF con le diciture "TIPO MAPPALE", "TIPO FRAZIONAMENTO", "TIPO PARTICELLARE", o "Atto di Aggiornamento" + "Codice file PREGEO"
- Chiede di "estrarre i dati dell'atto", "leggere il PDF del frazionamento", "preparare il sopralluogo per l'atto N"
- Inizia un nuovo collaudo per la commessa CEPAV/IRICAV/A4 Holding con PDF dell'atto da collaudare

**Non attivarti** per visure catastali o atti notarili — per quelli c'è la skill `estrai-dati-per-accesso-agli-atti`.

---

## Input attesi

Un singolo PDF nativo (testo selezionabile) prodotto dall'Agenzia delle Entrate, di una di queste tipologie:
- **TIPO MAPPALE** — ampliamento o demolizione fabbricato
- **TIPO FRAZIONAMENTO** — divisione di una particella in due o più
- **TIPO PARTICELLARE** — variante di confine senza coinvolgere fabbricati

Il PDF contiene, in ordine variabile: pagine di autodichiarazioni, informazioni generali,
informazioni censuarie, informazioni geometriche, libretto delle misure, relazione tecnica,
schema del rilievo, sviluppo.

Il parser non assume un ordine fisso: estrae usando ancore testuali ("Codice file PREGEO:",
"Comune:", "DITTA", riga `0|` del libretto, ecc.).

Se il PDF è una scansione (testo non selezionabile), lo script segnala l'errore.

---

## Flusso operativo

### Step 1 — Identifica il file

Se l'utente carica un PDF e l'identificazione del tipo atto fallisce (non trovi PREGEO o
le diciture standard), chiedi conferma:
> "Questo PDF è un atto di aggiornamento Pregeo?"

Procedi solo dopo conferma.

### Step 2 — Lancia lo script

```bash
python extract_atto.py --pdf <path-pdf> --id 121 --out 03_OUTPUT/
```

L'identificativo (`--id`) è il numero della cartella che contiene l'atto (es. `121` se la
cartella è `COMMESSE/121/`). Lo script:

1. Estrae il testo da tutte le pagine con `pypdf`
2. Identifica il tipo atto (Mappale/Frazionamento/Particellare) dalla prima pagina
3. Estrae con regex i dati catastali, l'estratto di mappa, le operazioni del modello censuario
4. Identifica il blocco "DITTA" e ne estrae intestatari + firmatari
5. Estrae il tecnico redattore
6. Parsa il libretto delle misure (righe `0|`, `1|`, `2|`, `6|`, `7|`, `9|`) per ricavare strumento, PF rilevati, punti di dettaglio, linee dividenti, punti vertice
7. Estrae i parametri di rappresentazione (`6|DISTORSIONE|`, `6|SCALAORIGINARIA|`, `6|ZONA|`)
8. Cattura il testo della relazione tecnica come paragrafo libero in fondo
9. Salva `dati_atto.md` nella cartella di output

### Step 3 — Riassumi e mostra

Mostra in chat una sintesi di quanto estratto:
- Tipo atto
- Comune / Foglio / Particella
- N. PF rilevati
- N. punti dettaglio

Flagga eventuali campi N.D. così l'utente sa subito se qualcosa manca. Linka il `dati_atto.md` prodotto.

### Step 4 — Verifica e correzioni

Se l'utente segnala che un dato è sbagliato o mancante:
- Non inventare
- Aggiungi una nota in fondo al `dati_atto.md`: "Campo X corretto manualmente dall'utente da '...' a '...'"
- Chiedi all'utente quale è il valore corretto
- Mai modificare silenziosamente l'estrazione automatica

---

## Riferimenti

- `scripts/extract_atto.py` — il parser principale. Dipende solo da `pypdf`
- `references/struttura_pdf_pregeo.md` — ancore testuali e formato libretto Pregeo
- `references/formato_dati_atto.md` — schema del Markdown prodotto

---

## Note operative

- **Non inventare dati.** Se un campo non è chiaramente presente nel PDF, scrivi `N.D.`
- **Codice catastale F-cat:** nel libretto la riga `0|` finisce con il codice comune (es. `F442` per Montebello Vicentino). Va sempre estratto — è quello che si trova nei nomi dei PF (`PFnn/foglio/F442`)
- **Particelle multiple:** alcuni atti hanno più particelle oggetto (es. 397, 398). Estraile tutte come lista
- **Pre vs post:** nelle operazioni del modello censuario distingui sempre: Originale (O), Soppressa (S), Costituita (C), Variata (V)
- **Firmatari ≠ Intestatari:** capita quando un consorzio firma come procuratore (es. RFI per IRICAV DUE). Riportali in due sezioni distinte per non confondere il proprietario reale con chi appone la firma tecnica
