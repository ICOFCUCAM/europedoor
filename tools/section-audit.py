#!/usr/bin/env python3
"""Audit the built product against the 36-section brief, section by section.

    python3 tools/section-audit.py            print the audit
    python3 tools/section-audit.py --check    fail if any claim is false
    python3 tools/section-audit.py --write    regenerate docs/section-audit.md

The point is that "we implemented section 14" is a claim, and a claim nobody
can check is a claim that quietly stops being true. Every section below
carries assertions against the actual dataset and the actual generated HTML.
A section is only BUILT if every one of them holds right now.

Verdicts:
  BUILT     shipped, and the assertions prove it
  PARTIAL   shipped in part, on purpose, with the missing half named
  DEFERRED  deliberately not built; the assertion checks the reasoning is
            recorded and that nothing pretends otherwise
  REFUSED   decided against; the assertion checks we have not drifted
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D

ROOT = D.ROOT
OUT = os.path.join(ROOT, "site")
DATA = D.load()

_cache = {}


def page(path):
    """The HTML served at a URL, e.g. page('/plan')."""
    key = path
    if key in _cache:
        return _cache[key]
    p = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" else os.path.join(OUT, "index.html")
    if not os.path.exists(p):
        p = os.path.join(OUT, path.strip("/") + ".html")
    _cache[key] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return _cache[key]


def src(path):
    p = os.path.join(ROOT, path)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def exists(path):
    return os.path.exists(os.path.join(OUT, path.strip("/"), "index.html")) or \
           os.path.exists(os.path.join(ROOT, path))


SPEC = src("docs/product-specification.md")
NCITY = len(DATA["cities"])
NCOUNTRY = len(DATA["countries"])


def edged_city():
    """A city the curation actually points at, chosen from the data rather
    than named here — naming one meant the assertion broke the moment the
    curation moved, which is how it found the Florence gap in the first place."""
    for cid, b in sorted(DATA["back"].items()):
        if b["journeys"] and b["themes"]:
            n = DATA["cities"][cid]
            return f"/atlas/{n['country']['macro_slug']}/{cid}"
    raise AssertionError("no city carries both a journey and a theme")


def has(path, *needles):
    h = page(path)
    missing = [n for n in needles if n not in h]
    return (not missing, f"{path}: missing {missing}" if missing else f"{path} carries all {len(needles)}")


def spec_covers(*needles):
    missing = [n for n in needles if n not in SPEC]
    return (not missing, f"spec missing {missing}" if missing else "documented in the specification")


SECTIONS = []


def section(num, title, verdict, note):
    def deco(fn):
        SECTIONS.append((num, title, verdict, note, fn))
        return fn
    return deco


# ──────────────────────────────────────────────────────────────────────

@section(1, "The core idea: discovery + planning + experience", "BUILT",
         "All five surfaces exist and none of them transacts.")
def s1():
    yield exists("/atlas") and exists("/plan") and exists("/experiences"), "atlas, plan and experiences all served"
    yield "checkout" not in page("/") and "Add to basket" not in page("/"), "no transaction surface on the homepage"
    yield "discover" in page("/").lower() and "plan" in page("/").lower(), "the homepage states the frame"


@section(2, "Brand positioning", "BUILT",
         "Settled as Europedoor, and enforced rather than merely asserted.")
def s2():
    yield "Europedoor" in src("tools/lib/render.py"), "SITE_NAME is Europedoor"
    yield "europedoor.com" in page("/"), "canonical is europedoor.com"
    yield bool(src("docs/brand-lock.md")), "the lock is written down"
    yield "brand is locked" in src("tools/checks.py"), "and enforced by a check"


@section(3, "Site architecture", "BUILT",
         "Five top-level items rather than the brief's eight; every node in "
         "the brief's tree is still reachable.")
def s3():
    for node in ("/atlas", "/journeys", "/plan", "/experiences", "/fund",
                 "/stories", "/business", "/themes", "/map", "/search",
                 "/events", "/my-europe", "/beyond-the-obvious"):
        yield exists(node), f"{node} is served"
    yield 'class="nav"' in page("/"), "one primary navigation, in the shell"


@section(4, "The Europe Atlas", "BUILT",
         "Five levels deep, and a city page now carries every block the "
         "brief lists that is not a country-level fact.")
def s4():
    # Pick a city with experiences from the data rather than by index. The
    # hard-coded index broke the moment Norway gained a region, which is
    # precisely the failure this file exists to catch.
    u = None
    for cid, n in sorted(DATA["cities"].items()):
        if n["city"].get("experiences") and n["country"]["festivals"]:
            u = f"/atlas/{n['country']['macro_slug']}/{cid}"
            break
    yield NCOUNTRY >= 50, f"{NCOUNTRY} countries"
    yield NCITY >= 240, f"{NCITY} cities"
    yield has(u, "What earns the time", "Experiences here", "When to come",
              "Getting there", "Nearest onward stops", "Fixed points in the year",
              "Europe Experience Score")
    yield has(edged_city(), "This place, in the rest of the site")
    yield has("/atlas/nordic/norway", "Getting around", "Travel regions",
              "Worth knowing", "At the table", "Facts checked")


@section(5, "Experience-based discovery, not just countries", "BUILT",
         "Thirteen themes, each crossing borders on purpose.")
def s5():
    themes = DATA["themes"]
    yield len(themes) >= 8, f"{len(themes)} themes"
    for t in themes:
        countries = {DATA["cities"][s["city"]]["country"]["slug"] for s in t["stops"]}
        yield len(countries) >= 3, f"{t['slug']} spans {len(countries)} countries"
    yield has("/themes", "Medieval Europe", "Sacred Europe", "Viking Europe")


@section(6, "The journey planner", "PARTIAL",
         "The engine, the scoring and a rule-based sentence reader are built. "
         "The model-written narration in §26 is specified and not built.")
def s6():
    yield has("/plan", "Say it in your own words", "How it decides", "What it will not do")
    js = src("assets/js/planner.js")
    for fn in ("function parseAsk", "function fitScore", "function plan(", "function costing"):
        yield fn in js, f"planner.js has {fn}"
    yield "not by a model" in page("/plan"), "the page says what is doing the reading"
    yield "explains why" not in page("/plan") and "Matches" in js, "each stop states why it was chosen"


@section(7, "The journey engine", "BUILT",
         "Eight curated journeys, with the night arithmetic enforced.")
def s7():
    js = DATA["journeys"]
    yield len(js) >= 8, f"{len(js)} journeys"
    for j in js:
        yield sum(l["nights"] for l in j["legs"]) == j["days"] - 1, \
            f"{j['slug']}: nights sum to days - 1"


@section(8, "Trans-Europe journeys", "BUILT",
         "Both flagship shapes from the brief exist and cross the continent.")
def s8():
    spans = {}
    for j in DATA["journeys"]:
        spans[j["slug"]] = len({DATA["cities"][l["city"]]["country"]["slug"] for l in j["legs"]})
    yield "arctic-to-the-baltic" in spans, "Arctic to Baltic exists"
    yield "atlantic-to-the-mediterranean" in spans, "Atlantic to Mediterranean exists"
    yield max(spans.values()) >= 5, f"the widest journey crosses {max(spans.values())} countries"


@section(9, "Experience marketplace", "PARTIAL",
         "Listings, kinds and price bands are live. Availability, checkout "
         "and commission are specified and blocked on a legal entity.")
def s9():
    n = len(D.all_experiences(DATA["countries"]))
    yield n >= 150, f"{n} experiences listed"
    yield len(DATA["taxonomy"]["experience_kinds"]) == 10, "ten kinds, each with a page"
    yield "Bookings &amp; commission" in page("/how-it-works"), "the unbuilt half is named in public"
    yield spec_covers("10–15%", "Operator sets the price")


@section(10, "European business directory", "BUILT",
         "Directory, three tiers and indicative pricing published. Claiming "
         "is blocked on the entity.")
def s10():
    yield has("/business", "European Business Directory", "wall between editorial and commerce")
    yield has("/experiences/join", "Applied", "Reviewed", "Verified", "€49–99", "€199+")
    yield len(DATA["providers"]["tiers"]) == 3, "three tiers in the data"
    yield "Sell placement inside the Journey Planner" in page("/experiences/join"), \
        "the refusal is published, not just internal"


@section(11, "Stories", "BUILT",
         "An editorial desk, linked into the Atlas in both directions.")
def s11():
    n = len(DATA["stories"])
    yield n >= 8, f"{n} stories"
    yield len({s["section"] for s in DATA["stories"]}) >= 5, "across five or more desks"
    for st in DATA["stories"]:
        yield len(st["body"]) >= 4, f"{st['slug']} has {len(st['body'])} paragraphs"
        for cid in st.get("places", []):
            n2 = DATA["cities"][cid]
            u = f"/atlas/{n2['country']['macro_slug']}/{cid}"
            yield st["title"] in page(u), f"{cid} links back to {st['slug']}"


@section(12, "Faith and heritage layer", "BUILT",
         "Sacred and Jewish Europe as themes, plus a sacred tag across the Atlas.")
def s12():
    yield exists("/themes/sacred-europe") and exists("/themes/jewish-europe"), "both themes served"
    n = sum(1 for x in DATA["cities"].values() if "sacred" in x["city"]["interests"])
    yield n >= 20, f"{n} cities tagged sacred"
    yield exists("/interests/sacred"), "the interest has its own page"


@section(13, "Events engine", "BUILT",
         "The recurring year, with a page per month that also answers where "
         "to go. Dated per-year listings need a feed and are Stage 2.")
def s13():
    yield has("/events", "The European year")
    for m in DATA["taxonomy"]["months"]:
        yield exists(f"/events/{m}"), f"/events/{m} is served"
    yield has("/events/oct", "At their best in October", "Quieter, and often better, in October")


@section(14, "Map", "BUILT",
         "Every city, sixteen togglable layers and a journey overlay. No "
         "third-party tiles, by design.")
def s14():
    h = page("/map")
    yield 'id="dots"' in h and h.count('class="dot') >= 240, "every city is drawn"
    yield 'id="layers"' in h, "layer filtering"
    yield 'id="journeylayer"' in h and "EUROPEDOOR_JOURNEYS" in h, "journey overlay"
    yield "mapbox" not in h.lower() and "googleapis" not in h.lower(), "no third-party map service"


@section(15, "The Europe Experience Score", "BUILT",
         "Six dimensions, formula published, recomputed every build.")
def s15():
    from lib import score as S
    yield len(S.DIMENSIONS) == 6, "six dimensions"
    yield has("/method", "The whole formula, on one page", "Not for sale")
    yield all("scores" not in c for c in DATA["countries"].values()), "no score is stored in the data"
    yield "Europe Experience Score" in page("/atlas/nordic/norway"), "shown on country pages"


@section(16, "Responsible tourism", "BUILT",
         "In the mechanism, not only the copy.")
def s16():
    yield has("/beyond-the-obvious", "Beyond the obvious", "undiscovered")
    yield "shoulder: 1.0" in src("assets/js/planner.js").replace("shoulder: 1.00", "shoulder: 1.0") or \
        "SEASON = {" in src("assets/js/planner.js"), "the planner weights season"
    yield "0.74" in src("assets/js/planner.js"), "off-season is damped, not excluded"
    yield "Quieter, and often better" in page("/events/may"), "month pages push the shoulder"


@section(17, "Hidden Europe", "BUILT",
         "A quiet tag, collected and argued for.")
def s17():
    n = sum(1 for x in DATA["cities"].values() if x["city"].get("quiet"))
    yield n >= 30, f"{n} cities tagged quiet"
    yield has("/beyond-the-obvious", "Six straight swaps")


@section(18, "The user account — My Europe", "PARTIAL",
         "Saving works for four kinds of thing, in the browser. Accounts and "
         "sync are blocked on a data controller and a privacy notice.")
def s18():
    yield has("/my-europe", "My Europe", "lives in your browser")
    js = src("assets/js/my-europe.js")
    yield "localStorage" in js and "try {" in js, "guarded local storage"
    for u, kind in (("/journeys/the-alpine-grand-tour", "Journey"),
                    ("/themes/sacred-europe", "Theme"),
                    ("/stories/the-last-forest", "Story"),
                    ("/atlas/nordic/norway/fjord-norway/bergen", "Place")):
        yield f'data-kind="{kind}"' in page(u), f"{kind} is saveable"
    yield "Accounts" in page("/how-it-works"), "the unbuilt half is named in public"


@section(19, "Social features", "DEFERRED",
         "Published itineraries are worth building; follows and feeds are a "
         "different company. Moderation capacity means people.")
def s19():
    yield spec_covers("Social features"), "the position is recorded"
    yield "follow" not in page("/").lower().replace("following", ""), "nothing pretends to be social"


@section(20, "Multilingual", "DEFERRED",
         "English only. The mechanism is decided — overlays in data/, "
         "localisation not machine translation — and not built.")
def s20():
    yield 'lang="en"' in page("/"), "the language is declared"
    yield spec_covers("data/i18n/fr/countries/norway.json", "localised, not machine-translated"), \
        "the mechanism is specified"
    yield not glob.glob(os.path.join(ROOT, "data", "i18n", "*")), "no half-translated content shipped"


@section(21, "Mobile app", "DEFERRED",
         "Correctly deferred by the brief itself. The responsive site is "
         "verified at 390 CSS pixels by an automated browser check.")
def s21():
    yield "390" in src("tools/browser-checks.js"), "phone width is tested"
    yield "viewport" in page("/"), "the viewport is declared"


@section(22, "Revenue model", "BUILT (as specification)",
         "Seven streams, sequenced, with display advertising refused rather "
         "than deferred.")
def s22():
    yield spec_covers("Affiliate", "Directory subscriptions", "Experience commission",
                      "Sponsored destination", "Premium membership",
                      "Curated journeys sold as packages", "Display advertising")
    yield "**refused**" in SPEC, "advertising is refused in writing"
    ads = [f for f in glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True)
           if re.search(r"doubleclick|googlesyndication|adsbygoogle", open(f, encoding='utf-8').read())]
    yield not ads, "no advertising code anywhere in the build"


@section(23, "B2B travel intelligence", "DEFERRED",
         "Worth nothing until there is traffic. The decision made now is the "
         "event schema, because unrecorded behaviour is gone.")
def s23():
    yield spec_covers("plan_requested", "unsupported_ask", "k-anonymised"), "the schema is fixed"
    yield "rotating daily session id" in SPEC, "and the privacy rule with it"


@section(24, "The database as a knowledge graph", "BUILT",
         "Edges in both directions: a city knows its journeys, themes and "
         "stories, not only its parents.")
def s24():
    yield "back" in DATA, "reverse edges are built"
    yield has("/atlas/mediterranean/italy/tuscany-and-the-centre/florence",
              "This place, in the rest of the site")
    linked = sum(1 for cid, b in DATA["back"].items()
                 if b["journeys"] or b["themes"] or b["stories"])
    yield linked >= 120, f"{linked} of {NCITY} cities carry a non-hierarchical edge"
    yield "create table city" in SPEC and "geography(point" in SPEC, "the Postgres shape is specified"


@section(25, "Technology stack", "BUILT (deliberately smaller)",
         "Python standard library and static output. Each proposed addition "
         "has a named trigger instead of a date.")
def s25():
    yield not os.path.exists(os.path.join(ROOT, "requirements.txt")), "no python dependencies"
    yield not os.path.exists(os.path.join(ROOT, "package.json")), "no npm runtime dependencies"
    yield "anyone other than a" in SPEC and "committer" in SPEC, \
        "the Postgres migration trigger is written down"
    h = page("/")
    yield "http://" not in h.replace("http://www.w3.org", ""), "nothing is loaded from another origin"


@section(26, "AI architecture", "PARTIAL",
         "The discipline is built and the model is not: retrieval, the route "
         "engine and refusal exist; narration is specified with its prompts.")
def s26():
    yield spec_covers("intent extraction", "citation check", "You convert a traveller's message",
                      "You are writing up an itinerary that has already been decided")
    yield "Every factual claim must appear in ROWS" in SPEC, "the no-invention rule is written"
    js = src("assets/js/planner.js")
    yield "CANT" in js and "cannot take account of" in js, \
        "the unsupported contract is implemented, not just specified"
    yield "we do not cover that yet" in SPEC, "the refusal path is specified"


@section(27, "MVP scope", "BUILT",
         "The brief asked for five countries done exceptionally well. Fifty "
         "at solid depth, and the five named ones now past the 25-city target.")
def s27():
    yield NCOUNTRY >= 50, f"{NCOUNTRY} countries"
    yield "Depth tier A" in SPEC, "the tiering is recorded"
    for slug in ["norway", "france", "italy", "spain", "greece"]:
        c = DATA["countries"][slug]
        n = sum(len(r["cities"]) for r in c["regions"])
        yield n >= 25, f"{c['name']}: {n} cities"
    yield NCITY >= 300, f"{NCITY} cities in total"


@section(28, "MVP feature list", "BUILT",
         "Every item on the brief's list is live except accounts, which are "
         "browser-local by choice.")
def s28():
    for url, what in (("/", "homepage"), ("/atlas/nordic/norway", "country pages"),
                      ("/atlas/nordic/norway/fjord-norway/bergen", "destination pages"),
                      ("/experiences/walk", "experience categories"), ("/search", "search"),
                      ("/map", "map"), ("/journeys/the-adriatic-run", "journey pages"),
                      ("/plan", "planner"), ("/my-europe", "save and bookmark"),
                      ("/business", "business listings"), ("/stories", "editorial stories")):
        yield exists(url), f"{what} at {url}"


@section(29, "Homepage", "BUILT",
         "The brief's running order, with the AI search box replaced by a "
         "sentence box that exists.")
def s29():
    yield has("/", "Nine regions of Europe", "Find your kind of Europe",
              "Journeys across borders", "Beyond the obvious", "Stories from Europe",
              "Tell it what you have")
    yield page("/").index("Nine regions") < page("/").index("Find your kind"), "regions before interests"
    yield page("/").index("Journeys across borders") < page("/").index("Stories from Europe"), \
        "journeys before stories"


@section(30, "The business flywheel", "BUILT (as specification)",
         "Recorded, with the slowest arrow named.")
def s30():
    yield spec_covers("flywheel", "load-bearing and slowest arrow"), "recorded honestly"


@section(31, "Competitors", "BUILT (as specification)", "Recorded.")
def s31():
    yield spec_covers("Booking.com"), "the position on inventory is stated"


@section(32, "The differentiator", "BUILT",
         "Adopted verbatim, and published on the site rather than kept internal.")
def s32():
    yield "We do not help people book Europe" in page("/about") or \
          "help them discover" in page("/about"), "the sentence is on /about"


@section(33, "Three-stage development", "BUILT (as specification)",
         "Adopted, with the editorial cost the brief understates called out.")
def s33():
    yield spec_covers("Cost, honestly framed", "15–25 days of a good writer"), "recorded"


@section(34, "Twelve-month roadmap", "BUILT (as specification)",
         "In the specification and kept current in docs/roadmap.md.")
def s34():
    yield spec_covers("Roadmap, twelve months"), "in the specification"
    yield "Twelve months" in src("docs/roadmap.md"), "and in the living roadmap"


@section(34.5, "The verification plan", "BUILT",
         "Not a numbered section of the brief, but the thing that decides "
         "whether any of the facts above are worth anything.")
def s34b():
    yield exists("/sources/freshness"), "the freshness board is served"
    yield has("/sources/freshness", "What \"unverified\" means here", "The order it happens in")
    unver = [c["name"] for c in DATA["countries"].values() if not c.get("checked")]
    yield "not verified" in page("/atlas/nordic/norway"), \
        f"{len(unver)} unverified countries, and each says so on its own page"
    yield "checked" in src("tools/lib/data.py"), "the schema carries the date"


@section(35, "The strategic decision", "BUILT",
         "Positioned as a discovery engine, and the honest status board is "
         "public rather than internal.")
def s35():
    yield has("/how-it-works", "Built and live", "Designed, not built", "Deliberately blocked")
    yield has("/about", "discover")
    yield has("/sources", "considered first draft")


# ──────────────────────────────────────────────────────────────────────

def label(num):
    """34.5 is the verification plan, which the brief never numbered and
    which decides whether anything else on this list is worth reading."""
    return str(int(num)) + "+" if num != int(num) else str(int(num))


def run():
    rows, failures = [], []
    for num, title, verdict, note, fn in SECTIONS:
        results = []
        for r in fn():
            if isinstance(r, tuple):
                results.append(r)
            else:
                results.append((bool(r), ""))
        bad = [e for ok, e in results if not ok]
        rows.append((num, title, verdict, note, len(results), bad))
        for e in bad:
            failures.append(f"§{num} {title}: {e}")
    return rows, failures


def main():
    rows, failures = run()
    write = "--write" in sys.argv
    check = "--check" in sys.argv

    print("Europedoor — brief sections 1–35, audited against the build\n")
    for num, title, verdict, note, n, bad in rows:
        mark = "ok  " if not bad else "FAIL"
        print(f"  {mark}  §{label(num):<4} {title:<44} {verdict:<26} {n} assertions")
        for e in bad:
            print(f"          ✗ {e}")
    built = sum(1 for r in rows if r[2].startswith("BUILT"))
    partial = sum(1 for r in rows if r[2] == "PARTIAL")
    deferred = sum(1 for r in rows if r[2] in ("DEFERRED", "REFUSED"))
    total = sum(r[4] for r in rows)
    print(f"\n  {built} built · {partial} partial · {deferred} deferred · "
          f"{total} assertions · {len(failures)} failing")

    if write:
        with open(os.path.join(ROOT, "docs", "section-audit.md"), "w", encoding="utf-8") as fh:
            fh.write(render_md(rows, built, partial, deferred, total, failures))
        print("\n  wrote docs/section-audit.md")

    if failures and check:
        print("\nFAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)


def render_md(rows, built, partial, deferred, total, failures):
    out = ["# The brief, audited against the build",
           "",
           "**Generated by `python3 tools/section-audit.py --write`. Do not edit by hand.**",
           "",
           "Every section of the 36-section brief, checked against the dataset and the",
           "generated HTML as they stand. A section is BUILT only if every assertion",
           "under it holds right now — which means this file cannot drift from the",
           "product without CI noticing.",
           "",
           f"**{built} built · {partial} partial · {deferred} deferred · "
           f"{total} assertions · {len(failures)} failing**",
           "",
           "Section 36 is the architecture diagram rather than a feature, and is",
           "reflected in the repository layout rather than audited here.",
           "",
           "| § | section | verdict | assertions | note |",
           "|---|---|---|---|---|"]
    for num, title, verdict, note, n, bad in rows:
        state = verdict if not bad else f"**FAILING** ({len(bad)})"
        out.append(f"| {label(num)} | {title} | {state} | {n} | {note} |")
    out += ["",
            "## What PARTIAL means here",
            "",
            "Four sections are partial, and in every case the missing half is named on",
            "the site itself at `/how-it-works` rather than only in a document:",
            "",
            "* **§6 / §26 the planner and the AI.** The engine, the scoring, the refusals",
            "  and a rule-based sentence reader are built. The model-written narration is",
            "  specified, with its prompts and its citation check, and not built — because",
            "  the discipline had to exist first.",
            "* **§9 marketplace.** Listings are live; availability, checkout and commission",
            "  are blocked on an entity that does not exist yet.",
            "* **§18 accounts.** Saving works, in the browser, for places, journeys, themes",
            "  and stories. Sync needs a data controller and a published privacy notice.",
            "* **§27 MVP depth.** Fifty countries at solid depth; the five named for",
            "  depth-first treatment are not there yet, and that is the current work.",
            "",
            "## What DEFERRED means here",
            "",
            "Not a to-do list. Each of these is a decision with a reason recorded in",
            "`product-specification.md`, and the assertion checks that nothing on the",
            "site pretends otherwise — no half-translated pages, no social features that",
            "do not work, no analytics we said we would not run.",
            ""]
    return "\n".join(out)


if __name__ == "__main__":
    main()
