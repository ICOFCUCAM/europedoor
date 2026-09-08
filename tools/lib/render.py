"""HTML for EuropeDoor.

There is exactly one page shell in this file and every page goes through it.
That is the whole anti-drift strategy: if a masthead, a footer or a set of
head tags exists in two places, they diverge within a month, so they exist
here once.

No photographs. Every place gets a generated "plate" instead — a small
deterministic SVG built from the hash of its own slug. It costs nothing, it
needs no licence, it never 404s, and two places never share one.
"""

from __future__ import annotations

import hashlib
import html
import json

from .i18n import Strings

# One catalogue, loaded once. Adding a language means adding a file, not
# editing this one — which is the whole point of the exercise.
T = Strings("en")

SITE_NAME = "EuropeDoor"
SITE_TAGLINE = "Open the door to Europe."
# The operating company is not incorporated yet. Nothing on this site may
# name an entity that does not exist; see docs/legal-position.md.
OPERATOR = "[OPERATOR ENTITY — NOT YET INCORPORATED]"


# The mark, drawn once. Concept B from the Brand Bible: two vertical forms,
# and the negative space between them is the symbol — the outer form is the
# doorway, the inner is the leaf standing ajar. Inline rather than an <img>
# so it takes the brand colour from CSS and survives with no extra request,
# and because checks.py forbids an <img> tag anywhere.
MARK = (
    '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
    '<path class="mark-frame" d="M5.5 29V15.2a10.5 10.5 0 0 1 21 0V29h-3.3V15.2'
    'a7.2 7.2 0 0 0-14.4 0V29z"/>'
    '<path class="mark-leaf" d="M10.9 29V16.6a5.1 5.1 0 0 1 5.1-5.1V29z"/>'
    "</svg>"
)


def esc(s):
    return html.escape(str(s), quote=True)


# The illustration system.
#
# There are no photographs on this site yet, and until there are, every
# surface that wants one gets a generated plate instead. The first version
# was a gradient with seven random bars on it, and at hero size on a city
# page it did not read as an illustration — it read as a broken image. That
# is a real cost: a reader who thinks a picture failed to load stops
# trusting the rest of the page.
#
# So a plate is now a small landscape, built entirely from the hash of the
# thing's own slug:
#
#   * the palette is not free-roaming HSL. It is sampled from a fixed ramp
#     of six brand-adjacent hues, so 987 plates look like one family rather
#     than like a colour picker.
#   * the composition is a horizon — sky, a far range, a mid range, a
#     foreground — with a light source whose height comes from the seed.
#   * the motif comes from what the place actually is, where the caller
#     knows: peaks for mountains, a headland and water for coast, a skyline
#     for cities, a tower for sacred, an archipelago for islands.
#
# The doorway is deliberately NOT in here; see the note further down for the
# three attempts that established why.
#
# When a real photograph arrives for a slug, picture() serves it and this is
# never called for that slug again. The plate is the honest empty state, not
# the policy.

# Six hues around the palette: Atlantic green, sea, slate blue, stone,
# brass, brick. Chosen so any two of them sit together.
#
# Heath purple (262) was in this list for one build and came out as
# saturated violet on a fifth of the plates — a colour that appears nowhere
# else in the identity, shouting from the card grid. Removed. The set is
# deliberately narrow: an illustration system with a wide gamut does not
# read as a system.
# ── plate hues ──────────────────────────────────────────────────────
#
# European Future. The old set was (168, 196, 210, 32, 24, 14) — Atlantic
# teal through to brick — and the warm half of it was the terracotta accent
# showing up in every generated landscape. Under the new system warmth comes
# from the ivory ground and from photography, not from the plates, so these
# are six cool steps around cobalt (229°) and ultramarine (244°): slate,
# steel, cold sea, cobalt, indigo, violet.
#
# Six, not four, because the distribution is `hash % len(PLATE_HUES)` across
# 794 cards and a shorter list is visibly repetitive on an index page. And
# low saturation throughout: this is meant to read as stone and weather at
# dusk, which is cinematic, rather than as six blue rectangles, which is a
# corporate deck.
PLATE_HUES = (200, 214, 224, 229, 236, 244)

# Saturation is capped per hue. The warm end (brass, brick) goes muddy above
# about 30%, and the cool end goes to a swimming-pool blue above 34%.
# Saturation is capped per hue. Above about 30% at the cobalt end the plates
# stop being architecture and start being a swimming pool, and the violet end
# goes purple-neon — which is on the avoid list by name.
PLATE_SAT = {200: 16, 214: 18, 224: 20, 229: 22, 236: 19, 244: 17}

MOTIFS = ("peaks", "coast", "skyline", "tower", "isles", "forest", "plain")

# Which motif an interest asks for. First match in this order wins, so a
# mountain town on a coast draws mountains — the thing it is known for.
# Order matters and it is not obvious. The first version put "history"
# third, and since almost every European city is tagged with it, six plates
# in twelve came out as the same church tower. History is now near the end:
# it is what a place falls back to when nothing more specific describes it.
MOTIF_BY_INTEREST = (
    ("mountains", "peaks"), ("winter", "peaks"), ("wild", "peaks"),
    ("islands", "isles"), ("coast", "coast"),
    ("sacred", "tower"),
    ("cities", "skyline"), ("architecture", "skyline"),
    ("nature", "forest"), ("wine", "forest"),
    ("art", "skyline"), ("food", "plain"),
    ("history", "tower"),
)


