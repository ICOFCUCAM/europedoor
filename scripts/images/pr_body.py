#!/usr/bin/env python3
"""Write the pull-request body for an acquired photograph, from the register.

    python3 scripts/images/pr_body.py --purpose homepage-hero --branch photo/x
    python3 scripts/images/pr_body.py --purpose a,b,c --branch photo/batch-x

ONE PURPOSE OR MANY, AND A BATCH IS NOT A DIFFERENT DOCUMENT. A country's
worth of destination portraits arrives as one branch and one pull request,
because thirteen pull requests for one editorial decision is thirteen places
for a reviewer to lose track of what they already looked at. The per-
photograph evidence is identical and stays identical — the same table, read
out of the same register — and what a batch adds is a summary above it and a
`<details>` around each one, so a reviewer meets the set before the rows.

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


def _row_for(purpose):
    reg = json.load(open(os.path.join(ROOT, "data", "images.json"),
                         encoding="utf-8"))["images"]
    rows = [(k, r) for k, r in reg.items() if r.get("purpose") == purpose]
    if not rows:
        sys.exit(f"no register row for purpose {purpose!r} — the acquisition "
                 f"did not complete, and a PR describing nothing must not open")
    return rows[0]


def body(purposes, branch, repo_slug=""):
    """One photograph or many. The evidence per photograph never changes."""
    names = [p.strip() for p in purposes.split(",") if p.strip()]
    if len(names) == 1:
        return _one(names[0], branch, repo_slug) + _checklist()
    parts = _summary(names, branch)
    for n in names:
        key, r = _row_for(n)
        parts += ["", f"<details><summary><b>{r['purpose']}</b> — "
                      f"{r['photographer']}, {r['width']}×{r['height']}"
                      f"</summary>", ""]
        parts.append(_one(n, branch, repo_slug))
        parts += ["", "</details>"]
    return "\n".join(parts) + "\n" + _checklist()


def _summary(names, branch):
    """WHAT ARRIVED, BEFORE ANY OF IT. A reviewer meets the set first."""
    rows = [_row_for(n) for n in names]
    total = sum(r["bytes"] for _, r in rows)
    derived = sum(len(r.get("derivatives") or {}) for _, r in rows)
    out = [f"## {len(rows)} photographs acquired", "",
           f"One branch, one pull request. `{branch}`", "",
           "| purpose | photographer | original | id |", "|---|---|---|---|"]
    for _, r in rows:
        out.append(f"| `{r['purpose']}` | "
                   f"[{r['photographer']}]({r['photographer_url']}) | "
                   f"{r['width']}×{r['height']} | "
                   f"[{r['provider_photo_id']}]({r['source']}) |")
    out += ["", f"{total:,} bytes of originals, kept untouched, and "
                f"{derived} derivatives built from them.", "",
            "Every row below is read out of `data/images.json` rather than "
            "typed here, so this description cannot name a photograph other "
            "than the ones committed."]
    return out


def _one(purpose, branch, repo_slug=""):
    key, r = _row_for(purpose)
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

    out += ["### Derivatives", "",
            "| file | pixels | bytes | sha256 |", "|---|---|---|---|"]
    for name in sorted(d):
        x = d[name]
        out.append(f"| `{name}` | {x['width']}×{x['height']} | "
                   f"{x['bytes']:,} | `{x['sha256'][:16]}…` |")
    return "\n".join(out) + "\n"


def _checklist():
    """THE NUMBERS ARE NOT THE DECISION, and it is said ONCE however many
    photographs arrived. Every figure above says the pipeline worked; none of
    them says the photograph is right for the surface, and that is the only
    question a human is here to answer. Repeating it under each of thirteen
    photographs is boilerplate, and boilerplate is what a reader learns to
    skip — which on this list is the whole point of the list."""
    return "\n".join([
        "", "### What to check before merging", "",
        "- Does each one look like this place on a particular morning, or "
        "like generic stock?",
        "- Subject placement against the headline and the masthead over it.",
        "- Contrast under the type; no watermark; nothing misleading about "
        "the subject.",
        "- The credit renders as the provider's terms require: a link to the "
        "photo page and a link to the provider.",
        "",
        "Everything above this line is mechanical and already passed. This "
        "list is the part that is not.", ""])


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--purpose", required=True,
                    help="one purpose, or several separated by commas")
    ap.add_argument("--branch", default="")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = ap.parse_args(argv)
    sys.stdout.write(body(args.purpose, args.branch, args.repo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
