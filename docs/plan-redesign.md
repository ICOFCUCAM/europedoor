# /plan — the European Journey Planning Instrument

Four pages, four instruments, one institution.

| page | the question | the grammar |
|---|---|---|
| `/discover` | what are you looking for? | the instrument — one map, a panel that re-lights it |
| `/countries` | where is it? | the atlas — geography first |
| `/experiences` | what do you want to do? | photography first |
| `/journeys` | how do you want to move? | the route — movement drawn |
| `/plan` | **what have you got, and what do you like?** | **the desk — a control and a continent** |

## Part 1 — the source audit

`pages.planner_page()` builds one `.pagehead.instrument`, a free-form
`<textarea>`, twelve structured fields, seventeen interest checkboxes, an
empty `#result` the browser fills, and then four hundred words of method.
`assets/js/planner.js` is 2,005 lines and does the work: it reads
`/api/atlas.json`, scores all 313 planning destinations, sequences them
against distance, and renders `<li class="leg">` rows with a `.leg-when`
column — so **the brief's "timeline replaces a conventional itinerary table"
is already half-true**, and what it asks for is a stronger treatment of a
shape that exists.

**Measured on the built page, and this is the finding that justifies the
whole brief:**

| | 1280 | 390 |
|---|---|---|
| page height | 2,703px | 5,772px |
| picture in the first screen | **0%** | **0%** |
| h1 | 30px at y=140 | 24px at y=226 |

`tools/opening.js` names three families that open with no picture at all.
This is one of them — on the page that is the product's own instrument, and
the one a reader arrives on having decided to travel.

## Part 2 — the weights are real, and they are the page's own

The brief states 30 / 20 / 15 / 10 / 20 / 5. Verified against
`assets/js/planner.js` rather than against the page that describes it:

```
relevance: 0.30   experience: 0.20   season: 0.15
reach:     0.10   quality:    0.20   novelty: 0.05
```

The page and the code agree, and the page already publishes why the
specification's 10% popularity term is not there: this atlas holds no traffic
and no licensed visitor data, so that term would be a number we invented
wearing a percentage sign, and its weight moved to content quality, which is
measurable. **Nothing in the brief's methodology needed changing** — it is
the current page's own, which is what it asked for.

## Part 3 — three of the brief's asks collide with recorded findings

Each is settled with evidence rather than by preference, because three of
them are things this repository has already measured and acted on.

### The monumental opening, against the instrument head

The brief opens on `font: 600 clamp(68px, 10vw, 155px)` — a 155-pixel
headline over a map, with the form below it. `CLAUDE.md` records the opposite
decision, taken on measurement:

> the head pushed the instrument to y=436 on `/plan`, 449 on `/map` and 460
> on `/search`, so half the first screen of a *tool* was a magazine headline
> and four or five lines of prose. **An instrument's title is a label,
> because the page is the tool.**

A 155px headline plus a 620px map plus a card would push the sentence box
further down than the y=436 that finding removed. So the monumentality comes
from the DRAWING rather than from the type: plate 01 is the desk — the
sentence box set into a continent — and the page's title stays a label on its
kicker's line. `checks.py` requires exactly one head role and the `instrument`
role is kept.

**That is the brief's own stated intent rather than a departure from it.** It
asks for "a beautiful instrument for composing a European journey, not a form
page"; a picture of Europe with the control in it is that, and a headline
about planning is a magazine cover about a tool.

### Bright bone and paper, against the INTELLIGENCE world

`/plan` is one of five INTELLIGENCE pages, and that world is dark in both
colour-scheme preferences on purpose — *the world says where the reader is,
not how they like their screen; if it followed the preference the two worlds
would collapse into a theme toggle.* The brief asks for a bone foundation and
"no muddy dark map".

Both hold, because `docs/cartography.md` already splits drawings on what they
ARE: **a picture is warm paper and an instrument is graphite.** The route map
in the opening is a picture — nothing on it responds to the reader — so it
takes the light atlas set. The bands take their own paper the way
`.sheet-gal` and `.sheet-paper` already do on /discover and the homepage, and
`body[data-world]` stays INTELLIGENCE so the world is not collapsed.

### A photograph per stop, for a result computed in the browser

The brief's §03 shows four stop cards — Vienna, The Alps, Salzburg,
Ljubljana — each with `assets/plan-stop-0N.jpg`.

