<!-- GENERATED IN PART: the coverage table's verdicts are authored, and the
     figures in it are asserted by tools/checks.py and tools/ad-tests.py.
     Do not hand-edit a number here; change the registry and re-run. -->

# The commercial layer — §1–33 mapped, then built

Advertising infrastructure now, advertising display later. This document is
the map the brief asked for **before** anything was built, the departures
from its letter with the measurement behind each, and the evaluation at the
end of what it did and did not close.

## The one structural difference, stated once

The specification is written for a running application: a Postgres database,
an admin UI, a REST service, React components, `ADVERTISING_ENABLED` in the
environment, Stripe later. EuropeDoor is **1,032 generated HTML files with no
server, no database, no session and no runtime dependency**, serving
`default-src 'none'` with no `'unsafe-inline'` in any directive.

Every section below therefore has an *equivalent* rather than a literal
implementation, and in four places the equivalent is **stronger than what was
asked for**:

| asked for | here | why it is stronger |
|---|---|---|
| `ADVERTISING_ENABLED=false` in the environment | a field in a committed registry | an environment variable can be flipped without a commit, a review or a diff. This cannot: switching it on is a pull request |
| "no ad scripts load" | there is no script to load | the site ships five scripts and none of them is this one. Not suppressed — absent |
| "zero advertising tracking at launch" | there is no analytics of any kind | nothing to disable, and `docs/legal-position.md` records why |
| "do not integrate a third-party ad network" | the CSP makes one impossible | adopting one changes the security posture of all 1,032 pages, which is recorded as an owner's decision rather than a build step |

The one place the letter is **not** followed is §10's ten components, and
that departure is argued in its own row.

## §1–33, mapped

