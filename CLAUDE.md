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
| **the mandate: what a first-class gateway to Europe would be, and where this one is not** | **`docs/first-class-audit.md`** — 27 surfaces rendered at 1280 and 390 and then measured. Three findings: on a phone 12 of 23 surfaces are effectively type to the fold, seven of them with no picture on the first screen at all (CORRECTED — the first version said 21 of 22 and was reading where the first figure STARTS rather than how much of the screen it fills); the site has one composition rendered 1,033 times; the homepage decays monotonically after the hero. The eight benchmark sites are BLOCKED by the egress proxy and the benchmark half is labelled second-hand |
| **the design language — what makes a page EuropeDoor with the logo removed, and which movements each family takes** | **`docs/design-language.md`** — the ARCHITECT step. Five marks that could not have been made by anybody else, the six-movement composition grammar per family, the three head roles, what the language forbids, and how a change is proved |
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
| **which family gets a photograph, and what it must do there** | **`docs/image-philosophy.md`** — twelve families, twelve visual languages. One row is measured (the homepage); six are claims and none may be bought until measured; three families get none ever |
| photographs, or "why is there no picture here" | **`docs/images.md`** — the pipeline is built and enforced; the library is empty |
| **the Postgres/PostGIS model, the API, Next.js, auth, search, the AI pipeline** | **`docs/technical-foundation.md`** — a destination with a trigger, not a plan for Monday. Nothing in it should be built yet |
| what to build next | **`docs/roadmap.md`**, and **`docs/content-report.md`** for where the dataset is thin |
| **"did we actually implement section N?"** | **`docs/section-audit.md`** — generated, never hand-edited. Every spec section asserted against the real build, and CI fails if any of them stops being true |
| **coastline detail on a local frame, and the rivers fault it found** | **`docs/coastline-lod.md`** — A/B/C measured on five destinations. Under 1,000 km a plate draws local geometry, clipped; above it, the continental file. And the same 111 rivers were on all 824 destination plates |
| **terrain — where relief is drawn and what decides it** | **`docs/terrain-prototype.md`** — Chamonix at four strengths judged by eye, then eight destinations judged together. One absolute palette, zoom 6 because that is where the licence is, and a measurement rather than a list deciding which 147 destinations get it |
| **the cartographic standard — the ten principles and what holds each** | **`docs/cartographic-standard.md`** — editorial European atlas, not GIS. Nine of the ten are held by a check or an invariant; the tenth is the editorial test |
| **how a map is DRAWN — palette, layers, what the benchmark still needs** | **`docs/cartography.md`** — the pictures are paper and the instruments are graphite. The four layers, the measured palette, and the four things the benchmark has that are blocked on a licence or a socket |
| **the map, geographic data, tiles, or "why not Mapbox?"** | **`docs/map-architecture.md`** — the pipeline, the three levels of detail, and why this is SVG rather than MapLibre. Then **`docs/data-licenses/`**, which is the register, and **`docs/boundary-policy.md`** for disputed frontiers |
| **the frontend — routes, the shell, primitives, what §4 must not do** | **`docs/frontend-architecture.md`** — §4, measured. 1,067 documents and five applications; eleven primitives cover 100% of the site |
| **the API — endpoints, contracts, empty states, what not to build** | **`docs/api-architecture.md`** — §3, written from the running system. Five static documents, no server, and the trigger that would change each of the nine things deliberately unbuilt |
| **"is field X in the model?" — the Build Package schema** | **`docs/schema-mapping.md`** — every entity and field of Build Package v1 §2 against the running data: HAVE, BUILT, or REFUSED with the promise behind each refusal |
| **changing anything visual — the protocol and the control** | **`docs/design-migration.md`** — §6. The pipeline, the invariant register as its control, and the three measured defects in the generated plates that are the next experiment's subject |
| **the visual system — tokens, type, the two worlds, what is left** | **`docs/visual-architecture.md`** — §5, measured. The European Future migration as it actually landed, plus the fifteen deliberate attacks that went red |
| **what each family's page is FOR — the nine questions, and where the door is deliberately absent** | **`docs/signature-moments.md`** — emotional promise, signature moment, geographic expression, hierarchy, interaction, aperture, imagery, data, and what is refused. Read before adding a map to a family |
| **"what is left, and who is blocking it"** | **`docs/gap-assessment.md`** — written from the site's own instruments. The engineering is finished, the content is a third written, and almost every remaining gap is a photograph nobody has licensed or a page nobody has written |
| **anything visual — layout, navigation, states, mobile** | **`docs/ux-specification.md`** — the 37-section design brief answered, including the seven things it asks for that this product will not do and why. **`docs/ux-audit.md`** is the generated evidence |

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

**A reference plate is art direction, never geographic truth.** The
cartographic benchmark this atlas is being drawn against is an AI-generated
image: its coastline, its rivers, its region boundaries and its relief are a
model's idea of Portugal rather than Portugal. Take its palette, its water
ramp, its type hierarchy, its key, its locator and its restraint; take
nothing about where anything is. All geometry comes from `data/geo/`, fetched
by `scripts/map/fetch.py`, hashed and registered in `docs/data-licenses/`.
Nothing is traced, eyeballed or transcribed. See `docs/cartography.md`.

**EuropeDoor does not pay for maps, and a check enforces it.** The land comes
from Natural Earth (public domain), fetched by `scripts/map/fetch.py`, hashed,
committed, and processed into `data/geo/` by `scripts/map/process.py`. There is
no provider, no key, no tile server and no request that leaves this origin to
draw a coastline. `checks.py` fails on a page or script that names a commercial
map host or a public tile server. Adding one is a decision for the owner, not
a convenience.

**No dataset enters without its licence written down first, and the block is
on the DATA rather than the label.** `fetch.py` refuses to open a socket for a
source with no row in `docs/data-licenses/sources.json` and no `.md` file
beside it. For a while it also refused the `blocked` list **by id typed on the
command line only** — the loop over `sources` never consulted that list — so a
row added as `osm-land-polygons` pointing at openstreetmap.org would have been
downloaded without the refusal printing a word. A guard on a label is a guard
whoever adds the dataset gets to choose. Each blocked entry now declares
`refuse_matching` patterns tested against a candidate's id, URL *and* dataset
name, `fetch.py` refuses on a match, and `checks.py` asserts the same thing on
every commit — because `fetch.py` runs when a person types it and CI runs
always. Two things are on that list on purpose:
**Eurostat NUTS** (copyrighted, use conditional on accepting provisions nobody
here has read — so region *boundaries* are not drawn) and **OpenStreetMap**
(ODbL share-alike, kept out of the knowledge graph deliberately). "Free to
download" is not "free of obligations".

**A page that draws land names where the land came from.** Two in five of the
pages that draw one had no credit at all, and most of the 499 that had one had it *by
accident*: a destination page named Natural Earth because `pop_line` prints
the dataset behind its population, so the 45 destinations with no population
figure named nothing and every place page named nothing. Coverage that depends
on a different field being present is worse than none, because it looks like a
policy. Natural Earth requires no attribution — the licence says so — so today
this is `geo.sources_line()`'s stated reason: a reader looking at a border is
entitled to know which dataset drew it. It stops being taste the moment any
row in the register carries `attribution_required`, and the check hardens
itself and says so when one does.

**A label is a label, and the physical names inherited none of the rules
written for the place names.** `.peakname`, `.fname` and `.sname` were added
after the two passes that fix exactly this, and took neither: they were sized
in a fixed px inside a scaled viewBox, so Monte Rosa's height rendered **5.1
pixels tall** at 390, and `phone_declutter()` matched `class="minilabel` and
nothing else, so a physical label went through the pass, was measured, lost,
and was drawn anyway. Chamonix printed *"Monte Rosa 4,634 m"* through its own
name on a phone, one commit after the peak was added. Found by rendering the
page at 390 while shooting something else; no count could see it, because the
label was placed, was inside the aperture, and did not collide at the width
every check ran at. All three families take the `--z` compensation now, all
four count toward `dense_class()`, and `phone_declutter()` marks the first
`class="` on whatever it is given.

**The most-seen map on the site never had a collision pass at production
size.** The country map and the macro map both run a greedy declutter; the
destination plate ran only the PHONE pass, which decides what fits at the
enlarged phone size and marks the losers `wide-only` — and `wide-only` is
`display: none` below 44rem and **drawn above it**. So every label the phone
pass rejected came back on a desktop and nothing resolved it. Measured across
all 319 destination plates at 1280: **160 of them carried an overlapping pair**,
271 pairs in all, the worst *"Levoča & the Spiš"* through *"Poprad & the High
Tatras"* by 135 pixels.

Three more families were wrong underneath it. **The route, region and motion
maps tested a DISTANCE between dots rather than an overlap of boxes** — the
mistake this file already records one family over — so they let "Omodos & the
wine villages" run 156 px through "Kardamyli & the Mani" while dropping names
that were merely near; the box test both fixed the overlaps and gave those
pages more names (motion 239 → 380). **The country portrait composed its own
country name at the END and never measured it**, so it landed at the middle of
the country on top of whatever was there, on 27 country plates of fifty, the
worst "ARMENIA" through "THE NORTH & SOUTH" by 125 px. And **the phone pass tested bare overlap
with no clearance**, so two names could be placed touching — four plates at 390
met by up to two pixels.

**The test belongs where a label is PLACED, not in a pass afterwards.**
`place_label_box()` takes a `clears` predicate now, so a name that collides
where it wants to go tries its other three positions before it is dropped. A
pass that filters a chosen position can only ever delete, which is why the
country map gained 54 names by having its test moved inside.

**Placing the country name first was the obvious reading and it broke a rule
the plate already had.** Every mark on a country plate carries a name, and the
capital's mark is drawn unconditionally — so reserving a large box across the
middle of Albania ate Tirana's label and left a star nothing named. The country
name is the one label with real freedom, so it goes after the names pinned to a
dot, and is offered nine anchors inside its own country rather than one. **And
a name too wide for its own country breaks at its last space**: BOSNIA AND
HERZEGOVINA measures 392 units against a plate 391 wide and UNITED KINGDOM 253
against 242, so both had been drawn straight off the edge of their frame and
sliced by the aperture for the life of the plate.

**The model cannot check itself.** All of this works from `LABEL_METRICS`, a
fitted upper envelope on the width of a name, so a static check re-running that
model would only ever agree with it. The browser's own
`getBoundingClientRect` is the instrument, at 1280 and at 390, and the numbers
are 271 overlapping pairs to zero.

**A PLATE HAS TWO COORDINATE SPACES AND `plate()` CONFLATED THEM, so the same
111 rivers were drawn on all 824 destination and journey plates.** `w`/`h` are
the viewBox; `view` is the window in the projection's own coordinates. On a
country plate they are the same thing — the projection is fitted to the frame —
and on a destination plate they are not: the continent is drawn at 1000×780 and
the plate scales a small window of it up inside a translate-and-scale. Every
caller passed `view=(0, 0, w, h)`, so the layers the renderer draws itself asked
which rivers are in the rectangle (0,0)–(900,320) of Europe — the North Sea and
Finland — and drew the answer at continent coordinates over a picture of the
Alps. **The Kama, the Dalälven and the Neva were on Chamonix, on Bergen and on
Athens, identically.** It survived because it looks right: blue lines and lakes
read as rivers wherever they are, and the country plates were correct all along
because they pass a real projection and no transform. `plate()` now takes
`view` and `transform` separately and applies the transform to everything it
renders itself — a caller cannot get half of it right, because a caller no
longer does any of it. Underneath it: a river was emitted **whole** if one point
of it fell in the window, and the clip pad was a flat 40 units, written for a
900-unit frame and left on a 90-unit one.

**The coastline was nine pixels coarse on a local frame, and it left seams of
sea colour on inland ones.** lod1 simplifies at 0.04° — 4.4 km — so Attica was
a wedge and the Cyclades were lozenges; and two neighbours simplified
independently do not share an edge, so **Kraków, which has no coast at all,**
had thin slivers of ocean running along the Polish frontier. Under
`geo.LOCAL_LOD_MAX_KM` (1,000 km) a destination plate draws from the lod2 file
already in the repository, merged over the continental one and clipped to the
window. Measured three ways: unclipped lod2 is the same picture for eight times
the bytes, so the clip is not an optimisation of the idea, it is the idea. 277
of 319 destinations are under the cap; `/map`, the country plates, the macro
regions and the journeys keep the level they had.

**Terrain is drawn where the GROUND says so, and the rule is a measurement.**
147 of 319 destinations and 6 of 17 journeys carry four hypsometric bands from
a public-domain elevation model; the rest carry none. What decides is the
spread and the crest of the ground within 40 km of the place, derived by
`scripts/map/relief.py` and stored beside the bands in
`data/geo/terrain-lod1.json` — Chamonix reads 1,798 m and 2,752 m, Paris reads
102 and 150. **A list of mountainous places would be an authored measurement**,
and it is the mechanism by which a topographic Paris eventually ships.

**Its first version measured sea.** Clamping water to zero and including it in
the percentile made a coastal circle four-fifths sea, so Athens — in a basin
ringed by three mountains — measured *lower* at 40 km than at 25. Land cells
only. That is the `city_type` failure again: a derivation can be
systematically biased against exactly the cases it exists for.

**One palette, absolute, and a second strength was measured out.** A fainter
variant for flatter places rendered 0.043 of luminance from the land tone on
the only band Bergen has — a layer that ships 23 KB and cannot be seen — and
made `#d8ceb4` mean 600 m on one page and something else on another. An
absolute scale reduces itself: Bergen's ground crosses one band boundary and
gets one step, Chamonix's crosses four.

**Relief is capped by frame width, not only by place.** The
Arctic-to-Mediterranean journey frames 4,207 km and drew 787 KB of bands with
the Alps a smudge the width of a thumb. `TERRAIN_MAX_KM` is 1,500 km, taken
from the seventeen journey frames rather than picked: it admits the six that
are regional and excludes the eleven that cross the continent.

**A boundary is a stroke on the land path, so relief buries it.**
`country-bounds` was folded into `land` with a note saying separating it was
what "terrain will force" — it did. The stroke-only pass is emitted only on
plates that draw relief, and writing it without `vector-effect:
non-scaling-stroke` reproduced the *frontier is a worm* failure one screen
from the rule that documents it. **A rule that exists is not a rule that is
inherited.**

**The coastline was nine pixels coarse on every coastal destination, and an
Alpine benchmark is what found it.** lod1 simplifies at 0.04° — 4.4 km, nine
pixels on a 590 km plate — so Attica was a wedge, the Cyclades were lozenges
and the Norwegian coast was a staircase, on every coastal page since these
maps were built. Nobody had put a coastal frame and an Alpine frame side by
side. `geo.local()` merges the lod2 already in the repository over the
continental file for frames under about 980 km: no new data, and Athens is
Attica again.

**The terrain file is checked by fingerprint, not by rebuilding it.**
Everything else in `data/geo/` is verified by re-running the pipeline in
memory and diffing, which costs a second. This one costs a minute — 182 PNGs
and twelve million cells in pure Python — and `checks.py` runs every few
minutes. So the guard moved to the inputs: every source byte, every parameter,
and `relief.py`'s own source hash. That is not the weaker contract it looks
like — it also fails on a refactor that produces identical rings, which is
correct.

**`data/geo/` is generated and CI fails if it is stale**, exactly like `site/`.
After changing `scripts/map/` or `data/raw/`, run
`python3 scripts/map/process.py` and commit the result in the same commit.

**Regions are a grouping, not a boundary.** We hold which destinations belong
to a region; we do not hold region geometry. The map draws a region as its own
destinations with the name at the middle of them and says so on the page. A
convex hull round Bergen and Ålesund labelled "Vestland" would look like an
answer and be a guess — and Monaco and Vatican City get a ringed point rather
than an invented outline for the same reason.

**One projection, and it has been wrong twice.** `pages.MAPPROJ` is the only
projection and everything that draws Europe uses it. It is now a **Lambert
conformal conic at EPSG:3034's angles** — standard parallels 35°N and 65°N,
origin 52°N, central meridian 10°E — which is the conformal conic the EU
publishes pan-European maps on, chosen for this exact extent.

The first version multiplied x by `cos(52°)/cos(52°)`, which is 1: Europe was
60% too wide for a year and nobody noticed, because 313 dots on an empty
rectangle are the right shape by definition. Real geography made that visible.
The second was equirectangular with one cos(latitude) correction at the middle
of the extent — exact on one line and wrong everywhere else. Measured as the
ratio of scale along the parallel to scale along the meridian, which is 1.000
everywhere on a conformal projection: **−25.3% at 35°N, +22.4% at 60°N, +44.9%
at 65°N, +89.7% at North Cape**, on every page that draws land
(`signature.apertures` counts them). A coastline stretched 45% still
looks like a coastline, so this one needed arithmetic rather than a contact
sheet. `checks.py` asserts conformality at 54 points and pins the four angles,
because moving a standard parallel keeps a projection conformal and quietly
redraws Europe.

A conic is not affine, so the browser can no longer be handed six numbers. It
is handed the four **angles** and derives the cone constant with the same three
lines `geo.py` uses — one projection, decided in one place — and a browser
check asserts the two implementations agree to a hundredth of a pixel on nine
points. **Rings are clipped in lon/lat before projecting**: `data/geo/` is cut
at 52°E and the extent stops at 45, and under a conic those seven degrees
rotate about the cone apex and land back inside the canvas instead of falling
off the right-hand edge.

**The aperture is the signature, and it is cut three ways.** Geography on
EuropeDoor is seen through a doorway: an elliptical arch, rx = span/2, ry =
34% of the height, on every embedded map, every generated plate and every
social card. `render.arch_path()` cuts the SVG, `raster.Canvas.arch_mask()`
cuts the pixels, and `.plate { border-radius: 50% 50% 0 0 / 34% 34% 0 0 }`
cuts the box — three renderers because a plate's viewBox is 16/9 and its
containers are 16/9, 3/4 and 21/9, so an aperture cut inside the drawing is
cropped away by `preserveAspectRatio="slice"`. The head is elliptical rather
than a circular segment for exactly one reason: CSS cannot state a circular
segment. `checks.py` asserts all four values agree, and `signature.apertures`
is a floor. **A map figure must paint no background** — the corners outside
the arch show the page through, and that is the difference between an
aperture and a panel. Light wall, dark opening.

