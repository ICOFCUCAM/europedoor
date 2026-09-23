# The search layer

**What this is.** EuropeDoor's pages were already technically sound — a
canonical, a title and a description on every one of them — and entirely
ungoverned: the sitemap was every URL the build wrote, there was no way to
withhold a page from search, and nothing measured whether a page was worth
finding. This is the layer that makes "is this page ready to be found" a
question with an answer, and "should it be" a decision somebody makes.

**It is a build-time layer and there is no model in it.** Claude helps write
and improve these pages; nothing in the shipped product calls an API, and the
readiness assessment is a Python script reading the built HTML. A runtime
dependency on a model would put a key, a request and a bill on a site whose
whole posture is `default-src 'none'` and no server.

## What is authored and what is derived

`data/seo.json` holds three fields per route and refuses the rest:

| | | |
|---|---|---|
| `status` | AUTHORED | `published` or `noindex` — a classification |
| `reason` | AUTHORED | required wherever the status is not the default |
| `last_reviewed` | AUTHORED | a decision about search is a claim about a moment |
| `indexable` | derived | `status != noindex` |
| `sitemap` | derived | the gate below, applied to `indexable` |
| `canonical` | derived | `render.page()` emits it; the page states it |
| `title` | derived | the page states it |
| `description` | derived | `render.meta_description`, from the record |
| `schema` | derived | the JSON-LD blocks the page carries |
| `readiness` | derived | `tools/seo.py`, measured on the built page |

That split is the Data Integrity Rule applied to a publishing state: **never
author a measurement; you may author a classification.** A canonical written
into a register is a second copy of the one in the `<head>`, which is `/map`
printing the old projection's name for a year; a readiness written into a
register is an authored measurement, which this repository refuses by name.

`tools/lib/seo_state.py` is the one decision point and has four consumers —
the renderer, the build's sitemap, `checks.py` and the readiness engine. Four
readers of one fact is the shape that cost a whole sitting when a dispatch cap
was typed in four places, so the fact is declared once and read.

## Readiness is four groups, never a score

`node`-free: `python3 tools/seo.py`. Every built page is assessed against four
groups of signals, and the report says which signals are missing rather than
producing a number:

| group | asks | |
|---|---|---|
| CONTENT | unique identity, own description | blocking |
| CONTENT | substantial information, distinctive editorial content, useful visitor context | advisory |
| TECHNICAL | canonical, structured data, weight under the ceiling | blocking |
| TECHNICAL | title within length, description likely shown whole | advisory |
| DISCOVERY | linked from somewhere, linked from its parent | blocking |
| MEDIA | every image is named, a picture or a drawing | blocking |

**A single figure is refused deliberately.** "Copenhagen = 94/100" claims to
know how a search engine will weigh these against each other, which nobody
here does — and a number is satisfied by moving whichever signal is cheapest,
where a list of missing signals names the work. The verdict is one of three:
READY (nothing missing), IMPROVE (only advisory signals missing, which is a
writing task), HOLD (a blocking signal missing, which needs a decision).

**Severity is declared beside the signal, and the test is which of the four
actions it calls for.** A signal a writer fixes by writing is advisory; a
signal that needs somebody to DECIDE something — which of two pages answers a
query, whether a page nothing links to should exist — is blocking. The first
version sorted by GROUP instead, so 46 of the 47 pages it held back were held
on a description of 166 to 296 characters — every one ending on a full stop,
and 32 of them inside the tag's own cap: whole sentences, read perfectly by a
crawler. Worse, it held them on the one
signal this file states is a guess about a search engine's behaviour, which is
"Copenhagen = 94/100" arriving through a named signal.

**`indexable` is not one of these signals**, and it used to be. `noindex` is
not a defect a page has, it is a decision this atlas has recorded about it, so
reading it here graded the site's own choice as a fault — a page deliberately
withheld would have been reported as not ready for the search it is being kept
out of on purpose. See the queue below.

**The thresholds are this file's own claims and are not read off the
product.** `SERP_VISIBLE` is a reading of how much of a description a result
prints; `render.META_DESC_MAX` bounds the tag. Binding the first to the second
would make the measurement agree with the product by construction, which is
the instrument fault this repository records seven times. The floor is the
same question in both places and *is* read rather than retyped.

## The sitemap is a decision, not a listing

`data/seo.json` carries the gate with its reason, and it has two settings:

- **`indexable`** — every page a reader can reach. What shipped before this
  layer existed, and what ships today.
- **`ready`** — additionally requires the readiness engine to assess the page
  READY. This is the brief's own reading: the sitemap should say which pages
  we consider ready for search discovery.

It is `indexable` today because the readiness report's own gap is structured
data and internal linking — those are fixes rather than withdrawals, and the
order is to improve the pages before deciding what to expose. Moving it is a
one-word edit to a registry and is the owner's.

