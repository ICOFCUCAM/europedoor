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

### 4. The Data Integrity Rule: never author a measurement; you may author a classification

The distinction is the difference between a fact about the world that somebody
measured and a judgement this atlas is qualified to make.

    A MEASUREMENT is derived, carries its source, and is absent where
    there is none.
        population · coordinates · iso3 · distance · a transport node

    A CLASSIFICATION may be authored, because it IS the editorial work.
        village · valley · island · archaeological site · region type ·
        story section · what an experience is for

Authoring `"Italy has an authenticity score of 87"` is inventing a
measurement. Authoring `"Theth is a village"` is doing the job. The validator
enforces the first half by refusing `iso3`, `lat`, `lon` and `population` as
authored keys anywhere in `data/`, and enforces the second by requiring every
authored classification to come from a stated vocabulary.

### 4a. A reputable dataset can still systematically bias the product

Natural Earth was not wrong. It simply was not built to answer the question
this atlas asks. Its populated-places file is, by construction, a list of
populated places — so deriving `city_type` from it produced **one village in
157**, and the destinations it could not classify were disproportionately the
villages, valleys and sites. That is the product's whole thesis, silently
under-served by its own data pipeline, and the only thing that found it was a
check asserting a fact about the output rather than about the code.

The correct pipeline, and the order matters:

    external dataset → derived classification → validation →
    author correction → published classification

Never stop at "derived". A derivation's coverage is a claim about the source,
not about the world, and the gap between the two is where the product lives.

### 5. Never invent data to fill a gap

Monaco is 2 km² and Vatican City is 0.44 km². At 1:50 million neither has a
polygon. They are drawn as a ringed point and the legend says why. Drawing an
outline would have taken four minutes and would have been a lie about a
measurement that a reader has no way to catch.

The same rule produced: no crowd proxy, no seeded businesses, no
`aggregateRating` in structured data, no region boundary hulled out of the
destinations inside it. **A gap stated is worth more than a gap filled.**

### 6. Declare every dependency that crosses a boundary

> No consumer may depend on a field belonging to another index unless the
> dependency is declared in `data/contracts.json` and checked.

Coupling is not the problem; **silent** coupling is. Do not remove a
dependency because coupling sounds bad — make it visible and testable, so the
build forces the consumer and its contract to be updated together.

The live case: the search index carries live counts, and the empty state
prints them. That is correct — the alternative is a number typed into a
JavaScript file, which is what it used to be, and it said "244 cities" while
the atlas held 319. What was wrong was that nothing declared it: splitting the
index would have broken a sentence in a UI with no test failing.

The check runs both ways — a declared field that vanishes, and an undeclared
fetch that appears — and a dependency must carry a *reason*, because one
without a reason is one nobody can ever decide to remove.

### 7. Every claim gets a check, and the check gets shown to fail

"EuropeDoor does not pay for maps" is now 1,249 assertions in `checks.py`,
including a hostname list that fails the build on any page or script naming a
commercial map provider or public tile server. It was verified by planting a
Mapbox URL and watching it go red, by making `data/geo/` stale, and by
corrupting a recorded hash.

A green check nobody has seen fail is a green check that may not be checking
anything. This repository has already shipped a browser suite that printed
*"all 4 browser checks passed"* while 540 ran, because a `const` shadowed the
counter. **Prove the check can go red in the same session you write it.**

### 8. Report every bug the work surfaced, including yours

The map rebuild is on record as having found three: a projection that
multiplied x by `cos(52°)/cos(52°)` and had therefore drawn Europe 60% too wide
for a year; 204px of phone overflow introduced by that same session's two-column
layout; and a page called "the map" that opened with no map on it. One was
inherited, one was self-inflicted, one was a design failure. All three are in
the commit message.

**Prefer recording a mistake to quietly deleting the evidence of it.** The note
in the CSS about the 47px overflow is worth more than the two lines that fixed
it.

### 9. Zero recurring cost is the default

A bill is the owner's decision, never a convenience. Where a free path exists
and costs operational work instead, take the operational work and write down
the pipeline so somebody can rebuild it. Where no free path exists, stop —
see rule 3.

### The order of authority

The methodology this session settled on, written down because the opposite is
the default:

    PRODUCT PRINCIPLES
          ↓
    BUILT SYSTEM
          ↓
    MEASUREMENTS
          ↓
    CHECKS
          ↓
    ARCHITECTURE
          ↓
    FUTURE EXTENSIONS

**Not** architecture document → force implementation → find reasons to justify
it. A blueprint is a hypothesis. When the running system disagrees with it,
the running system is the evidence and the blueprint is the thing that
changes — provided the disagreement is measured rather than asserted.

