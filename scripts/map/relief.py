#!/usr/bin/env python3
"""A DEM turned into a soft tonal field, in vectors.

    python3 scripts/map/relief.py            report, write nothing
    python3 scripts/map/relief.py --out X    write the bands to X

Called by scripts/map/process.py, which is where data/geo/terrain-lod1.json
and the per-destination relief measurement come from. The evidence behind the
decision to have this at all is in docs/terrain-prototype.md: Chamonix rendered
four ways and looked at.

WHY VECTORS AND NOT A PICTURE. There is no <img> on this site and there is
not going to be one for a map: the register holds no photographs, the
Content-Security-Policy is default-src 'none', and an invariant counts <img>
tags at zero. So a DEM cannot arrive as a raster the way it does in every
other mapping stack. It arrives as bands — the boundaries of "at least this
high" traced into lon/lat rings and painted back to front, which is what a
printed physical atlas is and what a hillshade is not.

WHY THE BANDS ARE THE WHOLE OF IT. The brief asked for a soft tonal field
with perceptible ridges and valleys and no hard digital shadows, and said no
GIS hillshade. A hillshade is a light source: it invents a direction and
paints structure onto flat ground. Hypsometric bands claim only height, which
is the one thing the source actually measures.

The chain is: decode -> blur -> threshold -> trace -> simplify -> project.
"""

import array
import hashlib
import json
import math
import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ZOOM 6 AND NO DEEPER, AND THE REASON IS THE LICENCE RATHER THAN THE PIXELS.
# Tilezen fills Europe with EU-DEM at zoom 9 and with four national CC BY sets
# at zoom 10, and zoom 7 brings in SRTM. At zoom 6 the land is GMTED2010 and
# the sea is ETOPO1 — two US Government public-domain sets and nothing else.
# See docs/data-licenses/aws-terrain-tiles.md, where every tile carries the
# provenance header the service returned for it.
#
# AND ZOOM 6 IS ALSO THE RIGHT PICTURE, which is luck rather than design and
# was measured rather than assumed. The prototype ran at zoom 7; rendered
# against the same Chamonix frame the two are indistinguishable, because the
# field is smoothed with a 5 km kernel either way and 865 m of detail is
# thrown away before anything is drawn. Zoom 7 over the same extent would be
# 728 tiles instead of 182 and four times the bytes for nothing a reader can
# see. Smoothed harder — an 8.6 km kernel — the Arve and Aosta valleys merge
# into one mass and the 2,000 m band nearly disappears, so this is not simply
# "coarser is fine".
Z, TILE = 6, 256

# The extent the atlas draws, which is pages.MAPPROJ's own bbox. Stated here
# rather than imported because scripts/ does not import tools/lib — but the
# numbers are asserted equal by checks.py, so the two cannot drift.
EXTENT = (-25.0, 33.0, 45.0, 71.5)          # lon0, lat0, lon1, lat1


def tile_x(lon):
    return int((lon + 180.0) / 360.0 * 2 ** Z)


def tile_y(lat):
    return int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi)
               / 2.0 * 2 ** Z)


def tiles():
    """Every tile that intersects the extent: 14 x 13 = 182.

    THE WHOLE EXTENT, NOT ONLY THE MOUNTAINS. Whether a destination gets
    terrain at all is a measurement taken from this grid, and Paris has to be
    measured to be found flat. A list of mountainous places typed by hand
    would be an authored measurement, which is the one thing this repository
    does not do.
    """
    xs = range(tile_x(EXTENT[0]), tile_x(EXTENT[2]) + 1)
    ys = range(tile_y(EXTENT[3]), tile_y(EXTENT[1]) + 1)
    return list(xs), list(ys)


XS, YS = tiles()

# The five steps of cartography.HYPSOMETRIC. The 0-200 step is the land tone
# the plate already paints, so only four boundaries are traced.
BANDS = (200, 600, 1200, 2000)

# Three box passes at radius 1 is a near-Gaussian over about five kilometres.
# This is the "soft tonal field, no hard digital shadows" half of the brief:
# a grid thresholded raw stair-steps at cell size, and a stair-step reads as a
# rendering fault rather than as a ridge.
BLUR_RADIUS = 1

# Douglas-Peucker tolerance in grid cells, and the smallest loop worth
# drawing. 0.6 cells is about a kilometre, under a pixel on a phone; 4 cells
# squared is about 12 square kilometres, which is a hill rather than a speck.
SIMPLIFY = 0.8
MIN_AREA = 8.0

