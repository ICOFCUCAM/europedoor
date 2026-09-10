# Automated photograph acquisition: architecture audit

**Question asked.** Can EuropeDoor acquire approved photographs automatically
through GitHub Actions — human approves a candidate, Actions does everything
else — self-hosted, without weakening the licence gate, the
Content-Security-Policy or the provenance standard?

**Answer.** Yes, through Pexels. No, through Unsplash. Nothing needs to be
weakened; six things need to be added or corrected. Written 2026-09-10 against
the five provider pages archived that day under `data-licenses/provider-terms/`.

Every conclusion below points at an archived page. Nothing here is answered
from recollection, from the sister repository, or from what an API "obviously"
allows.

---

## 1. The five questions, kept separate

The mistake this audit exists to avoid is collapsing a **licence** into an
**API's terms**. They are different documents with different scopes, and this
repository has already made the error in both directions within two commits:
first reading Pexels' licence page without its API guidelines and nearly
missing an attribution obligation, then reading Unsplash's API guidelines as
though they bound the licence and refusing a provider the licence permits.

So each provider is asked five questions, separately.

### Pexels

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Licence permits download / copy / distribution? | **Yes** | licence page: “All photos and videos on Pexels can be downloaded and used for free.” |
| 2 | API permits automated acquisition? | **Yes** | API documentation states no restriction on automation. Its limits are volume: “By default, the API is rate-limited to 200 requests per hour and 20,000 requests per month.” |
| 3 | API requires hotlinking / CDN delivery? | **No** | The archived API documentation contains no occurrence of hotlink, CDN, embed, “must use”, or any delivery condition. See §3 on why an absence is admissible here. |
| 4 | Self-hosting of an API-acquired image permitted? | **Yes** | Follows from 1 and 3: the licence grants use, the API adds attribution and adds no delivery condition. The licence's only distribution exclusion is “Don’t redistribute or sell the photos and videos on other stock photo or wallpaper platforms” — a European travel atlas is neither. |
| 5 | Download / event notification required? | **No** | No download endpoint exists anywhere in the archived API documentation; the word does not occur. |

**Attribution Pexels does require**, and it is not what the licence page implies:

