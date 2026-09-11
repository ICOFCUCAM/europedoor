"""The EuropeDoor editorial map renderer.

A MAP IS AN EDITORIAL ILLUSTRATION UNLESS IT IS EXPLICITLY DESIGNATED AN
INSTRUMENT. That is the default here — `role="illustration"` — and it is the
default because the failure runs one way: a picture that drifts into
instrument styling is a page that has quietly become a dashboard, and nobody
notices until somebody looks at twelve families side by side. An instrument
has to say so, in the markup, and `checks.py` reads it off the shipped HTML.

    illustration   country, destination, place, region, journey, story,
                   motion, macro — looked at. Warm paper, Atlantic water,
                   ink coastlines.
    instrument     /map, /plan, /search, /discover and the country reference
                   map — operated. Graphite, layers, a scale bar, links.


    GEOGRAPHIC DATA ─┐                    ┌─ VISUAL STYLE
      coast          │                    │   palette
      borders        ├──▶ THIS MODULE ◀───┤   relief
      rivers         │                    │   typography
                     │                    │
                     ▼
              terrain · water · labels
                     ▼
                aperture / arch

WHY THIS EXISTS AT ALL, AND WHY IT IS NOT A TIDY-UP.

Every plate on this site used to be composed inline: a function fetched its
own geometry, decided its own paint order, wrote its own `<g>` elements and
hard-coded which of them came first. Five families did that five times. The
cost is not duplication — it is that **there was no place to add a layer**.
Terrain has to sit above the land fill and below the coastline; rivers above
terrain and below the coast; a route above everything except labels. With
five inline compositions there are five opinions about that, and the first
one to be wrong is invisible, because a river drawn over a coastline still
looks like a river.

So the model is replaced rather than polished. Geography comes in as data
and knows nothing about colour. Style comes in as a declaration and knows
nothing about geography. This module is the only thing that holds both, and
the ONLY thing that decides what is drawn on top of what.

THE STYLE IS A CONTRACT, NOT A STYLESHEET. Nothing here emits a colour: a
`style="..."` attribute anywhere would force `style-src` open on all 1,033
pages, which is the reason there is not one in this repository. What the
style declares is the CLASS each layer paints through, and `checks.py`
asserts the stylesheet actually carries a rule for every one of them — so a
layer cannot be added here and silently render as nothing, which is the
failure this codebase has made three times with specificity alone.
"""

from __future__ import annotations

import math
import os
import re

from . import geo
from .render import arch_clip, arch_edge, arch_rim


# ── GEOGRAPHIC DATA ───────────────────────────────────────────────────
#
# Which dataset feeds each layer. `None` means the layer is drawn from data
# the build already holds (the atlas's own destinations, a journey's legs);
# a filename means a file in data/geo/, and its absence is the layer's
# absence. Nothing here describes how anything looks.
SOURCES = {
    "ocean":          None,
    "coastal-water":  "derived",      # from the coastline, by stroking it
    "land":           "countries",
    "terrain":        "terrain-lod1.json",
    "hillshade":      "hillshade-lod1.json",
    "rivers":         "hydrology-lod1.json",
    "coastline":      "countries",
    "country-bounds": "countries",
    "region-bounds":  "regions-lod1.json",
    "summits":        "summits-lod1.json",
    "cities":         None,
    "destinations":   None,
    "feature-labels": "features-lod1.json",
    "water-labels":   "marine-lod1.json",
    "labels":         None,
    "route":          None,
    "selected":       "countries",
}

# THE PAINT ORDER, DECIDED IN ONE PLACE. This is the whole reason the module
# exists; every other file may add content to a layer and none of them may
# reorder it.
ORDER = ("ocean", "coastal-water", "land", "terrain", "hillshade", "rivers",
         "coastline", "country-bounds", "region-bounds", "cities",
         "summits", "destinations", "feature-labels", "water-labels", "labels",
         "route", "selected")


# ── VISUAL STYLE ──────────────────────────────────────────────────────
#
# The class each layer paints through, and the rules that are decided but
# not yet drawable. `checks.py` reads both: every class here must have a rule
# in the stylesheet, and every layer whose source is absent must appear in
# DECIDED with a stated appearance, so a missing layer is a gap somebody
# wrote down rather than one nobody noticed.
CLASSES = {name: f"lyr-{name}" for name in ORDER}

# THE HYPSOMETRIC SCALE, AS DATA RATHER THAN AS PROSE. Declared now so the
# day a DEM lands the tint is a table lookup and not an argument. Five steps,
# because four cannot show a foothill and six start to read as a legend a
# reader has to consult. Warm as it rises, and never saturated: in an
# editorial atlas height is FELT, and the typography stays dominant.
#
# The colours are of this palette's own family — the land tone at the bottom
# and the warm accent at the top — so a terrain plate is recognisably the
# same atlas as a flat one, which a stock hypsometric ramp would not be.
# THE RAMP SWUNG 27 DEGREES OF HUE AND PEAKED IN SATURATION AT ITS MIDDLE.
# Measured on the values this tuple used to hold:
#
#     band        hue  sat  light
#     0-200        64   22   85     <- yellow-GREEN
#     200-600      54   27   80
#     600-1200     44   35   75     <- the loudest thing on the plate
#     1200-2000    38   33   71
#     2000+        37   24   87
#
# Three sentences above this one say "the land tone at the bottom" and "warm
# as it rises, and never saturated". The bottom was 22 degrees off the land it
# sat on and green rather than warm; the middle was the most saturated colour
# in the drawing, on a plate whose typography is meant to dominate. A reader
# saw a green lowland, a yellow foothill and a tan upland — three materials,
# where the thing being drawn is ONE ground at three heights.
#
# One warm family now, drifting 42 -> 35 degrees as it rises, which is the
# printed-atlas convention and is what the paragraph above already claimed.
# Saturation rises gently to 20 and drops for stone; LIGHTNESS carries the
# height, evenly — mixed 65% toward the land as the plates draw them, the
# steps measure 1.06, 1.08, 1.09 and 1.36, against 1.02, 1.08, 1.09 and 1.26
# before. Cleaner AND better separated, which is the argument: the hue swing
# was buying nothing.
HYPSOMETRIC = (
    (0,    200,  "#dedbd3", "lowland, the land's own tone"),
    (200,  600,  "#d4cfc4", "foothill, a half-step of warmth"),
    (600,  1200, "#cbc2b4", "upland, warm paper"),
    (1200, 2000, "#c2b5a3", "high ground, pale earth"),
    (2000, None, "#e8e6e3", "mountain, light stone"),
)

