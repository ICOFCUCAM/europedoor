# The non-home redesign — eight rooms, one institution

**What this is.** The answer to the MASTER NON-HOME REDESIGN DIRECTIVE, written
from the site's own instruments rather than from intention. Every number here
is reproducible by running the command named beside it. The homepage is out of
scope and was not touched.

The directive's own test is at the bottom of this file: *"Would a design-led
European cultural institution ship this?"* — and the evidence for it is
`tools/contact-sheet.js`, which puts twelve families in one field of view.

---

## A · What the site was, measured

`docs/design-direction-audit.md` measured it before any of this: **eleven of
twelve families placed an identically-sized h1 at an identical vertical
position**, and the entire art-directional difference between a magazine story
and a country encyclopedia was one 11px kicker changing hue.

One shell, one stylesheet and eleven primitives are an engineering achievement
and they are kept. They are not, by themselves, a design.

Three measurements set the work:

| instrument | what it said |
|---|---|
| `node tools/contact-sheet.js` | eleven of twelve families opened with a kicker, a serif h1, a lede and a large arched map in the same position |
| `node tools/opening.js` | how much of the first screen is a picture, per family |
| `node tools/voids.js` | 18,216 empty pixels of 239,404 across 47 families |

---

## B · The eight rooms

The directive names eight families and this repository now derives them from
the route, in one table, in `render.ed_family()`:

| room | routes | what its page is FOR |
|---|---|---|
| **ATLAS** | `/countries`, `/discover/<macro>`, `/europe/<c>`, `/europe/<c>/<r>` | where a place is, and what it is next to |
| **ARRIVAL** | `/europe/<c>/<r>/<city>`, `.../place/<x>` | you have decided to come; what is it like |
| **DISCOVERY** | `/discover`, `/experiences*`, `/interests*`, `/themes*`, `/europe-in*` | you have not decided; what is there |
| **JOURNEY** | `/journeys*` | an ordered sequence of places |
| **EDITORIAL** | `/stories*` | an argument, read start to finish |
| **TIME** | `/events*`, `/experiences/<cat>/<sub>` | when |
| **INSTRUMENT** | `/map`, `/plan`, `/search`, `/my-europe` | a tool you operate |
| **INSTITUTION** | everything else (~19 pages) | who we are and what we refuse |

**Derived, never passed.** Forty-seven builders each passing a family string is
forty-seven chances for two pages in one family to disagree, and this
repository has that failure recorded about the fourteen call sites that forgot
to pass a motif. A route is what a family IS.

---

## C · The helpers were what forced the grammar

The directive's own line: *"If a helper forces every page into the same visual
grammar, refactor the helper."* Three did, and all three were changed rather
than worked around:

- **`indexhero()`** emitted `pagehead index` with an arched map on the right.
  Every index used it, so every index was the same picture. It emits
  `ed-opening` now, and the visual is whatever the family's subject is.
- **`card()`** drew a plate from the seed when no motif was passed, which is
  how 272 of 319 destinations came to have two pictures. The card grid is gone
  from every index; **189 `.card-art` elements ship and every one is a map.**
- **`section()`** printed one h2 with one lede on three-quarters of the pages.
  It now takes `opens=True` to mark a change of movement with a rule and air.

Eleven new primitives were added and each is a SCALE rather than a component:
`ed_opening`, `ed_section_head`, `ed_rows`, `ed_split`, `ed_photo`, `ed_bleed`,
`ed_feature`, `ed_strip`, `ed_mosaic`, `ed_declare`, `ed_slot`.

---

## D · Photography is a content layer, and the empty ones say so

The register holds a handful of photographs and the site has **1,626 declared
image surfaces across 479 pages**, reproducible with:

    grep -ro 'class="ed-slot ' site --include=index.html | wc -l

**An empty slot is not a hole and it is not a plate.** `ed_slot()` renders the
surface at its declared proportion and prints the purpose key, the first
sentence of the slot's brief, and the native width and orientation a
photograph must have to fill it. A reader sees what is coming; an editor sees
the acquisition list; nothing is silently substituted.

That is the directive's own rule — *"mark the slot clearly and identify the
required acquisition"* — and it replaced a worse answer. `ed_photo()` falls
back to a generated plate, which is placeholder art doing a picture's job and
says nothing about what is missing.

Seven image scales, and no two families use the same set:

| scale | where |
|---|---|
| HERO | the homepage only (out of scope) |
| BLEED | a change of movement: country, destination, journey, story |
| FEATURE | a dominant picture with its own words, alternating sides |
| STRIP | a sequence, scrolled: region, interest, category, motion, month, place, theme |
| MOSAIC | one dominant and two beside it, never four equal tiles |
| DECLARE | a typographic statement over a picture, behind a measured scrim |
| SLOT | any of the above, unlicensed, saying which photograph it wants |

**Why a strip and not a grid.** A sequence is read along. Wrapping it into rows
turns an order into a grid, which is the shape this whole system replaced.

---

## E · What each room actually does differently

**ATLAS** — type beside the real geography, then an atlas margin index (a mono
`<dl>` of ISO code, population, region), then a bleed, then a destination strip.

