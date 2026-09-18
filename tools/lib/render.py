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
import os
import re
from urllib.parse import urlsplit

from .i18n import Strings

# One catalogue, loaded once. Adding a language means adding a file, not
# editing this one — which is the whole point of the exercise.
T = Strings("en")

SITE_NAME = "EuropeDoor"
# THE ORIGIN, ONCE. It was typed as a literal in six places — the sitemap,
# four JSON-LD blocks and the publisher record — and the Atom feed would have
# been the seventh. A canonical URL is a claim to a machine that cannot check
# it, and six copies of a claim are six chances for one of them to say
# something else the day the domain moves. `docs/brand-lock.md` says it does
# not move; that is a reason to write it once, not a reason not to.
ORIGIN = "https://europedoor.com"
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


def arch_path(w, h, rise=None):
    """An arch across a w x h frame, as an SVG path.

    THE SIGNATURE. The mark is a door: a frame with a semicircular head. An
    arch is also the one architectural form the whole continent shares —
    Roman, Romanesque, Gothic, Moorish, and every railway station built to
    look like all four. So the door stops being a logo shape and becomes the
    aperture: geography is seen THROUGH a doorway, on every family, at every
    scale. Structural, not illustrated, which is where brand metaphors last.

    Not a semicircle. A semicircular head on a 900x320 map would need a rise
    of 450 and there are only 320 to spend, so the head is struck across the
    full span at whatever rise the frame can afford — shallow and confident
    over a wide opening, which is what a mason does and what every bridge in
    Europe is.

    ELLIPTICAL, not circular, and that was a correction rather than a
    preference. The first version struck a circular segment,
    R = (rise^2 + (span/2)^2) / (2*rise). It is the more honest masonry and
    it cost the signature its third renderer: a circular segment cannot be
    written as a CSS border-radius, so the plates — whose containers are
    16/9, 3/4 and 21/9 while the viewBox is only ever 16/9 — had to be cut
    inside the drawing with `preserveAspectRatio="slice"` cropping the head
    flat on the wide ones and away entirely on the tall one. An elliptical
    head with rx = span/2 and ry = rise IS a border-radius:

        border-radius: 50% 50% 0 0 / <rise as % of height> ... 0 0

    so the same aperture is now cut three ways — SVG clipPath here, pixels in
    raster.arch_mask(), and the box itself in CSS — and all three describe one
    curve. The two forms differ by about 20px in 630 at the quarter span; the
    aperture surviving every aspect ratio is worth more than that.

    `rise` defaults to about a third of the height, clamped so a very wide
    frame keeps a shallow curve rather than a bulge.
    """
    if rise is None:
        rise = min(h * 0.34, w * 0.5)
    rise = max(1.0, min(rise, h * 0.9, w * 0.5))
    half = w / 2.0
    return (f"M0,{h:.1f} L0,{rise:.1f} "
            f"A {half:.1f},{rise:.1f} 0 0 1 {w:.1f},{rise:.1f} "
            f"L {w:.1f},{h:.1f} Z")


def arch_clip(uid, w, h, rise=None, x0=0.0, y0=0.0):
    """The arch as a <clipPath>, for clipping a map inside its own SVG.

    `x0`/`y0` are the viewBox origin, and they are not optional in practice:
    a route map's viewBox is the route's own bounding box and starts
    wherever the northernmost stop happens to be — often at a negative y.
    The first version built the path at 0,0 and clipped the entire drawing
    away, which renders as a black rectangle and looks exactly like a
    styling problem rather than a coordinate one.
    """
    off = f' transform="translate({x0:.1f},{y0:.1f})"' if (x0 or y0) else ""
    return (f'<clipPath id="arch-{esc(uid)}">'
            f'<path d="{arch_path(w, h, rise)}"{off}/></clipPath>')


def arch_rim(w, h, rise=None, x0=0.0, y0=0.0):
    """The wall's own edge, outside the reveal.

    A printed plate has a reveal you can see the THICKNESS of. The aperture
    had one hairline, which reads as a border rather than as an opening cut
    through something. Two lines — the outer in the page's own limestone,
    the inner in ink — is what an architectural opening actually shows: the
    face of the wall, and then the shadow of the cut. Drawn from the same
    `arch_path()` as the clip and the reveal, because three curves that
    disagree by a pixel is three signatures.
    """
    # TWO LINES, NOT ONE. A single hairline reads as a border round a
    # picture; a window cut in a wall shows the FACE of the wall and then the
    # shadow of the cut, and the eye reads depth from the pair. The outer is
    # the page's own limestone laid over the drawing's edge, the inner a fine
    # ink line just inside it.
    return (f'<path class="archrim" d="{arch_path(w, h, rise)}"/>'
            f'<path class="archrim inner" d="{arch_path(w, h, rise)}"/>')


def arch_edge(w, h, rise=None, x0=0.0, y0=0.0):
    """The cut edge of the aperture — the reveal.

    THE SIGNATURE ONLY EXISTED IN ONE COLOUR-SCHEME PREFERENCE.

    "Light wall, dark opening" is the whole reading of the door: the corners
    outside the arch show the page through, and a map figure paints no
    background so that they can. Measured on every arched map, as the
    contrast between the page the corners reveal and the ground inside the
    opening:

        light preference   17.94:1
        dark preference     1.03:1

    In the dark preference the wall is graphite and the opening is graphite,
    so there is no step and there is no door — on every page that draws one.
    And it cannot be fixed by darkening the opening: two near-blacks are
    always about 1:1, because luminance contrast collapses at that end of
    the scale. rgb(0,0,0) against the graphite ground is 1.11:1.

    So the door is read the other way a real one is: by its EDGE. A doorway
    cut in a wall is visible because the wall's surface stops, and the reveal
    catches the light. This is that line, and it is not a fourth definition
    of the curve — it calls the same arch_path() the clip does, so the
    check that asserts all the aperture's values agree still holds.
    """
    off = f' transform="translate({x0:.1f},{y0:.1f})"' if (x0 or y0) else ""
    return f'<path class="archedge" d="{arch_path(w, h, rise)}"{off}/>'


def esc(s):
    return html.escape(str(s), quote=True)


# IRREGULAR ONLY. Everything else takes an -s, which is the whole of the
# English this site needs.
_PLURALS = {"country": "countries", "city": "cities"}


def n_of(n, word, *, sep=" "):
    """A count and its noun, agreeing.

    MEASURED ON THE SHIPPED SITE BEFORE THIS EXISTED: "1 experiences" on 110
    pages, "1 nights" on 62, "1 cities" on 35, "1 destinations" on 25, "1
    regions" on 15, "1 places" on 8 and "1 countries" on 3. In meta
    descriptions that go to every search engine and every shared link, in the
    accessible name of a country map, in a destination's own facts table and
    in the figure caption under fifty country plates.

    Every one of them was a separate f-string writing `{n} things`, and each
    was individually invisible: the pages that trip it are the small ones —
    Monaco, San Marino, Liechtenstein, Andorra, a region with one destination
    — which is exactly the set nobody opens while checking a change.

    One function, and checks.py greps the built HTML for the fault so a
    hundred-and-first f-string cannot reintroduce it.
    """
    if n == 1:
        return f"{n}{sep}{word}"
    return f"{n}{sep}{_PLURALS.get(word, word + 's')}"


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
        # Night. The sky bottoms out near graphite and the light is a moon.
        # It used to be the electric accent, on the argument that a night
        # plate IS a dark ground and lime could not leak into the light
        # world from it. True, and it made 63 of the 319 cards carry an acid
        # green disc — a moon is a warm white, and the reason lime was there
        # was that the palette had one bright colour rather than that
        # anything about the picture wanted it. It went with the token.
        sky_a, sky_b = _hsl(hue, sat + 6, 9), _hsl(hue2, sat2, 21)
        band = [_hsl(hue, sat, l) for l in (18, 13, 9)]
        light = _hsl(44, 46, 86)
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
        # tw is a constant, and it was TRIED as a seeded value: 41 twin pairs
        # became 42, which is noise. Reverted rather than kept, because a
        # change with no measured benefit is a change that only looks like
        # progress — and an ablation later said why it could not have
        # worked. The shaft paints 4% of a card-sized plate. The two ridges
        # paint 68% of it between them, and both were constants.
        #
        #   plate-variation.py --ablate tower
        #
        #   layer          coverage   twins without it
        #   ridge-back        41.1%     44  (+3, noise — carries nothing)
        #   ridge-front       27.1%     35  (-6, it HID what varies)
        #   nave               6.0%     49  (+8)
        #   shaft              4.0%     47  (+6)
        #   cornice, spire      0.9%    41, 44
        #
        # Guessing had picked the 4% layer. The two numbers seeded below are
        # the ones the measurement named, and nothing else moved.
        tw = w * 0.075
        th = h * (0.26 + (d[10] % 60) / 500.0)
        nave_w = tw * (1.9 + (d[11] % 30) / 40.0)
        # Seeded: the nave is 6% of the plate and the ablation says that 6%
        # carries variation, but its height was pinned to the shaft's at a
        # fixed 0.42, so every tower was the same profile scaled. 32 -> 27.
        nave_h = th * (0.30 + (d[20] % 40) / 100.0)
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
        # The foreground ridge was pinned at 0.16h below the horizon on all
        # fifty plates. It is the only layer whose REMOVAL made the family
        # more varied — 41 twins down to 35 — because it is drawn last, over
        # the base of the nave and shaft, which is where the variation is.
        # A layer that occludes the varying part of a drawing is worse than
        # a constant: it subtracts. Seeding where it sits lets each plate
        # show a different amount of what actually differs. 41 -> 32.
        #
        # Seeding its amplitude and segment count instead — the treatment
        # that took coast from 125 twins to 25 — was tried first and moved
        # nothing at all: 41 -> 41. The same fix does not transfer between
        # motifs, and the ablation is what says which one to reach for.
        front_drop = h * (0.08 + (d[19] % 88) / 400.0)
        prims.append(ridge(horizon + front_drop, h * 0.10, 7, band[1], 20))
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


