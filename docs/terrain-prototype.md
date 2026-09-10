# The terrain prototype — Chamonix, four strengths, one decision

**Question asked:** does restrained terrain materially improve the recognition
and sense of place of an Alpine destination?

**Answer: yes, and not marginally.** Accepted at MEDIUM strength, and now
**integrated on the destination and journey illustrations** under the owner's
five rules. What follows is the eight things the brief asked to be written down
first, then what integration changed and what the second benchmark — eight
destinations, looked at together — found.

The benchmark question was put the other way round, and that is the version
worth answering: *does removing the terrain make Chamonix feel less like
Chamonix?* Panel A is the destination plate as it ships today — a beige
rectangle, five dots, a frontier and one named summit. It could be anywhere
between the Loire and the Danube. Panel C is the same frame with four
hypsometric bands under it, and the Arve valley, the Rhône trench, the Aosta
valley and the arc of the range are all legible before a single word is read.
The town sits *in* something. That is the whole of the finding.

## The four panels

Rendered at 1280, 704 and 390 CSS pixels, two-times device scale, from the
real shipped figure and the real stylesheet — not a mock.

| | what it is | luminance spread across the bands |
|---|---|---|
| **A** | today: no terrain | — |
| **B** | terrain, low | 0.088 |
| **C** | terrain, medium — **accepted** | 0.159 |
| **D** | terrain, high | 0.241 |

**B was rejected on the phone, not on the desktop.** At 1280 it is quiet and
correct and arguably the more restrained picture. At 390 the plate is 358 ×
127 CSS pixels and 0.088 of luminance across four steps is a faint mottle: the
Alps do not read. A signature that only works on a large screen is not this
product's signature, and there is no honest way to make the strength depend on
the viewport — that is two pictures of one place.

**D was rejected for the reason the brief predicted.** At 0.241 the ochre
stops being a ground and starts being a ramp: the eye reads the map as a
data visualisation of height rather than as a picture of a valley. The 2,000 m
band also goes near-white, which at this tonal distance reads as cloud rather
than as rock. It is the strongest version and it was not chosen.

**C is the one.** The bands are felt rather than read, the typography stays
dominant, and the label ink still measures 9.7:1 against the darkest band —
the same distance from AA it has always had.

## 1. Source

AWS Terrain Tiles (Mapzen / Tilezen), terrarium PNG encoding, **zoom 7**, the
six tiles `7/{65,66,67}/{45,46}` that cover the Chamonix frame.

    metres = (R * 256 + G + B / 256) - 32768

## 2. Licence

**Public domain, and arrived at by choosing the zoom rather than by hoping.**
The terrain tiles are a composite of eleven datasets, several of which require
attribution — including **EU-DEM**, which carries a Copernicus obligation this
repository has not accepted, on the same reasoning that keeps Eurostat NUTS on
the blocked list.

Tilezen switches Europe to EU-DEM at **zoom 9** and to four national CC BY / OGL
datasets at **zoom 10**. At zoom 7 the land is SRTM and GMTED2010 and the sea is
ETOPO1 — three US Government public-domain sets where credit is *requested*
rather than required.

That is verified per tile, not read off a table: the service publishes the
contributing images in an `x-amz-meta-x-imagery-sources` response header, and
each of the six register rows carries the header **as returned for that exact
tile**. All six name only `srtm/*`, `gmted/*` and `etopo1/*`.

Zoom 9 and deeper is now a `blocked` entry with `refuse_matching` patterns on
the URL, so "one zoom deeper for a bit more detail" is refused with the licence
printed. The guard is on the URL because that is where the zoom is. See
`docs/data-licenses/aws-terrain-tiles.md`.

Any page that draws terrain names:

    SRTM and GMTED2010 elevation data courtesy of the U.S. Geological Survey

## 3. Resolution

865 m per pixel at 45°N (`cos(lat) * 2πR / (256 * 2^7)`). The block is 768 ×
512 cells and covers 2.81°E–11.25°E, 43.17°N–47.01°N.

Sanity-checked with numbers before anything was drawn, because a decoder that
is out by a scale factor still produces something that looks like terrain:

| | decoded | true |
|---|---|---|
| Mont Blanc | 4,675 m | 4,808 m (one cell of an 865 m grid is an average) |
| Chamonix | 1,043 m | 1,035 m |
| Geneva | 379 m | 375 m |
| sea off Nice | −941 m | — |

