---
name: stima-immobiliare
description: >
  Produce stime immobiliari professionali per Leonardo Massafra / Cattura la Realtà,
  incrociando Valori Immobiliari Dichiarati (HTML portale OMI AdE) con Quotazioni OMI
  semestrali (CSV) e dati catastali da visura PDF. Genera Excel di analisi e report Word
  (sintetico o completo) con valore stimato, range di mercato, comparables, flag outlier,
  coefficienti di merito/demerito. Attiva SEMPRE questa skill quando l'utente menziona:
  stima immobiliare, perizia, parere di valore, valutazione immobile, valore di mercato,
  analisi di mercato, €/m², comparables, quotazioni OMI, valori dichiarati, CTU immobiliare,
  perizia per mutuo, divisione ereditaria, sintetico-comparativo, o carica HTML dal servizio
  Consultazione Valori Immobiliari Dichiarati AdE, CSV quotazioni OMI, visure catastali.
---

# Stima Immobiliare — Cattura la Realtà

**Autore:** Leonardo Massafra, geometra — Cattura la Realtà (Bovolone, VR)
**Versione:** 1.0
**Ambito:** Perizie professionali, pareri di valore, consulenze pre-compravendita, CTU, perizie per mutui e divisioni ereditarie.

---

## 1. Struttura di input attesa

```
[cartella_commessa]/
├── 01_valori_dichiarati/      ← OBBLIGATORIA — HTML dal portale AdE
├── 02_quotazioni_omi/          ← raccomandata — CSV VALORI + CSV ZONE
├── 03_visura/                  ← raccomandata — visura PDF immobile
├── 04_caratteristiche/         ← raccomandata — dati qualitativi (testo/MD/JSON)
├── 05_foto/                    ← opzionale — jpg/png per report completo
├── 06_documenti_extra/         ← opzionale — planimetrie, estratti mappa, APE
└── output/                     ← la skill scrive qui (creala se non esiste)
```

Se i file sono in cartella piatta, classificali automaticamente:
- `.html` con "Consultazione valori immobiliari dichiarati" → valori dichiarati
- `.csv` con colonne `Compr_min, Compr_max, Zona` → quotazioni OMI
- `.pdf` con termini catastali tabellari ("Rendita", "Categoria", "Subalterno") → visura
- `.pdf` con "NUOVO CATASTO EDILIZIO URBANO" e planimetrie → documenti_extra
- `.jpg/.jpeg/.png` grandi → foto immobile

---

## 2. Flusso operativo

**Principio fondamentale:** il file `04_caratteristiche/` è la fonte primaria per tutti i dati qualitativi. L'unica domanda interattiva obbligatoria riguarda la superficie commerciale (Fase B.1, Caso 4). Per tutto il resto: usa coefficiente neutro 1.00 e dichiaralo nel report.

### Fase A — Parsing Valori Dichiarati

Leggi tutti gli HTML in `01_valori_dichiarati/` con `scripts/parse_valori_dichiarati.py`.
Salva come `output/01_valori_dichiarati.xlsx` con colonne:
`Scheda, Tipologia_Atto, Mese, Anno, Numero_Immobili, Corrispettivo_EUR, Comune, Zona_OMI, Settore, Categoria, Consistenza, Unita, Quota, EUR_per_m2, Flag, Note_Flag`

### Fase B — Estrazione dati catastali dalla visura

**Divisione responsabilità:**
- **Dalla visura** (SEMPRE): comune, foglio, particella, subalterno, indirizzo, categoria catastale, classe, consistenza, superficie catastale ex DPR 138/98, rendita
- **Dal file caratteristiche** (complementare): piano, ascensore, esposizione, affaccio, stato manutentivo, classe energetica, riscaldamento, pertinenze qualitative, stato locativo, vincoli, finalità stima

⚠️ **REGOLA PRIVACY CRITICA:** I dati personali dei proprietari (nomi, cognomi, CF, quote nominative) presenti in visura **NON devono MAI comparire nel report finale** (né sintetico né completo). Motivazione: GDPR — principio di minimizzazione. Il nome del committente invece va incluso.

Se la finalità richiede esplicitamente i nomi dei proprietari (CTU, divisioni ereditarie): chiedi conferma esplicita prima di inserirli.

Procedura:
1. Usa la skill `estrai-dati-per-accesso-agli-atti` per estrarre dati catastali dalla visura
2. Se più visure → gestiscile come unità distinte dello stesso compendio
3. Integra con file `04_caratteristiche/` per dati qualitativi
4. Filtra dati personali prima di consolidare l'immobile oggetto

### Fase B.1 — Determinazione superficie commerciale

**Caso 1:** Superficie commerciale dichiarata nel file caratteristiche → usala direttamente
**Caso 2:** Superfici parziali nel file caratteristiche → leggi `references/coefficienti_superficie_commerciale.md` e calcola con coefficienti Tecnoborsa. Produci tabella: `Elemento | Superficie dichiarata (m²) | Coefficiente | Superficie equivalente (m²)`
**Caso 3:** "usa superficie catastale" nel file caratteristiche → usa la superficie ex DPR 138/98 dalla visura. Dichiara nel report.
**Caso 4 (INTERATTIVO):** Nessuna indicazione → chiedi all'utente:

