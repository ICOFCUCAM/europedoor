/* THE SLOTS, PLUS WHAT IS ACTUALLY IN THE REGISTER.
 *
 * Two halves with two lifetimes, which is why they arrive from two places.
 *
 * The SLOTS are generated: `tools/desk-registry.py` resolves every purpose
 * through `imageslots.resolve()` — the same resolver `acquire.py` uses — and
 * commits the answer, because a serverless function has no repository, no
 * Python and no atlas to resolve against. A stale copy is a failing build,
 * exactly like `site/`.
 *
 * The STATUS is live, read from `data/images.json` on the default branch. A
 * photograph acquired an hour ago has to show as filled without redeploying
 * this desk, and a status baked into a build is a status that goes stale.
 *
 * THE STATUS MACHINE IS DERIVED AND NEVER STORED. PUBLISHED means a row
 * exists on the default branch; EMPTY means one does not. A stored state is
 * a state that disagrees with the repository the moment anybody edits the
 * register by hand.
 */

import { requireSession, send, register, registry } from "./_lib.js";

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  const reg = registry();
  const byKey = (await register()) || {};

  const purposes = reg.purposes.map((p) => {
    const row = byKey[p.key] || null;
    return { ...p, status: row ? "PUBLISHED" : "EMPTY", photograph: row };
  });

  send(res, 200, {
    providers: reg.providers,
    slots: reg.slots,
    purposes,
    /* SAY WHERE THE STATUS CAME FROM. An open pull request holds a
     * photograph that has been acquired and NOT accepted, and a desk that
     * called that PUBLISHED would be reporting the reviewer's decision
     * before the reviewer made it. */
    status_source: "data/images.json on the default branch — a photograph in "
                 + "an open pull request has been acquired and not yet "
                 + "accepted, and does not count as filled here",
  });
}
