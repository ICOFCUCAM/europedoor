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
PLATE_HUES = (168, 196, 210, 32, 24, 14)

# Saturation is capped per hue. The warm end (brass, brick) goes muddy above
# about 30%, and the cool end goes to a swimming-pool blue above 34%.
PLATE_SAT = {168: 26, 196: 28, 210: 24, 32: 24, 24: 22, 14: 20}

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


def motif_for(interests):
    """The motif a place's own tagging asks for, or None to let the hash
    choose. Deterministic, and never random."""
    for want, motif in MOTIF_BY_INTEREST:
        if want in (interests or ()):
            return motif
    return None


def plate(seed, w=640, h=360, label="", motif=None):
    """A deterministic landscape for one slug. Same slug, same plate."""
    d = hashlib.sha256(seed.encode("utf-8")).digest()
    uid = f"{d[26]:02x}{d[27]:02x}{d[28]:02x}"
    if motif is None:
        motif = MOTIFS[d[0] % len(MOTIFS)]

    hue = PLATE_HUES[d[1] % len(PLATE_HUES)]
    hue2 = PLATE_HUES[(d[1] + 1 + d[2] % 3) % len(PLATE_HUES)]
    # Night for a fifth of them, and it is the seed that decides — so a
    # place does not change mood between builds.
    night = d[3] % 5 == 0
    sat, sat2 = PLATE_SAT[hue], PLATE_SAT[hue2]
    if night:
        sky_a, sky_b = f"hsl({hue} {sat + 6}% 13%)", f"hsl({hue2} {sat2}% 24%)"
        band = [f"hsl({hue} {sat}% {l}%)" for l in (21, 16, 11)]
        light = "hsl(44 48% 76%)"
    else:
        sky_a, sky_b = f"hsl({hue2} {sat2}% 78%)", f"hsl({hue} {sat}% 55%)"
        band = [f"hsl({hue} {sat}% {l}%)" for l in (43, 32, 22)]
        light = "hsl(42 62% 85%)"

    # The light: sun or moon, placed by the seed, never dead centre.
    lx = w * (0.16 + (d[4] / 255.0) * 0.68)
    ly = h * (0.16 + (d[5] / 255.0) * 0.28)
    lr = h * (0.055 + (d[6] % 40) / 900.0)

    # A 21:9 hero crops the same viewBox harder than a 16:9 card, so a
    # horizon that sits well on a card ends up near the bottom of a hero.
    # Raise it as the frame widens.
    wide = (w / h) > 2.0
    horizon = h * ((0.44 if wide else 0.56) + (d[7] % 24) / 180.0)
    parts = []

    def ridge(y, amp, n, colour, jitter):
        """One layer of the landscape, as a filled polygon along the top."""
        pts = []
        for i in range(n + 1):
            x = w * i / n
            k = d[(jitter + i) % 32]
            pts.append(f"{x:.0f},{y - amp * (k / 255.0):.0f}")
        return (f'<polygon points="0,{h} ' + " ".join(pts) + f' {w},{h}" fill="{colour}"/>')

    if motif == "peaks":
        # More layers on a wide crop: three ridges across a 21:9 hero leave
        # one enormous flat foreground, which is where the eye goes.
        layers = (((0.00, 0.30, 5), (0.08, 0.24, 7), (0.16, 0.18, 9), (0.26, 0.12, 11))
                  if wide else ((0.00, 0.30, 5), (0.10, 0.22, 7), (0.20, 0.14, 9)))
        for i, (drop, amp, n) in enumerate(layers):
            parts.append(ridge(horizon + h * drop, h * amp, n, band[min(i, 2)], 8 + i * 7))
    elif motif == "coast":
        parts.append(ridge(horizon, h * 0.10, 4, band[0], 8))
        # Water: flat, with two pale bands for the light's reflection.
        parts.append(f'<rect x="0" y="{horizon + h*0.10:.0f}" width="{w}" height="{h}" fill="{band[2]}"/>')
        # Under the light, and narrowing with distance from it — a
        # reflection somewhere else on the water is just a scratch.
        for i in range(3):
            yy = horizon + h * (0.18 + i * 0.11)
            bw = w * (0.13 - i * 0.032)
            parts.append(f'<rect x="{lx - bw/2:.0f}" y="{yy:.0f}" width="{bw:.0f}" '
                         f'height="{h*0.011:.0f}" fill="{light}" opacity="{0.34 - i*0.09:.2f}"/>')
    elif motif == "skyline":
        parts.append(ridge(horizon, h * 0.08, 6, band[0], 8))
        x = 0.0
        i = 0
        while x < w:
            bw = w * (0.035 + (d[(9 + i) % 32] % 60) / 900.0)
            bh = h * (0.10 + (d[(15 + i) % 32] / 255.0) * 0.30)
            parts.append(f'<rect x="{x:.0f}" y="{horizon - bh:.0f}" width="{bw:.0f}" '
                         f'height="{bh + h:.0f}" fill="{band[1] if i % 2 else band[2]}"/>')
            x += bw + w * 0.012
            i += 1
    elif motif == "tower":
        parts.append(ridge(horizon, h * 0.07, 5, band[0], 8))
        # A tower needs a building under it. The first version was a thin
        # shaft with a sharp triangle on top and read, unmistakably, as an
        # arrow — or worse, a rocket. Wider shaft, shallower spire, and a
        # nave block beside it.
        tx = w * (0.28 + (d[9] / 255.0) * 0.38)
        tw = w * 0.075
        th = h * (0.26 + (d[10] % 60) / 500.0)
        nave_w = tw * (1.9 + (d[11] % 30) / 40.0)
        nave_h = th * 0.42
        parts.append(f'<rect x="{tx + tw:.0f}" y="{horizon - nave_h:.0f}" '
                     f'width="{nave_w:.0f}" height="{nave_h + h*0.2:.0f}" fill="{band[2]}"/>')
        parts.append(f'<rect x="{tx:.0f}" y="{horizon - th:.0f}" width="{tw:.0f}" '
                     f'height="{th + h*0.2:.0f}" fill="{band[2]}"/>')
        # The spire must not be wider than the shaft. A triangle overhanging
        # a narrow stick is an arrowhead, and two rounds of this drawing
        # read as a rocket before the overhang was removed. Flush sides, a
        # taller and narrower point, and a cornice line where they meet.
        parts.append(f'<rect x="{tx - tw*0.10:.0f}" y="{horizon - th:.0f}" '
                     f'width="{tw*1.20:.0f}" height="{h*0.012:.0f}" fill="{band[2]}"/>')
        parts.append(f'<path d="M{tx:.0f} {horizon - th:.0f} '
                     f'L{tx + tw/2:.0f} {horizon - th - h*0.115:.0f} '
                     f'L{tx + tw:.0f} {horizon - th:.0f} Z" fill="{band[2]}"/>')
        parts.append(ridge(horizon + h * 0.16, h * 0.10, 7, band[1], 20))
    elif motif == "isles":
        parts.append(f'<rect x="0" y="{horizon:.0f}" width="{w}" height="{h}" fill="{band[2]}"/>')
        for i in range(4):
            cx = w * (0.10 + (d[(9 + i) % 32] / 255.0) * 0.8)
            rw = w * (0.05 + (d[(14 + i) % 32] % 50) / 700.0)
            rh = h * (0.03 + (d[(19 + i) % 32] % 40) / 700.0)
            parts.append(f'<ellipse cx="{cx:.0f}" cy="{horizon + h*(0.05 + i*0.09):.0f}" '
                         f'rx="{rw:.0f}" ry="{rh:.0f}" fill="{band[i % 2]}"/>')
    elif motif == "forest":
        parts.append(ridge(horizon, h * 0.09, 5, band[0], 8))
        x = 0.0
        i = 0
        while x < w:
            tw = w * 0.026
            th = h * (0.10 + (d[(11 + i) % 32] / 255.0) * 0.16)
            base = horizon + h * 0.10
            parts.append(f'<path d="M{x:.0f} {base:.0f} L{x + tw/2:.0f} {base - th:.0f} '
                         f'L{x + tw:.0f} {base:.0f} Z" fill="{band[1 + i % 2]}"/>')
            x += tw * 0.78
            i += 1
        parts.append(ridge(horizon + h * 0.22, h * 0.06, 6, band[2], 24))
    else:  # plain
        for i, (drop, amp) in enumerate(((0.00, 0.06), (0.13, 0.05), (0.26, 0.04))):
            parts.append(ridge(horizon + h * drop, h * amp, 4 + i * 2, band[i], 8 + i * 6))

    # The doorway, faintly, over everything: the illustration is seen through
    # it. Same geometry as the mark, scaled to the plate.
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
    # brand shape into all 987 illustrations, and a motif repeated into every
    # surface stops being a motif and becomes a tic. The doorway belongs in
    # the mark, the favicon and one deliberate place on the homepage — used
    # once, with intent — not stamped over every landscape.
    #
    # The plates are stronger without it.

    return (
        f'<svg class="plate" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label or seed)}" '
        f'preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="sky{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{sky_a}"/><stop offset="1" stop-color="{sky_b}"/>'
        f"</linearGradient>"
        f'<clipPath id="clip{uid}"><rect width="{w}" height="{h}"/></clipPath></defs>'
        f'<g clip-path="url(#clip{uid})">'
        f'<rect width="{w}" height="{h}" fill="url(#sky{uid})"/>'
        f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{lr:.0f}" fill="{light}" opacity="{0.5 if night else 0.75:.2f}"/>'
        f'{"".join(parts)}</g></svg>'
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


def page(title, body, *, path, description, trail=None, area=None, head_extra="", scripts=(), wide=False, ld_blocks=()):
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
<link rel="stylesheet" href="/assets/css/europedoor.css">
<link rel="icon" href="/assets/door.svg" type="image/svg+xml">
{ld(*ld_blocks)}{head_extra}</head>
<body class="area-{esc(area or 'none')}">
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


def section(title, body, *, id=None, lede=None, more=None):
    idattr = f' id="{esc(id)}"' if id else ""
    ledehtml = f'<p class="lede">{esc(lede)}</p>' if lede else ""
    morehtml = f'<p class="more"><a href="{esc(more[1])}">{esc(more[0])} →</a></p>' if more else ""
    return f"""<section class="band"{idattr}>
  <div class="band-head"><h2>{esc(title)}</h2>{ledehtml}</div>
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
