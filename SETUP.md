# PokeguessTCG: configurazione (gioco con account, Supabase)

Il gioco è su https://gattojr.github.io/PokeguessTCG/ (dal 24/10/2026; prima era in `beta/`, che ora rimanda qui).
Il pannello amministratore è su https://gattojr.github.io/PokeguessTCG/admin.html.
Il primo prototipo è in `prototype/` (https://gattojr.github.io/PokeguessTCG/prototype/) e nel ramo `prototype-v1`.
La versione rilasciata il 24/10/2026 è salvata anche nel ramo `release-v2`.

## Come è fatta
- **GitHub Pages** serve le pagine: `index.html` (gioco) e `admin.html` (pannello).
- **Supabase** fa da server:
  - login con Google;
  - database (`supabase/migrations/`): carte giocabili, calendario Daily, partite, Booster (10 carte), profili, classifica;
  - funzione `art` (`supabase/functions/art/`): dà al browser solo il riquadro del disegno, già ritagliato e censurato, senza nome né indirizzo della carta.
- Il browser non legge mai le tabelle: chiama funzioni del database che controllano le risposte e calcolano i punti.
- **GitHub Actions** (`.github/workflows/supabase.yml`) pubblica database e funzione su Supabase a ogni modifica in `supabase/`.

## Passi una tantum

### 1. Supabase
1. Nel progetto Supabase annota:
   - **Project URL** e **chiave publishable** (o "anon"): Project Settings → API Keys / Data API;
   - **project ref**: la parte `xxxx` di `https://xxxx.supabase.co`;
   - la **password del database** scelta alla creazione (se l'hai persa: Project Settings → Database → Reset password).
2. Crea un **access token**: supabase.com → icona account → Access Tokens → Generate new token.

### 2. Segreti su GitHub
Repository → Settings → Secrets and variables → Actions → New repository secret. Creane tre:
- `SUPABASE_ACCESS_TOKEN` = il token del punto 1.2
- `SUPABASE_PROJECT_ID` = il project ref
- `SUPABASE_DB_PASSWORD` = la password del database

Poi: scheda Actions → "Deploy Supabase" → Run workflow. In 2-3 minuti database e funzione sono online.

### 3. Login con Google
1. https://console.cloud.google.com → crea un progetto (es. PokeguessTCG).
2. APIs & Services → OAuth consent screen (o "Google Auth Platform"): tipo External, nome app PokeguessTCG, la tua email; pubblica l'app ("In production") quando vuoi aprirla a tutti.
3. Credentials → Create credentials → OAuth client ID → Web application.
   - Authorized redirect URI: `https://<project-ref>.supabase.co/auth/v1/callback`
4. Copia Client ID e Client secret.
5. Supabase → Authentication → Sign In / Providers → Google: attiva e incolla Client ID e secret.
6. Supabase → Authentication → URL Configuration:
   - Site URL: `https://gattojr.github.io/PokeguessTCG/`
   - Redirect URLs: aggiungi `https://gattojr.github.io/PokeguessTCG/**`

### 4. Collegare la pagina
In `config.js` vanno Project URL e chiave publishable. Sono pubblici per natura: la sicurezza sta nelle regole del database.

### 5. Diventare amministratore
1. Apri il gioco, entra con Google e scegli il nome utente.
2. Supabase → SQL Editor, esegui (con la tua email):
   ```sql
   insert into public.admins (user_id)
   select id from auth.users where email = 'LA-TUA-EMAIL';
   ```
3. Ora https://gattojr.github.io/PokeguessTCG/admin.html ti mostra il calendario.

## Regole del gioco (lato server)
- 1.000 punti per carta, blocchi da 5/15/60 (il primo è gratis), −50 per risposta sbagliata, 2 tentativi.
- Daily: una carta al giorno, uguale per tutti, stesso blocco di partenza. Cambia a mezzanotte UTC.
  Se un giorno non è programmato, il server ne sceglie una a caso (mai una usata nell'ultimo anno) e la fissa per tutti.
- Un giorno si può modificare dal pannello solo finché nessuno l'ha giocato.
- Booster: 10 carte casuali (mai quella del giorno), massimo 10.000 punti, rigiocabile.
- Classifica: miglior Booster di ogni giocatore registrato.
- Gli ospiti giocano tutto; se poi entrano con Google, le partite fatte in quel browser passano al loro account.

## Aggiornare le carte
Supabase applica ogni migrazione una sola volta, quindi le carte nuove vanno in un file nuovo con data successiva.
Dopo aver aggiornato `cards.json`:

```
python3 scripts/build_game_data.py supabase/migrations/AAAAMMGG000001_cards_update.sql
```

Il comando scrive le carte (le esistenti vengono aggiornate, le nuove aggiunte) e rigenera `names.json`.

## Accesso con il pulsante Google sul sito (al posto dell'indirizzo supabase.co)
Con il login "a redirect" la finestra di Google mostra l'indirizzo del progetto Supabase. Con il pulsante Google
disegnato direttamente sul sito (Google Identity Services) mostra invece il sito.
1. Google Cloud → il client OAuth "Web application" → **Authorized JavaScript origins** → aggiungi `https://gattojr.github.io`.
2. Copia il **Client ID** (finisce con `.apps.googleusercontent.com`) in `config.js`, campo `googleClientId`.
3. In Supabase → Authentication → Providers → Google lo stesso Client ID deve già esserci (è quello usato per il redirect).
Se il pulsante non si carica, la finestra di accesso offre comunque il vecchio metodo.

## Velocità
- Le immagini dei disegni vengono salvate nel bucket pubblico `art` con nomi segreti e da lì passano per la CDN di Supabase:
  la funzione `art` lavora solo la prima volta per ogni carta.
- La carta del giorno programmata dal pannello è già pronta (l'anteprima la genera); nel Booster la carta successiva
  viene preparata mentre si gioca quella attuale.

## Modalità (dal 24/10/2026)
- Daily, Booster (ex Guess10), Daily (Hard), Booster (Hard).
- Hard: si aprono solo i blocchi della cornice esterna (5 punti l'uno), 200 punti in palio per carta, −30 per risposta sbagliata,
  2 tentativi. Daily (Hard) ha una carta del giorno diversa e il suo calendario nel pannello (interruttore Daily / Daily (Hard));
  il blocco di partenza Hard deve stare sulla cornice esterna. Booster (Hard) ha la sua classifica (massimo 2.000).

## Accesso con email e password (dal 24/10/2026)

Nella finestra "Sign in", sotto Google, si può entrare o creare un account con email e password.
- **Create an account**: email e password (minimo 8 caratteri). Supabase manda una mail con un **codice di 6 cifre** e un link; il giocatore scrive il codice sul sito (funziona da qualsiasi dispositivo) oppure tocca il link (funziona solo nel browser dove ha chiesto la mail). Poi sceglie il nome utente come con Google.
- **Forgot password?**: arriva un codice; sul sito si scrivono codice e nuova password. Anche qui il link è un'alternativa.
- Se l'email ha già un account (anche via Google) il sito lo dice e propone di entrare. Chi è entrato con Google può aggiungersi una password con "Forgot password?".
- Le partite da ospite passano all'account come con Google.

Impostazioni e modelli delle email stanno in `supabase/auth/` (`settings.json`, `confirmation.html`, `recovery.html`). L'Action **"Configure Supabase sign-in"** li applica a Supabase a ogni modifica di quei file (o a mano dalla scheda Actions), con i segreti già presenti. Imposta anche il Site URL a `https://gattojr.github.io/PokeguessTCG/`. Se cambi i modelli dal pannello Supabase, la prossima esecuzione li sovrascrive: modificali qui.

### Servizio per l'invio delle email (da fare una volta, a mano)
Il servizio email incluso in Supabase manda messaggi **solo agli indirizzi dei membri del progetto** (cioè a te) e pochi all'ora: va bene per provare, non per i giocatori. Serve un servizio SMTP esterno. Brevo è gratuito fino a 300 email al giorno e non richiede un dominio:
1. Crea un account su brevo.com.
2. Senders, Domains & Dedicated IPs → Senders: aggiungi e verifica l'indirizzo mittente (per ora la tua Gmail).
3. SMTP & API → SMTP: annota server (`smtp-relay.brevo.com`), porta (`587`), login, e genera una **SMTP key** (è la password).
4. Supabase → Authentication → Emails → SMTP Settings → Enable custom SMTP: mittente (l'indirizzo verificato), nome mittente `PokeguessTCG`, host, porta, username (il login Brevo), password (la SMTP key). Salva.
5. Supabase → Authentication → Rate Limits: il limite di email all'ora (30 di default con SMTP esterno) si può alzare.
6. Prova: crea un account con un'altra email. Se la mail finisce nello spam, la soluzione definitiva è un dominio tuo (es. pokeguesstcg.io) verificato su Brevo come mittente.

**Finché l'SMTP non è impostato**: Supabase (piano gratuito) non accetta i modelli personalizzati, quindi le mail sono quelle standard di Supabase, con il solo link e senza codice. Inoltre arrivano solo a te: gli altri giocatori che provano a registrarsi vedono "Accounts with an email are not open yet. Please sign in with Google for now.". **Dopo aver impostato l'SMTP**: GitHub → Actions → "Configure Supabase sign-in" → Run workflow, così vengono applicati i modelli con il codice.

L'Action "Configure Supabase sign-in" nel suo riepilogo dice se l'SMTP esterno risulta impostato.
