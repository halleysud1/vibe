# Riferimento — Calibrare il funnel su un dominio nuovo

Il funnel e' agnostico. A cambiare da un dominio all'altro sono **cinque parametri**,
che vanno fissati in Fase 1 con l'utente e dichiarati nel sinottico finale. Questo
file spiega come scegliere ciascuno e mostra tre calibrazioni d'esempio.

Non sono preset da importare: sono esempi di come si ragiona.

---

## 1. Forma del funnel e limite di ricorsione

La forma tendenziale e' **tre round**: inquadramento → dubbi → focalizzazione. Non
si configura il "numero di round" a priori: si configura il **limite di ricorsione**
dello stadio dei dubbi, cioe' quanti round di verifica ti concedi prima di fermarti
e chiedere a un umano.

| Limite | Funnel risultante | Quando |
|---|---|---|
| **0** | 2 round (inquadramento → focalizzazione), i dubbi si chiudono solo con la gamba veloce | campo piccolo, dominio stabile, decisione reversibile. Onesto solo se dichiari che i dubbi strutturali non li hai indagati a fondo |
| **1** | fino a 3 round | default per una decisione ordinaria |
| **2** | fino a 4 round | **default raccomandato** quando la decisione a valle e' costosa o difficilmente reversibile |
| **3+** | fino a 5+ round | domini in cui la premessa e' notoriamente instabile (norma in evoluzione, mercato in movimento, fonti contraddittorie per costume) |

Due regole che valgono in ogni dominio:

- **Ogni round deve cambiare una decisione.** Se non sai dire quale decisione dipende
  dall'esito, quel round non serve — vale per i round di dubbi come per gli altri.
- **Il limite si dichiara prima di partire.** Deciderlo mentre si e' dentro non e' un
  budget, e' una resa: si finisce sempre per concedersi "un altro giro" fino a
  esaurire la pazienza invece del dubbio.

Il funnel puo' anche **accorciarsi**: se il controllo sul primo round non trova dubbi
strutturali, lo stadio 2 si salta. Tre round e' la tendenza, non una quota da
riempire.

## 2. Fonti primarie (cosa vale come prova)

Il criterio non e' l'autorevolezza percepita ma la **responsabilita' editoriale**:
vale come prova chi risponde di quel dato.

| Tipo di dominio | Fonti primarie | Da NON usare come prova |
|---|---|---|
| Normativo / pubblico | gazzetta o registro ufficiale, banca dati normativa, sito dell'ente erogatore, atti pubblicati | studi di consulenti, portali di intermediari, articoli di testate |
| Tecnico / prodotto | documentazione ufficiale versionata, repository e changelog, specifica dello standard body, security advisory | blog post, tutorial, risposte su forum, benchmark di vendor concorrenti |
| Societario / due diligence | registro delle imprese, bilanci depositati, comunicazioni al mercato, albi e registri professionali | siti aziendali auto-descrittivi, comunicati stampa, profili social |
| Mercato / prezzi | listini pubblicati dal fornitore, contratti quadro, aste e bandi pubblici, statistiche ufficiali | stime di analisti dietro paywall citate di seconda mano |

In ogni dominio esiste una zona grigia (associazioni di categoria, camere di
commercio, documentazione di partner): ammettila come **fonte secondaria per
contesto**, mai per i dati puntuali, e dillo nel prompt.

## 3. Dimensioni di score

Default (5 × 0-10 = 0-50): pertinenza · valore · certezza del dato · tempo ·
costo/complessita' (invertita).

Come adattarle:

- **Tieni sempre "certezza del dato".** E' la dimensione che rende il funnel diverso
  da una ricerca qualunque: penalizza i candidati la cui scheda poggia su fonti
  fragili o su conflitti irrisolti.
- **Sostituisci "valore" con l'unita' del dominio**: € di beneficio, ore risparmiate,
  punti di rischio ridotti, copertura funzionale. Dichiara l'unita': "8/10" senza
  unita' non e' confrontabile con nulla.
- **Aggiungi al massimo una dimensione specifica** (es. "reversibilita'" per scelte
  tecnologiche, "rischio di revoca" per contributi pubblici, "dipendenza da terzi"
  per fornitori). Oltre le 6 dimensioni lo score diventa rumore pesato.
- **Le dimensioni invertite vanno etichettate come tali** in ogni tabella, sempre.
  Un lettore che legge "complessita' 9" e capisce "molto complesso" prende la
  decisione opposta a quella che gli stai suggerendo.
- Le soglie di priorita' (alta ≥ 35 / media 20-34 / bassa < 20) sono un default
  configurabile: se cambi il numero di dimensioni, ricalcolale in proporzione.

## 4. Criterio di restringimento — e cosa conta come dubbio strutturale

Cosa fa passare un candidato dal round N al round N+1. Va deciso **prima** di
leggere i risultati, altrimenti si razionalizza a posteriori.

Prima ancora del criterio di selezione, va definito **cos'e' un dubbio strutturale
in questo dominio**: e' lui che decide se si stringe o si apre un altro round.

