# AWS Terrain Tiles — elevation, and the three datasets underneath it

**Status: integrated. Zoom 6 over the whole extent, and zoom 7 over one
frame.** The 182 zoom-6 tiles are what ships: they derive the hypsometric
bands drawn on 261 destination and journey plates and on the homepage hero.
The six zoom-7 tiles are the Chamonix prototype and are kept because the
prototype's measurements are quoted in `docs/terrain-prototype.md`.

## What this is

Amazon publishes the Mapzen/Tilezen *Terrain Tiles* as an
[AWS Open Data](https://registry.opendata.aws/terrain-tiles/) set:
web-mercator PNG tiles in the **terrarium** encoding, where each pixel is one
elevation in metres,

    metres = (R * 256 + G + B / 256) - 32768

The tiles themselves are a *composite*. They are not one dataset with one
licence, and that is the whole reason this document is long.

## The licence problem, and how it is avoided rather than accepted

The [attribution document](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)
lists eleven contributing sources. Several require attribution and two carry
terms this repository has already refused elsewhere in spirit:

| contributor | terms |
|---|---|
| EU-DEM (Copernicus / EEA) | attribution required — "Produced using Copernicus data and information funded by the European Union" |
| data.gv.at (Austria) | CC BY 3.0 AT |
| Kartverket (Norway) | CC BY 4.0 |
| data.gov.uk LIDAR | UK Open Government Licence v3 |
| SRTM, GMTED2010, 3DEP | **US Government, public domain.** Credit *requested*, not required |
| ETOPO1 | **NOAA, public domain.** Not subject to copyright in the United States |

**EU-DEM is the one that matters here**, because this is an atlas of Europe
and EU-DEM covers almost all of it. Accepting it would mean accepting a
Copernicus attribution obligation across every page that draws relief —
the same shape of decision as Eurostat NUTS, which is on the `blocked` list
because nobody here has read the provisions.

It is avoided by **zoom**, not by hope. Tilezen's
[data sources](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md)
document states which dataset fills which zoom:

| zoom | land | ocean |
|---|---|---|
| 4–6 | GMTED | ETOPO1 |
| 7–8 | **SRTM**, GMTED above 60°N | ETOPO1 |
| 9 | SRTM, **EUDEM in Europe**, GMTED above 60°N | ETOPO1 |
| 10+ | SRTM, data.gv.at, Kartverket, data.gov.uk, ArcticDEM… | ETOPO1 |

**EU-DEM enters at zoom 9. Every national dataset with a CC BY obligation
enters at zoom 10.** At zoom 7 the land is SRTM and GMTED and the sea is
ETOPO1 — three US Government public-domain datasets, and nothing else. At
zoom 6 it is GMTED and ETOPO1 and not even SRTM.

So the rule this repository fetches under is: **zoom 7, and no deeper**, and
what actually ships is a zoom deeper still. A zoom-9 tile of the Alps is a
different licence position wearing the same URL shape, which is exactly the
failure mode `refuse_matching` exists for elsewhere. Zoom 8 is also SRTM and
would also be clean; 7 is the limit that was verified tile by tile, so 7 is
what is recorded, because a limit set at what was actually checked is a limit
somebody else can re-check.

**The integration chose 6 for a cartographic reason and inherited a safer
licence position as a side effect.** 1,730 m a cell is the resolution a
restrained tonal field wants: at zoom 7 the bands carry detail that reads as a
GIS hillshade at plate size and costs four times the bytes for it. That the
land at that zoom is GMTED alone — one US Government public-domain dataset —
is a consequence rather than the argument, and it is why the credit names
GMTED2010 and ETOPO1 and not SRTM.

## It is verified per tile, not assumed

The service publishes the contributing images for every tile it serves, in
the `x-amz-meta-x-imagery-sources` response header. Each row in
`sources.json` carries that header **as returned for that exact tile**, so
the claim above is evidence rather than a reading of a table. Across all 188
tiles fetched, the headers name only `srtm/*`, `gmted/*` and `etopo1/*` —
and split by zoom, the six prototype tiles at 7 name srtm on 71 of their
contributing images while the 182 shipped tiles at 6 name gmted on 176 and
etopo1 on 157 and srtm on none.

If a re-fetch ever returns a header naming anything else, the recorded
`provenance` string will no longer match and the difference will be in the
diff. That is the only honest form this guarantee can take: the composite is
Amazon's to change.

## Credit

None of the three is *required*. The USGS and NOAA both *request* credit, and
this atlas already credits Natural Earth on the same reasoning — a reader
looking at relief is entitled to know which survey measured it. So any page
that draws terrain names:

    Relief from GMTED2010 (USGS) and ETOPO1 (NOAA), public domain.

**This sentence said "SRTM and GMTED2010" for three commits and was wrong.**
It was written against the six zoom-7 prototype tiles, whose imagery header
names `srtm/*` on 71 of their contributing images. The integration went to
**zoom 6**, and the header on those 182 tiles names `gmted/*` on 176 and
`etopo1/*` on 157 and `srtm/*` on none. Crediting a survey whose data is not
in the picture is the same class of untruth as crediting none, and it lasted
because the promise lived in prose here rather than in a check. `checks.py`
now derives the credit's dataset list from the `provenance` header recorded
in `sources.json`, filtered to the zoom `data/geo/terrain-lod1.json` says it
was built at, and asserts every page carrying `lyr-terrain` names each one.

**ETOPO1 is named even though no band boundary is traced through the sea.**
The grid is smoothed with a three-pass kernel before it is traced, so an
ocean cell pulls the 200 m contour about five kilometres inland — every
fjord, every Greek island and the whole Italian coast is inside that. A
dataset that moves the line is a dataset that drew it.

`attribution_required` stays `false` on these rows, because it is false; the
credit is drawn anyway. Setting the flag to `true` when the licence does not
demand it would make `checks.py`'s hardening branch — the one that exists for
the first genuinely share-alike byte — fire on a false alarm and be ignored.

## What is derived, and what is thrown away

`scripts/map/relief.py` decodes the tiles, smooths the grid, and traces
**hypsometric band boundaries** at 200, 600, 1,200 and 2,000 metres into
lon/lat rings. The bands are the only thing that ships. No pixel of the
source reaches a page: there is no `<img>` in this product and there is not
going to be one for a map.

The tiles stay in `data/raw/` because the build must run on a host with no
internet and produce identical pages, which is the same reason every Natural
Earth file is committed.

## Sources

* Registry entry: https://registry.opendata.aws/terrain-tiles/
* Attribution: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
* Data sources and zoom table: https://github.com/tilezen/joerd/blob/master/docs/data-sources.md
* SRTM distribution policy: public domain, USGS
* GMTED2010: public domain, USGS
* ETOPO1: public domain, NOAA/NCEI
