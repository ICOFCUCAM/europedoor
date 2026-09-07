# Roadmap

Kept current. The reasoning is in
[`product-specification.md`](product-specification.md) Part 3.

## Done

* Europe Atlas: 9 macro regions, 50 countries, 130 travel regions, 319
  cities, 197 experiences
* Depth tier A complete: Norway 25, France 28, Italy 25, Spain 27, Greece 25
* Fact freshness: every country states whether it has been verified, and
  `/sources/freshness` is the public board
* Journey Planner, browser-side, over the whole Atlas
* 8 curated cross-border journeys, 13 themes, 8 stories
* Map of every city, no third-party tiles
* Experience listings, ten kinds, with the verification model published
* Europe Fund register, 12 projects, holding nothing
* Europe Experience Score with the formula published at `/method`
* My Europe (browser-local saves), Events, `/beyond-the-obvious`
* Search: the whole index filtered in the browser, with accent folding
* A sentence box on the planner: rules, not a model, showing what it read
  and naming what it cannot take account of
* Month pages for the European year, answering where to go as well as what is on
* Journey overlays on the map; My Europe saves journeys, themes and stories
* Reverse edges: every city knows its journeys, themes and stories
* An honest status page separating built / designed / blocked
* 23 static checks, 102 browser checks and a 204-assertion audit of the
  brief's 35 sections, all in CI

## Next, in order

1. **Actually verify the facts.** The mechanism is built and the board reads
   0 of 50. Currency, blocs, entry and cost bands first, against official
   sources, one country at a time.
2. **Twenty more stories.** Organic traffic comes from these, not from the
   Atlas.
3. **Accessibility notes** per city and experience — the planner already
   admits it cannot take account of them, which is the argument for adding them.
4. **Depth tier B**: bring the next ten countries to 20+ cities.

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
| 1–2 | Foundation | Entity; trademark clearance; privacy notice; the depth-tier-A editorial plan |
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
