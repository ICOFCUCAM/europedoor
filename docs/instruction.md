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

**The owner's palette, and the three that carry it.** Canonical values live in
`docs/palette.json`, which is checked: every contrast figure below is
recomputed from the hexes actually in `assets/css/europedoor.css`, so if this
table and the JSON disagree, the JSON is right and this table is a bug.

    BONE #F3F0E6      the page
    PINE #0F433E      the masthead and the signature
    GRAPHITE #07100F  the instrument's ground

Those three are the product. Everything else identifies a **content family**,
and the brief is explicit that this is the critical half:

> And I would NOT make every page colorful. This is critical. The colors
> should identify different content families.

> UI = restrained, PHOTOGRAPHY = rich, MAPS = precise, TYPOGRAPHY = dramatic.
> So you can have an incredibly colorful photograph of the Dolomites beside a
> very restrained editorial interface. That's much more sophisticated.

An eight-hue wheel with a tinted ground and a gradient ribbon per family was
generated in OKLCH, measured, shipped and removed one commit later, because
it is the site the second quotation names: *green blue orange yellow pink
purple*. What replaced it is smaller and does more work — the accent is spent
on the kicker, the section rule and the marks, and the bright colour comes
from the photographs.

| token | hex | what it is |
|---|---|---|
| `--bone` | `#F3F0E6` | the page. The owner's main background, and never #fff: white is a screen and bone is paper |
| `--bone-light` | `#F8F6EF` | the LIFT above the page — a card, a field. The one surface that goes up rather than down |
| `--bone-2` | `#EAE6DA` | the middle rung of the surface ladder, derived so bone -> bone-2 -> mineral is monotonic and every step is one a reader can see |
| `--mineral` | `#D8D4C7` | warm stone: the third surface, and the land on the light map. One token for both, because they are the same material |
| `--ink-2` | `#3B443A` | secondary type: a caption, a meta line, a subline |
| `--ink-3` | `#5D675B` | the quietest type this palette allows on paper |
| `--rule` | `#CFCBBB` | the hairline between two list rows, and nothing that is a boundary |
| `--ink` | `#141716` | type. The owner's table names two near-blacks and this is the charcoal one; it was an alias for graphite, which made a page's letterforms and the instrument's field the same colour |
| `--pine` | `#0F433E` | the masthead and the signature. A drawn colour before a read one |
| `--pine-deep` | `#07302B` | everything pine that is text, and the interactive colour on light |
| `--pine-lift` | `#55A07E` | actions in the dark world |
| `--pine-air` | `#7FBFA1` | the accent on the dark world's editorial surfaces |
| `--graphite` | `#07100F` | the near-black GREEN: a ground, and the instrument's field |
| `--graphite-2` | `#101917` | the dark world's card |
| `--graphite-3` | `#18211F` | the dark world's well — tracks, score bars, the deepest surface |
| `--cobalt` | `#2457C5` | the geographic accent. Countries and journeys, and text at 5.68 on bone |
| `--cobalt-2` | `#1C46A0` | cobalt where it is pressed — the hover step under a cobalt link or kicker |
| `--cobalt-lift` | `#4076E7` | cobalt where the ground is graphite, because cobalt itself is 2.98 there |
| `--cobalt-air` | `#619BFF` | the instrument's accent on the instrument's own ground |
| `--sky` | `#78B4C7` | the Mediterranean and Alpine accent. A GROUND on light and a read colour on graphite |
| `--ochre` | `#C49A52` | the territorial accent: regions and events. A ground and a mark, never an action |
| `--ochre-deep` | `#8E6618` | ochre where it has to be read — a kicker on a region or a month |
| `--ochre-deep-2` | `#6F4F11` | ochre as emphasis rather than a ground: the year band’s current month, at 6.57 on bone |
| `--terracotta` | `#B9684A` | the warm architectural accent: destinations and stories. A graphic at 3.58 |
| `--terracotta-2` | `#A6573A` | terracotta where it has to be read |
| `--terracotta-3` | `#8C4930` | terracotta where it is pressed, at 6.35 on bone |
| `--terracotta-lift` | `#E08A5C` | the same accent on a dark ground |
| `--terracotta-lift-2` | `#EA9A6C` | and its deeper step there |
| `--olive` | `#687044` | the restrained natural accent: provenance, heritage, the fund |
| `--olive-2` | `#545A36` | olive where it has to be read on a lighter surface |
| `--olive-lift` | `#A3B167` | olive on a dark ground |
| `--olive-lift-2` | `#B4C179` | and its deeper step there |
| `--warn` | `#981F31` | a travel advisory, and nothing else ever |
| `--warn-lift` | `#EE8192` | the same warning on a dark ground |
| `--map-land` | `#D8D4C7` | the light map's land. Mineral, because it is the same stone |
| `--map-water` | `#DDE8E7` | the light map's water — and land against it is 1.18, which is why the border carries the coast |
| `--map-border` | `#68716E` | the coastline and the frontier on the light map. On this map the boundary IS the map |
| `--map-ink` | `#1A2725` | a place name on the light map's land |
| `--map-dark-bg` | `#07100F` | the dark map's ground |
| `--map-dark-land` | `#F3F0E6` | the continent, pale against graphite — the whole of the dark map |
| `--map-dark-border` | `#B9C1BA` | its frontier |
| `--map-dark-ink` | `#F3F0E6` | type on the dark map |
| `--ocean-deep` | `#346F6A` | a river on the land and the deepest sea: 3.90 on the stone, 4.62 on the water |
| `--ocean-mid` | `#549C96` | the step between, and the hero's own Atlantic |
| `--ocean-shallow` | `#93BDBA` | near water — the shore band under every coast |
| `--ocean-coastal` | `#D2DFDE` | the shallowest step, where the sea meets the stone |

