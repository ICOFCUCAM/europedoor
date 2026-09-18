# The First-Class Audit

> **The brief:** transform EuropeDoor from a website that is well made into
> the door through which somebody enters Europe. Desire first, orientation
> second, discovery third, planning fourth, action fifth.

**Nothing was changed to produce this document.** Twenty-seven surfaces were
rendered in Chromium at 1280×900 and 390×844, looked at as two contact
sheets, and then measured. No CSS, no template and no data was touched —
an audit that fixes as it goes ends up rationalising what is already there.

Labels: **MEASURED** · **OBSERVED** · **INFERRED** · **BLOCKED**

---

## Part 0 — What could not be done, said first

The mandate names eight benchmark sites and asks that they be opened and
studied: Visit Finland, Visit Norway, Switzerland Tourism, Austria Tourism,
I feel Slovenia, Visit Sweden, Italia.it, Condé Nast Traveler.

**BLOCKED.** The sandbox egress proxy refuses every one of them —
`EGRESS_BLOCKED` on `visitnorway.com`, `myswitzerland.com`,
`visitfinland.com` and the rest, from the same proxy that already answers
403 for pexels.com and unsplash.com. Web *search* is reachable; the sites
themselves are not.

So the benchmark half of this audit is **second-hand and is labelled as
such**. What the search results support, and nothing more:

| | evidenced |
|---|---|
| Visit Norway | hero is a **video** of landscape; bold sans headline; a call to action per trip type; seasonal imagery and curated guides below |
| Visit Finland | **full-bleed photography** and video thumbnails; campaign-led; user-generated content |
| I feel Slovenia | a communications platform ("MY WAY") built on **personalisation** — the user's own choice of experience as the organising idea |

That is thin, and it is deliberately not dressed up. Three things follow
from it that are safe to act on, because they are structural rather than
stylistic:

1. **Every one of them opens on a full-bleed moving or photographic image
   of the place.** Not a map, not a form, not a headline on paper.
2. **Every one of them organises by the visitor's intent**, not by the
   administrative shape of the country.
3. **None of them leads with data.**

**This repository must not copy their look and could not if it wanted to**
— it holds zero licensed photographs. What it holds instead is the one
thing none of the eight has: a continent drawn on its own conformal conic
through its own aperture. The strategy that follows from the benchmark is
therefore *not* "become Visit Norway". It is: **spend the drawing where
they spend the photograph, and stop spending type where they spend
either.**

---

## Part 1 — The three findings

### Finding 1 — On a phone, half the product's entry points open with no picture in them

**MEASURED.** Viewport 390×844. The masthead is 89px and the thumb bar 56,
so 699px of the screen is content. The figure below is the number of those
699 pixels that any figure, drawing or photograph actually occupies.

| surface | first visual at | picture on the first screen |
|---|---:|---:|
| map | 418 | 56% |
| country | 415 | 52% |
| month | 433 | 50% |
| my-europe | 478 | 48% |
| macro | 459 | 48% |
| fund project | 426 | 42% |
| motion | 515 | 39% |
| stories | 536 | 37% |
| homepage | 233 | 37% |
| quiet | 566 | 37% |
| category | 230 | 36% |
| europe-in | 549 | 36% |
| interests | 549 | 36% |
| subcategory | 259 | 36% |
| themes | 541 | 36% |
| story | 520 | 35% |
| events | 490 | 34% |
| place | 506 | 34% |
| journey | 599 | 32% |
| 404 | 358 | 32% |
| countries | 488 | 32% |
| interest | 390 | 32% |
| journeys | 488 | 32% |
| region | 462 | 30% |
| destination | 443 | 28% |
| theme | 159 | 27% |
| discover | 649 | 26% |
| experiences | none on the page | **0%** |
| plan | none on the page | **0%** |
| search | none on the page | **0%** |

**RE-MEASURED, AND THE TABLE ABOVE IS THE CURRENT ONE.** It read seven of
twenty-three surfaces with no picture on the first screen at all and five
more under a fifth of it — twelve of twenty-three, just over half,
effectively type to the fold. It is now **three of thirty with none, and none
under a fifth**: `/plan` and `/search` are instruments whose opening is the
control they exist to be, and `/experiences` carries a recorded refusal of a
map that survives re-checking. The median share is 35.6%, against 24% when
this was first measured.

