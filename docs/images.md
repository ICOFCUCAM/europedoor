# Photographs: the architecture, and the fact that there are none

The Brand Bible calls photography one of the most important parts of
EuropeDoor, and it is right. This file is the honest position: the pipeline
that serves a photograph is **built and enforced**, and the number of
photographs currently licensed is **zero**.

Those are two different statements, and most projects blur them. The
distinction matters because the shape of an image pipeline decides what a
licence audit costs two years from now, when there are eight thousand files
and nobody remembers where the third thousand came from.

## The four rules, all enforced

**1. No image without provenance.** A row in `data/images.json` must carry
`file`, `alt`, `photographer`, `source` (an https URL you can open) and
`licence` (from a closed list). `tools/lib/data.py` refuses a row that does
not, and `tools/checks.py` refuses a published page that references a file
with no row. There is no `unknown` and no default, so "we will fill that in
later" is not reachable from here.

An unlicensed photograph on a public page is the most expensive mistake a
travel site can make, and it is always made by accident — by an `<img>`
somebody added in a hurry. That is the specific thing being refused.

**2. Self-hosted, never hotlinked.** Every file is served from our own
origin. The Content-Security-Policy is `default-src 'none'` with `img-src
'self' data:`, so a hotlinked provider URL does not render at all. The policy
enforces the decision rather than a convention doing it. Hotlinking also
hands the provider every reader's IP address on every page view, which
contradicts `/privacy`.

**3. One eager image per page.** The hero is `loading="eager"` with
`fetchpriority="high"`; everything else is lazy and is never fetched until
somebody scrolls. Page weight is therefore **one question per page** rather
than a total, and a card grid of forty places costs nothing until it is
looked at. A check fails a page with two eager images.

**4. Every image carries its own dimensions.** `width` and `height` on the
tag, always, so nothing shifts when the file arrives.

## What is served

`<picture>` with AVIF, then WebP, then JPEG. Five widths — 480, 800, 1260,
1800, 2400 — as a fixed ladder, so filenames are predictable and can be
generated ahead of time.

Each row carries a **focal point** as `[x, y]` percentages, applied as
`object-position`. This is not a nicety: a 21:9 hero crop of a portrait
photograph, centred, takes the sky and loses the subject. It is the
commonest way a responsive hero goes wrong.

Credits are in the markup on every image, shown on hover and focus on a
desktop and always visible on a phone. Always-visible credits on 988 pages is
a design nobody ships; credits that live only in a data file are a licence
risk. This is the compromise, and a screen reader reads them either way.

## Adding one

1. Put the file through the width ladder as
   `assets/img/<name>-<width>.{avif,webp,jpg}`.
2. Add a row keyed by what it illustrates —
   `city:norway/fjord-norway/bergen`, `journey:<slug>`, `story:<slug>`,
   `place:<country>/<region>/<city>/<place>`.
3. `python3 tools/build.py check`, then build and commit.

Nothing else changes. Callers never branch on whether a photograph exists:
they ask `picture()` for one and get the best thing available. That is what
makes the library adoptable **one photograph at a time** rather than as a
migration.

## Until then: the plates

Every surface without a photograph gets a generated plate — a small landscape
built from the SHA-256 of the thing's own slug, with the motif taken from
what the place actually is. See `docs/brand.md`.

The plate is the honest empty state, **not the policy**. The policy used to
be "no photographs at all", enforced by refusing every `<img>`, and that was
the right rule while there was no pipeline: it made the licensing question
impossible to get wrong. It is the wrong rule now, because it bans the
correct behaviour along with the incorrect one. The replacement is stricter
in the way that matters and permissive in the way that does not.

## The acquisition problem, stated plainly

The Bible asks for three categories, and the third is the one that matters:

| category | what | how hard |
|---|---|---|
| **Iconic Europe** | Eiffel Tower, the Alps, Venice, Santorini | easy — free-licence stock is saturated with these |
| **Human Europe** | markets, families, pilgrims, artists, chefs, craftspeople | harder, and needs release paperwork for recognisable faces |
| **Hidden Europe** | small villages, remote landscapes, local festivals, mountain roads, quiet coastlines | **hard, and it is the whole product** |

319 destinations need a hero each. Free-licence stock will cover the iconic
tier and will not cover Albarracín, Theth or Bitola — which are precisely the
places this site exists to show. Stock for those either does not exist or is
the same four images everyone else is using.

That points at commissioning and at contributor licensing, both of which need
the entity that does not exist yet. It is a real constraint and it is not
solved by trying harder at stock.

**No photograph is downloadable from this environment in any case:** the
sandbox proxy does not reach an image provider, and it should not — acquiring
images is a decision with a licence attached, not a build step.
