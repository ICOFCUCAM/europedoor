# Gap assessment — what is built, what is missing, and what is blocked

**Written after a full design pass, from the site's own instruments rather
than from opinion.** Every number here is produced by a command in the gate
list and can be re-derived; nothing in it is an estimate.

The short version: the engineering is finished and the content is a third
written. Almost every remaining gap is one of two things — **a photograph
nobody has licensed** or **a page nobody has written** — and neither is
solvable by more code.

---

## 1. What is built and holds

Seven suites, all green, run on every commit:

| suite | what it holds |
|---|---|
| `checks.py` | 72 static checks, ~128,000 things examined |
| `browser-checks.js` | 905 assertions in Chromium, including contrast and target size |
| `section-audit.py` | 1,366 assertions against the two specifications |
| `ux-audit.py` | 374 assertions against the design brief and the Brand Bible |
| `invariants.py` | 28 things a visual change may not move silently |
| `plate-variation.py` | 7 motif families, none more alike than recorded |
| `photo-tests.py` | 74 checks on the acquisition pipeline, against a stub provider |

One page shell. One stylesheet. Eleven primitives. Zero webfonts, zero inline
styles, zero `<img>` tags outside the register, zero third-party requests. A
Content-Security-Policy of `default-src 'none'` that actually holds, because
the pages are built so it can.

## 2. Gaps closed in this pass

| gap | measured before | now |
|---|---|---|
| Abstract plates on index families | 1,718 on 227 pages | 860 on 209 pages |
| The seventeen interest pages | 728 plates, list truncated at 60 | an opening drawing and the whole set as rows |
| `/beyond-the-obvious` | 130 plates under its own map | rows |
| `/fund` | 12 plates | rows |
| The homepage's second band | four blocks of type | a full-bleed strip, four photograph slots |
| Three featured journeys | three identical continents | three frames, each on its own ground |
| Every glyph on the site | the dark world's accent on graphite | the editorial atlas palette |
| The dark world's accent | electric lime, spent on continents | cobalt-air, measured for that ground |

## 3. Gaps still open, and what each one needs

### 3.1 The site does not serve — BLOCKED ON THE OWNER

`europedoor.com` answers 404 with `x-vercel-error: DEPLOYMENT_NOT_FOUND` on
both the apex and the `www` host. DNS is correct, Vercel is answering, and no
deployment is attached to the domain. Nine consecutive runs of
`.github/workflows/deployed.yml` have failed, so the site has most likely
never served a page. **Nothing in this repository can fix it**: the config is
correct, the build is committed, and `site/index.html` exists. It is a Vercel
project setting.

### 3.2 Zero photographs — BLOCKED ON A HUMAN LOOKING

Twelve purposes are declared with written briefs and mechanical floors. The
pipeline is built, gated and tested end to end against a stub. One real
discover run has succeeded and produced eleven candidates. **What is missing
is somebody choosing one**, which is deliberate: the step between discovery
and acquisition is a person looking at a contact sheet, because a photograph
chosen from a filename is a photograph nobody looked at.

Until then five index openings, the homepage hero and four homepage panels
render their drawn state — which is designed, not degraded, and is the reason
the site is shippable with an empty register.

### 3.3 The dataset is a third written — EDITORIAL WORK

| | now | MVP target | |
|---|---:|---:|---|
| Countries | 50 | 5 | met |
| Destinations | 319 | 150 | met |
| Places | 255 | 1,000 | 26% |
| Experiences | 197 | 300 | 66% |
| Journeys | 17 | 50 | 34% |
| Stories | 9 | 100 | 9% |
| Business listings | 8 | 500 | 2% |

Two of those are deliberate rather than pending. Business listings will not
be seeded, because a directory of businesses that have not claimed their
entry is the thing this project refuses to publish. Stories and journeys are
about a day of writing each and the honest position is that they are behind.

### 3.4 Eight hundred and sixty plates remain — A DECISION, NOT A BUG

| family | plates | pages | per page |
|---|---:|---:|---:|
| country and region pages | 699 | 180 | 3.9 |
| month pages | 54 | 10 | 5.4 |
| macro region pages | 50 | 9 | 5.6 |
| motion pages | 45 | 9 | 5.0 |

None of these is a wall. Four cards in a grid of like things is the case a
card was designed for, and the measured failure has always been density:
eleven in a column on the homepage, forty-three on an interest page. **The
line is drawn at density rather than at the plate**, and it moves the day
photographs exist for destinations, not before.

### 3.5 What is deliberately not built

Recorded in full in `docs/api-architecture.md` and
`docs/technical-foundation.md`, each with the trigger that would change it:
no Postgres, no server, no auth, no booking engine, no ranking, no
accommodation card, no crowd measurement, no region boundaries.

---

## 4. The order to work in

1. **Attach a deployment.** Nothing else reaches a reader until this is done,
   and everything else is invisible without it.
2. **License four photographs** for the homepage strip, then one for the
   hero. That is one discover run and four acquire runs.
3. **Write.** Stories and journeys, in that order — the two furthest behind
   and the two a reader most notices.
