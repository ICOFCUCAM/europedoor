#!/usr/bin/env python3
"""What a paid band looks like, on the real pages, with nothing acquired.

    python3 tools/ad-preview.py && node tools/ad-preview.js

NOT A GATE, AND FOR THE SAME REASON THE HERO SHEET IS NOT ONE: it writes an
image rather than a verdict, and the step it exists for is a person looking.
Every gate here can say the commercial layer is off and correct; none of them
can say whether a sponsored band reads as bought rather than as editorial,
and that is the whole design question §17 and §33 are about.

It writes into `.cache/`, which is ignored, for the reason the candidate
previews do: this is not the site, nothing here is served, and a page
carrying an advertisement must never be mistaken for something the build
produced. `site/` is not touched and `data/advertising.json` is not written.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import addemo                 # noqa: E402
from lib import data as D              # noqa: E402
from lib import pages as P             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".cache", "ad-preview")


def main():
    d = D.load()
    shutil.rmtree(OUT, ignore_errors=True)
    with addemo.simulated():
        wrote = []
        path, html = P.home(d)
        wrote.append((path, html))
        # Bergen, because it is the destination every instrument here uses
        # as the shape of that family and the one the accessibility scan
        # already represents it with.
        c = d["countries"]["norway"]
        r = next(x for x in c["regions"] if x["slug"] == "fjord-norway")
        t = next(x for x in r["cities"] if x["slug"] == "bergen")
        path, html = P.city_page(d, c, r, t)
        wrote.append((path, html))
    for path, html in wrote:
        dest = os.path.join(OUT, path.lstrip("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(html)
        band = html.count('class="adband"')
        print(f"  {path}  {len(html):,} bytes, {band} paid band(s)")
        if band != 1:
            raise SystemExit(
                f"{path} rendered {band} bands: the preview exists to show "
                f"one, and a page with none is the OFF state photographed "
                f"by accident")
    print(f"\n{OUT} — now: node tools/ad-preview.js")


if __name__ == "__main__":
    main()
