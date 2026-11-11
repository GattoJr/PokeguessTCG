"""Build the game pictures of a card from its original in R2: the artwork window, AI-upscaled, as the players see it
(censored) and as it is shown when the card is over (full). Uses data/layouts_ptcg.json for pokemontcg.io pictures and
the TCGdex layouts for the cards that came from TCGdex.  render(...) is meant to be reused by the full run."""
import io, json
from pathlib import Path
import numpy as np, torch
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LAYOUTS = json.loads((ROOT / "data/layouts_ptcg.json").read_text())
TCGDEX = {
    "sv":   {"crop": [0.087, 0.105, 0.836, 0.360], "evo": [0.030, 0.066, 0.148, 0.112], "evot": [0.190, 0.089, 0.330, 0.030]},
    "me":   {"crop": [0.087, 0.105, 0.836, 0.360], "evo": [0.022, 0.060, 0.165, 0.125], "evot": [0.185, 0.089, 0.340, 0.030]},
    "swsh": {"crop": [0.087, 0.105, 0.836, 0.362], "evo": [0.036, 0.062, 0.124, 0.096], "evot": [0.172, 0.090, 0.360, 0.030]},
}
STRIPE_A, STRIPE_B = (0x2a, 0x3b, 0x60), (0x22, 0x31, 0x4f)
TARGET_W = 1200          # width of the finished artwork picture


def layout(card, source):
    if source == "tcgdex":
        return TCGDEX[card["serie"]]
    return LAYOUTS["sets"].get(card["set_id"]) or LAYOUTS["series"][card["serie"]]


def upscale(model, img, out_w):
    """4x AI model, then down to out_w with Lanczos; plain Lanczos when the picture is already big enough."""
    if model is None or img.width >= out_w * 0.95:
        return img.resize((out_w, round(img.height * out_w / img.width)), Image.LANCZOS)
    t = torch.from_numpy(np.array(img)).permute(2, 0, 1).unsqueeze(0).float() / 255
    with torch.no_grad():
        o = model(t)
    o = (o.squeeze(0).permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)
    return Image.fromarray(o).resize((out_w, round(img.height * out_w / img.width)), Image.LANCZOS)


def render(model, png_bytes, card, source, out_w=TARGET_W):
    card_img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    W, H = card_img.size
    lay = layout(card, source)
    c = lay["crop"]
    x0, y0 = round(c[0] * W), round(c[1] * H)
    w, h = min(W - x0, round(c[2] * W)), min(H - y0, round(c[3] * H))
    art = card_img.crop((x0, y0, x0 + w, y0 + h))
    full = upscale(model, art, out_w)
    k = full.width / w                                   # finished pixels per original pixel
    cens = full.copy()
    if card["has_evo"]:
        a = np.asarray(cens).copy()
        stripe = max(7, round(7 * full.width / 502))     # same stripes as today, scaled to the bigger picture
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        pattern = np.where((((xx + yy) // stripe) % 2)[..., None] == 1, STRIPE_A, STRIPE_B).astype(np.uint8)
        for key in ("evo", "evot"):
            r = lay[key]
            ax = max(0, int((np.floor(r[0] * W) - x0) * k)); ay = max(0, int((np.floor(r[1] * H) - y0) * k))
            bx = min(a.shape[1], int(np.ceil((np.ceil((r[0] + r[2]) * W) - x0) * k)))
            by = min(a.shape[0], int(np.ceil((np.ceil((r[1] + r[3]) * H) - y0) * k)))
            if bx > ax and by > ay:
                a[ay:by, ax:bx] = pattern[ay:by, ax:bx]
        cens = Image.fromarray(a)
    return cens, full


def jpeg(img, q=86):
    b = io.BytesIO(); img.save(b, "JPEG", quality=q, optimize=True, progressive=True); return b.getvalue()


def webp(img, q=86):
    b = io.BytesIO(); img.save(b, "WEBP", quality=q, method=6); return b.getvalue()
