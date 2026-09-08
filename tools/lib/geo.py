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


class Projection:
    """Equirectangular, corrected at the middle latitude of its own extent.

    The correction is what stops Europe looking stretched: a degree of
    longitude at 60°N is half the ground distance of one at the equator, so
    without cos(lat) Norway is twice as wide as it should be. Correcting at
    the *centre of the extent being drawn* rather than at a fixed 52° matters
    once there are country insets — a Norway inset corrected at 52° is visibly
    wrong, and a Cyprus one is wrong the other way.
    """

    def __init__(self, bbox, width, height, pad=0.06):
        x0, y0, x1, y1 = bbox
        # Pad in degrees, proportional to the extent, so a country is not
        # jammed against the frame.
        dx, dy = (x1 - x0) * pad, (y1 - y0) * pad
        x0, y0, x1, y1 = x0 - dx, y0 - dy, x1 + dx, y1 + dy
        self.k = math.cos(math.radians((y0 + y1) / 2.0))
        # Fit the corrected extent into the box, preserving aspect, so the
        # drawing is centred rather than squashed.
        gw = (x1 - x0) * self.k
        gh = (y1 - y0)
        scale = min(width / gw, height / gh)
        self.scale = scale
        self.w, self.h = width, height
        self.ox = (width - gw * scale) / 2.0
        self.oy = (height - gh * scale) / 2.0
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

    def xy(self, lat, lon):
        x = self.ox + (lon - self.x0) * self.k * self.scale
        y = self.oy + (self.y1 - lat) * self.scale
        return x, y

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
