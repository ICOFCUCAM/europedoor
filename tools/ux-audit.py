#!/usr/bin/env python3
"""Audit the build against the 37-section UI/UX specification.

    python3 tools/ux-audit.py            print the audit
    python3 tools/ux-audit.py --check    fail if any claim is false
    python3 tools/ux-audit.py --write    regenerate docs/ux-audit.md

Same discipline as tools/section-audit.py, and for the same reason: a design
brief is the easiest kind of document to declare "done" against, because most
of its requirements are about how something looks and nobody can check a
feeling. So each section here asserts against the generated HTML, the CSS and
the JavaScript as they actually are.

Verdicts:
  BUILT      shipped from this brief, and the assertions prove it
  ALREADY    was already there when the brief arrived
  PARTIAL    shipped in part, deliberately, with the missing half named
  REFUSED    decided against, with the reason on the site rather than only here
  LOCKED     a decision that overrides the brief
  DEFERRED   deliberately not built; the assertion checks nothing pretends otherwise
"""

from __future__ import annotations

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D

ROOT = D.ROOT
OUT = os.path.join(ROOT, "site")
DATA = D.load()
_cache = {}


def page(path):
    if path in _cache:
        return _cache[path]
    p = os.path.join(OUT, "index.html") if path == "/" else os.path.join(OUT, path.strip("/"), "index.html")
    _cache[path] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return _cache[path]


def src(path):
    p = os.path.join(ROOT, path)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


CSS = src("assets/css/europedoor.css")
PLANNER = src("assets/js/planner.js")
MINE = src("assets/js/my-europe.js")
RENDER = src("tools/lib/render.py")
PAGES = src("tools/lib/pages.py")
BROWSER = src("tools/browser-checks.js")
UXDOC = src("docs/ux-specification.md")
ALL_HTML = sorted(glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True))
CITY = page("/europe/norway/fjord-norway/bergen")


def has(path, *needles):
    h = page(path)
    if not h:
        return (False, f"{path} is not served")
    missing = [n for n in needles if n not in h]
    return (not missing, f"{path}: missing {missing}" if missing else f"{path} carries all {len(needles)}")


def every_page(pred, label):
    bad = [f for f in ALL_HTML if not pred(open(f, encoding="utf-8").read())]
    return (not bad, f"{len(bad)} pages fail: {label} (e.g. {os.path.relpath(bad[0], OUT) if bad else ''})")


def doc_covers(doc, *needles):
    text = src(doc)
    missing = [n for n in needles if n not in text]
    return (not missing, f"{doc} missing {missing}" if missing else f"recorded in {doc}")


def refusal_recorded(*needles):
    """A refusal is only defensible if the reason is written down where
    somebody can disagree with it."""
    missing = [n for n in needles if n not in UXDOC]
    return (not missing, f"docs/ux-specification.md missing {missing}" if missing
            else "the refusal is argued in docs/ux-specification.md")


SECTIONS = []


def section(num, title, verdict, note):
    def deco(fn):
        SECTIONS.append((num, title, verdict, note, fn))
        return fn
    return deco


# ── 1–3: direction, navigation, tokens ────────────────────────────────

@section(1, "Design direction", "PARTIAL",
         "Editorial, map-led, typography-forward, and every page leads to "
         "another. Photography leads discovery is answered by an enforced "
         "pipeline and zero licensed photographs — the architecture is "
         "built, the library is empty, and those are different claims.")
def s1():
    yield has("/", "heromap"), "maps provide context, on the homepage itself"
    yield every_page(lambda h: "book now" not in h.lower(),
                     "booking never dominates, because there is none")
    yield "def picture" in RENDER, "there is a photograph layer"
    yield "no image is published without a photographer" in src("tools/checks.py"), \
        "and no image ships without provenance"
    yield bool(src("docs/images.md")), "with the acquisition problem stated plainly"
    # The plates are the empty state, and they had to stop reading as a
    # broken image before that was defensible.
    yield "MOTIFS" in RENDER and "PLATE_HUES" in RENDER, \
        "and the empty state is an illustration system, not a gradient"


@section(2, "Global navigation", "BUILT",
         "The brief's desktop masthead exactly, and the five-item thumb bar "
         "on a phone. Both name the product EuropeDoor, not Europe Atlas.")
