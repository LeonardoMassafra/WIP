# Coefficienti di Merito e Demerito

Tabella dei coefficienti moltiplicativi da applicare al valore base €/m² dei comparables, per adattare la media del campione alle caratteristiche specifiche dell'immobile oggetto di stima.

**Fonti:** Tecnoborsa, IVS (International Valuation Standards), Borsa Immobiliare italiana, letteratura estimativa consolidata.

**IMPORTANTE per Leonardo:** questi valori sono standard di letteratura. Puoi modificarli direttamente in questo file in base alla tua esperienza sul mercato locale (Bovolone, Verona, bassa veronese). Le modifiche saranno effettive dalla prossima esecuzione della skill.

---

## Come si applicano

I coefficienti sono **moltiplicativi** e si combinano tra loro.

**Esempio di calcolo:**
- €/m² medio comparables puliti: 1.300 €/m²
- Coefficienti: stato ottimo ×1.10 | 3° piano con asc. ×1.02 | esposizione sud ×1.03 | classe B ×1.05 | affaccio cortile ×1.00
- Valore corretto: 1.300 × 1.10 × 1.02 × 1.03 × 1.05 × 1.00 = **1.577 €/m²**
- Su 120 m²: **189.240 €** → range ±5%: **179.800 € – 198.700 €**

---

## Stato manutentivo generale

| Condizione | Coefficiente |
|------------|--------------|
| Nuovo (<5 anni) o ristrutturato integralmente recente (<3 anni) | 1.12 |
| Ottimo / ristrutturato recente (3-10 anni) | 1.08 |
| Buono, manutenzione regolare | 1.00 *(riferimento)* |
| Mediocre, interventi parziali necessari | 0.90 |
| Da ristrutturare totalmente | 0.70 |
| Rudere / inagibile | 0.40 |

---

## Piano di collocazione (residenziale)

⚠️ **Il piano da usare è quello di accesso principale dell'unità abitativa**, non la notazione catastale. Molte visure riportano "S1-T" perché includono pertinenze al piano seminterrato (box/cantina): se l'unità principale è al rialzato/terra, applicare il coefficiente di quel piano, NON del seminterrato.

| Posizione | Coefficiente |
|-----------|--------------|
| Piano terra con giardino privato esclusivo | 1.05 |
| Piano terra senza giardino, su strada | 0.92 |
| Piano rialzato | 0.98 |
| Piano intermedio (1°-4° con ascensore) | 1.00 *(riferimento)* |
| Piano alto (5°+ con ascensore) | 1.03 |
| Ultimo piano con ascensore | 1.05 |
| Ultimo piano senza ascensore (edificio ≤4 piani) | 1.00 |
| Piano 2° senza ascensore | 0.97 |
| Piano 3°-4° senza ascensore | 0.88 |
| Piano 5°+ senza ascensore | 0.80 |
| Attico / superattico con terrazza di proprietà | 1.15 |
| Piano seminterrato ad uso abitativo | 0.75 |
| Piano seminterrato pertinenziale (box/cantina) | Non applicare — già calcolato nella superficie equivalente |

---

## Esposizione prevalente

| Orientamento | Coefficiente |
|-------------|--------------|
| Sud / sud-est / sud-ovest | 1.03 |
| Est / ovest (bilanciata) | 1.00 *(riferimento)* |
| Nord / nord-est / nord-ovest | 0.96 |
| Multipla (3-4 lati liberi) | +0.02 addizionale |

---

## Affaccio / posizione

| Tipo | Coefficiente |
|------|--------------|
| Panoramico (lago, montagna, monumento, skyline) | 1.08 |
| Verde pubblico o parco | 1.04 |
| Interno cortile silenzioso | 1.00 *(riferimento)* |
| Strada secondaria, poco rumore | 0.98 |
| Strada a forte traffico | 0.90 |
| Affaccio su industriale, stazione ferro, elettrodotto | 0.85 |

---

## Classe energetica

| Classe | Coefficiente |
|--------|--------------|
| A4, A3 | 1.08 |
| A2, A1 | 1.06 |
| A, B | 1.03 |
| C, D | 1.00 *(riferimento)* |
| E | 0.97 |
| F | 0.94 |
| G | 0.90 |

---

## Epoca di costruzione (per immobili non recenti)

| Periodo | Coefficiente |
|---------|--------------|
| Storico di pregio (<1850) ristrutturato | 1.10 |
| Storico (1850-1945) ristrutturato | 1.05 |
| Anni '50-'60 non ristrutturato | 0.90 |
| Anni '70-'80 non ristrutturato | 0.93 |
| Anni '90-2000 | 0.98 |
| 2000-2015 | 1.00 *(riferimento)* |
| Post 2015 | 1.05 |

*Se l'immobile è ristrutturato, il coefficiente di stato prevale su quello di epoca.*

---

## Pertinenze e accessori

| Elemento | Effetto |
|----------|---------|
| Box auto coperto | +8.000 – 15.000 € (valore assoluto) |
| Posto auto scoperto di proprietà | +3.000 – 6.000 € |
| Cantina >5 m² | +2.000 – 5.000 € |
| Soffitta praticabile | +3.000 – 8.000 € |
| Terrazzo >15 m² | ×1.02 – 1.05 |
| Balcone | già incluso nel valore base |
| Giardino privato esclusivo | ×1.05 – 1.10 |

**Nota:** pertinenze a valore assoluto si sommano al totale dopo aver applicato tutti i coefficienti moltiplicativi.

---

## Riscaldamento

| Tipo | Coefficiente |
|------|--------------|
| Autonomo a pompa di calore / sistemi rinnovabili | 1.03 |
| Autonomo a gas (caldaia moderna) | 1.00 *(riferimento)* |
| Centralizzato con contabilizzazione | 0.98 |
| Centralizzato senza contabilizzazione | 0.93 |
| Assente | 0.85 |

---

## Stato locativo

| Condizione | Coefficiente |
|------------|--------------|
| Libero (disponibile subito) | 1.00 *(riferimento)* |
| Locato con canone concordato | 0.90 |
| Locato con contratto libero 4+4 | 0.85 |
| Occupato senza titolo | 0.70 |

---

## Tipologie non residenziali

### Commerciale / Terziario

| Caratteristica | Coefficiente |
|---------------|--------------|
| Prima visibilità (strada principale, angolo) | 1.15 |
| Seconda visibilità | 1.00 *(riferimento)* |
| Retro, scarsa visibilità | 0.75 |
| Vetrine multiple (2+ affacci) | 1.08 |
| Ingresso carraio per carico/scarico | 1.05 |

### Produttivo / Industriale

| Caratteristica | Coefficiente |
|---------------|--------------|
| Accessibilità mezzi pesanti diretta | 1.05 |
| Altezza utile >6 m | 1.05 |
| Carroponte installato | 1.08 |
| Impianto fotovoltaico di proprietà | 1.03 – 1.08 (in base a kW) |
| Area esterna pertinenziale recintata | 1.03 |

### Agricolo

La valutazione di immobili agricoli (D/10) esula dalla stima sintetico-comparativa. Applicare solo coefficienti di stato e posizione, e consigliare nel report valutazione specialistica agronomica.

---

## Range di incertezza da dichiarare nel report

| Situazione | Range |
|-----------|-------|
| ≥10 comparables puliti, deviazione std <15% | ±5% dal valore centrale |
| 5-9 comparables o deviazione 15-25% | ±10% |
| <5 comparables o deviazione >25% | ±15% + nota di cautela |
