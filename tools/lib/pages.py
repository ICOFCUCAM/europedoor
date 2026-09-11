"""Every page EuropeDoor publishes.

Each builder returns (path, html). The build writes them; nothing here
touches the filesystem, so a page can be rendered and asserted against in a
test without a build directory existing.
"""

from __future__ import annotations

import hashlib
import math
import re
from urllib.parse import quote

from . import cartography
from . import geo
from . import stay as staylib
from . import urls
from .render import (LD_PUBLISHER, SITE_NAME, SITE_TAGLINE, arch_rim, card, chips, crumbs,
                     esc, factlist, grid, n_of,
                     jsondata, ld_breadcrumb, ld_place, ld_within, motif_for,
                     page, photo, picture, plate, section, arch_clip, arch_edge)
from .score import city_scores, country_scores, discoverability

HOME = ("Europe", "/discover")

# What a consumer of the public API may do with it. Stated in the document
# itself rather than only on a page, because a JSON file gets copied and the
# page it was linked from does not travel with it.
API_LICENCE = {
    "terms": "https://europedoor.com/terms",
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


def dusk_stops(lo=0.0, hi=1.0):
    """Smoothstep in five stops, as opacity only — the colour is the caller's.

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
        v = t * t * (3.0 - 2.0 * t)
        out.append(f'<stop offset="{lo + (hi - lo) * t:.4f}" '
                   f'stop-opacity="{v:.3f}"/>')
    return "".join(out)


# ── how far a data cut may reach ──────────────────────────────────────

DUSK_CEILING = 0.80
_DUSK_REACH = {}


def dusk_reach(data):
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


def cut_fade(idprefix, w, h, reach=None):
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
    eb, ea, sb, sa = reach or (330.0, 30.0, 130.0, 4.0)
    ex1, ey1, ex2, ey2 = cut_band(70.0, 40.0, 52.0, eb, ea)
    ax, ay = MAPPROJ.apex()
    r33 = MAPPROJ.parallel_radius(33.0)
    foot0, foot1 = (r33 - sb) / r33, (r33 - sa) / r33
    return (
        f'<defs>'
        f'<linearGradient id="{idprefix}edge" gradientUnits="userSpaceOnUse"'
        f' x1="{ex1:.1f}" y1="{ey1:.1f}" x2="{ex2:.1f}" y2="{ey2:.1f}">'
        f'{dusk_stops()}</linearGradient>'
        f'<radialGradient id="{idprefix}foot" gradientUnits="userSpaceOnUse"'
        f' cx="{ax:.1f}" cy="{ay:.1f}" r="{r33:.1f}">'
        f'{dusk_stops(foot0, foot1)}</radialGradient>'
        f'</defs>'
        f'<g class="mapcut" aria-hidden="true">'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="url(#{idprefix}edge)"/>'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="url(#{idprefix}foot)"/>'
        f'</g>'
    )


def heroeurope(data):
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
    ctx, land = geo.landmass(MAPPROJ, view, doc=doc,
                             thin_units=1.8, min_units=6.0,
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

    # WHOSE GROUND IS THIS? A name may run out over the SEA — a printed atlas
    # does that with Norway and with Chile — and may never run over a
    # neighbour. Keeping the name's middle on its own country was not enough
    # by half: SWITZERLAND ran from Bordeaux to Munich correctly centred,
    # CROATIA lay across Bosnia, AUSTRIA across Hungary, GREECE into Türkiye.
    # A bounding box is not a country either — Croatia's box has its middle in
    # Bosnia — so the test is the real polygon.
    #
    # Every country's rings are indexed once, with a bounding box in front of
    # each so that almost every sample is rejected by four comparisons.
    def _rings_of(d):
        out = []
        for sub in d.split("Z"):
            pts = [(float(a), float(b))
                   for a, b in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", sub)]
            if len(pts) >= 3:
                xs = [q[0] for q in pts]
                ys = [q[1] for q in pts]
                out.append(((min(xs), min(ys), max(xs), max(ys)), pts))
        return out

    def _inside(pts, x, y):
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

    shapes = []
    for _m in re.finditer(r'<path d="([^"]*)"><title>([^<]*)</title></path>',
                          land):
        shapes.append(_rings_of(_m.group(1)))

    def _crosses(mine, x, y):
        for k, rings in enumerate(shapes):
            if k == mine:
                continue
            for bb_, pts in rings:
                if not (bb_[0] <= x <= bb_[2] and bb_[1] <= y <= bb_[3]):
                    continue
                if _inside(pts, x, y):
                    return True
        return False

    # AND "NOT ONE PIXEL ON A NEIGHBOUR" WAS THE WRONG RULE, MEASURED.
    #
    # Forbidding every crossing left ten names — and it dropped GERMANY,
    # POLAND, SWEDEN, NORWAY, FINLAND and UNITED KINGDOM, which are exactly
    # the countries a reader orients by. A printed atlas lets the ends of a
    # name touch a neighbour; what it never does is lay a name ACROSS one.
    # So the test is a fraction rather than a flag: ten samples along the
    # name, at most two of them on somebody else's ground.
    #
    # It is tried at zero first and at two only if nothing fits, which makes
    # the four positions and nine anchors choose the cleanest placement
    # available rather than the first tolerable one — the routine returns the
    # first that fits, so the tolerance is the pass and not a score.
    CROSS_OK = 2

    def _crossings(mine, x0, y0, w0, h0):
        mid_y = y0 + h0 / 2.0
        cap_y = y0 + h0 * 0.34
        n_ = 0
        for i in range(7):
            if _crosses(mine, x0 + w0 * i / 6.0, mid_y):
                n_ += 1
        for i in range(3):
            if _crosses(mine, x0 + w0 * (0.15 + 0.35 * i), cap_y):
                n_ += 1
        return n_

    def _own(mine, x, y):
        for bb_, pts in shapes[mine]:
            if (bb_[0] <= x <= bb_[2] and bb_[1] <= y <= bb_[3]
                    and _inside(pts, x, y)):
                return True
        return False

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
    order_ = []
    for idx, m in enumerate(re.finditer(
            r'<path d="([^"]*)"><title>([^<]*)</title></path>', land)):
        spot = _dpath(m.group(1))
        if spot:
            order_.append(((spot[3][2] - spot[3][0]) * (spot[3][3] - spot[3][1]),
                           idx, m, spot))
    order_.sort(key=lambda t: -t[0])
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
        f'<defs><linearGradient id="heroedge" gradientUnits="userSpaceOnUse"'
        f' x1="{ex1:.1f}" y1="{ey1:.1f}" x2="{ex2:.1f}" y2="{ey2:.1f}">'
        f'{_dusk()}</linearGradient>'
        f'<radialGradient id="herofootg" gradientUnits="userSpaceOnUse"'
        f' cx="{ax:.1f}" cy="{ay:.1f}" r="{r33:.1f}">'
        f'{_dusk(foot0, foot1)}</radialGradient>'


        # The mask that keeps the dusk on the land and off the water. The
        # Caspian, the Aral and the Sea of Azov are the far-eastern water this
        # picture has, and an unmasked overlay would paint all three graphite.
        f'<mask id="herodim" maskUnits="userSpaceOnUse"'
        f' x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}" height="{vh:.0f}">'
        # WIDER IN THE MASK THAN IN THE DRAWING, on purpose. The land is
        # stroked at 1.4 units to close the seams between neighbours, and a
        # `<use>` clone does not inherit that: nothing selects the paths, so
        # the clone took the default stroke-width of 1 and left two tenths of
        # a unit of parchment uncovered along every edge. Along the 52°E cut
        # — a straight line 700 units long — that is a bright hairline
        # exactly where the picture must not have one.
        f'<use href="#heroctx" fill="#fff" stroke="#fff" stroke-width="3"/>'
        f'<use href="#heroland" fill="#fff" stroke="#fff" stroke-width="3"/>'
        f'</mask>'
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
        + ('<g class="lyr lyr-beyond" aria-hidden="true">'
           + "".join(f'<path d="{d}"/>' for d in beyond)
           + '</g>' if beyond else "")
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
        f'<use href="#heroctx" filter="url(#heroshore)"/>'
        f'<use href="#heroland" filter="url(#heroshore)"/></g>'
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
        f'<use href="#heroctx"/><use href="#heroland"/></g>'
        + f'<g class="lyr lyr-land">'
        + f'<g class="heroctxg" aria-hidden="true">{ctx}</g>'
        + f'<g class="herolandg">{land}</g></g>'
        + (f'<g class="lyr lyr-terrain" aria-hidden="true"'
           f' mask="url(#herolandmask)">{relief}</g>' if relief else "")
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
        + f'<g class="herodusk" aria-hidden="true">'
        + f'<rect x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}"'
        f' height="{vh:.0f}" fill="url(#heroedge)"/>'
        + f'<rect x="{view[0]:.0f}" y="{view[1]:.0f}" width="{vw:.0f}"'
        f' height="{vh:.0f}" mask="url(#herodim)" fill="url(#herofootg)"/></g>'
        + f'</svg></div>'
    )


def home(data):
    """The homepage is the door, not the catalogue — and it leads with Europe.

    It ran to eight bands once: four doors, twelve motions, the quiet places,
    the stories desk, the macro regions, seventeen interest tiles, a planner
    pitch and the journeys. Every one was a real surface worth linking to,
    which is exactly how a homepage becomes a contents list.

    Cutting it to three fixed that and introduced a different fault, which
    only looking at the built page found: it led with STRUCTURE. A headline,
    a form, a technical note, a row of counts and a data map, above eight
    identical generated tiles. Technically disciplined and emotionally cold —
    an information architecture demonstration rather than a way into a
    continent. The reader met the data model before they wanted to go
    anywhere.

    So the hero is now photographic and full-bleed, the map is gone from it
    (it is a discovery mechanism, not the hero, and it also happened to be
    90 KB of inlined coastline), the counts moved below the fold, and the
    eight equal tiles became an asymmetric mosaic.

    THE PHOTOGRAPH IS NOT HERE YET. `picture()` returns one when the register
    holds it and falls back when it does not, so this page is shippable
    today and the licensed file is a one-row change to data/images.json.
    The fallback is NOT a generated plate: rendering the plate system at
    hero scale was tried and measured, and at 1200x500 it is a flat
    monochrome band with a dead slab across the bottom third. It carries a
    160x100 card and it cannot carry a hero. See docs/hero-brief.md.
    """
    ncountries = len(data["countries"])
    ncities = len(data["cities"])
    nregions = sum(len(c["regions"]) for c in data["countries"].values())
    n_by_interest = {
        i["slug"]: sum(1 for n in data["cities"].values() if i["slug"] in n["city"]["interests"])
        for i in data["taxonomy"]["interests"]
    }

    # Eight ways in, not seventeen. The design this follows asks for
    # Mountains, History, Food, Nature, Faith & Heritage, Beaches, Adventure
    # and Culture. Six of those are interests this atlas actually holds.
    # ADVENTURE AND CULTURE ARE NOT: there is no such tag, no page behind
    # either word, and no list of destinations that answers them. Rather than
    # label a tile with a word the dataset cannot honour, the two slots go to
    # the next-largest real interests — Architecture (126) and Big cities
    # (74) — and every tile carries its true name and its true count, so the
    # label on the homepage is the heading of the page it opens.
    #
    # The ORDER is the mosaic's composition: the first and the sixth get the
    # wide cells, so the two largest pictures are a landscape and a coast.
    # FOUR DOORS, NOT EIGHT TILES, AND NOT A MAP ON ANY OF THEM.
    #
    # The eight-tile version drew every destination carrying a tag, lit on
    # the shared silhouette, and the argument for it was real: the count on
    # the tile was the number of dots on it, and the difference between the
    # Alps-and-Carpathians shape and the almost-everywhere shape was the
    # thing the tile was trying to say.
    #
    # Rendered, it said something else. Eight beige Europes with blue dots,
    # side by side, above three more on the journeys — eleven maps before a
    # reader has experienced anything. Repetition turned the signature into
    # background noise: you stop seeing destinations and start seeing UI
    # components, and the labels are too small to read anyway. That is this
    # atlas's own rule about the aperture — a signature applied to everything
    # is wallpaper — arriving through a different door.
    #
    # A PER-CATEGORY CROP DOES NOT FIX IT. It was the obvious repair and it
    # fails on the data: mountains, coast, history and food are all
    # continent-wide here, so four crops are four pictures of Europe again.
    #
    # So a door is TYPE-LED with a photograph slot. Orientation is words —
    # "From the Alps to the Caucasus" — desire is the photograph, and the map
    # lives one click away on the page the door opens, where it is the
    # subject rather than a card background. Cartography orients, photography
    # persuades, and neither does the other's job.
    #
    # THE FALLBACK IS NOT A PLATE. picture() returns one when the register is
    # empty, which is right on 800 pages and wrong here for the reason the
    # hero already records: eleven abstract plates in a column is placeholder
    # art doing a picture's job, and it was this exact section. So a door
    # asks the register directly and, with no photograph, is type and space.
    doors = []
    for d in data["home"]["doors"]:
        interest = data["interests"][d["interest"]]
        n = n_by_interest[d["interest"]]
        row = (data.get("images") or {}).get(d["purpose"])
        shot = picture(data.get("images"), d["purpose"], w=1600, h=1000,
                       alt=row["alt"], sizes="(min-width: 52rem) 50vw, 100vw"
                       ) if row else ""
        # THE BAND IS A STRIP, EDGE TO EDGE, AND EACH DOOR IS A PANEL IN IT.
        #
        # With the register empty this section rendered as four blocks of
        # type in the page column: the one part of the homepage whose job is
        # to make somebody want to go somewhere, doing it entirely in words.
        # Two answers were tried before this one. A lead door carrying its
        # own constellation was better and still wrong — a fifth picture of
        # Europe on a page that already opens on one. A single photograph
        # across the whole band was tried and abandoned for a reason no
        # amount of art direction fixes: the four names are set over it, so
        # a summit captions Mountains and contradicts Coast & islands,
        # Historic cities and Food & wine in the same frame.
        #
        # One photograph PER DOOR, in one full-bleed strip, is the only
        # arrangement where every picture answers the words on top of it and
        # the band still reads as one dominant element. It also arrives in
        # pieces: four slots fill one at a time, and the strip is composed at
        # every step rather than only when all four are licensed — which a
        # single band image cannot do, being all or nothing.
        #
        # NO DRAWING HERE. The empty panel is the atlas's own water with the
        # door set on it, which is a composition rather than a hole, and the
        # arch stays where it belongs: the hero above is the largest one on
        # the site and four more under it is the signature as wallpaper.
        doors.append(
            f"""<a class="way{' shot' if shot else ''}" href="{urls.interest(d['interest'])}">
  {shot}
  <div class="waytext">
    <h3>{esc(d['title'])}</h3>
    <p class="wayline">{esc(d['line'])}</p>
    <p class="waywhere">{esc(d['where'])}</p>
    <p class="waymeta"><span>{n} destinations</span><span class="waygo">Explore →</span></p>
  </div>
</a>"""
        )

    # Three journeys, chosen by MEASUREMENT rather than by taste: ranked by
    # countries crossed — the stated differentiator, since "a good European
    # trip rarely stays in one country" — taking the highest first and
    # skipping any that repeats a spine already represented. That yields
    # Arctic to Mediterranean (7 countries), The Hanseatic Arc (6) and The
    # Adriatic Run (5): a north-south spine, a Baltic one and an Adriatic
    # one. The comp that prompted this asked for the Italian Grand Tour,
    # Northern Lights Escape and Hidden Balkans; none of the three exists in
    # this repository, and inventing them to match a picture is how a
    # homepage starts lying about what is behind it.
    FEATURED = ("arctic-to-mediterranean", "the-hanseatic-arc", "the-adriatic-run")
    by_slug = {j["slug"]: j for j in data["journeys"]}
    picked = [by_slug[s] for s in FEATURED if s in by_slug]
    if len(picked) < 3:                       # the data moved; fall back to reach
        rank = sorted(data["journeys"],
                      key=lambda j: -len({l["city"].split("/")[0] for l in j["legs"]}))
        for j in rank:
            if len(picked) == 3:
                break
            if j["slug"] not in {p["slug"] for p in picked}:
                picked.append(j)
    # And a journey draws its ROUTE. The one thing that makes a journey a
    # journey is the ordered sequence, which is exactly what an abstract
    # plate could not show — the same finding that rebuilt /journeys.
    # AND A JOURNEY IS A ROW, NOT A CARD IN A GRID OF THREE.
    #
    # Three small cards each carrying a route drawn across the whole
    # continent is three more maps in the eleven, at a size where the route
    # is a squiggle. A journey is chosen on where it goes, in order — which
    # is what /journeys already learned — so the row leads with the
    # countries crossed and the stops, and the route drawing sits beside it
    # as the explanation rather than as the picture.
    jrows = []
    for j in picked:
        legs = [data["cities"][l["city"]]["city"] for l in j["legs"]]
        countries = []
        for l in j["legs"]:
            name = data["countries"][l["city"].split("/")[0]]["name"]
            if name not in countries:
                countries.append(name)
        km = j.get("km")
        facts = [f"{j['days']} days", f"{len(countries)} countries",
                 f"{len(j['legs'])} stops"]
        jrows.append(
            f"""<a class="jrow" href="{urls.journey(j)}">
  <div class="jrowtext">
    <p class="kicker">{esc(" → ".join(countries))}</p>
    <h3>{esc(j['name'])}</h3>
    <p class="jrowsub">{esc(j['strapline'])}</p>
    <p class="jrowmeta">{esc(" · ".join(facts))}<span class="waygo">Explore journey →</span></p>
  </div>
  <div class="jrowart">{constellation(
        [project(c["lat"], c["lon"]) for c in legs], route=True, frame=True)}</div>
</a>"""
        )

    # STORIES ARE PHOTOGRAPHY-FIRST AND THERE ARE NO PHOTOGRAPHS, so the
    # lead piece gets the treatment the family already owns: the places that
    # piece is actually about, drawn at size. That is the third distinct
    # visual language in three sections — the doors carry none, a journey
    # carries its route, a story carries its own scatter — which is the
    # point. Four adjacent cards wearing the same picture of Europe is what
    # this page was rebuilt to stop.
    closing = data["home"]["closing"]
    idx = data["cities"]

    def story_glyph(st):
        pts = [project(idx[cid]["city"]["lat"], idx[cid]["city"]["lon"])
               for cid in (st.get("places") or ()) if cid in idx]
        return constellation(pts, extra=" constel-theme", frame=True) if pts else ""

    recent = sorted(data["stories"], key=lambda st: st["published"], reverse=True)[:3]
    storyband = ""
    if recent:
        lead, rest = recent[0], recent[1:]
        others = "".join(
            f'''<a class="storysm" href="{urls.story(st)}">
        <p class="kicker">{esc(st["section"])}</p>
        <h3>{esc(st["title"])}</h3>
        <p class="rowsub">{esc(st["standfirst"])}</p></a>'''
            for st in rest)
        storyband = f'''<div class="storyband">
      <a class="storylead" href="{urls.story(lead)}">
        <div class="storyart">{story_glyph(lead)}</div>
        <p class="kicker">{esc(lead["section"])} · {esc(lead["reading"])}</p>
        <h3>{esc(lead["title"])}</h3>
        <p class="rowsub">{esc(lead["standfirst"])}</p>
        <p class="waygo">Read the story →</p>
      </a>
      <div class="storyside">{others}</div>
    </div>'''

    # The intent chips seed the same box they sit under, rather than jumping
    # somewhere else: the planner reads `ask` from the query string, so a
    # chip and a typed sentence take the identical path. A chip that went to
    # a different destination from the input above it would teach the reader
    # that the input is decorative.
    INTENTS = [
        ("Mountain escapes", "I want a quiet mountain escape."),
        ("Historic cities", "Show me Europe's most historic cities."),
        ("Food experiences", "Authentic food experiences, wherever they are."),
        ("Coastal journeys", "A coastal journey, ten days, no crowds."),
    ]
    intentchips = "".join(
        f'<a class="chip" href="/plan?ask={quote(q)}">{esc(label)}</a>'
        for label, q in INTENTS
    )

    # The hero photograph, when one is licensed. `picture()` already returns
    # a plate when the register has no row — which is right everywhere else
    # and wrong here, so the hero asks the register directly and renders
    # nothing rather than a plate it has been measured unable to carry.
    hero_row = (data.get("images") or {}).get("home-hero")
    heroimg = picture(data.get("images"), "home-hero", w=2400, h=1200,
                      alt=hero_row["alt"] if hero_row else "",
                      eager=True, sizes="100vw") if hero_row else ""

    # THE CREDIT IS READ OFF THE DRAWING, not off the intention to draw.
    # The hero's relief comes from the same bands the plates use and is
    # dropped entirely if the file is absent, so the note under it asks the
    # markup whether there is any ground in the picture before naming the
    # survey that measured it. Every other page gets this from
    # cartography.credited(); the hero builds its own SVG rather than a
    # plate, so it is the one place the same rule has to be written twice —
    # and a check asserts both say it.
    # A PHOTOGRAPH REPLACES THE DRAWING; IT DOES NOT SIT BEHIND IT. Rendering
    # both stacked them — the continent drawn over the picture, the picture
    # showing through every gap in the coastline — and it took looking at the
    # built page to see it, because every count was correct.
    #
    # Which one wins was already decided in the stylesheet, before the drawn
    # hero existed: ".shot is added only when the register actually holds the
    # file, and the ground below is what a reader sees until then." The
    # drawing is the interim answer to an empty register, and it is a good
    # one — it is why this page was shippable with no photograph at all. It
    # is not a layer under a photograph.
    hero = "" if heroimg else heroeurope(data)
    heroground = (" " + cartography.RELIEF_CREDIT
                  if "lyr-terrain" in hero else "")

    # AND THE NOTE UNDER IT DESCRIBES WHAT IS ACTUALLY THERE. It said "the
    # continent above is drawn from Natural Earth" unconditionally, which
    # would have been a false claim about a photograph on the one page that
    # opens the site — the same class as /map printing the projection it had
    # stopped using.
    #
    # AND IT NAMES THE PROJECTION, so it states the four angles, from the
    # constants the build projects with rather than typed. It named the
    # conic before and printed no angle at all — c_published_projection
    # never saw it, because the phrase fell across a line break in the
    # source and the check searched the raw HTML. A claim a check cannot
    # read is a claim nothing is holding; both ends are fixed.
    herosource = (
        f'The photograph above is by {esc(hero_row["photographer"])}, '
        f'licensed under the <a href="{esc(hero_row["licence_url"])}">'
        f'{esc(hero_row["licence"])} licence</a> and served from this origin.'
        if hero_row else
        "The continent above is drawn from "
        '<a href="/sources">Natural Earth</a>, public domain, on a Lambert '
        f"conformal conic — standard parallels {geo.LCC_P1:g}°N and "
        f"{geo.LCC_P2:g}°N, origin {geo.LCC_LAT0:g}°N, central meridian "
        f"{geo.LCC_LON0:g}°E — the same projection and the same file as "
        f"every other map here.{heroground}")

    body = f"""
<section class="herofull{' shot' if heroimg else ''}">
  {heroimg}
  {hero}
  <div class="herobody">
    <h1>Open the door to Europe.</h1>
    <p class="lede">One continent, drawn as we hold it. {numword(ncountries, cap=True)} countries, and
    somewhere in them the thing you have not thought of yet.</p>
  </div>
</section>

<div class="askband">
  <form class="askhero" action="/plan" method="get">
    <label for="homeask">Where would you like to go — or what would you like to discover?</label>
    <input type="text" id="homeask" name="ask" autocomplete="off"
           placeholder="I want a quiet mountain escape in October."
           data-rotate="Show me Europe&#39;s most historic cities.|Plan 10 days through Italy.|Where can I experience authentic Mediterranean culture?|I have 10 days in September. I love mountains, history and local food.">
    <button class="btn" type="submit">Plan my journey</button>
  </form>
  <div class="chips hero-intents">{intentchips}</div>
</div>

{constel_defs()}
{section("Where to begin", '<div class="wayin">' + "".join(doors) + "</div>",
         stage="Discover", tone="quiet",
         lede="Four ways in, not a list of everything we hold. Each one opens on a "
              "real list of destinations, and the map is there rather than here — "
              "on the page it belongs to, at the size it deserves.",
         more=("Every way in", "/discover"))}

{section("Journeys worth taking", '<div class="jrows">' + "".join(jrows) + "</div>"
         if jrows else '<p class="small">Curated journeys are being written.</p>',
         stage="Go",
         lede="A good European trip rarely stays in one country. These do not — and each "
              "one opens in the planner, so you can make it yours.",
         more=("All " + str(len(data["journeys"])) + " journeys", "/journeys"))}

{section("Stories from the road", storyband,
         lede="A continent is people before it is places. Every piece links into the "
              "Atlas, and every Atlas page a story touches links back.",
         more=("All " + str(len(data["stories"])) + " stories", "/stories"))}

<section class="closing">
  <div class="closein">
    <div class="closesay">
      <h2>{esc(closing["head"])}</h2>
      <p class="closebody">{esc(closing["body"])}</p>
      <p class="closego"><a class="btn" href="/discover">{esc(closing["cta"])} →</a></p>
    </div>
    <dl class="closeextent">
      <div><dt>Countries</dt><dd>{ncountries}</dd></div>
      <div><dt>Travel regions</dt><dd>{nregions}</dd></div>
      <div><dt>Destinations</dt><dd>{ncities}</dd></div>
    </dl>
  </div>
  <p class="colophon">EuropeDoor is pre-launch and editorial: nothing here takes a payment,
  holds money or makes a booking. <a href="/how-it-works">How it works</a> ·
  <a href="/about">Who is behind it</a></p>
  <p class="sourcenote">{herosource} <a href="/map">Open the map →</a></p>
</section>
"""
    return "/index.html", page(
        SITE_NAME, body, path="/", area=None, hero=True,
        description="Discover, plan and experience Europe: an atlas of every country, region and city, a journey planner, curated cross-border routes and local experiences.",
        og=("europedoor:home", "peaks", "EuropeDoor — open the door to Europe"),
        ld_blocks=[
            {"@context": "https://schema.org", "@type": "WebSite",
             "name": SITE_NAME, "url": "https://europedoor.com",
             "description": SITE_TAGLINE,
             "inLanguage": "en",
             "publisher": LD_PUBLISHER,
             # The sitelinks search box. It points at a page that answers in
             # the browser from a static index, which is the same search the
             # reader gets — not a second implementation.
             "potentialAction": {
                 "@type": "SearchAction",
                 "target": {"@type": "EntryPoint",
                            "urlTemplate": "https://europedoor.com/search?q={search_term_string}"},
                 "query-input": "required name=search_term_string"}},
        ],
    )


# ── atlas ─────────────────────────────────────────────────────────────

def countries_index(data):
    """Nine macro regions, each shown as the countries it is made of.

    IT WAS THE PAGE ABOUT EUROPE WITH NO EUROPE ON IT. Nine headings and fifty
    rows of name, tagline and a count — the atlas index as a contents list,
    which is the shape of the data standing in for a design. Measured across
    the built page, the median horizontal band used 44% of the column and 64%
    of bands used under 60%; the argument is not that the space was empty, it
    is that a reader choosing a region of Europe was never shown one.

    Each band now opens on its own members drawn on the shared silhouette, so
    the Nordics and the Caucasus are told apart before a word is read — the
    same move that rebuilt /themes and the homepage tiles, on the family that
    needed it most and had waited longest.

    THE COUNTS MOVED OFF THE ROWS AND INTO THE BAND. "6 regions · 25 cities"
    on each of fifty rows is fifty measurements a reader cannot hold; what
    separates the nine bands is how much of this atlas each one is, and that
    is one number per band, derived here rather than typed.
    """
    blocks = []
    for m in data["macros"]:
        rows = []
        mcity = 0
        for cs in m["countries"]:
            c = data["countries"][cs]
            ncity = sum(len(r["cities"]) for r in c["regions"])
            mcity += ncity
            adv = ' <span class="tag advisory">advisory</span>' if c.get("advisory") else ""
            rows.append(
                f"""<a class="row" href="{urls.country(c)}">
                <div><h3>{esc(c['name'])}{adv}</h3><p class="rowsub">{esc(c['tagline'])}</p></div>
                <p class="rowmeta">{n_of(len(c['regions']), 'region')} · {n_of(ncity, 'city')}</p></a>"""
            )
        blocks.append(
            f"""<section class="band macroband" id="{esc(m['slug'])}">
            <div class="bandtop">
            <div class="band-head"><p class="kicker">{n_of(len(m['countries']), 'country')} · {n_of(mcity, 'destination')}</p>
            <h2><a href="{urls.macro(m)}" class="nodec">{esc(m['name'])}</a></h2>
            <p class="lede">{esc(m['blurb'])}</p></div>
            <figure class="bandart">{region_glyph(m["countries"], macro_frame(data, m))}</figure>
            </div>
            <div class="rows">{''.join(rows)}</div></section>"""
        )
    # THE PAGE ABOUT FIFTY COUNTRIES OPENED ON NONE OF THEM. Nine bands each
    # carrying a regional glyph is three densities from the second band down
    # and one density at the top: a kicker, a headline and a lede, then
    # straight into the set. Every other index here now opens on its own
    # subject at size, and the subject of this one is the continent divided —
    # not Europe as a silhouette, which is what the glyphs below draw, but
    # Europe as the fifty separate countries this atlas has written about,
    # each one its own tile with a frontier around it. It is the only place
    # on the site where that drawing appears, and it says the h1 in a
    # picture.
    #
    # AND THE CUT IS SAID RATHER THAN HIDDEN. At the continental extent
    # Russia arrives with the 52°E data cut in it — a straight slant across
    # the top right of the opening, which is the rendering fault
    # `constel_defs` drops the whole context to avoid and the homepage hero
    # spends 320 units of fade on. Neither escape is available here: the
    # sliced ring is a MEMBER rather than context, and reframing cannot lose
    # it without losing the Caucasus, whose easternmost destination projects
    # within a hundred units of the cut. The atlas already has an answer for
    # exactly this, one family over — the Russia portrait cannot fix the
    # picture either, so it says so under the drawing. The number is read off
    # the dataset's own bbox rather than typed.
    heroart = region_glyph(list(data["countries"]))
    lim = (geo.load("europe-lod1.json") or {}).get("bbox", [None, None, None])[2]
    cutsay = (f" Russia's outline stops at {lim:.0f}°E, where this atlas's map "
              f"data ends, not at a border.") if lim is not None else ""
    body = f"""
{crumbs([("Europe", "/discover"), ("Atlas", None)])}
{constel_defs()}
{indexhero(
    kicker="Every country in Europe",
    title="Europe, all the way down.",
    lede=f"{numword(len(data['macros']), cap=True)} regions, {len(data['countries'])} countries, "
         f"{sum(len(c['regions']) for c in data['countries'].values())} travel regions "
         f"and {len(data['cities'])} cities. The regions below are editorial travel "
         f"regions rather than administrative ones: they group places that feel like "
         f"each other and are usually visited together.",
    art=heroart,
    img=photo(data.get("images"), "countries-hero", w=2000, h=1500,
              sizes="(min-width: 60rem) 52vw, 100vw"),
    actions='<a class="btn" href="/map">Open the map</a>'
            '<a class="btn ghost" href="/discover">Start from what you like</a>',
    note=f"Each of the {len(data['countries'])} countries above is drawn on its own, "
         f"so the frontiers are the picture.{cutsay}")}
{''.join(blocks)}
<p class="small">The shape beside each region is the countries that region is made
of, drawn to the same frame so the nine can be compared. A macro region is the one
grouping in this atlas with real borders behind it — a travel region is a set of
destinations and is shown as those destinations rather than given a boundary it
does not have. {geo.sources_line(geo.load("europe-lod0.json"))}</p>
"""
    return "/countries/index.html", page(
        "Countries", body, path="/countries", area="countries",
        description="Every country in Europe, grouped into nine travel regions, each opening onto its regions, cities and experiences.",
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
         for html, x0, y0, lw, lh in labels], w, h)))
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
        land=f"{ctx}{land}", labels=drawn,
        caption=f'<figcaption>{cap}</figcaption>',
        figure_class=f"minimap macromap arched atlas{dense_class(drawn)}",
        aria=(f'Map of {esc(m["name"])}: its {len(members)} countries filled, '
              f'the rest of Europe behind them'))


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
        cards.append(card(urls.country(c), c["capital"], c["name"], c["tagline"],
                          art=country_glyph(c["slug"], cs)
                              or region_glyph([cs], pts or None, min_span=340.0),
                          meta=meta))
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], None)])}
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



    def _try_label(px, py, text, cls, metric="minilabel", off=10.0,
                   prefer="beside", wrap=None):
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
                              wrap=wrap)
        if not got:
            return False
        lhtml, lx, ly, lw, lh = got
        boxes_.append((lx - LABEL_CLEAR, ly - LABEL_CLEAR,
                       lx + lw + LABEL_CLEAR, ly + lh + LABEL_CLEAR))
        labs_.append(lhtml)
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
    _cbox = _highlight_box(land)
    if _cbox:
        _ccx, _ccy, _cr = _cbox
        _anchors = ((0, 0), (0, -0.45), (0, 0.45), (-0.5, 0), (0.5, 0),
                    (-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4))
        _up = c["name"].upper()
        _placed_name = any(
            _try_label(_ccx + fx * _cr, _ccy + fy * _cr, _up, "cname",
                       metric="cname", off=10.0, prefer="over")
            for fx, fy in _anchors)
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

            for fx, fy in _anchors:
                if _try_label(_ccx + fx * _cr, _ccy + fy * _cr, _long,
                              "cname", metric="cname2", off=10.0,
                              prefer="over", wrap=_two):
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
    summitmarks = ""
    for px, py, nm, m in cartography.summit_points(proj.xy, (0, 0, w, h)):
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
                   r_["name"].upper(), "rname", metric="rlabel", off=9.0,
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
        art = constellation(rpts, extra=" regionmini",
                            frame=True) if onframe else ""
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
    popular = [
        card(urls.city(c, r, t), f"{r['name']}", t["name"], t["summary"],
             seed=f"city:{c['slug']}:{t['slug']}",
             motif=motif_for(t["interests"], t.get("city_type")),
             meta=f'<p class="cardmeta">{n_of(len(t.get("places", [])), "place")} · '
                  f'{n_of(len(t.get("experiences", [])), "experience")}</p>')
        for r, t in ranked[:6]
    ]
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
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], urls.macro(m)), (c["name"], None)])}
<div class="pagehead overture portraithead">
  <div class="portraitsay">
    <p class="kicker">{esc(m['name'])}</p>
    <h1>{esc(c['name'])}</h1>
    {statement(c['tagline'])}
    <p class="orient">{country_orient(c)}</p>
    {chips(c["interests"], data["interests"])}
  </div>
  {countryportrait(data, c)}
</div>
{advisory_note(c)}

<div class="measure lead">
  <p>{esc(c['summary'])}</p>
</div>

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

{section("Popular destinations", grid(popular, 3),
         lede="The destinations we have written most about, which is not the same as the ones most people go to — and is the only ranking we can honestly compute.",
         more=("Every region", "#regions")) if popular else ""}

{section("Experiences here", f'<div class="rows">{cexps}</div>',
         lede=f"A sample of what is listed across {c['name']}.",
         more=("Every experience category", "/experiences")) if cexps else ""}

{section("Journeys through " + c["name"], f'<div class="rows">{cjourneys}</div>') if cjourneys else ""}

{section("Stories set here", f'<div class="rows">{cstories}</div>') if cstories else ""}

{section("Fixed points in the year", f'<div class="rows">{festivals}</div>',
         more=("The whole European year", "/events")) if festivals else ""}

{section("The record", facts + scorebars(country_scores(c), _spread("country", data)) + provenance_block(c),
         tone="quiet",
         lede="What we hold about " + c["name"] + ", where each figure came "
              "from, and when it was last checked. The score says what this "
              "country is for, not how good it is — it is useful once you are "
              "already interested and is not a reason to be.")}
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
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], urls.macro(m)),
         (c["name"], urls.country(c)), (r["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">{esc(c['name'])}</p>
  <h1>{esc(r['name'])}</h1>
  {statement(r['summary'])}
  <p class="orient">{n_of(len(r["cities"]), "destination")} ·
  {len(rplaces)} place{"s" if len(rplaces) != 1 else ""} recorded ·
  about {n_of(int(pass_nights), "night")} to see it all</p>
  {chips(r["interests"], data["interests"])}
</div>

{regionmap(data, c, r)}

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
"""
    return f"/europe/{c['slug']}/{r['slug']}/index.html", page(
        f"{r['name']}, {c['name']}", body, path=urls.region(c, r), area="countries",
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

    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], urls.macro(m)),
         (c["name"], urls.country(c)), (r["name"], urls.region(c, r)), (t["name"], None)])}
