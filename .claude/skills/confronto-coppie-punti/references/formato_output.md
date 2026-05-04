# Formato output del Markdown

Questo documento descrive la struttura di `confronto_misurate.md` prodotto dalla skill
`confronto-coppie-punti`. Una futura skill di compilazione del report tecnico leggerà questo
file e popolerà il template Word del report (capitolo "Verifica 10% dei punti di dettaglio")
con un Find&Replace, sullo stesso pattern già in uso per l'accesso atti.

---

## Schema atteso

```markdown
# Confronto misurate — <NOME_LAVORO>

## Identificazione lavoro
- Commessa: <es. 25022-CR-001>
- Comune: <comune dei mappali>
- Foglio: <foglio>
- Mappali oggetto: <elenco>
- Data collaudo: <gg/mm/aaaa>
- File frazionamento: <nome file>
- File collaudo: <nome file>

## Tolleranze applicate
- PF ↔ PF: 0.20 m
- Dettaglio ↔ Dettaglio: 0.05 m
- PF ↔ Dettaglio (mista): 0.20 m

## Sintesi
| Tipo coppia | Coppie totali | OK | NOK | % conformità | max |Δ| (m) |
|---|---|---|---|---|---|
| PF ↔ PF | 3 | 3 | 0 | 100.0% | 0.041 |
| PF ↔ Dettaglio | 6 | 6 | 0 | 100.0% | 0.082 |
| Dettaglio ↔ Dettaglio | 1 | 1 | 0 | 100.0% | 0.012 |
| **Totale** | 10 | 10 | 0 | **100.0%** | 0.082 |

## Coppie PF ↔ PF
| # | Punto A | Punto B | Dist. frazionamento (m) | Dist. collaudo (m) | |Δ| (m) | Soglia (m) | Esito |
|---|---|---|---|---|---|---|---|
| 1 | PF03/0050/F442 | PF11/0050/F442 | 124.387 | 124.395 | 0.008 | 0.20 | OK |
…

## Coppie PF ↔ Dettaglio
…

## Coppie Dettaglio ↔ Dettaglio
…

## Punti senza omologo
- Presenti solo nel frazionamento: <elenco o "nessuno">
- Presenti solo nel collaudo: <elenco o "nessuno">

## Note
<eventuali avvisi: pattern PF non riconosciuto, tolleranze custom usate, file con encoding atipico, ecc.>
```

---

## Convenzioni di compilazione

- I numeri sono sempre con il **punto decimale** (formato neutro), **3 cifre decimali** per metri
- L'esito è la stringa letterale `OK` o `NOK` (maiuscolo, senza simboli)
- I nomi punto sono riportati esattamente come nel file di input (case preservato)
- Se un dato non è disponibile, si scrive `N.D.` — mai stringa vuota, così la skill di compilazione successiva sa che il campo è dichiaratamente assente

---

## Perché Markdown e non JSON

Markdown è leggibile a occhio (controllo veloce prima di passarlo alla skill report),
facile da iniettare in un prompt, e identico al pattern già in uso per l'accesso atti
(`dati_estratti.md`). Il JSON sarebbe più rigoroso ma aggiunge un formato in più senza
vantaggi pratici per il flusso di Leonardo.
