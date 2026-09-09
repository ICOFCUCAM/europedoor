# The OSM side goes here — after the licence question, not before

`measure.py` picks up any `*.geojson` or `*.geojson.gz` in this directory
holding Polygon or MultiPolygon features, cut to the bbox in `../README.md` §2,
in WGS84 lon/lat. Nothing else is needed and nothing here is read by the build.

**This directory is empty on purpose.** OpenStreetMap is on `fetch.py`'s
`blocked` list and `docs/data-licenses/openstreetmap-not-used.md` records why:
ODbL 1.0 is share-alike, and the condition under which OSM may return has not
been met. Putting a file here before that decision is made is the thing the
block exists to prevent — see `../README.md` §4 for the six steps, in order.

Whatever lands here is ODbL-licensed data in a working directory. It is not
the site's geometry, it must not be copied into `data/`, and the separation
condition in the licence note applies to it from the moment it arrives.