# THE CHAIN THE TERRAIN LAYERS RUN IN, which is the owner's and is the order
# a printed atlas is built in: the ground first, the light on it second, the
# country cut out of both third, and everything a reader reads on top.
#
#   DEM → hypsometric tint → hillshade → texture → country mask →
#   administrative boundaries → hydrography → labels
#
# Only the DEM is missing. Everything after it is a transform of the DEM and
# is written down above and below.
TERRAIN_CHAIN = ("dem", "hypsometric", "hillshade", "terrain-texture",
                 "country-mask", "country-bounds", "rivers", "labels")

# A LAYER MAY PAINT THROUGH A RULE IT SHARES WITH THE REST OF THE SITE.
# A route line looks the same on a plate as it does on /map — cobalt, dashed,
# 90% — so an atlas-scoped rule restating it is dead code, and the dead-rule
# scan proved exactly that when one was written. The layer is real, its group
# is real, and this records where its paint comes from instead of demanding a
# redundant rule with its own class.
PAINTED_BY = {"route": ".routeline"}

DECIDED = {
    "feature-labels": "Named ranges and basins — ALPS, PYRENEES, MASSIF "
                      "CENTRAL — in an italic serif, the way a printed atlas "
                      "has always set a physical feature apart from a "
                      "political one. THIS IS THE LAYER THAT LETS A READER "
                      "SEE WHERE THE ALPS ARE BEFORE ANY DEM EXISTS, which "
                      "is why it is worth fetching first.",
    "water-labels": "Sea and ocean names in widely tracked uppercase, in the "
                    "water colour rather than in ink. An area, not a point, "
                    "which is why it is tracked and why it carries no mark.",
    "hillshade": "One light from the north-west, at most 12% opacity, "
                 "multiplied over the terrain tint and clipped to land. "
                 "Never over flat ground, where it invents structure.",
    "rivers": "In the water colour, by stream order, and always thinner than "
              "the coastline. A river drawn as heavily as a coast turns a "
              "country into a leaf.",
    "region-bounds": "Dashed, lighter than a country frontier, labelled in "
                     "the same small caps as a sea. REFUSED rather than "
                     "missing: Eurostat NUTS is the only pan-European source "
                     "and its provisions have not been read.",
}


# LAYERS THAT ARE HELD BUT NOT YET THEIR OWN GROUP, and what carries them.
#
# A country is one filled path with a stroke, so its coastline, its frontiers
# and the emphasis on the subject are all that single stroke. Splitting them
# needs a stroke-only second pass over the same geometry, which re-emits about
# forty per cent of the bytes on these pages — and it BECOMES NECESSARY the
# day terrain arrives, because relief has to sit under a coastline and over a
# land fill, and it cannot if the two are one path.
#
# Recorded rather than left implicit: a layer in ORDER that quietly never
# appears is indistinguishable from one somebody forgot.
FOLDED = {
    "feature-labels": ("labels", "the NAMES are their own typographic level "
                                 "and keep their own class, but they are "
                                 "PLACED by the same rule as every other "
                                 "name — tested against the real curve of "
                                 "the aperture, in priority order, dropping "
                                 "what does not fit. Two placement rules "
                                 "would disagree within a month, and the "
                                 "first version proved it: features drawn "
                                 "outside that rule landed KJOLEN MOUNTAINS "
                                 "over France"),
    "water-labels": ("labels", "same rule, same reason"),
    "coastal-water": ("land", "three soft shadows of the land silhouette, "
                              "cast into the water. THE FIRST VERSION WAS "
                              "THREE `<use>` OF THE LAND GROUP AND PAINTED "
                              "NOTHING AT ALL: the shadow tree a `<use>` "
                              "clones is still matched by the selectors that "
                              "style the ORIGINAL paths, so every clone kept "
                              "the land's own paper fill and 0.9px coast "
                              "stroke and the stroke set on the `<use>` never "
                              "reached it. It looked like a decision, it "
                              "measured correctly on the `<use>` element "
                              "itself, and the ramp was never on the page. "
                              "A filter needs no second copy of Europe and "
                              "cannot lose a cascade fight"),
    "coastline": ("land", "the land path's own stroke. COUNTRY-BOUNDS USED TO "
                          "BE FOLDED HERE TOO and was unfolded the day terrain "
                          "landed, exactly as this note predicted: relief "
                          "paints over a stroke, so a boundary under it is a "
                          "boundary that is not there. The coastline stays "
                          "folded because it is where land meets water and "
                          "nothing is drawn between them"),
    "selected": ("land", "the `here` class on the land path, which sets its "
                         "own fill and a heavier stroke"),
    "cities": ("destinations", "the capital is a destination with a `cap` "
                               "class; no separate city source is held"),
}


def held(name):
    """Can this layer be drawn from what the repository holds today?"""
    src = SOURCES[name]
    if src in (None, "derived", "countries"):
        return True
    return os.path.exists(os.path.join(geo.GEO, src))


def waiting():
    return [(n, SOURCES[n]) for n in ORDER if not held(n)]


# ── THE RENDERER ──────────────────────────────────────────────────────

def _group(name, body):
    """One layer, as its own group.

    A layer with no content emits NOTHING — not an empty group. An empty
    `<g class="lyr-terrain">` on 1,033 pages is a claim that the map has
    terrain and simply had none here, which is the present-but-empty pattern
    this repository refuses in its JSON-LD for exactly the same reason.
    """
    if not body:
        return ""
    return f'<g class="lyr {CLASSES[name]}">{body}</g>'


def unwritten(name, path):
    """A layer whose data has arrived and whose renderer has not been written.

    Raising is the point. A layer that quietly draws nothing once its dataset
    lands is worse than one that was never declared, because the file is in
    the repository, the register says it is there, and the map is silently
    the same map.
    """
    raise NotImplementedError(
        f"data/geo/{path} has appeared and the {name} layer of "
        f"tools/lib/cartography.py has not been written. Its appearance is "
        f"already decided: {DECIDED.get(name, '(undecided)')}")


# THE BAND BOUNDARIES ARE CACHED WITH THEIR BOUNDING BOXES, once per build.
# 2,265 rings and 58,000 vertices are read for every plate that draws relief,
# and a min/max scan of every ring on every page is 46 million coordinate
# reads across the site. The box is computed once and the rejection is four
# comparisons.
_BANDS = None


def _bands():
    global _BANDS
    if _BANDS is None:
        doc = geo.load(SOURCES["terrain"])
        _BANDS = []
        if doc:
            for band in doc.get("bands", []):
                rows = []
                for r in band["rings"]:
                    lons, lats = r[0::2], r[1::2]
                    rows.append((min(lons), min(lats), max(lons), max(lats), r))
                _BANDS.append((band["min_m"], rows))
    return _BANDS