**No purpose declares `/plan` and the register holds nothing for it.** More
importantly, the stops are not known at build time: `planner.js` chooses them
in the reader's browser from their own sentence. A build-time set of four
named stops would be a **fake result** — the same fault as a curated list
wearing the clothes of a query, which `data/motions.json` is validated
against, one family over.

What is honest and is a real feature: the register holds **65 `city:`
photographs of 319 destinations**, and a leg whose chosen stop is one of those
65 can carry it. That needs the derivative URL in `/api/atlas.json` and a row
in `data/contracts.json`, because it crosses a boundary. Most legs would show
none, which is the declared-slot honesty this site already practises.

Measured before deciding, in Part 5.

## Part 4 — what the brief asks for that is already refused, and stays refused

**No booking, no price, no availability.** The brief agrees, and the current
page already publishes it: *"It will not book anything, price a real hotel, or
route you into a country under a travel advisory."* Estimates are editorial
rather than quotes. That sentence is kept verbatim.

**No popularity term.** See Part 2.

**No webfonts.** The prototype loads three Google families. `css.webfonts` is
an invariant at zero and the display serif is already the voice of this
product.

**No inline `<style>` and no `style="` attribute.** The prototype is one
inline stylesheet with `style="color:var(--c)"` on nine elements. Both are
refused by `checks.py`, and the second would force `style-src` open on all
1,034 pages because CSP hashes do not apply to style attributes.

**No traced geography.** The prototype's `<path class="land">` shapes are a
drawing of nowhere. All geometry comes from `data/geo/`, fetched, hashed and
registered.

### The two-column shell, against proof going under the thing it proves

The brief's `.shell` puts the form in the left column and the engine in the
right. That is the arrangement this page already removed, and the comment in
`pages.planner_page()` says why in the source:

> Four hundred words of scoring weights in a right-hand column, level with
> the twelve fields and seventeen checkboxes a reader is filling in — two
> things competing for the same attention, and the form squeezed into two
> thirds of the page to make room for an essay nobody reads while they are
> typing. The form takes the full measure now and the method sits under it,
> which is also where a reader asks the question: they run it, they look at
> the answer, and THEN they want to know why it chose that.

So the engine keeps its own band and keeps it AFTER the tool. The brief's
real ask — *the scoring methodology becomes a visually strong transparent
engine, rather than a block of explanatory text* — is about the treatment
rather than the position, and it is answered by drawing the six weights
instead of listing them.

## Part 5 — the one decision, measured

**A photograph per leg: yes, and it is 20% of legs.**

| | |
|---|---:|
| planning destinations in `/api/atlas.json` | 313 |
| of those, the register holds a `city:` photograph for | **63 (20%)** |
| bytes added to the index, smallest derivative per row | ~5,171 |
| `atlas.json` today | 317,645 |
| cost | **1.6%** |

So the leg carries a photograph where the planner's own choice happens to be
one of the sixty-three, and nothing where it is not. **Not a generated plate**
— the plate system is exclusively the social-card language now, and 189
`.card-art` elements on this site are every one a map. The field crosses a
boundary, so it is declared in `data/contracts.json`: markup one side, an
index the other, and a renamed key would show no photograph with no error
anywhere.

## Part 6 — the bands

| # | band | what it is |
|---|---|---|
| 01 | **The desk** | the sentence box beside the continent &mdash; every one of the 313 destinations the planner scores, and the six it refuses drawn hollow, which is the engine's own first claim drawn rather than written |
| 02 | **The controls** | the twelve structured fields and seventeen interests, at the full measure |
| 03 | **The result** | `#result`, where `planner.js` writes: two notes as a pair, the cost breakdown, the route drawn on /plan's own country rings, and the legs as a timeline with a photograph on the one in five whose stop the register holds |
| 04 | **The engine** | pine. The six weights drawn as bars with the figure at the end of each, under the tool that uses them |
| 05 | **Spending style** | three chapters, each carrying the median daily figure the position in a place's own band produces &mdash; &euro;60, &euro;105, &euro;150 &mdash; derived, with the spread beside it |
| 06 | **What it will not do** | six refusals as rows, each naming where this site publishes it |
| 07 | **Compose the journey** | the close |

## Part 7 — what only rendering found

Twelve defects. Nine of the twelve are faults this repository has already
recorded in another family, and three of those are faults recorded **in the
commit before this one**.

### The scrim, and then the scrim's own removal