# THE FOCAL POINT IS A CLASS, NOT AN INLINE STYLE, AND THE FIRST VERSION WAS
# AN INLINE STYLE.
#
# `picture()` emitted `style="--fx:40%;--fy:30%"`, and `checks.py` refuses any
# `style="` attribute anywhere on the site — because CSP hashes do not apply
# to style attributes, so a single one would force `style-src` open on every
# page. The whole photograph pipeline was built, enforced and waiting, and it
# would have failed the build on the FIRST photograph it ever rendered. It
# survived because the register is empty: a code path nothing exercises is a
# code path nothing checks.
#
# That is the rule this repository already states one screen over — a rule
# that exists is not a rule that is inherited — and it was written by the
# same hand that wrote the refusal.
#
# Nine anchors rather than a percentage pair. It is what a photo editor
# actually reaches for, it is nine CSS rules instead of an open-ended set,
# and the loss against a free percentage is invisible on a cover crop. The
# register keeps the precise `focal` it was given; the quantisation happens
# here, at the one place that renders.
FOCAL_X = (("l", 0), ("c", 50), ("r", 100))
FOCAL_Y = (("t", 0), ("c", 50), ("b", 100))


def focal_class(fx, fy):
    """[x, y] percentages -> one of nine `f-<x><y>` anchors."""
    x = min(FOCAL_X, key=lambda p: abs(p[1] - fx))[0]
    y = min(FOCAL_Y, key=lambda p: abs(p[1] - fy))[0]
    return f"f-{x}{y}"


def photo(images, key, *, w, h, alt="", eager=False, sizes="100vw"):
    """A photograph if the register holds one, and NOTHING if it does not.

    `picture()` falls back to a generated plate, which is right on eight
    hundred destination pages and wrong on every editorial surface: eleven
    abstract plates in a column is placeholder art doing a picture's job, and
    that measurement is why they came off the homepage. An index hero or a
    lead item wants a photograph or an honest absence, never a landscape
    chosen by the hash of a slug.

    So this is the seam every editorial layout asks through. A page calls it,
    gets "" today, and lays itself out around the gap on purpose — the
    no-image state is the SHIPPED state rather than a fallback, and the day a
    row lands in data/images.json the same call returns the picture with no
    page change at all.
    """
    row = (images or {}).get(key)
    if not row:
        return ""
    return picture(images, key, w=w, h=h, alt=alt or row.get("alt", ""),
                   eager=eager, sizes=sizes)


def credit_html(row):
    """The attribution Pexels' terms require, from one register row.

    ONE IMPLEMENTATION, BECAUSE THIS ONE IS A LICENCE OBLIGATION. It lived
    inside `picture()` while `picture()` was the only way a photograph
    reached a reader. The planner broke that: `planner.js` writes an `<img>`
    for a leg whose stop the register holds a photograph of, and a runtime
    `<img>` is invisible to `checks.py`'s output-side guard — the one that
    refuses a published page referencing a file with no register row. So a
    second copy of this rule in JavaScript would be *a second chance to make
    its mistake* in the worst place this repository has one: nothing here
    would go red, and the breach would be of somebody else's terms.

    Both targets come from the row rather than from a provider table:
    `source` is the photo's own page, and the provider link is the ORIGIN of
    `licence_url`, so https://www.pexels.com/license/ gives
    https://www.pexels.com — the example the guideline itself uses.
    """
    parts = urlsplit(row["licence_url"])
    provider_url = f"{parts.scheme}://{parts.netloc}"
    link = ' rel="noopener" target="_blank"'
    return (f'Photo by <a href="{esc(row["source"])}"{link}>'
            f'{esc(row["photographer"])}</a> on '
            f'<a href="{esc(provider_url)}"{link}>{esc(row["licence"])}</a>')


def photo_credits(images, keys, more=""):
    """One credit line for a ROW of photographs, paid once.

    SIX IMPLEMENTATIONS OF THIS LINE, AND THE COMMENT ON THE SIXTH COUNTED
    FIVE OF THEM AS A FACT RATHER THAN FIXING IT: "the homepage's row of
    eight, the destination rail, the country and theme strips, five call
    sites spelling `sheetcred rowcred`". Four were the same loop written out
    four times; the other two joined the links inline. *A second
    implementation of a thing is a second chance to make its mistake*, and
    this one is a LICENCE OBLIGATION, which is why `credit_html` one function
    up is single by the same argument.

    AND ALL SIX SAID "Photographs" WHATEVER THEY WERE CREDITING. The
    homepage's reading band draws exactly one — the lead story's picture —
    so it published *"Photographs by Jean-Paul Wettstein on Pexels"* over a
    single photograph. A count cannot assume a plural, which this repository
    already records about a region holding one destination; here it was the
    one sentence on the band that a provider's terms require to be right.

    THE PLURAL IS THE NUMBER OF PHOTOGRAPHS AND THE LIST IS OF
    PHOTOGRAPHERS, which are different counts: five pictures by three people
    is "Photographs by A, B, C" and one picture by one person is
    "Photograph by A". So the names dedupe and the count does not.

    A KEY THE REGISTER DOES NOT HOLD IS SKIPPED, NOT A KeyError. Every caller
    passes the keys of a band it has already filtered, so that is unreachable
    on the real register — and `contact_sheet.py` builds the homepage with a
    register holding ONE row, which is the state this line exists to describe
    honestly. A credit names the photographs that are ON the page; a key with
    no row is a photograph that is not.
    """
    n, out, seen = 0, [], set()
    for k in keys:
        row = (images or {}).get(k)
        if not row:
            continue
        n += 1
        nm = row["photographer"]
        if nm in seen:
            continue
        seen.add(nm)
        out.append(f'<a href="{esc(row["source"])}" rel="noopener" '
                   f'target="_blank">{esc(nm)}</a>')
    if not out:
        return ""
    return ('<p class="sheetcred rowcred">Photograph'
            + ("s" if n != 1 else "") + " by " + ", ".join(out)
            + " on Pexels." + (" " + more if more else "") + "</p>")


def photo_href(images, key, width):
    """One derivative's URL, for a surface that cannot hold a <picture>.

    `picture()` is the only way a photograph reaches an HTML page and that
    stays true: it emits the whole ladder, the focal anchor and the credit
    the licence requires. An SVG `<image>` can hold none of those — it is a
    single href — so the Living Atlas, which clips a photograph to a
    country's own boundary, needs the URL on its own.

    IT TAKES A REGISTER KEY AND NEVER A URL, which is the whole point. The
    row is looked up here, exactly as `picture()` looks it up, so a caller
    cannot name a file the register does not hold — the rule that stopped
    `ed_photo` taking a `src` and becoming a second way into the library
    with none of the licence gate behind it. An unknown key returns "" and
    the caller draws nothing, which is the same answer `picture()` gives by
    falling back.

    JPEG rather than the AVIF the ladder leads with: `<image>` has no
    `<source>` and therefore no negotiation, so the one format every
    browser that renders SVG can decode is the honest choice. The step is
    the nearest one at or above the width asked for, and the name carries
    the original's hash, so the URL cannot change without the photograph
    changing — which is what the immutable header on /assets/ promises.
    """
    row = (images or {}).get(key)
    if not row:
        return ""
    step = min((n for n in IMAGE_WIDTHS if n >= width), default=max(IMAGE_WIDTHS))
    return f"{IMAGE_HOST}/assets/img/{row['file']}.{row['version']}-{step}.jpg"


