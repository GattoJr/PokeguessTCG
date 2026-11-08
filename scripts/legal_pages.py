"""Privacy Policy, Cookie Policy and Terms of Service. Imported by build_pages.py, which writes the pages.
When a text changes, update UPDATED too."""
from sitekit import page

UPDATED = "8 November 2026"
MAIL = '<a href="mailto:pokeguesstcg@gmail.com">pokeguesstcg@gmail.com</a>'
G_PARTNERS = '<a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">How Google uses information from sites or apps that use its services</a>'
G_ADS = '<a href="https://policies.google.com/technologies/ads" target="_blank" rel="noopener">how Google uses cookies in advertising</a>'
G_CENTER = '<a href="https://myadcenter.google.com/" target="_blank" rel="noopener">My Ad Center</a>'
CHOICES = '<button type="button" class="pgchoices" data-privacy-choices style="text-decoration:underline;text-decoration-color:var(--gold-deep);text-underline-offset:2px">Privacy choices</button>'

# ---------------- Privacy Policy ----------------
page("privacy.html", "Privacy Policy · PokeguessTCG", "How PokeguessTCG handles your data, ads and cookies.", f"""    <h1>Privacy Policy</h1>
    <p class="updated">Last updated: {UPDATED}</p>

    <p class="lead">PokeguessTCG is a free browser game: you name a Pokémon card from its artwork. The game is paid for by ads served by Google. This page explains what data the game and the ads use, why, and what you can do about it. In short: you can play without an account; if you sign in, we keep your email address, your username and your game results; Google shows ads and, only if you agree, personalises them with cookies. We don't sell data.</p>

    <h2>Who is responsible</h2>
    <p>PokeguessTCG is run by a private individual based in Italy, who is the data controller for the data described here. Contact: {MAIL}.</p>

    <h2>Playing without an account</h2>
    <p>You can play every mode without signing in. To remember your games, your browser creates a random guest ID (a code that does not identify you) and stores it on your device together with the tiles you opened. The game server stores the guest ID with your games: the cards you played, the tiles you opened, your guesses and your score. These results also count, without any name, in the "how did other players do" charts.</p>

    <h2>If you sign in with Google</h2>
    <p>When you choose "Sign in with Google", Google tells us:</p>
    <ul>
      <li>your email address and Google account ID, which identify your account;</li>
      <li>your name and profile picture as stored in your Google account. Our sign-in service saves them with your account, but the game does not show or use them.</li>
    </ul>
    <p>We never receive your Google password. We then store:</p>
    <ul>
      <li>the username you choose, which other players see on the leaderboard;</li>
      <li>your games and scores (the same data as for guests), including the games played as a guest in the same browser before signing in, which move to your account;</li>
      <li>the sign-in session on your device, so you stay signed in.</li>
    </ul>
    <p>The leaderboard publicly shows your username and your best Booster score. Your email address is never shown to other players.</p>

    <h2>Ads</h2>
    <p>Ads on PokeguessTCG are served by <b>Google AdSense</b> (Google Ireland Limited). To show an ad, Google receives technical data from your browser, such as your IP address, your browser and device, the page you are on and your general location, and it may read or set cookies and similar identifiers on your device.</p>
    <ul>
      <li><b>Personalised ads</b>, only if you agree: Google and its partners use cookies to show ads based on your interests and on your visits to this and other websites, and to measure how ads perform.</li>
      <li><b>If you refuse</b>: you still see ads, but they are not personalised. They are chosen from the page content and your general location. Google may still use cookies or similar technology to limit how often you see an ad, for aggregated reporting and to fight fraud and abuse.</li>
    </ul>
    <p>You choose with the banner shown on your first visit, and you can change your choice at any time from {CHOICES} at the bottom of every page. To learn more, read {G_PARTNERS} and {G_ADS}. You can also manage the ads Google shows you in {G_CENTER}. Google may pass data to its advertising partners; the list of cookies and storage is in the <a href="cookies.html">Cookie Policy</a>.</p>

    <h2>Why we use this data</h2>
    <ul>
      <li>To run the game and your account: keeping scores, the leaderboard and your results across devices. Legal basis: providing the service you asked for (GDPR art. 6(1)(b)).</li>
      <li>To show personalised ads: only with your consent (GDPR art. 6(1)(a)), which you can withdraw at any time from Privacy choices.</li>
      <li>To show non-personalised ads, which pay for the free game, and to keep the game fair and working, for example spotting abuse or fixing errors. Legal basis: our legitimate interest in running a working, fair and free game (GDPR art. 6(1)(f)).</li>
      <li>To count visits, if we use statistics: we would only use cookie-free tools, such as Cloudflare Web Analytics, that don't identify you.</li>
    </ul>
    <p>We don't send marketing emails and we don't sell your data. Your games and account are never shared with advertisers.</p>

    <h2>Service providers</h2>
    <p>The game relies on these services, which process data on our behalf or receive the technical data (such as your IP address) that any website visit sends:</p>
    <ul>
      <li><b>Supabase</b>: database, sign-in and image storage. Our data is stored in the EU (Ireland).</li>
      <li><b>Google</b>: ads (Google AdSense), "Sign in with Google" and the fonts used by the site (Google Fonts).</li>
      <li><b>GitHub Pages</b>: hosts the website.</li>
      <li><b>jsDelivr</b>: delivers a software library used by the site.</li>
      <li><b>TCGdex</b>: card images are loaded from TCGdex's servers.</li>
      <li><b>Cloudflare</b>: cookie-free visit statistics, if enabled.</li>
    </ul>
    <p>Some of these companies may process technical data outside the European Union. When they do, they rely on the safeguards required by the GDPR, such as the EU Standard Contractual Clauses or the EU-US Data Privacy Framework.</p>

    <h2>Cookies and storage on your device</h2>
    <p>The game stores a few things in your browser so that it works: the guest ID, the tiles you opened, the Booster in progress, your settings, your cookie choice and, if you sign in, your session. These are needed for the game and don't require consent. Google's advertising cookies are described above. Every item, with its purpose and duration, is listed in the <a href="cookies.html">Cookie Policy</a>.</p>

    <h2>How long we keep it</h2>
    <p>Account data and games are kept while your account exists. Guest games stay on the server so that the daily statistics stay correct, but they are not linked to any personal information. Your cookie choice is kept for 6 months, then we ask again. You can delete your account yourself at any time from your profile (Delete account): your email address, your username and the games linked to the account are deleted straight away. If you can't sign in, write to us and we will delete it within 30 days. Data processed by Google for ads is kept according to Google's own policies.</p>

    <h2>Your rights</h2>
    <p>Under the GDPR you can ask to access, correct or delete your data, receive a copy of it, restrict how we use it, or object to its use, and you can withdraw your consent to personalised ads at any time from Privacy choices. Write to {MAIL} from the email address of your account. You can also complain to the Italian data protection authority, the <a href="https://www.garanteprivacy.it" target="_blank" rel="noopener">Garante per la protezione dei dati personali</a>, or to the authority of the EU country where you live.</p>

    <h2>Children</h2>
    <p>The game itself needs no personal data. To create an account you must be at least 14 years old (the age of digital consent in Italy), or have a parent's permission. Children under 14 should not accept personalised ads without a parent's permission.</p>

    <h2>Changes</h2>
    <p>If this policy changes, we will update this page and the date at the top. For important changes we will also tell signed-in players in the game, and if they affect ads we will ask for your choice again.</p>""", ads=False)

