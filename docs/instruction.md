# The standing instruction

What follows applies to every session on this repository, not to one task. It
is in two halves because the work has two halves: **how a thing gets built**,
and **what it looks like when it is**. Both are written as rules with the
failure that produced them attached, because a rule without its failure is a
rule somebody argues with.

---

## Part 0 — settled, and not reopened

| | |
|---|---|
| **Name** | **EuropeDoor**. One word, title case. Never `Europe Door`, never `Europe Atlas`, never an alternative from an incoming strategy document. |
| **Positioning** | **Open the door to Europe.** |
| **Why not "Europe Atlas"** | Atlas is a reference product. A door is an experience. EuropeDoor is a destination platform, and the name has to say so. |
| **Trademark** | **NOT cleared.** EUROPEDOOR is in use in the doors and building-materials trade. No ®, no ™, no public announcement, no investment in registrable assets before formal clearance. See `docs/brand-lock.md`. |

The name being settled does not make the mark safe. Those are two different
facts and this file keeps them apart on purpose.

---

## Part 1 — how work is done here

### 1. Audit before building, and name what you looked at

Not "I reviewed the codebase". The specific things, and what each one turned
out to be. The map rebuild began with five: `package.json` (does not exist —
zero runtime dependencies), the CSP (`default-src 'none'`, no `unsafe-inline`
anywhere), the toolchain (no GDAL, no `ogr2ogr`, no `tippecanoe`, no
`shapely`), the storage (static files, `site/` committed, no object store), and
the existing implementation (313 dots on an empty rectangle).

Three of those five changed the plan. None of them would have been found by
reading the brief.

### 2. A specification is a brief, not a court order — but you deviate with numbers

The map brief named MapLibre GL JS. The measurement was: all of Europe's
borders at continent detail is 88 KB of JSON, ~34 KB drawn, and the coarse
level that ships inline is ~19 KB, against MapLibre's ~800 KB before any data.
Eight times the weight of everything it would render, plus WebGL, plus a build
dependency the repo does not have, plus the first hole in `default-src 'none'`.

That is a deviation you can defend. "It felt heavy" is not. **Measure, state
the number, state what would reverse the decision, then build.** The reversal
clause matters as much as the number: `data/geo/` stores lon/lat rather than
pixels precisely so that the day roads and trails arrive, the expensive parts —
clipping, simplification, the level-of-detail ladder — are already done.

### 3. STOP on licensing, money, law and anything hard to undo

Not "flag it and continue". Stop, answer seven questions, wait:

    1. the dataset or service involved
    2. its licence or terms
    3. what we want to do with it
    4. the obligations that creates
    5. the alternatives, including shipping without it
    6. the estimated infrastructure cost
    7. a recommendation

Eurostat NUTS is the worked example (`docs/data-licenses/eurostat-gisco-nuts.md`).
Its data is copyrighted and *"usage of these data is subject to their
acceptance"* — a person accepting terms, not a script fetching a file — and the
terms page was unreachable from the build environment. So nothing was
imported, the seven answers were written down, and the product shipped without
region boundaries. **A summarised licence you could not read is a fabrication
with a citation on it.**

### 4. Never invent data to fill a gap

Monaco is 2 km² and Vatican City is 0.44 km². At 1:50 million neither has a
polygon. They are drawn as a ringed point and the legend says why. Drawing an
outline would have taken four minutes and would have been a lie about a
measurement that a reader has no way to catch.

The same rule produced: no crowd proxy, no seeded businesses, no
`aggregateRating` in structured data, no region boundary hulled out of the
destinations inside it. **A gap stated is worth more than a gap filled.**

### 5. Every claim gets a check, and the check gets shown to fail

"EuropeDoor does not pay for maps" is now 1,249 assertions in `checks.py`,
including a hostname list that fails the build on any page or script naming a
commercial map provider or public tile server. It was verified by planting a
Mapbox URL and watching it go red, by making `data/geo/` stale, and by
corrupting a recorded hash.

A green check nobody has seen fail is a green check that may not be checking
anything. This repository has already shipped a browser suite that printed
*"all 4 browser checks passed"* while 540 ran, because a `const` shadowed the
counter. **Prove the check can go red in the same session you write it.**

### 6. Report every bug the work surfaced, including yours

