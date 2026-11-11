"""Per-set check of the pokemontcg.io pictures: picture size of every stored card (from R2 metadata) and the
artwork window measured on one Basic and one evolved card of each set. Shows which sets differ from their series."""
import io, json, os, sys, statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import boto3, cv2, numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_sources import playable_cards  # noqa: E402
import time, urllib.request
TCGDEX = {"sv": {"crop": [0.087, 0.105, 0.836, 0.360]}, "me": {"crop": [0.087, 0.105, 0.836, 0.360]},
          "swsh": {"crop": [0.087, 0.105, 0.836, 0.362]}}
def get(url):
    for i in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")

OUT = Path("out/measure"); OUT.mkdir(parents=True, exist_ok=True)
acc = os.environ["R2_ACCOUNT_ID"]
s3 = boto3.client("s3", endpoint_url=f"https://{acc}.r2.cloudflarestorage.com", region_name="auto",
                  aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"], aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
cards = playable_cards()
def head(c):
    try:
        m = s3.head_object(Bucket="pokeguesstcg-art", Key=f"source/{c['id']}.png")["Metadata"]
        return c, m.get("size"), m.get("source")
    except Exception:
        return c, None, None
sizes = defaultdict(Counter)
with ThreadPoolExecutor(16) as ex:
    for c, size, src in ex.map(head, cards):
        sizes[c["set_id"]][f"{size} {src}"] += 1
log = []
def say(s=""): print(s, flush=True); log.append(s)
say("PICTURE SIZES PER SET")
for sid in sorted(sizes, key=lambda s: next(c["set_date"] for c in cards if c["set_id"] == s)):
    say(f"  {sid:10s} " + ", ".join(f"{k}: {v}" for k, v in sizes[sid].most_common()))

say(""); say("ARTWORK WINDOW PER SET (pokemontcg.io fractions)")
bysets = defaultdict(list)
for c in cards:
    if c["ptcg"]: bysets[c["set_id"]].append(c)
rows = {}
for sid, cs in bysets.items():
    serie = cs[0]["serie"]; boxes = TCGDEX[serie]
    pick = [c for c in cs if not c["has_evo"]][:1] + [c for c in cs if c["has_evo"]][:1]
    for c in pick:
        t = Image.open(io.BytesIO(get(c["tcgdex"]))).convert("RGB"); p = Image.open(io.BytesIO(get(c["ptcg"]))).convert("RGB")
        W, H = t.size; PW, PH = p.size; cr = boxes["crop"]
        x0, y0, w, h = round(cr[0] * W), round(cr[1] * H), round(cr[2] * W), round(cr[3] * H)
        tm0 = cv2.cvtColor(np.asarray(t.crop((x0, y0, x0 + w, y0 + h))), cv2.COLOR_RGB2GRAY)
        pg = cv2.cvtColor(np.asarray(p), cv2.COLOR_RGB2GRAY); best = None
        for s in np.arange(PW / W - 0.08, PW / W + 0.06, 0.002):
            tm = cv2.resize(tm0, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
            if tm.shape[0] >= pg.shape[0] or tm.shape[1] >= pg.shape[1]: continue
            r = cv2.matchTemplate(pg, tm, cv2.TM_CCOEFF_NORMED); _, v, _, loc = cv2.minMaxLoc(r)
            if not best or v > best[0]: best = (v, s, loc)
        v, s, (px, py) = best
        crop = [px / PW, py / PH, w * s / PW, h * s / PH]
        rows.setdefault(sid, []).append((serie, c["id"], PW, PH, v, crop))
for sid, rs in rows.items():
    for serie, cid, PW, PH, v, crop in rs:
        say(f"  {sid:10s} {serie:5s} {cid:14s} {PW}x{PH} match {v:.3f} crop [{', '.join(f'{x:.4f}' for x in crop)}]")
(OUT / "sets_report.txt").write_text("\n".join(log) + "\n")
(OUT / "sets.json").write_text(json.dumps({sid: [list(r[1:]) for r in rs] for sid, rs in rows.items()}, indent=0))
