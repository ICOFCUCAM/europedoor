#!/usr/bin/env python3
"""Is the site a reader gets the site this repository builds?

    python3 tools/deployed.py [--origin https://europedoor.com]

EVERY OTHER GATE HERE VALIDATES THE REPOSITORY. Not one of them has ever
opened the site. That gap has now cost this project twice, both times in the
same shape — correct in the repository, wrong in the response:

  * `site/_headers` is Netlify and Cloudflare syntax and Vercel does not read
    it, so HSTS, nosniff, Permissions-Policy and frame-ancestors were absent
    from every production response for as long as they lived only there.
  * `/assets/(.*)` is served `immutable`, which tells a browser never to
    revalidate for a year, and the stylesheet sat at a STABLE path under it.
    So every returning reader kept the stylesheet they first downloaded and
    every visual change reached new visitors only. It was found by being told
    nothing had changed and checking the response rather than the repository.

Both were invisible from inside. A build that is correct, committed and
green, serving a page styled by a file from months ago, looks exactly like a
build that shipped. So this reads the RESPONSE — the bytes a browser gets —
and compares them with what the build produced.

IT CANNOT RUN IN THE EUROPEDOOR SANDBOX. The egress proxy answers 403 to
CONNECT for general hosts, europedoor.com included, which was confirmed
rather than assumed. It runs in `.github/workflows/deployed.yml`, which has
network, on dispatch and on a schedule — and it is deliberately not in the
gate list for the same reason `scripts/map/fetch.py` is not: a gate that
needs the internet is a gate that fails for reasons that are not about the
code.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
UA = "EuropeDoor deploy check (+https://europedoor.com)"

FAILURES = []
CHECKED = 0


def check(name, cond, detail=""):
    global CHECKED
    CHECKED += 1
    print(("  ok   " if cond else "  FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        FAILURES.append(f"{name}{(': ' + detail) if detail else ''}")


def get(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", UA)
    # NO CACHE ANYWHERE IN THE PATH. The failure this exists to catch is a
    # stale copy being served, so a check that would happily read one from a
    # proxy is checking the wrong thing.
    req.add_header("Cache-Control", "no-cache")
    req.add_header("Pragma", "no-cache")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--origin", default="https://europedoor.com")
    args = ap.parse_args(argv)
    origin = args.origin.rstrip("/")

    built = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    want_css = re.search(r'href="(/assets/css/europedoor\.[0-9a-f]+\.css)"', built)
    if not want_css:
        sys.exit("the built homepage has no content-addressed stylesheet — "
                 "this check cannot tell old from new without one")
    want_css = want_css.group(1)

    print(f"{origin}  against the build in site/\n")

    status, headers, body = get(origin + "/")
    text = body.decode("utf-8", "replace")
    check("the homepage answers 200", status == 200, f"got {status}")
    if status != 200:
        return report()

    # THE ONE QUESTION THIS EXISTS FOR. The stylesheet's filename IS its
    # content hash, so a served page naming a different one is a served page
    # built from different bytes. That is the whole test for "did the work
    # actually reach the site", and it needs no version file and no build id.
    got_css = re.search(r'href="(/assets/css/europedoor\.[0-9a-f]+\.css)"', text)
    got = got_css.group(1) if got_css else "none"
    check("the served homepage is built from this commit's assets",
          got == want_css,
          f"serving {got}, this build made {want_css}" if got != want_css else "")

    s2, _h2, css = get(origin + want_css)
    check("that stylesheet is actually there", s2 == 200, f"got {s2} for {want_css}")
    local_css = None
    for name in os.listdir(os.path.join(SITE, "assets", "css")):
        if name.endswith(".css"):
            local_css = open(os.path.join(SITE, "assets", "css", name), "rb").read()
    check("and it is byte-for-byte the stylesheet in site/",
          local_css is not None and css == local_css,
          f"{len(css)} bytes served, {len(local_css or b'')} built")

    # THE HEADERS, FROM THE RESPONSE. render.HEADERS and vercel.json are
    # already checked against each other; neither says whether Vercel applied
    # them. site/_headers looked correct for months and was never read.
    low = {k.lower(): v for k, v in headers.items()}
    for key, want in (
        ("content-security-policy", "default-src 'none'"),
        ("strict-transport-security", "max-age="),
        ("x-content-type-options", "nosniff"),
        ("referrer-policy", "strict-origin"),
        ("permissions-policy", "geolocation=()"),
    ):
        check(f"the response carries {key}", want in low.get(key, ""),
              f"got {low.get(key, '(absent)')[:60]!r}")
    check("the policy admits no inline anything",
          "unsafe-inline" not in low.get("content-security-policy", ""))

    _s3, h3, _b3 = get(origin + want_css)
    cc = {k.lower(): v for k, v in h3.items()}.get("cache-control", "")
    check("a content-addressed asset is served immutable", "immutable" in cc,
          f"got {cc!r}")

    # cleanUrls, on real routes rather than on the configuration that claims
    # it. A directory index that 404s is a whole site that is not there.
    for path in ("/map", "/europe/austria", "/journeys", "/method", "/sources"):
        s, _h, _b = get(origin + path, method="HEAD")
        check(f"{path} is served", s == 200, f"got {s}")

    # AND THE THING THE PIPELINE IS BUILDING TOWARD. Zero photographs are
    # licensed, so the homepage must draw the continent; the day one is
    # merged this line is how anybody here learns it reached readers.
    check("the homepage opens on the hero",
          'class="herofull' in text,
          "the opening is missing from the served page")
    print("\n  the served homepage opens on "
          + ("a photograph" if 'class="herofull shot"' in text
             else "the drawn continent"))
    return report()


def report():
    print()
    if FAILURES:
        print(f"{len(FAILURES)} of {CHECKED} deployment check(s) failed:")
        for f in FAILURES:
            print("  - " + f)
        print("\nThe repository can be perfectly correct and every one of "
              "these still fail. That is the point of them.")
        return 1
    print(f"all {CHECKED} deployment checks passed — readers are getting this build")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