The map rebuild is on record as having found three: a projection that
multiplied x by `cos(52°)/cos(52°)` and had therefore drawn Europe 60% too wide
for a year; 204px of phone overflow introduced by that same session's two-column
layout; and a page called "the map" that opened with no map on it. One was
inherited, one was self-inflicted, one was a design failure. All three are in
the commit message.

**Prefer recording a mistake to quietly deleting the evidence of it.** The note
in the CSS about the 47px overflow is worth more than the two lines that fixed
it.

### 7. Zero recurring cost is the default

A bill is the owner's decision, never a convenience. Where a free path exists
and costs operational work instead, take the operational work and write down
the pipeline so somebody can rebuild it. Where no free path exists, stop —
see rule 3.

---

## Part 2 — the visual instruction: European Future

### The philosophy

**Editorial × Architectural × Cinematic × Intelligent.**

Not "a nice futuristic travel website". The interface to a new way of
experiencing Europe. The future is communicated through materials, light,
architecture, typography and restraint — never through neon, never through
glass panels, never through gradients used as decoration.

### The two worlds

The platform is not one dark futuristic surface. It alternates, and the
contrast between the two is meant to be one of the defining characteristics of
the product.

| | **WORLD 01 — DISCOVER** | **WORLD 02 — INTELLIGENCE** |
|---|---|---|
| feel | light, warm, editorial, human | dark, graphite, quietly luminous |
| holds | photography, architecture, food, culture, journeys, cities | maps, routes, planning, personalisation, live information |
| ground | Warm Ivory | Deep Graphite |
| purpose | where people fall in love with Europe | where people meet the machine behind it |

A surface belongs to one world. It does not blend them, and it does not switch
worlds because a component was convenient.

### The palette

Canonical values live in `docs/palette.json`, which is checked. This table is
the readable copy; if the two disagree, the JSON is right and this table is a
bug.

| token | hex | what it is |
|---|---|---|
| Deep Graphite | `#101214` | the technological foundation. Ink in the light world, ground in the dark |
| Graphite Surface | `#1A1E22` | cards and raised surfaces in the dark world |
| Warm Ivory | `#F5F2EA` | the main surface. **Never pure white** — white is a screen, ivory is paper |
| Stone / Mineral | `#D9D5CC` | cards, structural elements, rules |
| **European Cobalt** | `#3157FF` | the signature. Sparingly, and never as a background |
| Cobalt Deep | `#2A4AD9` | links and actions in the light world |
| Cobalt Lift | `#627FFF` | links and actions in the dark world |
| **Electric Lime** | `#C8FF4D` | the future accent. **Dark world only** |
| Ultramarine | `#665CFF` | atmosphere only: gradients, map washes, immersive moments |

### The ratio is the instruction, not the hex codes

    60%  warm light / ivory
    25%  graphite
    10%  cobalt
     5%  electric accent

A palette gives you *blue website with gold buttons*. A ratio gives you
*European editorial design over futuristic digital infrastructure*. If a screen
does not hold roughly this distribution, the palette has been applied and the
instruction has not.

### Where each colour may go, measured rather than asserted

WCAG 2.2, AA: body text needs 4.5:1, large text and UI edges need 3:1. These
are computed, and `checks.py` recomputes them from `docs/palette.json` on every
build — so a hex nudged "slightly warmer" in a redesign cannot quietly take a
contrast ratio with it.

|  | on ivory | on graphite | on stone |
|---|---|---|---|
| Graphite | **16.78** | — | **12.82** |
| Ivory | — | **16.78** | — |
| Cobalt `#3157FF` | **4.77** ✓ | 3.52 ✗ text | 3.64 ✗ text |
| Cobalt Deep `#2A4AD9` | **6.09** ✓ | — | **4.66** ✓ |
| Cobalt Lift `#627FFF` | 3.13 ✗ text | **5.36** ✓ | — |
| Electric Lime `#C8FF4D` | **1.05 — invisible** | **15.97** ✓ | **1.25 — invisible** |
| Ultramarine `#665CFF` | 4.13 ✗ | 4.06 ✗ | 3.16 ✗ text |

Three consequences that are not negotiable, because they are arithmetic:

- **Electric Lime does not exist in the light world.** At 1.05:1 on ivory it is
  not a subtle accent, it is nothing at all. This is not a constraint on the
  two-worlds idea — it is the two-worlds idea enforced by physics, and it makes
  lime an unmistakable signal that you have crossed into INTELLIGENCE.
