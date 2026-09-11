#!/usr/bin/env python3
"""The EuropeDoor Media Desk — sign in, browse candidates, save into git.

    python3 tools/desk/serve.py
    → open http://127.0.0.1:8765 and sign in with the passcode it prints

WHY THIS IS A LOCAL PROCESS AND NOT A PAGE ON europedoor.com.

The desk needs a trusted server-side half, because the provider key may never
reach a browser: the browser sends a provider, a photo id, a purpose and a
target, and nothing else ever comes back the other way. That half could live
as a function beside the site — and it would put a credential-holding,
authenticated service on the production origin of a product whose whole
security posture is `default-src 'none'`, no server, no session and no
database. This is the same screens, served by a process the editor runs, with
the key in their own environment. Nothing is added to europedoor.com, the CSP
does not move, and the only thing that ever leaves this machine is a git push
the editor asks for.

WHAT IT DOES NOT DO, and each is deliberate:

  * it does not search Pexels itself. `discover.cached_search` does, and the
    desk calls it — one search implementation, one cache, one rate limit.
  * it does not download a photograph itself. `acquire.py` does, by id, and
    asserts the returned id is the requested id before a byte is written.
  * it does not write a register row, build a derivative or compose a PR
    body. Three scripts already do, and a second implementation of any of
    them is a second chance to make its mistake — which this repository has
    now recorded four times.
  * it does not push and it does not open a pull request on its own. It
    commits to a branch and tells you the name. Sending work outward is a
    decision a person makes, not a side effect of clicking Acquire.

THE SIGN-IN IS ONE PASSCODE AND THERE IS NO USER STORE. A desk on 127.0.0.1
is reachable by anything else running as this user, which is the threat that
is actually here; inventing accounts, roles and password hashes for a
single-operator tool would be security theatre with a migration attached.
`EUROPEDOOR_DESK_PASSCODE` if it is set, otherwise a random one printed once
at startup and never written to disk. The session is an HttpOnly,
SameSite=Strict cookie holding a random token, and every mutating request must
also carry `X-Desk: 1` — a header a cross-site form cannot set, which is the
other half of the CSRF answer.

THE BROWSER NEVER TALKS TO THE PROVIDER. Thumbnails are proxied through this
process, so the editor's machine makes no request to pexels.com at all and no
provider URL is ever put in front of a reader. That is the same reason
`img-src 'self' data:` is what the site ships.
"""

from __future__ import annotations

import hmac
import html
import http.server
import json
import mimetypes
import os
import secrets
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "images"))

import acquire                                            # noqa: E402
import discover                                           # noqa: E402
from lib import imageslots                                # noqa: E402
from lib.data import load as load_data                    # noqa: E402

HOST = "127.0.0.1"
PORT = int(os.environ.get("EUROPEDOOR_DESK_PORT", "8765"))

# THE BROWSER NEVER HOLDS A PROVIDER URL, AND THAT IS NOT THE SAME AS THE
# BROWSER NOT FETCHING ONE.
#
# The first version handed each candidate its preview URL and proxied
# `/api/thumb?u=<url>`, with an allowlist of provider hosts. That works and it
# is the wrong shape: a route that fetches a URL a caller supplies is a
# server-side request forgery with a guard in front of it, and a guard is
# something the next person can widen. The preview URL never leaves this
# process now — a search records `token -> url` here and the candidate carries
# only the token. There is no caller-supplied address to check, so there is
# nothing to widen.
THUMBS: dict[str, str] = {}
THUMB_CAP = 400


# ── sessions ──────────────────────────────────────────────────────────
PASSCODE = os.environ.get("EUROPEDOOR_DESK_PASSCODE") or secrets.token_hex(4)
PASSCODE_WAS_GIVEN = bool(os.environ.get("EUROPEDOOR_DESK_PASSCODE"))
SESSIONS: dict[str, float] = {}
SESSION_HOURS = 12

# A FAILED SIGN-IN COSTS TIME. Not a lockout — locking a local tool out of
# itself is a worse failure than the one it prevents — but a fixed delay,
# so a script cannot walk the space of a short passcode quickly.
SIGNIN_DELAY = 0.4


