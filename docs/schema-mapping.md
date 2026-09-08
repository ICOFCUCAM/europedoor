> **§2 IS CLOSED.** The owner accepted this audit as the built state on
> 2026-09-08, with one consequence recorded here: **the original
> `relationships` table is removed from the target architecture rather than
> implemented.** A derived index is the stronger design and the blueprint
> changed to match the implementation, not the other way round.
>
> | section | status |
> |---|---|
> | §2.1 Geography | built |
> | §2.2 Classifications | built |
> | §2.3–2.13 Core data | built |
> | §2.14 Knowledge graph | built, **derived** |
> | §2.15 Users | refused, with the trigger named |
> | §2.16 Preferences | built, **derived** (Travel DNA) |
> | §2.17 Saved | built, six kinds |
> | §2.18 Geographic performance | measured; no spatial layer justified yet |
> | §2.19 Search | measured, three bugs found and corrected |
> | §2.20 Architecture | mapped layer by layer |
>
> §3 is `docs/api-architecture.md`, written the same way: from the running
> system. Do not reopen §2 to make the original blueprint look like the
> implementation.

# Build Package v1 §2 — the schema, against what is actually running

Every field the Build Package asks for, checked against the live dataset.
Three verdicts, and the third is the one worth reading:

| | |
|---|---|
| **HAVE** | the field exists, under our name or its own |
| **BUILT** | it did not exist before this audit and now does |
| **REFUSED** | it will not exist, and the reason is a promise this product makes |

Nothing here is aspirational. `tools/checks.py` asserts the HAVE and BUILT
rows against the data on every build, and asserts the REFUSED rows are absent
from every file — so the wall cannot be walked through by adding one key to
one JSON file.

## The principle the schema opens with

> *A page is a view of data. The data is the product.*

Already true and enforced. `site/` is deleted and rewritten on every build,
1,072 pages come from `data/`, and a hand-edited page vanishes on the next
build with no failing check. There is no CMS and no page anybody typed.

## §2.1 The hierarchy

    CONTINENT → COUNTRY → REGION → CITY → PLACE          HAVE
    plus EXPERIENCES, JOURNEYS, BUSINESSES,
         EVENTS, STORIES                                 HAVE
    TRANSPORT nodes                                      BUILT  (§2.11)
    TRANSPORT routes                                     REFUSED (§2.11)

Present as a real hierarchy, not a tag: 50 countries → 130 regions → 319
destinations → 255 places, with 197 experiences, 17 journeys, 150 events,
9 stories and 8 provider tiers hanging off it. The URL is the hierarchy —
`/europe/norway/fjord-norway/bergen/place/bryggen` — so the graph is
navigable without a query language.

## §2.2 Countries, regions, cities

| schema field | state | here |
|---|---|---|
| `id` | HAVE | the slug. Stable, human-readable, and already the URL |
| `name`, `slug` | HAVE | |
| `iso2` | HAVE | `code` |
| **`iso3`** | **BUILT** | derived from Natural Earth. 50 of 50 |
| `capital`, `currency`, `timezone` | HAVE | |
| **`latitude`, `longitude`** | **BUILT** | Natural Earth's `LABEL_X/LABEL_Y`, not a centroid — the centroid of Norway is in Sweden |
| **`population`** | **BUILT** | Natural Earth `POP_EST`, with the year printed, because a population with no year quietly becomes wrong |
| `description` | HAVE | `summary`, plus `tagline` |
| `hero_image` | HAVE (empty) | `data/images.json` is the register and the pipeline is enforced; **0 photographs are licensed**. See `docs/images.md` |
| **`status`** | **BUILT** | `published` / `draft`, and a draft is *excluded from the build* rather than published with a badge — a lifecycle column that changes nothing is a column that gets set wrongly and never noticed |
| `created_at`, `updated_at` | REFUSED | see below |
| **region `type`** | **BUILT** | the schema's seven administrative values, plus `editorial`, which is what all 130 of ours are |
| **region `latitude/longitude`** | **BUILT** | derived from the region's own destinations |
| region `geometry` | REFUSED | we hold region membership, not region geometry — `docs/data-licenses/eurostat-gisco-nuts.md` |
| **`city_type`** | **BUILT** | 8 values, **319 of 319**. See the note on the derivation's bias below |
| city `population` | BUILT (partial) | 157 of 319 |
| city `geometry` | HAVE | a destination is a point; `lat`/`lon` is its geometry |

