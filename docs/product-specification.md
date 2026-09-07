# Europedoor — product specification

**Product: Europedoor. Domain: europedoor.com. The name is settled — see
[`brand-lock.md`](brand-lock.md).**

This document takes a 36-section strategy brief and turns it into decisions:
what is built, what is specified and not built, what is deliberately refused,
and — for everything in the middle two categories — enough detail that a
developer could start on Monday.

It is organised in three parts.

* **Part 1** answers the brief section by section, so nothing is silently
  dropped.
* **Part 2** is the buildable specification: schema, API, AI architecture,
  dashboards, money.
* **Part 3** is sequencing: MVP, roadmap, cost, risk.

Where this document disagrees with the brief, it says so and why. There are
four such places and they are marked **DEVIATION**.

---

## Part 0 — the one-sentence version

> Europedoor is where a traveller works out what Europe *is* and what they
> want from it. Booking is what happens afterwards, and it is not the
> product.

Everything below is downstream of that sentence. The test for any feature is
whether it improves the decision a traveller makes before they book. A
feature that only improves the transaction belongs to somebody with more
inventory than us.

---

# Part 1 — the brief, answered

## 1. The core idea — **adopted**

Discovery + planning + experience, not booking. Built: the whole site is a
structure first (`/atlas`) with planning (`/plan`), curation (`/journeys`,
`/themes`), doing (`/experiences`) and reading (`/stories`) hung off it.

## 2. Brand positioning — **settled, and closed**

**DEVIATION 1.** The brief proposes a naming exercise (Europia, Via Europa,
Europe Atlas, and so on) and suggests "EUROPE ATLAS" as a working name. The
name is Europedoor, at europedoor.com, and that is a decision already taken.
"Atlas" survives as the name of pillar one — the country/region/city
structure — and never as the name of the product.

What is still genuinely open, and is on the pre-launch list: trademark
clearance in Nice classes 39 (travel arrangement), 41 (publishing) and 42
(software), plus an EU register search for confusable marks. Owning a domain
is not owning a mark.

## 3. Site architecture — **adopted with a changed top level**

The brief proposes `DISCOVER | COUNTRIES | EXPERIENCES | JOURNEYS | PLAN |
STORIES | BUSINESS | COMMUNITY` — eight items.

**DEVIATION 2.** Shipped with five: **Atlas · Journeys · Plan · Experiences ·
Fund**. Reasons, in order of weight:

1. *Discover* and *Countries* are the same thing wearing two labels. Merged
   into Atlas, which is the honest name for a hierarchy of places.
2. Eight top-level items is above the number a person scans. Five is not.
3. *Stories* and *Community* are real and are reachable from the footer and
   from contextual links, which is where editorial actually gets read — from
   inside an article about a place, not from a nav bar.
4. *Business* is a different audience with different intent. It belongs
   behind `/experiences/join`, where the person who needs it is already
   standing.

Everything in the brief's tree exists. It is reached from a shorter nav.

| brief's node | where it lives now |
|---|---|
| Discover / Countries | `/atlas`, `/atlas/<macro>`, `/atlas/<macro>/<country>` |
| Regions | `/atlas/<macro>` (nine regions of Europe) and per-country travel regions |
| Experiences (by type) | `/experiences/<kind>` and `/interests/<slug>` |
| Journeys (by length) | `/journeys`, filterable by days in `/plan` |
| Plan | `/plan` |
| Stories | `/stories` |
| Search | `/search` |
| Business | `/business`, `/experiences/join` |
| Community | `/fund`, `/my-europe` |

## 4. The Europe Atlas — **built**

`Europe → region of Europe → country → travel region → city → experience`,
generated end to end from `data/`. 50 countries, 121 travel regions, 244
cities, 166 experiences. Every city page carries: summary, what earns the
time, experiences, an Experience Score, a suggested night range, coordinates,
and computed nearest onward stops.

One deliberate difference from the brief: the brief's level 3 is
*municipality*. Ours is a **travel region**, which is editorial rather than
administrative — Fjord Norway is not an administrative unit and is exactly
how people think about going there. Administrative geography is a data field
we can add later without changing the URL shape.

## 5. Experience-first discovery — **built** as Themes

`/themes` — thirteen cross-border ways in: medieval, sacred, Viking, mountain,
Roman, wine, rail, island, Jewish, Renaissance, Grand Tour, thermal and
modernist Europe. Each is a real sequence of real
places, each place linked back into the Atlas. This is the brief's "I want
medieval Europe" query, answered as a page rather than a search result,
because a curated answer with reasons beats a filtered list.

