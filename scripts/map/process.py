#!/usr/bin/env python3
"""Stage 2 of the map pipeline: PROCESS -> SIMPLIFY -> VALIDATE -> PUBLISH.

    python3 scripts/map/process.py            rebuild data/geo/
    python3 scripts/map/process.py --check    rebuild in memory, compare, fail on drift

Reads the raw Natural Earth GeoJSON committed under data/raw/ and writes the
production geometry under data/geo/. Nothing here touches the network; the
whole stage is a pure function of the raw files and this script, so `--check`
can assert that what is committed is what the pipeline produces. Same contract
as `site/`: a stale data/geo/ means the map is drawing something no longer
derivable from its documented source.

## What comes out

    data/geo/europe-lod0.json   whole continent, coarse   (zoom 0-3)
    data/geo/europe-lod1.json   whole continent, borders  (zoom 4-6)
    data/geo/country/<slug>.json  one country in detail   (zoom 6+)

Three levels rather than one file, because §16 of the map brief is right for a
reason that only shows up on a phone: the continent view needs Norway's
coastline to be a suggestion, and the Norway view needs it to be a coastline.
Shipping the detailed version at continent zoom costs six times the bytes to
draw something no one can see.

## Coordinates

Longitude/latitude, WGS84, rounded to three decimal places — about 110 m at
these latitudes, which is finer than a 1:50m cartographic source can honestly
claim. Deliberately NOT pre-projected: the day this data feeds a second
renderer (a per-country inset at a different extent, a vector tile, a static
social card) a pre-projected file is a file that has to be regenerated. The
projection belongs to the renderer.

## What is deliberately absent

No region polygons. EuropeDoor holds region *membership* — which destinations
sit in Vestland — but no region *geometry*, because the dataset that has it
(Eurostat NUTS) is blocked on a licensing question; see
docs/data-licenses/eurostat-gisco-nuts.md. Drawing a hull around Bergen and
Ålesund and calling it Vestland would look like an answer and be a guess, and
§21 of the brief rules out exactly that trade.
"""

import gzip
import json
import math
import os
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "geo")
COUNTRIES = os.path.join(ROOT, "data", "countries")

# The window on the world. Wide enough to hold Iceland (-24), the Azores are
# out (they are a Portuguese inset problem, not a bounding box problem),
# Svalbard's south (74N is clipped), Cyprus (34E) and the Caucasus (47E).
# Anything outside is cut, not dropped: Russia's polygon runs to Kamchatka and
# without clipping the continent view is a thin strip down the left.
BBOX = (-32.0, 33.0, 52.0, 72.5)

# Natural Earth identifies a country several ways and each of them has a hole
# in it somewhere. ISO_A2 is "-99" for a handful of entities including Kosovo,
# ISO_A2_EH patches most of those, and the rest are named here rather than
# guessed. The key is our own two-letter `code` from data/countries/*.json.
ISO_FIX = {
    "KOS": "xk",   # Kosovo — ISO_A2 is -99; XK is the de-facto user-assigned code
    "GBR": "gb",
    "GRC": "gr",
    "FRA": "fr",   # NE splits France; the metropolitan polygon carries FRA
    "NOR": "no",
    "TUR": "tr",
    "VAT": "va",
    "SMR": "sm",
    "MCO": "mc",
    "LIE": "li",
    "AND": "ad",
    "MLT": "mt",
}

# The one country in the atlas with no ISO alpha-3 code, because ISO has
# never assigned one.
ISO3_USER_ASSIGNED = {"xk": "XKX"}

# Countries we do not have a page for but must draw, or the map has holes in
# it where the reader expects land. They are rendered as context: no fill
# treatment, no hover, no link. Not drawing them was tried first and produced
# a Mediterranean with no far shore, which reads as an error rather than as a
# choice.
CONTEXT = {
    "DZA": "Algeria", "TUN": "Tunisia", "MAR": "Morocco", "LBY": "Libya",
    "EGY": "Egypt", "SYR": "Syria", "LBN": "Lebanon", "ISR": "Israel",
    "IRQ": "Iraq", "IRN": "Iran", "JOR": "Jordan", "KAZ": "Kazakhstan",
    "TKM": "Turkmenistan", "UZB": "Uzbekistan", "SAU": "Saudi Arabia",
    "PSE": "Palestine", "CYN": "Northern Cyprus",
    "ESH": "Western Sahara",
}
# Greenland and Svalbard were in that list and came out. Both fall almost
# entirely outside the extent, so each rendered as a clipped sliver in a
# corner — and a sliver in a corner does not read as "there is more land that
# way", it reads as a bug in the drawing. Context only works when the shape is
# recognisable enough to be read as a place.