# ---------------- Cookie Policy ----------------
NEEDED = [
    ("pg_guest", "Random guest ID that links your games to this browser.", "Until you clear your browser data"),
    ("pg_tiles, pg_run, pg_run_hard", "The tiles you opened and the Booster in progress, so a reload doesn't lose them.", "Until the game or Booster ends"),
    ("pg_last_booster, pg_last_booster_hard", "Your last Booster score, shown on the start screen.", "Until you clear your browser data"),
    ("pg_badges, pg_bdot, pg_claimed", "Which badges you have already seen, and guest games already moved to your account.", "Until you clear your browser data"),
    ("pg_theme, pg_coach", "Your theme (light, dark or automatic) and whether you have seen the quick tour.", "Until you clear your browser data"),
    ("pg_consent", "Your cookie choice, so we don't ask at every visit.", "6 months"),
    ("sb-…-auth-token", "Your sign-in session (Supabase), only if you sign in.", "Until you sign out"),
    ("g_state and other Google sign-in cookies", "Set by Google when you use \"Sign in with Google\".", "Set by Google"),
]
ADS = [
    ("__gads, __gpi", "Google AdSense, on this site. Limit how often you see an ad, measure ads and, with your consent, personalise them.", "Up to 13 months"),
    ("__eoi", "Google AdSense, on this site. Security and fraud prevention for ads.", "Up to 6 months"),
    ("IDE, DSID, ar_debug and others", "Google, on Google domains (doubleclick.net, google.com). Personalised ads and measurement, only with your consent.", "Up to 13 months"),
]


def rows(items):
    return "\n".join(f"        <tr><td><code>{n}</code></td><td>{p}</td><td>{d}</td></tr>" for n, p, d in items)


