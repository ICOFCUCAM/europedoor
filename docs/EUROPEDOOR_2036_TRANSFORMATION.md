# EuropeDoor 2036 — audit and transformation architecture

Written before any code changed, per §65 of the transformation brief. Nothing
in this document has been built yet; where something already exists it is
marked as existing, and the distinction is the point.

---

# Part 1 — The audit

## 1. Current technology stack

| | |
|---|---|
| Language | Python 3.11, **standard library only** |
| Runtime dependencies | **zero** |
| Framework | none — a purpose-built generator, `tools/build.py` |
| Package manager | none. No `package.json`, no lockfile |
| Database | **none** — 57 validated JSON files under version control |
| Auth | **none** |
| Client JS | 5 vanilla files, 98 KB uncompressed, no framework, no bundler |
| CSS | one hand-written stylesheet, 44 KB, 208 classes |
| Deploy | Vercel, static, `buildCommand: python3 tools/build.py` |
| CI | GitHub Actions, 7 gates |
| Output | **1,059 HTML files + 781 social cards**, committed, CI fails if stale |

## 2. Existing architecture

`data/*.json` → validate → 68 page builders → **one page shell** → `site/`.

Four rules, all enforced: one shell; `site/` is generated and committed;
no inline `<style>` or `style=` attribute anywhere; no ranking column on a
place. The build takes 2 s warm.

## 3. Existing database

None. `tools/lib/data.py` is the schema, and it enforces more than most
relational schemas do: volatile fields (`hours`, `price`, `website`, `phone`)
are **rejected outright**, confidence is **derived and cannot be authored**, a
verification record **expires**, and no image may exist without a
photographer, a source and a licence.

## 4. Existing routes

| count | shape |
|---:|---|
| 50 | `/europe/<country>` |
| 130 | `/europe/<country>/<region>` |
| 319 | `/europe/<country>/<region>/<destination>` |
| 255 | `/europe/.../place/<place>` |
| 137 | destination facets (`/things-to-do`, `/food`, …) |
| 50 | `/experiences/...` |
| 18 | `/journeys/...` · 17 `/interests` · 14 `/themes` · 13 `/events` · 13 `/fund` · 10 `/stories` · 10 `/discover` |
| ~20 | statics: `/plan`, `/map`, `/search`, `/my-europe`, `/manifesto`, `/method`, `/api-docs`, `/sources/freshness`, … |

The URL shapes the brief's §36 asks for already exist, including the facets.

## 5. Existing components

208 CSS classes covering every component the brief's §57 lists: header,
footer, search, cards for each entity type, map, filter panel, planner,
save button, badge, breadcrumb, form, section nav, thumb bar, sticky action,
trust tiers, staged wait. **One stylesheet, no duplicates**, enforced.

## 6. Existing APIs

Four public, read-only, key-free JSON documents built at deploy time:
`/api/atlas.json` (281 KB), `/api/search.json` (468 KB),
`/api/countries.json`, `/api/journeys.json`. Documented at `/api-docs`.
No write API exists.

## 7. Existing authentication

None, deliberately. **No incorporated entity means no data controller.**
My Europe is `localStorage` plus a copy-paste device transfer.

## 8. Existing integrations

**Zero third-party origins across 1,059 pages** — verified by check, enforced
by `default-src 'none'`. No analytics, no fonts CDN, no map tiles, no image
host, no error reporting.

## 9. Existing content

50 countries · 130 regions · 319 destinations · **255 places**, plus
experiences, journeys, themes and stories — the live counts against their
targets are in `docs/content-report.md`, which is regenerated every build and
owns those numbers.

Two of them are zero and stay stated as zero: **0 photographs** and **0 of 50
countries fact-checked**. Both are published on the site, not just here.

## 10. Existing design system

Brand Bible V1 applied: Atlantic green, limestone, terracotta, charcoal,
brass. Mark drawn once, inline. Eleven type steps, one spacing scale, two
shadows. Illustrations generated per slug with a motif from the place's own
tagging, and the same geometry renders the social cards.

## 11. Technical debt

1. **`tools/lib/pages.py` is 3,300 lines and 68 builders in one module.** It
   works and it is tested, but it is the one file where a new page type is
   harder to add than it should be. **This is the real debt.**
2. **~359 English string literals in the page builders.** `i18n.py` and the
   catalogues exist; the shell uses them; the page bodies do not. French
   coverage is 17 of 56 keys.