# WHAT IS BEYOND THE ATLAS, FOR THE HOMEPAGE HERO AND NOTHING ELSE.
#
# BBOX above is the atlas: it stops at 52°E because that is where this product
# stops writing about places, and every map on the site is drawn from it. That
# is right for a map of a place and wrong for the one picture on the site whose
# subject is the CONTINENT — cut at 52°E, Europe ends in mid-air, and the hero
# had to fade its own eastern quarter to stop the cut reading as a rendering
# fault. Fading the edge of the world is not the same as drawing what is
# there.
#
# So the hero gets a second, much quieter geometry: the land around Europe,
# out to the Yenisei and down past Arabia, drawn as the ground Europe sits on
# rather than as anywhere this atlas has anything to say about. It is a
# separate file for the same reason the terrain is: nothing else may draw it,
# and a wider extent must not become a wider atlas by accident.
# AND EVERY EDGE OF THIS BOX IS A STRAIGHT CUT THROUGH REAL LAND, so the box
# is chosen so that none of them is inside the hero's frame. The first one ran
# -32°E to 74°N and both of those showed: Greenland was sliced down the middle
# of Scoresby Sund and drew a straight vertical edge in the Atlantic, and
# Novaya Zemlya was cut along the 74th parallel. At 17% opacity on a dark sea
# that is faint on a desktop and unmistakable on a phone, where the drawing is
# a third of the size and the eye has nothing else to look at.
#
# West is at -14.5°E: west of the African Atlantic coast at every latitude the
# frame shows — -11 left one vertex of the Saharan coast cut at 28.7°N, inside
# the frame at the bottom left — and east of the Canaries and of everything in
# the north Atlantic that survives the minimum ring size, so no island is
# sliced. It is not a round number because the honest one is wherever the cut
# stops crossing land, which is measured. North is at 78°N, above the top of
# the hero's frame at every longitude it holds (the frame's northern edge runs
# 77.8°N over Norway and 73.3°N over the Urals), so Svalbard's slice happens
# off the picture. East and south were already clear: under this conic the
# 102°E cut runs x=1,489 at 36°N and y=-192 at 68°N, and the 8°N cut y=1,003
# at 50°E, none of them inside the frame.
# checks.py asserts all four, because a wider dataset later is exactly the
# sort of improvement that would quietly put one back.
BEYOND_BBOX = (-14.5, 8.0, 102.0, 78.0)

# AND IT IS THE COMPLEMENT OF THE ATLAS, NOT A BOX THAT CONTAINS IT.
#
# The first version took every landmass in BEYOND_BBOX, which includes the
# whole of Europe — so under every European coast there was a second, coarser
# copy of the same coastline. Drawn in graphite under translucent parchment,
# the disagreement between two generalisations of one coast showed as a BLACK
# FRINGE five or six units wide along Anatolia, the Black Sea and North
# Africa. It reads as a drop shadow, which is exactly the kind of accident
# that gets mistaken for a decision.
#
# Two levels of detail of the same coast can be stacked only where one is
# hidden, and the honest fix is not a finer copy — it is not drawing the copy
# at all. This layer exists to show the ground the atlas does NOT hold, so it
# is cut to exactly that: the strip east of the atlas extent and the strip
# south of it. The two seams are 52°E and 33°N, which are the atlas's own cuts
# and already have the two fades over them.
# AND THE STRIPS OVERLAP THE ATLAS SLIGHTLY, INTO ITS OWN FADES. Cut exactly
# at 52°E and 33°N they abutted the atlas edge-to-edge, and the atlas fades to
# nothing 40 units short of its eastern cut — so between the two there was a
# band of bare sea and then a hard black diagonal, which is the rendering
# fault the fade was written to remove, arrived at from the other side. The
# strips reach back INTO the atlas far enough to cross-fade with it: the
# atlas's eastern fade is 320 units wide and is already down to 4% opacity at
# 46°E, so a strip starting there was still a hard edge in open sea. It
# starts at 36°E now — about 143 drawn units west of the cut — and fades in
# over the same band the atlas fades out over. The coastline they share in
# between is the Black Sea's eastern shore and the Arctic coast, both under a
# parchment that is a third opaque at most.
BEYOND_STRIPS = (
    (36.0, 8.0, 102.0, 78.0),      # east of the atlas: the Caspian to the Urals
    (-14.5, 8.0, 52.0, 34.0),      # south of it: the Sahara, Arabia, the Sahel
)
BEYOND = "beyond-lod0.json"

# Coarser than lod0 and with a much larger minimum ring, because this is
# drawn at a fifth of the contrast of the land in front of it: an island that
# reads as a speck in the subject reads as dirt on the lens out here.
BEYOND_EPS, BEYOND_MINBOX = 0.11, 0.6

# Level of detail. `eps` is the Douglas-Peucker tolerance in degrees; `minbox`
# drops a ring whose bounding box is smaller than this many square degrees.
# The numbers were chosen by rendering, not by theory — see docs/map-architecture.md.
LODS = {
    "lod0": {"src": "ne_110m_admin_0_countries.geojson.gz", "eps": 0.055, "minbox": 0.04},
    "lod1": {"src": "ne_50m_admin_0_countries.geojson.gz",  "eps": 0.04, "minbox": 0.010},
    "lod2": {"src": "ne_50m_admin_0_countries.geojson.gz",  "eps": 0.012, "minbox": 0.0015},
}


# ── geometry ──────────────────────────────────────────────────────────────

def rdp(pts, eps):
    """Douglas-Peucker, iterative.

    Recursive is the textbook form and blows the stack on Norway, which
    arrives as a single ring of 6,000-odd points. The explicit stack is not a
    micro-optimisation; it is the difference between working and not.
    """
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    e2 = eps * eps
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        ax, ay = pts[i]
        bx, by = pts[j]
        dx, dy = bx - ax, by - ay
        den = dx * dx + dy * dy
        best, bi = -1.0, -1
        for k in range(i + 1, j):
            px, py = pts[k]
            if den == 0.0:
                d = (px - ax) ** 2 + (py - ay) ** 2
            else:
                t = ((px - ax) * dx + (py - ay) * dy) / den
                t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                d = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
            if d > best:
                best, bi = d, k
        if best > e2:
            keep[bi] = True
            stack.append((i, bi))
            stack.append((bi, j))
    return [p for p, k in zip(pts, keep) if k]