<div class="pagehead overture arrivalhead">
  <div class="arrivalsay">
    <p class="kicker">{esc(r['name'])}, {esc(c['name'])}</p>
    <h1>{esc(t['name'])}</h1>
    {statement(t['summary'])}
    <p class="orient">{orient_line(t)}</p>
    {chips(t["interests"], data["interests"])}
  </div>
  <section class="whygo" aria-labelledby="why-visit">
    <h2 id="why-visit">Why go</h2>
    <ol class="reasons">{reasons}</ol>
  </section>
</div>

<div class="placeband{'' if has_photo else ' maponly'}">
  {photo_block}
  <div class="placeband-map">{minimap(data, t, span="auto", named=nearnamed)}</div>
  <p class="sourcenote">{esc(t["name"])} is at <span class="mono">{coord_line(t)}</span>.</p>
</div>
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
    <p>{esc(c['getting_around'][:150])}…
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
             id="getting-near") if transrows else ""}
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
         id="tips",
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
"""
    return f"/europe/{c['slug']}/{r['slug']}/{t['slug']}/index.html", page(
        f"{t['name']}, {c['name']}", body, path=urls.city(c, r, t), area="countries",
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
    return f'''<div class="stickycta">
  <span class="stickycta-where">{esc(t["name"])}</span>
  <button class="btn ghost" type="button" data-short
          data-save="city:{esc(c['slug'])}/{esc(r['slug'])}/{esc(t['slug'])}"
          data-kind="Place" data-label="{esc(t['name'])}, {esc(c['name'])}"
          data-url="{urls.city(c, r, t)}">Save</button>
  <a class="btn" href="/plan?from={esc(c['slug'])}%2F{esc(r['slug'])}%2F{esc(t['slug'])}">Add to my journey</a>
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
            f'<div><h3>{esc(n["city"]["name"])}</h3>'
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
                         for n in cities]) if cities else ""
    body = f"""
{crumbs([("Europe", "/discover"), ("Experiences", "/experiences"), (i["name"], None)])}
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
    return f"/interests/{slug}/index.html", page(
        i["name"], body, path=urls.interest(slug), area="countries",
        description=f"Where in Europe to go for {i['name'].lower()}: {len(cities)} cities across {len(countries)} countries.",
    )


