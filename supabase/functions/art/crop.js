// Cut the artwork window out of a card picture and paint over the parts that would give the card away
// (pre-evolution picture, "Evolves from ..." text, Mega box). Shared by the edge function and the tests.

const STRIPE_A = [0x2a, 0x3b, 0x60], STRIPE_B = [0x22, 0x31, 0x4f];   // same colours as the old in-page covers

/** Rectangles are fractions of the card: [left, top, width, height]. */
export function censorsFor(card, layout) {
  const out = [];
  if (card.has_evo) out.push(layout.evo, layout.evot);
  if (/^Mega /.test(card.name || '')) out.push(layout.mega);
  return out.filter((r) => r && r[2] > 0 && r[3] > 0);
}

/**
 * @param Image   ImageScript's Image class (passed in so Deno and Node can each import their own)
 * @param bytes   the card picture (PNG or JPEG)
 * @param crop    artwork window [left, top, width, height], fractions of the card
 * @param covers  rectangles to paint over, fractions of the card
 * @returns JPEG bytes of the artwork window only
 */
export async function renderArt(Image, bytes, crop, covers) {
  const img = await Image.decode(bytes);
  const W = img.width, H = img.height;
  const x0 = Math.round(crop[0] * W), y0 = Math.round(crop[1] * H);
  const w = Math.min(W - x0, Math.round(crop[2] * W)), h = Math.min(H - y0, Math.round(crop[3] * H));
  img.crop(x0, y0, w, h);
  const px = img.bitmap;   // RGBA, row by row
  for (const r of covers) {
    const ax = Math.max(0, Math.floor(r[0] * W) - x0), ay = Math.max(0, Math.floor(r[1] * H) - y0);
    const bx = Math.min(w, Math.ceil((r[0] + r[2]) * W) - x0), by = Math.min(h, Math.ceil((r[1] + r[3]) * H) - y0);
    for (let y = ay; y < by; y++) {
      for (let x = ax; x < bx; x++) {
        const c = Math.floor((x + y) / 7) % 2 ? STRIPE_A : STRIPE_B, i = (y * w + x) * 4;
        px[i] = c[0]; px[i + 1] = c[1]; px[i + 2] = c[2]; px[i + 3] = 255;
      }
    }
  }
  return await img.encodeJPEG(86);
}
