#!/usr/bin/env python3
"""Stage 1 of the map pipeline: DOWNLOAD -> VERIFY -> RECORD.

    python3 scripts/map/fetch.py            download anything missing
    python3 scripts/map/fetch.py --force    re-download everything
    python3 scripts/map/fetch.py --verify   check the bytes on disk, fetch nothing

This is the only place in the repository that opens a network socket, and it
is deliberately not part of `tools/build.py`. The build must run on a host with
no internet and produce identical pages, so the raw sources and the processed
geometry are both committed. Fetching is a thing a person does when a dataset
version changes, not a thing that happens on every deploy.

Three rules, each of which exists because the opposite is the normal failure:

1. **No entry in the register, no download.** The URL list lives in
   docs/data-licenses/sources.json, next to the licence records, so adding a
   dataset means writing down its terms in the same commit.

2. **No licence document, no download.** The `licence_doc` named by an entry
   must already exist as a file. A licence written after the data arrives is a
   licence written to fit what was already done.

3. **The `blocked` list is refused by id.** Naming a blocked dataset on the
   command line prints why it is blocked and exits non-zero. Eurostat NUTS is
   in that list; see docs/data-licenses/eurostat-gisco-nuts.md.

Stdlib only, like everything else here.
"""

import gzip
import hashlib
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTER = os.path.join(ROOT, "docs", "data-licenses", "sources.json")
LICDIR = os.path.join(ROOT, "docs", "data-licenses")

# GitHub answers a request with no User-Agent, but says so in the logs and is
# within its rights to stop. Identify the fetcher.
UA = "EuropeDoor-map-pipeline/1 (+https://europedoor.com; static site build)"


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load():
    with open(REGISTER, encoding="utf-8") as fh:
        return json.load(fh)


def save(reg):
    with open(REGISTER, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def read_local(path):
    """Return the bytes as stored — gzipped on disk stays gzipped here.

    The hash we record is the hash of the file in the repository, not of the
    decompressed content, because the point of the hash is 'is this the file I
    checked' and gzip is not deterministic across versions.
    """
    with open(path, "rb") as fh:
        return fh.read()


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read()


def store(path, raw):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith(".gz"):
        # mtime=0 so the same source produces the same bytes on every machine.
        # Without it every fetch shows as a change in `git diff` even when the
        # upstream file has not moved, and a diff that is always dirty is a
        # diff nobody reads.
        with open(path, "wb") as fh:
            with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
                gz.write(raw)
    else:
        with open(path, "wb") as fh:
            fh.write(raw)
    return read_local(path)


def main(argv):
    force = "--force" in argv
    verify = "--verify" in argv
    wanted = [a for a in argv[1:] if not a.startswith("-")]

    reg = load()
    blocked = {b["id"]: b for b in reg.get("blocked", [])}

    def refusal(src):
        """Which blocked entry a candidate source is, if any.

        THE BLOCK ONLY EVER FIRED ON THE ID TYPED ON THE COMMAND LINE.
        `blocked` was matched against argv and nothing else, and the loop
        over `sources` below never consulted it — so a row added to
        `sources` as, say, `osm-land-polygons`, pointing at
        openstreetmap.org, would have been fetched without the refusal
        printing a word. The guard was on the LABEL, and a label is chosen
        by whoever is adding the dataset.
        
        It matches the data now: the id, the URL and the dataset name, each
        against the patterns the blocked entry declares. Found by the Aegean
        experiment while it was reading this file to explain to a human how
        NOT to bypass it.
        """
        hay = " ".join((src.get("id", ""), src.get("url", ""),
                        src.get("dataset", ""))).lower()
        for b in blocked.values():
            if src.get("id") == b["id"]:
                return b
            for pat in b.get("refuse_matching", []):
                if pat.lower() in hay:
                    return b
        return None

    def refuse(name, b):
        print(f"REFUSED: {name} — {b['dataset']}")
        print(f"  licence: {b['licence']}")
        print(f"  reason:  {b['reason']}")
        print(f"  read:    docs/data-licenses/{b['licence_doc']}")

    for name in wanted:
        if name in blocked:
            refuse(name, blocked[name])
            return 2

    # And every row in the register, whatever it calls itself.
    for src in reg["sources"]:
        b = refusal(src)
        if b:
            refuse(src["id"], b)
            print(f"  matched: {src.get('url', '')}")
            print(f"  This row is in `sources`, not `blocked`, and would "
                  f"otherwise have been downloaded.")
            return 2

    # `awaiting_fetch` rows are registered and not in the repository. They
    # are fetched by the same loop and go through the same blocked-pattern
    # refusal, because a row's list does not decide whether it is allowed —
    # the data does. After a successful fetch the row is moved to `sources`
    # with its sha256, and `checks.py` fails if one is left here with its
    # file present.
    todo = list(reg["sources"]) + list(reg.get("awaiting_fetch", []))
    for src in todo:
        b = refusal(src)
        if b:
            refuse(src["id"], b)
            return 2

    bad = 0
    for src in todo:
        if wanted and src["id"] not in wanted:
            continue
        path = os.path.join(ROOT, src["path"])
        doc = os.path.join(LICDIR, src["licence_doc"])
        if not os.path.exists(doc):
            print(f"REFUSED: {src['id']} has no licence record at "
                  f"docs/data-licenses/{src['licence_doc']}")
            bad += 1
            continue

        if verify:
            if not os.path.exists(path):
                # An `awaiting_fetch` row is SUPPOSED to be absent. Counting
                # it as a failure would make the documented verify gate red
                # for the ordinary state of the repository, and a gate that
                # is red when nothing is wrong is a gate people stop running.
                if src.get("fills_layer"):
                    print(f"awaiting {src['id']:<16} {src['path']} "
                          f"— fills the {src['fills_layer']} layer")
                    continue
                print(f"MISSING  {src['id']:<16} {src['path']}")
                bad += 1
                continue
            got = sha256(read_local(path))
            if src["sha256"] and got != src["sha256"]:
                print(f"CHANGED  {src['id']:<16} recorded {src['sha256'][:12]} "
                      f"on disk {got[:12]}")
                bad += 1
            else:
                print(f"ok       {src['id']:<16} {src['bytes']:>9,} bytes  "
                      f"{got[:12]}")
            continue

        if os.path.exists(path) and not force:
            print(f"have     {src['id']:<16} {src['path']}")
            continue

        print(f"fetch    {src['id']:<16} {src['url']}")
        try:
            raw = download(src["url"])
        except Exception as exc:            # noqa: BLE001 — report, do not crash
            print(f"  FAILED: {exc}")
            bad += 1
            continue
        stored = store(path, raw)
        src["sha256"] = sha256(stored)
        src["bytes"] = len(stored)
        src["fetched"] = __import__("datetime").date.today().isoformat()
        print(f"  {len(raw):,} bytes source -> {len(stored):,} on disk  "
              f"{src['sha256'][:12]}")

    if not verify:
        save(reg)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
