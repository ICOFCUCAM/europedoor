# The Europe discovery loop

*search → discovery → exploration → saving → personalization → planning →
return → new discovery*

This document is the architecture of the visitor loop: how a reader who
arrives once comes back, and what makes the second visit different from the
first. It is written the way everything else here is written — the existing
system measured first, the gaps named with numbers, and every proposed
mechanism carrying the rule it must not break.

**It is not a plan to build eight features.** Seven of the eight transitions
already exist in some form, several of them well; the loop does not close
because of one missing stage and two narrow edges. Naming which is the whole
value of the audit, because the alternative is building a personalization
engine on top of a product that has no reason to be visited twice.

## 1. The loop as the site implements it today

Measured on the sources and the built site, 2026-09-18.

| # | transition | verdict | the measurement |
|---|---|---|---|
| 1 | **arrive → search** | **BUILT** | `/search` filters 1,062 records across twelve kinds in the browser, and its resting state lists every kind so the index is browsable without searching at all. The figure is read off `site/api/search.json` rather than quoted: it was 1,064 until the `FACET_MIN` floor took two sub-category pages off the site, and this document nearly shipped the older number while arguing for derived counts |
| 2 | **search → discovery** | **BUILT, and honest about failure** | a zero-result query re-runs itself with each modifier dropped in turn and names the ones that would bring results back — *"nothing for that"* was the old version, and it taught people the search was broken rather than that Czechia is not a low-cost country |
| 3 | **discovery → exploration** | **BUILT, five ways** | `/discover` (an instrument that re-lights the continent as the reader picks), twelve `/europe-in` motions, seventeen `/interests`, thirteen `/themes`, 130 quiet places on `/beyond-the-obvious` |
| 4 | **exploration → saving** | **BUILT, and wide** | a save button on 1,129 records across six kinds — Place 893, Experience 197, Journey 17, Theme 13, Story 9, and Itinerary, which the Planner creates |
| 5 | **saving → personalization** | **TWO EDGES, AND THAT IS ALL** | of 1,032 pages, **two** read the reader's own state: `/my-europe` (which owns all three storage keys and derives a Travel DNA) and `/plan` (one checkbox, *use my saved places*, which weights the route). Nothing else on the site knows a reader has ever saved anything |
| 6 | **personalization → planning** | **BUILT, narrow** | that one checkbox. `applyAsk` does not set it, so the sentence box cannot reach it — the same shape as the party-size defect already recorded, where the form was right and the sentence was not |
| 7 | **planning → return** | **BUILT, and it is the model for the rest** | `planUrl` carries the **route** rather than the inputs, deliberately, because the planner jitters and re-planning would return something slightly different. So a shared link is the same itinerary; My Europe stores nothing but that link; and there is no account anywhere in it |
| 8 | **return → new discovery** | **ABSENT** | see §3 |

## 2. What the loop is made of

Five applications and two enhancements. Most of the site loads no JavaScript
at all, which is why the loop's state is so small and so legible:

| key | owner | read by |
|---|---|---|
| `europedoor.saved.v1` | `my-europe.js` | `my-europe.js`, `planner.js` |
| `europedoor.collections.v1` | `my-europe.js` | `my-europe.js` |
| `europedoor.dna.v1` | `my-europe.js` | `my-europe.js` |

Three keys, one owner, one other reader. Nothing is sent anywhere, there is
no account, no session and no analytics — which is a constraint on every
mechanism below and is also the product's position, published on the page
that holds the saved list.

## 3. THE LOOP HAS SEVEN STAGES AND A FULL STOP

**Nothing a reader sees on this site is a function of time.** The whole build
calls `datetime.date.today()` exactly once, and it is the verification
freshness derivation — a check expiring after `REVIEW_DAYS` so a record reads
as *due for review* again. Not one of the 1,032 pages is different on a
second visit.

The one mechanism that could be is the stories feed: `/stories/feed.xml`,
discoverable from 1,031 pages, nine entries, published between 2026-08-14 and
2026-09-06 — one every three days, and **the newest is twelve days old.** The
return stage is not unbuilt so much as unfed.

So *"I wonder what EuropeDoor will show me today"* currently has no
mechanism at all, and the reason it has none is worth stating precisely
rather than treating as an oversight.

## 4. THE CONSTRAINT THAT DECIDES THE SHAPE: A "TODAY" SURFACE CANNOT READ THE CLOCK

Two independent rules make the obvious implementations impossible, and both
are already enforced.

**A build-time date breaks the staleness contract.** `site/` is generated,
committed, and CI fails when it is stale; `c_built` re-derives the expected
page count from `data/` on every run. A page whose content is a function of
the wall-clock date is correct on the day it is built and stale the morning
after — so the honest-looking version of this feature turns CI red every day,
and the pressure to fix that would be to weaken the check.

**A runtime rotator has been costed and refused twice.** `data-rotate` held
four alternative placeholders on the homepage for the life of that band and
nothing ever read them, because the homepage loads no JavaScript. The living
atlas sequence was built, measured and removed for the same reason, and its
removal was argued on numbers: the register held destination photographs
inside exactly one of the six featured countries, so a cross-fade would have
put the first script on the most-visited page to animate one country.