def clip(ring, box):
    """Sutherland-Hodgman against an axis-aligned box.

    Clipping rather than discarding matters for exactly four countries —
    Russia, Turkiye, Kazakhstan and Norway (Svalbard) — but those four are the
    difference between a map of Europe and a map of the western third of Asia.
    """
    x0, y0, x1, y1 = box
    edges = (
        (lambda p: p[0] >= x0, lambda a, b: _ix(a, b, x0, 0)),
        (lambda p: p[0] <= x1, lambda a, b: _ix(a, b, x1, 0)),
        (lambda p: p[1] >= y0, lambda a, b: _ix(a, b, y0, 1)),
        (lambda p: p[1] <= y1, lambda a, b: _ix(a, b, y1, 1)),
    )
    out = ring
    for inside, cut in edges:
        if not out:
            return []
        src, out = out, []
        prev = src[-1]
        for cur in src:
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
            prev = cur
    return out


def _ix(a, b, v, axis):
    """Where segment a-b crosses the line (axis == v)."""
    other = 1 - axis
    da = b[axis] - a[axis]
    t = 0.0 if da == 0.0 else (v - a[axis]) / da
    p = [0.0, 0.0]
    p[axis] = v
    p[other] = a[other] + (b[other] - a[other]) * t
    return (p[0], p[1])


def bbox_of(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def area2(ring):
    """Twice the signed shoelace area. Used only for ordering rings biggest
    first, so a country's mainland is the ring a label or a hit-test finds."""
    s = 0.0
    for i in range(len(ring)):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % len(ring)]
        s += x0 * y1 - x1 * y0
    return abs(s)


# ── the source ────────────────────────────────────────────────────────────

def read_ne(name):
    with gzip.open(os.path.join(RAW, name), "rt", encoding="utf-8") as fh:
        return json.load(fh)


def key_for(props):
    """Our two-letter country code for a Natural Earth feature, or None."""
    a3 = (props.get("ADM0_A3") or "").upper()
    if a3 in ISO_FIX:
        return ISO_FIX[a3]
    for field in ("ISO_A2_EH", "ISO_A2", "WB_A2"):
        v = (props.get(field) or "").strip()
        if v and v != "-99" and len(v) == 2:
            return v.lower()
    return None


def rings_for(feature, eps, minbox, box=None):
    """The rings of one Natural Earth feature, clipped to `box`.

    The box is a parameter because the homepage hero needs a WIDER one than
    the atlas — see BEYOND_BBOX. Everything else passes nothing and gets the
    atlas extent, which is what every call did when it was a constant.
    """
    box = BBOX if box is None else box
    geom = feature.get("geometry") or {}
    if geom.get("type") == "MultiPolygon":
        polys = geom["coordinates"]
    elif geom.get("type") == "Polygon":
        polys = [geom["coordinates"]]
    else:
        return []
    out = []
    for poly in polys:
        ring = [(float(x), float(y)) for x, y in poly[0]]
        x0, y0, x1, y1 = bbox_of(ring)
        if x1 < box[0] or x0 > box[2] or y1 < box[1] or y0 > box[3]:
            continue
        ring = clip(ring, box)
        if len(ring) < 4:
            continue
        bx0, by0, bx1, by1 = bbox_of(ring)
        if (bx1 - bx0) * (by1 - by0) < minbox:
            continue
        ring = rdp(ring, eps)
        if len(ring) < 4:
            continue
        out.append(ring)
    out.sort(key=area2, reverse=True)
    return out


def flatten(ring):
    """[(lon,lat), ...] -> [lon,lat,lon,lat,...] rounded to 3 decimals.

    Flat rather than nested because a pair-per-point JSON array is roughly 40%
    larger for the same numbers and reads no better once there are 6,000 of
    them."""
    out = []
    for x, y in ring:
        out.append(round(x, 3))
        out.append(round(y, 3))
    return out


# ── the knowledge graph ───────────────────────────────────────────────────

def load_graph():
    """Country slug/name/code, plus the destinations and places we hold.

    The map does not keep its own list of anything — §10 of the brief, and the
    reason it matters is that two lists diverge silently. Every point on the
    finished map is read from data/countries/*.json at build time and carries
    the id of the record it came from.
    """
    graph = {}
    for name in sorted(os.listdir(COUNTRIES)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(COUNTRIES, name), encoding="utf-8") as fh:
            c = json.load(fh)
        graph[c["code"].lower()] = {
            "slug": c["slug"],
            "name": c["name"],
            "code": c["code"].lower(),
            "macro": c["macro"],
            "regions": [
                {
                    "slug": r["slug"],
                    "name": r["name"],
                    "cities": [
                        {"slug": ct["slug"], "name": ct["name"],
                         "lat": ct["lat"], "lon": ct["lon"]}
                        for ct in r.get("cities", [])
                    ],
                }
                for r in c.get("regions", [])
            ],
        }
    return graph


# ── build ─────────────────────────────────────────────────────────────────

def provenance(*used):
    """The datasets that produced ONE output file.

    THE CREDIT WAS ATTACHED TO THE PIPELINE, NOT TO THE DRAWING. Every
    document in data/geo/ carried the same ten-row list — every .gz the
    fetcher had ever downloaded — so `geo.sources_line()` rendered a sixty-
    word sentence naming airports, ports, summits, marine polygons and river
    centrelines under a picture that is fifty country OUTLINES and nothing
    else. That is not verbose, it is WRONG: it credits datasets the drawing
    does not contain, on the family of pages whose whole argument is that a
    reader looking at a border is entitled to know which dataset drew it.

    This repository already has the rule, written for relief: the credit is
    attached to the drawing, never to the request. It had never been applied
    to the geometry files it was inherited from.

    `used` names the raw files this output actually reads. Empty means the
    whole register, which no caller now passes — a builder that adds a source
    and forgets this argument credits too little rather than too much, and
    too little is the failure a reader can see.
    """
    with open(os.path.join(ROOT, "docs", "data-licenses", "sources.json"),
              encoding="utf-8") as fh:
        reg = json.load(fh)
    want = {os.path.basename(u) for u in used}
    rows = []
    for s in reg["sources"]:
        if not s["path"].endswith(".gz"):
            continue
        if want and os.path.basename(s["path"]) not in want:
            continue
        rows.append({"dataset": s["dataset"], "licence": s["licence"],
                     "version": s["version"], "sha256": s["sha256"],
                     "fetched": s["fetched"]})
    if want and len(rows) != len(want):
        raise SystemExit(
            f"provenance(): {sorted(want - {os.path.basename(r['path']) for r in reg['sources']})} "
            f"is not in the licence register")
    return rows


