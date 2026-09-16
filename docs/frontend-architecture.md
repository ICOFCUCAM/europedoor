# §4 — The frontend, audited before it is designed

Measured on the running build. No new component architecture is proposed here;
this is what the pages are actually made of, so that any future visual
work touches the small number of things that generate them rather than the
pages themselves.

The headline finding, and it reframes the section:

> **This is not an application with a thousand routes. It is a set of documents
> and five applications.** 453 pages load no JavaScript at all; 613 load one
> file, and only to draw a save button. Five pages carry the entire
> client-side product.

---

## 4.1 The route tree

Twenty-two page families and twenty-one one-off pages produce everything.

| family | pages | generated from |
|---|---:|---|
| destination | 319 | `city_page()` |
| place | 255 | `place_page()` |
| destination facet (food, history, things to do, journeys) | 137 | `facet_page()` |
| region | 130 | `region_page()` |
| country | 50 | `country_page()` |
| experience index | 49 | one per kind and category |
| standalone (home, /map, /plan, /search, /my-europe, /method, /fund, …) | 21 | one function each |
| interest · journey · theme · motion | 60 | four families |
| events month · story · macro region | 30 | three families |
| fund · sources · index pages | 21 | |

**Five families generate 83% of the site.** A change to `city_page()` moves
319 pages; a change to `render.section()` moves every one of them. That ratio is the
whole reason the European Future migration was one commit rather than a
project.

## 4.2 The shell — genuinely shared, and measured rather than asserted

| | |
|---|---|
| functions that emit `<!doctype html>` | **1** (`render.page`) |
| mastheads per page | **exactly 1.0**, on every page |
| footers per page | **exactly 1.0** |
| inline `<style>` blocks | **0** |
| stylesheets | **1**, 64 KB |

There is no duplication to find. `checks.py` fails the build on a second page
shell and on any inline `<style>`, which is why: a masthead that exists twice
diverges within a month, and the failure is invisible because both copies keep
working.

For contrast, the sibling repository's measured state — 10 mastheads, 7
footers, 15 stylesheets, 418 distinct font sizes, 45 breakpoints — is what
this discipline is preventing, not a hypothetical.

## 4.3 Data consumption — where the client-side product actually is

| | pages | loads |
|---|---:|---|
| documents with no script at all | **453** | — |
| documents with a save button | **613** | the save-button half of `my-europe.js` |
| **applications** | **5** | `planner.js` · `map.js` · `my-europe.js` · `search.js` · `discover.js` |
| enhancements | 1 | `events.js` — 36 lines |

**The fifth application, named from the repository rather than the brief, is
Search.** In descending size:

| | lines | surface | reads | owns |
|---|---:|---|---|---|
| Planner | 1,721 | `/plan` | `atlas.json` | `saved.v1` |
| Map | 643 | `/map` | `geo/*` | — |
| My Europe | 394 | `/my-europe` | `atlas.json` | all three storage keys |
| **Search** | 385 | `/search` | `search.json` | — |
| Discover Mode | 270 | `/discover` | `atlas.json` | — |

**And a correction to this audit's own first draft.** It named `events.js` as
the fifth application and treated `my-europe.js` as "not one", which is
backwards: `events.js` is 36 lines of checkbox filtering over rows already in
the page, and `my-europe.js` owns every piece of client state in the product.

The boundary is now **behavioural rather than a list of filenames**, because a
list goes stale and a behaviour does not:

    an APPLICATION fetches an index, or owns client state, or both.
      It must declare its dependencies in data/contracts.json.
    an ENHANCEMENT does neither. The page works without it, and it stays
      under a hundred lines.

A script that starts fetching has become an application and has to say what it
depends on — verified by adding a `fetch()` to `events.js` and watching the
build go red.

Every one of the five reads an index declared in `data/contracts.json`, and
`checks.py` refuses a consumer that fetches an index it has not declared —
in both directions. See §4.7.

**A save button is not an application.** The 613 pages that load
`my-europe.js` do so for a DOM contract — any element with
`data-save="<kind>:<id>"` becomes a button — and everything they save is local
to the browser. That is why adding saved experiences was a markup change.

## 4.4 What the 651 browser checks are protecting

253 `ok()` call sites across **27 named sections**, run over 17 distinct pages
at two viewports — 1280×900 and 390×844. They are not a coverage exercise;
each section exists because something went wrong.

| what they protect | sections |
|---|---|
| the planner, as a product | 7 — inputs, why each stop, what-if, editing, honest refusal, the staged wait, the specification's output |
| the map | 4 — layers, real geography, the country map, the map as a list |
| search and discovery | 4 — the sentence box, Discover Mode, Europe in Motion, the knowledge graph |
| saved state | 3 — saving, moving a list between browsers, the travel profile |
| the phone | 3 — no horizontal overflow, the thumb bar and sticky action, the destination page's contents |
| the design system | 2 — the two worlds, WCAG 2.2 AA contrast in both colour schemes |
| the homepage | 1 |

**They earn their place repeatedly.** Findings only reachable in a browser:
a 47px mobile overflow on every city page; two colour tokens below the AA
line; a places layer that could never be turned on because `.hidden` is not a
property of an SVG element; a €700 fortnight routed through Switzerland; a
2,500 km final leg presented as an itinerary; 204px of overflow introduced by
making the map page two columns; and a search modifier that was displayed to
the reader and then not applied.

**The suite has a floor on its own count.** It once printed *"all 4 browser
checks passed"* and exited 0 while 540 ran, because a `const` shadowed the
counter. A green run that has stopped counting is worse than a red one.

## 4.5 Tokens and components — what exists before anything new is proposed

