# Template — Round 0: esplorazione dello scopo

Obiettivo del round: **mappare l'intero panorama** dei candidati plausibili, non
selezionarli. Ampiezza prima della profondita'. Un round 0 che restituisce 3 voci
ha fallito: o il prompt e' troppo stretto, o il tema e' piu' piccolo di un funnel.

Sostituisci tutti i `{{...}}`. Cancella le righe fra parentesi quadre: sono note
per chi compone, non per il modello.

---

## CONTESTO

Sei un ricercatore esperto di {{dominio}} che lavora per {{committente}}.
Oggetto della ricerca: {{soggetto}}.

Caratteristiche rilevanti del soggetto:
{{profilo_sintetico}}

[Anonimizza qui se l'utente ha scelto la variante anonima: range al posto dei
valori esatti, nessun identificativo fiscale/anagrafico, nessun nome proprio.]

Vincoli che restringono il campo:
{{vincoli}}
[es. geografia, tempistiche, budget, requisiti tecnici obbligatori, esclusioni]

## DOMANDA DI RICERCA

{{domanda_ricerca}}

## COSA DEVI PRODURRE

Una **mappatura ampia** di tutti i {{tipo_candidati}} potenzialmente rilevanti per
il soggetto: almeno {{n_minimo_candidati}} voci se esistono, includendo anche
quelle che a un primo sguardo sembrano marginali (le scarteremo noi dopo).

Copri esplicitamente tutte queste categorie, segnalando quelle in cui non hai
trovato nulla:
{{categorie_da_coprire}}
[es. per un dominio pubblico: nazionale / regionale / locale / UE / leve fiscali.
Per un dominio tecnico: soluzioni commerciali / open source / servizi gestiti /
build-in-house. La lista serve a impedire che il modello ignori un intero ramo.]

## PER CIASCUN CANDIDATO, RIPORTA

| Campo | Note |
|---|---|
| Denominazione esatta | come compare nella fonte ufficiale |
| Chi lo pubblica/eroga/produce | ente, azienda, community |
| Riferimento formale | {{tipo_riferimento}} (norma, standard, versione, delibera, DOI) |
| Stato corrente | attivo / in arrivo / chiuso / deprecato — con la data del dato |
| Finestra temporale | apertura, scadenza, ciclo di vita, roadmap |
| Ordine di grandezza economico | {{unita_valore}}, con base di calcolo |
| Requisiti di accesso | chi puo' / cosa serve |
| Perche' e' rilevante per QUESTO soggetto | 1-2 righe, riferite ai vincoli sopra |
| URL della fonte ufficiale | pagina istituzionale/ufficiale, non articoli di terzi |

## FONTI

Privilegia, in questo ordine:
1. {{fonti_primarie}}
   [es. gazzetta/registro ufficiale, sito dell'ente, documentazione del produttore,
   repository ufficiale, standard body]
2. {{fonti_secondarie_ammesse}}
   [es. camere di commercio, associazioni di categoria, testate specializzate]

**Non usare come prova**: blog, aggregatori di notizie, contenuti di consulenti che
vendono il servizio, forum, pagine senza data. Puoi usarli per *scoprire* un
candidato, ma il dato va poi ancorato alla fonte ufficiale, e devi dire quando non
ci sei riuscito.

## REGOLE DI OUTPUT

1. Ogni affermazione fattuale (importi, date, requisiti, versioni) deve avere un
   URL a fianco. Se non hai la fonte, scrivi **"dato non verificato"** — non
   ricostruirlo per plausibilita'.
2. Se una fonte ufficiale e' irraggiungibile o contraddittoria, dillo esplicitamente
   e riporta la contraddizione.
3. Dichiara sempre la **data del dato** (ultimo aggiornamento della pagina): un
   requisito valido l'anno scorso e' rumore.
4. Distingui cio' che e' **in vigore/disponibile ora** da cio' che e' annunciato,
   in consultazione o in beta.
5. Chiudi con tre sezioni brevi:
   - **Cosa non ho trovato** (categorie coperte a vuoto, e perche')
   - **Contraddizioni fra fonti** incontrate
   - **Riga di sintesi parsabile** per ogni candidato:
     `NOME | ENTE | STATO | SCADENZA | VALORE | URL`
     [questa riga serve al round successivo per lavorare in automatico:
      non ometterla dal prompt]
6. Lingua della risposta: {{lingua}}.
