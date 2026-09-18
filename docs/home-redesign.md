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

