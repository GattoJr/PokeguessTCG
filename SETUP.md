# PokeguessTCG: configurazione della versione con account (beta)

La versione nuova vive in `beta/` e si apre su https://gattojr.github.io/PokeguessTCG/beta/.
Il sito principale (`index.html`) resta il prototipo finché la beta non è pronta.
Il prototipo è salvato anche nel ramo `prototype-v1`: per tornare indietro basta ripristinare `index.html` da lì.

## Come è fatta
- **GitHub Pages** serve le pagine: `beta/index.html` (gioco) e `beta/admin.html` (pannello).
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
   - Site URL: `https://gattojr.github.io/PokeguessTCG/beta/`
   - Redirect URLs: aggiungi `https://gattojr.github.io/PokeguessTCG/**`

### 4. Collegare la pagina
In `beta/config.js` vanno Project URL e chiave publishable. Sono pubblici per natura: la sicurezza sta nelle regole del database.

### 5. Diventare amministratore
1. Apri la beta, entra con Google e scegli il nome utente.
2. Supabase → SQL Editor, esegui (con la tua email):
   ```sql
   insert into public.admins (user_id)
   select id from auth.users where email = 'LA-TUA-EMAIL';
   ```
3. Ora https://gattojr.github.io/PokeguessTCG/beta/admin.html ti mostra il calendario.

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

Il comando scrive le carte (le esistenti vengono aggiornate, le nuove aggiunte) e rigenera `beta/names.json`.

## Accesso con il pulsante Google sul sito (al posto dell'indirizzo supabase.co)
Con il login "a redirect" la finestra di Google mostra l'indirizzo del progetto Supabase. Con il pulsante Google
disegnato direttamente sul sito (Google Identity Services) mostra invece il sito.
1. Google Cloud → il client OAuth "Web application" → **Authorized JavaScript origins** → aggiungi `https://gattojr.github.io`.
2. Copia il **Client ID** (finisce con `.apps.googleusercontent.com`) in `beta/config.js`, campo `googleClientId`.
3. In Supabase → Authentication → Providers → Google lo stesso Client ID deve già esserci (è quello usato per il redirect).
Se il pulsante non si carica, la finestra di accesso offre comunque il vecchio metodo.

## Velocità
- Le immagini dei disegni vengono salvate nel bucket pubblico `art` con nomi segreti e da lì passano per la CDN di Supabase:
  la funzione `art` lavora solo la prima volta per ogni carta.
- La carta del giorno programmata dal pannello è già pronta (l'anteprima la genera); nel Booster la carta successiva
  viene preparata mentre si gioca quella attuale.