3. `/api/search.json` is **468 KB** and downloaded whole by the search page.
   Fine now; it is the number that decides when a search service is needed.
4. `planner.js` is 67 KB in one file — the largest single client asset.

Not debt: no dead code, no unused dependencies, no failing tests, no TODOs,
no duplicated shell, no inline styles.

## 12. Security concerns

None outstanding. CSP is `default-src 'none'` with no `'unsafe-inline'` in
any directive; HSTS, nosniff, Permissions-Policy, COOP and frame-ancestors
all ship and are checked against one source. No secrets exist to leak.

The one *historic* concern, fixed this month: the headers lived only in
`site/_headers`, which is Netlify syntax that **Vercel ignores** — so none of
them reached production while the repository looked correct.

## 13. Performance concerns

Genuinely fast: a destination page is 23 KB of HTML with no render-blocking
third-party anything. Two things to watch: the 468 KB search index, and
`planner.js` at 67 KB.

**No measured Core Web Vitals**, because there is no traffic and no
analytics. That is a real blind spot, not a claim of speed.

## 14. SEO problems

Mostly solved since the last audit: clean URLs, canonicals, breadcrumbs,
sitemap, robots, Open Graph, Twitter cards, **2,152 JSON-LD items** across
seven schema types, and 781 social cards.

Remaining: **no `hreflang`** (nothing to point at yet), and
`/api/search.json` is not the same thing as a semantic search engine.

## 15. UX problems

The honest list:

- **The map is a page, not an interface.** It draws 319 dots on an
  equirectangular projection with layers and a popup. It does not zoom, it
  has no coastlines, and it is not how anyone navigates the site. The brief's
  §5 is right that this is the biggest gap.
- ~~Discovery requires knowing what you want.~~ **Fixed** — Discover Mode.
- ~~No "why this?" on any recommendation.~~ **Fixed** — Discover Mode, the
  motion pages and now every itinerary leg.
- ~~The homepage is a good grid, not a story.~~ **Fixed.**
- ~~No seasonal front door.~~ **Fixed** — Europe in Motion.

## 16. Accessibility problems

WCAG 2.2 AA enforced in Chromium on every build in both colour schemes:
contrast, focus, target size, headings, landmarks, reduced motion, keyboard,
390px. The map has a full text alternative.

What is missing: **a screen-reader audit by a person**, and any access data
about the places themselves. `/accessibility` says both.

## 17. What should be preserved

**KEEP** — and these are not sentimental attachments, they are the assets:

- The **dataset and its schema**. Volatile fields refused, confidence
  derived, verification expiring, provenance per claim. A 2036 platform
  differentiated by *trust* cannot be built on a looser schema than this.
- The **knowledge graph and its reverse edges**.
- The **planner engine**: scoring, haversine, diversity pressure, honest
  refusal, and the edit layer.
- **28 static checks, 409 browser checks, 1,505 audit assertions.**
- The **trust architecture**: four labels, visible on the page.
- The **brand**, the mark, the illustration system, the social cards.
- The **security posture**: `default-src 'none'` and zero third parties.

## 18. What should be replaced

- **The map.** Point map → a real vector map with zoom, boundaries and
  content-linked layers. This is the single largest capability gap.
- **`pages.py` as one module** → one module per page family.
- **String literals in builders** → catalogue keys, so §37 is reachable.

## 19. What should be redesigned

- **The homepage**, as a progression rather than a grid (§50).
- **Discovery**, from a region list to a mood-and-constraint explorer (§7).
- **Recommendation surfaces**, to always carry a *why* (§7, §43).
- **Destination pages**, to adapt their order to stated preferences (§14).

## 20. Recommended architecture

**Recommendation: transform in place. Do not rewrite yet.**

The brief's §53 baseline — Next.js, Postgres, PostGIS, OpenSearch, Redis,
object storage — is the right destination and the wrong next step, and the
brief's own principles say why: *§1 do not destroy working functionality;
§54 do not introduce microservices to sound futuristic; §55 a beautiful
frontend on fake functionality is not acceptable; §62 do not build everything
at once.*

Concretely: of the ten signature features in §49, **eight need no database
and no server**. They need better interfaces over data that already exists
and is already validated. The two that do need a backend — European Memory
and the business ecosystem — are blocked on an incorporated entity, not on a
framework.

A rewrite now would spend the whole budget rebuilding what works and would
unblock nothing.