## 4. Preprocessing

`scripts/map/relief.py`. Stdlib only, like everything else here — the PNG
decoder is zlib plus the five filter types.

    decode → blur → threshold → trace → simplify → project

* **Blur**: separable box, radius 2, three passes ≈ a 4 km Gaussian. This is
  the "soft tonal field, no hard digital shadows" half of the brief. An 865 m
  grid thresholded raw stair-steps at cell size, and a stair-step reads as a
  rendering fault rather than as a ridge.
* **Threshold**: at 200, 600, 1,200 and 2,000 m — the four boundaries of
  `cartography.HYPSOMETRIC`. The 0–200 step is the land tone the plate already
  paints, so it is not traced.
* **Trace**: marching squares. The grid is padded with a ring of −1e9 so every
  loop closes; an open polyline cannot be filled. Holes are real holes — the
  Rhône valley is a hole in the 1,200 m band, and losing it would lose the
  valleys, which are the point.
* **Simplify**: Douglas–Peucker at 1.2 cells ≈ 1 km, under a pixel on a phone.
* **Project**: rings come out in lon/lat, so the existing `Projection.path()`
  draws them and no frame is privileged.

**No hillshade.** A hillshade is a light source: it invents a direction and
paints structure onto flat ground. Bands claim only height, which is the one
thing the source measures.

**The bands never touch the sea**, by construction — nothing below 200 m is
traced — so no clip to the coastline is needed and no water inherits land
shading.

### What went wrong, and what it looked like

**Two of the four saddle segments were emitted backwards.** Every other case
puts the high ground on the right of travel, so each vertex has one segment
leaving and one arriving; the saddle branch broke that, chains merged into one
another, and 8,424 traced segments at the 200 m threshold yielded 1,614 in a
closed ring. The outer boundary of the Alps — the one ring that matters — was
discarded in silence. The picture that produced was **terrain in the Rhône
valley and none on Mont Blanc**, which reads as a registration error and sent
the first hour of debugging at the projection instead of at the topology. A
point-in-polygon test against four known heights found it in one run:
Lyon at 111 m was inside the ≥200 m band and Mont Blanc at 4,675 m was inside
nothing, so the bands were the complement of themselves.

`loops()` now raises on any chain that does not close. Proved red by flipping
the `idx 1/14` orientation: 6,656 segments in unclosed chains.

**The saddle branch is currently unreachable in this data.** Counted across
all four thresholds after the blur: zero cells in configuration 5 or 10. Three
box passes at radius 2 remove the diagonal-pair configuration entirely at
865 m. The code is correct by construction and untested by this frame; a
wider extent or a lighter blur will exercise it.

**And the borders vanished under the terrain.** Panel A carries a clear
France / Switzerland / Italy frontier and the first render of C carried none,
because a boundary is a *stroke on the land path* and the bands paint over it.
`cartography.ORDER` already puts `country-bounds` above `terrain`; today that
layer is folded into `land`, and folding it is only correct while nothing is
drawn in between. The prototype re-emits the boundary geometry stroke-only
above the terrain. There is no cheaper form: a `<use>` clone is still matched
by the selectors that fill the original, which this repository has been caught
by once already.

Re-stroking it also reproduced the *frontier is a worm* failure the stylesheet
already documents — 0.9 units inside `scale(10)` is a nine-unit black rope
across the Alps — because the duplicate did not carry `vector-effect:
non-scaling-stroke`. A rule that exists is not a rule that is inherited.

## 5. Generated asset size

| | bytes |
|---|---|
| six source tiles in `data/raw/` | 546,569 |
| derived JSON, whole 6-tile block | 34,451 |
| **path data actually inlined in the Chamonix frame** | **30,335** |
| the destination page today | 55,344 |
| the destination page with terrain | ~86,000 |
| `weight.max_page_kb`, the recorded ceiling | 440 |

Smoothing pays for itself twice. At blur radius 1 and ε 0.6 the same frame
costs **77,287 bytes** and looks crisper in a way that is *less* editorial —
more detail, more GIS. Radius 2 and ε 1.2 is 39% of the bytes and the better
picture.

## 6. Render cost

