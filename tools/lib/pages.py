"""Every page Europedoor publishes.

Each builder returns (path, html). The build writes them; nothing here
touches the filesystem, so a page can be rendered and asserted against in a
test without a build directory existing.
"""

from __future__ import annotations

import math

from . import urls
from .render import (SITE_NAME, card, chips, crumbs, esc, factlist, grid,
                     jsonscript, page, plate, section)
from .score import city_scores, country_scores

HOME = ("Europe", "/atlas")


def haversine(a, b):
    """Kilometres between two {lat, lon} points. Used for realistic hops."""
    R = 6371.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p2 - p1
    dl = math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(h)))


def hop_note(km):
    """How you would actually cover that distance, in one line."""
    if km < 90:
        return f"{km} km — a local train or a short drive"
    if km < 400:
        return f"{km} km — a comfortable train leg, half a day at most"
    if km < 900:
        return f"{km} km — a long rail day, or a short flight if the days are tight"
    return f"{km} km — fly, or give the overland crossing a day of its own"


def advisory_note(c):
    a = c.get("advisory")
    if not a:
        return ""
    heading = "Check government travel advice before planning anything here"
    return f"""<div class="note warn">
  <h3>{esc(heading)}</h3>
  <p>{esc(a['note'])}</p>
  <p class="small">Europedoor keeps a page for every country in Europe, including the ones nobody
  should be travelling to right now. A page here is a record, not a recommendation, and
  countries at this level are excluded from the Journey Planner.</p>
</div>"""


def bloc_line(data, c):
    names = data["taxonomy"]["blocs"]
    got = [names[b] for b in c.get("blocs", []) if b in names]
    return ", ".join(got) if got else "No EU or Schengen membership"


def months_line(data, keys):
    names = data["taxonomy"]["month_names"]
    return ", ".join(names[m] for m in keys)


# ── home ──────────────────────────────────────────────────────────────

