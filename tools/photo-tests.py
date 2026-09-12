#!/usr/bin/env python3
"""The photograph pipeline, tested against a stub provider.

    python3 tools/photo-tests.py                  every test
    python3 tools/photo-tests.py --committed-only just the secret scan

WHY A STUB AND NOT THE REAL API. Every property worth testing here is about
what this repository does with a response, not about what Pexels returns: that
an id mismatch stops the run, that a purpose is required, that a half-written
row fails the validator, that the hash can be re-verified. Testing those
against the live API would need a key, would spend the rate limit, and would
make the suite depend on a photograph somebody might delete. The stub serves a
recorded response shape and a real JPEG this file generates, so the tests run
anywhere, including a machine with no network — which is where the build has
to run.

WHAT IT DOES NOT TEST, HONESTLY. It does not prove Pexels' live API behaves
the way the stub does. That is what the archived documentation is for, and the
one thing that closes the gap is the first real acquisition through the
workflow.

Every test asserts a REFUSAL as well as an acceptance where one exists. A test
that only shows the good path passing is a test that would still pass with the
guard deleted.

THIS SUITE IS DESTRUCTIVE AND IS NOT A POST-ACQUISITION GATE. It acquires the
homepage hero against the stub, wipes and rebuilds `site/`, and then restores
the register and deletes what it made. Run beside a live acquisition it
deletes THAT — which is what happened the first time the Media Desk ran it as
a gate in a clean clone: every earlier step succeeded and this one removed the
photograph they had just produced, then the checks failed because the register
named files no longer on disk. CLAUDE.md already records that this file builds
the site; it also owns the register, and that is the sharper half.
"""

from __future__ import annotations

import http.server
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
# ONE CREDENTIAL DECISION, IMPORTED RATHER THAN RESTATED. This file had
# its own copy, and the copies disagreed twice in two runs: run 19 died
# on a URL path segment this one had not learned about, run 20 on a slug
# neither had. `checks.py` owns the rule; a suite that re-implements the
# thing it is testing is testing its own restatement.
from checks import credential_shaped, in_url_path     # noqa: E402
IMG = os.path.join(ROOT, "assets", "img")
IMG_DIR = os.path.join(ROOT, "assets", "img")
REGISTER = os.path.join(ROOT, "data", "images.json")

FAILURES = []
RUN = 0


def check(name, cond, detail=""):
    global RUN
    RUN += 1
    if not cond:
        FAILURES.append(f"{name}{(': ' + detail) if detail else ''}")


# ── a stub provider ───────────────────────────────────────────────────
#
# One photograph, one id, and a real JPEG big enough to pass the homepage
# hero's 2,400px floor. Generated rather than committed so the suite carries
# no binary.

PHOTO_ID = "2014422"
PHOTO2_ID = "3110000"
STUB = {}


