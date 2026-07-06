---
name: claude-session-supervisor
description: "Trasforma una sessione `claude -p` non-interattiva in un agente disciplinato, supervisionato da una seconda sessione `claude -p` (judge) via hook `PreToolUse` che valuta ogni tool call rispetto alla mission. Multi-layer gating (counter -> denylist -> allowlist -> AI judge purpose-aware), audit trail, kill-switch. Use when the user wants automated/unattended Claude Code sessions, scheduled CLI agents, AI-judged tool permissions, or supervised autonomy patterns."
---

# /claude-session-supervisor — Sessione Claude autonoma con AI judge

Quando l'utente vuole **far girare Claude Code senza umano davanti** (`claude -p` schedulato, agent autonomo, run notturna) ma teme che il modello incontri un permission prompt e si blocchi — questa skill scaffolda il pattern **worker + supervisor**:

- Un primo `claude -p` (**worker**) esegue la mission
- Un secondo `claude -p` (**judge**) valuta *ogni tool call* del worker rispetto alla mission, via hook `PreToolUse`
- Multi-layer gating: counter -> denylist statica -> allowlist statica -> AI judge LLM (solo per i casi ambigui)
- Audit trail append-only, kill-switch a N tool call, lock anti-concorrenza
- Funziona su Windows (PowerShell), Linux, macOS

L'output e' un set di file che il progetto adotta tale-quale (con minimi adattamenti di dominio).

---

## Quando usare questo protocollo