| Dominio | Dubbi strutturali tipici (aprono un round) | Dubbi puntuali tipici (gamba veloce) |
|---|---|---|
| Normativo / pubblico | il soggetto e' fuori perimetro; la norma citata e' superata o abrogata; lo sportello e' chiuso o esaurito; due strumenti che si escludono a vicenda | massimale aggiornato, data di scadenza, aliquota, codice ATECO ammesso |
| Tecnico / prodotto | la licenza e' incompatibile con l'uso previsto; il prodotto e' in end-of-life; un requisito obbligatorio non e' supportato; lock-in non dichiarato | numero di versione, data di fine supporto, prezzo di listino |
| Societario / due diligence | l'identita' del soggetto e' ambigua (omonimie, catene di controllo); un atto rilevante risulta non pubblicato; il perimetro dei soggetti da verificare e' incompleto | data di deposito, importo di bilancio, numero di iscrizione |

La distinzione non e' la gravita' del dato ma la **posta in gioco**: se l'esito
sfavorevole cambia *chi vince*, e' strutturale; se cambia *di quanto*, e' puntuale.

Combinazioni tipiche:

- **Eliminatoria dura** su un requisito non negoziabile (fuori perimetro, chiuso,
  incompatibile) + **graduatoria qualitativa** sui restanti → default
- **Solo eliminatoria** quando i candidati sopravvissuti sono pochi: portane 5-6 al
  round 1 anche se qualcuno e' debole, costa poco e evita di scartare per errore
- **Score pieno** solo dopo la Fase 4: prima della validazione delle fonti gli score
  poggiano su dati non verificati, e uno score falsamente preciso e' peggio di una
  graduatoria dichiaratamente qualitativa

Chi decide resta l'utente (Fase 5.5). Il tuo compito e' proporre la rosa con la
motivazione, non presentare una selezione come inevitabile.

## 5. Livello di anonimizzazione

Il prompt esce verso un provider esterno. Prima di comporlo, decidi con l'utente:

| Livello | Cosa esce | Quando |
|---|---|---|
| **Pieno** | dati identificativi e numeri esatti | soggetto pubblico, dati gia' pubblici, ricerca su terzi |
| **Anonimizzato** | ruolo e caratteristiche, numeri in range, nessun identificativo | default per soggetti privati |
| **Astratto** | solo il profilo tipologico ("PMI manifatturiera del Sud Italia con 2-3 M€ di fatturato") | dati sensibili, contesti competitivi |

L'anonimizzazione non degrada la ricerca se i **vincoli** restano precisi: al motore
serve sapere che il soggetto e' sotto una certa soglia dimensionale, non il suo
codice fiscale.

---

## Tre calibrazioni d'esempio

### A. Incentivi e agevolazioni per un'impresa

| Parametro | Valore |
|---|---|
| Forma | inquadramento (panorama strumenti) → dubbi (rosa 3-6 + perimetro soggettivo) → verticale · limite ricorsione **2** |
| Fonti primarie | gazzetta/registro ufficiale, banca dati normativa, siti degli enti erogatori, portali di presentazione |
| Score | pertinenza · beneficio in € · certezza del dato · finestra temporale · complessita' di candidatura (inv.) |
| Restringimento | eliminatoria su perimetro soggettivo e sportello chiuso, poi graduatoria |
| Anonimizzazione | anonimizzata (range di fatturato e dipendenti) |
| Note | il verticale deve arrivare al livello "quale modulo, quale portale, quali allegati"; i punti di giudizio professionale vanno marcati per il consulente |

### B. Scelta di una tecnologia o di un fornitore software

| Parametro | Valore |
|---|---|
| Forma | inquadramento (panorama soluzioni) → dubbi (rosa 3-5 + licenze e supporto) → verticale · limite ricorsione **1-2** |
| Fonti primarie | documentazione ufficiale versionata, repository e changelog, advisory di sicurezza, licenze, status page e SLA pubblicati |
| Score | copertura funzionale · costo totale · certezza del dato · maturita'/supporto residuo · reversibilita' (inv. lock-in) |
| Restringimento | eliminatoria su requisiti tecnici obbligatori e licenza incompatibile |
| Anonimizzazione | astratta (il caso d'uso, non il cliente) |
| Note | chiedi esplicitamente end-of-support, breaking change recenti e incidenti noti: sono i dati che i confronti commerciali omettono |

### C. Due diligence documentale su una controparte

| Parametro | Valore |
|---|---|
| Forma | inquadramento (soggetti e legami) → dubbi (identita' e perimetro sui registri) → verticale sulle criticita' · limite ricorsione **2-3**: qui l'ambiguita' d'identita' e' la norma, non l'eccezione |
| Fonti primarie | registro delle imprese, bilanci depositati, albi, atti e provvedimenti pubblicati, comunicazioni al mercato |
| Score | rilevanza del rilievo · gravita' · certezza del dato · attualita' · onere di verifica ulteriore (inv.) |
| Restringimento | tutto cio' che e' documentato passa; si stringe sulle criticita', non sui soggetti |
| Anonimizzazione | piena (i dati sono pubblici per definizione) |
| Note | qui la Fase 4 e' il cuore: un rilievo senza documento allegato non e' un rilievo. Nessuna inferenza reputazionale: solo atti. |