def picture(images, key, *, w, h, alt, eager=False, sizes="100vw", fallback_seed=None,
            fallback_motif=None, credit=True):
    """A photograph for `key` if we hold one, otherwise a generated plate.

    Callers never branch on whether an image exists — they ask for one and
    get the best thing available. That is what makes the whole library
    adoptable one photograph at a time rather than in a big migration.
    """
    row = (images or {}).get(key)
    if not row:
        return plate(fallback_seed or key, w, h, alt, motif=fallback_motif)

    # CONTENT-ADDRESSED, because /assets/ is served immutable and that is a
    # promise about the URL. The tag is the original's own hash, written by
    # derive.py into every derivative's name, so replacing the photograph
    # replaces every URL and no reader is left with last year's picture.
    base = f"{IMAGE_HOST}/assets/img/{row['file']}.{row['version']}"
    fx, fy = row.get("focal", [50, 50])

    def srcset(ext):
        return ", ".join(f"{base}-{n}.{ext} {n}w" for n in IMAGE_WIDTHS)

    # THE CREDIT IS WHAT THE PROVIDER'S TERMS REQUIRE, AND IT IS DERIVED.
    # Pexels' API guidelines ask for two things and the first version of this
    # printed neither: "Whenever you are doing an API request make sure to
    # show a prominent link to Pexels" and "Always credit our photographers
    # when possible (e.g. 'Photo by John Doe on Pexels' with a link to the
    # photo page on Pexels)". It printed `photographer · licence`, plain text,
    # no link anywhere — so the pipeline would have published its first
    # photograph in breach of the terms it was fetched under.
    #
    # The gate's own question said this: "if a link to the provider or to the
    # photographer's profile or specific wording is required, the renderer
    # changes BEFORE the first fetch, not after". This is that change, made
    # while the register is still empty.
    #
    # Both targets come from the register row rather than from a table of
    # providers here: `source` is the photo's own page, required and checked
    # to be https, and the provider link is the ORIGIN of `licence_url`, so
    # https://www.pexels.com/license/ gives https://www.pexels.com — the
    # example the guideline itself uses. Nothing is authored per provider,
    # which is what keeps a second provider from needing a second renderer.
    # A CREDIT IS A LINK, SO A PICTURE CARRYING ONE CANNOT GO INSIDE A LINK.
    # An `<a>` may not contain an `<a>`: the parser closes the outer one at
    # the inner, so a thumbnail wrapped in a link came apart into three
    # siblings and a row of eight rendered as four pairs. It was latent on
    # the four homepage doors for the life of that band as well — they wrap
    # `picture()` in an `<a>` too, and with the register empty it returns a
    # plate with no credit, so nothing ever exercised it. A code path nothing
    # exercises is a code path nothing checks.
    #
    # `credit=False` is for a caller that places the attribution itself.
    # It does not make the credit optional: Pexels' terms require it, and a
    # caller that turns it off here owes one somewhere a reader can see.
    credit = credit and credit_html(row)
    return (
        f"<picture>"
        f'<source type="image/avif" srcset="{esc(srcset("avif"))}" sizes="{esc(sizes)}">'
        f'<source type="image/webp" srcset="{esc(srcset("webp"))}" sizes="{esc(sizes)}">'
        f'<img src="{esc(base)}-1260.jpg" srcset="{esc(srcset("jpg"))}" sizes="{esc(sizes)}" '
        f'alt="{esc(alt)}" width="{w}" height="{h}" '
        f'loading="{"eager" if eager else "lazy"}" '
        f'fetchpriority="{"high" if eager else "auto"}" decoding="async" '
        f'class="photo {focal_class(fx, fy)}">'
        + (f'<figcaption class="credit">{credit}</figcaption>' if credit else "")
        + "</picture>"
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
# TWENTY LINKS IN ONE FLAT ROW IS A LINK DUMP, and it was the last thing on
# all 1,033 pages. Every one the same weight and the same size, wrapping into
# two lines of near-identical text, so the register of the site — a public
# method, a source register, an accessibility statement, a fund that holds
# nothing — read as boilerplate. A reader looking for how the scores are
# computed scanned twenty items in no order.
#
# Four groups, and the grouping is what the links ARE rather than a tidy
# split: places to go next, what the project is and how to check it, who it
# is for besides a traveller, and the pages a reader needs when something is
# wrong. Same twenty links, same nav, same accessible name — the labels are
# not headings, because the homepage asserts its own <h2> count and a footer
# is not a band of the page.
FOOTER_GROUPS = [
    ("Explore", [
        ("/map", T("footer.map")),
        ("/themes", T("footer.themes")),
        ("/europe-in", T("footer.motion")),
        ("/beyond-the-obvious", T("footer.beyond")),
        # SEVENTEEN PAGES SHIPPED AND THEIR INDEX WAS A SERVER AUTOINDEX.
        # Nothing linked to /interests, which is exactly why no check caught
        # it: the link checker validates links that exist, and a missing
        # index is an absence.
        ("/interests", T("footer.interests")),
        ("/my-europe", T("footer.myeurope")),
    ]),
    ("The project", [
        ("/manifesto", T("footer.manifesto")),
        ("/about", T("footer.about")),
        ("/how-it-works", T("footer.how-it-works")),
        ("/method", T("footer.method")),
        ("/sources", T("footer.sources")),
        ("/api-docs", T("footer.api")),
    ]),
    ("Work with us", [
        ("/for-businesses", T("footer.for-businesses")),
        ("/for-tourism-boards", T("footer.for-tourism-boards")),
        ("/fund", T("footer.fund")),
    ]),
    ("Help & legal", [
        ("/contact", T("footer.contact")),
        ("/help", T("footer.help")),
        ("/accessibility", T("footer.accessibility")),
        ("/privacy", T("footer.privacy")),
        ("/terms", T("footer.terms")),
        ("/cookies", T("footer.cookies")),
    ]),
]

# Kept flat as well, because it is the set and several checks read it as one.
FOOTER_NAV = [row for _, rows in FOOTER_GROUPS for row in rows]


# ── the colophon's one fact ──────────────────────────────────────────
#
# A FOOTER ON 1,032 PAGES THAT SAID NOTHING ABOUT WHAT THIS IS. Twenty
# links, a sentence and a legal paragraph is the footer of any travel
# product; what no other travel product's footer can say is how much of
# Europe this one has actually written. The extent is the one fact that
# belongs in a colophon, and it is DERIVED on every build from the same
# documents the pages are built from — a figure typed here is the figure
# that was true two hundred destinations ago, which is a mistake this
# repository has already made on a live page.
#
# THE IMPORT IS LAZY AND THE ANSWER IS CACHED, for two reasons. `data.py`
# does not import this module and this module does not import it at the
# top, so nothing here can become a cycle; and `page()` is called 1,032
# times a build, where reading and counting the whole atlas once is free
# and doing it a thousand times is not.
_EXTENT = None


def extent_line():
    """Countries, regions, destinations, places — counted, never typed."""
    global _EXTENT
    if _EXTENT is None:
        from . import data as D
        d = D.load()
        n = [
            (len(d["countries"]), "countries"),
            (sum(len(c["regions"]) for c in d["countries"].values()), "regions"),
            (len(d["cities"]), "destinations"),
            (len(D.all_places(d["countries"])), "places"),
            (len(D.all_experiences(d["countries"])), "experiences"),
            (len(d["journeys"]), "journeys"),
        ]
        _EXTENT = " · ".join(f"{c:,} {label}" for c, label in n)
    return _EXTENT


# THE BROWSER PAINTS A BAR ABOVE THIS PAGE AND NOTHING TOLD IT WHAT COLOUR.
#
# On a phone the address bar and the task-switcher card take `theme-color`,
# and with none declared they take the platform default — so a site whose one
# band of signature colour is a cobalt masthead arrived on every Android
# phone with a white or black strip directly above it. The masthead is the
# element that appears on all 1,033 pages; the strip touching it is the first
# thing a reader sees and the only part of the page we were not colouring.
#
# TWO VALUES, BECAUSE THE BAR IS TRANSLUCENT. It is `--pine-deep` at 96%
# over whatever ground is behind it, and the ground differs by world: the
# DISCOVER world in the light preference is limestone, and DISCOVER-dark and
# INTELLIGENCE in both preferences are graphite. Composited:
#
# AND THEY WERE TYPED, SO THE PALETTE CHANGE LEFT THEM BEHIND. Bone & Pine
# moved the bar from cobalt to `--pine-deep` and these two stayed at the old
# composites, so every Android phone showed a blue strip directly above a
# green masthead — on all 1,034 pages, until the browser suite sampled the
# painted bar and named both values. That is the `vercel.json`/`HEADERS`
# arrangement working, and it is also the reason not to have the arrangement
# at all where the value can simply be computed: a hex that must equal a
# composite of two other hexes is a second implementation of them.
#
# Composited here from `docs/palette.json`, which is the register every
# other colour claim on this site is recomputed from, so moving a token
# moves the address bar with it and the suite's assertion becomes a check on
# the ARITHMETIC rather than on somebody's memory.
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(_REPO, "docs", "palette.json"), encoding="utf-8") as _f:
    _PALETTE = json.load(_f)


