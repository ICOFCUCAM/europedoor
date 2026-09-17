# /countries — the European Atlas

The brief: *"Discover = Let Europe answer. Countries = Know the continent."*
Its grammar is **CONTINENT → MAP → COUNTRY → INDEX → REGIONS → PHOTOGRAPHIC
ATLAS → FINAL**, and its central instruction is a refusal:

> Countries is not a directory of 50 destinations. It is EuropeDoor's living
> digital atlas: geography first, country second, photography third, index
> fourth. The map provides authority, photography provides emotion, and the
> index provides navigation. Build those as distinct layers and do not
> collapse them into generic cards.

It also says what not to do: no `[France] [Germany] [Italy]` grid, no
50-image card gallery, no dark instrument map, and — explicitly — *"Claude
should not invent these paths or introduce a new image system"*, but connect
to the photography registry, the provenance records, the existing
derivatives, the country data and the existing EPSG:3034 geometry.

This document is Part 1 before any code, which is how this repository works:
audit first, deviate with numbers.

## Part 1 — the source audit

`pages.countries_index` today is **not** a plate sequence, which every other
rebuilt index now is. It is `ed_opening()` followed by two `ed_section`s and
a closing `.small` note:

| | |
|---|---|
| **opening** | eyebrow *The Atlas*, h1 *"Europe, country by country."*, an intro stating 9 / 50 / 130 / 319, and the `countries-hero` photograph |
| **the continent** | `region_glyph(all 50)` — every country drawn on its own with its frontier — two buttons, and one sentence saying Russia's outline stops at the data cut rather than at a border |
| **the Atlas** | nine `band macroband` sections, each a macro glyph beside `ed_rows` of its countries |
| **closing** | a `.small` paragraph on why a macro region may have a boundary and a travel region may not |

Measured on the built page: **83,169 bytes, 1 `<img>`, 17 `<svg>`, 209 rows,
11 `<h2>`, 0 declared slots.**

The data behind it: **50 countries, 9 macro regions, 130 travel regions, 319
cities**, and three advisory countries (Belarus, Russia, Ukraine). A country
record carries `blocs`, `budget`, `capital`, `code`, `currency`, `daily_eur`,
`festivals`, `food`, `getting_around`, `interests`, `know`, `languages`,
`official`, `regions`, `season`, `summary` and `tagline` — so there is real
encyclopedic material, and the page prints a tagline and two counts of it.

## Part 2 — the image-coverage audit, and this is the largest gap yet

The standing answer to *"why does a travel site have so few pictures"* is the
register. On this page it does not apply, and the margin is wider than on
/experiences or /stories:

| the register holds, for this page | |
|---|---:|
| `country:<slug>` — one photograph per country | **50 of 50** |
| `macro:<slug>` — one per macro region | **9 of 9** |
| `countries-hero` | 1 |
| **total relevant to /countries** | **60** |
| **what the page draws** | **1** |

Every one of the fifty countries this atlas has written about has a licensed
photograph, and the page about the fifty countries shows one picture. The
nine macro photographs each appear on exactly one page — their own macro
page — and the band on /countries whose entire subject is those nine macro
regions draws none of them.

That is the /experiences finding and the /stories finding a third time, at
the largest scale on the site. **Nothing needs to be acquired.**

## Part 3 — the mechanism the brief asks for already exists

The brief's strongest idea is this:

> When the visitor selects France, the actual country polygon on the
> EPSG:3034 map should become the visual focus. The photograph can then
> transition inside France's geographic boundary. … So the country itself
> becomes the aperture. This also connects beautifully with the EuropeDoor
> name.

`pages.living_atlas()` and `pages.heroeurope()` **already do exactly that**,
on the homepage: a `<clipPath>` built from the country's own drawn path, and
an SVG `<image>` clipped to it at `preserveAspectRatio="xMidYMid slice"`, so
the photograph is the country FILLED rather than a picture pasted on a map —
with the frontiers, the rivers, the names and the dusk drawn over it. It is
the same geometry as the country under it, deliberately: *a second
simplification would differ by a tenth of a unit and show as a fringe along
every frontier.*

So the brief's instruction not to introduce a new image system is not a
constraint here, it is the answer. Measured:

| | |
|---|---:|
| countries `living_atlas` returns an aperture for | **41** |
| of those, `featured` (cycling their own destinations) | 6 |
| countries with a photograph but no aperture | 9 |
| drawn width on the hero frame: min / median / max | 8 / 69 / 265 units |

The nine without one are **Belarus, Russia and Ukraine** — excluded by
`if (c.get("advisory") or {}).get("level")`, deliberately — and **Andorra,
Liechtenstein, Malta, Monaco, San Marino and Vatican City**, which have no
drawn path at `min_units=6.0`. The last six are the same six this repository
already records as having no polygon at 1:50m at all, drawn as a ringed
point. A country with no polygon can never be an aperture, and that is a
fact about the dataset rather than a decision about the country.

