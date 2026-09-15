#!/usr/bin/env python3
"""FILL THE LIBRARY: every empty surface, in one dispatch, as far as one
sitting reaches.

WHY THIS EXISTS WHEN THE DESK ALREADY HAS THE BUTTON. The hosted Media Desk
has had a `Fill the library` press since the basket was built, and it works
— but it is a second Vercel project somebody has to be signed in to, and a
library of eleven photographs against 837 declared surfaces says nobody has
pressed it fourteen times. The same decision, dispatchable from Actions:
this runs INSIDE the workflow, where the key is, so the browser never holds
one and this sandbox never opens a socket to a provider.

IT IS NOT A SECOND PIPELINE. It does not download, does not hash, does not
write a register row and does not build a derivative — `acquire.py` does all
of that, by id, verifying the id it got back is the id it asked for, and
`batch.sh` runs it once per entry and keeps going past a refusal. This reads
the registry, searches, and writes a PLAN. That is the whole of it, and it is
deliberately the same shape as `desk/api/topup.js`, whose reasoning it
inherits:

  * ROUND-ROBIN ACROSS SLOTS. Taken in registry order one press is sixty
    Austrian destinations — a complete answer about Austria and no answer
    about the product. One from each family in turn means a press touches
    themes, countries, journeys, interests, macro regions, categories,
    stories, regions, destinations and places.
  * THE QUERY IS THE ROLE'S OWN FIRST CONCEPT, not the bare name. Nothing
    LOOKS at these candidates, so the query has to carry the intent the eye
    would have: `country-hero` declares `{name} landscape` and
    `destination-hero` declares `{name}`.
  * IT REQUIRES THE PHOTOGRAPHER'S OWN DESCRIPTION. Every acquisition needs
    an alt and the alternative to a real one is writing a description of a
    photograph nothing here has seen — the licence-from-memory failure in
    another costume. A candidate with no `alt` is not unusable, it is
    un-AUTOMATABLE, and it stays available to the two paths where a person
    looks.
  * AND A CEILING ON HOW MANY IT LOOKS AT, which is not the same number as
    how many it takes. A surface whose search returns nothing qualifying
    costs a request and yields no row, so bounding only the take walks all
    837 empty surfaces against a rate limit nobody here owns.

EMPTY SURFACES ONLY. Re-offering a filled one is proposing to replace a
photograph somebody accepted, which is a different act and not this one.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import acquire   # noqa: E402
import discover  # noqa: E402

ROOT = acquire.ROOT


def registry():
    with open(os.path.join(ROOT, "desk", "registry.json"), encoding="utf-8") as fh:
        return json.load(fh)


def held():
    """The purposes the register already holds, read from the repository."""
    path = os.path.join(ROOT, "data", "images.json")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = doc.get("images", doc)
    out = set()
    for key, row in rows.items():
        if isinstance(row, dict):
            out.add(row.get("purpose") or key)
    return out


def query_of(p, spec):
    """The role's first concept with the surface's name in it."""
    name = (p.get("target") or p.get("purpose") or "").split("/")[-1]
    name = name.replace("-", " ").strip()
    surface = p.get("surface") or ""
    for opener, closer in ((" of the ", " destination page"),
                           (" of the ", " place page")):
        if opener in surface and closer in surface:
            name = surface.split(opener, 1)[1].split(closer, 1)[0].strip()
            break
    if " of the story " in surface:
        seg = surface.split(" of the story ", 1)[1]
        for q in ("“", '"'):
            if q in seg:
                name = seg.split(q)[1] if seg.count(q) >= 2 else name
                break
    concept = ""
    search = (spec or {}).get("search") or []
    if search:
        concept = search[0]
    return concept.replace("{name}", name) if concept else name


def interleave(rows):
    """One queue per slot, then taken in turn.

    A declared purpose with no slot — the homepage hero, the four doors — is
    its own family, which puts each of them early rather than behind 255
    places.
    """
    lanes = {}
    for p in rows:
        lanes.setdefault(p.get("slot") or p["purpose"], []).append(p)
    out, queues = [], list(lanes.values())
    i = 0
    while any(i < len(q) for q in queues):
        for q in queues:
            if i < len(q):
                out.append(q[i])
        i += 1
    return out


def main(argv):
    reg = registry()
    cap = reg["dispatch_cap"]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=sorted(acquire.PROVIDERS),
                    default="pexels")
    ap.add_argument("--take", type=int, default=cap,
                    help=f"how many to plan for; the dispatch cap is {cap}")
    ap.add_argument("--out", required=True, help="where to write the plan")
    args = ap.parse_args(argv)

    take = min(max(1, args.take), cap)
    # TWICE THE FILL, DERIVED RATHER THAN TYPED, because taking sixty means
    # expecting to reject some — and a ceiling written as a number stops
    # being twice the fill the day the fill moves.
    looks = 2 * take

    have = held()
    empty = [p for p in reg["purposes"] if p["key"] not in have
             and p["purpose"] not in have]
    order = interleave(empty)
    print(f"{len(have)} surfaces hold a photograph, {len(order)} are empty; "
          f"planning up to {take} and looking at no more than {looks}.")
    if not order:
        print("Every surface this product declares already holds a "
              "photograph. There is nothing left for this to fill.")
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump([], fh)
        return 0

    used = {}
    plan, looked, covered = [], 0, set()
    for p in order:
        if len(plan) >= take or looked >= looks:
            break
        looked += 1
        covered.add(p.get("slot") or p["purpose"])
        spec = {k: v for k, v in p.items()}
        try:
            payload, cached = discover.cached_search(
                args.provider, query_of(p, spec),
                spec.get("orientation") or "landscape", 12)
        except Exception as exc:                       # noqa: BLE001
            print(f"the provider stopped answering after {len(plan)} of "
                  f"{len(order)} empty surfaces: {exc}")
            break
        pick = None
        for cand in discover.normalise(args.provider, payload):
            if acquire.fits(cand, spec):
                continue
            if cand["id"] in used:
                continue
            # A DESCRIPTION FROM THE PHOTOGRAPHER, or this one is not
            # automatable: writing one here would be describing a photograph
            # nothing has looked at.
            if not (cand.get("alt") or "").strip():
                continue
            pick = cand
            break
        if not pick:
            continue
        # AND NOT TWICE IN ONE DISPATCH. The provider can return the same
        # photograph for two neighbouring queries and the register refuses
        # one id against two purposes, so a plan must not contain a pair
        # the acquisition will reject.
        used[pick["id"]] = p["purpose"]
        plan.append({"purpose": p["purpose"], "photo_id": pick["id"],
                     "alt": pick["alt"].strip()})
        print(f"  {p['purpose']:<44} {pick['id']:>10}  {pick['alt'][:56]}")

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=1)
    print(f"\nplanned={len(plan)} looked={looked} "
          f"families={len(covered)} empty={len(order)}")
    if not plan:
        print("NOTHING QUALIFIED. A sitting that plans nothing is a failure "
              "rather than a quiet success, because 'found nothing suitable' "
              "and 'could not run' must not look the same.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
