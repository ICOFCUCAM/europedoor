# The EuropeDoor Cartographic Standard

**Visual character.** Editorial European atlas, modern luxury travel
publication, restrained geographic information design.

**Not:** Google Maps. OpenStreetMap default. A dashboard map. GIS software.
Dark-mode data visualisation. An AI fantasy map.

That last one is not rhetorical. The plate this cartography is drawn against
is itself generated, and its coastline, rivers, region boundaries and relief
are a model's idea of Portugal rather than Portugal. **It is art direction
and never geographic truth.** Everything drawn here comes from a dataset in
`data/geo/`, fetched by `scripts/map/fetch.py`, hashed and registered in
`docs/data-licenses/`. Nothing is traced, eyeballed or transcribed.

## The ten principles, and what holds each one

| # | principle | what holds it |
|---|---|---|
| 1 | **Terrain before polygon** | The fourteen-layer stack in `cartography.ORDER`. Terrain is **drawn** on the destination and journey families from a public-domain elevation model; hillshade and region boundaries stay declared, positioned and empty. A layer with no data emits nothing and raises the moment its file appears unwritten |
| 2 | **Geography before database** | A plate draws what it can name. Measured across the fifty country plates: **176 marks, 176 of them named.** Not one anonymous dot — and the homepage hero draws none at all, because nine restrained anchors were built, measured at 2.3 pixels, and removed rather than named |
| 3 | **Context before density** | Three voices — the subject, its neighbours in warm parchment, the rest quieter with distance — banded by measured distance on the drawing, not by a list |
| 4 | **Hierarchy before completeness** | One placement routine, one order: capital, city, destination, region. The capital is placed first and cannot be dropped |
| 5 | **Editorial composition before uniform cards** | Four page grammars, each with its own answers to the nine questions in `docs/signature-moments.md` |
| 6 | **Real geography before decoration** | The licence register, the hash check, and the rule above. `fetch.py` will not open a socket for an unregistered source |
| 7 | **Quiet colour before saturated colour** | A saturation ceiling on every colour the cartography paints, asserted from `assets/css/europedoor.css` |
| 8 | **Typography is part of the map** | Seven levels: country, capital, city, destination, region, feature, sea. Two of them wait on a fetch and both are written |
| 9 | **The aperture is the EuropeDoor signature** | `signature.apertures` is a floor in the invariant register; the arch is cut by four renderers that `checks.py` asserts agree |
| 10 | **Every map should tell you something about the place** | The editorial test, and the only one of the ten a machine cannot hold. It is what the recognition instrument is for |

## Terrain: where it explains the place, and nowhere else

| map | terrain | treatment |
|---|---|---|
| country | no | geography, rivers, peaks, destinations |
| region | no | geography and physical features |
| destination | **where the ground earns it** | four hypsometric bands, subordinate to the place. 147 of 319 |
| journey | **where the ground earns it, under 1,500 km** | the same bands as a backdrop to the route. 6 of 17 |
| place | inherits its destination | it is the same picture of the same town |
| homepage hero | **yes, as a picture** | three of the four bands over the whole continent, at half the plate's strength — see below |
| Europe overview | no | clean atlas |
| `/map` | **no** | an instrument, and relief is an illustration layer |

**"Where the ground earns it" is a measurement, never a list.** The spread and
the crest of the ground within 40 km of the destination, taken from the same
model that draws the bands and stored with them. Chamonix reads 1,798 and
2,752; Paris reads 102 and 150 and gets nothing. A list of mountainous places
typed by somebody would be an authored measurement, which this atlas does not
do — and it would be the mechanism by which a topographic Paris eventually
ships.

**One palette, absolute.** There is no weaker variant for flatter places: a
second strength was built, measured at 0.043 of luminance on the only band
Bergen has, and removed. An absolute scale reduces itself — a flat place
reaches only the quiet end of it — and two strengths would make one colour
mean two heights. See `docs/terrain-prototype.md`.

**The hero is the third family, and it is a different treatment rather than
an exception.** The suitability measurement, the two thresholds and the
1,500 km frame cap are a rule about a picture of a PLACE: does this ground
explain this destination. The homepage's subject is the continent, and the
question it answers is "this is Europe, and it has mountains in it" — so it
draws the same absolute scale over the whole extent, three bands rather than
four (the 200 m band is nothing at all at continental scale), thinned to a
picture's tolerance. The colours are `HYPSOMETRIC`'s own and `checks.py`
reads all three off it; only the alpha over them is the hero's, because the
land under it is itself translucent.

**The hero also draws the ground beyond the atlas, and draws it in a
different material.** `beyond-lod0.json` is western Siberia, the Caspian,
Iran, Arabia and the Sahara: anonymous rings, no country, no relief, no
label, nothing to click, in solid graphite. Europe is not an island and a
drawing that ends at 52°E said it was; a drawing that continues in fainter
parchment says the ground carries on and is less interesting, which is not
the claim. Lit parchment against unlit ground is the claim: *this is where
the light stops*, which is what a door does. It was tried at a sixth of the
land tone first and read as a haze the eye kept trying to resolve.

**Terrain must support recognition and sense of place, never become the
subject of the map.** And: **no layer may be added merely because the source
dataset exists.** Every layer earns its weight by improving one of
recognition, orientation, sense of place, hierarchy or beauty. If it does
none of those, it is omitted.

The elevation model is a low-resolution derived relief for **destination and
journey illustrations only**. Not the country plates, not the overview, not
the whole atlas — that is how an editorial atlas drifts into a GIS
application. It is zoom 6 of the AWS Terrain Tiles, 1,730 m a cell, smoothed
with a 5 km kernel and traced into four band boundaries; there is no
hillshade, because a hillshade invents a light direction and paints structure
onto flat ground, and a band claims only height.

## What the standard forbids, specifically

- **No invented geography, at any scale.** No hillshade fitted to nothing, no
  river drawn from memory, no region boundary hulled around a set of towns.
  An invented hillshade would be the most convincing wrong thing in this
  repository, because a reader cannot tell a fitted one from a decorative one.
- **No ranking a place to decide whether it is drawn.** `rank`, `featured`,
  `boost` and `sponsored` are refused on every editorial record. Curation is
  by **legibility** — a plate draws what it can name — which is a property of
  the drawing rather than a judgement about the place.
- **No saturated colour.** The ceiling is measured, not asserted.
- **No treatment that cannot be seen to be working.** Three specificity
  collisions and one `<use>` shadow-tree failure have each rendered as the
  thing simply not being there while measuring correctly. Look at it.

## The order of the layers

    ocean · coastal water · land · terrain · hillshade · rivers ·
    coastline · country boundaries · region boundaries · cities ·
    destinations · feature labels · water labels · labels · route · selected

Decided in one place, walked by one composer, asserted against the shipped
HTML on every page that carries a plate.
