# Data licences

Every geographic dataset that enters this repository is documented here
**before** it is downloaded, and the download script refuses to fetch a source
that has no record in `sources.json`. "Free to download" is not "free of
obligations", and the difference is invisible until somebody asks.

## The register

`sources.json` is the machine-readable half: one entry per dataset, carrying
the URL, the SHA-256 of the bytes we actually hold, the version, and the
licence id. `scripts/map/fetch.py` writes the hash and the date; it does not
invent an entry, so a source with no `.md` file in this directory and no row
in `sources.json` cannot be fetched at all.

Each `.md` file here answers the same eight questions, in the same order:

    dataset
    source
    licence
    version / date
    permitted use
    attribution requirements
    redistribution requirements
    share-alike requirements
    modification requirements

## What is in production today

| dataset | licence | status |
|---|---|---|
| Natural Earth 1:110m admin 0 countries | public domain | **in production** |
| Natural Earth 1:50m admin 0 countries | public domain | **in production** |
| Eurostat / GISCO NUTS (via Nuts2json) | copyrighted, specific provisions | **NOT imported — awaiting owner acceptance**, see `eurostat-gisco-nuts.md` |
| OpenStreetMap | ODbL | **not used, deliberately** — see `openstreetmap-not-used.md` |

## The rule this directory exists to enforce

A dataset does not become ours by being processed. Simplifying a coastline,
reprojecting it, cutting it into per-country files and renaming the properties
produces a **derived work**, and every obligation on the source travels with
it. The only reason EuropeDoor can publish `data/geo/*.json` with no notice
attached is that Natural Earth is public domain and we checked. The moment a
dataset with conditions enters, the conditions attach to the published site,
not to the download.
