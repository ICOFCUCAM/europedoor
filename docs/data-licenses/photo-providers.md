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

## The three questions, and why they are questions

`photo-providers.json` holds them. Each is a fact about the provider's live
terms, and **each must be answered by reading those terms** — this repository
records elsewhere that nothing may be committed against a licence gate from a
marketing page or from memory, and that rule applies hardest here, where
getting it wrong means republishing somebody's photograph on terms we invented.

**1. May we self-host?** This site serves `img-src 'self' data:` and
`checks.py` refuses any third-party origin. A provider whose terms require
hotlinking cannot be used without changing both, which is an owner decision
about the security posture of every page — not a build step.

**2. What exactly must the credit say?** `picture()` prints the photographer
and the licence. If the terms require a link to the provider, or to the
photographer's profile, or particular wording, **the renderer changes before
the first fetch**, not after. A credit that is close to right is a credit that
is wrong.

**3. Is a download ping required?** Some APIs require a request to a separate
endpoint when an image is actually used. If so it is part of using the image,
not an optional courtesy.

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

## The sandbox cannot do this

The proxy answers 403 to CONNECT for general hosts, and the build must run on
a machine with no internet and produce identical pages. So acquisition is a
human or CI step, exactly like `scripts/map/fetch.py`, and what gets committed
is the file and its row.
