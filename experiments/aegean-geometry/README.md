# Aegean geometry — does authoritative coastline help at the zoom we actually draw?

An experiment, not a proposal. It is set up so somebody else can run it, and
so that the half of it that can be run today has been run today. Nothing here
changes the site, the data, the build or the licence position.

**Status: one side measured, one side absent.** `FINDINGS.md` holds every
number that could be computed from files already in this repository. Every
OSM-side cell is empty and stays empty until a human settles the licence
question in §4.

---

## 1. The question

> Does authoritative OSM-derived coastline geometry materially improve
> EuropeDoor's map **at the zoom levels users actually see**?

Not "is OSM better than Natural Earth" — it plainly is, at some scale, and
that question has no decision attached to it. The decision is whether the
improvement lands inside the frames this site actually renders, at a byte cost
the page-weight invariants can carry, for a share-alike obligation that
`docs/openstreetmap-not-used.md` says must be paid deliberately.

**Null hypothesis (H₀).** At EuropeDoor's real zoom levels, the difference
between Natural Earth 1:50m as processed by `scripts/map/process.py` and
authoritative OSM-derived coastline, once both are simplified for the same
rendered stroke width, is **smaller than one stroke width** and therefore not
material.

H₀ is a real hypothesis and it may win. The measured prior is against it — see
§3, where the generalisation tolerance comes to 7.9 stroke widths on a desktop
minimap — but it comes close to winning on a phone at 2.2, and "the case is
desktop-only" is a finding worth having before anybody buys a dependency.

## 2. The test area

    lon 23.0 .. 26.6 E      lat 34.8 .. 38.1 N

Chosen because it is where the current geometry visibly fails, not because it
is convenient. It contains:

* **Santorini, Naxos, Paros, Milos** — four destinations with published pages,
  drawn today as polygons of three to five corners;
* **the north coast of Crete** (Chania, Heraklion) — a long generalised
  shoreline rather than a small ring, so the second failure mode is in frame;
* **Athens** — the control. It is drawn from a 136-corner mainland ring and
  should barely move.

Ten atlas destinations fall inside it. Symi, Rhodes, Corfu, Kefalonia and
Ikaria's neighbours are deliberately outside: a bigger box would add work
without adding a failure mode.

## 3. The zoom levels that matter — read from the code, not assumed

`pages.minimap()` is called with `span="auto"` from the destination
composition. `span` is a straight multiplier on `pages.MAPPROJ`, the single
Lambert conformal conic that draws the whole continent into 1000×780, and the
minimap's own viewBox is 900×320. The ladder is:

    for cand in (10.0, 8.0, 6.0, 4.5, 3.2, 2.4):
        if at least 6 destinations fall inside the half-frame: take it

so **the tightest frame that still has company wins**, and the fallback is
2.4. `measure.py` reproduces that ladder exactly — same candidates, same
threshold, same fallback, over all 319 destinations, because the answer for
one place depends on where every other place is.

Measured (`results.json`, `zoom`):

| | span | km per rendered unit | frame |
|---|---|---|---|
| Santorini, Naxos, Paros, Milos, Athens, Hydra, Monemvasia, Ikaria | **10** | **0.64** | ~575 × 200 km |
| Chania, Heraklion (Crete) | 6 | 1.06 | 950 × 340 km |

Across the whole atlas the ladder lands **158 of 319 destinations at span 10**
— just under half the site — and 21 of the 25 Greek ones. Span 10 is the zoom
this question is about.

**What one drawn line is worth on the ground.** The coastline stroke is
`vector-effect: non-scaling-stroke` at 1.1 CSS px, so it stays 1.1 px however
far the geometry is magnified. That makes it the natural unit of "visible":

| minimap width | 1 rendered unit | 1 stroke width | lod1 tolerance (4.42 km) |
|---|---|---|---|
| 1136 px — desktop, `.placeband.maponly` | 1.26 css px | **0.56 km** | **7.9 strokes** |
| 653 px — desktop, paired with a photograph | 0.73 css px | 0.97 km | 4.6 strokes |
| 310 px — 390px phone | 0.37 css px | 2.04 km | 2.2 strokes |