def _over(fg, bg, a):
    """`fg` at opacity `a` composited over `bg`, both as #rrggbb."""
    f = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a * f[i] + (1 - a) * b[i]):02x}" for i in range(3))


_HEX = {k: v["hex"] for k, v in _PALETTE["tokens"].items()}
# AND THE MASTHEAD STOPPED BEING A BAND OF SIGNATURE COLOUR, so the strip
# above it had to stop being one too. The non-home redesign made the bar the
# page's own paper — pine is spent on the mark and the current section rather
# than on the field behind all seven — and these two went on compositing
# `pine-deep`, so every Android phone showed a dark green strip above a cream
# page. The browser suite named both values in one run, which is the same
# assertion catching the same class of drift for the second time.
#
# The masthead paints `--paper` at 92% over the page, and the page is
# `--paper`: so the composite IS paper, in whichever preference. No blend is
# needed and stating one would be a third implementation of a colour.
THEME_COLOR_LIGHT = _HEX["bone-light"]
THEME_COLOR_DARK = _HEX["graphite"]


def theme_color_meta(world):
    """The bar above the page, per world.

    INTELLIGENCE is dark in BOTH colour-scheme preferences on purpose — the
    world says where the reader is, not how they like their screen — so it
    declares one value and no media query. A media-switched pair there would
    paint a light bar above a page that is never light.
    """
    if world == "intelligence":
        return f'<meta name="theme-color" content="{THEME_COLOR_DARK}">'
    return (f'<meta name="theme-color" content="{THEME_COLOR_LIGHT}" '
            f'media="(prefers-color-scheme: light)">\n'
            f'<meta name="theme-color" content="{THEME_COLOR_DARK}" '
            f'media="(prefers-color-scheme: dark)">')


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


# The version tag is part of the key because the drawing is an input to the
# picture and nothing else in the hash notices when it changes. v1 -> v2 is
# the arch aperture: without the bump every one of the 794 cached cards would
# have kept its pre-arch pixels under a filename that still looked current,
# and the only symptom would have been a shared link that no longer matched
# its page — invisible from here, because a card is rendered inside somebody
# else's product.
# v2 -> v3 IS THE PALETTE, AND THE TAG IS A THING SOMEBODY HAS TO REMEMBER.
# The comment above says so and it was not remembered. When the electric lime
# went out of the system it went out of the plate's night moon too — two
# guards on the stylesheet, a browser probe on the painted colour, and
# `css.lime` in the invariant register — and not one of them reads a PNG. The
# cards are keyed on the seed, the motif, the size and this tag, and none of
# those changed, so 96 of the 785 cached cards kept their acid-green moon
# under a filename that still looked current. Measured on the bytes on disk:
# #697d4b, 1,586 pixels, on Poprad's card among others.
#
# The tag is bumped and, because a tag is exactly the kind of promise that
# gets forgotten twice, `assets/og/cards.json` now records the inputs behind
# every cached file and `checks.py` re-renders a sample and compares BYTES.
# The next palette change that forgets this fails in the suite rather than on
# somebody else's timeline.
def og_key(seed, motif):
    return hashlib.sha256(f"{seed}|{motif}|{OG_W}x{OG_H}|v3-palette".encode()).hexdigest()[:16]


def og_tags(seed, motif, alt):
    key = og_key(seed, motif)
    OG_WANTED[key] = (seed, motif)
    url = f"{ORIGIN}/assets/og/{key}.png"
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

LD_PUBLISHER = {"@type": "Organization", "name": SITE_NAME, "url": ORIGIN}


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
            item["item"] = ORIGIN + href
        items.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": items}


def ld_place(kind, *, name, url, description, lat=None, lon=None, within=None,
             extra=None):
    out = {"@context": "https://schema.org", "@type": kind,
           "name": name, "url": ORIGIN + url,
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
    return {"@type": kind, "name": name, "url": ORIGIN + url}


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
# EIGHT ACCENTS, NOT TWO, AND THE MEASUREMENT IS WHY.
#
# `docs/palette.json` declares the accent at five per cent of a screen and
# the browser suite measures it at 0.3 — the one number in the ratio that
# disagrees with its instruction, and the design-direction audit's finding
# with a figure under it: "terracotta and atlantic are the entire
# art-directional difference between a magazine story and a country
# encyclopedia, and they are spent on an 11px kicker."
#
# Two accents over nine `area-` classes could not do better than that: 897 of
# the site's pages are one area, so binding colour there paints most of the
# atlas one colour whatever the hue. The family is the right grain and this
# is the hook that has it.
#
# The hues are an EXTENSION of the four this palette already had rather than
# a replacement for them — pine is the signature and is bound into a dozen
# contrast claims and the masthead — and they are generated in OKLCH at even
# hue steps so the set reads as a system rather than as eight picks. Every
# one clears 4.5 on limestone as text, carries a 3:1 graphic step and a
# ground tint that still holds its own ink at 4.7.
# THE OWNER'S FAMILY TABLE, and the names are what the colour MEANS rather
# than what it is: a region is territorial, a destination is human, a journey
# is movement, a fund project is natural. The eight colour-named accents this
# replaces were a wheel, and a wheel is a theme.
ACCENTS = ("", "heritage", "territory", "human", "movement", "natural")


# ── content-addressed assets ─────────────────────────────────────────
#
# CACHE-CONTROL SAID `immutable` ON A URL THAT WAS NOT.
#
# `/assets/(.*)` is served `public, max-age=31536000, immutable`, which is
# correct for the social cards — those are content-addressed, which is
# precisely what earns that header. The stylesheet and the scripts sat at a
# STABLE path under the same rule, and `immutable` means the browser is told
# never to revalidate for a year. So every returning visitor kept the
# stylesheet they first downloaded, and every visual change this site has
# ever shipped reached new visitors only.
#
# It is invisible from here: the repository is correct, the build is correct,
# the HTML that ships is correct, and the served page is styled by a file
# from months ago. That is the same shape as the _headers bug this repository
# already records — right in the repo, wrong in the response — and it is the
# reason a whole session of visual work could look like nothing had changed.
#
# The fix is the one the og cards already use: put the content hash IN THE
# NAME. A URL that changes when the bytes change may honestly be immutable;
# one that does not, may not.
ASSET_ROOT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "assets")
_ASSET_CACHE = {}


def asset(rel):
    """`css/europedoor.css` -> `/assets/css/europedoor.<hash>.css`.

    Falls back to the plain path when the file is missing, so a caller cannot
    silently emit a URL to nothing — `checks.py` fails on a dead link either
    way, which is the behaviour that finds this rather than hides it.
    """
    if rel not in _ASSET_CACHE:
        src = os.path.join(ASSET_ROOT, rel)
        if not os.path.exists(src):
            _ASSET_CACHE[rel] = "/assets/" + rel
        else:
            with open(src, "rb") as fh:
                h = hashlib.sha256(fh.read()).hexdigest()[:10]
            stem, ext = os.path.splitext(rel)
            _ASSET_CACHE[rel] = f"/assets/{stem}.{h}{ext}"
    return _ASSET_CACHE[rel]


