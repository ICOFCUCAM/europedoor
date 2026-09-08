# EuropeDoor — working notes

A static site: 1,072 generated HTML files, no dependencies, no database. Every
page comes from `data/` via `tools/build.py`. Nothing in `site/` was written
by a human and nothing ever should be.

**The name is EuropeDoor, at europedoor.com — one word, title case. It does
not change, and the mark is NOT cleared.** Strategy
documents keep arriving with alternatives on them — Europe Atlas, Europia,
Via Europa. Take their architecture and drop their branding section. See
`docs/brand-lock.md`; `tools/checks.py` enforces it.

## Read these first, depending on the work

| doing | read |
|---|---|
| **anything at all — read this first, every session** | **`docs/instruction.md`** — the standing instruction. Part 1 is how work is done here (audit first, deviate with numbers, STOP on licensing, never invent data, prove every check can fail). Part 2 is the visual instruction: **European Future**, the two worlds, the palette, the 60/25/10/5 ratio and the measured contrast limits. `docs/palette.json` is the checkable form |
| **the transformation brief, and the three decisions waiting on the owner** | **`docs/EUROPEDOOR_2036_TRANSFORMATION.md`** — the 2036 audit, what to keep/replace/redesign, and a five-phase roadmap. Phases B and C are unblocked; A waits on a map-licensing decision |
| **starting a session — read this first** | **`docs/audit-2026-09.md`** — the repository audit: current stack, what exists, technical debt, and the one open architectural decision (Next.js/Postgres: not yet, and why). Then **`docs/roadmap.md`** |
| **anything substantial** | **`docs/product-specification.md`** — both specifications answered: the 36-section brief in Parts 1–3, the 99-section one in Part 4. Plus the Postgres schema, the API, the AI pipeline with actual prompts, the dashboards, the money and the risks |
| changing how pages are generated | **`docs/architecture.md`** — the four rules the build depends on |
| adding or editing a place | **`docs/data-model.md`** — every field, and what the validator rejects |
| the scores | **`docs/scoring-method.md`** — and note the formula is published at `/method`, so changing `score.py` changes a public page |
| anything involving money | **`docs/europe-fund.md`** and **`docs/legal-position.md`** — three gates, all currently shut |
| naming, branding, domains | **`docs/brand-lock.md`** — settled, enforced, and the trademark is contested: EUROPEDOOR is in use in the doors trade, so no ®, no ™, nothing announced |
| **colour, the mark, voice, the manifesto** | **`docs/brand.md`** — the Brand Bible as built, including the four logo directions that were rejected and why |
| photographs, or "why is there no picture here" | **`docs/images.md`** — the pipeline is built and enforced; the library is empty |
| **the Postgres/PostGIS model, the API, Next.js, auth, search, the AI pipeline** | **`docs/technical-foundation.md`** — a destination with a trigger, not a plan for Monday. Nothing in it should be built yet |
| what to build next | **`docs/roadmap.md`**, and **`docs/content-report.md`** for where the dataset is thin |
| **"did we actually implement section N?"** | **`docs/section-audit.md`** — generated, never hand-edited. 100 sections, 1,273 assertions against the real build, and CI fails if any of them stops being true |
| **the map, geographic data, tiles, or "why not Mapbox?"** | **`docs/map-architecture.md`** — the pipeline, the three levels of detail, and why this is SVG rather than MapLibre. Then **`docs/data-licenses/`**, which is the register, and **`docs/boundary-policy.md`** for disputed frontiers |
| **"is field X in the model?" — the Build Package schema** | **`docs/schema-mapping.md`** — every entity and field of Build Package v1 §2 against the running data: HAVE, BUILT, or REFUSED with the promise behind each refusal |
| **anything visual — layout, navigation, states, mobile** | **`docs/ux-specification.md`** — the 37-section design brief answered, including the seven things it asks for that this product will not do and why. **`docs/ux-audit.md`** is the generated evidence: 51 sections, 326 assertions |

## The rules that catch people out

**`site/` is deleted on every build.** Editing a generated page is work that
disappears on the next `build.py` with no warning and no failing check. If a
page needs to say something new, it says it in `tools/lib/pages.py` or in
`data/`.

**There is exactly one page shell.** `render.page()` is the only function
that emits `<html>`. Do not add a second, and do not add an inline `<style>`
to a page — `checks.py` fails on both, because a masthead that exists twice
diverges within a month.