**The derivation was systematically biased, and a check caught it.** Natural
Earth's populated-places dataset is, by construction, a list of *populated
places* — so the derived `city_type` produced **one village in 157**, and the
162 destinations it could not classify were disproportionately the villages,
valleys, parks and sites. A browser check asserting "villages exist" went red,
which is how the bias surfaced.

All 319 are now classified, and the 162 the source could not reach were
**authored** — read one at a time from the summary this atlas had already
written about each. That is legitimate where a population is not: whether
Lofoten is an archipelago or a town is an editorial judgement, and Natural
Earth's answer for it is "not listed".

    city 108 · town 82 · capital 48 · village 30
    site 17 · island 16 · valley 9 · park 9

**Why 157 of 319 population figures is not a coverage failure.** Natural Earth lists the
destinations most people have heard of. The 162 it does not list are Theth,
Xınalıq, Madriu-Perafita-Claror, Mont-Saint-Michel — villages, valleys and
monuments — and they are *the product*. Where there is no source the row is
absent rather than estimated, and `docs/content-report.md` counts it.

**Derived facts are never authored.** `iso3`, coordinates and population live
in `data/geo/facts.json`, generated by `scripts/map/process.py` from the
public-domain Natural Earth files committed under `data/raw/`, each carrying
the dataset that produced it. The validator refuses all of them as authored
keys, for the same reason it refuses an authored `confidence`: a field a
person can type is a field somebody will type wrong, and a wrong population
with no source attached looks exactly like a right one.

**One country has no `iso3`, and that is a fact rather than a gap.** ISO 3166
has assigned Kosovo no alpha-3 code. It carries `XKX` with a note saying it is
user-assigned — the same decision, recorded the same way, as the `xk` alpha-2
this repository already uses as Kosovo's key. `docs/boundary-policy.md`
explains why that is an identifier join and not a recognition claim.

## §2.3 Places

| schema field | state | here |
|---|---|---|
| `id`, `name`, `slug` | HAVE | |
| `city_id`, `region_id`, `country_id` | HAVE | the nesting *is* the foreign key, and it cannot dangle |
| **`place_type`** | **BUILT** | `kind`, widened from 24 to 29 — `palace`, `mosque`, `synagogue`, `lake` and `gallery` were genuinely missing |
| `description` | HAVE | `summary` |
| `short_description` | HAVE | the summary is already one sentence |
| `latitude`, `longitude`, `geometry` | HAVE | |
| **`status`** | **BUILT** | |
| `hero_image` | HAVE (empty) | as above |
| `address` | GAP | we hold none and cannot source them; stated rather than invented |
| **`featured`** | **REFUSED** | |
| **`rating`, `review_count`** | **REFUSED** | |
| **`opening_hours`, `price_level`, `website`, `phone`** | **REFUSED** | |
| `verified` | HAVE, differently | a dated `checked` record with named sources beats a boolean |
| `created_at`, `updated_at` | REFUSED | |

### The three refusals, and why each is a promise rather than a shortfall

**`featured` (and `rank`, `boost`, `sponsored`, `promoted`).** A sponsor pays
a *provider*, and a provider affects *directory surfaces only*. A `featured`
flag on an editorial place is that wall with a door in it. The schema is the
only version of that promise worth making, so the validator refuses the key
and `checks.py` refuses it again at the file level.

