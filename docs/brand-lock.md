# The name is settled

**Product name: EuropeDoor. Domain: europedoor.com.**

This is a decision, not a proposal, and it is recorded here because it is the
kind of decision a later document quietly overturns. Strategy notes, agency
decks, blueprints and specifications that arrive with an alternative name —
Europe Atlas, Europia, Via Europa, Europe Unbound, or anything else — are
being *inspired by*, not *applied to*, this repository.

**The rule: no incoming document changes the name.** If a document is
otherwise good, take its architecture, its revenue model and its roadmap, and
drop its branding section on the floor.

## The one change that has been made, and who made it

The casing moved from **EuropeDoor** to **EuropeDoor** in the Brand Bible V1,
which came from the owner rather than from an incoming strategy document.
That distinction is the whole point of this file: it is not a rename and it
did not arrive from outside. The name, the domain and the metaphor are
unchanged.

Written as one word in every context. **Never `Europe Door`** — the space
turns a product name into a generic phrase, and a generic phrase is
unregistrable and unownable. Title case in prose (`EuropeDoor`), uppercase in
strong visual applications (`EUROPEDOOR`), lowercase in the wordmark, which
is a drawing rather than a spelling.

## What that means in the code

| thing | value | where it lives |
|---|---|---|
| Product name | EuropeDoor | `SITE_NAME` in `tools/lib/render.py` |
| Domain | europedoor.com | canonical + sitemap, `tools/lib/render.py`, `tools/build.py` |
| Tagline | Open the door to Europe. | `SITE_TAGLINE` in `tools/lib/render.py` |
| Wordmark | lowercase `europedoor` with the door glyph | `.wordmark` in `assets/css/europedoor.css` |
| Favicon | the same door, drawn once | `assets/door.svg` |
| The AI's name | EuropeDoor Guide | `docs/brand.md` |

`tools/checks.py` fails the build if the canonical domain is not
europedoor.com, if `SITE_NAME` is not exactly `EuropeDoor`, if any page
writes `Europe Door` with a space, or if a page ships a competing product
name in its title.

## What "Atlas" is

The Atlas is **pillar one of EuropeDoor** — the country/region/city
structure. It is a component name, like the Journey Planner or the Europe
Fund. It is never used as the name of the product, and never on its own in a
title tag.

## Trademark: open, and the answer is probably "not exclusively"

This is now the more important half of this file, because the honest position
has moved from *unknown* to *known and unfavourable in part*.

**EUROPEDOOR is already in use as a business name in the doors and
building-materials trade, including in South Africa, and the term appears in
European garage-door product contexts.** We should not assume exclusivity, we
should not announce the brand publicly, and we should not spend money on
registrable assets — signage, merchandise, packaging, a filed logo — until
clearance is done.

What that does *not* mean is that the name is dead. Trademark protection is
per class and per jurisdiction, and a door manufacturer and a travel
discovery platform are not in the same classes:

| Nice class | covers | our interest |
|---|---|---|
| 6 / 19 / 20 | metal and non-metal doors, door frames, fittings | **theirs**, and not contested |
| 39 | travel arrangement, transport booking, tours | ours, primary |
| 41 | publishing, entertainment, cultural information | ours, primary |
| 42 | software as a service, platform hosting | ours, primary |
| 35 | advertising, business directory services | ours, needed for the directory |

Coexistence across unrelated classes is ordinary. The risks that need a
lawyer, not a search engine, are: whether any existing mark is registered
broadly enough to reach 39/41/42; whether an EUTM application would face
opposition; and whether the goods are close enough for confusion in any
market where we would actually operate.

### The pre-launch clearance task

Formal, before any public announcement or any registrable spend:

1. **Knock-out search** — EUIPO eSearch plus (EUTM), WIPO Global Brand
   Database, UKIPO, and the national registers for the first operating
   markets, in classes 35, 39, 41, 42.
2. **Common-law and trade-name search** — companies registers and active use,
   including the South African door business and any European garage-door
   use, to establish what is actually in commerce rather than merely filed.
3. **Domain and handle audit** — europedoor.com is held; the matching
   handles on the platforms we would use are not audited.
4. **Counsel's opinion** — freedom to operate in the target classes and
   markets, and whether to file an EUTM, a Madrid designation, or neither
   yet.
5. **A fallback shortlist**, prepared but not adopted, so that a bad opinion
   is a decision rather than a crisis.

Until step 4 returns, EuropeDoor is the **working brand**: used throughout
the product, in the repository and in the domain, and not announced,
advertised, filed or printed. That distinction is what lets the build carry
on without betting the company on it.

Owning the domain is not owning the mark. It never was.