2.1 s for the whole chain on the 768 × 512 block: 0.3 s decode, 1.1 s blur,
0.7 s trace and simplify. That is a **pipeline** cost, not a build cost — the
derived rings would be committed to `data/geo/` exactly as the coastline is,
and `tools/build.py` would read them. The build stays offline and stays
deterministic.

## 7. Opacity and tonal range

No opacity anywhere. The bands are **opaque fills mixed toward the land tone**,
because stacked translucency compounds and the fifth band would be a different
colour depending on what is under it.

At medium, each band is 65% of the way from `--atlas-land` to its
`HYPSOMETRIC` colour:

| band | colour at C | |
|---|---|---|
| ≥ 200 m | `#dbd7c2` | foothill |
| ≥ 600 m | `#d8ceb4` | upland |
| ≥ 1,200 m | `#d3c5ac` | high ground |
| ≥ 2,000 m | `#e3ddd2` | mountain, light stone |

Luminance spread 0.159. Label ink against the darkest band: **9.7:1**.

**The aperture still works.** The signature is read as the step between the
wall the page shows through the corners and the ground inside the opening. The
palest band measures 1.26:1 against `--paper` where the flat land measures
1.33:1 — the step moves by seven hundredths and the reveal, which is what
carries the door in the dark preference, is untouched.

## 8. Mobile behaviour

At 390 the plate is 358 × 127 CSS pixels and the aperture is rx 179, ry 43.
The bands are geometry in a scaled viewBox, so they cost nothing extra to draw
small and they do not need a phone rule — this is the one layer on the plate
that is *better* on a phone than type is, because a tonal mass survives scaling
and a 4-pixel glyph does not.

Measured at three widths: the terrain reads at C at all three; at B it reads at
1280 and 704 and not at 390. That is the whole reason C is the answer.

## Where terrain is allowed

Terrain earns its place where terrain is part of the identity of the place,
which is a **classification** and therefore something this atlas may author —
the Data Integrity Rule permits authoring "Chamonix is a mountain town" and
forbids authoring its height.

| | terrain |
|---|---|
| Chamonix, Zermatt, the Dolomites | yes |
| a Norwegian fjord destination | probably; the fjord is the relief |
| Venice | no — the subject is water and a street plan |
| Paris, Amsterdam | no — flat, and relief would say something false by implying it is worth showing |

Destination and journey illustrations only. Not the country plates, not the
atlas, not `/map`. No layer is added merely because the source dataset exists.

## Integration, and what changed on the way

### Zoom 6, not zoom 7 — and the licence got cleaner

The prototype ran at zoom 7. Rendered against the same Chamonix frame the two
are indistinguishable: the field is smoothed with a 5 km kernel either way, so
865 m of detail is thrown away before anything is drawn. Zoom 7 over the whole
extent would be **728 tiles**; zoom 6 is **182 tiles and 10.5 MB**, and its
land is GMTED2010 with ETOPO1 in the sea — two US Government public-domain
sets, without even the SRTM that zoom 7 brings in. Smoothed harder, at an
8.6 km kernel, the Arve and Aosta valleys merge into one mass and the 2,000 m
band nearly disappears, so this is not "coarser is fine": it is the one step
where the picture does not change and the bytes do.

**The whole extent is fetched, not only the mountains**, because whether a
destination gets terrain is a measurement and Paris has to be measured to be
found flat.

### One palette, not two — measured out

A second, fainter strength was built first, at 40% of the way to the
hypsometric colours, for exactly the flatter places the owner asked to have
room for. It was wrong twice over:

* **It could not be seen.** The only band Bergen has is 0.043 of luminance
  from the land tone at that strength — a layer that ships 23 KB and renders
  as nothing, which is what this repository calls dead code that looks like a
  decision.
* **It broke the scale.** Two strengths make `#d8ceb4` mean 600 m on one page
  and something else on another. A hypsometric scale that is not absolute is
  decoration that looks like one.

The reduction the owner asked for was already there, for free: **an absolute
scale reduces itself.** Bergen's ground crosses one band boundary and gets one
step; Chamonix's crosses four and gets the pale stone at the top. Rendered
side by side that is exactly the difference between "there are hills here" and
"this is the high Alps", and nothing had to be dimmed to say it.

### The suitability rule is a measurement, and its first version was biased

Not a list of mountainous places — that would be an authored measurement, and
the one thing this repository does not do. Two numbers, taken from the same
model that draws the bands and stored beside them in
`data/geo/terrain-lod1.json`:

