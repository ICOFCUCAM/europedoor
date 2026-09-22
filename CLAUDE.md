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
| **ANY page redesign — read this before writing a line of CSS** | **`docs/redesign-doctrine.md`** — *preserve the information, reinterpret the presentation.* The existing content is authoritative and the existing visual structure is not. Inspect, then write a content architecture, then compose — in that order. The two per-page audits, why photography is structural rather than decorative, and `tools/monotony.js`, which measures the share of a page taken by one repeated component because nothing here counted repetition and forty-two identical rows passed every green gate. It also carries the second rule — **do not optimise for visual consistency at the expense of editorial difference**, because a site where every page is four editorial bands scores beautifully on monotony and is band monotony — the Inspect → Understand → Recompose → Preserve → Audit sequence, the eleven things a recomposition proves rather than claims, the thirteen page grammars, and why /themes and /map are reference implementations of the METHOD and never of the layout |
| **the mandate: what a first-class gateway to Europe would be, and where this one is not** | **`docs/first-class-audit.md`** — 27 surfaces rendered at 1280 and 390 and then measured. Three findings, and Finding 1 is now closed on the numbers: it read 12 of 23 surfaces effectively type to the fold with seven showing no picture at all, and reads **3 of 30 with none and none under a fifth**, median share 24% → 35.6% (CORRECTED twice — the first version said 21 of 22 and was reading where the first figure STARTS rather than how much of the screen it fills). `tools/opening.js` is the instrument, so the number is checkable in a minute. **Finding 2's other half is measured too** — it says the page is the same page and its evidence only ever covered the first 250 pixels: `tools/composition.js` reads the band sequence under the head and finds **29 distinct body shapes over 47 families**, and three h1 sizes at tops 136–745 where the original reading was one size at 150–312. The eight benchmark sites are BLOCKED by the egress proxy and the benchmark half is labelled second-hand |
| **/experiences — the third instrument, and why it is photography rather than a map** | **`docs/experiences-redesign.md`** — the source audit, the image-coverage audit, the twelve bands of the brief mapped onto what this atlas actually holds, the two that are refused, and the seven defects only rendering found. 311 photographs, and on this one page the library was never the constraint |
| **/journeys — movement rather than a list, and where the family's own photograph went** | **`docs/journeys-redesign.md`** — the source audit, the seventeen routes drawn at once as the opening, the three paces derived from measured kilometres a day rather than named, the two things the brief asks for that are refused with their triggers, and the five defects only rendering found |
| **/stories — an editorial desk, and the pictures it already owned** | **`docs/stories-redesign.md`** — the source audit, the eight photographs the register held while the page drew one, the brief's nine bands mapped onto a 1:1 desk taxonomy and 34 tags used once each, and the four class-name collisions one page's run produced with no guard anywhere |
| **/countries — geography first, and the country as its own aperture** | **`docs/countries-redesign.md`** — the source audit, the image-coverage audit (60 relevant photographs and the page drew one), why the brief's strongest idea was already a mechanism here, the seven plates, and the seven defects only rendering found. 41 of 50 countries can be an aperture and nine cannot — six have no outline in this dataset and three are advisory |
| **/events — the year as an instrument, and the month that is busiest is the least characteristic** | **`docs/events-redesign.md`** — the source audit, the eight filters built and discarded on every build, the month-by-kind cross-tab nobody had run, the two of the brief's bands that are one band, and the threshold that called 2-of-4 a finding. 150 fixtures, and the library was never the constraint either |
| **/plan — an instrument rather than a form, and the guard a runtime `<img>` walks straight past** | **`docs/plan-redesign.md`** — the source audit, the seven bands, the three of the brief's asks that collide with recorded findings, the twelve defects only rendering found (nine of them faults already recorded in another family and three of those recorded in the commit before), and the per-leg photograph: `render.credit_html` is one implementation because `checks.py` cannot see an `<img>` a script writes |
| **/my-europe — a private atlas, and the save kind the app did not know** | **`docs/my-europe-redesign.md`** — the source audit, the six save kinds against the five the sort knew, why `Itinerary` looked dead and is not, the brief's three kinds of memory measured as six, the monumental opening refused by the instrument-head measurement, and the three defects only rendering found. Nothing about how this page stores anything changed |
| **/interests — the useful tags are not the biggest, and the nine it had no picture of were the nine it recommends** | **`docs/interests-redesign.md`** — the source audit, eighteen photographs of which nine were spent, `INTEREST_BANDS` read as the three visual scales, the concentration measurement the ledger's own sentence was hiding, the two of the brief's asks that are refused, and the four defects only rendering found — one of them /stories' nested anchor, reproduced a commit after it was recorded |
| **/map — the instrument, and everything that made it one was behind a closed disclosure** | **`docs/map-redesign.md`** — the fault that is the opposite of every other page's: monotony does not list /map at all, and all seventeen interest filters, the four layers, the journey overlay, the distance origin, the legend and the 50-country 319-destination twin were inside two closed `<details>`. Five plates, all 22 map.js hooks asserted intact, and the key that said a destination is pine while the drawing drew it cobalt |
| **/themes — a thematic geography, and the page drew none of the thirteen shapes its own sentence described** | **`docs/themes-redesign.md`** — the first page redesigned under the doctrine and the page that caused it. The `head_figure` contract one of its three callers never honoured, the `c_same_frame` gap that made *says and draws nothing* invisible, the three band scales derived from how many of the nine corners a theme crosses, the four defects only rendering found — including the `object-fit: cover` that was refused on licence grounds — and 37% of the page as one repeated component becoming 18% |
| **/europe-in — the computed atlas, and the printed query was narrower than the query that ran** | **`docs/europe-in-redesign.md`** — the source audit, the 537 tag applications a region tag adds, the two live pages that publish two numbers for one word, the overlap measured at 0 of 66 pairs sharing half, the two of the brief's asks that are refused, and the five defects only rendering found. Zero photographs became eleven and a motion may still not have one of its own |
| **/beyond-the-obvious — the counter-atlas, and the corner with the most quiet places is not the quietest corner** | **`docs/beyond-redesign.md`** — the source audit, the count that argues the wrong way against the share that argues the right one, the rule's three promises measured against the built site (two kept, one not built anywhere), the seven plates, and the two defects only rendering found — plus the correction of a finding this file published three commits ago |
| **the eight page families, and what each room does differently** | **`docs/non-home-redesign.md`** — the non-home redesign answered A-J. The eight rooms derived from the route, the three helpers that were forcing one grammar, the seven image scales, 1,626 declared surfaces, and the defects only rendering found |
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
| **acquiring a photograph without touching a file — the desk, the sign-in, what the browser may send** | **`docs/media-desk-audit.md`** — Phase 1 of the Media Desk brief: what the pipeline already is, which of its thirty sections were already satisfied, and the finding that shaped everything after (there is no Backdoor, no server and no database anywhere in this product). Then run `python3 tools/desk/serve.py` for the local desk, or read **Part 6** for the hosted one, which is a second Vercel project from `desk/` and adds nothing to europedoor.com |
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

**AND THEN THE SAME FAULT ONE LEVEL UP: THE LIST WAS TWENTY URLs TYPED BY
HAND.** Adding Chamonix fixed the STATE that list was missing and left the
shape of the list alone — twenty-six page shapes had never been scanned in
either colour scheme, among them a macro region, a theme, a motion, a month,
a sub-category, a fund project, a facet list, the four legal pages, the
public API, contact, help and the manifesto. It reads `tools/lib/families.js`
now, which is the one list of rendered families and is enumerated against the
built site, plus the three entries that are a STATE rather than a family
(Chamonix with its Stay layer, a second place page, the freshness board).
The suite gained close to four hundred and fifty assertions, and the first run found eight graphics on
`/method` **claiming `role="img"` and hiding themselves** — an image with no
name, on the one page whose subject is how a number is arrived at. Nothing
was broken for a reader, which is why nothing had ever gone red: `aria-hidden`
wins in practice, so the markup was a contradiction rather than a barrier.
Hidden is the right answer rather than a label, because `.distnum` beside it
prints the same drawing in words. **A graphic is named or it is hidden, and
never both** — asserted now, with the element named in the message, because
"svg without a name" on a page with eleven of them is a failure message with
no measurement in it.

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

**AN ACCENT SPENT AS INK IS A DIFFERENT RUNG FROM THE SAME ACCENT SPENT AS A
MARK**, because ink is read against the ground and a mark is drawn on it.
`--pine-ink` and `--olive-ink` carry that, declared above the dark block and
lifted inside it. And **`--door-dark` means "the readable rung", which in the
dark world is the LIGHTER one** — the name says the opposite and three blocks
were written to the name, so ochre-deep measured 3.73 on graphite and
cobalt-lift 4.23. Both had been invisible to every check until `.kicker` moved
from `--door` to `--door-dark`: `--door` was already lifted there and
`--door-dark` had no reader. **A token nobody reads is a token nobody has
measured.**

**`--door` IS THE ACCENT AND `--door-dark` IS THE ACCENT AS TEXT, AND A KICKER
IS TEXT.** The two exist because a colour that gets DRAWN and a colour that
gets READ are different requirements — the same split recorded for the
signature, where `--signature` is the mark and `--door` is anything that is
words. The ground swap to the owner's near-white paper is what exposed it:
terracotta-2 measured 4.16 against #F8F6EF where it cleared on #F3F0E6. **A
lighter page makes every accent's ratio worse.**

**A TWO-COLUMN OPENING MUST NOT SPLIT BEFORE THERE IS ROOM FOR TWO.** Measured
on /journeys: at 704 the opening is one column of 672 and the standfirst sets
on four lines; at 834 it becomes two, column one is 302, and the same 226
characters take EIGHT. Nothing about the content changed, only the track
sizing — which is what the head-range scan exists to say, and it said it about
five heads at once. 834 is already recorded here as *the width that finds a
two-column layout collapsing a column just above its own breakpoint*.

**A CLAMP'S FLOOR IS A DECISION ABOUT EVERY WIDTH BELOW WHERE THE MIDDLE TERM
TAKES OVER, AND THAT WIDTH IS ARITHMETIC RATHER THAN INTUITION.**
"Kunsthistorisches" at 48px does not fit the 288 pixels a 320-wide screen
gives, so the opening h1 broke mid-word — the fault `overflow-wrap` is a last
resort FOR and not a design. Dropping the floor a step fixed that and took ten
pixels off the headline on every phone and every tablet, because 6.8vw does
not pass 48px until 706. The floor is itself width-aware now:
`min(--t-4xl, 12vw)` is 38.4 at 320, 46.8 at 390 and 48 from 400 up, so the
one screen that breaks gets a smaller headline and nothing else moves by more
than a pixel. **The arithmetic was done after the change rather than before
it**, which is the whole reason the first attempt was wrong.

**A SAMPLER THAT READS OUTSIDE ITS OWN IMAGE REPORTS THE CANVAS.**
`screenshot()` without `fullPage` photographs the VIEWPORT, and /events grew
by one band until the year band sat at y=905 on a 900-pixel page — so the
baseline "measured" 1.00:1 on a line that measures 9.36, at both widths, and
would have gone on doing so for any change that made the page one band taller.
That is the aperture sampler's own recorded failure in a check written after
it and without its guard. Both now: scroll it into the shot, and assert the
sample landed inside the image — because a ratio computed from transparent
black looks exactly like a ratio reporting a real defect.

**A COLOUR SIZED ON ONE GROUND IS A COLOUR THAT FAILS ON THE OTHER, AND
SEVENTY OF ONE BROWSER RUN'S 116 FAILURES WERE THAT.** `--pine` is #0F433E:
4.93 on bone paper and **1.74 on graphite**. The moment the masthead stopped
being a band of signature colour and became the page's own paper, every
wordmark and every current-section marker was below AA for a reader in the
dark preference — and the family accents were the same fault one layer over,
with `--ed-terracotta`, `--ed-ochre` and `--ed-olive` naming raw hexes that
read 3.51, 3.66 and 2.98 on graphite. `--door` is the token that already
carries *this family's accent, in this world*, and its lifts were measured
against graphite when they were written; naming the hex was a second
implementation that knew about one ground. Pine as ink is `--pine-ink`,
declared on `body` and never `:root`, because a `var()` resolves where the
DECLARATION lives.

**AND BINDING A FAMILY ACCENT TO THE WORLD BROKE THE ONE BAND THAT IS DARK IN
BOTH.** The arrival head is graphite whatever the preference, so `--door-dark`
handed it the LIGHT preference's dark terracotta on a dark ground: 2.12:1, the
same defect arrived at from the other side, in the commit that fixed it. A
band that is dark whatever the preference needs a colour that is light
whatever the preference, and the rule saying so has to out-specify the family
rule — `body[data-family=…] :is(.ed-eyebrow, …)` is (0,2,1).

**A PAGE HAS ONE GUTTER, AND A COMPONENT LAYER QUIETLY ADDED A SECOND.**
`main` already pads the document — 24px at 1280, 16 on a phone — and every ed-
component then computed `100% - 2 * --ed-gutter` INSIDE that, so a band sat at
75px where an h1 on an older family sat at 24 and the masthead sat at 16. The
browser suite reports it as the masthead disagreeing with the words under it,
which is a true report of a real inconsistency naming the wrong half: it is
the component layer that is indented, not the masthead that is out.

**`1fr` IS NOT `minmax(0, 1fr)`, AND AN `<svg>` SIZED IN PERCENT STILL
CONTRIBUTES 300 PIXELS TO INTRINSIC SIZING.** A `1fr` track has an automatic
minimum and never shrinks below its items' max-content; the SVG default
intrinsic width is 300. So a phone column came out 304.609 inside a 288-pixel
page and dragged the h1, the eyebrow and the intro out with it, and the place
family scrolled sideways. **`min(100%, min-content)` does not resolve on a
floor**: a percentage in `min-width` resolves against the containing block,
and the containing block is a track being sized BY this item, so the
constraint is circular and the browser treats the percentage as indefinite.
That form works for a `max-width` on a measure, where the container is already
sized, and not for a floor on the thing doing the sizing. The track takes the
zero floor and the heading takes `overflow-wrap: break-word`, which breaks
ONLY where the alternative is overflow — so the 108px mid-word break that
floor was written to prevent does not come back at any width where the word
fits, and at 320, where it does not fit, a broken word beats a page a reader
cannot put back.

**A STROKE IN USER UNITS IS NOT A STROKE IN PIXELS, AND THE FIX FOR THAT WAS
MADE AT ONE WIDTH TWICE.** The year band already records it — *1px was not
enough … the ratio a reader gets is the ratio of the pixel* — and the same 1.5
that reads at 1280 is sub-pixel at 390 under `preserveAspectRatio="none"`, so
the baseline sampled 1.00:1 on a phone, on the chart whose caption says "above
the line is what is on". `vector-effect: non-scaling-stroke` states the width
in device pixels at every size. The aperture's reveal had it too: 1.4 units
measured 2.69 against a token computing 4.4.

**AND THE REVEAL WENT WITH THE GROUND, BOTH HALVES OF IT.** The wall's face
was struck in `--bone` and the wall became `--paper` — #F3F0E6 against
#F8F6EF is a step of 1.058, the *rounding error with a token name* this file
refuses for a surface ladder, drawn here as a line nobody can see. The cut
edge takes the map's own border ink at full opacity, which is the colour that
already separates a frontier from the land it is drawn on.

**A DERIVED META VALUE FOLLOWS THE THING IT DESCRIBES OR IT IS A SECOND
IMPLEMENTATION OF IT.** `theme-color` composited `pine-deep` over the ground,
correctly, until the masthead became paper — and then every Android phone
showed a dark green strip above a cream page. The masthead paints `--paper`
over a page that IS `--paper`, so the composite is paper and no blend is
needed; stating one would be a third implementation of a colour.

**A SUITE THAT CRASHES HAS STOPPED COUNTING, AND IT TAKES THE REST OF THE
SUITE WITH IT.** The browser run died forty minutes in on
`document.querySelector(h)` returning null — a destination's contents row
linked to `#why-visit` and no element in the document carried that id.
`section()` emitted `<h2 id="...">` and `ed_section_head()` did not, so every
family that moved to the new head kept a jump target and an
`aria-labelledby` pointing at a heading that had stopped existing. Neither
half is visible in any count: a dangling `aria-labelledby` is not a missing
name in the markup, it is a name that resolves to nothing and the browser
hands the element its content instead, so the section reads as labelled and
is not. This file already says a green run that has stopped counting is worse
than a red one; a run that ENDS on a TypeError reports no failure and leaves
every later check unrun, which is the same fault louder. `c_fragments_resolve`
costs a second, says which page and which fragment, and found a second one in
its first run — `/experiences` pointed at `#kinds`, and neither of the two
bands that answer "how this list is cut" carried it.

**AN F-STRING EXPRESSION CANNOT CONTAIN A COMMENT**, which this file already
records about a paragraph that tried to go into emitted markup. It applies to
a keyword argument inside an f-string too: the reason for an anchor's name
went beside `more=(...)` and the build stopped with *"f-string expression part
cannot include '#'"*. A reason belongs in the function that composes the page.

**THE EYE FINDS A DEFECT AND IT DOES NOT CONFIRM ONE, AND THAT CUTS BOTH
WAYS ON A CONTACT SHEET.** The phone sheet showed the masthead navigation
apparently struck through the wordmark on six of twelve families — a
collision, in the component this file already records two narrow-width fixes
for. Measured in Chromium at 390 the wordmark occupies y=12 to y=45 and the
navigation starts at y=53, and what the thumbnail showed was a 273-pixel
wordmark LINK whose text sits at its left, read at a twelfth of scale. Same
finding as the masthead's own colour, where sampling the pixels said cobalt on
every page while a screen-shot-sized reading said graphite.

**TWO COMPONENTS CAN EACH PAY FOR THE SAME GAP.** `voids.js` reported 304
pixels before a section heading on /interests/mountains — the largest single
hole on the site — and it was not a composition fault: the head pays 178
pixels of its own bottom padding and the band then pays 115 more. Neither is
wrong alone; charging both when they are adjacent is the margin-doubling this
file already records about `main` and the footer, which summed to 224 pixels
of empty page on every page. `.headmeta` is part of the HEAD, so the band
after it is still the band after the head — the first version looked at the
immediate sibling rather than at what that sibling is. 18,216 empty pixels of
239,404 to 17,411 of 238,950.

**A FAMILY ACCENT CAN PAINT A LABEL THE COLOUR OF ITS OWN GROUND.**
`body[data-family="journey"] :is(.ed-eyebrow, .ed-section-index)` is (0,2,1)
and `.ed-journey-hero .ed-eyebrow` is (0,2,0), so the family colour won on the
one element that sits ON the accent: cobalt type on a cobalt field, 1.00:1.
That is the masthead focus ring one element over and the `--focus` token one
file over, and the answer is the same all three times — the thing INVERTS
rather than recolours, and the rule saying so has to out-specify the one that
made it a family colour.

**TWO TRANSLUCENT LAYERS OVER ONE ANOTHER ARE A THIRD TONE.** The journey
hero's route drawing gave its land and the ground beyond it the same 22% bone,
and they OVERLAP — the ground beyond is drawn across the whole frame and
Europe on top of it — so Europe came out at 39% against a 22% rectangle that
read as a pasted panel with a hard edge. The hero's own black-fringe finding,
where two levels of detail of one coast were stacked and the disagreement read
as a drop shadow.

**A FRAMED DRAWING WAS REFUSED THE DATA-CUT FADE BY A FLAG RATHER THAN BY A
MEASUREMENT.** `not (frame and pts)` reads "a framed glyph is a small window
and the cut is outside it", which is true and is not the same as never: the
Arctic-to-Mediterranean journey runs 69°N to 38°N so its frame IS the whole
canvas. The fade's gradients are `userSpaceOnUse` and a framed viewBox is a
WINDOW on those same coordinates rather than a transform of them, so what
decides is whether the window reaches the cut — arithmetic on the viewBox, not
a flag on the caller.

**`height: 100%` AGAINST A `min-height` PARENT RESOLVES TO `auto`**, because
the percentage has no definite height to be a percentage of. A photograph sat
at its intrinsic height inside a slot sized by a clamp, with a band of
`--paper-3` under it. A grid row stretches its item by default, so the box
became a grid and the child fills whatever the min-height resolved to without
asking for a percentage.

**A NAME GENERATED INTO A SENTENCE CANNOT BE THE SUBJECT OF A VERB, AND A
COUNT CANNOT ASSUME A PLURAL.** "What mountains looks like here" — seventeen
tags, some plural, some a compound with an ampersand, no conjugation right for
all of them. "1 destination, the same ones the drawing above plots" — a region
holds one to eight. Both branches get written, or the name becomes a noun
phrase and a derived count carries the sentence.

**A NAME IN A META ROW IS NOT A BYLINE.** The story head printed the author
bare among the desk, the reading time and the date, so the fourth token was a
proper noun among three facts. The section audit caught it on all nine stories
in the run that shipped the head, and nothing a contact sheet or a count could
see: the name is present, placed and legible. The claim was never that the
author is on the page.

**A DECLARED SLOT IS SIZED TO WHAT IT SAYS, NOT TO THE PHOTOGRAPH THAT WILL
REPLACE IT.** `ed_slot()` renders the purpose key, the first sentence of the
brief and the native width and orientation wanted; an opening's floor is
written for a picture, so an empty slot in one left a band of `--paper-3` with
a hairline above it. And `ed_photo()` is the wrong helper for an opening: it
falls back to a generated PLATE, which is placeholder art doing a picture's
job and says nothing about what is missing. `photo() or ed_slot()` marks the
surface and names the acquisition. **1,626 declared surfaces across 479
pages** — `grep -ro 'class="ed-slot ' site --include=index.html | wc -l`.

**EIGHT ROOMS, DERIVED FROM THE ROUTE.** `render.ed_family()` is the one table
mapping a path to ATLAS, ARRIVAL, DISCOVERY, JOURNEY, EDITORIAL, TIME,
INSTRUMENT or INSTITUTION, and no page builder passes a family string —
forty-seven builders each passing one is forty-seven chances for two pages in
one family to disagree, which is the fourteen-call-sites-forgot-the-motif
failure waiting to happen again. See `docs/non-home-redesign.md`.

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

**AND `pgrep -f "[p]hoto-tests"` MATCHED A WAITER THAT NAMED THE FILE, NOT
THE RUN.** The bracket trick stops the pattern matching its OWN shell and
says nothing about a DIFFERENT shell that mentions the same path: a
background loop polling for `…/wt24/tools/photo-tests.py` carried that string
unbracketed on its command line, so the regex found it. The gate had finished
in seven minutes and the poll went on reporting *(still running)* for
fifteen, against a process that was waiting for a directory this session had
already deleted. **A liveness check that matches on a NAME is matching
whoever says the name**, which is `cell` catching `cellar` arriving in
process management — and the tell was there the whole time in a log the poll
never read, at 42 bytes. Read the artefact, not the process table: the run
writes its verdict, and `wc -c` on the log answers the question directly.

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

**AND THAT WAS THE LAST ONE, WHICH MADE A CHECK STOP COUNTING.** Measured
across the built site: **189 `.card-art` elements and every one is a map** —
zero abstract plates on any page. `c_one_plate_per_thing` read the shipped
HTML for a `.card-art` holding a plate, so it has been examining nothing and
reporting green, which is the failure this file already records about the
browser suite, arriving in the static suite. The promise did not change and
its surface did: a plate is still drawn 785 times on the social cards, and
`assets/og/cards.json` maps each content-addressed card to the seed it came
from, so *one record, one picture* is checkable exactly instead of by
comparing markup. It carries a floor on the pages too, because *no page
draws a plate* should be a rule rather than a thing that happens to be true.
**The plate system is now exclusively the social-card language** — the one
surface nobody here ever looks at, rendered inside somebody else's product,
where an illustration drawn from what the place IS beats no picture at all.

**AND A SECOND CHECK WAS BLIND, FOUND BY READING THE COLUMN OF COUNTS.**
`checks.py` prints how many things each check examined, and two of the
hundred read zero. The other one is the check that found Longyearbyen drawn
at y = −317 on a viewBox starting at 0 — a dot outside its own frame, on an
empty sea, with nothing on the page saying a place was missing. It matched
the literal string `pointsmap arched"><svg`, which requires `arched` to be
the LAST class on the figure, and the cartography skin added ` atlas` after
it: from that commit the check examined **0 dots on a site with 130 region
maps** and reported green. Matched on the class LIST now, which is what a
class attribute is, with a floor that fails when it stops finding the family
— 1,293 dots, all inside their frames. **A count is only evidence if
somebody reads it**, and `c_cut_word` was returning the number of ellipses
it found, which ought to be zero, so a healthy check reading every page on
the site printed "(0)" and looked exactly like the two broken ones. It
counts pages.

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

**AND THEN IT WAS ALSO HOSTED, AS A SECOND VERCEL PROJECT FROM `desk/`.**
The brief asks for a desk an editor signs in to, and "run a Python process"
is not that. What did not change is the reason the paragraph below exists:
the hosted desk is **not on europedoor.com**. A credential-holding,
authenticated service on that origin would change the posture of all 1,034
pages to serve one internal tool; a second project, root directory `desk/`,
costs one deployment configured once and leaves the site exactly as strict.

**THE LOCAL DESK HELD STATE AND A SERVERLESS FUNCTION CANNOT.** A session
was a token in a dictionary and a thumbnail was a token in a map — two
invocations share no memory, so a dictionary works on the request that wrote
it and fails on the next, which is the port that appears to work in testing
because testing hits one warm instance. Both are **signed values** now. That
is not the allowlist-in-front-of-an-SSRF the local desk refused: **a
signature is not a guard on a caller's address, it is proof the address came
from a search this desk performed** — and the host allowlist stays anyway,
because a signature proves nothing about where an address points and would
go on proving nothing if the signing key leaked. One check signs
`169.254.169.254` correctly and asserts nothing is fetched.

**A FUNCTION CANNOT IMPORT `tools/lib` OR READ `data/`, so the slot answer is
generated.** `tools/desk-registry.py` resolves every purpose through the same
`imageslots.resolve()` `acquire.py` uses and writes `desk/registry.json` —
committed, and `checks.py` fails when it is stale, exactly like `site/`. **A
templated row carries no requirements of its own**: they belong to the slot,
stated once. 590 copies of one brief is half a megabyte saying one thing and
590 places for it to differ; 519 KB became 225.

**Three things are read live rather than baked, and each for its own
lifetime.** The register comes from `data/images.json` on the **default
branch**, because a photograph in an open pull request has been acquired and
not accepted, and calling it PUBLISHED reports the reviewer's decision before
the reviewer makes it. The licence verdict IS generated, because it changes
with a commit rather than with an acquisition — and it is **not the gate**:
`acquire.py` refuses before it opens a socket, inside the workflow, where the
key is, so this copy can only ever refuse more than the gate.

**THE PROGRESS PANEL HOLDS NO LIST OF STEPS.** The local desk owned its eight
because it ran them; this desk runs nothing, so a list here would be a copy
of `photograph.yml`'s shape that drifts the first time somebody adds a step —
**the ninth thing in this repository to pin a shape rather than a promise.**
GitHub reports the steps it actually ran. And `workflow_dispatch` answers 204
with no run id, so there is nothing to hold: the acquire route signs the
instant before it dispatched and the status route asks for dispatches since
then, inside a signed token so a caller cannot widen the window to read
somebody else's run. **A run GitHub has not created yet reads queued, never
failed** — a verdict nobody has reached is the same error as calling an open
PR published.

**And the word for a green run is not "published".** It is the word an editor
will reach for and the panel refuses it: the photograph is in a branch behind
a pull request, and nothing on europedoor.com has changed until somebody
merges. A check reads that sentence out of the shipped script.

**THE MEDIA DESK IS A LOCAL PROCESS, AND THAT IS A SECURITY DECISION RATHER
THAN A CONVENIENCE.** An editor signs in at `127.0.0.1:8765`, browses
candidates, approves one, and the photograph is acquired, hashed, derived,
registered, gated and committed to a branch — without ever handling a file or
seeing a key. The key never reaches the browser, which is the brief's own
first constraint, so the desk needs a trusted server-side half; putting that
half on europedoor.com would add a credential-holding, authenticated service
to the production origin of a product whose whole posture is `default-src
'none'`, no server, no session and no database. **Nothing is added to the
site, and the CSP does not move.**

**It reuses the pipeline rather than becoming a second one.** It does not
search (that is `discover.cached_search`, so one cache and one rate limit),
does not download (that is `acquire.py`, by id, asserting the returned id is
the requested one), and does not write a register row, build a derivative or
compose a PR body. **It does not push and does not open a pull request** —
sending work outward is a decision a person makes, not a side effect of
clicking Acquire.

**THE BROWSER NEVER HOLDS A PROVIDER URL, AND THAT IS NOT THE SAME AS NOT
FETCHING ONE.** The first version gave each candidate its preview URL and
proxied `/api/thumb?u=<url>` behind a host allowlist. That works and is the
wrong shape: a route that fetches an address a caller supplies is a
server-side request forgery with a guard in front of it, and a guard is
something the next person widens. A search records `token → url` in the
process and the candidate carries only the token, so **there is no
caller-supplied address to check.**

**Four defects only rendering the screens found**, which is the §27 rule
earning its place immediately:

| | |
|---|---|
| `[hidden]` is a UA `display: none` and `.gate { display: grid }` beat it | the hidden sign-in screen laid itself out — 138 pixels of empty page above the header, on every screen |
| a slot's note is written for somebody reading the JSON | rendered whole it pushed the search box 900px down and the contact sheet off screen. First sentence is the hint; the rest is a disclosure |
| each filter label and its control were separate grid cells | "Slot" rendered to the RIGHT of the status select. `for=` was correct throughout, which is exactly why no check saw it |
| the header was a flex row with no wrap | **Sign out** was off the right edge at 390 — the masthead and the section nav on the site itself both had this, twice |

And two more from one change: adding the photograph to the acquisition
dialogue pushed **both buttons off the bottom** — a confirmation whose
confirm button cannot be seen — and pinning the bar then showed that **a
sticky element inside a padded scroller only covers the content box**, so the
list scrolled past it and showed through on either side of an opaque middle.

**The tests own the boundary and not the pipeline.** `photo-tests.py` already
proves fetch-by-id, refusing a mismatched id, keeping the original, never
upscaling and generating the PR body from the register; re-testing those
through the desk would be testing one thing twice and calling it coverage.
`desk-tests.py` asserts what is new — every route refuses without a session,
a wrong passcode costs time and issues nothing, a POST without the desk
header is refused, the key is absent from every response and from the desk's
own log, an unknown thumbnail token serves nothing, and **the register and
the working tree are untouched by the suite.** It never acquires: a test that
did would write a register row, build the site and make a commit in the
repository it is testing.

**THE FIRST REAL PHOTOGRAPH WOULD HAVE FAILED THE BUILD IN FIVE PLACES, AND
THE ONLY THING THAT FOUND IT WAS RUNNING AN ACQUISITION FOR REAL.** The desk
was built, its own suite passed and its screens were rendered; none of that
touches the acquisition, because the desk's own suite deliberately never
acquires. So the pipeline was run end to end against the stub **in a fresh
clone**, and it stopped five times:

| | |
|---|---|
| `derive.py` never made `assets/img/` | it holds only generated files, so git does not track it and **a fresh clone does not have it** — including the checkout the `photograph` workflow runs on. `acquire.py` has always made `photographs/`. Every local run had worked because an earlier run had already created the directory |
| the homepage's own credit link | `rel=''`, no new tab — **a photograph credit in breach of the site's own outbound-link policy**, on the page that opens the site. `picture()`'s figcaption had it right; this is a second, hand-written credit in `pages.home()` |
| the land credit was attached to the HERO | with a photograph the sentence stopped naming Natural Earth and the page went on drawing land in its journey rows. Coverage that depends on a different element being present is worse than none — the `pop_line` finding, one surface over |
| `c_hero_frame` asserted the drawn hero's viewBox | a photograph REPLACES the drawing, so the assertion had no subject. **The ninth assertion here to pin a shape rather than a promise** |
| `c_dusk_reach` asked for two gradients | a fade over a data cut is a property of a drawing that no longer exists. It asserts the ABSENCE now, because "no fade" and "no drawing" must not look the same |

**And two more that only the SECOND run found.** `checks.py` runs the
invariant register as one of its own checks, so handling the register after
it meant the run died before reaching the handling written for it — the fix
was in the right place and the wrong order. Then `photo-tests.py` went red in
the clone on three assertions reading *"no file exists"* and *"nothing is
registered"*, which hold exactly while the register is empty: **the gate
suite that guards photographs would have gone permanently red the day the
product it guards started working.** What a refusal actually promises is that
it wrote nothing, so the state after is asserted equal to the state before,
whatever that state was.

**The invariant register is MEANT to move on the first photograph.**
`safety.img_tags` is recorded as zero with the reason written out — "this
moving is the signal that licensed imagery arrived" — so `--check` fails by
design and a desk that stopped there could never acquire a first photograph
at all. The register's rule is not *never move*, it is that **moving one
silently is not allowed**, and `--write` in the same commit is the deliberate
act. The desk runs the check, rewrites on failure, re-checks, and names every
row that moved in the step detail and in the commit message.

**One photograph is not automatically meant for two surfaces.** The register
already refused a SURFACE being taken over by a different id; the same
question from the other end had no answer, so the same provider id could be
acquired again for a second purpose and nothing anywhere would say so. Twice
is sometimes right and is never an accident: `--second-purpose` is the
escape, the refusal names every purpose the id already fills, and the desk
simply renders no Acquire button on a candidate that is already registered.

**THE DESK COULD SEARCH THE WHOLE LIBRARY AND COULD NOT HOLD ANYTHING.**
Two one-shot paths — find one photograph and approve it, or sweep a country
and approve that grid — and both end in a dispatch, so the only way to
exploit 837 purposes was to make a decision every few minutes and take a
pull request for each. The **basket** is the missing middle: keep candidates
as you go, from a search or from a whole sweep, read and edit every
description in one place, approve once. It is **keyed on the purpose**,
because a surface holds one photograph and the register refuses that pair at
the far end — a basket you can fill with a set the dispatch will reject
wastes the sitting it exists to collect, so a second pick for a surface
replaces the first and says so.

**IT LIVES IN THE BROWSER, AND THAT IS THE SAME DECISION AS THE SIGNED
SESSION.** This desk holds no state anywhere: two serverless invocations
share no memory, which is why a session and a preview token are signed
values rather than dictionary entries. A basket on the server would be the
first stored thing in the product, and it would be shared by everyone who
signs in with the one passcode with no notion of whose it is. So it is one
editor's working set in `localStorage`, the panel says so in those words,
and a browser that refuses to store it says **that** rather than losing the
sitting silently.

**A DISPATCH IS NOT A MERGE, so a sent entry stays in the basket.** Removing
it would call the work done at the moment the question is being asked, and a
red run would leave the editor hunting for every photograph again. Sent
entries are greyed, untickable and cleared by hand.

**A DEAD PREVIEW IS A MISSING PICTURE AND NEVER A MISSING ENTRY.** The
thumbnail token was a flat hour, chosen when a sitting was one search; a
basket makes a sitting hours long, which is what it is for. The token's
lifetime is **the session's own**, read off the cookie rather than
approximated — `/api/thumb` runs `requireSession` first, so anything shorter
buys nothing the session does not already give and anything longer lets a
leaked token outlive the access it was minted under. And where a preview
does expire the entry stays acquirable, because the workflow fetches BY ID
and the id has not changed.

**THE CAP WAS 30 FOR A REASON MEASUREMENT DID NOT SUPPORT.** It said "more
than one sitting", which is a claim about how long the work takes. Run 18
settled it: eight photographs fetched, verified, hashed, derived and
registered in **34 seconds** — 4.25s each — against **215 seconds of fixed
cost** (rebuild 28s, register 5s, static gates 37s, browser and design gates
145s). The acquisition is the small half and it is linear; the gates are the
big half and cost the same for one photograph as for sixty. So the cap was
never about the workflow. It is about what one **pull request** can carry a
reviewer through, and it is 60. The basket itself has no cap: it holds the
working set, the dispatch holds what one question can ask, and a fuller
basket is two sittings rather than a refusal. **And the old test sent 31
copies of ONE purpose**, so raising the cap made it read the duplicate
refusal instead — a test that was checking a different rule than the one it
named. Sixty is now asserted from both sides, because a cap nothing reaches
is a cap nobody has tested the far side of.

**THE PHOTOGRAPH CREDIT WAS THE SITE'S CAPTION INK ON NEAR-BLACK: 2.01:1.**
`.pageband figcaption` said "the credit belongs under the picture and never
over it" and set `margin-top` and `color` to say so. `.credit` is
`position: absolute` at the foot of the picture, on a near-black scrim, at
`opacity: 0` until hover — six declarations — and (0,1,1) beats (0,1,0). So
the COLOUR was overridden and the position, the scrim and the opacity were
not, on every family that opens on a photograph, on the two links Pexels'
terms require. `margin-top` on an absolutely positioned element does nothing
at all, so **a rule that changes two properties of a six-property component**
achieved exactly one thing and that thing was the defect. "Under the
picture" was never available to it either: `picture()` emits the figcaption
INSIDE the `<picture>` and `.pageband` is an `aspect-ratio` box with
`overflow: hidden`, so a static caption there is clipped away rather than
moved below — the rule described a layout the markup cannot produce.

**And the scrim was one twentieth above the floor by accident.** This is the
only contrast on the site that cannot be read off two tokens: the credit
sits on a photograph nobody has licensed yet. The scrim is what makes the
ratio a property of the DESIGN rather than of the picture, and nothing had
done the arithmetic — worst case is a white frame, 55% black composites to
`rgb(115,115,115)`, white on that is **4.74:1**. At 72% it is `rgb(71,71,71)`
and **9.2:1** whatever the photograph does. `checks.py` recomputes both from
the declaration. **The override half was put in `checks.py` first and was
wrong**: written as a CSS rule it refused seven MAP captions, which are real
captions under real drawings — an instrument that cannot tell a caption from
a credit is reading the selector rather than the element. It lives in
`photo-tests.py`, which reads the shipped markup for every class actually
standing over a `<figcaption class="credit">`, because that needs a credit to
exist and that suite makes one.

