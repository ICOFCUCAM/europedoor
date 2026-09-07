# Roadmap

Kept current. The reasoning is in
[`product-specification.md`](product-specification.md) Part 3.

## Done

* Europe Atlas: 9 macro regions, 50 countries, 121 travel regions, 244
  cities, 166 experiences
* Journey Planner, browser-side, over the whole Atlas
* 8 curated cross-border journeys, 9 themes, 8 stories
* Map of every city, no third-party tiles
* Experience listings, ten kinds, with the verification model published
* Europe Fund register, 12 projects, holding nothing
* Europe Experience Score with the formula published at `/method`
* My Europe (browser-local saves), Events, `/beyond-the-obvious`
* An honest status page separating built / designed / blocked
* 21 static checks and 71 browser checks, in CI

## Next, in order

1. **Search.** Client-side index over the 244 cities. The most-missed
   feature and about half a day's work.
2. **Depth tier A** — Norway, France, Italy, Spain, Greece to 25+ cities
   each, 40+ experiences, 5 stories apiece.
3. **Fact verification pass**, with `facts_checked_on` per country and city,
   surfaced on the page. Anything unverified says so.
4. **Twenty more stories.** Organic traffic comes from these, not from the
   Atlas.
5. **Accessibility notes** per city and experience.

## Blocked, and by what

| blocked | unblocked by |
|---|---|
| Any payment | entity + named payee on every card surface + PSP contract |
| Fund contributions | the above, plus a written position per collecting country |
| Accounts | data controller + lawful basis + published privacy notice |
| Naming an operating company | that company existing |
| Photography | a licence audit, or a commissioned shoot we own |
| Packages (journeys sold with transport) | Package Travel Directive advice |

## Twelve months

| months | focus | ships |
|---|---|---|
| 1–2 | Foundation | Entity; trademark clearance; privacy notice; search; the depth-tier-A editorial plan |
| 3–4 | Depth | Tier A to full depth; verification pass with dates; 10 more stories |
| 5–6 | Reach | i18n mechanism plus French and German for tier A; events feed; structured data |
| 7–8 | Intelligence | AI planner with the citation check; `POST /api/plan`; accounts and saved-list sync |
| 9–10 | Commercial | Operator dashboard; verification queue; directory subscriptions; disclosed affiliate links |
| 11–12 | Launch | PR on the Fund and the responsible-travel position; tourism boards; a bookings pilot in one country |

## Explicitly not doing

* A mobile app before the web product has users
* Social features beyond published itineraries
* Display advertising, at any stage
* Importing a large third-party place database — the written dataset is the
  moat, and an import is how it stops being one