**The signature was deleting the content it exists to frame, and the
instrument was measuring the wrong boundary.** Map labels were placed with
the cartographer's rule — put the name on the other side of the dot if it
runs off the right-hand edge — tested against the RECTANGLE. The drawing is
clipped by the ARCH, so the top corners are gone. Measured across every page that
draws a labelled map: 5,184 labels, **184 of them, on 142 of those
pages, had a corner outside the aperture and FOURTEEN were drawn entirely
inside the removed corner** — "Dürnstein & the Wachau" did not exist on the Hallstatt map, and
nothing anywhere said a place was missing. A rectangle check reported those
same pages as at most 0.7% over.

**Four families each chose their own label position, and three of them
offered only one.** `place_label_box()` is now the single rule: right of the
dot, then left, then under, then over, each tested against the real curve;
a name that fits nowhere is dropped exactly as a colliding one is, keeping
its dot, its `<title>` and its row below. 184 → 0, 14 invisible → 0, and no
map lost all its names.

**A label's width is not proportional to its length.** The old `6.1 *
chars` understated 244 of 311 rendered names, because a name has a fixed
cost no per-character figure carries — "Rome" measures 8.79 units per
character and "Amboise & the Loire châteaux" measures 5.9. Fitted as the
upper envelope over every label the site renders: `24.4 + 6.05 * chars` for
a destination, `18.8 + 8.89` for a region name at 15px bold. One model per
type size, and the browser's own `getBBox` is the only honest instrument —
a static check re-running the same model would only ever agree with itself.

**The aperture may be explicit, subtle, implied or absent — recognition, not
repetition.** A signature applied to everything is wallpaper. `docs/signature-moments.md`
answers nine questions per family — emotional promise, signature moment,
geographic expression, hierarchy, interaction, the role of the aperture, of
imagery, of data, and what is deliberately absent — and records where the
door is *correctly* missing: **/map** is the instrument rather than a picture
of somewhere, the **facet** pages exist to be left quickly and must not each
repeat their parent's map, and the **interest** pages would draw three
identical maps of Europe for their three largest tags. Before adding an
aperture to a family, answer question 2 for it.

**A great-circle distance is a floor on a journey, and for a year it was
printed as the journey.** Every distance here is haversine between two
coordinates; there is no road and no rail geometry in this repository. The
journey pages printed "69 km — a local train or a short drive" for Chamonix
to Zermatt, which is 69 km as the crow flies, about 170 on the ground, and
two changes round a mountain range. The thresholds were not wrong — Vienna to
Bratislava really is a short train — they were being asked a question the
input cannot answer, and the answer was the one number in this product a
reader could act on and be wrong about.

The first correction was worse: the planner said **"at least"**, and
`travelHours()` knows one average speed and nothing about whether a
high-speed line exists, so its error is not signed. Measured against six real
legs it undershoots short mountain hops and overshoots every fast corridor —
Paris to Marseille reads 8h36m against a real four and a half. An estimate is
not a bound and must not be dressed as one. The time now says "about", the
distance says "in a straight line", and the sentence saying the estimate is
out in **both** directions is hoisted once above the legs.

**Removing a claim leaves surfaces pointing at it.** Three did, and only
rendering the pages found them: the journey map caption promised "what each
one means on the ground is in the note under the leg", `/map`'s journey note
promised the same, and the facts list had a **"Ground covered"** row that was
neither ground nor covered. `checks.py` now asserts the promise on the
shipped HTML — a page printing a hop says "straight line", and no page
anywhere claims a mode or a ground distance. A source-level check would have
passed on all three.

**A story shipped a hash-drawn landscape to every platform that renders its
link.** The rule was enforced twice — the page rebuilt on `storymap()`, the
index's nine illustrations removed — and `og=` went on passing `motif=None`,
which is precisely the instruction to pick the picture from the hash of the
slug, on the one surface nobody here ever looks at. **The alternative to a
hash-drawn landscape is not a better hash**: a plate is an illustration, the
register holds no photographs, and rasterising a storymap needs a second
renderer for map geometry that does not exist. So a shared story link carries
its title and standfirst and no image. Nine cards pruned. `checks.py` refuses
`og=(seed, None, …)` anywhere — the shipped HTML cannot tell a hash-chosen
card from a named one, both are a URL to a PNG, so this one is asserted at
the source.

**Styling that cannot apply is dead code that looks like a decision, and a
check now deletes every rule in turn to find it.** Twice in three commits a
rule lost a specificity fight and the result rendered as *the thing is simply
not there* — the touch targets painted because `.minidot .hit` (0,2,0) lost
to `.minimap.arched .minidot circle` (0,3,1); the macro members were not
filled because two (0,3,1) selectors met and the later one won. Neither is
visible in any count. The scan removes each declaration and sees whether
anything on the page moves; a rule that matches elements and changes none of
them cannot apply.

**Every minimap is arched — 824 of 824 — so the un-arched base fills could
never apply.** They were written when a map was a light panel on a light page
and kept when it became a dark opening; `.minidot circle { fill }`,
`.minilabel { fill }` and `.countrymap .rlabel text { fill, stroke }` have
been superseded on every page since. Deleted, keeping the geometry those
selectors really decide. **And a media rule that does not currently apply is
asleep, not dead** — the first scan flattened every `@media` block and
reported the dark-preference reveal as a rule that never wins, which is true
in the light preference it runs in and exactly the wrong conclusion. 27 dead
rules to 18, and what survives is mostly **redundant** rather than
unreachable: a `color` restating what the element already inherits.

**Its first run found that a country is not highlighted on its own map** —
`.countrymap .countries path.here` never won anywhere, so Austria was drawn
on Austria's page in exactly the same grey as Germany, on all fifty. The
scan is a **ceiling, not zero**: several base rules are legitimately
superseded by an `.arched` variant on every page that has one, and the
honest fix for those is a refactor. Raising the number is allowed; raising
it without reading the list is not.

**The scanner's own first version examined nothing and reported clean.** A
`CSSStyleRule` carries an *empty* `cssRules` list for CSS nesting, and an
empty list is truthy — so the walker recursed into nothing for every rule and
collected none of the 630. The check asserts its own reach for that reason.

**The macro regions were the last geographic family with no geography** — a
headline and a grid of nine cards, telling a reader which countries are in
the Nordics without ever showing where it is. **A macro region is the one
grouping here with real polygons behind it**: a region is a set of
destinations and is refused a boundary, but the Nordics *is* five whole
countries and Natural Earth has all five. Nothing is invented — the members
are filled, everything else is context, the frame is the members' own extent.

**And the fill lost a specificity fight, so the map of the Nordics had the
Nordics indistinguishable from the rest of Europe while the caption said
"filled".** `.macromap .countries path.here` and `.minimap.arched .countries
path` are both (0,3,1) and the second is further down the file.
**That is the second such collision in three commits that rendered as "the
thing simply is not there"** — the touch targets painted because they lost
one, these vanished because they lost one — and neither is visible in any
count.

**Enlarging the type broke the rule that placed it.** Labels are positioned
at build time against boxes measured at 11 units; the phone rule draws a
sparse map's names at 26 so they resolve into glyphs at all. Nothing re-ran
the collision pass at the new size — **434 overlapping pairs, on a third of
every page that draws a labelled map**, "Hallstatt" through "Berchtesgaden" by
49px, "Andorra la Vella" through "Madriu-Perafita-Claror" by 91. Found by
*looking*, on a contact sheet at phone width, one commit after every
measurement of label **size** came back green. **Size and arrangement are
different questions and only one of them was being tested.**
`phone_declutter()` re-tests every box at the phone's scale and marks the
losers `wide-only`: 30% of labels are not drawn on a narrow screen, and each
keeps its dot, its `<title>` and its row below. `tools/contact-sheet.js`
takes `--phone` as well as `--dark`.

**The signature existed in one colour-scheme preference.** *Light wall, dark
opening* is the whole reading of the aperture — the corners outside the arch
show the page through, which is why a map figure paints no background.
Measured as the contrast between the page those corners reveal and the ground
inside the opening, on every arched map:

| preference | wall : opening |
|---|---|
| light | 17.94:1 |
| dark | 1.03:1 |

In the dark preference the wall is graphite and so is the opening: no step,
no door, on every page that draws one. **It cannot be fixed by darkening the
opening** — two near-blacks are always about 1:1, and pure black against the
graphite ground measures 1.11. So the door is read the other way a real one
is: by its **cut edge**, the reveal, drawn from the same `arch_path()` the
clip uses and stated in both preferences, because a signature that changes
shape with a system setting is two signatures. 1.03:1 to 2.18:1 in dark.

**The contact sheet takes `--dark`, and only ever looking in light is how
this survived.** The browser check now asserts the opening is readable
*either way* — by the step from the wall, or by the reveal — in both
preferences.

**The stories index was nine three-column grids each holding one card.**
Built from the desk taxonomy rather than from what a reader is doing: nine
desks, one story each, so nine `<h2>` bands and a 280px card alone in a
1,168px row with 888 pixels of white beside it, nine times, over 5,792 pixels
of page. *Design to purpose, not to data shape* — and the shape of the data
was the entire layout. Nine essays are a contents page: one list, newest
first, the desk as a kicker on the piece it belongs to, which is what a desk
always was.

**And all nine drew an illustration chosen by the hash of their own slug** —
the exact thing *a story is not a place, and its picture may not be drawn
from a hash* was written for, one page over from where it was enforced.
Nothing checked the index. The fix is no picture at all: the alternative to a
hash-drawn landscape is not a better hash. A check now reads every page for a
story card carrying a plate, because the next place this happens is a
related-reading rail that does not exist yet. **A section assertion required
an `<h2>` per desk and the index obliged** — it was reading "grouped by desk"
as "banded by desk" and enforcing the data's shape as the layout.

**An invisible thing painted, and every counting check was green.** The
touch targets behind each map dot are transparent circles. `.minidot .hit` is
specificity (0,2,0) and `.minimap.arched .minidot circle` is (0,3,1), so all
of them painted at 55% limestone: **three grey blobs the size of a region on
every country map**, and lime saucers over the month and quiet maps. Every
gate was green — the static suite, the browser suite, both audits and the
whole invariant register. Not one of them counts things a reader can see. A
contact sheet of twelve families found it in one look. Fixing it
then broke a contrast check, which had been reading the first `.minidot
circle` — now the invisible one — and reporting 1.00:1.

**A dot on a map is a link, and it was 3.9 pixels wide.** WCAG 2.2 AA puts
the floor at 24. The suite measured the thumb bar's five items and nothing
else, so 130 links on `/beyond-the-obvious`, 12 on a destination page and 345
country shapes on `/map` were never looked at. Enlarging the drawn dot would
destroy the map, so each link carries a transparent circle sized at build
time to **half the distance to its nearest neighbour** — the largest target
that can never steal an adjacent tap.

**Where it still cannot reach 24, SC 2.5.8 asks for the same function
elsewhere on the page, and three families did not have it.** Six of
Innsbruck's twelve dots led to places appearing nowhere else in the document
— not in the rows, not in the prose, not in the structured data. A dot the
page cannot name is now **context**: it keeps its `<title>`, loses its link,
and stops pretending to be navigation. The marker for the page you are on
stopped linking to itself. And `/map`'s text alternative now names the fifty
countries as well as the 319 destinations, because twenty of them draw
between 3.6 and 12 pixels wide.

**Measuring it the strict way was itself wrong**, and said the journey pages
had six unreachable stops. They are links inside an `h3`, 22px tall because
that is the line — and SC 2.5.8's own Inline exception exempts them. The
equivalent is judged on existing, not on being 24px itself.

**Three assertions broke on this, each pinning a shape rather than a
promise.** §17 counted `<circle>` and six stops became twelve; rewritten to
`<title>` it read thirty-one, because the land under the route carries a
title per country; it now counts destination links inside the figure. The
map's text alternative was asserted by a bare count of its links, which grew
by fifty. And the country total was asserted against `.cshape` alone, reading
44 against 50 — six countries have no polygon at 1:50m and are drawn as a
ringed point.

**A map label is 11 units, not 11 pixels, and on a phone it rendered at
3.9.** `.minilabel` is sized in a 1000-unit viewBox and the browser scales
that viewBox to its container, so what a reader gets is `11 × (width/1000)`:

| viewport | 390 | 480 | 704 | 900 | 1024 | 1280 |
|---|---|---|---|---|---|---|
| label px | 3.9 | 4.9 | 7.4 | 9.4 | 10.7 | 12.8 |

Below about 860px that is not small type, it is type that does not resolve
into glyphs — every phone and most tablets, on eight hundred pages, for the
life of the embedded map. **Every existing check asked whether a label was
placed and whether it survived the aperture; none asked whether it was
legible.** There is no non-scaling-text in SVG and the fix depends on how
many names a map carries, which only the build knows, so `dense_class()`
marks each figure from the names it **emitted** — the three families each had
a different idea of what "labels" meant, and counting the markup is the only
one that is the same everywhere. Six or fewer are enlarged on a phone; more
are dropped, keeping every dot, every `<title>`, and the list under the
figure. 577 maps keep their names, 238 hand them to the list.

**The invariant register counted a font size that existed only in a comment
about not adding font sizes.** `css.font_sizes` matched the whole file, and
this stylesheet's style is long comments naming the failure behind each rule
— so a comment saying *the first version wrote `font-size: 26px`* was itself
a seventeenth size. It can only inflate a count, never hide one, so nothing
measured before was too permissive; but an instrument that reads its own
documentation as code is wrong. Comments are stripped now, and the fix was
proved both ways: a real declaration still fails, the same text in prose does
not.

**One thing, one picture — and 272 of 319 destinations had two.** `card()`
takes an optional `motif`; without one, `plate_shapes()` picks from the seed.
**Fourteen of the twenty call sites passed no motif**, including every
destination card on a country page, a region page and an interest page, while
the quiet index passed one. So Hallstatt drew its own topography on
`/beyond-the-obvious` and whatever the hash of its slug chose everywhere
else. Measured before the fix: **272 of 319 destinations, 15 of 17 journeys,
11 of 13 themes.** The rule already existed for stories — *a story is not a
place, and its picture may not be drawn from a hash* — and this was the same
failure across every other record that knows what it is. A plate is
content-addressed, so two pictures is also two cached PNGs and two social
cards for one thing. `checks.py` compares the plate every page drew for each
seed **in the shipped HTML**, because a source check on the call sites passes
the day somebody adds a fifteenth.

**An index exists to say how big a set is, and five of eight did not.**
`/journeys`, `/themes`, `/europe-in`, `/beyond-the-obvious` and `/fund`
carried a head with no count in it at all. `/europe-in` was the sharpest: it
stated **319**, the population its queries run against, and never **12**, the
number of queries on the page in front of the reader — a number that is not
the set's own extent is worse than none, because it reads as one. Every count
is derived and `checks.py` asserts it equals what the build actually put on
the page, which also catches the opposite failure this repository has already
made once: a hard-coded figure that was true two hundred destinations ago.

**Eight of the nine indexes were the same 280px card grid, and the shape of
the data was the whole layout.** That is the design-direction finding again,
one level up from the h1. Five are fixed: `/stories` is a contents page,
`/events` is a year band, and now these three.

**A card is the right shape for a set of like things chosen on LOOK.** A
journey is not chosen on look and neither is a query, so neither of them was
a card.

**`/journeys` showed everything about a journey except the journey.** Four
across, a generated plate over a name, a truncated summary and "19 DAYS · 5
COUNTRIES · MODERATE" — and four abstract landscapes in a row read as a
family rather than as four trips. The one thing that makes a journey a
journey, and the one thing this atlas holds in full, is the **ordered
sequence of places**, and it was the only thing not on the page. It is the
`row` primitive now — already on 86% of pages, so not a new component —
carrying the stops in order, with the same `hopbar` the journey page draws
laid end to end instead of stacked. **The segments are a share of the whole
trip, not of its longest leg**: the journey page asks which day is the long
one, the index asks what the trip's rhythm is.

**`/europe-in` showed twelve generated landscapes and the queries nowhere.**
Every `/europe-in/*` page prints the query that made it — that is the rule
the family exists to demonstrate and `checks.py` asserts it on all twelve —
and the index that introduces them showed a picture per query instead. **A
motion is not a place**: it has no coastline, no topography and no season, so
a plate drawn for one is a picture of nowhere standing in for a sentence. The
same failure as the stories index, one family over, and the rule written
there applies word for word. The twelve queries are printed as queries now,
generated by the same function the twelve pages use, so the index cannot
state a query the page it links to would not.

**And the assertion that broke was pinning the shape again.** The browser
suite counted `.card` on the motion index; it went red when the index stopped
being a card grid, which is the fifth time an assertion in this repository
has protected a layout instead of a promise. It counts motions and queries
now, and still fails on the thing it was written for.

**`/themes` printed a count that was the same on all thirteen cards.** Every
theme in this dataset holds exactly eight stops, so "8 PLACES" was a constant
wearing the clothes of a measurement — the `/europe-in` failure one family
over, where a number that is not the set's own extent reads as one. What
separates the thirteen is **reach**: Renaissance Europe is Italy, France and
Belgium, Thermal Europe is the United Kingdom, Hungary, Iceland, Finland,
Bulgaria, Azerbaijan and Georgia, and three countries against seven is the
difference between a corner of the continent and an argument that crosses the
whole of it. The rows carry the eight destinations and the count of countries,
and the "every one holds eight" in the note under them is derived, because a
figure typed into prose is the figure that was true two hundred destinations
ago.

**A comma cannot separate a list of European place names.** "Victoria, Gozo",
"Mestia, Svaneti" and "Nida, Curonian Spit" are single destinations here, so
the first version of that list read as nine places and ten on the one index
whose whole argument is a count. The comma was chosen to stop the list reading
as a route, which the middot on `/journeys` deliberately does — but what
actually distinguishes the two families is the **route line** under a
journey's stops, and a theme has none. That is the same absence the theme page
makes its point out of, by drawing these dots with no path between them.

**A reason typed into `docs/invariants.json` is wiped by the next
`--write`.** The register is generated exactly like `site/`, so the paragraph
recording why `/journeys` and `/europe-in` moved `primitives.reach.card`
survived one commit and then vanished with no failing check — the same class
of loss as editing a page in `site/`. A reason belongs in
`tools/invariants.py`, which is the source the register is written from.

**Twenty-one of twenty-two families place a 60px h1 at y=164 or y=212.** Only
the homepage differs, because it has a hero. On the five INTELLIGENCE pages
that is actively wrong: the head pushed the instrument to y=436 on `/plan`,
449 on `/map` and 460 on `/search`, so half the first screen of a *tool* was a
magazine headline and four or five lines of prose. **An instrument's title is
a label, because the page is the tool** — `.pagehead.instrument` reuses the h2
font-size declaration verbatim rather than introducing a thirteenth size, and
that is the argument rather than a saving. The instructions moved to the
control they describe: how the planner scores sits beside the button that
runs it, and what the search box understands sits under the search box.
Instruments now start at 328–397.

**The map's 66vh cap bought a third of its width for a promise it did not
keep.** Measured on a 1440-wide window: the whole continent was above the fold
only at a 1200px viewport height, and at 760/900/1000 the map was *both*
narrower and still below the fold. The cost was not the sea either side, it
was empty **page** either side, outside the panel, misaligned with a
full-width head. Capping by viewport height instead is worse — the wrap goes
full width and the drawing letterboxes inside it, so the empty sea moves in
rather than away. The budget is 88vh, capped at the column: 857 / 1015 / 1354
against 643 / 762 / 1015.

**Commit 27 changed the projection and left the page that publishes it saying
the old name.** `/map` went on printing *"Projection: equirectangular,
corrected at the middle of the extent"* — the projection whose scale error ran
−25.3% to +89.7%, and the exact claim the correction existed to stop being
true. Three renderers were made to agree and 54 conformality points were
asserted; not one check read the prose. A name in a comment is history; a name
on a **page** is a claim to a reader, so `checks.py` now reads the shipped HTML
only, and also asserts that some page states the projection at all — saying
nothing is how it stayed wrong. **The first version of the angle half could be
satisfied by the drawing rather than the claim**: `/map` draws its own
graticule and "35°N" appears eight times as an axis label, so breaking the
prose left it green. Scoped to the sentence that names the projection.

**The mechanism was standing in front of the answer, and saying everything
twice.** A motion's signature moment is the query drawn as a shape: "everywhere
above 63° north" is eight lit points across Iceland, Norway, Sweden and Finnish
Lapland, and you see the latitude before you read it. That map sat *below* a
grey `.note` panel with its own `<h2>The query that made this page</h2>` — the
reader met how the page was built before they met Europe. And measured across
the built site, **all twelve motion pages printed the match count and the shown
count in that panel and again in the map caption**: this family's own rule,
never explain the constraint back, broken by the family that states it. The map
now comes up to meet the head and the query is one hoisted line under it,
stated once. **The query is the proof, and proof goes under the thing it
proves.**

**Four of the twelve queries only parsed under a heading.** `motion_query_words`
builds a clause list, and the interest clause carries its own subject ("any
destination tagged Islands") while the other four are relative clauses. With no
interest term the result dangled — *"The query lying above 63° north."* The
subject is a **prefix** now, not another list item: inserting it into the list
produced "Every destination *and* lying above 63° north", which is two wrongs in
one line and the second was only visible once the first was fixed and the
sentence was read aloud.

**Five assertions pinned the panel's strings rather than its promise**, across
the UX audit and the browser suite, and all five went red for the right reason
and the wrong claim. Rewritten: the page must print the query expression
generated from **its own data** — a page can carry the right heading and print
the wrong query — must say it is not a list, must say how many matched, must say
each of those **once**, and the query must begin with its subject. Every one
still fails on the thing it protects. The duplication was invisible to the old
assertions because it lived inside the shape they were protecting.

**A year is not a list, and it was rendered as twelve identical pills.** The
events family's subject is time. The index carried a chip per month and each
month page carried previous / whole year / next — every one the same width
and weight whether the month held 3 recurring fixtures or 28. Meanwhile the
shape was in the data and printed as prose eleven screens apart. `year_band()`
draws it: the bar above the line is what is on, the bar below is how many
countries are in their quieter shoulder. **October is one of the thinnest
above and the deepest below, and that disagreement is the argument the family
exists to make** — so a band showing only "what is on" would have drawn the
opposite of this atlas's editorial position. The first version drew the
shoulder as a 3px rule beneath each bar and it read as an underline; the one
thing worth seeing was the thing you could not. **No aperture on it** — the
door is how this atlas draws geography, and twelve little arches would be
the signature as wallpaper.

**A chart is a claim, so both series are checked against the dataset.**
`checks.py` counts the fixtures and the shoulder countries independently of
the generator, asserts every printed figure appears on all thirteen pages,
and asserts the bars are still scaled by the series they are labelled with —
correct labels over a drawing scaled from the wrong array still reads as a
finished chart. Proved red three ways.

**`preserveAspectRatio="none"` stretches the type with the picture.** Twelve
columns *should* fill whatever width they are given, and that transform
scales everything in the viewBox — so with the month names inside it they
rendered at 49% of their own width on a 390px screen. Setting `font-size` in
CSS does not save it; the transform is applied after. The SVG holds the
geometry and the names are an HTML grid beside it, which also fixed the
interaction: a 2px bar was never a reliable target.

**A story is not a place, and its picture may not be drawn from a hash.**
`plate_shapes()` picks a motif from the seed when none is passed, so for a
year every essay opened on a landscape chosen by chance — the piece about the
last unlogged primeval forest in Europe opened with tower blocks. A story
opens on `storymap()`: the destinations in its own validated `places` field,
same projection as `/map`, real coastline, through the arch. A photograph
first if the register holds one; never an illustration.

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

**There is no electric lime either, and it went for a different reason than
the gold.** Gold went because of what it says. `#c8ff4d` went because of where
it was being spent: declared as the dark world's accent — five per cent of a
screen — and used to draw seventeen journey routes, 894 homepage dots, 319
destinations on `/discover`, 172 experiences and every lit country on every
region glyph. A continent drawn in the accent is a network diagram, which is
the association the cartography split exists to escape, arriving through the
accent instead of through the ground. The dark world's accent is `cobalt-air`,
which the palette had already measured for that ground in the DISCOVER-dark
block: 7.06 on graphite, 6.31 on the card, 6.04 on the deep surface. Removed
rather than rehomed, with a guard on each end, and `css.lime` is an invariant.
**The declaration is what is refused** — `--lime` is a prefix of `--limestone`,
so the obvious form of that assertion is true of every stylesheet that has ever
existed here, and it passed for one run while reading its own naming scheme.
**And the browser probe read `color` and nothing else**, so it asked whether
lime was set on TEXT — which is the one property it was never mostly on. It
reads fill, stroke, colour and background now, over the whole document.

**The glyph family is cartography and never got the cartography.** The palette
splits maps on what the drawing IS: a picture is warm paper, pale water and an
ink coast; an instrument is graphite. That split was applied to the 824 plates
and to nothing else. Every theme row, every journey row, every story, the
homepage tiles, all nine region glyphs and all five index openings kept a grey
wash and the dark world's accent — the largest map family on the site by page
count, and the only one still outside its own standard. They are the atlas
palette now: `--atlas-land` for the land, `--atlas-here` with an ink frontier
for what is lit, `--cobalt` for the marks, and a hairline of the land on every
mark so it separates from whatever it sits on.

**A route needs a casing, and the arithmetic is what says so.** Cream land is
0.70 luminance and the Atlantic is 0.055, so a stroke needs to be above 0.265
to clear 3:1 on the water and below 0.20 to clear it on the land: no colour
satisfies both, and a route that crosses the Baltic either disappears at the
coast or shouts on the land. Every printed map answers this with a casing —
a wider stroke in the ground's light tone under a narrower one in the route's
colour — and `pages.route_line()` is that, in one place. On the seventeen-route
opening **all the casings are drawn before all the cores**, because a
per-route casing lays the next route's cream stroke over the last route's
cobalt one and every crossing becomes a break.

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

**Declare every dependency that crosses a boundary.** `data/contracts.json`
names, for each script, which index it reads and which fields — with a reason
per field. `checks.py` fails on a declared field that vanishes AND on a script
fetching an index it has not declared. Coupling is fine; silent coupling is
not. The live case is the search index's live counts, which the empty state
prints — it used to carry a hard-coded figure that had been true two hundred
destinations earlier.

**Five applications, two enhancements, and the test is behavioural.** An
application fetches an index or owns client state, and must declare what it
depends on in `data/contracts.json`; an enhancement does neither, operates on
markup already in the page, and stays under a hundred lines. Most of the site
loads no JavaScript at all. The first version of this check was a list of
filenames and
had the boundary backwards — it counted `events.js` (36 lines of checkbox
filtering) as an application and `my-europe.js` (which owns all three storage
keys) as not one.

**Eleven primitives cover the site**, four of them on 100% of pages. Changing
`render.section()` changes every page; changing a page changes one. A check
puts a floor under each primitive's reach, so a page family cannot quietly grow
its own component set. **No new primitive until repeated structure has actually
emerged** — do not invent a `ResultCard` family for a shape that has not
appeared three times.

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

**The Data Integrity Rule: never author a measurement; you may author a
classification.** `population`, `iso3`, coordinates and distances are derived,
carry their source, and are absent where there is none. `village`, `valley`,
`island`, `site`, a region's type, a story's section — those are the editorial
work and are authored from a stated vocabulary. Authoring "an authenticity
score of 87" invents a measurement; authoring "Theth is a village" is the job.

**The order of authority is: principles → built system → measurements → checks
→ architecture → future extensions.** Not architecture → force implementation →
justify. A blueprint is a hypothesis; when the running system disagrees, and
the disagreement is *measured*, the blueprint changes. Three things here exist
because of that: SVG rather than MapLibre, no Postgres, and a derived graph
index rather than a `relationships` table.

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

**A visual change is a controlled experiment, and `docs/invariants.json` is the
control.** Twenty-one things that must not move while something else does —
one shell, one stylesheet, zero webfonts, zero inline styles, zero `<img>`
tags, zero golds, five applications, the route-set hash, and a floor under
each primitive's reach. `exact`, `ceiling` and `floor`; every row carries a
reason, and a row without one fails. Moving one is allowed; moving one
*silently* is not — `tools/invariants.py --write` in the same commit is the
deliberate act. **`routes.hash` is the important one**: a restyle must not move
a URL, and every inbound link and social card depends on that.

**A plate's light is fitted to the sky, not placed by the seed.** It used to
be emitted before the motif, so a skyline's towers sliced it into a crescent
that reads as a stray glyph at card size — and it was not one plate, it was 69
of 319. The first fix pushed it up with no floor and cropped it against the
frame instead. It is now fitted: never more than a third of the available sky,
clear margins, and no moon at all where there is no sky. A geometric check
asserts it on every plate at both output sizes.

**A motif nothing reaches is dead code that looks like vocabulary.** `plain`
was declared for the life of the plate system and never drawn, because
`food → plain` sat below eight interests almost every European destination
carries. Reachability is an invariant now.

**Motif selection consumes `city_type`, but only where it is decisive.**
village, site, island, valley, park — and topography still gets first refusal,
so Theth is a mountain village and draws peaks. capital, city and town are
deliberately left to the interests: mapping all eight put a *universal* field
above the interest pass and `forest` fell from 19 plates to 1. One dead motif
traded for another.

**An instrument can be wrong three times and look right each time.** Measuring
within-motif variation reported "peaks: 92% duplication" (bounding boxes made
every ridge one constant), then "isles: 79%" (the scanline ignored ellipses),
then "isles: 74%" (the islands sit *below* the horizon and are interior detail,
not silhouette). Only rendering at 64×40 and comparing pixels was right —
measuring a drawing requires drawing it. `tools/plate-variation.py` holds a
ceiling on interchangeable pairs per motif family; it is not in `checks.py`
because eight seconds on every build is a gate people stop running.

**The hero is the doorway, and Europe is what is through it.** Stripped of
its mark and set beside eight other families by `tools/recognition.js`, the
homepage was the *least* EuropeDoor page on the site: a navy gradient, a
headline, a search box and four chips — a travel product and nothing more
specific. Six of the other eight carried the aperture and were unmistakable.
The one page that has to say what this is said the least.

So the opening is cut here at the largest size the arch appears anywhere, the
masthead stands on the limestone wall above it, and Europe is drawn inside —
one silhouette, no dot, no filter, no count, no label.

**Europe is not an island, and for three commits the hero drew it as one.**
`data/geo/` stops at 52°E and 33°N because that is where this product stops
writing about places, so the hero faded its own eastern quarter and its
southern eighth to stop two straight data cuts reading as rendering faults.
That is an honest way to hide an edge and a poor way to draw a continent. The
land carries on now — `beyond-lod0.json`, anonymous rings out to the Yenisei
and down past Arabia, no country, no relief, no label, nothing to click.
**The fades stayed exactly where they were and now do the opposite job**:
they no longer hide an edge, they hand the eye from the lit continent to the
ground around it.

**And that ground is graphite, not quieter parchment.** The first version
drew Asia and Africa from the same paper at a sixth of its presence — quieter
Europe, in other words — and it read as a haze the eye kept trying to resolve
into countries. Solid `--graphite`, the near-black the INTELLIGENCE world is
grounded in, says the thing the picture is for in one move: **Europe is what
the light falls on**, and the two fades run from lit parchment into shadow.
The hero stops being a map with a quiet margin and becomes a door with a lit
room through it. `--graphite` rather than `#000` for the same reason
limestone is never `#fff`: black is a screen and graphite is a shadow.

**A black ground has edges a pale one hides.** `preserveAspectRatio` was
`meet`, which letterboxes — and a letterbox band is where the drawing's own
frame edge shows, black meeting blue on a straight line 14 pixels above the
bottom of the hero. It is `slice` now: the margin this frame gained east and
south exists precisely to be cropped. Stacked, the drawing also runs full
width and to the top of the opening, where the arch cuts it, and fades over
its last tenth because the type is underneath. **That bottom fade is not the
one that was removed** — that one hid a data cut at 33°N and now lives inside
the drawing as a radial gradient along that parallel. This one ends the
picture, and a picture that ends may say so.

**The art-direction pass, and its test was a 20% crop.** Cut the hero into
tiles the size of a fifth of it, hide the masthead, the wordmark and the
headline, and look: the middle tile read as *a competent atlas of north-west
Europe* and as nothing else. Half of it was one flat blue field and the other
half was one flat cream one. Everything that followed came from that tile
rather than from a list of features other maps have.

**A shore band, from the palette's own ocean ramp.** `--ocean-deep`,
`--ocean-mid`, `--ocean-shallow`, `--ocean-coastal` — four steps, and the hero
used one and a half of them. The land's silhouette, blurred four and a half
units, in `--ocean-shallow` under everything: the North Sea, the Irish Sea and
the Baltic become near water and the open Atlantic stays far. **Constant
width, because it is a drawing convention and not a claim** — nothing here
holds a sounding, and real bathymetry is not a constant band. No geometry: a
`<use>` and a blur.

**A soft halo reads as an object glowing; a narrow one reads as water.** The
first version mixed a lighter blue by hand and blurred it at nine units, and
Iceland came out with a lit aura round it. Same idea, four units apart.

**The coast is heavier than a frontier now, for 27 bytes.** A coastline is
where land meets sea and a frontier is a line drawn on land, and both were the
same stroke. A `<use>` UNDER the land, stroked wider and darker, shows only
the half of its stroke that falls outside the fill — exactly the coast, and
never an internal border, because a neighbour's fill covers it. **It is not a
`lyr-` layer and the order check was right to say so**: ORDER puts `coastline`
after the rivers, where it would stroke every frontier at coast weight.

**Paper.** Fractal noise at a fine frequency, desaturated, multiplied over the
land at 8.5%. It claims nothing and is the same everywhere; it is the
difference between a fill and a surface. **On the LAND, not the frame** — the
first version covered the SVG, which is 78% of the hero inset right, and drew
a hard vertical seam down the middle of the Atlantic between grained water and
smooth water.

**And the reveal, which is the one part of the signature the hero did not
have.** Every plate cuts the aperture three ways and then draws two more
things at the cut: the wall's face laid over the drawing's edge, and a fine
ink line just inside it — which is what an opening in masonry actually shows
and where the eye reads depth from. The hero cuts the arch at the largest size
it appears anywhere and had a rounded rectangle. Same colour, same weight,
same 38% graphite as the 824 plates, fading out down the sides because the
bottom of this arch is not a cut. An `outline` rather than an inset
`box-shadow`, because the register counts shadows and two is the whole
vocabulary.

**The countries are named, and the name is the only type on the picture.**
Every other map here sets a country's name across it, and for the same second
reason: the recognition instrument strips the wordmark and the page title, and
a drawing that names what it draws survives that where a shape alone does not.
Placed by the atlas's own single placement rule — the centroid of the
country's drawn shape, then eight points around it, each of the four positions
tested against the frame and against every name already down — in the plates'
own tracked uppercase, so no font size is introduced. Twenty-three of the
forty-four are named; the rest are dropped, and keep their shape, their
frontier, their link and their accessible name.

**Three rules were needed and none was obvious.** Without the first, the
nine anchors and four positions are enough freedom to LEAVE: ICELAND floated
in the Denmark Strait, UNITED KINGDOM and PORTUGAL sat in the Atlantic and
BOSNIA AND HERZEGOVINA lay across the whole Balkan peninsula. **A name's
middle must be on the country it names** — it may run out over the sea, which
is what a printed atlas does with Norway, and it may not start there.

That fixed the position and left the width: SWITZERLAND then ran from
Bordeaux to Munich, correctly centred, CROATIA lay across Bosnia and AUSTRIA
across Hungary. **A BOUNDING BOX IS NOT A COUNTRY** — the middle of Croatia's
box is in Bosnia — so the test is the real polygon, and the second rule is
that **a name may run over water and never over a neighbour.**

**And "not one point on a neighbour" was the wrong rule, measured.** It left
ten names and dropped GERMANY, POLAND, SWEDEN, NORWAY, FINLAND and UNITED
KINGDOM, which are exactly the countries a reader orients by. A printed atlas
lets the ends of a name touch a neighbour; what it never does is lay a name
ACROSS one. So the third rule is a fraction rather than a flag: ten samples
along the name, at most two of them on somebody else's ground — tried at zero
first and at two only if nothing fits, so the nine anchors choose the cleanest
placement available rather than the first tolerable one.

**Fifteen names, and the number is geography's rather than a target.** Raising
the ceiling to 99 produced the same fifteen: RUSSIA, TÜRKIYE, UKRAINE, ITALY,
SWEDEN, FRANCE, SPAIN, GERMANY, UNITED KINGDOM, POLAND, ROMANIA, GREECE,
ICELAND, AZERBAIJAN, IRELAND. **The question is not how many countries can be
labelled** — an earlier, looser version put twenty-three on and every extra
one was a name lying across its neighbours. The rest of the continent is read
from its shape, which is what the shape is for. The countries are also placed
LARGEST FIRST, by drawn area, because in document order — alphabetical by ISO
code — Albania took a position before Germany was asked for one.

**And they come off below 44rem.** `--t-lg` is a length in a 1,120-unit
viewBox: at 390 that is a third of a pixel per unit, so a twenty-unit name
renders at seven pixels — not small type, type that does not resolve into
glyphs. It is the same measurement that took the map labels off narrow screens
on eight hundred pages.

**Every country on the hero is a door, and for one commit none of them
opened.** The picture's one job is to be the way in and it led nowhere:
`aria-hidden`, `pointer-events: none`, not in the tab order. Each of the
forty-four countries with a polygon is an SVG `<a>` now, named by its own
`<title>`, with the fill lifting under a hover or a keyboard focus. Still no
dot, no label, no filter, no legend and no count — a link is navigation, and
a control is what the brief refuses.

**Three things had to be undone before a click could reach one, and the
first two both worked from the keyboard.**

- **A masked group hit-tests as ONE region.** The atlas layers sat inside two
  `<g mask>` wrappers to fade toward the data cuts, so the click landed on
  the wrapper and stopped. Enter on a focused country navigated perfectly,
  which is exactly the kind of half-working that ships. The fade is PAINTED
  now — a graphite rectangle whose alpha ramps along the same band, masked to
  the atlas's own land so it dims the continent and not the Caspian — and the
  layers underneath it are unmasked and clickable.
- **`pointer-events: none` on the drawing was not overridable from inside
  it.** A child set back to `auto` did not receive the click; the target was
  the `<svg>`. Each layer above the land is set to `none` individually
  instead, because a rule that has to be overridden is a rule that will be
  got wrong again.
- **Every layer above the land has a fill and swallowed the click in turn** —
  terrain, then rivers, then the frontiers, then the dusk.

**`<clipPath>` takes shapes, so the relief vanished the moment the land became
a group.** The clip was `<use href="#heroland"/>`, `#heroland` became a `<g>`
of fifty countries, and Chromium renders a `<use>` of a group inside a
clipPath as nothing at all — every band gone. The terrain layer was still
there, still in ORDER, still counted by every check that counts layers. Only
looking found it. A mask takes any content.

**A `<use>` clone does not inherit a stroke-width from a selector that does
not match it.** The dusk is masked by a `<use>` of the land, and the land is
stroked at 1.4 units to close its seams while the clone took the default of
1 — so two tenths of a unit of parchment stayed uncovered along every edge,
which along the 700-unit straight cut at 52°E is a bright hairline exactly
where the picture must not have one.

**A two-stop gradient has a crease at each end and the eye draws a line along
it.** Every fade here was white-to-black in two stops: the brightness ramps at
a constant rate and then stops dead, and human vision sharpens exactly that
discontinuity — a Mach band. The ground arrived out of the dark along a
perfectly straight diagonal that nothing in the drawing had drawn, and it was
reported as a hard edge three times while "soften the gradient" never fixed
it, because widening a linear ramp moves the crease without removing it.
Smoothstep in five stops has zero slope at both ends and there is no crease to
find.

**The ranges are drawn as an edge rather than as a name.** The Alps, the
Pyrenees, the Carpathians, the Scandes and the Anatolian ranges are exactly
where the 1,200 and 2,000 metre bands are, but as a tonal wash they read as
haze at this size. A hairline on those two band boundaries turns the wash into
a ridge: same data, same layer, no new geometry, nothing to read. Thinner and
paler than a frontier, because a range is a fact about the ground and a border
is a claim about it. The band count is asserted by the FILLS for that reason —
a rule counting selectors read the ridge as a fourth band and a second
strength.

**The hero was a relief sculpture of Europe, not an atlas of it.** Water,
silhouette, terrain — three layers, where every other map here draws
frontiers, rivers, lakes, a coastline in ink and a subject. The land was one
value everywhere, so the eye could not read coast → country → mountain →
water, which is the whole difference between a map and a beautiful shape.
Five layers were added and one was tested and rejected.

**Frontiers cost 27 bytes, because the pass is a `<use` of the land path.**
ORDER puts `country-bounds` above `terrain` and it has to — a boundary here
is a stroke on the land path and the bands paint over it — and repeating
43 KB of country rings on the homepage to say so is not affordable. The escape
from the `<use>` selector trap that this repository already lost a day to is
to **paint by inheritance rather than by id**: nothing selects `#heroland` any
more, fill and stroke sit on `.herolandg`, so the clone inherits from its own
parent and comes out a stroke with no fill. One ink draws the frontiers and
the coast, and the coast comes out the sharpest line in the drawing without a
second weight being declared anywhere — a frontier has parchment on both sides
and a coastline has the sea on one.

**The water had to become water.** `--ocean-deep` alone is very nearly black
against warm parchment, and the hero was pinned to the deepest step of the
Atlantic ramp because it was built when the map was a faint silhouette that
needed the contrast. It sits 55% up that ramp now, the land went 0.78 → 0.90
so the parchment is luminous rather than grey, and the relief dropped to
52/62/74% so the Alps are discoverable rather than the headline. Limestone
measures 7.7:1 on the new ground and 6.9:1 on the lightest point of the pool
over it, against 10.4 and 8.4 before.

**Rank is where restraint lives in a water layer.** The plates draw rank 6 and
every lake, which over the whole continent is 153 rivers, 65 lakes and 49 KB —
a hydrology map with Europe underneath it. The hero draws rank 3 and cuts
lakes by **drawn area** rather than by the dataset's own importance, because
what a picture wants is the ones you can see: 9.5 KB, 35 rivers, 22 lakes,
and Ladoga, Vänern, Balaton and Geneva are all still there.

**Nine marks were built, measured and removed.** The brief asked for seven to
twelve extremely restrained points, so the continent would not read as empty
terrain: one per macro region, on the real destination nearest that region's
centre, no label, no link, no title. At 2.6 units they render 2.3 pixels wide
and you have to hunt for them, so they do not say the thing they were added to
say — and anything large enough to say it is **a dot on the cover of an atlas
that the page cannot name**, which is principle 2 and is held at 176 marks
named out of 176 across the fifty country plates. The centroid version also
put one in Belarus, an advisory country stripped from the planner: a derived
point is not automatically an honest one. The sentence under the picture
already says it in words.

**Two levels of detail of the same coast can be stacked only where one is
hidden.** The ground beyond the atlas was every landmass in a box that
CONTAINS Europe, so under every European coast there was a second, coarser
copy of the same coastline — and in graphite under translucent parchment the
disagreement showed as a **black fringe** five or six units wide along
Anatolia, the Black Sea and North Africa. It reads as a drop shadow, which is
exactly the kind of accident that gets mistaken for a decision. The layer is
cut to the atlas's **complement** now — the strip east of the atlas and the
strip south of it — which also took it from 18 KB to 6.

**And a complement has to cross-fade, not abut.** Cut exactly at 52°E and
33°N the two met edge-to-edge, and the atlas's eastern fade is 320 units wide
and already down to 4% at 46°E: between them was a band of bare sea and then a
hard black diagonal, which is the rendering fault the fade was written to
remove, arrived at from the other side. Each strip reaches back into the atlas
and fades **in** along the same edge the atlas fades **out** along — the same
gradient geometry with the stops swapped — so the two cross over and neither
has an edge. The strips are kept separately in the file for that reason: one
mask for both would erase the Sahara or the Urals depending which edge it
followed.

**A parallel is not a horizontal line on a conic, and the first southern fade
was one.** The 33rd runs from y=706 over Tunisia to y=590 over the Caspian,
so a horizontal gradient placed on the Tunisian end left the cut showing right
across Anatolia — the same failure as the vertical fade over the 52°E cut, one
edge round. A conic's parallels are circles about the cone apex, so it is a
**radial** gradient centred there (`geo.Projection.apex()`), exact at every
longitude by construction. And the box that data comes from has four straight
edges through real land: `checks.py` asserts that no vertex of a drawn ring
sitting ON one of those edges projects inside the hero's frame — the test is
where the cut meets land, because the western edge cannot be moved out of the
frame at all under this conic.

**The ground layer must not be stroked, and stroking it drew a rectangle.**
`#heroland` closes hairline seams between independently simplified neighbours
with a stroke in its own fill colour; the ground has no seams to close, and
its rings are clipped to the frame — so a stroke ran along all four edges of
the window and outlined it. On the parchment version that was a pale panel
behind the continent; in graphite it would have drawn the frame itself. Found
at 390px; on a desktop it was faint enough to read as atmosphere.

**The hero has its own window on the projection, and the stylesheet must
agree with it.** `pages.HERO_VIEW` is 1120×800 where every other map is
1000×780. An SVG clips to its VIEWPORT rather than to its viewBox, so the
phone rule's `aspect-ratio` carried the old 1000/780 for one commit and the
two twelve-pixel letterbox bands showed the geometry outside the frame as a
straight line above and below the continent. A check asserts the two agree.

**The side-by-side hero has nowhere to put a continent on a phone.** Held at
78% of a 390px screen the drawing was 304 units wide for the whole of Europe
and the headline crossed the Mediterranean. Below 52rem the two columns become
two rows: full width, its own proportion, the type under it — 304 to 390 units
and a quarter of the opening to half of it, with nothing cropped. Capped at
54vh, because at 820 wide the same rule made a 1,044px hero out of a 900px
window, which is the same fault the other way round.

**Every page that draws relief names the survey that measured it, and the
sentence in the licence document named the wrong one.** `docs/data-licenses/
aws-terrain-tiles.md` asked for "SRTM and GMTED2010" — true of the six zoom-7
prototype tiles and false of the 182 zoom-6 tiles that ship, whose imagery
headers name gmted and etopo1 and never srtm. `checks.py` now derives the
credit's dataset list from those recorded headers, at the zoom the terrain
document says it was built at, and asserts every page carrying `lyr-terrain`
names each one. **The credit is attached to the drawing, never to the
request** — `cartography.credited()` takes the rendered terrain markup, so a
journey that asks for relief and is refused it for its width cannot print a
credit for a layer nobody can see.

**A credit whose link goes to a page that does not carry it is worse than no
credit.** Every map on this site ends "Coastline from Natural Earth" with
Natural Earth linked to `/sources`, and `/sources` did not contain those two
words anywhere. It is built from the `sources` rows inside each `data/geo/`
document now — dataset, licence, version, the SHA-256 of the exact bytes and
the date they were fetched — so it cannot drift from what actually drew the
maps.

**A hero map was removed once, for reasons that do not apply to this.** That
one was an *instrument*: lod1 coastline, 319 dots, a filter row, ~90,000
bytes, and it led with structure. This leads with a continent.

| | bytes |
|---|---|
| the hero map that was removed | ~90,000 |
| the first version of this, a lod0 silhouette | 22,927 |
| Europe at lod1, thinned to 1.8 units | 42,550 |
| the hypsometric relief over it | 25,305 |
| the ground beyond the atlas | 18,171 |
| the licensed photograph the brief is still open for | 150,000+ |

`weight.home_kb` moved 25 → 47 → 109, each time recorded. **1.8 units rather
than 2.4 because the Europe side is where the detail is worth paying for**:
2.4 is 2.1 device pixels at this size, coarse enough to round the Danish
straits and turn the Aegean into wedges. The ground beyond is thinned three
times harder for the opposite reason. **The photograph brief stays
open** — a photograph does a job this cannot, the atmosphere of a particular
morning. This does one the photograph cannot either, and it is the reason it
is here rather than a placeholder: **no other travel product can draw Europe
on its own conformal conic through its own aperture.**

**Three things only rendering found.** The masthead's graphite scrim — right
for type over a photograph — painted across the two corners that make the
opening read, so the whole thing became a dark banner with a curved bottom;
the masthead now stands on the wall in the wall's own colours. Stroking every
country path made it a *political map*, fifty internal borders competing with
a headline; filled, adjacent countries merge and the only outline is where
land meets sea. And `data/geo/` is cut at 52°E, which under the conic runs
from x=747 at 70°N to x=1024 at 40°N — a clean diagonal through Russia that
reads as a rendering fault at screen scale, so the drawing fades where what we
hold ends.

**Moving the form out of the opening took its label with it.** `.askhero
label` was limestone at 76%, right on graphite and **1.00:1 on the light
band** — present, labelled, keyboard-reachable and invisible. The browser
suite caught it; nothing else could have.

**The old rule, kept because it is still true of everything below the fold:**
**The homepage leads with Europe, and the hero is photographic.** Cutting it
from eight bands to three fixed a catalogue and left a different fault that
only looking at the built page found: it led with *structure*. A headline, a
form, a technical note, a row of counts and a data map, above eight identical
generated tiles — an information architecture demonstration. The reader met
the data model before they wanted to go anywhere. The hero is now full-bleed
with the masthead over it (`body[data-hero]`, one shell, a body attribute the
single stylesheet reacts to — never a second header), the map is gone from it,
the counts are below the fold, and the eight equal tiles are an asymmetric
mosaic. **`.card` is unchanged: an asymmetric grid appears nowhere else in the
codebase, so the mosaic is a layout, not a new primitive.**

**The plate system cannot carry a hero, and that is measured.** Rendered at
1200×500 it is flat and monochrome with a dead slab across the bottom third —
it has nothing to reward a reader who looks closely. It keeps every other job.
That measurement is the whole justification for licensing a photograph, and
`docs/hero-brief.md` holds the brief and the seven-question licence gate, all
seven still unanswered. **Nothing may be committed against that gate from a
provider's marketing page or from memory** — the sandbox proxy answers 403 to
CONNECT for general hosts, so acquisition is a human step. Two independent
guards, both proved red: `checks.py` refuses an `<img>` with no register row,
and `safety.img_tags` catches it again.

**Weight is now an invariant, because for one commit it was not.** The
homepage shipped at 118,935 bytes while the commit message reported 45,806 —
90 KB of inlined coastline under a hero map, 76% of the page — and every
static check, every browser check, every section assertion and every
invariant said nothing, because not one of them measured bytes. `weight.home_kb` and
`weight.max_page_kb` are ceilings now. The homepage is 26 KB.

**The homepage is the door, not the catalogue — three bands, and the count
is checked.** It ran to eight: four doors, twelve motions, the quiet places,
the stories desk, the macro regions, seventeen interest tiles, a planner pitch
and the journeys. Every one was a real surface worth linking to, which is
exactly how a homepage becomes a contents list — no single section is wrong
and the sum says "here is everything we can do" instead of "here is Europe".
Now: hero, eight ways in, three journeys, stop. `section-audit.py` asserts
**two `<h2>` bands** as both a floor and a ceiling, because restraint erodes
one defensible section at a time. **Cutting a band orphans nothing here** —
every removed surface keeps its page and is linked from all 1,072, and the
audit asserts that too. And when a band goes, check what it was the *only*
home for: the four doors are a Brand Bible element and for one build they
existed nowhere on the site, so they moved to `/how-it-works`.

**A homepage assertion that demands six bands forbids restraint.** Cutting
the page turned four checks red, and none of them was wrong to exist — they
had encoded the old page's *shape* (six named stages, three ghost CTAs, a
filter row, a section title) rather than its *promise*. Each was rewritten to
assert the promise: the stages named must be real ones in canonical order
ending on Go, the primary CTA must precede the secondary wherever the
secondary now sits, the map filters must exist on the map that acts on them.
Weaker claims, made deliberately, and each still fails on the thing it was
protecting.

**Counting says a family is repetitive; only ablation says which layer to
change.** Three attempts to vary `tower` reasoned from the drawing and picked
the shaft, which paints 4% of a card-sized plate. Deleting each layer in turn
and re-counting the twins — `plate-variation.py --ablate tower` — found that
68% of the plate was two ridges carrying no variation at all, and that the
foreground one was *hiding* the nave and shaft, the only layers that vary:
removing it made the family more varied, not less. Seeding those two
constants took tower from 41 twin pairs to 27. **Seeding the ridges'
amplitude and segment count — the exact fix that took coast from 125 twins to
25 — moved nothing: 41 to 41.** The same repair does not transfer between
motifs. And read a negative delta against what is underneath: `isles` reports
its water as occluding, but the only thing under that water is the sky.

**Accommodation is a referral, and the whole design problem is keeping that
visible to a reader rather than only true in a contract.** The Stay layer is
built on one exemplar, Chamonix. It sits where a reader who has decided to
come would look for it — after the reasons, before the onward stops — and the
UX audit has asserted that order by id since before it existed.

**The first question was not "which provider" but "what do we actually
know".** This atlas holds no rooms, no prices, no availability and no ratings,
so any card grid it drew would be somebody else's inventory under our
masthead. What it holds and no booking site has is a judgement about the
PLACE: the ground within 40 km of Chamonix spreads 1,798 m and crests at
2,752 m, and *therefore* the valley floor, and *therefore* the town. That is
the only family whose signature moment is a derivation rather than a drawing.
Paris reads 102 and 150, so the paragraph is omitted there rather than filled
with a sentence about nothing.

**A provider is a link mechanism and a credential, and deliberately nothing
else.** `data/stay.json` declares `search_url`, `place_param`,
`partner_param`, `partner_id` and — required, at least forty characters —
`inventory_api`, which says what that provider can and cannot supply. Expedia
says NONE in capitals, because its creator programme offers tracked links and
no general API, and the standing temptation is to assume every large provider
has one and design a card that silently has nothing to fill it. Adding a
provider is an edit to that file and touches no page code.

**Two honest states, and the state is read off the credential.** With no
partner id the link is plain, `rel` is `nofollow noopener` and the page says
we are not a partner and earn nothing; with one, the link carries it, `rel`
gains `sponsored` and the disclosure becomes the commission sentence.
`checks.py` asserts `sponsored` appears **if and only if** a credential
exists, both directions proved red. **A disclosure that only appears once we
are paid is an advertisement with a conscience** — both states carry one.

**The card was asked for and is not built, and that is a sourcing fact rather
than a taste.** A photograph, a property name, a rating, a nightly price and
an availability state are five refusals, each enforced at least twice. None is
refused because a card is a bad idea: under a link-only affiliate mechanism
there is no honest source for any of them, and Booking.com's Demand API — the
one interface that would return a property with an attributed booking URL — is
for managed partners only, which needs the entity. `stay.inventory()` is the
seam, it returns nothing, and a page that gets nothing draws the reading
rather than an empty frame, because present-but-empty says "we have this" and
then does not.

**A ranking of accommodation is refused outright.** `/for-businesses`
publishes the sentence "there is nothing in its index that could carry a
boost", and a ranking module is the mechanism that sentence says does not
exist. `rank`, `boost`, `featured` and `sponsored` are refused by key in the
Stay registry as well as everywhere else.

**A CHECK CONFLATED AN OUTBOUND LINK WITH A SUBRESOURCE LOAD.** "No
third-party origin, which is what makes `default-src 'none'` hold" matched
`src` and `href` together, so the referral tripped it on the day it shipped —
right that something new had happened, wrong about what. `default-src` does
not govern navigations. Split into the two real promises: nothing may LOAD
from another origin, and nothing may NAVIGATE to another origin unless that
host is a declared, enabled provider carrying `rel="nofollow noopener"` and
opening in a new tab. That pins the set of external hosts to the registry, and
five ways of breaking it were proved red.

**An audit assertion pinned the literal old heading, and it was a landmine
rather than a live failure.** `section-audit.py` required
"Accommodation & restaurants" on a destination page — true of all 319 only
while none of them had a Stay layer, so the day the grammar propagated it
would have gone red for a page that had got *better*. Seventh assertion in
this repository to protect a shape instead of a claim. It asserts both states
now. **The heading is derived from what the place is** — "Sleep below the
peaks" under measured relief, "Stay on the island" on Naxos — because 319
authored headings is 319 chances to write "Hotels", and the validator refuses
a heading containing that word.

**The accessibility scan represented the destination shape with a page that
did not have the thing.** Bergen has no accommodation context, so the two
quietest paragraphs on the new section — who holds the rooms, and the
disclosure — had never been contrast-checked in either preference. That is the
thumb-bar failure again. Chamonix is in the list now, and a dedicated block
asserts the referral is a 24px target with a real name, that the disclosure is
*visible* rather than merely present, and that loading the page makes **zero**
requests off this origin — which is also the answer to how it behaves on a
slow network: there is nothing to be slow.

**No photograph, and it is a licence position rather than an aesthetic one.**
This is the family where a photograph does work type cannot — you choose where
to sleep partly on what the place looks like at seven in the morning — and the
only images that exist belong to the providers and arrive with affiliate terms
instead of a photographer, a source and a licence. A row waiting on a
measurement is answered by rendering something and looking; a row waiting on a
source is answered by a purchase order. The no-image state here is the
SHIPPED state, not a fallback.

**No second map.** Accommodation drawn as geography is the right long idea and
needs coordinates we do not hold; a second arch four screens below the first
would be the signature as wallpaper, and a pin has no page here to link to,
which makes it a dot the page cannot name.

**Rules and space, and four things deliberately absent: no border box, no
radius, no shadow, no fill.** Those four are what say "separate object, placed
here by a system". The action and the boundary sit side by side — the first
version stacked them in the left half of a 1,168px band with six hundred
pixels of white beside them, the same fault as the old stories index, found
the same way, by rendering the page instead of reading it.

**The masthead is the one band of signature colour, and the measurement is
why it is not the colour that prompted it.** It was paper on paper — a
limestone bar over a limestone page, separated by a hairline — which spent
none of the 10% the ratio gives cobalt on the single element that appears on
every page of the site. The prompt was a booking site's navy band, and measuring
before copying reversed the premise:

| | hue | saturation | lightness |
|---|---|---|---|
| the OTA's CTA blue `#006ce4` | 212 | 100% | 45% |
| this palette's cobalt `#3157ff` | 229 | 100% | 60% |

**Ours was already the brighter blue.** What differed was COVERAGE: a solid
band across the top of every page against a pale one. So the band is the
borrowed idea and the colour stays ours — which also matters because `/about`
publishes "Not an OTA" and destination pages now link to one, and wearing an
OTA's livery on the page that links to it blurs exactly the boundary the Stay
layer exists to keep visible.

**No new token and no new claim.** `limestone on cobalt-deep` was already in
`docs/palette.json` at 6.31:1 because the primary button has always used it.
Measured on the shipped pixels rather than on the declaration, because the bar
is translucent and the ground behind it differs by world: `#3251da` over
limestone and `#2847d0` over graphite, carrying the resting nav ink at 4.63
and 5.31 and the wordmark at 5.84 and 6.70. It is 96% opaque where the paper
bar was 88%, because the ink-to-ground margin here is 5.00 where graphite on
limestone was 17.4, and there is far less room for content scrolling
underneath to eat it.

**The mark's two tones invert rather than recolour.** On paper the frame is
ink and the leaf is the signature; on the signature itself a cobalt leaf
measures **1.28:1** and is simply not there. The leaf becomes the brightest
thing in the mark and the frame steps back — the same two-tone reading with
the emphasis reversed, both clearing the 3:1 a shape needs. Never one shape at
reduced opacity, which is what the mark's own comment has said since it was
drawn.

**And a thumbnail is not a measurement.** Reading the rendered `/map` at
screen-shot size, the bar looked graphite and the INTELLIGENCE world looked
like it had lost the change to a specificity collision — which this stylesheet
really has lost three times. Sampling the actual pixels said `#2847d0` on
every page in both worlds and both colour-scheme preferences. *Look to find,
count to conclude* cuts both ways: the eye is what finds a defect and it is
not what confirms one.

**Eleven abstract plates in a column is placeholder art doing a picture's
job, and it was the whole homepage body.** The hero is strong and everything
under it was a search form, eight purple gradients over "Find your kind of
Europe", three more over the journeys, a grey note and three hundred pixels of
nothing — a SaaS body under an atlas hero. The plate system was already
measured as unable to carry a hero; the same measurement applies here, and the
mosaic layout did not fix it because the *pictures* were the problem, not the
grid.

**What replaced them is not a better painting, it is the data.** Every
destination carrying that tag, lit on one shared silhouette: Mountains is the
Alps, the Pyrenees, the Carpathians and the Scandes; History is almost the
whole continent; and the difference between those two shapes is the argument
the tile exists to make. A journey draws its route, which is the one thing an
abstract plate could never show and the same finding that rebuilt `/journeys`.
**All of them and never a selection** — the count on the tile is the number of
dots on it, so a reader can check, and picking "the twelve best mountain
destinations" would be a ranking this atlas does not hold.
`weight.home_kb` 119 → 146, recorded: the plates cost 14.7 KB and came out,
894 dots and one lod0 coastline went in.

**And then the tiles became the four doors, and the doors carry NO drawing.**
That is the later decision and this paragraph is the earlier one: a lead door
carrying its own constellation was better than type alone and still wrong,
because it is a fifth picture of Europe on a page that opens on the largest
one on the site. Each door is a panel of the atlas's own water with a
photograph slot, one per door, so the strip composes as slots fill rather
than only when all four are licensed. `weight.home_kb` is back to 122.

**A slot waiting for a picture is honest; three hundred pixels of it is a
hole.** The panel was sized at 58vh, which is a photograph's height, and
measured on the built page that is about 300 pixels of flat teal above 230
pixels of words, four across, on the homepage's second screen. It is sized
to its content until there is a photograph, and `.shot` puts the full height
back.

**The same move fixed the index this session had already got wrong.** `/themes`
went from a card grid to rows, which traded one default for another — a
contact sheet of twelve families showed it as one of two cells that were simply
grey text. Each row draws its own eight places now, so a knot over Italy and a
line from Iceland to the Caucasus are told apart before a word is read.

**A contact sheet is what makes "every page looks the same" arguable.**
Eleven of twelve families open with a kicker, a serif h1, a lede and a large
arched map in the same position. The maps differ and the architecture does
not, which is the design-direction finding one level up from the h1 — and it
means the aperture has become the wallpaper its own rule warns about. The
tiles above are the first family answer that is not another arch: **a glyph,
not a window**, because eleven doors on one page is the signature as
wallpaper.

**And a selector cannot reach inside a `<use>`.** Cloned content lives in a
shadow tree, so `.constel path` matched nothing and the continent painted at
the SVG default — black, with the lit points invisible inside a blob. Second
time this repository has hit that trap; the escape is the same both times,
**paint by inheritance**: `fill` on the container is inherited through the
clone, and the lit dots are real DOM and override it. Two more of the same
class in the same hour: `geo.landmass` writes `context` and `atlas`, not
`countries`, so a rule reaching for the wrong class matched nothing; and
`.row` is baseline-aligned, which strands a 100px drawing at the top of its
cell. **The dead-rule scan caught the leftovers within one run** — a duplicate
`.themerow .rowmeta` declared 2,800 lines from its twin, and a redundant
`display: block`.

**`immutable` IS A PROMISE ABOUT THE URL, AND THE STYLESHEET'S URL COULD
CHANGE.** `/assets/(.*)` is served `public, max-age=31536000, immutable`.
That is correct for the social cards, whose filenames ARE their content hash
— that is what earns the header. The stylesheet and the five scripts sat at
a **stable** path under the same rule, and `immutable` tells a browser never
to revalidate for a year. So every returning reader kept the stylesheet they
first downloaded, and every visual change this site has ever shipped reached
new visitors only.

It is invisible from inside: repository correct, build correct, shipped HTML
correct, served page styled by a file from months ago. **That is the
`site/_headers` bug again** — right in the repo, wrong in the response — and
it is how a whole session of visual work can land and look like nothing was
fixed. It was found by being told nothing had changed and checking the
response rather than the repository.

The fix is the one the og cards already used: **the content hash goes in the
name**, and only the hashed name is published, because publishing both leaves
the stale URL live and cached forever. `checks.py` now asserts that nothing
under a directory served `immutable` sits at a URL that can change — from
both ends, the published files and the pages that reference them — and its
first pattern only recognised `name.<hash>.ext` and reported all 785 correctly
addressed cards as failures, which is an instrument that does not recognise
the good case it was written to protect.

**Four assertions broke on it, every one pinning a URL rather than a
promise** — two audits matching the literal `/assets/js/*.js`, the browser
suite fetching the planner by path, and the dead-rule scanner finding its
stylesheet by exact filename. **The scanner's own reach assertion caught
it**: "examined only 0 rules — it has stopped walking the stylesheet". That
assertion exists because its first version reported clean while collecting
nothing, and this is the second time it has paid for itself.

**The photograph pipeline would have failed the build on photograph number
one.** `picture()` emitted `style="--fx:40%;--fy:30%"` for the focal point,
and `checks.py` refuses any `style="` attribute anywhere, because CSP hashes
do not apply to style attributes and one would force `style-src` open on every
page. Built, enforced, waiting — and contradicting itself, written by the same
hand that wrote the refusal. **It survived because the register is empty: a
code path nothing exercises is a code path nothing checks.** The focal point
is nine anchor classes now, which is what a photo editor reaches for anyway.

**Photographs got the gate the map data has had all along.**
`scripts/map/fetch.py` refuses to open a socket for a dataset with no licence
row. Photographs were enforced only at the OUTPUT — no published page may
reference a file with no register row — and nothing at all stood between
somebody with an API key and a download.
`docs/data-licenses/photo-providers.json` holds four questions per provider
and `scripts/images/acquire.py` refuses before the request until they are
answered: **may we self-host** (this site serves `img-src 'self' data:` and
refuses a third-party origin, so a hotlink-only provider needs a decision
about the security posture of every page, not a build step), **what exactly
must the credit say** (the renderer changes *before* the first fetch, not
after), **is a download ping required**, and **may acquisition be automated
at all**. `Pexels` and `Unsplash` were already valid licence values in the
schema before any of this.

**THE GATE DOES NOT ASK WHETHER ANYBODY KNOWS WHAT UNSPLASH ALLOWS. IT ASKS
FOR THE SENTENCE, AND FOR THE ARCHIVED PAGE IT WAS COPIED OUT OF.** A model's
recollection of a commercial API's terms is not evidence — it is a guess
wearing the clothes of one, and these terms change. So each fact is answered
with a `value`, a **verbatim `quote`**, and the `source` URL, and `checks.py`
asserts the quote **appears in the archived snapshot of that page**. An answer
typed from memory fails the build, because the evidence has to exist in the
repository beside it and has to match. Proved four ways, including the one
that matters: a quote that is not in the page it cites.

`scripts/images/verify_provider.py` fetches every terms URL, archives it with
the date and the SHA-256 of the bytes as served, and prints the passages
mentioning hotlinking, attribution and downloads. **It answers nothing** — a
model summarising a licence page is the same failure as a model remembering
one, one step further from the source. It fetches, archives and points.

**It cannot run here, and that was confirmed rather than assumed**: the egress
proxy returns 403 for pexels.com and unsplash.com, tried directly. The
`photograph` workflow has network access and does it there.

**And the suspicion about Unsplash stays a suspicion.** There is a note on
record that their guidelines may require hotlinking, dual attribution with
links, and a download event. It lives in the gate file marked as a suspicion,
so somebody knows what to look for, and the check will not let it become an
answer without the quote behind it.

**THE GATE IS ON THE ROUTE, NOT ON THE PROVIDER, and collapsing the two cost
a correct provider a wrong refusal.** An image licence permitting free
commercial use says nothing about whether the *API terms* permit automated
acquisition followed by self-hosting, and for Unsplash the two have opposite
answers: the licence clears the use, the API guidelines require the hotlinked
`photo.urls` and a download event, which would open `img-src` on all 1,033
pages to a host we do not control. So `self_host` reads the LICENCE,
`api_route` reads the API guidelines, `automated_acquisition` is a field of
its own, and Unsplash enters by hand or not at all. Pexels clears every route.
**Answered is not permitted either** — the gate's first version failed the
build on any `self_host` that was not true, which turns "we read the terms and
they forbid this" into a red run forever.

**Discovery lists and stops; acquisition takes an ID.** They are two stages of
the workflow rather than two flags on one command, because they are two
decisions. `discover.py` prints the photographer, the native width, the page
and whether each candidate meets its purpose, and **names no winner** — a
photograph chosen from a filename is a photograph nobody looked at, and this
is the family whose entire argument for buying one is that it does a job the
drawing cannot. `acquire.py` takes one approved id, fetches it **by id**, and
asserts the id it got back is the id it asked for.

**The previous design took a search result by POSITION** — `--pick 3` — so the
picture a person approved and the picture that arrived could differ silently
while every provenance field was correctly recorded about the wrong one. A
position is not an identity, and a search result is not stable. If the id
cannot be retrieved the workflow fails; it never substitutes another
photograph, because a substitute is a picture nobody chose wearing correct
provenance.

**THE STEP BETWEEN DISCOVERY AND ACQUISITION IS A PERSON LOOKING, AND THE
FIRST VERSION HAD NO ARTEFACT FOR IT.** Discovery printed ids, photographers,
pages and pixel sizes, which answers what is *available* and cannot answer the
only question that decides an iconic hero from a competent one: does this
photograph work in THIS composition. The hero is a picture seen through an
elliptical arch cut into a limestone wall, with the cobalt masthead sitting on
its top edge, a 60px serif headline and a lede over its lower half behind a
scrim, and a form under that — and two of the picture's corners are removed by
the aperture. A provider's grid of rectangles shows none of it.

So the phase is:

    discover → contact sheet → A PERSON LOOKS → exact photo id →
    automated acquisition → PR carrying the rendered page →
    a person looks again → merge

`contact_sheet.py` renders **the actual page** once per candidate —
`pages.home()`, the shipped stylesheet, the same `arch_path()` — and
`hero-sheet.js` puts them in one image at 1280, at 390 and in the dark
preference. **The single substitution is the delivery ladder**, because a
preview is one JPEG where `picture()` emits AVIF, WebP and JPEG at five
widths, and that transform counts what it removed rather than assuming it: two
`<source>` elements and one `<img>`, or it stops.

**The sheet's first run cropped away its own subject.** Shooting the
`.herofull` element gives the photograph inside its aperture and removes the
masthead and the wall — so *is there anywhere for the masthead to sit* was the
question it existed to answer and the one thing out of frame. It shoots the
VIEWPORT now: an invented pad is a number nobody can check, and the viewport
is the reader's own frame.

**And it ranks nothing, deliberately.** The order is the provider's search
order and the sheet prints that on its face; no score, no sort, no highlighted
cell, no default — position is exactly what `--pick 3` got wrong. A candidate
`acquire.py` would refuse is left OFF and named, because art-directing a
photograph you cannot have wastes the one step that needs a person.

**A preview is never the acquisition.** Those bytes are somebody else's
photographs with no register row, no hash and no date, which is what the
licence gate refuses; they go to an ignored `.cache/`, leave as a workflow
artifact, and `checks.py` asserts from the other end that the repository holds
none of them and that the ignore rules are still there. The acquisition
fetches `original` by id and hashes that.

**A search cache keyed on the question hands back answers from somewhere
else.** `discover.py` cached on query, orientation and page size and not on
the endpoint — but the URLs inside a search result point at the provider that
answered it, so a cached payload outlived the host that served it. Invisible
in normal use, where the base never moves; immediate in the tests, where every
run gets a new port, which is the only reason it was found.

**And the test that asserted "no winner" read its own prose.** It searched the
whole manifest for "recommend", and the note explaining that nothing here is
*chosen, recommended or scored* was itself the match. Same class as the
invariant register counting a font size that existed only in a comment about
not adding font sizes: an instrument that cannot tell code from the
documentation of code. It reads the data now and the note is excluded.

**A purpose is declared before a photograph exists.**
`data/image-purposes.json` names the surface, the register key, the page, and
the native width, orientation and aspect a photograph must have to do that
job. `acquire.py` refuses an undeclared purpose and a photograph that misses
it; the validator refuses a row whose purpose is unknown and two rows claiming
the same one, so a hero cannot drift onto a destination page because it
happens to be in the register. `min_width` is **native** pixels rather than
the ladder's widest step — a 1,200-pixel original upscaled to 2,400 is the
same untruth as a population we estimated, and `derive.py` refuses to upscale.

**The original is kept and never overwritten.** `photographs/` holds the bytes
as served; the register's SHA-256 is of those bytes, which is what makes "this
file is the file that was licensed" checkable rather than a sentence.
Derivatives carry that hash in their names, so they sit at a URL that cannot
change — which is what the `immutable` header on `/assets/` promises, and the
lesson the stylesheet already taught this repository.

**The pull request is the approval boundary, so it is generated from the
register rather than typed.** `pr_body.py` reads the row the acquisition
wrote — photographer, licence, source page, both hashes, every derivative — so
the PR cannot describe a photograph other than the one committed. Keys come
from the environment, are never printed, and a check greps the committed files
for anything credential-shaped; the workflow runs that grep again before it
commits.

**A PHOTOGRAPH REPLACES THE DRAWING; IT DOES NOT SIT BEHIND IT.** The first
render put both on the homepage — the continent drawn over the picture, the
picture showing through every gap in the coastline — and every count was
correct. The stylesheet had already decided it before the drawn hero existed:
`.shot` is added only when the register holds the file, and the ground below
is what a reader sees until then. The drawing is the interim answer to an
empty register and a good one; it is not a layer under a photograph. **And the
note under it describes what is actually there**, because "the continent above
is drawn from Natural Earth" over a photograph is the `/map` failure on the
one page that opens the site.

**The derivatives were acquired, hashed, registered, referenced — and never
copied into `site/`.** `build.py` copies `assets/` and `assets/img` was not in
the list, so the hero was a 1280×736 hole: `<picture>` does not fall back once
a `<source>` matches, and a matching `<source>` pointing at a 404 renders
nothing. Every gate was green, because not one of them fetched a URL a page
had asked for.

**And two CSS rules for the photograph were dead the whole time.** `picture {
display: block }` and `.herofull picture { display: block }` were written for
a code path the empty register never ran; the dead-rule scan found them within
one run of a photograph actually rendering. **A code path nothing exercises is
a code path nothing checks** — the same reason the focal point shipped as a
`style="` attribute the CSP forbids.

**A line break defeated the projection check, on the homepage, for the life of
the drawn hero.** `c_published_projection` requires a page that names a
Lambert conformal conic to state its four angles in the same sentence. The
homepage named it and printed no angle at all, and the check never fired,
because the generated paragraph wrapped between "conformal" and "conic" and
the substring was not there to find. Whitespace is collapsed before the search
now, and the homepage states the angles from `geo`'s own constants. **An
instrument a line break can defeat is reading the file rather than the
claim**, and the claim is what a reader gets.

**NO EXTERNAL LICENCE CLAIM ENTERS PRODUCTION FROM MEMORY. EVERY EXTERNALLY
GOVERNED ASSET REQUIRES SOURCE + DATE + EVIDENCE.** One rule, stated once,
applied to every class — a map dataset, an elevation tile, a photograph:

| | |
|---|---|
| source | the URL it came from |
| date | when it was taken, because **a licence is a claim about a moment and without the moment it is a claim about nothing** |
| evidence | the SHA-256 of the bytes as served, so the file here is provably the file that was licensed |

The map datasets have carried all three since the map was built — `url`,
`fetched`, `sha256`. **Photographs carried five fields and not one was a date
or a hash**, so a row could say "Pexels-licensed" with nothing recording when
that was true or what bytes it was true of. That asymmetry is gone, and
`checks.py` also fails on a register in `docs/data-licenses/` that the rule
does not know about — a class governed by nothing is the failure the rule
cannot otherwise see.

**The field names came from the sister repository and the answers did not.**
It holds 629 photographs (595 Pexels, 34 Unsplash), self-hosted, each with a
photographer, a profile URL, a source page, a licence name and URL, a SHA-256
and four timestamps — a proven shape, worth copying wholesale. But it records
the licence *URL* without archiving what that page said on the day, so it has
source and date and only half the evidence. **A precedent in another
repository is a claim, not evidence**, and copying one is precisely what this
rule exists to stop.

**Design to purpose, not to data shape.** A page's structure comes from what
the reader is trying to do, not from the shape of the record behind it. The
experience template renders six rows because the data is six rows, and that is
the wrong reason for a layout to exist.

**Three roles, and every page head has one.** Twenty-one of twenty-two
families placed a 60px h1 at y=164 or y=212, and the only one that differed
had a hero. The roles are what the reader is *doing*, not decoration:

| role | it is | the head |
|---|---|---|
| `overture` | one thing | narrow measure, air above; the name is the event |
| `index` | a set | the extent sits *beside* the name; the set starts sooner |
| `instrument` | a tool | a label at section weight, on its kicker's line |

Measured after: 30px at y=136 for an instrument, 60px at 164 across 574 for
an index, 60px at 212 across 420 for an overture — and an index's set starts
at 347 where it used to start at 538. **None of the three adds a type
size**; a seventeenth was refused twice, and a role that needs a new scale
value is a decoration. `checks.py` requires exactly one role per head and
names the prose pages that have none, **so a new page cannot join the
twenty-one by accident** — which is how they got there.

**A shared template is not a shared experience.** One shell, one stylesheet
and eleven primitives are an engineering achievement and are kept. They are
not, by themselves, a design. Measured across twelve rendered families:
**eleven of the twelve place an identically-sized h1 at an identical vertical
position**, and the entire art-directional difference between a magazine story
and a country encyclopedia is one 11px kicker changing hue — terracotta on
`area-stories`, cobalt on `area-countries`. The accent system is not broken; it
is doing almost no work. See `docs/design-direction-audit.md`.

**Look to find, count to conclude.** A contact sheet of forty plates suggested
skylines were about 38% of them; measured across every destination they are
28%. The sample was biased and the eye was wrong. The same sheet *did* find
three real defects no amount of code-reading would have — including a moon
drawn behind a skyline and clipped into an unreadable glyph. Rendering finds
defects; counting settles proportions.

**Seventeen interest pages carried 728 abstract plates and the quiet index
carried 130.** That is forty-three hash-drawn landscapes in a column on the
average interest page, and a hundred and thirty in a grid directly under a map
whose whole argument is WHERE those places are — the measurement that emptied
the homepage, `/journeys`, `/europe-in` and the stories index, still shipping
on the family that had the most of it. A destination on those pages is chosen
on where it is and what it is like, and neither of those is a LOOK, which is
the test a card has to pass. They are rows now, and the WHOLE set: the interest
list used to stop at sixty with one sentence admitting it, and a row is cheap
enough that there is no longer a reason to stop. Each interest page opens on
its own tag drawn instead — every destination carrying it, unframed, so the
seventeen can be compared. **`docs/signature-moments.md` refused a map on this
family** on the grounds that the three largest tags would draw three identical
maps of Europe: true of History, Food and Architecture, and exactly what the
page already says in words, so the drawing agrees with the sentence rather than
contradicting it. The refusal was about the DOOR, and it still holds — this is
a glyph. Half the abstract plates on the site came off in one pass;
`docs/gap-assessment.md` carries the before and the after.

**The line is density, not the plate.** What remains is about four on a country
page and five on a month or macro page: four cards in a grid of
like things is the case a card was designed for. The measured failure has
always been eleven in a column or forty-three on a page, and the line moves the
day photographs exist for destinations rather than before.

**`docs/gap-assessment.md` is the standing answer to "what is left".** Written
from the site's own instruments rather than from opinion, and it says the thing
worth repeating: the engineering is finished and the content is a third
written, so almost every remaining gap is a photograph nobody has licensed or a
page nobody has written, and neither is solvable by more code.

**The four open decisions are answered, and each carries its trigger.**
`docs/gap-assessment.md` §4 and `docs/EUROPEDOOR_2036_TRANSFORMATION.md`.
Next.js and Postgres: **no**, until a write arrives from somebody who is not
us. Photography budget: **zero**, and the reason is the shape of what is
declared rather than thrift — eleven of the twelve declared purposes are
generic European scenes BY DESIGN and free stock covers every one of them,
while the set free stock cannot cover has no purpose declared for it. **The
premise of that question was right and the inference was wrong**: free stock
will never cover Theth, and nothing on this site asks it to. What to license
first: **the four homepage doors**, not the hero, because the drawn hero is
the one thing here no competitor can reproduce and a licensed stock
photograph is by definition a thing anyone can also license.

**A CONTRAST RATIO MEASURED AGAINST A TOKEN IS NOT THE RATIO A READER
GETS.** Every contrast assertion on this site read a declared colour against
a declared background, and the hero has neither: its type sits on a drawing
of Europe, so the ratio varies letter by letter. The stylesheet's own
figures — 7.7:1 bare, 6.9:1 on the lightest pool — are real and were measured
against the **water**, before the continent was drawn over it. The standfirst
runs across the lit parchment of Iberia and measured **4.36:1**, under the
4.5 AA floor, on the most-seen page on the site.

Worse, the scrim that exists to stop exactly this was `.herofull.shot::after`
— **gated on a photograph the register does not hold**, so the comment saying
"a scrim is what makes the contrast ratio a property of the design rather
than of the picture" sat on a rule no reader has ever had applied. A
bottom-left wash, ungated, six stops: 4.36 → 7.76 for the standfirst, 7.04 →
9.58 for the headline, and the continent stays luminous where there is no
type. Its first version painted at `z-index: -1`, **under** `.heroeurope` —
the sea behind the type darkened and the lit parchment, the only place the
ratio failed, did not move by one value.

**Measure where the glyphs are, not where the box is.** The instrument shoots
the page twice, with the type and without, and a pixel that differs is a
pixel a glyph paints. Scanning the RECTANGLE instead reported 2.15:1 against
a real 9.58, because an h1's measure is 14ch and the headline does not fill
it, so the bright parchment in the gutter past the last letter was read as a
failure of the type. The check counts the glyph pixels it found, because a
diff that finds none reports infinity and passes.

**A role is a claim about the markup under it.** The planner's add-a-stop
results were a `<ul role="listbox">` whose `<li>` children carried no role at
all, so assistive technology was told there was a listbox, asked for its
options and got none, while eight real buttons sat on the screen — and the
at-rest line was itself an `<li>` inside it. A plain list now, with the
sentence that CHANGES moved into a `role="status"` line, which is where a
change is heard. **And a disclosure that takes focus has to give it back**:
the panel focused its search box on open and had no keyboard exit at all.

**"In the list below" was a claim about the page around the sentence.**
`offframe_line()` ended that way unconditionally — true of the three callers
that print their own set, false on the 404, whose drawing IS the body. That
is the journey caption promising "a note under the leg" after the note was
removed, one family over. A shared function cannot know what follows it, so
the caller says. The check written for it **sliced the page at the first
`</header>`, which is the masthead's**, so the "below" it examined contained
the sentence's own words and it reported clean on the page it was written
for; fixed, it immediately found a second instance on `/experiences`, which
plots every place with an experience and lists twenty-four of the 197. Then
it went red on the HTML **comment** recording why — the third time an
instrument here has read the documentation of code as code.

**A separator belongs to the relationship, not to the element.** The index
hero drew its own bottom rule: right on twenty-one families, and on the 404 a
hairline across the column followed by two hundred and seventy pixels of
nothing above the footer — the one page a reader reaches having already
failed to find something. Nothing counts an empty band. The check for it was
itself pinning a shape on its first run, flagging `/map`'s bordered list: a
panel has a bottom border because it has four, and its fourth side separates
nothing. **A divider is a bottom edge and three bare ones.**

**THE PICTURES WERE GIVEN A CARTOGRAPHY AND THE INSTRUMENTS WERE NOT.**
`docs/cartography.md` splits every drawing on what it IS — a picture is
paper, an instrument is graphite — and the picture half got a four-step
ocean, a land family, an ink coast and a lit subject, every one measured.
The instrument half kept five raw hexes invented before European Future:
`#0a1220`, `#253546`, `#1b2735`, `#4a6480`, `#3a6299`. Navy rather than
graphite, in no token, recomputed by nothing. Land against water measured
**7.91 on the pictures and 1.50 on `/map`**, and a country outside the
subject measured **1.24**, which is not a quiet country but a country that
is not drawn — and the stylesheet already *stated* the 1.50, forty lines
from the tokens that produced it. The fix is the hero's own sentence applied
to the instrument: **Europe is what the light falls on.** `docs/palette.json`
carries a `cartography` block whose rows are **separations** rather than
claims — a claim says a colour may carry TEXT, these say two drawn areas must
be distinguishable — recomputed from the hexes in the stylesheet, and the
five navy hexes are refused by name the way the gold and the lime are.

**And the subject of a drawing is not painted in the accent.** Binding the
selected state to cobalt-air was right for `/map`, where hover lifts one
country under the cursor. The same token filled the subject *permanently* on
the fifty country reference maps, so Italy came out a quarter of the drawing
in periwinkle — a continent drawn in the accent, which is the failure that
removed electric lime, arriving through a different token one commit after
that token changed. Self-inflicted, and only rendering a country page found
it: every separation was green, because the register asked whether the
subject clears its neighbours and not what the subject IS.

**A `<use>` clone takes whatever matches the ORIGINAL in its own position,
and inherits from the `<use>` only what nothing else has claimed.** This
repository held two contradictory records of that — the cartography note says
a selector reaches in, the constellation note says it cannot. Both describe
the same rule from opposite sides. Settled with a two-case probe: a clone
paints red when the source is inside the scoping class, green when the source
sits in a `<defs>` outside it.

**Colour is more than luminance, and every instrument here measured only
luminance.** Three separate defects, none of which a contrast ratio can see:

- **The hypsometric ramp swung 27° of hue and peaked in saturation at its
  middle** — 64° yellow-*green* at the bottom, 35% saturation at 600–1200 m —
  on a file whose own comment says "the land tone at the bottom" and "warm as
  it rises, and never saturated". A reader saw a green lowland, a yellow
  foothill and a tan upland: three materials, where the thing drawn is one
  ground at three heights. One warm family now, 42° → 35°, lightness carrying
  the height, and the mixed steps came out *better* separated as well as
  cleaner.
- **The ocean drifted toward cyan-green as it lightened**, 200° → 185°, with
  the deep at 65% saturation — the most saturated colour in the atlas,
  covering the whole Atlantic. Khaki against teal is the muddiest pair
  available and it was the whole look. One hue, 205° → 202°, saturation
  *falling* toward the shore.
- **The advisory red and the cultural accent were the same colour.** `#a32a1e`
  and `#a4491f`: fourteen degrees apart at identical saturation and identical
  lightness, which measures **1.22:1**. A contrast ratio is a ratio of
  luminances, so two hues at the same lightness always measure 1.0 and every
  check here passed. `docs/palette.json` carries a `distinct` block now — pairs
  that must be told apart, and the minimum circular **hue distance** between
  them.

**A step that measures 1.045 is a rounding error with a token name.** The
light world's surfaces step 1.09 and 1.12; the dark world's stepped 1.12 and
then 1.045, so `--paper-3` was the card with a different name and every track,
score bar and hopbar on a dark card was drawn on its own colour. The reason is
the interesting half: `graphite-3` was sized so `cobalt-lift` would clear AA
on it — **a claim about the link colour deciding the size of a surface.** The
step is real now and the link colour moved to keep its claim, which is the
right way round. The register asserts the **steps** rather than the rungs: a
claim about a rung cannot say anything about a ladder.

**An accent on every row of a list is not an accent, it is a texture.** The
kicker says what KIND of thing is being read — one per page head answers that;
inside a row it answers nothing, because every row is the same kind.
Seventeen cobalt uppercase lines down `/journeys`, thirteen down `/themes`.
That is aperture-as-wallpaper arriving in colour, and on `/themes` it inverted
the hierarchy it sat in: the kicker is the theme's *argument* and the h3 is
its name, so the brightest thing in every row was the subtitle.

**Four premium defects that were all "nobody decided".**

| | |
|---|---|
| prose links | no `text-underline-offset` anywhere, so every page on the site drew a rule through every descender |
| the footer | `main` pads its bottom by `--s9` and the footer added another: **224 pixels** of empty page above the band, on every page |
| a row's subline | `p { max-width }` broke a middot list of place names at 544 px inside a 948 px column. A measure is for prose; a list is a sequence and you scan it |
| the theme glyphs | 132 px for the whole of Europe, on the page whose closing sentence is *"a knot is an argument about one corner of Europe, a scatter is one about the whole of it"* |

**And the search box was the page, in a card.** Border, fill, radius and
shadow each say "separate object, placed here by a system", and saying it
about the one control a page exists to be is the wrong sentence. Its help line
started at the exact pixel the input's box ended, and four of the seven bars
under it — journeys, themes, stories, fund projects — rendered between 2.4 and
4 pixels wide, because the extent is a share of 319 on an 80-pixel track. **A
chart on which four of seven series cannot be seen is the wrong track, not the
wrong data.**

**A `<stop>` that no rule reaches is black, and the SVG default is the one
colour this palette does not contain.** `datacut()` emitted its two gradients
in a `<defs>` BESIDE the group rather than inside it, so
`.minimap.arched.atlas .datacut stop` matched none of the ten stops on any
page — and the ramp that exists to stop a straight data cut reading as a
rendering fault was itself a black smear at the eastern edge of the parchment,
on every picture plate the site draws. It survived because the gradient is anchored at 52°E and most
plates are framed hundreds of units west of it, at zero opacity: invisible on
three hundred pages and plain on the twenty framed on the whole continent.
Nothing counts a gradient stop; the browser's computed value is the only
instrument that could have seen it.

**A FADE WRITTEN TO KEEP A PICTURE HONEST WAS UNLIGHTING THE ATLAS.**
`data/geo/` stops at 52°E and 33°N, so the hero ramps into shadow along each
cut. The widths of those ramps — 360 units east, 150 south — were chosen by
eye for atmosphere, and nothing ever asked what was underneath them:

| | | | |
|---|---|---|---|
| Baku | 100% | Paphos | 92% |
| Tbilisi | 89% | Heraklion | 85% |
| Moscow | 71% | Chania, Crete | 83% |
| Helsinki | 28% | Valletta | 77% |

**Forty-six of 319 destinations were dimmed past half**, and five countries —
Azerbaijan, Georgia, Armenia, Cyprus and Malta — were effectively unlit on a
picture whose own accessible label says every country is a link. It is the
fault `cartography.datacut` already records one file over, in the family that
learned it. `pages.dusk_reach()` derives the widths from the outermost
destination east and south, inverting smoothstep in closed form, so adding a
destination further out narrows the fade on the next build. The ceiling is the
one number here that is art direction and it was **rendered three ways and
looked at**: at 0.50 the band is 52 units and the terminator reads as a hard
shadow cutting the continent — the same rendering fault, arrived at from the
other side. 46 past half becomes 9. **/map takes none of it**: its marks are
drawn ABOVE the fade so a destination near the cut keeps its dot, and
narrowing it made the 52°E diagonal a hard edge on the instrument.

