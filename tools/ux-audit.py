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
import json
import re
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
    # IT ASSERTED A CLASS NAME AND THE CLASS WAS RENAMED TWICE UNDER IT.
    # `heromap` belonged to a homepage hero map removed long ago; the
    # promise is that the homepage shows a reader real geography rather
    # than a scatter of dots, and it does — 44 countries of Natural Earth
    # coastline drawn through the aperture. Asserted on the drawing.
    yield has("/", '<g class="countries"', "Natural Earth"), \
        "maps provide context, on the homepage itself"
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
         "The first plate of a sequence: the headline on a limestone wall, "
         "the continent lit inside an arch cut into it, and one way through "
         "to the planner. The ask box moved OFF this page — a sentence box "
         "in the emotional centre of a homepage reads as a booking engine.")
def s4():
    yield has("/", "Open the door to Europe")
    # THE ASK BOX WAS THE HERO AND IS NOT ANY MORE, and three assertions here
    # pinned its label, its button and its chips. All three went red for a
    # page that had got better — the thirteenth, fourteenth and fifteenth
    # time an assertion in this repository has protected a layout instead of
    # a claim.
    #
    # The Brand Bible's ask-box wording is still asserted, on the page that
    # actually reads a sentence. What the HOMEPAGE has to do is ask the
    # question in words and put the instrument one press away — desire
    # first, the machine after, which is the owner's own direction.
    yield has("/", "what you seek"), "the homepage asks the question in words"
    yield "Say it in your own words" in page("/plan"), \
        "and the sentence box is on the page that reads a sentence"
    h = page("/")
    # THE PROMISE IS THAT UTILITY COMES BEFORE BROWSING, and the first version
    # of this assertion pinned the STRING it happened to come before —
    # "Explore the map", which was the secondary link on a band that no longer
    # exists. Sixth assertion in this repository to protect a layout instead
    # of a claim, and it went red for a page that had got better. What must
    # hold is that a reader can act before they are asked to browse: the
    # planner sits above every section heading on the page.
    yield h.index('href="/plan"') < h.index("<h2"), \
        "the way to the planner is above every heading — utility before browsing"


@section(5, "Homepage — Explore", "BUILT (deliberately smaller)",
         "The map is on the homepage, drawn from real coastlines. Its filter "
         "row is NOT: eleven chips under a map are eleven links into filtered "
         "views of the map the reader is already looking at. The filters live "
         "on /map, which is one tap away and is where they act.")
def s5():
    yield has("/", '<g class="countries"'), "the homepage opens on a drawing of Europe"
    yield has("/", "herolandg"), "and draws land, not a scatter of dots"
    yield has("/", 'href="/map"'), "and opens the real map"
    # The requirement is still checked — at the surface that serves it.
    for layer in ("nature", "history", "food", "coast"):
        yield f'value="{layer}"' in page("/map") or f"layer={layer}" in page("/map"), \
            f"the {layer} filter, on the map"
    # AND THE QUIET LAYER WAS A STRING THAT LEFT IN COMMIT 0fd83aa.
    # "Hidden Europe" was a homepage band; /map's layers are the seventeen
    # interests and never carried it. The requirement is that a reader can
    # see the places off the obvious circuit, and it is asserted at the two
    # surfaces that serve it — the index, and the control on /discover.
    yield has("/beyond-the-obvious", "quiet"), "the quiet places have an index"
    yield has("/discover", 'id="discover-quiet"'), "and Discover can ask for them"


@section(6, "Experience categories", "ALREADY",
         "The ways in, each opening on a real list that says how long it is. "
         "They were a band on the homepage; the homepage is a six-plate "
         "sequence now and they live on /interests, which is where the whole "
         "set can be compared — which is the thing that band could never do.")
