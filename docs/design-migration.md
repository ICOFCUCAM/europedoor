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

**None of the three is fixed here.** They are the subject of the next
experiment, run through §6.1 with the register as its control.

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
