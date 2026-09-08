# The map

EuropeDoor draws Europe from open geographic data that it hosts itself. There
is no map provider, no API key, no tile server and no request that leaves this
domain to draw a coastline. That is a firm product decision — **EuropeDoor does
not pay for maps** — and this document is how it is kept.

    Natural Earth (public domain)
            │  scripts/map/fetch.py     download, hash, record
            ▼
    data/raw/*.geojson.gz              committed, verifiable
            │  scripts/map/process.py   clip, simplify, LOD, join to the graph
            ▼
    data/geo/*.json                    committed, 1.7 MB, WGS84 lon/lat
            │  tools/build.py           projected into SVG at build time
            ▼
    site/ + site/api/geo/              static files
            │
            ▼
    our CDN ──────────────────────────► the browser

Every arrow is a script in this repository. Nothing in that chain is a service
with a bill attached, and nothing in it can acquire one without somebody
editing `docs/data-licenses/sources.json`, which is next to the licence
records on purpose.

## The renderer: why this is SVG and not MapLibre GL JS

The map brief names MapLibre GL JS, and MapLibre is the right renderer for a
map that carries roads, trails and street-level OSM data. It is the wrong one
for the map this product needs today, and the numbers are not close:

| | |
|---|---|
| all of Europe's borders at the detail a continent view uses | 88 KB of JSON |
| the same, drawn, as SVG path text | ~34 KB |
| the coarse level that actually ships inline | ~19 KB |
| MapLibre GL JS itself, before any data | ~800 KB raw |

The renderer would be eight times the weight of everything it renders. It
needs WebGL. It needs vector tiles, which needs `tippecanoe`, which is a build
dependency this repository does not have and thousands of tile files where we
have fifty-two. And it needs `worker-src blob:`, which would be the first hole
in the `default-src 'none'` policy the whole site is arranged around.

**This is reversible and deliberately so.** `data/geo/` holds WGS84 lon/lat,
not pixels, because projection is a rendering decision. The day the map
carries roads and trails, the same pipeline output feeds a tile build with
nothing thrown away — the clipping, the simplification and the level-of-detail
ladder are the expensive parts and they are already done. What changes is the
last stage, not the first three.

Until then, the honest summary is: this map does more than the old one, costs
nothing to run, adds no third-party origin, and works with JavaScript turned
off.

## Levels of detail

One geometry file at every zoom is the mistake the LOD ladder exists to avoid:
the detailed file draws fjords three pixels wide at continent zoom, and the
coarse one turns Norway into a hexagon the moment you zoom in.

| level | source | tolerance | when |
|---|---|---|---|
| `lod0` | Natural Earth 1:110m | 0.055° | the whole continent. **Inlined in the page**, so the map draws with no JavaScript and no fetch |
| `lod1` | Natural Earth 1:50m | 0.04° | fetched once when zoom passes 1.6× |
| `lod2` | Natural Earth 1:50m | 0.012° | one file per country, fetched when a country is opened; carries its neighbours so the country is not floating in white space |

The thresholds were chosen by rendering, not by theory. `lod0` began at 0.10°
and made Iceland a blob; 0.055° is where it stopped looking wrong at the size
it is actually drawn.

## What the layers are, and the one that is missing

| layer | source | state |
|---|---|---|
| 1 · country polygons | Natural Earth | built |
| 2 · country borders | Natural Earth (the stroke on the polygon) | built, toggleable |
| 3 · regions | **our own data** — which destinations belong to which region | built, toggleable |
| 4 · NUTS regions | Eurostat / GISCO | **blocked** — see `docs/data-licenses/eurostat-gisco-nuts.md` |
| 5 · destinations | our own data | built, toggleable |
| 6 · places | our own data | built, toggleable |
| 7 · rivers, roads, trails, railways… | not yet sourced | modular, not hard-coded |

Layer 3 is drawn as its destinations grouped and labelled, with hairlines to
each. It is not a boundary and does not pretend to be one: we hold region
*membership* and we do not hold region *geometry*. A convex hull round Bergen
and Ålesund labelled "Vestland" would look like an answer and be a guess.

## The map does not keep a list of anything

Every country, region, destination and place on the map was read from
`data/countries/*.json` at build time and carries the id of the record it came
from. Add a region to the Atlas and it appears on the map without anybody
remembering to update the map, because there is nothing to update. The country
shapes are `<a href>` elements with the real URL in them before any JavaScript
runs:

    /map            →  /europe/norway
                    →  /europe/norway/vestland
                    →  /europe/norway/vestland/bergen

With scripting off, that ladder is plain links. With scripting on, the first
click is intercepted and opens the panel instead; a second click on the same
country follows the link.

## One projection

Equirectangular, corrected at the middle latitude of whatever extent is being
drawn. `pages.MAPPROJ` is the continent one and everything that draws Europe
uses it, so a coastline and the city on it cannot disagree about where they
are. The browser gets the same six numbers as an inert JSON block and applies
the same formula, rather than reimplementing the projection — a second copy of
a projection is a second copy that drifts.

The version this replaced claimed in its docstring to be corrected at 52°N and
then multiplied x by `cos(52°) / cos(52°)`, which is 1. Europe had been drawn
60% too wide since the map was written, and nobody caught it because there
were no coastlines to look wrong: 313 dots on an empty rectangle are the right
shape by definition.

## Running it

    python3 scripts/map/fetch.py              download anything missing
    python3 scripts/map/fetch.py --verify     check the bytes against the register
    python3 scripts/map/process.py            rebuild data/geo/
    python3 scripts/map/process.py --check    fail if data/geo/ is stale

`fetch.py` is the only file in this repository that opens a network socket,
and it is deliberately not part of `tools/build.py`: the build must run on a
host with no internet and produce identical pages. Fetching is something a
person does when a dataset version changes.

`process.py` is a pure function of `data/raw/` and its own source, which is
why `--check` can assert that what is committed is what the pipeline produces.
Same contract as `site/`.

## The rules that will catch somebody out

**`data/geo/` is generated. Do not edit it.** It carries a `$comment` saying
so. A hand-fixed coastline survives until the next `process.py` and no check
will tell you it went.

**No dataset without a licence record first.** `fetch.py` refuses to open a
socket for a source that has no entry in `docs/data-licenses/sources.json` and
no `.md` file next to it. A licence written after the download is a licence
written to fit what was already done.

**The `blocked` list is a decision, not a backlog.** Eurostat NUTS and
OpenStreetMap are both in it, both for stated reasons, and `fetch.py` exits
non-zero if you name either. Read the licence document before arguing with it.

**Do not make the dots imitate the coastline.** The old map's note said the
shape of Europe was "Europe's cities describing Europe's outline by
themselves". That was an honest description of a limitation and it is now
false. There is real geometry; use it.