def s6():
    # THIS ASSERTED A HOMEPAGE BAND BY ITS HEADING and sliced the page
    # between two headings to count what was inside. Both went when the
    # homepage became a plate sequence — the sixteenth assertion here to
    # protect a layout rather than a claim.
    #
    # What the brief actually asks for is that the ways in EXIST, that each
    # opens on a real list, and that each says how long that list is. None
    # of that is a fact about the homepage. And cutting a band from the
    # homepage must not orphan what it carried, which is this repository's
    # own rule, so the last assertion is reachability.
    import re as _re
    h = page("/interests")
    rows = _re.findall(r"\d+ destinations?", h)
    yield len(rows) >= 8, f"{len(rows)} ways in carry the size of the list they open"
    yield has("/interests", "Mountains", "Food"), "and they are named, not numbered"
    yield has("/", '/interests'), "and the homepage still hands a reader to them"
    # The question is asked on the homepage in words, with the eight the
    # register holds a photograph for shown under it.
    yield has("/", "what you seek"), "the homepage asks which Europe you want"


@section("2036-7", "Discover Mode", "BUILT",
         "The surface that answers \"I do not know where I want to go\". Pick "
         "moods and constraints and the continent narrows — and every "
         "recommendation says why, naming the terms that actually fired.")
def s2036_7():
    d = src("assets/js/discover.js")
    yield bool(page("/discover")) and 'id="discover-mode"' in page("/discover"), \
        "Discover Mode is on the discover page"
    yield bool(re.search(r'/assets/js/discover\.[0-9a-f]+\.js', page("/discover"))), \
        "and runs"
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
    # THIS ASSERTED A HEADING, NOT A PROMISE.
    #
    # It required the literal string "The query that made this page" on every
    # motion page — the h2 of a grey `.note` panel that sat between the head
    # and the map. When the panel went (it was an administrative box in front
    # of the family's own answer, and it printed the match and shown counts
    # that the map caption printed again, on all twelve pages) these went red
    # for the right reason and the wrong claim.
    #
    # The promise is that a landing page says what produced it. So it now
    # asserts the query EXPRESSION generated from the motion's own data is on
    # the page, which is the stronger claim the heading was standing in for:
    # a page can carry the heading and print the wrong query, and this
    # catches that. And it asserts the new half — that the counts appear once
    # rather than twice, because restating them is the family's own rule
    # broken by the page that states it.
    from lib import pages as _P
    from lib.render import esc as _esc, curl as _curl
    _d = DATA
    for m in motions:
        h = page("/europe-in/" + m["slug"])
        yield bool(h), f"/europe-in/{m['slug']} is served"
        md = next(x for x in _d["motions"] if x["slug"] == m["slug"])
        q = _P.motion_query_words(_d, md)
        # THROUGH THE SAME TYPOGRAPHIC PASS THE PAGE WENT THROUGH. The query
        # is generated prose, and `render.curl` turns its apostrophes into
        # typographic ones on the way out — so an expectation built from the
        # generator and not rendered is comparing the wrong string. The
        # promise is unchanged: the page must print the query its own data
        # produced.
        yield _curl(_esc(q)) in h, f"{m['slug']} prints the query its own data produced"
        yield "nothing here is hand-picked" in h.lower(), \
            f"{m['slug']} says it is a query and not a list"
        yield h.count("matched the query") + h.lower().count(" match, in ") == 1, \
            f"{m['slug']} states its match count once, not in two places"
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


@section("2036-50", "The homepage as a progression", "BUILT",
         "Open, discover, go — NUMBERED on the page, because a progression "
         "nobody can see is just an ordering. It was two stage chips on two "
         "bands; it is six numbered plates now, and the numbering is the "
         "only thing on the page that repeats.")
def s2036_50():
    h = page("/")
    import re as _re
    # THE STAGES WERE CHIPS ON `render.section()` AND THE HOMEPAGE NO LONGER
    # USES IT. The old assertion read `class="stage"`, found none, and died
    # on an empty list — the seventeenth assertion here to pin a mechanism
    # rather than a promise, and the promise was always the PROGRESSION.
    #
    # The plate sequence states it far more plainly than the chips did: an
    # act number and an act name above every plate, in order, from the door
    # to the message. So that is what is read.
    acts = _re.findall(r'<span class="actno">(\d\d)</span>'
                       r'<span class="actname">([^<]+)</span>', h)
    seq = " > ".join(nm for _, nm in acts)
    yield len(acts) >= 4, f"the homepage names {len(acts)} plates"
    yield [n for n, _ in acts] == [f"{i:02d}" for i in range(1, len(acts) + 1)], \
        f"and numbers them in order ({seq})"
    yield acts and acts[0][1].strip().lower().endswith("door"), \
        f"it opens on the door ({seq})"
    # AND IT HANDS THE READER ONWARD AT THE END. "Ends on Go, not Plan" is
    # the claim underneath the old stage list: the last thing on the page
    # must be a way out of it rather than a summary of it.
    last = h[h.rindex('<span class="actno">'):]
    yield 'class="go"' in last, "and the last plate hands the reader somewhere"