| § | asks for | verdict | what it is here |
|---|---|---|---|
| 1 | infrastructure on, serving off, and the eight-line status block | **BUILT** | `ads.status()` derives those eight lines from the registry and /for-businesses prints them, so the claim cannot drift from the mechanism |
| 2 | one global flag defaulting to false; nothing renders, no empty box, no reserved space | **BUILT** | `serving.enabled: false`, and an off slot emits **zero bytes** — no container, no placeholder. Proved by the layout-shift sweep: every family measures 0.0000 |
| 3 | advertising as a separate domain, not scattered | **BUILT** | `tools/lib/ads.py` and `data/advertising.json`. No page builder contains selection logic; it calls `for_surface()` and gets a list, which is empty |
| 4 | advertisers, campaigns, creatives; nine campaign statuses | **BUILT** | the registry carries all three tables with the specified fields and all nine statuses. `creatives.image_url` is declared and **refused in data** — see the creative row below |
| 5 | nine named placements, all `enabled = false` | **BUILT** | the brief's own nine slugs, each with its surface, format, disclosure and `enabled: false` |
| 6 | targeting on six dimensions; no behavioural advertising | **BUILT** | a closed vocabulary of exactly those six. `language` is declared and unreachable today because one locale ships |
| 7 | contextual relevance from the path | **BUILT** | `ads.context_for(path)` reads the same route table `render.ed_family()` uses, so a context and a page family cannot disagree |
| 8 | organic ranking never modified | **BUILT, and it was already enforced** | `rank`, `boost`, `featured`, `sponsored`, `promoted` have been refused on every place and experience record in the schema *and* at the file level since before this brief; a campaign now refuses nine keys of its own |
| 9 | the Guide and the ad system independent; "Sponsored partner" label | **BUILT** | a check asserts `planner.js` contains no reference to the registry, and that /plan's six published weights are unchanged |
| 10 | ten React components | **DEPARTED, measured** | `render.ad_slot(path)` and `render.ad_disclosure(label)`; the ten *products* are data. Ten components differ in what they target and what they say, not in their box — and this repository's rule is *no new primitive until repeated structure has actually emerged*, after forty-seven page builders each passing a family string was replaced by one table. Ten components is ten places for one disclosure to differ |
| 11 | every slot hidden at launch | **BUILT** | asserted on the built site: zero pages carry a slot marker |
| 12 | an admin interface, seven areas | **DEFERRED** | needs authentication and a backend, which is the gate every account feature here sits behind. The Media Desk is the precedent for how it would be built: a second Vercel project, never on europedoor.com |
| 13 | a campaign creation form | **DEFERRED** with §12 | the *shape* it would submit is in the registry, so the form has something to be checked against |
| 14 | draft → submitted → review → approved → scheduled → active, rejectable with a reason | **BUILT** | the nine statuses, a transition table, and a validator that refuses a transition the table does not name. No UI |
| 15 | a business dashboard, and "Advertising is not currently available." when off | **PARTIAL** | the dashboard needs accounts. The sentence is publishable today and is on /for-businesses, which is the page a business actually reads |
| 16 | analytics events defined, none firing | **BUILT** | five event names declared. Stronger than asked: no analytics runs at all, so there is nothing to suppress |
| 17 | explicit disclosure; never Recommended / Popular / Top choice / Best | **BUILT** | a closed disclosure vocabulary, and those four words refused on any page carrying a placement |
| 18 | Sponsored / EuropeDoor Editorial / Recommended by the Guide kept distinct | **BUILT** | three declared provenance labels, mapped onto the four claim origins `/manifesto` already publishes (Verified, Editorial, Computed, Community) |
| 19 | five inventory products | **BUILT** | all five are among the nine placements |
| 20 | six revenue models, no payment processing | **BUILT** | declared as a list; none implemented; no payment provider; the entity gate |
| 21 | no third-party network at launch | **BUILT, stronger** | impossible under this CSP, and a check refuses a named ad host in any page or script |
| 22 | no sensitive-category targeting | **BUILT, stronger** | the target vocabulary contains no such dimension, and there is no user profile anywhere in this product to build one from |
| 23 | prepare sponsored map results; distinguishable marker | **DECLARED, off, with an objection attached** | the placement exists and is off. The objection is recorded rather than decided: a mark on a map here is drawn only where the page can name it — 176 of 176 across the fifty country plates — and a paid pin is a dot whose reason the page cannot state. It is what has to be answered before the flag flips |
| 24 | sponsored search results, never replacing an organic one | **DECLARED, off, with an objection attached** | same shape. A paid row is either ordered among the organic ones, which is buying an ordering, or it is not a result at all |
| 25 | an `AdvertisingService` with eight methods | **BUILT** | eight functions in `ads.py` with those names. The four write methods raise until there is an entity, rather than returning a falsy value nobody checks |
| 26 | five feature flags, four phases | **BUILT** | the five flags and the phase order, declared. Nothing activates simultaneously because each flag is independent and each phase names what it requires |
| 27 | the EuropeDoor visual language, always with the disclosure | **BUILT** | the slot uses existing primitives. **No new token, no new type size, no new breakpoint** — the invariant register would refuse one and it should |
| 28 | zero ad JavaScript, no requests, no reserved space | **BUILT, measured** | zero bytes of ad markup on 1,032 pages, and the layout-shift sweep is the proof that nothing is reserved |
| 29 | automated tests for the OFF state, and a simulated ON | **BUILT** | `tools/ad-tests.py`, 44 assertions. It asserts the OFF state, then simulates a fully configured campaign **in memory** — not a temporary file, because a suite that edits the registry it is testing can leave the repository in the state its own failure produced, which the Media Desk's suite learned the harder way when it renamed two licensed originals aside and a later run overwrote them. It asserts the rendered band, the required `rel`, the hostile-creative refusals, that each of the nine conditions alone refuses, and that the registry's bytes and the built site are unchanged by the run |
| 30 | validated URLs; no script, HTML or tracking injection; no executable creatives | **BUILT** | https only, host must be declared exactly as a Stay provider is, no `<` in any creative field, `javascript:` and `data:` refused, and a creative cannot carry a file at all today |
| 31 | the organic platform and the commercial layer as separate halves | **BUILT** | the diagram below, and the module boundary that implements it |
| 32 | a fourteen-row launch checklist | **BUILT** | one check asserts all fourteen rows — the nine that must exist and the five that must be false |
| 33 | invisible infrastructure; nothing may look as though ads are waiting | **BUILT, measured** | zero slot markup, zero reserved space, and `tools/voids.js` unmoved. A reader cannot tell this exists, which is the requirement |

