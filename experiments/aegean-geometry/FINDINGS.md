# Findings — the Natural Earth side, measured; the OSM side, absent

Everything here was computed from files already committed to this repository,
by `measure.py`, on 2026-09-09. **Every OSM-side cell is empty.** There is no
network in this environment, OSM is on `fetch.py`'s `blocked` list, and the
licence question in README §4 is unanswered — so an OSM figure here could only
have come from memory, which is exactly the thing this repository refuses.

Figures marked **UNVERIFIED** were not measured with the instrument that could
settle them. They are flagged, not smoothed over.

---

## 1. What was measured, and with what

`measure.py` parses its constants out of production source rather than
restating them, so it fails loudly instead of quietly measuring a map that has
moved. As read on the day:

| constant | value | from |
|---|---|---|
| continent canvas | 1000 × 780 | `pages.MAP_W, MAP_H` |
| extent | −25 … 45 E, 33 … 71.5 N | `pages.LON0…LAT1` |
| minimap viewBox | 900 × 320 | `pages.minimap()` |
| span ladder | 10, 8, 6, 4.5, 3.2, 2.4 (fallback 2.4, threshold 6) | `pages.minimap()` |
| lod1 simplification | eps 0.04° | `process.LODS` |
| lod1 ring-drop floor | minbox 0.010 deg² | `process.LODS` |
| lod2 | eps 0.012°, minbox 0.0015 deg² | `process.LODS` |
| coastline stroke | 1.1 px, non-scaling | `.minimap.arched .countries path` |

Areas and perimeters are computed on a local kilometre plane about each ring's
own centre, not geodetically. **Instrument check:** Crete comes out at
8,368.5 km²; the island's commonly published area is about 8,336 km²
(UNVERIFIED — a general reference, not a figure held anywhere in this
repository), so the approximation is roughly 0.4% high at the largest thing
measured here. That is well inside the differences the experiment is looking
for, and both sides are measured the same way regardless.

## 2. The zoom the reader actually gets

The ladder was reproduced over all 319 destinations, because which frame one
place gets depends on where every other place is.

    span 10.0   158 destinations      span 4.5    27
    span  8.0    50                   span 3.2    10
    span  6.0    69                   span 2.4     5

**Just under half the atlas — 158 of 319 — is drawn at span 10**, the tightest
frame on the ladder, and so are 21 of the 25 Greek destinations. Inside the
test bbox: 8 at span 10, 2 (Crete) at span 6.

At span 10 the scale is **0.640 km per rendered unit**, a frame of about
575 × 200 km. What one drawn line is worth on the ground:

| minimap width | 1 stroke width | lod1 tolerance (4.42 km) in strokes |
|---|---|---|
| 1136 px desktop, map-only | 0.558 km | **7.93** |
| 653 px desktop, paired with a photograph | 0.970 km | 4.56 |
| 310 px on a 390px phone | 2.043 km | 2.16 |

**The three widths are UNVERIFIED** — derived from `--page`, `--s5` and `--s4`,
not measured in Chromium. `tools/browser-checks.js` is the instrument that
would settle them, and this repository has already been caught by exactly this
gap once: the `--thumbbar` offsets were 44px in the code and 63px on screen.

The finding: **the site magnifies its coastline until the generalisation
tolerance is about eight times the width of the line drawn to represent it**,
on the widest layout, on half the atlas. On a phone that falls to 2.2, which is
still above the line but no longer obviously so — the desktop and phone answers
to this experiment may differ, and that is worth knowing before anything is
bought.

## 3. Shape fidelity — the Natural Earth side

Nearest drawn ring to each destination in the bbox. `crn` is corners, i.e.
ring length less the repeated closing point. `cmp` is 4πA/P²: a square is
0.785, a circle 1.0.

| destination | span | crn | area km² | perimeter km | cmp | crn/100 km | dot | OSM crn | OSM cmp |
|---|---|---|---|---|---|---|---|---|---|
| **Santorini** | 10 | **3** | 56.8 | 34.9 | 0.587 | 8.60 | on land | — | — |
| **Paros** | 10 | **4** | 129.2 | 47.6 | 0.716 | 8.40 | **0.4 km at sea** | — | — |
| **Naxos** | 10 | **5** | 340.6 | 74.8 | 0.765 | 6.68 | **1.3 km at sea** | — | — |
| **Milos** | 10 | **4** | 154.9 | 53.6 | 0.676 | 7.46 | on land | — | — |
| Ikaria | 10 | 4 | 149.6 | 75.7 | 0.328 | 5.29 | on land | — | — |
| Chania, Crete | 6 | 22 | 8368.5 | 642.3 | 0.255 | 3.43 | on land | — | — |
| Heraklion & Knossos | 6 | 22 | 8368.5 | 642.3 | 0.255 | 3.43 | on land | — | — |
| Athens *(control)* | 10 | 136 | 106997.2 | 3531.6 | 0.108 | 3.85 | on land | — | — |
| Monemvasia | 10 | 136 | 106997.2 | 3531.6 | 0.108 | 3.85 | **0.4 km at sea** | — | — |
| Hydra | 10 | 136 | 106997.2 | 3531.6 | 0.108 | 3.85 | **8.6 km at sea** | — | — |

