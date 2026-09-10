"""Real geography: reading data/geo/ and turning it into SVG paths.

The map used to be 313 dots on an empty rectangle, and the page said so in as
many words — there were no coastlines because we had no licence to draw any.
That is now false: Natural Earth is public domain, the pipeline in
scripts/map/ fetches it, records its hash and its terms, simplifies it to
three levels of detail and writes data/geo/. This module is the only thing
that reads that directory.

## Why SVG and not MapLibre GL JS

The map brief names MapLibre, and MapLibre is the right renderer for a map
that carries roads, trails and street-level OSM data. It is the wrong one for
this map today, and the numbers are not close:

    all of Europe's borders, at the LOD a continent view uses   89 KB of JSON
    the same, as SVG path text                                  ~34 KB
    MapLibre GL JS itself                                      ~800 KB raw

The renderer would be eight times the weight of everything it renders, it
needs WebGL, it needs vector tiles (which needs tippecanoe, which is another
dependency and thousands of files where we have fifty-two), and it needs
`worker-src blob:` — the first hole in a `default-src 'none'` policy that the
whole site is arranged around. Paying all of that to draw 6,000 points is a
bad trade, and it is reversible: this pipeline emits lon/lat, not pixels,
precisely so that the day roads arrive the same geometry feeds a tile build
with nothing thrown away.

## Why lon/lat in the file and pixels only here

data/geo/ is renderer-neutral on purpose. Projection is a rendering decision —
the continent view and a country inset want different extents — so it happens
at the last possible moment, here, and never in the committed data.
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEO = os.path.join(ROOT, "data", "geo")

# Cached because a build reads europe-lod1.json once for /map and once more
# for every page that draws a locator, and re-parsing 89 KB fifty times is
# half a second of nothing.
_CACHE = {}


def load(name):
    """Read one file from data/geo/. Returns None if the pipeline has not run.

    Returning None rather than raising is deliberate: a checkout with no
    data/geo/ must still build a site — a map with no land in it, but a site —
    so that somebody who has just cloned the repository sees a working page
    and a clear message rather than a traceback. `checks.py` is what makes
    sure the committed site is not that.
    """
    if name in _CACHE:
        return _CACHE[name]
    path = os.path.join(GEO, name)
    if not os.path.exists(path):
        _CACHE[name] = None
        return None
    with open(path, encoding="utf-8") as fh:
        _CACHE[name] = json.load(fh)
    return _CACHE[name]


# ── THE LAYER STACK ───────────────────────────────────────────────────
#
# BUILD THE TERRAIN-READY ARCHITECTURE; DO NOT INVENT TERRAIN.
#
# A cartographic plate is not one drawing, it is an ordered stack, and the
# reason to declare the stack rather than emit three groups inline is that
# TWO OF ITS LAYERS HAVE NO DATA YET. Relief and hydrology are the largest
# visual gap between this atlas and a printed one, and the honest way to hold
# that gap open is to give each of them a real slot with a named dataset
# requirement, a fixed position in the paint order and its own class — so the
# day `data/geo/` carries rivers, one file appears and the layer draws.
#
# The rule this encodes is the Data Integrity Rule applied to DRAWING: a
# layer whose dataset is absent emits NOTHING. Not a placeholder, not a
# gradient standing in for relief, not a hand-drawn river. An invented
# terrain shade is a measurement authored, and it would be the most
# convincing wrong thing this repository has ever drawn, because a reader
# cannot tell a fitted hillshade from a decorative one.
#
# `needs` is a file in data/geo/, or None for a layer drawn from data the
# build already holds. `checks.py` asserts that every layer here is either
# drawn or absent-with-a-stated-dataset, that the paint order is the one the
# stylesheet expects, and that no page claims a layer that is not held.
LAYERS = (
    # name                needs                    what it draws / will draw
    ("ocean",             None,                    "the water, and the ground of the opening"),
    ("coastal-water",     None,                    "the band of lighter water along a coast"),
    ("land",              "countries",             "land, as a filled field of warm paper"),
    ("terrain",           "terrain-lod1.json",     "elevation tint: upland warmer, lowland cooler, four steps, no more"),
    ("hillshade",         "hillshade-lod1.json",   "relief, one light from the north-west, at most 12% opacity, never on flat ground"),
    ("rivers",            "hydrology-lod1.json",   "rivers by order and lakes, in the water colour, thinner than any coastline"),
    ("coastline",         "countries",             "the edge between land and water, the heaviest line that is not the subject"),
    ("country-bounds",    "countries",             "frontiers between neighbours, the lightest line on the plate"),
    ("region-bounds",     "regions-lod1.json",     "regional frontiers, dashed and lighter still. REFUSED, not merely absent"),
    ("cities",            None,                    "the capital, and cities where a source names them"),
    ("destinations",      None,                    "the places this atlas writes about"),
    ("labels",            None,                    "names, in one hierarchy, placed against the aperture"),
    ("route",             None,                    "a journey's line, where the plate is a route"),
    ("selected",          "countries",             "the country or place the plate is about"),
)

# HOW A LAYER WILL LOOK WHEN IT IS POPULATED, stated now so the renderer is
# terrain-ready rather than terrain-hopeful. Each of these is a decision that
# does not depend on having the data, and writing it down is what stops the
# day the data arrives from becoming a fresh argument about style.
#
#   terrain     Four steps and no more, from the palette's own land tone
#               towards its warm accent. No hypsometric rainbow: the whole
#               point of an editorial atlas is that height is felt, not read.
#   hillshade   One light, from the north-west, at most 12% opacity,
#               multiplied over the terrain tint and clipped to land. Never
#               over flat ground, where it invents structure.
#   rivers      In the water colour, by stream order, and always thinner than
#               the coastline — a river drawn as heavily as a coast turns a
#               country into a leaf.
#   region      Dashed, lighter than a country frontier, and labelled in the
#   bounds      same small caps as a sea. REFUSED today on licensing rather
#               than missing: Eurostat NUTS is the only pan-European source
#               and its provisions have not been read.
LAYER_LOOK_DECIDED = ("terrain", "hillshade", "rivers", "region-bounds")


def layer_state():
    """Which layers this repository can draw today, and which cannot.

    Returns [(name, needs, drawn, why)] in paint order. A layer that needs a
    file `data/geo/` does not have is reported as not drawn, with the file it
    is waiting for — which is what `/sources` prints and what `checks.py`
    reads. Absence is stated, never filled.
    """
    out = []
    for name, needs, role in LAYERS:
        if needs is None or needs == "countries":
            out.append((name, needs, True, role))
            continue
        drawn = os.path.exists(os.path.join(GEO, needs))
        out.append((name, needs, drawn, role))
    return out


def layers_held():
    return [n for n, _needs, drawn, _r in layer_state() if drawn]


def layers_waiting():
    return [(n, needs) for n, needs, drawn, _r in layer_state() if not drawn]


def layer_group(name, body=""):
    """One layer of the stack, as its own group, in paint order.

    Emitted even when empty for the layers that ARE held, because a group
    with a class is where a stylesheet and a reader of the DOM find a layer;
    NOT emitted at all for a layer whose dataset is absent, because an empty
    `<g class="terrain">` on 1,033 pages is a claim that terrain is a thing
    this map has and simply had none of here.
    """
    return f'<g class="lyr lyr-{name}" aria-hidden="true">{body}</g>'


def country(slug):
    return load(os.path.join("country", slug + ".json"))


# HOW WIDE A FRAME MAY BE AND STILL BE DRAWN FROM LOCAL GEOMETRY.
#
# Measured on five destinations at their real frames — A the continental file,
# B the local one unclipped, C the local one clipped to the window:
#
#     place      frame    A coords / bytes    B            C
#     Athens     578 km   492 /  6,280     7,271 / 89,661   895 / 11,119
#     Bergen     582 km   305 /  3,928     7,768 / 95,517   560 /  6,988
#     Corfu      581 km   578 /  7,529     7,271 / 89,661   990 / 12,475
#     Chamonix   589 km   405 /  5,449     7,230 / 89,268   729 /  9,377
#     Krakow     739 km   462 /  6,122     7,496 / 92,357   894 / 11,306
#
# B and C are the same picture — everything B adds is outside the window and
# thrown away by the viewBox — and B is eight times the bytes. So the answer
# is C, and the clip is not an optimisation, it is the whole difference
# between affordable and not.
#
# 1,000 km. Above it a plate is a continental picture: 42 of 319 destinations
# frame between 1,100 and 2,400 km, and at that scale 4.4 km of simplification
# is a third of a pixel and buys nothing. Below it the coarse file is nine
# pixels of error on a coastline a reader is looking straight at.
LOCAL_LOD_MAX_KM = 1000.0

_LOCAL = {}


def local(slug):
    """The continent at lod1, with one country's neighbourhood at lod2.

    A DESTINATION PLATE IS 590 KM WIDE AND WAS DRAWN AT CONTINENTAL DETAIL.
    lod1 simplifies at 0.04 degrees, which is 4.4 km, which is nine pixels on
    a 900-unit plate of a 590 km frame — so Attica came out as a wedge, the
    Cyclades as lozenges and the Norwegian coast as a staircase. The benchmark
    that found it was looking at terrain, and the terrain was fine: the
    coastline underneath had been that coarse on every coastal destination
    since these maps were built, and nobody had put a coastal frame and an
    Alpine frame side by side.

    lod2 is 0.012 degrees — 1.3 km, under three pixels at the same scale — and
    it is already in the repository, one file per country, carrying that
    country and every neighbour whose box comes within 0.75 degrees. So this
    costs no new data: it merges the finer entries over the continental ones
    and leaves everything the local file does not cover at lod1, which is what
    keeps a frame that reaches two countries further from having a hole in it.
    """
    base = load("europe-lod1.json")
    if slug is None or not base:
        return base
    if slug in _LOCAL:
        return _LOCAL[slug]
    fine = country(slug)
    if not fine or not fine.get("countries"):
        _LOCAL[slug] = base
        return base
    merged = dict(base)
    merged["countries"] = dict(base["countries"], **fine["countries"])
    _LOCAL[slug] = merged
    return merged


# LAMBERT CONFORMAL CONIC, at the parameters Europe's own official
# projection uses: standard parallels 35°N and 65°N, origin 52°N, central
# meridian 10°E. Those are EPSG:3034 (ETRS89-LCC), the conformal conic the
# EU publishes pan-European maps on, and this extent (33–71.5°N) is the
# extent it was chosen for.
LCC_P1, LCC_P2, LCC_LAT0, LCC_LON0 = 35.0, 65.0, 52.0, 10.0


def _lcc_n_f():
    """The cone constant and the scale factor. Derived once, not typed.

        n = ln(cos p1 / cos p2) / ln(tan(pi/4 + p2/2) / tan(pi/4 + p1/2))
        F = cos(p1) * tan^n(pi/4 + p1/2) / n
    """
    p1, p2 = math.radians(LCC_P1), math.radians(LCC_P2)
    t1 = math.tan(math.pi / 4 + p1 / 2)
    t2 = math.tan(math.pi / 4 + p2 / 2)
    n = math.log(math.cos(p1) / math.cos(p2)) / math.log(t2 / t1)
    f = math.cos(p1) * (t1 ** n) / n
    return n, f


LCC_N, LCC_F = _lcc_n_f()
LCC_RHO0 = LCC_F / (math.tan(math.pi / 4 + math.radians(LCC_LAT0) / 2) ** LCC_N)


def lcc(lat, lon):
    """(lat, lon) -> planar (x, y) on a unit sphere, y increasing north."""
    rho = LCC_F / (math.tan(math.pi / 4 + math.radians(lat) / 2) ** LCC_N)
    theta = LCC_N * math.radians(lon - LCC_LON0)
    return rho * math.sin(theta), LCC_RHO0 - rho * math.cos(theta)


def principal_frame(doc, slug, margin=1.0):
    """The bbox of a country's PRINCIPAL landmass, not of everything it owns.

    THE FAILURE THIS EXISTS FOR. A country's `bbox` in `data/geo/` is the
    extent of every ring it has, and for one country that is not a picture of
    the country. Portugal's bbox runs from 31.3°W to 6.2°W because the Azores
    are 1,400 km out in the Atlantic: the mainland fills NINE PER CENT of that
    box, so both the portrait and the reference map drew an empty ocean with
    Portugal as a sliver against one corner, and six of six destinations in
    that sliver. Measured across all 49 countries with a polygon, the mainland
    fills the bbox: Portugal 9%, Malta 35%, Denmark 37%, Greece 53%, and 90%+
    for forty of them.

    The rule is `countrymap`'s own, one level down — ONE OUTLIER SHOULD COST
    ONE MARKER, NOT THE WHOLE FRAME — applied to rings instead of dots. Rings
    are ordered by projected area; the largest is the principal landmass, and
    any other ring joins the frame if it lies within `margin` times that
    landmass's own span of it. Stating the distance in the country's own size
    rather than in kilometres is what makes it one rule: Gozo is a fifth of
    Malta and five km off it, the Azores are 2% of Portugal and two Portugals
    away, and an absolute threshold cannot tell those apart.

    Measured at margin 1.0 across the 49: exactly one country loses a ring.
    Portugal loses seven, holding 2.4% of its land area — the Azores and
    Madeira — and no destination at all, because all six of its destinations
    are on the mainland. Denmark keeps Bornholm, Greece keeps Crete and
    Rhodes, Norway keeps its islands, Malta keeps Gozo.

    Returns (bbox, outside) — the lon/lat frame, and how many rings fall
    outside it, so a caller can SAY SO rather than crop in silence.
    """
    ent = None
    for _k, v in (doc.get("countries") or {}).items():
        if v.get("slug") == slug:
            ent = v
            break
    if not ent or not ent.get("rings"):
        return (list(doc["bbox"]) if doc.get("bbox") else None), 0
    metric = []
    for ring in ent["rings"]:
        pts = [(ring[i], ring[i + 1]) for i in range(0, len(ring), 2)]
        pr = [lcc(la, lo) for lo, la in pts]
        a = 0.0
        n = len(pr)
        for i in range(n):
            x0, y0 = pr[i]
            x1, y1 = pr[(i + 1) % n]
            a += x0 * y1 - x1 * y0
        xs = [q[0] for q in pr]
        ys = [q[1] for q in pr]
        lons = [q[0] for q in pts]
        lats = [q[1] for q in pts]
        metric.append((abs(a) / 2.0, min(xs), min(ys), max(xs), max(ys),
                       min(lons), min(lats), max(lons), max(lats)))
    metric.sort(key=lambda z: -z[0])
    m = metric[0]
    span = max(m[3] - m[1], m[4] - m[2])
    lim = (m[1] - margin * span, m[2] - margin * span,
           m[3] + margin * span, m[4] + margin * span)
    keep = [m]
    outside = 0
    for b in metric[1:]:
        if b[1] >= lim[0] and b[2] >= lim[1] and b[3] <= lim[2] and b[4] <= lim[3]:
            keep.append(b)
        else:
            outside += 1
    bbox = [min(k[5] for k in keep), min(k[6] for k in keep),
            max(k[7] for k in keep), max(k[8] for k in keep)]
    return bbox, outside


class Projection:
    """Lambert conformal conic, fitted to whatever extent it is given.

    WHAT THIS REPLACED, AND THE NUMBER THAT JUSTIFIES IT. The previous
    projection was equirectangular with a single cos(latitude) correction
    taken at the middle of the extent. That is exact at one latitude and
    wrong everywhere else, and over Europe "everywhere else" is most of it.
    Measured as the ratio of scale along the parallel to scale along the
    meridian — which is 1.000 everywhere on a conformal projection, and is
    the whole definition of "shape is right here":

        latitude        before        after
        35°N  Crete     -25.8%        +0.0%
        45°N            -14.0%        -0.0%
        52.25°N          -0.7%        -0.0%
        60°N  Oslo      +21.6%        +0.0%
        65°N            +43.9%        -0.0%
        71°N  N. Cape   +86.8%        +0.1%

    Scandinavia was drawn 44% too wide at the Arctic Circle and Crete 26%
    too narrow, on 817 pages, for the whole life of the map. The predecessor
    of the predecessor multiplied x by cos(52°)/cos(52°) — exactly 1 — and
    drew Europe 60% too wide for a year; that was caught by putting real
    coastlines under the dots. This one needed the arithmetic, because a
    coastline stretched 44% still looks like a coastline.

    A conic is not affine, so the browser can no longer be handed six numbers
    and a multiplication. It is handed the four ANGLES instead — the two
    standard parallels, the origin and the central meridian — and derives n
    and F from them with the same three lines this file uses, so there is
    still exactly one projection and one place its parameters are decided.
    A browser check asserts the two implementations agree to a hundredth of
    a pixel on nine points spread across the extent.

    Fixed parallels for every drawing, including country insets. The old
    class re-derived its correction from each inset's own centre, which meant
    a Norway inset and a Cyprus inset were two different projections; now
    they are the same one, which is what "one projection" was always supposed
    to mean.
    """

    def __init__(self, bbox, width, height, pad=0.06):
        x0, y0, x1, y1 = bbox
        # Pad in degrees, proportional to the extent, so a country is not
        # jammed against the frame.
        dx, dy = (x1 - x0) * pad, (y1 - y0) * pad
        x0, y0, x1, y1 = x0 - dx, y0 - dy, x1 + dx, y1 + dy
        # The projected extent is found by walking the boundary, not by
        # projecting the four corners: on a conic the parallels are arcs, so
        # the northernmost drawn point of a box is the middle of its top edge
        # and the corners are lower. Projecting corners alone clips the top
        # of Scandinavia off its own map.
        xs, ys = [], []
        steps = 64
        for i in range(steps + 1):
            t = i / steps
            lon = x0 + (x1 - x0) * t
            lat = y0 + (y1 - y0) * t
            for a, b in ((lat, x0), (lat, x1), (y0, lon), (y1, lon)):
                px, py = lcc(a, b)
                xs.append(px)
                ys.append(py)
        self.px0, self.px1 = min(xs), max(xs)
        self.py0, self.py1 = min(ys), max(ys)
        gw, gh = self.px1 - self.px0, self.py1 - self.py0
        scale = min(width / gw, height / gh)
        self.scale = scale
        self.w, self.h = width, height
        self.ox = (width - gw * scale) / 2.0
        self.oy = (height - gh * scale) / 2.0
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        # Kept for the callers that still print a longitude span in the
        # caption; it is no longer part of projecting anything.
        self.k = math.cos(math.radians((y0 + y1) / 2.0))

    def xy(self, lat, lon):
        px, py = lcc(lat, lon)
        return (self.ox + (px - self.px0) * self.scale,
                self.oy + (self.py1 - py) * self.scale)

    def apex(self):
        """The cone's apex, in this drawing's own coordinates.

        A conic's meridians are straight lines radiating from one point and
        its parallels are circular arcs about it. Both facts are useful the
        moment anything has to follow a parallel — a fade along the southern
        edge of the atlas extent, say — because a LINEAR gradient can follow
        a meridian exactly and a parallel not at all. The hero's first
        southern fade was horizontal and left the 33°N cut showing across
        Anatolia and the Caspian, where that parallel is 150 units higher up
        the drawing than it is over Sicily. That is the same failure as the
        vertical fade over the 52°E cut, one edge round.

        rho is zero at the apex, so in lcc's own space it is (0, RHO0).
        """
        return (self.ox + (0.0 - self.px0) * self.scale,
                self.oy + (self.py1 - LCC_RHO0) * self.scale)

    def parallel_radius(self, lat):
        """How far one parallel sits from the apex, in drawn units."""
        ax, ay = self.apex()
        x, y = self.xy(lat, LCC_LON0)
        return math.hypot(x - ax, y - ay)

    def path(self, flat):
        """One flat [lon,lat,...] ring -> an SVG path `d`, or "" if degenerate.

        Points are emitted at one decimal place. Two was tried first and cost
        18% more bytes to move a coastline by a tenth of a pixel, which is
        below the width of the stroke drawn on top of it.

        Consecutive points that round to the same pixel are dropped. On the
        continent view that removes about a fifth of Norway's fjord vertices
        for no visible change, because a 1:50m source at continent zoom has
        more detail than the raster can show.
        """
        # CLIPPED IN LON/LAT, BEFORE PROJECTING — which the equirectangular
        # predecessor never needed and a conic cannot do without.
        #
        # data/geo/ is cut at 52°E and this projection's extent stops at 45.
        # Under the old projection the extra seven degrees simply landed past
        # x = 1000 and the viewBox threw them away. A conic ROTATES about its
        # apex, so the same vertices swung up and to the right and landed
        # back INSIDE the canvas: /map rendered a large grey wedge over the
        # north-east, which is Russia's straight data-clip edge at 52°E drawn
        # correctly as a radial line and looking exactly like a rendering
        # fault. Found by looking at the map, not by any arithmetic.
        #
        # So a ring is cut to the extent it is being drawn for, and the edge
        # a reader sees is the map's own edge rather than the shape of a
        # file. The min/max pre-test keeps this off the hot path: on the
        # continent view only a handful of rings touch the boundary at all.
        lons = flat[0::2]
        lats = flat[1::2]
        if (min(lons) < self.x0 or max(lons) > self.x1
                or min(lats) < self.y0 or max(lats) > self.y1):
            pts = _clip(list(zip(lons, lats)),
                        (self.x0, self.y0, self.x1, self.y1))
            if len(pts) < 3:
                return ""
            flat = [c for p in pts for c in p]
        out = []
        last = None
        for i in range(0, len(flat), 2):
            x, y = self.xy(flat[i + 1], flat[i])
            p = (round(x, 1), round(y, 1))
            if p == last:
                continue
            out.append(p)
            last = p
        if len(out) < 3:
            return ""
        d = [f"M{out[0][0]} {out[0][1]}"]
        for x, y in out[1:]:
            d.append(f"L{x} {y}")
        d.append("Z")
        return "".join(d)

    def shape(self, rings):
        """All of a country's rings as one path, so one <path> is one country.

        One element per country rather than per island is what makes the
        hit-test, the hover and the highlight work without any bookkeeping:
        clicking Greece's smallest island is clicking Greece.
        """
        return "".join(p for p in (self.path(r) for r in rings) if p)


def thin(pts, eps):
    """Visvalingam-Whyatt in PROJECTED units, for a drawing that is not a plate.

    THE LEVEL OF DETAIL A PICTURE NEEDS IS A PROPERTY OF THE PICTURE, not of
    the file. `data/geo/` is simplified in degrees, which is the right unit
    for a dataset and the wrong one for a frame: 0.04 degrees is 4.4 km, and
    4.4 km is nine pixels on a destination plate and one on the homepage's
    continent. So the continental drawing takes the FINER file and thins it
    here, in the units it is actually drawn in, which is both better looking
    and smaller than the coarse file — the coarse one is simplified in
    longitude, so it flattens Iceland and Scotland far harder than Greece.

    VISVALINGAM RATHER THAN DOUGLAS-PEUCKER, AND THE FIRST VERSION WAS
    DOUGLAS-PEUCKER. It keeps the point furthest from a chord, which on a
    fjord coast is the head of the fjord: the sides go and the head stays, so
    Norway came out covered in bright one-pixel needles radiating from the
    coast, and the Alps grew hairs. Visvalingam drops the vertex whose
    triangle with its neighbours is smallest, which is exactly the measure a
    needle fails — a spike is two long edges enclosing no area. The threshold
    is `eps` squared, so eps stays "a feature about this many units across".
    """
    if eps <= 0 or len(pts) < 5:
        return pts
    n = len(pts)
    closed = pts[0] == pts[-1]
    prev = list(range(-1, n - 1))
    nxt = list(range(1, n + 1))
    nxt[n - 1] = -1
    alive = [True] * n
    limit = eps * eps

    def tri(i):
        a, b, c = prev[i], i, nxt[i]
        if a < 0 or c < 0:
            return float("inf")
        return abs((pts[b][0] - pts[a][0]) * (pts[c][1] - pts[a][1])
                   - (pts[c][0] - pts[a][0]) * (pts[b][1] - pts[a][1])) / 2.0

    import heapq
    heap = [(tri(i), i) for i in range(1, n - 1)]
    heapq.heapify(heap)
    left = n
    while heap and left > 4:
        area, i = heapq.heappop(heap)
        if not alive[i] or area != tri(i):
            continue                      # stale entry, its neighbours moved
        if area > limit:
            break
        alive[i] = False
        left -= 1
        a, c = prev[i], nxt[i]
        if a >= 0:
            nxt[a] = c
        if c >= 0:
            prev[c] = a
        for j in (a, c):
            if j > 0 and j < n - 1 and alive[j]:
                heapq.heappush(heap, (tri(j), j))
    out = [p for p, k in zip(pts, alive) if k]
    if closed and out[0] != out[-1]:
        out.append(out[0])
    return out


def ring_area(pts):
    a = 0.0
    for i in range(len(pts) - 1):
        a += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
    return abs(a) / 2.0


def _clip(pts, box):
    """Sutherland-Hodgman in pixel space.

    The small maps — a city and its neighbours, a journey route — are windows
    a few hundred pixels across onto the continent projection. Without
    clipping, putting land under one of them means emitting the whole of
    France to show the corner of it that is visible, which is 12 KB a page
    across a thousand pages. Clipped, the same corner is a few hundred bytes.
    """
    x0, y0, x1, y1 = box
    tests = (
        (lambda p: p[0] >= x0, 0, x0),
        (lambda p: p[0] <= x1, 0, x1),
        (lambda p: p[1] >= y0, 1, y0),
        (lambda p: p[1] <= y1, 1, y1),
    )
    out = pts
    for inside, axis, v in tests:
        if not out:
            return []
        src, out = out, []
        prev = src[-1]
        for cur in src:
            ci, pi = inside(cur), inside(prev)
            if ci:
                if not pi:
                    out.append(_cross(prev, cur, axis, v))
                out.append(cur)
            elif pi:
                out.append(_cross(prev, cur, axis, v))
            prev = cur
    return out


def _cross(a, b, axis, v):
    other = 1 - axis
    da = b[axis] - a[axis]
    t = 0.0 if da == 0.0 else (v - a[axis]) / da
    p = [0.0, 0.0]
    p[axis] = v
    p[other] = a[other] + (b[other] - a[other]) * t
    return (p[0], p[1])


def distance_bands(doc, slug, proj, near=0.6, mid=1.3):
    """Which countries are near the subject on this drawing, and which are far.

    Returns {slug: "near"|"mid"|"far"}. The measure is the gap between a
    country's drawn bounding box and the subject's, as a fraction of the
    subject's own larger dimension — so it is the same judgement on a plate
    of Luxembourg and a plate of Ukraine, which an absolute distance in
    kilometres would not be.

    Touching or all but touching is `near`; out to about one subject-width is
    `mid`; beyond that is `far`. Nothing is hidden: a far country is still
    drawn, still carries its <title>, and is simply quieter, because a reader
    looking at France still needs to see that Spain is underneath it.
    """
    # CENTRE TO CENTRE, NOT BOX TO BOX. The first version measured the gap
    # between bounding boxes, which is zero the moment two boxes overlap on
    # either axis — so every country on France's plate came out `near`,
    # Austria included, because Austria's box overlaps France's in latitude.
    # A box is not a place.
    mid_pt = {}
    for _k, ent in (doc.get("countries") or {}).items():
        xs, ys = [], []
        for ring in ent.get("rings") or []:
            for i in range(0, len(ring), 2):
                x, y = proj.xy(ring[i + 1], ring[i])
                xs.append(x)
                ys.append(y)
        if xs:
            mid_pt[ent.get("slug")] = ((min(xs) + max(xs)) / 2.0,
                                       (min(ys) + max(ys)) / 2.0,
                                       max(max(xs) - min(xs), max(ys) - min(ys)))
    me = mid_pt.get(slug)
    if not me:
        return {}
    span = me[2] or 1.0
    out = {}
    for s_, b in mid_pt.items():
        if s_ == slug:
            continue
        gap = ((b[0] - me[0]) ** 2 + (b[1] - me[1]) ** 2) ** 0.5 / span
        out[s_] = "near" if gap <= near else ("mid" if gap <= mid else "far")
    return out


def landmass(proj, view, doc=None, highlight=None, pad=40.0, bands=None,
             thin_units=0.0, min_units=0.0, link=None, only=None):
    """Land under a small map, clipped to the window it is drawn in.

    `view` is (x, y, w, h) in the projection's own pixel space — the same
    numbers that go in the viewBox. Returns two <g> elements, context first so
    the Atlas sits on top of it.

    A dot map with nothing under it is a scatter plot. The city minimaps and
    the journey routes were exactly that for a year, and the reason was that
    there was no coastline to put under them; there is now, and the only thing
    standing between them was the page weight this function removes.
    """
    doc = doc if doc is not None else load("europe-lod1.json")
    if not doc:
        return "", ""
    # `only` DRAWS A SUBSET AND NOTHING ELSE, so a caller that already has the
    # continent on the page can put a handful of countries ON it rather than
    # repeat it. The atlas index needs that: nine macro regions, each shown as
    # the countries it is made of, over ONE shared silhouette. Drawing the
    # whole continent nine times would be the right picture at nine times the
    # bytes, and page weight is an invariant here for a reason.
    only = None if only is None else set(only)
    x, y, w, h = view
    box = (x - pad, y - pad, x + w + pad, y + h + pad)
    ctx, ours = [], []
    for ident, ent in sorted(doc["countries"].items()):
        if only is not None and ent.get("slug") not in only:
            continue
        parts = []
        for ring in ent["rings"]:
            pts = []
            last = None
            for i in range(0, len(ring), 2):
                px_, py_ = proj.xy(ring[i + 1], ring[i])
                if (px_ < box[0] - 1e6):      # never true; kept explicit for clarity
                    continue
                pts.append((px_, py_))
            if not pts:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if max(xs) < box[0] or min(xs) > box[2] or max(ys) < box[1] or min(ys) > box[3]:
                continue
            cut = _clip(pts, box)
            if thin_units:
                cut = thin(cut, thin_units)
            if len(cut) < 3 or (min_units and ring_area(cut) < min_units):
                continue
            d = []
            for i, (cx, cy) in enumerate(cut):
                cx, cy = round(cx, 1), round(cy, 1)
                if last == (cx, cy):
                    continue
                d.append(("M" if not d else "L") + f"{cx} {cy}")
                last = (cx, cy)
            if len(d) >= 3:
                parts.append("".join(d) + "Z")
        if not parts:
            continue
        # `highlight` takes a slug or a set of them. The macro maps need the
        # set: a macro region IS a group of whole countries, which is the one
        # grouping in this atlas with real polygons behind it — a region is a
        # grouping with no boundary and is drawn as its own destinations.
        cls = ""
        if highlight and ent.get("slug") in (
                {highlight} if isinstance(highlight, str) else set(highlight)):
            cls = "here"
        elif bands:
            # NEIGHBOURS ARE CONTEXT, AND DISTANT COUNTRIES ARE QUIETER STILL.
            # Every country used to be drawn in one tone, so France's plate
            # was France plus twenty polygons of equal weight all asking to
            # be read. The band is the country's own distance from the
            # subject, measured on the drawing in the drawing's own units —
            # derived, like everything else here, and not a list somebody
            # typed.
            cls = bands.get(ent.get("slug"), "")
        el = (f'<path{f" class={chr(34)}{cls}{chr(34)}" if cls else ""} '
              f'd="{"".join(parts)}"><title>{_esc(ent["name"])}</title></path>')
        # A COUNTRY CAN BE A WAY IN, WHERE THE CALLER SAYS SO. `link` takes
        # the entry and returns an href or "": the shape is then the link and
        # its <title> is the accessible name, which is what an SVG <a> uses.
        # Off by default, because a country on a destination plate is context
        # a reader is not meant to leave through and 824 plates do not need
        # 12,000 more anchors in them.
        if link and ent["atlas"]:
            href = link(ent)
            if href:
                el = f'<a href="{href}">{el}</a>'
        (ours if ent["atlas"] else ctx).append(el)
    return (f'<g class="context" aria-hidden="true">{"".join(ctx)}</g>',
            f'<g class="countries" aria-hidden="true">{"".join(ours)}</g>')


def beyondmass(proj, view, thin_units=0.0, min_units=0.0, pad=40.0):
    """The land outside the atlas: one path of `d` data PER STRIP.

    A list rather than a string, because the two strips cross-fade with the
    atlas along different edges — the eastern one along the 52°E meridian and
    the southern one along the 33rd parallel — and a single mask for both
    would erase the Sahara or the Urals depending which edge it followed.

    `beyond-lod0.json` holds anonymous rings — no country, no slug, no title —
    because it is scenery for one picture rather than geography this product
    writes about. See BEYOND_BBOX in scripts/map/process.py for why it exists
    at all: the hero's subject is the continent, and a continent cut off at
    52°E ends in mid-air.

    It returns bare path data rather than a group, because the caller merges
    it into a single element for exactly the reason the hero merges its own
    two: fifty translucent shapes with shared edges composite into fifty
    bright frontiers, and a political map is the one thing this drawing must
    not become.
    """
    doc = load("beyond-lod0.json")
    if not doc:
        return []
    x, y, w, h = view
    box = (x - pad, y - pad, x + w + pad, y + h + pad)
    return [_beyond_strip(st["rings"], proj, box, thin_units, min_units)
            for st in doc["strips"]]


def _beyond_strip(rings, proj, box, thin_units, min_units):
    out = []
    for ring in rings:
        pts = [proj.xy(ring[i + 1], ring[i]) for i in range(0, len(ring), 2)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if (max(xs) < box[0] or min(xs) > box[2]
                or max(ys) < box[1] or min(ys) > box[3]):
            continue
        # THINNED BEFORE IT IS CLIPPED, and the other order drew chords
        # across the picture. Sutherland-Hodgman leaves a run of vertices
        # along the box edge where a ring leaves the window; thinning that
        # run afterwards collapses it into one straight segment from where
        # the ring left to where it came back, which at this tolerance cut
        # visible diagonals across the Sahara and across Kazakhstan. The
        # clip is exact and cheap, so it goes last and stays exact.
        if thin_units:
            pts = thin(pts, thin_units)
        cut = _clip(pts, box)
        if len(cut) < 3 or (min_units and ring_area(cut) < min_units):
            continue
        d, last = [], None
        for cx, cy in cut:
            q = (round(cx, 1), round(cy, 1))
            if q == last:
                continue
            d.append(("M" if not d else "L") + f"{q[0]} {q[1]}")
            last = q
        if len(d) >= 3:
            out.append("".join(d) + "Z")
    return "".join(out)


def _esc(x):
    return (str(x).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def km_per_unit(proj, lat, lon):
    """Ground kilometres per projected unit, at one point.

    The captions used to compute this from degrees per pixel and a cosine,
    which was correct only for the equirectangular projection that is gone.
    A conformal projection has ONE scale at a point — the same along the
    parallel and along the meridian, which is what conformal means — so it is
    measured rather than derived: project two points a fiftieth of a degree
    apart, and divide the real distance by the drawn one.
    """
    d = 0.02
    x1, y1 = proj.xy(lat, lon - d)
    x2, y2 = proj.xy(lat, lon + d)
    drawn = math.hypot(x2 - x1, y2 - y1)
    if drawn <= 0:
        return 0.0
    # Great-circle distance between the same two points, R = 6371 km.
    a = math.radians(lat)
    ground = 2 * 6371.0 * math.asin(
        math.cos(a) * math.sin(math.radians(d)))
    return ground / drawn


# WHERE THE SCALE BAR SITS, IN ONE PLACE. A label pass has to keep out of it,
# and two copies of "bottom-left, 3.5% in, 7.5% up" drift the first time one
# of them is nudged. BAR_MAXW is the widest bar scale_bar will draw before it
# gives up (the 0.42 test below), which is what a reservation has to assume:
# the length is chosen from the frame's own scale and is not known until then.
BAR_X, BAR_UP, BAR_TICK, BAR_MAXW, BAR_TEXT = 0.035, 0.075, 0.018, 0.42, 0.055


def _bar_anchor(frame_w, frame_h):
    return (frame_w * BAR_X, frame_h - frame_h * BAR_UP,
            max(3.0, frame_h * BAR_TICK))


def scale_bar_box(frame_w, frame_h):
    """The rectangle a scale bar occupies, so a name can be kept out of it.

    THE LABEL PASS DID NOT KNOW THE BAR WAS THERE. After the destination map
    was given a clearance test, the last two overlapping pairs on the whole
    site were both a peak name lying across "100 km" — the one piece of type
    on these plates that is placed by arithmetic rather than by the placement
    rule, and so the one piece it had never been told about.
    """
    x, y, tick = _bar_anchor(frame_w, frame_h)
    top = y - tick - frame_h * BAR_TEXT
    return (x, top, frame_w * BAR_MAXW, (y - top) + 2.0)


def scale_bar(proj, lat_lo, lat_hi, lon, units_per_unit, frame_w, frame_h,
              tol=0.02):
    """A scale bar, or nothing, and the arithmetic that decides which.

    THE PROJECTION IS WHAT MADE THIS POSSIBLE, AND IT IS WORTH SAYING WHY.
    Under the equirectangular projection that preceded the conic, ground
    distance per drawn unit along a parallel ran from 7.52 km at 33°N to
    2.85 km at 71.5°N — a spread of 164% inside one frame. A single bar
    would not have been an approximation, it would have been a lie, and this
    site does not draw those. Under the conformal conic the same figure runs
    6.05 to 6.57 km/unit across the whole of Europe, is exact on both
    standard parallels, and is never more than 4.6% out anywhere.

    So the bar is drawn where it is honest and omitted where it is not: the
    scale is computed at the frame's own centre latitude, the worst departure
    across the frame's OWN latitude span is measured, and if that exceeds
    `tol` there is no bar. A map of Svalbard and Crete together gets none. A
    map of the Cyclades gets one good to a fraction of a percent.

    `units_per_unit` converts one RENDERED unit into one projection unit —
    the minimaps draw under a scale(span) transform and pointsmap normalises
    every frame to 1000 wide, so neither of them draws in projection units.
    """
    mid = (lat_lo + lat_hi) / 2.0
    at_mid = km_per_unit(proj, mid, lon)
    worst = 0.0
    steps = 8
    for i in range(steps + 1):
        lat = lat_lo + (lat_hi - lat_lo) * i / steps
        worst = max(worst, abs(km_per_unit(proj, lat, lon) / at_mid - 1.0))
    if worst > tol:
        return ""
    km_per_drawn = at_mid * units_per_unit
    # A bar somewhere near a fifth of the frame, at a number a reader can
    # hold: 10, 20, 50, 100, 200, 500, 1000.
    want = frame_w * 0.2 * km_per_drawn
    steps_km = [10, 20, 50, 100, 200, 500, 1000, 2000]
    km = min(steps_km, key=lambda v: abs(math.log(v / want)) if want > 0 else 0)
    length = km / km_per_drawn
    if length < frame_w * 0.06 or length > frame_w * 0.42:
        return ""
    x, y, tick = _bar_anchor(frame_w, frame_h)
    return (f'<g class="scalebar" aria-hidden="true">'
            f'<path d="M{x:.1f} {y - tick:.1f}V{y:.1f}H{x + length:.1f}'
            f'V{y - tick:.1f}"/>'
            f'<text x="{x:.1f}" y="{y - tick - 4:.1f}">{km:,} km</text></g>')


def sources_line(doc):
    """The attribution sentence for whatever drew this map.

    Natural Earth requires no credit at all — the licence says so explicitly.
    We print one anyway, because a reader looking at a border is entitled to
    know which dataset drew it and at what scale, and because an uncredited
    map invites the assumption that we surveyed it. If a dataset with a real
    attribution condition is ever added, this is the function that already
    carries it to every page rather than the one that has to be written in a
    hurry.
    """
    if not doc or not doc.get("sources"):
        return ""
    names = sorted({s["dataset"] for s in doc["sources"]})
    return " and ".join(names)
