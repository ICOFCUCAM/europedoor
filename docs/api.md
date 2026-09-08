# API

Four public, read-only, key-free JSON documents, built at deploy time and
served from the same origin as the site. They are the documents the product
itself runs on — not a reduced copy, which is the only way an API stays true.

The human-readable version is published at `/api-docs`.

| endpoint | holds | note |
|---|---|---|
| `/api/atlas.json` | every destination with interests, nights, cost band, season, coordinates, URL | the Journey Planner runs on this. **Advisory countries are absent** — a build-time exclusion, so no consumer can route into one by accident |
| `/api/search.json` | one flat row per findable thing: name, kind, URL, lowercased text blob | **Advisory countries ARE present.** A page nobody can search for is a page that does not exist |
| `/api/countries.json` | country facts plus the full region and destination tree, and each country's verification record | advisory countries present, with the advisory attached |
| `/api/journeys.json` | curated routes with every leg resolved to a real destination | estimates are planning arithmetic, not quotes |

The advisory asymmetry between the first two is deliberate: one is a list of
places to route through, the other is a description of the continent.

## Conventions

- **No version in the path.** There is no stability guarantee yet and
  pretending to one before anybody depends on it is worse than saying so.
  `/api-docs` says it plainly.
- **Licence travels in the document.** Each carries a `licence` object,
  because a JSON file gets copied and the page it was linked from does not
  travel with it.
- **Cached at the edge** for 600s (`vercel.json`); assets immutable for a
  year.
- **No key, no quota, no sign-up.** Nothing to authenticate against.

## The write API, and why none of it exists

`docs/technical-foundation.md` §3 specifies the authenticated surface:
`POST /api/plan`, `/api/me/saved`, `/api/me/itineraries`,
`/api/providers/claim`, `/api/fund/interest`.

Every one of them writes, every one needs somebody logged in, and
authentication needs a data controller. None is published as a stub that
returns nothing.

**The one rule to carry into that work:** `POST /api/plan` and the browser
planner must share one implementation of the scoring rules. If the server
ever disagrees with `/plan`, one of them is wrong and nobody will be able to
tell which.