# ── hydrology, seas and physical features ────────────────────────────────
#
# THE THREE THEMES THAT MAKE AN INLAND PLATE A PLACE. A country map built
# from coastlines and frontiers alone has nothing to show where there is no
# coast: measured on the rendered plates, Portugal and Greece read as
# geography and Paris and the Alpine Grand Tour read as empty parchment with
# dots on it. Rivers give an inland plate its structure, and named ranges let
# a reader see where the Alps are without any elevation model at all.
#
# THE SELECTION IS THE WHOLE JOB. Natural Earth ships 462 watercourses and
# 412 lakes at this scale; drawing them all is the OpenStreetMap default
# look. `scalerank` is the publisher's own judgement of the scale a feature
# belongs at, so using it is their editorial decision rather than one
# invented here.
# SCALERANK 6 IS THE WHOLE OF NATURAL EARTH'S RIVER SET, and it is the right
# cut here for a reason worth writing down: the Rhône, the Garonne, the Po
# and the Duero are rank 6, and a map of Europe without the Rhône is not
# restraint, it is an omission. The publisher's ranks are about how much of
# the WORLD a sheet shows; this atlas shows one continent, so the whole set
# clipped to the extent is about a hundred and thirty watercourses — an
# editorial number, not the four thousand an unfiltered OSM extract gives.
RIVER_RANK = 6
LAKE_RANK = 1       # 340 of 412 at this scale; the ones that shape a country
FEATURE_KINDS = ("Range/mtn", "Plateau", "Basin", "Plain", "Lowland",
                 "Foothills", "Valley", "Desert", "Tundra")


def _in_bbox(lon, lat, pad=6.0):
    return (BBOX[0] - pad <= lon <= BBOX[2] + pad
            and BBOX[1] - pad <= lat <= BBOX[3] + pad)


def _lines_of(geom):
    t = geom.get("type")
    if t == "LineString":
        return [geom["coordinates"]]
    if t == "MultiLineString":
        return geom["coordinates"]
    return []


def _rings_of(geom):
    t = geom.get("type")
    if t == "Polygon":
        return geom["coordinates"]
    if t == "MultiPolygon":
        return [r for poly in geom["coordinates"] for r in poly]
    return []


def hydrology():
    """Rivers and lakes, cut to the extent and simplified like the land."""
    rivers, lakes = [], []
    src = read_ne("ne_50m_rivers_lake_centerlines.geojson.gz")
    for feat in src["features"]:
        pr = feat.get("properties") or {}
        rank = pr.get("scalerank")
        if rank is None or rank > RIVER_RANK:
            continue
        for line in _lines_of(feat.get("geometry") or {}):
            pts = [(round(x, 3), round(y, 3)) for x, y in line
                   if _in_bbox(x, y)]
            if len(pts) < 2:
                continue
            pts = rdp(pts, 0.02)
            flat = [v for p in pts for v in p]
            rivers.append({"name": pr.get("name") or "", "rank": rank,
                           "line": flat})
    src = read_ne("ne_50m_lakes.geojson.gz")
    for feat in src["features"]:
        pr = feat.get("properties") or {}
        rank = pr.get("scalerank")
        if rank is None or rank > LAKE_RANK:
            continue
        rings = []
        for ring in _rings_of(feat.get("geometry") or {}):
            pts = [(round(x, 3), round(y, 3)) for x, y in ring
                   if _in_bbox(x, y)]
            if len(pts) < 4:
                continue
            pts = rdp(pts, 0.02)
            if len(pts) >= 4:
                rings.append([v for p in pts for v in p])
        if rings:
            lakes.append({"name": pr.get("name") or "", "rank": rank,
                          "rings": rings})
    return {"rivers": rivers, "lakes": lakes}


def _label_point(geom):
    """Where a name goes for an area, from the area itself.

    The mean of the largest ring's vertices rather than a bounding-box
    centre: the centre of the Alps' box is in Bavaria.
    """
    best = None
    for ring in _rings_of(geom):
        if best is None or len(ring) > len(best):
            best = ring
    if not best:
        return None
    xs = [p[0] for p in best]
    ys = [p[1] for p in best]
    return [round(sum(xs) / len(xs), 3), round(sum(ys) / len(ys), 3)]


def area_names(fname, kinds=None, upper=False):
    """One label point per named area, and nothing else.

    The geometry is read only to find WHERE the word goes. An area label is a
    name, not an outline, and drawing the edge of the Alps from a polygon
    somebody else generalised would be a claim about where they end.
    """
    out = []
    for feat in read_ne(fname)["features"]:
        pr = feat.get("properties") or {}
        name = (pr.get("name") or pr.get("NAME") or "").strip()
        kind = pr.get("featurecla") or pr.get("FEATURECLA") or ""
        if not name or (kinds and kind not in kinds):
            continue
        at = _label_point(feat.get("geometry") or {})
        if not at or not _in_bbox(at[0], at[1], pad=0.0):
            continue
        out.append({"name": name.upper() if upper else name,
                    "kind": kind, "at": at})
    return {"features": out}


