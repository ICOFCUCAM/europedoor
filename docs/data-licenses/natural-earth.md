# Natural Earth — admin 0 countries (1:110m and 1:50m)

**dataset**
`ne_110m_admin_0_countries` and `ne_50m_admin_0_countries`, the country
polygons and the coastlines that fall out of them. These are the only two
Natural Earth themes in this repository. Nothing else — no populated places,
no rivers, no roads — has been imported, because nothing else is used yet.

**source**
`https://raw.githubusercontent.com/nvkelso/natural-earth-vector` — the
official Natural Earth vector repository, maintained by Nathaniel Vaughn
Kelso, which republishes the naturalearthdata.com release as GeoJSON. We take
the GeoJSON rather than the shapefile because reading a shapefile needs a
dependency and this repository has none.

**licence**
**Public domain.** Verified first-hand from `LICENSE.md` in the source
repository on 2026-09-08, which begins:

> Everything here is public domain. […] All versions of Natural Earth raster +
> vector map data found on this website are in the public domain. You may use
> the maps in any manner, including modifying the content and design,
> electronic dissemination, and offset printing. The primary authors, Tom
> Patterson and Nathaniel Vaughn Kelso, and all other contributors renounce
> all financial claim to the maps and invites you to use them for personal,
> educational, and commercial purposes.

A copy of that file is held at `data/raw/natural-earth-LICENSE.md` so the terms
we relied on are the terms we can still read in five years, whatever the
upstream repository does.

**version / date**
Natural Earth v5.1.2, fetched 2026-09-08. The exact bytes are hashed in
`docs/data-licenses/sources.json`; `scripts/map/fetch.py --verify` fails if
what is on disk is not what was recorded.

**permitted use**
Any use, including commercial. Modification and redistribution explicitly
allowed.

**attribution requirements**
**None.** The licence says so in as many words: *"No permission is needed to
use Natural Earth. Crediting the authors is unnecessary."* We credit it anyway
on `/map` and in `/method`, because a reader is entitled to know where a
border came from and because an uncredited map invites the assumption that we
surveyed it ourselves. That is a house rule, not a licence term, and it can be
changed without asking anyone.

**redistribution requirements**
None. This is why `data/raw/*.geojson.gz` and the processed `data/geo/*.json`
can both sit in a public repository with no notice file travelling alongside
them.

**share-alike requirements**
**None.** This is the property that made Natural Earth the first choice rather
than OpenStreetMap. Our simplified, clipped, per-country derivatives are ours;
publishing them creates no obligation to publish anything else, and no
obligation on anyone who takes them from us.

**modification requirements**
None. We simplify (Douglas–Peucker), clip to a European bounding box, drop
rings below an area threshold, quantise coordinates to four decimal places and
re-key the properties against our own country slugs. All of that is permitted
without notice, and all of it is recorded in `docs/map-architecture.md` so the
result is never mistaken for a survey-grade boundary.

## The one caveat that is not a licence term

Natural Earth is a **cartographic** dataset, built to look right at a stated
scale. It is not a legal or authoritative source for where a border runs, and
the authors say so. Everywhere this data reaches a reader, the page says which
dataset drew it and at what scale. See `docs/boundary-policy.md`.