def new_session():
    tok = secrets.token_urlsafe(32)
    SESSIONS[tok] = time.time() + SESSION_HOURS * 3600
    return tok


def valid(tok):
    if not tok:
        return False
    exp = SESSIONS.get(tok)
    if not exp:
        return False
    if exp < time.time():
        SESSIONS.pop(tok, None)
        return False
    return True


# ── jobs ──────────────────────────────────────────────────────────────
# THE PIPELINE IS VISIBLE OR IT IS MAGIC. Each job keeps an ordered list of
# steps with a state, so the desk can show what has happened and, when
# something fails, exactly which step it failed at and what it said. A job
# that fails never continues to the next step: §17's "never silently
# continue" is the whole reason this is a list and not a boolean.
JOBS: dict[str, dict] = {}
JOB_LOCK = threading.Lock()

STEPS = [
    ("verify", "Candidate verified"),
    ("identity", "Provider id verified"),
    ("original", "Original acquired and hashed"),
    ("derive", "Derivatives generated"),
    ("register", "Provenance registered"),
    ("build", "Site rebuilt with the photograph"),
    ("gates", "Every gate run"),
    ("commit", "Committed to a branch"),
]


def job_new():
    jid = secrets.token_urlsafe(8)
    with JOB_LOCK:
        JOBS[jid] = {
            "id": jid, "state": "running", "started": time.time(),
            "steps": [{"key": k, "label": t, "state": "waiting", "detail": ""}
                      for k, t in STEPS],
            "failure": None, "branch": None, "purpose": None,
        }
    return jid


def job_step(jid, key, state, detail=""):
    with JOB_LOCK:
        for s in JOBS[jid]["steps"]:
            if s["key"] == key:
                s["state"] = state
                if detail:
                    s["detail"] = detail[-1200:]
                return


def job_fail(jid, key, why):
    job_step(jid, key, "failed", why)
    with JOB_LOCK:
        JOBS[jid]["state"] = "failed"
        JOBS[jid]["failure"] = why[-4000:]


def run(cmd, env=None):
    """Run one of the pipeline scripts and return (ok, output).

    THE ENVIRONMENT IS PASSED THROUGH AND NEVER LOGGED. The provider key is
    in it because `acquire.py` needs it; nothing here prints `env`, and the
    output that reaches the browser is the script's own stdout and stderr,
    which the scripts are already checked for not printing a credential.
    """
    r = subprocess.run([sys.executable] + cmd, cwd=ROOT, capture_output=True,
                       text=True, env=env or os.environ.copy())
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def acquire_job(jid, provider, photo_id, purpose, alt, focal):
    """The whole acquisition, as the existing scripts, in order."""
    try:
        data = load_data()
        spec = imageslots.resolve(purpose, data)
        if spec is None:
            job_fail(jid, "verify", f"{purpose!r} is not a purpose.")
            return
        with JOB_LOCK:
            JOBS[jid]["purpose"] = purpose
        job_step(jid, "verify", "done", spec["surface"])

        env = os.environ.copy()
        ok, out = run(["scripts/images/acquire.py", "--provider", provider,
                       "--photo-id", str(photo_id), "--purpose", purpose,
                       "--alt", alt, "--focal", focal], env)
        if not ok:
            # `acquire.py` refuses for several different reasons and its own
            # message is the useful one, so it is passed through rather than
            # replaced with a category.
            job_fail(jid, "identity", out)
            return
        job_step(jid, "identity", "done")
        job_step(jid, "original", "done", out)

        # `derive.py` takes the purpose as a bare argument, which is how the
        # photograph workflow calls it. The desk runs the same command.
        ok, out = run(["scripts/images/derive.py", purpose], env)
        if not ok:
            job_fail(jid, "derive", out)
            return
        job_step(jid, "derive", "done", out)
        job_step(jid, "register", "done", "data/images.json")

        ok, out = run(["tools/build.py"], env)
        if not ok:
            job_fail(jid, "build", out)
            return
        job_step(jid, "build", "done", out.splitlines()[-1] if out else "")

        gates = [("tools/build.py", ["check"]), ("tools/checks.py", []),
                 ("tools/invariants.py", ["--check"]),
                 ("tools/photo-tests.py", [])]
        lines = []
        for script, extra in gates:
            ok, out = run([script] + extra, env)
            lines.append((out.splitlines() or [""])[-1])
            if not ok:
                job_fail(jid, "gates", f"{script}:\n{out}")
                return
        job_step(jid, "gates", "done", "\n".join(lines))

        # THE BRANCH IS NAMED FOR THE PURPOSE, so two acquisitions cannot
        # land on one branch by accident and a reviewer can tell from the
        # name which surface is being filled.
        branch = "photo/" + purpose.replace("@", "-").replace("/", "-")
        ok, out = git("checkout", "-B", branch)
        if not ok:
            job_fail(jid, "commit", out)
            return
        ok, out = git("add", "-A")
        if not ok:
            job_fail(jid, "commit", out)
            return
        row = json.load(open(os.path.join(ROOT, "data", "images.json"),
                             encoding="utf-8"))["images"].get(spec["key"], {})
        msg = (f"photograph: {spec['surface']}\n\n"
               f"purpose {purpose}\n"
               f"{row.get('licence', '')} · {row.get('photographer', '')}\n"
               f"{row.get('source', '')}\n"
               f"sha256 {row.get('sha256', '')}\n\n"
               f"Acquired through the Media Desk, which runs the same "
               f"scripts the photograph workflow runs.")
        ok, out = git("commit", "-m", msg)
        if not ok:
            job_fail(jid, "commit", out)
            return
        job_step(jid, "commit", "done", branch)
        with JOB_LOCK:
            JOBS[jid]["state"] = "done"
            JOBS[jid]["branch"] = branch
    except Exception as exc:                              # noqa: BLE001
        job_fail(jid, "verify", f"{type(exc).__name__}: {exc}")


