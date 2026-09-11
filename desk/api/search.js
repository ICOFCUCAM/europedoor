/* SEARCH A PROVIDER AND HAND BACK CANDIDATES. NOTHING HERE CHOOSES ONE.
 *
 * The order is the provider's own and the response says so on its face. No
 * score, no sort, no highlighted cell, no default — position is exactly what
 * `--pick 3` got wrong, and a photograph a person approved and a photograph
 * that arrived must be the same one, which is why an approval carries an ID.
 *
 * THE LICENCE GATE IS CONSULTED AND IS NOT ENFORCED HERE. `acquire.py`
 * refuses before it opens a socket, inside the workflow, where the key that
 * could fetch anything actually lives — that refusal is the one that counts.
 * This reads the generated verdict so the desk can say WHY a provider is
 * unavailable instead of offering a search that gets refused three screens
 * later. It can only ever refuse more than the gate, never less.
 */

import {
  requireSession, send, registry, specOf,
  providerSearch, normalise, fits, sign, register,
} from "./_lib.js";

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  const url = new URL(req.url, "http://desk");
  const provider = url.searchParams.get("provider") || "pexels";
  const purpose = url.searchParams.get("purpose") || "";
  const query = (url.searchParams.get("q") || "").trim();

  const reg = registry();
  const verdict = reg.providers[provider];
  if (!verdict) {
    send(res, 400, { error: `${provider} is not a provider this desk knows` });
    return;
  }
  if (!verdict.cleared) {
    send(res, 400, { error: "REFUSED: " + verdict.because });
    return;
  }

  const spec = specOf(purpose);
  if (!spec) {
    send(res, 400, { error: `${purpose} is not a purpose` });
    return;
  }
  if (!query) { send(res, 400, { error: "say what to search for" }); return; }

  const r = await providerSearch(
    provider, query, spec.orientation || "landscape", 24);
  if (r.error) { send(res, r.rateLimited ? 429 : 502, { error: r.error }); return; }

  /* §25 IN THE DIRECTION THAT WAS MISSING: the same photograph already in
   * the register, wherever it is used. The registry refuses a SURFACE being
   * taken over by a different id; this is the same question from the other
   * end, and without it the same id could be acquired twice with nothing
   * anywhere saying so. */
  const used = {};
  for (const [k, row] of Object.entries((await register()) || {})) {
    if (row.provider === provider) {
      const id = String(row.provider_photo_id);
      (used[id] = used[id] || []).push(row.purpose || k);
    }
  }

  const exp = Date.now() + 60 * 60 * 1000;
  const candidates = normalise(provider, r.payload).map((c) => {
    const bad = fits(c, spec);
    return {
      id: c.id,
      photographer: c.photographer,
      photographer_url: c.photographer_url,
      page: c.page,
      width: c.width,
      height: c.height,
      alt: c.alt,
      aspect: c.height ? Number((c.width / c.height).toFixed(3)) : 0,
      /* A SIGNED PREVIEW, not a caller-supplied address. The browser never
       * holds a provider URL and never reaches pexels.com — same as the
       * local desk, and the same reason the site ships `img-src 'self'`. */
      thumb: sign({ u: c.preview, exp }),
      suits: bad.length === 0,
      why_not: bad,
      already: used[c.id] || [],
    };
  });

  send(res, 200, {
    candidates,
    surface: spec.surface,
    needs: {
      min_width: spec.min_width,
      orientation: spec.orientation,
      min_aspect: spec.min_aspect,
      max_aspect: spec.max_aspect,
    },
    order: "the provider's own search order, carrying no judgement",
  });
}
