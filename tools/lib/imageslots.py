"""A SLOT IS A TEMPLATE; A PURPOSE IS AN INSTANCE OF ONE.

`data/image-purposes.json` declared twelve purposes and every one of them was
one surface on ONE page. That is right for the surfaces there is exactly one
of — the homepage hero, the four doors, the five index openings — and it does
not scale at all for the ones there are hundreds of: `vienna-destination` and
`chamonix-destination` were two hand-written rows saying the same thing about
two of 319 destination pages, and the other 317 had no slot, so a photograph
could not be acquired for them at all.

The Media Desk brief names the shape: a `purpose` and a `target`, a template
and an instance. That is what this module is.

    slots()                      the templates
    declared()                   the one-of-a-kind purposes, unchanged
    targets(slot, data)          every entity that slot can be filled for
    resolve(name, data)          a spec for `slot@target` OR a declared purpose
    names(data)                  every purpose that could exist today

FOUR TEMPLATES NOW, AND EACH ONE ARRIVED WITH A CONTAINER RATHER THAN BEFORE
ONE. A slot nobody can fill is the thing `$requirements` refuses: this site
renders a photograph only where the markup has somewhere to put it, so
declaring `country-hero` meant BUILDING the country band first and declaring
the slot second. Three of the four vary per entity — a destination, a place
inside one, a story — and the fourth is the country, which was the largest
family on the site with no photograph anywhere: fifty pages of about seven
thousand pixels each.

A region page, an experience and a journey still have none, and their roles
carry a trigger naming the container that would create a purpose. The note
against `/plan` says the same thing in one sentence: the honest answer is no
slot rather than a slot nobody should fill.

THE INSTANCE NAME CARRIES BOTH HALVES. `destination-hero@france/the-alps/
chamonix` says which template and which entity, and the register key is
derived from the template rather than typed — so a row cannot claim a key the
slot would not produce.
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = os.path.join(ROOT, "data", "image-purposes.json")

SEP = "@"

# WHICH DATASET KEY EACH SOURCE READS, because they are not the same word.
# `places` is derived from `cities` rather than being a key of its own, so a
# guard written against the source NAME reported a missing `places` on a
# dataset that had everything it needed. Stated once, here, rather than
# inferred at each use.
SOURCE_KEY = {
    "countries": "countries",
    "regions": "countries",      # a region lives inside its country
    "cities": "cities",
    "places": "cities",
    "stories": "stories",
    "journeys": "journeys",
    "interests": "interests",
    "macros": "macros",
    "themes": "themes",
    "categories": "categories",
}


def _regions(data):
    """(country, region) pairs as `country/region`.

    A REGION IS NOT A TOP-LEVEL COLLECTION and that is the whole reason this
    function exists: regions live inside their countries, so the target has
    to carry both halves or `provence` and `the-valleys` would collide across
    fifty countries. It is the same shape `places` already uses one level
    down.
    """
    out = []
    for cs, c in data["countries"].items():
        for r in c.get("regions", []):
            out.append(f"{cs}/{r['slug']}")
    return sorted(out)


def _slugs(coll):
    """A COLLECTION IS A LIST OR A DICT HERE, AND BOTH ARE LOAD-BEARING.
    `interests` is keyed by slug and everything else is a list of records
    carrying one, so a single reader that assumed either shape would have
    been right about five of six — which is exactly the kind of near-miss
    that ships. Stated once, here."""
    if isinstance(coll, dict):
        return list(coll)
    return [r["slug"] for r in coll]


def _by_slug(coll, target):
    if isinstance(coll, dict):
        row = coll.get(target)
        if row is None:
            raise KeyError(target)
        return row if isinstance(row, dict) else {"name": row, "slug": target}
    for r in coll:
        if r.get("slug") == target:
            return r
    raise KeyError(target)


def _doc():
    with open(SPEC, encoding="utf-8") as fh:
        return json.load(fh)


def slots():
    """The templates. Keyed by slot name."""
    return _doc().get("slots", {})


def declared():
    """The one-of-a-kind purposes. Keyed by purpose name."""
    return _doc().get("purposes", {})


def targets(slot, data):
    """Every entity this slot can be filled for, as target strings.

    The source is the ATLAS rather than a list in the spec file, because a
    list of 319 destination ids typed into a JSON file is a list that is
    wrong the first time somebody adds a destination — the same reason
    `roles.purposes_today` is derived and `/themes` stopped printing "8
    places" on thirteen cards.
    """
    kind = slot.get("targets")
    # A MISSING SOURCE MUST SAY SO IN WORDS. Several callers hand this module
    # a PARTIAL dataset — the validator builds one from two indexes — so a
    # slot naming a source that caller did not include used to surface as a
    # bare KeyError from inside a loop, with nothing saying which key or
    # which slot. Adding `country-hero` produced exactly that.
    need = SOURCE_KEY.get(kind)
    if need and need not in data:
        raise KeyError(
            f"slot targets {kind!r}, which reads data[{need!r}], and the "
            f"dataset handed to imageslots has no {need!r} — a caller "
            f"building a partial dataset has to include every source a slot "
            f"can name")
    if kind == "countries":
        return sorted(data["countries"])
    if kind == "regions":
        return _regions(data)
    if kind in ("journeys", "interests", "macros", "themes", "categories"):
        return sorted(_slugs(data[kind]))
    if kind == "cities":
        return sorted(data["cities"])
    if kind == "places":
        out = []
        for cid, n in data["cities"].items():
            for pl in n["city"].get("places", []):
                out.append(f"{cid}/{pl['slug']}")
        return sorted(out)
    if kind == "stories":
        return sorted(s["slug"] for s in data["stories"])
    raise KeyError(f"slot targets {kind!r} is not a source this module knows")


def label(slot_name, target, data):
    """What a person calls this instance — the entity's own name."""
    slot = slots()[slot_name]
    kind = slot.get("targets")
    if kind == "countries":
        return data["countries"][target]["name"]
    if kind == "regions":
        cs, _, rs = target.partition("/")
        c = data["countries"][cs]
        return f"{_by_slug(c['regions'], rs)['name']}, {c['name']}"
    if kind in ("journeys", "interests", "macros", "themes", "categories"):
        return _by_slug(data[kind], target)["name"]
    if kind == "cities":
        n = data["cities"][target]
        return f"{n['city']['name']}, {n['country']['name']}"
    if kind == "places":
        cid, _, sl = target.rpartition("/")
        n = data["cities"][cid]
        for pl in n["city"].get("places", []):
            if pl["slug"] == sl:
                return f"{pl['name']}, {n['city']['name']}"
        raise KeyError(target)
    if kind == "stories":
        for s in data["stories"]:
            if s["slug"] == target:
                return s["title"]
        raise KeyError(target)
    raise KeyError(kind)


