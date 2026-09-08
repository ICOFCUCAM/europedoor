# §5 — European Future, audited

Measured on the running build, not proposed. The palette migration has already
happened; this is what it produced, what it did **not** touch, and what remains.

The governing constraint, restated because everything below is judged against
it:

> **2036 does not mean adding futuristic decoration. It means making the
> existing information architecture feel like a mature future European
> platform.**

The test for any change in this document: does it make the information easier
to read and act on? If it only makes the page look more like the future, it
does not go in.

---

## 5.1 Current tokens → target tokens

**Done.** The migration ran as one commit and the target *is* the current
state. What it produced:

| | |
|---|---|
| custom properties | 56 distinct, all in one `:root` block |
| raw palette | graphite · limestone · cobalt (3 variants) · lime · ultramarine · atlantic · terracotta |
| semantic layer | `--paper`, `--paper-2/3`, `--ink`, `--ink-2/3`, `--rule`, `--sea`, `--door`, `--signature`, `--warn`, and five `--map-*` |
| gold | **none.** Removed entirely; three checks keep it out |
| stylesheets | 1, 64 KB |

**The semantic layer is why the migration was one commit.** 240 rules consume
`--paper` and `--ink`; nothing consumes a raw hex. Rebinding what those names
resolve to changed every page, and the two worlds are the same mechanism used
twice.

## 5.2 The DISCOVER / INTELLIGENCE surface map

Built, shipped, and asserted in both colour-scheme preferences.

    DISCOVER — light, editorial            INTELLIGENCE — dark, luminous
      /                                      /map        route intelligence
      /countries · /europe/<country>         /plan       journey construction
      /europe/<country>/<region>             /my-europe  saved everything, Travel DNA
      /europe/.../<destination>              /search     search intelligence
      .../place/<place>                      /discover   filter intelligence
      /experiences · /stories · /events
      /themes · /europe-in/<motion>          and every embedded map figure,
      /method · /sources · /fund             wherever it sits
      /discover/<macro>

**The `/discover` split is deliberate and now settled.** `/discover` is a
filter interface — *filters → interpretation → results* — and belongs to
INTELLIGENCE. `/discover/<macro>` are editorial macro-region pages —
*photography → destinations → exploration* — and belong to DISCOVER. The
classification follows what the interface does, not what the route is called.

**An embedded map is INTELLIGENCE wherever it sits**, including inside an
editorial country page: a window into the machine, cut into a document. That
is the door as a design language rather than as a glyph.

## 5.3 Typography

| | |
|---|---|
| families | **3** — a display serif, a system sans, a mono |
| webfonts | **0**. No `@font-face`, no `fonts.googleapis.com`, no request |
| type-scale tokens | 11, `--t-xs` … `--t-6xl` |
| distinct `font-size` values in the whole stylesheet | **13** |
| font weights | 4 — 400, 500, 600, 700 |
| line heights | 4 — 1, 1.12, 1.25, 1.5 |
| measure | one token, `34rem` |

**Zero webfonts is a European Future decision, not a performance compromise.**
A system stack renders instantly, in every language the continent uses,
without a third-party origin — which is also what keeps `default-src 'none'`
intact. The display serif carries the editorial voice; the sans carries
everything a reader has to *use*.

**Nothing here is proposed to change.** Thirteen font sizes and four weights
is already tighter than most design systems arrive at after a year. The
sibling repository measures 418 font sizes.

## 5.4 Colour and contrast contracts

`docs/palette.json` is the contract: **31 claimed pairings and 10 explicit
refusals**, and `checks.py` recomputes every WCAG ratio from the hexes in the
file on every build.

The three rules that are arithmetic rather than taste:

- **Electric lime does not exist in the light world** — 1.09:1 on limestone.
  Not a policy; physics. It is therefore a reliable signal that the reader has
  crossed into INTELLIGENCE.
- **Ultramarine is never type** — it fails on every ground we hold. Gradients,
  map washes, atmosphere.
