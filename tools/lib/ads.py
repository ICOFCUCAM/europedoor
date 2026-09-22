"""The commercial layer: nine placements, five flags, nothing serving.

WHAT THE HARD PART IS. Not rendering a card — keeping "which parts of this
page were bought" answerable by a reader rather than only true in a contract.
The Stay layer solved that for one referral: a mechanism plus a credential,
the state read off the paperwork, and the disclosure inseparable from the
thing it discloses. This is that, generalised, with the switches off.

FIVE CONDITIONS, BECAUSE ONE FLAG IS NEVER THE WHOLE GATE.

    1. an operating entity exists          serving.entity            null
    2. serving is switched on              serving.enabled           false
    3. the placement's own flag is on      flags[placement.flag]     false x5
    4. the placement is enabled            placements[].enabled      false x9
    5. the campaign carries a signed order campaign.insertion_order  no campaigns

The specification asks for `ADVERTISING_ENABLED=false` in the environment.
This is a field in a committed registry instead, which is stronger: an
environment variable can be flipped without a commit, a review or a diff.
The sister repository records what one word costs — its `status: 'active'`
became inert the day a real compliance ladder was built, and its own notes
say guarding the wrong word is worse than guarding nothing.

AND AN OFF SLOT EMITS ZERO BYTES — no container, no placeholder, no reserved
height. That is the OPPOSITE of `ed_slot()` and for the opposite reason:
there the reader is an editor and the declared photograph surface IS the
acquisition list, here the reader is a traveller and a reserved advertising
box on a page with no advertiser is this product advertising that it would
like to carry advertising. §33 asks that nothing look as though ads are
waiting to be inserted, and zero bytes is the only version of that which a
check can hold. The architecture is published on /for-businesses, which is
the page an advertiser reads.

See docs/advertising.md for §1-33 mapped against what is built.
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_cache = None


def load():
    global _cache
    if _cache is None:
        with open(os.path.join(ROOT, "data", "advertising.json"), encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


# ── the vocabularies, exported so a check reads them rather than retyping ──

def disclosures():
    return tuple(load()["disclosures"])


def refused_campaign_keys():
    # And the creative file, for as long as the licence register cannot
    # express an advertiser's grant. See `refusals.creative_file`.
    return tuple(load()["refusals"]["campaign_keys"]) + (
        "image_url_file", "creative_image", "upload")


def statuses():
    return tuple(load()["statuses"])


def flags():
    # `$comment` keys carry the reasoning and are not flags. A dict that
    # returns its own documentation as a flag is the instrument-reads-its-
    # own-documentation fault this repository records seven times, arriving
    # in a registry rather than in a regex.
    return {k: v for k, v in load()["flags"].items() if not k.startswith("$")}


def entity():
    return load()["serving"].get("entity")


def wall():
    """Where the wall between editorial and commerce currently stands.

    Published at /for-businesses, whose own sentence is the procedure: if it
    ever moves, it moves in public, on that page. `checks.py` asserts the
    page and this agree IN BOTH DIRECTIONS, because either drifting alone is
    the failure — a page can keep a promise the mechanism has stopped
    keeping, and a mechanism can be quietly stricter than the page a reader
    is reading.
    """
    return load()["wall"]


# ── §1's status block, derived so the claim cannot drift ──────────────────

def status():
    """The eight lines §1 asks a launch to be able to state, derived.

    A status block typed into a page is a status block that was true on the
    day somebody typed it. Every line here is read off the registry, so
    switching one thing on changes the published sentence in the same build.
    """
    reg = load()
    on = [p["slug"] for p in reg["placements"] if p.get("enabled")]
    return [
        ("Advertising system", "built"),
        ("Ad inventory", f"{len(reg['placements'])} placements configured"),
        ("Campaign database", "ready" if reg["entities"]["campaigns"] else "absent"),
        ("Business advertising", "ready"),
        ("Analytics", f"{len(reg['events']['names'])} events defined"),
        ("Ad serving", "enabled" if may_serve() else "disabled"),
        ("Paid placements", f"{len(on)}" if on else "none"),
        ("Visible ads", f"{len(served())}" if served() else "none"),
    ]


# ── §25's AdvertisingService, as eight functions ──────────────────────────

def conditions(campaign=None):
    """Every condition between a campaign and a reader, with its verdict.

    ONE DECLARATION, DERIVED PROSE. The first version of this module said
    "five conditions" in its docstring, /for-businesses said "five separate
    conditions" in a lede and listed five, and `may_serve()` actually tested
    EIGHT — the two per-placement flags and the campaign's own status were in
    the mechanism and in neither sentence. That is a number typed in three
    places disagreeing with the thing it describes, which is the dispatch
    cap's own failure (four copies, and the one that was a gate was the one
    left behind) and the projection's (`/map` printed the old name for a
    year). The list is here, `may_serve()` is `all()` over it, the page
    prints it, and `ad-tests.py` proves each one alone refuses.
    """
    reg = load()
    pl = placement((campaign or {}).get("placement")) if campaign else None
    sf = surface(pl["page_type"]) if pl else None
    return [
        ("an operating entity exists", bool(entity())),
        ("serving is switched on", bool(reg["serving"].get("enabled"))),
        ("the global flag is set",
         bool(reg["flags"].get("ADVERTISING_ENABLED"))),
        ("a campaign exists to serve", campaign is not None),
        ("its placement is enabled", bool(pl and pl.get("enabled"))),
        ("that placement's own flag is set",
         bool(pl and reg["flags"].get(pl.get("flag")))),
        ("the surface it sits on is enabled", bool(sf and sf.get("enabled"))),
        ("the campaign is active",
         bool(campaign and campaign.get("status") == "active")),
        ("it carries a signed insertion order",
         bool(campaign and campaign.get("insertion_order"))),
    ]


def may_serve(campaign=None):
    """Would this campaign be served? Today: no, nine times over."""
    return all(v for _, v in conditions(campaign))


def get_eligible_ads(context):
    """§25's `getEligibleAds(context)`. The one function a page builder calls.

    `context` is what `context_for()` produced from the path. Returns the
    campaigns that would render, in order, capped at the placement's own
    `max_items` — which is why a page builder cannot become the thing that
    decides whether advertising appears, or how much of it.
    """
    out = []
    for c in load()["campaigns"]:
        pl = placement(c.get("placement"))
        if not pl or pl["page_type"] != context.get("page_type"):
            continue
        if not _targets_match(c.get("targets", {}), context):
            continue
        if not may_serve(c):
            continue
        out.append(c)
    pl = next((p for p in load()["placements"]
               if p["page_type"] == context.get("page_type")), None)
    cap = pl.get("max_items", 1) if pl else 1
    return out[:cap]


def record_impression(campaign_slug):
    """§25 and §16. Fires nowhere, and says why rather than silently passing."""
    if not load()["events"]["firing"]:
        return None
    raise NotImplementedError(
        "events.firing is true and there is no analytics pipeline in this "
        "product to receive an impression — docs/legal-position.md records "
        "why no analytics runs at all")


def record_click(campaign_slug):
    return record_impression(campaign_slug)


def get_campaign(slug):
    for c in load()["campaigns"]:
        if c.get("slug") == slug:
            return c
    return None


def _write_refused(what):
    """The four write methods raise rather than returning a falsy value.

    A write that quietly does nothing is a write somebody builds a UI on top
    of. This repository has the same rule about `stay.inventory()`, which
    returns nothing and whose callers draw the reading instead of an empty
    frame — the difference is that a read of nothing is a state and a write
    of nothing is a lie.
    """
    raise PermissionError(
        f"{what} is refused: {load()['serving']['gate']}")


def create_campaign(**kw):
    _write_refused("creating a campaign")


def update_campaign(slug, **kw):
    _write_refused("updating a campaign")


def approve_campaign(slug):
    _write_refused("approving a campaign")


def pause_campaign(slug):
    _write_refused("pausing a campaign")


# ── §7's contextual targeting ─────────────────────────────────────────────

# ONE ROUTE TABLE, NOT TWO. `render.ed_family()` already maps a path to a
# page family and this reads the same shapes, because a context and a family
# that disagree is the fourteen-call-sites-forgot-the-motif failure in a new
# place. Order matters for the same reason it does there: `/experiences/<c>`
# is a category and `/experiences` is the index.
def context_for(path):
    """What a page is ABOUT, from its path. No user, no profile, no history.

    §7's whole point: the system can know that a reader is looking at Bergen
    in Norway without knowing anything about the reader. There is nothing in
    this product to know anyway — no account, no session, no cookie, no
    analytics, and three localStorage keys that never leave the browser.
    """
    p = (path or "/").rstrip("/") or "/"
    parts = [x for x in p.split("/") if x]
    ctx = {"path": p, "page_type": None}
    if p == "/":
        ctx["page_type"] = "homepage"
    elif parts[0] == "europe" and len(parts) == 2:
        ctx.update(page_type="country", country=parts[1])
    elif parts[0] == "europe" and len(parts) == 3:
        ctx.update(page_type="region", country=parts[1], region=parts[2])
    elif parts[0] == "europe" and len(parts) == 4:
        ctx.update(page_type="destination", country=parts[1],
                   region=parts[2], destination=parts[3])
    elif parts[0] == "experiences" and len(parts) >= 2:
        ctx.update(page_type="experience", experience_category=parts[1])
    elif parts[0] == "journeys" and len(parts) == 2:
        ctx.update(page_type="journey", journey=parts[1])
    elif parts[0] == "stories":
        ctx["page_type"] = "stories"
    elif parts[0] == "search":
        ctx["page_type"] = "search"
    elif parts[0] == "map":
        ctx["page_type"] = "map"
    return ctx


# WHAT `context_for()` CAN ACTUALLY SUPPLY, which is not all six.
# `travel_interest` is a property of the destination rather than of the path,
# so it needs the page builder to hand its own tags over; `language` needs a
# second locale, and `SHIP_THRESHOLD` is 1.0 with one at 100%. Both are
# declared because the brief's vocabulary is right, and both are UNREACHABLE
# today — which is the state that goes wrong quietly, because a target on
# one of them returns no match and reports nothing. Named here so a campaign
# written against one is refused out loud rather than silently never served.
CONTEXT_DIMENSIONS = ("country", "region", "destination", "experience_category")
TRIGGERS = {
    "travel_interest": "travel_interest needs the page builder to hand over its own tags, because a path does not carry them.",
    "language": "language needs a second locale reaching SHIP_THRESHOLD, which is 1.0 with one at 100%.",
}


def _targets_match(targets, ctx):
    dims = load()["targeting"]["dimensions"]
    for k, v in targets.items():
        if k not in dims:
            return False
        if k not in CONTEXT_DIMENSIONS:
            trigger = TRIGGERS.get(k, "no trigger recorded")
            raise NotImplementedError(
                f"a campaign targets {k!r}, which is a declared dimension "
                f"that context_for() cannot supply: a target that can never "
                f"match must not look like a target that did not match. "
                f"{trigger}")
        want = v if isinstance(v, list) else [v]
        if ctx.get(k) not in want:
            return False
    return True


# ── the tables ────────────────────────────────────────────────────────────

def positions():
    """§5's `position` vocabulary, and the reason each value exists."""
    return (load().get("positions") or {}).get("vocabulary") or {}