**`rating` and `review_count`.** We hold no ratings for anywhere in Europe:
no reviews, no survey, no visitor numbers. `checks.py` already refuses
`aggregateRating` in JSON-LD for exactly this reason, and a number sitting in
the data that the structured data refuses to publish is a number waiting for
somebody to publish it.

**`opening_hours`, `price_level`, `website`, `phone`.** The four fields that
go stale fastest and damage a traveller most when wrong. A closed museum you
were told was open is a ruined day. Every place page says we hold none of them
rather than guessing.

## §2.4 Experiences

The schema's distinction — *the Louvre is a place; exploring Renaissance
masterpieces at the Louvre is an experience* — was already the model here. 255
places and 197 experiences are separate entities.

| schema field | state | here |
|---|---|---|
| `id`, `name`, `slug`, `description` | HAVE | |
| `experience_type` | HAVE | `kind`, 10 values — walk, table, workshop, water, museum, sacred, ride, stage, wild, cellar. Ours describes the *shape* of the thing you do; the schema's 14 describe the mood, which is what our `interests` already carry, so the two vocabularies are kept apart rather than merged |
| **`difficulty`** | **BUILT** | 4 values, optional. **0 of 197 authored** |
| **`seasonality`** | **BUILT** | `season`, optional. **0 of 197 authored** |
| `price_from`, `currency` | REFUSED | `band` is low/moderate/high, which is honest about being a band. A price_from is a number that goes stale and cannot be checked |
| `duration_minutes` | GAP | places have a `duration` in words; experiences do not |
| `latitude`, `longitude` | HAVE, differently | an experience inherits its destination's position. Giving it its own would imply a precision we do not have |
| **`status`** | **BUILT** | |
| `featured` | REFUSED | as above |

## §2.5 The place ↔ experience relationship — **BUILT**

This is the section that says EuropeDoor becomes more powerful than a
conventional travel website, and it was the largest genuine gap in the model:
places and experiences sat side by side under a destination with **nothing
joining them**. A place page could not say what there is to do there; an
experience page could not say where.

There is now an edge, and it is typed, because the distinction that matters is
where you actually stand:

| type | meaning | example |
|---|---|---|
| `at` | it happens there | *Swim in Lake Annecy* → `lake-annecy` |
| `from` | it starts there and ends elsewhere | *Fløyen to Ulriken ridge walk* → `floyen` |
| `about` | it is about the place without being on it | *Stromboli, from the water* → `stromboli` |

A conventional site collapses all three into "related", and then somebody
arrives at a trailhead expecting a summit.

**16 edges across 197 experiences.** They are *authored*, not inferred, and
each was read individually. Substring matching was tried first and produced
"Waterfront architecture walk" → Munch Museum: a plausible-looking lie, which
is worse than an empty column. The remainder is editorial work and
`docs/content-report.md` counts it.

The edge renders both ways: a place page gained a **What happens here**
section, and each experience on a destination page now says which place it is
tied to and how.

## §2.6 Journeys

| schema field | state | here |
|---|---|---|
| `id`, `name`, `slug`, `description` | HAVE | plus `strapline` as the short one |
| `duration_days` | HAVE | `days` |
| `difficulty` | HAVE | already required, already validated |
| `budget_level` | HAVE | `budget`. There is a check for this, because `difficulty` and `budget` share three words and a journey once shipped with `budget: "demanding"` |
| `starting_point`, `ending_point` | HAVE | `start` and `end` |
| **`journey_type`** | **BUILT** | `route` / `loop` / `base` — the three that behave differently when a planner reasons about them |
| **`published`** | **BUILT** | `status` |
| `featured` | REFUSED | as above |
| `hero_image` | HAVE (empty) | |

## §2.7 Journey stops