def summits():
    """Named peaks with measured heights, inside the extent.

    NOT A TERRAIN LAYER AND NOT PRETENDING TO BE ONE. A hillshade needs an
    elevation model this repository does not have; what it does have, now,
    is 105 named summits with the height somebody else measured. A reader
    sees where the high ground is because the peaks cluster along the Alps,
    the Caucasus and the Pyrenees — which is how a printed physical atlas
    labels a mountain range, and it is the closest honest thing to relief
    that does not involve fitting a surface.

    The 1:50m file has THREE in the whole of Europe. This is 1:10m for that
    reason and no other.
    """
    out = []
    for feat in read_ne("ne_10m_geography_regions_elevation_points.geojson.gz")["features"]:
        pr = feat.get("properties") or {}
        name = (pr.get("name") or "").strip()
        elev = pr.get("elevation")
        if not name or elev is None or (pr.get("featurecla") or "") != "mountain":
            continue
        lon, lat = (feat.get("geometry") or {}).get("coordinates", [None, None])[:2]
        if lon is None or not _in_bbox(lon, lat, pad=0.0):
            continue
        out.append({"name": name, "m": int(elev),
                    "at": [round(lon, 3), round(lat, 3)]})
    out.sort(key=lambda x: -x["m"])
    return {"features": out}


def beyond():
    """Every landmass in the wider window, as one anonymous set of rings.

    NO COUNTRY IDENTITY, ON PURPOSE. The atlas's own files are keyed by
    country because a reader can click one; this is scenery. Giving it codes
    would invite a page to colour it, label it or link it, and the moment
    anything does, the extent of this product has quietly moved east.

    It is not deduplicated against the atlas either. Russia and Kazakhstan
    appear in both — clipped at 52 in one and running to 102 here — and the
    hero draws this layer UNDER the others, so the overlap is covered by the
    stronger treatment rather than seamed against it. Cutting a hole in this
    layer where the atlas sits would put a boundary between them, which is
    the one thing the drawing must not have: Europe is meant to be part of
    the same land, only lit.
    """
    # THE SAME SOURCE THE ATLAS IS DRAWN FROM, and the first version was not.
    # It read the 1:110m file, which is a different generalisation of the same
    # coastline: along every shore the atlas also draws — Anatolia, the Black
    # Sea, North Africa — the two disagreed by five or six drawn units, and
    # because this layer is graphite under parchment the disagreement showed
    # as a BLACK FRINGE outside the coast. Two levels of detail of the same
    # coast can be stacked only where one of them is hidden.
    ne = read_ne(LODS["lod1"]["src"])
    # KEPT PER STRIP, because each one fades in along a different edge. The
    # eastern strip cross-fades with the atlas along the 52°E meridian and the
    # southern one along the 33rd parallel; masked together by either alone,
    # the Sahara would disappear or the Urals would.
    strips = []
    for box in BEYOND_STRIPS:
        rings = []
        for f in ne["features"]:
            for r in rings_for(f, BEYOND_EPS, BEYOND_MINBOX, box=box):
                rings.append(flatten(r))
        rings.sort(key=len, reverse=True)
        strips.append({"box": list(box), "rings": rings})
    return {
        "$comment": "GENERATED by scripts/map/process.py. The land around "
                    "Europe, for the homepage hero only: no country identity, "
                    "no link, no label. See BEYOND_BBOX and BEYOND_STRIPS.",
        "bbox": list(BEYOND_BBOX),
        # The two edges this layer SHARES with the atlas, where the atlas's
        # own geometry stops and this takes over. They are inside the hero's
        # frame on purpose and each cross-fades with it; every other edge of
        # every strip must fall outside the frame, and checks.py asserts it.
        "seams": {"lon": BEYOND_STRIPS[0][0], "lat": BEYOND_STRIPS[1][3]},
        "strips": strips,
    }


