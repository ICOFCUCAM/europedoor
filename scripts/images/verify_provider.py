#!/usr/bin/env python3
"""Fetch a provider's live terms, archive them, and surface what to read.

THE GATE IS NOT "DO YOU KNOW WHETHER UNSPLASH ALLOWS THIS". It is "open the
current official documentation and record what it actually says". This script
is the difference between those two: it downloads the pages, writes them into
`docs/data-licenses/provider-terms/` with the date and a SHA-256, and prints
the passages that mention hotlinking, attribution and download events so a
person can read them and copy the exact sentence into the gate.

IT DOES NOT ANSWER ANYTHING. It cannot: a model summarising a licence page is
the same failure as a model remembering one, one step further from the
source. It fetches, archives and points. The answer, and the verbatim quote
that supports it, are typed by somebody who read the page.

AND THE ARCHIVE IS WHAT MAKES THE GATE CHECKABLE. `checks.py` asserts that
every quote in the gate appears in the snapshot of the page it claims to come
from. So an answer cannot be typed from memory — the evidence has to exist in
the repository beside it, and it has to match.

It will not run in the EuropeDoor sandbox: the egress proxy blocks both
providers outright, which is the reason this is a gate rather than a
recollection. Run it locally or in the `photograph` workflow, which has
network access.

    python3 scripts/images/verify_provider.py --provider pexels
    python3 scripts/images/verify_provider.py --provider unsplash
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")
ARCHIVE = os.path.join(ROOT, "docs", "data-licenses", "provider-terms")

# What to surface for a reader. Deliberately broad: a false positive costs a
# person three seconds and a false negative costs a licence breach.
INTEREST = re.compile(
    r"hotlink|hot-link|photo\.urls|self-host|self host|host(?:ing)? (?:the|these|our) "
    r"|download|attribut|credit|link back|api guideline|must |may not|required",
    re.I)


def text_of(html):
    """Tags out, entities in, whitespace normalised — enough to read and to
    match a quote against. Not a parser: the archive keeps the raw bytes."""
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    for a, b in (("&amp;", "&"), ("&nbsp;", " "), ("&quot;", '"'),
                 ("&#39;", "'"), ("&rsquo;", "’"), ("&lt;", "<"), ("&gt;", ">")):
        html = html.replace(a, b)
    return re.sub(r"[ \t\r\f\v]+", " ", html)


def fetch(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "EuropeDoor licence check "
                                    "(+https://europedoor.com)"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", required=True)
    args = ap.parse_args(argv)

    with open(GATE, encoding="utf-8") as fh:
        gate = json.load(fh)
    if args.provider not in gate:
        sys.exit(f"{args.provider!r} has no row in the gate")
    row = gate[args.provider]
    today = datetime.date.today().isoformat()
    os.makedirs(ARCHIVE, exist_ok=True)

    snapshots = {}
    for url in row["terms_urls"]:
        try:
            raw = fetch(url)
        except Exception as exc:                       # noqa: BLE001
            sys.exit(f"could not read {url}: {exc}\n"
                     f"This machine may not be allowed out. Run it somewhere "
                     f"that is; do NOT answer the gate without the page.")
        stem = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:80]
        name = f"{args.provider}.{stem}.{today}.txt"
        body = text_of(raw.decode("utf-8", "replace"))
        with open(os.path.join(ARCHIVE, name), "w", encoding="utf-8") as fh:
            fh.write(f"# {url}\n# read {today}\n"
                     f"# sha256 of the bytes as served: "
                     f"{hashlib.sha256(raw).hexdigest()}\n\n{body}\n")
        snapshots[url] = name
        print(f"\n{'=' * 70}\n{url}\n  archived as provider-terms/{name}\n")
        hits = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body)
                if INTEREST.search(s) and len(s.strip()) > 40]
        if not hits:
            print("  nothing matched the keywords. READ THE PAGE ANYWAY — a "
                  "requirement can be phrased in words this script does not "
                  "know.")
        for s in hits[:40]:
            print("  · " + s[:300])

    row["terms_snapshot"] = snapshots
    with open(GATE, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"\n{'=' * 70}")
    print("NOW READ THE ARCHIVED PAGES and fill in, for each of self_host,")
    print("attribution and download_ping: `value`, a `quote` copied verbatim")
    print("from the page, and the `source` URL it came from. Then set")
    print(f"`read_on` to {today}.")
    print("checks.py asserts every quote appears in the snapshot it cites, so")
    print("an answer typed from memory fails the build.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