| schema field | state | here |
|---|---|---|
| `journey_id`, `place_id` | HAVE | a leg names a destination |
| **`sequence`, `day_number`** | **BUILT** | *derived* at load — an array already has an order and a day is one plus the nights before it. Authoring either is a second source of truth that goes wrong silently the first time a leg is inserted |
| `notes` | HAVE | `why` — and it is required, so no leg is unexplained |
| **`place_id` per stop** | **BUILT** | an optional `places` array on a leg, validated against that destination's own places. **0 of 121 legs authored** |
| `experience_id` per stop | GAP | the same edge, one level along |
| **`arrival_time`, `departure_time`** | **REFUSED** | timetable facts with a booking system behind them. We hold no timetables and own no inventory, and a wrong departure time is the most damaging thing this site could print |
| `duration_minutes` | HAVE, differently | `nights`, because the unit of a European journey leg is a night, not a minute |

## §2.8 Businesses

The entity exists as **`data/providers.json`**, and **0 businesses are
listed** — on purpose, not for want of time.

| schema field | state | here |
|---|---|---|
| `business_type` | HAVE | provider categories |
| `verified` | HAVE | a four-tier ladder: Applied (shown as unverified everywhere and in no recommendation) → Reviewed → … |
| `country_id` … `place_id` | HAVE | the same nesting |
| `website`, `phone`, `email`, `address` | HAVE, for a provider | these are volatile on an *editorial place* and are the whole point of a *business record*. The wall is what makes the difference safe |
| `price_level`, `rating` | REFUSED | as above |

**Why the directory is empty.** Seeding it — scraping hotels, importing a
listings feed — would make the product look finished and make every claim on
it unverifiable. `docs/legal-position.md` names three gates, all currently
shut, and `checks.py` fails the build on a payment form, an amount raised or a
progress bar anywhere near it.

## §2.9 Events

| schema field | state | here |
|---|---|---|
| `id`, `name`, `description`, `event_type` | HAVE | `kind` |
| `country_id` | HAVE | events hang off a country |
| **`city_id`** | **BUILT** | optional `city`, validated against that country's destinations. **56 of 150 attached** |
| **`status`** | **BUILT** | |
| `recurrence_rule` | HAVE, differently | every event we hold is annual and carries the month it falls in |
| **`start_at`, `end_at`** | **REFUSED** | we hold the **month**, which is verifiable and stable — Carnevale has been in February for centuries. Exact dates move every year, need a source per event per year, and go wrong silently. A month that is right beats a date that is nearly right |
| `price_from`, `currency`, `website` | REFUSED | volatile |
| `venue_id` | GAP | an event does not yet point at a place |

**Attaching events to destinations fixed a real content bug.** Every festival
in a country was printed on every destination page in it, so Carnevale
appeared on all 25 Italian city pages including the ones 700 km from Venice.
It read as a fact about the place and was a fact about the country. Events
tied to a destination now appear under **Events here**; genuinely nationwide
ones under **Elsewhere in Italy**; and an event tied to a *different*
destination no longer appears at all. Rome has stopped advertising the Palio
di Siena.

## `created_at` / `updated_at` — refused, with an alternative

Every entity in the schema asks for both. There are none, and adding them
would make things worse rather than better:

- **The repository is already the audit log.** `git log` holds the exact
  creation and modification time of every record and cannot drift, because
  nobody maintains it by hand.
- **A timestamp in the data is a second source of truth**, and the one that
  gets forgotten. A record edited without touching `updated_at` now carries a
  date that is confidently wrong.
- **The build must be deterministic.** It has to produce byte-identical output
  on any host with no network — that is what lets CI assert `site/` is not
  stale. Timestamps derived from git differ between a shallow clone and a full
  one, so they would break that guarantee to add a field nothing reads.

What we have instead is **stronger where it matters**: a dated `checked`
record with named sources and a kind for each, whose confidence is *derived*
from the source kind and the age of the check and expires after `REVIEW_DAYS`.
That answers "is this still true?", which is the question `updated_at` is
usually a poor proxy for. It is published at `/sources/freshness`, and **0 of
50 countries are checked today**, which that page states rather than implies.