## 6 & 26. The AI journey planner — **half built, and the half that matters**

**Built today, without a model:** `/plan` scores all 244 cities against your
interests, month, budget and pace, then builds a route greedily with a
distance penalty, allocates nights from each city's published range, and
estimates cost. It runs entirely in the browser. Nothing is sent anywhere.

**Not built:** natural language in, and prose out.

This ordering is deliberate and is the single most important architectural
decision in this document. The brief's own diagram (§26) has it right:

```
USER → intent extraction → knowledge graph → route engine → generator → USER
```

Everything except the first and last boxes is the hard part, and it is the
part that does not need a model. We built it first. Adding language later is
an interface change, not a re-architecture.

**The rule, which is non-negotiable:** the model never supplies facts. It
receives a route that the deterministic engine produced, plus the dataset
rows behind it, and writes it up. If the dataset is silent, the answer is
"we do not cover that yet." A travel platform that invents a train connection
is worse than no travel platform, and it is worse in a way that ends the
brand.

Prompts and the retrieval contract are in Part 2.

## 7 & 8. The journey engine and Trans-Europe journeys — **built**

Eight curated journeys, 148 days between them, including the brief's two
flagship shapes: Atlantic → Mediterranean, and Arctic → Baltic. Each leg
names a city in the Atlas, a night count and a reason, and the validator
refuses to load a journey whose nights do not sum to its advertised days —
an error that is invisible in prose and obvious to a customer.

## 9. Experience marketplace — **listed, not transacted**

Experiences are listed with kind, price band and location. What is
specified and not built: operator accounts, availability, checkout,
commission. See Part 2, "Money".

## 10. Business directory — **specified and seeded**

Three tiers (Applied / Reviewed / Verified), published at
`/experiences/join`, with what each tier actually checks. Eight illustrative
records at `/business`, labelled as examples.

The commercial rule is stated on the page, not just in this document: **paid
tiers buy presentation on directory surfaces, and never Atlas ranking,
planner weighting, or a place in a curated journey.** There is no field in
the data that could carry a paid boost, which is the only version of that
promise worth making.

## 11. Stories — **built**

Eight pieces across six desks, each linked into the Atlas and each Atlas
page reachable from the story. Editorial is not decoration here: it is the
only part of the product that a competitor cannot generate.

## 12. Faith and heritage layer — **built, carefully**

`/themes/sacred-europe` and `/themes/jewish-europe`, plus the `sacred`
interest across the Atlas. Two rules were applied while writing them: name
the tradition rather than genericising it, and where a site is a memorial
rather than an attraction, say so in the entry itself.

## 13. Events — **built at annual resolution**

`/events` lists the recurring European year — festivals, markets,
pilgrimages, harvests — month by month, drawn from country data. Dated
listings for a specific year need a live feed and a rights position on
third-party event data; that is Stage 2 and is specified in Part 2.

## 14. Map — **built, without a vendor**

`/map` draws all 244 cities from their own coordinates on an
equirectangular projection, filterable by sixteen layers, entirely
self-hosted. No tiles, no Mapbox key, no third-party request, and it works
offline. A tiled basemap is a Stage 2 decision with a bill attached; this
version costs nothing and cannot break when a vendor changes pricing.

## 15. The Europe Experience Score — **built, with the formula published**

Six dimensions — nature, history, food, culture, adventure, value — computed
from editorial tags by a formula published in full at `/method`, recomputed
on every build, never stored. Ceiling 97, floor 12, so nothing is perfect and
nothing is worthless.

The brief's caution is the whole design: "scores need transparent
methodology so they don't become arbitrary rankings." Ours are transparent to
the point of publishing the weight tables. They are also, deliberately,
*descriptive not evaluative* — a 94 for Adventure means the place is about
adventure, not that it does adventure better than a 71. That distinction is
printed under every score.

## 16. Responsible tourism — **built into the mechanism, not the copy**

`/beyond-the-obvious` names the quiet alternatives and six straight swaps.
More importantly the *mechanism* leans that way: the planner multiplies
shoulder-season fit upward, a Galician fishing town gets the same page
template as Paris, and nearest-onward-stops are computed rather than
curated so they cannot flatter a partner.

One editorial rule, on the page: **we never describe anywhere as
undiscovered.** Publishing that sentence is the fastest way to make it false.

