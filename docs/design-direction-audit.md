# §6 — Product Design & Art Direction Audit

**Nothing was changed to produce this document.** Twelve representative pages
were rendered in Chromium at 1280×900, screenshotted, looked at as a set, and
measured. No CSS, no template and no data was touched. That is deliberate: an
audit that fixes as it goes ends up rationalising what is already there.

Labels: **MEASURED** · **OBSERVED** · **INFERRED** · **PROPOSED**

---

## Part 1 — The finding, before the twelve

### The site has one page, rendered 1,072 times

**MEASURED**, across the twelve rendered pages:

| page | h1 size | h1 top | world | accent |
|---|---:|---:|---|---|
| Homepage | **76px** | **325** | discover | — |
| Country · Italy | 60px | 164 | discover | — |
| Region · Athens & the Peloponnese | 60px | 164 | discover | — |
| Destination · Chamonix | 60px | 164 | discover | — |
| Place · The Acropolis | 60px | 164 | discover | — |
| Experience · Markets | 60px | 164 | discover | — |
| Journey · Arctic to Mediterranean | 60px | 164 | discover | — |
| Story · What a pilgrimage is for | 60px | 164 | discover | — |
| Event · June in Europe | 60px | 164 | discover | — |
| Search | 60px | 164 | intelligence | — |
| Plan | 60px | 164 | intelligence | — |
| My Europe | 60px | 164 | intelligence | — |

**Eleven of twelve pages place an identically-sized headline at an identical
vertical position.** The only page that differs is the one rebuilt last week.
Every family opens with the same four moves in the same order:

```
breadcrumb  →  11px uppercase kicker  →  60px serif h1  →  grey lede  →  content
```

A reader arriving on a 34-day, seven-country journey and a reader arriving on
a single archaeological site meet the same first 200 pixels. **This is the
whole of the user's thesis, measured rather than asserted.**

### The art-direction layer exists and weighs 11 pixels

**MEASURED.** The accent system is not broken — it works exactly as designed:

| page | body class | kicker colour |
|---|---|---|
| Italy | `area-countries` | `#2A4AD9` cobalt |
| Story | `area-stories` | **`#A4491F` terracotta** |
| Event | `area-events` | **`#A4491F` terracotta** |
| Experience | `area-experiences` | **`#A4491F` terracotta** |
| Journey | `area-journeys` | `#2A4AD9` cobalt |
| Chamonix | `area-countries` | `#2A4AD9` cobalt |

And `data-accent` — the heritage/atlantic channel — fires on **4 pages out of
1,072**.

So the entire visual difference between a cultural magazine story and a
country encyclopedia entry is **one line of 11px uppercase text changing
hue**. Body copy, headline, links, cards, spacing, rhythm, imagery: identical.
The system is not absent. It is present and doing almost no work.

### 2,370 plates, on 834 of 1,072 pages

**MEASURED** — 2,370 rendered `.plate` elements across 78% of the site. The
owner's estimate of 2,377 is right to within seven.

They are the primary visual language of nearly every page, and the audit
confirms the risk named in the brief. Three observations from the renders:

- **Region · Athens & the Peloponnese** shows four destination plates in a
  row that are near-identical bands of navy and grey-green. A reader scanning
  them sees *a family*, not four places.
- **Place · The Acropolis** is illustrated with a **skyline** motif — vertical
  bars, a modern city silhouette — for a fifth-century BC hilltop ruin. The
  motif is derived correctly from Athens' interests; it is simply wrong about
  this place.
- The plates are the same visual weight on a *journey*, a *story*, a *place*
  and a *destination*. They do not know what kind of page they are on.

**INFERRED:** at 78% coverage the plate stops reading as illustration and
starts reading as *chrome*. The technology has become visible.

---

## Part 2 — The twelve families

Each block: purpose · user · action · emotion, then what the render actually
shows, then what is missing and the art direction proposed.

---

### 1 · HOMEPAGE — `/`

**Purpose** the entrance · **User** someone who has not decided anything ·
**Action** begin · **Emotion** *I want to go there*

- **Hierarchy** full-bleed dark hero → mosaic → journeys → stop.
- **Imagery** awaiting its licensed photograph; ground only.
- **Density** 370 words. Lowest on the site, correctly.
- **Designed:** the composition and the restraint. **Generated:** the eight
  mosaic plates. **Database:** nothing.
