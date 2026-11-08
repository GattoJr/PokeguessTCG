"""Builds one static page for each past Daily (daily/YYYY-MM-DD.html, Normal and Hard card of that day),
the list of all days (daily/index.html) and sitemap.xml. Run every day by the "Daily pages" GitHub Action,
right after the Daily card changes. Today's cards are never included: the server only returns past days.

Run from the repository root:  python3 scripts/build_archive.py
For a test without the server:  ARCHIVE_JSON=file.json python3 scripts/build_archive.py
(file.json = {"normal": [...], "hard": [...]} as returned by daily_archive)
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sitekit import ROOT, SITE, esc, page  # noqa: E402

BASE = '<base href="../">\n'


def config():
    s = (ROOT / "config.js").read_text()
    url = re.search(r"supabaseUrl:\s*'([^']+)'", s).group(1)
    key = re.search(r"supabaseKey:\s*'([^']+)'", s).group(1)
    return url, key


def fetch(hard):
    """All past Daily cards of one mode, newest first."""
    url, key = config()
    out, before = [], None
    while True:
        body = json.dumps({"p_hard": hard, "p_guest": None, "p_before": before, "p_limit": 60}).encode()
        req = urllib.request.Request(url + "/rest/v1/rpc/daily_archive", data=body, method="POST",
                                     headers={"apikey": key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            rows = json.load(r) or []
        out += rows
        if len(rows) < 60:
            return out
        before = rows[-1]["day"]


def load():
    if os.environ.get("ARCHIVE_JSON"):
        d = json.loads(pathlib.Path(os.environ["ARCHIVE_JSON"]).read_text())
        return d["normal"], d["hard"]
    return fetch(False), fetch(True)


def long_day(d):
    x = dt.date.fromisoformat(d)
    return f"{x.strftime('%A')} {x.day} {x.strftime('%B %Y')}"


def n(v):
    return f"{int(v):,}"


def card_block(x, hard):
    mode = "Daily (Hard)" if hard else "Daily"
    pts = 200 if hard else 1000
    if x["players"]:
        pct = round(100 * x["named"] / x["players"])
        stats = (f'{n(x["players"])} player{"s" if x["players"] != 1 else ""} tried it and {n(x["named"])} named it ({pct}%). '
                 f'Average score: {n(x["avg"] or 0)} of {n(pts)} points.')
    else:
        stats = "Nobody played this card."
    img = esc(x["image"] + "/high.webp")
    return f"""      <section class="dcard">
        <img src="{img}" alt="{esc(x['name'])} card from {esc(x['set'])}" width="120" height="167" loading="lazy">
        <div>
          <h2>{mode} #{x['no']}: {esc(x['name'])}</h2>
          <p>Set: {esc(x['set'])}.</p>
          <p>{stats}</p>
        </div>
      </section>"""


def day_page(d, normal, hard, prev_d, next_d):
    cards = [c for c in (normal, hard) if c]
    names = " and ".join(esc(c["name"]) for c in cards)
    title = f"Daily cards of {long_day(d)} · PokeguessTCG"
    desc = f"The PokeguessTCG Daily cards of {long_day(d)}: {', '.join(c['name'] for c in cards)}, with how many players named them."
    nav = []
    nav.append(f'<a href="daily/{prev_d}.html" rel="prev">‹ {long_day(prev_d)}</a>' if prev_d else "<span></span>")
    nav.append(f'<a href="daily/{next_d}.html" rel="next">{long_day(next_d)} ›</a>' if next_d else '<a href="./">Play today’s card ›</a>')
    body = f"""    <h1>Daily cards of {long_day(d)}</h1>
    <p class="lead">On this day the Daily card was {names}{' (the second one in Hard mode)' if len(cards) == 2 else ''}. Each player saw the artwork under 84 tiles and named the card from as few tiles as they could.</p>
    <div class="dday">
{chr(10).join(card_block(c, c is hard) for c in cards)}
    </div>
    <nav class="dnav" aria-label="Other days">{''.join(nav)}</nav>
    <p style="margin-top:16px"><a href="daily/">All Daily cards</a> · <a href="archive.html">Daily archive with your scores</a></p>"""
    img = cards[0]["image"] + "/high.png"
    page(f"daily/{d}.html", title, desc, body, base=BASE, image=img)


def index_page(days, by_day):
    months = {}
    for d in days:
        months.setdefault(d[:7], []).append(d)
    parts = []
    for m in sorted(months, reverse=True):
        label = dt.date.fromisoformat(m + "-01").strftime("%B %Y")
        items = "".join(
            f'<li><a href="daily/{d}.html">{dt.date.fromisoformat(d).day} {dt.date.fromisoformat(d).strftime("%b")}</a>: '
            + " / ".join(esc(c["name"]) for c in by_day[d] if c) + "</li>"
            for d in months[m])
        parts.append(f"      <section><h2>{label}</h2><ul>{items}</ul></section>")
    body = f"""    <h1>Every Daily card</h1>
    <p class="lead">All the past Daily cards of PokeguessTCG, day by day: Normal card first, then Hard. Today’s cards stay hidden until tomorrow.</p>
    <div class="months">
{chr(10).join(parts) if parts else '      <p>No past Daily cards yet.</p>'}
    </div>
    <p><a href="archive.html">Daily archive with your own scores</a> · <a href="./">Play today’s card</a></p>"""
    page("daily/index.html", "Every Daily card · PokeguessTCG",
         "All the past Daily cards of PokeguessTCG, day by day, with how many players named them.", body, base=BASE)


def sitemap(days):
    today = dt.date.today().isoformat()
    urls = [(SITE, today, "daily", "1.0")]
    for f in ("how-to-play.html", "faq.html", "archive.html", "about.html", "privacy.html", "cookies.html", "terms.html"):
        urls.append((SITE + f, None, "monthly", "0.5"))
    urls.append((SITE + "daily/", today, "daily", "0.6"))
    urls += [(SITE + f"daily/{d}.html", d, "yearly", "0.4") for d in days]
    rows = "\n".join(
        f"  <url><loc>{u}</loc>{f'<lastmod>{m}</lastmod>' if m else ''}<changefreq>{c}</changefreq><priority>{p}</priority></url>"
        for u, m, c, p in urls)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n')


def main():
    normal, hard = load()
    by_day = {}
    for x in normal:
        by_day.setdefault(x["day"], [None, None])[0] = x
    for x in hard:
        by_day.setdefault(x["day"], [None, None])[1] = x
    days = sorted(by_day, reverse=True)           # newest first
    keep = set()
    for i, d in enumerate(days):
        prev_d = days[i + 1] if i + 1 < len(days) else None
        next_d = days[i - 1] if i > 0 else None
        day_page(d, by_day[d][0], by_day[d][1], prev_d, next_d)
        keep.add(f"{d}.html")
    for f in (ROOT / "daily").glob("????-??-??.html"):   # a day removed from the schedule
        if f.name not in keep:
            f.unlink()
    index_page(days, by_day)
    sitemap(days)
    print(f"{len(days)} Daily pages built")


if __name__ == "__main__":
    main()