def build():
    graph = load_graph()
    # ONE LIST PER FILE, NAMING WHAT THAT FILE IS MADE OF. See provenance().
    files = {"facts.json": facts(graph)}
    files["hydrology-lod1.json"] = dict(hydrology(), sources=provenance(
        "ne_50m_rivers_lake_centerlines.geojson.gz", "ne_50m_lakes.geojson.gz"))
    files["marine-lod1.json"] = dict(
        area_names("ne_50m_geography_marine_polys.geojson.gz", upper=True),
        sources=provenance("ne_50m_geography_marine_polys.geojson.gz"))
    files["summits-lod1.json"] = dict(summits(), sources=provenance(
        "ne_10m_geography_regions_elevation_points.geojson.gz"))
    # The ground beyond the atlas is drawn from the 1:50m admin-0 coastline,
    # the same file the atlas itself uses — see beyond().
    files[BEYOND] = dict(beyond(), sources=provenance(LODS["lod1"]["src"]))
    files["features-lod1.json"] = dict(
        area_names("ne_50m_geography_regions_polys.geojson.gz",
                   kinds=FEATURE_KINDS, upper=True),
        sources=provenance("ne_50m_geography_regions_polys.geojson.gz"))

    cache = {}
    for lod, cfg in LODS.items():
        if cfg["src"] not in cache:
            cache[cfg["src"]] = read_ne(cfg["src"])
        src = cache[cfg["src"]]
        # A country outline file is one dataset: the admin-0 countries at this
        # level of detail, and nothing else.
        prov = provenance(cfg["src"])

        shapes = {}
        for feat in src["features"]:
            props = feat.get("properties") or {}
            a3 = (props.get("ADM0_A3") or "").upper()
            code = key_for(props)
            ours = code in graph
            if not ours and a3 not in CONTEXT:
                continue
            rings = rings_for(feat, cfg["eps"], cfg["minbox"])
            if not rings:
                continue
            ident = code if ours else a3.lower()
            entry = shapes.setdefault(ident, {
                "name": graph[code]["name"] if ours else CONTEXT[a3],
                "slug": graph[code]["slug"] if ours else None,
                "atlas": ours,
                "rings": [],
            })
            entry["rings"].extend(flatten(r) for r in rings)

        for ident, entry in shapes.items():
            xs, ys = [], []
            for r in entry["rings"]:
                xs.extend(r[0::2])
                ys.extend(r[1::2])
            entry["bbox"] = [round(min(xs), 3), round(min(ys), 3),
                             round(max(xs), 3), round(max(ys), 3)]

        # Countries we hold a page for and Natural Earth has no polygon for at
        # this scale. At 1:50m that is Monaco (2 km2) and Vatican City
        # (0.44 km2); at 1:110m it is those two plus Andorra, Liechtenstein,
        # Malta and San Marino. The file names them so the renderer can draw
        # them as a point and say why, rather than the map quietly having six
        # fewer countries than the atlas and nobody noticing for a year.
        drawn = {i for i, e in shapes.items() if e["atlas"]}
        nogeom = {
            code: {"name": g["name"], "slug": g["slug"]}
            for code, g in graph.items() if code not in drawn
        }

        if lod in ("lod0", "lod1"):
            files[f"europe-{lod}.json"] = {
                "$comment": "GENERATED by scripts/map/process.py. Do not edit — "
                            "run the pipeline. Coordinates are WGS84 lon/lat, "
                            "flat pairs, 3 decimal places.",
                "lod": lod,
                "bbox": list(BBOX),
                "sources": prov,
                "countries": shapes,
                "nogeometry": nogeom,
            }
        else:
            for code, g in nogeom.items():
                # A country with no polygon still gets a file, so every
                # /europe/<slug> page has the same contract to read.
                files[os.path.join("country", g["slug"] + ".json")] = {
                    "$comment": "GENERATED by scripts/map/process.py. Do not edit.",
                    "lod": "lod2",
                    "country": code,
                    "bbox": None,
                    "sources": prov,
                    "countries": {},
                    "nogeometry": {code: g},
                }
            for ident, entry in shapes.items():
                if not entry["atlas"]:
                    continue
                slug = entry["slug"]
                near = {
                    o: {"name": v["name"], "slug": v["slug"], "atlas": v["atlas"],
                        "rings": v["rings"], "bbox": v["bbox"]}
                    for o, v in shapes.items()
                    if o != ident and _touches(entry["bbox"], v["bbox"])
                }
                files[os.path.join("country", slug + ".json")] = {
                    "$comment": "GENERATED by scripts/map/process.py. Do not edit.",
                    "lod": "lod2",
                    "country": ident,
                    "bbox": entry["bbox"],
                    "sources": prov,
                    "countries": dict({ident: entry}, **near),
                    "nogeometry": {
                        c: g for c, g in nogeom.items()
                        if _touches(entry["bbox"], _pt_box(graph[c]))
                    },
                }
    return files


def _pt_box(entry):
    """A degenerate bbox at a country's first destination, so a country with
    no polygon can still be placed on a neighbour's map. Monaco appears on
    France's; Vatican City on Italy's."""
    for r in entry["regions"]:
        for c in r["cities"]:
            return [c["lon"], c["lat"], c["lon"], c["lat"]]
    return [999.0, 999.0, 999.0, 999.0]


def _touches(a, b, pad=0.75):
    """Does bbox b come within `pad` degrees of bbox a?

    A country page that draws only that country floats it in white space and
    loses the thing a map is for. Neighbours are drawn as context so Slovenia
    is between Austria and Croatia rather than nowhere.
    """
    return not (b[2] < a[0] - pad or b[0] > a[2] + pad or
                b[3] < a[1] - pad or b[1] > a[3] + pad)


# ── derived facts ────────────────────────────────────────────────────────
#
# The Build Package schema asks countries for iso3, latitude, longitude and
# population, and cities for population and a type. Every one of those is a
# MEASUREMENT, not an editorial judgement, and this repository already has a
# rule about the difference: a field a person can type is a field somebody
# will type the wrong thing into. So none of them is authored. They are
# derived here from the public-domain Natural Earth files already committed
# under data/raw/, written into data/geo/facts.json with the dataset that
# produced each one, and merged at load time. The validator refuses them as
# authored keys.
#
# What is deliberately NOT derived: anything the source does not actually
# know. Natural Earth lists 157 of our 319 destinations; the other 162 are
# villages, valleys and monuments — Theth, Xınalıq, Madriu-Perafita-Claror —
# and that is not a coverage failure, it is the product. Those rows are
# absent rather than estimated, and content-report.py counts them.

FEATURE_TO_TYPE = {
    "Admin-0 capital": "capital",
    "Admin-0 capital alt": "capital",
    "Admin-1 capital": "city",
    "Admin-1 region capital": "city",
    "Admin-0 region capital": "city",
    "Historic place": "site",
}

# Bands for a plain populated place. Natural Earth's POP_MAX is a metropolitan
# figure, so these are deliberately generous: the point is to tell a city from
# a village, not to rank them.
def _type_from(feature, pop):
    t = FEATURE_TO_TYPE.get(feature)
    if t:
        return t
    if pop is None:
        return None
    if pop >= 100_000:
        return "city"
    if pop >= 10_000:
        return "town"
    return "village"


