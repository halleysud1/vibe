---
name: deep-research
description: "Protocollo portabile per cicli di ricerca profonda multi-round con Google Deep Research (Interactions API, task long-running 10-40 min) piu' gamba grounded veloce. Funnel ricorsivo a tre stadi tendenziali — inquadramento del problema, chiusura dei dubbi, focalizzazione verticale — dove controllo delle fonti e confronto a due gambe girano dopo ogni round e i dubbi strutturali si chiudono con round dedicati PRIMA di stringere l'imbuto, cosi' l'errore di premessa non si scopre a funnel speso. Matrice di accordo arbitrata sulla fonte primaria, scoring, sinottico auditabile con traccia della ricorsione, blueprint di state machine per il full-auto. Usa questa skill quando l'utente chiede una deep research, una ricerca approfondita o multi-round, uno scouting, una due diligence documentale, un'analisi normativa o di mercato, un benchmark di soluzioni, oppure parla di Gemini Deep Research, funnel di ricerca, ricerca long-running in background."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, AskUserQuestion
---

# /deep-research — Cicli di ricerca profonda a imbuto

Skill per condurre una ricerca **profonda, verificata e tracciabile** su un tema
arbitrario, usando Deep Research come motore e Claude come orchestratore critico.

Il principio che regge tutto: **nessun output LLM e' autoritativo per default**.
Deep Research gira 10-40 minuti e cita decine di fonti, e puo' comunque sbagliare
una data, un'aliquota o un riferimento normativo. Il valore del ciclo non sta nel
lanciare la ricerca: sta nel funnel che la restringe e nel doppio controllo che la
verifica sulla fonte primaria.

**Lingua di lavoro: quella dell'utente** (le fonti restano nella lingua originale).

## Quando usare

- L'utente chiede una **ricerca approfondita** su un tema che richiede fonti
  ufficiali e non una risposta a memoria: normativa, incentivi, scouting fornitori,
  due diligence su un soggetto, analisi di mercato, benchmark tecnologico
- Serve un **artefatto consegnabile** (dossier, sinottico, scheda per un terzo
  professionista) che qualcuno dovra' poter verificare riga per riga
- L'utente vuole **automatizzare** un ciclo di ricerca ricorrente in un progetto
  agentificato (vedi `templates/fullauto/`)

## Quando NON usare

- **Una domanda secca con risposta breve**: usa `WebSearch`/`WebFetch` diretti.
  Deep Research ha un floor di ~10 minuti anche su prompt banali.