Three things in this repository exist because that order was followed: the map
is SVG rather than MapLibre (88 KB of data against 800 KB of renderer);
Postgres is not built (0.17 ms for the query it would accelerate); and the
`relationships` table was replaced by a derived index (an authored edge table
cannot be validated).

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
| Deep Graphite | `#101214` | the intelligence foundation. Ink in the light world, ground in the dark |
| Graphite Surface | `#1A1E22` | cards and raised surfaces in the dark world |
| **Limestone** | `#F7F6F3` | the DISCOVER ground, kept from the previous system. **Never pure white** |
| Limestone Surface | `#EEECE7` | cards and raised surfaces in the light world |
| **European Cobalt** | `#3157FF` | the digital signature — for things **drawn**, not read |
| Cobalt Deep | `#2A4AD9` | every cobalt that is text or an action, in the light world |
| Cobalt Lift | `#627FFF` | links and interactive elements on dark surfaces |
| Atlantic Green | `#14483C` | heritage and provenance. The previous primary, retained with a narrow home |
| Terracotta | `#A4491F` | the warm cultural accent |
| **Electric Lime** | `#C8FF4D` | the dark-world signal. INTELLIGENCE only |
| Ultramarine | `#665CFF` | atmosphere only: gradients, map washes, immersive moments |
| ~~Gold / Brass~~ | — | **none.** See below |

### There is no gold

Brass `#8A6D34` was the only gold in the previous system, it was already
forbidden on anything interactive, and European Future removes it outright.
The one place it survived — the "computed" tier on a source badge — is a
neutral grey now, which is also more honest about what that tier is.

Gold says *luxury · premium · heritage · wealth*. This product has to say
*Europe · discovery · movement · intelligence · culture · future*. Gold
against anything reads as a luxury travel agency; cobalt against graphite
reads as European digital infrastructure. `checks.py` fails the build on a
gold or brass token **and** on a raw gold hex smuggled into a rule — verified
by reintroducing `#8a6d34` as a token and `#c2a165` as a value, and watching
both go red.

### Three accents inside DISCOVER, one inside INTELLIGENCE

The accent says what **kind** of thing is being read. A reader will never name
this and will feel it: an essay about a festival should not be the same blue
as a boundary dataset.

| accent | colour | where |
|---|---|---|
| structural | Cobalt Deep | the default — homepage, countries, regions, destinations, journeys |
| cultural | Terracotta | stories, events, experiences — the human half of DISCOVER |
| heritage | Atlantic Green | how this project knows what it claims: `/method`, `/sources`, `/fund`, `/sources/freshness` |
| electric | Electric Lime | **INTELLIGENCE only**, in every colour-scheme preference |

Bound by the nav area the shell already sets, so most of it cost no page
change. Setting it surfaced a navigation bug that had been there for months:
`stories` and `events` passed no area at all, so the masthead never marked
either section as current. The accent depended on it, which is how it showed.

### The ratio is the instruction, not the hex codes

    60%  limestone
    25%  graphite
    10%  cobalt
     5%  the accent

A palette gives you *blue website with gold buttons*. A ratio gives you
*European editorial design over futuristic digital infrastructure*. If a
screen does not hold roughly this distribution, the palette has been applied
and the instruction has not.

The most visible tenth of that cobalt is the primary button. A graphite button
is correct and says nothing, and a signature that never appears on the one
thing the reader is meant to press is a signature that exists only in the
documentation.

### Where each colour may go, measured rather than asserted

WCAG 2.2, AA: body text needs 4.5:1, large text and UI edges need 3:1. These
are computed, and `checks.py` recomputes all thirty-one claimed pairings from
`docs/palette.json` on every build — so a hex nudged "slightly warmer" in a
redesign cannot quietly take a contrast ratio with it.

| | on limestone | on the light card | on graphite |
|---|---|---|---|
| Graphite | **17.37** | **15.90** | — |
| Limestone | — | — | **17.37** |
| Cobalt `#3157FF` | 4.93 | 4.52 | 3.52 ✗ |
| Cobalt Deep `#2A4AD9` | **6.31** ✓ | **5.78** ✓ | — |
| Cobalt Lift `#627FFF` | 3.13 ✗ | — | **5.36** ✓ |
| Atlantic `#14483C` | **9.61** ✓ | **8.80** ✓ | 1.81 ✗ |
| Terracotta `#A4491F` | **5.47** ✓ | **5.01** ✓ | 3.17 ✗ |
| Electric Lime `#C8FF4D` | **1.09 — invisible** | 1.13 — invisible | **15.97** ✓ |
| Ultramarine `#665CFF` | 4.28 ✗ | 4.15 ✗ | 4.06 ✗ |

Five consequences that are not negotiable, because they are arithmetic:

- **Electric Lime does not exist in the light world.** At 1.09:1 on limestone
  it is not a subtle accent, it is nothing at all. This is not a constraint on
  the two-worlds idea — it is the two-worlds idea enforced by physics, and it
  makes lime a reliable signal that the reader has crossed into the machine.
- **Ultramarine is never type.** It fails on every ground we hold. It is a
  gradient, a map wash, a glow behind a route. The moment a word is set in it,
  somebody cannot read that word.
- **The signature is a drawn colour, not a read one.** `#3157FF` is 4.93 on
  limestone, 4.52 on a card and 4.04 on the deepest light surface. It belongs
  to the mark, the score bars and the dots on the map; anything cobalt that is
  *text* is `cobalt-deep`. This was learned the hard way — see below.
- **Atlantic and terracotta both lift at night.** `#14483C` is 1.81:1 on
  graphite and `#A4491F` is 3.17:1: a heading nobody can see, and one that is
  nearly invisible. The lifted values are the ones the previous system already
  used at night, which is the one piece of the old palette's homework that
  carried straight across.
- **A dark palette has two backgrounds, and the lighter one binds.**
  `cobalt-lift` was first set at `#5070FF`, which clears AA on the graphite
  ground at 4.56:1 — and falls to 4.07:1 on the raised card surface, where
  links actually sit. It is `#627FFF`, chosen against the card.

### Two failures worth keeping

Both were caught by a check rather than by looking, which is the argument for
the checks.

**The palette register caught its own author on its first run**, on the
cobalt-lift value above.

**The browser suite failed seven pages** when the accent was first bound to
the signature `#3157FF`: 4.93 on the ground, but 4.36 on the card ground the
kickers actually sat on. That is the instruction's own sentence — *the
signature reads on the ground and nowhere else* — arriving as a build failure
three paragraphs after it was written. Which is what a check is for.

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

## Part 3 — what the migration did

**The correction that shaped it.** The direction arrived rejecting a
blue/gold identity. This site has never been blue/gold: it was limestone,
Atlantic green and terracotta, with brass forbidden on anything interactive.
So the migration was **green → graphite**, and it was a migration rather than
a replacement. Limestone stayed as the ground. Atlantic green and terracotta
stayed with narrow named homes rather than being deleted. Gold left entirely.
What is new is the graphite foundation, the cobalt signature, the electric
accent, and the two worlds those make possible.

**The gates it ran, in order.**

    current tokens
      → European Future tokens
      → DISCOVER / INTELLIGENCE surface classification
      → contrast verification, both worlds, both preferences
      → SVG plate re-toning
      → --map-* verification
      → social card verification
      → 1,072 pages regenerated
      → 30 static checks
      → 561 browser checks
      → 1,282 section assertions
      → 331 UX assertions
      → 0 failures

**Classification.** Five pages are INTELLIGENCE: `/map`, `/plan`,
`/my-europe`, `/search` and `/discover` — Discover Mode is a filter, not a
browse surface, and `/discover/<macro>` stays editorial. Everything else is
DISCOVER. The map figures on country, destination and journey pages carry
`data-world="intelligence"` on the element itself: an INTELLIGENCE component
embedded in an editorial page, which is the door working as a design language
rather than as a glyph — a window into the machine, cut into a page.

**INTELLIGENCE is dark in both colour-scheme preferences**, deliberately. The
world is a statement about where the reader is, not a lighting preference. If
it went light for a light-mode reader the two worlds would collapse into one
and the whole idea would be a theme toggle with extra steps. DISCOVER does
follow the preference, and for a dark-preference reader the two worlds stay
apart by accent: DISCOVER is blue, INTELLIGENCE is electric, and lime never
appears on an editorial page in either preference.

**The plates were re-toned, not just re-tinted.** All 794 social cards and
every generated illustration come from one `plate_shapes()` description, so
the SVG on the page and the PNG in somebody else's feed could not drift. The
hues moved from `(168, 196, 210, 32, 24, 14)` — Atlantic teal through brick —
to six cool steps around cobalt and ultramarine. Night plates bottom out near
graphite and their light is lime; day plates lift toward limestone with a low
warm sun, which is the single warm note in the system and the reason they read
as European light rather than as a gradient.

**Still the owner's:**

- Import Eurostat NUTS, or take Natural Earth admin 1 as the cheaper unblock
  for region shapes (`docs/data-licenses/eurostat-gisco-nuts.md`).
- The photography budget (`docs/images.md`). Free stock covers the Eiffel
  Tower and will never cover Albarracín or Theth, which is precisely the
  product — and it will certainly never cover the hero this document
  describes.
- Whether `/journeys/*` should be INTELLIGENCE rather than DISCOVER. They are
  editorial storytelling today and read as such; the route map inside them is
  already an INTELLIGENCE component.