def home(data):
    macros = data["macros"]
    countries = data["countries"]
    n_by_interest = {
        i["slug"]: sum(1 for n in data["cities"].values() if i["slug"] in n["city"]["interests"])
        for i in data["taxonomy"]["interests"]
    }
    cards = []
    for m in macros[:6]:
        n = len(m["countries"])
        cards.append(
            card(urls.macro(m), f"{n} countries", m["name"], m["blurb"], seed="macro:" + m["slug"])
        )
    jcards = [
        card(
            urls.journey(j), f"{j['days']} days · {len(j['legs'])} stops", j["name"], j["strapline"],
            seed="journey:" + j["slug"],
        )
        for j in data["journeys"][:3]
    ]
    ncountries = len(countries)
    ncities = len(data["cities"])
    nregions = sum(len(c["regions"]) for c in countries.values())

    interest_grid = '<div class="grid cols-4">' + "".join(
        f"""<a class="card" href="{urls.interest(i['slug'])}"><div class="card-body">
        <p class="kicker"><span aria-hidden="true">{esc(i['icon'])}</span> {n_by_interest[i['slug']]} cities</p>
        <h3>{esc(i['name'])}</h3></div></a>"""
        for i in data["taxonomy"]["interests"]
    ) + "</div>"

    quiet = [n for n in data["cities"].values() if n["city"].get("quiet")]
    nquiet = len(quiet)
    quietcards = [
        card(urls.city(n["country"], n["region"], n["city"]),
             f"{n['country']['name']} · {n['region']['name']}", n["city"]["name"],
             n["city"]["summary"], seed=f"city:{n['country']['slug']}:{n['city']['slug']}")
        for n in sorted(quiet, key=lambda n: n["city"]["name"])[:3]
    ]
    storycards = [
        card(f"/stories/{st['slug']}", st["section"], st["title"], st["standfirst"],
             seed="story:" + st["slug"], meta=f'<p class="cardmeta">{esc(st["reading"])}</p>')
        for st in data["stories"][:3]
    ]

    pillars = "".join(
        f"""<div class="card"><div class="card-body">
        <p class="kicker">{esc(k)}</p><h3>{esc(t)}</h3><p class="blurb">{esc(b)}</p></div></div>"""
        for k, t, b in [
            ("One", "Europe Atlas", "Every country, then its travel regions, then its cities, then the things you would actually do there. One shape, all the way down."),
            ("Two", "Journey Planner", "Tell it how many days you have, what you can spend and what you like. It returns a real itinerary with real distances — not a list of links."),
            ("Three", "European Journeys", "Curated routes that cross borders on purpose: Arctic to Baltic, Atlantic to Mediterranean, the Alpine grand tour."),
            ("Four", "Local Experiences", "Guides, kitchens, museums, cellars and boats, listed by the people who run them and checked before they appear."),
            ("Five", "Europe Fund", "Where travel money could go back: heritage repair, language survival, trail maintenance, coastline. Listed openly, long before a single euro moves."),
        ]
    )

    dots = []
    for cid, n in sorted(data["cities"].items()):
        x, y = project(n["city"]["lat"], n["city"]["lon"])
        cls = " advisory" if n["country"].get("advisory") else ""
        dots.append(f'<circle class="herodot{cls}" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
    heromap = (
        f'<a class="heromap" href="/map" aria-label="Map of all {len(data["cities"])} cities in the Atlas">'
        f'<svg viewBox="0 0 {MAP_W} {MAP_H}" aria-hidden="true">{"".join(dots)}</svg>'
        f'<span class="heromap-cap">{len(data["cities"])} cities. Every one has a page.</span></a>'
    )

    body = f"""
<div class="hero">
  <div class="hero-text">
  <p class="kicker">Discover · Plan · Experience</p>
  <h1>One door into Europe.</h1>
  <p class="lede">Fifty countries, their regions, their cities and what is worth your time in
  each — held in one structure, so a fjord in Vestland and a cellar in Alentejo can appear in
  the same itinerary without either being flattened into a listicle.</p>
  <div class="hero-actions">
    <a class="btn" href="/plan">Plan a journey</a>
    <a class="btn ghost" href="/atlas">Open the Atlas</a>
    <a class="btn ghost" href="/search">Search everything</a>
  </div>
  <p class="small" style="margin-top:var(--s6)">{ncountries} countries · {nregions} travel regions ·
  {ncities} cities · {len(data['journeys'])} curated journeys</p>
  </div>
  {heromap}
</div>

{section("Nine regions of Europe", grid(cards, 3),
         lede="Europe organised the way people actually travel it — by shared coast, shared mountain range and shared history, not by alphabet.",
         more=("All nine regions of Europe", "/atlas"))}

{section("Five things this is for", grid([pillars], 3) if False else '<div class="grid cols-3">' + pillars + "</div>",
         lede="Not a booking engine with articles bolted on. A structure first, and everything else hung off it.")}

{section("Find your kind of Europe", interest_grid,
         lede="Sixteen ways in. Each one is a real list of places tagged for it, and the Journey Planner weights the same tags.",
         more=("Cross-border themes", "/themes"))}

{section("Journeys across borders", grid(jcards, 3) if jcards else '<p class="small">Curated journeys are being written.</p>',
         lede="A good European trip rarely stays in one country. These do not.",
         more=("Every journey", "/journeys"))}

{section("Beyond the obvious", grid(quietcards, 3),
         lede=f"{nquiet} places tagged quiet in the dataset — the goods without the crowd. Europe's problem is not the number of visitors; it is that they arrive in the same eleven places in the same six weeks.",
         more=("Every quiet place, and six straight swaps", "/beyond-the-obvious"))}

{section("Stories from Europe", grid(storycards, 3),
         lede="A continent is people before it is places. Every story links into the Atlas, and every place it touches links back.",
         more=("The whole desk", "/stories"))}

<div class="band">
  <div class="band-head"><h2>Tell it what you have. It builds the route.</h2>
  <p class="lede">Twelve days, €2,500, history and mountains — in your own words or in a form.
  The planner reads the whole Atlas, scores every city against you, respects distance, and
  runs entirely in your browser.</p></div>
  <div class="hero-actions" style="margin-top:0">
    <a class="btn" href="/plan">Plan a journey</a>
    <a class="btn ghost" href="/map">See all {ncities} on the map</a>
  </div>
</div>

<div class="note">
  <h3>What this is, honestly</h3>
  <p>Europedoor is pre-launch and editorial. Nothing here takes a payment, holds money or
  makes a booking, and the Europe Fund deliberately carries no balances yet — see
  <a href="/how-it-works">how it works</a> for exactly which parts are built, which are
  designed and which are still questions.</p>
</div>
"""
    return "/index.html", page(
        SITE_NAME, body, path="/", area=None,
        description="Discover, plan and experience Europe: an atlas of every country, region and city, a journey planner, curated cross-border routes and local experiences.",
    )


# ── atlas ─────────────────────────────────────────────────────────────

def atlas(data):
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
            <h2><a href="{urls.macro(m)}" style="text-decoration:none">{esc(m['name'])}</a></h2>
            <p class="lede">{esc(m['blurb'])}</p></div>
            <div class="rows">{''.join(rows)}</div></section>"""
        )
    body = f"""
{crumbs([("Europe", "/atlas"), ("Atlas", None)])}
<div class="pagehead">
  <p class="kicker">The Atlas</p>
  <h1>Europe, all the way down.</h1>
  <p class="lede">Nine regions, {len(data['countries'])} countries, {sum(len(c['regions']) for c in data['countries'].values())}
  travel regions and {len(data['cities'])} cities. The regions below are editorial travel regions,
  not administrative ones: they group places that feel like each other and are usually visited together.</p>
</div>
{''.join(blocks)}
"""
    return "/atlas/index.html", page(
        "Atlas", body, path="/atlas", area="atlas",
        description="Every country in Europe, grouped into nine travel regions, each opening onto its regions, cities and experiences.",
    )


def macro_page(data, m):
    cards = []
    for cs in m["countries"]:
        c = data["countries"][cs]
        ncity = sum(len(r["cities"]) for r in c["regions"])
        meta = f'<p class="cardmeta">{len(c["regions"])} regions · {ncity} cities · {esc(c["budget"])} cost</p>'
        cards.append(card(urls.country(c), c["capital"], c["name"], c["tagline"], seed="country:" + c["slug"], meta=meta))
    body = f"""
{crumbs([("Europe", "/atlas"), ("Atlas", "/atlas"), (m["name"], None)])}
<div class="pagehead">
  <p class="kicker">Region of Europe</p>
  <h1>{esc(m['name'])}</h1>
  <p class="lede">{esc(m['blurb'])}</p>
</div>
{grid(cards, 3)}
"""
    return f"/atlas/{m['slug']}/index.html", page(
        m["name"], body, path=urls.macro(m), area="atlas",
        description=m["blurb"],
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
        f"""<div class="row"><div><h3>{esc(f['name'])}</h3>
        <p class="rowsub">{esc(f.get('where', ''))}</p></div>
        <p class="rowmeta">{esc(data['taxonomy']['month_names'][f['month']])}</p></div>"""
        for f in c["festivals"]
    )
    know = "".join(f"<li>{esc(k)}</li>" for k in c["know"])
    food = "".join(f"<li>{esc(f)}</li>" for f in c["food"])
    facts = factlist([
        ("Capital", esc(c["capital"])),
        ("Currency", esc(c["currency"])),
        ("Languages", esc(", ".join(c["languages"]))),
        ("Membership", esc(bloc_line(data, c))),
        ("Typical day", f"€{c['daily_eur'][0]}–{c['daily_eur'][1]} per person"),
        ("Best months", esc(months_line(data, c["season"]["peak"]))),
        ("Quieter months", esc(months_line(data, c["season"].get("shoulder", [])))),
    ])
    body = f"""
{crumbs([("Europe", "/atlas"), ("Atlas", "/atlas"), (m["name"], urls.macro(m)), (c["name"], None)])}
<div class="pagehead">
  <p class="kicker">{esc(m['name'])}</p>
  <h1>{esc(c['name'])}</h1>
  <p class="lede">{esc(c['tagline'])}</p>
</div>
{advisory_note(c)}
<div class="split">
  <div>
    <p>{esc(c['summary'])}</p>
    {chips(c["interests"], data["interests"])}
    {facts}
    {scorebars(country_scores(c))}
    <h2 id="getting-around" style="margin-top:var(--s7)">Getting around</h2>
    <p>{esc(c['getting_around'])}</p>
    <h2 id="when" style="margin-top:var(--s7)">When to come</h2>
    <p>{esc(c['season']['note'])}</p>
  </div>
  <aside class="rail">
    <h3>Worth knowing</h3>
    <ul>{know}</ul>
    <h3>At the table</h3>
    <ul>{food}</ul>
  </aside>
</div>

{section("Travel regions", grid(region_cards, 3),
         lede=f"{len(c['regions'])} editorial regions, each opening onto its cities.")}

{section("Fixed points in the year", f'<div class="rows">{festivals}</div>') if festivals else ""}
"""
    return f"/atlas/{c['macro_slug']}/{c['slug']}/index.html", page(
        c["name"], body, path=urls.country(c), area="atlas",
        description=c["summary"][:180],
    )


def region_page(data, c, r):
    m = next(x for x in data["macros"] if x["slug"] == c["macro_slug"])
    cards = []
    for t in r["cities"]:
        nights = t["nights"]
        n = f"{nights[0]}–{nights[1]} nights" if nights[0] != nights[1] else f"{nights[0]} nights"
        meta = f'<p class="cardmeta">{n}</p>'
        cards.append(card(urls.city(c, r, t), c["name"], t["name"], t["summary"], seed=f"city:{c['slug']}:{t['slug']}", meta=meta))
    body = f"""
{crumbs([("Europe", "/atlas"), ("Atlas", "/atlas"), (m["name"], urls.macro(m)),
         (c["name"], urls.country(c)), (r["name"], None)])}
<div class="pagehead">
  <p class="kicker">{esc(c['name'])}</p>
  <h1>{esc(r['name'])}</h1>
  <p class="lede">{esc(r['summary'])}</p>
  {chips(r["interests"], data["interests"])}
</div>
{grid(cards, 3)}
"""
    return f"/atlas/{c['macro_slug']}/{c['slug']}/{r['slug']}/index.html", page(
        f"{r['name']}, {c['name']}", body, path=urls.region(c, r), area="atlas",
        description=r["summary"][:180],
    )


def city_page(data, c, r, t):
    m = next(x for x in data["macros"] if x["slug"] == c["macro_slug"])
    cid = f"{c['slug']}/{r['slug']}/{t['slug']}"
    highlights = "".join(f"<li>{esc(h)}</li>" for h in t["highlights"])
    kinds = data["taxonomy"]["experience_kinds"]
    exps = "".join(
        f"""<div class="row"><div><h3>{esc(e['name'])}</h3>
        <p class="rowsub">{esc(e['summary'])}</p></div>
        <p class="rowmeta">{esc(kinds[e['kind']])} · {esc(e['band'])}</p></div>"""
        for e in t.get("experiences", [])
    )
    # Nearby cities, computed rather than curated: the same distance function
    # the planner uses, so the two never disagree about what is close.
    others = [n for n in data["cities"].values() if n["city"] is not t]
    near = sorted(others, key=lambda n: haversine(t, n["city"]))[:6]
    nearrows = "".join(
        f"""<a class="row" href="{urls.city(n['country'], n['region'], n['city'])}">
        <div><h3>{esc(n['city']['name'])}</h3><p class="rowsub">{esc(n['country']['name'])} · {esc(n['region']['name'])}</p></div>
        <p class="rowmeta">{esc(hop_note(haversine(t, n['city'])))}</p></a>"""
        for n in near
    )
    nights = t["nights"]
    stay = f"{nights[0]}–{nights[1]} nights" if nights[0] != nights[1] else f"{nights[0]} nights"

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
    fest = [f for f in c["festivals"]]
    festrows = "".join(
        f"""<div class="row"><div><h3>{esc(f['name'])}</h3>
        <p class="rowsub">{esc(f.get('where', ''))}</p></div>
        <p class="rowmeta">{esc(data['taxonomy']['month_names'][f['month']])}</p></div>"""
        for f in fest
    )
    body = f"""
{crumbs([("Europe", "/atlas"), ("Atlas", "/atlas"), (m["name"], urls.macro(m)),
         (c["name"], urls.country(c)), (r["name"], urls.region(c, r)), (t["name"], None)])}
<div class="pagehead">
  <p class="kicker">{esc(r['name'])}, {esc(c['name'])}</p>
  <h1>{esc(t['name'])}</h1>
  <p class="lede">{esc(t['summary'])}</p>
  {chips(t["interests"], data["interests"])}
</div>
<div class="card-art" style="max-width:100%;border:1px solid var(--rule);border-radius:var(--radius);aspect-ratio:21/9;overflow:hidden">
{plate(f"city:{c['slug']}:{t['slug']}", 1260, 540, t['name'])}
</div>
<div class="split" style="margin-top:var(--s7)">
  <div>
    <h2>What earns the time</h2>
    <ul class="stack">{highlights}</ul>
    {scorebars(city_scores(c, r, t))}
    {section("Experiences here", f'<div class="rows">{exps}</div>') if exps else ""}
    {section("Fixed points in the year", f'<div class="rows">{festrows}</div>',
             lede=f"Nationwide fixtures in {c['name']}. See the whole European year on /events.") if festrows else ""}
  </div>
  <aside class="rail">
    <h3>Give it {esc(stay)}</h3>
    <p>Enough to see the list on the left without spending the trip on trains. The Journey
    Planner uses exactly this range when it builds an itinerary.</p>
    <h3>When to come</h3>
    <p>Best: {esc(months_line(data, c["season"]["peak"]))}. Quieter:
    {esc(months_line(data, c["season"].get("shoulder", [])) or "—")}.
    <a href="{urls.country(c)}#when">Why, and what that means →</a></p>

    <h3>Getting there</h3>
    <p>{esc(c['getting_around'][:150])}…
    <a href="{urls.country(c)}#getting-around">All of {esc(c['name'])} →</a></p>

    <h3>Where you are</h3>
    <p class="mono">{t['lat']:.2f}°N, {t['lon']:.2f}°E</p>
    <p><a href="/plan?from={esc(c['slug'])}%2F{esc(r['slug'])}%2F{esc(t['slug'])}">Start a journey here →</a></p>
    <p><button class="btn ghost" type="button" data-save="city:{esc(cid)}" data-kind="Place" data-label="{esc(t['name'])}, {esc(c['name'])}" data-url="{urls.city(c, r, t)}">Save to My Europe</button></p>
  </aside>
</div>
{section("Nearest onward stops", f'<div class="rows">{nearrows}</div>',
         lede="Straight-line distance, and what that usually means in practice.")}
{edges}
"""
    return f"/atlas/{c['macro_slug']}/{c['slug']}/{r['slug']}/{t['slug']}/index.html", page(
        f"{t['name']}, {c['name']}", body, path=urls.city(c, r, t), area="atlas",
        description=t["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
    )


# ── interests ─────────────────────────────────────────────────────────

def interest_page(data, i):
    slug = i["slug"]
    cities = [n for n in data["cities"].values() if slug in n["city"]["interests"]]
    cities.sort(key=lambda n: (n["country"]["name"], n["city"]["name"]))
    countries = sorted({n["country"]["slug"] for n in cities})
    cards = [
        card(
            urls.city(n["country"], n["region"], n["city"]),
            f"{n['country']['name']} · {n['region']['name']}",
            n["city"]["name"], n["city"]["summary"],
            seed=f"city:{n['country']['slug']}:{n['city']['slug']}",
        )
        for n in cities[:60]
    ]
    body = f"""
{crumbs([("Europe", "/atlas"), ("Interests", "/atlas"), (i["name"], None)])}
<div class="pagehead">
  <p class="kicker">Travelling for</p>
  <h1>{esc(i['name'])}</h1>
  <p class="lede">{len(cities)} cities across {len(countries)} countries are tagged for this.
  The Journey Planner weights the same tag, so what you see here is what it will build from.</p>
</div>
{grid(cards, 3) if cards else '<p class="small">Nothing tagged yet.</p>'}
"""
    return f"/interests/{slug}/index.html", page(
        i["name"], body, path=urls.interest(slug), area="atlas",
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
        meta = f'<p class="cardmeta">{j["days"]} days · {len(countries)} countries · {esc(j["budget"])}</p>'
        cards.append(card(urls.journey(j), j["strapline"], j["name"], j["summary"][:150] + "…",
                          seed="journey:" + j["slug"], meta=meta))
    body = f"""
{crumbs([("Europe", "/atlas"), ("Journeys", None)])}
<div class="pagehead">
  <p class="kicker">European Journeys</p>
  <h1>Routes that cross borders on purpose.</h1>
  <p class="lede">Each of these is a real sequence with real distances: every stop links back
  into the Atlas, and the nights add up to the days on the tin. Take one as written, or open it
  in the Planner and bend it to the time you actually have.</p>
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
    for leg in j["legs"]:
        n = idx[leg["city"]]
        t, r, c = n["city"], n["region"], n["country"]
        hop = ""
        if prev is not None:
            km = haversine(prev, t)
            hop = f'<p class="hop">↳ {esc(hop_note(km))} from {esc(prev["name"])}</p>'
        last = day + leg["nights"] - 1
        when = f"Day {day}" if leg["nights"] == 1 else f"Days {day}–{last}"
        legs.append(
            f"""<li class="leg">
            <div class="leg-when">{esc(when)}</div>
            <div><h3><a href="{urls.city(c, r, t)}">{esc(t['name'])}</a>
            <span class="small">· {esc(c['name'])}</span></h3>
            <p>{esc(leg['why'])}</p>{hop}</div></li>"""
        )
        day = last + 1
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
    facts = factlist([
        ("Length", f"{j['days']} days"),
        ("Countries", esc(" → ".join(countries))),
        ("Ground covered", f"{total_km:,} km between stops"),
        ("Budget shape", esc(j["budget"])),
        ("Months that work", esc(months_line(data, j["months"]))),
    ])
    body = f"""
{crumbs([("Europe", "/atlas"), ("Journeys", "/journeys"), (j["name"], None)])}
<div class="pagehead">
  <p class="kicker">{esc(j['strapline'])}</p>
  <h1>{esc(j['name'])}</h1>
</div>
<div class="card-art" style="border:1px solid var(--rule);border-radius:var(--radius);aspect-ratio:21/9;overflow:hidden">
{plate("journey:" + j["slug"], 1260, 540, j["name"])}
</div>
<div class="split" style="margin-top:var(--s7)">
  <div>
    <p class="lede">{esc(j['summary'])}</p>
    {chips(j["interests"], data["interests"])}
    {facts}
    <h2>The route</h2>
    <ul class="legs">{''.join(legs)}</ul>
  </div>
  <aside class="rail">
    <h3>Make it yours</h3>
    <p>Fewer days than this? The Planner will keep the stops that match what you said you
    care about and drop the rest, rather than shortening every night.</p>
    <p><a class="btn" href="/plan#journey={esc(j['slug'])}">Open in the Planner</a></p>
    <p><button class="btn ghost" type="button" data-save="journey:{esc(j['slug'])}" data-kind="Journey"
       data-label="{esc(j['name'])}" data-url="{urls.journey(j)}">Save to My Europe</button></p>
    <h3>How to read a leg</h3>
    <p>Distances are straight-line between stops. Rail beats the straight line in the Alps and
    loses badly across the Adriatic — the note under each hop says which.</p>
  </aside>
</div>
"""
    return f"/journeys/{j['slug']}/index.html", page(
        j["name"], body, path=urls.journey(j), area="journeys",
        description=j["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
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
    budgets = "".join(
        f'<option value="{esc(b["slug"])}"{" selected" if b["slug"] == "moderate" else ""}>'
        f'{esc(b["name"])} — {esc(b["note"])}</option>'
        for b in data["taxonomy"]["budgets"]
    )
    body = f"""
{crumbs([("Europe", "/atlas"), ("Plan", None)])}
<div class="pagehead">
  <p class="kicker">Journey Planner</p>
  <h1>Twelve days, €2,500, history and mountains.</h1>
  <p class="lede">Say what you have and what you like — in a sentence or in the form. The planner reads the whole Atlas —
  {len(data['cities'])} cities across {len(data['countries'])} countries — scores every one against
  you, then builds a route that respects distance instead of teleporting between highlights.
  It runs entirely in your browser; nothing you type is sent anywhere.</p>
</div>

<form class="form ask" id="askform">
  <div class="field">
    <label for="ask">Say it in your own words</label>
    <textarea id="ask" name="ask" rows="2"
      placeholder="I have 12 days and €2,500, starting in Lisbon, and I love history, mountains and food."></textarea>
  </div>
  <div class="hero-actions" style="margin-top:0">
    <button class="btn" type="submit">Read that and build it</button>
  </div>
  <p class="small" style="margin-bottom:0">Read by rules in your browser — not by a model, and
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
      <fieldset class="fieldset">
        <legend>What are you travelling for?</legend>
        <div class="checks">{interests}</div>
      </fieldset>
      <div class="hero-actions" style="margin-top:0">
        <button class="btn" type="submit">Build the itinerary</button>
        <button class="btn ghost" type="button" id="again">Give me a different one</button>
      </div>
    </form>
    <div id="result" aria-live="polite"></div>
  </div>
  <aside class="rail">
    <h3>How it decides</h3>
    <ul>
      <li>Every city is scored on how many of your interests it carries, at region and city level.</li>
      <li>The month you pick moves the score: peak season up, off season down, never to zero.</li>
      <li>Each next stop is penalised by distance, so the route stops wandering.</li>
      <li>Nights come from the range on each city page, stretched or squeezed by your pace.</li>
      <li>Cost is nights × the country's daily band, plus a distance-based transport estimate.</li>
    </ul>
    <h3>What it will not do</h3>
    <p>It will not book anything, price a real hotel, or route you into a country under a
    travel advisory — those are excluded from the planning index entirely.</p>
    <p class="small">Estimates are editorial, not quotes. Check <a href="/sources">sources and
    corrections</a>.</p>
  </aside>
</div>
"""
    return "/plan/index.html", page(
        "Plan a journey", body, path="/plan", area="plan",
        description="Tell Europedoor your days, budget and interests and it builds a European itinerary with real distances, real night counts and a cost estimate.",
        scripts=["/assets/js/planner.js"],
    )


# ── the score ─────────────────────────────────────────────────────────

def scorebars(scores):
    from .score import DIMENSIONS, LABELS
    rows = "".join(
        f"""<div class="scorerow"><span class="scorelabel">{esc(LABELS[d])}</span>
        <span class="scorebar"><span style="width:{scores[d]}%"></span></span>
        <span class="scorenum">{scores[d]}</span></div>"""
        for d in DIMENSIONS
    )
    return f"""<div class="score">
    <p class="kicker">Europe Experience Score</p>{rows}
    <p class="small"><a href="/method">How this is calculated</a> — derived from our own tagging,
    not from measurement. It says what a place is for, not how good it is.</p></div>"""


# ── experiences & the marketplace ─────────────────────────────────────

def experiences_index(data):
    from .data import all_experiences
    kinds = data["taxonomy"]["experience_kinds"]
    items = all_experiences(data["countries"])
    counts = {}
    for it in items:
        counts[it["exp"]["kind"]] = counts.get(it["exp"]["kind"], 0) + 1
    cards = [
        card(urls.experience_kind(k), f"{counts.get(k, 0)} listed", name,
             "Things people do here, written up by the people who run them or by us, and checked before they appear.",
             seed="kind:" + k)
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
{crumbs([("Europe", "/atlas"), ("Experiences", None)])}
<div class="pagehead">
  <p class="kicker">Local Experiences</p>
  <h1>What people actually do here.</h1>
  <p class="lede">{len(items)} experiences across the Atlas, in ten kinds. Anything a business
  lists carries the name of who runs it and the tier of checking it has passed — an unchecked
  listing says so on its face rather than hiding behind a star rating.</p>
  <div class="hero-actions"><a class="btn" href="/experiences/join">List your experience</a>
  <a class="btn ghost" href="/business">For businesses</a></div>
</div>
{grid(cards, 4)}
{section("Recently added", f'<div class="rows">{rows}</div>')}
"""
    return "/experiences/index.html", page(
        "Experiences", body, path="/experiences", area="experiences",
        description="Guides, kitchens, cellars, boats and museums across Europe — every listing named, tiered and checked.",
    )


def experience_kind_page(data, kind, name):
    from .data import all_experiences
    items = [it for it in all_experiences(data["countries"]) if it["exp"]["kind"] == kind]
    items.sort(key=lambda it: (it["country"]["name"], it["city"]["name"]))
    rows = "".join(
        f"""<a class="row" href="{urls.city(it['country'], it['region'], it['city'])}">
        <div><h3>{esc(it['exp']['name'])}</h3><p class="rowsub">{esc(it['exp']['summary'])}</p></div>
        <p class="rowmeta">{esc(it['city']['name'])}, {esc(it['country']['name'])} · {esc(it['exp']['band'])}</p></a>"""
        for it in items
    )
    body = f"""
{crumbs([("Europe", "/atlas"), ("Experiences", "/experiences"), (name, None)])}
<div class="pagehead">
  <p class="kicker">{len(items)} across Europe</p>
  <h1>{esc(name)}</h1>
</div>
<div class="rows">{rows or '<p class="small">Nothing listed yet.</p>'}</div>
"""
    return f"/experiences/{kind}/index.html", page(
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
{crumbs([("Europe", "/atlas"), ("Experiences", "/experiences"), ("List your experience", None)])}
<div class="pagehead">
  <p class="kicker">For guides, kitchens, museums and operators</p>
  <h1>List what you do.</h1>
  <p class="lede">Europedoor lists experiences run by people who live where they happen.
  Listing is free. What costs is prominence, and we say so on the page rather than quietly
  sorting paid listings to the top.</p>
</div>
<div class="split">
  <div>
    <h2>Three tiers, and what each one means</h2>
    {grid([tiers], 3) if False else '<div class="grid cols-3">' + tiers + '</div>'}
    <h2 style="margin-top:var(--s7)">What we check</h2>
    <ul class="stack">
      <li><strong>You exist.</strong> A registered business or a licensed guide number in the country you operate in.</li>
      <li><strong>You are there.</strong> An address, a phone that answers, and a person whose name goes on the listing.</li>
      <li><strong>You are insured</strong> where the activity requires it — water, height, vehicles, food service.</li>
      <li><strong>You said what it costs</strong>, including what is not included.</li>
    </ul>
    <h2 style="margin-top:var(--s7)">What we will not do</h2>
    <ul class="stack">
      <li>Sell placement inside the Journey Planner. The planner scores on fit and distance; money does not enter it.</li>
      <li>Publish a listing whose owner we could not reach.</li>
      <li>Take a booking on your behalf until the payments and consumer-law work in
      <a href="/how-it-works">how it works</a> is finished and reviewed.</li>
    </ul>
    <div class="note">
      <h3>Applications are not open yet</h3>
      <p>This page describes the model so operators can tell whether it is worth their time.
      There is no form here on purpose: we will not collect business details before there is
      an entity to hold them and a published privacy notice to hold them under.</p>
    </div>
  </div>
  <aside class="rail">
    <h3>Directory tiers &amp; indicative pricing</h3>
    <p>Free listing · Professional €49–99 per month · Premium €199+ per month.</p>
    <p class="small">Indicative only, and untested. Pricing gets set after a hundred conversations
    with operators, not before.</p>
    <h3>Commission</h3>
    <p>When bookings exist, the intended range is 10–15% on experiences sold through the platform,
    with the operator setting the price and keeping the customer relationship.</p>
  </aside>
</div>
"""
    return "/experiences/join/index.html", page(
        "List your experience", body, path="/experiences/join", area="experiences",
        description="How guides, restaurants, museums and operators appear on Europedoor: three tiers, what is checked, and what placement never buys.",
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
{crumbs([("Europe", "/atlas"), ("For business", None)])}
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
    <h3>The wall between editorial and commerce</h3>
    <p>Paid tiers buy presentation on directory surfaces. They never buy Atlas ranking,
    Journey Planner weighting, or a place in a curated journey. If that wall ever moves, it
    moves in public, on this page.</p>
    <h3>Claiming a profile</h3>
    <p>Not open yet — same reason as <a href="/experiences/join">listings</a>.</p>
  </aside>
</div>
"""
    return "/business/index.html", page(
        "For business", body, path="/business", area="experiences",
        description="Europedoor's European business directory: profiles for hotels, operators, guides and institutions, three verification tiers, and a stated wall between paid placement and editorial.",
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
{crumbs([("Europe", "/atlas"), ("Fund", None)])}
<div class="pagehead">
  <p class="kicker">Europe Fund</p>
  <h1>What travel leaves behind.</h1>
  <p class="lede">Tourism arrives in a place and takes something out of it — a path, a language,
  a harbour wall, a summer. The Fund is the mechanism for putting something back, listed
  publicly, project by project, with the local partner named.</p>
</div>

<div class="note warn">
  <h3>The Fund holds no money, and will not until three things are true</h3>
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
    )


def fund_page(data, p):
    c = data["countries"][p["country"]]
    body = f"""
{crumbs([("Europe", "/atlas"), ("Fund", "/fund"), (p["name"], None)])}
<div class="pagehead">
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
               ("Money held by Europedoor", "None — see the note")])}
  </div>
  <aside class="rail">
    <h3>No balance shown, on purpose</h3>
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
             seed="theme:" + t["slug"])
        for t in data["themes"]
    ]
    body = f"""
{crumbs([("Europe", "/atlas"), ("Themes", None)])}
<div class="pagehead">
  <p class="kicker">Discovery without a map of borders</p>
  <h1>Europe, organised by what you came for.</h1>
  <p class="lede">Medieval Europe is not a country. Neither is sacred Europe, or Viking Europe,
  or the Europe you reach only by train. These cut across the Atlas: each one is a real
  sequence of real places, and each place stays linked to the country it is actually in.</p>
</div>
{grid(cards, 3)}
"""
    return "/themes/index.html", page(
        "Themes", body, path="/themes", area="atlas",
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
    body = f"""
{crumbs([("Europe", "/atlas"), ("Themes", "/themes"), (t["name"], None)])}
<div class="pagehead">
  <p class="kicker">{esc(t['strapline'])}</p>
  <h1>{esc(t['name'])}</h1>
  <p class="lede">{esc(t['summary'])}</p>
  {chips(t["interests"], data["interests"])}
</div>
<div class="split">
  <div>
    <h2>{len(t['stops'])} places, {len(countries)} countries</h2>
    <div class="rows">{''.join(rows)}</div>
  </div>
  <aside class="rail">
    <h3>Not an itinerary</h3>
    <p>A theme is a way of seeing, not a route: these places are not in travelling order and
    most people take three or four of them, not all. For an order that respects distance,
    put the ones you want into the <a href="/plan">Planner</a>.</p>
    <h3>Countries</h3>
    <p>{esc(", ".join(countries))}</p>
    <p><button class="btn ghost" type="button" data-save="theme:{esc(t['slug'])}" data-kind="Theme"
       data-label="{esc(t['name'])}" data-url="/themes/{esc(t['slug'])}">Save to My Europe</button></p>
  </aside>
</div>
"""
    return f"/themes/{t['slug']}/index.html", page(
        t["name"], body, path=f"/themes/{t['slug']}", area="atlas",
        description=t["summary"][:180],
        scripts=["/assets/js/my-europe.js"],
    )


# ── stories ───────────────────────────────────────────────────────────

def stories_index(data):
    cards = [
        card(f"/stories/{s['slug']}", s["section"], s["title"], s["standfirst"],
             seed="story:" + s["slug"], meta=f'<p class="cardmeta">{esc(s["reading"])}</p>')
        for s in data["stories"]
    ]
    sections = sorted({s["section"] for s in data["stories"]})
    body = f"""
{crumbs([("Europe", "/atlas"), ("Stories", None)])}
<div class="pagehead">
  <p class="kicker">Stories</p>
  <h1>A continent is people before it is places.</h1>
  <p class="lede">{len(data['stories'])} pieces across {len(sections)} desks — people, history,
  food, faith, nature and culture. Every story links into the Atlas, and every Atlas page that
  a story touches links back, so reading and planning are the same motion.</p>
</div>
{grid(cards, 3)}
"""
    return "/stories/index.html", page(
        "Stories", body, path="/stories", area=None,
        description="Editorial from across Europe: people, history, food, faith, nature and culture, each linked into the Atlas.",
    )


def story_page(data, s):
    paras = "".join(f"<p>{esc(p)}</p>" for p in s["body"])
    links = ""
    if s.get("places"):
        rows = "".join(
            f"""<a class="row" href="{urls.city_by_id(data['cities'], cid)}">
            <div><h3>{esc(data['cities'][cid]['city']['name'])}</h3>
            <p class="rowsub">{esc(data['cities'][cid]['country']['name'])}</p></div>
            <p class="rowmeta">In the Atlas</p></a>"""
            for cid in s["places"]
        )
        links = section("Where this happens", f'<div class="rows">{rows}</div>')
    body = f"""
{crumbs([("Europe", "/atlas"), ("Stories", "/stories"), (s["title"], None)])}
<article>
<div class="pagehead">
  <p class="kicker">{esc(s['section'])} · {esc(s['reading'])}</p>
  <h1>{esc(s['title'])}</h1>
  <p class="lede">{esc(s['standfirst'])}</p>
</div>
<div class="card-art" style="border:1px solid var(--rule);border-radius:var(--radius);aspect-ratio:21/9;overflow:hidden">
{plate("story:" + s["slug"], 1260, 540, s["title"])}
</div>
<div style="max-width:var(--measure);margin:var(--s7) 0">{paras}</div>
<p><button class="btn ghost" type="button" data-save="story:{esc(s['slug'])}" data-kind="Story"
   data-label="{esc(s['title'])}" data-url="/stories/{esc(s['slug'])}">Save to My Europe</button></p>
</article>
{links}
"""
    return f"/stories/{s['slug']}/index.html", page(
        s["title"], body, path=f"/stories/{s['slug']}", area=None,
        description=s["standfirst"][:180],
        scripts=["/assets/js/my-europe.js"],
    )


# ── the map ───────────────────────────────────────────────────────────

MAP_W, MAP_H = 1000, 780
LON0, LON1, LAT0, LAT1 = -25.0, 45.0, 33.0, 71.5


def project(lat, lon):
    """Equirectangular, corrected at 52°N so Europe is not stretched sideways."""
    k = math.cos(math.radians(52.0))
    x = (lon - LON0) / (LON1 - LON0) * MAP_W
    x = (x - MAP_W / 2) * (k / math.cos(math.radians(52.0))) + MAP_W / 2
    y = (LAT1 - lat) / (LAT1 - LAT0) * MAP_H
    return x, y


def map_page(data):
    dots = []
    for cid, n in sorted(data["cities"].items()):
        c, r, t = n["country"], n["region"], n["city"]
        x, y = project(t["lat"], t["lon"])
        tags = " ".join(sorted(set(t["interests"]) | set(r["interests"])))
        adv = " advisory" if c.get("advisory") else ""
        dots.append(
            f'<a class="dot{adv}" href="{urls.city(c, r, t)}" data-tags="{esc(tags)}" '
            f'data-name="{esc(t["name"])}" data-country="{esc(c["name"])}">'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2"></circle>'
            f'<title>{esc(t["name"])}, {esc(c["name"])}</title></a>'
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
    joptions = "".join(
        f'<option value="{esc(j["slug"])}">{esc(j["name"])} — {j["days"]} days</option>'
        for j in data["journeys"]
    )
    body = f"""
{crumbs([("Europe", "/atlas"), ("Map", None)])}
<div class="pagehead">
  <p class="kicker">The map</p>
  <h1>Every city in the Atlas, at once.</h1>
  <p class="lede">{len(data['cities'])} places, drawn from their own coordinates — no tiles, no
  third-party map service, nothing loaded from anyone else's server. Turn on a layer to see
  where in Europe that thing actually is.</p>
</div>
<div class="checks" id="layers">{filters}</div>
<div class="form-row" style="margin:var(--s4) 0;max-width:34rem">
  <div class="field">
    <label for="journeylayer">Draw a journey over it</label>
    <select id="journeylayer"><option value="">None</option>{joptions}</select>
  </div>
</div>
<p class="small" id="mapcount"></p>
<div class="mapwrap">
<svg viewBox="0 0 {MAP_W} {MAP_H}" class="europemap" role="img" aria-label="Map of European cities in the Atlas">
<rect width="{MAP_W}" height="{MAP_H}" fill="none"/>
<g id="route"></g>
<g id="dots">{''.join(dots)}</g>
</svg>
</div>
<p class="small" id="routenote"></p>
{jsonscript("EUROPEDOOR_JOURNEYS", jdata)}
<div class="note">
  <h3>What this drawing is and is not</h3>
  <p>It is a point map on an equirectangular projection, corrected at 52°N. There are no
  coastlines because we do not have a licence to draw any — the shape you see is Europe's
  cities describing Europe's outline by themselves, which is a fair picture of where people
  live. A tiled basemap is a Stage 2 job with a vendor and a bill attached.</p>
</div>
"""
    return "/map/index.html", page(
        "Map", body, path="/map", area="atlas",
        description="A point map of every city in the Europedoor Atlas, filterable by what you travel for. No third-party tiles.",
        scripts=["/assets/js/map.js"], wide=True,
    )


# ── events ────────────────────────────────────────────────────────────

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
            f"""<a class="row" href="{urls.country(c)}">
            <div><h3>{esc(f['name'])}</h3><p class="rowsub">{esc(f.get('where', ''))}</p></div>
            <p class="rowmeta">{esc(c['name'])}</p></a>"""
            for f, c in items
        )
        blocks.append(
            f'<section class="band" id="{esc(m)}"><div class="band-head">'
            f'<h2><a href="/events/{esc(m)}" style="text-decoration:none">{esc(names[m])}</a></h2>'
            f'<p class="lede">{len(items)} fixed points across Europe. '
            f'<a href="/events/{esc(m)}">Where to go in {esc(names[m])} →</a></p></div>'
            f'<div class="rows">{rows}</div></section>'
        )
    jump = " ".join(
        f'<a class="chip" href="/events/{esc(m)}">{esc(names[m])}</a>'
        for m in data["taxonomy"]["months"]
    )
    total = sum(len(v) for v in by_month.values())
    body = f"""
{crumbs([("Europe", "/atlas"), ("Events", None)])}
<div class="pagehead">
  <p class="kicker">The European year</p>
  <h1>What is on, and when.</h1>
  <p class="lede">{total} recurring fixtures — festivals, markets, pilgrimages, harvests and the
  handful of natural events worth planning a year around. These are the annual, dependable ones.
  Dated listings for a given year need a live events feed, which is Stage 2.</p>
  <div class="chips">{jump}</div>
</div>
{''.join(blocks)}
"""
    return "/events/index.html", page(
        "Events", body, path="/events", area=None,
        description="The recurring European year: festivals, markets, pilgrimages and seasonal events, month by month.",
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
        f"""<a class="row" href="{urls.country(c)}">
        <div><h3>{esc(f['name'])}</h3><p class="rowsub">{esc(f.get('where', ''))}</p></div>
        <p class="rowmeta">{esc(c['name'])}</p></a>"""
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
             n["city"]["summary"], seed=f"city:{n['country']['slug']}:{n['city']['slug']}")
        for n in quiet[:6]
    ]

    ms = data["taxonomy"]["months"]
    i = ms.index(month)
    prev_m, next_m = ms[(i - 1) % 12], ms[(i + 1) % 12]

    body = f"""
{crumbs([("Europe", "/atlas"), ("Events", "/events"), (name, None)])}
<div class="pagehead">
  <p class="kicker">The European year</p>
  <h1>{esc(name)} in Europe</h1>
  <p class="lede">{len(fixtures)} recurring fixtures, {len(peak)} countries at their best and
  {len(shoulder)} in the quieter shoulder — which is usually where you should be going.</p>
  <div class="chips">
    <a class="chip" href="/events/{esc(prev_m)}">← {esc(names[prev_m])}</a>
    <a class="chip" href="/events">The whole year</a>
    <a class="chip" href="/events/{esc(next_m)}">{esc(names[next_m])} →</a>
  </div>
</div>
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
        f"{name} in Europe", body, path=f"/events/{month}", area=None,
        description=f"What is on in Europe in {name}, which countries are at their best, which are in the quieter shoulder season, and where to go instead of the obvious.",
    )


# ── beyond the obvious ────────────────────────────────────────────────

def quiet_page(data):
    quiet = [n for n in data["cities"].values() if n["city"].get("quiet")]
    quiet.sort(key=lambda n: (n["country"]["name"], n["city"]["name"]))
    cards = [
        card(urls.city(n["country"], n["region"], n["city"]),
             f"{n['country']['name']} · {n['region']['name']}", n["city"]["name"], n["city"]["summary"],
             seed=f"city:{n['country']['slug']}:{n['city']['slug']}")
        for n in quiet
    ]
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
{crumbs([("Europe", "/atlas"), ("Beyond the obvious", None)])}
<div class="pagehead">
  <p class="kicker">Responsible travel, stated plainly</p>
  <h1>Beyond the obvious.</h1>
  <p class="lede">Europe's problem is not too many visitors; it is too many visitors in the same
  eleven places in the same six weeks. Every part of this platform is built to push the other
  way — the Planner rewards shoulder months, the Atlas gives a Galician fishing town the same
  page template as Paris, and this is where the quiet places are listed on purpose.</p>
</div>
{section(f"{len(quiet)} places we would send you instead", grid(cards, 3),
         lede="Tagged quiet in the dataset: places with the goods and without the crowd. The tag is editorial and we will be wrong sometimes.")}
{section("Six straight swaps", f'<div class="rows">{swaps}</div>',
         lede="Same idea, different pressure.")}
<div class="note">
  <h3>The rule we hold ourselves to</h3>
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
{crumbs([("Europe", "/atlas"), ("My Europe", None)])}
<div class="pagehead">
  <p class="kicker">My Europe</p>
  <h1>The list you are building.</h1>
  <p class="lede">Saved places, saved journeys, saved stories. This lives in your browser and
  nowhere else — there is no account, no server, no email address, and nothing to leak. When
  accounts arrive, this list will be importable into one; it will never be silently uploaded.</p>
</div>
<div id="mine" aria-live="polite"></div>
<div class="note">
  <h3>Where this goes next</h3>
  <p>The account version adds sync across devices, a shareable public list, and the ability to
  hand a saved list straight to the Planner as a set of must-visit stops. All three need a
  backend, a privacy notice and a data controller — see <a href="/how-it-works">how it works</a>.</p>
</div>
"""
    return "/my-europe/index.html", page(
        "My Europe", body, path="/my-europe", area=None,
        description="Your saved European places, journeys and stories — stored in your own browser, with no account and no server.",
        scripts=["/assets/js/my-europe.js"],
    )


