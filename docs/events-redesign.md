# /events — the European Calendar Atlas

The owner's brief: EVENTS → THE EUROPEAN YEAR → MONTH → FIXED POINTS →
SHOULDER SEASON → EVENT CHARACTER → OPEN A DOOR, and one sentence that
decides the whole thing — *it should not feel like Eventbrite for Europe; it
should feel like an editorial instrument for understanding Europe through
time.*

## Part 1 — the source audit

The page was **right and it stopped after three bands**. `ed_opening` over
the year band over twelve month rows: 16,849 bytes, one `<img>`, and a
closing `<p class="small">` saying there were eight categories without naming
one of them. Nothing in it was wrong — the catalogue of 197 rows and the
twelve identical month chips had both already been thrown away, and
`year_band()` is this family's signature. What was missing is what the data
holds and the page did not print.

**AND EIGHT FILTERS WERE BUILT AND DISCARDED ON EVERY BUILD.** `kindfilters`
was composed inside `events_page` from the eight kinds and their counts —
eight `<label><input>` elements — and the body f-string never mentioned it.
The identical variable in `events_month_page` IS that page's control; this
one was dead. *An ignored argument is dead code that looks like a decision*,
and it is exactly why the brief's event-character band was missing: **the
eight were counted, rendered, and thrown away.**

## Part 2 — the data, and the two numbers the brief got from the live page

| | |
|---|---|
| fixtures | 150, each a `name`, a `where` (prose), a `month` and a `kind` |
| months | 12, with the counts the brief quotes — 3, 13, 6, 15, 4, 20, 28, 16, 16, 11, 4, 14 |
| kinds | 8 — cultural 39, seasonal 25, religious 21, food 20, concert 20, market 15, exhibition 5, sport 5 |
| photographs | `events-hero` is in the register, so this family already opens on a picture |
| coordinates | **none** — a fixture's `where` is prose, so there is no map of the fixtures and no dot to draw |

**The brief's one wrong figure is the October shoulder count.** It asks for
*26 countries in their quieter shoulder in October*; the dataset says **25**,
because the three advisory countries are excluded. Derived on every build.

## Part 3 — the finding nobody had cross-tabbed

The brief asks for a FIXED POINTS ledger and fills it with six authored
groupings — *Winter traditions*, *Spring awakenings*, *The long light*,
*Europe in full colour*, *Harvest Europe*, *The winter threshold*. That is
the right instinct with nothing behind it, and **the data says it better.**
Crossing 150 fixtures by month and kind:

| month | n | one kind holds |
|---|---|---|
| February | 13 | **cultural 10** (77%) |
| April | 15 | **religious 9** (60%) |
| June | 20 | **seasonal 10** (50%) |
| September | 16 | **food 8** (50%) |
| December | 14 | **market 9** (64%) |
| **July** | **28** | nothing above **43%** |

**The busiest month is the least characteristic.** July holds 28 fixtures,
more than any other, and no kind reaches half of them; February holds
thirteen and 77% of those are one thing. A crowded month is not the same as
a month with a character — which is a second argument to sit beside the
shoulder one, and both are measured rather than written.

**AND "HALF OR MORE" IS SATISFIED BY 2 OF 4.** The first version of that
threshold reported **eight** decisive months, because March (3 of 6), May (2
of 4) and November (2 of 4) clear a share test on a handful of fixtures:
arithmetically true, editorially empty, and the small-sample form of *a count
that is not the set's own extent reads as one*. A month also has to hold at
least an average month's worth of the year for a share of it to mean
anything, and **the average is derived rather than picked** — 150/12 is 12.5,
which admits exactly the five above and excludes exactly the three that were
noise.

## Part 4 — what was built: six plates

| brief band | plate |
|---|---|
| EVENTS | `evopen` — the hero photograph and *What is on, and when.* |
| THE EUROPEAN YEAR | `year` — `pagehead index`, the derived extent, and `year_band()` at full width |
| MONTH | `months` — twelve rows, fixtures and shoulder countries |
| FIXED POINTS + EVENT CHARACTER | `character` — **one band, because they are two views of one cross-tab** |
| SHOULDER SEASON | `shoulder` — *Go when Europe breathes*, photographic |
| OPEN A DOOR | `pickmonth` — *Choose a month. Open a door.* |

