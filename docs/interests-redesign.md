# /interests — the Interest Atlas

The owner's brief: INTERESTS → QUESTION → LENSES → REACH → INTEREST ATLAS →
NARROW DISCOVERY → OPEN A DOOR, and one sentence that is the whole argument —
*the useful interests are not necessarily the biggest; a narrow question can
reveal a whole corner of the continent that a broad category hides.*

**Every reach figure the brief quotes is right.** It read the live page and
took History & ruins at 200 destinations in 47 countries and Festivals at 3 in
3 — both exactly what the build prints. That is worth saying because the
/events brief had one figure out by one, and this one has none.

## Part 1 — the source audit

The page was an `ed_opening`, a strip of eight and a seventeen-row ledger.
93,206 bytes and **nine photographs of the eighteen the register holds for
this family.**

| | |
|---|---|
| register rows for this family | **18** — one for each of the seventeen tags, plus `interests-hero` |
| photographs on the page | 9 — the hero and the widest eight |
| unspent | **9**, and they are the NARROW end |
| `<h2>` bands | 2 |
| bytes | 93,206 |

Fourth family running on the same finding: *the pictures were already bought
and were being spent on one strip.* **Nothing was acquired.** And the
particular shape of it here is worse than on the other three: the nine
photographs the page did not draw are the narrow tags — the half this page
argues is the useful half — so the family had a picture of everything it says
is too broad to filter by and none of what it recommends.

## Part 2 — the allocation is the family's own published judgement

`INTEREST_BANDS` has been on all seventeen interest pages since they were
written. It is three sentences with two floors:

| band | floor | what the page says about it |
|---|---|---|
| wide | ≥ 40% of the Atlas | *as a filter on its own it barely narrows Europe* |
| middle | 15–40% | *it narrows Europe usefully without emptying it* |
| narrow | < 15% | *one of the narrowest tags in this atlas, which makes it a real filter* |

Read against the data that is **2, 7 and 8**. So those are the three visual
scales: two at feature size, seven in a strip, eight with their own pictures
at the narrow end — 1 + 3 + 6 + 8 = 18, every photograph once.

The brief asks for an *explicit visual distinction between broad and narrow
interests*. This is that distinction derived from a sentence the family
already writes, rather than a threshold picked to make a layout work — and
`ranking[:3]` would have been a layout deciding an argument, and would have
silently stopped agreeing with the seventeen pages the day a tag crossed 40%.

## Part 3 — the measurement nobody had run, and the sentence that hid it

The ledger's subline was generated and read identically on every row:

> Greece, Italy and Spain carry the most of it.
> Norway, Switzerland and Germany carry the most of it.

The first is **26%** of History between them. The second is **73%** of Slow
travel by rail. One is barely a fact and the other is the whole tag, and the
two sentences have the same shape — which is the `8 PLACES` failure in prose
instead of in a number.

Measured across all seventeen, the share the three strongest countries hold:

| | top three hold | | | top three hold |
|---|---:|---|---|---:|
| History & ruins | 26% | | Wine & drink | 46% |
| Food | 34% | | Islands | 54% |
| Architecture | 40% | | Snow & winter | 52% |
| Wild nature | 29% | | Design & making | 50% |
| Coast & beaches | 39% | | Wildlife watching | 32% |
| Big cities | **22%** | | Slow travel by rail | **73%** |
| Mountains | 33% | | Festivals | 100% |

**Reach and concentration are different questions and the page ordered by one
and printed neither.** Big cities is 74 destinations in 41 countries — seventh
by reach and nearly everywhere; Coast & beaches is 92 in 29, more destinations
in far fewer countries, because a coast is a fact about geography. The share
is printed now, so a row says something different from the row above it.

And it is the evidence under the brief's closing argument: the eight narrow
tags put a **median 51%** of themselves into three countries against **33%**
for the nine above them. A narrow filter does not only shorten the list, it
points at a corner of the continent. The median rather than the mean, because
Festivals is three destinations in three countries and 100% computed on three
rows is a fact about the sample — the small-sample trap /events already
recorded when *half or more* was satisfied by 2 of 4.

**A SECOND MEASUREMENT WAS TAKEN AND NOT SHIPPED.** The country carrying the
most destinations of a tag is almost never the country most *characterised* by
it: **fifteen of seventeen differ** when the same question is asked as a share
of that country's own destinations. Mountains reads Norway, Greece and France
by count and Switzerland at 60% by share. It is not on the page, because the
share is computed on samples as small as five — Türkiye is 5 of 5 history —
and a measure that reports 100% on five rows is the trap above with a
different sign. Recorded rather than shipped, with the trigger being a
destination count per country that does not vary by a factor of fourteen.