**AN UNRESOLVABLE `var()` REACHED THE DESK STYLESHEET, one screen from the
rule that documents it.** `--sea` (the token is `--cobalt`) and `--paper`
(it is `--limestone`), in three declarations including both textareas — one
of which is the alt field, the single control on that desk that must be read
in full before it is approved. The declaration is invalid at computed-value
time and the property takes its INHERITED value, so nothing that counts
declarations sees it and nothing that renders does either, because the wrong
value is a real value. The main stylesheet already records this at length.
The hosted suite compares the two sets now; it costs a millisecond.

**AND THE WRAP WAS ON THE HEADER AND NOT ON THE ROW INSIDE IT.** `.top` was
given `flex-wrap` when *Sign out* went off the right edge at 390; `.areas`,
the row that actually holds the tabs, stayed one unbreakable line. Five tabs
fitted at 390 and six did not, so adding the basket put the document back
into sideways scroll on every screen — the same defect, one element in,
caught by `desk-render.js` in the run that introduced it.

**THE PRE-COMMIT SECRET SCAN FAILED ON THE PROVENANCE IT EXISTS TO PROTECT.**
`checks.py` and `photo-tests.py --committed-only` read the same eight files
for credential-shaped tokens, and both had to learn the same thing: a Pexels
source URL carries the photograph's own title as a path segment, and
`/photo/a-close-up-of-party-appetizers-served-on-plates-at-a-gathering-39122376/`
is a 71-character run of word characters and hyphens. `checks.py` was taught
with `in_url_path` — walk back to the start of the token, is it `https://`,
does the match fall before any `?` or `#` — narrow on purpose, because a
credential travels as a query parameter and essentially never as a path
segment. **The other copy kept a twelve-character lookbehind for `://`**,
which is true of a token straight after the host and false of one after
`/photo/`. So run 19 acquired seven photographs, rebuilt, passed every gate
including the browser suite, and was stopped by its own pre-commit scan on
seven register rows. *A second implementation of a thing is a second chance
to make its mistake* — fifth time, and the first where the fix had already
been written and simply not shared.

**And it survived because the scan had only ever read an EMPTY register.**
The suite does acquire, against a stub whose source URL is
`http://127.0.0.1:PORT/...` with no title in it, so the one shape that breaks
the predicate was never put in front of it. *A code path nothing exercises is
a code path nothing checks*, said about a predicate rather than a renderer.
The rows are synthesised from the real thing now, and `credential_shaped()`
is one decision both the scan and the test of the scan call — **the first
version of that test re-implemented the URL half and left the SHA-256 half
out, so it reported a hash as a credential**, which is the fault it was
written to catch, in the instrument.

**AND THEN THE SAME RULE FAILED A THIRD TIME, IN THE COPY THAT HAD BEEN
RIGHT.** Run 20 acquired ten photographs and died in `checks.py` on twenty
identical failures: *"data/images.json contains a 40-character token that
looks like a credential"*, twenty times, naming none of them. All twenty
were **one story slug**. `the-city-that-was-rebuilt-from-paintings` is the
only identifier in 837 purposes that reaches forty characters, and it
appears about twenty times in that story's register row — the purpose, the
file stem, the publication path, the original's path and every derivative
name — so acquiring that ONE photograph failed the build twenty times on a
slug an editor chose months ago.

**A failure message with no measurement in it cannot be diagnosed**, and
this one printed a LENGTH and not the token. That rule is already in this
file, about a map layer; it now applies to the scan as well.

**The exclusion is a lookup, never a shape.** The first attempt was
"every hyphen-separated part is a short lower-case word", which is wrong in
a way that looks airtight: `abcdefgh-ijklmnop-qrstuvwx-yzabcdef-ghijklmn` is
44 characters of key and satisfies it. The archive-stem exclusion three
lines up already states the rule — *checked against the directory rather
than by pattern, because a looser regex is how a real credential gets
through* — so this reads `desk/registry.json`, which declares every purpose,
path and target, is generated, and fails CI when stale. A key is not in the
registry. Both directions are asserted, including that contrived shape and
an undeclared slug.

**AND THERE IS ONE IMPLEMENTATION NOW.** Three real acquisitions died on
this rule in three different ways, each time because one copy knew
something the other did not: run 19 on a URL path segment `checks.py` had
already learned, run 20 on a slug neither had. `checks.py` owns
`credential_shaped()` and `photo-tests.py` imports it. *A second
implementation of a thing is a second chance to make its mistake* — and the
answer, on the third occurrence, is to stop having a second implementation.

**AND THEN THE OWNER REMOVED THE LAST MANUAL STEP.** The brief said *"I
should only have to review and merge the PR"*, and eleven runs later the
measured reality was that the review had become the one step a person still
had to remember — while every check it waited behind had already passed:
fetch by the approved id, id verified, original kept and hashed, ladder
derived without upscaling, provenance complete, every static gate, the
browser and design gates, the credential scan. A green run merges itself now.

**WHAT IS LOST IS NAMED RATHER THAN GLOSSED.** Nothing looks at the
photograph inside the rendered page before it is live. Every gate verifies
provenance, dimensions, contrast, the crop arithmetic and the licence; none
can say whether a gondola is the right opening for the Grand Tour. The art
direction is entirely in the basket now — where it always was for the first
look, and is now the only one. **The pull request is still the record**: it
carries the rendered page, the provenance row and both hashes, and it is
kept rather than skipped.

**THE MERGE MAY NEVER BE THE THING THAT REPORTS SUCCESS.** `gh pr merge` can
be refused by branch protection, a required review or a conflict, and the
workflow deliberately does NOT fail on that — by then the photographs are
acquired, registered, gated and pushed, and a red run would report a loss
that did not happen. So the step is green either way and **its state says
nothing about the outcome**. The desk reads `merged_at` off the pull request
instead. Reporting it from the step would be the `action_required` failure
again: a verdict nobody has reached.

**And the sentence had to move with the mechanism.** The panel's own rule was
that the word for a green run is not "published" — true while a run stopped
at a question, and the same fault reversed once it stops at an answer.
Calling a merged acquisition "waiting for you" is as wrong as calling an
unmerged one published. Two endings, told apart by the pull request rather
than by the run, and the merged one says **next deployment** rather than
"live", because a merge is a commit to the default branch and a reader sees
it when the deployment runs. *Removing a claim leaves surfaces pointing at
it* — the check that guarded the old wording now guards both.

**THE DESK HAD TWO WAYS IN AND BOTH ASKED WHERE FIRST.** Find asks which
surface, Fill a country asks which country — and with 837 purposes and an
empty library that is a lot of deciding before any picture arrives, on the
question an editor has least appetite for, because *"which of the 826 empty
surfaces next"* is not an editorial question at all. **Fill the library** asks
it once, for them: every empty surface, as far as one sitting reaches, in one
press. Press it again for the next tranche. Nothing else changed — this is a
third door into the same machinery, and the same dispatch with the same
refusals.

**ROUND-ROBIN ACROSS FAMILIES, WHICH IS THE WHOLE POINT OF THE ORDER.** Taken
in registry order one press is sixty Austrian destinations: a complete answer
about Austria and no answer about the product. One from each family in turn
means a press touches themes, countries, journeys, interests, macro regions,
categories, stories, regions, destinations and places, so every family gets
its first photograph early — which is when a photograph is worth the most.

**The query is the ROLE's own first concept, not the bare name.** The sweep
searches for "Austria" because a person is about to look at the grid and
judge; nothing looks here, so the query has to carry the intent the eye would
have. `country-hero` declares `{name} landscape` and `destination-hero`
declares `{name}`, and that difference is exactly the editorial knowledge the
roles were written to hold.

**IT REQUIRES THE PHOTOGRAPHER'S OWN DESCRIPTION AND SKIPS A CANDIDATE
WITHOUT ONE.** Every acquisition needs an alt and the alternative to a real
one is writing a description of a photograph nothing here has seen, which is
the licence-from-memory failure in another costume. A candidate with no `alt`
is not unusable — it is **un-automatable**, which is a different thing, and it
stays available to the two paths where a person is looking.

**THE CAP WAS ON THE WRONG QUANTITY, and a test that could not fail is what
found it.** The first version bounded how many it TAKES. A surface whose
search returns nothing qualifying costs a request and yields no row, so the
loop walked all 837 empty surfaces making 837 requests against a rate limit
nobody here owns — the thing `MAX_SURFACES` has guarded one file over since
the sweep was written. It surfaced because the ordering assertion could not
tell round-robin from registry order: **look at everything and every order
covers every family.** A test that cannot fail and a route that cannot stop
were the same bug. `MAX_LOOKS` is 120, twice the fill, because taking sixty
means expecting to reject some.

**And the promise had to become observable.** The ordering test read the
interleave function directly, so swapping `interleave(empty)` for `empty`
inside the handler left it green — the same gap as proving a predicate and
never putting it in the path. The response reports which families the press
actually touched, and the assertion reads that.

**A SENT BASKET ENTRY COULD NOT BE CLEARED**, caught by `desk-render.js` in
the run that added the button. Sent entries are deliberately untickable so
they cannot be sent twice — so *Select all* skips them and *Remove ticked*
works on ticks, and between them the two controls that look like they would
empty the basket could not touch the only thing that accumulates in it. The
per-entry Remove worked all along, which is fine for one and useless for
sixty. **Clear sent** is one press.

**One click is a promise about effort and never about surprise.** The band
states how many surfaces are empty, how many this press takes, that nothing
here has looked at the pictures, and that a green run now merges itself. Every
row still lands in the basket — not as a step to click past, since the
dispatch follows immediately, but because a set that publishes without leaving
a trace of what it chose is a set nobody can audit afterwards.

**FOUR COPIES OF THE DISPATCH CAP, AND THE ONE THAT WAS A GATE WAS THE ONE
LEFT BEHIND.** How many photographs one press may send is stated by the
basket, bounded by the Fill button, refused early by the acquire route, and
refused *for real* by `photograph.yml` before a socket opens — and only the
last is a gate. All four were typed. Three were raised to sixty when the
basket was built and the workflow was not, so run 22 gathered sixty
photographs across every family, put them in the basket, dispatched, and died
on the first step with **`60 entries is more than one sitting. The cap is
30.`** **A cap the editor's own screen contradicts is worse than a low cap**:
it spends the whole sitting before saying no, on the one number the desk
promises about effort.

*A second implementation of a thing is a second chance to make its mistake* —
sixth occurrence, and the first where the disagreeing copies were a *number*
rather than a predicate. The number is declared once in
`tools/desk-registry.py`, generated into `desk/registry.json` (committed, and
stale-checked like `site/`), and read by all four. **The check refuses a
numeric literal in each of the four places and requires each to read
`dispatch_cap`** — comparing the four values would go green the moment
somebody typed the same number twice, which is exactly the state this failed
from. `MAX_LOOKS` is derived as twice the fill for the same reason: a ceiling
written as a number stops being twice the fill the day the fill moves.

**And the refusal now prints the number it refused by.** Run 22's message was
a hard-coded `The cap is 30` beside a hard-coded `> 30`; had either
interpolated, the disagreement would have been in the first log line. *A
failure message with no measurement in it cannot be diagnosed*, applied to a
constant rather than to a measurement.

**THE PIPELINE REFUSED A PNG AND SAID SOMETHING FALSE ABOUT WHY, AND ONE
REFUSED CANDIDATE THREW AWAY EIGHTEEN FINISHED ACQUISITIONS.** With the cap
fixed, run 23 fetched, verified, hashed, derived and registered eighteen
photographs across every family, and then died on the nineteenth:

    the bytes from pexels are not a JPEG. The provenance row would record a
    hash of something this pipeline cannot derive from. Nothing written.

**The second sentence is not true.** `derive.py` decodes with Pillow and reads
PNG and WebP as readily as JPEG; what the header reader is actually FOR is the
size check under it, because the DECLARED dimensions are what cleared the
slot, so the served bytes have to be shown to match — and that needs a header
this script can read without an image dependency. Pexels serves an original in
whatever format the photographer uploaded. So `image_size()` reads all three
now, from their own headers, and **an original is kept under the extension its
bytes actually are** — a file named `.jpg` that is a PNG is a claim about its
own contents that is false, in the one directory that exists to be evidence.
**And `derive.py` reads that path out of the register** instead of rebuilding
`<stem>.original.jpg` from the convention: the seventh time a second
implementation of one fact has cost something here, and the first where it
would have been a file extension.

**Two kinds of no had the same exit code.** All-or-nothing is right for a
malformed PLAN — a reviewer cannot tell *these six were chosen* from *these
six arrived before it broke*, which is why the plan's shape is checked in full
before a socket opens — and **wrong for a judgement about one candidate**,
because with sixty automatic picks from the Fill button a rejection is
expected rather than exceptional. `acquire.py` exits **3** for a refusal about
this photograph and nothing else (does not suit the slot, bytes nothing can
size, served size not the declared one, the id already fills a surface) and
**1** for anything a next candidate would hit too (no key, a refused gate, a
rate limit, an id the provider swapped). **The line is whether the next
candidate could succeed** — and a swapped or missing id stays hard, because
the standing rule is to fail rather than ever substitute.

**Nothing is silent and nothing is substituted.** Each skip is named in the
step summary, in the commit message and in its own section of the pull
request, which says in those words that the surface is still empty. **A
sitting that acquired nothing fails**, because "found nothing suitable" and
"could not run" must not look the same. And the commit counts what ARRIVED:
it counted the plan, which was the same number until a batch could skip, and
a count that is not the set's own extent reads as one.

**THE LOOP MOVED OUT OF THE WORKFLOW BODY INTO `scripts/images/batch.sh`, so
the promise could be tested rather than asserted as a string.** "The others
still arrive" is behavioural, and a behavioural promise pinned as YAML text is
a shape — the eleventh time that has happened here. `photo-tests.py` now runs
that script against the stub with a three-entry plan whose middle candidate
the pipeline refuses, and reads the result: two acquired, one skipped, the
skip carrying `acquire.py`'s own sentence rather than a summary composed by
the loop, and no register row for the refused surface. Proved the other two
ways as well — everything refused fails, and a swapped id stops before the
next entry.

**And the suite had only ever put a JPEG in front of the acquisition**, which
is why the one thing that could have found this never ran. *A code path
nothing exercises is a code path nothing checks*, said about the stub's
fixtures rather than about the code.

**RUNNING IT FOUND FOUR MORE THINGS AND READING COULD NOT HAVE FOUND ONE OF
THEM.** `run()` prepends the interpreter, so handing it a shell script ran
Python against bash source and every assertion read a file the loop had never
created. A **multi-line reason** — "does not suit" names each requirement it
missed — put the rest of itself on following lines of a tab-separated record,
and taking only the first line instead left *"does not suit door-coast:"* with
nothing after the colon, which is the failure-message rule arriving in the
record rather than in a message. The plan's third entry named a slot capping
aspect at 1.9 against a 2.00 stub, so a test whose whole subject is the SKIP
could not tell a deliberate refusal from an accidental one. **And the block
inherited the register every block above it had written** — the PNG block
fills the homepage hero, the second-purpose block puts one id on two surfaces
— so entry one was refused as *already filled*, counted as a skip, and the run
reported two skips where it expected one. **A test about skipping has to own
its starting state**, which is the same fault as a test that cannot fail.

**THE FIRST RUN AFTER THE ELEVEN THEME HEROES MERGED DELETED THEIR
DERIVATIVES.** `photo-tests.py` cleans up after itself by prefix —
`homepage-hero`, `door-mountains`, `country-hero`, and **`-hero@`**, which
matches every slot instance. That list was written when the register was
empty and every `-hero@` file on disk was a stub the suite had just made. The
moment real photographs carried those names, a green suite run swept 165
licensed derivatives out of `assets/img`, and the only thing that noticed was
`checks.py` failing on every page referencing files that were no longer there.
**The restored register is the authority on what belongs**: anything it names
is somebody's licensed photograph, and a suite that writes into the
repository owns taking out only what it put in.

**And two of the desk suite's own assertions were the empty-register fault
again, one file over from where it is recorded.** *"With an empty register
every status is EMPTY"* is a claim about the product's contents wearing the
clothes of a claim about the desk's derivation, and *"the register is
untouched"* was written as `reg_now == {}`. Both went red the day eleven
photographs merged — for a desk that had got better. **A derivation promises
it AGREES with its source**, so the first asserts PUBLISHED if and only if
the register holds that purpose, in both directions; and **untouched means
unchanged, not empty**, so the second compares against the state read at the
start, whatever that state was. Proved red three ways.

**THE READING TYPE WAS A DOCUMENTATION SCALE.** Measured on a destination
page: 5,226 of its ~6,700 characters at 15px or under, 2,606 of those at 13 or
under, against a 76px h1 — and the stylesheet spent 99 of its font-size
declarations on the two smallest steps and four on the body. Body 15 → 17,
secondary 13 → 15, captions 12 → 13. **`--t-lg` did not move**: it is a length
in a 1,120-unit viewBox and `LABEL_METRICS` carries a width model fitted at
that size.

**And a label scale is not a reading scale.** `--t-sm` served both, so the
rise also enlarged the masthead navigation and three meta lines — uppercase at
.06em is a third wider at 15 than at 13, and "200 DESTINATIONS" stopped fitting
beside EXPLORE on a 240px door. Those five rules take the caption step.

**Raising it broke five things at narrow widths and the browser suite found
every one.** A `min-width: min-content` floor on the overture h1 — added to
stop four headlines being cut mid-word — pushed the place page 53px off a
320px screen uncapped; `19 DAYS · 5 COUNTRIES · MODERATE` was `nowrap` and
fitted at 13 and not at 15; "Travel regions" cannot fit a third of 288px; and
both sentence boxes were wider than the placeholder that teaches them.

**A MEASURE MAY NEVER BE NARROWER THAN ITS LONGEST WORD.** `14ch` is a
character count wearing a length's clothes — a `ch` is the width of a zero —
so Elbphilharmonie measured 214px inside a 210px box and dropped its last
glyph onto a line of its own, on four pages of 1,033. `min(100%, min-content)`.

**A MARK IN USER UNITS IS A DIFFERENT SIZE ON EVERY FRAMED DRAWING.**
`glyph_view()` fits the frame to the route, so the three journeys on the
homepage are drawn at 1000, 422 and 340 units and rendered at the same 690
pixels: a 5-unit dot came out 3.4px on one row and 10.1 on the next, and the
route stroke 3px against 9px. The build normalises the frame away and the
family states its own size; framed strokes are `non-scaling-stroke`.

**THIRTY COUNTRY PLATES NAMED A MOUNTAIN AND MOST NAMED A FOREIGN ONE.**
`summit_points` returns the highest peaks IN FRAME and a country plate frames
its neighbours, so the tallest thing on screen is usually across the border:
Austria named Triglav, Switzerland named Mont Blanc, Croatia named three peaks
and none was Croatian. A summit must be on the subject now — `NameGround`'s own
test — and 13 of 50 name one, Austria's being Grossglockner.

**And the model cannot check itself, so the browser does.** A check reads every
country portrait with `isPointInFill`, which is a different implementation of
the same question. Its first run found GREECE set with its middle in the
Aegean: `LABEL_METRICS` is a fitted UPPER envelope, so the modelled box and the
drawn one differ by a few units and on a fragmented coast that is land against
water. The middle is three samples now, not one — 43 portraits named to 39, all
true where the old 43 were measured by the model that placed them.

**A CONTROL A READER CANNOT SEE THE EDGE OF.** The homepage ask field painted
`rgb(247,246,243)` on a body of `rgb(247,246,243)` with a transparent border:
present, labelled, keyboard-reachable, no edge. It was right inside the hero,
where paper on graphite is a field, and moved to the light band keeping the
fill — the same move its own LABEL made, which was found at 1.00:1 and fixed
while the fill was left. A browser check crosses every control's edge pixel by
pixel against the 3:1 of WCAG 1.4.11, and found four more: `--rule` is the
hairline between two list rows and it bounded every form field on the site, so
the planner's days, budget and month each read **1.43:1**.

**EVERY POSSESSIVE WAS A TYPEWRITER APOSTROPHE** — 2,165 of them, on two pages in three.
Curled at the data loader, not in the renderer: the first version ran on the
emitted HTML, which skips `<script>`, so the page said Europe’s and the JSON-LD
breadcrumb beside it said Europe's and `checks.py` failed on exactly the
promise it exists to hold. One representation, and never in a slug or a URL.

**One paragraph in ten ended on a single word** — 106 widows of 998 multi-line
paragraphs. `text-wrap: pretty` on running text; `balance` stays on headings.

**EIGHT SECTIONS AT ONE GAP READ AS EIGHT EQUAL CLAIMS.** The section rhythm is
a single constant, so a destination page ran eight bands 104px apart with every
head the same size in the same place. `render.section(opens=True)` marks a
change of movement with a rule and more air. And `mini` did not mean small:
scoped to a note and a rail it left 587 of 1,288 headings at full section size,
every one of them a fact under a head.

**A CAPTION SAYS WHAT THE PICTURE IS; A SOURCE NOTE SAYS WHERE IT CAME FROM.**
They were one paragraph, so on a place page 199 pixels of caption sat under a
127-pixel drawing. The scale of the projection and the size of the frame are
facts about the instrument, not about the place. 852 of 917 figcaptions carry
the two tiers; the rest are two-word locator labels and photo credits. The
sizes sit on the SPANS — four containers set a caption's size and
`.placeband figcaption` is the same specificity as `.minimap figcaption` and
further down the file.

**A THIRD OF THE HERO WAS CROPPED AWAY ON A WIDE MONITOR.** `slice` is right —
the frame is 1120×800 where every other map is 1000×780 — but the drawing's
width is capped at the column while its height fills a hero whose floor is
43vw, so the taller the window the more of the WIDTH goes: 1,078 units shown at
1280, 961 at 1920 where AZERBAIJAN was sliced, and 721 at 2560. Bounded at
1,050, the margin the frame was given. **The dusk was checked against the names
and cleared**: it dims a name and its ground together, so all fifteen measure
1.95–2.13:1 in light or shadow.

**THE BODY MAPS HAD NO WATER, NO COAST AND CRACKS THROUGH THE LAND.** The glyph
family was one flat silhouette on the page's own paper: no sea, so a bay and
the margin were the same colour; lod0 rings simplified per country, so
independently thinned neighbours left white cracks; and the 52°E cut ran raw.
`.card-map` had painted water since the cartography split and this family never
got it.

**RULES AND SPACE, NOT A CARD — and two surfaces were the last holdouts.**
Border, fill, radius and shadow each say "separate object, placed here by a
system", and three surfaces had already given that up. The rail kept all four
on every family that carries one, and the Europe Experience Score was a card inside a `tone-quiet`
band whose fill is within a step of its own.

**`tools/voids.js` measures empty page per family**, and is NOT a gate on
`opening.js`'s reason: a ceiling on empty page is satisfied by tightening the
section rhythm, and the 104px between two bands is not a hole. Its first
version read `h2/p/li/figure` and reported 1,702px on a destination page
against a real 804 — the score bars are divs and it could not see them.

**THE OWNER'S PALETTE, AND THE FIRST THING IT CHANGES IS THE MAPS.** Bone
`#F3F0E6`, pine `#0F433E`, graphite `#07100F`, and five accents that identify a
content FAMILY rather than decorate a page. The brief is explicit about the
half that is easy to get wrong — *"I would NOT make every page colorful. This
is critical"* and *"UI = restrained, PHOTOGRAPHY = rich, MAPS = precise,
TYPOGRAPHY = dramatic"* — so an eight-hue wheel with a tinted ground and a
gradient ribbon per family was generated in OKLCH, measured, shipped and
removed one commit later, because it is the site the second sentence names.

**There are two map sets now and a drawing takes one of them by what it IS.**
The light map is the European atlas: `#D8D4C7` land on `#DDE8E7` water, which
is **1.18 against each other and that is the point** — a printed atlas is
stone on pale water and the COASTLINE is what separates them, so the ink went
up as the tone step came down. The dark map is the instrument and the hero:
`#F3F0E6` continent on `#07100F` at 16.90, where the coast needs no stroke at
all and `#B9C1BA` is a faint internal frontier at 1.62. *Notice: no olive.*

**AND THE APERTURE STOPPED BEING MEASURABLE THE MOMENT THE WATER WENT PALE.**
*Light wall, dark opening* was the whole reading, and on an inland frame there
is now no water in the opening: bone wall, stone opening, **1.10:1**, which
the browser suite failed Austria and Chamonix on and was right to. It cannot
be fixed by tuning the land — two tones a reader is meant to read as one
material are always close, which is the point of the atlas being drawn on one
stone. So the door is read by its REVEAL, and the reveal is the map's own
border ink: 4.41 against the wall, 3.39 against the land, from `#68716E` at
full opacity where graphite at 55% composited to 2.49. **One value in both
preferences**, where there used to be two, because the opening is pale in
either now.

**THE OCEAN RAMP HAD TO GO WITH THE WATER, OR THE SWAMP COMES BACK AS A
HALO.** Four steps of near-black navy — the shore band under every coast, the
rivers and lakes on 824 plates, the hero's own Atlantic — left alone under the
light map drew a dark blue fringe round every pale coastline: the exact
treatment the brief objects to, surviving as an outline after the fill had
been fixed. One hue at 175, saturation rising with depth, and **the deep step
is sized by what it has to do rather than by how a sea looks**: a river is a
line on the LAND, so `#346F6A` is 3.90 on the stone. Found on a contact sheet
of twelve families, which is the only instrument that could see it.

**GOLD IS NARROWED TO WHAT IT WAS PROTECTING RATHER THAN DELETED.** The old
rule refused every gold by arithmetic, and the reason was what gold SAYS. The
owner's palette then names ochre `#C49A52` as the territorial accent for the
regions and the events calendar, which is a different job from a gold button.
So: the two brasses stay out **by value**, the arithmetic is **untouched** —
loosening it until ochre passed would loosen it until a brass passed, which is
the credential scan's own lesson — the register declares which golds are the
ochre family, and **no gold may be `--sea`, `--sea-dark`, `--signature` or the
primary action**. That last clause is not decoration: `.btn { background:
var(--door) }` was one late line that gave every family its own button colour,
and on the regions that button was gold. `css.gold` counts golds the register
does not declare, so it is still zero and a fourth one has to be argued for.

**A DISTINCT PAIR IS TOLD APART BY HUE *OR* BY LUMINANCE.** The block was
written because a contrast ratio cannot see hue — the advisory red and the
cultural accent sat fourteen degrees apart at identical lightness and measured
1.22. Asked only for hue, it then refused the owner's own ochre and terracotta
at 22 degrees, which are not remotely the same colour: 0.355 of luminance
against 0.207, **1.57 against each other**. A hue floor alone would have
refused a real distinction and then been lowered until it refused nothing. The
disjunction is still red on the pair that created it, which fails both.

**TWO STRAY `*/` HAD EACH BEEN SWALLOWING THE RULE AFTER IT.** An edit closed
a comment one line early, twice, and the continuation prose then sat in the
stylesheet as raw text — which a CSS parser reads as the start of a selector
until it finds a `{`. So the next whole rule was consumed into an invalid
selector and dropped: `.essay { --measure: 38rem }`, the entire measure of the
story family, and `.minilabel.here { font-weight: 700 }`, which is how a map
says which place you are reading about. **Nothing counts a dropped rule** —
not the dead-rule scan, which walks rules the browser parsed, and not the
invariant register, which counts declarations. A four-line scan for a `*/`
outside a comment finds both in a second.

**AN INSTRUMENT THAT READS ITS OWN DOCUMENTATION AS CODE IS WRONG, AND SIX
PLACES DID IT INDEPENDENTLY.** This file already records it about the
font-size count. Within an hour of the palette landing it happened twice more:
the paragraph recording that `#6f4f11` had been REMOVED was read as a gold
still in the stylesheet, and the paragraph recording that `.btn` had stopped
taking `--door` was read as the rule itself. `bare_css()` is the one
implementation now, and `css_hex()` beside it — **a token that points at
another token is not a missing token**, which six checks reported as
"`--atlas-sea` is not declared in the stylesheet" the moment the cartography
was bound to the owner's map set.

**AND THE UX AUDIT PINNED TWO TOKEN NAMES THAT STOPPED EXISTING.**
`--limestone` became `--bone` and `--atlantic` became `--olive`, so §B4 went
red for the right event and the wrong claim — the tenth assertion here to pin
a shape rather than a promise. It reads the register's own token list now, and
case-insensitively, because a rename is a real failure and a capital letter is
not.

**THE HERO WAS THE DARK MAP DRAWN WITH THE LIGHT MAP'S LAND.** It painted
`--atlas-land`, which is right on pale water and reads as grey-brown on
near-black, so the one picture on the site was a dim continent in the dark.
Rebound rather than restated — six rules downstream mix against that token, so
setting the fill alone would have drawn a bone continent with a coastline
computed from a colour no longer in the picture. **Two things only rendering
found**: the context land beyond the atlas came up to 30% of bone and became
*quieter Europe*, which is the exact reading the graphite ground replaced; and
the shore band, blurred and pale, drew a hard-edged bright wedge over Russia
that looks like a beam somebody left on. **On a dark map a shore band is a
shadow, not a highlight** — the lit-aura failure this stylesheet already
records, arrived at from the other side.

**THE 2036 PAGE SYSTEM: EIGHT FAMILIES, ONE GRAMMAR, AND NOT FORTY-SEVEN
REDESIGNS.** The owner's brief makes the finding this repository had already
half-made — several families had converged on kicker → h1 → lede → rows — and
draws the right conclusion from it: build eight rooms and map every page into
one, so the site reads as one institution rather than as forty-seven
templates. Atlas, Arrival, Discovery, Journey, Editorial, Time, Instrument,
Institutional.

**THE FAMILY IS DERIVED FROM THE ROUTE, so no page builder changed.**
`render.ed_family(path)` is one table. Forty-seven builders each passing a
family string is forty-seven chances for two pages in one family to disagree,
which is the failure this repository already has recorded about the fourteen
call sites that forgot to pass a motif — and a family is what a route IS:
`/europe/<c>/<r>/<city>` is an arrival because of where it sits. Order
matters twice, because `/discover/` is Discovery and `/discover/<macro>` is a
macro region, and `/experiences/<cat>/<sub>` is Time while
`/experiences/<cat>` is Discovery.

**THE PRIMITIVES ARE THE BRIEF'S AND THE DEPARTURES ARE MEASURED.** Three of
them:

| | |
|---|---|
| `ed_photo` returns the drawing, never "" | the brief's version returns an empty string with no photograph, which would leave 826 of 837 surfaces as a hole. *A slot waiting for a picture is honest and three hundred pixels of one is a hole* — already measured, on the homepage doors |
| `ed_rows` derives the number | the brief passes `number` per row, and a figure typed into data is the figure that was true two hundred destinations ago |
| `ed_photo` takes a register key, never a URL | `picture()` is the one function that knows whether the register holds one; a component that took `src` would be a second way into the library with none of the licence gate behind it |

**FOUR NEW TYPE VALUES FOR EIGHT FAMILIES, WHERE THE BRIEF WRITES NINE
CLAMPS.** Each of its components carries its own, a few pixels from its
neighbour — and nine arbitrary clamps is a second type scale wearing the
first one's clothes, which is how the sibling repository reached 418 font
sizes. `--ed-display-1` is every opening, hero and institutional head;
`--ed-display-2` every section title, split and arrival; `--ed-display-3`
every row and route stop; `--ed-read` the standfirst under all of them. **No
new breakpoint**: the brief's 850 and 520 are 52rem and 44rem, which this
stylesheet already has, and the register refused a seventh once. **No new
line-height**: the eight the site had already cover it.

**THE `--ed-*` LAYER IS ONE-DIRECTIONAL AND A CHECK PROVES IT.** The brief
writes its components against `--ed-` names and this stylesheet's register
refuses a second NAME for a colour — *a second name for one colour is two
colours waiting to disagree*, which is why `--atlas-context` was deleted. It
refuses an unresolvable `var()` harder still. Between those two, an alias
that can be PROVED not to diverge is the smaller fault: every `--ed-` colour
is a bare `var()` of a registered token and never a literal. **On `body`
rather than `:root`**, because a `var()` resolves where the declaration lives
and the world tokens are set on `body[data-world]` — the `accent-color` bug,
forty lines from the note about it.

**AND THE PRIMITIVE FLOORS ARE ON THE PROMISE RATHER THAN THE CLASS NAME.**
`ed-opening` is a page head, `ed-arrival` is a page head, `ed-journey-hero`
is a page head, `ed-eyebrow` is a kicker, `ed-row` is a row. A floor counting
only the old spelling read the migration as *a page family has grown its own
components* — which is the exact thing it exists to catch, reported about a
page that had just stopped doing it. Three head checks and one reach check
had to learn it, one family at a time, each discovered by a build failing on
fifty or three hundred pages at once.

**THE THIRTEENTH AND FOURTEENTH SHAPES PINNED.** §13 required
`class="statement"` on a destination and §17 on a journey — and both went red
for compositions that do MORE of what they protect, the arrival band and the
cobalt hero. Both measure document order now: the place's own sentence before
any metadata, the strapline before the numbers. Proved red.

**AND THE INVARIANT FAILURE MESSAGE LEADS WITH THE MEASUREMENT AGAIN.**
`primitives.reach` carries every deliberate move that figure has ever made,
correctly, and printed all four thousand words of it on each of sixteen
sub-keys: a run reporting three one-page migrations printed twelve thousand
words, and the three numbers that diagnose it were in the first line of each.
*A failure message with no measurement in it cannot be diagnosed*, and the
corollary is that a measurement buried in an essay is not in the message
either.

**THE LIBRARY HAS ELEVEN PHOTOGRAPHS BECAUSE A CREDENTIAL SCAN COULD NOT
SPELL A PLACE, AND FIVE ACQUISITIONS WERE THROWN AWAY ONE AFTER ANOTHER.**

Runs 24 to 28 were dispatched by the owner and every one of them failed. They
were not failing to acquire: run 26's own log reads *"every registered
photograph still hashes to what was recorded (2,201)"* and *"a registered
photograph appears on the page its purpose claims (1,136)"*. It fetched,
verified by id, hashed, derived the ladder, completed the provenance and
passed every gate on the list — and then died on **86 identical failures**,
all of them the pre-commit credential scan, naming place slugs:

    austria__salzburg-and-the-lakes__salzburg__hohensalzburg    56 chars
    albania__tirana-and-the-south__gjirokaster                  42
    austria__salzburg-and-the-lakes__salzburg__mirabell-gardens 59

**The registry declares a place with SLASHES and a file stem cannot hold
one.** `desk/registry.json` has
`austria/salzburg-and-the-lakes/salzburg/hohensalzburg`; `derive.py` writes
`austria__salzburg-...`. The scan split the registry's target on every
non-word character, so the declared identifier became four short tokens and
not one of them reached the forty-character floor to be collected — while the
stem arrived as a single 56-character run with nothing to match it against.
The exclusion was a lookup, correctly, and the two sides were written in
different alphabets.

**THE RULE IS ONE NORMALISER, BOTH SIDES.** That sentence is already in this
file, about the planner: it lowercased the sentence and not the names, so a
quarter of the atlas could not be typed into its own search box. Same fault,
in a credential scan, with separators instead of accents. Fourth time this
one rule has stopped a real acquisition, and the first where the two
disagreeing copies were a *separator*.

**AND THE TRANCHE IS PUSHED BEFORE THE GATES RUN NOW.** `batch.sh` learned
this at the level of one candidate — run 23 lost eighteen finished
acquisitions to a nineteenth that was a PNG — and the same failure one level
up cost thousands, where the thing ending the sitting was not even about a
photograph: run 28 died on a sentence in `CLAUDE.md` that said *a page count*,
a prose check about documentation discarding a day of acquisition. A red gate
costs a pull request somebody has to fix, which is recoverable and visible; it
used to cost the whole sitting, which is neither. The merge step still
requires the gates, so nothing reaches the default branch unchecked — what
changed is that the WORK survives a failure.

**`stage: fill` IS THE DESK'S OWN BUTTON, DISPATCHABLE.** The hosted Media
Desk has had *Fill the library* since the basket was built and it works; it
is also a second Vercel project somebody has to be signed in to, and eleven
photographs against 837 surfaces says nobody pressed it fourteen times.
`scripts/images/fill.py` is that decision inside the workflow, where the key
is: it reads the registry, takes the empty surfaces round-robin across
families, searches, and writes a PLAN. It does not download, does not hash,
does not register and does not build a derivative — `acquire.py` does all of
that and `batch.sh` runs it once per entry. `photo-tests.py` asserts the
boundary: a plan with no purpose twice, no provider id twice, every entry
carrying the photographer's own description, no surface the register already
holds, and **the register and the working tree unchanged**, because planning
is deciding what to ask for and only the acquisition may write one down.

**THE NON-HOME REDESIGN: EIGHT ROOMS, AND THE HELPERS WERE WHAT FORCED THE
GRAMMAR.** The directive's central finding is that changing a page's colours,
spacing and card styles produces another variation of the same site, and that
the fix is to redesign the presentation layer rather than decorate it. Three
helpers were doing the forcing and all three changed rather than their call
sites:

| helper | was | is |
|---|---|---|
| `render.section()` | a small h2 with a lede under it, on three-quarters of the pages | the title at display size with its lede beside it and a **CSS counter** down the left, because a number typed per call site is wrong the day somebody reorders a page |
| `render.indexhero()` | a 60px h1 in a narrow column beside a 4:3 figure, on five indexes | the 2036 opening, keeping the three classes that are read as promises |
| `.pagehead` with no role | the institutional family, looking exactly like a travel page | a typographic monument — the head selected by what it is NOT, so a fourth role token cannot drift out of step with itself |

**THE MASTHEAD WAS THE LARGEST SINGLE REASON TWELVE FAMILIES READ AS ONE.** A
solid pine band across every document meant the first 63 pixels were identical
and the most saturated thing in frame, whatever changed underneath. It is the
page's own paper now, with pine spent on the mark and the current section, and
it inverts **only where there is a picture under it** — keyed with `:has()` on
the composition rather than on the family, because /journeys is family
`journey` and opens on bone, and the first version put a graphite scrim and a
white wordmark on a cream index.

