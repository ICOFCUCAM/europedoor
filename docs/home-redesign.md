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