- **Ricerca dentro il codice o i file del progetto**: sono `Grep`/`Glob`/subagent.
- **Il tema richiede fonti chiuse** (banche dati a pagamento, intranet, documenti
  che l'utente ha sul disco): Deep Research vede solo il web pubblico. In quel
  caso il funnel serve al massimo come cornice metodologica.
- **L'utente ha fretta e accetta meno profondita'**: allora si usa solo
  `grounded_research.py` (1-3 min), dichiarandolo nel report.

## Installazione

```bash
pip install "google-genai>=2.0.0"
```

Serve una chiave in ambiente oppure in `.env` / `.env.local` / `.env.txt`
(cercati risalendo dalla CWD):

```
GEMINI_API_KEY=...
```

Opzionali, per non hardcodare i modelli (regola anti-overfit):

```
DEEPRESEARCH_AGENT=deep-research-max-preview-04-2026   # agent Deep Research corrente
GROUNDED_MODEL=gemini-3.1-pro-preview                  # modello della gamba veloce
RESEARCH_OUT_DIR=data/ricerche                         # cartella artefatti grezzi
```

Check preliminare (non stampa mai i valori, solo prefisso e lunghezza):

```bash
python skills/deep-research/scripts/env_loader.py
```

> `google-genai < 2.0.0` non funziona: lo schema legacy `outputs[]` e' stato
> rimosso dall'API. Sintomo: *"legacy Interactions API schema is no longer supported"*.

## Regole non negoziabili

1. **Mai lanciare un round senza aver mostrato il prompt** all'utente e ottenuto
   conferma esplicita via `AskUserQuestion`. Un round costa 10-40 minuti: un
   prompt sbagliato costa tutto quel tempo piu' il tempo per rifarlo.
2. **Mai retry automatico.** Se lo script esce con codice != 0, mostra l'errore in
   chiaro e fermati. L'utente decide se rilanciare, cambiare prompt o ripiegare.
3. **Mai stampare o loggare la API key.** Solo prefisso e lunghezza.
4. **Mai attendere in polling manuale.** Lancia con `run_in_background: true` e
   aspetta la notifica di completamento del task. Un solo `tail` di sanity ~10s
   dopo il lancio (per verificare che la `create` sia stata accettata) e' lecito;
   altri check solo se l'utente chiede "a che punto siamo?".
5. **Mai inventare o completare dati.** Un dato che la fonte non conferma va
   marcato **non confermato** e mostrato come tale, non ripulito.
6. **Il cancello non si salta.** Dopo ogni round: riepilogo dei dubbi classificati +
   `AskUserQuestion` (apri un round di dubbi / stringi allo stadio successivo /
   ri-mira il round appena fatto / chiudi un puntuale con la gamba veloce / stop
   anticipato col sinottico).
7. **Fra due LLM che si contraddicono non vince la maggioranza: vince la fonte
   primaria.** Se la fonte primaria non e' conclusiva, il dato resta marcato
   "da validare" nel report finale.
8. **Non si stringe l'imbuto su un dubbio aperto.** Un dubbio strutturale si chiude
   con un round dedicato prima di passare allo stadio successivo. Se il limite di
   ricorsione e' esaurito e il dubbio resta, il funnel si ferma e decide l'utente:
   procedere e' una sua scelta esplicita, non un default.

## Il ciclo in breve

**Tre round e' la forma tendenziale**, non un numero fisso: lo stadio dei dubbi si
espande per ricorsione quando il controllo lo impone.

| Stadio | Round | Scopo |
|---|---|---|
| **1 — Inquadramento** | 1 | affrontare il problema: panorama largo dei candidati |
| **2 — Dubbi** | 1, di piu' per ricorsione | chiudere i dubbi **strutturali** che il controllo sul round precedente ha fatto emergere |
| **3 — Focalizzazione** | 1 | verticale sul candidato scelto — **solo a dubbi chiusi** |

```
Fase 0  preflight (chiave, dipendenza, artefatti preesistenti)
Fase 1  inquadramento (domanda, fonti primarie, criteri, limiti di ricorsione)
   │
   ▼
Fase 2  composizione prompt del round  →  APPROVAZIONE UTENTE
Fase 3  lancio in background  →  attesa notifica  →  JSON su disco
Fase 4  CONTROLLO delle fonti del round (WebFetch sugli URL, download documenti)
Fase 5  CONFRONTO: fact-check · second-opinion · matrice di accordo · scoring
        5.5 CANCELLO — classifica i dubbi e decide dove si va
   │
   ├─ dubbio strutturale aperto ──► round di DUBBI (torna a Fase 2) ──┐
   │                                                                  │
   │   ◄──────────── ricorsione, entro il limite dichiarato ──────────┘
   │
   ├─ limite raggiunto con dubbi aperti ──► STOP: non si stringe, decide l'utente
   │
   └─ nessun dubbio strutturale ──► round di FOCALIZZAZIONE ──► Fase 6 sinottico
```

**L'invariante che regge tutto: non si stringe l'imbuto su un dubbio aperto.**
Restringere su una premessa non verificata e' il modo tipico di scoprire l'errore
*dopo* aver speso il round piu' profondo — cioe' quando costa piu' caro. Meglio
quattro round di cui uno speso a smontare un dubbio, che tre round su una base
sbagliata.

Controllo (Fase 4) e confronto (Fase 5) girano dopo **ogni** round, non solo alla
fine: sono loro a produrre i dubbi che alimentano lo stadio successivo.

Gli artefatti su disco — non il contesto della conversazione — sono lo stato del
ciclo. E' cio' che rende il ciclo riprendibile dopo un compact, un riavvio o un
passaggio di mano, e cio' che tiene la traccia dei dubbi aperti e chiusi.

## Layout degli artefatti (default configurabile)

```
data/ricerche/                                   # grezzo (RESEARCH_OUT_DIR)
  <data>_<tema>_<stadio>_prompt.md               # prompt approvato dall'utente
  <data>_<tema>_<stadio>.json                    # artefatto completo (fonte di verita')
  <data>_<tema>_<stadio>_response.md             # solo il testo del report
  <data>_<tema>_<stadio>.log                     # timing, eventi, interaction_id
ricerche/<tema>/
  candidati/<slug>/scheda.md                     # una scheda per candidato
  candidati/<slug>/docs/                          # documenti ufficiali scaricati
  DUBBI.md                                        # registro dei dubbi: aperti, chiusi, come
  SINOTTICO.md                                    # output finale
```

`<stadio>` rende leggibile la forma del funnel dal solo nome dei file:
`r1-inquadramento`, `r2-dubbi1`, `r2-dubbi2`, `r3-focus`. La ricorsione si vede a
occhio in un `ls`, e il `tag` passato agli script e' `<data>_<tema>_<stadio>`
(deriva JSON, log e response da solo). `<data>` = `YYYY-MM-DD`.

`DUBBI.md` e' il registro vivo della ricorsione — una riga per dubbio: *enunciato ·
classe · da quale round e' emerso · come e' stato chiuso (o perche' e' aperto)*.
Va aggiornato a ogni cancello e riportato nel sinottico: senza questo la
ricorsione diventa un costo opaco che nessuno sa giustificare a posteriori.

---

## Fase 0 — Preflight

1. `python skills/deep-research/scripts/env_loader.py` → `GEMINI_API_KEY` presente?
   Se manca: fermati e chiedi all'utente di configurarla. Non proseguire "a vuoto".
2. `Glob data/ricerche/*.json` → esiste gia' una ricerca sullo stesso tema?
   - **< 30 giorni**: proponi via `AskUserQuestion` di riusarla come base (lo
     stadio di inquadramento e' gia' fatto) invece di ripartire da zero.
   - **Non terminata** (prompt presente, JSON assente): controlla il log per un
     `interaction_id` e proponi il recovery con `--resume-id` — non rilanciare una
     ricerca gia' pagata.
3. Verifica la dipendenza: `python -c "import google.genai"`. Se manca, mostra il
   comando di install e fermati.

## Fase 1 — Inquadramento del dominio

Il funnel e' agnostico; a essere specifici sono **quattro parametri** che vanno
fissati qui, con l'utente, e riportati in testa al sinottico finale.

Usa `AskUserQuestion` (blocchi, non una domanda per volta) per raccogliere:

| Parametro | Cos'e' | Default se l'utente non ha preferenze |
|---|---|---|
| **Domanda di ricerca** | Cosa si vuole sapere e per decidere cosa | — obbligatoria, riformulala e fatti confermare |
| **Soggetto/contesto** | Chi o cosa e' l'oggetto (azienda, prodotto, ente, tecnologia) e i vincoli che lo caratterizzano | file di profilo del progetto, se esiste |
| **Fonti primarie autorevoli** | Quali domini valgono come prova e quali no | siti istituzionali del dominio + documentazione ufficiale del produttore; blog e aggregatori mai come prova |
| **Criteri di valutazione** | Le dimensioni su cui i candidati verranno scorati | 5 dimensioni × 0-10 (vedi 5.4) |
| **Profondita'** | Forma del funnel | 3 round tendenziali: inquadramento → dubbi → focalizzazione |
| **Limite di ricorsione** | Quanti round di dubbi al massimo prima di fermarsi e chiedere | 2 (cioe' fino a 4 round totali); oltre, il funnel si ferma e decide l'utente |
| **Anonimizzazione** | Il prompt esce verso Google: dati identificativi dentro o fuori | varianti "pieno" e "anonimizzato" proposte in Fase 2 |

Il limite di ricorsione va **dichiarato prima di partire**, non deciso quando si e'
già dentro: e' la differenza fra un budget e una resa. Vale anche il verso opposto —
se il controllo sul round di inquadramento non trova dubbi strutturali, lo stadio 2
si salta e si va diretti al verticale, dichiarandolo nel sinottico. La forma
tendenziale sono tre round, non tre round obbligatori.

Se esiste un file di profilo/contesto nel progetto (`company/profile.md`,
`PROJECT_SPEC.md`, un dossier), leggilo e proponi i valori derivati: non
intervistare l'utente su cose che il progetto documenta gia'.

## Fase 2 — Composizione e approvazione del prompt

1. Parti dal template dello stadio:

   | Stadio | Template |
   |---|---|
   | 1 — inquadramento | `prompts/round_esplorazione.md` |
   | 2 — dubbi (fattuali/strutturali) | `prompts/round_dubbi.md` |
   | 2 — dubbi (comparativi: "quale fra questi") | `prompts/round_shortlist.md` |
   | 3 — focalizzazione | `prompts/round_verticale.md` |
   | fuori funnel — dubbio puntuale, gamba veloce | `prompts/round_mirato.md` |
   | fuori funnel — second-opinion | `prompts/audit_second_opinion.md` |
2. Sostituisci **tutti** i segnaposto `{{...}}`. Gli script rifiutano un prompt che
   contiene ancora `{{`: e' un guard-rail, non un dettaglio.
3. Un prompt di round efficace contiene sempre e in quest'ordine:
   contesto del soggetto → domanda esplicita → **elenco puntuale delle domande a
   cui rispondere** → formato di output richiesto (tabelle/campi, cosi' il round
   successivo puo' parsarlo) → fonti da privilegiare e fonti da non usare come
   prova → istruzione di **dichiarare l'incertezza** invece di colmarla → per i
   round ≥ 1, l'istruzione di **confermare o smentire** i dati del round precedente.
4. Prepara due varianti se ci sono dati sensibili (pieno / anonimizzato con range
   al posto dei valori esatti) e fai scegliere via `AskUserQuestion`, includendo
   sempre l'opzione "edita manualmente".
5. Scrivi il prompt approvato in `data/ricerche/<data>_<tema>_<stadio>_prompt.md`.

## Fase 3 — Lancio del round

```bash
python skills/deep-research/scripts/deep_research.py \
  --prompt-file data/ricerche/<data>_<tema>_<stadio>_prompt.md \
  --tag <data>_<tema>_<stadio>
```

Con `Bash` e `run_in_background: true`. Lo script scrive da solo JSON, log e
`_response.md` sotto `RESEARCH_OUT_DIR`.

- **Aspetta la notifica di completamento.** Niente `sleep`, niente `tail` ripetuti.
- Un solo `tail` del log ~10s dopo il lancio per confermare `status=in_progress`
  con un `interaction_id`: se non c'e', la `create` e' stata rifiutata.
- **Exit code != 0** → leggi il log, mostra l'errore in chiaro, fermati:

| Exit | Significato | Cosa fare |
|---|---|---|
| 1 | terminale ma non `completed` (`incomplete`, `budget_exceeded`, `failed`) | mostra lo stato; il JSON esiste e puo' contenere output parziale utile |
| 2 | argomenti o prompt non validi (incluso `{{` residuo, output gia' esistente) | correggi e rilancia |
| 3 | `google-genai` mancante o troppo vecchio | `pip install -U "google-genai>=2.0.0"` |
| 4 | `create` fallita (chiave, quota, agent inesistente) | verifica chiave e nome agent; **non** ritentare in loop |
| 5 | max-wait client superato | il task prosegue server-side: `--resume-id <id dal log>` |

Ripiego esplicito (Deep Research indisponibile o l'utente vuole velocita'):
`grounded_research.py --prompt-file ... --tag ...` (1-3 min) — e annotalo nel
sinottico: la copertura delle fonti non e' comparabile.

## Fase 4 — Controllo: le fonti del round

Il report cita URL: finche' non li apri, sono affermazioni.

1. `Read` del JSON del round (campo `response_text`; `citations` e `unique_domains`
   danno la mappa delle fonti usate).
2. Estrai i candidati (strumenti, fornitori, soluzioni, documenti…) e per ciascuno
   genera uno **slug kebab-case**.
3. `WebFetch` della pagina ufficiale di ogni candidato — priorita' ai domini
   dichiarati primari in Fase 1, massimo ~10 per round per non bruciare tempo.
   Chiedi al fetch di estrarre i campi che il dominio richiede (in Fase 1 li hai
   fissati) piu' sempre: chi pubblica, data del documento, stato corrente,
   riferimento formale, link ai documenti allegati.
4. Esito per candidato:
   - **pagina viva e coerente** → `ricerche/<tema>/candidati/<slug>/scheda.md` con
     frontmatter YAML + sezione "Fonti" con gli URL; scarica i documenti ufficiali
     in `docs/` (cap dimensione, salta con messaggio se sfora) e salva anche
     l'HTML grezzo della pagina: le pagine cambiano, il tuo dossier no.
   - **pagina morta / redirect a homepage / archivio / incoerente col claim** →
     scheda con `confermato: false` e nota sull'errore. Nessun download.
5. Le citazioni che nessuna pagina viva conferma sono un segnale: annotale, non
   cancellarle.

## Fase 5 — Confronto: cross-check a due gambe

### 5.1 Fact-check deterministico (Claude, dopo ogni round)

Per ogni scheda confermata:

- **Riferimenti formali** (norma, standard, decreto, versione, brevetto, DOI):
  verificali sulla fonte istituzionale, uno per uno. Marca ciascuno
  **CONFERMATO / SOSPETTO / NON RINTRACCIATO / CONTRADDETTO**.
- **Numeri**: rifai i calcoli espliciti (percentuali, totali, proiezioni,
  conversioni valuta/unita'). Riporta gli scostamenti, non sistemarli in silenzio.
- **Coerenza interna**: lo stesso candidato descritto due volte con dati diversi
  nello stesso report e' un red flag da annotare.

### 5.2 Second-opinion grounded (a valle dell'ultimo round)

Un modello **diverso** e piu' economico rilegge il corpus con mandato adversarial:

```bash
python skills/deep-research/scripts/grounded_research.py \
  --prompt-file data/ricerche/<data>_<tema>_audit_prompt.md \
  --tag <data>_<tema>_audit
```

Prompt da `prompts/audit_second_opinion.md`. Mostralo e fallo approvare come ogni
altro prompt. Se il progetto ha accesso a un provider terzo, una seconda
second-opinion da un vendor diverso e' meglio di due dal medesimo.

### 5.3 Matrice di accordo (arbitro: la fonte primaria)

| Claim | Deep Research | Second-opinion | Fact-check su fonte primaria | Esito |
|---|---|---|---|---|
| es. soglia applicabile | 180% | +80% | pagina ufficiale: "180%" | CONCORDE CON DR — auditor smentito |

Esiti: **CONCORDI** · **DISCORDI-RISOLTO** (documenta chi aveva torto) ·
**DISCORDI-IRRISOLTO** (fonte non conclusiva → il dato resta "da validare" nella
scheda **e** nel sinottico). Non c'e' un quarto esito: "probabilmente giusto" non
esiste.

> Perche' questa fase esiste: in un caso reale l'auditor ha smentito a torto due
> dati corretti del Deep Research **e** nello stesso giro ha colto due errori
> concettuali veri. Entrambe le gambe sbagliano; solo la fonte primaria arbitra.

### 5.4 Scoring multi-dimensione

Default: 5 dimensioni × 0-10 = totale 0-50, priorita' **alta ≥ 35 / media 20-34 /
bassa < 20**. Le dimensioni predefinite sono uno **schema, non un dogma**:
adattale al dominio in Fase 1 e scrivile nel sinottico.

| Dimensione | Domanda | Nota |
|---|---|---|
| **Pertinenza** | quanto risponde davvero alla domanda per *questo* soggetto | 0 = fuori perimetro |
| **Valore** | magnitudine del beneficio/impatto atteso | esplicita l'unita' di misura |
| **Certezza del dato** | fonte primaria viva + riferimenti confermati | penalizza i DISCORDI-IRRISOLTO |
| **Tempo** | finestra utile residua / time-to-value | |
| **Costo o complessita'** (invertito) | 10 = semplice, immediato, economico | invertita: dichiaralo sempre |

Scrivi gli score nel frontmatter della scheda con le motivazioni nel corpo, e
riporta **quale round** li ha prodotti.

### 5.5 Il cancello: classifica i dubbi e decidi dove si va

Questo e' il punto in cui il funnel decide se stringere o approfondire, e dove vive
la ricorsione. Si esegue dopo **ogni** round.

#### a. Enuncia i dubbi

Un dubbio non e' un'impressione: e' una **proposizione falsificabile** che, se falsa,
cambia qualcosa. "La fonte non e' chiarissima" non e' un dubbio. "Lo strumento X
richiede la sede operativa nella regione, e il soggetto non l'ha" e' un dubbio.

Le sorgenti sono i tre passi precedenti: riferimenti **CONTRADDETTI** o **NON
RINTRACCIATI** (5.1), rilievi dell'auditor non ancora arbitrati (5.2),
**DISCORDI-IRRISOLTO** della matrice (5.3), piu' le pagine morte o incoerenti della
Fase 4 e le lacune che il report stesso dichiara.

#### b. Classificali — e' la classificazione che tiene in piedi la ricorsione

| Classe | Definizione operativa | Trattamento |
|---|---|---|
| **Strutturale** | se il dubbio si risolve nel verso sfavorevole, **cambia la selezione o invalida il perimetro** (candidato inapplicabile, norma superata, premessa sbagliata, cumulabilita' che salta) | **round di dubbi** (stadio 2) |
| **Puntuale** | un dato isolato: una data, una soglia, una versione, un importo. Sbagliato costa una correzione, non la strategia | **gamba veloce** (`round_mirato.md`, 1-3 min) oppure un `WebFetch` diretto — mai un round da 30 minuti |
| **Irriducibile** | la fonte pubblica non e' conclusiva e non lo sara' | si **dichiara** e si marca "da validare con la figura professionale competente": non si insiste |

Nel dubbio sulla classe, **tratta come strutturale**: l'errore e' asimmetrico. Un
dubbio strutturale scambiato per puntuale ti fa arrivare al verticale su una base
falsa; un puntuale trattato come strutturale ti costa un round. Non sono lo stesso
danno.

#### c. Decidi

1. **Nessun dubbio strutturale aperto** → si stringe: prossimo stadio.
2. **Dubbi strutturali aperti, limite non raggiunto** → **round di dubbi**
   (`round_dubbi.md`, o `round_shortlist.md` se il dubbio e' comparativo). Il
   prompt deve attaccare i dubbi enunciati **e** rifare la domanda di premessa:
   *questo perimetro e' ancora quello giusto?*
3. **Round a vuoto**: l'ultimo round di dubbi non ne ha aperti di nuovi e ha chiuso
   quelli che c'erano → si stringe.
4. **Limite raggiunto con dubbi ancora aperti** → **STOP: non si stringe.**
   Presenta i dubbi irrisolti e fai scegliere all'utente via `AskUserQuestion`:
   concedere un altro round · procedere al verticale accettando il rischio (con i
   dubbi marcati in modo prominente in sinottico e schede) · chiudere con un
   sinottico parziale che elenca cosa resta da verificare prima di poter decidere.
   In full-auto il run **si mette in pausa** e notifica: non decide da solo.

Aggiorna `DUBBI.md` prima di procedere, sempre. Un dubbio chiuso senza traccia di
*come* e' stato chiuso e' un dubbio che tornera'.

#### d. Riepilogo in chat (a ogni cancello)

```
<stadio> completato — <r1-inquadramento | r2-dubbi<k> | r3-focus>
- Candidati emersi/approfonditi: <X>   confermati su fonte viva: <Y>
- Top per score: <lista>
- Dubbi: <n> strutturali · <n> puntuali · <n> irriducibili
  - strutturali aperti: <enunciati, uno per riga>
  - chiusi in questo giro: <enunciato → esito → fonte>
- Riferimenti CONTRADDETTI o NON RINTRACCIATI: <lista>
- Conflitti fra le due gambe: <n> (risolti <n>, irrisolti <n>)
- Ricorsione: round di dubbi <k>/<limite>
- Artefatti: <path JSON, schede, documenti, DUBBI.md>
→ Proposta: <round di dubbi su ... | verticale su ... | stop con sinottico parziale>
```

Poi `AskUserQuestion` con la proposta come prima opzione, piu': ri-mira il round
appena fatto con prompt corretto · chiudi un dubbio con la gamba veloce invece di un
round · **stop anticipato e sinottico**. La proposta e' motivata, non imposta: chi
decide di stringere e' l'utente.

## Fase 6 — Sinottico finale

`ricerche/<tema>/SINOTTICO.md`, con frontmatter che rende il ciclo auditabile:

```yaml
---
data_ricerca: ""
domanda_ricerca: ""
soggetto: ""
motori_usati: []          # agent/modelli effettivamente usati, per round
round_eseguiti: []        # in ordine: [r1-inquadramento, r2-dubbi1, r3-focus]
n_round_dubbi: 0          # profondita' effettiva della ricorsione
limite_ricorsione: 2      # il budget dichiarato in Fase 1
funnel_completo: true     # false se interrotto: spiega perche' in sintesi
stretto_su_dubbi_aperti: false      # true SOLO per decisione esplicita dell'utente
criteri_valutazione: []   # le dimensioni di score usate in questo ciclo
fonti_primarie: []        # domini accettati come prova
n_candidati: 0
n_confermati: 0
n_claim_contraddetti: 0
n_conflitti_irrisolti: 0
n_dubbi_chiusi: 0
n_dubbi_aperti: 0         # se > 0, la sintesi esecutiva DEVE aprirsi da qui
---
```

Corpo: sintesi esecutiva (cosa e' emerso, cluster, top 3 con score) · tabella
sinottica ordinata per score con una colonna per dimensione · **Audit report**
(anomalie, claim contraddetti, matrice di accordo, gap non coperti) · **traccia
della ricorsione** · schede dettagliate · prossimi passi operativi · disclaimer con
i limiti dichiarati (round saltati o compressi, fonti chiuse non accessibili, dati
"da validare").

La traccia della ricorsione e' la sezione che rende difendibile il costo del funnel:

| Dubbio | Classe | Emerso da | Round aperto | Esito | Fonte |
|---|---|---|---|---|---|
| es. sede operativa richiesta in regione | strutturale | controllo r1 | r2-dubbi1 | CHIUSO — richiesta solo per la misura B | pagina ufficiale, art. 4 |
| es. massimale aggiornato a giugno | puntuale | matrice r1 | — (gamba veloce) | CHIUSO — 200k | decreto in GU |
| es. cumulabilita' con incentivo Y | strutturale | controllo r2-dubbi1 | — | **APERTO** — fonte non conclusiva | — |

Se `n_dubbi_aperti > 0` la sintesi esecutiva si apre dichiarandolo, prima di
qualunque raccomandazione: chi legge deve sapere su cosa poggia il verticale prima
di leggere la conclusione, non dopo.

Chiudi in chat con: path del file, top 3 con score e scadenze/finestre, anomalie
critiche, **dubbi rimasti aperti**, cosa resta da validare umanamente.

---

## Full-auto (progetti agentificati)

Il ciclo con gate umani vive in Claude Code. Quando l'utente lo vuole **ricorrente
e non presidiato** (es. un agente Agno/AgentOS che lo lancia da chat o a
schedule), il gate umano va sostituito da una **state machine persistente**: un
round dura piu' di qualunque turno di chat, quindi non puo' stare dentro una run
sincrona.

`templates/fullauto/` contiene il blueprint:

| File | Cosa e' |
|---|---|
| `pipeline.py.template` | state machine **ricorsiva**: `compose → wait → controllo → confronto → cancello` per ogni round, con il cancello che rientra in un round di dubbi (fino al limite) oppure passa al verticale. Run persistiti su JSON con i dubbi aperti nello stato, runner daemon che avanza **di un solo step** per giro, retry per stato, resume al riavvio, notifiche proattive, e stato `attesa_decisione` quando il limite scade con dubbi aperti |
| `research_tools.py.template` | i due tool per la chat: `launch_research(prompt, tag)` (detached, ritorna subito) e `check_research(tag)` (completata/in corso/non trovata) |
| `WIRING.md` | come innestarli: composizione dei prompt delegata all'LLM, notifiche, scheduler, cosa NON automatizzare |

Regola di progetto: in full-auto **il gate umano non sparisce, si sposta** — diventa
una notifica proattiva a ogni transizione piu' un punto di conferma prima di
qualunque azione irreversibile a valle della ricerca. Se il progetto non ha un
canale per notificare, non e' pronto per il full-auto.

Vedi anche `vibecoding:agentify`: costruisce l'agente e porta il ruolo
`high-level-ops` (run schedulate), il tool-guard con autonomy gates L0-L5 e
l'audit trail — cioe' il contesto in cui questa pipeline va innestata.

## Anti-pattern

- ❌ **Stringere l'imbuto su un dubbio aperto** — il piu' costoso di tutti. Porti
  un dubbio strutturale dentro il verticale, spendi il round piu' profondo, e lo
  scopri alla fine: il funnel intero e' da rifare. Se un dubbio puo' cambiare la
  selezione, si chiude prima.
- ❌ **Aprire un round da 30 minuti per un dubbio puntuale**: una data o un
  massimale si chiudono con la gamba veloce o un `WebFetch`. La ricorsione e' per i
  dubbi che cambiano la strategia, non per quelli che cambiano una cifra.
- ❌ **Ricorsione senza limite dichiarato**: senza un budget fissato in Fase 1 il
  funnel non converge, perche' ogni round di dubbi ne produce di nuovi — e' la
  natura del mestiere, non un difetto del metodo.
- ❌ **Chiudere un dubbio senza scrivere come**: `DUBBI.md` non e' burocrazia. Un
  dubbio chiuso a memoria riapre al giro successivo, o peggio resta chiuso a torto.
- ❌ **Un round unico gigante** invece del funnel: il prompt largo produce un
  report largo e superficiale, e non hai nessun punto in cui correggere la rotta.
- ❌ **Lanciare senza far approvare il prompt**: 30 minuti buttati su un
  fraintendimento che una domanda avrebbe evitato.
- ❌ **Polling manuale / `sleep` in attesa del round**: blocca la sessione per
  mezz'ora e non accelera nulla di un microsecondo.
- ❌ **Retry automatico su fallimento**: se la `create` e' stata rifiutata per
  quota o agent inesistente, ritentare peggiora. Errore esplicito, decide l'utente.
- ❌ **Trattare il report come verita'**: senza Fase 4-5 stai consegnando un testo
  plausibile, non una ricerca.
- ❌ **Risolvere i disaccordi a maggioranza fra LLM** o, peggio, scegliendo la
  risposta piu' comoda. Arbitra la fonte primaria o si resta "da validare".
- ❌ **Rilanciare una ricerca il cui task e' ancora vivo**: cerca
  l'`interaction_id` nel log e usa `--resume-id`.
- ❌ **Hardcodare il nome dell'agent/modello** nei sorgenti del progetto ospite:
  passa da env (`DEEPRESEARCH_AGENT`, `GROUNDED_MODEL`). Cambiano ogni pochi mesi.
- ❌ **Cancellare le citazioni non confermate** per far quadrare il report: sono
  informazione, ed e' la piu' preziosa che hai sull'affidabilita' del round.

## Checklist (per chi usa o modifica la skill)

- [ ] `env_loader.py` trova la chiave e **non** stampa mai il valore
- [ ] Un prompt con `{{...}}` residuo viene rifiutato da entrambi gli script
- [ ] Il JSON del round contiene `response_text` non vuoto e `citations_count > 0`
- [ ] Un secondo lancio con lo stesso `--tag` non sovrascrive nulla senza `--overwrite`
- [ ] Ogni candidato del sinottico ha una scheda con URL verificato e stato
      `confermato` esplicito
- [ ] Ogni riferimento formale citato ha un esito in `audit_notes.normativa`
- [ ] La matrice di accordo e' presente e i DISCORDI-IRRISOLTO sono marcati anche
      nelle schede, non solo nella matrice
- [ ] Il frontmatter del sinottico dichiara motori usati, round eseguiti e criteri
- [ ] Se il funnel e' stato compresso, il sinottico lo dice in sintesi esecutiva
- [ ] **Ogni dubbio strutturale ha un esito**: chiuso con fonte, oppure aperto e
      dichiarato. Nessun dubbio evapora fra due round
- [ ] **`DUBBI.md` esiste e combacia** con la traccia della ricorsione nel sinottico
- [ ] Nessuno stadio e' stato saltato con dubbi strutturali aperti, salvo decisione
      esplicita dell'utente registrata in `stretto_su_dubbi_aperti: true`
- [ ] Il limite di ricorsione era dichiarato **prima** del primo round
- [ ] I dubbi puntuali sono stati chiusi con la gamba veloce, non con round interi
      (se no, il funnel costa il triplo del necessario: rivedi la classificazione)

## Limiti noti

- **Solo web pubblico**: nessun accesso a banche dati chiuse, portali autenticati o
  documenti locali. Vanno forniti nel prompt o verificati a mano.
- **Floor temporale ~10 minuti** per round, indipendente dalla lunghezza del prompt.
- **Cancel via API poco affidabile** (osservato 500): per abortire, lascia scadere
  `--max-wait` lato client — il task lato Google terminera' per conto suo.
- **Nomi degli agent volatili**: `deep-research-*-preview-*` cambia nel tempo; e'
  un default da env, non una costante.
- **Provider singolo** (Google): la second-opinion viene dallo stesso vendor a meno
  che il progetto ospite non abbia un secondo provider configurato. Due gambe dello
  stesso fornitore condividono qualche bias.
- **La ricorsione non garantisce la convergenza**: i dubbi strutturali possono
  essere genuinamente irriducibili sulle fonti pubbliche. Il limite serve a
  trasformare un pozzo senza fondo in una decisione consapevole, non a chiudere i
  dubbi. Un funnel che si ferma dichiarando due dubbi aperti ha fatto il suo lavoro
  meglio di uno che li ha ignorati per arrivare a una conclusione pulita.
- **Costo**: un funnel completo a 3 round e' l'equivalente di ~1-2 ore di calcolo
  agentico. Non e' la risposta giusta a una domanda da 30 secondi.
