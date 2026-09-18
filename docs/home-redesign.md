# The homepage — inspected before anything was changed

`docs/redesign-doctrine.md` says inspect first and write no CSS, so this is
the inspection. Measured on the built site at commit `0e75566`, 2026-09-18,
before a byte of the homepage moved.

## The eight plates as shipped

| plate | room | bytes | `<img>` | svg `<image>` | words |
|---|---|---:|---:|---:|---:|
| 01 the door | `sheet-door sheet-gal` | **91,176** | 0 | 41 | 196 |
| 02 the window | `sheet-bleed` | 1,957 | 1 | 0 | 35 |
| 03 the places | `sheet-places sheet-gal` | 11,806 | 5 | 0 | 102 |
| 04 the crossing | `sheet-crossing sheet-gal sheet-quiet` | 7,003 | 3 | 0 | 104 |
| 05 the atlas | `sheet-atlas sheet-gal` | 2,515 | **0** | **0** | 88 |
| 06 the reading | `sheet-reading sheet-gal sheet-quiet` | 4,324 | 1 | 0 | 131 |
| 07 the year | `sheet-year sheet-gal` | 5,166 | **0** | **0** | **228** |
| 08 the message | `sheet-end sheet-gal` | 1,158 | 0 | 0 | 79 |

131,975 bytes, one `h1`, seven `h2`, one `h3`, ten photographs and 41 clipped
country doors.

## FINDING 1 — THE PICTURE PLAN IS TWO REGISTER-GENERATIONS OUT OF DATE

This page was composed when the register held **eleven** photographs, and its
recorded history says so: the theme row grew from eight tiles to eleven, the
window arrived when `home-hero` was acquired, the four doors were removed
because a slot waiting for a picture is honest and three hundred pixels of one
is a hole.

The register now holds **826 rows**, and it is complete for the atlas:

| | |
|---:|---|
| 319 | every destination |
| 255 | every place |
| 130 | every region |
| 50 | every country |
| 17 | every interest |
| 13 | every theme |
| 10 | journeys |
| 9 | every macro region |
| 8 | every experience category |
| 8 | stories |
| 7 | index heroes |

The homepage spends 51 of them, and **three of its eight plates draw
nothing.** The sharpest instance is plate 05: it says *One continent. Fifty
doors.*, lists fifty country names as text links, and draws none of the fifty
country photographs the register holds. Plate 07 carries the most words on
the page — 228 — and no picture. Plate 08 is a closing statement, where
nothing is the right answer.

**This is not "the homepage needs more photographs".** It is that the
composition was solved against a constraint that no longer exists, and every
band which reads as thin reads that way for the same reason.

## FINDING 2 — EVERY HEADING ON THE PAGE RUNS TOGETHER IN TEXT

**CORRECTED: this section read SEVEN OF EIGHT and the answer is eight of
eight, and the eighth is the h1.** The first version listed the seven `<h2>`
plate headings and left out `Open the door<br>to Europe.`, which reads
*"Open the doorto Europe."* — the largest type on the site and the page's
own accessible heading. A finding that lists its instances and then states a
count is a finding whose count came from the list rather than from a
measurement.

Every plate heading is typeset by hand with a bare `<br>`:

    Europe<br>is not a checklist.
    One destination from<br>each corner of the continent.
    Europe reveals itself<br>when you move through it.
    One continent.<br>Fifty doors.
    Read the continent<br>differently.
    Every month opens<br>a different Europe.
    Open<br>the door.

`<br>` is a line break and not a word boundary, so the text content of the
second is **`Europeis not a checklist`**. A screen reader announces the
run-together word, and anything resolving one of these as an accessible name
gets the same. It is invisible to every instrument here: the markup is valid,
the heading is present, the contrast is right and the pixels are correct —
**a space immediately before a break collapses at the end of the line**,
which is both why nothing rendered wrong and why the repair costs nothing.

**AND THE MECHANISM IS SITE-WIDE, SO THE REPAIR IS.** Measured on the built
site: **28 occurrences in 26 distinct headings on five pages** — this page's
eight, /journeys' seven, /experiences' seven, /discover's three and /search's
two, plus the manifesto's closing couplet, which is not a heading and reads
*"opens the way.Come discover"*. One of the eight here is composed rather than
typed: `esc(head).replace(" is not", "<br>is not")`, a replace that **deletes
the space it breaks at**, which is the only one of the 28 a search for `<br>`
in the source would have found sitting next to a letter on purpose.

**AND THE CHECK WRITTEN FOR IT UNDERCOUNTED ITS OWN SUBJECT, BY READING THE
MARKUP.** Testing the two characters either side of the break in the HTML
cannot see `Keep<br><em class="lit">looking.</em>` — which reads
*"Keeplooking."* and has a `<` on one side. 26 against a real 28, and the two
it missed were the /discover and /search openings. That is *an instrument a
line break can defeat is reading the file rather than the claim*, which this
repository already records about the projection check, arriving in a check
written about line breaks. `c_break_word_boundary` turns the break into a
sentinel, strips every other tag and tests the TEXT; it reads 19,400 headings
and was proved red by putting one break back.

And underneath it, a hand-typed break in a heading is **typesetting by hand
in a stylesheet that already balances headings** — `text-wrap: balance` is on
them. The break points are art direction worth keeping at 76px; the missing
space is not.

## FINDING 3 — THE OPENING IS 69% OF THE PAGE

91,176 bytes of 131,975. That is 41 country outlines used as clip paths with
a photograph inside each, and it is the one picture on this site no
competitor can reproduce, so the question is not whether to keep it but
whether the page can afford it at that share — `weight.home_kb` exists to
make exactly that arguable rather than assumed, and the invariant register
already records this figure moving 25 → 47 → 109 → 119 → 146 → 122 → 148,
each time with the reason.

## What this inspection does NOT conclude

