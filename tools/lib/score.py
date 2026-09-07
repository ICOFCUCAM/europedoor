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

DIMENSIONS = ["nature", "history", "food", "culture", "adventure", "value"]
LABELS = {
    "nature": "Nature", "history": "History", "food": "Food & table",
    "culture": "Culture", "adventure": "Adventure", "value": "Value",
}


def _clamp(v):
    return max(FLOOR, min(CAP, int(round(v))))


def value_score(daily_eur):
    """Cheap countries score high. €40/day → 92, €260/day → 26, linear between."""
    mid = (daily_eur[0] + daily_eur[1]) / 2.0
    return _clamp(110 - (mid - 40) * (84.0 / 220.0))


def city_scores(country, region, city):
    tags = set(city["interests"]) | set(region["interests"])
    kinds = [e["kind"] for e in city.get("experiences", [])]
    out = {}
    for dim, table in WEIGHTS.items():
        v = BASE + sum(pts for tag, pts in table.items() if tag in tags)
        support = sum(1 for k in kinds if k in KIND_SUPPORT[dim])
        v += min(support, 3) * 4
        out[dim] = _clamp(v)
    out["value"] = value_score(country["daily_eur"])
    return out


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
    rows.append((LABELS["value"], "110 − (midpoint of the country's daily cost band − €40) × 0.382"))
    return rows
