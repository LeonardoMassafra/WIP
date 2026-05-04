---
name: checklist-generator
description: >
  Genera checklist operative professionali in formato .docx per lo studio tecnico
  "Cattura la Realtà" di Leonardo Massafra. Copre attività di campagna (rilievi topografici,
  laser scanner 3D, voli drone, sopralluoghi, tracciamenti) e attività d'ufficio (pratiche
  catastali, consegne cliente, verifiche). Usa questa skill ogni volta che l'utente chiede
  di creare una checklist, lista di controllo, to-do operativa, lista attività, elenco
  verifiche, procedura operativa, o menziona "checklist", "lista di controllo",
  "cose da non dimenticare", "preparami una lista per", "cosa mi serve per",
  "checklist cantiere/rilievo/drone/ufficio".
---

# Checklist Generator — Cattura la Realtà

Genera checklist operative professionali in formato .docx, sfruttando competenza di dominio
su topografia, laser scanner 3D, rilievi con drone, catasto e gestione studio tecnico.

---

## Principi guida

Una buona checklist non è un elenco generico: è una lista specifica, ordinata per sequenza
logica di esecuzione, che riflette l'esperienza reale sul campo. Sfrutta le conoscenze
tecniche del settore per proporre voci che un professionista esperto metterebbe davvero.

---

## Flusso operativo

### 1. Intervista iniziale — SEMPRE

Prima di generare qualsiasi cosa, raccogli il contesto con queste domande (anche in un unico messaggio):

