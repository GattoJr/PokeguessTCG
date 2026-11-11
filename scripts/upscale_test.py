"""Upscaling test: the artwork window of a few cards as the game shows it today, next to AI-upscaled versions.
Run by the GitHub Action "Upscale test" (TCGdex is reachable from there). Output in out/."""
import io, pathlib, sys, urllib.request
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont
from spandrel import ModelLoader

CARDS = [("sv01", "036", "Fuecoco", False), ("sv01", "075", "Pawmo", True)]   # Basic common, evolved common
CROP = [0.087, 0.105, 0.836, 0.360]                                            # sv layout, as in the database
EVO, EVOT = [0.030, 0.066, 0.148, 0.112], [0.190, 0.089, 0.330, 0.030]
STRIPE_A, STRIPE_B = (0x2a, 0x3b, 0x60), (0x22, 0x31, 0x4f)
MODELS = {"anime": "models/RealESRGAN_x4plus_anime_6B.pth", "general": "models/RealESRGAN_x4plus.pth"}
OUT = pathlib.Path("out"); OUT.mkdir(exist_ok=True)


def fetch(set_id, num):
    url = f"https://assets.tcgdex.net/en/sv/{set_id}/{num}/high.png"
    req = urllib.request.Request(url, headers={"User-Agent": "pokeguesstcg-upscale-test"})
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert("RGB")


def crop_box(W, H):
    x0, y0 = round(CROP[0] * W), round(CROP[1] * H)
    return x0, y0, min(W - x0, round(CROP[2] * W)), min(H - y0, round(CROP[3] * H))


def censor(img, W, H, x0, y0, scale, evo):
    """Same stripes as crop.js, drawn on an image that is `scale` times the crop."""
    if not evo:
        return img
    px = img.load(); w, h = img.size
    for r in (EVO, EVOT):
        ax = max(0, int((np.floor(r[0] * W) - x0) * scale)); ay = max(0, int((np.floor(r[1] * H) - y0) * scale))
        bx = min(w, int((np.ceil((r[0] + r[2]) * W) - x0) * scale)); by = min(h, int((np.ceil((r[1] + r[3]) * H) - y0) * scale))
        for y in range(ay, by):
            for x in range(ax, bx):
                px[x, y] = STRIPE_A if ((x + y) // (7 * scale)) % 2 else STRIPE_B
    return img


def upscale(model, img):
    t = torch.from_numpy(np.asarray(img)).permute(2, 0, 1).unsqueeze(0).float() / 255
    with torch.no_grad():
        o = model(t)
    o = (o.squeeze(0).permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)
    big = Image.fromarray(o)
    return big.resize((img.width * 2, img.height * 2), Image.LANCZOS)   # 4x model, kept at 2x


def save(img, name):
    p = OUT / name; img.save(p, "JPEG", quality=86); return p.stat().st_size


models = {k: ModelLoader().load_from_file(v).eval() for k, v in MODELS.items()}
font = ImageFont.load_default(size=30)
report = []
for set_id, num, name, evo in CARDS:
    card = fetch(set_id, num); W, H = card.size
    x0, y0, w, h = crop_box(W, H)
    art = card.crop((x0, y0, x0 + w, y0 + h))
    tag = f"{name.lower()}_{set_id}-{num}"
    today = censor(art.copy(), W, H, x0, y0, 1, evo)
    sizes = {"today": save(today, f"{tag}_today.jpg")}
    panels = [("Today (%dx%d, enlarged by the browser)" % (w, h), today.resize((w * 2, h * 2), Image.BICUBIC))]
    for k, m in models.items():
        up = censor(upscale(m, art), W, H, x0, y0, 2, evo)
        sizes[k] = save(up, f"{tag}_{k}.jpg")
        panels.append((f"AI {k} model, 2x ({up.width}x{up.height})", up))
    # full side-by-side, top to bottom
    pw, ph = panels[0][1].size; lab = 48
    sheet = Image.new("RGB", (pw, (ph + lab) * len(panels)), (19, 32, 61)); d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(panels):
        d.text((14, i * (ph + lab) + 8), label, fill=(255, 214, 0), font=font)
        sheet.paste(im, (0, i * (ph + lab) + lab))
    sheet.save(OUT / f"{tag}_compare.jpg", "JPEG", quality=92)
    # close-up: the centre of the artwork at 2x, side by side
    cw, ch = pw // 3, ph // 2; cx, cy = (pw - cw) // 2, (ph - ch) // 2
    zoom = Image.new("RGB", (cw * len(panels) + 10 * (len(panels) - 1), ch + lab), (19, 32, 61)); d = ImageDraw.Draw(zoom)
    for i, (label, im) in enumerate(panels):
        zoom.paste(im.crop((cx, cy, cx + cw, cy + ch)), (i * (cw + 10), lab))
        d.text((i * (cw + 10) + 10, 8), label.split(" (")[0].split(",")[0], fill=(255, 214, 0), font=font)
    zoom.save(OUT / f"{tag}_zoom.jpg", "JPEG", quality=92)
    report.append(f"{name} {set_id}-{num}: card {W}x{H}, artwork {w}x{h}; JPEG sizes " +
                  ", ".join(f"{k} {v // 1024} KB" for k, v in sizes.items()))
(OUT / "report.txt").write_text("\n".join(report) + "\n"); print("\n".join(report))