| | |
|---|---|
| **spread** | the 95th minus the 5th percentile of ground within 40 km |
| **crest** | the 95th percentile itself |

Terrain is drawn when spread ≥ 300 m **and** crest ≥ 600 m. The second test
exists because the 200 m band is 0.013 of luminance from the land tone — the
quietest thing on the plate, deliberately — so a place whose ground reaches
only that band would ship a layer nobody can read.

**The first version measured sea.** It clamped water to zero and included it,
so a percentile over a circle that is four-fifths sea is a percentile of sea:
Athens, in a basin ringed by Hymettus, Penteli and Parnitha, measured *lower*
at 40 km than at 25, because widening the circle added water rather than
mountains. Nice measured 1,200 m once the water came out. That is the same
shape of failure as deriving `city_type` from a dataset of populated places
and getting one village in 157: **a derivation can be systematically biased
against exactly the cases it exists for.**

**And 25 km was too tight.** It measured Bergen at 387 m — a town of seven
mountains — because at 1.7 km a cell Ulriken's 643 m averages down to a
shoulder and the fjord walls are just outside the circle. 40 km reads Bergen
at 707 m and still leaves Venice at 41, Amsterdam at 11 and Paris at 150. A
radius wide enough to find mountains everywhere would find them in the
Netherlands.

| | spread | crest | terrain |
|---|---|---|---|
| Zermatt | 2,002 m | 3,050 m | yes |
| Chamonix | 1,798 m | 2,752 m | yes |
| Ortisei & the Dolomites | 1,384 m | 2,162 m | yes |
| Bergen | 702 m | 707 m | yes |
| Athens | 586 m | **598 m** | no |
| Paris | 102 m | 150 m | no |
| Venice | 41 m | 41 m | no |
| Amsterdam | 11 m | 11 m | no |

**147 of 319 destinations** draw relief, and **six of seventeen** journeys.
Athens misses the crest test by two metres, which is recorded here rather than
smoothed over: a threshold has to fall somewhere, and the point of stating it
is that nobody had to pick Athens.

### The frame cap

Relief answers "what kind of ground is this place in". Across a continent it
answers a different question and becomes a physical map of Europe. Measured:
the Arctic-to-Mediterranean route frames 4,207 km and drew every band in the
dataset — **787 KB on one page**, with the Alps a smudge the width of a thumb.

`TERRAIN_MAX_KM` is **1,500 km**, chosen from the seventeen journey frames
rather than picked as a round number: it admits the six that are regional (the
Alpine Grand Tour at 1,278 km, the Carpathian Arc at 1,388, the Adriatic Run
at 1,449) and excludes the eleven that cross the continent, the nearest of
them at 1,691. A destination plate is 590 km and never comes near it.

### The boundary, unfolded

`cartography.ORDER` has always put `country-bounds` above `terrain`;
`FOLDED` said that layer was carried by `land` and that separating it was what
"terrain will force". It did. A frontier here is a stroke on the land path, so
the bands paint over it — the prototype's first render carried a clear
France/Switzerland/Italy border without relief and none with it. The
stroke-only pass costs about 5 KB against 24 KB of terrain, and is emitted
only on the plates that draw relief. Re-emitting it also reproduced the
*frontier is a worm* failure the stylesheet already documents, because the
duplicate was written without `vector-effect: non-scaling-stroke`: **a rule
that exists is not a rule that is inherited.**

### What the eight-destination benchmark found that terrain did not cause

Chamonix, Zermatt and Ortisei were unmistakable at once. Bergen and Athens
were not — and the reason had nothing to do with relief. **lod1 simplifies the
coastline at 0.04 degrees, which is 4.4 km, which is nine pixels on a 590 km
plate**: Attica came out as a wedge, the Cyclades as lozenges, and the
Norwegian coast as a staircase. Every coastal destination has looked like that
since these maps were built, and nobody had put a coastal frame and an Alpine
frame side by side.

lod2 is 0.012 degrees — 1.3 km, under three pixels at the same scale — and it
was already in the repository, one file per country carrying that country and
every neighbour within 0.75 degrees. `geo.local()` merges it over the
continental file for frames tighter than about 980 km, so this cost **no new
data**. Athens is now Attica and the Saronic Gulf; Bergen is fjords.

## Page weight