**The subject of every country portrait was drawn cold, and only a pixel
sample found it.** `path.here` was a translucent white — "a wash, not a fill,
so whatever is under it survives" — written on the premise that the land tone
is underneath. On a portrait there is no land underneath: `lyr-ocean` is a
rect of `--atlas-sea` across the whole frame and the subject is painted once,
with this fill. So 62% white sat on `#153851`: **Austria rendered `#ccd9e1`
and its neighbours `#d3cfc5`** — a cold blue-grey country in a warm parchment
frame, on all fifty portraits, reading as water. At thumbnail size it looks
like a slightly lighter country, which is why no contact sheet found it.
Opaque `--atlas-here`, the token that existed for exactly this and had no
user, and both steps are separations in `docs/palette.json` now.

**Nine portraits set their country's name on somebody else's ground.** The
hero has three rules for placing a country name and the portrait had none of
them: its anchors were offsets of a radius round the centre of the subject's
bounding box, tested against the aperture and the labels already down and
nothing else. Measured with the browser's own `isPointInFill`, **AUSTRIA,
DENMARK and FRANCE were ten samples out of ten on a neighbour** — AUSTRIA set
across Czechia on the one plate whose job is to say which country this page
is about. `pages.NameGround` is the hero's rule at module level, because
**there are two drawings that name countries and for the life of both only
one had the rule.**

