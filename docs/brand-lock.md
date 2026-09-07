# The name is settled

**Product name: Europedoor. Domain: europedoor.com.**

This is a decision, not a proposal, and it is recorded here because it is the
kind of decision a later document quietly overturns. Strategy notes, agency
decks, blueprints and specifications that arrive with an alternative name —
Europe Atlas, Europia, Via Europa, Europe Unbound, or anything else — are
being *inspired by*, not *applied to*, this repository.

**The rule: no incoming document changes the name.** If a document is
otherwise good, take its architecture, its revenue model and its roadmap, and
drop its branding section on the floor.

## What that means in the code

| thing | value | where it lives |
|---|---|---|
| Product name | Europedoor | `SITE_NAME` in `tools/lib/render.py` |
| Domain | europedoor.com | canonical + sitemap, `tools/lib/render.py`, `tools/build.py` |
| Tagline | One door into Europe | `SITE_TAGLINE` in `tools/lib/render.py` |
| Wordmark | lowercase `europedoor` with the door glyph | `.wordmark` in `assets/css/europedoor.css` |
| Favicon | the same door, drawn once | `assets/door.svg` |

`tools/checks.py` fails the build if the canonical domain is not
europedoor.com, or if a page ships a competing product name in its title.

## What "Atlas" is

The Atlas is **pillar one of Europedoor** — the country/region/city
structure. It is a component name, like the Journey Planner or the Europe
Fund. It is never used as the name of the product, and never on its own in a
title tag.

## Still open, and genuinely open

Trademark clearance for "Europedoor" in the relevant classes (Nice 39
travel arrangement, 41 entertainment/publishing, 42 software) has **not**
been done, and neither has a search for confusable marks in the EU register.
That is a lawyer's job and it is on the pre-launch checklist in
`docs/roadmap.md`. Owning the domain is not owning the mark.