**"Premium" is not a brief.** The doctrine says so in as many words: it is
satisfied by rounded cards, gradients, shadows and hover animations, and this
product wants none of them. The stylesheet holds two shadows and the
invariant register counts them; there are sixteen type sizes, eight
line-heights, six breakpoints and no seventh.

So the work this inspection authorises is: spend the register the page
already has, fix what is measurably wrong, and tighten the rhythm — and every
change is a measured delta against the baseline in §Baseline below, not a
change somebody preferred.

## Baseline

Every figure below is the homepage as shipped at commit `f89e0b81`, so each
later commit's delta is checkable rather than asserted.

| instrument | homepage, before |
|---|---|
| `monotony.js` | **6%** — the largest repeated component is three journey rows, 9,053 px of a page the instrument reads as 150,883 px. The site's ceiling is 52% and this page has never been near it: the homepage's fault was never repetition |
| `opening.js` at 390 | **72%** of the first screen is picture; the first figure starts at y=178 and the h1 is 60 px at y=264 |
| `opening.js` at 1280 | **85.5%**; figure at y=90, h1 60 px at y=251 |
| `voids.js` | **no band over 90 px with nothing painted in it**, at either width |
| bytes | 131,975, of which plate 01 is 91,176 (69%) |
| photographs | 51 of the register's 826 rows, and three of the eight plates draw none |

**Monotony at 6% is the measurement that says what this page's work is NOT.**
Every other page rebuilt in this arc was a listing — /countries at 63%,
/experiences at 62%, a motion page at 54%. This one is eight distinct
compositions already, so the doctrine's first rule does not apply here and
the second one does: *do not optimise for visual consistency at the expense
of editorial difference.* What the page is short of is not variety of shape.
It is that three of its eight plates hold no picture while the register holds
826.

## PLATE 05 — THE ALPHABET WAS THE LAYOUT, ON THE BAND THAT SAYS ONE CONTINENT

`One continent. Fifty doors.` over fifty country names, A to Z, in five
columns. 2,527 bytes, 51 links, no other structure — and an alphabet is a
finding aid for a reader who already knows the name, which is not the reader
a homepage has.

**FINDING 1 in §above was right that this band draws no picture and wrong
about the remedy.** It read *"it lists fifty country names as text links, and
draws none of the fifty country photographs the register holds"*, which is
true and led toward putting fifty photographs on it. Measured on the built
page, **plate 01 already draws 41 of them** — a photograph clipped into each
country's own outline, 41 SVG `<image>` elements inside 123 clip paths, and
the largest thing on the site. So the fault was never that the pictures are
missing from the page. It is that the page draws 41 of the fifty as pictures
at the top, lists the fifty as names four plates down, and **says nothing
about the difference.**

| | plate 01 | plate 05 |
|---|---|---|
| countries drawn as a picture | 41 | 0 |
| countries linked | 43 | 50 |
| the seven only this band reaches | — | Andorra, Liechtenstein, Malta, Monaco, Russia, San Marino, Vatican City |

**And the reason for the nine is derived rather than typed.** `living_atlas`
refuses a country with no photograph, a travel advisory, no macro region, or
no outline at `min_units=6.0`: six are too small to draw at that scale
(Andorra, Liechtenstein, Malta, Monaco, San Marino, Vatican City) and three
carry an advisory (Belarus, Russia, Ukraine). The clause is **hoisted once
under the list**, not marked on nine rows, which is this atlas's own rule
about never explaining the constraint back.

**AND `living_atlas` CARRIES THE SAME OVERSTATED COMMENT `country_door()`
DID.** *"EVERY COUNTRY THAT HAS A PHOTOGRAPH IS AN APERTURE, AND ALL FIFTY
DO"*, written directly above two filters that remove exactly nine. That
sentence is already recorded in `docs/countries-redesign.md` about the other
function that clips a photograph into a country — **two functions, one
claim, both overstating it by nine** — which is *the code had stopped
matching its own comment*, in the direction that reads as evidence.

### The nine corners, and the measurement that was refused

The fifty are grouped by the nine macro regions — this atlas's own partition,
authored in `data/taxonomy.json`, already the structure of `/countries`. A
grouping is a CLASSIFICATION and is the editorial work; what was refused is a
number.

**Destinations per country run 28 to 1** — France 28, Spain 27, Greece,
Italy and Norway 25, against Monaco, San Marino and Vatican City at one — a
real 28× spread, derived, and **it argues about the wrong subject.** France
holds 28 because somebody wrote 28; `docs/content-report.md` puts this
atlas's content at about a third written. Printing it beside fifty names
publishes a writing-progress artefact as an editorial judgement, which is
/beyond-the-obvious's own finding (*the corner with the most quiet places is
not the quietest corner*) and the reason /countries sizes nothing by it
either.

### Four defects only rendering found

| | |
|---|---|
| `columns: auto 12rem` | packed **five** columns at 1280 and left the fifth holding one group with two thirds of it empty. Nine corners want three columns of three, which is the data's own count rather than whatever a track width produces |
| the first breakpoint was 62rem | so a **834-wide tablet fell to two columns and measured 1,611px against 1,214 at 1280** — a narrower screen paying four hundred more pixels for the same fifty names. That is the fault 834 is on the contact sheet to find, and 52rem is the breakpoint that already exists |
| one column on a phone | 2,481px at 390 against the 900 the alphabet took. Two columns, 1,701 |
| the lede | printed *"50 countries, 130 travel regions"* under a heading that spells **Fifty** — one quantity in two representations on one screen — and both figures are plate 01's own lede. Its second sentence was *"the corner is the link above each list"*, an instruction for something a reader can see. What is left is the one fact the band adds: **a corner is itself somewhere to go** |

### And the class it replaced had exactly one user

