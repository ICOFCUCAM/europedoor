# /my-europe — the Personal European Atlas

The owner's brief: MY EUROPE → PRIVATE ATLAS → YOUR MAP → THREE KINDS OF
MEMORY → FUTURE ATLAS → PRIVACY → BUILD YOUR EUROPE, and four sentences that
decide the whole thing —

- *Most importantly, I kept the current product philosophy rather than
  inventing an account-based system.*
- *Reuse the existing My Europe local-storage/save-state architecture and
  replace only the presentation layer. The saved places, journeys and stories
  should remain real data — not decorative mock entries.*
- *"Nothing saved" treated as an elegant empty-state experience, not an error
  message.*
- *Privacy elevated into part of the actual product design rather than buried
  in legal copy.*

All four are held. Nothing about how this page stores anything changed.

## Part 1 — the source audit

**A HEAD, A DRAWING, TWO EMPTY CONTAINERS AND A FOOTNOTE.** 27,264 bytes:
`pagehead instrument`, `constellation([])` inside `#minemap`, `<div id="mine">`
and `<div id="dna">` for the runtime to fill, and one `.note` paragraph
carrying the privacy position. Nothing in it was wrong. What it did not do is
say anything at all to the reader who has saved nothing — which, on a page
whose whole content is written by a script from `localStorage`, is **the state
the page ships in and the state most readers see.**

| | before | after |
|---|---|---|
| bytes | 27,264 | 32,831 |
| plates | — | 7 |
| `<h2>` bands | 2 | 6 |
| head role | `instrument` | `instrument` — unchanged |
| runtime hooks | `#minemap`, `#minecap`, `#mine`, `#dna` | the same four, untouched |
| `<img>` | 0 | 0 |
| JavaScript | `my-europe.js` | `my-europe.js` |

## Part 2 — the defect the audit found, which is not a design defect

`my-europe.js` sorts a reader's collection with

    var ORDER = ["Itinerary", "Place", "Journey", "Theme", "Story"];

and the built site offers **six** save kinds, counted off the `data-kind`
attribute of every `data-save` button in `site/`:

| kind | save buttons | in `ORDER` |
|---|---:|---|
| Place | 893 | yes |
| **Experience** | **197** | **no** |
| Journey | 17 | yes |
| Theme | 13 | yes |
| Story | 9 | yes |
| Itinerary | 0 | yes |

**`ORDER.indexOf("Experience")` returns −1**, which sorts every saved
experience in FRONT of everything — ahead of `Itinerary` at index 0. A kind
the application does not know is not dropped and does not throw; it is sorted
first by accident, so nothing ever looked broken. One line, and it is the
reason this page's own audit was worth doing before its presentation layer
was touched.

**AND `Itinerary` WAS THE OPPOSITE SUSPICION, WHICH IS WHY IT WAS CHECKED.**
It is offered on zero pages, which is the exact shape of *a motif nothing
reaches is dead code that looks like vocabulary* — and it is real:
`planner.js:1755` pushes `kind: "Itinerary"` when a reader saves a route the
Planner built. It stays, and it stays first, because it is the only one of the
six the reader **made** rather than chose. *Checking a suspicion is what
stopped a wrong repair.*

## Part 3 — three kinds of memory are six

The brief's band 4 is *three kinds of memory* and its sentence is the good
half: **places tell you where, journeys tell you how, stories tell you why.**
It is right about the grammar and short by three. Naming three of six is the
`pop_line` shape — a taxonomy that omits part of its own set reads as a
policy — so the band keeps the sentence and covers all six, each with what it
answers and how many there are to choose from:

| | | derived |
|---|---|---:|
| Place | Where. Every destination and every place inside one. | 574 |
| Experience | What. The things worth crossing a country for. | 197 |
| Journey | How. Routes already worked out, stop by stop. | 17 |
| Theme | Why, across the continent. One argument, eight places. | 13 |
| Story | Why, in one place. The piece that made you look. | 9 |
| Itinerary | Yours. What the Planner builds when you ask it a question. | built by the Planner |

Every figure is computed on the build; the six sentences are editorial. *The
Data Integrity Rule in both directions on one band.*

**And this band IS the empty state.** *Nothing saved* is answered by saying
what there is and where it is, rather than by an apology or one "start
exploring" button: a reader who has saved nothing wants the door, and a reader
who has saved plenty still wants to know what else is savable. The same band
serves both, which is why it is not gated on the list being empty — a
server-rendered page cannot know whether the list is empty, and a band that
appeared only in one state would need JavaScript to decide it.

## Part 4 — the brief's monumental opening, refused with a measurement

The prototype opens on a large centred headline. This site has the
measurement that refuses it: *an instrument's title is a label, because the
page is the tool*, taken from a head pushing the instrument to **y=436 on
/plan, 449 on /map and 460 on /search** — half the first screen of a tool
spent on a magazine headline. All five INTELLIGENCE pages carry
`pagehead instrument`, /plan and /discover included as they were rebuilt
earlier in this same series, and the register asserts exactly one role per
head.

What the brief actually asks for — *personal and considered rather than a
dashboard* — is what the seven bands do, and it does not need the h1 to be
60px to do it.

## Part 5 — the seven plates

