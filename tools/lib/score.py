"""The Europe Experience Score.

A score nobody can audit is a ranking nobody should trust, so this file is
the entire methodology and /method publishes it verbatim. Six dimensions,
0-100, computed from editorial tags and dataset facts — never hand-typed
per place, because hand-typed numbers drift and cannot be defended.

Two honest limits, stated on the page as well as here:
  * these are derived from our own tagging, not from measurement or from
    visitor surveys; they say what a place is *for*, not how good it is;
  * VALUE is the only dimension with an external anchor (the country's
    daily cost band). The rest are structural.
"""

from __future__ import annotations

# dimension -> {tag: points}. A tag may feed several dimensions.
WEIGHTS = {
    "nature":    {"nature": 26, "mountains": 22, "coast": 16, "islands": 12, "winter": 10, "wild": 6},
    "history":   {"history": 26, "sacred": 16, "architecture": 16, "art": 10, "cities": 4},
    "food":      {"food": 30, "wine": 22, "festivals": 6, "cities": 6},
    "culture":   {"art": 22, "architecture": 18, "music": 16, "design": 14, "festivals": 10, "sacred": 8},
    "adventure": {"mountains": 24, "nature": 18, "coast": 14, "winter": 16, "islands": 10, "rail": 6},
}
# Experience kinds that corroborate a dimension: doing beats tagging.
KIND_SUPPORT = {
    "nature":    ("walk", "wild", "water"),
    "history":   ("museum", "sacred"),
    "food":      ("table", "cellar"),
    "culture":   ("museum", "stage", "workshop"),
    "adventure": ("walk", "water", "ride"),
}
BASE = 34
CAP = 97          # nothing scores 100; there is always somewhere better at something
FLOOR = 12

DIMENSIONS = ["nature", "history", "food", "culture", "adventure", "family",
              "authenticity", "value"]
LABELS = {
    "nature": "Nature", "history": "History", "food": "Food & table",
    "culture": "Culture", "adventure": "Adventure", "family": "Family",
    "authenticity": "Authenticity", "value": "Value",
}

# The specification lists ten dimensions. Two of them are refused rather than
# approximated, and the refusal is published on /method:
#
#   Accessibility — we hold no step-free access, hearing-loop or accessible-
#     toilet data for any place in the Atlas. A score derived from anything
#     else would be a guess about whether a disabled traveller can get in,
#     which is the worst possible thing to guess about.
#   Romance — not measurable from anything in this dataset without inventing
#     a proxy and calling it evidence.
REFUSED = {
    "Accessibility": (
        "We hold no step-free access, hearing-loop or accessible-toilet data for any place "
        "in the Atlas. Deriving a number from something else would be a guess about whether "
        "a disabled traveller can get in, and that is the worst thing on this list to guess "
        "about. The gap is stated on every place page and on /accessibility."),
    "Romance": (
        "Not measurable from anything in this dataset. Any formula would be a proxy — sunsets, "
        "coastlines, small hotels — dressed up as evidence, and the number would be doing "
        "persuasion rather than description."),
}

# Family: kinds a child can be handed, and the words that rule one out. This
# mirrors the rule the /experiences/family page publishes.
FAMILY_TAGS = {"nature": 14, "coast": 14, "history": 8, "islands": 8, "wild": 12, "winter": 6}
FAMILY_MINUS = {"music": 10}
AUTHENTIC_KINDS = ("workshop", "table", "wild", "cellar")


def _clamp(v):
    return max(FLOOR, min(CAP, int(round(v))))


def value_score(daily_eur):
    """Cheap countries score high. €40/day → 92, €260/day → 26, linear between."""
    mid = (daily_eur[0] + daily_eur[1]) / 2.0
    return _clamp(110 - (mid - 40) * (84.0 / 220.0))


def family_score(country, region, city):
    """What a child would get out of it, from tags and from the experiences
    that pass the family rule published at /experiences/family."""
    from . import categories as C
    tags = set(city["interests"]) | set(region["interests"])
    v = BASE + sum(p for t, p in FAMILY_TAGS.items() if t in tags)
    v -= sum(p for t, p in FAMILY_MINUS.items() if t in tags)
    ok_exp = sum(1 for e in city.get("experiences", []) if C.is_family(e))
    v += min(ok_exp, 3) * 5
    return _clamp(v)


def authenticity_score(country, region, city):
    """How much of the place is still for the people who live there.

    Derived, and arguable: the quiet tag, not being the capital, and
    experiences that are somebody's actual trade rather than a performance.
    Published on /method so it can be argued with rather than trusted."""
    v = BASE + 10
    if city.get("quiet"):
        v += 22
    if city["name"] != country["capital"]:
        v += 8
    if "cities" in city["interests"]:
        v -= 8
    trades = sum(1 for e in city.get("experiences", []) if e["kind"] in AUTHENTIC_KINDS)
    v += min(trades, 3) * 6
    v += min(len(city.get("places", [])), 4) * 2
    return _clamp(v)


