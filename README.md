# Europedoor

**One door into Europe** — europedoor.com

A discovery, planning and experience platform for the whole continent: an
atlas of every country, region and city; a journey planner that turns days,
budget and interests into a real itinerary; curated cross-border journeys;
local experiences; and a community fund.

Not a booking engine. The premise is that almost all of the interesting part
of a trip happens *before* the transaction, and almost nobody serves it well.

## What is here

| | |
|---|---|
| Countries | 50 |
| Travel regions | 121 |
| Cities | 244 |
| Experiences | 166 |
| Curated journeys | 8 |
| Themes | 13 |
| Stories | 8 |
| Fund projects | 12 (holding nothing — deliberately) |
| Generated pages | 524 |
| Runtime dependencies | 0 |

## Run it

```bash
python3 tools/build.py            # build site/
python3 tools/build.py check      # validate the data, render nothing
python3 tools/build.py stats      # what is in the dataset

python3 tools/checks.py           # 22 checks over the built HTML
node tools/browser-checks.js      # 103 checks in Chromium (needs playwright)
python3 tools/section-audit.py    # the brief, section by section, against the build

python3 -m http.server -d site 8000   # then open http://localhost:8000
```

Python 3.11 standard library only. No pip install, no npm install, no
database, no framework. Node and Playwright are needed for the browser
checks and for nothing else.

## Where to read next

Start with **[`docs/product-specification.md`](docs/product-specification.md)** —
the full specification: architecture, database schema, API, AI pipeline with
prompts, dashboards, monetisation, roadmap and risks.

| you are doing | read |
|---|---|
| **anything at all** | [`docs/product-specification.md`](docs/product-specification.md) |
| checking a claim about what is built | [`docs/section-audit.md`](docs/section-audit.md) — 35 sections, 199 machine-checked assertions |
| changing how the site is generated | [`docs/architecture.md`](docs/architecture.md) |
| adding or editing places | [`docs/data-model.md`](docs/data-model.md) |
| touching the scores | [`docs/scoring-method.md`](docs/scoring-method.md) |
| anything involving money | [`docs/europe-fund.md`](docs/europe-fund.md), [`docs/legal-position.md`](docs/legal-position.md) |
| naming things | [`docs/brand-lock.md`](docs/brand-lock.md) — the name is settled |
| planning | [`docs/roadmap.md`](docs/roadmap.md) |
| working in this repo as an agent | [`CLAUDE.md`](CLAUDE.md) |

## Status

Pre-launch and editorial. No entity, no payments, no accounts, no bookings,
no partners. `/how-it-works` is the honest public status board: what is
built, what is only designed, and what is deliberately blocked until the
legal work is done.

The dataset is a considered editorial first draft and has not been through a
source-by-source verification pass. `/sources` says so on the site. Check
official government travel advice before travelling anywhere.
