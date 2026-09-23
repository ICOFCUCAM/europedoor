# The publishing queue

GENERATED — `python3 tools/seo.py --write`. Do not hand-edit; `checks.py` fails when this document stops equalling what the generator produces, exactly as it does for `site/`.

Every page EuropeDoor serves, in two axes: what the readiness assessment MEASURES about it, and what `data/seo.json` has DECIDED about it. See `docs/seo-architecture.md` for the layer itself.

## The two axes, and why it is not one column

The brief's queue is READY / NEEDS IMPROVEMENT / PUBLISHED. The first two are measurements of a page and the third is a decision about it, so one column cannot hold both: a page can be published and not ready — the state a governed corpus exists to prevent — and ready and deliberately withheld, which the brief itself calls legitimate. **Readiness is derived and may never be authored; state is authored and may never be derived.**

| | READY | IMPROVE | HOLD | all |
|---|---:|---:|---:|---:|
| **published** | 769 | 262 | 0 | 1031 |
| **noindex** | 0 | 0 | 0 | 0 |
| **all** | 769 | 262 | 0 | 1031 |

1031 of 1031 routes are in the sitemap, under the `indexable` gate.

## The four actions, and the mechanism each one already is

Nothing here is a button, because this product has no server, no account and no admin surface — an action is an edit and a commit. Three of the four were already mechanisms in this repository before the brief arrived, so what follows is a map rather than a build.

| action | the mechanism | |
|---|---|---|
| **IMPROVE** | edit data/ and rebuild | the queue names the page and the signal; the fix is editorial |
| **REVIEW** | the pull request | already the approval boundary — the photograph pipeline uses the same one |
| **PUBLISH TO SEARCH** | data/seo.json → status "published" | it changes search ELIGIBILITY; nothing is submitted to anybody |
| **HOLD** | data/seo.json → status "noindex" | the page stays live in EuropeDoor and leaves the sitemap and the index |

## What IMPROVE is waiting on

Every signal that is missing anywhere, with its count. A signal marked advisory cannot HOLD a page — it is a page somebody has not finished writing, not a page that is wrong to expose.

| pages | signal | |
|---:|---|---|
| 214 | content: distinctive editorial content | advisory |
| 46 | technical: description likely shown whole | advisory |
| 1 | technical: title within length | advisory |
| 1 | content: substantial information | advisory |
| 1 | content: useful visitor context | advisory |

## By family

| family | pages | READY | IMPROVE | HOLD |
|---|---:|---:|---:|---:|
| facet/place | 355 | 332 | 23 | 0 |
| destination | 319 | 112 | 207 | 0 |
| region | 130 | 130 | 0 | 0 |
| country | 50 | 37 | 13 | 0 |
| experiences | 46 | 44 | 2 | 0 |
| interests | 18 | 18 | 0 | 0 |
| journeys | 18 | 13 | 5 | 0 |
| themes | 14 | 10 | 4 | 0 |
| europe-in | 13 | 13 | 0 | 0 |
| events | 13 | 13 | 0 | 0 |
| fund | 13 | 9 | 4 | 0 |
| discover | 10 | 10 | 0 | 0 |
| stories | 10 | 8 | 2 | 0 |
| sources | 2 | 2 | 0 | 0 |
| about | 1 | 1 | 0 | 0 |
| accessibility | 1 | 1 | 0 | 0 |
| api-docs | 1 | 1 | 0 | 0 |
| beyond-the-obvious | 1 | 1 | 0 | 0 |
| contact | 1 | 1 | 0 | 0 |
| cookies | 1 | 1 | 0 | 0 |
| countries | 1 | 1 | 0 | 0 |
| for-businesses | 1 | 0 | 1 | 0 |
| for-tourism-boards | 1 | 0 | 1 | 0 |
| help | 1 | 1 | 0 | 0 |
| homepage | 1 | 1 | 0 | 0 |
| how-it-works | 1 | 1 | 0 | 0 |
| manifesto | 1 | 1 | 0 | 0 |
| map | 1 | 1 | 0 | 0 |
| method | 1 | 1 | 0 | 0 |
| my-europe | 1 | 1 | 0 | 0 |
| plan | 1 | 1 | 0 | 0 |
| privacy | 1 | 1 | 0 | 0 |
| search | 1 | 1 | 0 | 0 |
| terms | 1 | 1 | 0 | 0 |

## HOLD

Empty, and measured rather than asserted: no page is missing a blocking signal. The state is exercised anyway — `python3 tools/seo.py --check` builds a held page in memory and reads the verdict back, because *a code path nothing exercises is a code path nothing checks*.