def position_name(placement):
    """Where this placement sits in its document.

    §5 LISTS `position` AS A PLACEMENT FIELD AND THE NINE CARRIED NONE.
    `serving.slot_position` answered it once for the whole registry — and
    that answer is true of seven of the nine and false of the two with an
    objection attached: a sponsored search result below the organic ones is
    not "before the footer", and a sponsored map marker is on the drawing or
    it is not a map placement. One global answer to a per-placement question
    is how those two came to share a position with the seven that cannot
    have it.
    """
    return (placement or {}).get("position") or ""


def inventory():
    """§19's products. Six, and the map claimed five.

    Five of them are a placement each; a SEASONAL CAMPAIGN is not a slot at
    all — it is a campaign whose window is the product, bought against
    several placements — so declaring it as a tenth placement would have
    been the shape of the data deciding the taxonomy. It is a campaign type,
    and `campaign_type` was a declared field with no vocabulary behind it,
    which is exactly what let the sixth product go missing.
    """
    return (load().get("inventory") or {}).get("products") or []


def campaign_types():
    """The closed vocabulary for `campaigns.campaign_type`, derived.

    From `inventory.products` rather than typed a second time: a second list
    is a second chance for the two to disagree, which this repository has
    paid for in a token name, a dispatch cap and a credential scan.
    """
    return [p["slug"] for p in inventory()]