### The family accents

The accent says what **kind** of thing is being read. A reader will never name
it and will feel it: an essay about a festival should not be the same blue as
a boundary dataset.

| accent | token | where |
|---|---|---|
| geographic | `--cobalt` (`#2457C5`) | countries and journeys: where a thing IS, and movement between. Bone + cobalt + mineral |
| territorial | `--ochre` (`#C49A52`) | regions and the events calendar: an area and a season. Bone + ochre + mineral |
| architectural | `--terracotta` (`#B9684A`) | destinations, stories and experiences — the human half. Bone + terracotta + photography |
| natural | `--olive` (`#687044`) | provenance, heritage and the Fund: how this project knows what it claims |
| mediterranean | `--sky` (`#76AFC2`) | a GROUND and a mark, never text: the section rule under a journey or a region |
| machine | `--cobalt-air` (`#619BFF`) | INTELLIGENCE only — /map, /plan, /my-europe, /search, /discover, which the brief names graphite + bone + cobalt and calls the instrument |

**The primary action is not the family's colour.** `--sea` is the interactive
colour — links, focus rings, controls, the primary button — and it is one
value across the whole site in each world. For one commit `.btn` took
`--door`, which made the region family's primary button a gold one; a control
that changes hue by family is the family-coloured UI the brief refuses.

### The two maps

The brief changes the maps before it changes anything else, and names the old
treatment by what it looked like: *I would not use the current green/black map
treatment.* The diagnosis is the water — a `#0e2a3c` Atlantic under a khaki
continent is a satellite photograph at night — so there are two sets of four
values and a drawing takes one of them by what it IS.

| | land | water / ground | border | ink |
|---|---|---|---|---|
| **light** — the European atlas: the 824 plates, the country portraits, the region glyphs | `#D8D4C7` | `#DDE8E7` | `#68716E` | `#1A2725` |
| **dark** — the instrument and the hero: `/map`, `/plan`, `/my-europe`, `/search`, `/discover`, and the homepage opening | `#F3F0E6` | `#07100F` | `#B9C1BA` | `#F3F0E6` |

*Notice: no olive.* On the light map the land is stone on pale water and the
**coastline** carries the separation the tone does not — land against water is
1.18, and the border ink measures 3.39 on the land. On the dark map that
inverts: the continent is bone against graphite at 16.90, so the coast is the
strongest edge in the drawing with no stroke at all and `#B9C1BA`
is a faint internal frontier at 1.62. The continent becomes pale against
graphite, which is the dramatic map without the swamp appearance.

