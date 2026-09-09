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
from . import urls
from .render import (LD_PUBLISHER, SITE_NAME, SITE_TAGLINE, arch_rim, card, chips, crumbs,
                     esc, factlist, grid,
                     jsondata, ld_breadcrumb, ld_place, ld_within, motif_for,
                     page, picture, plate, section, arch_clip, arch_edge)
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
    doc = geo.load("europe-lod0.json")
    if not doc:
        return ""
    ctx, land = geo.landmass(MAPPROJ, (0, 0, MAP_W, MAP_H), doc=doc)
    return (
        f'<div class="heroeurope" aria-hidden="true">'
        f'<svg viewBox="0 0 {MAP_W} {MAP_H}" preserveAspectRatio="xMidYMid meet"'
        f' focusable="false">{ctx}{land}</svg></div>'
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
    HOME_KINDS = ["mountains", "history", "food", "nature",
                  "coast", "sacred", "architecture", "cities"]
    kind_cards = [
        card(urls.interest(k), f"{n_by_interest[k]} destinations",
             data["interests"][k]["name"], None,
             seed="interest:" + k, motif=motif_for([k]))
        for k in HOME_KINDS
    ]

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
    jcards = [
        card(urls.journey(j),
             f"{j['days']} days · {len({l['city'].split('/')[0] for l in j['legs']})} countries",
             j["name"], j["strapline"], seed="journey:" + j["slug"], tall=True,
             motif=motif_for(j["interests"]))
        for j in picked
    ]

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

    body = f"""
<section class="herofull{' shot' if heroimg else ''}">
  {heroimg}
  {heroeurope(data)}
  <div class="herobody">
    <h1>Open the door to Europe.</h1>
    <p class="lede">One continent, drawn as we hold it. Fifty countries, and
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
  <p class="sourcenote">The continent above is drawn from
  <a href="/sources">Natural Earth</a>, public domain, on a Lambert conformal
  conic — the same projection and the same file as every other map here.
  <a href="/map">Open the map →</a></p>
</div>

{section("Find your kind of Europe", '<div class="grid mosaic">' + "".join(kind_cards) + "</div>",
         stage="Discover", tone="quiet",
         lede="From iconic cities to hidden gems, from mountains to coastlines, from history "
              "to the way a place eats. Each of these is a real list, and the Journey Planner "
              "weights the same ones — so what you see here is what it will build from.",
         more=("Explore the map", "/map"))}

{section("Journeys worth taking", grid(jcards, 3) if jcards else '<p class="small">Curated journeys are being written.</p>',
         stage="Go",
         lede="A good European trip rarely stays in one country. These do not — and each one "
              "opens in the planner, so you can make it yours.",
         more=("Build your own journey", "/plan"))}

<div class="note homefoot">
  <p>{ncountries} countries · {nregions} travel regions · {ncities} destinations ·
  {len(data['journeys'])} curated journeys. EuropeDoor is pre-launch and editorial: nothing
  here takes a payment, holds money or makes a booking — see
  <a href="/how-it-works">how it works</a> for what is built, what is designed and what is
  deliberately blocked.</p>
</div>
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
    blocks = []
    for m in data["macros"]:
        rows = []
        for cs in m["countries"]:
            c = data["countries"][cs]
            ncity = sum(len(r["cities"]) for r in c["regions"])
            adv = ' <span class="tag advisory">advisory</span>' if c.get("advisory") else ""
            rows.append(
                f"""<a class="row" href="{urls.country(c)}">
                <div><h3>{esc(c['name'])}{adv}</h3><p class="rowsub">{esc(c['tagline'])}</p></div>
                <p class="rowmeta">{len(c['regions'])} regions · {ncity} cities</p></a>"""
            )
        blocks.append(
            f"""<section class="band" id="{esc(m['slug'])}">
            <div class="band-head"><p class="kicker">{len(m['countries'])} countries</p>
            <h2><a href="{urls.macro(m)}" class="nodec">{esc(m['name'])}</a></h2>
            <p class="lede">{esc(m['blurb'])}</p></div>
            <div class="rows">{''.join(rows)}</div></section>"""
        )
    body = f"""
{crumbs([("Europe", "/discover"), ("Atlas", None)])}
<div class="pagehead index">
  <p class="kicker">Every country in Europe</p>
  <h1>Europe, all the way down.</h1>
  <p class="lede">Nine regions, {len(data['countries'])} countries, {sum(len(c['regions']) for c in data['countries'].values())}
  travel regions and {len(data['cities'])} cities. The regions below are editorial travel regions,
  not administrative ones: they group places that feel like each other and are usually visited together.</p>
</div>
{''.join(blocks)}
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
    cards = []
    for cs in m["countries"]:
        c = data["countries"][cs]
        ncity = sum(len(r["cities"]) for r in c["regions"])
        meta = f'<p class="cardmeta">{len(c["regions"])} regions · {ncity} cities · {esc(c["budget"])} cost</p>'
        cards.append(card(urls.country(c), c["capital"], c["name"], c["tagline"], seed="country:" + c["slug"],
                 meta=meta, motif=motif_for(c["interests"])))
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">Region of Europe</p>
  <h1>{esc(m['name'])}</h1>
  <p class="lede">{esc(m['blurb'])}</p>
</div>
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
                   prefer="beside"):
        """Place a label if it fits the aperture and hits nothing already there.

        One placement routine for every level of the hierarchy, so a region
        name and a village name compete on the same terms and in the order
        the hierarchy sets — which is the whole point of having one.
        """
        got = place_label_box(px, py, text, w, h, cls=cls, off=off,
                              prefer=prefer, metric=metric)
        if not got:
            return False
        lhtml, lx, ly, lw, lh = got
        bx = (lx - LABEL_CLEAR, ly - LABEL_CLEAR,
              lx + lw + LABEL_CLEAR, ly + lh + LABEL_CLEAR)
        if any(not (bx[2] < q[0] or bx[0] > q[2]
                    or bx[3] < q[1] or bx[1] > q[3]) for q in boxes_):
            return False
        boxes_.append(bx)
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

    cbox = _highlight_box(land)
    countryname = ""
    if cbox:
        ncx, ncy, _r = cbox
        countryname = (f'<text class="cname" x="{ncx:.1f}" y="{ncy:.1f}" '
                       f'text-anchor="middle">{esc(c["name"].upper())}</text>')
    namemarks = countryname + "".join(labs_)
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
    region_cards = []
    for r in c["regions"]:
        meta = f'<p class="cardmeta">{len(r["cities"])} cities</p>'
        region_cards.append(
            card(urls.region(c, r), "Region", r["name"], r["summary"], seed=f"region:{c['slug']}:{r['slug']}", meta=meta)
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
             meta=f'<p class="cardmeta">{len(t.get("places", []))} places · '
                  f'{len(t.get("experiences", []))} experiences</p>')
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