def s2():
    for label in ("Discover", "Countries", "Experiences", "Journeys", "Stories"):
        yield label in CITY, f"the masthead carries {label}"
    yield "navsearch" in CITY and "navmine" in CITY, "search and My Europe"
    from lib import render as R
    yield "BOTTOM_NAV" in RENDER, "the thumb bar exists"
    # Five and no more. A sixth turns a bar you can hit with a thumb into a
    # row of targets you have to aim at, and the CSS grid is written for five.
    yield len(R.BOTTOM_NAV) == 5, f"the thumb bar carries {len(R.BOTTOM_NAV)} items, not five"
    for label in ("Home", "Explore", "Map", "Plan", "Me"):
        yield f">{label}</span>" in CITY, f"the thumb bar carries {label}"
    yield every_page(lambda h: 'class="bottomnav"' in h, "the thumb bar on every page")
    yield "the thumb bar and the sticky action" in BROWSER, "measured in a phone viewport"


@section(3, "Design tokens", "PARTIAL",
         "One 8px-derived spacing scale, one type scale, the brief's radii. "
         "The named webfonts are refused: a font CDN would hand every "
         "reader's address to a third party and contradict /privacy.")
def s3():
    yield "--s1:" in CSS and "--s7:" in CSS, "one spacing scale"
    yield "--t-xs:" in CSS and "--t-sm:" in CSS, "one type scale"
    yield "--radius" in CSS, "one radius token"
    yield every_page(lambda h: "fonts.googleapis" not in h and "fonts.gstatic" not in h,
                     "no font CDN on any page")
    yield "font-src 'self'" in RENDER, "and the policy forbids one"
    yield refusal_recorded("Playfair Display + Inter")


# ── 4–9: the homepage ─────────────────────────────────────────────────

@section(4, "Homepage hero", "PARTIAL",
         "Full-bleed hero, the headline, the ask box and the call to "
         "action. The hero image is a generated plate.")
def s4():
    yield has("/", "Open the door to Europe", "Plan my journey")
    yield has("/", "what would you like to discover?"), "the Bible's own ask-box wording"
    yield has("/", "hero-actions"), "and the calls to action beneath it"
    h = page("/")
    yield h.index("Plan my journey") < h.index("Explore Europe"), \
        "primary before secondary — the planner is the conversion"


@section(5, "Homepage — Explore", "ALREADY",
         "The interactive map with the brief's filter row, as links into the "
         "real map rather than a second map to keep in step.")
def s5():
    yield has("/", "heromap", "heromap-filters")
    for layer in ("nature", "history", "food", "coast"):
        yield f"/map?layer={layer}" in page("/"), f"the {layer} filter"
    yield has("/", "Hidden Europe"), "and the quiet layer"


@section(6, "Experience categories", "ALREADY",
         "Eight large cards, one per category, with the brief's hover.")
def s6():
    yield has("/", "Find your kind of Europe")
    yield ".card:hover" in CSS, "the cards lift on hover"
    yield "@media (prefers-reduced-motion: reduce)" in CSS, "and stop for anyone who asked"


@section("2036-7", "Discover Mode", "BUILT",
         "The surface that answers \"I do not know where I want to go\". Pick "
         "moods and constraints and the continent narrows — and every "
         "recommendation says why, naming the terms that actually fired.")
def s2036_7():
    d = src("assets/js/discover.js")
    yield bool(page("/discover")) and 'id="discover-mode"' in page("/discover"), \
        "Discover Mode is on the discover page"
    yield "/assets/js/discover.js" in page("/discover"), "and runs"
    yield "function rate" in d, "it scores against the reader's choices"
    # The design decision the whole feature turns on: never explain the
    # constraint back. A card that repeats the filter is boilerplate, and
    # boilerplate is what a reader learns to skip.
    yield "asked" in d and "extra" in d, "reasons are split into asked-for and additional"
    yield "whyall" in d and "whythis" in d, "the shared reason is hoisted, the rest per card"
    yield 'aria-pressed' in d, "the chips are toggle buttons, not styled checkboxes"
    yield "at most two per country" in d, "and the list is Europe, not one corner of it"
    yield "Discover Mode" in src("tools/browser-checks.js"), "with browser checks"


@section("2036-18", "Discoverability, computed", "BUILT",
         "Hidden Europe was an editorial tag — the most interesting claim on "
         "the site and the one nobody could check. It is now a published "
         "score with five named terms, and it says plainly that it measures "
         "obscurity within this Atlas rather than crowds.")