## §2.10 Stories

Almost entirely present already, and richer than the schema in one place.

| schema field | state | here |
|---|---|---|
| `id`, `title`, `slug` | HAVE | |
| **`story_type`** | **BUILT** | `section`. Nine sections were in use as a *convention*; nothing stopped the tenth story inventing "Adventure & Nature" and quietly starting a second index. Now a validated vocabulary — the union of our nine and the schema's nine, five of which are shared |
| `excerpt`, `content` | HAVE | `standfirst`, `body` |
| `country_id` … `place_id` | HAVE, **better** | `places` is a *list* of destination ids, validated against the atlas. A story about Białowieża crosses the Polish–Belarusian border and a single `city_id` cannot say so |
| `author_id` | HAVE | `author` |
| `published_at` | HAVE | `published`, plus `updated` — the one entity that already carried both |
| **`status`** | **BUILT** | |
| `hero_image` | HAVE (empty) | |
| `featured` | REFUSED | as everywhere |

## §2.11 Transport — half built, half refused

The schema asks for `transport_nodes` and `transport_routes`. They are not the
same kind of thing and they do not get the same answer.

**Nodes: BUILT.** An airport is at a fixed place, and Natural Earth publishes
893 airports and 1,081 ports in the public domain. 257 of 319 destinations now
carry the airports and ports within reach of them, nearest first, derived by
`scripts/map/process.py` and rendered as a **Getting near** section.

| schema field | state | here |
|---|---|---|
| `name`, `node_type` | HAVE | `airport` / `port`. The schema's rail, bus, metro and ferry types are in the vocabulary and unsourced — Natural Earth does not publish stations |
| `latitude`, `longitude` | HAVE | |
| `city_id` | HAVE | attached by radius, not by a fixed top-3: the nearest airport to Amsterdam is 9 km and to Theth is 43 km over a mountain range, and a top-3 would present those as equivalent |
| `iata` | HAVE | where the source has one |

A radius also produces the right answer in the case that matters: **Theth's
nearest airport is Podgorica, in Montenegro.** That is genuinely how you get
there, and no amount of within-country logic would have found it.

**Routes: REFUSED.** `operator`, `duration_minutes`, `frequency`,
`price_from`. Every one needs a licensed feed, every one changes without
notice, and a wrong departure is the most damaging thing a travel page can
print. The distance we show is stated as a **straight line** on the page, in
those words, because 43 km across the Accursed Mountains is four hours and a
number without that sentence is a lie by omission.

## §2.12 Categories and tags

The schema's point — *a flexible taxonomy, so classification does not need a
migration* — is already the architecture, in two layers rather than one
generic join table.

| schema | state | here |
|---|---|---|
| `categories` with `parent_id` | HAVE | `data/taxonomy.json` → `categories`, each with `subs`. One level of nesting, deliberately: two levels of category on 319 destinations is a tree nobody browses |
| `category_type` | HAVE | categories, interests, themes and macro regions are four separate axes rather than one table with a discriminator |
| `entity_categories` | HAVE, differently | an entity carries its `interests`; a category declares which interests it gathers. The join is computed at build time from both ends, so it cannot dangle in either direction |
| the `Paris → Romantic, Historic, Food…` example | HAVE | 17 interests on destinations, regions and countries, plus 6 themes that cross all of them |

**Why not the generic join table.** `entity_categories(category_id,
entity_type, entity_id)` cannot be validated: nothing stops a row pointing at
an entity that does not exist, or at the wrong type. Ours is a list of
interest slugs on the entity, checked against the taxonomy on every build — 
which is the same expressiveness with a failure mode of "the build stops"
rather than "a page is quietly empty".

## §2.13 Media

`data/images.json` is the central register the schema asks for, and it has
been since before the schema arrived.

