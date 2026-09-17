# /stories — the European editorial desk

Four indexes, four instruments, one institution.

| page | the question | the grammar |
|---|---|---|
| `/discover` | what are you looking for? | the instrument — graphite, one map, a panel that re-lights it |
| `/countries` | where is it? | the atlas — geography first |
| `/experiences` | what do you want to do? | photography first |
| `/journeys` | how do you want to move? | the route — movement drawn |
| `/stories` | **who lives there, and what happened?** | **writing first, and the pictures spent** |

Every count below is derived on the build that produced this document, and `docs/content-report.md` is the generated record that owns them.

## Part 1 — the source audit

`pages.stories_index()` is 144 lines and most of them are comments recording
two repairs it has already had. It was nine three-column grids each holding
one card — 5,792 pixels, the desk taxonomy as the layout — and then a
contents page whose middle third was empty, and then a lead with its own
constellation over eight rows. Every one of those repairs was right.

**What it is now, measured on the built page:**

| | |
|---|---:|
| bytes | 31,882 |
| `<img>` on the page | **1** |
| `<h2>` on the page | 9, every one a story title |
| section heads | **0** |
| `.row` | 8 |
| drawings | the lead's own places, and nothing else |

So the page is a head, one photograph, one lead and eight identical rows. The
fault is the same sum every other family here has had: **one shape eight
times, and every picture the register holds spent on one surface.** That is
the /experiences finding word for word, on the family whose material is
writing.

## Part 2 — the image-coverage audit, and the library is not the constraint

| | |
|---|---:|
| `stories-hero` | held — a Liechtenstein village, which is the page's only picture today |
| `story:` rows | **7 of 9** |
| photographs available to this page | **8** |
| photographs the page spends | **1** |

The seven are History, People, Food, Travel, Culture, Places and Nature. The
two without are **Faith** and **Adventure**.

**AND THE LEAD IS ONE OF THE TWO.** The page picks its lead by date and says
why in its own source — *"an index of nine essays has room to say which one
to read first, and the answer is the newest — a date, not a judgement."* The
newest piece is *The long walk nobody finishes*, filed to Adventure on
2026-09-06, and the register holds no photograph for it. So the brief's
**large photographic lead** cannot be the lead unless the lead stops being
chosen by date, which would make it an editorial judgement wearing a rule's
clothes — the thing this page already refused once.

## Part 3 — the brief's nine bands against what this atlas holds

| the brief | what it becomes | why |
|---|---|---|
| **story atlas** | **refused as the opening**, kept as a band lower down | the page already refuses it in writing, and the reason survives re-checking: *a scatter of nine stories' places is not chosen by a hash and is still a picture of nothing in particular standing in front of nine pieces of writing.* As the band that says reading and planning are the same motion, further down, the same drawing is about something |
| **nine editorial desks** | **refused**, stated as a line | nine desks and nine stories is a **1:1 mapping** — a desk band is nine headings over one item each, which is literally the layout this page threw away. `docs/product-specification.md`'s own rule: design to purpose, not to data shape |
| **large photographic lead** | the lead by date, typographic today | see Part 2. It becomes photographic on its own the day the register holds Adventure |
| **feature story** | kept, and it is a different question from the lead | |
| **editorial ledger** | **kept exactly as the brief asks** — typographic, all nine | the brief's own best decision, and it agrees with what is already there |
| **large cinematic story photography** | **the seven, at size, each linked to its own piece** | this is where the eight photographs go. A story's picture belongs to that story, so a strip of seven captioned with their desks spends what the library holds and invents nothing |
| **editorial philosophy** | kept | the page already publishes the sentence; it becomes a band rather than a footnote |
| **desk-based discovery** | **refused** — the duplicate of band 2 | |
| **Atom feed** | kept | already built, already declared in the shell |
| **final door** | kept | |

### What the data refuses, with the count

| band | the data |
|---|---|
| a byline treatment | `author` is **"EuropeDoor editorial"** on all nine. A byline band would print one name nine times |
| a tag cloud or tag-led discovery | **36 tags across the nine and 34 of them are used once.** A tag index would be a scatter with no structure, and two of the three repeats are `poland` and `walking` |
| reading-time as a sort or a filter | the nine run 5 to 9 minutes. A four-minute spread is not a choice a reader makes |
| a "most read" or "editor's pick" rail | this atlas holds **no visitor numbers for anywhere** and says so at `/method`; `featured` is refused by name on every editorial record |