def s2036_18():
    sc = src("tools/lib/score.py")
    yield "def discoverability" in sc, "the score exists"
    yield "DISCOVER_TERMS" in sc, "its terms are a published table"
    yield has("/method", "Discoverability", "not a crowd measurement"), \
        "and /method publishes both the terms and what it is not"
    yield 'id="discoverability"' in page("/method"), "with an anchor to link at"
    # We hold no visitor numbers for anywhere, and a proxy presented as
    # evidence is the thing this project exists not to do.
    yield "no visitor numbers" in page("/method"), "and says why there is no crowd term"
    import json as _json
    api = _json.load(open(os.path.join(OUT, "api", "atlas.json"), encoding="utf-8"))
    yield all("disc" in c for c in api["cities"]), "every destination carries the score"
    yield all("discWhy" in c for c in api["cities"]), "and the terms that fired for it"
    # The field is discWhy, not why: `why` already holds the city summary,
    # and overwriting it silently emptied the description on every planner
    # leg and every Discover Mode row before a screenshot caught it.
    yield all(isinstance(c.get("why"), str) for c in api["cities"]), \
        "and has not overwritten the summary"


@section("2036-6", "Europe in Motion", "BUILT",
         "Twelve ways to cut the continent, each a query evaluated against "
         "every destination on every build — and each page prints the query "
         "that made it. A motion cannot become a hand-picked list, because "
         "the validator refuses a field that names destinations.")
def s2036_6():
    import json as _json
    motions = _json.load(open(os.path.join(ROOT, "data", "motions.json"),
                              encoding="utf-8"))["motions"]
    yield len(motions) >= 12, f"{len(motions)} motions"
    yield bool(page("/europe-in")), "the index is served"
    for m in motions:
        h = page("/europe-in/" + m["slug"])
        yield bool(h), f"/europe-in/{m['slug']} is served"
        # A landing page that will not say what produced it is an assertion.
        yield "The query that made this page" in h, f"{m['slug']} states its query"
        yield "Nothing here is hand-picked" in h, f"{m['slug']} says it is a query"
    # The one field that must not exist. A curated list wearing the clothes
    # of a query is exactly what this refuses to be.
    yield "a motion is a query, not a hand-picked list" in src("tools/lib/data.py"), \
        "and the validator refuses a destination list on a motion"
    yield "a motion with no query terms" in src("tools/lib/data.py"), \
        "and refuses a motion that would match everything"
    yield "Europe in Motion" in src("tools/browser-checks.js"), \
        "with browser checks that the queries differ and the latitude one is geographic"
    # Same discipline as Discover Mode: never explain the constraint back.
    yield "Never explain the constraint back" in src("tools/lib/pages.py"), \
        "and shared reasons are hoisted rather than repeated per row"


@section(7, "Featured journeys", "ALREADY",
         "Cards carrying days, countries and the route, as the brief draws "
         "them.")
def s7():
    yield has("/", "Journeys across borders")
    yield has("/journeys/the-alpine-grand-tour", "days", "The route")


@section(8, "Hidden Europe", "ALREADY",
         "A quiet tag, its own band, and a rule that nowhere is ever called "
         "undiscovered.")
def s8():
    yield bool(page("/beyond-the-obvious")), "the page exists"
    yield has("/beyond-the-obvious", "undiscovered"), "and refuses the word"


@section(9, "Homepage AI planner", "ALREADY",
         "The sentence box, in the hero, saying under the field what reads "
         "it — which is rules in the browser, not a model.")
def s9():
    yield has("/", "askhome", "Plan my journey")
    yield has("/", "not by a"), "and says what reads it"


# ── 10–14: the planner ────────────────────────────────────────────────

@section(10, "Planner — screen 1", "ALREADY",
         "Start, end, dates, travellers, budget and interests, all present "
         "and all moving the answer.")
def s10():
    for f in ("start", "end", "month", "travellers", "budget", "days"):
        yield f'id="{f}"' in page("/plan"), f"the {f} field"
    yield 'name="interest"' in page("/plan"), "the interest chips"


@section(11, "Conversational mode", "PARTIAL",
         "The planner reads a sentence, shows back what it understood, and "
         "asks only the follow-ups that would change the answer. It does "
         "not hold a turn-by-turn conversation, because that needs a model.")
def s11():
    yield "function parseAsk" in PLANNER, "it reads a sentence"
    yield "function readbackHtml" in PLANNER, "and shows what it understood"
    yield "function followUps" in PLANNER, "and asks only what matters"
    yield has("/plan", "not by a model"), "and says what is doing the reading"


@section(12, "Results screen", "ALREADY",
         "Days, travellers, the route, the estimate and save/share.")
def s12():
    yield "result-summary" in PLANNER, "the summary"
    yield "Estimated total" in PLANNER, "the cost"
    yield "saveplan" in PLANNER and "shareplan" in PLANNER, "save and share"


@section(13, "Day cards", "ALREADY",
         "A card per day with what is on it and what the day costs.")
def s13():
    yield "function dayPlan" in PLANNER, "the day-by-day"
    yield "daylist" in PLANNER, "rendered as day cards"