**Therefore the change has to arrive as committed data.** That is not a
workaround, it is the only form of *today* this product can keep honest: a
rotation whose input is a file in the repository is a rotation somebody can
review, a check can assert, and a reader can be told the rule for.

## 5. The three findings

**FINDING 1 — SAVING IS WIDE AND PERSONALIZATION IS TWO PAGES.** 1,129
records can be saved and two surfaces read the result. A reader can spend a
month building a collection and the Atlas will look identical on every page
of it except the one that lists it. This is the cheapest gap to close and the
easiest to close badly, because the obvious version — reorder things the
reader has shown interest in — is a **ranking**, and this product publishes
that there is nothing in its index that could carry one. Any mechanism here
has to change *what is offered* without changing *what is ranked*.

**FINDING 2 — THE RETURN STAGE IS ABSENT AND ITS ABSENCE IS STRUCTURAL.**
§3 and §4. No clock, no rotator, one stalled feed.

**FINDING 3 — THE ONE RETURN EDGE THAT IS BUILT IS THE BEST THING IN THE
LOOP, AND IT IS THE PATTERN TO COPY.** The planner puts the whole itinerary
in the URL, states that the link carries the route itself rather than the
inputs, and says so to the reader in those words. State in a URL, nothing
stored on a server, and the sentence on the page telling the reader exactly
what the link is. Every stage below should be judged against that standard.

## 6. What the loop needs, in the order the measurements justify

Stated as architecture with the gate each part must clear. **Nothing here is
built.**

**A. The daily face — `data/today.json`, rotated by a scheduled workflow.**
One committed file naming what today's surface shows; the build reads it as
data like anything else, so `site/` stays reproducible and the staleness
contract holds. The rotation is a commit somebody can read, revert and
audit — which is the same decision as the photograph pipeline, where the
pull request is the approval boundary. The rule the surface publishes must be
derived, not curated: *the destination whose verification is freshest*, *the
motion whose result set changed*, *the month that is in its shoulder now* are
all facts this atlas already holds. A hand-picked "place of the day" is an
editorial record and needs an editor, which is a content decision rather than
an architectural one.

**B. Personalization as a WIDENING, never a reordering.** The saved set may
add a band — *of the twelve motions, these four contain places you have
saved* — and may never change the order of a list, a score, or a search
result. That keeps every published refusal true and keeps the mechanism
checkable: a page must be byte-identical for a reader with an empty store and
a reader with a full one, except inside a container declared for the purpose.
That is assertable today by rendering with and without a seeded store, which
is how the crop boxes and the focus rings are already measured.

**C. The sentence box reaching the saved set.** `applyAsk` sets seven inputs
and not `form.saved`, so *"ten days from Kraków, places I have saved"* does
nothing. The readback already exists and already promises to name anything it
could not take account of; this is one input inside a mechanism that is built.

**D. The feed as the return promise it already is.** Nine entries and twelve
days of silence is the whole of the current answer to *why come back*. The
architecture does not need changing; the publication does.

## 7. What this refuses, and the trigger for each

| refused | why | trigger |
|---|---|---|
| an account | the product's published position is that the saved list lives in the reader's own browser and nowhere else, and there is no incorporated entity to be a data controller | `docs/legal-position.md` §3 |
| analytics, or any measurement of what a reader looked at | there is no analytics of any kind here, which is what makes *nothing was sent anywhere* true rather than aspirational | none; this is the position |
| a recommendation that reorders anything | ranking is refused in the schema and published on `/for-businesses`; discoverability is published as explicitly not a crowd measurement | none |
| an email capture | nothing on this site accepts a submission — zero `method="post"`, one `action`, and it is a GET to `/plan` | an entity, and a reason better than growth |
| a runtime rotator on the homepage | costed and refused twice, on the numbers | several featured countries holding photographed destinations |
| a clock-derived page | breaks the staleness contract CI depends on | none; §6A is the answer instead |

## 8. How any of it would be proved

The instruments exist, which is the reason this is worth attempting now
rather than a year ago: 10,793 browser checks, 121 static checks over 271,224
examined things, `tools/monotony.js` on composition, the content report,
the invariant register, and the provenance gates. A discovery feature is
exactly the kind of work that breaks an atlas quietly, and every one of those
is a tripwire already in place.

Three new instruments would be needed and each is small:

1. **A two-store render.** The same page rendered with an empty store and a
   seeded one, asserted byte-identical outside the declared container. This
   is the guard that keeps personalization from becoming a ranking.
2. **A rotation assertion.** Today's surface must state its own rule, and the
   rule must be derived from the dataset — the same contract every count on
   this site already carries, because a figure typed into a page is the figure
   that was true on the day somebody typed it.
3. **A loop reachability measure.** For each of the eight transitions, that a
   reader can get from one stage to the next in one click on the built site.
   Seven of the eight can be measured today, which is what makes the eighth's
   absence a number rather than an opinion.
