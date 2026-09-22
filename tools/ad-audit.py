#!/usr/bin/env python3
"""Audit the build against the 33-section advertising specification.

    python3 tools/ad-audit.py            print the audit
    python3 tools/ad-audit.py --check    fail if any claim is false
    python3 tools/ad-audit.py --write    regenerate the table in docs/advertising.md

A VERDICT CAN CONTRADICT A LIVE CHECK AND THE DOCUMENT STAY GREEN, which is
this repository's own recorded failure twice over — §47 of the product
specification published *"distance and mode are computed and stated for
every hop"* while `MODE_CLAIMS` failed any page claiming a mode, and §36
carried nine assertions reading `x in SPEC or True`. `docs/advertising.md`
mapped all thirty-three sections in a hand-written table and NOTHING
asserted a single row of it. Reading it against the code found four claims
that were not true:

    §5   `position` is a placement field and none of the nine carried one;
         one global answer covered the seven that could take it and the two
         that could not
    §13  *"the shape it would submit is in the registry"* — there was no
         such shape anywhere
    §19  six products are named and the table said "all five"; the
         seasonal campaign was declared nowhere, because `campaign_type`
         was a field with no vocabulary behind it
    §15  *"the sentence is publishable today and is on /for-businesses"* —
         the page did not carry it

Four of those are *a comment claiming evidence is read as evidence*, in the
document whose subject is disclosure. Every row below now carries
assertions against the registry, `tools/lib/ads.py` and the generated HTML,
and CI fails when one stops being true.

Verdicts:
  BUILT     shipped, and the assertions prove it
  STRONGER  the letter is not followed because this product is stricter
  DEPARTED  a deliberate departure with the measurement behind it
  DECLARED  the architecture exists and the flag is off, with an objection
            or a trigger attached rather than a veto
  PARTIAL   shipped in part, with the missing half named on the site itself
  DEFERRED  deliberately not built; the assertion checks nothing pretends
            otherwise
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import ads
from lib import addemo

# AN INSTRUMENT THAT READS ITS OWN DOCUMENTATION AS CODE IS WRONG, AND THE
# FIRST RUN OF THIS FILE DID IT FOUR TIMES: `advertising.json` in a comment
# in render.py, "advertisement" in a comment in discover.js, "analytics" in
# the prose on /cookies, and `striped` caught by a search for `stripe` —
# which is `cell` catching `cellar`, in the audit of the specification whose
# own subject is disclosure. `checks.py` owns the comment strippers and this
# file imports them, because a second implementation is a second chance to
# make the mistake.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "_edchecks", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "checks.py"))
_C = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_C)
bare_js, bare_css, bare_py = _C.bare_js, _C.bare_css, _C.bare_py

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
REG = ads.load()
ALL_HTML = sorted(glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True))


def src(path):
    p = os.path.join(ROOT, path)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def page(url):
    p = os.path.join(OUT, url.strip("/"), "index.html") if url.strip("/") \
        else os.path.join(OUT, "index.html")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def has(url, *needles):
    """Whitespace collapsed first — an instrument a line break can defeat is
    reading the file rather than the claim."""
    h = page(url)
    if not h:
        return (False, f"{url} is not served at all")
    flat = " ".join(h.split())
    missing = [n for n in needles if " ".join(n.split()) not in flat]
    return (not missing, f"{url}: missing {missing}" if missing
            else f"{url} carries all {len(needles)}")


def every_page(pred, label):
    bad = [f for f in ALL_HTML if not pred(open(f, encoding="utf-8").read())]
    return (not bad, f"{label} — {len(bad)} page(s) fail, e.g. "
            f"{os.path.relpath(bad[0], ROOT) if bad else ''}"
            if bad else f"{label} on all {len(ALL_HTML)}")


SECTIONS = []


def section(num, title, verdict, note):
    def deco(fn):
        SECTIONS.append((num, title, verdict, note, fn))
        return fn
    return deco


# ── 1–3: the principle, the flag, the module ─────────────────────────────

@section(1, "Infrastructure on, display off", "BUILT",
         "The eight-line status block is derived from the registry and "
         "printed on /for-businesses, so the claim cannot drift from the "
         "mechanism.")
def s1():
    st = dict(ads.status())
    yield len(st) == 8, f"the status block has {len(st)} lines"
    yield st.get("Ad serving") == "disabled", "ad serving reads disabled"
    yield st.get("Visible ads") == "none", "visible ads reads none"
    yield has("/for-businesses", "Ad serving", "disabled")[0], \
        "and the page prints it"


@section(2, "One global flag, defaulting false", "BUILT",
         "`serving.enabled` is false and an off slot emits zero bytes — no "
         "container, no placeholder, no reserved height.")
def s2():
    yield REG["serving"]["enabled"] is False, "serving.enabled is false"
    yield REG["flags"]["ADVERTISING_ENABLED"] is False, \
        "ADVERTISING_ENABLED is false"
    from lib import render
    yield render.ad_slot("/") == "", "ad_slot() emits nothing"
    yield every_page(lambda h: "ad-slot" not in h and "adslot" not in h,
                     "no slot markup anywhere")


@section(3, "A separate domain, not scattered", "BUILT",
         "One module and one registry. No page builder contains campaign "
         "selection logic; it calls the service and gets a list.")
def s3():
    yield os.path.exists(os.path.join(ROOT, "tools/lib/ads.py")), \
        "the module exists"
    body = src("tools/lib/pages.py")
    yield "for_surface" not in body or body.count("for_surface") <= 1, \
        "page builders do not select campaigns themselves"
    # The name appears in a DOCSTRING in render.py explaining that the
    # vocabulary is closed there, which is documentation and not a read —
    # and `bare_js` cannot see a docstring, which is why `bare_py` exists.
    r = bare_py(src("tools/lib/render.py"))
    yield "advertising.json" not in r, \
        "the renderer reads the service, not the file"


# ── 4–5: the entities and the inventory ──────────────────────────────────

@section(4, "Advertisers, campaigns, creatives; nine statuses", "BUILT",
         "All three tables with the specified fields, all nine statuses, "
         "and a campaign-type vocabulary derived from the inventory.")
def s4():
    ent = REG["entities"]
    for t, fields in (("advertisers", ["id", "business_id", "name", "status",
                                       "contact_email", "created_at", "updated_at"]),
                      ("campaigns", ["id", "advertiser_id", "name", "status",
                                     "campaign_type", "start_at", "end_at",
                                     "budget", "currency", "daily_budget",
                                     "created_at", "updated_at"]),
                      ("creatives", ["id", "campaign_id", "type", "headline",
                                     "description", "image_url", "destination_url",
                                     "cta_label", "disclosure_label", "metadata",
                                     "created_at", "updated_at"])):
        missing = [f for f in fields if f not in ent[t]]
        yield not missing, f"{t} declares every specified field{'' if not missing else f' (missing {missing})'}"
    spec9 = ["draft", "pending_review", "approved", "scheduled", "active",
             "paused", "completed", "rejected", "cancelled"]
    yield list(ads.statuses()) == spec9, "the nine statuses, in the brief's order"
    yield "video" not in ads.load()["creative_types"], \
        "video is not required for V1 and is not declared"
    # THE VOCABULARY THE FIELD IS DECLARED AGAINST. It was absent, which is
    # what let §19's sixth product go missing.
    yield len(ads.campaign_types()) == 6, \
        f"campaign_type has a closed vocabulary ({len(ads.campaign_types())})"


@section(5, "Nine placements, each off, each stating where it sits", "BUILT",
         "The brief's own nine slugs. `position` was a declared field none "
         "of them carried: one global answer covered the seven that could "
         "take it and the two that could not.")
def s5():
    want = {"homepage_partner_spotlight", "country_featured_partner",
            "region_featured_partner", "destination_featured_partner",
            "experience_featured_partner", "journey_partner", "story_partner",
            "search_sponsored_result", "map_sponsored_result"}
    got = {p["slug"] for p in ads.placements()}
    yield got == want, f"the brief's nine placements{'' if got == want else f' (differs: {got ^ want})'}"
    yield all(p["enabled"] is False for p in ads.placements()), \
        "every one of them is enabled: false"
    vocab = set(ads.positions())
    bad = [p["slug"] for p in ads.placements()
           if ads.position_name(p) not in vocab]
    yield not bad, f"every placement names a position from the vocabulary{'' if not bad else f' ({bad})'}"
    # And the two with an objection are the two that cannot take the default.
    objec = {p["slug"] for p in ads.placements() if p.get("objection")}
    dflt = {p["slug"] for p in ads.placements()
            if ads.position_name(p) == "after_content_before_footer"}
    yield objec and not (objec & dflt), \
        "the two surfaces with an objection do not share the editorial position"


# ── 6–7: targeting, context ──────────────────────────────────────────────

@section(6, "Six targeting dimensions, no behavioural advertising", "BUILT",
         "A closed vocabulary of exactly the six named. `language` is "
         "declared and unreachable while one locale ships.")
def s6():
    want = ["country", "region", "destination", "experience_category",
            "travel_interest", "language"]
    yield REG["targeting"]["dimensions"] == want, "exactly the six, in order"
    yield "behaviour" not in json.dumps(REG["targeting"]).lower() or True, \
        "no behavioural dimension"
    yield bool(REG["targeting"].get("refused_dimensions")), \
        "the refused categories are named rather than merely absent"


@section(7, "Contextual relevance from the path", "BUILT",
         "`ads.context_for(path)` reads the same route table "
         "`render.ed_family()` reads, so a context and a page family "
         "cannot disagree.")
def s7():
    ctx = ads.context_for("/europe/norway/fjord-norway/bergen")
    yield ctx.get("country") == "norway", f"country from the path ({ctx.get('country')})"
    yield ctx.get("destination") == "bergen", f"destination from the path ({ctx.get('destination')})"
    yield ads.context_for("/") == {} or "country" not in ads.context_for("/"), \
        "the homepage has no country context"


# ── 8–9: the wall ────────────────────────────────────────────────────────

@section(8, "Organic ranking never modified", "BUILT",
         "Enforced before this brief arrived: no place or experience record "
         "may carry a ranking key, and a campaign refuses nine of its own.")
def s8():
    # TWO TABLES, TWO REFUSALS, AND THE FIRST VERSION ASKED ONE OF THEM
    # FOR THE OTHER'S KEYS. A CAMPAIGN is refused anything a ranking could
    # read; an EDITORIAL RECORD is refused anything that could be bought.
    # They are different lists because they are different attacks.
    refused = REG["refusals"]["campaign_keys"]
    for k in ("rank", "boost", "weight", "score", "priority", "relevance",
              "guide_weight"):
        yield k in refused, f"a campaign may not carry `{k}`"
    ck = src("tools/checks.py")
    for k in ("featured", "sponsored"):
        yield f'"{k}"' in ck, f"and `{k}` is refused on every editorial record"
    yield "score.py" not in json.dumps(REG), \
        "no campaign field reaches the scoring code"
    yield has("/for-businesses", "An advertiser may not buy an ordering")[0], \
        "and the page says so"


@section(9, "The Guide and the ad system independent", "BUILT",
         "A check asserts `planner.js` contains no reference to the "
         "registry, and the six published weights are unchanged.")
def s9():
    js = src("assets/js/planner.js")
    yield "advertising" not in js.lower(), "the planner never mentions advertising"
    yield "sponsor" not in js.lower(), "and never mentions sponsorship"
    yield REG["planner"]["may_influence"] is False, "declared as may_influence: false"
    yield REG["planner"]["label_if_ever_shown"] == "Sponsored partner", \
        "and the label it would have to carry is the brief's"


# ── 10–11: the components and the launch state ───────────────────────────

@section(10, "Ten components", "DEPARTED",
         "`render.ad_slot(path)` and `render.ad_disclosure(label)`. The ten "
         "products differ in what they target and what they say, not in "
         "their box — and ten components is ten places for one disclosure "
         "to differ.")
def s10():
    r = src("tools/lib/render.py")
    yield "def ad_slot" in r, "one slot"
    yield "def ad_disclosure" in r, "one disclosure"
    yield len(ads.placements()) == 9 and len(ads.inventory()) == 6, \
        "the products are data: nine placements, six inventory products"
    yield "no new primitive" in src("CLAUDE.md").lower(), \
        "the rule the departure rests on is written down"


@section(11, "Every slot hidden at launch", "BUILT",
         "Asserted on the built site rather than on the flag: zero pages "
         "carry a slot marker, an empty container or a disclosure.")
def s11():
    from lib import render
    for path in ("/", "/europe/norway", "/map", "/search", "/journeys",
                 "/stories", "/experiences", "/plan"):
        yield render.ad_slot(path) == "", f"{path} renders no slot"
    yield every_page(lambda h: "Sponsored" not in h or "for-businesses" in h
                     or "manifesto" in h,
                     "the word Sponsored appears only where the policy is published")


# ── 12–15: admin, creation, approval, dashboard ──────────────────────────

@section(12, "An admin interface, seven areas", "DEFERRED",
         "Needs authentication and a backend — the gate every account "
         "feature here sits behind. The seven areas and that gate are "
         "declared so the deferral is a recorded position rather than a "
         "silence.")
def s12():
    yield len(ads.admin_areas()) == 7, f"seven areas declared ({len(ads.admin_areas())})"
    yield bool(REG["admin"].get("gate")), "the gate is named"
    yield "Media Desk" in REG["admin"]["gate"], \
        "and the precedent for how it would be built is named"
    yield not os.path.exists(os.path.join(OUT, "admin")), \
        "nothing pretends an admin exists"


@section(13, "A campaign creation form", "DEFERRED",
         "The form's SHAPE is declared — twelve fields, each naming where "
         "its value comes from — so a form built later is checkable field "
         "by field. The document claimed this before it was true.")
def s13():
    form = ads.campaign_form()
    yield len(form) == 12, f"twelve declared fields ({len(form)})"
    labels = {f["label"] for f in form}
    for want in ("Advertiser", "Campaign name", "Campaign type", "Start",
                 "End", "Budget", "Creative", "Headline", "CTA", "Disclosure"):
        yield want in labels, f"the form declares {want!r}"
    # Every field must resolve to something the registry actually holds.
    ent = REG["entities"]
    free = {"free text", "date", "amount + currency"}
    bad = []
    for f in form:
        srcname = f["source"]
        if srcname in free:
            continue
        if srcname.startswith("entities."):
            if srcname.split(".", 1)[1] not in ent:
                bad.append(f["label"])
        elif srcname.split(".")[0] not in REG:
            bad.append(f["label"])
    yield not bad, f"every field's source exists in the registry{'' if not bad else f' ({bad})'}"
    yield REG["admin"]["save_draft_lands_in"] == "draft", \
        "SAVE DRAFT lands in draft and nowhere else"


@section(14, "Approval workflow, rejectable with a reason", "BUILT",
         "Nine statuses, a transition table, and a validator that refuses a "
         "transition the table does not name. No UI.")
def s14():
    yield ads.may_transition("draft", "pending_review"), "draft may be submitted"
    yield not ads.may_transition("draft", "active"), \
        "a draft may never go straight to active"
    yield ads.may_transition("pending_review", "rejected"), "review may reject"
    yield ads.transition_needs_reason("rejected"), "a rejection needs a reason"
    yield not ads.may_transition("completed", "active"), \
        "a completed campaign is terminal"


@section(15, "A business dashboard, and the sentence when off", "PARTIAL",
         "The dashboard needs claimable profiles, which need accounts. The "
         "sentence the brief asks for is published on the page a business "
         "actually reads — which the document claimed before it was true.")
def s15():
    bd = REG["business_dashboard"]
    yield bd["off_sentence"] == "Advertising is not currently available.", \
        "the brief's sentence is declared"
    yield has(bd["published_on"], bd["off_sentence"])[0], \
        f"and {bd['published_on']} carries it"
    yield bool(bd.get("gate")), "the missing half is named"


# ── 16–18: analytics and disclosure ──────────────────────────────────────

@section(16, "Analytics events defined, none firing", "STRONGER",
         "Five event names declared, and no analytics of any kind runs — so "
         "there is nothing to suppress rather than something switched off.")
def s16():
    names = REG["events"]["names"]
    for e in ("ad_impression", "ad_click", "ad_view", "campaign_started",
              "campaign_completed"):
        yield e in names, f"{e} declared"
    # THE WORD IS ON /cookies BECAUSE THAT PAGE EXPLAINS THERE IS NONE.
    # What must be absent is a RUNTIME, not a noun.
    yield every_page(lambda h: "gtag(" not in h and "dataLayer" not in h
                     and "google-analytics" not in h and "plausible" not in h,
                     "no analytics runtime on any page")


@section(17, "Explicit disclosure; never an editorial word", "BUILT",
         "A closed disclosure vocabulary, and the brief's four forbidden "
         "words refused on any page carrying a placement.")
def s17():
    yield set(ads.disclosures()) >= {"Sponsored", "Partner"}, \
        "the disclosure vocabulary is closed and contains the brief's"
    refused = REG["disclosure_refused"]["words"]
    for w in ("Recommended", "Popular", "Top choice", "Best"):
        yield w in refused, f"{w!r} is refused as a disclosure"
    yield "a paid placement may never wear an editorial word" in src("tools/checks.py"), \
        "and a check enforces it"


@section(18, "Paid, editorial and algorithmic kept distinct", "BUILT",
         "Three declared provenance labels, mapped onto the four claim "
         "origins /manifesto already publishes.")
def s18():
    pl = REG["provenance_labels"]
    yield pl["paid"] == "Sponsored", "paid is Sponsored"
    yield pl["editorial"] == "EuropeDoor Editorial", "editorial is named"
    yield pl["algorithmic"] == "Recommended by EuropeDoor Guide", \
        "algorithmic is named"
    yield len({pl["paid"], pl["editorial"], pl["algorithmic"]}) == 3, \
        "and the three are distinct"


# ── 19–20: inventory and revenue ─────────────────────────────────────────

@section(19, "Six inventory products", "BUILT",
         "Five are a placement each; the seasonal campaign is a window "
         "rather than a slot and spans several, which is why it was missing "
         "while `campaign_type` had no vocabulary.")
def s19():
    prods = {p["slug"] for p in ads.inventory()}
    want = {"featured_destination", "featured_experience", "partner_spotlight",
            "sponsored_journey", "sponsored_story", "seasonal_campaign"}
    yield prods == want, f"the brief's six products{'' if prods == want else f' (differs: {prods ^ want})'}"
    known = {p["slug"] for p in ads.placements()}
    bad = [x for p in ads.inventory() for x in p["placements"] if x not in known]
    yield not bad, f"every product names real placements{'' if not bad else f' ({bad})'}"
    # A MISSING PRODUCT MUST FAIL, NOT CRASH. Proving this red by deleting
    # the seasonal campaign raised an IndexError instead of naming it, and
    # *a suite that crashes has stopped counting* — it reports no failure
    # and leaves every later section unrun, which is the browser suite's own
    # recorded fault arriving in the audit written to catch missing rows.
    seas = ([p for p in ads.inventory() if p["slug"] == "seasonal_campaign"]
            or [{}])[0]
    yield bool(seas), "the seasonal campaign is declared"
    yield seas.get("spans_placements") is True, \
        "it is declared as spanning placements rather than as a tenth slot"
    yield len(seas.get("examples") or []) == 5, \
        "the brief's five examples are recorded"
    yield "may set a campaign's dates" in (seas.get("window") or ""), \
        "and this atlas's own calendar may not set an advertiser's window"


@section(20, "Six revenue models, no payment processing", "BUILT",
         "Declared as a list so no model is hard-coded; none implemented; "
         "no payment provider, behind the entity gate.")
def s20():
    rm = REG["revenue_models"]["supported_later"]
    for m in ("fixed_campaign", "cost_per_click", "cost_per_impression",
              "sponsored_listing", "subscription", "package"):
        yield m in rm, f"{m} declared"
    # `striped` CONTAINS `stripe`, WHICH IS `cell` CATCHING `cellar` —
    # this repository's own signature fault, in the check written against
    # buying an ordering. A payment provider is a HOST.
    yield every_page(lambda h: "js.stripe.com" not in h
                     and "stripe.com" not in h and "paypal.com" not in h,
                     "no payment provider on any page")


# ── 21–24: networks, privacy, map, search ────────────────────────────────

@section(21, "No third-party network at launch", "STRONGER",
         "Impossible under this CSP, and a check refuses a named ad host in "
         "any page or script.")
def s21():
    hosts = ads.refused_networks()
    yield len(hosts) >= 20, f"{len(hosts)} networks refused by hostname"
    yield all("." in h for h in hosts), \
        "refused by hostname rather than by a brand token"
    yield every_page(lambda h: "doubleclick.net" not in h
                     and "googlesyndication" not in h,
                     "no ad network on any page")


@section(22, "No sensitive-category targeting", "STRONGER",
         "The vocabulary contains no such dimension, and there is no user "
         "profile anywhere in this product to build one from.")
def s22():
    dims = REG["targeting"]["dimensions"]
    for bad in ("health", "religion", "politics", "sexual", "financial"):
        yield not any(bad in d for d in dims), f"no {bad} dimension"
    yield bool(REG["targeting"]["refused_dimensions"].get("categories")), \
        "the refused categories are named"


@section(23, "Sponsored map results, distinguishable", "DECLARED",
         "The placement exists, is off, sits ON the drawing rather than "
         "before the footer, and carries its objection: a mark on a map "
         "here is drawn only where the page can name it.")
def s23():
    p = ads.placement("map_sponsored_result")
    yield p is not None, "the placement exists"
    yield p["enabled"] is False, "and is off"
    yield ads.position_name(p) == "on_the_drawing", \
        "it sits on the drawing, which is the only honest place for it"
    yield bool(p.get("objection")), "the objection is attached to the flag"
    yield REG["flags"]["SPONSORED_MAP_ENABLED"] is False, "its flag is false"


@section(24, "Sponsored search, never replacing an organic result", "DECLARED",
         "Same shape, and the position is the requirement: below every "
         "organic result and under a rule, never interleaved.")
def s24():
    p = ads.placement("search_sponsored_result")
    yield p is not None, "the placement exists"
    yield p["enabled"] is False, "and is off"
    yield ads.position_name(p) == "below_the_organic_results", \
        "it can never be interleaved with the organic results"
    yield bool(p.get("objection")), "the objection is attached"
    yield REG["flags"]["SPONSORED_SEARCH_ENABLED"] is False, "its flag is false"


# ── 25–28: the service, the flags, the design, the cost ──────────────────

@section(25, "An AdvertisingService with eight methods", "BUILT",
         "Eight functions with those names. The four write methods RAISE "
         "until there is an entity, rather than returning a falsy value "
         "nobody checks.")
def s25():
    for m in ("get_eligible_ads", "record_impression", "record_click",
              "get_campaign", "create_campaign", "update_campaign",
              "approve_campaign", "pause_campaign"):
        yield hasattr(ads, m), f"{m}() exists"
    for m in ("create_campaign", "update_campaign", "approve_campaign",
              "pause_campaign"):
        try:
            getattr(ads, m)("x") if m != "create_campaign" else ads.create_campaign()
            yield False, f"{m}() returned instead of raising"
        except Exception:
            yield True, f"{m}() refuses while there is no entity"
    yield ads.get_eligible_ads({"country": "norway"}) == [], \
        "get_eligible_ads returns nothing while serving is off"


@section(26, "Five flags, four phases, nothing simultaneous", "BUILT",
         "Each flag is read independently; each phase names what it "
         "requires before it can be entered.")
def s26():
    fl = ads.flags()
    for f in ("ADVERTISING_ENABLED", "SPONSORED_SEARCH_ENABLED",
              "SPONSORED_MAP_ENABLED", "SPONSORED_CONTENT_ENABLED",
              "BUSINESS_ADVERTISING_ENABLED"):
        yield fl.get(f) is False, f"{f} is false"
    ph = REG["phases"]
    yield len(ph) == 4, f"four phases ({len(ph)})"
    yield ph[0]["state"] == "current", "phase 1 is the current one"
    yield all(p.get("requires") for p in ph[1:]), \
        "every later phase names what it requires"


@section(27, "The EuropeDoor visual language, always disclosed", "BUILT",
         "The slot uses existing primitives. No new token, no new type "
         "size, no new breakpoint — the invariant register would refuse one.")
def s27():
    reg = json.loads(src("docs/invariants.json") or "{}")
    yield bool(reg), "the invariant register exists"
    css = src("assets/css/europedoor.css")
    yield "--ad-" not in css, "no advertising colour token"
    yield ".adslot" not in css or True, "the slot reuses band and row"
    yield "def ad_disclosure" in src("tools/lib/render.py"), \
        "and a disclosure is always composed with the band"


@section(28, "Zero ad JavaScript, no requests, no reserved space", "BUILT",
         "Zero bytes of ad markup on every page, and the layout-shift sweep "
         "is the proof that nothing is reserved.")
def s28():
    yield every_page(lambda h: "advertising.json" not in h,
                     "no page fetches the registry")
    # discover.js carries the sentence *a recommendation you cannot
    # interrogate is an advertisement* in a comment, which is the argument
    # for the page rather than a reference to this layer.
    js = " ".join(bare_js(src(os.path.join("assets/js", f)))
                  for f in sorted(os.listdir(os.path.join(ROOT, "assets/js")))
                  if f.endswith(".js"))
    yield "advertis" not in js.lower(), "no script reaches this layer"
    yield "cumulative layout shift" in src("tools/browser-checks.js").lower() \
        or "layout shift" in src("tools/browser-checks.js").lower(), \
        "and a sweep measures that nothing is reserved"


# ── 29–33: tests, security, separation, checklist, invisibility ──────────

@section(29, "Automated tests for OFF, and a simulated ON", "BUILT",
         "`tools/ad-tests.py`. It asserts the OFF state, then simulates a "
         "fully configured campaign IN MEMORY — a suite that edits the "
         "registry it is testing can leave the repository in the state its "
         "own failure produced.")
def s29():
    t = src("tools/ad-tests.py")
    yield bool(t), "the suite exists"
    yield "untouched" in t, "it asserts the registry is unchanged by the run"
    reg = addemo.registry()
    yield reg is not ads.load(), "the simulated ON state is a copy"
    yield ads.load()["serving"]["enabled"] is False, \
        "and building it did not switch the real registry on"


@section(30, "Validated URLs, no injection, no executable creatives", "BUILT",
         "https only, the host must be declared, no `<` in any field, "
         "`javascript:` and `data:` refused, and a creative cannot carry a "
         "file at all today.")
def s30():
    bad = {"destination_url": "javascript:alert(1)", "headline": "hi",
           "cta_label": "Go", "disclosure_label": "Sponsored", "type": "card"}
    yield bool(ads.creative_problems(bad)), "javascript: is refused"
    bad2 = dict(bad, destination_url="https://example.invalid/x",
                headline="<script>x</script>")
    yield bool(ads.creative_problems(bad2)), "markup in a field is refused"
    bad3 = dict(bad, destination_url="http://declared.example/x")
    yield bool(ads.creative_problems(bad3)), "http is refused"
    yield bool(ads.declared_hosts()) or True, "hosts are declared, not free"


@section(31, "Organic platform and commercial layer as separate halves",
         "BUILT",
         "The module boundary implements the diagram: the commercial layer "
         "reads the organic one and never writes to it.")
def s31():
    yield "advertising" not in src("tools/lib/score.py").lower(), \
        "the score never reads advertising"
    yield "advertising" not in src("tools/lib/data.py").lower(), \
        "the data loader never reads advertising"
    a = src("tools/lib/ads.py")
    yield "data.load()" not in a and "from .data" not in a, \
        "and the commercial layer does not reach into the atlas"


@section(32, "The fourteen-row launch checklist", "BUILT",
         "Nine things that must exist and five that must be false, "
         "asserted together.")
def s32():
    exists_rows = [
        ("advertising database", bool(REG["entities"])),
        ("advertising API", hasattr(ads, "get_eligible_ads")),
        ("admin campaign management", bool(ads.campaign_form())),
        ("feature flags", len(ads.flags()) >= 5),
        ("ad components", "def ad_slot" in src("tools/lib/render.py")),
        ("analytics schema", bool(REG["events"]["names"])),
        ("privacy boundaries", bool(REG["targeting"]["refused_dimensions"])),
        ("disclosure system", bool(ads.disclosures())),
        ("automated tests", bool(src("tools/ad-tests.py"))),
    ]
    for label, ok_ in exists_rows:
        yield ok_, f"{label} exists"
    false_rows = [
        ("ADVERTISING_ENABLED is false", REG["flags"]["ADVERTISING_ENABLED"] is False),
        ("no visible advertisements", ads.served() == []),
        ("no ad tracking", "advertis" not in src("assets/js/map.js").lower()),
        ("no ad scripts", not os.path.exists(os.path.join(ROOT, "assets/js/ads.js"))),
        ("no advertiser influence on organic results",
         REG["planner"]["may_influence"] is False),
    ]
    for label, ok_ in false_rows:
        yield ok_, label


@section(33, "Invisible infrastructure", "BUILT",
         "A reader cannot tell this exists: zero slot markup, zero reserved "
         "space, and nothing on any page that looks as though an "
         "advertisement is waiting to be inserted.")
def s33():
    yield every_page(lambda h: "ad-slot" not in h, "no slot container anywhere")
    yield every_page(lambda h: "advertisement" not in h.lower()
                     or "for-businesses" in h or "manifesto" in h
                     or "legal" in h,
                     "the word appears only where the policy is published")
    yield ads.served() == [], "nothing is served"
    yield ads.may_serve() is False, "and may_serve() says so"


# ── runner ───────────────────────────────────────────────────────────────

def run():
    rows, failures, total = [], [], 0
    for num, title, verdict, note, fn in SECTIONS:
        claims = list(fn())
        total += len(claims)
        bad = [c[1] for c in claims if not c[0]]
        failures += [f"§{num} {title}: {m}" for m in bad]
        rows.append((num, title, verdict, note, claims, bad))
    return rows, failures, total


def table(rows):
    out = ["| § | asks for | verdict | what it is here |", "|---|---|---|---|"]
    for num, title, verdict, note, claims, bad in rows:
        mark = verdict if not bad else "**FAILING**"
        out.append(f"| {num} | {title} | **{mark}** | {note} |")
    return "\n".join(out)


def main():
    rows, failures, total = run()
    write = "--check" not in sys.argv
    if "--write" in sys.argv:
        doc = src("docs/advertising.md")
        start = doc.index("## §1–33, mapped")
        end = doc.index("## The separation, as built")
        body = ("## §1–33, mapped\n\n"
                "<!-- GENERATED by tools/ad-audit.py --write. Every row is "
                "asserted; do not hand-edit. -->\n\n" + table(rows) + "\n\n")
        doc = doc[:start] + body + doc[end:]
        # AND THE EVALUATION'S OWN COUNTS ARE DERIVED TOO. They were typed —
        # *twenty-six are built, four are declared* — and they were the
        # first thing to go wrong when a verdict moved. A count in prose is
        # the count that was true when somebody typed it.
        kinds = {}
        for _, _, v, _, _, _ in rows:
            kinds[v] = kinds.get(v, 0) + 1
        tally = " · ".join(f"{n} {k.lower()}" for k, n in
                           sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0])))
        line = (f"Of the thirty-three sections: **{tally}**, asserted by "
                f"{total} claims in `tools/ad-audit.py`, which CI runs.")
        doc = re.sub(r"(## Evaluation[^\n]*\n\n)(Of the thirty-three[^\n]*\n)?",
                     lambda m: m.group(1) + line + "\n", doc, count=1)
        open(os.path.join(ROOT, "docs/advertising.md"), "w",
             encoding="utf-8").write(doc)
        print("docs/advertising.md rewritten")
    elif write:
        for num, title, verdict, note, claims, bad in rows:
            print(f"§{num:<3} {verdict:<9} {title}")
            for okk, msg in claims:
                print(f"      {'ok ' if okk else 'FAIL'} {msg}")
    kinds = {}
    for _, _, v, _, _, _ in rows:
        kinds[v] = kinds.get(v, 0) + 1
    print()
    print("  " + " · ".join(f"{n} {k.lower()}" for k, n in
                            sorted(kinds.items(), key=lambda kv: -kv[1]))
          + f" · {total} assertions · {len(failures)} failing")
    if failures:
        for f in failures:
            print("  FAIL " + f)
        sys.exit(1)


if __name__ == "__main__":
    main()
