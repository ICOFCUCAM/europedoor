# The terrain prototype — Chamonix, four strengths, one decision

**Question asked:** does restrained terrain materially improve the recognition
and sense of place of an Alpine destination?

**Answer: yes, and not marginally.** Accepted at MEDIUM strength. Nothing is
integrated yet; what follows is the eight things the brief asked to be written
down first.

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

## What integration still needs

1. `country-bounds` unfolded from `land`, so a boundary is drawn above the
   terrain rather than under it. This is the one structural change.
2. A renderer in `cartography.py` for the `terrain` layer, and the derived
   rings written to `data/geo/` under the same staleness contract as the
   coastline — `unwritten()` correctly refuses the file until the renderer
   exists, which is why nothing is in `data/geo/` yet.
3. The per-destination classification above, authored from a stated vocabulary.
4. A wider fetch for the journey frames, at zoom 7 and no deeper, with the
   provenance header recorded per tile as the six here are.
5. A check that the bands are what the DEM says: the point-in-polygon test
   that found the saddle bug, run over the shipped rings.
