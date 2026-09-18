"""Every page EuropeDoor publishes.

Each builder returns (path, html). The build writes them; nothing here
touches the filesystem, so a page can be rendered and asserted against in a
test without a build directory existing.
"""

from __future__ import annotations

import hashlib
import itertools
import math
import re
from urllib.parse import quote

from . import ads as ADS
from . import cartography
from . import geo
from . import stay as staylib
from . import urls
from .render import (LD_PUBLISHER, ORIGIN, SITE_NAME, SITE_TAGLINE, arch_rim, card, chips, crumbs,
                     esc, factlist, grid, n_of,
                     jsondata, ld_breadcrumb, ld_place, ld_within, motif_for,
                     page, photo, picture, plate, section, arch_clip, arch_edge,
                     ed_opening, ed_photo, ed_rows, ed_section_head, ed_split,
                     ed_bleed, ed_declare, ed_feature, ed_mosaic, ed_strip, held,
                     ed_slot, photo_href, credit_html, ad_slot)
from .score import city_scores, country_scores, discoverability

HOME = ("Europe", "/discover")

# What a consumer of the public API may do with it. Stated in the document
# itself rather than only on a page, because a JSON file gets copied and the
# page it was linked from does not travel with it.
API_LICENCE = {
    "terms": ORIGIN + "/terms",
    "use": "Free to read, cache and build on, with attribution to EuropeDoor. "
           "Estimates are planning arithmetic, not quotes. Nothing here is "
           "entry, visa or safety advice.",
    "attribution": "EuropeDoor — europedoor.com",
}

# How long a checked fact stays checked. Currencies, cost bands and seasons
# move slowly; opening arrangements move fast. 365 days is the outer bound
# for the slow ones, and the fast ones are refused by the validator rather
# than reviewed, so this interval only ever has to hold the slow ones.
#
# The number exists so that "verified" cannot quietly become a permanent
# badge earned once. A check has an expiry date from the moment it is made.
REVIEW_DAYS = 365


def verification_of(c, today=None):
    """The verification state of one country, as data.

    Four states, not two. "Never checked" and "checked, and now due again"
    are different problems with different fixes, and collapsing them into
    "unverified" loses the distinction exactly when it starts to matter.
    """
    import datetime

    ch = c.get("checked")
    if not ch:
        return {"status": "unverified", "state": "never", "on": None, "by": None,
                "confidence": "low", "sources": [], "dueIn": None}
    today = today or datetime.date.today()
    on = datetime.date.fromisoformat(ch["on"])
    age = (today - on).days
    due = age >= REVIEW_DAYS
    srcs = ch.get("sources", [])
    # Confidence is derived, never authored: a field somebody can type is a
    # field somebody will type "high" into. Official sources and a recent
    # check earn it; nothing else does.
    official = sum(1 for x in srcs if x.get("kind") == "official")
    if due or not srcs:
        confidence = "low"
    elif official and ch.get("status") in ("officially-sourced", "business-verified"):
        confidence = "high"
    else:
        confidence = "medium"
    return {
        "status": ch.get("status", "editor-reviewed"),
        "state": "due" if due else "current",
        "on": ch["on"],
        "by": ch["by"],
        "confidence": confidence,
        "sources": [{"what": x["what"], "where": x["where"], "kind": x["kind"],
                     "url": x.get("url")} for x in srcs],
        "dueIn": REVIEW_DAYS - age,
    }


def haversine(a, b):
    """Kilometres between two {lat, lon} points. Used for realistic hops."""
    R = 6371.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p2 - p1
    dl = math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(h)))


def hop_note(km):
    """A distance, and nothing that does not follow from it.

    THIS USED TO NAME THE MODE AND THE DURATION, FROM A STRAIGHT LINE.
    "69 km — a local train or a short drive" was printed for Chamonix to
    Zermatt, which is 69 km as the crow flies, about 170 km on the ground,
    and a change at Martigny and Visp: most of a day, round a mountain
    range. Zakopane to Poprad is 37 km with the Tatras in between. The
    thresholds themselves were not wrong — Vienna to Bratislava really is a
    short train — they were being asked a question the input cannot answer.

    This atlas holds no road and no rail geometry. It holds two coordinates,
    and a great-circle distance between them is a FLOOR on the journey, never
    the journey. So the line says the distance and stops, and the sentence
    explaining what a straight line is worth is hoisted once above the list
    rather than implied thirteen times inside it — the same rule Discover
    Mode and the motion pages are built on.

    The planner prints a TIME beside the same distance and keeps doing so,
    because a scale is what a planner is for — but it no longer calls that
    time a minimum. The first attempt at this correction said "at least",
    which measured worse than the claim it replaced: the speed model knows
    nothing about whether a high-speed line exists, so on Paris to Marseille
    it reads 8h36m against a real four and a half.

    Restoring the mode claim is the one thing that would make this page make
    an assertion a reader could act on and be wrong about, which is the whole
    reason routing is on the roadmap. Until it is there, the page does not
    guess.
    """
    return f"{km} km"


def advisory_note(c):
    a = c.get("advisory")
    if not a:
        return ""
    heading = "Check government travel advice before planning anything here"
    return f"""<div class="note warn">
  <h2 class="mini">{esc(heading)}</h2>
  <p>{esc(a['note'])}</p>
  <p class="small">EuropeDoor keeps a page for every country in Europe, including the ones nobody
  should be travelling to right now. A page here is a record, not a recommendation, and
  countries at this level are excluded from the Journey Planner.</p>
</div>"""


def daily_line(data, c):
    """The daily band in euros and, where the country does not use the euro,
    in its own money — because "€90 a day" in Norway means nothing until you
    have seen it as kroner."""
    lo, hi = c["daily_eur"]
    cur = c["currency"].split(" ")[0]
    cx = data["taxonomy"].get("currencies", {})
    rate = cx.get("rates", {}).get(cur)
    line = f"€{lo}–{hi} per person"
    if rate and cur != "EUR":
        sym = cx.get("symbols", {}).get(cur, cur + " ")
        step = 10 if rate * lo < 2000 else 100
        rlo = int(round(lo * rate / step) * step)
        rhi = int(round(hi * rate / step) * step)
        line += (f' <span class="small">≈ {esc(sym)}{rlo:,}–{rhi:,} '
                 f'<a href="/help#currency">indicative</a></span>')
    return line


def checked_line(c):
    """Every country page says when its practical facts were last verified.
    For almost all of them the honest answer is "never", and printing that is
    the point: an unmarked page reads as a checked page."""
    v = verification_of(c)
    if v["state"] == "never":
        return ('<span class="tag advisory">not verified</span> '
                '<a href="/sources/freshness">why this matters</a>')
    when = f'{esc(v["on"])} by {esc(v["by"])}'
    if v["state"] == "due":
        return (f'{when} <span class="tag advisory">due for review</span> '
                '<a href="/sources/freshness">what that means</a>')
    return f'{when} · {esc(v["confidence"])} confidence'


def provenance_block(c):
    """Per-field provenance: which fact, checked where, and what kind of
    source that is.

    The specification asks for a source URL and a confidence score. A URL on
    its own is the weaker half — it says a page was consulted, not which
    claim it supports. So the unit here is the claim: this fact, against this
    body, of this kind. The URL is optional because some of the best sources
    for a cost band are not addressable (a price list in a window), and
    requiring one would push a checker towards whatever happened to have a
    link.
    """
    v = verification_of(c)
    if not v["sources"]:
        return ""
    kinds = {"official": "official body", "operator": "the operator",
             "municipal": "the municipality", "press": "published reporting",
             "editorial": "our own editor on the ground"}
    items = []
    for src in v["sources"]:
        where = (f'<a href="{esc(src["url"])}" rel="nofollow noopener">{esc(src["where"])}</a>'
                 if src.get("url") else esc(src["where"]))
        items.append(f'<li><strong>{esc(src["what"])}</strong> — {where} '
                     f'<span class="small">({esc(kinds.get(src["kind"], src["kind"]))})</span></li>')
    return (f'<h2 id="provenance" class="mt7">What was checked, and against what</h2>'
            f'<ul class="stack">{"".join(items)}</ul>'
            f'<p class="small">Checked {esc(v["on"])} by {esc(v["by"])}. This record expires '
            f'after {REVIEW_DAYS} days and then reads as due for review again — '
            f'<a href="/sources/freshness">the board</a>.</p>')


def bloc_line(data, c):
    names = data["taxonomy"]["blocs"]
    got = [names[b] for b in c.get("blocs", []) if b in names]
    return ", ".join(got) if got else "No EU or Schengen membership"


def months_line(data, keys):
    names = data["taxonomy"]["month_names"]
    return ", ".join(names[m] for m in keys)


# ── home ──────────────────────────────────────────────────────────────

def cut_band(lat0, lat1, lon, before, after):
    """A gradient axis running perpendicular to one meridian of the data cut.

    `data/geo/` is cut at 52°E and at 33°N because that is where this product
    stops writing about places, and under this conic the eastern cut runs from
    x=747 at 70°N to x=1024 at 40°N — a clean diagonal through Russia that
    reads as a rendering fault rather than as a frontier. The hero has faded
    along it since the hero was drawn; /map, /plan, /discover and /search — the
    instrument family, and the one map on this site that a reader OPERATES —
    showed it raw for the life of the dark world.

    Module level rather than nested inside the hero, because the geometry is a
    property of the PROJECTION and there is one of those. A second copy of
    these six lines is a second projection waiting to disagree.
    """
    a, b = MAPPROJ.xy(lat0, lon), MAPPROJ.xy(lat1, lon)
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    nx, ny = dy / n, -dx / n                 # perpendicular, pointing east
    return (mx - nx * before, my - ny * before,
            mx - nx * after, my - ny * after)


def dusk_stops(lo=0.0, hi=1.0, top=1.0):
    """Smoothstep in five stops, as opacity only — the colour is the caller's.

    `top` CAPS HOW DEEP THE FADE GOES, which is a different lever from how
    WIDE it is. Narrowing /map's fade was tried and refused — it makes the
    52°E cut a hard edge on the instrument — and that refusal answered a
    question about DOTS: the marks are drawn above the fade, so a destination
    near the cut keeps its own. Nobody asked about the COUNTRIES, and every
    one of them on /map is a link. Measured on the painted pixels against the
    painted sea, sampling a point inside each real polygon: Armenia 1.06,
    Azerbaijan 1.11, Türkiye 1.14, Russia 1.18 — at or under the 1.24 that
    `docs/palette.json` itself calls "not quiet, it is absent", and five
    countries under its declared 1.35 floor.

    So the cut stays as soft as it was and stops short of erasing what it
    crosses.

    A TWO-STOP GRADIENT HAS A CREASE AT EACH END AND THE EYE DRAWS A LINE
    ALONG IT. The ramp is linear, so its first derivative stops dead at each
    end, and human vision sharpens exactly that discontinuity — a Mach band.
    This picture was reported as having a hard edge three separate times while
    "soften the gradient" never fixed it, because widening a linear ramp moves
    the crease without removing it. Smoothstep has zero slope at both ends.
    """
    out = []
    for i in range(5):
        t = i / 4.0
        v = t * t * (3.0 - 2.0 * t) * top
        out.append(f'<stop offset="{lo + (hi - lo) * t:.4f}" '
                   f'stop-opacity="{v:.3f}"/>')
    return "".join(out)


# ── how far a data cut may reach ──────────────────────────────────────

DUSK_CEILING = 0.80

# HOW DEEP THE CUT MAY GO ON AN INSTRUMENT, AND IT IS NOW THE PICTURE'S OWN
# NUMBER. /map and /discover draw every country as a link, and
# `docs/palette.json` requires a country to clear the field by 1.35 with the
# reason written out: 1.24 is not quiet, it is absent.
#
# It was 0.50 over a reach of 330 units — WIDE AND SHALLOW, fitted against
# the painted pixels of a land that was #3f483f. Dimming a dark green by half
# moves almost nothing, so a band a third of the continent wide cost nothing
# and hid the cut. The moment the continent became pale mineral the same band
# washed Russia, Ukraine, Türkiye, the Caucasus and the whole Levant from
# bright to black across a third of the drawing, and ENDED ON A HARD DIAGONAL
# where the ramp ran out — which is the exact rendering fault a data fade
# exists to remove, arrived at from the other side. Every separation stayed
# green, because a separation is between two TOKENS and says nothing about a
# gradient painted over one of them.
#
# Narrow and deep is the picture family's answer and it is now this one's:
# `dusk_reach()` derives the width from the outermost destination east and
# south, so a place near the cut keeps its ground, and DUSK_CEILING is the
# depth. Refitted against the pale land, 0.80 leaves a dimmed country at
# 1.42:1 on the field and 0.83 takes it to 1.33 — so the ceiling the picture
# already uses is also the deepest this register allows, and the instrument
# stops carrying a second number for the same decision.
_DUSK_REACH = {}


def dusk_reach(data=None):
    """How wide each data-cut fade may be, measured against the destinations.

    THE FADE WAS EXTINGUISHING THE PLACES IT EXISTS TO KEEP LEGIBLE. `data/geo/`
    stops at 52°E and 33°N, and both cuts are straight lines through real land,
    so the drawing ramps into the graphite ground rather than ending. The widths
    of those two ramps — 330 units east, 130 south — were chosen by eye for
    atmosphere, and nothing ever asked what was underneath them. Measured on the
    homepage, over destinations this atlas writes a page about:

        Baku            100%        Paphos            92%
        Tbilisi          89%        Chania, Crete     83%
        Moscow           71%        Valletta          77%
        Helsinki         28%        Heraklion         85%

    Five countries — Azerbaijan, Georgia, Armenia, Cyprus and Malta — were
    effectively unlit on a picture whose caption says every country is a link,
    and Baku, which is a destination in this atlas, was solid graphite. That is
    exactly the fault `cartography.datacut` already records one file over: a
    fade that dims the thing it exists to keep legible has swapped one rendering
    fault for another.

    So the width is derived rather than chosen. `DUSK_CEILING` is the most a
    destination may be dimmed; smoothstep is inverted in closed form to find
    where on the band that value falls, and the band is stretched so the
    outermost destination sits exactly there. Add a destination further east
    and the fade narrows on the next build; there is no number to remember.

    THE CEILING ITSELF WAS RENDERED THREE WAYS AND LOOKED AT, because it is the
    one number here that is art direction rather than arithmetic. It trades one
    fault against the other: at 0.50 the band is 52 units and the terminator
    reads as a hard shadow edge cutting the continent, which is the rendering
    fault the fade exists to remove arrived at from the other side; at 0.86 it
    is 105 and Baku is nearly out again. 0.80 is 87 east and 102 south, and the
    measurement it buys is destinations dimmed past half: 46 of 319 before, 9
    after — Cyprus, Malta, Crete and Baku, which sit on the cut itself.

    ONLY THE HERO TAKES IT. /map draws the same two fades and keeps the wide
    reach, because its marks are drawn ABOVE the cut and stay lit: a destination
    near the cut keeps its dot, which is the rule `cartography.datacut` already
    states. The hero has no dots — its countries ARE the marks, and its names
    are under the fade — so it is the one drawing where dimming the ground
    dims the subject.

    Returns (east_before, east_after, south_before, south_after) in projection
    units. The `after` ends are the small clearances that carry the ramp past
    the cut itself, so the cut is fully covered rather than merely approached.
    """
    if "v" in _DUSK_REACH:
        return _DUSK_REACH["v"]
    if data is None:
        # The glyph families reach this without a `data` in hand. Loading it
        # here costs one read per build because the result is memoised, and
        # the alternative is threading the whole dataset through four drawing
        # functions that do not otherwise want it.
        from . import data as _D
        data = _D.load()
    a, b = MAPPROJ.xy(70.0, 52.0), MAPPROJ.xy(40.0, 52.0)
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    nx, ny = dy / n, -dx / n                     # perpendicular, pointing east
    ax, ay = MAPPROJ.apex()
    r33 = MAPPROJ.parallel_radius(33.0)
    east = south = 1e9
    for v in data["cities"].values():
        t = v["city"]
        x, y = MAPPROJ.xy(t["lat"], t["lon"])
        east = min(east, -((x - mx) * nx + (y - my) * ny))
        south = min(south, r33 - math.hypot(x - ax, y - ay))
    # The clearance past the cut. Small, and not zero: a ramp that reaches full
    # exactly ON the cut leaves the outermost pixel of parchment undimmed, which
    # is the bright hairline the hero already lost a commit to.
    ea, sa = 4.0, 3.0
    # Smoothstep inverted: the point on the band where the ramp equals the
    # ceiling. Closed form rather than a search, so the width is exact.
    v = min(max(DUSK_CEILING, 0.02), 0.98)
    t = 0.5 - math.sin(math.asin(1.0 - 2.0 * v) / 3.0)

    def width(d, a):
        return max((d - t * a) / (1.0 - t), 24.0)

    out = (width(east, ea), ea, width(south, sa), sa)
    _DUSK_REACH["v"] = out
    return out


_CUT_N = itertools.count(1)


def cut_fade(idprefix, w, h, reach=None, cls="mapcut", top=1.0):
    """The two data cuts, faded, for an instrument that draws the atlas.

    Painted rather than masked, because every country on these maps is a
    link and a masked group hit-tests as ONE region — the hero lost fifty
    doors to exactly that and the keyboard still worked, which is the kind of
    half-working that ships. Two rectangles, `pointer-events: none`, above the
    land and below the marks so a destination near the cut keeps its dot.

    The eastern edge is a LINEAR gradient perpendicular to the 52°E meridian,
    which is straight under a conic. The southern edge is a RADIAL one centred
    on the cone apex, because **a parallel is not a horizontal line on a
    conic**: the 33rd runs 116 units of rise between Tunisia and the Caspian,
    so a horizontal fade placed on the Tunisian end leaves the cut showing
    right across Anatolia. Both come from the projection's own constants.
    """
    # THE ID IS UNIQUE PER EMISSION, AND IT WAS NOT.
    #
    # Two callers pass the prefix "ih" — the index hero and `constellation()`
    # — so /stories, which draws both, shipped `id="ihedge"` and
    # `id="ihfoot"` TWICE. Invalid HTML: `getElementById` returns the first,
    # a fragment link is ambiguous, and the second `url(#ihedge)` resolves to
    # the FIRST drawing's gradient. On /stories the two gradients happened to
    # be identical — both take their coordinates from the projection rather
    # than from the viewBox — so nothing looked wrong, which is luck and not
    # design: the moment two drawings on one page pass a different `reach` or
    # `top`, the second silently takes the first's geometry.
    #
    # The defs CANNOT be hoisted and shared, which is the obvious repair:
    # `.datacut stop` and `.reachhead .datacut stop` colour the stops by
    # ANCESTOR, so a hoisted `<defs>` would take the wrong colour or none —
    # the recorded fault this function already has, from the other end. So
    # the id carries a counter. A prefix chosen per caller would be a guard
    # whoever adds the next drawing gets to choose, and `c_unique_ids` found
    # this one rather than anybody remembering.
    idprefix = f"{idprefix}{next(_CUT_N)}"
    eb, ea, sb, sa = reach or (330.0, 30.0, 130.0, 4.0)
    ex1, ey1, ex2, ey2 = cut_band(70.0, 40.0, 52.0, eb, ea)
    ax, ay = MAPPROJ.apex()
    r33 = MAPPROJ.parallel_radius(33.0)
    foot0, foot1 = (r33 - sb) / r33, (r33 - sa) / r33
    # THE DEFS GO INSIDE THE GROUP, AND THIS IS THE SECOND IMPLEMENTATION TO
    # GET IT WRONG. `cartography.datacut()` emitted them beside the group and
    # every stop took the SVG default — black — because the rule that colours
    # them is a class selector on the group. That was found and fixed one file
    # over; this function had the same shape and nobody looked, because /map
    # colours its stops by ID (`#mapedge stop`) and so was green. The moment a
    # second caller asked for the class-scoped `.datacut`, the southern ramp
    # came out as a black wash across North Africa on 21 index openings.
    # Inside the group, the selector's own claim is true of the markup.
    return (
        f'<g class="{cls}" aria-hidden="true">'
        f'<defs>'
        f'<linearGradient id="{idprefix}edge" gradientUnits="userSpaceOnUse"'
        f' x1="{ex1:.1f}" y1="{ey1:.1f}" x2="{ex2:.1f}" y2="{ey2:.1f}">'
        f'{dusk_stops(0.0, 1.0, top)}</linearGradient>'
        f'<radialGradient id="{idprefix}foot" gradientUnits="userSpaceOnUse"'
        f' cx="{ax:.1f}" cy="{ay:.1f}" r="{r33:.1f}">'
        f'{dusk_stops(foot0, foot1, top)}</radialGradient>'
        f'</defs>'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="url(#{idprefix}edge)"/>'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="url(#{idprefix}foot)"/>'
        f'</g>'
    )


# ONE PATTERN FOR THE LAND MARKUP, AND THERE WERE TWO.
#
# `geo.landmass()` emits a country as `<path … d="…"><title>Name</title>`,
# and the hero reads that back twice — once to build `NameGround`, which is
# every country's real polygon, and once to order the names by drawn area.
# Both were written as the literal `<path d="…">`, and the day the land
# paths gained an `id` so the Living Atlas could clip a photograph to a
# country with a `<use>` rather than a second copy of its ring, one of them
# was widened and the other was not: the first returned fifty shapes and the
# second returned fifty indices into a list of ZERO, and the build stopped
# on an IndexError two hundred lines from either.
#
# Before that it was worse than a crash. With BOTH narrow, the name layer
# was simply empty — fifteen country names left the most-seen page on the
# site and nothing failed, because an unlabelled drawing and a drawing whose
# labels all missed look identical. *A second implementation of a thing is a
# second chance to make its mistake*, and the answer on this repeat is the
# one that worked the last three times: stop having a second implementation.
LAND_PATH = re.compile(
    r'<path[^>]*\sd="([^"]*)"[^>]*><title>([^<]*)</title></path>')


# ── THE LIVING PHOTOGRAPHIC ATLAS ────────────────────────────────────
#
# THE COUNTRY'S OWN BOUNDARY IS THE APERTURE. Every other photographic
# surface on this site is a rectangle — a bleed, a strip tile, a window —
# and that is right for a photograph standing on its own. On the hero it
# would be a picture BESIDE a map, which is what every travel product
# already is. Clipped to the country it belongs to, the same photograph
# becomes geography: you read WHERE before you read WHAT, and the door in
# the headline is the shape of France.
#
# NOTHING HERE IS A SECOND CARTOGRAPHY. The clip is `geo.landmass()` run
# for one slug with the hero's own parameters, so the outline of the
# aperture is the same path, from the same file, at the same thinning as
# the country drawn under it — a second copy would drift by a tenth of a
# unit and show as a fringe, which is the black-fringe failure this
# drawing already records about two levels of detail stacked.
#
# AND IT IS NOT A SECOND WAY INTO THE LIBRARY. Every frame is a REGISTER
# KEY resolved by `render.photo_href()`, which reads the same row
# `picture()` reads; a component that took a URL would be a photograph
# with none of the licence gate behind it. The credit each frame needs —
# the photographer, their page, and the prominent link to the provider
# that Pexels' guidelines require — is generated from that row and shown
# with the frame it belongs to.
#
# THE SET IS DERIVED, AND THE TWO RULES ARE THE ONES THIS PAGE ALREADY
# HAS. One per macro region, because this atlas holds no ranking and
# refuses one on /for-businesses in those words — the question is where
# will you go, so the answer is SPREAD. And an advisory country is never
# offered, because /api/atlas.json is stripped of them at build time and a
# derived selection is not automatically an honest one.
#
# WHICH country per macro region is decided by the LIBRARY rather than by
# taste: the one with the most photographed destinations, ties broken
# alphabetically. That is a measurement of what we can actually show, and
# it moves on its own as the register fills.
LIVING_MAX = 6
LIVING_FRAMES = 5


def living_atlas(data, images, doc):
    """The featured countries, their geometry, and their photographs.

    Returns a list of dicts in cycle order. Each carries the clip path, the
    box to draw the photograph in, and the frames — the country's own
    picture first, then its photographed destinations in the atlas's own
    order, each with the line that says what it is and the credit its
    licence requires.
    """
    macro_of = {}
    for m in data.get("macros", []):
        for cs in (m.get("countries") or []):
            macro_of[cs if isinstance(cs, str) else cs.get("slug")] = m["slug"]

    shots = {}
    for cid, e in data["cities"].items():
        key = "city:" + cid
        if key in images:
            shots.setdefault(cid.split("/")[0], []).append((cid, e, key))

    # AND THE APERTURE HAS TO BE BIG ENOUGH TO HOLD A PICTURE, WHICH IS A
    # MEASUREMENT AND NOT A PREFERENCE. The first version of this ranked on
    # the library alone — most photographed destinations, one per macro
    # region — and returned Croatia, Austria, Belgium, Finland, Armenia and
    # Estonia. Every one of those is a true answer to the question it was
    # asked and four of them are 34 to 70 units across on a 1,120-unit
    # frame: a photograph clipped into Belgium renders about 40 pixels wide
    # at 1280 and is a smudge with a coastline. That is the map-label
    # failure in another family — placed, correct, and not resolvable into
    # anything a reader can read.
    #
    # So the first filter is the DRAWN AREA of the country in this frame,
    # which is the same quantity `min_units` already uses one function over,
    # and the set is the largest such country per macro region.
    #
    # AND THE LIBRARY DECIDES THE SEQUENCE, NOT THE CAST — which is the
    # second thing measuring changed. Requiring a photographed DESTINATION
    # to be featured returned six countries nobody would open an atlas on,
    # because the 65 city photographs the register holds are clustered where
    # the round-robin happened to reach and every large, familiar country
    # has none: Portugal, Türkiye, Norway, Spain, Italy, Greece, Germany and
    # the United Kingdom are all at zero. Every one of them has its OWN
    # photograph, so every one of them can be an aperture today; what varies
    # is how many frames it cycles through. A country with one photograph
    # shows one and a country with five shows five, and the sequence grows on
    # its own as `stage: fill` reaches the rest.
    #
    # AREA RATHER THAN THE BOUNDING BOX, and the box is what the first
    # version measured. Portugal's box is the widest in Europe because it
    # contains the Azores and Madeira — 265 units of mostly Atlantic — so
    # ranking on it put a sliver and two island groups at the top of the
    # cast. A BOUNDING BOX IS NOT A COUNTRY, which is the rule this
    # repository already had about placing a name on one, arriving here
    # about choosing which country to photograph at all.
    area = {}
    paths = {}
    for c in data["countries"].values():
        slug = c["slug"]
        if ("country:" + slug) not in images:
            continue
        if (c.get("advisory") or {}).get("level"):
            continue
        if macro_of.get(slug) is None:
            continue
        # THE SAME PATH, NOT A COPY OF IT. `only` draws one country with the
        # hero's own thinning, so the aperture and the country under it are
        # the identical geometry — a second simplification would differ by a
        # tenth of a unit and show as a fringe along every frontier, which is
        # this drawing's own recorded failure about two levels of detail
        # stacked.
        _ctx, ours = geo.landmass(MAPPROJ, HERO_VIEW, doc=doc, thin_units=1.8,
                                  min_units=6.0, only={slug})
        d = "".join(re.findall(r'<path[^>]*\sd="([^"]*)"', ours))
        if not d:
            continue
        a = 0.0
        for sub in d.split("Z"):
            nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", sub)]
            pts = list(zip(nums[0::2], nums[1::2]))
            if len(pts) < 3:
                continue
            a += abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1]
                         for i in range(len(pts)))) / 2.0
        paths[slug] = d
        area[slug] = a

    best = {}
    for c in data["countries"].values():
        slug = c["slug"]
        if slug not in area:
            continue
        mac = macro_of[slug]
        cur = best.get(mac)
        if cur is None or (-area[slug], slug) < (-area[cur["slug"]], cur["slug"]):
            best[mac] = c
    feat = {c["slug"] for c in sorted(
        best.values(), key=lambda c: (-area[c["slug"]], c["slug"]))[:LIVING_MAX]}

    # EVERY COUNTRY THAT HAS A PHOTOGRAPH IS AN APERTURE, AND ALL FIFTY DO.
    # The first version lit six and left forty-four in stone, which reads as
    # six countries that matter and forty-four that do not — the opposite of
    # what an atlas says. The brief asked for the rest to borrow a picture
    # from somewhere else if they had none; none of them has to, because the
    # library already holds a photograph OF each one. Borrowing would have
    # been the first claim on this site that a picture is of a place it is
    # not of, which the register exists to make impossible.
    #
    # WHAT THE SIX ARE IS THE SEQUENCE, NOT THE CAST. A featured country
    # cycles through its own destinations; every other one shows the single
    # photograph it has, and gains a sequence on the build after `stage:
    # fill` reaches its destinations. So the difference between them is a
    # fact about the register rather than a decision about the countries.
    chosen = sorted((c for c in data["countries"].values()
                     if c["slug"] in area),
                    key=lambda c: (-area[c["slug"]], c["slug"]))

    out = []
    for c in chosen:
        slug = c["slug"]
        d = paths[slug]
        # THE IMAGE EXTENT IS THE WHOLE BOUNDING BOX, islands included, and
        # that is the opposite decision from the one above for a different
        # reason: the picture is CLIPPED to the country, so anything the
        # rectangle does not cover is a piece of the country drawn in stone
        # beside a piece drawn in photograph. `slice` then crops the source
        # to fill it, exactly as `object-fit: cover` does everywhere else.
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
        xs, ys = nums[0::2], nums[1::2]
        if not xs or not ys:
            continue
        box = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

        # THE STEP IS THE COUNTRY'S OWN DRAWN WIDTH, and asking for one
        # number for fifty apertures is how a homepage ships two megabytes.
        # The drawing is about one CSS pixel per unit at 1920, so a country
        # 60 units wide is 60px and wants the 480 step at twice that for a
        # retina screen; Türkiye is 252 and wants 800. The ladder's smallest
        # rung is 480 and most of these countries need a third of it, which
        # is a real finding and the trigger for a smaller step — recorded
        # rather than answered by inventing one here, because a sixth rung
        # is a decision about every purpose on the site.
        want = max(box[2], box[3]) * 2.0

        def frame(key, name, line, url, _w=want):
            row = images.get(key) or {}
            return {"key": key, "name": name, "line": line, "url": url,
                    "href": photo_href(images, key, _w),
                    "alt": row.get("alt", ""),
                    "photographer": row.get("photographer", ""),
                    "source": row.get("source", ""),
                    "licence": row.get("licence", ""),
                    "licence_url": row.get("licence_url", "")}

        frames = [frame("country:" + slug, c["name"],
                        c.get("tagline") or "", urls.country(c))]
        if slug in feat:
            for cid, e, key in shots.get(slug, [])[:LIVING_FRAMES - 1]:
                frames.append(frame(key, e["city"]["name"],
                                    e["city"].get("summary") or "",
                                    urls.city(e["country"], e["region"],
                                              e["city"])))
        out.append({"slug": slug, "name": c["name"], "href": urls.country(c),
                    "d": d, "box": box, "frames": frames,
                    "featured": slug in feat})
    return out


def heroeurope(data, featured=(), beyond_ground=True):
    """Europe, entire, seen through the doorway. The homepage's picture.

    THE HOMEPAGE WAS THE LEAST EUROPEDOOR PAGE ON THE SITE. Stripped of its
    mark and its wordmark and set beside eight other families, it was a navy
    gradient, a headline, a search box and four chips — recognisable as a
    travel product and as nothing more specific than that. Six of the other
    eight carried the aperture and were unmistakable; the one page that has
    to say what this is said the least.

    A HERO MAP WAS REMOVED ONCE, AND FOR GOOD REASONS THAT DO NOT APPLY HERE.
    That one was an instrument: lod1 coastline, 319 destination dots, a
    filter row and a row of counts — 90 KB, and it led with structure. The
    reader met the data model before they wanted to go anywhere.

    This is not that. It is a coastline and nothing else: no dot, no filter,
    no count, no label. An instrument is a thing you operate; a continent is
    a thing you look at.

        lod1 + 319 dots + filters   ~90,000 bytes   the version removed
        lod0, coastline only         22,927 bytes   this
        a licensed hero photograph  150,000+ bytes  what it stands beside

    It is a quarter of the drawing that failed and a seventh of the
    photograph. THE PHOTOGRAPH BRIEF STAYS OPEN — docs/hero-brief.md, seven
    questions unanswered — because a photograph does a job this cannot: the
    atmosphere of a particular morning in a particular place. This does a
    job the photograph cannot either, and the reason it is here rather than
    a placeholder: no other travel product on earth can draw Europe on its
    own conformal conic through its own aperture. It is the picture that is
    ONLY ours.

    Europe is fitted rather than cropped. The projection is 1.28:1 and a
    hero is nearly 2:1, so slicing it would cut the Arctic off the top and
    the Mediterranean off the bottom — the two edges that make the shape
    recognisable. It sits to the right at its own proportion and the opening
    runs on past it, which is where the type goes: the empty space is the
    composition rather than something to fill.
    """
    doc = geo.load("europe-lod1.json")
    if not doc:
        return ""
    # THE FINER FILE, THINNED IN THE UNITS THE PICTURE IS DRAWN IN. This drew
    # `europe-lod0.json`, which is simplified at 0.055 DEGREES — a unit that
    # is 6 km at the Mediterranean and half that at North Cape, so it flattened
    # Iceland into a pentagon and Britain into a wedge while leaving Greece
    # comparatively intact. At the hero's rendered size one projection unit is
    # about one pixel, so the fine file thinned at 1.8 units is both a better
    # shape and fewer bytes than the coarse one:
    #
    #     lod0, as published            22,927 bytes   blocky, and unevenly
    #     lod1, as published            73,463 bytes   too heavy for a hero
    # THE HERO HAS ITS OWN WINDOW ON THE PROJECTION, and it is wider and
    # deeper than the atlas's. MAP_W x MAP_H is the frame every other map on
    # this site is drawn in and it is fitted to what this product writes
    # about: it stops where data/geo/ stops. The hero's subject is not a set
    # of destinations, it is the continent — and a continent that ends in a
    # fade at 52°E is a continent that ends in mid-air.
    #
    # The window is checked against the edges of `beyond-lod0.json` rather
    # than chosen by eye: under this conic the 102°E cut runs from x=1,489 at
    # 36°N to y=-192 at 68°N and the 8°N cut from y=1,003 at 50°E outward, so
    # neither is inside this box at any latitude. The drawing reaches every
    # edge of its own frame and no fade has to hide anything.
    view = HERO_VIEW
    _, _, vw, vh = view
    #     lod1 thinned at 2.4 units     32,075 bytes   the first version
    #     lod1 thinned at 1.8 units     42,550 bytes   this
    #
    # AND THE EUROPE SIDE IS WHERE THE DETAIL IS WORTH PAYING FOR. 2.4 units
    # is 2.1 device pixels on a retina screen at this size, which is coarse
    # enough to see: it rounds the Danish straits, closes the narrower
    # Norwegian fjords and turns the Aegean into a handful of wedges. 1.8 is
    # 1.6 pixels and costs ten kilobytes on one page — the only page on this
    # site where the coastline IS the picture rather than the ground under
    # one. The layer beyond it is thinned three times harder for the opposite
    # reason.
    # AND EVERY COUNTRY IS A DOOR, which is the point of the picture.
    #
    # The hero was a picture you looked at: aria-hidden, pointer-events none,
    # not in the tab order, not in the accessibility tree. On a page whose one
    # job is to be the way in, the largest thing on it led nowhere. Each of
    # the fifty countries is an SVG <a> to its own page now, with its name as
    # the accessible name — no dot, no label, no filter and no count, so it is
    # still the cover of the atlas rather than the index.
    # AND EACH COUNTRY'S PATH CARRIES AN ID, so the Living Atlas can clip a
    # photograph to it with a `<use>` instead of a second copy of the ring.
    # Forty-one clipPaths holding real path data would be the 43 KB of
    # country geometry on this page twice — the exact cost the frontier pass
    # exists to avoid.
    # NOT `ground`: THAT NAME IS TAKEN, three hundred lines down, by the
    # `NameGround` this function builds to test whether a country name sits
    # on its own polygon — and a NameGround is always truthy, so a parameter
    # called `ground` was False at the top of the function and True by the
    # time the dusk was emitted. Russia vanished correctly and the fade that
    # existed only for Russia went on being drawn, which is a state no
    # caller can ask for. Second shadowed name in this session; the first
    # was `ident` in geo.landmass, where the loop variable of the same name
    # made the callback a string.
    #
    # THE COUNTRIES THE DATA CUT RUNS THROUGH, DERIVED FROM THE GEOMETRY
    # RATHER THAN NAMED. data/geo/ stops at 52°E, and exactly one country
    # this atlas writes about has land on both sides of it. With a ground to
    # dissolve into that is what the dusk is for; with no ground it is a
    # fragment occupying the whole north-east of the picture, and the fade
    # that hides its edge is a pale wash over a third of the drawing. So the
    # groundless hero drops it — the country keeps its page, its link from
    # every other surface and its advisory, and this one picture does not
    # draw a shape whose eastern side is a decision about a download.
    # READ OFF THE DOCUMENT'S OWN BBOX, never the number 52 typed here: the
    # bound lives in scripts/map/process.py and travels with the file, so a
    # wider fetch later moves this on its own instead of leaving a constant
    # that used to be true.
    _east = doc.get("bbox", [0, 0, 1e9, 0])[2]
    cut = {ent.get("slug") for ent in doc["countries"].values()
           if ent.get("atlas") and any(
               ring[i] >= _east - 0.02
               for ring in ent["rings"] for i in range(0, len(ring), 2))}
    ctx, land = geo.landmass(MAPPROJ, view, doc=doc,
                             drop=() if beyond_ground else cut,
                             thin_units=1.8, min_units=6.0,
                             # CONTEXT ENTRIES CARRY NO SLUG — they are the land outside
                             # this atlas, which has no page and therefore
                             # no photograph and nothing to clip.
                             path_id=lambda ent: ("lz-" + ent["slug"]
                                                  if ent.get("slug") else ""),
                             link=lambda ent: urls.country_by_slug(ent["slug"]))

    # ONE PATH PER GROUP, NOT ONE PER COUNTRY, and it is not a saving.
    #
    # Two neighbouring polygons simplified independently do not share an edge,
    # so at this alpha the water showed through the cracks as hairlines across
    # France, Germany and Poland. Stroking each country in its own fill colour
    # closed them and drew a POLITICAL MAP: where two countries meet two
    # strokes overlap, and the doubled alpha is a bright line — fifty frontiers
    # competing with a headline, which is the exact failure this hero was
    # rebuilt to remove.
    #
    # One path per group has neither problem. A single fill is painted once
    # however many subpaths overlap, and a single stroke of the same colour
    # closes the seams without ever doubling. The per-country <title> elements
    # go with it, which costs nothing: this drawing is aria-hidden, and a name
    # no screen reader can reach was never a name.
    def _merge(markup, ident):
        d = "".join(re.findall(r'<path[^>]*\sd="([^"]*)"', markup))
        return f'<path id="{ident}" d="{d}"/>' if d else ""

    ctx = _merge(ctx, "heroctx")
    # THE LAND IS NOT MERGED ANY MORE, and the reason the merge existed is
    # gone with it. Two neighbours simplified independently do not share an
    # edge, so the water showed through the cracks; stroking each country in
    # its own fill colour closed them and, at a group opacity below 1, the two
    # coincident strokes at a shared frontier composited BRIGHTER than either
    # — fifty white borders. That is arithmetic about alpha, not about
    # countries: at opacity 1 two identical opaque strokes are one stroke. The
    # group is opaque now, so the seams close and nothing doubles, and each
    # country can be its own element and therefore its own link.
    #
    # `<g id="heroland">` still exists for the two passes that need the union:
    # the frontier stroke above the terrain and the clip that keeps the relief
    # inside the atlas. Both are a `<use>` of the group, which costs no
    # geometry, and the anchors inside the clone are inert — a shadow tree is
    # not in the tab order.
    land = f'<g id="heroland">{land}</g>'

    # ── THE GRATICULE ────────────────────────────────────────────────
    # A PRINTED ATLAS SHOWS ITS OWN PROJECTION, and this drawing publishes
    # its four angles in the colophon and drew nothing. Under a conic a
    # meridian is a straight radial line from the cone apex and a parallel
    # is a circular arc about it — so the graticule is not decoration here,
    # it is the one mark that makes the projection visible rather than
    # merely stated. Sampled through `MAPPROJ` rather than drawn as arcs,
    # so it cannot disagree with the geometry it is laid over: if the
    # projection ever moves again, this moves with it.
    #
    # Ten degrees, which is the interval the EU's own pan-European sheets
    # use at this extent, and a hairline in the water's own tone: a reader
    # should find it when they look for it and never meet it first.
    _grat = []
    for _lon in range(-30, 51, 10):
        _pts = [MAPPROJ.xy(_la / 2.0, _lon) for _la in range(60, 161, 4)]
        _grat.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in _pts))
    for _lat in range(30, 81, 10):
        _pts = [MAPPROJ.xy(_lat, _lo / 2.0) for _lo in range(-70, 111, 4)]
        _grat.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in _pts))
    graticule = ('<g class="herograt" aria-hidden="true">'
                 + "".join(f'<path d="{d}"/>' for d in _grat) + '</g>')

    # ── THE SEA NAMES ────────────────────────────────────────────────
    # `data/geo/marine-lod1.json` holds twenty-one of them with a real
    # coordinate each, and `cartography.water_points()` has projected them
    # for the plates since the cartography split. The hero — the one
    # drawing on this site whose subject is the whole continent, and the
    # one with the most open water in it — named none.
    #
    # THE SET IS CHOSEN BY HOW MUCH SEA IS AROUND THE NAME, which is a
    # measurement rather than a list: the distance from the label's own
    # point to the nearest drawn coastline. A sea name wants open water, so
    # the Strait of Gibraltar and the Bristol Channel — real entries, and
    # nine units from land — are exactly the ones a printed sheet leaves
    # out at this scale. Six, because the water here is the page and a
    # seventh name starts to read as a legend.
    #
    # THE ATLANTIC IS NOT AMONG THEM AND IS NOT INVENTED. The reference
    # sheet names it; this dataset does not hold it, and typing a
    # coordinate for it here would be authoring geography, which is the one
    # thing this repository refuses in every other form.
    #
    # AND A SEA IS NAMED WHERE THIS DRAWING DRAWS LAND ON BOTH SIDES OF IT,
    # which is the rule a ceiling on the room was a poor proxy for. Ranked
    # on room alone the two roomiest seas in this picture are the WHITE SEA
    # at 60 units and the CASPIAN at 30 — for the reason that their shores
    # are Russia and Kazakhstan, and this hero draws neither. A ceiling
    # caught the White Sea and let the Caspian through, because Azerbaijan
    # is close enough on one side; what actually distinguishes a sea this
    # drawing can name is that the reader can see what encloses it. Land
    # east AND west, within a reach of its own room: the North Sea has the
    # British Isles and Denmark, the Mediterranean has Iberia and Greece,
    # the Black Sea has Bulgaria and Georgia, and the Caspian has one
    # shore. The floor is the same question from the other end — the
    # Strait of Gibraltar and the Bristol Channel are real entries at 0.8
    # units, and are exactly what a printed sheet leaves out at this scale.
    LABEL_ROOM = 12.0
    LABEL_REACH = 170.0
    _coast = []
    for _m in LAND_PATH.finditer(land):
        _n = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", _m.group(1))]
        _coast.extend(zip(_n[0::2], _n[1::2]))
    _lx1 = max((cx for cx, _cy in _coast), default=view[0] + vw)
    _ly0 = min((cy for _cx, cy in _coast), default=view[1])
    _seas = []
    for _x, _y, _nm in cartography.water_points(
            lambda la, lo: MAPPROJ.xy(la, lo), view):
        if not (view[0] < _x < view[0] + vw and view[1] < _y < view[1] + vh):
            continue
        _room = min((math.hypot(_x - cx, _y - cy) for cx, cy in _coast),
                    default=0.0)
        if _room < LABEL_ROOM:
            continue
        # AND NOT WHERE THE PICTURE ITSELF RUNS OUT. Two tests failed on
        # the WHITE SEA and the CASPIAN before this one: a ceiling on the
        # room caught the first and not the second, and counting the
        # countries that face a sea caught neither, because Azerbaijan's
        # coast wraps right round the Caspian's label and Finland, Sweden
        # and Norway are all within reach of the White Sea's. What those
        # two actually have in common is the thing a reader sees: their far
        # shore is Russia and Kazakhstan, and the drawn land simply STOPS
        # a few units beyond the name. `data/geo/` is cut at 52°E and at
        # 72.5°N, and this hero drops the one country the eastern cut runs
        # through — so a label within its own reach of the drawing's
        # northern or eastern extreme is a label with nothing behind it.
        # South and west the drawing ends in the Atlantic and in the
        # Mediterranean's own southern shore, which is a decision rather
        # than a data cut, so the test is on those two edges only.
        if (_x > _lx1 - LABEL_REACH * 0.55) or (_y < _ly0 + LABEL_REACH * 0.4):
            continue
        _seas.append((_room, _x, _y, _nm))
    _seas.sort(reverse=True)
    seanames = ('<g class="lyr lyr-water-labels" aria-hidden="true">'
                + "".join(
                    f'<text class="seaname" text-anchor="middle"'
                    f' x="{x:.1f}" y="{y:.1f}">{esc(nm)}</text>'
                    for _r, x, y, nm in _seas[:6]) + '</g>') if _seas else ""

    # AND THE RELIEF, which is the whole reason this is worth doing. Every
    # destination plate on this site carries hypsometric bands and the front
    # door carried a flat silhouette — the plainest map on the site, on the
    # largest surface, first. Three bands, thinned to a picture's tolerance:
    # the Alps, the Pyrenees, the Carpathians, the Scandinavian spine and
    # Iceland come up out of the dark, and nothing else is added. Still no
    # dot, no filter, no count, no label.
    relief = cartography.relief_wash(MAPPROJ, view,
                                     thin_units=2.5, min_units=50.0)

    # THE BOUNDARY PASS, AND IT COSTS NO GEOMETRY.
    #
    # The hero read as a relief sculpture of Europe rather than as an atlas of
    # fifty countries, and the reason is one missing layer: land was a single
    # blob. Every other map here draws frontiers. The first attempt at it on
    # this page drew fifty bright lines, because per-country translucent
    # strokes double where two countries share an edge — which is why the land
    # is one merged path with the transparency on its group.
    #
    # ORDER puts country-bounds ABOVE terrain, and it has to: a boundary here
    # is a stroke on the land path and the bands paint straight over it. On a
    # plate that costs the country rings a second time, and on this page the
    # rings are 43 KB. So the pass is a `<use>` of the same path.
    #
    # THAT IS THE TRAP THIS REPOSITORY LOST A DAY TO ONCE, and the escape is
    # to style by INHERITANCE rather than by id. A `<use>` clone is still
    # matched by a selector for the original element, so `#heroland { fill }`
    # would come back filled in the copy. Nothing selects the path any more:
    # fill and stroke are set on `.herolandg` and inherited, so the clone
    # inherits from ITS OWN parent instead and is a stroke with no fill.
    bounds = '<use href="#heroland"/>'

    # THE COUNTRIES ARE NAMED, AND THE NAME IS THE ONE PIECE OF TYPE ON THE
    # PICTURE.
    #
    # Every other map on this site sets the country's own name across it, and
    # for the same second reason: the recognition instrument strips the
    # wordmark and the page title, and a drawing that names what it draws
    # survives that where a shape alone does not. It is placed by the atlas's
    # single placement rule rather than a second one — the centroid of the
    # country's own drawn shape, then eight points around it inside its own
    # radius, each of the four positions tested against the frame and against
    # every name already down. A name that fits nowhere is dropped, exactly as
    # one that collides is, and the country keeps its shape, its link and its
    # accessible name. A wide name breaks at its last space, which is what a
    # printed atlas does.
    #
    # Tracked uppercase at the plates' own size and colour, so this is the
    # same typography one level up rather than a new one: no font size is
    # introduced, and `checks.py` counts them.
    def _dpath(d):
        """The bounding box of the largest subpath in a `d`, and its centre."""
        best, bb = 0.0, None
        for sub in d.split("Z"):
            pts = [(float(a), float(b))
                   for a, b in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", sub)]
            if len(pts) < 3:
                continue
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if area > best:
                best, bb = area, (min(xs), min(ys), max(xs), max(ys))
        if not bb:
            return None
        return ((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0,
                min(bb[2] - bb[0], bb[3] - bb[1]) / 2.0, bb)

    NAME_INSET = 14.0
    taken = []

    # WHOSE GROUND IS THIS? The two rules and the tolerance now live in
    # NameGround at module level, because there are TWO drawings on this site
    # that set a country's name across it and for the life of both only this
    # one had them. See the class.
    ground = NameGround([m_.group(1) for m_ in LAND_PATH.finditer(land)])
    shapes = ground.shapes
    CROSS_OK = NameGround.CROSS_OK

    def _own(mine, x, y):
        return ground.own(mine, x, y)

    def _crossings(mine, x0, y0, w0, h0):
        return ground.crossings(mine, x0, y0, w0, h0)

    def _clear(lx, ly, lw, lh):
        b = (lx - LABEL_CLEAR, ly - LABEL_CLEAR,
             lx + lw + LABEL_CLEAR, ly + lh + LABEL_CLEAR)
        return not any(not (b[2] < q[0] or b[0] > q[2]
                            or b[3] < q[1] or b[1] > q[3]) for q in taken)

    def _inframe(x, y, wide, anchor, mine=None, metric="cname", tol=0):
        x0, y0, w0, h0 = _label_box(
            x, y, wide, anchor, *LABEL_METRICS[metric][2:])
        if not (x0 >= view[0] + NAME_INSET
                and x0 + w0 <= view[0] + vw - NAME_INSET
                and y0 >= view[1] + NAME_INSET
                and y0 + h0 <= view[1] + vh - NAME_INSET):
            return False
        if mine is None:
            return True
        # THE MIDDLE ON ITS OWN COUNTRY, AND NOT ONE SAMPLE ON ANYBODY
        # ELSE'S. Nine sample points along the name — seven on the baseline
        # and three at cap height — because a name is a bar of type rather
        # than a point, and the whole bar has to be over its own ground or
        # over water.
        if not _own(mine, x0 + w0 / 2.0, y0 + h0 / 2.0):
            return False
        return _crossings(mine, x0, y0, w0, h0) <= tol

    ANCHORS = ((0, 0), (0, -0.35), (0, 0.35), (-0.4, 0), (0.4, 0),
               (-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3))
    # THE BIGGEST COUNTRIES CLAIM THEIR SPACE FIRST, and there is a cap.
    #
    # Placed in document order — which is alphabetical by ISO code — Albania
    # took a position before Germany was asked for one, and the map filled up
    # from whoever happened to be first. Drawn area is the honest order here:
    # it is a property of THIS picture rather than a judgement about the
    # country, and it is the same quantity that decides whether a name can
    # fit at all.
    #
    # And the cap is the point of the whole layer. The question is not how
    # many countries can be labelled, it is whether the labels make Europe
    # more recognisable — so sixteen is the ceiling and the rest of the
    # continent is read from its shape, which is what the shape is for.
    NAME_MAX = 16
    # AND THE PATTERN TOLERATES ATTRIBUTES BEFORE `d`, WHICH IT DID NOT.
    # It was the literal `<path d="..."><title>`, and the day the land paths
    # gained an `id` — so the Living Atlas could clip a photograph to a
    # country with a `<use>` instead of a second copy of its ring — the
    # regex matched nothing and all fifteen country names left the hero in
    # silence. Nothing failed: the layer was simply empty, which is the same
    # shape as the check that matched `pointsmap arched"><svg` and examined
    # zero dots on a site with 130 region maps. A pattern pinned to the
    # exact attribute order of markup somebody else emits is a pattern that
    # breaks on an attribute nobody thought about, so this one asks for the
    # attribute it needs and ignores the rest — and the assertion under the
    # loop says the layer found countries at all.
    order_ = []
    for idx, m in enumerate(LAND_PATH.finditer(land)):
        spot = _dpath(m.group(1))
        if spot:
            order_.append(((spot[3][2] - spot[3][0]) * (spot[3][3] - spot[3][1]),
                           idx, m, spot))
    order_.sort(key=lambda t: -t[0])
    assert order_, (
        "the hero's name layer read no country out of the land markup. The "
        "pattern above has stopped matching what geo.landmass() emits, and "
        "an empty layer looks exactly like a drawing that was always "
        "unlabelled")
    names = []
    for _area, idx, m, spot in order_:
        if len(names) >= NAME_MAX:
            break
        cx, cy, rad, bbox = spot
        up = (m.group(2).replace('&amp;', '&').replace('&lt;', '<')
              .replace('&gt;', '>').replace('&quot;', '"')).upper()
        # A NAME MUCH WIDER THAN ITS OWN COUNTRY IS NOT A LABEL, IT IS A
        # SENTENCE LYING ACROSS THE NEIGHBOURS. Keeping the centre on the
        # country stopped ICELAND floating in the Denmark Strait and left a
        # worse fault behind it: SWITZERLAND ran from Bordeaux to Munich,
        # BOSNIA AND HERZEGOVINA from Italy to Romania, BELGIUM out over the
        # North Sea. A printed atlas answers that with an abbreviation, a
        # leader line or a number in a key, and this picture will not carry
        # any of the three — so the name is dropped and the country keeps its
        # shape, its frontier, its link and its accessible name.
        #
        # Measured against the country's LONGEST side rather than its width,
        # because Portugal is 55 units across and 160 tall and its name reads
        # perfectly down it. Twice that side is the limit: Iceland's name is
        # 1.8 times its island and belongs on the map; Switzerland's is 3.6
        # times its country and does not.
        # A LOOSE CAP, AND ONLY TO BOUND THE WORK. The crossing test is what
        # decides now; this stops a name four times its own country's length
        # from paying for nine anchors and forty polygon tests to be told so.
        span = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        pad_, ch_, _u, _d = LABEL_METRICS["cname"]
        one = pad_ + len(up) * ch_
        two = (pad_ + max(len(a) for a in up.rsplit(" ", 1)) * ch_
               if " " in up else one)
        if min(one, two) > 3.0 * span:
            continue
        got = None
        for tol_ in (0, CROSS_OK):
            for fx, fy in ANCHORS:
                got = place_label_box(
                    cx + fx * rad, cy + fy * rad, up, vw, vh, cls="cname",
                    off=10.0, prefer="over", metric="cname", clears=_clear,
                    fits=lambda *a, _i=idx, _t=tol_: _inframe(
                        *a, mine=_i, tol=_t))
                if got:
                    break
            if got:
                break
        if not got and " " in up:
            a_, b_ = up.rsplit(" ", 1)
            long_ = a_ if len(a_) >= len(b_) else b_

            def _two(attr, x, y, _nm, _a=a_, _b=b_):
                return (f'<text class="cname"{attr} x="{x:.1f}" y="{y:.1f}">'
                        f'<tspan x="{x:.1f}" dy="{-CNAME_LEAD / 2:.1f}">'
                        f'{esc(_a)}</tspan>'
                        f'<tspan x="{x:.1f}" dy="{CNAME_LEAD:.1f}">'
                        f'{esc(_b)}</tspan></text>')

            for fx, fy in ANCHORS:
                got = place_label_box(cx + fx * rad, cy + fy * rad, long_,
                                      vw, vh, cls="cname", off=10.0,
                                      prefer="over", metric="cname2",
                                      clears=_clear, wrap=_two,
                                      fits=lambda *a, _i=idx: _inframe(
                                          *a, mine=_i, metric="cname2",
                                          tol=CROSS_OK))
                if got:
                    break
        if got:
            names.append(got[0])
            taken.append((got[1], got[2], got[1] + got[3], got[2] + got[4]))
    names = "".join(names)

    # A LITTLE WATER, AND THE RANK IS WHERE THE RESTRAINT LIVES. The plates
    # draw rank 6 and every lake, which over the whole continent is 153 rivers
    # and 65 lakes and 49 KB — a hydrology map with Europe underneath it. Rank
    # 3 is the thirty-five a reader would name unprompted: the Danube, the
    # Rhine, the Volga, the Loire, the Vistula, the Po. The lakes are cut by
    # DRAWN AREA rather than by the dataset's own importance, because what a
    # picture wants is the ones you can see: 55 becomes 22 and Ladoga, Vänern,
    # Balaton and Geneva are all still there.
    water = cartography.rivers(MAPPROJ, view, river_rank=3, lake_rank=0,
                               thin_units=1.6, min_lake_units=25.0)

    # NINE MARKS WERE TRIED HERE AND ARE NOT DRAWN, and the measurement is
    # the reason rather than the taste.
    #
    # Every other map on this site carries human destinations and this one
    # carries none, so the brief asked for seven to twelve extremely
    # restrained points — not a dataset, just "the continent is populated with
    # discoveries". It was built: one per macro region, placed on the real
    # destination nearest that region's own centre, 2.6 units across, in the
    # frontier ink, no label, no link, no title.
    #
    # Two things came back. At 2.6 units they render 2.3 pixels wide on a
    # 1,440 window and you have to hunt for them, so they do not say the thing
    # they were added to say; and anything large enough to say it is a dot on
    # the cover of an atlas that the page cannot name. **A plate draws what it
    # can name** is principle 2 of docs/cartographic-standard.md and is held
    # at 176 marks named out of 176 across the fifty country plates. A mark
    # this page cannot name is the "something is here" dot that rule exists to
    # refuse, and the sentence directly under the picture already says it in
    # words: fifty countries, and somewhere in them the thing you have not
    # thought of yet.
    #
    # The centroid version also placed one mark in Belarus — an advisory
    # country stripped from the planner — which is the second reason a derived
    # point is not automatically an honest one.

    # AND THE LAND CARRIES ON PAST THE ATLAS, drawn as a different thing.
    #
    # Europe is not an island and this drawing said it was. Everything east of
    # 52°E and south of 33°N is outside what this product writes about, so
    # data/geo/ stops there and the hero faded its own eastern quarter and its
    # southern eighth to keep two straight data cuts from reading as rendering
    # faults. That is an honest way to hide an edge and a poor way to draw a
    # continent: a fade says "the picture stops", and what is actually true is
    # that the LAND carries on and this atlas does not.
    #
    # So the ground under the picture is now the real ground — western Siberia,
    # the Caspian, Iran, Arabia, the Sahara — from beyond-lod0.json, anonymous
    # rings at a fifth of the contrast, with no relief on them and nothing to
    # click. Europe is what is lit; Asia and Africa are what it stands on. The
    # fades stay exactly where they were and now do the opposite job: they no
    # longer hide an edge, they hand the eye from the lit continent to the
    # quiet ground, so the boundary between two treatments is a gradient
    # rather than the straight line the two datasets actually meet along.
    # Thinned much harder than the atlas in front of it, because it is drawn
    # at a sixth of the contrast: 3.0/60 and 5.0/120 are indistinguishable at
    # 17% opacity and 4 KB apart on every request. Coarser than that starts
    # to show in Anatolia's south coast, which is the one stretch of this
    # layer that runs close to land the reader is looking at.
    # Thinned harder than the atlas because it is drawn as shadow rather than
    # as a shape a reader reads — and it is cheap now that it is cut to the
    # atlas's complement rather than to a box containing it: 18 KB of second,
    # coarser European coastline became 6 KB of Asia, Arabia and the Sahara.
    beyond = geo.beyondmass(MAPPROJ, view, thin_units=2.5, min_units=60.0,
                            pad=0.0)
    beyond = [b for b in beyond if b]
    # THE DATA CUT IS A DIAGONAL, AND THE FADE THAT HID IT WAS VERTICAL.
    #
    # data/geo/ stops at 52°E. Under the conic that meridian runs from
    # (747, 36) at 70°N to (1024, 471) at 40°N — a straight line leaning 57°
    # off the vertical — and a straight edge through Russia reads as a
    # rendering fault rather than as the edge of what this atlas holds. The
    # CSS mask that hid it faded left-to-right, so to cover a diagonal it had
    # to start at 40% of the width, which is central Europe: Italy, the
    # Adriatic, Greece and the whole Balkan peninsula were inside the fade and
    # read as sea, on the hero of a European travel product.
    #
    # The fade runs along the cut instead, in the drawing's own coordinates
    # where the cut's geometry is known exactly rather than guessed at in
    # percentages of a box the drawing is letterboxed inside. Everything west
    # of it is fully drawn.
    _band = cut_band

    # A TWO-STOP GRADIENT HAS A CREASE AT EACH END, AND THE EYE DRAWS A LINE
    # ALONG IT.
    #
    # Every fade here was white-to-black in two stops, which is linear: the
    # brightness ramps at a constant rate and then stops dead. That corner is
    # a discontinuity in the first derivative, and human vision sharpens
    # exactly that — a Mach band — so the ground arrived out of the dark along
    # a perfectly straight diagonal that nothing in the drawing had drawn. It
    # was read as a hard edge in three separate rounds of looking at this
    # picture and "soften the gradient" never fixed it, because widening a
    # linear ramp moves the crease without removing it.
    #
    # Smoothstep has zero slope at both ends, so there is no crease to find.
    # Five stops is enough at this size: the error against the real curve is
    # under 1.5% of full scale, which is a third of one 8-bit level.
    # AND THE FADE IS PAINTED NOW, NOT MASKED — because a mask breaks the
    # links.
    #
    # The atlas layers used to sit inside two `<g mask>` wrappers, which is
    # the natural way to fade them out toward the two data cuts. The moment
    # every country became an anchor, none of them could be clicked:
    # Chromium hit-tests a masked group as ONE region, so the click landed on
    # the wrapper and stopped there. Keyboard activation still worked, which
    # is exactly the kind of half-working that ships — the links were real, in
    # the tab order, correctly named, and dead to a mouse.
    #
    # The same picture is arrived at by painting instead: a rectangle of
    # graphite whose alpha ramps along the same band, over the top, masked to
    # the atlas's own land so it dims the continent and not the sea. Masks on
    # things nobody clicks are fine, and this one is on the overlay rather
    # than on the layers underneath it.
    def _dusk(lo=0.0, hi=1.0):
        """The shadow's ramp — and every stop names its colour.

        THE COMMENT SAID GRAPHITE AND THE PICTURE WAS BLACK. These stops
        carried an opacity and no `stop-color`, and the SVG default for that
        property is #000 — so the layer this file calls "two rectangles of
        graphite" ramped to pure black, measured (0, 0, 0) against the
        (16, 18, 20) the ground beside it is drawn in. It is the one thing
        `--graphite` rather than #000` was written down to prevent: black is
        a screen and graphite is a shadow, for the same reason limestone is
        never #fff.

        The colour stays in the stylesheet — there is a rule for it, and it
        had been selecting nothing, because the stops live in <defs> and the
        group only references the gradient. The rule points at the gradients
        now and the browser suite reads the resolved value.
        """
        return dusk_stops(lo, hi)

    def _stops(lo=0.0, hi=1.0, invert=False):
        out = []
        for i in range(5):
            t = i / 4.0
            v = t * t * (3.0 - 2.0 * t)
            if invert:
                v = 1.0 - v
            g = round((1.0 - v) * 255)
            out.append(f'<stop offset="{lo + (hi - lo) * t:.4f}" '
                       f'stop-color="#{g:02x}{g:02x}{g:02x}"/>')
        return "".join(out)

    # Fully transparent BEFORE the cut, not at it. Ending the fade on the cut
    # left the mask 7% opaque along it, and 7% of a bright coastline against
    # the water is still a straight line across the north-east — the exact
    # thing the fade exists to remove.
    # WIDTHS DERIVED FROM THE ATLAS'S OWN OUTERMOST DESTINATIONS. They were
    # 360 east and 150 south, chosen by eye for atmosphere, and nothing asked
    # what was underneath them: Baku read 100% graphite and Paphos 92% on the
    # one picture that opens this site. See dusk_reach().
    _eb, _ea, _sb, _sa = dusk_reach(data)
    ex1, ey1, ex2, ey2 = _band(70.0, 40.0, 52.0, _eb, _ea)
    # THE GROUND'S OWN FADE-IN WAS DELETED AND ITS AXIS WAS LEFT BEHIND.
    # `gx1, gy1, gx2, gy2 = _band(70, 40, 52, 150, 40)` sat here, unread by
    # anything, with a paragraph above it explaining a fade the drawing no
    # longer had — so the code still looked like it had one while the picture
    # showed a hard edge. Dead code that reads as a decision is worse than an
    # absence, which is the same reason the dead-rule scan exists for CSS.
    # THE SOUTHERN CUT WAS HIDDEN IN CSS AND SO WAS EVERYTHING NEAR IT. The
    # atlas holds North Africa down to 33°N and no further, and the bottom
    # eighth of the drawing was faded in the stylesheet to cover that straight
    # edge — a fade in the ELEMENT's coordinates, which is a different space
    # from the drawing's and moves whenever the box changes shape.
    #
    # AND THE FIRST FIX, A HORIZONTAL GRADIENT IN THE DRAWING'S OWN SPACE, WAS
    # WRONG FOR THE SAME REASON THE VERTICAL ONE WAS. **A parallel is not a
    # horizontal line on a conic.** The 33rd runs from y=706 over Tunisia to
    # y=590 over the Caspian — 116 units of rise — so a horizontal fade placed
    # on the Tunisian end left the cut showing right across Anatolia, which is
    # exactly where the eye goes once Asia is drawn.
    #
    # A conic's parallels are circles about the cone apex, so the fade is a
    # RADIAL gradient centred there: it follows the 33rd parallel exactly, at
    # every longitude, by construction rather than by tuning. The apex is
    # geo.Projection.apex() and the radius is parallel_radius(), so if the
    # projection ever moves this moves with it.
    ax, ay = MAPPROJ.apex()
    r33 = MAPPROJ.parallel_radius(33.0)
    foot0, foot1 = (r33 - _sb) / r33, (r33 - _sa) / r33
    return (
        # NOT aria-hidden ANY MORE. It held fifty links the moment the
        # countries became doors, and aria-hidden over focusable content is
        # the one accessibility fault that is worse than no label: the links
        # stay in the tab order and vanish from the accessibility tree. The
        # group carries a name; every decorative layer inside it is hidden
        # individually, so what a screen reader meets is fifty countries and
        # nothing else.
        f'<div class="heroeurope">'
        # SLICE RATHER THAN MEET, now that the frame is wider than Europe.
        # `meet` letterboxes, and a letterbox band is where the drawing's own
        # frame edge shows: with the ground beyond the atlas painted in
        # graphite, that edge is black meeting blue on a straight line, 14
        # pixels above the bottom of the hero on a desktop and across the
        # middle of the picture on a phone. The margin this frame gained to
        # the east and south exists precisely to be cropped — Europe sits
        # where it always did and the ground runs off the edges, which is
        # what ground does.
        f'<svg viewBox="{view[0]:.0f} {view[1]:.0f} {vw:.0f} {vh:.0f}"'
        f' preserveAspectRatio="xMidYMid slice" role="group"'
        f' aria-label="Europe, drawn: every country is a link to its own page">'
        f'<defs>'
        # AND THE TWO GRADIENTS GO WITH THE LAYER THAT REFERENCES THEM. An
        # orphan gradient is what `c_hero_dusk_reach` refuses in the other
        # direction — "no fade" and "no drawing" must not look the same —
        # and a `<defs>` full of ramps nothing paints is 900 bytes of
        # rendering instruction for a picture that is not there.
        + ((f'<linearGradient id="heroedge" gradientUnits="userSpaceOnUse"'
        f' x1="{ex1:.1f}" y1="{ey1:.1f}" x2="{ex2:.1f}" y2="{ey2:.1f}">'
        f'{_dusk()}</linearGradient>'
        f'<radialGradient id="herofootg" gradientUnits="userSpaceOnUse"'
        f' cx="{ax:.1f}" cy="{ay:.1f}" r="{r33:.1f}">'
        f'{_dusk(foot0, foot1)}</radialGradient>') if beyond_ground else '')
        # The mask that keeps the dusk on the land and off the water. The
        # Caspian, the Aral and the Sea of Azov are the far-eastern water this
        # picture has, and an unmasked overlay would paint all three graphite.
        + f'<mask id="herodim" maskUnits="userSpaceOnUse"'
        f' x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}" height="{vh:.0f}">'
        # WIDER IN THE MASK THAN IN THE DRAWING, on purpose. The land is
        # stroked at 1.4 units to close the seams between neighbours, and a
        # `<use>` clone does not inherit that: nothing selects the paths, so
        # the clone took the default stroke-width of 1 and left two tenths of
        # a unit of parchment uncovered along every edge. Along the 52°E cut
        # — a straight line 700 units long — that is a bright hairline
        # exactly where the picture must not have one.
        # AND THE CONTEXT CLONE GOES WITH THE CONTEXT. `#heroctx` is only
        # emitted when the ground beyond the atlas is drawn, and a `<use>`
        # of an id that is not on the page renders as nothing and reports
        # nothing — which `checks.py` is right to refuse, because the one
        # thing worse than a missing layer is a missing layer that looks
        # like a decision.
        + (f'<use href="#heroctx" fill="#fff" stroke="#fff" stroke-width="3"/>'
           if beyond_ground else "")
        + f'<use href="#heroland" fill="#fff" stroke="#fff" stroke-width="3"/>'
        + f'</mask>'
        # RELIEF ONLY WHERE THIS ATLAS GOES. Anatolia and the Atlas mountains
        # are real ground and this file holds them, and drawn at the weight the
        # Alps are drawn at they took the right-hand third of the picture: the
        # eye went to Turkey on the homepage of a European travel product. The
        # clip re-uses the land geometry rather than repeating it — 40 KB of
        # coastline emitted twice was the first version — and a clipPath cares
        # only about shape, so the selector trap that makes `<use>` unusable
        # for painting does not apply here.
        # A MASK RATHER THAN A CLIP PATH, because the land is a GROUP now.
        # `<clipPath>` takes shapes; Chromium renders a `<use>` of a group
        # inside one as nothing at all, so the relief was clipped away
        # entirely and the hero lost every band the moment the countries
        # became links. Nothing failed — the terrain layer was still there,
        # still in ORDER, still counted by every check that counts layers.
        # Only looking at the picture found it. A mask takes any content, and
        # white is opaque: the fill and stroke are presentation attributes on
        # the `<use>` itself, which the clone inherits, because nothing
        # selects the paths inside.
        # THE SHORE, AS A DRAWING CONVENTION AND NOT AS A CLAIM ABOUT DEPTH.
        #
        # Half of this picture is water and it was one flat wash: a 20% crop
        # of the middle read as a competent atlas of north-west Europe and as
        # nothing else. What a printed atlas puts there is a graduated band
        # along every coast, and what makes it honest is that it is CONSTANT
        # WIDTH — real bathymetry is not, and nothing here holds a sounding.
        # It is the land's own silhouette, blurred, in the lighter step of the
        # same Atlantic ramp the ground is drawn from, underneath everything.
        # No geometry: a `<use>` and a blur.
        f'<filter id="heroshore" x="-6%" y="-6%" width="112%" height="112%"'
        f' color-interpolation-filters="sRGB">'
        f'<feGaussianBlur stdDeviation="4.5"/></filter>'
        # THE PAPER. Editorial cartography is printed, and every plate on this
        # site is drawn as paper and graphite; the hero was the one surface
        # with no material in it at all — two flat washes and a coastline.
        # Fractal noise at a fine frequency, desaturated to a neutral and laid
        # over the whole picture at a few per cent, is the grain of the stock
        # rather than a texture of anything: it claims nothing, it is the same
        # everywhere, and it is what makes the difference between a fill and a
        # surface. One filter, no geometry, no request.
        f'<filter id="herograin" x="0" y="0" width="100%" height="100%"'
        f' color-interpolation-filters="sRGB">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.9"'
        f' numOctaves="3" stitchTiles="stitch" result="n"/>'
        f'<feColorMatrix in="n" type="saturate" values="0"/></filter>'
        + (f'<mask id="herolandmask" maskUnits="userSpaceOnUse"'
           f' x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}"'
           f' height="{vh:.0f}">'
           f'<use href="#heroland" fill="#fff" stroke="#fff"/></mask>'
           if relief else "")
        + f'</defs>'
        # THE GROUND, EACH STRIP FADING IN WHERE THE ATLAS FADES OUT. The
        # first is east of 46°E and crosses over along the 52°E meridian; the
        # second is south of 34°N and crosses over along the 33rd parallel.
        # Both are one colour, so the strip that overlaps the other in the
        # south-east corner cannot show a join.
        # THE GROUND, PLAIN AND UNDER EVERYTHING. It needed its own fades
        # while the atlas was masked, because the two had to cross over; with
        # the dusk painted on top instead, the atlas simply covers it where
        # the atlas exists and the dusk turns the atlas into it where it does
        # not. Nothing to cross-fade and no edge to hide.
        # JUST EUROPE, WHERE THE CALLER ASKS FOR IT. `lyr-beyond` is Asia
        # and Africa out to the Yenisei, and `heroctxg` is every non-atlas
        # neighbour; both exist because *Europe is not an island* — a
        # continent ending at 52°E on a graphite ground reads as a coastline
        # and then as a rendering fault. On the gallery hero there is no
        # ground: the sea is the white wall, so there is no water for an
        # edge to read as, and what the two layers actually contributed was
        # a grey mass filling the right third of the picture with the dusk
        # spread across it. The rule has not changed — it was about a
        # drawing with a painted ocean, and this one has none.
        + ('<g class="lyr lyr-beyond" aria-hidden="true">'
           + "".join(f'<path d="{d}"/>' for d in beyond)
           + '</g>' if (beyond and beyond_ground) else "")
        # OPACITY ON THE GROUP, NOT ON THE PAINT, and that is the whole fix.
        #
        # The seams between two independently simplified neighbours have to be
        # closed by a stroke, and a stroke in the fill's own colour drew a
        # bright frontier everywhere two countries met: at 78% alpha the two
        # coincident strokes composite to 95%, so the map grew fifty white
        # borders — the exact political map this hero was rebuilt to remove,
        # arrived at from the opposite direction.
        #
        # A group opacity flattens the group FIRST and composites it once, so
        # overlapping strokes inside it cannot double. The paths are opaque and
        # the group is not, which looks identical where nothing overlaps and
        # correct where things do.
        + f'<g class="lyr lyr-coastal-water" aria-hidden="true">'
        + (f'<use href="#heroctx" filter="url(#heroshore)"/>' if beyond_ground else "")
        + f'<use href="#heroland" filter="url(#heroshore)"/></g>'
        # AND THE COAST IS HEAVIER THAN A FRONTIER, for 27 bytes. A coastline
        # is where land meets sea and a frontier is a line drawn on land, and
        # until now both were the same stroke: the hierarchy every atlas has
        # was missing. A second `<use>` UNDER the land, stroked wider and
        # darker, shows only the half of its stroke that falls outside the
        # fill — which is exactly the coast, and never an internal border,
        # because a neighbour's fill covers it.
        #
        # NOT A `lyr-` LAYER, and the order check is right to have said so.
        # ORDER puts `coastline` after the rivers, and there it would be drawn
        # OVER the land and would stroke every internal frontier at coast
        # weight. In this drawing the coastline is still what ORDER says it
        # is — the land path's own edge — and this is how that edge is given
        # its weight, which is a rendering technique rather than a layer.
        + f'<g class="herocoast" aria-hidden="true">'
        + (f'<use href="#heroctx"/>' if beyond_ground else "")
        + f'<use href="#heroland"/></g>'
        + f'<g class="lyr lyr-land">'
        + (f'<g class="heroctxg" aria-hidden="true">{ctx}</g>' if beyond_ground else "")
        + f'<g class="herolandg">{land}</g></g>'
        + (f'<g class="lyr lyr-terrain" aria-hidden="true"'
           f' mask="url(#herolandmask)">{relief}</g>' if relief else "")
        # ── THE LIVING PHOTOGRAPHIC ATLAS, ABOVE THE GROUND AND UNDER
        # EVERYTHING THAT DESCRIBES IT. The frontiers, the rivers, the
        # country names and the dusk are all drawn over the photograph, so a
        # picture inside France is still bounded by France's own line and
        # still carries the name — which is what stops it being a
        # photograph pasted on a map and makes it the country FILLED.
        #
        # ONE FRAME PER COUNTRY, AND THE SEQUENCE WAS BUILT, MEASURED AND
        # REMOVED. The comment that stood here said the first frame carries
        # `href` and "the others carry `data-href` and are fetched by the
        # ENHANCEMENT the first time they are shown". There is no
        # enhancement: this page's only `<script>` is the inert JSON-LD
        # block, so the held-back frames were never fetched and never shown,
        # and `.herophoto image { opacity: 0 }` read as a dead rule because
        # the only elements it applied to had no `href` to draw. That is the
        # `data-rotate` failure — bytes shipped on the most-visited page
        # waiting for a rotator nobody wrote — found this time by the
        # dead-rule scan rather than by reading.
        #
        # WRITING THE ROTATOR WAS COSTED AND REFUSED ON THE NUMBERS. The
        # sequence is a country's own photograph followed by its photographed
        # DESTINATIONS, and the register holds destination photographs inside
        # exactly one of the featured countries: France has four frames and
        # the other five have one each. So an enhancement would put the first
        # JavaScript on the homepage to cross-fade one country, which is not
        # a trade this page should make — the same reasoning that built,
        # measured and removed the nine restraint marks.
        #
        # The trigger is the library. When the register holds photographed
        # destinations inside several featured countries the sequence is
        # worth ~40 lines of enhancement, and the markup to carry it is two
        # lines here.
        + (('<defs>' + "".join(
            f'<clipPath id="lzc-{f["slug"]}" clipPathUnits="userSpaceOnUse">'
            f'<use href="#lz-{f["slug"]}"/></clipPath>' for f in featured)
           + '</defs>'
           + '<g class="herophoto" aria-hidden="true">' + "".join(
               f'<g class="lzc" data-country="{f["slug"]}">' + "".join(
                   f'<image class="lzf"'
                   f' clip-path="url(#lzc-{f["slug"]})"'
                   f' x="{f["box"][0]:.1f}" y="{f["box"][1]:.1f}"'
                   f' width="{f["box"][2]:.1f}" height="{f["box"][3]:.1f}"'
                   f' preserveAspectRatio="xMidYMid slice"'
                   f' href="{esc(fr["href"])}"/>'
                   for j, fr in enumerate(f["frames"]) if fr["href"] and j == 0)
               + '</g>' for f in featured)
           + '</g>') if featured else "")
        # ORDER: terrain, then water, then the frontiers over both. Water is
        # a separate visual layer and must never inherit land shading — a
        # river under the relief would be tinted by the band it crosses and
        # would change colour coming down a valley — and a frontier under the
        # relief is not there at all.
        + (f'<g class="lyr lyr-rivers" aria-hidden="true">{water}</g>'
           if water else "")
        + (f'<g class="lyr lyr-country-bounds" aria-hidden="true">{bounds}</g>'
           if bounds else "")
        # THE NAMES, ABOVE THE FRONTIERS AND UNDER THE DUSK — so a name in
        # the east dims with the ground it is written on rather than floating
        # over it. `aria-hidden`, because the accessible name of each country
        # is already on its link and a screen reader should not hear fifty
        # countries twice.
        + (seanames if not beyond_ground else "")
        + (f'<g class="lyr lyr-labels" aria-hidden="true">{names}</g>'
           if names else "")
        # THE DUSK, LAST AND OVER EVERYTHING THE ATLAS DREW. Two rectangles
        # of graphite whose alpha ramps along the two data cuts, masked to
        # the atlas's own land. It is not a cartographic layer and is not in
        # ORDER: it is the light in the room, and the reason the continent
        # dissolves eastward into the ground it stands on rather than ending.
        # THE GRAIN IS ON THE LAND AND NOT ON THE WHOLE PICTURE. It covered
        # the frame first, and the frame is the SVG — which is 78% of the
        # hero, inset right, with bare background either side of it. The
        # result was a hard vertical seam down the middle of the Atlantic
        # between grained water and smooth water. Masked to the land it
        # cannot have an edge, and the land is what was flat: the sea has the
        # shore band and the deep-water ramp now, and paper is what the
        # continent is printed on.
        + f'<rect class="herograin" aria-hidden="true" mask="url(#herodim)"'
        f' x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}"'
        f' height="{vh:.0f}" filter="url(#herograin)"/>'
        # THE MASK BELONGS ON ONE OF THE TWO, AND PUTTING IT ON BOTH LEFT A
        # HARD BLACK WEDGE ACROSS THE TOP-RIGHT OF THE HOMEPAGE.
        #
        # `herodim` is the atlas's own land, and it was on the GROUP. The
        # eastern shadow therefore stopped at every coastline: Russia went to
        # graphite and the Barents Sea, the Black Sea and the Caspian beside
        # it stayed bright Atlantic teal, while the ground beyond the atlas —
        # graphite, opaque, cut dead straight along 52°E — began right there.
        # Measured across that boundary: (42, 95, 115) to (0, 0, 0) in one
        # pixel, a hard diagonal edge through the picture that opens the site,
        # exactly the rendering fault the fades exist to remove.
        #
        # The eastern rectangle is unmasked now, so the water dissolves with
        # the land it surrounds and there is nothing for the ground to abut.
        # THE SOUTHERN ONE KEEPS THE MASK, and not for symmetry: the drawing
        # is 78% of the hero inset right, so an unmasked southern shadow —
        # opaque at the bottom-left, where its radius about the cone apex is
        # largest — painted a straight vertical seam down the drawing's own
        # left edge, over open Atlantic, behind the headline. The southern cut
        # is only visible where it crosses LAND, so masking it to land costs
        # nothing and removes that edge.
        # AND THE EASTERN RECT IS MASKED TO THE LAND WHERE THERE IS NO
        # GROUND. It is unmasked on the drawn hero on purpose — the water
        # has to dissolve with the land it surrounds, or the shadow stops
        # at every coastline and the ground beyond begins on a hard
        # diagonal. With no ground and no painted sea there is nothing for
        # it to abut and nothing outside the land for it to dim, so an
        # unmasked rect is a wash over a white page: the fade's only job
        # here is to stop Russia ending on a straight line at 52°E.
        + ('' if not beyond_ground else f'<g class="herodusk" aria-hidden="true">'
        + f'<rect x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}"'
        f' height="{vh:.0f}" fill="url(#heroedge)"/>'
        + f'<rect x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}"'
        f' height="{vh:.0f}" mask="url(#herodim)" fill="url(#herofootg)"/></g>')
        + f'</svg></div>'
    )


def plate_sequence(plates, anchor=None):
    """The bands of a plate page, numbered by what is DRAWN.

    Five pages compose a plate sequence and each spelled this line itself —
    the homepage, /journeys, /experiences, /plan and now /stories, the last
    of them in a fourth spelling producing the same bytes. *A second
    implementation of a thing is a second chance to make its mistake*, and
    this one already has a mistake worth not repeating: **the number comes
    from the rendered sequence, not from the declared list.**
    `enumerate(PLATES, 1)` filtered afterwards numbers first and filters
    second, so an omitted band leaves a hole — with a register holding one
    photograph the homepage printed 01, 02, 05, 06, 07, 08, which
    `section-audit.py` failed on in the one state that produces it. *The
    selector that COUNTS is the selector that DRAWS*, which this repository
    records about two CSS counters and is equally true of a number composed
    in Python.

    A plate is `(classes, name, inner)` or `(classes, name, inner, anchor)`;
    with no anchor of its own it takes `act<n>`, which is how the homepage
    numbers its own.
    """
    out = []
    for i, plate in enumerate([p for p in plates if p[2]], 1):
        slug, name, inner = plate[0], plate[1], plate[2]
        at = plate[3] if len(plate) > 3 else f"act{i}"
        cls = " ".join("sheet-" + c for c in slug.split())
        out.append(f'<section class="sheet {cls}" id="{at}">'
                   f"{actmark(i, name)}{inner}</section>")
    return "\n".join(out)


def actmark(n, name):
    """The running furniture of a plate sequence: a number, a rule, a name.

    It is the only thing that repeats down this page, and it is what makes
    eleven bands read as one sequence rather than as a stack of sections —
    the finding that rebuilt this page. The number is set at reading size
    and the name at label size, because the number is the position and the
    name is the caption.
    """
    return (f'<p class="actmark"><span class="actno">{n:02d}</span>'
            f'<span class="actname">{esc(name)}</span></p>')


def golink(href, label, cls=""):
    """A circle, a rule, a tracked label. The one link shape on this page.

    It replaced `.waygo`'s bare arrow for a reason the contact sheet made
    obvious: an arrow after a sentence reads as a button that lost its box,
    and this page has no boxes at all. A mark that is drawn rather than typed
    belongs to the drawing family the rest of the page is made of.
    """
    return (f'<a class="go{cls}" href="{href}">'
            f'<span class="gomark" aria-hidden="true"></span>'
            f'<span class="golabel">{esc(label)}</span></a>')



def home(data):
    """Six plates in one sequence: the door, the question, the landscape,
    the journey, the atlas, the message.

    THE PAGE WAS A STACK OF SECTIONS AND IS NOW A SEQUENCE OF PLATES.

    What it was: a hero, a form, a band of four doors, a band of three
    journeys, a band of stories and a closing note — every one a real
    surface, and the sum reading as a content-management template with the
    content changed. Measured across four rendered proposals and four
    grammars, the fault was never the styling: it was that the spatial
    grammar repeated. Nav, hero, rule, text, cards, map, text, cards.

    What it is: six numbered plates, each with its own identity and its own
    margins — monumental, typographic, photographic, cartographic,
    typographic, empty — carrying the act number as the only running
    furniture. A plate is a BAND rather than a viewport, so the whole
    sequence is a page a reader can see the shape of rather than a scroll
    deck they have to travel through.

    EVERY FIGURE ON IT IS DERIVED. The journey's distance is the sum of the
    haversines between its own stops, its countries are counted from its own
    legs, and the fifty are the fifty this atlas holds. A benchmark for this
    page carried "3,400 km · 12 countries · 28 places" for the same journey;
    ours is 4,993 km, seven countries and thirteen stops, and the difference
    is the whole reason a number on a page is computed here rather than set.
    """
    ncountries = len(data["countries"])
    ncities = len(data["cities"])
    nregions = sum(len(c["regions"]) for c in data["countries"].values())
    idx = data["cities"]
    images = data.get("images") or {}

    # THE OPENING TAKES A PHOTOGRAPH WHEN ONE IS LICENSED, AND THE PATH TO IT
    # HAD BEEN GONE SINCE THE PLATE SEQUENCE LANDED. `data/image-purposes.json`
    # declares `homepage-hero` against the register key `home-hero`, the brief
    # for it is `docs/hero-brief.md`, and `checks.py` still reads that key in
    # three places — and nothing on this page asked `picture()` for it. A
    # purpose that reaches no surface is an acquisition nobody would ever see:
    # the workflow would fetch it, hash it, register it, pass every gate and
    # publish a photograph onto a page that does not reference it, which is
    # exactly the failure `c_photo_published` exists to name and which
    # `photo-tests.py` reported twelve times.
    #
    # A PHOTOGRAPH REPLACES THE DRAWING; IT DOES NOT SIT BEHIND IT. That rule
    # is already recorded here and it is why this asks the register directly
    # rather than letting `picture()` fall back: `picture()` returns a
    # generated plate with no row, which is right on a card and wrong on the
    # one opening the plate system has been MEASURED unable to carry.
    #
    # Nothing on the page changes today. The register holds no `home-hero`,
    # so the drawn continent is what a reader gets, exactly as now.
    # THE MAP IS IN THE HERO, AT THE OWNER'S DIRECTION, AND THE REASONING
    # IT OVERRULES IS KEPT RATHER THAN DELETED. `section-audit.py` §7
    # records why it was taken out: it made a data surface the first thing
    # a reader met on a page whose job is to make them want to go
    # somewhere, and it inlined 90 KB of coastline to do it. Both halves
    # are answered rather than ignored — this is `constellation()`, the
    # same 12 KB drawing the body plates use, not the 90 KB instrument,
    # and it carries no filter row, no legend and no `data-role`, which is
    # what that assertion actually pins. What changed is the judgement
    # about what belongs first, and that judgement is the owner's.
    #
    # The photograph did not lose its surface: `home-hero` is the
    # full-bleed window on plate 02, which is the largest a picture gets
    # anywhere on this site. A purpose that stops reaching a surface is
    # the failure `c_purpose_reaches` exists to name.
    #
    # AND IT IS THE ATLAS, NOT THE CONSTELLATION. The first version of this
    # panel drew `constellation()` — 319 dots on a silhouette — because it
    # is the cheap drawing the body plates use. That is a DIAGRAM: it says
    # how many destinations there are and nothing about Europe. The thing
    # a reader is being handed the door to is the continent itself, with
    # its relief, its rivers, its frontiers and its countries named, and
    # this repository draws exactly one of those. It costs bytes and the
    # ceiling moves deliberately, which is what `weight.home_kb` is for.
    #
    # AND THE PANEL IS A RECTANGLE. The aperture is the signature and it
    # is on 824 plates, every social card and every embedded map; on the
    # one surface that is already the largest picture on the site, cutting
    # it again makes the drawing a decoration of its own frame. *A
    # signature applied to everything is wallpaper* — `docs/
    # signature-moments.md` says so, and question 2 for this surface is
    # answered by the picture rather than by its edge.
    # THE LIVING ATLAS: the featured countries, their clip and their frames.
    # `doc` is the same europe-lod1 document the drawing itself reads, loaded
    # once here and handed down, because a second load is a second chance for
    # the aperture and the country under it to be different geometry.
    _lz = living_atlas(data, images, geo.load("europe-lod1.json"))
    _heromap = heroeurope(data, featured=_lz, beyond_ground=False)
    _hero_row = images.get("home-hero")

    # THE PANEL IS THE SAME STATE, WRITTEN OUT. One active country and one
    # active frame drive the aperture, the name, the line under it, the link
    # and the credit — so there are not five components to keep in step,
    # there is one state and five readings of it. Every frame is in the
    # markup, which is what makes the no-JavaScript answer the FIRST frame of
    # the first country rather than nothing: the enhancement moves a
    # `data-on` attribute and fetches the picture it just revealed.
    #
    # AND THE CREDIT TRAVELS WITH THE FRAME. Pexels' guidelines ask for the
    # photographer credited with a link to the photo's own page and a
    # prominent link to Pexels, and `picture()` derives both from the
    # register row. An SVG `<image>` can hold neither — it is one href — so
    # the credit for whichever frame is showing is here, generated from the
    # same row, and it changes with the picture it describes.
    # NO CREDIT ON THE HERO, AT THE OWNER'S DIRECTION, AND THE OBLIGATION
    # DOES NOT GO AWAY WITH IT.
    #
    # This was a "Currently exploring" panel and then a line naming
    # forty-one photographers, which at the sizes a credit is set in ran to
    # seven lines under the picture — a second thing to read on the one
    # plate whose job is to be looked at. Both are off.
    #
    # What cannot be off is the credit itself. Pexels' guidelines are
    # quoted in docs/data-licenses/photo-providers.json with the archived
    # page behind them: *"Whenever you are doing an API request make sure to
    # show a prominent link to Pexels"* and *"Always credit our
    # photographers when possible"*. That is a licence condition on every
    # photograph in the register, not a design preference, and this site
    # refuses a photograph whose provenance is incomplete in four places.
    #
    # So the credit moves to the COLOPHON at the foot of the sheet, beside
    # the line that names Natural Earth and the elevation surveys — which is
    # exactly what a colophon is for — and it is one sentence rather than
    # forty-one names, because each of these photographs is already
    # credited by `picture()` on its own country's page, with the
    # photographer, their profile and the licence. The link to Pexels is on
    # the page the photographs are on, which is what the guideline asks.
    _lzpanel = ""

    # ── 01 · THE DOOR ────────────────────────────────────────────────
    # The wall is paper and the opening is the only dark thing on the
    # screen. That is the aperture's own reading — light wall, dark opening
    # — applied at the largest size it appears anywhere, and it is the
    # correction to the first version of this plate, which was graphite with
    # a graphite arch inside it: the one thing the page exists to show,
    # invisible against its own ground.
    door = f"""
  <div class="doorgrid">
  <div class="sheettext">
    <h1 class="mega">Open the door <br>to <em class="lit">Europe</em>.</h1>
    <p class="lede">{numword(ncountries, cap=True)} countries. {numword(nregions)} travel
    regions. A continent of living cultures, extraordinary places and endless
    ways to belong.</p>
    {golink('/plan', 'Begin your journey')}
    <div class="figrow">
      <div><b>{ncountries}</b><span>Countries</span></div>
      <div><b>{nregions}</b><span>Travel regions</span></div>
      <div><b>{ncities}</b><span>Destinations</span></div>
      <div><b>{len(data["journeys"])}</b><span>Journeys</span></div>
    </div>
  </div>
  <div class="doorside">
  <div class="op">{_heromap}</div>
  {_lzpanel}
  </div>
  </div>"""

    # THE SET THIS ROOM HANGS — derived, and two of the three rules are
    # refusals rather than preferences.
    #
    # ONE PER MACRO REGION, NOT "THE BEST FIVE". This atlas holds no
    # ranking and refuses one on `/for-businesses` in those words. The
    # question is where will you go, so the answer is SPREAD.
    #
    # AND AN ADVISORY COUNTRY IS NEVER OFFERED. The first build of this
    # plate put MINSK on the homepage: Belarus carries `advisory.level:
    # avoid` and is stripped from `/api/atlas.json` at build time. A
    # derived selection is not automatically an honest one.
    macro_of = {}
    for m in data.get("macros", []):
        for cs in (m.get("countries") or []):
            macro_of[cs if isinstance(cs, str) else cs.get("slug")] = m["slug"]
    seen_macro, picks = set(), []
    for cid, e in idx.items():
        if ("city:" + cid) not in images:
            continue
        if (e["country"].get("advisory") or {}).get("level"):
            continue
        mac = macro_of.get(cid.split("/")[0])
        if mac is None or mac in seen_macro:
            continue
        seen_macro.add(mac)
        picks.append((cid, e))
    picks = picks[:5]

    def _phot(keys):
        """One credit line for a row, paid once. The licence asks for the
        photographer and the provider, not a caption per frame."""
        # A KEY THE REGISTER DOES NOT HOLD IS SKIPPED, NOT A KeyError. Every
        # caller passes the keys of a band it has already filtered, so this
        # is unreachable on the real register — and `contact_sheet.py` builds
        # this page with a register holding ONE row, which is the state the
        # whole credit line exists to describe honestly. A credit names the
        # photographs that are ON the page; a key with no row is a photograph
        # that is not.
        out, seen = [], set()
        for k in keys:
            if k not in images:
                continue
            nm = images[k]["photographer"]
            if nm in seen:
                continue
            seen.add(nm)
            out.append(f'<a href="{esc(images[k]["source"])}" rel="noopener" '
                       f'target="_blank">{esc(nm)}</a>')
        return ('<p class="sheetcred rowcred">Photographs by '
                + ", ".join(out) + " on Pexels.</p>") if out else ""

    # ── 02 · THE WINDOW ──────────────────────────────────────────────
    # THE ONE FULL-BLEED PICTURE ON THE PAGE, and it is the window: fixed
    # to the viewport while the wall scrolls past it. A gallery has one
    # wall you walk up to, and a quiet room earns exactly one of these.
    window = ""
    if _hero_row:
        _cl = data["home"]["closing"]
        window = f"""
  <div class="shotclip"><div class="shotfull">{picture(images, "home-hero", w=2400, h=1400,
      alt=_hero_row["alt"], sizes="100vw", credit=False, eager=True)}</div></div>
  <div class="sheettext">
    <h2 class="mega">{esc(_cl["head"]).replace(" is not", " <br>is not")}</h2>
    <p class="lede">{esc(_cl["body"])}</p>
    {golink('/beyond-the-obvious', 'Beyond the obvious')}
  </div>
  <p class="sheetcred">Photograph <a href="{esc(_hero_row["source"])}" rel="noopener"
  target="_blank">{esc(_hero_row["photographer"])}</a> · {esc(_hero_row["licence"])}</p>"""

    # ── 03 · THE PLACES ──────────────────────────────────────────────
    # A FEATURE, NOT A CONTACT STRIP. Five equal tiles 211 pixels wide
    # with a name under each is the eight-equal-tiles failure this
    # repository has already measured twice, at five: nothing in the row
    # is the subject, so the eye reads a catalogue of content types and
    # moves on. `docs/non-home-redesign.md` declares the scale that fixes
    # it — a feature is asymmetric at 1.35 against .65, "because two equal
    # columns read as a layout and an unequal pair reads as a picture with
    # something to say" — and this is the one band on the homepage with
    # five real photographs to spend on it.
    #
    # So the first destination is the picture and the other four are the
    # list beside it. Which one leads is not a judgement: `picks` is one
    # destination per macro region in the atlas's own order, and the lead
    # is simply the first of them.
    #
    # AND THE SEARCH FORM CAME OFF THIS PLATE. It was a tool dropped into
    # the middle of a gallery — an input 243 pixels wide with its own
    # placeholder clipped, between a headline about looking at places and
    # the places themselves. It is the one interactive thing on this page
    # and it belongs where an invitation belongs, which is the end: it is
    # on plate 08 now, beside the closing statement.
    # AND THE BAND IS OMITTED WHEN THERE IS NOTHING TO LEAD IT WITH. `picks`
    # is one photographed destination per macro region, so it is EMPTY for a
    # register holding none — which was every register before the first
    # tranche merged, and is the register `contact_sheet.py` builds when it
    # renders this page once per candidate: it swaps in ONE row so the sheet
    # shows that candidate and nothing else. `picks[0]` then raised
    # IndexError and took the whole acquisition suite down with it, which is
    # the crash-stops-counting fault this file records twice, arriving in a
    # page BUILDER rather than in a gate. Every other band here is already
    # guarded — `if inner` in the plate loop drops an empty one — and this is
    # the one that could not produce an empty string because it died first.
    places = ""
    if picks:
        _lead, _rest = picks[0], picks[1:5]
        _lc, _le = _lead
        placerows = "".join(
            f'<a class="pl" href="{urls.city(e["country"], e["region"], e["city"])}">'
            f'<span class="plshot">'
            f'{picture(images, "city:" + cid, w=400, h=400, credit=False, alt=images["city:" + cid]["alt"], sizes="7rem")}'
            f'</span>'
            f'<span class="pltext">'
            f'<span class="plwhere">{esc(e["country"]["name"])}</span>'
            f'<span class="plname">{esc(e["city"]["name"])}</span></span>'
            f'<span class="plgo" aria-hidden="true">→</span></a>'
            for cid, e in _rest)
        places = f"""
      <div class="galwrap">
      <div class="sheettext">
        <h2 class="mega">One destination from <br>each corner of the continent.</h2>
        <p class="lede">Europe changes with what you seek — mountains or coastlines,
        cities or quiet places. Every one of these is the first place this atlas
        would send you in its corner of the continent.</p>
      </div>
      <div class="feat">
        <a class="featlead" href="{urls.city(_le["country"], _le["region"], _le["city"])}">
          {picture(images, "city:" + _lc, w=1200, h=1500, credit=False,
                   alt=images["city:" + _lc]["alt"],
                   sizes="(min-width: 62rem) 46vw, 92vw")}
          <span class="featwhere">{esc(_le["country"]["name"])}</span>
          <span class="featname">{esc(_le["city"]["name"])}</span>
          <span class="featline">{esc(_le["city"].get("summary", ""))}</span>
        </a>
        <div class="featlist">{placerows}</div>
      </div>
      {_phot(["city:" + c for c, _e in picks[:5]])}
      </div>"""

    # ── 04 · THE CROSSING ────────────────────────────────────────────
    # A JOURNEY'S PICTURE IS ONE OF ITS OWN STOPS, NOT ITS `journey-hero`.
    # The automated fill searches the role's first concept and got
    # railways: three of the nine journey photographs are the same
    # commuter station at Geesthacht and not one is about its journey.
    # The Media Desk's own note names that trade — nothing looks at the
    # photograph before it is live. So this takes the picture it can
    # defend: a destination ON the route.
    #
    # AND IT SAYS WHAT IT MEASURED. Every distance here is a haversine
    # between two coordinates; for a year the journey pages printed that
    # as the journey. "Straight line" is the correction, and §7 asserts it.
    jrows, jkeys = [], []
    for j in data["journeys"]:
        if len(jrows) == 3:
            break
        stops = [idx[l["city"]] for l in j["legs"] if l["city"] in idx]
        shot = next(("city:" + l["city"] for l in j["legs"]
                     if ("city:" + l["city"]) in images), None)
        if not shot or len(stops) < 2:
            continue
        jkeys.append(shot)
        names = " · ".join(esc(e["city"]["name"]) for e in stops[:4])
        if len(stops) > 4:
            names += f" · +{len(stops) - 4} more"
        jrows.append(
            f'<a class="jr" href="{urls.journey(j)}">'
            f'{picture(images, shot, w=900, h=560, credit=False, alt=images[shot]["alt"], sizes="13rem")}'
            f'<span><span class="jrname">{esc(j["name"])}</span>'
            f'<span class="jrstops">{names}</span></span>'
            f'<span class="jrgo">View →</span></a>')
    crossing = ""
    if jrows:
        jf = data["journeys"][0]
        jl = [idx[l["city"]]["city"] for l in jf["legs"] if l["city"] in idx]
        jkm = int(round(sum(haversine(jl[i], jl[i + 1]) for i in range(len(jl) - 1))))
        jfacts = [(f"{jkm:,} km", "Straight-line distance"), (str(len(jl)), "Stops")]
        crossing = f"""
  <div class="galwrap">
  <div class="sheettext">
    <h2 class="mega">Europe reveals itself <br>when you move through it.</h2>
    <dl class="figures">{"".join(
        f'<div><dd>{esc(v)}</dd><dt>{esc(k)}</dt></div>' for v, k in jfacts)}</dl>
    <p class="lede">Measured on {esc(jf["name"])}. Every distance here is a straight
    line between two coordinates — the ground route is longer.</p>
  </div>
  <div class="jrows">{"".join(jrows)}</div>
  {_phot(jkeys[:3])}
  </div>"""

    # ── 05 · THE ATLAS ───────────────────────────────────────────────
    # PALE AND PRECISE. The graphite instrument belongs to the dark world;
    # on a white wall the same drawing reads as an engraving, which is
    # what "MAPS = precise" asks for. Every dot is a destination this
    # atlas holds, and the count beside it is the number of dots.
    # NO SECOND DRAWING HERE. The map moved to the hero, and two copies of
    # one continent on one page is the fault §7 already names — eleven
    # maps, and a reader who stopped seeing destinations at all.
    clist = "".join(
        f'<a href="{urls.country(c)}">{esc(c["name"])}</a>'
        for c in sorted(data["countries"].values(), key=lambda c: c["name"]))
    atlas = f"""
  <div class="galwrap">
  <div class="sheettext">
    <h2 class="mega">One continent. <br>{numword(ncountries, cap=True)} doors.</h2>
    <p class="lede">Every country has its own way in — {ncities} places drawn
    on one projection, the same file as every other map here.</p>
    {golink('/map', 'Open the map')}
  </div>
  <div class="countrycols">{clist}</div>
  </div>"""

    # ── 06 · THE READING ─────────────────────────────────────────────
    # A CONTENTS PAGE WITH A LEAD, WHICH IS WHAT NINE ESSAYS ARE.
    #
    # This band showed TWO stories as two 4:3 photographs side by side —
    # a card grid, and the exact shape `/stories` was rebuilt out of:
    # "nine essays are a contents page: one list, newest first, the desk as
    # a kicker on the piece it belongs to". It also showed two of nine,
    # silently, which is a selection wearing the clothes of a set — the
    # same `[:8]` failure plate 02 already records one band over.
    #
    # So: the newest story is the LEAD and carries the one photograph, at
    # the width a lead deserves, with its standfirst; every other story is
    # a line — desk, title, reading time — and all nine are here. The
    # pictures the register holds for the other six are not spent, and that
    # is the point: a contents page that illustrated every line would be
    # the grid again with smaller pictures.
    _st = sorted(data.get("stories", []),
                 key=lambda x: x.get("published", ""), reverse=True)
    reading = ""
    if _st:
        _lead_st = next((x for x in _st if ("story:" + x["slug"]) in images),
                        _st[0])
        _others = [x for x in _st if x["slug"] != _lead_st["slug"]]
        _leadshot = (picture(images, "story:" + _lead_st["slug"], w=1400, h=933,
                             credit=False,
                             alt=images["story:" + _lead_st["slug"]]["alt"],
                             sizes="(min-width: 62rem) 52vw, 92vw")
                     if ("story:" + _lead_st["slug"]) in images else "")
        _rows = "".join(
            f'<a class="rd" href="/stories/{esc(x["slug"])}">'
            f'<span class="rddesk">{esc(x.get("section", "Story"))}</span>'
            f'<span class="rdtitle">{esc(x["title"])}</span>'
            f'<span class="rdmin">{esc(x.get("reading", ""))}</span></a>'
            for x in _others)
        reading = f"""
  <div class="galwrap">
  <div class="sheettext">
    <h2 class="mega">Read the continent <br>differently.</h2>
  </div>
  <div class="lead">
    <a class="leadshot" href="/stories/{esc(_lead_st["slug"])}" aria-label="{esc(_lead_st["title"])}">{_leadshot}</a>
    <div class="leadtext">
      <p class="rddesk">{esc(_lead_st.get("section", "Story"))} · {esc(_lead_st.get("reading", ""))}</p>
      <h3 class="leadtitle"><a href="/stories/{esc(_lead_st["slug"])}">{esc(_lead_st["title"])}</a></h3>
      <p class="leadstand">{esc(_lead_st.get("standfirst", ""))}</p>
    </div>
  </div>
  <div class="rdlist">{_rows}</div>
  {_phot(["story:" + _lead_st["slug"]])}
  </div>"""

    # ── 07 · THE YEAR ────────────────────────────────────────────────
    # THE EVENTS FAMILY'S OWN CHART RATHER THAN FOUR SEASON CARDS. A
    # photograph captioned "Winter" would be an authored claim about a
    # picture taken somewhere else, on a page whose every other figure is
    # derived. The chart says what this atlas actually argues: October is
    # one of the thinnest months for what is ON and the deepest for
    # countries in their quieter shoulder — and a row of four seasonal
    # cards would have drawn the opposite.
    year = f"""
  <div class="galwrap">
  <div class="sheettext">
    <h2 class="mega">Every month opens <br>a different Europe.</h2>
    <p class="lede">What is on, and where the crowds are not. The bar above the line
    is the fixtures this atlas holds that month; the bar below is how many countries
    are in their quieter shoulder.</p>
    {golink('/events', 'Open the calendar')}
  </div>
  <div class="yearwrap">{year_band(data)}</div>
  </div>"""

    # ── 08 · THE MESSAGE ─────────────────────────────────────────────
    closing = data["home"]["closing"]
    # AND THE ASK IS HERE, at the end, where an invitation belongs. It was
    # in the middle of plate 03 — a tool between a headline about looking
    # at places and the places themselves, with its own placeholder clipped
    # by the button beside it. A reader who has come down eight plates has
    # seen what this atlas is; this is the sentence that hands it to them.
    message = f"""
  <div class="sheettext">
    <h2 class="mega">Open <br>the door.</h2>
    <p class="lede">Find the Europe waiting beyond the obvious itinerary.</p>
    <form class="askhero" action="/plan" method="get">
      <label for="homeask">Say it in your own words.</label>
      <input type="text" id="homeask" name="ask" autocomplete="off"
             placeholder="Somewhere quiet, in October.">
      <button class="btn" type="submit">Plan my journey</button>
    </form>
    {golink('/discover', esc(closing["cta"]))}
  </div>"""
    # THE SHEET'S OWN SOURCES, in the margin voice, at the foot of the last
    # plate. The page draws land on two plates and relief on one, and the
    # standing rule is that a page which draws land names where the land came
    # from — coverage that depends on a different element being present is
    # worse than none. The projection is stated with its four angles because
    # /map is not the only page that publishes it: a claim about geometry
    # belongs on every page that acts on it.
    #
    # The benchmark this sequence is drawn against carries no such line. It
    # is an illustration; this is a published atlas, and the difference is
    # exactly this sentence.
    relief = (" " + cartography.RELIEF_CREDIT) if "lyr-terrain" in _heromap else ""
    # NO SOURCE CREDIT FOR THE PHOTOGRAPHS ON THIS PAGE, AT THE OWNER'S
    # DIRECTION, AND THE PROVENANCE IS UNTOUCHED.
    #
    # The colophon names Natural Earth and the two elevation surveys
    # because a page that DRAWS land names where the land came from — that
    # rule is about geographic data and it stands. A sentence naming the
    # photographs' upstream marketplace is a different thing: it is a
    # supplier's name on the composition, and the owner's instruction is
    # that a supplier is not part of this product's visual identity.
    #
    # SOURCE PROVENANCE IS INVISIBLE INFRASTRUCTURE UNLESS A SPECIFIC
    # REQUIREMENT PUTS IT ON A PARTICULAR SURFACE. Every record is kept:
    # `data/images.json` holds the photographer, their profile, the source
    # page, the licence and its URL, the SHA-256 of the bytes as served and
    # the date they were fetched; `checks.py` still refuses a published
    # page referencing a file with no row and still re-hashes every
    # original; the licence gate still refuses an acquisition before it
    # opens a socket. What changed is where that record is PUBLISHED, and
    # the answer is /sources, which is the page this site already built for
    # exactly this question and which every map credit already points at.

    colophon = (
        f'<p class="sheetsource">Coastline, frontiers, rivers and lakes from '
        f'<a href="/sources">Natural Earth</a>, public domain, on a Lambert '
        f'conformal conic — standard parallels {geo.LCC_P1:g}°N and '
        f'{geo.LCC_P2:g}°N, origin {geo.LCC_LAT0:g}°N, central meridian '
        f'{geo.LCC_LON0:g}°E — the same projection and the same file as every '
        f'other map here.{relief} <a href="/map">Open the map →</a></p>')
    message += colophon

    # EIGHT PLATES, AND THE RHYTHM IS THE DESIGN. The sequence alternates
    # what a band IS rather than what it contains: photograph, white,
    # photograph, graphite, white, photograph, pine, white. The old sequence
    # was paper, paper, photograph, paper, paper, paper — six plates that
    # differed in content and not in kind, which is the design-direction
    # finding this repository keeps re-making one level up from the h1.
    #
    # The white strips are what make it read. They are the rests: a reader
    # comes off a full-bleed photograph onto a page that is suddenly, plainly
    # white, and the picture behind them stops instead of fading into more
    # cream. Photography is the emotional layer and the graphite atlas is the
    # navigation one — the two are deliberately never adjacent.
    # EIGHT ROOMS IN ONE GALLERY. The rhythm here is not colour — it is
    # SCALE. A quiet room alternates what a band asks of the eye: type,
    # then one picture you walk up to, then four hung in a line, then a
    # list you read, then an engraving, then two essays, then a chart,
    # then a sentence. The owner's own instruction is the argument: UI
    # restrained, PHOTOGRAPHY rich, MAPS precise, TYPOGRAPHY dramatic —
    # so colour appears as a mark and never as a field, and the white
    # wall contributes nothing on purpose.
    PLATES = [("door gal", "The door", door),
              ("bleed", "The window", window),
              ("places gal", "The places", places),
              ("crossing gal quiet", "The crossing", crossing),
              ("atlas gal", "The atlas", atlas),
              ("reading gal quiet", "The reading", reading),
              ("year gal", "The year", year),
              ("end gal", "The message", message)]
    # THE NUMBER COMES FROM THE RENDERED SEQUENCE, NOT FROM THE DECLARED LIST.
    # `enumerate(PLATES, 1) if inner` numbers first and filters second, so an
    # omitted band leaves a hole: with a register holding one photograph the
    # places, crossing and atlas plates return "" and the page printed 01, 02,
    # 05, 06, 07, 08 — which `section-audit.py` failed on, correctly, in the
    # one state that produces it. **The selector that COUNTS is the selector
    # that DRAWS**, which this repository already records about two CSS
    # counters; the same sentence is true of a number composed in Python.
    # Latent on the real register, where all eight bands render — and latent
    # is not fixed: the day a band is legitimately empty the sequence lies.
    body = constel_defs() + plate_sequence(PLATES) + ad_slot("/")

    return "/index.html", page(
        SITE_NAME, body, path="/", area=None, hero=True,
        description="Discover, plan and experience Europe: an atlas of every country, region and city, a journey planner, curated cross-border routes and local experiences.",
        og=("europedoor:home", "peaks", "EuropeDoor — open the door to Europe"),
        ld_blocks=[
            {"@context": "https://schema.org", "@type": "WebSite",
             "name": SITE_NAME, "url": ORIGIN,
             "description": SITE_TAGLINE,
             "inLanguage": "en",
             "publisher": LD_PUBLISHER,
             "potentialAction": {
                 "@type": "SearchAction",
                 "target": {"@type": "EntryPoint",
                            "urlTemplate": ORIGIN + "/search?q={search_term_string}"},
                 "query-input": "required name=search_term_string"}},
        ],
    )

# ── atlas ─────────────────────────────────────────────────────────────

def countries_index(data):
    """The European Atlas: the continent, then a country, then the index.

    *Discover = Let Europe answer. Countries = Know the continent.* The
    brief's grammar is CONTINENT -> MAP -> COUNTRY -> INDEX -> REGIONS ->
    PHOTOGRAPHIC ATLAS -> FINAL, and its instruction is a refusal:
    *"Countries is not a directory of 50 destinations. It is EuropeDoor's
    living digital atlas: geography first, country second, photography
    third, index fourth. The map provides authority, photography provides
    emotion, and the index provides navigation. Build those as distinct
    layers and do not collapse them into generic cards."*

    THE LIBRARY WAS NOT THE CONSTRAINT AND THE MARGIN WAS THE WIDEST YET.
    The register holds a photograph of every one of the fifty countries, one
    of each of the nine macro regions, and the index's own hero — sixty
    pictures relevant to this page — and the page drew ONE. That is the
    /experiences finding and the /stories finding a third time, on the
    family with the most photographs available and the fewest shown.
    Nothing was acquired; see `docs/countries-redesign.md`.

    AND THE BRIEF'S STRONGEST IDEA WAS ALREADY BUILT. *"The actual country
    polygon should become the visual focus … so the country itself becomes
    the aperture."* `heroeurope()` has clipped a photograph into a country's
    own path since the Living Atlas; `country_door()` is that at the
    country's own extent, which is the one thing the homepage could not do —
    its own measurement says a photograph clipped into Belgium on a
    continental frame *"renders about 40 pixels wide and is a smudge with a
    coastline."*

    WHAT IS KEPT: the nine macro bands. The brief flattens /countries into
    one list of fifty, and flattening is the single thing that would cost
    this page something it already has — each band drawing its own members
    on its own frame is what tells the Nordics from the Caucasus before a
    word is read, and it is the measurement that rebuilt this family. So the
    sequence is the brief's and the grouping is kept.
    """
    images = data.get("images") or {}
    cs = data["countries"]
    nreg = sum(len(c["regions"]) for c in cs.values())

    # ── WHICH COUNTRY GETS THE LARGE DOOR, DERIVED RATHER THAN CHOSEN.
    # A "selected country" in the brief is a hover state, and this page
    # loads no JavaScript — its only <script> is the inert JSON-LD block. So
    # the selection is a measurement instead, and the measurable question is
    # the one /journeys already asks about its featured route: which is the
    # one this atlas can actually SHOW. Counted over the register, France
    # carries 37 photographs of itself, its regions, its cities and its
    # places against Croatia's 18 and Austria's 17. The figure is printed,
    # so a reader can see it is a count rather than a preference, and it
    # moves on its own as `stage: fill` reaches the rest.
    shot_count = {}
    for k in images:
        if ":" not in k:
            continue
        fam, tgt = k.split(":", 1)
        if fam in ("country", "region", "city", "place"):
            shot_count[tgt.split("/")[0]] = shot_count.get(tgt.split("/")[0], 0) + 1
    doors = []
    for slug, n in sorted(shot_count.items(), key=lambda kv: (-kv[1], kv[0])):
        c = cs.get(slug)
        if c is None:
            continue
        m = country_door(data, images, c, brief=(not doors))
        if m:
            doors.append((c, n, m))
    lead = doors[0] if doors else None

    # ── HOW MANY DOORS THE PHOTOGRAPHIC BAND DRAWS, BOUNDED BY BYTES.
    # All 41 drawable doors together are 628 KB of inlined geometry against a
    # `weight.max_page_kb` ceiling of 441, so the whole set is not a layout
    # question at all — it is 187 KB over the largest page this site is
    # allowed to serve. The costliest single door is Norway at 62 KB, and the
    # first version of this comment said Russia at 107: RUSSIA IS ADVISORY AND
    # `country_door` REFUSES IT, so the number quoted as the reason for the
    # budget was the size of a door that is never drawn. A count picked by eye
    # would be taste; the budget is the quantity that actually binds, so the
    # band takes doors in the derived order until it has spent DOOR_BAND_KB,
    # and the page states how many that turned out to be. The set therefore
    # grows when the geometry gets cheaper and shrinks when it does not, which
    # is the right way round — and it SKIPS rather than stops, so Finland (9
    # photographs, an expensive coast) is passed over and Bulgaria, Albania
    # and Armenia get in behind it.
    band, spent = [], 0
    for c, n, m in doors[1:]:
        if spent + len(m) > DOOR_BAND_KB * 1024:
            continue
        band.append((c, n, m))
        spent += len(m)

    # ── 01 · THE CONTINENT ───────────────────────────────────────────
    # TWO CALLS FOR TWO DRAWINGS, AND ONE STRING IN TWO PLACES SHIPPED TWO
    # IDENTICAL GRADIENT IDS. `region_glyph` at the full extent emits
    # `cut_fade`, whose ids carry a build-wide counter precisely so two
    # drawings on one page cannot collide — and a counter cannot help when
    # the SAME emitted string is interpolated twice. It was invisible while
    # the register holds `countries-hero`, because then plate 01 draws the
    # photograph and the fallback is never used; `photo-tests.py` frees that
    # purpose to acquire against its stub, rebuilt, and `c_unique_ids`
    # reported `rg2edge` and `rg2foot` twice on this page. *A code path
    # nothing exercises is a code path nothing checks*, and the one thing
    # that exercises this one is the gate suite for photographs. Two calls
    # cost 40 KB only in the state where two continental drawings are what
    # the page has anyway.
    open_ = f"""
  <div class="sheettext">
    {head_extent([(len(cs), "countries"), (nreg, "travel regions"),
                  (len(data['cities']), "cities")])}
    <h1 class="mega">Europe, country by country.</h1>
    <p class="lede">{numword(len(data['macros']), cap=True)} regions,
    {len(cs)} countries, {nreg} travel regions and {len(data['cities'])}
    cities &mdash; every one of them written here rather than imported.</p>
  </div>
  <div class="atlasopen">{photo(images, "countries-hero", w=2000, h=1500,
      sizes="(min-width: 62rem) 52vw, 100vw") or region_glyph(list(cs))}</div>"""

    # ── 02 · THE MAP ─────────────────────────────────────────────────
    # AND THE CUT IS SAID RATHER THAN HIDDEN. At the continental extent
    # Russia arrives with the 52°E data cut in it — a straight slant across
    # the top right, which is the rendering fault `constel_defs` drops the
    # whole context to avoid and the hero spends 320 units of fade on.
    # Neither escape is available here: the sliced ring is a MEMBER rather
    # than context, and reframing cannot lose it without losing the
    # Caucasus. The number is read off the dataset's own bbox.
    lim = (geo.load("europe-lod1.json") or {}).get("bbox", [None, None, None])[2]
    cutsay = (f" Russia's outline stops at {lim:.0f}&deg;E, where this atlas's "
              f"map data ends, not at a border.") if lim is not None else ""
    themap = f"""
  <div class="sheettext">
    <h2 class="mega">Where the countries sit.</h2>
    <p class="lede">A geographic beginning before the alphabetical one. Each
    of the {len(cs)} countries is drawn on its own, so the frontiers are the
    picture.{cutsay}</p>
  </div>
  <div class="atlasmap">{region_glyph(list(cs))}</div>
  <p class="actions">
    <a class="btn" href="/map">Open the map</a>
    <a class="btn ghost" href="/discover">Start from what you like</a>
  </p>"""

    # ── 03 · THE COUNTRY AS THE APERTURE ─────────────────────────────
    door = ""
    if lead:
        c, n, m = lead
        door = f"""
  <div class="sheettext">
    <h2 class="mega">Every country is a door.</h2>
    <p class="lede">{esc(c['name'])} drawn on its own frontier with a
    photograph of it inside the outline. Not a picture beside a map: the
    country is the aperture, which is the one thing this atlas can draw that
    a list of names cannot.</p>
  </div>
  {m}
  <div class="doorsay">
    <p class="kicker">{esc(c['name'])}</p>
    <p class="dsay">{esc(c['tagline'])}</p>
    <p class="small">{esc(c['name'])} is the country this atlas can show
    best: the register holds {n_of(n, 'photograph')} of it, its regions, its
    cities and its places, against {band[0][1] if band else 0} for the next.
    That is a count rather than a preference, and it moves as the library
    fills. {n_of(len(doors), 'country')} can be drawn this way today;
    {numword(len(cs) - len(doors))} cannot, and the reason is geometry rather
    than choice &mdash; six of them have no outline in this dataset at all
    and are drawn as a ringed point, and three carry a travel advisory and
    are never lit.</p>
    <p class="actions"><a class="btn" href="{urls.country(c)}">Open
    {esc(c['name'])}</a></p>
  </div>"""

    # ── 04 · THE INDEX ───────────────────────────────────────────────
    # THE UTILITY LAYER, AND IT IS TYPE. *The index provides navigation* —
    # so it is fifty names a reader can scan and nothing else: no picture,
    # no count, no tagline. Nineteen initials rather than twenty-six,
    # because that is how many the fifty names actually start with, and an
    # A-Z that prints ten empty letters is a shape standing in for a set.
    groups = {}
    for c in sorted(cs.values(), key=lambda x: x["name"]):
        groups.setdefault(c["name"][0].upper(), []).append(c)
    azrows = "".join(
        f'<div class="azgroup"><p class="azletter">{esc(k)}</p><ul class="azlist">'
        + "".join(f'<li><a href="{urls.country(c)}">{esc(c["name"])}</a>'
                  + (' <span class="azwarn">advisory</span>'
                     if (c.get("advisory") or {}).get("level") else "")
                  + '</li>' for c in v)
        + '</ul></div>' for k, v in sorted(groups.items()))
    # AND THIS BAND IS THE PAGE'S HEAD. A plate sequence has no room for a
    # stage above its opening, so the head is the band that introduces the
    # set — /journeys and /experiences settled that one family over. The
    # index IS the set here, literally, so it is the honest place for the
    # extent: *an index exists to say how big a set is*, and every figure is
    # derived rather than typed.
    azband = f"""
  <div class="pagehead index">
    <p class="kicker">The European Atlas</p>
    <h2 class="mega">The index.</h2>
    <p class="lede">All {len(cs)} countries, alphabetically, under the
    {numword(len(groups))} letters they actually start with &mdash; not
    twenty-six, because ten of those begin nothing. Behind them:
    {nreg} travel regions and {len(data['cities'])} cities.</p>
  </div>
  <div class="azindex">{azrows}</div>"""

    # ── 05 · THE NINE REGIONS ────────────────────────────────────────
    # AND THE NINE MACRO PHOTOGRAPHS CAME ON. Each of the nine appeared on
    # exactly one page — its own — and the band whose entire subject is
    # those nine regions drew none of them. Same finding as the fifty, one
    # level up.
    #
    # THEN THE BAND WAS 63% OF THE PAGE, AND `tools/monotony.js` IS THE ONLY
    # THING HERE THAT COULD SAY SO. Nine regions that differ by 12x in
    # destinations, 6.6x in extent and 14x in photographs, drawn as nine
    # identical 1,250-pixel compositions — the worst figure on the site, on
    # a page already redesigned once, because the page-level recomposition
    # kept this band's shape and only moved it. That is exactly the fault
    # the owner named when he added the second doctrine rule: *do not
    # optimise for visual consistency at the expense of editorial
    # difference*, which replaces card monotony with band monotony.
    #
    # SO THE COMPOSITION IS THE REGION'S OWN SHAPE. `macro_shape` measures
    # it in kilometres and the three rhythms are its two natural boundaries
    # — taller than wide, wider than tall, and more than twice as wide as
    # tall. The nine fall 4 / 3 / 2, so the band carries three rhythms
    # rather than one and the largest repeated composition is four.
    #
    # ORIENTATION RATHER THAN SCALE, AND THAT IS THE DEPARTURE FROM
    # /themes. That page derives three band SIZES from a theme's reach,
    # which is a claim about importance; a region is not more important for
    # being wide. Nothing here is drawn larger than anything else — what
    # changes is which way up each region is, which is a fact about the
    # ground and the one thing nine boxes of one shape cannot say.
    blocks = []
    for m in data["macros"]:
        rows, mcity = [], 0
        for slug in m["countries"]:
            c = cs[slug]
            ncity = sum(len(r["cities"]) for r in c["regions"])
            mcity += ncity
            rows.append({"href": urls.country(c), "title": c["name"],
                         "sub": c["tagline"],
                         "meta": f"{n_of(len(c['regions']), 'region')} · "
                                 f"{n_of(ncity, 'city')}",
                         "flag": "advisory" if c.get("advisory") else ""})
        kw, kh, asp = macro_shape(data, m)
        shape = ("mac-pan" if asp >= MACRO_WIDE
                 else "mac-up" if asp >= 1.0 else "mac-por")
        # AND THE MEASUREMENT IS PRINTED, because a composition a reader
        # cannot check is decoration that happens to vary. The eyebrow
        # carries the extent that chose the rhythm beside the two counts,
        # rounded to ten kilometres rather than to the kilometre — a
        # haversine box across a region is not accurate to a kilometre and
        # printing one would be a precision this figure does not have.
        # AND THE THREE RHYTHMS ARE NOT NAMED ON THE PAGE. "Panoramic" is a
        # word about the layout, and a reader who is told the Mediterranean
        # is 3,600 km across and 1,310 deep can see which way up it is
        # without the page explaining its own grid back to them — which is
        # *never explain the constraint back*, and the sentence under the
        # nine states the rule once.
        # AND THE CREDIT IS THE STANDARD ONE, because these pictures are not
        # inside a link. `.credit` is `picture()`'s own figcaption, revealed
        # on hover and on `:focus-visible` — which is how every photograph on
        # this site that CAN carry one does, and it is what the owner's
        # standing position asks for: provenance is invisible infrastructure
        # unless a legal requirement wants it visible on that surface. The
        # aggregated `sheetcred rowcred` line exists for the other case, a
        # picture wrapped in an `<a>`, where an anchor inside an anchor ends
        # the outer one and the reveal rule loses its subject. Here the link
        # is on the heading, so there is no nesting and nothing to aggregate.
        pic = photo(images, "macro:" + m["slug"], w=1200, h=900,
                    sizes="(min-width: 62rem) 26vw, 92vw")
        # AND THE GLYPH IS FRAMED ON THE REGION'S OWN PROPORTION. Passing no
        # aspect holds it to the canvas's 1.282, which measured 42% padding
        # on Eastern Europe and 3% on the Caucasus: the drawing carries the
        # shape the composition is derived from, or the composition is
        # arguing about something the picture does not show. A DRAWING is
        # free to be reshaped where a photograph is not — a derived
        # proportion on `macro:` would be a crop on a surface the register
        # does not declare, which is what /themes refused `object-fit:
        # cover` for.
        blocks.append(
            f'<section class="macroband {shape}" id="{esc(m["slug"])}">'
            f'<div class="macrotop">'
            f'<div class="macrosay">'
            f'<p class="ed-eyebrow">{n_of(len(m["countries"]), "country")} · '
            f'{n_of(mcity, "destination")} · '
            f'{round(kw, -1):,.0f}&thinsp;×&thinsp;{round(kh, -1):,.0f}&thinsp;km</p>'
            f'<h3><a href="{urls.macro(m)}" class="nodec">{esc(m["name"])}</a></h3>'
            f'<p class="rowsub">{esc(m["blurb"])}</p></div>'
            f'<figure class="macroshot">{pic}</figure>'
            f'<figure class="macroart">'
            f'{region_glyph(m["countries"], macro_frame(data, m), aspect="own")}'
            f'</figure>'
            f'</div>{ed_rows(rows, level=4)}</section>')
    # AND THE NINE ARE NINE DRAWINGS RATHER THAN ONE, WHICH WAS TESTED AND
    # REFUSED. The obvious composition for a partition is to draw it once —
    # fifty countries on one continent with the nine groups told apart —
    # and it cannot be drawn honestly here. Telling nine areas apart on one
    # drawing needs nine tones, the owner's palette refuses an eight-hue
    # wheel in as many words (*"I would NOT make every page colorful. This
    # is critical"*), and nine steps inside the atlas's one stone are the
    # *rounding error with a token name* this repository already refuses for
    # a surface ladder. The seams cannot carry it either: a region boundary
    # is where two member groups meet and this atlas holds country rings
    # rather than topology, so a stroke on a group strokes every internal
    # frontier at region weight. Nine frames is what the data supports.
    widths = sorted((macro_shape(data, m)[2], m["name"]) for m in data["macros"])
    regband = f"""
  <div class="sheettext">
    <h2 class="mega">The {numword(len(data['macros']))} regions.</h2>
    <p class="lede">Editorial travel regions rather than administrative
    ones: they group places that feel like each other and are usually
    visited together. Each is drawn on its own ground at its own proportion,
    because that is what separates them before a word is read &mdash;
    {esc(widths[-1][1])} measures nearly three times as wide as it is deep
    and {esc(widths[0][1])} is the other way up, and the two had been drawn
    as the same shape.</p>
  </div>
  <div class="macrostack">{''.join(blocks)}</div>"""

    # ── 06 · THE PHOTOGRAPHIC ATLAS ──────────────────────────────────
    atlasband = ""
    if band:
        atlasband = f"""
  <div class="sheettext">
    <h2 class="mega">{numword(len(band) + 1, cap=True)} of them, filled.</h2>
    <p class="lede">The same drawing at a smaller size, {numword(len(band))}
    more times. Every outline is the country's own and every photograph is of
    the country inside it &mdash; taken in the order of how much of each one
    this atlas can show, skipping the ones whose outline is too expensive to
    inline rather than stopping at a number somebody chose.</p>
  </div>
  <div class="doorstack">{''.join(m for _c, _n, m in band)}</div>"""

    # ── 07 · WHICH DOOR ──────────────────────────────────────────────
    close = f"""
  <div class="atlassay">
    <h2 class="mega">Which door will you open?</h2>
    <p class="lede">{len(cs)} countries, {nreg} travel regions and
    {len(data['cities'])} cities, every one of them written here. Start from
    the continent, or from what you like.</p>
    <p class="actions">
      <a class="btn" href="/map">Open the map</a>
      <a class="btn ghost" href="/discover">Start from what you like</a>
    </p>
  </div>"""

    # THE PLATE SLUGS ARE UNIQUE ON PURPOSE. `sheet-open` is /stories', and
    # *a class name already in the stylesheet is a rule you inherit
    # silently* — the finding that cost four collisions in one run and has
    # no guard. Every name here was grepped against the stylesheet before it
    # was written, and three were changed for it: `sheet-door` is the
    # homepage's opening plate with 29 rules, `doorgrid` is that plate's own
    # grid, and `macroband` is KEPT because its one rule is this family's.
    PLATES = [("atlasopen gal", "The continent", open_, "the-continent"),
              ("atlasmap paper", "Where they sit", themap, "the-map"),
              ("aperture gal", "The country as the door", door, "the-door"),
              ("az gal quiet", "The index", azband, "the-index"),
              ("regions gal", "The nine regions", regband, "the-regions"),
              ("filled paper", "Filled", atlasband, "filled"),
              ("atlasclose gal", "Which door", close, "which-door")]

    body = f"""
{crumbs([("Europe", "/discover"), ("Atlas", None)])}
{constel_defs()}
{plate_sequence(PLATES)}
<p class="small">A macro region is the one grouping in this atlas with real
borders behind it &mdash; a travel region is a set of destinations and is shown
as those destinations rather than given a boundary it does not have.
{geo.sources_line(geo.load("europe-lod0.json"))}</p>
"""
    return "/countries/index.html", page(
        "Countries", body, path="/countries", area="countries", hero=True,
        description="Every country in Europe, drawn on its own frontier with a photograph of it inside the outline, grouped into nine travel regions.",
    )


def macromap(data, m):
    """A macro region as the countries it is made of.

    THE ONLY GEOGRAPHIC FAMILY WITH NO GEOGRAPHY. Every other one draws its
    subject: a country its borders, a region its destinations, a journey its
    route, a motion its answer, a month its fixtures. A macro region — the
    Nordics, the Caucasus and the Bosphorus — was a headline and a grid of
    nine cards, and the reader was told which countries are in it without
    ever being shown where it is.

    And it is the one grouping here that can be drawn honestly. Regions are
    refused a boundary because we hold which destinations belong to one and
    not its geometry; a macro region is a set of WHOLE COUNTRIES, and their
    polygons are Natural Earth's, already committed and already drawn on
    /map. Nothing is invented: the members are filled, everything else is
    context, and the frame is the members' own extent.
    """
    doc = geo.load("europe-lod0.json")
    if not doc:
        return ""
    members = set(m["countries"])
    boxes = [ent["bbox"] for ent in doc["countries"].values()
             if ent.get("slug") in members and ent.get("bbox")]
    if not boxes:
        return ""
    bbox = [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]
    w, h = 900, 420
    proj = geo.Projection(bbox, w, h, pad=0.10)
    ctx, land = geo.landmass(proj, (0, 0, w, h), doc=doc, highlight=members)
    uid = "mm" + "".join(ch for ch in m["slug"] if ch.isalnum())[:14]
    # The member names, at the middle of each country's own drawn extent,
    # through the same placement rule every other map uses.
    labels = []
    for ent in sorted(doc["countries"].values(), key=lambda e: e.get("name", "")):
        if ent.get("slug") not in members or not ent.get("bbox"):
            continue
        b = ent["bbox"]
        px, py = proj.xy((b[1] + b[3]) / 2.0, (b[0] + b[2]) / 2.0)
        got = place_label_box(px, py, ent["name"], w, h, cls="mmlabel",
                              off=9.0, prefer="over", metric="rlabel")
        if got:
            labels.append(got)
    drawn = "".join(phone_declutter(_declutter(
        [(0, x0, y0 + 14.0, lw + 8, lh + 4, html)
         for html, x0, y0, lw, lh in labels], w, h), frame=(w, h)))
    n = sum(len(data["countries"][cs]["regions"]) for cs in m["countries"]
            if cs in data["countries"])
    cap = (f'The {len(members)} countries of {esc(m["name"])}, filled, with the '
           f'rest of Europe behind them. Borders and coastline from '
           f'<a href="/sources">Natural Earth</a>, public domain. '
           f'<a href="/map">The whole map →</a>')
    # AN ILLUSTRATION, NOT AN INSTRUMENT. A macro region drawn as its member
    # countries is a picture of where the Nordics are; it carries no scale
    # bar, no layers and nothing to operate. It was the last editorial map
    # still in the graphite palette, which is the black-land-on-black-water
    # the standard forbids for editorial geography.
    return cartography.plate(
        uid=uid, w=w, h=h, proj=MAPPROJ, view=(0, 0, w, h),
        cut_reach=dusk_reach(),
        land=f"{ctx}{land}", labels=drawn,
        caption=f'<figcaption>{cap}</figcaption>',
        figure_class=f"minimap macromap arched atlas{dense_class(drawn)}",
        aria=(f'Map of {esc(m["name"])}: its {len(members)} countries filled, '
              f'the rest of Europe behind them'))


def pageband(data, key, alt_fallback=""):
    """The opening photograph of a page family, or nothing at all.

    ONE FUNCTION FOR EVERY FAMILY THAT OPENS ON A PHOTOGRAPH. Six copies of
    the same eight lines is six places for the rule to drift, which is what
    happened to map-label placement in four families before
    `place_label_box()` was written — three of them offered one position and
    the fourth offered four.

    AND IT RENDERS NOTHING WITH NO PHOTOGRAPH. `picture()` returns a
    generated plate when the register has no row, which is right on a card
    and wrong at the top of a page: a slot waiting for a picture is honest
    and three hundred pixels of one is a hole, which the homepage measured
    and the four doors were resized for. So this asks the register directly,
    exactly as the hero does, and a family with no photograph is the page it
    is today, unchanged.

    THE BAND IS ALWAYS AN ADDITION AND NEVER A REPLACEMENT. Every one of
    these families already opens on a DRAWING that is its signature moment —
    a country portrait, a region constellation, a route, a tag drawn across
    Europe — and each of those says something a photograph cannot. Replacing
    one would be the /map failure: a page going on stating a claim about a
    drawing that is no longer there.
    """
    row = (data.get("images") or {}).get(key)
    if not row:
        return ""
    return ('<figure class="pageband">'
            + picture(data.get("images"), key, w=2400, h=1030,
                      alt=row.get("alt") or alt_fallback, eager=True,
                      sizes="100vw")
            + "</figure>")


def head_figure(data, key, fallback, alt_fallback="", credit=True, eager=True):
    """The right-hand side of a page's opening: a photograph, or the drawing.

    THE BENCHMARK PUTS THE PICTURE BESIDE THE TYPE AND THIS PUT IT ABOVE IT.
    `pageband()` renders the opening photograph as a full-width band over the
    head, which is a magazine's cover and not its opening spread: the reader
    meets a picture, then a headline, then the drawing that headline is
    about, and the three never compose into one statement. Every one of these
    families ALREADY lays its head out as type beside a figure — the country
    portrait, the region constellation, a journey's route — so the
    photograph belongs in that figure's place, and the drawing moves down to
    a band of its own where its caption still explains it.

    AND THE DRAWING IS NEVER LOST, which is the rule `pageband` was written
    under: "replacing one would be the /map failure — a page going on stating
    a claim about a drawing that is no longer there." The caller emits it
    below with `moved_drawing()` when a photograph took its place; with no
    photograph this returns the drawing itself and the page is exactly what
    it is today.
    """
    row = (data.get("images") or {}).get(key)
    if not row:
        return fallback
    # `credit=False` WHERE THE FIGURE SITS INSIDE A LINK, AND AN <a> MAY NOT
    # CONTAIN AN <a>. `picture()`'s credit carries the photographer and the
    # provider as links, so a figure placed inside a row anchor makes the
    # parser SPLIT that anchor: the themes index rendered thirteen rows as a
    # mixture of full rows, 33-pixel empty ones and a picture with no text
    # beside it. The homepage's row of eight lost a whole layout to this and
    # the escape is the same — the container pays the attribution once — so
    # the caller says which case it is rather than finding out.
    return ('<figure class="headshot">'
            + picture(data.get("images"), key, w=1600, h=1200,
                      alt=row.get("alt") or alt_fallback, eager=eager,
                      sizes="(min-width: 60rem) 46vw, 100vw", credit=credit)
            + "</figure>")


def moved_drawing(data, key, drawing, caption):
    """The family's own drawing, below, on the pages where a photograph took
    the head. Returns nothing at all when there is no photograph, because
    then the drawing never moved."""
    if not (data.get("images") or {}).get(key) or not drawing:
        return ""
    return section("Where it is", f'<div class="movedraw">{drawing}</div>',
                   lede=caption)


def photostrip(data, items, limit=6):
    """A rail of photographs of the things below — and only the ones that
    exist.

    THE BENCHMARK CARRIES FOUR TO SIX PHOTOGRAPHS ACROSS THE FOOT OF NEARLY
    EVERY PAGE, and this atlas draws maps there instead. Both are right: a
    map answers WHERE and a photograph answers WHAT IT LOOKS LIKE, and the
    second is the question a reader browsing a country is actually asking.

    It composes as the library fills, which is the property the homepage's
    theme row already has: `items` is [(register key, name, url)] and a key
    the register does not hold is simply not in the rail. With none of them
    held the rail is not drawn at all — a slot waiting for a picture is
    honest, and a row of six empty frames is a page saying the library is
    thin.
    """
    reg = data.get("images") or {}
    have = [(k, n, u) for k, n, u in items if k in reg][:limit]
    if not have:
        return ""
    cells = "".join(
        f'<a class="pstile" href="{esc(u)}">'
        + picture(reg, k, w=560, h=700, alt=reg[k].get("alt") or n,
                  sizes="(min-width: 60rem) 16vw, 40vw", credit=False)
        + f'<span class="psname">{esc(n)}</span></a>'
        for k, n, u in have)
    # THE RAIL PAYS ITS ATTRIBUTION ONCE, under the row, exactly as the
    # homepage's row of eight does: six figcaptions under six thumbnails is
    # noise, and the licence asks for the photographer and the provider.
    who = ", ".join(dict.fromkeys(
        f'<a href="{esc(reg[k]["source"])}" rel="noopener" target="_blank">'
        f'{esc(reg[k]["photographer"])}</a>' for k, _n, _u in have))
    return (f'<div class="pstrip">{cells}</div>'
            f'<p class="sheetcred rowcred">Photographs by {who} on Pexels.</p>')


def macro_page(data, m):
    """A macro region, and the countries it is made of.

    THE CARD GRID WAS RIGHT AND ITS PICTURES WERE NOT. Five like things
    chosen partly on look is the case a card was designed for and the reason
    this family kept its grid when the region and month pages lost theirs.
    But the picture on each was a landscape generated from the country's
    slug, directly under a map that draws those same five countries filled
    and named — so the page said "here is where Norway is" and then showed a
    hash-drawn mountain instead of Norway.

    A country's picture on this site is its SHAPE. /countries and /discover
    both draw a macro region as `region_glyph`, and this is the same function
    with one member lit instead of all of them, on the region's own frame —
    so the five cards are five different outlines a reader can recognise
    before reading a word, framed identically so they can be compared, which
    is what a grid of like things is for.
    """
    cards = []
    for cs in m["countries"]:
        c = data["countries"][cs]
        ncity = sum(len(r["cities"]) for r in c["regions"])
        meta = (f'<p class="cardmeta">{n_of(len(c["regions"]), "region")} · '
                f'{n_of(ncity, "city")} · {esc(c["budget"])} cost</p>')
        # FRAMED ON THE COUNTRY, NOT ON THE REGION. The first version framed
        # all five on the macro region's own extent, and the Nordics' extent
        # is Iceland to Finnish Lapland — so every card drew almost the whole
        # continent with one small country lit, which is the identical-picture
        # fault that framing exists to stop, arrived at from the other side.
        pts = [project(t["lat"], t["lon"])
               for r in c["regions"] for t in r["cities"]]
        # level=2: the grid of member countries IS this page, so its cards
        # are the top level under the h1. A card's heading is an h3 where the
        # cards sit inside a band and the band's own h2 is above them.
        cards.append(card(urls.country(c), c["capital"], c["name"], c["tagline"],
                          art=country_glyph(c["slug"], cs)
                              or region_glyph([cs], pts or None, min_span=340.0),
                          meta=meta, level=2))
    photoband = pageband(data, f"macro:{m['slug']}")
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], None)])}
{photoband}
<div class="pagehead overture">
  <p class="kicker">Region of Europe</p>
  <h1>{esc(m['name'])}</h1>
  <p class="lede">{esc(m['blurb'])}</p>
</div>
{constel_defs()}
{macromap(data, m)}
{grid(cards, 3)}
"""
    return f"/discover/{m['slug']}/index.html", page(
        m["name"], body, path=urls.macro(m), area="countries",
        description=m["blurb"],
    )


# THE LARGEST SCALE THE SOURCE CAN CARRY, AND NO LARGER. A portrait blows a
# country's outline up to 416 pixels, and at that size a simplified polygon
# stops being an outline and becomes a claim about a shape. Measured as the
# MEDIAN straight segment of the principal ring, as a fraction of that ring's
# own diagonal — the median rather than the longest, because Russia's longest
# segment is 52% of its diagonal and is the 52°E cut in the dataset, not a
# simplification, and its median is 0.31%:
#
#     Monaco 63.7%   Liechtenstein 37.5%   San Marino 35.6%   Malta 34.4%
#     Andorra 16.6%  Luxembourg 12.5%  |  Cyprus 5.7%  Kosovo 4.5%  Italy 0.9%
#
# The gap between Luxembourg and Cyprus is the widest in the distribution, so
# the line sits in it. Monaco came out of the first build as a TRIANGLE and
# San Marino as a hexagon, four hundred pixels tall, on the page whose entire
# job is to say what a place is.
#
# The five above the line that /map already knows about are the five it draws
# as a ringed point rather than an outline, for this exact reason; this is the
# same refusal one zoom level in, and it finds Luxembourg as well.
PORTRAIT_SEGMENT_MAX = 0.10


def _outline_coarseness(rings):
    """Median segment of the largest ring, over that ring's diagonal."""
    if not rings:
        return 1.0
    def parea(ring):
        pr = [geo.lcc(ring[i + 1], ring[i]) for i in range(0, len(ring), 2)]
        a = 0.0
        n = len(pr)
        for i in range(n):
            a += pr[i][0] * pr[(i + 1) % n][1] - pr[(i + 1) % n][0] * pr[i][1]
        return abs(a) / 2.0
    main = max(rings, key=parea)
    pr = [geo.lcc(main[i + 1], main[i]) for i in range(0, len(main), 2)]
    if len(pr) < 3:
        return 1.0
    xs = [q[0] for q in pr]
    ys = [q[1] for q in pr]
    diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    if diag <= 0:
        return 1.0
    segs = sorted(math.hypot(pr[(i + 1) % len(pr)][0] - pr[i][0],
                             pr[(i + 1) % len(pr)][1] - pr[i][1])
                  for i in range(len(pr)))
    return segs[len(segs) // 2] / diag


def _settingportrait(data, c, doc):
    """A country the source cannot draw, marked in the country it is in.

    THE ALTERNATIVE TO A MADE-UP OUTLINE IS NOT A BETTER OUTLINE. Six
    countries are smaller than the tolerance the atlas's cartographic source
    was simplified at: Monaco, Vatican City, San Marino, Liechtenstein,
    Andorra, Malta — plus Luxembourg, which the measurement finds and /map
    does not, because a shape 21 vertices long is convincing at continent
    scale and a polygon at 416 pixels.

    So the door opens on the SETTING instead, at a scale the source is good
    for: four degrees of latitude centred on the country, its neighbours drawn
    the way every other portrait draws them, and the country itself a ringed
    point at its own coordinates. That is the same mark and the same reason as
    /map's, one zoom level in, and for a micro-state it is not a lesser
    picture — being a speck against the Pyrenees or the Ligurian coast is the
    most specific true thing this atlas can draw about Andorra or Monaco.

    Nothing is invented and nothing is magnified past what it can bear.
    """
    if doc.get("bbox"):
        lon0, lat0, lon1, lat1 = doc["bbox"]
        clon, clat = (lon0 + lon1) / 2.0, (lat0 + lat1) / 2.0
    else:
        pts = [t for r in c["regions"] for t in r["cities"]]
        if not pts:
            return ""
        clon = sum(t["lon"] for t in pts) / len(pts)
        clat = sum(t["lat"] for t in pts) / len(pts)
    # Four degrees of latitude, about 440 km: the window at which the median
    # segment of the coarsest of these outlines falls under a pixel, so the
    # simplification is gone and the geography around it is not.
    half = 2.0
    bbox = [clon - half * 1.6, clat - half, clon + half * 1.6, clat + half]
    w = 520.0
    h = round(w / 0.86)
    proj = geo.Projection(bbox, w, h, pad=0.0)
    ctx, land = geo.landmass(proj, (0, 0, w, h), doc=geo.load("europe-lod1.json"))
    x, y = proj.xy(clat, clon)
    uid = "cs" + "".join(ch for ch in c["slug"] if ch.isalnum())[:14]
    return (
        f'<figure class="minimap portrait setting arched atlas" data-role="illustration">'
        f'<svg viewBox="0 0 {w:.0f} {h:.0f}" role="img" data-world="discover" '
        f'aria-label="{esc(c["name"])} marked at its own coordinates, among its '
        f'neighbours. No cartographic source this atlas holds draws an outline '
        f'for it at a size this picture could show, so it is a point rather '
        f'than an invented shape">'
        f'<defs>{arch_clip(uid, w, h)}</defs>'
        f'<g clip-path="url(#arch-{uid})">'
        f'<rect x="0" y="0" width="{w:.0f}" height="{h:.0f}" class="archground"/>'
        f'{ctx}{land}'
        f'<g class="cmark"><circle cx="{x:.1f}" cy="{y:.1f}" r="23"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" class="core"/></g>'
        f'</g>{arch_edge(w, h)}</svg></figure>'
    )


def terrain_paths(proj, view):
    """Relief, when this repository holds any. It holds none.

    NOT A STUB THAT DRAWS SOMETHING PLAUSIBLE. The layer exists so the
    architecture is complete and the gap is visible; it returns nothing
    because `data/geo/terrain-lod1.json` does not exist, and the day it does
    this is the one function that has to learn to read it.

    An invented hillshade would be the most convincing wrong thing in this
    repository — a reader cannot tell a fitted one from a decorative one,
    which is exactly why the Data Integrity Rule forbids authoring a
    measurement. See docs/cartography.md for what would fill it.
    """
    doc = geo.load("terrain-lod1.json")
    if not doc:
        return ""
    raise NotImplementedError(
        "data/geo/terrain-lod1.json has appeared and terrain_paths() has not "
        "been written. Failing loudly is the point: a layer that silently "
        "draws nothing once its data arrives is worse than one that was "
        "never declared.")


def hillshade_paths(proj, view):
    """Relief shading, when this repository holds any. It holds none.

    One light from the north-west at no more than 12% opacity, multiplied
    over the terrain tint and clipped to land — decided now so the day the
    data arrives is not a fresh argument about style. Never over flat
    ground: a hillshade on a plain invents structure that is not there.
    """
    doc = geo.load("hillshade-lod1.json")
    if not doc:
        return ""
    raise NotImplementedError(
        "data/geo/hillshade-lod1.json has appeared and hillshade_paths() has "
        "not been written.")


def hydrology_paths(proj, view):
    """Rivers and lakes, when this repository holds any. It holds none.

    Natural Earth publishes both under the same public-domain terms as the
    land already here, so this is a fetch a person can run rather than a
    licence anybody has to decide. The register carries the rows; the bytes
    are not in the repository, and the build must run on a host with no
    internet, so they never will be until somebody fetches them.
    """
    doc = geo.load("hydrology-lod1.json")
    if not doc:
        return ""
    raise NotImplementedError(
        "data/geo/hydrology-lod1.json has appeared and hydrology_paths() has "
        "not been written.")


def coast_halo(uid):
    """The soft band a printed atlas puts in the water along a coast.

    A TREATMENT, NOT A MEASUREMENT. This is drawn from the coastline this
    repository already holds, by stroking the land silhouette thickly in the
    water beneath the land fill. It is the cartographic convention that says
    "this edge is a coast"; it is NOT bathymetry, and it must never be
    mistaken for one — the atlas holds no depth data and nothing here implies
    a distance from shore or a number of metres.

    Emitted as a `<use>` of the landmass group rather than a second copy of
    the geometry, because the geometry is most of the bytes on these pages
    and the coastline of Europe is not worth paying for twice: the whole
    treatment costs about forty bytes per plate.
    """
    return f'<use href="#{uid}-land" class="coasthalo"/>'


def plate_stack(proj, view, *, ocean="", landmass="", subject="",
                places="", labels=""):
    """A cartographic plate, composed through the declared layer stack.

    ONE PAINT ORDER, DECIDED IN ONE PLACE. The plates used to concatenate
    three strings inline, which works right up to the moment a fourth layer
    arrives and every family has its own opinion about where it goes. The
    order lives in `geo.LAYERS`; this walks it.

    A layer whose dataset is absent contributes NOTHING — not an empty group,
    which on 1,033 pages is a claim that the map has terrain and simply had
    none here. `checks.py` asserts the shipped HTML carries exactly the
    layers this repository holds.
    """
    made = {
        "ocean": ocean,
        "coastal-water": "",   # a `<use>` of the land group; see coast_halo()
        "land": landmass,
        "terrain": lambda: terrain_paths(proj, view),
        "hillshade": lambda: hillshade_paths(proj, view),
        "rivers": lambda: hydrology_paths(proj, view),
        # Coastline and frontiers are the land group's own stroke today. When
        # terrain arrives they have to become their own stroke-only pass so
        # relief sits UNDER them, and that pass re-emits the geometry — about
        # 40% of the bytes on these pages. Measured then, not guessed now.
        "coastline": "",
        "country-bounds": "",
        "region-bounds": "",
        "cities": "",
        "destinations": places,
        "labels": labels,
        "route": "",
        "selected": subject,
    }
    out = []
    for name, _needs, drawn, _role in geo.layer_state():
        if not drawn:
            continue
        body = made.get(name, "")
        if callable(body):
            body = body()
        if body:
            out.append(geo.layer_group(name, body))
    return "".join(out)


def _star(cx, cy, r):
    """A five-pointed star for a capital.

    The one mark every printed atlas reserves for a capital, and the reason
    to draw it rather than enlarge a dot: a bigger dot says "more", a star
    says "different in kind". `capital` is authored per country, so this is a
    classification drawn, not a ranking invented.
    """
    import math as _m
    pts = []
    for i in range(10):
        a = -_m.pi / 2 + i * _m.pi / 5
        k = r if i % 2 == 0 else r * 0.42
        pts.append(f"{cx + k * _m.cos(a):.1f} {cy + k * _m.sin(a):.1f}")
    return "M" + "L".join(pts) + "Z"


def locator_inset(slug, size=132.0):
    """Where in Europe this is, at a glance, beside the plate.

    The benchmark plate carries one and it is the single cheapest thing on
    it: a reader who does not already know where Moldova is learns it in one
    look, and the main plate is then free to be about the country rather than
    about the continent. Same projection, same data, same aperture logic —
    the continent at lod0, the subject filled, nothing else marked.
    """
    doc = geo.load("europe-lod0.json")
    if not doc:
        return ""
    proj = geo.Projection([-24.0, 34.0, 45.0, 71.0], size * 1.02, size, pad=0.0)
    ctx, land = geo.landmass(proj, (0, 0, size * 1.02, size), doc=doc,
                             highlight=slug)
    # A RING, BECAUSE A SMALL COUNTRY IS A FEW PIXELS. Portugal filled at
    # 112px across Europe is three pixels of cobalt and a reader's eye never
    # finds it; the ring is what the benchmark plate does and it is the whole
    # value of an inset. Centred on the subject's own drawn extent.
    ring = ""
    box = _highlight_box(land)
    if box:
        cx, cy, r = box
        ring = (f'<circle class="locring" cx="{cx:.1f}" cy="{cy:.1f}" '
                f'r="{max(9.0, r + 5.0):.1f}"/>')
    return (f'<figure class="locator" aria-hidden="true">'
            f'<svg viewBox="0 0 {size * 1.02:.0f} {size:.0f}" '
            f'role="presentation">{ctx}{land}{ring}</svg>'
            f'<figcaption>in Europe</figcaption></figure>')


# ── whose ground is this ──────────────────────────────────────────────


def path_rings(d):
    """Every closed subpath of an emitted `d`, each behind its bounding box.

    The box in front means almost every sample is rejected by four
    comparisons rather than by a crossing test over a few hundred points.
    """
    out = []
    for sub in d.split("Z"):
        pts = [(float(a), float(b))
               for a, b in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", sub)]
        if len(pts) >= 3:
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            out.append(((min(xs), min(ys), max(xs), max(ys)), pts))
    return out


def ring_hit(pts, x, y):
    """Even-odd crossing test — the standard one, and it is exact."""
    hit = False
    j = len(pts) - 1
    for i, (px_, py_) in enumerate(pts):
        qx, qy = pts[j]
        if (py_ > y) != (qy > y) and \
                x < (qx - px_) * (y - py_) / (qy - py_) + px_:
            hit = not hit
        j = i
    return hit


class NameGround:
    """Whose country a point is on, for one drawing's set of country paths.

    A NAME MAY RUN OUT OVER THE SEA AND MAY NEVER RUN ACROSS A NEIGHBOUR.
    That is what a printed atlas does with Norway and with Chile, and it is
    two rules rather than one: the name's MIDDLE has to be on the country it
    names, so it cannot float off into the Atlantic, and the BAR of type has
    to stay off everybody else's ground, so it cannot lie across Bosnia.
    A bounding box is not a country — the middle of Croatia's box is in
    Bosnia — so both tests are against the real polygon.

    And "not one sample on a neighbour" is the wrong rule, measured: it left
    the hero ten names and dropped GERMANY, POLAND, SWEDEN, NORWAY, FINLAND
    and UNITED KINGDOM, which are exactly the countries a reader orients by.
    A printed atlas lets the ENDS of a name touch a neighbour. So the test is
    a fraction — ten samples, at most `CROSS_OK` of them elsewhere — and it
    is tried at zero first so the anchors choose the cleanest placement
    available rather than the first tolerable one.

    MODULE LEVEL BECAUSE THERE ARE TWO DRAWINGS THAT NAME COUNTRIES, and for
    the life of both only one of them had this. The hero carried these rules
    nested inside it; the country portrait composed its own name against the
    FRAME and against the labels already down, and against nothing else — so
    it was free to put the name anywhere that fit. Measured on the shipped
    pages with the browser's own isPointInFill: nine of the forty-three
    portraits that carry a name printed it entirely off its own country, and
    AUSTRIA, DENMARK and FRANCE were ten samples out of ten on somebody
    else's ground. That is the hero's own finding, one family over, and it is
    what a second copy of a rule always costs.
    """

    CROSS_OK = 2

    def __init__(self, ds):
        self.shapes = [path_rings(d) for d in ds]

    def own(self, mine, x, y):
        for bb, pts in self.shapes[mine]:
            if (bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]
                    and ring_hit(pts, x, y)):
                return True
        return False

    def crosses(self, mine, x, y):
        for k, rings in enumerate(self.shapes):
            if k == mine:
                continue
            for bb, pts in rings:
                if not (bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]):
                    continue
                if ring_hit(pts, x, y):
                    return True
        return False

    def crossings(self, mine, x0, y0, w0, h0):
        """Ten samples along the bar of type: seven on the baseline, three at
        cap height, because a name is a bar rather than a point."""
        mid_y = y0 + h0 / 2.0
        cap_y = y0 + h0 * 0.34
        n = 0
        for i in range(7):
            if self.crosses(mine, x0 + w0 * i / 6.0, mid_y):
                n += 1
        for i in range(3):
            if self.crosses(mine, x0 + w0 * (0.15 + 0.35 * i), cap_y):
                n += 1
        return n

    def fits(self, mine, x0, y0, w0, h0, tol=0):
        """THE MIDDLE IS THREE SAMPLES, NOT ONE. `LABEL_METRICS` is a fitted
        UPPER envelope on the width of a name, so the box this rule reasons
        about is a few units wider than the one the browser draws and their
        centres do not coincide. On a fragmented coast a few units is the
        difference between land and water: GREECE passed here and the
        browser's own `isPointInFill` put the rendered name's middle in the
        Aegean, which is the one instrument that can settle it because it is
        asking the drawing rather than the model.

        Chasing the model would not fix it — a fitted envelope will always
        differ from the render. What fixes it is not letting the decision
        hinge on a single point.
        """
        mid_y = y0 + h0 / 2.0
        return (all(self.own(mine, x0 + w0 * f, mid_y) for f in (0.42, 0.5, 0.58))
                and self.crossings(mine, x0, y0, w0, h0) <= tol)

    def anchors(self, mine, grid=13):
        """Points to try the name at, and every one of them is ON the country.

        AN OFFSET OF A RADIUS IS NOT A POINT INSIDE A COUNTRY. The portrait
        offered its name nine positions round the centre of the subject's
        bounding box, at fractions of `max(width, height) / 2` — which for a
        long thin country is a circle mostly in the sea. The moment the name
        was required to sit on its own ground, ITALY, NORWAY and SPAIN lost
        theirs: Italy's bounding-box centre is in the Adriatic and its radius
        is half the length of the peninsula, so not one of the nine anchors
        was on Italy. That is the hero's own lesson — a bounding box is not a
        country — arriving through the anchors instead of through the test.

        A grid over the bounding box, keeping the cells that fall inside the
        real polygon, ordered from the middle outwards so the centre-most
        placement is tried first. For a country the grid misses entirely
        (a microstate at this scale) the list is empty and the name is
        dropped, which is what happens today.

        AND THE LIST IS NOT TRUNCATED. Keeping the seventy closest to the
        middle was the obvious economy and it cost NORWAY its name: the cells
        nearest the centre of Norway's bounding box are all in the crowded
        south where the place labels already are, and the empty north was
        past the cut. An ordering is free; a truncation is a judgement about
        which half of a country a name may sit in.
        """
        boxes = [bb for bb, _ in self.shapes[mine]]
        if not boxes:
            return []
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        out = []
        for i in range(grid):
            for j in range(grid):
                x = x0 + (x1 - x0) * (i + 0.5) / grid
                y = y0 + (y1 - y0) * (j + 0.5) / grid
                if self.own(mine, x, y):
                    out.append((math.hypot(x - cx, y - cy), x, y))
        out.sort()
        return [(x, y) for _d, x, y in out]


def _highlight_box(land):
    """Centre and radius of the highlighted shape in an emitted <g>.

    Read back off the path text rather than recomputed, so the ring cannot
    disagree with the drawing it rings — the same reason the plate and the
    social card come from one geometry function.
    """
    m = re.search(r'class="[^"]*\bhere\b[^"]*"[^>]*\sd="([^"]+)"', land)
    if not m:
        m = re.search(r'<path[^>]*\sd="([^"]+)"[^>]*class="[^"]*\bhere\b', land)
    if not m:
        return None
    nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', m.group(1))]
    if len(nums) < 4:
        return None
    xs, ys = nums[0::2], nums[1::2]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    return cx, cy, max(max(xs) - min(xs), max(ys) - min(ys)) / 2.0


def countryportrait(data, c):
    """The country's own outline, as a portrait. COUNTRY = identity.

    The country page opened on a REFERENCE MAP: the country with its regions
    named, its destinations dotted, its neighbours drawn, a scale bar and a
    caption explaining that a region is a grouping. All of that is true and
    all of it is the country as a RECORD. It answers "what is in here", which
    is the question the bands below the fold are for.

    A country page is for a different question — what kind of place is this —
    and the answer a reader keeps is the shape, the name and one sentence.
    So the top of the page is a portrait: the outline filled, alone, with no
    label on it and nothing to operate. A portrait is not an instrument.

    THE DOOR IS TALL HERE, AND THAT IS THE POINT. The homepage's opening is
    wide because a continent is wide. A country is a figure, so it stands in
    a figure's doorway — which is what a door actually is, and what the arch
    was drawn from. The aperture's proportion follows its subject; a
    signature that is the same shape at every size is a stamp.

    The reference map is not deleted. It moves down to `Travel regions`,
    which is the band that needs it, and keeps every label, dot and note it
    had.

    Where a country has no polygon at 1:50 million — Monaco and Vatican City
    — there is no portrait rather than an invented one, on the same rule
    that gives them a ringed point on /map instead of a made-up outline.
    """
    doc = geo.country(c["slug"])
    if not doc:
        return ""
    ent = next((v for v in (doc.get("countries") or {}).values()
                if v.get("slug") == c["slug"]), None)
    rings = (ent or {}).get("rings") or []
    if not doc.get("bbox") or _outline_coarseness(rings) >= PORTRAIT_SEGMENT_MAX:
        return _settingportrait(data, c, doc)
    # THE DOOR'S PROPORTION FOLLOWS THE COUNTRY, and one fixed shape does not
    # work. Measured on the real projection across the 49 countries that have
    # a polygon: they run from 0.41 (Liechtenstein) to 1.86 (Austria), median
    # 1.13 — the median country is slightly WIDER than tall, and a fixed
    # 520x720 door filled only 61% of its short axis, worst case 39%. Austria
    # stood in a tall doorway as a small wide sliver with empty above and
    # below it, which is a portrait of nothing.
    #
    # Clamped to [0.62, 1.30] so it is always more upright than the
    # homepage's full-bleed opening and never becomes a letterbox: median
    # fill 100%, worst 66%, and only two of 49 under 70%.
    # THE FRAME IS THE PRINCIPAL LANDMASS, not everything the country owns.
    # Portugal's bbox reaches the Azores, 1,400 km into the Atlantic, and the
    # first version of this portrait drew a door nine-tenths full of empty
    # ocean with Portugal against one corner. See geo.principal_frame.
    bbox, outside = geo.principal_frame(doc, c["slug"])
    if not bbox:
        return ""
    lon0, lat0, lon1, lat1 = bbox
    xs, ys = [], []
    for i in range(9):
        t = i / 8.0
        for lon, lat in ((lon0 + (lon1 - lon0) * t, lat0),
                         (lon0 + (lon1 - lon0) * t, lat1),
                         (lon0, lat0 + (lat1 - lat0) * t),
                         (lon1, lat0 + (lat1 - lat0) * t)):
            x, y = MAPPROJ.xy(lat, lon)
            xs.append(x)
            ys.append(y)
    span_y = (max(ys) - min(ys)) or 1.0
    aspect = max(0.62, min(1.30, (max(xs) - min(xs)) / span_y))
    # THE viewBox HEIGHT IS FIXED AND THE WIDTH FOLLOWS THE COUNTRY, which
    # is the opposite of the obvious way round and is the only way the type
    # can be sized. A label is drawn in viewBox UNITS and the browser scales
    # the viewBox to the box it is given: with a fixed 520-unit width the
    # rendered size is 11 x (renderedWidth / 520), and every portrait is hung
    # at one CSS height with its width following its country — 258px for
    # Portugal, 541px for Austria. So the same declaration came out at 5.8px
    # on one page and 11.4px on another. This is the same defect measured
    # across the embedded maps at commit 39, met again from the other side.
    #
    # Fixing the viewBox HEIGHT makes units-to-pixels constant on every
    # country whatever its shape, so one font-size is one size everywhere.
    #
    # AND THE HEIGHT IS CHOSEN SO THE EXISTING MAP-LABEL SIZE IS THE RIGHT
    # ONE. 391 units against a 416px plate is 1.064 pixels per unit, so
    # `.minilabel`'s 11 units render at 11.7px — a size this stylesheet
    # already has. Picking a round 640 instead needed an 18px declaration,
    # which is a SEVENTEENTH font size in a file with a ceiling of sixteen,
    # bought for a number that is not even a rendered size: a label in an
    # SVG is in viewBox units. Choosing the frame instead of the type also
    # means the width model fitted for these labels applies unchanged rather
    # than being scaled, and that model is an upper envelope with a fixed
    # per-name cost that does not scale per character.
    h = 391.0
    w = round(h * aspect)
    proj = geo.Projection(list(bbox), w, h, pad=0.14)
    # NEIGHBOURS ARE CONTEXT, AND DISTANT COUNTRIES ARE QUIETER STILL.
    # France's plate was France plus twenty polygons of equal weight, all
    # asking to be read. The band is a country's distance from the subject on
    # this drawing, in the drawing's own units, so it is the same judgement
    # on a plate of Luxembourg and a plate of Ukraine.
    ctx, land = geo.landmass(proj, (0, 0, w, h), doc=doc, highlight=c["slug"],
                             bands=geo.distance_bands(doc, c["slug"], proj))
    # THE PLACE LAYER. A shape answers "what shape is this country"; an atlas
    # answers "where are the places". Every destination the atlas holds for
    # this country, at its own coordinate, unlabelled and not a link — the
    # reference map further down is the instrument and carries the names, the
    # touch targets and the scale bar. Here they are marks on a map, and the
    # `<title>` is what a screen reader gets.
    #
    # ALL OF THEM, OR NONE, AND NEVER A SELECTION. Picking "the five most
    # meaningful" would be a ranking this atlas does not hold and refuses to
    # invent — there is no `rank`, `featured` or `boost` on a place, in the
    # schema or anywhere else. The median country has FOUR destinations and
    # 41 of 50 have six or fewer, so for most of Europe every mark fits.
    #
    # AND THE PLACES ARE NAMED. A mark with no name answers "how many" and
    # not "where"; an atlas plate names what it draws. Same placement rule
    # as every other map here — right of the dot, then left, then under,
    # then over, each tested against the real curve of the aperture — and a
    # name that fits nowhere is dropped exactly as a colliding one is,
    # keeping its mark, its <title> and its row in the regions band below.
    # The capital is marked differently because it is the one place on a
    # country map every atlas distinguishes, and `capital` is authored data.
    cap_name = (c.get("capital") or {}).get("name") if isinstance(c.get("capital"), dict) else c.get("capital")
    pts_, placed_, labs_ = [], [], []
    for r_ in c["regions"]:
        for t in r_["cities"]:
            px, py = proj.xy(t["lat"], t["lon"])
            if 0 <= px <= w and 0 <= py <= h:
                pts_.append((px, py, t["name"]))
    # THE CAPITAL IS PLACED FIRST AND WINS EVERY COLLISION, then the places
    # we have written most about. Ordered by position alone, Lisbon's label
    # was dropped for Sintra's — 25 km apart, and the alphabet of latitude
    # decided which name a reader of Portugal's plate gets. The capital is
    # the one name a country plate may not lose; after it, the same depth
    # measure the reference map uses, so a country keeps Bordeaux and drops
    # Bonifacio rather than the other way round.
    def _depth(t):
        return (len(t.get("places", [])) * 2 + len(t.get("experiences", []))
                + len(t.get("highlights", [])))
    order_ = []
    for r_ in c["regions"]:
        for t in r_["cities"]:
            px, py = proj.xy(t["lat"], t["lon"])
            if 0 <= px <= w and 0 <= py <= h:
                iscap = bool(cap_name and t["name"].split(" &")[0] == cap_name)
                kind_ = t.get("city_type") or ""
                # MINOR LOCATIONS GIVE WAY FIRST. An atlas drops the smallest
                # names when a plate runs out of room, not whichever the
                # alphabet reached last: capital, then city, then everything
                # else by how much this atlas has written about it.
                rank_ = 0 if iscap else (1 if kind_ == "city" else 2)
                order_.append((rank_, -_depth(t), px, py,
                               t["name"], iscap, kind_))
    order_.sort()
    dotmarks, boxes_, minor, marks_, named_ = "", [], [], [], set()
    boxed_ = []



    def _try_label(px, py, text, cls, metric="minilabel", off=10.0,
                   prefer="beside", wrap=None, fits=None):
        """Place a label if it fits the aperture and hits nothing already there.

        One placement routine for every level of the hierarchy, so a region
        name and a village name compete on the same terms and in the order
        the hierarchy sets — which is the whole point of having one.
        """
        # THE TEST MOVED INSIDE THE PLACEMENT. It used to run on the position
        # place_label_box had already chosen, so a name that collided where it
        # wanted to go was dropped without trying the other three positions —
        # which is what those four positions are for.
        def _free(lx, ly, lw, lh):
            bx = (lx - LABEL_CLEAR, ly - LABEL_CLEAR,
                  lx + lw + LABEL_CLEAR, ly + lh + LABEL_CLEAR)
            return not any(not (bx[2] < q[0] or bx[0] > q[2]
                                or bx[3] < q[1] or bx[1] > q[3])
                           for q in boxes_)

        got = place_label_box(px, py, text, w, h, cls=cls, off=off,
                              prefer=prefer, metric=metric, clears=_free,
                              wrap=wrap, fits=fits)
        if not got:
            return False
        lhtml, lx, ly, lw, lh = got
        boxes_.append((lx - LABEL_CLEAR, ly - LABEL_CLEAR,
                       lx + lw + LABEL_CLEAR, ly + lh + LABEL_CLEAR))
        labs_.append(lhtml)
        boxed_.append((lhtml, lx, ly, lw, lh, cls))
        return True

    def _mark(px, py, nm, iscap, kind):
        if iscap:
            return (f'<path class="pmark cap" d="{_star(px, py, 5.0)}">'
                    f'<title>{esc(nm)}</title></path>')
        city = kind == "city"
        return (f'<circle class="pmark{"" if city else " open"}" '
                f'cx="{px:.1f}" cy="{py:.1f}" r="{3.4 if city else 3.0}">'
                f'<title>{esc(nm)}</title></circle>')

    for _k, _d, px, py, nm, iscap, kind in order_:
        # A CARTOGRAPHIC TYPE HIERARCHY, FROM DATA THE ATLAS ALREADY HOLDS.
        # Every place used to be the same dot and the same 11px name, which
        # is a database printed on a map. `city_type` is classified for all
        # 319 — capital, city, town, village, island, valley, site, park —
        # and an atlas has always drawn those differently:
        #
        #   capital     a star, and the name in tracked small caps
        #   city        a filled dot
        #   everything  an OUTLINED dot: a place worth going to that is not
        #   else        a city is exactly what this atlas is for, and a ring
        #               is how a printed atlas has always said so
        #
        # Nothing is authored to make this work. It is the classification
        # already in the dataset, drawn.
        marks_.append((px, py, nm, iscap, kind))
        # A REAL BOX OVERLAP, NOT A DISTANCE. The first version dropped a
        # label only if its DOT was within 8% of the frame of another dot,
        # which says nothing about a name 28 characters long: France drew
        # "Sarlat & the Puy-en-Velay" through "Clermont-Ferrand", because the
        # dots were far enough apart and the words were not.
        #
        # Rank 2 — everything that is not a capital or a city — waits for the
        # second pass, so a REGION can take the space instead. A grouping is
        # a level of the hierarchy and only exists if it can win something:
        # placed last, it was drawn on twelve plates of fifty and never on a
        # large country.
        if _k >= 2:
            minor.append((px, py, nm))
            continue
        if _try_label(px, py, nm, "pname" + (" cap" if iscap else "")):
            named_.add(nm)

    # THE COUNTRY'S OWN NAME, MEASURED AND PLACED LIKE EVERY OTHER NAME, which
    # it never was: it used to be composed at the END and prepended to the
    # finished labels, so it landed at the middle of the country's highlight
    # box on top of whatever was already there. 27 of 50 country pages carried
    # an overlap because of it, the worst "ARMENIA" through "THE NORTH & SOUTH"
    # by 125 pixels.
    #
    # AFTER THE CAPITAL AND THE CITIES, NOT BEFORE THEM. Placing it first was
    # the obvious reading of "the largest type wins" and it broke a rule this
    # plate already has: every mark on a country plate carries a name, and the
    # capital's mark is drawn unconditionally. Reserving a large box across
    # the middle of Albania ate Tirana's label and left a star nothing named.
    # The country name is the one label with real freedom — it may sit
    # anywhere inside its own country — so it goes after the names that are
    # pinned to a dot, and takes one of its four positions round the centroid.
    #
    # AND IT IS OFFERED MORE THAN ONE ANCHOR, because it is the only label on
    # the plate that is not pinned to a dot. Four positions round a single
    # centroid left SEVENTEEN OF FIFTY plates with no country name on them,
    # which is a worse defect than the overlap it was fixing: the recognition
    # instrument strips the wordmark and the page title, and a plate that
    # cannot name its own subject fails that test by construction. A country
    # name may sit anywhere inside its own country, so it is tried at the
    # centroid and then at eight points around it, inside the country's own
    # drawn radius.
    # AND THE NAME HAS TO BE ON THE COUNTRY IT NAMES, which this plate never
    # tested. The anchors below are offered inside the subject's own drawn
    # radius, but the only thing they were tested against was the APERTURE
    # and the labels already down — so nine anchors and four positions were
    # enough freedom to leave, exactly as the hero's own comment predicted
    # for the hero. Measured on the shipped pages with the browser's
    # isPointInFill: nine of the forty-three portraits that carry a name
    # printed it entirely off its own country, and AUSTRIA, DENMARK and
    # FRANCE were ten samples out of ten on somebody else's ground — AUSTRIA
    # set across Czechia on the one plate whose whole job is to say which
    # country this page is about.
    #
    # NameGround is the hero's rule at module level, so there is one of it.
    _dsq = [_m.group(1) for _m in re.finditer(
        r'<path[^>]*\sd="([^"]+)"', ctx + land)]
    _here_i = next((_i for _i, _m in enumerate(re.finditer(
        r'<path([^>]*)\sd="[^"]+"', ctx + land))
        if "here" in (_m.group(1) or "")), None)
    _ground = NameGround(_dsq)

    def _cname_fits(x, y, wide, anchor, tol=0, metric="cname"):
        up_, down_ = LABEL_METRICS[metric][2:]
        if not label_fits(x, y, wide, anchor, w, h, up_, down_):
            return False
        if _here_i is None:
            return True
        return _ground.fits(_here_i, *_label_box(x, y, wide, anchor,
                                                 up_, down_), tol=tol)

    _anchors = _ground.anchors(_here_i) if _here_i is not None else []
    if _anchors:
        _up = c["name"].upper()
        # THREE RUNGS, AND THE THIRD IS WHAT KEEPS EVERY PLATE NAMED. Zero
        # crossings first, then two, so the anchors choose the cleanest
        # placement available rather than the first tolerable one — and then
        # five, because a portrait that cannot name its subject is a worse
        # defect than a name whose end overlaps a neighbour. The recognition
        # instrument strips the wordmark and the page title, so the plate is
        # all that is left to say which country this is. On a crowded plate
        # — France and Spain each carry fifteen place labels — every position
        # that satisfies the tighter rule can already be taken: with two
        # rungs FRANCE, NORWAY and SPAIN lost their names outright.
        #
        # Measured on the shipped pages: all forty-three plates that have a
        # polygon keep their name, none is off its own ground, and the three
        # that take the third rung land at exactly four samples of ten. A
        # free rung below this one is never reached, so there is not one.
        _placed_name = False
        for _tol in (0, NameGround.CROSS_OK, 5):
            _placed_name = any(
                _try_label(ax, ay, _up, "cname",
                           metric="cname", off=10.0, prefer="over",
                           fits=lambda *a, _t=_tol: _cname_fits(*a, tol=_t))
                for ax, ay in _anchors)
            if _placed_name:
                break
        # A NAME TOO WIDE FOR ITS OWN COUNTRY GOES ON TWO LINES, which is what
        # a printed atlas does and what this one was doing by accident: BOSNIA
        # AND HERZEGOVINA measures 392 units against a plate 391 wide, and
        # UNITED KINGDOM 253 against 242, so both were being drawn straight
        # off the edge of their own frame and sliced by the aperture. Dropping
        # them instead would be worse — the recognition instrument strips the
        # wordmark, and a plate that cannot name its subject fails by
        # construction — so the name breaks at its last space.
        if not _placed_name and " " in _up:
            _a, _b = _up.rsplit(" ", 1)
            _long = _a if len(_a) >= len(_b) else _b

            def _two(attr, x, y, _nm, _a=_a, _b=_b):
                return (f'<text class="cname"{attr} x="{x:.1f}" y="{y:.1f}">'
                        f'<tspan x="{x:.1f}" dy="{-CNAME_LEAD / 2:.1f}">'
                        f'{esc(_a)}</tspan>'
                        f'<tspan x="{x:.1f}" dy="{CNAME_LEAD:.1f}">'
                        f'{esc(_b)}</tspan></text>')

            for ax, ay in _anchors:
                if _try_label(ax, ay, _long,
                              "cname", metric="cname2", off=10.0,
                              prefer="over", wrap=_two,
                              fits=lambda *a: _cname_fits(
                                  *a, tol=NameGround.CROSS_OK,
                                  metric="cname2")):
                    break
    # THE PLATE NAMES ITS OWN SUBJECT. An atlas plate has the country's name
    # set across it, and there is a second reason here: the recognition test
    # strips the wordmark and the page title, and a plate that names what it
    # draws survives that where a shape alone does not. Tracked, quiet, and
    # UNDER the place names, which are the ones a reader is looking for.
    # REGIONS, IN SPACED UPPERCASE, AT THE MIDDLE OF THEIR OWN DESTINATIONS.
    # We hold which destinations belong to a region and no region geometry,
    # so a region is named where its places are and nowhere else — the same
    # honest device the reference map uses, and the reason there is no
    # boundary round it. Placed after the place names and tested against the
    # same boxes, so a region name never costs a destination its name: a
    # grouping is the thing a reader can most afford to lose.
    # THE MINOR LOCATIONS, THEN THE REGIONS. Placing regions first cost
    # France four place names for two groupings — "THE ALPS & THE EAST" is a
    # third of the plate's width at region size — and a plate that names four
    # fewer real places to name two groupings is a worse plate. A grouping is
    # the thing a reader can most afford to lose, so it takes what is left.
    for px, py, nm in minor:
        if _try_label(px, py, nm, "pname"):
            named_.add(nm)

    # THE HIGHEST NAMED PEAKS IN FRAME, after the destinations. The owner's
    # country-page order is capital, major cities, selected destinations,
    # then major geographic features — and placed BEFORE them the peaks took
    # Zermatt's and Lauterbrunnen's names off Switzerland's own plate, which
    # is a page about the places this atlas writes about. A triangle and a height is how a physical atlas says
    # "mountains here"; it is a measurement somebody else made rather than a
    # surface this atlas fitted, and it is never called relief.
    #
    # DRAWN ONLY WHERE THE NAME FITS, for the same reason every other mark
    # is: a triangle a reader cannot name says "something is here" and
    # nothing else, and this plate's whole rule is that it draws what it can
    # name. Never more than a few either — a plate is not a field of
    # triangles.
    #
    # AND IT MUST BE THIS COUNTRY'S MOUNTAIN. `summit_points` returns the
    # highest peaks IN FRAME, and a country plate frames its neighbours too —
    # so the tallest thing on screen is very often across the border. Measured
    # across the fifty: thirty plates named a summit and most named a foreign
    # one. Austria named Triglav, which is Slovenian, and not Grossglockner;
    # Switzerland named Mont Blanc; Germany named Finsteraarhorn, which is
    # Swiss; Greece named Musala, which is Bulgarian; Croatia named three
    # peaks and not one of them Croatian. A single triangle with a height on
    # a page about one country reads as that country's mountain, which is the
    # class of small lie this repository refuses everywhere else.
    #
    # The test is NameGround's, already built above for the country's own
    # name, and it is point-in-polygon against the drawn geometry rather than
    # an authored list of which peak belongs to whom. Where a country has no
    # named summit in the dataset it names none, which is what twenty plates
    # already do.
    summitmarks = ""
    for px, py, nm, m in cartography.summit_points(proj.xy, (0, 0, w, h)):
        if _here_i is not None and not _ground.own(_here_i, px, py):
            continue
        if _try_label(px, py, f"{nm} {m:,} m", "peakname", off=8.0):
            summitmarks += (f'<path class="peak" d="M{px:.1f} {py - 4.2:.1f}'
                            f'L{px + 4.0:.1f} {py + 2.6:.1f}'
                            f'L{px - 4.0:.1f} {py + 2.6:.1f}Z">'
                            f'<title>{esc(nm)} — {m:,} m</title></path>')

    # PHYSICAL FEATURES AND SEAS, through the same placement rule as every
    # other level and in the owner's order: after the places, before the
    # groupings. ALPS is geography and a region is an editorial grouping;
    # when only one of them fits, the geography wins.
    for px, py, nm in cartography.feature_points(proj.xy, (0, 0, w, h)):
        _try_label(px, py, nm, "fname", metric="rlabel", off=8.0,
                   prefer="over")
    for px, py, nm in cartography.water_points(proj.xy, (0, 0, w, h)):
        _try_label(px, py, nm, "sname", metric="rlabel", off=8.0,
                   prefer="over")
    # And the rivers, last of the physical families for the same reason they
    # are last on a destination plate: everything with a dot outranks them.
    for rnm, ranchors in cartography.river_points(proj.xy, (0, 0, w, h)):
        for rx, ry in ranchors:
            if _try_label(rx, ry, rnm, "rname", off=5.0, prefer="beside"):
                break

    for r_ in c["regions"]:
        pts_r = [proj.xy(t["lat"], t["lon"]) for t in r_["cities"]]
        pts_r = [(x, y) for x, y in pts_r if 0 <= x <= w and 0 <= y <= h]
        if len(pts_r) < 2:
            continue
        _try_label(sum(p[0] for p in pts_r) / len(pts_r),
                   sum(p[1] for p in pts_r) / len(pts_r),
                   # TWO LABEL FAMILIES WORE ONE CLASS NAME, and the
                   # stylesheet held two rules with the IDENTICAL selector.
                   # A river is a line with an italic serif name and a
                   # travel region is an area with a spaced uppercase one —
                   # they are placed by different metrics here and were
                   # painted by whichever rule came last in the file. So the
                   # river treatment was dead on every plate and the region
                   # treatment was on every river, and neither took the
                   # phone compensation the later rule dropped.
                   r_["name"].upper(), "gname", metric="rlabel", off=9.0,
                   prefer="over")

    # A PLATE DRAWS WHAT IT CAN NAME. Every destination used to get a mark,
    # so France carried twenty-eight and eleven of them were dots with no
    # word anywhere near them — "we hold 319 records, therefore 319 dots",
    # which is database visualisation rather than cartography.
    #
    # The rule is not a ranking, because this atlas holds none and refuses to
    # invent one: `rank`, `featured`, `boost` and `sponsored` are refused on
    # every editorial record, in the schema and again at the file level. It
    # is LEGIBILITY. A mark whose name the plate could not fit says only
    # "there is something here", and that is what the reference map further
    # down the page is for — it keeps every dot, every name, every touch
    # target and the scale bar.
    #
    # A capital and a city always draw, named or not: those are the two
    # levels a reader orients by, and a country plate with no capital on it
    # is not a country plate.
    # THE CAPITAL ALWAYS, AND OTHERWISE ONLY WHAT IS NAMED. The first version
    # of this rule also drew every city named or not, which left France with
    # fifteen marks and five words: ten dots saying "something is here" and
    # nothing else, which is the database behaviour the rule was written to
    # remove. A mark the plate cannot name belongs on the reference map,
    # which keeps every dot, every name and every touch target.
    for px, py, nm, iscap, kind in marks_:
        if iscap or nm in named_:
            dotmarks += _mark(px, py, nm, iscap, kind)

    # THE FIFTH DRAWING THAT NAMES THINGS, AND THE ONLY ONE WITH NEITHER
    # PASS. The macro map, the country reference map, the destination plate
    # and pointsmap all run `phone_declutter`, because a phone enlarges a
    # sparse map's labels and enlarging the type breaks the rule that placed
    # it. The portrait was written afterwards and inherited none of it —
    # which is the `.peakname` scar one function over, met again at the level
    # of the PASS rather than of the declaration.
    #
    # Measured with the browser's own getBoundingClientRect on all fifty
    # portraits: zero overlapping pairs at 1280, and at 390 **32 pairs on 18
    # of them**, the worst "Mount Ararat 5,137 m" through "PONTIC MOUNTAINS"
    # by 158 pixels. Not one label was under 9px: size was already right and
    # arrangement was never asked.
    #
    # The set tested is the set a phone DRAWS. `.pname` is display:none below
    # 62rem — the place names are all in the regions band — so measuring
    # against their boxes would drop a summit for colliding with a name that
    # is not there. And the country's own name is first in this list by
    # construction, so it wins every contest: a portrait that cannot name its
    # subject is a worse defect than a collision, which is already why it
    # takes a third placement rung.
    _phone_i = [i for i, b in enumerate(boxed_)
                if b[5].split()[0] != "pname"]
    for i, html in zip(_phone_i, phone_declutter(
            [boxed_[i][:5] + (1.0 if boxed_[i][5].split()[0] == "cname"
                              else PHONE_LABEL_SCALE,) for i in _phone_i],
            frame=(w, h))):
        labs_[i] = html

    namemarks = "".join(labs_)
    uid = "cp" + "".join(ch for ch in c["slug"] if ch.isalnum())[:14]
    # CROPPING IN SILENCE IS THE THING TO AVOID. Where a country has land
    # outside this frame it is said, in the one place a reader of the figure
    # can get at it. Today that is Portugal and nowhere else.
    away = (f". {outside} outlying island{'s' if outside != 1 else ''} "
            f"{'lie' if outside != 1 else 'lies'} outside this frame") if outside else ""
    # A COUNTRY CAN BE CLOSED BY THE DATA RATHER THAN BY ITS OWN BORDER, and
    # one is. data/geo/ is cut at 52°E, so Russia's outline ends on a straight
    # slant that a reader has every reason to read as a frontier. The picture
    # cannot be fixed — the geometry east of the cut is not in this repository
    # — so it is SAID, in the one place a portrait has room to say anything.
    # This is the only page in the atlas that gets a caption under its door.
    euro = geo.load("europe-lod1.json") or {}
    lim = (euro.get("bbox") or [None])[2]
    cut = lim is not None and abs(bbox[2] - lim) < 1e-6
    cutsay = (f". The outline stops at {lim:.0f} degrees east, where this "
              f"atlas's map data ends, not at a border") if cut else ""
    cap = (f'<figcaption>The outline stops at {lim:.0f}°E, where this atlas\'s '
           f'map data ends — not at a border.</figcaption>') if cut else ""
    # THE PLATE IS COMPOSED BY THE RENDERER, NOT HERE. Geography goes in as
    # projected paths and marks; the paint order, the aperture, the rim and
    # the reveal are `cartography.plate`'s, in one place, for every family
    # that will follow. Splitting the marks from the names is not tidiness:
    # they are two layers of the stack and terrain has to be able to land
    # between them.
    return (
        f'<div class="plate">'
        + cartography.plate(
            uid=uid, w=w, h=h, proj=proj, view=(0, 0, w, h),
            cut_reach=dusk_reach(),
            land=land, context=ctx,
            destinations=dotmarks, labels=namemarks,
            summits=summitmarks,
            caption=cap,
            figure_class="minimap portrait arched atlas",
            aria=(f'The outline of {esc(c["name"])}, drawn on this atlas\'s '
                  f'projection{away}{cutsay}'))
        + f'<div class="platefoot">{locator_inset(c["slug"])}'
          f'<ul class="platekey"><li class="k-cap">Capital</li>'
          f'<li class="k-city">City</li>'
          f'<li class="k-dest">Destination</li>'
          f'<li class="k-here">{esc(c["name"])}</li></ul></div></div>'
    )


def country_page(data, c):
    m = next(x for x in data["macros"] if x["slug"] == c["macro_slug"])
    # A TRAVEL REGION'S PICTURE IS WHERE IT IS, and it was a landscape
    # generated from the slug — directly under a plate of the country that
    # draws every one of those regions' destinations as a named mark. The
    # macro pages had the same fault a level up and took the same repair.
    #
    # A region is refused a boundary here, deliberately: we hold which
    # destinations belong to it and not its geometry, so a hull round Bergen
    # and Ålesund labelled Vestland would look like an answer and be a guess.
    # What a region IS, in this dataset, is its set of destinations — which
    # is exactly what the region's own page draws and what /themes draws for
    # FRAMED ON EACH REGION, NOT ON THE COUNTRY. One shared frame was tried
    # first, so the six regions of Norway would be six views of one scale and
    # a reader could see that Fjord Norway is the west and Northern Norway is
    # the top. NORWAY HOLDS SVALBARD AT 78°N. One destination 1,300 km off
    # the mainland blows the shared extent out to the whole canvas, and all
    # six cards drew Europe with two or three dots on it — the identical-
    # picture fault a third time in one commit. A single outlier destroys a
    # shared frame, and this atlas has several: Svalbard, the Azores, the
    # Canaries, Madeira. Each region gets its own.
    region_cards = []
    for r in c["regions"]:
        meta = f'<p class="cardmeta">{n_of(len(r["cities"]), "city")}</p>'
        # AND A REGION WHOSE ONLY DESTINATION IS OFF THE CANVAS GETS NO
        # DRAWING. Svalbard holds Longyearbyen, which projects to y = -48 on
        # a 1000x780 window, so `glyph_view` clamped the frame back onto the
        # canvas and the card drew Scandinavia with no mark on it at all —
        # a picture of somewhere else. A drawing that cannot hold its subject
        # is not a quieter drawing, it is the wrong one.
        rpts = [project(t["lat"], t["lon"]) for t in r["cities"]]
        onframe = [p for p in rpts
                   if 0.0 <= p[0] <= MAP_W and 0.0 <= p[1] <= MAP_H]
        art = constellation(rpts, extra=" regionmini", frame=True,
                            mark=11) if onframe else ""
        region_cards.append(
            card(urls.region(c, r), "Region", r["name"], r["summary"],
                 art=art, meta=meta)
        )
    festivals = "".join(
        f"""<a class="row" href="{urls.month(f['month'])}"><div><h3>{esc(f['name'])}</h3>
        <p class="rowsub">{esc(f.get('where', ''))}</p></div>
        <p class="rowmeta">{esc(EVENT_KIND_NAMES[f['kind']])} · {esc(data['taxonomy']['month_names'][f['month']])}</p></a>"""
        for f in c["festivals"]
    )

    # The specification asks a country page for popular destinations,
    # experiences, journeys and stories. "Popular" is not a thing we can
    # measure — there is no traffic — so it is the destinations we have
    # written most about, and the page says so.
    ranked = sorted(
        ((r, t) for r in c["regions"] for t in r["cities"]),
        key=lambda rt: -(len(rt[1].get("places", [])) * 2 + len(rt[1].get("experiences", []))
                         + len(rt[1]["highlights"])),
    )
    # THE LAST CARD GRID OF ABSTRACT PLATES ON THE SITE, AND IT WAS MEASURED
    # RATHER THAN ARGUED.
    #
    # The plate system's rule here is density — "four cards in a grid of like
    # things is the case a card was designed for", against eleven in a column
    # or forty-three on a page — and six passed it. What nobody had measured
    # is whether the six are six PICTURES. Across all fifty country pages:
    # 207 cards drawing 146 motifs on their own page, so 29% of every card
    # repeats a motif already beside it, and at the bad end FRANCE DRAWS FIVE
    # SKYLINES OUT OF SIX, Belgium four of five, Bosnia and Herzegovina four
    # towers out of four. A grid of six whose job is to tell six places apart,
    # showing one picture five times.
    #
    # And this family has an argument the others did not: the page draws the
    # REAL geography four hundred pixels above, with every region named and
    # its cities on it. A reader who wants to know where Florence is has it.
    # Six abstract gradients under a real map of Italy is two visual
    # languages on one page, and the weaker one is underneath.
    #
    # So rows, which is what /interests, the region pages, /journeys,
    # /themes, /europe-in and the stories index all landed on, for the reason
    # that governs all of them: a card is the right shape for a set of like
    # things chosen on LOOK, and a destination is chosen on where it is and
    # what it is like. Neither of those is a look. It also gives this page
    # one visual language below the map — the experiences, the journeys, the
    # stories and the fixtures under it were already rows.
    popular = "".join(
        f'<a class="row" href="{urls.city(c, r, t)}">'
        f'<div><h3>{esc(t["name"])}</h3>'
        f'<p class="rowsub">{esc(t["summary"])}</p></div>'
        f'<p class="rowmeta">{esc(r["name"])} · '
        f'{n_of(len(t.get("places", [])), "place")} · '
        f'{n_of(len(t.get("experiences", [])), "experience")}</p></a>'
        for r, t in ranked[:6]
    )
    kinds_map = data["taxonomy"]["experience_kinds"]
    # Slice the list, never the HTML: truncating the joined string cut a
    # closing tag in half and produced one malformed page.
    cexp_items = [
        (r, t, e) for r in c["regions"] for t in r["cities"] for e in t.get("experiences", [])
    ][:8]
    cexps = "".join(
        f"""<a class="row" href="{urls.city(c, r, t)}#things-to-do">
        <div><h3>{esc(e['name'])}</h3><p class="rowsub">{esc(e['summary'])}</p></div>
        <p class="rowmeta">{esc(t['name'])} · {esc(kinds_map[e['kind']])}</p></a>"""
        for r, t, e in cexp_items
    )
    seen_j, cjourneys = set(), ""
    seen_s, cstories = set(), ""
    for r in c["regions"]:
        for t in r["cities"]:
            b = data["back"][f"{c['slug']}/{r['slug']}/{t['slug']}"]
            for j in b["journeys"]:
                if j["slug"] in seen_j:
                    continue
                seen_j.add(j["slug"])
                cjourneys += (f"""<a class="row" href="{urls.journey(j)}">
                    <div><h3>{esc(j['name'])}</h3><p class="rowsub">{esc(j['strapline'])}</p></div>
                    <p class="rowmeta">{j['days']} days · via {esc(t['name'])}</p></a>""")
            for st in b["stories"]:
                if st["slug"] in seen_s:
                    continue
                seen_s.add(st["slug"])
                cstories += (f"""<a class="row" href="{urls.story(st)}">
                    <div><h3>{esc(st['title'])}</h3><p class="rowsub">{esc(st['standfirst'])}</p></div>
                    <p class="rowmeta">{esc(st['section'])} · {esc(st['reading'])}</p></a>""")
    know = "".join(f"<li>{esc(k)}</li>" for k in c["know"])
    food = "".join(f"<li>{esc(f)}</li>" for f in c["food"])
    # Derived facts, each carrying the dataset that produced it. Population
    # is a measurement and is therefore never authored — it comes from
    # Natural Earth via scripts/map/process.py, dated, and the page prints
    # the year, because "67 million" with no year is a number that quietly
    # becomes wrong and never announces it.
    d = c.get("derived", {})
    pop = ""
    if d.get("population"):
        yr = f" ({d['population_year']})" if d.get("population_year") else ""
        pop = (f'{d["population"]:,}{yr} <span class="small">— '
               f'{esc(c.get("derived_source", ""))}</span>')
    codes = c["code"].upper() + (f' · {esc(d["iso3"])}' if d.get("iso3") else "")

    facts = factlist([
        ("Capital", esc(c["capital"])),
        ("Currency", esc(c["currency"])),
        ("Languages", esc(", ".join(c["languages"]))),
        ("Population", pop),
        ("ISO codes", codes),
        ("Time zone", esc(c.get("timezone", ""))),
        ("Membership", esc(bloc_line(data, c))),
        ("Typical day", daily_line(data, c)),
        ("Best months", esc(months_line(data, c["season"]["peak"]))),
        ("Quieter months", esc(months_line(data, c["season"].get("shoulder", [])))),
        ("Facts checked", checked_line(c)),
    ])
    # FIFTY PAGES, SEVEN THOUSAND PIXELS EACH, AND NOWHERE TO ACT.
    #
    # Measured across three families: a destination page carries "Save to My
    # Europe" a quarter of the way down and hands the planner its own city
    # (`/plan?from=france/alps-and-east/chamonix`); a journey page opens in
    # the Planner. A COUNTRY PAGE HAD NOTHING — not one button, not one save,
    # and its only planner link was the one in the masthead that every page
    # on the site carries. It is the second-largest family here and the one a
    # reader most often arrives on from a search for "Austria travel", and it
    # ended on `The record`.
    #
    # The brief's sequence is desire, orientation, discovery, planning,
    # action. This page did the first three and stopped.
    #
    # THE LINK CARRIES THE COUNTRY AND NOTHING ELSE. `/plan?ask=` fills the
    # sentence box and runs it, which is how the homepage already hands over,
    # and the planner already understands a bare country name: it confines
    # the route to that country and uses its own defaults for everything
    # else. "A week in Austria" would read better and would be a trip length
    # nobody chose — the same class of invention as a population we
    # estimated. The planner states what it assumed and every field is
    # editable, so what a reader gets is a real route they can argue with.
    #
    # IT IS NOT A NOTE, AND THE CHECK THAT SAYS SO WAS RIGHT. The first
    # version used `.note.onward`, which wears the INTERACTIVE colour and is
    # deliberately rare — 12 pages. Fifty country pages took it to 62 and
    # `c_note_tones` failed with "it has become the default again by the back
    # door", which is exactly what had happened. This is an ACTION, and the
    # Stay layer already composes one: a rule above it, the action on the
    # left, the sentence naming what you are about to deal with on the right,
    # and no border box, radius, shadow or fill. The same grammar, not a
    # second one.
    #
    # AND THE DAYS ARE DERIVED, NOT TYPED. "A week in Austria" reads better
    # and is a trip length nobody chose. The number here is the sum of the
    # shortest stay this atlas records for each of the country's own
    # destinations — 1 night for Monaco, 49 for Greece — which is arithmetic
    # on held data, the same thing the planner itself does.
    #
    # AND A ROUTE NEEDS TWO PLACES. Monaco, San Marino and Vatican City hold
    # one destination each, and the advisory countries are stripped from the
    # planner index entirely, so for them the planner answers "we could not
    # build a journey we would stand behind" — honestly, and after a click
    # that promised one. No link there: a link to a refusal is worse than no
    # link, and the rule is the route's, not a threshold somebody picked.
    c_dests = [n["city"] for n in data["cities"].values()
               if n["country"]["slug"] == c["slug"]]
    plan_nights = sum(d["nights"][0] for d in c_dests)
    plan_handoff = ""
    if len(c_dests) > 1 and not c.get("advisory"):
        _ask = f"{plan_nights} days in {c['name']}"
        plan_handoff = (
            '<div class="handoff">'
            '<div class="handoff-do">'
            f'<p><a class="btn" href="/plan?ask={quote(_ask)}">Build a route '
            f'through {esc(c["name"])}</a></p></div>'
            '<div class="handoff-say">'
            f'<p>The Journey Planner holds all {len(c_dests)} of these '
            f'destinations and the real distances between them. It opens on '
            f'{plan_nights} days, which is the shortest stay this atlas records '
            f'for each of them added up — change the length, the month, the '
            f'budget or the pace and build it again.</p>'
            '</div></div>'
        )
    # THE COUNTRY BAND, AND IT IS AN ADDITION RATHER THAN A REPLACEMENT.
    #
    # Fifty country pages were the largest family on this site with no
    # photograph anywhere — seven thousand pixels each, and the page a reader
    # most often arrives on from a search for "Austria travel". The brief
    # that named it calls this the country SIGNATURE: what a whole country
    # feels like, above its name.
    #
    # What it must not do is take the portrait's place. The country plate is
    # this family's signature moment and it is the thing that says which
    # country the page is about; a photograph replacing it would be the /map
    # failure, where a page went on stating a claim about a drawing that was
    # no longer there. So the band sits ABOVE the head and the portrait stays
    # exactly where it is.
    #
    # AND WITH NO PHOTOGRAPH THERE IS NO BAND AT ALL — not an empty frame,
    # not a plate. `picture()` returns a generated plate when the register
    # has no row, which is right on a card and wrong here for the reason the
    # homepage already records: a slot waiting for a picture is honest and
    # three hundred pixels of one is a hole. So this asks the register
    # directly, exactly as the hero does.
    # THE OPENING SPREAD. The portrait already sat beside the name, so a
    # photograph takes its place in the head and the portrait moves to a band
    # of its own with the caption that explains it. A country with no
    # photograph is exactly the page it was.
    ckey = f"country:{c['slug']}"
    cportrait = countryportrait(data, c)
    cpic = head_figure(data, ckey, cportrait, alt_fallback=c["name"])
    cbelow = moved_drawing(
        data, ckey, cportrait,
        f"{esc(c['name'])} drawn from Natural Earth, with its capital and the "
        f"destinations this atlas holds in it.")
    # THE COUNTRY'S OWN DESTINATIONS, AS A SEQUENCE RATHER THAN A GRID.
    # A country page's second question is "what is in it", and the answer it
    # had was a grid of region cards four hundred pixels below a map. The
    # strip is that answer as pictures, in the order the atlas writes them,
    # and it is built from `destination-hero@<target>` — a slot this product
    # already declares 319 times. Nothing new is invented; it renders when
    # the register holds one and is absent when it does not.
    cstrip_items = []
    for _r in c["regions"]:
        for _t in _r["cities"]:
            cstrip_items.append({
                "key": f"city:{c['slug']}/{_r['slug']}/{_t['slug']}",
                "alt": _t["name"],
                "label": _t["name"],
                "href": urls.city(c, _r, _t)})
    # THE ATLAS INDEX, WHICH IS THE ONE THING THAT BELONGS BESIDE THE PROSE.
    # The portrait band was a 34rem measure inside a 90rem stage, so half of
    # it was empty page — the void this system exists to remove, arriving
    # from the section that is most purely text. What goes there is not an
    # illustration and not a pull quote: it is what an atlas prints in the
    # margin, set in the mono face, derived and checkable. Absent fields are
    # ABSENT rather than estimated, which is this product's data rule.
    _facts = [("Capital", c.get("capital") or ""),
              ("Travel regions", str(len(c["regions"]))),
              ("Destinations", str(sum(len(r["cities"]) for r in c["regions"]))),
              ("Places recorded", str(sum(len(t.get("places", []))
                                          for r in c["regions"] for t in r["cities"]))),
              ("Region of Europe", m["name"])]
    _gf = (geo.facts() or {}).get(c["slug"]) if hasattr(geo, "facts") else None
    if _gf and _gf.get("iso3"):
        _facts.append(("ISO 3166", _gf["iso3"]))
    if _gf and _gf.get("population"):
        _facts.append(("Population", f"{_gf['population']:,}"))
    cindex = ('<dl class="ed-index">'
              + "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>"
                        for k, v in _facts if v)
              + "</dl>")
    _shots = ed_strip(data.get("images"), cstrip_items, limit=8)
    cstrip = (f'<section class="ed-section">'
              + ed_section_head("In the country",
                                f"Where {c['name']} is worth going",
                                f"{n_of(sum(len(r['cities']) for r in c['regions']), 'destination')} "
                                f"across {n_of(len(c['regions']), 'travel region')}.")
              + _shots + "</section>") if _shots else ""
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], urls.macro(m)), (c["name"], None)])}
{ed_opening(
    eyebrow=f"Country · {m['name']}",
    title=c["name"],
    intro=c["tagline"],
    visual=cpic or cportrait,
    family="atlas")}
<div class="headmeta ed-section">
  <p class="orient">{country_orient(c)}</p>
  {chips(c["interests"], data["interests"])}
</div>
{cbelow}
{advisory_note(c)}

<section class="ed-section">
{ed_section_head("The portrait",
                 f"Why {c['name']} belongs in your Europe.")}
<div class="ed-split">
  <div class="ed-split-copy measure lead">
    <p>{esc(c['summary'])}</p>
  </div>
  <div class="ed-split-media">{cindex}</div>
</div>
{ed_bleed(data.get("images"), f"country:{c['slug']}",
          alt=f"{c['name']} seen whole",
          caption=f"{c['name']}", shape="tall")}
</section>

{cstrip}

<section class="practical" aria-label="Practical">
  <div>
    <h2 id="getting-around" class="mini">Getting around</h2>
    <p>{esc(c['getting_around'])}</p>
  </div>
  <div>
    <h2 id="when" class="mini">When to come</h2>
    <p>{esc(c['season']['note'])}</p>
  </div>
  <div>
    <h2 class="mini">Worth knowing</h2>
    <ul>{know}</ul>
  </div>
  <div>
    <h2 class="mini">At the table</h2>
    <ul>{food}</ul>
  </div>
</section>

{constel_defs()}
{section("Travel regions", countrymap(data, c) + grid(region_cards, 3), id="regions",
         lede=f"{len(c['regions'])} editorial regions, each opening onto its cities.")}

{section("Popular destinations", f'<div class="rows">{popular}</div>',
         lede="The destinations we have written most about, which is not the same as the ones most people go to — and is the only ranking we can honestly compute.",
         more=("Every region", "#regions")) if popular else ""}

{section("Experiences here", f'<div class="rows">{cexps}</div>', opens=True,
         lede=f"A sample of what is listed across {c['name']}.",
         more=("Every experience category", "/experiences")) if cexps else ""}

{section("Journeys through " + c["name"], f'<div class="rows">{cjourneys}</div>') if cjourneys else ""}

{plan_handoff}

{section("Stories set here", f'<div class="rows">{cstories}</div>') if cstories else ""}

{section("Fixed points in the year", f'<div class="rows">{festivals}</div>',
         more=("The whole European year", "/events")) if festivals else ""}

{section("The record", facts + scorebars(country_scores(c), _spread("country", data)) + provenance_block(c),
         tone="quiet",
         lede="What we hold about " + c["name"] + ", where each figure came "
              "from, and when it was last checked. The score says what this "
              "country is for, not how good it is — it is useful once you are "
              "already interested and is not a reason to be.")}
{ad_slot(urls.country(c))}
"""
    return f"/europe/{c['slug']}/index.html", page(
        c["name"], body, path=urls.country(c), area="countries",
        description=c["summary"][:180],
        og=("country:" + c["slug"], motif_for(c["interests"]),
            f"{c['name']} — {c['tagline']}"),
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Countries", "/countries"),
                           (m["name"], urls.macro(m)), (c["name"], urls.country(c))]),
            ld_place("Country", name=c["name"], url=urls.country(c),
                     description=c["summary"],
                     extra={"alternateName": c.get("official") or c["name"],
                            "currency": c["currency"].split(" — ")[0],
                            "containedInPlace": ld_within("Place", "Europe", "/discover")}),
        ],
    )


def region_page(data, c, r):
    m = next(x for x in data["macros"] if x["slug"] == c["macro_slug"])
    # The specification asks a region page for geography, culture, cities,
    # attractions, food, experiences, events, accommodation and journeys.
    # Everything we hold at this level is aggregated here rather than left
    # for the reader to assemble by clicking through every destination.
    kinds_map = data["taxonomy"]["experience_kinds"]
    rplaces = [(t, pl) for t in r["cities"] for pl in t.get("places", [])]
    rexps = [(t, e) for t in r["cities"] for e in t.get("experiences", [])]
    placerows = "".join(
        f"""<a class="row" href="{urls.place(c, r, t, pl)}">
        <div><h3>{esc(pl['name'])}</h3><p class="rowsub">{esc(pl['summary'])}</p></div>
        <p class="rowmeta">{esc(t['name'])} · {esc(PLACE_KIND_NAMES[pl['kind']])}</p></a>"""
        for t, pl in rplaces
    )
    exprows = "".join(
        f"""<a class="row" href="{urls.city(c, r, t)}#things-to-do">
        <div><h3>{esc(e['name'])}</h3><p class="rowsub">{esc(e['summary'])}</p></div>
        <p class="rowmeta">{esc(t['name'])} · {esc(kinds_map[e['kind']])}</p></a>"""
        for t, e in rexps
    )
    seen, jrows = set(), ""
    for t in r["cities"]:
        for j in data["back"][f"{c['slug']}/{r['slug']}/{t['slug']}"]["journeys"]:
            if j["slug"] in seen:
                continue
            seen.add(j["slug"])
            jrows += (f"""<a class="row" href="{urls.journey(j)}">
                <div><h3>{esc(j['name'])}</h3><p class="rowsub">{esc(j['strapline'])}</p></div>
                <p class="rowmeta">{j['days']} days · via {esc(t['name'])}</p></a>""")
    # Named apart from `nights`, which the card loop below reuses for a
    # per-destination range — the collision made this a list at render time.
    pass_nights = sum(sum(t["nights"]) / 2 for t in r["cities"])
    # A THREE-COLUMN CARD GRID HOLDING ONE CARD, ON A QUARTER OF THE REGIONS.
    #
    # 97 of the 130 travel regions hold one or two destinations — 26 hold
    # exactly one — so the band that IS the subject of the page opened with a
    # single 280px tile and two empty columns beside it. That is the stories
    # index failure exactly: a card alone in a 1,168px row, with the shape of
    # the data deciding the layout and the layout unable to say so.
    #
    # And the tile's picture was a plate drawn from the destination's own
    # hash, one or two per page over 130 pages, directly under a real map of
    # the region that shows where those same places are. The measurement that
    # emptied the homepage, /journeys, /europe-in, the stories index and the
    # seventeen interest pages applies here for the same reason: a
    # destination is chosen on where it is and what it is like, and neither
    # of those is a LOOK, which is the test a card has to pass.
    #
    # Rows, which is what the rest of this page already is — places, things
    # to do and journeys are all rows — so the region page stops speaking two
    # list languages one band apart.
    #
    # NOT the country in the meta. Every destination on a region page is in
    # the same country, so a kicker reading NORWAY eight times down the list
    # is the boilerplate the "never explain the constraint back" rule forbids:
    # the shared reason is hoisted into the breadcrumb and the h1, and each
    # row carries only what distinguishes it. What kind of place it is does.
    destrows = "".join(
        f'<a class="row" href="{urls.city(c, r, t)}">'
        f'<div><h3>{esc(t["name"])}</h3>'
        f'<p class="rowsub">{esc(t["summary"])}</p></div>'
        f'<p class="rowmeta">'
        f'{esc(CITY_TYPE_NAMES.get(t.get("city_type"), "Destination"))}<br>'
        f'<span class="small">{nights_line(t)}</span></p></a>'
        for t in r["cities"])
    photoband = pageband(data, f"region:{c['slug']}/{r['slug']}")
    # A REGION IS ITS DESTINATIONS AND THE PAGE LISTED THEM AS SENTENCES.
    #
    # `docs/data-model.md`'s own line is that a region is a GROUPING and not
    # a boundary — we hold which destinations belong to it and no geometry —
    # so the map above draws the region as its own destinations with the name
    # at the middle of them. That is the honest drawing and it is a small one,
    # and under it the page was a lede, a chip row and four lists. On the
    # contact sheet this family and the place page were the two cells that
    # read as grey text.
    #
    # The strip is the same set the map plots and the rows below carry, in
    # the same order. Nothing is chosen: a region holds two to eight
    # destinations and the strip takes all of them.
    _rstrip = ed_strip(data.get("images"), [
        {"key": f"city:{c['slug']}/{r['slug']}/{t['slug']}",
         "alt": t["name"], "label": t["name"], "href": urls.city(c, r, t)}
        for t in r["cities"]], limit=8)
    if _rstrip:
        _rstrip = ('<section class="ed-section">'
                   + ed_section_head("In the region",
                                     f"What {r['name']} is made of",
                                     # A COUNT CANNOT BE DROPPED INTO A
                                     # SENTENCE THAT ASSUMES A PLURAL. A
                                     # region holds one to eight
                                     # destinations, and Tyrol & the West
                                     # holds one, so the first version read
                                     # "1 destination, the same ones the
                                     # drawing above plots" — the tag-name
                                     # agreement failure two families over,
                                     # made again by the commit that
                                     # recorded it.
                                     ("The one destination the drawing above "
                                      "plots." if len(r["cities"]) == 1 else
                                      f"All {numword(len(r['cities']))} of them, "
                                      f"the same set the drawing above plots."))
                   + _rstrip + "</section>")
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], urls.macro(m)),
         (c["name"], urls.country(c)), (r["name"], None)])}
{photoband}
{ed_opening(
    eyebrow=f"Travel region · {c['name']}",
    title=r["name"],
    intro=r["summary"],
    visual=regionmap(data, c, r),
    family="atlas")}
<div class="headmeta ed-section">
  <p class="orient">{n_of(len(r["cities"]), "destination")} ·
  {len(rplaces)} place{"s" if len(rplaces) != 1 else ""} recorded ·
  about {n_of(int(pass_nights), "night")} to see it all</p>
  {chips(r["interests"], data["interests"])}
</div>
{_rstrip}
{section("Destinations", f'<div class="rows">{destrows}</div>')}
{section("Places to see", f'<div class="rows">{placerows}</div>',
         lede=f"Everything recorded across {r['name']}, in one list.") if placerows else ""}
{section("Things to do", f'<div class="rows">{exprows}</div>') if exprows else ""}
{section("Journeys through " + r["name"], f'<div class="rows">{jrows}</div>') if jrows else ""}
{section("Accommodation & restaurants", STAY_NOTE)}
{section("The record", factlist([
      ("Destinations", str(len(r["cities"]))),
      ("Places recorded", str(len(rplaces))),
      ("Experiences", str(len(rexps))),
      ("A full pass", f"about {n_of(int(pass_nights), 'night')}"),
      ("Best months", esc(months_line(data, c["season"]["peak"]))),
      ("Typical day", daily_line(data, c)),
  ]), tone="quiet",
  lede="What this atlas holds about " + r["name"] + ". The counts are "
       "derived from the region's own destinations and move when it does; "
       "the seasons and the daily cost belong to " + esc(c["name"]) + " and "
       "are repeated here rather than looked up.")}
<div class="note">
  <h2 class="mini">Food, events and practicalities are on the country page</h2>
  <p>They belong to {esc(c['name'])} rather than to {esc(r['name'])}, and repeating them on
  every region page is how two copies of a fact start disagreeing.
  <a href="{urls.country(c)}">{esc(c['name'])} →</a></p>
</div>
{ad_slot(urls.region(c, r))}
"""
    # AND THE FOURTH: Vatican City is a travel region holding a destination
    # called Vatican City, in a country called Vatican City — so the region
    # page and the destination page both composed "Vatican City, Vatican
    # City". A region is a grouping and a destination is a place, and the
    # title is where that has to be legible when the two sit next to each
    # other in a search result.
    return f"/europe/{c['slug']}/{r['slug']}/index.html", page(
        f"{r['name']}, a travel region in {c['name']}", body,
        path=urls.region(c, r), area="countries",
        accent="territory",
        description=r["summary"][:180],
        og=(f"region:{c['slug']}:{r['slug']}", motif_for(r["interests"]),
            f"{r['name']}, {c['name']}"),
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Countries", "/countries"),
                           (m["name"], urls.macro(m)), (c["name"], urls.country(c)),
                           (r["name"], urls.region(c, r))]),
            ld_place("TouristDestination", name=r["name"], url=urls.region(c, r),
                     description=r["summary"],
                     within=ld_within("Country", c["name"], urls.country(c)),
                     extra={"touristType": [data["interests"][i]["name"]
                                            for i in r["interests"]
                                            if i in data["interests"]],
                            "includesAttraction": [
                                ld_within("TouristDestination", t["name"],
                                          urls.city(c, r, t))
                                for t in r["cities"][:12]]}),
        ],
    )


CITY_TYPE_NAMES = {
    "capital": "Capital city", "city": "City", "town": "Town",
    "village": "Village", "island": "Island", "valley": "Valley",
    "park": "National park", "site": "Historic site",
}


def pop_line(t):
    """A destination's population, or nothing at all.

    Natural Earth lists 157 of our 319 destinations. The other 162 are
    villages, valleys and monuments — Theth, Xınalıq, Madriu-Perafita-Claror —
    and their absence is not a coverage failure, it is the product. So the
    row simply does not appear rather than saying "unknown", which would read
    as a defect in the record rather than as the size of the place.

    It never becomes a score. A population is the most tempting proxy for
    crowding there is, and discoverability is explicitly not a crowd
    measurement; checks.py asserts that no scoring code reads this field.
    """
    d = t.get("derived", {})
    if not d.get("population"):
        return ""
    return (f'{d["population"]:,} <span class="small">— '
            f'{esc(t.get("derived_source", ""))}</span>')


def city_page(data, c, r, t):
    m = next(x for x in data["macros"] if x["slug"] == c["macro_slug"])
    cid = f"{c['slug']}/{r['slug']}/{t['slug']}"
    highlights = "".join(f"<li>{esc(h)}</li>" for h in t["highlights"])
    # The three or four highlights are the ONLY universal editorial asset a
    # destination has: every one of the 319 carries three or four, while 194
    # of them carry no places at all and 98 carry neither places nor
    # experiences. So the page is built on what is always there. They used to
    # sit below a section nav, a map and a metadata table, inside the left
    # column of a split, under the heading "Why visit" — the best writing on
    # the page, four scrolls down and set at body size.
    reasons = "".join(
        f'<li><span class="rn" aria-hidden="true">{i + 1:02d}</span>'
        f'<span class="rt">{esc(h)}</span></li>'
        for i, h in enumerate(t["highlights"])
    )
    kinds = data["taxonomy"]["experience_kinds"]
    # The §2.5 edge in the other direction: an experience says which place it
    # is tied to, and how. Each row carries an id so a place page can link
    # straight to it — an experience is a row on its destination rather than a
    # page of its own, because 197 thin pages is not a product and "everything
    # there is to do in Bergen, in one place" is.
    _pl_by_slug = {pl["slug"]: pl for pl in t.get("places", [])}
    _HOW = {"at": "at", "from": "starting at", "about": "about"}

    def _where(e):
        links = [
            f'{_HOW[l["how"]]} <a href="{urls.place(c, r, t, _pl_by_slug[l["place"]])}">'
            f'{esc(_pl_by_slug[l["place"]]["name"])}</a>'
            for l in e.get("at", []) if l["place"] in _pl_by_slug
        ]
        return f'<p class="rowsub small">— {", ".join(links)}</p>' if links else ""

    # §2.16 saved_experiences. My Europe already saved destinations, places,
    # journeys, themes and stories; an experience was the one kind of thing
    # you could read about and not keep, which is a strange omission on a
    # page whose whole job is "things to do here". It became possible once
    # each row had a stable id to point at.
    exps = "".join(
        f"""<div class="row" id="exp-{esc(e['slug'])}"><div><h3>{esc(e['name'])}</h3>
        <p class="rowsub">{esc(e['summary'])}</p>{_where(e)}</div>
        <div class="rowside"><p class="rowmeta">{esc(kinds[e['kind']])} · {esc(e['band'])}</p>
        <button class="btn ghost tiny" type="button"
          data-save="experience:{esc(cid)}#{esc(e['slug'])}" data-kind="Experience"
          data-label="{esc(e['name'])}, {esc(t['name'])}"
          data-url="{esc(urls.experience(c, r, t, e))}">Save</button></div></div>"""
        for e in t.get("experiences", [])
    )
    # Nearby cities, computed rather than curated: the same distance function
    # the planner uses, so the two never disagree about what is close.
    others = [n for n in data["cities"].values() if n["city"] is not t]
    near = sorted(others, key=lambda n: haversine(t, n["city"]))[:6]
    nearrows = "".join(
        f"""<a class="row" href="{urls.city(n['country'], n['region'], n['city'])}">
        <div><h3>{esc(n['city']['name'])}</h3><p class="rowsub">{esc(n['country']['name'])} · {esc(n['region']['name'])}</p></div>
        <p class="rowmeta">{esc(hop_note(haversine(t, n['city'])))} away</p></a>"""
        for n in near
    )
    # What the page names, the map may link. See minimap(): six of Innsbruck's
    # twelve dots led to places that appeared nowhere else in the document.
    nearnamed = {urls.city(n["country"], n["region"], n["city"]) for n in near}

    stay = nights_line(t)
    # "Stay & eat" while that section is the honest refusal of both; "Stay"
    # once a destination carries a real accommodation context, because the
    # section then makes no promise at all about eating. Computed here and
    # not inside the nav call: that call sits inside an f-string, and a
    # comment cannot live in an f-string expression — which is how the first
    # version of this line failed the build.
    staytab = "Stay" if staylib.context(cid) else "Stay & eat"

    # Everything that points at this city. These are the graph edges: a
    # journey that stops here, a theme that names it, a story set in it.
    b = data["back"][cid]
    edge_rows = []
    for j in b["journeys"]:
        leg = next(l for l in j["legs"] if l["city"] == cid)
        edge_rows.append(
            f"""<a class="row" href="{urls.journey(j)}">
            <div><h3>{esc(j['name'])}</h3><p class="rowsub">{esc(leg['why'])}</p></div>
            <p class="rowmeta">Journey · {n_of(leg['nights'], 'night')} here</p></a>"""
        )
    for th in b["themes"]:
        stop = next(x for x in th["stops"] if x["city"] == cid)
        edge_rows.append(
            f"""<a class="row" href="/themes/{esc(th['slug'])}">
            <div><h3>{esc(th['name'])}</h3><p class="rowsub">{esc(stop['why'])}</p></div>
            <p class="rowmeta">Theme</p></a>"""
        )
    for st in b["stories"]:
        edge_rows.append(
            f"""<a class="row" href="/stories/{esc(st['slug'])}">
            <div><h3>{esc(st['title'])}</h3><p class="rowsub">{esc(st['standfirst'])}</p></div>
            <p class="rowmeta">Story · {esc(st['reading'])}</p></a>"""
        )
    edges = section(
        "This place, in the rest of the site", f'<div class="rows">{"".join(edge_rows)}</div>',
        lede="Every journey that stops here, every theme that names it and every story set in it.",
    ) if edge_rows else ""

    # When to come and how to arrive are country-level facts, and repeating
    # them on 244 city pages would be a maintenance trap. They are summarised
    # here and linked to the one place they are written.
    fkeys = facets_for(data, c, r, t)
    facetlinks = ("<h3>More on " + esc(t["name"]) + "</h3><p>" + " · ".join(
        f'<a href="{urls.facet(c, r, t, k)}">{esc(urls.FACETS[k])}</a>' for k in fkeys
    ) + "</p>") if fkeys else ""
    placerows = "".join(
        f"""<a class="row" href="{urls.place(c, r, t, pl)}">
        <div><h3>{esc(pl['name'])}</h3><p class="rowsub">{esc(pl['summary'])}</p></div>
        <p class="rowmeta">{esc(PLACE_KIND_NAMES[pl['kind']])} · {esc(pl['duration'])}</p></a>"""
        for pl in t.get("places", [])
    )
    # §2.11: the nodes, never the routes. What a destination page has to
    # answer is "how do I get near here", and an airport is at a fixed place
    # that a public-domain dataset knows. A timetable is not.
    NODE_NAMES = {"airport": "Airport", "port": "Port"}
    transrows = "".join(
        f"""<div class="row"><div><h3>{esc(nd['name'])}</h3>
        <p class="rowsub">{esc(NODE_NAMES[nd['kind']])}"""
        f"""{f" · {esc(nd['iata'])}" if nd.get('iata') else ""}</p></div>
        <p class="rowmeta">{nd['km']} km in a straight line</p></div>"""
        for nd in t.get("transport", [])
    )

    # Events, now that §2.9 gives one an edge into the graph.
    #
    # This used to print every festival in the country on every destination
    # page in it, so Carnevale appeared on all 25 Italian city pages
    # including the ones 700 km from Venice. It read as a fact about the
    # place and was a fact about the country. With `city` on an event, the
    # ones tied here come first and the ones tied *elsewhere* are dropped —
    # only the genuinely nationwide ones stay, under a heading that says so.
    here_f = [f for f in c["festivals"] if f.get("city") == t["slug"]]
    wide_f = [f for f in c["festivals"] if not f.get("city")]

    def _festrows(items):
        return "".join(
            f"""<div class="row"><div><h3>{esc(f['name'])}</h3>
            <p class="rowsub">{esc(f.get('where', ''))}</p></div>
            <p class="rowmeta">{esc(data['taxonomy']['month_names'][f['month']])}</p></div>"""
            for f in items
        )
    festrows = _festrows(here_f)
    widerows = _festrows(wide_f)
    # A VISUAL EARNS ITS POSITION OR IT IS NOT PLACED.
    #
    # The placeband used to be [generated plate | map] on all 319 pages. It
    # was rendered both ways and looked at: the plate at 480x310 is flat, and
    # the map beside it was squeezed to half width with its labels cramped.
    # The map ALONE, full width, is the stronger page — Chamonix with Annecy,
    # Zermatt, Lauterbrunnen and Lugano around it, legible, and true.
    #
    # So the illustration goes, and the rule is the same one the homepage
    # hero follows: a photograph if the register holds one, and where it does
    # not, no illustration in its place. The plates keep every other job they
    # have — the social card for this page is still drawn from plate_shapes.
    has_photo = bool((data.get("images") or {}).get(f"city:{cid}"))
    photo_block = (f'<div class="placeband-art">'
                   + picture(data["images"], f"city:{cid}", w=1260, h=540,
                             alt=f"{t['name']}, {c['name']}", eager=True,
                             sizes="(min-width: 76rem) 44rem, 100vw")
                   + '</div>') if has_photo else ""

    # THE PLACE IS THE PICTURE AND ITS PLACES ARE THE SEQUENCE.
    # A destination page had one map and a column of rows; the directive is
    # right that this is the family that should be most heavily image-led.
    # Both of these are built from slots this product already declares —
    # `city:<target>` for the wide turn and `place:<target>` for each
    # thing in it — and both are absent until the register holds them, so
    # the page composes rather than filling a hole.
    tkey = f"city:{c['slug']}/{r['slug']}/{t['slug']}"
    tbleed = ed_bleed(data.get("images"), tkey, alt=t["name"],
                      caption=f"{t['name']}, {c['name']}", shape="tall")
    tstrip_items = [{
        "key": f"place:{c['slug']}/{r['slug']}/{t['slug']}/{pl['slug']}",
        "alt": pl["name"], "label": pl["name"],
        "href": urls.place(c, r, t, pl)} for pl in t.get("places", [])]
    _tshots = ed_strip(data.get("images"), tstrip_items, limit=8)
    tstrip = (f'<section class="ed-section">'
              + ed_section_head("In the place",
                                f"What {t['name']} is made of",
                                f"{n_of(len(t.get('places', [])), 'place')} recorded here.")
              + _tshots + "</section>") if _tshots else ""
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], urls.macro(m)),
         (c["name"], urls.country(c)), (r["name"], urls.region(c, r)), (t["name"], None)])}
<section class="ed-arrival">
  <div class="ed-arrival-media{'' if has_photo else ' maponly'}">
    {photo_block}
    <div class="placeband-map">{minimap(data, t, span="auto", named=nearnamed)}</div>
  </div>
  <div class="ed-arrival-copy">
    <p class="ed-eyebrow">Arrival · {esc(c['name'])}</p>
    <h1>{esc(t['name'])}</h1>
    <p>{esc(t['summary'])}</p>
    <p class="ed-arrival-where">{esc(r['name'])} — <span class="mono">{coord_line(t)}</span></p>
  </div>
</section>
<section class="ed-section" aria-labelledby="why-visit">
{ed_section_head("Understand", "Why go", hid="why-visit")}
<ol class="reasons">{reasons}</ol>
<div class="headmeta">
  <p class="orient">{orient_line(t)}</p>
  {chips(t["interests"], data["interests"])}
</div>
</section>
{tbleed}
{tstrip}
{sectionnav([
    ("Overview", "why-visit"),
    ("Places", "places" if placerows else ""),
    ("Things to do", "things-to-do" if exps else ""),
    ("Getting near", "getting-near" if transrows else ""),
    ("Events", "events" if (festrows or widerows) else ""),
    ("Travel tips", "tips"),
    (staytab, "stay"),
    ("Onward", "onward"),
])}
<section class="practical" aria-label="Practical">
  <div>
    <h2 class="mini">Give it {esc(stay)}</h2>
    <p>Enough to see the list below without spending the trip on trains. The Journey
    Planner uses exactly this range when it builds an itinerary.</p>
  </div>
  <div>
    <h2 class="mini">When to come</h2>
    <p>Best: {esc(months_line(data, c["season"]["peak"]))}. Quieter:
    {esc(months_line(data, c["season"].get("shoulder", [])) or "—")}.
    <a href="{urls.country(c)}#when">Why, and what that means →</a></p>
  </div>
  <div>
    <h2 class="mini">Getting there</h2>
    <p>{esc(first_sentence(c['getting_around']))}
    <a href="{urls.country(c)}#getting-around">All of {esc(c['name'])} →</a></p>
  </div>
</section>

<div class="split mt7">
  <div>
    {section("Places to see", f'<div class="rows">{placerows}</div>'
             + f'<p class="sourcenote">{len(t.get("places", []))} recorded so far. We hold what each one is and how long to give it, and deliberately not its opening hours or price.</p>',
             id="places") if placerows else ""}
    {section("Things to do", f'<div class="rows">{exps}</div>', id="things-to-do") if exps else ""}
    {section("Getting near", f'<div class="rows">{transrows}</div>'
             + '<p class="sourcenote">Airports and ports within reach, from Natural Earth — '
               'public domain, hosted by us. The distance is a straight line, which is the only '
               'thing a coordinate can honestly tell you: 43 km across the Accursed Mountains is '
               'four hours, and we hold no timetables, operators or fares.</p>',
             id="getting-near", opens=True) if transrows else ""}
    {section("Events here", f'<div class="rows">{festrows}</div>', id="events",
             lede=f"Fixtures tied to {t['name']} itself.") if festrows else ""}
    {section(f"Elsewhere in {c['name']}" if festrows else "Events",
             f'<div class="rows">{widerows}</div>',
             id="" if festrows else "events",
             lede=f"Nationwide fixtures, not tied to one destination. "
                  f"The whole European year is on /events.") if widerows else ""}
  </div>
  <aside class="rail">
    <h2 class="mini">Take it further</h2>
    <p><a href="/plan?from={esc(c['slug'])}%2F{esc(r['slug'])}%2F{esc(t['slug'])}">Start a journey here →</a></p>
    {facetlinks}
    <p><button class="btn ghost" type="button" data-save="city:{esc(cid)}" data-kind="Place" data-label="{esc(t['name'])}, {esc(c['name'])}" data-url="{urls.city(c, r, t)}">Save to My Europe</button></p>
  </aside>
</div>
{section("Travel tips", '<ul class="stack">' + "".join(f"<li>{esc(k)}</li>" for k in c["know"]) + "</ul>",
         id="tips", opens=True,
         lede=f"Practical things about {c['name']} that are not obvious from outside it.")}

{stay_section(data, c, r, t, cid)}

{section("Nearest onward stops", f'<div class="rows">{nearrows}</div>',
         id="onward",
         lede="Straight-line distance, and what that usually means in practice.")}

{section("The record", factlist([
    ("Kind of place", esc(CITY_TYPE_NAMES.get(t.get("city_type"), ""))),
    ("Population", pop_line(t)),
    ("Region", f'<a href="{urls.region(c, r)}">{esc(r["name"])}</a>'),
    ("Coordinates", f'<span class="mono">{coord_line(t)}</span>'),
]) + scorebars(city_scores(c, r, t), _spread("city", data)), id="record", tone="quiet",
   lede="What we hold about this place, and what our own tagging makes of it. "
        "It is the last thing on the page on purpose: it is useful when you are "
        "already interested, and it is not a reason to be.")}
{edges}
{stickycta(data, c, r, t)}
{ad_slot(urls.city(c, r, t))}
"""
    return f"/europe/{c['slug']}/{r['slug']}/{t['slug']}/index.html", page(
        f"{t['name']}, {c['name']}", body, path=urls.city(c, r, t), area="countries",
        accent="human",
        description=t["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
        og=(f"city:{c['slug']}:{t['slug']}",
            motif_for(t["interests"], t.get("city_type")) or motif_for(r["interests"]),
            f"{t['name']}, {c['name']} — {t['summary'][:90]}"),
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Countries", "/countries"),
                           (m["name"], urls.macro(m)), (c["name"], urls.country(c)),
                           (r["name"], urls.region(c, r)), (t["name"], urls.city(c, r, t))]),
            ld_place("TouristDestination", name=t["name"], url=urls.city(c, r, t),
                     description=t["summary"], lat=t["lat"], lon=t["lon"],
                     within=ld_within("TouristDestination", r["name"], urls.region(c, r)),
                     extra={"touristType": [data["interests"][i]["name"]
                                            for i in t["interests"]
                                            if i in data["interests"]],
                            "includesAttraction": [
                                ld_within("TouristAttraction", pl["name"],
                                          urls.place(c, r, t, pl))
                                for pl in t.get("places", [])]}),
        ],
    )


def stickycta(data, c, r, t):
    """The persistent action on a destination page, on a phone.

    The UI specification says this should be "Add to my journey" rather than
    "Book now", and is right for a reason worth writing down: a booking
    button that cannot book is a lie, and this product has nothing to sell.
    What a reader can actually do here is save the place and start a route
    from it, so those are the two actions.

    Phone only, and only on a destination page. A bar pinned over every page
    at every width is a bar that is in the way most of the time.
    """
    # AND THE NAME CAME OUT OF THE BAR, BECAUSE IT WAS A BROKEN WORD ON
    # 146 OF 319 PAGES. The bar carried the destination's name in a flexed
    # span with an ellipsis, and two buttons take 230 of a 390-pixel phone:
    # measured on every destination at 390, 46% of them rendered a cut word —
    # "Innsbr...", and "Gura Humorului & the painted monasteries" 255 pixels
    # over its slot. A name sliced mid-word reads as a broken renderer, which
    # is the rule this repository already applies to a map label.
    #
    # It is also redundant where it is not broken. A reader is ON the page;
    # the h1 two screens up is the answer, and what the save actually records
    # comes from `data-label` rather than from this span. So the subject
    # moves INTO the actions, which is where a screen reader needs it anyway:
    # "Save Innsbruck" and "Add Innsbruck to my journey" name the thing being
    # acted on at the moment of acting, and the visible labels stay short
    # enough to be read on a phone.
    return f'''<div class="stickycta">
  <button class="btn ghost" type="button" data-short
          data-save="city:{esc(c['slug'])}/{esc(r['slug'])}/{esc(t['slug'])}"
          data-kind="Place" data-label="{esc(t['name'])}, {esc(c['name'])}"
          data-url="{urls.city(c, r, t)}"
          aria-label="Save {esc(t['name'])}">Save</button>
  <a class="btn" href="/plan?from={esc(c['slug'])}%2F{esc(r['slug'])}%2F{esc(t['slug'])}"
     aria-label="Add {esc(t['name'])} to my journey">Add to my journey</a>
</div>'''


def sectionnav(items):
    """The destination page's own contents, from the UI specification.

    Horizontally scrolling on a phone, a plain row on a desktop. Only
    sections that actually exist on this page are listed: a tab leading to an
    anchor that is not there is worse than no tab, because the page silently
    does not move and the reader assumes they mis-tapped.

    It is a <nav> with real in-page links, so it works with the keyboard,
    with a screen reader's landmark list, and with JavaScript off — which is
    the whole reason it is not a JS tab widget.
    """
    live = [(label, anchor) for label, anchor in items if anchor]
    if len(live) < 3:
        return ""
    links = "".join(f'<a href="#{esc(a)}">{esc(l)}</a>' for l, a in live)
    return (f'<nav class="sectionnav" aria-label="On this page">{links}</nav>')



# ── interests ─────────────────────────────────────────────────────────

# How wide a tag is, in words, from a stated vocabulary.
#
# THE BAND IS AUTHORED; THE NUMBER IS DERIVED. That is the Data Integrity
# Rule's line and this sits on the legal side of it: "History & ruins covers
# 63% of the atlas" is a measurement, computed on every build and never
# typed; "63% is too wide to be a useful filter" is a classification, made
# from a published threshold that a reader can disagree with.
INTEREST_BANDS = (
    (40, "As a filter on its own it barely narrows Europe. It is most useful "
         "combined with a second one in Discover Mode."),
    (15, "It narrows Europe usefully without emptying it, which is about "
         "where a filter earns its place."),
    (0,  "One of the narrowest tags in this atlas, which makes it a real "
         "filter — and a short list is a gap in the writing as much as a "
         "fact about Europe."),
)


_MACRO_OF = {}


def _macro_of(data, country_slug):
    """Which of the nine macro regions a country sits in.

    Built once. `data/taxonomy.json` puts every country in exactly one, which
    is asserted by the validator, so this cannot return None for a country
    the atlas holds a page for.
    """
    if not _MACRO_OF:
        for m in data["macros"]:
            for c in m["countries"]:
                _MACRO_OF[c] = m["slug"]
    return _MACRO_OF[country_slug]


def interests_index(data, ranking):
    """The Interest Atlas: seven plates, and the three scales are the page's
    own published judgement rather than a styling choice.

    THE PAGE WAS AN OPENING, A STRIP OF EIGHT AND A LEDGER. 93,206 bytes and
    nine photographs of the eighteen the register holds for this family —
    every one of the seventeen tags has one, and so does the index. That is
    the /experiences finding for the fourth family running: *the pictures
    were already bought and were being spent on one strip.* Nothing is
    acquired here. All eighteen are on the page now, each exactly once.

    AND THE ALLOCATION IS `INTEREST_BANDS`, WHICH THIS FAMILY ALREADY
    PUBLISHES. Every interest page prints one of three judgements about its
    own tag — at or above 40% of the Atlas it *barely narrows Europe*,
    between 15 and 40 it *narrows Europe usefully*, below 15 it is *one of
    the narrowest tags in this atlas*. Those three sentences are the three
    visual scales: two at feature size, seven in a strip, eight with their
    own pictures at the narrow end. The brief asks for an explicit visual
    distinction between broad and narrow interests and this is that
    distinction derived from the sentence the family already writes, rather
    than a threshold picked to make a layout work.

    THE BRIEF'S REACH BAR IS REFUSED, AND SO IS ITS INTERACTIVE MAP.

    A bar would be the THIRD drawing of one number: the row already prints
    the percentage, and the seventeen glyphs are drawn to one frame for
    exactly this reason — *a knot is an argument about one corner of Europe,
    a scatter is one about the whole of it* — so reach is the one thing this
    page has never needed a second representation of. /journeys records what
    happens when a band draws the same measurement twice on two grids.

    And *select an interest and the map becomes its geography* is a control.
    This page loads no JavaScript at all, so a selector here would be the
    chip that filters nothing and the `data-rotate` copy nobody ever read.
    The seventeen ARE the interest atlas, drawn at once, which is the one
    thing seventeen separate pages cannot do and is why the ledger band
    carries both names.

    WHAT THE LEDGER WAS MISSING IS THE SECOND AXIS, AND THE SENTENCE IT
    ALREADY PRINTED HID IT. *Greece, Italy and Spain carry the most of it*
    is 26% of History between them and *Norway, Switzerland and Germany
    carry the most of it* is 73% of Slow rail — two sentences of identical
    shape, one of which is barely a fact and one of which is the whole tag.
    That is the `8 PLACES` failure, in prose instead of a number. The share
    is printed now, so a row says something different from the row above it.

    And the share is the evidence under the brief's own closing argument:
    the eight narrow tags put a median 51% of themselves into three
    countries against 33% for the nine broad ones. A narrow filter does not
    only shorten the list, it points at a corner of the continent — which is
    what *a small filter can open a large door* means, measured.
    """
    images = data.get("images")
    idx = data["cities"]
    total = len(idx)
    silhouette = constel_defs()
    by_slug = {i["slug"]: i for i in data["taxonomy"]["interests"]}

    # ONE PASS OVER THE ATLAS, AND EVERY FIGURE ON THIS PAGE COMES OUT OF
    # IT. A second walk for the narrow band would be a second chance for the
    # two halves of one page to disagree about what Festivals is.
    facts = {}
    for slug in ranking:
        cities = [c for c in idx.values() if slug in c["city"]["interests"]]
        tally = {}
        for c in cities:
            tally[c["country"]["name"]] = tally.get(c["country"]["name"], 0) + 1
        top = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        facts[slug] = {
            "name": by_slug[slug]["name"],
            "cities": cities,
            "n": len(cities),
            "ncountry": len(tally),
            "pct": round(100.0 * len(cities) / total) if total else 0,
            "lead": [nm for nm, _ in top],
            # The share of the tag its three strongest countries hold. Never
            # a share of the ATLAS: that is the reach figure beside it, and
            # two percentages in one line that mean different things is how
            # a reader stops reading either.
            "top3": (round(100.0 * sum(v for _, v in top) / len(cities))
                     if cities else 0),
            "pts": [project(c["city"]["lat"], c["city"]["lon"]) for c in cities],
        }

    # THE THREE BANDS ARE READ OFF `INTEREST_BANDS` RATHER THAN SLICED BY
    # POSITION. `ranking[:3]` would be a layout deciding an argument, and it
    # would silently stop agreeing with the seventeen pages the day a tag
    # crosses 40%. The floors are the table's own.
    def _band(pct):
        for k, (floor, _) in enumerate(INTEREST_BANDS):
            if pct >= floor:
                return k
        return len(INTEREST_BANDS) - 1

    wide = [s for s in ranking if _band(facts[s]["pct"]) == 0]
    mid = [s for s in ranking if _band(facts[s]["pct"]) == 1]
    narrow = [s for s in ranking if _band(facts[s]["pct"]) == 2]

    drawn = []
    rows = []
    for slug in ranking:
        f = facts[slug]
        drawn.extend(f["pts"])
        # THE MARK SIZE HAS TO FOLLOW THE COUNT. `.constel-theme` was sized
        # for a theme's EIGHT stops; two hundred dots at that radius is a
        # solid mass with the coastline lost under it, which says "a lot"
        # and nothing else — and the whole argument of this band is that you
        # can see the difference between the shapes.
        dense = " constel-dense" if len(f["pts"]) > 60 else ""
        glyph = constellation(f["pts"], extra=" constel-theme" + dense)
        where = (f'{and_list(f["lead"])} hold {f["top3"]}% of it'
                 if len(f["lead"]) > 1 else
                 (f'{f["lead"][0]} holds all of it' if f["lead"]
                  else "Nothing carries it yet."))
        rows.append(
            f'<a class="row themerow interestrow" href="{urls.interest(slug)}">'
            f'<div class="rowart">{glyph}</div>'
            f'<div><p class="kicker">{n_of(f["n"], "destination")} &middot; '
            f'{f["pct"]}% of the Atlas &middot; {n_of(f["ncountry"], "country")}</p>'
            f'<h3>{esc(f["name"])}</h3>'
            f'<p class="rowsub">{esc(where)}</p></div></a>')

    def _median(xs):
        xs = sorted(xs)
        if not xs:
            return 0
        h = len(xs) // 2
        return xs[h] if len(xs) % 2 else round((xs[h - 1] + xs[h]) / 2)

    midconc = _median([facts[s]["top3"] for s in wide + mid])
    narrowconc = _median([facts[s]["top3"] for s in narrow])

    # ── 01 · INTERESTS ───────────────────────────────────────────────
    hero = photo(images, "interests-hero", w=2400, h=1200, eager=True,
                 sizes="100vw",
                 alt="A European street seen down its own length.")
    iopen = f"""
  <div class="iopen">
    <h1 class="mega">{numword(len(ranking), cap=True)} ways to cross a
    <em class="lit">continent</em>.</h1>
    <p class="lede">Not a list of everything Europe has. {numword(len(ranking),
    cap=True)} tags that each narrow {total:,} destinations to a set worth
    reading &mdash; and the useful ones are not the biggest. History covers
    almost the whole Atlas and tells you very little; the narrow ones are
    where a filter earns its place.</p>
  </div>
  <figure class="ibleed">{hero or ed_slot("interests-hero", shape="wide",
      label="What you are travelling for")}</figure>"""

    # ── 02 · THE QUESTION ────────────────────────────────────────────
    # A STATEMENT BAND SAYS ONE THING AND DOES NOT EXPLAIN THE PAGE BACK.
    # The opening has already said what the seventeen are; this says why
    # they exist at all, which is the only thing left to say before the
    # reader meets them.
    firstact = """
  <div class="sheettext">
    <h2 class="mega">Interest is the first act of discovery.</h2>
    <p class="lede">A tag here is an instrument rather than a label. Each one
    changes the geographic field: the destinations carrying it become the
    shape of your Europe, and two of them together become a much smaller and
    much more particular one.</p>
  </div>"""

    # ── 03 · THE WIDE END ────────────────────────────────────────────
    # THE FEATURE SCALE IS THE ONE THE SEVEN IMAGE SCALES ALREADY HOLD —
    # 1.35 against .65, because two equal columns read as a layout and an
    # unequal pair reads as a picture with something to say. No new
    # component, and the alternation is what stops two features reading as
    # a pattern.
    def _say(slug):
        f = facts[slug]
        return (f'<p class="kicker">{n_of(f["n"], "destination")} &middot; '
                f'{f["pct"]}% of the Atlas &middot; '
                f'{n_of(f["ncountry"], "country")}</p>'
                f'<p class="rowsub">{esc(and_list(f["lead"]))} hold '
                f'{f["top3"]}% of it.</p>'
                f'<p>{esc(INTEREST_BANDS[0][1])}</p>'
                f'{golink(urls.interest(slug), "Open " + f["name"].lower())}')

    feats = "".join(
        ed_feature(images, f"interest:{s}", title=facts[s]["name"],
                   body=_say(s), alt=facts[s]["name"], right=bool(k % 2),
                   level=3)
        for k, s in enumerate(wide))
    midstrip = ed_strip(images, [
        {"key": f"interest:{s}", "alt": facts[s]["name"],
         "label": facts[s]["name"], "href": urls.interest(s),
         "note": f'{facts[s]["n"]} destinations · {facts[s]["pct"]}%'}
        for s in mid], limit=len(mid))
    lenses = f"""
  <div class="sheettext">
    <h2 class="mega">The wide end.</h2>
    <p class="lede">{numword(len(wide), cap=True)} tags sit above
    {INTEREST_BANDS[0][0]}% of the Atlas, and this family's own judgement of
    them is that as a filter each barely narrows Europe. They are worth
    seeing rather than worth filtering by &mdash; which is why they are the
    pictures here and the narrow ones are the list at the end.</p>
  </div>
  {feats}
  <p class="small">Below them, {numword(len(mid))} more between
  {INTEREST_BANDS[1][0]} and {INTEREST_BANDS[0][0]}% of the Atlas: the band
  where, in this family's own words, a tag narrows Europe usefully without
  emptying it.</p>
  {midstrip}"""

    # ── 04 · THE INTEREST ATLAS ──────────────────────────────────────
    ledger = f"""
  <div class="pagehead index">
    <p class="kicker">The interest atlas</p>
    <h2 class="mega">Every question makes a different Europe.</h2>
    {head_extent([(len(ranking), "ways to travel"),
                  (total, "destinations"),
                  (len({c["country"]["slug"] for c in idx.values()}), "countries")])}
  </div>
  {silhouette}
  <div class="rows">{"".join(rows)}</div>
  <p class="small">Each shape is that tag&rsquo;s own destinations on the
  continent, drawn to the same frame so the {numword(len(ranking))} can be
  compared: a knot is an argument about one corner of Europe, a scatter is one
  about the whole of it. The order is reach &mdash; how much of the Atlas each
  tag carries &mdash; rather than alphabetical, and the sentence under each
  name is the share its three strongest countries hold, which is a different
  question from reach and disagrees with it more often than not.
  {geo.sources_line(geo.load("europe-lod0.json"))}{offframe_line(drawn, data, listed=False)}
  Two of them can be combined in <a href="/discover">Discover Mode</a>, which
  is where a narrow tag does its real work.</p>"""

    # ── 05 · THE NARROW END ──────────────────────────────────────────
    # AND THIS IS WHERE THE REST OF THE LIBRARY GOES. Eight tags, eight
    # photographs, none of which had ever been on this page: the strip took
    # the widest eight and the narrow end of the family — the half the page
    # argues is the useful half — was the half with no picture at all.
    # A ROW IS NOT AN `<a>` WHEN IT HOLDS A PHOTOGRAPH, AND THIS COMMIT
    # REPRODUCED /stories' OWN DEFECT BEFORE IT WAS CAUGHT. `picture()`
    # emits the Pexels credit as a `<figcaption class="credit">` INSIDE
    # the `<picture>`, and that credit is two anchors — so wrapping the
    # whole row in one made an `<a>` inside an `<a>`, which the HTML parser
    # is specified to resolve by CLOSING the outer one. Chromium's
    # error recovery then reopens it around each following run, so eight
    # rows measured as TWENTY-FOUR in the browser and the band rendered
    # 4,594 pixels tall. Nothing in the markup looks wrong and no count
    # sees it: the emitted HTML contains exactly eight.
    #
    # So the picture is a figure, the NAME is the link, and the two links
    # the licence requires sit in a credit that is inside no anchor at all.
    # Found by rendering, in the commit after the one that wrote the rule
    # down — *a rule recorded is not a rule inherited*.
    narrowcards = "".join(
        f'<div class="row narrowrow">'
        f'<figure class="narrowshot">{picture(images, "interest:" + s, w=900, h=700, alt=facts[s]["name"], sizes="(max-width: 52rem) 90vw, 22rem") if held(images, "interest:" + s) else ed_slot("interest:" + s, shape="square", label=facts[s]["name"])}</figure>'
        f'<div><p class="kicker">{n_of(facts[s]["n"], "destination")} &middot; '
        f'{facts[s]["pct"]}% of the Atlas</p>'
        f'<h3><a href="{urls.interest(s)}">{esc(facts[s]["name"])}</a></h3>'
        f'<p class="rowsub">{esc(and_list(facts[s]["lead"]))} hold '
        f'{facts[s]["top3"]}% of it.</p></div></div>'
        for s in narrow)
    narrowband = f"""
  <div class="sheettext">
    <h2 class="mega">The narrow end.</h2>
    <p class="lede">{numword(len(narrow), cap=True)} tags under
    {INTEREST_BANDS[1][0]}% of the Atlas. A short list is a gap in the
    writing as much as it is a fact about Europe &mdash; and it is also the
    only end of this family where choosing one changes where you would go.</p>
  </div>
  <div class="rows narrowgrid">{narrowcards}</div>"""

    # ── 06 · A SMALL FILTER ──────────────────────────────────────────
    # THE STATEMENT CARRIES ITS OWN EVIDENCE, because a claim about filters
    # made on a page that publishes the numbers is checkable in the line
    # under it. Festivals is excluded from neither figure and named in both
    # directions: three destinations in three countries is 100% in its top
    # three by arithmetic, which is the small-sample trap /events already
    # recorded — a median rather than a mean is what stops one row of three
    # deciding a sentence about eight.
    smallfilter = f"""
  <div class="sheettext">
    <h2 class="mega">A small filter can open a large door.</h2>
    <p class="lede">History covers {facts[ranking[0]]["pct"]}% of the Atlas
    and therefore tells you almost nothing about where to go next. The narrow
    tags do the opposite, and it is measurable: the {numword(len(narrow))} of
    them put a median {narrowconc}% of themselves into three countries,
    against {midconc}% for the {numword(len(wide) + len(mid))} above them. A
    narrow filter does not only shorten the list &mdash; it points at a corner
    of the continent.</p>
    <p class="note">The median rather than the average, because Festivals is
    {facts["festivals"]["n"] if "festivals" in facts else 3} destinations in
    as many countries and any share computed on three rows is a fact about
    the sample. Every figure on this page is counted on the build.</p>
  </div>"""

    # ── 07 · OPEN A DOOR ─────────────────────────────────────────────
    istart = """
  <div class="istart">
    <h2 class="mega">Start with what you care about.</h2>
    <p class="lede">Choose an interest and see where it lives. Follow it into
    a destination, a story, an experience or a journey &mdash; or put two of
    them together and watch most of Europe fall away.</p>
    <p class="keepgo"><a class="btn" href="/discover">Combine two interests</a>
    <a class="storygo" href="/countries">Or open the atlas &rarr;</a></p>
  </div>"""

    PLATES = [("iopen gal", "Ways to travel", iopen, "ways-to-travel"),
              ("firstact pine", "The question", firstact, "the-question"),
              ("lenses gal", "The wide end", lenses, "wide"),
              ("reach paper", "The interest atlas", ledger, "reach"),
              ("narrow gal quiet", "The narrow end", narrowband, "narrow"),
              ("smallfilter gal", "A small filter", smallfilter, "small-filter"),
              ("istart pine", "Start here", istart, "start")]
    body = f"""
{crumbs([("Europe", "/discover"), ("Ways to travel", None)])}
{plate_sequence(PLATES)}
"""
    return "/interests/index.html", page(
        "Ways to travel", body, path="/interests", area="countries",
        accent="natural", hero=True,
        description="Seventeen ways into Europe — history, food, mountains, islands, "
                    "sacred places, rail — each one drawn as the destinations that carry it.",
    )


def interest_page(data, i, ranking):
    slug = i["slug"]
    cities = [n for n in data["cities"].values() if slug in n["city"]["interests"]]
    cities.sort(key=lambda n: (n["country"]["name"], n["city"]["name"]))
    countries = sorted({n["country"]["slug"] for n in cities})
    total = len(data["cities"])
    pct = round(100.0 * len(cities) / total) if total else 0
    rank = ranking.index(slug) + 1
    # Zero is not the narrow end of the scale, it is off it. Forcing the
    # empty state to render — the only way to see a latent branch — showed
    # the band sentence claiming a tag with no destinations "makes a real
    # filter", which is a judgement about a list that does not exist.
    band = ("Nothing carries it yet, so there is no list to judge."
            if not cities
            else next(text for floor, text in INTEREST_BANDS if pct >= floor))
    # SEVEN HUNDRED AND TWENTY-EIGHT ABSTRACT PLATES ON SEVENTEEN PAGES.
    #
    # That is forty-three hash-drawn landscapes in a column on the average
    # interest page, which is the measurement that emptied the homepage,
    # /journeys, /europe-in and the stories index — placeholder art doing a
    # picture's job — still shipping on the family that had the most of it.
    # Eleven in a column was called a SaaS body under an atlas hero; forty
    # three is a wall of gradients with the destinations behind it.
    #
    # A destination on this page is not chosen on LOOK, which is the test a
    # card has to pass. It is chosen on where it is and what it is, and both
    # of those are words. So the set is rows, and the whole set: the list
    # used to stop at sixty with one sentence admitting it, and a list that
    # stops is the one kind of incompleteness a reader cannot detect. Rows
    # cost a few hundred bytes each, so there is no longer a reason to stop.
    #
    # AND SIXTY-THREE ROWS IN ONE COLUMN IS A LIST NOBODY READS. They were
    # sorted by country and nothing marked where one country ended, so the
    # order was real and invisible: Theth, Andorra la Vella, Madriu, Dilijan,
    # Tsaghkadzor — correct, and indistinguishable from alphabetical by
    # accident. The page opens on a drawing whose whole argument is WHERE
    # these places are, and then handed the reader a flat column.
    #
    # Grouped by macro region, which is the atlas's own geographic grouping
    # and the one the drawing above is made of — nine groups over sixty-three
    # rows rather than thirty country headings over two rows each. It is a
    # CLASSIFICATION and not a ranking: the groups run in the taxonomy's own
    # order on every one of the seventeen pages, and a reader can see that
    # Mountains is four ranges and History is the whole continent from the
    # group headings alone.
    by_macro = {}
    for n in cities:
        by_macro.setdefault(_macro_of(data, n["country"]["slug"]), []).append(n)
    rows = "".join(
        f'<div class="rowgroup"><p class="rowgrouphead">{esc(m["name"])}'
        f'<span class="rowgroupn">{len(by_macro[m["slug"]])}</span></p>'
        + "".join(
            f'<a class="row" href="{urls.city(n["country"], n["region"], n["city"])}">'
            f'<div><h2>{esc(n["city"]["name"])}</h2>'
            f'<p class="rowsub">{esc(n["city"]["summary"])}</p></div>'
            f'<p class="rowmeta">{esc(n["country"]["name"])} · '
            f'{esc(n["region"]["name"])}</p></a>'
            for n in by_macro[m["slug"]])
        + "</div>"
        for m in data["macros"] if m["slug"] in by_macro)
    # THE SHAPE OF THE TAG, DRAWN, AND IT IS THE PAGE'S OWN SENTENCE AS A
    # PICTURE. `docs/signature-moments.md` refused a map here on the grounds
    # that the three largest tags would draw three identical maps of Europe.
    # That is true of History, Food and Architecture and it is exactly what
    # this page already says in words — over 40% barely narrows anything —
    # so the drawing agrees with the sentence rather than contradicting it,
    # and for Islands, Snow and Wildlife it says something the sentence
    # cannot. It is the homepage tiles' own argument: Mountains is four
    # ranges, History is almost everywhere, and the difference between those
    # two shapes is the thing worth showing.
    #
    # NOT FRAMED, deliberately, for the reason /themes is not framed: what
    # is being compared across seventeen pages is REACH, and that comparison
    # only exists while every one of them is drawn at the same extent.
    #
    # AND NO APERTURE. The refusal in signature-moments was about the door,
    # not about geography, and it still holds: this is a glyph.
    art = constellation([project(n["city"]["lat"], n["city"]["lon"])
                         for n in cities], cut=True) if cities else ""
    photoband = pageband(data, f"interest:{i['slug']}")
    # SIXTY-THREE ROWS OF PLACE NAMES IS NOT A PICTURE OF ANYTHING.
    #
    # The page opens on a photograph of the tag and a drawing of its reach,
    # and then hands the reader a flat column of names grouped by macro
    # region — correct, complete, and the exact shape §23 names: text,
    # whitespace, a small map and rows. The destinations are the content,
    # and every one of them already declares a `city:` purpose.
    #
    # WIDEST-FIRST WOULD BE A RANKING THIS ATLAS DOES NOT HOLD, so the strip
    # takes the list's own order — country then name, the order the rows
    # below are in — and stops at eight. The reader who wants all of them
    # scrolls to the rows; the strip exists to say what a tag looks like,
    # not to choose for anybody.
    _ishots = ed_strip(data.get("images"), [
        {"key": f"city:{n['country']['slug']}/{n['region']['slug']}/{n['city']['slug']}",
         "alt": n["city"]["name"], "label": n["city"]["name"],
         "href": urls.city(n["country"], n["region"], n["city"])}
        for n in cities], limit=8)
    if _ishots:
        # A TAG NAME CANNOT BE THE SUBJECT OF A VERB HERE. "What mountains
        # looks like" — seventeen tags, some plural, some a compound with an
        # ampersand, and no single conjugation is right for all of them. A
        # heading that has to guess at agreement is a heading generated from
        # a name it does not know the grammar of, so the name is a noun
        # phrase and the count carries the sentence. Derived, because the
        # strip takes eight OR the whole set, whichever is smaller, and a
        # heading saying eight over five pictures is the constant-wearing-a
        # -measurement's-clothes failure this atlas has already made twice.
        _n = min(8, len(cities))
        _ishots = ('<section class="ed-section">'
                   + ed_section_head("Travelling for it",
                                     f"{i['name']}, in {numword(_n)} places",
                                     f"{numword(_n, cap=True)} of the {len(cities)} "
                                     f"destinations carrying the tag, in the order "
                                     f"the list below is in.")
                   + _ishots + "</section>")
    body = f"""
{crumbs([("Europe", "/discover"), ("Experiences", "/experiences"), (i["name"], None)])}
{photoband}
{constel_defs()}
{indexhero(
    kicker="Travelling for",
    title=esc(i["name"]),
    lede=f"{len(cities)} of the {total} destinations in this atlas are tagged "
         f"{esc(i['name'].lower())}. {band}",
    art=art,
    note=f"{pct}% of the atlas · {len(countries)} of {len(data['countries'])} "
         f"countries · {rank_phrase(rank, len(ranking))}"
         + (f'. Every destination carrying the tag, drawn on one frame so the '
            f'seventeen can be compared. Coastline from '
            f'<a href="/sources">Natural Earth</a>, public domain.'
            + datacut_line()
            + offframe_line([project(n["city"]["lat"], n["city"]["lon"])
                             for n in cities], data) if cities else ""))}

{_ishots}
{f'<div class="rows">{rows}</div>' if rows else empty_state(
      "No destination carries this tag yet.",
      "The tag exists in the taxonomy and the Journey Planner already weights "
      "it, so the moment a destination is written with it this page fills "
      "itself. Nothing is filtered out here — there is nothing in yet.")}

<div class="note mt7">
  <h2 class="mini">Why this page tells you its own tag is wide</h2>
  <p>A filter that matches most of a continent is not a filter, and hiding
  that makes the tool look better than it is. The share is counted from the
  dataset on every build; the sentence about it comes from one published
  rule — over 40% barely narrows anything, 15–40% narrows usefully, under
  15% is genuinely narrow. The Journey Planner weights this same tag, so what
  you see here is what it will build from.</p>
</div>
"""
    # FOUR TITLES COLLIDED ACROSS THE SITE and this is one of them:
    # /interests/architecture and /experiences/culture/architecture both
    # read "Architecture · EuropeDoor" in a tab, a bookmark, a search result
    # and this site's own index. They are different things — destinations
    # TAGGED architecture against experiences that are about it — and the
    # page says so in its kicker and not in its title. The kicker is the
    # disambiguation, so the title takes it.
    return f"/interests/{slug}/index.html", page(
        f"Travelling for {i['name'].lower()}", body,
        path=urls.interest(slug), area="countries",
        accent="natural",
        description=f"Where in Europe to go for {i['name'].lower()}: {len(cities)} cities across {len(countries)} countries.",
    )


# ── journeys ──────────────────────────────────────────────────────────

def journeys_index(data):
    """THE EUROPEAN JOURNEY ATLAS — movement drawn, and the drawing already
    existed.

    Four pages, four instruments, one institution: /discover is the
    instrument, /countries is the atlas, /experiences is photography, and
    this one asks how you want to MOVE. `docs/journeys-redesign.md` is the
    audit — what the page held, what the register holds, and which of the
    brief's bands are derived rather than authored.

    IT WAS SEVENTEEN IDENTICAL ROWS, AND EVERY ONE OF THEM WAS GOOD. A
    strapline kicker, the name, the stops in order, a `hopbar` laid end to
    end as the trip's own rhythm, the facts, and a route glyph framed on
    that journey's own extent — no two of the seventeen lines are alike,
    which is the test the homepage's four doors failed and this one passes.
    The row was itself a repair: this index used to be four abstract plates
    across. The fault is the sum. Measured on the built page at 1280: 5,095
    pixels, one photograph, 5.9% of the page area, one shape seventeen
    times.

    AND THE FAMILY'S OWN SIGNATURE DRAWING WAS BUILT ON EVERY BUILD AND
    THROWN AWAY. `heroart` composes all seventeen routes at once on one
    conformal conic — casings first and then cores, so a crossing does not
    break a line — and handed it to `indexhero(art=…)`, which prefers `img`
    when the register holds one. The register holds `journeys-hero`. So the
    one picture no other travel product can make was assembled and
    discarded, and what a reader met instead was a stock photograph of a
    train. It is the opening now, at size, which is what this family's
    opening is FOR.
    """
    images = data.get("images") or {}
    idx = data["cities"]
    js = data["journeys"]

    def legcities(j):
        return [idx[l["city"]] for l in j["legs"]]

    def pts_of(j):
        return [project(n["city"]["lat"], n["city"]["lon"]) for n in legcities(j)]

    def km_of(j):
        cs = [n["city"] for n in legcities(j)]
        return sum(haversine(cs[i], cs[i + 1]) for i in range(len(cs) - 1))

    def countries_of(j):
        out = []
        for n in legcities(j):
            if n["country"]["name"] not in out:
                out.append(n["country"]["name"])
        return out

    def credit(keys):
        """One credit per band, paid once — the homepage's own rule, and
        never on the opening: that surface is the composition and the
        register is where the record lives."""
        out, seen = [], set()
        for k in keys:
            row = images.get(k)
            if not row or row["photographer"] in seen:
                continue
            seen.add(row["photographer"])
            out.append(f'<a href="{esc(row["source"])}" rel="noopener" '
                       f'target="_blank">{esc(row["photographer"])}</a>')
        return ('<p class="sheetcred rowcred">Photographs by '
                + ", ".join(out) + " on Pexels.</p>") if out else ""

    # ── 01 · THE ROAD ────────────────────────────────────────────────
    # ALL SEVENTEEN AT ONCE, AND THE CASINGS BEFORE THE CORES. Seventeen
    # routes cross each other constantly, and a per-route casing lays the
    # next route's cream stroke over the last one's cobalt — a line that
    # breaks wherever another passes. Both passes over the whole set, which
    # is how a printed map plates a network.
    routepts = [pts_of(j) for j in js]
    allroutes = "".join(
        '<polyline class="constel-route case" points="'
        + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '"/>'
        for pts in routepts) + "".join(
        '<polyline class="constel-route" points="'
        + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '"/>'
        for pts in routepts)
    allmap = (f'<svg class="constel allroutes" viewBox="0 0 {MAP_W} {MAP_H}" '
              f'preserveAspectRatio="xMidYMid meet" '
              f'aria-hidden="true" focusable="false"><use href="#constel-eu"/>'
              f'{cut_fade("ih", MAP_W, MAP_H, dusk_reach(), cls="datacut")}'
              f'{allroutes}</svg>')
    stops_all = {l["city"] for j in js for l in j["legs"]}
    # AN INDEX STATES ITS EXTENT, AND THE HONEST EXTENT OF A JOURNEY SYSTEM
    # IS HOW MUCH OF THE CONTINENT IT REACHES. Seventeen routes and 76 stops
    # are both derived and both true, and neither of them says that a reader
    # looking for Iceland, Ireland, Bulgaria or Georgia will not find a
    # journey through it: the seventeen touch 29 of the fifty countries, and
    # only three of the twenty-one they miss carry a travel advisory. The
    # specification names four multi-country journeys and this atlas has all
    # four, which is the measurement the section audit already records — and
    # it is an extent rather than a coverage, so it can be entirely true
    # while the map has a hole in it. Derived, so writing a journey through
    # Iceland moves the number on the next build rather than leaving a
    # sentence that was accurate once.
    reached = {idx[cid]["country"]["slug"] for cid in stops_all if cid in idx}
    road = f"""
  <div class="sheettext">
    <p class="kicker">The European Journey Atlas</p>
    <h1 class="mega">Europe is <br>a <em class="lit">journey</em>.</h1>
    <p class="lede">Not a line between two points. {numword(len(js), cap=True)}
    routes, {len(stops_all)} stops across {len(reached)} of the
    {len(data["countries"])} countries, every one of them a real place in
    this atlas and every leg a real distance. Drawn here all at once, on the
    projection every other map on this site uses.</p>
    {golink('#the-routes', 'Read the seventeen')}
  </div>
  <figure class="roadart">{allmap}
    <figcaption>Every line is one of the {numword(len(js))}, drawn from its own
    stops. {geo.sources_line(geo.load("europe-lod0.json"))}{datacut_line()}</figcaption>
  </figure>"""

    # ── 02 · THE SEVENTEEN ───────────────────────────────────────────
    rows = []
    for i, j in enumerate(js, 1):
        cs = legcities(j)
        stops = [esc(n["city"]["name"]) for n in cs]
        hops = [haversine(cs[k]["city"], cs[k + 1]["city"])
                for k in range(len(cs) - 1)]
        total = sum(hops)
        # THE SEGMENTS ARE A SHARE OF THE WHOLE TRIP, not of its longest leg.
        # The journey page asks which of these days is the long one; here the
        # bar is the whole route in one line, so the shape is the trip's own
        # rhythm rather than a comparison between trips.
        segs = "".join(
            f'<span class="w{max(1, int(round(km / total * 100)))}"></span>'
            for km in hops) if total else ""
        route = constellation(pts_of(j), route=True, frame=True, mark=19)
        rows.append(
            f'<a class="row journeyrow" href="{urls.journey(j)}">'
            f'<div><p class="kicker"><span class="jno">{i:02d}</span>'
            f'{esc(j["strapline"])}</p>'
            f'<h2>{esc(j["name"])}</h2>'
            f'<p class="rowsub">{" · ".join(stops)}</p>'
            f'<span class="hopbar route" aria-hidden="true">{segs}</span>'
            f'<p class="rowmeta jfacts">{n_of(j["days"], "day")} · '
            f'{n_of(len(countries_of(j)), "country")} · {esc(j["difficulty"])}</p>'
            f'</div><div class="jart">{route}</div></a>')
    # THIS BAND IS THE PAGE'S HEAD, and /experiences settled the reason one
    # family over: a plate sequence has no room for a stage above the
    # opening, so the head is the band that introduces the SET. It is the
    # `pagehead` primitive rather than a fourth spelling of one, it declares
    # `index` because the page is a set, and it states the extent, because
    # an index exists to say how big a set is and five of eight once did not.
    # The count is derived; a figure typed here is the figure that was true
    # two hundred destinations ago.
    seventeen = f"""
  <div class="pagehead index">
    <h2 class="mega">Routes worth <br>remembering.</h2>
    <p class="lede">All {len(js)} of them, and a journey is not chosen on
    look, so none of these is a card. Each row carries where it goes, in
    order, and the line under it is that route's own legs end to end —
    its share of the whole distance, so the shape is the trip's rhythm.</p>
  </div>
  <div class="rows journeyrows">{"".join(rows)}</div>
  <p class="small">The shape beside each route is where it goes, on the same
  projection as every other map here. Distances are straight lines between
  coordinates; what they mean on the ground is on the journey's own page.</p>"""

    # ── 03 · THE CREED ───────────────────────────────────────────────
    creed = """
  <div class="sheettext creedsay">
    <h2 class="mega">The destination is <br>one moment in <br>the journey.</h2>
    <p class="lede">The landscape changes outside the window. The language
    shifts, then the architecture, then the table. A border stops being a
    line and becomes a day.</p>
  </div>"""

    # ── 04 · THE FEATURED JOURNEY ────────────────────────────────────
    # A JOURNEY'S PICTURE IS ONE OF ITS OWN STOPS, NOT ITS `journey-hero`.
    # The automated fill searched the role's first concept and got railways:
    # three of the nine journey photographs are the same commuter station at
    # Geesthacht and not one is about its journey. The homepage already takes
    # the picture it can defend and this page takes the same one — which also
    # decides WHICH journey is featured, because the one this atlas can show
    # best is the one it holds the most photographs of. Ties go to the
    # journey crossing the most countries, and the page says so.
    def shots_of(j):
        return [l["city"] for l in j["legs"] if ("city:" + l["city"]) in images]

    feat = max(js, key=lambda j: (len(shots_of(j)), len(countries_of(j))))
    fshots = shots_of(feat)
    fcs = legcities(feat)
    featured = ""
    if fshots:
        lead = fshots[0]
        leadleg = next(l for l in feat["legs"] if l["city"] == lead)
        rest = fshots[1:4]
        strip = "".join(
            f'<a class="fsh" href="{urls.city(idx[c]["country"], idx[c]["region"], idx[c]["city"])}">'
            + picture(images, "city:" + c, w=800, h=1000, credit=False,
                      alt=images["city:" + c]["alt"],
                      sizes="(min-width: 52rem) 16vw, 44vw")
            + f'<span class="fshname">{esc(idx[c]["city"]["name"])}</span></a>'
            for c in rest)
        featured = f"""
  <figure class="featshot">
    {picture(images, "city:" + lead, w=2000, h=1200, credit=False,
             alt=images["city:" + lead]["alt"], sizes="(min-width: 52rem) 52vw, 100vw")}
    <figcaption>{esc(idx[lead]["city"]["name"])}, {esc(idx[lead]["country"]["name"])}
    &mdash; day {leadleg["day_number"]} of {feat["days"]}</figcaption>
  </figure>
  <div class="sheettext">
    <p class="kicker">Featured &mdash; the journey this atlas can show best</p>
    <h2 class="mega">{esc(feat["name"])}</h2>
    <p class="lede">{esc(feat["summary"])}</p>
    <p class="jfacts">{n_of(feat["days"], "day")} &middot;
    {n_of(len(countries_of(feat)), "country")} &middot;
    {int(round(km_of(feat))):,} km in a straight line</p>
    {golink(urls.journey(feat), "Follow this route")}
  </div>
  <div class="fstrip">{strip}</div>
  {credit(["city:" + c for c in fshots[:4]])}"""

    # ── 05 · THE RHYTHM ──────────────────────────────────────────────
    # THE FOUR MOVEMENTS ARE DERIVED RATHER THAN NAMED. The brief asks for
    # Arrive, Cross, Pause and Continue, which is a true thing to say about
    # journeys in general and a claim no record here carries. A leg DOES
    # carry `nights`, and that is the same idea measured: a stop of one night
    # is a crossing and a stop of three is a stay. So the band draws one real
    # journey's own legs at their own lengths and the movements are that
    # journey's shape rather than four words about the idea of one.
    #
    # AND IT IS A DIFFERENT CLAIM FROM THE ROW ABOVE. The index bar is a
    # share of the DISTANCE and this is a share of the NIGHTS — the rhythm of
    # the road against the rhythm of the nights, which is why a journey with
    # eight legs and nineteen days is not eight equal blocks.
    def movement(nights):
        return ("a crossing" if nights <= 1 else
                "a stop" if nights == 2 else "a stay")

    nights_total = sum(l["nights"] for l in feat["legs"]) or 1
    nightbar = "".join(
        f'<span class="w{max(1, int(round(l["nights"] / nights_total * 100)))}"></span>'
        for l in feat["legs"])
    beats = "".join(
        f'<div class="beat">'
        f'<span class="beatno">{k:02d}</span>'
        f'<span class="beatname">{esc(idx[l["city"]]["city"]["name"])}</span>'
        f'<span class="beatkind">{n_of(l["nights"], "night")} &mdash; {movement(l["nights"])}</span>'
        f'<span class="beatwhy">{esc(l.get("why", ""))}</span></div>'
        for k, l in enumerate(feat["legs"], 1))
    rhythm = f"""
  <div class="sheettext">
    <h2 class="mega">Arrive. Cross. <br>Pause. Continue.</h2>
    <p class="lede">One journey's own legs, at their own lengths. A leg
    carries nights, so the movement is measured rather than named: one night
    is a crossing, two is a stop, three or more is a stay. This is
    {esc(feat["name"])} &mdash; {n_of(nights_total, "night")} over
    {n_of(len(feat["legs"]), "leg")}.</p>
  </div>
  <figure class="nightfig">
    <span class="hopbar route nights" aria-hidden="true">{nightbar}</span>
    <figcaption>Eight legs, each drawn at its share of the {nights_total}
    nights &mdash; a share of the WHOLE trip rather than of its longest leg,
    because the question here is the trip's rhythm.</figcaption>
  </figure>
  <div class="beats">{beats}</div>"""

    # ── 06 · THE STORIES ON THESE ROADS ──────────────────────────────
    # THE SET IS DERIVED AND THE RULE IS PRINTED. A story carries a validated
    # `places` field; the ones that name a place these seventeen routes pass
    # through are the essays that happen ON them, which is a relation this
    # atlas holds rather than an editorial guess about which essays are
    # "about travel". It SCROLLS, because `ed_strip` is the component for a
    # sequence and because showing three of six would be a selection wearing
    # the clothes of a set.
    MIDDOT = "\u00a0\u00b7 "
    onroad = []
    for s in sorted(data["stories"], key=lambda s: s.get("published", ""),
                    reverse=True):
        hits = [p for p in (s.get("places") or []) if p in stops_all]
        if hits and held(images, "story:" + s["slug"]):
            onroad.append((s, hits))
    tales = ""
    if onroad:
        tales = f"""
  <div class="sheettext">
    <h2 class="mega">Between the <br>destinations.</h2>
    <p class="lede">The {numword(len(onroad))} essays that name a place these
    routes pass through. A station, a ferry, a pass, a table &mdash; the part
    of a journey that is not a destination.</p>
    {golink('/stories', 'Every story')}
  </div>
  {ed_strip(images, [
      {"key": "story:" + s["slug"], "alt": images["story:" + s["slug"]]["alt"],
       "label": s["title"], "href": urls.story(s),
       "note": idx[h[0]]["city"]["name"] + MIDDOT + (s.get("section") or "")}
      for s, h in onroad], limit=8)}
  {credit(["story:" + s["slug"] for s, _ in onroad])}"""

    # ── 07 · THE PACE ────────────────────────────────────────────────
    # A MEASUREMENT WITH A CLASSIFICATION ON TOP, WHICH IS THE ONLY HONEST
    # ORDER. The brief names Slow, Deep and Grand. No journey record carries
    # a pace: `type` is `route` on all seventeen and `creator` is
    # `EuropeDoor editorial` on all seventeen, so neither can cut anything.
    # What the data holds is straight-line kilometres per day, which runs
    # from 30 to 319 and separates cleanly. The rule that cut it is printed,
    # exactly as every /europe-in page prints the query that made it — and
    # the figure says STRAIGHT LINE, because every distance here is a
    # haversine and this atlas holds no road or rail geometry.
    # THE LAST BAND HAS NO CEILING AND SAYS SO. The first version used a
    # sentinel of 10^9 as the loop's upper bound and then printed it: "under
    # 1000000000 km a day", on the page, as a claim to a reader. A bound that
    # exists for the arithmetic is not a bound that belongs in a sentence.
    PACE = (("Slow", 50, "under 50 km a day",
             "Short hops, long stays. The road is the smallest part of the "
             "day."),
            ("Deep", 110, "50 to 110 km a day",
             "One region, taken properly. Far enough to change the language, "
             "not far enough to lose the thread."),
            ("Grand", None, "over 110 km a day",
             "A continent in one sequence. The distance is the argument."))
    paced = {p[0]: [] for p in PACE}
    for j in js:
        rate = km_of(j) / max(1, j["days"])
        for name, cap, _rule, _say in PACE:
            if cap is None or rate < cap:
                paced[name].append((rate, j))
                break
    pacerows = "".join(
        f'<div class="pace">'
        f'<p class="kicker">{numword(len(paced[name]), cap=True)} of '
        f'{numword(len(js))}</p>'
        f'<h3>{esc(name)}</h3>'
        f'<p class="pacerule">{esc(rule)}</p>'
        f'<p class="pacesay">{esc(say)}</p>'
        f'<ul class="pacelist">' + "".join(
            f'<li><a href="{urls.journey(j)}">{esc(j["name"])}</a>'
            f'<span>{int(round(rate))} km/day</span></li>'
            for rate, j in sorted(paced[name])) + '</ul></div>'
        for name, cap, rule, say in PACE if paced[name])
    pace = f"""
  <div class="sheettext">
    <h2 class="mega">There is more <br>than one way.</h2>
    <p class="lede">Cut by straight-line kilometres a day, which is the only
    pace this atlas can measure: it holds no road and no rail geometry, so
    every distance here is a line between two coordinates and the real figure
    is higher. The names are editorial; the number is not.</p>
  </div>
  <div class="paces">{pacerows}</div>"""

    # ── 08 · THE ROAD AHEAD ──────────────────────────────────────────
    # THE FAMILY'S OWN HERO PHOTOGRAPH, SPENT ON THE CLOSE. `journeys-hero`
    # is a licensed picture of a train through a forest and the register had
    # been claiming a surface this page stopped reaching the moment the
    # opening became the drawn continent — `c_photo_published` said so in the
    # first run after the rebuild, which is the check earning its place.
    # The opening is not where it goes back: *a photograph replaces the
    # drawing, it does not sit behind it*, and the drawn seventeen-route
    # continent is the one picture no competitor can reproduce. The close is
    # where a picture does work type cannot — "where will the road take you"
    # over a line going into trees — so the band is a declaration: type over
    # the picture behind a scrim that makes the ratio a property of the
    # DESIGN. 72% graphite composites to rgb(76,83,82) and bone on that is
    # 6.90:1 whatever the photograph turns out to be, which is the same
    # arithmetic `.credit` and `ed_declare` already argued once each.
    # Not `ed_declare` itself: that composes a statement and nothing else,
    # and this band has to carry the two links the page ends on.
    sendshot = picture(images, "journeys-hero", w=2400, h=1400,
                       alt=images["journeys-hero"]["alt"], sizes="100vw") \
        if held(images, "journeys-hero") else ""
    # THE LITERAL CLASS NAME STANDS ALONE IN THE SOURCE, because
    # `c_container_is_emitted` reads `class="..."` out of this file and drops
    # any token carrying an f-string placeholder. Written
    # `class="send{' shot' if ... }"` the one token is `send{'`, which is
    # dropped whole, so the check reported that nothing on this site emits
    # `.send` — correctly, about a string it could not parse. A class the
    # instrument cannot see is a class the crop-box declaration cannot name.
    _shot = "shot" if sendshot else ""
    ahead = f"""
  <div class="send {_shot}">{sendshot}
    <div class="sendsay">
      <h2 class="mega">Where will the <br>road take you?</h2>
      <p class="lede">Take one as written, or open it in the Planner and bend
      it to the time you actually have. Every stop above is a place in the
      Atlas, and every one of them has a page.</p>
      <p class="keepgo">{golink('/plan', 'Build your own route')}
      {golink('/map', 'See them all on the map')}</p>
    </div>
  </div>"""

    PLATES = [("road gal", "The road", road, "the-road"),
              ("jindex gal quiet", "The seventeen", seventeen, "the-routes"),
              ("creed pine", "Why journey", creed, "why-journey"),
              ("feat gal", "The featured route", featured, "featured"),
              ("rhythm gal quiet", "The rhythm", rhythm, "the-rhythm"),
              ("jtales gal", "On these roads", tales, "on-these-roads"),
              ("pace gal quiet", "The pace", pace, "the-pace"),
              ("send", "The road ahead", ahead, "the-road-ahead")]
    body = (crumbs([("Europe", "/discover"), ("Journeys", None)])
            + constel_defs()
            + plate_sequence(PLATES))

    return "/journeys/index.html", page(
        "Journeys", body, path="/journeys", area="journeys", hero=True,
        accent="movement",
        description="Curated multi-country routes across Europe — Arctic to Baltic, Atlantic to Mediterranean, the Alpine grand tour and more.",
    )


def journey_page(data, j):
    idx = data["cities"]
    legs = []
    day = 1
    prev = None
    # THE SHAPE OF A JOURNEY IS THE LENGTHS OF ITS LEGS, and the page stated
    # them 104 times in prose and never once showed them. Measured across the
    # seventeen journeys: legs run 22 km to 2,531 km, and within a single
    # journey the longest is between 1.6x and 20.5x the shortest — the
    # Carpathian Arc is a 22 km hop and a 443 km haul in the same list, and
    # both rows were the same height, so the trip that is three short days and
    # one long one looked exactly like the trip that is six even ones.
    #
    # Drawn as a bar per leg on ONE scale within the journey — the longest leg
    # is full width — because a scale shared between journeys would make every
    # Alpine leg a stub next to an Arctic one and say nothing about either.
    # `.w0`-`.w100` are the utility classes the Europe Experience Score
    # already uses; a `style` attribute would force `style-src` open on all
    # 1,033 pages, which is the reason there is not one anywhere.
    hops = []
    _p = None
    for leg in j["legs"]:
        t_ = idx[leg["city"]]["city"]
        if _p is not None:
            hops.append(haversine(_p, t_))
        _p = t_
    longest = max(hops) if hops else 0.0
    for leg in j["legs"]:
        n = idx[leg["city"]]
        t, r, c = n["city"], n["region"], n["country"]
        hop = ""
        if prev is not None:
            km = haversine(prev, t)
            pct = int(round(km / longest * 100)) if longest else 0
            hop = (f'<p class="hop">↳ {esc(hop_note(km))} from '
                   f'{esc(prev["name"])} in a straight line</p>'
                   f'<span class="hopbar" aria-hidden="true">'
                   f'<span class="w{pct}"></span></span>')
        # The day numbers are derived at load now (see data.load), so the
        # page reads them rather than counting again. Two places counting the
        # same nights is how a journey page and an API disagree about which
        # day you are in Bergen.
        when = (f"Day {leg['day_number']}" if leg["nights"] == 1
                else f"Days {leg['day_number']}–{leg['day_last']}")
        # §2.7: which recorded places this stop is actually for.
        stops = "".join(
            f'<a href="{urls.place(c, r, t, pl)}">{esc(pl["name"])}</a>'
            for slug in leg.get("places", [])
            for pl in t.get("places", []) if pl["slug"] == slug
        )
        stoprow = (f'<p class="small">Here: {stops}</p>'
                   if stops else "")
        # The hop comes FIRST, above the stop it leads to, because it is how
        # you got there. It used to be appended after the `why`, which read
        # as a footnote belonging to the arriving town rather than as the
        # movement between two of them — on a page whose entire subject is
        # movement.
        nights = f"{leg['nights']} night" + ("" if leg["nights"] == 1 else "s")
        legs.append(
            f"""<li class="leg">
            <div class="leg-when"><span class="leg-no">{len(legs) + 1}</span>
              <span class="leg-day">{esc(when)}</span>
              <span class="leg-nights">{esc(nights)}</span></div>
            <div class="leg-what">{hop}
            <h3><a href="{urls.city(c, r, t)}">{esc(t['name'])}</a>
            <span class="leg-country">{esc(c['name'])}</span></h3>
            <p class="why">{esc(leg['why'])}</p>{stoprow}</div></li>"""
        )
        day = leg["day_last"] + 1
        prev = t
    countries = []
    for leg in j["legs"]:
        cn = idx[leg["city"]]["country"]["name"]
        if cn not in countries:
            countries.append(cn)
    total_km = sum(
        haversine(idx[j["legs"][i]["city"]]["city"], idx[j["legs"][i + 1]["city"]]["city"])
        for i in range(len(j["legs"]) - 1)
    )
    # Estimated budget, computed the same way the planner computes one, so a
    # journey page and a plan for the same route cannot disagree.
    style_i = {"low": 0, "moderate": 1, "high": 2}[j["budget"]]
    stay = 0
    for leg in j["legs"]:
        band = idx[leg["city"]]["country"]["daily_eur"]
        rate = band[0] + (band[1] - band[0]) * (style_i / 2)
        stay += leg["nights"] * rate
    transport_eur = 0
    for i in range(len(j["legs"]) - 1):
        km = haversine(idx[j["legs"][i]["city"]]["city"], idx[j["legs"][i + 1]["city"]]["city"])
        transport_eur += max(18, km * (0.11 if km < 400 else 0.09))
    est = int(round((stay + transport_eur) * 1.12 / 10) * 10)

    facts = factlist([
        ("Length", f"{j['days']} days"),
        ("From / to", f'<a href="{urls.city_by_id(idx, j["start"])}">{esc(idx[j["start"]]["city"]["name"])}</a> → '
                     f'<a href="{urls.city_by_id(idx, j["end"])}">{esc(idx[j["end"]]["city"]["name"])}</a>'),
        ("Countries", esc(" → ".join(countries))),
        ("Straight-line distance", f"{total_km:,} km, stop to stop"),
        ("Difficulty", esc(j["difficulty"])),
        ("Transport", esc(", ".join(j["transport"]))),
        ("Accommodation", esc(j["accommodation"])),
        ("Budget shape", esc(j["budget"])),
        ("Curated by", esc(j["creator"])),
        ("Estimated cost", f"about €{est:,} per person"),
        ("Months that work", esc(months_line(data, j["months"]))),
    ])
    packlist = "".join(f"<li>{esc(x)}</li>" for x in j["pack"])
    kinds_map = data["taxonomy"]["experience_kinds"]
    jexp_items = [
        (idx[l["city"]], e)
        for l in j["legs"] for e in idx[l["city"]]["city"].get("experiences", [])
    ][:10]
    jexps = "".join(
        f"""<a class="row" href="{urls.city(n['country'], n['region'], n['city'])}#things-to-do">
        <div><h3>{esc(e['name'])}</h3><p class="rowsub">{esc(e['summary'])}</p></div>
        <p class="rowmeta">{esc(n['city']['name'])} · {esc(kinds_map[e['kind']])}</p></a>"""
        for n, e in jexp_items
    )
    seen_food, jfood = set(), ""
    for l in j["legs"]:
        cc = idx[l["city"]]["country"]
        if cc["slug"] in seen_food:
            continue
        seen_food.add(cc["slug"])
        jfood += f"<li><strong>{esc(cc['name'])}</strong> — {esc(cc['food'][0])}</li>"
    photoband = pageband(data, f"journey:{j['slug']}")
    # A JOURNEY IS A SEQUENCE AND THE STOPS ARE THE PICTURES. This family
    # already draws the one thing an abstract plate never could — the route
    # — and the thing it could not show is what the stops LOOK like, in
    # order. `destination-hero@<target>` is declared for every one of them,
    # so the strip is the journey's own legs and nothing is invented.
    jstrip_items = []
    for _leg in j["legs"]:
        _n = idx.get(_leg["city"])
        if not _n:
            continue
        _t, _r, _c = _n["city"], _n["region"], _n["country"]
        jstrip_items.append({
            "key": f"city:{_c['slug']}/{_r['slug']}/{_t['slug']}",
            "alt": _t["name"], "label": _t["name"],
            "href": urls.city(_c, _r, _t)})
    _jshots = ed_strip(data.get("images"), jstrip_items, limit=10)
    jbleed = ed_bleed(data.get("images"), f"journey:{j['slug']}",
                      alt=j["name"], caption=j["name"], shape="tall")
    jstrip = (f'<section class="ed-section">'
              + ed_section_head("The route",
                                "What the journey passes through",
                                f"{n_of(len(j['legs']), 'stop')}, in order.")
              + _jshots + "</section>") if _jshots else ""
    # THE ONE THING THAT MAKES A JOURNEY A JOURNEY WAS NOT IN ITS HERO.
    #
    # /journeys was rebuilt from a grid of four abstract plates into rows
    # carrying each route, on the finding that "the ordered sequence of
    # places is the one thing that makes a journey a journey, and it was the
    # only thing not on the page". The DETAIL page then opened on 480 pixels
    # of flat cobalt with a name, a strapline and a meta line in the top
    # half — the same omission, on the page the index links to, with 250
    # pixels of empty blue under it.
    #
    # It is the index's own drawing, framed on this journey's own extent, so
    # the row a reader clicked and the hero they land on are the same
    # picture. Drawn in the hero's own ink rather than in the atlas palette:
    # this is a line on a field, not a map on paper, and `constellation`
    # takes the ground it is given.
    _heroroute = constellation(
        [project(data["cities"][l["city"]]["city"]["lat"],
                 data["cities"][l["city"]]["city"]["lon"])
         for l in j["legs"] if l["city"] in data["cities"]],
        route=True, frame=True, cut=True, aspect=1.35, mark=7, term=11,
        extra=" constel-onfield")
    body = f"""
{crumbs([("Europe", "/discover"), ("Journeys", "/journeys"), (j["name"], None)])}
{photoband}
{constel_defs()}
<section class="ed-journey-hero">
  <div class="ed-journey-hero-inner">
    <div class="ed-journey-say">
      <p class="ed-eyebrow">Journey</p>
      <h1>{esc(j['name'])}</h1>
      <p class="ed-intro">{esc(j['strapline'])}</p>
      <p class="ed-journey-facts">{n_of(j['days'], 'day')} · {n_of(len(j['legs']), 'stop')} · {n_of(len(countries), 'country')} · {total_km:,} km in a straight line</p>
    </div>
    <div class="ed-journey-line">{_heroroute}</div>
  </div>
</section>
{jbleed}
{jstrip}
<div class="headmeta ed-section">{chips(j["interests"], data["interests"])}</div>

<div class="routewrap">{routemap(data, j)}</div>

<div class="split mt7">
  <div>
    <p class="lede">{esc(j['summary'])}</p>
    <h2 id="the-route">The route, in order</h2>
    <p class="whyall"><span>Every hop</span> is a straight-line distance
    between two coordinates. This atlas holds no road and no rail geometry,
    so that number is a floor on the leg and never the leg — Chamonix to
    Zermatt is 69&nbsp;km here and about 170 on the ground, round a mountain
    range. It is here for the scale of the thing, not for planning a day.</p>
    <ol class="legs route">{''.join(legs)}</ol>
    <!-- A SECTION CALLED "The shape of it" HELD A TABLE OF FACTS. The shape
         of a journey is the lengths of its legs, and that is now drawn on
         the legs themselves; what is here is the record, so it says so.
         A heading that promises a shape and delivers a list is the same
         failure as an index that states the wrong count. -->
    <h2 class="mt7">The record</h2>
    {facts}

    <h2 class="mt7">Experiences along the way</h2>
    {f'<div class="rows">{jexps}</div>' if jexps else empty_state(
      "No experiences are recorded in the stops on this route.",
      "Experiences are written per destination, not per journey, so this "
      "list fills as the towns along the way get written up. It is a gap in "
      "the writing rather than a quiet stretch of Europe.")}

    <h2 class="mt7">What you will be eating</h2>
    <ul class="stack">{jfood}</ul>

    <h2 class="mt7">What to pack</h2>
    <ul class="stack">{packlist}</ul>

    <h2 class="mt7">What this estimate covers</h2>
    <p>About €{est:,} per person: {j['days'] - 1} nights at the {esc(j['budget'])} daily band for
    each country on the route, plus a distance-based transport figure between stops, plus 12%.
    It excludes getting to the start and home from the end, and it is planning arithmetic from
    published bands rather than a quote. <a href="/sources">How these numbers are made →</a></p>
  </div>
  <aside class="rail">
    <h2 class="mini">Make it yours</h2>
    <p>Fewer days than this? The Planner will keep the stops that match what you said you
    care about and drop the rest, rather than shortening every night.</p>
    <p><a class="btn" href="/plan#journey={esc(j['slug'])}">Open in the Planner</a></p>
    <p><button class="btn ghost" type="button" data-save="journey:{esc(j['slug'])}" data-kind="Journey"
       data-label="{esc(j['name'])}" data-url="{urls.journey(j)}">Save to My Europe</button></p>
  </aside>
</div>
{ad_slot(urls.journey(j))}
"""
    legs_ld = []
    for leg in j["legs"]:
        n = data["cities"][leg["city"]]
        legs_ld.append(ld_within("TouristDestination", n["city"]["name"],
                                 urls.city(n["country"], n["region"], n["city"])))
    return f"/journeys/{j['slug']}/index.html", page(
        j["name"], body, path=urls.journey(j), area="journeys",
        accent="movement",
        description=j["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
        og=("journey:" + j["slug"], motif_for(j["interests"]),
            f"{j['name']} — {j['strapline']}"),
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Journeys", "/journeys"),
                           (j["name"], urls.journey(j))]),
            # TouristTrip, with the stops as its itinerary. No offers and no
            # price: the estimate is planning arithmetic from published daily
            # bands, not a quote, and serialising it as an offer would turn a
            # caveat into a machine-readable commitment.
            {"@context": "https://schema.org", "@type": "TouristTrip",
             "name": j["name"], "url": ORIGIN + urls.journey(j),
             "description": j["summary"],
             "touristType": [data["interests"][i]["name"] for i in j["interests"]
                             if i in data["interests"]],
             "itinerary": {"@type": "ItemList",
                           "numberOfItems": len(legs_ld),
                           "itemListElement": [
                               {"@type": "ListItem", "position": i, "item": leg}
                               for i, leg in enumerate(legs_ld, start=1)]}},
        ],
    )


# ── planner ───────────────────────────────────────────────────────────

def planner_api(data):
    """The compact index the browser plans against. Advisory countries are
    excluded here rather than in the UI, so no client bug can route into one."""
    # A LEG CARRIES ITS PLACE'S OWN PHOTOGRAPH WHERE THE REGISTER HOLDS ONE,
    # AND THE STOPS ARE NOT KNOWN AT BUILD TIME. `planner.js` chooses them in
    # the reader's browser from their own sentence, so a build-time set of
    # named stop pictures would be a FAKE RESULT — the fault `data/motions.json`
    # is validated against one family over, where a curated list wearing the
    # clothes of a query looks identical on the day it ships.
    #
    # What is honest is the URL travelling with the destination: the register
    # holds a `city:` photograph for 63 of the 313 the planner can route
    # through, so a fifth of legs carry a picture and four fifths carry none,
    # which is the declared-slot honesty this site already practises. NEVER a
    # generated plate — the plate system is exclusively the social-card
    # language now, and every `.card-art` on this site is a map.
    #
    # `photo_href` TAKES A REGISTER KEY AND NEVER A URL, which is what keeps
    # this from becoming a second way into the library with none of the
    # licence gate behind it, and an unknown key returns "" so the row simply
    # has no `shot`. 640 rather than the ladder's widest: a leg tile renders
    # about 320 across, and this is a single `src` with no negotiation.
    images = data.get("images") or {}
    cities = []
    for cid, n in sorted(data["cities"].items()):
        c, r, t = n["country"], n["region"], n["city"]
        if c.get("advisory"):
            continue
        disc, why = discoverability(
            c, r, t,
            journeys_through=len(data["back"].get(cid, {}).get("journeys", [])),
            country_cities=sum(len(x["cities"]) for x in c["regions"]))
        cities.append({
            "id": cid,
            "name": t["name"],
            "country": c["name"],
            "countrySlug": c["slug"],
            "region": r["name"],
            "macro": c["macro_slug"],
            "lat": t["lat"], "lon": t["lon"],
            # PROJECTED HERE, NOT IN THE BROWSER. The planner draws the route
            # it built, and the only honest place to put a destination on
            # this atlas's conformal conic is the function that draws every
            # other map on the site. map.js re-derives the projection from
            # its four angles because it re-frames continuously and cannot be
            # handed a fixed answer; the planner never moves its frame, so it
            # is handed the answer instead. A third implementation of the
            # projection is a third one that drifts.
            "x": round(project(t["lat"], t["lon"])[0], 1),
            "y": round(project(t["lat"], t["lon"])[1], 1),
            "interests": sorted(set(t["interests"]) | set(r["interests"])),
            "nights": t["nights"],
            "budget": c["budget"],
            "daily": c["daily_eur"],
            "peak": c["season"]["peak"],
            "shoulder": c["season"].get("shoulder", []),
            "url": urls.city(c, r, t),
            "why": t["summary"],
            "highlights": t["highlights"][:2],
            "exp": len(t.get("experiences", [])),
            # How far this place is from being the obvious choice, and which
            # terms of that score actually fired — so Discover Mode can say
            # WHY it recommended something instead of asserting that it did.
            # NOT "why": that key already holds the city summary, and
            # overwriting it silently emptied the description on every
            # planner leg and every Discover Mode row. Two fields, two names.
            "disc": disc, "discWhy": why,
            # What there is actually to do, for the day-by-day, and how much
            # of it we hold, for the content-quality term in the score.
            "todo": ([{"n": pl["name"], "k": "place", "u": urls.place(c, r, t, pl)}
                      for pl in t.get("places", [])[:4]]
                     + [{"n": e["name"], "k": e["kind"], "u": urls.city(c, r, t) + "#things-to-do"}
                        for e in t.get("experiences", [])[:3]]),
            "depth": len(t.get("places", [])) + len(t.get("experiences", [])) + len(t["highlights"]),
            "quiet": bool(t.get("quiet")),
            "checked": bool(c.get("checked")),
        })
        # ABSENT RATHER THAN NULL, because present-but-empty says "we have
        # this" and then does not — the rule `checks.py` already enforces on
        # JSON-LD. 250 of 313 rows carry no key at all.
        _shot = photo_href(images, "city:" + cid, 640)
        if _shot:
            _row = images["city:" + cid]
            cities[-1]["shot"] = _shot
            cities[-1]["shotAlt"] = _row.get("alt") or t["name"]
            # AND THE CREDIT TRAVELS WITH THE PICTURE, COMPOSED BY THE ONE
            # FUNCTION THAT KNOWS THE RULE. Pexels' terms, recorded verbatim
            # in the gate, require "a prominent link to Pexels on any page
            # showing a Pexels photo, and the photographer credited as
            # 'Photo by <name> on Pexels' linking to that photo's page" — and
            # `checks.py` cannot see an `<img>` a script writes at runtime,
            # so the guard that refuses an unregistered file on a published
            # page has no reach here at all. Composing the sentence in
            # JavaScript instead would be a second implementation of a
            # LICENCE obligation, which is the one place this repository has
            # already learned not to have one.
            cities[-1]["shotCredit"] = credit_html(_row)
    journeys = [
        {
            "slug": j["slug"], "name": j["name"], "days": j["days"],
            "legs": [{"id": l["city"], "nights": l["nights"]} for l in j["legs"]],
            "interests": j["interests"],
        }
        for j in data["journeys"]
    ]
    return "/api/atlas.json", {
        "generated": "build",
        # Every published document says what it is and under what terms. Three
        # of the five endpoints carried this and two did not, which nothing
        # caught, because a missing key in a document nobody validates is
        # invisible. There is a check for it now.
        "licence": API_LICENCE,
        "note": ("The planner index. Advisory countries are STRIPPED from this "
                 "document — it is a list of places to route through, and routing "
                 "somebody into one is the harm. /api/countries.json is the "
                 "description of the continent and keeps them, with the advisory."),
        "currencies": data["taxonomy"].get("currencies", {}),
        "interests": data["taxonomy"]["interests"],
        "months": data["taxonomy"]["months"],
        "monthNames": data["taxonomy"]["month_names"],
        "budgets": data["taxonomy"]["budgets"],
        "cities": cities,
        "journeys": journeys,
    }


# THE SIX WEIGHTS, DECLARED ONCE AND CHECKED AGAINST THE CODE THAT USES
# THEM. `assets/js/planner.js` implements the scoring; this page publishes
# it. Two implementations of one fact is a second chance to make its
# mistake — seven times in this repository, once over a file extension — so
# `checks.py` reads the weight block out of the script and asserts these are
# the same numbers. The percentages are also the `.wN` utility classes the
# bars take, which is why they are integers rather than fractions: a bar
# whose width is not the figure beside it is a finished-looking chart about
# nothing, which the year band already records.
# WHERE EACH SPENDING STYLE SITS IN A DESTINATION'S OWN RECORDED DAILY
# BAND. `planner.js` holds this as `STYLE_DAILY = {low: 0, moderate: .5,
# high: 1}` and it is the whole of what a style IS: the bottom, the middle
# or the top of the range this atlas already records for that place. The
# band published it as three sentences and no number, which made the one
# measurable thing about it invisible — so the figure is derived from the
# 313 planning destinations here and the POSITION is declared once, read by
# both, and asserted equal in `checks.py`. A second copy of 0.5 is a second
# chance for the page and the planner to disagree about what "comfortable"
# means, which is the dispatch cap's own lesson at a sixth of the stakes.
PLAN_STYLE_POS = {"low": 0.0, "moderate": 0.5, "high": 1.0}

PLAN_WEIGHTS = (
    ("Your interests", 30,
     "how many of the things you are travelling for it actually carries"),
    ("Things to do", 20,
     "whether it has experiences recorded against those interests, rather "
     "than a tag and nothing behind it"),
    ("The month you named", 15,
     "peak, shoulder or off \u2014 never zero, because nowhere here is "
     "closed"),
    ("Atlas connectivity", 10,
     "how reachable it is from the rest of the Atlas. Reachability, not "
     "step-free access, which we hold no data for"),
    ("Content quality", 20,
     "how much of the place this atlas has actually written. It carries "
     "the specification's popularity weight as well, because we hold no "
     "visitor numbers for anywhere"),
    ("Novelty", 5,
     "quiet places, and countries not already in your route"),
)


def planner_page(data):
    """Seven plates: the desk, the controls, the result, the engine, the
    spending styles, the refusals, the close.

    THE PAGE WAS A FORM AND THE INSTRUMENT SAID SO. `tools/opening.js` names
    three families that open with no picture at all and this was one of them —
    0% at 1280 and 0% at 390, on the page that is this product's own
    instrument and the one a reader arrives on having decided to travel.
    2,703 pixels at 1280: a 30px label, a sentence box, twelve fields,
    seventeen checkboxes and four hundred words of method.

    WHAT DID NOT CHANGE IS THE METHOD OR ITS POSITION. The weights are the
    ones `assets/js/planner.js` implements, verified against the code rather
    than against the page describing it, and they stay UNDER the tool: the
    comment this function used to carry says why, and the brief that asked
    for a two-column shell was asking for the arrangement this page already
    removed. What changed is that six numbers are drawn instead of listed.

    See `docs/plan-redesign.md` for the four collisions and the one
    measurement.
    """
    interests = "".join(
        f"""<label><input type="checkbox" name="interest" value="{esc(i['slug'])}">
        <span aria-hidden="true">{esc(i['icon'])}</span> {esc(i['name'])}</label>"""
        for i in data["taxonomy"]["interests"]
    )
    months = "".join(
        f'<option value="{esc(m)}">{esc(data["taxonomy"]["month_names"][m])}</option>'
        for m in data["taxonomy"]["months"]
    )
    cx = data["taxonomy"].get("currencies", {})
    curoptions = "".join(
        f'<option value="{esc(code)}"{" selected" if code == "EUR" else ""}>{esc(code)}</option>'
        for code in sorted(cx.get("rates", {}))
    )
    # AN OPTION IS A LABEL, AND ONE OF THESE WAS A SENTENCE.
    #
    # The option read `{name} — {note}`, and "Generous — Well-reviewed
    # hotels, restaurants that book out, flights and first-class rail where
    # it saves a day." is 118 characters. Measured in Chromium against the
    # box it closes into: it needs 810 pixels in a 325-pixel field at 1280
    # and a 304-pixel one at 390, so the reader who picks it is shown about
    # forty per cent of their own choice, cut mid-word, at every width. A
    # `<select>` clips without an ellipsis, so it does not even look like a
    # truncation — it looks like the label.
    budgets = "".join(
        f'<option value="{esc(b["slug"])}"{" selected" if b["slug"] == "moderate" else ""}>'
        f'{esc(b["name"])}</option>'
        for b in data["taxonomy"]["budgets"]
    )

    # ── 01 · THE DESK ────────────────────────────────────────────────
    #
    # THE MONUMENTALITY COMES FROM THE DRAWING, NOT FROM THE TYPE. The brief
    # opens on a 155-pixel headline over a map with the form below it, which
    # is the composition a measurement here already removed: the head pushed
    # this instrument to y=436, so half the first screen of a TOOL was a
    # magazine headline and four or five lines of prose. An instrument's
    # title is a label because the page IS the tool, and `checks.py`
    # requires exactly one head role. So the head keeps `instrument` and the
    # picture is what fills the screen: the control set into the continent.
    #
    # AND THE PICTURE IS THIS PAGE'S OWN, WHICH TOOK THREE TRIES TO GET
    # RIGHT. 313 dots on a continent is what /discover already draws, and
    # *an index opening that is a continent with a different number of dots
    # on it is not a different opening* — 319 against 313 is the same
    # picture. What only THIS page holds is the six destinations it REFUSES:
    # Ukraine, Belarus and Russia are stripped from the planning index at
    # build time, so the planner scores 313 of 319. That is the one map on
    # this site whose subject is an editorial position rather than a set of
    # places, it is the sentence this page already publishes — "route you
    # into a country under a travel advisory: those are excluded from the
    # planning index entirely" — and it is drawn rather than only written.
    planned, refused = [], []
    for cid, n in sorted(data["cities"].items()):
        x, y = project(n["city"]["lat"], n["city"]["lon"])
        (refused if n["country"].get("advisory") else planned).append(
            (x, y, cid, n))
    advnames = sorted({n["country"]["name"] for _x, _y, _c, n in refused})
    # AND THE GROUND BEYOND THE ATLAS IS NOT DRAWN HERE, WHICH IS A
    # MEASUREMENT RATHER THAN A PREFERENCE. `landmass` returns the context
    # land first — every landmass in a box that contains Europe, clipped to
    # that box — and it is a HERO device: *Europe is not an island*, and the
    # graphite it is drawn on absorbs its straight edges completely. /map and
    # /discover keep it for exactly that reason, and the same slab on the
    # same projection is invisible there: measured on /map's own pixels, the
    # dusk over 52°E is near-black and Iran and Iraq are gone.
    # This band is the one light drawing that shows the whole eastern cut
    # inside its own frame with open water beyond it, and `--atlas-far`
    # (#C3BFB2) is DARKER than the water (#DDE8E7) rather than lighter — so
    # the fragment came out as a warm slab with three straight edges sitting
    # in the sea south-east of Baku, probed and named as Iran and Iraq
    # clipped at 52°E. The wide fade hides it and takes the ground out from
    # under Baku and Tbilisi with it, which is the fault `dusk_reach` exists
    # to stop and is why every caller passes it. So the layer that has no
    # claim to make here is the one that goes: this drawing's subject is 313
    # destinations and the six it refuses, and nothing outside the atlas is
    # part of that sentence.
    _dctx, dland = geo.landmass(MAPPROJ, (0, 0, MAP_W, MAP_H))
    deskmap = (
        # A MAP DECLARES WHETHER IT IS AN ILLUSTRATION OR AN INSTRUMENT,
        # and `checks.py` asserts it on every one. This is an
        # `illustration`: it draws the planning population and the six it
        # refuses, and nothing on it is a link, a filter or a legend — the
        # instruments are /map and /discover, where a country is a door.
        # AND THE `atlas` CLASS IS PART OF THAT DECLARATION. An
        # illustration must carry it, because the skin is what the role
        # MEANS on this site — warm paper and Atlantic water rather than
        # land on a near-black ground — and `checks.py` refuses an
        # illustration without it. Every `.atlas` rule in the stylesheet is
        # qualified by `.minimap.arched`, so it paints nothing here and the
        # picture's palette arrives through the band's own token binding;
        # verified by byte-identical screenshots at 1280 and 390.
        f'<svg class="instrmap atlas" data-role="illustration" '
        f'viewBox="0 0 {MAP_W} {MAP_H}" aria-hidden="true" '
        # `meet` RATHER THAN `slice`, AND THE LETTERBOX IS INVISIBLE BY
        # CONSTRUCTION. A map figure paints no background and this band's
        # paper IS `--map-water`, so the bands `meet` leaves above and below
        # the drawing are the drawing's own ocean. `slice` would crop the
        # Caucasus and the Atlantic off a column narrower than the frame,
        # which is what a full-bleed ground was doing here in three tries.
        f'focusable="false" preserveAspectRatio="xMidYMid meet">'
        # AND THE LAND CARRIES AN ID, BECAUSE THE RESULT'S ROUTE FIGURE
        # CLONES IT. `constel_defs()` emits one thinned lod0 silhouette with
        # no frontiers, which is the right picture for a 132-pixel theme
        # glyph and a blank field for a 400-km inland route: measured on a
        # three-stop Vienna route, the figure was 736 pixels of flat stone
        # with a green zigzag on it and no coast, no frontier and nothing to
        # place it by. This page already ships the country rings — the desk
        # draws forty-eight of them — so the route figure clones THOSE and
        # gets every frontier for the cost of a `<use>`, which is the same
        # 27-byte trick the hero uses for its own boundaries.
        f'<g id="deskland">{dland}</g>'
        f'{cut_fade("desk", MAP_W, MAP_H, dusk_reach())}'
        + "".join(f'<circle class="pdot" cx="{x:.1f}" cy="{y:.1f}" r="3.4"/>'
                  for x, y, _c, _n in planned)
        + "".join(f'<circle class="pdot out" cx="{x:.1f}" cy="{y:.1f}" r="3.4"/>'
                  for x, y, _c, _n in refused)
        + "</svg>")

    desk = f"""
  <div class="deskwrap">
  <div class="deskform">
    <div class="pagehead instrument">
      <p class="kicker">The European Journey Planner</p>
      <h1>Twelve days, &euro;2,500, history and mountains.</h1>
      {head_extent([(len(planned), 'destinations scored'),
                    (len(data['countries']), 'countries'),
                    (len(data['journeys']), 'routes already built')])}
    </div>
    <form class="form ask" id="askform">
      <div class="field">
        <label for="ask">Say it in your own words</label>
        <textarea id="ask" name="ask" rows="2"
          placeholder="I have 12 days and &euro;2,500, starting in Lisbon, and I love history, mountains and food."></textarea>
      </div>
      <div class="hero-actions mt0">
        <button class="btn" type="submit">Read that and build it</button>
      </div>
      <p class="small mb0">The planner reads the whole Atlas, scores every
      destination against you, then builds a route that respects distance
      instead of teleporting between highlights. It is read by rules in your
      browser &mdash; not by a model, and not sent anywhere &mdash; and it
      shows you exactly what it understood, naming anything it could not take
      account of rather than quietly dropping it.</p>
    </form>
  </div>
  <figure class="deskart">{deskmap}
    <figcaption><span class="capwhat">Every destination the planner scores,
    at once. The {numword(len(refused))} it will not &mdash;
    {n_of(len(refused), "destination")} in {and_list(advnames)} &mdash;
    are drawn dark: a country under a travel advisory is stripped from the
    planning index at build time rather than hidden in the
    interface.</span> <span class="capsrc">{geo.sources_line(geo.load("europe-lod0.json"))}</span></figcaption>
  </figure>
  </div>"""

    # ── 02 · THE CONTROLS ────────────────────────────────────────────
    # THE FORM TAKES THE FULL MEASURE, which is the other half of the
    # decision that moved the method out of the rail. Twelve fields and
    # seventeen checkboxes squeezed into two thirds of the page to make room
    # for an essay is two things competing for one attention.
    controls = f"""
  <div class="sheettext">
    <h2 class="mega">Or tell it precisely.</h2>
    <p class="lede">The same planner, said in fields rather than in a
    sentence. Nothing here is required: every one of them has a default the
    Atlas can work from.</p>
  </div>
  <form class="form planctl" id="planner">
    <div class="form-row">
      <div class="field">
        <label for="days">Days</label>
        <input type="number" id="days" name="days" min="3" max="45" value="12" inputmode="numeric">
      </div>
      <div class="field">
        <label for="budget">Total budget (&euro;, per person)</label>
        <input type="number" id="budget" name="budget" min="200" step="50" value="2500" inputmode="numeric">
      </div>
      <div class="field">
        <label for="month">Travelling in</label>
        <select id="month" name="month">{months}</select>
      </div>
    </div>
    <div class="form-row">
      <div class="field">
        <label for="style">Spending style</label>
        <select id="style" name="style">{budgets}</select>
      </div>
      <div class="field">
        <label for="pace">Pace</label>
        <select id="pace" name="pace">
          <option value="slow">Slow &mdash; fewer places, longer stays</option>
          <option value="balanced" selected>Balanced</option>
          <option value="fast">Fast &mdash; see as much as possible</option>
        </select>
      </div>
      <div class="field">
        <label for="start">Start from</label>
        <select id="start" name="start"><option value="">Anywhere that fits</option></select>
      </div>
    </div>
    <div class="form-row">
      <div class="field">
        <label for="end">End near</label>
        <select id="end" name="end"><option value="">Wherever it gets to</option></select>
      </div>
      <div class="field">
        <label for="travellers">Travellers</label>
        <input type="number" id="travellers" name="travellers" min="1" max="12" value="1" inputmode="numeric">
      </div>
      <div class="field">
        <label for="accommodation">Accommodation</label>
        <select id="accommodation" name="accommodation">
          <option value="mixed" selected>Mixed &mdash; whatever suits the place</option>
          <option value="guesthouse">Guesthouses and small places</option>
          <option value="hotel">Hotels</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="field">
        <label for="transport">Getting between</label>
        <select id="transport" name="transport">
          <option value="any" selected>Whatever is quickest</option>
          <option value="rail">Rail and ferry, no flights</option>
        </select>
      </div>
      <div class="field">
        <label for="currency">Show costs in</label>
        <select id="currency" name="currency">{curoptions}</select>
      </div>
      <div class="field">
        <p class="fieldhead">Places you saved</p>
        <label class="inlinecheck"><input type="checkbox" id="saved" name="saved">
        Favour the ones in My Europe</label>
      </div>
    </div>
    <fieldset class="fieldset">
      <legend>What are you travelling for?</legend>
      <div class="checks">{interests}</div>
    </fieldset>
    <div class="hero-actions mt0">
      <button class="btn" type="submit">Build the itinerary</button>
      <button class="btn ghost" type="button" id="again">Give me a different one</button>
    </div>
  </form>"""

    # ── 03 · THE RESULT ──────────────────────────────────────────────
    # PRESENT-BUT-EMPTY SAYS "WE HAVE THIS" AND THEN DOES NOT, so the plate
    # states what will appear here rather than leaving a hole above the
    # method. /discover's response plate had the same problem and took the
    # same answer: at rest it says what it IS showing.
    result = """
  <div class="sheettext">
    <h2 class="mega">Your Europe, assembled.</h2>
    <p class="lede">The planner is not trying to find every highlight. It is
    trying to make one coherent route out of what you said matters.</p>
  </div>
  <div id="result" aria-live="polite"></div>
  <p class="note atrest" id="atrest">Nothing has been built yet. When you run
  it, this is where the route appears &mdash; the stops in order, the nights on
  each, the straight-line distance between them, what every choice was made
  for, and an estimate you can argue with. You can move a stop, change its
  nights, drop it or add one, and every number above recomputes from your
  version rather than from the planner&rsquo;s.</p>"""

    # ── 04 · THE ENGINE ──────────────────────────────────────────────
    #
    # THE WEIGHTS ARE DRAWN AND THEY ARE READ OUT OF ONE PLACE. Six numbers
    # in a bulleted list is the "block of explanatory text" the brief
    # objects to, and it is right: this is the page's whole claim to being
    # an instrument rather than a recommendation, and a claim states itself
    # better as a proportion than as a percentage sign.
    #
    # A CHART IS A CLAIM, so the bars are scaled by the series they are
    # labelled with and the figures are the ones `planner.js` implements.
    # The year band already records what happens otherwise: correct labels
    # over a drawing scaled from the wrong array still reads as a finished
    # chart.
    engine = f"""
  <div class="sheettext">
    <h2 class="mega">A published method, not a mysterious recommendation.</h2>
    <p class="lede">Every destination is scored out of one, on a weighting
    this page publishes and the planner in your browser implements. Distance
    then shapes the sequence.</p>
  </div>
  <dl class="weights">{"".join(
      f'<div class="wrow"><dt>{esc(name)}</dt>'
      f'<dd><span class="wbar w{pct}"></span><b>{pct}%</b></dd>'
      f'<p class="wsay">{esc(say)}</p></div>'
      for name, pct, say in PLAN_WEIGHTS)}</dl>
  <p class="small plannote">The specification this came from allocates 10% to
  popularity. We have no traffic and no licensed visitor data, so that term
  would be a number we invented wearing a percentage sign. Its weight moved
  to content quality, which is measurable. And &ldquo;accessibility&rdquo;
  there means <em>reachability</em> &mdash; we hold no step-free access data
  at all, and <a href="/accessibility">say so</a>.</p>
  <p class="small plannote">Then: distance penalises each next stop so the
  route stops wandering; three big cities in a row start to push the fourth
  choice towards the alternative; nights come from the range on each
  destination page; and anything above what your budget can afford per day is
  damped.</p>"""

    # ── 05 · SPENDING STYLE ──────────────────────────────────────────
    # AND THE FIGURE IS THE MEDIAN ACROSS THE PLANNING POPULATION, with the
    # spread beside it, because a median alone reads as a price. Derived
    # from the same `daily` field the planner costs a night from, on the
    # same 313 destinations the desk draws — never authored, and it moves
    # on the next build when a destination's band is edited.
    def _at(pos):
        # `daily_eur` IS THE FIELD AND IT IS ON THE COUNTRY, NOT THE CITY.
        # Two wrong readings in a row, and both raised rather than shipping
        # a number — `daily` is the name atlas.json publishes it under, and
        # a destination inherits its country's band, which is exactly what
        # `planner.js` reads back out of `city.daily`. So the median is over
        # the 313 DESTINATIONS through their countries' bands, which is the
        # population the planner actually costs a night from.
        v = sorted(round(c["country"]["daily_eur"][0]
                         + (c["country"]["daily_eur"][1]
                            - c["country"]["daily_eur"][0]) * pos)
                   for c in data["cities"].values()
                   if not c["country"].get("advisory")
                   and c["country"].get("daily_eur"))
        return v[len(v) // 2], v[0], v[-1]

    stylerows = "".join(
        '<div class="styleway"><p class="kicker">'
        + ("%02d / " % i) + esc(b["name"]).upper() + "</p>"
        + "<h3>" + esc(b["name"]) + "</h3>"
        + '<p class="styleat"><b>&euro;' + str(_at(PLAN_STYLE_POS[b["slug"]])[0])
        + "</b> a day, typically</p>"
        + '<p class="stylesay">' + esc(b["note"]) + "</p>"
        + '<p class="stylerange">'
        + ("the bottom of each place\u2019s own recorded band"
           if PLAN_STYLE_POS[b["slug"]] == 0.0
           else "the top of it" if PLAN_STYLE_POS[b["slug"]] == 1.0
           else "the middle of it")
        + " &mdash; &euro;" + str(_at(PLAN_STYLE_POS[b["slug"]])[1])
        + " to &euro;" + str(_at(PLAN_STYLE_POS[b["slug"]])[2])
        + " across the " + str(len(planned)) + "</p></div>"
        for i, b in enumerate(data["taxonomy"]["budgets"], 1))
    styles = f"""
  <div class="sheettext">
    <h2 class="mega">Choose your way of travelling.</h2>
    <p class="lede">Three editorial planning assumptions, from the
    Atlas&rsquo;s own taxonomy. A style is a <em>position</em> in the daily
    band this atlas already records for each place &mdash; which is why the figures
    below are medians with their spread beside them rather than prices. They
    are not hotel quotes and nothing here books anything.</p>
  </div>
  <div class="styles">{stylerows}</div>"""

    # ── 06 · WHAT IT WILL NOT DO ─────────────────────────────────────
    # THE REFUSALS ARE THIS PAGE'S INSTITUTIONAL VOICE AND THEY ARE KEPT
    # VERBATIM. The brief agrees with every one of them, which is worth
    # noting: it asked for no fake booking functionality and this page has
    # published the sentence since before the brief arrived.
    # AND A BAND WHOSE SUBJECT IS A LIST OF REFUSALS HAD ONE SENTENCE IN
    # IT. 787 pixels for a headline, a lede and a note in the left half —
    # the hole this page had on four bands — on the band that carries the
    # product's whole position. Six refusals, and **not one is written here
    # for the first place**: each is already published on this site and the
    # row says where, so the band is a contents page for a promise rather
    # than a new claim. A refusal nobody can check is a slogan.
    refusals = [
        ("It will not book anything",
         "There is no basket, no payment and no availability anywhere in this "
         "product. The page that says what EuropeDoor is publishes the "
         "sentence \u201cNot an OTA\u201d and means it.", "/about"),
        ("It will not price a hotel",
         "This atlas holds no rooms, no rates and no availability. Where a "
         "destination page hands you to a provider it is a referral and says "
         "so, in both of its two states.", "/for-businesses"),
        ("It will not route you into an advisory country",
         "Ukraine, Russia and Belarus keep a page carrying the warning and "
         "are stripped from the planning index at build time rather than "
         "hidden in the interface.", "/help"),
        ("It will not tell you the weather",
         "No weather data and no forecast for anywhere. A \u201crainy day "
         "plan\u201d built from nothing would be a guess with a confident "
         "face on it.", None),
        ("It will not promise step-free access",
         "The connectivity term in the weighting above means "
         "<em>reachability</em>. We hold no step-free access data at all.",
         "/accessibility"),
        ("It will not give you a road distance",
         "Every distance here is a straight line between two coordinates. "
         "There is no road and no rail geometry in this repository, so the "
         "time is \u201cabout\u201d and the error runs in both directions.",
         "/method"),
    ]
    refrows = "".join(
        '<div class="rrow"><dt>' + esc(name) + "</dt><dd>" + why
        + ("" if not href
           else ' <a href="' + href + '">Where we say so</a>')
        + "</dd></div>"
        for name, why, href in refusals)
    wont = f"""
  <div class="sheettext">
    <h2 class="mega">What it will not do.</h2>
    <p class="lede">Six of them, and every one is a sourcing position rather
    than a feature nobody has built yet. Each says where this site publishes
    it, because a refusal nobody can check is a slogan.</p>
  </div>
  <dl class="refusals">{refrows}</dl>
  <p class="note plannote">Estimates are editorial, not quotes. Check <a href="/sources">sources
  and corrections</a>. The route is drawn from the coordinates in the Atlas
  rather than from any road or rail geometry, on the same Lambert conformal
  conic as every other map here &mdash; standard parallels {geo.LCC_P1:.0f}°N
  and {geo.LCC_P2:.0f}°N, origin {geo.LCC_LAT0:.0f}°N, central
  meridian {geo.LCC_LON0:.0f}°E.</p>"""

    # ── 07 · COMPOSE THE JOURNEY ─────────────────────────────────────
    # A CLASS NAME ALREADY IN THE STYLESHEET IS A RULE YOU INHERIT
    # SILENTLY, AND THE SECOND NAME WAS TAKEN TOO.
    # The first version of this band borrowed `.sendsay`, which is
    # /journeys' own closing composition — a centred statement over a
    # PHOTOGRAPH behind a 72% graphite scrim — and its rule is
    # `.sendsay .mega, .sendsay .lede { color: var(--bone) }`. On a white
    # wall that is bone on white, about 1.1:1: the last thing this page says
    # was present, placed, centred and unreadable. This repository recorded
    # exactly that about `.doorgo` two commits ago and it happened again
    # here. The band owns its own name and declares no colour at all, so the
    # room's ink is whatever the room binds. And `.closesay` — the obvious
    # second choice — is ALSO already declared, by the closing band on the
    # homepage and /discover, at `max-width: 32rem`: the statement came out
    # 512 pixels wide inside a 1,152-pixel band, centred inside its own cap
    # and therefore off-centre in the room. Two collisions in one band, from
    # the two most obvious names, with nothing in any suite that could see
    # either. Grep the stylesheet before naming a composition.
    close = f"""
  <div class="composesay">
    <h2 class="mega">Do not just choose places. <br>Compose the journey.</h2>
    <p class="lede">Start with what you have. Say what you like. The Atlas
    draws the line between them.</p>
    <p class="keepgo">{golink('#askform', 'Back to the desk')}
    {golink('/journeys', 'Or take one already built')}</p>
  </div>"""

    PLATES = [("desk paper", "The desk", desk, "the-desk"),
              ("planctls gal", "The controls", controls, "the-controls"),
              ("planres gal quiet", "The result", result, "the-result"),
              ("engine pine", "The engine", engine, "the-engine"),
              ("styles gal", "Spending style", styles, "spending-style"),
              ("wont gal quiet", "What it will not do", wont, "what-it-wont-do"),
              ("close gal", "Compose the journey", close, "compose")]
    body = (crumbs([("Europe", "/discover"), ("Plan", None)])
            + constel_defs()
            + jsondata("europedoor-glyphview-cases",
                       [f"{len(pts)}:" + glyph_view(pts) for pts in GLYPHVIEW_CASES])
            + plate_sequence(PLATES))

    return "/plan/index.html", page(
        "Plan a journey", body, path="/plan", area="plan", hero=True,
        description="Tell EuropeDoor your days, budget and interests and it builds a European itinerary with real distances, real night counts and a cost estimate.",
        scripts=["/assets/js/planner.js"],
        # INTELLIGENCE — the planner: journey construction
        world="intelligence"
    )

def stay_section(data, c, r, t, cid):
    """Where to stay, as an EuropeDoor answer rather than an OTA one.

    THE FIRST QUESTION WAS NOT "WHICH PROVIDER" BUT "WHAT DO WE ACTUALLY
    KNOW". An accommodation section that resembles a booking site is easy and
    is the wrong product: this atlas holds no rooms, no prices, no
    availability and no ratings, so any card grid it drew would be somebody
    else's inventory pasted under our masthead, and a reader would read it as
    an advertisement inserted into an article. What it does hold, and what no
    booking site has, is a judgement about the PLACE — how the ground here
    constrains where a bed can sensibly be, and when the beds go.

    So the section is two authored readings over one derived measurement, and
    one link out. In order:

      · the base — an authored classification ("the valley floor"), which is
        the job, over the relief figures for this destination, which are a
        derived measurement and carry their radius from the file that holds
        them. Chamonix reads a 2,752 m crest and a 1,798 m spread within
        40 km, and that is WHY the town is the only answer: the valley is the
        only flat ground at the bottom of the lifts. Paris would read 150 and
        102 and this paragraph would have nothing to say, which is correct —
        it is omitted where there is no relief rather than filled with a
        sentence about nothing.
      · the lead time — the same peak and shoulder months the pace note above
        prints, asked a different question. That note answers WHEN TO COME
        and this one answers WHEN TO BOOK, and the second is not derivable
        from the first by a reader who has not booked an Alpine August.
      · the action, once, to the provider's own search, with the provider
        named as the party that holds the rooms and takes the payment.

    THE HEADING IS DERIVED FROM WHAT THE PLACE IS. "Hotels in Chamonix" is
    generic listing language and also the wrong promise — what is on offer is
    a base, and a base means something different in a valley, on an island
    and in a capital. `staylib.heading` reads the same `city_type`
    classification and the same relief predicate the rest of the site uses,
    so Chamonix gets "Sleep below the peaks" and Naxos would get "Stay on the
    island" without anybody authoring either. The lede leads with the PROMISE
    and the boundary comes second: the first version opened on what this
    atlas does not hold, which is honest, defensive and the wrong first
    sentence for a reader who has just decided to come.

    NO SECOND MAP. `docs/signature-moments.md` asks question 2 before an
    aperture is added to a family, and the answer here is that this page
    already draws one — Chamonix with Annecy, Zermatt and Lauterbrunnen
    around it — and a second arch four screens down would be the signature as
    wallpaper. Accommodation AS geography is the right long idea and it needs
    accommodation coordinates, which arrive with an inventory API and not
    before; inventing them would be the region-hull failure with beds.

    NO PHOTOGRAPH, AND THAT IS THE REAL GAP. This is the one family where a
    photograph does work the type cannot: you choose where to sleep partly on
    what the place looks like at seven in the morning. The register holds
    none, an illustration drawn from a hash would be a picture of nowhere
    standing in for a room, and so there is none. The no-image state is not a
    fallback here, it is the shipped state.

    Everything commercial is read off `data/stay.json`: which providers, in
    what order, whether we hold a credential, and whether any of them can
    supply inventory. Adding Expedia is one field in that file.
    """
    row = staylib.context(cid)
    provs = staylib.providers()
    if not row or not provs:
        return section("Accommodation & restaurants", STAY_NOTE, id="stay")

    # The relief paragraph, only where the ground was measured to have
    # something to say. `draws_relief` is the same predicate that decides
    # whether this page's map carries bands, so the sentence and the drawing
    # can never disagree about whether this is mountain country.
    measure = cartography.relief_of(cid)
    mountainous = cartography.draws_relief(measure)
    ground = ""
    if mountainous:
        km = cartography.relief_radius_km()
        ground = (f'<p class="sourcenote">Within {km:.0f} km of here the ground '
                  f'spreads {measure[0]:,.0f} m and crests at {measure[1]:,.0f} m, '
                  f'measured from the same elevation model the map above is '
                  f'drawn from.</p>')

    peak = months_line(data, c["season"]["peak"])
    shoulder = months_line(data, c["season"].get("shoulder", []))
    # "PEAK HERE" WAS A COUNTRY'S FIGURE WEARING A DESTINATION'S CLOTHES.
    # These months belong to the country and are stated once on its own page;
    # an Alpine valley's season is not Italy's season, and a line that says
    # "here" while printing a national figure is the kind of quiet untruth
    # that survives because both halves are true separately. Named for what
    # it is, and linked to the page that argues it.
    when = (f'{esc(row["when"])}</p><p class="sourcenote">Peak in '
            f'<a href="{urls.country(c)}#when">{esc(c["name"])}</a> is '
            f'{esc(peak)}; the shoulder is {esc(shoulder)}.</p>'
            if shoulder else f'{esc(row["when"])}</p>')

    # THE ACTION. One primary, from the first enabled provider. The button
    # says what it does — it opens a search somewhere else — because "Book
    # now" on a page that cannot book is the lie `stickycta` already refuses
    # in its own docstring.
    #
    # No card above it, and the seam for one is `staylib.inventory`, which
    # returns nothing under a link-only affiliate mechanism. A card with a
    # property, a rating and a nightly rate is the right shape the day a
    # provider hands those over with its own figure attached; drawing an
    # empty one now would be present-but-empty, which says "we have this"
    # and then does not.
    first, rest = provs[0], provs[1:]
    compare = ""
    if staylib.compare(t["name"], c["name"]):
        compare = ('<p class="stayalso"><span class="staylabel">Compare places to '
                   'stay</span> '
                   + " · ".join(
                       f'<a href="{esc(staylib.deep_link(p, t["name"], c["name"]))}"'
                       f' rel="{staylib.rel(p)}" target="_blank">{esc(p["name"])}</a>'
                       for p in provs)
                   + "</p>")

    return section(
        staylib.heading(row, t, mountainous),
        f"""<div class="stay">
  <div class="stayreads">
    <div class="stayread">
      <h3 class="mini">{esc(row["base"])}</h3>
      <p>{esc(row["where"])}</p>
      {ground}
    </div>
    <div class="stayread">
      <h3 class="mini">{esc(row["lead"])}</h3>
      <p>{when}
    </div>
  </div>
  <div class="staygo">
    <div class="staygo-do">
      <p><a class="btn" href="{esc(staylib.deep_link(first, t["name"], c["name"]))}" rel="{staylib.rel(first)}" target="_blank">Search places to stay in {esc(t["name"])}</a></p>
      {compare}
    </div>
    <div class="staygo-say">
      <p class="staywho">Opens {esc(first["name"])}\u2019s own search for {esc(t["name"])}, in a new tab. They hold the rooms, the prices and the availability, and the booking and the payment are with them. EuropeDoor holds none of the three and publishes no ratings for anywhere in Europe.</p>
      <p class="small staydisc">{esc(staylib.disclosure(first))}</p>
    </div>
  </div>
  <p class="sourcenote">Restaurants are still not listed, here or anywhere: that is a business listing rather than an editorial entry and it needs an operator who claims it and a verification tier. <a href="/for-businesses">How listings will work</a>.</p>
</div>""",
        id="stay",
        # THE LEDE PROMISED THE GROUND ON A PAGE WHERE THE GROUND SAYS
        # NOTHING. It was one fixed sentence — "where the ground puts you and
        # when the beds go" — and on Vienna and Naxos the relief paragraph is
        # correctly omitted, so the section opened by promising a reading it
        # then did not carry. That is the removing-a-claim failure: the claim
        # went and the surface pointing at it stayed. Only rendering the
        # second and third destinations found it, because the exemplar is the
        # one case where the sentence happens to be true.
        lede=f"{row['promise']} What this atlas can tell you about sleeping in "
             f"{t['name']} is "
             + ("where the ground puts you" if mountainous else "where to base yourself")
             + " and when the beds go. It holds no hotels, and the booking "
               "happens somewhere else.",
    )


STAY_NOTE = """<div class="note">
  <p>EuropeDoor lists neither, yet. Both are business listings rather than editorial entries:
  they need an operator who claims them, a verification tier and a way to keep prices current,
  and all three are blocked on the same thing as everything else commercial here.
  <a href="/for-businesses">How listings will work</a> ·
  <a href="/how-it-works">what is built and what is blocked</a>.</p>
  <p class="small">Publishing a scraped hotel list would be quick and would be the first
  unverified thing on this site. That is the trade being refused.</p>
</div>"""


def _declutter(items, w, h):
    """Greedy label placement: keep a label only if its box is still free.

    Norway has 25 destinations in six regions and the first version drew all
    31 labels at their exact positions, so "Østlandet & the East" sat across
    "Fjord Norway" sat across four city names and the map was a smear. The
    fix is the oldest one in cartography: decide an order of importance and
    drop what does not fit.

    `items` are (priority, x, y, width, height, svg) with priority 0 first.
    Anything that collides with something already placed is dropped, not
    moved — nudging a label away from its own dot is how a map starts lying
    about where things are.
    """
    placed, out = [], []
    for pri, x, y, bw, bh, svg in sorted(items, key=lambda i: i[0]):
        b = (x, y - bh, x + bw, y)
        if b[0] < -20 or b[2] > w + 20 or b[1] < 0 or b[3] > h:
            continue
        if any(not (b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3])
               for o in placed):
            continue
        placed.append(b)
        # The box travels with the label: the phone pass re-tests it at the
        # size a narrow screen draws it, and can only do that if it knows
        # where the label ended up.
        out.append((svg, b[0], b[1], b[2] - b[0], b[3] - b[1]))
    return out


def countrymap(data, c):
    """The country, drawn, with its regions and every destination on it.

    This is the middle rung of Europe -> country -> region -> destination, and
    before there was geometry it was the rung that did not exist: a country
    page could list its regions but could not show you where they were.

    Regions are drawn as their destinations grouped and labelled, not as
    boundaries. We hold which region a destination belongs to; we do not hold
    region geometry, because the dataset that has it is blocked on a licensing
    question (docs/data-licenses/eurostat-gisco-nuts.md). A hull drawn round
    Bergen and Ålesund and labelled Vestland would look like an answer and be
    a guess, and a map that guesses once can be trusted about nothing.
    """
    doc = geo.country(c["slug"])
    allpts = [(r, t) for r in c["regions"] for t in r["cities"]]
    if not doc or not allpts:
        return ""
    w, h = 900, 560

    # The frame is the country's own geometry, and nothing else. An earlier
    # version widened it to hold every destination, which for Norway means
    # Longyearbyen at 78°N — 700 km beyond the top of the drawn coastline —
    # and produced a map that was two-fifths empty sea with Norway squeezed
    # into a corner. One outlier should cost one marker, not the whole frame.
    #
    # And the same rule one level down: the frame is the country's PRINCIPAL
    # landmass, because `bbox` is the extent of every ring and for Portugal
    # that reaches the Azores — this map was nine-tenths empty Atlantic with
    # all six destinations in one corner of it. geo.principal_frame.
    if doc.get("bbox"):
        bbox = geo.principal_frame(doc, c["slug"])[0] or list(doc["bbox"])
    else:
        # Vatican City has no polygon at any scale. Frame it on its own
        # destinations so every country page has the same shape.
        lons = [t["lon"] for _r, t in allpts]
        lats = [t["lat"] for _r, t in allpts]
        bbox = [min(lons) - 0.25, min(lats) - 0.2, max(lons) + 0.25, max(lats) + 0.2]
    proj = geo.Projection(bbox, w, h, pad=0.05)
    ctx, land = geo.landmass(proj, (0, 0, w, h), doc=doc, highlight=c["slug"])

    # When two destination labels collide the one we have written more about
    # wins, so a country map keeps Bergen and drops Geiranger rather than the
    # other way round because of where the alphabet put them.
    depth = {}
    for _r, t in allpts:
        depth[id(t)] = (len(t.get("places", [])) * 2 + len(t.get("experiences", []))
                        + len(t["highlights"]))
    deepest = max(depth.values()) or 1

    dots, ties, labels, offframe = [], [], [], []
    hitr = hit_radius(
        [proj.xy(t["lat"], t["lon"]) for r in c["regions"] for t in r["cities"]
         if -8 <= proj.xy(t["lat"], t["lon"])[0] <= w + 8
         and -8 <= proj.xy(t["lat"], t["lon"])[1] <= h + 8],
        w, cap=34.0 * w / 1000.0)
    for r in c["regions"]:
        rp = []
        for t in r["cities"]:
            x, y = proj.xy(t["lat"], t["lon"])
            if not (-8 <= x <= w + 8 and -8 <= y <= h + 8):
                offframe.append((r, t))
                continue
            rp.append((x, y))
            dots.append(
                f'<a class="minidot" href="{urls.city(c, r, t)}">'
                f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="{hitr:.1f}"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4"/>'
                f'<title>{esc(t["name"])} — {esc(r["name"])}</title></a>'
            )
            # The country map already sorts by depth and drops collisions;
            # it was choosing the position itself and only ever offering
            # one, to the right of the dot. It now asks place_label_box()
            # for a position that survives the aperture and sorts on the box
            # that comes back, so a name near the curve moves rather than
            # being sliced by it.
            got = place_label_box(x, y, t["name"], w, h,
                                  cls="minilabel", off=7.0)
            if got:
                lhtml, lx, ly, lw, lh = got
                labels.append((2.0 - depth[id(t)] / deepest,
                               lx, ly + LABEL_UP, lw + 8, lh + 4, lhtml))
        if len(rp) > 1:
            cx = sum(p[0] for p in rp) / len(rp)
            cy = sum(p[1] for p in rp) / len(rp)
            ties.extend(
                f'<line class="rtie" x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}"/>'
                for x, y in rp
            )
            # Priority 0: a region name is the thing this map is for, so it
            # displaces a destination label rather than the other way round.
            #
            # It is also the fourth thing on this site that emitted a map
            # label with its own idea of where one goes — centred over the
            # region's destinations, tested against nothing. It happened not
            # to be cut, because a centroid is by construction away from the
            # edges; "happened not to be" is not a property. It now asks for
            # a position that survives the aperture, preferring the middle,
            # and is dropped rather than sliced if none does. The region
            # keeps its tie-lines, its destinations and its row below.
            got = place_label_box(
                cx, cy - 10, r["name"], w, h, off=10.0, prefer="over",
                metric="rlabel",
                wrap=lambda a, x, y, name: (
                    f'<a class="rlabel" href="{urls.region(c, r)}">'
                    f'<text{a} x="{x:.1f}" y="{y:.1f}">{esc(name)}</text>'
                    f'<title>{esc(name)} — {len(r["cities"])} destinations'
                    f'</title></a>'))
            if got:
                rhtml, rx0, ry0, rw, rh = got
                labels.append((0, rx0, ry0 + 14.0, rw, rh + 6, rhtml))

    shown = sum(len(r["cities"]) for r in c["regions"]) - len(offframe)
    note = ""
    if offframe:
        links = ", ".join(
            f'<a href="{urls.city(c, r, t)}">{esc(t["name"])}</a>' for r, t in offframe[:4]
        )
        more = f' and {len(offframe) - 4} more' if len(offframe) > 4 else ""
        note = (f' {len(offframe)} outside this frame: {links}{more} — too far from the '
                f'mainland to draw at this scale without emptying the map.')
    drawn = "".join(phone_declutter(_declutter(labels, w, h), frame=(w, h)))
    return (
        # AND THE FIFTY COUNTRY MAPS WERE STILL CARRYING THE INSTRUMENT WORLD
        # INTO AN EDITORIAL PAGE. `data-world="intelligence"` was taken off
        # the FIGURE and left on the `<svg>` inside it, so every token the
        # dark world rebinds still resolved dark for everything in the
        # drawing — which nothing could see while the drawing was dark
        # anyway. Under the light map it is plain: `--map-ink` resolved to
        # the dark map's bone and every place name on Italy was painted
        # #F3F0E6 on #D8D4C7 stone. 1.00:1, on all fifty, on the only label
        # colour those maps have.
        #
        # A country map is a PICTURE — `docs/cartography.md` splits the two
        # families on what the drawing IS — so it takes the page's world and
        # the light map with it. `data-role` keeps saying it is an
        # instrument-shaped figure, which is a different claim.
        f'<figure class="minimap countrymap arched{dense_class(drawn)}" data-role="instrument">'
        f'<svg viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="Map of {esc(c["name"])} showing its regions and the destinations in the '
        f'Atlas"><defs>{arch_clip("cm" + c["slug"][:14].replace(chr(45), ""), w, h)}</defs>'
        f'<g clip-path="url(#arch-{"cm" + c["slug"][:14].replace(chr(45), "")})">'
        f'<rect x="0" y="0" width="{w}" height="{h}" class="archground"/>'
        f'{ctx}{land}{"".join(ties)}{"".join(dots)}'
        f'{drawn}</g>{arch_edge(w, h)}</svg>'
        # FOUR LINES OF GREY TYPE UNDER THE PAGE'S MOST IMPORTANT IMAGE.
        #
        # This caption carried the full attribution — five dataset names
        # joined by "and" — plus two sentences of methodology, and it was
        # written when the map sat two-thirds of the way down the page where
        # nobody read it. The composition moved the map directly under the
        # h1, and the same paragraph is now the second thing on a country
        # page. The claims are all still made: the register at /sources is
        # the honest form of the attribution, and the grouping-not-boundary
        # rule is on /method and in the map's own aria-label. What stays
        # here is what a reader of THIS map needs: what it shows, what is
        # missing from it, and where to open it bigger.
        f'<figcaption><span class="capsay">{esc(c["name"])}, its '
        f'{n_of(len(c["regions"]), "region")} and {shown} '
        f'{"destination" if shown == 1 else "destinations"}. Region names sit at the '
        f'centre of their own destinations — they are groupings, not boundaries.'
        f'</span><span class="capsrc">{note} '
        f'Coastline and borders from <a href="/sources">Natural Earth</a>, public domain. '
        f'<a href="/map?c={esc(c["slug"])}">Open {esc(c["name"])} on the full map →</a>'
        f'</span></figcaption></figure>'
    )


# The fewest vertices an outline needs to be a country's SHAPE rather than a
# stand-in for a point. Twenty reproduces the six countries this atlas
# already draws as a ringed point and admits the seventh, Luxembourg.
COUNTRY_DOOR_POINTS = 20

# HOW MUCH INLINED GEOMETRY THE PHOTOGRAPHIC BAND MAY SPEND, and this is the
# one number on this page that is art direction rather than a derivation —
# recorded as such, the way `DUSK_CEILING` is. All 41 drawable doors are
# 636 KB together and Russia's outline alone is 107, so the band cannot be
# "all of them" and a COUNT picked by eye would be taste dressed as a rule.
# The budget is the quantity that actually binds: `weight.max_page_kb` is a
# ceiling somebody has to raise in a diff, and the reader also pays for one
# photograph request per door at the ladder's 480 step. So the band takes
# doors in the derived order until the budget is spent and the page states
# how many that turned out to be — which means the set grows on its own when
# the geometry gets cheaper rather than when somebody edits a number.
DOOR_BAND_KB = 90


def country_door(data, images, c, w=900, h=560, brief=True):
    """A country with its own photograph inside its own frontier.

    THE BRIEF'S STRONGEST IDEA, AND THE MECHANISM WAS ALREADY BUILT. The
    /countries directive asks that *"the actual country polygon on the
    EPSG:3034 map should become the visual focus. The photograph can then
    transition inside France's geographic boundary … so the country itself
    becomes the aperture. This also connects beautifully with the EuropeDoor
    name."* `heroeurope()` has drawn exactly that on the homepage since the
    Living Atlas: a `<clipPath>` from the country's own drawn path and an
    SVG `<image>` clipped to it. The same directive says not to invent an
    image system, and this is what that instruction is FOR — the aperture
    here is the clip, not a second one.

    SO THE DOOR IS THE FRONTIER, AND THERE IS NO ARCH ON IT. Every other
    map on this site is seen through the elliptical aperture, and
    `docs/signature-moments.md` asks question 2 before a family gets one:
    this drawing's signature moment IS an aperture — the country's own
    outline, with a photograph of the country through it. Cutting an ellipse
    over that would be two doors on one picture, which is the wallpaper the
    aperture's own rule warns about.

    AND THE FRAME IS THE COUNTRY'S OWN, WHICH IS THE DEPARTURE FROM THE
    HOMEPAGE. That page draws its apertures on one continental frame and its
    own recorded measurement says why only six of them are legible there: *a
    photograph clipped into Belgium renders about 40 pixels wide at 1280 and
    is a smudge with a coastline.* At roughly a pixel per unit Luxembourg is
    eight. That is a property of the FRAME rather than of the idea — framed
    on its own extent, as the fifty country portraits and the nine macro
    glyphs already are, Luxembourg fills its tile exactly as Türkiye fills
    its own. Same geometry as `countrymap()` uses, for the same reason it
    gives: a second simplification would differ by a tenth of a unit and
    show as a fringe along every frontier.

    Returns "" for a country with no polygon and for one with no photograph,
    because a door has to have both — Monaco and Vatican City have no
    outline at any scale in this dataset and cannot be drawn as one.
    """
    key = "country:" + c["slug"]
    if key not in (images or {}):
        return ""
    # AND AN ADVISORY COUNTRY IS NOT LIT, which is `living_atlas`'s own
    # filter and the planner's. Ukraine, Russia and Belarus keep a page
    # carrying the warning; a photographic celebration of one on the atlas
    # index would be the opposite of that position, stated by the same site.
    if (c.get("advisory") or {}).get("level"):
        return ""
    doc = geo.country(c["slug"])
    if not doc or not doc.get("bbox"):
        return ""
    bbox = geo.principal_frame(doc, c["slug"])[0] or list(doc["bbox"])
    proj = geo.Projection(bbox, w, h, pad=0.05)
    ctx, land = geo.landmass(proj, (0, 0, w, h), doc=doc, highlight=c["slug"])
    here = re.findall(r'<path[^>]*class="[^"]*\bhere\b[^"]*"[^>]*\sd="([^"]*)"',
                      land)
    if not here:
        return ""
    d = here[0]
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    # AND A COUNTRY THE ATLAS DRAWS AS A POINT CANNOT BE A DOOR. The first
    # version drew whatever outline came back, which for Monaco is FOUR
    # points filling 659 x 480 units — a quadrilateral with a photograph in
    # it, labelled Monaco. That is *a bounding box is not a country*
    # arriving through the geometry rather than through a label.
    #
    # THE FLOOR IS MEASURED ON THE OUTLINE THIS DRAWING ACTUALLY USES, and
    # the first attempt borrowed a test that does not apply here: asking
    # `geo.landmass` for the country at `min_units=60` on the CONTINENTAL
    # frame is how `constel_defs` and `region_glyph` decide what to draw,
    # and it dropped Luxembourg — which is 5.6 units wide there and full
    # size here, because this frame is the country's own. *A rule measured
    # only where it loses looks like a rule that wins nowhere.*
    #
    # Measured at this frame, the vertex counts are 4, 7, 7, 12, 13, then
    # 21, 33, 51 — so a floor of twenty reproduces exactly the six
    # countries this repository already records as *having no polygon at
    # 1:50m and drawn as a ringed point*, and admits Luxembourg, whose
    # 21-point outline is its real shape rather than a stand-in. Two
    # independent derivations agreeing on the same six is the evidence for
    # the number; one of them alone would be a threshold picked to get an
    # answer.
    if len(xs) < COUNTRY_DOOR_POINTS or not ys:
        return ""
    # THE IMAGE EXTENT IS THE SUBJECT'S WHOLE BOX and `slice` crops the
    # source into it, exactly as `object-fit: cover` does everywhere else
    # and exactly as the Living Atlas does — anything the rectangle misses
    # is a piece of the country drawn in stone beside a piece drawn in
    # photograph.
    bx, by = min(xs), min(ys)
    bw, bh = max(xs) - bx, max(ys) - by
    # The step is the drawn width of the subject rather than one number for
    # every country, which is the Living Atlas's own reasoning: this is a
    # 900-unit frame in a column about 1,150 wide, so the subject is close
    # to its own unit count in CSS pixels and wants twice that for a retina
    # screen.
    href = photo_href(images, key, max(bw, bh) * 2.0)
    if not href:
        return ""
    row = (images or {}).get(key) or {}
    ident = "cd" + re.sub(r"[^a-z0-9]", "", c["slug"])[:16]
    return (
        f'<figure class="countrydoor">'
        f'<svg class="instrmap atlas" data-role="illustration"'
        f' viewBox="0 0 {w} {h}" role="img"'
        f' aria-label="{esc(c["name"])} drawn on its own frontier, filled with a '
        f'photograph of it">'
        f'<defs><clipPath id="{ident}" clipPathUnits="userSpaceOnUse">'
        f'<path d="{d}"/></clipPath></defs>'
        f'<rect class="lyr lyr-ocean" x="0" y="0" width="{w}" height="{h}"/>'
        f'<g class="lyr lyr-land">{ctx}{land}</g>'
        f'<image class="cdshot" clip-path="url(#{ident})"'
        f' x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}"'
        f' preserveAspectRatio="xMidYMid slice" href="{esc(href)}"'
        f' aria-hidden="true"/>'
        # THE FRONTIER GOES OVER THE PHOTOGRAPH, which is what stops it
        # being a picture pasted on a map and makes it the country FILLED —
        # the Living Atlas's own sentence, and the reason the line is drawn
        # from the identical path the clip uses rather than from a copy.
        f'<path class="cdedge" d="{d}" aria-hidden="true"/>'
        f'</svg>'
        # NEVER EXPLAIN THE CONSTRAINT BACK. The first version gave every
        # tile the same two sentences — *"<Country>, filled with a photograph
        # of it and bounded by its own frontier, the outline is the
        # aperture"* and *"Coastline and borders from Natural Earth"* — so a
        # band of ten said one thing ten times and the only word that
        # differed was the country's name. That is this site's own rule
        # broken by a band of this site's own making: a reason shared by
        # every result is hoisted once above the set and each row carries
        # what separates it. The LEAD door keeps the sentence, because there
        # it is the explanation rather than a repetition of one.
        #
        # AND THE ALT TEXT IS NOT A CAPTION. It was being printed under the
        # picture as prose — *"Aerial view of a mountainous coastal landscape
        # with lush greenery and scattered houses"* — which is written for a
        # reader who cannot see the photograph and says the same thing twice
        # to everybody who can.
        + (f'<figcaption><span class="capsay">{esc(c["name"])}, filled with a '
           f'photograph of it and bounded by its own frontier — the '
           f'outline is the aperture.</span><span class="capsrc">'
           f'Coastline and borders from <a href="/sources">Natural Earth</a>, '
           f'public domain.</span></figcaption>' if brief else
           f'<figcaption><span class="capsay">{esc(c["name"])}</span>'
           f'</figcaption>')
        + '</figure>')


def first_sentence(text):
    """The first sentence, whole.

    This was `text[:140] + "…"`, which cut "The Bergen and Dovre railways are
    two of Europe's great train rides and cost less than the equivalent
    flight if booked early. Coastal Norway…" — a truncation mid-clause,
    printed on 400 place pages, that reads as a rendering fault rather than
    as a summary. A sentence boundary is the one place a text can be cut
    without looking broken.

    AND THE DESTINATION PAGE'S "GETTING THERE" PANEL NEVER TOOK IT. It kept
    `getting_around[:150] + "…"`, which is the exact expression this function
    replaced, one screen away from the function that replaced it: 30 of the
    50 countries are cut mid-WORD at 150 characters, so **213 of 319
    destination pages** printed "Rural France needs a car; the re…". A rule
    that exists is not a rule that is inherited.

    It fits, measured rather than hoped: the first sentence of
    `getting_around` runs 8 to 171 characters with a median of 80, against
    the 150 the panel was already giving it.
    """
    for stop in (". ", "! ", "? "):
        i = text.find(stop)
        if i > 0:
            return text[:i + 1]
    return text


# The length at which a statement stops being one. Two lines of display
# serif at 26ch is about here; past it the type has to come down a step or
# the reader meets a wall instead of a sentence. Measured, not chosen: the
# thirteen theme summaries are 239–344 characters and every other family's
# copy is under 180.
STATEMENT_MAX = 160


def statement(text):
    """The overture's sentence, at whichever of the two sizes it needs."""
    long = " long" if len(text) > STATEMENT_MAX else ""
    return f'<p class="statement{long}">{esc(text)}</p>'


def rank_phrase(rank, total):
    """"the widest of 17 tags", "the second widest", "the narrowest".

    Rendered as `the {ordinal(rank)} widest` this produced "the FIRST widest
    of 17 tags" on /interests/history, which is not English — the superlative
    already carries the one. The ends of the list are the two places a rank
    has its own word, and both are worth having: the narrowest tag is as
    interesting a fact about this atlas as the widest."""
    if rank == 1:
        return f"the widest of {total} tags"
    if rank == total:
        return f"the narrowest of {total} tags"
    return f"the {ordinal(rank)} widest of {total} tags"


def ordinal(n):
    """1 -> first, 2 -> second … 17 -> 17th. Words to ten, digits after.

    "the 1th widest" was what `f"{n}th"` produced, which is the kind of thing
    a template does when nobody renders it."""
    words = ("", "first", "second", "third", "fourth", "fifth", "sixth",
             "seventh", "eighth", "ninth", "tenth")
    if n < len(words):
        return words[n]
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def empty_state(what, why):
    """An absence that says why it is an absence.

    THE FOURTH-MOST-COMMON THING THIS SITE SHOWS A READER IS A GAP, and for
    four of them it said only "Nothing tagged yet." / "Nothing listed yet." /
    "Nothing listed on this route yet." A bare "nothing yet" reads as a page
    that failed to load. Everywhere else this repository states its limits at
    length and gets credit for it — the place page's three refused fields,
    the interest page's idle keywords, Svalbard's missing map, the facet
    threshold — and these four were the surfaces where the habit lapsed.
    That inconsistency is not a small thing on a site whose whole claim is
    that it tells you what it does not have.

    Two parts, always: what is missing, and why — where "why" names the
    editorial work that would fill it, because on this site an empty list is
    almost always a gap in the writing rather than a fact about Europe.
    """
    return (f'<p class="emptystate"><strong>{what}</strong> {why}</p>')


# The central meridian of the projection. A scale bar is measured there
# because that is where a conic's own arithmetic is simplest; the check that
# the bar is honest walks the frame's latitudes, which is the axis that
# actually moves the scale.
LCC_MID_LON = 10.0


def _lat_at(y):
    """Projection y -> latitude, on the central meridian.

    A conic has no closed inverse worth writing here for one caption, and a
    bisection over the extent costs about forty comparisons — cheaper than
    the coastline it is drawn on top of, and impossible to get subtly wrong.
    """
    lo, hi = 20.0, 85.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if MAPPROJ.xy(mid, LCC_MID_LON)[1] > y:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def nights_line(t):
    """"2–3 nights", or "1 night" when the range has no range in it.

    Tatev read "1–1 NIGHTS" on the motion pages, which is a template showing
    through: a range whose ends are equal is not a range, and a plural on a
    one is not English. The region page already formatted this correctly and
    three other surfaces did not, which is the argument for one function.
    """
    lo, hi = t["nights"][0], t["nights"][1]
    if lo == hi:
        return f'{lo} night' if lo == 1 else f'{lo} nights'
    return f'{lo}–{hi} nights'


def country_orient(c):
    """One derived line under a country's statement.

    The country page's job is ORIENTATION, and the first thing a reader
    needs oriented is size: how much of this country the atlas actually
    holds, and where its centre of gravity is. Derived, never authored —
    the counts come from the regions themselves and change when the data
    does.
    """
    regions = len(c["regions"])
    towns = sum(len(r["cities"]) for r in c["regions"])
    return (f'{towns} destination{"s" if towns != 1 else ""} across '
            f'{regions} region{"s" if regions != 1 else ""} · '
            f'capital {esc(c["capital"])}')


def coord_line(t):
    """45.920°N, 6.870°E — a coordinate a reader can put into anything."""
    return (f'{abs(t["lat"]):.3f}°{"N" if t["lat"] >= 0 else "S"}, '
            f'{abs(t["lon"]):.3f}°{"E" if t["lon"] >= 0 else "W"}')


def orient_line(t):
    """One thin line under the statement: what kind of place, and how long.

    This is the ONLY factual line above the argument. Everything else —
    population, coordinates, the region link, the scores — moved below it,
    because a reader who has not yet been told why to care about a place has
    no use for its population. The two facts kept are the two that change
    whether you would go at all: what kind of thing it is, and whether it is
    an afternoon or a week.
    """
    bits = []
    kind = CITY_TYPE_NAMES.get(t.get("city_type"))
    if kind:
        bits.append(esc(kind))
    # AND IT FORMATTED THE NIGHTS ITSELF, WRONGLY. `nights_line()` exists
    # for exactly this and already says "1 night"; this line said "1 nights"
    # on every destination the atlas gives a single night. The docstring of
    # that function records three other surfaces getting it wrong; this was a
    # fourth, in the ONE factual line above the argument.
    if len(t.get("nights") or []) == 2:
        bits.append(nights_line(t))
    return " · ".join(bits)


# art_note() was deleted rather than kept.
#
# It existed to say "Illustration, not a photograph" beside a generated
# horizon, which was the honest thing to do while there WAS a generated
# horizon. The illustration is gone from this family, so the note became a
# disclaimer about something that is not on the page — the same class of
# untruth it was written to prevent, pointing the other way. A caption that
# survives the thing it captions is worse than no caption.


def minimap(data, t, span=3.2, about=None, named=None):
    """A small map centred on one destination, drawn from the same
    projection the big map uses. Its neighbours are on it so the reader can
    see the shape of the onward journey rather than read distances.

    `span="auto"` FITS THE FRAME TO THE COUNTRY, which a fixed number cannot.
    The destination composition first used a fixed span=8 — tight enough to
    feel local — and 43 of the 319 destinations came out as a nearly empty
    rectangle with one dot in it. Not only the genuinely remote ones:
    **Berlin and Kyiv** were in that list, because what a span means depends
    entirely on how densely the atlas covers that part of Europe. Svalbard
    really is alone; Berlin is not, and a map that says it is, is wrong.

    So the frame widens until it has company, and stops. The caption already
    derives and prints the real kilometres, so a map of Svalbard still says
    it is looking across 2,000 km — the reader is told, not misled.
    """
    cx, cy = project(t["lat"], t["lon"])
    w, h = 900, 320
    # NOT builtins.hash(). THE BUILD WAS NOT DETERMINISTIC.
    #
    # This was `abs(hash((name, lat, lon))) % 100000`, and Python randomises
    # the hash of a string per process unless PYTHONHASHSEED is set. So every
    # build gave all 319 destination pages a different clipPath id and 319
    # files changed with nothing behind it. The generated site is committed
    # and CI fails when it is stale, so the cost is not cosmetic: `git
    # status` after a build always said 319 files, which is exactly the
    # amount of noise a real one-file regression hides in. It survived four
    # commits of this work before a word-diff of a page I had not touched
    # showed the only change was the id.
    #
    # sha256 of the same three values: stable across processes, machines and
    # Python versions, which is what "the build produces identical pages"
    # requires.
    uid = "mm" + hashlib.sha256(
        f'{t["name"]}|{t["lat"]}|{t["lon"]}'.encode()).hexdigest()[:8]
    if span == "auto":
        pts = [project(n["city"]["lat"], n["city"]["lon"]) for n in data["cities"].values()]
        span = 2.4
        for cand in (10.0, 8.0, 6.0, 4.5, 3.2, 2.4):
            near = sum(1 for x, y in pts
                       if abs(x - cx) <= w / 2 / cand and abs(y - cy) <= h / 2 / cand)
            if near >= 6:          # the destination itself plus five others
                span = cand
                break
    # The caption used to claim "within about 192 kilometres", which was
    # span x 60 and meant nothing. Then it was derived from degrees per pixel
    # and a cosine, which was right for an equirectangular projection and is
    # wrong for the conformal conic that replaced it. A conformal projection
    # has one scale at a point — the same along the parallel and along the
    # meridian — so both numbers now come from measuring it there.
    # The land is the doorway's ground: an arch cut over emptiness is a
    # shape, an arch cut over a coastline is an opening onto somewhere.
    #
    # CLIPPED TO THE WINDOW, WHICH IT WAS NOT FOR THE LIFE OF THIS MAP.
    #
    # This asked landmass() for (0, 0, MAP_W, MAP_H) — the entire continent —
    # and let the arch's clip path hide everything outside the frame. So a
    # Santorini page carried the coastline of Norway: 73,464 bytes of Europe
    # emitted into every destination and place page, about 79% of the bytes
    # on the page, on a site whose heaviest page is a recorded ceiling.
    #
    # It cost nothing to notice and nothing to fix. It survived because the
    # picture was right — the clip path did hide it — and no check has ever
    # measured what a page contains that it does not show. The window is
    # (cx, cy) ± half the frame in projection units, which is the same
    # arithmetic the dots two blocks below already use.
    view = (cx - w / 2 / span, cy - h / 2 / span, w / span, h / span)
    kmu = geo.km_per_unit(MAPPROJ, t["lat"], t["lon"])
    km_w = int(round(w / span * kmu / 10) * 10)
    km_h = int(round(h / span * kmu / 10) * 10)
    # THE LOCAL LOD RULE, AND IT IS STATED IN KILOMETRES BECAUSE THAT IS WHAT
    # DECIDES IT. See geo.local() and docs/coastline-lod.md: the continental
    # file simplifies at 4.4 km, which is nine pixels on a frame this size,
    # and it made every coastal destination a set of wedges — and left visible
    # seams of sea colour along frontiers on inland ones. The finer file is
    # already in the repository and only what falls in the window is emitted.
    # A frame wider than the cap is a continental picture, where lod1 is both
    # the right detail and the affordable one.
    _home = next((n["country"]["slug"] for n in data["cities"].values()
                  if n["city"] is t), None)
    ctx, land = geo.landmass(
        MAPPROJ, view,
        doc=geo.local(_home) if km_w <= geo.LOCAL_LOD_MAX_KM else None)
    # And the bar, on the same arithmetic the caption uses. These are the
    # most-seen maps on the site — one per destination and one per place —
    # and until the projection was conformal none of them could carry one.
    bar = geo.scale_bar(MAPPROJ, _lat_at(cy + h / 2 / span),
                        _lat_at(cy - h / 2 / span), LCC_MID_LON,
                        1.0 / span, w, h)
    dots, labels = [], []
    # THE SCALE BAR IS TYPE TOO, and it is placed by arithmetic rather than by
    # the placement rule, so the rule had never been told about it. Reserving
    # its box before anything else is placed is what takes the site's last two
    # overlapping pairs to zero; the subject's own name still ignores it,
    # because the subject is never moved for anything.
    labels.append(("", *geo.scale_bar_box(w, h, PHONE_LABEL_SCALE), 1.0))
    inframe = []

    # PHYSICAL GEOGRAPHY ON THE TWO FAMILIES THAT MOST NEED IT. Rendered and
    # looked at, Chamonix's plate was a beige field with dots on it: you could
    # not tell it was the Alps. Peaks and named ranges are the terrain this
    # atlas actually holds — a measurement somebody else made, never a surface
    # fitted here.
    #
    # THE PROJECTOR IS THIS MAP'S OWN. The land is drawn inside a translate
    # and scale, so continent coordinates have to go through the same
    # transform or the Alps land in France, which is exactly what happened the
    # first time feature labels were added anywhere.
    _peaks_done = [False]

    def _tx(lat, lon):
        px_, py_ = project(lat, lon)
        return (w / 2 + (px_ - cx) * span, h / 2 + (py_ - cy) * span)

    def _free(lx, ly, lw, lh):
        """Is this box clear of every label already placed?

        The same clearance the physical names have always been tested with,
        now offered to the place names too — see place_label_box(), and see
        the 160 plates of overlaps that came of their never having had it.
        """
        bx = (lx - LABEL_CLEAR, ly - LABEL_CLEAR,
              lx + lw + LABEL_CLEAR, ly + lh + LABEL_CLEAR)
        # `[:5]` BECAUSE AN ENTRY MAY CARRY ITS OWN PHONE SCALE. The scale
        # bar's reservation does — it is pre-grown to the size a phone draws
        # it and then told not to grow again — and a fixed five-way unpack
        # stopped the whole build on it.
        for _e in labels:
            _hh, qx, qy, qw, qh = _e[:5]
            q = (qx - LABEL_CLEAR, qy - LABEL_CLEAR,
                 qx + qw + LABEL_CLEAR, qy + qh + LABEL_CLEAR)
            if not (bx[2] < q[0] or bx[0] > q[2]
                    or bx[3] < q[1] or bx[1] > q[3]):
                return False
        return True

    def _fits(got):
        """Place a label if it clears every box already down."""
        if not got:
            return False
        _lh, lx, ly, lw, lh = got
        bx = (lx - LABEL_CLEAR, ly - LABEL_CLEAR,
              lx + lw + LABEL_CLEAR, ly + lh + LABEL_CLEAR)
        # `[:5]` BECAUSE AN ENTRY MAY CARRY ITS OWN PHONE SCALE. The scale
        # bar's reservation does — it is pre-grown to the size a phone draws
        # it and then told not to grow again — and a fixed five-way unpack
        # stopped the whole build on it.
        for _e in labels:
            _hh, qx, qy, qw, qh = _e[:5]
            q = (qx - LABEL_CLEAR, qy - LABEL_CLEAR,
                 qx + qw + LABEL_CLEAR, qy + qh + LABEL_CLEAR)
            if not (bx[2] < q[0] or bx[0] > q[2]
                    or bx[3] < q[1] or bx[1] > q[3]):
                return False
        labels.append(got)
        return True

    def _physical():
        for fx, fy, fnm, fm in cartography.summit_points(_tx, (0, 0, w, h),
                                                         most=3):
            if any(_fits(place_label_box(fx, fy, f"{fnm} {fm:,} m", w, h,
                                         cls="peakname", off=off_,
                                         prefer=pref))
                   for pref in ("beside", "over")
                   for off_ in (9.0, 20.0)):
                dots.append(f'<path class="peak" d="M{fx:.1f} {fy - 4.2:.1f}'
                            f'L{fx + 4.0:.1f} {fy + 2.6:.1f}'
                            f'L{fx - 4.0:.1f} {fy + 2.6:.1f}Z">'
                            f'<title>{esc(fnm)} — {fm:,} m</title></path>')
        for fx, fy, fnm in cartography.feature_points(_tx, (0, 0, w, h)):
            _fits(place_label_box(fx, fy, fnm, w, h, cls="fname",
                                  metric="rlabel", off=8.0, prefer="over"))
        # A RIVER IS THE ONE PHYSICAL FAMILY THAT WAS DRAWN AND NEVER NAMED.
        # After the seas and before nothing: it is placed last of the
        # physical labels and the physical labels are placed after every
        # place name, so the destination's own names win every collision and
        # a river only gets what is left. On Vienna that is the Danube; on a
        # frame the river merely clips, it is nothing, which is the whole
        # point of scoring by drawn extent rather than by dataset rank.
        # THE SUBJECT IS PASSED IN, WHICH IS THE WHOLE DIFFERENCE. Scored on
        # extent alone, London's map named the Lek — a Rhine distributary in
        # the Netherlands that out-measures the Thames on a frame reaching
        # the Low Countries. A river is named because it identifies THIS
        # place, and the anchors are tried in order from the point nearest
        # the place outward, because a river crosses the whole picture and
        # its name only needs one gap.
        for rnm, ranchors in cartography.river_points(_tx, (0, 0, w, h),
                                                      subject=(w / 2, h / 2)):
            for rx, ry in ranchors:
                if _fits(place_label_box(rx, ry, rnm, w, h, cls="rname",
                                         off=5.0,
                                         prefer="beside", clears=_free)):
                    break
        for fx, fy, fnm in cartography.water_points(_tx, (0, 0, w, h)):
            _fits(place_label_box(fx, fy, fnm, w, h, cls="sname",
                                  metric="rlabel", off=8.0, prefer="over"))

    for _cid, n in sorted(data["cities"].items()):
        x, y = project(n["city"]["lat"], n["city"]["lon"])
        dx, dy = (x - cx), (y - cy)
        if abs(dx) > w / 2 / span or abs(dy) > h / 2 / span:
            continue
        inframe.append((w / 2 + dx * span, h / 2 + dy * span))
    # The frame here is w wide rather than 1000, so the cap scales with it.
    hitr = hit_radius(inframe, w, cap=34.0 * w / 1000.0)
    # THE SUBJECT FIRST, THEN THE PHYSICAL GEOGRAPHY, THEN THE NEIGHBOURS.
    # Mont Blanc is ten kilometres from Chamonix and the Matterhorn is beside
    # Zermatt, so at this scale a summit sits almost on top of the town it
    # explains and every placement rule that ran the towns first dropped both
    # peaks. On an Alpine plate the mountain outranks a NEIGHBOURING town's
    # name — it is the reason the town is there — and the subject's own name
    # outranks everything.
    _ordered = sorted(data["cities"].items(),
                      key=lambda kv: (0 if kv[1]["city"] is t else 1, kv[0]))
    for cid, n in _ordered:
        x, y = project(n["city"]["lat"], n["city"]["lon"])
        dx, dy = (x - cx), (y - cy)
        if abs(dx) > w / 2 / span or abs(dy) > h / 2 / span:
            continue
        if n["city"] is not t and not _peaks_done[0]:
            _peaks_done[0] = True
            _physical()
        px, py = w / 2 + dx * span, h / 2 + dy * span
        here = n["city"] is t
        # A DOT THE PAGE CANNOT NAME IS NOT A LINK.
        #
        # This map draws every destination that falls in the frame, and the
        # page lists the eight nearest. On Innsbruck that is twelve dots and
        # eight rows: Hallstatt, Bled, Bovec, Lauterbrunnen and St. Moritz
        # were reachable ONLY as a 4.9-pixel circle, appearing nowhere else
        # in the document — not in the rows, not in the prose, not in the
        # structured data. Six links on a phone that no reader could hit and
        # no screen reader would ever reach in the flow.
        #
        # The context dots are worth keeping: they are what shows that
        # Innsbruck sits among others rather than alone. So they stay as
        # context, with their name in a <title>, and stop pretending to be
        # navigation. What the page names, the map links.
        url = urls.city(n["country"], n["region"], n["city"])
        title = f'<title>{esc(n["city"]["name"])}, {esc(n["country"]["name"])}</title>'
        # The "here" dot linked to the page it is drawn on. That is a marker,
        # not navigation, and a 5.5-unit self-link is the worst kind of small
        # target: it costs a tap and goes nowhere.
        links = (named is None or url in named) and not here
        body = (f'<circle class="hit" cx="{px:.1f}" cy="{py:.1f}" r="{hitr:.1f}"/>'
                if links else "")
        body += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{5.5 if here else 3.6}"/>'
        if links:
            dots.append(f'<a class="minidot" href="{url}">{body}{title}</a>')
        else:
            dots.append(f'<g class="minidot{" here" if here else " context"}">'
                        f'{body}{title}</g>')
        if here or abs(dx) < w / 2 / span * 0.62:
            # Against the aperture, not the rectangle. Fourteen names across
            # the site were drawn entirely inside the corner the arch
            # removes, and most of them were on this map: it draws every
            # neighbour it can reach, so it is the family that puts labels
            # nearest the curve. See place_label().
            # THE SUBJECT IS PLACED WHEREVER IT WANTS TO GO. It is the one
            # name on this map that cannot be dropped or moved for somebody
            # else's sake; every other name gives way to it, which is what
            # placing it first already meant and what the clearance test now
            # enforces. A neighbour tries all four positions and is dropped
            # if none of them is free, keeping its dot, its <title> and its
            # row in the list below — the same bargain a name too close to
            # the aperture has always had.
            got = place_label_box(
                px, py, n["city"]["name"], w, h,
                cls="minilabel here" if here else "minilabel", off=8.0,
                clears=None if here else _free)
            if got:
                labels.append(got)
    # If the frame held only the subject, the physical pass never ran in the
    # loop; run it now.
    if not _peaks_done[0]:
        _physical()

    drawnlabels = "".join(phone_declutter(labels, frame=(w, h)))

    # RELIEF, WHERE THE GROUND SAYS SO AND NOWHERE ELSE. The strength is
    # derived from the elevation model — the 95th minus the 5th percentile of
    # height within 25 km of this destination — and never from a list of
    # mountainous places, which would be an authored measurement. Paris measures 99 m of
    # spread and gets no terrain, because a Paris illustration must not look
    # like a topographic map merely because the pipeline owns a DEM. See
    # docs/terrain-prototype.md.
    tkey = next((f'{n["country"]["slug"]}/{n["region"]["slug"]}/'
                 f'{n["city"]["slug"]}'
                 for n in data["cities"].values() if n["city"] is t), None)
    tdraw = cartography.draws_relief(cartography.relief_of(tkey))
    # `about` names something INSIDE this destination — a place page's
    # subject. The map is then honestly captioned as what it is: this atlas
    # has one projection and its finest unit is about four kilometres, so
    # there is no map of a building, and a map labelled "Bryggen" that is
    # actually a map of Bergen would be the kind of small lie refused
    # everywhere else here.
    #
    # AND THE CAPTION GOES THROUGH THE PLATE NOW, rather than being glued on
    # after slicing `</figure>` off the end of it. The plate is the only
    # thing that knows which layers it actually drew, and the relief credit
    # is attached to the drawing rather than to the request — see
    # cartography.credited(). Building the sentence out here and handing it
    # over costs nothing and removes the one place in this file that took a
    # renderer's output apart with a string index.
    # THE PROVENANCE WAS AS LOUD AS THE PICTURE. Measured at 390 on a
    # destination page: the map draws 250 pixels tall and the one paragraph
    # under it runs six lines and 160 — a caption, a frame measurement, a
    # coastline credit and a relief credit, all in one run of the same type.
    # Every one of them has to be there, and nobody had decided how loudly.
    #
    # Two lines: what the picture IS, and where the data came from. The
    # second is the site's own source-note scale, which is what it is for.
    # `credited()` still inserts before the map link, so the relief credit
    # lands with the other credits and not in the sentence.
    # AND THE LINE BETWEEN THEM IS WHAT YOU ARE LOOKING AT AGAINST HOW IT WAS
    # MADE. The first split left the whole sentence in the caption, and on a
    # place page that sentence carries the projection disclosure — measured at
    # 390, 199 pixels of caption under a 127-pixel drawing, a caption taller
    # than the picture it captions. The scale of the projection and the size
    # of the frame are facts about the instrument, not about the place, and
    # they belong with the datasets that drew it.
    cap = (
        f'<figcaption><span class="capsay">'
        + (f'{esc(about)} is in {esc(t["name"])}, and this is {esc(t["name"])}.'
           f'</span><span class="capsrc">The atlas draws Europe in one '
           f'projection whose finest unit is about four kilometres, so it maps '
           f'the town rather than the street. ' if about else
           f'{esc(t["name"])} and its neighbours in the Atlas.</span>'
           f'<span class="capsrc">') +
        f'The frame is about {km_w:,} km across and {km_h:,} km deep at this '
        f'latitude. '
        # THE CREDIT, WHICH 318 PAGES DID NOT CARRY AND 274 CARRIED BY
        # ACCIDENT. A destination page named Natural Earth because pop_line
        # prints the dataset behind its population — so the 45 destinations
        # with no population figure named nothing, and every place page named
        # nothing. Coverage that depends on a different field being present
        # is worse than none, because it looks like a policy. One clause, the
        # same one the region and story maps carry.
        f'Coastline from <a href="/sources">Natural Earth</a>, public domain. '
        f'<a href="/map">The full map →</a></span></figcaption>')
    return cartography.plate(
        # TWO SPACES, NAMED SEPARATELY. `view` is the window in the
        # continent projection this plate shows; `transform` is what
        # takes that window to the 900x320 picture. Every caller used to
        # pass (0, 0, w, h) here, which made the renderer select its own
        # layers from the North Sea and draw them over the Alps.
        uid=uid, w=w, h=h, proj=MAPPROJ, view=view,
        transform=(f'translate({w/2 - cx*span:.2f},'
                   f'{h/2 - cy*span:.2f}) scale({span})'),
        cut_reach=dusk_reach(),
        land=land, context=ctx, relief=tdraw, frame_km=km_w,
        destinations="".join(dots), labels=drawnlabels + bar,
        rim=False, caption=cap,
        figure_class=(f"minimap arched atlas{dense_class(drawnlabels)}"
                      + (" terrain" if tdraw else "")),
        aria=f"Map of {esc(t['name'])} and the places around it")


# THE CLIP IS AN ELLIPSE AND THE PLACEMENT RULE TESTED A RECTANGLE.
#
# `px + wide > vw` puts a label on the other side of its dot when it would
# run off the right-hand edge, which is what a cartographer does and was
# right about the edge it tested. It is not the edge that cuts. The drawing
# is clipped by the ARCH — rx = span/2, ry = 34% of the height — so the top
# corners are removed entirely, and a label can sit comfortably inside the
# viewBox and be sliced by the curve above it.
#
# Measured across all 815 pages that draw a labelled map: 5,184 labels, of
# which 184 on 142 pages had a corner outside the aperture and FOURTEEN were
# drawn entirely inside the removed corner — invisible, with nothing anywhere
# saying a place was missing. "Dürnstein & the Wachau" simply did not exist
# on the Hallstatt map. The rectangle check reported the same pages as at
# most 0.7% over, which is why nobody looked: the instrument was measuring
# the wrong boundary.
#
# So the signature was deleting the content it exists to frame, and only
# testing against the real curve finds it.
def in_arch(px, py, vw, vh, rise=None, inset=0.0):
    """Is this point inside the aperture? Same curve as render.arch_path.

    `inset` shrinks the opening before testing. Type that touches the curve
    exactly is not cut and still looks cramped, and the estimate of a label's
    box is an estimate: with no margin at all one name in 5,114 came out
    0.25% of the radius outside, which is a rounding error rather than a
    placement decision. LABEL_CLEAR is what a mason leaves.
    """
    if rise is None:
        rise = min(vh * 0.34, vw * 0.5)
    rise = max(1.0, min(rise, vh * 0.9, vw * 0.5))
    if not (inset <= px <= vw - inset and py <= vh - inset):
        return False
    if py >= rise:
        return True
    rx, ry = vw / 2.0 - inset, rise - inset
    if rx <= 0 or ry <= 0:
        return False
    dx = (px - vw / 2.0) / rx
    dy = (py - rise) / ry
    return dx * dx + dy * dy <= 1.0


# A LABEL'S WIDTH IS NOT PROPORTIONAL TO ITS LENGTH, AND 6.1 PER CHARACTER
# UNDERSTATED 244 OF 311 NAMES.
#
# The old constant was measured, and measured as a MEAN: it only ever had to
# decide which side of a dot a name went on, where being wrong by a few units
# changes nothing. It is now deciding whether a name can be drawn at all, and
# an estimate that is under the truth four times in five drops labels that fit
# and keeps labels that do not.
#
# Fitted instead against every label the site renders — 1,057 measured boxes,
# 311 distinct names from 3 to 40 characters, taking the WIDEST rendering of
# each name in any frame — as the upper envelope of width against length:
#
#     units = 24.4 + 6.05 * characters
#
# which underestimates none of the 311. The intercept is real: a name has a
# fixed cost (side bearings, the space the glyphs do not fill) that no
# per-character figure can carry, which is why "Rome" measures 8.79 units per
# character and "Amboise & the Loire châteaux" measures 5.9.
LABEL_PAD, LABEL_CH = 24.4, 6.05
# Ascent and descent from the same sample: the tallest rendered box is 13.10.
LABEL_UP, LABEL_DOWN = 9.6, 4.0
# And the clearance a name keeps from the curve, in frame units.
LABEL_CLEAR = 4.0

# ONE MODEL PER TYPE SIZE, because a region name is not a destination name.
# `.countrymap .rlabel text` is 15px bold against the destination labels'
# 11px, and the same envelope fitted over its 99 rendered names gives
# 18.8 + 8.89 per character — so the 6.05 model understates 95 of the 99.
# The old hand-written figure in the country map was `len(name) * 8.4`,
# which understates 94 of them: close enough to sort collisions by and not
# close enough to decide whether a name survives the curve.
# AND A THIRD, FOR THE ONE NAME ON A COUNTRY PLATE THAT IS NOT A PLACE NAME.
# `.cname` is the country's own name at --t-lg, uppercase, tracked 0.22em, and
# it was composed at the end and prepended to the finished labels WITHOUT
# being placed or measured — so it sat wherever the middle of the country was
# and everything else was arranged around a box nobody had declared. 27 of 50
# country pages carried an overlap because of it, the worst "ARMENIA" through
# "THE NORTH & SOUTH" by 125 pixels. Fitted as the upper envelope over the 43
# rendered names, which underestimates none of them.
# The measured line box of a country name is 22.56 units deep, so that is the
# leading a second line needs — see the two-line branch in countryportrait().
CNAME_LEAD = 22.6

LABEL_METRICS = {
    "minilabel": (LABEL_PAD, LABEL_CH, LABEL_UP, LABEL_DOWN),
    "rlabel": (18.8, 8.89, 14.0, 5.0),
    "cname": (10.4, 17.35, 17.9, 4.7),
    # And the same name on two lines, which is what an atlas does with a name
    # too wide for the country it belongs to. Same width model — the wider
    # half decides — and a box two lines deep, centred on the anchor.
    "cname2": (10.4, 17.35, 17.9 + CNAME_LEAD / 2, 4.7 + CNAME_LEAD / 2),
}


def label_fits(x, y, wide, anchor, vw, vh, up, down):
    """Every corner of a label's box, against the aperture."""
    x0, _y0, _w, _h = _label_box(x, y, wide, anchor, up, down)
    return all(in_arch(cx, cy, vw, vh, inset=LABEL_CLEAR)
               for cx in (x0, x0 + wide)
               for cy in (y - up, y + down))


def _label_box(x, y, wide, anchor, up, down):
    x0 = (x if anchor == "start" else
          x - wide if anchor == "end" else x - wide / 2.0)
    return x0, y - up, wide, up + down


def place_label_box(px, py, name, vw, vh, cls="minilabel here", off=10.0,
                    prefer="beside", wrap=None, metric="minilabel",
                    clears=None, fits=None):
    """The first position that fits inside the aperture AND is free, with its box.

    Right of the dot, then left, then under it, then over it. A name that
    fits nowhere is dropped exactly as a colliding one is — the dot, the
    <title> and the row in the list below all survive — because a name
    sliced mid-word by the signature reads as a broken renderer, and one
    drawn entirely outside it reads as a missing place.

    `clears(x0, y0, w, h)` is what makes the second half of that sentence
    true. IT WAS NOT TRUE FOR THE DESTINATION FAMILY, which is the most-seen
    map on this site — one per destination and one per place, 824 pages. The
    country map and the macro map both run a greedy declutter over their
    placed boxes; the destination map ran only the PHONE pass, which decides
    what fits at the enlarged phone size and marks the losers `wide-only`.
    `wide-only` is `display: none` below 44rem and drawn above it, so at
    production size every rejected label came back and nothing ever resolved
    an overlap: **160 of 319 destination plates carried at least one
    overlapping pair at 1280 px**, the worst of them "Andorra la Vella"
    through "Madriu-Perafita-Claror" by 120 pixels. Every colliding pair
    involved a `wide-only` label, which is what named the cause.

    The test belongs HERE rather than in a pass afterwards, because a label
    that collides where it wants to go should try the other three positions
    before it is dropped. A pass that filters a chosen position can only ever
    delete.

    Returns (html, x0, y0, w, h) or None. The box is returned because the
    country map sorts labels by depth and drops the ones that collide, and
    it cannot do that against a position it did not choose.
    """
    pad, ch, up, down = LABEL_METRICS[metric]
    wide = pad + len(name) * ch
    # A destination's name goes beside its dot; a REGION's name goes over the
    # middle of its destinations, because that is what it is naming — the
    # group, not a point. Same four positions, different first choice.
    if prefer == "over":
        order = ((px, py, "middle"), (px, py + off + 12, "middle"),
                 (px + off, py + 4, "start"), (px - off, py + 4, "end"))
    else:
        order = ((px + off, py + 4, "start"), (px - off, py + 4, "end"),
                 (px, py + off + 8, "middle"), (px, py - off - 1, "middle"))
    # `fits` IS A PARAMETER BECAUSE ONE FAMILY IS NOT CUT BY AN ARCH. Every
    # plate on this site is, so the default is the aperture and nothing else
    # passes anything. The homepage hero is cut by the HERO's arch rather than
    # by one inside its own drawing, and the drawing is inset within it, so
    # testing the map's own box as an ellipse would reject names that are
    # plainly visible — Iceland's, for one.
    fits = fits or (lambda x, y, wide, anchor:
                    label_fits(x, y, wide, anchor, vw, vh, up, down))
    for x, y, anchor in order:
        if not fits(x, y, wide, anchor):
            continue
        box = _label_box(x, y, wide, anchor, up, down)
        if clears is not None and not clears(*box):
            continue
        # ALWAYS EXPLICIT, even for "start". `.countrymap .rlabel text`
        # sets `text-anchor: middle` in CSS, and a presentation attribute
        # loses to a stylesheet rule — so omitting it on the default case
        # would have the region names silently centred on a box computed
        # for a left-anchored one.
        a = f' text-anchor="{anchor}"'
        if wrap:
            return (wrap(a, x, y, name), *box)
        return ((f'<text class="{cls}"{a} x="{x:.1f}" y="{y:.1f}">'
                 f'{esc(name)}</text>'), *box)
    return None


def place_label(px, py, name, vw, vh, cls="minilabel here", off=10.0,
                prefer="beside"):
    got = place_label_box(px, py, name, vw, vh, cls, off, prefer)
    return got[0] if got else ""


def hit_radius(pts, vw, cap=34.0, floor=6.0):
    """The largest touch target these dots can carry without overlapping.

    A DOT ON A MAP IS A LINK, AND IT WAS 3.9 PIXELS WIDE.

    The visible circle is r=5.5 in a 1000-unit viewBox, which on a 358px
    phone renders at 3.9px across. WCAG 2.2 AA puts the floor at 24. The
    suite already checked the thumb bar's five items and nothing else, so 130
    links on /beyond-the-obvious, 12 on a destination page and 345 on /map
    were never looked at.

    Enlarging the DRAWN dot would destroy the map, so the target is a
    transparent circle behind it, and its size is not a constant: it is half
    the distance to the nearest other dot, so two neighbours can never steal
    each other's tap. Where that is small the map is dense, the target stays
    small, and the honest answer is the list of the same places underneath —
    which is on every page that draws one of these maps, and which the
    caption points at.

    `cap` is 34 units, the radius that renders at 24px at 390.
    """
    if len(pts) < 2:
        return cap
    near = cap * 2
    for i, a in enumerate(pts):
        for b in pts[i + 1:]:
            d = math.hypot(a[0] - b[0], a[1] - b[1])
            if d < near:
                near = d
    return max(floor, min(cap, near / 2.0))


# The phone rule enlarges a sparse map's labels from 11 units to 26 (see the
# stylesheet). That is the ratio the boxes grow by, and the build has to know
# it because only the build can decide which names survive the larger size.
PHONE_LABEL_SCALE = 26.0 / 11.0


def phone_declutter(placed, reserve=(), frame=None):
    """Which of these labels still fit once a phone enlarges them.

    ENLARGING THE TYPE BROKE THE RULE THAT PLACED IT.

    Labels are positioned at build time against boxes measured at 11 units,
    and commit 38 made a phone draw them at 26 so they resolve into glyphs at
    all. Nothing re-ran the collision pass at the new size: measured across
    every page that draws a labelled map, at 390px, **434 overlapping pairs
    on 275 of 815 pages** — "Hallstatt" through "Berchtesgaden" by 49px,
    "Andorra la Vella" through "Madriu-Perafita-Claror" by 91.

    A fix that shrinks the type back is the original defect; one that drops
    every label is worse than the collision. So the boxes are re-tested here
    at the phone's scale, growing about each label's own anchor, and the ones
    that lose are marked `wide-only` — they keep their place and their size
    on a wide screen and are not drawn on a narrow one. The dot, the <title>
    and the row below survive either way, as they do for a collision.

    `placed` is [(html, x0, y0, w, h)] or [(html, x0, y0, w, h, scale)];
    returns the html, in order.

    THE SCALE IS PER LABEL BECAUSE ONE FAMILY DOES NOT TAKE THE PHONE RULE.
    A country plate's own name is set in `--t-lg`, a length in the viewBox
    rather than a `--z`-compensated one, so it is the same size on a phone as
    on a desk and a box grown by 2.36 about it is a box around nothing. Every
    other family here does take the rule, which is why the default is it.
    """
    # A BOX THIS PASS MUST KEEP OUT OF AND NEVER DROP. The scale bar is placed
    # by arithmetic rather than by the placement rule, so it is not in
    # `placed` and cannot lose; the destination plate has seeded it as a
    # zero-markup entry since the day the bar was added and `pointsmap` never
    # did. It matters now the bar's own type takes the phone enlargement.
    # AND THE APERTURE IS NOT A FIXED SIZE EITHER. `place_label_box` tests
    # every candidate position against the real curve at the size the build
    # draws it; this pass then multiplies that box by 2.36 and only ever
    # asked whether it now hits ANOTHER label. So the moment a family's type
    # actually took the phone enlargement, "Vienna & the East" grew off the
    # right-hand side of its own frame and was sliced by the arch — which is
    # the defect place_label_box exists to prevent, arriving one pass later.
    # A name that no longer fits the opening loses it exactly as a colliding
    # one does: it keeps its dot, its <title> and its row below.
    kept, out = list(reserve), []
    # THE SAME CLEARANCE EVERY OTHER PASS KEEPS, scaled with the boxes. This
    # tested bare overlap, so two names could be placed touching: measured at
    # 390 px, four plates had a pair meeting by up to two pixels. Not visible,
    # and not a number to leave in a check's tolerance either — a threshold
    # that forgives two pixels forgives the next regression that lands on
    # two.
    for item in placed:
        html, x0, y0, w, h = item[:5]
        scale = item[5] if len(item) > 5 else PHONE_LABEL_SCALE
        clear = LABEL_CLEAR * scale
        cx, cy = x0 + w / 2.0, y0 + h / 2.0
        bw, bh = w * scale, h * scale
        box = (cx - bw / 2.0 - clear, cy - bh / 2.0 - clear,
               bw + 2 * clear, bh + 2 * clear)
        clash = any(box[0] < k[0] + k[2] and k[0] < box[0] + box[2]
                    and box[1] < k[1] + k[3] and k[1] < box[1] + box[3]
                    for k in kept)
        if not clash and frame is not None and scale > 1.0:
            fw, fh = frame
            clash = not all(
                in_arch(cx_, cy_, fw, fh)
                for cx_ in (box[0], box[0] + box[2])
                for cy_ in (box[1], box[1] + box[3]))
        if clash:
            # ANY LABEL, NOT ONLY A PLACE NAME. This matched `class="minilabel`
            # and nothing else, so the physical names added later — a peak, a
            # range, a sea — went through this pass, were measured, lost, and
            # were drawn anyway. Chamonix at 390px printed "Monte Rosa
            # 4,634 m" through its own name, one commit after the pass that
            # added the peak and one commit after the pass that fixes exactly
            # this. Marking the first `class="` covers every label family and
            # the wrapped ones too, and `.minimap .wide-only` matches any
            # element, so a wrapper is as good a place to carry it as a text.
            out.append(html.replace('class="', 'class="wide-only ', 1))
        else:
            kept.append(box)
            out.append(html)
    return out


def dense_class(markup):
    """Does this map draw more names than a phone can enlarge?

    Counted from the EMITTED markup rather than from a list, because the
    three map families each had a different idea of what "labels" meant:
    pointsmap held placed labels, the country map held a priority-sorted
    list before collisions dropped from it, and the destination map held
    candidates. Marking density from those gave a country map with three
    visible names the same treatment as a continental one with forty-one.
    Six or fewer names can be drawn at 26 units on a phone; more cannot.
    """
    # AND THE PHYSICAL NAMES COUNT. They are labels a phone has to enlarge
    # exactly as it enlarges a place name, and counting only `.minilabel`
    # called a map with six towns and four mountains sparse — so all ten were
    # scaled up on a 390px screen and two of them collided.
    names = sum(markup.count(f'<text class="{c}') for c in
                ("minilabel", "peakname", "fname", "sname", "rname",
                 "gname"))
    return "" if names <= 6 else " dense"


def pointsmap(pts, uid, caption, aria, want=2.6, pad_frac=0.18, pad_min=24,
              min_w=120.0, min_h=75.0, line=False, extra="", relief=False,
              note="", highlight=None):
    """A set of places on the continent, through the aperture.

    `pts` is [(x, y, href, name)] in projection space. Extracted from
    storymap() when the region pages needed exactly the same picture — a
    handful of destinations, framed to fit, with the land under them — and
    the alternative was a second implementation of the framing, the clamp,
    the unit normalisation and the label collision rule, which is how two
    maps of the same atlas start disagreeing about where Bergen is.
    """
    # A POINT OUTSIDE THE PROJECTION IS NOT A POINT THIS MAP CAN DRAW.
    #
    # Longyearbyen is at 78.2°N and the projection stops at 71.5. Svalbard's
    # region map put its one destination at y = -317 on a frame that starts
    # at 0 — an invisible dot, a map of an empty sea, and nothing anywhere
    # saying a place was missing. The country map for Norway has always
    # handled this ("1 outside this frame: Longyearbyen") and the region map
    # inherited none of it.
    #
    # So the frame is built from the points it can actually contain, and
    # anything dropped is named in the caption rather than silently absent.
    # Found by asserting that every dot lands inside its own viewBox: one of
    # 130 region maps failed, and no rendering of the other 129 would have
    # shown it.
    off = [p for p in pts if not (0 <= p[0] <= MAP_W and 0 <= p[1] <= MAP_H)]
    pts = [p for p in pts if p not in off]
    if not pts:
        # Svalbard's only destination is its only point, and it is north of
        # the projection. Returning "" left the page with no map and no
        # explanation, which reads as a missing feature rather than as a
        # stated limit — so the absence says why it is absent.
        names = ", ".join(esc(p[3]) for p in off)
        return (f'<p class="sourcenote">No map: {names} '
                f'{"lies" if len(off) == 1 else "lie"} beyond the northern '
                f'edge of the projection this atlas draws, and a map without '
                f'the place on it would be a map of the wrong thing. '
                f'<a href="/map">The full map →</a></p>')
    if off:
        names = ", ".join(esc(p[3]) for p in off)
        caption += (f' {len(off)} outside this frame: {names} — beyond the '
                    f'northern edge of the projection this atlas draws.')
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    # PADDING IN PROPORTION TO THE SUBJECT, NOT IN ABSOLUTE UNITS.
    #
    # A flat 90 was larger than the Carpathian Arc: its six stops span 106
    # projection units, so 90 on each side put three-quarters of the frame
    # outside the route before the aspect fit had done anything. Breathing
    # room is a ratio; a floor keeps two places forty kilometres apart from
    # being drawn at street scale.
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    pad = max(pad_min, span * pad_frac)
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    # THE FLOOR, AND WHY IT POINTS THE OPPOSITE WAY FOR TWO KINDS OF MAP.
    #
    # A route has extent and IS the subject, so a frame much larger than it
    # buries it: the Alpine Grand Tour's six stops filled 12% of their own
    # map. A one-destination region has no extent at all, and the subject is
    # then the CONTEXT — Tyrol drawn at 250 km across is one dot in a tangle
    # of frontier lines that could be anywhere in the Alps.
    #
    # Measured both ways rather than argued: dominant-axis fill across the
    # 17 routes runs 36/63/82% (min/median/max) at this default, and the
    # region maps pass a much larger floor for the opposite reason. The
    # metric that first said regions were fine was itself wrong — it counted
    # every <circle> on the page, and every destination card carries a plate
    # with a moon in it.
    # AND THE FLOOR EXPANDS AROUND THE CENTRE, NOT FROM THE ORIGIN.
    # `w = max(min_w, x1 - x0)` left x0 alone, so a frame that had to grow
    # to the floor grew east and south only: Innsbruck, the single stop in
    # Tyrol & the West, sat 25% from the left edge and 15% from the top of
    # its own map. Rendering found it; the numbers said the frame was the
    # right size and never asked where it was.
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    # THE FLOOR IS ONE NUMBER AT THE TARGET PROPORTION, BECAUSE TWO WERE ONE.
    #
    # It used to be `min_w` and `min_h` applied independently, and the aspect
    # pass below then recomputes the width from the height — so whenever
    # `min_h * want` exceeded `min_w`, the width floor was DEAD and the
    # height floor silently decided both. It always did. The region map asked
    # for 260 x 165 with a comment reading "roughly 1,100 x 700 km" and
    # shipped 429 x 165, which is 2,916 x 1,087 km at 47°N: two and a half
    # times the width the comment states, on all 129 region maps.
    #
    # And 429 units is wider than the padded span of every region in the
    # atlas, so all 129 drew the IDENTICAL window with only the translate
    # differing — a family whose caption says "its N destinations" and whose
    # picture was the same quarter of Europe each time. "Framed to fit" was
    # not happening at all, and no count could see it: the viewBox is 1000
    # wide on every one of them, and the frame is in the transform.
    #
    # A CALLER'S FLOOR HAS TO BE A FRAME AT `want`, OR IT IS NOT THE FLOOR IT
    # LOOKS LIKE. The fix is at the call site rather than here: deriving the
    # height from the width for everybody changes the TALL frames too — a
    # narrow, tall route grows by GROW_MAX of its own width, so raising the
    # width floor widens it even when it was never at the floor, and four
    # journeys silently lost their relief to `TERRAIN_MAX_KM` the first time
    # this was tried. The two floors stay independent, and a caller that
    # wants a particular frame states both at the target proportion.
    w, h = max(min_w, x1 - x0), max(min_h, y1 - y0)
    x0, y0 = cx - w / 2.0, cy - h / 2.0
    # ONE PROPORTION ACROSS EVERY MAP OF THIS KIND, or the family has no
    # signature. The bounding box of two places 50 km apart is nearly square;
    # the box of five languages across a continent is a letterbox. Left
    # alone, the arch over each would be a different arch, and the reader
    # would never see that they are the same aperture. The SHORT axis grows,
    # which only ever adds context and never crops a place out.
    # AND THE TARGET MAY NOT COST THE SUBJECT ITS SCALE.
    #
    # A fixed 2.6:1 is right for a spread and catastrophic for a compact
    # one. Measured across the seventeen journey routes after the frames
    # were normalised: the Alpine Grand Tour occupied 12% of its own map's
    # width, the Carpathian Arc 11%, Arctic to the Baltic 13% — six valleys
    # in four countries drawn as three dots lost between Brittany and
    # Hungary. The aspect was being bought with the entire legibility of the
    # picture.
    #
    # So the short axis may grow, and may not grow without limit: GROW_MAX
    # of the padded bounding box. The aspect then lands anywhere between the
    # subject's own shape and the target, which is a range the arch survives
    # — a rounder head over a compact route is still a doorway, and a route
    # you can see is not optional.
    GROW_MAX = 1.7
    if w / h < want:
        w2 = min(h * want, w * GROW_MAX)
        x0, w = x0 - (w2 - w) / 2.0, w2
    elif w / h > want:
        h2 = min(w / want, h * GROW_MAX)
        y0, h = y0 - (h2 - h) / 2.0, h2
    # AND THEN CLAMPED TO THE WORLD THE PROJECTION DRAWS.
    #
    # Widening a nearly-square frame to 2.6:1 once put it at x = -173..1374
    # on a canvas that is 0..1000, so 400px of it were outside the dataset
    # and Natural Earth's own eastern limit drew as a hard vertical line
    # through empty black. It looks like a rendering fault and is in fact a
    # frame asking for land that was never in the file. The frame slides back
    # inside the canvas, and where the aspect it wants will not fit at all it
    # gives up the aspect rather than the land.
    if w >= MAP_W:
        x0, w = 0.0, float(MAP_W)
    else:
        x0 = min(max(x0, 0.0), MAP_W - w)
    if h >= MAP_H:
        y0, h = 0.0, float(MAP_H)
    else:
        y0 = min(max(y0, 0.0), MAP_H - h)
    # ONE UNIT SYSTEM, or the type changes size per page. These frames run
    # from 390 projection-pixels wide to the full 1000 and every one is drawn
    # at the same column width, so a viewBox of 390 magnifies an 11px label
    # to 33. Nothing in CSS can correct that — the browser scales the units
    # and the stylesheet only knows the units — so the geometry is scaled
    # into a fixed 1000-wide frame here and one rule sizes every label.
    k = 1000.0 / w
    vw, vh = 1000.0, h * k
    dots, placed, lab = [], [], []
    # A DISTANCE IS NOT A COLLISION, AND THIS FAMILY WAS STILL USING ONE.
    # `abs(px - qx) < vw * 0.10` drops a name that is near another DOT and
    # says nothing about whether the two boxes overlap: it dropped Tirana for
    # being 300 px from Budapest and let "Omodos & the wine villages" run 156
    # px through "Kardamyli & the Mani". Measured across the six families this
    # function draws: 18 overlapping pairs on 16 pages. The country map has
    # had the box test since the day it was written, and the note in
    # CLAUDE.md that a distance is not a collision was written for this same
    # mistake one family over.
    #
    # The box test is the same one every other name on this site gets, and it
    # is applied where a label is PLACED rather than after, so a name that
    # collides where it wants to go tries the other three positions first.
    bar_box = geo.scale_bar_box(vw, vh)

    def _free(lx, ly, lw, lh):
        for qx, qy, qw, qh in [bar_box] + [b[1:] for b in lab]:
            if not (lx + lw + LABEL_CLEAR < qx or lx > qx + qw + LABEL_CLEAR
                    or ly + lh + LABEL_CLEAR < qy or ly > qy + qh + LABEL_CLEAR):
                return False
        return True

    hitr = hit_radius([((x - x0) * k, (y - y0) * k) for x, y, _h, _n in pts], vw)
    for i, (x, y, href, name) in enumerate(pts):
        px, py = (x - x0) * k, (y - y0) * k
        # WHERE IT STARTS, ON A PICTURE OF A JOURNEY. A route line drawn in
        # order carries no direction a reader can see: the Alpine Grand Tour
        # and the same six valleys travelled backwards are the same drawing.
        # Only an ORDERED set gets this — `line` is already the one thing
        # separating "you go to these in this sequence" from "these places
        # make one case", and marking a first stop on a theme map would be
        # asserting an order the data does not have.
        ends = ""
        if line:
            ends = " first" if i == 0 else (" last" if i == len(pts) - 1 else "")
        dots.append(
            f'<a class="minidot here{ends}" href="{href}">'
            f'<circle class="hit" cx="{px:.1f}" cy="{py:.1f}" r="{hitr:.1f}"/>'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5.5"/>'
            f'<title>{esc(name)}</title></a>'
        )
        # Four candidate positions, each tested against the real curve AND
        # against every box already down. A name that fits nowhere free is
        # dropped, not moved: every place keeps its dot, its <title> and its
        # row in the list below.
        # The box comes back too: the phone pass has to re-test it at the
        # larger size the stylesheet draws it at.
        got = place_label_box(px, py, name, vw, vh, clears=_free)
        if got:
            lab.append(got)
    # A ROUTE IS THE SAME PICTURE WITH ONE MORE ELEMENT. `line` draws the
    # order; a theme, a month or a motion has no order and passes False,
    # and that single element is the whole difference between "these places
    # make one case" and "you go to these in this sequence".
    route = ""
    if line:
        d = " ".join(("M" if i == 0 else "L")
                     + f"{(x - x0) * k:.1f} {(y - y0) * k:.1f}"
                     for i, (x, y, _h, _n) in enumerate(pts))
        route = f'<path class="routeline" d="{d}"/>'
    # THE COUNTRY IS THE ONE THING THIS FRAME CAN LIGHT WITHOUT INVENTING A
    # SHAPE. A region has no geometry here on purpose; the country it is in
    # has real polygons, and the highlight is already built. Only the region
    # family passes it — a journey, a story, a theme, a month and a motion
    # each cross several countries, so there is nothing to light.
    ctx, land = geo.landmass(MAPPROJ, (x0, y0, w, h), highlight=highlight)
    # The frame's own latitude span, back out of projection space, so the bar
    # is drawn only where one number is true across the whole picture.
    lat_hi = _lat_at(y0)
    lat_lo = _lat_at(y0 + h)
    bar = geo.scale_bar(MAPPROJ, lat_lo, lat_hi, LCC_MID_LON,
                        1.0 / k, vw, vh)
    # SPARSE OR DENSE, DECIDED HERE, BECAUSE ONLY THE BUILD KNOWS.
    #
    # A label is 11 units in a 1000-unit viewBox, and the browser scales the
    # viewBox to the container — so the RENDERED size is 11 x (width/1000).
    # Measured across four families:
    #
    #     viewport   390   480   704   900  1024  1280
    #     label px   3.9   4.9   7.4   9.4  10.7  12.8
    #
    # Below about 860px it is under 9px, which is not small type, it is type
    # that does not resolve into glyphs. Every phone and most tablets were
    # being shown names nobody can read.
    #
    # CSS cannot fix it alone: there is no non-scaling-text, and the fix
    # depends on how MANY labels a map carries, which only this function
    # knows. A map with two names can afford to draw them at two and a half
    # times the size on a phone; one with forty-one cannot, and its names are
    # in the list underneath the figure on every page that draws it.
    bx, by, bw_, bh_ = bar_box
    bcx, bcy = bx + bw_ / 2.0, by + bh_ / 2.0
    gw, gh = bw_ * PHONE_LABEL_SCALE, bh_ * PHONE_LABEL_SCALE
    lab = phone_declutter(lab, reserve=[(bcx - gw / 2.0, bcy - gh / 2.0, gw, gh)],
                          frame=(vw, vh))
    dense = dense_class("".join(lab))
    # ONE RENDERER FOR EVERY PICTURE. A region, a journey, a story and a
    # motion are all "these places, on the real coastline, through the door",
    # and each used to compose its own SVG. They go through the same stack as
    # the country and destination plates now, so a layer added once lands on
    # all six kinds — which is the whole reason the stack exists.
    #
    # `/map`, `/plan`, `/search` and the country reference map stay graphite:
    # those are INSTRUMENTS, operated rather than looked at, and that is what
    # the two worlds have always meant.
    # RELIEF ON THE ONE FAMILY OF THESE THAT EARNS IT. `pointsmap` draws a
    # region, a story, a motion, a theme, a month and a journey, and only the
    # journey passes `relief` — a journey through the Alps is a picture of
    # crossing mountains, and a motion's map is a picture of a QUERY, where
    # relief would be decoration over an argument. The caller measures it, so
    # this function has no opinion about which places are mountainous.
    frame_km = w * geo.km_per_unit(MAPPROJ, _lat_at(y0 + h / 2), LCC_MID_LON)
    return cartography.plate(
        uid=uid, w=vw, h=vh, proj=MAPPROJ, view=(x0, y0, w, h),
        transform=f"scale({k:.4f}) translate({-x0:.1f},{-y0:.1f})",
        cut_reach=dusk_reach(),
        land=land, context=ctx, relief=relief, frame_km=frame_km,
        route=route, destinations="".join(dots),
        labels="".join(lab) + bar,
        # A CAPTION SAYS WHAT THE PICTURE IS AND A NOTE SAYS HOW IT WAS
        # MADE. `minimap` was given the two tiers and the seven families that
        # draw through here were not, so the same atlas captioned its plates
        # two different ways — and in one of them the coastline credit, the
        # projection's limits and an editorial sentence all read at the same
        # weight. `credited()` appends the relief credit at the end, which is
        # inside the note where the other credits are.
        caption=('<figcaption><span class="capsay">' + caption + '</span>'
                 + (f'<span class="capsrc">{note}</span>' if note else "")
                 + '</figcaption>'),
        figure_class=(f"minimap pointsmap arched atlas{dense}"
                      + (" terrain" if relief else "")),
        aria=esc(aria))


def regionmap(data, c, r):
    """A region as its own destinations, through the door.

    A region page had no map at all, on the one family that IS a grouping of
    places — and the atlas holds no region geometry on purpose: a convex hull
    round Bergen and Alesund labelled "Vestland" would look like an answer
    and be a guess. What it does hold is exactly which destinations belong
    here, so that is what is drawn, which is the same thing the country map
    already says in its caption.
    """
    pts = [(*project(t["lat"], t["lon"]), urls.city(c, r, t), t["name"])
           for t in r["cities"]]
    if not pts:
        return ""
    uid = "rg" + "".join(ch for ch in f'{c["slug"]}{r["slug"]}' if ch.isalnum())[:14]
    # A DOT IN A TANGLE OF FRONTIERS COULD BE ANYWHERE. Twenty-five of the
    # 130 regions hold one destination, so the picture was one mark in 1,100
    # km of unlabelled border. The country is filled now — which is the one
    # shape this atlas really holds at this level — so the caption names it
    # rather than leaving a reader to guess what the lit land is.
    cap = (f'{esc(c["name"])} filled, with the {len(pts)} destination'
           f'{"s" if len(pts) != 1 else ""} {esc(r["name"])} holds. The region '
           f'is those places, not a boundary — this atlas deliberately holds '
           f'no line round them.')
    note = (f'Coastline from <a href="/sources">Natural Earth</a>, '
            f'public domain. <a href="/map?c={esc(c["slug"])}">Open '
            f'{esc(c["name"])} on the full map →</a>')
    # A REGION NEEDS THE COUNTRY AROUND IT, NOT A CLOSE-UP OF ITSELF.
    # Tyrol & the West holds one destination; at the default floor that is a
    # single dot in 250 km of unlabelled frontier line, which could be
    # anywhere in the Alps. 170 units is about 1,120 km at 47°N — enough for
    # a coast or a recognisable border to appear and place it, and it is the
    # figure this comment has always named. What shipped was 429 units and
    # 2,916 km: the floor was 260 x 165 and the aspect pass recomputes the
    # width from the height, so `min_w` was DEAD and 165 x 2.6 decided both.
    # Stated at the target proportion the aspect pass has nothing to do.
    return pointsmap(pts, uid, cap, note=note, aria=f'Map of {r["name"]}, {c["name"]}: its '
                     f'{n_of(len(pts), "destination")} in the Atlas, '
                     f'with {c["name"]} filled',
                     min_w=170.0, min_h=170.0 / 2.6, highlight=c["slug"])


def storymap(data, s):
    """Where a story happens, drawn on the continent.

    This replaced a generated plate, and the plate was not merely weak here —
    it was WRONG. "The last forest that was never cut" is about Bialowieza,
    the one primeval forest in Europe that has never been logged, and it
    opened with 1260x540 of tower blocks. The motif comes from the hash of
    the seed when no motif is passed, and a story passes none, so the picture
    at the top of every essay was an illustration of nothing, chosen by
    chance, occasionally contradicting the first sentence beneath it.

    A plate is a landscape for a PLACE, derived from what that place is. A
    story is not a place. It is a claim about several of them — and this
    atlas knows exactly which, because `places` is validated against the
    city index and the margin note beside the text already lists them.

    So the opening image is the geography the story is about: the same
    projection as /map, the real coastline under it, its places lit and
    named, seen through the same doorway as every other map on the site. It
    cannot be wrong about the subject, because it is derived from it.

    Nine stories, two to five places each. Where a story names none there is
    no map, on the destination page's rule: a photograph if the register
    holds one, and where it does not, nothing in its place.
    """
    idx = data["cities"]
    pts, names = [], []
    for cid in s.get("places") or ():
        n = idx.get(cid)
        if not n:
            continue
        x, y = project(n["city"]["lat"], n["city"]["lon"])
        pts.append((x, y, urls.city(n["country"], n["region"], n["city"]),
                    n["city"]["name"]))
        names.append(n["city"]["name"])
    if not pts:
        return ""
    where = (names[0] if len(names) == 1
             else ", ".join(names[:-1]) + " and " + names[-1])
    uid = "st" + "".join(ch for ch in s["slug"] if ch.isalnum())[:14]
    # The full attribution is five dataset names joined by "and" — it runs to
    # two lines under the map and buries the one thing the caption is for,
    # which is naming the places. The register is the honest form of that
    # sentence and it is one click away, so the caption points at it rather
    # than reciting it.
    cap = f'Where this happens: {esc(where)}.'
    note = (f'Coastline and borders from '
            f'<a href="/sources">Natural Earth</a>, public domain. '
            f'<a href="/map">The full map →</a>')
    return pointsmap(pts, uid, cap,
                     f'Map of where {s["title"]} happens: {where}', note=note)


def routemap(data, j):
    """The journey drawn on the continent, in order.

    THE LABELS WERE THREE TIMES TOO BIG, ON EVERY JOURNEY WITH A SHORT
    ROUTE. This function used to build its own viewBox in raw projection
    units, so the Alpine Grand Tour — 509 km end to end — got a frame about
    330 units wide, rendered at the full column width, and every 11px label
    came out at 34: "Lauterbrunnen" straight through "Chamonix", both of
    them larger than the h2 below. Nothing in CSS can correct it, because
    the browser scales the units and the stylesheet only knows the units.
    That is the same defect pointsmap() was built to fix for the story maps,
    and the fix is to stop having two implementations of the same picture.

    A route is that picture with one more element: the line. Passing
    line=True is now the entire difference between a journey and a theme —
    which is exactly right, because the difference between them IS the
    order.

    The stops became links on the way through, which they were not before:
    every dot on every other map on this site opens the place it marks.
    """
    idx = data["cities"]
    pts = []
    for leg in j["legs"]:
        n = idx[leg["city"]]
        pts.append((*project(n["city"]["lat"], n["city"]["lon"]),
                    urls.city(n["country"], n["region"], n["city"]),
                    n["city"]["name"]))
    uid = "rt" + "".join(ch for ch in j["slug"] if ch.isalnum())[:14]
    cap = ('Straight lines between stops, in order, ending at the hollow dot '
           '— the order is real, the lines are not routes.')
    note = ('Coastline from <a href="/sources">Natural Earth</a>, public '
            'domain. <a href="/map">The whole map, with every journey →</a>')
    # A JOURNEY DRAWS RELIEF IF ANY OF ITS STOPS DOES. A route is one picture
    # of one crossing, and "this journey goes into the mountains" is what the
    # map is for; requiring every stop to qualify would drop the Alpine Grand
    # Tour because it starts in a valley town. The frame cap below is what
    # stops that becoming a physical map of Europe.
    rel = any(cartography.draws_relief(cartography.relief_of(k)) for k in (
            f'{idx[leg["city"]]["country"]["slug"]}/'
            f'{idx[leg["city"]]["region"]["slug"]}/'
            f'{idx[leg["city"]]["city"]["slug"]}' for leg in j["legs"]))
    return pointsmap(pts, uid, cap, f'Route map for {j["name"]}',
                     line=True, relief=rel, note=note)


# ── destination facets ────────────────────────────────────────────────
#
# The specification asks for /europe/norway/bergen/things-to-do and its
# siblings as a programmatic SEO channel. It also warns, in the same
# document, against creating thousands of thin pages. Both are right, so a
# facet only exists where there is enough material to justify it — the
# thresholds below are the whole policy.

HISTORY_KINDS = ("castle", "church", "monastery", "archaeological-site", "monument",
                 "ruin", "theatre", "bridge", "quarter", "library", "bath")
FOOD_KINDS = ("market",)
FOOD_EXP_KINDS = ("table", "cellar")
HISTORY_EXP_KINDS = ("museum", "sacred")

# Three. Below it, the page is a heading with a list under it that a reader
# could have seen in full on the destination page they came from.
FACET_MIN = 3


def facets_for(data, c, r, t):
    """Which facet pages this destination has earned, and their contents."""
    places = t.get("places", [])
    exps = t.get("experiences", [])
    cid = f"{c['slug']}/{r['slug']}/{t['slug']}"
    b = data["back"][cid]
    out = {}

    # ONE THRESHOLD, AND IT IS THE ONE THE PAGES THEMSELVES CLAIM.
    #
    # Every facet page ends with a note reading "a facet with two entries is
    # a thin page wearing a heading". It was printed on 76 pages that had two
    # entries or one. Measured across all 137:
    #
    #     food          42 pages, median 1 entry, ALL 42 under three
    #     journeys      61 pages, median 2,       34 under three
    #     things-to-do  26 pages, median 5,        0
    #     history        8 pages, median 3,        0
    #
    # The thresholds were 1, 2, 4 and 3 — four numbers, no policy, and two of
    # them below the line the pages print. "Food & markets in Siena" with one
    # row is the thin page the specification warns about in the same document
    # that asks for the SEO channel, and it is worse than absent because a
    # reader who follows a heading and finds one row learns that headings
    # here mean nothing.
    #
    # FACET_MIN is three for all four. 137 pages become 61, the note becomes
    # true, and nothing is orphaned: every row on every removed page is still
    # on the destination page it came from.
    food_exps = [e for e in exps if e["kind"] in FOOD_EXP_KINDS]
    food_places = [pl for pl in places if pl["kind"] in FOOD_KINDS]
    hist_places = [pl for pl in places if pl["kind"] in HISTORY_KINDS]
    hist_exps = [e for e in exps if e["kind"] in HISTORY_EXP_KINDS]
    candidates = {
        "things-to-do": (len(places) + len(exps), {"places": places, "exps": exps}),
        "food": (len(food_exps) + len(food_places),
                 {"places": food_places, "exps": food_exps}),
        "history": (len(hist_places) + len(hist_exps),
                    {"places": hist_places, "exps": hist_exps}),
        "journeys": (len(b["journeys"]) + len(b["themes"]) + len(b["stories"]), b),
    }
    for key, (n, payload) in candidates.items():
        if n >= FACET_MIN:
            out[key] = payload
    return out


def subs_with_a_page(data, cat):
    """The sub-categories of this category that have earned a page of their own.

    THE DESTINATION FACETS GOT A FLOOR AND THE SUB-CATEGORIES NEVER DID, AND
    TWO OF THE TWENTY-EIGHT SHIPPED ONE ROW. `FACET_MIN` is three, and its
    reason is written above it: below that the page is a heading over a list
    a reader could have seen in full on the page they came from. That is
    exactly true here — `/experiences/<cat>` lists every invitation the
    category holds, so a sub with one entry shows nothing the parent did not.

    **And the smaller of the two was worse than thin: it contained none of
    what its heading names.** `/experiences/nature/fjords` declares five
    keywords — fjord, inlet, calanque, ria, sea loch — and **no experience in
    this atlas mentions a fjord at all**, so the page called Fjords held one
    entry and it was Marseille, matched on `calanque`. A reader arriving from
    a search for fjords got a French Mediterranean inlet. The keyword is not
    the fault and is kept: a calanque is a drowned valley and the
    classification is editorial. The fault is publishing a page for a subject
    the atlas holds nothing of, which is what a floor is for.

    `/experiences/history/renaissance` is the other, one entry, Lucca.

    The floor is `FACET_MIN` READ rather than a third three typed — the
    dispatch cap's own lesson, where four copies of one number disagreed and
    a sitting was spent before anything said so.
    """
    from . import categories as C
    from .data import all_experiences
    items = all_experiences(data["countries"])
    return [sb for sb in cat.get("subs", [])
            if len(C.select(items, cat, sb)) >= FACET_MIN]


def facet_page(data, c, r, t, key, payload):
    name = urls.FACETS[key]
    facetart = ""
    rows = []
    if key == "journeys":
        for j in payload["journeys"]:
            leg = next(l for l in j["legs"] if l["city"] == f"{c['slug']}/{r['slug']}/{t['slug']}")
            rows.append((urls.journey(j), j["name"], leg["why"], f"{j['days']} days"))
        for th in payload["themes"]:
            stop = next(x for x in th["stops"] if x["city"] == f"{c['slug']}/{r['slug']}/{t['slug']}")
            rows.append((urls.theme(th), th["name"], stop["why"], "Theme"))
        for st in payload["stories"]:
            rows.append((urls.story(st), st["title"], st["standfirst"], st["reading"]))
        lede = (f"Every curated route, theme and story in the Atlas that passes through "
                f"{t['name']}. None of them was written to fill this page.")
        # THE ONE FACET WHOSE SUBJECT IS A SHAPE, AND IT DREW NOTHING.
        #
        # `docs/signature-moments.md` refuses a map on this family, and the
        # reason is exact: a facet exists to be left quickly and must not
        # repeat its parent's map. This is not the parent's map. The parent
        # draws a locator — where Vienna is — and this page's subject is
        # every route that passes THROUGH Vienna, which is five different
        # lines converging on one point and is the only thing on the page a
        # sentence cannot carry.
        #
        # ONE drawing for all of them, which is the /journeys opening scoped
        # to a place: five framed thumbnails would be five pictures of the
        # same continent. The casings are drawn before the cores, all of
        # them, because a per-route casing lays the next route's pale stroke
        # over the last route's cobalt one and every crossing becomes a
        # break — the rule pages.route_line() exists for.
        idx = data["cities"]
        routes, allpts = [], []
        for j in payload["journeys"]:
            pts = [project(idx[l["city"]]["city"]["lat"], idx[l["city"]]["city"]["lon"])
                   for l in j["legs"] if l["city"] in idx]
            if len(pts) > 1:
                routes.append(pts)
                allpts.extend(pts)
        here = project(t["lat"], t["lon"])
        if routes:
            allpts.append(here)
            lines = ("".join(f'<polyline class="constel-route case" points="'
                             + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '"/>'
                             for pts in routes)
                     + "".join(f'<polyline class="constel-route" points="'
                               + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '"/>'
                               for pts in routes))
            facetart = (
                f'<figure class="facetart">'
                f'<svg class="constel allroutes" viewBox="{glyph_view(allpts)}" '
                f'role="img" aria-label="The '
                f'{n_of(len(routes), "route")} in the Atlas that pass through '
                f'{esc(t["name"])}">'
                f'<use href="#constel-eu"/>{lines}'
                f'<g class="constel-lit"><circle cx="{here[0]:.0f}" '
                f'cy="{here[1]:.0f}"/></g></svg>'
                f'<figcaption><span class="capsay">'
                f'{n_of(len(routes), "curated route")} through '
                f'{esc(t["name"])}, drawn end to end on the same projection as '
                f'every other map here.</span><span class="capsrc">'
                f'{geo.sources_line(geo.load("europe-lod0.json"))}</span>'
                f'</figcaption>'
                f'</figure>')
    else:
        for pl in payload["places"]:
            rows.append((urls.place(c, r, t, pl), pl["name"], pl["summary"],
                         f"{PLACE_KIND_NAMES[pl['kind']]} · {pl['duration']}"))
        kinds = data["taxonomy"]["experience_kinds"]
        for e in payload["exps"]:
            rows.append((urls.city(c, r, t) + "#things-to-do", e["name"], e["summary"],
                         f"{kinds[e['kind']]} · {e['band']}"))
        lede = {
            "things-to-do": f"Everything in the Atlas for {t['name']}: places to see and things to do, in one list.",
            "food": f"What {t['name']} puts on a table, and where. Country-wide dishes are on the {c['name']} page.",
            "history": f"The layers you can actually stand in — {t['name']}'s built and excavated history.",
        }[key]

    rowhtml = "".join(
        f"""<a class="row" href="{esc(href)}"><div><h2>{esc(title)}</h2>
        <p class="rowsub">{esc(sub)}</p></div><p class="rowmeta">{esc(meta)}</p></a>"""
        for href, title, sub, meta in rows
    )
    extra = ""
    if key == "food":
        extra = section(
            f"Across {c['name']}",
            '<ul class="stack">' + "".join(f"<li>{esc(x)}</li>" for x in c["food"]) + "</ul>",
            lede="Dishes that belong to the country rather than to this destination.")
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (c["name"], urls.country(c)),
         (r["name"], urls.region(c, r)), (t["name"], urls.city(c, r, t)), (name, None)])}
<div class="pagehead index">
  <p class="kicker">{esc(t['name'])}, {esc(c['name'])}</p>
  <h1>{esc(name)} in {esc(t['name'])}</h1>
  <p class="lede">{esc(lede)}</p>
</div>
{constel_defs() if facetart else ""}
{facetart}
<div class="rows">{rowhtml}</div>
{extra}
<div class="note mt7">
  <p>This page exists because {t['name']} has at least {FACET_MIN} of them in the Atlas.
  Destinations with fewer do not have a page for this, on purpose — a facet with one or two
  entries is a heading with a list under it that you could have read in full on the page you
  came from. <a href="{urls.city(c, r, t)}">Back to {esc(t['name'])}</a>.</p>
</div>
"""
    return f"{urls.facet(c, r, t, key)}/index.html", page(
        f"{name} in {t['name']}", body, path=urls.facet(c, r, t, key), area="countries",
        description=f"{name} in {t['name']}, {c['name']}: {len(rows)} entries from the EuropeDoor Atlas.",
    )


# ── places ────────────────────────────────────────────────────────────

EVENT_KIND_NAMES = {
    "festival": "Festival", "concert": "Music", "sport": "Sport",
    "exhibition": "Exhibition", "religious": "Religious", "cultural": "Cultural",
    "food": "Food", "market": "Market", "seasonal": "Seasonal",
}

PLACE_KIND_NAMES = {
    "museum": "Museum", "gallery": "Gallery", "castle": "Castle",
    "palace": "Palace", "church": "Church", "mosque": "Mosque",
    "synagogue": "Synagogue", "lake": "Lake",
    "monastery": "Monastery", "mountain": "Mountain", "waterfall": "Waterfall",
    "beach": "Beach", "monument": "Monument", "archaeological-site": "Archaeological site",
    "park": "Park", "viewpoint": "Viewpoint", "bridge": "Bridge", "market": "Market",
    "garden": "Garden", "island": "Island", "cave": "Cave", "street": "Street",
    "square": "Square", "lighthouse": "Lighthouse", "quarter": "Quarter",
    "ruin": "Ruin", "theatre": "Theatre", "library": "Library", "bath": "Baths",
}
SEASON_NAMES = {
    "year-round": "Open year-round", "summer": "Summer only",
    "winter": "Winter only", "spring-autumn": "Spring and autumn",
    "weather-dependent": "Weather-dependent",
}


def place_page(data, c, r, t, pl):
    """A single point of interest.

    The specification's field list includes opening hours, prices and an
    official website. This page holds none of them, and says so instead of
    guessing: those are the three fields that go stale fastest and the three
    a traveller is most damaged by being wrong about."""
    # The §2.5 edge, read from the destination's own experiences. A place
    # page could not previously say what there is to DO here — places and
    # experiences sat side by side under a destination with nothing joining
    # them. The Louvre is a place; "Renaissance rooms before the coaches
    # arrive" is an experience that happens in it, and until there was an
    # edge, neither page could mention the other.
    HOW = {"at": "Happens here", "from": "Starts here", "about": "About this place"}
    doing = "".join(
        f"""<a class="row" href="{urls.experience(c, r, t, e)}">
        <div><h3>{esc(e['name'])}</h3><p class="rowsub">{esc(e['summary'])}</p></div>
        <p class="rowmeta">{esc(HOW[link['how']])}</p></a>"""
        for e in t.get("experiences", [])
        for link in e.get("at", []) if link["place"] == pl["slug"]
    )
    others = [x for x in t.get("places", []) if x is not pl]
    cid = f"{c['slug']}/{r['slug']}/{t['slug']}"
    b = data["back"][cid]
    # "JOURNEYS THAT STOP HERE" WAS A CLAIM ABOUT THE PLACE AND THE EDGE IS
    # ABOUT THE DESTINATION. `back[cid]["journeys"]` is every journey with a
    # leg in this TOWN, and this is a place page: the Alpine Grand Tour has a
    # leg in Chamonix and says nothing about the Mer de Glace, so 96 place
    # pages asserted that a route stops at a cable car, a cathedral or a
    # glacier on the strength of it visiting the town. That is an editorial
    # claim manufactured out of a containment fact — the same thing
    # `graph_api` refuses when it declines to derive `stops_at` from the
    # places of a leg's destination, and the same shape as `cell` catching
    # `cellar`: the rule is published honestly and a reader who checked would
    # find it describes something else.
    #
    # The heading names the destination, which is what the edge runs to, and
    # the lede says what is not held. "Journeys through <name>" is the form
    # the region page has always used for the same relation one level up.
    jrows = "".join(
        f"""<a class="row" href="{urls.journey(j)}">
        <div><h3>{esc(j['name'])}</h3><p class="rowsub">{esc(j['strapline'])}</p></div>
        <p class="rowmeta">{j['days']} days</p></a>"""
        for j in b["journeys"]
    )
    # A PLATE THAT KNEW NOTHING ABOUT THE PLACE, 1260x540, AT THE TOP.
    #
    # Bryggen is a row of Hanseatic trading houses on a specific wharf. Its
    # page opened with a generated coastline drawn from the hash of its slug
    # and the interests of the town around it — flat, monochrome, and about
    # nothing. The destination exemplar already measured that the plate
    # cannot carry a hero and removed it from 319 pages; this family kept a
    # bigger one.
    #
    # What replaces it is the only true picture available. This atlas draws
    # in one projection whose finest unit is about four kilometres, so there
    # is no honest map of a building — but there is an honest map of where
    # the building is, and for a reader who arrived here from a search that
    # is the orientation they lack. The caption says exactly that, because a
    # map captioned "Bryggen" that is actually a map of Bergen would be the
    # kind of small lie this repository refuses everywhere else.
    # AND THE DRAWING WAS DISCARDED THE DAY A PHOTOGRAPH ARRIVED, WHICH THE
    # PARAGRAPH TWENTY LINES DOWN FORBIDS IN AS MANY WORDS: *THE OPENING
    # KEEPS THE MAP … the strip is where the photographs go.* This was
    # `photograph if has_photo else minimap(...)` — an either/or that threw
    # the map away — and it was invisible while no `place:` purpose was
    # filled. Two photograph batches merged and **forty place pages lost
    # their geography entirely**: no minimap, no arch, no relief, and with
    # them the caption that says *there is no honest map of a building but
    # there is an honest map of where the building is*, which is exactly the
    # orientation a reader who arrived from a search lacks.
    #
    # `head_figure`/`moved_drawing` is the site's own answer and its
    # docstring states it: *the drawing is never lost — the caller emits it
    # below with `moved_drawing()` when a photograph took its place.* The
    # country page honours it, the theme page honours it, the themes index
    # never called it (fixed one commit ago) and **this family is the
    # fourth caller and had its own if/else instead**. A photograph of the
    # building is better in the opening than a map of the town around it, so
    # the photograph stays where `place-hero` declares it and the drawing
    # moves to a band with its caption.
    #
    # The container stays `.card-art frame`, which is what
    # `data/image-purposes.json` declares and what `c_photo_safe_area`
    # measures — the crop box does not move, only what is under it.
    pkey = f"place:{cid}/{pl['slug']}"
    has_photo = bool((data.get("images") or {}).get(pkey))
    placemap = minimap(data, t, span="auto", about=pl["name"])
    placeart = (f'<div class="card-art frame">'
                + picture(data["images"], pkey, w=1260, h=540,
                          alt=f"{pl['name']}, {t['name']}", eager=True,
                          sizes="(min-width: 76rem) 76rem, 100vw")
                + '</div>') if has_photo else placemap
    placewhere = moved_drawing(
        data, pkey, placemap if has_photo else "",
        f"There is no honest map of a building at this atlas's scale — the "
        f"projection's finest unit is about four kilometres — and there is an "
        # NO `esc()` HERE: `section()` escapes its own title and lede, and
        # the first version double-escaped four place names into '&amp;amp;'.
        # `checks.py` caught it in the run that introduced it.
        f"honest map of where {pl['name']} is. The photograph above is the "
        f"place; this is {t['name']} around it.")

    # THE THINNEST PAGE ON THE CONTACT SHEET, AND THIS IS THE FAMILY WITH
    # THE MOST DECLARED SURFACES BEHIND IT. 255 `place:` purposes exist and
    # a place page reached exactly one of them — its own — and only when the
    # register held it. "Other places in Vienna" was five sentences in a
    # column under a facts table, on a page whose subject is a single
    # building somebody is deciding whether to walk to.
    #
    # THE OPENING KEEPS THE MAP. That is not a hole waiting for a picture:
    # this atlas draws in one projection whose finest unit is about four
    # kilometres, so there is no honest map of a building — but there is an
    # honest map of where the building is, and for a reader who arrived from
    # a search that is the orientation they lack. The strip is where the
    # photographs go, and where the ones nobody has licensed say so.
    _pstrip = ed_strip(data.get("images"), [
        {"key": f"place:{cid}/{x['slug']}", "alt": f"{x['name']}, {t['name']}",
         "label": x["name"], "href": urls.place(c, r, t, x),
         # THE SENTENCE THE SECOND BAND USED TO CARRY. Printing this set once
         # as pictures and again as rows was the page saying one thing twice;
         # printing it once without the sentence would be the page saying
         # less. `others` is at most four on any page in this dataset, so the
         # strip's own limit never selects.
         "note": x["summary"]}
        for x in others], limit=8)
    if _pstrip:
        _pstrip = ('<section class="ed-section">'
                   + ed_section_head("Nearby",
                       f"The rest of {t['name']}",
                       f"{n_of(len(others), 'other place')} recorded in the "
                       f"same town, each one its own page.")
                   + _pstrip + "</section>")
    facts = factlist([
        ("Kind", esc(PLACE_KIND_NAMES[pl["kind"]])),
        ("Give it", esc(pl["duration"])),
        ("Season", esc(SEASON_NAMES[pl["season"]])),
        ("Where", f'<span class="mono">{pl["lat"]:.3f}°N, {pl["lon"]:.3f}°E</span>'),
        ("In", f'<a href="{urls.city(c, r, t)}">{esc(t["name"])}</a>'),
    ])
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (c["name"], urls.country(c)),
         (r["name"], urls.region(c, r)), (t["name"], urls.city(c, r, t)), (pl["name"], None)])}
<!-- THE VIEW IS PART OF THE OPENING, AND THIS WAS THE FOURTH FAMILY AND
     THE ONE THAT MISSED IT. The country, the region and the destination all
     bring their drawing inside the head and put the RECORD after it — the
     rule `.headmeta` was named for, whose own comment says "one class, three
     families". A place kept the older order: the name, the sentence, the
     coordinates, and then the picture, so 40 pixels of latitude and longitude
     sat between what a reader came for and the drawing that answers where it
     is, on 255 pages.

     ONE COLUMN, LIKE THE REGION AND UNLIKE THE COUNTRY. Measured at 1280
     the drawing is 1168x467, which is 2.5:1 — the region's own figure, and
     the reason recorded there applies unchanged: a plate that wide cannot
     stand beside the type the way a country's portrait does. -->
{ed_opening(
    eyebrow=f"{PLACE_KIND_NAMES[pl['kind']]} · {t['name']}, {c['name']}",
    title=pl["name"],
    intro=pl["summary"],
    visual=placeart,
    family="arrival")}
<div class="headmeta ed-section">
  <p class="orient">Give it {esc(pl['duration'])} · {esc(SEASON_NAMES[pl['season']])} ·
  <span class="mono">{pl["lat"]:.3f}°N, {pl["lon"]:.3f}°E</span></p>
</div>
{placewhere}

<section class="practical" aria-label="Practical">
  <div>
    <h2 class="mini">Accessibility</h2>
    <p>Not documented. EuropeDoor holds no step-free access, hearing loop or
    accessible toilet information for any place, and inventing it would be
    worse than the gap — <a href="/accessibility">the position in full</a>.</p>
  </div>
  <div>
    <h2 class="mini">Getting there</h2>
    <p>{esc(first_sentence(c['getting_around']))}
    <a href="{urls.country(c)}#getting-around">All of {esc(c['name'])} →</a></p>
  </div>
  <div>
    <h2 class="mini">Up a level</h2>
    <p><a href="{urls.city(c, r, t)}">{esc(t['name'])}</a> ·
    <a href="{urls.region(c, r)}">{esc(r['name'])}</a> ·
    <a href="{urls.country(c)}">{esc(c['name'])}</a></p>
  </div>
</section>

<div>
  <div>
    <!-- THE BOUNDARY AND THE ACTION SIT SIDE BY SIDE, which is the grammar
         the Stay layer already composed and named `.handoff`: a rule, what
         this atlas will not tell you, and the one thing you can do about it.
         Stacked, the note was 600 pixels wide in a 1,168-pixel band with six
         hundred pixels of white beside it and the button alone under it —
         the void this repository has now named five times, on the family the
         contact sheet showed as the emptiest. No new component: a second
         implementation of a two-column band is a second chance to make its
         mistakes. -->
    <div class="handoff">
      <div class="note">
        <h2 class="mini">We do not hold opening hours, prices or a website for this</h2>
        <p>Those are the three fields that go stale fastest and the three you are most damaged
        by being wrong about, so this site does not carry them at all rather than carrying an
        unverified version. Check the operator or the municipality on the day. The estimate of
        how long to give it, and the season, are editorial judgements and are usually stable.</p>
      </div>
      <p><button class="btn ghost" type="button" data-save="place:{esc(cid)}/{esc(pl['slug'])}"
         data-kind="Place" data-label="{esc(pl['name'])}, {esc(t['name'])}"
         data-url="{urls.place(c, r, t, pl)}">Save to My Europe</button></p>
    </div>
    {section("What happens here", f'<div class="rows">{doing}</div>',
             lede="Experiences tied to this place, and how each one is tied to it — "
                  "standing on it, starting from it, or looking at it.") if doing else ""}
    {_pstrip}
    {section("Journeys through " + t["name"], f'<div class="rows">{jrows}</div>',
             lede="These routes have a night in " + t["name"] + ". Whether a "
                  "traveller on one of them comes here is not something this "
                  "atlas holds — no journey leg names its places.") if jrows else ""}
  </div>
</div>
{section("The record", facts, tone="quiet",
         lede="What this atlas holds about " + pl["name"] + ", and nothing "
              "it does not.")}
"""
    return f"{urls.place(c, r, t, pl)}/index.html", page(
        f"{pl['name']}, {t['name']}", body, path=urls.place(c, r, t, pl), area="countries",
        accent="human",
        description=pl["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
        og=(f"place:{c['slug']}:{t['slug']}:{pl['slug']}", motif_for(t["interests"]),
            f"{pl['name']}, {t['name']}"),
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Countries", "/countries"),
                           (c["name"], urls.country(c)), (r["name"], urls.region(c, r)),
                           (t["name"], urls.city(c, r, t)),
                           (pl["name"], urls.place(c, r, t, pl))]),
            # No openingHours, no offers, no aggregateRating. The validator
            # refuses the first, nothing is bookable, and there are no
            # reviews — see the note above ld() in render.py.
            ld_place("TouristAttraction", name=pl["name"], url=urls.place(c, r, t, pl),
                     description=pl["summary"],
                     lat=t["lat"], lon=t["lon"],
                     within=ld_within("TouristDestination", t["name"], urls.city(c, r, t))),
        ],
    )


# ── the score ─────────────────────────────────────────────────────────

_SPREADS = {}


def _spread(kind, data):
    """Memoised, because it is 319 city_scores() and 369 pages ask for it.

    Computed once per build. It is derived from the same functions the pages
    print, so a median tick can never mark a value the site does not produce.
    """
    if kind not in _SPREADS:
        from . import score as S
        _SPREADS[kind] = (S.observed_spread(data["cities"]) if kind == "city"
                          else S.country_spread(data["countries"]))
    return _SPREADS[kind]


def scorebars(scores, spread=None):
    """The eight dimensions, and — since this commit — what they are against.

    EIGHT BARS WITH NOTHING TO COMPARE THEM TO. Bergen reads Nature 97,
    Authenticity 66, Value 54, and a reader has no way to know that 97 is the
    top of the Atlas while 66 is a little above the middle of a dimension
    that never exceeds 82 and 54 is well BELOW a value median of 85. The
    numbers were exact and the meaning was unavailable, which is the same
    fault /method had when it printed one range for all eight.

    So each bar carries a tick at the Atlas median for that dimension. It is
    the same derivation /method publishes, from the same function, so the two
    pages cannot disagree — and it is the cheapest possible answer to "is 66
    good", which is the question every score panel is really asked.

    `spread` is per-family: a country's scores come from a different function
    than a city's, so marking a destination with the country median would
    compare a place against a continent's aggregate under the same tick.
    """
    from .score import DIMENSIONS, LABELS
    rows = "".join(
        f"""<div class="scorerow"><span class="scorelabel">{esc(LABELS[d])}</span>
        <span class="scorebar"><span class="w{scores[d]}"></span>"""
        + (f'<span class="scoremed"><span class="w{spread[d][2]}"></span></span>'
           if spread and d in spread else "")
        + f"""</span>
        <span class="scorenum">{scores[d]}</span></div>"""
        for d in DIMENSIONS
    )
    med = ("" if not spread else
           " The tick on each bar is the median across the whole Atlas, so a bar "
           "short of it is a dimension this place is not for.")
    return f"""<div class="score">
    <p class="kicker">Europe Experience Score</p>{rows}
    <p class="small"><a href="/method">How this is calculated</a> — derived from our own tagging,
    not from measurement. It says what a place is for, not how good it is.{med}</p></div>"""


# ── experiences & the marketplace ─────────────────────────────────────

def country_spread(countries):
    """The countries a list reaches, as the page's own rhythm.

    On this family the spread IS the offer — "Markets" is six markets in six
    countries — and it used to be 11px grey text right-aligned at the end of
    each table row. Nothing here is authored: it is the set of countries in
    the list, in order.
    """
    return '<span class="sep" aria-hidden="true"> · </span>'.join(
        f'<span>{esc(c)}</span>' for c in countries)


def category_page(data, cat, sub=None):
    """A category or sub-category of experience, with its selection rule
    printed on it. A list nobody can reproduce is a list nobody can argue
    with."""
    from . import categories as C
    from .data import all_experiences
    items = all_experiences(data["countries"])
    chosen = C.select(items, cat, sub)
    chosen.sort(key=lambda it: (it["country"]["name"], it["city"]["name"]))

    # The country leads, because the spread across Europe IS the offer on
    # this family: "Markets" is six markets in six countries, and that was
    # 11px grey text right-aligned at the end of a table row. The class is
    # `row exprow` and not a replacement, so the `row` primitive keeps its
    # reach and this family gets its own composition on top of it.
    # AN EXPERIENCE IS AN INVITATION, AND THE WRITING IS THE PICTURE. This
    # list was a four-column table — country, city, name, summary, kind,
    # band — 48 rows deep, everything at one size, so "Bosnian coffee,
    # properly" and "Vermouth where it was invented" were fighting a
    # database layout. The family's only material is the sentence somebody
    # wrote, and the design of this page is that sentence being readable.
    #
    # AND THE KIND IS PRINTED ONLY WHERE IT DISTINGUISHES. On /experiences
    # /food every row said CELLAR & VINEYARD or FOOD & TABLE forty-eight
    # times, which is this atlas's own rule broken by the family that has
    # the longest lists: never explain the constraint back. What every row
    # shares is hoisted above the list; only what differs stays on the row.
    kindsin = {it["exp"]["kind"] for it in chosen}
    kindname = data["taxonomy"]["experience_kinds"]
    # THE PLACE LEADS, AND FOR A YEAR IT WAS THE LAST LINE IN GREY.
    #
    # The comment four paragraphs up says "The country leads, because the
    # spread across Europe IS the offer on this family" — and the markup put
    # the city and country at the BOTTOM of every entry, in 11px uppercase
    # ink-3, under the name and the summary. The list is sorted by country
    # and then by city, so the order a reader is given is alphabetical by a
    # key they cannot see: forty-eight entries in two columns that read as
    # random because the sort key is the least prominent thing on each one.
    #
    # It is a kicker now. Scanning the column gives Vienna, Mostar, Split,
    # Mikulov, Copenhagen, Bordeaux — the order becomes legible, and the
    # first thing a reader gets is the discriminator they are actually
    # scanning for on a page that spans twenty-six countries.
    # AND THE SAME GUARD WAS APPLIED TO ONE OF TWO FIELDS. The paragraph
    # above says the kind is printed only where it distinguishes, and the
    # BAND was printed unconditionally beside it — so /experiences/luxury
    # said "high" on all five of its invitations and /experiences/food said
    # "low" thirty times and "moderate" eighteen, with no "high" anywhere.
    # That is *never explain the constraint back*, in the field next to the
    # one it was written for.
    #
    # AND IT WAS PRINTING THE RAW SLUG. `data/taxonomy.json` gives each
    # budget band a NAME and a note — Frugal, Comfortable, Generous, each
    # with a sentence — and both invite call sites printed `low`,
    # `moderate`, `high`. An enum value is an identifier for a program;
    # every other surface on this site that shows a budget shows the name.
    bandname = {b["slug"]: b["name"] for b in data["taxonomy"]["budgets"]}
    bandnote = {b["slug"]: b["note"] for b in data["taxonomy"]["budgets"]}

    def _invites(part, withband):
        ilvl = "h3" if bgrouped else "h2"
        return "".join(
            f"""<li class="invite"><a href="{urls.city(it['country'], it['region'], it['city'])}">
        <p class="invite-where">{esc(it['city']['name'])}, {esc(it['country']['name'])}"""
            + (f" · {esc(kindname.get(it['exp']['kind'], it['exp']['kind']))}"
               if len(kindsin) > 1 else "")
            + (f" · {esc(bandname.get(it['exp']['band'], it['exp']['band']))}"
               if withband else "")
            + f"""</p>
        <{ilvl}>{esc(it['exp']['name'])}</{ilvl}>
        <p class="invite-sum">{esc(it['exp']['summary'])}</p></a></li>"""
            for it in part)

    # THE LIST HAD NO STRUCTURE AND `tools/monotony.js` SAID SO: 48
    # `.invite` siblings, 4,065 pixels of a 7,142-pixel page, **with no
    # second component at all** — the report's own diagnostic for a page
    # that is a list and nothing else, and the worst figure left on the site
    # once /countries and the motion pages came down.
    #
    # WHAT AN INVITATION COSTS IS THE ONE EXCLUSIVE AXIS THESE RECORDS
    # CARRY. The sub-categories cannot group this list and that refusal is
    # already recorded: six of Food's 48 are in no sub-category and eight
    # are in two, so the grouping would need a bucket the page has no name
    # for and would print some invitations twice. A band is one per record,
    # it is a real decision a reader makes, and the distribution is itself
    # the finding — **nothing in Food & drink or in Culture is generous at
    # all**, 0 of 48 and 0 of 52, where Luxury is 5 of 5.
    #
    # And the group's hoisted line is the taxonomy's own note rather than a
    # sentence written here, so a page cannot describe a band differently
    # from the planner that spends it.
    bandsin = {}
    for it in chosen:
        bandsin.setdefault(it["exp"]["band"], []).append(it)
    order = [b["slug"] for b in data["taxonomy"]["budgets"]]
    bgrouped = len(bandsin) > 1 and all(
        len(v) >= GROUP_MIN for v in bandsin.values())
    if bgrouped:
        # FRUGAL FIRST, WHICH IS THE TAXONOMY'S OWN ORDER rather than
        # largest first. A motion's groups are unordered clauses and take
        # the largest; a budget band is a SCALE, and printing Comfortable
        # above Frugal because there are more of them would be sorting an
        # ordered axis by population.
        rows = "".join(
            f'<section class="invband">'
            f'<h2 class="mini">{n_of(len(bandsin[b]), "experience")}</h2>'
            f'<p class="whyall"><span>{esc(bandname[b])}</span> '
            f'{esc(bandnote[b])}</p>'
            f'<ol class="invites">{_invites(bandsin[b], False)}</ol>'
            f'</section>'
            for b in order if b in bandsin)
    else:
        rows = (f'<ol class="invites">{_invites(chosen, len(bandsin) > 1)}</ol>'
                if chosen else "")
    subcards = ""
    if not sub and cat.get("subs"):
        counts = {sb["slug"]: len(C.select(items, cat, sb)) for sb in cat["subs"]}
        # A CARD IS A CONTAINER FOR SOMETHING, AND THESE HELD A COUNT AND A
        # NAME. Four grey boxes with nothing in them, taking a full band and
        # 150 pixels of the page above the list they narrow. They are what
        # they always were: four links with a number each.
        # AND THE FOUR NUMBERS ARE THE SHAPE OF THE CATEGORY, printed as
        # four numbers. Food & drink is 5 markets, 13 places to eat, 25
        # cellars and 7 producers — half of it is wine — and Nature is 1,
        # 3, 7 and 15. Those are different arguments about what a category
        # IS, and a reader had to read four figures and hold them.
        #
        # The bar is `hopbar` and the widths are the .w0-.w100 scale, both
        # of which this stylesheet already has: no new primitive, which is
        # the standing rule. Each bar is a share of the LARGEST sub rather
        # than of the whole, because the subs OVERLAP — an experience can
        # match more than one keyword set, and Food's four sum to 50
        # against a total of 48. A stacked bar would claim a partition the
        # data does not have, which is the "present-but-empty" failure in
        # its other direction: a drawing that states something untrue is
        # worse than no drawing.
        top = max(counts.values()) or 1
        # A SUB WITH NO PAGE KEEPS ITS COUNT AND LOSES ITS LINK, which is
        # this atlas's own answer to a map dot the page cannot name: the
        # measurement is real and the navigation is not. The count is what
        # the keyword set actually selects, so dropping the row would hide
        # the very number that explains why there is no page.
        withpage = {sb["slug"] for sb in subs_with_a_page(data, cat)}
        def _sublink(sb):
            body = f"""{esc(sb['name'])} <span>{counts[sb['slug']]}</span>"""
            return (f"""<a href="{urls.subcategory(cat['slug'], sb['slug'])}">{body}</a>"""
                    if sb["slug"] in withpage else f"""<span class="nopage">{body}</span>""")
        subcards = '<ul class="sublinks shares">' + "".join(
            f"""<li>{_sublink(sb)}"""
            f"""<span class="hopbar" aria-hidden="true"><span class="w"""
            f"""{max(5, round(counts[sb['slug']] / top * 100 / 5) * 5)}"></span>"""
            f"""</span></li>"""
            for sb in cat["subs"]
        ) + "</ul>"
        # AND THE ROW THAT IS NOT A LINK SAYS SO, derived, or it reads as a
        # broken one. The sentence names the sub, its count and the floor,
        # because "some of these are not links" is the constraint explained
        # back rather than the reason given.
        nolink = [sb for sb in cat["subs"] if sb["slug"] not in withpage]
        nonote = ("" if not nolink else
                  '<p class="small">' + esc(
                      and_list([f'{sb["name"]} ({counts[sb["slug"]]})' for sb in nolink])
                      + (" holds" if len(nolink) == 1 else " hold")
                      + f" fewer than {FACET_MIN} of the {len(items)} experiences in "
                        f"the Atlas, so it has no page of its own"
                      + ("" if len(nolink) == 1 else " each")
                      + ". Everything it selects is already in the list above.")
                  + "</p>")
        # The overlap is stated where it exists rather than everywhere: a
        # note on a category whose subs happen to partition cleanly would
        # be explaining a constraint that is not operating.
        if sum(counts.values()) > len(chosen):
            subcards += (f'<p class="small mw44">The {numword(len(cat["subs"]))} bars '
                         f'are each a share of the largest rather than of the whole: '
                         f'an experience can answer more than one of these, so they '
                         f'sum to {sum(counts.values())} against {len(chosen)}.</p>')
        subcards += nonote

    countries = sorted({it["country"]["name"] for it in chosen})
    # REACH IS THE ARGUMENT AND IT WAS A NUMBER IN A GREY LINE.
    #
    # `docs/signature-moments.md` refuses GEOGRAPHY on this family and the
    # reason survives re-checking: 48 dots scattered over Europe would say
    # "food is everywhere", which is true and is not an insight. That
    # refusal is about the forty-eight DOTS, and it is kept — nothing here
    # plots an experience.
    #
    # What is drawn instead is the thing this page's own code already claims
    # is its offer, four hundred lines up: "the country leads, because the
    # SPREAD ACROSS EUROPE is the offer on this family". Measured, that
    # spread is the one quantity that separates the eight categories:
    #
    #     Luxury       5 experiences   2 countries
    #     Nature      28              18
    #     History     30              21
    #     Faith       42              23
    #     Food        48              26
    #     Culture     52              27
    #     Family     131              42
    #     Adventure  124              44
    #
    # Two countries against forty-four is not "everywhere". It is the same
    # argument /themes was rebuilt around — a knot is a claim about one
    # corner of Europe and a scatter is one about the whole of it — and it
    # is drawn with that family's own component rather than a new one.
    #
    # AT THE FULL EXTENT, NEVER FRAMED. Eight categories are only comparable
    # while every one is drawn on the same Europe; framing each on its own
    # members would delete the comparison, which is exactly why /themes is
    # not framed and the nine macro regions are.
    #
    # COUNTRIES, NOT DOTS, and that is the second half of keeping the
    # refusal. The homepage tiles and /themes light DESTINATIONS on this
    # silhouette; this lights whole countries, which is what the sentence
    # under it claims and all it claims.
    reach = sorted({it["country"]["slug"] for it in chosen})
    title = sub["name"] if sub else cat["name"]
    path = urls.subcategory(cat["slug"], sub["slug"]) if sub else urls.category(cat["slug"])
    trail = [("Europe", "/discover"), ("Experiences", "/experiences")]
    if sub:
        trail.append((cat["name"], urls.category(cat["slug"])))
    trail.append((title, None))

    # THE WORKING OF THE RULE, INCLUDING THE PARTS THAT DID NOTHING.
    #
    # This line used to print the sub-category's whole keyword list as
    # though every term had selected something. Across the 38 sub-pages, 113
    # of 261 terms match nothing in the 197 experiences here — so /experiences
    # /food/cellars claimed to have selected against champagne and riesling,
    # which have never matched a word anybody wrote. A published rule that
    # overstates itself is worse than an unpublished one, because a reader
    # can check it.
    #
    # Both halves are printed now, and the idle half is the more useful one:
    # it is a list of things nobody has written about yet, on the page where
    # somebody looking for them would land.
    rulenote = ""
    if sub:
        texts = [C.text_of(it["exp"]) for it in items]
        live, idle = C.live_keywords(sub, texts)
        rulenote = (f'<p class="small mw44 rulenote">Selected by name and '
                    f'description against {esc(and_list(live))} — matched on '
                    f'what we wrote about the experience, never on the name of '
                    f'the town.')
        if idle:
            rulenote += (f' {len(idle)} more '
                         f'{"terms are" if len(idle) != 1 else "term is"} '
                         f'declared for this list and {"have" if len(idle) != 1 else "has"} '
                         f'matched nothing yet: {esc(", ".join(idle))}. That is a '
                         f'gap in the writing rather than a fact about Europe.')
        rulenote += "</p>"

    photoband = pageband(data, f"category:{cat['slug']}")
    # FORTY-EIGHT INVITATIONS AND NOTHING TO LOOK AT.
    #
    # `docs/signature-moments.md` refuses geography here and the refusal
    # holds: 48 dots over Europe says food is everywhere, which is true and
    # is not an insight. It says nothing about PHOTOGRAPHS, and this is the
    # family whose own recorded finding is that it "is thin because the
    # register holds no photographs, which is a licence position and not a
    # design one". A licence position is not an excuse for a page that does
    # not say which photographs it is waiting for.
    #
    # THE PICTURE IS OF THE PLACE, NEVER OF THE EXPERIENCE. An experience
    # carries a slug, a name, a kind, a band and a summary — no image
    # purpose, and declaring 197 of them would be 197 surfaces nobody has a
    # brief for. The town it happens in has one, already, so the strip is
    # the distinct cities in the list's own order. Distinct, because six
    # markets in Vienna would otherwise be six copies of one photograph.
    _seen, _cshots = set(), []
    for _it in chosen:
        _k = f"city:{_it['country']['slug']}/{_it['region']['slug']}/{_it['city']['slug']}"
        if _k in _seen:
            continue
        _seen.add(_k)
        _cshots.append({"key": _k, "alt": _it["city"]["name"],
                        "label": _it["city"]["name"],
                        "href": urls.city(_it["country"], _it["region"], _it["city"])})
    _cstrip = ed_strip(data.get("images"), _cshots, limit=8)
    if _cstrip:
        _n = min(8, len(_cshots))
        _cstrip = ('<section class="ed-section">'
                   + ed_section_head("Where they happen",
                       f"{numword(_n, cap=True)} of the "
                       f"{n_of(len(_seen), 'town')} on this list",
                       "The picture is of the place, not of the invitation: an "
                       "experience has no photograph of its own here, and the "
                       "town it happens in does.")
                   + _cstrip + "</section>")
    body = f"""
{crumbs(trail)}
{photoband}
<!-- AN INDEX, NOT AN OVERTURE. This page is a SET — 48 experiences across
     26 countries — and it carried the head of a page about one thing: a
     60px h1 at y=212 with the extent under it. The three roles are what the
     reader is doing, and an index's extent sits beside its name so the set
     starts sooner. Measured across the twenty-two families: 538 to 347. -->
{constel_defs()}
<div class="pagehead index reachhead">
  <p class="kicker">{esc(cat['name']) if sub else 'Experience category'}</p>
  <h1>{esc(title)}</h1>
  <div class="reach">
    {region_glyph(reach)}
    <p class="reachnote">{esc(and_list([c for c in countries]) if len(countries) < 4 else f"{len(countries)} of Europe's {len(data['countries'])} countries")}, filled. Nothing here plots an experience: the spread is the offer and a dot per invitation would only say it is everywhere.<span class="srcnote">{geo.sources_line(geo.load("europe-lod0.json"))}</span></p>
  </div>
  <!-- `.lede`, not `.statement`. An index head places its extent beside the
       name in column two, row two, and the display-size statement is
       three lines to the h1's one — so the row grew to 128px and pushed the
       count line 93 pixels below the title it belongs to. The role decides
       the slot; using an overture's element inside an index head is how the
       gap got there. -->
  {f'<p class="lede">{esc(cat["blurb"])}</p>' if not sub else ""}
  <p class="orient">{len(chosen)} across {len(countries)} {"country" if len(countries) == 1 else "countries"}</p>
</div>
{f'<p class="countryspread lead">{country_spread(countries)}</p>' if sub and countries else ""}
{f'<nav class="sublinkwrap" aria-label="Sub-categories">{subcards}</nav>' if subcards else ""}
{_cstrip}
<!-- THE MECHANISM WAS STANDING IN FRONT OF THE ANSWER. "How this list is
     built" was a full section with its own h2 and a lede, ABOVE the list,
     so a reader met the selection rule before they met a single thing to
     do — the exact defect the motion pages were rebuilt for, one family
     over. THE QUERY IS THE PROOF, AND PROOF GOES UNDER THE THING IT
     PROVES: the rule now sits below the list, beside the sub-category
     rulenote, which was already there and is the same kind of sentence. -->
{rows or empty_state(
      "Nothing matches this rule yet.",
      "The rule is printed below and is the same one every other list on "
      "this site is built from. An empty list is better than a padded one, "
      "and widening the rule until something fell in would make every other "
      "list on the site mean less.")}
{f'<p class="listrule">How this list is built: {esc(C.rule_text(cat))}</p>' if not sub else ""}
{rulenote}
{ad_slot(path)}
"""
    return f"{path}/index.html", page(
        title, body, path=path, area="experiences",
        
        description=f"{title}: {n_of(len(chosen), 'experience')} across {n_of(len(countries), 'European country')}, selected by a published rule.",
    )


def spread_names(nodes, n=4):
    """`n` destination names taken ACROSS a set rather than off the top.

    `data["cities"]` is ordered by country, so the first four mountain
    destinations are four Albanian ones — which is the opposite of the claim
    a door makes by listing them. Evenly spaced indices give Chamonix,
    Zermatt, Theth and Mestia: the same spread the tagline was asserting in
    words, stated by the places themselves.

    THE SAME FAULT THE EXPERIENCE TILES HAD, one family over, where
    `sample_names` was written for exactly this reason. Two callers now, and
    they take different shapes — an experience node and an atlas node — so
    the arithmetic is shared and the extraction is not.
    """
    if not nodes:
        return []
    k = min(n, len(nodes))
    step = len(nodes) / float(k)
    # THE MIDDLE OF EACH BAND, NOT ITS EDGE. Starting at index 0 takes the
    # first destination in atlas order, which is the same Albanian one for
    # every tag it carries — Historic cities and Food & wine both opened on
    # Tirana, four columns apart, on the second screen of the front door.
    return [nodes[int((i + 0.5) * step)]["city"]["name"] for i in range(k)]


def sample_names(items, n=3):
    """A few of the actual invitations in a set, spread across it.

    AN EXPERIENCE IS AN INVITATION, AND THE WRITING IS THE PICTURE. The
    category and kind tiles carried a generated plate each — eighteen
    hash-drawn landscapes standing for abstractions, so "Adventure" opened
    on a church tower and "Culture" on a lake, chosen by the hash of the
    slug and related to nothing. That is the rule already written one family
    over — a story is not a place, and its picture may not be drawn from a
    hash — and A CATEGORY IS NOT A PLACE EITHER. The alternative to a
    hash-drawn landscape is not a better hash.

    What replaces it is the thing the family is actually made of. "Bosnian
    coffee, properly", "The commuter ferry as a day out", "Hut to hut in the
    High Tatras" — three of those say what Adventure is here far better than
    any drawing this repository can generate, and they are real rows a
    reader can go and read.

    Evenly spaced through the sorted list rather than the first three, so
    they come from across Europe instead of from whichever country the
    alphabet put first. Deterministic, and derived.
    """
    if not items:
        return []
    order = sorted(items, key=lambda it: (it["country"]["name"], it["city"]["name"],
                                          it["exp"]["name"]))
    if len(order) <= n:
        return [it["exp"]["name"] for it in order]
    # AT THE MIDDLE OF EACH NTH OF THE LIST, NOT AT ITS ENDS. Spacing from
    # index 0 put the same Albanian entry — "The Koman Lake ferry" — at the
    # top of Nature, Adventure AND Culture, because every list is sorted by
    # country and Albania is first in all of them. Three tiles side by side
    # leading with the same line reads as a broken page, and it was an
    # artefact of the sampling rather than anything about the data.
    return [order[min(len(order) - 1, int((i + 0.5) * len(order) / n))]["exp"]["name"]
            for i in range(n)]


def experiences_index(data):
    """THE EUROPEAN EXPERIENCE ATLAS — photography first, and the subject is
    what says so.

    Three pages, three instruments, one institution. /discover asks what you
    are looking for and answers with an instrument; /countries asks where it
    is and answers with geography; this one asks what you want to DO, and the
    only honest answer to that is a picture. `docs/experiences-redesign.md`
    is the audit behind it — what the page held, what the register holds, and
    which of the brief's twelve bands are refused and why.

    IT WAS FORTY-TWO ROWS OF ONE COMPONENT. A photograph, a strip of eight
    categories, and then 24 experiences, 8 category bars and 10 kind bars —
    every one of them a `.row`. Nothing in it was wrong: the bars are a real
    comparison (Family holds 131 entries and Luxury holds 5) and putting the
    experiences before the taxonomy was itself a repair. The fault is the
    sum. A page about what a place FEELS like was made entirely of type,
    which is the data's shape as the layout — the finding that rebuilt
    /journeys, /europe-in, /themes and the stories index, arriving last on
    the family that could least afford it.

    AND THE LIBRARY IS NOT THE CONSTRAINT HERE, WHICH IS WORTH SAYING ONCE.
    The standing answer to "why does a travel site have so few pictures" is
    the register, and on this page it does not apply: all eight categories,
    all nine macro regions and the hero are held, and every one of the ten
    kinds happens in a destination this atlas holds a photograph of. Nothing
    is acquired for this page. The pictures were already bought and were
    being spent on one strip.
    """
    from .data import all_experiences
    from . import categories as C
    images = data.get("images") or {}
    kinds = data["taxonomy"]["experience_kinds"]
    items = all_experiences(data["countries"])
    macros = data["taxonomy"]["macros"]
    macname = {m["slug"]: m["name"] for m in macros}
    idx = {(e["country"]["slug"], e["city"]["slug"]): cid
           for cid, e in data["cities"].items()}

    counts = {}
    for it in items:
        counts[it["exp"]["kind"]] = counts.get(it["exp"]["kind"], 0) + 1
    catn = {c["slug"]: len(C.select(items, c)) for c in data["categories"]}
    bycat = sorted(data["categories"], key=lambda c: -catn[c["slug"]])

    def cid_of(it):
        return idx.get((it["country"]["slug"], it["city"]["slug"]))

    def credit(keys):
        """One credit line per band, paid once — the homepage's own rule.

        The licence asks for the photographer and the provider; it does not
        ask for a caption under every frame, and eight of them down one band
        is the provenance layer becoming the visual identity. Never on the
        opening: that surface is the composition and the register is where
        the record lives.
        """
        out, seen = [], set()
        for k in keys:
            row = images.get(k)
            if not row or row["photographer"] in seen:
                continue
            seen.add(row["photographer"])
            out.append(f'<a href="{esc(row["source"])}" rel="noopener" '
                       f'target="_blank">{esc(row["photographer"])}</a>')
        return ('<p class="sheetcred rowcred">Photographs by '
                + ", ".join(out) + " on Pexels.</p>") if out else ""

    # ── 01 · THE INVITATION ──────────────────────────────────────────
    # THE PHOTOGRAPH BREAKS THE COLUMN, which is the one move that makes
    # this page's opening not the twenty-two others'. Every index here
    # opens on a picture INSIDE the measure; this one runs past the right
    # gutter and is cut on the diagonal, so the first thing a reader meets
    # is a frame the page could not contain.
    _hero = photo(images, "experiences-hero", w=2000, h=1400, eager=True,
                  sizes="(min-width: 52rem) 58vw, 100vw")
    invite = f"""
  <div class="sheettext">
    <h1 class="mega">What do you <br>want to <em class="lit">experience?</em></h1>
    <p class="lede">Europe is not one journey. It is {len(items)} ways to be
    there — to walk, taste, watch, row, pray, listen and go and look at
    something. Every one of them is a real, named thing in a real place, run
    by somebody this atlas names.</p>
    {golink('#the-field', 'Choose a way to be there')}
  </div>
  <figure class="xshot">{_hero}</figure>"""

    # ── 02 · THE FIELD ───────────────────────────────────────────────
    # THE TYPE IS THE NAVIGATION AND THE SLIVER IS THE ARGUMENT.
    #
    # The brief asks for an index of enormous editorial words rather than a
    # card grid, and names a vocabulary — WILD, SLOW, CULTURAL — that this
    # atlas does not hold. It holds ten KINDS, which are what somebody
    # physically does, and they are EXCLUSIVE: every experience has exactly
    # one and the ten sum to all 197, so every number on this band is a
    # count of the whole rather than a share of an overlap.
    #
    # Each row carries a narrow crop of a destination where that kind
    # actually happens — not an illustration of the idea, a photograph of a
    # place the row leads to. A destination is used once, so ten rows are
    # ten places; where a kind's only photographed destination is already
    # spent the row is type alone, which is honest and is what an empty
    # register looks like on a page that does not pretend otherwise.
    used, sliver = set(), {}
    for k in sorted(kinds, key=lambda k: -counts.get(k, 0)):
        for it in items:
            if it["exp"]["kind"] != k:
                continue
            cid = cid_of(it)
            if not cid or cid in used or ("city:" + cid) not in images:
                continue
            used.add(cid)
            sliver[k] = (cid, it)
            break
    kindrows = []
    for i, k in enumerate(sorted(kinds, key=lambda k: -counts.get(k, 0)), 1):
        shot, where = "", ""
        if k in sliver:
            cid, it = sliver[k]
            shot = picture(images, "city:" + cid, w=600, h=800, credit=False,
                           alt=images["city:" + cid]["alt"], sizes="9rem")
            where = (f'<span class="kindwhere">{esc(it["city"]["name"])}</span>')
        kindrows.append(
            # A GRID'S TRACKS ARE POSITIONAL AND THE FIRST VERSION HAD THE
            # NAME AND THE PICTURE THE WRONG WAY ROUND. `3rem 9.5rem 1fr
            # 7rem` with the markup ordered number, name, picture put
            # "Walk or hike" in a 152-pixel column and the photograph in
            # the 768-pixel one — a 1,024-pixel-tall crop, ten times, and
            # a band 11,127 pixels long. The order here IS the layout.
            f'<a class="kindrow" href="{urls.experience_kind(k)}">'
            f'<span class="kindno">{i:02d}</span>'
            f'<span class="kindart">{shot}</span>'
            f'<span class="kindname">{esc(kinds[k])}</span>'
            f'<span class="kindmeta"><span class="kindn">{counts.get(k, 0)}</span>'
            f'{where}</span></a>')
    field = f"""
  <div class="pagehead index">
    <p class="kicker">The European Experience Atlas</p>
    <h2 class="mega">Choose a way to be there.</h2>
    <p class="lede">{numword(len(kinds), cap=True)} kinds, and they do not
    overlap: each of the {len(items)} experiences has exactly one, so every
    count below is a count of the whole. A cellar visit and a cathedral are
    both sacred to somebody and only one of them is a walk.</p>
  </div>
  <div class="kinds">{"".join(kindrows)}</div>
  {credit(["city:" + c for c, _ in sliver.values()])}"""

    # ── 03 · EUROPE, EXPERIENCED ─────────────────────────────────────
    # The cinematic plate. `ed_declare` already composes type over a
    # photograph behind a scrim that makes the ratio a property of the
    # design rather than of the picture — 72% graphite composites to
    # rgb(71,71,71) and bone on that is 9.2:1 whatever the frame turns out
    # to be. The picture is the largest category's own.
    _big = bycat[0]
    declare = ed_declare(
        images, f"category:{_big['slug']}",
        statement="Europe reveals itself when you do something in it.",
        alt=images.get(f"category:{_big['slug']}", {}).get("alt", ""),
        only_if_held=True) if held(images, f"category:{_big['slug']}") else ""

    # ── 04 · WHERE IT HAPPENS ────────────────────────────────────────
    # GEOGRAPHY IS THE SECOND INSTRUMENT HERE, NOT THE FIRST, and it is the
    # LIGHT atlas rather than the graphite one — which is the whole of what
    # keeps this page from being /discover with different words. The dark
    # instrument belongs to the tool; this is a picture of where a thing
    # can be done.
    #
    # `docs/signature-moments.md` refuses a map on the experience CATEGORY
    # pages, and the reason survives re-checking: 48 dots scattered over
    # Europe say "food is everywhere", which is true and is not an insight.
    # That refusal is about a category. This is the whole family at once,
    # and what it says is the thing the rows cannot: 172 of 319 destinations
    # hold one, and the 147 that do not are not a gap in Europe, they are a
    # gap in this atlas.
    withx = {}
    for it in items:
        cid = cid_of(it)
        if cid:
            withx[cid] = data["cities"][cid]
    xpts = [(*project(n["city"]["lat"], n["city"]["lon"]),
             urls.city(n["country"], n["region"], n["city"]), n["city"]["name"])
            for n in withx.values()]
    xmap = pointsmap(
        xpts, "exp",
        f'{len(withx)} of {len(data["cities"])} destinations hold at least one '
        f'experience. The {len(data["cities"]) - len(withx)} that do not are a '
        f'gap in this atlas rather than in Europe.',
        f'Map of the {len(withx)} destinations that hold an experience',
        note='Names are dropped where they would overlap; every dot is a link. '
             'Coastline from <a href="/sources">Natural Earth</a>, public '
             'domain.'
             + offframe_line([(p[0], p[1]) for p in xpts], data, listed=False)
    ) if len(xpts) >= 2 else ""
    geoband = f"""
  <div class="sheettext">
    <h2 class="mega">Where Europe <br>meets the doing.</h2>
    <p class="lede">The same continent as the instrument on /discover, drawn
    the other way: pale ground, ink coast, one mark per place. A map answers
    where, and where is the second question on this page rather than the
    first.</p>
    {golink('/map', 'Open the full map')}
  </div>
  <div class="geoart">{xmap}</div>"""

    # ── 05 · SAME FEELING, DIFFERENT EUROPE ──────────────────────────
    # KIND BY MACRO REGION, AND THE AXIS WAS CHOSEN BY MEASURING BOTH.
    # Two thirds of every experience in the atlas is `family` or
    # `adventure`, so their regional breakdown says EVERYWHERE — the exact
    # non-insight the category map is refused for. The kinds are exclusive
    # and the answer changes: the water is the Nordics, the sacred sites
    # are the Mediterranean, the cellars are the south. Each group carries
    # the macro region's own photograph, which the register holds for all
    # nine.
    pairs, pkeys = [], []
    for k in sorted(kinds, key=lambda k: -counts.get(k, 0)):
        if len(pairs) == 4:
            break
        tally, names = {}, {}
        for it in items:
            if it["exp"]["kind"] != k:
                continue
            ms = it["country"].get("macro_slug")
            if not ms:
                continue
            tally[ms] = tally.get(ms, 0) + 1
            names.setdefault(ms, []).append(it["city"]["name"])
        if not tally:
            continue
        top = max(tally, key=lambda m: tally[m])
        # A KIND WHOSE BIGGEST REGION IS A THIRD OF IT IS NOT A CLAIM ABOUT
        # A REGION. The band exists to say where something concentrates, so
        # a kind spread evenly across nine corners is left off rather than
        # printed with a number that reads as a finding.
        if tally[top] * 3 < counts.get(k, 0):
            continue
        # ONE PICTURE PER THING, AND THE FIRST VERSION DREW TWO TILES FROM
        # ONE FILE. The obvious photograph for "the water is the Nordics" is
        # `macro:nordic` — and the museums are the Nordics too, and the
        # cellars and the tables are both the Mediterranean, so four tiles
        # came out as two photographs side by side twice. That reads as a
        # rendering fault rather than as a composition, and it is this
        # repository's own `one thing, one picture` arriving from the other
        # end: not one record with two pictures, one picture on two records.
        #
        # So the tile takes a DESTINATION inside the group where the register
        # holds one — which is more specific anyway, because "11 of 25 on the
        # water are in the Nordics" is better illustrated by a place on that
        # water than by a photograph of the region in general. The macro's own
        # picture is the fallback, and either way a key already spent is
        # skipped rather than drawn twice.
        shot = None
        for it in items:
            if it["exp"]["kind"] != k or it["country"].get("macro_slug") != top:
                continue
            cid = cid_of(it)
            if cid and ("city:" + cid) in images and ("city:" + cid) not in pkeys:
                shot = "city:" + cid
                break
        if shot is None and held(images, "macro:" + top) \
                and ("macro:" + top) not in pkeys:
            shot = "macro:" + top
        if shot is None:
            continue
        pkeys.append(shot)
        seen, where = set(), []
        for nm in names[top]:
            if nm not in seen:
                seen.add(nm)
                where.append(nm)
        pairs.append(
            f'<a class="pairrow" href="{urls.experience_kind(k)}">'
            f'<span class="pairart">'
            + picture(images, shot, w=1000, h=750, credit=False,
                      alt=images[shot]["alt"],
                      sizes="(min-width: 52rem) 30vw, 92vw")
            + f'</span><span class="pairsay">'
              f'<span class="pairkind">{esc(kinds[k])}</span>'
              f'<span class="pairmac">{esc(macname[top])}</span>'
              f'<span class="pairn">{tally[top]} of {counts.get(k, 0)}</span>'
              f'<span class="pairwhere">'
              f'{esc(" · ".join(where[:5]))}'
            + (f' · +{len(where) - 5} more' if len(where) > 5 else "")
            + '</span></span></a>')
    samefeeling = f"""
  <div class="sheettext">
    <h2 class="mega">Same feeling. <br>Different Europe.</h2>
    <p class="lede">Where each kind actually concentrates, counted rather
    than chosen. A kind whose largest corner holds under a third of it is
    not on this band — a number that is true everywhere is not a finding.</p>
  </div>
  <div class="pairs">{"".join(pairs)}</div>
  {credit(pkeys)}""" if pairs else ""

    # ── 06 · WHAT THEY ARE ABOUT ─────────────────────────────────────
    # THE EIGHT CATEGORIES AT FOUR SCALES. The brief asks for an image
    # rhythm — large, narrow, panoramic, intimate — rather than eight of
    # one size, and the reason is this repository's own: every photograph
    # the same size in the same 16/9 box is what made the old page's one
    # strip read as a contact sheet. The order is largest first, the same
    # order the bars below are in, because the strip and the rows must not
    # argue about which category is which.
    # AND THE TILE NAMES THREE REAL EXPERIENCES, which is how the 197 stay
    # on the page at all. The old index printed 24 of them as rows; this
    # one printed none, and a page whose whole subject is what people
    # actually do had stopped naming a single thing anybody does. Three per
    # category is 24 again, in the band that says what the categories ARE
    # — the `ed_strip` repair applied here: the tile takes the sentence and
    # the second band goes.
    #
    # THE LABEL IS UNDER THE PICTURE RATHER THAN ON IT. A name over a
    # photograph needs a scrim, and a scrim over three lines of sample
    # names is a caption pretending to be a picture. Under it, in the
    # margin, is how a gallery labels a work — which is `.gi`'s own rule
    # and the reason this page can hang eight photographs without reading
    # as a catalogue.
    xtiles, xkeys = [], []
    SCALES = ("wide", "tall", "pan", "close")
    for i, cat in enumerate(bycat):
        key = f"category:{cat['slug']}"
        if not held(images, key):
            continue
        xkeys.append(key)
        names = sample_names(C.select(items, cat))
        xtiles.append(
            f'<a class="xt xt-{SCALES[i % len(SCALES)]}" '
            f'href="{urls.category(cat["slug"])}">'
            + picture(images, key, w=1600, h=1200, credit=False,
                      alt=images[key]["alt"],
                      sizes="(min-width: 52rem) 46vw, 92vw")
            + f'<span class="xtsay"><span class="xtn">{catn[cat["slug"]]} listed</span>'
              f'<span class="xtname">{esc(cat["name"])}</span>'
            + (f'<span class="xtaste">{esc(" · ".join(names))}</span>'
               if names else "")
            + '</span></a>')
    about = f"""
  <div class="sheettext">
    <h2 class="mega">What they <br>are about.</h2>
    <p class="lede">The other axis, and this one overlaps on purpose: an
    experience may be in several at once, so {len(data["categories"])}
    categories hold {sum(catn.values())} memberships across {len(items)}
    experiences. Largest first.</p>
  </div>
  <div class="xstrip">{"".join(xtiles)}</div>
  {credit(xkeys)}""" if xtiles else ""

    # ── 07 · THE STORIES ─────────────────────────────────────────────
    # An experience is a thing you book and a story is the reason you would.
    # `.galgrid` is the gallery grid the homepage already uses — the name
    # UNDER the picture, in the margin, the way a gallery labels a work,
    # which is the whole difference between a card and a plate.
    st = [s for s in sorted(data["stories"],
                            key=lambda s: s.get("published", ""), reverse=True)
          if held(images, "story:" + s["slug"])]
    tales = ""
    if len(st) >= 3:
        skeys = ["story:" + s["slug"] for s in st[:3]]
        tiles = "".join(
            f'<a class="gi" href="{urls.story(s)}">'
            + picture(images, "story:" + s["slug"], w=1200, h=1600,
                      credit=False, alt=images["story:" + s["slug"]]["alt"],
                      sizes="(min-width: 52rem) 30vw, 92vw")
            + (f'<span class="giwhere">{esc(s["section"])}</span>'
               if s.get("section") else "")
            + f'<span class="giname">{esc(s["title"])}</span>'
              f'<span class="giline">{esc(s.get("standfirst", ""))}</span></a>'
            for s in st[:3])
        tales = f"""
  <div class="galwrap">
  <div class="sheettext">
    <h2 class="mega">Why anybody <br>goes at all.</h2>
    <p class="lede">An experience is a thing you can book. A story is the
    reason you would. {len(data["stories"])} of them, and every place either
    one names has a page here.</p>
    {golink('/stories', 'Every story')}
  </div>
  <div class="tales">{tiles}</div>
  {credit(skeys)}
  </div>"""

    # ── 07 · THE PLACES ──────────────────────────────────────────────
    # THE CINEMATIC STRIP, AND `ed_strip` ALREADY IS ONE. It SCROLLS rather
    # than wrapping, because a sequence is read along and wrapping an order
    # into rows turns it into a grid — the rule that primitive was written
    # with. What the brief asks for here is a horizontal run of large
    # photographs with the type beside them, which is that component with
    # this band's own set in it.
    #
    # AND THE SET IS THE ONE THING ONLY THIS PAGE CAN SHOW: destinations
    # that hold an experience AND a photograph, with the number of
    # experiences each holds as the note. The library has 65 photographed
    # destinations and this band takes ten that no earlier band on the page
    # has spent, because `there is no third place to put them that would
    # not be the same eleven a third time` is this repository's own warning
    # and the way past it is to have more of them rather than to reuse.
    nx = {}
    for it in items:
        cid = cid_of(it)
        if cid:
            nx[cid] = nx.get(cid, 0) + 1
    fresh = [cid for cid in sorted(nx, key=lambda c: (-nx[c], c))
             if ("city:" + cid) in images and cid not in used]
    strip = ed_strip(images, [
        {"key": "city:" + cid, "alt": images["city:" + cid]["alt"],
         "label": data["cities"][cid]["city"]["name"],
         "href": urls.city(data["cities"][cid]["country"],
                           data["cities"][cid]["region"],
                           data["cities"][cid]["city"]),
         "note": f'{nx[cid]} experience{"s" if nx[cid] != 1 else ""} · '
                 f'{data["cities"][cid]["country"]["name"]}'}
        for cid in fresh], limit=10)
    places = f"""
  <div class="sheettext">
    <h2 class="mega">Ten places <br>it happens in.</h2>
    <p class="lede">The destinations that hold the most of them and that this
    atlas holds a photograph of — {len(nx)} of {len(data["cities"])} hold at
    least one, and {len([c for c in nx if ("city:" + c) in images])} of those
    are photographed. Read along.</p>
  </div>
  {strip}
  {credit(["city:" + c for c in fresh[:10]])}""" if strip else ""

    # ── 08 · THE BARS WERE THE SAME TWO AXES A SECOND TIME ───────────
    # DELETED, AND `docs/experiences-redesign.md` SAID TO KEEP THEM.
    # That audit was written before the page was rendered and it was wrong
    # for the reason this repository keeps recording: eight category bars
    # under eight category PHOTOGRAPHS, and ten kind bars under ten kind
    # ROWS, is one set printed twice to say two things — and here the
    # second printing said less than the first, because the picture and
    # the place are what the bar cannot carry.
    #
    # What the bars had that nothing else did was the category blurb, the
    # three sample experiences and the visual proportion. The samples moved
    # onto the tile, which is the `ed_strip` repair; the blurbs live on the
    # eight category pages and the section audit asserts them there; and
    # the proportion is 131 against 5 printed on the tiles in largest-first
    # order, which a reader can read. 3,086 pixels of page, and the two
    # numbers that were the argument for two axes are still on it.
    # ── 09 · THE DOOR ────────────────────────────────────────────────
    # ONE APERTURE ON THE PAGE, AND IT IS THE MAP. The brief asks for a
    # photographic aperture in band 11 and a circular one at the close, and
    # this page already cuts the door once — on the geography, which is how
    # this atlas draws it everywhere else. Three doors in one document is
    # the signature as wallpaper, which is the rule `docs/signature-moments.md`
    # states and this page would be the first to break.
    #
    # ANYTHING A BUSINESS LISTS CARRIES THE NAME OF WHO RUNS IT, and that
    # sentence had been buried in the old head's lede. It is the one claim
    # here no competitor makes, so it closes the page instead.
    door = f"""
  <div class="sheettext">
    <h2 class="mega">You do not need <br>another list.</h2>
    <p class="lede">Anything a business lists here carries the name of who
    runs it and the tier of checking it has passed — an unchecked listing says
    so on its face rather than hiding behind a star rating. Nothing on this
    page is paid for, and nothing on it can be.</p>
    <p class="keepgo">{golink('/experiences/join', 'List your experience')}
    {golink('/for-businesses', 'What we check, and what we refuse')}</p>
  </div>"""

    PLATES = [("invite gal", "The invitation", invite, "the-invitation"),
              ("kinds gal", "The field", field, "the-field"),
              ("declare", "Europe, experienced", declare, "experienced"),
              ("geo gal", "Where it happens", geoband, "where-it-happens"),
              ("pairs gal quiet", "Same feeling", samefeeling, "same-feeling"),
              ("about gal", "What they are about", about, "how-its-cut"),
              ("strip gal quiet", "The places", places, "the-places"),
              ("tales pine", "The stories", tales, "the-stories"),
              ("keep gal", "The door", door, "the-door")]
    body = (crumbs([("Europe", "/discover"), ("Experiences", None)])
            + constel_defs()
            + plate_sequence(PLATES))

    return "/experiences/index.html", page(
        "Experiences", body, path="/experiences", area="experiences", hero=True,
        description="Guides, kitchens, cellars, boats and museums across Europe — every listing named, tiered and checked.",
    )


def experience_kind_page(data, kind, name):
    from .data import all_experiences
    items = [it for it in all_experiences(data["countries"]) if it["exp"]["kind"] == kind]
    items.sort(key=lambda it: (it["country"]["name"], it["city"]["name"]))
    # THE SAME COMPOSITION AS A CATEGORY PAGE, because it is the same
    # content: a set of invitations. This was `.rows` with the place
    # right-aligned across 1,168 pixels from the name it belongs to, on the
    # other axis of the same family. Two lists of experiences laid out two
    # ways is the design system forking inside one family.
    #
    # Bound to a local rather than dug out inside the f-string: the empty-state
    # check reads the generator's source and pulls string literals out of the
    # reason, and a subscript like ["experience_kinds"] puts quotes inside the
    # expression where that regex sees them as the reason itself.
    nkinds = numword(len(data["taxonomy"]["experience_kinds"]))
    # THE BAND'S NAME RATHER THAN ITS SLUG, which the category page one
    # function up records at length: `data/taxonomy.json` gives each budget
    # band a name and a note, and both invite call sites printed the
    # identifier.
    bandname = {b["slug"]: b["name"] for b in data["taxonomy"]["budgets"]}
    # The kind is not printed on a kind page: every row on it is that kind
    # by definition, which is the constraint explained back.
    rows = "".join(
        f"""<li class="invite"><a href="{urls.city(it['country'], it['region'], it['city'])}">
        <h2>{esc(it['exp']['name'])}</h2>
        <p class="invite-sum">{esc(it['exp']['summary'])}</p>
        <p class="invite-where">{esc(it['city']['name'])}, {esc(it['country']['name'])}
        · {esc(bandname.get(it['exp']['band'], it['exp']['band']))}</p></a></li>"""
        for it in items
    )
    body = f"""
{crumbs([("Europe", "/discover"), ("Experiences", "/experiences"), (name, None)])}
<div class="pagehead index">
  <p class="kicker">{len(items)} across Europe</p>
  <h1>{esc(name)}</h1>
</div>
<ol class="invites">{rows or empty_state(
      "Nothing in the Atlas is classified this way yet.",
      f"This is one of {nkinds} kinds an experience can be given, and the kind is "
      "authored per experience. An empty page here means nobody has written "
      "one, not that Europe has none.")}</ol>
"""
    # AND THE OTHER TWO COLLISIONS ARE INSIDE THIS FAMILY, between its own
    # two axes. "Music & performance" is a sub-category of Culture and a
    # KIND; "On the water" is a sub-category of Adventure and a kind. The
    # /experiences index states the difference in as many words — "the other
    # axis: what you physically do" — and the titles did not carry it.
    return f"/experiences/kind/{kind}/index.html", page(
        f"{name} — what you do", body,
        path=urls.experience_kind(kind), area="experiences",
        
        description=f"{name} experiences across Europe, by city and country.",
    )


def join_page(data):
    tiers = "".join(
        f"""<div class="card"><div class="card-body"><p class="kicker">{esc(t['name'])}</p>
        <h3>{esc(t['who'])}</h3><p class="blurb">{esc(t['means'])}</p>
        <p class="cardmeta">{esc(t['badge'])}</p></div></div>"""
        for t in data["providers"]["tiers"]
    )
    body = f"""
{crumbs([("Europe", "/discover"), ("Experiences", "/experiences"), ("List your experience", None)])}
<div class="pagehead">
  <p class="kicker">For guides, kitchens, museums and operators</p>
  <h1>List what you do.</h1>
  <p class="lede">EuropeDoor lists experiences run by people who live where they happen.
  Listing is free. What costs is prominence, and we say so on the page rather than quietly
  sorting paid listings to the top.</p>
</div>
<div class="split">
  <div>
    <h2>Three tiers, and what each one means</h2>
    {grid([tiers], 3) if False else '<div class="grid cols-3">' + tiers + '</div>'}
    <h2 class="mt7">What we check</h2>
    <ul class="stack">
      <li><strong>You exist.</strong> A registered business or a licensed guide number in the country you operate in.</li>
      <li><strong>You are there.</strong> An address, a phone that answers, and a person whose name goes on the listing.</li>
      <li><strong>You are insured</strong> where the activity requires it — water, height, vehicles, food service.</li>
      <li><strong>You said what it costs</strong>, including what is not included.</li>
    </ul>
    <h2 class="mt7">What we will not do</h2>
    <ul class="stack">
      <li>Sell placement inside the Journey Planner. The planner scores on fit and distance; money does not enter it.</li>
      <li>Publish a listing whose owner we could not reach.</li>
      <li>Take a booking on your behalf until the payments and consumer-law work in
      <a href="/how-it-works">how it works</a> is finished and reviewed.</li>
    </ul>
    <div class="note">
      <h2 class="mini">Applications are not open yet</h2>
      <p>This page describes the model so operators can tell whether it is worth their time.
      There is no form here on purpose: we will not collect business details before there is
      an entity to hold them and a published privacy notice to hold them under.</p>
    </div>
  </div>
  <aside class="rail">
    <h2 class="mini">Directory tiers &amp; indicative pricing</h2>
    <p>Free listing · Professional €49–99 per month · Premium €199+ per month.</p>
    <p class="small">Indicative only, and untested. Pricing gets set after a hundred conversations
    with operators, not before.</p>
    <h2 class="mini">Commission</h2>
    <p>When bookings exist, the intended range is 10–15% on experiences sold through the platform,
    with the operator setting the price and keeping the customer relationship.</p>
  </aside>
</div>
"""
    return "/experiences/join/index.html", page(
        "List your experience", body, path="/experiences/join", area="experiences",
        description="How guides, restaurants, museums and operators appear on EuropeDoor: three tiers, what is checked, and what placement never buys.",
    )


def business_page(data):
    provs = data["providers"]["providers"]
    rows = "".join(
        f"""<div class="row"><div><h3>{esc(p['name'])}
        <span class="tag {'verified' if p['tier'] == 'verified' else ''}">{esc(p['tier'])}</span></h3>
        <p class="rowsub">{esc(p['summary'])}</p></div>
        <p class="rowmeta">{esc(p['city'])}, {esc(data['countries'][p['country']]['name'])}</p></div>"""
        for p in provs
    )
    # THE ARCHITECTURE IS PUBLISHED WHERE THE PEOPLE WHO NEED IT ARE. An ad
    # slot with no advertiser renders nothing anywhere on the site — zero
    # bytes, no container, no placeholder, which is the opposite of
    # `ed_slot()` and for the opposite reason: there the reader is an editor
    # and the acquisition list is the page, here the reader is a traveller
    # and a reserved box is this product advertising that it would like to
    # carry advertising. So the only surface that states the commercial layer
    # is the directory page, which is the one an advertiser reads.
    #
    # Every figure is derived from data/advertising.json, so a product that
    # is switched on cannot be switched on quietly: it says so here.
    adrows = "".join(
        f'<div class="row"><div><p class="kicker">{esc(pl["disclosure"])}</p>'
        f'<h3>{esc(pl["name"])}</h3>'
        f'<p class="rowsub">{esc(pl["brief"])}</p>'
        f'<p class="small">Never: {esc(pl["may_never"])}</p></div>'
        f'<p class="rowmeta">{esc(pl["page_type"])}<br>'
        f'<span class="small">{"running" if pl.get("enabled") else "off"}</span></p></div>'
        for pl in ADS.placements()
    )
    adobject = "".join(
        f'<div class="row"><div><h3>{esc(pl["name"])}</h3>'
        f'<p class="rowsub">{esc(pl["objection"])}</p></div>'
        f'<p class="rowmeta">{esc(pl["page_type"])}</p></div>'
        for pl in ADS.placements() if pl.get("objection")
    )
    adconds = "".join(
        f'<div class="row"><div><h3 class="mini">{esc(label_)}</h3></div>'
        f'<p class="rowmeta">{"yes" if v else "no"}</p></div>'
        for label_, v in ADS.conditions()
    )
    adstatus = "".join(
        f'<div class="row"><div><h3 class="mini">{esc(k)}</h3></div>'
        f'<p class="rowmeta">{esc(v)}</p></div>'
        for k, v in ADS.status()
    )
    # AN F-STRING EXPRESSION CANNOT HOLD A TRIPLE-QUOTED F-STRING, which is
    # the same construct this file already records about a comment and a
    # backslash. The band is composed here and interpolated as one name.
    adband = section(
        "The commercial layer, and why none of it is running",
        '<div class="rows">' + adstatus + "</div>"
        + '<h3 class="mini">The nine declared placements</h3>'
        + '<div class="rows">' + adrows + "</div>"
        + '<h3 class="mini">Every condition between a campaign and a reader</h3>'
        + '<div class="rows">' + adconds + "</div>",
        lede=("Nine placements, nine surfaces, and a campaign table with nothing "
              "in it. Switching one on takes " + str(len(ADS.conditions()))
              + " separate conditions rather than a flag, and they are listed "
              "under the placements below because a count typed into a sentence "
              "is a count that disagrees with the mechanism a commit later."),
        id="advertising", opens=True)
    body = f"""
{crumbs([("Europe", "/discover"), ("For businesses", None)])}
<div class="pagehead">
  <p class="kicker">European Business Directory</p>
  <h1>The businesses behind the experiences.</h1>
  <p class="lede">Hotels, guesthouses, restaurants, operators, guides, museums, castles,
  transport and cultural institutions — one profile each, claimable by whoever actually runs it.
  The directory is the commercial engine; the Atlas is not for sale.</p>
</div>
<div class="split">
  <div>
    <h2>Seeded profiles</h2>
    <p class="small">A handful of illustrative profiles showing the shape of a record and the
    three verification tiers. These are examples for design review, not live partners.</p>
    <div class="rows">{rows}</div>
  </div>
  <aside class="rail">
    <h2 class="mini">The wall between editorial and commerce</h2>
    <p>{esc(ADS.wall()["position"])}</p>
    <p class="small">{esc(ADS.wall()["surfaces"])} This wall moved on
    {esc(ADS.wall()["moved"].split(":")[0])}, and this page is where it moved: it used to read
    <em>{esc(ADS.wall()["replaced"].rstrip("."))}</em>. What did not move is the
    substance — ranking, weighting, curation, scores, result order and copy were never for
    sale and are not now.</p>
    <h2 class="mini">Claiming a profile</h2>
    <p>Not open yet — same reason as <a href="/experiences/join">listings</a>.</p>
  </aside>
</div>
{adband}
<div class="split">
  <div>
    <h2>What a paid placement may never do</h2>
    <p>{esc(ADS.load()["refusals"]["why"])}</p>
    <p class="small">There is no field on a campaign a ranking could read, so no code path
    can be written that reads one: {esc(", ".join(ADS.load()["refusals"]["campaign_keys"]))}
    are refused by name in the validator and again in the checks. A creative
    <strong>image</strong> is refused too, and for the register rather than for taste —
    nothing ships here without a photographer, a source, a licence, a date and the hash of
    the bytes, and an advertiser&#8217;s artwork arrives with a brand guideline instead.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Two surfaces with an objection attached rather than a veto</h2>
    <div class="rows">{adobject}</div>
  </aside>
</div>
"""
    return "/for-businesses/index.html", page(
        "For businesses", body, path="/for-businesses", area=None,
        description="EuropeDoor's European business directory: profiles for hotels, operators, guides and institutions, three verification tiers, and a stated wall between paid placement and editorial.",
    )


# ── the Fund ──────────────────────────────────────────────────────────

def fund_index(data):
    themes = {}
    for p in data["fund"]:
        themes.setdefault(p["theme"], []).append(p)
    # TWELVE HASH-DRAWN LANDSCAPES ON THE PAGE THAT PROMISES NOTHING IS
    # DECORATION. A fund project is a real thing in a real place — Saxon
    # fortified churches in Transylvania, hay meadows in Maramureș — and a
    # gradient generated from its slug says nothing about any of them. It is
    # the same measurement that emptied the homepage, /journeys, /europe-in,
    # the stories index and the seventeen interest pages, on the one page
    # where a picture nobody chose sits beside the words "listed publicly,
    # with the local partner named on each".
    rows = "".join(
        f'<a class="row" href="{urls.fund_project(p)}">'
        f'<div><p class="kicker">{esc(data["countries"][p["country"]]["name"])}</p>'
        f'<h3>{esc(p["name"])}</h3>'
        f'<p class="rowsub">{esc(p["summary"])}</p></div>'
        f'<p class="rowmeta">{esc(p["theme"])} · {esc(p["status"])}</p></a>'
        for p in data["fund"])
    # "THE FOUR THEMES" OVER SEVEN CARDS, AND FOUR OF THEM SAID "1 projects".
    #
    # The heading was a number typed into prose — the failure this repository
    # already has on record twice, where a figure that was true earlier stops
    # being true and nothing notices — and the card body had no plural rule at
    # all. Both are derived now.
    #
    # And a card holding a kicker and a count is what /experiences was before
    # the nav-bar pass: border, fill, radius and shadow spent on a tile that
    # separates nothing, in a grid of seven that leaves three empty cells. The
    # thing that distinguishes these seven is HOW MUCH of the register each
    # holds, and where the work is, so the rows carry the count as a bar
    # against the largest and name the countries.
    # AND THE FIRST VERSION PRINTED SLUGS. `p["country"]` is a key into
    # data["countries"], not a name, so the row read "ireland,
    # north-macedonia and romania" — the register's internal identifiers, on
    # a page whose whole argument is that each project is named publicly with
    # its local partner. The rows above it had always looked the name up.
    _peak = max(len(v) for v in themes.values()) if themes else 1
    themerows = '<div class="rows">' + "".join(
        '<div class="row"><div><h3>' + esc(t.title()) + '</h3>'
        '<p class="rowsub">'
        + esc(and_list(sorted(data["countries"][p["country"]]["name"]
                              for p in {q["country"]: q for q in v}.values())))
        + '</p></div><p class="rowmeta">'
        + f'{len(v)} project{"s" if len(v) != 1 else ""}<br>'
        # THE TRACK AND THE FILL ARE TWO ELEMENTS, and the first version was
        # one: `class="hopbar w50"` put the share on the TRACK, where
        # `.rowmeta .hopbar { width: 5rem }` at (0,2,0) beat `.w50` at
        # (0,1,0) and every bar came out the same length. Fifth specificity
        # collision in this stylesheet to render as "the thing is simply
        # wrong". `.hopbar` is the track and its child carries the width,
        # which is how the journeys and /experiences already use it.
        + f'<span class="hopbar" aria-hidden="true">'
        + f'<span class="w{round(100 * len(v) / _peak)}"></span></span>'
        + '</p></div>'
        for t, v in sorted(themes.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ) + "</div>"

    # THE WHOLE FUND FAMILY HAD NO GEOGRAPHY, on the one register whose
    # argument is that every entry is a real thing in a real place with a
    # named local partner beside it. The index opened on type alone and the
    # twelve project pages measured 0% picture on the first screen — the last
    # DISCOVER surface on the site to do so, and the only one that is not an
    # instrument, where a picture is correctly absent.
    #
    # What the register holds about a place is its COUNTRY, so that is what
    # is drawn and nothing else. Nine countries lit from Inis Mór to
    # Svaneti, and that scatter is the argument: this is not a Romanian
    # heritage charity with a website, it is the same kind of work in nine
    # places that have nothing else in common.
    #
    # `region_glyph` with no frame, deliberately: the nine ARE the continent's
    # own extent, so framing them would zoom to a picture of Europe.
    fund_countries = sorted({p["country"] for p in data["fund"]})
    fund_names = [data["countries"][cs]["name"] for cs in fund_countries]
    body = f"""
{crumbs([("Europe", "/discover"), ("Fund", None)])}
{constel_defs()}
<!-- NOT A FIFTH ARCH. `indexhero` was the obvious move and this page is the
     one where it is wrong: the audit already took two index openings off for
     being "a continent with a different number of dots on it", and a sea
     panel with nine countries lit is the reach glyph the experience category
     page already draws, in a doorway. The structure has appeared twice, so
     it is the same component — which is what "no new primitive until
     repeated structure has emerged" means from the other side. A glyph, not
     a window; a mark on the page's own paper. -->
<div class="pagehead index reachhead">
  <p class="kicker">Europe Fund</p>
  <h1>What travel leaves behind.</h1>
  <div class="reach">
    {region_glyph(fund_countries)}
    <p class="reachnote">{esc(and_list(fund_names)) if len(fund_names) < 4
        else f"{numword(len(fund_names), cap=True)} of Europe's {len(data['countries'])} countries"}, filled.
    The register records which country a project is in and no finer position than
    that, so these are whole countries rather than pins.
    {geo.sources_line(geo.load("europe-lod0.json"))}</p>
  </div>
  <p class="lede">Tourism arrives in a place and takes something out of it — a path, a language,
  a harbour wall, a summer. The Fund is the mechanism for putting something back: the same
  kind of work in places that have nothing else in common, listed publicly, with the local
  partner named on each.</p>
  <p class="orient">{len(data['fund'])} projects across {numword(len(fund_names))} countries</p>
</div>

<div class="note">
  <h2 class="mini">The Fund holds no money, and will not until three things are true</h2>
  <p>There is an operating entity; a regulated payment path with a named payee; and a written
  answer on how contributions are treated in each country we would collect in. Until then this
  is a register of projects and nothing else — there is no balance, no total raised, and no
  donate button anywhere on this site. The data files are validated to reject a project that
  carries an amount.</p>
  <p class="small">Rationale and the full gate: <a href="/how-it-works">how it works</a>.</p>
</div>

{section(f"{len(data['fund'])} projects on the register", f'<div class="rows">{rows}</div>',
         lede="Chosen for being small enough that a travel platform could plausibly matter to them, and specific enough that you could go and look at the result.")}

{section(f"{len(themes)} kinds of work", themerows,
    lede="What the register is actually made of. Sorted by how much of it each "
         "kind holds, and the bar is that share of the largest.") if themes else ""}
"""
    return "/fund/index.html", page(
        "Europe Fund", body, path="/fund", area="fund",
        description="A public register of European heritage, language, trail and coastline projects — listed openly, holding no money until the legal and payment work is done.",
        # heritage: this page is about how we know what we claim
        accent="heritage"
    )


def fund_page(data, p):
    """A project page opens on the country it is in, at the country's own size.

    Measured by `tools/opening.js` across every rendered family: this one was
    0% picture on the first screen — no figure anywhere on the page, on the
    one family whose argument is that each entry is a real thing in a real
    place. It was invisible because the family list the instruments read had
    never carried a fund project page at all; adding the three templates that
    list had missed found it in one run.

    `country_glyph` rather than the shared silhouette with one bit lit. The
    index above already answers "where in Europe" for all twelve at once, and
    repeating that drawing twelve times is the aperture-as-wallpaper rule in a
    different picture. What this page wants is WHICH country, and Ireland,
    Romania and Georgia are three shapes a reader tells apart before reading a
    word.

    AND FOUR OF THE TWELVE DRAW ROMANIA, which is a fact about the register
    rather than a fault in the drawing: four Romanian projects are four
    projects in Romania. A reader meets one project page at a time and the
    comparison happens on the index, which is exactly why the index draws all
    nine countries together and each page draws its own.

    The register holds a country and no finer position, so the caption says
    so. Inventing a point for the Aran Islands would be authoring a
    measurement, which is the one thing this data model refuses.
    """
    c = data["countries"][p["country"]]
    glyph = country_glyph(c["slug"], p["country"])
    art = (f'<figure class="pagehead-art fundart">{glyph}'
           f'<figcaption><span class="capsay">{esc(c["name"])}, where this '
           f'project is.</span><span class="capsrc">The register records the '
           f'country and no finer position — coastline and frontiers from '
           f'<a href="/sources">Natural Earth</a>, public domain.</span>'
           f'</figcaption></figure>') if glyph else ""
    body = f"""
{crumbs([("Europe", "/discover"), ("Fund", "/fund"), (p["name"], None)])}
<div class="pagehead overture fundhead">
  <div class="fundsay">
    <p class="kicker">{esc(p['theme'])} · {esc(c['name'])}</p>
    <h1>{esc(p['name'])}</h1>
  </div>
  {art}
</div>
<div class="split">
  <div>
    <p class="lede">{esc(p['summary'])}</p>
    <h2>What it needs</h2>
    <p>{esc(p['need'])}</p>
    {factlist([("Country", f'<a href="{urls.country(c)}">{esc(c["name"])}</a>'),
               ("Local partner", esc(p["partner"])),
               ("Status", esc(p["status"])),
               ("Money held by EuropeDoor", "None — see the note")])}
  </div>
  <aside class="rail">
    <h2 class="mini">No balance shown, on purpose</h2>
    <p>A progress bar implies custody of funds. We have none, so there is none. When the Fund
    becomes operational, every project page will show what was received, what was paid to the
    partner, and what was kept for running costs — in that order.</p>
    <p><a href="/fund">Back to the register →</a></p>
  </aside>
</div>
"""
    return f"/fund/{p['slug']}/index.html", page(
        p["name"], body, path=urls.fund_project(p), area="fund",
        description=p["summary"][:180],
    )


# ── themes: experience-first discovery ────────────────────────────────

def constel_defs():
    """The continent, emitted once per page and cloned by every glyph on it.

    A coarse silhouette — lod0, thinned hard — because these are 130 to 380
    pixels wide and any more detail is bytes nobody can see. Thirteen theme
    constellations or eleven homepage tiles therefore cost ONE coastline.

    A SELECTOR CANNOT REACH INSIDE A <use>. Cloned content lives in a shadow
    tree, so the fill is set on the containing <svg> and inherited through the
    clone — the same escape the hero needed, and the trap this repository has
    now hit twice.
    """
    _ctx, ours = geo.landmass(
        MAPPROJ, (0.0, 0.0, float(MAP_W), float(MAP_H)),
        doc=geo.load("europe-lod0.json"), thin_units=5.0, min_units=60.0)
    # THE CONTEXT IS DROPPED, BECAUSE A DATA CUT IS NOT A COASTLINE.
    # data/geo/ stops at 52°E and 33°N, so Russia, Kazakhstan, the Levant and
    # North Africa arrive here as rings sliced by the box — a straight
    # diagonal down the right-hand side and a straight edge along the bottom.
    # The hero has the same cut and answers it with a fade over 320 units;
    # a 132-pixel glyph has nowhere to put a fade, and at 280 on the atlas
    # index the trapezoid reads as a rendering fault rather than as land.
    #
    # The atlas countries need no such trick: they end at real coastlines and
    # real frontiers, which is what makes the silhouette recognisable as
    # Europe in the first place. Thirteen theme glyphs and eleven homepage
    # tiles all got quieter and lighter for it.
    # AND EUROPE IS NOT AN ISLAND. data/geo/ stops at 52°E, so every glyph at
    # the full extent carried a knife-straight diagonal through Russia — the
    # rendering fault the hero was rebuilt to remove, still shipping on the
    # family with the most drawings. The same anonymous rings the hero uses,
    # thinned harder for this size, in the LAND's own tone: the two abut along
    # the cut, so with one colour there is nothing to fade and the continent
    # simply carries on to the frame edge. 5 KB, emitted once per page and
    # cloned by every glyph on it.
    beyond = "".join(
        f'<path d="{d}"/>' for d in geo.beyondmass(
            MAPPROJ, (0.0, 0.0, float(MAP_W), float(MAP_H)),
            thin_units=6.0, min_units=120.0, pad=0.0) if d)
    return ('<svg class="constel-defs" width="0" height="0" aria-hidden="true" '
            'focusable="false"><defs><g id="constel-eu">'
            + ours + "</g>"
            + (f'<g id="constel-beyond">{beyond}</g>' if beyond else "")
            + "</defs></svg>")


NUMWORDS = ("no", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
            "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty")
_TENS = {30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy",
         80: "eighty", 90: "ninety"}


def numword(k, *, cap=False):
    """A small number spelled out, because a heading is prose.

    "8 categories" as an <h2> is a figure standing where a word belongs, and
    "Eight categories" typed into the template is the figure that was true two
    hundred experiences ago — the failure this repository has already shipped
    once on /themes and once in the search index's empty state. Derived and
    spelled: one place, so the two families cannot disagree about how to say
    nine.

    IT STOPPED AT THIRTEEN, AND THE PROSE DID NOT. "Fifty countries" opened
    the homepage and the 404, "Nine regions" opened /countries, "ten kinds"
    opened /experiences — every one a literal in an f-string on a page whose
    whole argument is that its figures are derived and checkable. They were
    also all correct, which is how a typed number survives: it is right on
    the day it is written and nothing fails when it stops being. Twenty, then
    the tens, then digits, which is the ordinary editorial rule and the
    reason these were words in the first place.
    """
    k = int(k)
    if 0 <= k < len(NUMWORDS):
        w = NUMWORDS[k]
    elif k in _TENS:
        w = _TENS[k]
    elif 20 < k < 100 and (k - k % 10) in _TENS:
        w = f"{_TENS[k - k % 10]}-{NUMWORDS[k % 10]}"
    else:
        return str(k)
    return w[:1].upper() + w[1:] if cap else w


def macro_frame(data, macro):
    """Every destination in a macro region, projected — the box to frame on.

    The countries themselves would be the truer extent and `geo.landmass`
    hands back markup rather than geometry, so this frames on what the region
    is FOR: the places in it. The difference matters least where it would
    show most — a region's destinations sit inside its countries by
    construction — and the padding is a third of the region's own size.
    """
    pts = []
    for cs in macro["countries"]:
        c = data["countries"].get(cs)
        if not c:
            continue
        for r in c["regions"]:
            for t in r["cities"]:
                pts.append(project(t["lat"], t["lon"]))
    return pts


# A region is taller than it is wide, roughly balanced, or more than twice as
# wide as tall. Two boundaries, both of them descriptions rather than fitted
# numbers — 1 is "which way up is it" and 2 is "twice as wide as tall", and
# the nine fall 3 / 4 / 2 under them. The alternative was a threshold read off
# the gaps in these nine values, which is a number chosen to produce an answer
# and stops being true the day a country moves between regions.
MACRO_WIDE = 2.0


def macro_shape(data, macro):
    """How wide a macro region is against how tall, in kilometres.

    THE NINE REGIONS WERE NINE IDENTICAL BANDS AND `glyph_view` SAID WHY IN
    ITS OWN COMMENT: *held to the canvas proportion, so a set of glyphs is a
    set of boxes of the same shape and only the geography inside them
    differs.* That is visual consistency bought with editorial difference —
    the owner's second doctrine rule, written as a decision in the function
    that implements it, one commit before the rule arrived. Measured, the
    nine regions of this atlas run from 0.63 (the Baltic States, 346 km wide
    and 546 tall) to 2.75 (the Mediterranean at 3,605 x 1,311 and the
    Caucasus at 1,965 x 714), and all nine were drawn at 1.282 and composed
    identically.

    KILOMETRES RATHER THAN PROJECTED UNITS, because the projection is
    conformal and a conic's units are not the same length at 35 N and 65 N —
    the Nordics measured against the Mediterranean in canvas units is the
    scale-error finding arriving in a layout decision. Haversine on the
    region's own destinations, which is every other distance in this product.

    THE PADDED BOX IS NOT THE SHAPE. `glyph_view` adds a third of the
    region's own size as context before it frames, which pulls every aspect
    toward 1: the same nine measure 0.75 to 1.69 padded against 0.63 to 2.75
    raw. The padding is a drawing convention and the shape is the
    geography, so the composition is decided on the geography.

    AND THE COUNT IS DELIBERATELY NOT WHAT DECIDES. Destinations per region
    run 8 to 94, which looks like the obvious scale and argues something
    false: Eastern Europe holds 8 because THREE OF ITS FOUR COUNTRIES CARRY
    A TRAVEL ADVISORY, so a size derived from it would print an advisory
    artefact as an editorial judgement. That is /beyond-the-obvious's own
    finding — *the count argues the wrong way* — and photograph coverage is
    refused for a second reason: this page already spends that measurement
    on which country gets the large door, and a band drawing one measurement
    twice is what /journeys recorded.
    """
    pts = []
    for cs in macro["countries"]:
        c = data["countries"].get(cs)
        if not c:
            continue
        for r in c["regions"]:
            for t in r["cities"]:
                pts.append((t["lat"], t["lon"]))
    if len(pts) < 2:
        return 0.0, 0.0, 1.0
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    mlat, mlon = sum(lats) / len(lats), sum(lons) / len(lons)
    w = haversine({"lat": mlat, "lon": min(lons)}, {"lat": mlat, "lon": max(lons)})
    h = haversine({"lat": min(lats), "lon": mlon}, {"lat": max(lats), "lon": mlon})
    return w, h, (w / h if h else 1.0)


def indexhero(*, kicker, title, lede, art="", img="", actions="", note=""):
    """The editorial opening five indexes now share.

    THE INDEXES WERE ALL THE SAME SHAPE AND THE SHAPE WAS A LIST. A kicker, a
    60px serif h1, a lede in the right-hand column, a rule, and then rows —
    every one of /journeys, /stories, /experiences, /events and /plan opened
    identically and then ran straight into a two-column list with a
    right-aligned meta column. Measured across them: eleven of twelve
    families place an identically-sized h1 at an identical vertical position,
    which is the design-direction finding, and these five were the clearest
    case of it. A shared template is not a shared experience.

    So an index opens on something now: the family's own subject, at size,
    beside the type rather than under it. The art is a PHOTOGRAPH where the
    register holds one and the family's own drawing where it does not —
    seventeen routes on one continent for the journeys, the year drawn as a
    chart for the events, the places a story is about for the stories. Never
    a generated plate: that is the measurement that took eleven of them off
    the homepage.

    `img` is the photograph slot and it is passed rather than fetched here,
    because the KEY is the caller's business — a hero has a declared purpose
    in data/image-purposes.json and an item has its own register key. When
    both are empty the hero is type and space, which is a composition rather
    than a hole: the lede takes the measure it wants and the rule under it
    does the work the picture would.
    """
    figure = ""
    if img:
        figure = f'<figure class="iheroart shot">{img}</figure>'
    elif art:
        figure = f'<figure class="iheroart">{art}</figure>'
    if not figure:
        # NO FIGURE MEANS THE HEAD THE SITE ALREADY HAS. /events is the one
        # index whose subject cannot go in the arch — a twelve-column chart
        # has to run the full width to be read — and the first version gave
        # it the wide grid anyway, so the type sat in five columns of eleven
        # with the other six empty. An opening with nothing on the right is
        # not an opening, it is a headline with a hole beside it. The classic
        # index head puts the lede BESIDE the name, which is what that layout
        # is for, and the chart underneath does the work the picture would.
        return (
            f'<header class="pagehead index"><p class="kicker">{kicker}</p>'
            f'<h1>{title}</h1><p class="lede">{lede}</p>'
            f'{f"<div class=chips>{actions}</div>" if actions else ""}'
            f'{f"<p class=small>{note}</p>" if note else ""}</header>')
    # IT IS A `pagehead` VARIANT, NOT A NEW HEAD. The first version emitted
    # its own <header class="ihero"> and the primitive check caught it in one
    # run: pagehead fell off five pages and "a page family has grown its own
    # components" is exactly what that floor exists to say. It was also two
    # other failures at once — the head-role check requires every page to
    # declare whether it is an overture, an index or an instrument, and the
    # extent check reads the count out of the head — so replacing the head
    # silently dropped both promises. A variant keeps all three and is what
    # the design system is for.
    # AND THE PICTURE WAS THE FOURTH THING ON A PHONE, ON EVERY INDEX THAT
    # HAS ONE. Below 60rem this head is one column and the whole text block
    # came first: on /countries that is a kicker, a 38px name, a four-line
    # lede, two buttons and a three-line provenance note — 550 pixels of type
    # before the drawing that is the reason the opening exists, so the arch
    # began at 740 and the first screen carried no picture at all.
    #
    # The actions and the note are not the opening. An action is what a
    # reader does AFTER seeing the set, and the note describes the DRAWING,
    # so it belongs under it and not four hundred pixels above it. They move
    # after the figure — a DOM change rather than a rule, because they sat
    # inside `.iherotext` and a grid can only place what it can address,
    # which is the same repair the destination and country heads took.
    foot = (f'{f"<div class=chips>{actions}</div>" if actions else ""}'
            f'{f"<p class=small>{note}</p>" if note else ""}')
    # AND THE HELPER IS WHAT WAS FORCING THE GRAMMAR, so the helper changed.
    #
    # Five indexes call this and every one of them opened on a 60px h1 in a
    # narrow column beside a 4:3 figure — which is precisely the "one
    # template with the title, image and description substituted" the
    # directive names as the thing to stop. Rewriting five call sites would
    # have left the sixth to arrive next month with the old shape.
    #
    # It emits the 2036 opening now: the eyebrow in mono, the name at
    # display size, the standfirst under it, and the figure taking the wide
    # half of the stage. The classes the checks read — `pagehead index`, the
    # kicker, the extent in the head — are kept, because those are promises
    # rather than shapes and three separate assertions read them.
    return (
        f'<header class="pagehead index ed-opening ed-family-discovery">'
        f'<div class="ed-opening-copy iherotext">'
        f'<p class="kicker ed-eyebrow">{kicker}</p>'
        f'<h1>{title}</h1><p class="lede ed-intro">{lede}</p>'
        f'{f"<div class=iherofoot>{foot}</div>" if foot else ""}</div>'
        f'<div class="ed-opening-visual">{figure}</div></header>')


def region_glyph(members, frame=None, min_span=0.0, aspect=None):
    """A macro region as the countries it is made of, on the shared silhouette.

    THE ATLAS INDEX IS THE PAGE ABOUT COUNTRIES AND IT DREW NONE. /countries
    was nine headings and fifty rows of name, tagline and "6 regions · 25
    cities" — the whole of Europe as a contents list. Measured, the median
    horizontal band of it used 44% of the column and the rest was blank, and
    what was missing from that space is not more type: it is WHERE THE NORDICS
    ARE, which is the one question a reader picking a region of Europe is
    actually asking.

    A macro region is the single grouping in this atlas with real polygons
    behind it — a travel region is a set of destinations and is refused a
    boundary, and the Nordics is five whole countries Natural Earth already
    holds. So this is drawn rather than invented, and it is the same claim
    `macromap()` makes on the region's own page at full size.

    NOT THE DOT CONSTELLATION, DELIBERATELY. The homepage tiles and /themes
    light destinations on this silhouette, and using the same drawing a third
    time would make it the wallpaper its own rule warns about. This family's
    subject is countries, so countries are what is lit.

    One coastline for all nine, because the members go ON the shared clone
    rather than carrying their own copy of Europe.

    AND EACH ONE IS FRAMED ON ITS OWN GROUND. The first version drew all nine
    at the full continental extent, so nine bands down the atlas index
    carried nine identical pictures of Europe with a different corner of it
    lit — which is the homepage's eleven-maps failure, on the page directly
    under it, and the Baltic States lit about 2% of a frame the reader had
    already seen eight times. The viewBox is the members' own extent now,
    padded and held to the canvas's proportion so the glyph box does not
    change shape between bands: the Nordics is a Nordic frame, the
    Mediterranean a Mediterranean one, and the two are told apart before the
    heading is read.

    `frame` is the points to frame on — a region's destinations — because
    `geo.landmass` returns markup rather than geometry and this needs a
    bounding box. Without it the drawing falls back to the whole continent,
    which is correct rather than clever: a caller that cannot say where a
    region is gets the picture that makes no claim.
    """
    doc = geo.load("europe-lod0.json")
    if not doc:
        return ""
    _ctx, lit = geo.landmass(
        MAPPROJ, (0.0, 0.0, float(MAP_W), float(MAP_H)), doc=doc,
        only=members, highlight=members, thin_units=5.0, min_units=60.0)
    # ONE FRAMING RULE, IN ONE PLACE. This was thirty lines inline here and
    # a journey row and a story row needed the same arithmetic — see
    # `glyph_view`, which is this, lifted out. `min_span=0` keeps this
    # family's behaviour exactly: a macro region is big by construction and
    # has never needed the floor a two-city story does.
    # `min_span` defaults to zero, which is this family's original behaviour:
    # a macro region is big by construction and has never needed the floor a
    # two-city story does. A SINGLE COUNTRY does — Luxembourg framed on its
    # own two destinations is a frame in which Europe is unrecognisable, and
    # the silhouette is the whole reason the glyph works.
    # AND THE FRAME TAKES THE REGION'S OWN PROPORTION WHERE THE CALLER KNOWS
    # IT. `glyph_view` holds every frame to the canvas's 1.282 unless asked
    # otherwise, and its comment states the reason as a benefit: *a set of
    # glyphs is a set of boxes of the same shape and only the geography
    # inside them differs.* Measured on the nine macro regions, that box was
    # 42% padding for Eastern Europe and 3% for the Caucasus, and it drew a
    # 2.75 region and a 0.63 one identically. A drawing costs nothing to
    # reshape — unlike a photograph, where a derived proportion would be an
    # undeclared crop — so a caller that has measured its subject's shape
    # passes it and the frame is the geography.
    view = (glyph_view(frame, min_span=min_span, aspect=aspect) if frame
            else f"0 0 {MAP_W} {MAP_H}")
    # The data cut only where the drawing is at the full extent: a framed
    # glyph is a window on one region and the cut is not in it.
    _cut = "" if frame else cut_fade("rg", MAP_W, MAP_H, dusk_reach(), cls="datacut")
    # The same cartography `constellation()` draws, because this is the same
    # drawing: water, the land beyond the cut, frontiers. Built here rather
    # than there only because this one lights countries instead of dots, and
    # two glyph families with two cartographies is what this pass is undoing.
    vx, vy, vw, vh = (float(n) for n in view.split())
    return (f'<svg class="constel regionglyph" viewBox="{view}" '
            f'aria-hidden="true" focusable="false">'
            f'<rect class="glyph-sea" x="{vx:.0f}" y="{vy:.0f}" '
            f'width="{vw:.0f}" height="{vh:.0f}"/>'
            f'<use class="glyph-beyond" href="#constel-beyond"/>'
            f'<use class="glyph-land" href="#constel-eu"/>'
            f'<use class="glyph-bounds" href="#constel-eu"/>'
            f'{_cut}{lit}</svg>')


def head_extent(pairs):
    """What an instrument reads, on the instrument's own head line.

    THE FIVE INTELLIGENCE HEADS LEFT HALF A ROW EMPTY. The instrument role is
    a grid of `auto 1fr` — kicker, then title, baseline-aligned, with the lede
    spanning under both — and a title is rarely wider than a third of the
    page, so /discover, /map, /plan and /search each opened on a label, a
    short line and about six hundred pixels of nothing beside it. That is the
    same shape the closing statement had, one screen from the top instead of
    at the bottom.

    An index says how big its set is; an instrument should say what it is
    operating OVER, which is the same promise from the other side and the one
    thing that belongs in that column. Every figure is derived at build time
    from the same structures the tool itself reads, so it cannot claim a
    corpus the page does not have.

    It is deliberately NOT instructions. How the planner scores sits beside
    the button that runs it, and what the search box understands sits under
    the search box — that move is why these heads are short, and putting it
    back in the head would undo it.
    """
    return ('<p class="headextent">'
            + "".join(f'<span><b>{n:,}</b> {esc(what)}</span>' for n, what in pairs)
            + '</p>')


def datacut_line():
    """One sentence naming where the drawn continent stops being a coastline.

    data/geo/ is cut at 52°E because that is where this product stops writing
    about places, so Russia arrives on any full-continent drawing with a
    straight slant through it. The site has three answers to that on record
    and only one of them is available to a glyph. The homepage hero fades
    over 320 units, which needs a frame wide enough to hold a fade.
    `constel_defs` drops the CONTEXT, which works because the context is not
    the subject — and cannot work here, because the sliced ring is a country
    this atlas has a page for. Reframing cannot lose the cut either: the
    easternmost destination in the Atlas projects within a hundred units of
    it, so a frame that excludes the slant excludes the Caucasus.

    What is left is the country portrait's answer, which is to SAY IT. The
    degree is read off the dataset's own bbox, so the sentence cannot drift
    from the data that produced the picture.
    """
    lim = (geo.load("europe-lod1.json") or {}).get("bbox", [None, None, None])[2]
    if lim is None:
        return ""
    return (f" The continent stops at {lim:.0f}°E on the right, where this "
            f"atlas's map data ends, not at a coast.")


def route_line(pts):
    """A route drawn the way a printed map draws one: a casing, then a core.

    NO SINGLE COLOUR READS ON BOTH THE LAND AND THE SEA. The editorial
    cartography is cream land on a deep Atlantic, and the arithmetic is
    closed: a stroke needs a relative luminance above 0.265 to clear 3:1 on
    #123f55 and below 0.20 to clear it on #ded8ca, so nothing satisfies both.
    A route that crosses the Baltic therefore either disappears at the coast
    or shouts on the land, which is what the acid-green version was solving
    by being brighter than everything.

    Every printed map answers this with a CASING: a wider stroke in the
    ground's own light tone under a narrower one in the route's colour. The
    casing separates the line from whatever it is over, and the core carries
    the meaning — so the same line reads over cream, over the Atlantic and
    over a neighbouring route, with no colour doing work it cannot do.
    """
    if len(pts) < 2:
        return ""
    d = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    return (f'<polyline class="constel-route case" points="{d}"/>'
            f'<polyline class="constel-route" points="{d}"/>')


# FOUR FRAMES THE BUILD AND THE BROWSER MUST AGREE ON.
#
# The planner draws the route it built, which means the browser has to frame
# a set of points — a second implementation of glyph_view(). Framing is not
# projection and cannot put a place in the wrong country, but it can still
# drift, so /plan publishes what the build makes of these four and the browser
# suite asserts its own answer is identical.
#
# They are chosen for the branches: a pair that needs the min_span floor, a
# tight cluster like a five-city Italian route, a set wider than the canvas
# that has to be clamped, and a single point.
GLYPHVIEW_CASES = [
    [(100.0, 100.0), (200.0, 300.0)],
    [(420.0, 480.0), (470.0, 520.0), (500.0, 560.0)],
    [(10.0, 10.0), (990.0, 770.0)],
    [(500.0, 400.0)],
]


def country_glyph(slug, cs):
    """A country card's picture is the COUNTRY, not Europe with one bit lit.

    Five Nordic cards drew five pictures of Europe differing only in which
    shape was white, and four of the five were the same corner of the
    continent at almost the same scale. Measured on the viewBoxes the build
    emitted: Norway 789 units wide — 79% of the canvas — because the frame is
    held to the canvas proportion and Norway is 616 units tall; Denmark and
    Iceland both exactly 340, which is `glyph_view`'s own floor.

    None of that is a bug. A tall country genuinely needs a wide 16:9 frame,
    and the floor exists because the shared silhouette stops reading as Europe
    below it. The conclusion is that the SHARED SILHOUETTE IS THE WRONG
    DRAWING FOR THIS CARD: it answers "where in Europe", the macro map at the
    top of the same page already answers that at full size, and repeating it
    five times is the aperture-as-wallpaper rule in a different drawing.

    What a reader choosing between five countries wants is which. Norway is
    long and ragged, Sweden is a blade, Denmark is a scatter, Finland is a
    fist, Iceland is an island — five genuinely different pictures, and the
    one thing the row could not show before.

    lod1 rather than the lod0 clone, because this is the country at its own
    size rather than a corner of a continent, and `principal_frame` rather
    than the raw bbox, because Portugal's bbox is 1,400 km of Atlantic with
    the Azores in the far corner and the mainland filling nine per cent of it.
    """
    doc = geo.load("europe-lod1.json")
    if not doc:
        return ""
    _ctx, lit = geo.landmass(
        MAPPROJ, (0.0, 0.0, float(MAP_W), float(MAP_H)), doc=doc,
        only=[cs], highlight=[cs], thin_units=1.1, min_units=6.0)
    if not lit:
        return ""
    bb, _outside = geo.principal_frame(doc, slug)
    if not bb:
        return ""
    corners = [project(lat, lon)
               for lon in (bb[0], bb[2]) for lat in (bb[1], bb[3])]
    view = glyph_view(corners, pad_frac=0.16, min_pad=10.0, min_span=0.0)
    vx, vy, vw, vh = (float(n) for n in view.split())
    return (f'<svg class="constel countryglyph" viewBox="{view}" '
            f'aria-hidden="true" focusable="false">'
            f'<rect class="glyph-sea" x="{vx:.0f}" y="{vy:.0f}" '
            f'width="{vw:.0f}" height="{vh:.0f}"/>{lit}</svg>')


def glyph_view(pts, pad_frac=0.34, min_pad=90.0, min_span=340.0,
               aspect=None):
    """The viewBox that frames a set of projected points, held to the canvas.

    Lifted out of `region_glyph`, which had it inline, because the same
    question was being asked by three families and answered once. THE FIRST
    VERSION OF THAT FUNCTION DREW ALL NINE MACRO REGIONS AT THE FULL
    CONTINENTAL EXTENT, so nine bands carried nine identical pictures of
    Europe with a different corner lit and the Baltic States lit about 2% of
    a frame the reader had already seen eight times. A journey row and a
    story row had exactly that fault and kept it.

    `min_span` is the floor a route and a story need and a region does not.
    A macro region is big by construction; a story set in two cities is not,
    and framed on its own extent alone it zooms until the drawing stops
    being recognisable as Europe at all — which is the whole reason the
    silhouette is there.
    """
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = max((x1 - x0), (y1 - y0)) * pad_frac
    pad = max(pad, min_pad)
    x0, x1, y0, y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad
    if (x1 - x0) < min_span:
        grow = (min_span - (x1 - x0)) / 2
        x0, x1 = x0 - grow, x1 + grow
    # Held to the canvas proportion, so a set of glyphs is a set of boxes of
    # the same shape and only the geography inside them differs.
    w, h = x1 - x0, y1 - y0
    # The frame's proportion is the canvas's unless the caller asks for
    # another. A journey row is a wide band and a route is usually wide, so
    # framing one at 1.28 makes a tall picture beside a short paragraph and
    # four hundred pixels of nothing under it.
    #
    # AND `aspect="own"` IS NO HOLD AT ALL, which is what the nine macro
    # regions needed and what the paragraph above was refusing them. The
    # hold is why nine regions running 0.54 to 3.21 on this projection were
    # nine boxes of one shape — the fault the doctrine's second rule names —
    # and the first repair passed each region's measured aspect as `want`.
    # THAT DID NOTHING FOR THE ONE REGION IT WAS WRITTEN FOR: the hold only
    # ever GROWS the short axis, the Mediterranean's padded box is already
    # 986 of a 1,000-unit canvas, so growing width to reach 2.75 clamped at
    # the canvas and the emitted frame came back at 1.30 — the whole
    # continent with a corner lit, which is this function's own recorded
    # failure. There is nothing to grow toward on the widest set in the
    # atlas; the honest frame is the padded box as measured, which keeps the
    # `min_pad` legibility floor and keeps the shape the projection actually
    # draws.
    if aspect == "own":
        want = w / h
    else:
        want = aspect or (MAP_W / MAP_H)
    if w / h < want:
        grow = (h * want - w) / 2
        x0, x1 = x0 - grow, x1 + grow
    else:
        grow = (w / want - h) / 2
        y0, y1 = y0 - grow, y1 + grow
    # And slid back onto the drawing: the padding is CONTEXT and there is no
    # context outside the canvas. Clamped where the set is wider than the
    # frame it is drawn on.
    w, h = x1 - x0, y1 - y0
    if w >= MAP_W:
        x0, w = 0.0, float(MAP_W)
    else:
        x0 = min(max(x0, 0.0), MAP_W - w)
    if h >= MAP_H:
        y0, h = 0.0, float(MAP_H)
    else:
        y0 = min(max(y0, 0.0), MAP_H - h)
    return f"{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}"


def offframe_line(pts, data, listed=True):
    """One sentence when a drawing cannot hold one of the places it is about.

    ONE DESTINATION IN THREE HUNDRED AND NINETEEN PROJECTS ABOVE THE CANVAS.
    Longyearbyen is at 78°N and lands at y = −48 on the 1000×780 window every
    unframed constellation is drawn in — so `/interests/wild` printed "19 of
    the 319 destinations are tagged wild nature", drew nineteen circles, and
    showed eighteen. The nineteenth was outside the viewBox, which renders as
    nothing and reports nothing: the same class as a <use> of an id that is
    not there, and invisible for the same reason — the picture looks
    finished.

    The alternatives were worse. Extending the canvas moves every map on the
    site for one point. Framing these drawings on their own extent deletes
    the comparison they exist to make — seventeen interest pages are only
    comparable while all seventeen are drawn at one extent. Placing the dot
    at the edge puts a mark where the place is not.

    So the atlas does here what it already does at 52°E: it says so. The
    sentence names the place and its latitude, and it is derived, so it
    appears only while the fault does and says nothing the moment the canvas
    or the dataset changes.

    AND `listed` IS THERE BECAUSE THE SENTENCE MADE A CLAIM ABOUT THE PAGE
    AROUND IT. It ended "that place is in the list below" unconditionally,
    which is true of the three callers that print a list of their own set and
    false of the 404, whose drawing is the whole body — so the one page a
    reader reaches having already failed to find something pointed them at a
    list that is not there. A shared function cannot know what follows it,
    so the caller says. That is the same failure as the journey map caption
    promising a note under the leg after the note was removed: removing or
    never having a surface leaves the prose pointing at it, and only
    rendering the page finds it.
    """
    out = [p for p in pts
           if not (0.0 <= p[0] <= MAP_W and 0.0 <= p[1] <= MAP_H)]
    if not out:
        return ""
    names = []
    for cid, rec in data["cities"].items():
        xy = project(rec["city"]["lat"], rec["city"]["lon"])
        if any(abs(xy[0] - x) < 0.6 and abs(xy[1] - y) < 0.6 for x, y in out):
            names.append((rec["city"]["name"], rec["city"]["lat"]))
    if not names:
        return (f" {n_of(len(out), 'place')} in this set "
                f"{'lies' if len(out) == 1 else 'lie'} outside the frame.")
    said = (" " + and_list([f"{esc(nm)} at {lat:.0f}°N" for nm, lat in names])
            + (" is" if len(names) == 1 else " are")
            + " above the top of this frame: the drawing stops where this "
              "atlas's map data does")
    if not listed:
        return said + "."
    return (said + ", and "
            + ("that place is " if len(names) == 1 else "those places are ")
            + "in the list below.")


def constellation(pts, extra="", route=False, frame=False, cut=False,
                  ocean=True, aspect=None, mark=None, term=None,
                  labels=None, overlay=""):
    """A set of real destinations lit on the shared silhouette.

    THE ARGUMENT DRAWN, AND THE REASON IT REPLACED ELEVEN PAINTINGS. The
    homepage body was eight abstract plates over "Find your kind of Europe"
    and three more over the journeys — eleven purple gradients in a column,
    which is placeholder art doing the job of a picture. The plate system was
    already measured as unable to carry a hero; it cannot carry this either.

    What it is replaced with is not a better painting, it is the DATA: every
    one of the 63 mountain destinations lit across the Alps, the Pyrenees, the
    Carpathians and the Scandes, and every one of the 200 with history lit
    almost everywhere — and the difference between those two shapes is the
    thing the tile is trying to say.

    ALL OF THEM, NEVER A SELECTION. The count on the tile is the number of
    dots on it, so a reader can check. Picking "the twelve best mountain
    destinations" would be a ranking this atlas does not hold.

    NO APERTURE. Eleven doors on one page is the signature as wallpaper.
    """
    # A ROUTE HAS A DIRECTION AND THE DRAWING DID NOT SHOW IT. Thirteen
    # identical dots on a line say "these places"; a journey says "this one,
    # then that one, ending there", which is the whole thing the row's own
    # kicker spells out in arrows. The terminals take the transit convention —
    # a ring with the ground's colour in its core — and the stops between them
    # stay plain, so the eye reads the ends first and the sequence after.
    last = len(pts) - 1
    line = route_line(pts) if route else ""
    # FRAMED ON ITS OWN GROUND WHERE THE SUBJECT IS A ROUTE OR A SET OF
    # PLACES, and never where the subject is REACH. Three featured journeys
    # drew three identical continents with a thumbnail-sized squiggle in a
    # different corner of each — the nine-macro-regions fault, on the
    # homepage, one band under the strip that was rebuilt to stop exactly
    # that. Framed, the Hanseatic Arc is a Baltic picture and the Adriatic
    # Run is an Adriatic one, and the line is big enough to read.
    #
    # /themes is deliberately NOT framed: what separates thirteen themes is
    # how far each one reaches, three countries against seven, and that
    # comparison only exists while all thirteen are drawn at one extent.
    # Framing them would delete the argument the family is making.
    view = (glyph_view(pts, aspect=aspect) if (frame and pts)
            else f"0 0 {MAP_W} {MAP_H}")
    # THE DATA CUT SHOWED RAW ON EVERY INDEX OPENING. All 21 `.iheroart`
    # drawings are at the full extent, which means the straight diagonal at
    # 52°E runs right through the arch — and there it is the worst case on
    # the site, because the ground behind these is the sea panel, so the cut
    # is a hard edge between parchment and deep navy rather than between
    # parchment and paper. The plates have faded along it since the picture
    # half got its data cuts and the hero since the hero was drawn; this
    # family said it in a sentence under the picture and showed it raw above.
    # A sentence and a fade are not alternatives: /map does both.
    #
    # Above the ground and below the marks, which is datacut()'s own rule, so
    # a lit destination east of the cut keeps its dot. The wide reach rather
    # than the measured one for the same reason.
    #
    # AND A FRAMED DRAWING WAS REFUSED THE FADE BY A FLAG RATHER THAN BY A
    # MEASUREMENT. The suppression read `not (frame and pts)` — a framed
    # glyph is usually a small window on one corner of Europe and the cut is
    # usually outside it, which is true and is not the same as never. The
    # Arctic-to-Mediterranean journey runs 69°N to 38°N, so its frame IS the
    # whole canvas, and its hero drew a knife-straight diagonal through
    # Russia: the exact rendering fault this fade exists to remove, on the
    # largest drawing in the family.
    #
    # The fade's gradients are `userSpaceOnUse` in the projection's own
    # coordinates and a framed viewBox is a WINDOW on those same coordinates
    # rather than a transform of them, so emitting it is geometrically
    # correct at any frame — it simply falls outside a small one. What
    # decides is therefore whether the window reaches the cut, which is
    # arithmetic on the viewBox and not a flag on the caller.
    _vx, _vy, _vw, _vh = (float(v) for v in view.split())
    _reaches = (_vx + _vw) > (MAP_W - dusk_reach()[0]) or (_vy + _vh) > (
        MAP_H - dusk_reach()[2])
    cut = (cut_fade("ih", MAP_W, MAP_H, dusk_reach(), cls="datacut")
           if cut and (not (frame and pts) or _reaches) else "")
    # WATER, A COAST AND CLOSED SEAMS — the three things this drawing never
    # had. It was one flat grey silhouette on the page's own paper: no sea,
    # so a bay and the margin are the same colour; no coast, so the edge is
    # mushy; and the lod0 rings are simplified per country, so independently
    # thinned neighbours leave white cracks running through the landmass.
    # `.card-map` has painted the water since the cartography split and this
    # family never got it.
    #
    # The ocean is a rect on the glyph's own frame rather than a background on
    # whatever contains it, because the containers disagreed: a card painted
    # it, a row did not, and the same drawing came out a picture in one and a
    # stain in the other. The coast is a `<use>` UNDER the land stroked wider
    # — only the half outside the fill shows, which is exactly the coast and
    # never an internal frontier, because a neighbour's fill covers it.
    vx, vy, vw, vh = (float(n) for n in view.split())
    # A MARK IS SIZED IN USER UNITS AND A FRAMED DRAWING'S UNITS ARE NOT THE
    # SAME SIZE TWICE. `glyph_view()` fits the frame to the route, so the
    # three journeys on the homepage were drawn at 1000, 422 and 340 units
    # across and rendered at the same 690 pixels — and a 5-unit dot is 3.4
    # pixels on the first and 10.1 on the last. Measured: a 2.9x swing in
    # apparent mark size between two rows of one band, which is why the
    # Hanseatic Arc read as two blobs joined by a rope. It is the /themes
    # finding one family over: a radius in viewBox units is a radius in
    # pixels at exactly one width.
    #
    # So the build normalises the frame away and the family keeps its own
    # size: `mark` is the radius at the reference 1000-unit frame, scaled by
    # what this frame actually is, and the drawing is marked `framed` so the
    # stylesheet's own radii stand aside. A CSS `r` beats a presentation
    # attribute and there is no value that hands it back, so the guard has
    # to be on the selector.
    z = vw / MAP_W
    rattr = (lambda m: f' r="{m * z:.2f}"') if (frame and pts and mark) else (lambda m: "")
    dots = "".join(
        f'<circle class="{"term" if route and i in (0, last) else ""}"'
        f'{rattr(term if (route and i in (0, last) and term) else mark)} '
        f'cx="{x:.0f}" cy="{y:.0f}"/>'
        for i, (x, y) in enumerate(pts))
    framed = " framed" if (frame and pts and mark) else ""
    ground = (f'<rect class="glyph-sea" x="{vx:.0f}" y="{vy:.0f}" '
              f'width="{vw:.0f}" height="{vh:.0f}"/>') if ocean else ""
    bounds = '<use class="glyph-bounds" href="#constel-eu"/>' if ocean else ""
    if ocean:
        ground += '<use class="glyph-beyond" href="#constel-beyond"/>'
    # A NAME BESIDE A MARK, WHERE THE CALLER HAS ONE. A route drawn with no
    # stops named is a line: the journey plate on the homepage has to say
    # Tromso and Rome or it is decoration. Sized from the frame rather than
    # in CSS for the reason this file records four times over — 11 units is
    # 11 x (width / frame) on screen, and a framed drawing's frame is not the
    # same size twice — so the text is scaled by `z` to land at one pixel
    # size whatever the route's extent turns out to be.
    names = ""
    if labels and frame and pts:
        names = '<g class="constel-names">' + "".join(
            f'<text x="{x + 13 * z:.1f}" y="{y + 4 * z:.1f}" '
            f'font-size="{11 * z:.2f}">{esc(nm)}</text>'
            for (x, y), nm in zip(pts, labels) if nm) + "</g>"
    return (f'<svg class="constel{extra}{framed}" viewBox="{view}" '
            f'aria-hidden="true" focusable="false">{ground}'
            f'<use class="glyph-land" href="#constel-eu"/>'
            f'{bounds}'
            f'{cut}{line}<g class="constel-lit">{dots}</g>{names}{overlay}</svg>')


def themes_index(data):
    """Five plates, and the page drew none of the thirteen shapes its own
    closing sentence describes.

    `head_figure()` prefers a photograph and falls back to the drawing, and
    its docstring states the contract: *the drawing is never lost — the
    caller emits it below with `moved_drawing()` when a photograph took its
    place.* Three callers use it. The country page honours that, the theme
    page honours that, and **this index never called `moved_drawing` at
    all** — so from the commit where the thirteenth theme photograph landed,
    every glyph was built and discarded, and the note under the list went on
    saying:

        Each shape beside a theme is that theme's own eight places on the
        continent, drawn to the same frame so the thirteen can be compared:
        a knot is an argument about one corner of Europe, a scatter is one
        about the whole of it. Drawn from Natural Earth 1:110m admin 0
        countries, public domain.

    A promise of a drawing beside each theme, on a page with none, crediting
    Natural Earth for land nobody drew — the inverse of *a page that draws
    land names where the land came from*. That is the
    fourteen-call-sites-forgot-the-motif shape in a helper with a two-call
    contract, and `c_same_frame` could not see it: it skipped any page
    carrying fewer than two glyphs, so *says and draws nothing* was outside
    its reach.

    THE SHAPES ARE THE OPENING NOW, drawn to one frame where they can be
    compared, and the photographs stay in the rows — which is the register
    spent on the surface where a reader is choosing between thirteen things
    on LOOK. Both bands are complete in their own register: the shapes are
    the reach, the rows are the places.

    AND THE REACH HAD A SECOND AXIS NOBODY PRINTED. The page states how many
    countries a theme crosses, 3 to 8. It also crosses 2 to 6 of the nine
    **corners of Europe**, and that is the closing sentence as a number:
    Renaissance Europe is two corners, Medieval and Island Europe are six.
    Between them the thirteen reach 88 of the 319 destinations, 37 of the 50
    countries and all nine corners — against /europe-in's twelve queries,
    which reach the whole Atlas, because a theme is an authored set of eight
    and a motion is a query over everything. See `docs/themes-redesign.md`.
    """
    idx = data["cities"]
    images = data.get("images")

    # ── ONE PASS ─────────────────────────────────────────────────────
    facts = {}
    allstops, allctry, allmacro = set(), set(), set()
    for t in data["themes"]:
        countries, places, pts = [], [], []
        for stop in t["stops"]:
            n = idx[stop["city"]]
            if n["country"]["name"] not in countries:
                countries.append(n["country"]["name"])
            places.append(n["city"]["name"])
            pts.append(project(n["city"]["lat"], n["city"]["lon"]))
            allstops.add(stop["city"])
        macros = {_macro_of(data, idx[s["city"]]["country"]["slug"])
                  for s in t["stops"]}
        allctry |= {idx[s["city"]]["country"]["name"] for s in t["stops"]}
        allmacro |= macros
        facts[t["slug"]] = {"countries": countries, "places": places,
                            "pts": pts, "ncorner": len(macros)}

    # NEAR-DISJOINT, MEASURED. Thirteen authored sets of eight could overlap
    # heavily and a reader cannot tell by looking; 15 of the 78 pairs share a
    # stop and the worst shares three — Florence, Rome and Venice, between
    # Renaissance Europe and the Grand Tour, which is a real relationship
    # rather than a duplication.
    shared, worst = 0, (0, "", "")
    ts = data["themes"]
    for a in range(len(ts)):
        for b in range(a + 1, len(ts)):
            k = len({x["city"] for x in ts[a]["stops"]}
                    & {x["city"] for x in ts[b]["stops"]})
            if k:
                shared += 1
            if k > worst[0]:
                worst = (k, ts[a]["name"], ts[b]["name"])
    npairs = len(ts) * (len(ts) - 1) // 2

    # DERIVED, because the note states it. Every theme holds eight stops
    # today; a hard-coded eight in the prose is the figure that was true two
    # hundred destinations ago, which this repository has already shipped.
    sizes = sorted({len(t["stops"]) for t in data["themes"]})
    held_say = (f"every one of these holds {numword(sizes[0])}"
                if len(sizes) == 1
                else f"they hold between {numword(sizes[0])} and "
                     f"{numword(sizes[-1])}")

    # ── 01 · SAME FRAME, DIFFERENT ARGUMENT ──────────────────────────
    tiles = []
    for t in data["themes"]:
        f = facts[t["slug"]]
        tiles.append(
            f'<a class="thtile" href="/themes/{t["slug"]}">'
            f'{constellation(f["pts"], extra=" constel-theme")}'
            f'<span class="thtilen">{f["ncorner"]} of '
            f'{len(data["macros"])} corners</span>'
            f'<span class="thtilenm">{esc(t["name"])}</span>'
            f'<span class="thtilep">{n_of(len(f["countries"]), "country")}'
            f'</span></a>')
    thopen = f"""
  <div class="pagehead index">
    <p class="kicker">Discovery without a map of borders</p>
    <h1 class="mega">Europe, organised by what you came for.</h1>
    {head_extent([(len(data["themes"]), "themes"),
                  (len(allstops), "destinations"),
                  (len(allmacro), "corners of Europe")])}
    <p class="lede">Medieval Europe is not a country. Neither is sacred Europe, or Viking
    Europe, or the Europe you reach only by train. {numword(len(data['themes']), cap=True)}
    of them cut across the Atlas, and each place under one of them stays linked to the
    country it is actually in.</p>
  </div>
  {constel_defs()}
  <div class="thgrid">{"".join(tiles)}</div>
  <p class="small">Each shape is that theme&rsquo;s own {numword(sizes[0])} places on the
  continent, drawn to the same frame so the {numword(len(data['themes']))} can be
  compared: a knot is an argument about one corner of Europe, a scatter is one about the
  whole of it. {geo.sources_line(geo.load("europe-lod0.json"))}</p>"""

    # ── 02 · CROSS-BORDER EUROPE ─────────────────────────────────────
    thcross = f"""
  <div class="sheettext">
    <h2 class="mega">A theme is a <em class="lit">crossing</em>, not a
    country.</h2>
    <p class="lede">Between them the {numword(len(data['themes']))} reach
    {len(allstops)} of the {len(idx)} destinations, {len(allctry)} of the
    {len(data['countries'])} countries and all {numword(len(allmacro))} corners of
    Europe &mdash; and each one is a different crossing rather than a slice of the
    same map. Reach runs from {numword(min(f['ncorner'] for f in facts.values()))}
    corners to {numword(max(f['ncorner'] for f in facts.values()))}.</p>
    <p class="note">They are also near-disjoint, which a reader cannot see by
    looking: {shared} of the {npairs} pairs share a destination at all, and the most
    any two share is {numword(worst[0])} &mdash; {esc(worst[1])} and
    {esc(worst[2])}, which is a real relationship rather than a duplication. The
    {len(data['motions'])} queries on <a href="/europe-in">Europe in Motion</a> reach
    every destination in the Atlas; these {numword(len(data['themes']))} reach a
    quarter of it, because a query runs over everything and a theme is
    {numword(sizes[0])} places somebody chose.</p>
  </div>"""

    # ── 03 · THIRTEEN ARGUMENTS ──────────────────────────────────────
    #
    # NOT THIRTEEN ROWS, AND NOT THIRTEEN CARDS. The owner read the first
    # version of this page and named the fault exactly: *keep the existing
    # page, add premium CSS and components around it, call it a redesign.*
    # The thirteen themes had been a card grid, then rows, then rows with a
    # photograph — three presentations of one list, and the list was the
    # layout every time. `docs/redesign-doctrine.md` is the rule that came
    # out of it and `tools/monotony.js` is the instrument: nothing here had
    # ever counted repetition, so a page could be thirteen identical
    # siblings and pass every gate.
    #
    # A theme holds a photograph, a geography, an authored summary, eight
    # places and a reach. That is a composition, so each theme gets one —
    # and THE COMPOSITION'S SCALE FOLLOWS THE THEME'S REACH, which is what
    # makes the layout argue what the closing sentence says rather than
    # captioning it. A theme crossing a MAJORITY of the nine corners of
    # Europe gets the wide band; three or four corners the feature; and the
    # one theme that is an argument about a single corner gets an intimate
    # one. Majority of nine is five — a threshold rather than a taste — and
    # it falls 6 / 6 / 1, with Renaissance Europe alone at the bottom,
    # which is precisely the knot the sentence is about.
    #
    # NO NUMBERS ON THEM. A numeral would claim an order the data does not
    # have — the same caveat this page already publishes about the eight
    # places — and a second numbering inside a plate sequence is the
    # 753-page double-numbering fault.
    #
    # THE MAP IS THE CONSTANT AND THE PICTURE IS THE VARIABLE. Every
    # argument draws on the same continental frame, because reach is what
    # separates the thirteen and `region_glyph`'s recorded refusal applies:
    # framed on its own extent, each becomes a picture of a different place
    # and the thirteen stop being comparable at all.
    majority = len(data["macros"]) // 2 + 1
    args = []
    for k, t in enumerate(data["themes"]):
        f = facts[t["slug"]]
        scale = ("wide" if f["ncorner"] >= majority
                 else "feat" if f["ncorner"] >= 3 else "tight")
        # THE SIDE ALTERNATES, AND THAT IS WHAT MAKES A SEQUENCE A SEQUENCE.
        # Six identical wide bands in a column is a listing with a bigger
        # component, which is the fault one level up; a magazine alternates
        # because the eye needs the rhythm to read a run of spreads as one
        # argument rather than as a stack.
        flip = " arg-flip" if k % 2 else ""
        key = "theme:" + t["slug"]
        shot = (f'<figure class="argshot">'
                f'{picture(images, key, w=1600, h=1200, alt=(images or {}).get(key, {}).get("alt") or t["name"], sizes="(max-width: 52rem) 92vw, 46vw", credit=False)}'
                f'</figure>' if held(images, key) else
                f'<figure class="argshot">'
                f'{ed_slot(key, shape="wide", label=t["name"])}</figure>')
        args.append(
            f'<article class="arg arg-{scale}{flip}">'
            f'<figure class="argmap">'
            f'{constellation(f["pts"], extra=" constel-theme")}'
            f'<figcaption><span class="capmain">'
            f'{n_of(len(f["places"]), "place")} across '
            f'{n_of(len(f["countries"]), "country")}.</span>'
            f'<span class="capsrc">{f["ncorner"]} of '
            f'{len(data["macros"])} corners of Europe, on the same frame as '
            f'the other {numword(len(data["themes"]) - 1)}.</span>'
            f'</figcaption></figure>'
            f'{shot}'
            f'<div class="argsay">'
            f'<p class="kicker">{esc(t["strapline"])}</p>'
            f'<h2><a href="/themes/{t["slug"]}">{esc(t["name"])}</a></h2>'
            f'<p class="lede">{esc(t["summary"])}</p>'
            f'<p class="argplaces">{" &middot; ".join(esc(p) for p in f["places"])}</p>'
            f'{golink("/themes/" + t["slug"], "Follow " + t["name"])}'
            f'</div></article>')
    # THE ROWS OWE THEIR ATTRIBUTION AND PAY IT ONCE, under the list. The
    # photograph inside a row carries no figcaption, because a credit's own
    # links inside a row's link split the anchor — so the container pays,
    # exactly as the homepage's row of eight does. The licence asks for the
    # photographer and the provider, not for one caption per thumbnail.
    _imgs = images or {}
    _shot = [t for t in data["themes"] if ("theme:" + t["slug"]) in _imgs]
    themecred = ""
    if _shot:
        _who = ", ".join(dict.fromkeys(
            f'<a href="{esc(_imgs["theme:" + t["slug"]]["source"])}" rel="noopener" '
            f'target="_blank">{esc(_imgs["theme:" + t["slug"]]["photographer"])}</a>'
            for t in _shot))
        _n = len(data["themes"]) - len(_shot)
        themecred = (f'<p class="sheetcred rowcred">Photographs by {_who} on Pexels.'
                     + (f' The {numword(_n)} without one carry their own places '
                        f'instead.' if _n else "") + '</p>')
    nwide = sum(1 for t in data["themes"]
                if facts[t["slug"]]["ncorner"] >= majority)
    ntight = sum(1 for t in data["themes"]
                 if facts[t["slug"]]["ncorner"] < 3)
    thirteen = f"""
  <div class="sheettext">
    <h2 class="mega">{numword(len(data['themes']), cap=True)} arguments about
    Europe.</h2>
    <p class="lede">Each one is a photograph of what it feels like, a map of where it
    is and the sentence it makes. {held_say.capitalize()}, so the number of places is
    not what separates them &mdash; what separates them is how far they cross, and the
    <em>size</em> of each argument below is that reach: {numword(nwide)} of them cross a
    majority of the {numword(len(data['macros']))} corners of Europe and
    {"one" if ntight == 1 else numword(ntight)} is an argument about a single
    corner.</p>
  </div>
  <div class="args">{"".join(args)}</div>
  {themecred}"""

    # ── 04 · THEME, THEN PLANNER ─────────────────────────────────────
    thplan = f"""
  <div class="sheettext">
    <h2 class="mega">A theme is not an itinerary.</h2>
    <p class="lede">The places under each theme are <em>not</em> in travelling order, and
    the theme pages draw them with no path between them on purpose. Renaissance Europe is
    three countries and the Grand Tour is four; Thermal Europe runs from Iceland to the
    Caucasus, and reading it top to bottom would be a fortnight of flights.</p>
    <p class="note">Put the ones you want into the <a href="/plan">Planner</a> and it
    orders them by real distance, prices the days and says where the long legs are.
    That is the difference between an argument about Europe and a trip through it.</p>
  </div>"""

    # ── 05 · OPEN THE DOOR ───────────────────────────────────────────
    thclose = f"""
  <div class="istart">
    <h2 class="mega">Come for one thing.</h2>
    <p class="lede">Then find that the continent is organised around it &mdash; and that
    every place under a theme is still an ordinary page in the same Atlas, written to the
    same template as Paris.</p>
    <p class="keepgo"><a class="btn" href="/discover">Find your kind of Europe</a>
    <a class="storygo" href="/countries">Or open the atlas &rarr;</a></p>
  </div>"""

    PLATES = [("thopen gal", "Same frame, different argument", thopen, "themes"),
              ("thcross pine", "Cross-border Europe", thcross, "crossing"),
              ("thargs gal", "Thirteen arguments", thirteen, "arguments"),
              ("thplan pine", "Theme, then Planner", thplan, "planner"),
              ("thclose gal", "Open the door", thclose, "open")]
    body = f"""
{crumbs([("Europe", "/discover"), ("Themes", None)])}
{plate_sequence(PLATES)}
"""
    return "/themes/index.html", page(
        "Themes", body, path="/themes", area="countries",
        accent="territory", hero=True,
        description="Cross-border ways into Europe: medieval, sacred, Viking, alpine, maritime and rail Europe, each a real sequence of places.",
    )


def theme_page(data, t):
    idx = data["cities"]
    rows = []
    for stop in t["stops"]:
        n = idx[stop["city"]]
        rows.append(
            f"""<a class="row" href="{urls.city(n['country'], n['region'], n['city'])}">
            <div><h2>{esc(n['city']['name'])}</h2><p class="rowsub">{esc(stop['why'])}</p></div>
            <p class="rowmeta">{esc(n['country']['name'])}</p></a>"""
        )
    countries = []
    for stop in t["stops"]:
        cn = idx[stop["city"]]["country"]["name"]
        if cn not in countries:
            countries.append(cn)

    # A CONSTELLATION, AND THE ABSENCE OF THE LINE IS THE POINT.
    #
    # The theme pages were the largest family carrying no geography at all —
    # thirteen pages, eight stops each, three to eight countries apiece, and
    # nothing on the page showed that the argument crosses a continent.
    #
    # But a theme must NOT borrow the journey page's route line. The rail on
    # this page has said "a theme is a way of seeing, not a route" since it
    # was written, and a line between Florence, Urbino and Rome would say the
    # opposite in the one language a reader reads first. Renaissance Europe
    # has no day one. So: the same aperture, the same projection, the same
    # dots — and deliberately no path element. What distinguishes this family
    # from journeys is exactly what is not drawn.
    tpts = [(*project(idx[st["city"]]["city"]["lat"], idx[st["city"]]["city"]["lon"]),
             urls.city(idx[st["city"]]["country"], idx[st["city"]]["region"],
                       idx[st["city"]]["city"]),
             idx[st["city"]]["city"]["name"])
            for st in t["stops"]]
    thememap = pointsmap(
        tpts, "th" + "".join(ch for ch in t["slug"] if ch.isalnum())[:14],
        f'{len(tpts)} places in {len(countries)} countries, and no line between '
        f'them: a theme is a way of seeing rather than a route, and these are '
        f'not in travelling order.',
        f'Map of the {len(tpts)} places in {t["name"]}, unlinked',
        note=f'Coastline from <a href="/sources">Natural Earth</a>, '
             f'public domain.') if len(tpts) >= 2 else ""

    # NO `pageband` HERE: THIS FAMILY MOVED TO `head_figure`. The band puts
    # the photograph ABOVE the head, which is a magazine's cover; the theme
    # page puts it BESIDE the name, which is its opening spread, and the
    # drawing moves down to a band of its own. `photoband` was left assigned
    # and never interpolated when that happened — a dead variable that reads
    # as a rendered band to anybody grepping for one, and the acquisition
    # suite grepped for exactly that.
    # ONE ARCHITECTURE, TWO PICTURES. Eleven of the thirteen themes carry a
    # photograph and two do not, and the two without were not a designed
    # state — they were what is left when the band is removed: an overture
    # head whose measure is 14ch inside a 1,168px column, so the first 780
    # pixels of the page were a headline with seven hundred and fifty of
    # nothing beside it, and the theme's own map began below the fold.
    #
    # A theme's map is its signature moment — eight places and no line
    # between them, which is the whole argument the family makes — so where
    # there is no photograph it takes the opening the photograph would have
    # had. The two states then differ in what the picture IS and not in the
    # shape of the page. Where a photograph exists the map keeps its place
    # under the head, because a picture and a drawing say different things
    # and neither replaces the other.
    # THE PICTURE SITS BESIDE THE NAME NOW, WHICH IS WHAT THE MEASUREMENT
    # BELOW WAS ASKING FOR. Stacked, one of the two states always loses: the
    # photograph pushed the h1 to y=750 and the map pushed it to 1,019, so a
    # reader met a gondola or eight dots and had to scroll to learn what
    # either was about. Beside it, both are above the fold and neither is
    # first — which is the opening spread of a magazine rather than its
    # cover, and the grammar the whole atlas is being rebuilt to.
    key = f"theme:{t['slug']}"
    headpic = head_figure(data, key, thememap, alt_fallback=t["name"])
    below = moved_drawing(
        data, key, thememap,
        "Where the eight places are, and how far apart. A theme is not a "
        "route, so there is no line between them.")
    # AND THE NAME COMES BEFORE THE PICTURE. Measured at 1280x900: with the
    # photograph opening the page the h1 sat at y=750 and with the map at
    # 1,019 — so a reader on a laptop met a gondola, or eight dots, and had
    # to scroll to find out what either was about. `want=2.6` is already
    # asked of the drawing and geography refuses it: Tallinn to Rhodes is
    # tall, and a frame cannot be wider than the canvas. So the picture does
    # not become a band; the name goes above it.
    #
    # Kicker, name, picture, then the sentence — which is a magazine opening
    # and not an invention: the headline announces, the picture carries the
    # desire, and the standfirst under it is where a standfirst has always
    # been. Both states take it, because the fault was the family's and not
    # the photograph's.
    # THE THEME'S OWN EIGHT STOPS, IN PICTURES. This is the one family whose
    # register rows are filled today — eleven theme heroes — so the opening
    # is a real photograph, and the eight destinations under it are the
    # sequence that says what the theme MEANS rather than where it goes.
    tmstrip_items = []
    for _stop in t["stops"]:
        _n = data["cities"].get(_stop["city"])
        if not _n:
            continue
        _t2, _r, _c = _n["city"], _n["region"], _n["country"]
        tmstrip_items.append({
            "key": f"city:{_c['slug']}/{_r['slug']}/{_t2['slug']}",
            "alt": _t2["name"], "label": _t2["name"],
            "href": urls.city(_c, _r, _t2)})
    _tmshots = ed_strip(data.get("images"), tmstrip_items, limit=8)
    tmstrip = (f'<section class="ed-section">'
               + ed_section_head("The theme", "Where it takes you")
               + _tmshots + "</section>") if _tmshots else ""
    body = f"""
{crumbs([("Europe", "/discover"), ("Themes", "/themes"), (t["name"], None)])}
{ed_opening(
    eyebrow=t["strapline"],
    title=t["name"],
    intro=t["summary"],
    visual=headpic,
    family="discovery")}
{tmstrip}
<div class="headmeta ed-section">
  <p class="orient">{len(t['stops'])} places across {len(countries)}
  {"countries" if len(countries) != 1 else "country"} · not an itinerary</p>
  {chips(t["interests"], data["interests"])}
</div>

{below}

<div class="rows">{''.join(rows)}</div>

<section class="practical" aria-label="Practical">
  <div>
    <h2 class="mini">Not an itinerary</h2>
    <p>A theme is a way of seeing, not a route: these places are not in travelling
    order and most people take three or four of them, not all. For an order that
    respects distance, put the ones you want into the
    <a href="/plan">Planner</a>.</p>
  </div>
  <div>
    <h2 class="mini">Countries it crosses</h2>
    <p>{esc(", ".join(countries))}</p>
  </div>
  <div>
    <h2 class="mini">Keep it</h2>
    <p><button class="btn ghost" type="button" data-save="theme:{esc(t['slug'])}" data-kind="Theme"
       data-label="{esc(t['name'])}" data-url="/themes/{esc(t['slug'])}">Save to My Europe</button></p>
  </div>
</section>
"""
    return f"/themes/{t['slug']}/index.html", page(
        t["name"], body, path=f"/themes/{t['slug']}", area="countries",
        accent="territory",
        description=t["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
    )


# ── stories ───────────────────────────────────────────────────────────

def stories_index(data):
    """The European editorial desk: nine essays, and the pictures spent.

    THE PAGE WAS A HEAD, ONE PHOTOGRAPH, ONE LEAD AND EIGHT IDENTICAL ROWS,
    and every repair that got it there was right. It was nine three-column
    grids each holding one card — the desk taxonomy as the layout, 5,792
    pixels — and then a contents page with an empty middle third, and then a
    lead with its own constellation over eight rows. What was left is the
    sum: one shape eight times, on 31,851 bytes, with **one `<img>` where
    the register holds eight**.

    That is /experiences' finding word for word, on the family whose
    material is writing: *the pictures were already bought and were being
    spent on one strip.* `stories-hero` plus seven `story:` rows is eight
    photographs available to this page and it drew one. Nothing is acquired
    by this rebuild. See `docs/stories-redesign.md` for the source audit,
    the coverage audit, the brief's nine bands mapped onto what the data
    holds, and the four bands the data refuses with the count behind each.
    """
    sections = sorted({s["section"] for s in data["stories"]})
    byline = sorted(data["stories"],
                    key=lambda s: (s["published"], s["title"]), reverse=True)
    images = data.get("images") or {}
    idx = data["cities"]

    def pts_of(st):
        out = []
        for cid in st.get("places") or ():
            n = idx.get(cid)
            if n:
                out.append(project(n["city"]["lat"], n["city"]["lon"]))
        return out

    def glyph(st):
        # A story that names no place gets no drawing, on the destination
        # page's rule: nothing in its place rather than something invented.
        pts = pts_of(st)
        return constellation(pts, extra=" constel-theme", frame=True,
                             cut=True, mark=14) if pts else ""

    lead, rest = byline[0], byline[1:]

    # ── 01 · THE DESK ────────────────────────────────────────────────
    # THE OPENING PHOTOGRAPH BELONGS TO THE PAGE AND NOT TO A STORY.
    # `stories-hero` is a Liechtenstein village — a picture of Europe's
    # people and their ground, which is exactly what the headline claims and
    # exactly NOT a claim about any of the nine. Putting it behind a story's
    # title would be the hash-drawn landscape in a different costume: a
    # generic picture standing in for a specific piece, which is the fault
    # this family exists to demonstrate against.
    #
    # So it is a BLEED under the head rather than a panel beside it — a
    # bleed leaves the column and is a change of movement, which is the one
    # of the seven image scales that says "this is the page, and here is
    # what it is about" without saying it about an essay.
    # AND THE LEDE NAMED SIX DESKS OF NINE, NEXT TO A DERIVED "NINE".
    # It read "nine desks — people, history, food, faith, nature and
    # culture", with the count generated and the list typed, so the sentence
    # stated its own extent and then silently dropped Places, Travel and
    # Adventure. That is `pop_line`'s shape in a list rather than a field:
    # coverage that looks like a policy, and a third of the set missing from
    # the one sentence that introduces it. Both halves are derived now, so a
    # tenth desk arrives in the prose on the build that adds it.
    #
    # THE BRIEF'S DESK BAND IS ANSWERED HERE RATHER THAN AS A ROOM. It asks
    # for a chip index under the opening, and a chip is a FILTER: this page
    # loads no JavaScript (its only `<script>` is the inert JSON-LD block)
    # and no per-desk page exists, so nine chips would be nine controls that
    # do nothing — `data-rotate`, which shipped 232 bytes of copy on the
    # homepage for the life of a band waiting for a rotator nobody wrote.
    # Naming the desks is what the chips were actually FOR, and a name in
    # the head is an extent rather than a directory.
    desknames = ", ".join(x.lower() for x in sections[:-1]) + \
        " and " + sections[-1].lower()
    open_ = f"""
  <div class="storyopen">
    <h1 class="mega">A continent is people before it is
    <em class="lit">places</em>.</h1>
    <p class="lede">{numword(len(data['stories']), cap=True)} pieces across
    {numword(len(sections))} desks &mdash; {desknames}. Every story links
    into the Atlas, and every Atlas page a story touches links back, so
    reading and planning are the same motion.</p>
  </div>
  <figure class="storybleed">{photo(images, "stories-hero", w=2400, h=1200,
      eager=True, sizes="100vw",
      alt="A village under snowcapped mountains in Liechtenstein.")}</figure>"""

    # ── 02 · THE LEDGER ──────────────────────────────────────────────
    # ALL NINE, PRINTED ONCE. The lead is the ledger's first entry at size
    # rather than a band of its own: two bands, one of them "read this
    # first" and the other "here are all nine", would print the same set
    # twice to say two things — the fault 220 place pages had, where a strip
    # and the rows underneath were the same places. One set, one band, and
    # the newest piece is given the weight.
    #
    # And the lead is the NEWEST, which is a date rather than a judgement.
    # That is why the opening above is not photographic today: the newest
    # piece is `The long walk nobody finishes`, filed to Adventure, and the
    # register holds no photograph for it. Choosing the newest PHOTOGRAPHED
    # piece instead would be an editorial judgement wearing a rule's
    # clothes, and this page already refused that once.
    ledger = f"""
  <div class="pagehead index">
    <p class="kicker">The desk</p>
    <h2 class="mega">Everything filed, newest first.</h2>
    {head_extent([(len(data['stories']), 'pieces'),
                  (len(sections), 'desks'),
                  (len({c for st in data['stories'] for c in (st.get('places') or ())}),
                   'places written about')])}
  </div>
  <a class="storylead storyleadwide" href="{urls.story(lead)}">
    <div class="storyart">{glyph(lead)}</div>
    <div><p class="kicker">{esc(lead["section"])} &middot; {esc(lead["reading"])} &middot;
    {esc(lead["published"])}</p>
    <h3>{esc(lead["title"])}</h3>
    <p class="rowsub">{esc(lead["standfirst"])}</p>
    <p class="storygo">Read the story &rarr;</p></div></a>
  <div class="rows">{"".join(
      f'<a class="row storyrow" href="{urls.story(s)}">'
      f'<div><p class="kicker">{esc(s["section"])}</p>'
      f'<h3>{esc(s["title"])}</h3>'
      f'<p class="rowsub">{esc(s["standfirst"])}</p></div>'
      f'<p class="rowmeta">{esc(s["published"])}<br>'
      f'<span class="small">{esc(s["reading"])}</span></p></a>'
      for s in rest)}</div>
  <p class="note">One piece per desk, which is why there is no band of desks
  above this one: {numword(len(sections))} headings over one item each is the
  taxonomy as the layout, and it is the shape this page was built as and
  threw away.</p>"""

    # ── THE FEATURE ──────────────────────────────────────────────────
    # THE BRIEF ASKS FOR A FEATURE STORY AND THIS PAGE HAD REFUSED THE
    # QUESTION NEXT DOOR TO IT. The recorded refusal is *the lead cannot be
    # the photographic one* — the ledger leads on the NEWEST piece, which is
    # a date rather than a judgement, and the newest is filed to Adventure
    # where the register holds nothing. That is still true and it is about
    # the LEDGER. A feature is a different question: which piece can carry a
    # photograph at size, which is a fact about the register and not a
    # ranking of the writing.
    #
    # So the two coexist, which is what the brief's own architecture does:
    # the ledger leads TYPOGRAPHICALLY on the newest, and the feature band
    # carries the newest piece the register holds a photograph of and the
    # ledger has not already led on. Today that is `The ferry is the
    # attraction`. Both are derived, so the day Adventure is photographed
    # the ledger keeps its lead and the feature moves down one rather than
    # drawing the same piece twice — which is the *same set printed twice*
    # fault this page already avoided once by refusing a lead band.
    feat = next((st for st in byline
                 if st is not lead and held(images, "story:" + st["slug"])), None)
    # NO NEW COMPONENT: `.ed-feature` IS THE SCALE THIS BAND IS. The seven
    # image scales already hold it — *a feature is asymmetric at 1.35
    # against .65, because two equal columns read as a layout and an unequal
    # pair reads as a picture with something to say* — and that is the
    # prototype's 54/46 stated as a proportion rather than a percentage.
    # *No new primitive until repeated structure has actually emerged*, and
    # what emerged here is a user for one that was already written.
    feature = "" if not feat else f"""
  <div class="ed-feature">
    <figure class="ed-feature-media">{picture(images, "story:" + feat["slug"],
        w=1600, h=1200, sizes="(min-width: 62rem) 62vw, 100vw",
        alt=feat["title"])}</figure>
    <div class="ed-feature-say">
      <p class="kicker">{esc(feat["section"])} &middot; {esc(feat["reading"])}
      &middot; {esc(feat["published"])}</p>
      <h2>{esc(feat["title"])}</h2>
      <p>{esc(feat["standfirst"])}</p>
      <p><a class="storygo" href="{urls.story(feat)}">Read the story
      &rarr;</a></p>
    </div>
  </div>"""

    # ── 03 · THE IDEA ────────────────────────────────────────────────
    # THE PAGE'S OWN SENTENCE, PROMOTED FROM A FOOTNOTE TO A ROOM. It was
    # the last paragraph on the page, at caption size, under a source note.
    # It is the reason this family looks the way it does and the reason
    # seven of these nine have a photograph and two do not, so it is the
    # thing a reader should meet before the pictures rather than after them.
    idea = """
  <div class="storyidea">
    <h2 class="mega">A story is not a place.</h2>
    <p class="lede">A landscape chosen by chance once put tower blocks above
    an essay on the last unlogged forest in Europe. So a piece here is
    illustrated by a photograph somebody took of the thing it is about, or
    by the places it is set in drawn on the atlas, or by nothing &mdash;
    and never by a picture picked from the hash of its own name.</p>
  </div>"""

    # ── 04 · THE PICTURES ────────────────────────────────────────────
    # SEVEN OF THE NINE, AT SIZE, EACH LINKED TO ITS OWN PIECE. This is
    # where the library goes. A story's photograph belongs to that story, so
    # nothing here is generic and nothing is reused: the seven keys are
    # `story:<slug>` and the two pieces without one are absent from the band
    # rather than filled with something else.
    #
    # `columns` RATHER THAN A GRID, which is /experiences' own measured
    # reason one family over: a grid row is as tall as its tallest item, so
    # a long title beside a short one pays for the difference on every row.
    # Column-major is right here because the order is the ledger's own,
    # newest first, down the left.
    #
    # AND EACH TILE CARRIES A DESK AND A TITLE AND NOT THE STANDFIRST.
    # The first version repeated the standfirst verbatim from the ledger two
    # bands up — *the same set printed twice to say two things*, which is
    # the fault 220 place pages had where a strip and the rows under it were
    # the same places. A title under a photograph is a CAPTION and names
    # what the picture is of; a second copy of the sentence is a second
    # contents list.
    #
    # The alternative was tried on paper and refused: putting the seven
    # photographs into the ledger's own rows and deleting this band halves
    # the page and makes every picture a row-sized thumbnail, which is what
    # /journeys' index already measured as saying nothing. The brief asks
    # for both and is right to — *photography at editorially meaningful
    # moments, while the main nine-story ledger remains typographic.*
    #
    # AND A CREDIT IS A LINK, SO THE PICTURE CANNOT GO INSIDE ONE. The first
    # version wrapped `photo()` in the tile's `<a>`, and `picture()`'s
    # figcaption carries the two links Pexels' terms require: an `<a>` may
    # not contain an `<a>`, so the parser closed the tile at the inner one
    # and reparented the credit out of the `<picture>` it belongs to. The
    # browser suite found **21 links painting nothing even with focus on
    # them** — `picture:focus-within .credit` could no longer reach them.
    # So `credit=False`, and the attribution is paid once under the row.
    # AND THE FEATURE IS NOT DRAWN TWICE. `photographed` is the register's
    # claim and stays the whole seven; `shots` is what this row DRAWS, which
    # is the seven less the one the feature band has already given the full
    # proportion to. A tile repeating a picture four bands after it was the
    # subject of its own band is the *same set printed twice* fault, and the
    # band's own figures are derived so the sentence cannot state a count
    # the row does not show.
    photographed = [st for st in byline if held(images, "story:" + st["slug"])]
    shots = [st for st in photographed if st is not feat]
    pics = "".join(
        '<figure class="picstory">'
        + f'<a class="picgo" href="{urls.story(st)}">'
        + picture(images, "story:" + st["slug"], w=1600, h=900,
                  sizes="(min-width: 62rem) 46vw, 100vw",
                  alt=st["title"], credit=False)
        + f'<p class="kicker">{esc(st["section"])}</p>'
        f'<h3>{esc(st["title"])}</h3></a>'
        + "</figure>"
        for st in shots)
    # AND THE BAND PAYS ITS ATTRIBUTION ONCE, which is what every other row
    # of pictures on this site already does — the homepage's row of eight,
    # the destination rail, the country and theme strips, five call sites
    # spelling `sheetcred rowcred`. Seven credits under seven tiles is the
    # accent-on-every-row failure in a licence line: the provenance is the
    # same kind of fact on all seven, so stating it per tile states nothing
    # that distinguishes them and puts somebody else's brand seven times
    # into a page that is EuropeDoor's. Once, under the row, with each
    # photographer linked to the photograph's own page.
    picwho = ", ".join(dict.fromkeys(
        f'<a href="{esc(images["story:" + st["slug"]]["source"])}" rel="noopener"'
        f' target="_blank">{esc(images["story:" + st["slug"]]["photographer"])}</a>'
        for st in shots))
    picband = f"""
  <div class="sheettext">
    <h2 class="mega">Photographed.</h2>
    <p class="lede">{numword(len(photographed), cap=True)} of the
    {numword(len(data['stories']))} carry a photograph somebody took of what
    the piece is about. {("The newest of them is the feature above, so here "
    "are the other " + numword(len(shots)) + ". ") if feat else ""}The
    {numword(len(data['stories']) - len(photographed))} without one carry the
    places they are set in, and will carry a photograph the day there is one
    to carry &mdash; the page does not change, only the register does.</p>
  </div>
  <div class="storypics">{pics}</div>
  <p class="sheetcred rowcred">Photographs by {picwho} on Pexels.</p>"""

    # ── 05 · WHERE THEY HAPPEN ───────────────────────────────────────
    # THE DRAWING IS HERE RATHER THAN AT THE TOP, AND THAT IS THE PAGE'S
    # OWN RECORDED REFUSAL KEPT RATHER THAN OVERTURNED. As an OPENING, a
    # scatter of nine stories' places is a picture of nothing in particular
    # standing in front of nine pieces of writing — not chosen by a hash,
    # and still not about any of them. As the band that says *reading and
    # planning are the same motion*, the same drawing is about exactly one
    # thing: which parts of the Atlas these essays reach into.
    allpts = [p for st in byline for p in pts_of(st)]
    touched = sorted({c for st in data["stories"] for c in (st.get("places") or ())
                      if c in idx},
                     key=lambda c: idx[c]["city"]["name"])
    inplace = f"""
  <div class="sheettext">
    <h2 class="mega">Where they happen.</h2>
    <p class="lede">Every place the {numword(len(data['stories']))} pieces are
    set in, lit at once. Each of them has a page in the Atlas, and each of
    those pages links back to the essay &mdash; which is the whole of what
    this desk is for.</p>
  </div>
  <figure class="storyplaces">
    {constellation(allpts, extra=" constel-theme", cut=True, mark=5)}
    <figcaption><span class="capwhat">The
    {n_of(len(touched), "destination")} the nine essays are set in, on the
    same projection as every other map here. Named in the
    ledger above and on each piece.</span>
    <span class="capsrc">{geo.sources_line(geo.load("europe-lod0.json"))}</span></figcaption>
  </figure>"""

    # ── 06 · THE FEED ────────────────────────────────────────────────
    # THE ONE THING A DESK OWES ITS READERS THAT THIS ONE DID NOT HAVE.
    # Nine dated, authored essays, a public JSON API and a sitemap — and no
    # way at all to be told when a tenth arrives. It was a `.note.onward`,
    # which wears the interactive colour and is deliberately rare; the Stay
    # layer already composes an ACTION — a rule, the sentence saying what it
    # will do, and the action beside it, with no border box, radius, shadow
    # or fill — so this takes that grammar rather than inventing a second.
    feed = """
  <div class="storyfeed">
    <p class="storysay">An Atom feed of every story, newest first, with the
    desk it was filed to and the standfirst as written. No tracking
    parameter, no email address, and nothing to sign up to. It is declared in
    the shell of every page for a reader whose browser looks for one, and
    said here in words for a reader whose browser does not.</p>
    <p class="keepgo"><a class="btn" href="/stories/feed.xml">Follow the desk</a></p>
  </div>"""

    # ── 07 · THE DOOR ────────────────────────────────────────────────
    # NOT `.sheet-send`, WHICH IS /journeys' CLOSE — a graphite band built
    # to carry a photograph behind a 72% scrim. Naming this plate `send`
    # gave a bone publication's last words light type on near-black. Fourth
    # class-name collision on this page's own run, after `.sendsay`,
    # `.closesay` and a duplicated `.deskart figcaption`.
    send = f"""
  <div class="composesay">
    <h2 class="mega">Read one. Then go.</h2>
    <p class="lede">Every piece ends where it is set, and every place it
    names is a page you can plan from.</p>
    <p class="keepgo">{golink('#the-desk', 'Back to the ledger')}
    {golink('/discover', 'Or open the Atlas')}</p>
  </div>"""

    PLATES = [("open gal", "The desk", open_, "the-opening"),
              ("feature paper", "The feature", feature, "the-feature"),
              ("ledger gal quiet", "Everything filed", ledger, "the-desk"),
              ("idea pine", "A story is not a place", idea, "the-idea"),
              ("pics gal", "Photographed", picband, "photographed"),
              ("inplace gal quiet", "Where they happen", inplace, "where-they-happen"),
              ("feed gal", "The feed", feed, "the-feed"),
              ("readgo gal", "Read one, then go", send, "read-one")]
    body = f"""
{crumbs([("Europe", "/discover"), ("Stories", None)])}
{constel_defs()}
{plate_sequence(PLATES)}
"""
    return "/stories/index.html", page(
        "Stories", body, path="/stories", area="stories", hero=True,
        description="Editorial from across Europe: people, history, food, faith, nature and culture, each linked into the Atlas.",
    )

def story_page(data, s):
    # THE ESSAY HEAD IS A `pagehead` VARIANT, like the other five family
    # heads. It was a free-standing `.essayhead`, which cost two things
    # nobody had counted: nine pages declared no head ROLE, because the role
    # check reads a `.pagehead` and there was none to read, and the
    # `pagehead` primitive's reach floor was nine pages short of the truth.
    # An essay is an overture by that check's own definition — one thing, and
    # the name is the event. Visually neutral, because `.essayhead`'s rules
    # sit later in the stylesheet at equal specificity, so its margin and its
    # type scale still win.
    #
    # AND THE REASON ABOVE WAS FIRST WRITTEN AS AN HTML COMMENT, which ships.
    # This file already records that failure once, on the homepage, where the
    # weight invariant caught it; here it was `c_no_fake_entity`, because the
    # sentence contained the word "AS" and \bAS\b is a Norwegian company
    # form. A reason belongs in the source that writes the page.
    paras = "".join(f"<p>{esc(p)}</p>" for p in s["body"])
    updated = ("" if s["updated"] == s["published"]
               else f', updated <time datetime="{esc(s["updated"])}">{esc(s["updated"])}</time>')
    tagchips = "".join(
        f'<a class="chip" href="/search?q={esc(t.replace(" ", "+"))}">{esc(t)}</a>'
        for t in s["tags"]
    )
    # THE OPENING IMAGE IS THE STORY'S OWN GEOGRAPHY.
    #
    # A photograph if the register holds one — the same rule the homepage
    # hero and the destination page follow — and where it does not, the map
    # of where this happens rather than a plate whose motif was chosen by a
    # hash and was, on the forest story, a skyline.
    has_photo = bool((data.get("images") or {}).get("story:" + s["slug"]))
    storyart = (f'<figure class="ed-bleed ed-bleed-tall">'
                + picture(data["images"], "story:" + s["slug"], w=2400, h=1030,
                          alt=s["title"], eager=True, sizes="100vw")
                + '</figure>') if has_photo else storymap(data, s)
    # WHERE THIS HAPPENS MOVES INTO THE MARGIN.
    #
    # It was a full section of rows below the save button — the last thing
    # on the page, read by nobody who stopped at the end of the story, and
    # the reason the essay's right-hand third was empty for its whole
    # length. In the margin it is beside the paragraph that mentions the
    # place, it is the same list the map above is drawn from, and it is what
    # fills the space a 38rem measure leaves in a 76rem page.
    #
    # No card, no panel, no .rail: a rail is the destination page's furniture
    # and this family is not that one. A hairline, a label and the names.
    margin = ""
    if s.get("places"):
        rows = "".join(
            f'<a class="marginplace" href="{urls.city_by_id(data["cities"], cid)}">'
            f'<span class="mp-name">{esc(data["cities"][cid]["city"]["name"])}</span>'
            f'<span class="mp-country">{esc(data["cities"][cid]["country"]["name"])}</span></a>'
            for cid in s["places"]
        )
        margin = (f'<aside class="essaymargin" aria-label="Where this happens">'
                  f'<h2 class="mp-label">Where this happens</h2>{rows}'
                  f'<p class="mp-note">Every one of them is in the Atlas.</p></aside>')
    # A NAME IN A META ROW IS NOT A BYLINE, AND THE NEW HEAD DROPPED THE ONE
    # WORD THAT SAYS SO. The row carries four tokens — the desk, the reading
    # time, the date and the author — and with "By" removed the fourth is a
    # proper noun among three facts, which a reader has to guess at. The
    # section audit caught it on all nine stories in the run that shipped the
    # head; nothing a contact sheet or a count could see, because the name is
    # present, placed and legible. The claim was never that the author is on
    # the page, it is that the reader can tell it IS the author.
    # AND A STORY NAMED DESTINATIONS THAT JOURNEYS PASS THROUGH AND LINKED
    # NONE OF THEM. §34 of the specification asks an article record for
    # "Related journeys"; measured against the built site, eight of the nine
    # stories have one to six journeys with a leg in a destination the story
    # is written about, and every story page linked zero. The relation needs
    # no authored field and manufactures nothing — a story's `places` are
    # destinations and a journey's legs are destinations, so both ends of
    # this are the same entity, which is exactly what `stops_at` is NOT and
    # why that one waits instead.
    #
    # The heading says what the relation is rather than what a reader might
    # hope it is: a journey through Mostar is not a journey about the bridge.
    # That distinction is the one this session already had to repair on 96
    # place pages, and writing the honest heading first is cheaper than
    # writing it twice.
    seenj, jrows = set(), ""
    for cid in s.get("places", []):
        for j in data["back"].get(cid, {}).get("journeys", []):
            if j["slug"] in seenj:
                continue
            seenj.add(j["slug"])
            jrows += (f'<a class="row" href="{urls.journey(j)}">'
                      f'<div><h3>{esc(j["name"])}</h3>'
                      f'<p class="rowsub">{esc(j["strapline"])}</p></div>'
                      f'<p class="rowmeta">{j["days"]} days</p></a>')
    jband = section(
        "Journeys through these places", f'<div class="rows">{jrows}</div>',
        lede="Routes with a night in one of the destinations this piece is "
             "written about. They are not about the story.") if jrows else ""

    body = f"""
{crumbs([("Europe", "/discover"), ("Stories", "/stories"), (s["title"], None)])}
<article class="essay">
<header class="ed-story-opening">
  <p class="ed-story-meta"><span>{esc(s['section'])}</span><span>{esc(s['reading'])}</span>
  <span><time datetime="{esc(s['published'])}">{esc(s['published'])}</time></span>
  <span>By {esc(s['author'])}</span></p>
  <h1>{esc(s['title'])}</h1>
  <p class="ed-intro">{esc(s['standfirst'])}</p>
</header>
{storyart}
<div class="essaywrap{'' if margin else ' nomargin'}">
  <div class="essaybody">{paras}</div>
  {margin}
</div>
<div class="essayfoot">
  <div class="chips">{tagchips}</div>
  <p><button class="btn ghost" type="button" data-save="story:{esc(s['slug'])}" data-kind="Story"
     data-label="{esc(s['title'])}" data-url="/stories/{esc(s['slug'])}">Save to My Europe</button></p>
</div>
</article>
{jband}
{ad_slot("/stories/" + s["slug"])}
"""
    return f"/stories/{s['slug']}/index.html", page(
        s["title"], body, path=f"/stories/{s['slug']}", area="stories",
        description=s["standfirst"][:180],
        scripts=["/assets/js/my-europe.js"],
        # NO SOCIAL CARD, AND THAT IS THE RULE RATHER THAN AN OMISSION.
        #
        # "A story is not a place, and its picture may not be drawn from a
        # hash. A photograph first if the register holds one; never an
        # illustration." The story PAGE was rebuilt on storymap() for that,
        # and the story INDEX had its nine hash-drawn cards removed. This
        # line went on passing motif=None, which is exactly the instruction
        # to pick the landscape from the hash of the slug — on the one
        # picture that is rendered inside somebody else's product, where
        # nobody here would ever see it.
        #
        # The alternative to a hash-drawn landscape is not a better hash. A
        # plate IS an illustration, so no motif is allowed either; the
        # register holds no photographs; and rasterising storymap() would
        # need a second renderer for map geometry that does not exist. So a
        # shared story link carries its title and its standfirst and no
        # image, until the register holds a photograph for it.
        og=None,
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Stories", "/stories"),
                           (s["title"], f"/stories/{s['slug']}")]),
            {"@context": "https://schema.org", "@type": "Article",
             "headline": s["title"], "description": s["standfirst"],
             "url": ORIGIN + urls.story(s),
             "articleSection": s["section"],
             "keywords": s["tags"],
             "author": {"@type": "Organization", "name": s["author"]},
             "publisher": LD_PUBLISHER,
             "datePublished": s["published"], "dateModified": s["updated"],
             "isAccessibleForFree": True},
        ],
    )


# ── the map ───────────────────────────────────────────────────────────

MAP_W, MAP_H = 1000, 780

# THE HOMEPAGE HERO'S OWN WINDOW ON THE SAME PROJECTION. Wider and deeper than
# the atlas frame, because its subject is the continent rather than a set of
# places: Europe is drawn where it always is and the land carries on past it
# into Asia and Africa, from beyond-lod0.json, quietly.
#
# The numbers are the largest window whose edges show no data cut. Checked
# against beyond-lod0.json's own bbox under this projection: the 102°E cut
# runs from x=1,489 at 36°N to y=-192 at 68°N and the 8°N cut from y=1,003 at
# 50°E outward, so neither is inside (0, 0)-(1120, 800) at any latitude, and
# no fade has to hide anything. Widening past this would put one back.
HERO_VIEW = (0.0, 0.0, 1120.0, 800.0)
LON0, LON1, LAT0, LAT1 = -25.0, 45.0, 33.0, 71.5


# One projection, used by everything that draws Europe: the big map, the
# journey overlays, the locator on a country page, the homepage strip.
#
# The version this replaced claimed in its docstring to be "corrected at 52°N
# so Europe is not stretched sideways" and then computed
# `(x - MAP_W/2) * (k / cos(52°)) + MAP_W/2` — where k was itself cos(52°), so
# the whole correction multiplied x by exactly 1.0 and did nothing. Europe had
# been drawn 60% too wide since the map was written, and nobody caught it
# because there were no coastlines to look wrong: 313 dots on an empty
# rectangle are the right shape by definition. Real geography is what made the
# bug visible, which is an argument for real geography on its own.
MAPPROJ = geo.Projection((LON0, LAT0, LON1, LAT1), MAP_W, MAP_H, pad=0.0)


def project(lat, lon):
    """Equirectangular, genuinely corrected at the middle of the extent."""
    return MAPPROJ.xy(lat, lon)


def maplist(data, flat=False):
    """The map, as a list — the accessible alternative the UI specification
    asks for.

    A point map is a picture. `role="img"` with a label says what the picture
    is *of*, and that is all it can do: it cannot tell a screen-reader user
    that Bergen exists, where it is, or how to open it. So the same 319
    places are here as text, grouped by macro region and giving each one's
    coordinates, and the map's `aria-describedby` points at it.

    This is deliberately not `display:none`. It is a <details> that anyone can
    open, because a "text version" nobody sighted ever sees is a text version
    that rots — the same reason alt text on a decorative image is worse than
    no image. It also answers the flat question the map cannot: what is
    actually in the Atlas, in a form you can search with ctrl-F.
    """
    by_macro = {}
    for cid, n in sorted(data["cities"].items(), key=lambda kv: kv[1]["city"]["name"]):
        by_macro.setdefault(n["country"]["macro_name"], []).append(n)
    blocks = []
    for macro in sorted(by_macro):
        items = "".join(
            f'<li><a href="{urls.city(n["country"], n["region"], n["city"])}">'
            f'{esc(n["city"]["name"])}</a> — {esc(n["country"]["name"])}, '
            f'{esc(n["region"]["name"])}. '
            f'<span class="mono">{n["city"]["lat"]:.2f}°N, {n["city"]["lon"]:.2f}°E</span></li>'
            for n in by_macro[macro]
        )
        blocks.append(f'<h3>{esc(macro)} <span class="small">{len(by_macro[macro])}</span></h3>'
                      f'<ul class="stack cols">{items}</ul>')
    # AND THE COUNTRIES, because twenty of the fifty are drawn small enough
    # that their shape is the only way in: Monaco and Vatican City are a
    # ringed point, and Andorra, Liechtenstein, San Marino, Malta and the
    # Baltic republics render between 3.6 and 12 pixels wide on a phone.
    # WCAG 2.5.8 allows a small target where the same function is available
    # from a control on the SAME page that is not small; this list is that
    # control, and it did not carry countries.
    countries = "".join(
        f'<li><a href="{urls.country(c)}">{esc(c["name"])}</a></li>'
        for c in sorted(data["countries"].values(), key=lambda c: c["name"])
    )
    blocks.insert(0, f'<h3>Every country <span class="small">'
                     f'{len(data["countries"])}</span></h3>'
                     f'<ul class="stack cols">{countries}</ul>')
    # AND IT IS A BAND NOW RATHER THAN A DISCLOSURE, on the one page where
    # it is the most complete content there is. The docstring above argues
    # that a text version nobody sighted ever sees is a text version that
    # rots, and a closed `<details>` is most of the way to that: fifty
    # countries and all 319 destinations with coordinates, grouped by macro
    # region, behind a summary line. `aria-describedby` still points at it,
    # a visible equivalent is strictly better than a hidden one, and the
    # only thing lost is the summary — which is now the band's own head.
    intro = (f'<p class="small">The map above is a picture and cannot be read '
             f'out. This is the same data as text, with coordinates, and it '
             f'is the accessible alternative \u2014 not a reduced version of '
             f'it.</p>')
    if flat:
        return (f'<div class="maplist maptwin" id="maplist">{intro}'
                f'{"".join(blocks)}</div>')
    return (f'<details class="maplist" id="maplist">'
            f'<summary>Every place on this map, as a list '
            f'({len(data["cities"])} places, grouped by region)</summary>'
            f'{intro}{"".join(blocks)}</details>')


def map_page(data):
    images = data.get("images") or {}
    dots, info, placedots = [], {}, []
    for cid, n in sorted(data["cities"].items()):
        c, r, t = n["country"], n["region"], n["city"]
        x, y = project(t["lat"], t["lon"])
        tags = " ".join(sorted(set(t["interests"]) | set(r["interests"])))
        adv = " advisory" if c.get("advisory") else ""
        dots.append(
            f'<a class="dot{adv}" id="dot-{esc(cid.replace("/", "-"))}" '
            f'href="{urls.city(c, r, t)}" data-tags="{esc(tags)}" data-id="{esc(cid)}" '
            f'data-name="{esc(t["name"])}" data-country="{esc(c["name"])}">'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2"></circle>'
            f'<title>{esc(t["name"])}, {esc(c["name"])}</title></a>'
        )
        # What the popup shows. Sent as data rather than read out of the DOM
        # so the summary can be a sentence rather than a title attribute.
        info[cid] = {
            "n": t["name"], "c": c["name"], "r": r["name"],
            "s": t["summary"], "u": urls.city(c, r, t),
            "i": sorted(set(t["interests"]) | set(r["interests"])),
            "la": t["lat"], "lo": t["lon"],
            "p": len(t.get("places", [])), "e": len(t.get("experiences", [])),
            "adv": bool(c.get("advisory")),
        }
        # AND THE PHOTOGRAPH, WHICH THE REGISTER HELD FOR 103 OF THESE AND
        # THIS SURFACE SPENT ON NONE. The popup's own comment listed what it
        # carries — "name, region, a sentence, the distance, and a way in" —
        # five things, and the specification's map popup asks for six. The
        # missing one is the picture, and the picture was already bought:
        # `city:<cid>` is a register key this build resolves for the planner's
        # leg tiles, so the most-used surface in the product for CHOOSING a
        # destination showed every fact about a place except what it looks
        # like. Fifth family on *the pictures were already bought and were
        # being spent on one surface*, and nothing is acquired for it.
        #
        # THE DIFFERENCE FROM THE PLANNER IS WHERE THE URL LIVES, AND IT IS
        # THE BETTER HALF. `planner.js` fetches atlas.json and writes an
        # `<img>` at runtime, so `checks.py`'s guard against a published page
        # referencing an unregistered file has no reach there — which is why
        # the credit is carried rather than composed in JavaScript. /map
        # BAKES its data into an inert `application/json` block, so this URL
        # is in the shipped HTML and that guard can see it. The credit still
        # travels with the picture, composed by `credit_html` — the one
        # function that knows Pexels' rule — because a second implementation
        # of a licence obligation is the one thing this repository has
        # already learned not to have.
        _mshot = photo_href(images, "city:" + cid, 640)
        if _mshot:
            _mrow = images["city:" + cid]
            # ABSENT RATHER THAN NULL on the 210 with no photograph, because
            # present-but-empty says "we have this" and then does not.
            info[cid]["sh"] = _mshot
            info[cid]["sa"] = _mrow.get("alt") or t["name"]
            info[cid]["sc"] = credit_html(_mrow)
        for pl in t.get("places", []):
            px, py = project(pl["lat"], pl["lon"])
            placedots.append(
                f'<a class="placedot" href="{urls.place(c, r, t, pl)}">'
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6"></circle>'
                f'<title>{esc(pl["name"])} · {esc(PLACE_KIND_NAMES[pl["kind"]])}</title></a>'
            )
    filters = "".join(
        f'<label><input type="checkbox" name="layer" value="{esc(i["slug"])}">'
        f'<span aria-hidden="true">{esc(i["icon"])}</span> {esc(i["name"])}</label>'
        for i in data["taxonomy"]["interests"]
    )
    # Journey overlays. The legs are projected here rather than in the
    # browser so the line and the dots cannot disagree about where a city is.
    jdata = []
    for j in data["journeys"]:
        pts = []
        for leg in j["legs"]:
            n = data["cities"][leg["city"]]
            x, y = project(n["city"]["lat"], n["city"]["lon"])
            pts.append({"x": round(x, 1), "y": round(y, 1), "id": leg["city"],
                        "name": n["city"]["name"]})
        jdata.append({"slug": j["slug"], "name": j["name"], "days": j["days"],
                      "url": urls.journey(j), "pts": pts})
    fromoptions = "".join(
        f'<option value="{esc(cid)}">{esc(n["city"]["name"])}, {esc(n["country"]["name"])}</option>'
        for cid, n in sorted(data["cities"].items(),
                             key=lambda kv: (kv[1]["country"]["name"], kv[1]["city"]["name"]))
    )
    joptions = "".join(
        f'<option value="{esc(j["slug"])}">{esc(j["name"])} — {j["days"]} days</option>'
        for j in data["journeys"]
    )

    # ── the land ──────────────────────────────────────────────────────
    #
    # Countries are drawn at build time into the same projection the dots use,
    # from the same function, so a coastline and the city on it cannot
    # disagree about where they are. That is the same reason the journey legs
    # are projected here rather than in the browser, and it is worth the
    # repetition: two projections is a bug that renders.
    #
    # One <path> per country, all of its islands in that one path, because
    # then a hit-test, a hover and a highlight are one element each with no
    # bookkeeping — clicking the smallest island in the Aegean is clicking
    # Greece.
    # lod0 inline, not lod1. A whole-continent view is zoom 0-3 in the map
    # brief's own ladder, and 1:110m is what that zoom can show: the detailed
    # file is 74 KB of path text to draw fjords three pixels wide. The
    # detailed levels are fetched when somebody zooms, which is what a level
    # of detail is for — shipping the finest one at every zoom is the same
    # mistake as having only one.
    doc = geo.load("europe-lod0.json")
    context, shapes, nogeo = [], [], []
    if doc:
        for ident, ent in sorted(doc["countries"].items(),
                                 key=lambda kv: kv[1]["name"]):
            d = MAPPROJ.shape(ent["rings"])
            if not d:
                continue
            if ent["atlas"]:
                # An <a> around the path, so the drill-down is a link with an
                # href before any JavaScript runs. With scripting off this map
                # is still a navigable map of Europe; with it on, the click is
                # intercepted and zooms instead.
                shapes.append(
                    f'<a class="cshape" href="{urls.country_by_slug(ent["slug"])}" '
                    f'id="cshape-{esc(ent["slug"])}" data-slug="{esc(ent["slug"])}" '
                    f'data-name="{esc(ent["name"])}" '
                    f'data-bbox="{",".join(str(v) for v in ent["bbox"])}">'
                    f'<path d="{d}"></path>'
                    f'<title>{esc(ent["name"])}</title></a>'
                )
            else:
                context.append(f'<path d="{d}"></path>')
        # Monaco is 2 km² and Vatican City is 0.44 km²; a 1:50m cartographic
        # source has no polygon for either, and inventing one would be exactly
        # the fake geography this map was rebuilt to get rid of. They are
        # drawn as a marked point at their own coordinates and the legend says
        # why, which is both honest and the only thing that would fit.
        for code, ent in sorted(doc.get("nogeometry", {}).items()):
            here = next((n for n in data["cities"].values()
                         if n["country"]["slug"] == ent["slug"]), None)
            if not here:
                continue
            x, y = project(here["city"]["lat"], here["city"]["lon"])
            nogeo.append(
                f'<a class="cpoint" href="{urls.country_by_slug(ent["slug"])}" '
                f'data-slug="{esc(ent["slug"])}" data-name="{esc(ent["name"])}">'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5"></circle>'
                f'<title>{esc(ent["name"])} — too small to draw at this scale'
                f'</title></a>'
            )

    # What the country panel shows when a shape is chosen. Read out of the
    # same data/countries/*.json the pages are built from — the map keeps no
    # list of its own, so a region added to the atlas appears here without
    # anybody remembering to update the map.
    cinfo = {}
    for c in sorted(data["countries"].values(), key=lambda c: c["name"]):
        cinfo[c["slug"]] = {
            "n": c["name"], "u": urls.country(c), "t": c["tagline"],
            "adv": bool(c.get("advisory")),
            "r": [{"n": r["name"], "u": urls.region(c, r),
                   "d": [{"n": t["name"], "u": urls.city(c, r, t),
                          "id": f'{c["slug"]}/{r["slug"]}/{t["slug"]}'}
                         for t in r["cities"]]}
                  for r in c["regions"]],
        }

    # THE NAMES, NOT THE SENTENCE. This paragraph writes its own lead-in —
    # "The land comes from X, which is in the public domain and which we host
    # ourselves" — so handing it a finished sentence produced "The land comes
    # from Drawn from Natural Earth 1:50m admin 0 countries, public domain.,
    # which is in the public domain and…". Found on a phone contact sheet.
    attribution = geo.dataset_names(geo.load("europe-lod1.json") or doc)

    # The projection, as six numbers, so the browser can place geometry it
    # fetches later at exactly the pixel the build would have put it at. Sent
    # rather than reimplemented: a second copy of a projection is a second
    # copy that drifts, and the way you find out is a coastline two pixels off
    # the city on it.
    # The four angles, not a derived constant: the browser recomputes n and F
    # from them with the same three lines geo.py uses, so the projection is
    # decided in exactly one place and transported as its own definition.
    projinfo = {
        "p1": geo.LCC_P1, "p2": geo.LCC_P2,
        "lat0": geo.LCC_LAT0, "lon0": geo.LCC_LON0,
        "scale": round(MAPPROJ.scale, 9),
        "ox": round(MAPPROJ.ox, 4), "oy": round(MAPPROJ.oy, 4),
        "px0": round(MAPPROJ.px0, 12), "py1": round(MAPPROJ.py1, 12),
        "w": MAP_W, "h": MAP_H,
    }
    # Nine points across the extent, with the answer this build computed.
    # The browser recomputes them and the suite requires agreement to a
    # hundredth of a pixel — the only thing standing between one projection
    # and two that look the same until they do not.
    projprobe = [[lat, lon, round(MAPPROJ.xy(lat, lon)[0], 6),
                  round(MAPPROJ.xy(lat, lon)[1], 6)]
                 for lat in (35.0, 52.25, 71.0) for lon in (-24.0, 10.0, 44.0)]
    # ── 01 · THE INSTRUMENT ──────────────────────────────────────────
    #
    # THE MAP WAS ALREADY THE HERO AND EVERYTHING THAT MAKES IT AN
    # INSTRUMENT WAS BEHIND A CLOSED DISCLOSURE. `<details class="maptools">`
    # held the legend, how to read the drawing, the four geography layers,
    # all seventeen interest filters, the journey overlay, the distance
    # origin and the live count — so a reader met a map they could only
    # click, under a four-word lede. The owner's brief is *make the map the
    # actual instrument*, and the controls ARE the instrument.
    #
    # `.mapstage` and every id map.js binds to survive exactly as they were:
    # the stage still gains `.withpanel` only while the panel or popup is
    # open, so the drawing is full width the rest of the time, which is the
    # behaviour that rule was written for.
    mapopen = f"""
  <div class="pagehead instrument">
    <p class="kicker">The map</p>
    <h1>Europe, and everything we hold in it.</h1>
    {head_extent([(len(data['countries']), 'countries'),
                  (len(data['cities']), 'destinations'),
                  (len(placedots), 'places')])}
    <p class="lede">Every country we write about, every destination in it and every place
    inside those &mdash; one drawing, drawn from public-domain geometry we host ourselves.
    Click a country to open it; click again to go into it.</p>
  </div>
  <div class="mapstage">
  <div class="mapmain">
  <div class="mapzoom">
    <button type="button" class="zbtn" id="zoomin" aria-label="Zoom in">+</button>
    <button type="button" class="zbtn" id="zoomout" aria-label="Zoom out">&minus;</button>
    <button type="button" class="zbtn wide" id="zoomreset">Whole of Europe</button>
    <span class="small" id="zoomwhere" aria-live="polite"></span>
  </div>
  <div class="mapwrap">
  <svg viewBox="0 0 {MAP_W} {MAP_H}" id="europemap" class="europemap" data-role="instrument" role="img" aria-describedby="maplist" aria-label="Map of Europe showing every country, destination and place in the Atlas">
  <rect width="{MAP_W}" height="{MAP_H}" fill="none"/>
  <g id="context" class="context" aria-hidden="true">{''.join(context)}</g>
  <g id="countries" class="countries">{''.join(shapes)}</g>
  <g id="detail" class="countries"></g>
  {cut_fade('map', MAP_W, MAP_H, dusk_reach())}
  <g id="nogeo" class="nogeo">{''.join(nogeo)}</g>
  <g id="route"></g>
  <g id="regions" hidden display="none"></g>
  <g id="places" hidden display="none">{''.join(placedots)}</g>
  <g id="dots">{''.join(dots)}</g>
  </svg>
  </div>
  <p class="small" id="routenote"></p>
  </div>
  <aside class="mapside">
    <div id="countrypanel" class="countrypanel" hidden aria-live="polite"></div>
    <div id="mappopup" class="mappopup" hidden aria-live="polite"></div>
  </aside>
  </div>
  <div class="mapkey">
    <ul class="legend">
      <li><span class="sw land"></span> A country in the Atlas &mdash; click it to open the
        panel, click again to go to its page</li>
      <li><span class="sw ctx"></span> Land outside the Atlas, drawn so the coast has a far
        shore</li>
      <li><span class="sw dest"></span> A destination we have written</li>
      <li><span class="sw ring"></span> A country too small to draw at this scale &mdash;
        Monaco and Vatican City, and four more at the widest zoom</li>
    </ul>
    <p class="small mapread">Drag to pan, scroll or use + and &minus; to zoom. Zooming past
    1.6&times; loads a finer coastline; opening a country loads that country&rsquo;s
    own.</p>
  </div>"""

    # ── 02 · WHAT YOU CAN ASK IT ─────────────────────────────────────
    #
    # THE CONTROLS ARE OUT OF THE DISCLOSURE AND THE HEAD SAYS WHAT THEY
    # DO. /discover already settled this one family over: the instructions
    # belong beside the control they describe, and "Choose what you are
    # travelling for" 950 pixels above the chips it describes was the fault
    # that moved it. The legend moves with them, because a key is part of
    # reading the drawing rather than a footnote to it.
    mapask = f"""
  <div class="sheettext">
    <h2 class="mega">One map, several questions.</h2>
    <p class="lede">The drawing answers a different question depending on what you switch
    on. Nothing here is a filter over a search result &mdash; every layer is geometry or
    data this Atlas already holds, drawn into the same projection as the dots.</p>
  </div>
  <div class="askgrid">
    <div class="askset">
      <p class="mini">What is drawn</p>
      <fieldset id="geolayers">
        <legend class="visually-hidden">Geography</legend>
        <label><input type="checkbox" name="geo" value="borders" checked> Borders</label>
        <label><input type="checkbox" name="geo" value="regions"> Regions</label>
        <label><input type="checkbox" name="geo" value="cities" checked> Destinations</label>
        <label><input type="checkbox" name="geo" value="places"> Places ({len(placedots)})</label>
      </fieldset>
    </div>
    <div class="askset">
      <p class="mini">What each destination is for</p>
      <div class="checks" id="layers">{filters}</div>
      <p class="small" id="mapcount"></p>
    </div>
    <div class="askset">
      <p class="mini">Over the top of it</p>
      <div class="field">
        <label for="journeylayer">Draw a journey over it</label>
        <select id="journeylayer"><option value="">None</option>{joptions}</select>
      </div>
      <div class="field">
        <label for="mapfrom">Measure distances from</label>
        <select id="mapfrom"><option value="">Nowhere in particular</option>{fromoptions}</select>
      </div>
      <p class="note">A distance here is a straight line between two coordinates. This atlas
      holds no road and no rail geometry, so it is a floor on the journey and never the
      journey.</p>
    </div>
  </div>
{jsondata("europedoor-journeys", jdata)}
{jsondata("europedoor-mapinfo", info)}
{jsondata("europedoor-countries", cinfo)}
{jsondata("europedoor-projection", projinfo)}
{jsondata("europedoor-projection-probe", projprobe)}"""

    # ── 03 · EVERYTHING WE HOLD, IN WORDS ────────────────────────────
    #
    # THE MOST COMPLETE INDEX ON THIS SITE WAS BEHIND A SUMMARY LINE. Fifty
    # countries and all 319 destinations with their coordinates, grouped by
    # macro region — the map's own `aria-describedby` target, and the
    # control WCAG 2.5.8 requires for the twenty countries that draw
    # between 3.6 and 12 pixels wide. It is a band now: the alternative
    # still exists for assistive technology and a sighted reader can use it
    # too, which is what the helper's own docstring asks for.
    maptwin = f"""
  <div class="sheettext">
    <h2 class="mega">Everything on the map, in words.</h2>
    <p class="lede">{len(data['countries'])} countries and {len(data['cities'])}
    destinations, grouped by region, each with the coordinates the dot was drawn from.
    Searchable with ctrl-F, which the drawing is not.</p>
  </div>
  {maplist(data, flat=True)}"""

    # ── 04 · WHAT THIS DRAWING IS AND IS NOT ─────────────────────────
    #
    # PROMOTED FROM A `.note` AT CAPTION SIZE AT THE FOOT OF THE PAGE. This
    # is the cartographic position of the whole product and the one place on
    # the site allowed to name the projection — and it was printed smaller
    # than everything it explains, which is the fault /beyond-the-obvious
    # and /themes both had.
    mapsay = f"""
  <div class="sheettext">
    <h2 class="mega">A <em class="lit">cartographic</em> source, not a legal
    one.</h2>
    <p class="lede">The land comes from {esc(attribution)}, which is in the public domain
    and which we host ourselves: the file your browser drew this from is on our own
    servers, fetched once by a script in this repository, hashed, and committed. There is
    no map account behind it and no per-view bill, and that is a deliberate architectural
    choice rather than a stage we have not reached yet.</p>
    <p class="note">It is built to look right at a stated scale, and at the scale of a
    whole continent a border is a line a few kilometres wide. <strong>Do not read a
    disputed frontier off this map.</strong> Two countries in the Atlas &mdash; Monaco and
    Vatican City &mdash; have no shape here at all, because at 1:50 million they are
    smaller than a pixel; they are drawn as a ringed point instead of a polygon we made
    up. <a href="/method#map">How the map is built</a>.</p>
    <!-- THE DEGREE SIGN IS THE CHARACTER AND NOT `&deg;`. `c_published_projection`
         reads the shipped HTML for "35\u00b0" within the sentence that names
         the conic, and the entity is five characters that are not that one:
         rewriting this paragraph with `&deg;` failed all four angles at once
         on the one page allowed to state them. -->
    <p class="note">Projection: a Lambert conformal conic on the angles the EU publishes
    pan-European maps at &mdash; standard parallels {geo.LCC_P1:g}\u00b0N and
    {geo.LCC_P2:g}\u00b0N, origin {geo.LCC_LAT0:g}\u00b0N, central meridian
    {geo.LCC_LON0:g}\u00b0E. Conformal means shape is preserved everywhere: a country is
    the shape it is, at any latitude on this map. Regions are shown by the destinations
    that belong to them, not as boundaries &mdash; we hold which region a place is in, and
    we do not hold region geometry.</p>
  </div>"""

    # ── 05 · GO IN ───────────────────────────────────────────────────
    mapgo = f"""
  <div class="istart">
    <h2 class="mega">Go in anywhere.</h2>
    <p class="lede">Every dot and every country on this drawing is a page. Or start from
    what you are travelling for and let the instrument narrow the continent for you.</p>
    <p class="keepgo"><a class="btn" href="/discover">Open Discover Mode</a>
    <a class="storygo" href="/countries">Or open the atlas &rarr;</a></p>
  </div>"""

    PLATES = [("mapopen", "The map", mapopen, "map"),
              # NOT "layers" — `id="layers"` IS THE INTEREST FILTER CONTAINER
              # AND map.js BINDS TO IT. A plate's anchor becomes an `id` on
              # the `<section>`, so naming this one after what it holds put
              # two elements with one id on the page: invalid HTML, and the
              # browser suite died on an ambiguous locator rather than
              # reporting a failure. `c_unique_ids` now fails on it directly.
              ("mapask paper", "What you can ask it", mapask, "ask-it"),
              ("maptwin gal", "Everything we hold", maptwin, "in-words"),
              ("mapsay pine", "What this drawing is", mapsay, "integrity"),
              ("mapgo gal", "Go in anywhere", mapgo, "go")]
    body = f"""
{crumbs([("Europe", "/discover"), ("Map", None)])}
{plate_sequence(PLATES)}
{ad_slot("/map")}
"""
    return "/map/index.html", page(
        "Map", body, path="/map", area="countries",
        description="A point map of every city in the EuropeDoor Atlas, filterable by what you travel for. No third-party tiles.",
        scripts=["/assets/js/map.js"], wide=True, hero=True,
        # INTELLIGENCE — route intelligence
        world="intelligence"
    )


# ── events ────────────────────────────────────────────────────────────

def year_band(data, here=None):
    """The European year as its own shape, and the events family's signature.

    THE SUBJECT OF THIS FAMILY IS TIME, AND TIME WAS RENDERED AS TWELVE
    IDENTICAL PILLS.

    The index carried a chip per month and the month pages carried
    previous / whole year / next. Every one the same width, the same weight,
    saying nothing about the month behind it — a table of contents for a year,
    which is the one thing a year is not. Meanwhile the shape was in the data
    and printed as prose eleven screens apart: "3 fixed points across Europe"
    under January and "28" under July.

    Measured from the dataset, which is the only place either number may come
    from:

        Jan  3   Feb 13   Mar  6   Apr 15   May  4   Jun 20
        Jul 28   Aug 16   Sep 16   Oct 11   Nov  4   Dec 14

    Europe is nearly silent in January and crowded in July, and this atlas's
    whole editorial position is that the shoulder is where you should be
    going — so the band carries both: the bar is what is ON, the rule beneath
    it is how many countries are in their quieter shoulder that month. October
    has the most of those, 25, and it is the month the bar makes look thin.
    That disagreement is the argument the family exists to make.

    NO APERTURE HERE, deliberately. The door is how this atlas draws
    GEOGRAPHY, and a year is not a place; twelve little arches would be the
    signature as wallpaper. See docs/signature-moments.md, question 6.

    Drawn in SVG because a bar's height has to be in the markup — a CSS
    custom property would need a style attribute, and there is not one of
    those anywhere on this site.
    """
    ms = data["taxonomy"]["months"]
    names = data["taxonomy"]["month_names"]
    fx = {m: 0 for m in ms}
    sh = {m: 0 for m in ms}
    for c in data["countries"].values():
        for f in c["festivals"]:
            fx[f["month"]] += 1
        if c.get("advisory"):
            continue
        for m in c["season"].get("shoulder", []):
            sh[m] += 1
    # MIRRORED ABOUT ONE AXIS, because the first version drew the shoulder as
    # a 3px rule under each bar and it read as an underline rather than as a
    # second series. The whole argument of this band is that October is THIN
    # on fixtures and THICKEST on shoulder countries, and rendering it showed
    # that the disagreement — the only reason to draw two numbers at all —
    # was the part you could not see. Up is what is on; down is where it is
    # quiet; October is short above the line and longest below it.
    #
    # AND THE TYPE IS NOT IN THE PICTURE, because the picture stretches.
    # `preserveAspectRatio="none"` is right for twelve columns that should
    # fill whatever width they are given — and it scales EVERYTHING in the
    # viewBox, text included. At 390px the horizontal scale is 0.39 and the
    # vertical 0.79, so the month names rendered at 49% of their own width:
    # squashed type, on a phone, on thirteen pages. Setting font-size in CSS
    # does not save it; the transform is applied after. Only rendering at
    # phone width shows it.
    #
    # So the SVG holds the geometry and nothing else, and the twelve names
    # are an HTML list beside it. That also fixes the interaction: a 2px bar
    # was never a reliable target, and the list is a proper set of links.
    W, H = 1000.0, 104.0
    COL = W / 12.0
    BASE, TALL, DEEP = 66.0, 58.0, 34.0
    fmax = max(fx.values()) or 1
    smax = max(sh.values()) or 1
    bars = []
    for i, m in enumerate(ms):
        x = i * COL
        # A month with no fixtures still has a floor under its bar: a zero
        # drawn as nothing reads as a rendering fault rather than a quiet
        # month. A month with no shoulder countries draws nothing, because
        # that is a real absence and December genuinely has none.
        bh = max(2.0, fx[m] / fmax * TALL)
        sd = max(2.0, sh[m] / smax * DEEP) if sh[m] else 0.0
        on = " on" if m == here else ""
        bars.append(
            f'<rect class="ybar{on}" x="{x + 7:.1f}" y="{BASE - bh:.1f}" '
            f'width="{COL - 14:.1f}" height="{bh:.1f}"/>'
        )
        if sd:
            bars.append(
                f'<rect class="yshoulder{on}" x="{x + 7:.1f}" '
                f'y="{BASE + 1:.1f}" width="{COL - 14:.1f}" height="{sd:.1f}"/>'
            )
    keys = "".join(
        f'<li class="ykey{" on" if m == here else ""}">'
        f'<a href="/events/{esc(m)}">'
        f'<span class="ymon">{esc(names[m][:3])}</span>'
        f'<span class="ynum">{fx[m]}</span>'
        f'<span class="visually-hidden">{esc(names[m])}: {fx[m]} recurring fixture'
        f'{"s" if fx[m] != 1 else ""}, {sh[m]} countr'
        f'{"ies" if sh[m] != 1 else "y"} in their quieter shoulder</span>'
        f'</a></li>'
        for m in ms
    )
    # The one line that says what the picture means, hoisted rather than
    # repeated twelve times — same rule as Discover Mode and the motions.
    note = ('<p class="whyall"><span>Above the line</span> is what is on. '
            'Below it is how many countries are in their quieter shoulder '
            'that month. October is one of the thinnest above and the '
            'deepest below, and that disagreement is the whole argument.</p>')
    return (f'<nav class="yearband" aria-label="The European year, month by month">'
            f'<svg class="ybars" viewBox="0 0 {W:.0f} {H:.0f}" '
            f'preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            f'<line class="ybase" x1="0" y1="{BASE:.1f}" x2="{W:.0f}" '
            f'y2="{BASE:.1f}"/>{"".join(bars)}</svg>'
            f'<ol class="ykeys">{keys}</ol>{note}</nav>')


def events_page(data):
    """The European Calendar Atlas: the year as an instrument, not a listing.

    THE PAGE WAS RIGHT AND IT STOPPED AFTER THREE BANDS. `ed_opening` over
    the year band over twelve month rows, 16,849 bytes, and a closing
    `<p class="small">` that said there were eight categories and never named
    one of them. Everything in it was correct — the catalogue of 197 rows and
    the twelve identical chips were both already thrown away, and the year
    band is this family's signature — so what is added here is what the data
    holds and the page did not print.

    AND EIGHT FILTERS WERE BUILT AND DISCARDED ON EVERY BUILD. `kindfilters`
    was composed in this function from the eight kinds and their counts, and
    the body f-string never mentioned it: the variable at the old line 11830
    was dead where the identical one in `events_month_page` is the month
    page's own control. *An ignored argument is dead code that looks like a
    decision*, and it is the reason the brief's event-character band was
    missing — the eight were counted, rendered and thrown away.

    THE YEAR HAS A MEASURED CHARACTER AND NOBODY HAD CROSS-TABBED IT. The
    owner's prototype asks for a FIXED POINTS ledger and fills it with six
    authored groupings — *Winter traditions*, *Spring awakenings*, *Harvest
    Europe*, *The winter threshold*. Those are the right instinct with no
    data behind them, and the data says it better: crossing 150 fixtures by
    month and kind, December is 9/14 markets, February 10/13 cultural, April
    9/15 religious, June 10/20 seasonal and September 8/16 food. **And July
    is the busiest month and the least characteristic of the twelve** — 28
    fixtures with no kind above 43% — where February has half as many and
    77% of them are one thing. That is a second argument to sit beside the
    shoulder one, and both are derived.

    See `docs/events-redesign.md`.
    """
    names = data["taxonomy"]["month_names"]
    ms = data["taxonomy"]["months"]
    by_month = {m: [] for m in ms}
    for c in data["countries"].values():
        for f in c["festivals"]:
            by_month[f["month"]].append((f, c))
    shoulder = {m: sum(1 for c in data["countries"].values()
                       if not c.get("advisory")
                       and m in (c.get("season") or {}).get("shoulder", []))
                for m in ms}
    total = sum(len(v) for v in by_month.values())
    images = data.get("images") or {}

    # ── 01 · THE YEAR ────────────────────────────────────────────────
    # THE HERO IS THE PHOTOGRAPH AND THE HEADLINE, WHICH IS WHAT IT WAS.
    # `events-hero` is in the register, so this family already opens on a
    # picture rather than on a slot — one of the seven that does.
    #
    # AND `ed_opening` ESCAPES ITS INTRO, so an HTML entity ships as the five
    # characters a reader sees: the first render printed `&mdash;` on the
    # page. The raw f-strings in this file take `&mdash;` because they ARE
    # markup; a helper's keyword argument takes the character. The reason for
    # that is written here rather than beside the argument, because **an
    # f-string expression cannot contain a comment** — this file records that
    # twice already and the build stopped on it a third time, on the line
    # below. AND THE ESCAPE `\u2014` FAILED FOR THE SAME FAMILY OF REASON:
    # an f-string expression may not contain a BACKSLASH either, so the
    # character is written as itself.
    evopen = f"""
  {ed_opening(
      eyebrow="The European year",
      title="What is on, and when.",
      intro=f"{total} recurring fixtures — festivals, markets, "
            f"pilgrimages, harvests and the handful of natural events worth "
            f"planning a year around. The annual, dependable ones.",
      visual=photo(images, "events-hero", w=2000, h=1200,
                   sizes="(min-width: 52rem) 58vw, 100vw")
             or ed_slot("events-hero", shape="square",
                        label="The European year"),
      family="time")}"""

    # ── 02 · THE EUROPEAN YEAR ───────────────────────────────────────
    # THE EXTENT LIVES HERE, ON THE BAND THAT INTRODUCES THE SET, WHICH IS
    # WHERE A PLATE SEQUENCE PUTS IT. /journeys, /experiences, /stories and
    # /countries each settled that once: there is no room for a stage above
    # an opening, so the head is the band that states how big the set is.
    #
    # NO DRAWING IN THE OPENING AND NO APERTURE ON THIS ONE. The year band
    # is a twelve-column chart that has to run the full width to be read at
    # all, and the door is how this atlas draws GEOGRAPHY — twelve little
    # arches would be the signature as wallpaper. `docs/signature-moments.md`
    # question 6.
    kinds = {}
    for v in by_month.values():
        for f, _ in v:
            kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    year = f"""
  <div class="pagehead index">
    <p class="kicker">The European year</p>
    <h2 class="mega">A year is another way to map Europe.</h2>
    {head_extent([(total, 'recurring fixtures'),
                  (len(ms), 'months'),
                  (len(kinds), 'kinds of fixture')])}
  </div>
  <div class="yearwrap">{year_band(data)}</div>"""

    # ── 03 · MONTH ───────────────────────────────────────────────────
    # NO SELECTION. "The three best festivals in June" would be a ranking
    # this atlas does not hold, and three rows out of twenty-eight presented
    # as a taste is a ranking wearing a smaller hat. The count is the taste.
    most = max((len(v) for v in by_month.values()), default=1) or 1
    monthrows = "".join(
        f"""<a class="row monthrow" href="/events/{esc(m)}">
        <div><h3>{esc(names[m])}</h3>
        <p class="rowsub">{len(by_month[m])} fixed point{"" if len(by_month[m]) == 1 else "s"} &middot;
        {shoulder[m]} countr{"y" if shoulder[m] == 1 else "ies"} in their quieter shoulder</p>
        <div class="hopbar"><span class="w{min(100, round(len(by_month[m]) / most * 100 / 5) * 5)}"></span></div></div>
        <p class="rowmeta">Where to go in {esc(names[m])} &rarr;</p></a>"""
        for m in ms)
    months = f"""
  <div class="sheettext">
    <h2 class="mega">Twelve doors.</h2>
    <p class="lede">Each month is a different Europe. The bar is what is on;
    the sentence beside it is how much of the continent is in its quieter
    shoulder that month, which is the number this atlas thinks you should
    travel by.</p>
  </div>
  <div class="rows monthrows">{monthrows}</div>"""

    # ── 04 · WHAT A MONTH IS MADE OF ─────────────────────────────────
    # THE BRIEF ASKS FOR A FIXED POINTS LEDGER AND FOR AN EVENT CHARACTER
    # BAND, AND THEY ARE TWO VIEWS OF ONE CROSS-TAB — so they are one band.
    # Printing the eight kinds with their counts and then the five decisive
    # months separately would be the same table twice on one page, which is
    # the fault 220 place pages had where a strip and the rows under it were
    # the same places. One band, both axes: each kind's own peak month
    # beside its count, and the months where one character actually holds.
    #
    # AND A LEDGER OF THE 150 IS THE CATALOGUE THIS PAGE ALREADY THREW
    # AWAY — 197 rows and 14,875 pixels, with no reader ever reaching
    # December. Every fixture is on its month's page, behind the filter that
    # belongs there.
    kindtab = {}
    for m in ms:
        for f, _ in by_month[m]:
            kindtab.setdefault(f["kind"], {})[m] = \
                kindtab.setdefault(f["kind"], {}).get(m, 0) + 1
    charrows = "".join(
        f'<div class="row charrow"><div>'
        f'<h3>{esc(EVENT_KIND_NAMES[k])}</h3>'
        f'<p class="rowsub">Most of them in {esc(names[peak])} '
        f'&mdash; {kindtab[k][peak]} of the {n}.</p>'
        f'<div class="hopbar"><span class="w'
        f'{min(100, round(n / max(kinds.values()) * 100 / 5) * 5)}"></span></div>'
        f'</div><p class="rowmeta">{n}<br>'
        f'<span class="small">fixture{"" if n == 1 else "s"}</span></p></div>'
        for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])
        for peak in [max(kindtab[k], key=lambda m: (kindtab[k][m], -ms.index(m)))])
    # THE DECISIVE MONTHS ARE A MEASUREMENT AND THE THRESHOLD IS STATED.
    # Half or more of a month's fixtures being one kind is the line, and it
    # is printed rather than implied — a fraction a reader cannot check is a
    # claim rather than a finding. Five months clear it and July does not,
    # which is the point of the sentence above them.
    # AND "HALF OR MORE" IS SATISFIED BY 2 OF 4. The first version reported
    # EIGHT decisive months, because March (3 of 6), May (2 of 4) and
    # November (2 of 4) clear a share threshold on a handful of fixtures —
    # arithmetically true and editorially empty, which is the small-sample
    # form of *a count that is not the set's own extent reads as one*. A
    # month also has to hold at least an average month's worth of the year
    # for a share of it to mean anything, and the average is DERIVED rather
    # than picked: 150/12 is 12.5, which admits February, April, June,
    # September and December and excludes exactly the three that were noise.
    mean = total / len(ms)
    dom = {}
    for m in ms:
        tot = len(by_month[m])
        if tot < mean:
            continue
        cnt = {}
        for f, _ in by_month[m]:
            cnt[f["kind"]] = cnt.get(f["kind"], 0) + 1
        k = max(cnt, key=lambda x: (cnt[x], x))
        if cnt[k] * 2 >= tot:
            dom[m] = (k, cnt[k], tot)
    busiest = max(ms, key=lambda m: len(by_month[m]))
    bcnt = {}
    for f, _ in by_month[busiest]:
        bcnt[f["kind"]] = bcnt.get(f["kind"], 0) + 1
    bshare = max(bcnt.values()) / len(by_month[busiest])
    character = f"""
  <div class="sheettext">
    <h2 class="mega">What a month is made of.</h2>
    <p class="lede">{numword(len(kinds), cap=True)} kinds of fixture across
    the {total}, and each one has a month it belongs to.
    {numword(len(dom), cap=True)} months are decisive &mdash; they hold at
    least an average month's share of the year and half or more of what is
    on is one kind:
    {", ".join(f"{names[m]} is {EVENT_KIND_NAMES[k].lower()} "
               f"({c} of {t})" for m, (k, c, t) in dom.items())}.</p>
    <p class="note">And the busiest month is the least characteristic.
    {esc(names[busiest])} holds {len(by_month[busiest])} fixtures, more than
    any other, and no single kind is more than
    {round(bshare * 100)}% of them &mdash; where
    {esc(names[min(dom, key=lambda m: -dom[m][1] / dom[m][2])])} has
    {len(by_month[min(dom, key=lambda m: -dom[m][1] / dom[m][2])])} and
    {round(max(c / t for _, (_, c, t) in dom.items()) * 100)}% of those are
    one thing. A crowded month is not the same as a month with a character,
    which is the whole reason this band is not a ranking.</p>
  </div>
  <div class="rows charrows">{charrows}</div>"""

    # ── 05 · THE SHOULDER ────────────────────────────────────────────
    # THE PHOTOGRAPH BELONGS TO THE ARGUMENT AND THE ARGUMENT IS ALREADY
    # WRITTEN. The brief asks for a photographic *Go when Europe breathes*
    # band, and the register holds a picture for exactly one piece of writing
    # that makes this case: `The case for going in October`. So the band is
    # that essay, with its own photograph, rather than a generic autumn
    # landscape standing in for a sentence — which is this site's oldest
    # rule about pictures and stories.
    #
    # AND THE FIGURE IS DERIVED, BECAUSE THE BRIEF'S WAS WRONG. It asks for
    # "26 countries in their quieter shoulder in October" and the dataset
    # says 25 — advisory countries are excluded, which is why. A number
    # typed into a design is the number that was true on the day it was
    # typed; this one is counted on every build.
    peakm = max(ms, key=lambda m: shoulder[m])
    oct_story = next((st for st in data["stories"]
                      if held(images, "story:" + st["slug"])
                      and peakm in st["title"].lower()), None)
    shoulderband = f"""
  <div class="sheettext">
    <p class="kicker">Beyond the headline</p>
    <h2 class="mega">Go when Europe breathes.</h2>
    <p class="lede">The calendar is not only a list of things to attend. It
    is how you find out when a place becomes quieter, slower and more
    available. {esc(names[peakm])} is the thinnest month on the bar above
    and the deepest below it: {shoulder[peakm]} of the
    {sum(1 for c in data['countries'].values() if not c.get('advisory'))}
    countries this atlas writes about are in their quieter shoulder.</p>
  </div>""" + ("" if not oct_story else f"""
  <div class="ed-feature">
    <figure class="ed-feature-media">{picture(
        images, "story:" + oct_story["slug"], w=1600, h=1200,
        sizes="(min-width: 62rem) 62vw, 100vw",
        alt=oct_story["title"])}</figure>
    <div class="ed-feature-say">
      <p class="kicker">{esc(oct_story["section"])} &middot;
      {esc(oct_story["reading"])}</p>
      <h3>{esc(oct_story["title"])}</h3>
      <p>{esc(oct_story["standfirst"])}</p>
      <p><a class="storygo" href="{urls.story(oct_story)}">Read the story
      &rarr;</a></p>
    </div>
  </div>""")

    # ── 06 · OPEN A DOOR ─────────────────────────────────────────────
    # `.sheet-door` IS TAKEN — 29 rules, the homepage's own opening — so the
    # close is `pickmonth`. *A class name already in the stylesheet is a
    # rule you inherit silently*, and grepping first is what that rule
    # actually asks for.
    pick = f"""
  <div class="pickmonth">
    <h2 class="mega">Choose a month. Open a door.</h2>
    <p class="lede">Every fixture sits on its month's page with the kind
    filter beside it, and every month names the countries that are quiet
    then. The calendar is where a journey starts, not where it ends.</p>
    <p class="keepgo"><a class="btn" href="/events/{esc(peakm)}">What is on in
    {esc(names[peakm])}</a>
    <a class="storygo" href="/plan">Or open the Planner &rarr;</a></p>
  </div>"""

    # `year` WOULD HAVE COLLIDED WITH THE HOMEPAGE'S PLATE 07, WHICH EMITS
    # `sheet-year` AND HAS NO RULE OF ITS OWN. Grepping the stylesheet —
    # which is what *grep the stylesheet before naming a composition* asks
    # for — returned zero, because a plate class can be emitted by a page
    # builder and styled by nothing. **The built site is the other half of
    # that grep**, and `checks.py` now asks it on every build.
    PLATES = [("evopen gal", "The European year", evopen, "what-is-on"),
              ("euyear paper", "The year", year, "the-year"),
              ("months gal quiet", "Twelve doors", months, "the-months"),
              ("character gal", "What a month is made of", character,
               "the-character"),
              ("shoulder paper", "The shoulder", shoulderband, "the-shoulder"),
              ("pickmonth gal", "Open a door", pick, "open-a-door")]
    body = f"""
{crumbs([("Europe", "/discover"), ("Events", None)])}
{plate_sequence(PLATES)}
"""
    return "/events/index.html", page(
        "Events", body, path="/events", area="events", hero=True,
        description="The recurring European year: festivals, markets, pilgrimages and seasonal events, month by month, filterable by category.",
    )


def events_month_page(data, month):
    """A month page answers two questions the year page cannot: what is on,
    and where is actually good right now. The second is the more useful one
    and comes free from the season data every country already carries."""
    names = data["taxonomy"]["month_names"]
    name = names[month]
    fixtures = []
    for c in data["countries"].values():
        for f in c["festivals"]:
            if f["month"] == month:
                fixtures.append((f, c))
    fixtures.sort(key=lambda p: p[1]["name"])
    rows = "".join(
        f"""<a class="row event" data-kind="{esc(f['kind'])}" href="{urls.country(c)}">
        <div><h3>{esc(f['name'])}</h3><p class="rowsub">{esc(f.get('where', ''))}</p></div>
        <p class="rowmeta">{esc(EVENT_KIND_NAMES[f['kind']])} · {esc(c['name'])}</p></a>"""
        for f, c in fixtures
    )

    # THE CATEGORY FILTER CAME WITH THE ROWS. It was on the index, acting on
    # all 197 fixtures across fifteen screens; the rows are here now, so the
    # control that acts on them is here too. Built from THIS MONTH'S kinds
    # rather than from the year's, because a checkbox that can only ever
    # empty the list is a control lying about what is behind it.
    kindcounts = {}
    for f, _c in fixtures:
        kindcounts[f["kind"]] = kindcounts.get(f["kind"], 0) + 1
    kindfilters = "".join(
        f'<label><input type="checkbox" name="eventkind" value="{esc(k)}"> '
        f'{esc(EVENT_KIND_NAMES[k])} ({n})</label>'
        for k, n in sorted(kindcounts.items(), key=lambda kv: -kv[1])
    )

    peak = sorted((c for c in data["countries"].values()
                   if month in c["season"]["peak"] and not c.get("advisory")),
                  key=lambda c: c["name"])
    shoulder = sorted((c for c in data["countries"].values()
                       if month in c["season"].get("shoulder", []) and not c.get("advisory")),
                      key=lambda c: c["name"])

    def country_rows(cs):
        return "".join(
            f"""<a class="row" href="{urls.country(c)}">
            <div><h3>{esc(c['name'])}</h3><p class="rowsub">{esc(c['tagline'])}</p></div>
            <p class="rowmeta">€{c['daily_eur'][0]}–{c['daily_eur'][1]} a day</p></a>"""
            for c in cs
        )

    # The quiet places in a shoulder-season country are the single most
    # useful recommendation this dataset can make, so the month page makes it.
    quiet = [n for n in data["cities"].values()
             if n["city"].get("quiet") and month in n["country"]["season"].get("shoulder", [])]
    quiet.sort(key=lambda n: (n["country"]["name"], n["city"]["name"]))
    # SIX HASH-DRAWN LANDSCAPES ON TWELVE MONTH PAGES, and the last card grid
    # of them on the site outside the country pages.
    #
    # This band is the single most useful recommendation this dataset makes —
    # a quiet place in a country that is in its shoulder season THIS MONTH —
    # and it was six abstract gradients above six names. A destination is
    # chosen on where it is and what it is like; neither is a look, which is
    # the test a card has to pass, and this is the same measurement that
    # emptied the homepage, /journeys, /europe-in, the stories index, the
    # seventeen interest pages, 130 region pages and twelve motion pages.
    #
    # ONE DRAWING FOR THE SIX, not six. What a reader wants from "where would
    # you send me in October" is where those places ARE — and six framed
    # thumbnails would be six pictures of the same continent, which is the
    # nine-macro-regions fault. The /themes answer: the set lit on one extent,
    # and the rows underneath it name them in the order the page already
    # sorted them.
    qshown = quiet[:6]
    qart = constellation(
        [project(n["city"]["lat"], n["city"]["lon"]) for n in qshown],
        frame=True, mark=13) if qshown else ""
    qrows = "".join(
        f'<a class="row" href="{urls.city(n["country"], n["region"], n["city"])}">'
        f'<div><h3>{esc(n["city"]["name"])}</h3>'
        f'<p class="rowsub">{esc(n["city"]["summary"])}</p></div>'
        f'<p class="rowmeta">{esc(n["country"]["name"])}<br>'
        f'<span class="small">{esc(n["region"]["name"])}</span></p></a>'
        for n in qshown)
    qband = (f'<div class="quietsend"><figure class="quietart">{qart}</figure>'
             f'<div class="rows">{qrows}</div></div>') if qshown else ""

    ms = data["taxonomy"]["months"]
    i = ms.index(month)
    prev_m, next_m = ms[(i - 1) % 12], ms[(i + 1) % 12]

    # THE MONTH, AS A PICTURE — and the honest half of it.
    #
    # A month page listed eleven fixtures in eleven countries and showed
    # nowhere. "October in Europe" is a shape: Areni, Motovun, Tokaj, Alba,
    # Tromsø. That is the family's whole subject and it was text.
    #
    # Only the fixtures carrying a validated `city` can be drawn, which is
    # 56 of 150 across the year, and the gap is not a data failure — it is
    # what a fixture IS. "Everywhere north of the Arctic Circle" and "Truffle
    # season" are not points, and pinning them to a capital to fill the map
    # would be inventing a location. So the caption counts both halves and
    # the list below carries all of them.
    #
    # Under two mapped fixtures there is no map: January has none and March
    # has one, and a map of Europe with a single dot on it is not a map of
    # Europe. Two months without the signature beats twelve with a fiction.
    mapped = []
    for f, fc in fixtures:
        n = data["cities"].get(f"{fc['slug']}/{f['city']}") if f.get("city") else None
        if not n:
            for r in fc["regions"]:
                for t in r["cities"]:
                    if f.get("city") and t["slug"] == f["city"]:
                        n = {"country": fc, "region": r, "city": t}
        if n:
            mapped.append((f, n))
    monthmap = ""
    if len(mapped) >= 2:
        pts = [(*project(n["city"]["lat"], n["city"]["lon"]),
                urls.city(n["country"], n["region"], n["city"]), n["city"]["name"])
               for _f, n in mapped]
        rest = len(fixtures) - len(mapped)
        cap = (f'{len(mapped)} of the {len(fixtures)} fixture'
               f'{"s" if len(fixtures) != 1 else ""} in {esc(name)} happen in a '
               f'destination this atlas holds, and those are the ones drawn.')
        note = ((f'The other {rest} '
                 f'{"are" if rest != 1 else "is"} in the list below: a season, '
                 f'a region or a whole country is not a point, and pinning '
                 f'one to a capital to fill the map would be inventing a '
                 f'location. ' if rest else '')
                + f'Coastline from <a href="/sources">Natural Earth</a>, public '
                  f'domain. <a href="/map">The full map →</a>')
        monthmap = pointsmap(pts, "ev" + month, cap,
                             f'Map of the {len(mapped)} fixtures in {name} that '
                             f'happen in a destination in the Atlas', note=note)

    # A MONTH IS A SHAPE AND IT WAS ALSO A PLACE, AND ONLY THE SHAPE WAS
    # DRAWN. The year band says what is on, the map says where, and between
    # them a reader still had no idea what October in Europe LOOKS like —
    # which is the one thing a month page is really being asked.
    #
    # The strip is the fixtures that could be MAPPED, which is the same set
    # the map draws and for the same recorded reason: a season, a region or
    # a whole country is not a point, and a town pinned to it to fill a
    # frame would be inventing a location. A photograph of a place that is
    # not where the fixture is would be the same invention, one medium over.
    _evshots = ed_strip(data.get("images"), [
        {"key": f"city:{n['country']['slug']}/{n['region']['slug']}/{n['city']['slug']}",
         "alt": n["city"]["name"], "label": n["city"]["name"],
         "href": urls.city(n["country"], n["region"], n["city"])}
        for _f, n in mapped], limit=8)
    if _evshots:
        _en = min(8, len(mapped))
        _evshots = ('<section class="ed-section">'
                    + ed_section_head("The month",
                        f"{numword(_en, cap=True)} places {name} happens in",
                        f"The same {n_of(len(mapped), 'fixture')} the drawing "
                        f"above plots — the rest of the list is a season or a "
                        f"region, and neither is a place to photograph.")
                    + _evshots + "</section>")
    body = f"""
{crumbs([("Europe", "/discover"), ("Events", "/events"), (name, None)])}
<div class="pagehead overture">
  <p class="kicker">The European year</p>
  <h1>{esc(name)} in Europe</h1>
  <p class="lede">{n_of(len(fixtures), "recurring fixture")},
  {n_of(len(peak), "country")} at their best and {len(shoulder)} in the quieter
  shoulder — which is usually where you should be going.</p>
</div>
{constel_defs() if qshown else ""}
{year_band(data, month)}
{monthmap}
{_evshots}
{section(f"On in {name}", f'<div class="checks" id="eventkinds">{kindfilters}</div>' + f'<p class="small" id="eventcount"></p>' + f'<div class="rows">{rows}</div>') if rows else ""}
{section(f"At their best in {name}", f'<div class="rows">{country_rows(peak)}</div>',
         lede="Peak season: the weather works, everything is open, and so is everyone else's calendar.") if peak else ""}
{section(f"Quieter, and often better, in {name}", f'<div class="rows">{country_rows(shoulder)}</div>',
         lede="Shoulder season. The Journey Planner scores these upward rather than downward for exactly this month.") if shoulder else ""}
{section("Where we would actually send you", qband,
         lede=("Quiet places in countries that are in shoulder season this month "
               "— the intersection of the two things that matter. The drawing is "
               "where those six are, on one frame. "
               + geo.sources_line(geo.load("europe-lod0.json"))),
         more=("Every quiet place", "/beyond-the-obvious")) if qshown else ""}
"""
    return f"/events/{month}/index.html", page(
        f"{name} in Europe", body, path=f"/events/{month}", area="events",
        description=f"What is on in Europe in {name}, which countries are at their best, which are in the quieter shoulder season, and where to go instead of the obvious.",
        scripts=["/assets/js/events.js"],
    )


# ── beyond the obvious ────────────────────────────────────────────────

def quiet_page(data):
    """The Counter-Atlas: seven plates, and the corner with the most quiet
    places is not the quietest corner.

    THE PAGE'S OWN POSITION WAS THE SMALLEST THING ON IT. *No page on this
    site tells you a place is undiscovered* is this product's sharpest
    editorial line and it sat in a `.note` at the very bottom, under 130
    rows and six swaps, at caption size — the /stories fault where the
    reason a family looks the way it does was printed smaller than
    everything it explains. It is a band now, and so is the refusal that
    comes before it.

    THE BRIEF GOT EVERY FIGURE RIGHT. 130 quiet destinations, 44 countries,
    and all nine macro-region counts — 19, 7, 6, 15, 15, 41, 18, 2, 7 —
    checked against the build. That is worth recording because the /events
    brief had one out by one, and it means the argument can be taken at
    face value and the work is in what the numbers do not say.

    AND WHAT THEY DO NOT SAY IS THE POINT. Nine counts alone read *go to the
    Mediterranean*, which is the opposite of what this page argues: the
    Mediterranean has 41 because it holds 94 destinations. As a SHARE of
    each corner's own set the order changes — the Baltic States is 58% quiet
    and the Mediterranean 44%, against 41% for the Atlas as a whole. That is
    /events' *the busiest month is the least characteristic*, one family
    over, and it is derived on every build. See `docs/beyond-redesign.md`.

    TWENTY-SEVEN OF THE 130 CARRY A PHOTOGRAPH AND THE PAGE DREW EIGHT.
    Nothing is acquired here. The corners band spends the nine the page
    already picks at a scale a reader can judge a place from, and says how
    many of the 130 the register actually holds, because a page arguing that
    Sifnos is a real alternative to Santorini with nothing to look at is the
    fault that took 130 hash-drawn plates off it, unanswered on the other
    side.
    """
    images = data.get("images")
    quiet = [n for n in data["cities"].values() if n["city"].get("quiet")]
    quiet.sort(key=lambda n: (n["country"]["name"], n["city"]["name"]))
    total = len(data["cities"])
    ncountry = len({n["country"]["slug"] for n in quiet})

    # ONE PASS, AND EVERY FIGURE ON THIS PAGE COMES OUT OF IT.
    by_macro = {}
    for n in quiet:
        by_macro.setdefault(_macro_of(data, n["country"]["slug"]), []).append(n)
    allmacro = {}
    for n in data["cities"].values():
        allmacro.setdefault(_macro_of(data, n["country"]["slug"]), []).append(n)

    def key(n):
        return (f'city:{n["country"]["slug"]}/{n["region"]["slug"]}'
                f'/{n["city"]["slug"]}')

    shot = [n for n in quiet if held(images, key(n))]

    # ── 01 · BEYOND THE OBVIOUS ──────────────────────────────────────
    # THE DRAWING IS THE OPENING, AND THERE IS NO PHOTOGRAPH HERE ON
    # PURPOSE. The register declares no hero for this family, and the one
    # that could be acquired for it is by definition a generic European
    # scene — which is the exact thing a page refusing the phrase "hidden
    # gems" cannot open on. What this page has and no stock library has is
    # the distribution: 130 dots spread across a continent that a reader
    # can see is nowhere near the eleven places.
    qpts = [(*project(n["city"]["lat"], n["city"]["lon"]),
             urls.city(n["country"], n["region"], n["city"]), n["city"]["name"])
            for n in quiet]
    quietmap = pointsmap(
        qpts, "quiet",
        f'Every destination carrying the quiet tag: {len(quiet)} of '
        f'{total}, in {ncountry} countries. The tag is editorial and we '
        f'will be wrong sometimes.',
        f'Map of the {len(quiet)} destinations tagged quiet',
        note=f'Names are dropped where they would overlap; every dot is a link. '
             f'Coastline from <a href="/sources">Natural Earth</a>, public '
             f'domain.'
             + offframe_line([project(n["city"]["lat"], n["city"]["lon"])
                              for n in quiet], data)) if len(qpts) >= 2 else ""
    btopen = f"""
  <div class="pagehead index">
    <p class="kicker">Responsible travel, stated plainly</p>
    <h1 class="mega">Beyond the obvious.</h1>
    {head_extent([(len(quiet), "quiet destinations"),
                  (ncountry, "countries"),
                  (len(by_macro), "corners of Europe")])}
    <p class="lede">Europe&rsquo;s problem is not too many visitors; it is too
    many visitors in the same eleven places in the same six weeks. Every part
    of this platform is built to push the other way &mdash; the Planner
    rewards shoulder months, the Atlas gives a Galician fishing town the same
    page template as Paris, and these {len(quiet)} places are where it would
    send you instead.</p>
  </div>
  {quietmap}"""

    # ── 02 · NOT HIDDEN GEMS ─────────────────────────────────────────
    # THE REFUSAL COMES BEFORE THE LIST, because a reader about to be handed
    # 130 places tagged "quiet" needs to know what the tag claims and what
    # it does not. It is a different band from THE RULE at 06: this one says
    # what we will not write, that one says what we write instead — and the
    # brief separates them for the same reason.
    hidden = f"""
  <div class="sheettext">
    <h2 class="mega">The alternative is not
    <em class="lit">hidden gems</em>.</h2>
    <p class="lede">Publishing a place as undiscovered is how it stops being
    one. So there is no secret list here and no ranking of it: there is an
    editorial tag, on {len(quiet)} of {total} destinations, meaning a place
    with the goods and without the crowd. It is a judgement, it is stated as
    one, and we will be wrong sometimes.</p>
    <p class="note">Every one of them is an ordinary page in the same Atlas,
    written to the same template as Paris. That is the whole mechanism: not a
    different product for quieter places, the same product, applied evenly.</p>
  </div>"""

    # ── 03 · ONE FROM EACH CORNER ────────────────────────────────────
    # NOT THE FIRST EIGHT OF 130. The list is sorted by country, so the
    # first eight would be Albania and Andorra — a claim about the alphabet
    # rather than about Europe. One per macro region, in the taxonomy's own
    # order, which is the same nine divisions the drawing above is an
    # argument about and the same nine the set below is grouped into.
    picks = [by_macro[m["slug"]][0] for m in data["macros"]
             if m["slug"] in by_macro]
    lead = [n for n in picks if held(images, key(n))][:3]
    rest = [n for n in picks if n not in lead]
    mosaic = ed_mosaic(images, [
        {"key": key(n), "alt": n["city"]["name"], "label": n["city"]["name"]}
        for n in lead]) if len(lead) >= 3 else ""
    strip = ed_strip(images, [
        {"key": key(n), "alt": n["city"]["name"], "label": n["city"]["name"],
         "href": urls.city(n["country"], n["region"], n["city"]),
         "note": n["country"]["name"]}
        for n in rest], limit=len(rest))
    corners = f"""
  <div class="sheettext">
    <h2 class="mega">One from each corner of the continent.</h2>
    <p class="lede">The first quiet destination in each of the
    {numword(len(picks))} macro regions &mdash; not the first
    {numword(len(picks))} of {len(quiet)}, which would be a claim about the
    alphabet. A reader choosing between Santorini and Sifnos is choosing
    partly on what the place looks like, and this is the page that asks for
    exactly that swap.</p>
  </div>
  {mosaic}
  {strip}
  <p class="small">{len(shot)} of these {len(quiet)} destinations carry a
  photograph in the register today, so most of this page is words and a map.
  That is a licensing position rather than a design one: a picture is bought
  one at a time, and the ones that exist are spent here rather than held
  back.</p>"""

    # ── 04 · 130 PLACES, NINE CORNERS ────────────────────────────────
    # THE COUNT IS THE OBVIOUS NUMBER AND IT ARGUES THE WRONG WAY. Nine
    # counts alone say "go to the Mediterranean", because the Mediterranean
    # holds 41 — and it holds 41 because it holds 94 destinations. The share
    # of each corner's OWN set is the number that answers the question this
    # page asks, and it reorders the nine. Both are printed, because the
    # count is what a reader came for and the share is what it means.
    share_all = 100.0 * len(quiet) / total if total else 0
    groups = []
    for m in data["macros"]:
        if m["slug"] not in by_macro:
            continue
        got = by_macro[m["slug"]]
        alln = len(allmacro.get(m["slug"], ()))
        pct = round(100.0 * len(got) / alln) if alln else 0
        groups.append(
            f'<div class="rowgroup"><p class="rowgrouphead">{esc(m["name"])}'
            f'<span class="rowgroupn">{len(got)}</span>'
            f'<span class="qshare">{pct}% of its own destinations</span></p>'
            + "".join(
                f'<a class="row quietrow" '
                f'href="{urls.city(n["country"], n["region"], n["city"])}">'
                f'<div><h3>{esc(n["city"]["name"])}</h3>'
                f'<p class="rowsub">{esc(n["city"]["summary"])}</p></div>'
                f'<p class="rowmeta">{esc(n["country"]["name"])} &middot; '
                f'{esc(n["region"]["name"])}</p></a>'
                for n in got)
            + "</div>")
    ranked = sorted(
        ((round(100.0 * len(by_macro[m["slug"]]) / len(allmacro[m["slug"]])),
          len(by_macro[m["slug"]]), m["name"])
         for m in data["macros"]
         if m["slug"] in by_macro and allmacro.get(m["slug"])),
        reverse=True)
    most = max(((len(by_macro[m["slug"]]), m["name"]) for m in data["macros"]
                if m["slug"] in by_macro))
    quietset = f"""
  <div class="sheettext">
    <h2 class="mega">{len(quiet)} places, {numword(len(by_macro))} corners.</h2>
    <p class="lede">Grouped geographically rather than ranked, so the
    alternative does not become another popularity list. Each corner carries
    two figures: how many quiet destinations it holds, and what share of its
    own destinations those are &mdash; and the two disagree.
    {esc(most[1])} holds the most at {most[0]}, because it holds the most
    destinations of any corner; {esc(ranked[0][2])} is the quietest at
    {ranked[0][0]}% against {share_all:.0f}% for the Atlas as a whole.</p>
  </div>
  <div class="rows">{"".join(groups)}</div>"""

    # ── 05 · SIX STRAIGHT SWAPS ──────────────────────────────────────
    # THE SIX ARE AUTHORED AND THAT IS LEGITIMATE — they are editorial
    # judgements about pressure and season, which is the work, not measured
    # claims dressed as one. Nothing here derives a swap from the dataset,
    # because a great-circle distance and a quiet flag cannot say that
    # Kvarner is what somebody wanted from Dubrovnik.
    swaps = "".join(
        f'<div class="row swaprow">'
        f'<div><p class="kicker">Instead of</p><h3>{esc(a)}</h3>'
        f'<p class="rowsub">{esc(why)}</p></div>'
        f'<div class="swapto"><p class="kicker">Try</p><h3>{esc(b)}</h3></div>'
        f'</div>'
        for a, b, why in [
            ("Paris in July", "Paris in October",
             "Same city, half the queue, and the light is better."),
            ("The Amalfi Coast in August", "Puglia's Adriatic side in June",
             "A coast that still belongs to the people who live on it."),
            ("Santorini at sunset", "Naxos or Sifnos, any evening",
             "The Cyclades without the cruise schedule."),
            ("Dubrovnik in high summer", "The Kvarner islands in May",
             "Walled towns exist all down that coast."),
            ("Reykjavík's Golden Circle", "The Westfjords",
             "Six hours further and a different country."),
            ("Barcelona in August", "Girona and the Empordà",
             "An hour by train from the thing everyone else is queueing for."),
        ])
    swapband = f"""
  <div class="sheettext">
    <h2 class="mega">Six straight swaps.</h2>
    <p class="lede">Same idea, different pressure. Two of the six are the same
    place at a different time of year, which is the cheapest swap there is and
    the one the Planner already weights for.</p>
  </div>
  <div class="rows swaps">{swaps}</div>"""

    # ── 06 · THE RULE ────────────────────────────────────────────────
    # A REFUSAL NOBODY CAN CHECK IS A SLOGAN, and this band's three promises
    # had never been checked. Two of them are kept on every one of the
    # destination pages — "When to come" and "Getting there" are section
    # headings on all of them. THE THIRD IS NOT BUILT: an experience record
    # carries a slug, a name, a kind, a band and a summary, and no operator;
    # the Stay layer publishes that we list neither hotels nor restaurants
    # and refuses a ranking outright. So the sentence has been promising
    # something this site does not do anywhere.
    #
    # It is stated as unbuilt with what it would take, rather than quietly
    # deleted — the /my-europe futures grammar and /plan's refusals, and the
    # standing rule that recording a mistake beats removing the evidence
    # of it.
    rule = f"""
  <div class="sheettext">
    <h2 class="mega">The rule we hold ourselves to.</h2>
    <p class="lede">No page on this site tells you a place is undiscovered.
    Publishing that sentence is what ends it. What we will say instead is
    three things &mdash; and two of them are on every one of the {total}
    destination pages, which is what makes them checkable rather than a
    slogan.</p>
  </div>
  <div class="rows">
    <a class="row" href="/europe/albania/tirana-and-the-south/gjirokaster">
    <div><h3>When to come</h3><p class="rowsub">The months a place is at its
    best and the ones it is quieter in, as a section on every one of the
    {total} destination pages.</p></div>
    <p class="rowmeta">Kept</p></a>
    <a class="row" href="/europe/albania/tirana-and-the-south/gjirokaster">
    <div><h3>How to arrive without a car</h3><p class="rowsub">Getting there,
    and getting near where there is no direct route &mdash; a section on every
    one of them too.</p></div>
    <p class="rowmeta">Kept</p></a>
    <div class="row"><div><h3>Who locally is worth your money</h3>
    <p class="rowsub">Named people and businesses, chosen and checked rather
    than ranked. It needs an operator field nothing here holds, and a way to
    choose that is not a ranking.</p></div>
    <p class="rowmeta">Not built</p></div>
  </div>
  <p class="note">The third is written here rather than removed. It has been
  on this page since the rule was, and an experience record carries a name, a
  kind and a summary and no operator &mdash; while <a href="/for-businesses">
  /for-businesses</a> publishes that there is nothing in this index that could
  carry a boost. Saying so is the only honest version of the sentence until
  somebody builds it.</p>"""

    # ── 07 · LEAVE THE OBVIOUS BEHIND ───────────────────────────────
    # `.istart` IS REUSED RATHER THAN DUPLICATED. It is /interests' closing
    # band — a statement, a lede and two links on a narrow measure — and a
    # second rule with an identical body is the duplicate this stylesheet
    # removed eighty-five of. Two users is not yet the three that earns a
    # neutral name; a third gets one rather than a fourth copy.
    leave = """
  <div class="istart">
    <h2 class="mega">Leave the obvious behind.</h2>
    <p class="lede">Not because the famous places are wrong &mdash; they are
    famous for reasons. Because Europe is larger than the eleven places
    everyone already knows, and the rest of it has pages too.</p>
    <p class="keepgo"><a class="btn" href="/discover">Find a quiet place</a>
    <a class="storygo" href="/plan">Or plan around the crowds &rarr;</a></p>
  </div>"""

    PLATES = [("btopen gal", "Beyond the obvious", btopen, "beyond-the-obvious"),
              ("hidden pine", "Not hidden gems", hidden, "not-hidden-gems"),
              ("corners gal", "One from each corner", corners, "corners"),
              ("quietset paper", "The set", quietset, "the-set"),
              ("swaps gal", "Six straight swaps", swapband, "swaps"),
              ("rule pine", "The rule", rule, "the-rule"),
              ("leave gal", "Leave the obvious behind", leave, "leave")]
    body = f"""
{crumbs([("Europe", "/discover"), ("Beyond the obvious", None)])}
{plate_sequence(PLATES)}
"""
    return "/beyond-the-obvious/index.html", page(
        "Beyond the obvious", body, path="/beyond-the-obvious", area=None,
        hero=True,
        description="Europe's quieter alternatives, shoulder-season travel and straight swaps for the eleven places everyone goes at once.",
    )

# ── my europe ─────────────────────────────────────────────────────────


def my_europe_page(data):
    """The private atlas: what you kept, drawn, and what the browser holds.

    THE PAGE WAS A HEAD, A DRAWING, TWO EMPTY CONTAINERS AND A FOOTNOTE.
    27,245 bytes, no photograph, no plate sequence, and the three things the
    owner's brief cares most about — the three kinds of memory, the future,
    and the privacy position — were one `.note` paragraph between them. The
    drawing and the local-first architecture were already right and are
    kept exactly as they were.

    AND THE SAVE VOCABULARY HAD DRIFTED. `my-europe.js` sorts a collection
    by `ORDER = ["Itinerary", "Place", "Journey", "Theme", "Story"]`, and
    the built site offers **six** kinds: `Experience` is savable from 197
    buttons and appears nowhere in that list, so `ORDER.indexOf` returns
    **-1** and every saved experience sorts in front of everything else. A
    kind the app does not know is a kind the app sorts first by accident.

    `Itinerary` was the opposite suspicion and it was wrong: it is offered
    on zero PAGES and `planner.js` creates one at runtime, so it is real and
    checking is what stopped a wrong repair. See `docs/my-europe-redesign.md`.

    THE BRIEF ASKS FOR A MONUMENTAL OPENING AND THE HEAD ROLE REFUSES IT.
    *An instrument's title is a label, because the page is the tool* — the
    measurement behind that is a head pushing the instrument to y=436 on
    /plan, 449 on /map and 460 on /search, half the first screen of a tool
    spent on a magazine headline. All five INTELLIGENCE pages carry
    `pagehead instrument`, including /plan and /discover as rebuilt in this
    same series. What the brief actually wants — a page that feels personal
    and considered rather than like a dashboard — is what the bands do.
    """
    # WHAT CAN BE SAVED, COUNTED FROM THE DATA THAT MAKES THE BUTTONS. Six
    # kinds, and the brief names three. Naming three would hide half of what
    # the product stores, which is the `pop_line` shape: a taxonomy that
    # omits part of its own set reads as a policy. The brief's sentence is
    # the good half and it survives — *places tell you where, journeys tell
    # you how, stories tell you why* — it just has to cover six.
    cities = data["cities"]
    nplace = len(cities) + sum(len(n["city"].get("places") or [])
                               for n in cities.values())
    nexp = sum(len(n["city"].get("experiences") or []) for n in cities.values())
    KINDS = [
        ("Place", nplace, "/countries",
         "Where. Every destination and every place inside one."),
        ("Experience", nexp, "/experiences",
         "What. The things worth crossing a country for."),
        ("Journey", len(data["journeys"]), "/journeys",
         "How. Routes already worked out, stop by stop."),
        ("Theme", len(data["themes"]), "/themes",
         "Why, across the continent. One argument, eight places."),
        ("Story", len(data["stories"]), "/stories",
         "Why, in one place. The piece that made you look."),
        ("Itinerary", None, "/plan",
         "Yours. What the Planner builds when you ask it a question."),
    ]
    kindrows = "".join(
        f'<a class="row mekind" href="{esc(u)}">'
        f'<div><h3>{esc(k)}</h3><p class="rowsub">{esc(w)}</p></div>'
        f'<p class="rowmeta">{("" if n is None else f"{n:,}")}<br>'
        f'<span class="small">{"built by the Planner" if n is None else "to choose from"}'
        f'</span></p></a>'
        for k, n, u, w in KINDS)

    # ── 01 · MY EUROPE ───────────────────────────────────────────────
    meopen = """
  <div class="pagehead instrument">
    <p class="kicker">My Europe</p>
    <h1>The list you are building.</h1>
    <p class="lede">Saved places, experiences, journeys, themes and stories.
    This lives in your browser and nowhere else &mdash; there is no account,
    no server, no email address, and nothing to leak. When accounts arrive,
    this list will be importable into one; it will never be silently
    uploaded.</p>
  </div>
  <p class="mestatus"><span class="medot" aria-hidden="true"></span>Stored on
  this device</p>"""

    # ── 02 · YOUR MAP ────────────────────────────────────────────────
    # THE DRAWING AND ITS ROOM ARE UNCHANGED, AND THE ROOM IS DARK ON
    # PURPOSE. The brief asks for no *swampy* dark map and it is right about
    # that — the cartography split answers it, because this is an INSTRUMENT
    # and instruments are graphite while pictures are paper. Its own
    # prototype keeps the map band dark for the same reason. What the split
    # forbids is the navy swamp the five raw hexes used to be, which went
    # when the instruments got their palette.
    meatlas = f"""
  <div class="sheettext">
    <h2 class="mega">Your Europe, drawn.</h2>
    <p class="lede">Saved places become a personal atlas. The map is not
    decoration: it is the geographic memory of what you chose to keep, and
    the emptiness is honest &mdash; you can see how much of Europe you have
    not chosen yet.</p>
  </div>
  {constel_defs()}
  <figure class="minemap" id="minemap">
    {constellation([], cut=True)}
    <figcaption><span class="capwhat" id="minecap">Nothing on it yet. Every
    place you save is drawn here.</span>
    <span class="capsrc">{geo.sources_line(geo.load("europe-lod0.json"))}
    Nothing about this list leaves your browser to draw it: the outline ships
    with the page and the coordinates come from the same public index every
    map here is built from.</span></figcaption>
  </figure>"""

    # ── 03 · THE LIST ────────────────────────────────────────────────
    # THE TWO RUNTIME CONTAINERS, UNTOUCHED. `#mine` is the collections and
    # `#dna` is the travel profile, both written by `my-europe.js` from
    # localStorage. A server-rendered placeholder inside either would be a
    # decorative mock entry, which is the one thing the brief asks not to
    # happen to this page.
    melist = """
  <div class="sheettext">
    <h2 class="mega">What you kept.</h2>
    <p class="lede">Grouped into collections you name yourself. Nothing here
    was suggested, ranked or promoted; it is what you pressed save on.</p>
  </div>
  <div id="mine" aria-live="polite"></div>
  <div id="dna"></div>"""

    # ── 04 · KINDS OF MEMORY ─────────────────────────────────────────
    # AND THIS IS THE EMPTY STATE, WHICH IS THE STATE THE PAGE SHIPS IN.
    # *Nothing saved* is answered by saying what there is and where it is,
    # rather than by an apology or a single "start exploring" button: a
    # reader who has saved nothing wants the door, and a reader who has
    # saved plenty still wants to know what else is savable.
    mekinds = f"""
  <div class="sheettext">
    <h2 class="mega">Six kinds of memory.</h2>
    <p class="lede">My Europe is deliberately broader than a wishlist. A
    place tells you where, an experience what, a journey how, and a theme or
    a story why. Every one of these carries a save button on its own page,
    and the count is what there is to choose from.</p>
  </div>
  <div class="rows mekinds">{kindrows}</div>"""

    # ── 05 · WHERE THIS GOES NEXT ────────────────────────────────────
    # THE THREE ARE A SET RATHER THAN A SENTENCE, and each names the one
    # thing it needs, because *a refusal nobody can check is a slogan*.
    mefuture = """
  <div class="sheettext">
    <h2 class="mega">A list that could travel with you.</h2>
    <p class="lede">The local-first version is the one that exists. Each of
    these is real work rather than a switch, and each names what it would
    take &mdash; so that the reason this page is simple stays checkable.</p>
  </div>
  <div class="rows mekinds">
    <div class="row mekind"><div><h3>Sync across devices</h3>
    <p class="rowsub">The same list on a phone and a desk.</p></div>
    <p class="rowmeta">Needs<br><span class="small">an account, a backend and
    a data controller</span></p></div>
    <div class="row mekind"><div><h3>A list you can share</h3>
    <p class="rowsub">A public address for a collection you made.</p></div>
    <p class="rowmeta">Needs<br><span class="small">a server, and a decision
    about what a shared link exposes</span></p></div>
    <div class="row mekind"><div><h3>Straight into the Planner</h3>
    <p class="rowsub">A saved list handed over as must-visit stops.</p></div>
    <p class="rowmeta">Needs<br><span class="small">no backend &mdash; this
    one is the nearest</span></p></div>
  </div>"""

    # ── 06 · PRIVACY ─────────────────────────────────────────────────
    # PRIVACY AS A BAND RATHER THAN A FOOTNOTE IS THE BRIEF'S BEST IDEA AND
    # IT IS ALSO THIS PRODUCT'S POSITION ALREADY. What the band may not do
    # is say it twice: the opening states it in one line and this states the
    # mechanism, which is the *never explain the constraint back* rule
    # applied to a promise rather than to a filter.
    privacy = """
  <div class="sheettext">
    <h2 class="mega">Private is not a footnote.</h2>
    <p class="lede">Three keys in this browser's own storage and nothing
    else: the saved list, the collections you named, and the travel profile
    the sliders set. No request carries them. No identifier is attached to
    them. Clearing your browser data deletes them, because there is nowhere
    else they exist &mdash; which is the cost of the promise and is stated
    rather than hidden.</p>
    <p class="note">The whole of this page's JavaScript is one file you can
    read, and what it may do is bounded by the same Content-Security-Policy
    every other page here ships: no third-party origin, nothing inline.</p>
  </div>"""

    # ── 07 · BUILD YOUR EUROPE ───────────────────────────────────────
    build = """
  <div class="mebuild">
    <h2 class="mega">Build your Europe.</h2>
    <p class="lede">Find something. Keep it. Come back to it. Put it next to
    another place and see what the two of them make. The continent stops
    being a catalogue and starts being a map you drew.</p>
    <p class="keepgo"><a class="btn" href="/discover">Start with a question</a>
    <a class="storygo" href="/countries">Or open the atlas &rarr;</a></p>
  </div>"""

    PLATES = [("meopen gal", "My Europe", meopen, "my-europe"),
              ("meatlas pine", "Your map", meatlas, "your-map"),
              ("melist gal", "What you kept", melist, "what-you-kept"),
              ("mekinds gal quiet", "Kinds of memory", mekinds, "kinds"),
              ("mefuture gal", "Where this goes", mefuture, "whats-next"),
              ("privacy pine", "Privacy", privacy, "privacy"),
              ("mebuild gal", "Build your Europe", build, "build")]
    body = f"""
{crumbs([("Europe", "/discover"), ("My Europe", None)])}
{plate_sequence(PLATES)}
"""
    return "/my-europe/index.html", page(
        "My Europe", body, path="/my-europe", area=None, hero=True,
        description="Your saved European places, journeys and stories — stored in your own browser, with no account and no server.",
        scripts=["/assets/js/my-europe.js"],
        # INTELLIGENCE — personalisation and saved journeys
        world="intelligence",
    )


def method_page(data):

    # Published on /method because the map is now a claim about the world and
    # a claim republished without its provenance is a claim nobody can check.
    # Built before the page body rather than inside it: the body is one big
    # f-string, and a nested triple-quoted f-string closes it early — which is
    # a syntax error two hundred lines further down, in a place that has
    # nothing to do with the mistake.
    maprows = "".join(
        f'<div class="row"><div><h2>{esc(h)}</h2><p class="rowsub">{b}</p></div>'
        f'<p class="rowmeta">{esc(m)}</p></div>'
        for h, b, m in (
            ("Where the land comes from",
             "Natural Earth, at 1:110 million and 1:50 million. Public domain: the licence says "
             "in as many words that no permission is needed and no credit is required. We credit "
             "it anyway, because a reader looking at a border is entitled to know which dataset "
             "drew it.", "public domain"),
            ("How it gets here",
             "A script fetches it and records the SHA-256 of the exact bytes; a second clips it "
             "to Europe, simplifies it to three levels of detail and writes the result into the "
             "repository. Both are re-runnable, and the build fails if what is committed is not "
             "what the pipeline produces.", "reproducible"),
            ("What it is not",
             "Natural Earth is a cartographic source, built to look right at a stated scale. It "
             "is not a legal or authoritative statement of where a border runs, and at the scale "
             "of a continent a border is a line several kilometres wide. Do not read a disputed "
             "frontier off this map.", "cartographic"),
            ("Two countries have no shape",
             "Monaco is 2&nbsp;km² and Vatican City is 0.44&nbsp;km². At 1:50 million neither has "
             "a polygon at all, so both are drawn as a ringed point. Inventing an outline would "
             "have been easy, and would have been a lie about a measurement.",
             f"2 of {len(data['countries'])}"),
            ("Regions are groupings, not boundaries",
             "We hold which region a destination belongs to. We do not hold region geometry — the "
             "dataset that has it carries conditions nobody here has accepted — so a region is "
             "drawn as its own destinations with its name at the middle of them, and never as a "
             "line.", "no geometry"),
        )
    )
    mapmethod = section(
        "How the map is drawn", f'<div class="rows">{maprows}</div>', id="map",
        lede="Open geographic data, hosted by us, with the licence written down before the data "
             "was downloaded. No map account, no key, no third-party tile server.")

    from .score import methodology_rows, observed_spread
    from .score import REFUSED, DISCOVER_TERMS, discoverability

    # "0–97" BESIDE ALL EIGHT DIMENSIONS WAS A CONSTANT WEARING THE CLOTHES
    # OF A MEASUREMENT — the /themes failure, where every card said "8
    # PLACES" because every theme holds eight. And it was not even the right
    # constant. Nothing scores 0: every dimension starts at a base of 34.
    # Food tops out at 96 and Authenticity at 82, so a reader comparing the
    # two was told they had the same range when one spans 46 points and the
    # other 60.
    #
    # What separates the eight is their SPREAD, and the spread is the whole
    # reason a reader is on this page: Value's median is 85 and Culture's is
    # 52, which says more about what this Atlas is for than either formula
    # does. Drawn on ONE 0–100 axis for all eight, so the bars are comparable
    # — a per-row axis would make every dimension look equally wide, which is
    # the constant again in a different medium.
    spread = observed_spread(data["cities"])

    def distbar(key):
        lo, hi, med = spread[key]
        # THE ENDS OF THE SCALE ARE DRAWN, because the axis alone cannot say
        # where it starts. A hairline running the width of a cell is read as
        # a rule under the bar rather than as an extent, so "34–97 out of a
        # hundred" arrived only in the caption and the drawing said "wide".
        # Two end caps turn the same hairline into a measured span, which is
        # the difference between a chart and a decoration, and they cost
        # nothing: the axis is already the full 0–100.
        return (f'<span class="rowdist">'
                # NOT `role="img"`. A graphic is named or it is hidden, and
                # this one claimed both: `role="img"` announces a meaningful
                # image to assistive technology and `aria-hidden` removes it,
                # so it was an image with no name — eight of them, on the one
                # page whose subject is how a number is arrived at. In
                # practice aria-hidden wins and the markup was a contradiction
                # rather than a barrier, which is why nothing had ever gone
                # red: the accessibility scan's page list was twenty typed
                # URLs and /method was not among them.
                #
                # Hidden is the right answer rather than a label, because
                # `.distnum` beside it prints the same drawing in words —
                # "34-97, median 63" — so a name here would be the sentence a
                # reader already has, said twice.
                f'<svg class="dist" viewBox="0 0 100 14" aria-hidden="true" '
                f'preserveAspectRatio="none">'
                f'<rect class="distaxis" x="0" y="6" width="100" height="2"/>'
                f'<rect class="distend" x="0" y="2" width="1" height="10"/>'
                f'<rect class="distend" x="99" y="2" width="1" height="10"/>'
                f'<rect class="distspan" x="{lo}" y="3" width="{hi - lo}" height="8"/>'
                f'<rect class="distmed" x="{med - 0.6:.1f}" y="1" width="1.2" height="12"/>'
                f'</svg>'
                f'<span class="distnum">{lo}–{hi}, median {med}</span></span>')

    rows = "".join(
        f'<div class="row"><div><h2>{esc(name)}</h2><p class="rowsub">{esc(formula)}</p></div>'
        f'<p class="rowmeta">{distbar(key)}</p></div>'
        for key, name, formula in methodology_rows()
    )
    refused = "".join(
        f'<div class="row"><div><h2>{esc(name)}</h2><p class="rowsub">{esc(why)}</p></div>'
        f'<p class="rowmeta">not computed</p></div>'
        for name, why in REFUSED.items()
    )
    discrows = "".join(
        f'<div class="row"><div><h2>{esc(name)}</h2><p class="rowsub">{esc(why)}</p></div>'
        f'<p class="rowmeta">+{pts}</p></div>'
        for name, pts, why in DISCOVER_TERMS
    )
    _d = [discoverability(n["country"], n["region"], n["city"],
                          journeys_through=len(data["back"].get(cid, {}).get("journeys", [])),
                          country_cities=sum(len(x["cities"]) for x in n["country"]["regions"]))[0]
          for cid, n in data["cities"].items()]
    high = sum(1 for v in _d if v >= 70)
    ncity = len(_d)
    body = f"""
{crumbs([("Europe", "/discover"), ("Method", None)])}
<div class="pagehead">
  <p class="kicker">Europe Experience Score</p>
  <h1>The whole formula, on one page.</h1>
  <p class="lede">Six numbers appear on every city and country page. Here is exactly how each
  one is produced, because a score whose method is secret is a ranking, and rankings for sale
  are how travel sites lose their readers.</p>
</div>
<div class="rows">{rows}</div>

{section(f"{numword(len(REFUSED), cap=True)} dimensions this refuses to compute", f'<div class="rows">{refused}</div>',
         lede="The specification this came from lists ten. Eight are computable from the dataset. These two are not, and an approximation would be worse than the gap.")}

{section("Discoverability", f'<div class="rows">{discrows}</div>', id="discoverability",
         lede="A second, separate score, used by Discover Mode and by Beyond the Obvious. It answers one narrow question: how far is this place from being the obvious choice?")}

<div class="note">
  <h2 class="mini">What discoverability is not</h2>
  <p><strong>It is not a crowd measurement.</strong> We hold no visitor numbers, no search
  volume and no occupancy data for anywhere in Europe — every product that sells those is
  licensed, and inventing a proxy for one and calling it evidence is the thing this project
  exists not to do.</p>
  <p>So the score measures obscurity <em>within this Atlas</em>: how far a place is from the
  obvious circuit as our own dataset describes it. That is a smaller claim than "undiscovered"
  and it is one we can actually defend. It is also <strong>not a quality score</strong> —
  a high number means fewer people will have told you about a place, not that it is better.
  {high} of {ncity} places score 70 or above.</p>
</div>

{mapmethod}

<div class="split mt7">
  <div>
    <h2>What the scores are not</h2>
    <ul class="stack">
      <li><strong>Not measurements.</strong> They are computed from our own editorial tags. If we
      tag a city wrongly, its score is wrong, and the fix is to fix the tag —
      <a href="/sources">tell us</a>.</li>
      <li><strong>Not quality.</strong> A 94 for Adventure means the place is <em>about</em>
      adventure, not that it does it better than a 71.</li>
      <li><strong>Not for sale.</strong> No business, tourism board or partner can change a score.
      There is no mechanism to; the numbers are recomputed from the dataset on every build.</li>
      <li><strong>Not capped at 100.</strong> The ceiling is 97 and the floor is 12, so nothing
      is ever perfect and nothing is ever worthless.</li>
    </ul>
    <h2 class="mt7">Why value is different</h2>
    <p>Five dimensions are structural — they come from tags. Value is the only one anchored to
    something outside our own judgement: the midpoint of the country's daily cost band, which is
    published on every country page and can be argued with directly.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Recomputed, never stored</h2>
    <p>No score is written into the data files. Every number on the site is derived at build
    time from the tags, so a score and its explanation cannot drift apart.</p>
  </aside>
</div>
"""
    return "/method/index.html", page(
        "Method", body, path="/method", area=None,
        description="The complete, published formula behind the Europe Experience Score — and the four things it deliberately is not.",
        # heritage: this page is about how we know what we claim
        accent="heritage"
    )


# ── the pages that explain the thing ──────────────────────────────────

def about_page(data):
    body = f"""
{crumbs([("Europe", "/discover"), ("About", None)])}
<div class="pagehead">
  <p class="kicker">About</p>
  <h1>We do not help people book Europe. We help them discover it.</h1>
  <p class="lede">Booking companies optimise a transaction that happens in the last ten minutes
  of a decision. Almost all of the interesting part happens before that, and almost nobody
  serves it well. That gap is the whole business.</p>
</div>
<div class="split">
  <div>
    <h2>The shape of it</h2>
    <p>One structure runs the length of the site: Europe → region of Europe → country →
    travel region → city → experience. Every page is generated from that structure, so a village
    in the Alentejo gets the same treatment as Rome, and anything we learn about how to present a
    place improves {len(data['cities'])} pages at once rather than one.</p>
    <p>Across it run the ways people actually think: <a href="/themes">themes</a> that ignore
    borders, <a href="/journeys">journeys</a> that cross them deliberately, a
    <a href="/plan">planner</a> that turns days and money into a route, and
    <a href="/stories">stories</a> that give the whole thing a reason to be read rather than queried.</p>

    <h2 class="mt7">What we are not doing</h2>
    <ul class="stack">
      <li><strong>Not an OTA.</strong> We are not going to out-inventory Booking.com and would be
      foolish to try. Discovery first; commerce arrives afterwards, on top of an audience.</li>
      <li><strong>Not a scraped directory.</strong> Every place on this site was written for this
      site. That is slow, and it is the moat.</li>
      <li><strong>Not an AI that invents Europe.</strong> Anything a model says here will be
      retrieved from this dataset, cited to the page it came from, and refused when the dataset
      is silent. See <a href="/how-it-works">how it works</a>.</li>
    </ul>

    <h2 class="mt7">On the inspiration, and the line</h2>
    <p>The idea of a continental discovery platform is not ours and is not anybody's to own —
    tourism boards, atlases and travel magazines have organised continents this way for a century.
    What is owned is expression: another platform's words, photographs, code, layout and brand.
    None of that is here. Every line of copy, every generated illustration, the taxonomy, the
    scoring method and all of the code were written for EuropeDoor. Where we were inspired by an
    existing model — a continental atlas with a community fund attached — we took the idea and
    built our own version of it, which is the part the law leaves open.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Status</h2>
    <p>Pre-launch. No entity, no payments, no accounts, no bookings, no partners. What exists is
    the Atlas, the Planner, the Journeys, the register and the editorial.</p>
    <h2 class="mini">The name</h2>
    <p>EuropeDoor, at europedoor.com. Settled — the Atlas is the name of the discovery layer
    inside it, not an alternative name for the product.</p>
    <h2 class="mini">Corrections</h2>
    <p>Everything here can be wrong. <a href="/sources">How to tell us →</a></p>
  </aside>
</div>
"""
    return "/about/index.html", page(
        "About", body, path="/about", area=None,
        description="What EuropeDoor is, what it refuses to be, and where the line sits between an idea anyone may use and expression nobody may copy.",
    )


def how_it_works_page(data):
    # THE PAGE IS ABOUT A DISTINCTION AND THE DISTINCTION WAS SET IN GREY.
    #
    # Three bands — built, designed, blocked — each a list of rows carrying
    # its state as an uppercase label in the same weight and the same ink as
    # the other two. So the only thing separating "Search: BUILT" from
    # "Accounts: DESIGNED, NOT BUILT" from "Taking a payment: BLOCKED" was
    # which heading you had scrolled past, on the one page whose entire
    # argument is that most pre-launch products blur exactly these three.
    #
    # State goes in the FORM, not only in the word: a filled mark for a thing
    # that exists, a hollow ring for a thing that is drawn and not made, and a
    # barred mark for a thing held shut. Form rather than hue alone, because a
    # reader who cannot separate two hues still separates a disc from a ring —
    # and because this stylesheet has no state palette and inventing one for
    # sixteen rows would be three tokens nothing else uses.
    STATEKIND = {"built": "on", "designed, seeded": "part", "register only": "part"}

    def table(rows):
        return '<div class="rows">' + "".join(
            f'<div class="row"><div><h3>{esc(a)}</h3><p class="rowsub">{esc(b)}</p></div>'
            f'<p class="rowmeta"><span class="statemark '
            f'sm-{STATEKIND.get(c, "off" if "blocked" in c else "draft")}"></span>'
            f'{esc(c)}</p></div>' for a, b, c in rows
        ) + "</div>"

    built = table([
        ("The Atlas", f"{len(data['countries'])} countries, {sum(len(c['regions']) for c in data['countries'].values())} regions, {len(data['cities'])} cities, all generated from one dataset", "built"),
        ("Journey Planner", "Runs in the browser against the whole Atlas; scores fit, respects distance, estimates cost", "built"),
        ("European Journeys", f"{len(data['journeys'])} curated cross-border routes with validated night counts", "built"),
        ("Themes", f"{len(data['themes'])} experience-first routes that ignore borders", "built"),
        ("Map", "Point map of every city, filterable, no third-party tiles", "built"),
        ("Experience listings",
         f"{numword(len(data['taxonomy']['experience_kinds']), cap=True)} kinds, tiered, "
         f"with the verification model published", "built"),
        ("Europe Experience Score", "Six dimensions, formula published on /method", "built"),
        ("Stories", "Editorial desk with pieces linked into the Atlas", "built"),
        ("My Europe", "Saved places, in your browser only", "built"),
        ("Events", "The recurring European year, by month", "built"),
        ("Search", "The whole index, filtered in your browser; nothing you type is sent anywhere", "built"),
    ])
    designed = table([
        ("AI planner", "Retrieval over this dataset only, with citations and a refusal when the data is silent — never free-form generation about Europe", "designed, not built"),
        ("Accounts", "Sync, shareable lists, planner integration. Needs a controller and a privacy notice first", "designed, not built"),
        ("Business directory", "Free / Professional / Premium tiers, claimable profiles, editorial wall stated", "designed, seeded"),
        ("Bookings & commission", "Operator sets price and keeps the customer; 10–15% intended", "designed, not built"),
        ("Europe Fund", "Public register of projects; no custody of money, and no balance shown until three gates clear", "register only"),
        ("Multilingual", "Ten languages, localisation rather than machine translation of destination copy", "designed, not built"),
    ])
    # The four doors moved here from the homepage when that page was cut to
    # three bands. They are a Brand Bible element, not a marketing section —
    # the reader's path through the product, as a sequence rather than a menu
    # of equals — and cutting the homepage band deleted the only place the
    # sequence was written down anywhere on the site. The homepage is the
    # door; this is the page that explains what is behind it.
    DOORS = [
        ("Door one", "Discover", "/discover",
         f"Find places. {numword(len(data['countries']), cap=True)} countries, their travel regions and their cities — including the "
         "ones nobody puts on a list."),
        ("Door two", "Understand", "/stories",
         "Learn the story behind them. Why a valley speaks a different language from the next "
         "one, and why the market starts before sunrise."),
        ("Door three", "Experience", "/experiences",
         "Find the things to do, the people to meet and the cultures to encounter — sorted by "
         "what you actually travel for."),
        ("Door four", "Journey", "/plan",
         "Turn discovery into a route: your days, your budget, your interests, costed and "
         "ordered, with the distances between stops made honest."),
    ]
    pillars = "".join(
        f"""<a class="card door" href="{esc(u)}"><div class="card-body">
        <p class="kicker">{esc(k)}</p><h3>{esc(t)}</h3><p class="blurb">{esc(b)}</p>
        <p class="waygo" aria-hidden="true">→</p></div></a>"""
        for k, t, u, b in DOORS
    )

    gated = table([
        ("Taking a payment", "Requires an incorporated entity, a named payee on every card surface, and a PSP contract", "blocked"),
        ("Holding contributions", "Requires the above plus a written position on the treatment of contributions in each collecting country", "blocked"),
        ("Storing business or user data", "Requires a data controller, a lawful basis and a published privacy notice", "blocked"),
        ("Naming an operating company anywhere on the site", "There is not one yet, so no page names one", "blocked"),
    ])
    body = f"""
{crumbs([("Europe", "/discover"), ("How it works", None)])}
<div class="pagehead">
  <p class="kicker">How it works</p>
  <h1>What is built, what is designed, and what is deliberately blocked.</h1>
  <p class="lede">Most pre-launch products blur these three. Keeping them apart in public is
  cheap insurance: nobody can accuse us of implying a booking engine or a fund that does not exist,
  and anybody evaluating this can see the actual state in one screen.</p>
</div>

{section(f"{numword(len(DOORS), cap=True)} doors", '<div class="grid cols-4 doors">' + pillars + "</div>",
         lede="Discover, then understand, then experience, then journey. Each one is only "
              "worth anything once the one before it has happened — which is why this is a "
              "sequence and not a menu, and why it is not search-then-book.")}

{section("Built and live", built)}
{section("Designed, not built", designed, lede="Specified in docs/product-specification.md in the repository, with schemas and flows. Not shipped.")}
{section("Deliberately blocked", gated, lede="Each of these is one decision away from possible and is being held shut on purpose until the thing in the middle column exists.")}
<div class="note">
  <h2 class="mini">The AI rule, in one paragraph</h2>
  <p>When the AI planner ships, it will not be a chat window with a model behind it. The pipeline
  is: intent extraction from what you typed → a query against this dataset → a route computed by
  the same distance code that runs the planner today → and only then a model, whose job is to
  write the itinerary it was handed. If the dataset has nothing for a request, the answer is
  "we do not cover that yet", not an invention. A travel platform that hallucinates a train
  connection is worse than no travel platform.</p>
</div>
"""
    return "/how-it-works/index.html", page(
        "How it works", body, path="/how-it-works", area=None,
        description="EuropeDoor's honest status board: what is built, what is only designed, and what is deliberately blocked until the legal and payment work is done.",
    )


def manifesto_page(data):
    """The manifesto, and the trust architecture underneath it.

    The Brand Bible offers the manifesto as "the foundational piece of the
    website". A manifesto on its own is a poster, though, and a travel site
    that opens with a poem about markets waking before sunrise and then
    presents an unchecked fact identically to a checked one has told you what
    it wants to be rather than what it is.

    So the page is both halves. The lines first, because they are the reason
    any of this is worth building — then, immediately underneath and on the
    same page, the four labels that say where every claim on this site comes
    from. The second half is what makes the first half something other than
    advertising copy.
    """
    lines = [
        "Europe is more than a collection of countries.",
        "It is the road between them.",
        "The language that changes from one valley to the next.",
        "The market that wakes before sunrise.",
        "The old church at the end of a village road.",
        "The mountain beyond the train window.",
        "The meal that becomes a memory.",
        "The story you didn't know you were looking for.",
    ]
    verse = "".join(f"<p>{esc(l)}</p>" for l in lines)

    # The trust architecture, §19. Four sources, and what each one is worth.
    # This is published rather than kept internal because the promise is not
    # "we know everything" — it is "you can tell where this came from".
    tiers = [
        ("Verified", "verified",
         "Checked by a person against a source that is answerable for the fact — a "
         "central bank for a currency, a border authority for an entry rule, an "
         "operator for its own season. Carries the date it was checked and what it "
         "was checked against.",
         f"{sum(1 for c in data['countries'].values() if c.get('checked'))} of "
         f"{len(data['countries'])} countries. The honest number, published on "
         "the freshness board, and it expires."),
        ("Editorial", "editorial",
         "Written by someone who knows the place, reviewed as a change to this "
         "repository, and published under a name. A considered first draft — not a "
         "citation-backed reference.",
         "Everything on this site that is not marked otherwise. All 319 destination "
         "summaries, every country write-up, every story."),
        ("Computed", "computed",
         "Derived by a published formula from data we hold: distances, costs, "
         "scores, nearest onward stops, seasonal fit. Change the formula and the "
         "public page changes with it.",
         "The Europe Experience Score and every estimate the Journey Planner makes. "
         "The formula is at /method."),
        ("Community", "community",
         "Contributed by a reader or by the business itself. Attributed, and never "
         "able to affect ranking.",
         "None yet. Contribution needs accounts, moderation and attribution, and "
         "none of the three exists. Nothing on this site is marked community, "
         "because nothing is."),
    ]
    tierhtml = "".join(
        f"""<div class="tier tier-{esc(cls)}">
        <h3><span class="tierbadge">{esc(name)}</span></h3>
        <p>{esc(what)}</p>
        <p class="small"><strong>Where it stands:</strong> {esc(where)}</p></div>"""
        for name, cls, what, where in tiers
    )

    body = f"""
{crumbs([("Europe", "/discover"), ("What this is for", None)])}
<div class="pagehead">
  <p class="kicker">The manifesto</p>
  <h1>Open the door to Europe.</h1>
</div>

<div class="manifesto">{verse}
  <p class="manifesto-close">EuropeDoor opens the way. <br>Come discover what lies beyond.</p>
</div>

<div class="mt7">
  <h2>And then the part that makes it true</h2>
  <p class="lede">A travel site can write all of the above and still present a fact somebody
  checked and a fact nobody checked in exactly the same typeface. Most of them do. Our promise
  is not that we know everything — it is that you can always tell where something came from.</p>
  <p>Four sources. Every claim on this site is one of them, and the difference is visible on the
  page rather than recorded in a policy nobody reads.</p>
  <div class="tiers">{tierhtml}</div>
  <p class="small">The verification board is at <a href="/sources/freshness">/sources/freshness</a>,
  the formulae at <a href="/method">/method</a>, and what is built versus what is merely designed
  at <a href="/how-it-works">/how-it-works</a>. If any of those three disagrees with this page,
  they are right and this page is out of date.</p>
</div>

<div class="hero-actions mt7">
  <a class="btn" href="/plan">Plan my journey</a>
  <a class="btn ghost" href="/discover">Explore Europe</a>
</div>
"""
    return "/manifesto/index.html", page(
        "What this is for", body, path="/manifesto",
        description="Why EuropeDoor exists — and the four labels that say where every claim "
                    "on it comes from: verified, editorial, computed, community.",
    )


def api_page(data):
    """Documentation for the public read API.

    An undocumented endpoint is an endpoint nobody can rely on, and an
    endpoint nobody can rely on may as well not be public. This page says
    what each one holds, what it deliberately does not, what may be done with
    it, and — the part most API pages leave out — where it will change.
    """
    ncity = len(data["cities"])
    nadv = sum(1 for c in data["countries"].values() if c.get("advisory"))
    rows = [
        ("/api/atlas.json",
         "The planner index: every destination with its interests, nights, "
         "cost band, season, coordinates and URL. This is the document the "
         "Journey Planner in your browser actually runs on.",
         f"{ncity - sum(len(r['cities']) for c in data['countries'].values() if c.get('advisory') for r in c['regions'])} destinations",
         f"Countries under a travel advisory ({nadv} of them) are absent. That "
         "is a build-time exclusion, not a UI filter, so no consumer of this "
         "file can route a traveller into one by accident."),
        ("/api/search.json",
         "One flat row per findable thing — country, region, destination, "
         "place, experience, journey, story, theme, event — with a name, a "
         "kind, a URL and a lowercased text blob to match against.",
         "every findable thing",
         "Advisory countries ARE present here. A page nobody can search for "
         "is a page that does not exist, and hiding a country from search "
         "does not make anyone safer."),
        ("/api/countries.json",
         "Country-level facts: capital, currency, time zone, languages, "
         "membership, daily cost band, seasons, and the full region and "
         "destination tree beneath each one.",
         f"{len(data['countries'])} countries",
         "Advisory countries are present, with the advisory attached. Every "
         "country carries its verification record, so a consumer can tell a "
         "checked fact from an unchecked one."),
        ("/api/journeys.json",
         "The curated routes, with every leg resolved to a real destination: "
         "coordinates, nights, the note for that stop, and the countries the "
         "route crosses.",
         f"{len(data['journeys'])} journeys",
         "Estimated costs are planning arithmetic from published daily bands "
         "and straight-line distances. They are not quotes and there is "
         "nothing to book."),
    ]
    cards = "".join(
        f"""<div class="row db">
        <h2><code>{esc(u)}</code></h2>
        <p class="rowsub">{esc(what)}</p>
        <p class="small"><strong>Holds:</strong> {esc(size)}</p>
        <p class="small"><strong>Note:</strong> {esc(note)}</p>
        <p class="small"><a href="{esc(u)}">Open it →</a></p></div>"""
        for u, what, size, note in rows
    )
    body = f"""
{crumbs([("Europe", "/discover"), ("Sources & corrections", "/sources"), ("The public API", None)])}
<div class="pagehead">
  <p class="kicker">The public API</p>
  <h1>{numword(len(rows), cap=True)} read-only endpoints. No key, no quota, no sign-up.</h1>
  <p class="lede">Everything the site knows is published as static JSON on the same domain,
  cacheable and versionless. They are the same documents this site's own planner, search and
  map run on — not a reduced copy of them, which is the only way an API stays true.</p>
</div>

<div class="rows">{cards}</div>

<div class="split mt7">
  <div>
    <h2>What you may do with them</h2>
    <p>Read them, cache them, and build on them, with attribution to EuropeDoor. That
    permission is written into each document as a <code>licence</code> field rather than left
    on this page, because a JSON file gets copied and the page it was linked from does not
    travel with it.</p>

    <h2 class="mt7">And one document that is not JSON</h2>
    <p>The editorial desk publishes an <a href="/stories/feed.xml">Atom feed</a> at
    <code>/stories/feed.xml</code> — every story, newest first, with its desk, its two
    dates and its standfirst. It is not counted above because it is not an endpoint:
    there is nothing to query, it is a document a reader subscribes to, and the four
    above are the ones this site's own planner, search and map run on.</p>

    <h2 class="mt7">What they are not</h2>
    <ul class="stack">
      <li><strong>Not advice.</strong> Nothing here is entry, visa, border or safety
      information. Those are refused across the whole product and
      <a href="/sources">the reason is on the sources page</a>.</li>
      <li><strong>Not quotes.</strong> Every cost is a band or a computed estimate. There is
      nothing to book on this site and no price came from a supplier.</li>
      <li><strong>Not verified, mostly.</strong> Each country carries a verification record
      saying when a person last checked it and against what. For most of them the answer is
      still "never", and <a href="/sources/freshness">that board is public</a>.</li>
      <li><strong>Not stable yet.</strong> There is no version number in these URLs on
      purpose: pretending to a stability guarantee before anyone depends on it is worse than
      saying plainly that the shape may still move.</li>
    </ul>
  </div>
  <aside class="rail">
    <h2 class="mini">Why these four and not more</h2>
    <p>These are read-only projections of data already committed to this repository, so they
    cost nothing to serve and cannot fall out of step with the site.</p>
    <p>The specification also lists endpoints that write — saving to an account, claiming a
    business listing, registering interest in the Fund. Every one of those needs somebody to
    be logged in, which needs an account, which needs a data controller, which needs a
    company. <a href="/how-it-works">None of that exists yet</a>, so none of it is published as a
    stub that returns nothing.</p>
    <h2 class="mini mt7">Attribution</h2>
    <p class="small">EuropeDoor — europedoor.com. A link back is enough.</p>
  </aside>
</div>
"""
    return "/api-docs/index.html", page(
        "The public API", body, path="/api-docs",
        description="Four public, read-only, key-free JSON endpoints: the Atlas index, "
                    "the search index, country facts and the curated journeys.",
        trail=None)


def sources_page(data):
    # THE PAGE A THOUSAND CREDITS POINT AT NEVER NAMED A SINGLE DATASET.
    #
    # Every map on this site ends "Coastline from Natural Earth, public
    # domain" with Natural Earth linked to /sources, and /sources was about
    # editorial facts: it did not contain the words "Natural Earth" anywhere.
    # A credit whose link goes to a page that does not carry the credit is
    # worse than an uncredited map, because it looks like a register. Found
    # while adding the relief credit, which would have been the second dead
    # link to the same page.
    #
    # It is BUILT FROM THE GEOMETRY FILES, not typed. Each data/geo/ document
    # carries the rows that produced it — dataset, licence, version, the
    # SHA-256 of the exact bytes and the date they were fetched — written
    # there by scripts/map/fetch.py from docs/data-licenses/sources.json. So
    # this table cannot drift from what actually drew the maps, and a dataset
    # added without a licence row cannot appear here at all, because fetch.py
    # will not open a socket for one.
    georows = []
    geodoc = geo.load("europe-lod1.json") or {}
    for src in geodoc.get("sources", []):
        georows.append((
            src["dataset"],
            f'{esc(src.get("version", ""))} · fetched {esc(src.get("fetched", "—"))} · '
            f'SHA-256 <span class="mono">{esc(src.get("sha256", "")[:12])}…</span>',
            src.get("licence", "").replace("-", " ")))
    tdoc = geo.load("terrain-lod1.json") or {}
    if tdoc.get("$source"):
        pl = tdoc.get("pipeline", {})
        georows.append((
            tdoc["$source"].split(";")[0].strip(),
            f'Decoded into four hypsometric band boundaries at '
            f'{", ".join(f"{b:,}" for b in pl.get("bands_m", []))} m, '
            f'about {tdoc.get("smoothed_m", 0):,} m across after smoothing. '
            f'No pixel of the source reaches a page: this atlas has no '
            f'<span class="mono">&lt;img&gt;</span> on any map.',
            "public domain"))
    georows = "".join(
        f'<div class="row"><div><h3>{esc(name)}</h3>'
        f'<p class="rowsub">{sub}</p></div>'
        f'<p class="rowmeta">{esc(lic)}</p></div>'
        for name, sub, lic in georows)
    geodata = section(
        "Where the geography comes from",
        f'<div class="rows">{georows}</div>'
        '<p class="small">Every one of these is public domain and none of '
        'them requires a credit. We print one on every map anyway: a reader '
        'looking at a border, or at a mountain range, is entitled to know '
        'which survey measured it, and an uncredited map invites the '
        'assumption that we surveyed it ourselves. The licence for each is '
        'written down in the repository before the data is downloaded — '
        'the fetcher refuses a source that has no licence file.</p>',
        id="geography",
        lede="Open data, hosted by us, fetched by a script that records the "
             "SHA-256 of the exact bytes. No map account, no key, no "
             "third-party tile server, and nothing traced by hand.")

    # ── THE PHOTOGRAPHS, AS A CATALOGUE RATHER THAN AS A BADGE ──────
    #
    # SOURCE PROVENANCE IS INVISIBLE INFRASTRUCTURE UNLESS A SPECIFIC
    # REQUIREMENT PUTS IT ON A PARTICULAR SURFACE, and this is the surface.
    # The rule the owner set is that a supplier's name is not part of this
    # product's visual identity: a photograph's upstream marketplace does
    # not belong on the composition it appears in, and the page every
    # credit on this site already points at is where the question is
    # answered once, in full, for every photograph in the library.
    #
    # BUILT FROM THE REGISTER, exactly as the geography table is built from
    # the rows inside each data/geo/ document — so it cannot drift from
    # what is actually published, and a photograph acquired tomorrow
    # appears here on the next build without anybody editing a page. Each
    # photographer is named once and links to the work; the provider links
    # to the licence the work was taken under.
    photos = data.get("images") or {}
    by_prov = {}
    for key, row in sorted(photos.items()):
        who = (row.get("photographer") or "").strip()
        src = row.get("source") or ""
        lic = (row.get("licence") or "").strip()
        if not who or not src or not lic:
            continue
        by_prov.setdefault((lic, row.get("licence_url") or ""), {})
        by_prov[(lic, row.get("licence_url") or "")].setdefault(who, src)
    provrows = []
    for (lic, licurl), people in sorted(by_prov.items()):
        names = ", ".join(
            f'<a href="{esc(src)}" rel="noopener" target="_blank">{esc(who)}</a>'
            for who, src in sorted(people.items()))
        provrows.append(
            f'<div class="row"><div><h3>{esc(lic)}</h3>'
            f'<p class="rowsub">{names}</p></div>'
            f'<p class="rowmeta">{n_of(len(people), "photographer")}</p>'
            f'</div>')
    npho = sum(len(p) for p in by_prov.values())
    photosec = section(
        "Who took the photographs",
        f'<div class="rows">{"".join(provrows)}</div>'
        f'<p class="small">Every photograph on this site is stored here, on '
        f'this origin, under a filename that is the SHA-256 of the bytes as '
        f'they were served: nothing is hotlinked, and loading a page on '
        f'EuropeDoor reaches no other server. The register behind this table '
        f'records, for each one, the photographer, their profile, the page it '
        f'came from, the licence and its URL, that hash and the date it was '
        f'taken — and the build refuses a photograph that is missing any of '
        f'them, and refuses a page that references a file the register does '
        f'not hold.</p>',
        id="photographs",
        lede=f"{n_of(npho, 'photographer')}, named once each. A photograph is "
             f"credited where it is the subject; a composition made of "
             f"forty-one of them credits them here.") if provrows else ""

    body = f"""
{crumbs([("Europe", "/discover"), ("Sources & corrections", None)])}
<div class="pagehead">
  <p class="kicker">Sources &amp; corrections</p>
  <h1>Where these facts come from, and how to tell us we are wrong.</h1>
</div>
<div class="split">
  <div>
    <h2>The honest position</h2>
    <p>The dataset behind this site was written editorially for the launch build. It is a
    considered first draft by people who know Europe, not a citation-backed reference work, and
    it has not yet been through a source-by-source verification pass. Costs, opening seasons,
    currencies, visa positions and border arrangements all move.</p>
    <p><strong>Before you travel, check the official source</strong> — your own government's
    travel advice, the destination country's border authority, and the operator's own site for
    anything you intend to turn up for.</p>

    <h2 class="mt7">What is derived rather than claimed</h2>
    <ul class="stack">
      <li><strong>Distances</strong> are computed great-circle kilometres between the coordinates
      on each city page. They are honest as straight lines and misleading as travel times — the
      note under each hop says which mode the distance implies.</li>
      <li><strong>Scores</strong> are computed from tags by a published formula: <a href="/method">/method</a>.</li>
      <li><strong>Cost estimates</strong> multiply nights by the country's daily band and add a
      distance-based transport figure. They are planning arithmetic, not quotes.</li>
      <li><strong>Nearby stops</strong> are computed, never curated, so they cannot flatter a partner.</li>
    </ul>

    <h2 class="mt7">The verification plan</h2>
    <ol class="stack">
      <li>Every country's practical facts — currency, blocs, entry, costs — checked against the
      relevant official body and dated in the data file.</li>
      <li>Every city's seasonal and opening claims checked against the operator or municipality.</li>
      <li>A visible "checked on" date on every country page; anything unchecked says so.</li>
      <li>A standing correction log, published, with what changed and when.</li>
    </ol>
  </div>
  <aside class="rail">
    <h2 class="mini">Fact freshness</h2>
    <p>Every country, and the date its practical facts were last checked.
    <a href="/sources/freshness">The board →</a></p>
    <h2 class="mini">Tell us</h2>
    <p>Corrections are wanted, including blunt ones — and there is nowhere on this site to
    send one yet. A channel needs an inbox, an inbox needs a controller and a retention
    period, and none of those exists before the entity does. If you hold the repository, its
    issue tracker is the channel and every correction is public that way. If you do not,
    there is no way to reach us, and this page is not going to paper over that.</p>
    <h2 class="mini">No photographs</h2>
    <p>Every illustration on this site is generated from the place's own name — a deterministic
    drawing, unique per place, owned outright. No stock library, no licence expiry, no
    accidental use of somebody's holiday photograph.</p>
  </aside>
</div>

{geodata}
{photosec}
"""
    return "/sources/index.html", page(
        "Sources & corrections", body, path="/sources", area=None,
        description="How EuropeDoor's facts are produced, what is computed rather than claimed, and the verification plan.",
        # heritage: this page is about how we know what we claim
        accent="heritage"
    )


def freshness_page(data):
    """The verification plan, made operational and public.

    Most travel sites present an unverified fact and a verified fact
    identically. This page is the alternative: every country, the date its
    practical facts were last checked, and — for now — a column of the word
    "never", because that is the truth."""
    # Four states, not two. "Never checked" and "checked a year ago and now
    # due again" are different problems with different fixes, and the older
    # version of this board collapsed both into "unverified" — which meant
    # that the day a check was finally made, the record would have silently
    # become permanent. A check has an expiry from the moment it is made.
    STATE_ORDER = {"never": 0, "due": 1, "current": 2}
    rows = []
    tally = {"never": 0, "due": 0, "current": 0}
    for c in sorted(data["countries"].values(),
                    key=lambda c: (STATE_ORDER[verification_of(c)["state"]], c["name"])):
        v = verification_of(c)
        tally[v["state"]] += 1
        if v["state"] == "never":
            meta, tag = "never", ' <span class="tag advisory">unverified</span>'
        elif v["state"] == "due":
            meta = f'{esc(v["on"])} · {esc(v["by"])}'
            tag = ' <span class="tag advisory">due for review</span>'
        else:
            meta = f'{esc(v["on"])} · {esc(v["by"])} · due in {v["dueIn"]} days'
            tag = f' <span class="tag">{esc(v["confidence"])} confidence</span>'
        nsrc = len(v["sources"])
        prov = f" · {nsrc} source{'s' if nsrc != 1 else ''}" if nsrc else ""
        ncity = sum(len(r["cities"]) for r in c["regions"])
        rows.append(
            f"""<a class="row" href="{urls.country(c)}">
            <div><h3>{esc(c['name'])}{tag}</h3>
            <p class="rowsub">{n_of(ncity, 'city')} · {esc(c['currency'])} · €{c['daily_eur'][0]}–{c['daily_eur'][1]} a day{prov}</p></div>
            <p class="rowmeta">{meta}</p></a>"""
        )
    n = len(data["countries"])
    checked = tally["current"] + tally["due"]
    body = f"""
{crumbs([("Europe", "/discover"), ("Sources & corrections", "/sources"), ("Fact freshness", None)])}
<div class="pagehead">
  <p class="kicker">Fact freshness</p>
  <h1>{tally["current"]} of {n} countries verified and current.</h1>
  <p class="lede">Currencies, costs, seasons, entry rules and opening arrangements all move.
  This page says, for every country, when a person last checked the practical facts against a
  source — and for most of them the answer is still "never", which is why it is written down
  rather than left to be assumed.</p>
</div>

<div class="note">
  <h2 class="mini">What "unverified" means here</h2>
  <p>The entry was written editorially by someone who knows the place. It is a considered
  first draft, not a citation-backed reference, and no one has yet gone back through it
  against an official source. Treat cost bands as indicative, seasons as typical rather than
  guaranteed, and anything involving a border, a visa or your safety as needing the
  government source instead of us.</p>
</div>

<dl class="facts">
  <div class="fact"><dt>Never checked</dt><dd>{tally["never"]}</dd></div>
  <div class="fact"><dt>Checked and current</dt><dd>{tally["current"]}</dd></div>
  <div class="fact"><dt>Checked but now due again</dt><dd>{tally["due"]}</dd></div>
  <div class="fact"><dt>Review interval</dt><dd>{REVIEW_DAYS} days</dd></div>
</dl>

<div class="split">
  <div><div class="rows">{''.join(rows)}</div></div>
  <aside class="rail">
    <h2 class="mini">The order it happens in</h2>
    <ol>
      <li>Currency, blocs, entry arrangements — against the relevant official body.</li>
      <li>Cost bands — against current published prices in three cities per country.</li>
      <li>Seasons and opening — against operators and municipalities.</li>
      <li>The date lands on the country page, in public, next to the facts it covers.</li>
    </ol>
    <h2 class="mini">Why the date and not a tick</h2>
    <p>A tick says "correct". A date says "correct on this day, and you can judge how much
    that is worth now". Only the second one is true.</p>

    <h2 class="mini mt7">And why the date expires</h2>
    <p>A check is good for {REVIEW_DAYS} days and then this board says <em>due for review</em>
    again, whoever made it and however carefully. Without that, the first country anybody
    checks would carry a verified badge for ever — which is how a date quietly turns back
    into a tick.</p>

    <h2 class="mini mt7">Confidence is derived, not typed</h2>
    <p>High confidence needs an official source <em>and</em> a check inside the interval.
    Anything else is medium, and no sources at all is low. Nobody can write
    <code>confidence: high</code> into a data file, because a field a person can type is a
    field a person will type that into.</p>
    <p><a href="/sources">Sources and corrections →</a> · <a href="/api-docs">the same record in the API →</a></p>
  </aside>
</div>
"""
    return "/sources/freshness/index.html", page(
        "Fact freshness", body, path="/sources/freshness", area=None,
        description=f"When every country's practical facts were last checked against a source — {checked} of {n} verified so far, and the rest said so plainly.",
        # heritage: this page is about how we know what we claim
        accent="heritage"
    )


def not_found(data):
    """THE COPY PROMISED A CONTINENT AND THE PAGE SHOWED TWO BUTTONS.

    "The page is not here. The continent still is." — under which sat a
    primary button, a ghost button and 250 pixels of nothing, on the one page
    a reader arrives at having already failed to find something. A sentence
    that names a picture and then does not draw it is the /map failure in
    miniature: the prose was making a claim the page declined to keep.

    So the continent is here, with every destination this Atlas holds lit on
    it. Not links: 319 points at this size are 3-pixel targets and a dot the
    page cannot name is not navigation — the ways out are the three actions
    under the type, which is where a reader who has hit a 404 is looking.
    """
    pts = [project(n["city"]["lat"], n["city"]["lon"])
           for n in data["cities"].values()]
    body = f"""
{constel_defs()}
{indexhero(
    kicker="404",
    title="That door does not open.",
    lede=(f"The page is not here. The continent still is — all "
          f"{len(data['cities'])} destinations in the Atlas, on one drawing."),
    art=constellation(pts, cut=True),
    actions='<a class="btn" href="/countries">Open the Atlas</a>'
            '<a class="btn ghost" href="/search">Search everything</a>'
            '<a class="btn ghost" href="/plan">Plan a journey</a>',
    note=geo.sources_line(geo.load("europe-lod0.json")) + datacut_line()
         + offframe_line(pts, data, listed=False))}
"""
    return "/404.html", page(
        "Not found", body, path="/404", area=None,
        description="That page is not on EuropeDoor. The Atlas, the curated journeys and the Journey Planner all still are.",
    )


def stories_feed(data):
    """The nine essays as an Atom document, at /stories/feed.xml.

    THE ONE THING AN EDITORIAL DESK OWES ITS READERS THAT THIS ONE DID NOT
    HAVE. Every publication with a masthead publishes a feed; this site has
    nine dated, authored essays, a public JSON API with four endpoints, a
    sitemap, and no way at all to be told when a tenth arrives. A reader who
    wants to follow the desk has to come back and look.

    ATOM RATHER THAN RSS, for the same reason the JSON-LD is written the way
    it is: Atom specifies what a date means, requires a permanent id per
    entry, and says what `type` a piece of text is. RSS 2.0 leaves all three
    to convention, and a convention is what every consumer gets to interpret
    differently.

    IT CLAIMS ONLY WHAT THE REGISTER HOLDS, which is the rule `checks.py`
    already enforces on the structured data: a feed is a machine-readable
    claim republished by people who cannot check it. So the id is the
    canonical URL, `published` and `updated` are the story's own two dates
    rather than the build's, the category is the desk it was filed to, and
    the summary is the standfirst as written. There is no `<content>`: the
    body is nine paragraphs of set editorial and putting a second copy of it
    in a second format is a second thing to go stale.

    THE DATES ARE DATES AND ATOM WANTS TIMESTAMPS. A story carries a day and
    no time, and inventing one — 09:00, or the build's own clock — would be
    authoring a measurement. Midnight UTC is the only reading of a bare date
    that adds nothing, and it is what the day means.
    """
    items = sorted(data["stories"], key=lambda s: (s["updated"], s["slug"]))
    newest = items[-1]["updated"] if items else "1970-01-01"

    def stamp(day):
        return f"{day}T00:00:00Z"

    entries = "".join(
        "<entry>"
        f"<title>{esc(s['title'])}</title>"
        f'<link rel="alternate" type="text/html" href="{ORIGIN}{urls.story(s)}"/>'
        f"<id>{ORIGIN}{urls.story(s)}</id>"
        f"<published>{stamp(s['published'])}</published>"
        f"<updated>{stamp(s['updated'])}</updated>"
        f'<category term="{esc(s["section"])}"/>'
        f"<author><name>{esc(s['author'])}</name></author>"
        f'<summary type="text">{esc(s["standfirst"])}</summary>'
        "</entry>"
        for s in reversed(items)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        "<title>EuropeDoor stories</title>"
        f'<subtitle type="text">A continent is people before it is places. '
        f"{numword(len(items), cap=True)} essays, filed to "
        f'{numword(len({s["section"] for s in items}))} desks.</subtitle>'
        f"<id>{ORIGIN}/stories</id>"
        f"<updated>{stamp(newest)}</updated>"
        f'<link rel="self" type="application/atom+xml" href="{ORIGIN}/stories/feed.xml"/>'
        f'<link rel="alternate" type="text/html" href="{ORIGIN}/stories"/>'
        "<rights>Editorial text is EuropeDoor's own. Reproduce with "
        "attribution and a link.</rights>"
        + entries + "</feed>\n"
    )


def sitemap(paths):
    urlset = "".join(
        f"<url><loc>{ORIGIN}{p}</loc></url>" for p in sorted(paths)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + urlset + "</urlset>\n"
    )

# ── search ────────────────────────────────────────────────────────────

# EVERY RELATIONSHIP THE GRAPH CAN EMIT, DECLARED — INCLUDING THE ONES AT
# ZERO. `gathers` shipped at zero for one build because the derivation read
# `theme["places"]` where a theme's destinations are `stops`, and the repair
# was a count per relationship in the document and a floor on each in
# `checks.py`. That floor was a hand-typed list of the NINE relationships
# that happened to be non-zero on the day it was written, and `stops_at` was
# not one of them: a journey leg's `places` field has never existed on any of
# the 121 legs in this dataset, so `journey stops_at place` has been derived,
# counted and dropped for the life of the graph, and the counts block could
# not show it because it was built from the edges that were EMITTED.
#
# A FLOOR OVER THE KEYS THAT ARE PRESENT IS BLIND TO EXACTLY THE CASE IT
# EXISTS FOR — a relationship that was already zero. So the vocabulary is
# declared here, `graph_api` seeds its counts from this table so a zero is
# published rather than absent, and `checks.py` reads this table rather than
# naming nine relationships a second time. Each row carries either a `floor`,
# which fails when the count falls under it, or an `awaiting` sentence naming
# the authored field that would create it — the trigger-rather-than-refusal
# shape the image roles already use, because a relationship nothing reaches
# is dead vocabulary only when nothing would ever create one.
#
# `stops_at` is NOT derived from the places of a leg's destination, which is
# the available shortcut: a journey passing through Vienna does not stop at
# the Kunsthistorisches, and asserting that it does would author an editorial
# claim out of a containment fact. That is the Data Integrity Rule, and it is
# why this relationship waits on somebody writing the field.
GRAPH_RELATIONSHIPS = {
    "part_of":      {"says": "the nesting: a country in a corner of Europe, a region in a country, a destination in a region", "floor": 400},
    "located_in":   {"says": "a place or an experience inside its destination", "floor": 400},
    "near":         {"says": "the six nearest destinations, by the planner's own haversine", "floor": 1500},
    "includes":     {"says": "a journey's legs, in order, with the nights", "floor": 100},
    "serves":       {"says": "a transport node and the destination it serves", "floor": 200},
    "gathers":      {"says": "a theme and the destinations it argues for", "floor": 50},
    "about":        {"says": "a story and the destinations it is written about", "floor": 20},
    "happens_in":   {"says": "a recurring fixture, the country it is held on and the destination it names where it names one", "floor": 140},
    "available_at": {"says": "an experience and the place you stand on, start from or look at it from", "floor": 10},
    "stops_at":     {"says": "a journey and the places on one of its legs",
                     "awaiting": "a `places` list on a journey leg. None of the 121 "
                                 "legs in this dataset carries one, and it may not be "
                                 "derived from the leg destination's own places — a "
                                 "journey through a city does not stop at everything in it"},
}


def graph_api(data):
    """§2.14 — every relationship in the atlas, as one traversable index.

    The Build Package asks for a `relationships` table: source_type,
    source_id, relationship_type, target_type, target_id, weight, metadata.
    This is that document, with one difference that matters.

    **The edges are derived, not stored.** A free-standing relationships
    table cannot be validated: nothing stops a row naming an entity that does
    not exist, or naming it with the wrong type, and the failure mode is a
    page that is quietly empty rather than a build that stops. Every edge
    below is computed at build time from a relation that is already checked
    somewhere else — the nesting, a journey leg, a story's `places`, the
    §2.5 place-experience edge — so an edge cannot dangle, because there is
    nowhere for it to dangle from.

    That is the same trade as `entity_categories` in §2.12: identical
    expressiveness, and a failure mode of "the build stops".

    **`weight` is only ever a real measurement.** Distance in kilometres,
    and nothing else. A relevance weight would be a number nobody computed
    from anything, sitting in a document that looks authoritative, and this
    repository has a rule about that.
    """
    E = []

    def edge(st, si, rel, tt, ti, **meta):
        row = [st, si, rel, tt, ti]
        if meta:
            row.append(meta)
        E.append(row)

    for slug, c in sorted(data["countries"].items()):
        edge("country", slug, "part_of", "macro", c["macro_slug"])
        # A FIXTURE IS HELD ON THE COUNTRY AND THE EDGE WAS ONLY EMITTED
        # WHERE IT NAMED A DESTINATION. 56 of the 150 recurring fixtures in
        # this atlas name a city; the other 94 are a national or regional
        # thing with no single town behind them, and the graph said nothing
        # about them at all — so /events published 150 and the knowledge
        # graph knew 56, which is the `pop_line` shape in an index rather
        # than in a sentence. Both edges are drawn now, because both are
        # true and they answer different questions: which country is this on,
        # and which town is it in. `part_of` and `located_in` already target
        # two entity types each, so one relationship with two targets is this
        # document's own idiom rather than a new one.
        for f in c.get("festivals", []):
            edge("event", f"{slug}#{f['name']}", "happens_in", "country", slug,
                 month=f["month"])
        for r in c["regions"]:
            rid = f"{slug}/{r['slug']}"
            edge("region", rid, "part_of", "country", slug)
            for t in r["cities"]:
                cid = f"{rid}/{t['slug']}"
                edge("destination", cid, "part_of", "region", rid)
                for pl in t.get("places", []):
                    edge("place", f"{cid}/{pl['slug']}", "located_in", "destination", cid,
                         kind=pl["kind"])
                for e in t.get("experiences", []):
                    eid = f"{cid}#{e['slug']}"
                    edge("experience", eid, "located_in", "destination", cid, kind=e["kind"])
                    # The §2.5 edge, carrying which of the three it is. The
                    # schema's example calls this available_at; ours knows
                    # whether you stand on the place, start from it, or look
                    # at it from a boat.
                    for link in e.get("at", []):
                        edge("experience", eid, "available_at", "place",
                             f"{cid}/{link['place']}", how=link["how"])
                # Transport is a relationship, not a column: a node serves a
                # destination, and the weight is a straight-line distance
                # rather than a travel time, which is stated everywhere it
                # appears.
                for nd in t.get("transport", []):
                    edge("transport_node", f"{nd['kind']}:{nd['name']}", "serves",
                         "destination", cid, km=nd["km"], straightLine=True)
                for f in c.get("festivals", []):
                    if f.get("city") == t["slug"]:
                        edge("event", f"{slug}#{f['name']}", "happens_in", "destination", cid,
                             month=f["month"])

    for j in data["journeys"]:
        for leg in j["legs"]:
            edge("journey", j["slug"], "includes", "destination", leg["city"],
                 day=leg["day_number"], nights=leg["nights"])
            for ps in leg.get("places", []):
                edge("journey", j["slug"], "stops_at", "place", f"{leg['city']}/{ps}",
                     day=leg["day_number"])

    for st in data["stories"]:
        for cid in st.get("places", []):
            edge("story", st["slug"], "about", "destination", cid)

    # A theme's destinations are `stops`, not `places` — the two entities use
    # different words for the same idea, and reading the wrong one produced
    # 0 `gathers` edges in a document that otherwise looked complete. That is
    # the failure mode a derived index is supposed to prevent, arriving via
    # the one place it cannot: a typo in the derivation itself. Hence the
    # per-relationship counts in this document and the floor on them in
    # checks.py — a relationship that silently drops to zero is exactly what
    # nobody notices.
    for th in data["themes"]:
        for stop in th.get("stops", []):
            edge("theme", th["slug"], "gathers", "destination", stop["city"],
                 why=bool(stop.get("why")))

    # Proximity, computed with the same function the planner uses so the
    # graph and a route can never disagree about what is close.
    nodes = sorted(data["cities"].items())
    for cid, n in nodes:
        near = sorted(
            ((haversine(n["city"], m["city"]), mid) for mid, m in nodes if mid != cid),
        )[:6]
        for km, mid in near:
            edge("destination", cid, "near", "destination", mid, km=round(km))

    # Seeded from the declared vocabulary, so a relationship the derivation
    # emits none of is published as 0 rather than omitted. The other
    # direction is asserted too: a relationship this function emits and the
    # table does not declare stops the build, because a new edge type with
    # no floor and no trigger is the state `stops_at` was in.
    kinds = {rel: 0 for rel in GRAPH_RELATIONSHIPS}
    for row in E:
        if row[2] not in kinds:
            raise SystemExit(
                f"graph_api emits the relationship {row[2]!r} and "
                f"GRAPH_RELATIONSHIPS does not declare it: it would ship with "
                f"no floor and no trigger, which is how `stops_at` stayed at "
                f"zero for the life of the graph")
        kinds[row[2]] += 1

    return "/api/graph.json", {
        "generated": "build",
        "licence": API_LICENCE,
        "note": ("Every relationship in the atlas, derived at build time from relations "
                 "that are validated elsewhere — so no edge can point at an entity that "
                 "does not exist. `weight` appears only as `km`, a real straight-line "
                 "distance; there is no relevance score, because nobody computed one."),
        "shape": ["sourceType", "sourceId", "relationship", "targetType", "targetId",
                  "metadata (optional)"],
        "relationships": kinds,
        "edges": E,
    }


def countries_api(data):
    """Country-level facts, as one flat document.

    The specification files this and /api/journeys.json under "Stage 2",
    alongside the endpoints that need authentication. That grouping was wrong
    and it took a re-read to notice: these two are read-only projections of
    data already committed to this repository. Nothing about them needs a
    backend, so the only thing keeping them unshipped was the label.

    Advisory countries ARE present, with the advisory on them. A consumer
    deciding what to do about Belarus needs to be told there is an advisory,
    not handed a document in which the country silently does not exist. That
    is the opposite of the rule for /api/atlas.json, and deliberately: the
    planner index is a list of places to route through, and this is a
    description of the continent.
    """
    out = []
    for slug, c in sorted(data["countries"].items()):
        regions = []
        for r in c["regions"]:
            regions.append({
                "slug": r["slug"], "name": r["name"], "url": urls.region(c, r),
                "interests": r["interests"],
                "type": r["type"],
                # Derived, and it says so: we hold region membership and no
                # region geometry, so a region's position is the middle of
                # its own destinations. A consumer that treats this as a
                # boundary centroid would be wrong, so the source is in the
                # document rather than in a footnote on a page.
                "position": r["derived"],
                "positionSource": r["derived_source"],
                "destinations": [
                    dict({"slug": t["slug"], "name": t["name"],
                          "url": urls.city(c, r, t),
                          "lat": t["lat"], "lon": t["lon"]},
                         **({"kind": t["city_type"],
                             "kindSource": t.get("city_type_source")}
                            if t.get("city_type") else {}),
                         **({"population": t["derived"]["population"],
                             "populationSource": t["derived_source"]}
                            if t.get("derived", {}).get("population") else {}))
                    for t in r["cities"]],
            })
        row = {
            "slug": slug,
            "name": c["name"],
            "url": urls.country(c),
            "macro": c["macro_slug"],
            "capital": c["capital"],
            "iso2": c["code"].upper(),
            # Every derived fact carries the dataset that produced it. A
            # population with no source is a number a consumer has to trust;
            # one with a source is a number they can check.
            "derived": dict(c.get("derived", {}), source=c.get("derived_source")),
            "currency": c["currency"],
            "timezone": c["timezone"],
            "languages": c["languages"],
            "membership": c.get("blocs", []),
            "budget": c["budget"],
            "dailyEur": c["daily_eur"],
            "season": {"peak": c["season"]["peak"],
                       "shoulder": c["season"].get("shoulder", [])},
            "regions": regions,
            # Verification, in the document rather than only on the page. A
            # consumer that cannot see whether a fact was checked will assume
            # it was.
            "verification": verification_of(c),
        }
        if c.get("advisory"):
            row["advisory"] = {"level": c["advisory"]["level"], "note": c["advisory"]["note"]}
        out.append(row)
    return "/api/countries.json", {
        "generated": "build",
        "licence": API_LICENCE,
        "note": "Country-level facts. Advisory countries are present, with the advisory.",
        "countries": out,
    }


def journeys_api(data):
    """The curated routes, with their legs resolved to real destinations."""
    out = []
    for j in data["journeys"]:
        legs = []
        for leg in j["legs"]:
            n = data["cities"][leg["city"]]
            legs.append({
                "city": leg["city"],
                "name": n["city"]["name"],
                "country": n["country"]["name"],
                "url": urls.city(n["country"], n["region"], n["city"]),
                "nights": leg["nights"],
                "note": leg.get("note", ""),
                "lat": n["city"]["lat"], "lon": n["city"]["lon"],
            })
        out.append({
            "slug": j["slug"], "name": j["name"], "url": urls.journey(j),
            "strapline": j["strapline"], "summary": j["summary"],
            "days": j["days"], "budget": j["budget"], "difficulty": j["difficulty"],
            "transport": j["transport"], "accommodation": j["accommodation"],
            "months": j["months"], "interests": j["interests"],
            "creator": j["creator"], "pack": j["pack"],
            "countries": sorted({data["cities"][l["city"]]["country"]["name"] for l in j["legs"]}),
            "legs": legs,
        })
    return "/api/journeys.json", {
        "generated": "build",
        "licence": API_LICENCE,
        "note": "Curated routes. Estimates are planning arithmetic, not quotes.",
        "journeys": out,
    }


# The kinds this index emits whose plural is not the noun plus an s. Not a
# general pluraliser: it is a closed list, and a kind added without a row here
# gets the -s that is right for most of them.
_KIND_PLURAL = {
    "City": "Cities",
    "Country": "Countries",
    "Category": "Categories",
    "Story": "Stories",
    "Region of Europe": "Regions of Europe",
}


def search_api(data):
    """One flat index of everything findable, built once and filtered in the
    browser. Small enough (a few hundred KB) that shipping it whole beats
    running a search service, and it works offline."""
    rows = []

    def add(kind, name, sub, url, text, weight=1.0, **extra):
        row = {"k": kind, "n": name, "s": sub, "u": url,
               "t": " ".join(text).lower(), "w": weight}
        row.update({k: v for k, v in extra.items() if v is not None})
        rows.append(row)

    for m in data["macros"]:
        add("Region of Europe", m["name"], f"{len(m['countries'])} countries",
            urls.macro(m), [m["name"], m["blurb"]], 1.4)
    for c in data["countries"].values():
        add("Country", c["name"], c["macro_name"], urls.country(c),
            [c["name"], c.get("official", ""), c["capital"], c["tagline"], c["summary"],
             " ".join(c["interests"]),
             " ".join(data["interests"][i]["name"] for i in c["interests"])], 2.0,
            b=c["budget"], m=c["season"]["peak"] + c["season"].get("shoulder", []),
            i=c["interests"])
        for r in c["regions"]:
            add("Region", r["name"], c["name"], urls.region(c, r),
                [r["name"], r["summary"], " ".join(r["interests"])], 1.2)
            for t in r["cities"]:
                # The extra fields are what make "cheap quiet beaches near
                # Prague in September" answerable without a search service.
                add("City", t["name"], f"{r['name']}, {c['name']}", urls.city(c, r, t),
                    [t["name"], t["summary"], " ".join(t["highlights"]),
                     " ".join(t["interests"]),
                     " ".join(data["interests"][i]["name"] for i in t["interests"]),
                     c["name"], r["name"]], 1.6,
                    b=c["budget"], q=(1 if t.get("quiet") else None),
                    m=c["season"]["peak"] + c["season"].get("shoulder", []),
                    la=t["lat"], lo=t["lon"], cs=c["slug"],
                    # §2.19: what KIND of place it is, so "mountain villages"
                    # can mean villages. The field existed after the schema
                    # audit and the search did not read it, so "romantic
                    # mountain villages near Milan" quietly dropped the word
                    # "villages" and returned Bellagio and Vernazza.
                    ct=t.get("city_type"),
                    i=sorted(set(t["interests"]) | set(r["interests"])))
                for pl in t.get("places", []):
                    add("Place", pl["name"], f"{t['name']}, {c['name']}",
                        urls.place(c, r, t, pl),
                        [pl["name"], pl["summary"], PLACE_KIND_NAMES[pl["kind"]], t["name"], c["name"]],
                        1.5, b=c["budget"], la=pl["lat"], lo=pl["lon"], cs=c["slug"])
                for e in t.get("experiences", []):
                    add("Experience", e["name"], f"{t['name']}, {c['name']}",
                        urls.city(c, r, t), [e["name"], e["summary"], e["kind"]], 0.9)
    for j in data["journeys"]:
        add("Journey", j["name"], f"{j['days']} days", urls.journey(j),
            [j["name"], j["strapline"], j["summary"]], 1.5)
    for t in data["themes"]:
        add("Theme", t["name"], t["strapline"], f"/themes/{t['slug']}",
            [t["name"], t["strapline"], t["summary"]], 1.5)
    for st in data["stories"]:
        add("Story", st["title"], st["section"], f"/stories/{st['slug']}",
            [st["title"], st["standfirst"], st["section"]], 1.1)
    for f in data["fund"]:
        add("Fund project", f["name"], f["theme"], urls.fund_project(f),
            [f["name"], f["summary"], f["need"]], 0.8)
    for i in data["taxonomy"]["interests"]:
        add("Interest", i["name"], "Everywhere tagged for it", urls.interest(i["slug"]),
            [i["name"], i["slug"]], 1.3)
    for cat in data["categories"]:
        add("Category", cat["name"], cat["blurb"][:70], urls.category(cat["slug"]),
            [cat["name"], cat["blurb"]], 1.3)
        # THE THIRD ENUMERATION OF THE SAME LIST. The build loop emits the
        # pages, the category page links them, and this index points at
        # them — so the floor had to reach all three, and the check that
        # found this one ("points at a page which is not built") is the only
        # reason the third was not left behind. `subs_with_a_page` is the
        # one implementation; a fourth caller inherits it for free.
        for sub in subs_with_a_page(data, cat):
            add("Category", sub["name"], cat["name"],
                urls.subcategory(cat["slug"], sub["slug"]),
                [sub["name"]] + sub["keywords"], 1.1)
    return "/api/search.json", {
        "generated": "build",
        "licence": API_LICENCE,
        "note": ("One flat index of everything findable, filtered in the browser. "
                 "`t` is the pre-lowercased haystack; `ct` is the kind of place; "
                 "`la`/`lo` are coordinates. No ranking is precomputed — the "
                 "weight `w` is a kind weight, not a relevance score."),
        "rows": rows,
        # Sent rather than typed into the prose. The empty state used to say
        # "50 countries and 244 cities" while the atlas held 319, and nothing
        # failed, because a number inside a sentence in a JavaScript file is
        # checked by nothing at all.
        "counts": {"countries": len(data["countries"]), "cities": len(data["cities"])},
        # THE RESULT HEADINGS WERE PLURALISED BY ADDING AN S IN THE BROWSER,
        # and five of the twelve kinds this index carries do not take one:
        # "Citys", "Countrys", "Categorys", "Storys" and "Region of Europes",
        # on the site's own search results. The comment two lines above says a
        # number typed into a JavaScript file is checked by nothing at all;
        # neither is a grammar rule. The build knows every kind it emits, so
        # it sends the plural rather than leaving the browser to guess.
        "kindPlural": {k: v for k, v in sorted(
            {r["k"]: _KIND_PLURAL.get(r["k"], r["k"] + "s") for r in rows}.items())},
        "monthNames": data["taxonomy"]["month_names"],
        "interests": {i["slug"]: i["name"] for i in data["taxonomy"]["interests"]},
    }


# WHERE EACH KIND IN THE INDEX CAN BE BROWSED WITHOUT SEARCHING. Declared
# beside the kinds rather than inside the page, because the resting state's
# own sentence promises it — "every kind is browsable without searching at
# all" — and a kind added to the index with no entry here makes that sentence
# false. `c_search_states_its_index` fails on a kind the index holds and this
# table does not.
#
# Places are the one that is not an index page: 255 of them and no /places,
# so the honest browse surface is /map, whose own layer toggle is labelled
# "Places (255)" and draws every one. Pointing it at a destination page
# instead would send a reader to one of 125.
# The third member is the kind's position in the Atlas's CONTAINMENT CHAIN,
# or None where the kind crosses it. A corner of Europe holds countries, a
# country holds regions, a region holds destinations, a destination holds
# places — that nesting is what every URL on this site is made of and what
# `/api/graph.json` derives its `contains` edges from. Everything else is a
# set drawn ACROSS it: an experience belongs to a destination, a journey
# crosses countries, a theme ignores borders altogether.
#
# THIS IS A CLASSIFICATION AND THE COUNTS BESIDE IT ARE MEASUREMENTS, which
# is the Data Integrity Rule in both directions on one table: the chain is
# editorial and the extent of each rung is counted off the index on every
# build. Sorting the twelve by size instead put Places above Countries — 255
# against 50 — which is arithmetically true and says the wrong thing about a
# nested atlas, and left the page twelve rows of one component at 56%.
_SEARCH_BROWSE = {
    "Region of Europe": ("/countries", "The nine corners the Atlas is grouped into", 1),
    "Country": ("/countries", "Every country the Atlas holds a page for", 2),
    "Region": ("/countries", "Groupings by coast, range and shared history", 3),
    "City": ("/discover", "Cities, villages, valleys, islands and sites", 4),
    "Place": ("/map", "Museums, castles, peaks and sites, drawn as a map layer", 5),
    "Experience": ("/experiences", "Things to do, each one attached to a place", None),
    "Category": ("/experiences", "The eight kinds of experience and their sub-categories", None),
    "Interest": ("/interests", "The seventeen tags, and how far each narrows Europe", None),
    "Journey": ("/journeys", "Cross-border routes, in order, with the nights counted", None),
    "Theme": ("/themes", "Ways through Europe that ignore its borders", None),
    "Fund project": ("/fund", "The public register of work worth putting something back into", None),
    "Story": ("/stories", "The editorial desk, each piece linked into the Atlas", None),
}


def search_page(data):
    # THE HEAD SAID 550 AND THE INDEX IT SHIPS HOLDS 1,064.
    #
    # That figure was a hand-assembled sum of SEVEN collections — countries,
    # regions, cities, journeys, themes, stories, fund — and `search_api`
    # writes TWELVE kinds. So the page understated its own index by 514
    # records: all 255 places, all 197 experiences, the seventeen interests,
    # the thirty-six categories and the nine macro regions. *A number that is
    # not the set's own extent is worse than none, because it reads as one* —
    # this repository's own line about /europe-in printing 319 where the set
    # was 12, arriving on the one page whose entire subject is the size of an
    # index.
    #
    # And the resting state under it listed those same seven kinds beneath a
    # sentence reading "every kind is browsable without searching at all",
    # which is the `pop_line` shape: a list that omits part of its own set
    # reads as a policy rather than as an omission.
    #
    # Both are derived from the index now — the same rows the browser
    # filters, counted by the function that builds them — so a kind added to
    # `search_api` appears here on the next build instead of waiting for
    # somebody to remember two places.
    # `search_api` returns (path, document) — the pair the build writes —
    # so the rows come out of its second member. Calling it here rather than
    # re-deriving the counts is the whole point: a second implementation of
    # one fact is a second chance for the page and the index to disagree.
    rows = search_api(data)[1]["rows"]
    n = len(rows)
    # A SEARCH PAGE AT REST WAS A BOX AND 280 PIXELS OF NOTHING.
    #
    # It said "550 records indexed" in the head and then showed a reader none
    # of them. Every other instrument on this site opens on the thing it
    # operates over — /map draws the continent, /discover draws its dots — and
    # this one, which holds the largest index on the site, opened on an empty
    # panel above the footer.
    #
    # What it shows is the index BY KIND, with the count and a way into each,
    # every figure derived from the same structures the index is built from.
    # It is not a list of suggested searches: a curated set of example queries
    # would be an editorial ranking of what people should look for, and this
    # page publishes that nobody can buy a position in it.
    #
    # It sits INSIDE #results, so the first keystroke replaces it. A resting
    # state that survives the first query is a resting state a reader has to
    # dismiss.
    # Every kind the index holds, largest first, each with the count the
    # index itself carries and the surface it can be browsed from.
    bykind = {}
    for r in rows:
        bykind[r["k"]] = bykind.get(r["k"], 0) + 1
    # THE PLURAL IS TAKEN VERBATIM, BECAUSE ONE OF THE TWELVE CARRIES A
    # PROPER NOUN. Lower-casing the name and re-capitalising its first letter
    # is the obvious way to normalise a heading and it printed "Regions of
    # europe" — the same class of fault as pluralising by adding an s in the
    # browser, which is what `_KIND_PLURAL` exists to have already fixed.
    def band(want_spine):
        # The spine keeps the NESTING's own order; what crosses it is
        # largest first, because nothing orders those seven but their size.
        picked = [(k, cnt) for k, cnt in bykind.items()
                  if k in _SEARCH_BROWSE
                  and (_SEARCH_BROWSE[k][2] is not None) == want_spine]
        picked.sort(key=lambda kc: _SEARCH_BROWSE[kc[0]][2] if want_spine else -kc[1])
        return [(cnt, _KIND_PLURAL.get(k, k + "s"),
                 _SEARCH_BROWSE[k][0], _SEARCH_BROWSE[k][1])
                for k, cnt in picked]

    spine, across = band(True), band(False)
    kinds = spine + across
    # AND THE BAR BESIDE EACH COUNT CAME OFF. "A chart on which four of
    # seven series cannot be seen is the wrong track, not the wrong data" is
    # this repository's own line about this exact element, and the repair it
    # got was a wider track: 80 pixels to 224. Measured after: the seven
    # fills are 36, 92, 224, 11, 9, 7 and 9 pixels, so four of the seven are
    # still under twelve. Widening a linear track cannot fix a 45:1 range —
    # 319 destinations against 9 stories — it only moves where the floor is.
    #
    # The bar was trying to say "the index is mostly destinations", and the
    # numbers beside it say that already, in one glance, exactly. A drawing
    # that four of seven rows cannot use is four rows of noise.
    # AN H2 ABOVE THE ROWS, BECAUSE A ROW'S NAME IS AN H3. The first version
    # put the rows straight under the page's h1 and the accessibility scan
    # caught it in one run: h1 → h3 at "Countries". Every other place this
    # primitive appears has a band heading over it, and the results that
    # replace this state announce themselves with an h2 too — so the resting
    # state and the state it becomes have the same shape.
    # AND THE LEDE NAMED EIGHT OF THE TWELVE KINDS IT INTRODUCES.
    # "countries, regions, destinations, places, journeys, themes, stories
    # and projects" left out experiences, interests, categories and the nine
    # corners of Europe — `pop_line`'s shape in a list rather than in a
    # field, on the page whose subject is the extent of an index. Twelve
    # names is not a sentence either, and "the kinds are below" is a claim
    # about the page around it that the first keystroke makes false, because
    # the resting state is what the results replace. So the lede states the
    # NUMBER of kinds, derived, and the band under it names every one.
    # TWELVE ROWS OF ONE COMPONENT ON A 1,783-PIXEL PAGE MEASURED 56% AGAINST
    # A CEILING OF 52, and shortening the list is the one repair this page
    # cannot take: its whole subject is the extent of the index. The two
    # bands are the structure the count-sorted list threw away, and they
    # each say something a flat list cannot — the spine is where a reader
    # goes DOWN, and the rest is where a reader goes ACROSS.
    def rows_html(items, level):
        return ('<div class="rows">' + "".join(
            f'<a class="row" href="{href}">'
            f'<div><h{level}>{esc(label)}</h{level}>'
            f'<p class="rowsub">{esc(what)}</p></div>'
            f'<p class="rowmeta">{count:,}</p></a>'
            for count, label, href, what in items) + "</div>")

    atrest = ('<h2>What is in the index</h2>'
              '<p class="lede">Everything here is searchable from the box '
              'above, and every kind is browsable without searching at all. '
              f'{len(spine)} of them nest inside one another; the other '
              f'{len(across)} cut across that.</p>'
              '<h3 class="mini">The Atlas, from the outside in</h3>'
              + rows_html(spine, 4)
              + '<h3 class="mini">And what crosses it</h3>'
              + rows_html(across, 4))

    body = f"""
{crumbs([("Europe", "/discover"), ("Search", None)])}
<div class="pagehead instrument">
  <p class="kicker">Search</p>
  <h1>Find it.</h1>
  {head_extent([(n, 'records indexed')])}
  <p class="lede">Everything on EuropeDoor — {len(kinds)} kinds of record — in one
  index that runs in your browser. Nothing you type is sent anywhere, and nobody
  can buy a position in it.</p>
</div>
<form class="form" id="searchform" role="search">
  <div class="field">
    <label for="q">Search Europe</label>
    <input type="text" id="q" name="q" autocomplete="off" autofocus
           placeholder="quiet beaches in september">
    <p class="small">It reads more than words: <em>cheap</em> and <em>quiet</em> filter,
    a month narrows to places that are good in it, and <em>near Prague</em> means within
    300 kilometres of Prague — so <em>medieval castles near Prague</em> and
    <em>cheap mountains</em> both work. Whatever it understood is shown back to you as
    chips.</p>
  </div>
</form>
<div class="chips" id="searchunderstood" aria-live="polite"></div>
<div id="results" aria-live="polite">{atrest}</div>
<noscript><p class="small">Search needs JavaScript. The
<a href="/countries">Atlas</a> is fully browsable without it.</p></noscript>
{ad_slot("/search")}
"""
    return "/search/index.html", page(
        "Search", body, path="/search", area=None,
        description="Search every country, region, city, journey, theme, story and project on EuropeDoor — in your browser, with nothing sent anywhere.",
        scripts=["/assets/js/search.js"],
        # INTELLIGENCE — search and filter intelligence
        world="intelligence"
    )

# ── discover: the entry point ─────────────────────────────────────────

# ── Europe in Motion ─────────────────────────────────────────────────
#
# The transformation brief asks for a dynamic discovery layer: "Europe in
# Autumn", "Europe by rail", "Europe's hidden villages". The trap in that
# request is that the cheapest version is a banner with a hand-picked list
# behind it, which looks identical to the real thing on the day it ships and
# is wrong within a season.
#
# So each motion is a QUERY, declared in data/motions.json and evaluated
# here against the whole Atlas on every build. Three consequences, all
# deliberate:
#
#   * there is no field for naming destinations, so a motion cannot become a
#     curated list without somebody changing the validator;
#   * every page prints the query it ran, in words, above the results —
#     which is the difference between a landing page and an assertion;
#   * a motion matching nothing fails the build rather than shipping an
#     empty page with a nice headline on it.
#
# The specification also warns against mass-producing thin programmatic
# pages. Twelve of these, each carrying a real query over 319 destinations
# plus the journeys and themes that match, is the opposite of thin — but the
# number matters, and it is small on purpose.

# A SECTION HOLDING FEWER THAN THREE IS A HEADING OVER A ROW, and three is
# the smallest number for which "group" is the right word. The case it
# excludes is real in both families that read it: the northern lights are
# eight destinations at eight distinct latitudes, which would be eight
# headings over one row each — the nine-desks-one-story layout the stories
# index was thrown away for — and /experiences/history holds exactly one
# generous invitation among thirty.
#
# ONE NUMBER, because two families decide the same question and *a second
# implementation of a thing is a second chance to make its mistake*. What
# each family groups BY is its own: a motion groups by the clause its query
# matched, a category by what an invitation costs. The floor is the shared
# part and it is the only shared part.
GROUP_MIN = 3


def motion_match(data, m, cid, n):
    """Does one destination satisfy one motion? Returns (bool, reasons)."""
    c, r, t = n["country"], n["region"], n["city"]
    own, near = set(t["interests"]), set(r["interests"])
    tags = own | near
    why = []

    wants = m.get("interests", [])
    if wants:
        hit = [w for w in wants if w in tags]
        if m.get("all_interests"):
            if len(hit) != len(wants):
                return False, []
        else:
            if not hit:
                return False, []
        # THE ROW-LEVEL CLAIM WAS THE ONE HALF OF THIS THAT STAYED FALSE.
        # The previous commit measured that `tags` is the UNION of a
        # destination's own interests and its region's — 537 extra tag
        # applications across the seventeen interests — and fixed the
        # sentence the PAGE prints. Every ROW went on saying "tagged
        # Islands", which for Tartu, a mainland university town in the
        # region "Tartu & South Estonia", is not true of the destination at
        # all: its region carries the tag. **Measured on the shown sets: 15
        # of the 25 on Europe's islands, 25 of 56 on the coastlines, 24 of
        # 59 on the mountains and 19 of 55 on the sacred world qualify on
        # their region rather than on themselves.** On the one family whose
        # whole credibility claim is that a page prints what produced it, a
        # majority of one page's rows made a claim about the wrong record.
        # The clause says which side it came from now, and the page groups
        # the list by it so the clause is hoisted once per group rather than
        # restated on every row.
        mine = [w for w in hit if w in own]
        theirs = [w for w in hit if w not in own]
        nm = lambda ws: and_list([data["interests"][w]["name"] for w in ws])
        verb = "carries" if m.get("all_interests") else "tagged"
        if mine and theirs:
            why.append(f"{verb} {nm(mine)}, in a region tagged {nm(theirs)}")
        elif mine:
            why.append(f"{verb} {nm(mine)}")
        else:
            why.append(f"in a region tagged {nm(theirs)}")

    months = m.get("months", [])
    if months:
        season = c["season"]
        if m.get("shoulder_only"):
            got = [x for x in months if x in season.get("shoulder", [])]
            if not got:
                return False, []
            why.append("in its quieter shoulder season in "
                       + and_list([data["taxonomy"]["month_names"][x] for x in got]))
        else:
            got = [x for x in months if x in season["peak"] or x in season.get("shoulder", [])]
            if not got:
                return False, []
            why.append("in season in "
                       + and_list([data["taxonomy"]["month_names"][x] for x in got]))

    if "min_lat" in m:
        if t["lat"] < m["min_lat"]:
            return False, []
        why.append(f"at {t['lat']:.1f}° north")

    if m.get("max_nights") and t["nights"][1] > m["max_nights"]:
        return False, []

    disc, terms = discoverability(
        c, r, t,
        journeys_through=len(data["back"].get(cid, {}).get("journeys", [])),
        country_cities=sum(len(x["cities"]) for x in c["regions"]))
    if disc < m.get("min_disc", 0):
        return False, []
    if m.get("min_disc", 0) >= 60 and terms:
        # Two clauses, not one. The score varies per place and is the
        # informative half; the terms behind it are usually identical across
        # a whole motion, and joining them into one string meant the shared
        # half could never be hoisted out.
        why.append(f"scores {disc} for discoverability")
        why.append(and_list([x.lower() for x in terms[:2]]))
    return True, why


def and_list(items):
    """"a", "a and b", "a, b and c" — and "" for nothing, because a motion
    with no interests (the latitude and discoverability ones) reaches here
    with an empty list and used to take the last index of it."""
    items = [x for x in items if x]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + " and " + items[1]
    return ", ".join(items[:-1]) + " and " + items[-1]


def motion_query_words(data, m):
    """The query, in words, printed above the results. A landing page that
    will not say what produced it is an assertion."""
    parts = []
    wants = m.get("interests", [])
    if wants:
        names = [data["interests"][w]["name"] for w in wants]
        parts.append(("every destination tagged " + and_list(names))
                     if m.get("all_interests") and len(names) > 1
                     else ("any destination tagged " + and_list(names)))
        if m.get("all_interests") and len(names) > 1:
            parts[-1] = "every destination tagged with all of " + and_list(names)
    if m.get("months"):
        names = [data["taxonomy"]["month_names"][x] for x in m["months"]]
        parts.append(("whose country's quieter shoulder season falls in "
                      if m.get("shoulder_only") else "in season in ") + and_list(names))
    if "min_lat" in m:
        parts.append(f"lying above {m['min_lat']:g}° north")
    if m.get("min_disc"):
        parts.append(f"scoring {m['min_disc']} or more for "
                     "discoverability")
    if m.get("max_nights"):
        parts.append(f"worth no more than {m['max_nights']} nights, which is "
                     "what makes it a village rather than a city")
    # EVERY CLAUSE NEEDS SOMETHING TO ATTACH TO.
    #
    # The interest clause carries its own subject ("any destination tagged
    # Islands"); the other four are relative clauses — "lying above 63°
    # north", "scoring 80 or more for discoverability", "whose country's
    # quieter shoulder season falls in October". A motion with no interest
    # term therefore produced a dangling fragment, which read acceptably
    # under a heading that said "The query that made this page" and stopped
    # reading at all once the query became one hoisted line: "The query
    # lying above 63° north." Four of the twelve are like that.
    #
    # So the subject is always present, and the result is a sentence.
    # It is a PREFIX and not another list item: and_list joins with "and",
    # so inserting it produced "Every destination and lying above 63° north."
    # Two wrongs in one line, and the second only visible once the first was
    # fixed and the sentence was read.
    out = and_list(parts) + "."
    if not wants:
        out = "every destination " + out
    out = out[0].upper() + out[1:]
    if wants:
        # THE PRINTED QUERY WAS NARROWER THAN THE QUERY THAT RAN, ON THE ONE
        # FAMILY WHOSE WHOLE RULE IS THAT A PAGE PRINTS WHAT PRODUCED IT.
        #
        # `motion_match` reads `set(city.interests) | set(region.interests)`,
        # so a destination is returned when ITS REGION carries the tag. The
        # sentence said "any destination tagged Islands" and said nothing
        # about the region, and the gap is not small: 62 of the 86 results
        # for Food and Wine are there on their region's tags rather than
        # their own, and 58 of the 150 for Coast. It returns **Nicosia**,
        # whose own tags are history, food and cities and which is inland,
        # because the region is "Nicosia & the South Coast"; and **Tartu**,
        # a mainland university town, for Islands, because its region is
        # "The Islands & the South".
        #
        # That is the `cell` catching `cellar` failure exactly: the page
        # published its rule honestly, and a reader who checked would find
        # something the rule did not describe. The engine is not changed
        # here — a region tag is a real fact about the ground around a place
        # and 537 tag applications across nine other surfaces depend on the
        # union — what changes is that the sentence now says so, once, at
        # the end, rather than inside each clause. `docs/europe-in-redesign.md`
        # carries the per-tag propagation question and its trigger.
        # AND THE CLAUSE IS SHORT BECAUSE NINE OF THE TWELVE CARRY IT. The
        # first version spelled the whole mechanism out and produced the
        # same 130 characters on nine rows of one page, which is *never
        # explain the constraint back* — a reason shared by every result
        # belongs hoisted once above the list, and only what distinguishes
        # a row belongs in the row. So the query says the thing that is
        # true of this query, and `motion_tag_note()` says the mechanism
        # once per page.
        # And the ALL case needs different words from the ANY case: under
        # `all_interests` a destination qualifies when its own tags and its
        # region's, taken together, cover every term — so "its own tag or
        # its region's" would be a claim about one tag on a query about two.
        out = out[:-1] + (
            " \u2014 own tags and region\u2019s counting together."
            if m.get("all_interests") and len(wants) > 1
            else " \u2014 its own tag or its region\u2019s.")
    return out


def motion_tag_note():
    """The mechanism behind the tag clause, stated once per page.

    Nine of the twelve queries read a destination's own tags and its
    region's together, and the clause on each says so in five words. This
    is the sentence that explains it, hoisted — and it also reconciles the
    two numbers this site publishes for one word: /interests counts a tag
    on the DESTINATION (Mountains, 63) and a motion counts it on the
    destination or its region (115). Both are derived, both are live, and
    for the life of both families neither said which it was.
    """
    return ("A destination\u2019s own tags and its region\u2019s count "
            "together here, so a place in a region tagged for something is "
            "returned whether or not it carries the tag itself. That is why "
            "a motion\u2019s count can be larger than the same tag\u2019s "
            "count on <a href=\"/interests\">Interests</a>, which reads the "
            "destination only.")


def motion_page(data, m):
    hits = []
    for cid, n in sorted(data["cities"].items()):
        ok, why = motion_match(data, m, cid, n)
        if ok:
            hits.append((n, why))
    # A motion matching nothing is a bug in the query, not a page.
    assert hits, f"motion {m['slug']} matched nothing"

    # Two per country, as everywhere else: a list where six of the first
    # eight are Italian has described Italy rather than Europe.
    per, shown = {}, []
    for n, why in sorted(hits, key=lambda h: (h[0]["country"]["name"], h[0]["city"]["name"])):
        cs = n["country"]["slug"]
        if per.get(cs, 0) >= 2:
            continue
        per[cs] = per.get(cs, 0) + 1
        shown.append((n, why))

    # Never explain the constraint back — the same rule Discover Mode is
    # built on. On the hidden-villages page every row said "not the capital
    # and editorially quiet", which is a restatement of the query the reader
    # is already reading two inches above. A clause true of every result is
    # hoisted; each row keeps only what distinguishes it.
    #
    # AND THE LIST IS GROUPED BY THAT DISTINGUISHING CLAUSE, WHICH IS ONE
    # MECHANISM FOR ALL TWELVE QUERIES. This page measured **54% one
    # component** — thirty-eight `.row` siblings with no second component at
    # all, which is `tools/monotony.js`'s own diagnostic for a page that is
    # a list and nothing else. The list is the right answer here, because
    # the page IS the result of a query; what was missing was any structure
    # inside it, and the structure the data already holds is WHY each
    # result is in the set.
    #
    # `motion_match` returns the clauses each destination satisfied. Hoist
    # the ones every result shares, group by what is left, and the groups
    # come out of the query rather than out of a taxonomy somebody chose:
    #
    #     islands          10 tagged Islands · 15 in a region tagged Islands
    #     autumn           42 October · 26 September · 15 November · 8 both
    #     hidden villages  22 scoring 97 · 14 scoring 84 · 9 scoring 90 · …
    #     the coast        31 tagged Coast & beaches · 25 in a region tagged
    #
    # The interest split is the sharpest of them and it is the previous
    # commit's own finding one level down: `motion_match` reads the union of
    # a destination's own interests and its region's, so **15 of the 25 on
    # Europe's islands are there on their region's tags** — Tartu is a
    # mainland university town in "Tartu & South Estonia". That commit fixed
    # the sentence the PAGE prints and left every ROW claiming "tagged
    # Islands", which is a statement about the wrong record. The clause says
    # which side it came from now, so the grouping falls out of it.
    #
    # A GROUP OF ONE IS NOT A GROUP, IT IS A ROW WITH A HEADING — which is
    # the nine-desks-one-story layout the stories index was thrown away for.
    # The northern lights are eight destinations at eight distinct
    # latitudes, so grouping them would produce eight headings over one row
    # each; the page keeps its list. The test is the mean group size, and
    # three is the smallest number for which "group" is the right word.
    def _vary(why, common):
        return tuple(c for c in why if c not in common)

    common_all = [c for c in (shown[0][1] if shown else [])
                  if all(c in w for _n, w in shown)]
    buckets = {}
    for n, why in shown:
        buckets.setdefault(_vary(why, common_all), []).append((n, why))
    # EVERY GROUP, NOT THE AVERAGE. The first test was the mean group size
    # and it let a tail through: hidden villages splits 22, 14, 9, 8, 6, 3,
    # 1, 1, 1 — a mean of 7.2 and three sections holding one row each, which
    # is the exact case the floor was written for. A heading over one row
    # carries nothing the row does not.
    grouped = len(buckets) > 1 and all(
        len(v) >= GROUP_MIN for v in buckets.values())

    # THE LEVEL IS THE OUTLINE AND THE CLASS IS THE LOOK, which this
    # stylesheet records about the `row` shape: a row's name is an h2 where
    # the LIST IS THE PAGE and an h3 inside a band whose own h2 is the level
    # above it. Both states exist on this family now — a grouped page puts
    # each list inside a section with its own heading, so a row there is an
    # h3, and the two ungrouped pages keep h2 because the list is still the
    # page. Reading it off `grouped` rather than passing it per call site is
    # the fourteen-call-sites-forgot-the-motif failure not repeated.
    lvl = "h3" if grouped else "h2"

    def _rows(part):
        common = [c for c in (part[0][1] if part else [])
                  if all(c in w for _n, w in part)]
        body = "".join(
            f"""<a class="row" href="{urls.city(n['country'], n['region'], n['city'])}">
        <div><{lvl}>{esc(n['city']['name'])}</{lvl}>
        <p class="rowsub">{esc(n['city']['summary'])}</p>
        {f'<p class="whythis">{esc(and_list([c for c in why if c not in common]))}.</p>'
             if [c for c in why if c not in common] else ""}</div>
        <p class="rowmeta">{esc(n['country']['name'])}<br><span class="small">
        {nights_line(n['city'])}</span></p></a>"""
            for n, why in part)
        return common, body

    blocks, shared_note = [], ""
    if not grouped:
        # AND THE LIST THAT STAYS A LIST IS ORDERED BY THE CLAUSE THAT WOULD
        # HAVE GROUPED IT. Two of the twelve keep their list — hidden
        # villages, whose clause is a discoverability SCORE with a long tail
        # of values held by one destination each, and the northern lights,
        # which are eight destinations at eight distinct latitudes. Both
        # were sorted alphabetically by country, which is *the order a
        # reader is given is alphabetical by a key they cannot see*: the
        # runs are together now, largest first, so the quietest villages
        # lead the page whose whole argument is the score. Ordered by the
        # bucket's own SIZE rather than by the clause string, because
        # "scores 97" sorting before "scores 84" is an accident of decimal
        # notation.
        shown.sort(key=lambda x: (-len(buckets[_vary(x[1], common_all)]),
                                  _vary(x[1], common_all),
                                  x[0]["country"]["name"], x[0]["city"]["name"]))
        common, body = _rows(shown)
        shared_note = (f'<p class="whyall"><span>All of them</span> '
                       f'{esc(and_list(common))}.</p>' if common else "")
        blocks.append(f'<div class="rows molist">{body}</div>')
    else:
        # LARGEST GROUP FIRST, because most of the answer is the answer. The
        # alternative is the order the clauses happened to be built in,
        # which is *the order a reader is given is alphabetical by a key
        # they cannot see* in another costume.
        shared_note = (f'<p class="whyall"><span>All of them</span> '
                       f'{esc(and_list(common_all))}.</p>' if common_all else "")
        for vary, part in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            # THE GROUP'S OWN HOISTED LINE, IN THE PAGE'S EXISTING
            # VOCABULARY. `_rows` already computes what every row in a set
            # shares, and inside a group that is the whole varying clause —
            # so the group head is the count and `.whyall` is the clause,
            # which is the component whose entire job is *a clause true of
            # every result in this set*, already on this page twice. The
            # first version set the clause IN the heading and produced
            # "42 destinations, in its quieter shoulder season in October":
            # the clause is written about one destination, so a plural
            # subject disagrees with its own pronoun. A count as the
            # heading and the clause under it says the same thing and needs
            # no second grammar.
            _c, body = _rows(part)
            blocks.append(
                f'<section class="moqual">'
                f'<h2 class="mini">{n_of(len(part), "destination")}</h2>'
                + (f'<p class="whyall"><span>All of them</span> '
                   f'{esc(and_list(_c))}.</p>' if _c else "")
                + f'<div class="rows molist">{body}</div></section>')
    rows = "".join(blocks)

    # THE ANSWER TO THE QUERY, AS A SHAPE.
    #
    # A motion is a query, and its result is a distribution across the
    # continent — "Europe's hidden villages" is 65 places in 42 countries and
    # the page showed none of them. Every point that is SHOWN is drawn, not
    # every point that matched: the two-per-country cap is what the reader is
    # actually reading, and a map with 83 dots under a list of 65 would be a
    # different answer to the same question.
    #
    # At this density most labels collide and are dropped, which is the
    # existing rule and is right here: the shape is the argument, and every
    # dot is a link with its name in the title.
    mpts = [(*project(n["city"]["lat"], n["city"]["lon"]),
             urls.city(n["country"], n["region"], n["city"]), n["city"]["name"])
            for n, _w in shown]
    motionmap = pointsmap(
        mpts, "mo" + "".join(ch for ch in m["slug"] if ch.isalnum())[:14],
        f'Names are dropped where they would overlap; every dot is a link.',
        f'Map of the {len(shown)} destinations in {m["name"]}',
        note=f'Coastline from <a href="/sources">Natural Earth</a>, '
             f'public domain.') if len(mpts) >= 2 else ""

    # THE QUERY IS THE PROOF, AND IT WAS A GREY BOX IN FRONT OF THE ANSWER.
    #
    # It sat above the map as `<div class="note"><h2 class="mini">The query
    # that made this page</h2>` — an administrative panel between the head
    # and the one thing on the page that answers the question. The reader met
    # the mechanism before they met Europe.
    #
    # And it said everything twice. Measured across the built site: all
    # twelve motion pages printed the match count and the shown count in the
    # panel AND again in the map caption — "19 destinations match … 8 are
    # shown" above, "The 8 destinations below … 19 matched the query" below,
    # on every one of them. That is the family's own rule broken by the page
    # that states it: never explain the constraint back.
    #
    # So the map comes up to meet the head, the counts are stated once, and
    # the query keeps the shape every other hoisted line on this site has —
    # one line, under the thing it explains, rather than a box in front of
    # it. It is still the whole credibility claim of the family and it still
    # prints the expression that produced the list.
    ncountries = len({n["country"]["slug"] for n, _ in hits})
    querynote = (
        f'<p class="whyall"><span>The query</span> {esc(motion_query_words(data, m))} '
        f'Run against all {len(data["cities"])} destinations on every build, and '
        f'nothing here is hand-picked — there is no field for naming a destination '
        f'in a motion, deliberately. {len(hits)} match, in {ncountries} '
        f'{"countries" if ncountries != 1 else "country"}'
        + (f'; the {len(shown)} below are at most two per country.'
           if len(hits) != len(shown) else ', and all of them are below.')
        + (" " + motion_tag_note() if m.get("interests") else "")
        + '</p>'
    )

    # FIVE HASH-DRAWN LANDSCAPES AT THE FOOT OF EVERY MOTION PAGE.
    #
    # This is the family whose entire argument is that a motion is not a
    # place: it has no coastline, no topography and no season, and the index
    # that introduces these twelve pages had its plates removed for exactly
    # that reason. The two related bands underneath kept theirs — three
    # journey cards and up to three theme cards, each opening on a gradient
    # chosen by the hash of a slug, on all twelve pages.
    #
    # /journeys and /themes both answered this already, and differently,
    # because the two families have different subjects: a journey's picture
    # is its ROUTE and a theme's is its SCATTER. Both are drawn from the same
    # projection as the map above, so the three bands on the page finally
    # agree about what Europe looks like.
    #
    # AND THE PAGE NEEDS `constel_defs()`. The first render was seven blue
    # dots joined by a line, floating on nothing: `constellation()` draws its
    # land with a <use> of #constel-eu, and a page that calls one without the
    # other gets a route with no continent under it. Third time in this
    # session — the same trap the 404 fell into an hour earlier.
    idx = data["cities"]
    wants = set(m.get("interests", []))

    def _pts(ids):
        return [project(idx[c]["city"]["lat"], idx[c]["city"]["lon"])
                for c in ids if c in idx]

    jrows = [j for j in data["journeys"] if wants & set(j["interests"])][:3]
    jrelated = "".join(
        f'<a class="row journeyrow" href="{urls.journey(j)}">'
        f'<div><p class="kicker">{esc(j["strapline"])}</p>'
        f'<h3>{esc(j["name"])}</h3>'
        f'<p class="rowsub">'
        + " · ".join(esc(idx[l["city"]]["city"]["name"])
                     for l in j["legs"] if l["city"] in idx)
        + f'</p><p class="rowmeta jfacts">{n_of(j["days"], "day")} · '
        f'{n_of(len(j["legs"]), "stop")} · {esc(j["difficulty"])}</p></div>'
        f'<div class="jart">'
        + constellation(_pts([l["city"] for l in j["legs"]]), route=True, frame=True,
                        aspect=1.75, mark=7, term=11)
        + '</div></a>'
        for j in jrows)

    trows = [t for t in data["themes"] if wants & set(t.get("interests", []))][:3]
    trelated = "".join(
        f'<a class="row themerow" href="/themes/{t["slug"]}">'
        + '<div class="rowart">'
        + constellation(_pts([st["city"] for st in t["stops"]]),
                        extra=" constel-theme")
        + '</div>'
        + f'<div><p class="kicker">{esc(t["strapline"])}</p>'
        f'<h3>{esc(t["name"])}</h3>'
        f'<p class="rowsub">'
        + " · ".join(esc(idx[st["city"]]["city"]["name"])
                     for st in t["stops"] if st["city"] in idx)
        + f'</p><p class="rowmeta">'
        f'{n_of(len({idx[st["city"]]["country"]["name"] for st in t["stops"] if st["city"] in idx}), "country")}'
        f'</p></div></a>'
        for t in trows)

    # THE ANSWER TO A QUERY IS A SET OF PLACES, AND NONE OF THEM WAS SHOWN.
    #
    # This family's own rule is that a motion is not a place — it has no
    # coastline, no topography and no season — and that rule took the plates
    # off the index and off the foot of these twelve pages. It says nothing
    # about the RESULTS, which are real destinations that each declare a
    # `city:` purpose. The shape of the answer is drawn above; what the
    # answer looks like was nowhere on the page.
    #
    # The strip takes the SHOWN set rather than every match, for the reason
    # already written about the map one screen up: the two-per-country cap is
    # what the reader is reading, and a strip drawn from 83 matches under a
    # list of 65 would be a different answer to the same question.
    _mstrip = ed_strip(data.get("images"), [
        {"key": f"city:{n['country']['slug']}/{n['region']['slug']}/{n['city']['slug']}",
         "alt": n["city"]["name"], "label": n["city"]["name"],
         "href": urls.city(n["country"], n["region"], n["city"])}
        for n, _w in shown], limit=8)
    if _mstrip:
        _mn = min(8, len(shown))
        _mstrip = ('<section class="ed-section">'
                   + ed_section_head("The answer",
                                     f"{numword(_mn, cap=True)} of them",
                                     "The same set the list below is, in the same "
                                     "order — not the whole match, which the query "
                                     "note above counts.")
                   + _mstrip + "</section>")
    body = f"""
{crumbs([("Europe", "/discover"), ("Europe in Motion", "/europe-in"), (m["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">Europe in Motion</p>
  <h1>{esc(m["name"])}</h1>
  <p class="lede">{esc(m["lede"])}</p>
</div>

{constel_defs()}
{motionmap}
{querynote}
{shared_note}
{_mstrip}
{rows}

{section("Journeys that go this way", f'<div class="rows journeyrows">{jrelated}</div>') if jrows else ""}
{section("Themes that run through it", f'<div class="rows">{trelated}</div>') if trows else ""}

<div class="note onward mt7">
  <h2 class="mini">Build this into a route</h2>
  <p>The Journey Planner weights the same tags this page queries on, so choosing
  {esc(and_list([data["interests"][w]["name"] for w in m.get("interests", [])]) or "these interests")}
  there will build a route through places like these.
  <a href="/plan">Plan a journey →</a> · <a href="/discover">Discover mode →</a></p>
</div>
"""
    return f"/europe-in/{m['slug']}/index.html", page(
        m["name"], body, path=f"/europe-in/{m['slug']}", area="discover",
        accent="territory",
        description=f"{m['strapline']} {len(hits)} destinations match, queried from the Atlas on every build.",
        og=("motion:" + m["slug"], motif_for(m.get("interests", [])),
            f"{m['name']} — {m['strapline']}"),
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Europe in Motion", "/europe-in"),
                           (m["name"], f"/europe-in/{m['slug']}")]),
            {"@context": "https://schema.org", "@type": "ItemList",
             "name": m["name"], "description": m["lede"],
             "url": ORIGIN + f"/europe-in/{m['slug']}",
             "numberOfItems": len(shown),
             "itemListElement": [
                 {"@type": "ListItem", "position": i,
                  "item": ld_within("TouristDestination", n["city"]["name"],
                                    urls.city(n["country"], n["region"], n["city"]))}
                 for i, (n, _w) in enumerate(shown, start=1)]},
        ],
    )


def motion_index(data):
    """The Computed Atlas: six plates, and the printed query was narrower
    than the query that ran.

    THE FAMILY'S WHOLE CREDIBILITY CLAIM IS THAT EVERY PAGE PRINTS WHAT
    PRODUCED IT, and for the life of the family the sentence said "any
    destination tagged Islands" while `motion_match` read
    `set(city.interests) | set(region.interests)`. The gap is not
    cosmetic: **62 of the 86 results for Food and Wine are there on their
    region's tags rather than their own**, 58 of 150 for Coast, 52 of 115
    for Mountains — 537 tag applications across the seventeen interests,
    47% more than the destination-only reading. It returns **Nicosia**,
    which is inland, for Europe's coastlines, because its region is
    "Nicosia & the South Coast"; and **Tartu**, a mainland university
    town, for Europe's islands. That is `cell` catching `cellar` exactly:
    the page published its rule honestly and a reader who checked would
    find something the rule did not describe.

    AND IT MEANT TWO LIVE PAGES PUBLISHED TWO NUMBERS FOR ONE WORD.
    /interests/mountains says *63 destinations*; /europe-in/mountains says
    *115 match*. Both derived, both correct under their own reading, and
    neither said which reading it was. The engine is unchanged — a region
    tag is a real fact about the ground around a place, and nine other
    surfaces depend on the union — what changed is that the query says so
    in five words and `motion_tag_note()` says the mechanism once.

    THE TWELVE SHAPES WERE ONE PER ROW, 1,152 PIXELS APART. The family's
    signature moment is the query drawn as a shape, and the argument is
    that the twelve shapes DIFFER — which is a comparison, and a
    comparison laid out vertically at one drawing per screen cannot be
    made. That is /themes' own finding about a 204-pixel continent, one
    axis over. They are a grid in the opening now, on one frame, and the
    rows carry the sentence and a photograph instead. See
    `docs/europe-in-redesign.md`.

    ZERO PHOTOGRAPHS, AND A MOTION MAY NOT HAVE ONE OF ITS OWN. The
    register declares no `motion:` purpose and must not: a motion has no
    coastline, no topography and no season, so a picture of one is a
    picture of nowhere — the refusal that took the twelve plates off this
    index. What it CAN spend is a photograph of a destination the query
    returned, and eleven of the twelve have one. The pick is derived: a
    member on its OWN tags rather than its region's, then the one fewest
    of the other eleven queries also return, then never a key already
    spent. `by-rail` has 20 results and none photographed, so it shows its
    slot and names the acquisition. Nothing was acquired.
    """
    images = data.get("images")
    total = len(data["cities"])

    # ── ONE PASS, AND EVERY FIGURE ON THIS PAGE COMES OUT OF IT ──────
    sets, facts = {}, {}
    for m in data["motions"]:
        hits = [cid for cid, n in sorted(data["cities"].items())
                if motion_match(data, m, cid, n)[0]]
        sets[m["slug"]] = hits
        facts[m["slug"]] = {
            "n": len(hits),
            "ncountry": len({data["cities"][c]["country"]["slug"] for c in hits}),
            "pct": round(100.0 * len(hits) / total) if total else 0,
            "pts": [project(data["cities"][c]["city"]["lat"],
                            data["cities"][c]["city"]["lon"]) for c in hits],
        }

    # HOW MANY OF THE TWELVE EACH DESTINATION SATISFIES. The twelve are not
    # a partition and nobody had said so: the union is the whole Atlas, the
    # commonest destination is in four of them, and one is in eight.
    degree = {cid: sum(1 for h in sets.values() if cid in h)
              for cid in data["cities"]}
    dist = {}
    for k in degree.values():
        dist[k] = dist.get(k, 0) + 1
    reached = sum(1 for k in degree.values() if k)
    # DERIVED, because "the commonest satisfies four" is a figure that was
    # true on the day it was typed — the /themes "8 PLACES" fault in prose.
    commonest = max(dist.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    most = max(degree.items(), key=lambda kv: (kv[1], kv[0]))
    mostname = data["cities"][most[0]]["city"]["name"]
    mostin = [m["name"] for m in data["motions"] if most[0] in sets[m["slug"]]]

    # THE OVERLAP, MEASURED, because "same frame, different Europe" is an
    # assertion until somebody runs the arithmetic. No two of the twelve
    # share more than 48% of their results and 0 of the 66 pairs share half.
    worst = (0.0, "", "")
    over = 0
    slugs = [m["slug"] for m in data["motions"]]
    for a in range(len(slugs)):
        for b in range(a + 1, len(slugs)):
            x, y = set(sets[slugs[a]]), set(sets[slugs[b]])
            j = len(x & y) / len(x | y) if (x | y) else 0.0
            if j > 0.5:
                over += 1
            if j > worst[0]:
                worst = (j, slugs[a], slugs[b])
    name_of = {m["slug"]: m["name"] for m in data["motions"]}

    # THE PHOTOGRAPH IS A DESTINATION THE QUERY RETURNED ON ITS OWN TAGS.
    #
    # Ordering by "fewest of the twelve" alone picked Nicosia for the coast
    # and Tartu for the islands — the region-only members, which are the
    # WEAKEST members of the set and the ones a reader would read as a
    # mistake. A direct member, then the one whose own tags are most nearly
    # just what the query asks for, then fewest of the other eleven, is the
    # picture that is both characteristic of the cut and specific to it.
    # Advisory countries are excluded because a derived point is not
    # automatically an honest one, and a key already spent is skipped
    # because one photograph on two records is *one thing, one picture* from
    # the other end.
    def direct(m, n):
        wants = m.get("interests", [])
        if not wants:
            return True
        own = set(n["city"]["interests"])
        hit = [w for w in wants if w in own]
        return len(hit) == len(wants) if m.get("all_interests") else bool(hit)

    def tagshare(m, n):
        """How much of a destination's own tag list this query asks for.

        ORDERING BY SPECIFICITY ALONE PUT THE MODERN CITY ON THE MEDIEVAL
        QUERY. "Fewest of the other eleven" is a good tie-break and a poor
        primary key: it rewards a place that is in few cuts for any reason,
        so `medieval` drew Baku (architecture, history, food, cities — the
        register's photograph is the Flame Towers) and `sacred` drew Garni.
        A destination whose own tags are most nearly JUST what the query
        asks for is the characteristic member: Mostar for the medieval
        world, Blagaj for the sacred places, Kuressaare on Saaremaa for the
        islands. Measured against the alternative on all twelve, three picks
        improve and none gets worse than a wash.
        """
        wants = set(m.get("interests", []))
        own = set(n["city"]["interests"])
        return len(wants & own) / len(own) if own else 0.0

    spent = set()
    for m in data["motions"]:
        cands = [c for c in sets[m["slug"]]
                 if held(images, "city:" + c) and c not in spent
                 and not data["cities"][c]["country"].get("advisory")
                 and direct(m, data["cities"][c])]
        cands.sort(key=lambda c: (-tagshare(m, data["cities"][c]),
                                  degree[c], c))
        facts[m["slug"]]["shot"] = cands[0] if cands else None
        if cands:
            spent.add(cands[0])
    nshot = sum(1 for f in facts.values() if f["shot"])

    # ── 01 · EUROPE IN MOTION ────────────────────────────────────────
    # THE TWELVE SHAPES, ON ONE FRAME, WHERE THEY CAN BE COMPARED. Autumn
    # is 97% of the continent, rail is a corridor up Norway and through the
    # Alps, the islands are a rim and above 63° north is the far north and
    # nothing else — and that difference is the whole argument of the page.
    # The mark size follows the count exactly as it does on /interests:
    # three hundred dots at a theme's radius is a blue mass with the
    # coastline lost under it, which says "a lot" and nothing else.
    tiles = []
    for m in data["motions"]:
        f = facts[m["slug"]]
        dense = " constel-dense" if len(f["pts"]) > 60 else ""
        tiles.append(
            f'<a class="motile" href="/europe-in/{m["slug"]}">'
            f'{constellation(f["pts"], extra=" constel-theme" + dense)}'
            f'<span class="motilen">{f["n"]}</span>'
            f'<span class="motilenm">{esc(m["name"])}</span>'
            f'<span class="motilep">{f["pct"]}% of the Atlas &middot; '
            f'{n_of(f["ncountry"], "country")}</span></a>')
    moopen = f"""
  <div class="pagehead index">
    <p class="kicker">Europe in Motion</p>
    <h1 class="mega">The continent, cut a dozen different ways.</h1>
    {head_extent([(len(data["motions"]), "queries"),
                  (total, "destinations"),
                  (len({n["country"]["slug"] for n in data["cities"].values()}),
                   "countries")])}
    <p class="lede">Not categories. {numword(len(data['motions']), cap=True)} queries, each run
    against all {total} destinations on every build, and each page prints the query that
    made it. A list somebody curated by hand looks identical to one a query produced
    &mdash; on the day it ships, and never again.</p>
  </div>
  {constel_defs()}
  <div class="mogrid">{"".join(tiles)}</div>
  <p class="small">Each shape is the destinations that query actually matched, drawn to
  the same frame so the {numword(len(data['motions']))} can be compared &mdash; computed by
  the same pass that produced the number on it, so a drawing here cannot show a set the
  page it links to would not. Marks are smaller above sixty results, because three
  hundred dots at one radius is a mass rather than a shape.
  {geo.sources_line(geo.load("europe-lod0.json"))}</p>"""

    # ── 02 · THE QUESTION ────────────────────────────────────────────
    # THE PAGE'S OWN POSITION WAS A CAPTION-SIZE NOTE AT THE BOTTOM, under
    # twelve rows, in a grey panel titled "Why this is not a set of tags" —
    # the /beyond-the-obvious fault, where the reason a family looks the way
    # it does is printed smaller than everything it explains.
    moq = f"""
  <div class="sheettext">
    <h2 class="mega">A tag tells you what carries a
    <em class="lit">label</em>.</h2>
    <p class="lede">These ask questions the tags cannot answer on their own. Which places
    have their <em>quieter</em> season in autumn rather than merely tolerating it. Which
    lie above 63&deg; north. Which score highly for
    <a href="/method#discoverability">discoverability</a> and are small enough to be
    villages rather than cities. The query is the product, and it is the thing printed on
    the page.</p>
    <p class="note">There is no field for naming a destination in a motion, so one cannot
    quietly become a hand-picked list; and a query matching nothing fails the build rather
    than shipping an empty page with a good headline on it.</p>
  </div>"""

    # ── 03 · TWELVE CUTS ────────────────────────────────────────────
    rows = []
    for m in data["motions"]:
        f = facts[m["slug"]]
        if f["shot"]:
            n = data["cities"][f["shot"]]
            shot = (f'<figure class="moshot">'
                    f'{picture(images, "city:" + f["shot"], w=900, h=700, alt=n["city"]["name"], sizes="(max-width: 52rem) 90vw, 20rem")}'
                    f'<figcaption>{esc(n["city"]["name"])}, '
                    f'{esc(n["country"]["name"])} &mdash; one of the '
                    f'{f["n"]}</figcaption></figure>')
        else:
            shot = (f'<figure class="moshot">'
                    f'{ed_slot("city:" + sets[m["slug"]][0], shape="square", label=m["name"])}'
                    f'</figure>')
        rows.append(
            f'<div class="row motionrow">{shot}'
            f'<div><p class="kicker">{n_of(f["n"], "destination")} &middot; '
            f'{n_of(f["ncountry"], "country")} &middot; {f["pct"]}% of the Atlas</p>'
            f'<h2><a href="/europe-in/{m["slug"]}">{esc(m["name"])}</a></h2>'
            f'<p class="rowsub">{esc(m["strapline"])}</p>'
            f'<p class="motionq">{esc(motion_query_words(data, m))}</p></div></div>')
    # NOT `ed_section_head()` HERE, AND THE REASON IS ALREADY WRITTEN ON IT:
    # `.ed-section` increments the same `band` counter a plate's `actmark`
    # numbers from, so one inside a plate sequence is the two-numbering-
    # systems collision that printed "01" twice on 753 pages. A plate states
    # its own head, which is what every other plate on this site does.
    mocuts = f"""
  <div class="sheettext">
    <h2 class="mega">{numword(len(data['motions']), cap=True)} cuts, and each one
    prints its own query.</h2>
    <p class="lede">The query is on the left of every row and the result is the
    number beside it. The photograph is a destination that query returned &mdash; on
    its <em>own</em> tags rather than its region&rsquo;s, and the one whose tag list
    is most nearly just what the query asks for, so the picture is of this cut
    rather than of Europe. The register holds one for {numword(nshot)} of the
    {numword(len(data['motions']))}.</p>
  </div>
  <div class="rows mocuts">{"".join(rows)}</div>"""

    # ── 04 · NOT TWELVE BUCKETS ─────────────────────────────────────
    # NOBODY HAD CROSSED THE TWELVE WITH EACH OTHER. The shapes differ, and
    # a reader can still read twelve shapes as twelve boxes — so the other
    # half of "same frame, different Europe" is that they OVERLAP: the union
    # is the whole Atlas, the commonest destination is in four of them, and
    # Narvik is in eight. A chart is a claim, so both series are asserted
    # against the dataset in `checks.py`.
    top = max(dist.values())
    # The width is a `.w0`-`.w100` utility class, not a `style` attribute —
    # a style attribute would force `style-src` open on all 1,034 pages,
    # which `checks.py` refuses. And the number sits at the END of its own
    # bar, which is /plan's own finding: a value six hundred pixels from the
    # thing it measures is not labelled.
    bars = "".join(
        f'<div class="mobar">'
        f'<span class="mobarlab">{k} '
        f'{"query" if k == 1 else "queries"}</span>'
        f'<span class="mobartr"><span class="mobarfill '
        f'w{round(100.0 * dist[k] / top)}"></span>'
        f'<span class="mobarn">{dist[k]}</span></span></div>'
        for k in sorted(dist))
    mooverlap = f"""
  <div class="sheettext">
    <h2 class="mega">Not {numword(len(data['motions']))} buckets.</h2>
    <p class="lede">The {numword(len(data['motions']))} are readings of one continent
    rather than divisions of it. {"Every one" if reached == total else numword(reached, cap=True)}
    of the {total} destinations satisfies at least one of them, the commonest number to
    satisfy is {numword(commonest)}, and
    {esc(mostname)} satisfies {numword(most[1])} &mdash;
    {esc(and_list(mostin))}.</p>
  </div>
  <figure class="mobars">
    {bars}
    <figcaption><span class="capmain">Destinations by how many of the
    {numword(len(data['motions']))} queries return them.</span>
    <span class="capsrc">Bars are a share of the largest group
    ({top}), not of the {total}. Counted on every build by the same
    {len(data['motions'])} queries the pages run.</span></figcaption>
  </figure>
  <p class="note">No two of the {numword(len(data['motions']))} share more than
  {round(worst[0] * 100)}% of their results &mdash; the closest pair is
  {esc(name_of[worst[1]])} and {esc(name_of[worst[2]])} &mdash; and
  {"none" if not over else str(over)} of the
  {len(slugs) * (len(slugs) - 1) // 2} pairs share half. That is the
  difference between twelve questions and twelve labels, and it is
  arithmetic rather than a claim.</p>"""

    # ── 05 · METHOD ─────────────────────────────────────────────────
    # THE PROJECTION IS NAMED IN ONE PLACE AND THIS IS NOT IT. A page naming
    # a Lambert conformal conic has to state its four angles in the same
    # sentence, because /map named the right projection on the wrong
    # parallels for six commits and no check read the prose. Naming it here
    # would be a second copy of that claim on a page whose subject is a
    # query rather than a drawing, so the note credits the data and links to
    # the page that publishes the projection.
    #
    # AND THIS REASON WAS FIRST WRITTEN AS AN HTML COMMENT, WHICH SHIPS.
    # `c_published_projection` reads the shipped HTML and found the words
    # "conformal conic" in the paragraph explaining why they are not on the
    # page — the third time a comment in emitted markup has cost something
    # here, and the first where the comment tripped the check it was written
    # about. A reason belongs in the source that writes the page.
    momethod = f"""
  <div class="sheettext">
    <h2 class="mega">How a cut is made.</h2>
    <p class="lede">A motion is a declared query &mdash; interests, months, a latitude, a
    <a href="/method#discoverability">discoverability</a> floor, a nights ceiling &mdash;
    evaluated against every destination in the Atlas on every build. Nothing is stored
    against a motion and nothing is chosen by hand.</p>
    <p class="note">{motion_tag_note()}</p>
    <p class="note">Coastline and country outlines from
    <a href="/sources">Natural Earth</a>, public domain, drawn on the
    projection <a href="/map">the map</a> publishes. The scoring is
    published in full at <a href="/method">the method</a>.</p>
  </div>"""

    # ── 06 · ASK A BETTER QUESTION ──────────────────────────────────
    moask = f"""
  <!-- `.istart` RATHER THAN A FOURTH CLASS WITH THE SAME BODY. /interests
       introduced this close shape and /beyond-the-obvious already reuses
       it; a third copy of `display: grid; justify-items: start` under a new
       name is the duplicated rule this stylesheet removed 85 of, and the
       first version of this band had one. -->
  <div class="istart">
    <h2 class="mega">Ask a better question.</h2>
    <p class="lede">These {numword(len(data['motions']))} are the questions we found worth
    asking. Discover Mode takes yours &mdash; any combination of the
    {len(data["interests"])} interests, a month, a budget and a pace &mdash; and the
    Planner turns the answer into an order you can travel in.</p>
    <p class="keepgo"><a class="btn" href="/discover">Open Discover Mode</a>
    <a class="storygo" href="/plan">Or build a route &rarr;</a></p>
  </div>"""

    # THE ACTMARK NAMED WHAT THE KICKER UNDER IT ALREADY SAID. Rendered,
    # plate 01 read "01 — EUROPE IN MOTION" and then, eight pixels below,
    # "EUROPE IN MOTION" again — two identical labels stacked, which is the
    # 753-page double-numbering fault in words rather than digits. The
    # actmark names what the plate DRAWS and the kicker names the family.
    PLATES = [("moopen gal", "Same frame, different Europe", moopen,
               "europe-in-motion"),
              ("moq pine", "The question", moq, "the-question"),
              ("mocuts gal", "Twelve cuts", mocuts, "twelve-cuts"),
              ("mooverlap paper", "Not twelve buckets", mooverlap, "overlap"),
              ("momethod pine", "Method", momethod, "method"),
              ("moask gal", "Ask a better question", moask, "ask")]
    body = f"""
{crumbs([("Europe", "/discover"), ("Europe in Motion", None)])}
{plate_sequence(PLATES)}
"""
    return "/europe-in/index.html", page(
        "Europe in Motion", body, path="/europe-in", area="discover",
        accent="territory", hero=True,
        description=f"A dozen ways to cut the continent — each a real query run against all {total} destinations on every build, with the query printed on the page.",
        og=("motion:index", "peaks", "Europe in Motion"),
        ld_blocks=[ld_breadcrumb([("Europe", "/discover"),
                                  ("Europe in Motion", "/europe-in")])],
    )


def discover_page(data):
    """Five plates: the instrument, the result, where it is, in motion, by month.

    THE PAGE WAS A TOOL WEARING A CATALOGUE'S CLOTHES. 6,449 pixels, twelve
    `<h2>` bands, fifteen cards, seventeen outlined chips and two
    cartographies on one screen — and the thing it exists to be, an
    instrument that answers a question, was one figure among the twelve.

    The governing correction is that DISCOVER MUST LEAD WITH DISCOVERY,
    NOT WITH CONTROLS. A visitor should feel an instrument responding to
    their curiosity rather than a catalogue asking them to filter a
    database, so the map IS the first plate and the seventeen things you
    can travel for are set ON it as type, in the ocean where a printed
    atlas puts its key. Choosing one re-lights the continent in place.

    AND THE CHIPS ARE GONE — the whole vocabulary of them. Border, fill,
    radius and shadow each say "separate object, placed here by a system",
    and a page spent all four on seventeen one-word tags and then again on
    twelve months. A tag with a count beside it is a REGISTER ENTRY; set as
    type at reading size it is a thing a person chooses. Nothing about the
    control changed — same buttons, same aria-pressed, same application —
    only that it stopped looking like a database front end.
    """
    n_by_interest = {
        i["slug"]: sum(1 for n in data["cities"].values() if i["slug"] in n["city"]["interests"])
        for i in data["taxonomy"]["interests"]
    }
    # THE SEVENTEEN ARE SERVER-RENDERED NOW, AND THAT IS NOT A DETAIL.
    # They were an empty div the application filled, so a reader with no
    # JavaScript met the page's whole subject as blank space — and the same
    # seventeen were ALSO printed further down as a chip index, so the page
    # carried two interest surfaces that could disagree. One surface: the
    # markup is the index (real links to each tag's own page are kept in the
    # line under it), and the application upgrades it in place.
    interest_words = "".join(
        f'<button type="button" class="pickword" data-interest="{esc(i["slug"])}"'
        f' aria-pressed="false"><span class="pickname">{esc(i["name"])}</span>'
        f'<span class="pickn">{n_by_interest[i["slug"]]}</span></button>'
        for i in sorted(data["taxonomy"]["interests"],
                        key=lambda i: (-n_by_interest[i["slug"]], i["name"]))
    )

    # A MACRO REGION IS THE ONE GROUPING IN THIS ATLAS WITH REAL POLYGONS.
    # A travel region is a set of destinations and is refused a boundary; the
    # Nordics is five whole countries Natural Earth already holds. The cards
    # became rows for the reason every other index here did: a card is the
    # right shape for like things chosen on LOOK, and a region of Europe is
    # chosen on where it is — which is the drawing, so the drawing leads and
    # the glyph is the row's own picture rather than a thumbnail on a panel.
    macro_rows = "".join(
        f'<a class="row macrorow" href="{urls.macro(m)}">'
        f'<div class="rowart">{region_glyph(m["countries"], macro_frame(data, m))}</div>'
        f'<div><h3>{esc(m["name"])}</h3>'
        f'<p class="rowsub">{esc(m["blurb"])}</p></div>'
        # NO TRUNCATED LIST HERE, AND `c_cut_word` CAUGHT IT IN ONE RUN.
        # The first version printed the first three country names with an
        # ellipsis after them — a word cut in half and a count that is not
        # the set's own extent, both of which this repository has already
        # paid for once. The glyph beside the row says WHICH countries by
        # drawing them, and the region's own page names them all.
        f'<p class="rowmeta">{len(m["countries"])}<br>'
        f'<span class="small">countries</span></p></a>'
        for m in data["macros"]
    )

    # A MOTION IS A QUERY, AND IT IS PRINTED AS ONE. Six of the twelve were
    # cards carrying a generated landscape — "a picture of nowhere standing
    # in for a sentence", the finding that rebuilt /europe-in, still shipping
    # two clicks away on the index that introduces the family. All twelve
    # now, because a printed line is cheap enough that there is no longer a
    # reason to stop at six, and the query under each is generated by the
    # function the twelve pages use, so this page cannot state a query the
    # page it links to would not.
    motion_lines = "".join(
        f'<a class="qq" href="/europe-in/{esc(m["slug"])}">'
        f'<h3 class="qqname">{esc(m["name"])}</h3>'
        f'<p class="qqsub">{esc(m["strapline"])}</p>'
        f'<p class="qqquery">{motion_query_words(data, m)}</p>'
        f'<p class="qqn">{sum(1 for cid, x in data["cities"].items() if motion_match(data, m, cid, x)[0])}'
        f' <span>destinations</span></p></a>'
        for m in data["motions"]
    )

    # EACH DOT CARRIES ITS ID, BECAUSE THE DRAWING IS THE INSTRUMENT'S OUTPUT
    # AND NOT ITS DECORATION. The join is the destination id, declared in
    # data/contracts.json because it crosses a boundary: markup one side, an
    # index the other, and a renamed id would light nothing with no error.
    dots = []
    for cid, n in sorted(data["cities"].items()):
        x, y = project(n["city"]["lat"], n["city"]["lon"])
        cls = " advisory" if n["country"].get("advisory") else ""
        dots.append(f'<circle class="herodot{cls}" data-city="{esc(cid)}" '
                    f'cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
    quiet = sum(1 for n in data["cities"].values() if n["city"].get("quiet"))

    # THE COUNT GOES UNDER THE MAP, NOT OVER THE LIST. What the MAP shows
    # and what the LIST shows are two claims, and this is the first: the
    # drawing re-lights and the sentence under it says how much of Europe is
    # still on. It also fills the one real void this plate had — the key
    # column runs taller than the drawing beside it, so 450 pixels of the
    # right-hand side were empty page, measured on the built page.
    #
    # And plate 02 cannot be empty at rest, which is where the application
    # used to leave it. "Present but empty says we have this and then does
    # not" — so at rest the result plate says what it IS showing, which is
    # everything.
    # NO ARCH ON THIS ONE, AND THE RULE ALREADY SAID SO.
    # `docs/signature-moments.md` records where the door is CORRECTLY absent
    # and names /map first: it is the instrument rather than a picture of
    # somewhere. /discover draws the same instrument and had been carrying an
    # aperture anyway — a picture's frame around a tool. Full-bleed, and the
    # plate's ground is `--map-sea` itself, so the drawing has no edge on the
    # left: it simply continues into the page and the key is set in its
    # ocean. That is the difference between a map ON a plate and a map that
    # IS one.
    # AND THE GROUND BEYOND THE ATLAS IS NOT DRAWN HERE, WHICH IS A
    # MEASUREMENT RATHER THAN A PREFERENCE. `landmass` returns the context
    # land first — every landmass in a box that contains Europe, clipped to
    # that box — and it is a HERO device: *Europe is not an island*, and the
    # graphite it is drawn on absorbs its straight edges completely. /map and
    # /discover keep it for exactly that reason, and the same slab on the
    # same projection is invisible there: measured on /map's own pixels, the
    # dusk over 52°E is near-black and Iran and Iraq are gone.
    # This band is the one light drawing that shows the whole eastern cut
    # inside its own frame with open water beyond it, and `--atlas-far`
    # (#C3BFB2) is DARKER than the water (#DDE8E7) rather than lighter — so
    # the fragment came out as a warm slab with three straight edges sitting
    # in the sea south-east of Baku, probed and named as Iran and Iraq
    # clipped at 52°E. The wide fade hides it and takes the ground out from
    # under Baku and Tbilisi with it, which is the fault `dusk_reach` exists
    # to stop and is why every caller passes it. So the layer that has no
    # claim to make here is the one that goes: this drawing's subject is 313
    # destinations and the six it refuses, and nothing outside the atlas is
    # part of that sentence.
    dctx, dland = geo.landmass(MAPPROJ, (0, 0, MAP_W, MAP_H))
    mapsvg = (f'<svg viewBox="0 0 {MAP_W} {MAP_H}" aria-hidden="true">'
              f'<rect x="0" y="0" width="{MAP_W}" height="{MAP_H}" class="archground"/>'
              f'{dctx}{dland}{cut_fade("disc", MAP_W, MAP_H, dusk_reach())}'
              f'{"".join(dots)}</svg>')

    # ── THE PHOTOGRAPHIC RESPONSE ────────────────────────────────────
    # A MAP ANSWERS *WHERE* AND A PHOTOGRAPH ANSWERS *WHAT IT IS LIKE*, and
    # this page had only the first. The instrument re-lights the continent
    # and then hands the reader a list of names: true, checkable, and no
    # answer at all to the question the plate above it asks.
    #
    # ONE PER MACRO REGION, IN THE ATLAS'S OWN ORDER, AND THE COUNT IS THE
    # SET'S OWN EXTENT. The first version walked the destinations sorted by
    # id and took the first photographed one in each macro, which put all
    # seven tiles in countries A to E — a row that reads as a spread across
    # the continent while being a spread across one end of the alphabet.
    # The macros are walked in the taxonomy's own order now, so the row
    # sweeps the continent the way /countries does, and the lede states how
    # many of the nine corners hold a photograph TODAY rather than implying
    # all of them do: a number that is not the set's own extent reads as
    # one, which is this atlas's own finding about /europe-in.
    #
    # AND THE TILES ANSWER THE INSTRUMENT. Each carries `data-city`, the
    # same join the dots use, so a destination that falls out of the chosen
    # set goes QUIET rather than away — the map's own rule, applied on the
    # band that exists to be the picture the map cannot draw. Nothing is
    # added to the contract: `city.id` is already declared for the dots.
    images = data.get("images") or {}
    first_in_macro = {}
    for cid, e in sorted(data["cities"].items()):
        if ("city:" + cid) not in images:
            continue
        if (e["country"].get("advisory") or {}).get("level"):
            continue
        first_in_macro.setdefault(e["country"].get("macro_slug"), (cid, e))
    macros = data["taxonomy"]["macros"]
    shots = [first_in_macro[m["slug"]] for m in macros
             if m["slug"] in first_in_macro]

    def _mostile(cid, e):
        return (f'<a class="mos" data-city="{esc(cid)}" '
                f'href="{urls.city(e["country"], e["region"], e["city"])}">'
                f'{picture(images, "city:" + cid, w=1000, h=1000, credit=False, alt=images["city:" + cid]["alt"], sizes="(min-width: 62rem) 30vw, 92vw")}'
                f'<span class="moscopy">'
                f'<span class="moswhere">{esc(e["country"]["name"])}</span>'
                f'<span class="mosname">{esc(e["city"]["name"])}</span></span></a>')

    # THE LEAD IS A SIBLING OF THE REST RATHER THAN A CELL AMONG THEM,
    # because a dominant tile that is a cell has to be told how many rows
    # to span and the count is data. See `.moswrap` in the stylesheet.
    mosaic = (_mostile(*shots[0])
              + '<div class="mosrest">'
              + "".join(_mostile(cid, e) for cid, e in shots[1:])
              + '</div>') if shots else ""

    body = f"""
{crumbs([("Europe", "/discover"), ("Discover", None)])}

<section class="sheet sheet-ask sheet-paper sheet-white" id="discover-open">
  {actmark(1, "Discover")}
  <div class="asktext">
    <h1 class="mega">What are you <br><em class="lit">looking for?</em></h1>
    <p class="lede">Do not begin with a destination. Begin with a curiosity — a landscape, a
    season, a culture, a road — and let the continent answer. Nothing here is submitted:
    the whole Atlas is already in your browser.</p>
    {head_extent([(len(data['cities']), 'destinations'),
                  (len(data['countries']), 'countries'),
                  (len(data['taxonomy']['interests']), 'things to travel for')])}
  </div>
</section>

<section class="sheet sheet-instrument" id="discover-mode">
  {actmark(2, "The instrument")}
  <div class="instrkey">
    <div class="pagehead instrument">
      <p class="kicker">The European instrument</p>
      <h2>Let Europe answer.</h2>
    </div>
    <p class="keyhead">Say what you are travelling for.</p>
    <div class="picks" id="discover-interests">{interest_words}</div>
    <p class="keynote">Pick as many as you like. The continent re-lights as you choose.
    <a href="/interests">Every tag also has its own page</a>.</p>
  </div>

  <div class="instrstage">
    <a class="instrmap" data-role="instrument" href="/map"
       id="discover-map" aria-label="Map of all {len(data['cities'])} places">
      {mapsvg}
      <span class="instrcap">Coastline from Natural Earth, public domain.
      Open the full map, with layers →</span>
    </a>
    <p class="lede instrcount" id="discover-count" aria-live="polite">Choose what you are
    travelling for. Europe will narrow itself.</p>
    <div class="instrfields">
      <div class="field">
        <label for="discover-month">Travelling in</label>
        <select id="discover-month"><option value="">Any month</option></select>
      </div>
      <div class="field">
        <label for="discover-budget">Spending band</label>
        <select id="discover-budget"><option value="">Any budget</option></select>
      </div>
      <div class="field">
        <label class="inlinecheck"><input type="checkbox" id="discover-quiet">
        Off the obvious circuit</label>
      </div>
      <div class="field">
        <label class="inlinecheck"><input type="checkbox" id="discover-rail">
        Reachable slowly, by rail</label>
      </div>
      <p class="small"><button type="button" class="linkish" id="discover-clear">Clear
      everything</button></p>
    </div>
  </div>
</section>

<section class="sheet sheet-response sheet-paper" id="discover-response">
  {actmark(3, "Your Europe")}
  <div class="sheettext">
    <h2 class="mega">Start here.</h2>
    <p class="lede">One destination from each corner of the continent &mdash;
    {len(shots)} of the {len(macros)} this atlas divides Europe into, because a corner
    appears here only once it holds a licensed photograph. What the map says in position,
    these say in weather and light.</p>
  </div>
  <div class="moswrap" id="discover-shots">{mosaic}</div>
</section>

<section class="sheet sheet-result sheet-paper sheet-white" id="discover-result">
  {actmark(4, "The result")}
  <div class="sheettext">
    <h2 class="mega">What is left.</h2>
    <p class="lede">Ranked by the terms you chose and nothing else. Each row says why it is
    on the list — the actual terms that fired, not "recommended for you".</p>
    {golink("/method", "How the ranking works")}
  </div>
  <div class="resultside" id="discover-results"></div>
</section>

{constel_defs()}

<section class="sheet sheet-where sheet-paper" id="discover-where">
  {actmark(5, "By where it is")}
  <div class="sheettext">
    <h2 class="mega">Europe, by region.</h2>
    <p class="lede">Grouped by shared coast, shared mountain range and shared history rather
    than by alphabet. Each one draws its own member countries, so a region is a shape before
    it is a name.</p>
    {golink("/countries", "Every country, A to Z")}
  </div>
  <div class="rows whererows">{macro_rows}</div>
</section>

<section class="sheet sheet-motion sheet-pine" id="discover-motion">
  {actmark(6, "Europe in questions")}
  <div class="sheettext">
    <h2 class="mega">Sometimes you know <br>the question before <br>you know the place.</h2>
    <p class="lede">Each one is a query run against every destination on every build, not a
    list somebody chose. The query is printed under the name, and it is the same query the
    page itself prints.</p>
    {golink("/europe-in", "Open the twelve")}
  </div>
  <div class="qqlist">{motion_lines}</div>
</section>

<section class="sheet sheet-month sheet-paper sheet-white" id="discover-month-band">
  {actmark(7, "Europe in time")}
  <div class="sheettext">
    <h2 class="mega">And the year itself.</h2>
    <p class="lede">What is on, and which countries are in their quieter shoulder — which is
    usually where you should be going. The two disagree, and the disagreement is the point.</p>
    {golink("/events", "The whole European year")}
  </div>
  <div class="monthside">{year_band(data)}</div>
  <div class="note qualify">
    <h3 class="mini">What "off the obvious circuit" means, exactly</h3>
    <p>It is a computed score, not a mood. A place scores higher for not being a capital, for
    being marked quiet by an editor who knows the region, for having no curated route through
    it, for not being tagged with the things a continent is famous for, and for sitting in a
    country the Atlas has written thinly. Every term and its points are
    <a href="/method#discoverability">published on the method page</a>.</p>
    <p class="small">It measures obscurity <em>within this Atlas</em> — which is a smaller and
    truer claim than "undiscovered". We hold no visitor numbers for anywhere, and a proxy for
    crowding presented as evidence is the thing this project exists not to do.
    {quiet} places carry the editorial quiet tag; <a href="/beyond-the-obvious">Beyond the
    obvious</a> collects them.</p>
  </div>
</section>

<section class="sheet sheet-keep sheet-paper sheet-white" id="discover-end">
  {actmark(8, "Keep looking")}
  <div class="sheettext">
    <h2 class="mega">Keep <br><em class="lit">looking.</em></h2>
    <p class="lede">There is always another road, another city, another landscape, another
    door. {len(data['cities'])} of them are written up here, and the atlas is a third
    finished.</p>
    {golink("/beyond-the-obvious", "Beyond the obvious")}
  </div>
</section>
"""
    return "/discover/index.html", page(
        "Discover Europe", body, path="/discover", area="discover",
        description=f"Say what you are travelling for and {len(data['cities'])} places across {len(data['countries'])} countries narrow themselves — each one saying why it is on the list.",
        scripts=["/assets/js/discover.js"], hero=True,
        # INTELLIGENCE — filter intelligence — Discover Mode is a tool, not a browse surface. /discover/<macro> stays editorial
        world="intelligence"
    )


# ── the pages the footer promises ─────────────────────────────────────

def _plain(title, kicker, lede, blocks, *, path, description, crumb):
    body = f"""
{crumbs([("Europe", "/discover"), (crumb, None)])}
<div class="pagehead">
  <p class="kicker">{esc(kicker)}</p>
  <h1>{esc(title)}</h1>
  <p class="lede">{esc(lede)}</p>
</div>
{blocks}
"""
    return f"{path}/index.html", page(title, body, path=path, area=None, description=description)


PRELAUNCH = """<div class="note">
  <h2 class="mini">This is a pre-launch draft, and it says so rather than pretending</h2>
  <p>There is no incorporated company behind EuropeDoor yet, so there is no legal person to
  be bound by this document and no data controller to be accountable under it. What follows
  is the position we intend to take, published early so it can be argued with — it is not a
  contract, and it will be reviewed by a lawyer and re-issued in the name of a real entity
  before anything on this site collects a payment or a personal detail.</p>
</div>"""


def privacy_page(data):
    blocks = PRELAUNCH + """
<div class="split">
  <div>
    <h2>What we collect today: nothing</h2>
    <p>No account system, no sign-in, no email capture, no contact form, no comments. The
    Journey Planner runs in your browser and the plan is never sent anywhere. My Europe
    stores your saved places in your own browser's local storage, which we cannot read.</p>
    <p>There is no third-party analytics script on this site, no advertising network, no
    social tracking pixel, no embedded video, no web font loaded from someone else's server
    and no map tile provider. Every byte served comes from this domain. You can verify that
    in your browser's network tab in about ten seconds, which is a better assurance than this
    paragraph.</p>

    <h2>What a server necessarily sees</h2>
    <p>Serving a page means the host receives the request: an IP address, a user agent, the
    path, a timestamp. That is true of every website and cannot be opted out of by us or by
    you. Our intent is that these logs are kept short and never joined to anything.</p>

    <h2>What will change, and what will not</h2>
    <ul class="stack">
      <li><strong>Accounts</strong> will need an email address and a password hash, a lawful
      basis, a retention period and working access, export and erasure. None of that exists
      yet, which is the reason accounts do not.</li>
      <li><strong>Analytics</strong>, when it exists, will use a session identifier that
      rotates daily and is never joined to a person, with no cross-site identifier. The event
      list is published in the specification in the repository before any of it is collected.</li>
      <li><strong>Business accounts</strong> will hold company details, which are commercial
      rather than personal data for the most part — but the named contact is a person.</li>
      <li><strong>We will not</strong> sell personal data, run behavioural advertising, or
      load a third-party tracker. That is a product decision, not a legal minimum.</li>
    </ul>

    <h2>Your rights under the GDPR</h2>
    <p>Access, rectification, erasure, restriction, portability and objection. They apply to
    a controller; there is not one yet. When there is, this page will name it, give an
    address, and give a working route to exercise each right rather than an invitation to
    email a mailbox nobody reads.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Cookies</h2>
    <p>This site sets none. Not a consent banner's worth, not one. <a href="/cookies">The
    detail →</a></p>
    <h2 class="mini">Local storage</h2>
    <p>My Europe uses <code>localStorage</code> under this origin. It never leaves your
    device and clearing site data removes it. <a href="/my-europe">Your list →</a></p>
    <h2 class="mini">Children</h2>
    <p>The site is not directed at children and collects nothing from anyone.</p>
  </aside>
</div>"""
    return _plain("Privacy", "Privacy", "What EuropeDoor collects: nothing. What it will collect, and under what conditions.",
                  blocks, path="/privacy", crumb="Privacy",
                  description="EuropeDoor collects no personal data, sets no cookies and loads no third-party scripts. What that means, and what will change when accounts exist.")


def cookies_page(data):
    blocks = PRELAUNCH + """
<div class="split">
  <div>
    <h2>This site sets no cookies</h2>
    <p>Not analytics cookies, not preference cookies, not a consent cookie to remember that
    you dismissed a consent banner. There is no banner because there is nothing to consent
    to, and a banner that appears anyway is a dark pattern with a legal costume on.</p>

    <h2>What is used instead</h2>
    <p><code>localStorage</code>, for one thing only: the list of places you save in My
    Europe. It is stored by your browser under this domain, it is never transmitted, and
    it is not a cookie — it is not attached to requests and cannot be read by anyone else.
    Clearing site data deletes it, and there is no copy anywhere.</p>

    <h2>What would require a banner</h2>
    <ul class="stack">
      <li>Any analytics that stores or reads an identifier on your device.</li>
      <li>Embedded third-party content — a video, a map tile provider, a social widget.</li>
      <li>Advertising of any kind, which we have refused outright rather than deferred.</li>
    </ul>
    <p>If any of those ever ship, this page changes first, and the banner is a real choice
    with a working reject button rather than a wall.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Verify it</h2>
    <p>Open your browser's developer tools, look at Application → Cookies for this domain,
    and confirm the list is empty. That is worth more than this page.</p>
  </aside>
</div>"""
    return _plain("Cookies", "Cookies", "There are none. Here is what is used instead, and what would have to change.",
                  blocks, path="/cookies", crumb="Cookies",
                  description="EuropeDoor sets no cookies at all — no analytics, no preferences, no consent cookie. What it uses instead and what would require a banner.")


def terms_page(data):
    blocks = PRELAUNCH + """
<div class="split">
  <div>
    <h2>What this site is</h2>
    <p>An editorial reference work about travel in Europe, published free of charge. It is
    not a travel agent, not a tour operator, not a booking service and not a financial
    service. Nothing on it constitutes an offer, and no contract can be formed here because
    there is nothing to buy.</p>

    <h2>Accuracy, stated plainly</h2>
    <p>The dataset behind this site was written editorially and has not been through a
    source-by-source verification pass. <a href="/sources/freshness">The freshness board</a>
    publishes, per country, when a person last checked the practical facts — and today the
    answer for most of them is "never". Costs are estimates from published bands, not quotes.
    Distances are straight lines. Scores are computed from our own tags by
    <a href="/method">a published formula</a>.</p>
    <p><strong>Check the official source</strong> for anything that matters: your government's
    travel advice, the destination's border authority, and the operator's own site for
    anything you intend to turn up for.</p>

    <h2>What you may do with it</h2>
    <ul class="stack">
      <li>Read it, quote it with attribution, link to it, and print it for your own trip.</li>
      <li>Not scrape it wholesale to reconstitute the dataset elsewhere. The writing is the
      work; the structure is the product.</li>
      <li>Not present it as your own, or as verified, or as advice.</li>
    </ul>

    <h2>Liability</h2>
    <p>To the extent the law allows once there is an entity to be liable, this material is
    provided as it is. Travel decisions are yours. Where a page and an official source
    disagree, the official source is right and we would like to be told.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Corrections</h2>
    <p>Wanted, including blunt ones. <a href="/sources">How to tell us →</a></p>
    <h2 class="mini">Not yet in force</h2>
    <p>These terms bind nobody until there is a company to be bound. See
    <a href="/about">about</a>.</p>
  </aside>
</div>"""
    return _plain("Terms", "Terms of use", "What this site is, what it is not, and what its facts are worth.",
                  blocks, path="/terms", crumb="Terms",
                  description="EuropeDoor's terms: an editorial reference, not a booking service; unverified facts marked as such; and no contract until there is a company.")


def accessibility_page(data):
    blocks = """
<div class="split">
  <div>
    <h2>The target</h2>
    <p>WCAG 2.2 Level AA, and the honest position is that we test a subset of it
    automatically on every build rather than claiming conformance we have not audited.</p>

    <h2>What is checked automatically, on every page</h2>
    <ul class="stack">
      <li>Every page has one <code>h1</code>, and headings descend without skipping a level.</li>
      <li>Every page has a skip link, a <code>main</code> landmark and a language declared.</li>
      <li>Body text and interface text meet the 4.5:1 contrast ratio in both the light and
      dark palettes, computed from the tokens rather than eyeballed.</li>
      <li>Every form control has a label, every link has discernible text, and every
      generated illustration carries a role and an accessible name.</li>
      <li>Nothing relies on colour alone to convey state.</li>
      <li>No page overflows horizontally at 390 CSS pixels, tested in a real browser.</li>
      <li><code>prefers-reduced-motion</code> disables every transition and hover movement.</li>
    </ul>

    <h2>What is not yet done</h2>
    <ul class="stack">
      <li>No audit with a screen reader by a person who uses one daily. That is the gap that
      matters most and cannot be automated away.</li>
      <li>No keyboard-only walkthrough of the planner by an independent tester.</li>
      <li>No accessibility information about the <em>places themselves</em> — step-free
      access, hearing loops, accessible toilets. The planner already tells you it cannot take
      account of accessibility needs; the honest fix is data we do not have yet, and inventing
      it would be worse than the gap.</li>
    </ul>

    <h2>If something here excludes you</h2>
    <p>That is a defect, not a preference, and we would rather hear it bluntly.
    <a href="/contact">How to reach us →</a></p>
  </div>
  <aside class="rail">
    <h2 class="mini">Why no photographs</h2>
    <p>Every illustration on this site is generated from the place's own name and carries a
    text alternative automatically. There is no library of stock images with missing alt
    text, because there is no library.</p>
    <h2 class="mini">Tested in a browser</h2>
    <p>The accessibility checks run in Chromium on every build, not as a checklist somebody
    ticks. If one fails, the build fails.</p>
  </aside>
</div>"""
    return _plain("Accessibility", "Accessibility", "The target is WCAG 2.2 AA. Here is what is enforced on every build, and what is still missing.",
                  blocks, path="/accessibility", crumb="Accessibility",
                  description="EuropeDoor's accessibility position: what is automatically enforced on every build, what has not been audited, and the place data that is missing.")


def help_page(data):
    # "FIVE COUNTRIES HAVE BEEN TAKEN TO DEPTH SO FAR" WAS TYPED, AND THE
    # LINK BESIDE IT PROMISED SOMETHING /countries DOES NOT DO.
    #
    # It was also true, which is how a typed number survives: Italy, Norway,
    # Spain, France and Greece each carry between 67 and 86 recorded
    # destinations, places and things to do, and the sixth country carries
    # 28. That gap is the real answer to "why is my country's page thin" and
    # the sentence was standing in front of it — and "which is which" pointed
    # at an index that lists fifty countries and says nothing about depth.
    #
    # So the answer names them, from the count, with the median beside it.
    # This is a ranking of OUR OWN COVERAGE and not of places, which is the
    # one kind this atlas does publish: docs/content-report.md ranks the same
    # thing from the other end.
    import statistics
    held = sorted(
        ((sum(len(r["cities"]) for r in c["regions"])
          + sum(len(t.get("places", [])) for r in c["regions"] for t in r["cities"])
          + sum(len(t.get("experiences", [])) for r in c["regions"] for t in r["cities"])),
         c["name"])
        for c in data["countries"].values())
    top = [nm for _, nm in held[-5:]][::-1]
    lo, hi = held[-5][0], held[-1][0]
    mid = int(statistics.median(n for n, _ in held))
    depth_answer = (
        f'{and_list([esc(t) for t in top])} are written deepest: between {lo} and '
        f'{hi} recorded destinations, places and things to do each, where the '
        f'median country holds {mid}. The rest are at a solid first pass, and '
        f'<a href="/sources/freshness">the freshness board</a> says when each '
        f"country's practical facts were last checked.")
    cx = data["taxonomy"].get("currencies", {})
    rates_note = (f"Indicative, recorded by hand on {esc(cx.get('as_of', '—'))}, covering "
                  f"{len(cx.get('rates', {}))} currencies. Rounded hard on purpose.")
    blocks = f"""
<div class="split">
  <div>
    <h2>How to use this site</h2>
    <ul class="stack">
      <li><strong>If you know where you are going</strong> — search, or go straight to
      <a href="/countries">countries</a>. Every place is four clicks from the homepage.</li>
      <li><strong>If you know what you want but not where</strong> —
      <a href="/discover">discover</a> sorts Europe by what you travel for, and
      <a href="/themes">themes</a> ignore borders entirely.</li>
      <li><strong>If you know when you are free</strong> — <a href="/events">the European
      year</a> has a page per month that also says where is good in it.</li>
      <li><strong>If you have days and a budget</strong> — <a href="/plan">the planner</a>
      takes a sentence or a form and returns a route with a cost estimate.</li>
    </ul>

    <h2>Common questions</h2>
    <h3>Can I book anything here?</h3>
    <p>No, and not by accident: there is no payment surface anywhere on the site and no
    company behind it yet. <a href="/how-it-works">What is built, designed and blocked →</a></p>
    <h3>How accurate is this?</h3>
    <p>It is a considered editorial first draft that has not been verified source by source.
    <a href="/sources/freshness">The board says so per country →</a></p>
    <h3>Why are there no photographs?</h3>
    <p>Because none is licensed yet, and the register that would hold one is empty. What you
    see instead is geography: a country drawn from its own outline, a journey drawn as its
    route, a tag drawn as every destination carrying it. Where there is nothing real to draw,
    the illustration is generated from the place's own name — no licence to expire, no stock
    library, and no risk of publishing somebody's holiday photograph.
    <a href="/sources">Where the geography comes from →</a></p>
    <h3 id="currency">Why are the local-currency figures marked indicative?</h3>
    <p>Because they are. The rates are recorded by hand, dated on this page, rounded hard, and
    not refreshed automatically. They exist so that "€90 a day" in Norway means something to
    you before you arrive — not so that you can budget to the krone. Your bank's rate will be
    worse than the one used here, and the date will keep getting older until there is a live
    feed and somebody paying for it.</p>
    <h3>Where did my saved places go?</h3>
    <p>They live in the browser you saved them in and nowhere else. A different browser, a
    private window or cleared site data means an empty list — which is the cost of not having
    an account system, and we think it is the right trade for now.</p>
    <h3>Why is my country's page thin?</h3>
    <p>{depth_answer}</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Currency rates</h2>
    <p>{rates_note}</p>
    <h2 class="mini">Something is wrong</h2>
    <p>Corrections are wanted. <a href="/sources">Sources and corrections →</a></p>
    <h2 class="mini">You run a business here</h2>
    <p><a href="/for-businesses">How listings work →</a></p>
  </aside>
</div>"""
    return _plain("Help", "Help", "How to use the site, and the questions people actually ask.",
                  blocks, path="/help", crumb="Help",
                  description="How to use EuropeDoor: finding a place, planning a journey, what the facts are worth, and where saved places live.")


def contact_page(data):
    blocks = PRELAUNCH + """
<div class="split">
  <div>
    <h2>There is no contact form, on purpose</h2>
    <p>A form collects a name, an email address and a message. That is personal data, and
    holding it requires a controller, a lawful basis, a retention period and a published
    privacy notice. None of those exist yet, so collecting it would be the first thing on
    this site to break its own rules.</p>

    <h2>What to do instead</h2>
    <ul class="stack">
      <li><strong>A correction</strong> — a wrong fact, a closed museum, a price that moved.
      If you hold the repository, its issue tracker is the channel and every correction is
      public that way, which is better than an inbox. If you do not, there is no route yet:
      this is the one thing on the list with no answer, and naming a channel a reader cannot
      reach would be worse than saying so.</li>
      <li><strong>You run a business we list, or should</strong> — read
      <a href="/for-businesses">how listings work</a> first. Applications are not open, and
      the page says why.</li>
      <li><strong>You are a tourism organisation</strong> —
      <a href="/for-tourism-boards">what we would and would not sell you</a>.</li>
      <li><strong>Press</strong> — everything we would say is already written down:
      <a href="/about">about</a>, <a href="/how-it-works">how it works</a>,
      <a href="/method">the scoring method</a>.</li>
    </ul>

    <h2>What arrives with the company</h2>
    <p>A named address, a real inbox with a stated response time, and a form that only asks
    for what it needs. In that order.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Why this reads oddly</h2>
    <p>Most sites put a form here whether or not anyone reads it. This is what it looks like
    when a product refuses to collect something it cannot yet look after.</p>
  </aside>
</div>"""
    return _plain("Contact", "Contact", "No form, and the reason is the same reason there are no accounts.",
                  blocks, path="/contact", crumb="Contact",
                  description="How to reach EuropeDoor before it has a company: corrections, business listings, tourism organisations and press.")


def tourism_boards_page(data):
    counts = {}
    for n in data["cities"].values():
        counts[n["country"]["name"]] = counts.get(n["country"]["name"], 0) + 1
    body_rows = "".join(
        f"""<div class="row"><div><h3>{esc(a)}</h3><p class="rowsub">{esc(b)}</p></div>
        <p class="rowmeta">{esc(c)}</p></div>"""
        for a, b, c in [
            ("Destination profile", "A verified, editorially written presence for a region — written by us, corrected by you, never ghostwritten by you.", "would build"),
            ("Seasonality intelligence", "Which months travellers plan for, by interest, for your region against its neighbours.", "would build"),
            ("Search and planner demand", "What people ask for that your region answers, including the requests we could not fulfil.", "would build"),
            ("Campaign placement", "Time-boxed, labelled promotion on directory and discovery surfaces.", "would build"),
            ("Ranking in the Atlas", "Editorial position, the Journey Planner, curated journeys, the Experience Score.", "never for sale"),
        ]
    )
    blocks = f"""
<div class="split">
  <div>
    <h2>What we would build for you</h2>
    <div class="rows">{body_rows}</div>

    <h2 class="mt7">The line, before the conversation rather than after</h2>
    <p>A tourism board's money can buy attention. It cannot buy the impression of independent
    editorial judgement, because that impression is the only thing we have to sell to anybody
    else. So: campaigns are labelled, time-boxed and confined to directory and discovery
    surfaces. The <a href="/method">Experience Score</a> is computed from tags by a published
    formula and has no field a payment could touch. The <a href="/plan">Journey Planner</a>
    scores fit and distance, and there is nothing in its index that could carry a boost.</p>
    <p>If that makes us less useful to you than a publisher who will sell the front page, that
    is the correct outcome for both of us.</p>

    <h2 class="mt7">What exists today</h2>
    <p>{len(data['countries'])} countries and {len(data['cities'])} destinations, written
    editorially, with the verification status of each country published on
    <a href="/sources/freshness">the freshness board</a>. No traffic to report yet, and we
    will not quote figures we do not have — which is the same reason the intelligence product
    is described above in the conditional.</p>
  </div>
  <aside class="rail">
    <h2 class="mini">Where your region already is</h2>
    <p>Every country has a page, every travel region has a page, and every destination links
    to the region and country above it. <a href="/countries">Find yours →</a></p>
    <h2 class="mini">Corrections first</h2>
    <p>If something about your region is wrong here, that is worth more to us than a campaign
    and costs you nothing. <a href="/sources">Tell us →</a></p>
  </aside>
</div>"""
    return _plain("For tourism boards", "For tourism organisations",
                  "What a national board, region or municipality could buy here — and the one thing that is not for sale.",
                  blocks, path="/for-tourism-boards", crumb="For tourism boards",
                  description="What EuropeDoor would offer tourism boards: destination profiles, seasonality and demand intelligence, labelled campaigns — and why editorial ranking is never for sale.")
