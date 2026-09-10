# The EuropeDoor Atlas — cartographic art direction

## The rule that governs the benchmark

> **The reference plate is art direction and never geographic truth.** All
> geometry, positions, borders, rivers and terrain come from authoritative
> datasets in `data/geo/`, fetched by `scripts/map/fetch.py`, hashed and
> registered in `docs/data-licenses/`. Nothing is ever traced, eyeballed or
> transcribed from the reference.

This matters more here than it would elsewhere, because the reference plate
is **itself generated**: its coastline, its rivers, its region boundaries and
its relief are an image model's idea of Portugal, not Portugal. Copying any
of it would put invented geography on 1,033 pages under the same aperture
that carries the real thing, and a reader has no way to tell the two apart.

What the reference is for: palette, the four-step water, the type hierarchy,
the key, the locator, the frame, the restraint. What it is not for: where
anything is.

The existing guards already catch the data half — `fetch.py` refuses a source
with no licence row, `checks.py` hashes every raw file against the register,
and the validator refuses `iso3`, coordinates and population as authored
keys. The guard for the drawing half is this paragraph and the fact that
every layer in the renderer reads a registered file or nothing at all.


**Principle: Europe is not displayed as data. It is revealed as geography.**

The country plates were a blue polygon on a near-black field with a thin
outline and an arch crop. Technically consistent, and the association it
carried was GIS software: a dashboard, a satellite interface, a database
selection state. The geography under it was sound; the visual language was
not.

## The split that decides everything else

**The pictures are paper. The instruments are graphite.**

| drawing | it is | ground |
|---|---|---|
| country plate, destination view, setting plate | a picture, looked at | paper |
| `/map`, `/plan`, `/search`, `/discover`, the country reference map | an instrument, operated | graphite |

That is what the two worlds have always meant — not a theme, but whether the
reader is browsing or working — and it is why black remains available for the
compositions that earn it rather than being the default for all 824 figures.

## The ocean, in four steps

    Deep ocean     #123f55
    Mid ocean      #28657a
    Shallow water  #5d91a0
    Coastal water  #8eb2b5

A flat pale fill made the water a surface the land was pasted onto. These
four are **cast, not stroked**: three soft shadows of the land silhouette,
widest and deepest first, so the water lightens as it approaches a shore.

**It is distance from land, and never a claim about depth.** The coastline is
the one thing that can tell us this, the atlas holds no bathymetry, and
nothing here implies a number of metres.

The first version was three `<use>` of the land group and **painted nothing at
all**. A `<use>` shadow tree is still matched by the selectors that style the
original paths, so every clone kept the land's own paper fill and 0.9px coast
stroke, and the wide stroke set on the `<use>` never reached it. It measured
correctly on the `<use>` element itself and was not on the page — the fourth
time in this stylesheet that a treatment rendered as the thing simply not
being there. A filter needs no second copy of Europe and cannot lose a
cascade fight.

## Land is one family, and the subject is a wash

The subject used to be a light blue, which worked against pale water and
reads as **sea** against an Atlantic one: Greece came out the same family of
blue as the Aegean around it. An atlas separates the country it is about by
making it the brightest land with the finest heaviest edge, not by turning it
into another shade of water.

And it is a **wash, not a fill**, so whatever is under it survives. An opaque
country hides everything the terrain layers will eventually put there — the
Alps, the Massif Central, the Loire basin — and a plate whose subject is the
one place you cannot see the ground is the wrong way round.

The boundary is 1.1 against the coastline's 0.9 and the frontier's 0.7. A
soft luminous edge needs a stroke-only second pass over the same geometry,
which is the same refactor terrain will force.

## The terrain chain, decided and waiting on one file

    DEM → hypsometric tint → hillshade → texture → country mask →
    administrative boundaries → hydrography → labels

Only the **DEM** is missing. Everything after it is a transform of the DEM and
is written down in `cartography.HYPSOMETRIC` and `cartography.DECIDED` as data
rather than as prose, so the day it lands the tint is a table lookup and not
an argument.