**The triggers that flip this**, unchanged: an entity exists (→ accounts,
Postgres, auth); somebody who is not a committer needs to write (→ CMS); the
search index passes ~2 MB (→ a search service); a real map provider is chosen
(→ tiles, and the first recurring bill).

---

# Part 2 — The transformation roadmap

Ordered by value per unit of risk. Everything in Phases A–C runs on the
current stack.

### Phase A — Geography becomes the interface

1. ~~**A real map.**~~ **BUILT.** Real coastlines and borders from Natural
   Earth, public domain, fetched and hashed by `scripts/map/fetch.py` and
   processed into `data/geo/` by `scripts/map/process.py` — both re-runnable,
   both checked for staleness in CI. Three levels of detail: the coarse one is
   inline so the map draws with JavaScript off, the finer continent file
   arrives when you zoom past 1.6×, and each country has its own. Fifty
   countries: 44 as shapes, and Monaco, Vatican City and four more at the
   widest zoom as ringed points, because at 1:50 million they have no polygon
   and inventing one would have been a lie about a measurement.

   The drill-down is Europe → country → region → destination and every rung is
   an `<a href>` before any script runs: `/europe/norway` →
   `/europe/norway/vestland` → `/europe/norway/vestland/bergen`. Country pages
   got the middle rung they never had — a map of the country with its regions
   and destinations on it, labels decluttered by content depth.

   **Cost: €0/month, and a check enforces it.** No provider, no key, no tile
   server, no request off this origin. `checks.py` fails the build on a page or
   script naming a commercial map host.

   What is *not* built, and why: region **boundaries**. That needs Eurostat
   NUTS, whose data is copyrighted with provisions a person has to accept, and
   the terms could not be read from the build environment. Documented and
   stopped rather than guessed — see
   `docs/data-licenses/eurostat-gisco-nuts.md`. Regions are drawn as their
   destinations grouped and named, which is exactly what we hold.

   The rebuild also found a projection bug a year old: the map claimed to
   correct for latitude and multiplied x by `cos(52°)/cos(52°)`, so Europe had
   been 60% too wide since the map was written. Nobody could see it, because
   313 dots on an empty rectangle are the right shape by definition.
2. **Map as navigation**, not a page: reachable from the masthead and the
   thumb bar. **PARTIAL** — the selection is now in the URL (`/map?c=norway`),
   so a drilled-in map can be sent to somebody; the navigation entry is not
   done.

### Phase B — Discovery becomes the product

3. ~~**Discover Mode**~~ **BUILT.** Pick moods and constraints at
   `/discover` and the continent narrows in the browser, with a **"why
   this"** on every card generated from the same terms `/method` publishes.

   The design decision the feature turns on: **never explain the constraint
   back.** The first version put the full reason on every card, and because
   the interests *are* the filter, all twelve began "carries every one of
   Mountains, History and Food" — individually true, collectively
   boilerplate, and boilerplate is what a reader learns to skip. Shared
   reasons are now hoisted once above the list and each card carries only
   what distinguishes it: the tags you did not ask for, whether it is peak
   or shoulder in your month, its discoverability terms, and whether we
   have actually written it up.
4. ~~**Europe in Motion**~~ **BUILT.** Twelve motions at `/europe-in`,
   each a **query** declared in `data/motions.json` and evaluated against
   every destination on every build.

   The trap in "dynamic discovery layer" is that the cheap version — a
   banner over a hand-picked list — looks identical to the real one on the
   day it ships and is wrong within a season. So: there is no field for
   naming a destination in a motion and the validator refuses one; a motion
   with no query terms is refused too, because it would match the whole
   Atlas; every page prints its query in words above the results; and a
   motion matching nothing fails the build rather than shipping an empty
   page with a good headline on it.

   Some of the queries are things a tag page cannot answer: which places
   have their *quieter* season in autumn, which lie above 63° north, which
   score 80+ for discoverability **and** are small enough to be villages.
5. ~~**Discoverability score**~~ **BUILT.** Five named terms, published at
   `/method#discoverability`, carried in `/api/atlas.json` per destination
   along with the terms that fired. Capitals sit at the floor; Theth,
   Xınalıq and Žabljak at the ceiling.

   It says plainly what it is not: **not a crowd measurement.** We hold no
   visitor numbers, search volume or occupancy data for anywhere in Europe,
   and inventing a proxy for one and calling it evidence is the thing this
   project exists not to do. It measures obscurity *within this Atlas* —
   a smaller claim, and one we can defend.