| schema field | state | here |
|---|---|---|
| `entity_type`, `entity_id` | HAVE | one key, `city:norway/fjord-norway/bergen` — type and id, and the id is the same string the URL uses |
| `url`, `storage_key` | HAVE | `file` |
| `alt_text` | HAVE | `alt`, and **required**: the validator refuses a row without one |
| `credit` | HAVE, **stricter** | `photographer`, `source` AND `licence`, all three required. The register refuses a row missing any, and `checks.py` refuses a published page referencing a file with no row |
| `width`, `height` | HAVE, differently | passed at render, so one photograph serves a card, a hero and a social card without three rows describing the same file |
| `media_type` | GAP | every entry is a photograph today |
| `caption` | GAP | |
| `is_hero` | HAVE, differently | the entity key decides — `city:…` is the hero for that destination |
| **`is_featured`** | **REFUSED** | the wall again: a featured photograph is a paid placement with a different name |

**The register is empty, and that is the honest state.** Zero photographs are
licensed. Everything you see is a generated plate — a landscape from the hash
of the slug, with the motif taken from what the place actually is. An empty
register is a true statement; a register with a placeholder row is not. See
`docs/images.md`.

## §2.14 The knowledge graph — **BUILT**, as a derived index

`/api/graph.json`: **3,716 edges** across nine relationship types, every one of
the schema's examples included.

| relationship | edges | derived from |
|---|---:|---|
| `near` | 1,914 | the same haversine the planner uses, so a route and the graph can never disagree about what is close |
| `serves` | 521 | §2.11 transport nodes, weighted in km |
| `part_of` | 499 | the nesting: destination → region → country → macro |
| `located_in` | 452 | places and experiences under their destination |
| `includes` | 121 | journey legs, carrying the day number |
| `gathers` | 104 | themes |
| `happens_in` | 56 | §2.9 events |
| `about` | 33 | stories |
| `available_at` | 16 | the §2.5 edge, carrying `at` / `from` / `about` |

**The edges are derived, not stored, and that is the whole design.** A
free-standing `relationships` table cannot be validated: nothing stops a row
naming an entity that does not exist, or naming it with the wrong type, and it
fails as a quietly empty page rather than as a stopped build. Every edge here
is computed at build time from a relation already checked somewhere else — so
an edge cannot dangle, because there is nowhere for it to dangle from.
`data/relationships.json` is refused by the validator by name.

**`weight` is only ever a real measurement.** `km`, and nothing else. A
relevance weight would be a number nobody computed from anything, sitting in a
document that looks authoritative. `checks.py` refuses `weight`, `score`,
`relevance` and `confidence` in any edge's metadata.

**One failure worth keeping.** `gathers` shipped at **zero** for one build,
because the derivation read `theme["places"]` and a theme's destinations are
`stops`. That is the one failure a derived index cannot catch for you: a typo
in the derivation itself. The document now carries a count per relationship
and `checks.py` puts a floor under each — a relationship that silently drops to
zero is exactly what nobody notices.

## §2.15 Users — refused, for now, with the reason

There are no accounts, no `users` table, no email addresses and no server that
could hold one. That is a standing decision recorded in
`docs/audit-2026-09.md`, and three things hold it:

- **There is no legal entity.** Holding an email address makes somebody a data
  controller under the GDPR, with obligations that attach to a company that
  does not exist yet.
- **There is no backend.** The site is static files on a CDN. Adding auth
  means adding a server, a session store and an attack surface, for a feature
  nothing currently needs.
- **The feature works without it.** `/my-europe` saves to the browser. No
  account, no email, nothing leaves the device — which is a better privacy
  position than any table could be, and it is what the page says.

`user_preferences` is the interesting one: it exists, and it is *derived*.
**Travel DNA** on `/my-europe` computes travel style, budget level and
interests from what somebody has actually saved, states its own denominator
("computed from the 5 places you have saved"), says it is not a personality
test, and is recomputed on the page every time it opens. A preferences table
somebody fills in once is a table that describes who they were.

## §2.16 Saved places, experiences and journeys — **BUILT**

