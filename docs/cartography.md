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

## The four layers

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