`.countrycols` reached one page, so its nine declarations are dead the moment
this band changed — deleted, and provably a no-op rather than a
screenshot-verified one, because nothing in the built site carries the class
and no element matches. **Its two recorded findings are kept as prose**: the
bone-on-bone index at 1.14:1, and *a declared colour is overridden, never
inherited away*, which is exactly the mistake `.dcorner a` can make the next
time this plate's paper moves.

## PLATE 07 — THE CHART'S KEY, PRINTED TWICE, AND A CROWD CLAIM

The lede read *"What is on, and where the crowds are not. The bar above the
line is the fixtures this atlas holds that month; the bar below is how many
countries are in their quieter shoulder."* `year_band()`'s own caption, **250
pixels below it**, reads *"ABOVE THE LINE is what is on. Below it is how many
countries are in their quieter shoulder that month."* The key twice on one
band is this family's own rule broken — *never explain the constraint back*,
and *the proof goes under the thing it proves*.

**And "where the crowds are not" is a crowd claim.** `/method` publishes *"It
is not a crowd measurement. We hold no visitor numbers, no search volumes"*.
A country's shoulder is an **authored seasonal classification**, which is the
editorial work and is legitimate; a statement about where crowds are is a
measurement nothing in this repository holds. The lede states the two series'
extents instead — **150 recurring fixtures and 47 countries recording a
shoulder** — both derived by `year_totals()`, which walks the two fields
`year_band()` walks, including its asymmetry: a fixture counts wherever it is
held and an advisory country's shoulder does not count at all.

`numword` spells under a hundred and uses digits above, so "150 … forty-seven"
is the ordinary editorial rule rather than plate 05's defect, which was **one
number in two representations on one screen**.

## THE CREDIT LINE HAD SIX IMPLEMENTATIONS AND ALL SIX SAID "PHOTOGRAPHS"

Four were the same loop written out four times; two joined the links inline.
The comment on the sixth **counted five of them as a fact rather than fixing
it**: *"the homepage's row of eight, the destination rail, the country and
theme strips, five call sites spelling `sheetcred rowcred`."*

Measured on the built site, **12 credit lines across five pages**, and one of
them credits a single photograph: the homepage's reading band draws the lead
story's picture and published *"Photographs by Jean-Paul Wettstein on
Pexels."* A count cannot assume a plural — already recorded here about a
region holding one destination — and this is the one sentence on the band a
provider's terms require to be right.

`render.photo_credits()` is the one implementation, beside `credit_html()`,
which is single by the same argument: **this is a licence obligation.** The
plural is the number of PHOTOGRAPHS and the list is of PHOTOGRAPHERS, which
are different counts — five pictures by three people is *Photographs by A, B,
C* and one picture by one person is *Photograph by A* — so the names dedupe
and the count does not. 11 plural and 1 singular, derived.

### And the sixth copy was in a function nothing calls

`pages.photostrip()` had **no caller**, and `.pstrip` / `.pstile` / `.psname`
reached **zero pages** — on the build before this one and on every build since
`ed_strip()` took that job.

**It was invisible to every instrument here, including the one written for
exactly this.** The dead-rule scan judges a rule on the pages it loads, so a
rule whose class no page emits is not reported dead — *it is not reported at
all*. What found it was converting the six copies into one: five of the call
sites were on a page and the sixth was not. Removed, function and rules, with
the finding kept in the stylesheet where the rules were.

Two content changes across 1,033 rebuilt files, which is what a refactor of a
shared line should produce: the singular credit, and the year lede.

## PLATE 03 — "EACH CORNER" WAS FIVE OF NINE, AND THE LEDE RANKED THEM

`One destination from each corner of the continent.` over a feature: one lead
photograph and four rows. **`picks[:5]`** — a cap written when five was what
the register could fill, reading as a statement about the layout. That is the
`[:8]` failure plate 02 already records one band over, on the band whose
heading *is* an extent.

Measured: **all nine corners hold a photographed, non-advisory destination** —
the Mediterranean 94 of them, Eastern Europe 2 — so the set the heading
promises exists. The cap is gone and the composition takes the count.

**AND THE LEDE MADE A RANKING CLAIM WITH ITERATION ORDER BEHIND IT.** It read
*"Every one of these is the first place this atlas would send you in its
corner of the continent."* The actual rule is: the first destination in each
corner, **in whatever order the index is stored**, that the register holds a
photograph of. Tirana is not this atlas's recommendation for the Adriatic; it
was alphabetically first among the photographed ones. Nothing in this product
ranks destinations — `/for-businesses` publishes that there is nothing in the
index that could carry a boost — and a sentence on the homepage saying
otherwise is the claim that refusal exists for. The lede states the real rule,
which also states a real property: **the set moves as the library fills.**

**And the order is the taxonomy's now, not the index's** — the Nordics first
and the Caucasus last, which is the order /countries and the corner index on
plate 05 already read.

### The label named a country on the band whose claim is a corner

Every row said ESTONIA, IRELAND, BELGIUM — so the one claim the band makes was
the one thing a reader could not check. The kicker is the corner now, nine
distinct, which is this atlas's own standard: *the count on the tile is the
number of dots on it, so a reader can check.*

### A refused repair, with its trigger

| | 1280 |
|---|---|
| the lead | 695px |
| the list | 969px |
| **empty page under the lead** | **274px** |
| the lead's rendered picture | 729 × 544, aspect **1.340** |

Before the change the imbalance ran the other way — four rows measured 484px
against the lead's 695, so 211px sat empty beside the LIST — and it is 274
now. The obvious repair is to raise `.featlead img`'s `max-height: 34rem` so
the lead column grows into the gap, and **it is refused**: that cap is what
crops a 4:5 rule into a 1.340 box, so raising it changes the crop box of an
**undeclared** surface. `destination-hero` declares one container,
`.placeband-art`, and already carries `unmeasurable` with a trigger on it;
`.featlead` is a second surface for the same 313 photographs and the register
declares one. *A photograph is cropped by every surface it appears on and the
register declares one* — the open gap this repository already records, and
widening it on the homepage is the one axis `c_photo_safe_area` exists to
guard. **Trigger: declare `.featlead` as a second container for `city:` and
measure it, in the same commit as any change to its crop.**

