---
name: md-to-pdf
description: "Converte Markdown in PDF con una veste grafica curata: motore Chromium ad alta fedelta' (tabelle, callout, syntax highlighting, diagrammi mermaid renderizzati, numeri di pagina) con fallback pure-python offline. Supporta CSS personalizzato, conversione batch e una sintesi AI opzionale in coda al PDF senza alterare il sorgente .md. Usala quando l'utente vuole esportare in PDF una spec, un report, una skill, una brochure o un documento markdown."
---

# /md-to-pdf — Markdown -> PDF (alta fedelta' + sintesi AI opzionale)

Skill per trasformare un file Markdown in PDF formattato con una **veste grafica professionale**.

Due backend, selezionati in automatico:

- **`chromium`** (default quando disponibile) — alta fedelta'. Converte il Markdown in HTML (markdown-it-py), lo impagina con un tema CSS curato e lo stampa via **headless Chromium** (Playwright). Rende: gerarchia tipografica, **tabelle eleganti**, **callout**, **syntax highlighting** dei code block (pygments), **diagrammi `mermaid` renderizzati**, **footer ricorrente con numeri di pagina**, page-break. Il tema puo' essere **generato da Gemini** su misura del documento (`--gemini-theme`).
- **`markdown-pdf`** (fallback pure-python) — nessun runtime nativo. CSS limitato, niente diagrammi/highlighting. Usato quando Playwright/Chromium non sono disponibili (es. offline, ambienti minimal).

La sintesi AI e' opzionale, dietro flag esplicito, e **non modifica mai il sorgente `.md`**.

## Quando usare

- L'utente ha un `.md` (spec, README, report, SKILL.md, brochure, best-practice) e vuole un PDF formattato e gradevole
- Il documento contiene **tabelle, diagrammi mermaid o code block** che devono rendere bene
- L'utente vuole un PDF batch di una cartella di markdown (es. `docs/specs/*.md`)
- L'utente vuole una **sintesi AI in coda al PDF** per leggere velocemente un documento lungo senza toccare il sorgente

## Quando NON usare

- Conversione **PDF → Markdown** (verso opposto): non e' questa la skill
- Tipografia editoriale estrema (impaginazione su griglia, riviste, libri con leading/kerning fine): valutare InDesign / `pandoc + LaTeX`
- Ambiente senza Chromium **e** senza `markdown-pdf` installati (manca ogni backend)

## Installazione

Backend ad alta fedelta' (consigliato):

```bash
pip install playwright markdown-it-py pygments
playwright install chromium
```

Backend fallback pure-python:

```bash
pip install markdown-pdf
```

Per il tema Gemini (`--gemini-theme`) e la sintesi AI (`--ai-summary`):

```bash
pip install google-genai python-dotenv
```

