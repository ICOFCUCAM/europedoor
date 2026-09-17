# /journeys — the European Journey Atlas

Four pages, four instruments, one institution.

| page | the question | the grammar |
|---|---|---|
| `/discover` | what are you looking for? | the instrument — graphite, one map, a panel that re-lights it |
| `/countries` | where is it? | the atlas — geography first |
| `/experiences` | what do you want to do? | photography first |
| `/journeys` | **how do you want to move?** | **the route — movement drawn** |

## Part 1 — the source audit

`pages.journeys_index()` built a head and **seventeen identical rows**. Each
row is genuinely good: a strapline kicker, the name, the stops in order, a
`hopbar` laid end to end as the trip's own rhythm, the facts, and a route
glyph framed on that journey's own extent — *no two of the seventeen lines
are alike*, which is the test the homepage's four doors failed and this one
passes. The row was itself a repair: this index used to be four abstract
plates across, and `docs/design-direction-audit.md` records why that went.

The fault is the sum, and it is the same one every other family here has
had. Measured on the built page at 1280: **5,095 pixels, one photograph,
5.9% of the page area.** One shape, seventeen times.

**AND THE FAMILY'S OWN SIGNATURE DRAWING IS BUILT AND NEVER SHOWN.**
`journeys_index` composes `heroart` — all seventeen routes at once on one
conformal conic, casings first and then cores, so crossings do not break —
and hands it to `indexhero(art=…)`. `indexhero` prefers `img` when the
register holds one, and the register holds `journeys-hero`. So the drawing
no other travel product can make is assembled on every build and thrown
away, and what a reader meets instead is a stock photograph of a train.

## Part 2 — the image-coverage audit

| | |
|---|---|
| `journeys-hero` | held &mdash; and spent on the CLOSE rather than the opening, see Part 5 |
| `journey:` rows | 9 of 17 |
| journeys with a photographed STOP on the route | **10 of 17** |
| `story:` rows | 7 of 9 |

**The nine `journey:` photographs are not usable as journey pictures, and
that is recorded rather than my judgement.** `pages.home()` says it: the
automated fill searches the role's first concept and got railways — three of
the nine are the same commuter station at Geesthacht and not one is about its
journey. The homepage already takes the picture it can defend, a destination
ON the route, and this page takes the same one.

## Part 3 — the brief's bands, mapped

| the brief | what it becomes | why |
|---|---|---|
| hero: *Europe is a journey*, route line over photography | the head beside **all seventeen routes**, drawn | a route line drawn over a photograph is geography laid on a picture of somewhere else. The routes are real and the drawing already exists; this is the first page to show it |
| the journey index, no card grid | **kept**, with the index number the brief asks for | it is already rows, and the rows are better than the brief's — they carry the stops and the rhythm |
| manifesto | a pine band, one sentence at display size | |
| featured journey, cinematic | a photograph of a stop **on that route**, its own line, its own legs | |
| light cartographic route instrument | **merged into the hero** | two drawings of the same seventeen routes on one page is the fault this atlas calls the signature as wallpaper |
| Arrive → Cross → Pause → Continue | **the same idea, derived** | see below |
| journey stories | the essays whose subject is moving | |
| Slow / Deep / Grand | **the same idea, derived** | see below |
| *Where will the road take you?* | the close, and it carries `journeys-hero` &mdash; the family's own photograph, set behind the question | the picture goes where a picture does work type cannot, and the opening keeps the drawing no competitor can make |

### The four movements are derived, not authored

The brief names Arrive, Cross, Pause, Continue. A leg carries `nights`, and
that is the same claim measured: a stop of three nights is a pause and a stop
of one is a crossing. The band draws one real journey's own legs at their own
lengths, so the four movements are that journey's shape rather than four
words about journeys in general.

### The three paces are a measurement with a classification on top

The brief names Slow, Deep and Grand. No journey record carries a pace —
`type` is `route` on all seventeen and `creator` is `EuropeDoor editorial` on
all seventeen, so neither can cut anything. What the data holds is
**straight-line kilometres per day**, and it separates cleanly:

    30 km/day   The Alpine Grand Tour       509 km over 17 days
    38          The Danube Line             610 over 16
    …
    120         The Mediterranean Arc     2,514 over 21
    147         Arctic to Mediterranean   4,993 over 34
    319         Camino & Sacred Europe    4,780 over 15

The Data Integrity Rule permits authoring a classification and forbids
authoring a measurement: the number is derived and the three names are
editorial. The page prints the rule that cut it, the way every
`/europe-in/*` page prints the query that made it. And the figure says
**straight line**, because every distance in this repository is a haversine
between two coordinates and this atlas holds no road or rail geometry —
which is the one number a reader could act on and be wrong about.

