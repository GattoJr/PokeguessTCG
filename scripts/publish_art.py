"""Make the upscaled pictures reachable by the game, under the same secret names the game already uses.

The game knows a picture only by its secret key, art_key(card, full) in the database = md5(secret:card:variant),
so the name says nothing about the card. This copies, inside the R2 bucket,
    upscaled/<card>_c.webp  ->  art/<art_key(card, false)>.webp   (covered: evolution box hidden)
    upscaled/<card>_f.webp  ->  art/<art_key(card, true)>.webp    (whole artwork, shown once the card is over)
The site's Worker serves art/<key>.webp at /art/<key>.webp and nothing else (no listing).
Keys come from the database through the Supabase Management API; they are never printed or saved in the repo.
Pictures already copied are skipped, so it can be re-run after new cards are rendered.

Run by the GitHub Action "Publish card pictures". Needs R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
SUPABASE_ACCESS_TOKEN, SUPABASE_PROJECT_ID.
"""
import json, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

import boto3
from botocore.config import Config

BUCKET = os.environ.get("R2_BUCKET", "pokeguesstcg-art")


def keys():
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{os.environ['SUPABASE_PROJECT_ID']}/database/query",
        data=json.dumps({"query": "select id, public.art_key(id, false) as c, public.art_key(id, true) as f from public.cards"}).encode(),
        headers={"Authorization": f"Bearer {os.environ['SUPABASE_ACCESS_TOKEN']}", "Content-Type": "application/json",
                 "User-Agent": "pokeguesstcg-publish-art"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = json.loads(r.read())
    return {x["id"]: (x["c"], x["f"]) for x in rows}


def main():
    for v in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "SUPABASE_ACCESS_TOKEN", "SUPABASE_PROJECT_ID"):
        if not os.environ.get(v):
            print(f"::error::missing secret {v}")
            sys.exit(1)
    s3 = boto3.client("s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                      region_name="auto", aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                      config=Config(retries={"max_attempts": 6, "mode": "standard"}, max_pool_connections=16))

    def listing(prefix):
        out = set()
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
            out |= {o["Key"] for o in page.get("Contents", [])}
        return out

    k = keys()
    rendered, published = listing("upscaled/"), listing("art/")
    jobs, missing = [], 0
    for card, (kc, kf) in k.items():
        for src, dst in ((f"upscaled/{card}_c.webp", f"art/{kc}.webp"), (f"upscaled/{card}_f.webp", f"art/{kf}.webp")):
            if src not in rendered:
                missing += 1
            elif dst not in published:
                jobs.append((src, dst))
    print(f"{len(k)} cards in the database, {len(jobs)} pictures to copy, {missing} not rendered")

    def copy(job):
        src, dst = job
        s3.copy_object(Bucket=BUCKET, Key=dst, CopySource={"Bucket": BUCKET, "Key": src}, MetadataDirective="REPLACE",
                       ContentType="image/webp", CacheControl="public, max-age=31536000, immutable")

    failed = 0
    with ThreadPoolExecutor(16) as ex:
        for i, f in enumerate([ex.submit(copy, j) for j in jobs], 1):
            try:
                f.result()
            except Exception as e:
                failed += 1
                print("copy failed:", str(e)[:150])
            if i % 1000 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    print(f"::notice::{len(jobs) - failed} pictures published, {failed} failed, "
          f"{len(published) + len(jobs) - failed} in art/ now, {missing} pictures not rendered (old pictures used for those)")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