## The separation, as built

```
                         EUROPEDOOR
                              │
             ┌────────────────┴────────────────┐
             │                                 │
      ORGANIC PLATFORM                  COMMERCIAL LAYER
      data/countries/                   data/advertising.json
      data/journeys.json                  advertisers
      data/stories.json                   campaigns      (empty)
      data/motions.json                   creatives      (empty)
      tools/lib/pages.py                  placements     (9, all off)
      tools/lib/score.py                  targeting      (6 dimensions)
      assets/js/planner.js                events         (5, none firing)
             │                            billing        (refused)
             │                                 │
             │         tools/lib/ads.py        │
             └──────────── one seam ───────────┘
                              │
                            READER
```

The seam is one function. A page builder asks `ads.for_surface(name)` and
receives a list; today that list is empty for every surface, and it is empty
because five separate conditions are false rather than because one flag is.

## The nine conditions

```
    1. an operating entity exists            serving.entity            null
    2. serving is switched on                serving.enabled           false
    3. the global flag is set                flags.ADVERTISING_ENABLED false
    4. a campaign exists to serve            campaigns                 empty
    5. its placement is enabled              placements[].enabled      false ×9
    6. that placement's own flag is set      flags[placement.flag]     false ×5
    7. the surface it sits on is enabled     surfaces[].enabled        false ×9
    8. the campaign is active                campaign.status           —
    9. it carries a signed insertion order   campaign.insertion_order  —
```

**AND THE FIRST VERSION OF THIS TABLE SAID FIVE.** `ads.py`'s docstring said
five, /for-businesses' lede said "five separate conditions" and listed five,
and `may_serve()` tested **eight** — the two per-placement flags and the
campaign's own status were in the mechanism and in neither sentence. That is a
number typed in three places disagreeing with the thing it describes, which is
the dispatch cap's own failure (four copies, and the one that was a gate was
the one left behind) and `/map`'s (it printed the old projection's name for a
year after the projection changed). `ads.conditions()` is the one declaration
now, `may_serve()` is `all()` over it, /for-businesses prints the list rather
than a count, and `tools/ad-tests.py` reads that list and proves **each entry
alone refuses** — so a condition added tomorrow is proved tomorrow, where a
typed list of five would quietly stop covering the set.

**One flag is never the whole gate.** The sister repository records what that
costs: its `status: 'active'` became inert the day a real compliance ladder
was built, and its own notes say that guarding the wrong word is worse than
guarding nothing. Every condition here is independently false, and the first
one is not ours to flip — `docs/legal-position.md` §3 records that there is no
incorporated entity, so there is nobody for an advertiser to pay and nobody to
be liable for what a placement says.

## The wall, and the fact that it moved

/for-businesses has published this since before the registry existed:

> Paid tiers buy presentation on directory surfaces. They never buy Atlas
> ranking, Journey Planner weighting, or a place in a curated journey. **If
> that wall ever moves, it moves in public, on this page.**

The brief's nine surfaces are every one of them editorial. So the wall moved,
and it moved where the page said it would: the position is now *paid
placement buys a declared slot*, the page states both the new position and
the sentence it replaced, and `checks.py` asserts the page and the registry
agree **in both directions** — because a page can keep a promise the
mechanism has stopped keeping, and a mechanism can be quietly stricter than
the page a reader is reading.

