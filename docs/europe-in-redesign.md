# /europe-in — the Computed Atlas

Six plates. Written from the data and then from the rendered page, in that
order, because the finding that mattered is not visible in either alone.

## 1 · The source audit

    12 motions, declared in data/motions.json, evaluated on every build
    319 destinations, 50 countries

| motion | matched | countries | share of the Atlas |
|---|---:|---:|---:|
| Europe in autumn | 309 | 47 | 97% |
| Europe's coastlines | 150 | 30 | 47% |
| Europe's medieval world | 123 | 42 | 39% |
| Europe's mountains | 115 | 33 | 36% |
| Europe's sacred places | 110 | 33 | 34% |
| Europe's culinary regions | 86 | 19 | 27% |
| Europe's hidden villages | 83 | 42 | 26% |
| Europe after dark | 66 | 21 | 21% |
| Europe's islands | 53 | 14 | 17% |
| Europe in winter | 50 | 15 | 16% |
| Europe by rail | 20 | 6 | 6% |
| Europe under the northern lights | 19 | 4 | 6% |

Every figure in the brief matched the build. The work was therefore in what
the numbers do not say.

## 2 · The finding: the printed query was narrower than the query that ran

This is the one family whose entire credibility claim is that **every page
prints what produced it** — `checks.py` has asserted the printed expression
on all twelve since the panel was removed. `motion_match` reads:

```python
tags = set(t["interests"]) | set(r["interests"])
```

so a destination is returned when **its region** carries the tag. The
printed sentence said *"any destination tagged Islands"* and said nothing
about the region. Measured:

| motion | matched | on its own tags | via its region only |
|---|---:|---:|---:|
| Europe's culinary regions | 86 | 24 | **62** |
| Europe's coastlines | 150 | 92 | 58 |
| Europe's mountains | 115 | 63 | 52 |
| Europe's sacred places | 110 | 74 | 36 |
| Europe's islands | 53 | 26 | 27 |
| Europe by rail | 20 | 11 | 9 |

Across the seventeen interests the destination-only reading gives 1,142 tag
applications and the propagating reading gives **1,679** — 47% more.

Two results make it concrete:

| returned by | destination | its own tags | its region |
|---|---|---|---|
| Europe's coastlines | **Nicosia** — inland | history, food, cities | *Nicosia & the South Coast* (coast) |
| Europe's islands | **Tartu** — mainland | history, cities, art | *The Islands & the South* (islands) |

That is `cell` catching `cellar` one family over: the page published its rule
honestly, and a reader who checked would find something the rule did not
describe.

**And it meant two live pages published two numbers for one word.**
`/interests/mountains` says *63 destinations*; `/europe-in/mountains` says
*115 match*. Both derived, both correct under their own reading, and neither
said which reading it was.

### What changed, and what deliberately did not

The engine is **unchanged**. A region tag is a real fact about the ground
around a place, and nine other surfaces read the same union —
`atlas.json`, the search index, Discover Mode among them — so narrowing it
is a data-semantics decision and not a redesign. What changed is the
sentence:

* the query carries a five-word clause — *"— its own tag or its region's"*,
  or *"— own tags and region's counting together"* under `all_interests`,
  because there a destination qualifies when the two lists **together** cover
  every term;
* `motion_tag_note()` states the mechanism **once** per page, hoisted, and
  names the /interests reconciliation.

The first version spelled the whole mechanism out inside the query and
produced the same 130 characters on nine rows of one page — *never explain
the constraint back*, which is this family's own rule.

### Recorded and not done: per-tag propagation

Propagation is right for a tag that describes the ground around a place
(`wine`, `food`, `mountains`) and wrong for one that describes the site
itself (`islands`, `coast`). That is a per-tag distinction, which is the
`monaster*` answer: **say which tags propagate.** It moves 537 tag
applications across nine surfaces and belongs to the owner.

**Trigger:** a `propagates` flag on the interest record in
`data/interests.json`, at which point `motion_match` reads it and the two
families' numbers converge by construction rather than by explanation.

