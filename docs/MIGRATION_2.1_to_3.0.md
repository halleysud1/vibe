# Migrazione vibecoding 2.1 → 3.0

Questa guida è per chi ha v2.1 installato e vuole passare a v3.0.

## TL;DR

- **Path del repo invariato**: `halleysud1/vibe` — non serve cambiare il marketplace
- **Plugin più piccolo**: meno agenti, meno hook, ma più skill metodologiche
- **Breaking**: agenti, comandi `/vibecoding:validate|status|review|plan`, hooks rimossi
- **Compatibile**: i progetti generati con v2.1 continuano a girare; migrali quando vuoi

---

## Cosa è ancora compatibile

| v2.1 | v3.0 | Note |
|---|---|---|
| `/vibecoding:init` | `/vibecoding:init` | Stesso comando, esteso con FASE A/C/D |
| Skill `methodology` | Skill `methodology` (in cartella) | Refactor SDD, principi invariati |
| Skill `validation-strategies` | Skill `validation-strategies` (in cartella) | Contenuto invariato |
| Marker `.vibecoding` | Non più richiesto | Era un trigger per gli hook v2.1, ora obsoleto |
| `PROJECT_SPEC.md`, `PLAN.md`, `decisions.log` | Stessi formati | Niente da cambiare |

---

## Cosa è stato rimosso

### Agenti (architect, reviewer, tester, security-auditor, validation-agent)

**Sostituzione**: subagent nativi di Claude Code + comandi nativi.

| v2.1 | v3.0 nativo |
|---|---|
| Invocavi `architect` | Usa il subagent `Plan` (nativo) |
| Invocavi `reviewer` | `/review` (nativo) |
| Invocavi `security-auditor` | `/security-review` (nativo) |
| Invocavi `tester` | Subagent generale o scrivi tu i test |
| Invocavi `validation-agent` | Combini subagent + skill `validation-strategies` |

### Comandi `/vibecoding:validate|status|review|plan`

- `/vibecoding:review` → usa **`/review`** nativo
- `/vibecoding:plan` → usa il subagent **`Plan`** nativo
- `/vibecoding:validate` → consulta la skill `validation-strategies` e segui la sezione del tipo di app
- `/vibecoding:status` → leggi `PLAN.md` direttamente, non serve un comando dedicato

### Hooks (`hooks/hooks.json` intero)

Tutti coperti nativamente:
- `SessionStart` → nativo, anche con type `prompt`
- `Stop` (type:prompt) → nativo
- `PreCompact` / `PostCompact` → nativi
- `PreToolUse Bash` con regex destructive → coperto dal **permission system** built-in
- `PostToolUse Write|Edit` con auto-lint → ancora supportato come hook custom, ma è
  responsabilità del progetto specifico, non più del plugin

Se vuoi continuare ad avere auto-lint, copia il blocco bash dal v2.1 nel tuo
`.claude/settings.json` locale.

### Skill `parallel-execution`

Sostituita da feature native:
- **Agent Teams** sperimentali: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **Parallel tool calls**: invoca più Agent in un singolo messaggio assistant

### Skill `quality-system`

Le parti operative sono state assorbite in `methodology`. Lo script
`scripts/quality-gate.sh` è in `templates/scripts/` come template **opzionale**:
copialo nel tuo progetto se ti serve, non è plugin-level.

### `userConfig` nel manifest

Non più supportato dallo schema plugin attuale. Se avevi configurato
`qualityScoreTarget`, `validationPassThreshold`, `autoLintLanguages`, perdi
la UI di config: questi valori sono ora hardcoded nel template del progetto
(che puoi editare liberamente).

---

## Come migrare un progetto v2.1 esistente

### Opzione A — Lasciare il progetto com'è

I progetti v2.1 continuano a funzionare con Claude Code attuale. Il plugin v3.0
è retrocompatibile per quanto riguarda i path (CLAUDE.md, PROJECT_SPEC.md, ecc).

L'unica differenza: i tuoi `.vibecoding` marker, gli hook `/vibecoding:validate`
e simili semplicemente non fanno più nulla. Puoi tenerli o rimuoverli.

### Opzione B — Adottare il routing 3-vie

Se vuoi sfruttare la nuova filosofia (regole operative ricorrenti → SKILL invece
di prompt sparsi):

1. Apri Claude Code nel progetto v2.1 esistente
2. Lancia `skill-bootstrap` (o lascia che `init` la chiami)
3. La skill rileva `CLAUDE.md` e `PROJECT_SPEC.md` esistenti, **non li sovrascrive**
4. Ti chiede quali regole/desiderata ricorrenti vuoi promuovere a skill
5. Scrive le nuove SKILL in `.claude/skills/`

Risultato: progetto v2.1 + skill operative dedicate.

---

## Aggiornare `~/.claude/settings.json`

Il path del marketplace è invariato. Probabilmente hai già:

```json
{
  "extraKnownMarketplaces": {
    "vibecoding-marketplace": {
      "source": { "source": "github", "repo": "halleysud1/vibe" }
    }
  },
  "enabledPlugins": {
    "vibecoding@vibecoding-marketplace": true
  }
}
```

Quando v3.0 viene merciata in `main`, basta un `claude plugin update vibecoding`
(o reinstallare). Se hai pinato una versione, sblocca il pin.

---

## FAQ

**Q: I miei progetti che usano `/vibecoding:review` smetteranno di funzionare?**
Sì. Il comando è stato rimosso. Sostituiscilo con `/review` nativo (alias che
ricordare: stessi compiti, ma è un comando di Claude Code, non del plugin).

**Q: Perdo il quality-gate composito di v2.1?**
Lo script `quality-gate.sh` è in `templates/scripts/`. Copialo nel tuo progetto
e adattalo. Non è più auto-eseguito dal plugin.

**Q: Posso tenere v2.1 in parallelo a v3.0?**
Tecnicamente sì, configurando due plugin diversi (es. fork del repo a un commit
v2.1). Sconsigliato — meglio fare il salto.

**Q: Le skill `change-request` e `agentify` funzionano in qualsiasi progetto?**
Sì. Sono progettate per essere portabili. `agentify` richiede skill esistenti
nel progetto target per produrre output utile.
