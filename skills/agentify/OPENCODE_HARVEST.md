# OPENCODE_HARVEST — provenance del tool layer di agentify

Il tool layer dei ruoli tool-empowered (Fase 3.5 della skill) deriva da
**opencode** — https://github.com/anomalyco/opencode — rilasciato sotto
**MIT License** (Copyright (c) 2025 opencode/Anomaly; il testo completo della
licenza e' nel repo upstream). opencode e' usato come **repository di
conoscenza, risorse e tool**: nulla di opencode viene installato, invocato o
vendorizzato come dipendenza runtime.

## Baseline harvest

| Campo | Valore |
|---|---|
| Repo upstream | `https://github.com/anomalyco/opencode` |
| Branch | `dev` |
| Commit di riferimento | `eb6ff0c1e049e5dfb6f61eb74f925c0a8007490c` |
| Data harvest | 2026-07-06 |
| Versione vibecoding | 4.0.0 |

## Cosa e' stato preso, da dove, con quali adattamenti

| Sorgente upstream (`packages/opencode/src/`) | Destinazione (template agentify) | Adattamenti |
|---|---|---|
| `tool/read.{ts,txt}` | `agno/tools/fs.py` → `read_file` | Port TS→Python; line-number prefix, offset/limit, truncation |
| `tool/glob.{ts,txt}` | `agno/tools/fs.py` → `glob_files` | Port; pathlib glob, cap 500 risultati |
| `tool/grep.{ts,txt}` | `agno/tools/fs.py` → `grep_search` | Port; ripgrep se presente, fallback Python puro |
| `tool/edit.{ts,txt}` | `agno/tools/fs.py` → `edit_file` | Port; exact-match + replace_all, read-before-edit enforcement |
| `tool/write.ts` | `agno/tools/fs.py` → `write_file` | Port |
| `tool/apply_patch.{ts,txt}` | `agno/tools/fs.py` → `apply_patch` | Port del formato envelope (Add/Delete/Update/Move to) |
| `tool/shell.ts` | `agno/tools/shell.py` → `run_shell` | Port; timeout, output cap, permessi a pattern delegati al guard |
| `tool/lsp.{ts,txt}` | `agno/tools/lsp.py` | Client JSON-RPC minimale (definition/references/documentSymbol); graceful degradation |
| `tool/todo.ts` + `todowrite.txt` | `agno/tools/tasklist.py` | Port semplificato (stati, one-in-progress) |
| `tool/webfetch.{ts,txt}` | `agno/tools/web.py` → `web_fetch` | Port ridotto (https-only, strip tag); default `deny` nel guard |
| `session/prompt/anthropic.txt` | `prompts/coding_agent/anthropic.md` | Branding/CLI rimossi, tool rimappati, aggiunto tool-guard awareness |
| `session/prompt/gemini.txt` | `prompts/coding_agent/gemini.md` | Idem; esempi CLI omessi |
| `session/prompt/gpt.txt` | `prompts/coding_agent/gpt.md` | Idem; response channels omessi |
| `session/prompt/default.txt` | `prompts/coding_agent/default.md` | Idem; fallback per famiglie senza variante |
| `session/prompt/plan.txt` | `prompts/coding_agent/plan.md` | Reminder read-only per modalita' plan |
| Modello permessi (`opencode.json`: allow/ask/deny + pattern bash) | `agno/tools/guard.py` (`PERMISSIONS`) | `ask` interattivo → `propose` asincrono via OUTBOX (contesto unattended) |
| Agent modes Build/Plan | Fase 3.5 SKILL.md (mapping autonomia) | Build ≈ L4 con guard; Plan ≈ L0-L2 + `plan.md` reminder |

## Cosa NON e' stato preso (deliberatamente)

- Il runtime (client/server, TUI, desktop app, `opencode serve`, SDK): il
  ciclo ReAct resta quello dell'engine scelto in Fase 2 (Agno di default)
- `tool/task.ts` (subagent spawning): in agentify la delega e' del Team Agno
- `tool/question.ts`, `tool/skill.ts`: coperti da AgentOS / skill_loader
- Prompt model-specific minori (`codex.txt`, `kimi.txt`, `beast.txt`,
  `trinity.txt`): la variante `default.md` fa da fallback

## Procedura di ricontrollo periodico

1. Confronta `packages/opencode/src/tool/` e `src/session/prompt/` upstream
   con il commit di riferimento qui sopra (`git log eb6ff0c1..dev -- <path>`
   sul clone upstream, o via GitHub compare).
2. Se emergono tool/prompt nuovi o migliorati utili ai nostri scopi, apri una
   `/change-request` per aggiornare i template del tool layer.
3. Ad aggiornamento fatto, aggiorna questa tabella e il commit di riferimento.

Prendiamo solo cio' che serve: non e' un fork e non insegue la parita' di
feature con upstream.
