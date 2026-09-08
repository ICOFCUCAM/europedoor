# Content model

## The shape

```
macro region  9      shared coast, mountain range or history — not alphabet
  country     50     capital, currency, timezone, languages, blocs, seasons,
    │                cost band, festivals, practical notes, verification
    region    130    a travel region, not an administrative one
      destination 319   coordinates, interests, nights, summary, highlights
        place     192   what it is, how long to give it, season, access
        experience 197  kind, category, what it actually involves
```

Crossing the hierarchy, which is what most travel databases lack:

```
destination ──N:M── journey        17 curated routes, legs with nights
destination ──N:M── story           9 articles, linked both ways
destination ──N:M── theme          13 cross-border themes
destination ──N:M── interest       16 things people travel for
experience  ──N:1── provider        who runs it, and its verification level
country     ──1:N── fact_check      per claim, with source kind and expiry
anything    ──1:1── image           photographer, source, licence, focal point
```

The reverse edges are built at load time, so every destination knows which
journeys pass through it, which stories mention it and which themes include
it. That is why the "in the rest of the site" sections are real rather than
tag-generated.

## The four labels

Every claim on the site is one of these, and the difference is **visible on
the page**, not recorded in a policy. Published at `/manifesto`.

| label | means | where it stands |
|---|---|---|
| **Verified** | checked by a person against a source answerable for the fact, with a date and an expiry | **0 of 50 countries.** Published as such at `/sources/freshness` |
| **Editorial** | written by someone who knows the place, reviewed as a diff | everything not marked otherwise |
| **Computed** | derived by a published formula from data we hold | scores, distances, costs, seasonal fit. Formula at `/method` |
| **Community** | contributed by a reader or a business, attributed, never affecting ranking | **none.** Needs accounts, moderation and attribution |

The five verification statuses the brief names — unverified, machine
reviewed, editor reviewed, business verified, officially sourced — are the
schema's `VERIFICATION_STATUS` and constrain the `checked.status` field.

## Provenance, per claim

The unit is the **claim**, not the page: *this fact, against this body, of
this kind*. A source URL alone is the weaker half — it says a page was
consulted, not which assertion it supports.

```json
"checked": {
  "on": "2026-09-01",
  "by": "A. Editor",
  "status": "officially-sourced",
  "sources": [
    {"what": "Currency and blocs", "where": "Norges Bank",
     "kind": "official", "url": "https://..."}
  ]
}
```

`kind` is one of official / operator / municipal / press / editorial, and the
distinction is **whether the source is answerable for the fact**: a border
authority is answerable for its own entry rules in a way a newspaper
reporting them is not.

Confidence is **derived** from source kind and the age of the check.
Authoring it is a validation error.

A record **expires** after `REVIEW_DAYS` and reads as *due for review* again.
Without that, the first country anybody verified would carry the badge for
ever — which is how a date quietly turns back into a tick.

## What is refused

- **Volatile fields.** `hours`, `price`, `website`, `phone` on a place are
  rejected by the validator. They move faster than we check them.
- **Entry, visa and safety information.** Refused across the product, with
  the reason published, and readers pointed at their own government.
- **Ranking fields.** No `rank`, `boost`, `featured` or `sponsored` on a
  place. Sponsorship attaches to a provider and reaches directory surfaces
  only.
- **Seeded business listings.** A directory of businesses that have not
  claimed their entry and cannot be verified is exactly what this refuses to
  publish.
- **Bulk AI-generated facts.** Never, without review.