- **The signature is drawn, not read** — `#3157FF` is 4.04:1 on the deepest
  light surface. `--signature` for the mark and the score bars; `--door` for
  anything that is text.

Two failures are recorded in the palette file itself because they were caught
by the checks rather than by looking: `cobalt-lift` chosen against the dark
*ground* and failing on the dark *card*; and the accent bound to the signature,
failing seven pages at 4.36:1.

## 5.5 Photography and SVG

| | |
|---|---|
| licensed photographs | **0** |
| `<img>` tags in the whole site | **0** |
| inline SVG plates rendered | 2,377 |
| social cards | 794 PNGs, 5.5 MB, mean 7 KB |

Every illustration is a **generated plate**: a deterministic landscape from the
SHA-256 of a slug, with the motif taken from what the place actually is. The
European Future re-tone moved the hues from Atlantic teal-through-brick to six
cool steps around cobalt and ultramarine; night plates bottom out near graphite
with a lime light, day plates lift toward limestone under a low warm sun — the
single warm note in the system.

**The photography direction cannot be executed without a budget.** Free stock
covers the Eiffel Tower and will never cover Albarracín or Theth, which is
precisely the product. `docs/images.md` holds the pipeline, which is built and
enforced; the register is empty and says so.

## 5.6 Cards, rows, bands — the information surfaces

Eleven primitives, and their reach was measured in §4:

    kicker · masthead · pagehead · crumbs      100% of pages
    row / rows                                  91%
    note                                        81%
    card · plate                                78%
    band                                        76%
    facts                                       73%
    split / rail                                64%
    btn                                         58%
    chip                                        52%

**No new primitive.** The rule from §4 stands: name a primitive after
observing repetition, not before. Specifically, do **not** create a
`ResultCard` family — `ResultCard`, `AIResultCard`, `SmartResultCard`,
`JourneyResultCard` — for structure that has not appeared. If the planner, the
map and Discover Mode converge on *interpretation → results → actions*, that
shape gets named then, once, from the three real instances.

**What the European Future change did to these surfaces:** the primary button
became the signature colour (the most visible tenth of the 10% cobalt), the
source-tier badges lost brass for a neutral grey, and the score bars became a
`--sea` → `--signature` gradient. Nothing was restructured. That is the point:
the migration re-toned an information architecture rather than replacing one.

## 5.7 Navigation

| surface | treatment |
|---|---|
| masthead | one, sticky, `color-mix` on `--paper` at 88% with a backdrop blur; exactly 1.0 per page across 1,072 |
| breadcrumbs | on 100% of pages, and every JSON-LD `BreadcrumbList` is checked against the visible one |
| section nav | 319 destination pages; scrolls rather than wraps, asserted in Chromium |
| bottom navigation | phone only, below 44rem; `--thumbbar` is its height and four other offsets derive from it |
| footer | one, exactly 1.0 per page |

**The accent tells you where you are.** Within DISCOVER: cobalt for the
structural and geographic, terracotta for the cultural, atlantic green for
provenance. Within INTELLIGENCE: lime, always. A reader will never name this
and will feel it.

## 5.8 The map's visual language

Five tokens — `--map-sea`, `--map-land`, `--map-context`, `--map-border`,
`--map-hover` — kept together so the drawing can be re-toned in one place.

The design problem the map solves is that **a map with a basemap wants to look
like every other map with a basemap.** A tile-service pastiche — motorway
yellow, park green, a scale bar — would say EuropeDoor bought a map. Instead:
the sea is near-black, land is a shade above it, a country in the Atlas is a
shade above that, and the only saturated colour is the country under the
pointer and the destinations on it.

`--z` carries the zoom so every stroke and radius divides by it; without that a
1px border is 8px at 8× and the coastline eats the coast.

## 5.9 The planner's visual language

The largest application — 1,721 lines — and the one where visual language is
mostly *state* language: the staged wait, the honest refusal, the why-line on
every leg, the what-if preview shown before it is applied.