**ARRIVAL** — a dark arrival block: the map first, the name over it, the
orientation line under. The only family whose opening inverts.

**DISCOVERY** — the argument is a SHAPE. `/interests` draws seventeen
constellations at one extent because reach is the argument no single tag page
can make; `/experiences` draws eight bars because 131 against 5 is the
argument; `/europe-in` prints twelve queries as queries.

**JOURNEY** — the hero is cobalt, full bleed, and carries the route drawn on
the field in the band's own ink. The index carries each route as a row.

**EDITORIAL** — a story opening: desk, reading time, date, byline; then the
essay at a 38rem measure with the places in the margin.

**TIME** — a year band whose two series disagree on purpose, then the month's
own places.

**INSTRUMENT** — graphite in both colour-scheme preferences, because the world
says where the reader is and not how they like their screen. An instrument's
title is a LABEL at section weight, so the tool starts at 328–397 rather than
at 436–460.

**INSTITUTION** — a monument: a narrow measure, display type, an olive mono
kicker, and no photograph. `/manifesto` alternates alignment down the page.

---

## F · What was preserved

Every gate that existed before this work still passes, and they are the proof
rather than the claim:

    python3 tools/build.py check
    python3 tools/checks.py                    103 checks
    python3 tools/section-audit.py --check     1,367 assertions
    python3 tools/ux-audit.py --check          421 assertions
    python3 tools/invariants.py --check        28 invariants
    node tools/browser-checks.js               ~1,820 checks

Routing, canonical URLs, structured data, image provenance, the CSP, the
planner, Discover Mode, search, My Europe, the map layers and the accessibility
contract are all asserted by those, and `routes.hash` is an invariant
specifically so that a restyle cannot move a URL.

---

## G · What moved in the registers, and why

A visual change here is a controlled experiment and `docs/invariants.json` is
the control. Moving one is allowed; moving one silently is not.

- `primitives.reach.pagehead` fell one page when `/interests` left the old head.
- `css.breakpoints` was held at six: a seventh was written and refused, and
  52rem already existed.
- `docs/palette.json` recomputes every contrast claim, forbidden pair and
  cartographic separation from the hexes in the stylesheet.

---

## H · Defects this work found by looking

Each of these was invisible to every counting check:

1. **The family accent painted a label the colour of its own ground.** Cobalt
   type on the cobalt journey hero, 1.00:1 — present, placed, keyboard
   reachable and unseeable.
2. **Two translucent layers over one another are a third tone.** The route
   drawing's land and its context ground both took 22% bone and overlap, so
   Europe came out at 39% against a 22% rectangle that read as a pasted panel.
3. **A framed drawing was refused the data-cut fade by a flag rather than a
   measurement**, so the longest journey drew a knife-straight diagonal
   through Russia.
4. **`height: 100%` against a `min-height` parent resolves to `auto`**, so a
   photograph sat at its intrinsic height with a band of `--paper-3` under it.
5. **A tag name cannot be the subject of a verb** — "What mountains looks like".
6. **A count cannot be dropped into a sentence that assumes a plural** — "1
   destination, the same ones".
7. **Two components each paying for the same gap** — 341 pixels between a lede
   and the next heading.
8. **A name in a meta row is not a byline** — the word that says so had gone.

9. **A colour sized on one ground fails on the other** — pine reads 4.93 on
   bone paper and 1.74 on graphite, so seventy of one browser run's 116
   failures were the wordmark, the current-section marker and the family
   eyebrows, all below AA for a reader in the dark preference.
10. **`1fr` is not `minmax(0, 1fr)`**, and an `<svg>` sized in percent still
    contributes 300 pixels to intrinsic sizing — a phone column came out
    304.609 inside 288 and the place family scrolled sideways.
11. **A page had two gutters** — `main`'s and the component layer's — so a
    band sat at 75px where an h1 on an older family sat at 24.
12. **A stroke in user units is not a stroke in pixels**, on a chart whose
    caption names the line and on the aperture's own cut edge.

And one the eye reported and the browser refused: the phone contact sheet
appeared to show the masthead navigation struck through the wordmark on six of
twelve families. Measured at 390, the wordmark ends at y=45 and the navigation
starts at y=53.

**Look to find, count to conclude** — and measure before you fix.

---

## I · What is still open, and who it is waiting on

Nothing here is blocked on code.

- **The photographs.** 1,626 declared surfaces, a handful licensed. The
  acquisition pipeline is built, gated and tested; `stage: fill` plans a
  tranche across every family and the workflow acquires, verifies, hashes,
  derives, registers and merges. It needs the branch merged and the workflow
  dispatched.
- **The eight benchmark sites** in `docs/first-class-audit.md` are blocked by
  the egress proxy, so that half of Finding 2 stays labelled second-hand.

---

## J · The test

*Would a design-led European cultural institution ship this?*

Run `node tools/contact-sheet.js` with `--set=1` through `--set=4` and look.
Before this work, eleven of twelve cells were the same page with different
words. The sheets now show a dark arrival, a cobalt journey field, a monument,
an instrument in graphite, a year band, a contents page, eight bars, seventeen
constellations and a warm parchment atlas — and the masthead is the only thing
they have in common, which is what *one institution, many rooms* means.