- **Ultramarine is never type.** It fails on every ground we have. It is a
  gradient, a map wash, a glow behind a route. The moment a word is set in it,
  somebody cannot read that word.
- **Cobalt needs two variants.** The signature `#3157FF` reads on ivory and
  nowhere else. `cobalt-deep` carries links on stone; `cobalt-lift` carries them
  on graphite. A single "brand blue" used everywhere fails two of three
  surfaces.

### The door is a design language, not a logo

    DISCOVER → PLAN → ENTER → EXPERIENCE

The door is *transition*. A user moves curiosity → discovery → planning →
journey → experience → memory, and the interface should make each of those
crossings feel like passing through something. Openings, thresholds, framed
views, a change of world. Not a door glyph stamped on a header.

### Photography

Cinematic, authentic, human, architectural. A vast contemporary European
opening, and beyond it the Mediterranean, the Alps, a historic city, modern
architecture, people moving naturally, morning or evening light — integrated,
not collaged. No tourist in front of the Eiffel Tower. Nothing that reads as
AI-generated.

Every image still needs a photographer, a source and a licence
(`docs/images.md`). The art direction does not soften that rule; it makes it
more expensive.

### AI is invisible infrastructure

The customer never sees `AI EUROPE TRAVEL PLATFORM`. They see **EuropeDoor**,
and then they experience intelligence:

> *Where should I go?* — EuropeDoor understands.
> *I have six days.* — EuropeDoor builds the journey.
> *Mountains, food, history.* — EuropeDoor connects the places.
> *I land in Vienna on Thursday.* — EuropeDoor knows what is around me.

The assistant is named **EuropeDoor Guide**. The letters "AI" do not appear in
the masthead, the navigation, or any `h1`. A check enforces that, because it is
the single easiest thing for a well-meaning person to add.

### The avoid list

    ✗ navy + gold as the primary pair       ✗ excessive gradients
    ✗ generic tourism blue as a background  ✗ glassmorphism
    ✗ gold or brass on anything interactive ✗ stock-tourist photography
    ✗ neon cyberpunk                        ✗ imagery that reads as AI-generated
                                            ✗ "AI" anywhere in the branding

---

## Part 3 — what this changes, and what is not done

**One correction, for the record.** The instruction above opens by rejecting a
blue/gold identity. The built site is not blue/gold and never has been: the
current tokens are limestone `#F7F6F3`, Atlantic green `#14483C` and terracotta
`#A4491F`, with a brass `#8A6D34` reserved for heritage moments and forbidden
on anything interactive — a palette chosen specifically to avoid EU blue and
gold. The critique appears to be of a mockup rather than of the running
product. That does not make the new direction wrong; it means the migration is
**green → graphite**, not **blue → graphite**, and the two are different pieces
of work.

**What this document does today.** It settles the name, the positioning, the
philosophy, the two worlds, the palette, the ratio, the accessibility limits,
the door as a design language, the photography direction and the avoid list. It
makes the palette machine-checkable. It does not repaint anything.

**What the migration would take.** One stylesheet holds every token
(`assets/css/europedoor.css`), so the token swap itself is small. What is not
small:

1. Deciding which of the existing surfaces belong to DISCOVER and which to
   INTELLIGENCE — the map, the planner and My Europe are the obvious
   INTELLIGENCE candidates, and that is a product decision, not a CSS one.
2. Re-verifying every colour pair in both schemes; the browser suite already
   checks WCAG contrast and has previously darkened two tokens for failing it.
3. The generated SVG plates, the social cards and the map's five `--map-*`
   tokens all derive from the palette and would need re-toning together.
4. 1,072 pages regenerated and re-checked.

**Open, and the owner's:**

- Approve the green → graphite migration, and the DISCOVER / INTELLIGENCE split
  of the existing surfaces.
- Import Eurostat NUTS, or take Natural Earth admin 1 as the cheaper unblock
  for region shapes (`docs/data-licenses/eurostat-gisco-nuts.md`).
- The photography budget (`docs/images.md`). Free stock covers the Eiffel Tower
  and will never cover Albarracín or Theth, which is precisely the product —
  and it will certainly never cover the hero described above.
