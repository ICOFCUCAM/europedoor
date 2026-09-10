#!/usr/bin/env python3
"""Fetch freely-licensed photographs into the register, one place at a time.

WHAT THIS IS FOR. `data/images.json` is the photograph register and it is
empty: `picture()` falls back to a generated plate for every key that has no
row, so the library adopts one photograph at a time rather than in a
migration. Everything downstream is already built and enforced — the
validator refuses a row missing a photographer, a source or a licence, and
`checks.py` refuses a published page referencing a file with no row. What was
missing was the thing that puts a row in.

IT CANNOT RUN HERE, AND THAT IS DELIBERATE. The sandbox answers 403 to CONNECT
for general hosts, and the build must run on a machine with no internet and
produce identical pages. So this is a step somebody runs — locally or in
GitHub Actions — exactly like `scripts/map/fetch.py`, and what it commits is
the file plus its register row.

CREDENTIALS COME FROM THE ENVIRONMENT AND ARE NEVER WRITTEN DOWN. No key in a
file, a commit, a workflow body or a log line. The provider table below names
the variable; it never holds a value, and this script refuses to print one.

THE LICENCE GATE IS THE SAME ONE THE MAP DATA HAS. `scripts/map/fetch.py`
refuses to open a socket for a source with no row in the register and no
licence document beside it. This does the same: a provider whose licence
questions in `docs/data-licenses/photo-providers.json` are unanswered is
refused before a request is made. The questions are there because the answers
must be read off the provider's live terms by a person — this repository
already records that nothing may be committed against a licence gate from a
marketing page or from memory.
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTER = os.path.join(ROOT, "data", "images.json")
GATE = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")
IMG_DIR = os.path.join(ROOT, "assets", "img")

# The licence VALUES the schema already accepts. A provider whose licence is
# not one of these cannot be added without widening tools/lib/data.py, which
# is the deliberate act it should be.
PROVIDERS = {
    "pexels": {
        "name": "Pexels",
        "env": "PEXELS_API_KEY",
        "licence": "Pexels",
        "endpoint": "https://api.pexels.com/v1/search",
        "auth": "header",
    },
    "unsplash": {
        "name": "Unsplash",
        "env": "UNSPLASH_ACCESS_KEY",
        "licence": "Unsplash",
        "endpoint": "https://api.unsplash.com/search/photos",
        "auth": "client-id",
    },
}


def gate():
    """The answered licence questions, or {} when the file is absent."""
    if not os.path.exists(GATE):
        return {}
    with open(GATE, encoding="utf-8") as fh:
        return json.load(fh)


def cleared(slug):
    """Whether this provider may be fetched from at all, and why not.

    Three questions have to be answered before a single request, and every
    one of them is a fact about the provider's live terms rather than a
    preference:

      self_host       may the file be downloaded and served from our origin?
                      This site's CSP is `img-src 'self' data:` and a check
                      refuses any third-party origin, so a provider that
                      requires hotlinking cannot be used without a decision
                      that changes both.
      attribution     the exact credit string the terms require. `picture()`
                      prints photographer and licence today; if the terms ask
                      for more, the renderer changes before the fetch runs.
      download_ping   some APIs require a request to a download endpoint when
                      an image is used. If true, `endpoint_download` must say
                      where.
    """
    row = gate().get(slug)
    if not row:
        return False, (f"{slug} has no row in docs/data-licenses/"
                       f"photo-providers.json — the licence is not written "
                       f"down, so nothing is fetched")
    # THIS READ THE FACT AND NOT ITS VALUE, AND HAD BEEN DEAD SINCE THE GATE
    # STARTED ASKING FOR A QUOTE. Each fact became {value, quote, source} in
    # the commit that made the gate demand the sentence, and this kept
    # comparing the whole object to the string "UNANSWERED" — so `unanswered`
    # was always empty and this branch never ran. What actually held the gate
    # was the line below it: a dict is not True, so every provider was refused
    # with a message about the CSP whatever was wrong. Refused for the wrong
    # reason is not the same as refused, because the reason is the thing
    # somebody acts on.
    def value(k):
        f = row.get(k)
        return f.get("value") if isinstance(f, dict) else f

    unanswered = [k for k in ("self_host", "attribution", "download_ping")
                  if value(k) in (None, "", "UNANSWERED")]
    if unanswered:
        return False, (f"{slug}: {', '.join(unanswered)} unanswered in the "
                       f"licence gate. Read the provider's terms and answer "
                       f"them; do not answer them from memory")
    # ANSWERED IS NOT THE SAME AS PERMITTED, AND THE THING REFUSED IS A ROUTE
    # RATHER THAN A PROVIDER. The first version of this conflated them and
    # refused Unsplash outright, which was wrong and was corrected by being
    # told so: the Unsplash LICENCE grants downloading, copying and
    # distribution outright, with two exclusions — selling unaltered images,
    # and compiling Unsplash images to replicate a competing service — and
    # this atlas does neither. What requires hotlinking is the API, and this
    # script IS an API client, so this is the refusal that belongs here. A
    # photograph obtained from the website under the licence and registered by
    # hand goes through no code path this function guards.
    if row.get("usable") is not True:
        return False, (f"{slug}: the licence gate is answered and this "
                       f"provider is REFUSED. "
                       + (row.get("unusable_because") or "no reason recorded"))
    api = row.get("api_route") or {}
    if api and api.get("usable") is not True:
        return False, (f"{slug}: the LICENCE permits use, and the API ROUTE is "
                       f"refused, which is the route this script takes. "
                       + (api.get("because") or "no reason recorded")
                       + " A photograph obtained from the website under the "
                         "licence can still be registered by hand.")
    if value("self_host") is not True:
        return False, (f"{slug}: self_host is not true. This site serves "
                       f"`img-src 'self' data:` and refuses a third-party "
                       f"origin, so a hotlink-only provider needs an owner "
                       f"decision that changes the CSP and that check")
    return True, ""


def key_for(slug):
    env = PROVIDERS[slug]["env"]
    val = os.environ.get(env, "").strip()
    if not val:
        sys.exit(f"{env} is not set. Put it in GitHub repository secrets and "
                 f"pass it to the workflow step; never in a file or a command "
                 f"line that gets logged.")
    return val


def search(slug, query, per_page=5):
    p = PROVIDERS[slug]
    key = key_for(slug)
    url = p["endpoint"] + "?" + urllib.parse.urlencode(
        {"query": query, "per_page": per_page, "orientation": "landscape"})
    req = urllib.request.Request(url)
    if p["auth"] == "header":
        req.add_header("Authorization", key)
    else:
        req.add_header("Authorization", f"Client-ID {key}")
    req.add_header("User-Agent", "EuropeDoor/1.0 (+https://europedoor.com)")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def candidates(slug, payload):
    """Provider payload -> [{id, photographer, page, download, width}].

    Normalised here so the rest of this script, and the person reading its
    output, never has to know whose API shape it came from.
    """
    out = []
    if slug == "pexels":
        for ph in payload.get("photos", []):
            out.append({"id": str(ph["id"]), "photographer": ph["photographer"],
                        "photographer_url": ph.get("photographer_url", ""),
                        "page": ph["url"], "download": ph["src"]["original"],
                        "width": ph.get("width", 0)})
    else:
        for ph in payload.get("results", []):
            out.append({"id": ph["id"],
                        "photographer": (ph.get("user") or {}).get("name", ""),
                        "photographer_url": ((ph.get("user") or {}).get("links") or {}).get("html", ""),
                        "page": (ph.get("links") or {}).get("html", ""),
                        "download": (ph.get("urls") or {}).get("full", ""),
                        "width": ph.get("width", 0)})
    return [c for c in out if c["photographer"] and c["page"] and c["download"]]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    ap.add_argument("--query", required=True,
                    help="what to search for, e.g. 'Vienna Stephansdom'")
    ap.add_argument("--key", help="the register key this would fill, "
                                  "e.g. city:austria/vienna-and-the-east/vienna")
    ap.add_argument("--alt", help="a caption for somebody who cannot see it — "
                                  "not the place name, which is the page title")
    ap.add_argument("--pick", type=int, default=None,
                    help="index from --list output. Without it, this only lists.")
    args = ap.parse_args(argv)

    ok, why = cleared(args.provider)
    if not ok:
        sys.exit("refused: " + why)

    found = candidates(args.provider, search(args.provider, args.query))
    if not found:
        sys.exit(f"no usable result for {args.query!r}")

    if args.pick is None:
        print(f"{len(found)} candidates for {args.query!r} on "
              f"{PROVIDERS[args.provider]['name']}:")
        for i, c in enumerate(found):
            print(f"  [{i}] {c['photographer']:24} {c['width']:>6}px  {c['page']}")
        print("\nLOOK AT THEM, then re-run with --pick N --key <key> --alt '<caption>'.")
        print("A photograph chosen from a filename is a photograph nobody looked at.")
        return 0

    if not args.key or not args.alt:
        sys.exit("--pick needs --key and --alt: a row without a caption is a "
                 "row the validator refuses, and correctly")
    if len(args.alt) < 12:
        sys.exit("--alt must describe the photograph, not repeat the place name")

    chosen = found[args.pick]
    stem = args.key.replace(":", "-").replace("/", "-")
    os.makedirs(IMG_DIR, exist_ok=True)
    dest = os.path.join(IMG_DIR, stem + ".src.jpg")
    req = urllib.request.Request(chosen["download"],
                                 headers={"User-Agent": "EuropeDoor/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        blob = r.read()
    with open(dest, "wb") as fh:
        fh.write(blob)

    # SOURCE + DATE + EVIDENCE, written at the moment the file arrives —
    # which is the only moment any of the three is knowable. A licence is a
    # claim about a moment; a row without the moment, and without the hash of
    # what was actually served, is a claim about nothing. The map datasets
    # have carried exactly this since the map was built.
    with open(REGISTER, encoding="utf-8") as fh:
        reg = json.load(fh)
    reg["images"][args.key] = {
        "file": stem,
        "alt": args.alt,
        "photographer": chosen["photographer"],
        "photographer_url": chosen.get("photographer_url") or "",
        "source": chosen["page"],
        "original_url": chosen["download"],
        "licence": PROVIDERS[args.provider]["licence"],
        "licence_url": gate()[args.provider]["terms_urls"][0],
        "fetched": datetime.date.today().isoformat(),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
        "focal": [50, 50],
    }
    with open(REGISTER, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"wrote {os.path.relpath(dest, ROOT)} and a register row for {args.key}")
    print("NEXT: scripts/images/derive.py builds the widths and formats "
          "picture() asks for. The build will not reference this photograph "
          "until those exist.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