def datacut(uid, proj, view):
    """The drawing fades where what this atlas HOLDS ends.

    `data/geo/` stops at 52°E and 33°N because that is where this product
    stops writing about places. Under this conic the eastern cut runs from
    x=747 at 70°N to x=1024 at 40°N — a clean straight diagonal through
    Russia that a reader can only read as a rendering fault, and the southern
    one is a circle about the cone apex crossing North Africa. The hero has
    faded along both since the hero was drawn, and /map since the land was
    lifted out of its water; every PICTURE plate framed on the continent
    still showed them raw — /beyond-the-obvious, the thirteen themes, the
    twelve motions, the nine stories, the seventeen interests.

    Emitted BETWEEN the ground and the marks rather than over everything: at
    49.8°E the eastern ramp is about a third opaque, and Baku is at 49.8°E.
    A fade that dims the thing it exists to keep legible has swapped one
    rendering fault for another.

    NOT A `lyr-` LAYER, and `geo.LAYERS` is right to have no row for it.
    Every layer there is a fact about the ground; this is a fact about the
    DATASET, and it belongs with the aperture's cut edge — the other thing
    this renderer draws about its own frame rather than about Europe.

    Both gradients come from the projection's own constants, so a projection
    change moves them. A meridian is straight under a conic and a parallel is
    a circle about the apex, which is why one is linear and the other radial:
    the 33rd rises 116 units between Tunisia and the Caspian, and a
    horizontal fade placed on the Tunisian end leaves the cut showing right
    across Anatolia.
    """
    x0, y0, vw, vh = view
    a, b = proj.xy(70.0, 52.0), proj.xy(40.0, 52.0)
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    nx, ny = dy / n, -dx / n                    # perpendicular, pointing east
    ex1, ey1 = mx - nx * 330.0, my - ny * 330.0
    ex2, ey2 = mx - nx * 30.0, my - ny * 30.0
    ax, ay = proj.apex()
    r33 = proj.parallel_radius(33.0)
    f0, f1 = (r33 - 130.0) / r33, (r33 - 4.0) / r33

    def stops(lo=0.0, hi=1.0):
        out = []
        for i in range(5):
            t = i / 4.0
            v = t * t * (3.0 - 2.0 * t)         # smoothstep: no Mach band
            out.append(f'<stop offset="{lo + (hi - lo) * t:.4f}" '
                       f'stop-opacity="{v:.3f}"/>')
        return "".join(out)

    # THE <defs> GOES INSIDE THE GROUP, AND PUTTING IT OUTSIDE PAINTED THE
    # FADE BLACK ON EVERY PICTURE PLATE. `.minimap.arched.atlas .datacut stop`
    # is what gives these stops the sea tone, and a <stop> that no rule
    # reaches takes the SVG default, which is black — so the ramp this
    # function exists to make honest was itself a black smear arriving out of
    # nowhere at the eastern edge, which is the exact rendering fault the
    # fade was written to remove, arrived at from the other side. It survived
    # because the gradient is positioned at 52°E and most plates are framed
    # far west of it, where the ramp is at zero opacity: a defect that is
    # invisible on 300 pages and plain on the twenty that matter. Moving the
    # defs inside makes the selector's own claim true — these gradients ARE
    # the data cut — rather than depending on a second selector agreeing with
    # it.
    return (
        f'<g class="datacut" aria-hidden="true">'
        f'<defs>'
        f'<linearGradient id="cut-{uid}-e" gradientUnits="userSpaceOnUse"'
        f' x1="{ex1:.1f}" y1="{ey1:.1f}" x2="{ex2:.1f}" y2="{ey2:.1f}">'
        f'{stops()}</linearGradient>'
        f'<radialGradient id="cut-{uid}-s" gradientUnits="userSpaceOnUse"'
        f' cx="{ax:.1f}" cy="{ay:.1f}" r="{r33:.1f}">{stops(f0, f1)}</radialGradient>'
        f'</defs>'
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{vw:.1f}" height="{vh:.1f}"'
        f' fill="url(#cut-{uid}-e)"/>'
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{vw:.1f}" height="{vh:.1f}"'
        f' fill="url(#cut-{uid}-s)"/></g>'
    )


def stroke_only(markup):
    """The same country geometry again, as a stroke with no fill.

    THE BOUNDARIES VANISH UNDER THE TERRAIN OTHERWISE, and the first render of
    the prototype proved it: the frame carried a clear France/Switzerland/Italy
    frontier without relief and none with it, because a boundary here is a
    STROKE ON THE LAND PATH and the bands paint over it. ORDER has always put
    `country-bounds` above `terrain`; FOLDED said that layer was carried by
    `land` and that separating it was what "terrain will force". This is that.

    It costs the country rings a second time — about 5 KB on a destination
    plate against 30 KB of terrain — and there is no cheaper form. A `<use>`
    clone is still matched by the selectors that fill the ORIGINAL paths, so
    the copy would come back filled; this repository has already lost a day
    to that once, on the coastal water ramp.

    `<title>` is dropped: the names are on the paths underneath, and a second
    copy would double every country in the accessibility tree.
    """
    if not markup:
        return ""
    out = []
    for m in re.finditer(r'<path\b([^>]*?)\sd="([^"]*)"', markup):
        cls = re.search(r'class="([^"]*)"', m.group(1))
        extra = " here" if cls and "here" in cls.group(1).split() else ""
        out.append(f'<path class="bnd{extra}" d="{m.group(2)}"/>')
    return "".join(out)


def draws_relief(measure):
    """Whether this place's picture gets relief at all.

    ONE PALETTE, ABSOLUTE, AND THE FLAT PLACES ARE REDUCED BY THE SCALE
    RATHER THAN BY A WEAKER INK. A second, fainter strength was built first
    and measured: at 40% of the way to the hypsometric colours the only band
    Bergen has is 0.043 of luminance from the land tone — a layer that ships
    twenty-three kilobytes and cannot be seen. And two strengths make
    #d8ceb4 mean 600 m on one page and something else on another, which is
    not a hypsometric scale, it is decoration that looks like one.

    A flat place is already quieter, automatically: it reaches only the quiet
    end of the scale. Bergen's ground crosses one band boundary and gets one
    step; Chamonix's crosses four. That is the reduction the owner asked for,
    delivered by the thing that was already true.

    Two measurements decide it, both taken from the same model that draws the
    bands and travelling with it in data/geo/terrain-lod1.json: the spread
    within 25 km, and the crest — because the 200 m step is 0.013 of
    luminance from the land tone, deliberately the quietest thing on the
    plate, and a place whose ground reaches only that band would ship a layer
    nobody can read.
    """
    doc = geo.load(SOURCES["terrain"])
    if not doc or not measure:
        return False
    t = doc["relief_thresholds_m"]
    return measure[0] >= t["min_spread"] and measure[1] >= t["min_crest"]


