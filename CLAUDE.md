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

**Eight of the nine indexes are the same 280px card grid.** Only `/countries`
differs. That is the design-direction finding again, one level up from the
h1 — and it is not yet fixed.

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

**A hero map was removed once, for reasons that do not apply to this.** That
one was an *instrument*: lod1 coastline, 319 dots, a filter row, ~90,000
bytes, and it led with structure. This is a coastline and nothing else.

| | bytes |
|---|---|
| the hero map that was removed | ~90,000 |
| this | 22,927 |
| the licensed photograph the brief is still open for | 150,000+ |

`weight.home_kb` moved 25 → 47, recorded. **The photograph brief stays
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

The browser checks need `npm install playwright` and take a couple of
minutes. They earn their place repeatedly: a 47-pixel mobile overflow on
every city page, two colour tokens below the WCAG contrast line, a places
layer that could never be turned on because `.hidden` is not a property of an
SVG element, and a €700 fortnight routed through Switzerland. They also
caught the planner producing a 2,500 km final leg to reach a named end city
and calling it an itinerary. None of those was findable by reading the code.
They launch the sandbox's own Chromium via `executablePath` because the npm
package version will not match the installed browser build.

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