**AND THE FUNCTION'S OWN COMMENT OVERSTATES IT BY NINE.** It reads *"EVERY
COUNTRY THAT HAS A PHOTOGRAPH IS AN APERTURE, AND ALL FIFTY DO"* and the
function returns 41, because two filters below that sentence remove the
advisory three and the polygon-less six. Both filters are right; the sentence
is not. *The code had stopped matching its own comment* is already recorded
here about a `[:8]` on the homepage, and this is the same shape in the other
direction — a comment claiming more than the code delivers reads as evidence.

**AND THE CONTINENTAL FRAME IS WHY THE HOMEPAGE COULD ONLY USE SIX.** That
page's own recorded measurement: *a photograph clipped into Belgium renders
about 40 pixels wide at 1280 and is a smudge with a coastline.* At roughly
one pixel per unit, Luxembourg is 8 units and Monaco is not drawn at all. So
on one continental frame the aperture is legible for large countries and
nothing else — which is a property of the FRAME, not of the idea. Framed on
its own extent, as the nine macro glyphs and the fifty country portraits
already are, Luxembourg fills its tile exactly as Türkiye fills its own.
That is the departure this page gets to make and the homepage could not.

## Part 4 — what is known before anything is built

- The library is not the constraint: 60 relevant photographs, 1 drawn, 0 to
  acquire.
- The mechanism is not a new one: `living_atlas`'s clip-path aperture.
- The frame is the variable: continental for authority, own-extent for
  legibility.
- Six countries can never be an aperture and three are refused one; nine of
  fifty, and the page has to say so rather than quietly show 41.
- 19 distinct initials over 50 names, so an A–Z index is 19 groups, not 26 —
  S holds seven and A holds five.
- The brief's *"no photographer/source credits visually inserted merely
  because an image originated from Pexels"* is the owner's standing position,
  and this site already answers it five times with `sheetcred rowcred`: the
  attribution is paid once under a row of pictures, never once per picture.

## Part 5 — what was built: seven plates

The brief's architecture is CONTINENT → MAP → COUNTRY → INDEX → REGIONS →
PHOTOGRAPHIC ATLAS → FINAL, and all seven are on the page in that order.
`pages.plate_sequence()` renders them, so the numbering comes from the
*rendered* sequence rather than the declared list — the mistake recorded one
family over, where `enumerate(PLATES, 1)` filtered afterwards and the
homepage printed 01, 02, 05, 06, 07, 08.

| plate | room | what it is |
|---|---|---|
| 01 · The continent | `gal` | *Europe, country by country.* over the index's own photograph, with the extent beside it |
| 02 · Where the countries sit | `paper` | all fifty drawn on the EPSG:3034 conic, each on its own frontier, nothing filled by a dot |
| 03 · The country as the door | `gal` | France's outline as a clip-path with a photograph of France inside it |
| 04 · The index | `gal quiet` | nineteen letter groups, the `pagehead index` and the derived extent |
| 05 · The nine regions | `gal` | nine bands, each a macro photograph, its glyph and its countries as rows |
| 06 · Filled | `paper` | ten apertures, largest photographic holding first |
| 07 · Which door | `gal` | one question and nothing else |

**THE OPENING IS A LIGHT MAP ON AN ALMOST-WHITE FIELD, WHICH IS WHAT THE
BRIEF ASKED FOR AND WHAT THE PALETTE ALREADY HELD.** *"I would use a large
light European map, not the dark instrument treatment. The map sits on an
almost-white field."* The owner's palette split the cartography months
earlier — `#D8D4C7` land on `#DDE8E7` water for a picture, `#F3F0E6` on
`#07100F` for an instrument — so this is a binding rather than a new colour.
`.atlasmap` caps the drawing at `min(100%, calc(72vh * 1000 / 780))`, because
the glyph space is 1000×780 and a percentage cap alone letterboxes: *a map
card is not 16:9, and the letterbox was invisible because it was the same
sea.*

**AND THE COUNTRY IS THE APERTURE, WHICH IS THE BRIEF'S STRONGEST IDEA AND
WAS ALREADY A MECHANISM HERE.** *"When the visitor selects France, the actual
country polygon on the EPSG:3034 map should become the visual focus. The
photograph can then transition inside France's geographic boundary … So the
country itself becomes the aperture."* `living_atlas` had built exactly that
clip-path for the homepage and it was measured out there, because on one
continental frame *a photograph clipped into Belgium renders about 40 pixels
wide and is a smudge with a coastline*. `country_door()` is the same
mechanism on the country's **own** extent, so Estonia fills its tile as
France fills its own — the frame was the variable, not the idea.

