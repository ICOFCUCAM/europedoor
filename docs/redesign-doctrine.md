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

And the rule that keeps the first one from eating itself, added by the owner
after reading the first three pages recomposed under it:

> **Do not optimise for visual consistency at the expense of editorial
> difference.**

The reasoning is exact and it is a warning about *this* doctrine rather than
about the old pages: *"Claude could successfully learn 'Don't make cards' …
and then make every page into the same kind of large editorial bands. That
would simply replace card monotony with band monotony."* `tools/monotony.js`
would not catch that — it measures repetition WITHIN a page, and a site where
every page is four full-bleed editorial bands scores beautifully on all 47 of
them. The instrument for this one is `tools/contact-sheet.js`, which puts
twelve families in one field of view, and it is the instrument that found the
fault it was written for: *eleven of twelve families open with a kicker, a
serif h1, a lede and a large arched map in the same position.*

So: **do not make the site visually uniform; make the design system coherent
while allowing each page type its own visual argument.** One shell, one
stylesheet and eleven primitives are the coherence. The argument is what
differs.

**"Premium" is not a brief.** It is satisfied by rounded cards, gradients,
shadows, glassmorphism, big headings and hover animations, none of which this
product wants. The doctrine above replaces it.

## The sequence, and it is not negotiable

**Inspect → Understand → Recompose → Preserve → Audit.** The three steps below
are the first three; the last two are not optional extras, they are where every
failure this repository has recorded actually lands. **Preserve** is the step
that keeps a recomposition from being a rewrite — the data loaders, the map
engine, the register, the runtime hooks and every derived count stay exactly
what they were, and /map is the reference for it (22 of map.js's 22 hooks
asserted intact). **Audit** is the step that makes the claim checkable: both
tables below, filled in, in the page's own `docs/*-redesign.md`, plus the
eleven-point pass under them.

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

## The family of page grammars

One table, because *do not make the site visually uniform* needs somewhere to
say what each page's own argument IS. A grammar is not a layout: /themes and
/map are the reference implementations of the METHOD and neither is a template
to copy.

| family | its visual argument |
|---|---|
| country | geographic identity — a living photographic atlas |
| destination | arrival, and a sense of place |
| theme | an argument that crosses geography |
| journey | movement, and a sequence |
| experience | an invitation, and immersion |
| story | editorial narrative |
| events | a calendar, and seasonality |
| map | a geographic instrument |
| interests | preference becoming geography |
| europe-in | questions producing different Europes |
| beyond-the-obvious | a counter-atlas, and alternative routes |
| my-europe | a personal atlas |
| countries | a continental index, and a geographic system |

Two of these are already recorded as REFUSALS rather than as briefs, and the
refusal is part of the grammar: `docs/signature-moments.md` refuses geography
on an experience category (*48 dots scattered over Europe would say food is
everywhere, which is true and is not an insight*) and on the interest pages
(three identical maps of Europe for the three largest tags). A grammar says
what the page argues; it does not license a drawing the data cannot support.

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

## And eleven things to prove, not to claim

The two checklists above are what the page had to KEEP and what it had to
BECOME. This is the pass that runs after it is built, and every line of it is
a measurement something in this repository can take:

1. **content preservation** — every count, link, destination, relationship and
   loader still there, and every figure derived (`checks.py`)
2. **visual hierarchy** — the head's role, the band sequence, what leads
   (`tools/composition.js`)
3. **monotony** — the largest repeated component, with the next two beside it
   (`tools/monotony.js --check`)
4. **photography** — how much of the first screen is a picture, and whether
   each one carries its section's meaning (`tools/opening.js`, then look)
5. **geographic meaning** — a drawing says something the prose does not, and
   the same frame where two drawings are being compared (`c_same_frame`)
6. **responsive behaviour** — 1280, 834, 390 and 320; 834 is the width that
   finds a two-column layout collapsing a column just above its breakpoint
7. **accessibility** — contrast on the painted pixels, focus visible, every
   link visible with focus on it, 24px targets, no clipped word
8. **provenance** — the register, the licence gate, the credit, the crop box;
   nothing acquired to make a composition work