## 17. Hidden Europe — **built** as the `quiet` flag

Cities carry a `quiet` boolean; `/beyond-the-obvious` collects them. Deliberately
a small, arguable, editorial tag rather than a claim of obscurity.

## 18. User account / My Europe — **built without an account**

`/my-europe` saves places in `localStorage`. No account, no server, no
identifier, nothing to leak, and honest about it: if the list is empty in a
new browser, the page says why. Accounts are specified in Part 2 and gated on
a data controller and a published privacy notice.

## 19. Social features — **deferred, and mostly refused for MVP**

Published itineraries and collections are worth building. Follows, feeds and
profiles are a different company. Specified in Part 2 at the level of "what
would have to be true first" — which includes moderation capacity, and
moderation capacity means people.

## 20. Multilingual — **specified, not built**

English only today. The infrastructure decision is made and recorded in
Part 2: every translatable string lives in `data/`, so translation is a data
task and not a code task. The harder decision is also made: destination copy
gets **localised, not machine-translated** — a French page about Bergen
should be written for a French traveller, not run through a model.

## 21. Mobile app — **agreed: not now**

The brief says build the web platform first. Correct. The site is responsive
and verified at 390 CSS pixels by an automated browser check, which is the
useful 90% of what an app would deliver in year one.

## 22. Revenue — **adopted, sequenced, and one stream refused**

Seven streams in the brief. Our order and our position on each is in Part 2,
"Money". Short version: affiliate first because it needs no counterparty
negotiation, directory subscriptions second because they are the only stream
that scales without inventory, bookings third, and **display advertising
refused** — not deferred. A discovery product whose recommendations sit next
to paid placements has thrown away the only thing it had.

## 23. B2B intelligence — **agreed as the long-term prize, deferred**

Real, and possibly larger than the consumer business. It is also worth
nothing until there is traffic to derive data from. Specified in Part 2 as a
data-collection design decision to make *now* (event schema) so the product
exists later.

## 24. The database as a knowledge graph — **adopted; this is the core asset**

The brief is right that this is the part to take seriously. Today it is JSON
files with a validator that refuses to load a city pointing at a region that
does not exist. The Postgres schema in Part 2 is the same shape, and the
migration is mechanical because the JSON was written against it.

**DEVIATION 3** on scale. The brief targets "hundreds of thousands of places,
millions of businesses". That is a scraped database, and a scraped database is
worth nothing here, because the entire premise is that a human wrote every
entry. 244 cities written properly beats 40,000 imported. Growth target is
tens of cities per month, forever, not import batches.

## 25. Technology stack — **deliberately smaller than proposed**

The brief proposes Next.js, Postgres, OpenSearch, Mapbox, an LLM API, an auth
provider, Stripe, a headless CMS, an image CDN and analytics.

**DEVIATION 4.** Today: Python 3 standard library, no dependencies, no
database, no JavaScript framework. Output is 507 static HTML files.

This is not minimalism as an aesthetic. It is that every item on that list is
a subscription, a key, an outage and a migration, and none of them earns its
place until there is a user whose problem it solves. Search is a client-side
filter over a 400 KB index. The map is an SVG. The CMS is a directory of JSON
files under version control with a validator, which gives review, history and
rollback for free.

Part 2 names the trigger for each addition — the specific condition under
which Postgres, or auth, or a payment provider, becomes the right call.

## 27 & 28. MVP scope — **partly followed**

The brief says: five countries, done exceptionally well.

**Our position:** we shipped fifty at solid depth rather than five at
maximum depth, and then designated five for depth-first work. The reason is
that the *structure* is the thing being tested and a five-country structure
cannot show whether the model holds across Europe — Norway and Albania break
different assumptions. The brief's instinct is right about effort
concentration, so:

**Depth tier A (deepen first):** Norway, France, Italy, Spain, Greece.
Target: 8+ regions, 25+ cities, 40+ experiences, 5 stories, verified facts
with dates.
**Depth tier B:** everything else, at current depth, verified opportunistically.

## 29. Homepage — **built, differently worded**

The brief's homepage is right in structure: explore by region, then by kind
of Europe, then journeys, then hidden Europe, then stories, then plan.
Shipped in that order. The AI search box is absent because there is no AI
search yet, and a box that pretends is worse than no box.

## 30. Flywheel — **agreed, with the loop named honestly**

Content → SEO → travellers → discovery → planner → journeys → bookings →
revenue → more local businesses → more content. The load-bearing and slowest
arrow is the first one, and Part 3 budgets for it accordingly.

