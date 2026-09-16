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


# GITHUB REFUSES A BODY OVER 65,536 CHARACTERS, and that is a hard limit on
# the createPullRequest mutation rather than a style rule. Runs 35 and 36 both
# acquired sixty photographs, rebuilt, passed the credential scan, pushed and
# passed EVERY gate — and then died on the last step before the merge with
# `GraphQL: Body is too long`, because this file writes a section per
# photograph and sixty of them measure about 188,000 characters.
#
# It is the dispatch cap's own lesson one step further on: the cap is 60
# because that is what one pull request can carry a REVIEWER through, and
# nobody had asked what one pull request can carry at all.
BODY_MAX = 65_536


def body(purposes, branch, repo_slug="", skipped=()):
    """One photograph or many. The evidence per photograph never changes."""
    names = [p.strip() for p in purposes.split(",") if p.strip()]
    if len(names) == 1:
        return (_one(names[0], branch, repo_slug)
                + _skipped(skipped) + _checklist())
    head = _summary(names, branch)
    tail = _skipped(skipped) + _checklist()
    parts = list(head)
    for n in names:
        key, r = _row_for(n)
        parts += ["", f"<details><summary><b>{r['purpose']}</b> — "
                      f"{r['photographer']}, {r['width']}×{r['height']}"
                      f"</summary>", ""]
        parts.append(_one(n, branch, repo_slug))
        parts += ["", "</details>"]
    full = "\n".join(parts) + "\n" + tail
    if len(full) <= BODY_MAX:
        return full

    # ALL OF THE DETAIL OR NONE OF IT. About eighteen of sixty blocks fit,
    # and a body carrying eighteen is a SELECTION — the fault this repository
    # already records about a photograph row that showed eight of eleven and
    # said nothing. Which eighteen would be decided by register order, which
    # is not an editorial judgement about anything.
    #
    # WHAT IS DROPPED IS THE REPEATED EVIDENCE, NEVER THE SET AND NEVER THE
    # QUESTION. The summary names every photograph, its photographer, its
    # dimensions and a link to its source page — one row each, which scales —
    # and the checklist is the only part a human is here for. What goes is the
    # per-photograph table, and it goes to the place that already holds it.
    short = "\n".join(head + _register_is_the_record(names, len(full))) + "\n" + tail
    if len(short) <= BODY_MAX:
        return short

    # AND A BODY THAT STILL CANNOT FIT SAYS SO RATHER THAN BEING CUT. A
    # truncated description that does not mention being truncated is
    # present-but-empty: it reads as the whole record. This cannot be reached
    # at the current dispatch cap and is here because the cap is a number
    # somebody may raise.
    return "\n".join(
        [f"## {len(names)} photographs acquired", "",
         f"One branch, one pull request. `{branch}`", "",
         f"The description of {len(names)} photographs does not fit a "
         f"GitHub pull-request body ({BODY_MAX:,} characters), and a summary "
         f"of them does not either. **Every field for every one of them is "
         f"in `data/images.json` in this branch** — photographer, licence, "
         f"source page, the SHA-256 of the bytes as served, and every "
         f"derivative. Nothing is omitted from the commit; only from this "
         f"description."]) + "\n" + tail


def _register_is_the_record(names, was):
    """WHERE THE EVIDENCE WENT, said in the body rather than left to be
    noticed. `data/images.json` is committed in the same branch and is what
    every figure in this file is read out of, so pointing at it is pointing
    at the source rather than at a substitute."""
    return ["", "### The per-photograph evidence is in the register", "",
            f"A table per photograph would make this description about "
            f"{was:,} characters and GitHub refuses a body over "
            f"{BODY_MAX:,}, so all {len(names)} of them are omitted here "
            f"rather than the first eighteen kept — a body carrying some of "
            f"them would be a selection, and register order is not an "
            f"editorial judgement.",
            "",
            "**Nothing is missing from the commit.** `data/images.json` in "
            "this branch carries every field this description would have "
            "shown, for every photograph: the provider and photo id, the "
            "photographer and their page, the source page, the licence and "
            "the date its terms were read, the original's pixel dimensions, "
            "byte count and SHA-256, and every derivative with its own "
            "dimensions, bytes and hash. The table above is read out of that "
            "same file.",
            ""]


def _skipped(rows):
    """WHAT DID NOT ARRIVE, AND WHY, BESIDE WHAT DID.

    A batch used to be all-or-nothing: one candidate that did not suit its
    slot ended the job, so run 23 discarded eighteen finished acquisitions
    over the nineteenth. A batch that carries on has to say what it left
    behind, or a reviewer cannot tell "these are the sixty that were
    approved" from "these are the ones that happened to work" — which is the
    reason all-or-nothing was chosen in the first place, and it is answered
    by naming them rather than by losing the sitting.

    The surfaces below are still EMPTY. Nothing was substituted for them.
    """
    if not rows:
        return ""
    out = ["", f"### {len(rows)} approved and not acquired", "",
           "These surfaces are still empty and nothing was substituted for "
           "them. Pick again for any that are worth another look — the "
           "basket keeps what you already chose.", "",
           "| surface | id | why |", "|---|---|---|"]
    for purpose, pid, why in rows:
        out.append(f"| `{purpose}` | {pid} | {why} |")
    return "\n".join(out) + "\n"


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
    ap.add_argument("--skipped", default="",
                    help="a TSV of purpose, id and reason for every approved "
                         "candidate the acquisition refused — read from a "
                         "file rather than the register, because the whole "
                         "point of these rows is that they have none")
    args = ap.parse_args(argv)
    skipped = []
    if args.skipped and os.path.exists(args.skipped):
        with open(args.skipped, encoding="utf-8") as fh:
            for line in fh:
                bits = line.rstrip("\n").split("\t")
                if len(bits) >= 3 and bits[0]:
                    skipped.append((bits[0], bits[1], bits[2]))
    sys.stdout.write(body(args.purpose, args.branch, args.repo, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
