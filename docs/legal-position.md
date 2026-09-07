# Legal position

Not legal advice. This is the record of what has been decided, what is
enforced in code, and what is waiting on a lawyer.

## 1. Originality

Europedoor was built after looking at an existing continental travel platform
and taking the *idea*: a continent organised as an atlas, with curated
journeys and a community fund attached.

**The idea is not owned by anybody.** Tourism boards, atlases and travel
magazines have organised continents this way for a century, and business
models are not protected by copyright.

**Expression is owned**, and none of it was taken:

| element | position |
|---|---|
| Text | Every line written for Europedoor. No source text consulted while writing. |
| Data | The taxonomy, the 50 countries, the regions, cities, experiences, journeys, themes and stories were authored here. |
| Code | Written from scratch. No shared lineage of any kind. |
| Design | Original type scale, palette, components and layout. |
| Images | There are none. Every illustration is generated from a hash of the place's own slug. |
| Brand | Europedoor, the door glyph, "One door into Europe" — all original. |

`/about` states this position publicly, which is the right place for it: a
claim of originality made only in an internal file is worth less than one
made in front of readers.

**Still to do:** if a competitor's terms of service were ever accepted by
anybody working on this, those terms may add contractual obligations beyond
copyright. Nobody should create an account on a competitor's site while
working on this project.

## 2. Trademark — open

Not done, and needed before any brand spend:

* clearance search for "Europedoor" in **Nice class 39** (travel
  arrangement), **41** (publishing, entertainment) and **42** (software);
* EUIPO register search for confusable marks;
* national searches in the launch markets;
* domain and social handle consolidation.

Owning europedoor.com is not owning the mark. The name is settled as a
product decision ([`brand-lock.md`](brand-lock.md)); whether it is
registrable is a separate question with a different answer.

## 3. Entity — open, and blocking

There is no incorporated company. Consequences, all currently enforced:

* every page footer carries `[OPERATOR ENTITY — NOT YET INCORPORATED]`;
* `checks.py` fails if any page names a company form (Ltd, GmbH, S.A., LLC,
  AS, Oy, AB);
* no payment can be taken, so no payment surface exists;
* the Fund holds nothing (see [`europe-fund.md`](europe-fund.md)).

## 4. Data protection — open, and the reason accounts do not exist

No personal data is collected. `/my-europe` stores saved places in the
visitor's own browser and the page says so plainly, including the
consequence: a new browser shows an empty list, and there is no copy
anywhere else.

Before accounts:

* a named data controller (needs the entity);
* a lawful basis for each processing purpose;
* a published privacy notice and a retention schedule;
* a data processing agreement with every processor;
* the mechanics of access, erasure and portability, built rather than
  promised.

The analytics design in `product-specification.md` §2.7 anticipates this: a
daily-rotating session id, no cross-site identifiers, no third-party
analytics.

## 5. Consumer law — open, and the largest lift

Two distinct problems, in increasing order of seriousness:

**Listings and commission.** Selling an experience on an operator's behalf
makes us an intermediary with disclosure duties, cancellation terms and
liability questions.

**Packages.** Combining transport with accommodation and selling it as one
thing is a **regulated package** under the EU Package Travel Directive, with
insolvency protection obligations attached. Revenue stream 6 ("curated
journeys sold as packages") is exactly this, which is why it is sixth of
seven and why it needs advice before code.

## 6. Editorial and factual risk

The dataset is a considered first draft, written editorially and not yet
verified source by source. `/sources` says this without hedging, tells
readers to check official government advice before travelling, and separates
what is *claimed* from what is *computed* (distances, scores, cost
estimates).

Three practices reduce the exposure:

* countries under a travel advisory keep a page carrying the warning and are
  removed from the planner index at build time;
* nothing is described as safe, and no entry, visa or security question is
  answered — those point to the government source;
* cost figures are labelled estimates from published bands, never prices.

## 7. Third-party content

There is none, deliberately: no photographs, no map tiles, no scraped
listings, no embedded third-party scripts, no fonts loaded from a CDN. Every
byte served is either written here or generated here.

This will change — commissioned photography, an events feed, a basemap — and
each addition needs its own licence position recorded here before it ships.