**And a bounding box is not a country came back through the ANCHORS.** The
moment the name had to sit on its own ground, ITALY, NORWAY and SPAIN lost
theirs — Italy's bounding-box centre is in the Adriatic and its radius is half
the peninsula, so not one of the nine anchors was on Italy. The anchors are a
grid over the box keeping the cells inside the real polygon, ordered from the
middle outwards and **not truncated**: keeping the seventy nearest the middle
cost NORWAY its name, because the cells near the centre of Norway's box are
all in the crowded south. Three rungs — zero crossings, two, five — because a
portrait that cannot name its subject is worse than a name whose end overlaps
a neighbour. 43 of 43 named, none off its own ground.

**A `.pyc` outlived its source, and a sweep of a constant reported the same
number four times.** `DUSK_CEILING` was edited and re-imported three times and
every run printed the value from a stale `__pycache__`, while `inspect.getsource`
— which reads the FILE — showed the new code. `python3 -B` does not help: it
stops Python WRITING bytecode, not reading it. Delete `tools/**/__pycache__`
before measuring a constant you have just changed, or the measurement is of
the last build.

**The browser suite crashed mid-run because `site/` was rebuilt under it.**
`ENOENT: site/404.html`, the same concurrency failure this file already
records as a green run that had stopped counting. Do not build while the
browser suite is running; it takes half an hour and the rebuild takes thirty
seconds.