## Part 4 — what is known before anything is built

The register holds eight photographs for this page and it spends one. The
nine pieces are one shape eight times. Neither of those is a licence
position and neither needs anything acquired.

## Part 5 — the bands as built

| # | band | what it is |
|---|---|---|
| 01 | **The desk** | a broadsheet masthead: the claim at display size across the measure, the extent under it, and `stories-hero` leaving the page entirely as a bleed. The photograph belongs to the PAGE and carries no story's title |
| 02 | **Everything filed** | the ledger, kept: the newest piece at size with its own places drawn, then the eight rows. `pagehead index` states the extent |
| 03 | **A story is not a place** | pine. The page's own editorial position, promoted from the last paragraph at caption size to a room |
| 04 | **Photographed** | the seven, at size, each linked to its own piece, in two packed columns |
| 05 | **Where they happen** | the 32 destinations the nine essays are set in, drawn at 960 pixels |
| 06 | **The feed** | the Atom feed as an ACTION rather than a `.note.onward` |
| 07 | **Read one, then go** | the close |

## Part 6 — what only rendering found

**A CLASS NAME ALREADY IN THE STYLESHEET IS A RULE YOU INHERIT SILENTLY,
FOUR TIMES ON ONE PAGE'S RUN.** `.sheet-send` is /journeys' close — a
graphite band built to carry a photograph behind a 72% scrim — so naming
this plate `send` gave the last thing a bone publication says light type on
near-black. It joins `.sendsay` (bone on white, about 1.1:1),
`.closesay` (a 32rem cap that left the statement 512 pixels wide inside a
1,152-pixel band) and a `.deskart figcaption` rule written twice with an
identical body eighty lines apart. **Grep the stylesheet before naming a
composition** — there is no guard, and none of the four is visible to any
suite here.

**A MARK IN USER UNITS IS A DIFFERENT SIZE AT EVERY WIDTH, AND THE RULE
CORRECTING IT HAS TO OUT-SPECIFY THE ONE THAT SET IT.**
`.constel-theme:not(.framed) .constel-lit circle` is `r: 22px` — right on a
/themes row, drawn unframed at the whole continent inside a 288-pixel cell —
and at 960 pixels across a 1,000-unit viewBox it rendered each of the 33
places **42 pixels wide**. The obvious `.storyplaces .constel-lit circle`
is (0,2,1) against that rule's (0,3,1) and lost, which renders as the change
simply not being there. 8.6 pixels at 1280, 6.4 at 390.

**AND THE INDEX HEAD INSIDE A PLATE IS ONE RULE NOW, BECAUSE THE STRUCTURE
HAS APPEARED THREE TIMES.** `.pagehead.index` is a three-column head — the
extent beside the name — which on a block plate puts the kicker alone in
the left half and the title starting at x=400. /experiences wrote its own
override for that; /stories' ledger needed the same one. *No new primitive
until repeated structure has actually emerged* cuts both ways, and a second
rule with an identical body is the duplicate this stylesheet removed 85 of
one commit ago. Promoted to `.sheet > .pagehead.index`, and /experiences was
shot at 1280, 834, 390 and 320 before and after: every box identical.

**AN `<a>` INSIDE AN `<a>` IS NOT NESTED — THE PARSER CLOSES THE FIRST
ONE, AND THE SELECTOR THAT REVEALED THE CREDIT STOPPED HAVING A SUBJECT.**
Each of the seven picture tiles is a link, and `picture()` emits the Pexels
credit as a `<figcaption class="credit">` **inside** the `<picture>` — which
put an anchor inside an anchor. Chromium does what the HTML parser is
specified to do and ends the outer `<a>` at the inner one, so the credit's
links became siblings of the tile rather than descendants of it, and
`picture:focus-within .credit { opacity: 1 }` had nothing to match:
**21 links of 3,685 painted nothing even with focus on them.** That is
`.doorgo`'s finding arrived at from the other end — there a class carried an
`opacity: 0` nobody expected, here the rule that clears it lost its subject —
and it is the same class of defect, because `getComputedStyle` reads
`opacity: 1` on the link itself either way. The tile is a `<figure>` now:
`picture(..., credit=False)` inside the link, and one
`<figcaption class="piccred">{credit_html(row)}</figcaption>` outside it.
Pexels' terms are satisfied by a credit that is *visible*, and a credit
standing under the tile is more visible than one revealed on hover.

