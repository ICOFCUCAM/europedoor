#!/usr/bin/env python3
"""Archive a provider's terms page that a PERSON read in a browser.

THE COMPANION TO verify_provider.py, FOR THE CASE THAT ACTUALLY HAPPENS. Both
photo providers refuse an automated request: on a GitHub runner Pexels answers
403 and Unsplash answers 401, to a client that names itself honestly. The way
past that is not a browser user-agent — that would misrepresent who made the
request, on the one errand here whose whole purpose is not misrepresenting
anything. The way past it is a person opening the page, which is exactly the
access the page is published for.

So this takes the text of a page somebody read and puts it where the gate
looks, with a header that says HOW IT GOT THERE. That last part is the reason
this is a script and not a hand-edit: verify_provider.py writes

    # sha256 of the bytes as served: <hash>

and a pasted page has no such thing. Writing that line over text out of a
clipboard would be a claim about a request nobody made — the same class of
untruth as answering the gate from memory, which is what the gate exists to
stop. This writes

    # saved by a person from a browser
    # sha256 of the text as saved: <hash>

which is true, and is still evidence: it pins exactly what was read, so a
quote can be checked against it and a later reader can tell the two kinds of
record apart.

IT DOES NOT ANSWER ANYTHING EITHER. It archives and stops. The value, the
verbatim quote and the source URL are typed by whoever read the page, and
checks.py asserts the quote appears in the snapshot it cites.

    python3 scripts/images/save_terms.py --provider pexels \\
        --url https://www.pexels.com/license/ --file ~/Downloads/license.txt

    pbpaste | python3 scripts/images/save_terms.py --provider unsplash \\
        --url https://unsplash.com/license
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")
ARCHIVE = os.path.join(ROOT, "docs", "data-licenses", "provider-terms")

# A PASTE THAT GRABBED NOTHING LOOKS EXACTLY LIKE A PASTE THAT WORKED once it
# is a file on disk, and it fails much later as "the quote is not in the
# archived page" — which reads as "the terms changed". A licence page is
# thousands of characters; anything under this is a mis-copy, and saying so
# here costs one line and saves that confusion.
MIN_CHARS = 400


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--url", required=True,
                    help="the page this text came from, exactly as in the "
                         "gate's terms_urls")
    ap.add_argument("--file", help="a file holding the page text; "
                                   "omit to read stdin")
    args = ap.parse_args(argv)

    with open(GATE, encoding="utf-8") as fh:
        gate = json.load(fh)
    if args.provider not in gate:
        sys.exit(f"{args.provider!r} has no row in the gate")
    row = gate[args.provider]

    # THE URL MUST BE ONE THE GATE ASKS ABOUT. A snapshot of some other page
    # is a document nothing checks, filed where checked documents live.
    if args.url not in row["terms_urls"]:
        sys.exit(f"{args.url} is not one of {args.provider}'s terms_urls:\n  "
                 + "\n  ".join(row["terms_urls"])
                 + "\nIf the provider moved the page, change terms_urls first "
                   "and say so in the commit.")

    text = (open(args.file, encoding="utf-8").read() if args.file
            else sys.stdin.read())
    text = text.replace("\r\n", "\n").strip()
    if len(text) < MIN_CHARS:
        sys.exit(f"only {len(text)} characters — that is a mis-copy rather "
                 f"than a licence page. Select the whole page and try again.")

    today = datetime.date.today().isoformat()
    os.makedirs(ARCHIVE, exist_ok=True)
    stem = re.sub(r"[^a-z0-9]+", "-", args.url.lower()).strip("-")[:80]
    name = f"{args.provider}.{stem}.{today}.txt"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    with open(os.path.join(ARCHIVE, name), "w", encoding="utf-8") as fh:
        fh.write(f"# {args.url}\n# read {today}\n"
                 f"# saved by a person from a browser\n"
                 f"# sha256 of the text as saved: {digest}\n\n{text}\n")

    # `or {}` rather than setdefault: the key EXISTS in the gate file and its
    # value is null until a page is archived, so setdefault handed back None
    # and assigning into it raised. A key that is present and empty is not an
    # absent key — the same distinction the JSON-LD check makes about an empty
    # property, one file over.
    snaps = row.get("terms_snapshot") or {}
    snaps[args.url] = name
    row["terms_snapshot"] = snaps
    with open(GATE, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"archived {len(text)} characters as provider-terms/{name}")
    print(f"recorded as the snapshot for {args.url}")
    print("\nNow fill in `value`, a verbatim `quote` and the `source` URL for "
          "each of\nself_host, attribution and download_ping in "
          "docs/data-licenses/photo-providers.json,\nset `read_on` to "
          f"{today}, and run python3 tools/checks.py — every quote is matched\n"
          "against the page it cites, so a sentence typed from memory fails "
          "the build.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
