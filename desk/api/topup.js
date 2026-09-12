/* FILL THE LIBRARY: ONE PRESS, EVERY CATEGORY, THE NEXT TRANCHE.
 *
 * The desk had two ways in and both asked the editor to decide WHERE first:
 * find one photograph for one surface, or sweep one slot in one country. With
 * 837 purposes and a library that starts empty, that is a lot of deciding
 * before any picture arrives — and the decision it asks for is the one an
 * editor has least appetite for, because "which of the 826 empty surfaces
 * next" is not an editorial question at all.
 *
 * So this asks it once, for them: every empty surface, in an order that gives
 * a bit of everything, as far as one sitting reaches. Press it again and it
 * takes the next tranche. Nothing about the other two paths changes; this is
 * a third door into the same machinery.
 *
 * ROUND-ROBIN ACROSS SLOTS, WHICH IS THE WHOLE POINT OF THE ORDER. Taken in
 * registry order a single press would be sixty Austrian destinations, which
 * is a complete answer about Austria and no answer about the product. One
 * from each slot in turn means a press touches themes, countries, journeys,
 * interests, macro regions, categories, stories, regions, destinations and
 * places — so the library fills EVENLY and every family gets its first
 * photograph early, which is when a photograph is worth the most.
 *
 * THE QUERY IS THE ROLE'S OWN FIRST CONCEPT, not the bare name. The sweep
 * searches for "Austria" because a person is about to look at the grid and
 * judge; nothing looks here, so the query has to carry more of the intent.
 * `country-hero` declares `{name} landscape` and `destination-hero` declares
 * `{name}` — the difference between those two is exactly the editorial
 * knowledge the roles were written to hold, and it costs nothing to spend it.
 *
 * IT REQUIRES THE PHOTOGRAPHER'S OWN DESCRIPTION AND SKIPS A CANDIDATE
 * WITHOUT ONE. Every acquisition needs an alt, and the alternative to a real
 * one is writing a description of a photograph nothing here has seen — which
 * is the licence-from-memory failure in another costume, and this repository
 * refuses it everywhere else. A candidate with no `alt` is not unusable; it
 * is un-AUTOMATABLE, which is a different thing, and it stays available to
 * the two paths where a person is looking.
 *
 * AND IT IS TIME-BUDGETED, NOT ONLY CAPPED. One surface is one request
 * against a rate limit nobody here owns, run serially, so sixty of them can
 * outlast the function. The budget returns whatever it has with an honest
 * count rather than dying at a gateway and reporting nothing — the same
 * reason the sweep says how far it got.
 */

import {
  requireSession, send, registry, specOf,
  providerSearch, normalise, fits, sign, register, sessionExpiry,
} from "./_lib.js";
import { queryFor } from "./sweep.js";

/* THE DISPATCH'S OWN CAP, READ RATHER THAN RESTATED. A restated number is
 * a number that drifts: this one was typed here, in acquire.js, in desk.js
 * and in the workflow, and when three were raised to sixty the fourth — the
 * only one that is a gate — stayed at thirty. It is declared once in
 * tools/desk-registry.py and generated into desk/registry.json. */
export function maxFill() { return registry().dispatch_cap; }

/* Serial provider requests, and a function that does not get to run for
 * ever. Twenty seconds leaves room for the register read and the response
 * inside a sixty-second ceiling. */
export const BUDGET_MS = 20000;

/* AND A CEILING ON HOW MANY SURFACES IT LOOKS AT, which is not the same
 * number as how many it takes.
 *
 * The first version bounded only the TAKE. A surface whose search returns
 * nothing qualifying costs a request and yields no row, so on a provider
 * having a bad day the loop walked all 837 empty surfaces making 837
 * requests against a rate limit nobody here owns — the exact thing
 * `MAX_SURFACES` exists for one file over, dropped by writing the cap on the
 * wrong quantity. Found because a TEST could not tell round-robin from
 * registry order: both cover every family once you have looked at all of
 * them, and that only happens if the looking is unbounded. TWICE THE FILL,
 * derived rather than typed, because taking sixty means expecting to reject
 * some — and a ceiling written as a number stops being twice the fill the
 * day the fill moves, which is exactly how the cap itself went wrong. */