- **Missing** the photograph. That is the standing gate.
- **Direction** already set. Not this audit's subject.

---

### 2 · COUNTRY — `/europe/italy`

**Purpose** *tell me what this country is actually like* · **User** deciding
between countries · **Action** explore the country · **Emotion** appetite and
orientation

- **Hierarchy MEASURED** kicker → h1 "Italy" → 3-line prose → chip row → a
  **facts table** (capital, currency, languages, population, ISO codes, time
  zone, membership, typical day, best months) → "Worth knowing" sidebar → 9
  h2s, 29 h3s, 18 rows, 12 fact blocks, 11 cards, 11 plates, 1,363 words.
- **Composition OBSERVED** two columns of text and metadata. The first
  1,400px of Italy contains **no image at all** — the first plate is far below
  the fold.
- **Typography** one serif h1, everything else grey sans at one size.
- **Designed:** the facts table is genuinely well made. **Generated:** the
  plates. **Database:** the whole upper third — Italy opens as a record.
- **Missing** Italy. Nothing above the fold distinguishes it from Estonia
  except the letters. No atmosphere, no light, no sense of a place with a
  character. An editorial country guide opens with the country.
- **Direction PROPOSED** *editorial / authoritative / cultural*. A country
  should open on an image and a sentence, and put its metadata **below** the
  first idea, not beside it. The facts table is reference material, and
  reference material belongs after the argument, not in place of it.

---

### 3 · REGION — `/europe/greece/athens-and-the-peloponnese`

**Purpose** regional discovery · **User** has chosen a country · **Action**
narrow to somewhere · **Emotion** *what is in here, and is it enough?*

- **Hierarchy MEASURED** kicker → h1 → lede → chips → **a metric strip**:
  DESTINATIONS 8 · PLACES RECORDED 14 · EXPERIENCES 3 · A FULL PASS ~14
  nights · TYPICAL DAY €95–145 → then four plates.
- **Composition OBSERVED** the metric strip is the most prominent element on
  the page. **This is a dashboard.** "PLACES RECORDED 14" is a statement about
  our database, not about the Peloponnese.
- **Designed:** the €/night and full-pass figures are real and useful.
  **Database:** "PLACES RECORDED" — the phrase names our own coverage.
- **Missing** the region's shape and character. A region is the one level
  where *geography* is the story — a coast, a mountain range, a group of
  islands — and there is no geography on it.
- **Direction PROPOSED** *spatial and comparative*. The region is where the
  map earns its place on a content page: these eight destinations, where they
  sit relative to each other, how long between them.

---

### 4 · DESTINATION — `/europe/france/alps-and-east/chamonix`

**Purpose** place immersion · **User** considering going · **Action** decide
and go deeper · **Emotion** *what is it like to be there*

- **Hierarchy MEASURED** kicker → h1 → lede → chips → fact row → **one large
  plate** → 13 h2s, 18 h3s, 17 rows, 1,049 words.
- **Imagery MEASURED** exactly **1 plate** on the highest-value template in
  the product, 319 of them.
- **Composition OBSERVED** the plate sits *after* the metadata, so the first
  screen is text and small caps.
- **Designed:** the section structure below is good — things to do, food,
  journeys through here, nearest onward stops.
- **Missing** immersion, entirely. This is the page the brief calls
  "photographic and intimate" and it is the least visual family on the site
  relative to its importance.
- **Direction PROPOSED** *immersive / photographic / intimate*. **This is the
  exemplar I would build first** — 319 pages inherit it, it is where search
  lands, and it currently has one flat picture below a metadata row.

---

### 5 · PLACE — `/europe/.../athens/place/acropolis`

**Purpose** a single thing worth going to · **User** already at the
destination level · **Action** understand this one thing · **Emotion**
anticipation

- **Hierarchy MEASURED** kicker "ARCHAEOLOGICAL SITE · ATHENS, GREECE" → h1
  "The Acropolis" → two-line lede → **a skyline plate** → 484 words, 7 h2s.
