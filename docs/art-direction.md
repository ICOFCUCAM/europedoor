# Art direction — the five exemplars

The shell establishes EuropeDoor. The page establishes the subject. Those are
different responsibilities, and until now the shell has been doing both.

**The shell provides:** brand, navigation, type foundation, spacing language,
the two worlds, global interaction.
**The page provides:** composition, imagery, hierarchy, pacing, purpose.

---

## The five families

| family | what it should feel like | primary job | the asset it is built on |
|---|---|---|---|
| **Destination** | invitation · sense of place | *make me want to know this place* | one authored sentence + three specific highlights |
| **Experience** | possibility · action | *make me want to do this* | the verb — a thing you can actually go and do |
| **Journey** | movement · narrative | *make me want to take the journey* | a sequence of real legs across real distance |
| **Country** | orientation · identity | *help me understand the country* | an authored characterisation, not a fact table |
| **Story** | editorial · human | *make me want to read* | prose, and a voice |

---

## The three questions every page answers, in order

1. **First five seconds** — what is this, and where am I? *Feeling and orientation.*
2. **Next thirty seconds** — why would I care? *The argument.*
3. **When ready to investigate** — the facts. *Population, coordinates, scores, timetables.*

**The database exists to support the experience.** A metric that appears in
band 1 has taken a slot that belonged to the subject. This is the single
diagnostic that failed most often in `docs/design-direction-audit.md`.

---

## Per family, the composition

### Destination — *invitation*
- **Dominant:** the place name, and the authored sentence at display scale.
- **Secondary:** three highlights, numbered, with air — the "why go".
- **Then:** where it is. Real geography, not decoration.
- **Investigation:** places, things to do, transport, tips, onward, scores.
- **Imagery:** one illustration, presented as *the kind of country this is*
  and never as a photograph of the place. It sits with the map, so the pair
  reads "this is what it looks like, this is where it is."
- **Refused:** population, coordinates and scores above the argument.

### Experience — *possibility*
- **Dominant:** the thing you would do, and where you would do it.
- **Imagery:** currently zero on the whole family. Something must carry it.
- **Refused:** a six-row table with a heading.

### Journey — *movement*
- **Dominant:** the sequence. The page should move down the page the way the
  journey moves down the continent.
- **Imagery:** the line itself — legs, distance, nights.
- **Refused:** 34 days rendered as an article with one picture.

### Country — *orientation*
- **Dominant:** what this country is *like*, in a sentence somebody wrote.
- **Investigation:** the fact table, which is good and belongs lower.
- **Refused:** opening on capital / currency / ISO codes.

### Story — *editorial*
- **Dominant:** type. This is the family where typography alone can carry the
  whole transformation, at no imagery cost.
- **Refused:** the atlas chassis — same h1, same measure, tag chips where air
  belongs.

---

## Rules that bind all five

**A visual earns its position or is not placed.** 2,370 plates across 834
pages means the illustration currently appears because the system has one,
which is the one reason the brief forbids.

**390px is a composition, not a stack.** Designed, not QA'd.

**Motion communicates or is absent.** Movement, transition, discovery,
hierarchy, state. Nothing decorative.

**No new primitive until the same pattern has appeared three times.** The
existing eleven remain available and are enough for the first exemplar.

**Nothing invented.** No measurement, no fact, no journey, no content. Every
figure on every exemplar is derived or authored under the existing rules.

---

## Order, and why

1. **Destination** — 319 pages, where search lands, currently one plate under
   a metadata row. Highest leverage in the product.
2. **Experience** — 50 pages, the most under-designed relative to its promise,
   and nothing there to unpick.
3. **Journey** — 18 pages, the widest gap between content shape and page shape.
4. **Country** — 50 pages, sets the editorial register for the atlas.
5. **Story** — 10 pages, type alone, no imagery budget.

Region, Place and Event derive from 1 and 4. **Search, Plan and My Europe are
not in the queue** — a form is the right shape for a form.

---

# Exemplar 1 — Destination, built

`/europe/france/alps-and-east/chamonix`, and the 318 pages that inherit it.

## The composition, and why each move

| act | what | why |
|---|---|---|
| **1. Invitation** | region · country → **name** → the authored sentence at display scale → `TOWN · 2–4 NIGHTS` → interests | The sentence was a `.lede` — 17px grey body copy. It is the single best-written thing on a destination page and it looked like a caption. |
| **2. The argument** | **WHY GO**, three or four highlights, numbered, at reading size | Every one of the 319 destinations has 3–4 highlights. **194 have no places at all** and 98 have neither places nor experiences — so the page is built on what is always there, not on what is usually missing. |
| **3. Where it is** | one figure: generated horizon + located map, captioned | Gives the illustration a reason to exist. The caption says which of the two it is — a generated horizon shown silently beside a real coordinate invites a reader to take it for a photograph. |
| **4. Investigation** | section nav, places, things to do, transport, events, tips, onward, **then** population / region / scores | A reader who has not been told why to care about a place has no use for its population. |

