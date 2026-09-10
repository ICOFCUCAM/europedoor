#!/usr/bin/env python3
"""Acquire ONE approved photograph by its provider id, and record what arrived.

    python3 scripts/images/acquire.py --provider pexels \\
        --photo-id 2014422 --purpose homepage-hero \\
        --alt "The Danube at dusk from the Leopoldsberg, the city beyond it"

THE HUMAN DECISION IS WHICH PHOTOGRAPH. EVERYTHING AFTER IT IS MECHANICAL,
and this script is the mechanical half. It is run by GitHub Actions with the
key in the environment, and what it leaves behind is a file, an untouched
original, and a register row nobody typed.

WHY THIS REPLACED `--pick 3`. The previous version listed search results and
took one BY POSITION. "The fourth result" is not a photograph, it is a
photograph's rank in a search performed at some moment — and a search
performed a minute later reorders. So the picture a person approved and the
picture that arrived could differ, silently, with every provenance field
correctly recorded about the wrong one. Nothing in the register would look
wrong. That is the worst kind of fault this repository can ship, because the
evidence would agree with itself.

An id is identity. `GET /v1/photos/:id` returns that photograph or nothing,
and this script ASSERTS THE RETURNED ID EQUALS THE REQUESTED ONE before a
byte is written — because "the API returned something" is not "the API
returned what was asked for", and a provider is free to redirect, alias or
merge ids without telling anybody.

WHAT IT REFUSES, IN ORDER, BEFORE ANY NETWORK REQUEST:

  * a provider whose licence gate is unanswered
  * a provider whose gate answers `automated_acquisition: false` — this is
    where Unsplash stops, and it stops here rather than in a comment
  * a purpose that is not declared in data/image-purposes.json
  * a purpose already filled by a different photograph

and after the metadata call, before the download:

  * a returned id that is not the requested id
  * a photograph that fails the purpose's stated minimum: native width,
    orientation, aspect

NO RETRIES. A failed acquisition fails. The instruction is explicit that a
requested id which cannot be retrieved must stop the workflow rather than
quietly become a different photograph, and a retry loop around a download is
how one approved id turns into four requests against a rate limit.

THE KEY IS READ FROM THE ENVIRONMENT AND NEVER PRINTED. Not into a log, not
into the register, not into an error. The provider table names the variable
and never holds a value.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTER = os.path.join(ROOT, "data", "images.json")
PURPOSES = os.path.join(ROOT, "data", "image-purposes.json")
GATE = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")
IMG_DIR = os.path.join(ROOT, "assets", "img")
# THE ORIGINAL IS EVIDENCE, NOT AN ASSET, and it lives outside assets/ for
# that reason. Under assets/ it would be published, and published under a
# prefix served `immutable` at a filename that can change — the exact cache
# bug this repository already shipped once on the stylesheet. It is also
# multi-megabyte and nobody's browser should ever be offered it. Kept in the
# repository because it is the only thing the whole processing chain can be
# re-checked against.
ORIG_DIR = os.path.join(ROOT, "photographs")

USER_AGENT = "EuropeDoor/1.0 (+https://europedoor.com)"

# The licence VALUES tools/lib/data.py already accepts. Adding a provider is
# an edit here AND an answered gate row AND a widened schema — three
# deliberate acts, which is the right number for admitting somebody else's
# photographs onto this site.
PROVIDERS = {
    "pexels": {
        "name": "Pexels",
        "env": "PEXELS_API_KEY",
        "licence": "Pexels",
        "api_base_env": "PEXELS_API_BASE",
        "api_base": "https://api.pexels.com/v1",
        "auth": "header",
    },
    "unsplash": {
        "name": "Unsplash",
        "env": "UNSPLASH_ACCESS_KEY",
        "licence": "Unsplash",
        "api_base_env": "UNSPLASH_API_BASE",
        "api_base": "https://api.unsplash.com",
        "auth": "client-id",
    },
}

FACTS = ("self_host", "attribution", "download_ping", "automated_acquisition")


def gate():
    if not os.path.exists(GATE):
        return {}
    with open(GATE, encoding="utf-8") as fh:
        return json.load(fh)


def purposes():
    with open(PURPOSES, encoding="utf-8") as fh:
        return json.load(fh)["purposes"]


def register():
    with open(REGISTER, encoding="utf-8") as fh:
        return json.load(fh)


def _value(row, fact):
    f = row.get(fact)
    return f.get("value") if isinstance(f, dict) else f


def cleared(slug):
    """(ok, why) for the AUTOMATED route. The gate is the only authority."""
    row = gate().get(slug)
    if not row:
        return False, (f"{slug} has no row in docs/data-licenses/"
                       f"photo-providers.json — the licence is not written "
                       f"down, so nothing is fetched")
    unanswered = [k for k in FACTS
                  if _value(row, k) in (None, "", "UNANSWERED")]
    if unanswered:
        return False, (f"{slug}: {', '.join(unanswered)} unanswered in the "
                       f"licence gate. Read the provider's terms and answer "
                       f"them; do not answer them from memory")
    # THE ONE THAT DECIDES THIS ROUTE. Unsplash's licence permits self-hosting
    # and its API does not: "All API uses must use the hotlinked image URLs
    # returned by the API." Acquire-then-self-host is exactly what that
    # forbids, so the automated path stops here and says which document said
    # so.
    if _value(row, "automated_acquisition") is not True:
        return False, (
            f"{slug}: REFUSED for automated acquisition. "
            + "The provider's own words: \""
            + ((row.get("automated_acquisition") or {}).get("quote") or "")
            + "\" — "
            + ((row.get("automated_acquisition") or {}).get("basis")
               or "no basis recorded")
            + " This script is the automated path; it does not have a manual "
              "mode and must not grow one.")
    # BOTH REFUSALS, BECAUSE THEY ARE DIFFERENT QUESTIONS. `api_route` says
    # whether the API may be used at all under this site's constraints;
    # `automated_acquisition` says whether an unattended job may do it. A
    # provider could clear one and not the other, and reading only the second
    # was a hole my own check found before any photograph went through it.
    api = row.get("api_route") or {}
    if api and api.get("usable") is not True:
        return False, (f"{slug}: the API route is refused. "
                       + (api.get("because") or "no reason recorded"))
    if _value(row, "self_host") is not True:
        return False, (f"{slug}: self_host is not true. This site serves "
                       f"`img-src 'self' data:` and refuses a third-party "
                       f"origin")
    if _value(row, "download_ping") is True and not row.get("endpoint_download"):
        return False, (f"{slug}: a download event is required and no "
                       f"endpoint_download is recorded")
    return True, ""


def key_for(slug):
    env = PROVIDERS[slug]["env"]
    val = os.environ.get(env, "").strip()
    if not val:
        sys.exit(f"{env} is not set. It lives in GitHub repository secrets "
                 f"and is passed as `env` on the one step that needs it; "
                 f"never in a file, a command line or a log.")
    return val


def api_base(slug):
    p = PROVIDERS[slug]
    # Overridable so the tests can point at a local stub. It is a base URL,
    # never a credential, and the tests are the reason it exists.
    return os.environ.get(p["api_base_env"]) or p["api_base"]


def get_json(slug, path):
    req = urllib.request.Request(api_base(slug) + path)
    key = key_for(slug)
    req.add_header("Authorization",
                   key if PROVIDERS[slug]["auth"] == "header"
                   else f"Client-ID {key}")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), dict(r.headers)
    except urllib.error.HTTPError as exc:
        # RATE LIMITING FAILS LOUDLY AND CHANGES NOTHING. No backoff loop, no
        # second provider, no other photograph: the state on disk is exactly
        # what it was, and the id that was approved is still the id to ask
        # for when the quota resets.
        if exc.code in (429, 403):
            sys.exit(f"{slug} answered {exc.code}. That is the rate limit or "
                     f"a revoked key. Nothing was downloaded and nothing was "
                     f"written. Re-run this exact photo id when the quota "
                     f"resets; do not substitute another photograph.")
        sys.exit(f"{slug} answered {exc.code} for {path}. Nothing written.")


def photo(slug, photo_id):
    """The one photograph, by id, normalised — never a list, never a position."""
    if slug == "pexels":
        payload, headers = get_json(slug, f"/photos/{urllib.parse.quote(photo_id)}")
        got = str(payload.get("id", ""))
        src = payload.get("src") or {}
        norm = {
            "id": got,
            "photographer": payload.get("photographer") or "",
            "photographer_url": payload.get("photographer_url") or "",
            "page": payload.get("url") or "",
            "download": (src.get("original") or "").split("?")[0],
            "width": int(payload.get("width") or 0),
            "height": int(payload.get("height") or 0),
            "alt": payload.get("alt") or "",
        }
    else:  # pragma: no cover - unreachable while the gate refuses it
        sys.exit(f"{slug} has no automated acquisition path and must not "
                 f"acquire one here")
    return norm, payload, headers


def fits(norm, spec):
    """The mechanical half of 'is this photograph suitable'. Never the whole."""
    bad = []
    if norm["width"] < spec["min_width"]:
        bad.append(f"native width {norm['width']}px is under the "
                   f"{spec['min_width']}px this purpose needs — the ladder "
                   f"never upscales, so a smaller original means a smaller "
                   f"picture rather than a softer one")
    if not norm["height"]:
        bad.append("no height reported")
        return bad
    aspect = norm["width"] / norm["height"]
    want = spec.get("orientation")
    if want == "landscape" and aspect <= 1.0:
        bad.append(f"orientation is not landscape ({norm['width']}x{norm['height']})")
    if want == "portrait" and aspect >= 1.0:
        bad.append(f"orientation is not portrait ({norm['width']}x{norm['height']})")
    if "min_aspect" in spec and aspect < spec["min_aspect"]:
        bad.append(f"aspect {aspect:.2f} is below {spec['min_aspect']}")
    if "max_aspect" in spec and aspect > spec["max_aspect"]:
        bad.append(f"aspect {aspect:.2f} is above {spec['max_aspect']}")
    return bad


def evidence(grow):
    """Which archived readings of the terms this acquisition happened under."""
    return sorted((grow.get("terms_snapshot") or {}).values())


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    ap.add_argument("--photo-id", required=True,
                    help="the provider's own id for the EXACT photograph a "
                         "person approved. Never an index into a search.")
    ap.add_argument("--purpose", required=True,
                    help="a purpose declared in data/image-purposes.json")
    ap.add_argument("--alt", required=True,
                    help="what the photograph shows, for somebody who cannot "
                         "see it — not the place name, which is the page title")
    ap.add_argument("--focal", default="50,50",
                    help="focal point as x,y percentages")
    args = ap.parse_args(argv)

    ok, why = cleared(args.provider)
    if not ok:
        sys.exit("REFUSED: " + why)

    specs = purposes()
    if args.purpose not in specs:
        sys.exit(f"{args.purpose!r} is not a declared purpose. Declare it in "
                 f"data/image-purposes.json with the surface it fills and "
                 f"what a photograph must be to fill it. Known: "
                 + ", ".join(sorted(specs)))
    spec = specs[args.purpose]

    reg = register()
    # A PURPOSE HOLDS ONE PHOTOGRAPH. Re-acquiring the SAME id for the same
    # purpose is a replay and is allowed; a different id silently taking over
    # a surface is the drift this field exists to stop.
    existing = reg["images"].get(spec["key"])
    if existing and str(existing.get("provider_photo_id")) != str(args.photo_id):
        sys.exit(f"{args.purpose} is already filled by "
                 f"{existing.get('provider')} {existing.get('provider_photo_id')}. "
                 f"Remove that row deliberately if it is being replaced — a "
                 f"surface changing its picture is an editorial act, not a "
                 f"side effect of running this twice.")

    if len(args.alt) < 12:
        sys.exit("--alt must describe the photograph. A row without a real "
                 "caption is a row the validator refuses, and correctly.")

    norm, payload, _headers = photo(args.provider, args.photo_id)

    # THE RETURNED ID MUST BE THE REQUESTED ID. "It answered 200" is not "it
    # answered with the photograph that was approved" — ids get aliased,
    # merged and redirected, and a mismatch here is the whole failure this
    # design exists to prevent.
    if norm["id"] != str(args.photo_id):
        sys.exit(f"asked {args.provider} for photo {args.photo_id} and it "
                 f"returned {norm['id']!r}. Nothing written. A different "
                 f"photograph is not a fallback.")
    if not norm["download"] or not norm["page"] or not norm["photographer"]:
        sys.exit(f"{args.provider} {args.photo_id} is missing a photographer, "
                 f"a page or an original — provenance would be incomplete and "
                 f"an incomplete row must never exist.")

    bad = fits(norm, spec)
    if bad:
        sys.exit(f"photo {args.photo_id} does not suit {args.purpose}:\n  - "
                 + "\n  - ".join(bad)
                 + "\nChoose another candidate; do not lower the purpose.")

    grow = gate()[args.provider]
    stem = args.purpose
    os.makedirs(ORIG_DIR, exist_ok=True)
    original = os.path.join(ORIG_DIR, stem + ".original.jpg")

    req = urllib.request.Request(norm["download"],
                                 headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            blob = r.read()
    except urllib.error.HTTPError as exc:
        sys.exit(f"downloading {norm['download']} answered {exc.code}. "
                 f"Nothing written.")
    if len(blob) < 10_000:
        sys.exit(f"the original is {len(blob)} bytes, which is an error page "
                 f"rather than a photograph. Nothing written.")

    digest = hashlib.sha256(blob).hexdigest()
    acquired_at = datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat().replace("+00:00", "Z")

    # THE ORIGINAL IS KEPT UNTOUCHED. It is the evidence the whole processing
    # chain can be re-checked against: derive.py reads it and writes beside
    # it, and checks.py re-hashes it on every build. Nothing overwrites it
    # with a resized copy, which is the one way a provenance hash quietly
    # stops meaning anything.
    with open(original, "wb") as fh:
        fh.write(blob)

    fx, fy = (args.focal.split(",") + ["50"])[:2]
    reg["images"][spec["key"]] = {
        "purpose": args.purpose,
        "publication_path": spec["path"],
        "file": stem,
        "original": os.path.relpath(original, ROOT),
        "alt": args.alt,
        "provider": args.provider,
        "provider_photo_id": norm["id"],
        "photographer": norm["photographer"],
        "photographer_url": norm["photographer_url"],
        "source": norm["page"],
        "original_url": norm["download"],
        "licence": PROVIDERS[args.provider]["licence"],
        "licence_url": grow["terms_urls"][0],
        "terms_read_on": grow.get("read_on") or "",
        "terms_evidence": evidence(grow),
        "fetched": acquired_at[:10],
        "acquired_at": acquired_at,
        "sha256": digest,
        "bytes": len(blob),
        "width": norm["width"],
        "height": norm["height"],
        "focal": [int(fx), int(fy)],
        # derive.py fills this in. Until it does the row is INCOMPLETE and the
        # validator says so, which is the point: a half-registered photograph
        # must never look valid.
        "processing": None,
        "derivatives": None,
    }
    with open(REGISTER, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"acquired {args.provider} photo {norm['id']} for {args.purpose}")
    print(f"  photographer  {norm['photographer']}")
    print(f"  source        {norm['page']}")
    print(f"  original      {norm['width']}x{norm['height']}, {len(blob):,} bytes")
    print(f"  sha256        {digest}")
    print(f"  saved         {os.path.relpath(original, ROOT)}")
    print("\nNEXT: scripts/images/derive.py builds the ladder and completes "
          "the provenance. The register row is incomplete until it does.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
