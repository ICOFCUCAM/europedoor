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

## Home 19/30 — the window is fixed again, and the studio gets a third state

### The window, to the owner's contract

`position: sticky` was my substitution for `position: fixed`, made against a
Firefox rendering I could not reproduce in a sandbox that has only Chromium.
The owner's specification is explicit and it is restored, with its own
constraints written on the rule rather than in a document: `clip-path:
inset(0)` on a band of at least 110svh, `position: fixed; inset: 0` on the
picture, `position: relative` on the copy, `svh` and never `vh`, the tint
inside the fixed element, no JavaScript, no scroll listener, no
`background-attachment: fixed` — and **nothing on the band, the picture or
anything between them may set `transform`, `filter`, `backdrop-filter`,
`perspective`, `will-change` or `contain`**, each of which makes a containing
block for fixed descendants and kills the effect in silence.

Measured: the picture's top moves **0 pixels against a 500-pixel scroll**, at
1280 and at 390.

**The copy scrolls and the picture does not**, which is the half the first
version had backwards: `.shotsay` was inside the fixed element, so the
sentence stood still *with* the photograph — a caption on a poster rather than
a window being passed. And the scrim gained a ramp at both ends: a flat wash
with a hard lower edge is invisible while it is fixed off the bottom of the
screen and becomes a cut across the picture the moment it moves.

**End to end costs most of the crop guarantee, and that is stated.** `inset: 0`
makes the container the raw viewport — 0.356 to 3.125, a guaranteed frame of
**9%**, below the 12% this repository refuses and the reason a bounded aperture
was measured in the first place. Flooring the height at 45.45vw caps the box at
2.2 while it still fills the viewport at every shape: **0.356–2.200, 12.8%**.
That is a thin margin and any change that lets the box grow past 2.2 puts the
purpose under the floor, where `c_photo_safe_area` will say so.

### Three states, so the studio is not governed like production

`data/images.json` is strict on purpose and it had started to constrain the
**studio** rather than only the product: a photograph the owner supplies to
direct the design cannot be acquired by id from a provider, so the strict
answer was to refuse it — and refusing it means the person deciding what this
site looks like cannot put a picture on a page.

| state | where it lives | what it needs | what a reader sees |
|---|---|---|---|
| **design asset** | `data/design-assets.json` | a file, an alt, a hash, a source type, a note | a photograph, and nothing else |
| **candidate** | a design asset with a purpose written against it | the purpose's own numbers | — |
| **production asset** | `data/images.json` | photographer, source, licence, date, SHA-256 | the photograph and its credit |

Nothing about the production gate moved. What is new is that the two registers
cannot be confused: `data.py` **refuses a design row that carries a
photographer, a licence, a source or a provider** — a design asset is not a
half-filled production row — and `c_design_assets` asserts the file is the
bytes it claims, that it is in neither the production register nor its hashes,
and that no page renders it within 1,200 characters of a credit, a licence or a
provider's name. Proved red on a design row claiming a licence.

**The owner's London photograph is the homepage window.** It ships at
`design.<hash>.jpg`, because `/assets/` is served `immutable` for a year and a
stable URL under that header is a file the browser never asks about again. One
file, no ladder: `derive.py` writes the provenance while it builds one, and
running it here would make a design asset look like a production one on disk.

**And the displaced credit came off.** The window drew the owner's photograph
and printed Ana Kenk's name under it — a false attribution, which is worse than
clutter. The credit belongs to whatever is on the page. `c_photo_published`
is told about the displacement rather than left to trip over it: while a design
asset stands in for a key, the stand-in has to be on that page and the
registered photograph is held rather than lost.

### The three criticisms

- **Section 2 end to end** — done, above.
- **Section 3, the image does not align with the text.** Measured at 1280: the
  two columns below are 797 and 411 and their tops and bottoms already aligned
  exactly; the HEAD was one column, so the headline ran 64→887 and the
  standfirst sat under it, both ending at a width that relates to neither
  track. The title takes the picture's track and the standfirst takes the
  list's, so the band reads on two columns throughout. The gap and the ratio
  are `.feat`'s own values rather than a second pair.
- **Section 4's route on the right-hand image** — removed, with its skin, on
  the owner's call. It was real projected geometry and it was still a diagram
  drawn over a landscape that is a stop on the same route, with the row beside
  it naming every stop in order.

**And two true findings between them deleted a value.** `color: var(--bone)`
came off `.featlead` because the anchor paints no text of its own and read
1.14:1 against the wall; `.featname`'s own `color` had come off the commit
before as a restatement of the anchor's. Between them the place name inherited
the page's near-black onto a dark scrim over a bright building and was not
there. The element that paints the scrim owns the ink on it.

## Home 20 — the footer is the other side of the door

The brief is that the masthead and the footer are two ends of one
architectural object: the header is the entrance and the footer is the far
side of the same door, sharing a ground so the site has a recognisable
frame — *same colour, not same weight*. The header is quiet, precise and
navigational; the footer is large, editorial and conclusive. **This commit
is the footer half.** The header's ground is the next one, because renaming
the masthead's sections without the fields behind them would be worse than
what exists.

**FIVE COLUMNS, AND TWO OF THEM ARE NOT LISTS OF LINKS.** That is the whole
composition rather than a wider grid: four identical lists side by side is
the 280px card grid this site already threw away, one component down — the
shape of the data as the layout. THE ATLAS is the geographic field, THE
JOURNEY is what a reader does with it, GO FURTHER is a register of external
services with a line under each, EUROPEDOOR is the house, and STAY WITH
EUROPE is a statement with three ways back in. The tracks are unequal for
the same reason a feature is 1.35 against .65.

**GO FURTHER IS A REGISTER AND NOT A LIST OF LINKS, BECAUSE EVERY ROW IS A
HOST.** `data/go-further.json` declares seven services — flying, buying a
home, moving, a car, digital privacy, Africa, selling a company — and
`checks.py` pins the set of external hosts this site may navigate to against
that file and `data/stay.json`. A new outbound destination cannot appear
anywhere without a row, and every one of these links carries
`rel="nofollow noopener"` and opens in a new tab. **They are deliberately
not in the primary navigation**: EuropeDoor's subject is the continent, and
seven commercial verbs in a masthead turn a European atlas into a
marketplace navigation bar.

**A SERVICE WITH NO DESTINATION DRAWS NOTHING.** `fly` is declared with
`state: "unbuilt"` and no partner, so the column renders no row for it — a
row that looks like navigation and leads nowhere is the chip that filters
nothing and the `data-rotate` attribute nobody reads. The declaration stays
in the file so the absence is written down, and `c_go_further` asserts both
halves: every live service reaches all 1,032 pages, and the unbuilt one
reaches none. Proved red by drawing it.

**AND THE TRACKING PARAMETERS WERE STRIPPED BEFORE THE FIRST BUILD.** The
URLs arrived carrying `utm_source=chatgpt.com`, which is a claim about where
a reader came from that is false for every reader of this site and a
parameter this product would not ship even if it were true. `data.py`
refuses a query string on any of them, proved red.

**THE VALIDATOR WAS ONLY REACHED WHEN A PAGE WAS BUILT, WHICH IS A
VALIDATOR NOTHING RUNS.** Three deliberately broken registers — a tracking
parameter, a live row with no host, an unbuilt row carrying an href — each
printed *data ok* and then stopped the build a minute later. `build.py
check` is the command that validates the data, so `load_go_further()` is
called from `load()`. All four refusals are red now.

**A CHECK CONFLATED AN OUTBOUND LINK WITH AN AFFILIATE REFERRAL, AND DID
NOT FAIL — IT CRASHED.** `c_csp` pins the outbound host set and then asks
whether `rel="sponsored"` tracks a credential, by looking the host up in
`data/stay.json` with `next(...)`. A GO FURTHER host is in the allowed set
and not in that registry, so the first build raised `StopIteration` and the
whole check reported as broken rather than naming a host. `sponsored` is
the machine-readable half of a *disclosure* and tracks a credential; a
declared service has no credential mechanism at all, so the rule inverts:
an ecosystem host must never carry `sponsored`, because claiming one would
spend the disclosure vocabulary on a relationship that does not exist. That
is the recorded *outbound LINK is not a subresource LOAD* finding one shape
over, with a referral instead of a request. Both directions proved red.

**THE CLOSE, AND THE APERTURE HAD TO LOSE ITS THRESHOLD.**
`EUROPE IS NOT A CHECKLIST. / OPEN ANOTHER DOOR.` at `--ed-display-2`, then
the signature, then a thin line carrying the strap, the four legal pages and
the notice. The arch is struck by `arch_path()` — the one implementation the
plates, the social cards and the CSS all agree with — and **it returns a
CLOSED figure**, because everywhere else on this site it is a clip and a
clip has to close. Stroked, that closing segment draws a line across the
bottom and the mark reads as a panel with a curved top rather than as an
opening. The path is struck at 96×54 and the frame stops at 52, so the
jambs run off the bottom edge exactly as a real opening does. Only
rendering it found that.

**AND THE NOTICE CARRIES NEITHER AN ENTITY NOR A YEAR.** `OPERATOR` is a
placeholder and `docs/legal-position.md` records the entity gap, which the
legal paragraph one line above names in as many words — writing the
placeholder into a © line would be the one place on this site where the gap
read as a company. And no year, which is a build decision rather than a
legal one: `site/` is committed and CI rebuilds it to check for staleness,
so `date.today().year` would turn every page in the repository red on the
first of January for nobody's change. The same reasoning made *Explore this
month* into *Explore the year*, pointing at the index rather than at a month
page that would move twelve times as often.