**SEVEN IMAGE SCALES, BECAUSE THE FAILURE WAS NEVER "TOO FEW PHOTOGRAPHS".**
It was every photograph the same size in the same 16/9 card. A bleed leaves
the column and is a change of movement; a feature is asymmetric at 1.35 against
.65, because two equal columns read as a layout and an unequal pair reads as a
picture with something to say; a strip SCROLLS rather than wrapping, because
wrapping an order into rows turns a sequence into a grid; a mosaic is one
dominant picture and two beside it and returns nothing below three, since two
in a three-cell grid is a grid with a hole; a declaration is type over a
picture behind a scrim that makes the ratio a property of the design.

**AND EACH FAMILY'S SEQUENCE IS ITS OWN SET.** A country's strip is its
destinations, a destination's is its places, a journey's is its legs in order,
a theme's is its eight stops — every one built from slots this product already
declares, which is "use the actual existing images" read as "use the actual
existing declarations". **The keys were wrong on all four**: they built
`destination:<target>` and the register writes `city:<target>`, so not one
could ever have matched even after the library fills. Found because an empty
slot can print its own brief and three of them printed nothing.

**A DECLARED SLOT IS NEITHER A PHOTOGRAPH NOR A HOLE.** 826 of 837 surfaces
are empty, so a redesign built around photography could not be *seen*:
returning nothing kept the page honest and made the composition invisible, and
a hash-drawn landscape would put back the exact thing this site measured out —
189 `.card-art` elements and every one a map. The slot prints the surface's own
brief from `desk/registry.json`: which surface, what the picture must be of,
and how large. No `<img>`, no register row, nothing for the licence gate to
refuse, and **the acquisition list is the page itself**. It is sized to what it
SAYS rather than to the bleed's 21:9 — 581 pixels of mineral with three lines
at the bottom is the hole it exists to remove — and the photograph that
replaces it takes the full proportion back.

**A `minmax(0, …)` TRACK SHRINKS BELOW ITS CONTENT, and at 108px that reads as
a broken name.** "Kunsthistorisches Museum" came out as *Kunsthistoris / ches
Museum*. The h1 asks for `min-width: min-content` — the fix this stylesheet
already recorded, a `ch` being the width of a zero — and an explicit 0 floor on
the track overrules it, so the box could not grow and the browser broke the
word instead. It held at 60px and stopped holding at 108, because min-content
is computed at the current size.

**THE PHOTOGRAPH IS A WINDOW, AND `overflow: hidden` CANNOT MAKE ONE.** Plate
03 was a 76vh box with the picture absolutely positioned inside it — which is
a large card, because a full-bleed photograph that scrolls with the page is
just a picture in a box. A window stays still while the wall moves past it, so
the picture is fixed to the VIEWPORT and the band is `clip-path: inset(0)`:
the band's own rectangle is the aperture and the photograph is revealed
through it. Three alternatives each fail, and the reasons are the whole
argument for this one:

| | |
|---|---|
| `background-attachment: fixed` | iOS Safari ignores it outright, so the effect would exist on a desk and silently not exist for half the readership |
| a scroll listener translating the picture | that is parallax, which is a DIFFERENT effect — parallax moves the picture slower, a window does not move it at all — and it needs JavaScript on a page whose only `<script>` is the inert JSON-LD block |
| `overflow: hidden` on the band | **does not clip a fixed descendant at all**, because a fixed box is laid out against the viewport rather than against any scrolling ancestor. `clip-path` clips descendants whatever their position, which is precisely why it is the one property that does this |

**AND SIX PROPERTIES KILL IT SILENTLY.** `transform`, `filter`,
`backdrop-filter`, `perspective`, `will-change` naming any of those, and
`contain` each make an element a containing block for FIXED descendants — so
one of them anywhere between `<body>` and the picture resolves `position:
fixed` against that element instead of the viewport, and the picture goes back
to scrolling with the page. **Nothing reports a fault**: every box is still
the right size in the right place, `getComputedStyle` still says `fixed`, and
every contrast, layout, count and weight check goes on passing. This
stylesheet already carries three of the six elsewhere — `backdrop-filter` on
the masthead, `filter: drop-shadow` on two map layers — so it is not
hypothetical. The chain is html → body → main → `.sheet-landscape` →
`.shotfull`, and `main` carries `z-index: 1`, which makes a stacking context
and is NOT a containing block for fixed. `browser-checks.js` walks that chain
and names the element that broke it, then proves the promise the only way a
promise about scrolling can be proved: it scrolls three hundred pixels and
asserts the picture did not move. Proved red with `main { transform:
translateZ(0) }` — the picture moved 300px against a 300px scroll, and
`position` still read `fixed`, which is exactly why the position assertion
alone is not enough.

**`svh`, NOT `vh`, AND THE HEIGHT IS OVER 100 ON PURPOSE.** `vh` is the LARGE
viewport, so a phone's toolbars growing and shrinking mid-scroll would resize
the band underneath a picture that is standing still — the one movement this
effect cannot have. 110 rather than 100 because the reveal needs scroll
distance to happen in.

**AND THE TINT GOES INSIDE THE FIXED ELEMENT.** As a pseudo-element of the
band the scrim was absolutely positioned against a 110svh box that scrolls, so
it would crawl across a photograph that is not moving and the gradient a
letter sits on would depend on how far down the page that letter had
travelled. Fixed with the picture, the tint is a property of the viewport
exactly as the picture is, so the ink meets the same ground at every scroll
position.

**THE INSTRUMENT WRITTEN TO MEASURE TYPE OVER THAT PHOTOGRAPH HAD BEEN READING
PAST THE END OF ITS OWN SCREENSHOT FOR THE LIFE OF THE PLATE, AND ONE NaN
DEFEATED BOTH THE MEASUREMENT AND THE GUARD WRITTEN TO CATCH A DEFEATED
MEASUREMENT.** `page.screenshot()` without `fullPage` photographs the VIEWPORT;
plate 03 opens 1,818 pixels below the fold, so the headline sat at y=2301–2447
of a 900-pixel image. Every index was past the end of the pixel data,
`A.data[i]` was `undefined`, and `Math.abs(undefined - undefined)` is NaN — so
`NaN < 40` is false, the *no glyph paints here* test never fired, and every
out-of-bounds pixel was **counted as a glyph**, which satisfied the reach
guard; and `NaN < worst` is false too, so `worst` stayed Infinity and the
ratio passed. That is the year band's own recorded failure — *a sampler that
reads outside its own image reports the canvas* — arriving through the one
hole its guard did not cover, because **the guard counted pixels rather than
asserting the rectangle was inside the picture.** Three more things about it
were wrong and every one of them passed:

- **One frame cannot hold four elements.** Scrolling the plate to the middle
  puts the headline and the standfirst in shot and pushes the licence credit
  21 pixels past the bottom edge, so a single pair of screenshots measures two
  elements and fails the reach guard on a third for a reason that is about the
  instrument. Each element is scrolled into its own frame now.
- **Hiding the element hid its scrim.** `visibility: hidden` is right while
  every measured element paints nothing of its own and wrong the moment one
  carries a tint: hiding the credit hid the scrim the credit exists to sit on,
  so the *ground* shot was the bare photograph and the instrument reported the
  defect the scrim had already fixed — **2.00:1 against a real 10.39**. The
  ground a glyph is painted over includes whatever its own box paints, so the
  INK is removed and the box is left standing.
- **And `color: transparent` reads back as `rgba(0,0,0,0)`**, so the
  foreground has to be captured before it is removed or every ratio collapses
  to about 1:1 — a failure that looks exactly like the defect being measured.

**IT MEASURED FOR THE FIRST TIME AND THE LICENCE CREDIT WAS AT 2.07:1.** Bone
on rgb(160,170,181), the pale sky at the top of the mountain, on the one
element Pexels' terms require to be there. The band's scrim runs at 100 degrees
and is transparent at the right BY DESIGN — that is what keeps the photograph a
photograph rather than a dark panel — and the credit sits bottom-right, which
is exactly where the tint runs out. So it carries its own, the way `.credit`
already does on every other photographic surface here, and the size is
arithmetic on the worst case a photograph can present: a pure white frame, with
graphite at 72% compositing to rgb(76,83,82) and bone on that measuring
**6.90:1 whatever the picture does**. 72% rather than a figure picked by eye
because `.credit` already argued for 72%, and a second number would be a second
decision about one thing. Measured on the real photograph: 2.07 → 10.39. The
call to action and the credit are both in the measured set now — they were
outside it while the instrument could not see anything at all.


**A ROW THAT SHOWS EIGHT OF ELEVEN AND SAYS NOTHING IS A SELECTION.** Plate
02's photograph row was `[:8]` — a cap written when eight was the whole of
what the register held and the grid was eight fixed tracks, so it read as a
statement about the layout. The comment directly above it already said the
opposite: *the register decides which eight … it grows to the full thirteen
as the library fills and the layout does not change.* Eleven themes carry a
photograph now and Grand Tour, Modernist and Thermal were dropped by data
order, silently, on the plate whose sentence is that the continent reorders
itself around what you seek. **The code had stopped matching its own
comment.** The register decides and the grid follows the count:
`repeat(auto-fill, minmax(10rem, 1fr))` — `auto-fill` rather than
`auto-fit`, because `auto-fit` collapses the empty tracks and stretches a
short last row to full width, so eleven tiles come out as eight small
pictures and three large ones. **The floor is the NAME under the tile, not
the picture**: RENAISSANCE is 115px of uppercase tracked at .16em and this
row has already overflowed once on exactly that, while eleven across 1,152px
would be 90px each, which is the contact strip the rule above it rejects. Six
and five, at 182px against the 134 they replaced, and two media rules pinning
four and two columns are gone because auto-fill already answers them.

**AND THE CREDIT UNDER IT WAS A LIST SET TO A PROSE MEASURE.** `max-width:
62ch` capped eleven photographers' names at 513px inside a 1,152px row: three
lines of commas in the left 45% with 639 pixels of empty plate beside them,
and the credit the longest paragraph in its own band. This file already
records the identical fault about a middot list of place names broken at
544px inside a 948px column — a measure exists so the eye can find the next
line of a sentence, and nobody reads a credit line as a sentence. **Deleting
the local rule was not the fix**: this is a `<p>`, and `p { max-width:
var(--measure) }` then capped it at 544, four lines from the comment saying a
measure is the wrong idea here. `max-width: none` is a declaration, not the
absence of one.

**A RULE STATED ONCE AND APPLIED TO ONE OF ITS FOUR CALL SITES.** *A declared
slot is sized to what it SAYS, not to the photograph that will replace it* is
written out on `.ed-slot-wide`, whose 21:9 left 581 pixels of mineral with
three lines at the bottom — and it was applied to `.ed-slot-wide`.
`.ed-slot-tall`, `.ed-slot-square` and `.ed-slot-portrait` kept an
`aspect-ratio`, which is the photograph's proportion and therefore the exact
thing the rule refuses. Measured on the two openings carrying a square slot:
**682 × 511 with the brief in the bottom third, 361 pixels of `--paper-3`,
71% of the box** — proportionally worse than the case the rule was written
for. The container's floor had already been fixed one line above
(`.ed-opening-visual:has(> .ed-slot) { min-height: 0 }`), so half the job was
done and **the half left standing was the visible half.**

**THE DISTINCTION THE RULE DID NOT MAKE IS WHERE THE SLOT IS.** In a STRIP a
portrait slot renders 240 × 320 and its proportion is what makes the strip a
row of like things — eight tiles that each shrink to their own caption is not
a strip, it is a ragged list — so every one of those is untouched
(`grep -ro 'ed-slot ed-slot-portrait' site --include=index.html | wc -l`). In an OPENING the slot is alone, nothing is beside it to be ragged
against, and reserving a picture nobody has licensed is reserving a hole.
511px → 208px, empty ground 361px → 58px, `voids.js` unmoved.

**THE LIBRARY IS THE BINDING CONSTRAINT AND NO AMOUNT OF LAYOUT FIXES IT.**
Eleven photographs against 1,626 declared surfaces. The homepage now spends
every one of them twice — eleven at 182px on plate 02 and one at full bleed
through the window on plate 03 — and there is no third place to put them that
would not be the same eleven a third time. `docs/gap-assessment.md` already
says this in general; it is worth saying again at the point somebody asks why
a touristic site has so few pictures. **The next photograph is a
`workflow_dispatch` of `photograph.yml` with `stage: fill`**, which plans
every empty surface round-robin across families, acquires by id, hashes,
derives, registers, gates and merges itself on green. It is one action and it
is the owner's, because the key is a repository secret and because nothing
here may acquire a real photograph unasked.


**THE DEAD-RULE SCAN WAS MEASURING WHERE THE MOUSE HAD BEEN LEFT.** It
reported 37 rules against a ceiling of 36 in a run where **no stylesheet byte
had moved**, and rerun standalone on the identical build it said 34 — with the
34 an exact subset. The three extra were `.staged .now` and two `:hover,
:focus-visible` rules, and the mechanism is that **a `:hover` selector matches
nothing when the pointer is nowhere**: standalone the scan skipped those rules
entirely, and in the suite an earlier check had left the mouse on a card, so
they matched, were judged, and counted. The scan was using the suite's shared
page and inheriting its pointer AND its viewport. It takes its own page now.

**AND IT SCANNED ONE WIDTH WHILE ITS OWN COMMENT ARGUED ABOUT THE OTHER.**
That comment says, specifically about `.band > .band-head`'s `display: grid`,
that *a media rule that does not currently apply is asleep, not dead* — and
the scan went on counting that rule dead, because it never looked at 390.
Measured: 34 dead at 1280, 34 at 390, **31 at both**. The principle was
written down and never implemented, which is *a rule stated once and applied
to one of its call sites* arriving in the instrument rather than in the
stylesheet. Both widths now, and a rule alive at either is alive — the same
union the scan already did across PAGES, on the axis the comment was about.

**AND ITS PAGE SET HELD NO PAGE CARRYING A PHOTOGRAPH.** Widening to 390 put
the `@media (max-width: 44rem)` block in the scan's reach for the first time
and reported `.credit {opacity}` dead — the rule that reveals the licence
credit on a phone. Measured on a real theme page it is **1 at 390 and 0 at
1280**, which is the rule working: not one of the seventeen scanned pages
carries a `.credit` where it decides anything. That is this check's own
recorded finding about `.regionglyph .countries path` — a rule measured only
where it loses looks like a rule that wins nowhere, and a ceiling raised for
that is a ceiling raised for a gap in the scan. `/themes/mountain-europe` is
in the set now, and it immediately found two real ones: **`display: block` on
the photograph inside an opening**, restating what a grid item already
computes. That is the **third and fourth dead `display: block` found on a
photograph container here**, each in the first run where a photograph actually
rendered — *a code path nothing exercises is a code path nothing checks*,
about a measuring device. Removed, and verified by byte-identical screenshots
at 1280 and 390 on both pages, because nothing here is deleted on the scan's
word alone.

**AND THEN THE COUNT WAS THE WRONG INSTRUMENT, BECAUSE IT JITTERS.** With the
pointer and the viewport both pinned, consecutive runs on one build read **34
of 332 rules examined and 35 of 334** — the REACH varies, so the population
differs rather than the verdicts. A ceiling on a quantity that moves does not
merely fail at random: **it teaches whoever hits it to re-run until green**,
which is how a real dead rule gets through, and it is the mirror of *a green
run that has stopped counting is worse than a red one*. The check's own
comment already said the LIST was the thing — *raising this number is allowed
and raising it without reading the list is not* — which makes a count a proxy
for a set somebody was asked to read by hand. The 35 are written down by name
now: a rule NOT on the list fails and is named, a run that finds one fewer
still passes because a subset is not a regression. Proved red by adding one
redundant declaration, which was named alone against a printed 36-of-335.


**AND THE FIFTH DEAD `display` ON A PHOTOGRAPH CONTAINER ARRIVED THE DAY THE
HOMEPAGE HERO WAS FILLED.** Run #32 acquired sixty photographs, among them
`home-hero`, and the tranche survived the red gate because commit 38 made
`batch` push before it gates — the branch carried the register at seventy-one
where it had held eleven. The browser suite came back with one failure and it was
`.sheet-door .opening :is(picture, img) {display}`: **an absolutely positioned
box is blockified by the layout**, so `display: block` beside `position:
absolute` restates what the box already computes and can never change a pixel.
It had never been reported because `.opening` had never held a `<picture>` —
the same *a code path nothing exercises is a code path nothing checks* that
produced the other four, each found in the first run where a photograph
actually rendered in that container. Verified the way this repository requires
rather than on the scan's word: the real homepage shot at 1280 and at 390
against that seventy-one-photograph register, with the declaration and
without, **byte-identical at both widths**.


**RUN 31 ACQUIRED SIXTY PHOTOGRAPHS, PASSED EVERYTHING ELSE, AND THREW ALL
SIXTY AWAY OVER THREE CHARACTERS.** The desk's own *Fill the library* button
dispatches `stage: batch`, and `batch` gated BEFORE it pushed — so the tranche
died in `checks.py` with the push step three steps below it. Two causes, both
invisible to every local run.

**THE LENGTH FLOOR WAS ON THE WRONG SIDE OF THE NORMALISER, WHICH IS THE OTHER
HALF OF THE BUG THAT STOPPED RUNS 24–28.** `_canon()` collapses every
separator to ONE underscore so a registry target and a file stem are compared
in the same alphabet — and `derive.py` writes a stem with TWO, so **the
canonical form is always shorter than the token that has to match it.** The
declarations were then filtered by the length of that shorter form:

| | |
|---|---:|
| `derive.py` writes | `austria__tyrol__innsbruck__goldenes-dachl` — **41** |
| its canon | `austria_tyrol_innsbruck_goldenes-dachl` — 38 |
| the registry declares | `austria/tyrol/innsbruck/goldenes-dachl` — 38 |

41 is long enough to be SCANNED and 38 is too short to be DECLARED, so the
floor discarded exactly the declaration the scan needed. There is no length of
a declaration that predicts the length of its token, so any floor there is a
guess: it is gone, and the canonical form is collected whatever it measures.
*One normaliser, both sides* was right and incomplete — **a test applied to a
normalised value has to be normalised with it.**

**AND FIVE PURPOSES POINTED AT SURFACES THAT HAD BEEN DELETED.** `door-coast`,
`door-food`, `door-history`, `door-mountains` and `themes-hero` appear nowhere
in `site/` at all: the four doors went when the homepage became the plate
sequence, `themes-hero` went when the themes index stopped opening on a map,
and neither removal took its purpose with it. *Removing a claim leaves
surfaces pointing at it*, five times, in a repository whose own rule that is.

**IT PASSED EVERY LOCAL RUN BECAUSE `c_photo_published` CAN ONLY ASK ABOUT A
PURPOSE THE REGISTER ALREADY HOLDS.** Eleven theme heroes were registered, so
it examined eleven surfaces and said nothing about the other 828 — the
empty-register fault again, and the check cannot be fixed into seeing it,
because the question it asks needs a photograph to exist. `c_purpose_reaches`
asks the other question: does a page builder ask `picture()` for this key at
all. **The absence is what has to be tested and absence is not in the shipped
HTML** — an unfilled surface renders `ed_slot()`, which prints the page's own
label rather than the register key, so a page that asks for `door-coast` and a
page that has never heard of it are the same bytes. That is why this one is
asserted at the SOURCE, exactly as `c_og_no_hash_motif` is.

The five are deleted rather than restored, because both removals were
deliberate and recorded. `purposes_today` is derived, so it is re-derived
rather than edited; `architecture` and `food` lost their only purpose and take
a **trigger** rather than a refusal, because the argument each serves is real
and unbuilt — a role nothing reaches is dead vocabulary only when nothing
would ever create one.

**AND `batch` PUSHES BEFORE IT GATES NOW, WHICH IS THE THIRD PLACE THIS RULE
HAS HAD TO BE LEARNED.** `batch.sh` learned it for one candidate (run 23 lost
eighteen acquisitions to a nineteenth that was a PNG); `fill` learned it for a
tranche; **the job the Media Desk actually dispatches never did.** A red gate
costs a pull request somebody has to fix, which is recoverable and visible; it
used to cost the sitting, which is neither. Nothing reaches the default branch
unchecked — the gates still run and the merge step is still skipped when they
fail.

**AND REORDERING FOR ONE PROMISE ALMOST DROPPED ANOTHER.** The first version
moved the push above the gates and left the credential scan below it — turning
a PRE-COMMIT guard into a report filed after the key had already reached the
remote. `fill` had the right order all along. The scan goes in front of the
push in both.


**THE CROP-BOX MEASUREMENT WAS ASSERTING NOTHING ABOUT SIX OF ITS SEVEN
SURFACES, AND THE SEVENTH WAS MEASURING A STATE A PHOTOGRAPH REMOVES.**
`checks.py` owns the safe-area arithmetic and `browser-checks.js` owns the
measurement, and the comment on each says the other exists so that *neither
can drift without the other noticing*. The measuring end had a list of three
entries typed by hand, and it had drifted on all three.

Two named elements the site no longer has. `.way` left when the four
homepage doors became the plate sequence; `.herofull` left in the same
commit, and `homepage-hero` renders inside `.opening` on plate 01. **A
selector that matches nothing has no aspect ratio**, so `lo` stayed
`Infinity` and `hi` stayed `-Infinity` — and `Infinity >= min_aspect` and
`-Infinity <= max_aspect` are BOTH true. Two green assertions per run, about
nothing, for the life of the plate sequence.

That is this repository's own recorded failure twice over: the check matching
`pointsmap arched"><svg` that examined 0 dots on a site with 130 region maps,
and `c_one_plate_per_thing` reading zero once the last abstract plate came
off. Both of those were caught by **reading the column of counts**, which
does not exist here — `ok()` counts an assertion MADE, and an assertion about
an empty set counts exactly like one about a page.

**AND THE THIRD ENTRY WAS WORSE THAN THE TWO THAT MATCHED NOTHING, BECAUSE IT
MATCHED AND MEASURED THE WRONG STATE.** `.iheroart` holds the drawing until a
photograph replaces it. The check added `.shot` — the class the build adds —
and left the drawing where it was, so it measured the box with the thing a
photograph removes still inside it:

| `.iheroart` at twenty viewports | | |
|---|---|---|
| with the drawing in it | 1.333 – 1.500 | what was declared |
| with a photograph in it | 0.692 – 1.500 | what a photograph gets |

So the declared floor was a fact about the page as it is rather than the page
a photograph makes, and the guaranteed frame it produced — **55%** — was
nearly double the real **29%**. *A code path nothing exercises is a code path
nothing checks*, about the one measurement whose entire subject is a state the
register has never been in. The simulation is the whole substitution now: the
drawing and any empty slot come out, a picture goes in, `.shot` goes on.

**THE SET IS DERIVED AND THE GROUPING IS BY COMPONENT.** Every purpose that
declares a container is measured, on the path `desk/registry.json` gives it,
so a purpose deleted with its surface leaves no entry behind and a new one is
measured the day it is declared. Surfaces group by SELECTOR because **a crop
box is a property of a component rather than of a page** — `.iheroart.shot`
exists on `/journeys` and not yet on `/experiences` or `/stories`, whose
openings render no figure at all until a photograph exists, and measuring the
component once is the only way to say anything true about either. Two
purposes on one component may not declare two boxes, which is asserted rather
than silently picked between. Each group asserts its own REACH.

Re-measured, and three of the seven had moved to a different component
entirely — `events`, `countries` and `interests` went from `indexhero()` to
`ed_opening()` and their container is `.ed-opening-visual`:

| | container | frame |
|---|---|---|
| homepage-hero | `.opening` 0.615 – 2.801 | 15% → **17%** |
| journeys / experiences / stories | `.iheroart.shot` 0.692 – 1.500 | 55% → **29%** |
| events / countries / interests | `.ed-opening-visual` 0.692 – 1.643 | 55% → **26%** |

All three clear the 12% floor, so nothing about the design has to change —
what changes is that the numbers are now about boxes that exist.

**AND THE TEMPLATED SLOTS ARE THE SAME FAULT AT A HUNDRED TIMES THE SCALE,
WHICH IS THE NEXT COMMIT RATHER THAN THIS ONE.** `checks.py` computes a safe
area for the ten `slots` as well, and the typed list never held one of them,
so not one has ever been measured. Seven declare `.pageband`, which the built site does not
contain at all — `grep -rlo 'class="pageband' site --include=index.html | wc -l`
is zero — and two declare `.card-art.frame`, where
`grep -rho 'class="card-art[^"]*"' site --include=index.html | sort -u`
returns `class="card-art card-map"` and nothing else. The eleven licensed
theme photographs render in `.ed-opening-visual > figure.headshot` and their
declared box describes a component that was removed. It is recorded here
rather than fixed in the same commit because it needs its own measurement
pass over nine families, and because a check that reports a known gap without
failing is a gate people stop running.

**AND THE SISTER SUITE'S FIXTURES WERE A SECOND DECLARATION OF WHICH PURPOSES
EXIST.** `tools/hosted-desk-tests.js` named `door-coast` and `door-food` in
four tests, and both purposes were deleted with the doors. `specOf()` then
refused them at entry ONE — so the assertions about entry TWO, about a
surface ticked twice, and about one photograph on two surfaces were every one
pre-empted by a refusal none of them was written for. **A suite whose subject
is the batch boundary stopped reaching the batch boundary**, and reported four
honest failures naming the wrong thing. `photo-tests.py` had the identical
fixtures and was repaired in the commit that deleted the purposes; this file
was not looked at — *a rule stated once and applied to one of its call sites*,
in the commit that wrote that sentence down. The two fixtures come out of
`desk/registry.json` now, which is the same document `specOf()` consults, is
generated, and fails CI when stale.



**THE TEN TEMPLATED SLOTS DECLARED A CROP BOX EACH AND FOUR NAMED THE WRONG
COMPONENT — AND THE FILE SAID SO IN A FIELD NOBODY READ.** Every slot's
`min_at` and `max_at` read the literal string **`"declared"`**, where a purpose
carries a viewport like `320x900`. That is the whole finding in one word: the
five that were right were right because somebody read the stylesheet, and the
four that were wrong had nothing to catch them, because `browser-checks.js`
never held one slot in its list and `c_photo_safe_area` recomputes arithmetic
from the numbers rather than asking what they are about.

| slot | declared | renders | measured |
|---|---|---|---|
| theme-hero | `.pageband` | `.headshot` in `.ed-opening-visual` | 0.692 – 1.333 |
| country-hero | `.pageband` | `.headshot` in `.pagehead.opening` | 0.941 – 1.129 |
| story-hero | `.card-art.frame` | `.ed-bleed.ed-bleed-tall` | 1.333 – 2.333 |
| place-hero | `.card-art.frame` | `.card-art.frame` — **correct** | 16/9, from the stylesheet |

The five `.pageband` families (macro, region, interest, journey, category) are
right: `pageband()` emits that figure and the stylesheet gives it `16/9` below
62rem and `21/9` above, which is exactly the 1.778 – 2.333 declared. They have
still never been measured, because `pageband()` returns nothing at all without
a photograph and none of those five families has one.

**A CHECK THAT CANNOT FAIL ON THE CASE THAT MOTIVATED IT IS THE FAULT IT WAS
WRITTEN TO CATCH.** `c_container_is_emitted` asks the prior question nothing
asked — is this selector a thing this site emits — and its first version
collected class TOKENS. `card-art` is emitted and `frame` is emitted, and the
defect was that they are never emitted TOGETHER: every `.card-art` on the
built site is `card-art card-map`. A set of bare tokens said yes. **A compound
selector is a claim about one element**, so the attribute groupings are kept
and each compound is tested whole. Read out of `class="..."` rather than by
substring, because a class named only in a comment is the
instrument-reads-its-own-documentation fault recorded six times above.

**AND IT IMMEDIATELY REFUSED ONE OF THE FOUR "CORRECTIONS".** `place-hero` was
moved to `.ed-strip .ed-shot` on the evidence that a place photograph appears
as a strip tile on its destination's page — and the check said `.card-art.frame`
IS emitted, by `pages.py` line 6834, on the place's own page. Both are true:
**that key renders in two containers at once**, 16/9 on the page the purpose is
FOR and 3/4 in the strip beside it, and the register has one field for it. The
declaration follows the purpose's own surface and the reuse is undeclared —
which is the same shape as a theme photograph appearing at 182px on the
homepage's plate 02 and full-bleed through the window on plate 03. **A
photograph is cropped by every surface it appears on and the register declares
one.** Recorded, not closed.

**AND `.headshot` PROVED COMMIT 39's GROUPING PRINCIPLE WRONG IN GENERAL.**
That commit grouped surfaces by selector and asserted two purposes on one
component may not declare two boxes, "because a crop box is a property of the
component". True of `.iheroart`, whose own rule is `aspect-ratio: 4/3`; false
of a component sized by its parent. Measured: `.headshot` is **0.692 – 1.333**
inside a theme page's `.ed-opening-visual` and **0.941 – 1.129** inside a
country page's `.pagehead.opening` — one class, two real boxes, because the
class sets no ratio of its own and the two families put it in different grids.
The assertion was green and unsound, which is the landmine this file already
records about a pinned heading, so it is gone. Nothing is lost: the group
measures the UNION over every path its purposes declare, so two families whose
real boxes differ produce a union wider than either declaration and the two
bounds fail and name it. **The union is both the stronger test and the honest
one** — the remedy it points at is separate selectors, not one number.



**TWO NUMBERING SYSTEMS ON ONE PAGE, AND 753 PAGES PRINTED THE SAME NUMBER
TWICE.** `section()` draws its index from a CSS counter — `main` resets
`band`, every `.band` increments it — and the reason is written on that rule:
*a number typed per call site is wrong the day somebody reorders a page*. The
2036 section head was then written with the number as its **first argument**,
so every page carrying both shapes numbered each sequence from one. Measured
across the built site: **753 of the 829 documents that carried a typed index
printed a number a band counter also printed.** A place page opened *"01 · NEARBY /
The rest of Vienna"* and then, directly under it, *"01 / Other places in
Vienna"*. Nothing counted it, because each system was internally correct.

`ed_section_head()` lost its `number` parameter — an ignored argument is dead
code that looks like a decision — and `.ed-section` increments the same
counter the bands do.

**AND THE SAME SET WAS BEING PRINTED TWICE TO SAY TWO THINGS.** Those two
bands were not merely adjacent, they were the same places: the strip carried
the picture, the name and the link, and the rows underneath carried the one
thing the strip could not — the sentence saying what each one IS. **220 of
the 255 place pages.** Neither band was wrong and neither was complete, so
deleting one would have been the page saying less: `ed_strip` takes an
optional `note` and the tile carries the sentence. `others` never exceeds
four on any page in this dataset, so the strip's own limit never selects.

**A COUNTER THAT COUNTS WHAT IT DOES NOT DRAW IS WRONG FROM ITS SECOND ENTRY
ON, AND BOTH HALVES OF THIS HAD IT.** The first repair scoped the increment
to `.ed-section` and immediately caught `<div class="headmeta ed-section">` —
the accessibility, getting-there and up-a-level block, a real section with no
head — so the place page opened at "02" and ended at "04" with nothing
numbered 01. And `.band` had the identical fault, unnoticed for longer:
`/countries` draws its nine macro regions as `<section class="band
macroband">` whose head sits inside a `.bandtop` wrapper, so `.band >
.band-head::before` never matched them. **Nine silent increments, and the two
numbered sections after them would have printed "010" and "011".** The rule
is the same on both: **the selector that COUNTS is the selector that DRAWS.**

**AND THE CHECK'S FIRST VERSION READ THE MODEL RATHER THAN THE PAGE.** It
tried to read the digits back with `getComputedStyle(e, "::before").content`
— which computes to the SPECIFIED value, `"0" counter(band)`, never to the
resolved string. The regex matched that literal `"0"` and the sweep reported
**nineteen of forty-seven families broken when not one of them was.** The
digits a reader sees cannot be read back from the DOM at all, so the
assertion is the STRUCTURE that makes the sequence right and needs no digits:
one reset on `main`, every element that increments also draws, every drawn
index sits inside something that increments. Given those three the numbers
are 1..n by construction — and each half is a defect this has already had.

**AND THE INVARIANT REGISTER ASKED THE RIGHT QUESTION ABOUT THE MERGE.**
`primitives.reach.row` fell 0.887 → 0.769, because the pages whose only other
list was that duplicate band lost their last `.row`. The floor exists to
catch *a family growing its own components*, and this is the opposite — a
removal of duplication onto a primitive that already existed — so it moved
deliberately, with the reason in `tools/invariants.py` rather than in the
register it generates.

**And two tokens that do not exist reached the stylesheet in the commit that
documents them.** `--sans` has never been declared (the token is `--ed-sans`,
itself `var(--text)`), and `line-height: 1.45` would have been a ninth where
the register holds eight. Both were caught in the same run — the first by the
unresolvable-`var()` check, the second by `css.line_heights` — which is the
whole argument for those two guards existing.



**THREE PAGES, THREE INSTRUMENTS, AND /experiences WAS FORTY-TWO ROWS OF ONE
COMPONENT.** /discover asks what you are looking for and answers with an
instrument; /countries asks where it is and answers with geography; this one
asks what you want to DO, and the only honest answer to that is a photograph.
What it had was one photograph, a strip of eight, and then 24 experiences, 8
category bars and 10 kind bars — every one of them a `.row`. Nothing in it was
wrong: the bars are a real comparison and putting the experiences before the
taxonomy was itself a repair. The fault is the sum, and it is the data's shape
as the layout — the finding that rebuilt /journeys, /europe-in, /themes and the
stories index, arriving last on the family that could least afford it.

**AND THE LIBRARY WAS NOT THE CONSTRAINT, WHICH IS WORTH SAYING ONCE.** The
standing answer to "why does a travel site have so few pictures" is the
register, and on this page it does not apply: 311 photographs are licensed,
including all eight categories, all nine macro regions, the hero and 65
destinations, and every one of the ten kinds happens somewhere this atlas holds
a picture of. Nothing was acquired. The pictures were already bought and were
being spent on one strip. 1 photograph to 28, and the page is 32.1% photograph
at 1280 and 45.6% at 390 against /discover's 5.2%.

**TWO OF THE BRIEF'S TWELVE BANDS ARE REFUSED AND EACH SAYS WHY.** *Seasons*
is four authored claims: an experience record carries a slug, a name, a kind, a
band and a summary, and **no season and no month on any of the 197**. The
nearby temptation is worse than the refusal — the destinations carry month
data, so the band could be built from WHERE the thing happens and labelled as
though it were about the thing, which is the `pop_line` failure, where coverage
that depends on a different field being present looks like a policy. The
trigger is a `season` field on the experience record. And *choose your Europe*
is the same ten kinds a third time: the index band already prints all ten with
their counts and a place, so a natural-language restatement of them is the
fault this file records about a place page printing one set as a strip and
again as rows.

**KIND BY MACRO REGION, AND THE AXIS WAS CHOSEN BY MEASURING BOTH.** Two
thirds of every experience here is `family` or `adventure` — 131 and 124 of 197
— so their regional breakdown says EVERYWHERE, which is true and is not an
insight, and is the exact sentence `docs/signature-moments.md` refuses a
category map for. The KINDS are exclusive and the answer changes: the water is
the Nordics (11 of 25), the sacred sites are the Mediterranean (8 of 13), the
wildlife is the Nordics (6 of 10). A kind whose largest corner holds under a
third of it is left off the band rather than printed with a number that reads
as a finding.

**A CLASS NAME ALREADY IN THE STYLESHEET IS A RULE YOU INHERIT SILENTLY.**
This file records the rule against a second NAME for one colour twice.
`.doorgo` is the other end of it — one name for two things — and it had no
guard at all. The name belongs to the homepage's four doors, which reveal
their go-link on hover: `opacity: 0` at rest, declared hundreds of lines above
the composition that reused it. So the two links closing /experiences were
present, placed, sized, keyboard-reachable and painted at zero alpha, and
**nothing on this site could see it**: `getComputedStyle` reads `visibility:
visible` and `opacity: 1` on the link itself, because the zero is two elements
up; the contrast sweep reads declared colours and the ratio was right; the
clipping scan asks whether an element holds more text than it shows and it
showed all of it; the layout sweep measured 732 x 21 in the right place. Only
walking the ancestor chain for the composited alpha finds it.

The browser suite now focuses **every link on every family** and asks
`checkVisibility({ checkOpacity: true })`. It focuses first on purpose: a
hover-revealed link is a real pattern this site ships — the four doors, the
licence credit on a photograph — and every one of those reveals on
`:focus-visible` too, because a link a keyboard reaches has to become visible
when it does. So one test admits the pattern and refuses the accident.

**AND THE PINE ROOM LOST TO THE WHITE ONE.** The stories plate was given both
`sheet-gal` and `sheet-pine`: the first paints `--white`, the second rebinds
the world's ink to bone, and both are (0,1,0) with `.sheet-gal` further down
the file. Bone on white, every word on the band, at about 1.1:1 — the fourth
specificity collision in this stylesheet that rendered as *the thing is simply
not there*. The answer is the same every time: not a third class, but stop
asking two rules to agree.

**A GRID'S TRACKS ARE POSITIONAL AND THE MARKUP ORDER IS THE LAYOUT.**
`3rem 9.5rem 1fr 7rem` with the kind rows written number, name, picture put
"Walk or hike" in a 152-pixel column and the photograph in the 768-pixel one:
a 1,024-pixel-tall crop, ten times, and a band **11,127 pixels long**.

**TWO TILES DREW ONE PHOTOGRAPH, WHICH IS *ONE THING, ONE PICTURE* FROM THE
OTHER END.** The obvious picture for "the water is the Nordics" is
`macro:nordic` — and the museums are the Nordics too, and the cellars and the
tables are both the Mediterranean, so four tiles came out as two photographs
side by side twice. Not one record with two pictures; one picture on two
records. The tile takes a photographed DESTINATION inside the group instead,
which is more specific anyway, and a key already spent is skipped.

**AND `columns` PACKS WHERE A GRID ALIGNS.** The eight categories are drawn at
four scales — large, narrow, panoramic, intimate — and a two-column grid makes
a row as tall as its tallest item, so a 21:9 panorama beside a 3:4 portrait
paid 340 pixels of empty page for the difference, four times down the band.
1,400 pixels. `columns: 2` with `break-inside: avoid` is the whole fix, and the
column-major order is correct here because it is largest-first down the left.

