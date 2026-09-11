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
"""

from __future__ import annotations

import http.server
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
IMG = os.path.join(ROOT, "assets", "img")
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
            if "://" in body[max(0, m.start() - 12):m.start()]:
                continue
            if m.group(0) in stems:
                continue
            # A 64-CHARACTER LOWERCASE HEX STRING IS A SHA-256, and the
            # register is FULL of them: the original's hash and one per
            # derivative. The scan would have failed the build on the first
            # real photograph — on the provenance the whole pipeline exists to
            # record. Matched by shape AND by the key it sits under, because
            # "it looks like hex" alone is how a real credential gets waved
            # through.
            if re.fullmatch(r"[0-9a-f]{64}", m.group(0)):
                before = body[max(0, m.start() - 40):m.start()]
                if "sha256" in before or "hash" in before:
                    continue
            check("no credential in committed files", False,
                  f"{rel} carries a {len(m.group(0))}-character token")
    check("the secret scan actually read the pipeline files", scanned >= 6,
          f"scanned {scanned}")
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
    STUB["meta"] = {
        "id": int(PHOTO_ID), "width": 2560, "height": 1440,
        "url": "https://www.pexels.com/photo/stub-2014422/",
        "photographer": "Stub Photographer",
        "photographer_url": "https://www.pexels.com/@stub",
        "alt": "a generated test pattern",
        "src": {"original": base + "/original.jpg",
                "large2x": base + "/preview.jpg"},
    }
    env = {"PEXELS_API_BASE": base, "PEXELS_API_KEY": "stub-key-not-a-secret"}

    reg_backup = open(REGISTER, encoding="utf-8").read()
    made = []

    def cleanup():
        with open(REGISTER, "w", encoding="utf-8") as fh:
            fh.write(reg_backup)
        for f in made:
            if os.path.exists(f):
                os.remove(f)
        for d in (IMG, os.path.join(ROOT, "photographs")):
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if f.startswith("homepage-hero"):
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
        r = run(A + ["--photo-id", "mismatch", "--purpose", "homepage-hero",
                     "--alt", "a test pattern image"], env)
        check("a mismatched returned id fails", r.returncode != 0)
        check("and nothing is written",
              "Nothing written" in (r.stdout + r.stderr))
        check("and no file appeared",
              not os.path.exists(os.path.join(ROOT, "photographs", "homepage-hero.original.jpg")))

        # ── 6. an id that does not exist stops, with no substitute ───
        r = run(A + ["--photo-id", "404404", "--purpose", "homepage-hero",
                     "--alt", "a test pattern image"], env)
        check("a missing id fails rather than substituting", r.returncode != 0)
        check("and no photograph was registered",
              "homepage-hero" not in json.load(open(REGISTER, encoding="utf-8"))
              .get("images", {}).get("home-hero", {}).get("purpose", ""))

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
        d = run(["scripts/images/derive.py", "homepage-hero"], {})
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