**AN UNRESOLVABLE `var()` IS NOT A MISSING VALUE, IT IS A DIFFERENT ONE.**
The whole declaration is invalid at computed-value time and the property takes
its INHERITED value. Two tokens were being referenced and had never been
declared. **`--serif` has never existed** — the token is `--display` — and
twelve rules asked for it; nine of those sit on an h1/h2/h3 that
`h1, h2, h3, h4 { font-family: var(--display) }` had already set correctly, so
those rules **actively replaced the right value with an invalid one** and the
heading fell back to the sans body face: the index hero h1 on five indexes,
the journey rows, the story lead on `/stories` and on the homepage, the four
doors and their waylines, the closing statement. The display serif is the
whole voice of this product and it was absent from most of the largest
headings on the site. And **`--atlantic-lift`** was referenced by
`--provenance` inside both dark blocks, so the heritage rule down the side of
843 provenance panels painted limestone — the text colour — in the dark
preference and across the whole INTELLIGENCE world. Neither is visible to a
check that counts declarations, to the dead-rule scan (the rule matches and
does change something: it changes the font to the wrong one), or to any
contrast assertion, because those read tokens rather than the pixels a
heading is painted in.

**The palette register and the stylesheet had never been compared.**
`docs/palette.json` declares eighteen tokens with a hex each and every claim,
forbidden pair and cartographic separation is recomputed from those hexes —
and deleting `--ultramarine` from the stylesheet entirely left the whole suite
green. The register went on asserting a contrast for a colour the site no
longer had. `checks.py` reads both directions now: every token's hex must be
in the stylesheet by name or by value, and **every custom property the
stylesheet declares must be spent by some rule**, which is the dead-rule
scan's finding one level up. Three were dead — `--atlas-context` (identical to
`--atlas-land`), `--shadow` (declared in all three world blocks, referenced by
none), and `--ultramarine`, which is real in this product as the violet end of
the PLATE ramp and was never a page colour.