## PLATE 04 — TWO FIGURES ABOUT ONE JOURNEY, STANDING ABOVE THREE

The head printed **`2,173 km` / `7 STOPS`** with the note *"Measured on Arctic
to the Baltic"* over a band of three journeys, on a site that holds
**seventeen**. A number that is not the set's own extent reads as one — the
/europe-in failure, where the index stated the 319 its queries run against and
never the 12 queries in front of the reader.

**And the journey those figures described was not necessarily on the band.**
They came from `data["journeys"][0]`, the first journey in the FILE, while the
rows are the first three that carry a photograph of a stop and hold at least
two stops. Those coincide today and are computed independently, so the head
could have read *"Measured on X"* about a journey a reader cannot see.

Both figures are the whole set now — **31,213 km across every route** and
**17 routes** — and the straight-line disclosure is kept, because it is the
rule `checks.py` asserts on every page that prints a hop and the figure is
what it is about.

**And the selection is stated rather than implied.** Measured: **all seventeen
journeys qualify** for the row — every one holds two stops and a photographed
one — so three is a cap and not a filter, and the lede says *three of them
below, in the order this atlas holds them.*

**The first draft then put the count in the figure and again in the lede** —
`17 Routes` over *"Seventeen routes"* — which is plate 05's own defect, made
again in the commit that cites it. The figure carries the extent; the sentence
carries the selection.

### And the assertion that broke pinned three captions

`ux-audit.py` §7 required the literal **`Straight-line distance`**,
**`Countries`** and **`Stops`** — the figure captions the band happened to
carry — so it went red the day those figures stopped describing one journey
and started describing all seventeen, which is *more* of what it protects.
**The fourteenth assertion here to pin a shape rather than a promise, and the
first where the shape was a figure's caption.**

The promise is that the band prints a distance and says what kind of distance
it is: every distance in this product is a haversine between two coordinates,
`checks.py` refuses a mode claim anywhere, and a kilometre figure with no
qualifier is the one number a reader could act on and be wrong about. It reads
`" km"` and `"straight"` now, in either order and whatever the captions are
called — **proved red by deleting the qualifier**, which named the page and
the missing needle.

## THE HERO'S SEA NAMES RENDERED AT FIVE PIXELS, AND A THIRD FAMILY AT SIX

The hero's fifteen country names come off below 44rem exactly as the
stylesheet says they do — `--t-lg` is a length in a 1,120-unit viewBox, and at
390 that is a third of a pixel per unit. Measured at 390 with the browser's
own laid-out boxes, **five labels were still drawn, all at 5 pixels**:

    NORTH SEA · MEDITERRANEAN SEA · BLACK SEA · TYRRHENIAN SEA · BAY OF BISCAY

They sit in `.lyr-water-labels`, a **second layer** the phone rule never
named — it hides `.lyr-labels` — and `.seaname` is `--t-xs`, smaller than the
countries' `--t-lg`, so the family that was left behind is the one that
renders smallest. That is this repository's own sentence about `.peakname`,
`.fname` and `.sname`: *a label family added after the two passes that fix
exactly this took neither.*

**And sweeping every SVG label on 27 pages found a third.** `.mmlabel`, on the
nine macro region maps, is `font-size: 15px` — a fixed px inside a scaled
viewBox — written **directly beneath** `.countrymap .rlabel text`, which takes
`calc(15px / var(--z))` and carries the paragraph explaining why. It rendered
*Denmark*, *Finland*, *Iceland*, *Greece*, *Portugal*, *Belgium* and *France*
at **6 pixels** at 390. Above 44rem `--z` is 1, so the fix is provably the
same 15px it always was: /discover/nordic is **byte-identical at 1280** and
differs only at 390.

### And the check for it asked about one class on a site with six families

`figure.minimap text.minilabel` is the family the 9px floor was written for,
and it cannot see `.cname`, `.seaname`, `.mmlabel`, `.peakname`, `.fname` or
`.sname`. The sweep now asserts the promise on **every `<text>` a map draws**,
whatever its class, at 390, measured by the browser's own laid-out box rather
than by a font-size — because a font-size in an SVG is in user units and that
is the whole family of defects. 31 labels across 15 pages, with its own reach
floor, because *a check reading zero looks exactly like a healthy one in the
column of counts.*

## AND ONE THING WAS MEASURED AND NOT CHANGED: THE PLATE MARK ON A CENTRED BAND

Seven bands across six pages centre their composition and leave the plate
number at the left — `/` act8, `/discover` discover-end, `/journeys`
the-road-ahead, `/experiences` the-door, `/plan` compose, `/stories` read-one,
`/my-europe` build, drifts of 82 to 456 pixels against a head with equal
margins either side.

**The first measurement of this was wrong and said eleven.** It compared the
mark's x against the head's x, which reports a *feature* band — where the head
sits in the second track and a mark at the band's left edge is correct — as
the same defect. Testing for equal margins gives seven.

**And seven is a taste, not a defect.** A plate mark is a folio: a page number
in a book does not move because the page is centred, and all 71 marks on this
site sit at the same x. Forcing them to follow the composition is optimising
for visual consistency, which the doctrine's second rule refuses. Recorded
with its measurement and left alone; the trigger is somebody deciding the mark
is a caption rather than a folio, and then it is **one** declaration of "this
plate is centred" read by both rules — not the six composition classes that
each centre in their own way today.

## THE INSTRUMENT THAT CLOSED FINDING 1 WAS COUNTING A PICTURE NOBODY CAN SEE

`tools/opening.js` measures how much of the first screen is a picture, and it
is what `docs/first-class-audit.md` closes its Finding 1 on. It counted every
`figure, svg, img, picture…` whose rect intersects the viewport.