**THE LEGAL PAGES LOST A COLUMN AND KEPT EVERYTHING ELSE.** Privacy, terms,
cookies and the accessibility statement are the register a reader needs when
something is wrong, and a fifth of a footer's visual weight spent on them
says they are a fifth of what this is. They are in the document, in the tab
order, inside `.footer-nav`'s accessible name and one click from all 1,032
pages; they are not a column.

**THE COST IS RECORDED AND IT IS THE ONE MOVE ON THAT CEILING THAT IS NOT
ABOUT /map.** The footer went 2,122 → 4,261 raw bytes: 2.1 KB on every one
of 1,032 documents, about 1.6 KB compressed for the whole band, and
`weight.max_page_kb` 598 → 601. It lands on EVERY page rather than on the
heaviest one, which is exactly the case that row exists to catch — so it is
paid deliberately, because a site-wide frame is the one thing that has to be
on every document, and the alternative is a footer that says less on 1,031
pages so the heaviest one can stay under a number.

**Two more the invariant register refused, each in the commit that made
them.** A `@media (max-width: 34rem)` block would have been a seventh
breakpoint, and the two-column rule already covers 320; `line-height: 1.06`
and `1.16` would have been a ninth and a tenth where the register holds
eight, and `1.12` was already in the set for both.

## Home 21 — one ground, two ends, and the refinement pass

**THE HEADER TAKES THE FOOTER'S BINDING, IN ONE SELECTOR.** The brief is
that the two are ends of one architectural object — *same colour, not same
weight* — so `.footer, .masthead` bind the same thirteen tokens and
everything that differs between them is SIZE and AIR rather than palette. A
second copy of that binding would be two chances to disagree, drifting one
token at a time, which this repository has recorded seven times about a
predicate, a number, a URL and a file extension.

**AND THE PINE BAND IS NOT WHAT CAME BACK.** A solid pine masthead was
measured as the largest single reason twelve families read as one page — the
first 63 pixels identical and *the most saturated thing in frame* whatever
changed underneath — and the recorded fix was *stop spending a saturated
colour there, not stop having a surface*. Graphite is a neutral: it costs
the family accents nothing and it is the ground the INTELLIGENCE world and
the footer are already built on. Measured on the painted pixel at 1280, in
both colour-scheme preferences, on four families:

| | light page | dark page |
|---|---|---|
| the band composites to | `rgb(30,38,36)` | `rgb(16,25,23)` |
| navigation ink | **9.30:1** | **10.76:1** |
| wordmark, and the focus ring | **13.56:1** | **15.70:1** |

against 4.63 and 5.84 on the old cobalt band, and against the **1.74** this
file records for pine on graphite. Nothing had to be restated to get there:
`--pine-ink` is bound to bone, so `.masthead .wordmark` resolves correctly
with no new rule, and the focus ring already reads `--ink`, which is *the
one colour guaranteed to read on this band in every preference*.

**AND THE REVEAL TURNED OVER WITH THE GROUND.** On a pale bar the fine line
inside the cut is the wall's own tone; on a dark one it is light, because
two near-blacks are always about 1:1 — the aperture's own finding. It is the
footer's top edge upside down, struck at the same 26%.

**`theme-color` MOVED FOR THE FOURTH TIME, WHICH IS THE ASSERTION WORKING.**
A derived meta value follows the thing it describes or it is a second
implementation of it. The bar is graphite in both preferences now, so the
*light* value stopped being a light value: what changes between them is no
longer the bar but what is UNDER it, and a 94% band composites differently
over bone paper than over graphite. `#1e2624` and `#0f1817`.

### The refinement pass

**THE DENSITY WAS THE FAULT AND THE STRUCTURE WAS RIGHT.** Five columns of
`--t-sm` links two pixels apart under a heading with `--s1` beneath it read
as a sitemap. Every number went up one rung of a ladder that already existed:
links `--t-sm` → `--t-base`, row gap `--s2` → `--s3`, column gaps `--s6/--s5`
→ `--s7/--s6`, the band's own padding `--s8/--s5` → `--s9/--s6`. **The column
head gained a rule**, which is what a printed index does and which says a
column *starts* rather than that a word happens to be above a list.

**THE STATEMENT LEFT THE MARK'S ROW, BECAUSE TWO COLUMNS MADE IT NARROWER AS
THE WINDOW GOT WIDER.** `minmax(0, auto)` sizes the first track to the
wordmark, and the wordmark is set in `--ed-display-3`, which is a clamp on
the viewport — so at 1440 the mark took more of the row than at 1280 and the
brand line beside it went **410 wide on one line to 382 on two**. A sentence
that breaks on the largest screens is the opposite of what it is for, and no
`max-width` fixes a track being eaten from the left. One column: the mark,
then *Open the door to Europe.* at display size with the rest as a note under
it — 704 at every width from 1024 up, one line.

**THE SIX EXTERNAL SERVICES SAY SO BEFORE THE CLICK DOES.** Every other link
in this footer stays inside the Atlas and these six leave it, so the
difference is stated in the type rather than left to a hostname in a status
bar. `aria-hidden` on the mark, because `target="_blank"` already carries it
for assistive technology and a glyph announced after each of six rows is the
constraint explained back.

**THE DISCLOSURE WAS ORDINARY FOOTER COPY AT THE FOOT OF A COLUMN.** It is
the sentence that keeps the commercial and the editorial apart — this
product's whole position on the six links above it — and as the sixth
paragraph of the third column it read as more of the list. It is its own
band with its own label between the monument and the legal strip, where a
publication puts a note about its own conduct. The heading is a LABEL rather
than an `<h2>`, because the homepage asserts its own heading count.

**THE BRIEF'S FIGURE FOR THE APERTURE WAS BELOW WHAT WAS ALREADY THERE.** It
asked for the mark to be *substantially larger, perhaps 56–72px*, against a
mark already drawn at 96. The instruction is followed and the number is not:
140 × 76 is where it stops reading as a glyph after a sentence and starts
reading as the door the sentence is about.

**And the close is two paragraphs rather than a `<br>`.** The first sentence
is what this atlas refuses and the second is what it asks for; a line break
makes them one three-line block where the turn between them is the point.
`--s9` above and below, so it reads as a page of its own rather than as the
band after the columns.

**MEASURED AT SIX WIDTHS, NO WRAPPED LINK AND NO OVERFLOW — AND THE ONE
THING THAT IS TIGHT IS RECORDED RATHER THAN FIXED.** At 1024 the five
columns are 146px each and four of the thirty entries set on two lines
(*Beyond the obvious*, *The European year*, *Sources & corrections*, *For
tourism boards*). At 1280 and above none do. Raising the five-column
threshold would need a **seventh breakpoint**, which the register refuses —
and two-line entries in a five-column index are what a printed index does,
where a three-column desktop would be the thing the brief explicitly rules
out.

**One label was not taken from the brief.** It lists */events* as *Europe in
the year*; the page's own head says **The European year**, and a second name
for one thing is two names waiting to disagree. The existing label stands.

## Home 22 — six rooms, and a z-index that had been wrong on every page

The bar was seven sibling indexes in a row — Discover, Countries,
Experiences, Journeys, Plan, Stories, Events — which is a list of the
indexes this site happens to have rather than a statement about what a
reader is doing. And two of those seven are the SAME KIND of thing as four
pages that were never in the bar at all: /themes, /interests, /map and
/europe-in are geography and ways in, and they lived only in the footer.

**SIX ROOMS, EACH A REAL PAGE, EACH CARRYING ITS OWN FIELD.**

| room | is | its field |
|---|---|---|
| DISCOVER | /discover | Experiences · Europe in Motion · Beyond the obvious · The European year |
| ATLAS | /countries | Countries · Ways to travel · Themes · Map |
| JOURNEYS | /journeys | — |
| PLAN | /plan | — |
| STORIES | /stories | — |
| EUROPE | /manifesto | About · How it works · Method · Sources & corrections · Europe Fund |

**NOTHING IS IN TWO FIELDS**, which is a departure from the brief and the
reason is that the brief lists Stories both as a room and inside DISCOVER:
a reader seeing STORIES twice in one bar learns that the bar is decoration.
And the sixth room is the one the brief named and did not fill — five rooms
are ways through the atlas and this one is why it exists, which had no place
in the bar at all and lived at the foot of 1,032 pages.

**THE FIELD IS CSS, AND THE ORDER OF THE TWO SELECTORS IS THE WHOLE TRICK.**
Most pages here load no script and the CSP carries no `'unsafe-inline'`, so
a navigation that needed JavaScript would be the first script on the
homepage — the trade the nine restraint marks on the hero were removed over.
`:hover` opens the field for a pointer and `:focus-within` opens it for a
keyboard. The field can be `display: none` — out of the tab order AND out of
the accessibility tree — only because the thing that reveals it is the ROOM
link, which is always visible and always focusable: Tab reaches the room,
`:focus-within` matches, the field displays, the next Tab enters it. A field
revealed by focus on ITSELF is the chicken-and-egg this pattern is usually
got wrong by, and it is invisible to every static check, because the markup
is identical either way. The browser suite asserts the SEQUENCE rather than
the state — `display` on a focused room, then `Tab`, then whether focus
landed inside — because a computed style cannot answer the second half.

**AND `aria-current` STOPPED BEING A JOIN BETWEEN A LABEL AND A STRING.** It
was `area == label.lower()`, so renaming COUNTRIES to ATLAS would have
silently unlit all twelve area keys the country family passes, on several
hundred documents, with nothing going red. Each row carries its own set of
area keys now, in the one table. Measured after: /europe/austria/ lights
ATLAS, /stories lights STORIES, /experiences lights DISCOVER.

### The defect the field exposed

