"""Measure the artwork window and the censor boxes on the pokemontcg.io pictures, per series.
For several cards per series: find the TCGdex artwork window (whose fractions we know) inside the pokemontcg.io
picture by template matching, then carry every box (crop, evo, evot, mega) over with the same scale and offset.
Prints the median per series and draws the boxes on the cards for a visual check. Output in out/measure/."""
import io, json, statistics, sys, urllib.request, time
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_sources import playable_cards  # noqa: E402

TCGDEX = {  # fractions [left, top, width, height] measured on TCGdex pictures (the layouts table today)
    "sv":   {"crop": [0.087, 0.105, 0.836, 0.360], "evo": [0.030, 0.066, 0.148, 0.112], "evot": [0.190, 0.089, 0.330, 0.030]},
    "me":   {"crop": [0.087, 0.105, 0.836, 0.360], "evo": [0.022, 0.060, 0.165, 0.125], "evot": [0.185, 0.089, 0.340, 0.030],
             "mega": [0.550, 0.085, 0.385, 0.055]},
    "swsh": {"crop": [0.087, 0.105, 0.836, 0.362], "evo": [0.036, 0.062, 0.124, 0.096], "evot": [0.172, 0.090, 0.360, 0.030]},
}
OUT = Path("out/measure"); OUT.mkdir(parents=True, exist_ok=True)
font = ImageFont.load_default(size=22)
log = []
def say(s=""): print(s, flush=True); log.append(s)

def get(url):
    for i in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")

def pick(cards, serie):
    cs = [c for c in cards if c["serie"] == serie and c["ptcg"]]
    sets = sorted({c["set_id"] for c in cs}, key=lambda s: next(c["set_date"] for c in cs if c["set_id"] == s))
    chosen = []
    for s in [sets[0], sets[len(sets) // 3], sets[2 * len(sets) // 3], sets[-1]]:
        inset = [c for c in cs if c["set_id"] == s]
        b = [c for c in inset if not c["has_evo"]]; e = [c for c in inset if c["has_evo"] and not c["name"].startswith("Mega ")]
        chosen += b[len(b) // 2: len(b) // 2 + 1] + e[len(e) // 2: len(e) // 2 + 1]
    if serie == "me":
        megas = [c for c in cs if c["name"].startswith("Mega ")]
        chosen += megas[:: max(1, len(megas) // 3)][:3]
    return chosen

cards = playable_cards()
result = {}
for serie, boxes in TCGDEX.items():
    say(f"=== {serie}")
    meas = {k: [] for k in boxes}; drawn = []
    for c in pick(cards, serie):
        t = Image.open(io.BytesIO(get(c["tcgdex"]))).convert("RGB")
        p = Image.open(io.BytesIO(get(c["ptcg"]))).convert("RGB")
        W, H = t.size; PW, PH = p.size
        cr = boxes["crop"]; x0, y0, w, h = round(cr[0] * W), round(cr[1] * H), round(cr[2] * W), round(cr[3] * H)
        tm0 = cv2.cvtColor(np.asarray(t.crop((x0, y0, x0 + w, y0 + h))), cv2.COLOR_RGB2GRAY)
        pg = cv2.cvtColor(np.asarray(p), cv2.COLOR_RGB2GRAY); best = None
        for s in np.arange(PW / W - 0.06, PW / W + 0.06, 0.002):
            tm = cv2.resize(tm0, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
            r = cv2.matchTemplate(pg, tm, cv2.TM_CCOEFF_NORMED); _, v, _, loc = cv2.minMaxLoc(r)
            if not best or v > best[0]: best = (v, s, loc)
        v, s, (px, py) = best
        def carry(b):  # TCGdex fractions -> pokemontcg.io fractions
            return [(px + (b[0] * W - x0) * s) / PW, (py + (b[1] * H - y0) * s) / PH, b[2] * W * s / PW, b[3] * H * s / PH]
        mapped = {k: carry(b) for k, b in boxes.items()}
        for k in boxes:
            if k == "mega" and not c["name"].startswith("Mega "): continue
            if k in ("evo", "evot") and not c["has_evo"]: continue
            meas[k].append(mapped[k])
        say(f"  {c['id']:12s} {c['name'][:24]:24s} {PW}x{PH} scale {s:.3f} match {v:.3f}  crop [{', '.join(f'{x:.4f}' for x in mapped['crop'])}]")
        drawn.append((c, p, mapped, v))
    med = {k: [round(statistics.median(m[i] for m in v), 4) for i in range(4)] for k, v in meas.items() if v}
    for k, v in meas.items():
        if v:
            spread = max(max(m[i] for m in v) - min(m[i] for m in v) for i in range(4))
            say(f"  {k:5s} median {med[k]}  (largest spread between cards {spread:.4f}, {len(v)} cards)")
    result[serie] = med
    # visual check: every card with the median boxes drawn (yellow = artwork window, red = censors)
    th = 520; tiles = []
    for c, p, mapped, v in drawn:
        im = p.copy(); d = ImageDraw.Draw(im); PW, PH = im.size
        for k, b in med.items():
            if k == "mega" and not c["name"].startswith("Mega "): continue
            if k in ("evo", "evot") and not c["has_evo"]: continue
            d.rectangle([b[0] * PW, b[1] * PH, (b[0] + b[2]) * PW, (b[1] + b[3]) * PH], outline=(255, 214, 0) if k == "crop" else (255, 40, 40), width=4)
        im = im.resize((round(th * PW / PH), th)); ImageDraw.Draw(im).text((8, th - 30), c["id"], fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        tiles.append(im)
    cols = 4; rows = (len(tiles) + cols - 1) // cols; tw = tiles[0].width
    sheet = Image.new("RGB", (tw * cols, th * rows), (19, 32, 61))
    for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(OUT / f"{serie}_boxes.jpg", quality=88)
say("")
say("RESULT (pokemontcg.io fractions): " + json.dumps(result))
(OUT / "report.txt").write_text("\n".join(log) + "\n")
(OUT / "layouts_ptcg.json").write_text(json.dumps(result, indent=1))
