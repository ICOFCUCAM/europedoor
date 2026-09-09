# The EuropeDoor Atlas — cartographic art direction

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