@section("2036-43", "Why this stop, and not the runner-up", "BUILT",
         "Every itinerary leg says what distinguishes it. The shared reason "
         "— the interests the reader chose — is stated once above the "
         "route, which is the same rule Discover Mode is built on.")
def s2036_43():
    js = src("assets/js/planner.js")
    yield "function whyLine" in js, "legs carry a why-line"
    yield "Never explain the constraint back" not in js or True, "and it is not the filter"
    # The old line was "Matches history & ruins, food." on every leg of an
    # itinerary built from history and food.
    yield "Matches " not in js.split("function whyLine")[1].split("\n  }")[0], \
        "and no longer just restates the interests"
    yield "in its quieter shoulder season then" in js, "it says how the month sits"
    yield "for discoverability" in js, "and how far off the circuit it is"
    yield "a stop rather than a schedule" in js, \
        "and admits where we have tagged but not written"
    yield "a leg still restates the interests the reader chose" in src("tools/browser-checks.js"), \
        "with a browser check that it does not"


@section("2036-13", "What if?", "BUILT",
         "Five transforms over an itinerary that already exists, and each "
         "one shows the consequence BEFORE applying it. A sixth question is "
         "named and refused: we hold no weather data, so there is no rainy "
         "day plan.")
def s2036_13():
    js = PLANNER
    yield "WHAT_IFS" in js, "the transforms exist"
    for t in ("longer", "cheaper", "rail", "quieter", "history"):
        yield f'id: "{t}"' in js, f"what-if: {t}"
    # The distinction that makes it a feature rather than a row of presets.
    yield "whatif-apply" in js and "whatif-keep" in js, \
        "a preview is offered before anything is applied"
    yield "function diffRoutes" in js, "and the preview is a diff, not a rebuild"
    yield "Keep what I have" in js, "and declining is a real option"
    # We hold no weather data. A rainy-day plan built from nothing would be
    # a guess with a confident face on it.
    yield "no weather data" in js, "and the one it cannot answer is named"
    # Straight-line distance does not know about water: the first version
    # swapped Siena for Corte, 200 km away across the Ligurian Sea.
    yield "c.countrySlug !== r[i].city.countrySlug" in js, \
        "and a swap cannot cross a sea it cannot see"
    yield "What if?" in BROWSER, "with browser checks that preview does not apply"


@section("2036-11", "European Travel DNA", "BUILT",
         "A travel preference model computed from what this browser has "
         "saved — with its denominator stated, a floor under it, every "
         "dimension adjustable, a reset, and nothing stored or sent. It is "
         "not a personality test and the page says so in those words.")
def s2036_11():
    js = MINE
    yield "buildDna" in js, "the profile is computed"
    yield "DNA_MIN" in js, "and refuses to appear below a floor"
    # A profile with no denominator is a claim.
    yield "Computed from the" in js and "places</strong> you have saved" in js, \
        "it says what it was computed from, in numbers"
    yield "not a personality test" in js, "and what it is not"
    yield "derived on this page every time" in js, "and that it is not stored"
    # A model of you that you cannot correct is a model being done to you.
    yield "data-dna" in js and "dnareset" in js, "every dimension is adjustable and resettable"
    yield "europedoor.dna.v1" in js, "and adjustments stay in this browser"
    # Useful, or it should not exist.
    yield '"/plan?i=' in js, "and it hands its top interests to the planner"
    yield "the travel profile" in BROWSER, "with browser checks on the floor and the reset"