**`.masthead { z-index: 40 }` WAS SILENTLY OVERRIDDEN SEVEN THOUSAND LINES
LATER, AND THE STICKY BAR HAD BEEN BEHIND THE DOCUMENT ON ALL 1,032 PAGES.**
`.masthead, main, .sitefoot, .thumbbar { z-index: 1 }` set it at equal
specificity and later in the file, so the bar and `main` were on one layer
and `main`, which comes after it in the document, painted over it. Measured
with `elementFromPoint(640, 40)` after scrolling 1,400 pixels:

| page | topmost element inside the bar's own band |
|---|---|
| / | `sheet sheet-bleed` |
| /europe/austria/ | `movedraw` |
| /map/ | `mapkey` |

**It looked correct because the bar is 94% opaque and carries a
`backdrop-filter`**, so content passing under it is blurred and washed —
which reads exactly like a translucent bar with the page scrolling beneath.
Nothing here could see it: every box was the right size in the right place,
every contrast ratio was measured against the bar's own paint, and **nothing
in the masthead had ever overflowed its own box**, so there was nothing whose
disappearance would show. A room's field is the first thing that does, and
it came out clipped at the band's bottom edge. After: the bar is the topmost
element on all three.

**And the list is about a ribbon that no longer exists.** The comment
directly above it records that the family-colour gradient behind the page
was built three ways and removed; those three elements are there to sit
above it, and `.masthead` was swept in with them.

### The two assertions that could not have failed

**§5 READ `label in page("/")`** — true of a word appearing anywhere on a
145 KB document, including the footer, which carries every one of these
links on every page. Seven assertions about the PRIMARY navigation were
satisfied by the FOOT of the page and would have stayed green on a bar that
had stopped carrying any of them. §2 of the UX audit had the identical
fault. Both slice the masthead out by its own element now, and both assert
an **href** rather than a label: the specification's subject is the surface
being reachable from the top of every page, and a label is a word somebody
may rewrite. §5 also asserts that each of the six rooms is a page of its own
— a room that were a heading over a field would be the chip that filters
nothing, in the bar.

**The phone loses two links from the masthead and that is the trade.** Six
rooms with their fields flattened is fifteen links on a 390px screen, and
the recorded measurement is that FIVE already wrapped into two rows. Below
44rem the bar is the four rooms the thumb bar does not carry — Atlas,
Journeys, Stories, Europe — and every field entry is one tap away in the
footer of the same document, which is exactly where /themes, /interests,
/map and /europe-in have always been. Measured at 320, 390, 834, 1024, 1280
and 1440: no overflow, no wrapped entry in any panel, and every panel inside
the viewport.

`weight.max_page_kb` 601 → 602, recorded: the masthead went 916 → 1,685 raw
bytes, 683 compressed, for thirteen links that were previously reachable
only from the foot of the page.

### The eight the dead-rule scan named, and the one that was not a no-op

The browser suite came back with one failure of 12,889 — the dead-rule
scan, naming eight declarations, five of them new. **The three keyboard
assertions passed**, which is what that run was for. Read rather than
ceilinged, per the check's own rule:

| | |
|---|---|
| `.staysay {color}` · `.footsay {color}` | `color: var(--ink)` on elements already inheriting it from `.footer { color: var(--ink) }` |
| `.footlegal-nav a {color}` | `.footline` already sets `--ink-3` and `a { color: inherit }` carries it |
| `.stayrow {display}` | a grid item is **blockified by the layout** — the fifth and sixth occurrence of that finding are already on this stylesheet's record, and this is the seventh |
| `.masthead-in .nav .navfield, …:hover >, …:focus-within > {display}` | the first selector restated `.navfield { display: none }`, which is true at every width. Writing all three in one rule also **defeated the scan's own guard**: a `:hover` selector matches nothing when the pointer is nowhere and is skipped, but the base selector matched, so the rule was judged as a whole and reported dead on the half that really was |

**`.masthead .wordmark {color}` IS THE SAME CLASS OF EXPIRY THIS FILE
ALREADY RECORDS ABOUT A PHONE RULE WHOSE COMMENT DESCRIBED A 132px MARK.**
The two rules under *the pine is spent on the mark and the current section*
were right for a bar the colour of the page. The bar binds the graphite
ladder now, and on graphite `--pine-ink` IS bone — #0F433E measures 1.74:1
there, which is why the token is lifted at all. So the declaration set bone
on an element already inheriting bone. **A rule's reason can stop being true
when the ground moves under it.**

**AND THE SECOND ONE WAS NOT A NO-OP, WHICH IS WHY IT WAS WORTH READING.**
`.masthead .nav a[aria-current="page"]` was reported dead for a different
reason — *two rules setting one value, so the scan names both*. It beat
`.nav .navtop[aria-current="page"]` at (0,3,1) against (0,3,0) and set the
same bone, so each changed nothing only because the other produced the same
colour. What it also did, silently, was take the current room's **underline**
from `--door` to `--pine-ink`: a bone rule under bone type, where hover draws
a cobalt one — the marker and the hover state were two different colours for
one relationship. Deleting it lets the nav block's own rule stand. Measured
after: the current room's ink is bone at 13.56:1 and its underline is
cobalt-air at **3.66:1 on the light-page band and 4.23 on the dark one**,
clearing the 3:1 WCAG 1.4.11 asks of a non-text component, and matching
hover exactly.

**NOTHING WAS DELETED ON THE SCAN'S WORD ALONE.** The five redundant
declarations were put back through the CSSOM and the footer and the masthead
were shot at 1280 and 390 on two families: **six of six byte-identical**.
`addStyleTag` could not do it — this site's CSP is `style-src 'self'` with
no `'unsafe-inline'` and refused the injected `<style>`, which is the policy
working; `insertRule` writes into the stylesheet already loaded from this
origin and is not an inline style.

## Home 24 — the hero drew forty-one photographs and could show six

`living_atlas`'s own comment states the measurement: *"a photograph clipped
into Belgium renders about 40 pixels wide at 1280 and is a smudge with a
coastline"* — and it was the reason the cast was six. Forty lines later a
second comment overrides it: *"every country that has a photograph is an
aperture, and all fifty do"*, and all 41 went in. **The code stopped
matching its own comment, two comments apart in one function.**

Measured on the shipped page at 1280, where the drawing is 671px across a
1,120-unit frame:

| | |
|---|---|
| Portugal 158.6 · Türkiye 153.5 · Norway 145.0 | pictures |
| Spain 97.9 · France 95.6 · Italy 90.7 | pictures |
| Greece 75.3 · Germany 58.3 · Sweden 54.5 | smudges |
| **Belgium 24.0** · Kosovo 12.8 · **Luxembourg 4.8** | pixels |

**Belgium is 24 pixels, not the 40 its own comment claims** — and 18 of the
41 were under that 40, with a median of **42**. At 390 the median was 22 and
34 of 41 were under 40.

**Zoomed 2× it is not a map.** Adjacent photographed countries in different
tones read as a torn collage: the edges you can trace are a picture's edge
rather than a border, and where two photographs happen to be similar the
frontier vanishes. **And the lighting is inverted against the meaning** —
the countries with no photograph are the palest, brightest things in the
frame, so the eye reads the ones we have nothing of as the lit ones.

**THE FLOOR IS THE BREAK IN THE DISTRIBUTION RATHER THAN A NUMBER PICKED BY
EYE.** 90.7 to 75.3 is a 17% step, the largest relative gap anywhere in the
top half of that list, and it falls exactly where looking says the picture
stops being one. `HERO_SHOT_MIN_UNITS` is 150 units — 89.9px at 1280 — so it
is a statement about the drawing rather than about one viewport.

| | before | after |
|---|---|---|
| photographs drawn | 41 | **6** |
| median drawn width at 1280 | 42px | **145px** |
| under 40px | 18 | **0** |
| under 80px | 35 | **0** |
| median at 390 | 22px | **77px** |
| homepage | 145.6 KB | **135.0 KB** |

And **35 image fetches came off the most-visited page** — the invariant
register already recorded that the page asks for its country photographs at
the ladder's 480 step, about 950 KB, *"and most of these countries render
under 150px"*. Six do not.

**SIX IS NOT "SIX THAT MATTER AND FORTY-FOUR THAT DO NOT"**, which is the
reading the override was written against. It is /countries' own rule — 41 of
50 can be a door and nine cannot, six for want of a polygon and three for an
advisory — applied to a frame where the whole continent is 1,120 units
instead of one country. Every other country keeps its shape, its frontier,
its name and its link, in the atlas's own stone.

### And the hero had been drawing licensed photographs with no credit at all

`_lzpanel` was the literal empty string. It is where the living atlas's
credit used to live; the panel went when the rotator was costed and refused,
**and the photographs it credited stayed on the drawing**. So the most-visited
page on this site drew 41 licensed Pexels photographs and named no
photographer and no provider, for the life of the living atlas. That is
*removing a claim leaves surfaces pointing at it* the other way round — a
surface removed, and the thing it made a claim about left behind. It is a
breach of somebody else's terms rather than a defect of taste.

**NOTHING HERE COULD SEE IT.** Every one of those 41 had a register row, so
`c_photo_published` was satisfied; the rows were complete, so every
provenance check was satisfied; and the credit is a property of `picture()`,
which the hero never calls — it writes SVG `<image>` straight into the
drawing, because a picture clipped to a country's own geometry cannot be a
`<picture>`. **That is the runtime-`<img>` finding arriving through a
renderer instead of a script.**

`c_svg_image_credit` is the guard: a page that draws a registered photograph
as an SVG `<image>` must also name a photographer and link to the provider.
It counts PAGES, because a check reporting `(0)` looks exactly like the two
this repository found examining nothing. Proved red by removing the line.
The credit itself is `photo_credits`, the one implementation, so it cannot
say *Photographs* over one picture or name a photographer twice — and the
`.lzcred` rule was still in the stylesheet, written for this line, waiting
for markup that had been deleted.

