# The UI/UX specification, answered

A 37-section design brief arrived after the 99-section product specification.
This document records what was built from it, what was already there, and the
seven things it asks for that this product will not do — with the reason for
each, because "we skipped it" and "we decided against it" are different
answers and only one of them is defensible a year later.

Every claim below is machine-checked. `tools/ux-audit.py` carries an
assertion per section against the real build, writes the verdict table to
`docs/ux-audit.md`, and CI fails when one stops being true. This file is the
argument; that one is the evidence.

## The name, first

The brief's navigation and page headers read **EUROPE ATLAS**. The name is
**EuropeDoor, at europedoor.com**, locked by an instruction that predates
every document that has arrived since. See `docs/brand-lock.md`;
`tools/checks.py` enforces it on all 987 pages. Everything else in §2 is
taken as written.

## Built from this brief

| § | what | where |
|---|---|---|
| 2, 27 | **Mobile bottom navigation** — Home, Explore, Map, Plan, Me | `render.bottom_nav`, phone only, five items, 44px targets |
| 16 | **Destination section tabs**, scrolling sideways on a phone | `pages.sectionnav` — only sections the page actually has |
| 27 | **"Add to my journey"**, not "Book now" | `pages.stickycta` — save and plan, the two things a reader can really do |
| 30 | **The staged wait** — five real steps, ticked as each finishes | `planner.js: stage()` |
| 32 | **A refusal instead of a fabricated result** | `planner.js: whyUnreliable()` |
| 33 | **The map as a list** — the accessible alternative | `pages.maplist`, 319 places with coordinates |
| 29 | **Save state, everywhere it appears** | one place saved relabels both its buttons, with `aria-pressed` |

### §32 is the sharpest line in the brief

> Do not fabricate a result just to avoid an error.

That is a description of what this planner did. It scores every city in the
Atlas, so there is always a best one — which means a request it cannot really
answer got a route anyway, presented with exactly the confidence of a good
one. Four conditions now refuse:

- nothing in the Atlas fits the constraints at all
- the stops fill under 60% of the days asked for
- half or more of the stated interests are not delivered by the route
- the cost exceeds a **stated** budget by more than 80%

Each names the control that would fix it, and offers the rejected plan inside
a collapsed block marked as rejected — never a dead end.

The word **stated** is doing real work there. The first version refused
*"three weeks by train through the alps in winter, luxury"* at €4,686 against
€2,500 — a budget that sentence never mentioned and that we had filled in as
a default. Refusing your own assumption and telling the reader they asked for
something impossible is worse than the fabrication it was meant to replace.
A browser check now holds that line.

## Already built when the brief arrived

§5 map with interest layers · §6 experience category cards · §7 featured
journeys · §8 Hidden Europe as a contrasting band · §9 the ask box in the
hero · §10 the planner form, all ten supported inputs · §12 route, cost and
day-by-day · §13 day cards · §15 country page with regions, destinations,
experiences and journeys · §17 the discovery-first content order · §21 map
with filters · §22–23 search with its interpretation shown back · §24 My
Europe with collections · §26 the content half of the admin figures, computed
at build time into `docs/content-report.md` · §31 empty states · §36 crumbs
and onward links on every page.

## What this product will not do, and why

Seven of the brief's requirements collide with positions that are settled,
published on the site, and enforced by checks. Taking the architecture and
dropping these is the same treatment the 36- and 99-section specifications
got.

### 1. Photography (§1, §4, §6, §8, §18)

> Photography leads discovery.

There are **no photographs on this site at all**, and `checks.py` fails the
build on an `<img>` tag. Every illustration is a deterministic SVG generated
from the place's own slug: unique per place, owned outright, no licence to
expire, no stock library, no chance of publishing somebody's holiday
photograph by accident.

This is a licensing decision rather than an aesthetic one, and it is the
cheapest version of a problem that gets expensive later. The brief's
*structure* — full-bleed hero, large category cards, hover that lifts and
reveals an arrow, visual contrast between the popular and the hidden — is all
built. It is built on generated plates.

The day there is a company, a budget and a rights position, the plates become
`<picture>` elements and nothing else in the design has to move. That is why
the hero and card shapes were built to the brief's proportions.

### 2. Ratings and review scores (§18, §19, §20)