> "Nel file caratteristiche non ho trovato la superficie commerciale. Come vuoi procedere?
> 1) Dichiara la superficie commerciale in m²
> 2) Dammi le superfici parziali e calcolo io (coefficienti Tecnoborsa)
> 3) Usa la superficie catastale da visura (scrivi 'catastale')
> 4) Ho le planimetrie in 06_documenti_extra/ (scrivi 'planimetrie')"

Il report deve sempre dichiarare esplicitamente quale caso è stato adottato.

### Fase B.2 — Gestione planimetrie catastali (opzionale)

Se presenti PDF con "NUOVO CATASTO EDILIZIO URBANO" in `06_documenti_extra/`:
1. Identifica il subalterno oggetto (dalla visura)
2. Seleziona le pagine corrispondenti al subalterno (testo ruotato 90° sul bordo sinistro)
3. Cataloga i vani identificati (NON estrarre automaticamente le superfici — qualità scansione insufficiente per perizie)
4. Presenta lista vani all'utente e chiedi le superfici misurate
5. Verifica coerenza con superficie catastale (avvisa se scostamento >±15%)
6. Inserisci la planimetria nel report completo (Sezione 9) con didascalia: "Planimetria catastale — Subalterno [N], [piano]. Fonte: Agenzia delle Entrate."

### Fase B.3 — Lettura caratteristiche qualitative

Leggi `04_caratteristiche/` per: piano, ascensore, esposizione, affaccio, stato manutentivo, classe energetica, riscaldamento, pertinenze qualitative, stato locativo, vincoli, finalità stima, committente.

- Se il file esiste: interpreta tutto (formato libero, campi etichettati, o JSON futuro)
- Se manca: procedi con coefficienti neutri 1.00 per ogni caratteristica, dichiarandolo nel report
- **Default minimi se mancanti:** finalità → "Parere di valore orientativo" | committente → "[da compilare manualmente]" | stato manutentivo → "buono" (coeff. 1.00)

### Fase C — Lettura Quotazioni OMI

Due file CSV complementari in `02_quotazioni_omi/`:
- **File VALORI** (obbligatorio): `Compr_min, Compr_max, Loc_min, Loc_max` per zona/tipologia/stato
- **File ZONE** (raccomandato): `Zona_Descr` (descrizione estesa), `Fascia` (B/C/D/R/E/Z)

Usa `scripts/parse_quotazioni_omi.py`. Filtra per Comune + Zona OMI + Tipologia.
Salva come `output/02_quotazioni_omi_zona.xlsx`.

Se mancano i CSV: informa l'utente e suggerisci di scaricarli da "Forniture dati OMI" AdE (SPID richiesto).

### Fase D — Flag outlier

Per ogni scheda-atto nei Valori Dichiarati, confronta il corrispettivo con:
- **Valore catastale teorico** (Rendita × moltiplicatore da `references/coefficienti_valore_catastale.md`): se entro ±10% → 🔴 "sospetto errore comma 497 L. 266/2005"
- **Range Quotazioni OMI**: se fuori ±50% mediana OMI → 🟡 "scostamento dal mercato"
- **Mediana campione dichiarati**: se fuori ±50% → 🟡 "outlier statistico"

**Convenzione flag (OBBLIGATORIO — usare emoji, NON stringhe):**
- 🟢 = atto pulito, utilizzabile senza riserve
- 🟡 = scostamento o categoria diversa, attenzione
- 🔴 = sospetto errore comma 497
- ℹ️ = nota informativa

**Non escludere mai automaticamente gli atti flaggati.** La decisione di esclusione spetta al perito.

### Fase E — Analisi di stima

Crea `output/03_analisi_stima.xlsx` con fogli:
1. **Comparables puliti** — atti con flag vuoto, per settore di mercato
2. **Statistica €/m²** — min, Q1, mediana, media, Q3, max per settore
3. **Coefficienti merito/demerito** — leggi `references/coefficienti_merito.md` (OBBLIGATORIO). Per ogni caratteristica: valore osservato | coefficiente | riferimento file | motivazione | risultato progressivo
4. **Valore finale** — triplice (min/centrale/max): `€/m² base × coefficienti × superficie commerciale`

### Fase E.1 — Cross-check Income Approach

Se disponibili `Loc_min` e `Loc_max` in Quotazioni OMI:
- Canone medio mensile al m²: `(Loc_min + Loc_max) / 2`
- Canone annuo lordo: `canone_medio × superficie_commerciale × 12`
- GRM per fascia: B=20, C=18, D=16, R=14, E=14, Z=15
- V_income = canone_annuo_lordo × GRM
- Scostamento da Market: <15% convergenza | 15-30% moderato | >30% segnalare con cautela

Aggiungi foglio "Cross-check Income" in `output/03_analisi_stima.xlsx`.

### Fase E.2 — Cross-check Cost Approach

Leggi `references/costi_ricostruzione.md` (OBBLIGATORIO) per costi ricostruzione a nuovo.