def asset_map():
    """Every asset that gets a hashed name, as {source rel: published path}."""
    out = {}
    for sub in ("css", "js"):
        d = os.path.join(ASSET_ROOT, sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.endswith((".css", ".js")):
                rel = f"{sub}/{name}"
                out[rel] = asset(rel)
    out["door.svg"] = asset("door.svg")
    return out


# ── typography: the apostrophe ─────────────────────────────────────────
#
# 2,165 STRAIGHT APOSTROPHES ON 722 PAGES. Every possessive and every
# contraction on a site whose whole voice is a display serif was set with a
# typewriter quote — `atlas's`, `Europe's`, `Brunelleschi's`. It is the
# oldest tell of type nobody attended to, and it is the same family as the
# underline through every descender and the 224 pixels above the footer:
# nobody decided it, so it defaulted.
#
# THE PASS RUNS ON THE WHOLE DOCUMENT AND ONLY IN TEXT. Doing it inside
# `esc()` would corrupt every attribute and every URL that function also
# escapes; doing it at 37 call sites would miss the 38th. So it walks the
# emitted HTML, skips anything between `<` and `>`, and skips the contents
# of script, style, code and pre outright — the JSON-LD block and the inert
# data blocks are scripts, and a code sample means the character it prints.
#
# NARROW ON PURPOSE: only an apostrophe with a word character on both sides,
# which is every possessive and every contraction and nothing else. A
# leading apostrophe ('90s) and a quotation mark both need to know which end
# they are, and this atlas writes neither.
_SKIP = ("script", "style", "code", "pre", "textarea")


def curl(html):
    out, i, n = [], 0, len(html)
    skip_until = None
    while i < n:
        lt = html.find("<", i)
        if lt < 0:
            out.append(html[i:] if skip_until else _curl_text(html[i:]))
            break
        chunk = html[i:lt]
        out.append(chunk if skip_until else _curl_text(chunk))
        gt = html.find(">", lt)
        if gt < 0:
            out.append(html[lt:])
            break
        tag = html[lt:gt + 1]
        out.append(tag)
        name = tag[1:].split()[0].lower().rstrip(">/") if len(tag) > 1 else ""
        if skip_until:
            if name == "/" + skip_until:
                skip_until = None
        elif name in _SKIP and not tag.endswith("/>"):
            skip_until = name
        i = gt + 1
    return "".join(out)


def _curl_text(t):
    if "&#x27;" not in t and "'" not in t:
        return t
    return re.sub(r"(?<=\w)(?:&#x27;|')(?=\w)", "&#8217;", t)


def page(title, body, *, path, description, trail=None, area=None, head_extra="", scripts=(), wide=False, ld_blocks=(), og=None, world="discover", accent="", hero=False):
    if world not in WORLDS:
        raise ValueError(f"{path}: unknown world {world!r}; it is one of {WORLDS}")
    if accent not in ACCENTS:
        raise ValueError(f"{path}: unknown accent {accent!r}; it is one of {ACCENTS}")
    # SIXTEEN PAGES SHIPPED THE CONTINENT AND CLONED IT ZERO TIMES.
    #
    # `constel_defs()` inlines one thinned lod0 silhouette so that thirteen
    # theme glyphs cost ONE coastline. Nineteen call sites emit it and TWO of
    # them guard the call — `if facetart`, `if qshown` — which is the
    # fourteen-call-sites-forgot-the-motif shape exactly: two callers proving
    # the guard is needed while seventeen do not have it. Measured on the
    # built site, 18,806 bytes each on the homepage (12% of it), /themes
    # (37%), /experiences, /plan, nine macro pages and three motion pages —
    # about 301 KB of geometry nobody draws, on a site where page weight is
    # an invariant BECAUSE a page once shipped 90 KB of coastline under a map
    # and every gate stayed green.
    #
    # The strip is here rather than at the call sites for the reason `plate()`
    # takes its own transform: a caller cannot get half of it right, because a
    # caller no longer does any of it. It is a pure subtraction — the block is
    # `<svg class="constel-defs" width="0" height="0">`, paints nothing, and
    # is removed only when the document references neither id it provides.
    if 'class="constel-defs"' in body and "#constel-eu" not in body \
            and "#constel-beyond" not in body:
        i = body.index('<svg class="constel-defs"')
        j = body.index("</svg>", i) + len("</svg>")
        body = body[:i] + body[j:]
    # A LINK THE THUMB BAR ALSO CARRIES IS MARKED, and the set is derived
    # from BOTTOM_NAV rather than typed here, because a hand-listed copy of
    # another list is a list that is wrong one commit after somebody edits
    # the other one.
    #
    # WHY IT MATTERS: below 44rem the masthead's seven sections used to be
    # one line that scrolled sideways, on the reasoning that dropping them
    # would take them out of the tab order too. That reasoning is right
    # about five of them and was applied to all seven — /discover and /plan
    # are in the thumb bar, which appears at exactly the same 44rem
    # breakpoint, so hiding those two in the masthead hides nothing from
    # anybody. Measured before: at 390 the row's content was 552px in a
    # 366px box, so Plan, Stories and Events were WHOLLY off-screen behind
    # a horizontal swipe inside a 24px strip whose only affordance was a
    # 44px mask fade; at 320 Journeys was off too. Three of seven primary
    # sections reachable on a phone only by a gesture nobody discovers.
    nav = []
    thumbed = {href for href, _l, _d in BOTTOM_NAV}
    for href, label, _blurb in NAV:
        mark = ' aria-current="page"' if area == label.lower() else ''
        dup = ' class="inthumb"' if href in thumbed else ''
        nav.append(f'<a href="{href}"{mark}{dup}>{esc(label)}</a>')
    # Scripts are hashed for the same reason the stylesheet is. Callers pass
    # "/assets/js/my-europe.js"; the published URL carries the content hash.
    scripts_html = "".join(
        f'<script src="{esc(asset(s[len("/assets/"):]) if s.startswith("/assets/") else s)}" defer></script>'
        for s in scripts)
    footer_nav = "".join(
        f'<div class="fgroup"><p class="fghead">{esc(head)}</p>'
        + "".join(f'<a href="{href}">{esc(label)}</a>' for href, label in rows)
        + "</div>"
        for head, rows in FOOTER_GROUPS)
    full_title = title if title == SITE_NAME else f"{title} · {SITE_NAME}"
    return curl(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{esc(CSP_META)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
{theme_color_meta(world)}
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{ORIGIN}{esc(path)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{ORIGIN}{esc(path)}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
{og_tags(*og) if og else ''}
<link rel="stylesheet" href="{asset("css/europedoor.css")}">
<link rel="icon" href="{asset("door.svg")}" type="image/svg+xml">
<!-- ON EVERY PAGE, NOT ONLY ON /stories. Feed discovery is a browser and
     reader convention that looks at the document it is given, and a reader
     who wants to follow this desk is as likely to be standing on a
     destination page as on the index. One document, one feed, declared in
     the one place that emits <head>. -->
<link rel="alternate" type="application/atom+xml" href="/stories/feed.xml" title="EuropeDoor stories">
{ld(*ld_blocks)}{head_extra}</head>
<body class="ed-page ed-family-{ed_family(path)} area-{esc(area or 'none')}" data-family="{ed_family(path)}" data-world="{world}"{f' data-accent="{accent}"' if accent else ''}{' data-hero' if hero else ''}>
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
      <a class="navmine inthumb" href="/my-europe">{esc(T("nav.myeurope"))}</a>
    </div>
  </div>
</header>
<main id="main" class="{'wide' if wide else ''}">
{body}
</main>
{bottom_nav(path)}
<footer class="footer">
  <div class="footer-in">
    <div class="colophon">
      <a class="footmark" href="/" aria-label="{esc(SITE_NAME)}, home">
        {MARK}<span class="footmark-text">europedoor</span>
      </a>
      <p class="footer-lede">{esc(T("footer.lede"))}</p>
    </div>
    <p class="footer-extent">{extent_line()}</p>
    <nav class="footer-nav" aria-label="{esc(T("nav.aria.footer"))}">{footer_nav}</nav>
    <p class="footer-legal">{esc(T("footer.legal", operator=OPERATOR))}</p>
  </div>
</footer>
{scripts_html}</body>
</html>
""")


def section(title, body, *, id=None, lede=None, more=None, stage=None, tone=None,
            opens=False):
    """A band.

    `stage` prints a small step marker above the heading. It exists for the
    homepage, where the specification asks for an emotional progression —
    open, discover, wonder, understand, plan, go — rather than a grid of
    thirty cards. A progression nobody can see is just an order, so the
    steps are named on the page.
    """
    idattr = f' id="{esc(id)}"' if id else ""
    toneattr = f" tone-{esc(tone)}" if tone else ""
    # `opens` MARKS A CHANGE OF MOVEMENT, and it exists because the rhythm was
    # one constant. Measured across the built site: a destination page runs
    # eight bands with every gap at 104px and every head the same size in the
    # same place, a country page six — a table of contents rendered as a page.
    # A destination is not eight peers: what is here, how you reach it, what
    # to do once you have decided, and where the record came from. Space and
    # a rule are the only things that can say so without adding a word.
    toneattr += " opens" if opens else ""
    stagehtml = f'<p class="stage">{esc(stage)}</p>' if stage else ""
    ledehtml = f'<p class="lede">{esc(lede)}</p>' if lede else ""
    morehtml = f'<p class="more"><a href="{esc(more[1])}">{esc(more[0])} →</a></p>' if more else ""
    return f"""<section class="band{toneattr}"{idattr}>
  <div class="band-head">{stagehtml}<h2>{esc(title)}</h2>{ledehtml}</div>
  {body}
  {morehtml}
</section>"""


# ONE BAND HEAD, FOR EVERY FAMILY AT ONCE.
#
# `section()` is on three-quarters of the pages here and it prints a small
# h2 with a lede under it, left-aligned, identical on all of them — so the
# 2036 grammar applied to the OPENINGS and stopped at the first band, and a
# reader met a magazine head followed by six of the old ones. The
# alternative was rewriting nine hundred call sites.
#
# The band's head takes the section grammar instead: the title at display
# size with its lede beside it rather than under it, and an index down the
# left. THE INDEX IS DERIVED FROM POSITION — a number typed per call site
# is a number that is wrong the day somebody reorders the page, which is
# this repository's most repeated finding about counts — so the stylesheet
# counts them with a CSS counter and the markup carries none.
#
# `stage` is untouched. It is the homepage's named progression and the
# homepage is out of scope.
SECTION_GRAMMAR = True


def card(href, kicker, title, blurb, *, seed=None, meta="", tall=False, motif=None,
         level=3,
         art=None):
    """`blurb` may be None, for a tile that is a picture and a name.

    It is None in exactly one place — the eight ways-in tiles on the
    homepage, where the interests carry a name and a count and no prose,
    because none was ever written for them. The alternative was an empty
    <p class="blurb"></p>, which is the present-but-empty pattern this
    repository refuses in its JSON-LD for the same reason: a container that
    says "there is copy here" and then has none.
    """
    # `art` overrides the generated plate. It exists for the homepage, where
    # eleven abstract plates in a column read as placeholder art — which is
    # what they are — and are replaced by each tile's OWN destinations lit on
    # the continent. A plate is right for a card in a grid of like things; it
    # is wrong as the entire visual argument of a page.
    if art is not None:
        art = f'<div class="card-art card-map">{art}</div>'
    else:
        art = f'<div class="card-art">{plate(seed, 640, 360, title, motif=motif)}</div>' if seed else ""
    blurbhtml = f'<p class="blurb">{esc(blurb)}</p>' if blurb else ""
    return f"""<a class="card{' tall' if tall else ''}" href="{esc(href)}">
  {art}
  <div class="card-body">
    <p class="kicker">{esc(kicker)}</p>
    <h{level}>{esc(title)}</h{level}>
    {blurbhtml}
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


# ============================================================
# THE 2036 PAGE SYSTEM — EIGHT FAMILIES, ONE GRAMMAR
#
# The brief's own finding, and it is the right one: several families had
# converged on kicker -> h1 -> lede -> rows, and the answer is NOT to
# redesign forty-seven pages independently. It is to build eight families
# and map every page into one of them, so the site reads as one institution
# with different rooms.
#
# These are primitives in the sense the eleven already here are: a page
# builder composes them and changing one changes every page that uses it.
# They do not replace `section()`, `card()` or `row()` — a family that is
# already right keeps what it has, and this is the grammar a family adopts
# when it is rebuilt.
# ============================================================

ED_FAMILIES = ("atlas", "arrival", "discovery", "journey", "editorial",
               "time", "instrument", "institutional")


def ed_family(path):
    """Which of the eight rooms a page is in, from its own route.

    ONE TABLE, AND NO PAGE BUILDER CHANGES. Forty-seven builders each
    passing a family string is forty-seven chances for two pages in one
    family to disagree, and this repository has that failure recorded about
    the fourteen call sites that forgot to pass a motif. The route is what a
    family IS — /europe/<country>/<region>/<city> is an arrival because of
    where it sits, not because somebody typed "arrival" — so it is derived.

    Order matters twice. `/discover/` is the Discovery family and
    `/discover/<macro>` is a macro region, which the brief puts in Atlas;
    and `/experiences/<category>/<sub>` is a Time page while
    `/experiences/<category>` is Discovery.
    """
    p = "/" + (path or "").strip("/")
    seg = [s for s in p.split("/") if s]
    if not seg:
        return "institutional"
    head = seg[0]

    if head == "europe":
        # /europe/<country> · /europe/<c>/<region>      -> atlas
        # /europe/<c>/<r>/<city> · .../place/<x>        -> arrival
        return "arrival" if len(seg) >= 4 else "atlas"
    if head == "countries":
        return "atlas"
    if head == "discover":
        return "discovery" if len(seg) == 1 else "atlas"
    if head == "experiences":
        return "time" if len(seg) >= 3 else "discovery"
    if head in ("interests", "themes", "europe-in"):
        return "discovery"
    if head == "journeys":
        return "journey"
    if head == "stories":
        return "editorial"
    if head == "events":
        return "time"
    if head in ("map", "plan", "search", "my-europe"):
        return "instrument"
    return "institutional"


def ed_section_head(label, title, lede="", hid=""):
    """A numbered section head: the index beside the title, not above it.

    THE NUMBER IS THE COUNTER'S, NOT A CALLER'S, AND FOR THE LIFE OF THIS
    HELPER IT WAS BOTH. `section()` numbers its bands from a CSS counter —
    `main` resets `band`, every `.band` increments it — with the reason
    written on that rule: *a number typed per call site is wrong the day
    somebody reorders a page*. This helper was then written with the number
    as its FIRST ARGUMENT, so the redesign put a second numbering system on
    the same pages as the first.

    They did not merely disagree, they collided: measured across the built
    site, **753 of the 829 pages carrying a typed index printed a number a
    band counter also printed**. A place page opened "01 · NEARBY / The rest
    of Vienna" and then, immediately under it, "01 / Other places in
    Vienna". Nothing counted it, because each system was internally correct.

    So `.ed-section` increments the same counter and the index is drawn by
    CSS from it, exactly as `.band` already does. The label stays real text;
    only the digits are generated, which is what the sibling component had
    settled on before this one existed.

    `hid` GOES ON THE HEADING, AND LEAVING IT OUT BROKE TWO THINGS AT ONCE.
    `section()` emitted `<h2 id="...">` and every caller that moved to this
    head kept its `aria-labelledby` and its entry in the page's own contents
    row — so a destination page pointed at `#why-visit`, which no longer
    existed anywhere in the document. The section claimed a label it did not
    have, and the jump nav linked to nothing: the browser suite died on
    `document.querySelector(h)` returning null rather than reporting a
    failure, which is the one shape of regression a suite cannot describe.

    Neither half is visible in any count. A dangling `aria-labelledby` is not
    a missing name in the markup, it is a name that resolves to nothing, and a
    jump link to a missing id scrolls nowhere and raises nothing.
    """
    return (
        '<header class="ed-section-head">'
        f'<div><p class="ed-section-index">{esc(label)}</p></div>'
        f'<div><h2 class="ed-section-title"'
        + (f' id="{esc(hid)}"' if hid else "")
        + f'>{esc(title)}</h2>'
        + (f'<p class="ed-intro">{esc(lede)}</p>' if lede else "")
        + "</div></header>"
    )


def ed_photo(images, key, *, w=1800, h=1000, alt="", eager=False,
             ratio="wide", seed=None, motif=None, credit=True):
    """A large photograph, through the pipeline that owns provenance.

    IT NEVER TAKES A URL, which is the whole point of routing it here:
    `picture()` is the one function that knows whether the register holds a
    photograph for this key, emits the AVIF/WebP/JPEG ladder at five widths
    when it does, and draws the plate when it does not. A component that
    took `src` would be a second way into the library with none of the
    gate behind it.

    AND IT DOES NOT RETURN AN EMPTY STRING WHEN THE REGISTER IS EMPTY. The
    brief's version does, which would leave 826 of 837 surfaces as a hole in
    the page — and this repository has already measured that a slot waiting
    for a picture is honest and three hundred pixels of it is a hole. The
    interim answer is the drawing, exactly as it is everywhere else.
    """
    cls = {"wide": "ed-photo-wide", "landscape": "ed-photo-landscape",
           "portrait": "ed-photo-portrait"}.get(ratio, "ed-photo-wide")
    inner = picture(images, key, w=w, h=h, alt=alt, eager=eager,
                    sizes="(max-width: 52rem) 100vw, 70vw",
                    fallback_seed=seed or key, fallback_motif=motif,
                    credit=credit)
    return f'<figure class="ed-photo {cls}">{inner}</figure>'


def ed_opening(*, eyebrow, title, intro="", visual="", family="atlas"):
    """The stage every rebuilt family opens on: type beside a picture.

    `family` is on the SECTION as well as the body, because a page can hold
    a second opening — a journey inside an atlas page — and the grammar has
    to follow the content rather than the document.
    """
    return (
        f'<section class="ed-opening ed-family-{esc(family)}">'
        '<div class="ed-opening-copy">'
        f'<p class="ed-eyebrow">{esc(eyebrow)}</p>'
        f'<h1>{esc(title)}</h1>'
        + (f'<p class="ed-intro">{esc(intro)}</p>' if intro else "")
        + "</div>"
        f'<div class="ed-opening-visual">{visual}</div>'
        "</section>"
    )


def ed_split(*, title, body, media="", reverse=False):
    """Copy and a picture, alternating sides down a page."""
    return (
        '<section class="ed-section">'
        f'<div class="ed-split{" reverse" if reverse else ""}">'
        f'<div class="ed-split-copy"><h2>{esc(title)}</h2>{body}</div>'
        f'<div class="ed-split-media">{media}</div>'
        "</div></section>"
    )


def ed_rows(rows, *, numbered=True, level=3):
    """An index as a set of rules, not a grid of cards.

    THE NUMBER IS DERIVED AND NEVER PASSED. The brief's version takes a
    `number` per row, which is a figure typed into data — and a figure typed
    into data is the figure that was true two hundred destinations ago, which
    is this repository's most repeated finding about counts. It is the row's
    position, formatted here.

    AND `level` IS THE OUTLINE WHERE THE CLASS IS THE LOOK, which is the
    rule `card()` already takes an argument for. A row's name is an `<h3>`
    wherever the band's own `<h2>` is the level above it, and that is every
    caller but one: /countries nests its fifty country rows under a macro
    region's `<h3>`, so there they are `<h4>`. Nothing in WCAG fails on a
    flattened outline, which is why the site had a sixth of its pages
    starting at h3 with no h2 above them; what it costs is a reader
    navigating by heading being told two things are siblings when one is
    inside the other.
    """
    h = f"h{max(2, min(6, int(level)))}"
    out = []
    for i, row in enumerate(rows, 1):
        num = f"{i:02d}" if numbered else ""
        # A SUBLINE IS PART OF THE ROW AND A FLAG IS NOT PROSE. The brief's
        # row carries a title and a meta; every index on this site also has
        # a sentence that says what distinguishes this one from the fifty
        # under it, and three of them carry a travel advisory, which is a
        # STATE rather than a word and has its own tone.
        sub = (f'<p class="rowsub">{esc(row["sub"])}</p>'
               if row.get("sub") else "")
        flag = (f' <span class="tag advisory">{esc(row["flag"])}</span>'
                if row.get("flag") else "")
        out.append(
            f'<a class="ed-row" href="{esc(row["href"])}">'
            f'<span class="ed-row-number">{num}</span>'
            f'<div><{h}>{esc(row["title"])}{flag}</{h}>{sub}</div>'
            f'<span class="ed-row-meta">{esc(row.get("meta", ""))}</span>'
            '<span class="ed-row-arrow" aria-hidden="true">&#8594;</span>'
            "</a>")
    return '<div class="ed-rows">' + "".join(out) + "</div>"


# ============================================================
# PHOTOGRAPHY AS A CONTENT LAYER — SEVEN SCALES
#
# The failure these replace is not "too few photographs", it is every
# photograph the same size in the same box. Each of these is a different
# editorial job, and every one of them routes through `picture()`, which is
# the one function that knows whether the register holds a photograph for a
# key — so each draws the interim illustration until the library fills and
# none is a second way into the image system with the licence gate missing.
# ============================================================

def held(images, key):
    """Does the register hold a photograph for this surface?

    THE INTERIM FOR AN ABSENT PHOTOGRAPH IS NOT ALWAYS A DRAWING. `picture()`
    returns a generated plate when the register has no row, which is right on
    a card — a reader gets the best thing available and the library becomes
    adoptable one photograph at a time. It is wrong for the scales below.

    This site measured that once and acted on it: 189 `.card-art` elements
    and every one is a map, zero abstract plates on any page, because forty
    hash-drawn landscapes in a column is placeholder art doing a picture's
    job. A strip of eight plates or a full-bleed one would put that straight
    back, at the largest sizes on the site, on every family at once.

    So the big scales ASK. A composition that would be carried by a
    photograph renders when there is one and is omitted when there is not,
    and the page composes around its absence rather than filling it. That is
    the homepage doors' own rule — a slot waiting for a picture is honest,
    three hundred pixels of it is a hole — applied to seven more scales.
    """
    return bool((images or {}).get(key))


def held_any(images, keys):
    """The subset of these surfaces the register actually holds."""
    return [k for k in keys if held(images, k)]


# THE SLOTS ARE DECLARED, SO AN EMPTY ONE CAN SAY WHAT BELONGS IN IT.
#
# The first version of the scales below returned "" when the register held
# nothing, to keep hash-drawn landscapes off the page — a measured decision
# this repository already made once, 189 `.card-art` elements and every one
# a map. That is right about the plate and wrong about the hole: with 826
# of 837 surfaces empty it meant the redesign could not be SEEN, and a
# composition nobody can look at cannot be judged.
#
# A DECLARED PLACEHOLDER IS NEITHER. It is not a photograph and never
# pretends to be one: no <img>, no register row, nothing for the licence
# gate to refuse. It is the slot's own brief, rendered where the slot is —
# the purpose, what the picture must be OF, and the size it must be — which
# is exactly what `docs/image-purposes.json` already declares and what the
# directive asks for in its own words: mark the slot clearly and identify
# the required acquisition. The page composes, a reader sees the shape of
# the design, and the acquisition list is the page itself.
_SLOTNOTES = None


def slot_brief(key):
    """The one-line brief for an unfilled surface, from the declarations."""
    global _SLOTNOTES
    if _SLOTNOTES is None:
        _SLOTNOTES = {}
        try:
            import json as _json
            import os as _os
            # `render` HAS NO ROOT AND NEVER NEEDED ONE. Every other path
            # in this module is a URL; this is the first file it reads, so
            # the repository is derived from the module's own location
            # rather than from a constant somebody has to keep true.
            here = _os.path.dirname(_os.path.abspath(__file__))
            root = _os.path.dirname(_os.path.dirname(here))
            path = _os.path.join(root, "desk", "registry.json")
            with open(path, encoding="utf-8") as fh:
                doc = _json.load(fh)
            slots = doc.get("slots", {})
            for row in doc.get("purposes", []):
                spec = dict(slots.get(row.get("slot") or "", {}))
                spec.update({k: v for k, v in row.items() if v is not None})
                _SLOTNOTES[row["key"]] = spec
        except Exception:                                    # noqa: BLE001
            _SLOTNOTES = {}
    return _SLOTNOTES.get(key) or {}


def ed_slot(key, *, shape="wide", label=""):
    """An empty surface, saying what belongs in it.

    THE FIRST SENTENCE OF THE NOTE AND NOT THE WHOLE NOTE. A slot's brief is
    written for somebody reading the JSON and runs to a paragraph; rendered
    whole it would be the page. The desk already learned this — its own slot
    note pushed the search box nine hundred pixels down — and the answer is
    the same: the first sentence is the hint.
    """
    spec = slot_brief(key)
    note = (spec.get("note") or "").strip()
    first = note.split(". ")[0].rstrip(".") if note else ""
    want = ""
    if spec.get("min_width"):
        want = f'{spec["min_width"]}px {spec.get("orientation") or "landscape"}'
    cls = {"wide": "ed-slot-wide", "tall": "ed-slot-tall",
           "portrait": "ed-slot-portrait", "square": "ed-slot-square"}.get(
        shape, "ed-slot-wide")
    return (
        f'<div class="ed-slot {cls}" role="note" '
        f'aria-label="A photograph is not yet licensed for this surface">'
        f'<p class="ed-slot-key">Photograph · {esc(label or key)}</p>'
        + (f'<p class="ed-slot-note">{esc(first)}</p>' if first else "")
        + (f'<p class="ed-slot-spec">{esc(want)}</p>' if want else "")
        + "</div>")


def ed_bleed(images, key, *, alt, seed=None, motif=None, caption="",
             shape="tall", eager=False, only_if_held=True):
    """A picture that leaves the column. Used for a change of movement.

    It is the one image scale that is not inside the measure, which is what
    makes it read as a transition rather than as another illustration: the
    page stops, the continent or the city is the whole width, and the page
    resumes. `margin-inline: calc(50% - 50vw)` rather than a second wrapper,
    because a full-bleed element that needs its parent to cooperate is an
    element every caller can get wrong.
    """
    if only_if_held and not held(images, key):
        return ed_slot(key, shape="wide", label=alt or key)
    cls = {"tall": "ed-bleed-tall", "deep": "ed-bleed-deep"}.get(shape, "ed-bleed-tall")
    inner = picture(images, key, w=2400, h=1030, alt=alt, eager=eager,
                    sizes="100vw", fallback_seed=seed or key,
                    fallback_motif=motif)
    cap = f'<figcaption class="ed-caption">{esc(caption)}</figcaption>' if caption else ""
    return f'<figure class="ed-bleed {cls}">{inner}</figure>{cap}'


def ed_feature(images, key, *, title, body, alt, seed=None, motif=None,
               right=False, level=3, eager=False, only_if_held=False):
    """A dominant picture with its own words beside it.

    ASYMMETRIC ON PURPOSE — 1.35 against .65, not a half-and-half split. Two
    equal columns read as a layout; an unequal pair reads as a picture that
    has something to say about it. `right` alternates the side down a page,
    which is what stops three features in a row becoming a pattern.
    """
    if only_if_held and not held(images, key):
        return ed_slot(key, shape="square", label=alt or key)
    inner = picture(images, key, w=1600, h=1200, alt=alt, eager=eager,
                    sizes="(max-width: 52rem) 100vw, 55vw",
                    fallback_seed=seed or key, fallback_motif=motif)
    h = f"h{level}"
    return (
        f'<div class="ed-feature{" right" if right else ""}">'
        f'<figure class="ed-feature-media">{inner}</figure>'
        f'<div class="ed-feature-say"><{h}>{esc(title)}</{h}>{body}</div>'
        "</div>")


def _strip_note(it):
    """The sentence under a strip tile's name, or nothing at all."""
    note = (it.get("note") or "").strip()
    return f'<span class="ed-strip-note">{esc(note)}</span>' if note else ""


def ed_strip(images, items, *, limit=8):
    """A horizontal sequence: a visual journey rather than a grid.

    `items` are dicts of key, alt, label and optionally href and note. It
    SCROLLS rather than wrapping, because a sequence is read along — wrapping
    it into rows turns an order into a grid, which is the thing this whole
    system is replacing.

    `note` EXISTS BECAUSE A SET WAS BEING PRINTED TWICE TO SAY TWO THINGS.
    A place page rendered its town's other places as a strip — picture, name,
    link — and then again, directly underneath, as rows carrying the one
    thing the strip could not: the sentence saying what each one IS. Two
    bands, one set, on 220 of the 255 place pages. Neither band was wrong and
    neither was complete, so the answer is not to delete one: the tile takes
    the sentence and the second band goes.
    """
    out = []
    for it in items[:limit]:
        if not held(images, it["key"]):
            label = esc(it.get("label", ""))
            if it.get("href"):
                label = f'<a href="{esc(it["href"])}">{label}</a>'
            out.append(
                '<figure>'
                + ed_slot(it["key"], shape="portrait", label=it.get("label", ""))
                + f'<figcaption>{label}{_strip_note(it)}</figcaption></figure>')
            continue
        inner = picture(images, it["key"], w=900, h=1200, alt=it.get("alt", ""),
                        sizes="(max-width: 52rem) 60vw, 18rem",
                        fallback_seed=it.get("seed") or it["key"],
                        fallback_motif=it.get("motif"))
        label = esc(it.get("label", ""))
        if it.get("href"):
            label = f'<a href="{esc(it["href"])}">{label}</a>'
        out.append(f'<figure><div class="ed-shot">{inner}</div>'
                   f'<figcaption>{label}{_strip_note(it)}</figcaption></figure>')
    return f'<div class="ed-strip">{"".join(out)}</div>' if out else ""


def ed_mosaic(images, items, *, limit=3):
    """One dominant picture and two beside it. Never four equal tiles."""
    if len(items) < 3:
        # A MOSAIC IS A COMPOSITION OF THREE, and two pictures in a
        # three-cell grid is a grid with a hole in it. Below three it is not
        # a smaller mosaic, it is a different component's job.
        return ""
    out = []
    for i, it in enumerate(items[:limit]):
        big = i == 0
        if not held(images, it["key"]):
            out.append(ed_slot(it["key"], shape="square",
                               label=it.get("label", "")))
            continue
        inner = picture(images, it["key"], w=1400 if big else 800,
                        h=1400 if big else 800, alt=it.get("alt", ""),
                        sizes="(max-width: 52rem) 100vw, "
                              + ("40vw" if big else "28vw"),
                        fallback_seed=it.get("seed") or it["key"],
                        fallback_motif=it.get("motif"))
        out.append(f'<div class="ed-shot">{inner}</div>')
    return f'<div class="ed-mosaic-3">{"".join(out)}</div>' if out else ""


def ed_declare(images, key, *, statement, alt, seed=None, motif=None,
               only_if_held=True):
    """A typographic statement over a picture — the directive's own diagram.

    THE SCRIM IS NOT AN EFFECT, it is what makes the contrast a property of
    the design rather than of the photograph. This site has measured that
    once already, on the homepage hero: type over a drawing measured 4.36:1
    on the lit parchment of Iberia, under AA, because a ratio against a
    TOKEN is not the ratio a reader gets. 72% graphite composites to
    rgb(71,71,71) and bone on that is 9.2:1 whatever the picture does.
    """
    if only_if_held and not held(images, key):
        return ed_slot(key, shape="wide", label=alt or key)
    inner = picture(images, key, w=2400, h=1400, alt=alt,
                    sizes="100vw", fallback_seed=seed or key,
                    fallback_motif=motif)
    return (f'<figure class="ed-declare">{inner}'
            f'<figcaption class="ed-declare-say"><p>{esc(statement)}</p>'
            f"</figcaption></figure>")


# ── the commercial layer's one seam into a page ───────────────────────────
#
# TWO FUNCTIONS RATHER THAN THE BRIEF'S TEN COMPONENTS, and the reason is
# this repository's own rule: no new primitive until repeated structure has
# actually emerged. The ten differ in what they TARGET and what they SAY,
# which is data, and not in their box. Ten components is ten places for one
# disclosure to differ, which is the fourteen-call-sites-forgot-the-motif
# failure written into a commercial layer, where the cost of two of them
# disagreeing is a paid band a reader cannot tell from editorial.

def ad_disclosure(label):
    """The word that says this was bought, inseparable from the thing.

    The Stay layer already settled the principle — *a disclosure that only
    appears once we are paid is an advertisement with a conscience* — and the
    vocabulary is closed in `data/advertising.json`, so a campaign cannot
    invent "Recommended". `ads.creative_problems()` refuses a label that is
    not in it, and `checks.py` refuses the four ranking words on any page
    carrying a placement.
    """
    from . import ads as _ads
    if label not in _ads.disclosures():
        raise ValueError(
            f"{label!r} is not a declared disclosure: {_ads.disclosures()}")
    return f'<p class="kicker addisc">{esc(label)}</p>'


def ad_slot(path):
    """Everything bought on this page, in document order. Today: nothing.

    AN OFF SLOT EMITS ZERO BYTES — no container, no placeholder, no reserved
    height, no class a stylesheet could give a height to. That is the
    OPPOSITE of `ed_slot()` and for the opposite reason: there the reader is
    an editor and the declared photograph surface IS the acquisition list,
    here the reader is a traveller and a reserved advertising box on a page
    with no advertiser is this product advertising that it would like to
    carry advertising. §33 asks that nothing look as though ads are waiting
    to be inserted, and an empty string is the only version of that a check
    can hold: `checks.py` reads the built site for the marker and requires
    zero across all 1,032 pages, and the layout-shift sweep measures that
    nothing was reserved.

    A page builder calls this and does not decide anything. It cannot choose
    how many appear (the placement's `max_items` does), which surface it is
    (the path does), or whether anything appears at all (five conditions in
    the registry do) — because a selection rule spread across forty-seven
    builders is forty-seven chances for one page to carry two bands.
    """
    from . import ads as _ads
    ctx = _ads.context_for(path)
    out = []
    for c in _ads.get_eligible_ads(ctx):
        pl = _ads.placement(c.get("placement")) or {}
        cr = c.get("creative") or {}
        bad = _ads.creative_problems(cr)
        if bad:
            # A CREATIVE THAT FAILS VALIDATION IS NOT DRAWN AND NOT SILENT.
            # The build stops, because the alternative is shipping an
            # advertiser's unvalidated text to every reader of this page —
            # and this is the one family where the thing being refused
            # arrived from outside the repository.
            raise ValueError(
                f"campaign {c.get('slug')!r} has an invalid creative: "
                + "; ".join(bad))
        href = cr["destination_url"]
        out.append(
            f'<aside class="adband" data-placement="{esc(pl["slug"])}">'
            + '<div class="adband-in">'
            + ad_disclosure(cr["disclosure_label"])
            + f'<h2 class="mini">{esc(cr["headline"])}</h2>'
            + f'<p>{esc(cr.get("description") or "")}</p>'
            + f'<p><a href="{esc(href)}" rel="sponsored nofollow noopener" '
              f'target="_blank">{esc(cr.get("cta_label") or "Visit")}</a></p>'
            + "</div></aside>")
    return "".join(out)
