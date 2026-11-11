"""Generate the finished game pictures of every card from the originals in R2 (source/<id>.png):
upscaled/<id>_c.webp (censored, what players see) and upscaled/<id>_f.webp (full, shown when the card is over).
The bucket is private: these names reveal the card, the game will publish them under secret names later.
Cards already done are skipped, so the workflow can be re-run. Run by the Action "Render card pictures".
Options: --shard K/N  --limit N"""
import argparse, json, os, sys, time
from pathlib import Path
import boto3, torch
from botocore.config import Config
from spandrel import ModelLoader
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_sources import playable_cards  # noqa: E402
from render_art import render, webp       # noqa: E402

BUCKET = "pokeguesstcg-art"
ap = argparse.ArgumentParser(); ap.add_argument("--shard", default="0/1"); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args(); k, n = map(int, a.shard.split("/"))
acc = os.environ["R2_ACCOUNT_ID"]
s3 = boto3.client("s3", endpoint_url=f"https://{acc}.r2.cloudflarestorage.com", region_name="auto",
                  aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"], aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                  config=Config(retries={"max_attempts": 8, "mode": "standard"}))
torch.set_num_threads(os.cpu_count() or 4)
model = ModelLoader().load_from_file("models/RealESRGAN_x4plus.pth").eval()

def keys(prefix):
    out = set()
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
        out |= {o["Key"] for o in page.get("Contents", [])}
    return out

sources, done = keys("source/"), keys("upscaled/")
cards = [c for c in playable_cards() if f"source/{c['id']}.png" in sources][k::n]
if a.limit:
    cards = cards[: a.limit]
todo = [c for c in cards if f"upscaled/{c['id']}_c.webp" not in done or f"upscaled/{c['id']}_f.webp" not in done]
print(f"shard {k}/{n}: {len(cards)} cards, {len(todo)} to do", flush=True)
t0, made, failed, nbytes = time.time(), {}, [], 0
for i, c in enumerate(todo, 1):
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=f"source/{c['id']}.png")
        src = obj["Metadata"].get("source", "pokemontcg.io")
        cens, full = render(model, obj["Body"].read(), c, src)
        for suffix, img in (("c", cens), ("f", full)):
            data = webp(img); nbytes += len(data)
            s3.put_object(Bucket=BUCKET, Key=f"upscaled/{c['id']}_{suffix}.webp", Body=data, ContentType="image/webp",
                          CacheControl="public, max-age=31536000, immutable")
        made[c["id"]] = {"source": src, "size": f"{full.width}x{full.height}"}
    except Exception as e:
        failed.append(f"{c['id']}: {str(e)[:150]}")
    if i % 20 == 0 or i == len(todo):
        el = time.time() - t0
        print(f"{i}/{len(todo)} done in {el / 60:.0f} min ({el / i:.0f} s/card), {nbytes / 1e6:.0f} MB, {len(failed)} failed", flush=True)
s3.put_object(Bucket=BUCKET, Key=f"upscaled/manifest-{k}-of-{n}.json", ContentType="application/json",
              Body=json.dumps({"cards": made, "failed": failed}).encode())
if failed:
    print(f"::warning::{len(failed)} failed (run again to retry): " + " | ".join(failed[:4]))
print(f"::notice::shard {k}: {len(made)} cards made, {nbytes / 1e6:.0f} MB, {len(failed)} failed, {(time.time() - t0) / 60:.0f} min")
