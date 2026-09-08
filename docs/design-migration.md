# §6 — Design migration, as a controlled experiment

Nothing in this document changes the site. It defines how a visual change is
run, what the control is, and what the first subject should be.

An experiment needs a control. `docs/invariants.json` is it: **21 things that
were true before a change and must still be true after it**, recomputed on
every build. Moving one is allowed. Moving one *silently* is not.

---

## 6.1 The pipeline

    current visual state
          ↓  measured, and recorded as invariants
    token migration
          ↓  the semantic layer only; no rule touches a raw hex
    surface classification
          ↓  which world each page belongs to
    component-level changes
          ↓  the eleven primitives, never a page
    generated plates
          ↓  one hue table, two renderers
    map
          ↓  five --map-* tokens
    social cards
          ↓  regenerated from the same plate_shapes()
    mobile
          ↓  390 × 844, every page shape
    full regeneration
          ↓  every page rebuilt from data
    red-team
          ↓  break each new guarantee deliberately
    green

**Each stage is verified before the next begins.** The order is not arbitrary:
tokens before components because components consume tokens; plates before
social cards because the cards are rendered from the plates; mobile before
full regeneration because a layout failure at 390px is cheaper to find on one
page than on all of them.

## 6.2 The control: the invariant register

`docs/invariants.json`, written by `tools/invariants.py --write` and
recomputed by `checks.py` on every build. Three kinds:

| kind | meaning | examples |
|---|---|---|
| **exact** | must equal this | one page shell · one masthead and one footer per page · one stylesheet · three font families · **zero** webfonts · zero inline styles · zero `<img>` tags · zero golds · five applications · the route set's hash |
| **ceiling** | must not exceed | distinct font sizes · font weights · line heights · breakpoints · box-shadows |
| **floor** | must not fall below | each of the eleven primitives' reach across pages |

**A ceiling is a line, not a target.** Thirteen font sizes is not a number to
defend to the death; it is one that should only be crossed on purpose, in a
diff somebody reads.

**Every invariant carries a `why`**, and a row without one fails the build. An
invariant nobody can explain is one nobody can decide to change.

**`routes.hash` is the one that matters most for a visual migration.** A
restyle must not move a URL — every inbound link, every social card and every
sitemap entry depends on that set. Verified by renaming one route function and
watching the build go red.

## 6.3 What has already run through this pipeline

The European Future migration, in the order above. Recording it here because
the protocol was followed before it was written down, and the evidence is what
makes the protocol credible rather than aspirational.

| stage | evidence |
|---|---|
| token migration | one `:root` block; 240 rules consume `--paper`/`--ink`, none consumes a raw hex — which is why it was one commit |
| surface classification | five INTELLIGENCE pages plus every embedded map figure; asserted in both colour-scheme preferences |
| contrast verification | 31 claimed pairings and 10 refusals, every ratio recomputed from the hexes |
| component changes | the primary button became the signature; source-tier badges lost brass; score bars became a gradient. **No primitive was restructured** |
| plates | six hues, both renderers, from one table |
| map | five tokens |
| social cards | 794 regenerated in 18 seconds |
| mobile | 390 × 844, zero overflow |
| regeneration | every page |
| red-team | fifteen deliberate attacks, fifteen red builds — `docs/visual-architecture.md` §5.14 |

## 6.4 The first subject for the next experiment: the plates

**The question is not "how do we make generated images look like
photography".** It is *can the generated plates become a coherent visual
atlas* — something more distinctive than stock, not a substitute for it.

To answer it I rendered forty plates as a contact sheet and looked at them.
Three defects fell out that reading the code would not have found, and one
thing I got wrong by eye.

**1. One of the seven motifs is unreachable.** `plain` is never drawn.
`motif_for()` maps `food → plain`, but every destination in the atlas matches
an earlier interest — mountains, islands, coast, sacred, cities,
architecture, nature, wine, art all come first — so `food` is always
pre-empted. The hash fallback that could also pick `plain` never fires,
because `motif_for()` never returns `None` for any of the 319. A seventh of
the visual vocabulary is dead code.

