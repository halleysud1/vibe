# Changelog

## [5.0.0] - 2026-07-27

Release di hardening: tutti i difetti corretti qui erano **comportamentali** —
cose che facevano lavorare peggio l'agente, non refusi. Nessuna skill rimossa.

### Added — intervista d'ingresso + gate di rotta all'invocazione di agentify

Appena agentify viene invocata — prima della discovery — parte SEMPRE
un'**intervista sui casi d'uso** via `AskUserQuestion` (cosa deve fare
l'agente con esempi concreti, chi lo usa, dove gira, chi paga i modelli e se
serve più di un vendor), anche quando la richiesta sembra già chiara: la rotta
dipende dai casi d'uso, e assumerli è il modo tipico di scaffoldare la cosa
sbagliata. Le risposte confluiscono nel manifesto (`route.use_cases`) e fanno
da input alla Fase 1, che non le richiede. Sulla base delle risposte il gate
decide fra quattro rotte:
abbonamento Claude + automazione interna → **nativo Claude Code** (routine,
workflow, subagent); abbonamento Claude + agente standalone self-hosted
Anthropic-only → **Claude Agent SDK con l'auth dell'abbonamento** (hosting
libero a prezzo fisso, nessun costo a token); API Anthropic a token senza
infrastruttura → **Claude Managed Agents**; chiavi API esterne multi-vendor
(Gemini, Claude API, OpenAI, GLM, DeepSeek, …) pagate a token con hosting
libero (PC, server locale, cloud proprio) → **agentify**. Il moat dichiarato
di agentify si riduce a uno ed è netto: **multi-modello per ruolo** — se
l'agente può essere Anthropic-only, l'abbonamento vince sul costo e la skill
si ferma dicendolo. La rotta scelta si registra nel manifesto (`route.choice`
+ `route.reason`), con i limiti onesti della rotta SDK+abbonamento (quota
condivisa con l'uso interattivo, termini d'uso per servizi esposti a terzi).

### Changed — la tabella dei modelli si costruisce a ogni lancio

Rimossa la tabella statica dei default modello dalla Fase 3 (stesso principio
della rimozione dello "Stack default" da methodology: una tabella scritta nella
skill diventa il default che nessuno rimette in discussione, e i nomi/prezzi
dei modelli invecchiano in mesi). Restano i **requisiti di capability per
ruolo** (la parte stabile); id, prezzi e provider si raccolgono con una
**ricognizione al momento del lancio** — chiedendo all'utente quali chiavi ha e
verificando i listini correnti, mai dalla memoria del modello — e si datano nel
manifesto (`models.surveyed_at`). Il verdetto resta del bench e di `eval_coder`
(anti-pattern A4).

### Fixed — `_models.py`: `budget_tokens` rimosso dall'API Claude (errore 400)

Il factory traduceva il reasoning per i modelli `claude-*` in
`{"thinking": {"type": "enabled", "budget_tokens": N}}`: sui Claude 5-family la
shape è **rifiutata con un 400**, quindi ogni delega dell'Orchestrator con un
livello di reasoning verso un ruolo Claude moriva a runtime. Ora: thinking
**adattivo** + **effort** (`low`/`medium`/`xhigh` — `high` interno mappa su
`xhigh`, il livello raccomandato per l'agentic coding), mai `disabled`, mai
`budget_tokens`. Il thinking budget a token resta solo per Gemini.

### Fixed — i path degli script erano sbagliati per chiunque installi il plugin

Nessuna skill usava `${CLAUDE_PLUGIN_ROOT}`: 15 invocazioni su 3 skill puntavano
a `skills/…` o `.claude/skills/…`, path che esistono solo se la skill è copiata
dentro il progetto. Installato da marketplace il plugin vive altrove, quindi la
**Fase 0 di `agentify` falliva al primo comando** — e il danno non è l'errore, è
che poi il modello improvvisa (cerca il file, o riscrive lo script a mano).

- `agentify`, `deep-research`, `md-to-pdf`: tutte le invocazioni passano da
  `${CLAUDE_PLUGIN_ROOT}`; idem il docstring di `discover.py` e il riferimento
  alla cartella dei template.
- `fullauto`: `DEEPRESEARCH_SCRIPT` ora punta di default a `scripts/…` **nel
  progetto** (la destinazione che `WIRING.md` prescrive), non alla skill; WIRING
  dichiara la sorgente come `$CLAUDE_PLUGIN_ROOT`.
- Nuovo check in CI che fallisce su qualunque invocazione non prefissata.

### Changed (breaking) — il propose-and-confirm del coding-agent si sposta sul diff

`edit: propose` era il default. Ma una `propose` **non viene eseguita**: nessun
edit atterrava, `verify()` restituiva sempre lo stesso rosso e il ruolo
ri-proponeva fino a churn o kill-switch. Il ciclo `edita → verifica → itera fino
a verde`, che la skill dichiara obbligatorio, era **strutturalmente impossibile**
con la configurazione di default. In più in OUTBOX finiva il payload della call
troncato a 800 caratteri: non revisionabile e non applicabile.

- `edit` / `write` / `apply_patch` passano a `allow` nel profilo di default. Il
  contenimento del coder è **strutturale** — solo branch `agent/*`, niente push
  né merge, checkpoint reversibile, path sensibili negati dalla baseline — non
  un permesso.
- Il gate umano resta, al livello giusto: `git_propose_diff` con il **diff
  reale** e il tetto di `max_propose_diff_lines`.
- Per i ruoli non isolati su branch (es. `high-level-ops`) la raccomandazione è
  invariata: `write` ristretto alla output dir, `"*": propose`.

**Impatto**: chi ri-scaffolda un agente ottiene il nuovo profilo. Chi vuole il
comportamento precedente lo dichiara nel manifesto (`tools.permissions.edit:
propose`) — sapendo che il verify loop non chiuderà.

### Fixed — il kill-switch tagliava il paracadute

Il contatore incrementava su ogni tool call e al superamento negava tutto,
`gitops` e `verify` compresi. L'istruzione di recovery del ruolo («verify rosso
per N cicli → `git_revert_to_checkpoint()`») veniva quindi **negata proprio
quando serviva**: worktree mezzo editato, nessun modo di ripulirlo.

- Budget di grazia (`recovery_grace`, default 20) sui soli tool che non scrivono
  codice: `read`, `glob`, `grep`, `repomap`, `context`, `verify`, `gitops`.
- Il messaggio di DENY dice esplicitamente cosa resta possibile.

### Fixed — il churn detector puniva l'iterazione legittima