## 3 · The twelve shapes were one per row, 1,152 pixels apart

The family's signature moment is *the query drawn as a shape*, and its
argument is that the twelve shapes **differ**. That is a comparison, and a
comparison laid out at one drawing per screen cannot be made — /themes'
204-pixel-continent finding on the other axis: there the drawing was too
small to read, here it was too far from the drawing it is being compared
with.

They are a grid in the opening now: four across at 1280, 270px a tile
against the 204 /themes measured as too small and the 288 it settled on.
`auto-fill` rather than `auto-fit`, because auto-fit collapses the empty
tracks and stretches a short last row, so twelve tiles come out as eight
small pictures and four large ones.

**And the overlap is measured, because "same frame, different Europe" is an
assertion until somebody runs the arithmetic.** No two of the twelve share
more than **49%** of their results — the closest pair is *Europe in autumn*
and *Europe's coastlines* — and **0 of the 66 pairs** share half.

## 4 · Not twelve buckets

Nobody had crossed the twelve with each other. The shapes differ, and a
reader can still read twelve shapes as twelve boxes, so the other half of
the claim is that they **overlap**:

| satisfies | destinations |
|---:|---:|
| 1 query | 8 |
| 2 | 33 |
| 3 | 92 |
| 4 | **111** |
| 5 | 63 |
| 6 | 10 |
| 7 | 1 |
| 8 | 1 |

Every one of the 319 satisfies at least one. **Narvik satisfies eight** —
autumn, rail, hidden villages, islands, mountains, northern lights, winter
and the coast — and Senja seven. The bars are a share of the largest group
(111) rather than of the 319, because eight groups summing to the Atlas
would put the largest at 35% of its track and read as a share of the
continent, which is a different claim.

`c_motion_distribution` asserts the scaling, the labels and the sum **with
no reference to the generator**: recomputing the distribution means
re-running the twelve queries, and an instrument that re-runs the model can
only ever agree with it.

## 5 · Zero photographs, and a motion may not have one of its own

The register declares no `motion:` purpose and must not: a motion has no
coastline, no topography and no season, so a picture of one is a picture of
nowhere — the refusal that took the twelve plates off this index. What it
**can** spend is a photograph of a destination the query returned.

The pick is derived, and **both first attempts were wrong**:

| rule | what it picked |
|---|---|
| fewest of the other eleven | Nicosia for the coastlines, Tartu for the islands — the region-only members, the weakest in the set |
| direct member, then fewest of the other eleven | Baku for the medieval world, whose registered photograph is the Flame Towers |
| **direct member, then the highest share of its own tag list, then fewest of the other eleven** | **Mostar**, **Blagaj**, **Kuressaare on Saaremaa** |

Advisory countries are excluded, because a derived point is not
automatically an honest one — the first rule offered Belovezhskaya Pushcha,
in Belarus, which is stripped from the planner index. A key already spent is
skipped, because one photograph on two records is *one thing, one picture*
from the other end.

**`by-rail` has twenty results and none photographed**, so it shows its slot
and names the acquisition. Eleven of the twelve carry a photograph. **Nothing
was acquired.** 0 `<img>` → 11.

## 6 · What the brief asked for and is refused

| ask | why not |
|---|---|
| six comparative plates, one per motion | that is a second drawing of six of the twelve, at six scales, on the page whose argument is that they are drawn to ONE frame. /journeys records what happens when a band draws one measurement twice on two grids |
| a cut chosen and the map responding | /europe-in loads no JavaScript — its only `<script>` is the inert JSON-LD block — so a control here is the chip that filters nothing, and `data-rotate` again. The twelve ARE the comparison, drawn at once |

## 7 · Five defects only rendering found