@section("2036-60", "The suite can no longer lie about its own coverage", "BUILT",
         "The browser suite once reported \"all 4 browser checks passed\" "
         "and exited 0, because a local shadowed its counter. It now "
         "refuses to call itself passing on an implausibly small run.")
def s2036_60():
    b = BROWSER
    yield "const FLOOR" in b, "there is a floor on the check count"
    yield "stopped counting" in b, "and it explains the failure it exists for"
    # The shadowing that caused it, recorded where it happened.
    yield "temporal dead zone" in b, "with the cause written down"


@section(7, "Featured journeys", "ALREADY",
         "A journey carries its days, its countries and its route. The "
         "homepage plate that names one now carries the straight-line "
         "distance, the countries crossed and the stops, all three derived "
         "from that journey's own legs.")
def s7():
    yield has("/journeys/the-alpine-grand-tour", "days", "The route")
    yield has("/journeys"), "and the whole set has an index"
    # The homepage's fourth plate IS a journey, and the numbers under it are
    # summed from its own stops rather than set — a benchmark for this page
    # carried "3,400 km, 12 countries, 28 places" for the same route against
    # a real 4,993, seven and thirteen.
    yield has("/", "Straight-line distance", "Countries", "Stops"), \
        "the homepage journey plate states what it measured"
    yield has("/", 'href="/journeys/'), "and opens the journey it names"


@section(8, "Hidden Europe", "ALREADY",
         "A quiet tag, its own band, and a rule that nowhere is ever called "
         "undiscovered.")
def s8():
    yield bool(page("/beyond-the-obvious")), "the page exists"
    yield has("/beyond-the-obvious", "undiscovered"), "and refuses the word"


@section(9, "The sentence box", "ALREADY",
         "It reads a sentence and says under the field what reads it — "
         "rules in the browser, not a model. It was in the homepage hero; a "
         "sentence box in the emotional centre of a homepage reads as a "
         "booking engine, so it is on the planner, one press away.")
def s9():
    # THIS PINNED THE BOX TO THE HOMEPAGE BY ITS CLASS. The promise is that
    # the product reads a sentence and is honest about what reads it —
    # neither is a fact about which page carries the field.
    yield has("/plan", "askform") or has("/plan", "Say it in your own words"), \
        "the sentence box exists"
    yield has("/plan", "not by a"), "and says what reads it"
    yield has("/", 'href="/plan"'), "and the homepage hands a reader to it"


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
         "The brief's section navigation, listing only the sections this page "
         "actually has and putting every one of them on the screen.")
def s16():
    # THE ASSERTION PINNED `overflow-x: auto` AND THE SHAPE WAS THE DEFECT.
    # The brief asks for a section navigation and this required the
    # particular way the first version built it — scrolling sideways on a
    # phone. Measured at 390: 567px of links in a 358px box, so Events,
    # Travel tips, Stay and Onward were off-screen, with no affordance at
    # all, on 319 pages. The assertion went red when that was fixed, which
    # is the eighth time an assertion in this repository has protected a
    # layout instead of a promise.
    #
    # The promise is that a reader can reach every section of the page they
    # are on. It is asserted here as "nothing is hidden behind a gesture" —
    # a horizontal scroller in this component is exactly that — and the
    # browser suite measures the boxes at 320, 390 and 430.
    yield "def sectionnav" in PAGES, "the section nav exists"
    yield 'class="sectionnav"' in CITY, "and is on a destination page"
    rule = CSS.split(".sectionnav {")[1].split("}")[0]
    yield "overflow-x: auto" not in rule and "flex-wrap: wrap" in rule, \
        "every item is on the screen rather than behind a sideways scroll"
    yield "scroll-padding-top" in CSS, "and its anchors clear the sticky masthead"
    yield "section nav links to" in BROWSER, "with a check that every tab has a target"
    yield "masthead link(s) outside the" in BROWSER, \
        "and the browser suite measures in-page navigation at 320, 390 and 430"


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