The CSS widths are derived from the tokens (`--page` 76rem, `--s5`, `--s4`) and
are marked **UNVERIFIED**: they have not been measured in Chromium. That
matters — this repository's `--thumbbar` offsets were 44px in the code and 63px
on the screen, and only measuring both boxes found it. `tools/browser-checks.js`
is the instrument that would settle these three numbers, and doing so is step 0
of running this experiment for real.

## 4. Getting the OSM side — the licence comes first

**Do not fetch anything before this is settled.** `docs/data-licenses/openstreetmap-not-used.md`
records a decision, not an oversight, and it is still in force.

### 4.1 The question a human has to answer

ODbL 1.0 is share-alike, and its share-alike condition attaches to a *derived
database*. The existing licence note states the risk precisely: EuropeDoor's
knowledge graph is the product, and merging ODbL geometry into it risks making
the graph a derived database, with an obligation to publish it under ODbL.
The note also sets the condition under which OSM may return:

> OSM-derived geometry lives in its own dataset, in its own directory, with
> its own licence record, and is **joined to** the knowledge graph at render
> time rather than merged into it. If that separation cannot be maintained for
> a given feature, the feature waits.

So the first output of this experiment is not a map. It is an answer to: *does
a coastline substitution keep that separation?* `FINDINGS.md` §4 sets out what
the answer looks like on the page and in the repository. Counsel, or the owner,
answers it. Not this script and not an agent.

### 4.2 Plausible sources

Named so the search is not started from nothing. **Every URL, filename and
version below is UNVERIFIED** — this sandbox has no network, the proxy answers
403 to CONNECT for general hosts, and nothing about a dataset may be committed
from memory:

* **`land-polygons` / OSMCoastline** (osmdata.openstreetmap.de) — the OSM
  coastline assembled into polygons, published split and unsplit, WGS84 and
  Mercator. This is the closest match to what `data/geo/` holds: coastline
  only, no roads, no POIs, no tags. Shapefile, so a conversion step is needed.
* **Geofabrik regional extract** (`greece-latest`) — a full `.osm.pbf` for one
  country. Far more than a coastline, which is a licensing liability rather
  than a bonus here: the smaller the imported surface, the easier the
  separation in §4.1 is to defend.
* **Daylight Map Distribution** — an ODbL OSM snapshot with quality filtering.
  Same obligations.

All three are **ODbL 1.0**. There is no ODbL-free authoritative alternative at
this resolution that this experiment knows of; if one is found, it should be
tested here first, because it would make the whole licence question moot.

### 4.3 The rule the experiment obeys rather than bypasses

`scripts/map/fetch.py` refuses to open a socket for a source with no row in
`docs/data-licenses/sources.json` and no `.md` file beside it, and refuses by
id anything on the `blocked` list — where `osm` currently sits. Obtaining the
OSM side therefore means, in this order:

1. **Settle §4.1.** Written down, by a person, before anything is downloaded.
2. Write the licence record: a new `.md` in `docs/data-licenses/` stating ODbL
   1.0, the attribution text, the share-alike analysis and the separation
   condition. Not a copy of `openstreetmap-not-used.md` with the negation
   removed — that document is the *record of the refusal* and should survive
   as history whatever is decided.
3. Add a row to `sources.json` with `share_alike: true` and
   `attribution_required: true`. Both fields already exist and are `false` on
   every current source; this would be the first `true` for either, and
   `geo.sources_line()` is the function that already carries an attribution to
   every page — see FINDINGS §4.
4. Move `osm` off `blocked`, or leave it there and register the specific
   product (`osm-land-polygons`) instead. **If you do the latter, be aware the
   `blocked` list will not stop you** — see FINDINGS §5, which records that
   gap without fixing it.
5. `python3 scripts/map/fetch.py <id>` — from a machine with a network. Not
   from a build host and not from an agent sandbox.
6. Cut the fetched data to the §2 bbox, convert to GeoJSON, and drop it in
   `experiments/aegean-geometry/osm/`. `measure.py` picks up any `*.geojson`
   or `*.geojson.gz` there and needs nothing else.

Steps 1–5 are outside this directory on purpose. This experiment is designed
to be runnable *after* a licence decision, never to be the reason one gets
made in a hurry.

## 5. The pass/fail bar, decided in advance