# ── the API ───────────────────────────────────────────────────────────
def registry(data):
    """Every purpose the desk can fill, declared or templated, with the
    requirements that come from the SLOT rather than from the interface."""
    reg = json.load(open(os.path.join(ROOT, "data", "images.json"),
                         encoding="utf-8"))["images"]
    by_key = {k: v for k, v in reg.items()}
    out = []
    for name in imageslots.declared():
        spec = imageslots.resolve(name, data)
        out.append(_entry(name, spec, by_key, None))
    for sn, slot in imageslots.slots().items():
        for t in imageslots.targets(slot, data):
            out.append(_entry(f"{sn}{imageslots.SEP}{t}", None, by_key,
                              (sn, t), data))
    return out


def _entry(name, spec, by_key, slot_target, data=None):
    if spec is None:
        sn, t = slot_target
        slot = imageslots.slots()[sn]
        spec = {k: v for k, v in slot.items() if k not in ("targets", "key")}
        spec["key"] = slot["key"].replace("{target}", t)
        spec["slot"] = sn
        spec["target"] = t
        spec["surface"] = slot["surface"].replace(
            "{name}", imageslots.label(sn, t, data))
        spec["path"] = imageslots.path(sn, t, data)
    row = by_key.get(spec["key"])
    return {
        "purpose": name,
        "slot": spec.get("slot"),
        "target": spec.get("target"),
        "role": spec.get("role"),
        "key": spec["key"],
        "path": spec["path"],
        "surface": spec["surface"],
        "min_width": spec.get("min_width"),
        "orientation": spec.get("orientation"),
        "min_aspect": spec.get("min_aspect"),
        "max_aspect": spec.get("max_aspect"),
        "note": spec.get("note", ""),
        # THE STATUS MACHINE, DERIVED. A stored state is a state that goes
        # stale the moment somebody edits the register by hand; every one of
        # these is read off what actually exists.
        "status": "PUBLISHED" if row else "EMPTY",
        "photograph": row or None,
    }


