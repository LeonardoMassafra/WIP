# Caratteristiche immobile — dati aggiuntivi alla visura

**Come funziona:** la skill `stima-immobiliare` estrae automaticamente dalla visura catastale tutti i dati identificativi dell'immobile (categoria, rendita, superficie catastale, foglio, particella, subalterno, indirizzo, consistenza). In questo file scrivi **solo le informazioni che NON sono ricavabili dalla visura** e che invece sono necessarie per applicare i coefficienti di merito/demerito.

**Formato:** linguaggio naturale, frasi libere. La skill interpreta il testo, non cerca una sintassi rigida. Lascia vuote le voci che non conosci o non ti interessano.

---

## Superficie commerciale (scegli una delle 3 modalità)

### Modalità 1 — Hai già calcolato la superficie commerciale

```
Superficie commerciale: 118 m²
```
La skill usa direttamente quel numero e dichiara nel report che il calcolo è stato fatto dal perito.

### Modalità 2 — La skill calcola dalle superfici parziali

```
Superficie interna: 105 m²
Balcone 1: 8 m²
Balcone 2: 6 m²
Terrazzo: 18 m²
Giardino privato: 40 m²
Box auto: 18 m²
Cantina: 6 m²
```

La skill applica i coefficienti di omogeneizzazione standard (Tecnoborsa).
Vedi `references/coefficienti_superficie_commerciale.md` per l'elenco completo.

### Modalità 3 — Usa la superficie catastale da visura (fallback)

```
Usa superficie catastale
```
Di norma inferiore del 5-15% rispetto alla commerciale — stima leggermente conservativa.

---

## Piano e posizione nell'edificio

- Piano: [piano terra / rialzato / 1° / 2° / 3° / ... / ultimo / attico]
- Ascensore: [sì / no / non applicabile]
- Numero piani totali dell'edificio: [___]
- Esposizione prevalente: [sud / sud-est / sud-ovest / est / ovest / nord / nord-est / nord-ovest / multipla]
- Affaccio: [interno cortile silenzioso / strada secondaria / strada trafficata / verde pubblico / panoramico / industriale-ferrovia]

---

## Stato manutentivo (dato cruciale per la stima)

- Stato attuale: [nuovo / ristrutturato recente / ottimo / buono / mediocre / da ristrutturare / rudere]
- Anno ultima ristrutturazione significativa: [____]
- Interventi principali eseguiti: [impianti rifatti / serramenti sostituiti / pavimenti nuovi / bagno rifatto / cucina rifatta / cappotto termico / tetto rifatto / nessuno]

---

## Prestazioni energetiche

- Classe energetica (da APE): [A4 / A3 / A2 / A1 / A / B / C / D / E / F / G / non disponibile]
- Riscaldamento: [autonomo pompa di calore / autonomo gas / centralizzato con contabilizzazione / centralizzato senza contabilizzazione / assente]
- Raffrescamento estivo: [impianto centralizzato / split presenti / predisposizione / assente]

---

## Pertinenze e accessori

Se le pertinenze hanno sub catastale autonomo sono già nella visura.
Indica qui solo le **caratteristiche qualitative** che la visura non riporta:

- Box auto: [presente con accesso diretto / presente in corte condominiale / non presente]
- Posto auto scoperto di proprietà: [sì / no]
- Cantina: [presente, asciutta / presente, umida / non presente]
- Soffitta: [presente, praticabile con altezza agibile / presente, non praticabile / non presente]
- Balconi: [___ m² totali, esposizione prevalente ___]
- Terrazzo: [___ m², di proprietà esclusiva / comune]
- Giardino privato esclusivo: [___ m²]

---

## Stato locativo

- Libero: [sì / no]
- Locato: [no / sì, contratto libero 4+4 / sì, canone concordato / sì, uso transitorio]
- Occupato senza titolo: [no / sì]

---

## Vincoli e condizioni particolari

- Ipoteche / pignoramenti: [nessuno / presenti, descrivere]
- Vincoli storico-paesaggistici: [no / sì, descrivere]
- Abusi edilizi: [nessuno / sanato nel ___ / presenti in attesa di sanatoria]
- Diritti di terzi: [nessuno / servitù di passaggio / uso / abitazione, descrivere]
- Lavori condominiali deliberati: [nessuno / facciata / tetto / ascensore, con quota a carico dell'immobile di € ___]

---

## Note libere del perito

[Qualsiasi osservazione rilevante: qualità del contesto urbano, vicinanza a servizi, stato del condominio, qualità delle finiture, particolarità architettoniche, problematiche osservate durante il sopralluogo...]

---

## Finalità della stima

- Finalità: [perizia volontaria / pre-compravendita / mutuo bancario / divisione ereditaria / CTU / contenzioso / altro: ___]
- Committente: [nome / società]
- Data sopralluogo: [gg/mm/aaaa]