# What KIND of place gets which drawing, once its topography has had first
# refusal. This arrived after the schema audit gave every destination a
# `city_type`, and it fixes a data-to-visual mismatch: the atlas knew Civita
# di Bagnoregio was a village on a tufa pillar and drew it as a skyline of
# tower blocks, because the plate reads interests and nothing else.
#
# Deliberately NOT one motif per city_type — no village_motif, no park_motif.
# Eight classifications map onto the six drawings that already exist:
#
#   village  →  plain    open country with soft ridges
#   site     →  tower    a single monument in a landscape
#   island   →  isles
#   valley   →  peaks
#   park     →  forest
# ONLY the classifications that are visually decisive. capital, city and town
# are deliberately absent: what a settlement is *for* — sacred, wine, art,
# nature — describes it better than its size does, and those live in
# MOTIF_BY_INTEREST below.
#
# The first version of this table mapped all eight, and the experiment
# measured the cost: `forest` fell from 19 plates to 1, because a universal
# classification placed above the interest pass means the interest pass never
# runs. One dead motif was traded for another. Five decisive kinds, and the
# interests keep everything else.
MOTIF_BY_KIND = {
    "village": "plain",    # a village is not a skyline of tower blocks
    "site": "tower",       # a single monument in a landscape
    "island": "isles",
    "valley": "peaks",
    "park": "forest",
}

# Topography wins over classification. Bergen is a city AND is wedged between
# seven mountains on a fjord; drawing it as a skyline would be true and
# useless. These three interests describe the land itself, so they get first
# refusal before the kind of settlement is considered at all.
MOTIF_BY_LAND = (
    ("mountains", "peaks"), ("winter", "peaks"), ("wild", "peaks"),
    ("islands", "isles"), ("coast", "coast"),
)


def motif_for(interests, city_type=None):
    """The motif a place asks for, in three passes.

        1. the land          mountains, islands, coast
        2. what kind of place it is    city_type
        3. everything else   the remaining interests

    Returns None only if all three miss, which lets the hash choose. Before
    city_type was consulted, pass 3 caught everything and `plain` was
    unreachable — one of seven motifs was dead code, because `food → plain`
    sat below eight interests that almost every European destination carries.
    Villages reach it now.
    """
    have = interests or ()
    for want, motif in MOTIF_BY_LAND:
        if want in have:
            return motif
    if city_type in MOTIF_BY_KIND:
        return MOTIF_BY_KIND[city_type]
    for want, motif in MOTIF_BY_INTEREST:
        if want in have:
            return motif
    return None


def _hsl(h, sl, l):
    """HSL to an (r, g, b) triple.

    The SVG renderer could emit hsl() and let the browser do this. The PNG
    renderer cannot, and having two colour pipelines is how the two drawings
    start disagreeing — so both go through here.
    """
    sl, l = sl / 100.0, l / 100.0
    c = (1 - abs(2 * l - 1)) * sl
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = l - c / 2
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60) % 6]
    return (round((r + m) * 255), round((g + m) * 255), round((b + m) * 255))


