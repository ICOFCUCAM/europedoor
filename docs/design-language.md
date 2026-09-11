# The EuropeDoor design language

> **The test:** remove the wordmark, the masthead and the page title. Put the
> page beside eight other travel products. Can somebody still say which one
> this is?

`tools/recognition.js` runs exactly that, and the answer it gave the first
time it ran was **no for the homepage** — a navy gradient, a headline, a
search box and four chips, while six of the other eight pages in the sheet
carried the aperture and were unmistakable. The page that has to say what
this is said the least.

This document is the answer to that test, stated so it can be argued with.
It is Part 3 of the mandate's loop — ARCHITECT — and it sits between
`docs/first-class-audit.md`, which says what is wrong, and the commits that
fix it.

---

## Part 1 — Five marks, and why each one is not decoration

A design language is not a palette and a typeface. It is the set of
decisions that could not have been made by anybody else, because they follow
from what this product actually holds.

### 1. The aperture — geography is seen through a doorway

An elliptical arch, `rx = span/2`, `ry = 34%` of the height, cut three ways
because a plate's viewBox and its containers disagree: `render.arch_path()`
cuts the SVG, `raster.Canvas.arch_mask()` cuts the pixels, and a CSS
`border-radius` cuts the box. `checks.py` asserts all four values agree.

**Why it is not decoration.** The head is elliptical rather than a circular
segment for one reason: CSS cannot state a circular segment, and a signature
that changes shape with the renderer is three signatures. And a map figure
paints **no background** — the corners outside the arch show the page
through, which is the difference between an opening and a panel. Light wall,
dark opening.

**It is allowed to be absent.** `docs/signature-moments.md` records where the
door is correctly missing, and the rule that governs it is the one worth
repeating here: *a signature applied to everything is wallpaper.* The audit
found twenty-two families opening with an arched map in the same position,
which is that rule being broken by the thing it protects.

### 2. One projection, and it is the EU's own

Lambert conformal conic at EPSG:3034's angles — standard parallels 35°N and
65°N, origin 52°N, central meridian 10°E. Every drawing on the site uses it.
`checks.py` asserts conformality at 54 points and pins the four angles,
because moving a standard parallel keeps a projection conformal and quietly
redraws Europe.

**Why it is not decoration.** It has been wrong twice — once 60% too wide for
a year, once running −25.3% to +89.7% of scale error across the extent — and
both were invisible until somebody did arithmetic. A coastline stretched 45%
still looks like a coastline. **No other travel product draws Europe on its
own conformal conic**, and that is the whole reason the drawn hero is not a
placeholder waiting for a photograph.

### 3. Two worlds, one set of components

`<body data-world>` selects which semantic tokens the single stylesheet
resolves to. DISCOVER is limestone and editorial. INTELLIGENCE is graphite
and luminous, and is **dark in both colour-scheme preferences on purpose** —
the world says where the reader is, not how they like their screen. If it
followed the preference the two worlds would collapse into a theme toggle.

Five pages are INTELLIGENCE, and so is every embedded map figure wherever it
sits.

### 4. Pictures are paper, instruments are graphite

The cartographic split is on what the drawing **is**, not where it sits. A
picture of somewhere gets warm paper, a four-step ocean ramp and an ink
coast. An instrument gets graphite. `docs/palette.json` carries the
separations as *separations* rather than as contrast claims — two drawn
areas that must be distinguishable, which is a different job from a colour
carrying text.

### 5. A measurement is never authored; a classification can be

`population`, `iso3`, coordinates and distances are derived, carry their
source, and are **absent** where there is none — 162 of 319 destinations have
no population figure because Natural Earth does not know them. `village`,
`valley`, `island`, a region's type, a story's section: those are the
editorial work.

**Why it is a design rule and not a data rule.** It decides what a page can
show. A page cannot open on a rating, a review count or a price, because
none exists and none may be authored — so the composition has to be carried
by geography, by the sentence somebody wrote, and by the shape of a set.
Every other travel product's hierarchy is built on numbers this one refuses.

---

## Part 2 — The composition grammar

The brief asks for six movements: **Hero/orientation → Editorial proposition
→ Discovery → Evidence/geographic context → Deep exploration → Action.**

A page takes the movements its subject needs and skips the rest. What it may
not do is take all six because they exist, which is how a homepage becomes a
contents list — the failure this repository already made once, at eight
bands.

