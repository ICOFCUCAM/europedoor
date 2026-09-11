# The Media Desk — Phase 1, the architecture that already exists

Written before anything was modified, which is what the brief asks for. It
answers three questions: what the media pipeline already is, which of the
brief's thirty sections it already satisfies, and the one finding that
changes the shape of every phase after this one.

---

## 0 · The finding that changes everything after it

**There is no Backdoor.** Not in `europedoor`, not in `fako-journeys`.
Searched both repositories for the word in every file: no matches. There is
also no Supabase, no database, no server, no authentication, no session, no
runtime npm dependency and no serverless function anywhere in this product.
`vercel.json` has an empty `buildCommand` and serves a directory of 1,034
static files under `default-src 'none'`.

So sections 2, 3, 4, 6, 17, 18, 19 and 22 of the brief — the navigation, the
search screen, the candidate card, the acquisition dialogue, the progress
states, the media library, the replacement workflow and the editorial visual
design — are **not an extension of the media pipeline. They are a new
application**, and the brief's own section 7 decides where it has to live:
the Pexels key may never reach the browser, so whatever renders those screens
needs a trusted server-side half to hold the key, proxy the search and
dispatch the workflow.

That is an owner's decision, not an engineering one, and it is the only thing
in this brief I cannot settle from the code. Section 33 below states the
three real options and a recommendation.

**Everything else in the brief is buildable now**, and a large part of it is
already built.

---

## 1 · What exists today

### The scripts — `scripts/images/`

| file | what it does | lines |
|---|---|---|
| `discover.py` | searches a provider, prints candidate ids, photographers, native sizes and whether each meets the purpose. **Names no winner.** Caches so looking twice costs one call | 9.8 KB |
| `contact_sheet.py` | renders **the actual page** once per candidate — `pages.home()`, the shipped stylesheet, the same `arch_path()` — for art direction | 10.7 KB |
| `acquire.py` | takes ONE approved id: fetches by id, asserts the returned id equals the requested id, downloads, hashes, keeps the original, writes the register row | 17.9 KB |
| `derive.py` | the width ladder from one source file, Pillow, **never upscales** | 7.7 KB |
| `pr_body.py` | the pull-request body, every figure read **out of the register** so it cannot describe a different photograph | 4.8 KB |
| `verify_provider.py` | fetches each provider's terms page, archives it with the date and the SHA-256 of the bytes as served, prints the passages about hotlinking, attribution and downloads. **Answers nothing** | 7.6 KB |
| `save_terms.py` | the archive side of the same gate | 5.7 KB |

### The data

| file | what it holds |
|---|---|
| `data/images.json` | the register. Every row needs file, alt, photographer, source, licence, **and** a date and a SHA-256. Currently `{}` — nothing has been licensed |
| `data/image-purposes.json` | `purposes` (12 declared), `roles` (12), `$requirements`, `$crop`. A purpose declares a role, a register key, a page, a `min_width` in **native** pixels, an orientation, an aspect band, a `container` and a `safe_area` |
| `docs/data-licenses/photo-providers.json` | four questions per provider — may we self-host, what must the credit say, is a download ping required, may acquisition be automated — each answered with a `value`, a **verbatim quote** and a `source` URL, and the quote must appear in the archived snapshot |

### The workflow — `.github/workflows/photograph.yml`

Two stages, `workflow_dispatch`, because they are two decisions.

```
discover → contact sheet → A PERSON LOOKS → exact photo id →
acquire → verify id → download → hash → derive → register →
every gate → shoot the page → PR → a person looks again → merge
```

`PEXELS_API_KEY` is a repository secret passed as `env` on the three steps
that need it, never on a command line, never into the register, never into
the PR body. A step before the commit greps the committed files for anything
credential-shaped.

### The gates

`tools/photo-tests.py` — 74 checks, end to end against a **stub provider**.
`tools/checks.py` — 91 checks including: no `<img>` without a register row, no
published page referencing a file with no row, no `style="` attribute
anywhere, no third-party image origin, every crop rule the arithmetic of its
measured container, and the credential grep.