**And the design-asset check went red on a proximity heuristic that had just
broken.** It read 1,200 characters either side of the asset's own filename,
which is a proxy for *the same surface* — and the plate ABOVE the window
gained a credit line of its own, naming six photographers none of whom shot
the design asset one band down. Right that something new had happened, wrong
about what, which is the shape already recorded here about an outbound link
and a subresource load. A `<section>` is what a band IS on this site, so the
test slices to the enclosing one: the claim itself rather than a stand-in
for it, and **stricter as well as more accurate**, because a band longer than
1,200 characters is no longer partly out of reach. Proved red by putting a
credit inside the window's own band.

## Home 25 — two label families on one drawing, and only one of them had a box

Every label on this site goes through one machine: `place_label_box` measures
it against `LABEL_METRICS`, tests it against the aperture, tests it against
the names already down, and drops it when it fits nowhere. That machine is
the reason the destination plates went from 271 overlapping pairs to zero and
the reason 184 labels stopped being drawn into the removed corners of the
arch.

**The water labels went through none of it.** `sea_names()` picked a point
with enough open sea around it and emitted a `<text>` — no width model, no
aperture test, no collision test, and nothing for anybody else to avoid. So
`name_countries()`, which has all four, was arranging half a layer: its own
comment promises each name is tested "against every name already down", and
that was true of its own family and of nothing else.

Measured in Chromium at 1280, 1440 and 1920:

| | | |
|---|---|---|
| NORTH SEA | UNITED KINGDOM | 68px · the homepage |
| BAY OF BISCAY | FRANCE | 41px · the homepage |
| BLACK SEA | ROMANIA | 18px · the homepage |
| NORTH SEA | UNITED KINGDOM | 80px · /map |
| IONIAN SEA | GREECE | 49px · /map |

**AND THE TWO DRAWINGS IT HAPPENS ON ARE THE TWO NO OVERLAP CHECK HAS EVER
LOOKED AT.** Counted across the built site, twenty-nine shapes carry more
than one label family and **twenty-eight of them are a `.minimap`** — which
is the selector both existing overlap sweeps read. The twenty-ninth is the
hero, which is not a `<figure>` at all, and the thirtieth is `#europemap`.
Those two are the only drawings here that carry `.seaname` beside `.cname`,
they are the largest pictures on the site, and they sat outside the check by
a selector nobody had re-read since the day the sea names were added.

That is this repository's own recorded failure for the fourth time: the
check matching `pointsmap arched"><svg` that examined **0 dots** on a site
with 130 region maps, `c_one_plate_per_thing` reading zero once the last
abstract plate came off, and the crop-box sweep making two green assertions
a run about elements the site no longer had. **A selector, not a figure
class** — whether two labels on one drawing overlap is not a question about
which element the build chose to wrap it in.

**THE PINNED FAMILY GOES FIRST AND THE FREE ONE IS TOLD WHERE IT WENT.** A
sea name has exactly one position, the middle of its own water; a country
name has nine anchors and four positions at each. The country plate already
settled which of those is composed first, when reserving a box across the
middle of Albania ate Tirana's label and left a star nothing named. So
`sea_names()` returns its boxes as well as its markup and
`name_countries(reserved=…)` seeds them into `taken`, which is the one list
`place_label_box`'s `clears` predicate reads. **`/map` had the order
backwards** — it composed the country names and the sea names two lines
later, so the free family chose before the fixed one existed.

**ONE MODEL PER TYPE SIZE, and this family needed two.** The face and the
.34em tracking are shared; the size is not. The hero sets this family at 13
units in an 1,120-unit frame and /map at 11 in a 1,000-unit one, so their
boxes differ by 18% and one model cannot serve both. Fitted as the upper
envelope over every name each drawing renders, measured with the browser's
own `getBBox` in the drawing's own user units:

    seaname        11.0 + 10.20 * chars      up 9.85   down 2.95
    seaname-hero    0.5 + 12.75 * chars      up 11.68  down 3.34

**What it cost, counted rather than glossed.** Five pairs to **zero**, at all
three widths. On the hero four names moved and the count held at its cap of
sixteen: UNITED KINGDOM came down 22 units off the North Sea and onto the
slot IRELAND wanted, so Ireland lost its name and **LATVIA**, the next
country by drawn area, took the freed place. On /map the count went 13 → 12
and the one that went is **GREECE** — precisely the name that had been drawn
through IONIAN SEA. Each of those keeps its shape, its frontier, its link and
its accessible name, which is what a dropped label has always promised here.
The substitution is the drawn-area rule doing what it says: that order is a
property of THIS picture rather than a judgement about the country, and
raising the cap to save Ireland would be tuning the design to one case.

**AND `most` WAS A PARAMETER NOTHING READ.** `sea_names(land, view, most=6)`
sliced `[:6]` in its body, so a caller asking for four got six and a caller
asking for ten got six. Neither caller passed it, so nothing a reader sees
was ever wrong — the lie was in the interface. *An ignored argument is dead
code that looks like a decision*, which is what `kindfilters` cost /events
and `opts.geoTooNarrow` cost /plan.

**The instrument, and it asserts its own reach.** The new sweep reads every
`<text>` whatever its class, on any `<svg>` carrying two label families, at
three widths — three because the hero is `preserveAspectRatio="slice"` and
crops a different part of its frame at every window shape. It fails when it
stops finding six drawings over two pages and three widths, because a
selector that matches nothing reports zero overlapping pairs and passes.

**And the model is checked against the drawing, because it cannot check
itself.** `LABEL_METRICS` is a fitted envelope, so the build reserves a box
it has MODELLED rather than one it has measured, and a static check
re-running that model would only ever agree with it. `getBBox` is the
different implementation of the same question. The failure that matters is an
envelope that UNDERSTATES: the reserved box would be smaller than the type
and a country name would be let through into it.

Proved red four ways — the hero's wiring removed (9 pairs), /map's order put
back (6 pairs), the envelope shrunk (11 names wider than their box), and the
sweep pointed at pages with no two-family drawing (0 of an expected 6).

**And one thing was measured and deliberately not built.** The sea-name pass
tests its POINT against the rectangle and never its BOX against the arch —
which is, word for word, the failure that put 184 labels' corners outside the
aperture and drew fourteen of them entirely inside a removed corner. Measured
against `in_arch` at the hero's own frame, all five of the names it draws are
four corners inside with the mason's clearance, so the test would change
nothing today. It is recorded rather than added for a second reason that is
not thrift: **the hero is `preserveAspectRatio="slice"` and crops a different
part of its 1,120-unit frame at every window shape** — 1,078 units shown at
1280 and 961 at 1920 — so a build-time arch test would be testing a frame no
reader is ever shown. The trigger is a sea name measuring outside the
aperture, which the browser sweep above would see as a name that is placed
and not drawn.

**AND RUNNING THE ACQUISITION GATE FOUND SOMETHING THIS COMMIT DID NOT
CAUSE — WHICH IS WHY IT IS A GATE.** `photo-tests.py` failed on *the credit
the provider requires is still on it*, and `git log -S` puts the cause in
**Home 19**, six commits back: that commit added the design-asset state and
registered `london-thames` as standing in for `home-hero`. `home()` suppresses
the hero's credit while a design asset claims the purpose — correctly, because
printing a photographer's name under somebody else's picture is a false
attribution worse than clutter — and `contact_sheet.py` substitutes a
candidate by **replacing the register and leaving `design` untouched**. So the
sheet drew the candidate and credited nobody: the one artefact whose job is to
show a person the real composition was showing neither state, on a page where
the credit is a measured part of the composition with its own scrim and 6.90:1
by arithmetic.

The comment directly above that substitution states the principle it needed —
*the register is REPLACED for this render, never merged into: a candidate must
not inherit a real row's provenance by sitting beside it in the same dict* —
and it was applied to `images` and not to `design`. **A rule stated once and
applied to one of its call sites**, in the comment that states it.

**The honest half is that nothing caught it for six commits because the gate
was not run.** It is on the list in `CLAUDE.md`, it takes about five minutes,
and Home 20 to Home 24 each shipped without it. A gate people skip is a gate
that finds things six commits late, which is the same sentence this repository
already writes about a gate that cannot fail.

## Home 26 — the empty part of the homepage was a margin that escaped its box

The owner sent a screenshot of the deployed page with a vast blank region on
it and the instruction *this empty part of the home page need to be design
with information*. The honest answer is that there was nothing to design
there: the band was not a composition waiting for content, it was 558 pixels
of wall that a margin had pushed open, and filling it would have been
designing around a bug.

**`voids.js` reported zero voids on this page**, correctly. That instrument
finds a band over 90px with **nothing** painted in it; every 50-pixel slice
of this run carried the plate mark, a hairline or the top edge of the window,
so not one of them was empty, and the band still read as a hole. A band with
*almost* nothing in it is a different measurement and nothing here had ever
taken it. `tools/density.js` does: the horizontal union of everything that
paints, per 50px slice, as a share of the page's own width.

**And its first version reported the photograph as the largest hole on the
page.** It read an 850-pixel run at 1% covered inside plate 03 — the window,
which is a full-bleed photograph of London. A `position: fixed` rectangle is
viewport-relative, so adding `scrollY` to it files the picture in whatever
slice the page happened to be scrolled to; a screenshot at y=1500 showing
London filling the frame is what disproved it. What such a box paints is the
whole of its **clipping ancestor**, which is what a reader sees. The first
correction read `position` on the child alone and changed nothing, because the
fixed element is the parent — the walk goes up the whole chain. 31% → 27%.

| | |
|---|---|
| `clip-path: inset(0)` clips a fixed descendant | which is the whole reason the window uses it, and is recorded |
| `clip-path: inset(0)` establishes a block formatting context | **false**, and that half was assumed |