> Whenever you are doing an API request make sure to show a prominent link to
> Pexels. […] Always credit our photographers when possible (e.g. "Photo by
> John Doe on Pexels" with a link to the photo page on Pexels).

The licence page says attribution is not required; the API guidelines require
it of API consumers. Both are true and the narrower one binds us. `picture()`
already renders exactly this, added before any fetch.

### Unsplash

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Licence permits download / copy / distribution? | **Yes** | licence page: “Unsplash grants you an irrevocable, nonexclusive, worldwide copyright license to download, copy, modify, distribute, perform, and use images from Unsplash for free, including for commercial purposes…” |
| 2 | API permits automated acquisition? | **Doubtful, and unresolved** | API guidelines, Usage Guideline 4: “The API is to be used for non-automated, high-quality, and authentic experiences.” The linked article explaining it is **not archived and not read**. It does not matter to the outcome, because 3 already settles it. |
| 3 | API requires hotlinking / CDN delivery? | **Yes** | Technical Guideline 1: “All API uses must use the hotlinked image URLs returned by the API under the `photo.urls` properties. This applies to all uses of the image and not just search results.” |
| 4 | Self-hosting of an API-acquired image permitted? | **No** | Same sentence. “All uses of the image and not just search results” forecloses the read that hotlinking applies to previews only. |
| 5 | Download / event notification required? | **Yes** | Technical Guideline 2: “you must send a request to the download endpoint returned under the `photo.links.download_location` property.” |

**So `automated_acquisition` is false for Unsplash, and precisely why:** the
required architecture is *acquire through the API, then self-host*. Guideline 1
forbids the second half for anything acquired through the API. The two are not
separable — it is not that we would prefer to self-host, it is that the API
route obliges CDN delivery for every use of the image.

Serving `images.unsplash.com` would mean opening `img-src` on all 1,033 pages
to a host we do not control, plus firing a per-use event to a third party from
readers' browsers. **That is not on the table**: the instruction is explicit
that the CSP is not to be changed to accommodate a provider, and it is the
right instruction.

Unsplash's **licence route** is unaffected and stays open: an image obtained
from the website without the API may be self-hosted. It is simply not the
automated architecture, so it does not answer this brief.

---

## 2. Provider capability matrix

| Provider | Automated acquisition | Self-host permitted | Attribution | Download event | API restrictions | Suitable for EuropeDoor |
|---|---|---|---|---|---|---|
| **Pexels** | **Yes** — no clause against it; 200 req/hr, 20,000/month | **Yes** — licence grants use, API adds no delivery condition | **Required by API**: prominent link to Pexels, plus “Photo by *name* on Pexels” linking to the photo page | **None** | No replicating Pexels' core functionality; no wallpaper apps; no working around the rate limit | **YES — this is the provider** |
| **Unsplash** | **No** | **No** for API-acquired images | Photographer **and** Unsplash, with a profile link carrying utm parameters | **Required**, per use, on `photo.links.download_location` | Hotlinking mandatory; keys confidential; “non-automated … experiences” (unread article) | **NO — for the automated route.** Licence route remains open and is out of scope here |

---

## 3. On admitting a negative

Three of the Pexels answers are absences: no hotlinking condition, no download
event, no automation clause. A quote shows what a page says and never what it
omits, so an absence needs a reason its silence is conclusive. Here it is:

- The Pexels API documentation has a section headed **Guidelines** that
  enumerates what a consumer must and must not do. It names four things, and
  none is a delivery condition or an event.
- **Unsplash's equivalent section states both explicitly.** Two providers,
  same kind of document, same page structure; one says it and one does not.
  That makes the omission meaningful rather than merely unobserved.
- The full endpoint list in the Pexels documentation contains no
  download-tracking endpoint, and its Photo resource carries no
  `download_location` field to call one with.

`checks.py` now refuses a `false` answer that carries no `basis`, so this
reasoning lives beside the answer rather than in somebody's head.

---

## 4. What the current implementation actually does

Audited: `scripts/images/fetch.py`, `scripts/images/derive.py`,
`scripts/images/verify_provider.py`, `docs/data-licenses/photo-providers.json`,
`data/images.json`, `tools/lib/data.py`, `.github/workflows/photograph.yml`.

**Already right and worth keeping.** The gate refuses before a socket opens.
Keys come only from the environment and are never printed; a check greps the
committed files for credential-shaped tokens. `derive.py` produces the ladder
at settled quality values and never upscales. The workflow passes secrets as
`env` on the single step that needs them. `picture()` renders the Pexels credit
correctly. The licence answers are backed by archived pages and matched
verbatim.

**Six defects against the required architecture.**

1. **The candidate is chosen by list index, not by identity.** `--pick 3` means
   "the fourth result of a search I am running now". The human approves an
   index from a previous run's output, and search results reorder — so the
   approved photograph and the acquired photograph can differ, silently, with
   every provenance field correctly recorded about the wrong picture. This is
   the single most serious fault found.

2. **The workflow pushes a branch and does not open a pull request.** The
   required flow ends in a PR for human approval; today somebody has to notice
   the branch.

3. **There is no `purpose`.** The register key doubles as the destination, so
   the request cannot say "homepage-hero" and have the pipeline resolve it.

4. **Provenance is incomplete.** Measured against the required list:

   | Required | Present today |
   |---|---|
   | photographer | yes, and required by the validator |
   | photographer / profile URL | written by `fetch.py`, **not required** by the validator |
   | source page | yes, required |
   | provider | **absent** — inferable from `licence`, which is not the same thing |
   | licence name / URL | yes, required |
   | date verified | **absent from the row** — `read_on` lives in the gate, so a row cannot say which reading of the terms was in force when it was taken |
   | source / archive evidence | **absent** — the row names no archived snapshot |
   | SHA-256 of received original | yes, required |
   | acquisition timestamp | **date only**, not a timestamp |
   | processing / encoding information | **absent entirely** — widths, formats, quality values and encoder version are recorded nowhere |

5. **Nothing ever re-verifies the SHA-256.** It is written once and never
   compared against the bytes on disk. A provenance claim nothing checks is
   the failure class this repository has recorded more than once.

6. **The licence gate has no question about automation.** It asks whether we
   may self-host, what the credit must say, and whether an event is required.
   It does not ask whether the provider permits automated acquisition — which
   is the question this brief turns on, and the one whose answer differs
   between the two providers.

---

## 5. The sister repository is a precedent, not evidence — and it is
   non-compliant

`fako-journeys` self-hosts 629 photographs, **34 of them from Unsplash**,
served from its own R2 bucket. Its Unsplash provider retrieves and stores
`downloadLocation` and **nothing in that repository ever calls it**.

Against the guidelines archived here, that is two breaches: images acquired
through the Unsplash API are served from a bucket rather than hotlinked, and
the required download event is never fired. The field *names* in its register
are good and were copied deliberately. Its *practice* on Unsplash must not be,
and this section exists so that nobody later reaches for it as a reason.

---

## 6. What needs to change

Nothing in this list weakens the gate; four items strengthen it.

1. **Acquire by candidate identity.** `candidate_id` replaces `--pick N`,
   resolved through the provider's own single-photo endpoint
   (`GET /v1/photos/:id` on Pexels) rather than by re-running a search. A
   listing run still exists to find candidates and prints ids.
2. **Add `purpose`** to the workflow inputs, resolved to a register key by a
   declared map, so the request reads `provider / candidate_id / purpose`.
3. **Add `automated_acquisition` to the licence gate**, answered per provider
   from the archived pages, with `fetch.py` refusing before the request when
   it is false — the same shape as the existing `api_route` refusal, and the
   place Unsplash's `false` is recorded.
4. **Extend the register schema** with `provider`, `terms_read_on`,
   `terms_snapshot`, `acquired_at` (a timestamp, not a date) and a
   `processing` object holding widths, formats, quality values and the
   encoder version — and make the whole set required, including
   `photographer_url`, so a row cannot be half-provenanced.
5. **Re-verify the hash in `checks.py`**: every registered original must still
   hash to its recorded `sha256`, and every width and format the register
   claims must exist.
6. **The workflow opens a pull request** carrying the credit, the alt text,
   the licence, the archived terms it was taken under and the hash, so the
   human approval step reviews evidence rather than a file listing.

**One decision belongs to the owner, not to this audit.** `fetch.py` commits
the untouched original beside the derivatives, which is what makes the
SHA-256 re-checkable. Originals are multi-megabyte and the repository is
already 1,072 generated pages. The alternative is to record the hash and drop
the original, which makes the evidence unverifiable later. This audit
recommends keeping the original, and flags the weight as the cost.
