#!/usr/bin/env python3
"""Write the slot registry the HOSTED desk serves.

    python3 tools/desk-registry.py --write
    python3 tools/desk-registry.py --check

THE LOCAL DESK IMPORTS `tools/lib/`; A SERVERLESS FUNCTION CANNOT.

`tools/desk/serve.py` resolves a purpose by calling `imageslots.resolve()`
with the whole dataset loaded — a Python process sitting in the repository.
A Vercel function is a Node bundle with no repository, no Python and no
dataset, so the same answer has to arrive as data.

It is GENERATED AND COMMITTED, exactly like `site/` and
`docs/invariants.json`, and `checks.py` fails when it is stale. That is the
only shape that keeps one source of truth: the slots are still declared once
in `data/image-purposes.json`, the targets still come from the atlas rather
than from a list somebody typed, and a function serving a stale copy is a
failing build rather than a desk quietly offering a destination that no
longer exists.

IT CARRIES NO PHOTOGRAPH STATE. The register is read live by the function
from the repository, because a photograph acquired an hour ago must show as
filled without regenerating this file — the status is derived, and a status
baked into a build is a status that goes stale.

IT DOES CARRY THE LICENCE GATE'S VERDICT, and that is not the same thing.
A photograph's presence changes hourly; whether Pexels clears the automated
route changes when somebody edits `docs/data-licenses/photo-providers.json`
and commits it, which is the same act that regenerates this file. So the
verdict is generated FROM `acquire.cleared()` rather than restated, and a
provider that stops clearing goes dark on the desk in the commit that
refuses it.

THE VERDICT HERE IS NOT THE GATE. `acquire.py` refuses before it opens a
socket, inside the workflow, where the key is — and that refusal is the one
that counts. This copy exists so the desk can say WHY a provider is
unavailable instead of offering a search that will be refused three screens
later. A desk that could clear a provider the gate refuses would be a second
gate; this cannot, because it never runs an acquisition.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

sys.path.insert(0, os.path.join(ROOT, "scripts", "images"))

import acquire                                            # noqa: E402
from lib import imageslots                                # noqa: E402

# THE DISPATCH CAP, DECLARED ONCE BECAUSE FOUR COPIES OF IT DISAGREED.
#
# How many photographs one press may send is enforced in four places: the
# desk's Acquire route refuses a longer batch before it dispatches, the
# Fill button gathers exactly this many, the basket says so on its face,
# and the WORKFLOW refuses the plan again before a socket opens. The last
# one is the only gate — it is the copy that runs where the key is.
#
# Run 22 sent sixty and died on `60 entries is more than one sitting. The
# cap is 30.` The desk had been raised to sixty and the workflow had not,
# so the editor's own screen promised something the gate would refuse,
# which is worse than a low cap: it spends a whole sitting before saying
# no. A SECOND IMPLEMENTATION OF A THING IS A SECOND CHANCE TO MAKE ITS
# MISTAKE, and on the recurrence the answer is to stop having one — the
# number lives here, is generated into `desk/registry.json`, and all four
# read it from there.
#
# Sixty, measured: run 18 fetched, verified, hashed, derived and
# registered eight photographs in 34 seconds — 4.25s each — against 215
# seconds of fixed cost. The acquisition is the small, linear half; the
# gates are the big half and cost the same for one as for sixty. So the
# cap is not about the workflow at all. It is about what one PULL REQUEST
# can carry a reviewer through.
DISPATCH_CAP = 60

from lib.data import load                                 # noqa: E402

OUT = os.path.join(ROOT, "desk", "registry.json")


REQS = ("role", "min_width", "orientation", "min_aspect", "max_aspect", "note")

# THE ROLE'S SEARCH CONCEPTS TRAVEL WITH THE SLOT. They are what turns a
# purpose from a size into a subject — "what do I type to find a picture of
# this kind" — and the desk has no data/ to read them from. `{name}` is left
# unsubstituted here and filled per surface in the browser, because one
# template is one decision and 593 substitutions are 593 copies of it.


def build():
    data = load()
    rows = []
    for name in sorted(imageslots.declared()):
        rows.append(_row(name, imageslots.resolve(name, data), templated=False))
    roles = imageslots._doc().get("roles", {})
    slots = {}
    for sn in sorted(imageslots.slots()):
        slot = imageslots.slots()[sn]
        slots[sn] = {k: slot.get(k) for k in REQS}
        # A SLOT'S OWN CONCEPTS WIN OVER ITS ROLE'S, because the one slot
        # that declares them does so for a reason the role cannot know: a
        # story's entity name is a title, not a subject.
        slots[sn]["search"] = (slot.get("search")
                               or (roles.get(slot.get("role")) or {}).get("search", []))
        for t in imageslots.targets(slot, data):
            spec = imageslots.resolve(f"{sn}{imageslots.SEP}{t}", data)
            rows.append(_row(f"{sn}{imageslots.SEP}{t}", spec, templated=True,
                             data=data))
    providers = {}
    for slug in sorted(k for k in acquire.gate() if not k.startswith("$")):
        ok, why = acquire.cleared(slug)
        providers[slug] = {"cleared": ok, "because": "" if ok else why}
    return {
        "$comment": (
            "GENERATED by tools/desk-registry.py — never hand-edited, and "
            "checks.py fails when it is stale. It is the slot registry the "
            "hosted Media Desk serves, because a serverless function cannot "
            "import tools/lib or read data/. It carries no photograph state: "
            "the desk reads the register live, so a photograph acquired an "
            "hour ago shows as filled without a rebuild. The provider "
            "verdicts ARE generated, from acquire.cleared(), because they "
            "change with a commit rather than with an acquisition — and they "
            "are not the gate: acquire.py refuses inside the workflow, where "
            "the key is. A TEMPLATED ROW CARRIES NO REQUIREMENTS: they are "
            "the SLOT's, stated once under `slots`, because 590 copies of "
            "the same 300-word brief is half a megabyte saying one thing, "
            "and a value repeated 590 times is 590 places for it to differ. "
            "`dispatch_cap` is here for the same reason one level up: four "
            "copies of that number disagreed and the one that mattered was "
            "the workflow's."),
        "dispatch_cap": DISPATCH_CAP,
        "providers": providers,
        "slots": slots,
        "purposes": rows,
    }


def _row(name, spec, templated, data=None):
    """Identity always; requirements only where they are the row's OWN.

    A templated instance inherits every number and the brief from its slot,
    and the desk reads them from there — which is also what the interface
    says out loud, because an editor should never have to know that a
    destination portrait wants 1,800 native pixels.

    THE COUNTRY IS DERIVED, NEVER TYPED. A target is `country/region/city`
    for a destination and one segment deeper for a place, so the country is
    the first segment — but the desk needs the country's NAME, and a slug
    title-cased is "Bosnia And Herzegovina" and "Turkiye". So it comes out of
    the atlas, which is where the name is written, for the same reason
    `targets()` reads the atlas rather than a list in the spec file: a list
    typed into JSON is wrong the first time somebody adds a country.

    A story has no country. It has `places`, which are in several, so a
    single country field would be a claim the data does not make — and the
    honest answer is an absent field rather than a guess, exactly as a
    destination with no population figure prints none.
    """
    row = {
        "purpose": name,
        "slot": spec.get("slot"),
        "target": spec.get("target"),
        "key": spec["key"],
        "path": spec["path"],
        "surface": spec["surface"],
    }
    if not templated:
        row.update({k: spec.get(k) for k in REQS})
        roles = imageslots._doc().get("roles", {})
        row["search"] = (roles.get(spec.get("role")) or {}).get("search", [])
    elif data is not None:
        cslug = (spec.get("target") or "").split("/")[0]
        country = data["countries"].get(cslug)
        if country:
            row["country"] = cslug
            row["country_name"] = country["name"]
    return row


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    want = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if args.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(want)
        print(f"desk/registry.json — {len(build()['purposes'])} purposes")
        return 0
    have = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if have != want:
        print("desk/registry.json is stale. Run tools/desk-registry.py --write "
              "and commit it in the same commit, exactly like site/.")
        return 1
    print(f"desk/registry.json is current — {len(build()['purposes'])} purposes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
