---
name: md-to-pdf
description: "Converte file Markdown in PDF formattati (pure-python, via libreria markdown-pdf). Supporta tabelle, table of contents, CSS personalizzato, batch e una sintesi AI opzionale (Gemini) appesa in coda al PDF senza alterare il sorgente .md. Usa questa skill quando l'utente vuole esportare in PDF una spec, una skill, un report o un documento markdown, oppure ottenere una sintesi rapida del contenuto."
---

# /md-to-pdf — Markdown -> PDF (con sintesi AI opzionale)

Skill per trasformare un file Markdown in PDF formattato. **Pure-python**: nessun runtime nativo (GTK, cairo, LaTeX) da installare. La sintesi AI è opzionale, dietro flag esplicito, e **non modifica mai il sorgente `.md`**.

## Quando usare

- L'utente ha un `.md` (spec, README, report, SKILL.md, best-practice) e vuole un PDF formattato
- L'utente vuole un PDF batch di una cartella di markdown (es. `docs/specs/*.md`)
- L'utente vuole una **sintesi AI in coda al PDF** per leggere velocemente un documento lungo senza dover toccare il sorgente

## Quando NON usare

- Output editoriale tipografico (paginazione fine, header/footer ricorrenti, page-break custom): meglio `weasyprint` o `pandoc + LaTeX`
- Conversione **PDF → Markdown** (verso opposto): non e questa la skill
- Documenti con syntax highlighting essenziale nei code block: `markdown-pdf` rende monospace plain
- Il documento contiene immagini con path assoluti che non esistono sul disco del chiamante

## Installazione

La skill richiede una dipendenza pip:

```bash
pip install markdown-pdf
```

Per la sintesi AI (`--ai-summary`) servono inoltre:

```bash
pip install google-genai python-dotenv
```

E una variabile ambiente:

```
GEMINI_API_KEY=...
```