The first composition held the drawing as the band's full-bleed GROUND with
the form over it. Measured with the column's words removed, the ground under
the form ran **0.055 to 0.789 of luminance at 1280 and 0.007 to 0.789 at
390**: the head read on flat water and the prose, the button and the extent
figures at the bottom of the column sat on bare drawing, letter by letter,
over 313 cobalt dots and every frontier. The h1's own `#141716` measured
**1.81:1** against the darkest ground it crossed at 1280 and **1.02:1** at
390 &mdash; on a form. That is the homepage hero's recorded failure (a
standfirst at 4.36 across the lit parchment of Iberia) arrived at from the
dark-ink end, where it is worse: a pale scrim lifts pale type, and there is
nothing a wash of the ground's own colour can do for ink except cover what
is under it.

The wash was on `.deskwrap` at 100 degrees &mdash; **a diagonal, and a
diagonal is by construction weakest at one corner of the column it exists to
cover.** Moving it onto the form fixed the ratio at every height and cost
half the continent: Iberia, Ireland, Britain, France and western Norway
under an opaque panel, with the dots showing through the ramp at low alpha as
a field the eye keeps trying to resolve, and a terminator down the middle of
Europe that nothing in the drawing had drawn.

**So the overlap went instead.** Two tracks, no scrim at all: the band's
paper IS `--map-water` and a map figure paints no background, so the
drawing's own ocean and the band's ground are one colour and there is no
seam. The type meets a flat `#DDE8E7` by construction &mdash; 14.41:1 for
the title, 11.43 for the kicker and the prose, 4.72 for the label &mdash; at
every width, and the whole continent is visible.

**AND THE FIRST SAMPLER HID THE SCRIM IT WAS MEASURING.**
`visibility: hidden` on the column hides its own `::before`, so the run
reported the ground the scrim exists to replace. That is the instrument's own
recorded failure, in the instrument written to find this one.

### Three class-name collisions on one page, and there is no guard

**A class name already in the stylesheet is a rule you inherit silently.**
This repository recorded that two commits ago about `.doorgo`, whose
`opacity: 0` made two links on /experiences present, placed, sized,
keyboard-reachable and invisible. It happened twice more here, from the two
most obvious names for a closing statement:

| name | what it already was | what it did |
|---|---|---|
| `.sendsay` | /journeys' close &mdash; a centred statement over a photograph behind a 72% graphite scrim, with `color: var(--bone)` on its heading and lede | bone on a white wall, about **1.1:1**, on the last thing this page says |
| `.closesay` | the closing band on the homepage and /discover, at `max-width: 32rem` | the statement came out 512 pixels wide inside a 1,152-pixel band, centred inside its own cap and therefore off-centre in the room |

Neither is visible to any suite here. The third was mine twice over: a
`.deskart figcaption` rule written and then written again eighty lines
later with an identical body &mdash; one of the 85 duplicated rules the
previous commit removed, reintroduced within the hour. Grep the stylesheet
before naming a composition.

### The eastern slab, and the eye finding the wrong thing

A warm slab with three straight edges sat in the sea south-east of Baku on
the desk drawing. The first reading was "a clipped fragment of a country
with no destinations"; probing it with `isPointInFill` said **Georgia,
Armenia, Azerbaijan and T&uuml;rkiye** &mdash; the Caucasus, correctly drawn,
whose eastern side is the 52&deg;E data cut that `dusk_reach()` deliberately
does not hide so that Baku and Tbilisi keep their ground. *The eye finds a
defect and it does not confirm one.*

Probing a tighter grid found the real one: **Iran and Iraq, in the CONTEXT
layer**, clipped into a slab. That layer is a hero device &mdash; *Europe is
not an island* &mdash; and the graphite it is drawn on absorbs its straight
edges completely, which is why /map and /discover keep it and the same slab
on the same projection is invisible there. This is the one light drawing
that shows the whole eastern cut inside its own frame with open water
beyond it, and `--atlas-far` (`#C3BFB2`) is DARKER than the water rather
than lighter. The wide fade hides it and takes the ground out from under
Baku with it. So the layer with no claim to make here is the one that goes.

### `--atlas-*` is a role and the comment claimed a palette

`.planmap .constel` carries the comment *"This is a picture inside an
instrument, and it takes the picture's palette"* and painted
`background: var(--atlas-sea)`. That token resolves per WORLD, and this
figure only ever renders on /plan and /my-europe, both INTELLIGENCE &mdash;
so for the life of the rule the picture took the instrument's near-black.
Invisible while those pages were dark throughout, and **a black slab the
moment /plan's bands became bone**: measured on the built result, the svg's
own background computed `rgb(7,16,15)` inside a band of `rgb(248,246,239)`.
Named by palette now, which is what the sentence above it claims. That is
the /journeys `--map-sea` finding from the other end &mdash; there a token
that does not exist fell back to transparent; here a token that does exist
resolved to the other set.

