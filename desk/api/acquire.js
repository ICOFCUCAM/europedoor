/* DISPATCH THE ACQUISITION. THE DESK DOES NOT ACQUIRE.
 *
 * The browser sends a provider, a photo id, a purpose and an alt text. This
 * turns that into one `workflow_dispatch` on `photograph.yml` with
 * `stage=acquire`, and everything after it happens in GitHub Actions, where
 * the provider key is: fetch by id, refuse anything that is not that id,
 * keep the untouched original and hash it, build the ladder without
 * upscaling, write the provenance row, run every gate, open a pull request.
 *
 * NOTHING IS PUBLISHED BY CLICKING ACQUIRE. The workflow's last act is a
 * pull request, and a pull request is a question. That boundary is the whole
 * design: the desk chooses, GitHub acquires, the register remembers, and a
 * person merges.
 *
 * IT REFUSES BEFORE IT DISPATCHES, and every refusal here is also enforced
 * inside the workflow — this is the early word, never the gate. A desk that
 * were the only thing saying no would be a gate you can reach with curl.
 */

import {
  guardPost, requireSession, send, body, registry, specOf,
  sign, register, repo, gh,
} from "./_lib.js";

export default async function handler(req, res) {
  if (!guardPost(req, res)) return;
  if (!requireSession(req, res)) return;

  const b = await body(req);
  const provider = String(b.provider || "pexels");

  const reg = registry();
  const verdict = reg.providers[provider];
  if (!verdict) { send(res, 400, { error: `${provider} is not a provider this desk knows` }); return; }
  if (!verdict.cleared) { send(res, 400, { error: "REFUSED: " + verdict.because }); return; }

  /* ONE OR MANY, THROUGH ONE SET OF REFUSALS.
   *
   * A batch is not a second route with its own idea of what a photo id is —
   * that is how two implementations of one rule end up disagreeing, which
   * this repository has recorded four times. The list below is ONE entry for
   * a single acquisition and N for a batch, and every check after this point
   * runs over every entry either way.
   *
   * IT IS STILL NOT A SELECTION. The desk sends ids a person ticked while
   * looking at the photographs; a list of ids is as incapable of choosing as
   * a single id is. `--pick 3` was wrong because a POSITION is not an
   * identity, which has nothing to do with how many identities travel
   * together. */
  const many = Array.isArray(b.batch);
  const plan = many ? b.batch : [b];
  if (!plan.length) { send(res, 400, { error: "nothing was ticked" }); return; }
  /* THE CAP WAS 30 FOR A REASON THAT MEASUREMENT DID NOT SUPPORT.
   *
   * It said "more than one sitting", which is a claim about how long the
   * work takes — and run 18 settled it: EIGHT photographs were fetched,
   * verified, hashed, derived and registered in 34 seconds, 4.25s each,
   * against 215 seconds of FIXED cost (rebuild 28s, register 5s, the static
   * gates 37s, the browser and design gates 145s). The acquisition is the
   * small half of the run and it is linear; the gates are the big half and
   * they cost the same for one photograph as for sixty. So the cap was
   * never about the workflow at all.
   *
   * WHAT IT IS ABOUT IS THE PULL REQUEST. One dispatch is one branch is one
   * PR, and a PR is a question somebody has to answer by looking at every
   * photograph in it. It is also all-or-nothing: a batch that fails on the
   * last entry rebuilds nothing and commits nothing.
   *
   * Sixty, because that is what the basket is for — the editor accumulates
   * over a whole sitting and approves in one act — and because a person who
   * has already looked at sixty photographs one at a time while building the
   * basket is not meeting them for the first time in the PR. The basket
   * itself has no cap: it holds the working set, this holds what one
   * question can carry, and a fuller basket is two sittings rather than a
   * refusal. */
  /* AND IT IS READ RATHER THAN TYPED, because for one commit it was typed
   * in four places and the four disagreed. This copy said sixty, the
   * workflow's said thirty, and the workflow's is the gate — so run 22
   * gathered sixty photographs across every family, dispatched, and died on
   * the first step of the run. `dispatch_cap` is declared once in
   * tools/desk-registry.py and generated into the registry. */
  const cap = reg.dispatch_cap;
  if (plan.length > cap) {
    send(res, 400, { error: `${plan.length} is more than one pull request `
                          + `should carry. The cap is ${cap} — the basket `
                          + `holds as many as you like, and this is what one `
                          + `question can ask. Acquire ${cap} and the rest `
                          + `stay in the basket.` });
    return;
  }

  /* SHAPE FIRST, AND THE REGISTER ONLY AFTER IT.
   *
   * The duplicate checks need the register, which is a request to GitHub —
   * and reading it before the shape is checked means a malformed id, an
   * empty alt or an invented purpose costs a network round trip before it is
   * refused. The suite caught it in the form it actually matters: "a photo
   * id that is not an identity is refused — it dispatched something", which
   * was six register reads for six malformed requests. A request this desk
   * can refuse on its own contents must reach nothing at all. */
  const clean = [];
  const seen = new Set();
  for (let i = 0; i < plan.length; i += 1) {
    const e = plan[i] || {};
    const where = many ? `entry ${i + 1}: ` : "";
    const photoId = String(e.photo_id || "").trim();
    const purpose = String(e.purpose || "").trim();
    const alt = String(e.alt || "").trim();

    /* A PHOTO ID IS AN IDENTITY, so it is checked as one. Anything else in
     * this field is a string being handed to a workflow input, and a field
     * that accepts anything is the field somebody puts a shell fragment in. */
    if (!/^[0-9]{1,20}$/.test(photoId)) {
      send(res, 400, { error: where + "a photo id is digits — that is not one" });
      return;
    }
    const spec = specOf(purpose);
    if (!spec) { send(res, 400, { error: where + `${purpose} is not a purpose` }); return; }
    if (!alt) {
      send(res, 400, { error: where + "say what the photograph shows, for "
                             + "somebody who cannot see it" });
      return;
    }
    if (alt.length > 240) { send(res, 400, { error: where + "alt text is too long" }); return; }

    /* ONE SURFACE HOLDS ONE PHOTOGRAPH, inside the batch as well as against
     * the register. Two entries naming the same purpose would have the
     * second overwrite the first inside a single run, and the PR would
     * describe whichever one landed last. */
    if (seen.has(purpose)) {
      send(res, 400, { error: `${purpose} is ticked twice. One surface holds `
                            + `one photograph.` });
      return;
    }
    seen.add(purpose);

    /* NOT TWICE INSIDE THE BATCH EITHER, and this one needs no register: a
     * sweep can offer the same photograph for two surfaces when a provider
     * returns it for two neighbouring names, and the register cannot refuse
     * that because neither row exists yet. */
    if (clean.some((x) => x.photo_id === photoId)) {
      send(res, 400, { error: `photograph ${photoId} is ticked for two `
                            + `surfaces in this batch. One photograph is not `
                            + `automatically meant for two.` });
      return;
    }
    clean.push({ purpose, photo_id: photoId, alt, key: spec.key,
                 surface: spec.surface });
  }

  /* TWO DUPLICATE REFUSALS, BECAUSE THEY ARE TWO QUESTIONS. One surface may
   * not be taken over by a second photograph, and one photograph is not
   * automatically meant for two surfaces — the second was answerable by
   * nothing at all until the register was asked from this end. */
  const rows = (await register()) || {};
  for (const e of clean) {
    if (rows[e.key]) {
      send(res, 409, { error: `${e.surface} already holds a photograph. `
                            + `Replacing one is a different act from filling `
                            + `an empty slot, and it is not this button.` });
      return;
    }
    const elsewhere = Object.entries(rows)
      .filter(([, r]) => r.provider === provider
                      && String(r.provider_photo_id) === e.photo_id)
      .map(([k, r]) => r.purpose || k);
    if (elsewhere.length) {
      send(res, 409, { error: `that photograph is already registered, for `
                            + `${elsewhere.join(", ")}. Twice is sometimes `
                            + `right and is never an accident, so it is a `
                            + `deliberate flag on acquire.py rather than a `
                            + `click here.` });
      return;
    }
  }
  for (const e of clean) { delete e.key; delete e.surface; }

  /* THE MOMENT BEFORE THE DISPATCH IS THE ONLY HANDLE ON THE RUN.
   * `workflow_dispatch` answers 204 with no body and no run id — GitHub
   * gives you nothing to hold — so the run is found afterwards by asking
   * for dispatches of this workflow created since this instant. The window
   * is signed so a caller cannot widen it and read somebody else's run. */
  const since = Date.now() - 5000;
  const { slug, branch, workflow } = repo();
  const inputs = many
    ? { stage: "batch", provider, batch: JSON.stringify(clean) }
    : { stage: "acquire", provider, purpose: clean[0].purpose,
        photo_id: clean[0].photo_id, alt: clean[0].alt, focal: "50,50" };
  const r = await gh(`/repos/${slug}/actions/workflows/${workflow}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: branch, inputs }),
  });
  if (r.status !== 204) {
    const text = await r.text();
    send(res, 502, { error: explain(r.status, text, branch, many) });
    return;
  }

  /* THE PROGRESS VIEW READS THE RUN'S OWN STEPS AND THIS RETURNS NONE.
   * A list of eight step names here would be a second copy of the workflow's
   * shape, drifting the first time somebody adds a step to `photograph.yml`
   * — and a progress panel that shows a step the run does not have is the
   * ninth thing in this repository to pin a shape rather than a promise. */
  send(res, 200, {
    job: sign({ since, batch: many, count: clean.length,
                purpose: clean[0].purpose, photo_id: clean[0].photo_id,
                exp: Date.now() + 6 * 60 * 60 * 1000 }),
    /* A BATCH'S BRANCH IS NAMED BY THE RUN, so the desk cannot state it
     * before the run exists. The status route finds the pull request by the
     * run instead, which is the honest handle either way. */
    branch: many ? "" : `photo/${clean[0].purpose}-${clean[0].photo_id}`,
    count: clean.length,
  });
}


/* A RELAYED ERROR IS NOT A DIAGNOSIS.
 *
 * The first real batch came back as GitHub's own words — `Unexpected inputs
 * provided: ["batch"]` with a documentation link — which is accurate, is
 * about a JSON field the editor never typed, and says nothing about what to
 * do. It is the failure this repository already records one level up: a
 * message with no measurement in it cannot be diagnosed.
 *
 * WHAT IT ACTUALLY MEANS IS A BRANCH. GitHub validates a dispatch's inputs
 * against the workflow file ON THE REF BEING DISPATCHED, so an input the
 * desk knows about and the target branch has never heard of is a desk that
 * is newer than the branch it is firing at. `DESK_BRANCH` decides that ref
 * and defaults to `main`.
 */
export function explain(status, text, branch, many) {
  let body = {};
  try { body = JSON.parse(text); } catch { body = {}; }
  const msg = String(body.message || text || "").slice(0, 300);

  if (status === 422 && /Unexpected inputs/i.test(msg)) {
    const named = (msg.match(/\[(.+?)\]/) || [, ""])[1]
      .replace(/[\\"']/g, "") || "an input";
    return `The workflow on branch "${branch}" does not accept ${named}, so `
         + `GitHub refused before anything ran. Nothing was acquired.\n\n`
         + `This desk dispatches to the branch named by DESK_BRANCH, which `
         + `defaults to main — and the branch it is firing at is older than `
         + `this desk. Either merge the branch carrying the acquisition `
         + `pipeline into "${branch}", or set DESK_BRANCH to that branch in `
         + `this deployment's environment variables and redeploy.`
         + (many ? `\n\nA single acquisition would fail the same way for a `
                 + `different reason: that branch's acquire.py does not know `
                 + `slot instances either.` : "");
  }
  if (status === 404) {
    return `GitHub cannot find the workflow, or the branch "${branch}", or `
         + `the token cannot see this repository. Nothing was acquired. `
         + `Check DESK_REPO, DESK_BRANCH, and that DESK_GITHUB_TOKEN has `
         + `Actions read and write on this repository.`;
  }
  if (status === 403) {
    return `GitHub refused the dispatch as unauthorised. Nothing was `
         + `acquired. DESK_GITHUB_TOKEN needs Actions: Read and write; a `
         + `fine-grained token on an organisation may also be waiting for an `
         + `owner to approve it.`;
  }
  return `GitHub refused the dispatch (${status}) on branch "${branch}". `
       + `Nothing was acquired. ${msg}`;
}