## 31 & 32. Competition and the differentiator — **agreed**

We do not compete with Booking.com on inventory. The sentence to build the
company around, from the brief and adopted verbatim:

> We don't just help people book Europe. We help them discover Europe.

## 33, 34. Stages and roadmap — **adopted, in Part 3**

## 35. The strategic decision — **adopted**

Positioned as Europe's discovery engine, not another European travel site.

## 36. Final architecture — **adopted; it is the shape of the repo**

```
                        EUROPEDOOR
                            |
        +-------------------+-------------------+
     DISCOVER              PLAN            EXPERIENCE
     Atlas /atlas       Planner /plan     Experiences
     Themes /themes     Journeys          Fund /fund
     Stories /stories   Budget & season   Business
     Map /map           Transport notes   Events
        +-------------------+-------------------+
                            |
                     EUROPE DATABASE
                        (data/)
        +-------------------+-------------------+
      PEOPLE             PLACES           BUSINESSES
      Stories       Countries/regions      Providers
      Guides        Cities/experiences     Tiers
      Partners      Themes/journeys        Fund partners
```

---

# Part 2 — the buildable specification

## 2.1 Data model, today

Everything lives in `data/` as validated JSON. `tools/lib/data.py` is the
schema and it fails the build rather than publishing a broken page.

```
data/taxonomy.json      9 macro regions, 17 interests, 3 budget bands,
                        12 months, 5 blocs, 10 experience kinds
data/countries/*.json   50 files, one per country, each containing its
                        regions and their cities and their experiences
data/journeys.json      8 curated routes referencing city ids
data/themes.json        9 cross-border themes referencing city ids
data/stories.json       8 editorial pieces referencing city ids
data/fund.json          12 register entries (no amounts — enforced)
data/providers.json     3 tiers, 8 seeded provider records
```

A city's identity is `"<country>/<region>/<city>"` and every cross-reference
in the dataset uses it. The full field list is in
[`data-model.md`](data-model.md).

## 2.2 Data model, at Postgres

The migration trigger: **when a write comes from anyone other than a
committer.** Operator claiming a listing, a user account, a booking — the
first of those is the day this schema ships. Until then, files are better:
review, history, rollback and offline editing, for free.

