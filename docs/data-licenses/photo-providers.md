# Photograph providers — the gate, and which route it opens

**Status: Pexels is cleared for automated acquisition. Unsplash is refused
for that route and permitted for a hand-download.** The register
(`data/images.json`) is still empty: the gate being open is not a photograph
arriving, and nothing here may claim one was acquired unless the workflow
actually acquired it.

## What is built

| piece | state |
|---|---|
| the register, and its twenty-four required fields | built, enforced twice |
| `picture()` — a photograph if we hold one, a plate if not | built |
| `data/image-purposes.json` — why a photograph exists, before one exists | built |
| `scripts/images/discover.py` — search, list, name no winner | built |
| `scripts/images/acquire.py` — take ONE approved id, verify, download, register | built |
| `scripts/images/derive.py` — the width ladder, hashed per derivative | built |
| the licence gate, per provider **and per route** | built, and it refuses two of the three routes |
| `.github/workflows/photograph.yml` — the only thing that touches the network | built |

`Pexels` and `Unsplash` were already valid licence values in
`tools/lib/data.py` before any of this, so the schema has always been ready
for exactly these two.

## The gate is on the ROUTE, not on the provider

That was the correction that produced this version. The first answer refused
Unsplash outright, which was wrong: an image licence permitting free
commercial use says nothing about whether the **API terms** permit automated
acquisition followed by self-hosting, and the two questions have different
answers for the same provider.

| provider | licence permits the use | API permits automated acquisition + self-host |
|---|---|---|
| Pexels | yes | yes |
| Unsplash | yes | **no** — the API guidelines require the hotlinked URLs and a download event |

So `automated_acquisition` is a field of its own, `acquire.py` refuses a
provider that is not `true` there, and `checks.py` asserts the same thing
independently on every commit. A provider may be perfectly usable by hand and
still be refused this route, and saying so is more useful than one verdict per
provider.

## Why a quote is required

`photo-providers.json` holds the questions. **The gate does not ask whether
anybody knows what a provider allows. It asks for the sentence, and for the
archived page it was copied out of.**

That distinction is the whole design. A model's recollection of a commercial
API's terms is not evidence — it is a guess wearing the clothes of one, and
these terms change. So each fact is answered with three things:

| | |
|---|---|
| `value` | true / false, or the required credit as a string |
| `quote` | the sentence, **copied verbatim** from the page |
| `source` | the URL it came from |

and `checks.py` asserts **the quote appears in the archived snapshot of that
page**. An answer typed from memory fails the build, because the evidence has
to exist in the repository beside it and has to match. Proved four ways: a
quote with no snapshot, a quote that is not in the page it cites, a correct
quote that passes, and a gate half-answered.

**1. May we self-host?** This site serves `img-src 'self' data:` and
`checks.py` refuses any third-party origin. A provider whose terms require
hotlinking cannot be used without changing both, which is an owner decision
about the security posture of every page — not a build step. This is the
question Unsplash fails.

**2. What exactly must the credit say?** `picture()` prints it. If the terms
require a link to the provider, or to the photographer's profile, or
particular wording, **the renderer changes before the first fetch**, not
after. Pexels asks for "Photo by <photographer> on Pexels" with both linked,
so that is what `render.picture()` emits, and it emitted it before anything
was downloaded.

**3. Is a download event required?** Some APIs require a request to a separate
endpoint when an image is used. A cleared `download_ping: true` with no
`endpoint_download` fails the check, because nothing would call it.

**4. May acquisition be automated at all?** The route question above. Then
`read_on`: a gate opened without recording when the terms were read cannot be
re-checked.

## How the terms get read

    python3 scripts/images/verify_provider.py --provider pexels

fetches every URL in `terms_urls`, writes each into
`provider-terms/<provider>.<page>.<date>.txt` with the SHA-256 of the bytes as
served, and prints the passages mentioning hotlinking, attribution and
downloads. **It answers nothing** — it fetches, archives and points, and a
person reads.

It will not run in the EuropeDoor sandbox. The egress proxy returns 403 for
both providers, which was confirmed rather than assumed, and is precisely why
this is a gate. Run it in the `photograph` workflow, which has network access.

**A page read in a browser and pasted in is also evidence**, and
`scripts/images/save_terms.py` archives it the same way — the date, the
SHA-256 of the text as saved, and a header saying a person saved it from a
browser rather than a socket. The provenance of the snapshot is recorded
because the two are not the same kind of artefact and the difference should
not be silent.

## Acquiring one

Two stages, because they are two decisions, and they are separate inputs to
`.github/workflows/photograph.yml` rather than two flags on one command.