def campaign_form():
    """§13's creation form, as a declaration rather than a UI.

    `docs/advertising.md` claimed *the shape it would submit is in the
    registry, so the form has something to be checked against* and there was
    no such shape anywhere — a comment claiming evidence, in the file whose
    subject is disclosure. Every field names where its value comes from, so
    a form built later against an admin backend is checkable field by field
    instead of believed.
    """
    return (load().get("admin") or {}).get("campaign_form") or []


def admin_areas():
    """§12's seven areas, declared and unbuilt. See `admin.gate`."""
    return (load().get("admin") or {}).get("areas") or []


def placements():
    return load()["placements"]


def placement(slug):
    for p in load()["placements"]:
        if p["slug"] == slug:
            return p
    return None


def surfaces():
    return load()["surfaces"]


def surface(slug):
    for s in load()["surfaces"]:
        if s["slug"] == slug:
            return s
    return None


def campaigns():
    return load()["campaigns"]


def served():
    """Every campaign that would render anywhere. Empty, by construction."""
    return [c for c in load()["campaigns"] if may_serve(c)]


def for_surface(page_type):
    """What a page builder calls. Empty for every surface today."""
    return get_eligible_ads({"page_type": page_type})


# ── §14's approval workflow ───────────────────────────────────────────────

def may_transition(frm, to):
    """A business may never publish advertising instantly.

    The only route to `active` runs through a review somebody performed, and
    a transition the table does not name is refused rather than merely
    discouraged.
    """
    t = load()["transitions"]
    if frm not in t or not isinstance(t[frm], list):
        return False
    return to in t[frm]