**Usalo quando** l'utente:
- Ha un progetto Claude Code maturo (CLAUDE.md, eventuali skill, scripts) e vuole una run autonoma di Claude su una task ben definita
- Vuole evitare `--dangerously-skip-permissions` ma anche evitare un `--allowedTools` rigido che non gestisce il contesto
- Accetta il trade-off "AI giudica AI" (un secondo LLM costa token e aggiunge latenza, ma da' giudizio contestuale)
- Lavora su Windows/Linux/macOS con shell PowerShell o bash

**Non usarlo** quando:
- Basta `--allowedTools` statico (caso semplice, deterministico) -> sufficiente
- Il task e' totalmente read-only e non c'e' rischio di azioni dannose -> `--dangerously-skip-permissions` in sandbox e' sufficiente
- Serve un agente standalone con UI chat / multi-modello / memoria longitudinale -> usa `/agentify` (Agno+AgentOS)
- Serve solo schedulare una CLI gia' esistente (no coding agent) -> usa `/agentic-ops-daemon`

**Skill complementari** (componibili):
- `/agentic-ops-daemon` — se vuoi *anche* schedulare il worker (cron / Task Scheduler / systemd). Stesso vocabolario ops (`RUNBOOK.md`, `AUDIT.md`)
- `/change-request` — per gestire questa adozione in modo disciplinato sul progetto target

---

## Architettura del pattern

```
┌────────────────────┐
│ wake_worker.ps1/sh │ entrypoint (manuale o schedulato)
└─────────┬──────────┘
          │
          │ stdin: TASK_QUEUE.md (mission)
          ▼
┌────────────────────────────┐       ┌──────────────────────────────┐
│ claude -p (WORKER)         │       │ supervisor.py                │
│ --settings worker-          │ ─────►│ (hook PreToolUse)            │
│   settings.json             │ ogni  │                              │
│                             │ tool  │  1. counter > N? -> DENY     │
│                             │ call  │  2. denylist statica? -> DENY│
│                             │       │  3. allowlist statica? -> APP│
│                             │       │  4. claude -p JUDGE          │
│                             │       │     (judge-settings.json,    │
│                             │       │      NO hook, NO ricorsione) │
│                             │       │     -> APPROVE/DENY+motivo   │
└─────────────────────────────┘       └──────────┬───────────────────┘
                                                  │
                            APPROVE -> exit 0     │     DENY -> exit 2
                            tool procede          │     motivo iniettato come messaggio
                                                  ▼
                                      AUDIT.md (append-only)
```

I 4 livelli sono **in ordine di costo crescente**: il 90%+ dei tool call deve essere risolto da allowlist/denylist statiche, l'AI judge serve solo per i casi che le regole non sanno valutare.

---

## Fase 0 — Discovery

Capisci se il progetto target e' candidato e identifica i punti di ancoraggio.

```bash
python skills/claude-session-supervisor/scripts/discover.py --save
```

Output: `.claude-session-supervisor-discovery.json` nella root. Contiene:
- OS rilevato (decide se scaffoldare `.ps1`, `.sh`, o entrambi)
- Posizione di `CLAUDE.md` (per ereditarlo nella sessione worker)
- Skill / MCP server presenti (informativo)
- Scripts esistenti (utili come tool che il worker potrebbe richiamare)
- Path "sensibili" del progetto (`.env*`, segreti, file di config) per la denylist baseline
- Suggerimenti automatici di mission tipiche (analisi notturna, refresh dati, report)

Mostra il report. Se l'inventario e' povero (nessun script, nessuna skill, nessun CLAUDE.md), suggerisci di costruire prima questi pezzi: una sessione autonoma senza scaffolding fallisce molto.

---

## Fase 1 — Mission Interview

Max 6 domande mirate (puoi usare `AskUserQuestion`). L'identita' della mission e' il pezzo piu' importante: senza, il judge non puo' essere purpose-aware.

1. **Mission**: cosa deve fare il worker, in 1-3 frasi? (es. "estrai gli ordini di ieri e produci un report markdown")
2. **Trigger primario**: lancio manuale / Task Scheduler / cron / event-driven? (Influenza solo il wrapper; il pattern non cambia.)
3. **Tool ammessi nominalmente**: Read/Grep/Glob/Write/Bash/Edit/MCP — quali servono? Quali no?
4. **Path di output**: dove scrive il worker? (sola scrittura permessa nell'allowlist)
5. **Cadenza** (se schedulato): giornaliera / settimanale / ad-hoc?
6. **Boundary hard del progetto**: cosa il worker NON deve MAI fare? (es. "non scrivere su Odoo prod", "non toccare branch git", "non mandare email")

Output: bozza testuale di **mission file** (`TASK_QUEUE.md`) e di **boundaries di dominio**. Mostra all'utente, itera.

### Red flag — bias additivo

Se la mission e' "fai un po' di tutto" non e' un buon candidato per autonomia. Restringi a una mission misurabile, con criterio di terminazione esplicito.

---

## Fase 2 — Boundaries

Decidi tre layer:

### 2.1 Denylist baseline (mai negoziabile)

Sempre presente nel `supervisor.py`:
- Tool `mcp__*` se l'utente NON ha confermato esplicitamente di volerlo abilitare (default: nego)
- Bash con regex `(rm |Remove-Item|del |curl|wget|Invoke-WebRequest|scp|mv|Move-Item)|git\s+push|python.*(<script-sensibile>)` (passare lista da Fase 1)
- Read/Edit/Write su `.env*`
- Edit/Write su path fuori dalla cartella di output dichiarata

### 2.2 Denylist domain-specific (extension point `PROJECT_DENYLIST`)

L'utente puo' aggiungere proibizioni specifiche. Esempi tipici:
- "Bash che invoca `python.*estrai_*\.py`" (se quel comando tocca un sistema esterno critico)
- "Edit su `src/<modulo>/policy.py`" (file con regole di business)

### 2.3 Allowlist statica (le strade autorizzate)

Path/pattern noti che il worker usa nella sua mission. Esempi:
- `Read` su `data/input/*.json`
- `Write` su `reports/output/<date>.md`
- `Bash` con regex `^(ls|pwd|cd|cat\s)` (solo se confermato)
- `Glob` su path dichiarati

**Principio**: allowlist deve coprire l'80-90% dei tool call attesi. Il resto va al judge. Se gia' in Fase 2 ti accorgi che meta' dei tool call andranno al judge, raffina l'allowlist.

---

## Fase 3 — Scaffolding

Genera i file dal template. Layout target:

```
<project-root>/
├── scripts/ops/
│   ├── wake_worker.ps1            # Windows (sempre scaffoldato se OS=Windows o portabile)
│   ├── wake_worker.sh             # Unix/macOS (sempre scaffoldato se OS != Windows o portabile)
│   ├── supervisor.py              # multi-layer gating, audit, kill-switch
│   ├── worker-settings.json       # allow/deny + hook PreToolUse
│   └── judge-settings.json        # solo Read/Grep, NO hook (evita ricorsione)
├── docs/ops/
│   ├── RUNBOOK.md                 # protocollo operativo human-readable
│   ├── TASK_QUEUE.md              # mission (dall'output Fase 1)
│   ├── LAST_RUN.md                # output ultima run (placeholder)
│   └── AUDIT.md                   # append-only decisioni del judge (placeholder)
└── (tests/ops/test_supervisor.py opzionale — pytest base)
```

### Rendering manuale dei template (stile `/agentify`)

Per ogni template in `skills/claude-session-supervisor/templates/`, leggi -> sostituisci i placeholder con i valori della Fase 1/2 -> scrivi il file risultante nel progetto target. Placeholder convenzionali:

- `{{ mission_title }}` — short title della mission
- `{{ mission_body }}` — corpo della mission
- `{{ output_dir }}` — cartella di output (`docs/ops/` di default)
- `{{ allowlist_rules }}` — array di regole allowlist
- `{{ denylist_rules }}` — array di regole denylist (baseline + domain)
- `{{ kill_switch_limit }}` — N tool call max (default 200)
- `{{ judge_timeout_sec }}` — secondi (default 90)
- `{{ os }}` — `windows` / `unix` (scaffolda lo script wrapper giusto)

### File da NON dimenticare

- `worker-settings.json`: il valore di `hooks.PreToolUse[*].command` deve **quotare** il path assoluto (`python "$CLAUDE_PROJECT_DIR/scripts/ops/supervisor.py"`) per gestire spazi nel project path su Windows
- `judge-settings.json`: NESSUN hook (la sua mancanza e' la garanzia anti-ricorsione)
- `wake_worker.ps1` su Windows: non usare `Start-Process -ArgumentList` (bug noto col quoting di argomenti contenenti spazi). Usare `System.Diagnostics.Process` raw + mission via stdin + UTF-8 forzato

---

## Fase 4 — Validation

### 4.1 Smoke test del supervisor (no LLM)

```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"<path-allowlisted>"}}' | python scripts/ops/supervisor.py
# atteso exit=0

echo '{"tool_name":"mcp__odoo_search","tool_input":{}}' | python scripts/ops/supervisor.py
# atteso exit=2 con motivo "denylist"
```

### 4.2 Hello world safe (prima run reale)

Mission template "hello world safe" (es. "conta file in una cartella di sola lettura e scrivi sintesi"). Esegui il wake_worker manualmente. Verifica:

- Esito OK, tool call > 0 e < kill_switch_limit
- `LAST_RUN.md` con output coerente
- `AUDIT.md` con mix di `rule=allowlist_static` e `rule=judge_llm` (almeno una di entrambe)
- Nessuna decisione `rule=denylist_static` (in run normale non dovrebbero esserci)

### 4.3 Test negativi (opzionali ma raccomandati)

- Mission con istruzione contraddittoria -> verifica DENY (allowlist o judge)
- Mission che chiede tool MCP (se denylisted) -> verifica DENY hard immediato

### 4.4 Mission reale

Solo dopo 4.1-4.3 PASS. Run controllata (orario non critico, persona reperibile).

---

## Pattern centrale: purpose-aware judge

Il judge non valuta in astratto, ma rispetto alla **mission**. Riceve via prompt:
- `mission` (estratto da `TASK_QUEUE.md`)
- `tool_name` e `tool_input` del tool call proposto
- (opzionale) `audit_tail` delle ultime N decisioni

Output: una sola riga `APPROVE: <motivo>` oppure `DENY: <motivo>`.

Esempio con mission = "conta file in `data/estrazioni` e scrivi sintesi":

| Tool call proposto | Decisione attesa | Layer |
|---|---|---|
| `Read data/estrazioni/x.json` | APPROVE | allowlist_static |
| `mcp__odoo_search` | DENY | denylist_static |
| `Read CLAUDE.md` | DENY | judge_llm (non coerente con la mission) |
| `Bash: ls data/estrazioni` | APPROVE | judge_llm ("read-only coerente") |
| `Bash: rm temp.txt` | DENY | denylist_static |

Il valore del judge LLM e' la riga 3: nessuna regola statica la bloccherebbe, ma e' fuori scope. Per i casi 1, 2, 5 le regole statiche sono piu' veloci ed economiche.

### Anti-sycophancy del judge

Da' al judge **solo** il contesto necessario (mission + tool call + audit tail). MAI passargli l'intera transcript del worker — il judge tende ad approvare per "non far perdere lavoro" se vede tutto il flusso.

---

## Considerazioni operative

### Costo

Ogni invocazione del judge LLM costa token. Una run con 100 tool call di cui 20% va al judge = 20 invocazioni piccole (~500 token input + 50 output ciascuna). Tieni l'allowlist ben tarata per ridurre il rapporto.

### Latenza

Ogni tool call ha overhead +5-30s se passa per il judge. Per task con molti tool call, considera di:
- Ampliare l'allowlist
- Usare un modello fast/cheap per il judge (`--model haiku` se confermato dall'utente del judge-settings)
- Accettare la latenza se il valore di sicurezza giustifica

### Ricorsione (anti-loop hard)

Il judge **non** deve a sua volta avere hook PreToolUse, altrimenti loop infinito. Verifica:
- `judge-settings.json` non ha sezione `hooks`
- Il prompt al judge dice esplicitamente "NON eseguire alcun tool"
- Allowlist del judge limitata a `Read,Grep` (read-only, basta a leggere `TASK_QUEUE.md` se serve)

### Kill-switch

Counter di tool call della run corrente. Se supera `kill_switch_limit` (default 200), DENY hard di tutti i tool call successivi + emergency log. Non e' parte della logica di business: e' una rete di sicurezza contro bug runaway.

### MCP nella skill matura

A differenza dei PoC iniziali (dove MCP era off-limits hard), la skill abilita MCP con extension point:
- L'utente dichiara in Fase 1 quali MCP server / quali tool MCP sono ammessi
- Il template `supervisor.py` ha denylist baseline `mcp__*` ma con override `PROJECT_MCP_ALLOWLIST = ["mcp__myserver_safe_action"]`
- Le **scritture** verso MCP esterni (es. `create`, `write`) devono passare per propose-and-confirm: il judge approva la PROPOSTA, l'azione viene scritta in `OUTBOX.md` invece che eseguita, un umano (o un secondo wake) la confermera'

---

## Anti-pattern

### A1. Worker con `--dangerously-skip-permissions`
Annulla lo scopo. Se l'utente lo chiede "per comodita'", la skill non e' adatta — usa direttamente `claude -p --dangerously-skip-permissions`.

### A2. Allowlist statica troppo larga
`"Bash"` senza qualificatore = il worker puo' fare qualunque cosa. Sempre con regex/path concreto.

### A3. Judge con accesso al transcript completo
Favorisce sycophancy. Da' solo mission + tool call + audit tail.

### A4. File `LAST_RUN.md` / `AUDIT.md` con segreti
Il supervisor non deve loggare contenuto dei file letti, valori di `.env`, prompt completi del judge se contengono dati di dominio.

### A5. Saltare il rendering dei template
File con `{{ placeholder }}` rimasti non resi = bug latente. Verifica con grep dopo lo scaffolding.

### A6. Trigger schedulato senza lock
Due wake concorrenti possono corrompere AUDIT/LAST_RUN. Lock file con PID + cleanup robusto.

### A7. Niente kill-switch
Senza, un worker buggato puo' macinare migliaia di tool call (e token) prima di esaurire.

### A8. Path con spazi non quotati negli hook
Su Windows, il path del progetto puo' contenere spazi. Il `command` dell'hook PreToolUse deve quotare il path al supervisor: `python "$CLAUDE_PROJECT_DIR/scripts/ops/supervisor.py"`.

---

## Checklist di auto-verifica

Prima di dichiarare la skill applicata correttamente:

1. Mission e' specifica (verbo + oggetto + criterio di terminazione)?
2. Boundaries hard sono nel `supervisor.py` (denylist baseline + domain)?
3. Allowlist copre l'80-90% dei tool call attesi della mission?
4. `judge-settings.json` NON ha hook PreToolUse?
5. Su Windows, path con spazi sono quotati nel command dell'hook?
6. Kill-switch e' presente e con soglia ragionevole (50-500 a seconda del task)?
7. AUDIT.md e' append-only e non logga segreti?
8. Lock file impedisce wake concorrenti?
9. Hello world safe (4.2) PASS prima di mission reale?
10. RUNBOOK.md spiega a un umano come leggere LAST_RUN.md e AUDIT.md?

Se anche una sola risposta e' "no" o "forse", torna indietro.

---

## Compatibilita' OS

| OS | Wrapper | Note |
|---|---|---|
| Windows (PowerShell 5.1+) | `wake_worker.ps1` | NON usare `Start-Process -ArgumentList` (bug quoting); usare `System.Diagnostics.Process`. UTF-8 forzato per accenti. |
| Linux | `wake_worker.sh` | bash 4+. `timeout`, `flock` per lock. |
| macOS | `wake_worker.sh` | come Linux ma `timeout` da brew (`gtimeout`) se non disponibile di default. |

Il `supervisor.py` e' Python puro (3.8+), portabile out-of-the-box.

---

## Output finale atteso

Quando chiudi il lavoro, riporta:

- file scaffoldati (lista esplicita)
- mission registrata
- allowlist/denylist applicate
- kill_switch_limit configurato
- esito hello world safe (4.2)
- eventuali test negativi eseguiti (4.3)
- comandi `wake_worker.{ps1,sh}` documentati nel RUNBOOK
- punti di attenzione (es. MCP abilitato? propose-and-confirm in vigore?)

Quando suggerire `/agentic-ops-daemon` come step successivo: se l'utente vuole **schedulare** il wake_worker. Le due skill condividono il vocabolario ops (RUNBOOK, AUDIT, LAST_RUN) e si compongono naturalmente.
