# /experiences — the European Experience Atlas

The brief: three pages, three instruments belonging to one institution.

| page | the question | the grammar |
|---|---|---|
| `/discover` | what are you looking for? | the instrument — graphite, one map, a panel that re-lights it |
| `/countries` | where is it? | the atlas — geography first |
| `/experiences` | what do you want to do? | **photography first** |

The failure the brief names is real and this repository has measured it
before in other words: *if all three have the same hero, the same map and
the same cards, it is a CMS however good the CSS is.* What follows is what
the page held before, what the library actually holds, and what the twelve
bands of the brief map onto — including the two that are refused, and why.

## Part 1 — the source audit

`pages.experiences_index()` built, in order:

1. `indexhero()` — kicker, h1 *"What people actually do here."*, a lede, two
   buttons, and `photo(images, "experiences-hero")`. **No drawing**, and the
   comment says why: it used to open on 197 dots at the full extent, which
   is the same continent in the same arch as `/stories`, `/countries`,
   `/interests` and the 404.
2. `ed_strip()` of the eight categories — the only band on the page that was
   already photographic, and the only one that survives this rewrite intact.
3. *Twenty-four of them* — 24 of 197 experiences as `.row`s, in country
   order, with a note saying it is a sample and not a recency.
4. *Eight categories* — eight `barrow`s, a `hopbar` scaled to the largest.
5. *Ten kinds* — ten more `barrow`s, same shape.

So: one photograph, one strip, and **forty-two rows of the same component**.
Measured on the built page before this change, `.row` accounted for 42 of the
page's 48 body elements. That is the data's shape as the layout, which is the
finding that rebuilt `/journeys`, `/europe-in`, `/themes` and the stories
index — arriving on the family whose subject is the least list-like thing in
the product.

**Nothing in it was wrong.** The bars are a real comparison (Family holds 131
entries and Luxury holds 5) and the order — experiences first, then how the
list is cut — was itself a repair. The fault is that a page about what a place
FEELS like was made entirely of type.

## Part 2 — the image-coverage audit

`data/images.json` holds **311 photographs**, every one with a photographer, a
source, a licence, a date and the SHA-256 of the bytes as served.

