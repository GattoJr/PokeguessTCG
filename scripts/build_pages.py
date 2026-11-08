"""Builds the site pages (How to play, FAQ, Daily archive, About, 404) from one template,
and puts the same header and footer on privacy.html and terms.html.

Run from the repository root:  python3 scripts/build_pages.py
Edit the texts here, not in the generated .html files (they are overwritten).
The pages are reached only from the links at the bottom of every page.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGO = (ROOT / "favicon.svg").read_text().replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg aria-hidden="true"').replace('id="h"', 'id="lgclip"').replace('url(#h)', 'url(#lgclip)')

LINKS = [("how-to-play.html", "How to play"), ("faq.html", "FAQ"), ("archive.html", "Daily archive"),
         ("about.html", "About"), ("privacy.html", "Privacy"), ("terms.html", "Terms")]


def head(title, desc, base=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{base}<meta name="theme-color" content="#0F1A31">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://gattojr.github.io/PokeguessTCG/og.png">
<script>try{{var t=localStorage.getItem('pg_theme'); if(t==='light'||t==='dark') document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anybody:wdth,wght@75..150,700..900&family=Instrument+Sans:wght@400;600;700&display=swap">
<link rel="stylesheet" href="legal.css">
</head>"""


def top():
    return f"""<header class="pagetop">
    <a class="brand" href="./">{LOGO}<b>Pokeguess<span>TCG</span></b></a>
    <a class="play" href="./">Play</a>
  </header>"""


def foot(current):
    cur = ' aria-current="page"'
    links = "".join('<a href="%s"%s>%s</a>' % (h, cur if h == current else "", t) for h, t in LINKS)
    return f"""<footer class="sitefoot">
    <nav aria-label="Site pages">{links}</nav>
    Unofficial fan site. Card data from <a href="https://github.com/tcgdex/cards-database" target="_blank" rel="noopener">TCGdex</a>. Pokémon and card images are © Nintendo, Creatures, GAME FREAK and The Pokémon Company.
  </footer>"""


def page(name, title, desc, body, base="", scripts=""):
    html = f"""{head(title, desc, base)}
<body>
<div class="page">
  {top()}
  <main class="doc">
{body}
  </main>
  {foot(name)}
</div>
{scripts}</body>
</html>
"""
    (ROOT / name).write_text(html)


def mini(hard=False, free=(30,)):
    cells = []
    for i in range(84):
        r, c = divmod(i, 12)
        ring = min(r, c, 6 - r, 11 - c, 2)
        cls = "f" if i in free else ("" if ring == 0 else ("l" if hard else ("m" if ring == 1 else "h")))
        cells.append(f'<i class="{cls}"></i>' if cls else "<i></i>")
    return f'<div class="mini" aria-hidden="true">{"".join(cells)}</div>'


