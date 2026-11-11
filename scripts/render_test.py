"""Finished pictures for a few cards: today's TCGdex picture next to the new one (pokemontcg.io + AI general model)."""
import io, os, sys, urllib.request
from pathlib import Path
import boto3
from PIL import Image, ImageDraw, ImageFont
from spandrel import ModelLoader
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_sources import playable_cards  # noqa: E402
from render_art import render, jpeg, TCGDEX  # noqa: E402

IDS = ["sv10-088", "me05-041", "swsh1-76", "sv06.5-024", "30th-061"]
OUT = Path("out/render"); OUT.mkdir(parents=True, exist_ok=True)
acc = os.environ["R2_ACCOUNT_ID"]
s3 = boto3.client("s3", endpoint_url=f"https://{acc}.r2.cloudflarestorage.com", region_name="auto",
                  aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"], aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
model = ModelLoader().load_from_file("models/RealESRGAN_x4plus.pth").eval()
cards = {c["id"]: c for c in playable_cards()}
font = ImageFont.load_default(size=30)
for cid in IDS:
    c = cards[cid]
    png = s3.get_object(Bucket="pokeguesstcg-art", Key=f"source/{cid}.png")["Body"].read()
    cens, full = render(model, png, c, "pokemontcg.io")
    (OUT / f"{cid}_censored.jpg").write_bytes(jpeg(cens)); (OUT / f"{cid}_full.jpg").write_bytes(jpeg(full))
    # today's picture: TCGdex, old layout, 500 px, enlarged by the browser
    old = urllib.request.urlopen(urllib.request.Request(c["tcgdex"], headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
    tcens, _ = render(None, old, c, "tcgdex", out_w=round(Image.open(io.BytesIO(old)).width * 0.836))
    tcens = tcens.resize(cens.size, Image.BICUBIC)
    lab = 50; sheet = Image.new("RGB", (cens.width, (cens.height + lab) * 2), (19, 32, 61)); d = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate([("Today: TCGdex", tcens), ("New: pokemontcg.io + AI general", cens)]):
        d.text((14, i * (cens.height + lab) + 10), f"{t}  ·  {cid} {c['name']}", fill=(255, 214, 0), font=font)
        sheet.paste(im, (0, i * (cens.height + lab) + lab))
    sheet.save(OUT / f"{cid}_compare.jpg", quality=90)
    print(cid, c["name"], f"censored {len(jpeg(cens)) // 1024} KB, full {len(jpeg(full)) // 1024} KB, {cens.size}", flush=True)
