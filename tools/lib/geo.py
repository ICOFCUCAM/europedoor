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


def country(slug):
    return load(os.path.join("country", slug + ".json"))


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


def landmass(proj, view, doc=None, highlight=None, pad=40.0):
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
    x, y, w, h = view
    box = (x - pad, y - pad, x + w + pad, y + h + pad)
    ctx, ours = [], []
    for ident, ent in sorted(doc["countries"].items()):
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
            if len(cut) < 3:
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
        cls = ""
        if highlight and ent.get("slug") == highlight:
            cls = ' class="here"'
        el = f'<path{cls} d="{"".join(parts)}"><title>{_esc(ent["name"])}</title></path>'
        (ours if ent["atlas"] else ctx).append(el)
    return (f'<g class="context" aria-hidden="true">{"".join(ctx)}</g>',
            f'<g class="countries" aria-hidden="true">{"".join(ours)}</g>')


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