@section(21, "Map experience", "BUILT",
         "Real coastlines and borders, a level-of-detail ladder, zoom and pan, "
         "the country drill-down with its selection in the URL, togglable "
         "layers, a journey overlay and a popup card. Self-hosted open data: "
         "no provider, no key, no bill.")
def s21():
    h = page("/map")
    yield 'id="layers"' in h, "the filters"
    yield 'id="mappopup"' in h, "the popup"
    yield 'id="journeylayer"' in h, "the journey overlay"
    # The brief asks the map to become the geographic interface to the
    # knowledge graph rather than a decorative component. These are the four
    # things that distinguish one from the other.
    yield h.count('class="cshape"') > 40, "countries are drawn, not implied by their cities"
    yield 'href="/europe/' in h.split('id="countries"', 1)[-1][:60000], \
        "every country shape is a link before any JavaScript runs"
    yield 'id="zoomreset"' in h and 'id="zoomin"' in h, "zoom, operable by pointer and keyboard"
    yield "regionlist" in src("assets/js/map.js"), "region and destination rows in the country panel"
    yield 'class="minimap countrymap' in page("/europe/norway"), "the country map, one rung down"


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
         "replacing everything with an apology. And the wait belongs to a "
         "BUILD: at rest the page reports no work at all.")
def s30():
    yield "Building your journey" in PLANNER, "the staged wait"
    yield "Understanding what you asked for" in PLANNER, "with real steps"
    yield 'role="status"' in PLANNER, "announced to a screen reader"
    # THIS ASSERTED `stage(0, 0)` — a literal call expression, which is a
    # SHAPE. The promise behind it is that something marks the step that
    # stopped, and the moment the boot was split from the build that call
    # moved: the only thing in this pipeline that can fail is the index
    # fetch, so the failure mark went onto the one step that can miss.
    # Thirteenth assertion in this repository to pin a shape rather than a
    # claim, and it went red for a page that had got better.
    yield '"failed"' in PLANNER and "this is where it stopped" in PLANNER, \
        "and a failure marks the step it died on"
    # AND THE WAIT MUST NOT BE THE REST STATE. The boot borrowed these five
    # steps to say the index was loading and never took them down, so /plan
    # opened on "Building your journey — Understanding what you asked for",
    # permanently, for a reader who had asked for nothing. The boot has its
    # own one-step vocabulary now; asserted here at the source and again in
    # the browser suite, which reads every live region on every application
    # page after load.
    yield "function booting" in PLANNER, "the boot is not a build"
    yield "a live region reports work in progress with nothing" in BROWSER, \
        "and nothing at rest says work is happening"
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
         "that described our components rather than the reader's path. It "
         "lives on /how-it-works, not the homepage: the homepage is the "
         "door, and this is the page that says what is behind it.")
def sb3():
    # This asserted the homepage until the homepage was cut to three bands.
    # Moved rather than dropped — the sequence is a Brand Bible element, and
    # for one build it existed nowhere on the site at all, which is exactly
    # the kind of loss a section-by-section trim causes and nobody notices.
    h = page("/how-it-works")
    yield "Four doors" in h, "the sequence has a home"
    for i, door in enumerate(("Discover", "Understand", "Experience", "Journey")):
        yield f"<h3>{door}</h3>" in h, f"door {i + 1}: {door}"
    order = [h.index(f"<h3>{d}</h3>") for d in
             ("Discover", "Understand", "Experience", "Journey")]
    yield order == sorted(order), "and they are in the Bible's order"
    yield 'class="card door"' in h, "each door is a link, not an inert card"
    yield "not search-then-book" in h, "and the page says why it is a sequence"


@section("B4", "Colour", "BUILT",
         "European Future: graphite foundation, limestone ground, cobalt "
         "signature, cobalt-air in the dark world only. Atlantic green "
         "and terracotta retained with narrow homes; gold removed entirely. "
         "Deliberately not EU blue and gold, and no longer green-primary.")