def city_scores(country, region, city):
    tags = set(city["interests"]) | set(region["interests"])
    kinds = [e["kind"] for e in city.get("experiences", [])]
    out = {}
    for dim, table in WEIGHTS.items():
        v = BASE + sum(pts for tag, pts in table.items() if tag in tags)
        support = sum(1 for k in kinds if k in KIND_SUPPORT[dim])
        v += min(support, 3) * 4
        out[dim] = _clamp(v)
    out["family"] = family_score(country, region, city)
    out["authenticity"] = authenticity_score(country, region, city)
    out["value"] = value_score(country["daily_eur"])
    return out


# ── discoverability ──────────────────────────────────────────────────
#
# "Hidden Europe" was an editorial tag: somebody decided a place was quiet
# and wrote it down. That is a defensible way to start and an indefensible
# way to stay, because it makes the most interesting claim on the site the
# one nobody can check.
#
# This is the computed version. It answers a narrow question — **how far is
# this place from being obvious?** — and it is deliberately NOT a quality
# score. A high discoverability does not mean better; it means fewer people
# will have told you about it.
#
# What we can honestly use, and what we cannot:
#
#   we DO NOT have visitor numbers, search volume, hotel occupancy or any
#   other measure of how busy anywhere actually is. Every crowd-data
#   product is licensed, and inventing a proxy for it and calling it
#   evidence is the thing this project exists not to do.
#
#   we DO have: whether a place is a capital, how big a country's whole
#   dataset is, how many curated routes pass through it, how many of the
#   famous-by-default tags it carries, and whether an editor who knows the
#   region marked it quiet.
#
# So the score measures OBSCURITY WITHIN OUR OWN ATLAS, which is a smaller
# and truer claim than "undiscovered". The page says exactly that.
DISCOVER_TERMS = (
    ("Not the capital", 22,
     "A capital is where a first visit goes. Everything else has to be chosen."),
    ("Editorially quiet", 24,
     "An editor who knows the region marked it as somewhere that stays quiet "
     "in season. This is the one judgement in the score, and it is a person's."),
    ("Few curated routes pass through", 18,
     "Our own journeys are a proxy for the obvious circuit. A place none of "
     "them reaches is off it."),
    ("Not tagged for the famous things", 20,
     "Cities, art and architecture are what a continent is famous for. Nature, "
     "wild and sacred are what people find later."),
    ("In a country we have written thinly", 16,
     "Where the Atlas itself is thin, the place is very likely thin in every "
     "other guide too — which is either a gap or an opportunity, and the "
     "content report says which."),
)
OBVIOUS_TAGS = ("cities", "art", "architecture")


def discoverability(country, region, city, *, journeys_through=0, country_cities=0):
    """0-100: how far this place is from being the obvious choice.

    Not a quality score, and not a crowd measurement — see the note above.
    Every term is listed on /method with the points it can contribute.
    """
    tags = set(city["interests"]) | set(region["interests"])
    v = 0
    fired = []
    if city["name"] != country.get("capital"):
        v += 22; fired.append("Not the capital")
    if city.get("quiet"):
        v += 24; fired.append("Editorially quiet")
    if journeys_through == 0:
        v += 18; fired.append("Few curated routes pass through")
    elif journeys_through == 1:
        v += 9
    obvious = sum(1 for t in OBVIOUS_TAGS if t in tags)
    if obvious == 0:
        v += 20; fired.append("Not tagged for the famous things")
    elif obvious == 1:
        v += 10
    if country_cities and country_cities <= 4:
        v += 16; fired.append("In a country we have written thinly")
    elif country_cities and country_cities <= 6:
        v += 8
    return _clamp(v), fired


def country_scores(country):
    """A country scores as the mean of its cities, so a country cannot be
    stronger on a dimension than the places you would actually visit."""
    cities = [(r, t) for r in country["regions"] for t in r["cities"]]
    acc = {d: 0 for d in DIMENSIONS}
    for r, t in cities:
        s = city_scores(country, r, t)
        for d in DIMENSIONS:
            acc[d] += s[d]
    return {d: _clamp(acc[d] / max(1, len(cities))) for d in DIMENSIONS}


def methodology_rows():
    """Rendered on /method. If the table above changes, that page changes."""
    rows = []
    for dim in ["nature", "history", "food", "culture", "adventure"]:
        parts = ", ".join(f"{t} +{p}" for t, p in sorted(WEIGHTS[dim].items(), key=lambda kv: -kv[1]))
        support = ", ".join(KIND_SUPPORT[dim])
        rows.append((LABELS[dim], f"base {BASE}; {parts}; +4 per matching experience (max 3), kinds: {support}"))
    fam = ", ".join(f"{t} +{p}" for t, p in sorted(FAMILY_TAGS.items(), key=lambda kv: -kv[1]))
    rows.append((LABELS["family"],
                 f"base {BASE}; {fam}; music & nightlife −10; +5 per experience (max 3) that "
                 f"passes the family rule published at /experiences/family"))
    rows.append((LABELS["authenticity"],
                 f"base {BASE} + 10; quiet +22; not the capital +8; tagged big-city −8; "
                 f"+6 per experience (max 3) of kind {', '.join(AUTHENTIC_KINDS)}; "
                 f"+2 per recorded place (max 4)"))
    rows.append((LABELS["value"], "110 − (midpoint of the country's daily cost band − €40) × 0.382"))
    return rows
