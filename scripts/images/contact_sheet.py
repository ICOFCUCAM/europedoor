#!/usr/bin/env python3
"""Draw every discovered candidate INSIDE the real EuropeDoor hero.

    python3 scripts/images/discover.py --provider pexels \\
        --purpose homepage-hero --query "…" --manifest /tmp/cands.json
    python3 scripts/images/contact_sheet.py --manifest /tmp/cands.json
    node tools/hero-sheet.js /tmp/hero-sheet.png

A PHOTOGRAPH CAN BE BEAUTIFUL AND STILL BE WRONG FOR THIS COMPOSITION, and a
provider's grid of thumbnails cannot show that. The hero is a photograph seen
through an elliptical arch, on a limestone wall, with a cobalt masthead over
its top edge, a 60px serif headline and a form beside it, and a scrim between
the two. What a reviewer has to judge is whether the subject survives the
aperture's removed corners, whether the headline lands on something quiet
enough to read, and whether there is anywhere for the masthead to sit. None of
that is visible in a rectangle on somebody else's website.

So this renders the actual page. `pages.home()` is the same function the build
calls, the stylesheet is the shipped one, the arch is cut by the same
`arch_path()` — the ONE substitution is the delivery ladder, and that is
stated below and asserted rather than assumed.

IT RANKS NOTHING. The order is the provider's search order, which is a
ranking by Pexels and not by us; the sheet prints that on itself, because
position is exactly what the `--pick 3` design got wrong. There is no score,
no sort, no "best match" and no default. `fits` is a mechanical gate against
the purpose — a candidate that acquire.py would refuse is left off the sheet,
because art-directing a photograph you cannot have wastes the only step in
this pipeline that needs a person.

NOTHING IT WRITES MAY BE COMMITTED. The previews are somebody else's
photographs with no register row, and a register row needs the original's
bytes, its hash and the date they were served. They go to a scratch directory
under .cache/, which is ignored, and a check asserts the repository carries
none of them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acquire  # noqa: E402

sys.path.insert(0, os.path.join(acquire.ROOT, "tools"))
from lib import data as D  # noqa: E402
from lib import pages as P  # noqa: E402

DEFAULT_OUT = os.path.join(acquire.ROOT, ".cache", "contact")

# The purposes this can draw. A sheet is only worth looking at if it is the
# real page, so a purpose whose surface has no renderer wired here is REFUSED
# rather than drawn as a homepage with the wrong photograph in it — which
# would look exactly like a finished review and be about nothing.
RENDERABLE = {"homepage-hero", "door-mountains", "door-coast",
              "door-history", "door-food"}

# WHERE ON THE PAGE EACH PURPOSE LIVES, because a sheet that shoots the top of
# the page for a surface four screens down is a finished-looking review of
# nothing. The doors are on the same page as the hero, which is why they can
# be drawn at all; they just have to be scrolled to.
SURFACE = {
    "homepage-hero": ".herofull",
    "door-mountains": ".wayin",
    "door-coast": ".wayin",
    "door-history": ".wayin",
    "door-food": ".wayin",
}


def fetch_preview(url, dest):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", acquire.USER_AGENT)
    with urllib.request.urlopen(req, timeout=30) as r:
        blob = r.read()
    with open(dest, "wb") as fh:
        fh.write(blob)
    return len(blob)


def preview_row(cand, spec, preview_url):
    """A register-SHAPED row that is deliberately not a register row.

    It carries what `picture()` reads and nothing else: no sha256, no
    fetched-at, no purpose, no licence evidence. It is never written to
    data/images.json and would be refused by the validator if it were,
    which is the correct relationship between a preview and a provenance
    record.
    """
    return {
        "file": f"candidate-{cand['id']}",
        "version": "preview",
        "alt": cand.get("alt") or f"Pexels candidate {cand['id']}",
        "photographer": cand.get("photographer") or "",
        "source": cand.get("page") or "",
        "licence": "Pexels",
        "licence_url": "https://www.pexels.com/license/",
        "focal": [50, 50],
        "_preview": preview_url,
    }


def use_preview(html, row):
    """Point the hero's <picture> at the one preview file.

    THE SUBSTITUTION IS THE WHOLE DIFFERENCE BETWEEN THIS AND THE REAL PAGE,
    so it is surgical and it is counted. `picture()` emits an AVIF source, a
    WebP source and a JPEG <img>, each with five widths; a preview has one
    file. Serving the same bytes at all fifteen URLs does not work — the
    browser picks the AVIF source by its declared type and then fails to
    decode it — and <picture> does not fall back once a <source> has matched,
    which is how the hero shipped as a 1280x736 hole once already.

    Everything else is untouched: the class, the focal anchor, the credit,
    the scrim, the arch and every byte of the page around it. If the counts
    below are ever not 2 and 1, the renderer has changed shape and this
    transform is no longer describable — so it stops instead of guessing.
    """
    base = f"/assets/img/{row['file']}.{row['version']}"
    html, sources = re.subn(
        r'<source type="image/(?:avif|webp)" srcset="[^"]*'
        + re.escape(base) + r'[^"]*"[^>]*>', "", html)
    if sources != 2:
        raise SystemExit(f"expected 2 <source> elements for {base}, found "
                         f"{sources}. picture() has changed shape and this "
                         f"substitution can no longer describe itself.")
    html, imgs = re.subn(
        r'src="' + re.escape(base) + r'-1260\.jpg" srcset="[^"]*" sizes="[^"]*"',
        f'src="/previews/{row["file"]}.jpg"', html)
    if imgs != 1:
        raise SystemExit(f"expected 1 <img> for {base}, found {imgs}.")
    return html


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True,
                    help="written by discover.py --manifest")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="scratch directory; never committed")
    ap.add_argument("--limit", type=int, default=12,
                    help="how many candidates to draw. A cap on the SHEET, "
                         "not a shortlist: the ones left off are named.")
    args = ap.parse_args(argv)

    with open(args.manifest, encoding="utf-8") as fh:
        man = json.load(fh)

    provider = man.get("provider") or ""
    ok, why = acquire.cleared(provider)
    if not ok:
        # THE SAME GATE, because downloading a preview is still downloading.
        # A provider whose route is refused is refused here too, and finding
        # that out at the sheet rather than at the acquisition is the point.
        sys.exit("REFUSED: " + why)

    purpose = man.get("purpose") or ""
    specs = acquire.purposes()
    spec, _slots = acquire.spec_for(purpose)
    if spec is None:
        sys.exit(f"{purpose!r} is not a purpose — neither a declared one nor "
                 f"an instance of a slot written slot@target.")
    # THE RENDERER IS WIRED PER SLOT OR PER DECLARED PURPOSE, and a slot
    # instance asks for its template: `destination-hero@…` is 319 pages of
    # one composition, so one renderer answers for all of them.
    wanted = spec.get("slot") or purpose
    if wanted not in RENDERABLE:
        sys.exit(f"no renderer is wired for {wanted!r}. The sheet draws the "
                 f"REAL page for a purpose or it does not draw it: a "
                 f"destination photograph judged inside a homepage hero is a "
                 f"review of the wrong composition. Wire "
                 f"{spec['path']} into RENDERABLE first.")

    cands = man.get("candidates") or []
    usable = [c for c in cands if not acquire.fits(c, spec)]
    refused = [c for c in cands if acquire.fits(c, spec)]
    if not usable:
        sys.exit(f"none of {len(cands)} candidates meets {purpose}. Nothing "
                 f"to look at: acquire.py would refuse every one of them.")
    drawn, spare = usable[:args.limit], usable[args.limit:]

    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    os.makedirs(os.path.join(args.out, "previews"))

    d = D.load()
    sheet = []
    for c in drawn:
        row = preview_row(c, spec, c["preview"])
        dest = os.path.join(args.out, "previews", row["file"] + ".jpg")
        size = fetch_preview(c["preview"], dest)
        # The register is REPLACED for this render, never merged into: a
        # candidate must not inherit a real row's provenance by sitting
        # beside it in the same dict.
        page = dict(d, images={spec["key"]: row})
        path, html = P.home(page)
        del path
        out = os.path.join(args.out, f"cand-{c['id']}")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(use_preview(html, row))
        sheet.append({
            "id": c["id"], "url": f"/cand-{c['id']}/",
            "photographer": c["photographer"], "page": c["page"],
            "native": f"{c['width']}x{c['height']}",
            "preview_bytes": size,
        })
        print(f"  drew {c['id']:<12} {c['width']}x{c['height']:<11} "
              f"{c['photographer'][:30]}")

    with open(os.path.join(args.out, "sheet.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "$comment":
                "THE ORDER IS THE PROVIDER'S SEARCH ORDER. It is not a "
                "ranking by EuropeDoor and position on this sheet means "
                "nothing. Every candidate drawn here meets the mechanical "
                "minimum for its purpose; which one is RIGHT is the question "
                "the sheet exists to put to a person.",
            "provider": provider, "purpose": purpose,
            "query": man.get("query"), "searched": man.get("searched"),
            "surface": spec["surface"],
            # The selector the sheet renderer scrolls to and measures. It
            # travels in the manifest rather than being a second table in the
            # renderer, so one file decides which surface a purpose occupies.
            "selector": SURFACE[purpose],
            "cells": sheet,
        }, fh, indent=2, ensure_ascii=False)

    print(f"\n{len(sheet)} candidates drawn into the real hero → {args.out}")
    if refused:
        print(f"{len(refused)} left off: acquire.py would refuse them — "
              + ", ".join(c["id"] for c in refused))
    if spare:
        print(f"{len(spare)} more met the minimum and are past --limit "
              f"{args.limit}: " + ", ".join(c["id"] for c in spare))
    print("\nNext: node tools/hero-sheet.js  (add --phone or --dark)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
