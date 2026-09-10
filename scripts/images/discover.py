#!/usr/bin/env python3
"""Search a provider and print CANDIDATE IDS. Downloads nothing, ever.

    python3 scripts/images/discover.py --provider pexels \\
        --purpose homepage-hero --query "Europe coastline dawn aerial"

DISCOVERY AND ACQUISITION ARE TWO STAGES BECAUSE THEY ARE TWO DECISIONS.
This one answers "what is available"; `acquire.py` answers "take that one".
Nothing here writes to assets/, to the register, or to anything else — a
photograph appearing in a search result is not a photograph anybody chose,
and the previous design blurred exactly that line by letting `--pick N` both
search and take in one command.

WHAT IT PRINTS is what a person needs in order to choose: the id to approve,
the photographer, the page to open and look at, the native size, and whether
the picture meets the mechanical minimum for the purpose it is being
considered for. It marks each candidate SUITABLE or not, and it does not sort
by suitability or hide the failures — the numbers are a floor, not a ranking,
and a ranking is a recommendation this script has no business making.

IT NEVER NAMES A WINNER. Choosing is the whole editorial act: subject
placement, what the type will sit over, whether it reads as a particular
morning or as generic stock. No count decides that.

THE SEARCH IS CACHED so that looking twice costs one call. Pexels allows 200
requests an hour and the point of discovery is to look repeatedly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acquire  # noqa: E402

CACHE_DIR = os.path.join(acquire.ROOT, ".cache", "discovery")
CACHE_SECONDS = 60 * 60


def cached_search(slug, query, orientation, per_page):
    os.makedirs(CACHE_DIR, exist_ok=True)
    ident = hashlib.sha256(
        f"{slug}|{query}|{orientation}|{per_page}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE_DIR, f"{slug}.{ident}.json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_SECONDS:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), True
    qs = urllib.parse.urlencode({"query": query, "orientation": orientation,
                                 "per_page": per_page, "size": "large"})
    payload, _headers = acquire.get_json(slug, "/search?" + qs)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return payload, False


def normalise(slug, payload):
    out = []
    if slug == "pexels":
        for p in payload.get("photos", []):
            src = p.get("src") or {}
            out.append({
                "id": str(p.get("id", "")),
                "photographer": p.get("photographer") or "",
                "photographer_url": p.get("photographer_url") or "",
                "page": p.get("url") or "",
                "width": int(p.get("width") or 0),
                "height": int(p.get("height") or 0),
                "alt": p.get("alt") or "",
                "has_original": bool(src.get("original")),
            })
    return [c for c in out if c["id"] and c["page"] and c["has_original"]]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=sorted(acquire.PROVIDERS),
                    default="pexels")
    ap.add_argument("--purpose", required=True,
                    help="what the photograph would be for — the minimums "
                         "come from data/image-purposes.json")
    ap.add_argument("--query", required=True)
    ap.add_argument("--per-page", type=int, default=15)
    args = ap.parse_args(argv)

    ok, why = acquire.cleared(args.provider)
    if not ok:
        sys.exit("REFUSED: " + why)

    specs = acquire.purposes()
    if args.purpose not in specs:
        sys.exit(f"{args.purpose!r} is not a declared purpose. Known: "
                 + ", ".join(sorted(specs)))
    spec = specs[args.purpose]

    payload, was_cached = cached_search(
        args.provider, args.query, spec.get("orientation", "landscape"),
        args.per_page)
    found = normalise(args.provider, payload)
    if not found:
        sys.exit(f"no candidate for {args.query!r}")

    print(f"{len(found)} candidates on {acquire.PROVIDERS[args.provider]['name']} "
          f"for {args.query!r}"
          + ("  (from cache)" if was_cached else ""))
    print(f"purpose {args.purpose}: {spec['surface']}")
    print(f"needs {spec['min_width']}px wide, {spec.get('orientation')}, "
          f"aspect {spec.get('min_aspect')}–{spec.get('max_aspect')}\n")
    suitable = 0
    for c in found:
        bad = acquire.fits(c, spec)
        mark = "  ok " if not bad else "  -- "
        suitable += 0 if bad else 1
        print(f"{mark}id {c['id']:<12} {c['width']}x{c['height']:<6} "
              f"{c['photographer'][:26]:<26} {c['page']}")
        if c["alt"]:
            print(f"       {c['alt'][:96]}")
        for b in bad:
            print(f"       ! {b.split(' — ')[0]}")
    print(f"\n{suitable} of {len(found)} meet the mechanical minimum for "
          f"{args.purpose}.")
    print("OPEN THE PAGES AND LOOK. These numbers are a floor, not a ranking:")
    print("  subject placement, what the headline will sit over, and whether")
    print("  it reads as a particular morning or as generic stock are the")
    print("  actual decision, and nothing here can make it.")
    print(f"\nThen acquire the ONE you chose, by its id:")
    print(f"  --provider {args.provider} --photo-id <id> --purpose {args.purpose}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