Read it this way:

* **Santorini is a triangle.** Three corners, and its compactness of 0.587 is
  the compactness of a triangle because that is the shape. Paros and Milos are
  quadrilaterals, Naxos a pentagon.
* **The vertex density is not low, it is high — and that is the point.** These
  islands carry 6.7 to 8.6 corners per 100 km of coast against Crete's 3.4 and
  the Greek mainland's 3.9. The pipeline is not starving them; the source
  simply has three to five points for each of them and Douglas-Peucker cannot
  add what is not there. **More aggressive tuning of `eps` cannot fix this
  family**, which is the single strongest argument in favour of a different
  dataset rather than a different tolerance.
* **Hydra has no island at all.** The nearest drawn land to Hydra is the
  mainland, 8.6 km away. Its ring is below the 1:50m source's own threshold.
* **Four of ten destinations in the box are drawn in the sea** — Hydra by
  8.6 km, Naxos 1.3, Paros 0.4, Monemvasia 0.4. Monemvasia's is the
  generalisation moving the coast inland of a town that is genuinely coastal;
  Paros's and Naxos's are the polygon being a rough hull that misses the
  settlement.
* **Athens is the control and behaves like one**: 136 corners, on land, and
  nothing about it looks broken.

## 4. Capture and drop

| | |
|---|---|
| rings in the raw 1:50m source touching the bbox | 23 |
| of those, below the lod1 ring-drop floor | **2** |
| of those, below the lod2 floor | 0 |
| rings in `europe-lod1.json` (what a minimap draws) | 21 |
| rings in `country/greece.json` (what a country page draws) | 23 |
| rings in the OSM side | — |
| **islands in the bbox absent from the current data** | **— (needs the authoritative side)** |

The floor is `minbox` **0.010 deg² of bounding box**, which at 36.5°N is about
**99 km²** — not 76, the figure quoted in `CLAUDE.md`, which is the same
threshold evaluated near 52°N. It is latitude-dependent because it is stated
in square degrees, and it is a **bounding box** rather than an area, so a long
thin island of much smaller true area survives while a compact 90 km² one does
not. lod2's floor is about 14.9 km² here.

**The last row cannot be filled from this repository, and that is itself the
finding.** The only reference available is the same 1:50m file the pipeline
already consumes, so "how many Aegean islands are missing" can only be
answered against a source that knows about more of them. Two rings are lost to
our own floor; how many the source never had is exactly what the OSM side is
for.

## 5. Bytes at the real render size

| | |
|---|---|
| whole-continent coastline emitted into **every** minimap | **73,464 B** |
| the Aegean bbox alone, lod1 (21 rings) | 5,229 B |
| the Aegean bbox alone, lod2 | 10,115 B |
| the Aegean bbox alone, OSM | — |

`minimap()` calls `geo.landmass(MAPPROJ, (0, 0, MAP_W, MAP_H))` — the whole
continent — and lets the SVG clip path hide everything outside the frame. So a
Santorini page carries the coastline of Norway. Measured on the built page:
**95,188 bytes total, of which the minimap figure is 75,833 — 79.7%.** (Read
that pair as a snapshot: `site/` is regenerated on every build and another
change was landing while this was written; the 73,464 B figure above is
computed from `data/geo/` and is the stable one.)

Two consequences for the experiment:

1. **The byte budget is tight and it is not the Aegean that is spending it.**
   `invariants.weight.max_page_kb` is a 438 KB ceiling. Substituting a denser
   coastline multiplies the dominant term of every destination page, not just
   the ones near the change.
2. **There is a cheaper fix sitting next to the expensive one.** Clipping the
   minimap to its own view instead of emitting the continent would cut most of
   73 KB without touching the dataset or the licence. That is why README §5's
   N3 exists: if the OSM side wins only on the "dot in the sea" metric, the
   right answer is the clip, not the import.

## 6. The licence and attribution analysis

### 6.1 What ODbL would require on the page

Attribution. Every page that displays OSM-derived geometry would have to carry
the credit and the licence notice — conventionally *© OpenStreetMap
contributors*, with the data licensed ODbL. Today the credit is voluntary,
because Natural Earth requires none and this repository prints one anyway.
That voluntariness is measurable and it is a gap:

    pages that draw land (contain a <g class="context">)          817
    of those, naming Natural Earth anywhere on the page           499
    of those, carrying NO credit at all                           318
      — 300 under /europe, 17 journeys, 1 discover

