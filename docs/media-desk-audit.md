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