```sql
-- Places -------------------------------------------------------------
create table macro_region (
  slug text primary key,
  name text not null,
  blurb text not null,
  sort int not null
);

create table country (
  slug text primary key,
  iso2 char(2) not null unique,
  name text not null,
  official_name text,
  macro_region text not null references macro_region(slug),
  capital text not null,
  currency text not null,
  languages text[] not null,
  blocs text[] not null default '{}',       -- eu, schengen, eurozone, eea, cta
  tagline text not null,
  summary text not null,
  interests text[] not null,
  budget_band text not null check (budget_band in ('low','moderate','high')),
  daily_eur int4range not null,
  season_peak text[] not null,
  season_shoulder text[] not null default '{}',
  season_note text not null,
  getting_around text not null,
  advisory_level text check (advisory_level in ('caution','avoid')),
  advisory_note text,
  facts_checked_on date,                    -- null = never verified
  facts_checked_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table travel_region (
  id bigserial primary key,
  country text not null references country(slug) on delete cascade,
  slug text not null,
  name text not null,
  summary text not null,
  interests text[] not null,
  unique (country, slug)
);

create table city (
  id bigserial primary key,
  travel_region bigint not null references travel_region(id) on delete cascade,
  slug text not null,
  name text not null,
  point geography(point, 4326) not null,    -- postgis
  summary text not null,
  interests text[] not null,
  nights_min smallint not null check (nights_min between 1 and 7),
  nights_max smallint not null check (nights_max between 1 and 7),
  quiet boolean not null default false,
  highlights text[] not null,
  facts_checked_on date,
  check (nights_max >= nights_min),
  unique (travel_region, slug)
);
create index on city using gist (point);
create index on city using gin (interests);

-- Doing --------------------------------------------------------------
create table experience (
  id bigserial primary key,
  city bigint not null references city(id) on delete cascade,
  slug text not null,
  name text not null,
  kind text not null,                       -- walk, table, cellar, ...
  band text not null check (band in ('low','moderate','high')),
  summary text not null,
  provider bigint references provider(id),  -- null = editorial, not sold
  price_cents int,
  currency char(3),
  unique (city, slug)
);

create table provider (
  id bigserial primary key,
  slug text not null unique,
  name text not null,
  kind text not null,
  city bigint references city(id),
  country text references country(slug),
  tier text not null check (tier in ('applied','reviewed','verified')),
  summary text not null,
  checks text[] not null default '{}',
  claimed_by bigint references app_user(id),
  registration_ref text,                    -- company number / guide licence
  insured_until date,
  subscription text check (subscription in ('free','professional','premium')),
  created_at timestamptz not null default now()
);

-- Curation -----------------------------------------------------------
create table journey (
  slug text primary key,
  name text not null, strapline text not null, summary text not null,
  days smallint not null, budget_band text not null,
  interests text[] not null, months text[] not null
);
create table journey_leg (
  journey text references journey(slug) on delete cascade,
  position smallint not null,
  city bigint not null references city(id),
  nights smallint not null check (nights >= 1),
  why text not null,
  primary key (journey, position)
);
-- The invariant the JSON validator enforces today, kept in the database:
create or replace function journey_nights_match() returns trigger as $$
begin
  if (select sum(nights) from journey_leg where journey = new.journey)
     <> (select days - 1 from journey where slug = new.journey) then
    raise exception 'journey % nights do not sum to days - 1', new.journey;
  end if;
  return new;
end $$ language plpgsql;

create table theme (
  slug text primary key, name text not null, strapline text not null,
  summary text not null, interests text[] not null
);
create table theme_stop (
  theme text references theme(slug) on delete cascade,
  city bigint not null references city(id),
  why text not null,
  primary key (theme, city)
);

create table story (
  slug text primary key, title text not null, section text not null,
  standfirst text not null, reading text not null,
  body text[] not null, published_at timestamptz
);
create table story_place (
  story text references story(slug) on delete cascade,
  city bigint not null references city(id),
  primary key (story, city)
);

-- Community ----------------------------------------------------------
create table fund_project (
  slug text primary key,
  name text not null, theme text not null,
  country text not null references country(slug),
  partner text not null, summary text not null, need text not null,
  status text not null check (status in ('listed','in-progress','complete'))
  -- deliberately no amount, raised, goal or target column. See europe-fund.md.
);

-- People -------------------------------------------------------------
create table app_user (
  id bigserial primary key,
  email citext unique,
  created_at timestamptz not null default now(),
  locale text not null default 'en',
  marketing_consent_at timestamptz             -- opt-in only, timestamped
);
create table saved_item (
  app_user bigint references app_user(id) on delete cascade,
  kind text not null check (kind in ('city','journey','theme','story','experience')),
  ref text not null,
  saved_at timestamptz not null default now(),
  primary key (app_user, kind, ref)
);

-- Measurement (see 2.7) ----------------------------------------------
create table event (
  id bigserial primary key,
  at timestamptz not null default now(),
  session uuid not null,                    -- rotates daily, never joined to a person
  name text not null,
  props jsonb not null default '{}'
);
create index on event (name, at desc);
```

Three notes on this schema, because they are the arguable parts:

* **`facts_checked_on` is nullable and that is the feature.** A null means
  "written editorially, never verified", which is the truth for the whole
  dataset today, and `/sources` says so. A schema that cannot express "we do
  not know" produces a site that lies by omission.
* **`experience.provider` is nullable.** An experience with no provider is
  editorial: we think you should do this, nobody pays us, nothing is sold.
  That must remain the majority of them.
* **There is no `rank`, `boost`, `featured_until` or `sponsored` column on
  `city` or `experience`.** Sponsorship lives on `provider` and can only
  affect directory surfaces. This is the schema-level version of the
  editorial wall.

## 2.3 API surface

Public, read-only, cacheable, no key:

```
GET /api/atlas.json          the planner index: every city with interests,
                             nights, cost band, season and url. ~400 KB.
                             Advisory countries are absent from it.
GET /api/search.json         one flat row per findable thing: name, kind,
                             url and a lowercased text blob. Advisory
                             countries ARE present — a page nobody can
                             search for is a page that does not exist.
GET /api/countries.json      country-level facts (Stage 2)
GET /api/journeys.json       curated routes (Stage 2)
```

Authenticated, Stage 2 onward:

```
POST   /api/plan             { days, budgetEur, month, style, pace,
                               start?, interests[] } -> itinerary
GET    /api/me/saved         the saved list
PUT    /api/me/saved/:kind/:ref
DELETE /api/me/saved/:kind/:ref
POST   /api/providers/claim  { providerSlug, evidence }
GET    /api/providers/:slug/stats   directory analytics for the owner
POST   /api/fund/interest    register interest in a project (no money)
```