# ---------------- How to play ----------------
page("how-to-play.html", "How to play · PokeguessTCG",
     "The rules of PokeguessTCG: open tiles, spend points, name the Pokémon card. Daily, Booster and Hard mode, streaks and badges.",
     f"""    <h1>How to play</h1>
    <p class="lead">A Pokémon card is hidden under 84 tiles. Open as few tiles as you can, then name the card. The fewer points you spend, the higher your score.</p>

    <h2>Tiles and points</h2>
    <p>Each card starts with <b>1,000 points</b> in play. Opening a tile shows that part of the artwork and costs its value: the closer to the centre, the more it costs. The first tile (yellow here) is open for free.</p>
    {mini()}
    <div class="legendrow"><span><i style="background:#3D5D92"></i>Edge: 5 points</span><span><i style="background:#2B4677"></i>Inner ring: 15 points</span><span><i style="background:#1A2A4C;outline:1px solid #2B4677"></i>Centre: 60 points</span><span><i style="background:var(--gold)"></i>Free first tile</span></div>
    <p>When the points reach 0 you can still open tiles and guess: the card just scores nothing.</p>

    <h2>Naming the card</h2>
    <ul>
      <li>Type the card’s <b>English name</b> and pick it from the suggestions. Only names from the list can be sent, so a typo never costs you a guess. Capitals and accents don’t matter.</li>
      <li>You have <b>2 guesses</b> per card. A wrong guess costs <b>50 points</b>.</li>
      <li>Stuck? <b>Give up</b> shows the card and scores 0.</li>
    </ul>

    <h2>Four ways to play</h2>
    <div class="facts">
      <div><b>Daily</b><span>One card a day, the same for everyone, with the same free tile. It changes at midnight UTC.</span></div>
      <div><b>Booster</b><span>Ten random cards in a row, never today’s Daily. Up to 10,000 points.</span></div>
      <div><b>Hard</b><span>Only the 34 edge tiles can be opened. 200 points per card, a wrong guess costs 30.</span></div>
    </div>
    <p>Daily (Hard) has its own card, and Booster (Hard) its own leaderboard.</p>
    {mini(hard=True, free=(5,))}

    <h2>Streaks, badges and the leaderboard</h2>
    <ul>
      <li><b>Streak</b>: the days in a row on which you named the Daily card, in Normal or Hard. Miss a whole day and it starts again.</li>
      <li><b>Badges</b>: 32 for each mode, in bronze, silver and holo gold: Daily cards named, streaks, Booster scores, Booster habits and skill badges such as naming a card with only the free tile open.</li>
      <li><b>Leaderboard</b>: the best Booster of every player with an account, in Normal and Hard.</li>
    </ul>

    <h2>Playing without an account</h2>
    <p>You can play everything as a guest: your games are kept in this browser. Sign in with Google to keep them on every device and to appear on the leaderboard; the games you played as a guest move to your account.</p>""")

# ---------------- FAQ ----------------
FAQ = [
    ("When does the Daily card change?", "Every day at midnight UTC: 1 am in Italy in winter, 2 am in summer. Everyone gets the same card and the same free tile."),
    ("Why can I only send names from the suggestions?", "So a typo never costs you a guess. Type a few letters and pick the card from the list; capitals and accents don’t matter."),
    ("Is the answer the Pokémon or the card name?", "The card name in English, exactly as printed, for example a trainer’s Pokémon or a name with a suffix. The suggestions show every name you can send."),
    ("How does the streak work?", "It counts the days in a row on which you named the Daily card, in Normal or Hard. A missed or abandoned Daily doesn’t count, and the Booster doesn’t either."),
    ("What is Hard mode?", "Only the 34 tiles on the edge can be opened, so you see much less of the artwork. Each card is worth 200 points and a wrong guess costs 30."),
    ("Do I need an account?", "No. Guests can play every mode and earn badges in their browser. Signing in with Google keeps your results on every device and puts your best Booster on the leaderboard."),
    ("Which cards are in the game?", "Regular cards from the Scarlet & Violet, Sword & Shield and Mega Evolution series. Full-art cards and V, VMAX, VSTAR and ex cards are left out."),
    ("Where can I see past Daily cards?", "In the Daily archive, with how all players did and your own score. Today’s card stays hidden until the next day."),
    ("Is this an official Pokémon game?", "No. PokeguessTCG is an unofficial fan site, not affiliated with Nintendo, Creatures, GAME FREAK or The Pokémon Company."),
    ("How do I delete my account?", "Write to pokeguesstcg@gmail.com from the email address of your account. Your data is deleted within 30 days."),
]
page("faq.html", "FAQ · PokeguessTCG", "Answers about PokeguessTCG: the Daily card, scoring, Hard mode, streaks, accounts and the cards in the game.",
     """    <h1>Frequently asked questions</h1>
    <p class="lead">Short answers about the Daily card, scoring, accounts and the cards in the game.</p>
    <div class="faq">
""" + "\n".join(f"      <details{' open' if i == 0 else ''}><summary>{q}</summary><p>{a}</p></details>" for i, (q, a) in enumerate(FAQ)) + """
    </div>
    <p style="margin-top:16px">Something else? Write to <a href="mailto:pokeguesstcg@gmail.com">pokeguesstcg@gmail.com</a>.</p>""")