`.shotsay` is the window's first child and takes `margin-top: 62svh` to set
the type two-thirds down the picture. With no BFC that margin collapses
*through* the window and moves the window itself down the page instead: the
plate mark ended at y=964 and the window opened at y=1523, which is 62svh of
900 to the pixel, and 523 at 390 against 62svh of 844. `display: flow-root`
contains it, and — unlike `transform`, `filter`, `contain` and the four
others this stylesheet already records — it does **not** make the box a
containing block for a fixed descendant, so the picture still stands still
while the wall moves past it. Proved the only way that can be proved: the
page was scrolled 300 pixels and the photograph moved 0.

| | before | after |
|---|---|---|
| the gap above the window | 558px | 16px |
| plate 03's own height | 1,653px | 1,111px |
| the document | 12,244px | 11,702px |
| slices under 20% covered | 27% | 23% |
| the largest run | 700px at 1% | 250px at 2% |

**`density.js` is a reporter and must not become a gate**, on `voids.js`'s own
reason turned round: a floor on coverage is satisfied by widening every
measure until the page is a wall of type, which is the opposite of this
product, and a 200-pixel run at 8% is right where the thing above it is a
closing statement. What the number is for is the outlier, and for the
before-and-after of a composition change.

## Menu 01 — thirteen links a mouse could not reach

The masthead names six rooms and three of them carry a field: Discover's four
links, Atlas's four, Europe's five. The field is `display: none` until
`:hover` or `:focus-within`, with no JavaScript — which is right, and which
had one thing wrong with it that no gate here could see.

`.navfield` is `position: absolute` at `top: calc(100% + var(--s3))`. An
absolutely positioned child is out of flow, so it contributes nothing to
`.navroom`'s own box: the twelve pixels between the room and the panel belong
to neither element. `.navroom:hover` stops matching the moment the pointer
enters them, and `display: none` takes the panel away before the hand
arrives.

Measured at 1280, moving from the middle of the word to the first link in the
panel, in Playwright's `steps` — which is what makes a movement a hand rather
than a teleport:

| mouse events | Discover | Atlas | Europe |
|---|---|---|---|
| 1 | opens | opens | opens |
| 5 | closed | closed | closed |
| 12 | closed | closed | closed |
| 30 | closed | closed | closed |

The same at 1440, 1152, 1024 and 960. **The keyboard route works because it
never crosses the gap** — Tab moves focus from the room straight into the
field, `:focus-within` matches throughout — which is exactly why the suite's
existing assertion was green: it presses Tab, on purpose, and that is the
route that was never broken.

The bridge is a transparent strip that belongs to the **field**, so it exists
only while the field does and there is no phantom hover target at rest. 13px
rather than 12, because `top` resolves against the padding box and the field's
own 1px border sits between that and the gap.

And the check is the movement, because a promise about movement cannot be
proved any other way. It pushes the pointer in 5, 12 and 30 steps, asserts the
panel survives and that the point under the cursor is inside it, and asserts
the room's own word is still the element under the pointer when it is hovered
— because the obvious bridge is one that covers the link that opens the menu.
Proved red both ways: 9 of 15 assertions with the bridge collapsed to zero
height, 3 of 15 with it four times too tall.

## Menu 02 — three of the six rooms open a directory and nothing said which

DISCOVER carries four links, ATLAS four and EUROPE five; JOURNEYS, PLAN and
STORIES carry none. At rest all six were the same word, in the same type, at
the same weight — so the only way to learn that thirteen of the bar's
nineteen destinations existed was to hover a word at random and find out.

It is the same thirteen links Menu 01 had just made reachable with a pointer,
which is the half that makes this worth a commit rather than a nicety: a
repair nobody can find is not a repair.

The mark is **drawn rather than typed**, which is this page's own rule — the
go-link is a circle and a rule rather than an arrow character, because a mark
that is drawn belongs to the drawing family the rest of the page is made of.
Two 1px borders on a rotated square is the caret every printed contents page
has used for a century, at 0.3em, which is five pixels at this type size
against the nine a `▾` would set. It inherits `currentColor`, so it lifts on
hover and on the current room exactly as the label does and there is no second
colour decision, and a pseudo-element is not in the accessibility tree, so
"submenu" is not read aloud after three of six words.

**And it comes off where the field does.** Below 60rem the two rules that open
a field are undone, so the mark would promise a directory that cannot be
opened — *removing a claim leaves surfaces pointing at it*, written in advance
for once.

| | before | after |
|---|---|---|
| the nav row at 1280 | 456px | 490px |
| slack at 961, the narrowest one-row width | 75px | 58px |
| rows at every width down to 961 | 1 | 1 |

**The assertion is the painted advance rather than the `content` property.**
`getComputedStyle(e, "::after").content` computes to the SPECIFIED value —
this repository already records a check defeated by exactly that, reading back
`"0" counter(band)` and reporting nineteen families broken when none was. What
is measurable is that the link's box is wider than its own text: a Range over
the text node gives the glyphs, the element gives the box, and the difference
is the mark. Proved red both ways — three failures with no mark anywhere,
four with a mark on every room including the phone.

**And the check's own first version asked the wrong element.**
`a.parentElement.querySelector(".navfield")` is `.nav` for a room with no
field, and `.nav` contains every other room's field, so it reported all six as
carrying one and went red on the three that are correct. The question is about
THIS room and is asked of this room.

## Home 27 — the atlas index listed fifty countries and drew none of them

The owner pointed at plate 05: *the countries listed on section 5 of the home
page are without design.* He is right, and the measurement is specific.

The band's own sentence is **One continent. Fifty doors.** What it drew was
nine headings and fifty names, set in the body serif at reading size, in three
multicol columns — a sitemap, on a page whose whole argument is that geography
IS the design. Every one of those fifty countries has an outline in
`data/geo/`, and the band showed none of them. That is the /themes failure
word for word: a page describing shapes its own closing sentence is about and
drawing none.

**`country_mark` is `country_door` at the size of a word.** Same own-frame
fitting — Luxembourg fills its box as Türkiye fills its own, which is the
decision `country_door` records and the reason a continental frame cannot
carry this: at about a pixel per unit Luxembourg is eight of them there. Same
`COUNTRY_DOOR_POINTS` floor deciding which six countries are a ringed point,
**read** rather than typed a second time. No photograph, so no register row
and no image request.

Three ways to draw fifty countries were costed before one was built:

| | bytes |
|---|---|
| the country doors at lod1, 41 of them | 628 KB |
| one shared continental silhouette + the lit rings | 18.8 + 9.8 KB |
| **fifty own-frame outlines, adaptively thinned** | **8.4 KB** |

The cheapest is also the only one that draws fifty *different shapes* rather
than nine pictures of Europe with different bits lit — which is the refusal
this site already made for /interests, and the wallpaper the aperture's own
rule warns about.

**And the first size was the smudge this repository had already measured.** A
2.1rem track renders a country 33 pixels wide: Italy was readable, Greece was
a blob and Norway was a stroke. *A photograph clipped into Belgium renders
about 40 pixels wide and is a smudge with a coastline* is the same finding one
drawing over, and so is the /themes continent at 204 pixels. 3.4rem by 2.4rem
is 54 × 38, and it costs the band about 300 pixels.

**Each corner states its own extent**, which nine identical headings could not:
they hold two countries and nine. The figure is derived from the grouping
directly above it, so it cannot disagree with the names under it.

`weight.home_kb` 148 → 151, recorded.

### And a stray `*/` swallowed the rule that laid it out

The comment above the size decision contained the characters `*/themes*`.
That closed the comment, the prose after it was read as a selector, and the
next whole rule — the grid that puts a country's outline beside its name —
was dropped. The page rendered the name on one line and the shape centred on
another, and every box was the right size.

`CLAUDE.md` has recorded this failure twice, with the repair written out: *a
four-line scan for a `*/` outside a comment finds both in a second.* **Nobody
ever wrote it.** That is `data-rotate` arriving in this repository's own
documentation — a described repair is not a repair — and it cost a third
occurrence. `c_css_comments` is those four lines, both directions, examining
1,160 comments, proved red on a stray close and on an unterminated open.

### And `country_glyph` was already taken

The first version of this function was called `country_glyph`, which is the
name of the country card's own picture eight hundred lines below it. Python
resolves the **later** definition, so the build called that one and stopped on
its signature. *Grep the stylesheet before naming a composition* is written
here about a CSS class; it is the same rule about a module-level function, and
this time it was loud only by luck — the two signatures differ.

## Menu 03 — nineteen of forty-seven families lit no room, including a room's own page

`aria-current` in the masthead was decided by the **area** string a page
builder passes, and the table's area sets cover the indexes rather than the
pages the fields point at. Measured across every rendered family:

| | before | after |
|---|---|---|
| lit exactly one room | 28 | 34 |
| lit two rooms | 0 | 0 |
| lit none | 19 | 13 |

Among the nineteen: /about, /how-it-works, /method, /sources,
/beyond-the-obvious, /search, /my-europe — and, most plainly, **/manifesto,
which is the EUROPE room's own href.** A reader standing on the page a word in
the bar links to was told nothing by that word.

**The field already declares the answer.** A room is current when the reader
is on its own page or on any page its directory names, and both are in the
same table — so the test is derived from the row rather than from a second
hand-listed set somebody has to remember to extend. It is `bottom_nav`'s own
rule, which has marked by PREFIX rather than by equality since it was written
so that a city page lights Explore; the masthead never got it. One mechanism,
two bars.

