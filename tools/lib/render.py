"""HTML for Europedoor.

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

SITE_NAME = "Europedoor"
SITE_TAGLINE = "One door into Europe"
# The operating company is not incorporated yet. Nothing on this site may
# name an entity that does not exist; see docs/legal-position.md.
OPERATOR = "[OPERATOR ENTITY — NOT YET INCORPORATED]"


def esc(s):
    return html.escape(str(s), quote=True)


def plate(seed, w=640, h=360, label=""):
    """A deterministic abstract crest for a place. Same slug, same plate."""
    d = hashlib.sha256(seed.encode("utf-8")).digest()
    hue = d[0] * 360 // 256
    hue2 = (hue + 40 + d[1] % 90) % 360
    sat = 22 + d[2] % 26
    lig = 26 + d[3] % 18
    bars = []
    for i in range(7):
        x = (d[4 + i] / 255.0) * w
        bw = 8 + (d[11 + i] % 46)
        op = 0.06 + (d[18 + i] % 20) / 100.0
        bars.append(
            f'<rect x="{x:.1f}" y="0" width="{bw}" height="{h}" fill="#fff" opacity="{op:.2f}"/>'
        )
    arc = d[25] % 3
    marks = {
        0: f'<circle cx="{w*0.72:.0f}" cy="{h*0.34:.0f}" r="{h*0.22:.0f}" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="2"/>',
        1: f'<path d="M0 {h*0.78:.0f} L{w*0.3:.0f} {h*0.3:.0f} L{w*0.52:.0f} {h*0.62:.0f} L{w*0.74:.0f} {h*0.24:.0f} L{w} {h*0.7:.0f}" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="2"/>',
        2: f'<rect x="{w*0.62:.0f}" y="{h*0.2:.0f}" width="{w*0.2:.0f}" height="{h*0.6:.0f}" fill="none" stroke="#fff" stroke-opacity=".26" stroke-width="2"/>',
    }[arc]
    return (
        f'<svg class="plate" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label or seed)}" '
        f'preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="g{d[26]:02x}{d[27]:02x}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="hsl({hue} {sat}% {lig}%)"/>'
        f'<stop offset="1" stop-color="hsl({hue2} {sat+8}% {lig+12}%)"/>'
        f"</linearGradient></defs>"
        f'<rect width="{w}" height="{h}" fill="url(#g{d[26]:02x}{d[27]:02x})"/>'
        f'{"".join(bars)}{marks}</svg>'
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
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span class="sep" aria-hidden="true">/</span>'.join(parts) + "</nav>"


# Primary navigation, from the product specification. Seven items plus the
# two persistent utilities. The Fund moved to the footer when that spec
# arrived: it is a community surface rather than a way into the continent,
# and giving it a seventh of the masthead was overstating it.
NAV = [
    ("/discover", "Discover", "The map, the regions, the ways in."),
    ("/countries", "Countries", "Every country, region and destination."),
    ("/experiences", "Experiences", "What people actually do here."),
    ("/journeys", "Journeys", "Curated routes across the continent."),
    ("/plan", "Plan", "Days, budget, interests — an itinerary."),
    ("/stories", "Stories", "People, places, history, food, faith."),
    ("/events", "Events", "The European year, month by month."),
]

# Secondary navigation, also from the specification: everything a visitor may
# need to find and never has to see.
FOOTER_NAV = [
    ("/for-businesses", "For businesses"),
    ("/for-tourism-boards", "For tourism boards"),
    ("/fund", "Europe Fund"),
    ("/map", "Map"),
    ("/themes", "Themes"),
    ("/beyond-the-obvious", "Beyond the obvious"),
    ("/my-europe", "My Europe"),
    ("/about", "About"),
    ("/how-it-works", "How it works"),
    ("/method", "Method"),
    ("/sources", "Sources & corrections"),
    ("/contact", "Contact"),
    ("/help", "Help"),
    ("/accessibility", "Accessibility"),
    ("/privacy", "Privacy"),
    ("/terms", "Terms"),
    ("/cookies", "Cookies"),
]


def page(title, body, *, path, description, trail=None, area=None, head_extra="", scripts=(), wide=False):
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
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="https://europedoor.com{esc(path)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="/assets/css/europedoor.css">
<link rel="icon" href="/assets/door.svg" type="image/svg+xml">
{head_extra}</head>
<body class="area-{esc(area or 'none')}">
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <div class="masthead-in">
    <a class="wordmark" href="/">
      <span class="door" aria-hidden="true"></span>
      <span class="wordmark-text">europedoor</span>
    </a>
    <nav class="nav" aria-label="Primary">{"".join(nav)}</nav>
    <div class="navutil">
      <a class="navsearch" href="/search"><span aria-hidden="true">⌕</span> Search</a>
      <a class="navmine" href="/my-europe">My Europe</a>
    </div>
  </div>
</header>
<main id="main" class="{'wide' if wide else ''}">
{body}
</main>
<footer class="footer">
  <div class="footer-in">
    <p class="footer-lede">{esc(SITE_TAGLINE)} — discover it, plan it, and leave it better than you found it.</p>
    <nav class="footer-nav" aria-label="Footer">{footer_nav}</nav>
    <p class="footer-legal">
      Editorial project, pre-launch. Operated by {esc(OPERATOR)}. Nothing here is a booking,
      an offer, or financial advice; nothing on this site takes a payment.
      Country facts are editorial and may be out of date — check official
      government advice before you travel.
    </p>
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


def card(href, kicker, title, blurb, *, seed=None, meta="", tall=False):
    art = f'<div class="card-art">{plate(seed, 640, 360, title)}</div>' if seed else ""
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


def jsonscript(var, obj):
    payload = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    payload = payload.replace("</", "<\\/")
    return f'<script>window.{var}={payload};</script>'
