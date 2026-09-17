# The redesign doctrine

Written after the owner read several finished pages and said the same thing
about each: *"Keep the existing page → add premium CSS/components around it →
add a few visual elements → call it a redesign. That is not what you asked
for."*

He was right, and the reason it happened is worth more than the apology: **no
instrument here counted repetition.** Every gate was green on `/experiences`
when it was forty-two rows of one component, on the stories index when it was
nine three-column grids each holding one card, and on `/interests` when it
carried 728 abstract plates. The suite measures contrast, weight, overflow,
reach, coverage, provenance and correctness — a page can pass every one of
those and still be a CMS listing.

## The rule

> **Preserve the information. Reinterpret the presentation.**
>
> The existing content is authoritative. The existing visual structure is not.

EuropeDoor is an editorial geographic atlas, not a tourism dashboard. Content
determines composition. Maps are geographic instruments. Photography is
evidence of place. Typography creates hierarchy. Whitespace creates authority.
Data is visualised where it has geographic meaning. Navigation feels like
opening another part of the atlas. The aperture is a recurring language, not a
component that must appear everywhere.

**"Premium" is not a brief.** It is satisfied by rounded cards, gradients,
shadows, glassmorphism, big headings and hover animations, none of which this
product wants. The doctrine above replaces it.

## The order of work, and it is not negotiable

**1 · Inspect. Do not write CSS.**
Read the page builder and the *rendered* page. Write down: its purpose; every
piece of content and data already present; the hierarchy; the relationships
between pieces; the existing images; the maps; the statistics; the links; the
interactions; the navigation; the data loaders; the reusable components that
already exist. Do not redesign yet.

**2 · Produce a content architecture.** Answer, in writing:
* What is this page actually about?
* What is the single idea the visitor should understand?
* Which content deserves a monumental visual, a typographic statement, a map,
  photography, a data instrument, a sequence, a quiet editorial section?
* **Which content should not become a card?**

**3 · Compose from the content.**
Do not keep the existing section structure merely because it exists. Recompose
into a new page grammar.

| existing | do NOT | DO |
|---|---|---|
| 17 interests | 17 cards | an Interest Atlas |
| 13 themes | 13 cards | a thematic geography |
| 12 queries | 12 cards | twelve views of Europe |
| 130 quiet destinations | a grid | a counter-atlas |
| 319 destinations | a directory | geographic discovery |
| 50 countries | country cards | a living photographic atlas |
| 150 fixtures | event cards | a European calendar instrument |
| 9 essays | article cards | an editorial desk |
| a saved list | a dashboard | a personal atlas |
| a map with controls | a map with controls | the map as the instrument |

## Photography is structural

A page does not satisfy "use more photography" by putting three pictures under
the existing sections. A photograph carries the meaning of its section or it is
decoration:

| family | the photograph's job |
|---|---|
| country | geometry with the photograph clipped into the country |
| destination | a large arrival photograph with geographic context |
| journey | a landscape sequence following the route |
| story | an editorial opener |
| theme | the character of the theme, with geography saying where it exists |
| events | seasonal photography tied to the calendar |

The licence gate does not move for any of this: no image without a
photographer, a source and a licence, and nothing is acquired to make a
composition work.

## The two audits, per page

Written into the page's own `docs/*-redesign.md`, not remembered.

**CONTENT PRESERVATION**

- [ ] every important existing content item retained
- [ ] existing counts retained (and derived, never typed)
- [ ] existing links retained
- [ ] existing destinations retained
- [ ] existing relationships retained
- [ ] existing functionality retained
- [ ] existing data loaders reused
- [ ] existing map engine reused
- [ ] existing image and provenance system reused

**DESIGN TRANSFORMATION**

- [ ] the page has a new composition
- [ ] the existing card/grid structure was not merely reskinned
- [ ] the opening communicates the page's actual purpose
- [ ] the content hierarchy was reconsidered
- [ ] photography has an editorial role
- [ ] the map or the data has a meaningful visual role
- [ ] the sections have different visual rhythms
- [ ] the page does not read as a CMS listing
- [ ] the page has a memorable signature moment

## And one of them is measured

A checklist is a promise and this repository's own history says a promise
nobody can check is a slogan. `tools/monotony.js` measures the share of a
page's own height taken by **the single most repeated component**, where a
repeated component is three or more siblings agreeing on their class attribute
**and on their children's class attributes** — because six differently
composed `.band` sections share a class and are not a listing, while thirteen
theme rows share their inner shape and are.

Measured across all 47 rendered families the day it was written:

| page | share | component |
|---|---:|---|
| /countries | 63% | 9 × `macroband` |
| /experiences/‹category› | 62% | 48 × `invite` |
| /europe-in/‹motion› | 54% | 38 × `row` |
| /for-businesses | 51% | 8 × `row` |
| /discover/‹macro› | 49% | 9 × `card` |
| /europe/…/‹facet› | 46% | 6 × `row` |
| /fund | 45% | 12 × `row` |
| /search | 42% | 7 × `row` |
| /experiences/‹cat›/‹sub› | 37% | 25 × `invite` |
| /themes | 37% | 13 × `row themerow` |
| /europe-in | 36% | 12 × `row motionrow` |
| … | | |
| /plan | 15% | 6 × `rrow` |

**A long list is sometimes the right answer** — an index whose subject is a
set of 130 places is a list, and this instrument is not an argument against
lists. What it catches is a page that is a list **and nothing else**, which is
why the second line of each row prints the next two components: a page at 60%
with two other bands is a list with a frame round it, and a page at 60% with
nothing else is the fault.

`--check` fails above the ceiling, set at the current worst so it cannot get
worse silently and comes down in a diff as each page is recomposed. A ceiling
set at where the work should end would be red for a fortnight, and a gate that
is red for a fortnight is a gate people stop running.

Three things it deliberately does not measure, and each is a judgement a
person has to make: whether the opening says what the page is for, whether the
photography carries meaning, and whether there is a signature moment.
