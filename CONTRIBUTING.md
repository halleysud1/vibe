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

## Struttura del plugin (v3.0)

```
.claude-plugin/     → Manifest e marketplace config
commands/           → Comandi slash (solo /vibecoding:init in v3.0)
skills/             → Skill in cartelle dedicate (skills/<nome>/SKILL.md)
templates/          → Template copiati nei progetti utente
docs/               → Documentazione del plugin (es. migration guide)
```

> **Nota**: in v3.0 sono stati rimossi `agents/`, `hooks/`, `scripts/` (a livello plugin)
> perché coperti nativamente da Claude Code. Vedi `CHANGELOG.md` 3.0.0 e
> `docs/MIGRATION_2.1_to_3.0.md`.

### Aggiungere una skill

1. Crea cartella `skills/<nome-kebab>/`
2. Crea `skills/<nome-kebab>/SKILL.md` con frontmatter YAML:
   - `name`: kebab-case, uguale al nome cartella
   - `description`: una frase azionabile (verbo + oggetto + trigger)
3. Scrivi il body markdown con le sezioni standard (Quando usare / Regole / Esempi / Anti-pattern / Checklist)
4. Aggiungi `./skills/<nome-kebab>/SKILL.md` a `.claude-plugin/plugin.json` sotto `skills`
5. Verifica che la CI passi

### Aggiungere uno script di supporto a una skill

Se la skill richiede script Python o asset, aggiungili sotto la sua cartella:

```
skills/<nome>/
├── SKILL.md
├── scripts/
│   └── helper.py
└── templates/
    └── output.template
```

Vedi `skills/agentify/` come esempio.

### Modificare `/vibecoding:init`

`commands/init.md` è il punto di ingresso. La logica di routing 3-vie è codificata
nella skill `skill-bootstrap`: se modifichi il flusso, sincronizza entrambi.

## Code of Conduct

Sii rispettoso, costruttivo, e collaborativo.
