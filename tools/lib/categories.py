"""The experience category system.

The specification asks for eight core categories with sub-categories under
them. Six of those have a real signal in the dataset — the tags we authored
and the words we wrote. Two do not, and rather than fake them, they are
derived by a rule that is published on the page itself:

  * **Luxury** is simply the experiences priced high. Calling the expensive
    end "luxury" adds nothing; listing it as expensive is the honest version.
  * **Family** is a rule over kind, price band and hazard words. It is an
    editorial judgement about our own writing, in the same class as the
    `quiet` tag, and it is stated as one.

Keyword matching runs over the experience's own name and summary. That is
loose, so the pages say so and say what matched.
"""

from __future__ import annotations

import re

FAMILY_KINDS = ("museum", "ride", "water", "wild", "table", "workshop", "walk")
# Words that make an experience unsuitable to hand to a child, in our own
# copy. Deliberately blunt: it is better to exclude a fine one than to
# include a via ferrata.
FAMILY_EXCLUDE = (
    "ferrata", "exposure", "exposed", "glacier", "crampon", "rifle", "bear",
    "wine", "cellar", "brewery", "beer", "rakija", "whisky", "distiller",
    "vermouth", "bar ", "nightlife", "club", "sauna", "naked", "cold water",
    "rescue", "danger", "steep", "hours of", "sixteen kilometres", "ten hours",
    "1,200-metre", "mountaineering", "vertigo",
)


def text_of(exp, city=None):
    bits = [exp.get("name", ""), exp.get("summary", ""), exp.get("kind", "")]
    if city:
        bits.append(city.get("name", ""))
    return " ".join(bits).lower()


def matches_sub(exp, sub, city=None):
    t = text_of(exp, city)
    return any(re.search(r"\b" + re.escape(k.lower()), t) for k in sub["keywords"])


def is_family(exp):
    if exp.get("kind") not in FAMILY_KINDS:
        return False
    if exp.get("band") == "high":
        return False
    t = text_of(exp)
    return not any(w in t for w in FAMILY_EXCLUDE)


def is_luxury(exp):
    return exp.get("band") == "high"


def in_category(item, cat):
    """item: the dict all_experiences() yields."""
    exp = item["exp"]
    if cat.get("derived") == "family":
        return is_family(exp)
    if cat.get("derived") == "luxury":
        return is_luxury(exp)
    tags = set(item["city"]["interests"]) | set(item["region"]["interests"])
    if tags & set(cat.get("interests", [])):
        return True
    return any(matches_sub(exp, sub, item["city"]) for sub in cat.get("subs", []))


def select(items, cat, sub=None):
    out = [it for it in items if in_category(it, cat)]
    if sub:
        out = [it for it in out if matches_sub(it["exp"], sub, it["city"])]
    return out


def rule_text(cat):
    """What the page says about how its list was built."""
    if cat.get("derived") == "family":
        return ("Every experience whose kind is one of " + ", ".join(FAMILY_KINDS) +
                ", priced low or moderate, and whose own description contains none of "
                f"{len(FAMILY_EXCLUDE)} exclusion words — ferrata, glacier, rifle, cellar, "
                "sauna and the rest. It is a judgement about our own writing, not a "
                "certification, and it errs towards leaving good things out.")
    if cat.get("derived") == "luxury":
        return ("Every experience we priced in the high band. There is no separate luxury "
                "inventory and no partner arrangement behind this list — it is the "
                "expensive end of what is already in the Atlas, labelled as expensive.")
    return ("Anything in a place tagged " + ", ".join(cat.get("interests", [])) +
            ", plus anything whose own name or description matches one of the "
            f"{sum(len(s['keywords']) for s in cat.get('subs', []))} terms under the "
            "sub-categories below.")