**And the area wins where it speaks, which the first version did not say and
one page proved.** `/discover/adriatic-balkans` is a macro region: it passes
`area="countries"`, which is ATLAS, and its path sits under DISCOVER — so
adding the path test lit both, on a bar whose whole job is to say where one
is. The area is the page builder's own statement of what the page IS; the path
is the fallback for pages whose builder says nothing.

The thirteen still unlit are the homepage and the 404, which are correctly
none, the two utilities, which are marked in their own half of the bar, and
nine institutional and legal pages that are in no room and live in the footer.

**And a marked link could be marked and not look it.** `.navutil a` had the
transparent border and the hover colour and no rule for the marked state at
all, so /search and /my-europe announced a current page to a screen reader and
showed nothing to anybody else — present, correct, announced and invisible,
which is this repository's most repeated shape. Same two declarations the
rooms use, because a marker that differs between two halves of one bar is two
markers.

Both halves proved red: seven failures with the area-only test (naming
/manifesto and /sources by name), one with the utility rule emptied.

## Menu 04 — the ceiling was twenty-two pixels under the bar it is a ceiling on

`--mast` exists because of a defect this repository already had: every
in-page anchor scrolled its target to y=0, which is where the sticky masthead
is, and on a phone a heading landed nine pixels behind it. The repair was one
token, "a ceiling on the bar and a floor on everything that has to clear it",
and its comment says the two values are the two measured heights rounded up.

Then the bar grew. `.masthead-in` went from `--s3` to `--s5` of block padding
— 58 to 82 at desk width, with its own comment recording the move — and
nothing moved the token with it. Swept in Chromium at twenty-seven widths
from 320 to 2560:

| | bar | `--mast` | |
|---|---|---|---|
| ≥ 961 | 82.0 | 60 | **over by 22.0** |
| 704–960 | 90.4 | 60 | **over by 30.4** |
| < 704 | 90.4 | 92 | ok |

**The breakpoint was wrong as well as the value.** The bar becomes two rows at
60rem and the token only noticed at 44rem, so the widest gap is the 256 pixels
of width between them — the range the contact sheet's own 834 finding exists
to look at.

Nothing went red, because the three rules that read the token are offsets a
section's own top margin was already absorbing. That is a latent defect of
exactly the kind this token was invented to stop, in the token invented to
stop it — and a comment claiming a ceiling the measurement does not support is
read as evidence.

**And the bar's height was stated twice more.** `scroll-padding-top: 5rem` is
a third number for one thing — 80 against 82 and 90 — and with
`scroll-margin-top` ALSO carrying the bar, an anchor landed at
`padding + margin` = 156 pixels, 74 below a bar it only had to clear once. The
two properties are different questions: the **scrollport's** padding is what
the bar covers, and the **target's** margin is the air a reader wants above the
heading. One copy each.

| jumping to a section on a destination page | before | after |
|---|---|---|
| clearance at 1280 | 74px | 24px |
| at 960 | 65px | 25px |
| at 390 | 97px | 25px |

Uniform, and by construction rather than by three numbers happening to sum.

**The sweep is the check**, and it is the half `--mast`'s own comment promised
and nobody wrote: one page, a `setViewportSize` per width, eighteen widths
with 961 and 960 both in it on purpose, because the two-row transition is
between them. Proved red on the old values: thirteen widths over.

## Home 28 — the ruled line through Russia

The owner said it twice, and the second time named the country: *the map you
are using is not good as it had a straight line around Russia … remove the
line inside Russia.*

**The fill had already stopped saying it.** Plate 05 draws the ground beyond
the atlas under the fifty, in the *same* stone, precisely so that the 52°E
data cut is not a boundary between two treatments — that was the previous
pass, and it is why the fade came off rather than being tuned. What was left
was the INK. `.lyr-land path` strokes every edge a country ring has, and
Russia's ring has one edge that is not a frontier: the meridian this
repository's data stops at. It rendered in the same weight and the same
colour as the Poland–Germany border, from the White Sea to the north Caspian.

| | |
|---|---|
| what it is | the eastern edge of `doc["bbox"]`, which `europe-lod1.json` carries as `[-32.0, 33.0, 52.0, 72.5]` |
| why it is straight | a meridian is a straight line under a Lambert conformal conic, so two projected points describe the whole cut |
| what drew it | the frontier stroke, at .6 CSS px, `vector-effect: non-scaling-stroke` |

**The land group is clipped two units short of the meridian.** The easternmost
thing this atlas draws is Azerbaijan at 50.6°E — about eighteen drawn units
west of the cut — so no real frontier is anywhere near the clip, and the
two-unit sliver taken off Russia shows the ground beyond underneath it, which
is the identical fill. The polygon is built from `doc["bbox"]` rather than
from a typed 52.

**A clip rather than a second, stroke-only pass.** The obvious shape is a
`<use>` of the land drawn twice — fill unclipped, stroke clipped — and it
cannot carry this stroke, because a clone inherits `stroke` and does not
inherit `vector-effect`. Duplicating the path data is 26 KB for one hairline.

### What the repair found in the gates

**Two honest answers to a data cut, and the check knew one.** The hero drops
the one country the cut runs through and draws no ground beyond it, so there
is no cut inside the picture. The register draws the ground and clips the
ink. `c_hero_dusk_reach` asserted `"lyr-beyond" not in h`, which is a claim
about the whole document, so it went red for a drawing that was right. It
reads the hero's own `<svg>` now and asks every other drawing the question in
the form that drawing answers it. The third answer — a stroked cut with
nothing hiding it — is what stays refused, and the check is proved red on it.

**`lyr-beyond` had never been a declared layer.** Found by mutation: moving it
under the land proved nothing, because the order check ranked only the names
`cartography.ORDER` knows and `if g in rank` skipped the rest. Declared, and
the converse asserted — every `lyr-` class the site emits must be in the
table.

**And the order check read a page where the promise is about a drawing.** Two
correctly ordered maps on one document read as one page out of order the
moment the second one's first layer ranks below the first one's last. It is
per-`<svg>` now, with a floor on the drawings as well as on the pages.

### Cost

| | |
|---|---|
| `weight.home_kb` | 150 → 173, recorded |
| the register plate | 36 KB: 26 of country rings, 7 of ground beyond, 1.2 of names, 119 bytes of clipPath |
| the ground beyond | 11.5 KB → 7, thinned at 6 units and nothing under 200 square, because it carries no name, no link and no frontier and both are the same picture at this size |

Two more the run caught: the role was declared on the `<figure>` where
`c_map_roles` reads the `<svg>`, which is the slip /countries already paid
for; and `.atsum` carried an eighth `line-height`, a hundredth from two the
file already had.

---

## Plate 05 — the drawing answers the reading, and the line came back as a fill

The register lit the NAME and left the shape alone: the panel said Western
Europe, the word FRANCE went to ink, and France itself stayed exactly the
stone every other country was. The continent is the subject of this band, and
a continent that does not move is a caption with a picture beside it. Every
country carries its corner now — `geo.landmass`'s own `bands` hook — so nine
rules light nine corners rather than fifty naming fifty countries.

| | |
|---|---|
| the water | the plate's ground was `--paper-2`, the page's own paper, so the Adriatic, the Aegean and the Baltic were the same tone as the margin and a bay read as a hole in the land. `--map-water`, which the body glyph family got at the cartography split and this figure never did |
| the lit ground | `--atlas-here` against `--map-land`, which is the step the fifty country portraits already ship and the register the arithmetic of |
| the line | lighting a country whose ring ends on our bbox drew the bbox |

### The line

Two commits, two mechanisms, one diagonal.

| | what drew it | why it was invisible before |
|---|---|---|
| ink | `.lyr-land path` strokes every ring edge, and Russia's ring has one edge that is a meridian | nothing — it was plain, and it was fixed by clipping the land group two units short of the cut |
| fill | the corner light made Russia `--atlas-here` where the ground beyond stayed `--map-land` | the fill had matched on both sides of the cut since the ground beyond was drawn in the same stone |

A cut country is context: shape, frontier, name and link, and no light.
Derived from `europe-lod1.json`'s own rings against its own bbox — one named
country reaches 52.0°E, and Azerbaijan, the next furthest east, stops at 50.6
— so the exclusion lifts itself if the dataset ever reaches the Urals. The
resolve band names it, because /countries already settled that a set shown
short says so.

### The panel was standing on the answer

Measured in Chromium at 1440 with the eastern step lit:

| | |
|---|---|
| plate | x 409 → 1296 |
| the panel's wash begins | x 760 — the eastern **half** of the drawing, at 90% paper |
| the card's own words | over Ukraine's centre (989, 482); `elementsFromPoint` → `.atkick` |
| corners east or south-east | 4 of 9 |

So on nearly half the sequence the band lit ground a reader could not see.
/plan's answer to a scrim over the thing it covers was to stop the overlap;
here the overlap is the composition the brief supplies, so the continent pans.
`.atcue` had been saying *scroll to move through the continent* while the
picture stood still, which is a caption claiming something the page does not
do.

| | before | after |
|---|---|---|
| Ukraine at the eastern step | 913 → 1066, under `.atcard` | 802 → 955, under its own lit path |
| the scrim | `min(34%, 27rem)`, 90% paper at 72% | `min(36%, 28rem)`, 62% at 84% |

Ink on `--map-land` measures 12.5:1 and on `--map-water` 14:1, so the wash was
never doing legibility; 62% is what separation costs.

### Three positions, derived

`data-pan` is a classification the build writes on each step from the mean of
the paths it emitted for that corner's countries — which third of the drawn
span the mass sits in. Four west, three centre, two east. `atlas.js` copies
one attribute to the stage; the stylesheet holds three rules and no geography.

### And the pan revealed the frame