**FIXED POINTS AND EVENT CHARACTER ARE ONE BAND.** Printing the eight kinds
with their counts and then the five decisive months separately is the same
table twice on one page — the fault 220 place pages had, where a strip and
the rows under it were the same places. One band carries both axes: each
kind's own peak month beside its count, and the months where one character
actually holds. **And a ledger of the 150 is the catalogue this page already
threw away** — 197 rows and 14,875 pixels, with no reader ever reaching
December. Every fixture is on its month's page, behind the filter that
belongs there.

**THE CHARACTER ROWS ARE `<div>` AND NOT `<a>`**, because there is nowhere
for them to go: this atlas has no per-kind page, and a row that looks like
navigation and leads nowhere is the chip-that-filters-nothing one family
over. **And the bar is against the largest kind rather than against the
total** — eight kinds summing to 150 would put `cultural` at 26% and read as
a share of the year, where what the row compares is one kind against another.

**THE SHOULDER BAND'S PHOTOGRAPH BELONGS TO THE ARGUMENT.** The brief asks
for a photographic *Go when Europe breathes*, and the register holds a
picture for exactly one piece of writing that makes this case: *The case for
going in October*. So the band is that essay, with its own photograph, linked
to it — rather than a generic autumn landscape standing in for a sentence,
which is this site's oldest rule about pictures and stories. `.ed-feature` is
the scale, its second caller after /stories. **Nothing was acquired**;
`safety.img_tags` moved 1205 → 1206 and the reason is in
`tools/invariants.py`.

**NO APERTURE AND NO SECOND DRAWING.** The door is how this atlas draws
GEOGRAPHY and a year is not a place — twelve little arches would be the
signature as wallpaper, which `docs/signature-moments.md` question 6 already
settles. And a map of the fixtures is refused by the data rather than by
taste: a fixture's `where` is prose, so there are no coordinates to plot.

## Part 5 — the defects only building it found

**`ed_opening` ESCAPES ITS INTRO**, so `&mdash;` shipped as the five
characters a reader sees. The raw f-strings in `pages.py` take the entity
because they ARE markup; a helper's keyword argument takes the character.

**AND AN F-STRING EXPRESSION CANNOT CONTAIN A COMMENT.** Writing the reason
for that fix beside the keyword argument stopped the build with *"f-string
expression part cannot include '#'"* — which `CLAUDE.md` already records
twice. **Nor a backslash**: the escape `—` then failed with *"f-string
expression part cannot include a backslash"*, so the character is written as
itself and the reason lives in the function above.

