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


# A PURPOSE IS EITHER DECLARED OR IS AN INSTANCE OF A SLOT.
#
# `vienna-destination` and `chamonix-destination` were two hand-written rows
# saying the same thing about two of 319 destination pages, and the other 317
# could not be acquired for at all. A slot is the template and
# `destination-hero@france/alps-and-east/chamonix` is the instance; the
# register key is derived from the template, so a row cannot claim a key the
# slot would not produce. tools/lib/imageslots.py owns the resolution and is
# the only place that does it — the Media Desk, the validator and this script
# all ask it, so none of them can disagree about what a purpose is.
sys.path.insert(0, os.path.join(ROOT, "tools"))


def spec_for(name):
    """The spec for a purpose name, and the data needed to resolve a slot."""
    from lib import imageslots
    from lib.data import load
    return imageslots.resolve(name, load()), imageslots


def register():
    with open(REGISTER, encoding="utf-8") as fh:
        return json.load(fh)


def _value(row, fact):
    f = row.get(fact)
    return f.get("value") if isinstance(f, dict) else f


def jpeg_size(blob):
    """(width, height) from a JPEG's own SOF marker, or None.

    A JPEG is a chain of segments: 0xFFD8, then markers each carrying a
    two-byte big-endian length. The frame header — SOF0 through SOF15, minus
    the four that are not frame headers — holds height then width as two-byte
    values three bytes in. Walking to it reads a few dozen bytes and proves
    the file is a JPEG at the same time, because a walk that falls off the end
    of a truncated or non-JPEG file returns None rather than a number.
    """
    if not blob.startswith(b"\xff\xd8"):
        return None
    i, n = 2, len(blob)
    while i + 9 < n:
        if blob[i] != 0xFF:
            return None
        marker = blob[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg = int.from_bytes(blob[i + 2:i + 4], "big")
        if seg < 2:
            return None
        # SOF0-SOF15 except DHT (C4), JPG (C8) and DAC (CC), which share the
        # range and are not frame headers.
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h = int.from_bytes(blob[i + 5:i + 7], "big")
            w = int.from_bytes(blob[i + 7:i + 9], "big")
            return (w, h) if w and h else None
        i += 2 + seg
    return None


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
    ap.add_argument("--second-purpose", action="store_true",
                    help="this photograph is already in the register for a "
                         "DIFFERENT purpose and that is intended")
    args = ap.parse_args(argv)

    ok, why = cleared(args.provider)
    if not ok:
        sys.exit("REFUSED: " + why)

    specs = purposes()
    spec, imageslots = spec_for(args.purpose)
    if spec is None:
        sys.exit(f"{args.purpose!r} is not a purpose. Declare it in "
                 f"data/image-purposes.json with the surface it fills and "
                 f"what a photograph must be to fill it, or name an instance "
                 f"of a slot as slot@target.\n"
                 f"  declared: " + ", ".join(sorted(specs)) + "\n"
                 f"  slots:    " + ", ".join(sorted(imageslots.slots())))

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

    # AND ONE PHOTOGRAPH IS NOT AUTOMATICALLY MEANT FOR TWO SURFACES.
    #
    # The rule above is about a SURFACE and reads the register by key; this is
    # the same question from the other end and the register had no answer for
    # it — the same provider id could be acquired again, for a second purpose,
    # and nothing anywhere would say so. Twice is sometimes right: a
    # photograph good enough for a door may be right for the index it opens.
    # What is never right is arriving there by accident, so it is a refusal
    # with an escape rather than a warning nobody reads, and the refusal names
    # every purpose the id already fills.
    elsewhere = sorted(
        (row.get("purpose") or key)
        for key, row in reg["images"].items()
        if row.get("provider") == args.provider
        and str(row.get("provider_photo_id")) == str(args.photo_id)
        and key != spec["key"])
    if elsewhere and not args.second_purpose:
        sys.exit(f"{args.provider} {args.photo_id} is already in the register, "
                 f"for {', '.join(elsewhere)}. One photograph on two surfaces "
                 f"is sometimes right and is never an accident — pass "
                 f"--second-purpose if that is what this is.")

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
    stem = imageslots.stem(args.purpose)
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

    # THE BYTES ARE VERIFIED AGAINST WHAT THE API PROMISED, AND A LENGTH
    # FLOOR IS NOT THAT.
    #
    # Everything before this point checks the METADATA: the id came back the
    # id we asked for, the photographer is present, the declared width suits
    # the slot. Then a URL out of that same payload is fetched and the result
    # was accepted on one test — "more than ten kilobytes" — which passes for
    # a truncated transfer, a differently-sized re-encode, and any image at
    # all that happens to be large.
    #
    # It matters because the DECLARED size is what cleared the slot. Pexels
    # said 12000x9000 and `fits()` admitted the candidate on that number; if
    # the bytes are 1200x900 then a photograph that does not meet the slot has
    # been hashed, registered and committed with a correct-looking provenance
    # row, and the only thing that would ever notice is derive.py refusing to
    # upscale — a step later, in a different script, with the register already
    # written.
    #
    # NO PILLOW HERE, DELIBERATELY. This script has no image dependency and
    # installing one to read two numbers out of a header is how a dependency
    # arrives without a reason; derive.py installs Pillow because it decodes
    # pixels. A JPEG's own SOF marker carries the dimensions in six bytes.
    got = jpeg_size(blob)
    if got is None:
        sys.exit(f"the bytes from {args.provider} are not a JPEG. The "
                 f"provenance row would record a hash of something this "
                 f"pipeline cannot derive from. Nothing written.")
    if got != (norm["width"], norm["height"]):
        sys.exit(f"{args.provider} described photo {args.photo_id} as "
                 f"{norm['width']}x{norm['height']} and served "
                 f"{got[0]}x{got[1]}. The description is what cleared this "
                 f"slot, so the file does not. Nothing written.")

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