def search(provider, purpose, query, per_page, data):
    spec = imageslots.resolve(purpose, data)
    if spec is None:
        return {"error": f"{purpose!r} is not a purpose"}
    ok, why = acquire.cleared(provider)
    if not ok:
        return {"error": "REFUSED: " + why}
    try:
        payload, cached = discover.cached_search(
            provider, query, spec.get("orientation", "landscape"), per_page)
    except urllib.error.HTTPError as exc:
        # RATE LIMITS ARE REPORTED, NEVER RETRIED AROUND. A loop that retries
        # into a 429 is how an integration gets a key revoked, and the brief
        # forbids it by name. One attempt, and the reader is told to wait.
        if exc.code == 429:
            return {"error": "The provider is rate-limiting this key. Wait "
                             "and search again — nothing here retries, "
                             "because retrying into a limit is how a key "
                             "gets revoked.", "rate_limited": True}
        return {"error": f"the provider answered {exc.code}"}
    except urllib.error.URLError as exc:
        return {"error": f"could not reach the provider: {exc.reason}"}

    reg = json.load(open(os.path.join(ROOT, "data", "images.json"),
                         encoding="utf-8"))["images"]
    used = {}
    for k, row in reg.items():
        if row.get("provider") == provider:
            used.setdefault(str(row.get("provider_photo_id")), []).append(
                row.get("purpose") or k)

    cands = []
    for c in discover.normalise(provider, payload):
        bad = acquire.fits(c, spec)
        tok = secrets.token_urlsafe(12)
        if len(THUMBS) > THUMB_CAP:
            THUMBS.clear()
        THUMBS[tok] = c["preview"]
        cands.append({
            **{k: c[k] for k in ("id", "photographer", "photographer_url",
                                 "page", "width", "height", "alt")},
            "thumb": tok,
            "aspect": round(c["width"] / c["height"], 3) if c["height"] else 0,
            "suits": not bad,
            "why_not": bad,
            # §25, in the direction that was missing: the same photograph
            # already in the register, wherever it is used.
            "already": used.get(c["id"], []),
        })
    return {
        "candidates": cands, "cached": cached,
        "surface": spec["surface"],
        "needs": {"min_width": spec.get("min_width"),
                  "orientation": spec.get("orientation"),
                  "min_aspect": spec.get("min_aspect"),
                  "max_aspect": spec.get("max_aspect")},
        # NOTHING HERE IS RANKED. The order is the provider's own and the
        # desk says so on its face — position is exactly what `--pick 3` got
        # wrong, and a highlighted cell is a recommendation by another name.
        "order": "the provider's own search order, carrying no judgement",
    }


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "EuropeDoorDesk"

    def log_message(self, fmt, *args):                    # noqa: A003
        # The default logger prints the full request line, which would put a
        # search query and a photo id in the terminal on every keystroke.
        # The method and the path without its query is enough to debug.
        path = self.path.split("?")[0]
        sys.stderr.write(f"  {self.command} {path}\n")

    # ── plumbing ──────────────────────────────────────────────────
    def _send(self, code, body, ctype="application/json", extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # The desk is a local tool and still ships the headers the site does:
        # a page that can be framed or sniffed is a page that can be abused,
        # and there is no reason for this one to be the exception.
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _cookie(self):
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "desk":
                return v
        return ""

    def _authed(self):
        return valid(self._cookie())

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 1 << 20:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def _q(self):
        return urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)

    # ── routes ────────────────────────────────────────────────────
    def do_GET(self):                                     # noqa: N802
        path = urllib.parse.urlsplit(self.path).path
        if path in ("/", "/index.html"):
            return self._page("desk.html")
        if path in ("/desk.css", "/desk.js"):
            return self._page(path.lstrip("/"))
        if path == "/api/session":
            return self._send(200, {"signed_in": self._authed()})
        if not self._authed():
            return self._send(401, {"error": "sign in first"})
        if path == "/api/registry":
            return self._send(200, {"purposes": registry(load_data()),
                                    "slots": list(imageslots.slots()),
                                    "providers": sorted(acquire.PROVIDERS)})
        if path == "/api/search":
            q = self._q()
            return self._send(200, search(
                (q.get("provider") or ["pexels"])[0],
                (q.get("purpose") or [""])[0],
                (q.get("q") or [""])[0],
                max(1, min(40, int((q.get("n") or ["15"])[0]))),
                load_data()))
        if path == "/api/thumb":
            return self._thumb()
        if path.startswith("/api/job/"):
            jid = path.rsplit("/", 1)[-1]
            with JOB_LOCK:
                job = JOBS.get(jid)
            return self._send(200 if job else 404, job or {"error": "no such job"})
        return self._send(404, {"error": "no such route"})

    def do_POST(self):                                    # noqa: N802
        path = urllib.parse.urlsplit(self.path).path
        # A cross-site form can POST and cannot set a custom header, so this
        # plus SameSite=Strict is the CSRF answer without a token round-trip.
        if self.headers.get("X-Desk") != "1":
            return self._send(400, {"error": "not a desk request"})
        if path == "/api/signin":
            given = str(self._body().get("passcode") or "")
            time.sleep(SIGNIN_DELAY)
            if not hmac.compare_digest(given, PASSCODE):
                return self._send(401, {"error": "that is not the passcode"})
            tok = new_session()
            return self._send(200, {"signed_in": True}, extra={
                "Set-Cookie": f"desk={tok}; HttpOnly; SameSite=Strict; Path=/"})
        if path == "/api/signout":
            SESSIONS.pop(self._cookie(), None)
            return self._send(200, {"signed_in": False}, extra={
                "Set-Cookie": "desk=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"})
        if not self._authed():
            return self._send(401, {"error": "sign in first"})
        if path == "/api/acquire":
            b = self._body()
            for field in ("provider", "photo_id", "purpose", "alt"):
                if not str(b.get(field) or "").strip():
                    return self._send(400, {"error": f"{field} is required"})
            jid = job_new()
            threading.Thread(target=acquire_job, args=(
                jid, str(b["provider"]), str(b["photo_id"]), str(b["purpose"]),
                str(b["alt"]), str(b.get("focal") or "50,50")), daemon=True).start()
            return self._send(202, {"job": jid})
        return self._send(404, {"error": "no such route"})

    def _page(self, name):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            return self._send(404, "not found", "text/plain")
        ctype = mimetypes.guess_type(p)[0] or "text/plain"
        with open(p, "rb") as fh:
            body = fh.read()
        if name == "desk.html":
            body = body.replace(b"{{PASSCODE_HINT}}", html.escape(
                "Set in EUROPEDOOR_DESK_PASSCODE." if PASSCODE_WAS_GIVEN
                else "Printed in the terminal this desk is running in."
            ).encode())
        return self._send(200, body.decode(), ctype + "; charset=utf-8")

    def _thumb(self):
        """Serve one preview by the TOKEN the search issued.

        The editor's machine makes no request to the provider, no provider
        URL is ever in the page, and this route cannot be pointed anywhere:
        a token either names a URL this process recorded during a search it
        performed, or it names nothing.
        """
        if not self._authed():
            return self._send(401, {"error": "sign in first"})
        url = THUMBS.get((self._q().get("t") or [""])[0] or "")
        if not url:
            return self._send(404, {"error": "no such preview"})
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                blob = r.read(12 << 20)
                ctype = r.headers.get("Content-Type", "image/jpeg")
        except (urllib.error.URLError, OSError) as exc:
            return self._send(502, {"error": f"preview failed: {exc}"})
        if not ctype.startswith("image/"):
            return self._send(502, {"error": "that was not an image"})
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(blob)))
        self.send_header("Cache-Control", "private, max-age=600")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(blob)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    provider_keys = [p for p, cfg in acquire.PROVIDERS.items()
                     if os.environ.get(cfg["env"])]
    srv = Server((HOST, PORT), Handler)
    print()
    print("  EuropeDoor Media Desk")
    print(f"  http://{HOST}:{srv.server_address[1]}")
    print()
    print(f"  passcode   {PASSCODE}"
          + ("   (from EUROPEDOOR_DESK_PASSCODE)" if PASSCODE_WAS_GIVEN
             else "   (random, this run only)"))
    print(f"  providers  {', '.join(provider_keys) or 'NONE — no key in the environment'}")
    print()
    print("  The key stays in this process. The browser sends a provider, a")
    print("  photo id, a purpose and a target, and nothing else.")
    print()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  desk closed")


if __name__ == "__main__":
    main()