**The generated site is committed, and CI fails if it is stale.** After any
change to `data/`, `tools/` or `assets/`, run `python3 tools/build.py` and
commit `site/` in the same commit. A stale `site/` means the checks validated
output nobody is going to serve.

**Advisory countries are stripped from the planner index at build time**, not
hidden in the UI. Ukraine, Russia and Belarus keep a page carrying the
warning and are absent from `/api/atlas.json`. Do not "fix" this by filtering
in JavaScript.

**One drawing, two renderers.** `render.plate_shapes()` is the geometry;
`plate()` emits SVG and `raster.plate_png()` emits the social card. Never add
a shape to one only — a card that stops matching its page is invisible from
here, because it is rendered inside somebody else's product. A check asserts
both still come from `plate_shapes`. Cards are cached in `assets/og/`,
content-addressed, and pruned: first build 24s, every build after that 2s.

**A motion is a query, not a list.** `data/motions.json` declares twelve
queries; the validator refuses a field naming destinations and refuses a
motion with no query terms, and every `/europe-in/*` page prints the query
that made it. A curated list wearing the clothes of a query looks identical
on the day it ships and is wrong within a season.

**Never explain the constraint back.** Discover Mode and the motion pages
both hoist a reason shared by every result into one line above the list, and
carry only what distinguishes each row. The first version repeated the filter
on every card; individually true, collectively boilerplate, and boilerplate is
what a reader learns to skip.

**The browser suite has a floor on its own count.** It once reported "all 4
browser checks passed" and exited 0, because a `const checked` inside `main()`
shadowed the module-level counter. Every assertion ran; almost none was
counted. A green run that has stopped counting is worse than a red one,
because nobody looks at it.

**Two scores, both published, neither for sale.** The Europe Experience
Score says what a place is *for*; **discoverability** says how far it is from
being the obvious choice. Both are computed from the dataset on every build
and both are published in full at `/method`. Discoverability is **not a crowd
measurement** — we hold no visitor numbers for anywhere, and the page says so.

**Structured data claims only what we hold.** JSON-LD is a machine-readable
claim republished by people who cannot check it, so `checks.py` refuses
`aggregateRating`, `offers`, `price` and `openingHours` anywhere in it, refuses
an empty property (present-but-empty says "we have this" and then does not),
and asserts every `BreadcrumbList` matches the breadcrumb a reader can see.
`application/ld+json` is exempt from the inline-script rule because Chromium
reports zero CSP violations for it — verified, not assumed.

**Security headers live in `render.HEADERS`, and `vercel.json` is checked
against it.** Vercel does NOT read `site/_headers` — that is Netlify and
Cloudflare Pages syntax — so for as long as the headers lived only there,
HSTS, nosniff, Permissions-Policy and frame-ancestors were absent from every
production response while the repository looked correct. A check now fails on
drift between the two.

**The Fund holds nothing, and the checks enforce it.** No form, no payment
link, no amount raised, no progress bar on any `/fund` page; no `amount`,
`raised`, `goal` or `target` in `data/fund.json`. This is the single easiest
thing for a well-meaning person to break.

**No image without a photographer, a source and a licence.** This replaced
"no photographs at all", which was the right rule until there was a pipeline
and the wrong one after. `data/images.json` is the register, the validator
refuses a row missing any of the three, and `checks.py` refuses a published
page referencing a file with no row. Zero photographs are licensed today;
`docs/images.md` says why and what it would take. Everything else is a
generated plate — a landscape from the hash of the slug, with the motif taken
from what the place actually is.

**The Content-Security-Policy is strict, and the pages are what make it
possible.** `default-src 'none'`, no `'unsafe-inline'` in any directive. That
holds only because there is no inline `<script>` anywhere (page data goes in
an inert `application/json` block — see `render.jsondata`) and no `style="..."`
attribute anywhere (utility classes instead; CSP hashes do **not** apply to
style attributes, so one of them would force `style-src` open on all 987
pages). `checks.py` fails on either. `frame-ancestors` lives in `site/_headers`
only, because a browser ignores it in a meta tag and logs that it did.

**Two fixed bars on a phone, one token.** `--thumbbar` is the height of the
bottom navigation, and the sticky destination action, the footer padding and
the destination-page footer padding all derive their offsets from it. The
first version hard-coded 44px in those offsets while the bar rendered at 63,
so the action sat on top of the navigation. Only measuring both boxes in
Chromium finds that.