Translating the `<svg>` element moves its crop with it, so the plate's own
`--map-water` showed on the far side as a hard vertical seam at x=1163 — stone
one side, water the other, the full height of the plate. The frame is 1120×800
and the geometry fills it exactly. `PAN_MARGIN` is 170 units of spare
geography each side, `xMidYMid slice` crops the wider viewBox back to 0–1120
to within half a unit, and the pan translates a group inside it. **The
geometry is generated over the panned frame too** — `landmass` clips to the
view it is given, so widening only the viewBox moves the seam a hundred units
out instead of removing it. `weight.home_kb` 174 → 179.

Below 62rem the pan is undone with the stage: nothing is over the continent
there, so a pan would only crop it.

## Plate 05 — the corner lifts, and the continent holds still

The pan above answered a measured fault with the wrong subject. The reader is
being shown a **corner**; the corner is what may move. Everything else is
where it was.

### The direction is derived and the distance is one number

`data-lift` is one of eight compass points, worked out at build time from the
unit vector between two means: every liftable country's drawn centre, and that
corner's own. Eight names are a vocabulary and may be authored here; which
corner takes which is a measurement and may not — the same rule the pan was
written under. One distance for all nine, 18 user units of a 1,460-unit frame,
because a lift that varied with the corner would be nine typed numbers again.

The mean of every liftable country is (591.4, 462.5). In document order,
which is reach descending:

| corner | reach from the mean | lift |
|---|---:|---|
| caucasus-bosphorus | 324 | e |
| british-isles | 269 | w |
| nordic | 259 | n |
| mediterranean | 167 | sw |
| western | 148 | w |
| baltic | 145 | n |
| eastern | 122 | e |
| adriatic-balkans | 103 | se |
| alpine-central | **35** | w |

**The middle of Europe has the least defined direction of the nine**, and that
is a fact about the continent rather than a defect: 35 units against 324. It
still lifts, because a band that does nothing on one of its nine steps is a
promise kept eight times.

### SVG has no `z-index`, so the paint order had to carry it

Probed in Chromium rather than assumed: two overlapping rects, the earlier one
given `z-index: 5` and then `z-index: 5; position: relative`, and the later
rect wins all three times. Document order is the only paint order there is.

So the fifty are grouped by corner and **the groups are emitted
most-peripheral-first**. A corner lifts outward, so everything it can slide
onto is further out than it is, and the order is a construction rather than a
lookup table. The two cases a document order in macro order gets wrong are
what prove it: the Baltic states move north onto Russia, and central Europe
moves west onto France.

### The reorder costs hairlines, and they were counted

Two adjacent countries each stroke their own ring, so on a shared frontier the
later one wins — and the reorder changes which that is wherever the two sit in
different corners. The plate shot at 1280 and 390 with every transition and
every lift frozen, before and after:

| | |
|---|---|
| differing pixels | 2,659 of 1,153,280 — **0.23%** |
| worst delta | 89 of 255 |
| where | hairlines on the Scandinavian, Alpine, Balkan and Caucasus frontiers |

The first draft of the comment on that code said *byte-identical*. That is
what the argument predicted and not what the instrument said.

### What moved with it

`.atdoor` carries the same attribute, because a country name here is placed ON
the country it names. A **cut** country has a corner and no lift: its ring ends
on our bbox, so it may not be moved and may not be lit, and its name un-dims
with the rest of its corner exactly as before — Russia keeps its ground while
Ukraine, Belarus and Moldova lift off it.

`.atcue` said *scroll to move through the continent*, written for the pan and
false in the commit that removed it. `PAN_MARGIN` and `PAN_VIEW` are
`EDGE_MARGIN` and `WIDE_VIEW`: the frame is still wider than the window,
because `landmass` clips to the view it is given and a margin generated over
the narrow frame comes out empty, and nothing pans. `weight.home_kb` 179 → 180
— nine `<g>` wrappers and sixteen attributes.

## Home 38 — the corner lifts out of a socket, not out of a hole

### The lift was measured at the pixel and nobody looked underneath

A corner that moves eighteen units off its own ground exposes what is under
it, and what is under it is the plate's ground — `--map-water`, because *the
band's paper IS the map's water* is the repair that made this drawing a room
rather than an object on a page. So at 2x:

| the step | what opened |
|---|---|
| Alpine & Central | a channel from the Baltic to the Adriatic, through Poland's eastern frontier |
| Mediterranean | Iberia cut off from France at the Pyrenees — an island |

That is not a rendering artefact, it is **a false statement about the ground**,
on the one drawing whose whole argument is that geography is the design. Every
gate was green: nothing in this repository measures whether a drawing still
says something true.

### The socket

Each corner's own shape, left where it was, in the land's own tone, revealed
only where the group has moved off it. Nine `<use>` elements against a second
copy of 26 KB of country rings. Three things had to be right:

| | |
|---|---|
| it clones the INNER group | `#atgi-<corner>` sits inside `.atg`, and `.atg` carries the transform. *A clone takes whatever matches the ORIGINAL in its own position*, so cloning the transformed group moves the socket with the corner — the hole again, with extra bytes |
| it is painted by INHERITANCE | the lit fill is on `.atg[data-corner]` and a clone inherits from its own parent, so `fill` on `.atsock` gives the socket stone while the corner above it is lit. Paint it by id and the socket lights with the corner it stands in for |
| the wrapper had to be renamed | moving fill and stroke onto the LAYER so the clone could inherit them let `.instrmap .countries path` repaint the frontier ink at `rgb(61,68,65)` against `--map-border`'s `rgb(104,113,110)` — a rule that matches the path directly, which inheritance can never beat. `.atland`. **And the note on that rename overstated it**: it said the rename would have shrunk `c_land_credit`'s reach, so the trigger was widened from `class="countries"` to the declared layer `lyr-land` — measured afterwards, 919 pages before and 919 after, zero gained, because the homepage's `class="countries"` is the HERO's drawing. Kept as a guard, not a repair, and proved red through its own path |

### What is refused

*One territory, one outer ink stroke* — the other half of the proposal. The
card beside the drawing says **9 COUNTRIES** and lists nine links, so the
internal frontiers of the lit corner are the doors that count claims exist.
Dissolving them makes the drawing disagree with its own caption. A corner is a
grouping, not a country.

### The instrument counted moving type as opening sea, twice

Shoot the plate per corner with the lift frozen and live; count pixels that
were land and became water.

| classifier | reported | what it actually was |
|---|---|---|
| `blue > red + 4` | 872 on the Adriatic & Balkans | true of water `#DDE8E7` (221/231) and of pine `#0F433E` (15/62). 833 were the words ROMANIA and BULGARIA at their new position — the names travelling with their ground |
| + `red > 190` | 160 on the Mediterranean | Portugal's Atlantic coast under `.atstats`: the lead column's wash lightens the moved coastline's ink over 190 while it stays blue-dominant, 199/204. Washed WATER reads as land by the same arithmetic, so the furniture comes off in both shots |
| + furniture off | 57 on the Caucasus | anti-aliased edges of AZERBAIJAN — a pine fraction between .232 and .249 satisfies both tests. The names come off too; the question is about the geography |

### A hole is an area and anti-aliasing is not

The count alone could never have settled it, so the instrument reports the
largest **connected run** beside it.

| | count | largest run |
|---|---|---|
| eight corners, socket on | 0–1 | 0–1 |
| Caucasus, socket on | 17 | **2** |
| Mediterranean, `.atsock` removed | 9,800 | **2,896** |

Proved red. And the diff map is what diagnosed all three false readings: *a
failure message with no measurement in it cannot be diagnosed*, and a
measurement with no picture beside it cannot be interpreted.

### And the screenshot came back unstyled

`site/` is deleted and rewritten on every build, and the stylesheet's filename
is its content hash — so a page shot mid-rebuild 404s its own stylesheet and
renders as a wall of blue links. That is the ENOENT the browser suite has died
on twice, arriving in a screenshot, where it does not crash: **it produces an
image that looks like a design regression.**

`weight.home_kb` 180 → 181, recorded.

## Home 39 — the four next upgrades were refused, and two instruments were wrong

### The register's own paragraph refuses five of them

The next items on this session's own list were rivers and lakes on the
register, relief inside the lit corner, the shore band, sea names, and a
photograph clipped into the lit corner's lead country. `atlas_register`'s
comment refuses all five in a sentence written when the band was built:

> Plate 01 is the continent as a PICTURE — warm parchment on graphite, four
> relief bands, rank-3 rivers and lakes … A second continent five plates
> down is *the signature as wallpaper* … It is the continent as a REGISTER:
> no water, no relief, no rivers, no lakes, no photograph and no dusk.

Measured on the shipped page rather than taken on trust:

| | plate 01 | plate 05 |
|---|---|---|
| layers | coastal-water, land, **terrain**, **rivers**, country-bounds, water-labels, labels | beyond, land, labels |
| sea names | 5 | 0 |
| photographs clipped into countries | **6** | 0 |

The premise holds exactly, so the refusal survives. `weight.home_kb` refuses
it a second way on its own: the page is at **181 against a ceiling of 181**.

### A plate mark is the band's kicker

`actmark` is *the number is the position and the name is the caption* — so a
composition that carries its own kicker says the band's name twice. Five of
ninety-eight plates did, about a hundred pixels apart:

| page | mark | said again as |
|---|---|---|
| / | The atlas | `<p class="ateyebrow">The Atlas` |
| /events | The European year | `ed-eyebrow` — **four occurrences in one `<main>`** |
| /map | The map | `pagehead` kicker |
| /interests | The interest atlas | `pagehead` kicker |
| /my-europe | My Europe | `pagehead` kicker |

**Which of the two moves is decided by the primitive rather than by taste.**
`ed_opening`'s eyebrow and a `pagehead`'s kicker are required and are that
head's own label, so on four pages the MARK moved — *The fixtures*, *The
instrument*, *All seventeen*, *A private atlas*. The register's eyebrow was a
hand-written `<p>` inside a composition, so there the eyebrow went.