**LAZY IMAGES DO NOT LOAD FOR A FULL-PAGE SCREENSHOT.** `loading="lazy"` keys
on the viewport and `fullPage` stitches without scrolling, so every picture
below the fold photographs as an empty box — and an empty box under a scrim
looks exactly like a photograph that is not there. The first sheet of this page
showed eight grey rectangles and was read as eight missing photographs; the
register held all eight. Any instrument that shoots a page taller than the
viewport has to scroll it first.

**AND THE STYLESHEET SHIPPED 1,813 DUPLICATED LINES IN HEAD.** An edit wrote
the whole plate-and-discover region twice with 50 KB of other rules between the
copies, so the later copy silently overrode every rule written between them —
which is why `.sheet-response { display: block }` had lost. A second, 85-line
copy of *the one window* was found the same way. Both were asserted
byte-identical before deletion and the homepage was shot at 1280 and 390 before
and after, **byte-identical at both widths**, because nothing here is deleted
on a scan's word alone. A comment beside the white wall claimed `checks.py`
asserts no other page takes `--white`; **no such check exists, in that file or
in any other suite**, and /discover has taken it for three rests since it was
rebuilt. A comment claiming an assertion that does not exist is worse than no
comment, because it is read as evidence.


**A ROOM WHOSE GROUND IS WHITE IN BOTH PREFERENCES NEEDS INK THAT IS DARK IN
BOTH, AND TWO OF THEM TOOK `--ink`.** The gallery wall is `--white` whatever
the system is set to, and `--ink` is bone in the dark preference — so the
homepage's own `<h1>Open the door to Europe.</h1>` measured **1.14:1** for a
reader whose system is dark, and `Europe is not a checklist.` on the next
plate measured the same. The h2 and the lede were saved **by accident**, by
`.sheet-gal .mega { color: var(--ink) }` resolving to the same wrong value
they had already inherited — which is exactly why the dead-rule scan kept
reporting those two colour rules as changing nothing. **They were redundant
in the light preference and the only thing standing between the dark one and
this defect, and they were not enough.** `.sheet-paper` on /discover has done
it correctly since it was written: a band binds the eleven tokens rather than
naming `--ink`, because a `var()` resolves where the DECLARATION lives.
1.14 → 18.04, and the redundant rules went with the fix rather than before it.

**THE LIVING ATLAS SEQUENCE WAS BUILT, MEASURED AND REMOVED.**
`heroeurope()`'s own comment said the first frame of each featured country
carries `href` and *"the others carry `data-href` and are fetched by the
ENHANCEMENT the first time they are shown"*. There is no enhancement: this
page's only `<script>` is the inert JSON-LD block, so the held-back frames
were never fetched and never shown, and `.herophoto image { opacity: 0 }`
read as a dead rule for the right reason — the only elements it applied to
had no `href` to draw. That is the `data-rotate` failure, found this time by
an instrument rather than by reading.

**Writing the rotator was costed and refused on the numbers.** The sequence
is a country's own photograph followed by its photographed DESTINATIONS, and
the register holds destination photographs inside exactly ONE of the six
featured countries — France has four frames and the other five have one
each. An enhancement would put the first JavaScript on the homepage to
cross-fade one country, which is the trade the nine restraint marks were
removed over. The trigger is the library: when several featured countries
hold photographed destinations it is about forty lines and two lines of
markup.

**THE PICTURE IS BOUNDED AND THE WINDOW IS NOT, SO NINETY PIXELS OF WALL
SHOWED THROUGH THE OPENING.** Plate 03's photograph is capped at 16/9 of the
viewport width — deliberately, because a viewport-filling slot guaranteed 9%
of a photograph's frame at some window shapes against 35.5% for this one — so
at 1280×900 it is 1280×720 inside an aperture 900 tall on screen, with the
band's white above and below it, and at 390 a 4:5 picture in an 844-tall
window. Filling the viewport puts the crop box back to 9%, which is a licence
cost rather than a layout one. **The opening paints its own ground instead:
light wall, dark opening, and what a gallery does with a picture smaller than
its frame is MOUNT it.** The assertion moved with it — *the picture fills the
window* was true while it was `inset: 0` and stopped being true the moment
the crop box was measured, so what is held now is that the gap is the
OPENING's ground and not the wall's, measured as the step between the two.

**A CLASS NAME ALREADY IN THE STYLESHEET IS A RULE YOU INHERIT SILENTLY, AND
THE STYLESHEET HELD 85 IDENTICAL DUPLICATED RULES.** `.doorgo` is the first
half: it belongs to the homepage's four doors, which reveal their go-link on
hover at `opacity: 0`, so two links closing /experiences were present,
placed, sized, keyboard-reachable and painted at zero alpha — and
`getComputedStyle` reads `opacity: 1` ON the link, because the zero is two
elements up. The browser suite now focuses every link on every family and
asks `checkVisibility({ checkOpacity: true })`; it focuses FIRST, because a
hover-revealed link is a pattern this site ships and every one of those
reveals on `:focus-visible` too.

The second half is the mechanism behind three defects in one session: a
selector declared twice with an identical body, where the later copy wins and
the earlier is invisible. 85 of them. **Removing the EARLIER copy is a
cascade no-op by construction** — the later still applies and everything
between them loses to it exactly as before — and it was proved rather than
argued: sixteen pages shot at 1280 and 390 before and after, 32 of 32
byte-identical.

**AND THE DEAD-RULE SCAN NAMES DECLARATIONS RATHER THAN RULES.** It reported
`.featlead {display,color}` and the first deletion pass removed the whole
rule, taking `text-decoration: none` with it — the homepage's two story links
came back underlined at both widths. The before-and-after screenshots are the
only reason that is a sentence here rather than a defect.

**FIVE ASSERTIONS WERE READING NOTHING, AND BOTH WERE FOUND THE SAME WAY.**
`.sheet-landscape` does not exist — the window plate was renamed
`.sheet-bleed` — so four contrast assertions and the one that proves the
picture stands still while the page scrolls had been dark since the rename.
And `.qtile`, the homepage's row of theme photographs, appears on ZERO pages
and in no page builder: its check has been printing *"it examined 0 states"*
since the homepage became the plate sequence — its own guard working, and
nobody reading the number — and its five stylesheet rules sat in the file the
whole time. **A count is only evidence if somebody reads it**, which this file
already says, about a different check, for the same reason. The check moved
to /discover's `.moswrap`, which is the same promise in a stronger form.

**AND A COMMENT CLAIMED AN ASSERTION THAT DOES NOT EXIST.** Beside the white
wall: *"`checks.py` asserts that no OTHER page takes it"*. There is no such
check in that file or in any other suite, and /discover has taken `--white`
for its three rests since it was rebuilt with nothing going red. A comment
claiming evidence is read as evidence.


**THE JOURNEY ATLAS, AND AN UNRESOLVABLE `var()` MADE THE DATA-CUT FADE THE
ONLY THING PAINTING SEA.** /journeys was `indexhero()` over seventeen rows —
the right rows, and the family's own signature drawing was built on every
build and thrown away, because `indexhero` prefers a photograph and the
seventeen routes at once were never asked for. They are the opening now. And
the panel that holds them took `background: var(--map-sea)`, which is the
name `docs/palette.json` uses where the stylesheet's token is `--atlas-sea`:
the declaration is invalid at computed-value time, `background-color` does
not inherit, and the panel fell back to `transparent`. **The drawing paints
no ocean of its own — the panel does** — so the routes sat on the band's
white and `cut_fade()`'s two ramps were the only sea on the picture.
Measured on the pixels: rgb(255,255,255) off Iberia and rgb(221,232,231) in
the Black Sea, on one drawing. The fade exists to stop a straight data cut
reading as a rendering fault and, with nothing under it, **was one**. Nothing
counts a background that is not there; a four-line scan for a `var()` with no
declaration finds it in a second, and this stylesheet already carries the
paragraph saying so.

**TWO DRAWINGS OF THE SAME EIGHT THINGS, ON DIFFERENT GRIDS, TOUCHING.** The
rhythm band draws one journey's legs twice: a bar whose eight segments are
their share of the whole trip, and under it a five-across grid of equal
tracks. Segment three does not sit over Piran and never can. Both drew the
same 2px accent rule twenty pixels apart, so the bar read as a mis-drawn
header for the grid rather than as the measurement it is. The bar is a
captioned `<figure>` now — stating what it draws, the way every chart here
does — and the cards' rule is the page's hairline. **Nothing counts a rule
that reads as a promise it cannot keep.**

**AND THE REGISTER WAS CLAIMING A SURFACE THE PAGE HAD STOPPED REACHING.**
`journeys-hero` is a licensed photograph of a train in a forest and the old
index opened on it; the moment the opening became the drawn continent nothing
asked for that key, and `c_photo_published` said so in the first run after the
rebuild — the check earning its place on exactly the fault it was written for.
It does not go back into the opening: *a photograph replaces the drawing, it
does not sit behind it*, and the drawn continent is the one picture here no
competitor can reproduce. It carries the CLOSE instead, as a declaration —
type over the picture behind a scrim, 72% graphite compositing to
rgb(76,83,82) and bone on that measuring 6.90:1 whatever the frame turns out
to be, which is `.credit`'s own arithmetic rather than a second number for one
decision. Ten `<img>` where the page drew one, and **nothing was acquired.**

**A PLATE SEQUENCE HAS NO ROOM FOR A STAGE ABOVE ITS OPENING, SO THE HEAD IS
THE BAND THAT INTRODUCES THE SET.** /journeys had no `pagehead` at all and
stated no extent, and `checks.py` failed on both. /experiences had already
settled it one family over. The seventeen band declares `index` and states
the count, derived — because *an index exists to say how big a set is*, and a
figure typed there is the figure that was true two hundred destinations ago.

**AND THE PACE SENTINEL WAS PRINTED AS A CLAIM.** The last of the three paces
has no ceiling, and the first version used `10**9` as the loop's upper bound
and then set it in the sentence: *"under 1000000000 km a day"*, on the page,
to a reader. **A bound that exists for the arithmetic is not a bound that
belongs in a sentence.** The three names are editorial and the number is
derived, which is the Data Integrity Rule in both directions on one band.

**THE GATE SUITE CRASHED THE DAY THE HOMEPAGE HERO WAS FILLED, AND THAT IS
THE EMPTY-REGISTER FAULT FOR THE FOURTH TIME.** `photo-tests.py` runs against
the LIVE register and `acquire.py` refuses a purpose the register already
fills, so the block that acquires a PNG for `homepage-hero` stopped acquiring
the moment run #32 put a real photograph there. Its own `returncode == 0`
assertion caught that — and the very next line opened the file the acquisition
had not written, so the **suite ended on a traceback instead of on one
failure**, leaving every later block unrun. A run that ends on a `TypeError`
reports no failure, which this file already records about the browser suite;
the same sentence now applies to the gate that guards photographs. **A block
that must SUCCEED owns its starting state**, so it frees the purpose first and
`cleanup()` restores the whole register from the backup it already held.

**AND FREEING THE ROW WAS NOT ENOUGH, BECAUSE A FILE NAME COMES FROM THE
PURPOSE.** The first version of that fix restored only the register — so the
acquisition it enabled wrote its stub straight over
`photographs/homepage-hero.original.jpg` and
`photographs/country-hero@austria.original.jpg`, two licensed originals, in
the one directory that exists to be evidence. `cleanup()` then put the
register back, so it named a SHA-256 of bytes that were no longer in the
repository, and `checks.py` said exactly that: *"the file is not the file that
was acquired"* and *"the original is not in the repository"*. `keep` protects
a file from being DELETED and says nothing about it being overwritten, which
is the sister failure to the run that swept 165 licensed derivatives out of
`assets/img` — same suite, same directory, opposite verb. **A test that frees
a surface moves its files aside and `cleanup()` moves them back**: a rename is
cheap and it is the only form of this that cannot lose bytes the repository is
the evidence for. Found because the run left the working tree dirty and the
static suite was run on it rather than only on the build.

**A 76px HEADLINE IN A 461px COLUMN STRANDS ITS LAST WORD AND
`text-wrap: balance` CANNOT HELP.** Measured at 1280: "The Adriatic Run"
needs 486 units of glyph and the featured band's type column gives 461, so it
must break — and 364 + 122 is the best split balance can find, because the
heading is three words and the last one is short. The browser suite reported
it as *balance being overridden*, which is a true report of a real defect
naming the wrong cause: balance IS applied and is doing its job. **The
proportion is the feature scale doing what it is for** — a feature is
asymmetric at 1.35 against .65 so the PICTURE is the subject, which makes the
type column narrow BY DESIGN — so the name takes the section step rather than
the opening one. `--ed-display-2` is already spent as a font-size in eight
rules, so no type value is added, and at 1280 the name sets on one line.

**And a reason stated on one of two rules is a reason applied to one of
them.** `.journeyrow .jfacts` carries the comment *"`.row .rowmeta` already
sets `--ink-3` and every `.jfacts` is one, so restating it is a declaration
that changes nothing"* — and the base `.jfacts` rule four thousand lines down
put the declaration straight back. The dead-rule scan named it in the first
run after /journeys was rebuilt. This stylesheet's most repeated shape,
arriving inside one property of one component.

**AND THE ART-DIRECTION SHEET WAS THREE REDESIGNS BEHIND, IN THE ONE
ARTEFACT WHOSE JOB IS TO SHOW A PERSON THE REAL COMPOSITION.**
`contact_sheet.py` renders the actual homepage once per candidate so somebody
can judge a photograph inside the page before it is bought. Its `RENDERABLE`
set still named `door-coast`, `door-food`, `door-history` and
`door-mountains` — four purposes deleted with the composition that held them
— and `SURFACE` mapped the hero to `.herofull`, gone in the same commit. The
suite's own assertions then named `class="opening"`, **the fourth spelling of
where the hero lives, written in a comment recording the third.** `home-hero`
renders on plate 02, the WINDOW, which is the container
`data/image-purposes.json` has declared since the crop box was measured.

**And one promise had to be restated rather than repointed.** *A photograph
replaces the drawing; it does not sit behind it* was true while both were the
same surface. On a plate sequence the opening draws the continent and the
window carries the photograph: two plates, coexisting by design. So the
assertion is no longer "the drawing is gone" — it is that the candidate went
into the window rather than over the drawing, which is the defect the
original sentence was written for, stated about the page that exists. The
window also writes its own credit (`credit=False` to `picture()`), so "Photo
by" — the figcaption's wording — was never on that surface.

**AND A GUARD ON A TUPLE IS ALWAYS TRUE.** `has()` returns
`(bool, message)`, so `_jp = has("/", 'class="jrows"')` is a non-empty tuple
whatever the bool inside it is: `not _jp` was constantly False and the guard
written to make two assertions conditional fired never. Same fault as the
dead-rule scanner recursing into an EMPTY `cssRules` list because an empty
list is truthy — a container standing in for the boolean inside it, and the
message it printed was about the assertion it was meant to be guarding.

**AND THE HOMEPAGE'S OWN BUILDER CRASHED ON AN EMPTY PICK LIST, IN THE ONE
CALLER THAT MAKES ONE.** `picks` is one photographed destination per macro
region, so it is empty for a register holding none — which was every register
before the first tranche merged, and is the register `contact_sheet.py` builds
when it renders this page once per candidate: it swaps in ONE row so the sheet
shows that candidate and nothing else. `picks[0]` raised IndexError and took
the acquisition suite down with it. **Every other band on that page is already
guarded** — `if inner` in the plate loop drops an empty one — and this was the
one that could never produce an empty string, because it died first. The
crash-stops-counting fault arriving in a page BUILDER rather than in a gate.


**THREE CLASS-NAME COLLISIONS ON ONE PAGE, FROM THE TWO MOST OBVIOUS NAMES,
AND THERE IS NO GUARD.** *A class name already in the stylesheet is a rule
you inherit silently* is recorded above about `.doorgo`, whose `opacity: 0`
made two links on /experiences present, placed, sized, keyboard-reachable
and painted at zero alpha. /plan's closing band hit it twice in a row:
`.sendsay` is /journeys' close — a centred statement over a photograph
behind a 72% graphite scrim — and sets `color: var(--bone)` on its own
heading and lede, so on a white wall the last thing the page says measured
about **1.1:1**; `.closesay`, the obvious second choice, is the closing band
on the homepage and /discover at `max-width: 32rem`, so the statement came
out 512 pixels wide inside a 1,152-pixel band, centred inside its own cap
and therefore off-centre in the room. The third was a `.deskart figcaption`
rule written twice with an identical body eighty lines apart — one of the 85
duplicated rules the previous commit removed, reintroduced within the hour.
**Grep the stylesheet before naming a composition.**

**A RUNTIME `<img>` IS INVISIBLE TO THE GUARD THAT REFUSES AN UNREGISTERED
FILE, WHICH MAKES IT THE WORST PLACE IN THIS PRODUCT FOR A SECOND
IMPLEMENTATION.** `checks.py` reads the shipped HTML for a page referencing
a photograph with no register row. `planner.js` writes an `<img>` for a leg
whose stop the register holds a picture of — 63 of the 313 destinations the
planner can route through — and that check has no reach there at all. So
composing Pexels' attribution in JavaScript would have been a second copy of
a **licence obligation** with nothing on either end able to go red, and the
breach would be of somebody else's terms. `render.credit_html(row)` was
lifted out of `picture()` and is the one implementation: `picture()` calls
it, `planner_api()` calls it, and the fragment travels in the index as
`cities.shotCredit` beside `shot` and `shotAlt`, each declared in
`data/contracts.json` with its reason. The terms are the gate's own recorded
answer, verbatim — *"make sure to show a prominent link to Pexels … Always
credit our photographers when possible (e.g. 'Photo by John Doe on Pexels'
with a link to the photo page on Pexels)"* — and each leg tile carries both
links. `atlas.json` 317,645 → 346,303 bytes, 9.0%, recorded.

**`--atlas-*` IS A ROLE THAT RESOLVES PER WORLD AND `--map-*` IS THE
PALETTE, AND A COMMENT CLAIMING THE SECOND WAS WRITTEN OVER THE FIRST.**
`.planmap .constel` — the planner's own route figure — carries the sentence
*"this is a picture inside an instrument, and it takes the picture's
palette"* and painted `background: var(--atlas-sea)`. That figure only ever
renders on /plan and /my-europe, both INTELLIGENCE, so for the life of the
rule it took the instrument's near-black: invisible while those pages were
dark throughout, and a black slab the moment /plan's bands became bone.
Measured on the built result, the svg's own background computed
`rgb(7,16,15)` inside a band of `rgb(248,246,239)`. That is the /journeys
`--map-sea` finding from the other end — there a token that does not exist
fell back to transparent; here a token that does exist resolved to the other
set, and only one of the two is visible to a scan for an unresolvable
`var()`.

**A SOURCE RULE REACHES A `<use>` CLONE ONLY WHERE THE SELECTOR MATCHES THE
CLONE'S OWN POSITION, WHICH REFINES WHAT THIS FILE HAD SETTLED.** The
planner's route figure clones /plan's country rings — `#constel-eu` is one
thinned lod0 silhouette with no internal boundaries, right for a 132-pixel
theme glyph and 736 pixels of flat stone with a green zigzag on it for a
three-stop route that never leaves central Europe. Measured, the `<use>`
computed `rgb(216,212,199)`: the fill `.planmap`'s own rule sets, where
`.instrmap .countries path` would have given it the ink coast. Writing
`.planmap .constel .countries path` did not reach it either. What draws
every boundary is the anti-aliased edge between two adjacent country fills,
one device pixel at every frame — and **two strokes were tried and both are
refused**, because `stroke` is inherited and `vector-effect` is not, and
`glyphView` frames 340 to 1,000 units so a user-unit stroke is three times
wider on a city break than on a continental crossing.

**A SCRIM THAT RUNS DIAGONALLY IS WEAKEST AT A CORNER OF THE COLUMN IT
EXISTS TO COVER, AND A PALE WASH CANNOT SAVE DARK INK.** /plan's first
composition held the drawing as the band's full-bleed ground with the form
over it. Measured with the column's words removed, the ground ran **0.055 to
0.789 of luminance at 1280 and 0.007 to 0.789 at 390**: the head read on
flat water and the prose, the button and the extent figures sat on bare
drawing over 313 cobalt dots, the h1's `#141716` at **1.81:1** at 1280 and
**1.02:1** at 390, on a form. Moving the wash onto the form fixed the ratio
at every height and cost half the continent — Iberia, Ireland, Britain,
France and western Norway under an opaque panel, the dots showing through
the ramp as a field the eye keeps trying to resolve, and a terminator down
the middle of Europe that nothing in the drawing had drawn. **So the overlap
went instead**: two tracks, no scrim, and the band's paper IS `--map-water`,
so the drawing's own ocean and the band's ground are one colour and there is
no seam to see. 14.41:1 for the title, 11.43 for the kicker and the prose,
4.72 for the label, by construction. **And the first sampler hid the scrim
it was measuring** — `visibility: hidden` on the column hides its own
`::before`, so the run reported the ground the scrim exists to replace,
which is this instrument's own recorded failure inside the instrument
written to find it.

**AN `aspect-ratio` ON A CONTAINER THAT ALSO HOLDS PROSE IS A PROPORTION
SHARED WITH THE PROSE.** `.deskart { aspect-ratio: 1000/780 }` sat on the
`<figure>`, which includes its caption: measured at 390 the figure was
390×304 and the caption took 231 of it, so **the whole of Europe rendered 73
pixels tall** on the band that says the planner works across the continent.

**THE CONTEXT LAND IS A HERO DEVICE AND THE GRAPHITE IS WHAT MAKES IT
WORK.** A warm slab with three straight edges sat in the sea south-east of
Baku on /plan's desk drawing. The eye said "a clipped fragment of a country
with no destinations"; `isPointInFill` said **Georgia, Armenia, Azerbaijan
and Türkiye** — the Caucasus, correctly drawn, whose eastern side is the
52°E cut `dusk_reach()` deliberately does not hide so Baku and Tbilisi keep
their ground. *The eye finds a defect and it does not confirm one.* A
tighter grid found the real one: **Iran and Iraq, in the CONTEXT layer**,
clipped into a slab. /map and /discover keep that layer and the same slab on
the same projection is invisible there, because near-black absorbs its
straight edges — and `--atlas-far` (`#C3BFB2`) is DARKER than the light
map's water rather than lighter. The wide fade hides it and takes the ground
out from under Baku with it, so the layer with no claim to make on this
drawing is the one that goes.

**"NOTHING HAS BEEN BUILT YET" UNDER A BUILT ITINERARY.** `#atrest` was new
and `planner.js` had never heard of the id, so the sentence stayed on the
page under four legs, a cost breakdown and a route map — *removing a claim
leaves surfaces pointing at it*, arrived at from the other side.
`#result:not(:empty) ~ .atrest { display: none }` decides it from the DOM
rather than from a flag somebody has to clear: the sentence shows if and
only if the element it describes is empty, and it cannot drift because the
condition IS the thing it is about.

**A CHART WHOSE VALUE SAT SIX HUNDRED PIXELS FROM ITS BAR.** *A chart on
which four of seven series cannot be seen is the wrong track* was a share of
319 on an 80-pixel track; this is the same fault inverted. /plan's weighting
bars had a `minmax(0, 1fr)` track — 896 pixels at 1280 — and a bar is a
share of ONE HUNDRED, so the largest weight can never exceed 30% of it:
"Your interests" drew 245px and its "30%" sat at x=1,167. The scaling did
not move, because *the bars are still scaled by the series they are labelled
with* and a share-of-the-largest version would read as 100%. The number
moved, to the end of the bar it belongs to. And **the two constants are
declared once now** — `PLAN_WEIGHTS` sums to 100 and `PLAN_STYLE_POS` is
asserted equal to `planner.js`'s own `STYLE_DAILY`, because a second copy of
0.5 is a second chance for the page and the planner to disagree about what
"comfortable" means.

**A SPENDING STYLE IS A POSITION IN A PLACE'S OWN BAND, AND THE BAND
PUBLISHED THREE SENTENCES AND NO NUMBER.** `STYLE_DAILY` is
`{low: 0, moderate: .5, high: 1}` — the bottom, the middle or the top of the
daily range this atlas already records for each destination — which is the
one measurable thing about the three styles and was invisible. €60, €105 and
€150 now, each a median over the 313 with its spread beside it, derived on
every build. *The Data Integrity Rule in both directions on one band*: the
three names are editorial and every figure is derived. **And the field is
`daily_eur` on the COUNTRY** — two wrong readings in a row, `daily` (which
is the name `atlas.json` publishes it under) and then the city, and both
raised rather than shipping a number, which is the right way round.

**A BAND WHOSE SUBJECT IS A LIST OF REFUSALS HAD ONE SENTENCE IN IT.** 787
pixels for a headline, a lede and a note in the left half, on the band that
carries this product's whole position. Six refusals now — no booking, no
hotel price, no advisory routing, no weather, no step-free promise, no road
distance — and **not one is written there for the first place**: each is
already published on this site and the row says where, because a refusal
nobody can check is a slogan.

**AND FOUR BANDS PUT THEIR HEAD IN THE LEFT HALF.** `.sheettext` is a
one-column grid, which is right on /discover where each plate's text is one
of two tracks, and /plan's bands are `display: block` — so the h2 took its
own measure and the lede sat UNDER it at 361 pixels inside a 1,152-pixel
band. `render.section()` had already answered this for three quarters of the
site: the title at display size with its lede beside it. 1.1 against .9
rather than equal halves, because two equal columns read as a layout and an
unequal pair reads as a statement with a note on it, which is the feature
scale's own argument at 1.35/.65.


**/stories DREW ONE PHOTOGRAPH WHILE THE REGISTER HELD EIGHT FOR IT.**
`stories-hero` and seven `story:` rows, and the index spent one — which is
the /experiences finding word for word on the family whose material is
writing: *the pictures were already bought and were being spent on one
surface.* Nothing was acquired. 1 `<img>` to 8, 31,851 bytes to 53,278,
a head and eight identical rows to seven plates.

**AND THE BRIEF'S DESK BAND IS REFUSED BY A COUNT: NINE DESKS AND NINE
STORIES IS A 1:1 MAPPING.** A band of desks is nine headings over one item
each, which is literally the layout this page was built as and threw away.
Three more of its asks go the same way: `author` is "EuropeDoor editorial"
on all nine so a byline band prints one name nine times; 36 tags across the
nine and 34 used exactly once, so a tag index is a scatter with no
structure; and the nine run 5 to 9 minutes, which is not a choice a reader
makes. **And the lead cannot be the photographic one**: the page picks its
lead by DATE and says why — *a date, not a judgement* — and the newest piece
is filed to Adventure, one of the two the register holds nothing for. So the
opening carries the page's own photograph and no story's title, and it
becomes photographic on its own the day the register holds Adventure.

**FOUR CLASS-NAME COLLISIONS ON ONE PAGE'S RUN, AND THERE IS NO GUARD.**
This file already records `.doorgo`, whose `opacity: 0` made two links on
/experiences present, placed, sized, keyboard-reachable and painted at zero
alpha. Building /plan and /stories produced four more, every one from an
obvious name: `.sendsay` (/journeys' close, bone on a white wall at about
1.1:1), `.closesay` (the homepage's close at `max-width: 32rem`, so a
centred statement came out 512 pixels wide inside a 1,152-pixel band),
`.sheet-send` (/journeys' graphite photograph band, so a bone publication's
last words rendered on near-black), and a `.deskart figcaption` rule written
twice with an identical body eighty lines apart — one of the 85 duplicates
the previous commit removed, reintroduced within the hour. Not one is
visible to any suite here. **Grep the stylesheet before naming a
composition.**

**A RULE MEASURED ONLY WHERE IT LOSES LOOKS LIKE A RULE THAT WINS NOWHERE,
FOR THE THIRD TIME — AND THE THIRD TIME THE ANSWER WAS A PAGE.** The
dead-rule scan reported `.sheet-paper {color}` dead. Removing it in the
browser turns every word on /discover's six light bands from
`rgb(20,23,22)` to `rgb(243,240,230)`: bone on bone, on the page the whole
room system was written for. The scan's page list carries
`/discover/nordic` — a macro REGION page — and no `/discover`, no
`/experiences` and no `/journeys`, so the only page in it that has ever
held a `.sheet-paper` band is /plan, where `.sheet-desk` set the same
colour later at the same specificity. **The redundancy was mine and it is
the half that could be removed without widening the instrument**; adding the
three indexes takes the population from 381 rules to 506 and the dead list
from 42 to 71, with 31 fresh, which is its own commit with its own triage
and is recorded in the check rather than done here.

**AND ELEVEN DECLARATIONS WERE DEAD BECAUSE A ROOM ALREADY SAID THEM.**
`.sheet-gal` ends `display: block`, so `.sheet-planctls`, `.sheet-planres`,
`.sheet-styles`, `.sheet-wont` and `.sheet-close` each restated it; a base
`.sheet-engine { grid-template-columns }` made `.sheet-pine { display }`
unable to move a pixel, because `display: block` and a one-column grid
render identically with one child per row; `.deskart svg { display: block }`
and `.instrmap { display: block }` were two rules setting one value, so the
scan named both; `.wbar` is a flex item and `.instrmap` is a grid item on
both its users, so each is **blockified by the layout** — the fifth and
sixth of that finding on this stylesheet's record.

**`overflow-wrap: break-word` DOES NOT REDUCE A MIN-CONTENT CONTRIBUTION,
AND `justify-items: start` PINS AN ITEM AT ITS OWN MIN-CONTENT.** /plan
scrolled sideways by 16 pixels at 320: "A published method, not a mysterious
recommendation." and the word `recommendation.` is 320 pixels of glyph at
the 48px clamp floor, so `.sheettext`'s implicit `auto` track took that as
its minimum and the h2 rendered 320 wide inside a 288-pixel band. Flooring
the track at `minmax(0, 1fr)` was necessary and not sufficient, because a
`start`-aligned item is sized fit-content and fit-content never goes below
its own min-content. **`anywhere` is the one value that lets a soft wrap
opportunity count toward min-content**, which is the distinction this
stylesheet had not had to make. Proved surgical: every `.sheettext` box and
every head inside one on /discover and /experiences is identical to the
pixel at 1280, 834, 390 and 320, and the single line that changed in the
whole matrix is /plan at 320 going from 16 pixels over to 0.

**AND THE INDEX HEAD INSIDE A PLATE IS ONE RULE NOW.** `.pagehead.index` is
a three-column head — the extent beside the name — which on a block plate
puts the kicker alone in the left half and starts the title at x=400.
/experiences wrote its own override; /journeys and /stories needed the same
one. *No new primitive until repeated structure has actually emerged* cuts
both ways: three users is emerged, and a second rule with an identical body
is the duplicate this stylesheet removed 85 of one commit ago.
`.sheet > .pagehead.index`, with /experiences shot at four widths before and
after and every box identical. /plan's desk head keeps its own rule, because
it stacks to a SINGLE column inside a 34rem form track.


**FIVE PAGES COMPOSED A PLATE SEQUENCE AND EACH SPELLED THE SAME LINE
ITSELF.** The homepage, /journeys, /experiences and /plan wrote one form and
/stories arrived as a fifth in a fourth spelling producing the same bytes.
`pages.plate_sequence()` is the one implementation now, and what it carries
is the mistake worth not repeating: **the number comes from the rendered
sequence, not from the declared list.** `enumerate(PLATES, 1)` filtered
afterwards numbers first and filters second, so an omitted band leaves a
hole — with a register holding one photograph the homepage printed 01, 02,
05, 06, 07, 08. *The selector that COUNTS is the selector that DRAWS*, which
this file records about two CSS counters and is equally true of a number
composed in Python.


**AN `<a>` INSIDE AN `<a>` IS NOT NESTED — THE PARSER CLOSES THE FIRST ONE,
AND THE RULE THAT REVEALS THE LICENCE CREDIT LOST ITS SUBJECT.** `picture()`
emits the Pexels credit as a `<figcaption class="credit">` INSIDE the
`<picture>`, at `opacity: 0` until `picture:focus-within`. /stories made each
picture tile a link, so the credit's two anchors sat inside one — and the HTML
parser is specified to end the outer `<a>` at the inner one, which made them
siblings of the tile rather than descendants of it. **21 links of 3,685
painted nothing even with focus on them**, on the two links Pexels' terms
require. That is `.doorgo` from the other end: there a class carried an
`opacity: 0` nobody expected, here the rule that clears it stopped having
anything to match, and `getComputedStyle` reads `opacity: 1` ON the link
either way. The tile is a `<figure>` with `credit=False` inside the link and
the credit in a `<figcaption>` outside it — which is also more visible than a
credit revealed on hover.

**A CLAMP SOLVED FOR EQUALITY IS NOT A CLAMP THAT FITS.** `.sheet .mega`'s
floor was made width-aware to stop `recommendation.` breaking mid-word at 320,
and the arithmetic was done BEFORE the change — 320 pixels of glyph at 48px
inside a 288-pixel column, so 43.2px, so 13.5vw — which is the repair this
file already records for the overture h1. It was still wrong: measured after,
the word came out **288.0 against a box of 288.0** and broke anyway, because a
word wraps when it does not FIT and equal is not smaller. *A floor one page
from its threshold is a check that fails without saying anything*, recorded
here about a palette ratio and true of a type clamp identically. 12.8vw is
40.96px at 320 and the headroom is 14.9 pixels rather than none; the floor
reaches the full 48 at 375. **All five users of that clamp take it**, because
one of them is the reason the other four have the declaration at all.

**AND TWO DECLARED CROP BOXES NAMED A CONTAINER NEITHER PAGE EMITS ANY
MORE.** `experiences-hero` and `stories-hero` both declared `.iheroart`,
which is `indexhero()`'s figure, and neither index calls `indexhero()` since
it became a plate sequence. *A selector that matches nothing has no aspect
ratio*, so the sweep reported no box larger than 4px at any of 40 viewports —
the green-assertion-about-nothing fault the crop-box measurement was rebuilt
to catch, arriving in the commit that rebuilt the pages it measures.
`.xshot` is 0.731–1.501 (frame 30.1%) and `.storybleed` is 1.778–2.333
(frame 47.2%); both clear the 12% floor.


**/countries DREW ONE PHOTOGRAPH WITH SIXTY IN THE REGISTER FOR IT, AND THE
BRIEF'S STRONGEST IDEA WAS ALREADY A MECHANISM HERE.** The page was an
`ed_opening()` over a 4:3 figure with nine macro bands under it. The register
holds a photograph of every one of the fifty countries, of each of the nine
macro regions and of the index itself — sixty pictures whose subject IS this
page — and it spent one. Third family in a row on the same finding: *the
pictures were already bought and were being spent on one surface.* 1 `<img>`
to 10, plus 10 SVG `<image>`, and **nothing was acquired.**

**THE COUNTRY IS THE APERTURE, AND `living_atlas` HAD ALREADY BUILT THAT
CLIP-PATH AND MEASURED IT OUT.** The brief asks for the photograph to appear
*inside France's geographic boundary* so the country itself becomes the door —
which is the one thing this atlas can draw that no competitor can, and which
the homepage tried and refused on its own numbers: *a photograph clipped into
Belgium renders about 40 pixels wide at 1280 and is a smudge with a
coastline.* **The frame was the variable, not the idea.** `country_door()` is
the same clip on the country's OWN extent, so Estonia fills its tile exactly
as France fills its own. **41 of 50 can be drawn this way and nine cannot, and
the nine are geometry rather than taste** — six have no polygon at 1:50m at
all and three are advisory. The page says so rather than quietly showing 41.

**AND THE FUNCTION'S OWN COMMENT OVERSTATED IT BY NINE**, reading *"every
country that has a photograph is an aperture, and all fifty do"* above two
filters that remove exactly those nine. *The code had stopped matching its own
comment*, in the direction that reads as evidence.

**THE BYTE BUDGET WAS RIGHT AND ITS STATED REASON NAMED A DOOR THAT IS NEVER
DRAWN.** All 41 drawable doors are **628 KB** of inlined geometry against a
`weight.max_page_kb` of 441, so the whole set is 187 KB over the largest page
this site may serve — a real constraint, and `DOOR_BAND_KB` spends 90 KB of it
and lets the page state how many that turned out to be, because a count picked
by eye would be taste. The comment justified it with *"Russia's outline alone
is 107 KB"*, and **Russia is advisory, so `country_door()` refuses it before
any geometry is read**: the costliest door that actually exists is Norway at
62 KB. The budget SKIPS rather than stops, so Finland — nine photographs and
an expensive coast — is passed over and Bulgaria, Albania and Armenia get in
behind it.

**NINE SILENT INCREMENTS OF THE SECTION COUNTER WERE ON THIS PAGE.** The macro
regions were `<section class="band macroband">` with the head inside a
`.bandtop` wrapper, so `.band > .band-head::before` never matched them and the
two numbered sections after them would have printed "010" and "011". That is
*the selector that COUNTS is the selector that DRAWS*, recorded one commit
earlier and live here the whole time; `primitives.reach.band` 0.768 → 0.767 is
the repair rather than a family growing its own components.

**THREE CLASS-NAME COLLISIONS, AND THIS TIME THE STYLESHEET WAS GREPPED
FIRST.** `.sheet-door` is the homepage's opening with 29 rules, `.doorgrid`
already exists twice, `.sheet-open` is shared with /stories — all three the
obvious names for these compositions. Five pages in a row have now hit *a
class name already in the stylesheet is a rule you inherit silently*, and this
is the first where it cost a rename instead of a defect. **And the first
rename went to the wrong occurrence**: `.doorgrid` at line 1822 is the
homepage's, line 2477 is this family's, so a grep returning two matches still
needs the right one read.

**A BLACK SEA ON EVERY APERTURE.** `.instrmap svg { background: none }` is
correct — *a map figure must paint no background* — so a new figure's own
`<rect class="lyr lyr-ocean">` had nothing to fill it and took the SVG
default. The plates escape it because they carry the cartography skin: **a new
figure inherits the geometry rules and not the paint**, which is the ten
unreached `<stop>` elements one component over.

