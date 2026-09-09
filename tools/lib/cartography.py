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

import os

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
HYPSOMETRIC = (
    (0,    200,  "#dfe0cf", "lowland, a muted green-grey"),
    (200,  600,  "#d9d6bd", "foothill, soft olive"),
    (600,  1200, "#d5c9a8", "upland, warm ochre"),
    (1200, 2000, "#cdbb9c", "high ground, pale brown"),
    (2000, None, "#e6e0d6", "mountain, light stone"),
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
    "terrain": "The five steps of HYPSOMETRIC above, from the land tone "
               "toward the warm accent. No hypsometric rainbow: in an "
               "editorial atlas height is felt, not read off a legend, and "
               "the typography stays dominant over the ground.",
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
    "coastline": ("land", "the land path's own stroke; needs a stroke-only "
                          "pass to separate, which terrain will force"),
    "country-bounds": ("land", "same stroke as the coastline — the two are "
                               "one path per country at this LOD"),
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


def terrain(proj, view):
    if not held("terrain"):
        return ""
    unwritten("terrain", SOURCES["terrain"])


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


def rivers(proj, view):
    """Rivers and lakes, when the repository holds them.

    Written now, not stubbed: the day `data/geo/hydrology-lod1.json` lands
    this draws, and the reason to write it before the data is that a layer
    which quietly renders nothing once its file arrives is the failure this
    whole stack was built to make impossible.

    Two classes, because a hierarchy of one is a list: `major` for the rivers
    that carry a country's shape and `minor` for the rest that survive the
    rank cut. Both thinner than the coastline — a river drawn as heavily as a
    coast turns a country into a leaf.
    """
    doc = geo.load(SOURCES["rivers"])
    if not doc:
        return ""
    x, y, w, h = view
    box = (x - 40.0, y - 40.0, x + w + 40.0, y + h + 40.0)
    out = []
    for feat in doc.get("rivers", []):
        if feat.get("rank", 99) > RIVER_RANK:
            continue
        d, last, seen = [], None, False
        for i in range(0, len(feat["line"]), 2):
            px, py = proj.xy(feat["line"][i + 1], feat["line"][i])
            if box[0] <= px <= box[2] and box[1] <= py <= box[3]:
                seen = True
            px, py = round(px, 1), round(py, 1)
            if last == (px, py):
                continue
            d.append(("M" if not d else "L") + f"{px} {py}")
            last = (px, py)
        if seen and len(d) >= 2:
            cls = "major" if feat.get("rank", 99) <= 4 else "minor"
            out.append(f'<path class="riv {cls}" d="{"".join(d)}">'
                       f'<title>{feat.get("name", "")}</title></path>')
    for feat in doc.get("lakes", []):
        if feat.get("rank", 99) > LAKE_RANK:
            continue
        d, last, seen = [], None, False
        for ring in feat.get("rings", []):
            for i in range(0, len(ring), 2):
                px, py = proj.xy(ring[i + 1], ring[i])
                if box[0] <= px <= box[2] and box[1] <= py <= box[3]:
                    seen = True
                px, py = round(px, 1), round(py, 1)
                if last == (px, py):
                    continue
                d.append(("M" if not d else "L") + f"{px} {py}")
                last = (px, py)
            d.append("Z")
        if seen and len(d) >= 4:
            out.append(f'<path class="lake" d="{"".join(d)}">'
                       f'<title>{feat.get("name", "")}</title></path>')
    return "".join(out)


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
          cities="", destinations="", labels="", route="", caption="",
          features="", waters="", summits="", role="illustration",
          figure_class="minimap arched atlas", aria="", rim=True):
    """A complete editorial plate: the layers, in order, through the arch.

    `land` and `context` arrive already projected — geography is `geo.py`'s
    job and this module never touches a coordinate. Everything else is a
    fragment a caller has built from data the build holds.

    The aperture is last and outermost, because it is not a layer: it is the
    opening the whole stack is seen through, and the rim and reveal are
    outside the clip so a reader sees the thickness of the cut.
    """
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
                        f'{context}{land}</g>' if (land or context) else "")
        elif name == "terrain":
            body.append(_group(name, terrain(proj, view)))
        elif name == "hillshade":
            body.append(_group(name, hillshade(proj, view)))
        elif name == "rivers":
            body.append(_group(name, rivers(proj, view)))
        elif name == "region-bounds":
            body.append(_group(name, region_bounds(proj, view)))
        elif name == "feature-labels":
            body.append(_group(name, features))
        elif name == "water-labels":
            body.append(_group(name, waters))
        elif name in ("coastline", "country-bounds", "selected"):
            # Drawn by the land group's own stroke today. When terrain lands
            # these become their own stroke-only pass so relief sits UNDER
            # them, and that pass re-emits the geometry — about 40% of the
            # bytes on these pages. Measured then, not guessed now.
            continue
        elif name == "summits":
            body.append(_group(name, summits))
        elif name == "cities":
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
        f'</svg>{caption}</figure>'
    )
