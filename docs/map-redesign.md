# /map — the instrument

Redesigned under `docs/redesign-doctrine.md`. Its fault was the opposite of
every other page's: `tools/monotony.js` does not list /map at all, because no
repeated component covers it. **Everything that made it an instrument was
behind a closed disclosure.**

## 1 · Inspect (doctrine step 1)

451,895 bytes — the largest page on the site. `pagehead instrument`; the h1
was already the brief's headline. The lede was four words: *"Click a country
to go into it."*

| behind `<details class="maptools">`, CLOSED | |
|---|---|
| the legend | four swatches |
| how to read the drawing | drag, scroll, zoom, what 1.6× loads |
| four geography layers | borders, regions, destinations, places — the count is derived, see [`docs/content-report.md`](content-report.md) |
| **all seventeen interest filters** | the instrument's main control |
| the journey overlay | 17 routes |
| the distance origin | 313 destinations |
| the live count | *"319 destinations across 50 countries"* |

| behind `<details class="maplist">`, CLOSED | |
|---|---|
| **the most complete index on this site** | 50 countries and all 319 destinations with coordinates, grouped by macro region — and the map's own `aria-describedby` target, and the control WCAG 2.5.8 requires for the twenty countries that draw between 3.6 and 12 pixels wide |

And a `.note` at the foot of the page, at caption size, holding the
cartographic position of the whole product — the one place on the site allowed
to name the projection.

**One `<h2>` on the entire page.**

map.js binds to eighteen ids plus `.mapstage`, `.mappopup-close`,
`#dots .dot` and `.cshape/.cpoint`. Every one had to survive, and every one
did: `id=` present for all twenty-two, verified on the built page.

## 2 · Content architecture (doctrine step 2)

**What the page is about:** this is the instrument — every country, every
destination and every place we hold, on one drawing you can interrogate.

**The single idea:** one map, and every way into the Atlas runs through it.

| content | treatment |
|---|---|
| the map | the monumental visual, which it already was |
| the layers and filters | the data instrument — **visible, below the drawing they act on** |
| the twin | a band: the most complete index there is |
| "a cartographic source, not a legal one" | the typographic statement |
| the provenance and the projection | the quiet editorial section |
| photography | **none** — this is the instrument, not a picture of somewhere |
| the aperture | **deliberately absent**, per `docs/signature-moments.md` |

## 3 · The composition

Five plates: the instrument, what you can ask it, everything we hold in
words, what this drawing is and is not, go in anywhere.

**The controls are below the drawing and not above it**, and that constraint
is inherited rather than guessed: the browser suite's own comment records why
the `<details>` existed — *"the first layout put thirteen interest filters and
two selects between the headline and the drawing and a 1280×1000 laptop opened
the page called 'the map' with no map on it."* Measured after: the drawing
starts at y=526 at 1280 and the controls at y=1528, and the browser suite now
asserts that ordering instead of opening a disclosure.

**Three sets rather than one control panel**, because they are three
questions: what is *drawn*, what each destination is *for*, and what is laid
over the top. Twenty-three controls in one grid is the chip wall the brief
refuses.

## 4 · The defect the disclosure had been hiding

`.legend .sw.dest` is `var(--sea)`. The map's dots are `var(--sea)` too — the
same token, and **two different colours**, because a `var()` resolves where
the declaration lives: inside the graphite map figure `--sea` is cobalt-air,
and inside a light band it is pine-deep.

| | the drawing paints | the key showed |
|---|---|---|
| a destination | `rgb(64,118,231)` | **`rgb(7,48,43)`** |
| a country in the Atlas | `rgb(243,240,230)` | `rgb(243,240,230)` |
| land outside the Atlas | `rgb(108,115,110)` | `rgb(108,115,110)` |

**A key that names the wrong colour is worse than no key** — it is the /map
projection prose one element over — and nothing counts a swatch, so it was
invisible for as long as the key sat inside a closed `<details>`.

The fix is not a hard-coded hex. **The key sits in the same band as its
drawing**, where every token it reads resolves exactly as the drawing's does,
which is also where a key belongs. The browser suite reads the computed paint
off both ends, because the declaration is the same string in both places and
comparing declarations would agree with itself.