| key prefix | rows | what this page can do with them |
|---|---:|---|
| `city:` | 65 | the destinations an experience happens in |
| `place:` | 64 | — (a place is inside a destination; not this page's subject) |
| `region:` | 62 | — |
| `country:` | 50 | — |
| `interest:` | 17 | — (that is `/interests`' own vocabulary) |
| `theme:` | 13 | — |
| `macro:` | 9 | **the nine corners of the continent — Experience × Place** |
| `journey:` | 9 | — |
| `category:` | 8 | **all eight categories, one each** |
| `story:` | 7 | **the editorial band** |
| `experiences-hero` | 1 | **the opening** |

Three sets are exactly the right size for this page and all three are full:
**8 of 8 categories, 9 of 9 macro regions, 1 of 1 hero.** The stories are 7 of
9. The destinations are 65 of 319, which is thin for a cinematic strip of
places and is the one place the page has to be honest about what it does not
hold.

**No slot is missing and nothing needs acquiring for this page.** That is
worth saying plainly, because the standing answer to "why so few pictures" is
the library — and on this family, for once, it is not.

## Part 3 — the twelve bands, mapped

| the brief | what it becomes | why |
|---|---|---|
| 01 invitation | the head: *What do you want to experience?* | the brief's own words; the count is derived |
| 02 experience field | `experiences-hero`, breaking the column | the register holds it |
| 03 experience index | **the ten KINDS**, as type | the brief's WILD / SLOW / CULTURAL is invented vocabulary; this atlas holds ten real ones that are EXCLUSIVE and sum to 197, so the numbers are clean and checkable |
| 04 Europe, experienced | a declaration over the largest category | `ed_declare` already exists and is exactly this |
| 05 experience map | the 172 destinations with an experience, on the **light** map set | the brief's correction, and it is what separates this from `/discover` |
| 06 experience × place | **kind × macro region**, with the macro's own photograph | see below |
| 07 cinematic strip | the eight categories at four scales | large → narrow → panoramic → intimate |
| 08 seasons | **REFUSED** | see below |
| 09 experience stories | the stories, lead + two | 7 of 9 hold a photograph |
| 10 choose your Europe | **merged into 03** | the same ten kinds, printed twice, is the fault this repository records about a place page printing one set as a strip and again as rows |
| 11 aperture | one, at the close | eleven doors on one page is the signature as wallpaper — the rule is already written |
| 12 open another door | the close | |

### Why kind × macro and not category × macro

The brief's section 6 wants *WALK EUROPE → ALPINE / COASTAL / NORDIC*: one
experience, broken down by where in Europe it is. Both axes were measured:

    family     131 of 197   Nordics 29 · Mediterranean 28 · Alpine 18
    adventure  124 of 197   Nordics 31 · Mediterranean 25 · Alpine 17

Two thirds of every experience in the atlas is *family* or *adventure*, so
their regional breakdown says **everywhere** — which is true and is not an
insight. `docs/signature-moments.md` refuses a map on this family for exactly
that sentence. The kinds are exclusive and the answer changes:

    On the water        25   The Nordics 11
    Sacred site         13   The Mediterranean 8
    Wildlife & nature   10   The Nordics 6
    Cellar & vineyard   17   The Mediterranean 6

That is a real argument about the continent, and each group has nine
photographs to draw from.

### Why the seasons band is refused

An experience record carries `slug`, `name`, `kind`, `band`, `summary` and
sometimes `at`. **There is no season and no month on any of the 197.** Four
seasonal doors would therefore be four authored claims about when to do
something, which is the Data Integrity Rule's own line: never author a
measurement.

The nearby temptation is worse rather than better — the destinations carry
month data, so the band could be built from *where* the experience happens
and labelled as though it were about the experience. That is the `pop_line`
failure: coverage that depends on a different field being present looks like
a policy.

**The trigger is a `season` or `months` field on the experience record.** The
day one exists the band is four `ed_declare`s and the photographs are already
in the register.

## Part 4 — what is kept, and the line above was wrong

The audit said the bars would be kept: *Family 131 against Luxury 5 is the
argument for having two axes at all, and a page that dropped it would be
prettier and say less.* **Rendering the page refuted it in one look.** Eight
category bars sat under eight category PHOTOGRAPHS and ten kind bars under
ten kind ROWS — one set printed twice to say two things, twice, and the
second printing said less than the first because the picture and the place
are what a bar cannot carry. 3,086 pixels of page.

What the bars had that nothing else did was the category blurb, three sample
experiences and the visual proportion. The samples moved onto the tile, which
is the `ed_strip` repair this repository already made on 220 place pages; the
blurbs live on the eight category pages and `section-audit.py` asserts them
there; and the proportion is 131 against 5 printed on the tiles in
largest-first order.

The paragraph is left standing rather than corrected in place, because the
audit was the hypothesis and the render was the measurement, and the order of
authority here is principles → built system → measurements.

## Part 5 — what only rendering found

| | |
|---|---|
| **`.doorgo` was already taken** | it belongs to the homepage's four doors, which reveal their go-link on hover: `opacity: 0` declared hundreds of lines above, and the two links closing this page were present, placed, sized, keyboard-reachable and painted at zero alpha. The rule against a second NAME for one colour is written down twice in this repository; **this is one name for two things** and had no guard. `browser-checks.js` now focuses every link on every family and asks `checkVisibility({checkOpacity: true})` |
| **the pine room lost to the white one** | the stories plate carried `sheet-gal` and `sheet-pine`: the first paints `--white`, the second rebinds the world's ink to bone, and both are (0,1,0) with `sheet-gal` further down the file. Bone on white, every word on the band, at about 1.1:1 |
| **a grid's tracks are positional** | `3rem 9.5rem 1fr 7rem` with the markup ordered number, name, picture put "Walk or hike" in a 152-pixel column and the photograph in the 768-pixel one — a 1,024-pixel-tall crop, ten times, and a band 11,127 pixels long |
| **two tiles drew one photograph** | the obvious picture for *the water is the Nordics* is `macro:nordic`, and the museums are the Nordics too — so four tiles came out as two photographs twice. *One thing, one picture* from the other end. The tile takes a destination inside the group instead, which is more specific anyway |
| **four scales left 1,400 pixels of white** | a two-column grid makes a row as tall as its tallest item, so a 21:9 panorama beside a 3:4 portrait pays 340 pixels for the difference, four times down the band. `columns: 2` packs instead of aligning |
| **the desk field is `section`** | the story tile reached for `s["desk"]`, which no story record has, and emitted an empty `<span>` nine times |
| **lazy images do not load for a full-page shot** | `loading="lazy"` keys on the viewport and `fullPage` stitches without scrolling, so every picture below the fold photographed as an empty box. The first contact sheet of this page showed eight grey rectangles and read exactly like eight missing photographs |

## Part 6 — measured

| | /experiences | /discover | homepage |
|---|---|---|---|
| photograph, share of page area at 1280 | **32.1%** | 5.2% | 14.8% |
| photograph, share at 390 | **45.6%** | — | — |
| first screen that is picture, at 1280 | **66.3%** | — | — |
| page length at 1280 | 13,241 px | 9,212 | 9,053 |
| bands | 9 | 8 | 8 |

The brief asks for 45–60% of the visual area. At 390 the page is inside that
and at 1280 it is under it — and the remaining gap is the kind index, which
is ten portrait crops beside ten names. Inflating those boxes to reach a
number would be designing to the number, which the brief itself says is not
the point; the figure is recorded rather than chased.


---

## Part 7 — the doctrine audit

`docs/redesign-doctrine.md` arrived after this page shipped, so both of its
audits are filled in here from the evidence above rather than from memory.
Every line that is not satisfied says so.

**Monotony**, measured at 1280: **19%**, ten `kindrow` siblings, with the next two at 5% and 3%. Below the ceiling and the second figure is the diagnostic: a page at 19% with two other components is a composition rather than a listing.

### CONTENT PRESERVATION

- [x] every important existing content item retained — 197 experiences, 8
      categories, 10 kinds, every summary
- [x] existing counts retained and derived — Part 1 lists each
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained — kind x macro region is a cross-tab of
      data that was already there, not a new relation
- [x] existing functionality retained — this page loads no JavaScript
- [x] existing data loaders reused — `all_experiences`, `categories.select`
- [x] existing map engine reused — `region_glyph`, and the category map is
      REFUSED rather than drawn (Part 3)
- [x] existing image and provenance system reused — 1 photograph to 28, and
      **nothing was acquired**

### DESIGN TRANSFORMATION

- [x] the page has a new composition — plate sequence
- [x] the existing card/grid structure was not merely reskinned — 42 rows of
      one component became eight plates
- [x] the opening communicates the page's purpose
- [x] the content hierarchy was reconsidered — the experiences precede the
      taxonomy
- [x] photography has an editorial role — the only honest answer to *what do
      you want to DO* is a photograph, and the register held 311
- [x] the map or the data has a meaningful visual role — kind x macro, and
      the axis was chosen by measuring both
- [x] the sections have different visual rhythms
- [x] the page does not read as a CMS listing
- [x] the page has a memorable signature moment — the eight categories at
      four scales

### Notes, including what this audit does not claim

**The category page is a separate fault and is NOT closed by this.**
`/experiences/<category>` measures **51%**, 48 `invite` siblings, **with no
second component at all** — which is the report's own diagnostic for a page
that is a list and nothing else. `docs/signature-moments.md` refuses geography
there and the sub-category grouping is refused by the data (6 of 48 in no sub,
8 in two); what has NOT been looked at is the one exclusive axis those records
carry. Recorded here rather than ticked.

---

## Part 8 — the category page, recomposed; and the guard applied to one of two fields

Part 7 named this as the open fault and it was the worst figure left on the
site once /countries and the motion pages came down: **51%, forty-eight
`.invite` siblings, 4,065 pixels of a 7,142-pixel page, with no second
component at all.**

### Inspect

The page holds a photoband, an index head with the reach glyph, four
sub-category bars, a strip of eight photographed towns, the invitations, and
the selection rule under them. An invitation carries a slug, a name, a kind,
a **band** and a summary — and the destination it happens in.

Measured across the eight categories:

| category | n | countries | bands | subs |
|---|---:|---:|---|---|
| family | 131 | 42 | 85 low / 46 moderate | none declared |
| adventure | 124 | 44 | 74 / 46 / 4 | 5 |
| culture | 52 | 27 | 33 / 19 / **0** | 5 |
| food | 48 | 26 | 30 / 18 / **0** | 4 |
| faith | 42 | 23 | 30 / 12 / 0 | 4 |
| history | 30 | 21 | 18 / 11 / 1 | 6 |
| nature | 28 | 18 | 11 / 15 / 2 | 4 |
| luxury | 5 | 2 | **5 high** | none |

### Two findings before any layout

**THE SAME GUARD WAS APPLIED TO ONE OF TWO FIELDS.** The builder's own
comment says the KIND is printed only where it distinguishes — *on
/experiences/food every row said CELLAR & VINEYARD or FOOD & TABLE
forty-eight times, which is this atlas's own rule broken by the family that
has the longest lists: never explain the constraint back* — and the BAND sat
next to it, printed unconditionally. So **/experiences/luxury said "high" on
all five of its invitations**, and food said "low" thirty times and
"moderate" eighteen with no "high" anywhere on the page.

**AND IT WAS PRINTING THE RAW SLUG.** `data/taxonomy.json` gives each budget
band a NAME and a note — Frugal, Comfortable, Generous, each with a sentence
— and both invite call sites printed `low`, `moderate`, `high`. An enum value
is an identifier for a program, and every other surface on this site that
shows a budget shows the name. The kind page had it too.

### Recompose

**What an invitation costs is the one exclusive axis these records carry.**
The sub-categories cannot group this list and that refusal is already
recorded in Part 3: six of Food's 48 are in no sub-category and eight are in
two, so the grouping would need a bucket the page has no name for and would
print some invitations twice. A band is one per record, it is a real decision
a reader makes, and **the distribution is itself the finding**: nothing in
Food & drink or in Culture is generous at all, 0 of 48 and 0 of 52, where
Luxury is 5 of 5.

The group's hoisted line is **the taxonomy's own note**, so a page cannot
describe a band differently from the planner that spends it.

**FRUGAL FIRST, WHICH IS THE TAXONOMY'S ORDER RATHER THAN LARGEST FIRST.** A
motion's groups are unordered clauses and take the largest; a budget band is
a SCALE, and printing Comfortable above Frugal because there are more of them
would be sorting an ordered axis by population.

**And the floor is one number for two families.** A section holding fewer
than three is a heading over a row — `GROUP_MIN`, read by the motion pages
and by this one, because *a second implementation of a thing is a second
chance to make its mistake*. What each family groups BY is its own. Three of
the eight categories keep one flat list under it: nature (11 / 15 / **2**),
history (18 / 11 / **1**) and luxury (one band), and those keep the band on
the row because there it distinguishes.

### And `columns` packs where a grid aligns

The invitations were already two columns — and a GRID, whose row is as tall
as its tallest item. Measured on /experiences/food: 48 invitations took
**4,065 pixels** where twenty-four rows of the tallest need about 3,384;
nearly seven hundred pixels paid for the difference between a one-line
summary and a three-line one, twenty-four times. That is Part 5's own finding
about the eight category panoramas, one level down on the same family.

| | before | after |
|---|---:|---:|
| /experiences/food | 7,142 px | 7,218 |
| an invitation | 580 × 141 | 580 × 113 |
| its summary | 3 lines | 2 |
| **monotony, category** | **51%**, nothing else | **36%**, 20% behind it |
| **monotony, sub-category** | 31% | **16%**, 15% and 6% behind it |

The page is 76 pixels taller: the two group heads and their notes cost more
than the packing saves on this category, and on the sub-category pages the
packing wins outright.

### And the heading level follows the grouping

*The level is the outline and the class is the look.* `.invite h2` carries a
recorded reason — *each invitation IS a top-level item of this page, and the
browser suite caught a skipped heading level on two of them* — which is still
right about the ungrouped case and stopped being the only case. A grouped
category puts each list inside a section with its own h2, so an invitation
there is an h3; the three flat categories keep h2. The size lives on the
class, so `:is(h2, h3)`.

### CONTENT PRESERVATION

- [x] every invitation retained — every name, summary, kind, band, place
- [x] existing counts retained and derived — and each band's count is new
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained
- [x] existing functionality retained
- [x] existing data loaders reused — `categories.select`, `all_experiences`,
      and the budget vocabulary is `data/taxonomy.json`'s rather than a
      second list written here
- [x] existing map engine reused — the reach glyph is unchanged, and the
      category map stays REFUSED per Part 3
- [x] existing image and provenance system reused — **nothing was acquired**

### DESIGN TRANSFORMATION

- [x] the page has a new composition — budget bands where there was one list
- [x] the existing card/grid structure was not merely reskinned — the grid
      became packed columns for a measured reason, and the grouping is the
      records' own axis
- [x] the opening communicates the page's purpose
- [x] the content hierarchy was reconsidered
- [x] photography has an editorial role — unchanged: the photoband and the
      strip of eight towns, because an experience has no photograph of its
      own here and the town it happens in does
- [x] the map or the data has a meaningful visual role
- [x] the sections have different visual rhythms
- [x] the page does not read as a CMS listing — 51% → 36%
- [x] the page has a memorable signature moment — the category drawn as its
      own spread across Europe, and now *nothing here is generous* said by
      the absence of a band rather than in a sentence