**AND THREE MORE THE FIRST RUN CAUGHT, EACH BY A GUARD THIS FILE ARGUES FOR.**
`--warn-ink` has never existed (the token is `--warn`), found by the
unresolvable-`var()` scan. A `line-height: 1.24` one hundredth from the
existing 1.25 took `css.line_heights` to nine against a ceiling of eight — *a
rounding error with a token name*. And `data-role="illustration"` was put on
the `<figure>` where the check reads the `<svg>`. Then ten identical captions,
ten identical source notes and ten identical alt texts, which is *never
explain the constraint back*: `brief=` puts the sentence on the lead door and
the bare country name on the other nine.

**A CLASS MOVED FROM THE LINK TO ITS FIGURE AND THREE OF ITS FOUR
DECLARATIONS STAYED BEHIND — TWO DEAD, AND THE THIRD UNDERLINED SEVEN
HEADLINES.** `.picstory` on /stories was an `<a>` until the credit's own two
links made a nested anchor illegal; the fix put the class on the `<figure>`
and the anchor inside it, and left `display: block` (a `<figure>` already
computes it), `color: inherit` (`a { color: inherit }` already does it) and
**`text-decoration: none` on a box that is not a link**, while the UA's
`underline` went on applying to the anchor's own subtree. Measured by serving
the stylesheet with and without an override: **the seven story titles in the
photographed band were underlined**, 34px of display serif with a rule
through it, shipped by the commit that fixed the credit. **A dead declaration
was the SYMPTOM rather than the fault** — two of the three changed nothing
and the third changed the wrong element, and the dead-rule scan is the only
instrument here that looks for either. The decoration belongs on the thing
that is decorated.

**`Read the story` WAS AT `opacity: 0` ON EVERY DESK, AND THE GUARD ASKED
THE QUESTION OF THE LINK.** The /stories ledger lead's call to action was
`class="doorgo"` — the homepage doors' hover-reveal — put there by the
commit that wrote the paragraph recording what that class had already cost
on /experiences. Measured in Chromium: **544 × 33 at 1280 with computed
`opacity: 0` and `checkVisibility` false**, `opacity: 1` at 390, because the
only thing restoring it is a `max-width: 60rem` rule written for a phone. It
was the ONLY `.doorgo` on the built site. **And the sweep that exists for
exactly this passed it, correctly**: `.storylead` IS the anchor and the
anchor is visible, while the `<p>` inside it carries the alpha —
`checkVisibility` is false when the element or an ANCESTOR is transparent,
so asking it of every link cannot see a transparent CHILD, and the walk that
names the culprit starts at the link and goes up. **The guard was written
for the element that is the link, and a class carrying an unexpected zero is
not always the link.** A second sweep walks in: every descendant of a
visible link that holds its own words and paints nothing with focus on the
link. Proved red and green on the shipped page — 51 links, 0 hits as
shipped, 1 named with an injected zero.

**AND THE FEATURE STORY WAS REFUSED NEXT DOOR TO THE QUESTION IT ASKS.**
*The lead cannot be the photographic one* is about the LEDGER: it leads on
the newest piece, a date rather than a judgement, and the newest is filed to
Adventure where the register holds nothing. A feature asks which piece can
carry a photograph at size, which is a fact about the register and not a
ranking of the writing — so the two coexist, exactly as the brief's own
architecture separates its band 3 from its band 4. The ledger leads
typographically on Adventure; the feature carries **the newest photographed
piece the ledger has not already led on**, which is *The ferry is the
attraction*. Both derived, so the day Adventure is photographed the ledger
keeps its lead and the feature moves down one rather than drawing one piece
twice. The `pics` row drops the feature and states both figures: seven carry
a photograph, six are in the row, and the sentence says why.

**AND THE LEDE STATED ITS OWN EXTENT AND THEN NAMED SIX OF NINE.** *"Nine
desks — people, history, food, faith, nature and culture"*, with the count
generated and the list typed, so **Places, Travel and Adventure were absent
from the one sentence that introduces the publication.** `pop_line`'s shape
in a list rather than a field, with a derived figure beside it that
disagrees. **That is also where the brief's desk band lands, because a chip
is a FILTER**: this page loads no JavaScript and no per-desk page exists, so
ten chips would be ten controls that do nothing — `data-rotate` again.
Naming the desks is what the chips were for, and a name in the head is an
extent rather than a directory.

**A COMPOSITION THAT IS ONE CHILD OF A `.sheet` LANDS IN ITS 40% TRACK.**
`.sheet` is `grid-template-columns: minmax(0, 40%) minmax(0, 1fr)`, so the
feature's first version rendered **205 × 154 of photograph beside 137 pixels
of type at 1280**, the h2 one word per line, the second track empty. /plan
already recorded it — *`.sheettext` is a one-column grid and /plan's bands
are `display: block`* — and it arrived here in a commit whose own comment
says *the band contributes its room and its rhythm and nothing else*. A rule
stated and applied to none of its call sites.

**AND `.ed-feature-media` HAD NEVER HELD A `<figure>`.** There is no global
`figure { margin: 0 }` here — only `.ed-strip figure` and `.geoart figure` —
so the UA's 40 pixels either side ate **80 pixels at every width**: 278 of
photograph inside a 358-pixel column at 390. /stories is the first caller of
`.ed-feature` anywhere on the site, so the one thing a media box has to do
had never been exercised. *A code path nothing exercises is a code path
nothing checks*, about a component the 2036 brief declared and nothing used,
and the fix belongs on the primitive: the next band must not have to know
which element the last one chose. 752 × 564 at 1280 after.

**/events COMPUTED EIGHT FILTERS AND THREW THEM AWAY ON EVERY BUILD.**
`kindfilters` was composed inside `events_page` from the eight kinds and
their counts and the body f-string never mentioned it — the identical
variable in `events_month_page` IS that page's control, and this one was
dead. *An ignored argument is dead code that looks like a decision*, and it
is exactly why the brief's event-character band was missing: **the eight
were counted, rendered and discarded**, while the page closed on a
`<p class="small">` saying there were eight categories without naming one.

**AND NOBODY HAD CROSSED THE 150 FIXTURES BY MONTH AND KIND.** The brief
asks for a FIXED POINTS ledger and fills it with six authored groupings —
*Winter traditions*, *Spring awakenings*, *Harvest Europe* — which is the
right instinct with nothing behind it. Measured, the data says it better:
February is 10/13 cultural, April 9/15 religious, June 10/20 seasonal,
September 8/16 food, December 9/14 market. **And the busiest month is the
least characteristic** — July holds 28, more than any other, and no kind
reaches 43% of them, where February holds thirteen and 77% are one thing. A
crowded month is not a month with a character, which is a second argument
beside the shoulder one and is derived rather than written.

**"HALF OR MORE" IS SATISFIED BY 2 OF 4.** The first threshold reported
EIGHT decisive months, because March (3 of 6), May (2 of 4) and November (2
of 4) clear a share test on a handful of fixtures: arithmetically true,
editorially empty, and the small-sample form of *a count that is not the
set's own extent reads as one*. A month also has to hold at least an average
month's worth of the year, and **the average is derived rather than picked**
— 150/12 is 12.5, which admits exactly the five real ones and excludes
exactly the three that were noise.

**AND THE BRIEF'S OWN SHOULDER FIGURE WAS OUT BY ONE.** It asks for *26
countries in their quieter shoulder in October*; the dataset says **25**,
because the three advisory countries are excluded. *A number typed into a
design is the number that was true on the day it was typed* — this one is
counted on every build, against the 47 countries this atlas writes about.

**TWO OF THE BRIEF'S BANDS ARE ONE BAND, BECAUSE THEY ARE TWO VIEWS OF ONE
CROSS-TAB.** FIXED POINTS and EVENT CHARACTER printed separately is the same
table twice on one page — the fault 220 place pages had. One band carries
both axes: each kind's count with its own peak month, and the months where
one character holds. **The rows are `<div>` and not `<a>`**, because this
atlas has no per-kind page and a row that looks like navigation and leads
nowhere is the chip-that-filters-nothing one family over. **And the bar is
against the largest KIND rather than the total**: eight kinds summing to 150
would put `cultural` at 26% and read as a share of the year, where what the
row compares is one kind against another.

**AND AN F-STRING EXPRESSION CANNOT CONTAIN A COMMENT — NOR A BACKSLASH.**
`ed_opening` escapes its intro, so `&mdash;` shipped as the five characters
a reader sees; writing the reason for that fix beside the keyword argument
stopped the build with *"f-string expression part cannot include '#'"*,
which this file already records twice. The escape `\u2014` then failed with
*"cannot include a backslash"*. The character is written as itself and the
reason lives in the function above it. **A rule recorded twice is not a rule
inherited**, which is the third occurrence of that sentence about this one
construct.

**`.sheet-gal` ENDS `display: block` AND `.sheet-paper` DOES NOT.** Both
`paper` bands on /events would otherwise inherit `.sheet`'s `minmax(0, 40%)
minmax(0, 1fr)` and put their head in the 40% track — /stories' feature band
shipped with exactly that one commit earlier, a 205-pixel photograph at
1280. The year band is a twelve-column chart that cannot be read in 40% of a
page. And **both obvious names for the close were taken**: `.sheet-door` is
the homepage's opening (29 rules) and `.closesay` is the close /plan already
recorded as a statement 512 pixels wide inside a 1,152-pixel band. Grepped
first, named `pickmonth`.

**A CLASS NAME WITH NO RULE IN THE STYLESHEET IS STILL TAKEN, AND THAT IS THE
OTHER HALF OF A RULE THIS FILE RECORDS FIVE TIMES.** *Grep the stylesheet
before naming a composition* was written after `.doorgo`, `.sendsay`,
`.closesay`, `.sheet-send` and a duplicated `.deskart figcaption`. It was
done for all six of /events' plate names and `.sheet-year` came back with
**zero rules** — and **the homepage's plate 07 has emitted `sheet-year`
since the homepage became a plate sequence**, styled by nothing, because the
class names the band and its room does the work. So a `display: block`
written for the calendar's year chart landed on the homepage too. **The
built site is the other half of that grep.**

**AND THE DEAD-RULE SCAN REPORTED THAT DECLARATION DEAD, WHICH IS HOW THE
COLLISION WAS FOUND.** Its page list carries `/events/oct` and not
`/events`, so the only page it could measure the rule on was the homepage,
where the plate is already block. Measured on /events: without the
declaration `.sheet-year` computes `grid`, the year chart falls from
**1,152 pixels to 619**, its head from 1,152 to 461 and the shoulder
photograph from 752 to 392. *A rule measured only where it loses looks like
a rule that wins nowhere* — fourth occurrence, fourth time the answer is a
page.

**THE GUARD IS A CHECK NOW RATHER THAN A SENTENCE.** `c_plate_class_owner`
reads the built site for every `sheet-` class and the families that emit it.
The five ROOMS — `gal`, `paper`, `pine`, `quiet`, `bleed` — bind tokens and
are shared by design; a COMPOSITION class belongs to one family. A second
family wanting one is not forbidden and has to be declared: `.sheet-keep` is
a real centred close /discover and /experiences share and sits in
`SHEET_SHARED` with its reason. **Moving one is allowed; moving one silently
is not**, which is the invariant register's own rule applied to a class
name. Proved red both ways — a composition class on a second family, and a
declared exception nothing reaches.

**/my-europe KNEW FIVE SAVE KINDS AND THE SITE OFFERS SIX, AND THE MISSING
ONE SORTED FIRST.** `my-europe.js` orders a reader's collection with
`ORDER = ["Itinerary", "Place", "Journey", "Theme", "Story"]`, and
`data-kind="Experience"` is on **197 save buttons** and appears nowhere in
that list — so `ORDER.indexOf` returned **−1** and every saved experience was
placed in FRONT of everything, ahead of `Itinerary` at index 0. **A kind the
application does not know is not dropped and does not throw; it is sorted
first by accident**, which is exactly why nothing ever looked broken. The
counts off the built site are Place 893, Experience 197, Journey 17, Theme
13, Story 9 — and Itinerary **0**.

**AND `Itinerary` WAS THE OPPOSITE SUSPICION, WHICH IS WHY IT WAS CHECKED
RATHER THAN REMOVED.** Zero pages offer it, which is the exact shape of *a
motif nothing reaches is dead code that looks like vocabulary* — and
`planner.js:1755` pushes `kind: "Itinerary"` when a reader saves a route the
Planner has just built. It is real, it stays, and it stays first, because it
is the only one of the six the reader MADE rather than chose. Checking a
suspicion is what stopped a wrong repair.

**THREE KINDS OF MEMORY ARE SIX.** The brief's sentence is the good half —
*places tell you where, journeys tell you how, stories tell you why* — and
naming three of six is the `pop_line` shape, a taxonomy that omits part of
its own set reading as a policy. The band keeps the grammar and covers all
six with a derived count each (574, 197, 17, 13, 9, and *built by the
Planner*), because a figure typed there is the figure that was true two
hundred destinations ago. **And that band IS the empty state**: a
server-rendered page cannot know whether a `localStorage` list is empty, so a
band that appeared only in one state would need JavaScript to decide it — and
*nothing saved* is answered by saying what there is and where it is, which a
reader with a full list wants too.

**THE BRIEF'S MONUMENTAL OPENING IS REFUSED BY A MEASUREMENT THIS SITE
ALREADY HOLDS.** *An instrument's title is a label, because the page is the
tool*, from a head pushing the instrument to y=436 on /plan, 449 on /map and
460 on /search. All five INTELLIGENCE pages carry `pagehead instrument` and
the register asserts exactly one role per head. What the brief actually asks
for — personal and considered rather than a dashboard — is what the seven
bands do, and it does not need a 60px h1 to do it.

**`.minemap .constel` WAS CAPPED AT 30rem, SO THE PAGE'S CENTRAL INSTRUMENT
DREW AT 480px IN A 1,152px BAND** — 42% of its own room, on the one drawing
whose caption says *the emptiness is honest, you can see how much of Europe
you have not chosen yet*. That is /themes' 204-pixel continent and the
`.card-art` letterbox a third time: **nothing counts a cap.** 1152 × 899 at
1280 after.

**AND THE PARAGRAPH THAT STOOD HERE WAS WRONG, WHICH IS THE POINT OF
LEAVING IT.** It said *`.sheet-pine` sets no `display`, so both pine bands
landed in a 40% track*, called it the third occurrence in three commits, and
went into a commit message and into this file. **`.sheet-pine` has ended
`display: block` since the commit that introduced it**, and so do
`.sheet-gal` and `.sheet-bleed`; only `.sheet-paper` and `.sheet-quiet` do
not. /stories' feature band at 205 × 154 and /events' year chart at 619 were
both **paper**, which is exactly what made "a paper or pine composition lands
in the 40% track" look true — a correct diagnosis of two cases, generalised
one room too far and then repeated as evidence. Seven declarations on
/my-europe, five on /interests and six on /beyond-the-obvious restated what
their room already computes; all eighteen are gone and twelve screenshots
across six pages at 1280 and 390 are **byte-identical** before and after.
`grep -n '^\.sheet-pine' -A 6` is the whole check and it takes a second.
*A comment claiming evidence is read as evidence* — and so is a finding.
**`sheet-kinds` was already emitted by /experiences with no rule anywhere**,
found by grepping the stylesheet AND the built site, which is the lesson
`.sheet-year` cost one commit earlier; `c_plate_class_owner` now fails on it
without anybody remembering to look.

**AND NOTHING ABOUT HOW THIS PAGE STORES ANYTHING CHANGED.** The three
`localStorage` keys, the four runtime hooks (`#minemap`, `#minecap`, `#mine`,
`#dna`), the drawing and the empty containers are what they were — the brief
asked for the presentation layer and for the saved entries to stay real data
rather than decorative mock rows, and a placeholder inside `#mine` is the one
thing that would have made this page lie.


**/interests HELD EIGHTEEN PHOTOGRAPHS AND DREW NINE, AND THE NINE IT DREW
WERE THE WRONG NINE.** The register carries one for each of the seventeen
tags and one for the index. The page spent a hero and a strip of the widest
eight — so the nine it never drew were the NARROW end, which is the half this
page exists to argue is the useful half. **The family had a picture of
everything it says is too broad to filter by and none of what it
recommends.** Fourth family running on *the pictures were already bought and
were being spent on one strip*, and **nothing was acquired.** All eighteen are
on it now, each exactly once.

**AND THE THREE SCALES ARE `INTEREST_BANDS`, WHICH THIS FAMILY HAS PUBLISHED
ON ALL SEVENTEEN OF ITS OWN PAGES SINCE THEY WERE WRITTEN.** At or above 40%
of the Atlas a tag *barely narrows Europe*, between 15 and 40 it *narrows
usefully*, below 15 it is *one of the narrowest here* — which is 2, 7 and 8,
and therefore two at feature size, seven in a strip and eight with their own
pictures. `ranking[:3]` would have been a layout deciding an argument, and
would have stopped agreeing with the seventeen pages the day a tag crossed a
floor. The brief asks for an explicit visual distinction between broad and
narrow; this is that distinction read off a sentence the page already writes.

**A SENTENCE OF ONE SHAPE MEANT 22% ON ONE ROW AND 73% ON ANOTHER.** *Greece,
Italy and Spain carry the most of it* is 26% of History between them; *Norway,
Switzerland and Germany carry the most of it* is **73%** of Slow travel by
rail, and *France, Spain and Norway* is **22%** of Big cities. Identical
shape, opposite content — the `8 PLACES` failure in prose rather than in a
number. **Reach and concentration are different questions and the page ordered
by one and printed neither**: Big cities is 74 destinations in 41 countries
and Coast & beaches is 92 in 29, because a coast is a fact about geography.
The share is on every row now, and it is the evidence under the brief's own
closing claim — the eight narrow tags put a **median 51%** of themselves into
three countries against **33%** for the nine above them. The median rather
than the mean, because Festivals is three destinations in three countries and
100% computed on three rows is a fact about the sample.

**AND A SECOND MEASUREMENT WAS TAKEN AND DELIBERATELY NOT SHIPPED.** Asked as
a share of each country's OWN destinations, **fifteen of seventeen** strongest
countries change — Mountains reads Norway by count and Switzerland at 60% by
share. It is not on the page because Türkiye is 5 of 5 for history, and a
measure that reports 100% on five rows is the small-sample trap with a
different sign. Recorded with its trigger rather than published.

**THE REACH BAR AND THE INTERACTIVE MAP ARE BOTH REFUSED.** A bar would be the
THIRD drawing of one number — the row prints the percentage and the seventeen
glyphs are drawn to one frame precisely so reach is visible — and /journeys
records what happens when a band draws one measurement twice on two grids. And
*select an interest and the map becomes its geography* is a control on a page
whose only `<script>` is the inert JSON-LD block: the chip that filters
nothing, and `data-rotate` again. The seventeen ARE the interest atlas, drawn
at once, which is the one thing seventeen separate pages cannot do.

**AN `<a>` INSIDE AN `<a>` IS NOT NESTED — AND THIS COMMIT REPRODUCED
/stories' DEFECT ONE COMMIT AFTER IT WAS WRITTEN DOWN.** `picture()` emits the
Pexels credit as a `<figcaption class="credit">` inside the `<picture>` and
that credit is two anchors, so a row that was an `<a>` wrapping one had its
outer anchor CLOSED by the parser at the inner one — and Chromium's error
recovery reopened it around each following run. **Eight rows measured as
twenty-four in the browser and the band rendered 4,594 pixels tall**, while
the emitted HTML contained exactly eight, so no count here could see it. The
picture is a `<figure>`, the name is the link, and the licence's two links sit
inside no anchor. 4,594 → 2,763. **And the dead declaration came straight
behind it**: with the row a `<div>`, `.row { text-decoration: none }` sits on
a box that is not a link and the UA underline lands on the name instead — 34px
of display serif with a rule through it, which is `.picstory` exactly. *A rule
recorded is not a rule inherited.*

**A CROP-BOX MEASUREMENT TAKEN BEFORE LAYOUT SETTLES REPORTS A BOX THAT DOES
NOT EXIST.** The first sweep read `.ibleed` at 0.314–2.333, guaranteeing 13.5%
of a photograph's frame, and `.atlasopen` at 0.200–1.961 at 10.2%. Both are
impossible — each container states an `aspect-ratio` — and two animation
frames later they read **1.778–2.333** and **1.333–1.500**. That is *a sampler
that reads outside its own image reports the canvas* in another costume, and
what it costs is specific: it sends somebody to fix a layout that is right.

**AND `countries-hero` DECLARED A CONTAINER ITS OWN PAGE HAD STOPPED
EMITTING.** `.ed-opening-visual` is nowhere on /countries since it became a
plate sequence; the hero renders in `.atlasopen`. `c_container_is_emitted`
passed it because that selector IS emitted — on /events and /interests — and
the browser sweep groups by selector and measures the union over its purposes'
paths, so two live paths kept the group green and the third contributed
nothing. **A selector that matches nothing on the page that declares it is
invisible to a check that asks the question site-wide.** Both declarations
follow their page now: countries 26% claimed against a measured **55%**,
interests 26% → **47%**.


**THE COUNT ARGUES THE WRONG WAY AND THE PAGE PRINTED ONLY THE COUNT.**
/beyond-the-obvious groups its 130 quiet destinations into nine corners of
Europe, and the nine counts alone say **go to the Mediterranean** — it holds
41, three times the next corner. That is the opposite of what the page argues
and it is an artefact: the Mediterranean holds 41 because it holds **94
destinations**. As a share of each corner's own set the order changes — the
**Baltic States is 58% quiet** and Eastern Europe 25%, against 41% for the
Atlas as a whole, and the Mediterranean is 44%, barely above average. *The
busiest month is the least characteristic*, one family over. Both figures are
on the group head now, the count because it is what a reader came for and the
share because it is what the count means, and both are derived.

**AND THE RULE HAD THREE PROMISES, ONE OF WHICH THIS SITE DOES NOT KEEP
ANYWHERE.** *No page on this site tells you a place is undiscovered … what we
will say is when to come, how to arrive without a car where that is possible,
and who locally is worth your money.* Measured against the built site: **When
to come** and **Getting there** are section headings on all 319 destination
pages, so two are kept and checkable. The third is not built at all — an
experience record carries a slug, a name, a kind, a band and a summary and
**no operator**, the Stay layer publishes that we list neither hotels nor
restaurants and refuses a ranking, and /for-businesses publishes that there is
nothing in this index that could carry a boost. *A refusal nobody can check is
a slogan*, and this one had never been checked. It is stated as unbuilt with
what it would take, rather than quietly deleted.

**AND THE PAGE'S OWN POSITION WAS THE SMALLEST THING ON IT** — a `.note` at
the very bottom, under 130 rows and six swaps, at caption size. It is two
bands now, because the refusal (*the alternative is not hidden gems*) and what
we write instead are two statements rather than one said twice.

**`.rowmeta` IS `white-space: nowrap`, AND PROSE IN IT RAN 831 PIXELS OFF THE
PAGE.** The rule band's third row put its explanation in the metadata column —
the slot that carries a country and a region everywhere else on this site — so
the document scrolled sideways by **223px at 1280 and 263 at 834**. That is
`19 DAYS · 5 COUNTRIES · MODERATE` exactly, and **the phone-overflow check
could not see it because it is a check about phones**: at 390 and 320 the row
stacks and there is no overflow at all. Prose goes in the subline; the meta
says *Kept* or *Not built*. **And a swap is a pair whose second half was also
typeset as metadata** — *Naxos or Sifnos, any evening*, the one thing the band
exists to say, sat in the region-name slot. Both halves are headings now.

**NO PHOTOGRAPH IN THE OPENING, AND IT IS A REFUSAL RATHER THAN A GAP.** The
register declares no hero for this family, and the one that could be acquired
is by definition a generic European scene — the exact thing a page refusing
the phrase *hidden gems* cannot open on. 27 of the 130 carry a photograph and
the page spends nine, one per corner, because **27 of 130 is a fact about the
library rather than about Europe** and presenting it as a selection is what
this page refuses. The corner with none shows its slot, which names the
acquisition. **Nothing was acquired.**



**THE ONE FAMILY WHOSE WHOLE CREDIBILITY CLAIM IS THAT A PAGE PRINTS WHAT
PRODUCED IT WAS PRINTING SOMETHING NARROWER.** `motion_match` reads
`set(city.interests) | set(region.interests)`, so a destination is returned
when **its region** carries the tag — and the printed query said *"any
destination tagged Islands"* and said nothing about the region. The gap is
not cosmetic: **62 of the 86 results for Food and Wine are there on their
region's tags rather than their own**, 58 of 150 for Coast, 52 of 115 for
Mountains, and across the seventeen interests the propagating reading gives
**1,679 tag applications against 1,142** — 47% more. It returns **Nicosia**
(own tags history, food, cities) for *Europe's coastlines*, because its
region is "Nicosia & the South Coast", and **Tartu**, a mainland university
town, for *Europe's islands*. That is `cell` catching `cellar` one family
over: the page published its rule honestly and a reader who checked would
find something the rule did not describe.

**AND TWO LIVE PAGES PUBLISHED TWO NUMBERS FOR ONE WORD.**
`/interests/mountains` says *63 destinations* and `/europe-in/mountains`
says *115 match* — both derived, both correct under their own reading, and
for the life of both families neither said which reading it was. **The
engine is unchanged**: a region tag is a real fact about the ground around a
place and nine other surfaces read the same union, so narrowing it is a
data-semantics decision for the owner and carries a trigger (a `propagates`
flag per interest). What changed is the sentence — five words in the query,
the mechanism hoisted once by `motion_tag_note()`, and the /interests
reconciliation named. `c_motion_query_breadth` asserts **both halves**,
because either alone goes quietly wrong: the page must state the mechanism,
AND `motion_match` must still have the mechanism the page states. Narrow the
engine and every page keeps a sentence that has become false in the other
direction, which no count anywhere would see.

**THE TWELVE SHAPES WERE ONE PER ROW, 1,152 PIXELS APART.** This family's
signature moment is the query drawn as a shape and its argument is that the
twelve shapes DIFFER — which is a comparison, and a comparison at one
drawing per screen cannot be made. That is /themes' 204-pixel-continent
finding on the other axis: there the drawing was too small to read, here it
was too far from the drawing it is being compared with. They are a grid in
the opening now, 270px a tile at 1280, and **the overlap is measured rather
than asserted**: no two of the twelve share more than **49%** of their
results and **0 of the 66 pairs** share half.

**AND NOBODY HAD CROSSED THE TWELVE WITH EACH OTHER.** Twelve differing
shapes still read as twelve boxes, so the other half of the claim is that
they overlap: every one of the 319 destinations satisfies at least one, the
commonest number to satisfy is four (111 destinations), and **Narvik
satisfies eight**. The bars are a share of the largest group rather than of
the Atlas, because eight groups summing to 319 would put the largest at 35%
of its track and read as a share of the continent.
`c_motion_distribution` asserts the scaling, the labels and the sum **with
no reference to the generator** — recomputing the distribution means
re-running the twelve queries, and an instrument that re-runs the model can
only ever agree with it.

**A MOTION MAY NOT HAVE A PHOTOGRAPH OF ITS OWN, AND BOTH DERIVATIONS OF
THE ONE IT MAY HAVE WERE WRONG FIRST.** The register rightly declares no
`motion:` purpose: a motion has no coastline, no topography and no season,
so a picture of one is a picture of nowhere — the refusal that took twelve
plates off this index. What it can spend is a photograph of a destination
the query returned. Ordering by *fewest of the other eleven* picked the
region-only members — Nicosia for the coastlines, Tartu for the islands —
which are the weakest in the set; adding *direct member first* then picked
**Baku** for the medieval world, whose registered photograph is the Flame
Towers. **A destination whose own tag list is most nearly just what the
query asks for** is the characteristic member: Mostar, Blagaj, Kuressaare on
Saaremaa. Advisory countries are excluded because a derived point is not
automatically an honest one — the first rule offered Belovezhskaya Pushcha,
in Belarus. `by-rail` has twenty results and none photographed, so it shows
its slot. 0 `<img>` to 11, and **nothing was acquired.**

**A COMMENT IN EMITTED MARKUP SHIPS — AND THIS ONE TRIPPED THE CHECK IT WAS
WRITTEN ABOUT.** The reason the projection is *not* named on /europe-in went
into the page as an HTML comment, and it contained the words "conformal
conic": `c_published_projection` reads the shipped HTML only, correctly, and
failed four times on a paragraph explaining why those words are not on the
page. Third occurrence of that rule here. A reason belongs in the source
that writes the page.

**A DESCENDANT SELECTOR WRITTEN FOR ONE FIGCAPTION REPAINTED THE LICENCE
CREDIT, AND ONLY THE BROWSER SUITE COULD SEE IT.** `picture()` emits Pexels'
two required links as a `<figcaption class="credit">` INSIDE the
`<picture>`, absolutely positioned on a 72% graphite scrim whose arithmetic
gives 6.90:1 whatever the photograph is. `.moshot figcaption` — written for
the row's own caption, *"Zagreb, Croatia — one of the 309"* — is (0,2,0)
against `.credit`'s (0,1,0), so it repainted the credit `--ink-3` and left
its position, its scrim and its opacity alone: **3.56:1 in both preferences,
on the two links the licence requires**, two failures of 9,709. That is the
`.pageband figcaption` defect this stylesheet already records, reproduced
two hundred lines from the paragraph recording it — *a rule that changes two
properties of a six-property component achieves exactly one thing, and here
that thing was the defect.* A child combinator cannot reach inside the
`<picture>`.

**AND THE CLOSE WAS A FOURTH CLASS WITH THE SAME BODY.** `.istart` is the
close shape /interests introduced and /beyond-the-obvious already reuses —
`display: grid; justify-items: start; max-width: 46rem` and a 38rem lede.
Written here as `.moask`, measured at a 361px lede against the shared
shape's 608, and **deleted rather than tuned**. The same hour produced a
second `.motilenm` declaration eight lines below the first, which is the
duplicated selector this stylesheet removed 85 of, made in the hour after
the comment recording that.


**NOTHING HERE COUNTED REPETITION, AND THAT IS HOW A PAGE COULD BE A CMS
LISTING AND PASS EVERY GATE.** The owner read several finished redesigns and
said the same thing about each: *keep the existing page, add premium CSS and
components around it, add a few visual elements, call it a redesign.* He was
right, and the reason is measurable: this suite checks contrast, weight,
overflow, reach, coverage, provenance and correctness, and a page can be
perfect on all of them while being forty-two rows of one component — which
`/experiences` was, and the stories index was nine three-column grids each
holding one card, and `/interests` was 728 abstract plates. Every gate was
green through all of it.

`tools/monotony.js` measures it: the share of a page's own height taken by
the single most repeated component, where a repeated component is three or
more siblings agreeing on their class attribute **and on their children's
class attributes**. That second half is what makes it an instrument rather
than a count — six `section class="band"` siblings on a country page share a
class and hold six different compositions, and the first version reported
that page at 76%; thirteen theme rows share their inner shape too, and that
difference IS the difference between a composition and a listing. Three
earlier definitions were each wrong in a way that looked right: class tokens
anywhere on the page put every plate page at 99% `sheet` (the room wrapper);
summing the heights of siblings reported /macro at 144% and /map at 762%,
because nine cards in a three-column grid sit three rows deep and an
instrument's layers overlap, so what is wanted is the vertical UNION; and
counting what a reader cannot scroll to put /map at 789%, because its text
twin — the alternative naming fifty countries and 319 destinations — is laid
out from y=2,087 to y=18,355 inside a 2,665-pixel document and clipped for
sighted readers. **A share over 100% is an instrument saying it does not know
what it is dividing by.**

Measured, the worst offenders were mostly pages nobody had redesigned:
/countries 63% (nine identical macro bands), an experience category 62% (48
invites), a motion page 54% (38 rows), /for-businesses 51%, a macro region
49%, a facet page 46%, /fund 45%, /search 42%. **A long list is sometimes the
right answer** — an index whose subject is 130 places is a list — so the
report prints the next two components beside the first: a page at 60% with
two other bands is a list with a frame round it, and a page at 60% with
nothing else is the fault. The ceiling is the current worst and comes down in
a diff as each page is recomposed, which is the invariant register's
discipline applied to composition.

**AND THE DOCTRINE IS IN THE REPOSITORY RATHER THAN IN A SESSION.**
`docs/redesign-doctrine.md` carries it: *preserve the information,
reinterpret the presentation* — the existing content is authoritative, the
existing visual structure is not. Inspect first and write no CSS; then a
content architecture answering what the page is about, what single idea the
visitor should take, and which content must NOT become a card; then compose.
Photography is structural — a photograph carries the meaning of its section
(a country's geometry with the picture clipped into it, a journey's landscape
sequence along the route) or it is decoration under the existing sections.
And **"premium" is not a brief**: it is satisfied by rounded cards,
gradients, shadows and hover animations, none of which this product wants.


**/themes DREW NONE OF THE THIRTEEN SHAPES ITS OWN CLOSING SENTENCE
DESCRIBED, AND THE HELPER'S DOCSTRING HAD STATED THE CONTRACT.**
`head_figure()` prefers a photograph and falls back to the drawing, and it
says in as many words: *the drawing is never lost — the caller emits it below
with `moved_drawing()` when a photograph took its place.* Three callers use
it; the country page honours that, the theme page honours that, and **the
themes index never called `moved_drawing` at all.** So from the commit where
the thirteenth theme photograph landed, every glyph was built and discarded
while the note under the list went on promising *"each shape beside a theme
is that theme's own eight places … drawn to the same frame so the thirteen
can be compared"* and crediting Natural Earth for land nobody drew. That is
the fourteen-call-sites-forgot-the-motif shape in a helper with a two-call
contract.

**AND `c_same_frame` COULD NOT SEE IT.** That check skipped any page carrying
fewer than two `.constel` glyphs, so *says and draws nothing* — the strongest
form of the defect it exists for — was the one form outside its reach. Both
directions now, proved red by removing the drawings and green by restoring
them.

**THE THIRTEEN ARE NOT THIRTEEN ROWS, AND THE SCALE OF EACH IS DERIVED FROM
ITS REACH.** A theme holds a photograph, a geography, an authored summary,
eight places and a reach: that is a composition, and `.row` was the shape of
the LIST rather than of the content. A theme crossing a **majority of the
nine corners of Europe** takes the wide band (geography-led, 736 × 574 with
its caption beside it), three or four corners the feature (picture-led at
745 × 496 against a narrow type column), and the one theme that is an
argument about a single corner takes an intimate one. Majority of nine is
five, so it falls 6 / 6 / 1 — and the single tight band is Renaissance
Europe, precisely the knot this page's closing sentence is about, so **the
layout argues what the sentence says instead of captioning it.** The side
alternates because a magazine alternates: six identical wide bands in a
column is a listing with a bigger component. `tools/monotony.js` measured the
change — the largest repeated component went from **37% to 18%**, with the
next two at 16 and 15.

**AND THE REPAIR THAT WOULD HAVE LOOKED BEST ON SCREEN WAS REFUSED ON
LICENCE GROUNDS.** The picture-led band measured say 507 + map 280 against a
photograph of 496 — 290 pixels of empty page under a picture-led band's own
picture — and the obvious fix is `object-fit: cover`. That CROPS, and
`theme-hero` declares one container (`.headshot`, on the theme page) while
this index is a second, undeclared surface: *a photograph is cropped by every
surface it appears on and the register declares one* is already recorded here
as an open gap, and the fix would have widened it into a crop nobody has
measured, on the one axis `c_photo_safe_area` exists to guard. The map moved
out of the spanned column instead.

**A 76px HEADLINE IN A 359px COLUMN STRANDS ITS LAST WORD**, which /journeys
already recorded in a 461px one: `--ed-display-2` is 64px at 1280 and "Sacred
Europe" needs about 380, so two of the six feature bands broke their name
while the six wide bands — 745px of type column — did not. And **the wide
plate was 1,152 × 899**, because the frame is 1000×780 and a full column is
899 pixels tall; it cannot be cropped to a letterbox, since an SVG with no
`preserveAspectRatio` letterboxes inside a wider box rather than filling it,
which is the `.card-art` finding from the other side.


**/map's FAULT WAS THE OPPOSITE OF EVERY OTHER PAGE'S: `tools/monotony.js`
DOES NOT LIST IT AT ALL, BECAUSE EVERYTHING THAT MADE IT AN INSTRUMENT WAS
BEHIND A CLOSED DISCLOSURE.** `<details class="maptools">` held the legend,
how to read the drawing, the four geography layers, **all seventeen interest
filters**, the journey overlay, the distance origin and the live count; a
second `<details>` held the text twin, which is the most complete index on
this site — fifty countries and all 319 destinations with coordinates,
grouped by macro region, the map's own `aria-describedby` target and the
control WCAG 2.5.8 requires for the twenty countries that draw between 3.6
and 12 pixels wide. A reader met a map they could only click, under a
four-word lede, with one `<h2>` on the whole page. Both are bands now.

**AND THE CONSTRAINT THAT PUT THEM IN A DISCLOSURE IS INHERITED RATHER THAN
GUESSED.** The browser suite's own comment records why: *the first layout put
thirteen interest filters and two selects between the headline and the
drawing and a 1280×1000 laptop opened the page called "the map" with no map
on it.* So the controls are BELOW the drawing, measured — the map starts at
y=526 at 1280 and the controls at y=1528 — and the suite asserts that
ordering instead of opening a disclosure, which is the eleventh assertion
here to stop pinning a shape. All twenty-two ids `map.js` binds to are
asserted present on the built page, because a recomposition that breaks the
application is not a redesign.

**A KEY THAT NAMES THE WRONG COLOUR IS WORSE THAN NO KEY, AND TAKING IT OUT
OF THE DISCLOSURE IS WHAT PROVED IT.** `.legend .sw.dest` is `var(--sea)`
and the map paints its dots `var(--sea)` too — the same token and two
different colours, because **a `var()` resolves where the DECLARATION
lives**: inside the graphite map figure `--sea` is cobalt-air and inside a
light band it is pine-deep. Measured on the shipped page the drawing painted
`rgb(64,118,231)` and the key beside it showed `rgb(7,48,43)`. Nothing counts
a swatch, so it was invisible for as long as the key sat behind a summary
line. **The fix is not a hard-coded hex** — the key sits in the same band as
its drawing, where every token it reads resolves exactly as the drawing's
does, which is also where a key belongs; and the browser suite reads the
computed paint off BOTH ends, because the declaration is the same string in
both places and comparing declarations would agree with itself.

