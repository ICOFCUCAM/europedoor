#!/usr/bin/env python3
"""The Media Desk, against the stub provider. No network, no real photograph.

    python3 tools/desk-tests.py

WHAT THIS OWNS AND WHAT IT DOES NOT. `tools/photo-tests.py` already exercises
the acquisition pipeline end to end — fetch by id, refuse a mismatched id,
keep the original, hash it, never upscale, write provenance, generate the PR
body. The desk RUNS those same scripts, so re-testing them here would be
testing the same code twice and calling it coverage.

What is new is the boundary: a sign-in, a session, what the browser is allowed
to send, what it is allowed to get back, and whether the key can reach it.
That is what this asserts.

AND IT NEVER ACQUIRES. The acquisition route is exercised only for what it
REFUSES — no session, missing fields, an unknown purpose — because a test that
ran it for real would write a register row, build the site and make a git
commit in the repository it is testing. The brief's closing line says the same
thing from the other side: nothing acquires a real photograph until a person
decides to.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

FAILS = []
N = 0


def check(name, ok, detail=""):
    global N
    N += 1
    if not ok:
        FAILS.append(name + (f"\n      {detail}" if detail else ""))


# The stub provider, borrowed whole rather than written again.
sys.path.insert(0, os.path.join(ROOT, "tools"))
import importlib.util                                     # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "phototests", os.path.join(ROOT, "tools", "photo-tests.py"))
PT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PT)

KEY = "stub-key-not-a-secret-0123456789abcdef"
PASSCODE = "desk-test-passcode"


class Desk:
    """The desk as a subprocess, exactly as an editor would run it."""

    def __init__(self, base, port):
        env = dict(os.environ)
        env.update({
            "PEXELS_API_BASE": base,
            "PEXELS_API_KEY": KEY,
            "EUROPEDOOR_DESK_PASSCODE": PASSCODE,
            "EUROPEDOOR_DESK_PORT": str(port),
        })
        self.port = port
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "tools", "desk", "serve.py")],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True)
        self.log = []
        threading.Thread(target=self._drain, daemon=True).start()
        self.cookie = ""
        for _ in range(100):
            try:
                self.get("/api/session")
                return
            except Exception:                             # noqa: BLE001
                time.sleep(0.1)
        raise RuntimeError("the desk did not start\n" + "".join(self.log))

    def _drain(self):
        for line in self.proc.stdout:
            self.log.append(line)

    def _req(self, path, method="GET", body=None, desk_header=True, cookie=None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if desk_header:
            req.add_header("X-Desk", "1")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        ck = self.cookie if cookie is None else cookie
        if ck:
            req.add_header("Cookie", ck)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read(), r.headers
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), exc.headers

    def get(self, path, **kw):
        return self._req(path, **kw)

    def post(self, path, body=None, **kw):
        return self._req(path, "POST", body if body is not None else {}, **kw)

    def signin(self, passcode=PASSCODE):
        code, body, headers = self.post("/api/signin", {"passcode": passcode})
        if code == 200:
            raw = headers.get("Set-Cookie") or ""
            self.cookie = raw.split(";")[0]
        return code, body

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def jbody(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def main():
    srv = PT.serve()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    PT.STUB["jpeg"] = PT._jpeg(2560, 1440)
    PT.STUB["preview"] = PT._jpeg(400, 260)
    PT.STUB["meta"] = {
        "id": int(PT.PHOTO_ID), "width": 2560, "height": 1440,
        "url": "https://www.pexels.com/photo/stub-2014422/",
        "photographer": "Stub Photographer",
        "photographer_url": "https://www.pexels.com/@stub",
        "alt": "a generated test pattern",
        "src": {"original": base + "/original.jpg",
                "large2x": base + "/preview.jpg"},
    }
    desk = Desk(base, 8791)
    try:
        run(desk)
    finally:
        desk.stop()
        srv.shutdown()

    if FAILS:
        print(f"\n{len(FAILS)} desk failure(s) of {N}:")
        for f in FAILS:
            print("  - " + f)
        return 1
    print(f"\nall {N} desk checks passed")
    return 0


def run(desk):
    # ── 1. nothing is reachable before signing in ────────────────────
    for path in ("/api/registry", "/api/search?purpose=homepage-hero&q=x",
                 "/api/thumb?t=anything", "/api/job/x"):
        code, body, _ = desk.get(path)
        check(f"{path.split('?')[0]} refuses without a session", code == 401,
              f"got {code}")
    code, _, _ = desk.post("/api/acquire", {
        "provider": "pexels", "photo_id": PT.PHOTO_ID,
        "purpose": "homepage-hero", "alt": "x"})
    check("acquire refuses without a session", code == 401, f"got {code}")

    # The sign-in page itself is public, or nobody could sign in.
    code, body, _ = desk.get("/")
    check("the sign-in page is served", code == 200 and b"Media Desk" in body)
    check("and it does not leak the passcode",
          PASSCODE.encode() not in body)

    # ── 2. the passcode is the gate ──────────────────────────────────
    code, body = desk.signin("not-the-passcode")
    check("a wrong passcode is refused", code == 401, f"got {code}")
    check("and no session cookie is issued", not desk.cookie)

    t0 = time.time()
    code, body = desk.signin("also-wrong")
    check("a failed sign-in costs time", time.time() - t0 >= 0.3)

    code, body = desk.signin()
    check("the right passcode signs in", code == 200, f"got {code} {body[:200]}")
    check("and issues a session cookie", desk.cookie.startswith("desk="))
    raw = desk._req("/api/signin", "POST", {"passcode": PASSCODE})[2]
    check("the cookie is HttpOnly and SameSite=Strict",
          "HttpOnly" in (raw.get("Set-Cookie") or "")
          and "SameSite=Strict" in (raw.get("Set-Cookie") or ""))

    # ── 3. a cross-site POST cannot act ──────────────────────────────
    # A form on another origin can POST with the cookie attached and cannot
    # set a custom header. SameSite=Strict is the first answer and this is
    # the second, because one control is not a control.
    code, _, _ = desk.post("/api/acquire", {"provider": "pexels",
                                            "photo_id": PT.PHOTO_ID,
                                            "purpose": "homepage-hero",
                                            "alt": "x"}, desk_header=False)
    check("a POST without the desk header is refused", code == 400, f"got {code}")

    # ── 4. the registry comes from the slots ─────────────────────────
    code, body, _ = desk.get("/api/registry")
    reg = jbody(body)
    check("the registry is served", code == 200)
    purposes = reg.get("purposes", [])
    check("it carries every declared purpose and every slot instance",
          len(purposes) > 500, f"{len(purposes)} rows")
    check("and it names the slots", set(reg.get("slots", [])) >= {
        "destination-hero", "place-hero", "story-hero"})
    by_name = {p["purpose"]: p for p in purposes}
    cham = by_name.get("destination-hero@france/alps-and-east/chamonix")
    check("a slot instance resolves to a real surface and page",
          bool(cham) and cham["path"] == "/europe/france/alps-and-east/chamonix",
          str(cham)[:200])
    check("and its requirements come from the SLOT",
          bool(cham) and cham["min_width"] == 1800 and cham["orientation"] == "landscape")
    check("every row carries a status", all(
        p["status"] in ("EMPTY", "PUBLISHED") for p in purposes))
    check("and with an empty register every status is EMPTY", all(
        p["status"] == "EMPTY" for p in purposes))

    # ── 5. searching goes through the desk, never the browser ────────
    code, body, _ = desk.get(
        "/api/search?provider=pexels&purpose=homepage-hero&q=europe")
    res = jbody(body)
    check("a search returns candidates", code == 200 and res.get("candidates"),
          str(res)[:240])
    cand = (res.get("candidates") or [{}])[0]
    check("a candidate carries the provider's ID", cand.get("id") == PT.PHOTO_ID)
    check("and its native size", cand.get("width") == 2560)
    check("and whether it suits the slot", cand.get("suits") is True)
    check("and the sheet names no winner", "order" in res
          and "carrying no judgement" in res["order"])
    check("NO candidate is marked chosen, recommended or scored",
          not any(k in cand for k in ("rank", "score", "recommended", "best",
                                      "pick", "position")))

    # THE KEY IS NOT IN ANYTHING THE BROWSER RECEIVES. Asserted over the
    # whole response rather than over a field, because the failure this
    # guards against is a key arriving somewhere nobody thought to look.
    for path in ("/api/registry",
                 "/api/search?provider=pexels&purpose=homepage-hero&q=europe",
                 "/", "/desk.js", "/desk.css"):
        _, raw, _ = desk.get(path)
        check(f"the key is absent from {path}", KEY.encode() not in raw)
    check("and the key is absent from the desk's own log",
          KEY not in "".join(desk.log))

    # ── 6. the preview is a token, not a URL ─────────────────────────
    check("a candidate carries a thumbnail token and no provider URL",
          bool(cand.get("thumb")) and "preview" not in cand
          and not any(isinstance(v, str) and "://" in v and "pexels.com" not in v
                      for k, v in cand.items() if k != "page"),
          str(cand)[:240])
    code, blob, headers = desk.get("/api/thumb?t=" + cand["thumb"])
    check("the token serves the preview", code == 200 and blob[:2] == b"\xff\xd8",
          f"got {code}, {len(blob)} bytes")
    check("and it is served as an image",
          (headers.get("Content-Type") or "").startswith("image/"))
    code, _, _ = desk.get("/api/thumb?t=not-a-real-token")
    check("an unknown token serves nothing", code == 404, f"got {code}")
    # The route this replaced took a URL. Asserting the old shape is gone is
    # the only way to notice if somebody reintroduces it as a convenience.
    src = open(os.path.join(ROOT, "tools", "desk", "serve.py"), encoding="utf-8").read()
    check("the thumbnail route takes no caller-supplied URL",
          'get("u")' not in src and "urlopen(url" in src)

    # ── 7. a purpose is required and is checked ──────────────────────
    code, body, _ = desk.get("/api/search?purpose=not-a-purpose&q=europe")
    check("an unknown purpose is refused", "error" in jbody(body))
    code, body, _ = desk.get("/api/search?purpose=destination-hero@not/a/place&q=x")
    check("a slot instance with an unknown target is refused",
          "error" in jbody(body))
    for missing in ("provider", "photo_id", "purpose", "alt"):
        b = {"provider": "pexels", "photo_id": PT.PHOTO_ID,
             "purpose": "homepage-hero", "alt": "x"}
        b.pop(missing)
        code, raw, _ = desk.post("/api/acquire", b)
        check(f"acquire refuses without {missing}", code == 400, f"got {code}")

    # ── 8. the desk cannot be told which SEARCH RESULT to take ───────
    # The whole reason `--pick 3` was removed. The acquire route takes an id
    # and there is no index anywhere in the browser half either.
    js = open(os.path.join(ROOT, "tools", "desk", "desk.js"), encoding="utf-8").read()
    check("the browser sends an id and never an index",
          "photo_id: CHOSEN.candidate.id" in js
          and not re.search(r"candidates\[\s*\d", js))
    check("and the acquire route reads photo_id rather than a position",
          '"photo_id"' in src and "search_results" not in src)

    # ── 9. signing out ends the session ──────────────────────────────
    code, _, _ = desk.post("/api/signout")
    check("sign-out is accepted", code == 200)
    code, _, _ = desk.get("/api/registry")
    check("and the session is gone", code == 401, f"got {code}")

    # ── 10. nothing was written ──────────────────────────────────────
    reg_now = json.load(open(os.path.join(ROOT, "data", "images.json"),
                             encoding="utf-8"))["images"]
    check("the register is untouched by this suite", reg_now == {},
          f"{len(reg_now)} rows")
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    check("and the working tree is not dirtied by it",
          "photographs/" not in dirty and "assets/img" not in dirty,
          dirty[:300])


if __name__ == "__main__":
    sys.exit(main())
