// Artwork of a card, cropped to the artwork window, with the giveaway parts covered.
// The browser normally loads pictures straight from the public bucket "art" (fast, through Supabase's CDN),
// under a secret name returned by the game functions. This function is called only when a picture is not
// there yet: it builds it, saves it in the bucket, and returns it.
//
// GET /functions/v1/art?round=<round id>        covered artwork of the card being played
// GET /functions/v1/art?round=<id>&full=1       uncovered artwork, only once the round is over
// GET /functions/v1/art?run=<run id>&idx=<0-9>  covered artwork of a Guess10 card (to get the next one ready)
// GET /functions/v1/art?card=<card id>          covered artwork for the admin panel (admin sign-in required)
// The answer never contains the card's name, number or TCGdex address.
// Deployed with --no-verify-jwt so a plain <img src> works; access is checked here.
import { createClient } from "npm:@supabase/supabase-js@2";
import { Image } from "npm:imagescript@3.3.0";
import { censorsFor, renderArt } from "./crop.js";

const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});
const BUCKET = "art";   // public; file names are unguessable (see art_key in the database)
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function fail(status: number, msg: string) {
  return new Response(msg, { status, headers: { ...CORS, "Content-Type": "text/plain", "Cache-Control": "no-store" } });
}

async function isAdmin(req: Request) {
  const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!token) return false;
  const { data } = await db.auth.getUser(token);
  if (!data?.user) return false;
  const { data: row } = await db.from("admins").select("user_id").eq("user_id", data.user.id).maybeSingle();
  return !!row;
}

// TCGdex serves each card as PNG and JPEG (and WebP, which ImageScript cannot read): try them in turn
async function buildArt(base: string, crop: number[], covers: number[][]) {
  let last: unknown = null;
  for (const ext of ["high.png", "high.jpg"]) {
    try {
      const r = await fetch(`${base}/${ext}`);
      if (!r.ok) { last = new Error(`${ext}: HTTP ${r.status}`); continue; }
      return await renderArt(Image, new Uint8Array(await r.arrayBuffer()), crop, covers);
    } catch (e) { last = e; }
  }
  throw last ?? new Error("no picture on TCGdex");
}

async function cached(path: string) {
  const { data } = await db.storage.from(BUCKET).download(path);
  return data ? new Uint8Array(await data.arrayBuffer()) : null;
}

async function store(path: string, bytes: Uint8Array) {
  const opts = { contentType: "image/jpeg", upsert: true, cacheControl: "31536000" };
  let { error } = await db.storage.from(BUCKET).upload(path, bytes, opts);
  if (error && /not found/i.test(error.message)) {
    await db.storage.createBucket(BUCKET, { public: true });
    ({ error } = await db.storage.from(BUCKET).upload(path, bytes, opts));
  }
  if (error) console.error("cache upload failed", error.message);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "GET") return fail(405, "GET only");
  const q = new URL(req.url).searchParams;
  const round = q.get("round"), run = q.get("run"), cardParam = q.get("card"), full = q.get("full") === "1";
  let cardId: string | null = null, forAdmin = false;
  try {
    if (round) {
      if (!UUID.test(round)) return fail(400, "bad round");
      const { data } = await db.from("rounds").select("card_id, over").eq("id", round).maybeSingle();
      if (data && full && !data.over) return fail(403, "the card is still in play");
      cardId = data?.card_id ?? null;
    } else if (run) {
      const idx = Number(q.get("idx"));
      if (!UUID.test(run) || !Number.isInteger(idx) || idx < 0 || idx > 9 || full) return fail(400, "bad request");
      const { data } = await db.from("runs").select("cards").eq("id", run).maybeSingle();
      cardId = data?.cards?.[idx] ?? null;
    } else if (cardParam) {
      if (!(await isAdmin(req))) return fail(403, "not allowed");
      cardId = cardParam;
      forAdmin = true;
    }
    if (!cardId) return fail(404, "not found");

    const { data: card } = await db.from("cards").select("id, serie, image, has_evo, name").eq("id", cardId).maybeSingle();
    if (!card) return fail(404, "not found");
    const { data: key, error: keyErr } = await db.rpc("art_key", { p_card: card.id, p_full: full });
    if (keyErr || !key) throw keyErr ?? new Error("no art key");
    const path = `${key}.jpg`;

    let jpg: Uint8Array | null = await cached(path);
    if (!jpg) {
      const { data: layout } = await db.from("layouts").select("crop, evo, evot, mega").eq("serie", card.serie).maybeSingle();
      if (!layout) return fail(500, "no layout for this series");
      const fresh: Uint8Array = await buildArt(card.image, layout.crop, full ? [] : censorsFor(card, layout));
      await store(path, fresh);
      jpg = fresh;
    }
    return new Response(new Uint8Array(jpg), {
      headers: {
        ...CORS,
        "Content-Type": "image/jpeg",
        // a round always shows the same card, so the browser may keep it; the admin preview is never kept
        "Cache-Control": forAdmin ? "no-store" : "public, max-age=604800, immutable",
      },
    });
  } catch (e) {
    console.error(e);
    return fail(502, "could not prepare the picture");
  }
});