## Measured

- **390 × 844, usable height 712px** (viewport minus the 76px sticky action
  and 56px bottom nav). First screen delivers: context, name, statement,
  kind + nights, interests, WHY GO, reason 01. Intentional — the numbering
  is the scroll cue.
- **41% of the first screen is spent before the name**, and 168px of that is
  a wrapped masthead. **That is shell, not family**, and is untouched here.
- `routes.hash` unchanged. No URL moved.

## Five defects found by rendering, not by reading

1. **The minimap appeared twice** — the original call survived beneath the new figure.
2. **The frame spanned 1,520 km.** Not "where Chamonix is"; half of Europe, labels colliding.
3. **A fixed span of 8 emptied 43 of 319 maps** — including **Berlin and Kyiv**, which are not remote. What a span means depends on how densely the atlas covers that part of Europe, so the frame now widens until it has company and stops.
4. **Four-highlight destinations wrapped 3 + 1**, orphaning the fourth. Venice and Longyearbyen both shipped it.
5. **Coordinates appeared three times** on one page.

## And one defect in the instruments

`primitives.reach` and `checks.py` both matched a class with `\bcard\b`. **A
hyphen is a word boundary**, so `card` counted `card-art` and `row` counted
`rowsub`. The card floor read **0.785 / 0.70; the true figure is 0.226** —
the design system's most-cited primitive was three-quarters an image wrapper.
Found only because this exemplar renamed that wrapper and the floor collapsed.
Both matchers corrected, both floors rewritten to the truth,
`docs/frontend-architecture.md` corrected from 78% to 23%.

## Honest, still open

- **The plates remain the weakest element.** They are carried by the caption's
  honesty rather than by their own quality. Correct motif on all four sampled
  (peaks, skyline, coast, isles) — but at 480×310 they are flat.
- The 168px mobile masthead is a **shell** decision and is not this family's
  to take.

---

# Exemplar 2 — Experience, built

`/experiences/food/markets` and the 49 pages that inherit it.

## What was there

Six left-aligned titles with right-aligned metadata. **Zero plates, zero
cards, zero bands** — the only family on the site with no visual element of
any kind. A database table with a heading, on a page whose job is to make
somebody want to do something.

## What the page actually has

Six well-written sentences about six specific things, **in six different
countries**. The spread across Europe *is* the offer — and it was 11px grey
text, right-aligned, at the end of each row.

## The composition

| | |
|---|---|
| **Leads with** | the country, then the town — the page reads down its left edge like the contents of a magazine feature |
| **Then** | the thing, at reading size, with the sentence somebody wrote about it |
| **Then** | kind and price band, quiet, right |
| **A category** | leads with its authored blurb at display scale |
| **A sub-category** | leads with the countries it reaches, and **is not given its parent's sentence** |

**No imagery, deliberately.** The obvious move was a plate per row, and it is
exactly the trap the brief names: a plate here illustrates the *city*, is
already on that city's own page, and would be placed because the system has
one. Typography and geography carry it instead.

`row exprow`, never a replacement — the `row` primitive holds its reach at
0.909.

## A content defect found on the way

`matches_sub()` searched the **town's name**. The keywords are matched as
prefixes on purpose — so `monaster` catches monasteries and `archaeolog`
catches archaeological — and that made place names satisfy them:

```
\bhall  matched Hallstatt   ->  a salt mine listed under Markets
\bwar   matched Warsaw      ->  a museum listed under Modern history
\bport  matched Portree     ->  a ridge walk listed under Cellars
\bsnow  matched Snowdonia   ->  a slate railway listed under Skiing
```

**Eight of 423 listings across the 40 sub-pages arrived this way; five were
nonsense and three were defensible.** A rule right three times in eight is
not a rule. Dropping the town empties no page (423 → 415). A trailing `\b`
was the other candidate and was rejected — it would break the four keywords
that are stems on purpose.

The published selection rule now says so on the page itself: *"matched
against what we wrote about the experience and never against the name of the
town, because a salt mine in Hallstatt is not a market."*

Four assertions added, all **proved red** by restoring the old matcher.

## The content gap this exposes, and does not paper over

**Forty sub-categories have a name, a keyword list and no authored
characterisation.** The first version filled that hole with the parent
category's blurb, which put *"Markets, tables, cellars, vineyards and the
dishes that belong to one valley"* in 40px type at the top of the Markets
page — authored, true, and about the wrong thing. A sub-page now leads with
its countries instead. **The missing sentence is editorial work, not a design
problem, and the design's job is to leave the gap visible.**

---

# Exemplar 3 — Journey, built

`/journeys/arctic-to-mediterranean` and the 17 that inherit it.

## What was there

34 days, 13 stops, 8 countries — as an article with one plate at the top, an
**eleven-item fact table above the route**, and the sequence itself four
screens down as a bulleted list. The audit called this the widest gap in the
product between what content *is* and what a page *is*.