(caricata da `.env` cercato a partire dalla CWD verso l'alto).

## Regole

1. **Non modificare il sorgente.** Lo script lavora su una copia in memoria. La sintesi AI vive solo nel PDF.
2. **Default off per AI.** La sintesi richiede flag esplicito (`--ai-summary`). Non attivarla automaticamente.
3. **Errori non bloccanti per AI.** Se manca la API key, manca il pacchetto, o la chiamata fallisce: warning su `stderr` e PDF generato comunque, senza sintesi.
4. **Front-matter YAML rimosso prima del rendering.** Le SKILL.md, le spec con metadata Jekyll/Hugo hanno `---...---` in testa: vanno strippati o `markdown-pdf` rompe il TOC.
5. **Fallback TOC senza errori.** Se i heading del MD non sono lineari (saltano da H1 a H3), il TOC fallisce: ritenta automaticamente senza TOC con un warning.

## Esempi

```bash
# Conversione singola (output accanto al sorgente, .md -> .pdf)
python skills/md-to-pdf/scripts/convert.py docs/spec.md

# Output specifico
python skills/md-to-pdf/scripts/convert.py docs/spec.md -o reports/spec_v2.pdf

# Batch su una cartella
python skills/md-to-pdf/scripts/convert.py docs/specs/*.md --out-dir reports/

# Con sintesi AI in coda al PDF (sorgente .md NON viene toccato)
python skills/md-to-pdf/scripts/convert.py docs/long-spec.md --ai-summary

# Modello Gemini esplicito
python skills/md-to-pdf/scripts/convert.py docs/spec.md --ai-summary --ai-model gemini-3.1-pro-preview

# CSS personalizzato + metadata
python skills/md-to-pdf/scripts/convert.py spec.md --css mio_stile.css --title "Spec v2" --author "Team"

# Senza TOC, formato Letter
python skills/md-to-pdf/scripts/convert.py spec.md --toc-level 0 --paper-size Letter
```

## Opzioni CLI

| Flag | Default | Descrizione |
|---|---|---|
| `inputs` (positional) | - | Uno o piu file `.md` |
| `-o`, `--output` | `<input>.pdf` | Path PDF (singolo input) |
| `--out-dir` | dir del sorgente | Cartella output per batch |
| `--css` | `styles/default.css` | File CSS custom |
| `--no-css` | off | Disabilita ogni CSS |
| `--toc-level` | `3` | Depth TOC (0 = no TOC) |
| `--mode` | `commonmark` | preset markdown-it: `commonmark`, `default`, `zero` |
| `--paper-size` | `A4` | A4, A5, Letter, ... |
| `--title` / `--author` | - | Metadata PDF |
| `--ai-summary` | off | Appende sintesi AI in coda al PDF |
| `--ai-model` | `gemini-3.1-pro-preview` | Modello Gemini per la sintesi |

## Sintesi AI opzionale

Con `--ai-summary` lo script accoda una sezione "Sintesi AI (generata automaticamente)" alla **fine del PDF**, contenente:

- **TL;DR** (3-4 frasi)
- **Punti chiave** (5-8 bullet)
- **Quando consultarlo** (a chi serve, in che casi)
- **Limiti / cose da sapere** (prerequisiti, attenzioni)

Caratteristiche:
- Il file `.md` **non viene modificato** — la sintesi vive solo nel PDF
- Header esplicito + disclaimer "Sintesi prodotta da `<modello>` a scopo di lettura veloce. Il contenuto autoritativo resta quello del documento sopra."
- Errori non bloccanti: API key assente o chiamata fallita → warning + PDF senza sintesi (mai blocco)
- Pensata per spec lunghe, SKILL.md di terzi, best-practice, report — quando il lettore vuole un'idea rapida prima della lettura integrale

Quando suggerirla all'utente:
- Documento lungo (spec, RFC, ADR) di cui si chiede un PDF
- L'utente chiede esplicitamente "una sintesi", "un riassunto", "un executive summary", "un TL;DR"

Quando NON suggerirla:
- Documento gia di per se sintetico (TL;DR, README breve, slide markdown)
- Documenti che contengono gia un loro abstract/sintesi al proprio interno

## Anti-pattern

- ❌ **Aggiungere la sintesi al sorgente `.md`**: la skill esiste apposta per non farlo. Se l'utente la vuole nel sorgente, e un'altra operazione (modifica file).
- ❌ **Attivare `--ai-summary` di default**: ha costi (chiamata API) e tempi (latenza), va sempre opt-in.
- ❌ **Bloccare la generazione se Gemini non risponde**: la conversione MD->PDF deve funzionare anche offline. La sintesi e un nice-to-have.
- ❌ **Cercare di renderizzare proprieta CSS Paged Media avanzate** (header/footer ricorrenti, page-break-after): `markdown-pdf` non le supporta. In caso, suggerire `weasyprint`.
- ❌ **Passare `.md` con front-matter YAML senza strippiarlo prima**: lo script lo fa gia automaticamente; non duplicare la logica nel chiamante.

## Checklist (per chi modifica la skill)

- [ ] La conversione MD->PDF funziona senza `--ai-summary` anche con `GEMINI_API_KEY` non settata
- [ ] La conversione con `--ai-summary` su API key mancante stampa warning e produce PDF senza sintesi
- [ ] Il file `.md` sorgente non viene mai toccato (verifica via `sha256sum` prima/dopo)
- [ ] Front-matter YAML viene strippato (test: SKILL.md di un'altra skill con `---...---` in testa)
- [ ] Il fallback TOC funziona su MD con heading non lineari (test: file che inizia con `## ...` senza H1)
- [ ] Batch mode con `--out-dir` non sovrascrive file fuori dalla cartella indicata

## Limiti noti

- No header/footer ricorrenti per pagina (limite di `markdown-pdf`)
- No syntax highlighting nei code block (rendering monospace plain)
- Sintesi AI solo via Gemini (provider singolo per ora; in futuro potrebbe essere multi-provider via env var)