def plate_shapes(seed, w, h, motif=None):
    """The geometry of one plate, as primitives, in draw order.

    This exists so that the SVG on the page and the PNG a social card shows
    come from ONE description. Two drawings of the same illustration diverge
    the first time somebody adjusts one of them, and nobody would ever
    notice — the PNG is only ever seen inside somebody else's product.

    Returns (sky_top, sky_bottom, prims), where each prim is a tuple:
        ("poly",    [(x, y), ...],        rgb, alpha)
        ("rect",    x, y, w, h,           rgb, alpha)
        ("circle",  cx, cy, r,            rgb, alpha)
        ("ellipse", cx, cy, rx, ry,       rgb, alpha)
    """
    d = hashlib.sha256(seed.encode("utf-8")).digest()
    if motif is None:
        motif = MOTIFS[d[0] % len(MOTIFS)]

    hue = PLATE_HUES[d[1] % len(PLATE_HUES)]
    hue2 = PLATE_HUES[(d[1] + 1 + d[2] % 3) % len(PLATE_HUES)]
    # Night for a fifth of them, and it is the seed that decides — so a
    # place does not change mood between builds.
    night = d[3] % 5 == 0
    sat, sat2 = PLATE_SAT[hue], PLATE_SAT[hue2]
    if night:
        # Night. The sky bottoms out near graphite and the light is the
        # electric accent — which is the only place lime appears in a
        # DISCOVER surface, and it appears there because a night plate IS a
        # dark ground. Contrast does the policing: lime on #101214 is 16:1
        # and on ivory is 1.05:1, so it cannot leak into the light world.
        sky_a, sky_b = _hsl(hue, sat + 6, 9), _hsl(hue2, sat2, 21)
        band = [_hsl(hue, sat, l) for l in (18, 13, 9)]
        light = _hsl(79, 62, 66)
    else:
        # Day. The sky lifts toward ivory rather than to a saturated blue, so
        # a card sits on the page instead of shouting off it, and the sun is
        # a low warm one — the single warm note in the system, and the reason
        # the plates read as European light rather than as a gradient.
        sky_a, sky_b = _hsl(hue2, max(8, sat2 - 8), 86), _hsl(hue, sat, 54)
        band = [_hsl(hue, sat, l) for l in (42, 31, 21)]
        light = _hsl(38, 54, 88)

    # The light: sun or moon, placed by the seed, never dead centre.
    lx = w * (0.16 + (d[4] / 255.0) * 0.68)
    ly = h * (0.16 + (d[5] / 255.0) * 0.28)
    lr = h * (0.055 + (d[6] % 40) / 900.0)

    # A 21:9 hero crops the same viewBox harder than a 16:9 card, so a
    # horizon that sits well on a card ends up near the bottom of a hero.
    # Raise it as the frame widens.
    wide = (w / h) > 2.0
    horizon = h * ((0.44 if wide else 0.56) + (d[7] % 24) / 180.0)

    # The light is appended LAST and inserted at the front, because where it
    # can go depends on what the motif draws. It used to be emitted first at a
    # seed-chosen height, and a skyline whose towers rose past it sliced the
    # circle into a crescent: on Lille's night plate the moon survived as a
    # sliver that reads, at the size a card is actually looked at, as a stray
    # character. A sun behind a smooth ridge is a sunset; a moon behind a
    # thin vertical bar is a rendering fault, and the difference is only
    # visible at consumption size.
    prims = []

    def ridge(y, amp, n, colour, jitter):
        pts = [(0.0, h)]
        for i in range(n + 1):
            pts.append((w * i / n, y - amp * (d[(jitter + i) % 32] / 255.0)))
        pts.append((float(w), h))
        return ("poly", pts, colour, 1.0)

    if motif == "peaks":
        # More layers on a wide crop: three ridges across a 21:9 hero leave
        # one enormous flat foreground, which is where the eye goes.
        layers = (((0.00, 0.30, 5), (0.08, 0.24, 7), (0.16, 0.18, 9), (0.26, 0.12, 11))
                  if wide else ((0.00, 0.30, 5), (0.10, 0.22, 7), (0.20, 0.14, 9)))
        for i, (drop, amp, n) in enumerate(layers):
            prims.append(ridge(horizon + h * drop, h * amp, n, band[min(i, 2)], 8 + i * 7))
    elif motif == "coast":
        # The headland count and depth were fixed at 4 and 0.10h for the life
        # of the motif, so the only thing distinguishing two coasts was where
        # the ridge jitter happened to land — 57 plates, 48 of them within 3%
        # of another and sharing its hue. Seeding the two numbers that were
        # constants is the smallest change that can move that, and it adds no
        # new shape.
        n_head = 4 + d[12] % 4
        amp = 0.07 + (d[13] % 70) / 900.0
        prims.append(ridge(horizon, h * amp, n_head, band[0], 8))
        prims.append(("rect", 0, horizon + h * amp, w, h, band[2], 1.0))
        # Under the light, and narrowing with distance from it — a
        # reflection somewhere else on the water is just a scratch.
        for i in range(3):
            bw = w * (0.13 - i * 0.032)
            prims.append(("rect", lx - bw / 2, horizon + h * (amp + 0.08 + i * 0.11),
                          bw, h * 0.011, light, 0.34 - i * 0.09))
        # ONE compositional variant, on about half of coasts: a headland
        # reaching into the water from whichever side the light is not on.
        #
        # Seeding the ridge count and depth above took coast from 125 twin
        # pairs to 82 and left it still the least varied family — because the
        # water is 40% of the frame and was identical on every plate. This is
        # the smallest thing that breaks that: one polygon, no new colour, no
        # new concept. Measured before keeping.
        if d[16] % 2:
            from_left = lx > w * 0.5
            reach = w * (0.22 + (d[17] % 90) / 400.0)
            drop = h * (0.10 + (d[18] % 60) / 700.0)
            base = horizon + h * amp
            pts = ([(0.0, base), (reach, base), (reach * 0.62, base + drop), (0.0, base + drop * 1.5)]
                   if from_left else
                   [(float(w), base), (w - reach, base), (w - reach * 0.62, base + drop),
                    (float(w), base + drop * 1.5)])
            prims.append(("poly", pts, band[1], 1.0))
    elif motif == "skyline":
        prims.append(ridge(horizon, h * 0.08, 6, band[0], 8))
        x, i = 0.0, 0
        while x < w:
            bw = w * (0.035 + (d[(9 + i) % 32] % 60) / 900.0)
            bh = h * (0.10 + (d[(15 + i) % 32] / 255.0) * 0.30)
            prims.append(("rect", x, horizon - bh, bw, bh + h,
                          band[1] if i % 2 else band[2], 1.0))
            x += bw + w * 0.012
            i += 1
    elif motif == "tower":
        prims.append(ridge(horizon, h * 0.07, 5, band[0], 8))
        # A tower needs a building under it. The first version was a thin
        # shaft with a sharp triangle on top and read, unmistakably, as an
        # arrow — or worse, a rocket. Wider shaft, shallower spire, and a
        # nave block beside it.
        tx = w * (0.28 + (d[9] / 255.0) * 0.38)
        # tw is a constant, and it was TRIED as a seeded value in the §6
        # variation experiment: 41 twin pairs became 42, which is noise. The
        # same minimal treatment that took coast from 125 twins to 25 does
        # nothing here, because a tower's similarity comes from the whole
        # composition — ridge, nave, shaft, spire, second ridge — and not
        # from one width. Reverted rather than kept, because a change with no
        # measured benefit is a change that only looks like progress.
        tw = w * 0.075
        th = h * (0.26 + (d[10] % 60) / 500.0)
        nave_w = tw * (1.9 + (d[11] % 30) / 40.0)
        nave_h = th * 0.42
        prims.append(("rect", tx + tw, horizon - nave_h, nave_w, nave_h + h * 0.2,
                      band[2], 1.0))
        prims.append(("rect", tx, horizon - th, tw, th + h * 0.2, band[2], 1.0))
        # The spire must not be wider than the shaft. A triangle overhanging
        # a narrow stick is an arrowhead, and two rounds of this drawing
        # read as a rocket before the overhang was removed. Flush sides, a
        # taller and narrower point, and a cornice where they meet.
        prims.append(("rect", tx - tw * 0.10, horizon - th, tw * 1.20, h * 0.012,
                      band[2], 1.0))
        prims.append(("poly", [(tx, horizon - th),
                               (tx + tw / 2, horizon - th - h * 0.115),
                               (tx + tw, horizon - th)], band[2], 1.0))
        prims.append(ridge(horizon + h * 0.16, h * 0.10, 7, band[1], 20))
    elif motif == "isles":
        # Four islands, always, at y = horizon + 0.05h + i*0.09h — a fixed
        # ladder. Only cx, rw and rh varied, so 19 destinations produced 8
        # distinct silhouettes and the nearest-neighbour distance was 0.001.
        # The count and the vertical placement were the constants; seeding
        # them is again the smallest change that adds no new shape.
        prims.append(("rect", 0, horizon, w, h, band[2], 1.0))
        n_isle = 3 + d[12] % 4
        for i in range(n_isle):
            cx = w * (0.10 + (d[(9 + i) % 32] / 255.0) * 0.8)
            rw = w * (0.05 + (d[(14 + i) % 32] % 50) / 700.0)
            rh = h * (0.03 + (d[(19 + i) % 32] % 40) / 700.0)
            cy = horizon + h * (0.04 + (d[(24 + i) % 32] / 255.0) * 0.30)
            prims.append(("ellipse", cx, cy, rw, rh, band[i % 2], 1.0))
    elif motif == "forest":
        prims.append(ridge(horizon, h * 0.09, 5, band[0], 8))
        x, i = 0.0, 0
        while x < w:
            tw = w * 0.026
            th = h * (0.10 + (d[(11 + i) % 32] / 255.0) * 0.16)
            base = horizon + h * 0.10
            prims.append(("poly", [(x, base), (x + tw / 2, base - th), (x + tw, base)],
                          band[1 + i % 2], 1.0))
            x += tw * 0.78
            i += 1
        prims.append(ridge(horizon + h * 0.22, h * 0.06, 6, band[2], 24))
    else:  # plain
        for i, (drop, amp) in enumerate(((0.00, 0.06), (0.13, 0.05), (0.26, 0.04))):
            prims.append(ridge(horizon + h * drop, h * amp, 4 + i * 2, band[i], 8 + i * 6))

    # Now place the light clear of everything the motif drew. `top` is the
    # highest painted point; the light sits in the band above it, keeping its
    # seed-chosen horizontal position so two plates from the same slug still
    # differ. Where the motif reaches so high there is no room — a tall tower
    # on a low horizon — the light moves aside instead of up.
    top = h
    for prim in prims:
        if prim[0] == "poly":
            top = min(top, min(y for _x, y in prim[1]))
        elif prim[0] == "rect":
            top = min(top, prim[2])
    # `top` is now the height of the clear sky. The first version of this fix
    # only pushed the light UP, with no floor, and on the tallest skylines
    # that jammed it against the frame and cropped it — Bucharest, Turin and
    # Amsterdam all gained a half-moon sitting on the top edge. A defect
    # traded for a different defect, found the same way: by looking at the
    # sheet at the size a card is actually seen.
    #
    # So the light is fitted to the sky rather than pushed out of the way. It
    # never takes more than a third of the available height, and it keeps a
    # clear margin at the top and at the silhouette. Where the sky is too
    # small to hold anything, the plate simply has no moon — which is a real
    # thing a night city looks like, and better than a sliver.
    lr = min(lr, top * 0.34)
    if lr >= h * 0.028:
        ly = min(max(ly, lr * 1.25), top - lr * 1.25)
        prims.insert(0, ("circle", lx, ly, lr, light, 0.5 if night else 0.75))

    # The doorway is NOT in the plate, and getting there took three tries
    # worth recording.
    #
    #   1. a stroked arch     — a line with two visible ends reads as a
    #                           scratch on the picture
    #   2. a linear-faded fill — the sides stayed at full value, so it read
    #                           as a pane of glass laid over the image
    #   3. a radial-faded fill — no edges at all, and now a soft bright blob
    #                           competing with the sun the plate already has
    #
    # The third was the useful failure. Every version was trying to get the
    # brand shape into all 988 illustrations, and a motif repeated into every
    # surface stops being a motif and becomes a tic. The doorway belongs in
    # the mark, the favicon and one deliberate place — used once, with
    # intent — not stamped over every landscape.
    return sky_a, sky_b, prims