### There is no gold, and ochre is admitted

Brass `#8A6D34` and `#C2A165` were the previous system's only golds, they were
already forbidden on anything interactive, and they stay out **by value**.
Gold says *luxury · premium · heritage · wealth*; this product has to say
*Europe · discovery · movement · intelligence · culture · future*.

The owner's palette then names **ochre `#C49A52`** as the territorial accent,
and that is a different job from a gold button: a ground and a kicker on the
regions and the events calendar, never the colour a reader clicks. So the
refusal was narrowed to what it was actually protecting rather than deleted —
no gold on an action, a link, a focus ring or the mark — and the arithmetic
that catches a gold stays exactly as strict as it was, with the register
declaring which golds are the ochre family by hex. Loosening the arithmetic
until ochre passed would have loosened it until a brass passed too.

### The ratio is the instruction, not the hex codes

    60%  bone
    25%  graphite
    10%  pine
     5%  the accent

A palette gives you *blue website with gold buttons*. A ratio gives you
*European editorial design over futuristic digital infrastructure*. If a
screen does not hold roughly this distribution, the palette has been applied
and the instruction has not. It is measured on the pixels a reader is painted,
over twelve pages spanning both worlds, and the reading on the previous
palette was bone 64.1, graphite 18.9, water 9.7, signature 7.0 and **accent
0.3** against a declared 5 — which is the finding this palette answers, by
giving five families an accent that identifies them rather than two that tint
an 11px kicker.

### Where each colour may go, measured rather than asserted

WCAG 2.2, AA: body text needs 4.5:1, large text and UI edges need 3:1. These
are computed, and `checks.py` recomputes all thirty-one claimed pairings from
`docs/palette.json` on every build — so a hex nudged "slightly warmer" in a
redesign cannot quietly take a contrast ratio with it.

| | on bone | on the light card | on graphite |
|---|---|---|---|
| Graphite | **16.01** | **14.49** | — |
| Bone | — | — | **16.01** |
| Pine `#2E7157` | **5.09** ✓ | **4.61** ✓ | 3.15 ✗ |
| Pine Deep `#1E4636` | **9.27** ✓ | **8.39** ✓ | 1.73 ✗ |
| Pine Lift `#55A07E` | 2.74 ✗ | 2.48 ✗ | **5.84** ✓ |
| Olive `#4A5326` | **7.20** ✓ | **6.51** ✓ | 2.22 ✗ |
| Terracotta `#A4491F` | **5.18** ✓ | **4.69** ✓ | 3.09 ✗ |
| Pine Air `#7FBFA1` | 1.86 ✗ | 1.69 ✗ | **8.59** ✓ |
| Ultramarine `#665CFF` | 4.09 ✗ | 3.96 ✗ | 4.31 ✗ |

Five consequences that are not negotiable, because they are arithmetic:

- **There is no Electric Lime, and what retired it was not contrast.**
  `#C8FF4D` measured 15.97:1 on graphite and cleared every ground it was ever
  used on. What it failed was the ratio above. An accent is five per cent of a
  screen, and this one had become the colour of seventeen journey routes, 894
  homepage dots, 319 destinations on `/discover`, 172 experiences and every
  lit country on every region glyph — a continent, drawn in the accent, on a
  near-black ground. That is a network diagram, and it is the exact
  association the cartography split was written to escape, arriving through
  the accent rather than through the ground. The dark world's accent is
  `pine-air`, which this palette had already measured for that ground.
  Lime is out of the system the way brass is: removed, not rehomed, with a
  check on each end.
- **Ultramarine is never type.** It fails on every ground we hold. It is a
  gradient, a map wash, a glow behind a route. The moment a word is set in it,
  somebody cannot read that word.
- **The signature is a drawn colour, not a read one.** `#2E7157` is 5.09 on
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
      → every page regenerated
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
apart by the ground itself rather than by a hue: INTELLIGENCE is dark in
both preferences and DISCOVER only in one, which is a difference a reader
meets on every page rather than only where an accent happens to appear.

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
