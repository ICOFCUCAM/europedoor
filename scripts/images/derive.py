#!/usr/bin/env python3
"""Build the widths and formats `picture()` asks for, from one source file.

`render.picture()` emits a <picture> with three formats at five widths:

    /assets/img/<file>-{480,800,1260,1800,2400}.{avif,webp,jpg}

Fifteen files per photograph, and `checks.py` already refuses a page whose
`src` does not resolve — so a register row without its derivatives fails the
build rather than shipping a broken image. That is the right order: the row is
the claim and the files are the evidence.

PILLOW, AND THE SISTER REPOSITORY IS WHY. It encodes 629 photographs this way
and the shape is proven; the first version of this file shelled out to
ImageMagick, which is one more thing to have installed and one more place for
a quality flag to mean something different. This is not part of the build —
the build is stdlib-only and runs with no network — it is a step somebody runs
in the `photograph` workflow, where a dependency costs nothing.

THE ORIGINAL IS KEPT. A better encoder, or a width this ladder does not have
yet, must not mean going back to the provider for a file we already hold —
and after the register row exists, that file is the evidence the licence claim
rests on.

NEVER UPSCALE, and the reason is sharper than saving bytes: a browser choosing
between a real 1260 and a fake 1800 will take the fake one. A file named
-2400 holding 900 pixels of detail is the same class of untruth as a
population we estimated.
"""

import datetime
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from lib.render import IMAGE_WIDTHS                       # noqa: E402

IMG_DIR = os.path.join(ROOT, "assets", "img")
REGISTER = os.path.join(ROOT, "data", "images.json")
# Per-format quality, taken from the sister repository's settled values rather
# than guessed here. AVIF carries far more at a lower number than JPEG does.
QUALITY = {"avif": 50, "webp": 78, "jpg": 82}


def _original_of(stem):
    """The path the REGISTER records for this stem, never a reconstruction.

    `acquire.py` writes `original` into the row it creates, and it names the
    file for the format the provider actually served — `.jpg`, `.png` or
    `.webp`. Rebuilding that name here from a convention is a second
    implementation of one fact, which this repository has now paid for six
    times; the sixth was a number and this would have been a file extension.
    """
    if not os.path.exists(REGISTER):
        sys.exit("there is no register — run scripts/images/acquire.py first")
    with open(REGISTER, encoding="utf-8") as fh:
        reg = json.load(fh)
    paths = {r["original"] for r in reg.get("images", {}).values()
             if r.get("file") == stem and r.get("original")}
    if not paths:
        sys.exit(f"no register row has file {stem!r} with an original — run "
                 f"scripts/images/acquire.py first")
    if len(paths) > 1:
        sys.exit(f"{stem} is claimed by {len(paths)} different originals: "
                 f"{', '.join(sorted(paths))}. One file, one stem.")
    src = os.path.join(ROOT, paths.pop())
    if not os.path.exists(src):
        sys.exit(f"the register names {os.path.relpath(src, ROOT)} and no "
                 f"such file exists — the acquisition did not finish")
    return src


def _stem(name):
    """ACCEPT A PURPOSE OR A STEM, because a caller has the purpose.

    The workflow and the desk both hand this script the PURPOSE they just
    acquired — `region-hero@austria/tyrol-and-vorarlberg` — and the file on
    disk is named with the slashes folded. Asking every caller to fold them
    itself is asking every caller to know a rule that lives in one place.
    """
    return name.replace("/", "__")