def _fold(s):
    """Strip accents and punctuation for name matching.

    Ålesund/Alesund, Gjirokastër/Gjirokaster, Xınalıq/Xinaliq — the dataset
    and our editors do not agree about diacritics and there is no reason they
    should."""
    out = unicodedata.normalize("NFKD", s or "")
    out = out.encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in out if ch.isalnum())


def _km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def facts(graph):
    """Country and destination facts, each carrying the dataset it came from."""
    admin = read_ne("ne_50m_admin_0_countries.geojson.gz")
    countries = {}
    for feat in admin["features"]:
        props = feat.get("properties") or {}
        code = key_for(props)
        if code not in graph:
            continue
        iso3 = props.get("ISO_A3_EH") or props.get("ADM0_A3") or ""
        row = {"source": "Natural Earth 1:50m admin 0 countries"}
        if iso3 and iso3 != "-99":
            row["iso3"] = iso3
        elif code in ISO3_USER_ASSIGNED:
            # Kosovo. ISO 3166 has assigned it no code at all, so there is
            # nothing to look up and nothing to derive — XKX is the
            # user-assigned code in common use, exactly as XK is the alpha-2
            # this repository already uses as Kosovo's country key. Recording
            # it with the note attached is the same decision as that one, and
            # docs/boundary-policy.md says why it is an identifier join rather
            # than a recognition claim. Silently omitting the field would
            # have read as a data gap; silently filling it would have read as
            # an ISO assignment.
            row["iso3"] = ISO3_USER_ASSIGNED[code]
            row["iso3_note"] = ("user-assigned; ISO 3166 has assigned no alpha-3 "
                                "code. See docs/boundary-policy.md")
        # LABEL_X/LABEL_Y is the cartographer's label anchor, not a centroid.
        # It is the better number by a distance: the centroid of Norway is in
        # Sweden and the centroid of Croatia is in Bosnia, because a centroid
        # knows nothing about the shape it sits in.
        if props.get("LABEL_X") is not None:
            row["lat"] = round(float(props["LABEL_Y"]), 4)
            row["lon"] = round(float(props["LABEL_X"]), 4)
        if props.get("POP_EST"):
            row["population"] = int(props["POP_EST"])
            row["population_year"] = int(props.get("POP_YEAR") or 0) or None
        countries[code] = row

    with gzip.open(os.path.join(RAW, "ne_10m_populated_places.geojson.gz"),
                   "rt", encoding="utf-8") as fh:
        pp = json.load(fh)
    index = []
    for feat in pp["features"]:
        q = feat.get("properties") or {}
        lat, lon = q.get("LATITUDE"), q.get("LONGITUDE")
        if lat is None or lon is None:
            continue
        if not (BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]):
            continue
        index.append((
            (q.get("ISO_A2") or "").lower(),
            _fold(q.get("NAME_EN") or q.get("NAME")), _fold(q.get("NAME")),
            float(lat), float(lon), q.get("POP_MAX"), q.get("FEATURECLA"),
        ))

    dests = {}
    for code, c in graph.items():
        for r in c["regions"]:
            for t in r["cities"]:
                want = _fold(t["name"])
                best = None
                for iso, en, nat, la, lo, pop, fc in index:
                    if iso != code:
                        continue
                    # Both tests must pass: within 25 km AND the name agrees.
                    # Distance alone matches the wrong village in the next
                    # valley; the name alone matches a Springfield anywhere.
                    d = _km(t["lat"], t["lon"], la, lo)
                    if d > 25.0:
                        continue
                    if not (want in (en, nat) or want.startswith(en) or en.startswith(want)):
                        continue
                    if best is None or d < best[0]:
                        best = (d, pop, fc)
                if best is None:
                    continue
                _d, pop, fc = best
                row = {"source": "Natural Earth 1:10m populated places",
                       "match_km": round(_d, 1)}
                if pop:
                    row["population"] = int(pop)
                kind = _type_from(fc, pop)
                if kind:
                    row["city_type"] = kind
                dests[f'{c["slug"]}/{r["slug"]}/{t["slug"]}'] = row
    return {
        "$comment": "GENERATED by scripts/map/process.py from the public-domain "
                    "Natural Earth files in data/raw/. Do not edit and do not copy "
                    "these values into data/countries/*.json — the validator refuses "
                    "them there, because a derived fact that can be typed is a "
                    "derived fact that will be typed wrong.",
        "countries": countries,
        "destinations": dests,
        "transport": transport(graph),
    }


# ── §2.11, the half of it that can be sourced ────────────────────────────
#
# The Build Package asks for transport_nodes AND transport_routes. The nodes
# are geography: an airport is at a fixed place and Natural Earth publishes
# 893 of them in the public domain. The routes are not: an operator, a
# frequency, a duration and a fare need a licensed feed, change without
# notice, and are the single most damaging thing a travel page can get wrong.
#
# So the nodes are built and the routes are refused, which is the honest half
# and is also the useful half: what a destination page needs to answer is
# "how do I get near here", not "what time is the 14:05".
NODE_KINDS = {"airport": 120.0, "port": 60.0}


