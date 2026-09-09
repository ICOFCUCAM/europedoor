# Signature moments

> **What should the visitor remember about this page ten minutes later?**
>
> Not which component it uses. Not which fields it shows.

Part 2 of `docs/art-direction.md` established the aperture and put it on 804
pages. That was the right first move and it is now the risk: a signature
applied to everything is wallpaper, and **the goal is recognition, not
repetition**. So the aperture is allowed to be **explicit**, **subtle**,
**implied** or **absent**, and this document says which, per family, with
the reason.

Each family answers nine questions. Where a row reads REFUSED it is a
deliberate absence, not an omission.

---

## Where the aperture actually is, measured

Counted across the built site, not estimated:

| family | pages | arched | plates |
|---|---:|---:|---:|
| destination | 319 | 319 | 0 |
| place | 255 | 255 | 0 |
| region | 130 | 130 | 130 |
| **facet** | **100** | **0** | **0** |
| country | 50 | 50 | 50 |
| **experience sub-category** | **38** | **0** | **0** |
| **interest** | **17** | **0** | **17** |
| journey | 17 | 17 | 0 |
| **theme** | **13** | **0** | **0** |
| month | 12 | 10 | 10 |
| motion | 12 | 12 | 9 |
| **experience category** | **10** | **0** | **1** |
| story | 9 | 9 | 0 |
| home | 1 | 0 | 1 |
| **/map** | **1** | **0** | **0** |

Five families carry no aperture. Two of those are correct and stay that way;
three are gaps. That distinction is the whole content of this document.

---

## The nine questions, per family

### Destination — 319 pages — *invitation*

1. **Emotional promise** — you could actually go here, and here is why you would.
2. **Signature moment** — the three numbered reasons, then the country around it.
3. **Geographic expression** — the destination and its neighbours, frame fitted until it has company.
4. **Visual hierarchy** — one authored sentence, three reasons, the map, the practical answers, the record last.
5. **Primary interaction** — save it, or open a neighbour.
6. **Aperture** — **explicit**. This is where the door was proved.
7. **Imagery** — a photograph when the register holds one; otherwise nothing. Never a plate.
8. **Data** — last, quiet, with a lede saying it is not a reason to go.
9. **Absent** — opening hours, prices, a website, a rating. Seventeen refusals, each a promise.

### Macro region — 9 — *where in Europe this is*

1. The Nordics is a place, not a list of five countries.
2. **The five countries, filled.** A macro region is the one grouping in this atlas with real polygons behind it — a region is a set of destinations and is refused a boundary, but the Nordics *is* Norway, Sweden, Denmark, Finland and Iceland, and Natural Earth has all five.
3. The members filled, the rest of Europe behind them, framed to the members' own extent.
4. Head, map, the countries as cards.
5. Go into a country.
6. **Explicit.**
7. None.
8. The count of members, and each country's regions and destinations on its card.
9. **REFUSED**: a boundary drawn round the group. The frame is the members' extent; the shapes are the members' own.

**This was the last geographic family with no geography** — a headline and a
grid of nine cards, telling the reader which countries are in the Nordics
without ever showing where it is. Every other geographic family draws its
subject.

---

### Country — 50 — *orientation*

1. A whole country, held in one frame, without a guidebook's contents page.
2. The map immediately under the name.
3. The country, its regions at their own centres, its destinations.
4. Statement, map, argument, practical, the atlas, the record.
5. Go into a region.
6. **Explicit.**
7. None. The country is its own shape.
8. Last. Facts with sources, score with a disclaimer.
9. **REFUSED**: a rail of grey bullets; a fact table above the country.

### Region — 130 — *a grouping, honestly*

1. These places belong together, and here is the belonging.
2. The caption: *"Fjord Norway is the 8 destinations below, not a boundary."*
3. Its own destinations, and nothing invented around them.
4. Statement, map, the destinations, the record.
5. Go into a destination.
6. **Explicit.**
7. Plates on the destination cards only — small, arched, not a hero.
8. Counts derived from the destinations themselves.
9. **REFUSED**: a boundary. We hold membership, not geometry, and a convex hull would look like an answer.

### Place — 255 — *is this worth my hour?*