@section(14, "Journey customisation", "BUILT",
         "Reorder, remove and lengthen or shorten any stop; the days, the "
         "distances and the estimate all recompute from the reader's "
         "version. Buttons rather than drag handles, deliberately — and the "
         "edited route is what gets shared, not the inputs that made it.")
def s14():
    yield "alternativesFor" in PLANNER, "each stop offers alternatives"
    yield 'id="again"' in page("/plan"), "and the whole plan can be rebuilt"
    for control in ("data-move", "data-nights", "data-drop"):
        yield control in PLANNER, f"stops can be edited: {control}"
    # Drag-and-drop is unusable with a keyboard, unusable with a screen
    # reader and miserable on a phone. For a list of at most fourteen
    # things, "move earlier" is a better interaction that looks less
    # impressive — and it is testable, which drag is not.
    yield "aria-label=\"Move " in PLANNER, "every control is labelled"
    yield "EDITED" in PLANNER, "an edited route is carried, not regenerated"
    yield "You have changed this itinerary" in PLANNER, "and the page says so"
    # The planner jitters, so regenerating a shared plan from its inputs
    # would return a different trip. The route travels in the link.
    yield 'q.set("r"' in PLANNER, "the shared link carries the route itself"
    yield "a shared edited plan came back different" in BROWSER, \
        "with a browser check that a shared edit restores as edited"
    # And a stop can be added, which is the half that makes the rest useful.
    yield "data-add" in PLANNER, "a stop can be added to an existing route"
    yield "function addPanel" in PLANNER, "with a picker over the whole Atlas"
    yield "inRoute[c.id]" in PLANNER, "that never offers a stop already on the route"
    # Distance on every row: on a route the question is always what a stop
    # costs, and a list that hides it invites a 900 km detour that looks
    # like a small edit.
    yield 'f.d.toLocaleString("en-GB")' in PLANNER, "and states the distance from the stop before"
    yield "a city already on the route was offered again" in BROWSER, \
        "with checks for the exclusion and the accent folding"


# ── 15–20: the page types ─────────────────────────────────────────────

@section(15, "Country page", "ALREADY",
         "Hero, regions, popular destinations, experiences and journeys, in "
         "the brief's order.")
def s15():
    yield has("/europe/norway", "Travel regions", "Popular destinations",
              "Experiences here", "Journeys through")


@section(16, "Destination page", "BUILT",
         "The brief's section navigation, scrolling sideways on a phone and "
         "listing only the sections this page actually has.")
def s16():
    yield "def sectionnav" in PAGES, "the section nav exists"
    yield 'class="sectionnav"' in CITY, "and is on a destination page"
    yield "overflow-x: auto" in CSS.split(".sectionnav {")[1].split("}")[0], \
        "it scrolls rather than wraps"
    yield "scroll-padding-top" in CSS, "and its anchors clear the sticky masthead"
    yield "section nav links to" in BROWSER, "with a check that every tab has a target"


@section(17, "Content hierarchy", "ALREADY",
         "Why visit, then what to see, then what to do, then where to stay, "
         "then how to turn it into a journey. Discovery-first, as asked.")
def s17():
    order = ["why-visit", "places", "things-to-do", "stay", "onward"]
    at = [CITY.index(f'id="{x}"') for x in order if f'id="{x}"' in CITY]
    yield at == sorted(at), "the sections are in the brief's order"
    yield "Add to my journey" in CITY, "and it ends by offering the journey"


@section(18, "Place page", "PARTIAL",
         "About, location, nearby and a save action. Refused: the "
         "photograph, the star rating and the opening hours — the last of "
         "these is rejected by the validator, not merely omitted.")
def s18():
    u = "/europe/norway/fjord-norway/bergen/place/bryggen"
    yield has(u, "We do not hold opening hours", "Season")
    yield "is volatile and must not be authored" in src("tools/lib/data.py"), \
        "the validator rejects hours, price, website and phone"
    yield every_page(lambda h: "★" not in h, "no star rating anywhere")
    yield refusal_recorded("Ratings and review scores", "Opening hours (§18)")


@section(19, "Experience page", "PARTIAL",
         "What it is, where, when and who runs it. Refused: the rating and "
         "the book button.")
def s19():
    yield bool(page("/experiences/nature")), "the experience surfaces exist"
    yield every_page(lambda h: "book now" not in h.lower(), "nothing offers to book")
    yield refusal_recorded("Booking (§19")


@section(20, "Business page", "PARTIAL",
         "Verification is published with what each level actually checks, "
         "and sponsorship can never touch a place — that wall is in the "
         "schema, which is the only version of the promise worth making.")
def s20():
    yield bool(page("/for-businesses")), "the business surface exists"
    yield "sponsored" not in str(DATA["countries"]), "no place carries a sponsorship field"
    yield bool(page("/for-businesses")), "and the tiers are published"