| | |
|---|---|
| the actmark named what the kicker under it already said | plate 01 read *"01 — EUROPE IN MOTION"* and then, eight pixels below, *"EUROPE IN MOTION"* — the double-numbering fault in words rather than digits. The actmark names what the plate **draws** |
| `.mobarn` was 23 pixels off a 390px screen | the largest group IS the track at 100%, so the number at the end of its own bar had nowhere to go. A percentage resolves against the CONTENT box, so padding on the container is what makes 100% mean the bar area rather than the row |
| **"4 QUERYS"** | `n_of()` pluralises by appending an *s* |
| the tile meta line landed at two heights in every row of four | seven of the twelve names wrap and five do not. A grid row cannot align the third element of twelve independent tiles; reserving the name's second line can |
| the close was a fourth class with the same body | `.istart` is the close shape /interests introduced and /beyond-the-obvious already reuses. Written as `.moask`, measured at a 361px lede against the shared shape's 608, and **deleted rather than tuned** |

And two the gates found in the commit that wrote them:

* **a `line-height: 1.2`** — a ninth where the register holds eight, caught
  by `css.line_heights` in the run that introduced it, exactly as
  `line-height: 1.24` was on /countries.
* **a comment in emitted markup ships.** The paragraph explaining why the
  projection is *not* named on this page contained the words "conformal
  conic", and `c_published_projection` reads the shipped HTML — so the
  comment tripped the check it was written about. Third occurrence of that
  rule here. A reason belongs in the source that writes the page.

## 7b · And the browser suite found the one the gates could not

Two failures of 9,709, in both colour-scheme preferences:

    light /europe-in/: contrast 3.56:1 (needs 4.5) on <a> "Pham Ngoc Anh"
    dark  /europe-in/: contrast 3.56:1 (needs 4.5) on <a> "Pexels"