| band | tint | reads as |
|---|---|---|
| 0–200 m | `#dfe0cf` | lowland, muted green-grey |
| 200–600 m | `#d9d6bd` | foothill, soft olive |
| 600–1200 m | `#d5c9a8` | upland, warm ochre |
| 1200–2000 m | `#cdbb9c` | high ground, pale brown |
| 2000 m+ | `#e6e0d6` | mountain, light stone |

Five steps, because four cannot show a foothill and six begin to read as a
legend a reader has to consult. Warm as it rises and never saturated: height
is **felt**, and the typography stays dominant over the ground.

## Three voices of context

    subject      the brightest land, the finest heaviest edge
    near         warm parchment
    mid / far    increasingly quiet, still parchment

A plate of France used to be France and twenty polygons of equal weight, all
asking to be read. The band is **measured, not listed**: a country's distance
from the subject on this drawing, in the drawing's own units, so it is the
same judgement on a plate of Luxembourg and a plate of Ukraine.

The first version measured the gap between bounding boxes, which is zero the
moment two boxes overlap on either axis — so every country on France's plate
came out `near`, Austria included. A box is not a place. It is centre to
centre now.

And the quieter bands are mixed toward a **warm grey, not toward the sea**:
mixing toward the water desaturates and darkens them into exactly the blue
they have to be distinguished from, and Germany and Spain went quiet by
becoming sea.

Nothing is hidden. A far country keeps its shape, its coastline and its
`<title>`, because a reader looking at France still needs to see that Spain
is underneath it.

## The cartographic type hierarchy

| feature | mark | type |
|---|---|---|
| country | — | tracked serif caps, quiet, under the place names |
| capital | a **star** | ink, bold |
| city | a filled dot | ink on a paper halo |
| destination | an **outlined** dot | ink on a paper halo |
| sea, range, river | *waiting on a fetch* | tracked caps · italic serif · small italic |

Every place used to be the same dot and the same name: a database printed on
a map. `city_type` is classified for all 319 destinations already, so this is
that classification **drawn** rather than anything authored. A star rather
than a bigger dot, because a bigger dot says *more* and a star says
*different in kind*.

The country's own name on the plate does a second job: the recognition test
strips the wordmark and the page title, and a plate that names what it draws
survives that where a shape alone does not.

## What was fetched, and what the plates gained

**The proxy reaches raw.githubusercontent.com.** Five Natural Earth themes
were registered, fetched, hashed and processed in one pass, so four of the
declared-and-empty layers now draw real data:

| dataset | layer | in the extent |
|---|---|---|
| 1:50m rivers and lake centrelines | rivers | 153 river parts |
| 1:50m lakes | rivers | 65 lakes |
| 1:50m marine polygons | water labels | 21 named seas |
| 1:50m physical geography regions | feature labels | 20 named ranges and plains |
| 1:10m named elevation points | summits | 99 named peaks with heights |

**Scalerank 6 is the whole of Natural Earth's river set, and it is the right
cut here.** The Rhône, the Garonne, the Po and the Duero are rank 6, and a
map of Europe without the Rhône is not restraint, it is an omission. The
publisher's ranks are about how much of the *world* a sheet shows; this atlas
shows one continent, so the whole set clipped to the extent is about a
hundred and thirty watercourses — an editorial number, not the four thousand
an unfiltered extract gives.

**The summits are not relief and are never called relief.** A hillshade needs
an elevation model this repository does not have. What it has is 99 named
peaks with the height somebody else measured, and a reader sees where the
high ground is because they cluster along the Alps, the Caucasus and the
Pyrenees. The 1:50m file has **three** in the whole of Europe — Elbrus, Mont
Blanc and one depression — which is why this one is 1:10m.

## Rivers: written, registered, one command away

The renderer is **written, not stubbed** — proved by dropping a test file in
and watching the layer appear in the stack in the right position, then
removing it and watching it go. Four datasets are now in the register under
`awaiting_fetch`, all Natural Earth, all under the same public-domain terms
as the land already here, so **no licence decision is waiting on anybody**:

| dataset | fills | selection |
|---|---|---|
| 1:50m rivers and lake centrelines | rivers | `scalerank ≤ 5` |
| 1:50m lakes | rivers | `scalerank ≤ 4` |
| 1:50m marine polygons | labels | named seas and oceans |
| 1:50m physical geography regions | labels | named ranges and basins |

The selection matters as much as the licence: Natural Earth ships several
thousand watercourses and this atlas wants the Loire, the Seine, the Rhône,
the Garonne and the Danube. Hundreds of tiny streams is the OpenStreetMap
default look, which is the thing this cartography exists not to be.
`checks.py` refuses a row that does not say which layer it fills and what it
selects, and refuses one whose file is present — a fetched row must move to
`sources` with its hash, or the bytes nobody hashed are the ones that ship.

The last of those four is worth naming separately: **named ranges and basins
are what let a reader see where the Alps are before any DEM exists.**

## The pipeline

    GEOGRAPHIC DATA ─┐                        ┌─ VISUAL STYLE
      coast          │                        │   palette
      borders        ├──▶ cartography.py ◀────┤   relief
      rivers         │    the renderer        │   typography
                     ▼
              terrain · water · labels
                     ▼
                aperture / arch

`tools/lib/cartography.py` is the renderer and the only thing that holds both
sides. Geography comes in as projected paths and knows nothing about colour;
style comes in as a declaration of which class each layer paints through and
knows nothing about geography.

**Nothing in the renderer emits a colour.** A `style="…"` attribute anywhere
would force `style-src` open on all 1,033 pages, which is why there is not one
in this repository. `checks.py` asserts the stylesheet carries a rule for
every layer the renderer can draw, so a layer cannot be added and silently
render as nothing — the failure this codebase has made three times on
specificity alone.

**Why this replaced inline composition rather than tidying it.** Five families
each fetched their own geometry, wrote their own groups and decided their own
paint order. The cost was never duplication; it was that there was nowhere to
add a layer. Terrain sits above the land fill and below the coastline, rivers
above terrain and below the coast, a route above everything but the labels.
With five inline compositions there are five opinions about that, and the
first one to be wrong is invisible: a river drawn over a coastline still looks
like a river.

Three layers are **held but folded** into the land path's own stroke —
coastline, country boundaries and the selected-place emphasis — because a
country is one filled, stroked path at this level of detail. `FOLDED` records
each one and what carries it. Splitting them needs a stroke-only second pass
over the same geometry, about forty per cent more bytes on these pages, and
**terrain will force it**: relief cannot sit under a coastline and over a land
fill while the two are one path.

## Cartography v2 — the fourteen layers

The stack is declared in `geo.LAYERS` and walked by `pages.plate_stack()`.
Four of the fourteen have no data. **They are not stubs that draw something
plausible**: a layer whose dataset is absent emits nothing at all, not even an
empty group, because an empty `<g class="terrain">` on 1,033 pages is a claim
that the map has terrain and simply had none here. `terrain_paths()`,
`hillshade_paths()` and `hydrology_paths()` exist, return nothing today, and
**raise loudly** the moment their file appears without them being written.

| # | layer | data | held |
|---|---|---|---|
| 1 | ocean | none needed | yes |
| 2 | coastal water | derived from the coastline | yes |
| 3 | land | `country/*.json` | yes |
| 4 | terrain | `terrain-lod1.json` | **no** |
| 5 | hillshade | `hillshade-lod1.json` | **no** |
| 6 | rivers | `hydrology-lod1.json` | **no** |
| 7 | coastline | `country/*.json` | yes |
| 8 | country boundaries | `country/*.json` | yes |
| 9 | region boundaries | `regions-lod1.json` | **no, and refused** |
| 10 | cities | `data/countries` | yes |
| 11 | destinations | `data/countries` | yes |
| 12 | labels | derived | yes |
| 13 | route | derived | yes |
| 14 | selected place | `country/*.json` | yes |

### How the empty layers will look, decided now

Writing this down is what stops the day the data arrives from becoming a
fresh argument about style.