**AND `&deg;` IS NOT `°`.** Rewriting the projection paragraph with the HTML
entity failed all four angles at once on the one page allowed to state them:
`c_published_projection` reads the shipped HTML for "35°" inside the sentence
that names the conic, and the entity is five characters that are not that
one. The degree sign is the character.


**A DUPLICATE `id` IS INVALID HTML AND NOTHING HERE CAUGHT IT, AND THE CHECK
WRITTEN FOR IT FOUND A SECOND CASE IN ITS FIRST RUN.** /map's plate 02 was
given the anchor `layers` — a good name for a band of layer controls, and
already the `id` of the interest filter container `map.js` binds to. A
plate's anchor becomes an `id` on the `<section>`, so the page shipped two
elements carrying `id="layers"`, and the browser suite did not report a
failure: it **died**, on a strict locator resolving to two elements, which is
the shape of regression a suite cannot describe. `c_fragments_resolve` asks
whether every fragment finds AN element; `c_unique_ids` asks whether every id
names exactly one, which is the question that was missing.

Its first run found `ihedge` and `ihfoot` twice on /stories. Two callers pass
the prefix `"ih"` to `cut_fade()` — the index hero and `constellation()` —
and /stories draws both, so the second `url(#ihedge)` resolved to the FIRST
drawing's gradient. On that page the two gradients happened to be identical,
because both take their coordinates from the projection rather than from the
viewBox, **so nothing looked wrong — which is luck and not design**: the
moment two drawings on one page pass a different `reach` or `top`, the second
silently takes the first's geometry. The defs cannot be hoisted and shared,
which is the obvious repair — `.datacut stop` and `.reachhead .datacut stop`
colour the stops by ANCESTOR, so a hoisted `<defs>` takes the wrong colour or
none, which is this function's own recorded fault from the other end. The id
carries a counter instead; a prefix chosen per caller would be a guard
whoever adds the next drawing gets to choose.

**THE WORST MONOTONY FIGURE ON THE SITE WAS A PAGE ALREADY REDESIGNED, AND
`glyph_view`'s OWN COMMENT STATED THE DOCTRINE'S SECOND RULE AS A DESIGN
DECISION.** /countries measured **63%** — nine `macroband` siblings, 11,300
pixels of an 18,569-pixel page — one commit after the page-level
recomposition, because that pass kept the biggest band's shape and only moved
it. The docstring says so: *WHAT IS KEPT: the nine macro bands*, which is
right about the GROUPING and was applied to the SHAPE.

Measured across the nine: destinations 8 to 94, extent 546 km to 3,605,
photographs in the register 4 to 56, own proportion **0.63 to 2.75** — and
**proportion as drawn, 1.282, nine times.** `glyph_view` explains the last
one itself: *"held to the canvas proportion, so a set of glyphs is a set of
boxes of the same shape and only the geography inside them differs"* —
**do not optimise for visual consistency at the expense of editorial
difference, written as a decision in the function that implements it**, one
commit before the owner added that rule. That box was 42% padding for Eastern
Europe and 3% for the Caucasus.

`macro_shape()` measures each region in kilometres and the composition is its
own shape. Two boundaries that are descriptions rather than fitted numbers —
taller than wide, wider than tall, more than twice as wide as tall — and the
nine fall **4 portrait / 3 upright / 2 panoramic**. **63% → 25%**, next two
20% and 8%, and the monotony ceiling came down 63 → 55 in the same diff.

**ORIENTATION RATHER THAN SCALE, WHICH IS THE DEPARTURE FROM /themes.** That
page derives three band SIZES from a theme's reach, which is a claim about
importance; a region is not more important for being wide, and nothing here is
drawn larger than anything else. *One method reused as a template is band
monotony* — the rule cuts both ways, and the owner's own instruction is to
copy the reference implementations' METHOD and never their layout.

**Three measurements were taken and refused, and each refusal is the finding.**
The COUNT argues the wrong way: Eastern Europe holds 8 destinations because
**three of its four countries carry a travel advisory**, so a size derived
from it prints an advisory artefact as an editorial judgement —
/beyond-the-obvious's own sentence one family over. PHOTOGRAPH COVERAGE is a
real 14× spread and this page already spends it on which country gets the
large door, and a band drawing one measurement twice is what /journeys
recorded. And **the partition cannot be drawn once**: nine areas on one
continent need nine tones, the owner's palette refuses an eight-hue wheel in
as many words, nine steps inside the atlas's one stone are the *rounding error
with a token name*, and a seam needs topology this atlas does not hold — it
holds country rings, so a stroke on a group strokes every internal frontier at
region weight. Nine frames is what the data supports.

**AND THE FIRST REPAIR DID NOTHING FOR THE ONE REGION IT WAS WRITTEN FOR.**
Passing each region's measured aspect to `glyph_view` looked complete: the
hold only ever GROWS the short axis, the Mediterranean's padded box is already
986 units of a 1,000-unit canvas, so growing width toward 2.75 clamped at the
canvas and the emitted frame came back at **1.30 — the whole continent with a
corner lit**, which is that function's own recorded failure. `aspect="own"` is
no hold at all. **And the isotropic pad is why the drawn spread is narrower
than the geographic one** — a third of the region's own size on every side
pulls every aspect toward 1, so the nine measure 0.54–3.21 raw on this
projection and 0.86–1.69 padded; the pad floor is a legibility floor for a
region the size of the Baltic States, so it stays and the CLASSIFICATION is
done on the geography rather than on the frame.

**AND ONE UNCONDITIONAL RULE WAS WRITTEN TWICE, TWO SCREENS FROM THE
PARAGRAPH RECORDING THE LAST 85.** The portrait glyph's height cap went into
the 62rem block and into its complement with an identical body — two media
ranges that between them cover every width, which is a rule that is
unconditional, written twice.

**AND ONE EMITTED STRING IN TWO PLACES SHIPPED TWO IDENTICAL GRADIENT IDS,
FOUND BY THE GATE SUITE FOR PHOTOGRAPHS.** `region_glyph` at the full extent
emits `cut_fade`, whose ids carry a build-wide counter precisely so two
drawings on one page cannot collide — and **a counter cannot help when the
same emitted string is interpolated twice.** /countries built its continental
drawing once into `heroart` and used it in plate 01's fallback and in plate
02. It is invisible while the register holds `countries-hero`, because then
plate 01 draws the photograph and the fallback is never reached;
`photo-tests.py` frees that purpose to acquire against its stub, rebuilt, and
`c_unique_ids` reported `rg2edge` and `rg2foot` twice. *A code path nothing
exercises is a code path nothing checks* — and the only thing that exercises
this one is the suite whose subject is something else entirely. Two calls, so
each emission takes its own number; proved on the state that broke it.

**A RHYTHM WRITTEN AT (0,2,0) BEAT THE 62rem BLOCK AT EVERY WIDTH**, which is
the trap this stylesheet already records twice: a phone drew the Baltic States
**115 pixels wide inside a three-track grid** and the document scrolled
sideways by 66px at 390. Both rhythms live inside `@media (min-width: 62rem)`
now, because a rhythm is a statement about a wide column, and no breakpoint
was added. Then a full-width portrait drawing measured 358 × 564 at 390 —
*the full-width glyph at 600 made /interests 11,972 pixels tall* — so it is
capped at 24rem with `width: auto`, which keeps the proportion the rhythm is
about; holding it back to 1.282 below the breakpoint would reintroduce the
fault at the width most readers are at.

**THE MOTION PAGE'S ROW-LEVEL CLAIM STAYED FALSE AFTER THE SENTENCE WAS
FIXED, AND THE LIST HAD NO STRUCTURE AT ALL.** /europe-in/‹motion› measured
**54%, thirty-eight `.row` siblings with no second component** — the worst
figure on the site once /countries came down. The previous commit measured
that `motion_match` reads the UNION of a destination's own interests and its
region's and fixed the sentence the PAGE prints; every ROW went on saying
*tagged Islands*, which for Tartu — a mainland university town in the region
"Tartu & South Estonia" — is a claim about the wrong record. Measured on the
shown sets: **15 of the 25 on Europe's islands**, 25 of 56 on the
coastlines, 24 of 59 on the mountains, 19 of 55 on the sacred world and 12
of 25 on winter qualify on their region rather than on themselves.

**ONE MECHANISM FOR ALL TWELVE QUERIES: the list is grouped by the clause
each result satisfied.** Hoist what every result shares, group by what is
left, and the groups come out of the query rather than out of a taxonomy
somebody chose — islands 15/10, autumn 42 October / 26 September / 15
November / 8 both, the medieval world 51/8/5/3. **A GROUP OF ONE IS NOT A
GROUP, IT IS A ROW WITH A HEADING**, and the first test was the MEAN group
size, which let a tail through: hidden villages splits 22, 14, 9, 8, 6, 3,
1, 1, 1 — a mean of 7.2 and three sections holding one row each. Every group
must hold three now, so two of the twelve keep their list and are **ordered
by the run that would have grouped them**, largest first, where both had
been alphabetical by country. Ordered by the run's own SIZE rather than the
clause string, because "scores 97" sorting before "scores 84" is an accident
of decimal notation. 54% → **31%**, with 8% behind it.

**AND THE LIST SETS IN TWO COLUMNS, WHICH FIXED A MEASURE AS WELL AS A
HEIGHT.** A motion row is 1,232 × 97 at 1280 and its summary — a sentence of
prose — occupied **1,120 pixels on one line**, because `.row .rowsub` carries
`max-width: none`. The reason written on that rule is exact and about a
different content type: *`.rowsub` is a `<p>` holding a middot-separated
list of place names … nobody reads a list of names end to start, they scan
it.* A destination's SUMMARY is prose and 140 characters on one line is what
a measure exists to prevent; the generalisation was one family too far. Two
columns give 68 characters, and the page falls 7,497 → 6,133 pixels.

**A CHECK PINNED A SOURCE SPELLING — the twelfth here to pin a shape rather
than a promise.** `c_motion_query_breadth` required the literal
`set(t["interests"]) | set(r["interests"])` and went red the moment that line
became `own, near = …` followed by `own | near` so the clause could say which
side it came from, which is MORE of what the check protects. The engine half
is behavioural now: at least one destination must be returned whose region
carries the tag while it does not. Proved red by narrowing it.

**And the group head disagreed with its own pronoun.** *"42 destinations, in
its quieter shoulder season in October"* — the clause is written about one
destination, so a plural subject disagrees with the pronoun inside it. The
count is the heading and the clause is the `.whyall` line under it, which is
the component whose entire job is *a clause true of every result in this
set*. **And the row's heading level follows the grouping**: h3 inside a
group whose own h2 is above it, h2 on the two pages where the list is still
the page, read off `grouped` rather than passed per call site.

**AN EXPERIENCE CATEGORY PRINTED THE SPEND BAND ON EVERY ROW AND THE KIND
ONLY WHERE IT DISTINGUISHED — THE SAME GUARD, APPLIED TO ONE OF TWO FIELDS
SITTING NEXT TO EACH OTHER.** The builder's own comment records why the kind
is conditional (*on /experiences/food every row said CELLAR & VINEYARD or
FOOD & TABLE forty-eight times … never explain the constraint back*) and the
band beside it was unconditional, so **/experiences/luxury said "high" on all
five of its invitations** and food said "low" thirty times with no "high"
anywhere on the page. **And it was printing the raw slug**: `taxonomy.json`
gives each band a NAME and a note — Frugal, Comfortable, Generous — and both
invite call sites, plus the kind page, printed `low`/`moderate`/`high`. An
enum value is an identifier for a program.

**WHAT AN INVITATION COSTS IS THE ONE EXCLUSIVE AXIS THOSE RECORDS CARRY**,
and the list had no structure at all: 48 `.invite` siblings, **51% with no
second component**, the worst figure left on the site. The sub-categories
cannot group it and that refusal was already recorded — six of Food's 48 are
in no sub-category and eight are in two — where a band is one per record. The
distribution is itself the finding: **nothing in Food & drink or in Culture is
generous at all**, 0 of 48 and 0 of 52, where Luxury is 5 of 5. The hoisted
line is the taxonomy's own note, so a page cannot describe a band differently
from the planner that spends it. **Frugal first, which is the taxonomy's order
rather than largest first** — a motion's groups are unordered clauses and take
the largest; a budget band is a SCALE, and printing Comfortable above Frugal
because there are more of them would be sorting an ordered axis by
population. 51% → **36%**, and the sub-category page 31% → **16%**.

**AND `columns` PACKS WHERE A GRID ALIGNS, WHICH THIS FAMILY HAD ALREADY
LEARNED ONE LEVEL UP.** The invitations were already two columns and a GRID,
whose row is as tall as its tallest item: 48 of them took **4,065 pixels**
where twenty-four rows of the tallest need about 3,384 — seven hundred pixels
paid for the difference between a one-line summary and a three-line one,
twenty-four times. The /experiences index recorded exactly this about its
eight category panoramas.