Calcolo:
- Costo ricostruzione €/m² da tabella (tipologia + fascia qualitativa)
- Superficie lorda: catastale +15% per muri (o dichiarata dal perito)
- Deprezzamento Ross-Heidecke: K = (1 - D_ross) × (1 - Heidecke)
- Valore terreno: da OMI o incidenza percentuale (centro 30-40%, semicentro 20-30%, periferia 15-25%, rurale 10-15%)
- V_cost = V_terreno + (C_ricostruzione × S_lorda × K_deprezzamento)

**Gerarchia approcci:** Per residenziale con >5 comparables: Market primario, Cost e Income cross-check. Per immobili industriali (D/1, D/7 con <5 comparables), agricoli (D/10), speciali (B, E), da ristrutturare/rudere: Cost primario, Market cross-check.

### Fase F — Generazione report Word

Chiedi all'utente: sintetico, completo, o entrambi. Struttura dettagliata in `references/struttura_report.md`.

**Regole pulizia dati nelle tabelle:**
- Mai mostrare "nan", "None", "NaN", "null" → usa cella vuota, "—" o "n.d."
- Dati personali: verificare assenza in ogni tabella
- Numeri: formato italiano (208.000,00 €)
- Date: "15 gennaio 2026" nel corpo, gg/mm/aaaa nelle tabelle
- Superfici: sempre m² (non "mq" né "m2")
- Termini interni della skill ("Fase B.1", "Caso 2", "Modalità") → tradurre in linguaggio estimativo professionale

**Template:** Usa template grafico Cattura la Realtà (logo, intestazione, footer). Se non disponibile chiedi il percorso. Se irreperibile usa formato sobrio con:
- Intestazione: "Cattura la Realtà — Geom. Leonardo Massafra"
- Footer: tutti i dati studio

⚠️ **REGOLA CRITICA FOOTER:** Se mancano dati studio, inserire placeholder VISIBILI tra parentesi quadre. MAI rimuovere campi silenziosamente.
```
Cattura la Realtà — Via [INSERIRE INDIRIZZO STUDIO], Bovolone (VR)
Tel. [INSERIRE TELEFONO] — Email: [INSERIRE EMAIL] — P.IVA [INSERIRE P.IVA]
www.catturalarealta.it  |  Pag. X di Y
```

Avvertenza normativa obbligatoria nel report completo (Cassazione n. 3197/2018):
> "Le quotazioni OMI forniscono indicazioni di valore di larga massima e non sostituiscono la stima puntuale effettuata dal tecnico professionista, che rimane l'unico strumento idoneo a motivare il valore attribuito all'immobile specifico."

### Fase G — Presentazione al cliente

Mostra all'utente: report Word + `03_analisi_stima.xlsx` + Excel di dettaglio.
Messaggio di sintesi: valore stimato (centrale + range) | n. comparables | n. outlier | note critiche.

---

## 3. Principi invariabili

- **Cita SEMPRE le fonti:** "Agenzia Entrate — OMI" (obbligatorio per legge)
- **Dichiara sempre la metodologia:** "approccio sintetico-comparativo"
- **Precisa il periodo di riferimento** dei comparables
- **Se comparables puliti <5:** avvisa nel report che la significatività statistica è ridotta
- **Non sostituire il perito:** il report è supporto alla perizia che Leonardo firma e assume in responsabilità professionale

---

## 4. File di riferimento

- `references/categorie_catastali.md` — Classificazione A/B/C/D/E/F
- `references/coefficienti_valore_catastale.md` — Moltiplicatori imposta di registro (flag comma 497)
- `references/coefficienti_superficie_commerciale.md` — Coefficienti Tecnoborsa (Fase B.1 Caso 2)
- `references/settori_omi.md` — Mappatura RES/PER/TCO/PRO/AGR/ALT ↔ categorie catastali
- `references/coefficienti_merito.md` — Coefficienti merito/demerito (modificabile da Leonardo)
- `references/costi_ricostruzione.md` — Costi ricostruzione a nuovo + metodo Ross-Heidecke (modificabile)
- `references/struttura_report.md` — Struttura 15 sezioni report completo IVS + sintetico

## 5. Script Python

- `scripts/parse_valori_dichiarati.py` — Parsing HTML schede-atto AdE
- `scripts/parse_quotazioni_omi.py` — Lettura e filtro CSV Quotazioni OMI

---

## 6. Gestione errori e casi limite

| Caso | Comportamento |
|------|--------------|
| HTML malformati | Segnala e procedi con gli altri, non fallire l'intero flusso |
| <5 atti dopo parsing | Avvisa e proponi di ampliare i criteri di ricerca |
| Categoria catastale anomala (F/3, F/4, E, B) | Avvisa che l'approccio sintetico-comparativo non è applicabile |
| Superficie commerciale mancante (solo consistenza in vani) | Non inventare con coefficienti generici — chiedi all'utente |
| Comuni a sistema tavolare (TN, BZ, TS, GO...) | Avvisa mancanza dati dichiarati, procedi solo con Quotazioni OMI |