| | |
|---|---|
| custom properties | **56 distinct** |
| type-scale tokens | **11** (`--t-xs` … `--t-6xl`) |
| distinct `font-size` values in the whole stylesheet | **13** |
| breakpoints | **6** — 40, 44, 52, 60, 62, 64 rem |
| distinct box-shadows | **2** |
| class selectors | 236 |
| renderer functions | 23, of which ~11 are components |

### The primitives that generate the site

**THE FIGURES ARE NOT COPIED HERE, AND THE VERSION THAT WAS COPIED HAD ALL
MOVED.** This section used to carry a table of instance counts and
percentages typed into the document — `card` at 23%, `plate` at 78%, `note`
on 1,014 pages — against a register that recomputes the same quantity on
every build. By the time anybody read them `card` was 6%, `plate` was ZERO
because every abstract plate has come off the pages, and the page total the
percentages were of had moved three times. Two measurements of one quantity,
one generated and one typed, is the arrangement this repository has paid for
more than once; the generated one is `primitives.reach` in
`docs/invariants.json`, it carries a FLOOR per primitive so a family cannot
quietly grow its own component set, and CI fails when it is stale.

The snapshot below is from that register rather than from a hand count, and
the shape is what matters rather than the digits:

| primitive | on % of pages |
|---:|---:|
| `kicker` | 100% |
| `masthead` | 100% |
| `crumbs` | 100% |
| `pagehead` | 99% |
| `row` | 89% |
| `note` | 82% |
| `band` | 76% |
| `facts` | 76% |
| `btn` | 64% |
| `chip` | 52% |
| `card` | 6% |

**Two primitives are on literally every page, two more on all but a handful,
and eleven cover the site.** The handful is named rather than rounded away:
the homepage has no `pagehead`, because its head is the hero, and the two
pages with no `crumbs` are the homepage and the 404, which is where a
breadcrumb has nothing to say. Restyling `row` or `band` restyles three
quarters of the site; restyling the four at the top restyles all of it. That is the lever, and it is why §4 should never contain
the phrase "redesign every page".

**And `plate` is no longer on this list at all.** It reached 78% of pages
when this document was written and it reaches none: the abstract plate came
off one family at a time, each with its own measurement, and it is now
exclusively the social-card language. See `docs/gap-assessment.md` §3.4.

## 4.6 The two worlds, classified

Built and shipped. `<body data-world>` selects which set of semantic tokens the
whole stylesheet resolves to, and a browser check asserts each page is in the
world it should be, in **both** colour-scheme preferences.

    DISCOVER — light, editorial          INTELLIGENCE — dark, luminous
      home                                 /map
      countries · regions · destinations    /plan
      places · experiences                  /my-europe   (saved everything)
      stories · events · themes             /search
      the fund, method, sources             /discover    ← see below
      every editorial surface               every embedded map figure

**One classification is a judgement and should be checked with the owner.**
`/discover` is INTELLIGENCE here, on the reasoning that Discover Mode is a
*filter interface* rather than a photography-led browse surface — you tell it
constraints and it narrows the continent. It is not in either list in the
§4 brief. If it should be DISCOVER, it is a one-line change and the browser
check moves with it. `/discover/<macro>`, the editorial macro-region pages,
are DISCOVER either way.

**An embedded map is INTELLIGENCE wherever it sits**, including inside an
editorial country page. That is the door working as a design language rather
than as a glyph: a window into the machine, cut into a page.

## 4.7 The declared-dependency rule

Written into the architecture as a result of §3:

> **No consumer may depend on a field belonging to another index unless the
> dependency is declared in `data/contracts.json` and checked.**

Coupling is not the problem. *Silent* coupling is. The live case:

    search.json
         ├── rows          → results
         ├── interests     → the interpretation line
         └── counts.cities → the EMPTY STATE prints it

That relationship is legitimate and load-bearing — the empty state must print
a live count, not a number typed into a JavaScript file, because it did that
once and said "244 cities" while the atlas held 319. What was wrong was that
nothing declared it: splitting the index into `search.json` + `counts.json`
would have broken a sentence in a UI with no test failing.

The check enforces it **in both directions**, and both were verified by
breaking them:

1. **Declared field missing** — removing `counts` from the index fails with
   *"search.js depends on /api/search.json → counts.cities, which is not
   there"*.
2. **Undeclared fetch** — pointing any script at an index it has not declared
   fails with *"…fetches /api/countries.json and does not declare it"*.

A dependency also has to carry a *reason*; one without a reason is one nobody
can ever decide to remove.

## 4.8 What §4 should NOT do

| not this | because |
|---|---|
| a new component library | eleven primitives already cover 100% of the site and are measured |
| a CSS framework | one 64 KB stylesheet, 13 font sizes, 6 breakpoints, 2 shadows |
| a JS framework | all but five pages are documents; five are applications, and each is one file |
| a build step for the frontend | there is no bundler and no `package.json`; adding one adds a thing that breaks |
| per-page redesign | changing `render.section()` changes every page; changing a page changes one |
| a design-token package | tokens live in one `:root` block, checked against `docs/palette.json` for contrast |
| hydration or client routing | the fastest page is the one that is already HTML |

**The one thing §4 legitimately opens:** the five application pages are the
only place where component structure is not already shared, because each is a
bespoke surface. If a common shape emerges across the planner, the map and
Discover Mode — a results list with an interpretation line above it, say —
that is a real primitive waiting to be named. It has not emerged yet, and
naming it before it does is how design systems acquire components nobody uses.

## 4.9 Method

Unchanged, and now applied to the frontend:

    audit → measure → check → implement → deliberately break → verify → close

Every number in this document came from the build. Where a claim can go stale,
`checks.py` or `browser-checks.js` asserts it; where a check was added, it was
watched going red before being trusted.