9. **interaction** — every runtime hook the page's application binds to still
   present (all 22 of map.js's, asserted)
10. **browser behaviour** — the full suite, alone, on the built site: a page
    that renders differently from what the markup says is the only fault class
    reading cannot find
11. **regression** — the invariant register, and screenshots before and after
    wherever something was DELETED, because nothing here comes out on a scan's
    word alone

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
| /countries | ~~63%~~ **25%** | ~~9 × `macroband`~~ 3 × `macroband mac-up` |
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
worse silently and comes down in a diff as each page is recomposed. **63 → 55
on the first row of that table**: /countries' nine identical macro bands
became three rhythms derived from each region's own shape in kilometres, 4
portrait / 3 upright / 2 panoramic, and its largest repeated composition is
25% with the next two at 20 and 8. The reasoning is in
`docs/countries-redesign.md` Part 8, including the three alternative
measurements that were taken and refused and the finding that `glyph_view`'s
own comment stated the doctrine's second rule as a design decision. A ceiling
set at where the work should end would be red for a fortnight, and a gate that
is red for a fortnight is a gate people stop running.

Three things it deliberately does not measure, and each is a judgement a
person has to make: whether the opening says what the page is for, whether the
photography carries meaning, and whether there is a signature moment.

## The two reference implementations

`/themes` and `/map`, and **the method rather than the layout.**

/themes is the content deciding the composition: a theme holds a photograph, a
geography, a summary, eight places and a REACH, and the reach — how many of
the nine corners of Europe it crosses — chooses which of three band scales it
takes. It falls 6 / 6 / 1, and the one tight band is Renaissance Europe,
which is exactly the knot the page's own closing sentence is about. The layout
argues what the sentence says instead of captioning it. 37% → 18%.

/map is the opposite fault and the same method: monotony does not list it at
all, because everything that made it an instrument — the legend, seventeen
filters, four layers, the journey overlay, the distance origin and a
319-destination text twin — was inside two closed `<details>`. Nothing was
added. What changed is that the page's own content is on the page, with all 22
of map.js's hooks asserted intact, which is the **Preserve** step made
checkable.

Copying either layout onto a third page would be band monotony, which is the
rule at the top of this file. What transfers is: read the data, find the
measurement already in it, let that measurement choose the composition, and
prove the result.

## Where each page's audit lives, and what it measured

Written down rather than remembered, which is the whole point of the two
checklists being in the repository. Every figure is `tools/monotony.js` at
1280, and the second column is the diagnostic the report exists to print: a
page at 30% with two other components is a list with a frame round it, and a
page at 50% with nothing else is the fault.

| page | largest repeated | next two | audit |
|---|---:|---|---|
| /countries | 25% | 20%, 8% | `docs/countries-redesign.md` Part 8 |
| /europe-in/‹motion› | 31% | 8% | `docs/europe-in-redesign.md` §10 |
| /experiences/‹category› | 36% | 20% | `docs/experiences-redesign.md` Part 8 |
| /experiences/‹cat›/‹sub› | 16% | 15%, 6% | the same pass |
| /europe-in | 36% | 12%, 2% | `docs/europe-in-redesign.md` Part 9 |
| /interests | 33% | 16% | `docs/interests-redesign.md` Part 8 |
| /journeys | 33% | 5%, 4% | `docs/journeys-redesign.md` Part 8 |
| /themes | 20% | 16%, 15% | `docs/themes-redesign.md` |
| /experiences | 19% | 5%, 3% | `docs/experiences-redesign.md` Part 7 |
| /events | 18% | 12%, 1% | `docs/events-redesign.md` Part 7 |
| /beyond-the-obvious | 18% | 9%, 8% | `docs/beyond-redesign.md` Part 8 |
| /stories | 16% | 11% | `docs/stories-redesign.md` Part 10 |
| /plan | 11% | 7%, 5% | `docs/plan-redesign.md` Part 8 |
| /my-europe | 10% | 5% | `docs/my-europe-redesign.md` Part 8 |
| /map | not listed | — | `docs/map-redesign.md` |

**/map is absent from the instrument on purpose and that was its fault**, not
its defence: everything that made it an instrument was inside two closed
`<details>`, and a box a reader cannot scroll to is outside the measurement.

**The three that were open, and where they stand.** Two are closed in the same session that named them; the third is named rather than glossed:

| page | share | and | the recorded position |
|---|---:|---|---|
| ~~/europe-in/‹motion›~~ | ~~54%~~ **31%** | 30 × `row`, then 8% | **closed** — grouped by the clause each result satisfied, `docs/europe-in-redesign.md` §10 |
| ~~/experiences/‹category›~~ | ~~51%~~ **36%** | 30 × `invite`, then 20% | **closed** — grouped by what an invitation costs, `docs/experiences-redesign.md` Part 8 |
| /how-it-works | 52% | 3 × `band`, then 20% and 12% | a prose page, and three bands with two other components is a composition |

And five more the instrument lists that nobody has redesigned:
/for-businesses 51%, a macro region 48%, a facet page 46%, /fund 45%,
/search 42%.

**Two of the rebuilt pages sit at 33% and neither is defended.** /journeys is
seventeen journeys and /interests is seventeen tags, so the list is the
subject — and both have a second component in the single digits or low teens,
which is the shape this instrument reads as *a list and little else*. The
honest next question for /journeys is whether its three derived paces should
set three rhythms the way /countries' nine regions now do. Recorded as a
trigger, not ticked.
