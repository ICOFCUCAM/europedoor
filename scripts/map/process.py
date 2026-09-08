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


def rings_for(feature, eps, minbox):
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
        if x1 < BBOX[0] or x0 > BBOX[2] or y1 < BBOX[1] or y0 > BBOX[3]:
            continue
        ring = clip(ring, BBOX)
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

def provenance():
    with open(os.path.join(ROOT, "docs", "data-licenses", "sources.json"),
              encoding="utf-8") as fh:
        reg = json.load(fh)
    return [
        {"dataset": s["dataset"], "licence": s["licence"], "version": s["version"],
         "sha256": s["sha256"], "fetched": s["fetched"]}
        for s in reg["sources"] if s["path"].endswith(".gz")
    ]


def build():
    graph = load_graph()
    prov = provenance()
    files = {}

    cache = {}
    for lod, cfg in LODS.items():
        if cfg["src"] not in cache:
            cache[cfg["src"]] = read_ne(cfg["src"])
        src = cache[cfg["src"]]

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


def dump(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n"


def main(argv):
    check = "--check" in argv
    files = build()

    if check:
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
        for extra in sorted(have - set(files)):
            stale.append(extra + " (not produced by the pipeline)")
        if stale:
            print("data/geo/ is stale — run: python3 scripts/map/process.py")
            for s in sorted(stale):
                print("  " + s)
            return 1
        print(f"data/geo/ matches the pipeline: {len(files)} files")
        return 0

    total = 0
    for rel, obj in files.items():
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = dump(obj)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        total += len(body)
    print(f"wrote {len(files)} files, {total:,} bytes into data/geo/")
    for rel in ("europe-lod0.json", "europe-lod1.json"):
        n = sum(len(r) // 2 for c in files[rel]["countries"].values() for r in c["rings"])
        print(f"  {rel:<20} {len(files[rel]['countries']):>3} shapes  {n:>6,} points  "
              f"{len(dump(files[rel])):>8,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