`POST /api/plan` exists so the mobile app and the AI layer share the exact
route engine the browser runs. There must never be two implementations of the
scoring rules; if the server ever disagrees with `/plan`, one of them is
wrong and nobody will know which.

## 2.4 The AI architecture, concretely

### The pipeline

```
user text
   ↓  (1) intent extraction        model, strict JSON out, no facts
   ↓  (2) retrieval                SQL / index over our own data only
   ↓  (3) route engine             the same deterministic code as /plan
   ↓  (4) narration                model, given rows + route, no lookup
   ↓  (5) citation check           every place named must be in the payload
answer
```

Steps 2, 3 and 5 are ours and are not probabilistic. Steps 1 and 4 are the
only model calls, and neither is permitted to introduce a fact.

### (1) Intent extraction — system prompt

```
You convert a traveller's message into a JSON planning request for
Europedoor. You never answer travel questions and you never name places
that the user did not name.

Return exactly this JSON and nothing else:

{
  "days": integer | null,
  "budgetEur": integer | null,
  "travellers": integer | null,
  "month": "jan".."dec" | null,
  "startCity": string | null,      // verbatim from the user, not resolved
  "endCity": string | null,
  "interests": string[],           // ONLY from the allowed list below
  "style": "low" | "moderate" | "high" | null,
  "pace": "slow" | "balanced" | "fast" | null,
  "unsupported": string[]          // anything asked for that this schema
                                   // cannot express, quoted verbatim
}

Allowed interests: history, art, architecture, sacred, food, wine,
mountains, coast, islands, nature, wild, winter, cities, music, design,
rail, festivals.

Rules:
- Never invent a value to be helpful. Missing means null.
- Never map an interest to a near neighbour. "I like castles" is history.
  "I want to see the northern lights" is nature and winter. "I want to go
  clubbing in Berlin" is music, and "Berlin" goes in startCity only if
  they said they are starting there.
- Anything you cannot express goes in "unsupported" verbatim, including
  accessibility needs, travelling with a dog, dietary requirements and
  visa questions. Do not silently drop them.
```

`unsupported` is the important field. It is how the product finds out what
it does not do, from the people who wanted it, in their words.

### (2) Retrieval contract

The only source is our own data. The retriever returns, for a request:

* up to 60 candidate cities with all scoring fields;
* the country rows behind them;
* any curated journey or theme whose interest set overlaps by ≥2;
* the `advisory` state of every country touched — and advisory countries are
  filtered out before this point, not after.

If retrieval returns fewer than 3 cities, the pipeline stops and answers "we
do not cover that yet." It does not proceed to a model with thin context and
hope.

### (4) Narration — system prompt

```
You are writing up an itinerary that has already been decided. You are not
choosing anything.

You will receive:
  ROUTE  — an ordered list of stops with night counts and distances
  ROWS   — the Europedoor dataset rows for exactly those places
  ASK    — what the traveller said they wanted

Write the itinerary in the voice of a well-travelled editor: specific,
unhurried, no superlatives, no "hidden gem", no "must-see", no exclamation
marks. British spelling. Second person.

Absolute rules:
- Every factual claim must appear in ROWS. If it is not in ROWS, you may
  not write it. This includes opening hours, prices, journey times,
  restaurant names and the existence of anything.
- Do not add a place that is not in ROUTE, even as a suggestion.
- Where the ASK mentions something ROWS cannot answer, say so plainly in
  one sentence at the end, under "What this plan does not cover".
- Costs are estimates from published daily bands. Say "estimate", never
  "price".
- End each stop with why it is in this route, referring to what the
  traveller asked for.
```

### (5) Citation check — refusal is a feature

After generation, every proper noun in the output is matched against the
place names in the payload. Any unmatched name fails the response and it is
regenerated once; a second failure returns the deterministic itinerary
without prose. **The user never sees a sentence we cannot source.**

### What we will not do with a model

* Answer visa, entry or safety questions. These change, they are
  consequential, and the correct answer is a link to the government source.
* Generate destination copy at scale. The written dataset is the moat; a
  generated one is a commodity with our name on it.
* Translate destination copy. See §20.

## 2.5 Money

Streams, in the order they can realistically be turned on:

| # | stream | needs | when | position |
|---|---|---|---|---|
| 1 | Affiliate (rail, ferry, accommodation, activities) | a company, a bank account, programme approvals | Stage 2 | Disclosed on every link. Never determines ranking. |
| 2 | Directory subscriptions (Free / €49–99 / €199+ per month) | entity, invoicing, VAT (MOSS/OSS), an operator dashboard | Stage 2 | The only stream that scales without inventory. Prices untested — set them after 100 operator conversations, not before. |
| 3 | Experience commission, 10–15% | payments, consumer law, refunds, insurance verification | Stage 3 | Operator sets the price and keeps the customer relationship. |
| 4 | Sponsored destination campaigns (tourism boards) | media pack, ad-labelling policy | Stage 3 | Labelled, time-boxed, never inside planner results. |
| 5 | Premium membership (~€49/yr: offline guides, deeper planning) | accounts, PDF export, billing | Stage 3 | Only once the free planner is good enough that people would miss it. |
| 6 | Curated journeys sold as packages | package travel regulations, bonding/insolvency protection, ATOL-equivalents | Stage 3+ | The heaviest regulatory lift in this table. Do not stumble into it by accident — selling a flight plus a hotel together is a package, legally. |
| 7 | Display advertising | — | **refused** | Not deferred. Refused. |

**The commission flow**, when it exists:

```
traveller books  →  Europedoor takes payment as agent (PSP)
                 →  operator is paid out on completion, minus 10–15%
                 →  cancellations follow the operator's stated policy,
                    which must be published before a listing goes live
                 →  disputes: we refund from our commission first
```

Three things must be true before a single euro moves, and they are the same
three that gate the Fund:

1. an incorporated entity with a bank account;
2. a named payee on every surface where a card number can be typed —
   the check that fails the day a card field appears without one;
3. a written position on consumer law in the jurisdictions we sell into,
   including cancellation rights and package travel rules.

## 2.6 Dashboards

**Operator dashboard** (Stage 2). Six screens, no more:

1. *Profile* — the listing, and the tier with what it means and what is
   missing to reach the next one.
2. *Verification* — upload registration, licence, insurance; each shows
   status and expiry. Insurance expiring silently drops the tier.
3. *Experiences* — listings, prices, what is and is not included.
4. *Stats* — views, saves, planner appearances, click-throughs. Weekly, not
   real-time, because real-time invites gaming.
5. *Billing* — plan, invoices, VAT number.
6. *Messages* — traveller enquiries, with a response-time figure shown to
   the operator before it is ever shown to a traveller.

**Admin dashboard** (Stage 1.5 — this is the first thing that needs auth):

1. *Editorial queue* — new and edited places awaiting review; every change
   is a diff, because every change is a file.
2. *Verification queue* — provider applications with evidence.
3. *Fact freshness* — every country and city by `facts_checked_on`, oldest
   first. This screen is the verification plan made operational.
4. *Fund register* — projects, partners, status.
5. *Corrections log* — reader reports, what changed, when. Published.

**Tourism-board dashboard** (Stage 3, the B2B product): demand by month,
interest mix, planner route flows through a region, comparison against
neighbouring regions. Aggregated, k-anonymised, never per-person.

## 2.7 Measurement, decided now because it cannot be retrofitted

The B2B product in §23 is derived from behaviour, and behaviour you did not
record is gone. So the event schema is fixed now even though nothing consumes
it yet:

```
plan_requested   { days, budgetBand, month, pace, interests[] }
plan_returned    { stops, countries[], estimatedEur, overBudget }
plan_rejected    { reason }              -- nothing fit
city_viewed      { cityId, from }
theme_viewed     { themeSlug }
journey_opened   { journeySlug, inPlanner }
save_added       { kind, ref }
outbound_click   { target, context }
unsupported_ask  { text }                -- from the AI intent extractor
```

Rules: a rotating daily session id, no cross-site identifiers, no third-party
analytics, and `unsupported_ask` reviewed weekly by a person because it is the
product roadmap arriving for free.

## 2.8 Internationalisation

Decided: translatable strings live in data, not in code. The mechanism:

```
data/countries/norway.json          -> the English source of truth
data/i18n/fr/countries/norway.json  -> a partial overlay; any key present
                                       replaces the English one
```

The build emits `/fr/atlas/...` with `hreflang` alternates and a canonical
per language. A missing key falls back to English and the page marks that
section as untranslated rather than pretending.

Order: **fr, de, es, it, nl** first (largest intra-European travel markets),
then pt, pl, and the Nordics — which is a smaller win because English
literacy there is very high.

