# Artifact — pattern (superficie condivisa di /guify)

GUI come **pagina pubblicata** (artifact): privata di default, condivisibile
coi colleghi che hanno un account Claude. Zero infrastruttura; gira su
claude.ai, non self-hosted.

> Prima di costruire: se nell'ambiente è disponibile la skill
> `artifact-capabilities`, caricala — è l'autorità su cosa il runtime consente
> a questo account (stato condiviso, dati live, versioni, ecc.).

## Quando è la superficie giusta

- Gli utenti sono colleghi CON account Claude e non serve self-hosting
- Il pannello deve **sopravvivere alla sessione** ed essere raggiungibile da
  un link: dashboard di stato, sinottico approvabile, board di lavorazione
- L'interazione con la sessione può essere **asincrona**: la pagina non
  comanda la sessione in tempo reale — la sveglia

## Il collegamento bidirezionale (asincrono)

- **Sessione → GUI**: la sessione ripubblica l'artifact a ogni avanzamento
  (stesso file → stesso URL). Chi guarda ha sempre l'ultima versione.
- **GUI → sessione**: due canali che risvegliano la sessione che tiene il
  watch sull'artifact:
  1. **Commenti** attivati per Claude: il commento arriva alla sessione, che
     agisce e risponde nel thread;
  2. **Pagine che salvano nuove versioni di sé** (dove la capability è
     disponibile): il salvataggio arriva alla sessione come repubblica — la
     sessione rilegge, fonde, riagisce.

## I tre pattern

### 1. Dashboard viva
La sessione (o una routine schedulata) rigenera la pagina a ogni ciclo:
stato della lavorazione, metriche, ultimi report. Read-only, sempre fresca.

### 2. Pannello di approvazione asincrono
La pagina mostra le proposte con il **diff/contenuto reale** (regola G4);
il collega commenta "approvo la 2" sul thread attivato per Claude → la
sessione col watch riceve, applica, ripubblica con lo stato aggiornato.

### 3. Form condiviso
Pagina-form che salva una nuova versione di sé con i valori compilati → la
sessione la riceve, valida i campi (la validazione è sua, non della pagina),
esegue e ripubblica con l'esito.

## Regole

- **La sessione resta l'esecutore**: la pagina raccoglie intenzioni, non ha
  poteri propri. La validazione dell'input sta nella sessione (regola G1).
- **Stesso file → stesso URL**: mai cambiare path a ogni aggiornamento, o i
  colleghi perdono il link.
- **Niente dati sensibili oltre il necessario**: la pagina è condivisibile;
  ciò che ci finisce sopra può essere visto da chiunque riceva il link.