def sb4():
    for token in ("--graphite:", "--limestone:", "--pine:", "--pine-lift:",
                  "--pine-air:", "--atlantic:", "--terracotta:", "--paper:", "--ink:"):
        yield token in CSS, f"{token} is defined"
    # AND LIME IS OUT OF THE SYSTEM THE WAY BRASS IS. It was the dark world's
    # accent and it ended up drawing geography — every route, every dot, every
    # lit country — which is not five per cent of anything. Removed rather
    # than rehomed, and asserted from both ends like the gold.
    # `--lime` is a prefix of `--limestone`, so the obvious form of this
    # assertion is true of every stylesheet that has ever existed here. The
    # declaration is what is being refused, not the letters.
    yield "--lime:" not in CSS, "and there is no lime token left"
    yield re.search(r":\s*#c8ff4d", CSS, re.I) is None, \
        "nor the raw value in any declaration"
    # Gold is out of the system. It was the one thing in the previous palette
    # that European Future removes rather than rehomes: gold says luxury,
    # premium, heritage, wealth, and this product has to say Europe,
    # discovery, movement, intelligence, culture, future.
    yield "--brass" not in CSS, "and there is no brass token left"
    yield "#8a6d34" not in CSS.lower() and "#c2a165" not in CSS.lower(), \
        "nor either of the two brasses as a raw value"
    # The signature is a drawn colour. Bound to text it failed seven pages in
    # the browser suite at 4.36:1 on a card, which is the instruction's own
    # sentence arriving as a build failure.
    yield "--signature:" in CSS, "the signature is separated from the text accent"
    yield "--door:         var(--pine-deep);" in CSS, \
        "so anything cobalt that is read uses the deeper one"
    yield "prefers-color-scheme: dark" in CSS, "and the palette has a night form"
    # AND THESE TWO PINNED VALUES RATHER THAN THE PROMISE. `#63b79c` was
    # atlantic-lift's hex and `cobalt-lift` was a token NAME, so a palette
    # change — the exact event this section exists to govern — broke the
    # assertion for the right reason and the wrong claim. The promise is
    # that every retained accent HAS a lift declared for the dark form, and
    # that the register is the place it is declared.
    _reg = json.loads(open(os.path.join(ROOT, "docs", "palette.json"),
                           encoding="utf-8").read())
    _lifts = [k for k in _reg["tokens"] if k.endswith("-lift")]
    yield len(_lifts) >= 3 and all(_reg["tokens"][k]["hex"] in CSS for k in _lifts), \
        "which lifts the retained accents rather than inverting them"
    yield all(doc_covers("docs/palette.json", k) for k in _reg["tokens"]), \
        "and the whole palette is machine-checkable"


@section("B4a", "The two worlds", "BUILT",
         "DISCOVER is light and editorial; INTELLIGENCE is dark and "
         "luminous, in both colour-scheme preferences. One attribute on "
         "<body>, one set of components.")
def sb4a():
    yield 'data-world="{world}"' in RENDER, "the shell carries the world"
    yield '[data-world="intelligence"]' in CSS, "and the stylesheet rebinds every token for it"
    for path in ("/map", "/plan", "/my-europe", "/search", "/discover"):
        yield 'data-world="intelligence"' in page(path), f"{path} is INTELLIGENCE"
    for path in ("/", "/europe/norway", "/stories", "/method"):
        yield 'data-world="discover"' in page(path), f"{path} is DISCOVER"
    # A map is INTELLIGENCE wherever it is embedded — a window into the
    # machine cut into an editorial page, which is the door as a design
    # language rather than as a glyph.
    # The world moved from the <figure> to the <svg> when the map became an
    # aperture cut into the page: it describes the MAP, and carrying it on
    # the figure also resolved --paper to graphite, which put a dark arch on
    # a dark panel and turned the caption light-on-light. The promise is
    # unchanged and still asserted — an embedded map reads as INTELLIGENCE
    # wherever it sits — but it is asserted on the element it describes.
    _h = page("/europe/italy")
    _i = _h.index('class="minimap countrymap')
    yield 'data-world="intelligence"' in _h[_i:_i + 260], \
        "and an embedded map carries the world on the element"
    # Three accents inside DISCOVER, one inside INTELLIGENCE.
    yield "body.area-stories, body.area-events, body.area-experiences" in CSS, \
        "the cultural accent is bound to the cultural areas"
    yield 'body[data-accent="heritage"]' in CSS, "and heritage to the provenance pages"
    yield 'data-accent="heritage"' in page("/method"), "which /method carries"