def derive(stem):
    """Build the ladder from the UNTOUCHED original and record what was made.

    THE DIRECTORY IS CREATED HERE, AND NOT DOING SO WOULD HAVE FAILED THE
    FIRST REAL ACQUISITION. `assets/img/` holds only generated derivatives,
    so it is empty and git does not track an empty directory — a fresh clone
    does not have it, and that includes the checkout the `photograph`
    workflow runs on. `acquire.py` has always made `photographs/` for exactly
    this reason and this script never made its own. It survived because every
    local run happened in a tree where an earlier run had already created it:
    a code path nothing exercises is a code path nothing checks, and the only
    thing that found it was running the desk's acquisition in a clean clone.

    THE ORIGINAL IS READ AND NEVER WRITTEN. It is the evidence the whole
    chain is checked against — checks.py re-hashes it on every build — so
    this reads it, writes beside it, and leaves it exactly as the provider
    served it.

    AND ITS PATH IS READ OUT OF THE REGISTER RATHER THAN RECONSTRUCTED.
    This script used to build `photographs/<stem>.original.jpg` from the
    convention, which was true while the only readable format was JPEG and
    became a second implementation of a fact `acquire.py` already recorded
    the moment a PNG could be acquired. The row carries `original`; that is
    the path, and a file named for a format it is not is exactly what this
    directory exists to make impossible.

    AND IT COMPLETES THE PROVENANCE ROW rather than leaving it half-filled.
    acquire.py writes the row with `processing` and `derivatives` set to null,
    which the validator refuses: a photograph that has arrived but has no
    ladder is not publishable, and the state where it LOOKS publishable is the
    one worth making impossible. This fills both, with the hash and the real
    pixel dimensions of every file it wrote, so a later reader can re-check
    any step without trusting this script's word for it.
    """
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is not installed. `pip install pillow` — and for AVIF "
                 "either Pillow 11+ or `pip install pillow-avif-plugin`. It is "
                 "installed by the photograph workflow; it is deliberately not "
                 "a dependency of the build, which stays stdlib-only.")
    import PIL
    stem = _stem(stem)
    src = _original_of(stem)

    with open(src, "rb") as fh:
        original_sha = hashlib.sha256(fh.read()).hexdigest()

    # THE VERSION TAG IS THE ORIGINAL'S OWN HASH, and it is in every
    # derivative's NAME. /assets/ is served `public, max-age=31536000,
    # immutable`, which is a promise about the URL: a browser told that will
    # not revalidate for a year. A ladder at `homepage-hero-1260.jpg` is a
    # stable URL whose contents change the day the photograph is replaced —
    # the stylesheet bug, exactly, in a new place, and the check that exists
    # because of that bug caught this within a minute of the first real
    # acquisition. One tag for the whole set rather than one per file,
    # because the set changes together.
    tag = original_sha[:10]
    made, skipped = {}, []
    with Image.open(src) as im:
        im = im.convert("RGB")
        for w in IMAGE_WIDTHS:
            if w > im.width:
                skipped.append(w)
                continue
            small = im.resize((w, round(im.height * w / im.width)),
                              Image.LANCZOS)
            os.makedirs(IMG_DIR, exist_ok=True)
            for ext in ("avif", "webp", "jpg"):
                name = f"{stem}.{tag}-{w}.{ext}"
                dst = os.path.join(IMG_DIR, name)
                kw = {"quality": QUALITY[ext]}
                if ext == "webp":
                    kw["method"] = 5
                if ext == "jpg":
                    kw["optimize"] = True
                small.save(dst, **kw)
                with open(dst, "rb") as fh:
                    body = fh.read()
                made[name] = {"sha256": hashlib.sha256(body).hexdigest(),
                              "bytes": len(body),
                              "width": small.width, "height": small.height}
        width, height = im.width, im.height

    processing = {
        "tool": f"Pillow {PIL.__version__}",
        "version_tag": tag,
        "source_sha256": original_sha,
        "source_width": width,
        "source_height": height,
        "widths": [w for w in IMAGE_WIDTHS if w <= width],
        "skipped_widths": skipped,
        "formats": ["avif", "webp", "jpg"],
        "quality": dict(QUALITY),
        "resample": "LANCZOS",
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }

    with open(REGISTER, encoding="utf-8") as fh:
        reg = json.load(fh)
    keys = [k for k, r in reg["images"].items() if r.get("file") == stem]
    if not keys:
        sys.exit(f"no register row has file {stem!r}. derive.py completes a "
                 f"row acquire.py wrote; it does not invent one.")
    for k in keys:
        row = reg["images"][k]
        # THE LADDER MUST COME FROM THE FILE THE ROW CLAIMS. If the original
        # on disk is not the one the register recorded, the derivatives are of
        # some other photograph and every hash below would be true about the
        # wrong picture.
        if row.get("sha256") and row["sha256"] != original_sha:
            sys.exit(f"{k}: the original on disk hashes {original_sha[:12]} "
                     f"and the register says {row['sha256'][:12]}. The file "
                     f"has been replaced since it was acquired. Nothing "
                     f"written.")
        row["version"] = tag
        row["processing"] = processing
        row["derivatives"] = made
    with open(REGISTER, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"{stem}: original is {width}x{height}, made {len(made)} derivatives")
    print(f"  provenance completed on {len(keys)} register row(s)")
    if skipped:
        print(f"  no upscaling: {', '.join(str(w) for w in skipped)} skipped. "
              f"A browser choosing between a real width and a fake larger one "
              f"takes the fake one.")
    return made


def main(argv):
    if not argv:
        sys.exit("usage: derive.py <stem> [<stem> ...]   "
                 "(a stem is the register row's `file`)")
    for stem in argv:
        derive(stem)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