# ── journeys ──────────────────────────────────────────────────────────

def journeys_index(data):
    """Seventeen journeys, shown as routes rather than as cards.

    THE INDEX SHOWED EVERYTHING ABOUT A JOURNEY EXCEPT THE JOURNEY. Four
    across, each a generated plate over a name, a truncated summary and
    "19 DAYS · 5 COUNTRIES · MODERATE" — and four abstract landscapes in a
    row read as a family rather than as four trips. The one thing that makes
    a journey a journey, and the one thing this atlas holds in full, is the
    ORDERED SEQUENCE OF PLACES. It was the only thing not on the page.

    Eight of the nine indexes were the same 280px card grid; that finding is
    recorded in docs/design-direction-audit.md as the h1 finding one level up.
    A card is the right shape for a set of like things a reader is choosing
    between on look. A journey is not chosen on look: it is chosen on where it
    goes, how long it takes and how hard it is, and all three of those are
    text.

    So it is the `row` primitive — already on 86% of pages, so this is not a
    new component — carrying the stops in order, and a route line that is the
    same `hopbar` the journey page draws, laid end to end instead of stacked.
    A reader sees the shape of the trip: many short segments is a slow local
    circuit, three long ones is a continental haul.
    """
    rows = []
    for j in data["journeys"]:
        countries, stops, hops = [], [], []
        prev = None
        for leg in j["legs"]:
            n = data["cities"][leg["city"]]
            cn = n["country"]["name"]
            if cn not in countries:
                countries.append(cn)
            stops.append(esc(n["city"]["name"]))
            if prev is not None:
                hops.append(haversine(prev, n["city"]))
            prev = n["city"]
        # THE SEGMENTS ARE A SHARE OF THE WHOLE TRIP, not of its longest leg.
        # The journey page scales each hop against the longest one, because
        # there the question is "which of these days is the long one". Here
        # the bar is the whole route in one line, so a segment is its share of
        # the total distance and the line reads as the trip's own rhythm.
        total = sum(hops)
        segs = "".join(
            f'<span class="w{max(1, int(round(km / total * 100)))}"></span>'
            for km in hops) if total else ""
        # AND THE ROUTE IS DRAWN. Seventeen rows of kicker, name, dot-separated
        # stops and a thin bar is a spreadsheet: the page told a reader
        # everything about a journey except where it goes, which is the one
        # question a journey is chosen on and the one this atlas can answer
        # in a picture. The homepage was showing three journeys better than
        # the journeys index showed seventeen.
        #
        # No two of these seventeen lines are alike — Arctic to Mediterranean
        # is the length of Europe, the Iberian Circle is a loop in one corner,
        # the Baltic Crossing is four capitals in a square — so this is the
        # one family where a drawing per row differentiates rather than
        # repeats. That is the test the homepage's four doors failed and this
        # one passes.
        route = constellation(
            [project(data["cities"][l["city"]]["city"]["lat"],
                     data["cities"][l["city"]]["city"]["lon"]) for l in j["legs"]],
            route=True, frame=True)
        rows.append(
            f'<a class="row journeyrow" href="{urls.journey(j)}">'
            f'<div><p class="kicker">{esc(j["strapline"])}</p>'
            f'<h3>{esc(j["name"])}</h3>'
            f'<p class="rowsub">{" · ".join(stops)}</p>'
            f'<span class="hopbar route" aria-hidden="true">{segs}</span>'
            f'<p class="rowmeta jfacts">{n_of(j["days"], "day")} · {n_of(len(countries), "country")}'
            f' · {esc(j["difficulty"])}</p></div>'
            f'<div class="jart">{route}</div></a>')
    # THE OPENING IS EVERY ROUTE AT ONCE, and no other travel product can
    # draw it: seventeen real sequences of real places on one conformal
    # conic, so a reader sees the reach of the whole set before reading a
    # word. It is the family's own subject at size, which is what an index
    # hero is for — and it is the honest stand-in until a photograph lands in
    # the slot beside it, because a plate here would be a picture of nowhere.
    # THE CASINGS FIRST, ALL OF THEM, THEN THE CORES. Seventeen routes cross
    # each other constantly, and a per-route casing would lay the next
    # route's cream stroke over the previous route's cobalt one — a line that
    # breaks wherever another passes. Both passes over the whole set, which
    # is how a printed map plates a network.
    routepts = [[project(data["cities"][l["city"]]["city"]["lat"],
                         data["cities"][l["city"]]["city"]["lon"])
                 for l in j["legs"]] for j in data["journeys"]]
    allroutes = "".join(
        f'<polyline class="constel-route case" points="'
        + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '"/>'
        for pts in routepts) + "".join(
        f'<polyline class="constel-route" points="'
        + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '"/>'
        for pts in routepts)
    # `slice` rather than the default `meet`. The frame is 4:3 and the map is
    # 1000x780, which is 1.28 — close enough that slicing crops a few units of
    # open sea and far enough that letterboxing left the continent floating in
    # black margins with the arch cutting nothing. A drawing in an opening
    # should fill the opening; that is what the homepage hero had to learn.
    heroart = (f'<svg class="constel allroutes" viewBox="0 0 {MAP_W} {MAP_H}" '
               f'preserveAspectRatio="xMidYMid slice" '
               f'aria-hidden="true" focusable="false"><use href="#constel-eu"/>'
               f'{allroutes}</svg>')
    body = f"""
{crumbs([("Europe", "/discover"), ("Journeys", None)])}
{constel_defs()}
{indexhero(
    kicker="European Journeys",
    title="Routes that cross borders on purpose.",
    lede=f"{len(data['journeys'])} routes, each a real sequence with real distances: "
         f"every stop links back into the Atlas, and the nights add up to the days on "
         f"the tin. Take one as written, or open it in the Planner and bend it to the "
         f"time you actually have.",
    art=heroart,
    img=photo(data.get("images"), "journeys-hero", w=2000, h=1200,
              sizes="(min-width: 60rem) 52vw, 100vw"),
    actions='<a class="btn" href="/plan">Build your own</a>'
            '<a class="btn ghost" href="/map">See them on the map</a>',
    note="Every line above is one of the seventeen, drawn from its own stops."
         + datacut_line())}
<div class="rows journeyrows">{"".join(rows)}</div>
<p class="small">The shape beside each route is where it goes, drawn on the same
projection as every other map here. {geo.sources_line(geo.load("europe-lod0.json"))}
Every stop above is a place in the Atlas, in the order the
route takes it. The line under each is that journey's own legs end to end —
its share of the whole distance, so the shape is the trip's rhythm rather
than a comparison between trips. Distances are straight lines between
coordinates; what they mean on the ground is on the journey's own page.</p>
"""
    return "/journeys/index.html", page(
        "Journeys", body, path="/journeys", area="journeys",
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
    body = f"""
{crumbs([("Europe", "/discover"), ("Journeys", "/journeys"), (j["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">Journey</p>
  <h1>{esc(j['name'])}</h1>
  {statement(j['strapline'])}
  <p class="orient">{n_of(j['days'], 'day')} · {n_of(len(j['legs']), 'stop')} · {n_of(len(countries), 'country')} · {total_km:,} km in a straight line</p>
  {chips(j["interests"], data["interests"])}
</div>

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
"""
    legs_ld = []
    for leg in j["legs"]:
        n = data["cities"][leg["city"]]
        legs_ld.append(ld_within("TouristDestination", n["city"]["name"],
                                 urls.city(n["country"], n["region"], n["city"])))
    return f"/journeys/{j['slug']}/index.html", page(
        j["name"], body, path=urls.journey(j), area="journeys",
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
             "name": j["name"], "url": "https://europedoor.com" + urls.journey(j),
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


def planner_page(data):
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
    budgets = "".join(
        f'<option value="{esc(b["slug"])}"{" selected" if b["slug"] == "moderate" else ""}>'
        f'{esc(b["name"])} — {esc(b["note"])}</option>'
        for b in data["taxonomy"]["budgets"]
    )
    body = f"""
{crumbs([("Europe", "/discover"), ("Plan", None)])}
{constel_defs()}
{jsondata("europedoor-glyphview-cases",
          [f"{len(pts)}:" + glyph_view(pts) for pts in GLYPHVIEW_CASES])}
<div class="pagehead instrument">
  <p class="kicker">Journey Planner</p>
  <h1>Twelve days, €2,500, history and mountains.</h1>
  {head_extent([(len(data['cities']), 'destinations scored'),
                (len(data['countries']), 'countries'),
                (len(data['journeys']), 'routes already built')])}
  <p class="lede">Say what you have and what you like — in a sentence, or in the form below.</p>
</div>

<form class="form ask" id="askform">
  <div class="field">
    <label for="ask">Say it in your own words</label>
    <textarea id="ask" name="ask" rows="2"
      placeholder="I have 12 days and €2,500, starting in Lisbon, and I love history, mountains and food."></textarea>
  </div>
  <div class="askfoot">
    <div class="hero-actions mt0">
      <button class="btn" type="submit">Read that and build it</button>
    </div>
    <p class="small mb0">The planner reads the whole Atlas, scores every destination
    against you, then builds a route that respects distance instead of teleporting
    between highlights. It is read by rules in your browser — not by a model, and not
    sent anywhere — and it shows you exactly what it understood, naming anything it
    could not take account of rather than quietly dropping it.</p>
  </div>
</form>

<div class="planform">
  <div>
    <form class="form" id="planner">
      <div class="form-row">
        <div class="field">
          <label for="days">Days</label>
          <input type="number" id="days" name="days" min="3" max="45" value="12" inputmode="numeric">
        </div>
        <div class="field">
          <label for="budget">Total budget (€, per person)</label>
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
            <option value="slow">Slow — fewer places, longer stays</option>
            <option value="balanced" selected>Balanced</option>
            <option value="fast">Fast — see as much as possible</option>
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
            <option value="mixed" selected>Mixed — whatever suits the place</option>
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
    </form>
    <div id="result" aria-live="polite"></div>
  </div>
</div>

<!-- HOW IT DECIDES CAME OUT OF THE RAIL AND WENT UNDER THE TOOL.
     Four hundred words of scoring weights in a right-hand column, level
     with the twelve fields and seventeen checkboxes a reader is filling
     in — two things competing for the same attention, and the form
     squeezed into two thirds of the page to make room for an essay
     nobody reads while they are typing. The form takes the full measure
     now and the method sits under it, which is also where a reader asks
     the question: they run it, they look at the answer, and THEN they
     want to know why it chose that. Proof goes under the thing it
     proves, which is the rule the motion pages already publish. -->
<div class="planmethod">
  <div class="methodcols">
    <h2 class="mini">How it decides</h2>
    <p>Every destination is scored out of one, on a published weighting:</p>
    <ul>
      <li><strong>30%</strong> how many of your interests it carries</li>
      <li><strong>20%</strong> whether it has things to actually do that match them</li>
      <li><strong>15%</strong> the month you named — peak, shoulder or off, never zero</li>
      <li><strong>10%</strong> how connected it is to the rest of the Atlas</li>
      <li><strong>20%</strong> how much of it we have actually written</li>
      <li><strong>5%</strong> novelty: quiet places, and countries not yet in your route</li>
    </ul>
    <p class="small">The specification this came from allocates 10% to popularity. We have no
    traffic and no licensed visitor data, so that term would be a number we invented wearing a
    percentage sign. Its weight moved to content quality, which is measurable. And
    "accessibility" there means <em>reachability</em> — we hold no step-free access data at
    all, and <a href="/accessibility">say so</a>.</p>
    <p>Then: distance penalises each next stop so the route stops wandering; three big cities
    in a row start to push the fourth choice towards the alternative; nights come from the
    range on each destination page; and anything above what your budget can afford per day is
    damped.</p>
    <h2 class="mini">What it will not do</h2>
    <p>It will not book anything, price a real hotel, or route you into a country under a
    travel advisory — those are excluded from the planning index entirely.</p>
    <p class="small">Estimates are editorial, not quotes. Check <a href="/sources">sources and
    corrections</a>. The route above is drawn from the coordinates in the Atlas
    rather than from any road or rail geometry, on the same Lambert conformal conic
    as every other map here — standard parallels {geo.LCC_P1:.0f}°N and
    {geo.LCC_P2:.0f}°N, origin {geo.LCC_LAT0:.0f}°N, central meridian
    {geo.LCC_LON0:.0f}°E. {geo.sources_line(geo.load("europe-lod0.json"))}</p>
  </div>
</div>
"""
    return "/plan/index.html", page(
        "Plan a journey", body, path="/plan", area="plan",
        description="Tell EuropeDoor your days, budget and interests and it builds a European itinerary with real distances, real night counts and a cost estimate.",
        scripts=["/assets/js/planner.js"],
        # INTELLIGENCE — the planner: journey construction
        world="intelligence"
    )


# Named on every destination page, and honestly empty. A scraped hotel list
# would take an afternoon and would be the first unverified thing on the site.
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
    drawn = "".join(phone_declutter(_declutter(labels, w, h)))
    return (
        f'<figure class="minimap countrymap arched{dense_class(drawn)}" data-role="instrument">'
        f'<svg viewBox="0 0 {w} {h}" role="img" data-world="intelligence" '
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
        f'<figcaption>{esc(c["name"])}, its {n_of(len(c["regions"]), "region")} and {shown} '
        f'{"destination" if shown == 1 else "destinations"}. Region names sit at the '
        f'centre of their own destinations — they are groupings, not boundaries.{note} '
        f'Coastline and borders from <a href="/sources">Natural Earth</a>, public domain. '
        f'<a href="/map?c={esc(c["slug"])}">Open {esc(c["name"])} on the full map →</a>'
        f'</figcaption></figure>'
    )


def first_sentence(text):
    """The first sentence, whole.

    This was `text[:140] + "…"`, which cut "The Bergen and Dovre railways are
    two of Europe's great train rides and cost less than the equivalent
    flight if booked early. Coastal Norway…" — a truncation mid-clause,
    printed on 400 place pages, that reads as a rendering fault rather than
    as a summary. A sentence boundary is the one place a text can be cut
    without looking broken.
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
    labels.append(("", *geo.scale_bar_box(w, h)))
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
        for _hh, qx, qy, qw, qh in labels:
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
        for _hh, qx, qy, qw, qh in labels:
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

    drawnlabels = "".join(phone_declutter(labels))

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
    cap = (
        f'<figcaption>'
        + (f'{esc(about)} is in {esc(t["name"])}, and this is {esc(t["name"])} '
           f'— the atlas draws Europe in one projection whose finest unit is '
           f'about four kilometres, so it maps the town rather than the '
           f'street. The frame is about ' if about else
           f'{esc(t["name"])} and its neighbours in the Atlas — the frame is about ') +
        f'{km_w:,} km across and {km_h:,} km deep at this latitude. '
        # THE CREDIT, WHICH 318 PAGES DID NOT CARRY AND 274 CARRIED BY
        # ACCIDENT. A destination page named Natural Earth because pop_line
        # prints the dataset behind its population — so the 45 destinations
        # with no population figure named nothing, and every place page named
        # nothing. Coverage that depends on a different field being present
        # is worse than none, because it looks like a policy. One clause, the
        # same one the region and story maps carry.
        f'Coastline from <a href="/sources">Natural Earth</a>, public domain. '
        f'<a href="/map">The full map →</a></figcaption>')
    return cartography.plate(
        # TWO SPACES, NAMED SEPARATELY. `view` is the window in the
        # continent projection this plate shows; `transform` is what
        # takes that window to the 900x320 picture. Every caller used to
        # pass (0, 0, w, h) here, which made the renderer select its own
        # layers from the North Sea and draw them over the Alps.
        uid=uid, w=w, h=h, proj=MAPPROJ, view=view,
        transform=(f'translate({w/2 - cx*span:.2f},'
                   f'{h/2 - cy*span:.2f}) scale({span})'),
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


def phone_declutter(placed):
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

    `placed` is [(html, x0, y0, w, h)]; returns the html, in order.
    """
    kept, out = [], []
    # THE SAME CLEARANCE EVERY OTHER PASS KEEPS, scaled with the boxes. This
    # tested bare overlap, so two names could be placed touching: measured at
    # 390 px, four plates had a pair meeting by up to two pixels. Not visible,
    # and not a number to leave in a check's tolerance either — a threshold
    # that forgives two pixels forgives the next regression that lands on
    # two.
    clear = LABEL_CLEAR * PHONE_LABEL_SCALE
    for html, x0, y0, w, h in placed:
        cx, cy = x0 + w / 2.0, y0 + h / 2.0
        bw, bh = w * PHONE_LABEL_SCALE, h * PHONE_LABEL_SCALE
        box = (cx - bw / 2.0 - clear, cy - bh / 2.0 - clear,
               bw + 2 * clear, bh + 2 * clear)
        clash = any(box[0] < k[0] + k[2] and k[0] < box[0] + box[2]
                    and box[1] < k[1] + k[3] and k[1] < box[1] + box[3]
                    for k in kept)
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
                ("minilabel", "peakname", "fname", "sname", "rname"))
    return "" if names <= 6 else " dense"


def pointsmap(pts, uid, caption, aria, want=2.6, pad_frac=0.18, pad_min=24,
              min_w=120.0, min_h=75.0, line=False, extra="", relief=False):
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
    ctx, land = geo.landmass(MAPPROJ, (x0, y0, w, h))
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
    lab = phone_declutter(lab)
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
        land=land, context=ctx, relief=relief, frame_km=frame_km,
        route=route, destinations="".join(dots),
        labels="".join(lab) + bar,
        caption=f'<figcaption>{caption}</figcaption>',
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
    cap = (f'{esc(r["name"])} is the {len(pts)} destination'
           f'{"s" if len(pts) != 1 else ""} below, not a boundary — this atlas '
           f'holds which places belong to a region and deliberately not a line '
           f'round them. Coastline from <a href="/sources">Natural Earth</a>, '
           f'public domain. <a href="/map?c={esc(c["slug"])}">Open '
           f'{esc(c["name"])} on the full map →</a>')
    # A REGION NEEDS THE COUNTRY AROUND IT, NOT A CLOSE-UP OF ITSELF.
    # Tyrol & the West holds one destination; at the default floor that is a
    # single dot in 250 km of unlabelled frontier line, which could be
    # anywhere in the Alps. 260 x 165 is roughly 1,100 x 700 km — enough for
    # a coast or a recognisable border to appear and place it.
    return pointsmap(pts, uid, cap,
                     f'Map of {r["name"]}, {c["name"]}: its '
                     f'{n_of(len(pts), "destination")} in the Atlas',
                     min_w=260.0, min_h=165.0)


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
    cap = (f'Where this happens: {esc(where)}. Coastline and borders from '
           f'<a href="/sources">Natural Earth</a>, public domain. '
           f'<a href="/map">The full map →</a>')
    return pointsmap(pts, uid, cap,
                     f'Map of where {s["title"]} happens: {where}')


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
           '— the order is real, the lines are not routes. Coastline from '
           '<a href="/sources">Natural Earth</a>, public domain. '
           '<a href="/map">The whole map, with every journey →</a>')
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
                     line=True, relief=rel)


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
                f'<figcaption>{n_of(len(routes), "curated route")} through '
                f'{esc(t["name"])}, drawn end to end on the same projection as '
                f'every other map here. '
                f'{geo.sources_line(geo.load("europe-lod0.json"))}</figcaption>'
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
        f"""<a class="row" href="{esc(href)}"><div><h3>{esc(title)}</h3>
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
    nearby = "".join(
        f"""<a class="row" href="{urls.place(c, r, t, x)}">
        <div><h3>{esc(x['name'])}</h3><p class="rowsub">{esc(x['summary'])}</p></div>
        <p class="rowmeta">{esc(PLACE_KIND_NAMES[x['kind']])}</p></a>"""
        for x in others
    )
    cid = f"{c['slug']}/{r['slug']}/{t['slug']}"
    b = data["back"][cid]
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
    has_photo = bool((data.get("images") or {}).get(f"place:{cid}/{pl['slug']}"))
    placeart = (f'<div class="card-art frame">'
                + picture(data["images"], f"place:{cid}/{pl['slug']}", w=1260, h=540,
                          alt=f"{pl['name']}, {t['name']}", eager=True,
                          sizes="(min-width: 76rem) 76rem, 100vw")
                + '</div>') if has_photo else minimap(data, t, span="auto", about=pl["name"])

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
<div class="pagehead overture">
  <p class="kicker">{esc(PLACE_KIND_NAMES[pl['kind']])} · {esc(t['name'])}, {esc(c['name'])}</p>
  <h1>{esc(pl['name'])}</h1>
  {statement(pl['summary'])}
  <p class="orient">Give it {esc(pl['duration'])} · {esc(SEASON_NAMES[pl['season']])} ·
  <span class="mono">{pl["lat"]:.3f}°N, {pl["lon"]:.3f}°E</span></p>
</div>
{placeart}

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
    <div class="note sourced">
      <h2 class="mini">We do not hold opening hours, prices or a website for this</h2>
      <p>Those are the three fields that go stale fastest and the three you are most damaged
      by being wrong about, so this site does not carry them at all rather than carrying an
      unverified version. Check the operator or the municipality on the day. The estimate of
      how long to give it, and the season, are editorial judgements and are usually stable.</p>
    </div>
    <p><button class="btn ghost" type="button" data-save="place:{esc(cid)}/{esc(pl['slug'])}"
       data-kind="Place" data-label="{esc(pl['name'])}, {esc(t['name'])}"
       data-url="{urls.place(c, r, t, pl)}">Save to My Europe</button></p>
    {section("What happens here", f'<div class="rows">{doing}</div>',
             lede="Experiences tied to this place, and how each one is tied to it — "
                  "standing on it, starting from it, or looking at it.") if doing else ""}
    {section("Other places in " + t["name"], f'<div class="rows">{nearby}</div>') if nearby else ""}
    {section("Journeys that stop here", f'<div class="rows">{jrows}</div>') if jrows else ""}
  </div>
</div>
{section("The record", facts, tone="quiet",
         lede="What this atlas holds about " + pl["name"] + ", and nothing "
              "it does not.")}
"""
    return f"{urls.place(c, r, t, pl)}/index.html", page(
        f"{pl['name']}, {t['name']}", body, path=urls.place(c, r, t, pl), area="countries",
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
    rows = "".join(
        f"""<li class="invite"><a href="{urls.city(it['country'], it['region'], it['city'])}">
        <h2>{esc(it['exp']['name'])}</h2>
        <p class="invite-sum">{esc(it['exp']['summary'])}</p>
        <p class="invite-where">{esc(it['city']['name'])}, {esc(it['country']['name'])}"""
        + (f" · {esc(kindname.get(it['exp']['kind'], it['exp']['kind']))}"
           if len(kindsin) > 1 else "")
        + f""" · {esc(it['exp']['band'])}</p></a></li>"""
        for it in chosen
    )
    subcards = ""
    if not sub and cat.get("subs"):
        counts = {sb["slug"]: len(C.select(items, cat, sb)) for sb in cat["subs"]}
        # A CARD IS A CONTAINER FOR SOMETHING, AND THESE HELD A COUNT AND A
        # NAME. Four grey boxes with nothing in them, taking a full band and
        # 150 pixels of the page above the list they narrow. They are what
        # they always were: four links with a number each.
        subcards = '<ul class="sublinks">' + "".join(
            f"""<li><a href="{urls.subcategory(cat['slug'], sb['slug'])}">"""
            f"""{esc(sb['name'])} <span>{counts[sb['slug']]}</span></a></li>"""
            for sb in cat["subs"]
        ) + "</ul>"

    countries = sorted({it["country"]["name"] for it in chosen})
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

    body = f"""
{crumbs(trail)}
<!-- AN INDEX, NOT AN OVERTURE. This page is a SET — 48 experiences across
     26 countries — and it carried the head of a page about one thing: a
     60px h1 at y=212 with the extent under it. The three roles are what the
     reader is doing, and an index's extent sits beside its name so the set
     starts sooner. Measured across the twenty-two families: 538 to 347. -->
<div class="pagehead index">
  <p class="kicker">{esc(cat['name']) if sub else 'Experience category'}</p>
  <h1>{esc(title)}</h1>
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
<!-- THE MECHANISM WAS STANDING IN FRONT OF THE ANSWER. "How this list is
     built" was a full section with its own h2 and a lede, ABOVE the list,
     so a reader met the selection rule before they met a single thing to
     do — the exact defect the motion pages were rebuilt for, one family
     over. THE QUERY IS THE PROOF, AND PROOF GOES UNDER THE THING IT
     PROVES: the rule now sits below the list, beside the sub-category
     rulenote, which was already there and is the same kind of sentence. -->
<ol class="invites">{rows or empty_state(
      "Nothing matches this rule yet.",
      "The rule is printed below and is the same one every other list on "
      "this site is built from. An empty list is better than a padded one, "
      "and widening the rule until something fell in would make every other "
      "list on the site mean less.")}</ol>
{f'<p class="listrule">How this list is built: {esc(C.rule_text(cat))}</p>' if not sub else ""}
{rulenote}
"""
    return f"{path}/index.html", page(
        title, body, path=path, area="experiences",
        description=f"{title}: {n_of(len(chosen), 'experience')} across {n_of(len(countries), 'European country')}, selected by a published rule.",
    )


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
    from .data import all_experiences
    kinds = data["taxonomy"]["experience_kinds"]
    items = all_experiences(data["countries"])
    counts = {}
    for it in items:
        counts[it["exp"]["kind"]] = counts.get(it["exp"]["kind"], 0) + 1
    from . import categories as C

    def taste(sel):
        names = sample_names(sel)
        return ('<p class="taste">' + "".join(
            f"<span>{esc(x)}</span>" for x in names) + "</p>") if names else ""

    # EIGHTEEN IDENTICAL BORDERED BOXES, TWICE. Border, fill, radius and
    # shadow each say "separate object", and spending all four on every tile
    # of an eighteen-tile page spends them on nothing: the grid read as one
    # texture, and what actually separates these rows — that Family holds 131
    # entries and Luxury holds 5 — was four characters of kicker type.
    #
    # The count is the subject, so the count is drawn. A bar is scaled to the
    # LARGEST IN ITS OWN GROUP rather than to the total, and that is a
    # measured decision rather than a convenience: an experience carries ONE
    # kind and ANY NUMBER of categories, so the ten kinds sum to 197 and the
    # eight categories sum to 493 memberships over the same 197 experiences.
    # A bar labelled as a share of the whole would read 250% down the
    # category column. Both figures are derived here and the note under them
    # says which is which.
    def barrow(href, n, biggest, name, blurb, sel):
        pct = 0 if not biggest else round(100.0 * n / biggest, 1)
        return (f'<a class="row barrow" href="{href}">'
                f'<div><h3>{esc(name)}</h3>'
                + (f'<p class="rowsub">{esc(blurb)}</p>' if blurb else "")
                + taste(sel)
                + f'</div><div class="barside">'
                f'<p class="rowmeta">{n} listed</p>'
                # THE BAR IS `hopbar` AND THE WIDTHS ARE THE .w0-.w100 SCALE,
                # because both already exist: a journey's legs and the score
                # bars draw proportions exactly this way, and this is the
                # third of them rather than the first. No new primitive until
                # repeated structure has actually emerged — it has.
                + f'<span class="hopbar" aria-hidden="true">'
                  f'<span class="w{int(round(pct))}"></span></span>'
                + '</div></a>')

    catn = {cat["slug"]: len(C.select(items, cat)) for cat in data["categories"]}
    catbig = max(catn.values()) if catn else 0
    catcards = [
        barrow(urls.category(cat["slug"]), catn[cat["slug"]], catbig,
               cat["name"], cat["blurb"], C.select(items, cat))
        for cat in sorted(data["categories"], key=lambda c: -catn[c["slug"]])
    ]
    # NO BLURB, BECAUSE IT WAS THE SAME SENTENCE TEN TIMES. Every kind tile
    # carried "Grouped by what you actually do rather than by what it is
    # about", which is a fact about the axis and not about the kind — the
    # boilerplate this atlas's own rule forbids, hoisted into the section
    # lede where one copy of it belongs. `blurb=None` is the pattern the
    # homepage's eight ways-in tiles already use.
    kindbig = max(counts.values()) if counts else 0
    cards = [
        barrow(urls.experience_kind(k), counts.get(k, 0), kindbig, name, None,
               [it for it in items if it["exp"]["kind"] == k])
        for k, name in sorted(kinds.items(), key=lambda kv: -counts.get(kv[0], 0))
    ]
    rows = "".join(
        f"""<a class="row" href="{urls.city(it['country'], it['region'], it['city'])}">
        <div><h3>{esc(it['exp']['name'])}</h3>
        <p class="rowsub">{esc(it['exp']['summary'])}</p></div>
        <p class="rowmeta">{esc(it['city']['name'])} · {esc(it['country']['name'])}</p></a>"""
        for it in items[:24]
    )
    body = f"""
{crumbs([("Europe", "/discover"), ("Experiences", None)])}
{constel_defs()}
{indexhero(
    kicker="Local Experiences",
    title="What people actually do here.",
    lede=f"{len(items)} experiences across the Atlas, in {numword(len(data['taxonomy']['experience_kinds']))} kinds. Anything a business "
         f"lists carries the name of who runs it and the tier of checking it has passed — "
         f"an unchecked listing says so on its face rather than hiding behind a star "
         f"rating.",
    art=constellation(sorted({project(it["city"]["lat"], it["city"]["lon"])
                              for it in items})),
    img=photo(data.get("images"), "experiences-hero", w=2000, h=1200,
              sizes="(min-width: 60rem) 52vw, 100vw"),
    actions='<a class="btn" href="/experiences/join">List your experience</a>'
            '<a class="btn ghost" href="/for-businesses">For businesses</a>',
    note='Every place in the Atlas with something on this list. Coastline from '
         '<a href="/sources">Natural Earth</a>, public domain.'
         + datacut_line()
         + offframe_line(sorted({project(it["city"]["lat"], it["city"]["lon"])
                                 for it in items}), data, listed=False))}
<!-- listed=False on the off-frame note: the drawing plots every place in
     the Atlas with an experience, and the body under it shows twenty-four
     of the 197 — so "that place is in the list below" pointed at a list
     that does not hold the place it names. Found by the check written for
     the 404, on a page the 404's own fix would have walked past. -->
<!-- "Recently added" WAS A CLAIM THE DATA CANNOT SUPPORT. An experience
     carries a slug, a name, a kind, a band and a summary, and no date of
     any sort, so these 24 were simply the first 24 the loader returned in
     country order — Austria to Croatia, called recent. A false ordering is
     worse than none, because a reader takes it for a signal. -->
{section("Twenty-four of them", f'<div class="rows">{rows}</div>',
         lede="What people actually do, in country order — there is no date on an "
              "experience here, so this is a sample and not a recency. Every one is a "
              "real, named thing in a real place, and every one links to the page of "
              "the place it happens in.",
         more=("How this list is cut", "#kinds"))}

<!-- THE TWO AXES CAME AFTER THE EXPERIENCES, and the order is the whole
     change. The page opened on eighteen taxonomy rows — eight categories,
     then ten kinds, both as bar charts — so a reader met the information
     architecture before a single thing anybody does. That is design to the
     data's shape rather than to the reader's purpose, and this page's own
     head says its subject is "what people actually do here".
     The bars are kept: Family holds 131 entries and Luxury holds 5, and
     that difference is real and is the argument for having two axes at all.
     They are now the answer to "how is this list cut", asked after the
     list. -->
{section(f"{numword(len(data['categories'])).capitalize()} categories", '<div class="rows">' + "".join(catcards) + "</div>",
         tone="quiet",
         lede=f"What an experience is about, largest first. An experience may be in "
              f"several of these at once — {len(data['categories'])} categories hold "
              f"{sum(catn.values())} memberships across {len(items)} experiences — so each "
              f"bar is drawn against the largest category rather than against the total. "
              f"Each row carries three of its own entries, and each category page prints the "
              f"rule that built it.")}
{section(f"{numword(len(kinds)).capitalize()} kinds", '<div class="rows">' + "".join(cards) + "</div>",
         tone="quiet",
         lede=f"The other axis: what you physically do. A cellar visit and a cathedral are "
              f"both sacred to somebody; only one of them is a walk. These do not overlap — "
              f"every experience has exactly one kind, and the {len(kinds)} of them account "
              f"for all {sum(counts.values())}.")}
"""
    return "/experiences/index.html", page(
        "Experiences", body, path="/experiences", area="experiences",
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
    # The kind is not printed on a kind page: every row on it is that kind
    # by definition, which is the constraint explained back.
    rows = "".join(
        f"""<li class="invite"><a href="{urls.city(it['country'], it['region'], it['city'])}">
        <h2>{esc(it['exp']['name'])}</h2>
        <p class="invite-sum">{esc(it['exp']['summary'])}</p>
        <p class="invite-where">{esc(it['city']['name'])}, {esc(it['country']['name'])}
        · {esc(it['exp']['band'])}</p></a></li>"""
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
    return f"/experiences/kind/{kind}/index.html", page(
        name, body, path=urls.experience_kind(kind), area="experiences",
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
    <p>Paid tiers buy presentation on directory surfaces. They never buy Atlas ranking,
    Journey Planner weighting, or a place in a curated journey. If that wall ever moves, it
    moves in public, on this page.</p>
    <h2 class="mini">Claiming a profile</h2>
    <p>Not open yet — same reason as <a href="/experiences/join">listings</a>.</p>
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

    body = f"""
{crumbs([("Europe", "/discover"), ("Fund", None)])}
<div class="pagehead index">
  <p class="kicker">Europe Fund</p>
  <h1>What travel leaves behind.</h1>
  <p class="lede">Tourism arrives in a place and takes something out of it — a path, a language,
  a harbour wall, a summer. The Fund is the mechanism for putting something back:
  {len(data['fund'])} projects, listed publicly, with the local partner named on each.</p>
</div>

<div class="note sourced">
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
    c = data["countries"][p["country"]]
    body = f"""
{crumbs([("Europe", "/discover"), ("Fund", "/fund"), (p["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">{esc(p['theme'])} · {esc(c['name'])}</p>
  <h1>{esc(p['name'])}</h1>
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
    return ('<svg class="constel-defs" width="0" height="0" aria-hidden="true" '
            'focusable="false"><defs><g id="constel-eu">'
            + ours + "</g></defs></svg>")


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
    return (
        f'<header class="pagehead index ihero{" wide" if figure else ""}">'
        f'<div class="iherotext"><p class="kicker">{kicker}</p>'
        f'<h1>{title}</h1><p class="lede">{lede}</p>'
        f'{f"<div class=chips>{actions}</div>" if actions else ""}'
        f'{f"<p class=small>{note}</p>" if note else ""}</div>'
        f'{figure}</header>')


def region_glyph(members, frame=None, min_span=0.0):
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
    view = (glyph_view(frame, min_span=min_span) if frame
            else f"0 0 {MAP_W} {MAP_H}")
    return (f'<svg class="constel regionglyph" viewBox="{view}" '
            f'aria-hidden="true" focusable="false"><use href="#constel-eu"/>'
            f'{lit}</svg>')


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
    return (f'<svg class="constel countryglyph" viewBox="{view}" '
            f'aria-hidden="true" focusable="false">{lit}</svg>')


def glyph_view(pts, pad_frac=0.34, min_pad=90.0, min_span=340.0):
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
    want = MAP_W / MAP_H
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


def constellation(pts, extra="", route=False, frame=False):
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
    dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}"/>' for x, y in pts)
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
    view = glyph_view(pts) if (frame and pts) else f"0 0 {MAP_W} {MAP_H}"
    return (f'<svg class="constel{extra}" viewBox="{view}" '
            f'aria-hidden="true" focusable="false"><use href="#constel-eu"/>'
            f'{line}<g class="constel-lit">{dots}</g></svg>')


def themes_index(data):
    """Thirteen themes, shown by how far each one reaches.

    "8 PLACES" WAS ON ALL THIRTEEN CARDS AND IS NOT INFORMATION. Every theme
    in this dataset holds exactly eight stops, so the one figure the card grid
    printed was a constant wearing the clothes of a measurement. That is the
    /europe-in failure one family over: a number that is not the set\'s own
    extent reads as one.

    What actually separates them is REACH. Renaissance Europe is Italy, France
    and Belgium; Thermal Europe is the United Kingdom, Hungary, Iceland,
    Finland, Bulgaria, Azerbaijan and Georgia. Three countries against seven is
    the difference between a corner of the continent and an argument that
    crosses the whole of it, and the grid showed neither — it showed a
    generated landscape, and a theme is not a place: it has no coastline, no
    topography and no season, which is the same reason the twelve motions lost
    theirs.

    So the row carries the eight destinations and the count of countries.

    A COMMA WAS THE FIRST SEPARATOR AND THREE PLACE NAMES CONTAIN ONE.
    "Victoria, Gozo", "Mestia, Svaneti" and "Nida, Curonian Spit" are single
    destinations in this atlas, so Island Europe\'s eight places read as nine
    and Mountain Europe\'s as nine — a list that miscounts itself, on the one
    index whose whole argument is a count. The comma was chosen to stop the
    list reading as a route, which the middot on /journeys deliberately does;
    what actually distinguishes the two families is the ROUTE LINE under a
    journey\'s stops, and a theme has none — the same absence the theme page
    makes its point out of by drawing these dots with no path between them.
    """
    idx = data["cities"]
    # THE CONSTELLATION, WHICH IS THE WHOLE ARGUMENT DRAWN.
    #
    # The card grid was replaced with rows and the rows were a wall of small
    # grey text — a generic list traded for a generic grid, which is two
    # defaults and no art direction. A contact sheet of twelve families made
    # that unarguable: eleven of them open with a kicker, a serif h1, a lede
    # and a large arched map in the same position, and this index was one of
    # the two cells that were simply text.
    #
    # What distinguishes thirteen themes is REACH, and reach is a shape. So
    # each row draws its own eight destinations on a coarse silhouette of the
    # continent: Renaissance Europe is a tight knot over Italy and France,
    # Thermal Europe is a line from Iceland to the Caucasus. You see the
    # difference before you read a word, which is the thing a list of country
    # names cannot do.
    #
    # NOT AN APERTURE. It is 150 units wide and there are thirteen of them on
    # one page; the door at that size, thirteen times, is the signature as
    # wallpaper, which is the failure the events band already refused. This
    # is a glyph, not a window.
    #
    # The silhouette is emitted ONCE and every row is a <use> of it, so
    # thirteen constellations cost one coastline and 104 dots.
    silhouette = constel_defs()

    # DERIVED, because the note under the list states it. Every theme holds
    # eight stops today; a hard-coded eight in the prose is the figure that
    # was true two hundred destinations ago, which this repository has
    # already shipped once.
    sizes = sorted({len(t["stops"]) for t in data["themes"]})
    say = numword

    held = (f"every one of these holds {say(sizes[0])}" if len(sizes) == 1
            else f"they hold between {say(sizes[0])} and {say(sizes[-1])}")
    rows = []
    for t in data["themes"]:
        countries, places = [], []
        for stop in t["stops"]:
            n = idx[stop["city"]]
            cn = n["country"]["name"]
            if cn not in countries:
                countries.append(cn)
            places.append(esc(n["city"]["name"]))
        glyph = constellation(
            [project(idx[st["city"]]["city"]["lat"], idx[st["city"]]["city"]["lon"])
             for st in t["stops"]], extra=" constel-theme")
        rows.append(
            f'<a class="row themerow" href="/themes/{t["slug"]}">'
            f'<div><p class="kicker">{esc(t["strapline"])}</p>'
            f'<h3>{esc(t["name"])}</h3>'
            f'<p class="rowsub">{" · ".join(places)}</p></div>'
            f'<div class="themeside">{glyph}'
            f'<p class="rowmeta">{len(countries)} '
            f'{"countries" if len(countries) != 1 else "country"}</p></div></a>')
    body = f"""
{crumbs([("Europe", "/discover"), ("Themes", None)])}
<div class="pagehead index">
  <p class="kicker">Discovery without a map of borders</p>
  <h1>Europe, organised by what you came for.</h1>
  <p class="lede">Medieval Europe is not a country. Neither is sacred Europe, or Viking Europe,
  or the Europe you reach only by train. {len(data['themes'])} of them cut across the Atlas,
  and each place under one of them stays linked to the country it is actually in.</p>
</div>
{silhouette}
<div class="rows">{"".join(rows)}</div>
<p class="small">Each shape beside a theme is that theme\u2019s own eight places on the
continent, drawn to the same frame so the thirteen can be compared: a knot is an
argument about one corner of Europe, a scatter is one about the whole of it.
{geo.sources_line(geo.load("europe-lod0.json"))}
The places under each theme are not in travelling order, and
the number beside them is how many countries the theme crosses rather than how
many places it holds — {held}. For an order that
respects distance, put the ones you want into the <a href="/plan">Planner</a>.</p>
"""
    return "/themes/index.html", page(
        "Themes", body, path="/themes", area="countries",
        description="Cross-border ways into Europe: medieval, sacred, Viking, alpine, maritime and rail Europe, each a real sequence of places.",
    )


def theme_page(data, t):
    idx = data["cities"]
    rows = []
    for stop in t["stops"]:
        n = idx[stop["city"]]
        rows.append(
            f"""<a class="row" href="{urls.city(n['country'], n['region'], n['city'])}">
            <div><h3>{esc(n['city']['name'])}</h3><p class="rowsub">{esc(stop['why'])}</p></div>
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
        f'not in travelling order. Coastline from '
        f'<a href="/sources">Natural Earth</a>, public domain.',
        f'Map of the {len(tpts)} places in {t["name"]}, unlinked') if len(tpts) >= 2 else ""

    body = f"""
{crumbs([("Europe", "/discover"), ("Themes", "/themes"), (t["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">{esc(t['strapline'])}</p>
  <h1>{esc(t['name'])}</h1>
  {statement(t['summary'])}
  <p class="orient">{len(t['stops'])} places across {len(countries)}
  {"countries" if len(countries) != 1 else "country"} · not an itinerary</p>
  {chips(t["interests"], data["interests"])}
</div>

{thememap}

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
        description=t["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
    )


# ── stories ───────────────────────────────────────────────────────────

def stories_index(data):
    # NINE THREE-COLUMN GRIDS, EACH CONTAINING ONE CARD.
    #
    # The page was built from the DESK TAXONOMY rather than from what a
    # reader is doing. Nine desks, one story each, so nine <h2> bands and
    # nine grids of one — a 280px card alone in a 1,168px row with 888
    # pixels of white beside it, nine times, over 5,792 pixels of page. The
    # rule this repository already states is "design to purpose, not to data
    # shape", and the shape of the data was the whole layout.
    #
    # AND EVERY ONE OF THEM DREW AN ILLUSTRATION CHOSEN BY HASH. The other
    # rule this repository already states is that a story is not a place and
    # its picture may not be drawn from a hash — that is why the story PAGE
    # opens on a storymap of its own validated places. The index went on
    # picking a landscape from the slug for all nine, which is the same
    # failure the rule was written for, one page over.
    #
    # Nine essays is a contents page. The desk becomes a kicker on the piece
    # it belongs to, which is what it always was — a property of the story,
    # not a heading over one — and the date and the reading time are what a
    # reader actually chooses on.
    sections = sorted({s["section"] for s in data["stories"]})
    byline = sorted(data["stories"],
                    key=lambda s: (s["published"], s["title"]), reverse=True)
    # AND THE CONTENTS PAGE LEFT ITS MIDDLE THIRD EMPTY. Rewriting nine
    # one-card grids as one list was right and only half the job: what
    # replaced the nine hash-drawn landscapes was nothing at all, so the row
    # ran a title and a standfirst down the left and a date 550 pixels away on
    # the right. Measured on the built page, the median horizontal band used
    # 46% of the column.
    #
    # A STORY'S PICTURE IS ITS OWN PLACES, WHICH IS THE RULE THAT REMOVED THE
    # PLATES RATHER THAN AN EXCEPTION TO IT. The story page already opens on
    # exactly that, drawn from the validated `places` field; this is the same
    # derivation at glyph size. It cannot be wrong about its subject because
    # it is made of it — and it is the one thing that tells these nine apart
    # before a word is read. "The languages with no relatives" is San
    # Sebastián, Budapest, Helsinki and Tbilisi, corner to corner; "the city
    # rebuilt from paintings" is Warsaw, Dresden and Rotterdam, a knot. That
    # difference IS the piece.
    #
    # Not the hash, and not a photograph either: the register holds none, and
    # a story is the family where an illustration of nowhere did real damage
    # — the essay about the last unlogged forest in Europe opened on tower
    # blocks for a year.
    idx = data["cities"]
    def glyph(s):
        pts = []
        for cid in s.get("places") or ():
            n = idx.get(cid)
            if n:
                pts.append(project(n["city"]["lat"], n["city"]["lon"]))
        # A story that names no place gets no drawing, on the destination
        # page's rule: nothing in its place rather than something invented.
        return constellation(pts, extra=" constel-theme", frame=True) if pts else ""
    # A LEAD, AND THEN THE REST. Nine identical rows with a 132px grey Europe
    # at the right-hand end is a contents page with a decoration on it: the
    # glyph was too small to name a place, the text stopped at a third of the
    # column, and the newest piece looked exactly like the ninth. An index of
    # nine essays has room to say which one to read first, and the answer is
    # the newest — a date, not a judgement.
    #
    # The lead's own places are drawn at size, which is the treatment the
    # story page and the homepage both already use for this family. The other
    # eight keep the row, and lose the glyph: at 132px it said nothing, and
    # eight of them said nothing eight times.
    # THE OPENING DRAWS EVERY PLACE THE NINE PIECES ARE SET IN. That is the
    # family's own subject at size and it is the same derivation the story
    # page and the homepage already use — never a plate, which is the rule
    # this family exists to demonstrate.
    allplaces = []
    for st in byline:
        for cid in st.get("places") or ():
            if cid in idx:
                allplaces.append(project(idx[cid]["city"]["lat"], idx[cid]["city"]["lon"]))
    lead, rest = byline[0], byline[1:]
    desks = (
        f'<a class="storylead storyleadwide" href="{urls.story(lead)}">'
        f'<div class="storyart">{glyph(lead)}</div>'
        f'<div><p class="kicker">{esc(lead["section"])} · {esc(lead["reading"])} · '
        f'{esc(lead["published"])}</p>'
        f'<h3>{esc(lead["title"])}</h3>'
        f'<p class="rowsub">{esc(lead["standfirst"])}</p>'
        f'<p class="doorgo">Read the story →</p></div></a>'
        '<div class="rows">' + "".join(
            f'<a class="row storyrow" href="{urls.story(s)}">'
            f'<div><p class="kicker">{esc(s["section"])}</p>'
            f'<h3>{esc(s["title"])}</h3>'
            f'<p class="rowsub">{esc(s["standfirst"])}</p></div>'
            f'<p class="rowmeta">{esc(s["published"])}<br>'
            f'<span class="small">{esc(s["reading"])}</span></p></a>'
            for s in rest
        ) + "</div>")
    body = f"""
{crumbs([("Europe", "/discover"), ("Stories", None)])}
{constel_defs()}
{indexhero(
    kicker="Stories",
    title="A continent is people before it is places.",
    lede=f"{len(data['stories'])} pieces across {len(sections)} desks — people, history, "
         f"food, faith, nature and culture. Every story links into the Atlas, and every "
         f"Atlas page that a story touches links back, so reading and planning are the "
         f"same motion.",
    art=constellation(allplaces),
    img=photo(data.get("images"), "stories-hero", w=2000, h=1200,
              sizes="(min-width: 60rem) 52vw, 100vw"),
    note='Every place these nine pieces are set in, on one frame. Coastline from '
         '<a href="/sources">Natural Earth</a>, public domain.'
         + datacut_line())}
{desks}
<p class="small">The shape above the lead piece is the places it is about, drawn
on the same projection as every other map here — and the same reason there is no
other picture on this page: a story is not a place, and a landscape chosen for it
by chance once put tower blocks above an essay on the last unlogged forest in
Europe. Coastline from <a href="/sources">Natural Earth</a>, public domain.</p>
"""
    return "/stories/index.html", page(
        "Stories", body, path="/stories", area="stories",
        description="Editorial from across Europe: people, history, food, faith, nature and culture, each linked into the Atlas.",
    )


def story_page(data, s):
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
    storyart = (f'<div class="card-art frame">'
                + picture(data["images"], "story:" + s["slug"], w=1260, h=540,
                          alt=s["title"], eager=True,
                          sizes="(min-width: 76rem) 76rem, 100vw")
                + '</div>') if has_photo else storymap(data, s)
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
    body = f"""
{crumbs([("Europe", "/discover"), ("Stories", "/stories"), (s["title"], None)])}
<article class="essay">
<div class="essayhead">
  <p class="kicker">{esc(s['section'])} · {esc(s['reading'])}</p>
  <h1>{esc(s['title'])}</h1>
  <p class="deck">{esc(s['standfirst'])}</p>
  <p class="byline">By {esc(s['author'])} · published
  <time datetime="{esc(s['published'])}">{esc(s['published'])}</time>{updated}</p>
</div>
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
             "url": f"https://europedoor.com/stories/{s['slug']}",
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


def maplist(data):
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
    return (f'<details class="maplist" id="maplist">'
            f'<summary>Every place on this map, as a list '
            f'({len(data["cities"])} places, grouped by region)</summary>'
            f'<p class="small">The map above is a picture and cannot be read out. This is the '
            f'same data as text, with coordinates, and it is the accessible alternative — not '
            f'a reduced version of it.</p>{"".join(blocks)}</details>')


def map_page(data):
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
    body = f"""
{crumbs([("Europe", "/discover"), ("Map", None)])}
<div class="pagehead instrument">
  <p class="kicker">The map</p>
  <h1>Europe, and everything we hold in it.</h1>
  {head_extent([(len(data['countries']), 'countries'),
                (len(data['cities']), 'destinations'),
                (len(placedots), 'places')])}
  <p class="lede">Click a country to go into it.</p>
</div>
<div class="mapstage">
<div class="mapmain">
<div class="mapzoom">
  <button type="button" class="zbtn" id="zoomin" aria-label="Zoom in">+</button>
  <button type="button" class="zbtn" id="zoomout" aria-label="Zoom out">−</button>
  <button type="button" class="zbtn wide" id="zoomreset">Whole of Europe</button>
  <span class="small" id="zoomwhere" aria-live="polite"></span>
</div>
<div class="mapwrap">
<svg viewBox="0 0 {MAP_W} {MAP_H}" id="europemap" class="europemap" data-role="instrument" role="img" aria-describedby="maplist" aria-label="Map of Europe showing every country, destination and place in the Atlas">
<rect width="{MAP_W}" height="{MAP_H}" fill="none"/>
<g id="context" class="context" aria-hidden="true">{''.join(context)}</g>
<g id="countries" class="countries">{''.join(shapes)}</g>
<g id="detail" class="countries"></g>
{cut_fade('map', MAP_W, MAP_H)}
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

<details class="maptools">
  <summary>Layers, overlays and how to read the map</summary>
  <div class="maphint">
    <ul class="legend">
      <li><span class="sw land"></span> A country in the Atlas — click it to open the panel,
        click again to go to its page</li>
      <li><span class="sw ctx"></span> Land outside the Atlas, drawn so the coast has a far
        shore</li>
      <li><span class="sw dest"></span> A destination we have written</li>
      <li><span class="sw ring"></span> A country too small to draw at this scale — Monaco and
        Vatican City, and four more at the widest zoom</li>
    </ul>
    <p class="small">Drag to pan, scroll or use + and − to zoom. Zooming past 1.6× loads a finer
    coastline; opening a country loads that country's own.</p>
  </div>
  <div class="maplayers">
    <fieldset id="geolayers">
      <legend class="mini">Geography</legend>
      <label><input type="checkbox" name="geo" value="borders" checked> Borders</label>
      <label><input type="checkbox" name="geo" value="regions"> Regions</label>
      <label><input type="checkbox" name="geo" value="cities" checked> Destinations</label>
      <label><input type="checkbox" name="geo" value="places"> Places ({len(placedots)})</label>
    </fieldset>
  </div>
  <p class="mini">What each destination is for</p>
  <div class="checks" id="layers">{filters}</div>
  <div class="form-row mw34">
    <div class="field">
      <label for="journeylayer">Draw a journey over it</label>
      <select id="journeylayer"><option value="">None</option>{joptions}</select>
    </div>
    <div class="field">
      <label for="mapfrom">Measure distances from</label>
      <select id="mapfrom"><option value="">Nowhere in particular</option>{fromoptions}</select>
    </div>
  </div>
  <p class="small" id="mapcount"></p>
</details>
{jsondata("europedoor-journeys", jdata)}
{jsondata("europedoor-mapinfo", info)}
{jsondata("europedoor-countries", cinfo)}
{jsondata("europedoor-projection", projinfo)}
{jsondata("europedoor-projection-probe", projprobe)}
<div class="note">
  <h2 class="mini">What this drawing is and is not</h2>
  <p>The land comes from <strong>{esc(attribution)}</strong>, which is in the public domain and
  which we host ourselves: the file your browser drew this from is on our own servers, fetched
  once by a script in this repository, hashed, and committed. There is no map account behind it
  and no per-view bill, and that is a deliberate architectural choice rather than a stage we
  have not reached yet.</p>
  <p>It is a <strong>cartographic</strong> source, not a legal one. It is built to look right at
  a stated scale, and at the scale of a whole continent a border is a line a few kilometres
  wide. Do not read a disputed frontier off this map. Two countries in the Atlas — Monaco and
  Vatican City — have no shape here at all, because at 1:50 million they are smaller than a
  pixel; they are drawn as a ringed point instead of a polygon we made up.
  <a href="/method#map">How the map is built</a>.</p>
  <p>Projection: a <strong>Lambert conformal conic</strong> on the angles the EU publishes
  pan-European maps at — standard parallels {geo.LCC_P1:g}°N and {geo.LCC_P2:g}°N, origin
  {geo.LCC_LAT0:g}°N, central meridian {geo.LCC_LON0:g}°E. Conformal means shape is preserved
  everywhere: a country is the shape it is, at any latitude on this map. Regions are shown by
  the destinations that belong to them, not as boundaries — we hold which region a place is in,
  and we do not hold region geometry.</p>
</div>

{maplist(data)}
"""
    return "/map/index.html", page(
        "Map", body, path="/map", area="countries",
        description="A point map of every city in the EuropeDoor Atlas, filterable by what you travel for. No third-party tiles.",
        scripts=["/assets/js/map.js"], wide=True,
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
    names = data["taxonomy"]["month_names"]
    by_month = {m: [] for m in data["taxonomy"]["months"]}
    for c in data["countries"].values():
        for f in c["festivals"]:
            by_month[f["month"]].append((f, c))
    # THE INDEX PRINTED THE WHOLE YEAR AND RAN TO FIFTEEN SCREENS.
    #
    # Twelve <h2> bands, one per month, each holding every fixture in it:
    # 197 rows, 14,875 pixels, and no reader has ever reached December. It is
    # the catalogue failure in its purest form — the shape of the data as the
    # whole layout — and it was worse here than anywhere, because the family's
    # subject is TIME and the one thing the page could not show was the year.
    #
    # The year band above already answers "when should I go", which is the
    # question an events index exists for. So the twelve months are twelve
    # entries rather than twelve dumps: how many fixed points, how many
    # countries are in their quieter shoulder, and a link to the month, which
    # is where the fixtures and their filter live. Every figure is derived.
    #
    # NO SELECTION. "The three best festivals in June" would be a ranking
    # this atlas does not hold, and three rows out of twenty-eight presented
    # as a taste is a ranking wearing a smaller hat. The count is the taste.
    shoulder = {m: sum(1 for c in data["countries"].values()
                       if m in (c.get("season") or {}).get("shoulder", []))
                for m in data["taxonomy"]["months"]}
    most = max((len(v) for v in by_month.values()), default=1) or 1
    monthrows = "".join(
        f"""<a class="row monthrow" href="/events/{esc(m)}">
        <div><h3>{esc(names[m])}</h3>
        <p class="rowsub">{len(by_month[m])} fixed point{"" if len(by_month[m]) == 1 else "s"} ·
        {shoulder[m]} countr{"y" if shoulder[m] == 1 else "ies"} in their quieter shoulder</p>
        <div class="hopbar"><span class="w{min(100, round(len(by_month[m]) / most * 100 / 5) * 5)}"></span></div></div>
        <p class="rowmeta">Where to go in {esc(names[m])} →</p></a>"""
        for m in data["taxonomy"]["months"]
    )
    blocks = [f'<div class="rows monthrows">{monthrows}</div>']
    # The twelve chips this replaces were the same width and the same weight
    # whether the month held 3 fixtures or 28. See year_band().
    jump = year_band(data)
    total = sum(len(v) for v in by_month.values())
    kindcounts = {}
    for v in by_month.values():
        for f, _ in v:
            kindcounts[f["kind"]] = kindcounts.get(f["kind"], 0) + 1
    kindfilters = "".join(
        f'<label><input type="checkbox" name="eventkind" value="{esc(k)}"> '
        f'{esc(EVENT_KIND_NAMES[k])} ({n})</label>'
        for k, n in sorted(kindcounts.items(), key=lambda kv: -kv[1])
    )
    body = f"""
{crumbs([("Europe", "/discover"), ("Events", None)])}
{indexhero(
    kicker="The European year",
    title="What is on, and when.",
    lede=f"{total} recurring fixtures — festivals, markets, pilgrimages, harvests and the "
         f"handful of natural events worth planning a year around. These are the annual, "
         f"dependable ones. Dated listings for a given year need a live events feed, "
         f"which is Stage 2.",
    img=photo(data.get("images"), "events-hero", w=2000, h=1200,
              sizes="(min-width: 60rem) 52vw, 100vw"))}
<!-- NO DRAWING IN THE OPENING, AND THAT IS THE ONE EXCEPTION. Four of the
     five indexes put their subject in the arch beside the headline; this
     family's subject is TIME, and the year band under this head is a
     twelve-column chart that has to run the full width to be read at all —
     the same reason it is not an aperture. Squeezing it into a 4:3 opening
     would be the signature applied for its own sake. So the hero is type
     until a photograph lands in its slot, and the chart immediately under
     it is the dominant visual the section needs. -->
{jump}
{''.join(blocks)}
<p class="small">Every fixture is on its month's page, with the category filter
beside it — {total} of them across {len(kindcounts)} categories. They are the
annual, dependable ones; a dated listing for a given year needs a live events
feed, which is Stage 2.</p>
"""
    return "/events/index.html", page(
        "Events", body, path="/events", area="events",
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
        frame=True) if qshown else ""
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
               f'destination this atlas holds, and those are the ones drawn. '
               + (f'The other {rest} '
                  f'{"are" if rest != 1 else "is"} in the list below: a season, '
                  f'a region or a whole country is not a point, and pinning '
                  f'one to a capital to fill the map would be inventing a '
                  f'location. ' if rest else '')
               + f'Coastline from <a href="/sources">Natural Earth</a>, public '
                 f'domain. <a href="/map">The full map →</a>')
        monthmap = pointsmap(pts, "ev" + month, cap,
                             f'Map of the {len(mapped)} fixtures in {name} that '
                             f'happen in a destination in the Atlas')

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
    quiet = [n for n in data["cities"].values() if n["city"].get("quiet")]
    quiet.sort(key=lambda n: (n["country"]["name"], n["city"]["name"]))
    # ONE HUNDRED AND THIRTY ABSTRACT PLATES ON ONE PAGE, directly under a
    # map whose whole argument is WHERE these places are. The map answers
    # the question and the grid beneath it answered nothing: a hash-drawn
    # landscape per destination, 130 of them, on the page that exists to say
    # a Galician fishing town gets the same treatment as Paris. A
    # destination here is chosen on where it is and what it is like, and
    # neither of those is a look, which is the test a card has to pass.
    # A HUNDRED AND THIRTY ROWS IN ONE COLUMN, FIFTEEN THOUSAND PIXELS LONG.
    #
    # Sorted by country with nothing marking where one ended, which is the
    # order this page had and could not show — the interest pages had exactly
    # this and were grouped by macro region for exactly this reason. The
    # drawing above is the argument, a distribution across the continent, and
    # the list under it then asked a reader to scroll a hundred and thirty
    # names to find out which part of Europe any of them is in.
    #
    # Grouped by macro region, in the taxonomy's own order, so the list has
    # the same nine divisions the picture above it has.
    by_macro = {}
    for n in quiet:
        by_macro.setdefault(_macro_of(data, n["country"]["slug"]), []).append(n)
    rows = "".join(
        f'<div class="rowgroup"><p class="rowgrouphead">{esc(m["name"])}'
        f'<span class="rowgroupn">{len(by_macro[m["slug"]])}</span></p>'
        + "".join(
            f'<a class="row" href="{urls.city(n["country"], n["region"], n["city"])}">'
            f'<div><h3>{esc(n["city"]["name"])}</h3>'
            f'<p class="rowsub">{esc(n["city"]["summary"])}</p></div>'
            f'<p class="rowmeta">{esc(n["country"]["name"])} · '
            f'{esc(n["region"]["name"])}</p></a>'
            for n in by_macro[m["slug"]])
        + "</div>"
        for m in data["macros"] if m["slug"] in by_macro)
    # THE ARGUMENT OF THIS PAGE IS A DISTRIBUTION, AND IT WAS PROSE.
    #
    # "Too many visitors in the same eleven places" is a claim about where
    # people are NOT. The quiet tag is on 89 destinations in 40 countries and
    # the page listed them as cards, which shows how many and not where —
    # and where is the entire point: the alternative to Santorini is not "a
    # quieter island", it is a specific set of dots spread across a
    # continent that a reader can see is nowhere near the eleven places.
    qpts = [(*project(n["city"]["lat"], n["city"]["lon"]),
             urls.city(n["country"], n["region"], n["city"]), n["city"]["name"])
            for n in quiet]
    quietmap = pointsmap(
        qpts, "quiet",
        f'Every destination carrying the quiet tag: {len(quiet)} of '
        f'{len(data["cities"])}, in '
        f'{len({n["country"]["slug"] for n in quiet})} countries. The tag is '
        f'editorial and we will be wrong sometimes. Names are dropped where '
        f'they would overlap; every dot is a link. Coastline from '
        f'<a href="/sources">Natural Earth</a>, public domain.'
        + offframe_line([project(n["city"]["lat"], n["city"]["lon"])
                         for n in quiet], data),
        f'Map of the {len(quiet)} destinations tagged quiet') if len(qpts) >= 2 else ""

    swaps = "".join(
        f"""<div class="row"><div><h3>{esc(a)}</h3><p class="rowsub">{esc(why)}</p></div>
        <p class="rowmeta">try {esc(b)}</p></div>"""
        for a, b, why in [
            ("Paris in July", "Paris in October", "Same city, half the queue, and the light is better."),
            ("The Amalfi Coast in August", "Puglia's Adriatic side in June", "A coast that still belongs to the people who live on it."),
            ("Santorini at sunset", "Naxos or Sifnos, any evening", "The Cyclades without the cruise schedule."),
            ("Dubrovnik in high summer", "The Kvarner islands in May", "Walled towns exist all down that coast."),
            ("Reykjavík's Golden Circle", "The Westfjords", "Six hours further and a different country."),
            ("Barcelona in August", "Girona and the Empordà", "An hour by train from the thing everyone else is queueing for."),
        ]
    )
    body = f"""
{crumbs([("Europe", "/discover"), ("Beyond the obvious", None)])}
<div class="pagehead index">
  <p class="kicker">Responsible travel, stated plainly</p>
  <h1>Beyond the obvious.</h1>
  <p class="lede">Europe's problem is not too many visitors; it is too many visitors in the same
  eleven places in the same six weeks. Every part of this platform is built to push the other
  way — the Planner rewards shoulder months, the Atlas gives a Galician fishing town the same
  page template as Paris, and these {len(quiet)} places are where it would send you
  instead.</p>
</div>
{quietmap}
{section(f"{len(quiet)} places we would send you instead", f'<div class="rows">{rows}</div>',
         lede="Tagged quiet in the dataset: places with the goods and without the crowd. The tag is editorial and we will be wrong sometimes.")}
{section("Six straight swaps", f'<div class="rows">{swaps}</div>',
         lede="Same idea, different pressure.")}
<div class="note">
  <h2 class="mini">The rule we hold ourselves to</h2>
  <p>No page on this site tells you a place is undiscovered. Publishing that sentence is what
  ends it. What we will say is when to come, how to arrive without a car where that is possible,
  and who locally is worth your money.</p>
</div>
"""
    return "/beyond-the-obvious/index.html", page(
        "Beyond the obvious", body, path="/beyond-the-obvious", area=None,
        description="Europe's quieter alternatives, shoulder-season travel and straight swaps for the eleven places everyone goes at once.",
    )


# ── my europe ─────────────────────────────────────────────────────────

def my_europe_page(data):
    body = f"""
{crumbs([("Europe", "/discover"), ("My Europe", None)])}
<div class="pagehead instrument">
  <p class="kicker">My Europe</p>
  <h1>The list you are building.</h1>
  <p class="lede">Saved places, saved journeys, saved stories. This lives in your browser and
  nowhere else — there is no account, no server, no email address, and nothing to leak. When
  accounts arrive, this list will be importable into one; it will never be silently uploaded.</p>
</div>
<div id="mine" aria-live="polite"></div>
<div id="dna"></div>
<div class="note">
  <h2 class="mini">Where this goes next</h2>
  <p>The account version adds sync across devices, a shareable public list, and the ability to
  hand a saved list straight to the Planner as a set of must-visit stops. All three need a
  backend, a privacy notice and a data controller — see <a href="/how-it-works">how it works</a>.</p>
</div>
"""
    return "/my-europe/index.html", page(
        "My Europe", body, path="/my-europe", area=None,
        description="Your saved European places, journeys and stories — stored in your own browser, with no account and no server.",
        scripts=["/assets/js/my-europe.js"],
        # INTELLIGENCE — personalisation and saved journeys
        world="intelligence"
    )


def method_page(data):

    # Published on /method because the map is now a claim about the world and
    # a claim republished without its provenance is a claim nobody can check.
    # Built before the page body rather than inside it: the body is one big
    # f-string, and a nested triple-quoted f-string closes it early — which is
    # a syntax error two hundred lines further down, in a place that has
    # nothing to do with the mistake.
    maprows = "".join(
        f'<div class="row"><div><h3>{esc(h)}</h3><p class="rowsub">{b}</p></div>'
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
        return (f'<span class="rowdist">'
                f'<svg class="dist" viewBox="0 0 100 12" role="img" aria-hidden="true" '
                f'preserveAspectRatio="none">'
                f'<rect class="distaxis" x="0" y="5" width="100" height="2"/>'
                f'<rect class="distspan" x="{lo}" y="2" width="{hi - lo}" height="8"/>'
                f'<rect class="distmed" x="{med - 0.6:.1f}" y="0" width="1.2" height="12"/>'
                f'</svg>'
                f'<span class="distnum">{lo}–{hi}, median {med}</span></span>')

    rows = "".join(
        f'<div class="row"><div><h3>{esc(name)}</h3><p class="rowsub">{esc(formula)}</p></div>'
        f'<p class="rowmeta">{distbar(key)}</p></div>'
        for key, name, formula in methodology_rows()
    )
    refused = "".join(
        f'<div class="row"><div><h3>{esc(name)}</h3><p class="rowsub">{esc(why)}</p></div>'
        f'<p class="rowmeta">not computed</p></div>'
        for name, why in REFUSED.items()
    )
    discrows = "".join(
        f'<div class="row"><div><h3>{esc(name)}</h3><p class="rowsub">{esc(why)}</p></div>'
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

<div class="note sourced">
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
        ("Europe Atlas", f"{len(data['countries'])} countries, {sum(len(c['regions']) for c in data['countries'].values())} regions, {len(data['cities'])} cities, all generated from one dataset", "built"),
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
  <p class="manifesto-close">EuropeDoor opens the way.<br>Come discover what lies beyond.</p>
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
        <h3><code>{esc(u)}</code></h3>
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

<div class="note sourced">
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
    art=constellation(pts),
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


def sitemap(paths):
    urlset = "".join(
        f"<url><loc>https://europedoor.com{p}</loc></url>" for p in sorted(paths)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + urlset + "</urlset>\n"
    )

# ── search ────────────────────────────────────────────────────────────

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

    kinds = {}
    for row in E:
        kinds[row[2]] = kinds.get(row[2], 0) + 1

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
        for sub in cat.get("subs", []):
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


def search_page(data):
    n = (len(data["countries"]) + sum(len(c["regions"]) for c in data["countries"].values())
         + len(data["cities"]) + len(data["journeys"]) + len(data["themes"])
         + len(data["stories"]) + len(data["fund"]))
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
    kinds = [
        (len(data["countries"]), "countries", "/countries",
         "Every country the Atlas holds a page for"),
        (sum(len(c["regions"]) for c in data["countries"].values()),
         "travel regions", "/countries", "Groupings by coast, range and shared history"),
        (len(data["cities"]), "destinations", "/discover",
         "Cities, villages, valleys, islands and sites"),
        (len(data["journeys"]), "journeys", "/journeys",
         "Cross-border routes, in order, with the nights counted"),
        (len(data["themes"]), "themes", "/themes",
         "Ways through Europe that ignore its borders"),
        (len(data["stories"]), "stories", "/stories",
         "The editorial desk, each piece linked into the Atlas"),
        (len(data["fund"]), "Fund projects", "/fund",
         "The public register of work worth putting something back into"),
    ]
    _kpeak = max(k[0] for k in kinds)
    # AN H2 ABOVE THE ROWS, BECAUSE A ROW'S NAME IS AN H3. The first version
    # put the rows straight under the page's h1 and the accessibility scan
    # caught it in one run: h1 → h3 at "Countries". Every other place this
    # primitive appears has a band heading over it, and the results that
    # replace this state announce themselves with an h2 too — so the resting
    # state and the state it becomes have the same shape.
    atrest = ('<h2>What is in the index</h2>'
              '<p class="lede">Everything below is searchable from the box '
              'above, and every kind is browsable without searching at all.</p>'
              '<div class="rows">'
              + "".join(
                  f'<a class="row" href="{href}">'
                  f'<div><h3>{esc(label[:1].upper() + label[1:])}</h3>'
                  f'<p class="rowsub">{esc(what)}</p></div>'
                  f'<p class="rowmeta">{count:,}<br>'
                  f'<span class="hopbar" aria-hidden="true">'
                  f'<span class="w{round(100 * count / _kpeak)}"></span></span></p></a>'
                  for count, label, href, what in kinds)
              + "</div>")

    body = f"""
{crumbs([("Europe", "/discover"), ("Search", None)])}
<div class="pagehead instrument">
  <p class="kicker">Search</p>
  <h1>Find it.</h1>
  {head_extent([(n, 'records indexed')])}
  <p class="lede">Everything on EuropeDoor — countries, regions, destinations, places,
  journeys, themes, stories and projects — in one index that runs in your browser.
  Nothing you type is sent anywhere, and nobody can buy a position in it.</p>
</div>
<form class="form" id="searchform" role="search">
  <div class="field">
    <label for="q">Search Europe</label>
    <input type="text" id="q" name="q" autocomplete="off" autofocus
           placeholder="quiet beaches in september · medieval castles near prague · cheap mountains">
    <p class="small">It reads more than words: <em>cheap</em> and <em>quiet</em> filter,
    a month narrows to places that are good in it, and <em>near Prague</em> means within
    300 kilometres of Prague. Whatever it understood is shown back to you as chips.</p>
  </div>
</form>
<div class="chips" id="searchunderstood" aria-live="polite"></div>
<div id="results" aria-live="polite">{atrest}</div>
<noscript><p class="small">Search needs JavaScript. The
<a href="/countries">Atlas</a> is fully browsable without it.</p></noscript>
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

def motion_match(data, m, cid, n):
    """Does one destination satisfy one motion? Returns (bool, reasons)."""
    c, r, t = n["country"], n["region"], n["city"]
    tags = set(t["interests"]) | set(r["interests"])
    why = []

    wants = m.get("interests", [])
    if wants:
        hit = [w for w in wants if w in tags]
        if m.get("all_interests"):
            if len(hit) != len(wants):
                return False, []
            why.append("carries " + and_list(
                [data["interests"][w]["name"] for w in wants]))
        else:
            if not hit:
                return False, []
            why.append("tagged " + and_list([data["interests"][w]["name"] for w in hit]))

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
    return out[0].upper() + out[1:]


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
    # hoisted into the query note; each row keeps only what distinguishes it.
    common = [c for c in (shown[0][1] if shown else [])
              if all(c in w for _n, w in shown)]
    rows = "".join(
        f"""<a class="row" href="{urls.city(n['country'], n['region'], n['city'])}">
        <div><h3>{esc(n['city']['name'])}</h3>
        <p class="rowsub">{esc(n['city']['summary'])}</p>
        {f'<p class="whythis">{esc(and_list([c for c in why if c not in common]))}.</p>'
         if [c for c in why if c not in common] else ""}</div>
        <p class="rowmeta">{esc(n['country']['name'])}<br><span class="small">
        {nights_line(n['city'])}</span></p></a>"""
        for n, why in shown
    )
    shared_note = (f'<p class="whyall"><span>All of them</span> {esc(and_list(common))}.</p>'
                   if common else "")

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
        f'Names are dropped where they would overlap; every dot is a link. '
        f'Coastline from <a href="/sources">Natural Earth</a>, public domain.',
        f'Map of the {len(shown)} destinations in {m["name"]}') if len(mpts) >= 2 else ""

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
        + constellation(_pts([l["city"] for l in j["legs"]]), route=True, frame=True)
        + '</div></a>'
        for j in jrows)

    trows = [t for t in data["themes"] if wants & set(t.get("interests", []))][:3]
    trelated = "".join(
        f'<a class="row themerow" href="/themes/{t["slug"]}">'
        f'<div><p class="kicker">{esc(t["strapline"])}</p>'
        f'<h3>{esc(t["name"])}</h3>'
        f'<p class="rowsub">'
        + " · ".join(esc(idx[st["city"]]["city"]["name"])
                     for st in t["stops"] if st["city"] in idx)
        + '</p></div><div class="themeside">'
        + constellation(_pts([st["city"] for st in t["stops"]]),
                        extra=" constel-theme")
        + f'<p class="rowmeta">'
        f'{n_of(len({idx[st["city"]]["country"]["name"] for st in t["stops"] if st["city"] in idx}), "country")}'
        f'</p></div></a>'
        for t in trows)

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
<div class="rows">{rows}</div>

{section("Journeys that go this way", f'<div class="rows journeyrows">{jrelated}</div>') if jrows else ""}
{section("Themes that run through it", f'<div class="rows">{trelated}</div>') if trows else ""}

<div class="note mt7">
  <h2 class="mini">Build this into a route</h2>
  <p>The Journey Planner weights the same tags this page queries on, so choosing
  {esc(and_list([data["interests"][w]["name"] for w in m.get("interests", [])]) or "these interests")}
  there will build a route through places like these.
  <a href="/plan">Plan a journey →</a> · <a href="/discover">Discover mode →</a></p>
</div>
"""
    return f"/europe-in/{m['slug']}/index.html", page(
        m["name"], body, path=f"/europe-in/{m['slug']}", area="discover",
        description=f"{m['strapline']} {len(hits)} destinations match, queried from the Atlas on every build.",
        og=("motion:" + m["slug"], motif_for(m.get("interests", [])),
            f"{m['name']} — {m['strapline']}"),
        ld_blocks=[
            ld_breadcrumb([("Europe", "/discover"), ("Europe in Motion", "/europe-in"),
                           (m["name"], f"/europe-in/{m['slug']}")]),
            {"@context": "https://schema.org", "@type": "ItemList",
             "name": m["name"], "description": m["lede"],
             "url": f"https://europedoor.com/europe-in/{m['slug']}",
             "numberOfItems": len(shown),
             "itemListElement": [
                 {"@type": "ListItem", "position": i,
                  "item": ld_within("TouristDestination", n["city"]["name"],
                                    urls.city(n["country"], n["region"], n["city"]))}
                 for i, (n, _w) in enumerate(shown, start=1)]},
        ],
    )


def motion_index(data):
    """Twelve queries, printed as queries.

    THE FAMILY'S WHOLE ARGUMENT WAS THE ONE THING THE INDEX DID NOT SHOW.
    Every `/europe-in/*` page prints the query that made it — that is the
    rule this family exists to demonstrate, and `checks.py` asserts it on all
    twelve. The index showed twelve generated landscapes instead, one per
    query, and the query nowhere.

    **A motion is not a place.** It has no coastline, no topography and no
    season of its own, so a plate drawn for one is a picture of nowhere
    standing in for a sentence — the same failure as the stories index, one
    family over, and the rule written for it applies here word for word: the
    alternative to a hash-drawn landscape is not a better hash.

    So the picture goes and the query arrives, generated by the same
    `motion_query_words()` the twelve pages use, so the index cannot state a
    query the page it links to would not.
    """
    rows = []
    for m in data["motions"]:
        n = sum(1 for cid, x in data["cities"].items()
                if motion_match(data, m, cid, x)[0])
        rows.append(
            f'<a class="row motionrow" href="/europe-in/{m["slug"]}">'
            f'<div><h3>{esc(m["name"])}</h3>'
            f'<p class="rowsub">{esc(m["strapline"])}</p>'
            f'<p class="motionq">{esc(motion_query_words(data, m))}</p></div>'
            f'<p class="rowmeta">{n}<br><span class="small">destinations</span>'
            f'</p></a>')
    body = f"""
{crumbs([("Europe", "/discover"), ("Europe in Motion", None)])}
<div class="pagehead index">
  <p class="kicker">Europe in Motion</p>
  <h1>The continent, cut a dozen different ways.</h1>
  <p class="lede">Not categories. {len(data['motions'])} queries, each run against all
  {len(data['cities'])} destinations on every build, and each page prints the query that
  made it. A list somebody curated by hand looks identical to one a query produced — on
  the day it ships, and never again.</p>
</div>
<div class="rows">{"".join(rows)}</div>

<div class="note mt7">
  <h2 class="mini">Why this is not a set of tags</h2>
  <p>A tag page tells you what carries a label. These ask questions the tags cannot answer on
  their own: which places have their <em>quieter</em> season in autumn, which lie above 63°
  north, which score highly for <a href="/method#discoverability">discoverability</a> and are
  small enough to be villages. The query is the product.</p>
</div>
"""
    return "/europe-in/index.html", page(
        "Europe in Motion", body, path="/europe-in", area="discover",
        description=f"A dozen ways to cut the continent — each a real query run against all {len(data['cities'])} destinations on every build, with the query printed on the page.",
        og=("motion:index", "peaks", "Europe in Motion"),
        ld_blocks=[ld_breadcrumb([("Europe", "/discover"),
                                  ("Europe in Motion", "/europe-in")])],
    )


def discover_page(data):
    """The specification's first navigation item, and the honest answer to
    "where do I start". Four ways in — by region, by what you travel for, by
    a curated route, and by month — plus the map, because most people mean
    the map when they say discover."""
    # THE LAST FIFTEEN ABSTRACT PLATES ON THE SITE WERE ON THIS PAGE.
    #
    # Nine macro cards and six motion cards each opened on a landscape chosen
    # by the hash of a slug — the exact thing measured as "placeholder art
    # doing a picture's job" when it was removed from the homepage, still
    # here, on the page whose whole subject is how to choose. A reader
    # scrolling /discover met fifteen purple gradients that agree with
    # nothing on the page and tell them nothing about what is behind the
    # link.
    #
    # A MACRO REGION IS THE ONE GROUPING IN THIS ATLAS WITH REAL POLYGONS.
    # A travel region is a set of destinations and is refused a boundary; the
    # Nordics is five whole countries Natural Earth already holds. So the
    # card draws its own members, which is the same claim `macromap()` makes
    # on the region's own page and the same drawing /countries uses — and
    # nine of them are nine different shapes, where nine plates were nine
    # pictures of nowhere.
    macro_cards = [
        card(urls.macro(m), f"{len(m['countries'])} countries", m["name"], m["blurb"],
             art=region_glyph(m["countries"], macro_frame(data, m)))
        for m in data["macros"]
    ]
    n_by_interest = {
        i["slug"]: sum(1 for n in data["cities"].values() if i["slug"] in n["city"]["interests"])
        for i in data["taxonomy"]["interests"]
    }
    # SEVENTEEN CARDS, EACH HOLDING ONE WORD AND A NUMBER.
    #
    # Border, fill, radius and shadow each say "separate object, placed here
    # by a system", and a four-column grid spent all four of them on a tag
    # name — the /experiences finding, on the page whose whole subject is how
    # to choose. It is also the brief's ninth constraint word for word: no
    # grid should require the reader to read tiny labels. A tag with a count
    # on it is a REGISTER ENTRY, and the register directly below it, the
    # twelve months, was already drawn as chips.
    #
    # ORDERED BY THE COUNT, WHICH IS A MEASUREMENT RATHER THAN A RANKING. The
    # taxonomy's own order is editorial and says nothing to a reader; what
    # this atlas is mostly about is derived on every build and is the one
    # thing the seventeen can be compared on. Nothing is promoted: every tag
    # is here and the number beside it is the number of destinations that
    # carry it, so a reader can check it against the page it opens.
    interest_chips = "".join(
        f'<a class="chip countchip" href="{urls.interest(i["slug"])}">'
        f'<span aria-hidden="true">{esc(i["icon"])}</span> {esc(i["name"])}'
        f'<span class="chipn">{n_by_interest[i["slug"]]}</span></a>'
        for i in sorted(data["taxonomy"]["interests"],
                        key=lambda i: (-n_by_interest[i["slug"]], i["name"]))
    )
    # AND A MOTION IS A QUERY, NOT A PLACE. It has no coastline, no
    # topography and no season, so a plate drawn for one is a picture of
    # nowhere standing in for a sentence — the finding that rebuilt
    # /europe-in, which prints its twelve queries as queries. This is the
    # same family two clicks away and it was still drawing landscapes.
    # The query is generated by the function the twelve pages use, so this
    # index cannot state a query the page it links to would not.
    motion_cards = "".join(
        f"""<a class="card motioncard" href="/europe-in/{esc(m['slug'])}">
        <div class="card-body">
        <p class="kicker">{sum(1 for cid, x in data['cities'].items()
                               if motion_match(data, m, cid, x)[0])} destinations</p>
        <h3>{esc(m['name'])}</h3>
        <p class="rowsub">{esc(m['strapline'])}</p>
        <p class="motionq">{motion_query_words(data, m)}</p></div></a>"""
        for m in data["motions"][:6]
    )
    months = data["taxonomy"]["months"]
    names = data["taxonomy"]["month_names"]
    dots = []
    for cid, n in sorted(data["cities"].items()):
        x, y = project(n["city"]["lat"], n["city"]["lon"])
        cls = " advisory" if n["country"].get("advisory") else ""
        dots.append(f'<circle class="herodot{cls}" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
    quiet = sum(1 for n in data["cities"].values() if n["city"].get("quiet"))

    # Land under the dots: /discover had the same scatter-plot fault that
    # the homepage hero and the destination locator both had.
    dctx, dland = geo.landmass(MAPPROJ, (0, 0, MAP_W, MAP_H))
    body = f"""
{crumbs([("Europe", "/discover"), ("Discover", None)])}
<div class="pagehead instrument">
  <p class="kicker">Discover</p>
  <h1>Where will Europe take you?</h1>
  {head_extent([(len(data['cities']), 'destinations'),
                (len(data['countries']), 'countries'),
                (len(data['taxonomy']['interests']), 'things to travel for')])}
  <p class="lede">Every other page here asks you to already know where you want to go — a
  country, a region, a sentence. This one does not. Say what you are travelling for and the
  list narrows itself, and each place left on it will tell you why it is there.</p>
</div>

<section class="band" id="discover-mode">
  <div class="band-head">
    <h2>Discover mode</h2>
    <p class="lede">Pick as many as you like. Nothing is submitted; the whole Atlas is in
    your browser and the list re-sorts as you choose.</p>
  </div>
  <div class="chips picks" id="discover-interests"></div>
  <div class="form-row mt5">
    <div class="field">
      <label for="discover-month">Travelling in</label>
      <select id="discover-month"></select>
    </div>
    <div class="field">
      <label for="discover-budget">Spending band</label>
      <select id="discover-budget"></select>
    </div>
    <div class="field">
      <p class="fieldhead">Off the obvious circuit</p>
      <label class="inlinecheck"><input type="checkbox" id="discover-quiet">
      Only places with a high discoverability score</label>
    </div>
    <div class="field">
      <p class="fieldhead">Reachable slowly</p>
      <label class="inlinecheck"><input type="checkbox" id="discover-rail">
      Favour places on the slow-rail list</label>
    </div>
  </div>
  <p class="small"><button type="button" class="linkish" id="discover-clear">Clear everything</button></p>
  <p class="small" id="discover-count" aria-live="polite"></p>
  <div id="discover-results"></div>
</section>


<a class="heromap wide-map arched" data-role="instrument" href="/map" aria-label="Map of all {len(data['cities'])} places">
  <svg viewBox="0 0 {MAP_W} {MAP_H}" aria-hidden="true"><defs>{arch_clip("disc", MAP_W, MAP_H)}</defs><g clip-path="url(#arch-disc)"><rect x="0" y="0" width="{MAP_W}" height="{MAP_H}" class="archground"/>{dctx}{dland}{''.join(dots)}</g>{arch_edge(MAP_W, MAP_H)}</svg>
  <span class="heromap-cap">Coastline from Natural Earth, public domain.
  Open the full map, with layers →</span>
</a>

{constel_defs()}
{section("By where it is", grid(macro_cards, 3),
         lede="Nine regions of Europe, grouped by shared coast, shared mountain range and shared history rather than by alphabet.",
         more=("Every country, A to Z", "/countries"))}

{section("By what you travel for", f'<div class="chips">{interest_chips}</div>',
         lede=f"{numword(len(data['taxonomy']['interests'])).capitalize()} tags, biggest "
              f"first, with the number of destinations carrying each. The Journey Planner "
              f"weights the same ones, so what you see here is what it will build from.",
         more=("Cross-border themes", "/themes"))}

{section("Europe in Motion", '<div class="grid cols-3">' + motion_cards + "</div>",
         lede="A dozen ways to cut the continent, each one a query run against every destination on every build rather than a list somebody chose. Each page prints the query that made it.",
         more=("All twelve", "/europe-in"))}

{section("By month", year_band(data),
         lede="What is on, which countries are at their best, and which are in the quieter shoulder — which is usually where you should be going.",
         more=("The whole European year", "/events"))}

<div class="note">
  <h2 class="mini">What "off the obvious circuit" means, exactly</h2>
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
"""
    return "/discover/index.html", page(
        "Discover Europe", body, path="/discover", area="discover",
        description=f"Say what you are travelling for and {len(data['cities'])} places across {len(data['countries'])} countries narrow themselves — each one saying why it is on the list.",
        scripts=["/assets/js/discover.js"],
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


PRELAUNCH = """<div class="note sourced">
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