## Part 4 — what is refused

**The animated route line.** The brief asks for a line that feels animated.
These pages load no JavaScript, and a CSS dash animation on a route would be
motion that decorates rather than explains — the line is already the whole
argument, and a moving one says nothing the still one does not. Refused, with
the trigger stated: motion here would have to express something the drawing
cannot, and direction is already given by the order of the stops.

**The decorative arc over the photograph.** The prototype draws the hero's
route as a rotated ellipse border. Every line on this site that looks like a
route is a route: `pages.route_line()` draws real legs between real
coordinates, with a casing under the core because cream land is 0.70 of
luminance and the Atlantic is 0.055 and no single stroke clears 3:1 on both.

**The prototype's map.** Its `<path class="land">` shapes are a drawing of
nowhere. All geometry here comes from `data/geo/`, fetched, hashed and
registered — nothing is traced or eyeballed.

## Part 5 — what only rendering found

Five defects, every one of them invisible to a count and to the whole static
suite, and four of the five are faults this repository has already recorded
in another family.

**AN UNRESOLVABLE `var()` MADE THE DATA-CUT FADE THE ONLY THING PAINTING
SEA.** `.roadart .constel` took `background: var(--map-sea)` — the name
`docs/palette.json` uses for the light map's water, where the stylesheet's
token is `--atlas-sea`. The declaration is invalid at computed-value time and
`background-color` does not inherit, so the panel fell back to `transparent`.
The drawing paints no ocean of its own; the panel does. So the seventeen
routes sat on the band's own white, and `cut_fade()`'s two ramps — which
paint `--atlas-sea` at rising opacity toward 52°E and 33°N — were the only
sea on the picture. Measured on the rendered pixels: rgb(255,255,255) off
Iberia, rgb(221,232,231) in the Black Sea, on one drawing. **The fade exists
to stop a straight data cut reading as a rendering fault and, with nothing
under it, was one.** Four lines from the stylesheet's own paragraph about
unresolvable tokens.

**THE NIGHTS BAR AND THE LEGS WERE TWO DRAWINGS OF THE SAME EIGHT THINGS ON
DIFFERENT GRIDS, TOUCHING.** The bar is the journey's rhythm — eight segments
at their share of the eighteen nights — and the legs under it are a
five-across grid of equal tracks, so segment three does not sit over Piran
and never can. Both drew the same 2px accent rule, twenty pixels apart. The
bar read as a mis-drawn header for the grid rather than as the measurement it
is. Two things separate them: the bar is a captioned `<figure>` now, stating
what it draws the way every chart here does, and the cards' rule dropped to
the page's hairline. Nothing counts a rule that reads as a promise it cannot
keep.

**THE PAGE HAD NO HEAD AND NO EXTENT, AND `checks.py` SAID BOTH.** A plate
sequence has no room for a stage above its opening, so /experiences had
already settled where the head goes: the band that introduces the SET. The
seventeen band is `pagehead index` now and states the count, because *an
index exists to say how big a set is and five of eight once did not*. The
figure is derived; a number typed there is the number that was true two
hundred destinations ago.

**THE REGISTER WAS CLAIMING A SURFACE THE PAGE HAD STOPPED REACHING.**
`journeys-hero` is a licensed photograph of a train in a forest, and the old
index opened on it. The moment the opening became the drawn seventeen-route
continent nothing on the page asked for that key, and `c_photo_published`
said so in the first run after the rebuild — which is the check earning its
place, on exactly the fault it was written for. It is not put back into the
opening: *a photograph replaces the drawing, it does not sit behind it*, and
the drawn continent is the one picture on this page no competitor can
reproduce. It goes on the CLOSE, as a declaration — type over the picture
behind a scrim that makes the ratio a property of the design. 72% graphite
composites to rgb(76,83,82) and bone on that is 6.90:1 whatever the frame
turns out to be, which is `.credit`'s own arithmetic and not a second number
for one decision. **Ten `<img>` where the old page drew one, and nothing was
acquired**: the featured route's lead and three of its stops, the essays that
name a place these routes pass through, and this.

**THE PACE SENTINEL WAS PRINTED AS A CLAIM.** The last band has no ceiling,
and the first version used `10**9` as the loop's upper bound and then set it
in the sentence: *"under 1000000000 km a day"*, on the page, to a reader. A
bound that exists for the arithmetic is not a bound that belongs in a
sentence.

## Part 6 — measured