`picture()` emits Pexels' two required links as a `<figcaption
class="credit">` **inside** the `<picture>`, absolutely positioned on a 72%
graphite scrim whose arithmetic gives 6.90:1 whatever the photograph is. The
row's own caption — *"Zagreb, Croatia — one of the 309"* — was styled
`.moshot figcaption`, which is (0,2,0) against `.credit`'s (0,1,0): so a
descendant selector written for one figcaption repainted the other
`--ink-3` and left its position, its scrim and its opacity alone.

**That is the `.pageband figcaption` defect this stylesheet already records,
reproduced two hundred lines from the paragraph recording it.** A rule that
changes two properties of a six-property component achieves exactly one
thing, and here that thing was the defect. A child combinator cannot reach
inside the `<picture>`; measured after, the credit computes
`rgb(255,255,255)` at `position: absolute` in both preferences and the
caption computes `rgb(93,103,91)`, which is 5.90:1 on the gallery wall.

## 8 · Measured after

| | before | after |
|---|---:|---:|
| bytes | 77,358 | 111,404 |
| `<img>` | 0 | 11 |
| declared slots | 0 | 1 |
| `<h2>` bands | 13 | 6 plates |
| page height at 1280 | — | 10,026px |
| page height at 390 | — | 18,547px |
| horizontal overflow at 834 / 390 / 320 | — | 0 / 0 / 0 |

18,547px at 390 sits inside the family — /interests 18,600, /experiences
17,172, /journeys 19,847, /countries 28,198, /beyond-the-obvious 33,721 —
and at 1280 this is the shortest of the rebuilt indexes but for /themes and
/events. That is a measurement rather than a feeling, which is the only
reason it is here.


---

## Part 9 — the doctrine audit

`docs/redesign-doctrine.md` arrived after this page shipped, so both of its
audits are filled in here from the evidence above rather than from memory.
Every line that is not satisfied says so.

**Monotony**, measured at 1280: **36%**, twelve `row motionrow` siblings, with `motile` at 12% and `mobar` at 2%. The highest figure of the pages rebuilt under the brief after /journeys and /interests, and for the same reason: the subject is a set of twelve.

### CONTENT PRESERVATION

- [x] every important existing content item retained — 12 motions, every
      query, every match count
- [x] existing counts retained and derived
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained
- [x] **existing functionality retained, and the engine is deliberately
      UNCHANGED** — `motion_match` still reads the union of a destination's
      own tags and its region's, because that is a data-semantics decision
      for the owner; what changed is the sentence the page prints
- [x] existing data loaders reused — the twelve queries are generated by the
      same function the twelve pages use
- [x] existing map engine reused
- [x] existing image and provenance system reused — 0 `<img>` to 11, every
      one a photograph of a destination the query returned, and **nothing was
      acquired**

### DESIGN TRANSFORMATION

- [x] the page has a new composition
- [x] the existing card/grid structure was not merely reskinned
- [x] the opening communicates the page's purpose — the twelve shapes as a
      grid, because the argument is that they DIFFER and a comparison at one
      drawing per screen cannot be made
- [x] the content hierarchy was reconsidered
- [x] photography has an editorial role
- [x] the map or the data has a meaningful visual role — and the overlap is
      measured rather than asserted: 0 of 66 pairs share half
- [x] the sections have different visual rhythms
- [x] the page does not read as a CMS listing
- [x] the page has a memorable signature moment

### Notes, including what this audit does not claim

**The motion PAGE is the open fault and this audit does not close it.**
`/europe-in/<motion>` measures **54%**, 38 `row` siblings, which is the worst
figure on the site now that /countries has come down, and it is the page whose
whole credibility claim is that it prints what produced it.

---

## 10 · The motion PAGE, recomposed — and the row-level claim that stayed false

Part 9 closed the index and named the motion page as the open fault:
**54%, thirty-eight `.row` siblings of a 6,894-pixel page, with no second
component at all**, which is `tools/monotony.js`'s own diagnostic for a page
that is a list and nothing else. It was the worst figure on the site once
/countries came down.

### Inspect

The page held a head, the answer drawn as a dot map, the query note, a
hoisted shared clause, a strip of eight photographs, up to 91 rows, a
journeys band, a themes band and the onward note. Measured at 1280:

| | |
|---|---:|
| a row | 1,232 × 97 |
| its summary, a sentence of prose | **1,120 pixels on one line** |
| the rows band | 3,694 px of a 7,497-px page |
| rows printing a distinguishing clause on /europe-in/after-dark | **0 of 38** |

### The finding: §2's fix was half a fix

Part 2 measured that `motion_match` reads the UNION of a destination's own
interests and its region's — 537 extra tag applications, 47% more than the
destination-only reading — and fixed **the sentence the page prints.** Every
**row** went on saying *tagged Islands*. For Tartu, a mainland university
town in the region "Tartu & South Estonia", that is not true of the
destination at all.

Measured on the shown sets:

| motion | on its own tags | on its region's |
|---|---:|---:|
| Europe's islands | 10 | **15** |
| Europe's coastlines | 31 | 25 |
| the mountains | 35 | 24 |
| the sacred world | 36 | 19 |
| winter | 13 | 12 |
| after dark | 30 | 8 |
| the medieval world | 64 | 3 |

**On a majority of one page's rows the claim was about the wrong record**,
on the one family whose whole credibility claim is that a page prints what
produced it.

### Recompose: one mechanism, twelve queries

`motion_match` says which side the tag came from, and the list is **grouped
by the clause each result satisfied** — hoist what every result shares,
group by what is left. The groups come out of the query rather than out of a
taxonomy somebody chose:

| motion | groups |
|---|---|
| Europe's islands | 15 in a region tagged Islands · 10 tagged Islands |
| autumn | 42 October · 26 September · 15 November · 8 September and October |
| the medieval world | 51 carrying both · 8 · 5 · 3 |
| the table | 15 · 11 · 3 · 3 |

**A GROUP OF ONE IS NOT A GROUP, IT IS A ROW WITH A HEADING**, which is the
nine-desks-one-story layout the stories index was thrown away for. The first
test was the MEAN group size and it let a tail through: hidden villages
splits 22, 14, 9, 8, 6, 3, 1, 1, 1 — a mean of 7.2 and three sections
holding one row each. The test is every group now, and two of the twelve
keep their list: hidden villages, whose clause is a discoverability SCORE
with a tail of values held by one destination each, and the northern lights,
eight destinations at eight distinct latitudes.

**And the list that stays a list is ordered by the clause that would have
grouped it**, largest run first, where both had been alphabetical by
country — *the order a reader is given is alphabetical by a key they cannot
see*. Ordered by the run's own SIZE rather than by the clause string,
because "scores 97" sorting before "scores 84" is an accident of decimal
notation.

### And the list sets in two columns, which fixes a measure as well as a height

`.row .rowsub` carries `max-width: none`, and the reason written on that rule
is exact and about a different content type: *`.rowsub` is a `<p>` holding a
middot-separated list of place names … nobody reads a list of names end to
start, they scan it.* A destination's SUMMARY is prose, and **140 characters
on one line** is the fault a measure exists to prevent. The generalisation
was one family too far. Two columns give about 68 characters.

| | before | after |
|---|---:|---:|
| /europe-in/after-dark | 7,497 px | 6,133 |
| its rows band | 3,694 | ~2,200 |
| its summary measure | 1,120 px | 509 |
| **monotony** | **54%**, nothing else | **31%**, 8% behind it |
| /europe-in/autumn | 10,080 | 8,912 |

### Three defects the work found

**A CHECK PINNED A SOURCE SPELLING — the twelfth in this repository to pin a
shape rather than a promise.** `c_motion_query_breadth` required the literal
`set(t["interests"]) | set(r["interests"])` in `motion_match`, and went red
the moment that line became `own, near = …` followed by `own | near` so the
clause could say which side it came from — which is MORE of what the check
exists to protect, not less. The engine half is behavioural now: at least
one destination must be returned whose region carries the tag while it does
not, re-running the engine against the destination's own interest list read
from the data. Proved red by narrowing `tags = own | near` to `tags = own`.

**THE GROUP HEAD DISAGREED WITH ITS OWN PRONOUN.** The first version set the
clause in the heading: *"42 destinations, in its quieter shoulder season in
October"*. The clause is written about one destination, so a plural subject
disagrees with the pronoun inside it. The count is the heading and the clause
is a `.whyall` line under it — which is the component whose entire job is *a
clause true of every result in this set*, already on this page twice, so the
group needs no second grammar.

**AND THE ROW'S HEADING LEVEL HAD TO FOLLOW THE GROUPING.** *The level is the
outline and the class is the look*: a row's name is an h2 where the LIST IS
THE PAGE and an h3 inside a band whose own h2 is the level above it. Both
states exist on this family now — a grouped page puts each list inside a
section with a heading, so a row there is an h3, and the two ungrouped pages
keep h2. Read off `grouped` rather than passed per call site, which is the
fourteen-call-sites-forgot-the-motif failure not repeated.

### CONTENT PRESERVATION

- [x] every content item retained — every match, every clause, every
      summary, the map, the strip, the query note, both related bands
- [x] existing counts retained and derived — and each group's count is new
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained
- [x] existing functionality retained — this page loads no JavaScript
- [x] existing data loaders reused — `motion_match` is the same engine and
      still reads both tag sources; only the clause it emits changed
- [x] existing map engine reused
- [x] existing image and provenance system reused — **nothing was acquired**

### DESIGN TRANSFORMATION

- [x] the page has a new composition — groups derived from the query
- [x] the existing structure was not merely reskinned — the grouping is the
      query's own axis, and the row-level claim is now true
- [x] the opening communicates the page's purpose
- [x] the content hierarchy was reconsidered
- [x] photography has an editorial role — unchanged from Part 5
- [x] the map or the data has a meaningful visual role
- [x] the sections have different visual rhythms — 2 to 4 groups, sized by
      the data
- [x] the page does not read as a CMS listing — 54% → 31%
- [x] the page has a memorable signature moment — the query drawn as a
      shape, and now the answer split by how it qualified

### Recorded and not closed

**/europe-in/hidden-villages is 58% and keeps its list.** Its clause is a
discoverability score, and the honest grouping would be a BAND over that
number — authoring a classification on a derived measurement, which the Data
Integrity Rule permits and /journeys' three paces are precedent for. It is a
separate decision with its own thresholds to justify, so the page is ordered
by the score instead and the figure is recorded rather than hidden.
