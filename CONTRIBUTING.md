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
4. Verifica che la CI passi: JSON validi, frontmatter corretti, file presenti,
   script che compilano, invocazioni via `${CLAUDE_PLUGIN_ROOT}`, nessun
   segnaposto in prosa nei prompt dei ruoli, description entro 600 caratteri
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
commands/           → Comandi slash (solo /vibecoding:init)
skills/             → Skill in cartelle dedicate (skills/<nome>/SKILL.md)
templates/          → Template copiati nei progetti utente
docs/               → Documentazione del plugin
```

> Il plugin non spedisce `agents/` né `hooks/`: sono coperti nativamente da
> Claude Code. Quello che spedisce è il metodo.

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

`commands/init.md` è un **entry point sottile**: invoca `skill-bootstrap` e non
altro. Tutto il protocollo (detect, intervista, routing 3-vie, scrittura,
chiusura) vive nella skill, che è la fonte autoritativa.

Non reintrodurre il protocollo nel comando "per comodità": due copie che
divergono producono bootstrap diversi per lo stesso progetto, ed è esattamente
il parallel flow che questo toolkit insegna a non fare.

### Invocare script dalle skill

Sempre via `${CLAUDE_PLUGIN_ROOT}`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/<nome>/scripts/helper.py"
```

Un path relativo tipo `skills/<nome>/scripts/helper.py` funziona solo se la
skill è copiata dentro il progetto: installata da marketplace la skill vive
nella directory del plugin, il comando fallisce al primo uso e il modello
finisce a improvvisare. La CI lo verifica.

## Code of Conduct

Sii rispettoso, costruttivo, e collaborativo.