def _rgb(c):
    return f"rgb({c[0]},{c[1]},{c[2]})"


def plate(seed, w=640, h=360, label="", motif=None):
    """A deterministic landscape for one slug, as SVG. Same slug, same plate."""
    sky_a, sky_b, prims = plate_shapes(seed, w, h, motif)
    uid = hashlib.sha256(f"{seed}{w}{h}".encode()).hexdigest()[:6]
    out = []
    for prim in prims:
        kind = prim[0]
        op = "" if prim[-1] >= 1.0 else f' opacity="{prim[-1]:.2f}"'
        if kind == "poly":
            pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in prim[1])
            out.append(f'<polygon points="{pts}" fill="{_rgb(prim[2])}"{op}/>')
        elif kind == "rect":
            _, x, y, rw, rh, colour, _a = prim
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{rw:.0f}" '
                       f'height="{rh:.0f}" fill="{_rgb(colour)}"{op}/>')
        elif kind == "circle":
            _, cx, cy, r, colour, _a = prim
            out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" '
                       f'fill="{_rgb(colour)}"{op}/>')
        elif kind == "ellipse":
            _, cx, cy, rx, ry, colour, _a = prim
            out.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" '
                       f'ry="{ry:.0f}" fill="{_rgb(colour)}"{op}/>')
    return (
        f'<svg class="plate" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label or seed)}" '
        f'preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="sky{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{_rgb(sky_a)}"/>'
        f'<stop offset="1" stop-color="{_rgb(sky_b)}"/>'
        f'</linearGradient>'
        f'<clipPath id="clip{uid}"><rect width="{w}" height="{h}"/></clipPath></defs>'
        f'<g clip-path="url(#clip{uid})">'
        f'<rect width="{w}" height="{h}" fill="url(#sky{uid})"/>'
        f'{"".join(out)}</g></svg>'
    )