**2. The night light can be clipped into an unreadable glyph.** In
`plate_shapes()` the sun or moon is emitted before the motif, so a `skyline`
whose towers rise past it occludes it. On Lille's night plate the lime moon
survives as a crescent sliver that reads, at card size, as a stray character.
It is one draw-order line.

**3. Motif selection does not read `city_type`, which now exists on all 319.**
Civita di Bagnoregio — a village on an eroding tufa pillar — is drawn as a
city skyline. Exactly one destination is affected today, which makes this
small; it is listed because the fix is to feed a classification the plates
were built before we had.

**And a correction to my own reading.** From the contact sheet I judged
skylines to be roughly 38% of plates. Measured across all 319 they are **28%**
— skyline 90, peaks 81, coast 57, tower 53, forest 19, isles 19. The sample of
forty was biased and the eye was wrong; the distribution is healthy. This is
recorded because the mistake is instructive: **a contact sheet is good for
finding defects and bad for measuring proportions.** Look to find, count to
conclude.

## 6.4a The experiment, run — results

All three fixes as one controlled change, rebuilt, and inspected at the size a
card is actually looked at rather than at generation resolution.

### A — motif reachability: FIXED

`plain` is drawn on **8 destinations**. All seven declared motifs are now
reachable, and reachability is an invariant (`plates.motifs_reachable`), so a
motif cannot silently become dead code again.

### B — the sliced light: FIXED, and it was systemic

The light is no longer emitted before the motif at a seed-chosen height. It is
appended after the silhouette is known, fitted to the sky that exists above
it, and inserted behind. Where there is no sky, the plate simply has no moon —
which is a real thing a night city looks like, and better than a sliver.

**Lille was not a one-off. 69 of 319 destinations — 22% — had a light sliced
by a tower or a spire.** 54 skylines and 15 towers. It was invisible because a
single plate looks plausible; only the set, at card size, shows it.

**And the first fix introduced a different defect.** Pushing the light up with
no floor jammed it against the frame on the tallest skylines — Bucharest,
Turin, Amsterdam and Chișinău all gained a cropped half-moon on the top edge.
Found the same way, by looking at the sheet again. The light is now *fitted*
rather than *pushed*: never more than a third of the available sky, with a
clear margin top and bottom.

A geometric check now asserts, on all 319 plates at both output sizes, that
the light is inside the frame and clear of every narrow shape. Reverting the
fix produces 40 failures; the check was watched going red before it was
trusted.

### C — `city_type` consumed: FIXED, narrowly

**And the first attempt was wrong in an instructive way.** Mapping all eight
classifications to motifs put a *universal* field above the interest pass, so
the interest pass stopped running: `forest` fell from 19 plates to 1. One dead
motif traded for another.

The shipped version maps only the five classifications that are visually
**decisive** — village, site, island, valley, park — and leaves capital, city
and town to the interests, because what a settlement is *for* describes it
better than its size does. Topography still gets first refusal: Theth is a
mountain village and draws peaks, not a plain.

### The measured result

| motif | before | after | Δ |
|---|---:|---:|---:|
| skyline | 90 | 89 | −1 |
| peaks | 81 | 83 | +2 |
| coast | 57 | 57 | 0 |
| tower | 53 | 50 | −3 |
| forest | 19 | 13 | −6 |
| isles | 19 | 19 | 0 |
| **plain** | **0** | **8** | **+8** |

**11 plates changed motif, of 319.** A small, targeted change — which is what
the experiment was supposed to produce. Civita di Bagnoregio, a village on an
eroding tufa pillar, is no longer a skyline of tower blocks.

### Newly discovered, and not fixed

| finding | judgement |
|---|---|
| skyline lights are now visibly smaller than those on peaks and coast plates | a consequence of fitting to available sky. Consistent, and reads as a distant sun above a city — but it slightly weakens the family resemblance across the set |
| Postojna & Škocjan, a cave system, draws a tower | `site → tower` assumes a monument. One destination; not worth a sixth mapping |
| Albarracín, a town of about a thousand people, is still a skyline | the deliberate trade in C: `town` is left to the interests. It remains the weakest plate in the sheet |

### The verdict on the atlas question