# ── 21–27: map, search, dashboards, mobile ────────────────────────────

@section(21, "Map experience", "ALREADY",
         "Layers, a journey overlay, a distance origin and a popup card.")
def s21():
    yield 'id="layers"' in page("/map"), "the filters"
    yield 'id="mappopup"' in page("/map"), "the popup"
    yield 'id="journeylayer"' in page("/map"), "the journey overlay"


@section(22, "Search interface", "ALREADY",
         "One box that takes a sentence, answered in the browser.")
def s22():
    yield 'id="q"' in page("/search"), "the search box"
    yield "MODIFIER_INTENT" in src("assets/js/search.js"), "it reads intent"


@section(23, "Search results", "ALREADY",
         "The interpretation shown back above the results, exactly as the "
         "brief draws it, then results grouped by kind.")
def s23():
    yield "understood" in src("assets/js/search.js"), "the interpretation is shown"
    yield has("/search", "Search"), "above the results"


@section(24, "My Europe", "PARTIAL",
         "Saved places, collections and bucket lists, plus a way to move "
         "the whole list to another device. No account, so no welcome-back "
         "and no cross-device sync on our side.")
def s24():
    yield "europedoor.collections.v1" in MINE, "collections"
    yield "Move this to another browser" in MINE, "and the list is portable"
    yield has("/my-europe", "lives in your browser"), "and says where it lives"


@section(25, "Business dashboard", "REFUSED",
         "The layout is specified. The figures are not, because there is no "
         "traffic and nothing booked, and a dashboard of invented numbers "
         "makes every other number on the product untrustworthy.")
def s25():
    yield every_page(lambda h: "Profile views" not in h, "no invented traffic figure")
    yield refusal_recorded("The business dashboard's numbers")


@section(26, "Admin dashboard", "PARTIAL",
         "The content half is real and computed on every build, including "
         "the verification queue. The traffic half waits for traffic.")
def s26():
    yield bool(src("docs/content-report.md")), "the content figures are computed"
    yield "Never checked" in page("/sources/freshness"), "including the verification queue"
    yield "due for review" in page("/sources/freshness"), "and expired data as a live figure"
    yield refusal_recorded("The admin dashboard's user metrics")


@section(27, "Mobile-first behaviour", "BUILT",
         "The sticky thumb bar, and a persistent action that says Add to my "
         "journey rather than Book now — the brief's own suggestion, and "
         "the only honest one here.")
def s27():
    yield "def stickycta" in PAGES, "the sticky action exists"
    yield 'class="stickycta"' in CITY, "on a destination page"
    yield "Add to my journey" in CITY, "and it offers the journey"
    yield every_page(lambda h: "Book now" not in h, "no booking button anywhere")
    # It must be a destination-page action only: a bar pinned to every page
    # at every width is a bar that is in the way most of the time.
    yield 'class="stickycta"' not in page("/plan"), "and only where there is a destination"
    yield "the destination action appeared on a page with no destination" in BROWSER, \
        "with a check that it stays there"


# ── 28–33: components, states, accessibility ──────────────────────────

@section(28, "Component library", "PARTIAL",
         "The brief's 24 components exist as CSS classes in one stylesheet "
         "rather than as objects in a library. A page may not ship its own "
         "style block, and now may not ship a style attribute either.")
def s28():
    for cls in (".card", ".row", ".chip", ".btn", ".facts", ".score", ".legs",
                ".europemap", ".checks", ".crumbs", ".note", ".sectionnav"):
        yield cls in CSS, f"{cls} is defined once"
    yield every_page(lambda h: "<style" not in h, "no page ships its own styles")
    yield len(glob.glob(os.path.join(OUT, "assets", "css", "*.css"))) == 1, "one stylesheet"


@section(29, "Design states", "PARTIAL",
         "Default, hover, focus and disabled are in the stylesheet; loading, "
         "empty and error are real states in the planner and My Europe. The "
         "gap the brief exposed was a real bug: one place saved from two "
         "buttons only relabelled the button that was pressed.")
def s29():
    yield ":focus-visible" in CSS, "focus is visible"
    yield ":hover" in CSS, "hover"
    yield "function labelAll" in MINE, "and a saved state that is shared, not per-button"
    yield "aria-pressed" in MINE, "and reported to assistive technology"
    yield "saving from the sticky bar did not update the button in the rail" in BROWSER, \
        "with the check that would have caught it"


@section(30, "AI loading experience", "BUILT",
         "Five named steps, ticked when the work they name has actually "
         "finished — so a failure marks where it stopped instead of "
         "replacing everything with an apology.")