def method_page(data):
    from .score import methodology_rows
    rows = "".join(
        f'<div class="row"><div><h3>{esc(name)}</h3><p class="rowsub">{esc(formula)}</p></div>'
        f'<p class="rowmeta">0–97</p></div>'
        for name, formula in methodology_rows()
    )
    body = f"""
{crumbs([("Europe", "/atlas"), ("Method", None)])}
<div class="pagehead">
  <p class="kicker">Europe Experience Score</p>
  <h1>The whole formula, on one page.</h1>
  <p class="lede">Six numbers appear on every city and country page. Here is exactly how each
  one is produced, because a score whose method is secret is a ranking, and rankings for sale
  are how travel sites lose their readers.</p>
</div>
<div class="rows">{rows}</div>
<div class="split" style="margin-top:var(--s7)">
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
    <h2 style="margin-top:var(--s7)">Why value is different</h2>
    <p>Five dimensions are structural — they come from tags. Value is the only one anchored to
    something outside our own judgement: the midpoint of the country's daily cost band, which is
    published on every country page and can be argued with directly.</p>
  </div>
  <aside class="rail">
    <h3>Recomputed, never stored</h3>
    <p>No score is written into the data files. Every number on the site is derived at build
    time from the tags, so a score and its explanation cannot drift apart.</p>
  </aside>
</div>
"""
    return "/method/index.html", page(
        "Method", body, path="/method", area=None,
        description="The complete, published formula behind the Europe Experience Score — and the four things it deliberately is not.",
    )