## The composition

| act | what |
|---|---|
| **1** | `JOURNEY` → name → **the strapline as the hero** — *"The full length of Europe, 69°N to 38°N"* was an 11px uppercase kicker |
| **2** | `34 days · 13 stops · 7 countries · 4,993 km`, one derived line |
| **3** | **the route, drawn, immediately** — over real land |
| **4** | the sequence as a rail: days and nights left, a node per stop, the distance sitting *on* the rule above the town it leads to |
| **5** | then the fact table, the experiences, the food, the packing, the estimate |

**The hop moved above the stop it leads to.** It used to be appended after
the `why`, which read as a footnote belonging to the arriving town rather
than as the movement between two of them — on a page whose entire subject is
movement. The first and last nodes are filled: a journey has a beginning and
an end, and that is the one thing thirteen identical bullets cannot say.

## Three defects found by rendering

1. **The route map rendered ~2,700px deep.** Its viewBox is the route's own
   bounding box, and a north–south journey is 2.35× taller than it is wide;
   at `width:100%` that is what you get. It is now **sized by height** and
   the width follows the ratio — which gives a portrait map for Arctic to
   Mediterranean and a landscape one for the Hanseatic Arc, without either
   being told which it is.
2. **No land under the line.** A lime zigzag on black — the same "a dot map
   with nothing under it is a scatter plot" fault as the homepage hero, and
   worse here, because the whole claim of a journey page is that the route
   crosses a real continent.
3. **Labels printed through each other** — "Lofoten (Svolvær)" straight
   across "Abisko" on the flagship route. A label is now dropped when it
   would land on one already placed: **29 of 121 across all journeys**.
   Costs nothing — every stop keeps its dot and its `<title>`, and the rail
   below names all of them in order.

## And a check that could not fail

The first version of the ordering assertion compared two **headings**, so
moving the fact table back above the route left both headings where they
were and the deliberate regression passed. Rewritten to compare the position
of `class="facts"` against `class="legs route"`, and then proved red.
**A check that cannot fail on the thing it names is worse than no check.**

---

# Exemplar 1, finished

The first pass designed the **opening** and left everything below the
placeband as the audit found it. That is not a first-grade page; it is a
first-grade opening bolted to the old one. What changed on the second pass:

| | before | after |
|---|---|---|
| the practical writing | *"Give it 2–4 nights"*, *"When to come"*, *"Getting there"* — in a grey rail on the right | **in the flow**, three columns, directly under the map. It is what a reader asks the moment they decide they might go |
| the rail | four headings of prose plus the actions | **actions only** — that is what a rail is for. Sticky, so it travels |
| the score bars | first thing after the argument | last, in **"The record"**, with a lede saying what it is: *useful when you are already interested, and not a reason to be* |
| section ledes | *"2 recorded so far. We hold what each one is and deliberately not its opening hours"* — our data policy, as the section's introduction | a **quiet note under the rows**. The honesty is a rule here and stays; its prominence does not |

## The plate: it did not earn its place

I called the plates the weakest element and then left them on 319 pages.
Rendered three ways and looked at:

- **plate + map** — the map squeezed to half width, labels cramped, and a
  flat illustration beside it
- **map at half width alone** — lopsided, no visual at all
- **map at full width** — Chamonix with Annecy, Zermatt, Lauterbrunnen and
  Lugano around it, legible, and true

The third is plainly the strongest. **So the illustration goes**, under the
same rule the homepage hero follows: a photograph if the register holds one,
and where it does not, nothing in its place. The plates keep every other job —
this page's social card is still drawn from `plate_shapes()`.

`plates.page_share` is now a **ceiling** at 0.465 (was 0.778 across 834
pages). A ceiling, not a floor, because the failure mode being guarded is an
illustration *spreading* onto pages that do not need one. Proved red by
putting the plate back: *"0.762 exceeds the recorded ceiling 0.465"*.

**And a caption that outlived what it captioned.** `art_note()` printed
"Illustration, not a photograph" — honest while there was an illustration,
and a disclaimer about something absent once there wasn't. Deleted.

## Motion: considered, tried, removed

The only candidate was transition — the section nav jumps several screens.
`html { scroll-behavior: smooth }` was added for it and **failed the browser
suite within a minute**: it makes every programmatic `scrollTo` asynchronous,
and a check that scrolls to the bottom to assert the sticky bars do not cover
the last link measured before the scroll landed. The layout was fine; the
global setting was not.

The site already had the answer — `planner.js` opts in per call with
`scrollIntoView({behavior:"smooth"})`, exactly where a transition needs
explaining. **No motion was added.**

## Still open, and not this family's to take

The **168px mobile masthead** — 20% of a 390×844 viewport on all 1,072 pages,
on a site that already carries a bottom thumbbar covering the same
destinations. Shell, not page. Owner's call.