**AND THE TABLE GREW BY THREE BECAUSE THE INSTRUMENT HAD NEVER REACHED THEM.**
`tools/lib/families.js` is the one list `opening.js` and `contact-sheet.js`
both read, and it carried twenty-seven rendered families. Enumerated against
the built site by page depth, three templates were missing — the month page
under `/events` (12 pages), the sub-category page under an experience
category (39) and a fund project page (12), 63 pages in all. In every one of
the three the family's INDEX was on the list and the page it indexes was not,
which is the shape of the omission: the index is the surface somebody names.
A family's index and its leaf are different templates with different heads and
different jobs, which is exactly why this list already carried an `interest`
beside `interests` and a `theme` beside `themes`.

Two of the three measured well on the first run — the month page is the
second-strongest opening on the site at 50%, and the sub-category page 36%.
**The third, a fund project page, had no figure anywhere on it at any
width**: the register whose entire argument is that each entry is a real
thing in a real place with a named local partner was the last DISCOVER
surface opening on type alone. Nothing had ever photographed or measured it.
*An instrument that cannot reach a family cannot find a defect in it.*

It is answered. What the register holds about a place is its COUNTRY and no
finer position, so that is what is drawn and nothing else: the project page
opens on its own country at the country's own size, and the index on the nine
lit together. **0% → 42%**, first visual at 426. And the index took the reach
head rather than a fifth arch — a sea panel with nine countries lit is the
glyph `/experiences/food` already draws, in a doorway, and this audit has
already removed two openings for being a continent with a different number of
marks on it.

The original reading, kept because the measurement is the record:

**A CORRECTION.** The first version of this table said twenty-one of
twenty-two surfaces "show a visitor nothing but type", and that was wrong.
The instrument that produced it recorded whether a figure *intersected* the
first screen and then the document position of the first one, and the
document position was read as though it were the answer — so a region page
whose map begins at 563 and runs to the fold was counted with an experiences
index whose art begins at 807 and is not on the screen at all. The
directional finding survives and the number does not: it is twelve of
twenty-three, not twenty-one of twenty-two, and the right measure is how
many pixels of the first screen are a picture rather than where the first
one starts.

The three that mattered most, and what each of them is now:

- **The destination page was 0%**, on 319 pages, and it is the richest
  family in the product. Its first 795 pixels were a kicker, a 38px name, a
  lede, a metadata line, three interest chips and three numbered reasons to
  go. The view moved into the opening and the record moved after it: 443,
  28%.
- **The experience category page had no picture anywhere on it, at any
  scroll position, at any width.** It draws its own reach now — the
  countries its invitations are spread across, filled — at 230, 36%.
- **`/discover` reached its first drawing at 1,702** under a filter row, and
  the drawing did not exist below 1024px at all. It leads with the continent
  now: 649, 26%.

And the destination page's order is not the fault. Name, what the place is,
why go, then where it is, is exactly the sequence the brief asks for — 
desire before orientation. The fault is that with no photograph in the
register, desire is being carried entirely by type, and the type is set at
the same size as every other family's.

### Finding 2 — The site has one composition, rendered 1,033 times

**MEASURED.** h1 size and position, at both widths:

| | 390 | 1280 |
|---|---|---|
| h1 font-size on 17 of 22 surfaces | **38px** | **60px** |
| h1 top on the index/overture families | 187–233 | 150–312 |
| surfaces whose opening differs at all | homepage; the five instruments | same |

`docs/design-direction-audit.md` measured this a while ago and it recorded
the right half of it: eleven of twelve families place an identically-sized
h1 at an identical vertical position, and the entire art-directional
difference between a magazine story and a country encyclopedia is one 11px
kicker changing hue.

What the contact sheet adds is the half that measurement could not see:
**above the fold, twenty-two pages are interchangeable**, and the one
element that *is* on every one of them — the cobalt masthead — is the most
repeated object in the product. One shell, one stylesheet and eleven
primitives are an engineering achievement. They are not a design.

**AND THE OTHER HALF OF THE CLAIM HAD NEVER BEEN MEASURED AT ALL.** The
finding is about a COMPOSITION and everything above is about an h1: the
sentence says the page is the same page, and the evidence only ever covered
the first 250 pixels of it. `tools/composition.js` reads the rest — the
ordered sequence of band shapes under the head, in the vocabulary the eleven
primitives actually emit (rows, cards, figure, facts, list, note, a band of
prose), with consecutive repeats collapsed because three `rows` bands and one
are the same composition holding different amounts of content.

