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
    """A sub-category keyword describes the EXPERIENCE, not the town it sits in.

    `city` is accepted and ignored, and that is the fix rather than an
    oversight. It used to be searched, and because the keywords are matched
    as prefixes — deliberately, so `monaster` catches monasteries and
    `archaeolog` catches archaeological — a place name would satisfy them:

        \bhall  matched Hallstatt   -> a salt mine listed under Markets
        \bwar   matched Warsaw      -> a museum listed under Modern history
        \bport  matched Portree     -> a ridge walk listed under Cellars
        \bsnow  matched Snowdonia   -> a slate railway listed under Skiing

    Eight of 423 listings across the 40 sub-pages came in this way. Five were
    plainly wrong and three were defensible (Plitvice Lakes under lakes), and
    a rule that is right three times in eight is not a rule. Dropping the
    city empties no page. A trailing \b was the other candidate and was
    rejected: it would break the four keywords that are stems on purpose.
    """
    t = text_of(exp)
    return any(re.search(r"\b" + re.escape(k.lower()), t) for k in sub["keywords"])


def live_keywords(sub, texts):
    """Which of a sub-category's terms have actually matched something, and
    which are declared and idle.

    113 of 261 keywords across the 38 sub-categories match nothing in the
    197 experiences this atlas holds — puffin, kayak, bauhaus, quattrocento,
    holocaust. That is NOT the dead-vocabulary defect the motifs and the
    sub-categories had: a keyword costs nothing when it matches nothing, it
    ships no URL and no empty page, and deleting "puffin" would delete the
    intent to write about puffins.

    The defect is what the page SAYS. Every sub-page printed its full term
    list — "Selected by name and description against: wine, cellar,
    vineyard, qvevri, port, champagne, riesling, harvest…" — as though all
    fourteen had done work, when champagne and riesling have never selected
    anything. A published rule that overstates itself is worse than an
    unpublished one, because a reader can check it and will find it wrong.

    So the page prints both halves, and the idle half is a content report a
    reader can act on: it is a list of things nobody has written about yet.
    """
    live, idle = [], []
    for k in sub["keywords"]:
        pat = re.compile(r"\b" + re.escape(k.lower()))
        (live if any(pat.search(t) for t in texts) else idle).append(k)
    return live, idle


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
    """A category describes the EXPERIENCE, not the town it sits in.

    THE SAME MISTAKE AS THE CITY NAME, ONE LEVEL UP, AND FAR LARGER. This
    used to open with:

        tags = city["interests"] | region["interests"]
        if tags & cat["interests"]: return True

    so a destination tagged `food` put every experience in it under Food &
    drink. The category page for food opened with a five-storey nuclear
    bunker in Tirana, chant in a rock-cut chamber in Geghard, a manuscript
    library in Yerevan and standing room at the Vienna Staatsoper before it
    reached a heuriger. Measured across all six real categories:

        Nature      147 listed,  32 matched their own words   115 from tags
        Adventure   173          117                           56
        Culture     147          61                            86
        History     167          33                           134
        Food        139          48                            91
        Faith        93          59                            34

    866 listings from 197 experiences — 4.4 categories each, which is the
    arithmetic of a taxonomy that has stopped discriminating. A property of
    the CONTAINER cannot establish a claim about the ITEM, and this is the
    same rule that took the town's name out of matches_sub eight listings
    ago; here it was 516.

    What replaces it is the experience's own authored classification. `kind`
    is one of ten values written per experience — table, cellar, museum,
    stage, workshop, walk, water, ride, wild, sacred — and the categories now
    declare which kinds belong to them in data/taxonomy.json. That is
    authoring a classification, which this repository allows, rather than
    inferring one from a neighbour, which is what the tag pass did.

    368 listings, 1.9 per experience, and every one of the 197 still lands
    somewhere: nothing was orphaned by the change.
    """
    exp = item["exp"]
    if cat.get("derived") == "family":
        return is_family(exp)
    if cat.get("derived") == "luxury":
        return is_luxury(exp)
    if exp.get("kind") in set(cat.get("kinds") or ()):
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
    kinds = cat.get("kinds") or []
    kindbit = ("Everything we classified as " + ", ".join(kinds) + ", plus a"
               if kinds else "A")
    return (kindbit + "nything whose own name or description matches one of the "
            f"{sum(len(s['keywords']) for s in cat.get('subs', []))} terms under the "
            "sub-categories below. Both tests are about the experience itself. "
            "Neither the name of the town nor the interests the town is tagged "
            "with can put something in this list: a salt mine in Hallstatt is "
            "not a market, and a bunker museum in a city known for its food is "
            "not a meal.")