TABLE_HEAD = "<thead><tr><th>Name</th><th>What it is for</th><th>How long</th></tr></thead>"
page("cookies.html", "Cookie Policy · PokeguessTCG", "The cookies and browser storage used by PokeguessTCG and by Google ads, and how to change your choice.", f"""    <h1>Cookie Policy</h1>
    <p class="updated">Last updated: {UPDATED}</p>

    <p class="lead">Cookies and similar storage are small pieces of data kept by your browser. PokeguessTCG uses some to make the game work, and Google uses some to show and, if you agree, personalise ads. You can change your choice at any time from {CHOICES}.</p>

    <h2>Needed for the game</h2>
    <p>These items are kept in your browser's local storage and are needed for the game to work, so they don't require consent. They stay on your device: the game server only receives the guest ID and your games.</p>
    <table class="ctable">{TABLE_HEAD}<tbody>
{rows(NEEDED)}
    </tbody></table>

    <h2>Ads by Google</h2>
    <p>Ads are served by Google AdSense. With your consent, Google and its partners use cookies to personalise ads and measure them. Without it, the ads are not personalised, but Google may still use cookies to limit how often you see an ad, for aggregated reporting and to prevent fraud. Names and durations are set by Google and may change; the main ones are:</p>
    <table class="ctable">{TABLE_HEAD}<tbody>
{rows(ADS)}
    </tbody></table>
    <p>More in {G_PARTNERS} and {G_ADS}. You can manage the ads Google shows you in {G_CENTER}.</p>

    <h2>Statistics</h2>
    <p>If we count visits, we only use cookie-free tools such as Cloudflare Web Analytics, which store nothing on your device and don't identify you.</p>

    <h2>Your choice</h2>
    <ul>
      <li><b>Accept all</b>: personalised ads.</li>
      <li><b>Reject all</b>: ads that are not personalised. The game works exactly the same.</li>
      <li><b>Customise</b>: turn personalised ads on or off.</li>
    </ul>
    <p>We keep your choice for 6 months, then ask again. You can also delete cookies and site data from your browser settings: the game then forgets your guest games on that device.</p>

    <h2>Contact</h2>
    <p>Questions about cookies or your data: {MAIL}. See also the <a href="privacy.html">Privacy Policy</a>.</p>""", ads=False)

# ---------------- Terms of Service ----------------
page("terms.html", "Terms of Service · PokeguessTCG", "The rules for using PokeguessTCG.", f"""    <h1>Terms of Service</h1>
    <p class="updated">Last updated: {UPDATED}</p>

    <p class="lead">These terms are the rules for using PokeguessTCG, a free browser game where you name a Pokémon card from its artwork. By playing or creating an account you accept them. If you don't agree, please don't use the game.</p>

    <h2>Who runs the game</h2>
    <p>PokeguessTCG is run by a private individual based in Italy. Contact: {MAIL}.</p>

    <h2>Unofficial fan project</h2>
    <div class="box">PokeguessTCG is an unofficial fan site. It is not affiliated with, sponsored or endorsed by Nintendo, Creatures, GAME FREAK or The Pokémon Company. Pokémon, card images and card names are trademarks and copyright of their respective owners.</div>
    <p>Card data comes from <a href="https://github.com/tcgdex/cards-database" target="_blank" rel="noopener">TCGdex</a> (MIT licence). If you own rights to any content shown here and want it removed, write to the contact above and we will act promptly.</p>

    <h2>The game</h2>
    <ul>
      <li>The game is free. You can play without an account.</li>
      <li>An account (with Google) saves your results across devices and puts your best Booster on the public leaderboard.</li>
      <li>Rules, scoring, modes and cards may change over time, for example to fix errors or balance the game.</li>
    </ul>

    <h2>Ads</h2>
    <ul>
      <li>The game is paid for by ads served by Google. How they use your data, and how to choose whether they are personalised, is explained in the <a href="privacy.html">Privacy Policy</a> and the <a href="cookies.html">Cookie Policy</a>.</li>
      <li>We are not responsible for the content of ads or of the websites they lead to. If you see an ad that seems wrong or offensive, tell us.</li>
      <li>Don't click ads you aren't interested in, don't ask others to click them, and don't use scripts or tools that view or click ads automatically.</li>
      <li>You may use an ad blocker; the game works the same.</li>
    </ul>

    <h2>Your account</h2>
    <ul>
      <li>You must be at least 14 years old to create an account, or have a parent's permission.</li>
      <li>Use one account per person and keep access to it to yourself.</li>
      <li>Your username is public. It must not be offensive, impersonate someone else, or contain advertising or personal data.</li>
      <li>You can delete your account at any time from your profile (Delete account), or ask us to do it by writing to the contact above.</li>
    </ul>

    <h2>Fair play</h2>
    <p>Don't cheat or harm the game. In particular, don't:</p>
    <ul>
      <li>use scripts, bots or tools to find the answers or play automatically;</li>
      <li>tamper with the game, its server or other players' data, or overload it with requests;</li>
      <li>create several accounts to climb the leaderboard.</li>
    </ul>
    <p>We may remove scores, rename usernames, or suspend or delete accounts that break these rules.</p>

    <h2>No guarantees</h2>
    <p>The game is offered "as is", for fun. We do our best to keep it running and correct, but we can't guarantee that it is always available, error-free, or that scores and data are never lost. We may change, pause or close the game at any time.</p>

    <h2>Liability</h2>
    <p>To the extent allowed by law, we are not liable for damages arising from using the game, which is free of charge. Nothing in these terms limits liability that cannot be limited by law, such as for intent or gross negligence, or your rights as a consumer.</p>

    <h2>Privacy</h2>
    <p>How we handle your data is explained in the <a href="privacy.html">Privacy Policy</a> and the <a href="cookies.html">Cookie Policy</a>.</p>

    <h2>Changes and applicable law</h2>
    <p>We may update these terms. The date at the top shows the latest version, and continuing to play means you accept it. These terms are governed by Italian law; if you are a consumer, you also keep the protections of the law of the country where you live.</p>""", ads=False)
