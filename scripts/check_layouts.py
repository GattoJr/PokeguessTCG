"""Draw the measured boxes (out/measure/layouts_ptcg.json) on evolved cards of every series and every exception set."""
import io, json, sys, time, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_sources import playable_cards  # noqa: E402

L = json.loads(Path("out/measure/layouts_ptcg.json").read_text())
def get(url):
    for i in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    raise RuntimeError(err)
cards = [c for c in playable_cards() if c["ptcg"] and c["has_evo"]]
want = ["sv01", "sv10", "me01", "me05", "swsh1", "swsh12.5"] + list(L["sets"])
font = ImageFont.load_default(size=22); th = 520; tiles = []
for sid in want:
    cs = [c for c in cards if c["set_id"] == sid]
    for c in cs[len(cs) // 2: len(cs) // 2 + 1]:
        lay = L["sets"].get(sid) or L["series"][c["serie"]]
        p = Image.open(io.BytesIO(get(c["ptcg"]))).convert("RGB"); W, H = p.size; d = ImageDraw.Draw(p)
        lw = max(3, W // 180)
        for k in ("crop", "evo", "evot"):
            b = lay[k]
            d.rectangle([b[0] * W, b[1] * H, (b[0] + b[2]) * W, (b[1] + b[3]) * H], outline=(255, 214, 0) if k == "crop" else (255, 40, 40), width=lw)
        top = p.crop((0, 0, W, int(H * 0.5))).resize((560, round(560 * H * 0.5 / W)))
        ImageDraw.Draw(top).text((8, 6), f"{c['id']} {W}x{H}", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        tiles.append(top)
cols = 3; tw = 560; th = max(t.height for t in tiles); rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (tw * cols, th * rows), (19, 32, 61))
for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
sheet.save("out/measure/check_boxes.jpg", quality=88)
print("ok", len(tiles))
