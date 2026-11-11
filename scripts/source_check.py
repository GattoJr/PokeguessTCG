"""Check pokemontcg.io as a source of bigger card pictures (run by the Action "Upscale test").
1) coverage: which playable cards of cards.json exist in the pokemontcg.io data (repo PokemonTCG/pokemon-tcg-data)
2) pictures: Fuecoco and Pawmo from both sources, size, where the artwork window falls, sharpness side by side."""
import io, json, pathlib, re, urllib.request, unicodedata
from collections import defaultdict
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path("ptcg-data")
OUT = pathlib.Path("out/source"); OUT.mkdir(parents=True, exist_ok=True)
ERAS = {"me", "swsh", "sv"}
FULL_ART = re.compile(r"^(ultra rare|secret rare|illustration rare|special illustration rare|hyper rare|mega hyper rare|"
                      r"shiny ultra rare|black white rare|mega attack rare|rgb rare|futuristic rare|holo rare v|holo rare vmax|"
                      r"holo rare vstar|double rare)$", re.I)
FULL_ART_NAME = re.compile(r" (ex|V|VMAX|VSTAR)$")
CROP = [0.087, 0.105, 0.836, 0.360]
log = []
def say(s=""): print(s); log.append(s)
def norm(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())
def num(n): return n.lstrip("0") or "0"
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pokeguesstcg-check"}), timeout=60).read()

# ---- 1. coverage
say("LICENSE of PokemonTCG/pokemon-tcg-data: " + (DATA / "LICENSE").read_text().splitlines()[0] if (DATA / "LICENSE").exists() else "no LICENSE file")
db = json.loads((ROOT / "cards.json").read_text())
ours = defaultdict(list)
for c in db["cards"]:
    st = db["sets"][c[0]]; serie = db["series"][st[2]][0]
    rarity = db["rarities"][c[3]] if c[3] is not None and c[3] < len(db["rarities"]) else None
    if serie in ERAS and not ((rarity and FULL_ART.match(rarity)) or FULL_ART_NAME.search(c[2])):
        ours[(st[0], st[1], st[3])].append((c[1], c[2]))
psets = json.loads((DATA / "sets/en.json").read_text())
by_name = {norm(s["name"]): s for s in psets}
say(f"pokemontcg.io sets: {len(psets)}, newest: " + ", ".join(f"{s['id']} {s['name']} ({s['releaseDate']})" for s in sorted(psets, key=lambda s: s["releaseDate"])[-5:]))
say("")
tot = found = 0; missing_sets = []; rows = []
for (sid, sname, sdate), cards in sorted(ours.items(), key=lambda k: k[0][2] or ""):
    ps = by_name.get(norm(sname))
    tot += len(cards)
    if not ps:
        missing_sets.append(f"{sid} {sname} ({sdate}, {len(cards)} cards)"); continue
    f = DATA / "cards/en" / f"{ps['id']}.json"
    pc = {num(x["number"]): x for x in json.loads(f.read_text())} if f.exists() else {}
    hit = [n for n, _ in cards if num(n) in pc]
    found += len(hit)
    big = next(iter(pc.values()), {}).get("images", {}).get("large", "")
    rows.append(f"{sid:10s} -> {ps['id']:10s} {len(hit):4d}/{len(cards):4d}  {sname}")
say(f"COVERAGE: {found} of {tot} playable cards found ({100 * found / max(tot, 1):.1f}%)")
say(f"Sets not found by name: {len(missing_sets)}")
for m in missing_sets: say("  - " + m)
say(""); say("Per set (ours -> pokemontcg.io, cards found / playable):")
for r in rows: say("  " + r)

# ---- 2. pictures
font = ImageFont.load_default(size=28)
def sharp(img):  # variance of the Laplacian, same size for both
    return cv2.Laplacian(cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY), cv2.CV_64F).var()
say(""); say("PICTURES")
for tnum, pnum, name in [("036", "36", "Fuecoco"), ("075", "75", "Pawmo")]:
    t = Image.open(io.BytesIO(get(f"https://assets.tcgdex.net/en/sv/sv01/{tnum}/high.png"))).convert("RGB")
    pcard = next(x for x in json.loads((DATA / "cards/en/sv1.json").read_text()) if x["number"] == pnum)
    url = pcard["images"]["large"]
    p = Image.open(io.BytesIO(get(url))).convert("RGB")
    W, H = t.size
    x0, y0, w, h = round(CROP[0] * W), round(CROP[1] * H), round(CROP[2] * W), round(CROP[3] * H)
    tart = t.crop((x0, y0, x0 + w, y0 + h))
    # find the same window in the pokemontcg.io picture (scale search + template matching)
    pg = cv2.cvtColor(np.asarray(p), cv2.COLOR_RGB2GRAY); best = None
    for s in np.arange(1.0, 1.6, 0.005):
        tm = cv2.resize(cv2.cvtColor(np.asarray(tart), cv2.COLOR_RGB2GRAY), (round(w * s), round(h * s)), interpolation=cv2.INTER_CUBIC)
        if tm.shape[0] >= pg.shape[0] or tm.shape[1] >= pg.shape[1]: break
        r = cv2.matchTemplate(pg, tm, cv2.TM_CCOEFF_NORMED); _, v, _, loc = cv2.minMaxLoc(r)
        if not best or v > best[0]: best = (v, s, loc, tm.shape[1], tm.shape[0])
    v, s, (px, py), pw, ph = best
    PW, PH = p.size
    part = p.crop((px, py, px + pw, py + ph))
    say(f"{name}: TCGdex {W}x{H} ({len(get(f'https://assets.tcgdex.net/en/sv/sv01/{tnum}/high.png')) // 1024} KB png), artwork {w}x{h}")
    say(f"   pokemontcg.io {PW}x{PH} ({url}), artwork {pw}x{ph} = {s:.3f}x, match {v:.3f}, "
        f"window as fractions [{px / PW:.4f}, {py / PH:.4f}, {pw / PW:.4f}, {ph / PH:.4f}]")
    D = (1004, round(1004 * h / w))
    a, b = tart.resize(D, Image.BICUBIC), part.resize(D, Image.BICUBIC)
    say(f"   sharpness at {D[0]}px (higher = more detail): TCGdex {sharp(a):.0f}, pokemontcg.io {sharp(b):.0f}")
    sheet = Image.new("RGB", (D[0], (D[1] + 46) * 2), (19, 32, 61)); d = ImageDraw.Draw(sheet)
    for i, (lab, im) in enumerate([(f"TCGdex ({w}x{h}) enlarged", a), (f"pokemontcg.io ({pw}x{ph}) enlarged", b)]):
        d.text((12, i * (D[1] + 46) + 8), lab, fill=(255, 214, 0), font=font); sheet.paste(im, (0, i * (D[1] + 46) + 46))
    sheet.save(OUT / f"{name.lower()}_sources.jpg", quality=92)
    cw, ch = D[0] // 3, D[1] // 2; cx, cy = (D[0] - cw) // 2, (D[1] - ch) // 2
    z = Image.new("RGB", (cw * 2 + 10, ch + 46), (19, 32, 61)); d = ImageDraw.Draw(z)
    for i, (lab, im) in enumerate([("TCGdex", a), ("pokemontcg.io", b)]):
        z.paste(im.crop((cx, cy, cx + cw, cy + ch)), (i * (cw + 10), 46)); d.text((i * (cw + 10) + 10, 8), lab, fill=(255, 214, 0), font=font)
    z.save(OUT / f"{name.lower()}_sources_zoom.jpg", quality=92)
(OUT / "report.txt").write_text("\n".join(log) + "\n")
