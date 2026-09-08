# The homepage hero photograph — brief, and the licence gate

**Status: NOT ACQUIRED. No candidate selected, no licence read, no file in
the repository.** `data/images.json` holds zero rows and
`safety.img_tags` is still `0`.

This document exists so that acquiring it is a decision with a record, not a
build step somebody does in a hurry.

---

## Why a photograph, and not the generated system

The plate system was tried at hero scale first, because §17 of the standing
instruction requires the generated system to be exhausted before photography
is proposed. **It was rendered at 1200×500 through the same rasteriser the
social cards use and looked at.** The result, measured and observed:

- flat, monochrome bands; no atmosphere, no depth, no light quality
- the bottom third is a single dead slab of navy on every seed
- no detail survives at hero size — the drawing has nothing to reward a
  reader who looks closely, because there is nothing there to find

**The plate system carries a 160×100 card and cannot carry a hero.** That is
a measurement, not an opinion, and it is the justification for spending
anything at all here. The plates keep every other job they have.

---

## The photographic brief

**One image.** Not 319. The acquisition problem in `docs/images.md` is about
319 destination heroes, which is a genuinely hard problem in the "Hidden
Europe" tier. This is one image in the "Iconic Europe" tier, which that same
document rates as easy.

| requirement | |
|---|---|
| subject | one exceptional European landscape; a real, identifiable place |
| register | cinematic and authentic; sophisticated, not tourist-brochure |
| human scale | present — a figure, a boat, a village — so the frame has a sense of proportion |
| composition | substantial negative space on the left or lower-left for an h1, a lede, a discovery field and four chips |
| tonality | must take a dark scrim and hold light text at AA or better |
| dimensions | ≥ 2400px wide |
| crops | a strong 21:9-ish desktop crop AND a viable portrait-ish mobile crop from the same frame |
| avoid | obvious stock-photo look, artificial HDR, visible logos or commercial branding |
| people | no problematic identifiable private individuals |
| the test | it should read as *"Open the door to Europe"*, not as *"travel website hero image"* |

---

## The licence gate — SEVEN QUESTIONS, ALL UNANSWERED

**No candidate may be committed until every row below is filled in from the
licence text itself, opened and read.** Not from a provider's marketing page,
not from a summary, and not from an assistant's recollection.

| # | question | answer | evidence (URL of the licence text read) |
|---|---|---|---|
| 1 | Commercial use permitted? | — | — |
| 2 | Modification and cropping permitted? | — | — |
| 3 | Attribution required — and in what form? | — | — |
| 4 | Redistribution restrictions? | — | — |
| 5 | Identifiable people / property releases needed? | — | — |
| 6 | Website **and** marketing use both covered? | — | — |
| 7 | Any additional rights required for our use? | — | — |

**An image is not safe because it sits on a free-photo website.** Free-tier
providers host user uploads, and a licence granted by somebody who did not
own the image grants nothing.

**This could not be done from the build environment.** The sandbox's egress
proxy answers `403` to `CONNECT` for general web hosts — verified, not
assumed, in the proxy's own failure log — so no licence page can be opened
and no candidate can be viewed from here. **Acquisition is a human step.**

---

## Adding it, once the gate above is complete

One row. Nothing else in the codebase changes.

```json
"home-hero": {
  "file": "home-hero",
  "alt": "<what is in the photograph, for someone who cannot see it>",
  "photographer": "<name>",
  "source": "<https:// URL that can be opened>",
  "licence": "<from the closed list in tools/lib/data.py>",
  "focal": [38, 55]
}
```

Then the width ladder — 480, 800, 1260, 1800, 2400 — in AVIF, WebP and JPEG,
into `assets/img/`.

`tools/lib/data.py` refuses a row missing any of `file`, `alt`,
`photographer`, `source` or `licence`. There is no `unknown` and no default.

**`focal` is not a nicety.** It is `object-position`, and a 21:9 hero crop of
a portrait frame, centred, takes the sky and loses the subject. That is the
commonest way a responsive hero goes wrong.

---

## What is already built and waiting

- `render.picture()` — AVIF → WebP → JPEG, five widths, explicit `width` and
  `height` so nothing shifts when the file arrives, `loading="eager"` and
  `fetchpriority="high"` for the hero, credit rendered from the register.
- `.herofull.shot` — the scrim, applied only when the register holds the
  file. Without it the hero renders on its own ground and the page ships.
- Two independent guards, both **proved to go red**:
  - `checks.py` — *"/index.html: `<img>` for 'unlicensed-hero' has no row in
    data/images.json — no photographer, no source, no licence"*
  - `invariants.py` — *"safety.img_tags: 1, recorded 0"*

Both must be deliberately updated when the photograph lands, which is the
point: **the image cannot arrive quietly.**

---

## To re-measure the day it lands

1. Painted contrast over the *photograph*, not the fallback. The current
   measured worst case is 15.97:1 against the flat ground; a bright sky
   behind the h1 will be far lower, and the scrim is what must fix it.
2. `weight.home_kb` — the ceiling will move, deliberately.
3. The mobile crop, at 390×844, with the focal point applied.