# ── photographs ──────────────────────────────────────────────────────
#
# There are none yet. This is the layer that serves one when there is, and
# it exists now rather than later for a reason: the shape of the image
# pipeline decides what a licence audit costs two years from now, and by
# then there are thousands of files.
#
# The rules, all four enforced by tools/checks.py:
#
#   1. NO IMAGE WITHOUT PROVENANCE. A row in data/images.json must name the
#      photographer, the source and the licence. The validator refuses one
#      that does not, so "we will fill that in later" is not reachable.
#      An unlicensed photograph on a published page is the single most
#      expensive mistake a travel site can make, and it is always made by
#      accident.
#
#   2. SELF-HOSTED, NEVER HOTLINKED. Every file is served from our own
#      origin. The Content-Security-Policy is default-src 'none' with
#      img-src 'self' data:, so a hotlinked provider URL does not render at
#      all — the policy enforces the decision rather than a convention doing
#      it. Hotlinking also means the provider sees every reader.
#
#   3. ONE EAGER IMAGE PER PAGE. The hero is loading="eager"; everything
#      else is lazy and is never fetched until somebody scrolls. Page weight
#      is therefore one question per page rather than a total, and a card
#      grid of forty places costs nothing until it is looked at.
#
#   4. EVERY IMAGE CARRIES ITS OWN DIMENSIONS. width and height on the tag,
#      always, so the layout never shifts when the file arrives.
#
# Formats are AVIF, then WebP, then JPEG, in a <picture>; widths are a fixed
# ladder so the same file names can be generated ahead of time. Focal point
# is per image, because a 21:9 crop of a portrait photograph without one
# takes the sky.
#
# Until a slug has a row, plate() draws a landscape instead. The plate is
# the honest empty state, not the policy.

IMAGE_WIDTHS = (480, 800, 1260, 1800, 2400)
IMAGE_HOST = ""          # same origin. A CDN hostname goes here and in the CSP.


def picture(images, key, *, w, h, alt, eager=False, sizes="100vw", fallback_seed=None,
            fallback_motif=None):
    """A photograph for `key` if we hold one, otherwise a generated plate.

    Callers never branch on whether an image exists — they ask for one and
    get the best thing available. That is what makes the whole library
    adoptable one photograph at a time rather than in a big migration.
    """
    row = (images or {}).get(key)
    if not row:
        return plate(fallback_seed or key, w, h, alt, motif=fallback_motif)

    base = f"{IMAGE_HOST}/assets/img/{row['file']}"
    fx, fy = row.get("focal", [50, 50])

    def srcset(ext):
        return ", ".join(f"{base}-{n}.{ext} {n}w" for n in IMAGE_WIDTHS)

    credit = row["photographer"]
    return (
        f"<picture>"
        f'<source type="image/avif" srcset="{esc(srcset("avif"))}" sizes="{esc(sizes)}">'
        f'<source type="image/webp" srcset="{esc(srcset("webp"))}" sizes="{esc(sizes)}">'
        f'<img src="{esc(base)}-1260.jpg" srcset="{esc(srcset("jpg"))}" sizes="{esc(sizes)}" '
        f'alt="{esc(alt)}" width="{w}" height="{h}" '
        f'loading="{"eager" if eager else "lazy"}" '
        f'fetchpriority="{"high" if eager else "auto"}" decoding="async" '
        f'class="photo" style="--fx:{fx}%;--fy:{fy}%">'
        f'<figcaption class="credit">{esc(credit)} · {esc(row["licence"])}</figcaption>'
        f"</picture>"
    )


def chips(items, interests):
    out = []
    for slug in items:
        i = interests.get(slug)
        if not i:
            continue
        out.append(
            f'<a class="chip" href="/interests/{esc(slug)}"><span aria-hidden="true">{esc(i["icon"])}</span> {esc(i["name"])}</a>'
        )
    return '<div class="chips">' + "".join(out) + "</div>"


def crumbs(trail):
    """trail: [(label, href_or_None)] — the last item is the current page."""
    parts = []
    for i, (label, href) in enumerate(trail):
        if href and i < len(trail) - 1:
            parts.append(f'<a href="{esc(href)}">{esc(label)}</a>')
        else:
            parts.append(f'<span aria-current="page">{esc(label)}</span>')
    return f'<nav class="crumbs" aria-label="{esc(T("nav.aria.breadcrumb"))}">' + '<span class="sep" aria-hidden="true">/</span>'.join(parts) + "</nav>"