**318 pages draw a coastline with no attribution on them.** Under a
public-domain source that is a stylistic choice. Under ODbL it is a licence
breach on 318 pages, and it would have shipped, because nothing checks it: the
attribution is hard-coded into thirteen caption strings in `pages.py` plus one
derived line from `geo.sources_line()`, and the families that got no caption
simply got no credit. A `checks.py` assertion binding *draws land* to *names
the source* does not exist and would have to, in the same commit as the first
ODbL byte.

The mechanism is already there — `geo.sources_line()` builds the sentence from
the provenance carried inside `data/geo/`, and `sources.json` already has
`attribution_required` and `share_alike` fields on every row. Both are `false`
everywhere today; OSM would be the first `true` for either. The gap is not the
plumbing, it is the check.

### 6.2 What ODbL would require in the repository

`docs/data-licenses/openstreetmap-not-used.md` already sets the condition, and
it is stricter than the licence:

> OSM-derived geometry lives in its own dataset, in its own directory, with
> its own licence record, and is **joined to** the knowledge graph at render
> time rather than merged into it.

Applied to a coastline substitution, that means concretely:

* a separate directory (`data/geo-osm/`, not `data/geo/`), with its own
  provenance block and its own licence document;
* **nothing OSM-derived may enter `data/geo/facts.json`.** That file holds
  `iso3`, coordinates and population — the derived measurements the knowledge
  graph reads — and it is the exact seam where a coastline import would turn
  the graph into a derived database. A coastline can be joined at render time;
  a population cannot;
* `geo.landmass()` is the join point, and it already takes a `doc` argument,
  so the joining is a parameter rather than a rewrite;
* no tile server and no OSM host at runtime — already enforced;
  `checks.py` bans `tile.openstreetmap.org` and `tiles.openstreetmap.org` by
  name, and that ban is about the volunteer service, not the licence, so it
  survives whatever is decided here.

If that separation cannot be maintained, the existing note already gives the
answer: the feature waits.

### 6.3 A gap in the existing guard, recorded and not fixed

`fetch.py` refuses a blocked dataset **by id, and only when the id is typed on
the command line**. The `blocked` array is never iterated by the fetch loop —
it does not need to be, since blocked entries are not in `sources`. So:

    python3 scripts/map/fetch.py osm          -> REFUSED, correctly

but adding a row to `sources` under a *different* id — `osm-land-polygons`,
say — with a licence document beside it, downloads OSM without the block
firing at all. The guard stops somebody who names the decision; it does not
stop somebody who does not know there was one.

This is reported, not repaired: this experiment does not modify `scripts/`.
The cheap repair, whenever somebody does touch that file, is to match on the
dataset's host or URL as well as its id, and to prove the check can fail by
adding a blocked host and watching it refuse.

## 7. What rendering found that counting did not

`render.py` was screenshotted in Chromium while being written, and that found
four defects in it that reading the code did not. Recorded because this
repository's rule is to keep the evidence of a mistake:

1. **The whole sheet rendered black.** `docs/palette.json` stores each token
   as an object — hex, name, role — and the first version dropped the object
   into the stylesheet, producing `fill: {'hex': '#f7f6f3', …}`. Every fill was
   invalid, the browser fell back to black, and the file still *opened*.
2. **The two column headers overlapped** on the phone sheet: at 310 px per
   panel the left header was wider than its own column and ran through the
   right one.
3. **The captions rendered at four pixels.** They carried a computed
   `font-size` presentation attribute, and a CSS rule beat it — CSS wins over
   presentation attributes.
4. **Twice, the sheet became an XML parser error page**, because a comment
   inside a style element mentioned a literal less-than. An SVG is XML. The
   style block is wrapped in CDATA now.

None of the four was visible in the source, all four were visible in one
screenshot, and #1 and #4 would have produced an artefact that looked like a
missing file rather than a broken one.

## 8. The OSM side

| measure | Natural Earth | OSM |
|---|---|---|
| corners, Santorini / Paros / Naxos / Milos | 3 / 4 / 5 / 4 | — |
| compactness, same four | 0.587 / 0.716 / 0.765 / 0.676 | — |
| corners per 100 km, same four | 8.60 / 8.40 / 6.68 / 7.46 | — |
| rings in the bbox | 21 | — |
| islands in the bbox absent from the other side | — | — |
| destinations drawn in the sea (of 10) | 4 | — |
| path bytes, bbox, at span 10 | 5,229 | — |
| max silhouette deviation vs the other side | — | — |

Empty on purpose. Filling any cell in that column requires a licence decision
first, a download second and this script third — in that order.