**29 distinct body shapes over 47 families.** The clusters, largest first:

| families | shape |
|---:|---|
| 8 | `HEAD rows` — experiences, journeys, stories, themes, interests, search, for businesses, tourism boards |
| 5 | `HEAD list` — category, subcategory, about, accessibility, help |
| 5 | `HEAD note list` — plan, contact, privacy, terms, cookies |
| 3 | `HEAD rows note` — interest, europe-in, facet |
| 2 | `HEAD figure rows note` — motion, quiet |
| 2 | `HEAD figure note` — map, my-europe |
| 1 each | the remaining 22 |

The eight in the largest cluster are the families whose subject genuinely IS
a list, plus two prose pages that are also lists. That is a shape doing its
job, not a shape nobody chose. What the number says is that the claim as
written — one composition, 1,033 times — is no longer true of the body, and
the heads have gone with it:

| | at 1280 |
|---|---|
| h1 sizes in use | 30 (instrument), 60 (index), 76 (overture) |
| h1 top | 136–745 |
| head height | 82–1018 |
| share of the head's own width its content reaches | 60%–144% |

Against the original reading of 60px at 150–312 on seventeen of twenty-two.
The four heads at 60% are overtures with nothing beside the name, which is
the role working as written; the four past 100% are carrying a drawing wider
than the type. **This is a reported measurement and not a gate**, for the
same reason `opening.js` is not one: a threshold on "distinct shapes" is a
number to satisfy by shuffling bands, and the fault it exists to find is a
page that is dull.

### Finding 3 — The homepage decays monotonically after the hero

**MEASURED**, at 1440 wide, full page 4,934px:

| band | height | share | dominant element |
|---|---:|---:|---|
| hero | 310 | 6% | **the drawn continent** |
| the search strip | 90 | 2% | an input |
| four doors | 290 | 6% | four flat teal panels |
| three journeys | 520 | 11% | three 160px route maps |
| stories | 270 | 5% | one 120px map, two text blocks |
| closing statement | 200 | 4% | three numerals |
| footer + legal | ~700 | 14% | type |

**OBSERVED.** The hero is the best thing in the product and no competitor
can reproduce it. Everything under it is smaller than the thing above it,
in sequence, to the bottom of the page. There is no second visual moment,
no change of scale, no change of ground, and no editorial proposition
between the continent and the form — the transition from *a drawing of
Europe at 736px* to *a bare text input on white* happens in 40 pixels.