**The generated system is stronger than it was and is not yet a flagship
visual language.** It now has seven working motifs, no rendering faults, and a
classification feeding it. What it does not have is variety *within* a motif:
two mountain towns are still interchangeable, because the only thing that
distinguishes them is a hash.

That is the next experiment, and it is also zero-cost. **No photography
purchase is justified yet** — the free system has not been exhausted.

## 6.4b Experiment D — variation within motifs

**Measured first, as instructed.** The result inverted the assumption the
experiment was proposed on.

### The instrument was wrong three times before it was right

Worth recording in full, because each wrong version produced a confident
number that looked like a finding:

| version | method | what it reported | why it was wrong |
|---|---|---|---|
| 1 | bounding boxes of each primitive | *peaks: 92% duplication* | a ridge polygon spans the whole frame, so its box is the frame and its min-y is the single highest peak. Every peaks plate collapsed to one constant vector |
| 2 | + polygon scanline | *isles: 79% duplication* | isles is drawn from **ellipses**, which the scanline ignored, so every isles plate was the flat water line |
| 3 | + ellipses | *isles: 74% duplication* | isles' islands sit **below** the horizon. They are interior detail and never touch the silhouette at all — the metric could not see the thing that varies |
| 4 | **render at 64×40 and compare pixels** | the numbers below | measuring a drawing requires drawing it |

**Look to find, count to conclude — and check the counter.** Three
plausible-looking measurements in a row were artefacts of the instrument, not
properties of the atlas.

### The measured baseline, by rendering

| motif | n | mean d | nearest d | twin pairs | % of pairs |
|---|---:|---:|---:|---:|---:|
| skyline | 89 | 0.182 | **0.069** | 3 | 0.1% |
| tower | 50 | 0.178 | 0.021 | 41 | 3.3% |
| coast | 57 | 0.132 | 0.013 | **125** | **7.8%** |
| peaks | 83 | 0.122 | 0.025 | 32 | 0.9% |
| forest | 13 | 0.196 | 0.028 | 3 | 3.8% |
| isles | 19 | 0.118 | 0.020 | 10 | 5.8% |
| plain | 8 | 0.253 | 0.019 | 3 | 10.7% |

A *twin* is a pair whose rendered plates differ by under 2% of pixel value.

**This contradicts the claim that prompted the experiment.** "Two mountain
towns are still interchangeable" was wrong: **peaks is the second-most varied
family** (0.9% twin pairs), and **skyline — which I had eyeballed as the most
repetitive — is by far the most varied** (0.1%). The genuinely flat families
were **coast** and **isles**: a thin ridge over a large plane of identical
water.

### The smallest possible change, applied and measured

No new motifs, no new primitives, no new concepts. In order:

**1. Seed the parameters that were constants.** Coast's headland count was
fixed at 4 and its depth at 0.10h; isles always drew exactly 4 islands at
`horizon + 0.05h + i·0.09h` — a fixed ladder. Seeding those four numbers, and
adding no shape at all:

    coast   125 → 82 twin pairs
    isles    10 →  5

**2. One compositional variant, on the family still worst.** A headland
reaching into the water from the side the light is not on, on about half of
coasts. One polygon, no new colour:

    coast    82 → 25 twin pairs   (7.8% → 1.6%)

**3. The same treatment tried on tower, and REVERTED.** Tower's width was also
a constant. Seeding it moved 41 twin pairs to 42, which is noise — a tower's
similarity comes from the whole composition, not from one width. **Reverted
rather than kept, because a change with no measured benefit is a change that
only looks like progress.** The constant is still there, with the negative
result recorded beside it.

### Result

| motif | before | after |
|---|---:|---:|
| coast | 125 | **25** |
| isles | 10 | **5** |
| tower | 41 | 41 (unchanged, deliberately) |
| everything else | unchanged | unchanged |

Confirmed by rendering coast, isles, plain and peaks at card size and looking:
the headlands break the flat water, and the islands no longer sit on a fixed
ladder.

### The gate

`tools/plate-variation.py --check` records a **ceiling** on twin pairs per
family. Variation is easy to lose by accident — a constant reintroduced, a
seeded range narrowed — and the loss is invisible on any single plate.
Reverting the headland fails it by name: *"coast: 82 interchangeable pairs,
ceiling 25 — the family got more repetitive."*