export function maxLooks() { return 2 * maxFill(); }

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  const url = new URL(req.url, "http://desk");
  const provider = url.searchParams.get("provider") || "pexels";
  const reg = registry();
  const cap = reg.dispatch_cap;
  const looks = 2 * cap;
  const want = Math.min(Number(url.searchParams.get("n")) || cap, cap);

  const verdict = reg.providers[provider];
  if (!verdict) { send(res, 400, { error: `${provider} is not a provider this desk knows` }); return; }
  if (!verdict.cleared) { send(res, 400, { error: "REFUSED: " + verdict.because }); return; }

  const held = (await register()) || {};
  const used = {};
  for (const [k, row] of Object.entries(held)) {
    if (row.provider === provider) {
      const id = String(row.provider_photo_id);
      (used[id] = used[id] || []).push(row.purpose || k);
    }
  }

  /* EMPTY SURFACES ONLY. Re-offering a filled one is proposing to replace a
   * photograph somebody accepted, which is a different act and not this
   * button — the same sentence the sweep already holds. */
  const empty = reg.purposes.filter((p) => !held[p.key]);

  const order = interleave(empty);

  if (!order.length) {
    send(res, 200, {
      rows: [], empty: 0, looked: 0,
      note: "Every surface this product declares already holds a "
          + "photograph. There is nothing left for this button to fill.",
    });
    return;
  }

  const exp = sessionExpiry(req);
  const started = Date.now();
  const rows = [];
  /* THE FAMILIES THIS PRESS ACTUALLY TOUCHED, reported rather than implied.
   * The round-robin is the whole point of the button, and a test that only
   * read the ordering function could not tell whether the route still called
   * it — replacing `interleave(empty)` with `empty` left the suite green.
   * The response carries the answer now, so the promise is observable from
   * outside, and the band can say it. */
  const covered = new Set();
  let looked = 0;
  let stopped = "";

  for (const p of order) {
    if (rows.length >= want) break;
    if (looked >= looks) {
      stopped = `It looked at ${looked} of the ${order.length} empty `
              + `surfaces and found ${rows.length}. Press it again for the `
              + `next tranche.`;
      break;
    }
    if (Date.now() - started > BUDGET_MS) {
      stopped = `This sitting reached ${rows.length} of the ${order.length} `
              + `empty surfaces before its time ran out. Press it again for `
              + `the next tranche.`;
      break;
    }
    looked += 1;
    covered.add(p.slot || p.purpose);
    const spec = specOf(p.purpose);
    const r = await providerSearch(
      provider, queryOf(p, spec), spec.orientation || "landscape", 12);
    if (r.error) {
      stopped = r.error + ` It reached ${rows.length} of ${order.length} `
              + `empty surfaces; nothing was acquired.`;
      break;
    }
    const pick = normalise(provider, r.payload)
      .filter((c) => fits(c, spec).length === 0)
      .filter((c) => !used[c.id])
      /* A DESCRIPTION FROM THE PHOTOGRAPHER, or this one is not automatable.
       * Writing one here would be describing a photograph nothing has
       * looked at. */
      .filter((c) => String(c.alt || "").trim().length > 0)[0];
    if (!pick) continue;
    /* AND NOT TWICE IN ONE PRESS. The provider can return the same
     * photograph for two neighbouring queries, and the register refuses one
     * id against two purposes — so a set this button gathers must not
     * contain a pair the dispatch will reject. */
    used[pick.id] = [p.purpose];
    rows.push({
      purpose: p.purpose,
      surface: p.surface,
      target: p.target,
      query: queryOf(p, spec),
      candidate: {
        id: pick.id,
        photographer: pick.photographer,
        photographer_url: pick.photographer_url,
        page: pick.page,
        width: pick.width,
        height: pick.height,
        alt: pick.alt,
        thumb: sign({ u: pick.preview, exp }),
      },
    });
  }

  send(res, 200, {
    rows,
    stopped,
    empty: order.length,
    looked,
    covered: [...covered].sort(),
    cap,
    order: "one surface from each family in turn, so a press fills every "
         + "category rather than one country. Each row is the provider's own "
         + "first result for that surface's role-written query that meets the "
         + "slot, is not already registered, and carries the photographer's "
         + "own description. Nothing is ranked: there is no order of merit "
         + "here, only an order of results.",
  });
}

/* THE ROLE'S FIRST CONCEPT WITH THE SURFACE'S NAME IN IT.
 *
 * `queryFor` reads the entity's name out of the surface sentence, which is
 * where the atlas writes it. The concept is what turns that name into a
 * subject: a country wants `{name} landscape` and a destination wants
 * `{name}`, and that difference is the editorial knowledge the roles exist
 * to hold. Where a slot declares none, the name alone is the fallback and is
 * exactly what the sweep already sends.
 */
export function queryOf(p, spec) {
  const name = queryFor(p);
  const concept = (spec && spec.search && spec.search[0]) || "";
  return concept ? concept.replace(/\{name\}/g, name) : name;
}


/* ONE QUEUE PER FAMILY, THEN TAKEN IN TURN.
 *
 * A declared purpose — the homepage hero, the four doors — has no slot and is
 * its own family, which puts each of them early rather than behind 255
 * places.
 *
 * IT IS A FUNCTION BECAUSE A TEST COULD NOT REACH IT OTHERWISE. Written
 * inline, the only assertion available was "the route made at least ten
 * searches", which is true of registry order as well — so replacing the
 * round-robin with `const order = empty` left the suite green. A test that
 * still passes with the guard deleted is not a test of the guard, and this
 * repository has recorded that exact sentence about five other assertions.
 */
export function interleave(rows) {
  const lanes = new Map();
  for (const p of rows) {
    const lane = p.slot || p.purpose;
    if (!lanes.has(lane)) lanes.set(lane, []);
    lanes.get(lane).push(p);
  }
  const out = [];
  const queues = [...lanes.values()];
  for (let i = 0; queues.some((q) => i < q.length); i += 1) {
    for (const q of queues) if (i < q.length) out.push(q[i]);
  }
  return out;
}