- **Imagery** the motif is **wrong for the subject**. Not a bug — the motif is
  derived from Athens' interests and Athens is a city — but a reader sees a
  modern skyline over the words "The Acropolis".
- **Designed:** the kicker's kind + parent line is a genuinely good
  orientation device. **Database:** the rest.
- **Missing** the reason it matters. 484 words about the Acropolis is a stub,
  and the page's whole job is *this one thing*.
- **Direction PROPOSED** *singular and reverent*. A place page should be the
  most focused thing in the product: one subject, one image, one argument.
  **Plates should probably not appear here at all** — a wrong picture is worse
  than none.

---

### 6 · EXPERIENCE — `/experiences/food/markets`

**Purpose** experience discovery · **User** browsing by what they like doing ·
**Action** find one and go · **Emotion** sensory appetite

- **Hierarchy MEASURED** kicker → h1 "Markets" → one line → **six rows**.
- **Imagery MEASURED** **zero plates, zero cards, zero bands.** 310 words,
  1,479px tall.
- **Composition OBSERVED** a list of six left-aligned titles with
  right-aligned place names. **This is a database table with a heading**, and
  it is the clearest single example in the product of the fault this audit was
  called to find.
- **Designed:** nothing on this page is art-directed.
- **Missing** everything sensory. A page called "Markets" — food, noise,
  colour, morning light — is rendered as a bare table.
- **Direction PROPOSED** *sensory / visual / inspirational*. The most
  under-designed template relative to its promise, and the cheapest to
  transform because there is nothing there to unpick.

---

### 7 · JOURNEY — `/journeys/arctic-to-mediterranean`

**Purpose** a curated travel story · **User** wants the trip designed for them
· **Action** start imagining it · **Emotion** narrative pull

- **Hierarchy MEASURED** kicker → h1 → lede → **one plate** → prose → 7 h2s,
  23 h3s, 12 fact blocks, 1,347 words, 7,294px tall.
- **Composition OBSERVED** 34 days and seven countries, rendered as **an
  article with one picture at the top.** There is no sequence, no line, no
  movement, no sense of north-to-south — on a journey whose entire idea is
  "69°N to 38°N".
- **Designed:** the leg structure and the honest night counts.
- **Missing** the journey *as a journey*. This is the family where the gap
  between purpose and rendering is widest: the content is a sequence and the
  page is a document.
- **Direction PROPOSED** *narrative / cinematic / sequential*. A journey page
  should move down the page the way the journey moves down the continent.

---

### 8 · STORY — `/stories/what-a-pilgrimage-is-for`

**Purpose** a digital magazine · **User** reading, not planning · **Action**
read to the end · **Emotion** absorption

- **Hierarchy MEASURED** terracotta kicker "FAITH · 8 MIN" → h1 → standfirst →
  byline → 5 tag chips → **a forest plate** → 591 words.
- **Composition OBSERVED** the closest thing on the site to editorial, and
  still on the atlas chassis: same h1 size, same position, same measure, tag
  chips where a magazine would have air.
- **Designed:** the standfirst and the reading time. **Generated:** the plate.
- **Missing** typographic voice. 591 words is a short read given the promise,
  and the type does nothing an article's type should do — no drop, no pull
  quote, no shift in measure, no rhythm.
- **Direction PROPOSED** *editorial and typographic*. **This is the family
  where type alone can carry the whole transformation**, with no imagery
  budget at all.

---

### 9 · EVENT — `/events/jun`

**Purpose** a live cultural calendar · **User** has dates, wants what's on ·
**Action** find something worth travelling for · **Emotion** timeliness

- **Hierarchy MEASURED** kicker → h1 "June in Europe" → lede → chips → **66
  rows and 70 h3s**, 1,456 words, 8,021px tall — the longest page audited.
- **Composition OBSERVED** an undifferentiated list, each row title-left,
  country-right. Nothing is bigger than anything else. **No event is more
  worth travelling for than any other**, which is exactly the judgement a
  cultural calendar exists to make.
- **Designed:** the recurring-fixtures framing is honest and right.
- **Missing** hierarchy of any kind, and time. A calendar with no sense of
  *when in the month* is a list.
- **Direction PROPOSED** *editorial calendar*. A few things given real weight,
  the rest listed. A flat 66-row list is a data dump wearing a month's name.