| | before | after |
|---|---|---|
| page height at 1280 | 5,095 | 12,281 |
| picture in the first screen at 1280 | — | 69% |
| picture in the first screen at 390 | — | 10.9% |
| `<img>` on the page | 1 | 10 |
| document overflow at 390 / 834 | 0 | 0 |
| distinct body shapes over 47 families | 29 | 35 |

The phone opening is the one number that stays low, and it is the same
10–12% /experiences measures for the same reason: the type stacks above the
picture, so the first screen is the kicker, the headline, the standfirst and
a sliver of map. `opening.js` has no threshold on purpose — *the fault it
exists to find is a page that is DULL, and a number to satisfy is satisfied
by shuffling bands* — and raising it here means putting the drawing above the
headline, which is shuffling a band to move a number. Recorded rather than
chased.

## Part 7 — three gate bugs found on the way, none of them about /journeys

All three were already there and all three ended `photo-tests.py` on a
traceback rather than on a failure, which reports nothing and leaves every
later block unrun.

**A block that must SUCCEED owns its starting state.** The suite runs against
the LIVE register and `acquire.py` refuses a purpose the register already
fills, so the block that acquires a PNG for `homepage-hero` stopped acquiring
the moment a real photograph was merged there. Its own `returncode == 0`
assertion caught it — and the next line opened the file the acquisition had
not written. The three batch blocks had it too, on `homepage-hero`,
`stories-hero` and `country-hero@austria`: a block whose whole subject is
telling a deliberate skip from an accidental one reported three skips where it
expected one.

**And freeing the register row was not enough, because a file name comes from
the purpose.** The first version of that repair let the following acquisition
write its stub over two licensed originals, and `cleanup()` then restored a
register naming a hash of bytes no longer in the repository — `keep` protects
a file from deletion and says nothing about it being overwritten. The files
move aside and come back now.

**An assertion pinned `gh pr create` after it moved into `open_pr.sh`**, so
`wf.index()` raised. Two repairs: it reads the workflow's steps rather than
its raw text, because the first `tools/checks.py` in that file is in a comment
and an instrument that reads the documentation of code as code is wrong; and a
marker it cannot find is a failure naming what it looked for, never an
exception.

**And the homepage's own builder crashed on an empty pick list.** `picks` is
one photographed destination per macro region and `contact_sheet.py` renders
the page with a register holding ONE row, so it is empty there by design.
Every other band on that page is guarded by `if inner` in the plate loop; this
was the one that could never return an empty string because it died first.


---

## Part 8 — the doctrine audit

`docs/redesign-doctrine.md` arrived after this page shipped, so both of its
audits are filled in here from the evidence above rather than from memory.
Every line that is not satisfied says so.

**Monotony**, measured at 1280: **33%**, seventeen `row journeyrow` siblings, next two 5% and 4%. The highest figure of the pages rebuilt under the brief, and the subject of the page is a set of seventeen journeys, so the list is not the fault; what the second figure says is that there is little else, and the opening — all seventeen routes drawn at once — is what carries the page.

### CONTENT PRESERVATION

- [x] every important existing content item retained — every journey in the
      dataset (the count is `docs/content-report.md`'s, and derived on the
      page), every stop in order, every derived distance
- [x] existing counts retained and derived — including the extent, which the
      page had never stated
- [x] existing links retained
- [x] existing destinations retained
- [x] existing relationships retained — a leg is a relation and the routes
      are drawn from it
- [x] existing functionality retained
- [x] existing data loaders reused — `glyph_view`, `route_line`, `haversine`
- [x] existing map engine reused — the seventeen routes are the family's own
      signature drawing, which was built on every build and thrown away
- [x] existing image and provenance system reused — 1 `<img>` to 10, and
      **nothing was acquired**

### DESIGN TRANSFORMATION

- [x] the page has a new composition
- [x] the existing card/grid structure was not merely reskinned
- [x] the opening communicates the page's purpose — movement, drawn
- [x] the content hierarchy was reconsidered
- [x] photography has an editorial role — `journeys-hero` carries the CLOSE
      as a declaration, because a photograph replaces a drawing and does not
      sit behind it
- [x] the map or the data has a meaningful visual role
- [x] the sections have different visual rhythms
- [x] the page does not read as a CMS listing
- [x] the page has a memorable signature moment

### Notes, including what this audit does not claim

**33% is worth re-reading rather than defending.** Seventeen rows each
carrying a route drawing, a name, a pace and its stops in order is a
composition repeated seventeen times, which is what this instrument is for —
and it is also what the page IS. The honest next question is whether the three
paces (derived from measured kilometres a day) should set three rhythms the
way /countries' nine regions now do. Recorded with that as the trigger, not
ticked.