# Primary navigation, from the product specification. Seven items plus the
# two persistent utilities. The Fund moved to the footer when that spec
# arrived: it is a community surface rather than a way into the continent,
# and giving it a seventh of the masthead was overstating it.
NAV = [
    ("/discover", T("nav.discover"), "The map, the regions, the ways in."),
    ("/countries", T("nav.countries"), "Every country, region and destination."),
    ("/experiences", T("nav.experiences"), "What people actually do here."),
    ("/journeys", T("nav.journeys"), "Curated routes across the continent."),
    ("/plan", T("nav.plan"), "Days, budget, interests — an itinerary."),
    ("/stories", T("nav.stories"), "People, places, history, food, faith."),
    ("/events", T("nav.events"), "The European year, month by month."),
]

# Secondary navigation, also from the specification: everything a visitor may
# need to find and never has to see.
FOOTER_NAV = [
    ("/for-businesses", T("footer.for-businesses")),
    ("/for-tourism-boards", T("footer.for-tourism-boards")),
    ("/fund", T("footer.fund")),
    ("/europe-in", T("footer.motion")),
    ("/map", T("footer.map")),
    ("/themes", T("footer.themes")),
    ("/beyond-the-obvious", T("footer.beyond")),
    ("/my-europe", T("footer.myeurope")),
    ("/manifesto", T("footer.manifesto")),
    ("/about", T("footer.about")),
    ("/how-it-works", T("footer.how-it-works")),
    ("/method", T("footer.method")),
    ("/sources", T("footer.sources")),
    ("/api-docs", T("footer.api")),
    ("/contact", T("footer.contact")),
    ("/help", T("footer.help")),
    ("/accessibility", T("footer.accessibility")),
    ("/privacy", T("footer.privacy")),
    ("/terms", T("footer.terms")),
    ("/cookies", T("footer.cookies")),
]


# The Content-Security-Policy, in one place because there is one shell.
#
# Every directive is the most restrictive value the site can actually run
# under, and the reason each one holds is the architecture rather than
# discipline:
#
#   default-src 'none'  nothing is allowed that is not named below
#   script-src 'self'   there is no inline executable script anywhere. Page
#                       data is an inert application/json block instead; see
#                       jsondata(). This is the directive that pays for that.
#   style-src 'self'    checks.py fails the build on an inline <style>, so
#                       'unsafe-inline' is not needed for styles either
#   img-src 'self' data: there are no photographs; every illustration is an
#                       inline SVG element, and the favicon is a file
#   connect-src 'self'  the only fetch is /api/atlas.json, same origin
#   form-action 'self'  the two forms both submit to /plan
#   frame-ancestors 'none'  nothing here is meant to be framed. Header only:
#                       a browser ignores this directive in a meta tag
#   base-uri 'none'     a <base> tag would repoint every relative URL
#
# It ships as a meta tag because the site is static and the host is not
# chosen yet. site/_headers carries the same policy for a host that reads
# one, and checks.py asserts the two do not drift apart — a header and a
# meta tag saying different things is worse than either alone.
_CSP_COMMON = ("default-src 'none'; "
               "script-src 'self'; "
               "style-src 'self'; "
               "img-src 'self' data:; "
               "font-src 'self'; "
               "connect-src 'self'; "
               "form-action 'self'; "
               "base-uri 'none'")

# frame-ancestors is deliberately absent from the meta version. A browser
# ignores it there and says so in the console, and a directive that is
# ignored is worse than a missing one: it reads as protection in a source
# view while doing nothing. It lives in _headers only, where it works.
CSP_META = _CSP_COMMON
CSP_HEADER = _CSP_COMMON + "; frame-ancestors 'none'"

# Sent alongside it by any host that reads _headers. These cannot be set from
# a meta tag at all, which is why the file exists as well.
HEADERS = {
    "Content-Security-Policy": CSP_HEADER,
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "Cross-Origin-Opener-Policy": "same-origin",
    # Nothing on this site asks for a device capability, so every one of them
    # is refused rather than left at the browser's default.
    "Permissions-Policy": "geolocation=(), camera=(), microphone=(), payment=(), usb=(), interest-cohort=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def headers_file():
    """The same policy, for a host that reads a _headers file."""
    lines = ["/*"]
    for k, v in HEADERS.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines) + "\n"


# The mobile bottom bar, from the UI specification: Home, Explore, Map, Plan,
# Me. Five items and no more — a sixth turns a bar you can hit with a thumb
# into a row of targets you have to aim at.
#
# It is not a second navigation. Every destination here is already in the
# masthead or the footer; this is the same site reachable from where a thumb
# actually is. That matters because the masthead is sticky and the seven
# primary items wrap on a phone, which puts the important ones off the first
# line.
BOTTOM_NAV = [
    ("/", "Home", "M3 10.5 12 3l9 7.5V21H3z"),
    ("/discover", "Explore", "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm3.5 5.5-2 5-5 2 2-5z"),
    ("/map", "Map", "M9 3 3 5.5v15L9 18l6 3 6-2.5v-15L15 6zM9 3v15M15 6v15"),
    ("/plan", "Plan", "M4 5h16M4 12h16M4 19h10"),
    ("/my-europe", "Me", "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0"),
]


def bottom_nav(path):
    """The five-item thumb bar. Marked current by prefix, not by equality,
    so a city page lights Explore rather than nothing."""
    out = []
    for href, label, d in BOTTOM_NAV:
        if href == "/":
            here = path == "/"
        else:
            here = path == href or path.startswith(href + "/")
        # /europe/... is the Atlas, which is what Explore leads to.
        if href == "/discover" and (path.startswith("/europe/") or path.startswith("/countries")):
            here = True
        mark = ' aria-current="page"' if here else ""
        out.append(
            f'<a href="{href}"{mark}>'
            f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
            f'<span>{esc(label)}</span></a>'
        )
    return (f'<nav class="bottomnav" aria-label="{esc(T("nav.aria.bottom"))}">'
            + "".join(out) + "</nav>")


