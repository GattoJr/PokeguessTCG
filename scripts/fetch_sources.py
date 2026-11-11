"""Download the original picture of every playable card into the R2 bucket, once.

Source: pokemontcg.io (734x1024, sharper), found through its data repository (PokemonTCG/pokemon-tcg-data,
cloned to ./ptcg-data by the workflow); TCGdex high.png (600x825) for the few cards pokemontcg.io lacks.
Each picture goes to  source/<card id>.png  (card id = "<TCGdex set>-<number>", as in the database), plus
source/manifest.json with where each card came from. Cards already in the bucket are skipped, so the
workflow can be re-run safely after an error.

Run by the GitHub Action "Fetch card pictures". Needs R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY.
Options:  --limit N  (first N cards only, for a test)   --shard K/N  (only every N-th card from K, for parallel jobs)
"""
import argparse, io, json, os, re, sys, time, unicodedata, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_game_data import ERAS, FULL_ART, FULL_ART_NAME, ROOT  # noqa: E402

BUCKET = os.environ.get("R2_BUCKET", "pokeguesstcg-art")
DATA = Path("ptcg-data")
UA = {"User-Agent": "Mozilla/5.0 (pokeguesstcg picture fetch)"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())


def num(n):
    return n.lstrip("0") or "0"


def get(url):
    err = None
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:  # network hiccups and 5xx: wait and retry
            err = e
            if getattr(e, "code", None) == 404:
                break
            time.sleep(4 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def playable_cards():
    db = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
    base = db.get("imageBase", "https://assets.tcgdex.net/en")
    psets = {norm(s["name"]): s for s in json.loads((DATA / "sets/en.json").read_text())}
    pcards = {}
    out = []
    for c in db["cards"]:
        st = db["sets"][c[0]]
        serie = db["series"][st[2]][0]
        rarity = db["rarities"][c[3]] if c[3] is not None and c[3] < len(db["rarities"]) else None
        if serie not in ERAS or (rarity and FULL_ART.match(rarity)) or FULL_ART_NAME.search(c[2]):
            continue
        ps = psets.get(norm(st[1]))
        hires = None
        if ps:
            if ps["id"] not in pcards:
                f = DATA / "cards/en" / f"{ps['id']}.json"
                pcards[ps["id"]] = {num(x["number"]): x for x in json.loads(f.read_text())} if f.exists() else {}
            hit = pcards[ps["id"]].get(num(c[1]))
            if hit and norm(hit["name"]) == norm(c[2]):  # same number AND same name, or it is not the same card
                hires = hit["images"].get("large")  # the _hires.png picture
        out.append({"id": f"{st[0]}-{c[1]}", "serie": serie, "name": c[2],
                    "ptcg": hires, "tcgdex": f"{base}/{serie}/{st[0]}/{c[1]}/high.png"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--dry-run", action="store_true", help="only report which source each card would use")
    a = ap.parse_args()
    k, n = map(int, a.shard.split("/"))

    if a.dry_run:
        cards = playable_cards()
        miss = [c for c in cards if not c["ptcg"]]
        print(f"::notice::{len(cards)} playable cards: {len(cards) - len(miss)} from pokemontcg.io, {len(miss)} from TCGdex")
        for c in miss:
            print(f"   TCGdex: {c['id']} {c['name']}")
        return

    acc = os.environ.get("R2_ACCOUNT_ID", "")
    if not (acc and os.environ.get("R2_ACCESS_KEY_ID") and os.environ.get("R2_SECRET_ACCESS_KEY")):
        print("::error::R2 secrets are missing: set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in the repository.")
        sys.exit(1)
    s3 = boto3.client("s3", endpoint_url=f"https://{acc}.r2.cloudflarestorage.com", region_name="auto",
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                      config=Config(retries={"max_attempts": 6, "mode": "standard"}))

    cards = playable_cards()
    print(f"{len(cards)} playable cards; {sum(1 for c in cards if c['ptcg'])} on pokemontcg.io")
    todo = cards[k::n]
    if a.limit:
        todo = todo[: a.limit]
    have = set()
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix="source/"):
        have |= {o["Key"] for o in page.get("Contents", [])}

    def one(c):
        key = f"source/{c['id']}.png"
        if key in have:
            return c["id"], "skip", None, 0
        src, data = None, None
        if c["ptcg"]:
            try:
                data, src = get(c["ptcg"]), "pokemontcg.io"
            except Exception as e:
                print(f"   {c['id']}: pokemontcg.io failed ({e}), using TCGdex")
        if data is None:
            data, src = get(c["tcgdex"]), "tcgdex"
        w, h = Image.open(io.BytesIO(data)).size  # also checks it is a real picture
        s3.put_object(Bucket=BUCKET, Key=key, Body=data, ContentType="image/png",
                      Metadata={"source": src, "size": f"{w}x{h}"})
        return c["id"], src, f"{w}x{h}", len(data)

    done, failed, total_bytes = {}, [], 0
    with ThreadPoolExecutor(6) as ex:
        for i, f in enumerate([ex.submit(one, c) for c in todo], 1):
            try:
                cid, src, size, nb = f.result()
                done[cid] = {"source": src, "size": size}
                total_bytes += nb
            except Exception as e:
                failed.append(str(e)[:200])
            if i % 200 == 0 or i == len(todo):
                print(f"{i}/{len(todo)} done, {total_bytes / 1e6:.0f} MB uploaded, {len(failed)} failed", flush=True)

    counts = {}
    for v in done.values():
        counts[v["source"]] = counts.get(v["source"], 0) + 1
    print("by source:", counts)
    s3.put_object(Bucket=BUCKET, Key=f"source/manifest-{k}-of-{n}.json", ContentType="application/json",
                  Body=json.dumps({"cards": done, "failed": failed}, indent=0).encode())
    if failed:
        print(f"::warning::{len(failed)} cards failed (run again to retry them): " + " | ".join(failed[:5]))
    print(f"::notice::{len(done)} cards processed ({counts}), {total_bytes / 1e6:.0f} MB uploaded, {len(failed)} failed")


if __name__ == "__main__":
    main()
