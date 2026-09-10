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

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from lib.render import IMAGE_WIDTHS                       # noqa: E402

IMG_DIR = os.path.join(ROOT, "assets", "img")
# Per-format quality, taken from the sister repository's settled values rather
# than guessed here. AVIF carries far more at a lower number than JPEG does.
QUALITY = {"avif": 50, "webp": 78, "jpg": 82}


def derive(stem):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is not installed. `pip install pillow` — and for AVIF "
                 "either Pillow 11+ or `pip install pillow-avif-plugin`. It is "
                 "installed by the photograph workflow; it is deliberately not "
                 "a dependency of the build, which stays stdlib-only.")
    src = os.path.join(IMG_DIR, stem + ".src.jpg")
    if not os.path.exists(src):
        sys.exit(f"no source at {os.path.relpath(src, ROOT)} — run "
                 f"scripts/images/fetch.py first")
    made, skipped = [], []
    with Image.open(src) as im:
        im = im.convert("RGB")
        for w in IMAGE_WIDTHS:
            if w > im.width:
                skipped.append(w)
                continue
            small = im.resize((w, round(im.height * w / im.width)),
                              Image.LANCZOS)
            for ext in ("avif", "webp", "jpg"):
                dst = os.path.join(IMG_DIR, f"{stem}-{w}.{ext}")
                kw = {"quality": QUALITY[ext]}
                if ext == "webp":
                    kw["method"] = 5
                if ext == "jpg":
                    kw["optimize"] = True
                small.save(dst, **kw)
                made.append(os.path.basename(dst))
        width = im.width
    print(f"{stem}: source is {width}px, made {len(made)} derivatives")
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