# ── social cards ─────────────────────────────────────────────────────
#
# og:image, and the reason it is a real problem rather than a meta tag.
#
# Every illustration on this site is an SVG generated at build time. The
# platforms that render a link preview want a raster, so without this a
# shared EuropeDoor link is a grey box with a title on it — which is a poor
# showing for a product whose whole argument is that discovery is visual.
#
# tools/lib/raster.py renders these from render.plate_shapes(): the same
# geometry the SVG comes from, never a second drawing. A PNG that diverged
# from the SVG would only ever be seen inside somebody else's product, so
# nobody here would notice.
#
# They cost about 23 ms each, which is 23 seconds across the site — too much
# to pay on every build for something that changes only when the plate
# algorithm does. So a plate is content-addressed by exactly the inputs that
# determine it, cached in assets/og/, and rendered only when missing. The
# build prunes anything no page asked for, so the cache cannot silently grow
# into a directory of orphans nobody can account for.
OG_W, OG_H = 1200, 630

# Filled by page(); read by build.py after every page is emitted.
OG_WANTED = {}


def og_key(seed, motif):
    return hashlib.sha256(f"{seed}|{motif}|{OG_W}x{OG_H}|v1".encode()).hexdigest()[:16]


def og_tags(seed, motif, alt):
    key = og_key(seed, motif)
    OG_WANTED[key] = (seed, motif)
    url = f"https://europedoor.com/assets/og/{key}.png"
    return (f'<meta property="og:image" content="{url}">'
            f'<meta property="og:image:width" content="{OG_W}">'
            f'<meta property="og:image:height" content="{OG_H}">'
            f'<meta property="og:image:alt" content="{esc(alt)}">'
            f'<meta name="twitter:card" content="summary_large_image">')


# ── structured data ──────────────────────────────────────────────────
#
# 988 correct pages that a search engine has to guess at. JSON-LD is what
# turns "a heading that says Bergen" into "a TouristDestination at 60.39N,
# 5.32E, inside Fjord Norway, inside Norway".
#
# The rule here is the same one the rest of the product runs on: emit only
# what we actually hold. That means several properties Google's rich-result
# documentation encourages are deliberately absent, and the absences are the
# interesting part:
#
#   aggregateRating   there are no reviews. A rating with no reviewers is a
#                     number we invented, and in structured data it is a
#                     number we invented in a machine-readable format.
#   offers / price    nothing is bookable and no price came from a supplier.
#   openingHours      the validator refuses the field, so there is nothing
#                     to serialise.
#   image             there are no photographs yet, and a plate is an SVG.
#                     Pointing at one would be claiming a photograph.
#   Event             our festivals are recurring fixtures with no dated
#                     instance. schema.org/Event requires startDate, and
#                     inventing one to satisfy a validator is exactly the
#                     failure mode this whole product is arranged against.
#
# A wrong rich result is worse than none: it is a claim, machine-readable,
# republished by somebody who cannot check it.

LD_PUBLISHER = {"@type": "Organization", "name": SITE_NAME, "url": "https://europedoor.com"}


def ld(*blocks):
    """Serialise JSON-LD blocks into one script element.

    application/ld+json is a data block, not executable script — the browser
    never runs it — so it does not need the Content-Security-Policy loosened.
    checks.py allows this type alongside application/json for that reason and
    no other.
    """
    items = [b for b in blocks if b]
    if not items:
        return ""
    payload = json.dumps(items[0] if len(items) == 1 else items,
                         separators=(",", ":"), ensure_ascii=False)
    payload = payload.replace("</", "<\\/")
    return f'<script type="application/ld+json">{payload}</script>'


def ld_breadcrumb(trail):
    """trail: [(label, href_or_None)] — the same list crumbs() is given, so
    the visible breadcrumb and the machine-readable one cannot disagree."""
    items = []
    for i, (label, href) in enumerate(trail, start=1):
        item = {"@type": "ListItem", "position": i, "name": label}
        if href:
            item["item"] = "https://europedoor.com" + href
        items.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": items}


