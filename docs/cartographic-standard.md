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
| 1 | **Terrain before polygon** | The fourteen-layer stack in `cartography.ORDER`, with terrain, hillshade, rivers and region boundaries declared, positioned and empty. A layer with no data emits nothing and raises the moment its file appears unwritten |
| 2 | **Geography before database** | A plate draws what it can name. Measured across the fifty country plates: **176 marks, 176 of them named.** Not one anonymous dot |
| 3 | **Context before density** | Three voices — the subject, its neighbours in warm parchment, the rest quieter with distance — banded by measured distance on the drawing, not by a list |
| 4 | **Hierarchy before completeness** | One placement routine, one order: capital, city, destination, region. The capital is placed first and cannot be dropped |
| 5 | **Editorial composition before uniform cards** | Four page grammars, each with its own answers to the nine questions in `docs/signature-moments.md` |
| 6 | **Real geography before decoration** | The licence register, the hash check, and the rule above. `fetch.py` will not open a socket for an unregistered source |
| 7 | **Quiet colour before saturated colour** | A saturation ceiling on every colour the cartography paints, asserted from `assets/css/europedoor.css` |
| 8 | **Typography is part of the map** | Seven levels: country, capital, city, destination, region, feature, sea. Two of them wait on a fetch and both are written |
| 9 | **The aperture is the EuropeDoor signature** | `signature.apertures` is a floor in the invariant register; the arch is cut by four renderers that `checks.py` asserts agree |
| 10 | **Every map should tell you something about the place** | The editorial test, and the only one of the ten a machine cannot hold. It is what the recognition instrument is for |

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