**A sitemap is a recommendation and not a permission**, which is why the gate
and the robots meta are separate mechanisms: removing a URL from the file does
not deindex the page, and only `noindex` does.

## NOINDEX exists, is empty, and carries its trigger

No route declares it. Every built page was measured for the three things that
earn one and none has any: no page's canonical points anywhere but itself,
exactly one page is under the readiness word floor, and the lowest share of a
page's own sentences is a destination sharing its region's grammar rather than
a duplicate. The site serves no parameterised result page, no printer view and
no tag archive — the three shapes that normally fill that list.

A vocabulary entry nothing reaches is dead code that looks like vocabulary, so
the mechanism is **exercised on every run** by `c_seo_noindex_path`, which
swaps the register in memory the way `ad-tests.py` simulates a serving
campaign: nothing is written, so there is nothing to restore. The trigger for a
real entry is a route whose canonical names another page, a result page built
from a query string, or a page whose content is a visitor's own storage.

And the tag is emitted **only where it changes something**. `index,follow` on
every document states the default a browser already has with no tag at all, so
it cannot be read as a decision — the same reasoning that makes an off
advertising slot emit zero bytes.

## The queue is two axes, and one of them may not be measured

`python3 tools/seo.py --queue` prints the back office;
`--write` regenerates **`docs/seo-queue.md`**, which is committed and
stale-checked exactly like `site/`.

The brief's queue is READY / NEEDS IMPROVEMENT / PUBLISHED. The first two are
measurements of a page and the third is a decision about it, so one column
cannot hold both — and the two cells worth looking at are the disagreements:

| | READY | IMPROVE | HOLD |
|---|---|---|---|
| **published** | in search, and should be | in search while somebody finishes writing it | **the cell a governed corpus exists to prevent** |
| **noindex** | deliberately withheld — legitimate, and the brief says so | withheld and unfinished | correctly withheld |

That is the Data Integrity Rule written as a queue: **readiness is a
measurement and may never be authored; state is a classification and may never
be derived.** `--check` proves the two are separate by moving the one that
must not matter — it withholds a page from search in memory, in both halves a
real declaration produces (the register row AND the robots tag), and asserts
the readiness did not move.

## The four actions are already mechanisms here

The brief asks for IMPROVE / REVIEW / PUBLISH TO SEARCH / HOLD as back-office
actions, and it is right that those are the four things anybody does to a
page. What it cannot know is that this product has no server, no account and
no admin surface — so an action is an edit and a commit, and three of the four
existed before the brief arrived. Building buttons for them would be building
twice.

| action | the mechanism | |
|---|---|---|
| IMPROVE | edit `data/` and rebuild | the queue names the page and the signal |
| REVIEW | the pull request | already the approval boundary the photograph pipeline uses |
| PUBLISH TO SEARCH | `data/seo.json` → `status: published` | changes search ELIGIBILITY; nothing is submitted to anybody |
| HOLD | `data/seo.json` → `status: noindex` | the page stays live in EuropeDoor and leaves the sitemap and the index |

**The publishing queue is a document rather than a screen**, on
`docs/content-report.md`'s own reasoning, which it states in its first
paragraph: *"An admin dashboard needs authentication, a backend and somebody
logged in. This build has none of those, so the same figures are computed at
build time and committed — which has one advantage a dashboard does not: the
gaps show up in a diff."* The hosted Media Desk is the measure of what the
other answer costs: a second Vercel project, a passcode, signed sessions and a
suite of its own, deliberately off europedoor.com.

## What the checks hold

- the register authors a classification and nothing derived, every non-default
  status carries a reason and a date, and every route it names is built;
- the sitemap, the robots meta and the register say one thing, in both
  directions — a page in the sitemap is not noindex, and a noindex page is not
  in the sitemap;
- every URL the sitemap names is a page this build serves;
- the noindex path and both sitemap gates work, on a register no page uses;
- no page the sitemap recommends is one the measurement HOLDS, which is the
  brief's own sentence about the sitemap as a gate;
- the readiness of a page does not move when its state does, and an advisory
  signal alone never holds a page back from search.

Run `python3 tools/checks.py` for the totals. Each was proved by failing on
the thing it is about rather than by passing.

## What is not built

**Search Console is the feedback loop and needs a credential.** Impressions,
average position and the queries a page actually wins are facts only Google
holds, and reading them needs an OAuth client and a property somebody has
verified. Nothing here can do that from a sandbox that cannot open a socket to
google.com. The trigger is the owner connecting a property; the shape it would
take is `tools/deployed.py`'s — a workflow with network access, writing a
committed report, so the repository holds the evidence rather than a dashboard
nobody can check.

**Submitting URLs is refused and is not the same as publishing.** "Publish to
search" changes a page's eligibility — `indexable`, the sitemap, the canonical
— and does not tell Google anything. A crawler finds the sitemap from
`robots.txt`.
