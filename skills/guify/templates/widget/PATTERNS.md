# Widget in-chat — pattern (superficie leggera di /guify)

GUI **dentro la conversazione** Claude Code (desktop app con il tool di
visualizzazione widget). Zero file nel progetto, zero infra: il widget è HTML/
SVG renderizzato nella chat, e l'input torna alla sessione con `sendPrompt()`.

## Quando è la superficie giusta

- L'unico utente è chi ha la sessione aperta (tu)
- Il pannello serve ADESSO, dentro il flusso di lavoro: form rapido, checklist
  interattiva, scelta tra opzioni, mini-dashboard sui dati appena prodotti
- Non serve persistenza: il widget è effimero, vive nella conversazione

Se serve che sopravviva alla sessione o che lo veda un collega → artifact.
Se serve a chi non ha Claude → standalone.

## I tre pattern

### 1. Form → prompt
Un form HTML i cui campi compongono un prompt preciso via `sendPrompt()`:

```js
function submit() {
  const settimana = document.getElementById("settimana").value;
  sendPrompt(`Genera il report della settimana ${settimana} seguendo la skill di progetto.`);
}
```

Il valore: l'utente non riscrive l'istruzione ogni volta, e il prompt che
parte è sempre quello giusto. È la versione in-chat della regola G1.

### 2. Console di scelte
Bottoni per le decisioni ricorrenti ("approva", "rigenera", "passa al
prossimo") che mandano prompt canonici. Utile nei loop di revisione: la
decisione diventa un click, non una frase da riscrivere.

### 3. Dashboard di sessione
Vista compatta dei dati appena prodotti (tabella, chart) con azioni contestuali
per riga ("approfondisci questo PM", "rigenera questo report") via
`sendPrompt()` parametrizzato.

## Regole

- **Un widget = un'azione chiara.** Non costruire "l'app dentro la chat":
  oltre 2-3 azioni per widget, il caso d'uso chiede un'altra superficie.
- **I prompt generati sono template fissi** con i valori dei campi interpolati:
  mai un textarea libero che passa a `sendPrompt` tal quale, se il widget
  serve a disciplinare l'input.
- **Niente stato critico nel widget**: è effimero. Lo stato vive nei file
  della lavorazione.