def transition_needs_reason(to):
    return to == "rejected"


# ── §30's creative validation ─────────────────────────────────────────────

def creative_problems(creative):
    """Everything wrong with a creative, in one pass.

    An advertiser may never supply markup or a script. That is enforced twice:
    there is no field that could carry one, and the characters that would
    smuggle one into a field that carries words are refused. The URL must be
    https and its host must be declared exactly as a Stay provider's is —
    which is what pins the set of external hosts to a registry rather than to
    whatever an advertiser typed.
    """
    reg = load()
    rules = reg["creative_rules"]
    bad = []
    for field in ("headline", "description", "cta_label", "disclosure_label"):
        v = creative.get(field) or ""
        for token in rules["refused_in_text"]:
            if token.lower() in str(v).lower():
                bad.append(f"{field} contains {token!r}")
    if len(creative.get("headline") or "") > rules["max_headline"]:
        bad.append("headline is over the declared maximum")
    if len(creative.get("description") or "") > rules["max_description"]:
        bad.append("description is over the declared maximum")
    url = creative.get("destination_url") or ""
    if url and not url.startswith("https://"):
        bad.append("destination_url is not https")
    if url:
        host = re.sub(r"^[a-z]+://", "", url).split("/")[0]
        if host not in declared_hosts():
            bad.append(f"destination_url host {host!r} is not a declared host")
    if creative.get("image_url"):
        bad.append("image_url is set: " + reg["refusals"]["creative_file"][:80])
    if creative.get("type") in reg["creative_types_refused"]:
        bad.append(f"type {creative['type']!r} is refused")
    elif creative.get("type") not in reg["creative_types"]:
        bad.append(f"type {creative.get('type')!r} is not a declared type")
    if creative.get("disclosure_label") not in reg["disclosures"]:
        bad.append("disclosure_label is not one of " + str(reg["disclosures"]))
    return bad


def declared_hosts():
    """Every outbound host a paid link may reach. One registry, not two.

    A paid link leaves this origin exactly as a Stay referral does, which is
    the mechanism `checks.py` already pins: nothing may NAVIGATE to another
    origin unless the host is declared and enabled, and it carries
    `rel="sponsored nofollow noopener"` in a new tab.
    """
    return {a.get("host") for a in load()["advertisers"] if a.get("host")}


def refused_networks():
    return tuple(load()["refusals"]["third_party_networks"])