**THE RATIO WAS THE INSTRUCTION AND NOTHING HAD EVER MEASURED IT.** 60
limestone, 25 graphite, 10 cobalt, 5 accent — and the only assertion on it was
that the four numbers add to 100. Measured on the pixels a reader is painted,
over twelve pages spanning both worlds and six families:

| | measured | declared |
|---|---|---|
| limestone | 64.2% | 60 |
| graphite | 18.9% | 25 |
| cobalt | 16.6% | 10 |
| accent | **0.3%** | 5 |

Three say the instruction is being followed. The fourth does not: terracotta
and atlantic are the entire art-directional difference between a magazine
story and a country encyclopedia, and they are spent on an 11px kicker.
**Classified by CHROMA rather than by HSL saturation** — limestone is `#f7f6f3`
and HSL calls that 20% saturated, so the first version counted the paper as an
accent and reported the site 60% terracotta.

**The interactive colour was edging 465 panels about what we refuse.** The
provenance pass gave the heritage rule to five call sites and left the rest on
`--sea`: 445 destination pages saying we list neither hotels nor restaurants,
130 region pages, seventeen interest pages. Every one except "Build this into
a route" is a statement about what this atlas holds, refuses to hold, or has
not built. **The default is the common case now** — a note is provenance
unless it says otherwise, `.onward` is the one that hands a reader somewhere
and keeps the interactive colour, `.warn` keeps the tinted ground. `.sourced`
is gone rather than kept as a synonym for the default.