Written before the OSM side exists, so it cannot be fitted to the result.
All numbers are at **span 10** and the **1136 px desktop minimap**, which is
the zoom and the width that carry the case; where the phone changes the answer
that is itself reported.

### Materially better — all three must hold

**M1 · Silhouette.** For at least **3 of the 4 named islands**, the maximum
perpendicular deviation between the NE silhouette and the OSM silhouette is
**≥ 3 stroke widths = 1.67 km**.
*Why 3.* One stroke width (0.56 km) is the floor of detectability — a
difference thinner than the line drawn to represent it is not a difference.
Three is the point where the error is a visible fraction of the destination
marker already on the map (r = 5.5 units ≈ 3.5 km at this scale), i.e. a
reader sees it without being told to compare.

**M2 · Fidelity.** For at least **3 of the 4**, the relative compactness error
`|C_ne − C_osm| / C_osm` is **≥ 0.25**, where `C = 4πA/P²`.
*Why compactness and why 0.25.* Compactness is scale-free and separates a
blob from an island in one number: a square is 0.785, a circle 1.0, a crescent
far lower. Santorini is drawn today as a **three-corner polygon at C = 0.587**,
which is the compactness of a triangle because it is one. A 25% error in this
figure is a silhouette a reader would not match to a photograph.

**M3 · Truth.** The OSM side puts **all 10** destinations in the bbox on land.
Natural Earth puts **4 of 10 in the sea** today (Hydra 8.6 km, Naxos 1.3 km,
Monemvasia 0.4 km, Paros 0.4 km from the nearest drawn coast). This is not a
shape metric; it is a claim the page makes and gets wrong.

### Not worth it — any one is sufficient

**N1 · Invisible.** Fewer than 2 of the 4 islands reach even **1 stroke width
(0.56 km)** of deviation. Then the improvement exists only in the file.

**N2 · Unaffordable.** The OSM side, **simplified to the same visible
tolerance** (an RDP epsilon of one stroke width on the ground at span 10 —
0.56 km, versus the 4.42 km lod1 uses today) costs more than **1.25× the
current 5,229 bytes** of Aegean path data, and cannot be brought under that
without failing M1 or M2.
*Why 1.25×.* `invariants.weight.max_page_kb` is a 438 KB ceiling and coastline
is already the dominant term of a destination page: 73,464 bytes of continent
under every minimap, 75% of Santorini's 95,066-byte page. A geometry change
must not be the thing that moves a weight invariant, and 25% headroom on the
region slice is roughly what the ceiling affords with nothing else changed.
The comparison must be **like for like**: raw OSM against simplified NE is not
a measurement, it is a category error.

**N3 · The cheap defect bought the expensive fix.** M3 improves but M1 and M2
do not. A dot in the sea has fixes that cost nothing: clip the minimap frame
to its own view instead of emitting the whole continent, or draw the marker
against the coastline it belongs to. If the truth metric is doing all the
work, do the cheap fix and keep Natural Earth.

### Explicitly not in the bar

Renderer choice (this is geometry through the existing SVG pipeline and
nothing else), roads, trails, POIs, routing, region boundaries, and page
aesthetics. Each is a separate decision with its own trigger.

## 6. Running it

    python3 experiments/aegean-geometry/measure.py     # the table + results.json
    python3 experiments/aegean-geometry/render.py      # out/*.svg, both sizes

Both are standard library plus `tools/lib`, both run offline, and neither
writes outside this directory. `measure.py` reports the OSM side as **not
present** until `osm/` holds a file, and never estimates it.

`render.py` writes two contact sheets at the real rendered widths — 1136 px
and 310 px per panel — because the desktop and phone answers differ and a
sheet at some convenient middle size would hide that. Look at both. This
repository's own record is that counting settles proportions and only
rendering finds defects, and writing these two scripts produced four more
examples of that; they are listed in FINDINGS §6.

## 7. What this experiment cannot tell you

* Whether OSM is right. It is a comparison against a second source, not
  against ground truth. Where the two disagree, the experiment says *how much*
  and *where*, not *which*.
* Anything about coastlines outside the Aegean. One test area, chosen because
  it fails; a Norwegian fjord or a Croatian archipelago may fail differently
  and neither is measured here.
* Anything about the licence. §4 is the shape of the question, not an answer
  to it.
