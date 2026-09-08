# EuropeDoor

**Open the door to Europe** — europedoor.com

Discover Europe. Understand its places. Build your journey. Experience it.

A European discovery, cultural knowledge and journey-planning platform: an
atlas of every country, travel region and destination; a planner that turns
days, budget and interests into a real costed itinerary; curated cross-border
journeys; local experiences; stories; and a community fund that holds nothing.

Not a booking engine. The premise is that almost all of the interesting part
of a trip happens *before* the transaction, and almost nobody serves it well.

> **The name is a working brand.** EUROPEDOOR is already in use in the doors
> and building-materials trade. Trademark clearance is a formal pre-launch
> task and nothing here is announced, filed or printed. See
> [`docs/brand-lock.md`](docs/brand-lock.md).

## Run it

```bash
python3 tools/build.py                  # 988 pages, ~4 seconds
python3 -m http.server -d site 8000
```

**There is nothing to install.** Python 3.11 standard library, zero runtime
dependencies, no package manager, no database, no server, no secrets. That is
a deliberate property — see [`docs/architecture.md`](docs/architecture.md).

## The gates

All seven pass in CI, and all seven must pass before anything is called done.

```bash
python3 tools/build.py check              validate the dataset
python3 tools/build.py                    988 pages + 4 APIs + sitemap
python3 tools/checks.py                   25 static checks, ~88,000 assertions
node tools/browser-checks.js              389 checks in Chromium, incl. WCAG 2.2 AA
python3 tools/section-audit.py --check    100 spec sections, 1,253 assertions
python3 tools/ux-audit.py --check         43 UI/UX + brand sections, 218 assertions
python3 tools/content-report.py --write   the dataset against its own targets
```

The browser suite needs `npm install --no-save playwright@1.49.0`. It earns
its place repeatedly: a 47px mobile overflow on every city page, two colour
tokens under the WCAG line, a places layer that could never be switched on, a
€700 fortnight routed through Switzerland, a 2,500 km final leg presented as
an itinerary, and two sticky bars overlapping on a notched phone. None of
those was findable by reading the code.

## What is here

| | | | |
|---|---:|---|---:|
| Countries | 50 | Journeys | 17 |
| Travel regions | 130 | Themes | 13 |
| Destinations | 319 | Stories | 9 |
| Places | 192 | Photographs | **0** |
| Experiences | 197 | Countries fact-checked | **0 of 50** |

The last two are published as zeros on the site itself, at `/sources/freshness`
and in [`docs/images.md`](docs/images.md). An empty number stated plainly is
worth more than a number nobody can check.

## Documentation

| | |
|---|---|
| [`docs/audit-2026-09.md`](docs/audit-2026-09.md) | **start here** — the repository audit and the one open architectural decision |
| [`docs/roadmap.md`](docs/roadmap.md) | what is next, and what every blocked item is blocked on |
| [`docs/development.md`](docs/development.md) | how to work on it, and the rules that catch people out |
| [`docs/architecture.md`](docs/architecture.md) | the four rules the build depends on |
| [`docs/product.md`](docs/product.md) | what the product is and what it deliberately does not do |
| [`docs/content-model.md`](docs/content-model.md) · [`docs/data-model.md`](docs/data-model.md) · [`docs/database.md`](docs/database.md) | the shape of the data, field by field, and why there is no database |
| [`docs/api.md`](docs/api.md) · [`docs/ai.md`](docs/ai.md) | the four public endpoints; the retrieval-first pipeline that runs without a model |
| [`docs/security.md`](docs/security.md) · [`docs/deployment.md`](docs/deployment.md) | the policy, and the production gap it closed |
| [`docs/brand.md`](docs/brand.md) · [`docs/images.md`](docs/images.md) | the identity as built; the photograph pipeline and the empty library |
| [`docs/technical-foundation.md`](docs/technical-foundation.md) | the PostGIS/Next.js destination — **and its trigger, which has not fired** |
| [`docs/section-audit.md`](docs/section-audit.md) · [`docs/ux-audit.md`](docs/ux-audit.md) · [`docs/content-report.md`](docs/content-report.md) | generated, never hand-edited, and CI fails when they go stale |

## The one thing to understand before changing anything

`site/` is generated and committed. It is deleted on every build. Editing a
page there is work that disappears with no warning and no failing check — if a
page needs to say something new, it says it in `tools/lib/pages.py` or in
`data/`.