| | bytes |
|---|---|
| Chamonix before any of this | 55,344 |
| Chamonix now (terrain 24 KB, boundary 5 KB, lod2 coast) | 93,039 |
| the heaviest page on the site, unchanged | 452,785 |
| `weight.max_page_kb`, the recorded ceiling | 440 |

`data/geo/terrain-lod1.json` is 677 KB and `data/raw/terrarium/` is 10.5 MB.
Neither reaches a browser.

## What holds it

* `checks.py` — relief is an illustration layer only, on the destination and
  journey families only; a plate draws it exactly when the measurement says
  so; the boundary pass is present wherever relief is; the four band fills are
  the approved 65% mix and there are exactly four; no frame past the cap
  carries it. Proved red three ways.
* `invariants.py` — `map.relief_pages`, a floor, because six derivation
  stages each of which can silently return nothing look identical to a page
  that was always flat.
* `process.py --check` — the terrain file's fingerprint: every input byte,
  every parameter, and `relief.py`'s own source.

## What is still open

1. **Small islands measure flat and get nothing.** Santorini's caldera rim is
   about a kilometre wide against a 1.7 km cell, so the model shows sea. That
   is honest — we cannot draw what we cannot resolve — and it is a limit of
   zoom 6 rather than of the approach.
2. **A place plate inherits its destination's relief**, which is right (it is
   the same picture of the same town) and has not been looked at on its own.
3. **The `here` wash is still under the terrain** on the families that have
   one. No destination plate highlights a country today, so nothing is wrong;
   a country plate that gains relief would need `selected` unfolded the same
   way `country-bounds` just was.

## Vienna, and why the threshold is right

Asked to give Vienna its Wienerwald, and asked for a good method rather than
an exception. The method was: measure before changing anything.

**First, a correction that changed the answer.** Vienna was reported here as
102 m of spread and a 150 m crest. That is Paris. Vienna reads **332 m and
480 m** — it passes the spread threshold and misses the crest threshold by
120 m, which makes it a near miss rather than a flat city, and made the
question worth asking properly.

**The near misses are a cliff, and that is a separate finding.** 53
destinations pass spread and fail crest, and the top of that list is not a
gentle tail:

| | spread | crest | short by |
|---|---:|---:|---:|
| Córdoba | 466 | 598 | **2** |
| Athens | 586 | 598 | **2** |
| Naples | 592 | 598 | **2** |
| Kefalonia | 576 | 591 | 9 |
| Rome | 576 | 587 | 13 |
| Stavanger | 578 | 582 | 18 |

**Athens is the case this measurement exists for** — `relief_at`'s own
docstring cites it, a basin ringed by Hymettus, Penteli and Parnitha — and it
fails by two metres. A rule where Athens gets nothing and something at 601 m
gets four bands is a coin toss at the boundary, not a measurement. That is
worth fixing and it is not fixed here; it needs its own experiment, because
the honest instrument is whether the DRAWN layer is visible rather than
whether a percentile clears a number.

**And the obvious instrument for that measured the wrong thing.** Computing
the fraction of each destination's plate frame the bands would cover gives
Vienna 73% at 200 m and 24% at 600 m — more than Athens, more than Rome, more
even than Paris at 27.7%. All of that is the Alps and the Carpathians and the
Massif Central: a destination frame is 590 km across, so a frame-wide measure
answers a question about the neighbourhood rather than about the place. That
is the trap `relief_at` was written to avoid, walked into by the check meant
to test it, and it is the third instrument in one session to answer a
different question from the one asked.

**Measured correctly, at 40 km, Vienna is a lowland city with wooded hills.**
The Wienerwald is real and it is under 600 m, which the absolute band scale
deliberately renders at 0.013 of luminance from the land tone — a layer that
ships kilobytes and cannot be seen. The threshold is not wrong about Vienna.

**So Vienna's physical identity is not relief. It is the Danube**, which is
already drawn on its map as one of six anonymous blue lines while
`data/geo/hydrology-lod1.json` names all 153 rivers and ranks the Danube at 2.
The map has the name and does not print it. That is the buildable answer to
"Vienna should look like Vienna before the visitor has read much text", and it
needs a water-label family that takes the `--z` compensation, counts toward
`dense_class()` and is marked by `phone_declutter()` — because the last label
family added here inherited none of those and printed Monte Rosa through
Chamonix's own name at 390.