def relief_of(key):
    """[spread, crest] within 25 km of one destination, or None."""
    doc = geo.load(SOURCES["terrain"])
    return (doc or {}).get("relief", {}).get(key)


def relief_radius_km():
    """The radius the two relief figures were measured over.

    Read from the file rather than written here, because the Stay layer
    PRINTS it — "within 40 km of here the ground crests at 2,752 m" is a
    claim to a reader, and the radius is a parameter of `relief.py` that has
    already moved once (25 km measured sea and became 40 over land cells
    only). A number typed into a sentence is the number that stays behind.
    """
    doc = geo.load(SOURCES["terrain"])
    return (doc or {}).get("relief_radius_km")


# HOW WIDE A FRAME MAY BE AND STILL BE A PICTURE OF SOMEWHERE.
#
# Relief answers "what kind of ground is this place in". Across a continent it
# answers a different question — it becomes a physical map of Europe, which is
# a fine document and is not what a journey page is. Measured: the
# Arctic-to-Mediterranean route frames 4,207 km and drew every band in the
# dataset, 787 KB on one page, and at that scale the Alps are a smudge the
# width of a thumb. The owner's rule is the one being kept: the objective is
# not more geographic information, it is more convincing geography, and a
# layer that improves none of recognition, orientation, sense of place,
# hierarchy or beauty is omitted.
#
# 1,500 km, which is chosen from the seventeen journey frames rather than
# picked as a round number. It admits the six that are regional — the Alpine
# Grand Tour at 1,278 km, the Carpathian Arc at 1,388, the Adriatic Run at
# 1,449 — and excludes the eleven that cross the continent, the nearest of
# them at 1,691. The Alps are about 1,200 km end to end, so the widest frame
# this allows is still one mountain system rather than a subcontinent.
#
# A destination plate is 590 km and never comes near it. The cap is not a
# byte budget, but it is also the thing that keeps these pages under the
# recorded weight ceiling, which is how the first version was found.
TERRAIN_MAX_KM = 1500.0


# THE CREDIT FOR THE GROUND, WHICH FOR THREE COMMITS NO PAGE CARRIED.
#
# `docs/data-licenses/aws-terrain-tiles.md` says, in its own Credit section,
# that any page which draws terrain names this sentence. Then relief shipped
# to 153 destination plates, six journeys and the homepage and not one of them
# said the word GMTED — a promise written in a licence document and kept
# nowhere, which is the same failure as the coastline credit that 318 pages
# did not carry and 274 carried by accident.
#
# None of the three datasets requires it. SRTM and GMTED2010 are USGS and
# ETOPO1 is NOAA; all three are US Government public domain and all three
# merely REQUEST credit. It is drawn anyway for the reason the Natural Earth
# credit is drawn: a reader looking at a mountain range is entitled to know
# which survey measured it, and an uncredited relief invites the assumption
# that we modelled it.
#
# AND THE SENTENCE THE LICENCE DOCUMENT ASKED FOR NAMED THE WRONG SURVEY.
# It said "SRTM and GMTED2010", which was true of the six zoom-7 tiles the
# Chamonix prototype fetched and is not true of anything that ships: the
# integration went to zoom 6, where Tilezen's own per-tile
# `x-amz-meta-x-imagery-sources` header names GMTED and ETOPO1 and never
# SRTM. Recorded per tile in the register, so the mistake was a sentence
# nobody re-read rather than a claim nobody could check — 176 of the 182
# shipped tiles name gmted, 157 name etopo1, none name srtm.
#
# ETOPO1 is named even though no band boundary is traced through the sea.
# The grid is smoothed with a three-pass kernel before it is traced, so an
# ocean cell pulls the 200 m contour for about five kilometres inland, and
# every fjord, every Greek island and the whole Italian coast is inside that.
# A dataset that moves the line is a dataset that drew it.
RELIEF_CREDIT = ('Relief from GMTED2010 (USGS) and ETOPO1 (NOAA), '
                 '<a href="/sources">public domain</a>.')


def credited(caption, drew):
    """The relief credit, added to a caption by the plate that drew it.

    IT IS ATTACHED TO THE DRAWING, NEVER TO THE INTENTION. `relief=True` is a
    request; `terrain()` answers it with "" for a frame past the cap, so a
    journey can ask for relief, be refused for its width, and would then have
    printed a credit for a layer nobody can see. Crediting a dataset that
    drew nothing is a smaller lie than failing to credit one that did, and it
    is still a lie about the picture — so this takes the rendered markup as
    its input and the caller never gets a say.

    The credit goes with the other credits, before the map link that ends
    these captions, because a link is a way out of the page and nothing
    should read as an afterthought behind it.
    """
    if not drew or not caption:
        return caption
    cut = caption.rfind('<a href="/map')
    if cut != -1:
        return caption[:cut] + RELIEF_CREDIT + " " + caption[cut:]
    cut = caption.rfind("</figcaption>")
    if cut == -1:
        return caption
    return caption[:cut] + " " + RELIEF_CREDIT + caption[cut:]