# HOW FAR FROM A PLACE ITS OWN RELIEF IS MEASURED. Not the plate frame: a
# destination frame is 590 km across, and Venice's contains the whole of the
# eastern Alps. What decides whether terrain belongs on a picture OF VENICE is
# the ground within an afternoon of Venice, which is flat.
#
# 40 km rather than 25, because 25 measured Bergen at 387 m and Bergen is a
# town of seven mountains: at 1.7 km a cell, Ulriken's 643 m averages down to
# a shoulder, and the fjord walls that make the place are just outside the
# circle. 40 km is still an afternoon and reads Bergen at 707 m. It does not
# rescue Venice (41 m), Amsterdam (11) or Paris (150), which is the test that
# matters — a radius wide enough to find mountains everywhere would find them
# in the Netherlands.
RELIEF_RADIUS_KM = 40.0

# The two thresholds that decide whether a place's picture gets relief:
# 300 m of variation within 25 km, AND ground reaching the 600 m band, which
# is the first band a reader can see. See draws() for why there is one
# strength rather than two.
RELIEF_OFF, RELIEF_CREST = 300.0, 600.0


# ── the source ───────────────────────────────────────────────────────────

def png_rgb(path):
    """A truecolour 8-bit PNG as (w, h, channels, bytes). Stdlib only.

    Everything else in this repository is stdlib and a raster decoder is not
    a reason to break that: it is zlib plus the five filter types, and the
    filters are the whole of the format that matters here.
    """
    raw = open(path, "rb").read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    i, idat, w, h, chan = 8, [], None, None, None
    while i < len(raw):
        ln = struct.unpack(">I", raw[i:i + 4])[0]
        typ = raw[i + 4:i + 8]
        body = raw[i + 8:i + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _comp, _filt, inter = struct.unpack(">IIBBBBB", body)
            if depth != 8 or inter:
                raise ValueError(f"{path}: only 8-bit non-interlaced is decoded")
            chan = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
        i += 12 + ln
    data = zlib.decompress(b"".join(idat))
    stride = w * chan
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = data[p]
        p += 1
        line = bytearray(data[p:p + stride])
        p += stride
        if f == 1:
            for x in range(chan, stride):
                line[x] = (line[x] + line[x - chan]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - chan] if x >= chan else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - chan] if x >= chan else 0
                b = prev[x]
                c = prev[x - chan] if x >= chan else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, chan, bytes(out)


def grid():
    """The whole mosaic as one elevation array, in metres, row-major.

    An `array('f')` rather than a list: 11.9 million cells is 48 MB packed and
    about half a gigabyte as Python floats, and the blur needs two of them.

    Terrarium encoding: metres = (R * 256 + G + B / 256) - 32768. Verified
    against four known heights before anything was drawn from it — Mont Blanc,
    Chamonix, Geneva and the sea off Nice — because a decoder that is out by a
    scale factor still produces a picture that looks like terrain, so this is
    checked with numbers rather than by looking.

    A tile that is not in data/raw/ is an error, not a hole. Half a mosaic
    would draw a coastline of missing data straight through the Alps and look
    like a rendering fault, which this repository has already shipped once.
    """
    W, H = len(XS) * TILE, len(YS) * TILE
    g = array.array("f", bytes(4 * W * H))
    for ti, x in enumerate(XS):
        for tj, y in enumerate(YS):
            path = os.path.join(ROOT, "data", "raw", "terrarium",
                                str(Z), str(x), f"{y}.png")
            tw, th, chan, px = png_rgb(path)
            if (tw, th) != (TILE, TILE):
                raise ValueError(f"{path} is {tw}x{th}")
            for r in range(TILE):
                base = r * TILE * chan
                row = (tj * TILE + r) * W + ti * TILE
                for c in range(TILE):
                    o = base + c * chan
                    g[row + c] = (px[o] * 256 + px[o + 1]
                                  + px[o + 2] / 256.0) - 32768.0
    return W, H, g


def cell(lon, lat):
    """(lon, lat) -> fractional cell in the mosaic."""
    n = 2 ** Z * TILE
    x = (lon + 180.0) / 360.0 * n - XS[0] * TILE
    y = ((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
         - YS[0] * TILE)
    return x, y


def lonlat(x, y):
    """A cell in the mosaic -> (lon, lat)."""
    n = 2 ** Z * TILE
    gx = x + XS[0] * TILE
    gy = y + YS[0] * TILE
    return (gx / n * 360.0 - 180.0,
            math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gy / n)))))


