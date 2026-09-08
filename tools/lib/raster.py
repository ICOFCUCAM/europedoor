"""Rasterise a plate to PNG, with the standard library and nothing else.

Why this exists: `og:image`. The platforms that show a link preview want a
raster, and every illustration on this site is an SVG built at build time.
Without this, a shared EuropeDoor link is a grey box with a title on it.

Why it is written rather than installed: the alternative is Pillow plus a
headless SVG renderer — two large dependencies, one of them a browser — added
to a project whose entire dependency list is currently empty, to draw
gradients, circles and filled polygons. `zlib` and `struct` are standard
library and a scanline filler is about a hundred lines. See
`docs/architecture.md` on why the dependency list is a feature.

It renders from `render.plate_shapes()`, the same geometry the SVG comes
from. There is deliberately no second drawing: a PNG that diverges from the
SVG would only ever be seen inside somebody else's product, so nobody here
would ever notice.

Everything is span-based. The image is a list of row bytearrays, and every
primitive resolves to "fill x0..x1 on row y". That keeps a 1200x630 plate at
a few milliseconds rather than the seconds a per-pixel Python loop costs.
"""

from __future__ import annotations

import struct
import zlib


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rows = [bytearray(w * 3) for _ in range(h)]

    # ── spans ────────────────────────────────────────────────────────
    def span(self, y, x0, x1, rgb, alpha=1.0):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, int(x0))
        x1 = min(self.w, int(x1))
        if x1 <= x0:
            return
        row = self.rows[y]
        if alpha >= 1.0:
            row[x0 * 3:x1 * 3] = bytes(rgb) * (x1 - x0)
            return
        # Blended spans are rare — the light, and three reflection bars —
        # so the per-pixel cost here never shows up in a build.
        r, g, b = rgb
        inv = 1.0 - alpha
        for x in range(x0 * 3, x1 * 3, 3):
            row[x] = int(row[x] * inv + r * alpha)
            row[x + 1] = int(row[x + 1] * inv + g * alpha)
            row[x + 2] = int(row[x + 2] * inv + b * alpha)

    def vertical_gradient(self, top, bottom):
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            c = (round(top[0] + (bottom[0] - top[0]) * t),
                 round(top[1] + (bottom[1] - top[1]) * t),
                 round(top[2] + (bottom[2] - top[2]) * t))
            self.rows[y][:] = bytes(c) * self.w

    def rect(self, x, y, w, h, rgb, alpha=1.0):
        for yy in range(max(0, int(y)), min(self.h, int(y + h) + 1)):
            self.span(yy, x, x + w, rgb, alpha)

    def ellipse(self, cx, cy, rx, ry, rgb, alpha=1.0):
        if rx <= 0 or ry <= 0:
            return
        for yy in range(max(0, int(cy - ry)), min(self.h, int(cy + ry) + 1)):
            dy = (yy + 0.5 - cy) / ry
            if abs(dy) > 1:
                continue
            half = rx * (1 - dy * dy) ** 0.5
            self.span(yy, cx - half, cx + half, rgb, alpha)

    def polygon(self, pts, rgb, alpha=1.0):
        """Scanline fill, even-odd. Handles the concave ridge shapes."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            cy = y + 0.5
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if y1 == y2:
                    continue
                if (y1 <= cy < y2) or (y2 <= cy < y1):
                    xs.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.span(y, xs[i], xs[i + 1] + 1, rgb, alpha)

    # ── PNG ──────────────────────────────────────────────────────────
    def png(self):
        """Truecolour, 8-bit, filter type 0 on every scanline.

        Filter 0 (None) rather than the adaptive filtering a real encoder
        does. These images are flat bands of colour, so zlib already finds
        the runs; Paeth filtering would cost a full extra pass over two
        million pixels to save a few percent on a file that is already small.
        """
        # One join rather than 630 appends and 630 concatenations. That
        # halved the cost of a 1200x630 plate; the remainder is zlib, which
        # is C and is not going to get faster.
        raw = b"".join(b"\x00" + bytes(row) for row in self.rows)
        def chunk(tag, payload):
            return (struct.pack(">I", len(payload)) + tag + payload
                    + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9))
                + chunk(b"IEND", b""))


def plate_png(shapes, w, h):
    """Render (sky_top, sky_bottom, prims) from render.plate_shapes()."""
    sky_a, sky_b, prims = shapes
    c = Canvas(w, h)
    c.vertical_gradient(sky_a, sky_b)
    for prim in prims:
        kind = prim[0]
        if kind == "poly":
            c.polygon(prim[1], prim[2], prim[3])
        elif kind == "rect":
            c.rect(prim[1], prim[2], prim[3], prim[4], prim[5], prim[6])
        elif kind == "circle":
            c.ellipse(prim[1], prim[2], prim[3], prim[3], prim[4], prim[5])
        elif kind == "ellipse":
            c.ellipse(prim[1], prim[2], prim[3], prim[4], prim[5], prim[6])
    return c.png()