6. ~~**The homepage as a progression**~~ **BUILT.** Open → discover →
   wonder → understand → browse → plan → go, with each step **named on the
   page**, because a progression nobody can see is just an ordering. The
   wonder band changes ground and runs full-bleed so the rhythm is felt
   rather than merely intended, and the geography index — nine regions,
   seventeen tags — moves *after* the emotional part instead of opening the
   page with a filing cabinet.

   This puts the 2036 brief in direct conflict with §7 of the earlier UI
   specification, which fixes the order as regions → experiences →
   journeys. The later brief wins; the section audit records that it does
   and why.

**Phase B is complete.** Every UX finding in the audit above is now struck
through except the map, which is Phase A and waits on the licensing
decision.

### Phase C — The journey engine grows up

7. ~~**"What if?"**~~ **BUILT.** Five transforms over the itinerary you
   already have: two days longer, spend less, entirely by train, avoid the
   crowded places, more history and sacred places.

   What separates it from a row of preset buttons is that **it shows the
   consequence before applying it** — what you lose, what you gain, how the
   days move, what it costs against what you were paying. A button that
   silently rebuilds the itinerary is a slot machine: after three presses
   the reader has lost the plan they liked and cannot tell what any press
   cost them. "Keep what I have" is a real option.

   A sixth question is named and **refused**: *what if it rains?* We hold no
   weather data and no forecast for anywhere, and a rainy-day plan built
   from nothing would be a guess with a confident face on it.

   Two bugs worth recording. The crowd-avoiding swap first offered Siena →
   **Corte** — 200 km away and across the Ligurian Sea, because
   straight-line distance does not know about water; swaps stay in the same
   country now. And the threshold for "meaningfully less obvious" was set at
   +25 discoverability, which rejected Arezzo, Urbino and Civita di
   Bagnoregio at exactly +24 — the right answers for Tuscany — and reported
   that nothing would change.
8. ~~**Travel DNA**~~ **BUILT.** A travel *preference* model on
   `/my-europe`, computed from what this browser has saved and nothing else.

   The brief says it must never be presented as psychological truth, and
   that is harder than it sounds: a bar chart of percentages with a
   person's name over it reads as a personality test whatever the caption
   says. So it states its denominator — "computed from the 7 places you
   have saved" — refuses to appear at all under four saves, marks every
   adjusted row, resets completely, and uses the same `.scorebar` as the
   published Europe Experience Score rather than a more personal-looking
   visual.

   It also has to be *useful* or it should not exist: its top four
   interests hand straight to the planner, pre-selected.

**Phase C is complete.**

### Phase D — Blocked on the entity

9. Accounts, European Memory, business and tourism-board ecosystems,
   commerce, analytics. Specified in `docs/technical-foundation.md`.

### Phase E — Blocked on a decision or a bill

10. Semantic search (a model, or a vector index), narration (a model),
    photography (licensing and budget), languages beyond English
    (translation, and the string extraction in §11 first).

---

## The three decisions that are the owner's, not mine

1. ~~**Map provider and boundary licensing.**~~ **ANSWERED, 2026-09-08, by the
   owner: EuropeDoor does not pay for maps.** No commercial provider, no paid
   API, no per-load billing, no key that creates a recurring map cost, and no
   dependence on somebody else's public tile server. The map is self-hosted
   open data on our own CDN.

   Built on that decision: Natural Earth (public domain) fetched, hashed,
   committed and processed by `scripts/map/`; three levels of detail in
   `data/geo/`; the Europe → country → region → destination drill-down; layers
   that toggle; €0 of recurring cost. See `docs/map-architecture.md`.

   One licensing question stayed open rather than being guessed at: **Eurostat
   NUTS** would give real region *boundaries*, and its data is copyrighted with
   provisions that must be accepted by a person. The provisions could not be
   read from the build environment, so nothing was imported. The seven answers
   §24 of the map brief asks for are in
   `docs/data-licenses/eurostat-gisco-nuts.md`; the recommendation there is to
   ship without it, which is what happened.
2. **Whether to start the Next.js/Postgres migration before the entity
   exists.** I recommend no, for the reasons in §20 above. It is a strategic
   call and I have not started it.
3. **Photography budget.** Free stock covers the Eiffel Tower and will never
   cover Albarracín or Theth — which is precisely the product. See
   `docs/images.md`.

Decision 1 is answered and Phase A's map is built. Decisions 2 and 3 remain
the owner's; Phases B and C are complete.