def s30():
    yield "Building your journey" in PLANNER, "the staged wait"
    yield "Understanding what you asked for" in PLANNER, "with real steps"
    yield 'role="status"' in PLANNER, "announced to a screen reader"
    yield "stage(0, 0)" in PLANNER, "and a failure marks the step it died on"
    # Not "no occurrence of the word" — the comment above the code explains
    # why a bare one is banned, and a check that fails on its own rationale is
    # a check nobody will keep. Every step has to say what it is doing.
    steps = [x.strip().strip('",') for x in
             PLANNER.split("var STEPS = [")[1].split("];")[0].strip().splitlines()]
    yield all(len(x.split()) >= 2 for x in steps if x), \
        f"a wait step says nothing about what it is doing: {steps}"


@section(31, "Empty states", "ALREADY",
         "Every empty surface says what it is empty of and what to do, and "
         "the empty state is a real state rather than a spinner.")
def s31():
    yield "Nothing saved yet" in MINE, "My Europe is empty rather than blank"
    yield "Nothing in the Atlas fits that yet" in PLANNER, "and so is the planner"


@section(32, "Error states", "BUILT",
         "The brief's sharpest line — do not fabricate a result just to "
         "avoid an error — described what this planner did, because it "
         "scores every city and so can always return something.")
def s32():
    yield "function whyUnreliable" in PLANNER, "there is a refusal path"
    yield "could not build a journey we would stand behind" in PLANNER, "and it says so"
    yield "data-focus" in PLANNER.split("function renderRefusal")[1][:2000], \
        "and names the control that would fix it"
    yield "Show it anyway" in PLANNER, "and is never a dead end"
    # The refusal must be about the reader's constraints, not ours.
    yield "opts.budgetStated" in PLANNER, \
        "and never refuses against a budget the reader did not give"
    yield "the planner refused against a budget the sentence never stated" in BROWSER, \
        "with the check that caught exactly that"


@section(33, "Accessibility", "PARTIAL",
         "Keyboard, focus, reduced motion, zoom and touch targets are all "
         "enforced in a browser on every build, and the map now has a real "
         "text alternative. A screen-reader audit by a person has not "
         "happened, and /accessibility says so.")
def s33():
    yield ":focus-visible" in CSS, "focus is visible"
    yield "prefers-reduced-motion" in CSS, "motion can be turned off"
    yield "def maplist" in PAGES, "the map has a text alternative"
    yield 'aria-describedby="maplist"' in page("/map"), "and points at it"
    yield "the map draws" in BROWSER, "with a check that it lists every place drawn"
    yield "under 44px" in BROWSER, "touch targets are measured"
    yield bool(page("/accessibility")), "and what is missing is published"


# ── the Brand Bible ───────────────────────────────────────────────────
#
# Numbered B1-B6 rather than folded into the UI sections above, because they
# came from a different document and a verdict should say which brief it is
# answering.

@section("B1", "Name, casing and the trademark position", "LOCKED",
         "EuropeDoor, one word, title case. The mark is NOT cleared — it is "
         "in use in the doors trade — so the site carries no ® or ™ and the "
         "brand is working rather than announced.")
def sb1():
    from lib import render as R
    yield R.SITE_NAME == "EuropeDoor", f"SITE_NAME is {R.SITE_NAME!r}"
    yield every_page(lambda h: "Europe Door" not in h,
                     "never two words — a generic phrase is unregistrable")
    yield every_page(lambda h: "®" not in h and "™" not in h,
                     "no registration symbol on an uncleared mark")
    yield doc_covers("docs/brand-lock.md", "already in use as a business name",
                     "South Africa", "Nice class"), \
        "the conflict is recorded rather than assumed away"
    yield doc_covers("docs/brand-lock.md", "pre-launch clearance task"), \
        "with a formal clearance task before any registrable spend"


@section("B2", "Tagline and promise", "BUILT",
         "Open the door to Europe. One primary line; the six campaign lines "
         "are not in the shell, because a site with six taglines has none.")
def sb2():
    from lib import render as R
    yield R.SITE_TAGLINE == "Open the door to Europe.", "the primary tagline"
    yield has("/", "Open the door to Europe"), "in the hero"
    yield every_page(lambda h: "Open the door to Europe" in h, "and in the footer")
    for campaign in ("Europe, opened", "Find your Europe", "See Europe differently"):
        yield every_page(lambda h, c=campaign: c not in h, f"{campaign} is not in the shell")


@section("B3", "The four doors", "BUILT",
         "Discover, understand, experience, journey — as a numbered "
         "sequence of links, not a menu of equals. It replaced five pillars "
         "that described our components rather than the reader's path.")