The four doors are the sharpest case. `pages.home()` already records why
they carry no drawing (four crops of a continent-wide tag are four
pictures of Europe again) and why they carry no plate (placeholder art
doing a picture's job). Both are right. What is left, with the register
empty, is **four identical flat panels of atlas water**, 130px tall,
reading as unloaded images — on the second screen of the front door.

---

## Part 2 — Twenty-eight surfaces

Nine questions each, per the mandate: primary question · feeling ·
five-second understanding · primary action · secondary action · visual ·
textual · interactive · hidden until needed. **VERDICT** is against the
mandate, not against the tests.

### 1 · Homepage `/`
- **Q** Is Europe here, and can this thing help me find my part of it?
- **Feel** Scale, then invitation. Awe that resolves into a first step.
- **5s** This is a whole continent, editorially held, and there is a way in.
- **1°** Open a door (an interest, a journey, the planner).
- **2°** Search.
- **Visual** The continent. **Textual** One proposition sentence. **Interactive** The planner. **Hidden** Counts, method, the data note.
- **VERDICT** Hero excellent. Everything below it undersized and unled. The four doors read as holes. No editorial proposition anywhere. **REDESIGN THE BODY.**

### 2 · Countries `/countries/`
- **Q** How is this continent divided, and which part is mine?
- **Feel** Nine coherent Europes, not fifty administrative units.
- **5s** Europe comes in nine macro regions and I can pick one.
- **1°** Enter a macro region. **2°** Open the map.
- **Visual** Nine region shapes, compared. **Textual** What each region *is*. **Interactive** Region choice. **Hidden** Country counts per region.
- **VERDICT** The nine maps are the right idea and are drawn at 358×239 on a phone, below the fold, in a right-hand column that makes them decorations. **PROMOTE THE GEOGRAPHY.**

### 3 · Country detail `/europe/austria/`
- **Q** What is this country actually like, and where in it should I go?
- **Feel** A country with a character, not an encyclopaedia entry.
- **5s** Austria is alpine and imperial, has N regions, and here are the places.
- **1°** Open a region or a destination. **2°** Add to a journey.
- **Visual** The country's own shape and its destinations. **Textual** The one-paragraph character. **Interactive** Destination choice. **Hidden** Practicalities, getting around, when to go.
- **VERDICT** Composition is correct and the portrait map is good. Opens on type; the country portrait is at y=184 desktop, y=591 phone. **RAISE THE PORTRAIT; GIVE THE CHARACTER PARAGRAPH REAL TYPOGRAPHIC WEIGHT.**

### 4 · Regions (index, inside a country) and 5 · Region detail
- **Q** What holds these places together?
- **Feel** A coherent stretch of ground with a reason.
- **5s** Tyrol is the alpine heart, and here are its destinations.
- **1°** Open a destination. **2°** Back up to the country.
- **VERDICT** Best-composed family on the site: the region map draws its own destinations and the reason is in the head. Still type-first on a phone. **PHONE OPENING ONLY.**

### 6 · Destination detail `/europe/france/alps-and-east/chamonix/`
- **Q** Should I go here, and what would I do?
- **Feel** *Yes, this place.* Specific, physical, particular.
- **5s** What this place is, what the ground is like, how long to stay.
- **1°** Save it / add it to a journey. **2°** Read what to do.
- **Visual** The place. **Textual** Why it is worth it. **Interactive** Save, plan, stay. **Hidden** Facts, sources, structured data.
- **VERDICT** The richest page in the product and the one most punished by having no photograph. The measured-relief paragraph in the Stay layer is the best writing on the site and is six screens down. **THE DEEP REDESIGN.**

### 7 · Experiences `/experiences/` and 8 · Experience category
- **Q** What do people actually *do* in Europe?
- **Feel** Curiosity. Verbs, not nouns.
- **5s** 197 experiences in ten kinds, and none of them is an advert.
- **1°** Open a kind. **2°** Read the honesty note about listings.
- **VERDICT** The category page is the **worst-composed page in the product**: two columns of undifferentiated text rows, no visual element anywhere on the page at any width, at any scroll position. It is a database printout. **REBUILD.**

### 9 · Journeys and 10 · Journey detail
- **Q** Could I actually do a trip like this?
- **Feel** Possibility, and the pull of a line across a map.
- **5s** Seventeen routes that cross borders on purpose; this one is N days.
- **1°** Open the journey / build your own. **2°** Open the planner.
- **VERDICT** `/journeys` was rebuilt around the ordered sequence and is right. The journey page's route map is at y=541 on a phone — the one drawing that *is* the subject, below the fold. **RAISE IT.**

### 11 · Stories and 12 · Story detail
- **Q** Is there anything here worth reading?
- **Feel** A magazine, not a blog. Authority and voice.
- **5s** Nine essays, each anchored to real places.
- **1°** Read one. **2°** Follow a place into the Atlas.
- **VERDICT** The index was rebuilt as a contents page and is right. The story page's `storymap` is good. Both open in the same 60px serif at the same y as a country encyclopedia — the *one* family whose whole argument is that it is editorial. **DIFFERENTIATE.**

### 13 · Events `/events/`
- **Q** When should I come?
- **Feel** A year with a shape.
- **5s** The year is uneven, and October is the argument.
- **1°** Open a month. **2°** Read the shoulder-season case.
- **VERDICT** `year_band()` is a genuine signature moment and the only chart in the product that makes an argument. It renders 358×84 on a phone. **SCALE IT.**

### 14 · Plan · 15 · Search · 16 · My Europe · 17 · Map · 5 · Discover — the five instruments
- **Q** (plan) Can this make a trip out of what I have? (search) Where is X? (my-europe) What have I kept? (map) Where is everything? (discover) What fits my constraints?
- **Feel** Competence and control. Dark, luminous, precise.
- **5s** The control I need is the first thing on the screen.
- **VERDICT** The instrument head role already fixed the worst of this (titles are labels, controls start at 328–397). The remaining fault is **`/discover`**: a filter row above a 1168×911 black map with 319 three-pixel dots is the single most GIS-application surface in the product, and the mandate names that as a thing EuropeDoor must never feel like. `/my-europe` empty is three grey boxes. **DISCOVER AND THE EMPTY STATES.**

### 18 · Beyond the obvious · 19 · Themes · 20 · Theme · 21 · Motion · 22–23 · Interests
- **VERDICT** `/themes` and `/europe-in` were both rebuilt this year around their own arguments and hold up. **`/interests/` DOES NOT EXIST** — seventeen interest pages ship and the directory has no index, so the server autoindexes it. Nothing links to it, which is why no check caught it: seventeen pages that cannot be seen as a set. **BUILD IT.**

### 24 · Error states `/404.html`
- **VERDICT** "That door does not open" with the whole Atlas drawn under it is the best 404 I have seen on a travel product. **KEEP. DO NOT TOUCH.**

### 25 · Empty states
- **VERDICT** `/my-europe` with nothing saved, `/search` before a query, `/discover` before a filter. All three are honest and all three are grey. An empty state is a first impression for the visitor who got there first. **ART DIRECT THEM.**

### 26 · Loading states
- **VERDICT** There are none, because there is nothing to load — no server, no fetch on most pages, `default-src 'none'`. **CORRECTLY ABSENT.** The five applications fetch an index; those have honest empty states already.

### 27 · Accessibility · SEO · Performance · Image system · Map system
- **VERDICT** The strongest part of the product and the part the mandate says least about, because it is finished: 1,071 browser checks including contrast in both preferences, a 24px floor on every map dot, text alternatives that name all 319 destinations, JSON-LD that refuses claims we cannot hold, 26 KB homepage before the drawn hero and 122 KB after, one projection asserted at 54 points. **NO WORK. DO NOT REGRESS.**

### 28 · Internal linking and conversion paths
- **Q** From any page, what is the next thing?
- **VERDICT** 3,716 derived edges and every removed band keeps its page. But the *conversion* path — the sequence desire → orientation → discovery → planning → action — is not composed anywhere. A destination page's actions are Save and Add to journey, in a sticky bar, at the bottom. **COMPOSE THE PATH.**
- **MEASURED, after.** Every action on three families, at 1280 and 390: a destination page has Save to My Europe at 1,675 of 6,864 and hands the planner its own city; a journey page opens in the Planner. A **country page had nothing at all** — 7,016 pixels, no button, no save, and only the masthead's `/plan`. That is now a hand-off in the Stay layer's grammar on 44 of the 50, and the six without it are the three advisory countries and the three that hold one destination, where no route exists to build.

---

## Part 3 — The mandate's eight refusals, against the built site

| must never feel like | does it? |
|---|---|
| a GIS application | **`/discover` does.** 319 dots on black under a filter row. |
| a tourism database | **the experience category page does.** |
| a government tourism portal | no |
| a generic SaaS dashboard | `/plan` is close; the instrument head role pulled it back |
| a collection of cards | **no longer** — the card grids came off five indexes |
| an AI-generated website | no. The voice is specific and argued |
| a map catalogue | **twenty-two arched maps in the same position, one per family, is exactly this.** The signature has become the wallpaper its own rule warns about |
| a template-driven travel blog | structurally yes: one composition, 1,033 times |

Two of the eight are held, three are partly held, three are live.

---

## Part 4 — The work, in order

The mandate's loop is AUDIT → BENCHMARK → ARCHITECT → ART DIRECT →
IMPLEMENT → RENDER → CRITIQUE → REFINE → TEST → RENDER AGAIN. This document
is the first two. What follows is the order the rest runs in, and the
reason each item is where it is.

1. **The photography architecture** — twelve roles, each with a crop rule,
   a subject rule and an art-direction brief. Declared before a photograph
   exists, which is this repository's standing rule and also the only way
   the empty slots can be designed rather than left.
2. **The design language** — what makes a page EuropeDoor with the logo
   removed, stated as something checkable.
3. **The composition grammar** — the six movements, and which families
   take which. This is what replaces "one page, 1,033 times".
4. **The homepage body** — the doors, the proposition, the second moment.
5. **The phone opening**, every family. Finding 1 is the largest.
6. **The families, in order of damage**: experience category, discover,
   destination, country, events, story, journeys.
7. **The instruments' empty states.**
8. **`/interests/`**, and the linking that follows from it.
9. **Render, critique, refine, render again** — at 1280, 834 and 390, in
   both colour-scheme preferences, as contact sheets.

---

## Part 5 — What has been done against it

Written as the work landed, so the audit and the record do not drift.

| # | done | measured before → after |
|---|---|---|
| 1 | the audit and the benchmark, with the blocked half labelled | — |
| 2 | twelve photography ROLES, a purpose instantiates one | 12 slots → 12 roles + 12 purposes |
| 3 | mobile navigation: three sections behind a gesture | 552px in 366 → nothing off-screen; chrome 149 → 145 |
| 4 | the crop rule, derived and checked at both ends | hero 7% of a frame → 15% |
| 5 | the doors band stopped reserving picture height | 1440: 352 → 245; 390: 1,184 → 920 |
| 6 | the chips stopped naming the four doors below them | 4 duplicated categories → 4 worked examples |
| 7 | the section nav, the same defect on 319 pages | 567px in 358 → nothing off-screen |
| 8 | the experience list leads with the place; the category's shape drawn | invisible sort key → legible |
| 9 | `/discover` fills its land | `fill: none` → 1.91:1 against the water |
| 10 | `/interests` exists | server autoindex → an index ordered by reach |
| 11 | My Europe draws the list it is about | 0% of the phone's first screen → 17% |
| 12 | the doors' crop box, caught by the check added in 4 | 2.794 → 1.923 |
| 13 | the year band's axis | 1.16:1 → 4.76 at 1280, 9.25 at 390 |
| 14 | two index openings that were a generic continent | /stories 23% → 36% of the phone's first screen |
| 15 | the country pages' last grid of abstract plates | 207 plates → 0 |
| 16 | the glyph's missing middle size | 132px at 834 → 240 |
| 17 | a lead journey at size — built, rendered, removed | recorded as a negative result |
| 18 | a map card takes the drawing's ratio, not a photograph's | 834: Europe 138px wide → 208 |
| 19 | `/discover`'s map narrows with the control it sat beside | decoration → 125 of 319 lit, and the count above it |
| 20 | five sub-category pages selected on the wrong word | 39 wrong listings of 401; Monasteries 22 → 4 |
| 21 | the country pages got an action, in the Stay layer's grammar | 50 pages with none → 44 hand-offs |
| 22 | and building it found the planner could not be handed a name | 77 of 313 destinations unnameable → 0 |
| 23 | an instrument for the first screen, so Finding 1 is re-measurable | measured once by hand → `tools/opening.js` |
| 24 | an overture's name was an index label's size on nine families | h1 38px → 48 at 390 |
| 25 | the country page's record moved after its portrait | first figure 591 → 415; 33.6% → 52% |
| 26 | the country portrait never ran the phone collision pass | 32 overlapping label pairs on 18 of 50 plates → 0 |
| 27 | the index opening's actions and note moved after the figure | countries 740 → 488; journeys 718 → 488 |
| 28 | a page claimed its nine shapes were drawn to one frame | 10 viewBoxes → the sentence the drawing supports |
| 29 | the kicker rule named two classes rather than the situation | 6 accent kickers inside a link on the homepage → 0 |
| 30 | the motion index draws the answer each query produced | /europe-in 0% → 20%, then 36% |
| 31 | half of every row on two indexes was empty in the middle | 49% and 48% interior gap → 3% |
| 32 | one row shape for the three indexes that draw their set | two layouts → one |
| 33 | the aperture check was sampling pixels outside its own shot | /events/oct 1.12:1 reported against a real 17.37 |
| 34 | 213 of 319 destinations printed a word cut in half | `[:150]…` → `first_sentence()`, and a check on the shipped HTML |
| 35 | all 129 region maps drew the identical window | 2,916 km on every one → 1,117 at the floor, 27 framed on their own |
| 36 | the plates drew the fade the hero had measured away | 25 of 319 destinations dimmed past half → 6 |
| 37 | the contact sheet named one family wrong and missed four | 23 of 27 covered → 34 pages in three sets, from one list |
| 38 | 196 drawings were hidden on a phone behind a dead rule | region, macro and journey cards blank → drawn |
| 39 | the record moved after the picture on the other two families | destination 574 → 443; region 585 → 438 |
| 40 | the four doors rendered 3 + 1 between the two breakpoints | 30 grids measured, 1 with a mostly-empty last row → 0 |
| 41 | the planner opened on a progress panel for work nobody asked for | 7 live regions at rest, 1 claiming work → 0 |
| 42 | three templates the instruments had never reached | 27 families on the list → 30, and 63 pages that had never been measured |
| 43 | the Fund family had no geography at all | project page 0% of the phone's first screen → 42% |
| 44 | a place put its coordinates between the sentence and the view | desk 31.6% → 38.9%; first figure 634 → 572 |
| 45 | Finding 2's other half, which had never been measured | one composition asserted → 29 body shapes over 47 families |
| 46 | the editorial desk had no feed | nine dated essays, no way to follow them → /stories/feed.xml |
| 47 | a check that had stopped counting, and a document 860 plates stale | 0 of 785 records examined → 785 |
| 48 | the check that found Longyearbyen, blind since the atlas skin | 0 dots of 1,293 → 1,293 |
| 49 | thirty-three pages never reached the head-role check | 1,001 heads of 1,034 → 1,033 |
| 50 | a headline ran off the right edge of a phone, at the design width | /place +7px at 390, +77 at 320 → 0 at every width, on every family |

**Finding 1, re-measured FOUR times, and the fourth correction is the
instrument rather than the pages.** Seven surfaces with no picture on the
phone's first screen became six, then three of twenty-seven, then three of
thirty with none under a fifth and a median of 35.6% — **and that reading
counted, on the homepage, a photograph no reader can see.**

`tools/opening.js` measured every `figure, svg, img, picture…` intersecting
the first screen. The homepage's window plate holds its photograph
`position: fixed`, so it stands still while the wall scrolls past it, and the
band clips it with `clip-path: inset(0)`. **A fixed box's client rect is the
viewport whatever the scroll**, so at scroll 0 the probe read a 1280×720
photograph at y=90 while the band containing it begins 1,818 pixels below the
fold and clips it to nothing. The probe intersects with every clipping
ancestor now, and re-running it moved **one family of thirty** — which is what
says the repair is surgical rather than a new reading of the site:

| | before | after |
|---|---|---|
| homepage at 1280 | 85.5% | **50.5%** |
| homepage at 390 | 72% | **4.4%** |

At 1280 the corrected figures are **three of thirty with no picture** —
`/discover`, `/search` and `/my-europe`, every one an instrument — **one more
under a fifth** (`/stories/<story>` at 16.6%) and a median of **49.7%**.

At 390 they are five with none and twelve more under a fifth, median 16.8% —
and those were true before this repair as well as after it, because only the
homepage moved. **The phone column was never the column this finding was
closed on**, and saying so is the correction: Finding 1 is closed at 1280 and
is open at 390. The table
grew by three because `tools/lib/families.js` had never carried a month
page, a sub-category page or a fund project page, and the last of those was
the find: no figure anywhere on it, at any width, on the register whose
whole argument is that each entry is a real thing in a real place.
`tools/opening.js` is the instrument, so this number can be checked in a
minute rather than re-audited by hand.
**Finding 2**: five families now open on something no other family does —
`/experiences`, `/stories`, `/interests`, `/my-europe`, `/discover` — and
the other half of the finding, which is about the BODY and had never been
measured at all, reads **29 distinct shapes over 47 families**, three h1
sizes and head tops from 136 to 745. `tools/composition.js` is that
instrument.
**Finding 3**: the homepage's second screen is a strip rather than four
holes, and the transition from the continent to the form has air in it.
Measured band by band at 1280, the page is not monotonic: hero 91% ink,
doors 99%, journeys 13%, stories 7%, close 5% — a loud opening, a loud
second screen and three quiet bands, which is rhythm rather than decay.

**Still open**, and each blocked on something that is not design work: the
destination page has no photograph and its order is already correct;
`/experiences` has no picture on its first screen and a recorded refusal of
the only one it could draw; `/plan` and `/search` are instruments and read
as instruments.

**The experience category page was taken up and put down again, twice.** It
is the family Part 3 records as reading like a tourism database, so the
obvious answer is to draw its set — and the eight categories really are
distinct, 27 of 28 pairs overlapping under 0.31. `docs/signature-moments.md`
refuses geography there for a reason that survives re-checking: *48 dots
scattered over Europe would say "food is everywhere", which is true and is
not an insight.* The second idea was to group the list under the four
sub-category bars the page already draws, and the data refuses that: six of
48 experiences are in no sub-category and eight are in two, so the grouping
needs a bucket the page has no name for and prints some invitations twice.
What the page is missing is a photograph, and the register is empty.

**What is not on the list, deliberately.** Acquiring photographs: the
proxy refuses both providers and acquisition is a GitHub Actions step with
a repository secret. Weakening the licence gate to get pictures on the
page faster: refused. Writing the 91 missing stories and 33 missing
journeys: editorial work, not design work, and
`docs/gap-assessment.md` already says so.