def relief_at(W, H, g, lon, lat, radius_km=RELIEF_RADIUS_KM):
    """How much ground goes up and down within `radius_km` of a point.

    NOT THE PLATE FRAME. A destination frame is 590 km across and Venice's
    contains the whole of the eastern Alps, so a frame-wide measure would put
    the Dolomites' relief on a picture of a lagoon. What decides whether
    terrain belongs on a picture OF somewhere is the ground within an
    afternoon of it.

    The 95th minus the 5th percentile rather than max minus min, so one
    summit or one sinkhole in range cannot decide it.

    LAND ONLY, AND THE FIRST VERSION WAS SYSTEMATICALLY BIASED AGAINST
    EXACTLY THE PLACES THIS IS FOR. Clamping the sea to zero and including it
    put a coastal town's water in the same distribution as its hills, and a
    percentile over a circle that is four-fifths sea is a percentile of sea:
    Athens, in a basin ringed by Hymettus, Penteli and Parnitha, measured 556
    m at 40 km — lower than at 25 — because widening the circle added water,
    not mountains. Nice measured 1,200 once the water came out. A derivation
    can be systematically biased and only a measurement finds it; this
    repository has made that exact mistake once already, deriving `city_type`
    from a dataset of populated places and getting one village in 157.

    Returns [spread, crest]; both zero where there is not enough land to
    measure, which is how a small island answers honestly rather than flat.
    """
    # Mercator cells are square in metres, so one radius in cells covers the
    # circle at this latitude.
    m_per_cell = (math.cos(math.radians(lat)) * 2 * math.pi * 6378137.0
                  / (2 ** Z * TILE))
    r = max(1, int(round(radius_km * 1000.0 / m_per_cell)))
    cx, cy = cell(lon, lat)
    x0, x1 = max(0, int(cx) - r), min(W - 1, int(cx) + r)
    y0, y1 = max(0, int(cy) - r), min(H - 1, int(cy) + r)
    vals = []
    rr = r * r
    for y in range(y0, y1 + 1):
        dy = y - cy
        row = y * W
        for x in range(x0, x1 + 1):
            dx = x - cx
            if dx * dx + dy * dy <= rr:
                v = g[row + x]
                if v > 0.0:
                    vals.append(v)
    if len(vals) < 8:
        return [0.0, 0.0]
    vals.sort()
    hi = vals[int(0.95 * (len(vals) - 1))]
    lo = vals[int(0.05 * (len(vals) - 1))]
    return [round(hi - lo, 1), round(hi, 1)]


def draws(measure):
    """Whether this place's picture gets relief at all. Two tests.

    ONE PALETTE, ABSOLUTE, AND THE FLAT PLACES ARE REDUCED BY THE SCALE
    RATHER THAN BY A WEAKER INK. A second, fainter strength was built first
    and measured: at 40% of the way to the hypsometric colours, the only band
    Bergen has is 0.043 of luminance from the land tone, which is a layer
    that paints twenty-three kilobytes and cannot be seen. Worse, two
    strengths make #d8ceb4 mean 600 m on one page and something else on
    another, and a hypsometric scale that is not absolute is not a
    hypsometric scale.

    A flat place is already quieter, automatically: it only ever reaches the
    quiet end of the scale. Bergen's ground crosses one boundary and gets one
    step; Chamonix's crosses four.

    So the reduction is an on/off, and it takes two measurements:

      spread  the 95th minus the 5th percentile within 25 km — is there
              variation to show at all
      crest   the 95th percentile itself — does that variation cross a
              boundary a reader can SEE. The 200 m step is 0.013 of
              luminance from the land tone, which is deliberately the
              quietest thing on the plate; a place whose ground reaches only
              that band would ship a layer nobody can read.
    """
    spread, crest = measure
    return spread >= RELIEF_OFF and crest >= RELIEF_CREST


def blur(W, H, g, radius=BLUR_RADIUS, passes=3):
    """Separable box blur, three times, which is near-Gaussian.

    This is the "soft tonal field, no hard digital shadows" half of the brief.
    An 865 m grid thresholded raw gives band edges that stair-step at cell
    size, and a stair-step reads as a rendering fault rather than as a ridge.
    """
    for _ in range(passes):
        n = 2 * radius + 1
        out = array.array("f", bytes(4 * W * H))
        for y in range(H):
            row = y * W
            acc = sum(g[row + min(W - 1, max(0, i))] for i in range(-radius, radius + 1))
            for x in range(W):
                out[row + x] = acc / n
                acc += (g[row + min(W - 1, x + radius + 1)]
                        - g[row + max(0, x - radius)])
        g = out
        out = array.array("f", bytes(4 * W * H))
        for x in range(W):
            acc = sum(g[min(H - 1, max(0, j)) * W + x] for j in range(-radius, radius + 1))
            for y in range(H):
                out[y * W + x] = acc / n
                acc += (g[min(H - 1, y + radius + 1) * W + x]
                        - g[max(0, y - radius) * W + x])
        g = out
    return g