# ---------------- About ----------------
page("about.html", "About · PokeguessTCG", "What PokeguessTCG is, who makes it and where the card data comes from.",
     """    <h1>About PokeguessTCG</h1>
    <p class="lead">PokeguessTCG is a free browser game for Pokémon Trading Card Game fans: name the card from a small part of its artwork.</p>

    <h2>Why it exists</h2>
    <p>Collectors know cards by their artwork long before they read the name. PokeguessTCG turns that into a daily puzzle: a new card every day, the same for everyone, plus Booster runs of ten cards and a Hard mode for the experts.</p>

    <h2>Who makes it</h2>
    <p>PokeguessTCG is made by a single fan in Italy, in their free time. It has no publisher and no sponsor.</p>

    <h2>The cards</h2>
    <p>Card names, sets and images come from <a href="https://tcgdex.dev" target="_blank" rel="noopener">TCGdex</a>, an open database of Pokémon TCG cards (MIT licence). The game uses regular cards from the Scarlet &amp; Violet, Sword &amp; Shield and Mega Evolution series.</p>
    <div class="box">PokeguessTCG is an unofficial fan site. It is not affiliated with, sponsored or endorsed by Nintendo, Creatures, GAME FREAK or The Pokémon Company. Pokémon, card names and card images are trademarks and copyright of their owners. If you own rights to any content here and want it removed, write to the address below.</div>

    <h2>How it works</h2>
    <p>The game runs in your browser. Scores, the Daily schedule and accounts are kept on servers in the European Union. Signing in is optional and uses Google. Read the <a href="privacy.html">Privacy Policy</a> for the details.</p>

    <h2>Contact</h2>
    <p>Ideas, bugs or questions: <a href="mailto:pokeguesstcg@gmail.com">pokeguesstcg@gmail.com</a>.</p>""")

# ---------------- Daily archive ----------------
ARCHIVE_JS = """<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>
<script src="config.js?v=5"></script>
<script>
(function(){
  var CFG = window.PG_CONFIG || {}, sb = null;
  try{ sb = window.supabase.createClient(CFG.supabaseUrl, CFG.supabaseKey, {auth:{persistSession:true, autoRefreshToken:true, detectSessionInUrl:false}}); }catch(e){}
  var guest = null; try{ guest = JSON.parse(localStorage.getItem('pg_guest')); }catch(e){}
  var state = {hard:false, before:null, done:false, busy:false};
  var list = document.getElementById('arch'), more = document.getElementById('more'), status = document.getElementById('status');
  function fmt(n){ return Number(n).toLocaleString('en-US'); }
  function day(d){ return new Date(d+'T00:00:00Z').toLocaleDateString('en-GB',{weekday:'short', day:'numeric', month:'short', year:'numeric', timeZone:'UTC'}); }
  function el(tag, cls, text){ var e=document.createElement(tag); if(cls) e.className=cls; if(text!=null) e.textContent=text; return e; }
  function todayRow(){
    var li=el('li'); li.appendChild(el('span','hid','?'));
    var mid=el('div'); mid.appendChild(el('b',null,'Today’s card')); mid.appendChild(el('small',null,'Hidden until tomorrow. Name it before the others!')); li.appendChild(mid);
    var go=el('a','go','Play'); go.href='./'; var sc=el('div','sc'); sc.appendChild(go); li.appendChild(sc);
    return li;
  }
  function row(x){
    var li=el('li'), img=el('img'); img.alt=x.name+' card'; img.loading='lazy'; img.width=56; img.height=77;
    img.src=x.image+'/low.webp'; img.onerror=function(){ if(!/png$/.test(img.src)) img.src=x.image+'/low.png'; };
    li.appendChild(img);
    var mid=el('div'); mid.appendChild(el('b',null,x.name));
    mid.appendChild(el('small',null,'#'+x.no+', '+day(x.day)));
    mid.appendChild(el('small',null,x.set+(x.players ? '. Named by '+x.named+' of '+x.players+' player'+(x.players===1?'':'s') : '. Nobody played it')));
    li.appendChild(mid);
    var sc=el('div','sc');
    if(x.mine!=null){ var b=el('b',x.mine_won?null:'miss',x.mine_won?fmt(x.mine):'Missed'); sc.appendChild(b); sc.appendChild(el('small',null,'your score')); }
    else if(x.players){ sc.appendChild(el('b',null,fmt(x.avg))); sc.appendChild(el('small',null,'average')); }
    li.appendChild(sc);
    if(x.mine!=null && x.players){ mid.appendChild(el('small',null,'Average '+fmt(x.avg))); }
    return li;
  }
  function load(reset){
    if(!sb){ status.textContent='The archive is not available right now.'; return; }
    if(state.busy) return;
    if(reset){ state.before=null; state.done=false; list.innerHTML=''; list.appendChild(todayRow()); }
    state.busy=true; more.hidden=true; status.textContent='Loading…';
    sb.rpc('daily_archive',{p_hard:state.hard, p_guest:guest, p_before:state.before, p_limit:30}).then(function(r){
      state.busy=false;
      if(r.error) throw r.error;
      var rows=r.data||[];
      rows.forEach(function(x){ list.appendChild(row(x)); });
      if(rows.length){ state.before=rows[rows.length-1].day; }
      state.done = rows.length<30;
      more.hidden = state.done;
      status.textContent = (!rows.length && list.children.length<=1) ? 'No past Daily cards yet. Come back tomorrow!' : '';
    }).catch(function(e){
      state.busy=false;
      status.textContent = /fetch|network/i.test(String(e && e.message)) ? 'No connection. Check your internet and reload the page.' : 'The game server is waking up. Reload the page in a few seconds.';
    });
  }
  document.querySelectorAll('[data-hard]').forEach(function(b){
    b.addEventListener('click',function(){
      state.hard = b.getAttribute('data-hard')==='1';
      document.querySelectorAll('[data-hard]').forEach(function(x){ x.setAttribute('aria-selected', x===b); });
      load(true);
    });
  });
  more.addEventListener('click',function(){ load(false); });
  load(true);
})();
</script>
"""
page("archive.html", "Daily archive · PokeguessTCG", "Every past Daily card of PokeguessTCG, with how all players did and your own score.",
     """    <h1>Daily archive</h1>
    <p class="lead">Every past Daily card, with how many players named it and your own score. Today’s card stays hidden until tomorrow.</p>
    <div class="seg" role="tablist" aria-label="Mode"><button type="button" role="tab" data-hard="0" aria-selected="true">Daily</button><button type="button" role="tab" data-hard="1" aria-selected="false">Daily <i>(Hard)</i></button></div>
    <ul class="arch" id="arch" aria-live="polite"></ul>
    <p class="status" id="status"></p>
    <button class="morebtn" id="more" type="button" hidden>Show older cards</button>""", scripts=ARCHIVE_JS)