All three, plus two more, in `localStorage` under `europedoor.saved.v1`:

    saved_places        HAVE   destinations and places, two kinds
    saved_journeys      HAVE
    saved_experiences   BUILT  the one kind you could read about and not keep
    saved themes        HAVE   beyond the schema
    saved stories       HAVE   beyond the schema

Experiences became savable once §2.5 gave each row a stable id to point at,
which is the second time that edge paid for itself.

There is no `user_id` column, because there is no user. The list exports and
imports as text, so moving it between devices is a copy and paste rather than
an account.

## §2.17 The AI layer — already the architecture, and stricter

> *We should not store the AI as the source of truth. The database remains
> authoritative. AI operates on top of it. This prevents the common mistake of
> allowing an LLM to invent the underlying travel database.*

That mistake is **structurally impossible here**, because there is no LLM at
all. The planner and the search are deterministic rule engines that run in the
browser, over `/api/atlas.json` and `/api/search.json`. Every sentence on
every page was written by a person or generated from a validated field. The
planner's own page says so in those words: *"read by rules in your browser —
not by a model, and not sent anywhere."*

When a model is added — it is Phase E, and it is blocked on a decision or a
bill — the contract is already written and is narrower than §2.17 asks for:

1. **A model may read the graph. It may never write it.** No generated value
   enters `data/`, and `git diff` is what enforces it.
2. **No generated sentence may assert a fact that is not in the data.** The
   claim and the field it came from get published together, the way every
   derived fact in this audit already carries its source.
3. **It is named `EuropeDoor Guide`, and the letters "AI" appear in no
   masthead, no navigation and no `h1`** — a check enforces that today,
   before there is anything to name.

## §2.18 PostgreSQL + PostGIS — the trigger, not the timetable

Every capability §2.18 lists is answered today, and the reason is scale rather
than cleverness. Measured on the running dataset:

| §2.18 asks for | state | measured |
|---|---|---|
| find attractions within 2 km | HAVE | scanning **all 255 places** takes **0.17 ms** and finds Sainte-Chapelle and the Covered Passages within 2 km of Paris |
| find destinations within 100 km | HAVE | all **101,442** destination pairs in **73 ms**, in pure Python, at build time |
| find experiences along this route | HAVE | the planner does it, in the browser |
| find places inside this region | HAVE | the nesting *is* containment, and it cannot dangle |
| find nearby transport | HAVE | §2.11, 257 of 319 destinations |
| calculate geographic relationships | HAVE | §2.14, 3,716 edges |
| find restaurants near this hotel | REFUSED | there are no businesses, deliberately — §2.8 |

**A spatial index is an optimisation, and there is nothing yet to optimise.**
PostGIS earns its place the moment one of three things is true, and not
before:

1. **The data stops fitting in a browser.** `/api/atlas.json` is 303 KB today.
   Somewhere north of a few megabytes, shipping the index to the client stops
   being reasonable and the query has to move to a server.
2. **Queries become user-defined at runtime**, rather than the fixed set the
   build can precompute.
3. **There is write traffic** — accounts, submissions, bookings — which needs
   §2.15, which needs a company.

Until then Postgres would add a server, a migration story, a backup story and
a failure mode, to answer in 40 ms what is currently answered in 0.17 ms.
`docs/technical-foundation.md` holds the destination — schema, extensions,
index strategy — and is explicit that nothing in it should be built yet.

## §2.19 The search layer

    PostgreSQL → PostGIS → full-text → vector

Three of those four are answered; the fourth is honest about being absent.

**Full-text and geography: HAVE.** The spec's own example query was run
against the live search during this audit, and it parsed:

> *"romantic mountain villages near Milan"* →
> `near Milan: within 300 km` · `villages: destinations recorded as that` ·
> `reading that as: coast & beaches, islands, wine & drink, architecture, mountains`

Two real gaps surfaced from running it, and both are now closed:

- **"villages" was silently dropped.** `city_type` existed after the §2.2
  audit and the search did not read it, so the query returned Bellagio and
  Vernazza — neither a village. The field is in the index now, and eight kind
  words are parsed.
- **An empty result explained nothing.** It said "nothing for that" and left
  the reader to guess which of five constraints did it, which teaches people
  the search is broken rather than that Czechia is not a low-cost country. It
  now re-runs the query with each modifier dropped and reports what would come
  back: *"Dropping villages would leave 52 places, and dropping near Milan
  would leave 1."*

That second fix also removed a stale number: the empty state said "50
countries and 244 cities" while the atlas held 319. A count typed into a
sentence in a JavaScript file is checked by nothing at all; it comes from the
index now.

**Vector search: GAP, and honestly so.** Semantic similarity needs embeddings,
which needs a model and a bill — Phase E. What stands in for it today is the
modifier map: "romantic" resolves to a set of interests we actually hold. That
is a lookup table pretending to be nothing more than a lookup table, and the
page shows the reader exactly what it did with their words.

## §2.20 The resulting architecture, layer by layer

| the diagram's layer | here |
|---|---|
| EXPERIENCE LAYER — Discover / Plan / Experience | `/discover`, `/plan`, `/experiences`, and the two design worlds those split into |
| JOURNEY ENGINE | `assets/js/planner.js` — deterministic, in the browser, with an honest refusal when it cannot do what was asked |
| AI SERVICES | **none, on purpose.** §2.17 |
| SEARCH ENGINE | `assets/js/search.js` over a 459 KB index |
| RECOMMENDER | Discover Mode and Travel DNA, both derived and both showing their working |
| KNOWLEDGE GRAPH | `/api/graph.json`, 3,716 derived edges |
| GEOGRAPHY | 50 countries, 130 regions, 319 destinations, 255 places, real Natural Earth geometry |
| EXPERIENCES | 197 experiences, 17 journeys, 0 businesses (deliberately), 9 stories |
| LIVE DATA | 150 events by month, 521 transport `serves` edges. **Availability and updates: none** — that is a feed, and feeds are §2.8's problem |
| POSTGRES + POSTGIS | not yet — §2.18 names the three triggers |
| OBJECT STORAGE | not yet. 0 photographs are licensed, so there is nothing to store |

**The shape is right; two floors are unbuilt and both are unbuilt on purpose.**

## What this audit changed

    place_type            24 → 29 values
    iso3                  0 → 50 countries
    country coordinates   0 → 50
    country population    0 → 50, dated
    region type           0 → 130 (all editorial, stated)
    region coordinates    0 → 130, derived
    city_type             0 → 319 of 319 (157 derived, 162 authored)
    city population       0 → 157 of 319
    place↔experience      0 → 16 typed edges
    events → destination  0 → 56 of 150
    journey type          0 → 17
    stop sequence/day     authored twice → derived once
    status                nowhere → countries, regions, destinations,
                          places, experiences, journeys, events
    story_type            convention → validated vocabulary
    transport nodes       none → 257 of 319 destinations
    graph edges           none → 3,716 derived, across 9 relationships
    saved_experiences     unsavable → savable
    searchable city_type  ignored → 8 kind words parsed
    empty search state    "nothing for that" → which constraint emptied it
    refusals              4 fields → 25, enforced at the file level

## Still open, and editorial rather than technical

| | |
|---|---|
| place ↔ experience edges | 181 of 197 experiences unlinked |
| journey stop places | 121 of 121 legs unlinked |
| experience difficulty and season | 0 of 197 |
| events tied to a destination | 94 of 150 |
| photographs | 0 licensed. `docs/images.md` |
| fact-checking | 0 of 50 countries. `/sources/freshness` |
| transport nodes | 62 of 319 destinations have no airport or port within reach — mostly inland villages, which is the true answer |
| media `caption`, `media_type` | not modelled; nothing to caption yet |
