# /themes — the Thematic Atlas

The first page redesigned under `docs/redesign-doctrine.md`, and the page that
caused the doctrine. The owner read the version before this one and named the
fault exactly: *keep the existing page, add premium CSS and components around
it, add a few visual elements, call it a redesign.* Thirteen themes had been a
card grid, then rows, then rows with a photograph — three presentations of one
list, and the list was the layout every time.

## 1 · Inspect (doctrine step 1, and no CSS was written during it)

| | |
|---|---|
| 13 themes | name, strapline, summary, interests, 8 stops |
| 104 stops | each with an authored `why` sentence |
| 13 photographs | one per theme — the register's largest single holding |
| geometry | 8 stops each on the shared projection |
| reach | 3–8 countries, **2–6 of the 9 corners of Europe** |
| relationships | 15 of 78 pairs share a stop; 88 of 319 destinations; 37 of 50 countries; all 9 corners |
| links | 13 theme pages, /plan, /countries, /discover, /europe-in |
| the caveat | the eight places are **not** in travelling order |

## 2 · The finding: the page drew none of the thirteen shapes its own closing sentence described

`head_figure()` prefers a photograph and falls back to the drawing, and its
docstring states the contract in as many words: *the drawing is never lost —
the caller emits it below with `moved_drawing()` when a photograph took its
place.* Three callers use it. The country page honours that. The theme page
honours that. **This index never called `moved_drawing` at all** — so from the
commit where the thirteenth theme photograph landed, every glyph was built and
discarded, while the note under the list went on saying:

> Each shape beside a theme is that theme's own eight places on the continent,
> drawn to the same frame so the thirteen can be compared: a knot is an
> argument about one corner of Europe, a scatter is one about the whole of it.
> Drawn from Natural Earth 1:110m admin 0 countries, public domain.

A promise of a drawing beside each theme, on a page with none, crediting
Natural Earth for land nobody drew — the inverse of *a page that draws land
names where the land came from*. It is the
fourteen-call-sites-forgot-the-motif shape in a helper with a two-call
contract.

**And `c_same_frame` could not see it.** That check skipped any page carrying
fewer than two `.constel` glyphs, so *says and draws nothing* — the strongest
form of the defect it exists for — was the one form outside its reach. It
asserts both directions now, and was proved red by removing the drawings
(*"/themes: says its shapes are drawn to the same frame and draws 0 of them"*)
and green by putting them back.

## 3 · Content architecture (doctrine step 2)

**What the page is about:** Europe can be organised by what you came for, and
each of those organisations is a different geography.

**The single idea:** a theme is a geography without a border — thirteen of
them, each a different argument about the continent.

| content | treatment |
|---|---|
| the thirteen geographies | the monumental visual, **as a sequence of arguments** |
| "a theme is a crossing, not a country" | the typographic statement |
| the 13 photographs | structural — one per argument, the character of the theme |
| reach and near-disjointness | the data instrument |
| the Planner caveat | the quiet editorial section |
| **the thirteen themes** | **must not be a card — and must not be a row either** |

## 4 · The composition

Each theme is one **argument band** carrying its geography, its photograph,
its authored summary, its eight places and its reach — which is a composition,
because that is what a theme record holds.

**The band's scale follows the theme's reach.** A theme crossing a *majority*
of the nine corners of Europe gets the wide band; three or four corners the
feature; and the one theme that is an argument about a single corner gets an
intimate one. Majority of nine is five — a threshold, not a taste:

| scale | corners | themes | composition |
|---|---|---:|---|
| wide | ≥ 5 | 6 | the geography leads, 736 × 574 across the column, caption beside it; then the words with the picture at their side |
| feature | 3–4 | 6 | the picture leads at 745 × 496 against a narrow type column; the geography is a 480px band beneath both |
| tight | 2 | 1 | type-led at 960 wide, the map at 320 beside the words and the picture under it |

The single tight band is Renaissance Europe — precisely the knot the page's
closing sentence is about, so **the layout argues what the sentence says
instead of captioning it**.

The side alternates down the sequence, because a magazine alternates: six
identical wide bands in a column is a listing with a bigger component, which
is the fault one level up.

**No numbers on the thirteen.** A numeral would claim an order the data does
not have — the same caveat this page already publishes about the eight places
— and a second numbering inside a plate sequence is the 753-page
double-numbering fault.

