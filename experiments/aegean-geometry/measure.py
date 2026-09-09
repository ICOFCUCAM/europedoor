#!/usr/bin/env python3
"""Measure BOTH sides of the Aegean geometry experiment with the same code.

    python3 experiments/aegean-geometry/measure.py
    python3 experiments/aegean-geometry/measure.py --json   just the JSON path

Reads nothing but files already committed to this repository plus, IF a human
has put one there, an OSM-derived side under experiments/aegean-geometry/osm/.
Writes exactly one file: results.json next to this script. It touches nothing
in data/, site/, tools/ or scripts/.

## Why the same code for both sides

The question is whether authoritative geometry improves the map at the zoom
levels users actually see. That is a comparison, and a comparison run through
two different measuring instruments measures the instruments. So every figure
here — vertices, area, perimeter, compactness, emitted path bytes — is
produced by ONE function that takes a list of rings and does not know or care
where they came from. The Natural Earth side and the OSM side differ in
exactly one thing: the file the rings were read out of.

## Why it does not import the constants it depends on

The zoom levels, the simplification tolerance, the ring-drop floor and the
stroke width all live in production code and CSS. Retyping them here would
produce an experiment that keeps reporting the right answer about a system
that has moved. So they are PARSED OUT OF THE SOURCE FILES, and a parse that
fails stops the script with the file and the pattern named, rather than
falling back to a remembered value. `tools/lib/pages.py` is 5,600 lines and
imports the whole data layer; parsing four constants out of it is cheaper and
more honest than importing it, and it fails loudly when somebody moves one.

`geo` IS imported, because the projection is the thing under test and there
must be exactly one of it.

## What it deliberately does not do

It does not download anything, it does not estimate what OSM would say, and
it does not fill an OSM cell with a plausible number. Every OSM-side figure is
"—" until osm/ holds a file. `docs/data-licenses/openstreetmap-not-used.md`
records why that directory is empty, and the licence question is a human's to
settle before it stops being.
"""

import argparse
import gzip
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from lib import geo                                          # noqa: E402

OSM_DIR = os.path.join(HERE, "osm")
RESULTS = os.path.join(HERE, "results.json")

# THE TEST AREA. Chosen because it is where the current geometry visibly
# fails, not because it is convenient: it holds Santorini, Naxos, Paros and
# Milos — four destinations the atlas publishes a page for — and the north
# coast of Crete, which is a long generalised shoreline rather than a small
# ring, so the two failure modes (a blob and a smoothed coast) are both in
# frame. Athens is inside the northern edge on purpose: it is the one place
# in the box drawn from a large mainland ring, and it is the control.
BBOX = (23.0, 34.8, 26.6, 38.1)          # lon0, lat0, lon1, lat1

# The islands the experiment is named for. Matched to atlas destinations by
# slug, so a renamed destination fails visibly rather than silently dropping
# a row.
NAMED = ("santorini", "naxos", "paros", "milos")

# Rendered widths of a destination minimap, in CSS pixels, derived from the
# tokens in assets/css/europedoor.css:
#
#   --page 76rem = 1216px, main padding var(--s5) = 24px each side,
#   .minimap padding var(--s4) = 16px each side
#     -> 1216 - 48 - 32 = 1136 for .placeband.maponly (no photograph: the
#        map takes the full column, which is the case on every destination
#        page today because zero photographs are licensed)
#     -> the 7fr of a 5fr/7fr grid, less the var(--s4) gap, for the paired
#        case that arrives with the first licensed photograph
#     -> a 390px phone viewport, same two paddings
#
# UNVERIFIED: derived from tokens, not measured in a browser. The instrument
# that could settle it is tools/browser-checks.js, which already measures box
# geometry in Chromium — and the repository's own history says to trust that
# over arithmetic: the --thumbbar offsets were 44px in the code and 63px on
# the screen, and only measuring both boxes found it.
CSS_WIDTHS = {
    "desktop_maponly": 1136.0,
    "desktop_paired": 653.0,
    "phone_390": 310.0,
}