- **Terrain** — four steps and no more, from the land tone toward the warm
  accent. No hypsometric rainbow: in an editorial atlas height is felt, not
  read off a legend.
- **Hillshade** — one light from the north-west, at most 12% opacity,
  multiplied over the terrain tint and clipped to land. **Never over flat
  ground**, where it invents structure that is not there.
- **Rivers** — in the water colour, by stream order, always thinner than the
  coastline. A river drawn as heavily as a coast turns a country into a leaf.
- **Region boundaries** — dashed, lighter than a country frontier, labelled in
  the same small caps as a sea.

### What was built for the data that IS held

- **Coast treatment.** The soft band a printed atlas puts in the water along a
  coast, drawn by stroking the land silhouette under the land fill. Emitted as
  a `<use>` so the geometry is not paid for twice: about forty bytes a plate.
  It is a convention, **not bathymetry** — the atlas holds no depth data.
- **Boundary hierarchy.** Three weights: a frontier is lightest because it is
  context, a coast is the edge of the subject's world, the subject's own
  outline is the heaviest thing on the plate.
- **Label and city hierarchy.** The capital in cobalt and bold, destinations in
  ink, and the capital placed first so it wins every collision.
- **A Europe locator**, with the subject ringed, because a country filled at
  112px across the continent is three pixels a reader's eye never finds.
- **A key**, so a map stops needing a caption to explain its own dots.
- **A limestone rim** outside the reveal: the face of the wall, then the shadow
  of the cut, both from the same `arch_path()`.

## The four layers (v1, superseded above)

1. **The window.** The aperture, unchanged: `arch_path()` at rx = span/2, ry =
   34% of height, cut three ways. On paper it is read by its **cut edge**
   rather than by a tonal step from the wall, which is the machinery the dark
   colour-scheme preference already needed and already has.
2. **The land.** Warm paper, with a fine ink coastline. For the life of the
   embedded map this was `fill: none` — frontier lines on one dark field — so
   Portugal's Atlantic edge meant nothing and Greece's islands were fragments.
3. **The context.** Neighbours, drawn as the same land. `context` means "a
   country this atlas does not write about", which is a fact about the dataset
   and not about the ground; giving it its own tone drew a warm wedge across
   Cyprus, Azerbaijan and Türkiye that reads as a geographic claim.
4. **The places.** Every destination the atlas holds, marked and named, the
   capital in cobalt. Not links — the reference map below is the instrument.

## The palette, measured

| token | hex | role |
|---|---|---|
| `--atlas-sea` | `#bccfe0` | water, and the ground of the opening |
| `--atlas-land` | `#f2efe8` | land, warm paper |
| `--atlas-coast` | `#6d7f95` | coastlines and frontiers |
| `--atlas-here` | `#7fa1cf` | the subject country |
| `--atlas-hereline` | `#3f5f96` | its edge, and the place marks |

land : sea 1.39 · coast : land 3.57 · subject : land 2.31 · names (ink on
land) 16.35 · the scale bar 6.55 on water and 9.11 on land.

**The accent is drawn, not read.** Cobalt-deep names the place a destination
page is about and measures 4.27:1 on this water, under AA — so the *mark* is
cobalt and the *name* is ink in bold, which is the same rule that separated
`--signature` from `--door` everywhere else on the site.

## Scale decides composition

- **Micro-states** — Monaco, Vatican City, San Marino, Liechtenstein, Andorra,
  Malta and Luxembourg get a **setting plate**: four degrees of latitude, the
  neighbours drawn, the country a ringed point. Measured by the median
  straight segment of the principal ring over its own diagonal; above a tenth,
  the source holds a simplification rather than a shape. Monaco came out of
  the first build as a **triangle** four hundred pixels tall.
- **Every country** — the door's proportion follows the country, clamped to
  [0.62, 1.30], and every plate is hung at one height so what differs between
  two pages is the shape.
- **Outlying territory** — the frame is the principal landmass. Portugal's
  bbox reaches the Azores and the mainland filled **nine per cent** of it.

## What the benchmark has that this does not, and why

The owner's benchmark plate is the target. Four things on it are not here, and
three of them are **not build tasks**:

| missing | what it needs | status |
|---|---|---|
| terrain and relief | an elevation dataset through `scripts/map/fetch.py` | **BLOCKED**: no network from the build sandbox, and `fetch.py` refuses a source with no licence row. A human acquisition step |
| rivers and lakes | Natural Earth 1:50m rivers and lakes — public domain | **BLOCKED**: same. Cheap once a person can run the fetch |
| region boundaries (Norte, Centro, Alentejo) | Eurostat NUTS | **REFUSED, and it is an owner decision.** NUTS is copyrighted and its use is conditional on provisions nobody here has read; it is on the blocked list in `docs/data-licenses/` with `refuse_matching` patterns, and `checks.py` asserts the refusal on every commit. Nothing else in the dataset holds region geometry, which is why a region is drawn as its own destinations |
| higher-detail geometry (LOD 3/4) | Natural Earth 1:10m | **BLOCKED**: same fetch step. `data/geo/` holds lod0/1/2 today |

Achievable next, in order of value: the ocean and neighbour **names**
(`ATLANTIC OCEAN`, `SPAIN`), a Europe locator inset, a key, and a limestone
rim on the arch. None needs a licence or a socket.

## Naming the water: the last physical family

Summits, ranges and seas have carried names since the plates were built —
`peakname`, `fname`, `sname`, all through one placement rule and one density
pass. **Rivers were drawn with a `<title>` and nothing on the page**, so
Vienna's map showed six anonymous blue lines while the dataset that drew them
names all 153 and ranks the Danube at 2.

`river_points()` answers the three questions a label system has to answer —
what deserves a name on THIS map, where does it go, when does it disappear —
in the order subject, scale, importance, space.

**Subject first, and the test set is why.** Scored on drawn extent alone,
London's map named the **Lek**: a Rhine distributary in the Netherlands that
out-measures the Thames on a 900-unit frame reaching the Low Countries. The
system had learned to place a word rather than to understand a place. A river
passing within 16% of the frame width of the destination is that
destination's river and sorts above everything else.

**Importance is drawn extent in this frame, never the dataset's rank.**
Natural Earth's rank is a global hydrological figure. Measured across the
file: rank ≤ 3 is Danube, Donau, Volga, Nile, the Euphrates under three names
and three Danube delta arms — while **the Thames and the Po are rank 6**, the
Rhône is rank 6, and the Tiber and the Douro are not in the file at all. A
system built on rank names delta arms and never names the Thames.

**The same river is several features in several languages**, so ALIASES
merges them. That is an authored *classification*, which the Data Integrity
Rule permits; the extent underneath it is still derived. Running it over all
319 destinations and counting the output found two the design missed —
"Rhin" on four pages beside "Rhine" on six, "Tajo" on three beside "Tagus" on
three. **No single page showed both**, so looking at one map would never have
found it.

**The subject's river is all or nothing.** Bratislava named the **Tisza**,
300 km away and on the map only because the frame is wide, because the
Danube's anchors were all taken by place names and the next river down found
a gap. A map of Bratislava naming the Tisza is worse than one naming no
river: it does not fail to help a reader place themselves, it tells them
something false. Where a river passes near the subject it is the only
candidate; scenery is offered only on a map that has no river of its own.

**Ten anchors, nearest the subject first.** Six was not enough — a river
crosses the whole picture and its name needs one gap, and the country name
has been offered nine anchors for the same reason.

### What is open

**On dense city maps the river still loses every collision.** Vienna,
Budapest, Bratislava, Cologne, Paris and London draw no river name, not
because the selection is wrong — the Danube is correctly first on Vienna —
but because the label hierarchy puts every neighbouring destination's name
above every physical one.

That is a real question rather than a bug: **is the subject's own river
scenery, or is it part of the subject's identity?** If it is identity it
should outrank a neighbouring town's name. That changes what is drawn on 319
maps and it is settled by rendering and looking, not by counting, so it is
recorded here rather than guessed at.

**Rome will never get a river from this data.** The Tiber is absent from the
dataset, and inventing it is not available.
