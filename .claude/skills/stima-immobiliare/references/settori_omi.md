# Settori di Mercato OMI e Mappatura Categorie Catastali

Classificazione ufficiale dell'Osservatorio del Mercato Immobiliare (Tabella 2 della Guida al Servizio "Consultazione Valori Immobiliari Dichiarati", aggiornamento ottobre 2024).

---

## Acronimi e mappatura

| Acronimo | Settore | Categorie catastali |
|----------|---------|---------------------|
| **RES** | Residenziale | Gruppo A tranne A/10 |
| **PER** | Pertinenze | C/2 fino a 30 m², C/6 e C/7 fino a 50 m² |
| **TCO** | Terziario-Commerciale | A/10, C/1, C/3, D/2, D/5, D/8, B/4, C/2 oltre 30 m², C/6 e C/7 oltre 50 m² |
| **PRO** | Produttivo | D/1, D/7 |
| **AGR** | Produttivo agricolo | D/10 |
| **ALT** | Altre destinazioni | C/4, C/5, D/3, D/4, D/6, D/9, gruppo B tranne B/4, gruppo E, gruppo F |
| **RSD** | Residuo | Beni comuni non censibili, unità non classificate |

---

## Soglie dimensionali per pertinenze

| Categoria | Fino a | Settore | Oltre | Settore |
|-----------|--------|---------|-------|---------|
| C/2 (cantine, soffitte) | 30 m² | PER | 30 m² | TCO |
| C/6 (box, posti auto) | 50 m² | PER | 50 m² | TCO |
| C/7 (tettoie) | 50 m² | PER | 50 m² | TCO |

**Avvertenza:** è una convenzione statistica, non un criterio normativo. La skill usa la segmentazione come fornita dal portale.

---

## Logica di raggruppamento per l'analisi

I valori vengono sempre raggruppati per settore di mercato, **mai mescolati**. Le pertinenze (PER) non vanno mai incluse nel calcolo €/m² della residenza (RES).

---

## Fasce urbanistiche delle zone OMI

| Codice | Denominazione | Descrizione |
|--------|---------------|-------------|
| **B** | Centro urbano | Cuore storico/commerciale, valori tipicamente più alti |
| **C** | Semicentro | Aree limitrofe al centro, buona accessibilità |
| **D** | Periferia | Aree esterne al tessuto centrale |
| **R** | Zona rurale | Territorio rurale, fabbricati sparsi |
| **E** | Zona extraurbana | Zone isolate o turistiche |
| **Z** | Zona particolare | Zone a destinazione specifica (industriali, artigianali, commerciali) |

Il codice zona completo = fascia + progressivo (es. B1, D3).

Nel report: indicare sempre **codice zona** + **descrizione estesa** (dal file ZONE OMI).

---

## Sotto-classificazione categoria A

| Codice | Descrizione | Uso tipico |
|--------|-------------|------------|
| A/1 | Abitazioni signorili | Fascia alta, finiture di pregio |
| A/2 | Abitazioni civili | Fascia media-alta, standard urbano |
| A/3 | Abitazioni economiche | Fascia media, edilizia popolare di buon livello |
| A/4 | Abitazioni popolari | Fascia medio-bassa |
| A/5 | Abitazioni ultrapopolari | Fascia bassa (raro attualmente) |
| A/6 | Abitazioni rurali | Case rurali in contesto agricolo |
| A/7 | Villini | Ville piccole con giardino |
| A/8 | Ville | Ville con parco |
| A/9 | Castelli, palazzi di pregio | Immobili storico-monumentali |
| A/11 | Abitazioni tipiche | Trulli, baite, rifugi alpini |

**Regola:** confrontare preferibilmente immobili della stessa categoria. Se i comparables mescolano categorie diverse, segnalarlo nel report.

---

## Filtro per stima sintetico-comparativa

Esempio: immobile A/2 a Bovolone zona B1:

1. **Valori Dichiarati:** preferire atti con unità RES categoria A/2 (o A/3 se campioni A/2 insufficienti)
2. **Quotazioni OMI:** cercare tipologia 20 ("Abitazioni civili") o 21 ("Abitazioni economiche"), stato "NORMALE", zona B1
3. Se le due fonti differiscono di più del 30% → segnalare il disallineamento nel report e raccomandare approfondimento
