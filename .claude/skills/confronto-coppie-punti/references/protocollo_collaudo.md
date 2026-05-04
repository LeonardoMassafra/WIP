# Protocollo di collaudo atto di aggiornamento

## Cosa si rileva sul campo

Per ciascun atto di aggiornamento catastale (tipo mappale, frazionamento) sottoposto a
collaudo si rilevano:

- **3 Punti Fiduciali** (gli stessi usati nel libretto Pregeo del frazionamento approvato)
- **almeno 2 punti significativi** dell'oggetto del rilievo, scelti fra quelli stabilmente
  materializzati (vertici di fabbricato, paletti, capisaldi, manufatti permanenti)

Si genera così un set minimo di **5 punti omologhi** per atto, da cui derivano
**10 mutue distanze** (C(5,2) = 10).

---

## Misure omologhe controllate al tavolo

Le distanze controllate sono tutte le mutue fra i 5 (o più) punti rilevati:

- Fra i 3 PF → **3 coppie PF↔PF**
- Fra ciascun PF e i punti di dettaglio → **6 coppie miste** (se 3 PF + 2 dettaglio)
- Fra i punti di dettaglio → **1 coppia** (se sono 2 dettaglio)

Per ogni coppia si confronta:
- la distanza calcolata dalle coordinate del **frazionamento approvato** (libretto Pregeo originario)
- la distanza calcolata dalle coordinate del **collaudo** (rilievo dello studio)

---

## Tolleranze

| Tipo coppia | Tolleranza | Riferimento |
|-------------|-----------|-------------|
| PF ↔ PF | 0.20 m | Tolleranza planimetrica per i punti fiduciali da Istruzioni Pregeo |
| Dettaglio ↔ Dettaglio | 0.05 m | Precisione attesa stazione totale + materializzazione su punti netti |
| PF ↔ Dettaglio | 0.20 m | Conservativa: l'incertezza del PF determina la soglia |

Le tolleranze sono configurabili — se il capitolato della commessa ne fissa di diverse,
vanno passate come parametro allo script.

---

## Output di consegna

Per ogni atto collaudato si consegna:

1. **Excel di lavoro** con tutte le mutue, esiti, evidenziazioni colore (archivio interno)
2. **Report tecnico** (compilato da skill dedicata) con la tabella di confronto integrata
   e il giudizio di conformità

---

## Vincolo di rappresentazione

Il confronto è in **planimetria (Est/Nord)**. La quota non entra mai nella verifica
catastale: i CSV di input possono avere la colonna Quota o esserne privi, in entrambi i
casi la quota non viene riportata negli output (Excel, Markdown, report).