### "Nothing has been built yet" under a built itinerary

`#atrest` is new in this composition and `planner.js` has never heard of the
id, so the sentence stayed on the page under four legs, a cost breakdown and
a route map. `#result:not(:empty) ~ .atrest { display: none }` &mdash;
decided by the DOM rather than by a flag somebody has to clear, so the
sentence is shown if and only if the element it describes is empty and it
cannot drift, because the condition IS the thing it is about.

### A chart whose value was six hundred pixels from its bar

*A chart on which four of seven series cannot be seen is the wrong track*
&mdash; that finding was a share of 319 on an 80-pixel track. This is the
same fault inverted. The bar's track was `minmax(0, 1fr)`, 896 pixels at
1280, and a bar is a share of ONE HUNDRED, so the largest weight in the set
can never exceed 30% of it: "Your interests" drew 245px and its `30%` sat at
x=1,167. The scaling did not move &mdash; *the bars are still scaled by the
series they are labelled with*, which is why a share-of-the-largest version
was refused, since a full bar reads as 100% &mdash; the number did, to the
end of the bar it belongs to.

### An aspect-ratio on a container that also holds prose

`.deskart { aspect-ratio: 1000/780 }` put the proportion on the `<figure>`,
which includes the caption: at 390 the figure was 390&times;304 and the
caption took 231 of it, so **the whole of Europe rendered 73 pixels tall**
&mdash; a thumbnail on the band that says the planner works across the
continent. The proportion belongs to the drawing.

### Four bands with a head in the left half

`.sheettext` is a one-column grid, right on /discover where each plate's
text is one of two tracks, and these bands are `display: block` &mdash; so
the h2 took its own measure and the lede sat UNDER it at 361 pixels inside
a 1,152-pixel band. Measured on four of the seven. `render.section()` had
already answered this for three quarters of the site: the title at display
size with its lede beside it, 1.1 against .9 rather than equal halves,
because two equal columns read as a layout and an unequal pair reads as a
statement with a note on it.

### A band whose subject is a list of refusals had one sentence in it

787 pixels for a headline, a lede and a note in the left half, on the band
that carries the product's whole position. Six refusals now, and **not one
is written there for the first place**: each is already published on this
site and the row says where, because a refusal nobody can check is a slogan.

### A sentence box that clips its own placeholder

`.form.ask textarea` starts at two lines and a phone rule already raises it
to four, recorded, because the placeholder needs four at 390. Putting the
form in a 34rem track made the DESK case the narrow one: measured at 1280
the box was 464&times;97 and the placeholder needed 126, so "mountains and
food" was cut off below the fold of the one control this page IS.

### A nine-figure sentinel, a raw path, and two new line-heights

`css.line_heights` refused `1.04` and `1.1` in one run &mdash; the register
holds eight and the display step is 1.12, which both were within a hundredth
of. `c_published_projection` refused the refusals note because it printed
`35&amp;deg;N` where the check reads raw HTML and every other page emits a
literal degree sign. And `c_map_role` refused the desk drawing twice: once
for declaring no role at all, and once for declaring `illustration` without
the `atlas` class the skin means &mdash; added, and verified by
byte-identical screenshots at 1280 with the class and without.

## Part 8 &mdash; the per-leg photograph, and the gap it found in the gate

The register holds a `city:` photograph for **63 of the 313** destinations
the planner can route through, so a fifth of legs carry one and four fifths
carry none &mdash; the declared-slot honesty this site already practises,
and never a generated plate, because the plate system is exclusively the
social-card language now.

**A RUNTIME `<img>` IS INVISIBLE TO THE GUARD THAT REFUSES AN UNREGISTERED
FILE.** `checks.py` reads the shipped HTML for a page referencing a file
with no register row; `planner.js` writes this `<img>` in the reader's
browser, so that check has no reach here at all. Composing Pexels'
attribution in JavaScript would therefore have been **a second
implementation of a LICENCE obligation with nothing on either end able to go
red** &mdash; the one place this repository has already learned not to have
one. `render.credit_html(row)` was lifted out of `picture()` and is now the
single implementation: `picture()` calls it, `planner_api()` calls it, and
the fragment travels in the index as `cities.shotCredit`.