`_edit_counts` era monotono per tutta la run: con `churn_limit` 5, un refactor su
più batch verificati che tocca lo stesso modulo core scattava — sul file su cui
il task insiste per definizione — e negava l'edit necessario a riparare un verify
rosso. La metrica confondeva *molti edit* con *nessun progresso*.

- Nuovo `GUARD.mark_progress()`, chiamato da `verify()` a ogni VERDE: azzera i
  contatori. Si contano gli edit **dall'ultimo verde**, non dall'inizio della run.
- Il messaggio di DENY dichiara che il contatore riparte al primo verde.

### Fixed — un `TODO` dentro il system prompt, invisibile al controllo previsto

`role_coding_agent` conteneva `# TODO durante scaffolding: descrivere il
perimetro…` **dentro la stringa delle instructions**: se lo scaffolding lo
saltava, il coder partiva con "TODO: descrivi il perimetro" come definizione del
proprio scope. E non essendo un `{{ }}`, il grep prescritto dall'anti-pattern A6
non lo intercettava.

- I punti che finiscono nel system prompt sono ora placeholder veri:
  `{{ role_perimeter }}`, `{{ role_task }}`, `{{ ops_profiles }}`,
  `{{ orchestrator_flows }}`; la guida su cosa scriverci sta in un commento
  Python **fuori** dalla stringa.
- A6 riscritto: si grep-pano entrambe le forme. Nuovo check in CI.
- `CODING_AGENT_PROMPT` non fa più `read_text` nudo: se il file manca, errore
  parlante invece di stack trace all'import.

### Fixed — il gate anti-degrado era silenziosamente inerte su Windows

La definition-of-done di default usava `pytest … | tail -1`: con `shell=True` su
Windows il check fallisce sempre e, essendo `required: false`, falliva *in
silenzio*. Nessuna baseline si stabiliva mai, quindi la metrica non-decrescente —
l'intero meccanismo 4.2.0 contro il degrado — non girava. Un gate inerte è peggio
di nessun gate: ti credi coperto.

- Niente pipe POSIX nei comandi di default; il check con metrica è `required: true`.
- `metric_pattern` **obbligatorio** (regex con gruppo di cattura). Prima si
  prendeva "l'ultimo numero dell'output": bastava un `in 3.42s` nella coda per
  fissare la baseline sul tempo di esecuzione, e da lì qualunque coverage passava.

### Changed — `/vibecoding:init` è un entry point sottile

Comando e skill non erano solo duplicati (300 righe contro 291): **divergevano**.
`init.md` aveva il detect del contesto e la chiusura con journal/memory che la
skill non aveva; `skill-bootstrap` aveva la verifica finale che il comando non
aveva; la regola sulla `description` era formulata diversamente nei due file.
Stesso task, due percorsi, artefatti diversi — su un flusso che scrive file nel
progetto dell'utente.

- `init.md` scende a ~40 righe: invoca la skill e basta.
- `skill-bootstrap` assorbe Fase 0 (detect), l'anti-overfit in D3, D6 (strategia
  di validazione) e D7 (verifica + consegna + `decisions.log` + memory).
- CONTRIBUTING dichiara il vincolo: non reintrodurre il protocollo nel comando.

### Changed — niente ricette POSIX nelle skill

`change-request` Fase 0 prescriveva `ls -la`, `find … | head -30`,
`test -f … && echo`; `init.md` usava `ls … 2>/dev/null` e `mkdir -p`. Su
PowerShell falliscono, e il modello parte con tre o quattro comandi rotti proprio
mentre si costruisce il quadro del progetto. Ora la skill dice **cosa** cercare e
lascia all'agente i suoi strumenti di ricerca.

### Changed — `change-request` non si ferma più sui repo senza mappa docs

Fase 0.3 interrompeva il protocollo se mancava `docs/README.md`. È la maggioranza
dei repo reali: nella pratica o il protocollo non parte mai, o si impara che i
cancelli di questa skill si scavalcano — Fase 5 compresa, che è quella che conta.
Ora l'Impact Analysis procede sui documenti che trova, dichiarando cosa non ha
potuto verificare, e la creazione della mappa entra fra le voci di Fase 5. Resta
un unico stop: CR strategic **e** nessun documento autoritativo.

### Removed — la tabella "Stack default" da `methodology`

Prescriveva FastAPI, React+Tailwind, JWT+bcrypt. Dieci righe sotto, lo stesso
file elenca fra gli anti-pattern «Specificare framework nel prompt → depotenzia
il modello». Il modello leggeva entrambi e ancorava sulla tabella, perché è
concreta: si otteneva la scelta di stack che il principio dichiarava dannosa. Al
suo posto una sezione che spiega perché non c'è un default.

### Changed — description come budget, non come spazio libero

Le description stanno **sempre** in contesto. `deep-research` ne occupava 956
caratteri con trigger larghi ("scouting", "benchmark di soluzioni") davanti a un
motore da 10-40 minuti a pagamento: un falso positivo costa caro. `methodology`
aveva invece un trigger vago e sotto-attivava proprio la regola anti-overfit.

- Tutte riscritte con trigger espliciti; totale da 3.535 a 2.954 caratteri.
- Nuovo check in CI: tetto di 600 caratteri per skill, con report del totale.

### Added — CI che intercetta questi difetti

`compileall` sugli script, path via `${CLAUDE_PLUGIN_ROOT}`, nessun segnaposto in
prosa nei prompt dei ruoli, budget delle description.

### Added — test del guard per i nuovi comportamenti

`test_kill_switch_grace_allows_diagnosis_and_rollback` e
`test_churn_resets_on_verified_progress`; `test_kill_switch` riscritto sulle
scritture (il vecchio caso passava per grazia, come deve).

---

## [4.5.0] - 2026-07-26

### Changed — `deep-research`: il funnel diventa ricorsivo

La 4.4.0 portava avanti i dubbi emersi dal controllo marcandoli "da validare" mentre l'imbuto si stringeva. È il modo tipico di scoprire l'errore **dopo** aver speso il round più profondo: se la premessa era sbagliata, il verticale è da rifare e il funnel intero è denaro buttato. Ora i dubbi si chiudono prima.

**Nuovo invariante (regola non negoziabile n. 8): non si stringe l'imbuto su un dubbio aperto.**