# ── marching squares ─────────────────────────────────────────────────────

# A CELL EXACTLY ON THE THRESHOLD IS THE DEGENERATE CASE, and it happened.
# Six cells in the mosaic hold exactly 200.0 m, one exactly 1200.0 and one
# exactly 2000.0 — GMTED is metres and the box blur of a flat neighbourhood
# lands back on an integer often enough. A corner exactly equal to the
# threshold puts the crossing ON a grid corner, two cells then produce
# coincident endpoints, and the chain has two ways to leave one point: six
# segments in chains that did not close, on a run that was correct
# everywhere else. Nudging the threshold off every representable elevation
# by a millimetre removes the case rather than special-casing it, and moves
# a band boundary by a millimetre of height.
THRESHOLD_EPS = 1e-3


def _interp(a, b, t):
    return 0.5 if b == a else (t - a) / (b - a)


def loops(W, H, g, t):
    """Every closed iso-line at `t`, as rings of (x, y) in grid coordinates.

    THE GRID MUST BE PADDED with a ring of very low values before this is
    called, so no contour can reach the boundary and every loop closes. An
    open polyline cannot be filled.

    EVERY SEGMENT IS EMITTED WITH THE HIGH GROUND ON ITS RIGHT, so each
    vertex has exactly one segment leaving it and one arriving, and the
    chaining below is unambiguous. THE SADDLE CASES BROKE THAT IN THE FIRST
    VERSION: two of their four segments were emitted backwards, which gives
    some vertices two departures and others none, so chains merge into one
    another and never close. 8,424 segments traced at the 200 m threshold and
    1,614 of them ended up in a closed ring; the outer boundary of the Alps —
    the one ring that matters — was silently discarded, and the picture that
    produced was terrain in the Rhone valley and none on Mont Blanc. It reads
    as a registration error, which is what sent the first hour of debugging
    at the projection instead of at the topology.
    """
    t = t + THRESHOLD_EPS
    segs = []
    for y in range(H - 1):
        row = y * W
        for x in range(W - 1):
            v0 = g[row + x]              # top-left
            v1 = g[row + x + 1]          # top-right
            v2 = g[row + W + x + 1]      # bottom-right
            v3 = g[row + W + x]          # bottom-left
            idx = ((v0 >= t) << 3) | ((v1 >= t) << 2) | ((v2 >= t) << 1) | (v3 >= t)
            if idx == 0 or idx == 15:
                continue
            top = (x + _interp(v0, v1, t), y)
            right = (x + 1, y + _interp(v1, v2, t))
            bottom = (x + _interp(v3, v2, t), y + 1)
            left = (x, y + _interp(v0, v3, t))
            if idx in (1, 14):
                segs.append((left, bottom) if idx == 1 else (bottom, left))
            elif idx in (2, 13):
                segs.append((bottom, right) if idx == 2 else (right, bottom))
            elif idx in (3, 12):
                segs.append((left, right) if idx == 3 else (right, left))
            elif idx in (4, 11):
                segs.append((right, top) if idx == 4 else (top, right))
            elif idx in (6, 9):
                segs.append((bottom, top) if idx == 6 else (top, bottom))
            elif idx in (7, 8):
                segs.append((left, top) if idx == 7 else (top, left))
            else:
                # A saddle, resolved by the cell average — the standard
                # disambiguation, and the only one that keeps a ridge from
                # pinching into an hourglass at every col.
                mid = (v0 + v1 + v2 + v3) / 4.0
                if idx == 5:            # TR and BL high; TL and BR low
                    if mid >= t:        # centre high: the low corners are cut
                        segs.append((left, top)); segs.append((right, bottom))
                    else:               # centre low: the high corners are cut
                        segs.append((right, top)); segs.append((left, bottom))
                else:                   # TL and BR high; TR and BL low
                    if mid >= t:
                        segs.append((top, right)); segs.append((bottom, left))
                    else:
                        segs.append((top, left)); segs.append((bottom, right))

    # Endpoints computed from the same two corner values on the same shared
    # edge are bit-identical, so an exact tuple key is safe and no tolerance
    # is needed. A tolerance here would merge two ridges that pass close.
    avail = {}
    for s in segs:
        avail.setdefault(s[0], []).append(s)
    out, lost = [], 0
    for h in list(avail):
        while avail.get(h):
            seg = avail[h].pop()
            ring = [seg[0], seg[1]]
            while True:
                nxt = avail.get(ring[-1])
                if not nxt:
                    break
                seg = nxt.pop()
                ring.append(seg[1])
                if ring[-1] == ring[0]:
                    break
            if len(ring) >= 4 and ring[-1] == ring[0]:
                out.append(ring)
            else:
                lost += len(ring) - 1
    if lost:
        # Not a warning to ignore: an unclosed chain is the saddle bug back.
        raise AssertionError(f"{lost} segments in chains that did not close "
                             f"at {t} m — the segment orientation is wrong")
    return out


