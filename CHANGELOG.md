# Changelog

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