| family | opens on | proposition | discovery | geography | deep | action |
|---|---|---|---|---|---|---|
| homepage | the continent, full-bleed | the hero lede | four doors | **in the hero** | journeys, stories | the planner, second |
| country | the country's own portrait | its character paragraph | its regions | the portrait | destinations | add to a journey |
| region | its destinations drawn | why they belong together | the list | the map | — | — |
| destination | name, then why go | the three reasons | places, things to do | the locator | stay, onward | save · add |
| journey | the route | the trip's argument | the stops in order | the route | leg by leg | open in the planner |
| story | the headline | the standfirst | — | its own places | the essay | the places it touches |
| theme · motion | the shape of the query | the query, printed once | the set | the shape | — | — |
| experience category | the kinds, drawn | what the category is | the invitations | — | — | — |
| an index | its own extent | one line | the set | where it applies | — | — |
| an instrument | the control | — | the results | the drawing | — | the result |

Three rules govern the table.

**A movement a family cannot honour is omitted, not filled.** The Stay layer
has no photograph, no rating and no price because there is no honest source
for any of them, and `stay.inventory()` returns nothing — so the page draws
the reading rather than an empty frame. *Present-but-empty says "we have
this" and then does not.*

**The proposition is one sentence and it is stated once.** The motion pages
learned this the hard way: all twelve printed the match count in a panel and
again in the map caption, breaking the family's own rule — never explain the
constraint back — on the family that exists to state it.

**Geography orients; it does not persuade.** A map answers *where*, and
*where* is the second question. It earns the opening only on the families
whose subject IS a shape: a journey's route, a theme's scatter, a motion's
query, a country's outline. On the rest it goes where it belongs, at the
size it deserves.

---

## Part 3 — Three roles for a page head, and no fourth

Twenty-one of twenty-two families placed a 60px h1 at y=164 or y=212. The
roles are what the reader is *doing*:

| role | it is | the head |
|---|---|---|
| `overture` | one thing | narrow measure, air above; the name is the event |
| `index` | a set | the extent sits *beside* the name; the set starts sooner |
| `instrument` | a tool | a label at section weight, on its kicker's line |

**None of the three adds a type size.** A seventeenth was refused twice, and
a role that needs a new scale value is a decoration. `checks.py` requires
exactly one role per head, so a new page cannot join the twenty-one by
accident — which is how they got there.

---

## Part 4 — What the language forbids

Each of these is enforced, and each exists because somebody nearly did it.

| | |
|---|---|
| a second page shell | `render.page()` is the only function that emits `<html>` |
| an inline `<style>` or a `style="…"` attribute | CSP hashes do not apply to style attributes; one would force `style-src` open on 1,034 pages |
| a webfont | zero, and it is an invariant |
| gold, electric lime, and five pre-European-Future navies | refused by name in the stylesheet and again on the painted pixel |
| `rank`, `boost`, `featured`, `sponsored` on a place | the wall between editorial and directory, enforced in the schema |
| an `<img>` with no register row | no photograph without a photographer, a source, a licence, a date and a hash |
| a plate on a story, a motion or a theme | a story is not a place and its picture may not be drawn from a hash |
| a new primitive before the structure has appeared three times | eleven cover the site; four are on 100% of pages |
| a commercial map host or a public tile server | EuropeDoor does not pay for maps and a check enforces it |

---

## Part 5 — How a change is proved

The loop is **audit → benchmark → architect → art direct → implement →
render → critique → refine → test → render again**, and the two halves that
are easy to skip are the two that find things.

**Look to find, count to conclude.** A contact sheet of forty plates
suggested skylines were 38% of them; measured across every destination they
are 28%. The same sheet found three real defects no amount of code-reading
would have. Rendering finds defects; counting settles proportions.

**Prove every check can fail.** A green run that has stopped counting is
worse than a red one, because nobody looks at it. Every assertion added here
is run against a deliberately broken version first, and the count is printed
in the failure message — *a failure message with no measurement in it cannot
be diagnosed.*

**An assertion pins a promise, never a shape.** Nine times now an assertion
in this repository has gone red because a page got better: it counted
`<circle>`, or `.card`, or required `overflow-x: auto`, or demanded six
`<h2>` bands. Each was rewritten to the claim it was protecting, and each
still fails on the thing it was written for.