---

## 2 · The brief's thirty sections against the built system

| § | asks for | state |
|---|---|---|
| 1 | audit first, reuse, do not build a second system | **this document** |
| 2 | Backdoor navigation with a Media section | **no Backdoor exists** |
| 3 | image discovery from Backdoor | discovery exists as a script and a workflow; **no UI** |
| 4 | candidate card | `discover.py` prints every field the card asks for; **no UI** |
| 5 | purpose is first-class, no `unknown` | **DONE.** `acquire.py` refuses an undeclared purpose before any network call |
| 6 | acquisition dialogue | the dispatch form is the dialogue today; **no UI** |
| 7 | the key never reaches the browser | **DONE, and structurally** — there is no browser in the loop at all |
| 8 | GitHub Actions is the acquisition worker | **DONE** |
| 9 | never acquire by search position | **DONE, and it is the reason the design was rewritten.** `--pick 3` was removed; `acquire.py` asserts the returned id equals the requested id before a byte is written |
| 10 | original preserved, derivatives, never upscale | **DONE.** `derive.py` refuses to upscale; the original is kept and is what the SHA-256 is of |
| 11 | a media abstraction that survives moving to object storage | **partial.** The register is the asset record; there is no `MediaPlacement` and no storage indirection |
| 12 | complete provenance | **DONE**, with one naming difference — this register uses `provider_photo_id`, `fetched`, `sha256` |
| 13 | hash verification | **DONE** for the original |
| 14 | attribution generated from provenance, one source of truth | **DONE.** `render.picture()` and `pr_body.py` both read the register |
| 15 | an explicit media status machine | **NOT BUILT.** Status is implicit in which files exist |
| 16 | the PR is the publication gate | **DONE** |
| 17 | Backdoor shows pipeline progress | the workflow log is the progress view; **no UI** |
| 18 | media library | **NOT BUILT** |
| 19 | replacement workflow | **NOT BUILT.** `acquire.py` refuses a purpose already filled, which is the safe half and not the workflow |
| 20 | image slots tied to the editorial architecture | **partial, and the gap is structural.** Twelve roles and twelve purposes exist — the homepage hero, four doors, five index openings and two named destinations. But a purpose is one surface on **one page**, so a slot that applies to 319 destinations needs 319 purposes. The brief's own model is the fix: `purpose: destination_hero` plus `target: amalfi-coast`, a template and an instance |
| 21 | requirements come from the slot, not the UI | **DONE** in the data; nothing reads it from a UI because there is none |
| 22 | Backdoor designed as an editorial tool | **no Backdoor exists** |
| 23 | do not turn EuropeDoor into Pexels | **DONE** — there is no public search surface and cannot be |
| 24 | respect rate limits, no runaway retries | **partial.** `discover.py` caches; there is no explicit rate-limit detection |
| 25 | duplicate protection on provider + photo_id | **partial and the wrong way round.** It refuses a purpose already filled by a different photograph; it does **not** yet refuse the same photograph being acquired again for a second purpose, or report where an id is already used |
| 26 | tests for every invariant | **largely DONE** — 74 photograph-pipeline checks against a stub |
| 27 | render tests, do not trust unit tests | **DONE for the page** — `contact_sheet.py` renders the real hero per candidate and the workflow shoots the finished page into the PR. There are no Backdoor screens to render |
| 28 | do not stop at "it works" | — |
| 29 | the twelve-step editor experience | steps 1–6 need the Backdoor; steps 7–12 exist |
| 30 | phased implementation | this is Phase 1 |

**Fourteen of the thirty are already done, five are partial, and eight
require an application that does not exist.**

---

## 3 · What is missing and does not depend on the Backdoor decision

These are worth building whichever host the Backdoor gets, because every
option needs them and none of them is a UI:

1. **The slot system as a TEMPLATE** (§20, §21). Twelve roles and twelve
   purposes exist, and the requirements already come from the purpose rather
   than from a caller. What is missing is that a purpose is one surface on
   one page — `vienna-destination` and `chamonix-destination` are two rows
   saying the same thing about two of 319 pages. The brief's split of
   `purpose` from `target` is the shape that scales.

   **A CORRECTION.** The first version of this row said "only 2 purposes are
   declared". That was a miscount of the file's top-level keys, not of its
   purposes; there are twelve. The gap is the template, not the coverage.
2. **Duplicate protection on provider + photo_id** (§25), in the direction
   that is missing, with the answer naming where the id is already used.
3. **The media status machine** (§15), derived rather than stored — the
   states are already implied by which files and rows exist.
4. **A placement record** (§11) — which slot a registered asset fills, so
   the library and the replacement workflow have something to list.
5. **Rate-limit handling** (§24) — detect the provider's 429, surface it,
   never retry into the limit.
6. **The replacement workflow's data half** (§19) — retain history, never
   overwrite a provenance row.

---

## 4 · The one decision, and a recommendation

Section 7 forbids the key in the browser, so the Backdoor needs a trusted
server-side half. Three real shapes:

**(a) A serverless function beside the site.** `europedoor.com/backdoor`,
authenticated, with `PEXELS_API_KEY` and a GitHub token as environment
secrets on the host. Closest to the brief. It also puts a credentialed,
authenticated surface on the production origin of a product whose recorded
position is that it has no server, and it is the largest new attack surface
this repository would have ever had.

**(b) A local editorial desk.** The same screens, served by a small local
process the editor runs on their own machine; the key lives in their
environment, and the only thing that reaches GitHub is a `workflow_dispatch`.
Every screen in the brief is buildable exactly as specified. Nothing is added
to europedoor.com, the CSP does not move, and the production origin gains no
authentication surface, no session and no credential.

**(c) No new application.** Keep the workflow as the desk: discovery
publishes the contact sheet as an artifact, the editor approves by
dispatching acquire with the id. This is what exists today, and it is the
reason fourteen of thirty sections are already satisfied.

**CHOSEN: (b), by the owner.** What follows was built against it, and no
real photograph is acquired — everything is tested against the existing stub
provider, as the brief's closing line instructs.

**Recommendation: (b).** It gives the brief's actual acceptance criterion —
"an editor can discover, evaluate, acquire, provenance, process, approve and
publish without manually downloading a file, while the credential remains
private and every asset is auditable" — without putting a credential-holding,
authenticated service on the production origin. The editorial desk is an
internal tool used by one desk; the brief itself says so in §23. If the desk
later needs to be reachable from anywhere, (b) moves to (a) by changing where
the same process runs, which is why §11's storage abstraction and §15's
status machine are worth building either way.

**This is the owner's call and the work below it is blocked on nothing** —
section 3's six items are being built first, because all three options need
all six.


---

## 5 · What the desk is, as built

`python3 tools/desk/serve.py` → `http://127.0.0.1:8765`, sign in, browse,
approve, and the photograph lands on a branch.