**The map is the constant and the picture is the variable.** Every argument
draws on the same continental frame, because reach is what separates the
thirteen: `region_glyph`'s recorded refusal applies, and framed on its own
extent each becomes a picture of a different place and the thirteen stop being
comparable at all.

## 5 · Measured

| | before | after |
|---|---:|---:|
| bytes | 32,725 | 82,250 |
| `<img>` | 13 | 13 |
| `.constel` drawn | **0** | 27 |
| largest repeated component | **37%** (13 identical rows) | **18%** (4 feature bands) |
| next two components | — | 16%, 15% |
| page height at 1280 | 8,806px | 19,459px |
| overflow at 834 / 390 / 320 | — | 0 / 0 / 0 |

`tools/monotony.js` is the instrument and this is the number it exists for: a
page whose largest repeated component covers 37% of it with nothing else above
15% is a list; one whose three largest are 18 / 16 / 15 is a sequence of
compositions.

## 6 · Four defects only rendering found

| | |
|---|---|
| the wide map was 1,152 × **899** | the frame is 1000×780 and a full column is 899 pixels tall — a wall rather than a leading picture. It cannot be cropped: an SVG with no `preserveAspectRatio` letterboxes inside a wider box instead of filling it, which is the `.card-art` finding from the other side. Capped at 46rem → 736 × 574 |
| the caption overflowed by 84px at 834 and 390 | the plate is capped at 736, so the caption's track is the column minus 736 minus the gap — 18 pixels at 834. The `.arg` phone rule collapses the band and said nothing about this nested grid: *a rule applied to one of its call sites*. The caption sits beside the plate only above 64rem, which is an existing breakpoint |
| "Sacred Europe" and "Viking Europe" broke their names | `--ed-display-2` is 64px at 1280 and the feature's type column is 359px. /journeys recorded the same arithmetic in a 461px column: the proportion is the feature scale doing what it is for, so the name takes the section step |
| 290 pixels of empty page under a picture-led band's own picture | say 507 + map 280 against a photograph of 496. The obvious repair was `object-fit: cover`, **and it was refused**: that crops, `theme-hero` declares one container (`.headshot`, on the theme page) and this index is a second, undeclared surface, so it would be a crop nobody has measured. The map moved out of the spanned column into a band of its own instead |

That last one is worth the space. *A photograph is cropped by every surface it
appears on and the register declares one* is already recorded here as an open
gap; the fix that would have looked best on screen would have widened it.

## 7 · The two audits

**CONTENT PRESERVATION**

- [x] every content item retained — the thirteen names, straplines,
      **summaries (new to the index)**, all 104 place names, all reach figures
- [x] counts retained and derived — 13, 8 per theme, 3–8 countries, 2–6
      corners, 88 / 319, 37 / 50, 9 / 9, 15 / 78
- [x] links retained — thirteen theme pages, /plan, /countries, /discover, and
      /europe-in is new
- [x] destinations retained — all 104 stops named
- [x] relationships retained, and the near-disjointness measurement is new
- [x] functionality retained — the page loads no JavaScript before or after
- [x] data loaders reused — `data["themes"]`, no second taxonomy
- [x] map engine reused — `constellation()`, `constel_defs()`, `project()`
- [x] image and provenance system reused — `picture()`, `head_figure()`, the
      one credit line the licence asks for. **Nothing was acquired.**

**DESIGN TRANSFORMATION**

- [x] a new composition — five plates, thirteen argument bands at three scales
- [x] the card/grid structure was not reskinned; it was replaced
- [x] the opening says what the page is for and shows the thirteen shapes
- [x] the hierarchy was reconsidered: the summary is on the index for the
      first time, the eight places moved out of the metadata slot
- [x] photography is editorial — one photograph per argument, at the scale the
      argument earns
- [x] the geography has a meaningful role: it *is* the reach, and the reach
      decides the band
- [x] different visual rhythms — geography-led, picture-led and type-led
- [x] measured not to read as a listing: 37% → 18%
- [x] a signature moment: the one theme that is an argument about a single
      corner is composed as one

## 8 · What the brief asked for and is refused

| ask | why not |
|---|---|
| the 104 `why` sentences on the index | they are the theme page's substance; thirteen of them here is an index restating thirteen pages |
| each geography framed on its own extent | reach is the axis, and thirteen incomparable pictures is `region_glyph`'s recorded refusal |
| a chip per theme | this page loads no JavaScript, so a filter chip is the control that does nothing — `data-rotate` again |