def path(slot_name, target, data):
    """The page this instance is published on."""
    slot = slots()[slot_name]
    kind = slot.get("targets")
    if kind == "countries":
        return "/europe/" + target
    if kind == "regions":
        cs, _, rs = target.partition("/")
        return f"/europe/{cs}/{rs}"
    if kind == "journeys":
        return "/journeys/" + target
    if kind == "interests":
        return "/interests/" + target
    if kind == "macros":
        # /discover/<slug>, not /europe/<slug>. The path is a CLAIM about
        # where the photograph is published and `checks.py` asserts a
        # registered photograph appears on the page its purpose names, so a
        # wrong one here is a check that can never pass.
        return "/discover/" + target
    if kind == "themes":
        return "/themes/" + target
    if kind == "categories":
        return "/experiences/" + target
    if kind == "cities":
        return "/europe/" + target
    if kind == "places":
        cid, _, sl = target.rpartition("/")
        return f"/europe/{cid}/place/{sl}"
    if kind == "stories":
        return "/stories/" + target
    raise KeyError(kind)


def stem(purpose):
    """A PURPOSE IS A NAME AND A FILENAME IS NOT THE SAME THING.

    `acquire.py` used the purpose verbatim as the file stem, which worked for
    every one-of-a-kind purpose and for a story, and could never have worked
    for the families whose TARGET carries a path:

        place-hero@austria/salzburg-and-the-lakes/salzburg/hohensalzburg
        region-hero@austria/tyrol-and-vorarlberg
        destination-hero@norway/fjord-norway/bergen

    `photographs/<stem>.original.jpg` then names a file three directories
    deep, and `acquire.py` makes only `photographs/` — so the first real
    acquisition for any of 704 slot instances would have died on a missing
    directory. It survived because no test had ever acquired one: the same
    empty-register blindness that shipped a `style="` attribute the CSP
    forbids and two dead CSS rules. Six new families is what finally made a
    test try it.

    `/` becomes `__` rather than `-`, because a slug may contain a hyphen
    and `a/b-c` and `a-b/c` would then collide — and checks.py asserts no two
    purposes reduce to one stem, because a collision here means two
    photographs overwriting each other's original with every provenance
    field correct about the wrong one.
    """
    return purpose.replace("/", "__")


def split(name):
    """`slot@target` -> (slot, target); a declared purpose -> (name, None)."""
    if SEP in name:
        s, _, t = name.partition(SEP)
        return s, t
    return name, None


def resolve(name, data):
    """The full spec for a purpose name, declared or templated.

    Returns None when the name is neither, so a caller can say so in its own
    words rather than catching an exception — `acquire.py` and the validator
    have different sentences to print.
    """
    slot_name, target = split(name)
    if target is None:
        return declared().get(name)
    slot = slots().get(slot_name)
    if slot is None or target not in targets(slot, data):
        return None
    spec = {k: v for k, v in slot.items() if k not in ("targets", "key")}
    spec["slot"] = slot_name
    spec["target"] = target
    spec["key"] = slot["key"].replace("{target}", target)
    spec["path"] = path(slot_name, target, data)
    spec["surface"] = slot["surface"].replace("{name}", label(slot_name, target, data))
    return spec


def names(data):
    """Every purpose that could exist today: the declared ones and every
    resolvable instance of every slot. This is what the Media Desk lists and
    what duplicate protection is checked against; it is NOT what the role
    bookkeeping counts, because 319 instances of one template are one
    editorial decision rather than 319."""
    out = list(declared())
    for sn, slot in slots().items():
        out += [f"{sn}{SEP}{t}" for t in targets(slot, data)]
    return out


def role_users():
    """Which roles are reached, counting a slot once. A template is one
    decision however many entities it covers."""
    used = {}
    for n, p in declared().items():
        used.setdefault(p.get("role"), []).append(n)
    for n, s in slots().items():
        used.setdefault(s.get("role"), []).append(n)
    return used