| § | now |
|---|---|
| 2 · navigation | Find images · Library · Provenance |
| 3 · discovery | a search box, the slot's own requirements read out beside it |
| 4 · candidate card | a contact sheet: the photograph, photographer, native size, aspect, id, whether it meets the slot and why not, and whether it is already registered |
| 5 · purpose first-class | the slot picker is the first control; there is no way to search without one |
| 6 · acquisition dialogue | the photograph, the five facts, what will happen, and the word Acquire |
| 7 · security | the key is in the process and never in a response, a log, the DOM or a commit; the browser sends a provider, a photo id, a purpose and an alt text |
| 9 · never by position | the approval carries an id; there is no index anywhere in either half |
| 11 · storage | the register is the asset record and the desk reads it; moving the bytes to object storage changes `derive.py`'s output path and nothing in the desk |
| 15 · status machine | DERIVED, never stored — a stored state goes stale the moment somebody edits the register by hand |
| 17 · progress | eight steps with a state each, and on failure the step, what it said, and that nothing was published |
| 18 · library | every slot with its status, filterable by status, slot and text |
| 20 · slots | three templates covering 583 entities, plus ten one-of-a-kind purposes |
| 21 · requirements from the slot | the line under the search box is read out of the slot, not typed into the form |
| 24 · rate limits | a 429 is reported and never retried around |
| 25 · duplicates | a candidate already in the register says so, and names every purpose it fills |
| 26 · tests | `tools/desk-tests.py`, 50 checks against the stub, three of them proved red |
| 27 · render tests | every screen rendered at 1440 and 390; six defects found and fixed, none of which any count could see |

**Still not built, and each says why.** A PR is not opened by the desk —
sending work outward is a person's decision, and the branch is left for them.
The replacement workflow's UI is not built; its data half is (a purpose holds
one photograph, and re-acquiring the same id for the same purpose is a replay
while a different id is refused). And no slot exists for a country, region,
experience or journey hero, because those pages have no photograph container
in the markup: a slot nobody can fill is what `$requirements` already refuses.

## 6 · The hosted desk, and why it is a second Vercel project

The desk above runs on the editor's own machine. It was the right first
answer and it is not the answer to the brief, which asks for a desk an
editor **signs in to** — so it is now also deployed from `desk/`, as a
project of its own.

**IT IS NOT ON europedoor.com, AND THAT IS THE WHOLE POINT.** The
production site is `default-src 'none'`, no server, no session, no database,
no `api/` directory and an empty `buildCommand`. Putting a
credential-holding, authenticated service on that origin would change the
security posture of all 1,034 pages to serve one internal tool. A second
Vercel project from the same repository, root directory `desk/`, keeps the
site exactly as strict as it is now and costs one deployment configured
once.

**THE LOCAL DESK HELD STATE AND THIS ONE CANNOT.** `tools/desk/serve.py` is
one process: a session is a random token in a dictionary and a thumbnail is
a token in a map. Two serverless invocations share no memory, so a
dictionary here would work on the request that wrote it and fail on the
next — the classic port of a stateful design that appears to work in testing
because testing hits one warm instance. Both became **signed values**: a
session is a signed expiry, a thumbnail is a signed URL, and the server can
verify it minted the thing without having remembered it.

That is not the allowlist-in-front-of-an-SSRF the local desk refused. The
objection there was that a route fetching a caller-supplied address is
guarded by something the next person widens. **A signature is not a guard on
a caller's address; it is proof the address came from a search this desk
performed** — and the host allowlist stays as well, because two independent
reasons to refuse is the posture this repository takes everywhere else. One
of the 38 checks is exactly that: a correctly signed token pointing at
`169.254.169.254` fetches nothing.

**A SERVERLESS FUNCTION CANNOT IMPORT `tools/lib` OR READ `data/`.** So the
slot answer arrives as data: `tools/desk-registry.py` resolves every purpose
through `imageslots.resolve()` — the same resolver `acquire.py` uses — and
writes `desk/registry.json`, generated and committed exactly like `site/`,
with `checks.py` failing when it is stale. The slots are still declared once
in `data/image-purposes.json` and the targets still come from the atlas.

A templated row carries **no requirements of its own**: they are the slot's,
stated once under `slots`. 590 copies of one 300-word brief is half a
megabyte saying one thing, and a value repeated 590 times is 590 places for
it to differ. 519 KB → 225 KB, and one answer to "what does this slot need".

**The register is read live and the licence verdict is generated**, because
they have different lifetimes. A photograph appears when somebody merges a
pull request, so a status baked into a build goes stale within the hour; a
provider's clearance changes when somebody edits
`docs/data-licenses/photo-providers.json`, which is the same act that
regenerates this file. The verdict here is **not the gate** — `acquire.py`
refuses before it opens a socket, inside the workflow, where the key is —
and it can only ever refuse more than the gate, never less.