It is deliberately **not** in `tools/checks.py`: it renders 319 plates and
compares every pair, which takes eight seconds, and a gate that slows every
build is a gate people stop running.

### Still open

| finding | measured |
|---|---|
| `plain` is the flattest family | 10.7% of pairs are twins — but n=8, so 3 pairs. Low priority until more villages exist |
| ~~`tower` did not respond to the minimal treatment~~ | ~~41 twin pairs, 3.3%~~ — **answered in §6.4c. It responded to a different constant, and the sentence above named the wrong reason** |
| skyline lights are smaller than other families' | from §6.4a. Geometrically safe, not yet visually normalised |

**The verdict on the atlas question, updated.** The generated system now has
seven reachable motifs, no geometric faults, classification-aware selection,
and measured variation with a ceiling on it. Two families remain flatter than
the rest and both are small. **It is closer to a flagship visual language than
it was, and still no photography purchase is justified** — the free system has
not been exhausted, and each experiment so far has cost nothing and found
something.

## 6.4c Experiment E — why the 41 tower twins were twins

**The instruction that set this up was to measure before changing.** Not
"vary tower"; *"investigate the 41 tower twin pairs, but only after measuring
why they are twins. If the duplication comes from one constant, test that
constant. If it comes from the composition itself, test the smallest
compositional change. If neither produces a measurable improvement, leave
tower alone."* That order is the whole result below, because the answer this
experiment gives is one no amount of looking at the drawing had produced in
three previous attempts.

### The instrument: ablation

The twin count says a family is repetitive. It cannot say **which layer** is
responsible, and `tower` draws seven of them. So `plate-variation.py --ablate
tower` deletes each primitive in turn, re-renders all 50 plates and re-counts
the twins. A layer whose deletion changes nothing was distinguishing nothing;
a layer whose deletion makes the family *more* varied is hiding the part that
does.

| layer | coverage of the plate | twins without it | delta |
|---|---|---|---|
| ridge-back | **41.1%** | 44 | +3 — noise |
| ridge-front | **25.8%** | 35 | **−6 — it was hiding what varies** |
| nave | 6.3% | 49 | +8 |
| shaft | 4.0% | 47 | +6 |
| spire | 0.6% | 44 | +3 |
| cornice | 0.3% | 41 | 0 |
| light | 0.8% | 53 | +12 |

**Two thirds of a tower plate is two ridges, and neither was doing any work.**
The shapes that distinguish one tower from another — the nave and the shaft —
paint 10% of the frame between them, and the foreground ridge was drawn last,
over their bases.

This is why the §6.4b attempt failed. It seeded `tw`, the shaft width: the
4% layer. It was the shaft that *looked* like the subject of the drawing.

**Reading a negative delta requires knowing what is underneath.** Deleting a
layer reveals the layer below it, so if that one varies more, the result reads
as "occludes" whether or not anything is wrong. `isles` reports −4 on its
water — and under that water there is only the sky gradient, which varies by
hue on every plate. The water is doing its job. Tower's −6 was real because
what sat under that ridge was the base of the nave and the shaft: the two
layers the same run had just named as carrying the variation. **The delta
locates a suspect; what lies beneath it settles the case.**

### The four tests, in order, smallest first

| # | change | twins | verdict |
|---|---|---|---|
| — | baseline | 41 | |
| 1 | seed both ridges' amplitude and segment count — *the exact treatment that took coast from 125 to 25* | **41** | **no effect at all.** Kept nothing |
| 2 | seed the foreground ridge's drop, the constant the ablation named | **32** | kept |
| 3 | widen the tower height range | 31 | **one pair — noise, and it changes the drawing's proportions.** Reverted |
| 4 | seed the nave height, pinned at a fixed 0.42 of the shaft | **27** | kept |

**41 → 27 twin pairs, 3.3% → 2.2% of pairs, nearest-neighbour distance
0.0207 → 0.0245.** Two constants seeded. No new shape, no new colour, no new
concept, and eleven lines of diff.