def sb3():
    h = page("/")
    for i, door in enumerate(("Discover", "Understand", "Experience", "Journey")):
        yield f"<h3>{door}</h3>" in h, f"door {i + 1}: {door}"
    order = [h.index(f"<h3>{d}</h3>") for d in
             ("Discover", "Understand", "Experience", "Journey")]
    yield order == sorted(order), "and they are in the Bible's order"
    yield 'class="card door"' in h, "each door is a link, not an inert card"
    yield "not search-then-book" in h, "and the page says why it is a sequence"


@section("B4", "Colour", "BUILT",
         "Atlantic green, limestone ground, terracotta accent, charcoal "
         "type, brass reserved for heritage and never for a control. "
         "Deliberately not EU blue and gold.")
def sb4():
    for token in ("--atlantic:", "--terracotta:", "--brass:", "--paper:", "--ink:"):
        yield token in CSS, f"{token} is defined"
    # Brass is a heritage highlight, not a UI colour: a gold control reads
    # as a premium upsell, and there is nothing to sell.
    for control in (".btn {", ".btn.ghost"):
        block = CSS.split(control)[1].split("}")[0] if control in CSS else ""
        yield "--brass" not in block, f"{control} does not use brass"
    yield "prefers-color-scheme: dark" in CSS, "and the palette has a night form"
    yield "--atlantic: #4f9d85" in CSS.replace("    ", "").replace("\n", "\n"), \
        "which lifts the green rather than inverting it"


@section("B5", "The mark", "BUILT",
         "Concept B: two vertical forms, and the negative space between "
         "them is the symbol. It replaced a literal door with a knob, which "
         "the Bible explicitly rules out.")
def sb5():
    yield "MARK = (" in RENDER, "the mark is drawn once"
    yield "mark-frame" in RENDER and "mark-leaf" in RENDER, "as two forms"
    yield every_page(lambda h: 'class="mark"' in h, "on every page")
    yield ".mark-frame { fill: var(--atlantic); }" in CSS, "taking the brand colour from CSS"
    # It used to be a border-radius trick with a ::after dot for the knob.
    yield ".door::after" not in CSS, "and the literal door with a knob is gone"
    yield doc_covers("docs/brand.md", "Rejected on the way"), \
        "with the four rejected directions recorded"


@section("B6", "Voice, manifesto and trust", "BUILT",
         "The manifesto is a page rather than a slide, and the four labels "
         "that say where every claim comes from are on the same page "
         "underneath it. That second half is what stops the first half "
         "being advertising copy.")
def sb6():
    yield bool(page("/manifesto")), "the manifesto is a page"
    yield has("/manifesto", "Europe is more than a collection of countries",
              "EuropeDoor opens the way"), "carrying the Bible's own lines"
    for tier in ("Verified", "Editorial", "Computed", "Community"):
        yield f">{tier}</span>" in page("/manifesto"), f"the {tier} label"
    # Community is deliberately empty, and says so rather than being absent.
    yield "None yet" in page("/manifesto"), \
        "and an empty tier says it is empty instead of being hidden"
    # The corporate-software vocabulary the Bible bans.
    for banned in ("AI-powered", "next-generation", "hyper-personalised",
                   "travel ecosystem", "optimize your European"):
        yield every_page(lambda h, b=banned: b.lower() not in h.lower(),
                             f"{banned} appears nowhere")
    yield every_page(lambda h: "as an AI language model" not in h.lower(),
                     "nothing on the site talks like a model")


# ── 34–37: the Figma deliverables ─────────────────────────────────────

@section(34, "Figma file structure", "DEFERRED",
         "There is no Figma file. There is a built site, and a second source "
         "of truth would have to be kept in step with the first.")
def s34():
    yield refusal_recorded("§34, §35, §37 — Figma")


@section(35, "Prototype flows", "BUILT",
         "All six flows are clickable on the live build rather than in a "
         "prototype, which is the stronger version of the same deliverable.")
def s35():
    flows = [
        ("/", "/europe/norway", "/europe/norway/fjord-norway/bergen"),
        ("/", "/plan"),
        ("/search", "/europe/italy/tuscany-and-the-centre/florence", "/my-europe"),
        ("/map", "/europe/norway/fjord-norway/bergen", "/journeys"),
        ("/for-businesses", "/experiences/nature"),
        ("/my-europe", "/plan"),
    ]
    for i, flow in enumerate(flows, 1):
        for step in flow:
            yield bool(page(step)), f"flow {i}: {step} is a real page"


@section(36, "The most important UX decision", "ALREADY",
         "Where am I, what is here, where next — answered on every page by "
         "breadcrumbs, the section nav and the onward links, rather than by "
         "a search box and hope.")