**NOTHING WAS ACQUIRED AND THE PAGE DREW ONE PICTURE BEFORE THIS.** 1 `<img>`
to 10, plus 10 SVG `<image>` inside the apertures, out of the 60 photographs
the register already holds for this page's subject. That is the /experiences
and /stories finding for the third time: *the pictures were already bought and
were being spent on one surface.*

## Part 6 — the things only rendering and measuring found

**THREE CLASS-NAME COLLISIONS, CAUGHT BY GREPPING BEFORE A LINE OF CSS WAS
WRITTEN.** `.sheet-door` is the homepage's opening and carries 29 rules;
`.doorgrid` already exists twice; `.sheet-open` is shared with /stories. All
three were the obvious names. This is the fifth page in a row to hit *a class
name already in the stylesheet is a rule you inherit silently*, and the first
where the answer was cheap, because the file was searched first: the
compositions are `sheet-aperture`, `doorstack` and `atlasopen`. **And the
first rename went to the wrong occurrence** — `.doorgrid` at line 1822 is the
homepage's and line 2477 is this family's, so a grep that finds two matches
still needs the right one read.

**A BLACK SEA ON EVERY COUNTRY DOOR.** `.instrmap svg { background: none }`
is correct — *a map figure must paint no background* — so the aperture's own
`<rect class="lyr lyr-ocean">` had nothing to fill it with and rendered at the
SVG default, which is black. The plates escape this because they carry the
cartography skin; a new figure inherits the geometry rules and not the paint.
`.countrydoor .lyr-ocean { fill: var(--atlas-sea) }`, which is the same
finding as the ten `<stop>` elements no rule reached.

**TEN IDENTICAL CAPTIONS, TEN IDENTICAL SOURCE NOTES AND TEN IDENTICAL ALT
TEXTS.** *Never explain the constraint back* — the reason the country is an
aperture belongs once, above the band, not under each of ten drawings.
`country_door(brief=)` carries the sentence on the lead door and the country's
bare name on the other nine, and the alt text left the caption entirely
because the `aria-label` on the `<svg>` already says it.

**`--warn-ink` HAS NEVER EXISTED.** The token is `--warn`. Caught by the
unresolvable-`var()` scan in the first run — which is the whole argument for
that four-line check, because *an unresolvable `var()` is not a missing value,
it is a different one* and the advisory marker would have inherited the row's
own ink and looked deliberate.

**A LINE-HEIGHT ONE HUNDREDTH FROM AN EXISTING ONE.** `.doorsay .dsay` was
written at `1.24` and `css.line_heights` went to nine against a ceiling of
eight. 1.25 was already in the scale and is indistinguishable; a ninth value
would have been *a rounding error with a token name*.

**A MAP WITH NO DECLARED ROLE.** `data-role="illustration"` was put on the
`<figure>` and the check reads the `<svg>`. One attribute, one element out.

**THE PAGE MEASURED 30,759 PIXELS BEFORE ANY OF ITS CSS EXISTED**, because
every new composition fell back to block flow. 30,759 → 19,306 → 18,569 at
1280. That is not a defect so much as the reason a plate sequence cannot be
judged from its markup.

**AND THE BYTE BUDGET'S OWN REASON NAMED A DOOR THAT IS NEVER DRAWN.** The
comment on `DOOR_BAND_KB` said *"Russia's outline alone is 107 KB"* — and
Russia is advisory, so `country_door()` refuses it before geometry is read.
Measured: 41 drawable doors are **628 KB** against a `weight.max_page_kb` of
441, and the costliest is **Norway at 62 KB**. The budget is right and its
stated evidence was about a case the function excludes. *A comment claiming
evidence is read as evidence.*

## Part 7 — what the register moved, and why each move is deliberate

| invariant | from | to | why |
|---|---|---|---|
| `safety.img_tags` | 1196 | 1205 | the nine macro photographs. The ten apertures are SVG `<image>` and this figure does not count them |
| `primitives.reach.ed-opening` | 0.454 | 0.453 | one page: `/countries` stopped calling `ed_opening()` |
| `primitives.reach.ed-section` | 0.835 | 0.834 | the same page, same reason |
| `primitives.reach.band` | 0.768 | 0.767 | **a repair, not a migration** |

The last one is the interesting one. The nine macro regions were
`<section class="band macroband">` with their head inside a `.bandtop`
wrapper, so `.band > .band-head::before` never matched them — **nine silent
increments** of the counter that numbers every other section on the site, and
the two numbered sections after them would have printed "010" and "011". That
is *the selector that COUNTS is the selector that DRAWS*, recorded one commit
earlier and live on this page the whole time. They are plate bands now and
they neither count nor draw an index.

**And the extent had to move with the composition.** A plate sequence has no
room for a stage above its opening, so `checks.py` failed on *no page head*
and *no extent* — the same pair /journeys and /experiences already answered.
The A–Z band carries `<div class="pagehead index">` and states the derived
count, because *an index exists to say how big a set is*.
