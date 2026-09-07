# How Europedoor is built

981 static HTML files, generated from 63 JSON files by 2,000 lines of
dependency-free Python. No database, no framework, no runtime. This is a
deliberate position and the trigger for changing it is written down in
[`product-specification.md`](product-specification.md) §2.2.

## The shape

```
data/            the whole product, as validated JSON
  taxonomy.json  macro regions, interests, budgets, months, blocs, kinds
  countries/     50 files; each holds its regions, cities and experiences
  journeys.json  themes.json  stories.json  fund.json  providers.json

tools/
  build.py       the only entry point that writes anything
  checks.py      21 checks over the built HTML
  browser-checks.js   71 checks in a real browser
  lib/
    data.py      load + validate. Refuses malformed data, loudly.
    urls.py      one place that knows what a URL looks like
    render.py    ONE page shell. Every page goes through it.
    pages.py     one function per page family
    score.py     the Experience Score, and its published methodology

assets/          one stylesheet, three small scripts, one favicon
site/            generated. Deleted and rewritten on every build.
```

## Four rules the rest depends on

**1. One page shell.** `render.page()` is the only function that emits
`<html>`. A masthead or footer that exists in two places diverges within a
month, so it exists in one. `checks.py` fails the build if any page ships an
inline `<style>`, which is the usual first step in that divergence.

**2. One URL module.** `urls.py` knows that a city lives at
`/atlas/<macro>/<country>/<region>/<city>`. That is a strong claim about how
people look for places and it will eventually be revised. When it is, it is
revised in one file.

**3. The validator refuses rather than warns.** `data.py` collects every
problem and then raises with all of them, so one run fixes one round of
mistakes. It rejects: a city in a region that does not exist, a journey whose
nights do not sum to its days, a coordinate outside Europe, a night range
outside 1–7, an unknown interest, a duplicate slug, a fund project carrying
an amount, and a country belonging to no macro region or to two.

**4. `site/` is deleted on every build.** There is no page in it that a human
edited and there must never be one — a hand edit would vanish without a
warning. If a page needs to say something new, it says it in `pages.py` or in
`data/`.

## The generated illustrations

There are no photographs. Every illustration is a deterministic SVG derived
from the SHA-256 of the place's own slug: hue, saturation, seven vertical
bars at pseudo-random positions and opacities, and one of three overlay
marks. Same slug, same picture, forever; different slugs, different pictures.

This is not primarily an aesthetic decision. It means no licence to expire,
no attribution to get wrong, no CDN bill, no broken image, and no risk of
publishing somebody's holiday photograph. `checks.py` fails on any `<img>`
tag.

When photography arrives it will be commissioned and owned, and it will
arrive as an additive field on the city record rather than a replacement for
this.

## The planner

`assets/js/planner.js`, 260 lines, no dependencies, running against
`/api/atlas.json`.

```
score(city)  = (0.30 + 0.70 × interest match)
             × season factor (peak 1.18, shoulder 1.00, off 0.74)
             × style fit
             × depth (1 + 0.035 per listed experience, capped at 3)
             × affordability

next stop    = argmax over unvisited cities of
               score × 1/(1 + (km/420)^1.55) × country repeat penalty × jitter

affordable   = 1, unless the city's daily rate exceeds
               (budget × 0.78 / days), in which case it is damped in
               proportion. Cheaper than the ceiling is never penalised —
               under budget is a good outcome.

nights       = clamp(round(mean(city.nights)) + pace, city.nights)
cost         = Σ nights × daily rate(country, style)
             + Σ transport(km) between stops
             + 12% buffer
```

Two properties worth stating because they are promises, not implementation
details:

* **Nothing is sent anywhere.** The whole plan is computed in the browser.
  A planner that phones home before there is an account system is collecting
  travel intentions it has no basis to hold.
* **Money cannot influence a stop.** There is no field in `atlas.json` that
  could carry a paid boost, and no code path that reads one.

Countries under a travel advisory are removed from `atlas.json` at build
time, not filtered in the UI, so no client bug can route into one.
`checks.py` verifies this against the built file.

## Running it

```
python3 tools/build.py            build site/
python3 tools/build.py check      validate data, render nothing
python3 tools/build.py stats      what is in the dataset
python3 tools/checks.py           23 checks, ~36,000 things examined
node tools/browser-checks.js      320 checks in Chromium, incl. accessibility
python3 tools/section-audit.py    the 99 spec sections, 1,080 assertions
python3 tools/content-report.py   dataset coverage against the spec's targets
```

CI runs all four, and fails if the committed `site/` differs from a fresh
build — a stale `site/` means the checks validated output nobody will serve.

## Serving it

Any static host. `vercel.json` sets `cleanUrls`, so `/atlas` serves
`site/atlas/index.html`. The browser checks serve the directory with the same
semantics, because a link to `/atlas` that only works as `/atlas/index.html`
is a bug that never appears locally.