**A CLAMP SOLVED FOR EQUALITY IS NOT A CLAMP THAT FITS.** `.sheet .mega`'s
floor was made width-aware to stop `recommendation.` breaking mid-word at
320, and the arithmetic — 320 pixels of glyph at 48px inside a 288-pixel
column, therefore 43.2px, therefore 13.5vw — was done *before* the change,
which is the repair this repository already records for the overture h1. It
was still wrong: measured after, the word came out **288.0 against a box of
288.0** and broke anyway, because a word wraps when it does not FIT and
equal is not smaller. *A floor one page from its threshold is a check that
fails without saying anything* — recorded here about a palette ratio, and
true of a type clamp in exactly the same way. 12.8vw is 40.96px at 320, the
word measures 273.1 in 288, and the headroom is 14.9 pixels rather than
none. Proved with a Range-rect probe over eight families at 320 and 390: a
word occupying two client rects is a word split, and there are none.

**AND A DECLARED CROP BOX NAMED A CONTAINER NEITHER PAGE EMITS.**
`experiences-hero` and `stories-hero` both declared `.iheroart`, which is
`indexhero()`'s figure — and neither index calls `indexhero()` any more.
A selector that matches nothing has no aspect ratio, so the browser suite's
sweep reported *no box larger than 4px at any of 40 viewports*, which is the
green-assertion-about-nothing fault the crop-box measurement was rebuilt to
catch, arriving in the commit that rebuilt the two pages. Re-measured on the
containers that exist: `experiences-hero` renders in `.xshot` at 0.731
(834x900) to 1.501 (1280x640), guaranteed frame **30.1%**; `stories-hero` in
`.ed-bleed.ed-bleed-tall`-styled `.storybleed` at 1.778 (320x640) to 2.333
(1024x640), frame **47.2%**. Both clear the 12% floor.

**AND ONE DECLARATION WAS DEAD BECAUSE THE BASE RULE ALREADY SAID IT.**
`.storyplaces .constel { display: block }` restates `.constel { display:
block }`, declared thousands of lines above it. The dead-rule scan named it
in the first run after this page existed.

## Part 7 — measured

| | before | after |
|---|---|---:|
| bytes | 31,851 | 52,545 |
| `<img>` on the page | **1** | **8** |
| photographs the register holds for it | 8 | 8 |
| photographs acquired | &mdash; | **0** |
| bands | a head, a lead and eight rows | **seven plates** |
| page height at 1280 | &mdash; | 8,361 |
| document overflow at 1280 / 834 / 390 / 320 | 0 | 0 |

The before height is not in that table because it was not measured: the
previous build's page is in git and its stylesheet is content-addressed, so
serving the old HTML resolves to a filename that no longer exists and lays
out unstyled. A number obtained that way would be a measurement of nothing,
which is the failure this repository records about a sampler reading outside
its own image.

**AND THE FIX FOR THE NESTED ANCHOR LEFT THREE OF THE TILE'S FOUR
DECLARATIONS BEHIND, ONE OF WHICH A READER COULD SEE.** `.picstory` was an
`<a>` carrying `display: block`, `break-inside: avoid`, `text-decoration:
none`, `color: inherit` and a margin. Making the credit's own two links legal
moved the class onto the `<figure>` and put the anchor inside it — and the
declarations stayed on the class:

| declaration | after the move |
|---|---|
| `break-inside: avoid`, `margin` | still the tile's, correct |
| `display: block` | a `<figure>` already computes it — **dead** |
| `color: inherit` | `a { color: inherit }` already does it — **dead** |
| `text-decoration: none` | on a box that is not a link, while the UA's `underline` applies to the anchor's subtree |

The dead-rule scan named the first two and the third is the one that mattered:
measured by serving the stylesheet with and without an override, **the seven
story titles in the photographed band were underlined** — 34px of display
serif with a rule through it, in the commit that fixed the credit. A dead
declaration is the **symptom** here rather than the fault: two of the three
changed nothing and the third changed the wrong element, and only the scan
looks for either. `.picgo { text-decoration: none }` puts the decoration on
the thing that is decorated.
