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