**The substance did not move.** Ranking, weighting, curation, scores, result
order and editorial copy were never for sale and are not now.

## Two refusals that are about sourcing rather than taste

**A creative may not carry an image yet.** Nothing ships on this site without
a photographer, a source, a licence, a date and the SHA-256 of the bytes as
served; `data/images.json` is that register and `checks.py` refuses a
published page referencing a file with no row. An advertiser's artwork has
none of those — it arrives with a brand guideline. The field is declared,
because the shape the brief asks for is the right shape; it is refused in data
until the register can express *granted to us by this advertiser under this
insertion order, on this date*, at which point a creative is an image like any
other and goes through the same gate as a photograph.

**No third-party advertising network, and the cost is named.** This site
serves `default-src 'none'`, `img-src 'self' data:`, and no inline script
anywhere. An external network needs a script origin and an image origin, so
adopting one changes the security posture of every page to serve a revenue
mechanism. That is recorded here so nobody makes the decision by adding a tag.

## Three things only building it found

**A BRAND TOKEN IS NOT A HOSTNAME, AND `readForm` CONTAINS `adform`.** §21's
refusal was declared as twenty-one bare tokens, and the check reading them
required a dot — so nineteen of the twenty-one were never tested and
appending `doubleclick.net` to a script left it green. Removing that filter
then failed `planner.js` on `readForm`, which is `cell` catching `cellar` one
family over. `checks.py`'s commercial-map-host refusal settled this years ago
and says why on its own list: *hostnames rather than a vague substring,
because a page that says "the map" is not a violation and a check that cannot
tell the difference gets switched off.* The registry declares twenty-six
hostnames now, and the guard is proved red on a **script**, where the
outbound-link check has no reach at all.

**TWO OF THE SIX TARGETING DIMENSIONS CANNOT BE SUPPLIED, AND RETURNED NO
MATCH IN SILENCE.** `context_for()` reads a path, so it can answer country,
region, destination and experience category. `travel_interest` is a property
of the destination record rather than of the path, and `language` needs a
second locale reaching `SHIP_THRESHOLD`. A campaign targeting either returned
False from `_targets_match` — correct behaviour, and indistinguishable from a
target that simply did not match this page, which is `opts.geoTooNarrow`
computed and read nowhere. Both stay declared, because the brief's vocabulary
is right; both now raise with their own trigger named, so a campaign written
against one is refused out loud.

**AND THE STATUS BLOCK IS ON THE PAGE, DERIVED.** §1 asks a launch to be able
to state eight lines about the commercial layer. `ads.status()` derives all
eight from the registry and /for-businesses prints them, beside the nine
conditions and the nine placements — so a product that is switched on cannot
be switched on quietly, and a status block nobody can contradict is a status
block that was true on the day somebody typed it.

## Evaluation — what this covers and what it does not

Of the thirty-three sections: **twenty-six are built**, four are **declared
and off with an objection or a trigger attached** (§23 map, §24 search, and
the two halves of §12/§13 admin), one is **partial** (§15, the dashboard
needs accounts and its sentence is published), one is a **measured departure**
(§10's ten components), and **one is stronger than asked** in four separate
places, listed at the top.

Nothing is refused outright. The three surfaces this repository would have
refused on its own — search, map and the planner — are declared and off, with
the measurement that argues against each attached to the flag rather than
used to delete it, because the brief asked for the architecture and the
objection is a thing to answer rather than a veto.

**What is genuinely not covered, and why:**

- **The admin UI and the business dashboard.** Both need authentication and a
  backend. Every account feature in this product is behind that same gate and
  §12 does not change it.
- **Payment.** Explicitly out of scope in the brief and behind the entity
  gate here.
- **A creative image.** Blocked on the licence register, as above.
- **`language` targeting.** Declared and unreachable: `SHIP_THRESHOLD` is 1.0
  and one locale is at 100%, so there is no second language to target.