# ---------------- 404 ----------------
page("404.html", "Page not found · PokeguessTCG", "This page doesn’t exist.",
     f"""    <div class="lost">
    {mini(free=(29, 30, 41))}
    <h1>This page is still face down</h1>
    <p class="lead">The address doesn’t match any page. Today’s card is waiting on the home page.</p>
    <p><a class="play" href="./" style="display:inline-flex;align-items:center;height:44px;padding:0 20px;border-radius:12px;background:var(--gold);color:#2E2300;font-weight:700;text-decoration:none;box-shadow:inset 0 -3px 0 var(--gold-deep)">Play today’s card</a></p>
    </div>""", base='<base href="/PokeguessTCG/">\n')

# ---------------- Privacy and Terms: same header and footer ----------------
for name in ("privacy.html", "terms.html"):
    p = ROOT / name
    s = p.read_text()
    s = re.sub(r'  <a class="back" href="\./">‹ Back to the game</a>\n|  <header class="pagetop">.*?</header>\n', "  " + top() + "\n", s, flags=re.S)
    s = re.sub(r'  <p class="foot">.*?</p>\n|  <footer class="sitefoot">.*?</footer>\n', "  " + foot(name) + "\n", s, flags=re.S)
    if "pg_theme" not in s:
        s = s.replace('<link rel="preconnect" href="https://fonts.googleapis.com">',
                      "<script>try{var t=localStorage.getItem('pg_theme'); if(t==='light'||t==='dark') document.documentElement.setAttribute('data-theme',t);}catch(e){}</script>\n<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">", 1)
    p.write_text(s)
print("pages built")