- **Tre stadi tendenziali invece di tre round fissi**: inquadramento del problema → chiusura dei dubbi → focalizzazione verticale. Lo stadio dei dubbi si **ripete per ricorsione** finché i dubbi strutturali sono chiusi, e il funnel può anche accorciarsi (se il controllo sul primo round non trova dubbi strutturali si va diretti al verticale, dichiarandolo).
- **Controllo (Fase 4) e confronto (Fase 5) girano dopo ogni round**, non solo alla fine: sono loro a produrre i dubbi che alimentano lo stadio successivo. Le due fasi prendono il nome che hanno nell'uso reale.
- **Classificazione dei dubbi**, ciò che rende la ricorsione sostenibile invece di infinita: **strutturale** (se si risolve male cambia la selezione o invalida il perimetro → merita un round), **puntuale** (un dato isolato → gamba veloce o `WebFetch`, mai un round da 30 minuti), **irriducibile** (fonte pubblica non conclusiva → si dichiara e si marca). Nel dubbio sulla classe si tratta come strutturale: l'errore è asimmetrico.
- **Il dubbio è una proposizione falsificabile**, non un'impressione: "la fonte non è chiara" non apre un round, "lo strumento X richiede la sede in regione e il soggetto non l'ha" sì.
- **La domanda di premessa è obbligatoria in ogni round di dubbi**: *il perimetro dell'analisi è ancora quello giusto?* L'errore costoso non sta quasi mai in un dato, sta nell'inquadramento.
- **Limite di ricorsione dichiarato in Fase 1**, non deciso strada facendo (default 2, cioè fino a 4 round). A limite esaurito con dubbi ancora aperti il funnel **si ferma e chiede**: concedere un altro round, procedere accettando il rischio (tracciato con `stretto_su_dubbi_aperti: true`), o chiudere con un sinottico parziale.
- **Registro dei dubbi** (`DUBBI.md`) e **traccia della ricorsione** nel sinottico: un dubbio per riga con classe, round che l'ha aperto, esito e fonte. Nuovi campi nel frontmatter (`round_eseguiti`, `n_round_dubbi`, `limite_ricorsione`, `n_dubbi_aperti`, `stretto_su_dubbi_aperti`); se restano dubbi aperti la sintesi esecutiva **si apre da lì**, prima di qualunque raccomandazione.
- **Nuovo template `prompts/round_dubbi.md`** (verdetto CONFERMATO/SMENTITO/NON CONCLUSIVO con prova puntuale, conseguenza sulla selezione, effetti collaterali, domanda di premessa; "NON CONCLUSIVO è preferibile a una risposta plausibile"). `round_shortlist.md` è riformulato come la variante comparativa dello stesso stadio ("quale fra questi", che è anch'esso un dubbio bloccante).
- **Nomi degli artefatti parlanti**: `r1-inquadramento`, `r2-dubbi1`, `r2-dubbi2`, `r3-focus` — la forma del funnel si legge da un `ls`.
- **`references/funnel_tuning.md`**: non si configura più il numero di round ma il limite di ricorsione (tabella 0/1/2/3+ con i casi d'uso), più cosa conta come dubbio strutturale per dominio (normativo, tecnico, due diligence). Il criterio: se l'esito sfavorevole cambia *chi vince* è strutturale, se cambia *di quanto* è puntuale.

### Changed — blueprint full-auto riscritto per la ricorsione

- **Stati generici e stadi dinamici**: `compose → wait → controllo → confronto → cancello`, con `run["stage"]` che porta lo stadio corrente. La catena fissa `round0 → round1 → round2` non poteva esprimere un ciclo.
- **Il modello classifica, il codice decide**: il cancello chiede all'LLM un JSON con i dubbi classificati, ma il *routing* è una politica deterministica in Python. Un giudizio sbagliato costa un round; un controllo di flusso in mano al modello costa il funnel.
- **Nuovo stato `attesa_decisione`**, non terminale e che il runner **non tocca**: ci si finisce a budget esaurito con dubbi aperti, oppure quando il cancello non restituisce un JSON leggibile (il fallback è sempre verso l'umano, mai verso "vai avanti"). Si esce con la nuova `decide(run_id, "altro-round"|"procedi"|"chiudi")`, esposta anche come comando CLI.
- **I dubbi non evaporano**: il registro si fonde per enunciato normalizzato e un dubbio assente da un cancello successivo conserva l'esito precedente.
- `PIPELINE_MAX_DOUBT_ROUNDS` (default 2) fra le env; `WIRING.md` aggiornato con i nuovi stati, il comando `decide` obbligatorio, i test della ricorsione e il divieto di automatizzare la decisione di stringere su dubbi aperti.

### Validazione
State machine ricorsiva provata end-to-end con le giunture finte: percorso senza dubbi (2 round), ricorsione con dubbio aperto e poi chiuso (3 round), limite esaurito → `attesa_decisione` con verifica che il runner non modifichi il run, le tre decisioni umane, cancello con JSON illeggibile → attesa umana, persistenza del registro dubbi con match normalizzato, round `incomplete` → errore, timeout round → errore, estrazione JSON da fence/inline/assente.

---

## [4.4.0] - 2026-07-26

### Added — nuova skill `deep-research`: cicli di ricerca profonda a imbuto

Il motore (Deep Research come task long-running) è la parte facile. Il valore sta nel funnel che restringe e nel doppio controllo che verifica: un report che gira 30 minuti e cita 40 fonti può sbagliare una data, un'aliquota o un riferimento normativo, e va trattato come un'affermazione da verificare, non come una risposta.

- **Funnel a tre round** (esplorazione ampia → cerchia ristretta 3-6 → verticale su un candidato), con **gate umano** dopo ogni round (`AskUserQuestion`: prosegui / ri-mira / round mirato / stop anticipato) e prompt sempre mostrato e approvato **prima** del lancio: un round costa 10-40 minuti, un fraintendimento costa quel tempo due volte. Il round N+1 fa anche da verifica incrociata del round N (istruzione esplicita di confermare o smentire, con tabella di esiti).
- **Verifica a due gambe indipendenti**: validazione degli URL citati con `WebFetch` + download dei documenti ufficiali (Fase 4); fact-check deterministico su fonte primaria con esiti CONFERMATO/SOSPETTO/NON RINTRACCIATO/CONTRADDETTO e ricalcolo di ogni numero derivato (5.1); second-opinion adversarial da un modello diverso (5.2); **matrice di accordo in cui l'arbitro è la fonte primaria, mai la maggioranza fra LLM** (5.3). Nasce da un caso reale: l'auditor ha smentito a torto due dati corretti e nello stesso giro ha trovato due errori concettuali veri.
- **Scoring multi-dimensione** (default 5 dimensioni × 0-10, soglie di priorità configurabili) e **sinottico finale** con frontmatter auditabile: motori usati, round eseguiti, criteri, fonti primarie, conflitti irrisolti.
- **Dominio-agnostica** (regola anti-overfit): numero di round, fonti primarie, dimensioni di score, criterio di restringimento e livello di anonimizzazione sono parametri fissati nell'inquadramento iniziale, non valori nel codice. `references/funnel_tuning.md` spiega come calibrarli, con tre esempi (incentivi d'impresa, scelta tecnologica/fornitore, due diligence documentale).
- **`scripts/deep_research.py`** — Interactions API: `create` con `agent_config` + `tools` + `background=True` (senza i primi due il task viene creato e **non parte mai**, senza il terzo l'API rifiuta con 400), consumo SSE, fallback a polling quando lo stream si chiude prima del termine, GET finale sempre necessaria (`interaction.completed` porta solo uno scheletro senza `steps`), estrazione manuale del testo da **tutti** i `model_output` perché l'helper SDK `output_text` tronca il report in presenza di content non testuali. `--tag` deriva JSON/log/response, `--resume-id` recupera un task già pagato quando muore il client, guard su segnaposto `{{...}}` residui e su output preesistente, exit code parlanti (0/1/2/3/4/5).
- **`scripts/grounded_research.py`** — gamba veloce (reasoning single-shot con `google_search`, 1-3 min) per audit, second-opinion e round mirati su gap; retry solo su errori transitori, mai su 4xx.
- **`scripts/env_loader.py`** — credenziali senza dipendenze: env di processo > `.env.local` > `.env` > `.env.txt`, cercati risalendo dalla CWD e fermandosi alla prima directory utile; mai un valore in chiaro nei log.
- **Template di prompt** per i round (esplorazione, shortlist, verticale, mirato) e per l'audit adversarial, con le regole che fanno la differenza: formato parsabile per il round successivo, fonti ammesse e fonti mai valide come prova, obbligo di dichiarare l'incertezza invece di colmarla.
- **`references/interactions_api.md`** — comportamenti verificati sul campo e tabella di diagnostica dal log (task creato che non parte, stream interrotto, stato `incomplete`/`budget_exceeded`, `citations_count == 0`, cancel via API che risponde 500, floor temporale ~10 min per round).
- **Blueprint full-auto (`templates/fullauto/`)** — per progetti agentificati: state machine persistente `compose_round<N> → wait_round<N> → … → post-step → done` con run su JSON e scrittura atomica, runner daemon che avanza di **un solo step** per giro, retry per stato, resume al riavvio, notifiche proattive a ogni transizione, CLI ops (`new`/`list`/`status`/`advance`/`cancel`/`serve`); tool di chat `launch_research`/`check_research`; `WIRING.md` con le tre giunture da collegare, i test da fare **senza spendere Deep Research** e la lista di cosa non automatizzare. Principio: in full-auto il gate umano non sparisce, si sposta (notifica + conferma prima di ogni azione irreversibile a valle).

### Dipendenze (solo per la nuova skill)
- `google-genai>=2.0.0` — obbligatoria: il breaking change "may-2026" ha rimosso lo schema legacy `outputs[]` in favore di `steps[]`; con SDK 1.x l'API risponde *"legacy Interactions API schema is no longer supported"*.
- `GEMINI_API_KEY` in ambiente o `.env`; opzionali `DEEPRESEARCH_AGENT`, `GROUNDED_MODEL`, `RESEARCH_OUT_DIR` per non hardcodare modelli e path (gli agent Deep Research cambiano nome ogni pochi mesi).

### Changed
- `plugin.json` / `marketplace.json`: 4.3.1 → 4.4.0, descrizioni e keywords aggiornati, `./skills/deep-research/` nell'array `skills`, count skill 6 → 7.
- `README.md`: versione corrente, riga della nuova skill, voce in "Novità recenti", struttura del repo, requisiti.
- CI `validate.yml`: i file della nuova skill tra i required.

---

## [4.3.1] - 2026-07-11

### Fixed
- **Context tools sotto il guard**: `project_context` e `log_decision` (introdotti in 4.3.0) ora passano da `GUARD.gate("context", ...)` come ogni altro tool del layer — audit trail, kill-switch e permessi coerenti con la spec ("enforcement attorno a ogni tool call"). Nuovo permesso `context: allow` nel default (read-only + append-only by-construction).

---

## [4.3.0] - 2026-07-08

### Added — `agentify`: orientamento decisionale del coding-agent (contro la context-blindness)

Nasce da un incidente reale: un coding-agent ha aggiunto una funzione **corretta** (matematica giusta, test verdi, convenzioni rispettate) sopra un pannello con un difetto dati noto e già fixato nei moduli gemelli, documentato nel decision journal del progetto — risultato plausibile ma sbagliato del 60%. Il coder è affidabile sul **locale** e cieco sul **globale**; la contromisura è rendere l'orientamento **meccanico** (un tool call), non affidarlo al prompt.

- **Nuovo tool `project_context(keywords)`** (`tools/context.py.template`, nostro per design come verify/gitops/repo_map): in una chiamata restituisce stato corrente + entry del decision journal pertinenti per keyword + ADR pertinenti. Nei toolset di coding-agent e scout.
- **Nuovo tool `log_decision(summary)`**: chiude il loop appendendo la change al journal (cosa/perché/come verificata, min 60 char). Anche in high-level-ops. Test verdi senza journal entry = lavoro incompleto.
- **Ciclo del coding-agent** aggiornato (*orienta → checkpoint → edita → verifica → chiudi*): `project_context` OBBLIGATORIO al passo 1 con il monito "il codice circostante NON è una specifica affidabile"; al passo 4 **plausibilità del risultato** oltre ai test (ordine di grandezza vs letteratura/funzione analoga/dati reali — un numero assurdo con test verdi è un bug di contesto: indagare i DATI); al passo 5 `log_decision` obbligatoria.
- Nuovo anti-pattern **A13 "Il codice circostante come specifica (context-blindness)"**, col caso reale.

### Fixed
- **AFC di google-genai disabilitato** nel provider Gemini di `_models.py.template` (wrapper `_GeminiNoAFC`, fallback pulito): l'Automatic Function Calling ha un tetto default di **10 remote call** — un limite nascosto che tronca silenziosamente i task multi-tool quando è il framework a guidare il loop.
- **Sicurezza interfaccia chat**: accanto alla whitelist, documentato il livello **RBAC multi-utente** — autorizzazione a livello di TOOL (closure con scope verificato in codice, default-deny, niente shell/editing ai ruoli ristretti), non nel system prompt.

### Changed
- CI `validate.yml`: `context.py.template` tra i required.
- `plugin.json` / `marketplace.json`: 4.2.0 → 4.3.0.

---

## [4.2.0] - 2026-07-06

### Added — `agentify`: gate anti-degrado (contro il "debito tecnico a velocità macchina")

Il rischio principale di un coding-agent autonomo non è il guardrail che cede rumorosamente, ma il mese in cui tutto è verde e la qualità cala in silenzio. Quattro contromisure strutturali:

- **Quality gates in `verify`**: supporto a check **metrici non-decrescenti** (`"metric": "non_decreasing"` — es. coverage): il comando stampa un numero, verify lo confronta con la baseline persistita in `docs/ops/.metrics.json` e fallisce se scende (anche con exit code 0, tolleranza `metric_tolerance`). Default della definition-of-done aggiornato: lint `required` + coverage come metrica.
- **Tetto ai diff proposti** (`max_propose_diff_lines`, default 400): `git_propose_diff` rifiuta diff irrevisionabili e impone batch più piccoli — un diff che non si può leggere verrebbe approvato senza lettura.
- **Churn detector nel guard** (`churn_limit`, default 5): stesso file modificato troppe volte nella stessa run = thrashing → DENY (`rule=churn_detector`) con istruzione di fermarsi/rollback. Nuovo test deterministico in `test_guard`.
- **Revisione OUTBOX anti rubber-stamping** (RUNBOOK): cadenza dichiarata, staleness (`outbox_stale_days`, default 7 → escalation), "leggi il diff, non il titolo", e la regola: se approvi tutto senza leggere, riduci l'autonomia.
- Nuovo anti-pattern **A12 "Verde = buono"**; SKILL.md dichiara il limite onesto: i gate riducono la probabilità del degrado, non la azzerano.

### Changed
- `plugin.json` / `marketplace.json`: 4.1.0 → 4.2.0.

---

## [4.1.0] - 2026-07-06

### Added — `agentify`: harness del coding-agent (potenza = struttura del loop, non solo tool)

- **Loop di verifica strutturale**: nuovo tool `verify` che esegue la **definition-of-done** del progetto (comandi oggettivi con exit code, dichiarati nel manifesto `tools.definition_of_done`). Le instructions del coder impongono il ciclo *orienta → checkpoint → edita → verifica*: `verify()` dopo ogni batch, VERDE per procedere, ROSSO → correggi la causa reale; oltre `max_verify_cycles` → STOP e rollback.
- **Checkpoint git** (`gitops`): `git_checkpoint`/`git_diff`/`git_revert_to_checkpoint`/`git_propose_diff` — il coder lavora solo su branch `agent/*` (mai main, mai push, by-construction), checkpoint prima/dopo ogni batch, rollback pulito quando verify resta rosso, e propose-and-confirm col **diff reale** in OUTBOX (chi approva rivede codice, non descrizioni).
- **Ruolo `scout`**: ricognizione a contesto separato su modello fast/cheap (default `gemini-3.5-flash`), toolset read-only; il contesto del coder resta pulito. Deriva da `tool/task.{ts,txt}` di opencode (harvest esteso, provenance aggiornata): regole di delega — prompt dettagliato, dichiarare esattamente cosa deve tornare, research-only, no duplicazione.
- **`repo_map`**: mappa compatta file → simboli (regex-based multi-linguaggio, zero dipendenze) per orientarsi senza saturare il contesto (pattern alla Aider).
- **Eval a esito oggettivo**: `eval_coder.py` + `golden_tasks.yaml` — fixture riproducibile → il candidato esegue il task → i comandi verify decidono PASS/FAIL; scoreboard per modello. I golden task vanno presi da manutenzioni reali del progetto; incluso il pattern "task impossibile-senza-contesto" (PASS = dichiara il blocco invece di inventare). La scelta del modello del coder si fa coi numeri, non a sensazione.
- **Failure recovery** nelle instructions del coder: retry singolo su edit fallito, stop+rollback dopo N verify rossi, mai "aggiustare" un test per farlo passare.
- **Decision table "routine nativa Claude Code vs agentify"** in testa alla skill: per automazione interna di chi ha Claude Code il nativo vince; agentify dichiara la sua nicchia (utenti terzi, multi-modello, always-on, manutenzione delimitata).
- Manifesto: nuova sezione `tools` (permissions, definition_of_done, max_verify_cycles, kill_switch_limit).

### Changed

- `validation-strategies` **alleggerita** (322 → ~130 righe): rimossi gli script-fotocopia Playwright/httpx e la meccanica duplicata dai tool nativi (`/verify`, `/run`, Claude Preview); resta la checklist di scenari per tipo di app (il valore che si dimentica) + rimando a `eval_coder` per i coding-agent. Nuovo anti-pattern A5 (niente boilerplate mantenuto nelle skill).
- `guard.py`: permessi `repomap`/`verify`/`gitops` (allow, vincolati by-construction).
- CI `validate.yml`: aggiunti i nuovi template required (verify, gitops, role_scout, eval_coder).
- `plugin.json` / `marketplace.json`: 4.0.1 → 4.1.0.

---

## [4.0.1] - 2026-07-06

### Fixed
- **Ripubblicazione completa della 4.0.0.** Il merge della PR #4 aveva incluso solo il primo commit del branch (race sul PR head): il pacchetto 4.0.0 finito in cache poteva mancare di due commit, reintegrati con la PR #5 — fix `_pid_alive` Windows-safe nel tool-guard (era `os.kill(pid,0)`, che su Windows termina il processo; ora `OpenProcess` via ctypes) + path posix in `glob`/`grep`, e i contenuti "startagent/stopagent.bat, baseline modelli, reasoning policy" descritti sotto nella 4.0.0. Il bump a 4.0.1 forza il refresh della cache del plugin.

---

## [4.0.0] - 2026-07-06

### BREAKING — Skill rimosse (consolidate in `agentify`)

- **`agentic-ops-daemon` rimossa.** I suoi pattern vivono in `agentify` come archetipo di ruolo **`high-level-ops`**: livelli di autonomia L0-L5, ops runbook (`RUNBOOK/STATE/TASK_QUEUE/LAST_RUN/OUTBOX/AUDIT`), scheduler wrapper (`ops-run.ps1`/`.sh`), regole per task unattended (idempotenti, loggati, fail-loud).
- **`claude-session-supervisor` rimossa.** I suoi pattern vivono in `agentify` come **tool-guard** dei ruoli tool-empowered: kill-switch, denylist/allowlist statiche, propose-and-confirm via `OUTBOX.md`, audit trail append-only, lock anti-concorrenza. Il meccanismo specifico "hook `PreToolUse` + secondo `claude -p` judge" NON è migrato: era legato a Claude Code come runtime, mentre in `agentify` il giudizio contestuale spetta al modello del ruolo (scelto nell'intervista) col Critic come second opinion, e il guard fa enforcement deterministico dei confini.
- **Migrazione per chi usava le skill rimosse**: invocare `/vibecoding:agentify`; il caso "daemon/scheduler su CLI esistente" è coperto dal ruolo `high-level-ops`, il caso "sessione autonoma con boundaries" dal ruolo `coding-agent`/`high-level-ops` con tool-guard. Il caso residuo "supervisionare letteralmente una sessione `claude -p` con AI judge" non è più coperto dal toolkit (recuperabile dalla storia git, tag 3.3.1).

### Added — `agentify`: ruoli tool-empowered con tool layer derivato da opencode

- **Nuova Fase 3.5 — Tool Layer & Autonomy**: si attiva quando il team include ruoli tool-empowered.
- **Archetipo `coding-agent`**: ruolo del team ReAct con tool reali di coding — `read`, `glob`, `grep`, `edit`, `write`, `apply_patch`, `shell`, `lsp`, `todo`, `webfetch` — con potenza paragonabile a un coding agent dedicato. Tool, prompt di descrizione e system prompt (varianti per famiglia di modello: anthropic/gemini/gpt/default/plan) **derivati da opencode** (https://github.com/anomalyco/opencode, MIT, con attribuzione). opencode è fonte di conoscenza/risorse/tool, NON dipendenza runtime: nulla viene installato o invocato.
- **Archetipo `high-level-ops`**: operatore disciplinato schedulato (check, refresh, report, proposte) con tool layer ridotto.
- **Modello permessi per tool** in stile opencode: `allow`/`propose`/`deny` per tool, pattern glob per `shell` (l'`ask` interattivo di opencode diventa `propose` asincrono via OUTBOX nel contesto unattended).
- **Tool-guard** (`tools/guard.py`): enforcement a 4 livelli in ordine di costo (kill-switch → denylist → allowlist → propose-and-confirm) + audit append-only + lock.
- **Provenance harvest**: `docs/OPENCODE_HARVEST.md` (nella skill e scaffoldato nel progetto target) registra cosa è stato preso da opencode, da quale commit, con quali adattamenti; è la baseline per il ricontrollo periodico dell'upstream.
- **Nuovi template**: `agno/role_coding_agent.py`, `agno/role_high_level_ops.py`, `agno/tools/*` (fs, shell, lsp, tasklist, guard, registry), `agno/test_guard.py`, `ops/*` (RUNBOOK, STATE, TASK_QUEUE, LAST_RUN, OUTBOX, AUDIT, ops-run.ps1/.sh), `OPENCODE_HARVEST.md`.
- **`scripts/discover.py` esteso**: rileva anche OS (per `.ps1` vs `.sh`) e path sensibili (seed della denylist del guard) — funzioni assorbite dal discover dell'ex claude-session-supervisor.
- **Validazione estesa**: `test_guard.py` (deny/allow/propose/kill-switch/lock, deterministico, no API) e task di editing reale nel bench del coding-agent.
- **`startagent.bat` / `stopagent.bat`**: lifecycle dell'agente su Windows — avvio AgentOS in background (PID file, log su `logs/agentos.log`, avvio via PowerShell `Start-Process`, niente `wmic` deprecato) e arresto pulito con `taskkill /T`.
- **Baseline modelli 4.0.x** (default+candidates da validare col bench): Orchestrator/Analyzer `gemini-3.1-pro-preview` (candidate `glm-5.2`), Writer `gemini-3.5-flash`, Critic `deepseek-v4-pro`, coding-agent `glm-5.2`. Nuovo mapping `glm-*` nel model factory (Zhipu/Z.ai via endpoint OpenAI-compatible, `ZHIPU_API_KEY`). Nota: `deepseek-chat`/`deepseek-reasoner` sono deprecati upstream dal 2026-07-24 → si passa a `deepseek-v4-pro`.
- **Reasoning policy `orchestrator`**: il livello di ragionamento (`low`/`medium`/`high`) non è fissato per ruolo — lo decide l'Orchestrator task per task alla delega; `resolve_model(id, reasoning=...)` lo traduce nel parametro del provider (thinking budget Gemini/Claude, `reasoning_effort` GPT, thinking on/off DeepSeek/GLM) con fallback pulito.

### Changed

- `agentify/SKILL.md`: rimossa l'esclusione "l'agente target deve essere un coding tool → meglio OpenCode/Aider/Continue" — il caso è ora coperto dal ruolo `coding-agent`. Rimossi i cross-reference alle skill pensionate.
- `plugin.json` / `marketplace.json`: versione 3.3.1 → 4.0.0; count skill 8 → 6; descrizioni e keyword aggiornate (rimossi `ops-daemon`, `supervisor`, `pre-tool-use-hook`; aggiunti `coding-agent`, `tool-guard`, `opencode-harvest`).
- CI `validate.yml`: rimossi i file required delle skill pensionate; aggiunti i nuovi file required di `agentify`.
- `README.md`: allineato (6 skill, sezione agentify riscritta).

---

## [3.3.1] - 2026-07-06

### Added
- **Skill `claude-session-supervisor`** — pattern worker + supervisor con AI judge purpose-aware via hook `PreToolUse` di Claude Code: una sessione `claude -p` non interattiva (worker) governata da una seconda sessione `claude -p` (judge) che valuta ogni tool call rispetto alla mission. Gating multi-livello (counter kill-switch → denylist baseline + `PROJECT_DENYLIST` → allowlist statica → AI judge LLM), audit trail append-only, lock anti-concorrenza, UTF-8 forzato. Include `scripts/discover.py` (Fase 0) e template portabili (`supervisor.py`, `worker/judge-settings.json`, `wake_worker.ps1`/`.sh`, `test_supervisor.py`, `RUNBOOK/TASK_QUEUE/AUDIT/LAST_RUN/OUTBOX.md`).
- **`OUTBOX.md.template`** nella skill — supporta il pattern propose-and-confirm per le scritture MCP (referenziato da `supervisor.py` ma non presente nella 3.3.0 upstream).
- **Cross-reference reciproco** tra `claude-session-supervisor` e `agentic-ops-daemon` (skill sorelle: la prima supervisiona una sessione Claude Code, la seconda schedula una CLI; vocabolario ops condiviso).

### Changed
- `plugin.json` / `marketplace.json`: versione 3.2.0 → 3.3.1; aggiunta `./skills/claude-session-supervisor/` (count skill 7 → 8); nuovi keyword (`autonomous-agent`, `supervisor`, `ai-judge`, `pre-tool-use-hook`).
- CI `validate.yml`: aggiunti `skills/claude-session-supervisor/SKILL.md` e `scripts/discover.py` alla lista dei file richiesti.

### Note
- **Riconciliazione della 3.3.0**: la skill era stata pubblicata sul branch `feature/claude-session-supervisor` come 3.3.0, ma partendo da una base che precedeva `agentic-ops-daemon` (gap documentato nella 3.3.0 stessa). La 3.3.1 la reintegra sul `main` corrente, così le due skill coesistono affiancate come da design SPEC-010. La 3.3.0 non è mai stata rilasciata su `main`.

---

## [3.2.0] - 2026-05-16

### Added
- **Skill `agentic-ops-daemon`** - protocollo portabile per progettare daemon/scheduler operativi che risvegliano periodicamente una CLI di progetto o un coding agent, eseguono check/refresh/report, scrivono runbook e audit trail, e applicano livelli di autonomia graduati.
- **Ops runbook pattern** - standardizza `docs/ops/RUNBOOK.md`, `STATE.md`, `TASK_QUEUE.md`, `LAST_RUN.md`, `OUTBOX.md`, `AUDIT.md` come interfaccia fra scheduler, CLI e agente.
- **Autonomy gates** - classifica le azioni da L0 read-only a L5 azioni vietate, con regola propose-and-confirm per modifiche a codice, policy, strategie, pesi o sistemi esterni.
- **Provider AI guidance** - include regole per integrare provider come Google Vertex/Gemini senza salvare segreti in repo e distinguendo ricerca/proposta da decisione vincolante.

### Changed
- `plugin.json`: versione 3.1.0 -> 3.2.0, descrizione e keywords aggiornati, aggiunto `./skills/agentic-ops-daemon/` all'array `skills`.
- `marketplace.json`: versione 3.1.0 -> 3.2.0, descrizione e count skill aggiornati (6 -> 7).
- CI workflow: aggiunta la nuova skill alla lista required.

---

## [3.1.0] — 2026-05-02

### Added
- **Skill `md-to-pdf`** — converte file Markdown in PDF formattati (pure-python via `markdown-pdf`, niente runtime nativi). Supporta TOC, CSS personalizzato, batch, paper-size e metadata. Aggiunto `skills/md-to-pdf/SKILL.md`, `scripts/convert.py`, `styles/default.css`.
- **Sintesi AI opzionale** (`--ai-summary`) — accoda al PDF una sezione "Sintesi AI (generata automaticamente)" con TL;DR, punti chiave, "quando consultarlo" e limiti, prodotta da Gemini. **Non modifica il sorgente `.md`**: la sintesi vive solo nel PDF. Pensata per leggere velocemente spec lunghe, SKILL.md di terzi, best-practice. Errori non bloccanti: senza `GEMINI_API_KEY` o con chiamata fallita, il PDF si genera comunque senza sintesi.
- **Strip front-matter YAML automatico** — le SKILL.md e i markdown con metadata Jekyll/Hugo (`---...---`) vengono gestiti correttamente; senza questo, `markdown-pdf` interpretava le fence come thematic break e rompeva il TOC.
- **Fallback TOC** — se il documento ha heading non lineari, lo script ritenta automaticamente la generazione senza TOC con un warning, anziche fallire.

### Dipendenze (per la nuova skill)
- `markdown-pdf` (obbligatoria per la conversione)
- `google-genai` + `python-dotenv` (solo per `--ai-summary`)

### Changed
- `plugin.json`: versione 3.0.1 -> 3.1.0, descrizione e keywords aggiornati, aggiunto `./skills/md-to-pdf/` all'array `skills`.
- `marketplace.json`: versione 3.0.1 -> 3.1.0, descrizione e count skill aggiornati (5 -> 6).
- CI workflow: aggiunti i tre file della nuova skill alla lista required.

---

## [3.0.1] — 2026-05-01

### Fixed
- **Manifest schema**: il campo `skills` in `plugin.json` ora punta a **directory** (`./skills/<nome>/`) invece che a file `SKILL.md`, conformemente allo schema attuale del Claude Code plugin loader. Senza questo fix, il plugin v3.0.0 non caricava le skill dopo l'installazione.
- CI workflow aggiornato per verificare path-a-directory invece di path-a-file per le skill.

### Note di installazione
Chi ha tentato di aggiornare a 3.0.0 e ha visto errori di validazione del manifest deve:
1. (Opzionale ma raccomandato) cancellare la cache locale: `rm -rf ~/.claude/plugins/cache/vibecoding-marketplace/`
2. Lanciare `claude plugin update vibecoding` (o disinstalla + reinstalla via `/plugin`)

L'errore precedente _"userConfig.qualityScoreTarget.title: Invalid input: expected string, received undefined"_ era causato dalla **cache locale 2.1.0** (con `userConfig` non più valido nello schema), non dal codice 3.0.0 stesso. Una volta pulita la cache, il plugin 3.0.1 si carica correttamente.

---

## [3.0.0] — 2026-05-01

### Pivot: from "autonomous multi-agent team" to "SDD toolkit"

Il plugin è stato ripensato come **toolkit di skill** per spec-driven development.
Un audit ha mostrato che ~70% delle feature di v2.1 sono ora coperte nativamente da
Claude Code (hooks, subagents, parallel execution, validation strategies). v3.0 si
concentra sul valore unico: la **metodologia** e il **routing 3-vie** delle desiderata.

### Added
- **Skill `change-request`** — protocollo a 5 fasi per change non banali (Impact Analysis → Spec First → Migration Plan → Implementation → Close the Loop). Anti bias additivo, no parallel flows
- **Skill `agentify`** — protocollo a 5 fasi per trasformare un progetto Claude Code in agente standalone (default: Agno + AgentOS). Include scripts/discover.py e templates Jinja2
- **Skill `skill-bootstrap`** — intervista metodologica di inizio progetto: distingue modulo vs cartella di lavorazione, fa routing delle desiderata in CLAUDE.md / PROJECT_SPEC / SKILL
- **Templates `modulo/`** — scaffold per progetti software (CLAUDE.md, PROJECT_SPEC, PLAN, docs/ARCHITECTURE)
- **Templates `cartella/`** — scaffold per cartelle di lavorazione Claude (analisi, automazione, documentazione)
- **Template `skill-stub/SKILL.md`** — usato da Fase D di skill-bootstrap per scrivere nuove skill
- **`docs/MIGRATION_2.1_to_3.0.md`** — guida per chi aveva v2.1 installato

### Changed
- **`/vibecoding:init`** esteso: aggiunte FASE A (modulo vs cartella), FASE C (routing 3-vie delle desiderata), FASE D (writer di SKILL.md). Delega la logica di routing a `skill-bootstrap`
- **Skill `methodology`** — refactor SDD-focused: tolti i riferimenti agli agenti rimossi, integrate parti utili di `quality-system`, allineata ai subagent nativi e ai comandi `/review` `/security-review`
- **Skill `validation-strategies`** — contenuto invariato (resta unica), spostata in `skills/validation-strategies/SKILL.md`
- **Manifesto `plugin.json`** — versione 3.0.0, descrizione aggiornata, rimosso `userConfig` (non più nello schema plugin), rimossi `agents`, `hooks`, comandi obsoleti
- **README.md** — riscrittura completa: pivot SDD toolkit
- Tutte le skill spostate in cartelle (`skills/<nome>/SKILL.md`) per allinearsi al formato Agent Skills standard

### Removed
- **Tutti gli agenti** (`architect`, `reviewer`, `tester`, `security-auditor`, `validation-agent`) — usa **subagent nativi** di Claude Code e i comandi `/review`, `/security-review`
- **Comandi obsoleti** (`/vibecoding:validate`, `/vibecoding:status`, `/vibecoding:review`, `/vibecoding:plan`) — slash command custom deprecati a favore di skills; le funzionalità sono coperte dai comandi nativi
- **`hooks/hooks.json`** intero — tutti gli hook (SessionStart, Stop type:prompt, PreCompact, PostCompact, PreToolUse Bash, PostToolUse Edit) sono coperti nativamente. I pattern destructive sono coperti dal permission system
- **Skill `parallel-execution`** — sostituita da Agent Teams nativi (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) e da parallel tool calls
- **Skill `quality-system`** — parti utili assorbite in `methodology`, altre rimosse
- **`scripts/quality-gate.sh`** spostato in `templates/scripts/` (opzionale, non plugin-level)
- **`templates/docs/vibecoding/METHODOLOGY.md`** — duplicato della skill methodology, eliminato
- **Campo `userConfig` nel manifest** — non più nello schema plugin attuale

### Migration
Chi aveva v2.1 installato deve aggiornare `~/.claude/settings.json` (path repo invariato:
`halleysud1/vibe`). I progetti generati con v2.1 continuano a funzionare; per migrarli
al routing 3-vie, lancia `skill-bootstrap` su una sessione del progetto. Vedi
`docs/MIGRATION_2.1_to_3.0.md`.

---

## [2.1.0] — 2026-03-29

### Added
- **Comando `/vibecoding:review`** — Invoca reviewer e security-auditor in parallelo con report unificato
- **Comando `/vibecoding:plan`** — Esplorazione codebase e piano approvabile interattivo
- **Hook PreCompact** — Salva automaticamente state snapshot prima della compaction del contesto
- **Hook PostCompact** — Ripristina contesto critico dopo la compaction
- **Skill `parallel-execution`** — Guida all'esecuzione parallela di agenti con merge dei risultati
- **Template `STATE_SNAPSHOT.md`** — Template per snapshot stato tra fasi di sviluppo
- **Claude Preview integration** — Metodo preferito per validazione web app (fallback Playwright)
- **Auto-lint per Go** (gofmt), **Rust** (rustfmt), **TOML** (taplo), **YAML** (yamllint)
- **Quality gate per Go** (golangci-lint, go test, govulncheck) e **Rust** (clippy, cargo test, cargo-audit)
- **Plugin `userConfig`** — Soglie configurabili (quality score, validation pass, lint languages)
- **Plugin `skills` field** — Tutte le 4 skill registrate nel manifest

### Changed
- **Hook Stop** — Da bash grep su emoji a `prompt` type (LLM valuta se OK fermarsi)
- **Hook SessionStart** — Alleggerito: solo conteggio task PLAN + reminder, non dump file interi
- **Hook PreToolUse(Bash)** — Pattern distruttivi ampliati (+`git push --force`, `DROP TABLE`, `dd`, `chmod -R 777`, `DELETE FROM`, `truncate`, `mkfs`)
- **validation-agent** — Aggiunto `effort: high`, `isolation: worktree`, sezione Claude Preview come metodo preferito, rimosso hooks block non funzionante su Windows
- **architect** — Aggiunto `effort: high`
- **reviewer/tester/security-auditor** — Aggiunto `effort: medium`
- **security-auditor** — Aggiunto supporto Go (govulncheck) e Rust (cargo-audit) nella checklist dipendenze
- **commands/validate.md** — Rilevamento Claude Preview, review+security paralleli post-validazione
- **commands/status.md** — Quality score composito, risultato ultima validazione, formato arricchito
- **commands/init.md** — Riferimenti 2.1, STATE_SNAPSHOT.md al posto di CONTEXT_RULES.md, integrazione auto-memory
- **skills/methodology.md** — Sezione "Gestione del Contesto" (merge da context-optimization), auto-memory per decisioni, anti-pattern aggiornati
- **skills/quality-system.md** — Sezione "Quality Gate Paralleli", metriche Go e Rust
- **skills/validation-strategies.md** — Nuova Sezione 0 "Claude Preview (METODO PREFERITO)"
- **scripts/quality-gate.sh** — Supporto Go e Rust per build, lint, test, dipendenze

### Removed
- **`scripts/load-context.sh`** — Dead code, funzionalità duplicata dal SessionStart hook
- **`templates/docs/vibecoding/CONTEXT_RULES.md`** — Contenuto duplicato, regole integrate in methodology skill
- **`skills/context-optimization.md`** — Regole ora default di Claude Code, parti utili migrate in methodology
- **Hook `Notification`** — Non funzionava su Windows, Claude Code ha notifiche native

---

## [2.0.0] — 2025-12-15

### Added
- Sistema multi-agente completo (5 agenti: architect, reviewer, tester, security-auditor, validation-agent)
- Filosofia dei tre livelli (Business / Ecosistema / Tecnico)
- Regola anti-overfit per requisiti configurabili
- Hooks deterministici (SessionStart, Stop, PreToolUse, PostToolUse, Notification)
- Quality gate con scoring composito su 7 dimensioni
- Validation Agent per testing dal punto di vista utente
- 3 comandi: init, validate, status
- 4 skill: methodology, validation-strategies, context-optimization, quality-system

### Removed (from v1.0)
- Approccio monolitico senza agenti specializzati
- Workflow manuale senza hooks
- Testing solo a livello codice (senza product validation)
