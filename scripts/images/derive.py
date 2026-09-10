#!/usr/bin/env python3
"""Build the widths and formats `picture()` asks for, from one source file.

`render.picture()` emits a <picture> with three formats at five widths:

    /assets/img/<file>-{480,800,1260,1800,2400}.{avif,webp,jpg}

Fifteen files per photograph, and `checks.py` already refuses a page whose
`src` does not resolve — so a register row without its derivatives fails the
build rather than shipping a broken image. That is the right order: the row
is the claim and the files are the evidence.

WHY IT SHELLS OUT. This repository is stdlib-only by design and there is no
image library here — decoding and re-encoding AVIF in pure Python is not a
thing anybody should attempt. ImageMagick is on the GitHub Actions runner and
on most workstations, so this drives it and says plainly what is missing when
it is not there, rather than failing three layers down.

NEVER UPSCALE. A 900-pixel source does not get a 2400-pixel derivative: it
gets the widths it can actually fill, and `picture()`'s srcset is honest about
what exists because the browser picks from what is offered. A file named
-2400 that holds 900 pixels of detail is the same class of untruth as a
population we estimated.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from lib.render import IMAGE_WIDTHS                       # noqa: E402

IMG_DIR = os.path.join(ROOT, "assets", "img")
FORMATS = ("avif", "webp", "jpg")
QUALITY = {"avif": "50", "webp": "78", "jpg": "82"}


def tool():
    for name in ("magick", "convert"):
        if shutil.which(name):
            return name
    sys.exit("ImageMagick is not installed. `sudo apt-get install -y "
             "imagemagick libheif1` on Debian or Ubuntu; it is already on the "
             "GitHub Actions ubuntu runner.")


def source_width(exe, src):
    out = subprocess.run([exe, "identify", "-format", "%w", src]
                         if exe == "magick" else ["identify", "-format", "%w", src],
                         capture_output=True, text=True, check=True)
    return int(out.stdout.strip())


def derive(stem):
    exe = tool()
    src = os.path.join(IMG_DIR, stem + ".src.jpg")
    if not os.path.exists(src):
        sys.exit(f"no source at {os.path.relpath(src, ROOT)} — run "
                 f"scripts/images/fetch.py first")
    have = source_width(exe, src)
    made, skipped = [], []
    for w in IMAGE_WIDTHS:
        if w > have:
            skipped.append(w)
            continue
        for ext in FORMATS:
            dst = os.path.join(IMG_DIR, f"{stem}-{w}.{ext}")
            cmd = ([exe] if exe == "magick" else []) + [
                src, "-resize", f"{w}x", "-strip",
                "-quality", QUALITY[ext], dst,
            ]
            if exe != "magick":
                cmd = ["convert"] + cmd
            subprocess.run(cmd, check=True)
            made.append(os.path.basename(dst))
    print(f"{stem}: source is {have}px, made {len(made)} derivatives")
    if skipped:
        print(f"  no upscaling: {', '.join(str(w) for w in skipped)} skipped, "
              f"because the source cannot fill them")
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