def _jpeg(width, height):
    from PIL import Image
    im = Image.new("RGB", (width, height))
    px = im.load()
    for y in range(0, height, 8):
        for x in range(0, width, 8):
            v = (x * 7 + y * 3) % 255
            for dy in range(8):
                for dx in range(8):
                    if x + dx < width and y + dy < height:
                        px[x + dx, y + dy] = (v, (v + 60) % 255, (v + 120) % 255)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return buf.getvalue()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/photos/" + PHOTO_ID):
            return self._json(STUB["meta"])
        if self.path.startswith("/photos/mismatch"):
            # THE CASE THE WHOLE DESIGN EXISTS FOR: a 200 carrying a
            # different photograph than the one asked for.
            body = dict(STUB["meta"])
            body["id"] = 999999
            return self._json(body)
        if self.path.startswith("/photos/undersized"):
            # A 200 DESCRIBING ONE PHOTOGRAPH AND SERVING ANOTHER SIZE.
            # The declared width is what cleared the slot, so bytes that do
            # not match it are a photograph that does not meet the slot
            # wearing a provenance row that says it does. This route keeps
            # the metadata and points `original` at the small file.
            body = dict(STUB["meta"])
            body["id"] = "undersized"
            body["src"] = dict(body["src"])
            body["src"]["original"] = body["src"]["original"].replace(
                "/original.jpg", "/small.jpg")
            return self._json(body)
        if self.path.startswith("/small.jpg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(STUB["small"])))
            self.end_headers()
            self.wfile.write(STUB["small"])
            return
        if self.path.startswith("/notajpeg.bin"):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(STUB["notajpeg"])))
            self.end_headers()
            self.wfile.write(STUB["notajpeg"])
            return
        if self.path.startswith("/photos/notajpeg"):
            body = dict(STUB["meta"])
            body["id"] = "notajpeg"
            body["src"] = dict(body["src"])
            body["src"]["original"] = body["src"]["original"].replace(
                "/original.jpg", "/notajpeg.bin")
            return self._json(body)
        if self.path.startswith("/photos/" + PHOTO2_ID):
            return self._json(STUB["meta2"])
        # EVERY FAMILY NEEDS ITS OWN ID, because one photograph may not fill
        # two surfaces and the register refuses it in both directions.
        want = self.path.split("/photos/")[-1].split("?")[0]
        if want in STUB.get("extra", {}):
            body = dict(STUB["meta2"])
            body["id"] = int(want)
            return self._json(body)
        if self.path.startswith("/original2.jpg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(STUB["jpeg2"])))
            self.end_headers()
            self.wfile.write(STUB["jpeg2"])
            return
        if self.path.startswith("/photos/"):
            self.send_response(404)
            self.end_headers()
            return
        if self.path.startswith("/original.jpg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(STUB["jpeg"])))
            self.end_headers()
            self.wfile.write(STUB["jpeg"])
            return
        if self.path.startswith("/preview.jpg"):
            # DELIBERATELY NOT THE SAME BYTES AS THE ORIGINAL. A preview is
            # for looking at and an original is what gets hashed into the
            # register; a stub that served one file for both would let the
            # two be confused and the suite would never notice.
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(STUB["preview"])))
            self.end_headers()
            self.wfile.write(STUB["preview"])
            return
        if self.path.startswith("/search"):
            return self._json({"photos": [STUB["meta"]]})
        self.send_response(404)
        self.end_headers()

    def _json(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def run(args, env):
    e = dict(os.environ)
    e.update(env)
    return subprocess.run([sys.executable] + args, cwd=ROOT, env=e,
                          capture_output=True, text=True)


def main(argv):
    only_secrets = "--committed-only" in argv

    # ── 1. no credential is committed, anywhere ──────────────────────
    #
    # Runs on its own in the workflow, immediately before the commit, so a
    # key that reached a file cannot be pushed even if every other check
    # somehow passed.
    keyish = re.compile(r"[A-Za-z0-9_-]{40,}")
    archive = os.path.join(ROOT, "docs", "data-licenses", "provider-terms")
    stems = set()
    if os.path.isdir(archive):
        stems = {n.rsplit(".", 1)[0] for n in os.listdir(archive)}
        stems |= {part for n in stems for part in n.split(".")}
    scanned = 0
    for rel in ("data/images.json", "data/image-purposes.json",
                "docs/data-licenses/photo-providers.json",
                "scripts/images/acquire.py", "scripts/images/discover.py",
                "scripts/images/derive.py", "scripts/images/pr_body.py",
                ".github/workflows/photograph.yml"):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        scanned += 1
        body = open(path, encoding="utf-8").read()
        for m in keyish.finditer(body):
            # A SECOND IMPLEMENTATION OF A THING IS A SECOND CHANCE TO MAKE
            # ITS MISTAKE, and this one made it and was fixed alone.
            #
            # `checks.py` and this scan both read the same eight files for
            # credential-shaped tokens, and both had to learn that a Pexels
            # source URL carries the photograph's own title as a path
            # segment: `/photo/a-close-up-of-party-appetizers-served-on-
            # plates-at-a-gathering-39122376/` is a 71-character run of word
            # characters and hyphens. `checks.py` was taught with
            # `in_url_path`, which walks back to the start of the token and
            # asks whether it begins `https://` and whether the match falls
            # before any `?` or `#` — narrow on purpose, because a credential
            # travels as a query parameter and essentially never as a path
            # segment.
            #
            # THIS COPY KEPT A TWELVE-CHARACTER LOOKBEHIND for `://`, which
            # is true of a token straight after the host and false of one
            # after `/photo/`. So the workflow's own pre-commit scan failed
            # run 19 on seven register rows — after the acquisition, after
            # the rebuild, after every gate including the browser suite — on
            # the provenance the whole pipeline exists to record. It is the
            # same predicate now, imported rather than restated.
            if not credential_shaped(body, m, stems):
                continue
            check("no credential in committed files", False,
                  f"{rel} carries a {len(m.group(0))}-character token")
    check("the secret scan actually read the pipeline files", scanned >= 6,
          f"scanned {scanned}")

    # AND IT HAD ONLY EVER READ AN EMPTY REGISTER, WHICH IS WHY IT PASSED.
    #
    # The scan runs over `data/images.json` among eight files, and until run
    # 19 that file held `{"images": {}}` here and in CI. The full suite does
    # acquire — against a stub whose source URL is `http://127.0.0.1:PORT/...`
    # with no title in it — so the one shape that breaks the predicate, a
    # provider URL carrying the photograph's own title as a path segment,
    # was never once put in front of it. A code path nothing exercises is a
    # code path nothing checks, and this is that sentence about a PREDICATE
    # rather than about a renderer.
    #
    # So the rows are synthesised here, from the real thing: seven register
    # rows failed run 19 and every one of them failed on this.
    sample = json.dumps({"images": {"door-food": {
        "source": "https://www.pexels.com/photo/a-close-up-of-party-"
                  "appetizers-served-on-plates-at-a-gathering-39122376/",
        "photographer_url": "https://www.pexels.com/@dave-garcia-1234567",
        "licence_url": "https://www.pexels.com/license/",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b"
                  "7852b855",
    }}}, indent=2)
    slug = [m.group(0) for m in keyish.finditer(sample)
            if credential_shaped(sample, m)]
    check("a real provider URL is not read as a credential",
          not slug,
          "these would stop the commit: " + ", ".join(s[:50] for s in slug))

    # AND A SLUG IS WORDS, WHICH IS WHAT RUN 20 DIED ON.
    #
    # Exactly one identifier in 837 purposes reaches forty characters:
    # `the-city-that-was-rebuilt-from-paintings`, a story slug an editor
    # chose months ago. It appears about twenty times in that story's
    # register row — purpose, file stem, publication path, the original's
    # path, every derivative name — so acquiring that ONE photograph
    # produced twenty identical failures, and the message named none of
    # them because it printed a length and not the token.
    #
    # The rule is that a key is one long unbroken run of mixed-case
    # alphanumerics and a slug is short lower-case words with separators.
    # Asserted on the real slug rather than an invented one, because the
    # thing that broke was a real slug and the next one will be too.
    SLUG = "the-city-that-was-rebuilt-from-paintings"
    row = json.dumps({"images": {"story-hero@" + SLUG: {
        "purpose": "story-hero@" + SLUG,
        "file": "story-hero@" + SLUG,
        "publication_path": "/stories/" + SLUG,
        "original": "photographs/story-hero@" + SLUG + ".jpg",
        "derivatives": {"story-hero@" + SLUG + ".abc12345-2400.avif": 1},
    }}}, indent=2)
    slugs = [m.group(0) for m in keyish.finditer(row)
             if credential_shaped(row, m)]
    check("a long slug is an identifier, not a credential",
          not slugs, "these would stop the commit: " + ", ".join(slugs[:3]))
    check("and the slug this actually failed on is forty characters",
          len(SLUG) == 40, f"it is {len(SLUG)}")

    # AND AN UNDECLARED SLUG IS NOT ONE. The exclusion is a lookup in the
    # registry, not a judgement about shape, so a token that merely LOOKS
    # like one of this product's identifiers is still refused.
    body = '"x": "a-story-slug-that-nobody-ever-declared-here"'
    check("a slug the product does not declare is still refused",
          credential_shaped(body, next(keyish.finditer(body))))

    # A KEY IS STILL A KEY. The slug rule must not become "anything long is
    # fine": a provider key is what this whole scan exists for, so real
    # shapes are put through it and every one has to be refused.
    #
    # THE FOURTH IS THE ONE THAT MATTERS. The first attempt at the slug rule
    # was a SHAPE — "every hyphen-separated part is a short lower-case
    # word" — and `abcdefgh-ijklmnop-qrstuvwx-yzabcdef-ghijklmn` is 44
    # characters of key that satisfies it. That is why the rule is a lookup
    # in `desk/registry.json` instead, and why this case is in the list.
    for shape in (
        "TESTKEYTESTKEYTESTKEYTESTKEYTESTKEYTESTKEY0123456789",
        "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij0123456789",
        "a" * 44,
        "abcdefgh-ijklmnop-qrstuvwx-yzabcdef-ghijklmn",
    ):
        body = '"secret": "' + shape + '"'
        m = next(keyish.finditer(body))
        check("a real key shape is still refused", credential_shaped(body, m),
              f"{shape[:24]}… was waved through")

    # AND THE PREDICATE IS NARROW IN THE DIRECTION THAT MATTERS. A key
    # travels as a query parameter or a fragment and essentially never as a
    # path segment, so exempting everything after `https://` would exempt
    # exactly where one goes. Both directions, because a guard that only
    # says yes is a guard that says nothing.
    for body, at_text, want in (
        ("https://www.pexels.com/photo/a-very-long-title-here-12345/",
         "a-very-long-title-here-12345", True),
        ("https://api.example.com/v1?key=" + "K" * 44, "K" * 44, False),
        ("https://example.com/x#" + "K" * 44, "K" * 44, False),
        ('"' + "K" * 44 + '"', "K" * 44, False),
    ):
        got = in_url_path(body, body.index(at_text))
        check("the URL predicate answers both ways", got == want,
              f"{at_text[:24]}… in {body[:40]}… returned {got}, wanted {want}")
    # The key must never be echoed by the workflow either.
    wf = open(os.path.join(ROOT, ".github", "workflows", "photograph.yml"),
              encoding="utf-8").read()
    check("the workflow never echoes the key",
          "echo" not in wf.split("PEXELS_API_KEY")[-1].split("\n")[0])
    check("the key is passed as env, not on a command line",
          "PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}" in wf
          and "--key ${{ secrets" not in wf)

    if only_secrets:
        return report()

    try:
        import PIL  # noqa: F401
    except ImportError:
        print("Pillow is not installed — the acquisition tests need it.")
        print("  pip install pillow")
        return report()

    srv = serve()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    STUB["jpeg"] = _jpeg(2560, 1440)
    STUB["preview"] = _jpeg(1880, 1058)
    # Large enough to clear the ten-kilobyte floor and the wrong size, which
    # is exactly the case the floor cannot see.
    STUB["small"] = _jpeg(1200, 675)
    # A SECOND PHOTOGRAPH, BECAUSE ONE ID MAY NOT FILL TWO SURFACES. The
    # register refuses that in both directions and this suite asserts both,
    # so exercising a slot instance needs its own id and its own bytes.
    STUB["jpeg2"] = _jpeg(2600, 1300)
    STUB["extra"] = {}
    STUB["notajpeg"] = b"\x89PNG\r\n\x1a\n" + b"\0" * 40000
    STUB["meta"] = {
        "id": int(PHOTO_ID), "width": 2560, "height": 1440,
        "url": "https://www.pexels.com/photo/stub-2014422/",
        "photographer": "Stub Photographer",
        "photographer_url": "https://www.pexels.com/@stub",
        "alt": "a generated test pattern",
        "src": {"original": base + "/original.jpg",
                "large2x": base + "/preview.jpg"},
    }
    STUB["meta2"] = {
        "id": int(PHOTO2_ID), "width": 2600, "height": 1300,
        "url": "https://www.pexels.com/photo/stub-3110000/",
        "photographer": "Second Stub Photographer",
        "photographer_url": "https://www.pexels.com/@stub2",
        "alt": "a second generated test pattern",
        "src": {"original": base + "/original2.jpg",
                "large2x": base + "/preview.jpg"},
    }
    env = {"PEXELS_API_BASE": base, "PEXELS_API_KEY": "stub-key-not-a-secret"}

    reg_backup = open(REGISTER, encoding="utf-8").read()
    # THE SUITE NOW REWRITES THE INVARIANT REGISTER, so it owns putting it
    # back. `docs/invariants.json` is generated exactly like `site/`, and a
    # test that leaves it moved leaves the repository claiming a photograph
    # is licensed after the photograph has been deleted — which is the same
    # class of loss as leaving a stub original on disk.
    INVARIANTS = os.path.join(ROOT, "docs", "invariants.json")
    inv_backup = open(INVARIANTS, encoding="utf-8").read()
    made = []

    def cleanup():
        with open(REGISTER, "w", encoding="utf-8") as fh:
            fh.write(reg_backup)
        with open(INVARIANTS, "w", encoding="utf-8") as fh:
            fh.write(inv_backup)
        for f in made:
            if os.path.exists(f):
                os.remove(f)
        for d in (IMG, os.path.join(ROOT, "photographs")):
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                # `door-mountains` is the second-purpose test's own artefact
                # and is cleaned up here for the same reason as the hero: a
                # suite that writes into the repository owns taking it out.
                # AND A SLOT INSTANCE, whose stem carries an `@`. The list
                # is a prefix match rather than a set of full names because a
                # derivative's name is the stem plus a hash plus a width plus
                # an extension — and a suite that writes into the repository
                # owns taking it out, or the next run of checks.py finds an
                # original with no register row and says so.
                if (f.startswith("homepage-hero") or f.startswith("door-mountains")
                        or "-hero@" in f or f.startswith("country-hero")):
                    os.remove(os.path.join(d, f))
        # AND site/ IS REBUILT, because these tests build it. Restoring the
        # register without rebuilding leaves the shipped homepage carrying an
        # <img> for a stub with no row and five derivatives that are no longer
        # on disk — a state no gate produces and every gate then validates,
        # since checks.py reads site/ as given. It survived one full green run
        # here: the register read empty, the invariants read one <img> tag,
        # and the difference was a build nobody re-ran.
        #
        # This is the "site/ is deleted on every build" rule arriving from the
        # other side: a test that builds owns putting the build back.
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build.py")],
                       cwd=ROOT, capture_output=True)

    try:
        A = ["scripts/images/acquire.py", "--provider", "pexels"]
        A2 = list(A)

        # ── 2. an exact photo id is required ─────────────────────────
        r = run(A + ["--purpose", "homepage-hero", "--alt", "a test pattern image"], env)
        check("acquisition without --photo-id fails", r.returncode != 0)
        check("and says the id is required",
              "photo-id" in (r.stderr + r.stdout))

        # ── 3. a search position cannot select anything ──────────────
        r = run(A + ["--photo-id", PHOTO_ID, "--pick", "3",
                     "--purpose", "homepage-hero",
                     "--alt", "a test pattern image"], env)
        check("--pick is rejected even with everything else present",
              r.returncode != 0 and "unrecognized arguments" in r.stderr,
              r.stderr[-160:])
        src = open(os.path.join(ROOT, "scripts", "images", "acquire.py"),
                   encoding="utf-8").read()
        # The docstring records why --pick was removed, which is the house
        # style; what must not exist is the OPTION and any indexing of a
        # result list.
        code = "\n".join(l for l in src.splitlines()
                          if not l.lstrip().startswith("#"))
        code = code.split('"""', 2)[-1]
        check("acquire.py declares no --pick option",
              '"--pick"' not in code and "'--pick'" not in code)
        check("acquire.py never indexes a result list",
              "found[" not in code and "results[" not in code
              and "photos[" not in code)

        # ── 4. a purpose is required, and must be declared ───────────
        r = run(A + ["--photo-id", PHOTO_ID, "--alt", "a test pattern image"], env)
        check("acquisition without --purpose fails", r.returncode != 0)
        r = run(A + ["--photo-id", PHOTO_ID, "--purpose", "not-a-purpose",
                     "--alt", "a test pattern image"], env)
        # THE PROMISE, NOT THE PHRASE. This asserted the literal words
        # "declared purpose" and went red when slots arrived and the message
        # started naming both the declared purposes and the slot templates —
        # the same class as every other assertion here that pinned a string.
        # What matters is that it refuses AND tells the reader both ways a
        # purpose can exist, so the fix is in the message.
        out = r.stdout + r.stderr
        check("an undeclared purpose fails", r.returncode != 0
              and "homepage-hero" in out and "destination-hero" in out)
        # And a slot instance whose TARGET is not a real entity is refused
        # exactly as an invented purpose name is: a template is not a licence
        # to name anything after the @.
        r = run(A + ["--photo-id", PHOTO_ID,
                     "--purpose", "destination-hero@not/a/place",
                     "--alt", "a test pattern image"], env)
        check("a slot instance with an unknown target fails", r.returncode != 0)

        # ── 5. a returned id that is not the requested id stops ──────
        #
        # ASSERTED AS *UNCHANGED* RATHER THAN *ABSENT*, AND THAT IS NOT A
        # WEAKER CLAIM — it is the only one that stays true. These three read
        # "no file exists" and "nothing is registered", which hold exactly
        # while the register is empty. The first real acquisition puts a
        # homepage hero on disk permanently, so this whole suite would have
        # gone RED FOREVER on the day the product it guards started working.
        # Found by running the desk's acquisition in a clean clone and then
        # running the gates in that clone.
        #
        # What the refusal actually promises is that it wrote NOTHING: the
        # state after is the state before, whatever that state was.
        def snapshot():
            path = os.path.join(ROOT, "photographs", "homepage-hero.original.jpg")
            blob = open(path, "rb").read() if os.path.exists(path) else None
            return (hashlib.sha256(blob).hexdigest() if blob else None,
                    open(REGISTER, encoding="utf-8").read())

        before = snapshot()
        r = run(A + ["--photo-id", "mismatch", "--purpose", "homepage-hero",
                     "--alt", "a test pattern image"], env)
        check("a mismatched returned id fails", r.returncode != 0)
        check("and nothing is written",
              "Nothing written" in (r.stdout + r.stderr))

        # ── the BYTES are verified, not just their length ────────────
        #
        # Everything above checks the metadata and then fetches a URL out of
        # that same payload. The result used to be accepted on one test —
        # more than ten kilobytes — which passes for a truncated transfer,
        # for a re-encode at a different size, and for any large image at
        # all. The DECLARED size is what cleared the slot, so bytes that
        # disagree with it are a photograph that does not meet the slot
        # carrying a provenance row that says it does; the only thing that
        # would ever have noticed is derive.py refusing to upscale, a step
        # later, in another script, with the register already written.
        r = run(A + ["--photo-id", "undersized", "--purpose", "homepage-hero",
                     "--alt", "a test pattern image"], env)
        out = r.stdout + r.stderr
        check("bytes that are not the declared size fail",
              r.returncode != 0 and "1200x675" in out and "Nothing written" in out)
        r = run(A + ["--photo-id", "notajpeg", "--purpose", "homepage-hero",
                     "--alt", "a test pattern image"], env)
        out = r.stdout + r.stderr
        check("bytes that are not a JPEG fail",
              r.returncode != 0 and "not a JPEG" in out)
        check("and the original on disk is exactly what it was",
              snapshot()[0] == before[0])
        check("and the register is exactly what it was",
              snapshot()[1] == before[1])

        # ── 6. an id that does not exist stops, with no substitute ───
        before = snapshot()
        r = run(A + ["--photo-id", "404404", "--purpose", "homepage-hero",
                     "--alt", "a test pattern image"], env)
        check("a missing id fails rather than substituting", r.returncode != 0)
        check("and no photograph was registered by it", snapshot() == before)

        # ── 7. Unsplash cannot enter the automated path ──────────────
        r = run(["scripts/images/acquire.py", "--provider", "unsplash",
                 "--photo-id", "abc", "--purpose", "homepage-hero",
                 "--alt", "a test pattern image"],
                {"UNSPLASH_ACCESS_KEY": "stub"})
        check("unsplash is refused for automated acquisition", r.returncode != 0)
        check("and the refusal cites the gate",
              "REFUSED" in (r.stdout + r.stderr)
              and "hotlinked" in (r.stdout + r.stderr))

        # ── 8. the happy path, end to end ────────────────────────────
        r = run(A + ["--photo-id", PHOTO_ID, "--purpose", "homepage-hero",
                     "--alt", "a generated test pattern, not a photograph"], env)
        check("an approved id acquires", r.returncode == 0,
              (r.stderr or r.stdout)[-300:])
        original = os.path.join(ROOT, "photographs", "homepage-hero.original.jpg")
        made.append(original)
        check("the original is kept", os.path.exists(original))

        reg = json.load(open(REGISTER, encoding="utf-8"))["images"]
        row = reg.get("home-hero", {})
        check("the register records the provider photo id",
              row.get("provider_photo_id") == PHOTO_ID)
        check("and an acquisition timestamp, not just a date",
              re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
                       str(row.get("acquired_at", ""))))
        check("and the terms evidence it was taken under",
              isinstance(row.get("terms_evidence"), list)
              and row["terms_evidence"])

        # ── 9. the row is INCOMPLETE until the ladder is built ───────
        check("processing is empty before derive", row.get("processing") is None)
        v = run(["tools/build.py", "check"], {})
        check("a half-registered photograph FAILS the validator",
              v.returncode != 0, "it passed, which is the dangerous state")
        check("and the validator says what is missing",
              "derivatives" in (v.stdout + v.stderr))

        # ── 10. the ladder completes it ──────────────────────────────
        # THE DIRECTORY MUST NOT HAVE TO EXIST. `assets/img/` holds only
        # generated files, so git does not track it and a fresh clone — the
        # workflow's own checkout included — does not have it. Removing it
        # here is the only way this is tested, because every local run after
        # the first happens in a tree where an earlier run made it.
        if os.path.isdir(IMG_DIR) and not os.listdir(IMG_DIR):
            os.rmdir(IMG_DIR)
        d = run(["scripts/images/derive.py", "homepage-hero"], {})
        check("derive works in a tree with no assets/img",
              d.returncode == 0 and os.path.isdir(IMG_DIR),
              (d.stdout + d.stderr)[-400:])
        check("derive builds the ladder", d.returncode == 0,
              (d.stderr or d.stdout)[-300:])
        reg = json.load(open(REGISTER, encoding="utf-8"))["images"]
        row = reg["home-hero"]
        check("derivative hashes are recorded",
              all(re.match(r"^[0-9a-f]{64}$", x["sha256"])
                  for x in row["derivatives"].values()))
        check("derivative dimensions are recorded",
              all(x["width"] > 0 and x["height"] > 0
                  for x in row["derivatives"].values()))
        check("processing records the encoder and the quality",
              row["processing"].get("tool")
              and row["processing"].get("quality"))
        v = run(["tools/build.py", "check"], {})
        check("the completed row validates", v.returncode == 0,
              (v.stdout + v.stderr)[-300:])
        # BUILD BEFORE ASSERTING PUBLICATION. The publication check reads the
        # SHIPPED html, which is the only place the question "is it on the
        # page" can be answered — so the pages have to exist first. Asserting
        # it against a stale site/ tests the previous build.
        b = run(["tools/build.py"], {})
        check("the site builds with a photograph in it", b.returncode == 0,
              (b.stderr or "")[-200:])

        # ── A SLOT INSTANCE, END TO END, ON A REAL PAGE ──────────────
        #
        # A CODE PATH NOTHING EXERCISES IS A CODE PATH NOTHING CHECKS, and
        # this suite has now been caught by that rule twice: the focal point
        # shipped as a `style="` attribute the CSP forbids, and two CSS rules
        # for the photograph were dead the whole time. Both survived because
        # the register was empty.
        #
        # The country band is the newest container and it renders NOTHING
        # with no photograph, by design — so with an empty register it is
        # exactly as unexercised as those were. This acquires one for a real
        # country, derives it, rebuilds, and asserts the band is on that
        # page and on no other.
        r = run(A2 + ["--photo-id", PHOTO2_ID, "--purpose", "country-hero@austria",
                      "--alt", "a test pattern standing in for a country"], env)
        check("a slot instance acquires", r.returncode == 0,
              (r.stdout + r.stderr)[-400:])
        d2 = run(["scripts/images/derive.py", "country-hero@austria"], {})
        check("a slot instance derives", d2.returncode == 0,
              (d2.stdout + d2.stderr)[-400:])
        b2 = run(["tools/build.py"], {})
        check("the site builds with a country band in it", b2.returncode == 0,
              (b2.stderr or "")[-200:])
        at = os.path.join(ROOT, "site", "europe", "austria", "index.html")
        austria = open(at, encoding="utf-8").read() if os.path.exists(at) else ""
        check("the band renders on the country it was acquired for",
              "pageband" in austria)
        # AND THE PORTRAIT IS STILL THERE. The band is an addition, not a
        # replacement: the country plate is this family's signature moment
        # and it is what says which country the page is about.
        check("and the country portrait is still on the page",
              "countrymap" in austria)
        # A photograph is a photograph and not a plate, on the page and in
        # the markup: `picture()` returns a generated plate when the register
        # has no row, and the band asks the register directly for exactly
        # that reason.
        check("the band carries a photograph rather than a plate",
              "<picture" in austria and "pageband" in austria)
        # ── AND EVERY OTHER FAMILY THAT OPENS ON ONE ──────────────────
        #
        # Six page families grew a container in one commit and five of them
        # would otherwise have been exactly as unexercised as the country
        # band was: `pageband()` renders nothing with an empty register, so
        # an empty register tests none of them. Each is acquired against the
        # stub, derived, and asserted ON ITS OWN PAGE — which is the only
        # place the question can be answered, because a band computed into a
        # variable and never interpolated into the body is invisible to every
        # count. This suite has already been paid for by that exact fault
        # twice: a `style="` attribute the CSP forbids, and two dead CSS
        # rules, both surviving because the register was empty.
        FAMILIES = [
            ("region-hero@austria/tyrol",
             os.path.join("site", "europe", "austria", "tyrol")),
            ("journey-hero@arctic-to-the-baltic",
             os.path.join("site", "journeys", "arctic-to-the-baltic")),
            ("interest-hero@architecture",
             os.path.join("site", "interests", "architecture")),
            ("macro-hero@nordic", os.path.join("site", "discover", "nordic")),
            ("theme-hero@medieval-europe",
             os.path.join("site", "themes", "medieval-europe")),
            ("category-hero@nature",
             os.path.join("site", "experiences", "nature")),
        ]
        for i, (purpose, where) in enumerate(FAMILIES):
            pid = str(4000000 + i)
            STUB["extra"][pid] = purpose
            r = run(A + ["--photo-id", pid, "--purpose", purpose,
                         "--alt", f"a test pattern for {purpose}"], env)
            check(f"{purpose.split('@')[0]} acquires", r.returncode == 0,
                  (r.stdout + r.stderr)[-300:])
            dz = run(["scripts/images/derive.py", purpose], {})
            check(f"{purpose.split('@')[0]} derives", dz.returncode == 0,
                  (dz.stdout + dz.stderr)[-300:])
        b3 = run(["tools/build.py"], {})
        check("the site builds with every family's band in it",
              b3.returncode == 0, (b3.stderr or "")[-300:])
        for purpose, where in FAMILIES:
            f = os.path.join(ROOT, where, "index.html")
            html = open(f, encoding="utf-8").read() if os.path.exists(f) else ""
            check(f"{purpose.split('@')[0]} renders its band on its own page",
                  "pageband" in html and "<picture" in html,
                  f"{where}: {'no file' if not html else 'no band'}")

        # ── THE ORDER THE WORKFLOW HAS TO RUN THESE IN ──────────────
        #
        # `tools/checks.py` RUNS THE INVARIANT REGISTER AS ONE OF ITS OWN
        # CHECKS. So a workflow that rewrites the register AFTER its gate step
        # never reaches the rewrite: the run dies inside checks.py on the very
        # row the rewrite exists to move. That is the ordering mistake this
        # repository already recorded once, in the local desk, in exactly
        # those words — "the fix was in the right place and the wrong order" —
        # and it was made again in the workflow, where it cost a real
        # acquisition that had already fetched, hashed, derived and
        # registered eight photographs.
        #
        # The sequence is BUILD, then rewrite, then gate. Asserted here in
        # that order, with the middle step's necessity proved rather than
        # assumed: before the rewrite the register must FAIL, because a
        # photograph landing is exactly what `safety.img_tags` is recorded to
        # notice.
        iv = run(["tools/invariants.py", "--check"], {})
        check("the invariant register refuses until it is rewritten",
              iv.returncode != 0,
              "a photograph landed and no invariant moved — the register has "
              "stopped noticing")
        ck = run(["tools/checks.py"], {})
        check("and checks.py fails too, because it runs the register",
              ck.returncode != 0,
              "checks.py passed with a register that invariants.py refuses, "
              "so the two disagree about the same rows")
        w = run(["tools/invariants.py", "--write"], {})
        check("the register rewrites", w.returncode == 0,
              (w.stdout + w.stderr)[-300:])
        iv2 = run(["tools/invariants.py", "--check"], {})
        check("and then holds", iv2.returncode == 0,
              (iv2.stdout + iv2.stderr)[-300:])
        ck2 = run(["tools/checks.py"], {})
        check("and checks.py passes with a photograph in the register",
              ck2.returncode == 0, (ck2.stdout + ck2.stderr)[-600:])

        # AND THE AUDITS, which is where the next two failures came from.
        # §39 "Image management" and §83 "Visual direction" both asserted
        # `<img` appears on NO page and called that the rule — so both went
        # red on the first acquisition, on the one page that had a
        # photograph. The tenth and eleventh assertion here to pin a SHAPE
        # rather than a CLAIM, and the same failure as `c_hero_frame`
        # asserting a drawn hero's viewBox after a photograph replaced the
        # drawing. The rule was never absence: no image without a
        # photographer, a source and a licence.
        sa = run(["tools/section-audit.py", "--check"], {})
        check("the section audit passes with a photograph in the register",
              sa.returncode == 0, (sa.stdout + sa.stderr)[-600:])
        ua = run(["tools/ux-audit.py", "--check"], {})
        check("and the UX audit does too",
              ua.returncode == 0, (ua.stdout + ua.stderr)[-400:])

        # ── the credit, measured on the element rather than on a selector ──
        # A RULE THAT CHANGES TWO PROPERTIES OF A SIX-PROPERTY COMPONENT IS
        # NOT A DIFFERENT DESIGN, IT IS A BROKEN ONE. `.pageband figcaption`
        # set `margin-top` and `color` to say "the credit belongs under the
        # picture and never over it". `.credit` is `position: absolute` at the
        # foot of the picture on a near-black scrim at `opacity: 0`, and
        # (0,1,1) beats (0,1,0) — so the colour was overridden and the
        # position, the scrim and the opacity were not. The site's caption
        # ink, a dark grey for a light page, landed on 55% black at 2.01:1,
        # on the two links Pexels' terms require, on every family that opens
        # on a photograph. `margin-top` on an absolutely positioned element
        # does nothing, so the rule achieved exactly one thing and that thing
        # was the defect.
        #
        # IT IS ASSERTED ON THE ELEMENT AND NOT ON THE SELECTOR, because the
        # first attempt was a CSS rule in checks.py — "no figcaption selector
        # carries a colour" — and it refused seven MAP captions, which are
        # real captions under real drawings. The question is which rules can
        # reach a `<figcaption class="credit">`, and that needs a credit to
        # exist, which is exactly what this suite has just made.
        credited = []
        for root, _dirs, files in os.walk(os.path.join(ROOT, "site")):
            for fn in files:
                if not fn.endswith(".html"):
                    continue
                h = open(os.path.join(root, fn), encoding="utf-8").read()
                if 'class="credit"' in h:
                    credited.append((os.path.join(root, fn), h))
        check("a photograph publishes a credit a rule can be tested against",
              bool(credited), f"{len(credited)} pages carry one")

        css_path = os.path.join(ROOT, "assets", "css", "europedoor.css")
        css_src = re.sub(r"/\*.*?\*/", "", open(css_path, encoding="utf-8").read(),
                         flags=re.S)
        # Every ancestor class actually standing over a credit in the shipped
        # markup, read from the markup rather than from a list here — a list
        # is wrong the first time a family starts opening on a photograph.
        over = set()
        for _f, h in credited:
            for chunk in h.split('class="credit"'):
                for cls in re.findall(r'class="([^"]*)"', chunk[-4000:]):
                    over.update(cls.split())
        over.discard("credit")

        offenders = []
        for sel, block in re.findall(r"([^{}@]+)\{([^}]*)\}", css_src):
            sel = sel.strip().split("\n")[-1].strip()
            if "figcaption" not in sel or ".credit" in sel:
                continue
            if not re.search(r"(^|;|\s)color\s*:", block):
                continue
            scope = re.findall(r"\.([A-Za-z0-9_-]+)", sel)
            if scope and all(c in over for c in scope):
                offenders.append(sel)
        check("and no rule recolours it from outside the component",
              not offenders,
              "these reach a credit and give it a colour of their own: "
              + ", ".join(sorted(offenders)))

        bt = os.path.join(ROOT, "site", "europe", "belgium", "index.html")
        belgium = open(bt, encoding="utf-8").read() if os.path.exists(bt) else ""
        check("and no band at all on a country with no photograph",
              bool(belgium) and "pageband" not in belgium)
        v2 = run(["tools/build.py", "check"], {})
        check("the dataset still validates with a slot instance registered",
              v2.returncode == 0, (v2.stdout + v2.stderr)[-300:])

        # ── 11. the hash can be re-verified, and a swap is caught ────
        # SCOPED TO THE PHOTOGRAPH CHECKS. Running the whole suite here would
        # also assert `safety.img_tags` is zero and the homepage is under its
        # weight ceiling — both of which MOVE when a photograph lands, on
        # purpose, because that movement is the deliberate signal that
        # licensed imagery arrived. A test that demanded they not move would
        # be asserting the pipeline never works.
        photo_checks = ("python3 -c 'import sys;sys.path.insert(0,\"tools\");"
                        "import checks;"
                        "[fn() for n,fn in checks.CHECKS if \"photograph\" in n "
                        "or \"hashes to what was recorded\" in n];"
                        "print(checks.FAILURES);"
                        "sys.exit(1 if checks.FAILURES else 0)'")
        c = subprocess.run(photo_checks, shell=True, cwd=ROOT,
                           capture_output=True, text=True)
        check("the photograph checks pass with it registered", c.returncode == 0,
              (c.stdout + c.stderr)[-300:])

        # ── ONE PHOTOGRAPH IS NOT AUTOMATICALLY MEANT FOR TWO SURFACES ──
        #
        # The register already refused a SURFACE being taken over by a
        # different id. The same question from the other end had no answer:
        # the same provider id could be acquired again for a second purpose
        # and nothing anywhere would say so. Twice is sometimes right and is
        # never an accident, so it is a refusal with an explicit escape.
        r = run(["scripts/images/acquire.py", "--provider", "pexels",
                 "--photo-id", PHOTO_ID, "--purpose", "door-mountains",
                 "--alt", "the same test pattern, a second time"], env)
        check("the same id for a second purpose is refused", r.returncode != 0,
              (r.stdout + r.stderr)[-300:])
        check("and the refusal names where it is already used",
              "homepage-hero" in (r.stdout + r.stderr))
        check("and nothing was written for the second purpose",
              "door-mountains" not in
              open(REGISTER, encoding="utf-8").read())
        r = run(["scripts/images/acquire.py", "--provider", "pexels",
                 "--photo-id", PHOTO_ID, "--purpose", "door-mountains",
                 "--alt", "the same test pattern, a second time",
                 "--second-purpose"], env)
        check("and --second-purpose lets it through", r.returncode == 0,
              (r.stdout + r.stderr)[-400:])
        reg2 = json.load(open(REGISTER, encoding="utf-8"))["images"]
        check("both surfaces now name the same photograph",
              str(reg2.get("door-mountains", {}).get("provider_photo_id")) == PHOTO_ID
              and str(reg2.get("home-hero", {}).get("provider_photo_id")) == PHOTO_ID)
        # A CRASH HERE HID EVERY FAILURE THE RUN HAD ALREADY COLLECTED.
        # `check()` gathers and the summary prints at the end, so a KeyError
        # in the cleanup after a failed acquisition threw away the one line
        # that said what went wrong. Same rule as the render suite: a red run
        # that cannot say why is worse than a red one that can.
        reg2.pop("door-mountains", None)
        with open(REGISTER, "w", encoding="utf-8") as fh:
            json.dump({"$comment": json.load(open(REGISTER + ".none", encoding="utf-8"))
                       ["$comment"] if False else
                       json.loads(reg_backup)["$comment"], "images": reg2}, fh, indent=2)
        with open(original, "ab") as fh:
            fh.write(b"tampered")
        c = subprocess.run(photo_checks, shell=True, cwd=ROOT,
                           capture_output=True, text=True)
        check("a replaced original is caught by re-hashing", c.returncode != 0)
        check("and the failure names the drift",
              "is not the file that was acquired" in (c.stdout + c.stderr))
        with open(original, "rb") as fh:
            body = fh.read()[:-len(b"tampered")]
        with open(original, "wb") as fh:
            fh.write(body)

        # ── 12. a missing licence evidence row fails ─────────────────
        reg_now = json.load(open(REGISTER, encoding="utf-8"))
        reg_now["images"]["home-hero"]["terms_evidence"] = []
        with open(REGISTER, "w", encoding="utf-8") as fh:
            json.dump(reg_now, fh, ensure_ascii=False, indent=2); fh.write("\n")
        v = run(["tools/build.py", "check"], {})
        check("a row with no licence evidence fails", v.returncode != 0)

        # ── 13. a missing sha256 fails ───────────────────────────────
        reg_now = json.load(open(REGISTER, encoding="utf-8"))
        reg_now["images"]["home-hero"]["terms_evidence"] = row["terms_evidence"]
        reg_now["images"]["home-hero"]["sha256"] = ""
        with open(REGISTER, "w", encoding="utf-8") as fh:
            json.dump(reg_now, fh, ensure_ascii=False, indent=2); fh.write("\n")
        v = run(["tools/build.py", "check"], {})
        check("a row with no sha256 fails", v.returncode != 0)

        # ── 14. the PR body is generated from the register ───────────
        with open(REGISTER, "w", encoding="utf-8") as fh:
            json.dump(reg, fh, ensure_ascii=False, indent=2) if False else None
        reg_now["images"]["home-hero"]["sha256"] = row["sha256"]
        with open(REGISTER, "w", encoding="utf-8") as fh:
            json.dump(reg_now, fh, ensure_ascii=False, indent=2); fh.write("\n")
        b = run(["scripts/images/pr_body.py", "--purpose", "homepage-hero"], {})
        check("the PR body is generated", b.returncode == 0,
              (b.stderr or "")[-200:])
        for want in (PHOTO_ID, row["sha256"], "Stub Photographer",
                     "Photography acquisition", "generic stock"):
            check(f"the PR body carries {want[:24]!r}", want in b.stdout)
        check("the PR body carries no key",
              "stub-key-not-a-secret" not in b.stdout)
        b2 = run(["scripts/images/pr_body.py", "--purpose", "chamonix-destination"], {})
        check("a PR body for a purpose nothing filled fails", b2.returncode != 0)

        # ── 15. discovery writes a manifest, and it ranks nothing ────
        #
        # THE STEP BETWEEN DISCOVERY AND ACQUISITION IS A PERSON LOOKING, and
        # the sheet is what they look at. Everything asserted here is about
        # the sheet refusing to make the choice: no winner, no score, no sort,
        # and an order that says on its face whose order it is.
        manifest = os.path.join(tempfile.gettempdir(), "ed-cands.json")
        made.append(manifest)
        dsc = run(["scripts/images/discover.py", "--provider", "pexels",
                   "--purpose", "homepage-hero", "--query", "stub",
                   "--manifest", manifest], env)
        check("discovery writes a manifest", dsc.returncode == 0 and
              os.path.exists(manifest), (dsc.stderr or "")[-200:])
        man = json.load(open(manifest, encoding="utf-8"))
        check("the manifest carries the query and the purpose",
              man.get("query") == "stub" and man.get("purpose") == "homepage-hero")
        check("the manifest says the order is the provider's",
              "NOT A RANKING" in man.get("$comment", "").upper())
        # THE FIRST VERSION OF THIS READ ITS OWN PROSE. It searched the whole
        # document for "recommend" and the $comment says "nothing here is
        # chosen, recommended or scored" — so the note explaining that there
        # is no ranking was itself read as one. Same class as the invariant
        # register counting a font size that existed only in a comment about
        # not adding font sizes: an instrument that cannot tell code from the
        # documentation of code. The DATA is what must carry no winner.
        body = json.dumps({k: v for k, v in man.items() if k != "$comment"}).lower()
        check("the manifest names no winner",
              not any(k in body for k in
                      ("recommend", '"best"', '"score"', '"rank"', '"chosen"')))
        check("a candidate carries a preview distinct from the original",
              man["candidates"][0]["preview"].endswith("/preview.jpg"))
        check("discovery downloads nothing — the sheet has not been drawn yet",
              not os.path.exists(os.path.join(tempfile.gettempdir(), "ed-sheet")))

        # ── 16. the sheet draws the REAL hero, and only the ladder differs ─
        scratch = os.path.join(tempfile.gettempdir(), "ed-sheet")
        cs = ["scripts/images/contact_sheet.py", "--manifest", manifest,
              "--out", scratch]
        r = run(cs, env)
        check("the sheet is drawn", r.returncode == 0, (r.stderr or "")[-300:])
        page = os.path.join(scratch, f"cand-{PHOTO_ID}", "index.html")
        check("a candidate page exists", os.path.exists(page))
        drawn = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
        check("the candidate page is the real hero",
              'class="herofull shot"' in drawn)
        check("the drawing is replaced, not stacked behind the photograph",
              "heroeurope" not in drawn)
        check("the delivery ladder is gone", "image/avif" not in drawn)
        check("the preview is what renders",
              f'src="/previews/candidate-{PHOTO_ID}.jpg"' in drawn)
        check("the credit the provider requires is still on it",
              "Photo by" in drawn and "Stub Photographer" in drawn)
        check("the focal anchor survived the substitution",
              'class="photo f-cc"' in drawn)
        check("the preview was fetched",
              os.path.exists(os.path.join(scratch, "previews",
                                          f"candidate-{PHOTO_ID}.jpg")))
        # A SUITE THAT RAISES REPORTS NOTHING. When the sheet fails to draw,
        # the twelve assertions after it must each fail and be counted, not
        # be replaced by a traceback — the same reason the browser suite has
        # a floor on its own count.
        sjp = os.path.join(scratch, "sheet.json")
        sj = json.load(open(sjp, encoding="utf-8")) if os.path.exists(sjp) else {}
        check("the sheet states whose order it is",
              "PROVIDER'S SEARCH ORDER" in sj.get("$comment", "").upper())
        sbody = json.dumps({k: v for k, v in sj.items() if k != "$comment"}).lower()
        check("the sheet carries no score or ranking field",
              not any(k in sbody for k in
                      ('"score"', '"rank"', '"best"', "recommend", '"chosen"')))

        # NOTHING IT WROTE TOUCHED THE REPOSITORY. A preview is somebody
        # else's photograph with no register row and no hash, and the one
        # thing that must never happen is one of them arriving in assets/ or
        # in the register by way of a review.
        check("the sheet wrote nothing into the register",
              json.load(open(REGISTER, encoding="utf-8"))["images"] == {}
              or "candidate-" not in open(REGISTER, encoding="utf-8").read())
        check("the sheet wrote nothing into assets/img",
              not any(n.startswith("candidate-")
                      for n in (os.listdir(IMG) if os.path.isdir(IMG) else [])))
        check("the sheet wrote nothing into site/",
              not os.path.exists(os.path.join(ROOT, "site", "previews")))
        check("the scratch directory is ignored by git",
              subprocess.run(["git", "check-ignore", "-q", ".cache/contact/x.jpg"],
                             cwd=ROOT).returncode == 0)

        # ── 17. a candidate acquire.py would refuse is not art-directed ───
        narrow = dict(man)
        narrow["candidates"] = [dict(man["candidates"][0], width=900, height=506)]
        small = os.path.join(tempfile.gettempdir(), "ed-cands-small.json")
        made.append(small)
        with open(small, "w", encoding="utf-8") as fh:
            json.dump(narrow, fh)
        r2 = run(["scripts/images/contact_sheet.py", "--manifest", small,
                  "--out", scratch + "-2"], env)
        check("a sheet of unacquirable candidates refuses to draw",
              r2.returncode != 0 and "refuse" in (r2.stdout + r2.stderr).lower())

        # ── 18. a purpose with no renderer is refused rather than faked ───
        wrong = dict(man, purpose="destination-hero@france/alps-and-east/chamonix")
        wf3 = os.path.join(tempfile.gettempdir(), "ed-cands-wrong.json")
        made.append(wf3)
        with open(wf3, "w", encoding="utf-8") as fh:
            json.dump(wrong, fh)
        r3 = run(["scripts/images/contact_sheet.py", "--manifest", wf3,
                  "--out", scratch + "-3"], env)
        check("a purpose with no renderer is refused", r3.returncode != 0 and
              "renderer" in (r3.stdout + r3.stderr))

        shutil.rmtree(scratch, ignore_errors=True)
        shutil.rmtree(scratch + "-2", ignore_errors=True)
        shutil.rmtree(scratch + "-3", ignore_errors=True)

        # ── 19. the workflow opens a PR and offers only cleared providers ─
        check("the workflow creates a pull request", "gh pr create" in wf)
        check("the workflow has both stages",
              "stage == 'discover'" in wf and "stage == 'acquire'" in wf)
        check("discovery produces the contact sheet",
              "contact_sheet.py" in wf and "hero-sheet.js" in wf)
        check("the sheet leaves the run as an artifact rather than a commit",
              "upload-artifact" in wf)
        check("the acquisition shows the acquired photograph on the real page",
              "--acquired" in wf or "hero-shot" in wf)
        check("the workflow offers only pexels",
              re.search(r"options: \[pexels\]", wf) is not None)
        check("the workflow runs the gates before opening the PR",
              wf.index("tools/checks.py") < wf.index("gh pr create"))
    finally:
        cleanup()

    return report()


def report():
    if FAILURES:
        print(f"{len(FAILURES)} photograph-pipeline failure(s) of {RUN}:")
        for f in FAILURES:
            print("  - " + f)
        return 1
    print(f"all {RUN} photograph-pipeline checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
