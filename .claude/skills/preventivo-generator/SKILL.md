---
name: preventivo-generator
description: >
  Compila automaticamente i preventivi (offerte di servizio) per lo studio "Cattura la Realtà"
  di Leonardo Massafra. Legge i dati da un Modulo_Preventivo.xlsx compilato, da testo libero
  in chat, o da un comando veloce. Applica i default (pagamento "da concordare", firma inserita,
  Bovolone, 30 giorni validità) e genera il preventivo finale in formato .docx modificabile.
  Usa questa skill quando l'utente dice "fammi un preventivo", "crea un'offerta",
  "genera preventivo", "preventivo snello", "preventivo veloce", "compila preventivo",
  oppure allega un file Modulo_Preventivo.xlsx o qualsiasi Excel con fogli DATI e VOCI.
---

# Skill: preventivo-generator

Compila i preventivi (offerte di servizio) di "Cattura la Realtà" partendo da dati strutturati
o testo libero, producendo un .docx pronto all'invio.

---

## 3 modalità di input supportate

### Modalità 1 — Modulo Excel compilato (preferita da PC)

L'utente allega `Modulo_Preventivo.xlsx` compilato. La skill:
1. Legge il foglio **DATI** per destinatario, oggetto, numero, data, modalità pagamento, ecc.
2. Legge il foglio **VOCI** e prende le righe con "X" nella colonna SPUNTA + il TOTALE in fondo
3. Genera il preventivo

### Modalità 2 — Testo libero in chat (preferita da mobile)

L'utente scrive in chat in linguaggio naturale. Esempio:
> "Preventivo per Studio Rossi Srl, oggetto rilievo capannone via Milano 12, voci rilievo laser scanner + restituzione nuvola punti CAD + planimetria generale, totale 2.800 euro, numero 2026-042, firma sì"

La skill estrae i campi, applica i default per quelli mancanti e genera il preventivo.
Se mancano dati obbligatori (destinatario, oggetto, numero, voci, totale), chiede **solo quelli**.

### Modalità 3 — Comando veloce

Formato: `preventivo veloce [cliente], [oggetto], [totale]`

Esempio: `preventivo veloce Rossi, rilievo capannone, 2200`

In questa modalità:
- La voce del preventivo = l'oggetto (voce unica)
- Il numero va chiesto all'utente
- Tutto il resto va in default

---

## Campi e default

| Campo | Default se mancante |
|-------|---------------------|
| Numero preventivo | Richiesto (chiedi all'utente) |
| Data | Data di oggi, formato gg/mm/aaaa |
| Destinatario | **Obbligatorio** |
| Oggetto | **Obbligatorio** |
| Validità (giorni) | 30 |
| Luogo | Bovolone |
| Modalità pagamento | "da concordare" |
| Inserire firma | SÌ (sempre, se non specificato NO) |
| Note aggiuntive | (vuoto) |
| Voci | **Obbligatorio** (almeno 1) |
| Totale | **Obbligatorio** (numero in euro, senza IVA/CNG) |

---

## Vincoli stabiliti con l'utente

- ❌ NON generare numeri progressivi automatici — il numero lo gestisce l'utente
- ❌ NON tenere un registro Excel dei preventivi emessi
- ❌ NON inserire la "Nota: Il rilievo acquisito da tecnologia laser scanner..." (eliminata dal template)
- ❌ NON produrre PDF — solo .docx modificabile
- ❌ NON spezzare il prezzo per voce — il totale è sempre UN SOLO importo in fondo

---

## Come generare il preventivo

1. Raccogli i dati (da xlsx / testo libero / comando veloce)
2. Applica i default ai campi vuoti
3. Valida i campi obbligatori (numero, destinatario, oggetto, voci, totale); se mancano, chiedi SOLO quelli
4. Chiama lo script:

```bash
# Da xlsx
python generate_preventivo.py --input <percorso_modulo.xlsx> --output Preventivo_<numero>_<cliente>.docx

# Da JSON (per testo libero / comando veloce)
python generate_preventivo.py \
  --json '{"numero":"2026-042","destinatario":"Studio Rossi","oggetto":"Rilievo capannone","voci":["Rilievo laser scanner","Restituzione nuvola punti CAD"],"totale":2800}' \
  --output Preventivo_2026-042_Rossi.docx
```

### Dove salvare il .docx (in ordine di priorità)

1. Se esiste `preventivi_generator/02_PREVENTIVI_FINITI/<anno>/` → salva lì
2. Se esiste `preventivi_generator/` → crea `02_PREVENTIVI_FINITI/<anno>/` e salva lì
3. Fallback: cartella corrente

**Nome file:** `Preventivo_<numero>_<cliente>.docx` (cliente = versione safe del destinatario, max 40 caratteri)

### Dopo la generazione

- Sposta il modulo Excel di input (se presente) in `preventivi_generator/03_ARCHIVIO_MODULI/`
- Presenta il file generato con una breve conferma dei dati inseriti

---

## Firma

Il file della firma deve trovarsi in: `assets/firma.png`

- Se esiste e l'utente ha richiesto la firma (o non l'ha esclusa): lo script la inserisce sopra "LEONARDO MASSAFRA"
- Se NON esiste: genera il preventivo senza firma e avvisa l'utente dove mettere il file

---

## Lista attività di riferimento

La lista completa delle voci ricorrenti è in `references/lista_attivita.txt`.

Quando l'utente menziona voci in forma abbreviata (es. "laser scanner", "drone", "docfa"),
cerca la corrispondenza nella lista ufficiale e usa la forma completa nel preventivo.

---

## Output finale

Dopo la generazione, rispondi con:
- Breve riepilogo: numero, cliente, oggetto, n. voci, totale
- Quali default sono stati applicati (es. "pagamento: da concordare — firma: inserita")
- Link al file .docx
- Nessun post-ambolo lungo
