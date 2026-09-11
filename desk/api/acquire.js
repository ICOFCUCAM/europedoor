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
  const photoId = String(b.photo_id || "").trim();
  const purpose = String(b.purpose || "").trim();
  const alt = String(b.alt || "").trim();

  const reg = registry();
  const verdict = reg.providers[provider];
  if (!verdict) { send(res, 400, { error: `${provider} is not a provider this desk knows` }); return; }
  if (!verdict.cleared) { send(res, 400, { error: "REFUSED: " + verdict.because }); return; }

  /* A PHOTO ID IS AN IDENTITY, so it is checked as one. Anything else in
   * this field is a string being handed to a workflow input, and a field
   * that accepts anything is the field somebody puts a shell fragment in. */
  if (!/^[0-9]{1,20}$/.test(photoId)) {
    send(res, 400, { error: "a photo id is digits — that is not one" });
    return;
  }
  const spec = specOf(purpose);
  if (!spec) { send(res, 400, { error: `${purpose} is not a purpose` }); return; }
  if (!alt) {
    send(res, 400, { error: "say what the photograph shows, for somebody who "
                          + "cannot see it" });
    return;
  }
  if (alt.length > 240) { send(res, 400, { error: "alt text is too long" }); return; }

  /* TWO DUPLICATE REFUSALS, BECAUSE THEY ARE TWO QUESTIONS. One surface may
   * not be taken over by a second photograph, and one photograph is not
   * automatically meant for two surfaces — the second was answerable by
   * nothing at all until the register was asked from this end. */
  const rows = (await register()) || {};
  if (rows[spec.key]) {
    send(res, 409, { error: `${spec.surface} already holds a photograph. `
                          + `Replacing one is a different act from filling an `
                          + `empty slot, and it is not this button.` });
    return;
  }
  const elsewhere = Object.entries(rows)
    .filter(([, r]) => r.provider === provider
                    && String(r.provider_photo_id) === photoId)
    .map(([k, r]) => r.purpose || k);
  if (elsewhere.length) {
    send(res, 409, { error: `that photograph is already registered, for `
                          + `${elsewhere.join(", ")}. Twice is sometimes right `
                          + `and is never an accident, so it is a deliberate `
                          + `flag on acquire.py rather than a click here.` });
    return;
  }

  /* THE MOMENT BEFORE THE DISPATCH IS THE ONLY HANDLE ON THE RUN.
   * `workflow_dispatch` answers 204 with no body and no run id — GitHub
   * gives you nothing to hold — so the run is found afterwards by asking
   * for dispatches of this workflow created since this instant. The window
   * is signed so a caller cannot widen it and read somebody else's run. */
  const since = Date.now() - 5000;
  const { slug, branch, workflow } = repo();
  const r = await gh(`/repos/${slug}/actions/workflows/${workflow}/dispatches`, {
    method: "POST",
    body: JSON.stringify({
      ref: branch,
      inputs: {
        stage: "acquire", provider, purpose, photo_id: photoId, alt,
        focal: "50,50",
      },
    }),
  });
  if (r.status !== 204) {
    const text = await r.text();
    send(res, 502, { error: `GitHub refused the dispatch (${r.status}). `
                          + text.slice(0, 400) });
    return;
  }

  /* THE PROGRESS VIEW READS THE RUN'S OWN STEPS AND THIS RETURNS NONE.
   * A list of eight step names here would be a second copy of the workflow's
   * shape, drifting the first time somebody adds a step to `photograph.yml`
   * — and a progress panel that shows a step the run does not have is the
   * ninth thing in this repository to pin a shape rather than a promise. */
  send(res, 200, {
    job: sign({ since, purpose, photo_id: photoId,
                exp: Date.now() + 6 * 60 * 60 * 1000 }),
    branch: `photo/${purpose}-${photoId}`,
  });
}