**A verification record expires.** A check is good for `REVIEW_DAYS` and then
reads as *due for review* again. Confidence is derived from the source kind
and the age of the check — the validator refuses an authored `confidence`
field, because a field a person can type is a field somebody will type "high"
into.

**No `rank`, `boost`, `featured` or `sponsored` field on a place.**
Sponsorship attaches to a provider and affects directory surfaces only. That
wall is enforced in the schema, which is the only version of the promise
worth making.

**EuropeDoor does not pay for maps, and a check enforces it.** The land comes
from Natural Earth (public domain), fetched by `scripts/map/fetch.py`, hashed,
committed, and processed into `data/geo/` by `scripts/map/process.py`. There is
no provider, no key, no tile server and no request that leaves this origin to
draw a coastline. `checks.py` fails on a page or script that names a commercial
map host or a public tile server. Adding one is a decision for the owner, not
a convenience.

**No dataset enters without its licence written down first.** `fetch.py`
refuses to open a socket for a source with no row in
`docs/data-licenses/sources.json` and no `.md` file beside it, and it refuses
by name anything on the `blocked` list. Two things are on that list on purpose:
**Eurostat NUTS** (copyrighted, use conditional on accepting provisions nobody
here has read — so region *boundaries* are not drawn) and **OpenStreetMap**
(ODbL share-alike, kept out of the knowledge graph deliberately). "Free to
download" is not "free of obligations".

**`data/geo/` is generated and CI fails if it is stale**, exactly like `site/`.
After changing `scripts/map/` or `data/raw/`, run
`python3 scripts/map/process.py` and commit the result in the same commit.

**Regions are a grouping, not a boundary.** We hold which destinations belong
to a region; we do not hold region geometry. The map draws a region as its own
destinations with the name at the middle of them and says so on the page. A
convex hull round Bergen and Ålesund labelled "Vestland" would look like an
answer and be a guess — and Monaco and Vatican City get a ringed point rather
than an invented outline for the same reason.

**One projection, and it was wrong for a year.** `pages.MAPPROJ` is the only
projection; everything that draws Europe uses it, and the browser is handed its
six numbers rather than reimplementing it. The version this replaced claimed to
correct for latitude and then multiplied x by `cos(52°)/cos(52°)`, which is 1 —
Europe was 60% too wide and nobody noticed, because 313 dots on an empty
rectangle are the right shape by definition. Real geography is what made it
visible.

**Two worlds, one set of components.** `<body data-world>` selects which set
of semantic tokens the whole stylesheet resolves to: DISCOVER is limestone and
editorial, INTELLIGENCE is graphite and luminous. Five pages are INTELLIGENCE
(`/map`, `/plan`, `/my-europe`, `/search`, `/discover`) and so is every
embedded map figure, wherever it sits. **INTELLIGENCE is dark in both
colour-scheme preferences on purpose** — the world says where the reader is,
not how they like their screen; if it followed the preference the two worlds
would collapse into a theme toggle.

**There is no gold, and two checks keep it out.** Brass was the only gold in
the previous palette and European Future removes it — `checks.py` fails on a
`--brass`/`--gold` token, on a raw gold hex anywhere in the stylesheet, and the
browser suite fails on a gold the browser actually paints. Verified all three
ways. Atlantic green and terracotta were *retained* rather than deleted: green
for heritage and provenance, terracotta as the warm cultural accent on
stories, events and experiences.

**The palette is data, and the contrast is recomputed.** `docs/palette.json`
declares which colours may carry text on which surfaces; `checks.py` recomputes
every ratio from the hexes in the file and fails on a claim the arithmetic does
not support. It caught its own author twice. First: `cobalt-lift` cleared AA on
the graphite ground and failed on the card surface, which is lighter — **a dark
palette has two backgrounds and the lighter one binds.** Then the browser suite
failed seven pages when the accent was bound to the signature `#3157FF`: 4.93
on the ground, 4.36 on the card the kickers actually sit on. **The signature is
a colour that gets drawn, not read** — `--signature` for the mark and the score
bars, `--door` (cobalt-deep) for anything that is text.

**"AI" does not appear in the masthead, the navigation or any h1.** The
assistant is called EuropeDoor Guide. The customer sees EuropeDoor and then
experiences intelligence; they never see AI EUROPE TRAVEL PLATFORM. Enforced,
because every competitor has crossed that line and it is the easiest one to
cross by accident.