1. A specific thing, described by somebody who has seen it.
2. The honest map caption: *"Bryggen is in Bergen, and this is Bergen."*
3. The town, because the projection's finest unit is about four kilometres.
4. Statement, orientation line, map, practical, the record.
5. Save it, or read what happens here.
6. **Subtle** — it is the town's map, not the place's, and the caption says so.
7. A photograph when registered; otherwise none.
8. Kind, duration, season, coordinates. Nothing volatile.
9. **REFUSED**: opening hours, prices, a website, accessibility we have not checked.

### Story — 9 — *editorial*

1. Somebody wrote this because it was worth writing.
2. The type. Serif body at 38rem, and a hed that exists nowhere else on the site.
3. Its own validated `places`, and only those.
4. Kicker, hed, deck, rule, byline, map, the writing, the margin.
5. Reading. Then one of the places in the margin.
6. **Explicit**, once, at the top — and then nothing for the length of the piece.
7. A photograph when registered; otherwise the map. Never a plate, and never a motif chosen by a hash.
8. **REFUSED** on this family: no score, no facts, no counts. A story is not a record.
9. **REFUSED**: a drop cap, tag chips above the text, related-content furniture in the body.

### Journey — 17 — *movement*

1. Seventeen days, and you can see the shape of them.
2. The route drawn across the continent, hop by hop.
3. The line, with the land under it.
4. Statement, route, the legs in order, the record.
5. Open a leg.
6. **Explicit.**
7. None.
8. Days, distances, and what each leg costs in hours.
9. **REFUSED**: a price, a booking, a "from £".

### Motion — 12 — *a query, answered*

1. This is not a list somebody wrote. It is what the atlas says when asked.
2. **The answer as a shape.** "Everywhere above 63° north" is eight lit points across Iceland, Norway, Sweden and Finnish Lapland, and you see the latitude before you read it. The query is the *proof*, and proof goes under the thing it proves.
3. Every destination shown, spread across the continent.
4. Head, map, the query as one line, the hoisted shared reason, the rows.
5. Go into one.
6. **Explicit.**
7. None.
8. The query expression itself, published in full, plus the match count and the shown count — each stated once.
9. **REFUSED**: a field naming a destination; the validator refuses it. **REFUSED**: the query as a boxed panel in front of the map.

**The mechanism was standing in front of the answer.** The query used to be a
grey `.note` panel with its own `<h2>`, between the head and the map — the
reader met how the page was built before they met Europe. And it said
everything twice: measured across the built site, **all twelve pages printed
the match count and the shown count in the panel and again in the map
caption**. That is this family's own rule, never explain the constraint back,
broken by the family that states it.

Fixing it broke two assertions, both correctly and both for the wrong claim:
they required the literal heading `The query that made this page`. They now
assert that the query expression generated from the motion's own data is on
the page — a page can carry the heading and print the wrong query — and that
the counts appear once. Four of the twelve queries also turned out to be
dangling clauses that only read under a heading: "The query lying above 63°
north." Every one now carries its subject.

### Month — 12 (and the events index) — *where this month sits in the year*

1. Europe is nearly silent in January and crowded in July, and the month you are looking at has a position in that.
2. **The year band.** Twelve columns: the bar above the line is what is on that month, the bar below it is how many countries are in their quieter shoulder. The month you are on is the only one in full accent.
3. Above the fold, none — the year is time, not place. Below it, the fixtures that sit in a validated destination.
4. Lede, the year, the map, what is on, who is at their best, who is quieter.
5. Step to any of the twelve, from a control that also says how big each is.
6. **Absent on the band, explicit on the map.** The door is how this atlas draws geography; a year is not a place, and twelve little arches would be the signature as wallpaper. The map below keeps it where there are at least two mapped fixtures, and loses it in January and March, where there are none and one.
7. None.
8. Two derived series in the band, both counted from the dataset and both asserted against it on every build; counts of both halves — mapped and unmappable — in the map caption.
9. **REFUSED**: pinning a season or a nationwide festival to a capital to fill the map. **REFUSED**: twelve identical chips, which is what this family had — a table of contents for a year, and a year is the one thing that is not a list.

**The disagreement is the design.** October is one of the thinnest months
above the line, eleven fixtures, and the deepest below it, twenty-five
countries in shoulder season. This atlas's editorial position is that the
shoulder is where you should be going, so a band that showed only "what is
on" would draw the opposite of the argument the family exists to make. The
first version drew the shoulder as a 3px rule under each bar; it read as an
underline, and the one thing worth seeing was the thing you could not.

---

## The three gaps

### Theme — 13 pages — *an argument that crosses borders* — GAP

