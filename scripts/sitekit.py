"""Shared template for the site pages (used by build_pages.py and build_archive.py)."""
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Public address of the site. Change it here when the site moves to its own domain.
SITE = "https://gattojr.github.io/PokeguessTCG/"
LOGO = (ROOT / "favicon.svg").read_text().replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg aria-hidden="true"').replace('id="h"', 'id="lgclip"').replace('url(#h)', 'url(#lgclip)')

LINKS = [("how-to-play.html", "How to play"), ("faq.html", "FAQ"), ("archive.html", "Daily archive"),
         ("about.html", "About"), ("privacy.html", "Privacy"), ("cookies.html", "Cookies"), ("terms.html", "Terms")]
CONFIG_JS = '<script src="config.js?v=6"></script>'
CONSENT_JS = '<script src="consent.js?v=2"></script>'


def esc(s):
    return html.escape(str(s), quote=True)


def ad(name):
    return (f'<aside class="adslot" data-ad="{name}" aria-label="Advertisement" hidden>'
            '<span class="adlabel">Advertisement</span><div class="adbox"></div></aside>')


def head(title, desc, path, base="", image=None):
    canon = SITE + ("" if path == "index.html" else path)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{base}<meta name="theme-color" content="#0F1A31">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(image or SITE + 'og.png')}">
<script>try{{var t=localStorage.getItem('pg_theme'); if(t==='light'||t==='dark') document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anybody:wdth,wght@75..150,700..900&family=Instrument+Sans:wght@400;600;700&display=swap">
<link rel="stylesheet" href="legal.css?v=2">
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
    <nav aria-label="Site pages">{links}<button type="button" class="pgchoices" data-privacy-choices>Privacy choices</button></nav>
    Unofficial fan site. Card data from <a href="https://github.com/tcgdex/cards-database" target="_blank" rel="noopener">TCGdex</a>. Pokémon and card images are © Nintendo, Creatures, GAME FREAK and The Pokémon Company.
  </footer>"""


def page(path, title, desc, body, base="", scripts="", ads=True, image=None):
    """Write one page. path is relative to the site root (e.g. 'faq.html' or 'daily/2026-11-07.html')."""
    slot = ("\n  " + ad("page")) if ads else ""
    scripts = scripts.replace(CONFIG_JS + "\n", "")   # config.js always comes first, before consent.js
    out = f"""{head(title, desc, path, base, image)}
<body>
<div class="page">
  {top()}
  <main class="doc">
{body}
  </main>{slot}
  {foot(path)}
</div>
{CONFIG_JS}
{CONSENT_JS}
{scripts}</body>
</html>
"""
    f = ROOT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(out)