> ★★★★★ · 4.8

There are no reviews and no ratings anywhere, and there is no field that
could carry one. §27 of the product specification defers reviews until there
are accounts and anti-fraud, and says so itself. A star rating with no
reviewers behind it is a number we invented, and it would sit on the page
looking exactly like one we measured.

The Europe Experience Score is published instead, at `/method`, with its
formula — and it says what a place is *for*, never how good it is.

### 3. Booking (§19, §20)

> [ VIEW / BOOK EXPERIENCE ] · [ Book ]

Nothing on this site can be booked, no operating company exists, and there is
no payment surface. A booking button that cannot book is the single most
dishonest control a travel site can ship. The brief's own §5 — "booking is
present but never dominates" — resolves cleanly here: it is absent, and the
reason is on `/how-it-works`.

The action in its place is **Add to my journey**, which the brief itself
proposes in §27 and which is better than a book button even once booking
exists.

**A referral is not a booking, and the Stay layer is the line between them.**
One destination — Chamonix — now carries an accommodation referral: an
outbound link to a provider's own search, with the provider named on the page
as the party that holds the rooms, the prices and the availability and takes
the payment. Nothing about the paragraph above changes. There is still no
booking button, no basket, no price, no availability state and no payment
surface, and `checks.py` refuses an outbound link to any host that is not a
declared provider in `data/stay.json`.

What is refused inside that layer is worth writing down, because the brief
for it asked for all four: a **hotel photograph** (the register holds no
licensed photograph and an illustration drawn from a hash would be a picture
of nowhere standing in for a room), a **rating** (`★` may not appear on any
page on this site, and we hold no reviews for anywhere in Europe), a
**nightly price** (`price` is refused on every record and a price we cannot
keep current is worse than none) and an **availability state** (we hold no
inventory). None of the four is refused because a card is a bad idea. They
are refused because under a link-only affiliate mechanism — which is the only
mechanism available without an approved partner account, which needs the
entity — there is no honest source for any of them. `stay.inventory()` is the
seam that would fill a card and it returns nothing, and a page that gets
nothing draws the editorial reading instead of an empty frame.

### 4. Opening hours (§18)

> OPENING HOURS

The validator **rejects** `hours`, `price`, `website` and `phone` on a place.
These move faster than we can check them, and a wrong opening time is worse
than no opening time: it sends somebody across a city. Each place page says
we do not hold them and points at the operator.

### 5. The business dashboard's numbers (§25)

> Profile views 2,481 · Website clicks 312 · Leads 48 · Bookings 17

There is no traffic, no authentication and nothing booked. Those figures
would have to be invented, and a dashboard of invented numbers is the thing
that makes every other number on a product untrustworthy. The dashboard's
*layout* is specified in the product specification; it ships when it has
something true to display.

### 6. The admin dashboard's user metrics (§26)

> Users 12,482 · AI plans 482

Same reason. The **content** half of that panel is real and is computed on
every build into `docs/content-report.md` — countries, destinations, places,
journeys, stories, and the verification queue including "expired data", which
is now a live figure rather than a mockup. The traffic half waits for
traffic.

### 7. Playfair Display + Inter from a font CDN (§3)

The Content-Security-Policy is `default-src 'none'` with `font-src 'self'`,
and no page loads anything from a third-party origin. A webfont CDN would
mean giving every reader's IP address to a third party on every page view,
which contradicts `/privacy` — where the claim is that nothing is loaded from
another origin and here is how to verify it.

The brief's *typographic intent* is honoured: a display face for authority
and a separate interface face, one scale, editorial measure. They are system
stacks. Self-hosted licensed faces are a drop-in change to two CSS custom
properties on the day someone buys them.

## §34, §35, §37 — Figma

The brief's last three sections describe a Figma file, six prototype flows
and a ten-screen clickable prototype. There is no Figma file, because there
is a built site: all ten of §37's screens exist as real pages, all six of
§35's flows are clickable on the live build, and the design system in §28 is
CSS classes rather than components in a library.

A prototype exists to answer "would this work?" before building it. That
question has been answered by building it, and a Figma file made now would be
a second source of truth to keep in step with the first. If a designer wants
to work in Figma, the built site is the reference to import — not the other
way round.