## 2.9 What is deliberately blocked, and by what

| blocked | unblocked by |
|---|---|
| Taking any payment | entity + named payee on every card surface + PSP contract |
| Holding Fund contributions | the above, plus a written position per collecting country |
| Storing user or business data | a named data controller + lawful basis + published privacy notice |
| Naming an operating company on the site | that company existing |
| Publishing a photograph | a licence audit, or a commissioned shoot we own |

`tools/checks.py` enforces four of these five against the built HTML on every
run.

---

# Part 3 — sequencing

## 3.1 MVP — what is already true

Built and passing checks: the Atlas (50/121/244), the Planner, Search, 8
Journeys, 13 Themes, 8 Stories, the Map, Experiences with a verification
model, the Fund register, the Experience Score with a published method, My
Europe, Events, and an honest status page.

Search shipped as part of this pass: one flat index of every findable thing,
fetched once and filtered in the browser, with accent folding so "malmo"
finds Malmö. Ranking is exact name, then prefix, then substring, then body
position, weighted by kind — explainable, and with no field that could carry
a paid position.

Not built and next, in order:

1. **Depth tier A.** Norway, France, Italy, Spain, Greece to 25+ cities each.
2. **Fact verification pass** with `facts_checked_on` dates surfaced.
3. **Twenty more stories**, because organic traffic comes from those and not
   from the Atlas.
4. **The AI layer**, as specified in 2.4, once 1–3 are done.

## 3.2 Roadmap, twelve months

| months | focus | ships |
|---|---|---|
| 1–2 | Foundation | Entity incorporated; trademark search; privacy notice; the depth-tier-A editorial plan; search |
| 3–4 | Depth | Tier A countries to full depth; fact verification pass with dates; 10 more stories |
| 5–6 | Reach | i18n mechanism plus French and German for tier A; events feed; sitemap and structured data work |
| 7–8 | Intelligence | AI planner per 2.4, with the citation check; `POST /api/plan`; accounts and saved-list sync |
| 9–10 | Commercial | Operator dashboard; verification queue; directory subscriptions; affiliate links with disclosure |
| 11–12 | Launch | PR around the Fund and the responsible-travel position; tourism-board conversations; first bookings pilot in one country |

## 3.3 Cost, honestly framed

The brief's three stages (€10–30k, €50–150k, €250k+) are reasonable for
*development*. They understate the thing that actually decides this business,
which is editorial. A country at depth-tier-A quality is roughly 15–25 days
of a good writer who knows the place. Fifty of those is a year of a small
desk, and it is not optional: the dataset is the product and a cheap dataset
is a dead product.

Budget shape for year one, if building in-house:

* editorial: the largest single line, and the one to protect in a cut;
* engineering: one person can carry Stage 1 and most of Stage 2;
* legal: entity, trademark, privacy, and — before any booking — package
  travel advice. Small in euros, fatal if skipped;
* infrastructure: near zero until Stage 2, by design.

## 3.4 The risks that actually matter

1. **The dataset gets diluted.** The moment the answer to "we need more
   coverage" is an import, the differentiator is gone. Mitigation: the growth
   target is in cities per month, and there is no importer in the codebase.
2. **The editorial wall moves under commercial pressure.** Mitigation: it is
   enforced in the schema and in `checks.py`, so moving it requires a commit
   that says so.
3. **Facts age and nobody notices.** Mitigation: `facts_checked_on`, the
   freshness screen, and `/sources` stating plainly that the dataset is a
   considered first draft.
4. **The AI layer ships before the retrieval discipline.** This is the one
   that ends the brand rather than slowing it. Mitigation: the citation check
   in 2.4(5), and shipping the deterministic planner first — which is done.
5. **Package travel regulation, walked into sideways.** Selling a journey
   with transport and accommodation together is a regulated package in the
   EU. Mitigation: it is stream 6 of 7 and needs advice before a line of
   code.

---

## Where to look next

* [`architecture.md`](architecture.md) — how the built system works
* [`data-model.md`](data-model.md) — the field-by-field schema
* [`scoring-method.md`](scoring-method.md) — the Experience Score
* [`europe-fund.md`](europe-fund.md) — why the Fund holds nothing
* [`legal-position.md`](legal-position.md) — originality, entity, data
* [`brand-lock.md`](brand-lock.md) — the name, and why it does not change
* [`roadmap.md`](roadmap.md) — the same roadmap, kept current
