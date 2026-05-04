# Skill `stima-immobiliare` — Guida rapida

Skill per produrre stime immobiliari professionali per Leonardo Massafra / Cattura la Realtà.

## Cosa fa

Produce perizie estimative con approccio sintetico-comparativo, incrociando:

1. **Valori Immobiliari Dichiarati** — HTML salvati manualmente dal portale AdE
2. **Quotazioni OMI semestrali** — CSV pubblico dal servizio "Forniture dati OMI"
3. **Visura catastale** dell'immobile oggetto di stima
4. **Caratteristiche descrittive** (stato, piano, esposizione, classe energetica, ecc.)
5. **Foto e documentazione aggiuntiva**

**Output:**
- Excel valori dichiarati strutturati + flag outlier
- Excel quotazioni OMI filtrate per zona
- Excel analisi di stima (applicazione coefficienti)
- Report Word sintetico (1-2 pagine)
- Report Word completo (5-10 pagine, con foto e documenti)

---

## Struttura della cartella di input

```
[NOME_COMMESSA]/
├── 01_valori_dichiarati/       ← OBBLIGATORIA
│   ├── pagina_1.html
│   ├── pagina_2.html
│   └── ...
├── 02_quotazioni_omi/          ← raccomandata
│   ├── QI_*_VALORI_*.csv
│   └── QI_*_ZONE_*.csv
├── 03_visura/                  ← raccomandata
│   └── visura_oggetto.pdf
├── 04_caratteristiche/         ← raccomandata
│   └── caratteristiche_immobile.md
├── 05_foto/                    ← opzionale
│   ├── 01_esterno.jpg
│   └── ...
├── 06_documenti_extra/         ← opzionale
│   ├── planimetrie.pdf
│   └── ...
└── output/                     ← la skill scrive qui (auto-creata)
```

---

## Come preparare i Valori Dichiarati (1 minuto di lavoro manuale)

1. Collegati a `telematici.agenziaentrate.gov.it` con SPID
2. Vai su "Osservatorio Mercato Immobiliare" → "Consultazione Valori Immobiliari Dichiarati"
3. Imposta la ricerca (indirizzo, zona, periodo, tipologia) e clicca **Avvia ricerca**
4. Sulla pagina 1 dei risultati: **Ctrl+S** → scegli *"Pagina Web, solo HTML"* → salva come `pagina_1.html` nella cartella `01_valori_dichiarati/`
5. Clicca su "2" nel paginatore → Ctrl+S → `pagina_2.html`
6. Ripeti per tutte le pagine disponibili

**Attenzione:** salva SEMPRE come "Pagina Web, solo HTML" (NON "Completa").

---

## Come preparare le Quotazioni OMI (una volta a semestre)

1. Collegati a `telematici.agenziaentrate.gov.it` con SPID
2. Vai su "Osservatorio Mercato Immobiliare" → **"Forniture OMI - Quotazioni Immobiliari"**
3. Richiedi i dati per la provincia VR, semestre corrente
4. Scarica lo ZIP. Al suo interno:
   - **`QI_*_VALORI_*.csv`** — range €/m² (OBBLIGATORIO)
   - **`QI_*_ZONE_*.csv`** — anagrafica descrittiva zone OMI (raccomandato)
   - File KML — perimetri geografici (non usati dalla skill, conserva a parte)
5. Metti i due CSV in `02_quotazioni_omi/`
6. I CSV valgono 6 mesi — riutilizzali per tutte le stime del semestre

---

## Come preparare il file caratteristiche

Il file `caratteristiche_immobile.md` contiene **solo le informazioni NON presenti in visura** (piano, ascensore, esposizione, stato manutentivo, classe energetica, pertinenze qualitative, superficie commerciale, vincoli, finalità).

I dati identificativi (categoria, rendita, superficie catastale, foglio, particella) li estrae la skill dalla visura — non devi ricopiarli.

### Tre modalità per la superficie commerciale

- **Modalità 1 (fai tu il calcolo):** scrivi `Superficie commerciale: 118 m²`
- **Modalità 2 (la skill calcola):** elenca le superfici parziali — la skill applica i coefficienti Tecnoborsa e produce tabella di calcolo trasparente
- **Modalità 3 (automatica):** scrivi `Usa superficie catastale`

### Esempio di compilazione

```
Piano: 3° con ascensore
Esposizione: sud-est
Affaccio: interno cortile silenzioso
Stato: ristrutturato nel 2019 (impianti rifatti, serramenti PVC, bagno nuovo)
Classe energetica: B
Riscaldamento: autonomo a gas (caldaia 2019)

Superficie interna: 105 m²
Balconi: 14 m² totali
Terrazzo: 18 m²
Box auto: 18 m²
Cantina: 6 m²

Pertinenze: box auto con accesso diretto, cantina asciutta
Stato: libero
Finalità: perizia per mutuo
Committente: Mario Rossi
```

---

## Come funzionano le planimetrie catastali (opzionale)

Se metti la planimetria PDF in `06_documenti_extra/`:
1. La skill identifica il subalterno dalla visura
2. Individua le pagine corrispondenti nel PDF
3. Cataloga i vani rilevati (senza estrarre automaticamente le superfici — qualità scansione variabile)
4. Ti chiede le superfici misurate
5. Verifica coerenza con la superficie catastale (avvisa se scostamento >±15%)
6. Inserisce la planimetria nel report completo con didascalia

---

## Modifica dei coefficienti

I coefficienti di merito/demerito sono in `references/coefficienti_merito.md`.
I costi di ricostruzione sono in `references/costi_ricostruzione.md`.

Modificali direttamente con un editor di testo. Effettivi dalla prossima esecuzione.

---

## Note legali

I report citano sempre la fonte: *"Agenzia Entrate — OMI"*.

Il report **non è una perizia autonoma**: è un documento di supporto alla perizia che il geometra firma e assume in responsabilità professionale. L'avvertenza Cassazione 3197/2018 è sempre inclusa nel report completo.
