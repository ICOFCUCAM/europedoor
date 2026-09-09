#!/usr/bin/env python3
"""The terrain prototype: a DEM turned into a soft tonal field, in vectors.

    python3 scripts/map/relief.py --report
    python3 scripts/map/relief.py --out /tmp/relief.json

THIS IS A PROTOTYPE AND IS DELIBERATELY NOT WIRED INTO process.py. It writes
where it is told and never into data/geo/, because `cartography.unwritten()`
raises the moment a layer's file appears without a renderer for it — the
guard is right, and the renderer is the next decision rather than this one.
Everything here is the evidence behind docs/terrain-prototype.md.

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

import json
import math
import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ZOOM 7 AND NO DEEPER, AND THE REASON IS THE LICENCE RATHER THAN THE PIXELS.
# Tilezen fills Europe with EU-DEM at zoom 9 and with four national CC BY sets
# at zoom 10; at zoom 7 the land is SRTM and GMTED and the sea is ETOPO1, all
# three US Government public domain. See docs/data-licenses/aws-terrain-tiles.md.
Z, TILE = 7, 256

# The six tiles that cover the Chamonix frame. A wider extent is a wider fetch
# and a decision for whoever integrates this, not a default.
XS, YS = (65, 66, 67), (45, 46)

# The five steps of cartography.HYPSOMETRIC. The 0-200 step is the land tone
# the plate already paints, so only four boundaries are traced.
BANDS = (200, 600, 1200, 2000)

# Three box passes at radius 2 is a near-Gaussian over about five cells, which
# at 865 m a cell is roughly a 4 km kernel. Measured against radius 1: the
# ridges survive both, and radius 2 costs 34 KB where radius 1 costs 84.
BLUR_RADIUS = 2

# Douglas-Peucker tolerance in grid cells, and the smallest loop worth
# drawing. 1.2 cells is about 1 km, which is under a pixel on a phone and
# about two on a desktop plate.
SIMPLIFY = 1.2
MIN_AREA = 10.0


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
    """The tile block as one elevation array, in metres.

    Terrarium encoding: metres = (R * 256 + G + B / 256) - 32768. Verified
    against four known heights before anything was drawn from it — Mont Blanc
    4,675 against a true 4,808 (the summit is one cell of an 865 m grid, so
    an average), Chamonix 1,043 against 1,035, Geneva 379 against 375, and
    the sea off Nice at -941. A decoder that is out by a scale factor still
    produces a picture that looks like terrain, so this is checked with
    numbers rather than by looking.
    """
    W, H = len(XS) * TILE, len(YS) * TILE
    g = [0.0] * (W * H)
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
                    g[row + c] = (px[o] * 256 + px[o + 1] + px[o + 2] / 256.0) - 32768.0
    return W, H, g


def blur(W, H, g, radius=BLUR_RADIUS, passes=3):
    """Separable box blur, three times, which is near-Gaussian.

    This is the "soft tonal field, no hard digital shadows" half of the brief.
    An 865 m grid thresholded raw gives band edges that stair-step at cell
    size, and a stair-step reads as a rendering fault rather than as a ridge.
    """
    for _ in range(passes):
        n = 2 * radius + 1
        out = [0.0] * (W * H)
        for y in range(H):
            row = y * W
            acc = sum(g[row + min(W - 1, max(0, i))] for i in range(-radius, radius + 1))
            for x in range(W):
                out[row + x] = acc / n
                acc += (g[row + min(W - 1, x + radius + 1)]
                        - g[row + max(0, x - radius)])
        g = out
        out = [0.0] * (W * H)
        for x in range(W):
            acc = sum(g[min(H - 1, max(0, j)) * W + x] for j in range(-radius, radius + 1))
            for y in range(H):
                out[y * W + x] = acc / n
                acc += (g[min(H - 1, y + radius + 1) * W + x]
                        - g[max(0, y - radius) * W + x])
        g = out
    return g


# ── marching squares ─────────────────────────────────────────────────────

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
    def at(x, y):
        return g[y * W + x]

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

def bands():
    """[(min_m, [flat lon/lat ring, ...])], and the counts behind it."""
    W, H, g = grid()
    g = blur(W, H, g)
    PW, PH = W + 2, H + 2
    pad = [-1e9] * (PW * PH)
    for y in range(H):
        pad[(y + 1) * PW + 1:(y + 1) * PW + 1 + W] = g[y * W:(y + 1) * W]

    n = 2 ** Z

    def lonlat(x, y):
        gx = (x - 1) + XS[0] * TILE
        gy = (y - 1) + YS[0] * TILE
        lon = gx / (n * TILE) * 360.0 - 180.0
        lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gy / (n * TILE)))))
        return lon, lat

    out, stats = [], []
    for t in BANDS:
        traced = loops(PW, PH, pad, t)
        kept = [r for r in traced if area(r) >= MIN_AREA]
        simp = [simplify(r) for r in kept]
        rings = []
        for r in simp:
            flat = []
            for x, y in r:
                lo, la = lonlat(x, y)
                flat += [round(lo, 3), round(la, 3)]
            rings.append(flat)
        out.append((t, rings))
        stats.append((t, len(traced), len(kept),
                      sum(len(r) for r in kept), sum(len(r) for r in simp)))
    return out, stats


def main(argv):
    import time
    t0 = time.time()
    out, stats = bands()
    took = time.time() - t0
    doc = {"$source": "AWS Terrain Tiles zoom 7 (SRTM, GMTED2010, ETOPO1 — "
                      "public domain); see docs/data-licenses/aws-terrain-tiles.md",
           "bands": [{"min_m": t, "rings": r} for t, r in out]}
    blob = json.dumps(doc, separators=(",", ":"))
    print(f"{len(XS) * TILE}x{len(YS) * TILE} cells, "
          f"blur r={BLUR_RADIUS}x3, simplify {SIMPLIFY}, min area {MIN_AREA}")
    for t, traced, kept, v0, v1 in stats:
        print(f"  >={t:>4} m  loops {traced:>4} kept {kept:>4}  "
              f"vertices {v0:>6} -> {v1:>5}")
    print(f"  {len(blob):,} bytes of JSON, {took:.1f}s")
    for i, a in enumerate(argv):
        if a == "--out":
            path = argv[i + 1]
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(blob)
            print(f"  wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