The terms are the gate's own recorded answer, verbatim: *"Whenever you are
doing an API request make sure to show a prominent link to Pexels &hellip;
Always credit our photographers when possible (e.g. 'Photo by John Doe on
Pexels' with a link to the photo page on Pexels)."* Each leg tile carries
both links.

| | |
|---|---:|
| `atlas.json` before | 317,645 |
| after `shot`, `shotAlt` and `shotCredit` | 346,303 |
| cost | **9.0%** |

Declared in `data/contracts.json` with a reason per field, because it
crosses a boundary: an index one side, markup the other, and a renamed key
would show no photograph with no error anywhere.

**And the route figure was a blank field.** `#constel-eu` is one thinned
lod0 silhouette with no internal boundaries &mdash; the right picture for a
132-pixel theme glyph, and 736 pixels of flat stone with a green zigzag on
it for a three-stop route that never leaves central Europe. /plan already
ships the country rings in plate 01, so the figure clones THOSE. No source
rule reaches the clone: measured, the `<use>` computed `rgb(216,212,199)`,
the fill the `.planmap` rule sets, where `.instrmap .countries path` would
have given it the ink coast &mdash; **which refines what this repository had
settled.** A source rule reaches a clone only when the selector matches the
CLONE's position, and writing `.planmap .constel .countries path` did not
reach it either. What draws every boundary is the anti-aliased edge between
two adjacent country fills: one device pixel at every frame. Two strokes
were tried and both are refused, because `glyphView` frames 340 to 1,000
units and there is no non-scaling stroke available through a `<use>`.

## Part 9 &mdash; measured

| | before | after |
|---|---|---|
| page height at 1280, at rest | 7,022 | 7,246 |
| page height at 1280, with a route built | &mdash; | 10,645 |
| picture in the first screen at 1280 | 0% | see below |
| document overflow at 390 / 834 / 1280 | 0 | 0 |
| `<img>` on a built result | 0 | one per photographed stop |

**The opening is 0% photograph and that is the answer rather than a gap.**
`docs/signature-moments.md` refuses a photograph on this family: the page is
an instrument, the reader came to type a sentence, and the one picture that
belongs above the fold is the population the instrument scores. The brief
asked for a route line crossing the continent in the hero and it is refused
twice over &mdash; the seventeen built routes are /journeys' own opening and
drawing them again here is the signature as wallpaper, and the route this
page is about does not exist until the reader presses the button. **So the
route line is drawn where the route exists**, in plate 03, on /plan's own
country rings.


---

## Part 8 — the doctrine audit

`docs/redesign-doctrine.md` arrived after this page shipped, so both of its
audits are filled in here from the evidence above rather than from memory.
Every line that is not satisfied says so.

**Monotony**, measured at 1280: **11%**, six `wrow` siblings, with `rrow` at 7% and `styleway` at 5%. Three components sharing the page, and the page's subject is a form rather than a set.

### CONTENT PRESERVATION

- [x] every important existing content item retained
- [x] existing counts retained and derived — and the three spending styles
      gained a number each, medians over the 313 with their spread
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained
- [x] **existing functionality retained** — every `planner.js` hook, and
      `PLAN_STYLE_POS` is asserted equal to that file's own `STYLE_DAILY` so
      the page and the planner cannot disagree about what "comfortable" means
- [x] existing data loaders reused
- [x] existing map engine reused
- [x] existing image and provenance system reused — and
      `render.credit_html()` became the ONE implementation of Pexels'
      attribution, because a runtime `<img>` is invisible to the guard that
      refuses an unregistered file

### DESIGN TRANSFORMATION

- [x] the page has a new composition
- [x] the existing card/grid structure was not merely reskinned
- [x] the opening communicates the page's purpose
- [x] the content hierarchy was reconsidered
- [x] photography has an editorial role — a photograph per leg, written by
      the planner at runtime with its licence links
- [x] the map or the data has a meaningful visual role
- [x] the sections have different visual rhythms
- [x] the page does not read as a CMS listing
- [x] the page has a memorable signature moment

### Notes, including what this audit does not claim

**The monumental opening stays refused** on the instrument-head
measurement, and the two-column shell stays refused because proof goes under
the thing it proves. The band whose subject is a list of refusals now carries
six, and **not one of them is written there for the first place**: each is
already published on this site and the row says where, because a refusal
nobody can check is a slogan.
