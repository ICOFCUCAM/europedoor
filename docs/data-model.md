# The data model

Every page is generated from `data/`. This is the field list. The
authoritative version is `tools/lib/data.py`, which fails the build rather
than publishing something malformed.

## Identity

A city's id is `"<country-slug>/<region-slug>/<city-slug>"` — for example
`norway/fjord-norway/bergen`. Journeys, themes and stories reference cities
by that id and the validator checks every one.

## `data/taxonomy.json`

| key | what |
|---|---|
| `macros[]` | the nine regions of Europe: `slug`, `name`, `blurb`, `countries[]` |
| `interests[]` | 17 tags: `slug`, `name`, `icon` |
| `budgets[]` | `low` / `moderate` / `high`, each with a note |
| `months` | `jan`…`dec`, and `month_names` |
| `blocs` | `eu`, `schengen`, `eurozone`, `eea`, `cta` |
| `experience_kinds` | 10 kinds: walk, table, workshop, water, museum, sacred, ride, stage, wild, cellar |

Every country must be listed under exactly one macro region. Listing one
twice, or not at all, fails the build.

## `data/countries/<slug>.json`

```jsonc
{
  "code": "no",                    // ISO 3166-1 alpha-2
  "slug": "norway",                // must equal the filename
  "name": "Norway",
  "official": "Kingdom of Norway", // optional
  "macro": "nordic",
  "capital": "Oslo",
  "currency": "NOK — Norwegian krone",
  "languages": ["Norwegian (Bokmål and Nynorsk)", "Sámi languages"],
  "blocs": ["schengen", "eea"],
  "advisory": {                    // optional; presence removes the country
    "level": "avoid",              //   from the planner index entirely
    "note": "…"
  },
  "tagline": "…",                  // one line, used on cards
  "summary": "…",                  // 3–5 sentences
  "interests": ["mountains", "coast", …],
  "budget": "high",
  "daily_eur": [115, 260],         // [frugal, generous] per person per day
  "season": {
    "peak": ["jun","jul","aug"],
    "shoulder": ["may","sep"],
    "note": "…"                    // when to come, and why not otherwise
  },
  "getting_around": "…",
  "food": ["…", "…"],
  "festivals": [{ "name": "…", "month": "may", "where": "…" }],
  "know": ["…"],                   // practical, non-obvious, non-generic
  "regions": [ … ]
}
```

### A region

```jsonc
{
  "slug": "fjord-norway",
  "name": "Fjord Norway",
  "summary": "…",
  "interests": ["mountains", "coast", …],
  "cities": [ … ]
}
```

Regions are **editorial travel regions, not administrative units.** Fjord
Norway is not a county and is exactly how people think about going there.
Administrative geography can be added later as a separate field without
changing any URL.

### A city

```jsonc
{
  "slug": "bergen",
  "name": "Bergen",
  "lat": 60.39, "lon": 5.32,       // approximate, validated 34–72 N, −26–50 E
  "summary": "…",                  // one or two sentences
  "interests": ["coast", "history", …],
  "nights": [2, 3],                // [min, max], each 1–7; the planner uses it
  "quiet": true,                   // optional; collects into /beyond-the-obvious
  "highlights": ["…", "…"],        // at least two
  "experiences": [ … ]             // optional
}
```

### An experience

```jsonc
{
  "slug": "bergen-seven-mountains-walk",
  "name": "Fløyen to Ulriken ridge walk",
  "kind": "walk",                  // from taxonomy.experience_kinds
  "band": "low",                   // low | moderate | high
  "summary": "…"
}
```

An experience with no provider attached is editorial: we think you should do
it, nobody pays us, nothing is sold. That must remain the majority of them.

## `data/journeys.json`

```jsonc
{ "slug": "…", "name": "…", "strapline": "…", "summary": "…",
  "days": 20, "budget": "moderate", "interests": [...], "months": [...],
  "legs": [ { "city": "<city id>", "nights": 3, "why": "…" } ] }
```

**Invariant, enforced:** `sum(legs[].nights) == days - 1`. The last day is
the journey home. A journey that fails this does not load — the error is
invisible in prose and obvious to a customer.

## `data/themes.json`

```jsonc
{ "slug": "…", "name": "…", "strapline": "…", "summary": "…",
  "interests": [...],
  "stops": [ { "city": "<city id>", "why": "…" } ] }   // at least four
```

A theme is not an itinerary and the page says so: stops are not in travelling
order.

## `data/stories.json`

```jsonc
{ "slug": "…", "title": "…", "section": "…", "standfirst": "…",
  "reading": "8 min",
  "places": ["<city id>", …],       // linked both ways
  "body": ["paragraph", …] }        // at least four
```

## `data/fund.json`

```jsonc
{ "slug": "…", "name": "…", "theme": "…", "country": "<country slug>",
  "partner": "…", "summary": "…", "need": "…",
  "status": "listed" | "in-progress" | "complete" }
```

**`amount`, `raised`, `goal` and `target` are rejected by the validator.**
See [`europe-fund.md`](europe-fund.md).

## `data/providers.json`

```jsonc
{ "tiers": [ { "name": "…", "who": "…", "badge": "…", "means": "…" } ],
  "providers": [ { "slug": "…", "name": "…", "kind": "…", "city": "…",
                   "country": "<country slug>",
                   "tier": "applied" | "reviewed" | "verified",
                   "summary": "…", "checks": ["…"] } ] }
```

## What is deliberately absent

* **No score fields.** The Experience Score is recomputed from tags on every
  build. A stored score and its explanation drift apart; a computed one
  cannot.
* **No rank, boost, featured or sponsored field** on any place. Sponsorship
  can only ever attach to a provider, and only affects directory surfaces.
* **No image paths.** Illustrations are generated from the slug.
* **No prices**, only bands. A price we cannot keep current is worse than no
  price.

## What is missing and should be added

* `facts_checked_on` / `facts_checked_by` per country and city. The whole
  dataset is currently unverified editorial writing and `/sources` says so;
  this field is how that stops being true one row at a time.
* Administrative region codes (NUTS), for later data joins.
* Accessibility notes per city and experience — the most common thing a real
  traveller needs and the most common thing a travel site omits.
