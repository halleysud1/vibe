# Contributing a Vibecoding

Grazie per il tuo interesse nel contribuire al progetto!

## Come contribuire

### Segnalare bug
Apri una issue su GitHub descrivendo:
- Cosa hai fatto
- Cosa ti aspettavi
- Cosa è successo invece
- Versione di Claude Code e sistema operativo

### Proporre miglioramenti
Apri una issue con tag `enhancement` descrivendo:
- Il problema che vuoi risolvere
- La soluzione proposta
- Alternative considerate

### Pull Request

1. Forka il repository
2. Crea un branch: `git checkout -b feature/nome-feature`
3. Fai le modifiche
4. Verifica che la CI passi (JSON validi, frontmatter corretti, file presenti)
5. Committa: `git commit -m "feat: descrizione"`
6. Pusha: `git push origin feature/nome-feature`
7. Apri una Pull Request

### Convenzioni commit

Formato: `tipo: descrizione`

| Tipo | Quando |
|------|--------|
| `feat` | Nuova feature |
| `fix` | Bug fix |
| `docs` | Documentazione |
| `refactor` | Refactoring senza cambio di comportamento |
| `test` | Aggiunta o modifica test |

## Struttura del plugin

```
.claude-plugin/     → Manifest e marketplace config
commands/           → Comandi slash (/vibecoding:*)
agents/             → Subagenti specializzati (file .md con frontmatter YAML)
skills/             → Knowledge base (file .md con frontmatter YAML)
hooks/              → Hook configuration (JSON)
scripts/            → Script bash di supporto
templates/          → Template copiati nei progetti utente
```

### Aggiungere un agente

1. Crea `agents/nome-agente.md`
2. Aggiungi frontmatter YAML con `name`, `description`, `tools`, `model`
3. Scrivi il system prompt nel body markdown
4. Verifica che la CI passi

### Aggiungere una skill

1. Crea `skills/nome-skill.md`
2. Aggiungi frontmatter YAML con `name`, `description`
3. Scrivi il contenuto della skill
4. Verifica che la CI passi

### Aggiungere un comando

1. Crea `commands/nome-comando.md`
2. Aggiungi frontmatter YAML con `name`, `description`
3. Scrivi le istruzioni per Claude
4. Registra il file in `.claude-plugin/plugin.json` sotto `commands`

## Code of Conduct

Sii rispettoso, costruttivo, e collaborativo.