---

### 10 · SEARCH — `/search`

**Purpose** intelligent discovery · **Action** find it · **Emotion**
competence

- **MEASURED** intelligence world, 225 words, 1,241px, no plates.
- **OBSERVED** the most *purpose-fit* page in the audit. Dark, quiet, a field,
  and an honest statement that nothing typed is sent anywhere. It looks like
  an instrument because it is one.
- **Missing** little. **Direction** unchanged.

---

### 11 · PLAN — `/plan`

**Purpose** a planning workspace · **Action** build my journey · **Emotion**
focus

- **MEASURED** 2,379 words — the most text of any page audited — 0 plates,
  0 cards, 3 h2s.
- **OBSERVED** correctly a tool: sentence box, then the form. The word count
  is explanatory copy carrying the honesty commitments, and it is *dense*.
- **Missing** nothing structural. **OBSERVED** the one risk is that a
  first-time reader meets 2,379 words before their itinerary.
- **Direction** *focused / intelligent / functional*, as built. Leave alone.

---

### 12 · MY EUROPE — `/my-europe`

**Purpose** a personal space · **Action** return to what I saved · **Emotion**
quiet ownership

- **MEASURED** 272 words, 1,239px, empty state.
- **OBSERVED** the empty state is genuinely well written — "The list you are
  building", and an explanation that nothing leaves the browser.
- **Missing** any sense that this is *mine*. It is the same limestone-and-
  graphite as the tools.
- **Direction PROPOSED** *personal / quiet / collected*. The one family where
  a different ground is justified by purpose rather than by decoration.

---

## Part 3 — Answers to the audit's own questions

**What feels designed** the homepage; the search page; the facts table on a
country; the kind+parent kicker on a place; the honesty copy everywhere.

**What feels generated** the plates, at 78% site coverage — and specifically
wherever the motif contradicts the subject, as on the Acropolis.

**What feels like database output** the region's metric strip ("PLACES
RECORDED"), the experience list, the 66-row event list, and the first 200px
of nine families.

**What is missing across the board**

1. **Family identity.** One opening for twelve purposes.
2. **Imagery that knows what page it is on.** One plate at one weight everywhere.
3. **Typographic range.** One h1 size, one measure, one rhythm, 1,072 pages.
4. **Editorial judgement in lists.** Nothing is ever bigger than anything else.

---

## Part 4 — The exemplar plan

Not 1,072 pages. **Five pages, in this order**, each one deriving a family
system the rest inherit:

| # | exemplar | why first | inherits |
|---|---|---|---|
| 1 | **Destination — Chamonix** | highest value, where search lands, currently one plate below a metadata row | 319 pages |
| 2 | **Experience — Markets** | most under-designed relative to promise; nothing to unpick | 50 pages |
| 3 | **Journey — Arctic to Mediterranean** | widest gap between content shape and page shape | 18 pages |
| 4 | **Country — Italy** | opens as a record; sets the editorial register for the atlas | 50 pages |
| 5 | **Story — a pilgrimage** | type alone can carry it, no imagery budget | 10 pages |

Region, place and event follow from 1 and 4. Search, plan and my-europe are
**not** in the queue — they are the three pages already fit for purpose.

**Every exemplar must be judged as one composition at 1280 and at 390 before
its family inherits anything.**

---

## Part 5 — Two rules this audit adds

**Design to purpose, not to data shape.** A page's structure should come from
what the reader is trying to do, not from the shape of the record behind it.
The experience list is six rows because the data is six rows; that is the
wrong reason for a layout to exist.

**A shared template is not a shared experience.** One shell, one stylesheet
and eleven primitives are an engineering achievement and must be kept. They
are not, by themselves, a design. Eleven of twelve families currently prove
it: identical h1 size, identical position, one 11px line of colour between a
magazine and an encyclopedia.

---

## Part 6 — What this audit did not do

It changed nothing. It also did not measure:

- any page at 390px (the twelve renders are desktop only)
- interaction, hover, focus or motion on any family
- the 24 families not represented among the twelve
- whether the plate motif is wrong on places other than the Acropolis —
  **one instance is an observation, not a rate**

Those are the next measurements, and they come before any exemplar is drawn.