**Relationships are derived, never stored.** `/api/graph.json` carries 3,716
edges across nine types, every one computed at build time from a relation that
is validated somewhere else — the nesting, a journey leg, a story's `places`.
`data/relationships.json` is refused by name: a free-standing edge table cannot
be validated, and it fails as a quietly empty page rather than a stopped build.
The only `weight` in that graph is `km`, a real distance; `checks.py` refuses
`weight`, `score`, `relevance` and `confidence` in any edge.

**A relationship that drops to zero is what nobody notices.** `gathers` shipped
at zero for one build because the derivation read `theme["places"]` and a
theme's destinations are `stops`. The document now carries a count per
relationship and `checks.py` puts a floor under each.

**A derivation can be systematically biased, and only a check finds it.**
`city_type` derived from Natural Earth's populated places produced **one
village in 157**, because that dataset is by construction a list of populated
places — so the destinations it could not classify were disproportionately the
villages. All 319 are classified now: 157 derived, 162 authored from the
summary this atlas had already written about each. Authoring a *classification*
is legitimate where authoring a *measurement* is not.

**A measurement is never authored; an editorial record can never be bought.**
Two rules from the schema audit, both enforced twice. `iso3`, coordinates and
population live in `data/geo/facts.json`, derived by `scripts/map/process.py`
from committed public-domain data, each carrying the dataset that produced it —
the validator refuses them as authored keys. And `featured`, `rank`, `boost`,
`sponsored`, `rating`, `review_count`, `opening_hours`, `price_level`,
`website` and `phone` are refused on every editorial record, in the schema and
again at the file level in `checks.py`. Seventeen refusals, each one a promise.

**Natural Earth knows 157 of 319 destinations, and that is the product.** The
162 it does not know are Theth, Xınalıq, Madriu-Perafita-Claror. Where there is
no source the field is absent rather than estimated, and `content-report.py`
counts it. **A population may never feed a score** — it is the most tempting
proxy for crowding there is, discoverability is published as explicitly not a
crowd measurement, and a check greps `score.py` to keep it that way.

## Gates

Run all seven before claiming anything is done.

    python3 tools/build.py check       validate the data
    python3 tools/build.py           1,072 pages
    python3 tools/checks.py            28 checks, ~99,900 things examined
    node tools/browser-checks.js       540 checks in Chromium, incl. accessibility
    python3 tools/section-audit.py --check   the 99 spec sections, 1,273 assertions
    python3 tools/ux-audit.py --check        the 37 UI/UX + brand + 2036 sections, 326 assertions
    python3 tools/content-report.py --write  what is missing, against the spec's targets

The browser checks need `npm install playwright` and take a couple of
minutes. They earn their place repeatedly: a 47-pixel mobile overflow on
every city page, two colour tokens below the WCAG contrast line, a places
layer that could never be turned on because `.hidden` is not a property of an
SVG element, and a €700 fortnight routed through Switzerland. They also
caught the planner producing a 2,500 km final leg to reach a named end city
and calling it an itinerary. None of those was findable by reading the code.
They launch the sandbox's own Chromium via `executablePath` because the npm
package version will not match the installed browser build.

The map pipeline is **not** part of the build — the build must run on a host
with no internet and produce identical pages, so the raw data and the processed
geometry are both committed. Run these when a dataset version changes:

    python3 scripts/map/fetch.py --verify    the bytes on disk are the bytes checked
    python3 scripts/map/process.py --check   data/geo/ matches the pipeline

Both are also asserted by `checks.py`, so a stale `data/geo/` fails CI.

**Three of the gates write files.** `section-audit.py --write`, `ux-audit.py --write`
and `content-report.py --write` regenerate documents that CI then checks for
staleness, exactly like `site/`. Run them and commit the result.

## Adding a country

1. Write `data/countries/<slug>.json` against `docs/data-model.md`.
2. Add the slug to exactly one macro region in `data/taxonomy.json`.
3. `python3 tools/build.py check` — the validator lists every problem at
   once, so one run fixes one round of mistakes.
4. Build, run both check suites, commit `site/` with the data.

Depth beats breadth. 244 cities written properly beats 40,000 imported, and
there is no importer in this repository on purpose.

## Style

Long comments that explain *why*, usually naming the failure that prompted
the change. Keep them. Prefer recording a mistake to quietly deleting the
evidence of it — the note in `assets/css/europedoor.css` about the 47px
overflow is worth more than the two lines of CSS that fixed it.