## 4b · And two faults the recomposition itself produced

| | |
|---|---|
| **a duplicate `id`** | plate 02's anchor was `layers`, which is also the interest filter container's id and one of `map.js`'s hooks. The browser suite did not report a failure — it **died** on a strict locator resolving to two elements. `c_unique_ids` now fails on it directly, and found `ihedge`/`ihfoot` twice on /stories in its first run: two `cut_fade()` callers pass the prefix `"ih"`, so the second `url(#ihedge)` resolved to the first drawing's gradient. Identical there by luck, because both take their coordinates from the projection; the id carries a counter now |
| **`&deg;` is not `°`** | rewriting the projection paragraph with the HTML entity failed all four angles at once, on the one page allowed to state them: `c_published_projection` reads the shipped HTML for "35°" inside the sentence that names the conic |

## 5 · Measured

| | before | after |
|---|---:|---:|
| bytes | 451,895 | 454,708 |
| `<h2>` | 1 | 4 |
| controls reachable without opening a disclosure | 0 of 23 | 23 of 23 |
| the twin reachable the same way | no | yes |
| map.js hooks intact | 22 | **22** |
| drawing top at 1280 | 526px | 526px |
| document overflow at 1280 / 834 / 390 / 320 | — | 0 / 0 / 0 |
| page height at 1280 | 2,665px | 22,325px |
| largest repeated component | not listed | not listed |

`weight.max_page_kb` 441 → 444, recorded: the three kilobytes are a
`<details>`'s markup becoming two plates with heads on them. The drawing did
not change by a byte.

**The page is now 22,325px at 1280 and 34,149px at 390,** and almost all of
the growth is the twin becoming visible. That is the intended trade: 319
destinations with coordinates is a long list because it is a complete one, and
the alternative is the disclosure this commit removed.

## 6 · Refused

| ask | why not |
|---|---|
| a monumental opening | all five INTELLIGENCE pages carry `pagehead instrument` and the register asserts one role per head. *An instrument's title is a label, because the page is the tool* — measured from heads that pushed the instrument to y=436 on /plan, 449 on /map and 460 on /search |
| "pale mineral Europe on deep pine/graphite" | that is what the instrument map already draws, after the *Europe is what the light falls on* fix |
| a photograph anywhere on it | this is the instrument and not a picture of somewhere |
| the aperture | `docs/signature-moments.md` records /map as correctly without it |
| touching `dusk_reach()` | /map draws its marks ABOVE the fade so a destination near the 52°E cut keeps its dot, and narrowing the fade made that diagonal a hard edge on the instrument |

## 7 · The two audits

**CONTENT PRESERVATION**

- [x] every content item retained — the legend, the reading instructions, all
      four geography layers, all 17 interest filters, the journey overlay, the
      distance origin, the live count, the twin, the provenance, the
      projection
- [x] counts retained and derived — 50, 319, 255 places
- [x] links retained — 50 countries and 319 destinations in the twin, /method,
      and /discover and /countries are new
- [x] relationships retained — the twin's macro grouping
- [x] **functionality retained — all 22 map.js hooks, asserted on the built
      page; the stage still gains `.withpanel` only while something is open**
- [x] data loaders reused — the five inert JSON blocks are unchanged
- [x] map engine reused — same projection, same geometry, same `cut_fade`
- [x] image and provenance system reused — no photograph is asked for

**DESIGN TRANSFORMATION**

- [x] a new composition — five plates where there was one flow
- [x] no card/grid structure existed to reskin; the fault was concealment
- [x] the opening says what the page is for in a sentence rather than four
      words
- [x] the hierarchy was reconsidered: the twin and the cartographic position
      are bands, not disclosures
- [x] photography has no role here, stated as a refusal rather than a gap
- [x] the map is the instrument and its controls are visible
- [x] different rhythms — graphite instrument, paper control panel, gallery
      index, pine statement, close
- [x] does not read as a CMS listing (it never did; monotony does not list it)
- [x] signature moment: the drawing, and the key that now tells the truth
      about it
