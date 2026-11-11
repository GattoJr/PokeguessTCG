// The site's Worker. Every file of the site is served by Cloudflare's static assets before this code runs;
// the Worker only answers what is not a file:
//   /art/<32 hex>.webp   a card picture from the R2 bucket (binding ART), by its secret name. Nothing else of the
//                        bucket is reachable: no listing, no other folder.
//   anything else        handed back to the static assets (which answer with 404.html).
const ART = /^\/art\/([0-9a-f]{32})\.webp$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const m = ART.exec(url.pathname);
    if (!m || (request.method !== "GET" && request.method !== "HEAD")) return env.ASSETS.fetch(request);

    const cache = caches.default;
    const hit = await cache.match(request);
    if (hit) return hit;

    const obj = await env.ART.get(`art/${m[1]}.webp`);
    if (!obj) {
      return new Response("not found", {
        status: 404,
        headers: { "Content-Type": "text/plain", "Cache-Control": "no-store", "Access-Control-Allow-Origin": "*" },
      });
    }
    const res = new Response(request.method === "HEAD" ? null : obj.body, {
      headers: {
        "Content-Type": "image/webp",
        "Cache-Control": "public, max-age=31536000, immutable",
        "Access-Control-Allow-Origin": "*",
        "ETag": obj.httpEtag,
      },
    });
    if (request.method === "GET") await cache.put(request, res.clone());
    return res;
  },
};