# ── reading the constants out of production code ──────────────────────────

def _grab(path, pattern, what, count=1):
    """Pull a constant out of a source file, or stop.

    Stopping is the point. An experiment that silently falls back to a
    remembered value keeps agreeing with itself after production has moved,
    which is the failure this whole directory is supposed to avoid.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(
            f"measure.py: could not read {what} from {os.path.relpath(path, ROOT)}\n"
            f"  pattern: {pattern}\n"
            f"  The constant moved or was renamed. Fix the pattern rather than\n"
            f"  typing the value in here — a hard-coded copy is how this script\n"
            f"  would start measuring a map that no longer exists.")
    return m.groups() if count > 1 else m.group(1)


def constants():
    pages = os.path.join(ROOT, "tools", "lib", "pages.py")
    process = os.path.join(ROOT, "scripts", "map", "process.py")
    css = os.path.join(ROOT, "assets", "css", "europedoor.css")

    mw, mh = _grab(pages, r"MAP_W,\s*MAP_H\s*=\s*(\d+),\s*(\d+)",
                   "MAP_W/MAP_H", count=2)
    lon0, lon1, lat0, lat1 = _grab(
        pages, r"LON0,\s*LON1,\s*LAT0,\s*LAT1\s*=\s*"
               r"(-?[\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+)",
        "the map extent", count=4)
    ladder = _grab(pages, r"for cand in \(([^)]*)\):\s*\n\s*near = sum",
                   "the minimap span ladder")
    mini_w, mini_h = _grab(pages, r"cx, cy = project\(t\[\"lat\"\], t\[\"lon\"\]\)\s*\n"
                                  r"\s*w, h = (\d+), (\d+)",
                           "the minimap viewBox", count=2)
    near_min = _grab(pages, r"if near >= (\d+):", "the minimap company threshold")
    span_floor = _grab(pages, r"pts = \[project.*\n\s*span = ([\d.]+)",
                       "the minimap fallback span")
    lod1 = _grab(process, r'"lod1":\s*\{[^}]*"eps":\s*([\d.]+)', "lod1 eps")
    lod1_min = _grab(process, r'"lod1":\s*\{[^}]*"minbox":\s*([\d.]+)', "lod1 minbox")
    lod2 = _grab(process, r'"lod2":\s*\{[^}]*"eps":\s*([\d.]+)', "lod2 eps")
    lod2_min = _grab(process, r'"lod2":\s*\{[^}]*"minbox":\s*([\d.]+)', "lod2 minbox")
    stroke = _grab(css, r"\.minimap\.arched \.countries path \{ stroke: [^;]+; "
                        r"stroke-width: ([\d.]+)",
                   "the minimap coastline stroke width")

    return {
        "map_w": int(mw), "map_h": int(mh),
        "extent": [float(lon0), float(lat0), float(lon1), float(lat1)],
        "minimap_view": [int(mini_w), int(mini_h)],
        "span_ladder": [float(x) for x in ladder.replace(" ", "").split(",") if x],
        "span_floor": float(span_floor),
        "near_min": int(near_min),
        "lod1_eps_deg": float(lod1), "lod1_minbox_deg2": float(lod1_min),
        "lod2_eps_deg": float(lod2), "lod2_minbox_deg2": float(lod2_min),
        "stroke_px": float(stroke),
    }


# ── the atlas ─────────────────────────────────────────────────────────────

def destinations():
    out = []
    d = os.path.join(ROOT, "data", "countries")
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(d, name), encoding="utf-8") as fh:
            c = json.load(fh)
        for r in c.get("regions", []):
            for t in r.get("cities", []):
                out.append({
                    "slug": t["slug"], "name": t["name"],
                    "country": c["slug"], "region": r["slug"],
                    "lat": t["lat"], "lon": t["lon"],
                    "city_type": t.get("city_type"),
                })
    return out


def in_bbox_pt(lon, lat, box=BBOX):
    return box[0] <= lon <= box[2] and box[1] <= lat <= box[3]


# ── the two sides ─────────────────────────────────────────────────────────

def _ring_pairs(flat):
    return list(zip(flat[0::2], flat[1::2]))


def side_natural_earth():
    """Rings the site actually draws under a destination minimap.

    europe-lod1.json, because that is what geo.landmass() loads when no doc
    is passed and minimap() passes none. The country file (lod2) is a
    different, finer set and is measured separately — a reader on a
    destination page never sees it.
    """
    doc = geo.load("europe-lod1.json")
    if not doc:
        raise SystemExit("measure.py: data/geo/europe-lod1.json is missing. "
                         "Run scripts/map/process.py first.")
    rings = []
    for ident, ent in sorted(doc["countries"].items()):
        for flat in ent["rings"]:
            rings.append({"owner": ident, "pts": _ring_pairs(flat)})
    return rings


def side_natural_earth_lod2():
    doc = geo.country("greece")
    if not doc:
        return []
    rings = []
    for ident, ent in sorted(doc["countries"].items()):
        for flat in ent["rings"]:
            rings.append({"owner": ident, "pts": _ring_pairs(flat)})
    return rings


def side_raw_ne50m():
    """The unprocessed 1:50m source, so the pipeline's own losses are visible.

    This is the only way to answer "how many islands did the ring-drop floor
    take out" without a second dataset: the floor's input is committed.
    """
    path = os.path.join(ROOT, "data", "raw", "ne_50m_admin_0_countries.geojson.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        src = json.load(fh)
    rings = []
    for feat in src["features"]:
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        if geom.get("type") == "MultiPolygon":
            polys = geom["coordinates"]
        elif geom.get("type") == "Polygon":
            polys = [geom["coordinates"]]
        else:
            continue
        for poly in polys:
            rings.append({"owner": (props.get("ADM0_A3") or "").lower(),
                          "pts": [(float(x), float(y)) for x, y in poly[0]]})
    return rings


def side_osm():
    """The authoritative side — empty until a human settles the licence.

    Accepts any *.geojson or *.geojson.gz in experiments/aegean-geometry/osm/
    holding Polygon or MultiPolygon features. Returns None (not []) when the
    directory is empty, because "no data" and "data with no islands in it"
    are different answers and only one of them is a finding.
    """
    if not os.path.isdir(OSM_DIR):
        return None
    files = sorted(f for f in os.listdir(OSM_DIR)
                   if f.endswith(".geojson") or f.endswith(".geojson.gz"))
    if not files:
        return None
    rings = []
    for name in files:
        path = os.path.join(OSM_DIR, name)
        opener = gzip.open if name.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
        feats = doc.get("features", [doc]) if doc.get("type") != "Feature" else [doc]
        for feat in feats:
            geom = feat.get("geometry") or feat
            if geom.get("type") == "MultiPolygon":
                polys = geom["coordinates"]
            elif geom.get("type") == "Polygon":
                polys = [geom["coordinates"]]
            else:
                continue
            for poly in polys:
                rings.append({"owner": name,
                              "pts": [(float(x), float(y)) for x, y in poly[0]]})
    return rings


# ── geometry, identical for both sides ────────────────────────────────────

R_EARTH = 6371.0088


def bbox_of(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def touches(pts, box=BBOX):
    x0, y0, x1, y1 = bbox_of(pts)
    return not (x1 < box[0] or x0 > box[2] or y1 < box[1] or y0 > box[3])


def plane_of(pts):
    """The local kilometre plane a ring is measured in.

    A local tangent plane about the ring's own centre. At island scale — the
    largest thing measured here is Crete at about 250 km across — the error
    against a proper geodesic area is well under a percent, and the figure
    that matters is a RATIO between two sides measured the same way. Stated
    rather than hidden: this is not a geodesic area and must not be quoted as
    one.

    Returned rather than applied, because a point being tested against a ring
    has to land in that ring's plane and not in its own.
    """
    x0, y0, x1, y1 = bbox_of(pts)
    latm = (y0 + y1) / 2.0
    return x0, y0, 111.320 * math.cos(math.radians(latm)), 110.574


def km_xy(pts, plane=None):
    x0, y0, kx, ky = plane or plane_of(pts)
    return [((x - x0) * kx, (y - y0) * ky) for x, y in pts]


def closed(pts):
    """GeoJSON rings repeat their first point. Both sides will, so the count
    that means anything is the count of CORNERS.

    Santorini's ring is four numbers long and draws a triangle. Reporting
    "4 vertices" would understate the defect by exactly one.
    """
    return len(pts) > 1 and pts[0] == pts[-1]


def corners(pts):
    return len(pts) - 1 if closed(pts) else len(pts)


def area_km2(pts):
    p = km_xy(pts)
    s = 0.0
    for i in range(len(p)):
        x0, y0 = p[i]
        x1, y1 = p[(i + 1) % len(p)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def perimeter_km(pts):
    p = km_xy(pts)
    return sum(math.dist(p[i], p[(i + 1) % len(p)]) for i in range(len(p)))


def compactness(pts):
    """4*pi*A / P^2. A circle is 1.0; a square 0.785; a thin sliver -> 0.

    This is the number that separates a blob from an island. A four-sided
    ring standing in for Santorini scores like a quadrilateral because that
    is what it is; the real caldera rim is a crescent and scores far lower.
    A single figure per island, comparable across the two sides, and it
    cannot be gamed by scale.
    """
    per = perimeter_km(pts)
    if per <= 0:
        return 0.0
    return 4.0 * math.pi * area_km2(pts) / (per * per)


def point_in_ring(pt, pts):
    x, y = pt
    inside = False
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            dy = (y1 - y0) or 1e-15
            if x < (x1 - x0) * (y - y0) / dy + x0:
                inside = not inside
    return inside


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    if den == 0.0:
        return math.dist(p, a)
    t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / den
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.dist(p, (ax + t * dx, ay + t * dy))


def ring_dist_km(pt, pts):
    """Kilometres from a point to the nearest edge of a ring. 0 if inside."""
    if point_in_ring(pt, pts):
        return 0.0
    plane = plane_of(pts)
    q = km_xy([pt], plane)[0]
    p = km_xy(pts, plane)
    return min(_seg_dist(q, p[i], p[(i + 1) % len(p)]) for i in range(len(p)))


def ring_for(dest, rings):
    """The ring that draws a destination's land, and whether the dot is on it.

    CONTAINMENT FIRST, NEAREST SECOND — and the first version of this did
    neither. It took the smallest ring whose BOUNDING BOX held the point,
    which assigned Athens to Euboea: a bounding box that contains a point is
    not a polygon that contains it, and on a generalised coast the two
    disagree constantly. That is the whole defect under test, so the
    instrument may not depend on the two agreeing.

    When nothing contains the point the nearest ring is returned WITH its
    distance, because "0.9 km offshore because the coast was smoothed" and
    "25 km away because this island is not in the dataset at all" are two
    different findings and a boolean cannot tell them apart.
    """
    pt = (dest["lon"], dest["lat"])
    for r in rings:
        if point_in_ring(pt, r["pts"]):
            return r, True, 0.0
    if not rings:
        return None, False, None
    best = min(rings, key=lambda r: ring_dist_km(pt, r["pts"]))
    return best, False, round(ring_dist_km(pt, best["pts"]), 2)


# ── the zoom the reader actually sees ─────────────────────────────────────

def spans(proj, dests, C):
    """Reproduce minimap()'s span="auto" ladder for every destination.

    Not approximated: the same candidates, the same half-frame test, the same
    threshold, the same fallback. The ladder is a function of where every
    OTHER destination is, so it needs all 319 — which is why this walks the
    whole atlas to report on twenty-five places.
    """
    w, h = C["minimap_view"]
    pts = [proj.xy(d["lat"], d["lon"]) for d in dests]
    out = {}
    for d in dests:
        cx, cy = proj.xy(d["lat"], d["lon"])
        span = C["span_floor"]
        for cand in C["span_ladder"]:
            near = sum(1 for x, y in pts
                       if abs(x - cx) <= w / 2 / cand and abs(y - cy) <= h / 2 / cand)
            if near >= C["near_min"]:
                span = cand
                break
        kmu = geo.km_per_unit(proj, d["lat"], d["lon"])
        out[d["slug"]] = {
            "span": span,
            "km_per_projection_unit": round(kmu, 4),
            "km_per_rendered_unit": round(kmu / span, 4),
            "frame_km_w": int(round(w / span * kmu / 10) * 10),
            "frame_km_h": int(round(h / span * kmu / 10) * 10),
        }
    return out


def visibility(C, km_per_rendered_unit):
    """What one drawn line is worth, on the ground, at each rendered width.

    The coastline stroke is `vector-effect: non-scaling-stroke`, so it is
    1.1 CSS pixels wide however far the geometry is magnified. That makes it
    the natural unit of "visible": a difference smaller than the line drawn
    to represent it is not a difference the reader can see, whatever the
    arithmetic says about the data.
    """
    vw = C["minimap_view"][0]
    out = {}
    for name, css_px in CSS_WIDTHS.items():
        px_per_unit = css_px / vw
        km_per_css_px = km_per_rendered_unit / px_per_unit
        out[name] = {
            "css_px": css_px,
            "css_px_per_rendered_unit": round(px_per_unit, 4),
            "km_per_css_px": round(km_per_css_px, 4),
            "km_per_stroke_width": round(km_per_css_px * C["stroke_px"], 4),
        }
    return out


# ── bytes ─────────────────────────────────────────────────────────────────

def path_bytes(proj, rings):
    """Bytes of SVG `d` text, from the site's own emitter.

    geo.Projection.path() — one decimal place, consecutive duplicate pixels
    dropped — so this is the number a page would actually carry, not an
    estimate of it.
    """
    total = 0
    drawn = 0
    for r in rings:
        d = proj.path([c for p in r["pts"] for c in p])
        if d:
            total += len(d.encode())
            drawn += 1
    return total, drawn


# ── the report ────────────────────────────────────────────────────────────

def dash(v, fmt="{}"):
    return "—" if v is None else fmt.format(v)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true",
                    help="print the results path and nothing else")
    args = ap.parse_args(argv[1:])

    C = constants()
    lon0, lat0, lon1, lat1 = C["extent"]
    proj = geo.Projection((lon0, lat0, lon1, lat1),
                          C["map_w"], C["map_h"], pad=0.0)

    dests = destinations()
    box_dests = [d for d in dests if in_bbox_pt(d["lon"], d["lat"])]
    span_by_slug = spans(proj, dests, C)

    ne = side_natural_earth()
    ne2 = side_natural_earth_lod2()
    raw = side_raw_ne50m()
    osm = side_osm()

    ne_box = [r for r in ne if touches(r["pts"])]
    ne2_box = [r for r in ne2 if touches(r["pts"])]
    raw_box = [r for r in raw if touches(r["pts"])]
    osm_box = None if osm is None else [r for r in osm if touches(r["pts"])]

    res = {
        "$comment": "GENERATED by experiments/aegean-geometry/measure.py. "
                    "Every OSM-side value is null until osm/ holds a file; a "
                    "null here means 'not measured', never 'zero'.",
        "bbox": list(BBOX),
        "constants_read_from_source": C,
        "osm_side_present": osm is not None,
    }

    # ── 1. the zoom levels that matter ────────────────────────────────
    rows = [(d["name"], span_by_slug[d["slug"]]) for d in box_dests]
    rows.sort(key=lambda r: -r[1]["span"])
    ladder_counts = {}
    for _n, s in rows:
        ladder_counts[s["span"]] = ladder_counts.get(s["span"], 0) + 1
    res["zoom"] = {
        "destinations_in_bbox": len(box_dests),
        "span_histogram": {str(k): v for k, v in sorted(ladder_counts.items())},
        "per_destination": {d["slug"]: span_by_slug[d["slug"]] for d in box_dests},
    }
    # The dominant span is the zoom the question is about.
    dominant = max(ladder_counts.items(), key=lambda kv: kv[1])[0]
    kmu_dom = sum(s["km_per_rendered_unit"] for _n, s in rows
                  if s["span"] == dominant) / max(1, ladder_counts[dominant])
    res["zoom"]["dominant_span"] = dominant
    res["zoom"]["dominant_km_per_rendered_unit"] = round(kmu_dom, 4)
    res["zoom"]["visibility"] = visibility(C, kmu_dom)
    # The simplification tolerance expressed in the units the reader sees.
    lat_mid = (BBOX[1] + BBOX[3]) / 2.0
    eps_km_lat = C["lod1_eps_deg"] * 110.574
    eps_km_lon = C["lod1_eps_deg"] * 111.320 * math.cos(math.radians(lat_mid))
    res["zoom"]["lod1_tolerance_km"] = {"along_meridian": round(eps_km_lat, 3),
                                        "along_parallel": round(eps_km_lon, 3)}
    strokes = {k: round(eps_km_lat / v["km_per_stroke_width"], 2)
               for k, v in res["zoom"]["visibility"].items()}
    res["zoom"]["lod1_tolerance_in_stroke_widths"] = strokes

    # ── 2. capture and drop ───────────────────────────────────────────
    def dropped(rings, minbox):
        n = 0
        for r in rings:
            x0, y0, x1, y1 = bbox_of(r["pts"])
            if (x1 - x0) * (y1 - y0) < minbox:
                n += 1
        return n
    lat_scale = 110.574
    lon_scale = 111.320 * math.cos(math.radians(lat_mid))
    res["capture"] = {
        "raw_ne50m_rings_in_bbox": len(raw_box),
        "raw_rings_below_lod1_floor": dropped(raw_box, C["lod1_minbox_deg2"]),
        "raw_rings_below_lod2_floor": dropped(raw_box, C["lod2_minbox_deg2"]),
        "lod1_rings_in_bbox": len(ne_box),
        "lod2_rings_in_bbox": len(ne2_box),
        "osm_rings_in_bbox": None if osm_box is None else len(osm_box),
        "islands_absent_from_current_data": None,   # needs the authoritative side
        "lod1_floor_bbox_km2_at_this_latitude":
            round(C["lod1_minbox_deg2"] * lat_scale * lon_scale, 1),
        "lod2_floor_bbox_km2_at_this_latitude":
            round(C["lod2_minbox_deg2"] * lat_scale * lon_scale, 1),
    }

    # ── 3. shape fidelity, per named island ───────────────────────────
    def describe(ring, on_land, dist):
        pts = ring["pts"]
        per = perimeter_km(pts)
        n = corners(pts)
        return {
            "corners": n,
            "point_on_land": on_land,
            "km_offshore": dist,
            "area_km2": round(area_km2(pts), 2),
            "perimeter_km": round(per, 2),
            "compactness": round(compactness(pts), 4),
            "corners_per_100km": round(100.0 * n / per, 2) if per else None,
        }

    islands = []
    for d in box_dests:
        r_ne, on_ne, dist_ne = ring_for(d, ne_box)
        r_o, on_o, dist_o = ((None, False, None) if osm_box is None
                             else ring_for(d, osm_box))
        row = {
            "slug": d["slug"], "name": d["name"],
            "city_type": d["city_type"],
            "named": d["slug"] in NAMED,
            "span": span_by_slug[d["slug"]]["span"],
            "ne": None, "osm": None,
        }
        if r_ne:
            row["ne"] = describe(r_ne, on_ne, dist_ne)
        if r_o:
            row["osm"] = describe(r_o, on_o, dist_o)
        if row["ne"] and row["osm"]:
            c1, c2 = row["ne"]["compactness"], row["osm"]["compactness"]
            row["compactness_error"] = round(abs(c1 - c2) / c2, 4) if c2 else None
        else:
            row["compactness_error"] = None
        islands.append(row)
    res["islands"] = islands

    # THE DOT IN THE SEA. Not a shape metric — a truth metric. A destination
    # whose own coordinates fall outside every drawn polygon is a page whose
    # map says the place is offshore.
    sea = [(r["name"], r["ne"]["km_offshore"]) for r in islands
           if r["ne"] and not r["ne"]["point_on_land"]]
    res["truth"] = {
        "destinations_in_bbox": len(box_dests),
        "ne_dot_in_sea": [{"name": n, "km_offshore": d} for n, d in sorted(sea)],
        "osm_dot_in_sea": None if osm_box is None else sorted(
            r["name"] for r in islands if r["osm"] and not r["osm"]["point_on_land"]),
    }

    # ── 4. bytes at the real render ───────────────────────────────────
    ctx, land = geo.landmass(proj, (0, 0, C["map_w"], C["map_h"]))
    ne_bytes, ne_drawn = path_bytes(proj, ne_box)
    ne2_bytes, _ = path_bytes(proj, ne2_box)
    osm_bytes = None
    if osm_box is not None:
        osm_bytes, _ = path_bytes(proj, osm_box)
    res["bytes"] = {
        "minimap_whole_continent_svg_bytes": len(ctx.encode()) + len(land.encode()),
        "aegean_bbox_path_d_bytes_lod1": ne_bytes,
        "aegean_bbox_rings_emitted_lod1": ne_drawn,
        "aegean_bbox_path_d_bytes_lod2": ne2_bytes,
        "aegean_bbox_path_d_bytes_osm": osm_bytes,
        "note": "minimap() calls geo.landmass(MAPPROJ, (0,0,MAP_W,MAP_H)) — the "
                "WHOLE continent — and lets the SVG clip-path hide the rest. So "
                "every destination page carries the first figure whatever it is "
                "a map of, and the Aegean figure is what a frame-clipped "
                "minimap would carry instead.",
    }

    with open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    if args.json:
        print(RESULTS)
        return 0

    # ── the table ─────────────────────────────────────────────────────
    W = 78
    print("=" * W)
    print("AEGEAN GEOMETRY EXPERIMENT — measured", " " * 8,
          "OSM side:", "PRESENT" if osm is not None else "NOT PRESENT")
    print(f"bbox {BBOX[0]}..{BBOX[2]}E  {BBOX[1]}..{BBOX[3]}N")
    print("=" * W)

    print("\n1. THE ZOOM THE READER ACTUALLY SEES  (minimap span='auto')")
    print(f"   {len(box_dests)} atlas destinations in the bbox")
    for span, n in sorted(res["zoom"]["span_histogram"].items(),
                          key=lambda kv: -float(kv[0])):
        print(f"     span {span:>5}  {n:>3} destinations")
    z = res["zoom"]
    print(f"   dominant span {z['dominant_span']} -> "
          f"{z['dominant_km_per_rendered_unit']} km per rendered unit")
    print(f"   lod1 simplification tolerance: "
          f"{z['lod1_tolerance_km']['along_meridian']} km N-S, "
          f"{z['lod1_tolerance_km']['along_parallel']} km E-W")
    print(f"   coastline stroke: {C['stroke_px']} CSS px, non-scaling")
    for k, v in z["visibility"].items():
        print(f"     {k:<16} {v['css_px']:>7.0f} css px wide  "
              f"1 stroke = {v['km_per_stroke_width']:>6.3f} km  "
              f"tolerance = {z['lod1_tolerance_in_stroke_widths'][k]:>5} strokes")

    print("\n2. CAPTURED vs DROPPED  (the ring-drop floor)")
    c = res["capture"]
    print(f"   rings in the raw 1:50m source touching the bbox   {c['raw_ne50m_rings_in_bbox']:>5}")
    print(f"   of those, below the lod1 floor (dropped)          {c['raw_rings_below_lod1_floor']:>5}")
    print(f"   of those, below the lod2 floor (dropped)          {c['raw_rings_below_lod2_floor']:>5}")
    print(f"   rings actually in europe-lod1.json                {c['lod1_rings_in_bbox']:>5}")
    print(f"   rings actually in country/greece.json (lod2)      {c['lod2_rings_in_bbox']:>5}")
    print(f"   rings in the OSM side                             "
          f"{dash(c['osm_rings_in_bbox']):>5}")
    print(f"   islands absent from current data (needs OSM)      "
          f"{dash(c['islands_absent_from_current_data']):>5}")
    print(f"   lod1 floor is a {c['lod1_floor_bbox_km2_at_this_latitude']} km2 "
          f"BOUNDING BOX at this latitude (not an area)")

    print("\n3. SHAPE FIDELITY — the nearest drawn ring to each destination")
    hdr = (f"   {'destination':<22}{'sp':>5}{'crn':>5}{'area':>9}{'perim':>8}"
           f"{'cmp':>7}{'c/100km':>9}{'offshore':>10}   {'crn':>5}{'cmp':>7}")
    print(hdr)
    print("   " + "-" * (len(hdr) - 3))
    for r in sorted(islands, key=lambda r: (not r["named"], r["name"])):
        n = r["ne"]
        o = r["osm"]
        star = "*" if r["named"] else " "
        if not n:
            print(f"   {star}{r['name'][:21]:<21}{r['span']:>5}"
                  f"   no ring in the data")
            continue
        off = "on land" if n["point_on_land"] else f"{n['km_offshore']:.1f} km"
        print(f"   {star}{r['name'][:21]:<21}{r['span']:>5}{n['corners']:>5}"
              f"{n['area_km2']:>9.1f}{n['perimeter_km']:>8.1f}"
              f"{n['compactness']:>7.3f}{n['corners_per_100km']:>9.2f}"
              f"{off:>10}   "
              f"{dash(o and o['corners']):>5}"
              f"{dash(o and round(o['compactness'], 3)):>7}")
    print("   * = one of the four islands the experiment is named for")
    print("   crn = corners, i.e. ring length less the repeated closing point")
    print("   offshore = km from the destination to the nearest drawn coastline")

    print("\n4. TRUTH  (a dot outside every polygon is a place drawn offshore)")
    t = res["truth"]
    print(f"   NE: {len(t['ne_dot_in_sea'])} of {t['destinations_in_bbox']} "
          f"destinations in the bbox land in the sea")
    for row in t["ne_dot_in_sea"]:
        print(f"     - {row['name']:<22} {row['km_offshore']:>6.1f} km from the "
              f"nearest drawn land")
    print(f"   OSM: {dash(t['osm_dot_in_sea'] and len(t['osm_dot_in_sea']))}")

    print("\n5. BYTES AT THE REAL RENDER SIZE")
    b = res["bytes"]
    print(f"   whole-continent coastline carried by EVERY minimap  "
          f"{b['minimap_whole_continent_svg_bytes']:>9,} B")
    print(f"   the Aegean bbox alone, lod1                         "
          f"{b['aegean_bbox_path_d_bytes_lod1']:>9,} B "
          f"({b['aegean_bbox_rings_emitted_lod1']} rings)")
    print(f"   the Aegean bbox alone, lod2                         "
          f"{b['aegean_bbox_path_d_bytes_lod2']:>9,} B")
    print(f"   the Aegean bbox alone, OSM                          "
          f"{dash(b['aegean_bbox_path_d_bytes_osm'], '{:,}'):>9} B")

    print(f"\nwrote {os.path.relpath(RESULTS, ROOT)}")
    if osm is None:
        print("\nThe OSM side is NOT PRESENT. Nothing above is a comparison; it is")
        print("a measurement of one side. See README.md for what a human must do")
        print("first — and note that the licence question comes before the data.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
