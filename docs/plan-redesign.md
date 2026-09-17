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
| 01 | **The desk** | the sentence box set into the continent — every one of the 313 destinations the planner scores, lit at once, which is the engine's own first claim drawn rather than written |
| 02 | **The controls** | the twelve structured fields and seventeen interests, at the full measure |
| 03 | **The result** | `#result`, where `planner.js` writes, with an at-rest state that says what will appear rather than leaving a hole |
| 04 | **The engine** | pine. The six weights DRAWN, under the tool that uses them |
| 05 | **Spending style** | three editorial columns, from `data/taxonomy.json`'s own `budgets` |
| 06 | **What it will not do** | the refusals, which are this page's institutional voice and are kept verbatim |
| 07 | **Compose the journey** | the close |