def area(ring):
    a = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def simplify(ring, eps=SIMPLIFY):
    """Douglas-Peucker on a closed ring, keeping it closed."""
    pts = ring[:-1]
    if len(pts) < 4:
        return ring

    def dp(seq):
        if len(seq) < 3:
            return seq
        x0, y0 = seq[0]
        x1, y1 = seq[-1]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy)
        worst, wi = -1.0, 0
        for i in range(1, len(seq) - 1):
            px, py = seq[i]
            d = (abs(dy * px - dx * py + x1 * y0 - y1 * x0) / n if n
                 else math.hypot(px - x0, py - y0))
            if d > worst:
                worst, wi = d, i
        if worst <= eps:
            return [seq[0], seq[-1]]
        return dp(seq[:wi + 1])[:-1] + dp(seq[wi:])

    # Split at two opposite points, or the ring is simplified as one line
    # from a point to itself and collapses.
    half = len(pts) // 2
    out = dp(pts[:half + 1])[:-1] + dp(pts[half:] + [pts[0]])
    if out[-1] != out[0]:
        out.append(out[0])
    return out


# ── the whole chain ──────────────────────────────────────────────────────

def field():
    """The smoothed mosaic, once. Both outputs are derived from this."""
    W, H, g = grid()
    return W, H, blur(W, H, g)


def bands(W, H, g):
    """[(min_m, [flat lon/lat ring, ...])], and the counts behind it."""
    PW, PH = W + 2, H + 2
    pad = array.array("f", bytes(4 * PW * PH))
    for i in range(PW * PH):
        pad[i] = -1e9
    for y in range(H):
        pad[(y + 1) * PW + 1:(y + 1) * PW + 1 + W] = g[y * W:(y + 1) * W]

    out, stats = [], []
    for t in BANDS:
        traced = loops(PW, PH, pad, t)
        kept = [r for r in traced if area(r) >= MIN_AREA]
        simp = [simplify(r) for r in kept]
        rings = []
        for r in simp:
            flat = []
            for x, y in r:
                lo, la = lonlat(x - 1, y - 1)
                flat += [round(lo, 3), round(la, 3)]
            rings.append(flat)
        out.append((t, rings))
        stats.append((t, len(traced), len(kept),
                      sum(len(r) for r in kept), sum(len(r) for r in simp)))
    return out, stats


SOURCE_LINE = ("AWS Terrain Tiles zoom 6 (GMTED2010 and ETOPO1, US Government "
               "public domain); see docs/data-licenses/aws-terrain-tiles.md")