**ONE FLOOR, TWO FAMILIES.** `GROUP_MIN` is 3 — a section holding fewer than
three is a heading over a row — read by the motion pages and by the category
pages, because *a second implementation of a thing is a second chance to make
its mistake*. What each family groups BY is its own: a motion groups by the
clause its query matched, a category by what an invitation costs. Three of the
eight categories keep one flat list under it (nature 11/15/**2**, history
18/11/**1**, luxury one band) and keep the band on the row, because there it
distinguishes.


**A READBACK THAT REPORTS THE PARSE RATHER THAN THE PLAN IS NOT A READBACK,
AND THIS PAGE'S WHOLE CLAIM IS THAT IT IS ONE.** /plan ships the sentence
that it *"shows you exactly what it understood, naming anything it could not
take account of rather than quietly dropping it"*, and `section-audit.py`
published the matching verdict: *ten of the eleven inputs are taken and every
one of them moves the answer.* True of the FORM and false of the sentence box
in three places. `goFromSentence` calls `plan(opts)` **four lines before** it
composes `readbackHtml(got)`, so every disagreement was already known and the
readback was handed the wrong object:

| you typed | the page said | the plan did |
|---|---|---|
| `for 4 people` | "for 4" | priced one person |
| `2 days in Vienna` | "2 days" | built three |
| `A week in Slovakia` | "within Slovakia" | planned the whole continent |

**The party size was the expensive one.** `applyAsk` set days, budget, month,
style, pace, start and interests and never `form.travellers`, so `readForm`
read the control's default of one. The cost model is careful — a double is not
twice a single, so the second traveller adds 55% of a room and everything else
scales linearly — and all of it was spent on the wrong number: measured in
Chromium on one sentence with and without four people, **€1,491 against
€4,958**, accommodation ×2.65 exactly and food, transport and activities ×4. A
party of four saw a total **70% under its own cost**, on the one number in this
product a reader could act on and be wrong about.

**The geography was the dishonest one, because it was not silence but a false
statement.** `plan()` honours a named country only where four destinations sit
inside it, and **12 of the 47 countries in the planner index hold fewer** —
Monaco, San Marino and Vatican City one; Slovakia, Montenegro, Cyprus, Kosovo,
North Macedonia and Azerbaijan three. `opts.geoTooNarrow` was set for exactly
this and **read nowhere**, which is `kindfilters` and `data-rotate` again.

**And the browser suite already asserted the party size — through the FORM,
with the same cost band.** *A code path nothing exercises is a code path
nothing checks*, and here the exercised path was right and the unexercised one
was wrong, in the same function. `DAY_MIN`, `DAY_MAX`, `PARTY_MIN` and
`PARTY_MAX` are declared once and asserted against **the `min` and `max` the
form actually ships**, because comparing four typed copies to each other goes
green the moment somebody types the same number twice — the dispatch cap
exactly. See `docs/plan-redesign.md`.

**AND TWO OF THE THREE NEW CHECKS WERE GREEN ON THE STATE THEY EXIST TO
REFUSE, BOTH FOUND BY MUTATION.** The flag scan asserts that every constraint
the planner computes is read back — and the paragraph in `planner.js`
explaining that `opts.geoTooNarrow` was *read nowhere* contains those words, so
deleting the real read left it passing. **Seventh occurrence of an instrument
reading the documentation of code as code, and the first where the check and
the comment that defeated it were written in the same commit.** `bare_js()`
now does for a script what `bare_css()` does for the stylesheet, stepping over
string literals rather than stripping them because `https://` inside one is not
a comment, and its output is asserted to still parse. The other: replacing
`applyAsk`'s condition with `if (false)` left the words `form.travellers` in
place and the check green — a shape rather than a promise, in a check written
against that, so the static half says only what it can and its message names
the instrument that owns the rest. **A check is not proved by passing; it is
proved by failing on the thing it is about.**

**AND A SPECIFICATION ARRIVING AGAIN IS AN AUDIT RATHER THAN A BUILD.** §1–13
of the product specification are already absorbed and asserted section by
section — `tools/section-audit.py` tracks every one of them with a published
verdict and its own assertions, and CI fails when one stops being true —
run `python3 tools/section-audit.py --check` for the totals, which is the
rule this sentence broke on its first draft by copying them here. So the
answer to "what is the gap" is generated rather than argued: §5's navigation is
the specified nine items in the specified order, §11's essential information is
every field on its list except visa and emergency, **which are refused as
unverified** with `docs/legal-position.md` behind them, and the traveller types
are seven with a route, two derived by published rule, and accessibility needs
held nowhere at all. **The gap the audit did NOT know was the one above**,
because §10's assertions proved the arithmetic exists — `bedFactor` is in the
file — which is not the claim that the input reaches it.

**AND ONE CONTENT GAP IS RECORDED RATHER THAN INVENTED: NO JOURNEY HERE IS
SHORTER THAN A FORTNIGHT.** The seventeen run 14 to 34 days, median 19, and the
specification asks for a seven-day one by name. The data does not agree with
the shape of the index: **282 of 319 destinations are a complete trip in three
nights or fewer** and 181 in a single night, every one authored per destination
in `nights`. A journey is an authored editorial record — legs, nights, a
summary and a route — so four short journeys are a writing task and not a
derivation, and inventing them would be authoring a measurement. The planner
answers a weekend today ("weekend" parses to three days, "long weekend" to
four), and the trigger for the index is somebody writing them.


**THE INSTRUMENT HAD FIVE OF THE POPUP'S SIX FIELDS AND NONE OF ITS
PICTURES.** /map's popup prints a destination's name, country, region,
summary and link off the baked `mapinfo` block, and the register holds a
photograph for **105 of the 319** — which the one page whose whole job is
opening a destination showed none of. The three fields are the derivative
URL, the photographer's own alt and the fragment `render.credit_html`
composes: **46,505 raw bytes and 10,045 over the wire**, measured by gzipping
the page with the fields and without, and `weight.max_page_kb` moved 444 →
489 with that arithmetic in the register. **The credit is carried rather than
composed in the browser** because it is a licence obligation with exactly one
implementation here — the same reason the planner receives
`cities.shotCredit` — and it is shown at `opacity: 1` rather than revealed on
hover, because a popup is transient and a credit nobody can reach is not a
credit. Reading it out of `/api/atlas.json` instead would trade 10 KB against
a 350 KB fetch to show one picture.

**/search PRINTED 550 AND SHIPPED 1,064.** The head was a hand-assembled sum
of SEVEN collections and `search_api` writes TWELVE kinds, so the page
understated its own index by **514 records** — all 255 places, all 197
experiences, the seventeen interests, the thirty-six categories and the nine
corners of Europe — on the one page whose entire subject is the extent of an
index. The resting state listed the same seven under a sentence promising
"every kind is browsable without searching at all", which is the `pop_line`
shape: a list that omits part of its own set reads as a policy. Both are
derived from the rows the browser filters now.

**AND THE REPAIR PUT THE PAGE OVER THE MONOTONY CEILING — 56% AGAINST 52,
twelve rows of one component on a 1,783-pixel page.** Shortening the list is
the one fix this page cannot take. What the count-sorted list threw away is
that the twelve are not flat: five of them NEST — nine corners of Europe, 50
countries, 130 regions, 319 destinations, 255 places — and seven cut ACROSS
that. Sorting by size put Places above Countries, which is arithmetically
true and says the wrong thing about a nested atlas. Two bands, **56% →
31%**, and the chain is a classification while every count beside it is a
measurement. **And taking the plural verbatim matters on exactly one row**:
lower-casing a heading and re-capitalising its first letter printed *"Regions
of europe"*, which is pluralising-by-adding-an-s one fault over.

**`stops_at` WAS DERIVED, COUNTED AND DROPPED FOR THE LIFE OF THE GRAPH, AND
THE FLOOR WRITTEN TO CATCH EXACTLY THAT COULD NOT SEE IT.** `gathers` shipped
at zero once and the repair was a count per relationship in
`/api/graph.json` and a floor on each in `checks.py`. That floor was **a
hand-typed list of the NINE relationships that happened to be non-zero the
day it was written** — and `journey stops_at place` reads `leg.get("places")`,
a field **none of the 121 legs in this dataset has ever carried**, so it
emitted nothing, and the counts block could not show it because it was built
from the edges that were EMITTED. **A floor over the keys that are PRESENT is
blind to exactly the case a floor exists for.** `pages.GRAPH_RELATIONSHIPS` is
the one declaration now: `graph_api` seeds its counts from it so a zero is
published rather than absent, raises on an edge type the table does not
declare, and `checks.py` reads that table rather than naming nine
relationships a second time. Each row carries a `floor` or an `awaiting`
sentence naming the authored field that would create it. Proved red five
ways, including the two that are about the instrument: a relationship at zero
omitted rather than published, and one declared as awaiting that starts
emitting.

**AND IT IS NOT DERIVED FROM THE LEG'S DESTINATION, WHICH IS THE AVAILABLE
SHORTCUT.** A journey passing through Vienna does not stop at the
Kunsthistorisches. Asserting it does would author an editorial claim out of a
containment fact, which is the Data Integrity Rule, and it is why this
relationship waits on somebody writing the field rather than being filled in.

**AND 96 PLACE PAGES HAD ALREADY MADE THAT CLAIM IN PROSE.** `back[cid]
["journeys"]` is every journey with a leg in the TOWN, and the place page
headed it **"Journeys that stop here"** — so the Alpine Grand Tour, which has
a night in Chamonix and says nothing about the Mer de Glace, was published as
stopping at a glacier. The links were right, the journeys were right, and
only the heading was wrong, which is the half no count reads; `section-audit`
asserted the literal string, so the audit was green ON the defect. The
heading names the destination now — *"Journeys through Chamonix"*, the form
the region page has always used for the same relation one level up — with a
lede saying what is not held. `c_journey_claim_subject` is on the **promise
rather than the wording**: a page may name a place as the subject of a
journey relation only when the graph holds a journey-to-place edge, read off
the published count, so it relaxes by itself the day `stops_at` is real.
Proved red on all 96.

**94 OF 150 RECURRING FIXTURES WERE INVISIBLE TO THE KNOWLEDGE GRAPH.** A
festival is held on the COUNTRY and 56 of them name a city, and the edge was
only emitted inside the per-destination loop — so /events published 150 and
the graph knew 56, which is the `pop_line` shape arriving in an index rather
than in a sentence. Both edges are drawn now, because both are true and they
answer different questions; `part_of` and `located_in` already target two
entity types each, so one relationship with two targets is this document's
own idiom. `happens_in` 56 → 206. **And the guard is the exact form rather
than the floor**: every fixture must produce a country edge, because a round
number below the current count goes on passing when half of them stop being
drawn.

**NINE ASSERTIONS IN THE SECTION AUDIT READ `x in SPEC or True`.** §36's
subject is whether the specification's thirty-two entities exist in the
model, and nine of its assertions were True whatever the model held — the
`c_photo_safe_area`-matching-nothing failure with the tell written into the
source. Each entity is counted off the running data now, or named as held
under another shape, or named as refused **against the promise that refuses
it** — and three of those refusals were pointed at the wrong file or the
wrong wording on the first run, which is the point of asserting them. 12
assertions → 28. §37 read **BUILT** while its own summary named place →
journey; it is PARTIAL, and its assertions read the published graph rather
than a page heading. 4 → 13.

**AND EIGHT OF THE NINE STORIES HAD A DERIVABLE JOURNEY AND LINKED NONE.**
§34 asks an article record for "Related journeys"; measured, the nine stories
have one to six journeys with a leg in a destination they are written about,
and every story page linked zero. **Both ends of this relation are
destinations** — a story's `places` and a journey's legs — so nothing is
manufactured by drawing it, which is exactly what separates it from the edge
the graph publishes at zero. The heading was written honestly the first time
for once: *"Journeys through these places … They are not about the story."*
And an authored **SEO title is refused** rather than added: the headline, the
tab title and the og:title are one string, and a second name for one thing is
two names waiting to disagree.

**A CHECK APPENDED AFTER `main()` IS DEFINED AND NEVER REGISTERED, AND THE
RUN STILL SAYS EVERY CHECK PASSED.** Sixty lines of new check went on the end
of `checks.py`, below `if __name__ == "__main__": main()`, so the decorator
ran after the suite had finished: the run reported every check passing on the
same total as before, with no error anywhere. That is *a green run that
has stopped counting* arriving through the file's own layout rather than
through a shadowed variable. **Read the total, not the word.**

**AND THE CHECK'S FIRST DRAFT BROKE THIS FILE'S MOST REPEATED RULE.** "Ortisei
& the Dolomites" is `&amp;` in the shipped HTML and `&` in the record, so five
correct pages were reported as making the claim the check exists to refuse.
*One normaliser, both sides* — fifth occurrence, and the first inside a check
written in the same hour as the paragraph recording the fourth. The heading is
unescaped rather than the name escaped, because what a reader gets is the
unescaped form and that is the thing being judged.


**A PAGE CALLED FJORDS HELD MARSEILLE, AND THE FLOOR THAT WOULD HAVE REFUSED
IT WAS ONE FAMILY OVER.** `FACET_MIN` is three, and the reason written above
it is that below three a page is a heading over a list a reader could have
seen in full on the page they came from. That is exactly true of a
sub-category — `/experiences/<cat>` lists every invitation the category holds
— and **the sub-categories never got a floor at all**, so two of the
twenty-eight shipped a single row. The smaller was worse than thin:
`/experiences/nature/fjords` declares five keywords, **no experience in this
atlas mentions a fjord**, and the page matched one thing on `calanque` — so a
reader arriving from a search for fjords got a French Mediterranean inlet.
The keyword is not the fault and is kept, because a calanque is a drowned
valley and the classification is editorial; the fault is publishing a page
for a subject the atlas holds nothing of. `/experiences/history/renaissance`
was the other, one entry, Lucca.

**THE FLOOR IS `FACET_MIN` READ RATHER THAN A THIRD THREE TYPED** — the
dispatch cap's own lesson, where four copies of one number disagreed and a
whole sitting was spent before anything said so. **And it had to reach four
callers, of which the check found the third and the fourth found itself**:
the build loop emits the pages, the category page links them, `search_api`
indexes them, and `checks.py` re-derives the expected page count. The search
index was caught by an existing check — *"points at a page which is not
built"* — and the count check by the rebuild after it. A fifth caller
inherits the rule for free.

**AND A SUB WITH NO PAGE KEEPS ITS COUNT AND LOSES ITS LINK**, which is this
atlas's own answer to a map dot the page cannot name: the measurement is real
and the navigation is not. Dropping the row would hide the very figure that
explains why there is no page, so the bar and the number stay and one derived
sentence says which sub, how many it selects, and against what floor — the
alternative being a row that reads as a broken link. `routes.count` 1,034 →
1,032 and `routes.hash` moved, which is the deliberate act those rows exist
to make visible.

**A VERDICT CAN CONTRADICT A LIVE CHECK AND THE AUDIT STAY GREEN, BECAUSE THE
ASSERTION PINNED A FUNCTION NAME.** §47 published *"distance and mode are
computed and stated for every hop"* — and `hop_note` REMOVED the mode, with
its own docstring recording why ("69 km — a local train or a short drive" for
a leg that is about 170 km round a mountain range), and `checks.py` carries
`MODE_CLAIMS`, which fails on any page claiming one. Two sentences in this
repository, in direct contradiction, both true when written. The assertions
were `"hop_note" in src(...)` and `"hopNote" in src(...)`: symbols that still
exist, so nothing could see that their behaviour had reversed. **The
thirteenth assertion here to pin a shape rather than a promise, and the first
where the shape was a function's NAME.**

Measured, the honest distinction is clean and checkable both ways: **all
seventeen journeys carry an authored `transport` list** — rail, ferry, bus,
cable car, postbus, river boat, bicycle, flight, car, on foot — **and none of
the 121 legs carries one.** A journey's transport is editorial record; a
hop's mode is refused because a great circle cannot support it. That is the
Data Integrity Rule stated as a page family. Proved red by putting a `mode`
on one leg.

**AND §40's TWELVE URL SHAPES ARE ONE LITERAL MATCH AND ELEVEN EQUIVALENTS,
WHICH THE VERDICT HAD TO SAY.** The specification writes
`/europe/norway/bergen`; this atlas writes
`/europe/norway/fjord-norway/bergen`, because **the region is a real level
with a page of its own** and the breadcrumb a check already validates names
it — a URL that skips a level the hierarchy has a page at strands every one
of those pages off the path and makes the path disagree with the breadcrumb. Measured,
a two-level URL would collide **zero** times today, which is a fact about
today and not a reason. The other two are a bare `/europe/` prefix, and
`routes.hash` exists precisely so a URL cannot move without somebody deciding
to. Of its four experience routes, `castles` has no surface and should not:
**one experience in this atlas mentions a castle.**

**AND §41 WAS CHECKED FOR THE FAULT THE LAST ROUND FOUND AND DOES NOT HAVE
IT.** A destination linking a journey it has no leg from was the suspicion —
Bergen links none — and the measurement says the atlas is right and the
suspicion was wrong: **journeys derivable on 76 destinations and linked on
76, themes 88 of 88, stories 32 of 32, and all 100 facet pages linked from
their own destination.** Every destination carries at least nine inbound
links and the median is 26. Bergen has no journey because **no journey in
this dataset visits western Norway at all** — the three Norwegian routes are
Tromsø and Lofoten — which is the seven-day-journey content gap one family
over, and inventing a Norwegian Fjord Journey to satisfy a diagram would be
authoring an editorial record.


**EIGHTEEN VERDICTS CHECKED AND EIGHTEEN SURVIVED, WHICH IS WORTH RECORDING
BECAUSE THE LAST TWO ROUNDS DID NOT.** §53–70 of the specification is mostly
a backend: an admin dashboard, moderation, fraud prevention, eleven user
roles, analytics, a contributor programme. Every one is already tracked with
a verdict that says what needs an account, a server or a socket — so the work
was falsifying the ones that make a positive claim rather than building.

**§59's was the falsifiable one and it is exactly true.** "Local currency
alongside euros on every country page, from a dated, rounded, hand-recorded
table" — measured, all fifty carry a euro figure and the pairing reads
*"Typical day €115–260 per person ≈ kr1,320–2,990 indicative"*. The table
declares all ten currencies the specification names plus fourteen more, with
`as_of` and a note saying a bank's rate will be worse and the date will get
older; `planner.js` spends it. **The table is read rather than computed and
discarded**, which was the suspicion worth checking, because this repository
has now found that shape four times.

**§57 NAMES SEVEN REQUIREMENTS AND THE AUDIT ASSERTED FIVE.** Keyboard
navigation was measured in the browser and simply never claimed here. And
**"captions where appropriate" was satisfied by there being no time-based
media at all** — zero `<video>` and zero `<audio>` on the built site — which
is the easiest kind of requirement to lose, because absence goes red on
nothing and the day somebody embeds a clip there is no subject for a check.
So the guard exists while the count is still zero, written in advance for
once rather than after the fifth occurrence: it fails on the first media
element that ships without a captions track, and it counts PAGES rather than
media, because a check reporting `(0)` looks exactly like the two this
repository found examining nothing. Proved red on an injected `<video>`.

**§58 SHIPS ONE LANGUAGE OF ELEVEN AND THAT IS THE MECHANISM WORKING.**
`SHIP_THRESHOLD` is 1.0 and `fr.json` holds 16 of the 57 interface strings,
so French is a demonstration rather than a locale and the build will not emit
it. A half-translated language is worse than an untranslated one, and the
threshold is what makes that a rule rather than an intention. The
specification's *"do not hard-code text"* applies to the interface chrome,
which is in `data/strings/`; editorial copy stays beside the thing it
describes.

**AN AUDIT CAN DISAGREE WITH ITS OWN EVIDENCE AND STAY GREEN, AND §71–99 HAD
THAT TWICE.** Twenty-nine sections of the specification arrived and
twenty-seven of their verdicts survived being re-measured — §76 and §77 are
absorbed with their refusals published on the pages themselves (/method's
*"Two dimensions this refuses to compute"* for Accessibility and Romance, and
/plan's *"it carries the specification's popularity weight as well, because we
hold no visitor numbers for anywhere"*), §79's peak/shoulder is authored on all
fifty countries with **off derived as the complement**, and §80 is this atlas's
own published position rather than an unbuilt feature. What did not survive was
the arithmetic of two sections against their own assertions.

**§97 PUBLISHED "TWELVE OF THE FOURTEEN PASS" AND ALL FOURTEEN ASSERTIONS WERE
GREEN.** The two that do not pass are the account, and the audit had no way to
say so: `saveplan` exists and `routeFromParams` exists, which is true of a
product with an account and true of one without. Both halves are observable —
the mechanism is browser storage and **the page has to SAY so** — so the
criteria now also read /my-europe's own *"lives in your browser and nowhere
else … there is no account"* and its *"Sync across devices · an account, a
backend and a data controller"*. A criterion met locally on a page that implies
an account is the failure worth catching; the missing backend was already
recorded.

**AND §98 NAMED TWELVE MODULES, EXAMINED ELEVEN, AND THE ONE IT NEVER EXAMINED
WAS AUTHENTICATION — one of the two its own verdict says do not ship.** That is
§36's nine `or True` assertions arriving as an *omission* rather than as a
literal, and an omission is the harder of the two to see: nothing reads as
wrong, the section simply says less than it claims. The refusal is asserted
against the promise that refuses it, exactly as §36's are — /how-it-works'
Accounts row and `docs/legal-position.md`'s entity gap. And module 12 read
`bool(src("docs/content-report.md"))`, which cannot tell *the figures ship as a
committed report* from *the dashboard shipped*: **a file existing is not a claim
about what stands in for what.**

**TWO ASSERTIONS WERE THE LITERAL `yield True`, AND ONE OF THEM CARRIED THE
STRONGEST SECURITY CLAIM IN THE AUDIT.** §55 asserted *"no user-generated
content exists to moderate"* and §61 *"no secret is committed"*. Both claims
are measurable and both measurements are stronger than the sentences: **nothing
on this site accepts a submission** — zero `method="post"` anywhere, one
`action` on the whole built site and it is a GET to /plan, which is navigation
— so there is no route by which content could arrive; and the security promise
is not that nobody typed a key, which is a hope and is what three real
acquisitions were already stopped by, but that a **registered** gate refuses a
committed credential and the key reaches the workflow only as
`${{ secrets.PEXELS_API_KEY }}`. Proved red four ways: an injected `<form
method="POST">`, a literal key in the workflow, /my-europe claiming an account,
and /how-it-works renaming its Accounts row — because *a check is not proved by passing; it is proved by failing on the thing it is about*.

**AND A NEEDLE MAY NOT SPAN AN ELEMENT.** `has()` collapses whitespace and
does not strip tags — the right trade, and the reason is written on it — so
*"Needs an account, a backend and a data controller"* failed on a row whose
markup puts *Needs* and what it needs in different elements. Two needles, not
one sentence.

**BUILD PACKAGE v1 ARRIVED AGAIN AND ITS FIRST SENTENCE IS THE ONE THING THAT
CANNOT BE TAKEN.** It proposes freezing the product as *Europe Atlas*, with
the name provisional pending domain and trademark checks. The caution is
right and the conclusion is already this repository's: `docs/brand-lock.md`
locks EuropeDoor, the section audit has carried §1.1 as **LOCKED** since the
first specification proposed the same rename, and the trademark position is
recorded rather than assumed — EUROPEDOOR is in use in the doors trade, so no
®, no ™, nothing announced. **A later document does not get to rename a
product.** Its §2 was already audited field by field in
`docs/schema-mapping.md`; its §18, §27, §35–36 and §38–39 are
`docs/frontend-architecture.md`, `docs/api-architecture.md`, §40 and §60–61.

**AND THE CHECK THAT REFUSES THAT NAME WAS A GUARD ON A PUNCTUATION MARK.**
`c_brand`'s banned list read **`"Europe Atlas ·"`** — the name plus the middot
a page title happens to put after it — so the bare phrase passed, and
/how-it-works shipped `<h3>Europe Atlas</h3>` as the name of a built feature,
on a page listing what is built, for the life of that band. That is the
`fetch.py` blocked-list failure inside the brand lock: **a guard on a label is
a guard whoever renames the product gets to choose**, and here the choice was
whether to type a middot. The bare phrase is refused now — the site calls this
dataset *the Atlas* 597 times and had exactly one place where it spelled it as
a product name — and a naming discussion belongs in `docs/brand-lock.md`,
which is not a page and is not scanned. Proved red on the string that was
shipping.

**NOTHING HERE HAD EVER MEASURED A LAYOUT SHIFT, AND ONE PAGE OF THIRTY WAS
AT 0.3025.** §49 asks for "excellent Core Web Vitals"; the only performance
gates in this repository are ceilings on BYTES, and **bytes are not
movement** — a page can be 26 KB and still throw its own content down the
screen after it has painted. Measured across every family at 1280,
twenty-nine of thirty are **exactly 0.0000**, which is what a static site
with `width`/`height` on all 1,617 of its images and 64 `aspect-ratio`
declarations should be. /search was **0.3025**, past the 0.25 that reads as
poor.

`search.js` replaced the build's own 1,185-pixel index breakdown with
`<p class="small">Loading the index…</p>` and put it back when the fetch
resolved: `#results` 25px at 72ms **with `readyState` already complete**,
1,185px the instant `/api/search.json` arrived, 266 pixels of push that sent
the footer off the fold. **Delaying the index by 400ms moved the jump to
448ms, which is what proves the fetch is the trigger rather than the parse.**

**And the line that did it sat 168 lines below a comment saying it had been
removed.** `AT_REST` captures the band and restores it — the half that got
written — and the assignment that threw it away first was left standing, which
is `.picstory` exactly: the repair addressed the cousin and left the cause.
**A loading state over a complete page is a regression dressed as feedback**,
and it is honest only where the reader is waiting for something they asked
for, which is the `?q=` arrival. 0.3025 → 0.0000.

**THE CEILING IS 0.02 RATHER THAN GOOGLE'S 0.1**, because a threshold a site
is nowhere near is a threshold that admits a real regression: every family
here is at zero, so the honest ceiling is *essentially zero*. The sweep takes
its own page — `buffered: true` reports whatever that page already loaded,
which is the dead-rule scan's recorded failure — carries a reach floor, and
names the ELEMENT that moved with its box before and after, because a CLS
figure with no element in it cannot be diagnosed. The cause is asserted
statically beside it: **no image ships without its intrinsic size**, 1,617 of
1,617, with its own floor because an assertion about an empty set counts
exactly like one about a page.

**AND §53 STATES THE SEED AS A DENSITY WHERE THE REPORT WAS COUNTING SUMS.**
10–30 places and 5–15 experiences *per destination*, against 0.80 and 0.62
measured. `docs/content-report.md` reported only totals, so *places: 26% of
MVP* was true and read as most of the way there on the wrong axis — **a sum
divided by a met denominator reads as progress**, and the destination count
met its target while the place count did not. On the seed's own floor places
are **8%** and experiences **12%**. **And the specification disagrees with
itself**: §67 asks for 1,000 places over 150 destinations, which is 6.7 each
and under §53's own floor of ten, so this repository had been reporting
against the looser of two numbers one document publishes. Both framings are
now in the report, and neither is a code change.

**THE COMMERCIAL LAYER IS BUILT AND NOTHING IS SERVING, AND THE NUMBER OF
GATES BETWEEN A CAMPAIGN AND A READER WAS TYPED IN THREE PLACES AND WRONG IN
ALL THREE.** The advertising specification's thirty-three sections are mapped
in `docs/advertising.md` — twenty-six built, four declared and off with an
objection or a trigger attached, one partial, one a measured departure. The
registry is `data/advertising.json`, the service is `tools/lib/ads.py`, the
seam into a page is `render.ad_slot(path)`, and **an off slot emits zero
bytes**: no container, no placeholder, no reserved height, which is the
OPPOSITE of `ed_slot()` and for the opposite reason — there the reader is an
editor and the declared photograph surface IS the acquisition list, here the
reader is a traveller and a reserved advertising box on a page with no
advertiser is this product advertising that it would like to carry
advertising. The marker is what `checks.py` tests and never the words,
because /for-businesses publishes the whole disclosure vocabulary and the
Stay layer's own disclosure carries *sponsored* on every destination page
that has one: a guard on the word would fail two surfaces that are correct
and could never be made to pass.

`ads.py`'s docstring said **five conditions**, /for-businesses' lede said
"five separate conditions" and listed five, and `may_serve()` tested
**eight** — the two per-placement flags and the campaign's own status were in
the mechanism and in neither sentence. That is the dispatch cap exactly, and
`/map` printing the old projection's name for a year. `ads.conditions()` is
the one declaration now, `may_serve()` is `all()` over it, the page prints
the LIST rather than a count, and `tools/ad-tests.py` reads that list and
proves **each entry alone refuses** — so a condition added tomorrow is
proved tomorrow, where a typed five would quietly stop covering the set.

**A BRAND TOKEN IS NOT A HOSTNAME, AND `readForm` CONTAINS `adform`.** The
third-party network refusal was declared as twenty-one bare tokens and the
check reading them required a dot, so **nineteen of the twenty-one were never
tested** and appending `doubleclick.net` to a script left it green — the
mutation that proved the guard was caught by the OUTBOUND-LINK check
instead, on a page, where this one has no reach. Removing the filter then
failed `planner.js` on `readForm`, which is `cell` catching `cellar` one
family over. `checks.py`'s commercial-map-host refusal settled this years ago
and says why on its own list: *hostnames rather than a vague substring,
because a page that says "the map" is not a violation and a check that cannot
tell the difference gets switched off.* Twenty-six hostnames now, proved red
on a script.

**AND TWO OF THE SIX TARGETING DIMENSIONS RETURNED NO MATCH IN SILENCE.**
`context_for()` reads a path, so it answers country, region, destination and
experience category. `travel_interest` is a property of the destination
record rather than of the path and `language` needs a second locale reaching
`SHIP_THRESHOLD`, so a campaign targeting either returned False from
`_targets_match` — correct behaviour, and indistinguishable from a target
that simply did not match this page, which is `opts.geoTooNarrow` computed
and read nowhere. Both stay declared because the brief's vocabulary is right;
both raise with their own trigger named now.

**The simulated ON state lives in memory and never on disk.** A suite that
edits the registry it is testing can leave the repository in the state its
own failure produced — the Media Desk's suite learned the harder version,
renaming two licensed originals aside and having a later run overwrite them.
`ad-tests.py` swaps `ads._cache`, so there is nothing to restore, and its
last block asserts the registry's bytes and the built site are unchanged by
the run. **Nothing to restore is stronger than restoring carefully.**

**And the wall moved, in public, on the page whose own sentence is the
procedure.** /for-businesses has published *if that wall ever moves, it moves
in public, on this page* since before the registry existed, and the brief's
nine placements are every one of them editorial. So the position is now
*paid placement buys a declared slot*, the page states the sentence it
replaced, and `checks.py` asserts the page and the registry agree **in both
directions** — a page can keep a promise the mechanism has stopped keeping,
and a mechanism can be quietly stricter than the page a reader is reading,
which is worse, because then the published position is the looser of the two.
The substance did not move: ranking, weighting, curation, scores, result
order and editorial copy were never for sale and are not now.
`tools/monotony.js` read /for-businesses at 51% before this and reads 27%
after, because the page gained three bands that are not its provider list.



**TWO LABEL FAMILIES ON ONE DRAWING, AND ONLY ONE OF THEM HAD A BOX.** Every
label here goes through one machine — `place_label_box` measures it against
`LABEL_METRICS`, tests it against the aperture, tests it against the names
already down, and drops it when it fits nowhere — and that machine is why
the destination plates went from 271 overlapping pairs to zero. **The water
labels went through none of it**: `sea_names()` picked a point with enough
open sea round it and emitted a `<text>`, with no width model, no aperture
test, no collision test and nothing for anybody else to avoid. So
`name_countries()`, which has all four, was arranging half a layer — its own
comment promises each name is tested *against every name already down*, and
that was true of its own family and of nothing else. Measured in Chromium at
1280, 1440 and 1920: NORTH SEA through UNITED KINGDOM by **68px** and /map's
by **80**, BAY OF BISCAY through FRANCE by 41, IONIAN SEA through GREECE by
49, BLACK SEA through ROMANIA by 18.

**AND THE TWO DRAWINGS IT HAPPENS ON ARE THE TWO NO OVERLAP CHECK HAS EVER
LOOKED AT.** Twenty-nine shapes on the built site carry more than one label
family and **twenty-eight are a `.minimap`**, which is the selector both
existing sweeps read; the twenty-ninth is the hero, which is not a `<figure>`
at all, and the thirtieth is `#europemap`. The only two drawings that carry
`.seaname` beside `.cname` are the largest pictures on the site and they sat
outside the check by a selector nobody re-read when the sea names were added.
Fourth occurrence of the same shape — the check matching
`pointsmap arched"><svg` that examined 0 dots on a site with 130 region maps,
`c_one_plate_per_thing` reading zero once the last abstract plate came off,
and the crop-box sweep making two green assertions a run about elements the
site no longer had. **A selector, not a figure class**: whether two labels on
one drawing overlap is not a question about which element wraps it.

**THE PINNED FAMILY IS COMPOSED FIRST AND THE FREE ONE IS TOLD WHERE IT
WENT.** A sea name has one position, the middle of its own water; a country
name has nine anchors and four positions at each. The country plate settled
that order already, when reserving a box across the middle of Albania ate
Tirana's label and left a star nothing named. `sea_names()` returns its boxes
with its markup and `name_countries(reserved=…)` seeds them into `taken`.
**`/map` had the order backwards** and composed the free family two lines
before the fixed one existed. **One model per type size, and this family
needed two**: the face and the .34em tracking are shared and the size is not
— 13 units in the hero's 1,120-unit frame against 11 in /map's 1,000 — so the
boxes differ by 18% and one model cannot serve both. Fitted as the upper
envelope over every name each drawing renders, with the browser's own
`getBBox`, and the browser re-measures it, because a static check re-running
a fitted model only ever agrees with it and **an envelope that UNDERSTATES
lets a country name into ground the drawing has already spent.**

**What it cost is counted rather than glossed.** Five pairs to zero at all
three widths. The hero held its cap of sixteen with four names moved:
UNITED KINGDOM came down 22 units off the North Sea onto the slot IRELAND
wanted, so Ireland lost its name and LATVIA — the next country by drawn area
— took the freed place. /map went 13 → 12 and the one that went is GREECE,
precisely the name that had been drawn through IONIAN SEA. Each keeps its
shape, its frontier, its link and its accessible name. **Raising the cap to
save Ireland would be tuning the design to one case**, and drawn area is
deliberately a property of THIS picture rather than a judgement about the
country. And **`most` was a parameter nothing read** — the body sliced `[:6]`,
so a caller asking for four got six; neither caller passed it, so nothing a
reader sees was ever wrong and the lie was in the interface.


**A CANDIDATE WAS RENDERED UNDER A DIFFERENT PICTURE'S SUPPRESSION, AND THE
COMMENT ABOVE THE LINE STATED THE RULE IT NEEDED.** `contact_sheet.py` renders
the real homepage once per candidate so a person can judge a photograph inside
the composition before it is bought, and it substitutes by **replacing the
register and leaving `design` untouched**. `home()` suppresses the hero's
credit while a design asset claims that purpose — correctly, because printing
a photographer's name under somebody else's picture is a false attribution
worse than clutter — so from the commit that registered `london-thames` as
standing in for `home-hero`, the sheet drew the CANDIDATE and credited NOBODY.
The one artefact whose job is to show the real composition was showing neither
state, and the credit is a measured part of that composition rather than a
footnote: its own scrim, 6.90:1 by arithmetic. The comment directly above the
substitution says *the register is REPLACED for this render, never merged
into: a candidate must not inherit a real row's provenance by sitting beside
it in the same dict* — **applied to `images` and not to `design`**, which is
*a rule stated once and applied to one of its call sites*, inside the comment
that states it.

**And nothing caught it for six commits because the gate was not run.**
`python3 tools/photo-tests.py` is on the list above, costs about five minutes,
and five consecutive commits shipped without it while every other gate was
green. **A gate people skip finds things six commits late**, which is the same
sentence this file already writes about a gate that cannot fail — and the
`git log -S` that dated the cause took one command, where the reasoning that
would have guessed at it took twenty minutes.


**THE EMPTY PART OF THE HOMEPAGE WAS A MARGIN THAT ESCAPED ITS BOX, AND
`clip-path` CLIPS WITHOUT CONTAINING.** The window plate uses `clip-path:
inset(0)` because it is the one property that clips a `position: fixed`
descendant — recorded at length above — and the assumption that arrived free
with it is that it also establishes a block formatting context. It does not.
`.shotsay` is the window's first child and takes `margin-top: 62svh` to set
the type two-thirds down the picture; with no BFC that margin **collapses
through** the window and moves the window itself down the page instead. The
plate mark ended at y=964 and the window opened at y=1523: **558 pixels of
blank wall at 1280 and 523 at 390**, which is 62svh of 900 and of 844 to the
pixel. `display: flow-root` contains it and is the one repair that does NOT
also make the box a containing block for a fixed descendant — the picture
still stands still, proved by scrolling 300 pixels and measuring 0. 558 → 16,
plate 03 1,653 → 1,111, the document 542 pixels shorter.

**AND `voids.js` REPORTED ZERO VOIDS ON THAT PAGE, CORRECTLY.** It finds a
band over 90px with NOTHING painted in it, and every slice of this run
carried the plate mark, a hairline or the top edge of the window — so not one
was empty and the band still read as a hole. **A band with ALMOST nothing in
it is a different measurement** and nothing here had ever taken it.
`tools/density.js` is the horizontal union of everything that paints, per
50px slice, as a share of the page's own width; 27% of the homepage was under
a fifth covered and is 23%. It reports and **cannot become a gate**, on
`voids.js`'s own reason inverted: a floor on coverage is satisfied by widening
every measure until the page is a wall of type.

**And its first version reported the photograph as the largest hole on the
page** — 850 pixels at 1% covered inside the one plate that IS a full-bleed
photograph. A `position: fixed` rectangle is viewport-relative, so `+ scrollY`
files it in whatever slice the page happened to be scrolled to; a screenshot
at y=1500 showing London filling the frame is what disproved it. What such a
box paints is the whole of its CLIPPING ancestor. **The first correction read
`position` on the child alone and changed nothing**, because the fixed element
is the parent — the walk goes up the whole chain. *The eye finds a defect and
it does not confirm one*, applied to an instrument rather than to a page.


**A TWELVE-PIXEL GAP BETWEEN A MENU AND THE WORD THAT OPENS IT IS A MENU NO
POINTER CAN REACH.** The bar names six rooms and three of them carry a field
of four or five links, revealed by `.navroom:hover` with no JavaScript
anywhere. **An absolutely positioned child is out of flow and contributes
nothing to its parent's box**, so the twelve pixels between the room's bottom
edge and the panel's top edge belonged to NEITHER element: the instant the
pointer entered that band `:hover` stopped matching and the panel went to
`display: none`. Measured in Chromium, moving from the middle of the word to
the first link in the panel:

| mouse events | the panel |
|---|---|
| 1 (a teleport) | survives |
| 5 | gone |
| 12 | gone |
| 30 | gone |

on all three rooms at 1280, 1440, 1152, 1024 and 960. **Thirteen links
reachable with a keyboard and not with a mouse, on every page on the site** —
and the
keyboard route works precisely BECAUSE `:focus-within` never crosses the gap:
Tab moves focus straight from the room into the field. The suite already
asserted that sequence and was right to; it could not see this, because it is
the same promise asked of the other input device. Every link was present,
named, sized, focusable and `checkVisibility` true.

**The bridge belongs to the FIELD rather than to the room**, so it exists only
while the field does and there is no phantom hover target at rest — and it is
13px rather than 12 because `top` resolves against the padding box and the
field's own 1px border sits between that and the gap. A promise about movement
is proved by moving: the check pushes the pointer in 5, 12 and 30 steps and
asserts the panel is still there and the point under the cursor is inside it.
**It also asserts the room's own word is still the thing under the pointer**,
because the obvious bridge is one that covers the link that opens the menu —
proved red both ways, 9 of 15 with the bridge collapsed and 3 of 15 with it
four times too tall.


**AND THREE OF THE SIX ROOMS OPEN A DIRECTORY WHILE NOTHING SAID WHICH
THREE.** DISCOVER carries four links, ATLAS four, EUROPE five; JOURNEYS, PLAN
and STORIES carry none, and at rest all six were the same word in the same
type at the same weight. Thirteen of the bar's nineteen destinations could
only be found by hovering a word at random — **the same thirteen the hover
gap had just made reachable**, which is what makes it a repair rather than a
nicety: a repair nobody can find is not one. The mark is DRAWN rather than
typed, on this page's own rule that a go-link is a circle and a rule rather
than an arrow character: two 1px borders on a rotated square, 0.3em, five
pixels against the nine a `▾` would set, inheriting `currentColor` so it
lifts with the word and adds no second colour decision. **And it comes off
where the field does** — below 60rem the two rules that open a field are
undone, so the mark would promise a directory that cannot be opened.

**The assertion is the painted advance rather than the `content` property**,
because `getComputedStyle(e, "::after").content` computes to the SPECIFIED
value — the failure this file already records about `"0" counter(band)`,
where a check read the model back and reported nineteen families broken when
none was. A Range over the text node gives the glyphs, the element gives the
box, and the difference is the mark. Proved red both ways. **And the check's
own first version asked the wrong element**: `a.parentElement` is `.nav` for
a room with no field, and `.nav` contains every other room's field, so it
reported all six as carrying one and went red on the three that were correct.


**THE ATLAS INDEX LISTED FIFTY COUNTRIES AND DREW NONE OF THEM.** The
homepage's plate 05 carries the sentence *One continent. Fifty doors.* and
drew nine headings over fifty names in the body serif, in three multicol
columns: a sitemap, on a page whose argument is that geography IS the design.
Every one of those countries has an outline in `data/geo/`. That is the
/themes failure word for word — a page describing shapes its own closing
sentence is about and drawing none. `country_mark` is `country_door` at the
size of a word: the same own-frame fitting, the same `COUNTRY_DOOR_POINTS`
floor deciding which six are a ringed point (READ rather than typed a second
time), and no photograph, so no register row and no image request. **Three
ways were costed before one was built** — 628 KB for the lod1 doors, 18.8 + 9.8
for one shared silhouette and its lit rings, **8.4 KB** for fifty own-frame
outlines — and the cheapest is the only one that draws fifty DIFFERENT SHAPES
rather than nine pictures of Europe with different bits lit, which is the
wallpaper the aperture's own rule warns about. **And the first size was the
smudge**: a 2.1rem track renders a country 33 pixels wide, where Italy read
and Greece was a blob.

**AND A STRAY `*/` SWALLOWED THE RULE THAT LAID IT OUT, FOR THE THIRD TIME,
BECAUSE THE REPAIR THIS FILE DESCRIBES WAS NEVER BUILT.** The comment above
that size decision contained the characters `*/themes*`: the comment closed,
the prose after it was read as a selector, and the next whole rule — the grid
that puts a country's outline beside its name — was dropped. Every box was
still the right size and the tell was a `getComputedStyle` reading
`display: block` where the file says `grid`. This file already records the
fault twice **with the fix written out** — *a four-line scan for a `*/`
outside a comment finds both in a second* — and nobody ever wrote it, which
is `data-rotate` arriving in this file's own documentation. **A described
repair is not a repair.** `c_css_comments` is those four lines, both
directions, 1,160 comments examined, proved red on a stray close and on an
unterminated open.

**AND `country_glyph` WAS ALREADY TAKEN, IN PYTHON.** The first version of
that function carried the name of the country card's own picture eight hundred
lines below it; Python resolves the LATER definition, so the build called that
one and stopped on its signature. *Grep the stylesheet before naming a
composition* is written here about a CSS class and is the same rule about a
module-level function — loud this time only by luck, because the two
signatures differ.


**NINETEEN OF FORTY-SEVEN FAMILIES LIT NO ROOM IN THE MASTHEAD, INCLUDING A
ROOM'S OWN PAGE.** `aria-current` was decided by the AREA string a page
builder passes, and the table's area sets cover the indexes rather than the
pages the FIELDS point at — so /about, /how-it-works, /method, /sources,
/beyond-the-obvious and **/manifesto, which is the EUROPE room's own href**,
were every one of them unmarked. A reader standing on the page a word in the
bar links to was told nothing by that word. **The field already declares the
answer**: a room is current when the reader is on its own page or on any page
its directory names, both of which are in the same table, so the test is
derived from the row rather than from a second hand-listed set somebody has
to extend. It is `bottom_nav`'s own prefix rule, which the masthead never
got. 28 lit one → 34, 19 lit none → 13, and the thirteen are the homepage,
the 404, the two utilities and nine institutional pages that are in no room.

**AND THE AREA WINS WHERE IT SPEAKS, WHICH THE FIRST VERSION DID NOT SAY AND
ONE PAGE PROVED.** `/discover/<macro>` passes `area="countries"`, which is
ATLAS, and its path sits under DISCOVER — so adding the path test lit both,
on a bar whose whole job is to say where you are. The area is the builder's
own statement of what the page IS and the path is the fallback for the pages
whose builder says nothing.

**AND A MARKED LINK COULD BE MARKED AND NOT LOOK IT.** `.navutil a` had the
transparent border and the hover colour and no rule for `[aria-current]`, so
/search and /my-europe announced a current page to a screen reader and showed
nothing to anybody else. Present, correct, announced and invisible.


**THE CEILING WAS TWENTY-TWO PIXELS UNDER THE BAR IT IS A CEILING ON.**
`--mast` was invented because every in-page anchor scrolled its target to
y=0, which is where the sticky masthead is; its own comment calls it *a
ceiling on the bar and a floor on everything that has to clear it*, and the
two values *the two measured heights rounded up*. **Then the bar grew** —
`.masthead-in` went from `--s3` to `--s5` of block padding, 58 to 82 at desk
width, with its own comment recording the move — and nothing moved the token.
Swept at twenty-seven widths: **over by 22.0 at every width from 961 up and
by 30.4 from 704 to 960**, correct only below 704. **The breakpoint was wrong
as well as the value**, because the bar becomes two rows at 60rem and the
token only noticed at 44. Nothing went red, because the three rules that read
it are offsets a section's own top margin was absorbing — a latent defect of
exactly the kind this token was invented to stop, in the token invented to
stop it, and *a comment claiming a ceiling the measurement does not support
is read as evidence*.

**AND THE BAR'S HEIGHT WAS STATED TWICE MORE.** `scroll-padding-top: 5rem` is
a third number for one height — 80 against 82 and 90 — and with
`scroll-margin-top` ALSO carrying the bar an anchor landed at `padding +
margin` = 156 pixels, 74 below a bar it had to clear once. **The two
properties are different questions**: the SCROLLPORT's padding is what the
bar covers and the TARGET's margin is the air above the heading. One copy
each, and the landing is a uniform 24–25px at every width where it ran 65 to
97. **The sweep is the check** — the half the token's comment promised and
nobody wrote, with 961 and 960 both in it because the two-row transition is
between them. Proved red on the old values at thirteen widths.


**THE RULED DIAGONAL THROUGH RUSSIA WAS THE FRONTIER INK DRAWING A FACT
ABOUT OUR DATASET.** The atlas register on the homepage's fifth plate had
the ground beyond the atlas under it already, in the same stone, so the FILL
crossed the 52°E cut with no seam — and `.lyr-land path` strokes every edge a
country ring has, and Russia's ring has one edge that is not a frontier. It
came out as a hard line from the White Sea to the north Caspian, in the same
ink as the Poland–Germany border, on the one drawing whose ground is meant to
be continuous. **The fill had stopped saying it and the ink had not.**

The land group is clipped two units short of that meridian. Nothing real is
lost: the easternmost thing this atlas draws is Azerbaijan at 50.6°E, about
eighteen drawn units west of the cut, and the two-unit sliver taken off Russia
shows the ground beyond underneath it, which is the identical fill. The
number comes from `doc["bbox"]` rather than from a typed 52, because it
belongs to the dataset. **And a meridian is a straight line under a conic**,
which is why two projected points describe the whole cut — and why it read as
ruled in the first place.

**A CLIP RATHER THAN A SECOND, STROKE-ONLY PASS.** The obvious shape is a
`<use>` of the land drawn twice, fill unclipped and stroke clipped, and it
cannot carry this stroke: a clone inherits `stroke` and does **not** inherit
`vector-effect`, which this file already records, and this frontier is .6 CSS
px at every render size on purpose. Duplicating 26 KB of path data for one
hairline is the other way.

**THERE ARE TWO HONEST ANSWERS TO A DATA CUT AND THE CHECK KNEW ONE.** The
hero drops the one country the cut runs through and draws no ground beyond
it, so there is no cut inside the picture; the register draws the ground and
clips the ink. `c_hero_dusk_reach` asserted `"lyr-beyond" not in h` — a claim
about the whole DOCUMENT — so it went red for a second drawing that was
right. It reads the hero's own `<svg>` now, and asks every other drawing on
the page the same question in the form that drawing answers it: a ground
beyond with no fade must show the clip. What stays refused is the third
answer, which is a stroked cut with nothing hiding it.

**AND `lyr-beyond` HAD NEVER BEEN A DECLARED LAYER.** `cartography.ORDER` is
the one place paint order is decided and the hero has emitted that class
since the ground beyond was drawn. Found by **mutation**: moving it under the
land proved nothing, because the order check ranked only the names the table
knows and `if g in rank` skipped the rest — so an undeclared layer could be
painted anywhere and no gate would say a word. Declared, and the converse is
asserted now: every `lyr-` class the site emits has to be in the table.

**AND THE ORDER CHECK READ A WHOLE PAGE WHERE THE PROMISE IS ABOUT ONE
DRAWING.** A flat list per document is the same question only while a page
carries one map. The homepage draws the hero and then the register, and the
register's first layer ranks below the hero's last, so two correctly ordered
drawings read as one page out of order. It is per-`<svg>` now, with a floor
on the drawings as well as on the pages, because a boundary regex that
stopped matching would examine nothing and report green.

**AND THE ROLE WAS DECLARED ON THE `<figure>` WHERE THE CHECK READS THE
`<svg>`** — /countries paid for exactly that slip, and a declared role on the
wrong element is a map with no declared role. Two more from the same run: an
eighth `line-height` a hundredth from two the file already had, caught by the
register in the commit that introduced it; and the ground beyond thinned at
6 units rather than 2.5, because it carries no name, no link and no frontier
and both are the same picture at this size — 11.5 KB against 7, measured by
rendering both.


**AND THE BROWSER SUITE FOUND A SEVENTH REDUNDANT DECLARATION IN THE SAME
COMMIT.** `.atsum` — the register's closing resolution — set
`color: var(--ink)` inside `.sheet-gal`, and that room binds `--ink` to a
literal for everything in it, because *a room whose ground is white in both
preferences needs ink that is dark in both* is a lesson this stylesheet has
already paid for. So the `<p>` already inherited exactly that value and the
declaration could never move a pixel. **The DECLARATION came out and not the
rule** — the scan names declarations, and the first pass that deleted a whole
rule on its word put an underline back under two homepage story links.
Verified the way this repository requires: plate 05 shot at 1280 and 390
before and after, byte-identical at both.


**THE LINE THROUGH RUSSIA CAME BACK AS A FILL ONE COMMIT AFTER IT WENT AS AN
INK.** The frontier ink was clipped two units short of the 52 degree meridian
because `.lyr-land path` strokes every edge a country ring has and Russia's
ring has one edge that is not a frontier. The FILL was safe at the time and
only at the time: the ground beyond the cut is the same stone, so there was no
step to see. Then the register was made to ANSWER the reading — every country
carries its corner's class, so scrolling to Eastern Europe lights the *shapes*
of Belarus, Moldova, Russia and Ukraine and not just the words — and lighting
Russia made its fill `--atlas-here` where the ground east of the cut stayed
`--map-land`. The diagonal from the White Sea to the north Caspian was back,
as a tone step instead of a stroke, in the commit that improved the drawing.
**The same defect arrived at from the other side**, which this file already
records of a fade, a shore band and a scrim.

**A COUNTRY WHOSE RING ENDS ON OUR BBOX CANNOT BE LIT WITHOUT DRAWING THE
BBOX.** So a cut country is CONTEXT on this band: it keeps its shape, its
frontier, its name and its link, and it is not lit. Derived from the
document's own rings against the document's own bbox — one named country
reaches 52.0°E and Azerbaijan, the next furthest, stops at 50.6 — so a dataset
that one day reaches the Urals stops excluding Russia without anybody editing
a list. And the resolve band NAMES it, because /countries already settled that
a set shown short says so rather than quietly showing 41 of 50.

**THE PANEL WAS DELETING THE THING IT DESCRIBES, AND `.atcue` WAS PROMISING A
MOVEMENT THE PAGE DID NOT MAKE.** Measured in Chromium at 1440 on the eastern
step: the panel's wash begins at x=760 of a plate running 409 to 1296 — the
whole eastern half at 90% paper — and the card's own words sit over Ukraine's
centre at (989, 482), `elementsFromPoint` returning `.atkick`. Four of the
nine corners are eastern or south-eastern, so on nearly half the sequence the
band lit ground a reader could not see. **A scrim that runs over the part of
the drawing a band is ABOUT deletes that band's subject** — /plan's finding one
page over, where the answer was to stop the overlap. Here the overlap IS the
composition the brief supplies, so the continent pans instead, which is also
what *Scroll to move through the continent* had been claiming while the
picture stood still. Ukraine 913–1066 becomes 802–955 and the topmost element
at its centre becomes its own lit path.

**THREE POSITIONS, NOT NINE OFFSETS.** Nine translate values would be nine
numbers typed into a stylesheet, wrong the day a country changes corner. The
build derives which third of the DRAWN span each corner's mass sits in — the
mean of the paths it actually emitted, so a corner cannot be placed by a
geometry the reader is not looking at — writes `data-pan` on the step, and
`atlas.js` copies one attribute to the stage. Four west, three centre, two
east. Authoring the vocabulary is allowed here and authoring the measurement
is not.

**AND A PAN ON A FRAME-FILLING DRAWING REVEALS THE FRAME.** Translating the
`<svg>` ELEMENT moves its crop with it, so the plate's own `--map-water`
showed on the far side as a hard vertical seam — measured at x=1163, stone one
side and water the other, the full height of the plate. The frame is 1120×800
and the geometry fills it exactly, so there is no margin to pan into. The
viewBox carries `PAN_MARGIN` units of spare geography each side now and
`xMidYMid slice` crops it back to 0–1120 to within half a unit, which is the
window every other measurement on this plate is about; the pan translates a
group INSIDE that window, where the margin is what comes into view. The
geometry has to be GENERATED over the wider frame as well — `landmass` clips
to the view it is given, so generating over `HERO_VIEW` and drawing inside a
wider viewBox moves the seam a hundred units out rather than removing it.
`weight.home_kb` 174 → 179, recorded.

**AND THE PAN IS UNDONE WHERE ITS REASON EXPIRES.** Below 62rem the stage is
undone, the map is a sticky band and the cards are a column under it, so
nothing is over the continent and a pan would only crop it — *a rule's reason
can stop being true when the drawing changes*, which this stylesheet records
about a glyph rule that outlived the 132-pixel drawing it was written for.


**THE DRAWING WAS AN OBJECT ON THE PAGE AND IT SHOULD BE THE ROOM.** Plate
05 held its map in a 1120x800 plate centred in the stage with a ruled
outline and a reveal inside it, on a white wall — measured at 1440 as a
rectangle from (409,133) to (1296,767) with the lead column's own figures
running under its left edge. *Border, fill, radius and shadow each say
"separate object, placed here by a system"*, which this stylesheet says
about a search box and a rail and says here about the one thing the band
exists to show. **Three ways out were rendered and two are refusals.**
Taking the outline off alone leaves the `lyr-beyond` ground as its own
rectangle — a slab of stone with three straight edges where it is clipped
to the window, which is /plan's context-land finding arrived at from the
other side. A second APERTURE is refused by `docs/signature-moments.md`:
plate 01 cuts the largest arch on the site and two doors on one page is the
wallpaper that rule warns about. What works is the one /plan already
measured — **the band's paper IS the map's water**, so the drawing paints
no ocean of its own and there is no seam to find — with the frame bled past
the stage by `--page-gutter`, the token `.sheet` pads itself with, so the
three edges where LAND meets it are off-screen. **White was rendered and
refused too**: at 1.36 against the stone it is a handsome engraving and it
makes a bay the same colour as the margin, which is the finding this
drawing already paid for once.

**AND THE PAN PUT LAND UNDER THE HEADLINE.** With the drawing filling the
band, the eastern steps slide Iberia and Britain under a 76px serif. Ink on
stone is 12.5:1, so this is composition rather than legibility — and the
answer both the hero and /plan reached is to give the words a ground rather
than to move them. `.atlead::before` belongs to the COLUMN rather than to
the stage, so it is exactly as tall as the words: a stage-height wash ran
over the scroll cue at the foot and read as the cue fading out.

**EIGHT CARDS AT ZERO ALPHA ARE STILL IN THE TAB ORDER.**
`pointer-events: none` stops a mouse and says nothing about a keyboard, so
the browser suite measured **38 links of 5,391 painting nothing even with
focus on them** — every country link and every corner heading in the eight
cards that are not current. That is `.doorgo` for the third time here.
Removing them from the tab order is worse, because this page is the only
route to them, so **focus drives the stage**: tabbing into a corner makes it
the corner being read, the card comes up, and the continent lights and pans
to match. It is the rule this site already applies to every hover-revealed
link it ships.

**AND THE PHONE OVERRIDE LOST A SPECIFICITY FIGHT IT WAS WRITTEN TO WIN.**
`.atlas[data-live] .atcorner:not([data-on]) .atcard` is (0,5,0) and the
phone block's undo was (0,4,0), so for the life of that block the eight
cards a reader scrolls past on a phone were at `opacity: 0` — present,
placed, sized and unseeable. **Found by the dead-rule scan**, which reported
the `opacity` declaration as changing nothing. Fourth specificity collision
in this stylesheet to render as *the thing is simply not there*.

**A TRANSITIONED PROPERTY CANNOT ANSWER THE DEAD-RULE SCAN'S QUESTION.**
`getComputedStyle` returns the INTERPOLATED value while a transition is in
flight, and removing the declaration behind it does not change that value
in the same frame — so a rule that decides everything reads as a rule that
changes nothing. Measured on this band: `.atstage[data-at] .atname
{opacity}` read **0.344667 and then 0.665944 on two runs of the same
build**, where a single clean read of the same element returns exactly 0.34
and names that rule as the only one matching it. **Two live rules reported
dead, with values that differed between runs** — the jitter this check
already refuses in its own count, arriving in its verdicts. The scan
inserts `transition: none` into the sheet it walks before it measures and
deletes it after; proved by re-running the same removal on a resting page,
where all three rules change every sampled element.

**AND THE OPENING STATE MUST NOT ANIMATE.** `mark()` runs the moment the
script does, so gating the transitions on `[data-live]` meant eight cards
faded 1 → 0 and the continent slid to its first pan as the page arrived.
`[data-ready]` is set two frames later — one is not enough, because the
browser coalesces the style `mark()` wrote with the arrival of the
transition rules and animates it anyway.

**A LINE COUNT THAT INCLUDES COMMENTS MEASURES THE HOUSE STYLE.** The
enhancement boundary — *a script that neither fetches nor stores and grows
past a hundred lines is doing something that needs declaring* — counted raw
lines, and this repository's style rule requires long comments naming the
failure behind each change. `atlas.js` crossed 100 on a paragraph recording
that eight cards at zero alpha are still in the tab order, and **a paragraph
cannot turn a script into an application**. It counts `bare_js` now, which
is the same implementation the planner's flag scan uses, and prints both
figures. Proved red at 148 lines of code and green at 26.

**THE WHOLE CONTINENT WAS MOVING AND THE THING BEING READ WAS A CORNER.** The
pan was a correct repair to a measured fault — the panel's wash starts at
x=760 of a plate running 409 to 1296 and the card's own words sit over
Ukraine's centre, so four of the nine corners lit ground a reader could not
see — and it answered it by sliding Europe under the headline every time a
step was crossed. **What the reader is being shown is a corner, so the corner
is what may move**: the lit one lifts out of the continent and everything else
holds still, which is the exploded-atlas move and the one thing on this band
that a picture of Europe can do and a list of countries cannot.

**DIRECTION DERIVED, DISTANCE CONSTANT, EIGHT NAMES AUTHORED.** `data-lift` is
one of eight compass points the build works out from the drawn geometry — the
unit vector from the mean of every liftable country to the mean of that
corner's own — and the stylesheet holds eight rules turning a name into a pair
of components. Eight names are a vocabulary and may be authored; which corner
takes which is a measurement and may not, which is the rule the pan was
already written under. One distance for all nine, because a lift that varied
with the corner would be nine numbers again. **And the names travel with their
own ground**: `.atdoor` carries the same attribute, because a country name
here is placed ON the country it names and a shape that moves while its name
stays put is the defect nine country portraits were repaired for.

**SVG HAS NO `z-index`, SO PAINT ORDER IS THE ONLY WAY TO PUT A LIFTED CORNER
ABOVE WHAT IT MOVES ONTO — probed rather than assumed.** Two overlapping
rects in Chromium, the earlier one given `z-index: 5` and then
`z-index: 5; position: relative`: the later rect wins all three times.
Document order is the whole of it. So the fifty countries are grouped by
corner and **the groups are emitted most-peripheral-first**, because a corner
lifts OUTWARD and everything it can slide onto is further out than it is —
which makes the order a construction rather than a lookup table, and it is
the two cases a document order in macro order gets wrong that prove it: the
Baltic states move north onto Russia, and central Europe moves west onto
France.

**AND THE MIDDLE OF EUROPE HAS THE LEAST DEFINED DIRECTION OF THE NINE.**
`alpine-central` measures 35 units from the mean against 324 for the Caucasus,
so its lean is small and the vector it resolves to is the least meaningful
one on the drawing. It still lifts, because a band that does nothing on one
of its nine steps is a promise kept eight times; what makes that safe is the
paint order, and the fact is recorded rather than tuned away.

**AND THE REORDER IS NOT FREE, WHICH IS WHY IT WAS MEASURED.** Two adjacent
countries each stroke their own ring, so on a shared frontier the later one
wins — and the reorder changes which that is wherever the two sit in
different corners. The plate was shot at 1280 and 390 with every transition
and every lift frozen, before and after: **2,659 differing pixels of
1,153,280, 0.23%, worst delta 89 of 255**, and the diff map is a set of
hairlines along exactly those frontiers — the Scandinavian borders, the
Alpine ones, the Balkan ones, one in the Caucasus. The first draft of that
comment said *byte-identical*, which is what the argument predicted and not
what the instrument said.

**AND THE CUE HAD TO MOVE WITH THE MECHANISM.** `.atcue` said *Scroll to move
through the continent*, which was written for the pan and became false in the
commit that removed it — *removing a claim leaves surfaces pointing at it*,
and this one was the surface whose whole job is to say what the scroll does.
`EDGE_MARGIN` and `WIDE_VIEW` are renamed from `PAN_MARGIN` and `PAN_VIEW`
for the same reason: the frame is still wider than the window, because
`landmass` clips to the view it is given and a margin generated over the
narrow frame comes out EMPTY, but nothing pans and a constant that says so is
a comment claiming evidence.

**THE LIFTED CORNER LEFT A HOLE AND THE BAND PAINTED ITS WATER.** The lift
was measured at the pixel and the one thing nobody looked at is what is
UNDERNEATH: a corner that moves eighteen units off its own ground exposes the
plate's ground, which is `--map-water`, because *the band's paper IS the map's
water* is the repair that made this drawing a room rather than an object. So
the Alpine step opened a channel from the Baltic to the Adriatic and the
Mediterranean step cut Iberia off the continent — **a false geographic
statement, on the one drawing whose whole argument is that geography IS the
design**, and it is a claim about the ground rather than a rendering artefact,
which is worse. Every count was green: nothing here measures whether a drawing
still says something true. Rendering the plate at 2x is what found it.

**A SOCKET, NOT A HOLE: each corner's own shape, left where it was, in the
land's own tone, revealed only where the group has moved off it.** It costs
nine `<use>` elements rather than a second copy of 26 KB of country rings, and
three things about it are the parts that had to be got right:

- **It clones the INNER group.** `<use href="#atgi-<corner>"/>` points at a
  `<g>` inside `.atg`, and `.atg` is where the transform lives — because *a
  clone takes whatever matches the ORIGINAL in its own position*, cloning the
  transformed group would have moved the socket with the corner, which is the
  hole again with extra bytes.
- **It is painted by INHERITANCE.** The lit fill sits on `.atg[data-corner]`
  and a clone inherits from its own parent, so `fill` on `.atsock` gives the
  socket the land's stone while the corner above it is lit — paint it by id
  and the socket lights with the corner it is standing in for.
- **And the wrapper had to be renamed.** Moving fill and stroke off
  `.lyr-land path` onto the LAYER so the clone could inherit them silently
  changed the frontier ink: `.instrmap .countries path` matches the path
  directly, and inheritance can never beat a rule that matches. Measured at
  `rgb(61,68,65)` where `--map-border` is `rgb(104,113,110)`. The register's
  wrapper is `.atland`, so the instrument skin no longer reaches it.

**AND THE NOTE ON THAT RENAME CLAIMED A LOSS THE COUNT DOES NOT SUPPORT.** Its
first draft said the rename *would have silently shrunk `c_land_credit`'s
reach*, because that check triggered on `class="countries"` — so the trigger
was widened to `lyr-land`, the declared layer. Measured afterwards rather than
before: **the old trigger and the new examine the same set, and there is not
one page that only the new one reaches.** The homepage's `class="countries"`
is the HERO's drawing, at line 59, and never the register's, so nothing was
ever at risk. The widening stays — a wrapper's class is a name somebody
renames and `lyr-land` is asserted from both ends by `cartography.ORDER`, so a
trigger on what the page DRAWS cannot be lost to a rename — and it is recorded
as a **guard** rather than as a repair, proved red through its own path: a
page carrying `lyr-land`, no `countries`, no `context` and no credit fails and
is named. *A comment claiming evidence is read as evidence*, and this one was
mine, in the commit that quotes that rule twice.

**THE OTHER HALF OF PROPOSAL 2 IS REFUSED AND THE CARD IS WHY.** *One
territory, one outer ink stroke* would dissolve the internal frontiers of the
lit corner — and the card beside it says **9 COUNTRIES** and lists nine links.
Those frontiers are the doors that count says are there, so merging them would
make the drawing disagree with its own caption. A corner is a grouping, not a
country.

**AND THE INSTRUMENT WRITTEN TO PROVE IT COUNTED MOVING TYPE AS OPENING SEA,
IN TWO DIFFERENT COSTUMES.** Shoot the plate per corner with the lift frozen
and live, count pixels that were land and became water: it reported **872 on
the Adriatic & Balkans** and the socket looked right at 2x, which is the
*eye finds a defect and does not confirm one* problem from the other end.

| | |
|---|---|
| `blue > red + 4` | true of water `#DDE8E7` (221/231) and **also of pine `#0F433E` (15/62)** and of the frontier ink `#68716E` (104/110). 833 of those 872 were the words ROMANIA and BULGARIA arriving at their new position — the names travelling with their ground, working exactly as designed |
| adding *pale*, `red > 190` | left **160 on the Mediterranean**, all of them on Portugal's Atlantic coast, under `.atstats`: the lead column's wash lightens the moved coastline's INK back over 190 while it stays blue-dominant, 199/204. **Washed WATER reads as land by the same arithmetic**, so no classifier can be trusted under that wash — the furniture comes off in both shots instead |
| hiding the furniture | left **57 on the Caucasus**, scattered along the word AZERBAIJAN: anti-aliased glyph edges at a pine fraction between .232 and .249, the narrow band where a blend of pine and the lit stone satisfies both tests. The names come off too, because the question is about the GEOGRAPHY |

**A HOLE IN A SOCKET IS AN AREA AND ANTI-ALIASING IS NOT, SO THE COUNT ALONE
COULD NEVER HAVE SETTLED IT.** The instrument reports the largest CONNECTED
RUN beside the count. With the socket: 0 or 1 on eight corners, **17 on the
Caucasus with a largest run of 2**, which is single ink-edge pixels on
frontiers that have moved eighteen units — a drawing being drawn. With
`.atsock` removed: **9,800 pixels and a 2,896-pixel run** on the Mediterranean.
Proved red, and the diff map is what diagnosed all three of the false
readings — *a failure message with no measurement in it cannot be diagnosed*,
and a measurement with no PICTURE beside it cannot be interpreted.

**AND THE SCREENSHOT CAME BACK UNSTYLED BECAUSE A BUILD WAS RUNNING UNDER
IT.** `site/` is deleted and rewritten on every build and the stylesheet's
filename is its content hash, so a page shot mid-rebuild 404s its own
stylesheet and renders as a wall of blue links. That is the ENOENT the browser
suite already died on twice, arriving in a screenshot rather than in a gate,
where it does not crash — **it produces an image that looks like a design
regression.** Nothing may read `site/` while anything is writing it.

**THE NEXT FOUR THINGS THIS SESSION PROPOSED WERE REFUSED BY ONE PARAGRAPH
NOBODY HAD READ.** Rivers and lakes on the register, relief inside the lit
corner, the shore band, sea names, and a photograph clipped into the lit
corner's lead country — five upgrades, and `atlas_register`'s own comment
refuses every one of them in a sentence written when the band was built:
*Plate 01 is the continent as a PICTURE … this one is the continent as a
REGISTER: no water, no relief, no rivers, no lakes, no photograph and no
dusk.* Measured on the shipped page rather than taken on trust, and the
premise holds exactly — plate 01 carries `lyr-terrain`, `lyr-rivers`, five
sea names and **six photographs clipped into countries**, and plate 05
carries `beyond`, `land` and `labels` and nothing else. **A recorded
refusal is evidence**, and this is the second time one has stopped a
good-looking change. `weight.home_kb` refuses it a second way on its own:
the page sits at 181 against a ceiling of 181.

**A PLATE MARK IS THE BAND'S KICKER, SO A BAND THAT CARRIES ITS OWN KICKER
SAYS ITS NAME TWICE.** `actmark` is *the number is the position and the name
is the caption*, and five of the ninety-eight plates on this site printed
that caption again inside themselves, about a hundred pixels below it. The
homepage's atlas register had `The atlas` over a hand-written `The Atlas`;
/events took the phrase to **four occurrences in one `<main>`**. That is the
two-numbering-systems finding in the NAME rather than in the number — each
system internally correct, which is why nothing counted it.

**WHICH OF THE TWO MOVES IS DECIDED BY THE PRIMITIVE RATHER THAN BY TASTE.**
`ed_opening`'s eyebrow and a `pagehead`'s kicker are REQUIRED and are that
head's own label, so on /events, /map, /interests and /my-europe the MARK
moved; the register's eyebrow was a hand-written `<p>` inside a composition,
so there the eyebrow went and the mark stayed. **And the hand sweep that
found this found three fifths of it** — it read eight index pages and the
FIRST kicker in each, where `c_plate_name_once` reads every page and every
`<h1>`–`<span>` and found /map, /interests and /my-europe as well. An
instrument narrower than the check it motivates is the same fault as an
instrument that reads its own documentation. The test is an element whose
WHOLE text is the name and never a substring, because a band may discuss its
own subject in prose. Proved red on the state that shipped.

**AND `density.js` REPORTED A 1,600-PIXEL HOLE THAT DOES NOT EXIST, ON THE
BAND THIS SESSION HAD JUST REBUILT.** Its own comment records that *a fixed
box's rect is viewport-relative* and walks the chain to the clipping
ancestor for it — and **a sticky box is the same fault one property over**.
The register is a 900px sticky stage inside a 3,240px track of scroll steps
whose eight resting cards are at `opacity: 0`, so the walk filed everything
in the first 900 pixels and read the remaining 1,600 as a run at 0% covered.
The homepage measured **34%** where the honest figure is **19%**, and it
nearly sent its own author to fix a composition that is right — which is the
exact cost that comment names.

**THE ONE EXCEPTION IS MEASURED RATHER THAN NAMED.** What a sticky element
paints is its CONTAINING BLOCK's range, because that is the scroll distance
it stays put over — and the masthead is sticky too, with the document as its
containing block, so attributing it would cover every slice of every page at
full width and the instrument would report nothing anywhere. A sticky
element whose range is the whole document is chrome: it is on every screen
of the page and therefore says nothing about any part of it. Verified from
the other end, because a guard that silences an instrument looks exactly
like a guard that fixes one — /404, /discover, /experiences and /plan still
read 34, 31, 28 and 28.


**THE PAGE'S OWN TYPE STOOD OVER THE REGISTER'S DRAWING AND THE DRAWING HAD
NEVER HEARD OF IT.** `place_label_box` tests every label against the frame,
against its own country's ground and against every box already `taken` — and
`taken` held only what that drawing placed itself. The headline and the
region card are set ON the continent, in the page's own grid. Measured at
1280, ICELAND ran **109 pixels** through *One continent. Fifty doors.* and
SPAIN 43 through the figures; at 1920 six names collided; at 2560 UNITED
KINGDOM ran **256 pixels** through the headline. Nothing called it a contrast
fault because the column's wash DIMS a name rather than deleting it, so what
a reader got was a place name arriving faintly through a 76px serif, which is
worse than either.

**THE RESERVE IS A UNION OVER VIEWPORTS, AND THE UNION OF THE WHOLE COLUMN IS
REFUSED ON THE NUMBERS.** The drawing is `slice` on a 1460x800 frame inside a
container whose aspect runs 1.1 to 5.4, so the scale between the page's
pixels and the projection's units differs on every screen and the same
headline lands in a different part of Europe on each — `.mega` measures
[48, 67, 345, 326] at 1280x900 and [232, 186, 422, 353] at 2560x900, in the
drawing's own units. A reserve fitted to one viewport is a fact about that
viewport. 385 samples, and the extremes are ordinary screens: a 1152x640
laptop sets the headline's depth, a 1024x1440 portrait monitor its width, a
3440x1080 ultrawide the card's left edge. Adding the intro, the action and
the figures to the reserve takes **eleven of the seventeen names**, among them
UNITED KINGDOM, FRANCE, SPAIN, RUSSIA and TÜRKIYE — the exact list this file
already records as the wrong answer. What is reserved is the headline and the
card. 17 names to 11, and every collision gone at every width the two-column
composition applies at.

**AND IT IS THE HULL OF TWO READINGS, BECAUSE THIS HEADLINE FILLS ITS OWN
MEASURE.** An h1's box is wider than its glyphs — a contrast sweep here once
read 2.15:1 against a real 9.58 for that reason — so the sweep was run again
over the headline's own line boxes expecting the reserve to shrink. It did
not: the glyph union is **narrower by 18 units and deeper by 6**, and neither
contains the other. 76px display type on three short lines is the one case
where the trap does not apply.

**AND THE SIX FIGURES CAME OUT OF THE COLUMN, BECAUSE THE PAGE SAYS THEM
THREE TIMES.** A derived `<dl>` of countries, regions, destinations, places,
experiences and journeys — correct, and an extent that is not this band's
own. Counted on the built homepage, every one of them is stated twice more:
the opening prints four and the footer prints all six. A reader met the
site's extent three times before meeting a corner of Europe, while the number
the band IS about was the closing line a thousand pixels below — `.atsum` has
printed *50 countries · 9 corners · 1 continent* since the band was built,
which is the chapter transition the brief asks for and it was already there.
`c_home_extent_kept` asserts each removed figure is still on the page beside
its own word, because *when a band goes, check what it was the ONLY home
for*. The vertical rail went with them: `Europe through the door`,
`aria-hidden`, repeating the headline's own metaphor in smaller type.

**FIFTY DOORS WERE DRAWN, MEASURED AND REFUSED; THE DOOR IS ON WHAT IS
OPEN.** The band's sentence is *One continent. Fifty doors.* and it drew
fifty country shapes with nothing on them that is a door — the /themes fault
word for word. Fifty arches were prototyped in Chromium at 6, 9, 13 and 16
units and photographed at 1x and 2x BEFORE any build code was written: **at
the size that fits the smallest country it is a texture, and at the size that
resolves into an arch it does not fit.** Luxembourg's largest ring spans 8
units and a mark needs about 13 to read, so forty-four at one weight draw a
second frontier network over the first, which is *a signature applied to
everything is wallpaper* exactly. What ships is 29 of 44 — one per country
that can hold one on its own ground — revealed only on the corner being read:
never more than nine on screen, and *fifty doors* demonstrated across the
nine steps rather than asserted all at once. A STATE rather than a selection,
because every country carries one.

**AND THE RISE IS STATED, BECAUSE THE DEFAULT IS FOR A MAP.** `arch_path`
defaults to `min(h * .34, w * .5)` — the confident flat span a mason strikes
over an opening cut across a 900x320 drawing — and at glyph size it rendered
a **rounded rectangle**. The head is struck at half the span, which is the
semicircle the wordmark's own door has. Three more things had to be got right
and each is a fault already on this record: the curve is `render.arch_path`
translated rather than a fourth drawing of the one shape the aperture is cut
from in three renderers; the mark is placed by five samples rather than by
walking out from the bounding-box centre to the first point inside the fill,
which put Denmark's in the Kattegat (*a bounding box is not a country*, and a
point inside the fill is not a box inside it); and it goes inside `.atg` and
OUTSIDE `#atgi-`, because a `<use>` takes whatever matches the ORIGINAL in
its own position and `.atmark` is a bare class selector — a mark inside the
clone draws a second set of pine doors in the hole the corner has just lifted
out of.

**AND `boxes` HANDED BACK WHAT IT WAS GIVEN, WHICH COST THE BRITISH ISLES
BOTH THEIR DOORS.** The type zones are a union over viewports, right for a
name with nine anchors and far too blunt for a 20-unit glyph, so a mark
avoids them where it can and takes the ground under them where that is all
there is — `NameGround`'s own shape, zero crossings first and two only if
nothing fits. The soft rung could never fire: `name_countries` starts `taken`
as a copy of `reserved`, so extending the caller's list with the whole of it
told the register its own reserve was a NAME. Both British countries sit
inside the headline's union, so the one step of the nine whose corner is two
islands said nothing, silently, on a rung written to stop exactly that.
`boxes` is what the pass PLACED.

**AND TWO LABEL LEVELS ARE A SWITCH RATHER THAN A READING.** The corner being
read was at full ink and everything else at a third, so the continent flicked
on and off nine times and nothing said where the corner SAT. A middle rung
needs to know which corners are NEXT to the one being read and this atlas
holds no adjacency — a macro region is a set of countries, and a list of
neighbours would be an authored measurement. It is derived from the same
means the lift is: the two corners whose own middles are nearest this one's,
nine pairs out of the drawn geometry, and it reads as geography — the Nordics
beside the Baltic and the British Isles, the Caucasus beside Eastern Europe
and the Balkans. **Two rather than three**, because at three the rung covers
more than half the continent and stops being a middle. `data-near` is a
space-separated list and `~=` reads it, so the stylesheet gets nine selectors
rather than eighty-one and `atlas.js` copies one attribute across, computing
no distance of its own.


**THE MAP IS THE RIGHT TWO THIRDS AND THE FRAME IS EUROPE RATHER THAN THE
DATASET, WHICH ARE THE OWNER'S TWO INSTRUCTIONS AND THEY PAY FOR EACH
OTHER.** *The map should take only 2/3 and extend to the right, not more than
that*, and *Russia is not supposed to be in Europe, but it covers a bigger
place than Europe — the focus is Europe.* **The literal crop is refused,
measured**: keeping `slice` and narrowing the box to two thirds crops
whichever axis is long, so at 1280 the box becomes 853x900 against a frame of
1460x800 and the drawing shows 760 of its 1460 units — Iceland, western
Iberia and the whole Caucasus leave the picture. `meet` aligned to the top
shows the whole drawing instead, on a frame `atlas_frame()` fits to the
countries this atlas writes about with **the CUT countries left out of the
fit**: this atlas holds a fragment of Russia, so its northern reach is a fact
about where `data/geo/` stops rather than about Europe, and a frame sized
around it makes the fragment the biggest thing in a picture of the other
forty-nine. 1460x800 becomes 840.8x771 and five kilobytes of ground beyond
come off with it.

**AND THE RELIEF WAS REFUSED TWICE HERE AND THE OWNER OVERRULED IT.**
`atlas_register`'s own paragraph says this band is the continent as a
REGISTER — *no water, no relief, no rivers, no lakes, no photograph and no
dusk* — and that refusal has stopped two good-looking changes, which is why
*a recorded refusal is evidence* is in this file twice. **A band claims only
HEIGHT, which is the one thing the elevation model measures**, so nothing is
invented; that is exactly what separates it from the water, the rivers and
the photograph the same paragraph refuses, and those stay refused. The
settings were **rendered and looked at rather than picked**: four candidates
injected into the real page and photographed at 1440 — three bands at 3.5
units (15.7 KB), the same at 4.5 (10.8), two at 4.5 (4.4), three at 6.0
(6.6) — and the two cheap ones are a layer that ships and cannot be seen,
which is the measurement that removed the terrain's second strength. 13.0 KB
shipped, `weight.home_kb` 184 to 192, itemised in `tools/invariants.py`.

**EVERY PICTURE TAKEN OF THIS BAND WAS TAKEN FROM THE MIDDLE OF THE
SEQUENCE, AND BOTH ENDS WERE BROKEN.** The stage is `100svh` sticky inside
`.atlas`, so it is pinned while the section spans the viewport and for
nothing either side of that; the nine steps are `40svh` each and started at
the section's own top, and `atlas.js` marks a step when its middle crosses
the middle of the viewport — **30svh before the stage pins** for step one
and 40svh after it unpins for step nine. Measured at 1280, 1440 and 1920: on
the FIRST corner the card rendered at y=420 and the headline at 345-636, so
the panel sat **217 pixels inside the headline's own box**; on the LAST the
headline had left the screen, top at -195, with 277 pixels of it behind the
masthead. The inset is arithmetic — a step's middle must fall inside the
pinned range, which needs at least 30svh at each end — so `.atread` takes
`padding-block: 36svh`, that floor with six to spare. It costs 72svh of
scroll and no pixel of page: the track is invisible and what it moves across
is the stage. The headline now holds at 75-367 on every corner at every
width. **And the inset had to be undone where its reason expires**: the
narrow block resets `.atread`'s MARGIN and not its padding, so 72svh of empty
page would have shipped on every phone — below 62rem the stage is not sticky,
the cards are a column and the steps are `min-height: 0`, which is *a repair
applied where its reason has expired*, made in the commit that added the
padding.

**LAND THAT ENDS ON A RULED LINE WITH NO FRAME ROUND IT IS A RENDERING
FAULT.** This drawing has no visible edge — the band paints the map's own
water, which is the repair that made it a room rather than an object — so
`beyondmass(pad=0.0)`, which clips the ground exactly to the frame, is right
on three edges and wrong on the fourth: the top sits at the stage's own top
with the masthead on it, the left and right bleed past the viewport, and the
SOUTH is in the middle of the stage. Measured at 1440 on the Mediterranean
step, Tunisia and Anatolia ended as two straight-edged wedges on a horizontal
730 pixels down with the band's water under them — **/plan's context-land
slab, arrived at from below**. `ATLAS_FRAME_PAD_S` is 0.20 against 0.05 on
the other three sides, which puts the southernmost named country 16% of the
frame above the bottom, and `ATLAS_GROUND_FADE` is 0.10, smoothstep in five
stops, handing what is left of the ground to the water. **Masked rather than
clipped, and on the ground alone** — it is the only layer that reaches that
edge, and *a masked group hit-tests as ONE region*, which is what the hero
lost fifty country links to. It also shortens the dead band under the drawing
from 235 pixels to 144 at 1280x900 without the continent losing a unit.

**AND `ATLAS_TYPE_ZONES` IS GONE, BECAUSE THE COMPOSITION REPLACED IT.** That
reserve was a union over 385 samples of where the headline and the card land
in the projection's own units, seeded into the label placer's `taken` so a
country name could not be set under either; it cost six of the seventeen
names and it was the right trade while the type stood on the drawing. Re-run
on the two-column composition, the same 385 samples report the headline's
union ending at **x=140.7** and the card's at **x=174.5** against a frame
that begins at **x=201** — neither touches the drawing at any width, height
or scroll position the stage is sticky at. **A reserve over ground the frame
does not contain is a cost with no subject**: 11 names to **17**, and the six
it had been buying nothing with are RUSSIA, GERMANY, UNITED KINGDOM, ICELAND,
IRELAND and LATVIA, which is the list this file already records as the wrong
answer. The doors go 29 to 26 in the same move and every corner keeps at
least one. **The two-rung mark placer went with it** — a soft rung whose list
is always empty can never fire, and *a rung nothing reaches is dead code that
looks like a decision*. And the guarantee is STRUCTURAL now rather than
measured: `.atlead` is `min(29%, 25rem)` and `.atread` is `min(30%, 23rem)`
against a `.atwin` that starts at 34%, so the column cannot reach the drawing
at any width by construction, where a union is a fact about a sample.
`browser-checks.js` asserts that against the page's own `viewBox` rather than
against a declared number — **proved red by serving the stylesheet with both
columns widened to 60%: 30 failures over eighteen samples, against 0 of 18 as
shipped.**

**AND A STALE PARAGRAPH IN THE STYLESHEET ARGUED FOR THE OPPOSITE OF THE RULE
UNDER IT.** *THE BOX TAKES THE FRAME'S OWN PROPORTION INSTEAD* was written
for a version that set an `aspect-ratio` on `.atwin` and was reversed in the
same commit, one paragraph down, without the argument coming with it. *A
comment claiming evidence is read as evidence*, and this one contradicted the
declaration eight lines below it. Two more from the same run, each caught by
a guard this file argues for: an eighth `line-height` — 1.05, four
hundredths from the `1` the file already had, on a heading that sets on two
lines — caught by `css.line_heights` in the run that introduced it; and the
weight ceiling, which is the only instrument here that measures bytes.


**A BAND WHOSE EMPTINESS IS ALL ON ONE SIDE IS THE ONE SHAPE NEITHER
INSTRUMENT CAN SEE.** `voids.js` finds a band with NOTHING painted in it and
`density.js` measures the painted UNION as a share of the page's own width —
so a 566px headline column over 1,280 is 44% covered, clears density's fifth,
and is not empty. Measured on the homepage: the year plate left **791 × 352
pixels of nothing** beside *Every month opens a different Europe.* (62% of
the width at 1280 and still 41% at 1920) and the reading plate left 610 × 194
beside a head that had no lede at all. Three of the eight plates have nothing
to the right of the head and two of those are right — one sets its type over
a full-bleed photograph and one is a deliberately centred close.

**AND THE RULE FOR IT EXISTED AND NAMED A FAMILY THAT DOES NOT EXIST.**
`.sheet-pairs > .sheettext, .sheet-about > .sheettext, .sheet-tales >
.galwrap > .sheettext` carries its own reason — *one column … leaves the
right two-thirds of a full-width band empty* — and that is *a rule stated
once and applied to one of its call sites* written as a selector list. It
failed in both directions at once: the homepage's two plates were never
added, and **`.sheet-tales` matched on /experiences and never on /journeys**,
whose plate is `sheet-jtales` with its head a direct child of the section
rather than of a `.galwrap`. So /journeys' *Between the destinations.* head
was one column for the life of that band — the lede moved from x=64 under the
title to x=800 beside it, the head fell 333 → 191px and the plate 1,123 →
982. **The dead-rule scan could not have caught it**: it removes each
declaration and asks whether anything moves, which is a question about a rule
that MATCHES elements, and this selector matched none. The rule is a property
of the HEAD now — `.sheettext.headwide`, five call sites stating it where
three were named — and the nesting stops mattering. Proved rather than
argued: /experiences shot full-page at 1280 and 390 before and after,
byte-identical at both, with a **run-to-run control first** (4 of 4
identical), because *the count jitters* is already on this record.

**AND THE READING PLATE NEVER SAID HOW BIG ITS SET IS.** Every other plate
states its extent — eight more corners, 31,213 km over seventeen routes,
fifty countries and nine corners, 150 fixtures and forty-seven countries —
and this one printed a headline and nine stories and no number, which is *an
index exists to say how big a set is* on the one band that also had no lede
to put beside its title. **Both branches are written**, because *one to each
desk* is a fact about today: nine essays filed to nine desks, one each, and a
tenth on an existing desk makes that sentence false, so the count decides
which sentence prints.

**A GATE KILLED MID-RUN TAKES THE LIBRARY WITH IT, AND EVERYTHING IT TOUCHES
IS TRACKED FOR EXACTLY THIS REASON.** `photo-tests.py` was killed by a worker
restart while the session's disk allowance was exhausted, so `cleanup()`
never ran: **12,390 licensed derivatives deleted from `assets/img`, 818
originals renamed aside, and `data/images.json` left holding the suite's stub
register** — 123,348 lines gone, and every count with them. `git checkout --
data/images.json assets/img photographs` restores all three and `site/` is
regenerated; the suite's two backup directories were verified file-by-file
against the restored library (12,390 and 826, none missing) before being
deleted, and the 120 leftover derivatives were confirmed as stubs by their
hashes appearing **zero** times in the restored register rather than by their
names. **A restore is verified by the gate rather than by the absence of
errors** — `checks.py` re-run on the restored tree reports the same 343,524
things examined as before the crash, which is the evidence the library is
whole. And the sizes are why the gate could not simply be re-run: `site/` is
1.7 GB, `assets/img` 2.4, `photographs` 3.6 and `.git` 14, against an
allowance that had **4.1 MB** left. Deleting the regenerable build artifact
first is what made the restore possible at all.


**A REFUSAL'S TRIGGER FIRED AND NOBODY PULLED IT, SO THE LARGEST SLOT ON THE
SITE HAD AN UNMEASURED CROP ON EVERY DESTINATION.** `destination-hero` declared its
container `unmeasurable` with the reason written out — above 62rem
`.placeband-art` is *"exactly as tall as the MAP BESIDE IT"* — and a trigger
saying **give it a declared aspect at every width in the same commit as the
first destination photograph**. All 319 destinations carry one now, and the
reason had expired with the layout: the parent is `.ed-arrival-media`,
`display: block`, the photograph and the map are two full-width rows, and
`grep -rho 'class="[^"]*placeband[^"]*"' site --include=index.html | sort -u`
returns `placeband-art` and `placeband-map` and **never `placeband`** — four
rules, including the 5fr/7fr grid the flag cited, described a wrapper the site
emits nowhere. With that grid gone nothing gave the box a ratio and
`picture { height: 100% }` against an auto-height parent resolves to `auto`,
so **the container took the PHOTOGRAPH'S OWN shape**: 1.500–1.778 on a 3:2
source, flat 1.778 on a 16:9 one, 1.778–**2.126** on the single 2.125 source.
The opening band's height was decided by whatever was licensed — 27 of 319
pages opened on a shape the other 292 did not. `aspect-ratio: 3/2` at every
width, chosen because the slot's note asks for the vertical relationship and
both candidates give the same 62.5% frame, so the arithmetic does not choose
and the note does. Safe area 44.1% → 62.5%. **And a first sample of twelve
destinations read 1.500–1.778 and was wrong** because all twelve were 3:2: *a
sample that is not spread is a fact about its own first entries.*

**AND THE MEASUREMENT END HAD NEVER LOOKED AT A TEMPLATED SLOT.**
`c_photo_safe_area` merges `slots` into `purposes` with its reason on it — *a
slot's crop rule is the same claim as a purpose's, and a template that escaped
this check would be a whole templated family of unchecked crop* — while
`browser-checks.js`,
whose comment says the two exist so *"neither can drift without the other
noticing"*, read `.purposes` alone. **Seventeen entries of arithmetic against
seven of measurement**, and the ten never looked at are every templated family
on the site. Wired in, ten of twelve groups held and two were real:
`.card-art.frame` is **2.333** on all 120 samples against a declared 1.778 —
read off `.card-art`, whose own rule is 16/9, missing the `.frame` modifier
that overrides it — and `.headshot` measures **0.692–1.333 on both** families
that use it, so the recorded finding that one class had two real boxes has
stopped being true and the remedy was one correct number rather than two
selectors. The literal string `"declared"` is gone from all ten `min_at`s.

**AND 129 OF THE 319 DESTINATIONS BROKE THEIR OWN NAME MID-WORD.** Found by
rendering Český Krumlov to check the crop and reading `Český / Krumlo / v`.
**The first instrument reported zero and was measuring the symptom**: a Range
over a word that is already wrapped returns the union of its line fragments,
which is narrower than the word. Measured unbroken, the h1's content box is
177px at 834, 211 at 1280 and 223 from 1520 up — **it never passes 239 at any
width** — against "Belovezhskaya" at 247, 379 and 450, so the overrun gets
worse as the window grows (1.40× → 2.02×). Three causes: the track is `.55fr`
of 1.45/.55; `padding: clamp(2.25rem, 5vw, 5rem)` was written for the BLOCK
axis and applied to all four sides, so a padding sized to the viewport sat
inside a column that is a quarter of the viewport (128px of 339); and
`--ed-display-2` keeps growing to 76px while the band caps at 1392 — **a
viewport-scaled font inside a max-width column**. Solved for the worst name
that CANNOT break, because the four longer all carry a hyphen and may break
there. Media:copy 2.64:1 → 1.93:1, which is the feature scale this file
already argues for rather than a new proportion. **129 → 0 on all 319 at six
widths from 390 to 2560.**

**AND THREE CEILINGS WERE TYPED TWICE, EVERY ONE LOOSER THAN THE REGISTER.**
The h1's clamp is a 25th font-size value and the invariant register refused
it, which is the register working. Moving it found that `checks.py` types its
own copies: font sizes 24 against the register's 25, breakpoints 10 against 6,
shadows 6 against 3. Nothing got through, because the register is a gate too
and is the tighter of each pair — but the comment directly above that block
ends *"One implementation"*, about the PARSER, which is shared, while the
NUMBER was typed. That is the dispatch cap exactly, three times in one
function, and the answer is the same as the third time it happened: stop
having a second implementation. `checks.py` reads all three from the register,
each proved red by lowering it.


**AND CENTRING THE ARRIVAL COPY WAS THE SAME EXPIRED ANCHOR ONE PROPERTY
OVER.** `.ed-arrival-copy` carried `justify-content: flex-end`, written when
the media column was the photograph alone and the band was its own 620px. The
map is inside that column now, so the band is 939px at 1280 and the bottom the
copy was pinned to is the bottom of the MAP — which put Innsbruck's eyebrow at
732 against a map starting at 705, and the browser suite caught it by id in
the run after the photograph's aspect was declared and the column got shorter:
*a reader meets the instrument before they are told what the place is.* It had
been passing by fourteen pixels. Centred, the copy sits against the middle of
the photograph (164–705, middle 434) at 496 and 475 on the two pages the check
reads — **the thing it is actually beside.**


**`aria-hidden` ON A SUBTREE THAT HOLDS FOCUSABLE CONTENT IS A CONFORMANCE
ERROR, AND THE HOMEPAGE HERO SHIPPED 43 OF THEM UNDER AN ARIA-LABEL PROMISING
THEM.** `geo.landmass()` set `aria-hidden="true"` on the countries group
unconditionally — right on every other page that draws one, where the group
is ground and holds nothing to leave through, and wrong on the one page where
the caller passes
`link=` and every country becomes an SVG `<a>`. That svg's own accessible
name reads *"Europe, drawn: every country is a link to its own page"*, so the
label claimed exactly the subtree the markup removes. It is the fourth thing
in the hero's *three things had to be undone before a click could reach one*
family, and it survived all three, because `aria-hidden` takes nothing away
from a mouse, a keyboard, `checkVisibility` or a contrast sweep.

**AND THE BROWSER REFUSED TO CONFIRM IT.** Read out of Chromium's own
accessibility tree, the hero svg reports 54 children and all ten sampled
country links come back as `link` with the country's name on them: Chromium
does not propagate `aria-hidden` over focusable descendants — it recovers and
logs. So the claim is not *43 links are hidden from assistive technology*; it
is that the markup is invalid and its behaviour is the recovery strategy of
one engine, where every other engine gets to choose its own. **One browser
recovering is not a design** — the same reasoning that moved the map-layer
assertion onto the computed display after Chromium 131 and 141 disagreed about
an empty box. `anchored` is set where a link is actually emitted, so the
attribute follows what the group HOLDS rather than what the caller asked for.

**AND THE 481 KB OF NAMES IN THOSE HIDDEN GROUPS ARE NOT DEAD, WHICH WAS THE
OTHER READING AND IT IS REFUSED.** 19,913 titled country paths sit inside an
`aria-hidden` group across the whole site — `grep -rl 'aria-hidden="true"' site
--include=index.html` names the set — and *named and hidden, never both* is this
repository's own rule — so the obvious conclusion is that every one of those
names is weight. It is wrong: an SVG `<title>` is the native TOOLTIP, a
rendering feature rather than an accessibility-tree one, so hovering any
country on any drawing here says what it is, and `aria-hidden` does not touch
that. Deleting them would buy 481 KB by removing the only affordance a sighted
reader has on 824 plates that name nothing else.

**AND THREE SUSPICIONS ABOUT THE MAPS WERE MEASURED AND CHANGED NOTHING**,
which is the same number as the commit that recorded them. The country
portraits and macro maps carry no scale bar and should not — *a country is a
shape; a destination is a position*, recorded in `docs/signature-moments.md`
before either was drawn. The 40 `pointsmap` pages with no bar are the
continental frames plus Finnish Lapland and Nord-Norge, every one of them a
latitude span the conic cannot hold inside 2%, which is the tolerance test
doing its job. And the atlas register's names ALREADY come off below 44rem
(`.atplate .lyr-labels { display: none }`), so the 6.5-pixel type the hero's
own rule exists to prevent was never on plate 05.




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
    node tools/monotony.js --check           no page is one component and little else
    python3 tools/ad-tests.py                 the commercial layer: the OFF state,
                                              and a simulated ON in memory
    python3 tools/photo-tests.py              the acquisition pipeline
                                              its batch loop and its fill planner,
                                              against a stub provider
    python3 tools/desk-tests.py               the Media Desk: the sign-in, and what the browser may send
    node tools/hosted-desk-tests.js           the HOSTED desk: signed sessions, signed thumbnails, the dispatch
    node tools/desk-render.js                 the HOSTED desk's screens and its basket, at 1280 and 390

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

**Two more that are deliberately not gates, and answer the two halves of the
mandate's first two findings.** `node tools/opening.js` measures how much of
the first screen is a picture, per family, at 390 and (`--wide`) at 1280;
`node tools/composition.js` measures the band sequence UNDER the head, the
h1's size and position, and how much of its own width each head reaches.
Neither has a threshold and neither can fail, for the same reason: the fault
they exist to find is a page that is DULL, and a number to satisfy is
satisfied by shuffling bands. Both read `tools/lib/families.js`, which is the
one list of rendered families and is enumerated against the built site — a
template missing from it is a family no instrument here can see, which is how
the fund project page shipped at 0% picture for the life of the family.

**And a third, on the same reasoning.** `node tools/voids.js` measures bands
over 90px with nothing painted in them, per family, at 1280 or (`--phone`) at
390. It reports and cannot fail: the fault it looks for is an outlier — a
296px column beside a picture, a standfirst alone in the right half — and the
section rhythm it would otherwise punish is what says two bands are separate.

**And a fourth, which is the other half of that question.** `node
tools/density.js` measures how much of each 50px slice is painted AT ALL, as
a share of the page's own width, and prints every run of 200px or more under
a fifth covered. `voids.js` finds a band with NOTHING in it; this finds a
band with ALMOST nothing, which is what a reader means by "this part of the
page is empty" and what `voids.js` reported as zero on the homepage while 558
pixels of wall sat above the window. Same reason it cannot be a gate: a floor
on coverage is satisfied by widening every measure until the page is a wall
of type. It takes a path (`node tools/density.js /`) or the whole list.

**And one that is deliberately not a gate.** `node tools/contact-sheet.js`
puts one page per family in a single image. `--dark` shoots the dark
colour-scheme preference, `--phone` shoots 390px, `--tablet` shoots 834, and
`--set=N` pages through the whole list twelve at a time (`--more` is
`--set=2`). **834 is the width that finds a two-column layout collapsing a
column just above its own breakpoint** — two heads and the four doors on
/how-it-works were each wrong only between the breakpoints, and invisible at
both the widths everything else is shot at. **The list
is `tools/lib/families.js` and both this and `opening.js` read it**, because
the sheet used to type its own and the two disagreed: it carried
`["macro", "/countries/"]` — the countries INDEX under the macro family's
name — so no macro page had ever been on a contact sheet, and neither had a
story, a theme, `/journeys`, `/interests`, `/europe-in`, `/events`,
`/discover`, `/search`, `/my-europe` or the 404. Its own comment said "every
family is in one field of view" while it covered 23 of 27 and named one of
them wrong. Each of those three found a defect the whole gate suite was green
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