Thirteen themes, eight stops each, three to eight countries apiece. A theme
is not a route — you do not travel Renaissance Europe in order — so it must
not borrow the journey page's line. It is a **constellation**: eight places
that make one case.

1. **Emotional promise** — Europe has arguments running through it, and this is one.
2. **Signature moment** — eight dots, no line, and the reason under each.
3. **Geographic expression** — the eight stops, unlinked. The absence of a line is the point.
4. **Visual hierarchy** — the claim, the constellation, the eight cases.
5. **Primary interaction** — read one stop's *why*, then go to it.
6. **Aperture** — **explicit**, and distinguished from a journey by having no route line.
7. **Imagery** — none.
8. **Data** — how many countries the argument crosses.
9. **REFUSED** — an order, a duration, a "start here". Renaissance Europe has no day one.

### Interest — 17 pages — *how much of Europe is this?* — GAP

Measured across the atlas:

| tag | destinations | of 319 | countries |
|---|---:|---:|---:|
| History & ruins | 200 | 63% | 47 |
| Food | 157 | 49% | 42 |
| Architecture | 126 | 39% | 43 |
| Wild nature | 108 | 34% | 43 |
| Coast & beaches | 92 | 29% | 29 |
| Sacred places | 74 | 23% | 32 |
| Big cities | 74 | 23% | 41 |
| Mountains | 63 | 20% | 30 |
| Art & museums | 58 | 18% | 29 |
| Music & nightlife | 45 | 14% | 21 |
| Wine & drink | 41 | 13% | 18 |
| Islands | 26 | 8% | 14 |
| Snow & winter | 25 | 8% | 14 |
| Design & making | 20 | 6% | 12 |
| Wildlife watching | 19 | 6% | 16 |
| Slow travel by rail | 11 | 3% | 6 |
| Festivals | 3 | 1% | 3 |

**A map is the wrong instrument here.** History on 200 of 319 destinations
draws as "Europe", and so does Food, and so does Architecture — three
identical maps that say nothing. The interesting fact is the *proportion*,
and specifically how badly the top of that table discriminates.

1. **Emotional promise** — an honest answer to "is this a real filter, or does everywhere have it?"
2. **Signature moment** — the page telling you its own tag is weak: *History & ruins is on 200 of 319 destinations. As a filter it barely narrows anything.*
3. **Geographic expression** — country count, not a map.
4. **Visual hierarchy** — the tag, the proportion, the caveat, then the places.
5. **Primary interaction** — combine it with another in Discover Mode.
6. **Aperture** — **absent**, deliberately, and this is the first family where that is the right answer. A doorway onto 200 dots is a doorway onto Europe.
7. **Imagery** — plates on the cards, unchanged.
8. **Data** — the proportion is the content, not a footnote.
9. **REFUSED** — a map that would be identical for the three largest tags.

### Facet — 100 pages — *a focused list, and nothing more* — CORRECT AS IS

1. **Emotional promise** — everything of one kind in one town, in one screen.
2. **Signature moment** — none, and that is the design. This family exists to be left quickly.
3. **Geographic expression** — none. The destination page one click up has the map.
4. **Visual hierarchy** — heading, rows, the note about the threshold.
5. **Primary interaction** — open a row, or go back up.
6. **Aperture** — **absent**. A hundred pages that each repeat their parent's map would make the door mean nothing.
7. **Imagery** — none.
8. **Data** — the threshold, printed, so the page's own existence is accounted for.
9. **REFUSED** — a map, a score, a hero. Depth belongs one level up.

---

## The two deliberate absences

### /map — the instrument, not the picture

The flagship map is a rectangle and stays one. Every embedded map is a
picture *of* somewhere and is cut into the page; this one is a working
surface a reader pans, zooms and filters, and an arch would spend its corners
on decoration while removing usable continent. **Aperture: absent, on
purpose.** The door is what you look through to see Europe; here you are
already inside.

### Home — blocked, not undesigned

The hero is a placeholder and must stay one until the licensed photograph
clears the seven-question gate in `docs/hero-brief.md`. Nothing in this
document authorises work on it.

---

## The test this is all for

A screenshot with the logo removed should still be recognisable as
EuropeDoor. Today that passes on the arched families and fails on the five
that carry nothing. Closing three of those five — theme, interest, facet —
does not mean giving all three an arch. It means giving each one a moment
worth remembering, and two of the three will get there without one.