def terrain(proj, view, draw=False, frame_km=None):
    """The hypsometric bands, painted lowest first.

    NOT A HILLSHADE. A hillshade is a light source: it invents a direction
    and paints structure onto flat ground. A band claims only height, which
    is the one thing the elevation model measures. See
    docs/terrain-prototype.md for the four strengths that were rendered and
    why the strongest was not chosen.

    Only where the ground says so. `draw` is False on most of the atlas, and
    there this returns nothing at all rather than a faint wash: a Paris
    illustration must not look like a topographic map because the pipeline
    happens to own an elevation model.
    """
    if not draw or not held("terrain"):
        return ""
    if frame_km is not None and frame_km > TERRAIN_MAX_KM:
        return ""
    x, y, w, h = view
    # CLIPPED TO THE WINDOW, AND THE FIRST VERSION WAS NOT. The bands are
    # traced over the whole extent, so the 200 m boundary is a handful of
    # enormous rings — one of them runs from the Pyrenees to the Urals. A
    # rejection test on the ring's bounding box keeps every one of those,
    # and a destination page went from 55 KB to 154 KB drawing the relief of
    # countries it does not show. Sutherland-Hodgman against the window is
    # the same repair `landmass()` already carries for the coastline, and for
    # the same reason: a page must not contain geography it cannot display.
    #
    # The box is a sixth of the window beyond every edge — far enough that
    # the cut and the slivers an even-odd fill leaves where an outer ring and
    # a hole meet on the same clip edge land outside the viewBox, and near
    # enough that a page is not carrying four times the geography it shows.
    # A whole plate's width of padding was the first version and cost 90 KB a
    # page, which is the same failure, one order down.
    pad = max(w, h) * 0.16
    box = (x - pad, y - pad, x + w + pad, y + h + pad)
    out = []
    for min_m, rows in _bands():
        ds = []
        for _lo0, _la0, _lo1, _la1, flat in rows:
            pts = [proj.xy(flat[i + 1], flat[i]) for i in range(0, len(flat), 2)]
            if (max(p[0] for p in pts) < box[0]
                    or min(p[0] for p in pts) > box[2]
                    or max(p[1] for p in pts) < box[1]
                    or min(p[1] for p in pts) > box[3]):
                continue
            pts = geo._clip(pts, box)
            if len(pts) < 3:
                continue
            d, last = [], None
            for px, py in pts:
                q = (round(px, 1), round(py, 1))
                if q == last:
                    continue
                d.append(("M" if not d else "L") + f"{q[0]} {q[1]}")
                last = q
            if len(d) >= 4:
                ds.append("".join(d) + "Z")
        if ds:
            out.append(f'<path class="tband t{min_m}" d="{"".join(ds)}"/>')
    return "".join(out)


def relief_wash(proj, view, thin_units=2.5, min_units=30.0,
                bands=(600, 1200, 2000)):
    """The continent's relief, simplified for a PICTURE rather than a plate.

    THE HOMEPAGE IS THE ONE PLACE THIS PRODUCT DRAWS THE WHOLE CONTINENT AS AN
    IMAGE, and it was the plainest map on the site: a flat silhouette at 15%
    limestone, at the coarsest level of detail, on the largest surface and the
    first thing anybody sees. Every destination plate had warm parchment,
    Atlantic water, an ink coastline, rivers, named summits and four
    hypsometric bands; the front door had none of it.

    `terrain()` is the plate treatment and stays exactly as it is — the
    suitability measurement, the two thresholds and the 1,500 km frame cap are
    a rule about DESTINATION and JOURNEY illustrations and are not touched
    here. This is a different family with a different job: not "what kind of
    ground is this place in" but "this is Europe, and it has mountains in it".

    It reuses the same band boundaries and thins them in the units the
    drawing is actually made in, which is what makes it affordable: the four
    bands over the whole extent are 58,000 vertices and about 660 KB, and the
    three that read at continental scale, thinned at two and a half units,
    are about a hundred rings and 24 KB. The 200 m band is dropped: it is
    0.013 of luminance from the land tone on a plate and nothing at all here.
    """
    if not held("terrain"):
        return ""
    x, y, w, h = view
    box = (x - 40.0, y - 40.0, x + w + 40.0, y + h + 40.0)
    out = []
    for min_m, rows in _bands():
        if min_m not in bands:
            continue
        ds = []
        for _lo0, _la0, _lo1, _la1, flat in rows:
            pts = [proj.xy(flat[i + 1], flat[i]) for i in range(0, len(flat), 2)]
            if (max(p[0] for p in pts) < box[0] or min(p[0] for p in pts) > box[2]
                    or max(p[1] for p in pts) < box[1]
                    or min(p[1] for p in pts) > box[3]):
                continue
            pts = geo.thin(pts, thin_units)
            if len(pts) < 4 or geo.ring_area(pts) < min_units:
                continue
            d, last = [], None
            for px, py in pts:
                q = (round(px, 1), round(py, 1))
                if q == last:
                    continue
                d.append(("M" if not d else "L") + f"{q[0]} {q[1]}")
                last = q
            if len(d) >= 4:
                ds.append("".join(d) + "Z")
        if ds:
            out.append(f'<path class="tband t{min_m}" d="{"".join(ds)}"/>')
    return "".join(out)


def hillshade(proj, view):
    if not held("hillshade"):
        return ""
    unwritten("hillshade", SOURCES["hillshade"])


# WHICH WATERCOURSES ARE CARTOGRAPHY AND WHICH ARE NOISE. Natural Earth
# ships several thousand rivers at 1:50m. This atlas wants the Loire, the
# Seine, the Rhône, the Garonne, the Danube — the rivers a reader recognises
# as the shape of a country — and hundreds of tiny streams would be the
# OpenStreetMap default look, which is the thing this cartography exists not
# to be. Natural Earth's own `scalerank` is the selection: it is the map
# scale at which the publisher intends a feature to appear, so this is their
# editorial judgement rather than one invented here.
RIVER_RANK = 6
LAKE_RANK = 1


