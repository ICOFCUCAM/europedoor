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
| **"did we actually implement section N?"** | **`docs/section-audit.md`** — generated, never hand-edited. Every spec section asserted against the real build, and CI fails if any of them stops being true |
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

Depth beats breadth. A few hundred destinations written properly beats 40,000
imported, and there is no importer in this repository on purpose.

## Style

Long comments that explain *why*, usually naming the failure that prompted
the change. Keep them. Prefer recording a mistake to quietly deleting the
evidence of it — the note in `assets/css/europedoor.css` about the 47px
overflow is worth more than the two lines of CSS that fixed it.