def transport(graph):
    nodes = []
    for fn, kind, namekey in (("ne_10m_airports.geojson.gz", "airport", "name"),
                              ("ne_10m_ports.geojson.gz", "port", "name")):
        with gzip.open(os.path.join(RAW, fn), "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
        for feat in doc["features"]:
            q = feat.get("properties") or {}
            g = feat.get("geometry") or {}
            if g.get("type") != "Point":
                continue
            lon, lat = g["coordinates"][0], g["coordinates"][1]
            if not (BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]):
                continue
            name = q.get("name_en") or q.get(namekey)
            if not name:
                continue
            row = {"name": name, "kind": kind,
                   "lat": round(float(lat), 4), "lon": round(float(lon), 4)}
            if q.get("iata_code"):
                row["iata"] = q["iata_code"]
            nodes.append(row)

    # Attach each destination to the nodes within reach of it, nearest first.
    # A radius rather than a count, because "the nearest airport" to Theth is
    # 90 km away over a mountain and "the nearest airport" to Amsterdam is
    # nine kilometres, and a fixed top-3 would present those as equivalent.
    out = {}
    for code, c in graph.items():
        for r in c["regions"]:
            for t in r["cities"]:
                near = []
                for nd in nodes:
                    d = _km(t["lat"], t["lon"], nd["lat"], nd["lon"])
                    if d <= NODE_KINDS[nd["kind"]]:
                        near.append(dict(nd, km=round(d)))
                near.sort(key=lambda n: n["km"])
                if near:
                    out[f'{c["slug"]}/{r["slug"]}/{t["slug"]}'] = {
                        "source": "Natural Earth 1:10m airports and ports",
                        "nodes": near[:4],
                    }
    return out


TERRAIN = "terrain-lod1.json"


def terrain_places(graph):
    """[(key, lon, lat)] for every destination, keyed as facts.json keys it."""
    out = []
    for c in graph.values():
        for r in c.get("regions", []):
            for t in r.get("cities", []):
                out.append((f'{c["slug"]}/{r["slug"]}/{t["slug"]}',
                            t["lon"], t["lat"]))
    return sorted(out)


def terrain_doc():
    """The expensive one, kept out of build() on purpose — see relief.fingerprint."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import relief
    W, H, g = relief.field()
    doc, _stats = relief.document(W, H, g, terrain_places(load_graph()))
    return doc


def terrain_is_current():
    """Cheap staleness: the fingerprint on disk against the one now."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import relief
    path = os.path.join(OUT, TERRAIN)
    if not os.path.exists(path):
        return False, f"{TERRAIN} is missing"
    with open(path, encoding="utf-8") as fh:
        try:
            have = json.load(fh).get("pipeline")
        except ValueError:
            return False, f"{TERRAIN} is not valid JSON"
    want = relief.fingerprint()
    if have != want:
        diff = sorted(k for k in set(list(have or {}) + list(want))
                      if (have or {}).get(k) != want.get(k))
        return False, f"{TERRAIN} was built from different inputs: {', '.join(diff)}"
    return True, f"{TERRAIN} matches its inputs"


def dump(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n"


def main(argv):
    check = "--check" in argv
    files = build()

    if check:
        ok, why = terrain_is_current()
        if not ok:
            print("data/geo/ is stale — run: python3 scripts/map/process.py")
            print("  " + why)
            return 1
        stale = []
        for rel, obj in files.items():
            path = os.path.join(OUT, rel)
            if not os.path.exists(path):
                stale.append(rel + " (missing)")
                continue
            with open(path, encoding="utf-8") as fh:
                if fh.read() != dump(obj):
                    stale.append(rel)
        have = set()
        for root, _dirs, names in os.walk(OUT):
            for n in names:
                if n.endswith(".json"):
                    have.add(os.path.relpath(os.path.join(root, n), OUT))
        for extra in sorted(have - set(files) - {TERRAIN}):
            stale.append(extra + " (not produced by the pipeline)")
        if stale:
            print("data/geo/ is stale — run: python3 scripts/map/process.py")
            for s in sorted(stale):
                print("  " + s)
            return 1
        print(f"data/geo/ matches the pipeline: {len(files) + 1} files "
              f"({why})")
        return 0

    # THE TERRAIN FILE IS REGENERATED HERE AND NOWHERE ELSE, and it is not in
    # `files` because build() is called by checks.py on every run. Decoding
    # 182 PNGs and smoothing twelve million cells takes about a minute; the
    # static suite takes seventeen seconds, and a gate that takes a minute is
    # a gate people stop running. Its staleness is guarded by a fingerprint
    # of every input byte, every parameter and this pipeline's own source —
    # see relief.fingerprint() for why that is not the weaker contract it
    # looks like.
    ok, why = terrain_is_current()
    if ok and "--force" not in argv:
        print(f"  {TERRAIN} is already current ({why}) — pass --force to rebuild")
    else:
        doc = terrain_doc()
        with open(os.path.join(OUT, TERRAIN), "w", encoding="utf-8") as fh:
            fh.write(dump(doc))
        n = sum(len(b["rings"]) for b in doc["bands"])
        print(f"  {TERRAIN:<20} {n:>5,} rings  "
              f"{len(doc['relief']):>4} places measured  "
              f"{len(dump(doc)):>9,} bytes")

    total = 0
    for rel, obj in files.items():
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = dump(obj)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        total += len(body)
    print(f"wrote {len(files)} files, {total:,} bytes into data/geo/")
    nb = sum(len(r) // 2 for st in files[BEYOND]["strips"] for r in st["rings"])
    nr = sum(len(st["rings"]) for st in files[BEYOND]["strips"])
    print(f"  {BEYOND:<20} {nr:>3} rings   {nb:>6,} points  "
          f"{len(dump(files[BEYOND])):>8,} bytes")
    for rel in ("europe-lod0.json", "europe-lod1.json"):
        n = sum(len(r) // 2 for c in files[rel]["countries"].values() for r in c["rings"])
        print(f"  {rel:<20} {len(files[rel]['countries']):>3} shapes  {n:>6,} points  "
              f"{len(dump(files[rel])):>8,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