def rivers(proj, view, river_rank=None, lake_rank=None, thin_units=0.0,
           min_lake_units=0.0):
    """Rivers and lakes, when the repository holds them.

    THE RANKS ARE PARAMETERS BECAUSE THE HERO NEEDS A DIFFERENT ANSWER. A
    plate is a picture of somewhere and wants the watercourses that carry
    that somewhere's shape: RIVER_RANK 6 and LAKE_RANK 1, which over the
    whole continent is 153 rivers and 65 lakes and 49 KB. The homepage draws
    the whole continent as one image, where 153 rivers is a hydrology map and
    what the picture wants is the half-dozen a reader would name unprompted.
    Everything else about the layer — the clip, the run-splitting, the
    classes, the order — is the same, because two implementations of the same
    layer disagree within a month.

    Two classes, because a hierarchy of one is a list: `major` for the rivers
    that carry a country's shape and `minor` for the rest that survive the
    rank cut. Both thinner than the coastline — a river drawn as heavily as a
    coast turns a country into a leaf.

    ABOVE THE TERRAIN AND BELOW THE LABELS, which is the owner's rule and a
    printed atlas's: water is a separate visual layer and must never inherit
    land shading. A river under the relief would be tinted by the band it
    crosses and would change colour as it came down a valley.
    """
    doc = geo.load(SOURCES["rivers"])
    if not doc:
        return ""
    x, y, w, h = view
    # PROPORTIONAL TO THE WINDOW, AND FOR ONE COMMIT IT WAS NOT. A flat
    # 40-unit pad is 4% of the continent frame this was written against and
    # 44% of a destination frame's 90 units, so a plate carried rivers four
    # hundred plate-units outside its own picture. The same arithmetic as the
    # coastline's own clip, for the same reason: a page must not contain
    # geography it cannot display.
    pad = max(4.0, max(w, h) * 0.10)
    box = (x - pad, y - pad, x + w + pad, y + h + pad)

    def runs(pts):
        """The parts of a polyline inside the box, as separate subpaths.

        A river was emitted WHOLE if any point of it fell in the window, so a
        plate showing fifty kilometres of the Danube shipped the Danube from
        the Black Forest to the Black Sea. One point either side of each run
        is kept so the line still reaches the edge of the frame rather than
        stopping short of it.
        """
        out, cur = [], []
        inside = [box[0] <= px <= box[2] and box[1] <= py <= box[3]
                  for px, py in pts]
        for i, p in enumerate(pts):
            near = (inside[i] or (i and inside[i - 1])
                    or (i + 1 < len(inside) and inside[i + 1]))
            if near:
                cur.append(p)
            elif cur:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return out

    def draw(pts):
        d, last = [], None
        for px, py in pts:
            q = (round(px, 1), round(py, 1))
            if q == last:
                continue
            d.append(("M" if not d else "L") + f"{q[0]} {q[1]}")
            last = q
        return "".join(d) if len(d) >= 2 else ""

    rrank = RIVER_RANK if river_rank is None else river_rank
    lrank = LAKE_RANK if lake_rank is None else lake_rank
    out = []
    for feat in doc.get("rivers", []):
        if feat.get("rank", 99) > rrank:
            continue
        line = feat["line"]
        pts = [proj.xy(line[i + 1], line[i]) for i in range(0, len(line), 2)]
        if thin_units:
            pts = geo.thin(pts, thin_units)
        d = "".join(draw(r) for r in runs(pts))
        if d:
            cls = "major" if feat.get("rank", 99) <= 4 else "minor"
            out.append(f'<path class="riv {cls}" d="{d}">'
                       f'<title>{feat.get("name", "")}</title></path>')
    for feat in doc.get("lakes", []):
        if feat.get("rank", 99) > lrank:
            continue
        d = []
        for ring in feat.get("rings", []):
            pts = [proj.xy(ring[i + 1], ring[i]) for i in range(0, len(ring), 2)]
            if (max(p[0] for p in pts) < box[0] or min(p[0] for p in pts) > box[2]
                    or max(p[1] for p in pts) < box[1]
                    or min(p[1] for p in pts) > box[3]):
                continue
            cut = geo._clip(pts, box)
            if thin_units:
                cut = geo.thin(cut, thin_units)
            # A LAKE TOO SMALL TO READ IS NOT A LAKE, it is a dot of water.
            # The rank in the source is Natural Earth's own importance, and
            # its coarsest step still admits 55 of them across the continent;
            # what a picture of Europe wants is the ones a reader can see,
            # which is a property of THIS drawing rather than of the dataset.
            # Measured in drawn units, like every other threshold here.
            if len(cut) < 3 or (min_lake_units
                                and geo.ring_area(cut) < min_lake_units):
                continue
            piece = draw(cut)
            if piece:
                d.append(piece + "Z")
        if d:
            out.append(f'<path class="lake" d="{"".join(d)}">'
                       f'<title>{feat.get("name", "")}</title></path>')
    return "".join(out)


# ── naming the water that is drawn ───────────────────────────────────────
#
# THE RIVERS WERE THE ONE PHYSICAL FAMILY DRAWN AND NEVER NAMED. Summits get
# `peakname`, ranges and plains get `fname`, seas get `sname`, all through the
# same placement rule and all counted by the same density pass. Rivers had a
# `<title>` and nothing on the page — so Vienna's map carried six anonymous
# blue lines while the dataset that drew them names all 153 of them and ranks
# the Danube at 2.
#
# TWO THINGS MAKE THIS A SUBSYSTEM RATHER THAN PRINTING "DANUBE".
#
# 1. THE DATASET'S RANK IS NOT EUROPEAN IMPORTANCE, and building on it would
#    have produced a map that names the Danube's delta arms and never the
#    Thames. Measured across the file: rank <= 3 is Danube, Donau, Volga,
#    Nile, Al Furat / Euphrates / Firat, and Bratul Chillia / Sfintu Gheorghe
#    / Sulina — while the Thames and the Po are rank 6, the Rhône is rank 6,
#    and the Tiber and the Douro are not in it at all. Rank is a global
#    hydrological figure; what a European atlas needs is how much of the
#    river is IN THIS PICTURE.
#
#    So importance is the drawn extent inside the frame, in the frame's own
#    units — the same idiom as the lake cut two hundred lines up, which is a
#    property of this drawing rather than of the dataset. On Vienna the Danube
#    crosses the whole frame and the Morava clips a corner, and that ordering
#    is computed rather than declared.
#
# 2. THE SAME RIVER IS SEVERAL FEATURES IN SEVERAL LANGUAGES. "Rhine" and
#    "Rhein" are six separate rows; "Danube" and "Donau" are three; the Tagus
#    is "Tejo". Naming from the file directly puts Rhine and Rhein on
#    Cologne's map, one above the other. ALIASES is an authored
#    CLASSIFICATION — the Data Integrity Rule permits authoring one and
#    forbids authoring a measurement, and "the Rhein is the Rhine" is naming,
#    not measuring. The extent is still derived.
ALIASES = {
    "Rhein": "Rhine", "Donau": "Danube", "Duna": "Danube", "Dunav": "Danube",
    "Tejo": "Tagus", "Rhône": "Rhone", "Wisla": "Vistula", "Wisła": "Vistula",
    "Tevere": "Tiber", "Loira": "Loire", "Elba": "Elbe", "Sena": "Seine",
    "Firat": "Euphrates", "Al Furat": "Euphrates",
    "Rio Douro": "Douro", "Dnipro": "Dnieper", "Dnepr": "Dnieper",
    # FOUND BY RUNNING IT OVER ALL 319 AND READING THE NAMES THAT CAME OUT:
    # "Rhin" on four pages and "Tajo" on three, beside "Rhine" on six and
    # "Tagus" on three. The same river under two flags, and no single page
    # showed both — which is exactly why counting the output mattered and
    # looking at one map would not have found it.
    "Rhin": "Rhine", "Tajo": "Tagus", "Tage": "Tagus",
    "Rhein/Rhine": "Rhine", "Donau/Danube": "Danube",
    "Douro/Duero": "Douro", "Duero": "Douro",
    "Maas": "Meuse", "Mosel": "Moselle", "Weichsel": "Vistula",
    "Theiss": "Tisza", "Tisa": "Tisza", "Drau": "Drava", "Sava/Save": "Sava",
}