**discover** searches, prints candidates — id, photographer, page, native
width, and whether each one meets the purpose's requirements — and **draws
every candidate inside the real hero**, uploading the sheets as an artifact of
the run. It commits nothing and it names no winner.

    stage: discover · provider: pexels · purpose: homepage-hero
    query: "alpine valley at dawn"

The sheet is the reason this stage exists rather than a list of ids. A
photograph is judged here through an elliptical arch, on a limestone wall,
under a cobalt masthead, with a serif headline over its lower half — and a
picture that is lovely in a provider's grid can be unusable in that
composition, or the reverse. Three sheets come back: 1280, 390, and the dark
colour-scheme preference.

**It downloads a preview per candidate, and a preview is never the
acquisition.** Those bytes are for looking at; they go to an ignored scratch
directory, they leave as a workflow artifact, and `checks.py` asserts the
repository contains none of them. The acquisition fetches `original` by id
and hashes THAT.

**acquire** takes ONE id that a person approved, fetches that id by id,
**asserts the returned id is the requested id**, downloads, hashes, keeps the
untouched original, builds the ladder, completes the provenance, runs every
gate and opens a pull request.

    stage: acquire · provider: pexels · purpose: homepage-hero
    photo_id: 1234567 · alt: "…" · focal: "50,40"

**The previous design took a search result by POSITION** — `--pick 3` — so the
picture a person approved and the picture that arrived could differ silently
while every provenance field was correctly recorded about the wrong one. A
position is not an identity. If the id cannot be retrieved the workflow fails;
it never substitutes another photograph.

## Purpose is mandatory, and it is declared first

`data/image-purposes.json` names the surface a photograph is FOR, the register
key it fills, the page it is published on, and the minimum it must be —
native width, orientation, aspect range. `acquire.py` refuses a purpose that
is not declared and a photograph that does not meet it; `data.py` refuses a
register row whose purpose is unknown and two rows claiming the same one. A
photograph acquired for the homepage hero cannot drift onto a destination page
because it happens to be in the register.

`min_width` is **native** pixels, not the ladder's widest step. A 1,200-pixel
original upscaled to 2,400 is the same class of untruth as a population we
estimated, and `derive.py` refuses to upscale for the same reason.

## The original is kept

`photographs/<key>.original.<ext>` is the bytes as served, and it is never
overwritten by a resized or recompressed version and never deleted to make the
repository smaller. The SHA-256 in the register is of **those** bytes, which
is what makes "this file is the file that was licensed" a checkable claim
rather than a sentence.

`derive.py` reads it, builds the widths and formats `picture()` asks for with
**Pillow** — the sister repository encodes 629 photographs this way, and
ImageMagick is one more thing to have installed — and records the SHA-256,
byte count and real pixel dimensions of every derivative. The derivative
filenames carry the original's hash, so they sit at a URL that cannot change,
which is what the `immutable` header on `/assets/` promises.

## Credentials

`PEXELS_API_KEY`, from the environment only. **Never in a file, a commit, a
workflow body, a log line, generated metadata or a PR body.** A GitHub
repository secret, passed as `env` on the single step that needs it rather
than on a command line that gets logged. `acquire.py` exits with that
instruction rather than a stack trace when the variable is missing, and it
never prints a key. `tools/checks.py` greps the committed files for anything
credential-shaped, and the workflow runs that grep again before it commits.

## The approval boundary is the pull request

The workflow opens a branch and a PR; it never pushes to the default one. The
PR body is generated by `scripts/images/pr_body.py` **from the register the
acquisition wrote** — photographer, licence, source page, both hashes, every
derivative — so it cannot describe a photograph other than the one committed.
Nothing is typed into it.

**And the run carries the finished page.** `tools/hero-shot.js` shoots the
built homepage at both widths and fails on any request the page made that came
back 4xx — which is exactly how the derivatives were once registered,
referenced and absent, with the hero rendering as a hole while every count was
green. The contact sheet answers "which of these", from previews; this answers
"and it actually works", from the real files. They are different questions.

A photograph moves `safety.img_tags` off an exact zero and moves
`weight.home_kb`. Both are invariants, so both have to be moved deliberately
in that diff, which is the point: licensed imagery arriving is a thing
somebody reads rather than a thing that happens.

## The sandbox cannot do this

The proxy answers 403 to CONNECT for general hosts, and the build must run on
a machine with no internet and produce identical pages. So acquisition is a CI
step, exactly like `scripts/map/fetch.py`, and what gets committed is the
original, the derivatives and the row.