**And the hand sweep that found this found three fifths of it.** It read
eight index pages and the first kicker in each; `c_plate_name_once` reads
every page and every `<h1>`–`<span>`, and found /map, /interests and
/my-europe as well. The test is an element whose WHOLE text is the name,
never a substring, because a band may discuss its own subject in prose.
Proved red on the state that shipped.

### density.js reported a 1,600px hole that does not exist

Its own comment records that a fixed box's rect is viewport-relative and
walks to the clipping ancestor for it. **A sticky box is the same fault one
property over.** The register is a 900px sticky stage inside a 3,240px track
of scroll steps whose eight resting cards are at `opacity: 0`, so everything
was filed in the first 900 pixels and the remaining 1,600 read as 0% covered.

| | before | after |
|---|---|---|
| homepage slices under 20% covered | **34%** | **19%** |
| worst run | 1,600px at 0% | 300px at 2% |

**The exception is measured rather than named.** A sticky element paints over
its containing block's range — and the masthead is sticky with the document
as its containing block, so attributing it would cover every slice of every
page at full width. A sticky element whose range is the whole document is
chrome. Verified from the other end, because a guard that silences an
instrument looks like one that fixes it: /404, /discover, /experiences and
/plan still read 34, 31, 28 and 28.

### And two things the eye got wrong

The vertical rail at the right of the register looked clipped at 1440. It is
not: measured at seven widths from 1024 to 2560 it sits inside the viewport
at every one. And the static suite reported **43,558 dead links** — it was run
while the background build was recreating `site/`, which is the concurrency
failure recorded one screen above, three minutes after writing it down.

## Home 40 — the headline is a protected zone, and the band stopped saying the page's extent a third time

The owner's reading of the live plate 05 was that *the map is doing too much
work, while the actual concept — "Fifty doors" — is not yet visually
convincing*, with a specific rule under it: **no geographic label should ever
cross the headline.** Measured before anything was written, and it is worse
than the report:

| viewport | what crossed what |
|---|---|
| 1280 | ICELAND through `One continent. Fifty doors.` by **109px**; SPAIN through the figures by 43 |
| 1440 | the same two |
| 1920 | **six** — RUSSIA through the card by 104, UNITED KINGDOM and IRELAND through the intro, FRANCE and SPAIN through the figures |
| 2560 | UNITED KINGDOM through the headline by **256px** |

**The drawing had never heard of the page.** `place_label_box` tests every
label against the frame, against its own country's ground and against every
box already `taken` — and `taken` held only what that drawing placed itself.
The headline and the region card are set ON the continent, in the page's own
grid. Nothing called it a contrast fault because the column's wash dims a
name rather than deleting it, so what a reader got was a place name arriving
faintly through a 76px serif, which is worse than either.

### The reserve is a union over viewports, and it had to be

The drawing is `xMidYMid slice` on a 1460×800 frame inside a container whose
aspect runs 1.1 to 5.4, so the scale between the page's pixels and the
projection's units differs on every screen and the same headline lands in a
different part of Europe on each:

| | in the drawing's own units |
|---|---|
| `.mega` at 1280×900 | [48, 67, 345, 326] |
| `.mega` at 2560×900 | [232, 186, 422, 353] |
| `.mega` at 1280×700 | [-97, 70, 284, 403] |

A reserve fitted to one viewport is a fact about that viewport. 385 samples —
twelve widths from 992 to 3440 crossed with seven heights from 640 to 1440,
five scroll positions each, read through the SVG's own
`getScreenCTM().inverse()`. The extremes are driven by ordinary screens: a
1152×640 laptop sets the headline's depth, a 1024×1440 portrait monitor its
width, a 3440×1080 ultrawide the card's left edge.

**The union of the whole COLUMN is refused, measured.** Adding the intro, the
action and the figures takes the left zone to y=846 and the right to x=652:
**eleven of the seventeen names go**, among them UNITED KINGDOM, FRANCE,
SPAIN, RUSSIA and TÜRKIYE — the exact list this repository already records as
the wrong answer, the countries a reader orients by. What is reserved is the
headline and the card, the two pieces of type that are display-size.

**And it is the hull of two readings, because this headline fills its own
measure.** An h1's box is wider than its glyphs — a contrast sweep here once
read 2.15:1 against a real 9.58 for exactly that reason — so the sweep was run
a second time over the headline's own line boxes, expecting the reserve to
shrink. It did not: the glyph union is **narrower by 18 units and deeper by
6**, and neither contains the other. 76px display type on three short lines is
the one case where the trap does not apply. The hull costs no name the box
union did not already cost.

17 names → 11, and every collision with the headline and the card is gone at
every width where the two-column composition applies. The six that went keep
their shape, their frontier, their link and their row in the register column.

### And the six figures came out, because the page says them three times

The lead column carried a six-figure `<dl>` — countries, regions,
destinations, places, experiences, journeys — derived, correct, and an extent
that is not this band's own. Counted on the built homepage, **every one of
them is stated twice more**: plate 01 prints four under the opening and the
footer prints all six. A reader met the site's extent three times before
meeting a corner of Europe, while the number this band IS about was the
closing line a thousand pixels below — `.atsum` has printed *50 countries · 9
corners · 1 continent* since the band was built, which is the chapter
transition the owner asked for and it was already there.

`an index exists to say how big a set is` is the rule that put them there and
the rule that takes them out. `c_home_extent_kept` asserts each figure is
still on the page beside its own word, because *when a band goes, check what
it was the ONLY home for* — proved red by renaming one. The vertical rail went
with them: `Europe through the door` set down the right edge, `aria-hidden`,
repeating the headline's own metaphor in smaller type.

## Home 41 — the door is drawn on what is open, and fifty of them were measured out

The band's own sentence is *One continent. Fifty doors.* and it drew fifty
country shapes with nothing on them that is a door. That is the /themes fault
word for word — a page describing shapes its own closing sentence is about and
drawing none.

**Fifty arches were prototyped and refused on the measurement.** Rendered in
Chromium at 6, 9, 13 and 16 units and photographed at 1× and 2× before a line
of build code was written: at the size that fits the smallest country it is a
texture, and at the size that resolves into an arch it does not fit.
Luxembourg's largest ring spans 8 units and a mark needs about 13 to read as
an arch rather than a tick — so forty-four at one weight draw a second
frontier network over the first, which is *a signature applied to everything
is wallpaper* exactly.

What ships is the same mark on the corner that is **open**: 29 of 44, one per
country that can hold one on its own ground, revealed only on the corner being
read. Never more than nine on screen, and `fifty doors` is demonstrated across
the nine steps rather than asserted all at once. It is a STATE rather than a
selection — every country carries one — so the count is never a judgement
about which countries matter.

Four things had to be got right and three of them are faults this repository
already records:

- **The curve is `render.arch_path`, translated.** A hand-written arc would be
  a fourth drawing of the one shape the aperture is cut from in three
  renderers.
- **The rise is stated.** `arch_path` defaults to `min(h × .34, w × .5)`,
  which is the confident flat span a mason strikes over an opening cut across
  a 900×320 drawing — at glyph size it rendered a **rounded rectangle**. The
  head is struck at half the span, which is the semicircle the wordmark's own
  door has.
- **It sits on its own ground.** The first prototype walked out from the
  bounding-box centre to the first point inside the fill and put Denmark's
  mark in the Kattegat: *a bounding box is not a country*, and a point inside
  the fill is not a box inside it. Five samples now — the middle and the four
  corners of the glyph pulled in.
- **It is inside the transform and outside the clone.** The mark has to move
  with its corner, so it goes in `.atg`; it may NOT go in `#atgi-`, which is
  what the socket clones, because *a `<use>` takes whatever matches the
  ORIGINAL in its own position* and `.atmark` is a bare class selector — a
  mark inside the clone draws a second set of pine doors in the hole the
  corner has just lifted out of.

**And the first run left the British Isles with no door at all.** The type
zones are a union over viewports, which is right for a name with nine anchors
and far too blunt for a 20-unit glyph: both British countries sit inside it,
so the one step of the nine whose corner is two islands said nothing. There
are two rungs now — a mark avoids the zones where it can and takes the ground
under them where that is all there is — which is `NameGround`'s own shape,
zero crossings first and two only if nothing fits.

**The rung could not fire, because `boxes` handed back what it was given.**
`name_countries` starts `taken` as a copy of `reserved`, so extending the
caller's list with the whole of it told the register that its own reserve was
a *name* — hard, not soft. It cost both British doors silently, on a rung
written to stop exactly that. `boxes` is what the pass PLACED.

## Home 42 — a middle rung, because two levels are a switch and not a reading

The corner being read was at full ink and everything else at a third: the
continent flicked between on and off nine times and nothing said where the
corner SAT. A middle rung needs to know which corners are NEXT to the one
being read, and this atlas holds no adjacency — a macro region is a set of
countries, and a hand-written list of neighbours would be an authored
measurement.

It is derived from the same means the lift is: the two corners whose own
middles are nearest this one's, nine pairs out of the drawn geometry. The
result reads as geography — the Nordics next to the Baltic and the British
Isles, the Mediterranean next to the Adriatic & Balkans and Alpine Central,
the Caucasus next to Eastern Europe and the Balkans — and a country moving
corner moves the neighbours with it. **Two rather than three**, because with
three the rung covers more than half the continent and stops being a middle.

`data-near` is a space-separated list and `~=` reads it, so the stylesheet
gets nine selectors rather than eighty-one; `atlas.js` copies one attribute
across, exactly as it copies the corner, and computes no distance of its own.
Measured on the Mediterranean step: 3 names at full ink, 3 at .62, 5 at .34.