**The status is read off the DEFAULT BRANCH.** A photograph sitting in an
open pull request has been acquired and has not been accepted, and a desk
that called it PUBLISHED would be reporting the reviewer's decision before
the reviewer made it.

### What happens when an editor clicks Acquire

    browser  →  /api/acquire      provider, photo id, purpose, alt text
    function →  workflow_dispatch  photograph.yml, stage=acquire
    Actions  →  fetch by id · verify the id · keep and hash the original ·
                build the ladder · write provenance · run every gate ·
                shoot the page · open a pull request
    browser  →  /api/status        the run's own steps, then the PR link

The browser never holds a key, never calls a provider, and never fetches an
image from anywhere but this deployment.

**THE PROGRESS PANEL HOLDS NO LIST OF STEPS.** The local desk owned its
eight because it ran them; this desk runs nothing, so a list here would be a
copy of `photograph.yml`'s shape that drifts the first time somebody adds a
step to it — the ninth thing in this repository to pin a shape rather than a
promise. GitHub reports every step it actually ran, with its conclusion, and
that is what is shown.

**`workflow_dispatch` answers 204 with no run id**, so there is nothing to
hold. The acquire route signs the instant before it dispatched and the
status route asks for dispatches created since then. The window is inside a
signed token, so a caller cannot widen it to read a run they did not start.
A run GitHub has not created yet reads **queued**, never failed: a verdict
nobody has reached is the same error as calling an open PR published.

### The three secrets, and where each lives

| environment variable | what it is for |
|---|---|
| `DESK_PASSCODE` | the one passcode. No user store: a single-operator tool with accounts, roles and password hashes is security theatre with a migration attached |
| `DESK_SESSION_SECRET` | signs sessions and thumbnail tokens. **Separate from the passcode** — rotating one should not invalidate the other, and a signing key should never be something a person types. Unset, the desk refuses to sign rather than falling back to a constant |
| `PEXELS_API_KEY` | the provider key. It exists on this deployment and in GitHub Actions, and nowhere else |
| `DESK_GITHUB_TOKEN` | dispatches the workflow and reads the register. Needs `actions:write`, `contents:read` and `pull_requests:read` on this repository and nothing more |

Optional: `DESK_REPO` (default `ICOFCUCAM/europedoor`) and `DESK_BRANCH`
(default `main`).

**A failed sign-in costs a fixed 700 ms.** Not a lockout — a lockout on a
single-operator tool locks the operator out — but the passcode cannot be
walked quickly. On 127.0.0.1 the threat was anything running as that user;
on a public origin it is everyone, and the delay is the difference.

### Deploying it

1. New Vercel project, same repository, **root directory `desk`**.
2. Framework preset: Other. `desk/vercel.json` carries the rest —
   `outputDirectory: public`, the functions, and headers as strict as the
   site's, including `X-Robots-Tag: noindex` and a CSP with no
   `unsafe-inline` and `img-src 'self'`.
3. Set the four environment variables above. None of them is ever written
   to a file, a commit, a log line or a response, and one of the 38 checks
   greps `desk/` for anything credential-shaped.
4. Point a hostname at it — `desk.europedoor.com` — or use the deployment
   URL. Nothing about europedoor.com changes either way.

### What it still does not do

It does not search (`providerSearch` calls the provider once and a 429 is
reported rather than retried around), does not download a photograph, does
not write a register row, does not build a derivative and does not compose a
PR body. Four scripts already do all of that, and a second implementation of
any of them is a second chance to make its mistake.

It does not merge. **A pull request is a question, not a publication**, and
the panel says so in those words: the run going green says the photograph is
in a branch with its provenance, its rendered page and both hashes, and that
nothing on europedoor.com has changed.

    node tools/hosted-desk-tests.js     38 — the hosted boundary