| | class | what it is |
|---|---|---|
| 01 | `meopen gal` | the instrument head, and one line saying where this lives |
| 02 | `meatlas pine` | the drawing, unchanged, in the dark room |
| 03 | `melist gal` | `#mine` and `#dna` — the two runtime containers, untouched |
| 04 | `mekinds gal quiet` | six kinds of memory, derived — and the empty state |
| 05 | `mefuture gal` | three futures, each naming what it would take |
| 06 | `privacy pine` | the three storage keys, and the cost of the promise |
| 07 | `mebuild gal` | build your Europe |

**Band 05 names its own price.** Sync needs an account, a backend and a data
controller; a shareable list needs a server and a decision about what a shared
link exposes; handing a saved list to the Planner needs no backend at all and
is the nearest. *A refusal nobody can check is a slogan* — the same form
/plan's six refusals take.

**Band 06 states the mechanism and never repeats the promise.** The opening
says this lives in your browser; the privacy band says which three keys, that
no request carries them, that no identifier is attached, and that clearing
browser data deletes them **because there is nowhere else they exist** — which
is the cost, stated rather than hidden. Saying "private" twice would be
*never explain the constraint back* applied to a promise instead of a filter.

**The dark map band is deliberate and is not the thing the brief objects
to.** The brief says no *swampy* dark map treatment and it is right; the
cartography split already answers it, because a drawing takes its palette from
what it IS — a picture is paper and an instrument is graphite — and the navy
swamp it names is the five raw hexes that went when the instruments got their
palette. The brief's own prototype keeps this band dark.

## Part 6 — the defects only rendering found

**`.minemap .constel` WAS CAPPED AT 30rem, SO THE PAGE'S CENTRAL INSTRUMENT
DREW AT 480px IN A 1,152px BAND.** 42% of its own room, on the one drawing
whose caption says *the emptiness is honest — you can see how much of Europe
you have not chosen yet*. That is `/themes`' 204-pixel continent and the
`.card-art` letterbox, a third time: **nothing counts a cap.** `width: 100%`
→ 1152 × 899 at 1280.

**`.sheet-pine` SETS NO `display`, SO BOTH PINE BANDS LANDED IN A 40% TRACK.**
`.sheet` is `grid-template-columns: minmax(0, 40%) minmax(0, 1fr)`, and only
`.sheet-gal` ends `display: block`. This is the **third** occurrence of that
repair in three commits — /stories' feature band shipped at 205 × 154 of
photograph at 1280, /events' year band fell from 1,152 pixels to 619 — and the
answer is the same every time: a composition that is one child of a `.sheet`
states its own display.

**`sheet-kinds` WAS ALREADY EMITTED BY /experiences WITH NO RULE ANYWHERE.**
Grepped in both directions before naming anything, which is the lesson
`.sheet-year` cost one commit earlier: **a class name with no rule in the
stylesheet is still taken**, because the built site is the other half of that
grep. Renamed `mekinds`. `c_plate_class_owner`, written in the /events commit,
now fails on this automatically.

## Part 7 — what is NOT here, and why

| asked for | why not |
|---|---|
| an account | the product philosophy the brief asks to keep. There is no server anywhere in EuropeDoor |
| mock saved entries so the design can be seen | *the saved places, journeys and stories should remain real data* — the brief's own sentence, and the one thing that would make this page lie |
| a photograph | the register holds no `my-europe` purpose, and inventing one would put a stock European scene on the page whose subject is the reader's own choices. The drawing IS the picture here |
| a second map | one arch per page. The saved atlas is the signature moment and a second would be the wallpaper its own rule warns about |
| a share button | band 05 says what it would need. A link that exposes a reader's list is a decision about somebody else's data, not a feature |


---

## Part 8 — the doctrine audit

`docs/redesign-doctrine.md` arrived after this page shipped, so both of its
audits are filled in here from the evidence above rather than from memory.
Every line that is not satisfied says so.

**Monotony**, measured at 1280: **10%**, six `row mekind` siblings, the lowest figure of any page rebuilt under the brief. The page's central instrument is a drawing and its saved entries are written by the application at runtime, so there is very little repeated markup to measure.

### CONTENT PRESERVATION

- [x] every important existing content item retained
- [x] existing counts retained and derived — all six save kinds, each with
      its own figure
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained
- [x] **existing functionality retained, and this is the load-bearing line on
      this page** — the three `localStorage` keys and the four runtime hooks
      (`#minemap`, `#minecap`, `#mine`, `#dna`) are exactly what they were,
      and a placeholder inside `#mine` is the one thing that would have made
      this page lie
- [x] existing data loaders reused
- [x] existing map engine reused
- [x] existing image and provenance system reused

### DESIGN TRANSFORMATION

- [x] the page has a new composition — seven plates
- [x] the existing card/grid structure was not merely reskinned
- [x] the opening communicates the page's purpose
- [x] the content hierarchy was reconsidered
- [x] photography has an editorial role
- [x] the map or the data has a meaningful visual role — 1,152 x 899 where the
      page's own instrument had been capped at 480px in a 1,152px band
- [x] the sections have different visual rhythms
- [x] the page does not read as a CMS listing
- [x] the page has a memorable signature moment — the emptiness is honest

### Notes, including what this audit does not claim

**The monumental opening stays refused**, on a measurement this site already
holds: an instrument's title is a label, because the page is the tool.