def fingerprint():
    """What this file would be regenerated FROM, in one comparable dict.

    WHY A FINGERPRINT AND NOT A RECOMPUTATION. Everything else in data/geo/ is
    checked by rebuilding it and comparing: `checks.py` calls process.build()
    and diffs the result, which is the strongest possible staleness contract
    and costs a second. This one costs a minute — decoding 182 PNGs and
    smoothing twelve million cells in pure Python — and `checks.py` is the
    gate people run every few minutes. A gate that takes a minute is a gate
    people stop running, which is the same reason plate-variation.py is kept
    out of the suite.

    So the guard moves to the inputs. It fails if any source byte changes
    (the tiles are hashed), if any parameter changes, or if this file changes
    at all — including a comment, because a check that decides which of your
    edits mattered is a check that will one day decide wrongly. Regenerating
    is one command.

    That is not weaker than diffing the output. It is different: diffing
    catches an edit that changes the drawing, and this catches an edit that
    changes the pipeline, which is a superset — a refactor that happens to
    produce identical rings still has to be re-run and re-committed, and the
    diff will show nothing, which is the correct answer.
    """
    h = hashlib.sha256()
    for x in XS:
        for y in YS:
            path = os.path.join(ROOT, "data", "raw", "terrarium",
                                str(Z), str(x), f"{y}.png")
            with open(path, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
    with open(os.path.abspath(__file__), "rb") as fh:
        code = hashlib.sha256(fh.read()).hexdigest()
    return {
        "zoom": Z, "extent": list(EXTENT),
        "tiles": f"{len(XS)}x{len(YS)}",
        "bands_m": list(BANDS),
        "blur_radius": BLUR_RADIUS, "blur_passes": 3,
        "threshold_eps": THRESHOLD_EPS,
        "simplify_cells": SIMPLIFY, "min_area_cells": MIN_AREA,
        "relief_radius_km": RELIEF_RADIUS_KM,
        "relief_thresholds_m": [RELIEF_OFF, RELIEF_CREST],
        "tiles_sha256": h.hexdigest(),
        "relief_py_sha256": code,
    }


def document(W, H, g, places=()):
    """The terrain file: the bands, and the relief measured for each place.

    `places` is [(key, lon, lat)] — the atlas's own destinations. The
    measurement lives here rather than in facts.json because it comes from
    this grid and nothing else does, and because facts.json is rebuilt and
    diffed on every checks.py run while this file is guarded by its
    fingerprint.
    """
    out, stats = bands(W, H, g)
    cell_m = (math.cos(math.radians(45.0)) * 2 * math.pi * 6378137.0
              / (2 ** Z * TILE))
    relief = {}
    for key, lon, lat in places:
        relief[key] = relief_at(W, H, g, lon, lat)   # [spread, crest]
    return {
        "$comment": "GENERATED by scripts/map/relief.py. Hypsometric band "
                    "boundaries traced from a public-domain elevation model, "
                    "and the relief measured within "
                    f"{RELIEF_RADIUS_KM:.0f} km of each destination as "
                    "[spread, crest] in metres — which is what decides "
                    "whether that destination's picture gets terrain at all. Never hand-edited: run "
                    "`python3 scripts/map/process.py --terrain`.",
        "$source": SOURCE_LINE,
        "cell_m": round(cell_m),
        "smoothed_m": round(cell_m * (2 * BLUR_RADIUS + 1)),
        "relief_radius_km": RELIEF_RADIUS_KM,
        "relief_thresholds_m": {"min_spread": RELIEF_OFF,
                                "min_crest": RELIEF_CREST},
        "pipeline": fingerprint(),
        "relief": relief,
        "bands": [{"min_m": t, "rings": r} for t, r in out],
    }, stats


def main(argv):
    import time
    t0 = time.time()
    W, H, g = field()
    t1 = time.time()
    doc, stats = document(W, H, g)
    blob = json.dumps(doc, separators=(",", ":"))
    print(f"{W}x{H} cells over {len(XS)}x{len(YS)} tiles, "
          f"blur r={BLUR_RADIUS}x3, simplify {SIMPLIFY}, min area {MIN_AREA}")
    print(f"  field in {t1 - t0:.1f}s")
    for t, traced, kept, v0, v1 in stats:
        print(f"  >={t:>4} m  loops {traced:>5} kept {kept:>5}  "
              f"vertices {v0:>7} -> {v1:>6}")
    print(f"  {len(blob):,} bytes of JSON, {time.time() - t0:.1f}s total")
    for lon, lat, name in ((6.87, 45.92, "Chamonix"), (7.75, 46.02, "Zermatt"),
                           (5.32, 60.39, "Bergen"), (11.67, 46.57, "Ortisei"),
                           (23.73, 37.98, "Athens"), (12.34, 45.44, "Venice"),
                           (4.90, 52.37, "Amsterdam"), (2.35, 48.86, "Paris")):
        m = relief_at(W, H, g, lon, lat)
        print(f"  {name:<10} spread {m[0]:>7.0f} m  crest {m[1]:>7.0f} m "
              f"within {RELIEF_RADIUS_KM:.0f} km -> "
              f"{'terrain' if draws(m) else 'none'}")
    for i, a in enumerate(argv):
        if a == "--out":
            with open(argv[i + 1], "w", encoding="utf-8") as fh:
                fh.write(blob)
            print(f"  wrote {argv[i + 1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