E una variabile ambiente (caricata da `.env` cercato dalla CWD verso l'alto):

```
GEMINI_API_KEY=...
```

## Regole

1. **Non modificare il sorgente.** Lo script lavora su una copia in memoria. Sintesi AI e tema vivono solo nel PDF.
2. **Default off per le funzioni Gemini.** Sia `--ai-summary` sia `--gemini-theme` richiedono flag esplicito. Non attivarle automaticamente (costo + latenza).
3. **Errori AI non bloccanti.** Se manca la API key / il pacchetto / la chiamata fallisce: warning su `stderr` e PDF generato comunque (con il tema di default, senza sintesi).
4. **Fallback di motore automatico.** Con `--engine auto` (default), se Chromium non e' avviabile si usa `markdown-pdf` senza errori.
5. **Front-matter YAML rimosso prima del rendering.** SKILL.md e spec con metadata in testa vanno strippati (lo script lo fa gia').
6. **Fallback TOC senza errori** (motore markdown-pdf): se i heading non sono lineari, ritenta senza TOC.

## Esempi

```bash
# Conversione singola, alta fedelta' (auto -> chromium se disponibile)
python "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/scripts/convert.py" docs/spec.md

# Output specifico
python "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/scripts/convert.py" docs/spec.md -o reports/spec_v2.pdf

# Tema grafico generato da Gemini su misura del documento
python "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/scripts/convert.py" docs/brochure.md --gemini-theme

# Forzare il fallback pure-python (offline / no Chromium)
python "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/scripts/convert.py" docs/spec.md --engine markdown-pdf

# Batch su una cartella
python "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/scripts/convert.py" docs/specs/*.md --out-dir reports/

# Con sintesi AI in coda al PDF (sorgente .md NON viene toccato)
python "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/scripts/convert.py" docs/long-spec.md --ai-summary

# CSS personalizzato + metadata
python "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/scripts/convert.py" spec.md --css mio_stile.css --title "Spec v2" --author "Team"
```

## Opzioni CLI

| Flag | Default | Descrizione |
|---|---|---|
| `inputs` (positional) | - | Uno o piu' file `.md` |
| `-o`, `--output` | `<input>.pdf` | Path PDF (singolo input) |
| `--out-dir` | dir del sorgente | Cartella output per batch |
| `--engine` | `auto` | `auto` \| `chromium` \| `markdown-pdf` |
| `--gemini-theme` | off | Tema CSS generato da Gemini (motore chromium). Richiede `GEMINI_API_KEY` |
| `--css` | `theme.css` (chromium) / `default.css` (md-pdf) | File CSS custom |
| `--no-css` | off | Disabilita ogni CSS |
| `--toc-level` | `3` | Depth TOC (motore markdown-pdf) |
| `--mode` | `commonmark` | preset markdown-it (motore markdown-pdf) |
| `--paper-size` | `A4` | A4, A5, Letter, ... (motore markdown-pdf) |
| `--title` / `--author` | - | Metadata PDF |
| `--ai-summary` | off | Appende sintesi AI in coda al PDF |
| `--ai-model` | `gemini-3.5-flash` | Modello Gemini per sintesi/tema |

## Motore Chromium (alta fedelta')

Pipeline: `Markdown --(markdown-it-py: tabelle + strikethrough)--> HTML --(tema CSS + mermaid.js)--> Chromium print-to-PDF`.

- **Tema di default** (`styles/theme.css` / `html_engine.DEFAULT_THEME_CSS`): palette sobria navy + accenti oro, heading con gerarchia, tabelle con header a contrasto e zebra striping, callout su blockquote, code block con bordo e highlighting, footer con titolo + `pagina / totale`.
- **`mermaid`**: i fence ```` ```mermaid ```` vengono renderizzati come diagrammi SVG (mermaid.js via CDN — serve rete). Con il fallback markdown-pdf restano testo.
- **Syntax highlighting**: pygments sui code block con lingua dichiarata.
- **Tema Gemini** (`--gemini-theme`): Gemini riceve un estratto del documento + il tema base e produce un foglio di stile su misura. NB: il file `html_engine.py` e' una copia self-contained del motore (vedi progetti che lo integrano in libreria, es. `portfolio_lab.reports.html_render`).

## Sintesi AI opzionale

Con `--ai-summary` lo script accoda una sezione "Sintesi AI (generata automaticamente)" alla **fine del PDF**:

- **TL;DR** (3-4 frasi), **Punti chiave** (5-8 bullet), **Quando consultarlo**, **Limiti / cose da sapere**
- Il file `.md` **non viene modificato** — la sintesi vive solo nel PDF
- Header esplicito + disclaimer sul fatto che il contenuto autoritativo resta il documento
- Errori non bloccanti

Quando suggerirla: documento lungo (spec, RFC, ADR) di cui si chiede il PDF, o richiesta esplicita di "sintesi / riassunto / TL;DR".
Quando NO: documento gia' sintetico o che contiene gia' un proprio abstract.

## Anti-pattern

- ❌ **Aggiungere la sintesi al sorgente `.md`**: la skill esiste apposta per non farlo.
- ❌ **Attivare `--ai-summary` / `--gemini-theme` di default**: hanno costi e latenza, sempre opt-in.
- ❌ **Bloccare la generazione se Gemini non risponde**: la conversione MD->PDF deve funzionare anche offline (tema di default).
- ❌ **Passare `.md` con front-matter YAML senza strippiarlo**: lo script lo fa gia'.
- ❌ **Rigenerare il tema Gemini a ogni run in pipeline batch**: chi integra il motore in libreria dovrebbe cache-are il tema (vedi `gemini_theme.get_theme_css`).

## Checklist (per chi modifica la skill)

- [ ] `--engine auto` produce PDF sia con Chromium presente sia con solo markdown-pdf
- [ ] La conversione funziona senza `--gemini-theme` / `--ai-summary` anche con `GEMINI_API_KEY` non settata
- [ ] Le funzioni Gemini su API key mancante stampano warning e producono comunque il PDF
- [ ] Il file `.md` sorgente non viene mai toccato (verifica via `sha256sum` prima/dopo)
- [ ] Front-matter YAML viene strippato
- [ ] Diagrammi mermaid e code block highlighting rendono nel motore chromium
- [ ] Batch mode con `--out-dir` non sovrascrive file fuori dalla cartella indicata

## Limiti noti

- Il motore chromium richiede `playwright install chromium` (una tantum) e, per i diagrammi mermaid, accesso di rete alla CDN
- Il fallback `markdown-pdf` resta limitato: niente header/footer ricorrenti, niente highlighting, niente mermaid
- Funzioni AI (sintesi/tema) solo via Gemini (provider singolo per ora)