## Part 4 — the seven plates

| | class | what it is |
|---|---|---|
| 01 | `iopen gal` | *Seventeen ways to cross a continent* + the hero, full bleed |
| 02 | `firstact pine` | *Interest is the first act of discovery* |
| 03 | `lenses gal` | the wide end: two at feature scale, seven in a strip |
| 04 | `reach paper` | the interest atlas: `pagehead index` + seventeen drawn to one frame |
| 05 | `narrow gal quiet` | the narrow end: eight tags, eight photographs, the share each concentrates into |
| 06 | `smallfilter gal` | *A small filter can open a large door*, with the median under it |
| 07 | `istart pine` | *Start with what you care about* |

## Part 5 — two of the brief's asks are refused, each with a reason

**The reach bar.** The row already prints the percentage, and the seventeen
glyphs are drawn to one frame for exactly this reason — *a knot is an argument
about one corner of Europe, a scatter is one about the whole of it*. A bar
would be the **third** drawing of one number, and /journeys records what
happens when a band draws the same measurement twice on two grids: the bar
read as a mis-drawn header for the thing under it.

**The interactive map.** *Select an interest and the map becomes its
geography* is a control, and this page loads no JavaScript at all — its only
`<script>` is the inert JSON-LD block. A selector here would be the chip that
filters nothing and the `data-rotate` copy nobody ever read. The seventeen ARE
the interest atlas, drawn at once, which is the one thing seventeen separate
pages cannot do, so the ledger band carries both of the brief's names.

## Part 6 — the defects only rendering found

**AN `<a>` INSIDE AN `<a>` IS NOT NESTED, AND THIS COMMIT REPRODUCED /stories'
OWN DEFECT ONE COMMIT AFTER IT WAS WRITTEN DOWN.** `picture()` emits the
Pexels credit as a `<figcaption class="credit">` INSIDE the `<picture>`, and
that credit is two anchors. The narrow band's rows were `<a class="row
narrowrow">` wrapping one — so the parser closed the outer anchor at the inner
one and Chromium's error recovery reopened it around each following run:
**eight rows measured as twenty-four in the browser and the band rendered
4,594 pixels tall.** The emitted HTML contains exactly eight, so no count on
this site could see it. The picture is a `<figure>` now, the NAME is the link,
and the two links the licence requires sit inside no anchor at all. 4,594 →
2,763.

**AND THE DEAD DECLARATION CAME STRAIGHT BEHIND IT.** With the row a `<div>`,
`.row { text-decoration: none }` is set on a box that is not a link, and the
UA underline applies to the name instead — 34px of display serif with a rule
through it. That is `.picstory` on /stories, which shipped underlined for a
commit. *The decoration belongs on the thing that is decorated.*

**A CROP-BOX MEASUREMENT TAKEN BEFORE LAYOUT SETTLES REPORTS A BOX THAT DOES
NOT EXIST.** The first sweep said `.ibleed` swings 0.314–2.333 and guarantees
13.5% of a photograph's frame, and `.atlasopen` 0.200–1.961 at 10.2%. Both are
impossible: each container states an `aspect-ratio`. Waiting two animation
frames gives **1.778–2.333** and **1.333–1.500**. That is *a sampler that
reads outside its own image reports the canvas* in a different costume, and
the damage it does is specific: it would have sent somebody to fix a layout
that is already right.

**AND `countries-hero` DECLARED A CONTAINER /countries HAD STOPPED
EMITTING.** `.ed-opening-visual` is not on that page at all since it became a
plate sequence — the hero renders in `.atlasopen`. `c_container_is_emitted`
passed it because the selector IS emitted, on /events and /interests, and the
browser sweep groups by selector and measures the union over the paths its
purposes declare, so two of three paths kept the group alive and the third
contributed nothing. **A selector that matches nothing on the page that
declares it is invisible to a check that asks the question site-wide.** The
declaration follows the page now: 26% claimed against a measured **55%**, and
`interests-hero` 26% → **47%**.

## Part 7 — what is NOT here

| asked for | why not |
|---|---|
| a filter-chip wall | the brief refuses it too, and so does this page: there is no JavaScript and no per-desk page, so a chip would be a control that does nothing |
| a dark map | the cartography split already decides it — a picture is paper and an instrument is graphite, and these glyphs are pictures |
| a new taxonomy or a second geographic calculation | the brief asks for neither, and the page takes `ranking`, `project()` and `constellation()` exactly as the seventeen tag pages do |
| a ranking of interests | the order is reach, which is a measurement, and the page says so |
