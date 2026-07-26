# Riferimento — Calibrare il funnel su un dominio nuovo

Il funnel e' agnostico. A cambiare da un dominio all'altro sono **cinque parametri**,
che vanno fissati in Fase 1 con l'utente e dichiarati nel sinottico finale. Questo
file spiega come scegliere ciascuno e mostra tre calibrazioni d'esempio.

Non sono preset da importare: sono esempi di come si ragiona.

---

## 1. Numero di round

| Round | Quando ha senso |
|---|---|
| **1** | il perimetro e' gia' noto e serve solo profondita' su un candidato unico. Non e' un funnel, e' un dossier. |
| **2** | il campo e' piccolo (< 10 candidati plausibili) o il tempo e' il vincolo dominante |
| **3 (default)** | campo ampio e decisione a valle che vale piu' di un'ora di ricerca |
| **4+** | solo se la Fase 5 rivela che l'imbuto si e' stretto sul candidato sbagliato. Non pianificarli in anticipo: pianifica il gate che li decide. |

Regola pratica: ogni round costa 10-40 minuti e produce un artefatto. Se non sai
dire **quale decisione** cambia in base all'esito di un round, quel round non serve.

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

## 4. Criterio di restringimento fra i round

Cosa fa passare un candidato dal round N al round N+1. Va deciso **prima** di
leggere i risultati, altrimenti si razionalizza a posteriori.

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
| Round | 3 (panorama strumenti → rosa 3-6 → verticale sullo strumento scelto) |
| Fonti primarie | gazzetta/registro ufficiale, banca dati normativa, siti degli enti erogatori, portali di presentazione |
| Score | pertinenza · beneficio in € · certezza del dato · finestra temporale · complessita' di candidatura (inv.) |
| Restringimento | eliminatoria su perimetro soggettivo e sportello chiuso, poi graduatoria |
| Anonimizzazione | anonimizzata (range di fatturato e dipendenti) |
| Note | il verticale deve arrivare al livello "quale modulo, quale portale, quali allegati"; i punti di giudizio professionale vanno marcati per il consulente |

### B. Scelta di una tecnologia o di un fornitore software

| Parametro | Valore |
|---|---|
| Round | 3 (panorama soluzioni per categoria → rosa 3-5 → verticale sulla candidata) |
| Fonti primarie | documentazione ufficiale versionata, repository e changelog, advisory di sicurezza, licenze, status page e SLA pubblicati |
| Score | copertura funzionale · costo totale · certezza del dato · maturita'/supporto residuo · reversibilita' (inv. lock-in) |
| Restringimento | eliminatoria su requisiti tecnici obbligatori e licenza incompatibile |
| Anonimizzazione | astratta (il caso d'uso, non il cliente) |
| Note | chiedi esplicitamente end-of-support, breaking change recenti e incidenti noti: sono i dati che i confronti commerciali omettono |

### C. Due diligence documentale su una controparte

| Parametro | Valore |
|---|---|
| Round | 2-3 (identificazione soggetti e legami → verifica sui registri → verticale sulle criticita' emerse) |
| Fonti primarie | registro delle imprese, bilanci depositati, albi, atti e provvedimenti pubblicati, comunicazioni al mercato |
| Score | rilevanza del rilievo · gravita' · certezza del dato · attualita' · onere di verifica ulteriore (inv.) |
| Restringimento | tutto cio' che e' documentato passa; si stringe sulle criticita', non sui soggetti |
| Anonimizzazione | piena (i dati sono pubblici per definizione) |
| Note | qui la Fase 4 e' il cuore: un rilievo senza documento allegato non e' un rilievo. Nessuna inferenza reputazionale: solo atti. |