**KEYBOARD FOCUS WAS INVISIBLE ON THE NAVIGATION OF EVERY PAGE.** The ring is
`--sea` and sits three pixels OUTSIDE its link, which on every other surface
puts it on the page and on the masthead puts it on the band: **1.06:1**,
present, correctly placed, correctly sized and unseeable. It is the mark's own
finding one element over, and it takes the same answer — the thing inverts
rather than recolours, and limestone measures 6.70 on the band. The four
homepage doors already did this by hand. **A `--focus` token was tried and
refused**: `:root { --focus: var(--sea) }` resolves `--sea` where the
declaration lives, so every world inherits the light world's cobalt, which is
the `accent-color` bug one paragraph over. The check shoots the element's
neighbourhood twice, focused and not, and compares every pixel that changed —
because a focus ring has no declared background.

**A word cut in half is a rendering fault, and one family had it on 146
pages.** The destination page's sticky phone action carried the place name in
a flexed span with an ellipsis, and two buttons take 230 pixels of a 390-pixel
bar: 46% of destinations rendered a cut word, "Innsbr…" and "Gura Humorului &
the painted monasteries" 255 pixels over its slot. The name is also redundant
where it is not broken — the reader is on the page — so it moved into the
buttons' own accessible labels, which is where a screen reader needs it. The
check is general: no element anywhere may hold more text than it shows.

**The subject of every country portrait was drawn cold, and only a pixel
sample found it.** `path.here` was a translucent white written on the premise
that the land tone is underneath; on a portrait there is no land underneath,
only the sea rect, so 62% white sat on `#153851` and **Austria rendered
`#ccd9e1` against `#d3cfc5` neighbours** — a cold country in a warm frame, on
all fifty. At thumbnail size it looks like a slightly lighter country.

**Nine portraits set their country's name on somebody else's ground.** The
hero has three rules for that and the portrait had none of them.
`pages.NameGround` is the hero's rule at module level, because **there are two
drawings on this site that name countries and for the life of both only one
had the rule**. And *a bounding box is not a country* came back through the
ANCHORS: the moment the name had to sit on its own ground, ITALY, NORWAY and
SPAIN lost theirs, because Italy's bounding-box centre is in the Adriatic. The
anchors are a grid over the box keeping the cells inside the real polygon, and
**not truncated** — keeping the seventy nearest the middle cost NORWAY its
name, because the cells near the centre of Norway's box are all in the crowded
south.

**204 pixels for the whole of Europe, on the page whose subject is reach.**
`/themes` closes with "a knot is an argument about one corner of Europe, a
scatter is one about the whole of it" and drew it at 204 pixels, where eight
stops are four pixels apart. Now 18rem — and **the mark had to come down as
the drawing went up**, because a radius in viewBox units is a radius in pixels
at exactly one width: 22 units is 4.5 pixels at 204 and 10.5 at 480. The width
is capped by the page's own length rather than by taste: at 22rem the page ran
to 5,739 pixels, within fifty of the old stories index this repository threw
away for being 5,792.

**THE RATIO'S FIRST MEASUREMENT COUNTED THE SEA AS THE SIGNATURE.** Everything
blue went into one bucket and cobalt came back at 16.6% against a declared 10
— a finding about the masthead that was mostly the Atlantic. The families do
not overlap: the ocean ramp and the atlas water run 202–205° of hue and every
cobalt runs 228–230°. Split at 218:

| | measured | declared |
|---|---|---|
| limestone | 64.1% | 60 |
| graphite | 18.9% | 25 |
| water | 9.7% | unbudgeted |
| cobalt | **7.0%** | 10 |
| accent | 0.3% | 5 |

Cobalt sits UNDER its budget on all twelve pages and varies between six and
eight per cent — the masthead and the links, and almost nothing else. **The
correction matters more than the original reading**: the conclusion was that
the signature was overspent, and it is not. Water gets no line in the ratio
because it is the DRAWINGS rather than the interface, and a ceiling keeps that
true. The accent is the one number that still disagrees, and it stays recorded
rather than closed — making terracotta a ground is "generic tourism blue as a
page background" in a warmer hue.

**A LIST THAT IS THE PAGE STARTS AT h2, AND A SIXTH OF THE SITE STARTED AT
h3.** The
`row` shape carries its name in an `<h3>`, which is right inside a band where
the band's `<h2>` is the level above it — and wrong on every family where the
list IS the page: the facet pages, the theme pages, the motion pages, the
interest pages, the macro pages, `/method`, `/api-docs`, `/discover`,
`/stories`, `/themes` and three indexes. Nothing in WCAG fails on a skipped
level, which is why it survived every gate; what it costs is that a reader
navigating by heading hears "level three" with no level two above it. The
stylesheet already held this opinion for notes and rails. **The level is the
outline and the class is the look**, so the selectors are `:is(h2, h3)` and
`render.card()` takes a `level`. **And `main h2` started matching all of
them** — 32 pixels above and 16 below — so a change meant to move nothing
moved something on every one of them until the components stated their own
margins.

**THE ELECTRIC LIME WAS STILL ON NINETY-SIX SOCIAL CARDS.** A card is
content-addressed on the seed, the motif, the size and a **hand-typed version
tag**, and the tag is the only part of that key that notices a change to the
DRAWING — `render.og_key` says so, in a paragraph about the last time it was
forgotten. When lime left the palette it left the plate's night moon too, and
nothing produced a new filename: two stylesheet guards, a browser probe on the
painted colour and `css.lime` in the register, and **not one of them reads a
PNG**. #697d4b, 1,586 pixels, on 96 of 785. Found by building a contact sheet
of eight cards and seeing an olive disc in a palette with no green in it. The
build writes `assets/og/cards.json` now and `checks.py` re-renders a sample and
compares BYTES.

**The data cut ran raw through all 21 index openings**, which is the worst
surface for it: the ground behind those glyphs is the sea panel, so the cut is
a hard edge between parchment and deep navy. **And the defs were outside the
group again** — `cut_fade()` has the same shape `cartography.datacut()` had,
and stayed green only because `/map` colours its stops by ID rather than by
class. A second implementation of a thing is a second chance to make its
mistake.

**The terrain's top band went back the other way.** 2000 m+ was `#e8e6e3`,
"light stone", which is the convention for permanent ICE. Measured as the
plates draw them the ramp ran 1.081, 1.081, 1.084 and then **1.353 upwards**,
so the ground above 2,000 m measured **1.069 against the ground below 200**
and **1.207 against the page's own limestone** — the highest ground read as a
hole in the drawing. This DEM has no ice class, so the ramp runs the whole way
down and the Alps are the darkest ground rather than the lightest.

**Keyboard focus was invisible on the navigation of every page**, and the
**sticky phone action cut its own place name on 146 of 319 destinations**.
Both are in the same family of fault: a thing that is present, correctly
placed, correctly sized and unusable. The focus check shoots the element's
neighbourhood twice, focused and not, because a focus ring has no declared
background; the clipping check asserts that no element anywhere holds more
text than it shows.

**`tools/photo-tests.py` BUILDS THE SITE, and running it beside the browser
suite killed the suite.** It exercises the acquisition pipeline end to end
against a stub provider, which means it wipes and rebuilds `site/` — so the
suite's own server read `site/404.html` while the directory was being
recreated and the run died with ENOENT. That is the concurrency failure this
file already records twice, arriving through a gate nobody thinks of as a
build. **Run the browser suite alone.** It takes about forty minutes and
everything else here takes seconds; there is never a reason to overlap them.

**A floor that is one page away from its threshold is a check that fails
without saying anything.** The palette ratio's accent floor was 0.2% against a
measured 0.3, and the run reported "the accent paints 0.00%" and nothing about
where it went. Both halves were wrong: a site-wide share is the wrong quantity
for a colour that has a HOME — the families whose `--door` is terracotta or
atlantic — and a message carrying one aggregate number cannot be diagnosed.
Every page's figure is in the message now, which is the same rule the map-layer
failure was fixed by: *a failure message with no measurement in it cannot be
diagnosed.*

**AND THE RATIO'S CLASSIFIER LOST A BOUND WHEN IT WAS COMPRESSED.** Water is
185–218 degrees of hue and cobalt is 218–270; everything else — and everything
else is mostly the warm end, terracotta at 20 — is the accent. Written into
the suite as `h < 218 ? water : h <= 270 ? cobalt : accent`, the first clause
swallowed every warm hue on the site, so the run reported the accent at 0.00%
on all twelve pages while the prototype, which kept `h >= 185 &&`, reported
0.3. The numbers in `docs/palette.json` came from the prototype and are right;
the check was measuring something else for two runs. **A condition that is
correct in a prototype can lose a bound when it is compressed into a ternary**,
and the only reason this surfaced is that the failure message was made to print
every page's figure — twelve zeroes is a classifier fault and one zero is a
page fault.

**And a rule's reason can stop being true when the drawing changes.**
`.constel:not(.regionglyph) { display: none }` takes the glyph off a phone, and
its comment says a theme's constellation "is 132px inside a row and stays 132px
on a phone" — which was right while it WAS a 132-pixel mark. Once the row stated
its proportions and the drawing became 288, the phone case had become the case
the same block already makes an exception for, where a journey's route and a
story's places get the whole width. The reason had expired and the rule had not.

**A SEPARATION BETWEEN TWO TOKENS SAYS NOTHING ABOUT WHETHER EITHER IS
PAINTED.** `docs/palette.json` declares `--map-land` against `--map-sea` at
1.8 with the reason written out — *the land is a mass, not a hairline* — and
`checks.py` recomputes that from the hexes in the stylesheet, so it has been
green since the day it was written. **/discover drew all fifty countries with
`fill: none`**: unfilled outlines at one pixel on `#0b0e11` under 319 dots, a
wireframe continent on black, on the page whose whole job is to open one. The
rule was older than its only user — written for a homepage hero map that was
removed, where an outline WAS the look. Filling it then exposed the 52°E data
cut as a hard diagonal, which is why that map now draws a fade it never
needed: **with nothing filled, there was nothing to cut.** The browser suite
reads the painted fill now, not the token.

**THE SAME DEFECT TWICE, IN TWO COMPONENTS, BECAUSE ONE FIX DID NOT LOOK FOR
THE OTHER.** Below 44rem the masthead's seven sections were one line that
scrolled sideways and the rule's own comment called the mask fade "the
affordance saying so": measured at 390, 552px of content in a 366px box, so
**Plan, Stories and Events were wholly off-screen**, and at 320 Journeys was
too. The reasoning that put them there was right about five of the seven and
was applied to all seven — /discover, /plan and /my-europe are in the thumb
bar, which appears at *the same breakpoint*, so hiding those three hides
nothing. And `.sectionnav`, a destination's own contents row, did exactly the
same thing on every destination page: 567px in a 358px box, with Events, Travel tips, Stay
and Onward behind a swipe and no affordance at all. **A link a reader cannot
see is not reachable because it is focusable**, and the document-overflow
check passes on both by design, because overflow contained inside a scroller
is what that check was written to allow.

**The masthead sat on a 24px gutter and every word under it on 16.** `main`
is padded `--s4` on a phone and `.masthead-in` was left on the desk's `--s5`,
so the wordmark and the whole navigation were indented eight pixels further
than the h1, the breadcrumb and every line of prose, on every page. Nothing
counts a gutter and at thumbnail size nothing sees one.