# A river named on a picture it barely enters is a label about somewhere else.
# As a fraction of the frame's shorter side, so it means the same thing on a
# destination plate and on the continent.
RIVER_MIN_FRAC = 0.34

# HOW CLOSE A RIVER HAS TO PASS TO BE *THIS PLACE'S* RIVER, as a fraction of
# the frame's width. THE FIRST VERSION HAD NO SUCH TEST AND THE TEST SET
# CAUGHT IT: scoring purely by drawn extent, London's map named the **Lek** —
# a Rhine distributary in the Netherlands, which out-measures the Thames on a
# 900-unit frame that reaches the Low Countries. The system had learned to
# place a word rather than to understand a place.
#
# The subject comes first, which is what the pipeline this was built to
# answer says in its first line. A river that passes near the destination is
# what a reader recognises the destination by; everything else is scenery,
# and scenery is ranked by extent underneath it.
RIVER_NEAR_FRAC = 0.16


def river_points(to_xy, view, subject=None, min_frac=RIVER_MIN_FRAC, limit=3):
    """Rivers worth naming on THIS map: (name, [anchors]), best first.

    SUBJECT, THEN SCALE, THEN IMPORTANCE, THEN SPACE.

    · subject — a river passing within `RIVER_NEAR_FRAC` of the place is that
      place's river and sorts above everything, nearest first. The Thames for
      London, the Seine for Paris, the Rhine for Cologne, the Danube for
      Vienna and Budapest and Bratislava.
    · scale — the extent floor and the near radius are both fractions of the
      frame, so they mean the same thing on a destination plate and on a
      continent.
    · importance — drawn extent inside the frame, never the dataset's rank.
      Natural Earth's rank is a global hydrological figure: rank <= 3 is the
      Danube's delta arms and the Euphrates in three languages, while the
      Thames and the Po are rank 6 and the Tiber is not in the file at all.
    · space — several anchors are returned per river, spaced along its longest
      run, because a river crosses the whole picture and its name only needs
      one gap. One anchor is a name that loses a collision it never had to
      lose; the country name has been offered nine for the same reason.

    The caller places them after every place name, so the subject's own labels
    win, and marks them for the phone pass like every other physical family.
    """
    doc = geo.load(SOURCES["rivers"])
    if not doc:
        return []
    x, y, w, h = view
    floor = min(w, h) * min_frac
    near = w * RIVER_NEAR_FRAC
    runs_by_name = {}
    for feat in doc.get("rivers", []):
        raw = (feat.get("name") or "").strip()
        if not raw:
            continue
        name = ALIASES.get(raw, raw)
        line = feat["line"]
        pts = [to_xy(line[i + 1], line[i]) for i in range(0, len(line), 2)]
        cur = []
        for px, py in pts:
            if x <= px <= x + w and y <= py <= y + h:
                cur.append((px, py))
            elif cur:
                runs_by_name.setdefault(name, []).append(cur)
                cur = []
        if cur:
            runs_by_name.setdefault(name, []).append(cur)

    def length(run):
        return sum(math.dist(run[i], run[i + 1]) for i in range(len(run) - 1))

    scored = []
    for name, runs in runs_by_name.items():
        total = sum(length(r) for r in runs)
        if total < floor:
            continue
        best = max(runs, key=length)
        gap = None
        if subject:
            gap = min(math.dist(subject, p) for r in runs for p in r)
        # Anchors along the longest run: the point nearest the subject first
        # where there is one, then evenly spaced, so a name that cannot fit
        # beside the place still fits somewhere on its own river.
        # Ten anchors, evenly spread, nearest the subject first. Six was not
        # enough: Vienna's map is dense with place names and every one of the
        # Danube's six gaps was taken, so the river that IS Vienna went
        # unnamed while a lesser one found a hole.
        step = max(1, len(best) // 10)
        idx = list(range(0, len(best), step))[:10]
        if subject:
            idx.sort(key=lambda i: math.dist(subject, best[i]))
        anchors = [best[i] for i in idx]
        # A river that passes near the subject sorts above every other, and
        # nearest wins among those; the rest fall back to drawn extent.
        own = gap is not None and gap <= near
        key = (0, gap, -total) if own else (1, 0.0, -total)
        scored.append((key, name, anchors, own))
    scored.sort(key=lambda r: r[0])

    # THE SUBJECT'S RIVER IS ALL OR NOTHING, AND THE TEST SET IS WHY.
    # Bratislava named the **Tisza** — 300 km away, and on the map only
    # because the frame is wide — because the Danube's anchors were all taken
    # by place names and the next river down found a gap. A map of Bratislava
    # that names the Tisza and not the Danube is worse than one that names no
    # river at all: it does not merely fail to help a reader place themselves,
    # it tells them something false about where they are.
    #
    # So where a river passes near the subject, it is the only candidate. The
    # scenery below it is offered only on a map that HAS no river of its own —
    # a country portrait, or a destination nowhere near water.
    own_rivers = [r for r in scored if r[3]]
    chosen = own_rivers if own_rivers else scored
    return [(nm, anc) for _k, nm, anc, _o in chosen[:limit]]


def area_points(path, to_xy, view, margin=22.0):
    """Named areas as (x, y, name), in the PLATE's own coordinates.

    THE PROJECTOR IS PASSED IN, NOT ASSUMED. The first version took the
    atlas's projection and used it directly, which is right for a country
    plate and wrong for every other family: a destination map and a route map
    draw the continent's geometry inside their own `transform`, so the land
    is scaled and translated and the labels were not. KJOLEN MOUNTAINS
    appeared over France and NORTHERN EUROPEAN PLAIN over the Alps. The
    caller knows its own transform; this does not.

    Returns points, not markup, because WHERE a name goes is a placement
    decision and this atlas already has one rule for that — tested against
    the real curve of the aperture, in priority order, dropping what does not
    fit. Two placement rules would disagree within a month.

    The geometry is read only for where the word goes. An area label is a
    name, not an outline: drawing the edge of the Alps from a polygon
    somebody else generalised would be a claim about where they end.
    """
    doc = geo.load(path)
    if not doc:
        return []
    x, y, w, h = view
    out = []
    for feat in doc.get("features", []):
        name = (feat.get("name") or "").strip()
        at = feat.get("at")
        if not name or not at or len(at) < 2:
            continue
        px, py = to_xy(at[1], at[0])
        if not (x + margin <= px <= x + w - margin
                and y + margin <= py <= y + h - margin):
            continue
        out.append((px, py, name))
    return out


def summit_points(to_xy, view, most=5):
    """The highest named peaks in this frame, and no more than a few.

    NOT RELIEF, AND NEVER CALLED RELIEF. A hillshade needs an elevation model
    this repository does not have. What it has is 99 summits with the height
    somebody else measured, and a reader sees where the high ground is
    because they cluster along the Alps, the Caucasus and the Pyrenees —
    which is how a printed physical atlas labels a range.

    `most` is the whole discipline: a plate is never a field of triangles.
    The list arrives sorted by height, so taking the first few that fall in
    frame takes the ones a reader has heard of.
    """
    doc = geo.load(SOURCES["summits"])
    if not doc:
        return []
    x, y, w, h = view
    out = []
    for feat in doc.get("features", []):
        at = feat.get("at")
        if not at:
            continue
        px, py = to_xy(at[1], at[0])
        if not (x + 14 <= px <= x + w - 14 and y + 14 <= py <= y + h - 14):
            continue
        out.append((px, py, feat["name"], feat["m"]))
        if len(out) >= most:
            break
    return out


def feature_points(to_xy, view):
    if not held("feature-labels"):
        return []
    return area_points(SOURCES["feature-labels"], to_xy, view)


def water_points(to_xy, view):
    if not held("water-labels"):
        return []
    return area_points(SOURCES["water-labels"], to_xy, view)


def _esc(x):
    return (str(x).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def region_bounds(proj, view):
    if not held("region-bounds"):
        return ""
    unwritten("region-bounds", SOURCES["region-bounds"])


def plate(*, uid, w, h, proj, view, land="", context="", ocean=True,
          transform="", relief=False, frame_km=None,
          cities="", destinations="", labels="", route="", caption="",
          features="", waters="", summits="",
          role="illustration", figure_class="minimap arched atlas",
          aria="", rim=True):
    """A complete editorial plate: the layers, in order, through the arch.

    `land` and `context` arrive already projected — geography is `geo.py`'s
    job and this module never touches a coordinate. Everything else is a
    fragment a caller has built from data the build holds.

    TWO SPACES, AND CONFLATING THEM PUT THE KAMA ON EVERY ALPINE PLATE.

    `w` and `h` are the viewBox — the picture. `view` is the window in
    `proj`'s own coordinates that the picture shows, and `transform` is what
    takes the second to the first. On a country plate they are the same
    thing: the projection is fitted to the frame, so view is (0, 0, w, h) and
    there is no transform. On a destination or a journey plate they are not:
    the continent projection is drawn at 1000x780 and the plate scales a
    small window of it up, inside a translate-and-scale.

    Every caller used to pass `view=(0, 0, w, h)` regardless, and the layers
    this module renders itself — rivers, region boundaries — were selected
    with that box and emitted OUTSIDE the transform. So a destination plate
    asked "which rivers are in the rectangle (0,0)-(900,320) of Europe",
    which is the North Sea and Finland, and drew the answer at continent
    coordinates over a picture of the Alps. **The same 111 watercourses
    appeared on all 824 of them**: the Kama, the Dalälven, the Kemijoki and
    the Neva on Chamonix, on Bergen, on Athens, identically. It looked right
    — blue lines and lakes on a map look like rivers wherever they are — and
    the country plates, which pass a real projection and no transform, were
    correct all along, which is what kept it invisible.

    So the two spaces are now separate parameters and this function wraps
    everything it renders in `transform` itself. A caller cannot get half of
    it right any more, because a caller no longer does any of it.

    The aperture is last and outermost, because it is not a layer: it is the
    opening the whole stack is seen through, and the rim and reveal are
    outside the clip so a reader sees the thickness of the cut.
    """
    def placed(body):
        """Into the plate's own space, if it has one."""
        return f'<g transform="{transform}">{body}</g>' if (transform and body) else body

    terrain_body = terrain(proj, view, relief, frame_km)
    body = []
    for name in ORDER:
        if name == "ocean":
            body.append(_group(name, f'<rect x="0" y="0" width="{w:.0f}" '
                                     f'height="{h:.0f}" class="archground"/>'
                          if ocean else ""))
        elif name == "coastal-water":
            # FOLDED INTO THE LAND SILHOUETTE — see FOLDED, and see the note
            # there about what the first version of this did.
            continue
        elif name == "land":
            body.append(f'<g id="{uid}-land" class="lyr {CLASSES["land"]}">'
                        f'{placed(context + land)}</g>'
                        if (land or context) else "")
        elif name == "terrain":
            body.append(_group(name, placed(terrain_body)))
        elif name == "hillshade":
            body.append(_group(name, placed(hillshade(proj, view))))
        elif name == "rivers":
            body.append(_group(name, placed(rivers(proj, view))))
        elif name == "region-bounds":
            body.append(_group(name, placed(region_bounds(proj, view))))
        elif name == "feature-labels":
            body.append(_group(name, features))
        elif name == "water-labels":
            body.append(_group(name, waters))
        elif name == "country-bounds":
            # UNFOLDED, and only where it has to be. With no terrain the land
            # path's own stroke IS the boundary and a second pass would be
            # 5 KB of duplicate geometry on 1,033 pages for no visible
            # change; with terrain over it the stroke is buried and the
            # picture loses its frontiers. Derived here from the same markup
            # the land layer got, so it cannot drift from it.
            body.append(_group(name, placed(stroke_only(context + land))
                               if terrain_body else ""))
        elif name in ("coastline", "selected"):
            # Still the land path's own stroke and its `here` fill.
            continue
        elif name == "summits":
            body.append(_group(name, summits))
        elif name == "cities":
            # The data cut goes here: above the ground and below every mark.
            # See datacut() — at 49.8°E the eastern ramp is a third opaque
            # and Baku is at 49.8°E.
            body.append(placed(datacut(uid, proj, view)))
            body.append(_group(name, cities))
        elif name == "destinations":
            body.append(_group(name, destinations))
        elif name == "labels":
            body.append(_group(name, labels))
        elif name == "route":
            body.append(_group(name, route))
    inner = "".join(body)
    return (
        f'<figure class="{figure_class}" data-role="{role}">'
        f'<svg viewBox="0 0 {w:.0f} {h:.0f}" role="img" data-world="discover"'
        f'{f" aria-label={chr(34)}{aria}{chr(34)}" if aria else ""}>'
        f'<defs>{arch_clip(uid, w, h)}</defs>'
        f'<g clip-path="url(#arch-{uid})">{inner}</g>'
        f'{arch_rim(w, h) if rim else ""}{arch_edge(w, h)}'
        f'</svg>{credited(caption, terrain_body)}</figure>'
    )