def ld_place(kind, *, name, url, description, lat=None, lon=None, within=None,
             extra=None):
    out = {"@context": "https://schema.org", "@type": kind,
           "name": name, "url": "https://europedoor.com" + url,
           "description": description}
    if lat is not None:
        out["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon}
    if within:
        out["containedInPlace"] = within
    if extra:
        # Drop empties rather than serialising them. A property present with
        # no value says "we hold this" and then does not — which in a format
        # designed to be trusted is worse than the property being absent.
        # 200 destinations were emitting includesAttraction: [] before a
        # check caught it, because they have no places recorded yet.
        out.update({k: v for k, v in extra.items() if v not in (None, "", [], {})})
    return out


def ld_within(kind, name, url):
    return {"@type": kind, "name": name, "url": "https://europedoor.com" + url}


# The two worlds. A surface belongs to one of them and does not blend.
#
#   DISCOVER      light, warm, editorial, human — where people fall in love
#                 with Europe: stories, destinations, places, experiences,
#                 culture, food, photography-led browsing.
#   INTELLIGENCE  dark, graphite, quietly luminous — where people meet the
#                 machine: the map, the planner, My Europe, search, route
#                 and filter intelligence, EuropeDoor Guide.
#
# It is one attribute on <body> and the stylesheet does the rest, because the
# alternative — a second set of components for the dark world — is how a
# masthead comes to exist twice and diverge within a month. The tokens are
# rebound per world; every rule that consumes them is written once.
WORLDS = ("discover", "intelligence")


# Accents inside DISCOVER. cobalt is the default and needs no marker; the
# cultural accent is bound by the nav area the shell already sets. Only
# heritage — the pages about how this project knows what it claims — needs
# saying out loud, because those pages have no nav area of their own.
ACCENTS = ("", "heritage")


def page(title, body, *, path, description, trail=None, area=None, head_extra="", scripts=(), wide=False, ld_blocks=(), og=None, world="discover", accent=""):
    if world not in WORLDS:
        raise ValueError(f"{path}: unknown world {world!r}; it is one of {WORLDS}")
    if accent not in ACCENTS:
        raise ValueError(f"{path}: unknown accent {accent!r}; it is one of {ACCENTS}")
    nav = []
    for href, label, _blurb in NAV:
        mark = ' aria-current="page"' if area == label.lower() else ''
        nav.append(f'<a href="{href}"{mark}>{esc(label)}</a>')
    scripts_html = "".join(f'<script src="{esc(s)}" defer></script>' for s in scripts)
    footer_nav = "".join(f'<a href="{href}">{esc(label)}</a>' for href, label in FOOTER_NAV)
    full_title = title if title == SITE_NAME else f"{title} · {SITE_NAME}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{esc(CSP_META)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="https://europedoor.com{esc(path)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://europedoor.com{esc(path)}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
{og_tags(*og) if og else ''}
<link rel="stylesheet" href="/assets/css/europedoor.css">
<link rel="icon" href="/assets/door.svg" type="image/svg+xml">
{ld(*ld_blocks)}{head_extra}</head>
<body class="area-{esc(area or 'none')}" data-world="{world}"{f' data-accent="{accent}"' if accent else ''}>
<a class="skip" href="#main">{esc(T("skip"))}</a>
<header class="masthead">
  <div class="masthead-in">
    <a class="wordmark" href="/">
      {MARK}
      <span class="wordmark-text">europedoor</span>
    </a>
    <nav class="nav" aria-label="{esc(T("nav.aria.primary"))}">{"".join(nav)}</nav>
    <div class="navutil">
      <a class="navsearch" href="/search"><span aria-hidden="true">⌕</span> {esc(T("nav.search"))}</a>
      <a class="navmine" href="/my-europe">{esc(T("nav.myeurope"))}</a>
    </div>
  </div>
</header>
<main id="main" class="{'wide' if wide else ''}">
{body}
</main>
{bottom_nav(path)}
<footer class="footer">
  <div class="footer-in">
    <p class="footer-lede">{esc(T("footer.lede"))}</p>
    <nav class="footer-nav" aria-label="{esc(T("nav.aria.footer"))}">{footer_nav}</nav>
    <p class="footer-legal">{esc(T("footer.legal", operator=OPERATOR))}</p>
  </div>
</footer>
{scripts_html}</body>
</html>
"""


def section(title, body, *, id=None, lede=None, more=None, stage=None, tone=None):
    """A band.

    `stage` prints a small step marker above the heading. It exists for the
    homepage, where the specification asks for an emotional progression —
    open, discover, wonder, understand, plan, go — rather than a grid of
    thirty cards. A progression nobody can see is just an order, so the
    steps are named on the page.
    """
    idattr = f' id="{esc(id)}"' if id else ""
    toneattr = f" tone-{esc(tone)}" if tone else ""
    stagehtml = f'<p class="stage">{esc(stage)}</p>' if stage else ""
    ledehtml = f'<p class="lede">{esc(lede)}</p>' if lede else ""
    morehtml = f'<p class="more"><a href="{esc(more[1])}">{esc(more[0])} →</a></p>' if more else ""
    return f"""<section class="band{toneattr}"{idattr}>
  <div class="band-head">{stagehtml}<h2>{esc(title)}</h2>{ledehtml}</div>
  {body}
  {morehtml}
</section>"""


def card(href, kicker, title, blurb, *, seed=None, meta="", tall=False, motif=None):
    art = f'<div class="card-art">{plate(seed, 640, 360, title, motif=motif)}</div>' if seed else ""
    return f"""<a class="card{' tall' if tall else ''}" href="{esc(href)}">
  {art}
  <div class="card-body">
    <p class="kicker">{esc(kicker)}</p>
    <h3>{esc(title)}</h3>
    <p class="blurb">{esc(blurb)}</p>
    {meta}
  </div>
</a>"""


def grid(cards, cols=3):
    return f'<div class="grid cols-{cols}">' + "".join(cards) + "</div>"


def factlist(pairs):
    rows = "".join(
        f"<div class=\"fact\"><dt>{esc(k)}</dt><dd>{v}</dd></div>" for k, v in pairs if v
    )
    return f'<dl class="facts">{rows}</dl>'


def jsondata(id, obj):
    """Page data as an inert JSON block, read by the script that needs it.

    This used to be `<script>window.X = {...}</script>`. It worked, and it
    cost the site its Content-Security-Policy: one inline executable script
    anywhere means `script-src` has to allow `'unsafe-inline'`, which allows
    every injected script too — so a single convenience on one page disabled
    the defence on all 987.

    `type="application/json"` is not executed by the browser at all. The
    consumer does `JSON.parse(el.textContent)`. Same data, no execution, and
    `script-src 'self'` now holds with nothing to except.
    """
    payload = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    # Only `</` can end the block early; escaping it is the whole requirement.
    payload = payload.replace("</", "<\\/")
    return f'<script type="application/json" id="{esc(id)}">{payload}</script>'