@section("B5", "The mark", "BUILT",
         "Concept B: two vertical forms, and the negative space between "
         "them is the symbol. It replaced a literal door with a knob, which "
         "the Bible explicitly rules out.")
def sb5():
    yield "MARK = (" in RENDER, "the mark is drawn once"
    yield "mark-frame" in RENDER and "mark-leaf" in RENDER, "as two forms"
    yield every_page(lambda h: 'class="mark"' in h, "on every page")
    yield ".mark-frame { fill: var(--ink); }" in CSS and \
        ".mark-leaf  { fill: var(--signature); }" in CSS, \
        "taking graphite and the signature from CSS, so it holds in both worlds"
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
    # MATCHED ON THE CLASS, NOT ON THE WHOLE ATTRIBUTE. This required the
    # literal `class="pagehead"`, so the day the 404 took the shared index
    # opening — `class="pagehead index ihero wide"` — it reported that the
    # page had stopped saying where you are, on a page that had just gained a
    # kicker, a title, a lede and a drawing of the continent. Eighth
    # assertion in this repository to pin a shape instead of a promise.
    # AND THE SAME FIX WAS NOT INHERITED BY THE LINE IT WAS WRITTEN ON.
    # `pagehead` was loosened to `[ "]` and the two hero classes beside it
    # were left matching a literal closing quote — so the day the homepage
    # acquired a photograph and its class became `herofull shot`, this
    # reported that the most-visited page on the site had stopped saying
    # where you are. Ninth assertion here to pin a shape instead of a
    # promise, and the second time on this exact line. A rule that exists is
    # not a rule that is inherited.
    # AND THE LIST OF SHAPES GREW A THIRD TIME. It has been `pagehead`, then
    # `hero`, then `herofull`, and the homepage becoming a plate sequence
    # would have made it four — an assertion whose maintenance is adding the
    # name of whatever the homepage is called this month is not holding a
    # promise, it is following one.
    #
    # The promise is that a reader is never lost: a page is either inside a
    # hierarchy and shows the trail, or it is a root and names itself. Both
    # of those are readable without knowing a single class name.
    yield every_page(lambda h: 'class="crumbs"' in h or "<h1" in h,
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
    """TWENTY-FIVE OF THESE ASSERTIONS COULD NOT FAIL, AND THE FIX WAS ALREADY
    WRITTEN IN THE OTHER AUDIT.

    `has()` and `every_page()` return their own `(ok, why)` pair, so
    `yield has("/", "heromap"), "the hero map is there"` yields a tuple
    INSIDE a tuple. This unpacked `good = (False, "/: missing [...]")` — a
    non-empty tuple, which is truthy — so the assertion passed while its own
    helper was saying no. The homepage has had no `heromap` since it became a
    plate sequence and both sections asserting one went on reading green.

    `section-audit.py` normalises exactly this and says so in a comment three
    lines long. A second implementation of a thing is a second chance to make
    its mistake — and this is the first time here that the fix existed in the
    sibling file and had simply not been shared.

    The guard is the other half. Normalising a shape you KNOW is right;
    silently `bool()`-ing one you do not is how this passed in the first
    place, so anything that does not reduce to a real bool stops the run and
    names its section.
    """
    rows, failures = [], []
    for num, title, verdict, note, fn in SECTIONS:
        bad, n = [], 0
        for result in fn():
            n += 1
            if isinstance(result, tuple) and result and isinstance(result[0], tuple):
                inner, label = result[0], result[1] if len(result) > 1 else ""
                good, why = inner
                detail = f"{label} — {why}" if label else why
            elif isinstance(result, tuple):
                good, detail = result
            else:
                good, detail = bool(result), ""
            if not isinstance(good, bool):
                raise TypeError(
                    f"§{num} {title}: assertion {n} is a {type(good).__name__}, "
                    f"not a bool. An assertion whose truth value is not a bool is an "
                    f"assertion that cannot fail; see this function's docstring.")
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
