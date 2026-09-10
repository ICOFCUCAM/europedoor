#!/usr/bin/env python3
"""Write the pull-request body for an acquired photograph, from the register.

    python3 scripts/images/pr_body.py --purpose homepage-hero --branch photo/x

THE PR IS THE APPROVAL BOUNDARY, so it has to carry the evidence rather than
a file listing. Every figure here is READ OUT OF THE REGISTER the acquisition
wrote — none of it is passed in — so the PR cannot describe a photograph other
than the one committed. A body typed by the workflow could drift from the
files in the same commit, and a reviewer would have no way to tell.

IT IS A SCRIPT AND NOT A HEREDOC IN THE WORKFLOW for a reason this repository
has already paid for once: inside a YAML block scalar every line is indented,
and a terminator that is not at column zero is a terminator bash never sees.
A file also means the body generator can be tested, which a heredoc cannot.

IT PRINTS NO SECRET. It reads the register and the purposes file, neither of
which has ever held a credential, and the check that greps committed files for
credential-shaped tokens covers this one too.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def body(purpose, branch, repo_slug=""):
    reg = json.load(open(os.path.join(ROOT, "data", "images.json"),
                         encoding="utf-8"))["images"]
    rows = [(k, r) for k, r in reg.items() if r.get("purpose") == purpose]
    if not rows:
        sys.exit(f"no register row for purpose {purpose!r} — the acquisition "
                 f"did not complete, and a PR describing nothing must not open")
    key, r = rows[0]
    d = r.get("derivatives") or {}
    out = ["## Photography acquisition", "", "| | |", "|---|---|"]
    for label, value in [
        ("Provider", r["provider"]),
        ("Photo ID", r["provider_photo_id"]),
        ("Purpose", r["purpose"]),
        ("Register key", f"`{key}`"),
        ("Publication path", r["publication_path"]),
        ("Photographer", f"[{r['photographer']}]({r['photographer_url']})"),
        ("Source", r["source"]),
        ("Licence", f"[{r['licence']}]({r['licence_url']})"),
        ("Terms read on", r["terms_read_on"]),
        ("Terms evidence", "<br>".join(r["terms_evidence"])),
        ("Acquired at", r["acquired_at"]),
        ("Original dimensions", f"{r['width']}×{r['height']}"),
        ("Original bytes", f"{r['bytes']:,}"),
        ("Original SHA-256", f"`{r['sha256']}`"),
        ("Derivatives", f"{len(d)} files, "
                        f"{sum(x['bytes'] for x in d.values()):,} bytes"),
        ("Encoder", (r.get("processing") or {}).get("tool", "")),
        ("Quality", ", ".join(f"{k} {v}" for k, v in
                              ((r.get("processing") or {}).get("quality") or {}).items())),
    ]:
        out.append(f"| {label} | {value} |")

    out += ["", "### Preview", ""]
    if repo_slug and branch:
        raw = (f"https://raw.githubusercontent.com/{repo_slug}/{branch}"
               f"/assets/img/{r['file']}-1260.jpg")
        out.append(f"![{r['alt']}]({raw})")
    else:
        out.append(f"`assets/img/{r['file']}-1260.jpg`")
    out += ["", f"**Alt text:** {r['alt']}", ""]

    # THE NUMBERS ARE NOT THE DECISION. Every figure above says the pipeline
    # worked; none of them says the photograph is right for the surface, and
    # that is the only question a human is here to answer.
    out += [
        "### What to check before merging", "",
        "- Does it look like this place on a particular morning, or like "
        "generic stock?",
        "- Subject placement against the headline and the masthead over it.",
        "- Contrast under the type; no watermark; nothing misleading about "
        "the subject.",
        "- The credit renders as the provider's terms require: a link to the "
        "photo page and a link to the provider.",
        "",
        "Everything above this line is mechanical and already passed. This "
        "list is the part that is not.",
        "", "### Derivatives", "",
        "| file | pixels | bytes | sha256 |", "|---|---|---|---|",
    ]
    for name in sorted(d):
        x = d[name]
        out.append(f"| `{name}` | {x['width']}×{x['height']} | "
                   f"{x['bytes']:,} | `{x['sha256'][:16]}…` |")
    return "\n".join(out) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--purpose", required=True)
    ap.add_argument("--branch", default="")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = ap.parse_args(argv)
    sys.stdout.write(body(args.purpose, args.branch, args.repo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
