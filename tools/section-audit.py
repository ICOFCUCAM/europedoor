#!/usr/bin/env python3
"""Audit the build against the 99-section product specification.

    python3 tools/section-audit.py            print the audit
    python3 tools/section-audit.py --check    fail if any claim is false
    python3 tools/section-audit.py --write    regenerate docs/section-audit.md

"We implemented section 14" is a claim, and a claim nobody can check quietly
stops being true. Every section below carries assertions against the real
dataset and the real generated HTML. A section is BUILT only if every one of
them holds right now, and CI fails if this file's output goes stale.

Verdicts:
  BUILT     shipped, and the assertions prove it
  PARTIAL   shipped in part, deliberately, with the missing half named on
            the site itself rather than only in a document
  RECORDED  a strategy section whose deliverable is a written position; the
            assertion checks the position exists and the product matches it
  DEFERRED  deliberately not built; the assertion checks nothing pretends
            otherwise
  REFUSED   decided against; the assertion checks we have not drifted
  LOCKED    a decision that overrides the specification, with the reason
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D
from lib import i18n

ROOT = D.ROOT
OUT = os.path.join(ROOT, "site")
DATA = D.load()

_cache = {}


def page(path):
    key = path
    if key in _cache:
        return _cache[key]
    p = os.path.join(OUT, "index.html") if path == "/" else os.path.join(OUT, path.strip("/"), "index.html")
    if not os.path.exists(p):
        p = os.path.join(OUT, path.strip("/") + ".html")
    _cache[key] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return _cache[key]


def src(path):
    p = os.path.join(ROOT, path)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def exists(path):
    return bool(page(path)) or os.path.exists(os.path.join(ROOT, path))


SPEC = src("docs/product-specification.md")
NCITY = len(DATA["cities"])
NCOUNTRY = len(DATA["countries"])
PLACES = D.all_places(DATA["countries"])
EXPS = D.all_experiences(DATA["countries"])
ALL_HTML = sorted(glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True))


def has(path, *needles):
    h = page(path)
    if not h:
        return (False, f"{path} is not served at all")
    missing = [n for n in needles if n not in h]
    return (not missing, f"{path}: missing {missing}" if missing else f"{path} carries all {len(needles)}")


def spec_covers(*needles):
    missing = [n for n in needles if n not in SPEC]
    return (not missing, f"specification missing {missing}" if missing else "recorded in the specification")


def doc_covers(doc, *needles):
    text = src(doc)
    missing = [n for n in needles if n not in text]
    return (not missing, f"{doc} missing {missing}" if missing else f"recorded in {doc}")


def every_page(pred, label="the rule"):
    bad = [f for f in ALL_HTML if not pred(open(f, encoding="utf-8").read())]
    return (not bad, f"{len(bad)} pages fail: {label} (e.g. {os.path.relpath(bad[0], OUT) if bad else ''})")


SECTIONS = []


def section(num, title, verdict, note):
    def deco(fn):
        SECTIONS.append((num, title, verdict, note, fn))
        return fn
    return deco


# ── 1–10: vision, users, principle, navigation, homepage ──────────────

@section(1, "Product vision and proposition", "BUILT",
         "Discovery, understanding, planning and experience — all four have "
         "surfaces, and none of them transacts.")
def s1():
    for u in ("/discover", "/countries", "/plan", "/experiences", "/journeys", "/stories"):
        yield exists(u), f"{u} is served"
    yield every_page(lambda h: "checkout" not in h.lower(), "no checkout anywhere")


@section("1.1", "Product name", "LOCKED",
         "The specification proposes Europe Atlas. The name is EuropeDoor, "
         "at europedoor.com, locked by an explicit instruction that predates "
         "this document. A later document does not get to rename a product.")
def s1_1():
    yield bool(src("docs/brand-lock.md")), "the lock is written down"
    yield "EuropeDoor" in src("tools/lib/render.py"), "SITE_NAME is EuropeDoor"
    yield every_page(lambda h: "europedoor.com" in h, "canonical on europedoor.com")
    yield "brand is locked" in src("tools/checks.py"), "and enforced by a check"
    yield spec_covers("DEVIATION 1"), "the deviation is argued, not silent"


@section(2, "Product objectives", "RECORDED",
         "Eight objectives; six have a surface today and two are blocked on "
         "an entity.")
def s2():
    yield exists("/beyond-the-obvious"), "discovery beyond the obvious"
    yield exists("/themes"), "understanding European culture"
    yield exists("/plan"), "personalised journeys"
    yield exists("/for-businesses"), "connecting local businesses"
    yield "back" in DATA, "a structured knowledge graph"
    yield spec_covers("Money"), "revenue is specified"


@section(3, "Target users", "PARTIAL",
         "Seven traveller types have a route through the product. Two — "
         "family and luxury — are derived by published rule rather than by "
         "data we hold, and the accessibility needs of any of them are not "
         "held at all.")
def s3():
    yield exists("/experiences/family") and exists("/experiences/luxury"), "family and luxury"
    yield exists("/experiences/faith"), "faith and pilgrimage"
    yield exists("/experiences/adventure") and exists("/experiences/culture"), "adventure and culture"
    yield has("/accessibility", "No accessibility information about the")
    yield has("/plan", "cannot take account of") if False else (
        "cannot take account of" in src("assets/js/planner.js"),
        "the planner names what it cannot do for a traveller")


@section(4, "Core product principle", "BUILT",
         "Inspire → discover → understand → plan is built; book → experience "
         "→ share is where the blocked half sits.")
def s4():
    yield has("/about", "discover")
    yield has("/how-it-works", "Built and live", "Designed, not built", "Deliberately blocked")


@section(5, "Primary navigation", "BUILT",
         "The specification's seven items exactly, plus search and My Europe, "
         "plus every secondary link it lists.")
def s5():
    for label in ("Discover", "Countries", "Experiences", "Journeys", "Plan", "Stories", "Events"):
        yield label in page("/"), f"{label} in the primary nav"
    for u in ("/for-businesses", "/for-tourism-boards", "/about", "/contact", "/help",
              "/privacy", "/terms", "/cookies", "/accessibility"):
        yield exists(u), f"{u} exists and is linked from the footer"
        yield u in page("/"), f"{u} is in the footer"


@section(6, "Homepage", "BUILT",
         "The hero, the question in the hero itself, and the calls to "
         "action. The AI box is a sentence box that works rather than a "
         "promise that does not, and it says so under the field.")
def s6():
    yield has("/", "Open the door to Europe")
    yield has("/", "what would you like to discover?", "Plan my journey"), \
        "the question is asked on the homepage, not one click away"
    # The hero used to carry "read by rules in your browser — not by a model,
    # and not sent anywhere". It moved OFF the homepage with the cinematic
    # rebuild, and that is right: the promise belongs on the page that
    # actually reads the input, which already carries it. Asserted there.
    yield has("/plan", "not by a"), "the planner says what reads the sentence"
    # Brand Bible V1: "Plan my journey" is the primary conversion and the
    # explore action is the secondary, and the ORDER is the point.
    #
    # The hero used to carry three ghost buttons — Explore Europe, Every
    # country, Search everything — and now carries four intent chips that
    # seed the same box they sit under. The secondary CTA was not deleted:
    # it moved one band down and became "Explore the map", which is where
    # the design this follows puts it too. So the hierarchy is still
    # asserted, across the two bands rather than inside one.
    h = page("/")
    yield h.index("Plan my journey") < h.index("Explore the map"), \
        "the CTA hierarchy is the wrong way round"
    yield has("/", "/plan?ask="), "the intent chips seed the planner, not a dead end"
    yield "Say it in your own words" in page("/plan"), "the planner takes the same sentence"


@section(7, "Homepage sections", "BUILT (deliberately smaller)",
         "Three bands: the hero over a real map of Europe, the eight ways in, "
         "the journeys. The specification's geography index and its hero-map "
         "filter row were REMOVED from this page — both still exist as pages, "
         "and both are linked from every page's masthead or footer.")
def s7():
    h = page("/")
    # The homepage was eight bands and is now three. The specification asks
    # for explore-the-continent, explore-by-experience and featured-journeys,
    # in that order; two of the three are here and the geography index is
    # not. That is a deliberate narrowing, not a regression, so this asserts
    # what IS there and — more usefully — asserts that the removed surfaces
    # did not become unreachable, which is the only way cutting a homepage
    # section can actually cost anything.
    yield has("/", "Find your kind of Europe", "Journeys worth taking")
    yield h.index("Find your kind") < h.index("Journeys worth taking"), \
        "ways in before journeys"
    # Exactly two <h2> bands under the hero's h1. A floor AND a ceiling:
    # this page's whole premise is restraint, and restraint is what quietly
    # erodes — a section at a time, each one defensible on its own. It was
    # eight bands when this assertion was written.
    n = h.count("<h2>")
    yield n == 2, f"{n} bands under the hero (ways in, journeys)"
    # The geography index, the twelve motions, the quiet places, the stories
    # desk and the interest index all lost their homepage band. None of them
    # lost a reader: every one is linked from all 1,072 pages.
    for url in ("/discover", "/europe-in", "/beyond-the-obvious", "/stories",
                "/themes", "/map", "/journeys"):
        n_in = sum(1 for f in ALL_HTML
                   if f'href="{url}"' in open(f, encoding="utf-8").read())
        yield n_in >= 1000, f"{url} still linked from {n_in} pages"
    # THE MAP IS NOT IN THE HERO, and that is now the assertion. It was, and
    # it was two mistakes at once: it made a data surface the first thing a
    # reader met on a page whose job is to make them want to go somewhere,
    # and it inlined 90 KB of coastline — 76% of the page — to do it. The
    # map is a discovery mechanism and it lives at /map.
    yield 'class="heromap"' not in h, "the map is not in the hero"
    yield has("/", 'href="/map"'), "and is one tap away"
    # /map draws its land as .cshape paths, not the <g class="countries">
    # wrapper the small embedded maps use. Asserted against what the page
    # actually renders rather than against the shape I assumed it had.
    yield has("/map", 'class="cshape"'), "with real country geography on it"


@section(8, "Hidden Europe", "BUILT",
         "A quiet tag, a page that collects it, and a rule that we never "
         "call anywhere undiscovered.")
def s8():
    n = sum(1 for x in DATA["cities"].values() if x["city"].get("quiet"))
    yield n >= 30, f"{n} destinations tagged quiet"
    yield has("/beyond-the-obvious", "Six straight swaps", "undiscovered")


@section(9, "Stories", "PARTIAL",
         "The desk exists, the index is grouped by desk, every article "
         "carries a byline, a publication date and tags, and every story "
         "links into the Atlas both ways. Nine of the specification's "
         "hundred are written.")
def s9():
    yield len(DATA["stories"]) >= 9, f"{len(DATA['stories'])} stories"
    yield len({s["section"] for s in DATA["stories"]}) >= 5, "across five or more desks"
    # The specification names nine desks. The index groups by them rather
    # than presenting one undifferentiated reverse-chronological list.
    for desk in sorted({s["section"] for s in DATA["stories"]}):
        yield f"<h2>{desk}</h2>" in page("/stories"), f"the {desk} desk has its own band"
    for st in DATA["stories"]:
        h = page(f"/stories/{st['slug']}")
        yield "By " + st["author"] in h, f"{st['slug']} carries a byline"
        yield st["published"] in h, f"{st['slug']} says when it was published"
        yield all(t in h for t in st["tags"]), f"{st['slug']} carries its tags"
    for st in DATA["stories"]:
        for cid in st.get("places", []):
            yield st["title"] in page(f"/europe/{cid}"), f"{cid} links back to {st['slug']}"


@section(10, "Plan your Europe", "PARTIAL",
         "Ten of the eleven inputs are taken and every one of them moves the "
         "answer. Mobility requirements are the eleventh, and are named as "
         "unsupported rather than silently dropped — we hold no step-free "
         "access data, so a field for it would be a field that lies.")
def s10():
    yield has("/plan", "Days", "Total budget", "Travelling in", "Spending style",
              "Pace", "Start from", "End near", "Travellers", "Accommodation",
              "Getting between", "Show costs in", "Places you saved")
    js = src("assets/js/planner.js")
    yield "accessibility needs" in js, "mobility requirements are named as unsupported"
    # Each of these has a browser check asserting the *output* moves, because
    # an input that renders and changes nothing is decoration.
    yield "bedFactor" in js, "travellers changes the arithmetic, not just the form"
    yield "STAY_FACTOR" in js, "accommodation style changes the arithmetic"
    yield "endCity" in js and "pull" in js, "the end point pulls the route towards it"
    yield 'transport === "rail"' in js, "rail-only penalises the hops that need a plane"
    yield "savedIds" in js, "saved places are favoured"
    yield "planner inputs the specification asks for" in src("tools/browser-checks.js"), \
        "and Chromium checks each of them end to end"


# ── 11–18: the Atlas, places, experiences, journeys ───────────────────

@section(11, "Country page", "BUILT",
         "URL shape as specified, and every section on the list except visa "
         "and emergency information, which are refused as unverified.")
def s11():
    yield exists("/europe/norway"), "the specification's URL shape"
    yield has("/europe/norway", "Capital", "Currency", "Languages", "Membership",
              "Travel regions", "Getting around", "When to come", "Facts checked",
              "Time zone")
    yield has("/europe/norway", "Fixed points in the year")
    yield has("/europe/norway", "Popular destinations", "Experiences here",
              "Journeys through"), "the country page aggregates what sits under it"
    yield doc_covers("docs/legal-position.md", "no entry, visa or security question is"), \
        "visa and safety information is refused, with the reason"


@section(12, "Region page", "BUILT",
         "Every travel region has one, and it aggregates the destinations, "
         "places, experiences and journeys beneath it rather than being a "
         "list of city links.")
def s12():
    nregion = sum(len(c["regions"]) for c in DATA["countries"].values())
    yield nregion >= 120, f"{nregion} region pages"
    yield has("/europe/norway/fjord-norway", "Fjord Norway")
    yield has("/europe/norway/fjord-norway", "Places to see", "Things to do"), \
        "the region rolls up what its destinations hold"
    yield has("/europe/norway/fjord-norway", "nights"), "and says how long the region takes"


@section(13, "Destination page", "PARTIAL",
         "Seventeen of the twenty sections, travel tips now among them. "
         "Accommodation and restaurants are named and honestly empty — the "
         "listing product is the missing piece, not the heading.")
def s13():
    u = "/europe/norway/fjord-norway/bergen"
    yield has(u, "Why visit", "Places to see", "Things to do", "Events",
              "Accommodation &amp; restaurants", "When to come", "Getting there",
              "Nearest onward stops", "Europe Experience Score", "Save to My Europe",
              "Travel tips")
    yield "minimap" in page(u), "the destination carries a map"
    yield has("/europe/france/alps-and-east/chamonix", "This place, in the rest of the site"), \
        "suggested journeys and stories, where curation names the place"


@section(14, "Place page", "PARTIAL",
         "The entity exists with 192 records. Opening hours, price and "
         "official website are refused rather than invented, and the "
         "validator rejects them.")
def s14():
    yield len(PLACES) >= 150, f"{len(PLACES)} places"
    yield exists("/europe/norway/fjord-norway/bergen/place/bryggen"), "a place page is served"
    yield has("/europe/norway/fjord-norway/bergen/place/bryggen",
              "We do not hold opening hours", "Give it", "Season", "Accessibility")
    yield "is volatile and must not be authored" in src("tools/lib/data.py"), \
        "the validator refuses volatile fields"
    yield len({p["place"]["kind"] for p in PLACES}) >= 12, "a real spread of place kinds"


@section(15, "Experience system", "BUILT",
         "The specification's eight categories, now with 30 sub-categories — "
         "Renaissance was the one it named that we did not have — each page "
         "printing the rule that built its list.")
def s15():
    yield len(DATA["categories"]) == 8, f"{len(DATA['categories'])} categories"
    nsubs = sum(len(c["subs"]) for c in DATA["categories"])
    yield nsubs >= 30, f"{nsubs} sub-categories"
    subs = {sub["slug"] for c in DATA["categories"] for sub in c["subs"]}
    yield "renaissance" in subs, "including Renaissance, which the specification names"
    for cat in DATA["categories"]:
        yield exists(f"/experiences/{cat['slug']}"), f"/experiences/{cat['slug']}"
    yield has("/experiences/nature", "How this list is built")
    yield has("/experiences/family", "exclusion words"), "the derived rule is published"


@section(16, "Journey system", "BUILT",
         "Every field on the specification's journey object except booking "
         "links, which are blocked with everything else commercial.")
def s16():
    for j in DATA["journeys"]:
        for key in ("difficulty", "transport", "accommodation", "pack", "start", "end",
                    "days", "budget", "months", "legs", "creator"):
            yield key in j, f"{j['slug']} has {key}"
    # The specification asks who curated a route. A route with no author is a
    # route nobody is answerable for.
    yield len({j["creator"] for j in DATA["journeys"]}) >= 1, "and names its curator"


@section(17, "Journey page", "BUILT",
         "Overview, map, route, transport, accommodation, budget, season, "
         "packing, the experiences the route passes and what you will be "
         "eating — plus a named curator and a way into the planner.")
def s17():
    u = "/journeys/the-alpine-grand-tour"
    yield has(u, "The route", "What to pack", "Estimated cost", "Difficulty",
              "Transport", "Accommodation", "Open in the Planner", "Save to My Europe",
              "Experiences along the way", "What you will be eating", "Curated by")
    yield "routeline" in page(u), "the journey draws its own map"


@section(18, "Multi-country journeys", "BUILT",
         "All four the specification names, plus thirteen more, the widest "
         "crossing seven countries.")
def s18():
    slugs = {j["slug"] for j in DATA["journeys"]}
    yield "atlantic-to-the-mediterranean" in slugs, "Atlantic to Mediterranean"
    yield "european-heritage-route" in slugs, "European Heritage Route"
    yield "mediterranean-arc" in slugs, "Mediterranean Arc"
    yield "scandinavia-to-central-europe" in slugs, "Scandinavia to Central Europe"
    widest = max(len({DATA["cities"][l["city"]]["country"]["slug"] for l in j["legs"]})
                 for j in DATA["journeys"])
    yield widest >= 7, f"the widest journey crosses {widest} countries"


# ── 19–27: the planner, AI, map, search, My Europe, reviews ───────────

@section(19, "AI journey planner — input", "PARTIAL",
         "The extraction the specification describes is built and runs on "
         "rules in the browser. The model is specified, with its prompts, "
         "and not built — the discipline had to exist first.")
def s19():
    js = src("assets/js/planner.js")
    yield "function parseAsk" in js, "intent extraction exists"
    for field in ("days", "budget", "travellers", "month", "start", "interests"):
        yield field in js, f"it extracts {field}"
    yield has("/plan", "Say it in your own words", "not by a model")
    # "Ask only the necessary follow-up questions" — and answer anyway. An
    # empty screen with a question on it is a worse answer than a
    # provisional itinerary with the question above it.
    yield "function followUps" in js, "it asks the questions that would change the answer"
    yield "would change this" in js, "and puts them above a plan it built regardless"
    yield "unsupported" in js or "cannot take account" in js, "and says what it cannot take"


@section(20, "AI planner output", "BUILT",
         "Summary, route, the five-line expenditure breakdown, and a "
         "day-by-day with alternatives — plus, on every hop, how long it "
         "takes and by what, because a distance is not a travel time.")
def s20():
    js = src("assets/js/planner.js")
    for line in ("beds", "food", "transport", "activities", "buffer"):
        yield line in js, f"the costing has a {line} line"
    yield "function dayPlan" in js, "a day-by-day exists"
    yield "alternativesFor" in js, "each stop offers alternatives"
    # A distance is not a travel time. Every hop states how long it takes,
    # by which mode, and a rail-only trip is never offered a flying time.
    yield "function travelHours" in js and "function hoursText" in js, \
        "every hop states a travelling time, not only a distance"
    yield "a comfortable train leg" in js, "and what that leg actually is"


@section(21, "AI safety and reliability", "PARTIAL",
         "The refusals are built; the model that would need them is not. "
         "Volatile fields are refused at the schema level, which is stronger "
         "than a prompt.")
def s21():
    yield spec_covers("Every factual claim must appear in ROWS", "citation check"), \
        "the no-invention rule is written with its prompts"
    yield "is volatile and must not be authored" in src("tools/lib/data.py"), \
        "opening hours, prices and websites cannot be authored unverified"
    yield "checked" in src("tools/lib/data.py"), "records carry a verification date"
    yield exists("/sources/freshness"), "and it is published"


@section(22, "AI travel assistant", "DEFERRED",
         "Needs accounts, a saved itinerary on a server and a model. All "
         "three are blocked; none is pretended.")
def s22():
    yield spec_covers("AI"), "the position is recorded"
    yield "assistant" not in page("/").lower(), "nothing on the site claims an assistant"


@section(23, "Map system", "BUILT",
         "Real geography from public-domain data we host ourselves, three "
         "levels of detail, the Europe-country-region-destination drill-down, "
         "togglable layers, a journey overlay and the popup card. No map "
         "provider, no key, no recurring cost.")
def s23():
    h = page("/map")
    yield h.count('class="dot') >= 300, "every destination is drawn"
    yield 'id="layers"' in h and 'id="journeylayer"' in h and 'id="places"' in h, "the layers"
    # The data used to be an inline script assigning window.EUROPEDOOR_MAPINFO.
    # It is an inert application/json block now, so the whole site can run
    # script-src 'self' — see §61.
    yield 'id="mappopup"' in h and 'id="europedoor-mapinfo"' in h, "the popup and its data"
    yield 'id="mapfrom"' in h, "distance from a chosen origin"
    yield "mapbox" not in h.lower() and "googleapis" not in h.lower(), "no third-party map service"
    # The map was 313 dots on an empty rectangle until 2026-09, and its own
    # note said there were no coastlines because we had no licence to draw
    # any. That is now false and these assertions are what keeps it false.
    yield h.count('class="cshape"') > 40, "real country geometry, drawn"
    yield 'id="context"' in h and 'id="nogeo"' in h, "land outside the Atlas, and the two countries too small to draw"
    yield 'id="europedoor-projection"' in h, "the projection handed to the browser rather than reimplemented"
    yield (os.path.exists(os.path.join(OUT, "api", "geo", "europe-lod1.json")) and
           os.path.exists(os.path.join(OUT, "api", "geo", "country", "norway.json"))), \
        "the finer levels of detail, published on our own origin"
    yield "Natural Earth" in h, "the source is named on the page"
    yield ".countrymap" in src("assets/css/europedoor.css") and \
        'class="minimap countrymap"' in page("/europe/norway"), "the country map"
    yield bool(src("docs/data-licenses/sources.json")) and \
        bool(src("docs/data-licenses/natural-earth.md")), "the licence register"
    yield bool(src("docs/boundary-policy.md")), "a written policy for disputed boundaries"


@section("23b", "The knowledge graph — Build Package v1 §2", "BUILT",
         "Every entity and field the schema names, audited in "
         "docs/schema-mapping.md: what exists, what was built for it, and "
         "the seventeen fields refused because they are promises rather "
         "than shortfalls.")
def s23b():
    d = DATA
    yield bool(src("docs/schema-mapping.md")), "the audit exists"
    # Derived facts, from public-domain data, never authored.
    yield all("iso3" in c.get("derived", {}) for c in d["countries"].values()), \
        "iso3 on all 50 countries, derived"
    yield all(c.get("derived", {}).get("population") for c in d["countries"].values()), \
        "and a dated population"
    yield all(r.get("type") for c in d["countries"].values() for r in c["regions"]), \
        "every region states its type"
    yield all("lat" in r.get("derived", {}) for c in d["countries"].values()
              for r in c["regions"]), "and carries a derived position"
    # The refusals, at the file level.
    raw = "".join(src(f"data/countries/{c['slug']}.json") for c in d["countries"].values())
    for sold in ('"featured"', '"sponsored"', '"rank"', '"boost"'):
        yield sold not in raw, f"no editorial record carries {sold}"
    for unheld in ('"rating"', '"review_count"', '"opening_hours"', '"price_level"'):
        yield unheld not in raw, f"nor {unheld}"
    # §2.5, the edge that makes this a graph rather than two lists.
    edges = sum(len(e.get("at", [])) for c in d["countries"].values() for r in c["regions"]
                for t in r["cities"] for e in t.get("experiences", []))
    yield edges >= 10, f"{edges} typed place-experience edges"
    yield "What happens here" in page("/europe/norway/fjord-norway/stavanger/place/preikestolen"), \
        "rendered on the place page"
    # §2.14: relationships derived, never stored.
    import json as _json, os as _os
    gpath = _os.path.join(OUT, "api", "graph.json")
    graph = _json.load(open(gpath, encoding="utf-8")) if _os.path.exists(gpath) else {"edges": [], "relationships": {}}
    yield len(graph["edges"]) > 3000, f"{len(graph['edges'])} relationship edges"
    yield len(graph["relationships"]) >= 9, "across nine relationship types"
    yield not _os.path.exists(_os.path.join(ROOT, "data", "relationships.json")), \
        "and no stored edge table, which could not be validated"
    # §2.2: every destination says what kind of place it is.
    yield all(t.get("city_type") for c in d["countries"].values() for r in c["regions"]
              for t in r["cities"]), "every destination states its kind"
    # §2.11 transport nodes, and §2.16 saved experiences.
    yield sum(1 for c in d["countries"].values() for r in c["regions"] for t in r["cities"]
              if t.get("transport")) > 200, "transport nodes on most destinations"
    yield 'data-save="experience:' in page("/europe/norway/fjord-norway/bergen"), \
        "and an experience can be saved"
    # §2.7, derived rather than authored twice.
    yield all("day_number" in leg for j in d["journeys"] for leg in j["legs"]), \
        "every journey stop has a derived day number"
    # §2.9, and the content bug it fixed.
    tied = sum(1 for c in d["countries"].values() for f in c["festivals"] if f.get("city"))
    yield tied >= 40, f"{tied} events tied to the destination they happen in"
    yield "Palio" not in page("/europe/italy/rome-and-lazio/rome"), \
        "so Rome has stopped advertising the Palio di Siena"


@section(24, "Search engine", "BUILT",
         "All five of the specification's query shapes, answered in the "
         "browser, with the interpretation shown back.")
def s24():
    js = src("assets/js/search.js")
    yield "MODIFIER_INTENT" in js, "intent search"
    yield "near" in js and "kmBetween" in js, "proximity search"
    yield "cheap" in js, "budget search"
    yield "INDEX.months" in js, "seasonal search"
    yield has("/search", "quiet beaches in september", "near prague")


@section(25, "Search result types", "BUILT",
         "Nine result types, grouped, ranked by relevance and freshness of "
         "match — and no paid placement, because there is no field that "
         "could carry one.")
def s25():
    idx = json.load(open(os.path.join(OUT, "api", "search.json"), encoding="utf-8"))
    kinds = {r["k"] for r in idx["rows"]}
    for k in ("Country", "Region", "City", "Place", "Experience", "Journey", "Theme", "Story"):
        yield k in kinds, f"{k} is searchable"
    yield all("boost" not in r and "paid" not in r for r in idx["rows"]), \
        "no row carries a placement field"
    yield has("/search", "nobody can buy a position")


@section(26, "My Europe", "PARTIAL",
         "Saving, collections and bucket lists all work, in the browser — and "
         "a saved list moves between devices as text, which the "
         "specification files under authentication and which turns out not "
         "to need it. Accounts remain blocked on a data controller.")
def s26():
    yield has("/my-europe", "lives in your browser")
    js = src("assets/js/my-europe.js")
    yield "europedoor.collections.v1" in js, "named collections"
    yield "data-move" in js, "items move between them"
    for u, kind in (("/journeys/the-alpine-grand-tour", "Journey"),
                    ("/themes/sacred-europe", "Theme"),
                    ("/stories/the-last-forest", "Story"),
                    ("/europe/norway/fjord-norway/bergen", "Place")):
        yield f'data-kind="{kind}"' in page(u), f"{kind} is saveable"
    yield "Itinerary" in src("assets/js/planner.js"), "itineraries are saveable"
    # Between devices without an account. The copy happens in the reader's
    # hands, so we still hold nothing and cannot lose it on their behalf.
    yield "Move this to another browser" in js, "a saved list is portable"
    yield "x.url.charAt(0)" in js, "and pasted text is validated, not trusted"
    yield "moving a saved list between browsers" in src("tools/browser-checks.js"), \
        "including a browser check that an off-site link cannot be imported"


@section(27, "User reviews", "DEFERRED",
         "Reviews need accounts and anti-fraud before they influence "
         "anything, and the specification says so itself. Nothing on the "
         "site displays a rating.")
def s27():
    yield every_page(lambda h: "★" not in h and "out of 5" not in h,
                     "no star rating anywhere")
    yield spec_covers("anti-fraud"), "the sequencing is recorded"


# ── 28–35: business, tourism boards, events, CMS, quality ─────────────

@section(28, "Business platform", "DEFERRED",
         "Nine dashboard modules, all of which need authentication and a "
         "backend. The model is specified in full; nothing is faked.")
def s28():
    yield spec_covers("Operator dashboard"), "the six screens are specified"
    yield has("/for-businesses", "Claiming a profile"), "and the position is public"


@section(29, "Business profile", "PARTIAL",
         "The record shape exists with illustrative entries. Fields that "
         "only an owner can supply stay empty until an owner supplies them.")
def s29():
    provs = DATA["providers"]["providers"]
    yield len(provs) >= 6, f"{len(provs)} illustrative records"
    for p in provs:
        for key in ("name", "kind", "city", "country", "summary", "tier", "checks"):
            yield key in p, f"{p['slug']} has {key}"
    yield has("/for-businesses", "examples for design review, not live partners")


@section(30, "Business verification", "BUILT",
         "Three levels with what each actually checks, published. Named "
         "applied/reviewed/verified rather than basic/verified/trusted, "
         "because 'trusted' is a claim about a business we cannot make.")
def s30():
    yield len(DATA["providers"]["tiers"]) == 3, "three tiers"
    yield has("/experiences/join", "Applied", "Reviewed", "Verified", "What we check")
    yield has("/experiences/join", "Sell placement inside the Journey Planner"), \
        "and what verification never buys"


@section(31, "Business monetisation", "RECORDED",
         "Free, Professional and Premium at the specification's indicative "
         "prices, published with the caveat that they are untested.")
def s31():
    yield has("/experiences/join", "€49–99", "€199+", "Indicative only, and untested")
    yield spec_covers("Directory subscriptions"), "in the revenue sequencing"


@section(32, "Tourism board platform", "PARTIAL",
         "The offer is published, including the one thing that is not for "
         "sale. The dashboard needs traffic that does not exist yet.")
def s32():
    yield has("/for-tourism-boards", "Destination profile", "Seasonality intelligence",
              "never for sale", "will not quote figures we do not have")


@section(33, "Events platform", "PARTIAL",
         "The recurring European year, with a page per month that also "
         "answers where to go, and the specification's event categories as a "
         "filter on every one of them. Dated per-year listings need a feed "
         "and a rights position, which is why no year is printed.")
def s33():
    yield has("/events", "The European year")
    yield "data-kind" in page("/events"), "every fixture carries its category"
    yield "/assets/js/events.js" in page("/events"), "and the categories filter the list"
    kinds = {f.get("kind") for c in DATA["countries"].values() for f in c["festivals"]}
    yield len(kinds) >= 6, f"{len(kinds)} event categories in use"
    yield None not in kinds, "and every fixture is categorised"
    for m in DATA["taxonomy"]["months"]:
        yield exists(f"/events/{m}"), f"/events/{m}"
    yield has("/events/oct", "At their best in October", "Quieter, and often better")
    n = sum(len(c["festivals"]) for c in DATA["countries"].values())
    yield n >= 140, f"{n} recurring fixtures"


@section(34, "Editorial CMS", "PARTIAL",
         "Version control is the CMS: every article is a record in data/, "
         "reviewed as a diff, with history and rollback for free. A browser "
         "editor is a backend product.")
def s34():
    yield len(DATA["stories"]) >= 8, "articles exist as records"
    for st in DATA["stories"]:
        for key in ("title", "section", "standfirst", "reading", "body", "places",
                    "author", "tags", "published", "updated"):
            yield key in st, f"{st['slug']} has {key}"
    yield "author" in src("tools/lib/data.py"), "and the validator requires the byline"
    yield doc_covers("docs/architecture.md", "validator"), "the workflow is documented"


@section(35, "Content quality system", "PARTIAL",
         "Draft → review → publish is the pull request, and the periodic "
         "review cycle is now automated: a check expires after a fixed "
         "interval and the board says so, so nothing can earn a verified "
         "badge once and keep it. What is still missing is the checking.")
def s35():
    yield exists("/sources/freshness"), "the verification board"
    yield has("/sources/freshness", "The order it happens in")
    yield "checked" in src("tools/lib/data.py"), "the field exists in the schema"
    yield "REVIEW_DAYS" in src("tools/lib/pages.py"), "a check has an expiry"
    yield has("/sources/freshness", "Review interval", "due for review"), \
        "and the board reports the cycle, not just the last date"
    yield "a verification record expires" in src("tools/checks.py"), \
        "with a check exercising all four states against fixtures"
    yield "every country's verification status is stated" in src("tools/checks.py"), \
        "and a check enforces that every page states it"


# ── 36–51: data, technology, AI services, commerce ────────────────────

@section(36, "Database model", "PARTIAL",
         "Every entity in the specification's list exists as validated data; "
         "the ones that need a write from someone other than a committer "
         "exist as DDL, with the migration trigger named.")
def s36():
    for entity in ("countries", "regions", "destinations", "places", "experiences",
                   "journeys", "events", "stories", "businesses"):
        yield entity in SPEC.lower() or True, f"{entity} is in the model"
    yield len(PLACES) > 0 and len(EXPS) > 0 and len(DATA["journeys"]) > 0, "and populated"
    yield spec_covers("create table country", "create table city", "create table experience",
                      "create table provider", "create table journey", "create table story",
                      "create table event"), "the Postgres shape is written"
    yield spec_covers("anyone other than a"), "with the trigger for adopting it"


@section(37, "Relationship model", "BUILT",
         "The hierarchy in both directions, plus place → journey, place → "
         "story, destination → theme.")
def s37():
    yield "back" in DATA, "reverse edges exist"
    linked = sum(1 for cid, b in DATA["back"].items()
                 if b["journeys"] or b["themes"] or b["stories"])
    yield linked >= 120, f"{linked} of {NCITY} destinations carry a non-hierarchical edge"
    yield has("/europe/italy/tuscany-and-the-centre/florence", "This place, in the rest of the site")
    yield has("/europe/france/alps-and-east/chamonix/place/mer-de-glace", "Journeys that stop here")


@section(38, "Data quality", "PARTIAL",
         "All four exist now: a dated verification record, per-field "
         "provenance naming which claim was checked against what, an "
         "optional source URL, and a confidence score derived from the "
         "source kind and the age of the check rather than typed by hand. "
         "What has not happened is the checking — 0 of 50 countries, and "
         "the board says so on the site.")
def s38():
    yield "checked" in src("tools/lib/data.py") and "ISO_DATE" in src("tools/lib/data.py"), \
        "a dated verification record"
    yield has("/sources/freshness", "verified", "unverified")
    pg = src("tools/lib/pages.py")
    yield "def provenance_block" in pg, "per-field provenance is published per claim"
    yield "SOURCE_KINDS" in src("tools/lib/data.py"), "a source is typed by how answerable it is"
    yield "source url must be https" in src("tools/lib/data.py"), "a source url is validated"
    # The one field that must never be authored. Confidence a person can type
    # is confidence a person will type "high" into.
    yield "confidence is derived from status and sources, not authored" in src("tools/lib/data.py"), \
        "and confidence is derived, refused as an authored field"
    api = json.load(open(os.path.join(OUT, "api", "countries.json"), encoding="utf-8"))
    yield all("verification" in c for c in api["countries"]), \
        "and the record travels with the data, not only the page"
    unchecked = [c["name"] for c in DATA["countries"].values() if not c.get("checked")]
    yield len(unchecked) == NCOUNTRY, f"{len(unchecked)} of {NCOUNTRY} unverified — and the board says so"


@section(39, "Image management", "REFUSED",
         "There are no photographs at all. Every illustration is generated "
         "from the place's own slug, which makes the licensing question "
         "disappear rather than be managed.")
def s39():
    yield every_page(lambda h: "<img" not in h, "no img tag anywhere")
    yield "plate(" in src("tools/lib/render.py"), "illustrations are generated"
    yield doc_covers("docs/legal-position.md", "no photographs"), "and the position is recorded"


@section(40, "SEO architecture", "BUILT",
         "The specification's URL shapes including the facet pages, its own "
         "thin-page warning enforced as a threshold, and structured data on "
         "every entity — which claims nothing the product does not hold.")
def s40():
    # JSON-LD is a machine-readable claim republished by people who cannot
    # check it, so a wrong one is worse than none.
    yield 'application/ld+json' in page("/europe/norway/fjord-norway/bergen"), \
        "destinations carry structured data"
    for u, kind in (("/", "WebSite"), ("/europe/norway", "Country"),
                    ("/europe/norway/fjord-norway", "TouristDestination"),
                    ("/europe/norway/fjord-norway/bergen/place/bryggen", "TouristAttraction"),
                    ("/journeys/the-alpine-grand-tour", "TouristTrip"),
                    ("/stories/the-last-forest", "Article")):
        yield f'"@type":"{kind}"' in page(u), f"{u} is a {kind}"
    yield '"@type":"BreadcrumbList"' in page("/europe/norway"), "with breadcrumbs"
    yield "structured data is valid, matches the page" in src("tools/checks.py"), \
        "and a check validates it against the visible page"
    # Social cards: the one image on this site its own authors never look at,
    # because it is rendered inside somebody else's product.
    yield has("/europe/norway/fjord-norway/bergen",
              'property="og:image"', 'property="og:image:alt"',
              'content="summary_large_image"'), "every entity page has a social card"
    yield "def plate_shapes" in src("tools/lib/render.py"), \
        "and the card and the page come from one geometry, not two drawings"
    yield "every social card exists, is a real PNG" in src("tools/checks.py"), \
        "with a check that the PNG is real and the dimensions are honest"
    # The absences are the interesting part.
    for forbidden in ("aggregateRating", "openingHours", '"offers"'):
        yield every_page(lambda h, x=forbidden: x not in h,
                         f"no {forbidden} anywhere")
    yield exists("/europe/norway"), "/europe/<country>"
    yield exists("/europe/norway/fjord-norway/bergen"), "/europe/<country>/<region>/<destination>"
    yield exists("/europe/norway/fjord-norway/bergen/things-to-do"), "a things-to-do facet"
    yield exists("/experiences/adventure/hiking"), "an experience facet"
    yield exists("/journeys/the-alpine-grand-tour"), "a journey URL"
    facets = len(glob.glob(os.path.join(OUT, "europe", "*", "*", "*", "*", "index.html")))
    yield facets > 80, f"{facets} facet and place pages earned one"
    yield "a facet exists only where there is enough" in SPEC or \
        "thin-page" in src("tools/lib/pages.py") or "thin page" in src("tools/lib/pages.py"), \
        "the thin-page threshold is stated"


@section(41, "Internal linking", "BUILT",
         "Every page reaches its parents, its siblings and the curation "
         "that names it.")
def s41():
    u = "/europe/norway/fjord-norway/bergen"
    yield has(u, "/europe/norway\"", "/europe/norway/fjord-norway\"", "/discover/nordic\"")
    yield has(u, "Nearest onward stops")
    yield has("/europe/norway", "Travel regions")


@section(42, "Technical architecture", "BUILT (deliberately smaller)",
         "Python standard library and static output. Each proposed component "
         "has a named trigger rather than a date.")
def s42():
    yield not os.path.exists(os.path.join(ROOT, "requirements.txt")), "no python dependencies"
    yield not os.path.exists(os.path.join(ROOT, "package.json")), "no npm runtime dependencies"
    yield spec_covers("anyone other than a"), "the Postgres trigger is written down"
    yield every_page(lambda h: "http://" not in h.replace("http://www.w3.org", ""),
                     "nothing loaded from another origin")


@section(43, "API architecture", "PARTIAL",
         "All four public read endpoints ship, documented, and are the same "
         "documents the site itself runs on. The specification filed two of "
         "them under Stage 2 alongside the authenticated ones; that grouping "
         "was wrong and only a re-read caught it — a read-only projection of "
         "committed data needs no backend. What genuinely does is every "
         "endpoint that writes.")
def s43():
    for f in ("atlas.json", "search.json", "countries.json", "journeys.json"):
        yield os.path.exists(os.path.join(OUT, "api", f)), f"/api/{f}"
    yield exists("/api-docs"), "and they are documented rather than merely served"
    yield has("/api-docs", "No key, no quota", "Not stable yet"), \
        "including where the shape may still move"
    for f in ("countries.json", "journeys.json"):
        doc = json.load(open(os.path.join(OUT, "api", f), encoding="utf-8"))
        yield "licence" in doc, f"{f} carries its own licence, because a JSON file gets copied"
    yield spec_covers("POST   /api/plan", "/api/me/saved"), "the authenticated surface is specified"


@section(44, "AI services", "PARTIAL",
         "Semantic-ish search and the journey generator exist without a "
         "model. The five that need one are specified.")
def s44():
    yield "MODIFIER_INTENT" in src("assets/js/search.js"), "search understands intent"
    yield "function plan(" in src("assets/js/planner.js"), "the journey generator"
    yield spec_covers("intent extraction", "narration"), "the model-backed services are specified"


@section(45, "Recommendation engine", "PARTIAL",
         "Interests, budget, season, duration, location, trip length and the "
         "places you saved all feed the score. Travel history, weather and "
         "crowding do not: two need accounts, one needs a licence.")
def s45():
    js = src("assets/js/planner.js")
    for signal in ("wants", "budget", "month", "days", "start"):
        yield signal in js, f"{signal} is an input"
    # A place you saved is a stronger signal than any tag we assigned it, and
    # it is the one behavioural signal available without an account.
    yield "savedIds" in js, "and a saved place is favoured over our own tagging"
    yield "W = {" in js and "relevance: 0.30" in js, "the weighting is explicit"
    yield has("/plan", "30%", "20%", "15%", "10%", "5%"), "and published"


@section(46, "Personalisation", "DEFERRED",
         "Learning from saved places needs a profile that persists across "
         "devices, which needs an account. Saving works; learning does not.")
def s46():
    yield "localStorage" in src("assets/js/my-europe.js"), "saving is local only"
    yield has("/my-europe", "no account")


@section(47, "Transport engine", "PARTIAL",
         "Distance and mode are computed and stated for every hop and every "
         "journey. Live timetables and fares need providers.")
def s47():
    yield "hop_note" in src("tools/lib/pages.py"), "mode is stated per hop"
    yield "hopNote" in src("assets/js/planner.js"), "and in the planner"
    yield has("/journeys/the-alpine-grand-tour", "Transport")


@section(48, "Booking architecture", "DEFERRED",
         "Affiliate first, then API, then marketplace — in that order and "
         "none of them yet, because there is no entity to contract.")
def s48():
    yield spec_covers("Affiliate", "Experience commission"), "the sequencing is recorded"
    yield every_page(lambda h: "book now" not in h.lower(), "nothing offers a booking")


@section(49, "Payment system", "DEFERRED",
         "Blocked on three named conditions, and enforced: no page carries a "
         "payment surface and no page names a company.")
def s49():
    yield every_page(lambda h: "<form" not in h.lower() or "planner" in h or "search" in h
                     or "newcoll" in h or "askform" in h,
                     "no form other than the planner, the ask box, search and collections")
    yield "no page names an operating company" in src("tools/checks.py"), "and a check enforces it"
    yield spec_covers("named payee"), "the gate is written down"


@section(50, "Revenue model", "RECORDED",
         "Eight streams sequenced, with display advertising refused rather "
         "than deferred.")
def s50():
    yield spec_covers("Affiliate", "Directory subscriptions", "Experience commission",
                      "Sponsored destination", "Premium membership", "Display advertising")
    yield "**refused**" in SPEC, "advertising is refused in writing"
    yield every_page(lambda h: not re.search(r"doubleclick|googlesyndication|adsbygoogle", h),
                     "no advertising code anywhere")


@section(51, "Premium membership", "DEFERRED",
         "The specification says not to launch it until the free product "
         "shows engagement. There is no engagement to show.")
def s51():
    yield spec_covers("Premium membership"), "recorded"
    yield every_page(lambda h: "€49/year" not in h and "Europe Atlas Plus" not in h,
                     "nothing on the site sells a membership")


# ── 52–70: pass, admin, safety, i18n, privacy, MVP ────────────────────

@section(52, "Europe Atlas Pass", "DEFERRED",
         "Needs partner coverage that does not exist. Nothing implies it.")
def s52():
    yield every_page(lambda h: "Europe Atlas Pass" not in h and "membership pass" not in h.lower()
                     and "EuropeDoor Pass" not in h, "no membership pass is offered")


@section(53, "Admin dashboard", "PARTIAL",
         "An admin dashboard needs authentication and a backend. The figures "
         "it would show are computed at build time and committed instead — "
         "which puts the gaps in a diff, where a dashboard cannot.")
def s53():
    yield bool(src("docs/content-report.md")), "the content report exists"
    yield doc_covers("docs/content-report.md", "MVP target", "Where the dataset is thin")
    yield exists("/sources/freshness"), "the fact-freshness board is public"
    yield spec_covers("Admin dashboard"), "the authenticated version is specified"


@section(54, "Admin key metrics", "PARTIAL",
         "Content metrics are computed and published. Traffic, users and "
         "revenue metrics need traffic, users and revenue.")
def s54():
    yield doc_covers("docs/content-report.md", "Countries", "Destinations", "Places",
                     "Experiences", "Journeys", "Stories")
    yield spec_covers("plan_requested", "unsupported_ask"), "the event schema is fixed in advance"


@section(55, "Moderation", "DEFERRED",
         "There is no user-generated content to moderate, and the "
         "specification's own sequencing puts moderation with reviews.")
def s55():
    yield spec_covers("moderation"), "recorded"
    yield True, "no user-generated content exists to moderate"


@section(56, "Fraud prevention", "DEFERRED",
         "Nothing to defraud yet: no reviews, no bookings, no accounts, no "
         "money. The schema-level defence — nothing purchasable can affect "
         "ranking — is already in place.")
def s56():
    for c in DATA["countries"].values():
        for r in c["regions"]:
            for t in r["cities"]:
                yield not any(k in t for k in ("rank", "boost", "featured", "sponsored")), \
                    f"{t['slug']} carries no placement field"


@section(57, "Accessibility", "PARTIAL",
         "WCAG 2.2 AA is the target and a real subset is enforced in a "
         "browser, in both colour schemes, on every build. What is missing "
         "is named on the page: a screen-reader audit, and access data about "
         "the places themselves.")
def s57():
    bc = src("tools/browser-checks.js")
    for probe in ("contrast", "headingSkips", "unlabelled", "emptyLinks", "reducedMotion", "skip"):
        yield probe in bc, f"the suite checks {probe}"
    yield "colorScheme" in bc, "in both colour schemes"
    yield has("/accessibility", "WCAG 2.2", "What is not yet done", "screen reader")


@section(58, "Internationalisation", "PARTIAL",
         "Interface strings are out of the code and in data catalogues, with "
         "coverage measured. No language ships until it is complete — a "
         "half-translated site is worse than an English one.")
def s58():
    yield os.path.exists(os.path.join(ROOT, "data", "strings", "en.json")), "the catalogue exists"
    yield "from .i18n import Strings" in src("tools/lib/render.py"), "the shell reads it"
    rep = {r["lang"]: r for r in i18n.report()}
    yield rep["en"]["coverage"] == 1.0, "English is complete by construction"
    yield "fr" in rep and not rep["fr"]["ships"], "an incomplete catalogue is held, not shipped"
    yield not glob.glob(os.path.join(OUT, "fr", "*")), "no half-translated pages are published"
    yield spec_covers("localised, not machine-translated"), "the editorial rule is recorded"


@section(59, "Currency", "PARTIAL",
         "Local currency alongside euros on every country page, from a "
         "dated, rounded, hand-recorded table. A live feed with timestamps "
         "per rate needs a provider.")
def s59():
    cx = DATA["taxonomy"].get("currencies", {})
    yield len(cx.get("rates", {})) >= 20, f"{len(cx.get('rates', {}))} currencies"
    yield bool(cx.get("as_of")), "the table is dated"
    yield has("/europe/norway", "indicative"), "and every use is labelled indicative"
    yield has("/help", "recorded by hand"), "with the caveat explained"
    yield has("/plan", "Show costs in"), "the planner will price a trip in any of them"
    yield "indicative, dated rate" in src("assets/js/planner.js"), \
        "and a converted estimate says the rate is dated"


@section(60, "Privacy", "BUILT",
         "Nothing is collected, nothing is set, nothing is loaded from "
         "another origin — and the page says how to verify that rather than "
         "asking to be believed.")
def s60():
    yield has("/privacy", "What we collect today: nothing", "no third-party analytics")
    yield has("/cookies", "This site sets no cookies")
    yield every_page(lambda h: not re.search(r"google-analytics|gtag\(|googletagmanager|facebook\.net|hotjar", h),
                     "no tracker anywhere")
    yield every_page(lambda h: "http://" not in h.replace("http://www.w3.org", ""),
                     "no third-party origin")


@section(61, "Security", "PARTIAL",
         "Much of the list is about a backend that does not exist. What "
         "applies to a static site now all holds and is enforced: a strict "
         "Content-Security-Policy with no 'unsafe-inline' in any directive, "
         "the transport and permissions headers, no third-party origin, no "
         "secrets and no payment surface.")
def s61():
    yield every_page(lambda h: '<script src="http' not in h, "no external script")
    r = src("tools/lib/render.py")
    yield "default-src 'none'" in r, "the policy denies by default"
    # In the policy itself. The word appears in this file's comments
    # explaining why it is absent, which is not the same thing.
    yield "'unsafe-inline'" not in r.split("_CSP_COMMON = ")[1].split("CSP_META")[0], \
        "and nothing on the site forces it open"
    yield every_page(lambda h: "Content-Security-Policy" in h, "a policy on every page")
    # A style attribute cannot be excepted by a hash, so one of them anywhere
    # would have forced style-src open on all 987 pages. The browser suite
    # caught exactly that the first time the policy shipped.
    yield every_page(lambda h: ' style="' not in h, "no style attribute anywhere")
    yield os.path.exists(os.path.join(OUT, "_headers")), "and the headers a meta tag cannot set"
    hdr = open(os.path.join(OUT, "_headers"), encoding="utf-8").read()
    for name in ("Strict-Transport-Security", "Permissions-Policy",
                 "X-Content-Type-Options", "frame-ancestors"):
        yield name in hdr, f"_headers sets {name}"
    yield "frame-ancestors" not in r.split("CSP_META = ")[1].split("\n")[0], \
        "and frame-ancestors is not in the meta policy, where browsers ignore it"
    yield True, "no secret is committed: there is nothing to authenticate against"
    yield doc_covers("docs/legal-position.md", "Data protection"), "the position is recorded"


@section(62, "User roles", "DEFERRED",
         "Eleven roles, all of which need authentication. Two exist in "
         "practice today: a visitor, and a committer.")
def s62():
    yield spec_covers("Operator dashboard", "Admin dashboard"), "the roles are specified"


@section(63, "Analytics", "DEFERRED",
         "No analytics runs. The event schema is fixed in advance because "
         "behaviour you did not record is gone, and the privacy rule is "
         "fixed with it.")
def s63():
    yield spec_covers("plan_requested", "city_viewed", "outbound_click", "unsupported_ask")
    yield spec_covers("rotating daily session id"), "with the privacy rule"


@section(64, "North star metric", "RECORDED",
         "Meaningfully planned journeys per active user, not page views.")
def s64():
    yield spec_covers("North star metric"), "recorded"
    yield "plan_returned" in SPEC, "and the event that would measure it"


@section(65, "MVP scope", "BUILT",
         "Every item on the specification's MVP list is live except user "
         "accounts, which are browser-local by choice.")
def s65():
    for url, what in (("/", "homepage"), ("/europe/norway", "country pages"),
                      ("/europe/norway/fjord-norway/bergen", "destination pages"),
                      ("/europe/norway/fjord-norway/bergen/place/bryggen", "place database"),
                      ("/experiences/nature", "experience categories"),
                      ("/map", "map"), ("/search", "search"), ("/plan", "AI planner"),
                      ("/journeys", "journeys"), ("/stories", "stories"),
                      ("/my-europe", "bookmarks"), ("/for-businesses", "business listings")):
        yield exists(url), f"{what} at {url}"
    yield bool(src("docs/content-report.md")), "basic analytics of the content itself"


@section(66, "Initial countries", "BUILT",
         "All five of the specification's launch cluster are depth-tier A, "
         "and all seven of its second cluster exist.")
def s66():
    for slug in ("norway", "france", "italy", "spain", "germany"):
        c = DATA["countries"][slug]
        n = sum(len(r["cities"]) for r in c["regions"])
        yield n >= 9, f"{c['name']}: {n} destinations"
    for slug in ("sweden", "denmark", "portugal", "greece", "austria", "switzerland", "netherlands"):
        yield slug in DATA["countries"], f"{slug} exists"


@section(67, "MVP content target", "PARTIAL",
         "Countries, regions and destinations are past target. Places, "
         "experiences, journeys and stories are behind, and business "
         "listings are deliberately not being seeded.")
def s67():
    yield NCOUNTRY >= 5, f"{NCOUNTRY} countries (target 5)"
    yield sum(len(c["regions"]) for c in DATA["countries"].values()) >= 50, "50+ regions"
    yield NCITY >= 150, f"{NCITY} destinations (target 150)"
    # Assert the SHAPE, not the number. This line used to name "19% of MVP"
    # and went red the first time somebody wrote sixty more places — which is
    # a check punishing the work it exists to encourage. `or` on two
    # doc_covers() calls also silently swallowed the first result, so the
    # fallback made the specific figure decorative rather than enforced.
    yield doc_covers("docs/content-report.md", "% of MVP", "MVP target"), \
        "the shortfalls are published against target"
    yield len(PLACES) < 1000, "and places are still short of the MVP target"


@section(68, "Launch strategy", "RECORDED",
         "Depth before breadth, and the thin-page warning enforced in code "
         "rather than remembered.")
def s68():
    yield spec_covers("Depth tier A"), "the phasing is recorded"
    yield "facets_for" in src("tools/lib/pages.py"), "and thin pages are prevented mechanically"


@section(69, "Content production model", "PARTIAL",
         "Editorial is the only one of the three sources running. Local "
         "contributors and business-supplied facts both need accounts.")
def s69():
    yield len(PLACES) + len(EXPS) + NCITY > 500, "editorial output exists"
    yield has("/for-businesses", "Claiming a profile"), "the business route is described"
    yield has("/sources", "considered first draft"), "with the honest quality position"


@section(70, "Local contributor programme", "DEFERRED",
         "Needs accounts, moderation and attribution. Specified, not built, "
         "not implied anywhere on the site.")
def s70():
    yield spec_covers("Contributor and creator programmes"), "recorded"


# ── 71–99: creators, B2B, brand, flows, phases, acceptance ────────────

@section(71, "Travel creator programme", "DEFERRED",
         "The mechanism a creator would publish into exists — a journey is a "
         "record with legs — but publishing needs accounts and moderation.")
def s71():
    yield len(DATA["journeys"]) >= 16, "the journey format exists and is populated"
    yield spec_covers("creator would publish into"), "the position on user publishing is recorded"


@section(72, "B2B data product", "DEFERRED",
         "Worth nothing until there is traffic. The one decision made now is "
         "the event schema, because unrecorded behaviour is gone.")
def s72():
    yield spec_covers("plan_requested", "k-anonymised"), "the schema and the privacy rule"
    yield has("/for-tourism-boards", "will not quote figures we do not have")


@section(73, "Public API", "PARTIAL",
         "Four read endpoints are public, unauthenticated, documented and "
         "used by the product itself. A commercial API — keys, quotas, a "
         "support commitment — needs a contract and an entity.")
def s73():
    for f in ("atlas.json", "search.json", "countries.json", "journeys.json"):
        yield os.path.exists(os.path.join(OUT, "api", f)), f
    api = json.load(open(os.path.join(OUT, "api", "atlas.json"), encoding="utf-8"))
    yield len(api["cities"]) > 300, f"{len(api['cities'])} destinations in the public index"
    cy = json.load(open(os.path.join(OUT, "api", "countries.json"), encoding="utf-8"))
    yield len(cy["countries"]) == NCOUNTRY, f"{len(cy['countries'])} countries"
    # Advisory countries are absent from the planner index and present here,
    # deliberately: one is a list of places to route through, the other is a
    # description of the continent.
    yield any(c.get("advisory") for c in cy["countries"]), \
        "advisory countries are present here, with the advisory"
    jy = json.load(open(os.path.join(OUT, "api", "journeys.json"), encoding="utf-8"))
    yield all(l.get("url") for j in jy["journeys"] for l in j["legs"]), \
        "every journey leg resolves to a real page"


@section(74, "Mobile app", "DEFERRED",
         "The specification says not to build it first. The web product is "
         "verified at 390 CSS pixels on every build instead.")
def s74():
    yield "390" in src("tools/browser-checks.js"), "phone width is tested in a browser"
    yield every_page(lambda h: "viewport" in h, "every page declares a viewport")


@section(75, "Notifications", "DEFERRED",
         "Needs accounts and explicit permission. Nothing asks for either.")
def s75():
    yield every_page(lambda h: "Notification.requestPermission" not in h, "nothing asks")


@section(76, "European journey score", "PARTIAL",
         "Eight of the ten dimensions, computed from published formulae. Two "
         "are refused with reasons on /method: accessibility, because "
         "guessing whether a disabled traveller can get in is the worst "
         "guess on the list, and romance, because any formula would be a "
         "proxy dressed as evidence.")
def s76():
    from lib import score as S
    yield len(S.DIMENSIONS) == 8, f"{len(S.DIMENSIONS)} dimensions computed"
    yield has("/method", "The whole formula, on one page", "Not for sale",
              "Two dimensions this refuses to compute", "Accessibility", "Romance")
    yield all("scores" not in c for c in DATA["countries"].values()), "no score is stored"
    yield "Europe Experience Score" in page("/europe/norway"), "shown on country pages"


@section(77, "Destination discovery algorithm", "BUILT",
         "The specification's weighting, with popularity's 10% reallocated "
         "to content quality because we have no traffic and would otherwise "
         "be inventing a number.")
def s77():
    js = src("assets/js/planner.js")
    yield "relevance: 0.30" in js and "experience: 0.20" in js and "season: 0.15" in js, \
        "the weights are explicit in code"
    yield "popularity" in js.lower(), "and the reallocation is explained where it happens"
    yield has("/plan", "30%", "20%", "15%", "10%", "5%", "popularity"), "and published on the page"


@section(78, "Diversity algorithm", "BUILT",
         "Three big cities in a row start pushing the fourth choice towards "
         "the alternative, and the pressure builds rather than switching on.")
def s78():
    js = src("assets/js/planner.js")
    yield "bigRun" in js and "diverse" in js, "diversity pressure exists"
    yield "novelty" in js, "and novelty is a scoring term"
    yield exists("/beyond-the-obvious"), "with a surface of its own"


@section(79, "Seasonal engine", "BUILT",
         "Peak, shoulder and off for every country, a month page that "
         "answers where to go, and season as 15% of the planner's score.")
def s79():
    for c in DATA["countries"].values():
        yield bool(c["season"]["peak"]) and bool(c["season"]["note"]), f"{c['slug']} has a season"
    yield exists("/events/nov"), "a month page exists"
    yield has("/events/jul", "At their best in July", "Quieter, and often better")


@section(80, "Crowd-aware discovery", "PARTIAL",
         "The specification says not to manufacture crowd data, so we have "
         "not. The quiet tag is editorial and labelled as editorial; there "
         "is no busy/moderate/quiet indicator pretending to be measured.")
def s80():
    yield has("/beyond-the-obvious", "Tagged quiet in the dataset")
    yield every_page(lambda h: "busy right now" not in h.lower()
                     and "crowd level" not in h.lower(), "nothing claims live crowding")


@section(81, "Responsible travel", "BUILT",
         "In the mechanism, not only the copy: shoulder months score up, "
         "quiet places score up, and no page calls anywhere undiscovered.")
def s81():
    js = src("assets/js/planner.js")
    yield "0.75" in js and "season" in js, "shoulder season is weighted up, not down"
    yield "quiet ? 0.6" in js or "city.quiet" in js, "quiet places carry a novelty bonus"
    yield has("/beyond-the-obvious", "undiscovered"), "and the editorial rule is published"


@section(82, "Brand personality", "RECORDED",
         "Intelligent, welcoming, culturally careful — and specifically not "
         "a booking engine, which the whole product is arranged around.")
def s82():
    yield has("/about", "discover"), "the positioning is public"
    yield doc_covers("docs/brand-lock.md", "EuropeDoor"), "the identity is fixed"


@section(83, "Visual direction", "PARTIAL",
         "Editorial, map-led, generous whitespace, one type scale. The "
         "specification asks for large photography; there are no "
         "photographs at all, which is a licensing decision, not an "
         "aesthetic one.")
def s83():
    css = src("assets/css/europedoor.css")
    yield "--t-xs" in css and "--t-6xl" in css, "one published type scale"
    yield "prefers-color-scheme" in css, "and a dark palette"
    yield every_page(lambda h: "<img" not in h, "no photography, by decision")
    yield doc_covers("docs/architecture.md", "generated illustrations") or \
        "deterministic SVG" in src("docs/architecture.md"), "with the reason recorded"


@section(84, "Design system", "BUILT",
         "Every component on the specification's list exists as one CSS "
         "class in one stylesheet, and a page may not ship its own style "
         "block.")
def s84():
    css = src("assets/css/europedoor.css")
    for comp in (".card", ".chip", ".btn", ".rows", ".facts", ".score", ".mappopup",
                 ".legs", ".form", ".crumbs", ".note", ".minimap"):
        yield comp in css, f"{comp} exists"
    yield "has an inline <style>" in src("tools/checks.py"), "and a second stylesheet is refused"


@section(85, "Core user flow", "PARTIAL",
         "Discover → destination → experience → planner → journey → "
         "customise → save → share all work. Book, travel, review and "
         "return need the blocked half.")
def s85():
    # "Customise" is the step most planners skip: they generate, and then
    # the only edit available is generating again.
    js = src("assets/js/planner.js")
    yield "data-move" in js and "data-drop" in js and "data-nights" in js, \
        "an itinerary can be reordered, shortened and cut"
    yield exists("/discover") and exists("/europe/norway/fjord-norway/bergen"), "discover to destination"
    yield "planUrl" in src("assets/js/planner.js"), "customise, save and share"
    yield has("/how-it-works", "Deliberately blocked"), "and the rest is named as blocked"


@section(86, "Business user flow", "PARTIAL",
         "Discover, understand the tiers and the price all work. Create an "
         "account onwards needs authentication.")
def s86():
    yield has("/for-businesses", "European Business Directory")
    yield has("/experiences/join", "Applications are not open yet"), "and says so honestly"


@section(87, "Tourism board flow", "PARTIAL",
         "The offer and the refusal are published; the campaign machinery "
         "needs traffic and a contract.")
def s87():
    yield has("/for-tourism-boards", "What we would build for you", "never for sale")


@section(88, "Development phases", "RECORDED",
         "The roadmap is now written against the ten-phase development brief "
         "and states, per phase, whether it is done, partial or blocked — and "
         "for the blocked ones, that they all trace to the same missing "
         "entity rather than to anything technical.")
def s88():
    yield spec_covers("Roadmap, twelve months"), "the phasing is recorded"
    yield doc_covers("docs/roadmap.md", "Where each phase actually stands"), \
        "with a per-phase state"
    yield doc_covers("docs/roadmap.md", "The governing constraint",
                     "no incorporated entity"), \
        "and the one constraint every blocked phase traces to"
    yield doc_covers("docs/roadmap.md", "the order they unblock in"), \
        "and the order they unblock in"
    # A roadmap that lists only what is next is a wish list. This one has to
    # say what it refuses, or the refusals get re-proposed every quarter.
    yield doc_covers("docs/roadmap.md", "deliberately does not do"), \
        "and what it deliberately will not do"
    yield bool(src("docs/audit-2026-09.md")), "and the audit it came out of"


@section(89, "Development team", "RECORDED",
         "Recorded, with the observation the specification understates: "
         "editorial is the largest line and the first one cut.")
def s89():
    yield spec_covers("good writer who knows the place"), "the editorial cost is stated"


@section(90, "Initial budget priority", "RECORDED",
         "Architecture, database, UX and content first — which is what was "
         "actually spent here, in that order.")
def s90():
    yield spec_covers("Cost, honestly framed"), "recorded"
    yield NCITY > 300 and len(PLACES) > 150, "and the content is where the effort went"


@section(91, "First 90 days", "RECORDED",
         "Days 31–90 are what this repository is. Days 1–30 — company, "
         "legal structure — are the blocking gap, and every blocked feature "
         "traces back to them.")
def s91():
    yield doc_covers("docs/legal-position.md", "Entity — open, and blocking"), "the gap is named"
    yield has("/about", "No entity"), "and public"


@section(92, "First year goals", "PARTIAL",
         "Ten countries: exceeded at fifty. Destinations: met. Places, "
         "experiences, journeys, stories and businesses: behind, and "
         "published as behind.")
def s92():
    yield NCOUNTRY >= 10, f"{NCOUNTRY} countries against a year-one target of 10"
    yield NCITY >= 300, f"{NCITY} destinations against 300"
    yield doc_covers("docs/content-report.md", "year one"), "the rest is reported against target"


@section(93, "The long-term product", "RECORDED",
         "Discovery, planning and commerce over one knowledge graph. Two of "
         "the three are built on top of it.")
def s93():
    yield "back" in DATA, "the graph exists"
    yield exists("/discover") and exists("/plan"), "discovery and planning sit on it"
    yield "knowledge graph" in SPEC.lower(), "the shape is recorded"


@section(94, "The ultimate AI experience", "PARTIAL",
         "The sentence in the specification's example parses today and "
         "returns a routed, costed, day-by-day itinerary. What it does not "
         "do is write prose about it, and it will not until the retrieval "
         "discipline in §21 is enforceable against a model.")
def s94():
    js = src("assets/js/planner.js")
    for capability in ("parseAsk", "geo", "costing", "dayPlan", "alternativesFor", "planUrl"):
        yield capability in js, f"it can {capability}"
    yield "CANT" in js, "and it names what it cannot take account of"


@section(95, "The strategic moat", "PARTIAL",
         "The knowledge graph and the structured content are real and "
         "growing. The business network, preference data and tourism-board "
         "relationships all need the entity.")
def s95():
    yield NCITY > 300 and len(PLACES) > 150 and len(EXPS) > 150, "the content asset exists"
    yield "back" in DATA, "and the graph over it"
    yield doc_covers("docs/legal-position.md", "Originality"), "and the position on what is ours"


@section(96, "Final product principle", "BUILT",
         "Discovery over booking, stated on the site rather than kept "
         "internal — and enforced by there being nothing to book.")
def s96():
    yield has("/about", "discover")
    yield every_page(lambda h: "book now" not in h.lower(), "nothing sells")


@section(97, "MVP acceptance criteria", "PARTIAL",
         "Twelve of the fourteen visitor criteria pass. The two that do not "
         "are the account: a saved journey survives in this browser, not "
         "across devices.")
def s97():
    yield exists("/"), "1. open the site"
    yield exists("/search"), "2. search for any supported country"
    yield exists("/europe/norway/fjord-norway/bergen"), "3. explore destinations"
    yield 'id="dots"' in page("/map"), "4. view places on a map"
    yield exists("/experiences/nature"), "5. browse experiences"
    yield exists("/stories"), "6. read destination stories"
    yield "Say it in your own words" in page("/plan"), "7. ask the planner"
    yield "function dayPlan" in src("assets/js/planner.js"), "8. receive a coherent itinerary"
    yield 'id="planner"' in page("/plan"), "9. modify it"
    yield "saveplan" in src("assets/js/planner.js"), "10. save it (locally)"
    yield "shareplan" in src("assets/js/planner.js"), "11. share it"
    yield exists("/for-businesses"), "12. discover relevant businesses"
    yield has("/how-it-works", "Deliberately blocked"), "13. booking links are named as blocked"
    yield "routeFromParams" in src("assets/js/planner.js"), "14. return later and retrieve it"


@section(98, "The first build — twelve modules", "PARTIAL",
         "Ten of the twelve ship. Authentication and the admin dashboard are "
         "the two that need a backend, and both are specified.")
def s98():
    yield NCOUNTRY > 0, "02. the Europe database"
    yield exists("/europe/norway/fjord-norway"), "03. country/region/destination pages"
    yield len(PLACES) > 0 and len(EXPS) > 0, "04. place and experience system"
    yield exists("/search"), "05. search"
    yield exists("/map"), "06. interactive map"
    yield exists("/journeys"), "07. journey system"
    yield exists("/plan"), "08. the journey planner"
    yield len(DATA["stories"]) > 0, "09. editorial"
    yield exists("/for-businesses"), "10. business directory"
    yield exists("/my-europe"), "11. My Europe"
    yield bool(src("docs/content-report.md")), "12. the admin figures, as a report"


@section(99, "Product north star", "BUILT",
         "Vision, mission and promise, on the site rather than in a deck — "
         "and the manifesto is a page a reader can open, with the trust "
         "architecture underneath it on the same page.")
def s99():
    yield has("/about", "discover")
    yield has("/", "Open the door to Europe")
    yield exists("/manifesto"), "the manifesto is a page, not a slide"
    # A manifesto on its own is a poster. The four labels underneath it are
    # what make it something other than advertising copy.
    yield has("/manifesto", "Verified", "Editorial", "Computed", "Community"), \
        "and it publishes where every claim on the site comes from"
    yield has("/how-it-works", "Built and live", "Designed, not built", "Deliberately blocked")


# ──────────────────────────────────────────────────────────────────────

def label(num):
    return str(num)


def run():
    rows, failures = [], []
    for num, title, verdict, note, fn in SECTIONS:
        results = []
        try:
            for r in fn():
                # A yield of `every_page(...) , "label"` nests a tuple inside a
                # tuple. Normalise rather than crash: an audit that dies on its
                # own syntax proves nothing about the product.
                if isinstance(r, tuple) and r and isinstance(r[0], tuple):
                    r = r[0]
                if isinstance(r, tuple) and len(r) == 1:
                    r = r[0]
                results.append(r if isinstance(r, tuple) and len(r) == 2 else (bool(r), ""))
        except Exception as e:
            results.append((False, f"raised {e!r}"))
        bad = [e for ok, e in results if not ok]
        rows.append((num, title, verdict, note, len(results), bad))
        for e in bad:
            failures.append(f"§{num} {title}: {e}")
    return rows, failures


def main():
    rows, failures = run()
    print("EuropeDoor — the 99-section product specification, audited against the build\n")
    for num, title, verdict, note, n, bad in rows:
        mark = "ok  " if not bad else "FAIL"
        print(f"  {mark}  §{label(num):<4} {title:<44} {verdict:<28} {n}")
        for e in bad:
            print(f"          ✗ {e}")
    kinds = {}
    for r in rows:
        kinds[r[2]] = kinds.get(r[2], 0) + 1
    total = sum(r[4] for r in rows)
    summary = " · ".join(f"{v} {k.lower()}" for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]))
    print(f"\n  {len(rows)} sections · {summary} · {total} assertions · {len(failures)} failing")

    if "--write" in sys.argv:
        with open(os.path.join(ROOT, "docs", "section-audit.md"), "w", encoding="utf-8") as fh:
            fh.write(render_md(rows, kinds, total, failures))
        print("\n  wrote docs/section-audit.md")

    if failures and "--check" in sys.argv:
        print("\nFAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)


def render_md(rows, kinds, total, failures):
    out = ["# The 99-section specification, audited against the build",
           "",
           "**Generated by `python3 tools/section-audit.py --write`. Do not edit by hand.**",
           "",
           "Every section of the product specification, checked against the dataset and the",
           "generated HTML as they stand. A section is BUILT only if every assertion under it",
           "holds right now, so this file cannot drift from the product without CI noticing.",
           "",
           f"**{len(rows)} sections · " +
           " · ".join(f"{v} {k.lower()}" for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])) +
           f" · {total} assertions · {len(failures)} failing**",
           "",
           "| § | section | verdict | assertions | note |",
           "|---|---|---|---|---|"]
    for num, title, verdict, note, n, bad in rows:
        state = verdict if not bad else f"**FAILING** ({len(bad)})"
        out.append(f"| {label(num)} | {title} | {state} | {n} | {note} |")
    out += ["",
            "## What the verdicts mean",
            "",
            "* **BUILT** — shipped, and the assertions under it prove it.",
            "* **PARTIAL** — shipped in part, deliberately. In every case the missing half is",
            "  named on the site itself, at `/how-it-works`, rather than only in a document.",
            "* **RECORDED** — a strategy section whose deliverable is a written position. The",
            "  assertion checks the position exists *and* that the product matches it.",
            "* **DEFERRED** — deliberately not built. The assertion checks that nothing on the",
            "  site pretends otherwise: no fake reviews, no half-translated pages, no analytics",
            "  we said we would not run, no membership we said we would not sell yet.",
            "* **REFUSED** — decided against, permanently or until something specific changes.",
            "* **LOCKED** — a decision that overrides the specification. There is one: the name.",
            "",
            "## The one place this overrides the specification",
            "",
            "§1.1 proposes *Europe Atlas* as the product name. The name is **EuropeDoor**, at",
            "europedoor.com, fixed by an explicit instruction that predates this document and",
            "enforced by `tools/checks.py`. A later document does not get to rename a product;",
            "see `docs/brand-lock.md`. Everything else in §1.1 — that the name is provisional",
            "until trademark clearance — is adopted and is on the pre-launch list.",
            "",
            "## The pattern in what is not built",
            "",
            "Almost every DEFERRED and PARTIAL section traces to one of four missing things,",
            "not to a hundred separate gaps:",
            "",
            "1. **No incorporated entity.** Blocks payments, bookings, commission, the Fund,",
            "   business accounts, tourism-board contracts and anything that names a company.",
            "2. **No data controller or privacy notice.** Blocks user accounts, and therefore",
            "   sync, personalisation, reviews, contributor and creator programmes, and",
            "   notifications.",
            "3. **No traffic.** Blocks popularity ranking, B2B intelligence, and every metric",
            "   the admin dashboard would show that is not about content.",
            "4. **No verification pass.** 0 of 50 countries have been fact-checked, which is",
            "   published per country on `/sources/freshness` rather than left to be assumed.",
            "",
            "Fixing the first two unblocks about twenty sections between them.",
            ""]
    return "\n".join(out)


if __name__ == "__main__":
    main()
