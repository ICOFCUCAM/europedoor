/* ONE COUNTRY, ONE SLOT, A PHOTOGRAPH OFFERED FOR EVERY EMPTY SURFACE.
 *
 * Filling a country one destination at a time is thirteen searches, thirteen
 * dialogues and thirteen pull requests for what is one editorial sitting. This
 * runs the search per surface and hands back a grid.
 *
 * IT PROPOSES AND IT DOES NOT CHOOSE, AND THE DIFFERENCE IS WHAT THE EDITOR
 * CAN SEE. `--pick 3` was wrong because a POSITION is not an identity: the
 * photograph a person approved and the photograph that arrived could differ
 * silently while every provenance field was correct about the wrong one. That
 * cannot happen here — every tile carries its own id, the tile shows the
 * photograph, and the id on the tile is the id dispatched. What a person
 * approves is what they looked at.
 *
 * So this returns the provider's own first qualifying result per surface, says
 * so on its face, and ticks nothing. The editor sees the pictures, unticks
 * what is wrong, and acquires the rest. A tile nobody looked at is a tile
 * nobody ticked.
 *
 * THE QUERY IS THE SURFACE'S OWN SUBJECT, never typed per row. A destination
 * hero for Bergen searches for Bergen, Norway — derived from the atlas the
 * registry was generated from, so thirteen queries are one decision rather
 * than thirteen.
 *
 * AND IT IS CAPPED AND SERIAL. Twelve searches is twelve requests against a
 * rate limit nobody here owns, so the cap is small, the requests run one
 * after another, and a 429 stops the sweep and says how far it got —
 * retrying into a limit is how a key gets revoked.
 */

import {
  requireSession, send, registry, specOf,
  providerSearch, normalise, fits, sign, register,
} from "./_lib.js";

export const MAX_SURFACES = 24;

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  const url = new URL(req.url, "http://desk");
  const provider = url.searchParams.get("provider") || "pexels";
  const slot = url.searchParams.get("slot") || "";
  const country = url.searchParams.get("country") || "";

  const reg = registry();
  const verdict = reg.providers[provider];
  if (!verdict) { send(res, 400, { error: `${provider} is not a provider this desk knows` }); return; }
  if (!verdict.cleared) { send(res, 400, { error: "REFUSED: " + verdict.because }); return; }
  if (!reg.slots[slot]) { send(res, 400, { error: `${slot} is not a slot` }); return; }
  if (!country) { send(res, 400, { error: "choose a country" }); return; }

  const held = (await register()) || {};
  const used = {};
  for (const [k, row] of Object.entries(held)) {
    if (row.provider === provider) {
      const id = String(row.provider_photo_id);
      (used[id] = used[id] || []).push(row.purpose || k);
    }
  }

  /* THE SURFACES THAT ARE EMPTY, and only those. A sweep that re-offered a
   * filled surface would be proposing to replace a photograph somebody
   * already approved, which is a different act and is not this button. */
  const surfaces = reg.purposes.filter(
    (p) => p.slot === slot && p.country === country && !held[p.key]);
  if (!surfaces.length) {
    send(res, 200, {
      rows: [], note: "Every surface of this kind in this country already "
                    + "holds a photograph. Replacing one is a different act "
                    + "from filling an empty slot, and it is not this button.",
    });
    return;
  }

  const spec0 = specOf(surfaces[0].purpose);
  const exp = Date.now() + 60 * 60 * 1000;
  const rows = [];
  let stopped = "";

  for (const p of surfaces.slice(0, MAX_SURFACES)) {
    const spec = specOf(p.purpose);
    const r = await providerSearch(provider, queryFor(p), spec.orientation || "landscape", 8);
    if (r.error) {
      /* A SWEEP THAT STOPS SAYS HOW FAR IT GOT. Silently returning the rows
       * it managed would look like a complete answer about the country. */
      stopped = r.error + ` The sweep stopped after ${rows.length} of `
              + `${surfaces.length} surfaces; nothing was acquired.`;
      break;
    }
    const cands = normalise(provider, r.payload)
      .map((c) => ({ c, bad: fits(c, spec) }))
      .filter((x) => x.bad.length === 0)
      .filter((x) => !used[x.c.id]);
    const pick = cands[0];
    rows.push({
      purpose: p.purpose,
      surface: p.surface,
      target: p.target,
      query: queryFor(p),
      /* A SURFACE WITH NO QUALIFYING CANDIDATE IS NAMED, NEVER DROPPED. A
       * grid that silently omits four of thirteen destinations reads as a
       * complete answer about the country and is not one. */
      candidate: pick ? {
        id: pick.c.id,
        photographer: pick.c.photographer,
        photographer_url: pick.c.photographer_url,
        page: pick.c.page,
        width: pick.c.width,
        height: pick.c.height,
        alt: pick.c.alt,
        thumb: sign({ u: pick.c.preview, exp }),
        alternatives: cands.length - 1,
      } : null,
      why_none: pick ? "" : "nothing in this provider's first page of results "
                          + "for this name meets the slot",
    });
  }

  send(res, 200, {
    rows,
    stopped,
    surfaces: surfaces.length,
    swept: rows.length,
    needs: {
      min_width: spec0.min_width, orientation: spec0.orientation,
      min_aspect: spec0.min_aspect, max_aspect: spec0.max_aspect,
    },
    order: "each row is the provider's own first result for that surface's "
         + "own name that meets the slot. Nothing is ranked and nothing is "
         + "ticked: what you approve is what you can see.",
  });
}

/* The subject of the surface, in the words the atlas uses for it. The
 * registry's `surface` sentence already names the entity — "The opening image
 * of the Bergen, Norway destination page" — so the name is read out of that
 * rather than reconstructed from a slug, which would give "alps and east". */
export function queryFor(p) {
  const m = /of the (.+?) (?:destination|place) page/.exec(p.surface || "");
  if (m) return m[1];
  const m2 = /of the story “(.+?)”/.exec(p.surface || "");
  if (m2) return m2[1];
  return (p.target || "").split("/").pop().replace(/-/g, " ");
}