**TWELVE PURPOSES WERE TWELVE SLOTS.** A surface, a page, a register key and
a minimum width answer where a photograph goes and not one word about what it
must be a picture OF — so the pipeline could have acquired a technically
perfect 2,400px landscape for the Mountains door that was a summit portrait,
passing every number and contradicting the door's own sentence. `roles` is
the vocabulary now and a purpose instantiates one: subject rule, crop rule,
brief, and the refusals that disqualify a candidate which passes every
number. Three roles have no purpose and each says why — two carry a trigger,
`accommodation` is refused on the Stay layer's licence position — because **a
role nothing reaches is a dead motif wearing the clothes of vocabulary.**

**THE HERO'S CROP BOX SWINGS 8.6x AND NOBODY HAD MEASURED IT.** Safe area is
arithmetic: a container narrower than its source crops width, a wider one
crops height, so the guaranteed frame is `container_min / source_max` by
`source_min / container_max`. Measured in Chromium by adding the class a
photograph would add and removing the drawing it would replace: the homepage
hero ran 0.435 to 3.720, which left **7% of a photograph's frame guaranteed
visible**. A slot that destroys whatever is put in it. A 43vw floor on the
hero's height caps it at 2.33 — which also fixed a thing a reader sees today,
because at 1920 the arch had stopped reading as a doorway — and the 2.6
aspect ceiling came down to 1.9. 7% to 15%. `checks.py` refuses a safe area
under 12% and the browser suite re-measures the boxes: **a layout change that
would have ruined the first four photographs anybody licenses now fails in
the commit that causes it.** It already has.

**AN INDEX OPENING THAT IS A CONTINENT WITH A DIFFERENT NUMBER OF DOTS ON IT
IS NOT A DIFFERENT OPENING.** Six were: /countries, /experiences, /stories,
/interests, /beyond-the-obvious and the 404, in the same arch in the same
position. At opening size 197 dots and 130 are the same picture. Two came
off, chosen because their subject is not a shape — a map answers WHERE, and
where earns the opening only where the subject IS one. /experiences was still
emitting the silhouette with nothing using it, 13,791 bytes, a third of the
page, and the coastline-credit check caught it in one run.

**/interests HAD NO INDEX AND NOTHING LINKED TO IT.** Seventeen pages shipped
and the directory autoindexed. A link checker validates links that exist, and
a missing index is an absence — which is also why it cost something invisible:
every interest page says it draws its tag "so the seventeen can be compared",
and there was nowhere they could be.

**THE COUNTRY PAGES WERE THE LAST GRID OF ABSTRACT PLATES, AND THE DENSITY
RULE WAS NOT THE QUESTION.** "Four cards in a grid of like things is the case
a card was designed for" kept six per page. What nobody had measured is
whether the six are six PICTURES: 207 cards across fifty pages drawing 146
motifs on their own page, and **France draws five skylines out of six**,
Belgium four of five, Bosnia and Herzegovina four towers out of four.
`plate-variation.py` cannot see it — it measures duplication across the
corpus and this is duplication on one screen. And the page draws the real
geography four hundred pixels above them.

**A CHART'S CAPTION NAMED A LINE THAT MEASURED 1.16:1.** The year band says
"above the line is what is on" and the axis was `--rule` — the hairline
between two list rows — sampled at rgb(231,230,223) against a page of
rgb(247,246,243). The two series measured 1.19 against *each other*: 150° of
hue apart, so a colour-sighted reader tells them apart instantly, which is
the `distinct` block's own trap. And **1px was not enough**: the band is
drawn `preserveAspectRatio="none"`, so a one-unit line does not land on a
device pixel and `--ink-2` at 1px sampled 2.59 while the token is far darker.
The ratio a reader gets is the ratio of the pixel.

**A COMMENT IN EMITTED MARKUP SHIPS.** A paragraph of reasoning went into the
homepage's HTML and the weight invariant caught it in one run. A reason
belongs in the source that writes the page — the same rule as a reason
belonging in `tools/invariants.py` rather than in the register it generates.
And an f-string cannot contain a comment at all, which is where that one was
trying to go.

**`data-rotate` HELD FOUR ALTERNATIVE PLACEHOLDERS AND NOTHING HAS EVER READ
IT.** The homepage loads no JavaScript — its only `<script>` is the inert
JSON-LD block — so 232 bytes of copy shipped on the most-visited page for the
life of the band, waiting for a rotator nobody wrote. **The dead-rule scan
does not read attributes.**

**THE GLYPH HAD THREE SIZES AND ONLY TWO WERE WRITTEN.** A desk rule at 64rem
and a phone rule at 44rem, and between them neither applies: at 834 the theme
and interest rows fell back to the drawing's intrinsic size, **a continent 132
pixels wide**. And the phone rule runs to 704, which is not a phone: a
full-width glyph at 600 made /interests 11,972 pixels tall. Two repairs failed
first and both are traps this file already records — a base rule later in the
file beat the 64rem block, and writing it at (0,3,0) beat the block at every
width. The third worked and **the invariant register refused it for adding a
seventh breakpoint**; a plain rule at the right specificity in the right place
does the same job and adds none.

**AND ONE THING WAS BUILT, RENDERED AND REMOVED.** The homepage's three
journey rows have no dominant element, so the first was given a 34rem column.
A route is FRAMED on its own extent — which is what makes each of the three a
picture of its own corner rather than three identical continents — and the
Arctic-to-Mediterranean extent is tall, so the wider column produced a
490-pixel picture beside 140 pixels of type and three hundred pixels of empty
row. **The thing that makes each one legible is what stops one of them being
the wide element.**

**A MAP CARD IS NOT 16:9, AND THE LETTERBOX WAS INVISIBLE BECAUSE IT WAS THE
SAME SEA.** `.card-art` is 16/9 because that is a *photograph's* proportion,
and every drawing ever put inside one is 1.282 — `constellation()` fits every
frame to 1000×780, so all 129 region minis, all 44 country glyphs and the
nine region tiles on `/discover` share it. The drawing therefore fits to the
box's HEIGHT and a third of its width is padding: at 1280 the tile is 345
wide and the continent is 231 of it, and **at 834 the whole of Europe renders
138 pixels wide** — two-thirds of the 204 that `/themes` already measured as
too small, on the page whose second band is *where a region is*. It survived
every gate because `.card-map` paints `--atlas-sea` and so does the drawing's
own ocean, so the wasted third reads as more sea rather than as a frame that
does not fit. **Nothing counts a letterbox, and the box was what every
measurement reported.**

**THE DRAWING ON `/discover` WAS DECORATION BESIDE A FORM.** 319 dots on
graphite under seventeen chips and four fields, and the picture did not
respond to the panel — the single most GIS-application surface in the
product, and a GIS application is the first thing the brief says EuropeDoor
must never feel like. The whole Atlas is already in the reader's browser and
`render()` already computed the matching set; the map was simply never told.
The join is the destination id, written on every dot as `data-city` and
carried by `/api/atlas.json` as `city.id`, declared in `data/contracts.json`
because it crosses a boundary — markup one side, an index the other, and a
renamed id would light nothing with no error anywhere. **A place that drops
out goes quiet, it does not go away**: the unlit dot takes the LAND's tone
rather than a dimmed accent, because a map that deleted its unlit places
would be a different Europe for every query. Advisory places are never lit,
and that falls out rather than being written — atlas.json is stripped of them
at build time.

**And the drawing had to stop MOVING when the reader picked.** It sat above
`#discover-results`, so the first choice pushed the one thing that had just
become meaningful off the screen. It sits between the control and the list
now, and the two counts were split because they are two claims: what the MAP
shows goes above it, what the LIST shows goes above the list. Moving it up
also left "Choose what you are travelling for" 950 pixels below the chips it
describes — the instrument-head rule broken by the commit applying it.

**`cell` CAUGHT `cellar`, SO `/experiences/faith/monasteries` WAS EIGHTEEN
WINE CELLARS, A LAMBIC BREWERY AND THREE DISTILLERIES.** A sub-category
keyword is matched as a bare prefix. `matches_sub`'s own docstring records
that failure for the CITY name and fixes it there — `hall` catching
Hallstatt, `snow` catching Snowdonia — and never asked whether the same
prefix was doing the same thing inside the experience's own text:

| | | |
|---|---|---|
| `cell` → cellar | 18 | Monasteries: Port, Tokaj, the crayères |
| `villa` → village | 11 | Architecture: a ferry, a scythe, a hiking trail |
| `opera` → operator | 2 | Music: a Sámi reindeer-herding afternoon |
| `ski` → skip | 2 | Skiing: a Saint-Émilion cellar |
| `wall` → wallet | 2 | Medieval and Modern history: fried pizza |

39 wrong listings of 401. The page published its rule honestly — "Selected
by name and description against monaster, hermitage, cell and monk" — which
is what made it look right: **a reader who checked would find `cell` in
`cellar` and believe it.** The docstring was right about the evidence and
wrong about the conclusion: it rejected a trailing boundary because that
"would break the four keywords that are stems on purpose", which is true, and
100 of the 111 prefix matches are ordinary plurals and gerunds. The answer is
not one rule for everything, it is to **say which are stems** — `monaster*`
matches any continuation, every other keyword matches the word plus one
English inflection. `boatman`, `musicians` and `dancers` are in the suffix set
because losing them would trade a false positive for a false negative.

**And the check for it cannot be the matcher.** Re-running the model would
only ever agree with it — the instrument fault this file already records
three times. It asserts the two things AROUND the model: a star is
**bounded**, because a stem is the one place a new false positive can enter
silently, so a star catching a word more than four characters past its stem
fails and names it (`mon*` → "catches monastery, monument"); and a star
**never reaches a reader**, because a page printing `monaster*` publishes a
regular expression as though it were a word.

**A RECORDED REFUSAL IS EVIDENCE, AND IT STOPPED A GOOD-LOOKING CHANGE.** The
experience category page is 4,980 pixels of one row shape and reads as a
tourism database, so the obvious move is to draw its set — and the eight
categories are genuinely distinct (27 of 28 pairs overlap under 0.31). But
`docs/signature-moments.md` already refuses geography there with a reason
that survives re-checking: *48 dots scattered over Europe would say "food is
everywhere", which is true and is not an insight.* Grouping the list under
the four sub-category bars was the second idea and the data refuses it: six
of 48 are in no sub-category and eight are in two, so the grouping would
need a bucket the page has no name for and would print some invitations
twice. **The page is thin because the register holds no photographs, which
is a licence position and not a design one.**

**A QUARTER OF THE ATLAS COULD NOT BE TYPED INTO THE PLANNER'S OWN SENTENCE
BOX.** `words()` lowercases the sentence and strips everything outside
`[a-z0-9]` to a space; the names it is compared against were only lowercased.
So the sentence became *"start from krakow"* while the name stayed
*"kraków"*, and the two never met — **77 of 313 destinations** (Kraków,
Málaga, Córdoba, Reykjavík, Tromsø, Brașov, Gdańsk, Évora, San Sebastián,
Lübeck) and **Türkiye**, the one country whose own name carries a diacritic.
A reader typing "Ten days from Kraków" got a route that ignored Kraków. It is
the worst surface on the site for a silent failure: this planner's whole
pitch is that it *"shows you exactly what it understood, naming anything it
could not take account of rather than quietly dropping it"* — **and it cannot
name a word it never saw.**

**NFD fixes half of it.** ø, þ, ð, ħ, ł, æ and ß have no combining
decomposition, so Tromsø, Þingvellir, Ísafjörður, Ħaġar Qim and Białowieża
survived the first repair. A transliteration table is not an optimisation
here, it is the other half of the alphabet Europe writes in. And folding the
letters and not the punctuation still left 41: *"Kardamyli & the Mani"* keeps
its ampersand where the sentence has lost it. **The rule is one normaliser,
both sides** — every name goes through `words()` now, the same function the
sentence goes through, and the count is 77 → 0. The guard is on the DATA
rather than the matcher: every letter any destination or country name is
spelled with must reduce to a–z under NFD or be in the planner's own table,
so it goes red the day somebody adds a spelling this repository has not seen,
naming the place.

**FIFTY COUNTRY PAGES, SEVEN THOUSAND PIXELS EACH, AND NOWHERE TO ACT.** A
destination page carries *Save to My Europe* a quarter of the way down and
hands the planner its own city; a journey page opens in the Planner. A
country page had **nothing** — not a button, not a save, and only the `/plan`
link every page carries in its masthead. It is the second-largest family here
and the one a reader most often arrives on from a search for "Austria
travel", and it ended on *The record*. `?ask=` fills the sentence box and runs
it, which is how the homepage already hands over.

**And the hand-off is an ACTION, not a note.** The first version used
`.note.onward`, which wears the interactive colour and is deliberately rare;
fifty country pages took it to 62 and `c_note_tones` failed with *"it has
become the default again by the back door"*, which is exactly what had
happened. The Stay layer already composes an action — a rule, the action
beside the sentence saying what it will do, and no border box, radius, shadow
or fill — so this takes that grammar rather than inventing a second one.
**The days are derived**: the sum of the shortest stay this atlas records for
each of the country's own destinations, 8 for Austria and 49 for Greece,
because "a week in Austria" reads better and is a trip length nobody chose.
**And a route needs two places** — Monaco, San Marino and Vatican City hold
one destination each and the three advisory countries are stripped from the
planner index, so 44 of 50 carry it and the six that do not are decided by
the route rather than by a threshold somebody picked.

## Gates

Run all of these before claiming anything is done. **No counts here on
purpose** — every total here grew during a single session, and this list spent
weeks understating the static and browser suites by a wide margin while looking
authoritative. Each command prints its own total; the generated documents own
the rest.

    python3 tools/build.py check              validate the data
    python3 tools/build.py                    build every page
    python3 tools/checks.py                   the static checks
    node tools/browser-checks.js              Chromium, incl. accessibility and contrast
    python3 tools/section-audit.py --check    the spec sections
    python3 tools/ux-audit.py --check         the UI/UX, brand and 2036 sections
    python3 tools/content-report.py --write   what is missing, against the spec's targets
    python3 tools/invariants.py --check       what a visual change may not move
    python3 tools/plate-variation.py --check  the plates have not got more alike
    python3 tools/photo-tests.py              the acquisition pipeline, against a stub provider

And three more that are deliberately NOT gates. Two write an image rather
than a verdict: `node tools/hero-sheet.js` draws every discovered candidate
inside the real hero for art direction, and `node tools/hero-shot.js` shoots
the built homepage once a photograph is in the register.

The third needs the internet, which is the other reason a thing is not a
gate: **`python3 tools/deployed.py` reads the site a reader is actually
served** and compares it with the build in `site/`. EVERY OTHER GATE HERE
VALIDATES THE REPOSITORY AND NOT ONE OF THEM HAS EVER OPENED THE SITE — the
gap that hid the `site/_headers` bug and the `immutable` stylesheet bug, both
of which were correct in the repository and wrong in the response. The
stylesheet's filename is its content hash, so a served page naming a
different one is a served page built from different bytes: that single
comparison is the whole test for "did the work reach readers", and it needs
no version file and no build id. It runs in `.github/workflows/deployed.yml`,
on push, daily and on demand, because the sandbox proxy answers 403 for
europedoor.com.

The browser checks need `npm install playwright` and take a couple of
minutes. They earn their place repeatedly: a 47-pixel mobile overflow on
every city page, two colour tokens below the WCAG contrast line, a places
layer that could never be turned on because `.hidden` is not a property of an
SVG element, and a €700 fortnight routed through Switzerland. They also
caught the planner producing a 2,500 km final leg to reach a named end city
and calling it an itinerary. None of those was findable by reading the code.
They launch the sandbox's own Chromium via `executablePath` because the npm
package version will not match the installed browser build.

**And that is why the suite ran against a different browser here than in CI,
which cost eighty-nine consecutive red runs.** CI has no `/opt/pw-browsers`,
so it downloads Chromium Headless Shell 131; this sandbox has 141. The same
two map-layer checks were green here and red there for the life of the suite.
**Playwright's `isHidden()` means "the element has an empty bounding box",
and Chromium 131 returns the CHILDREN'S geometry for an SVG `<g>` whose
computed display is `none`, where 141 returns a zero rect** — so two browsers
that agreed exactly about the drawing disagreed about the box, and the suite
was reading the box. The map was never wrong. That is the map-label failure in
another family: eleven units is not eleven pixels, and an empty box is not an
undrawn layer. A layer assertion reads the computed display now.

**A failure message with no measurement in it cannot be diagnosed, and this
one was diagnosed in one run once it carried the state.** Three theories were
tried against a browser that cannot be launched here before the message was
made to print `computed-display`, the box and the child count; the first line
of that output ended it. Every other count in this repository is in its
message for the same reason.

**And one that is deliberately not a gate.** `node tools/contact-sheet.js`
puts one page per family in a single image. `--dark` shoots the dark
colour-scheme preference, `--phone` shoots 390px, and `--more` shoots the
twelve families the default set leaves out — macro, place, facet, interest,
experiences, category, how-it-works, fund, method, about, manifesto,
sources. Each of those three found a defect the whole gate suite was green
on. **It refuses to draw a page that is not 200**: the second sheet
photographed a 404 as a blank white cell, which is the same failure as a
suite that stops counting — the output still looks like a result. A sheet cannot fail, and a gate
that cannot fail is a gate people stop running — the same reason
`plate-variation.py` is kept out. Run it after a visual change, and look.

The map pipeline is **not** part of the build — the build must run on a host
with no internet and produce identical pages, so the raw data and the processed
geometry are both committed. Run these when a dataset version changes:

    python3 scripts/map/fetch.py --verify    the bytes on disk are the bytes checked
    python3 scripts/map/process.py --check   data/geo/ matches the pipeline
    python3 scripts/map/process.py --force   rebuild it INCLUDING the terrain

`process.py` on its own leaves `terrain-lod1.json` alone when its fingerprint
still matches, because rebuilding it decodes 182 elevation tiles and smooths
twelve million cells and takes about a minute. `--force` rebuilds it anyway.

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

Depth beats breadth. A few hundred destinations written properly beats 40,000
imported, and there is no importer in this repository on purpose.

## Style

Long comments that explain *why*, usually naming the failure that prompted
the change. Keep them. Prefer recording a mistake to quietly deleting the
evidence of it — the note in `assets/css/europedoor.css` about the 47px
overflow is worth more than the two lines of CSS that fixed it.