{section("Travel regions", countrymap(data, c) + grid(region_cards, 3), id="regions",
         lede=f"{len(c['regions'])} editorial regions, each opening onto its cities.")}

{section("Popular destinations", grid(popular, 3),
         lede="The destinations we have written most about, which is not the same as the ones most people go to — and is the only ranking we can honestly compute.",
         more=("Every region", "#regions")) if popular else ""}

{section("Experiences here", f'<div class="rows">{cexps}</div>',
         lede=f"A sample of what is listed across {esc(c['name'])}.",
         more=("Every experience category", "/experiences")) if cexps else ""}

{section("Journeys through " + c["name"], f'<div class="rows">{cjourneys}</div>') if cjourneys else ""}

{section("Stories set here", f'<div class="rows">{cstories}</div>') if cstories else ""}

{section("Fixed points in the year", f'<div class="rows">{festivals}</div>',
         more=("The whole European year", "/events")) if festivals else ""}

{section("The record", facts + scorebars(country_scores(c)) + provenance_block(c),
         tone="quiet",
         lede="What we hold about " + esc(c["name"]) + ", where each figure came "
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
    cards = []
    for t in r["cities"]:
        meta = f'<p class="cardmeta">{nights_line(t)}</p>'
        # NOT the country. Every destination on a region page is in the same
        # country, so a kicker reading NORWAY eight times down the grid is
        # the boilerplate the "never explain the constraint back" rule
        # forbids: a reason shared by every result is hoisted into one line
        # above the list — here, the breadcrumb and the h1 — and the row
        # carries only what distinguishes it. What kind of place it is does.
        cards.append(card(urls.city(c, r, t),
                          CITY_TYPE_NAMES.get(t.get("city_type"), "Destination"),
                          t["name"], t["summary"],
                          seed=f"city:{c['slug']}:{t['slug']}", meta=meta,
                          motif=motif_for(t["interests"], t.get("city_type"))))
    body = f"""
{crumbs([("Europe", "/discover"), ("Countries", "/countries"), (m["name"], urls.macro(m)),
         (c["name"], urls.country(c)), (r["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">{esc(c['name'])}</p>
  <h1>{esc(r['name'])}</h1>
  {statement(r['summary'])}
  <p class="orient">{len(r["cities"])} destination{"s" if len(r["cities"]) != 1 else ""} ·
  {len(rplaces)} place{"s" if len(rplaces) != 1 else ""} recorded ·
  about {int(pass_nights)} nights to see it all</p>
  {chips(r["interests"], data["interests"])}
</div>

{regionmap(data, c, r)}

{section("Destinations", grid(cards, 3))}
{section("Places to see", f'<div class="rows">{placerows}</div>',
         lede=f"Everything recorded across {esc(r['name'])}, in one list.") if placerows else ""}
{section("Things to do", f'<div class="rows">{exprows}</div>') if exprows else ""}
{section("Journeys through " + r["name"], f'<div class="rows">{jrows}</div>') if jrows else ""}
{section("Accommodation & restaurants", STAY_NOTE)}
{section("The record", factlist([
      ("Destinations", str(len(r["cities"]))),
      ("Places recorded", str(len(rplaces))),
      ("Experiences", str(len(rexps))),
      ("A full pass", f"about {int(pass_nights)} nights"),
      ("Best months", esc(months_line(data, c["season"]["peak"]))),
      ("Typical day", daily_line(data, c)),
  ]), tone="quiet",
  lede="What this atlas holds about " + esc(r["name"]) + ". The counts are "
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

    # Everything that points at this city. These are the graph edges: a
    # journey that stops here, a theme that names it, a story set in it.
    b = data["back"][cid]
    edge_rows = []
    for j in b["journeys"]:
        leg = next(l for l in j["legs"] if l["city"] == cid)
        edge_rows.append(
            f"""<a class="row" href="{urls.journey(j)}">
            <div><h3>{esc(j['name'])}</h3><p class="rowsub">{esc(leg['why'])}</p></div>
            <p class="rowmeta">Journey · {leg['nights']} nights here</p></a>"""
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
    ("Stay & eat", "stay"),
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
             lede=f"Fixtures tied to {esc(t['name'])} itself.") if festrows else ""}
    {section(f"Elsewhere in {esc(c['name'])}" if festrows else "Events",
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
         lede=f"Practical things about {esc(c['name'])} that are not obvious from outside it.")}

{section("Accommodation & restaurants", STAY_NOTE, id="stay")}

{section("Nearest onward stops", f'<div class="rows">{nearrows}</div>',
         id="onward",
         lede="Straight-line distance, and what that usually means in practice.")}

{section("The record", factlist([
    ("Kind of place", esc(CITY_TYPE_NAMES.get(t.get("city_type"), ""))),
    ("Population", pop_line(t)),
    ("Region", f'<a href="{urls.region(c, r)}">{esc(r["name"])}</a>'),
    ("Coordinates", f'<span class="mono">{coord_line(t)}</span>'),
]) + scorebars(city_scores(c, r, t)), id="record", tone="quiet",
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
    shown = cities[:60]
    cards = [
        card(
            urls.city(n["country"], n["region"], n["city"]),
            f"{n['country']['name']} · {n['region']['name']}",
            n["city"]["name"], n["city"]["summary"],
            seed=f"city:{n['country']['slug']}:{n['city']['slug']}",
            motif=motif_for(n["city"]["interests"], n["city"].get("city_type")),
        )
        for n in shown
    ]
    # 200 destinations were silently cut to 60 with nothing on the page
    # saying so — a list that stops without admitting it stopped is the one
    # kind of incompleteness a reader cannot detect.
    cut = (f" Showing the first {len(shown)} of {len(cities)}, alphabetically "
           f"by country." if len(cities) > len(shown) else "")
    body = f"""
{crumbs([("Europe", "/discover"), ("Experiences", "/experiences"), (i["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">Travelling for</p>
  <h1>{esc(i['name'])}</h1>
  {statement(f"{len(cities)} of the {total} destinations in this atlas are tagged "
             f"{i['name'].lower()}. {band}")}
  <p class="orient">{pct}% of the atlas · {len(countries)} of
  {len(data['countries'])} countries · {rank_phrase(rank, len(ranking))}</p>
</div>

{grid(cards, 3) if cards else empty_state(
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
  you see here is what it will build from.{cut}</p>
</div>
"""
    return f"/interests/{slug}/index.html", page(
        i["name"], body, path=urls.interest(slug), area="countries",
        description=f"Where in Europe to go for {i['name'].lower()}: {len(cities)} cities across {len(countries)} countries.",
    )


# ── journeys ──────────────────────────────────────────────────────────

def journeys_index(data):
    cards = []
    for j in data["journeys"]:
        countries = []
        for leg in j["legs"]:
            cn = data["cities"][leg["city"]]["country"]["name"]
            if cn not in countries:
                countries.append(cn)
        meta = (f'<p class="cardmeta">{j["days"]} days · {len(countries)} countries · '
                f'{esc(j["difficulty"])} · {esc(j["budget"])}</p>')
        cards.append(card(urls.journey(j), j["strapline"], j["name"], j["summary"][:150] + "…",
                          seed="journey:" + j["slug"], meta=meta,
                          motif=motif_for(j["interests"])))
    body = f"""
{crumbs([("Europe", "/discover"), ("Journeys", None)])}
<div class="pagehead index">
  <p class="kicker">European Journeys</p>
  <h1>Routes that cross borders on purpose.</h1>
  <p class="lede">{len(data['journeys'])} routes, each a real sequence with real distances:
  every stop links back into the Atlas, and the nights add up to the days on the tin. Take one
  as written, or open it in the Planner and bend it to the time you actually have.</p>
</div>
{grid(cards, 3)}
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
  <p class="orient">{j['days']} days · {len(j['legs'])} stops · {len(countries)} countries · {total_km:,} km in a straight line</p>
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
<div class="pagehead instrument">
  <p class="kicker">Journey Planner</p>
  <h1>Twelve days, €2,500, history and mountains.</h1>
  <p class="lede">Say what you have and what you like — in a sentence, or in the form below.</p>
</div>

<form class="form ask" id="askform">
  <div class="field">
    <label for="ask">Say it in your own words</label>
    <textarea id="ask" name="ask" rows="2"
      placeholder="I have 12 days and €2,500, starting in Lisbon, and I love history, mountains and food."></textarea>
  </div>
  <p class="small">The planner reads the whole Atlas — {len(data['cities'])} cities across
  {len(data['countries'])} countries — scores every one against you, then builds a route that
  respects distance instead of teleporting between highlights. It runs entirely in your
  browser; nothing you type is sent anywhere.</p>
  <div class="hero-actions mt0">
    <button class="btn" type="submit">Read that and build it</button>
  </div>
  <p class="small mb0">Read by rules in your browser — not by a model, and
  not sent anywhere. It shows you exactly what it understood, and names anything it could not
  take account of rather than quietly dropping it.</p>
</form>

<div class="split">
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
  <aside class="rail">
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
    corrections</a>.</p>
  </aside>
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
        f'<figcaption>{esc(c["name"])}, its {len(c["regions"])} regions and {shown} '
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
    n = t.get("nights") or []
    if len(n) == 2:
        bits.append(f"{n[0]}–{n[1]} nights" if n[0] != n[1] else f"{n[0]} nights")
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
    ctx, land = geo.landmass(MAPPROJ, view)

    kmu = geo.km_per_unit(MAPPROJ, t["lat"], t["lon"])
    km_w = int(round(w / span * kmu / 10) * 10)
    km_h = int(round(h / span * kmu / 10) * 10)
    # And the bar, on the same arithmetic the caption uses. These are the
    # most-seen maps on the site — one per destination and one per place —
    # and until the projection was conformal none of them could carry one.
    bar = geo.scale_bar(MAPPROJ, _lat_at(cy + h / 2 / span),
                        _lat_at(cy - h / 2 / span), LCC_MID_LON,
                        1.0 / span, w, h)
    dots, labels = [], []
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
            got = place_label_box(
                px, py, n["city"]["name"], w, h,
                cls="minilabel here" if here else "minilabel", off=8.0)
            if got:
                labels.append(got)
    # If the frame held only the subject, the physical pass never ran in the
    # loop; run it now.
    if not _peaks_done[0]:
        _physical()

    drawnlabels = "".join(phone_declutter(labels))
    return (
        cartography.plate(
            uid=uid, w=w, h=h, proj=MAPPROJ, view=(0, 0, w, h),
            # The transform is the destination map's own: it draws the
            # continent's geometry and scales the window in, where a country
            # plate projects to its own frame. The renderer takes the land as
            # given and never touches a coordinate.
            land=(f'<g transform="translate({w/2 - cx*span:.2f},'
                  f'{h/2 - cy*span:.2f}) scale({span})">{ctx}{land}</g>'),
            destinations="".join(dots), labels=drawnlabels + bar,
            rim=False,
            figure_class=f"minimap arched atlas{dense_class(drawnlabels)}",
            aria=f"Map of {esc(t['name'])} and the places around it")[:-len("</figure>")]
        # `about` names something INSIDE this destination — a place page's
        # subject. The map is then honestly captioned as what it is: this
        # atlas has one projection and its finest unit is about four
        # kilometres, so there is no map of a building, and a map labelled
        # "Bryggen" that is actually a map of Bergen would be the kind of
        # small lie refused everywhere else here.
        + f'<figcaption>'
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
        f'<a href="/map">The full map →</a></figcaption></figure>'
    )


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
LABEL_METRICS = {
    "minilabel": (LABEL_PAD, LABEL_CH, LABEL_UP, LABEL_DOWN),
    "rlabel": (18.8, 8.89, 14.0, 5.0),
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
                    prefer="beside", wrap=None, metric="minilabel"):
    """The first position that fits inside the aperture, with its box.

    Right of the dot, then left, then under it, then over it. A name that
    fits nowhere is dropped exactly as a colliding one is — the dot, the
    <title> and the row in the list below all survive — because a name
    sliced mid-word by the signature reads as a broken renderer, and one
    drawn entirely outside it reads as a missing place.

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
    for x, y, anchor in order:
        if label_fits(x, y, wide, anchor, vw, vh, up, down):
            # ALWAYS EXPLICIT, even for "start". `.countrymap .rlabel text`
            # sets `text-anchor: middle` in CSS, and a presentation attribute
            # loses to a stylesheet rule — so omitting it on the default case
            # would have the region names silently centred on a box computed
            # for a left-anchored one.
            a = f' text-anchor="{anchor}"'
            box = _label_box(x, y, wide, anchor, up, down)
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
    for html, x0, y0, w, h in placed:
        cx, cy = x0 + w / 2.0, y0 + h / 2.0
        bw, bh = w * PHONE_LABEL_SCALE, h * PHONE_LABEL_SCALE
        box = (cx - bw / 2.0, cy - bh / 2.0, bw, bh)
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
                ("minilabel", "peakname", "fname", "sname"))
    return "" if names <= 6 else " dense"


def pointsmap(pts, uid, caption, aria, want=2.6, pad_frac=0.18, pad_min=24,
              min_w=120.0, min_h=75.0, line=False, extra=""):
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
    # A tenth of the frame, not the route map's fifth: these places are few
    # and far apart, and 0.20 of a continental frame dropped Tirana's label
    # for being within 300px of Budapest's.
    dx_min, dy_min = vw * 0.10, vh * 0.030
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
        # Same collision rule as the route map: a label that would land on
        # one already placed is dropped, not moved. Every place keeps its
        # dot, its <title> and its row in the list below.
        if any(abs(px - qx) < dx_min and abs(py - qy) < dy_min for qx, qy in placed):
            continue
        placed.append((px, py))
        # Four candidate positions, each tested against the real curve.
        # See place_label(): the previous rule tested the rectangle, which is
        # not the edge that cuts.
        # The box comes back too: the phone pass has to re-test it at the
        # larger size the stylesheet draws it at.
        got = place_label_box(px, py, name, vw, vh)
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
    return cartography.plate(
        uid=uid, w=vw, h=vh, proj=MAPPROJ, view=(0, 0, vw, vh),
        land=(f'<g transform="scale({k:.4f}) '
              f'translate({-x0:.1f},{-y0:.1f})">{ctx}{land}</g>'),
        route=route, destinations="".join(dots),
        labels="".join(lab) + bar,
        caption=f'<figcaption>{caption}</figcaption>',
        figure_class=f"minimap pointsmap arched atlas{dense}",
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
                     f'{len(pts)} destinations in the Atlas',
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
    return pointsmap(pts, uid, cap, f'Route map for {j["name"]}',
                     line=True)


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
    <div class="note warn">
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
         lede="What this atlas holds about " + esc(pl["name"]) + ", and nothing "
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

def scorebars(scores):
    from .score import DIMENSIONS, LABELS
    rows = "".join(
        f"""<div class="scorerow"><span class="scorelabel">{esc(LABELS[d])}</span>
        <span class="scorebar"><span class="w{scores[d]}"></span></span>
        <span class="scorenum">{scores[d]}</span></div>"""
        for d in DIMENSIONS
    )
    return f"""<div class="score">
    <p class="kicker">Europe Experience Score</p>{rows}
    <p class="small"><a href="/method">How this is calculated</a> — derived from our own tagging,
    not from measurement. It says what a place is for, not how good it is.</p></div>"""


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
        description=f"{title}: {len(chosen)} experiences across {len(countries)} European countries, selected by a published rule.",
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

    catcards = [
        card(urls.category(cat["slug"]), f"{len(C.select(items, cat))} listed", cat["name"],
             cat["blurb"], meta=taste(C.select(items, cat)))
        for cat in data["categories"]
    ]
    # NO BLURB, BECAUSE IT WAS THE SAME SENTENCE TEN TIMES. Every kind tile
    # carried "Grouped by what you actually do rather than by what it is
    # about", which is a fact about the axis and not about the kind — the
    # boilerplate this atlas's own rule forbids, hoisted into the section
    # lede where one copy of it belongs. `blurb=None` is the pattern the
    # homepage's eight ways-in tiles already use.
    cards = [
        card(urls.experience_kind(k), f"{counts.get(k, 0)} listed", name, None,
             meta=taste([it for it in items if it["exp"]["kind"] == k]))
        for k, name in kinds.items()
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
<div class="pagehead index">
  <p class="kicker">Local Experiences</p>
  <h1>What people actually do here.</h1>
  <p class="lede">{len(items)} experiences across the Atlas, in ten kinds. Anything a business
  lists carries the name of who runs it and the tier of checking it has passed — an unchecked
  listing says so on its face rather than hiding behind a star rating.</p>
  <div class="hero-actions"><a class="btn" href="/experiences/join">List your experience</a>
  <a class="btn ghost" href="/for-businesses">For businesses</a></div>
</div>
{section("Eight categories", grid(catcards, 4),
         lede="What an experience is about. Each tile carries three of its own entries, spread across the list, and each category page prints the rule that built it.")}
{section("Ten kinds", grid(cards, 4),
         lede="The other axis: what you physically do. A cellar visit and a cathedral are both sacred to somebody; only one of them is a walk.")}
<!-- "Recently added" WAS A CLAIM THE DATA CANNOT SUPPORT. An experience
     carries a slug, a name, a kind, a band and a summary, and no date of
     any sort, so these 24 were simply the first 24 the loader returned in
     country order — Austria to Croatia, called recent. A false ordering is
     worse than none, because a reader takes it for a signal. -->
{section("Twenty-four of them", f'<div class="rows">{rows}</div>',
         lede="The first two dozen in country order — there is no date on an experience here, so this is a sample and not a recency.")}
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
      "This is one of ten kinds an experience can be given, and the kind is "
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
    cards = [
        card(urls.fund_project(p), data["countries"][p["country"]]["name"], p["name"], p["summary"],
             seed="fund:" + p["slug"], meta=f'<p class="cardmeta">{esc(p["theme"])} · {esc(p["status"])}</p>')
        for p in data["fund"]
    ]
    body = f"""
{crumbs([("Europe", "/discover"), ("Fund", None)])}
<div class="pagehead index">
  <p class="kicker">Europe Fund</p>
  <h1>What travel leaves behind.</h1>
  <p class="lede">Tourism arrives in a place and takes something out of it — a path, a language,
  a harbour wall, a summer. The Fund is the mechanism for putting something back:
  {len(data['fund'])} projects, listed publicly, with the local partner named on each.</p>
</div>

<div class="note warn">
  <h2 class="mini">The Fund holds no money, and will not until three things are true</h2>
  <p>There is an operating entity; a regulated payment path with a named payee; and a written
  answer on how contributions are treated in each country we would collect in. Until then this
  is a register of projects and nothing else — there is no balance, no total raised, and no
  donate button anywhere on this site. The data files are validated to reject a project that
  carries an amount.</p>
  <p class="small">Rationale and the full gate: <a href="/how-it-works">how it works</a>.</p>
</div>

{section(f"{len(data['fund'])} projects on the register", grid(cards, 3),
         lede="Chosen for being small enough that a travel platform could plausibly matter to them, and specific enough that you could go and look at the result.")}

{section("The four themes", '<div class="grid cols-4">' + "".join(
    f'<div class="card"><div class="card-body"><p class="kicker">{esc(t)}</p><h3>{len(v)} projects</h3></div></div>'
    for t, v in sorted(themes.items())) + "</div>") if themes else ""}
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

def themes_index(data):
    cards = [
        card(f"/themes/{t['slug']}", f"{len(t['stops'])} places", t["name"], t["strapline"],
             seed="theme:" + t["slug"], motif=motif_for(t.get("interests", [])))
        for t in data["themes"]
    ]
    body = f"""
{crumbs([("Europe", "/discover"), ("Themes", None)])}
<div class="pagehead index">
  <p class="kicker">Discovery without a map of borders</p>
  <h1>Europe, organised by what you came for.</h1>
  <p class="lede">Medieval Europe is not a country. Neither is sacred Europe, or Viking Europe,
  or the Europe you reach only by train. {len(data['themes'])} of them cut across the Atlas:
  each one is a real sequence of real places, and each place stays linked to the country it is
  actually in.</p>
</div>
{grid(cards, 3)}
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
    desks = '<div class="rows">' + "".join(
        f'<a class="row" href="{urls.story(s)}">'
        f'<div><p class="kicker">{esc(s["section"])}</p>'
        f'<h3>{esc(s["title"])}</h3>'
        f'<p class="rowsub">{esc(s["standfirst"])}</p></div>'
        f'<p class="rowmeta">{esc(s["published"])}<br>'
        f'<span class="small">{esc(s["reading"])}</span></p></a>'
        for s in byline
    ) + "</div>"
    body = f"""
{crumbs([("Europe", "/discover"), ("Stories", None)])}
<div class="pagehead index">
  <p class="kicker">Stories</p>
  <h1>A continent is people before it is places.</h1>
  <p class="lede">{len(data['stories'])} pieces across {len(sections)} desks — people, history,
  food, faith, nature and culture. Every story links into the Atlas, and every Atlas page that
  a story touches links back, so reading and planning are the same motion.</p>
</div>
{desks}
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

    attribution = geo.sources_line(geo.load("europe-lod1.json") or doc)

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
  <p class="lede">{len(data['countries'])} countries, {len(data['cities'])} destinations and
  {len(placedots)} places. Click a country to go into it.</p>
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
<g id="nogeo" class="nogeo">{''.join(nogeo)}</g>
<g id="route"></g>
<g id="regions" hidden></g>
<g id="places" hidden>{''.join(placedots)}</g>
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
    blocks = []
    for m in data["taxonomy"]["months"]:
        items = sorted(by_month[m], key=lambda p: p[1]["name"])
        if not items:
            continue
        rows = "".join(
            f"""<a class="row event" data-kind="{esc(f['kind'])}" href="{urls.country(c)}">
            <div><h3>{esc(f['name'])}</h3><p class="rowsub">{esc(f.get('where', ''))}</p></div>
            <p class="rowmeta">{esc(EVENT_KIND_NAMES[f['kind']])} · {esc(c['name'])}</p></a>"""
            for f, c in items
        )
        blocks.append(
            f'<section class="band" id="{esc(m)}"><div class="band-head">'
            f'<h2><a href="/events/{esc(m)}" class="nodec">{esc(names[m])}</a></h2>'
            f'<p class="lede">{len(items)} fixed points across Europe. '
            f'<a href="/events/{esc(m)}">Where to go in {esc(names[m])} →</a></p></div>'
            f'<div class="rows">{rows}</div></section>'
        )
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
<div class="pagehead index">
  <p class="kicker">The European year</p>
  <h1>What is on, and when.</h1>
  <p class="lede">{total} recurring fixtures — festivals, markets, pilgrimages, harvests and the
  handful of natural events worth planning a year around. These are the annual, dependable ones.
  Dated listings for a given year need a live events feed, which is Stage 2.</p>
</div>
{jump}
<div class="checks" id="eventkinds">{kindfilters}</div>
<p class="small" id="eventcount"></p>
{''.join(blocks)}
"""
    return "/events/index.html", page(
        "Events", body, path="/events", area="events",
        description="The recurring European year: festivals, markets, pilgrimages and seasonal events, month by month, filterable by category.",
        scripts=["/assets/js/events.js"],
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
    qcards = [
        card(urls.city(n["country"], n["region"], n["city"]),
             f"{n['country']['name']} · {n['region']['name']}", n["city"]["name"],
             n["city"]["summary"], seed=f"city:{n['country']['slug']}:{n['city']['slug']}",
             motif=motif_for(n["city"]["interests"], n["city"].get("city_type")))
        for n in quiet[:6]
    ]

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
  <p class="lede">{len(fixtures)} recurring fixtures, {len(peak)} countries at their best and
  {len(shoulder)} in the quieter shoulder — which is usually where you should be going.</p>
</div>
{year_band(data, month)}
{monthmap}
{section(f"On in {name}", f'<div class="rows">{rows}</div>') if rows else ""}
{section(f"At their best in {name}", f'<div class="rows">{country_rows(peak)}</div>',
         lede="Peak season: the weather works, everything is open, and so is everyone else's calendar.") if peak else ""}
{section(f"Quieter, and often better, in {name}", f'<div class="rows">{country_rows(shoulder)}</div>',
         lede="Shoulder season. The Journey Planner scores these upward rather than downward for exactly this month.") if shoulder else ""}
{section("Where we would actually send you", grid(qcards, 3),
         lede=f"Quiet places in countries that are in shoulder season this month — the intersection of the two things that matter.",
         more=("Every quiet place", "/beyond-the-obvious")) if qcards else ""}
"""
    return f"/events/{month}/index.html", page(
        f"{name} in Europe", body, path=f"/events/{month}", area="events",
        description=f"What is on in Europe in {name}, which countries are at their best, which are in the quieter shoulder season, and where to go instead of the obvious.",
    )


# ── beyond the obvious ────────────────────────────────────────────────

def quiet_page(data):
    quiet = [n for n in data["cities"].values() if n["city"].get("quiet")]
    quiet.sort(key=lambda n: (n["country"]["name"], n["city"]["name"]))
    cards = [
        card(urls.city(n["country"], n["region"], n["city"]),
             f"{n['country']['name']} · {n['region']['name']}", n["city"]["name"], n["city"]["summary"],
             seed=f"city:{n['country']['slug']}:{n['city']['slug']}",
             motif=motif_for(n["city"]["interests"], n["city"].get("city_type")))
        for n in quiet
    ]
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
        f'<a href="/sources">Natural Earth</a>, public domain.',
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
{section(f"{len(quiet)} places we would send you instead", grid(cards, 3),
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

    from .score import methodology_rows
    from .score import REFUSED, DISCOVER_TERMS, discoverability
    rows = "".join(
        f'<div class="row"><div><h3>{esc(name)}</h3><p class="rowsub">{esc(formula)}</p></div>'
        f'<p class="rowmeta">0–97</p></div>'
        for name, formula in methodology_rows()
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

{section("Two dimensions this refuses to compute", f'<div class="rows">{refused}</div>',
         lede="The specification this came from lists ten. Eight are computable from the dataset. These two are not, and an approximation would be worse than the gap.")}

{section("Discoverability", f'<div class="rows">{discrows}</div>', id="discoverability",
         lede="A second, separate score, used by Discover Mode and by Beyond the Obvious. It answers one narrow question: how far is this place from being the obvious choice?")}

<div class="note warn">
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
    def table(rows):
        return '<div class="rows">' + "".join(
            f'<div class="row"><div><h3>{esc(a)}</h3><p class="rowsub">{esc(b)}</p></div>'
            f'<p class="rowmeta">{esc(c)}</p></div>' for a, b, c in rows
        ) + "</div>"

    built = table([
        ("Europe Atlas", f"{len(data['countries'])} countries, {sum(len(c['regions']) for c in data['countries'].values())} regions, {len(data['cities'])} cities, all generated from one dataset", "built"),
        ("Journey Planner", "Runs in the browser against the whole Atlas; scores fit, respects distance, estimates cost", "built"),
        ("European Journeys", f"{len(data['journeys'])} curated cross-border routes with validated night counts", "built"),
        ("Themes", f"{len(data['themes'])} experience-first routes that ignore borders", "built"),
        ("Map", "Point map of every city, filterable, no third-party tiles", "built"),
        ("Experience listings", "Ten kinds, tiered, with the verification model published", "built"),
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
         "Find places. Fifty countries, their travel regions and their cities — including the "
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
        <p class="doorgo" aria-hidden="true">→</p></div></a>"""
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

{section("Four doors", '<div class="grid cols-4 doors">' + pillars + "</div>",
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
  <h1>Four read-only endpoints. No key, no quota, no sign-up.</h1>
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
    <p>Corrections are wanted, including blunt ones. A correction channel goes up with the entity;
    until then, the repository's issue tracker is the honest answer.</p>
    <h2 class="mini">No photographs</h2>
    <p>Every illustration on this site is generated from the place's own name — a deterministic
    drawing, unique per place, owned outright. No stock library, no licence expiry, no
    accidental use of somebody's holiday photograph.</p>
  </aside>
</div>
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
            <p class="rowsub">{ncity} cities · {esc(c['currency'])} · €{c['daily_eur'][0]}–{c['daily_eur'][1]} a day{prov}</p></div>
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

<div class="note warn">
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
    body = """
<div class="pagehead">
  <p class="kicker">404</p>
  <h1>That door does not open.</h1>
  <p class="lede">The page is not here. The continent still is.</p>
  <div class="hero-actions">
    <a class="btn" href="/countries">Open the Atlas</a>
    <a class="btn ghost" href="/plan">Plan a journey</a>
  </div>
</div>
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
        "monthNames": data["taxonomy"]["month_names"],
        "interests": {i["slug"]: i["name"] for i in data["taxonomy"]["interests"]},
    }


def search_page(data):
    n = (len(data["countries"]) + sum(len(c["regions"]) for c in data["countries"].values())
         + len(data["cities"]) + len(data["journeys"]) + len(data["themes"])
         + len(data["stories"]) + len(data["fund"]))
    body = f"""
{crumbs([("Europe", "/discover"), ("Search", None)])}
<div class="pagehead instrument">
  <p class="kicker">Search</p>
  <h1>Find it.</h1>
  <p class="lede">Everything on EuropeDoor — {n} countries, regions, destinations, places,
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
<div id="results" aria-live="polite"></div>
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

    wants = set(m.get("interests", []))
    jrows = [j for j in data["journeys"] if wants & set(j["interests"])][:3]
    jcards = [card(urls.journey(j), f"{j['days']} days · {len(j['legs'])} stops",
                   j["name"], j["strapline"], seed="journey:" + j["slug"],
                   motif=motif_for(j["interests"]))
              for j in jrows]
    trows = [t for t in data["themes"] if wants & set(t.get("interests", []))][:3]
    tcards = [card(f"/themes/{t['slug']}", "Theme", t["name"], t["summary"],
                   seed="theme:" + t["slug"],
                   motif=motif_for(t.get("interests", []))) for t in trows]

    body = f"""
{crumbs([("Europe", "/discover"), ("Europe in Motion", "/europe-in"), (m["name"], None)])}
<div class="pagehead overture">
  <p class="kicker">Europe in Motion</p>
  <h1>{esc(m["name"])}</h1>
  <p class="lede">{esc(m["lede"])}</p>
</div>

{motionmap}
{querynote}
{shared_note}
<div class="rows">{rows}</div>

{section("Journeys that go this way", grid(jcards, 3)) if jcards else ""}
{section("Themes that run through it", grid(tcards, 3)) if tcards else ""}

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
    cards = []
    for m in data["motions"]:
        n = sum(1 for cid, x in data["cities"].items()
                if motion_match(data, m, cid, x)[0])
        cards.append(card(f"/europe-in/{m['slug']}", f"{n} destinations",
                          m["name"], m["strapline"],
                          seed="motion:" + m["slug"],
                          motif=motif_for(m.get("interests", []))))
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
{grid(cards, 3)}

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
    macro_cards = [
        card(urls.macro(m), f"{len(m['countries'])} countries", m["name"], m["blurb"],
             seed="macro:" + m["slug"])
        for m in data["macros"]
    ]
    n_by_interest = {
        i["slug"]: sum(1 for n in data["cities"].values() if i["slug"] in n["city"]["interests"])
        for i in data["taxonomy"]["interests"]
    }
    interest_cards = "".join(
        f"""<a class="card" href="{urls.interest(i['slug'])}"><div class="card-body">
        <p class="kicker"><span aria-hidden="true">{esc(i['icon'])}</span> {n_by_interest[i['slug']]} places</p>
        <h3>{esc(i['name'])}</h3></div></a>"""
        for i in data["taxonomy"]["interests"]
    )
    motion_cards = [
        card(f"/europe-in/{m['slug']}",
             f"{sum(1 for cid, x in data['cities'].items() if motion_match(data, m, cid, x)[0])} destinations",
             m["name"], m["strapline"], seed="motion:" + m["slug"],
             motif=motif_for(m.get("interests", [])))
        for m in data["motions"][:6]
    ]
    months = data["taxonomy"]["months"]
    names = data["taxonomy"]["month_names"]
    month_chips = "".join(
        f'<a class="chip" href="{urls.month(m)}">{esc(names[m])}</a>' for m in months
    )
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
  <p class="lede">Every other page here asks you to already know where you want to go — a
  country, a region, a sentence. This one does not. Say what you are travelling for and
  {len(data['cities'])} places across {len(data['countries'])} countries will narrow
  themselves, and each one will tell you why it is on the list.</p>
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

{section("By where it is", grid(macro_cards, 3),
         lede="Nine regions of Europe, grouped by shared coast, shared mountain range and shared history rather than by alphabet.",
         more=("Every country, A to Z", "/countries"))}

{section("By what you travel for", '<div class="grid cols-4">' + interest_cards + "</div>",
         lede="Seventeen tags. The Journey Planner weights the same ones, so what you see here is what it will build from.",
         more=("Cross-border themes", "/themes"))}

{section("Europe in Motion", grid(motion_cards, 3),
         lede="A dozen ways to cut the continent, each one a query run against every destination on every build rather than a list somebody chose. Each page prints the query that made it.",
         more=("All twelve", "/europe-in"))}

{section("By month", f'<div class="chips">{month_chips}</div>',
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


PRELAUNCH = """<div class="note warn">
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
    <p>Every illustration is generated from the place's own name. No licence to expire, no
    stock library, and no risk of publishing somebody's holiday photograph.</p>
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
    <p>Five countries have been taken to depth so far. The rest are at a solid first pass.
    <a href="/countries">Which is which →</a></p>
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
      The repository's issue tracker is the honest channel while this is a pre-launch
      editorial project, and every correction is public that way, which is better.</li>
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
