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

THREE TEMPLATES, AND NOT TWELVE, BECAUSE A SLOT NOBODY CAN FILL IS THE THING
`$requirements` ALREADY REFUSES. The brief lists twelve slot families across
six page families. This site renders a photograph in exactly four places —
`.herofull.shot`, `.way.shot`, `.iheroart.shot` and `.card-art` — and only
three of those vary per entity: a destination, a place inside a destination,
and a story. A country page, a region page, an experience and a journey have
no photograph container in the markup at all, so declaring `country.hero`
would be declaring a slot that cannot be filled and cannot be checked. The
note against `/plan` in that file says the same thing in one sentence: the
honest answer is no slot rather than a slot nobody should fill.

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
    if kind == "cities":
        return "/europe/" + target
    if kind == "places":
        cid, _, sl = target.rpartition("/")
        return f"/europe/{cid}/place/{sl}"
    if kind == "stories":
        return "/stories/" + target
    raise KeyError(kind)


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