# ── the pages that explain the thing ──────────────────────────────────

def about_page(data):
    body = f"""
{crumbs([("Europe", "/atlas"), ("About", None)])}
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

    <h2 style="margin-top:var(--s7)">What we are not doing</h2>
    <ul class="stack">
      <li><strong>Not an OTA.</strong> We are not going to out-inventory Booking.com and would be
      foolish to try. Discovery first; commerce arrives afterwards, on top of an audience.</li>
      <li><strong>Not a scraped directory.</strong> Every place on this site was written for this
      site. That is slow, and it is the moat.</li>
      <li><strong>Not an AI that invents Europe.</strong> Anything a model says here will be
      retrieved from this dataset, cited to the page it came from, and refused when the dataset
      is silent. See <a href="/how-it-works">how it works</a>.</li>
    </ul>

    <h2 style="margin-top:var(--s7)">On the inspiration, and the line</h2>
    <p>The idea of a continental discovery platform is not ours and is not anybody's to own —
    tourism boards, atlases and travel magazines have organised continents this way for a century.
    What is owned is expression: another platform's words, photographs, code, layout and brand.
    None of that is here. Every line of copy, every generated illustration, the taxonomy, the
    scoring method and all of the code were written for Europedoor. Where we were inspired by an
    existing model — a continental atlas with a community fund attached — we took the idea and
    built our own version of it, which is the part the law leaves open.</p>
  </div>
  <aside class="rail">
    <h3>Status</h3>
    <p>Pre-launch. No entity, no payments, no accounts, no bookings, no partners. What exists is
    the Atlas, the Planner, the Journeys, the register and the editorial.</p>
    <h3>The name</h3>
    <p>Europedoor, at europedoor.com. Settled — the Atlas is the name of the discovery layer
    inside it, not an alternative name for the product.</p>
    <h3>Corrections</h3>
    <p>Everything here can be wrong. <a href="/sources">How to tell us →</a></p>
  </aside>
</div>
"""
    return "/about/index.html", page(
        "About", body, path="/about", area=None,
        description="What Europedoor is, what it refuses to be, and where the line sits between an idea anyone may use and expression nobody may copy.",
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
    gated = table([
        ("Taking a payment", "Requires an incorporated entity, a named payee on every card surface, and a PSP contract", "blocked"),
        ("Holding contributions", "Requires the above plus a written position on the treatment of contributions in each collecting country", "blocked"),
        ("Storing business or user data", "Requires a data controller, a lawful basis and a published privacy notice", "blocked"),
        ("Naming an operating company anywhere on the site", "There is not one yet, so no page names one", "blocked"),
    ])
    body = f"""
{crumbs([("Europe", "/atlas"), ("How it works", None)])}
<div class="pagehead">
  <p class="kicker">How it works</p>
  <h1>What is built, what is designed, and what is deliberately blocked.</h1>
  <p class="lede">Most pre-launch products blur these three. Keeping them apart in public is
  cheap insurance: nobody can accuse us of implying a booking engine or a fund that does not exist,
  and anybody evaluating this can see the actual state in one screen.</p>
</div>
{section("Built and live", built)}
{section("Designed, not built", designed, lede="Specified in docs/product-specification.md in the repository, with schemas and flows. Not shipped.")}
{section("Deliberately blocked", gated, lede="Each of these is one decision away from possible and is being held shut on purpose until the thing in the middle column exists.")}
<div class="note">
  <h3>The AI rule, in one paragraph</h3>
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
        description="Europedoor's honest status board: what is built, what is only designed, and what is deliberately blocked until the legal and payment work is done.",
    )


def sources_page(data):
    body = f"""
{crumbs([("Europe", "/atlas"), ("Sources & corrections", None)])}
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

    <h2 style="margin-top:var(--s7)">What is derived rather than claimed</h2>
    <ul class="stack">
      <li><strong>Distances</strong> are computed great-circle kilometres between the coordinates
      on each city page. They are honest as straight lines and misleading as travel times — the
      note under each hop says which mode the distance implies.</li>
      <li><strong>Scores</strong> are computed from tags by a published formula: <a href="/method">/method</a>.</li>
      <li><strong>Cost estimates</strong> multiply nights by the country's daily band and add a
      distance-based transport figure. They are planning arithmetic, not quotes.</li>
      <li><strong>Nearby stops</strong> are computed, never curated, so they cannot flatter a partner.</li>
    </ul>

    <h2 style="margin-top:var(--s7)">The verification plan</h2>
    <ol class="stack">
      <li>Every country's practical facts — currency, blocs, entry, costs — checked against the
      relevant official body and dated in the data file.</li>
      <li>Every city's seasonal and opening claims checked against the operator or municipality.</li>
      <li>A visible "checked on" date on every country page; anything unchecked says so.</li>
      <li>A standing correction log, published, with what changed and when.</li>
    </ol>
  </div>
  <aside class="rail">
    <h3>Tell us</h3>
    <p>Corrections are wanted, including blunt ones. A correction channel goes up with the entity;
    until then, the repository's issue tracker is the honest answer.</p>
    <h3>No photographs</h3>
    <p>Every illustration on this site is generated from the place's own name — a deterministic
    drawing, unique per place, owned outright. No stock library, no licence expiry, no
    accidental use of somebody's holiday photograph.</p>
  </aside>
</div>
"""
    return "/sources/index.html", page(
        "Sources & corrections", body, path="/sources", area=None,
        description="How Europedoor's facts are produced, what is computed rather than claimed, and the verification plan.",
    )


def not_found(data):
    body = """
<div class="pagehead">
  <p class="kicker">404</p>
  <h1>That door does not open.</h1>
  <p class="lede">The page is not here. The continent still is.</p>
  <div class="hero-actions">
    <a class="btn" href="/atlas">Open the Atlas</a>
    <a class="btn ghost" href="/plan">Plan a journey</a>
  </div>
</div>
"""
    return "/404.html", page(
        "Not found", body, path="/404", area=None,
        description="That page is not on Europedoor. The Atlas, the curated journeys and the Journey Planner all still are.",
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

def search_api(data):
    """One flat index of everything findable, built once and filtered in the
    browser. Small enough (a few hundred KB) that shipping it whole beats
    running a search service, and it works offline."""
    rows = []

    def add(kind, name, sub, url, text, weight=1.0):
        rows.append({"k": kind, "n": name, "s": sub, "u": url,
                     "t": " ".join(text).lower(), "w": weight})

    for m in data["macros"]:
        add("Region of Europe", m["name"], f"{len(m['countries'])} countries",
            urls.macro(m), [m["name"], m["blurb"]], 1.4)
    for c in data["countries"].values():
        add("Country", c["name"], c["macro_name"], urls.country(c),
            [c["name"], c.get("official", ""), c["capital"], c["tagline"],
             c["summary"], " ".join(c["interests"])], 2.0)
        for r in c["regions"]:
            add("Region", r["name"], c["name"], urls.region(c, r),
                [r["name"], r["summary"], " ".join(r["interests"])], 1.2)
            for t in r["cities"]:
                add("City", t["name"], f"{r['name']}, {c['name']}", urls.city(c, r, t),
                    [t["name"], t["summary"], " ".join(t["highlights"]),
                     " ".join(t["interests"]), c["name"], r["name"]], 1.6)
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
    return "/api/search.json", {"rows": rows}


def search_page(data):
    n = (len(data["countries"]) + sum(len(c["regions"]) for c in data["countries"].values())
         + len(data["cities"]) + len(data["journeys"]) + len(data["themes"])
         + len(data["stories"]) + len(data["fund"]))
    body = f"""
{crumbs([("Europe", "/atlas"), ("Search", None)])}
<div class="pagehead">
  <p class="kicker">Search</p>
  <h1>Find it.</h1>
  <p class="lede">Everything on Europedoor — {n} countries, regions, cities,
  journeys, themes, stories and projects — in one index that runs in your browser.
  Nothing you type is sent anywhere.</p>
</div>
<form class="form" id="searchform" role="search">
  <div class="field">
    <label for="q">Search Europe</label>
    <input type="text" id="q" name="q" autocomplete="off" autofocus
           placeholder="bergen, medieval, truffle, twelve days, sacred…">
  </div>
</form>
<div id="results" aria-live="polite"></div>
<noscript><p class="small">Search needs JavaScript. The
<a href="/atlas">Atlas</a> is fully browsable without it.</p></noscript>
"""
    return "/search/index.html", page(
        "Search", body, path="/search", area=None,
        description="Search every country, region, city, journey, theme, story and project on Europedoor — in your browser, with nothing sent anywhere.",
        scripts=["/assets/js/search.js"],
    )