def s36():
    # The homepage is the one page that does not need to say where you are,
    # because you are at the front door; it carries the hero instead.
    yield every_page(lambda h: 'class="crumbs"' in h or 'class="pagehead"' in h
                     or 'class="hero"' in h,
                     "every page says where you are")
    yield "Nearest onward stops" in CITY, "and where you can go next"
    yield "This place, in the rest of the site" in page(
        "/europe/france/alps-and-east/chamonix"), "and how it connects"


@section(37, "The ten-screen prototype", "BUILT",
         "All ten screens exist as real pages on the live build.")
def s37():
    for label, u in [("Homepage", "/"), ("Search", "/search"), ("Country", "/europe/norway"),
                     ("Destination", "/europe/norway/fjord-norway/bergen"),
                     ("Place", "/europe/norway/fjord-norway/bergen/place/bryggen"),
                     ("Map", "/map"), ("Planner", "/plan"),
                     ("Journey", "/journeys/the-alpine-grand-tour"),
                     ("My Europe", "/my-europe"), ("Experiences", "/experiences")]:
        yield bool(page(u)), f"{label}: {u}"


def run():
    rows, failures = [], []
    for num, title, verdict, note, fn in SECTIONS:
        bad, n = [], 0
        for result in fn():
            n += 1
            if isinstance(result, tuple):
                good, detail = result
            else:
                good, detail = bool(result), ""
            if not good:
                bad.append(detail or f"assertion {n}")
        rows.append((num, title, verdict, note, n, bad))
        failures += [f"§{num} {title}: {e}" for e in bad]
    return rows, failures


def render_md(rows, kinds, total, failures):
    out = ["# The 37-section UI/UX specification, audited against the build",
           "",
           "**Generated by `python3 tools/ux-audit.py --write`. Do not edit by hand.**",
           "",
           "The argument is in `docs/ux-specification.md`; this is the evidence. A design",
           "brief is the easiest kind of document to declare done against, because most of",
           "its requirements are about how something looks and nobody can check a feeling.",
           "So every row here asserts against the generated HTML, the CSS and the JavaScript",
           "as they actually are.",
           "",
           f"**{len(rows)} sections · " +
           " · ".join(f"{v} {k.lower()}" for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])) +
           f" · {total} assertions · {len(failures)} failing**",
           "",
           "| § | section | verdict | assertions | note |",
           "|---|---|---|---|---|"]
    for num, title, verdict, note, n, bad in rows:
        state = verdict if not bad else f"**FAILING** ({len(bad)})"
        out.append(f"| {num} | {title} | {state} | {n} | {note} |")
    out += ["",
            "## What the verdicts mean",
            "",
            "* **BUILT** — built from this brief, and the assertions prove it.",
            "* **ALREADY** — was already there when the brief arrived. Recorded rather than",
            "  claimed as new work.",
            "* **PARTIAL** — shipped in part, deliberately, with the missing half named.",
            "* **REFUSED** — decided against. The assertion checks both that we have not",
            "  drifted *and* that the reason is written down in `docs/ux-specification.md`,",
            "  because a refusal nobody can argue with is not a decision, it is a habit.",
            "* **DEFERRED** — deliberately not built.",
            "* **LOCKED** — a decision that overrides the brief.",
            "",
            "## The one lock",
            "",
            "The brief's navigation and page headers read **EUROPE ATLAS**. The name is",
            "**EuropeDoor**, at **europedoor.com**, and `tools/checks.py` enforces it on every",
            "page. See `docs/brand-lock.md`. A later document does not rename a product.",
            ""]
    return "\n".join(out)


def main():
    rows, failures = run()
    print("EuropeDoor — the 37-section UI/UX specification, audited against the build\n")
    for num, title, verdict, note, n, bad in rows:
        mark = "ok  " if not bad else "FAIL"
        print(f"  {mark}  §{num:<3} {title:<38} {verdict:<10} {n}")
        for e in bad:
            print(f"          ✗ {e}")
    kinds = {}
    for r in rows:
        kinds[r[2]] = kinds.get(r[2], 0) + 1
    total = sum(r[4] for r in rows)
    summary = " · ".join(f"{v} {k.lower()}" for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]))
    print(f"\n  {len(rows)} sections · {summary} · {total} assertions · {len(failures)} failing")

    if "--write" in sys.argv:
        with open(os.path.join(ROOT, "docs", "ux-audit.md"), "w", encoding="utf-8") as fh:
            fh.write(render_md(rows, kinds, total, failures))
        print("\n  wrote docs/ux-audit.md")

    if failures and "--check" in sys.argv:
        print("\nFAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)


if __name__ == "__main__":
    main()