**Its visual job is to make reasoning legible**, not to look computational.
The refusal is a `note`, the legs are `row`s, the estimate is a `facts` list.
It uses the same eleven primitives as a destination page, in the dark world.

## 5.10 Mobile

| | |
|---|---|
| breakpoints | 6 — 40, 44, 52, 60, 62, 64 rem |
| sticky elements | 2 — the masthead and the destination action |
| `--thumbbar` | one token, consumed in 4 places |
| viewport tested | 390 × 844, on every page shape in the browser suite |
| horizontal overflow | **0 pages**, asserted statically *and* in Chromium |

**Two fixed bars, one token.** The first version hard-coded 44px for the
offsets while the bar rendered at 63, so the action sat on top of the
navigation. Only measuring both boxes in Chromium finds that — which is also
how the 204px overflow from making the map page two columns was found.

## 5.11 Social cards

794 PNGs at 1200×630, mean 7 KB, content-addressed and pruned. Every page
carries `og:title`, `og:description`, `og:url`, `og:image`, dimensions,
`og:image:alt` and `twitter:card=summary_large_image`.

**One drawing, two renderers.** `plate_shapes()` is the geometry; `plate()`
emits the SVG on the page and `raster.plate_png()` emits the card, through a
pure-Python PNG encoder. A check asserts both still come from the same
description — a card that stops matching its page is invisible from here,
because it renders inside somebody else's product.

The European Future re-tone flowed through automatically: one hue table, both
renderers, 794 cards regenerated in 18 seconds.

## 5.12 What remains unchanged, and why

| unchanged | why |
|---|---|
| the information architecture | §5's constraint: re-tone the IA, do not replace it |
| all eleven primitives' structure | measured to cover the site; only their tones moved |
| the type scale | 13 sizes, 4 weights, 3 families — already tighter than the target |
| zero webfonts | instant render, every European language, no third-party origin |
| the breakpoints | 6, and the phone is tested at every page shape |
| plate geometry | only the hues moved; the motifs still come from what a place is |
| `render.section()` and the shell | the lever stays a lever precisely because it is not special-cased |

## 5.13 Migration order — what is done and what is left

**Done, in this order, and each verified before the next:**

    1  tokens → European Future                  DONE
    2  DISCOVER / INTELLIGENCE classification    DONE
    3  contrast verification, both worlds,
       both colour-scheme preferences            DONE — 651 browser checks
    4  SVG plate re-tone                         DONE — 6 hues
    5  --map-* re-tone                           DONE — 5 tokens
    6  social card regeneration                  DONE — 794
    7  1,072 pages rebuilt and re-checked        DONE

**Left, and each blocked on something real rather than on effort:**

| left | blocked on |
|---|---|
| photography | a budget. `docs/images.md` |
| the flagship hero | the same budget — the described image is a commission, not a stock search |
| languages beyond English | ~359 English string literals in the page builders would need extracting first |
| motion and transitions | nothing, but §5's constraint applies: motion explains a relationship or it does not happen |

## 5.14 Red-team checks — what has been attacked, and went red

The standard carried forward from §4. Every one of these was performed and
watched failing before being trusted:

| attack | result |
|---|---|
| a `--brass` token reintroduced | red |
| a raw gold hex `#c2a165` in a rule | red |
| a gold the browser actually paints | red |
| a palette hex nudged "slightly warmer" | red — 2.52:1, claim refused |
| the accent bound to the signature | red — 7 pages at 4.36:1 |
| `cobalt-lift` chosen against the ground not the card | red — 4.07:1 |
| a second stylesheet | red |
| the type scale sprawled to 38 sizes | red |
| a sixth application script | red |
| an enhancement that starts fetching | red |
| an undeclared index dependency | red |
| a declared field removed from an index | red |
| "AI" placed in an `h1` | red |
| an inline `<style>` on a page | red |
| a second page shell | red |

**Fifteen deliberate attacks, fifteen red builds.** That is what makes the
numbers in the gate mean something.