**The window plate's photograph is `position: fixed`** — that is the whole
mechanism of the plate, and it carries a paragraph about six CSS properties
that silently kill it — **and a fixed box's client rect is the viewport
whatever the scroll.** So at scroll 0 the probe read a 1280×720 photograph at
y=90 on the homepage, while the band holding it begins 1,818 pixels below the
fold and clips it with `clip-path: inset(0)`.

| the homepage's opening | before | after |
|---|---|---|
| at 1280 | 85.5% | **50.5%** |
| at 390 | 72% | **4.4%** |

**One family of thirty moved**, which is what says the repair is surgical
rather than a new reading of the site: the probe now intersects each element
with every ancestor that clips — a `clip-path`, or an overflow that is not
visible — which is the honest reading of *what a reader gets*, and a fixed box
inside a clipping ancestor is bounded by it exactly as a static one is.

**And the correction hands back a real finding about this page.** At 390 the
homepage's first screen is the masthead, the plate mark, a 60px headline, a
three-line lede, a link, a rule and four counts — **not one pixel of
picture**, on the most-seen page of a product whose own mandate says a page
that is type to the fold is the thing to fix. The hero's drawing begins at
y=812 of an 844-tall screen. That is the next commit, not this one: this one
is the instrument, and mixing the two would mean measuring a change with the
device that was wrong about it.

## AND STACKED, THE CONTINENT GOES FIRST

With the instrument repaired, the homepage at 390 measured **4.4% picture**:
the masthead, the plate mark, a 60px headline, a three-line lede, a link, a
rule and four counts, with the drawing beginning at y=812 of an 844-tall
screen. The page whose own sentence is *the homepage leads with Europe* led
with type at the width most readers are at.

Below 62rem the two columns stack, and DOM order is reading order, so the
drawing was last. `.sheet-door .doorside { order: -1 }` inside that block —
`order` rather than moving the markup, because the tab order and the
accessible reading order should stay the composition's: the h1 still names
the page before the picture is described.

| the homepage at 390 | before | after |
|---|---|---|
| picture share of the first screen | 4.4% | **31.4%** |
| the first figure begins at | y=812 | **y=264** |
| the h1 begins at | y=264 | y=513 |

**Side by side the type is already first for a reader of a left-to-right
page**, so nothing above 62rem changes — proved rather than argued: the
homepage at 1280 is **byte-identical** before and after, and only 390 differs.

## PLATE 02 — THE WINDOW'S CROP WAS THE ACQUISITION'S DEFAULT, AND IT WAS SKY

**A fixed picture cannot be judged from an element screenshot.** `position:
fixed` paints against the viewport, so shooting the band gives the photograph
wherever it happens to be at scroll 0 rather than where a reader meets it —
the same mistake `opening.js` was making two commits ago, in the instrument
rather than in the page. Scrolled to and shot as a viewport, the window reads
properly.

Measured on the rendered `<img>`:

| viewport | box | source | cover crops | keeps |
|---|---|---|---|---|
| 1280 | 1280×720 (1.778) | 1280×853 (1.501) | height | 84% |
| 834 | 834×469 (1.778) | 834×556 (1.500) | height | 84% |
| 1920 | 1920×1080 (1.778) | 1920×1280 (1.500) | height | 84% |
| **390** | **390×488 (0.800)** | 389×259 (1.502) | **width** | 53% |

So the three wide widths crop top and bottom and the phone crops left and
right, and **a vertical focal anchor is a no-op at 390 by construction** —
which is why the first render after the change looked identical there and
would have been read as the change not working.

All 826 rows carry the acquisition's default `focal: [50, 50]`, and at 16:9
from a 3:2 source that centres a frame whose subject is in its lower third:
the 1280 window was about 300 pixels of sky over a 105-pixel band of city.
`[50, 82]` quantises to `f-cb`, keeping the bottom 84% — **the city band grows
to about 165 pixels and the picture reads as a city seen from above rather
than as a sky with a city under it.** The phone is untouched, as the
arithmetic says it must be.

**This is the step the pipeline names as the one it loses.** The Media Desk's
own note says a green run merges itself and *nothing looks at the photograph
inside the rendered page before it is live*; a focal anchor is exactly what a
photo editor sets after looking, and the register had never had one set. It is
the first non-default `focal` in 826 rows.

## THE BROWSER SUITE'S ONE FAILURE WAS PLATE 05's, AND IT NAMED THE WRONG CAUSE

11,371 browser checks, **one failure**, and it was mine:

    1 heading(s) end on a line under a third of their widest at 1280:
    / "The Nordics" 111/363px. text-wrap: balance is on every heading and
    something is overriding it

`text-wrap: balance` was never overridden. The corner heading is **one line**
of 111 pixels, and the 363 the check read as a first line is a **box**:
`.dcorner a { display: block }` was written for the fifty country links and
also matched the anchor inside each corner's own `<h3>`, so the heading's link
blockified to the full column width.

| | before | after |
|---|---|---|
| The Nordics | `[363, 111]` | `[111, 111]` |
| The Caucasus & the Bosphorus | `[363, 286]` | `[286, 286]` |

**So the check was right that something was wrong and wrong about what** —
the third time in this arc, after /journeys' *"balance being overridden"* and
the masthead-versus-words report. What it measured as a second line was the
blockified anchor's own rect.

And the defect was real and not only an instrument artefact: the heading's
hover and its focus ring spanned the whole 363-pixel column rather than the
words. `.dcorner > a` is the fix — **the child combinator is load-bearing**,
because the country links are the direct children and the heading's anchor is
not.

### And the re-run found the next one, 637 lines from the note that forbids it

The heading-line failure was gone and the dead-rule scan named
**`.dcorner h3 a {color}`**: `color: inherit` restating `a { color: inherit }`,
which is the global rule at the top of the file. The stylesheet **already
carries that exact note**, written for a different band:

> *No `color: inherit`: `a { color: inherit }` is the global rule at the top
> of this file, and restating it here is the redundancy the dead-rule scan
> exists to find — a declaration that matches its element and changes
> nothing, which reads as a decision and is not one.*

637 lines above the rule that ignored it. *A rule recorded is not a rule
inherited*, in one file, in one session, by one hand.

**The declaration goes and the rule stays.** The scan names declarations, not
rules, and deleting the whole rule is exactly how the `.picstory` repair put
an underline through seven story headlines — `text-decoration: none` is doing
real work here. Proved: plate 05 at 1280 is **byte-identical** with the
declaration and without it.

## TWO UNPROVENANCED ORIGINALS, AND THE AUDIT THE OWNER ASKED FOR

Two Pexels photographs were uploaded straight into `photographs/` —
`pexels-itsehsanh-18442653.jpg` (2,655,622 bytes, 5726×3817) and
`pexels-mikebird-6100149.jpg` (5,165,366 bytes, 6000×4000). `checks.py`
refused both in the first run:

> *an original with no row has no photographer, no source, no licence, no
> date and no hash — delete it, or acquire it properly so the register
> carries the evidence*

**The gate did exactly its job and it was not weakened.** They are removed
from the candidate set at the owner's direction; the supported route is
`photograph.yml` fetching each BY ID (18442653, 6100149) where the key is, so
the register carries the photographer, the source page, the licence, the date
and the SHA-256 of the bytes **as served**. A hash of an uploaded copy is not
that, and nothing here can verify any of it: the sandbox proxy answers 403 for
pexels.com.

### The visible-metadata audit

Measured on the built homepage: **four visible provenance lines and 14
outbound links to pexels.com.**

| plate | line |
|---|---|
| 02 the window | `Photograph Ana Kenk · Pexels` |
| 03 the places | `Photographs by Charlie Jordan, Argo Allvee, …` |
| 04 the crossing | `Photographs by Efrem Efre, Jérémy Glineur, JENNY DILPHY on Pexels.` |
| 06 the reading | `Photograph by Jean-Paul Wettstein on Pexels.` |

**None of them was introduced by this arc.** Home 04 replaced six
implementations of that line with one (`render.photo_credits`) and added no
surface; plate 03's line grew longer because Home 05 took the band from five
photographs to nine, which is more names on an existing line rather than a new
one. The hero itself carries no credit — that was removed at an earlier
direction and is recorded.

### And they are NOT removed, because the owner's own exception covers them

The instruction says remove visible provenance *"unless an explicit
legal/editorial requirement for that particular asset requires visible
attribution."* There is one, recorded in this repository's own licence gate
with the verbatim quote behind it — `docs/data-licenses/photo-providers.json`,
`pexels.attribution`:

> **A prominent link to Pexels on any page showing a Pexels photo**, and the
> photographer credited as "Photo by \<name\> on Pexels" linking to that
> photo's page on Pexels.

and the quote it was read from:

> *"Whenever you are doing an API request make sure to show a prominent link
> to Pexels … Always credit our photographers when possible (e.g. 'Photo by
> John Doe on Pexels' with a link to the photo page on Pexels)."*

Every photograph on this page is a Pexels photograph, so the exception applies
to all of them. Removing the four lines would put the product in breach of the
terms its own gate records — which is the opposite of *do not weaken the
licence gate*. **Recorded and referred rather than acted on**: the design
question (a supplier's name on the composition) is real and the answer is not
mine to pick, because it has a licence consequence.


## Home 14/30 — the window says its own words, and the wall lost a screen and a quarter

`margin-top: 124svh`. That is what stood between "Europe is not a checklist."
and the photograph it is about, and the reasoning written above it was right
about a caption and wrong about this: *the label arrives after the work … a
label level with the picture would be a caption on a card.* True of a
caption. This is not one — it is the page's closing argument, and an argument
separated from its evidence by 1,116 pixels of white paper is two bands where
one was meant. Measured on the built page at 1280x900 the plate ran **1,622
pixels** for one photograph and four lines of type.

It is a **declaration** now, which is a scale `docs/non-home-redesign.md`
already declares and this page had spent nowhere: type over a picture behind
a scrim that makes the contrast a property of the design rather than of the
photograph. 1,622 → **1,353** at 1280, 1,492 → **1,275** at 390, and the
whole document 10,334 → 10,066.

**The scrim is a flat wash the size of the words, with the ramp above it.**
A gradient under the type is weakest exactly where the type runs out — the
diagonal-scrim failure /plan already records — and the alpha a glyph is
painted over would then depend on how many lines the sentence happens to
take. So the box the words are in carries the full 72% and the ramp is a
separate strip above it, in five stops because a two-stop ramp has a crease
at each end and the eye draws a line along it. The arithmetic is `.credit`'s
own rather than a second decision about one thing: the worst case a
photograph can present is a white frame, graphite at 72% composites over
white to `rgb(76,83,82)`, and bone on that is **6.90:1** whatever the picture
turns out to be.

**AND THE PICTURE STANDS STILL BY STICKING RATHER THAN BY BEING FIXED.**
`position: fixed` inside a `clip-path` stacks two undefined-in-practice
behaviours on one composition. The first is already written down: six
properties — transform, filter, backdrop-filter, perspective, will-change,
contain — each make an ancestor a containing block for fixed descendants, so
one of them anywhere between `<body>` and the picture turns the window into a
panel that scrolls, silently, with every box still the right size in the
right place. The second is worse because it is not on that list: **the CSS
Masking specification says a `clip-path` other than `none` itself creates a
containing block for fixed descendants.** Chromium does not do that; other
engines do. So the one element this composition requires to carry a clip is,
read strictly, the element that cancels the positioning it exists to clip —
and every instrument in this repository runs in Chromium, which is the half
where it works.

`position: sticky` is defined identically everywhere, is clipped by an
ancestor's clip-path exactly as any in-flow box is, is constrained to its own
container by the specification rather than by a guard, and needs no
containing-block reasoning at all. The opening is an in-flow box again, the
standing frame is one viewport tall and sticks to the top of it, and the
picture is centred inside that.

**The phone box went 4:5 → 2:3, and that is the one thing this cost.**
Measured at 390x844 with the words on the photograph: the picture was 390x488
inside an 844-tall opening, so **356 pixels of the first screen were the
mount** and the declaration covered 330 of the 488 that were left — 158
pixels of visible photograph, on the one full-bleed picture on the page. A
taller box fixes both ends at once: 390x585 leaves 129 of mount either side
and 295 of photograph above the words. The crop arithmetic follows honestly
rather than being left describing the old box — container **0.667–1.778**
against a 1.5–1.9 source is a guaranteed frame of **29.6%** where 0.800 gave
35.5%, against a floor of 12%. Re-measured in Chromium at the same twenty
viewports the browser sweep uses.

**And the plate mark was near-black on the opening.** `.actmark` is `--ink-3`
on the wall's own paper, which is right on every other plate and wrong on the
only one whose first screen is the opening rather than the wall: it sat at the
top of the band, at z-index 2, over graphite. Nothing counts a mark that is
the colour of what is behind it.

## Home 16/30 — the masthead is furniture, and the footer is the bound edge

Two components, both on all 1,032 pages, both asked for by name: *give the
menu bar a premium colour and design. Also do same for the footer. Make the
footer iconic.*

### The masthead was a rule with words above it

`background: color-mix(in srgb, var(--paper) 92%, transparent)` over a page of
`--paper`. So the only thing separating the first component every reader meets
from the document under it was a one-pixel hairline. That was a **correction
rather than a design**: the band used to be solid pine, which was measured as
the largest single reason twelve families read as one page — the first 63
pixels identical and the most saturated thing in frame whatever changed
underneath — and the fix was to stop spending a *saturated* colour there, not
to stop having a surface. `--paper-2` is the next rung of the same ladder, a
step of 1.09, bound per world, neutral, and it costs the family accents
nothing.

Four more moves, and every one is rules and space rather than a box:

| | |
|---|---|
| the edge | a **reveal**, not a border: the wall's face and a fine line just inside it, which is what every aperture on this site draws at its cut. One hairline says *a border*; two say *an edge* |
| the air | 58 → **82** at desk width. 58 pixels is a toolbar; this is the masthead of a publication, and the h1 under it is 76 |
| the mark | 1.05em → **1.24em**. At the same optical size as the word beside it, the door read as a decoration in front of a name rather than as a mark and its name |
| the tools | a hairline before Search and My Europe. Seven rooms and two tools are not the same kind of thing, and the bar set all nine in one weight at one size with one gap |

**Two things were built, measured and taken out again.** Centring the sections
on the page: `space-between` puts the nav wherever its neighbours leave it — at
1280 it ran 309 to 921, so its middle sat at 615 against a page middle of 640 —
and three tracks fix that exactly. They also give the middle track only what
the two `1fr` cheeks leave, so at 960 the row wrapped and the bar went 82 →
114, and at 1024 → 95. **A two-row masthead across every laptop and every split
window is a real cost; twenty-five pixels of optical centring is not.**

And the air was first written as `@media (min-width: 60rem)`, which is wrong by
one pixel: **`max-width: 60rem` and `min-width: 60rem` both match at exactly
960**, so the padding landed on top of the two-row grid on the one width where
the two-row grid is what is wanted — 90 became 114. The narrow block already
exists and already wins at equal specificity by coming later, so the air goes
in the base rule and that block takes it back.

**The row had under nine pixels of slack at 1024 and nothing knew it.**
Measured before: 58 pixels, one row. After a mark went up a tenth of an em and
a hairline appeared: 122, two rows. A layout whose one-row-ness depends on
nobody ever adding a glyph is not a layout, so the gap between the three groups
paid for it — `--s6` to `--s5` is sixteen pixels back across two gaps, and the
groups are still further apart than the items inside them, which is the only
thing that gap has to say. Measured at ten widths from 320 to 1800: no
horizontal overflow anywhere, and every width below 1024 is byte-for-byte the
height it was.

### The footer is a colophon now

A sentence, twenty links and a legal paragraph is the footer of any travel
product, and that is exactly what the last band of every page was: competent,
anonymous, and the one place on the site where nothing said what this is.

A publication closes on its own name. The band is the document's **bound edge**
— the mark at scale, the name in the display serif, the one fact a colophon
carries, and the lists quiet beside it — and it is **graphite**, because this
atlas's whole reading of a surface is *light wall, dark opening* and the end of
a document is the other edge of the same idea. The top edge takes the
masthead's reveal upside down.

**The tokens are bound rather than named**, which is `.sheet-paper`'s own rule:
a `var()` resolves where the declaration lives, so a footer that set `color:
var(--ink)` would paint bone on bone in one preference and near-black on
graphite in the other. On the five INTELLIGENCE pages this changes nothing,
which is correct — a colophon is a colophon on every page of the edition.

**The one fact is DERIVED.** *50 countries · 130 regions · 319 destinations ·
255 places · 197 experiences · 17 journeys*, counted on every build from the
same documents the pages are built from, because a figure typed there is the
figure that was true two hundred destinations ago — a mistake this repository
has already made on a live page. The import is lazy and the answer is cached:
`data.py` does not import `render` and `render` does not import it at the top,
so nothing here can become a cycle, and `page()` is called 1,032 times a build.

**And the extent broke at 536 pixels inside a 1,232-pixel band**, because `p`
carries the prose measure and this is a list of figures. `max-width: none` is a
declaration rather than the absence of one — the same fault this stylesheet
already records about a credit line and about a middot list of place names.

## Home 17/30 — the places leave the column, and the crossing draws the crossing

Two bands, both transformed against a composition the owner supplied.

### 03 · the places

The feature scale is 1.35 against .65 *so the photograph is the subject*, and
the photograph was still a picture inside a 76rem measure with its caption set
underneath — **which is a large card**, and a card is the shape this band
already stopped being once. A band whose subject *is* a photograph lets the
photograph leave the column.

- The grid bleeds to the viewport and the lead runs to the left edge.
- The label sits **on** the picture, taking plate 02's declaration arithmetic
  rather than a second decision about one thing: a flat 72% wash the size of
  the words with a five-stop ramp above it, which composites over the worst
  case a photograph can present — a white frame — to `rgb(76,83,82)`, where
  bone measures **6.90:1** whatever the picture is.
- `Explore <place>` is a **span**, not an anchor. The tile is already a link
  and an `<a>` inside an `<a>` is not nested — the parser closes the first one
  — which is how /stories lost the two links Pexels' terms require.
- The list beside it gains a third line, and it is the **country, not the
  summary**. This atlas writes a destination's summary as a sentence rather
  than as a tagline (Copenhagen's is 97 characters), so eight of them in a
  300-pixel column is four lines apiece and the list stops being a list.
  Clipping is not the alternative: `c_cut_word` refuses any element holding
  more text than it shows. The country is short by construction, always
  present, and the one thing the row does not already say — the kicker is the
  macro region, so *THE MEDITERRANEAN / Andorra la Vella / Andorra* carries
  three facts.
- The head over the list states its own extent, derived, and the band closes
  on the one link shape this page has.

**The bleed is a length and never a percentage.** The classic `calc(50% -
50vw)` cannot be handed to a child: a percentage inside a custom property is
substituted textually and resolved against whatever element eventually *uses*
it. So `.galwrap` carries `--edge: max(--s5, (100vw - 76rem) / 2)` — checked
against the built page at 32 (1280), 192 (1600), 392 (2000) and the gutter
below that — `margin-inline: calc(-1 * var(--edge))` bleeds, and the same
value as padding on the other column puts it back on the measure.

**Two things from the supplied composition are refused.** The prev/next arrows
and the `01 — 08` counter are a carousel, and this page's only `<script>` is
the inert JSON-LD block: a control that does nothing is `data-rotate` again,
and this repository has already shipped 232 bytes of copy waiting for a
rotator nobody wrote. And the faint continent behind the headline is the
signature as wallpaper — plate 05 draws the atlas on this same page, and
*eleven doors on one page* is the rule that stopped.

### 04 · the crossing

This band's subject is **movement and it drew none**: a headline, two figures
and three rows, with the one thing that makes a journey a journey — the ordered
line across the continent — nowhere on it. That is the finding that rebuilt
/journeys, still standing on the homepage.

It is two columns now. The right one is the **lead route drawn over a
photograph of one of its own stops**: the picture bleeds to the right edge and
runs the full height of the band, and the line over it is `constellation()`'s
own geometry framed on that journey's extent. A decorative squiggle would be
authoring a measurement, which is the one thing this repository never does.

- **The photograph is a stop no row is already drawing.** *One record, one
  picture* is a rule about a record; one picture twice on one screen is a
  different fault with the same shape, and the band has three thumbnails and
  one column to fill.
- **The route has no land under it.** A translucent silhouette over a
  photograph of one of the route's own stops is two pictures; the line carries
  a graphite casing and a bone core, which is the rule `route_line` was written
  for — no single colour reads on a ground you cannot predict.
- The rows gain an index and the journey's own sentence. A journey's summary is
  authored to be read, unlike a destination's, which is why it is refused one
  band up.
- The caption states the route, its straight-line distance and its stop count,
  all derived.

**The bordered button is refused.** Border, fill, radius and shadow each say
*separate object, placed here by a system*, and this page has no boxes at all —
which is why the one link shape here is a drawn mark, a rule and a tracked
label. The close takes that shape.

## Home 18/30 — the seven the browser found in plates 03 and 04

The static suite, the invariant register and both audits were green on the two
recomposed bands. The browser suite was not, and every one of the seven is a
class of fault this repository already has a name for.

| | |
|---|---|
| `.featname {display,color}`, `.crossart > :is(picture,img) {display}`, `.crossroute .constel {display}` | **a grid item is blockified by the layout**, and `color` restated what `.featsay` already binds. The seventh, eighth and ninth dead `display` on a photograph container found here, each in the first run where a photograph actually rendered in it |
| the window picture moved 230px at 1280 and 261px at 390 | the measurement, not the picture. The wall carries the plate mark and the aperture is cut BELOW it, so a scroll to the top of the *band* begins 230 pixels before the sticky box engages — and the picture travels those 230 with the wall, exactly as it should. **The aperture is where the standing starts**, so the check scrolls the clip host |
| `<a>` "The Nordics / Copenhagen" at 1.14:1 | **an element that paints no text of its own may not claim an ink.** Every word inside the tile is in `.featsay`, which binds bone on its own scrim; bone on the anchor as well made an element whose ground is the wall's white claim a colour it never paints. That is the plate mark on the opening one band over, in the run that fixed it |
| the homepage scrolls sideways by 15px at 320 | the journey rows. The index is `aria-hidden` decoration and its track plus its gap is **56 pixels of a 288-pixel phone** — the order is already the order, so the ordinal comes off below 44rem and the picture and the words keep the row |

Bisected rather than guessed: hiding each band in turn named `.sheet-crossing`,
then each element in turn named `.jrows` and all three `.jr` rows. The only
elements whose boxes reached past 320 were `<use>` clones inside an SVG, which
is clipped and contributes nothing — *the eye finds a defect and it does not
confirm one*, applied to an overflow probe.
