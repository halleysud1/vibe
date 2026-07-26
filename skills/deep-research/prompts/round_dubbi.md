# Template — Stadio 2: round di dubbi

Il round che il funnel deve avere e che quasi nessun processo di ricerca ha: non
serve a **trovare di più**, serve a **chiudere quello che il controllo ha aperto**.

Si lancia quando il cancello (Fase 5.5) ha classificato almeno un dubbio come
**strutturale** — uno che, se si risolve male, cambia la selezione o invalida il
perimetro. I dubbi puntuali NON si portano qui: si chiudono con la gamba veloce
(`round_mirato.md`) o con un `WebFetch`. Un round costa 10-40 minuti: spenderlo per
confermare una data è uno spreco che si paga due volte, in tempo e in attenzione.

Questo round può ripetersi (ricorsione) finché i dubbi strutturali sono chiusi o il
limite dichiarato in Fase 1 è esaurito.

Sostituisci tutti i `{{...}}`.

---

## RUOLO

Sei un ricercatore esperto di {{dominio}} incaricato di una verifica, non di una
ricognizione. Il lavoro precedente ha prodotto risultati che **non sono affidabili
finché non si sciolgono i dubbi qui sotto**. Il tuo compito è scioglierli, o
dimostrare che non si possono sciogliere sulle fonti pubbliche.

## CONTESTO

Oggetto: {{soggetto}} — caratteristiche rilevanti: {{profilo_sintetico}}
Vincoli: {{vincoli}}
Domanda di ricerca originale: {{domanda_ricerca}}

Stato dell'analisi finora: {{sintesi_stato}}
[3-6 righe: quali candidati sono in piedi, quale sarebbe il preferito, e su cosa
poggia quella preferenza. Serve al modello per capire *cosa* è in gioco in ogni
dubbio: un dubbio senza posta in gioco riceve una risposta generica.]

## I DUBBI DA CHIUDERE

{{elenco_dubbi}}

[Uno per blocco, in quest'ordine di importanza. Per ciascuno:
- **Enunciato**: la proposizione falsificabile, non l'impressione.
  ("Lo strumento X richiede la sede operativa in regione" — non "non è chiaro se X
  sia applicabile".)
- **Perché conta**: cosa cambia nella selezione se si risolve nel verso sfavorevole.
- **Cosa dice la fonte finora**: il claim del round precedente, con URL.
- **Perché è in dubbio**: fonte morta, riferimento non rintracciato, contraddizione
  fra fonti, rilievo dell'auditor, dato smentito dal fact-check.]

## PER CIASCUN DUBBIO, PRODUCI

1. **Verdetto**: **CONFERMATO** (il claim regge) / **SMENTITO** (il claim è falso, e
   il dato corretto è questo) / **NON CONCLUSIVO** (le fonti pubbliche non
   permettono di decidere — e allora dimmi *cosa servirebbe* per deciderlo: un atto
   non pubblicato, un interpello, una richiesta all'ente).
2. **La prova**: citazione breve del passaggio decisivo + URL + data di ultimo
   aggiornamento della pagina. Un verdetto senza prova puntuale non è un verdetto.
3. **Conseguenza sulla selezione**: dato il verdetto, il candidato resta in gioco,
   esce, o cambia posizione? Dillo esplicitamente, non lasciarlo dedurre.
4. **Effetti collaterali**: la verifica ha toccato altri claim del lavoro
   precedente? Se hai visto qualcosa che contraddice un dato che nessuno ti ha
   chiesto di controllare, **dillo**: è la scoperta più preziosa di questo round.

## LA DOMANDA DI PREMESSA (obbligatoria, sempre)

Oltre ai dubbi elencati, rispondi a questa:

> **Il perimetro dell'analisi è ancora quello giusto?**
> Dato il soggetto, i vincoli e la domanda di ricerca, c'è qualcosa di
> strutturalmente sbagliato nell'impostazione — un candidato escluso a torto, una
> categoria di {{tipo_candidati}} mai considerata, un requisito frainteso, una
> norma o versione superata, un'assunzione data per buona da tutti?

È la domanda che intercetta l'errore costoso: quello che non sta in nessun dato ma
nell'inquadramento. Se la risposta è "sì, c'è un problema", spiegalo con la fonte
anche se ribalta tutto il lavoro precedente. Se è "no", dillo esplicitamente e in
una riga — non lasciarla senza risposta.

## FONTI

Solo {{fonti_primarie}} come prova. Per i dubbi nati da una contraddizione fra
fonti, vai alla fonte **più a monte** che esista (testo ufficiale, atto pubblicato,
documentazione del produttore), non a una terza fonte che ripete una delle due.

Se una fonte citata dal round precedente è morta o è stata archiviata, dillo e
cerca il documento equivalente ancora pubblicato.

## REGOLE DI OUTPUT

1. Un blocco per dubbio, nell'ordine in cui te li ho dati, con il verdetto in
   **prima riga** del blocco. Chi legge deve poter scorrere solo i verdetti.
2. Niente riepilogo del lavoro precedente, niente reintroduzione del contesto: il
   report di questo round viene letto insieme agli altri, non da solo.
3. **NON CONCLUSIVO è una risposta legittima e preferibile a una plausibile.** Il
   danno di un dubbio chiuso a torto è più grande di quello di un dubbio dichiarato
   aperto: il primo porta una decisione sbagliata fino in fondo, il secondo si vede.
4. Se un dubbio si rivela mal posto (l'enunciato non ha senso applicato a questo
   soggetto), dillo e riformulalo: un dubbio mal posto genera un round inutile.
5. Chiudi con: **quali dubbi restano aperti** dopo il tuo lavoro, e **quali dubbi
   nuovi** hai aperto tu (sono l'input del prossimo giro, o la ragione per fermarsi).
6. Lingua della risposta: {{lingua}}.