**`.sheet-gal` ENDS `display: block` AND `.sheet-paper` DOES NOT.** Both
`paper` bands here would otherwise inherit `.sheet`'s `minmax(0, 40%)
minmax(0, 1fr)` and put their head in the 40% track — the fault /stories'
feature band shipped with one commit earlier, measured there as a 205-pixel
photograph at 1280. The year band is a twelve-column chart that cannot be
read in 40% of a page.

**AND BOTH OBVIOUS NAMES FOR THE CLOSE WERE TAKEN.** `.sheet-door` is the
homepage's opening (29 rules) and `.closesay` is the homepage's and
/discover's close at `max-width: 32rem`, which /plan already recorded as a
statement 512 pixels wide inside a 1,152-pixel band. Grepped first, named
`pickmonth`, and the measure sits on the prose rather than on the band.

Measured after, with no horizontal overflow at any width:

| | 1280 | 834 | 390 | 320 |
|---|---|---|---|---|
| the year chart | 1152 | 786 | 358 | 288 |
| the shoulder picture | 752 × 564 | 514 × 385 | 358 × 269 | 288 × 216 |
| page height | 7,738 | 7,665 | 10,060 | 10,381 |

16,849 bytes and 1 photograph to 23,996 and 2, three bands to six.

## Part 6 — a class name with no rule is still taken

**`sheet-year` COLLIDED WITH THE HOMEPAGE AND THE GREP THAT EXISTS TO
PREVENT THAT RETURNED ZERO.** This repository records five class-name
collisions — `.doorgo`, `.sendsay`, `.closesay`, `.sheet-send` and a
duplicated `.deskart figcaption` — and the answer written after each is
*grep the stylesheet before naming a composition*. That was done here, for
all six plate names, and `.sheet-year` came back with **0 rules**.

It was still taken. **The homepage's plate 07 has emitted `sheet-year` since
the homepage became a plate sequence, and nothing styles it** — the class is
there to name the band, and its room (`sheet-gal`) does the work. So the
grep is half an answer: a plate class can be emitted by a page builder and
styled by nothing at all.

The consequence was live: `.sheet-year, .sheet-shoulder { display: block }`,
written for the calendar's year chart, landed on the homepage's plate 07 as
well.

**AND THE DEAD-RULE SCAN THEN REPORTED THE DECLARATION DEAD**, which is how
the collision was found. Its page list carries `/events/oct` — a month page
— and not `/events`, so the only page it could measure that rule on was the
homepage, where the plate is already block and removing it changes nothing.
Measured on /events with the declaration and without:

| | with | without |
|---|---|---|
| `.sheet-year` computes | block | grid |
| the year chart | **1,152** | 619 |
| the band's head | 1,152 | 461 |
| the shoulder photograph | 752 | 392 |

*A rule measured only where it loses looks like a rule that wins nowhere* —
the fourth occurrence, and the fourth time the answer is a page. `/events` is
in the scan's list now.

**AND THE GUARD IS A CHECK RATHER THAN A SENTENCE.**
`c_plate_class_owner` reads the built site for every `sheet-` class and the
families that emit it. The five rooms — `gal`, `paper`, `pine`, `quiet`,
`bleed` — bind tokens and are shared by design; a composition class belongs
to one family. A second family wanting one is not forbidden and has to be
**declared**: `.sheet-keep` is a real centred close that /discover and
/experiences share, and it is in `SHEET_SHARED` with its reason. Moving one
is allowed; moving one silently is not, which is the invariant register's own
rule applied to a class name. Proved red both ways — a composition class on
a second family, and a declared exception nothing reaches.


---

## Part 7 — the doctrine audit

`docs/redesign-doctrine.md` arrived after this page shipped, so both of its
audits are filled in here from the evidence above rather than from memory.
Every line that is not satisfied says so.

**Monotony**, measured at 1280: **18%**, twelve `row monthrow` siblings, with `row charrow` at 12%. The year band is the page's subject and it is a chart rather than a repeated component, so it does not appear in this measurement at all.

### CONTENT PRESERVATION

- [x] every important existing content item retained — 150 fixtures, 12
      months, 8 kinds
- [x] existing counts retained and derived — including the shoulder figure,
      which the brief had as 26 and the dataset says is 25
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained
- [x] existing functionality retained — `events.js` still filters
- [x] existing data loaders reused
- [x] existing map engine reused — and the year band deliberately carries NO
      aperture, because twelve little arches is the signature as wallpaper
- [x] existing image and provenance system reused

### DESIGN TRANSFORMATION

- [x] the page has a new composition
- [x] the existing card/grid structure was not merely reskinned — twelve
      identical pills became a year instrument
- [x] the opening communicates the page's purpose
- [x] the content hierarchy was reconsidered — two of the brief's bands are
      one band, because they are two views of one cross-tab
- [x] photography has an editorial role
- [x] the map or the data has a meaningful visual role — the chart is the page
- [x] the sections have different visual rhythms
- [x] the page does not read as a CMS listing
- [x] the page has a memorable signature moment — October is thin above the
      line and deep below it, and that disagreement is the family's argument

### Notes, including what this audit does not claim

**The month page is not covered by this audit.** `/events/<month>` measures
21% with `row event` at 16% behind it, which is a list with a frame round it
and is the right shape for a month.
