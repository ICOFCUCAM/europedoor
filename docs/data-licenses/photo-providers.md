# Photograph providers — the gate, and why it is shut

**Status: the pipeline is built and no provider is cleared.** Zero
photographs are licensed. `data/images.json` is empty and every `picture()`
call falls back to a generated plate, which is why the site ships today.

## What is built

| piece | state |
|---|---|
| the register, and its five required fields | built, enforced twice |
| `picture()` — a photograph if we hold one, a plate if not | built |
| `scripts/images/fetch.py` — search, look, pick, write the row | built |
| the licence gate | **shut, and this document is why** |
| the derivative step — the widths and formats `picture()` asks for | not built |

`Pexels` and `Unsplash` were already valid licence values in
`tools/lib/data.py` before any of this, so the schema has always been ready
for exactly these two.

## The three questions, and why a quote is required

`photo-providers.json` holds them. **The gate does not ask whether anybody
knows what Unsplash allows. It asks for the sentence, and for the archived
page it was copied out of.**

That distinction is the whole design. A model's recollection of a commercial
API's terms is not evidence — it is a guess wearing the clothes of one, and
these terms change. So each of the three facts is answered with three things:

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
about the security posture of every page — not a build step.

**2. What exactly must the credit say?** `picture()` prints the photographer
and the licence. If the terms require a link to the provider, or to the
photographer's profile, or particular wording, **the renderer changes before
the first fetch**, not after. A credit that is close to right is wrong.

**3. Is a download event required?** Some APIs require a request to a separate
endpoint when an image is used. If so it is part of using the image, and a
cleared `download_ping: true` with no `endpoint_download` fails the check,
because nothing would call it.

Then `read_on`. A gate opened without recording when the terms were read
cannot be re-checked.

## How the terms get read

    python3 scripts/images/verify_provider.py --provider pexels

fetches every URL in `terms_urls`, writes each into
`provider-terms/<provider>.<page>.<date>.txt` with the SHA-256 of the bytes as
served, and prints the passages mentioning hotlinking, attribution and
downloads. **It answers nothing** — it fetches, archives and points, and a
person reads.

It will not run in the EuropeDoor sandbox. The egress proxy returns 403 for
both providers, which was confirmed rather than assumed, and is precisely why
this is a gate. Run it locally, or run the `photograph` workflow with
**verify_terms** ticked: that runner has network access, and it opens a branch
carrying the archived pages for you to read.

**On Unsplash specifically.** There is a suspicion on record — in the gate
file, marked as a suspicion — that their API guidelines require using the
hotlinked URLs returned under `photo.urls`, require crediting both the
photographer and Unsplash with links, and require triggering a download
endpoint on use. **None of that is a fact here.** It is written down only so
somebody knows what to look for on the page, and the check will not let it
become an answer without the quote that supports it.

## What happens when the gate opens

`fetch.py` lists candidates and **stops**. It will not pick one for you:

    python3 scripts/images/fetch.py --provider pexels --query "Vienna Stephansdom"

prints the photographer, the pixel width and the page for each, and then says
to look at them. A photograph chosen from a filename is a photograph nobody
looked at, and this is a family — see `docs/image-philosophy.md` — where the
whole argument for buying one is that it does a job the drawing cannot.

Then, with a caption written for somebody who cannot see it:

    python3 scripts/images/fetch.py --provider pexels --query "…" \
      --pick 2 --key city:austria/vienna-and-the-east/vienna \
      --alt "Rooftops and the cathedral spire from the north, early light"

which writes the source file and the register row. The build will not
reference it until the derivatives exist.

## Credentials

`PEXELS_API_KEY` and `UNSPLASH_ACCESS_KEY`, from the environment only.
**Never in a file, a commit, a workflow body or a log line.** GitHub
repository secrets, passed to the step that runs the fetch. `fetch.py` exits
with that instruction rather than a stack trace when the variable is missing,
and it never prints a key.

## Running it

`.github/workflows/photograph.yml`, on manual dispatch only. A schedule would
mean photographs arriving on this site that nobody chose, and choosing is the
entire job.

Leave **pick** empty and it lists candidates and stops. Fill in **pick**,
**key** and **alt** and it takes that one, builds the derivatives, rebuilds
the site, runs the checks — and **opens a branch rather than pushing to the
default one**. A photograph moves `safety.img_tags` off an exact zero, which
is the deliberate signal that licensed imagery has arrived, so it is a diff
somebody reads.

The keys are passed as `env` on the single step that needs them rather than
on a command line, and `fetch.py` never prints one.

**Derivatives are ImageMagick**, because this repository is stdlib-only and
re-encoding AVIF in pure Python is not a thing anybody should attempt.
`scripts/images/derive.py` says what to install when it is missing rather
than failing three layers down, and it **never upscales**: a 900-pixel source
gets the widths it can fill and no more, because a file named `-2400` holding
900 pixels of detail is the same class of untruth as a population we
estimated.

## The sandbox cannot do this

The proxy answers 403 to CONNECT for general hosts, and the build must run on
a machine with no internet and produce identical pages. So acquisition is a
human or CI step, exactly like `scripts/map/fetch.py`, and what gets committed
is the file and its row.