1. **Titolo / oggetto** della checklist (es. "Rilievo laser scanner villa storica")
2. **Tipo di attività** (campagna/ufficio, sotto-tipo: rilievo GPS, laser scanner, drone, sopralluogo, tracciamento, pratica catastale, consegna cliente, ecc.)
3. **Cliente**
4. **Commessa / riferimento pratica**
5. **Data** (o periodo previsto)
6. **Orientamento pagina: orizzontale o verticale?** ← chiedere SEMPRE, esplicitamente
7. **Numero indicativo di voci o sezioni** (se l'utente ha idee precise)
8. **Voci specifiche** già in mente da includere obbligatoriamente

Se l'utente ha già fornito alcune informazioni, chiedi solo quelle mancanti.
**L'orientamento pagina va confermato sempre, anche se sembra ovvio.**

### 2. Proposta delle voci

Proponi una checklist completa strutturata in sezioni logiche, basata sul tipo di attività.

**Conoscenze di dominio da sfruttare:**

- **Rilievo laser scanner:** preparazione strumentale (scanner, batterie, target, treppiedi), documentazione preliminare (planimetrie catastali, sopralluogo, permessi), operazioni in campo (punti di stazione, sovrapposizione nuvole, target georeferenziati, foto), chiusura cantiere, backup dati
- **Volo drone:** verifiche normative (NOTAM, zone ENAC, permessi), pre-volo (batterie, eliche, calibrazione, meteo, vento), piano di volo, acquisizione, log, post-volo, backup
- **Rilievo topografico GPS:** stazione base, rover, PF catastali, schede monografiche, meteo, batterie, libretto delle misure
- **Pratica catastale in ufficio:** visure, estratti di mappa, documenti cliente, compilazione Pregeo/Docfa, controlli, protocollo, archiviazione
- **Sopralluogo:** appuntamento confermato, strumenti di misura, macchina fotografica, moduli, DPI, modulistica accesso atti

Dopo la proposta, chiedi esplicitamente:
> "Ecco la mia proposta. Vuoi che aggiunga, tolga o modifichi qualche voce prima di generare il documento?"

**Itera fino a conferma. Solo allora genera il file.**

### 3. Generazione del file .docx

Usa `python-docx`. Struttura del documento:

**Intestazione (header):**
- Logo `assets/logo.jpg` a sinistra (larghezza ~3,5 cm)
- A destra: "Studio Tecnico Leonardo Massafra — Cattura la Realtà" in grassetto

**Blocco dati pratica:**
- Titolo checklist (18pt grassetto, centrato)
- Tabella 2 colonne: Cliente | Commessa | Data | Luogo/Cantiere | Operatore

**Sezioni checklist:**
- Titolo sezione: 14pt grassetto
- Ogni voce: carattere `☐` (U+2610) + spazio + testo
- Interlinea leggermente ampia (space_after = Pt(4)) per poter spuntare a penna

**Note finali:**
- Sezione "Note" con 4-5 righe vuote sottolineate

**Firma:**
- "Firma operatore: ______________________" e "Data: ______________________"

**Formato:**
- File: `.docx`
- Orientamento: come richiesto (LANDSCAPE = scambia larghezza/altezza)
- Margini: 2 cm su tutti i lati
- Font: Calibri 11pt corpo, 14pt grassetto sezioni, 18pt grassetto titolo
- Colori sobri (nero/grigio scuro, nessuna esplosione di colori)

**Nome file:** `Checklist_<tipo>_<commessa-o-cliente>_<YYYY-MM-DD>.docx`

**Output:** salva nella cartella `WIP/cattura-la-realta/tecnica/` o nella cartella di lavoro corrente.

```python
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent  # per trovare assets/logo.jpg

doc = Document()
section = doc.sections[0]

# Orientamento
if orientamento == "orizzontale":
    section.orientation = WD_ORIENT.LANDSCAPE
    new_w, new_h = section.page_height, section.page_width
    section.page_width = new_w
    section.page_height = new_h

# Margini
for m in ('top_margin','bottom_margin','left_margin','right_margin'):
    setattr(section, m, Cm(2))

# Logo in header
header = section.header
htab = header.add_table(rows=1, cols=2, width=Cm(25))
cell_logo, cell_text = htab.rows[0].cells
logo_path = SKILL_DIR / "assets" / "logo.jpg"
if logo_path.exists():
    cell_logo.paragraphs[0].add_run().add_picture(str(logo_path), width=Cm(3.5))
p = cell_text.paragraphs[0]
r = p.add_run("Studio Tecnico Leonardo Massafra — Cattura la Realtà")
r.bold = True

# Titolo
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = t.add_run(titolo)
tr.bold = True; tr.font.size = Pt(18)

# Tabella dati
tab = doc.add_table(rows=0, cols=2)
tab.style = "Light Grid Accent 1"
for label, value in [("Cliente", cliente), ("Commessa", commessa),
                     ("Data", data), ("Luogo", luogo), ("Operatore", operatore)]:
    row = tab.add_row().cells
    row[0].text = label
    row[1].text = value or ""

doc.add_paragraph()

# Sezioni
for sezione in sezioni:
    h = doc.add_paragraph()
    hr = h.add_run(sezione["titolo"])
    hr.bold = True; hr.font.size = Pt(14)
    for voce in sezione["voci"]:
        p = doc.add_paragraph(f"☐  {voce}")
        p.paragraph_format.space_after = Pt(4)

# Note
doc.add_paragraph()
n = doc.add_paragraph()
nr = n.add_run("Note")
nr.bold = True; nr.font.size = Pt(14)
for _ in range(5):
    doc.add_paragraph("_" * 90)

# Firma
doc.add_paragraph()
doc.add_paragraph("Firma operatore: ______________________          Data: ______________________")

doc.save(output_path)
```

### 4. Consegna

Fornisci un link diretto al file e un breve riepilogo di una riga (titolo, orientamento, numero di voci). Niente postamble lunghi.

---

## Note importanti

- **L'orientamento pagina va chiesto sempre** — non assumere mai un default
- **Non inventare dati:** se un campo non essenziale manca, lascialo vuoto
- **Itera sulle voci:** meglio un secondo giro di conferma che un file da rifare
- **Logo:** percorso assoluto costruito dalla directory della skill → `SKILL_DIR / "assets" / "logo.jpg"`