Test 1 is the one worth keeping in mind. The coast fix was a *good* fix, and
applying it to the next-worst family was the obvious move — it moved nothing.
**The same repair does not transfer between motifs, because the layer that
was constant is not in the same place twice.** Only the ablation says where
to reach.

### Confirmation, not just a smaller number

Re-running the ablation after the change is the check on the diagnosis:
`ridge-front` moved from **−6 (occluding what varies)** to **+7 (carrying
variation)**. It is now doing the opposite of what it was doing. That is a
prediction made before the change and confirmed after it, which a twin count
alone could never have supplied.

Rendered at card size before and after, and measured: the tower is *more*
visible on average, not less — mean 207 → 221 painted pixels of 2,560, range
159–262 → 148–327. The foreground band now sits at a different height on each
plate instead of the same one on all fifty.

One honest note: the single closest pair, Echternach / Toledo, got marginally
closer (0.0086 → 0.0077). Individual pairs move both ways under a change that
improves the aggregate, and the aggregate is the thing being measured.

### What was NOT done

`plain` is untouched. It has the highest twin *percentage* of any family
(10.7%) and n=8, which is three pairs — a denominator too small to learn
anything from. **A percentage over 28 pairs is not a finding.** It waits for
more villages in the dataset, not for more code.

### The ceiling moves

`docs/plate-variation.json` records tower at **27**, down from 41. Restoring
the fixed `0.16h` foreground drop fails the gate by name — *"tower: 40
interchangeable pairs, ceiling 27"* — exit 1. Verified, not assumed.

## 6.5 What must stay distinct while the identity changes

The migration must **not** turn every page into INTELLIGENCE. The worlds stay
apart:

    DISCOVER                    INTELLIGENCE
    warm                        graphite
    editorial                   precise
    spatial                     interactive
    cinematic                   data-led
    human                       functional
    place-led                   system-oriented

**But the transition must feel like one product, not two websites.** That is
what the door metaphor is for, and it is a *state language* rather than a
decoration:

    DISCOVER → PLAN → ENTER → EXPERIENCE

The interface moves a reader through those states — a destination page offers
the planner, the planner opens the map, the map returns to a destination —
without ever announcing the machinery. **"AI" appears in no masthead, no
navigation and no `h1`**, and a check enforces that today, before there is
anything to name. The assistant is EuropeDoor Guide.

The mechanism that already makes this work: one set of components, with
`<body data-world>` selecting which semantic tokens they resolve to. Two
worlds, one product, because it is literally one stylesheet.

## 6.6 Red-team protocol

A guarantee is not a guarantee until it has been seen failing. For every new
check:

1. State what it protects, in the failure message, in terms a reader who has
   just broken it would understand.
2. Break it deliberately, in the same session.
3. Watch the build go red.
4. Restore, and confirm green.

Twenty attacks have been performed and recorded across §5.14 and this
document. The two most recent: renaming a route function to move a URL
(`routes.hash` went red) and adding a `fetch()` to a 36-line enhancement
(the application boundary went red).

**A check that has never been seen failing is a check that may not be
checking anything.** This repository has already shipped a browser suite that
printed *"all 4 browser checks passed"* while 540 ran.

## 6.7 What would stop this

The migration stops, rather than proceeding under an assumption, if any of
these appears:

| trigger | why it stops |
|---|---|
| licensed photography becomes necessary | STOP → licensing investigation → budget → explicit decision. No assumed rights, no "probably fine", no citation for a licence nobody read |
| a change requires a new primitive | prove the structure has appeared three times first. The burden is on the new component, not on the eleven that already cover the site |
| a change requires a webfont | it is an `exact` invariant at zero, and a third-party origin in a `default-src 'none'` policy |
| a change moves a URL | `routes.hash` fails. A visual change is not a content change |
| an invariant moves and nobody can say why | the register requires a reason per row |

## 6.8 The order of authority, applied to design

    PRINCIPLES → BUILT SYSTEM → MEASUREMENTS → CHECKS →
    ARCHITECTURE → FUTURE EXTENSIONS

Applied here: the plates are not a placeholder to be replaced because a
flagship concept wants more emotion. They are 2,377 drawings that already
exist, already cohere, and have three measured defects. Fix those first and
look again. That is cheaper than a photography budget and it might be better.
