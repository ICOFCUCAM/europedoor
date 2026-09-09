#!/usr/bin/env python3
"""Every check that has to pass before EuropeDoor ships.

    python3 tools/checks.py

Written as a flat list of named assertions rather than a framework, because
the thing that matters is that a failure names what broke and where. Each
check returns the number of things it looked at, so a check that silently
starts examining nothing shows up as a zero.

The rule for adding one: a check earns its place by catching a mistake that
has actually been made, or one the build makes easy to make. There is a
comment on each explaining which.
"""

from __future__ import annotations

import glob
import hashlib
import html.parser
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D
from lib import pages as P
from lib import score as S
from lib import render as R
from html import unescape as html_unescape

from lib.render import OPERATOR, SITE_NAME, esc

ROOT = D.ROOT
OUT = os.path.join(ROOT, "site")

VOID = {"meta", "link", "br", "img", "input", "hr", "source", "col", "area", "base", "wbr"}
FAILURES = []
CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


def fail(msg):
    FAILURES.append(msg)


def site_files():
    return sorted(glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True))


def rel(path):
    return "/" + os.path.relpath(path, OUT)


def canonical_of(path):
    """The URL a file is served at, given cleanUrls-style hosting."""
    r = rel(path)
    if r == "/index.html":
        return "/"
    if r.endswith("/index.html"):
        return r[: -len("/index.html")]
    return r[: -len(".html")]


class Structure(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errs = []
        self.h1 = 0
        self.titles = []
        self.in_title = False
        self.styles = 0

    def handle_startendtag(self, t, a):
        pass

    def handle_starttag(self, t, a):
        if t == "h1":
            self.h1 += 1
        if t == "title":
            self.in_title = True
        if t == "style":
            self.styles += 1
        if t not in VOID:
            self.stack.append(t)

    def handle_data(self, d):
        if self.in_title:
            self.titles.append(d)

    def handle_endtag(self, t):
        if t == "title":
            self.in_title = False
        if self.stack and self.stack[-1] == t:
            self.stack.pop()
        elif t in self.stack:
            self.errs.append(f"</{t}> closed out of order")
            while self.stack and self.stack.pop() != t:
                pass
        else:
            self.errs.append(f"stray </{t}>")


# ── the checks ────────────────────────────────────────────────────────

@check("the dataset loads and validates")
def c_data():
    d = D.load()
    return len(d["countries"]) + len(d["cities"])


@check("the site was built from the current data")
def c_built():
    # Caught a real failure: a data edit, no rebuild, and a page that still
    # showed the old count. The page count is derived, so a stale site
    # directory shows up here rather than in review.
    if not os.path.isdir(OUT):
        fail("site/ does not exist — run tools/build.py")
        return 0
    d = D.load()
    expect = 1 + 1 + len(d["macros"])
    expect += len(d["countries"])
    expect += sum(len(c["regions"]) for c in d["countries"].values())
    expect += len(d["cities"])
    expect += len(D.all_places(d["countries"]))
    expect += sum(len(P.facets_for(d, c, r, t))
                  for c in d["countries"].values() for r in c["regions"] for t in r["cities"])
    expect += len(d["taxonomy"]["interests"])
    expect += 1 + len(d["journeys"])
    expect += 1 + len(d["themes"])
    expect += 1 + len(d["stories"])
    expect += 2                                   # /plan, /search
    expect += 1 + len(d["taxonomy"]["experience_kinds"]) + 1 + 1   # experiences, kinds, join, business
    expect += len(d["categories"]) + sum(len(c.get("subs", [])) for c in d["categories"])
    expect += 1 + len(d["fund"])
    expect += 6                                   # map, events, quiet, my-europe, method, about
    expect += len(d["taxonomy"]["months"])        # /events/<month>
    expect += 5                                   # how-it-works, sources, freshness,
                                                  # api-docs, manifesto
    expect += 1 + len(d["motions"])               # Europe in Motion
    expect += 1                                   # /discover
    expect += 7                                   # privacy, cookies, terms, accessibility,
                                                  # help, contact, for-tourism-boards
    expect += 1                                   # 404
    got = len(site_files())
    if got != expect:
        fail(f"expected {expect} html files from this data, found {got} — rebuild")
    return got


@check("every page is well-formed and has exactly one h1")
def c_structure():
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        p = Structure()
        p.feed(s)
        if p.errs:
            fail(f"{rel(f)}: {p.errs[0]}")
        if p.stack:
            fail(f"{rel(f)}: unclosed {p.stack[:3]}")
        if p.h1 != 1:
            fail(f"{rel(f)}: {p.h1} h1 elements, expected 1")
        if p.styles:
            # The design system only works if there is one stylesheet. An
            # inline <style> is how that quietly stops being true.
            fail(f"{rel(f)}: has an inline <style> block; put it in the stylesheet")
        n += 1
    return n


@check("every page has a title and a description under 200 characters")
def c_head():
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        if "<title>" not in s:
            fail(f"{rel(f)}: no title")
        m = re.search(r'<meta name="description" content="([^"]*)"', s)
        if not m:
            fail(f"{rel(f)}: no meta description")
        elif len(m.group(1)) > 200:
            fail(f"{rel(f)}: description is {len(m.group(1))} chars")
        elif len(m.group(1)) < 40:
            fail(f"{rel(f)}: description is too short to be useful")
        n += 1
    return n


@check("the brand is locked to EuropeDoor and europedoor.com")
def c_brand():
    # docs/brand-lock.md exists because incoming strategy documents keep
    # arriving with a different name on them. This is the enforcement.
    banned = ["Europe Atlas ·", "Europia", "Via Europa", "Eurovia", "Europe Unbound",
              "europedoor.example",
              # One word, always. The space turns a product name into a
              # generic phrase, and a generic phrase is unregistrable — which
              # matters more than usual here, because the mark is contested.
              "Europe Door"]
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        if "europedoor.com" not in s:
            fail(f"{rel(f)}: no canonical on europedoor.com")
        for b in banned:
            if b in s:
                fail(f"{rel(f)}: carries a competing or placeholder product name {b!r}")
        n += 1
    if SITE_NAME != "EuropeDoor":
        fail(f"SITE_NAME is {SITE_NAME!r}, must be 'EuropeDoor' — see docs/brand-lock.md")
    # The mark is not cleared, and the site must not imply that it is. No page
    # may carry a registration symbol.
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        for sym in ("®", "™"):
            if sym in s:
                fail(f"{rel(f)}: carries {sym} — the mark is not cleared, "
                     "see docs/brand-lock.md")
        n += 1
    return n


@check("every internal link resolves to a page that exists")
def c_links():
    served = set()
    for f in site_files():
        served.add(canonical_of(f))
    # Everything that is not HTML, discovered rather than listed: the
    # hardcoded list went stale the first time a script was added.
    for f in glob.glob(os.path.join(OUT, "**", "*"), recursive=True):
        if os.path.isfile(f) and not f.endswith(".html"):
            served.add("/" + os.path.relpath(f, OUT))
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        for href in re.findall(r'(?:href|src)="(/[^"#?]*)', s):
            n += 1
            if href not in served:
                fail(f"{rel(f)}: dead link to {href}")
    return n


@check("no page leaks an unrendered template expression")
def c_leaks():
    # A f-string that never got interpolated ships as literal Python. It has
    # happened; it is invisible in a diff and obvious on the page.
    bad = re.compile(r"\{esc\(|\{urls\.|\{[a-z_]+\[['\"]|<function |object at 0x")
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        m = bad.search(s)
        if m:
            fail(f"{rel(f)}: unrendered template fragment near {s[max(0,m.start()-40):m.start()+40]!r}")
        n += 1
    return n


@check("countries under a travel advisory are excluded from the planner index")
def c_advisory():
    # The planner must not be able to route into a country nobody should be
    # travelling to. Enforced in the data the browser gets, not in the UI,
    # so no client bug can undo it.
    d = D.load()
    api = json.load(open(os.path.join(OUT, "api", "atlas.json"), encoding="utf-8"))
    advisory = {c["slug"] for c in d["countries"].values() if c.get("advisory")}
    if not advisory:
        fail("no advisory countries in the dataset — this check is no longer testing anything")
    for city in api["cities"]:
        if city["countrySlug"] in advisory:
            fail(f"planner index contains {city['id']}, in an advisory country")
    return len(api["cities"])


@check("advisory countries still have a page, and it carries the warning")
def c_advisory_pages():
    d = D.load()
    n = 0
    for c in d["countries"].values():
        if not c.get("advisory"):
            continue
        f = os.path.join(OUT, "europe", c["slug"], "index.html")
        s = open(f, encoding="utf-8").read()
        if "note warn" not in s or "government travel advice" not in s.lower():
            fail(f"{c['name']}: advisory page does not carry the advisory note")
        n += 1
    return n


@check("the Fund holds no money and offers no way to give any")
def c_fund_holds_nothing():
    # docs/europe-fund.md: the register may not imply custody of funds
    # before there is an entity, a payment path and a legal position.
    # Look for the affordance rather than the word: this page says "there is
    # no donate button" in prose on purpose, and a word-match flagged our own
    # disclaimer, which is exactly the wrong failure.
    affordance = re.compile(
        r"<form|type=\"submit\"|>\s*(donate|give now|contribute now|支付)\s*<"
        r"|href=\"[^\"]*(stripe|paypal|gofundme|justgiving|patreon)",
        re.I,
    )
    amount = re.compile(r"€\s?\d[\d,.]*\s*(raised|of\s+(the\s+)?goal|so far)", re.I)
    n = 0
    for f in glob.glob(os.path.join(OUT, "fund", "**", "*.html"), recursive=True):
        s = open(f, encoding="utf-8").read()
        for rx, why in ((affordance, "a way to give money"), (amount, "an amount raised")):
            m = rx.search(s)
            if m:
                fail(f"{rel(f)}: fund surface offers {why} ({m.group(0)!r})")
        n += 1
    d = D.load()
    for p in d["fund"]:
        for k in ("amount", "raised", "goal", "target"):
            if k in p:
                fail(f"fund/{p['slug']}: carries {k!r}")
    return n


@check("no page names an operating company that does not exist")
def c_no_fake_entity():
    # Naming an entity that is not incorporated would be a straightforward
    # misrepresentation. The footer says so explicitly instead.
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        if OPERATOR not in s:
            fail(f"{rel(f)}: footer does not carry the unincorporated-operator statement")
        if re.search(r"\b(Ltd|GmbH|S\.A\.|LLC|AS|Oy|AB)\b", s):
            fail(f"{rel(f)}: names a company form; there is no operating entity yet")
        n += 1
    return n


@check("scores are derived, in range, and never stored in the data")
def c_scores():
    d = D.load()
    n = 0
    for c in d["countries"].values():
        if "scores" in c:
            fail(f"{c['slug']}: scores must be computed, not written into the data")
        cs = S.country_scores(c)
        for dim, v in cs.items():
            if not (S.FLOOR <= v <= S.CAP):
                fail(f"{c['slug']}: {dim} score {v} out of range")
        for r in c["regions"]:
            for t in r["cities"]:
                for dim, v in S.city_scores(c, r, t).items():
                    if not (S.FLOOR <= v <= S.CAP):
                        fail(f"{c['slug']}/{t['slug']}: {dim} score {v} out of range")
                n += 1
    return n


@check("the method page publishes every dimension the scores use")
def c_method_published():
    # A score whose formula is not on /method is a ranking, which is the one
    # thing docs/scoring-method.md says this must never become.
    s = open(os.path.join(OUT, "method", "index.html"), encoding="utf-8").read()
    for dim in S.DIMENSIONS:
        if esc(S.LABELS[dim]) not in s:
            fail(f"/method does not publish the {dim} dimension")
    return len(S.DIMENSIONS)


@check("every journey's nights add up to the days it advertises")
def c_journeys():
    d = D.load()
    for j in d["journeys"]:
        total = sum(l["nights"] for l in j["legs"])
        if total != j["days"] - 1:
            fail(f"journeys/{j['slug']}: {total} nights but {j['days']} days")
    return len(d["journeys"])


@check("every city page links up to its region, country and macro region")
def c_hierarchy():
    d = D.load()
    n = 0
    for c in d["countries"].values():
        for r in c["regions"]:
            for t in r["cities"]:
                f = os.path.join(OUT, "europe", c["slug"], r["slug"], t["slug"], "index.html")
                s = open(f, encoding="utf-8").read()
                for up in (f"/europe/{c['slug']}\"", f"/europe/{c['slug']}/{r['slug']}\"",
                           f"/discover/{c['macro_slug']}\""):
                    if up not in s:
                        fail(f"{t['slug']}: no link up to {up}")
                n += 1
    return n


@check("the sitemap lists every page and nothing else")
def c_sitemap():
    s = open(os.path.join(OUT, "sitemap.xml"), encoding="utf-8").read()
    listed = set(re.findall(r"<loc>https://europedoor\.com([^<]*)</loc>", s))
    served = {canonical_of(f) for f in site_files() if f.endswith("index.html")}
    missing = served - listed
    extra = listed - served
    if missing:
        fail(f"sitemap missing {len(missing)} pages, e.g. {sorted(missing)[:3]}")
    if extra:
        fail(f"sitemap lists {len(extra)} pages that do not exist, e.g. {sorted(extra)[:3]}")
    return len(listed)


@check("the planner index points only at pages that exist")
def c_api():
    api = json.load(open(os.path.join(OUT, "api", "atlas.json"), encoding="utf-8"))
    served = {canonical_of(f) for f in site_files()}
    for city in api["cities"]:
        if city["url"] not in served:
            fail(f"api: {city['id']} points at {city['url']}, which is not built")
        if not city["nights"] or city["nights"][0] < 1:
            fail(f"api: {city['id']} has no usable night range")
    for j in api["journeys"]:
        ids = {c["id"] for c in api["cities"]}
        for leg in j["legs"]:
            if leg["id"] not in ids:
                # A journey may legitimately pass through an advisory country
                # only if we ever add one; today that would be a bug.
                fail(f"api: journey {j['slug']} leg {leg['id']} is not in the planner index")
    return len(api["cities"])


@check("the search index points only at pages that exist")
def c_search():
    idx = json.load(open(os.path.join(OUT, "api", "search.json"), encoding="utf-8"))
    served = {canonical_of(f) for f in site_files()}
    d = D.load()
    advisory = {c["slug"] for c in d["countries"].values() if c.get("advisory")}
    for row in idx["rows"]:
        if row["u"] not in served:
            fail(f"search index: {row['n']!r} points at {row['u']}, which is not built")
    # Advisory countries stay findable — a page nobody can search for is a
    # page that does not exist, and the warning is the point of keeping it.
    names = {r["n"] for r in idx["rows"]}
    for slug in advisory:
        c = d["countries"][slug]
        if c["name"] not in names:
            fail(f"search index is missing {c['name']}, which still has a page")
    return len(idx["rows"])


@check("no image is published without a photographer, a source and a licence")
def c_images():
    """The rule that replaced "no photographs at all".

    Refusing every <img> kept the licensing position simple by making it
    impossible to get wrong, and that was the right rule while there was no
    image pipeline. It is the wrong rule now that there is one, because it
    bans the correct behaviour along with the incorrect one.

    So the rule is stronger rather than looser: an image may be published,
    and only if a row in data/images.json names who took it, where it came
    from and under what licence. An unlicensed photograph on a public page
    is the most expensive mistake a travel site can make, and it is always
    made by accident — by an <img> somebody added in a hurry, which is
    exactly what this refuses.
    """
    d = D.load()
    images = d["images"]
    known = {row["file"] for row in images.values()}
    n = 0
    svgs = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        svgs += s.count("<svg")
        for tag in re.findall(r"<img[^>]*>", s):
            m = re.search(r'src="([^"]+)"', tag)
            if not m:
                fail(f"{rel(f)}: an <img> with no src")
                continue
            src = m.group(1)
            # Never a third party. The CSP already blocks it, but a check
            # that names the reason is worth more than a silent failure.
            if src.startswith("http") and "europedoor.com" not in src:
                fail(f"{rel(f)}: hotlinks a photograph from {src}")
            stem = re.sub(r"-\d+\.(jpg|webp|avif)$", "", src.split("/")[-1])
            if stem not in known:
                fail(f"{rel(f)}: <img> for {stem!r} has no row in data/images.json — "
                     "no photographer, no source, no licence")
            for attr in ("alt=", "width=", "height=", "loading="):
                if attr not in tag:
                    fail(f"{rel(f)}: <img> for {stem!r} is missing {attr[:-1]}")
            n += 1
        # One eager image per page, and no more. Page weight is then one
        # question per page rather than a total.
        eager = len(re.findall(r'<img[^>]*loading="eager"', s))
        if eager > 1:
            fail(f"{rel(f)}: {eager} eager images; a page gets one hero and the rest lazy")
    if svgs == 0:
        fail("no generated illustrations found at all")
    return n + svgs


@check("every experience kind has a page and every experience is on one")
def c_experiences():
    d = D.load()
    kinds = d["taxonomy"]["experience_kinds"]
    for k in kinds:
        if not os.path.exists(os.path.join(OUT, "experiences", "kind", k, "index.html")):
            fail(f"no page for experience kind {k}")
    items = D.all_experiences(d["countries"])
    for it in items:
        f = os.path.join(OUT, "experiences", "kind", it["exp"]["kind"], "index.html")
        s = open(f, encoding="utf-8").read()
        if esc(it["exp"]["name"]) not in s:
            fail(f"experience {it['exp']['slug']} missing from its kind page")
    return len(items)


@check("every country's verification status is stated, not implied")
def c_freshness():
    # An unmarked page reads as a checked page. Every country page must say
    # which it is, and the board must list all of them.
    d = D.load()
    board = open(os.path.join(OUT, "sources", "freshness", "index.html"), encoding="utf-8").read()
    for c in d["countries"].values():
        if c["name"] not in board:
            fail(f"freshness board omits {c['name']}")
        f = os.path.join(OUT, "europe", c["slug"], "index.html")
        s = open(f, encoding="utf-8").read()
        if "Facts checked" not in s:
            fail(f"{c['name']}: country page does not state its verification status")
        if not c.get("checked") and "not verified" not in s:
            fail(f"{c['name']}: unverified, but the page does not say so")
    return len(d["countries"])


@check("a verification record expires, and confidence cannot be authored")
def c_verification_expiry():
    """Exercise all four verification states against synthetic records.

    No country has been checked yet, so every real record takes the same
    branch and the other three would rot untested until the first check was
    made — which is exactly the wrong moment to discover that "due for
    review" never fires. These are fixtures, not data: they are constructed
    here and never written to a file, so nothing on the site claims a check
    that did not happen.
    """
    import datetime
    today = datetime.date(2026, 1, 1)
    n = 0

    def v(checked):
        return P.verification_of({"checked": checked} if checked else {}, today=today)

    never = v(None)
    if never["state"] != "never" or never["confidence"] != "low":
        fail(f"an unchecked country did not read as never/low: {never}")
    n += 1

    official = [{"what": "Currency and blocs", "where": "Norges Bank",
                 "kind": "official", "url": "https://example.invalid/"}]

    fresh = v({"on": "2025-12-01", "by": "A. Editor",
               "status": "officially-sourced", "sources": official})
    if fresh["state"] != "current" or fresh["confidence"] != "high":
        fail(f"a recent officially-sourced check did not read as current/high: {fresh}")
    n += 1

    # One day past the interval, the same record must stop reading as
    # verified. This is the assertion the whole mechanism exists for.
    stale = v({"on": "2024-12-31", "by": "A. Editor",
               "status": "officially-sourced", "sources": official})
    if stale["state"] != "due":
        fail(f"a check {P.REVIEW_DAYS + 1} days old still read as current: {stale}")
    if stale["confidence"] != "low":
        fail("a check past its review interval kept its confidence")
    n += 2

    # Recent, but nobody wrote down what they checked it against.
    thin = v({"on": "2025-12-01", "by": "A. Editor", "status": "editor-reviewed"})
    if thin["confidence"] != "low":
        fail(f"a check with no sources did not read as low confidence: {thin}")
    n += 1

    # Recent and sourced, but not to a body answerable for the fact.
    mid = v({"on": "2025-12-01", "by": "A. Editor", "status": "editor-reviewed",
             "sources": [{"what": "Cost bands", "where": "our own editor",
                          "kind": "editorial"}]})
    if mid["confidence"] != "medium":
        fail(f"a recent non-official check did not read as medium: {mid}")
    n += 1

    # And the schema must refuse an authored confidence outright.
    if "confidence is derived" not in open(
            os.path.join(ROOT, "tools", "lib", "data.py"), encoding="utf-8").read():
        fail("the validator no longer refuses an authored confidence field")
    n += 1

    board = open(os.path.join(OUT, "sources", "freshness", "index.html"), encoding="utf-8").read()
    for phrase in ("Never checked", "Checked and current", "Checked but now due again",
                   "Review interval"):
        if phrase not in board:
            fail(f"the freshness board no longer reports {phrase!r}")
        n += 1
    return n


@check("the content security policy is strict, and nothing on any page needs it loosened")
def c_csp():
    """The policy is only worth what the pages let it be.

    A single inline <script> or a single style="..." attribute anywhere
    forces 'unsafe-inline' into the corresponding directive, and that keyword
    allows every injected script or style too — so the weakest page sets the
    policy for all 987. This check is the thing that stops one convenience
    from quietly doing that.

    Style ATTRIBUTES are the trap: Chromium's own console message says CSP
    hashes do not apply to them, so unlike an inline <style> block they
    cannot be excepted individually. They have to be gone.
    """
    n = 0
    for keyword in ("'unsafe-inline'", "'unsafe-eval'", "'unsafe-hashes'", "*"):
        if keyword in R.CSP_HEADER.replace("data:", ""):
            fail(f"the policy has been loosened with {keyword}")
        n += 1
    # frame-ancestors does nothing in a meta tag and Chromium logs that it is
    # ignored. It belongs in the header only.
    if "frame-ancestors" in R.CSP_META:
        fail("frame-ancestors is in the meta policy, where browsers ignore it")
    if "frame-ancestors" not in R.CSP_HEADER:
        fail("frame-ancestors is missing from the header policy, where it works")
    n += 2

    inline_style = re.compile(r'\sstyle="')
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, OUT)
        # An inline <script> with no src. type="application/json" is data,
        # not script, and is exactly how page data is passed instead.
        for m in re.finditer(r"<script([^>]*)>", h):
            attrs = m.group(1)
            if "src=" in attrs:
                continue
            # Data blocks, not script. The browser never executes either,
            # and Chromium reports zero CSP violations for both — verified
            # rather than assumed, because "surely CSP does not apply to
            # that" is how an exception list starts growing.
            if 'type="application/json"' in attrs or 'type="application/ld+json"' in attrs:
                continue
            fail(f"{rel}: an inline script would force script-src 'unsafe-inline'")
        if inline_style.search(h):
            fail(f"{rel}: a style attribute would force style-src 'unsafe-inline' "
                 "— use a utility class; CSP hashes do not apply to style attributes")
        if "Content-Security-Policy" not in h:
            fail(f"{rel}: no content security policy")
        n += 1

    # THE HOST ACTUALLY READS vercel.json.
    #
    # site/_headers is Netlify and Cloudflare Pages syntax. This site deploys
    # to Vercel, which ignores it entirely — so for as long as the headers
    # lived only in that file, not one of them shipped to production. The
    # repository looked correct and the served site had no HSTS, no nosniff,
    # no Permissions-Policy and no frame-ancestors. Only the meta CSP was
    # doing anything.
    #
    # Both files are now emitted from render.HEADERS, and this check fails if
    # either drifts from it. A security header that exists in the repository
    # and not in the response is worse than a missing one, because it stops
    # anybody looking.
    vercel = json.load(open(os.path.join(ROOT, "vercel.json"), encoding="utf-8"))
    catch_all = [h for h in vercel.get("headers", []) if h.get("source") == "/(.*)"]
    if len(catch_all) != 1:
        fail("vercel.json has no single catch-all header rule; "
             "the security headers do not reach production")
    served = {h["key"]: h["value"] for h in catch_all[0]["headers"]}
    for name, value in R.HEADERS.items():
        if served.get(name) != value:
            fail(f"vercel.json {name}: serves {served.get(name)!r}, "
                 f"render.HEADERS says {value!r}")
        n += 1

    hdr = open(os.path.join(OUT, "_headers"), encoding="utf-8").read()
    for directive in R.CSP_META.split("; "):
        if directive not in hdr:
            fail(f"_headers is missing {directive!r} that the meta policy carries")
        n += 1
    for name in ("Referrer-Policy", "X-Content-Type-Options", "Permissions-Policy",
                 "Strict-Transport-Security"):
        if name not in hdr:
            fail(f"_headers no longer sets {name}")
        n += 1

    # And no third-party origin, which is what makes default-src 'none' hold.
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        for m in re.finditer(r'(?:src|href)="(https?://[^"]+)"', h):
            if not m.group(1).startswith("https://europedoor.com"):
                fail(f"{os.path.relpath(f, OUT)}: loads from {m.group(1)}")
        n += 1
    return n


@check("every social card exists, is a real PNG, and comes from the same drawing as the page")
def c_social_cards():
    """og:image, and the failure mode nobody catches.

    A social card is the one image on this site that its own authors never
    look at: it is rendered inside somebody else's product, days later, from
    a URL nobody clicks. So a card that is missing, corrupt, the wrong size,
    or a *different drawing from the page it represents* can be broken for
    months without anybody noticing.

    Hence four assertions rather than "the tag is present": the file exists,
    it is a valid PNG whose real dimensions match the ones the tag declares,
    nothing in the cache is an orphan, and the raster and the SVG are driven
    by one geometry function so they cannot drift apart.
    """
    n = 0
    referenced = set()
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        m = re.search(r'<meta property="og:image" content="([^"]+)"', h)
        if not m:
            # Only entity pages carry a card. A card for /terms would be a
            # landscape with no relationship to the page.
            continue
        url = m.group(1)
        if not url.startswith("https://europedoor.com/assets/og/"):
            fail(f"{rel(f)}: og:image points off-site: {url}")
            continue
        name = url.rsplit("/", 1)[-1]
        referenced.add(name)
        path = os.path.join(OUT, "assets", "og", name)
        if not os.path.exists(path):
            fail(f"{rel(f)}: og:image {name} does not exist")
            continue
        raw = open(path, "rb").read()
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            fail(f"{name}: not a PNG")
            continue
        # IHDR is always the first chunk: 8 magic + 4 length + 4 tag.
        width, height = struct.unpack(">II", raw[16:24])
        declared_w = re.search(r'og:image:width" content="(\d+)"', h)
        declared_h = re.search(r'og:image:height" content="(\d+)"', h)
        if not declared_w or not declared_h:
            fail(f"{rel(f)}: og:image with no declared width and height")
        elif (width, height) != (int(declared_w.group(1)), int(declared_h.group(1))):
            fail(f"{rel(f)}: og:image is {width}x{height}, tag says "
                 f"{declared_w.group(1)}x{declared_h.group(1)}")
        if 'og:image:alt' not in h:
            fail(f"{rel(f)}: og:image with no alt")
        if 'name="twitter:card" content="summary_large_image"' not in h:
            fail(f"{rel(f)}: og:image without a large-card hint")
        n += 1

    if not referenced:
        fail("no social cards at all")

    # Orphans. The cache is content-addressed, so changing the drawing
    # changes every filename; without pruning it accumulates a directory of
    # pictures from past versions that nobody can account for.
    cache = os.path.join(ROOT, "assets", "og")
    on_disk = {x for x in os.listdir(cache) if x.endswith(".png")}
    for orphan in sorted(on_disk - referenced):
        fail(f"assets/og/{orphan} is an orphan: no page asks for it")
    for missing in sorted(referenced - on_disk):
        fail(f"assets/og/{missing} is referenced but not cached")
    n += len(on_disk)

    # One drawing, two renderers. This is the assertion that matters: if
    # somebody adds a shape to the SVG path only, the card silently stops
    # representing the page.
    r = open(os.path.join(ROOT, "tools", "lib", "render.py"), encoding="utf-8").read()
    raster_src = open(os.path.join(ROOT, "tools", "lib", "raster.py"), encoding="utf-8").read()
    if "def plate_shapes" not in r:
        fail("render.plate_shapes is gone; the two renderers have no shared geometry")
    plate_body = r.split("def plate(seed")[1].split("\ndef ")[0]
    if "plate_shapes(" not in plate_body:
        fail("render.plate() no longer renders from plate_shapes(); "
             "the SVG and the social card are now two separate drawings")
    if "plate_shapes" not in raster_src and "shapes" not in raster_src:
        fail("raster.py no longer renders from the shared geometry")
    n += 3
    return n


@check("structured data is valid, matches the page, and claims nothing we do not hold")
def c_structured_data():
    """JSON-LD is a machine-readable claim, republished by people who cannot
    check it. That makes a wrong one worse than none at all.

    Three things are checked. That it parses and carries the required
    properties. That it agrees with the visible page — a breadcrumb that
    disagrees with the one a reader can see is the exact failure this format
    invites, because nobody looks at it. And that it never carries the four
    properties this product cannot honestly emit.
    """
    # Emitting any of these would be inventing data in a format designed to
    # be trusted. There are no reviews, nothing is bookable, the validator
    # refuses opening hours, and there are no photographs.
    FORBIDDEN = ("aggregateRating", "reviewCount", "ratingValue", "offers",
                 "price", "priceRange", "openingHours", "openingHoursSpecification")
    n = 0
    seen_types = set()
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
        if not blocks:
            continue
        if len(blocks) > 1:
            fail(f"{rel(f)}: {len(blocks)} ld+json blocks; one per page, as an array")
        try:
            data = json.loads(blocks[0])
        except Exception as e:
            fail(f"{rel(f)}: ld+json does not parse: {e}")
            continue
        items = data if isinstance(data, list) else [data]
        flat = json.dumps(items)
        for bad in FORBIDDEN:
            if f'"{bad}"' in flat:
                fail(f"{rel(f)}: structured data carries {bad!r}, which this "
                     "product does not hold")
        for item in items:
            if "@context" not in item:
                fail(f"{rel(f)}: an ld+json item with no @context")
            if "@type" not in item:
                fail(f"{rel(f)}: an ld+json item with no @type")
                continue
            seen_types.add(item["@type"])
            # A null or empty value is worse than an absent one: it says
            # "we have this property" and then does not.
            for key, value in item.items():
                if value is None or value == "" or value == []:
                    fail(f"{rel(f)}: {item['@type']}.{key} is empty; omit it instead")
            n += 1

            if item["@type"] == "BreadcrumbList":
                # It must agree with the breadcrumb a reader can see. A
                # machine-readable trail nobody looks at is a trail that
                # drifts.
                names = [x["name"] for x in item["itemListElement"]]
                positions = [x["position"] for x in item["itemListElement"]]
                if positions != list(range(1, len(positions) + 1)):
                    fail(f"{rel(f)}: breadcrumb positions are not 1..n")
                visible = re.search(r'<nav class="crumbs".*?</nav>', h, re.S)
                if visible:
                    text = re.sub(r"<[^>]+>", "\u0000", visible.group(0))
                    shown = [x.strip() for x in text.split("\u0000") if x.strip() and x.strip() != "/"]
                    if [html_unescape(x) for x in shown] != names:
                        fail(f"{rel(f)}: the structured breadcrumb says {names} "
                             f"but the page shows {shown}")
                n += 1
            else:
                # Every entity must be self-identifying and point at itself.
                # Article names itself with headline rather than name, which
                # is schema.org's own spelling, not an exception.
                naming = "headline" if item["@type"] == "Article" else "name"
                for required in (naming, "url"):
                    if required not in item:
                        fail(f"{rel(f)}: {item['@type']} has no {required}")
                url = item.get("url", "")
                if url and not url.startswith("https://europedoor.com"):
                    fail(f"{rel(f)}: {item['@type']}.url is {url}")

    # The types we mean to emit. A new one appearing without a decision is
    # worth a failing check, because schema types carry search behaviour.
    # ItemList arrived with Europe in Motion, where a page IS a list of
    # destinations a query returned. Added deliberately: this guard exists so
    # a schema type cannot appear without somebody deciding it should, and
    # this is that decision.
    expected = {"BreadcrumbList", "Country", "TouristDestination",
                "TouristAttraction", "TouristTrip", "Article", "WebSite",
                "ItemList"}
    if seen_types - expected:
        fail(f"unexpected schema types: {sorted(seen_types - expected)}")
    if expected - seen_types:
        fail(f"schema types that should be emitted and are not: "
             f"{sorted(expected - seen_types)}")
    if n < 2000:
        fail(f"only {n} structured-data items across the site")
    return n


@check("the map is drawn from open data we hold, host and can rebuild")
def c_map():
    """The map must cost nothing to run, and that has to be checkable.

    "EuropeDoor does not pay for maps" is a product decision, and a product
    decision that lives only in a document is a product decision somebody
    undoes in a hurry on a Friday. Six assertions, each one guarding a
    different way that could happen:

      1. no published page reaches a commercial map provider or a public tile
         server — checked by hostname, on the actual HTML and JavaScript
      2. no licence-bearing source is fetched without its licence written down
         first, and the bytes on disk are the bytes that were checked
      3. the datasets deliberately refused stay refused, and stay documented
      4. data/geo/ is what the pipeline produces from data/raw/ — the same
         staleness contract as site/
      5. every country in the Atlas is on the map, as a shape or as a named
         point, and never quietly missing
      6. the provenance travels with the geometry: every published file names
         the dataset, the licence and the hash it came from
    """
    n = 0

    # 1. No third-party map anything. Hostnames rather than a vague "maps"
    # substring, because a page that says "the map" is not a violation and a
    # check that cannot tell the difference gets switched off.
    banned = (
        "api.mapbox.com", "mapbox.com", "maps.googleapis.com", "maps.google.com",
        "api.maptiler.com", "maptiler.com", "tile.openstreetmap.org",
        "tiles.openstreetmap.org", "basemaps.cartocdn.com", "api.here.com",
        "dev.virtualearth.net", "services.arcgisonline.com", "tiles.stadiamaps.com",
        "unpkg.com/maplibre", "cdn.jsdelivr.net/npm/maplibre",
    )
    for path in site_files() + sorted(glob.glob(os.path.join(OUT, "assets", "js", "*.js"))):
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
        low = body.lower()
        for host in banned:
            if host in low:
                fail(f"{rel(path)} reaches {host} — the map must cost nothing to run "
                     f"and must add no third-party origin")
        n += 1

    # 2 and 3. The register, and the licence document that must exist before
    # anything is fetched.
    regpath = os.path.join(ROOT, "docs", "data-licenses", "sources.json")
    if not os.path.exists(regpath):
        fail("docs/data-licenses/sources.json is missing — no dataset can be traced")
        return n
    with open(regpath, encoding="utf-8") as fh:
        reg = json.load(fh)
    for src in reg["sources"]:
        doc = os.path.join(ROOT, "docs", "data-licenses", src["licence_doc"])
        if not os.path.exists(doc):
            fail(f"{src['id']} has no licence record at docs/data-licenses/{src['licence_doc']}")
        raw = os.path.join(ROOT, src["path"])
        if not os.path.exists(raw):
            fail(f"{src['id']} is registered but {src['path']} is not in the repository")
            continue
        if not src.get("sha256"):
            fail(f"{src['id']} has no recorded sha256 — run scripts/map/fetch.py")
            continue
        with open(raw, "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
        if got != src["sha256"]:
            fail(f"{src['path']} is not the file that was checked: recorded "
                 f"{src['sha256'][:12]}, on disk {got[:12]}")
        n += 3
    for b in reg.get("blocked", []):
        doc = os.path.join(ROOT, "docs", "data-licenses", b["licence_doc"])
        if not os.path.exists(doc):
            fail(f"blocked dataset {b['id']} has no licence record saying why")
        if not b.get("reason"):
            fail(f"blocked dataset {b['id']} carries no reason")
        n += 2

    # 4. data/geo/ is generated, and a stale generated directory means the
    # site is drawing something no longer derivable from its documented source.
    sys.path.insert(0, os.path.join(ROOT, "scripts", "map"))
    try:
        import process as MAPPIPE
    except Exception as exc:                        # noqa: BLE001
        fail(f"scripts/map/process.py will not import: {exc}")
        return n
    produced = MAPPIPE.build()
    geodir = os.path.join(ROOT, "data", "geo")
    for relpath, obj in produced.items():
        full = os.path.join(geodir, relpath)
        if not os.path.exists(full):
            fail(f"data/geo/{relpath} is missing — run scripts/map/process.py")
            continue
        with open(full, encoding="utf-8") as fh:
            if fh.read() != MAPPIPE.dump(obj):
                fail(f"data/geo/{relpath} is stale — run scripts/map/process.py")
        n += 1

    # 5. Every country in the Atlas is on the map somewhere. A country that is
    # neither a shape nor a named point has silently fallen off, and on a map
    # of fifty countries nobody counts.
    d = D.load()
    for lod in ("europe-lod0.json", "europe-lod1.json"):
        doc = produced[lod]
        drawn = {i for i, e in doc["countries"].items() if e["atlas"]}
        named = set(doc["nogeometry"])
        for c in d["countries"].values():
            code = c["code"].lower()
            if code not in drawn and code not in named:
                fail(f"{c['name']} is in the Atlas but is neither drawn nor named "
                     f"in {lod}")
            n += 1
        # 6. Provenance travels with the geometry.
        if not doc.get("sources"):
            fail(f"{lod} carries no provenance")
        for src in doc.get("sources", []):
            if not src.get("licence") or not src.get("sha256"):
                fail(f"{lod} names a source with no licence or no hash")
            n += 1

    # The published copies under /api/geo/ must be the same files.
    for lod in ("europe-lod0.json", "europe-lod1.json"):
        pub = os.path.join(OUT, "api", "geo", lod)
        if not os.path.exists(pub):
            fail(f"/api/geo/{lod} was not published")
            continue
        with open(pub, encoding="utf-8") as a, open(os.path.join(geodir, lod), encoding="utf-8") as b:
            if a.read() != b.read():
                fail(f"/api/geo/{lod} differs from data/geo/{lod}")
        n += 1
    return n


@check("the standing instruction holds, and its palette is arithmetically possible")
def c_instruction():
    """docs/instruction.md and docs/palette.json, checked rather than trusted.

    A palette written only in prose drifts. Somebody nudges a hex "slightly
    warmer" during a redesign, the contrast ratio goes with it, and nothing
    complains until a reader cannot see a link — at which point the palette
    document still says 4.77:1 and is wrong. So the roles are declared as data
    and the ratios are recomputed here, from the hexes actually in the file.

    Also: the letters AI stay out of the branding. The customer sees
    EuropeDoor and then experiences intelligence; they do not see AI EUROPE
    TRAVEL PLATFORM. That is the single easiest line in the instruction for a
    well-meaning person to cross, because every competitor has crossed it.
    """
    n = 0
    path = os.path.join(ROOT, "docs", "palette.json")
    if not os.path.exists(path):
        fail("docs/palette.json is missing — the palette has no checkable form")
        return n
    with open(path, encoding="utf-8") as fh:
        pal = json.load(fh)

    def _lum(hexv):
        h = hexv.lstrip("#")
        ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]

    def _ratio(a, b):
        la, lb = _lum(a), _lum(b)
        hi, lo = max(la, lb), min(la, lb)
        return (hi + 0.05) / (lo + 0.05)

    tok = pal["tokens"]
    for name, t in tok.items():
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", t["hex"]):
            fail(f"palette token {name} is not a six-digit hex: {t['hex']}")
        if not t.get("role"):
            fail(f"palette token {name} has no stated role")
        n += 1

    # Every claimed pairing must actually clear the line it claims. WCAG 2.2
    # AA: 4.5 for body text, 3.0 for large text and UI edges.
    for c in pal["claims"]:
        for side in ("fg", "bg"):
            if c[side] not in tok:
                fail(f"palette claim names unknown token {c[side]}")
                break
        else:
            r = _ratio(tok[c["fg"]]["hex"], tok[c["bg"]]["hex"])
            if c.get("text") and r < 4.5:
                fail(f"palette claims {c['fg']} is body text on {c['bg']}, but it is "
                     f"{r:.2f}:1 and AA needs 4.50")
            if c.get("ui") and r < 3.0:
                fail(f"palette claims {c['fg']} is usable UI on {c['bg']}, but it is "
                     f"{r:.2f}:1 and AA needs 3.00")
            n += 2

    # And the forbidden pairings must stay forbidden. A hex edit that
    # accidentally makes one of these pass means the palette moved without
    # anybody deciding to move it — which is worth failing on, because the
    # instruction reasons about these values by name.
    for c in pal["forbidden"]:
        if c["fg"] not in tok or c["bg"] not in tok:
            fail(f"forbidden pairing names an unknown token: {c['fg']} on {c['bg']}")
            continue
        r = _ratio(tok[c["fg"]]["hex"], tok[c["bg"]]["hex"])
        if r >= 4.5:
            fail(f"{c['fg']} on {c['bg']} is listed as forbidden but now measures "
                 f"{r:.2f}:1 — the palette moved; re-decide rather than re-label")
        if not c.get("why"):
            fail(f"forbidden pairing {c['fg']} on {c['bg']} carries no reason")
        n += 1

    if sum(pal["ratio"][k] for k in pal["ratio"] if not k.startswith("$")) != 100:
        fail("the palette ratio does not add to 100")
    n += 1

    # Gold is out of the system entirely, and this is the assertion that keeps
    # it out: no token in the palette, and no rule in the stylesheet, may be a
    # gold or brass. Gold says luxury, premium, heritage, wealth. The product
    # has to say Europe, discovery, movement, intelligence, culture, future.
    if not pal.get("gold", "").startswith("None"):
        fail("docs/palette.json no longer states that there is no gold")
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"), encoding="utf-8").read()
    if re.search(r"--(brass|gold)\s*:", css):
        fail("assets/css/europedoor.css defines a gold or brass token; "
             "European Future has no gold")
    for hexv, token in re.findall(r"(#[0-9a-fA-F]{6})", css) and \
            [(m, m) for m in re.findall(r"#[0-9a-fA-F]{6}", css)]:
        r_, g_, b_ = (int(hexv[i:i + 2], 16) for i in (1, 3, 5))
        # A gold is a mid-lightness, saturated yellow: red high, green close
        # behind, blue far back. This catches #8a6d34 and #c2a165, the two
        # brasses that were in the previous system, without catching the
        # limestone ground (which is barely saturated) or terracotta (whose
        # green sits far below its red).
        if 90 <= r_ <= 215 and abs(r_ - g_) < 55 and (g_ - b_) > 45 and (r_ - b_) > 70:
            fail(f"assets/css/europedoor.css still contains a gold: {hexv}")
    n += 2

    doc = os.path.join(ROOT, "docs", "instruction.md")
    if not os.path.exists(doc) or os.path.getsize(doc) < 4000:
        fail("docs/instruction.md is missing or a stub")
    else:
        body = open(doc, encoding="utf-8").read()
        for token in ("#101214", "#F7F6F3", "#3157FF", "#C8FF4D", "#14483C", "#A4491F"):
            if token not in body:
                fail(f"docs/instruction.md does not name {token}")
            n += 1
        # The readable table and the register must agree on the values the
        # instruction reasons about by name.
        for name in ("graphite", "limestone", "cobalt", "lime", "atlantic", "terracotta"):
            if tok[name]["hex"].upper() not in body.upper():
                fail(f"docs/instruction.md and docs/palette.json disagree about {name}")
            n += 1

    # "AI" stays out of the branding: the masthead, the primary navigation and
    # every h1. Matched as a standalone word so "Ukraine" and "said" are safe,
    # and case-sensitively so nothing trips on ordinary prose.
    word = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])")
    for path in site_files():
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
        head = body.split("</header>", 1)[0]
        if word.search(re.sub(r"<[^>]+>", " ", head)):
            fail(f"{rel(path)} puts AI in the masthead — the assistant is called "
                 f"EuropeDoor Guide, and the customer sees EuropeDoor")
        for m in re.finditer(r"<h1[^>]*>(.*?)</h1>", body, re.S):
            if word.search(re.sub(r"<[^>]+>", " ", m.group(1))):
                fail(f"{rel(path)} puts AI in an h1")
        n += 1
    return n


@check("the knowledge graph holds what the schema asks for, and refuses what it cannot know")
def c_schema():
    """The Build Package v1 §2 schema, audited against the running data.

    Three groups of assertion, and the third is the one that matters:

      1. What EXISTS. Every entity the schema names has the fields it asks
         for, or a documented equivalent — iso3, coordinates and population
         are derived from Natural Earth and carry the dataset that produced
         each value.
      2. What is DERIVED rather than authored. A measurement a person can
         type is a measurement somebody will type wrong, and a wrong
         population with no source attached is indistinguishable from a right
         one. So the derived fields must be absent from every authored file
         and present in data/geo/facts.json.
      3. What is REFUSED. The schema asks a place for `featured`, `rating`
         and `review_count`. There is no such field and there will not be:
         sponsorship attaches to a provider and affects directory surfaces
         only, and we hold no ratings for anywhere in Europe. This group
         asserts the refusal at the file level, so the wall cannot be walked
         through by adding a key to one JSON file.
    """
    n = 0
    d = D.load()

    # 1. Derived facts exist and travel with their provenance.
    for c in d["countries"].values():
        got = c.get("derived", {})
        for field in ("iso3", "lat", "lon", "population"):
            if field not in got:
                fail(f"{c['slug']} has no derived {field} — run scripts/map/process.py")
            n += 1
        if got and not c.get("derived_source"):
            fail(f"{c['slug']} carries derived facts with no source named")
        for r in c["regions"]:
            if r.get("type") not in D.REGION_TYPES:
                fail(f"{c['slug']}/{r['slug']} has type {r.get('type')!r}")
            if "lat" not in r.get("derived", {}):
                fail(f"{c['slug']}/{r['slug']} has no derived position")
            n += 2
    # 2. And are absent from every authored file.
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "countries", "*.json"))):
        raw = json.load(open(path, encoding="utf-8"))
        base = os.path.basename(path)
        for field in D.DERIVED_COUNTRY:
            if field in raw:
                fail(f"data/countries/{base} authors {field!r}, which is derived")
        for r in raw.get("regions", []):
            for field in ("lat", "lon", "latitude", "longitude", "geometry"):
                if field in r:
                    fail(f"data/countries/{base} authors a region {field!r}")
            for t in r.get("cities", []):
                for field in D.DERIVED_CITY:
                    if field in t:
                        fail(f"data/countries/{base}: {t.get('slug')} authors {field!r}")
                # 3. The wall, at the file level.
                for entity, rows in (("place", t.get("places", [])),
                                     ("experience", t.get("experiences", []))):
                    for row in rows:
                        for sold in ("featured", "rank", "boost", "sponsored", "promoted"):
                            if sold in row:
                                fail(f"data/countries/{base}: {entity} "
                                     f"{row.get('slug')} carries {sold!r} — an editorial "
                                     f"record may never be buyable")
                        for unheld in ("rating", "review_count", "reviews", "stars"):
                            if unheld in row:
                                fail(f"data/countries/{base}: {entity} "
                                     f"{row.get('slug')} carries {unheld!r}, which we do "
                                     f"not hold for anywhere in Europe")
                        for volatile in ("hours", "opening_hours", "price", "price_level",
                                         "website", "phone"):
                            if volatile in row:
                                fail(f"data/countries/{base}: {entity} "
                                     f"{row.get('slug')} carries {volatile!r}, which goes "
                                     f"stale and damages a traveller when it is wrong")
                        n += 3
        n += 1

    # The §2.5 edge: every link resolves, and resolves within its own
    # destination. An edge that crosses destinations is a bug that renders as
    # a plausible sentence.
    edges = 0
    for node in d["cities"].values():
        t = node["city"]
        slugs = {pl["slug"] for pl in t.get("places", [])}
        for e in t.get("experiences", []):
            for link in e.get("at", []):
                if link["place"] not in slugs:
                    fail(f"{node['id']}: experience {e['slug']} links to "
                         f"{link['place']!r}, which is not a place here")
                if link["how"] not in D.RELATIONSHIPS:
                    fail(f"{node['id']}: unknown relationship {link['how']!r}")
                edges += 1
                n += 2
    if edges < 10:
        fail(f"only {edges} place-experience edges — the §2.5 relationship is the "
             f"thing that makes this a graph rather than two lists")

    # THE ONE THAT MATTERS. Population is the most tempting proxy for crowding
    # there is, and discoverability is published as explicitly NOT a crowd
    # measurement. The day a score reads a population, /method starts lying.
    score_src = open(os.path.join(ROOT, "tools", "lib", "score.py"), encoding="utf-8").read()
    for banned in ("population", "derived[", 'get("derived")', "pop_max", "POP_"):
        if banned in score_src:
            fail(f"tools/lib/score.py mentions {banned!r} — a score may not read a "
                 f"derived population. Discoverability is not a crowd measurement, "
                 f"and /method says so in those words")
        n += 1

    # §2.14: every edge in the derived relationship index resolves to an
    # entity that exists, and no relationship silently drops to zero.
    #
    # The second half is not hypothetical. `gathers` shipped at zero for one
    # build because the derivation read `theme["places"]` and a theme's
    # destinations are `stops` — a typo in the derivation itself, which is the
    # one failure a derived index cannot catch for you. A count per
    # relationship in the document, and a floor on each here, is what makes it
    # visible.
    gpath = os.path.join(OUT, "api", "graph.json")
    if not os.path.exists(gpath):
        fail("/api/graph.json was not published")
    else:
        with open(gpath, encoding="utf-8") as fh:
            g = json.load(fh)
        ids = {
            "macro": {m["slug"] for m in d["macros"]},
            "country": set(d["countries"]),
            "region": {f'{c["slug"]}/{r["slug"]}'
                       for c in d["countries"].values() for r in c["regions"]},
            "destination": set(d["cities"]),
            "place": {f'{cid}/{pl["slug"]}' for cid, node in d["cities"].items()
                      for pl in node["city"].get("places", [])},
            "experience": {f'{cid}#{e["slug"]}' for cid, node in d["cities"].items()
                           for e in node["city"].get("experiences", [])},
            "journey": {j["slug"] for j in d["journeys"]},
            "story": {st["slug"] for st in d["stories"]},
            "theme": {th["slug"] for th in d["themes"]},
        }
        for row in g["edges"]:
            st, si, _rel, tt, ti = row[:5]
            for kind, ident in ((st, si), (tt, ti)):
                if kind in ids and ident not in ids[kind]:
                    fail(f"/api/graph.json: {kind} {ident!r} does not exist")
            n += 1
        floors = {"part_of": 400, "located_in": 400, "near": 1500, "includes": 100,
                  "serves": 200, "gathers": 50, "about": 20, "happens_in": 40,
                  "available_at": 10}
        for rel, floor in floors.items():
            got = g["relationships"].get(rel, 0)
            if got < floor:
                fail(f"/api/graph.json has {got} {rel!r} edges and this atlas has "
                     f"{floor}+ — a relationship that drops to zero is what nobody notices")
            n += 1
        # A weight is a measurement or it is absent. There is no relevance
        # score, because nobody computed one from anything.
        for row in g["edges"]:
            meta = row[5] if len(row) > 5 else {}
            for invented in ("weight", "score", "relevance", "confidence"):
                if invented in meta:
                    fail(f"/api/graph.json carries {invented!r} — the only weight in this "
                         f"graph is `km`, which is a real distance")
            n += 1

    # §2.11: nodes yes, routes never. An operator, a frequency, a duration or
    # a fare in the data is a promise about a departure we cannot keep, and
    # the failure mode is somebody standing on a platform.
    facts_path = os.path.join(ROOT, "data", "geo", "facts.json")
    if os.path.exists(facts_path):
        with open(facts_path, encoding="utf-8") as fh:
            fjson = json.load(fh)
        tr = fjson.get("transport", {})
        if len(tr) < 100:
            fail(f"only {len(tr)} destinations carry a transport node — "
                 f"run scripts/map/process.py")
        for cid, row in tr.items():
            if not row.get("source"):
                fail(f"transport for {cid} names no source")
            for nd in row.get("nodes", []):
                for routish in ("operator", "frequency", "duration_minutes",
                                "price_from", "departs", "arrives"):
                    if routish in nd:
                        fail(f"transport node at {cid} carries {routish!r} — routes are "
                             f"refused; we hold no timetables and own no inventory")
        n += len(tr)
        # Every destination page that shows a distance must say it is a
        # straight line. A kilometre figure next to an airport name reads as
        # travel distance, and for Theth the difference is four hours.
        page = os.path.join(OUT, "europe", "albania", "the-albanian-alps",
                            "theth", "index.html")
        if os.path.exists(page):
            body = open(page, encoding="utf-8").read()
            if "getting-near" in body and "straight line" not in body:
                fail("a destination shows transport distances without saying they are "
                     "straight-line")
            n += 1

    # A draft is excluded from the build, not published with a badge on it.
    for path in sorted(glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True)):
        pass
    published = {c["slug"] for c in d["countries"].values()}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "countries", "*.json"))):
        raw = json.load(open(path, encoding="utf-8"))
        if raw.get("status") == "draft" and raw["slug"] in published:
            fail(f"{raw['slug']} is a draft and was published anyway")
        n += 1
    return n


@check("every published endpoint states what it is, and holds to its contract")
def c_api():
    """The read API, checked as a contract rather than trusted as output.

    Five JSON endpoints and 53 geometry files are published from this build.
    They are static files on a CDN — there is no server, no query parameter
    and no request that can fail — which means the only things that can go
    wrong are silent: a document that stops saying what it is, a field that
    disappears, or a number in one endpoint that disagrees with the same
    number in another.

    So: every endpoint names its terms, every one carries the keys its
    consumers read, and the counts across endpoints have to agree with the
    dataset and with each other.
    """
    n = 0
    d = D.load()
    endpoints = ["atlas.json", "countries.json", "graph.json", "journeys.json",
                 "search.json"]
    docs = {}
    for name in endpoints:
        path = os.path.join(OUT, "api", name)
        if not os.path.exists(path):
            fail(f"/api/{name} was not published")
            continue
        with open(path, encoding="utf-8") as fh:
            docs[name] = json.load(fh)
        n += 1

    # 1. Terms. An endpoint that does not say what may be done with it is an
    # endpoint somebody will assume the wrong thing about. Two of the five
    # shipped without this for months and nothing noticed.
    for name, doc in docs.items():
        lic = doc.get("licence")
        if not isinstance(lic, dict) or not lic.get("use") or not lic.get("attribution"):
            fail(f"/api/{name} does not state its licence")
        if not doc.get("note"):
            fail(f"/api/{name} does not say what it is")
        if doc.get("generated") != "build":
            fail(f"/api/{name} does not declare that it is built, not live")
        n += 3

    # 2. The keys each consumer actually reads. A renamed field in a document
    # nothing validates is a feature that stops working in the browser and
    # nowhere else.
    contracts = {
        "atlas.json": ["cities", "journeys", "interests", "months", "monthNames",
                       "budgets", "currencies"],
        "search.json": ["rows", "counts", "interests", "monthNames"],
        "countries.json": ["countries"],
        "journeys.json": ["journeys"],
        "graph.json": ["edges", "relationships", "shape"],
    }
    for name, keys in contracts.items():
        for key in keys:
            if name in docs and key not in docs[name]:
                fail(f"/api/{name} has lost its {key!r} key, which a consumer reads")
            n += 1

    # 3. The counts agree — with the dataset, and with each other. This is the
    # failure that a static build makes possible and easy: two documents
    # generated in the same run from the same data, disagreeing, because one
    # of them filters and the other forgot to say so.
    if "atlas.json" in docs and "search.json" in docs:
        atlas_cities = len(docs["atlas.json"]["cities"])
        advisory = sum(1 for c in d["countries"].values() if c.get("advisory"))
        stripped = sum(1 for node in d["cities"].values()
                       if node["country"].get("advisory"))
        if atlas_cities != len(d["cities"]) - stripped:
            fail(f"/api/atlas.json holds {atlas_cities} destinations; the atlas has "
                 f"{len(d['cities'])} and {stripped} are stripped as advisory")
        # And the note has to say so, because a document that silently omits
        # 12 destinations is worse than one that omits them and explains why.
        if "advisor" not in docs["atlas.json"].get("note", "").lower():
            fail("/api/atlas.json strips advisory countries and does not say so")
        counts = docs["search.json"].get("counts", {})
        if counts.get("cities") != len(d["cities"]):
            fail(f"/api/search.json counts {counts.get('cities')} destinations, "
                 f"the atlas has {len(d['cities'])}")
        if counts.get("countries") != len(d["countries"]):
            fail(f"/api/search.json counts {counts.get('countries')} countries")
        n += 4

    if "countries.json" in docs:
        if len(docs["countries.json"]["countries"]) != len(d["countries"]):
            fail("/api/countries.json does not hold every country")
        # The opposite rule to atlas.json, and it is deliberate: a consumer
        # deciding what to do about Belarus needs to be told there is an
        # advisory, not handed a document in which it silently does not exist.
        adv = sum(1 for c in docs["countries.json"]["countries"] if c.get("advisory"))
        if adv != sum(1 for c in d["countries"].values() if c.get("advisory")):
            fail("/api/countries.json drops advisory countries; it must keep them")
        n += 2

    # 4. Nothing published invents a number. The same refusal as the schema,
    # applied to the output rather than the input, because a field can be
    # absent from data/ and computed into an endpoint.
    for name, doc in docs.items():
        body = json.dumps(doc)
        for invented in ('"rating"', '"review_count"', '"featured"', '"sponsored"',
                         '"price_from"', '"opening_hours"'):
            if invented in body:
                fail(f"/api/{name} publishes {invented}, which we do not hold")
            n += 1

    # 6. DECLARED DEPENDENCIES. No consumer may depend on a field belonging to
    # another index unless the dependency is declared in data/contracts.json
    # and checked here.
    #
    # Coupling is not the problem; SILENT coupling is. The search.json ->
    # counts -> empty-state relationship is legitimate and load-bearing — the
    # empty state prints "319 destinations" and that number must be live, not
    # typed. What was wrong with it was that nothing said so: splitting the
    # index into search.json + counts.json would have broken a sentence in a
    # UI and no test would have failed.
    cpath = os.path.join(ROOT, "data", "contracts.json")
    if not os.path.exists(cpath):
        fail("data/contracts.json is missing — no data dependency is declared")
    else:
        with open(cpath, encoding="utf-8") as fh:
            contracts = json.load(fh)

        def _dig(doc, path):
            cur = doc
            for part in path.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    return None
                cur = cur[part]
            return cur

        declared_fetches = {}
        for con in contracts["consumers"]:
            js = os.path.join(ROOT, con["consumer"])
            if not os.path.exists(js):
                fail(f"contracts name {con['consumer']}, which does not exist")
                continue
            declared_fetches[con["consumer"]] = set(con["reads"])
            for endpoint, fields in con["reads"].items():
                # A wildcard endpoint (one file per country) is checked
                # against a representative instance.
                probe = endpoint.replace("*", "norway")
                path = os.path.join(OUT, probe.lstrip("/"))
                if not os.path.exists(path):
                    fail(f"{con['consumer']} declares {endpoint}, which is not published")
                    continue
                with open(path, encoding="utf-8") as fh:
                    doc = json.load(fh)
                for field, why in fields.items():
                    if _dig(doc, field) is None:
                        fail(f"{con['consumer']} depends on {endpoint} -> {field}, "
                             f"which is not there ({why[:60]})")
                    if not why:
                        fail(f"{con['consumer']} declares {endpoint} -> {field} "
                             f"with no reason; a dependency without a reason is "
                             f"one nobody can decide to remove")
                    n += 1

        # And the other direction: a consumer that fetches an index it has not
        # declared. This is what makes the rule enforceable rather than
        # aspirational — a new fetch() has to be written down.
        for js_path in sorted(glob.glob(os.path.join(ROOT, "assets", "js", "*.js"))):
            rel = os.path.relpath(js_path, ROOT)
            body = open(js_path, encoding="utf-8").read()
            fetched = set()
            for m in re.finditer(r'["\'](/api/[A-Za-z0-9/_.-]*)', body):
                url = m.group(1)
                if url.endswith("/"):
                    url += "*.json"
                fetched.add(url)
            if not fetched:
                continue
            declared = declared_fetches.get(rel, set())
            for url in fetched:
                if url in declared:
                    continue
                # /api/geo/country/ is written as a prefix and completed at
                # runtime; match it against the wildcard form.
                if any(dec.replace("*.json", "") == url.replace("*.json", "")
                       for dec in declared):
                    continue
                fail(f"{rel} fetches {url} and does not declare it in "
                     f"data/contracts.json — declare the dependency and say "
                     f"which fields it reads")
            n += 1

        for ep in contracts["published_only"]["endpoints"]:
            name = os.path.basename(ep)
            users = [c["consumer"] for c in contracts["consumers"] if ep in c["reads"]]
            if users:
                fail(f"{ep} is listed as published-only but {users[0]} declares it")
            n += 1

    # 5. The documentation page lists every endpoint that exists. An
    # undocumented endpoint is one nobody can rely on.
    api_html = os.path.join(OUT, "api", "index.html")
    if os.path.exists(api_html):
        page = open(api_html, encoding="utf-8").read()
        for name in endpoints:
            if f"/api/{name}" not in page:
                fail(f"/api/{name} is published and not documented on /api")
            n += 1
    return n


@check("the frontend is one shell, eleven primitives and five applications")
def c_frontend():
    """The §4 audit, asserted rather than trusted.

    Every number in docs/frontend-architecture.md came from the build, which
    means every one of them can quietly stop being true. These are the four
    that would change the architecture if they moved:

      1. ONE shell. A second function emitting <html> is how a masthead comes
         to exist twice and diverge within a month.
      2. FIVE applications. 1,067 of 1,072 pages are documents; the moment a
         sixth page starts carrying application logic, the "documents plus a
         handful of apps" framing is wrong and §4 needs revisiting.
      3. ELEVEN primitives covering the site. If a page family stops using
         them, it has grown its own component set and the design system has
         forked without anybody deciding to.
      4. The type scale and the breakpoints stay small. The sibling repository
         measured 418 font sizes and 45 breakpoints; that is what happens
         without a number to hold the line on.
    """
    n = 0
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"), encoding="utf-8").read()

    # 1. One shell, one masthead per page, one footer, no inline style.
    shells = sum(open(os.path.join(ROOT, "tools", "lib", f), encoding="utf-8").read()
                 .count("<!doctype html>") for f in ("render.py", "pages.py"))
    if shells != 1:
        fail(f"{shells} functions emit a page shell; there must be exactly one")
    n += 1
    for path in site_files():
        body = open(path, encoding="utf-8").read()
        mast = body.count('class="masthead"')
        foot = body.count("<footer")
        if mast != 1:
            fail(f"{rel(path)} has {mast} mastheads; there must be exactly one")
        if foot != 1:
            fail(f"{rel(path)} has {foot} footers; there must be exactly one")
        n += 2

    # 2. Five applications and two enhancements — tested by BEHAVIOUR rather
    # than by a list of filenames, because a list of filenames goes stale and
    # a behaviour does not.
    #
    # The first version of this check was a hardcoded set and it had the
    # boundary backwards: it counted events.js (36 lines, a checkbox filter
    # over rows already in the page) as an application, and my-europe.js
    # (which owns all three storage keys) as not one. The objective test:
    #
    #   an APPLICATION fetches an index, or owns client state, or both.
    #     It must declare its dependencies in data/contracts.json.
    #   an ENHANCEMENT does neither. It operates on markup already in the
    #     page, so the page works without it, and it stays small.
    #
    # A script that starts fetching or storing has become an application and
    # has to say what it depends on. A script that does neither and grows past
    # a hundred lines is doing something that needs declaring.
    cpath = os.path.join(ROOT, "data", "contracts.json")
    declared = set()
    if os.path.exists(cpath):
        with open(cpath, encoding="utf-8") as fh:
            declared = {c["consumer"] for c in json.load(fh)["consumers"]}
    apps, enhancements = [], []
    for js_path in sorted(glob.glob(os.path.join(ROOT, "assets", "js", "*.js"))):
        relp = os.path.relpath(js_path, ROOT)
        body = open(js_path, encoding="utf-8").read()
        stateful = ("fetch(" in body or "localStorage" in body)
        (apps if stateful else enhancements).append((relp, body.count("\n")))
        if stateful and relp not in declared:
            fail(f"{relp} fetches or owns state, which makes it an application — "
                 f"declare what it depends on in data/contracts.json")
        if not stateful and body.count("\n") > 100:
            fail(f"{relp} has {body.count(chr(10))} lines and neither fetches nor "
                 f"stores anything. An enhancement that large is an application "
                 f"that has not said so")
        n += 1
    if len(apps) != 5:
        fail(f"{len(apps)} application scripts, and docs/frontend-architecture.md "
             f"is written on there being five: {sorted(a for a, _ in apps)}")
    n += 1

    # 3. The primitives still generate the site. Percentages are floors, not
    # targets: a family that stops using `row` has grown its own components.
    # `card` was 0.70 here and 0.785 in the invariant register, and BOTH were
    # measured with `\bcard\b`, which matches `card-art` because a hyphen is
    # a word boundary. The true figure is 0.226: the design system's
    # most-cited primitive was three-quarters an image wrapper. Found when
    # the destination exemplar renamed that wrapper and the floor collapsed.
    # The matcher below now ends a class token at whitespace or the quote.
    FLOORS = {"kicker": 0.99, "masthead": 0.99, "pagehead": 0.99, "crumbs": 0.99,
              "row": 0.85, "card": 0.20, "band": 0.70, "note": 0.70}
    total = 0
    hits = {k: 0 for k in FLOORS}
    for path in site_files():
        body = open(path, encoding="utf-8").read()
        total += 1
        for prim in FLOORS:
            if re.search(r'class="[^"]*(?<![\w-])' + prim + r'(?![\w-])', body):
                hits[prim] += 1
    for prim, floor in FLOORS.items():
        got = hits[prim] / total
        if got < floor:
            fail(f"the {prim!r} primitive is on {got:.0%} of pages and the audit "
                 f"says {floor:.0%} — a page family has grown its own components")
        n += 1

    # 4. The scale stays small.
    sizes = set(re.findall(r"font-size:\s*([^;]+);", css))
    if len(sizes) > 20:
        fail(f"{len(sizes)} distinct font-size values; the audit measured 13 and the "
             f"sibling repository measured 418")
    bps = set(re.findall(r"@media[^{]*\(m(?:in|ax)-width:\s*([^)]+)\)", css))
    if len(bps) > 10:
        fail(f"{len(bps)} breakpoints; the audit measured 6")
    shadows = set(re.findall(r"box-shadow:\s*([^;]+);", css))
    if len(shadows) > 6:
        fail(f"{len(shadows)} distinct shadows; the audit measured 2")
    if len(glob.glob(os.path.join(ROOT, "assets", "css", "*.css"))) != 1:
        fail("there is more than one stylesheet")
    n += 4
    return n


@check("every plate's light is whole, and every motif is reachable")
def c_plates():
    """Geometry, asserted on all 319 destination plates.

    Two guarantees, both of which were defects until this experiment:

    1. THE LIGHT IS NEVER SLICED. It used to be emitted before the motif at a
       seed-chosen height, so a skyline whose towers rose past it cut the
       circle into a crescent — on Lille's night plate the moon survived as a
       sliver that reads, at the size a card is actually looked at, as a stray
       character. It is now fitted to the sky that exists above the
       silhouette, and where there is no sky the plate has no moon, which is a
       real thing a night city looks like.

       The first attempt at that fix only pushed the light UP with no floor,
       which jammed it against the frame on the tallest skylines. This check
       asserts both: clear of every shape, AND fully inside the frame.

    2. EVERY MOTIF IS REACHABLE. `plain` was declared and never drawn, because
       `food -> plain` sat below eight interests that almost every European
       destination carries, and the hash fallback never fired. A seventh of
       the vocabulary was dead code, and nothing said so.
    """
    d = D.load()
    n = 0
    drawn = set()
    for cid, node in sorted(d["cities"].items()):
        t, r, c = node["city"], node["region"], node["country"]
        motif = (R.motif_for(t["interests"], t.get("city_type"))
                 or R.motif_for(r["interests"]))
        drawn.add(motif)
        seed = f'city:{c["slug"]}:{t["slug"]}'
        for w, h in ((640, 360), (1200, 630)):
            _a, _b, prims = R.plate_shapes(seed, w, h, motif)
            light = next((p for p in prims if p[0] == "circle"), None)
            if light is None:
                n += 1
                continue
            _k, lx, ly, lr, _col, _op = light
            if lx - lr < 0 or lx + lr > w or ly - lr < 0 or ly + lr > h:
                fail(f"{cid}: the light is cropped by the frame at {w}x{h} "
                     f"(centre {lx:.0f},{ly:.0f} radius {lr:.0f})")
            # Nothing painted after the light may overlap it. Bounding boxes
            # are enough: every motif element is axis-aligned or a polygon,
            # and a box that misses cannot overlap.
            for prim in prims:
                if prim is light:
                    continue
                if prim[0] == "rect":
                    x0, y0 = prim[1], prim[2]
                    x1, y1 = x0 + prim[3], y0 + prim[4]
                elif prim[0] == "poly":
                    xs = [p[0] for p in prim[1]]
                    ys = [p[1] for p in prim[1]]
                    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
                else:
                    continue
                # A ridge or a water plane spans the full width and sits below
                # the horizon; overlapping those is a sunset, not a fault. Only
                # the narrow elements — towers, spires, trees — can slice.
                if (x1 - x0) > w * 0.55:
                    continue
                if lx + lr > x0 and lx - lr < x1 and ly + lr > y0 and ly - lr < y1:
                    fail(f"{cid}: the {motif} light is cut by a shape at {w}x{h} — "
                         f"it reads as a stray glyph at card size")
            n += 1

    missing = set(R.MOTIFS) - drawn
    if missing:
        fail(f"{sorted(missing)} declared in MOTIFS and never drawn — a motif "
             f"nothing reaches is dead code that looks like vocabulary")
    n += len(R.MOTIFS)
    return n


@check("the invariants hold — what a visual change may not move")
def c_invariants():
    """docs/invariants.json, recomputed.

    A visual migration is a controlled experiment and this is the control:
    21 things that were true before the change and must still be true after
    it. Recorded with a `why` each, because an invariant nobody can explain
    is one nobody can decide to change.

    Moving one is allowed. Moving one *silently* is not — the register is
    updated in the same commit, and the diff is the record.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import importlib
    inv = importlib.import_module("invariants")
    got = inv.measure()["invariants"]
    path = os.path.join(ROOT, "docs", "invariants.json")
    if not os.path.exists(path):
        fail("docs/invariants.json is missing — run tools/invariants.py --write")
        return 0
    with open(path, encoding="utf-8") as fh:
        want = json.load(fh)["invariants"]
    n = 0
    for name, spec in sorted(want.items()):
        now = got.get(name, {}).get("value")
        exp, kind = spec["value"], spec["kind"]
        if not spec.get("why"):
            fail(f"invariant {name} carries no reason")
        if kind == "floor" and isinstance(exp, dict):
            for k, v in exp.items():
                if now.get(k, 0) < v:
                    fail(f"invariant {name}.{k} fell to {now.get(k)} from {v} — "
                         f"{spec['why']}")
                n += 1
        elif kind == "ceiling":
            if now > exp:
                fail(f"invariant {name} rose to {now} above {exp} — {spec['why']}")
            n += 1
        else:
            if now != exp:
                fail(f"invariant {name} is {now!r}, recorded {exp!r} — {spec['why']}")
            n += 1
    return n


@check("the documentation set exists and is not describing a different repository")
def c_docs():
    """Ten documents the development brief names, plus the ones this project
    added, plus the thing that actually goes wrong with documentation.

    Documentation does not usually go missing. It goes *stale*: docs/roadmap.md
    sat for three sessions claiming 8 journeys, 8 stories, 23 checks and 204
    assertions long after every one of those had moved, and nothing failed —
    because a document that is merely out of date is still a document.

    So this check does two things. It asserts the files exist, and it asserts
    the hand-written ones do not carry counts that the generated ones own. A
    number copied out of a generated document is a number that will be wrong
    within a month, and the fix is to link rather than to copy.
    """
    required = ["api-architecture", "frontend-architecture", "visual-architecture",
                "design-migration", "schema-mapping", "instruction",
                "architecture", "product", "development", "database", "roadmap",
                "api", "ai", "deployment", "security", "content-model",
                "brand", "brand-lock", "images", "data-model", "legal-position",
                "technical-foundation", "audit-2026-09",
                "EUROPEDOOR_2036_TRANSFORMATION"]
    n = 0
    for name in required:
        path = os.path.join(ROOT, "docs", f"{name}.md")
        if not os.path.exists(path):
            fail(f"docs/{name}.md is missing")
            continue
        if os.path.getsize(path) < 400:
            fail(f"docs/{name}.md is a stub")
        n += 1

    # CLAUDE.md is read first by every session and was the one hand-written
    # file the staleness rule did not cover. It carried five wrong counts —
    # 28 checks, 540 browser checks, 1,273 and 326 assertions, 244 cities —
    # all of which had been true once. A count in the file everybody reads
    # first is the worst place for a count to go stale.
    claude = os.path.join(ROOT, "CLAUDE.md")
    if os.path.exists(claude):
        body = open(claude, encoding="utf-8").read()
        for pat, what in ((r"\b(\d+) checks\b", "a check count"),
                          (r"\b(\d+) browser checks\b", "a browser-check count"),
                          (r"\b(\d+) assertions\b", "an assertion count"),
                          (r"\b(\d+) cities\b", "a destination count"),
                          (r"\b(\d+) pages\b", "a page count")):
            for m in re.finditer(pat, body):
                fail(f"CLAUDE.md states {what} ({m.group(0)!r}). Every one of these "
                     f"grew during a single session — link to the command or the "
                     f"generated document instead of copying its number")
            n += 1

    # The generated documents own these numbers. A hand-written document that
    # restates one has taken on a maintenance obligation nobody will honour.
    d = D.load()
    owned = {
        str(len(D.all_places(d["countries"]))): "places",
        str(len(d["journeys"])): "journeys",
        str(len(d["stories"])): "stories",
    }
    generated = {"content-report", "section-audit", "ux-audit"}
    for path in sorted(glob.glob(os.path.join(ROOT, "docs", "*.md"))):
        name = os.path.basename(path)[:-3]
        if name in generated:
            continue
        text = open(path, encoding="utf-8").read()
        for number, what in owned.items():
            # Only the "<n> <thing>" form — a bare number can be anything, and
            # a check that fires on coincidences is a check somebody disables.
            #
            # A document that links content-report.md is exempt, deliberately.
            # The rule being enforced is "if you state a count, point at the
            # document that owns it", not "never state a count": the roadmap
            # and the audit both need to name figures to make an argument,
            # and both send the reader to the regenerated source.
            if f"{number} {what}" in text and "docs/content-report.md" not in text:
                fail(f"docs/{name}.md states '{number} {what}' without pointing at "
                     "docs/content-report.md, which owns that number and regenerates it")
        n += 1

    # The README has to get somebody to a build.
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    for needed in ("python3 tools/build.py", "docs/roadmap.md", "docs/architecture.md"):
        if needed not in readme:
            fail(f"README.md does not mention {needed!r}")
        n += 1
    return n


@check("the honest-status page still distinguishes built from designed")
def c_status_page():
    # The value of /how-it-works is entirely in the distinction. If a
    # section disappears, so does the point of the page.
    s = open(os.path.join(OUT, "how-it-works", "index.html"), encoding="utf-8").read()
    for phrase in ("Built and live", "Designed, not built", "Deliberately blocked"):
        if phrase not in s:
            fail(f"/how-it-works no longer has the {phrase!r} section")
    return 3


@check("no page horizontally overflows on a phone by construction")
def c_no_fixed_widths():
    # Not a rendering test — a source test for the two things that have
    # historically caused it: a pixel width on a block, and a table.
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        for m in re.finditer(r'style="[^"]*width:\s*(\d{3,})px', s):
            fail(f"{rel(f)}: fixed pixel width {m.group(1)}px in an inline style")
        n += 1
    return n


@check("an absence says why it is an absence")
def c_empty_states_explain():
    # THE FOUR PLACES WHERE THIS SITE'S OWN HABIT LAPSED. Everywhere else it
    # states its limits at length — the place page's three refused fields,
    # the interest page's idle keywords, Svalbard's missing map, the facet
    # threshold — and four empty states said only "Nothing tagged yet.",
    # "Nothing listed yet.", "Nothing listed on this route yet." A bare
    # "nothing yet" reads as a page that failed to load.
    #
    # All four are LATENT: not one of them renders today, because every
    # interest has destinations and every kind has entries. So this is
    # asserted against the generator, which is the only place a state nobody
    # can see today still exists. Both halves are required — what is
    # missing, and why — because the second half is the whole point.
    src = open(os.path.join(ROOT, "tools/lib/pages.py"), encoding="utf-8").read()
    n = 0
    for m in re.finditer(r"empty_state\(\s*(?P<q>['\"])(?P<what>.*?)(?P=q)\s*,"
                         r"(?P<why>.*?)\)\}", src, re.S):
        what = m.group("what")
        why = "".join(re.findall(r"['\"]([^'\"]*)['\"]", m.group("why")))
        if not what.endswith((".", "!", "?")):
            fail(f'empty_state("{what[:48]}…") — the first half must be a '
                 f'sentence naming what is missing')
        if len(why) < 80:
            fail(f'empty_state("{what[:48]}…") gives {len(why)} characters of '
                 f'reason — an absence this site chose is content, and "nothing '
                 f'yet" on its own reads as a page that failed to load')
        n += 1
    if n < 4:
        fail(f"only {n} explained empty states found in the generator; there "
             f"were four bare ones and each was replaced")
    # And no bare one may come back.
    for m in re.finditer(r'"[^"]*Nothing (?:tagged|listed|matches)[^"]*"', src):
        if "empty_state" not in src[max(0, m.start() - 300):m.start()]:
            fail(f"a bare empty state is back: {m.group(0)[:70]}")
    return n


@check("a blocked dataset cannot enter the register under another name")
def c_blocked_by_data_not_label():
    # THE BLOCK ONLY EVER FIRED ON THE ID TYPED ON THE COMMAND LINE.
    # fetch.py matched `blocked` against argv and its loop over `sources`
    # never consulted the list at all, so a row added as
    # `osm-land-polygons`, pointing at openstreetmap.org, would have been
    # downloaded without the refusal printing a word. The guard was on the
    # LABEL, and the label is chosen by whoever is adding the dataset.
    #
    # fetch.py matches the data now. This asserts the same thing at CI,
    # because fetch.py is run by a person when a dataset version changes and
    # CI runs on every commit — the register can go wrong months before
    # anybody types the command that would catch it.
    reg = json.load(open(os.path.join(ROOT, "docs/data-licenses/sources.json"),
                         encoding="utf-8"))
    blocked = reg.get("blocked", [])
    n = 0
    for b in blocked:
        if not b.get("refuse_matching"):
            fail(f'blocked entry "{b["id"]}" declares no refuse_matching '
                 f'patterns, so it can only ever be refused by its own id — '
                 f'which is the hole this check exists for')
        n += 1
    for src in reg["sources"]:
        hay = " ".join((src.get("id", ""), src.get("url", ""),
                        src.get("dataset", ""))).lower()
        for b in blocked:
            hit = ([b["id"]] if src.get("id") == b["id"] else []) + [
                pat for pat in b.get("refuse_matching", []) if pat.lower() in hay]
            if hit:
                fail(f'source "{src["id"]}" matches blocked dataset '
                     f'"{b["id"]}" on {hit[0]!r} — {b["licence"]}. A blocked '
                     f'dataset does not become permitted by being given a '
                     f'different id; see docs/data-licenses/{b["licence_doc"]}')
        n += 1
    return n


@check("a page that draws land names where the land came from")
def c_land_is_credited():
    # 318 OF 817 PAGES DREW A COASTLINE WITH NO CREDIT ON THEM, and the 499
    # that had one mostly had it BY ACCIDENT: a destination page names
    # Natural Earth because `pop_line` prints the dataset that produced its
    # population, so the 45 destinations with no population figure had no
    # credit either. Coverage that depends on a different field being
    # present is worse than no coverage, because it looks like a policy.
    #
    # Natural Earth requires no attribution at all — the licence says so —
    # so today this is a matter of taste, and geo.sources_line()'s own
    # docstring gives the reason: a reader looking at a border is entitled
    # to know which dataset drew it, and an uncredited map invites the
    # assumption that we surveyed it.
    #
    # It stops being taste the moment any source in the register carries
    # attribution_required. Every row is false today; this check hardens
    # itself automatically when one is not, and the message says so, so that
    # the first ODbL byte cannot arrive without the credit already being
    # everywhere it has to be.
    reg = json.load(open(os.path.join(ROOT, "docs/data-licenses/sources.json"),
                         encoding="utf-8"))
    required = [s for s in reg["sources"] if s.get("attribution_required")]
    n = 0
    for f in site_files():
        html = open(f, encoding="utf-8").read()
        if '<g class="context"' not in html and 'class="countries"' not in html:
            continue
        n += 1
        if "Natural Earth" not in html:
            extra = (f" A source in the register now requires attribution "
                     f"({required[0]['id']}), so this is a licence breach and "
                     f"not a style question." if required else "")
            fail(f"{rel(f)} draws a coastline and names no source for it."
                 f"{extra}")
    return n


@check("no page carries geography it does not show")
def c_map_land_is_in_frame():
    # A SANTORINI PAGE CARRIED THE COASTLINE OF NORWAY.
    #
    # minimap() asked landmass() for the whole 1000x780 canvas and let the
    # arch's clip path hide everything outside the frame. The picture was
    # right, so nothing looked wrong, and no check had ever measured what a
    # page CONTAINS as against what it SHOWS: 73,464 bytes of continent in
    # every destination and place page, 79.7% of the bytes on a Santorini
    # page, on a site whose heaviest page is a recorded ceiling.
    #
    # It was found by an experiment measuring something else entirely, which
    # is the argument for measuring things. This is the check that would have
    # found it: every coordinate emitted into a map's <g> must be inside the
    # window that <g> is drawn through, with a margin for the clip's own pad.
    def inner_of(html, start):
        """The transform group's contents, matched by depth.

        A non-greedy `(.*?)</g>` was the first version and it stopped at the
        first close tag, which is the end of the nested <g class="context">.
        On most pages that group is empty once the frame is clipped, so the
        check silently examined 74 of 574 maps and reported itself green. A
        check that quietly stops looking is the failure mode this repository
        has already had once, in the browser suite's own counter.
        """
        # Depth starts at 1: `start` is already INSIDE the transform group.
        # Starting it at 0 made the first nested close look like the end and
        # reproduced the original bug exactly — 74 of 574 again.
        depth, i = 1, start
        while i < len(html):
            j = html.find("<g", i)
            k = html.find("</g>", i)
            if k < 0:
                return ""
            if 0 <= j < k:
                depth += 1
                i = j + 2
            else:
                depth -= 1
                if depth == 0:
                    return html[start:k]
                i = k + 4
        return ""

    n = 0
    for f in site_files():
        html = open(f, encoding="utf-8").read()
        for m in re.finditer(
                r'<g transform="translate\((-?[\d.]+),(-?[\d.]+)\) '
                r'scale\(([\d.]+)\)">', html):
            tx, ty, sc = (float(m.group(1)), float(m.group(2)),
                          float(m.group(3)))
            inner = inner_of(html, m.end())
            xs = [float(v) for v in re.findall(r'[ML](-?[\d.]+) ', inner)]
            ys = [float(v) for v in re.findall(r'[ML]-?[\d.]+ (-?[\d.]+)', inner)]
            if not xs:
                continue
            # Into rendered units, the same way the browser will.
            rx = [x * sc + tx for x in xs]
            ry = [y * sc + ty for y in ys]
            # 900x320 is the minimap frame; allow landmass()'s own 40-unit pad
            # scaled, plus a little, before calling it waste.
            slack = 40.0 * sc + 20.0
            out = sum(1 for x, y in zip(rx, ry)
                      if x < -slack or x > 900 + slack
                      or y < -slack or y > 320 + slack)
            if out > len(rx) * 0.02:
                fail(f"{rel(f)}: {out} of {len(rx)} coastline points are "
                     f"outside the frame they are drawn in — the clip path "
                     f"hides them and the page still ships them")
            n += 1
    return n


@check("the projection keeps shape at every latitude it draws")
def c_projection_conformal():
    # THE MEASUREMENT THAT JUSTIFIED REPLACING THE PROJECTION, KEPT AS A
    # GATE. "Shape is right here" has a definition: the scale along the
    # parallel equals the scale along the meridian. The ratio is 1.000
    # everywhere on a conformal projection and nowhere else.
    #
    # The equirectangular predecessor took one cos(latitude) correction at
    # the middle of its extent, so it was exact on one line and wrong on
    # every other. Measured against a sphere of R = 6371 km:
    #
    #     35°N Crete      -25.3%      65°N            +44.9%
    #     45°N            -13.4%      71°N N. Cape    +89.7%
    #     60°N Oslo       +22.4%
    #
    # Norway was drawn 45% too wide at the Arctic Circle on 817 pages. A
    # coastline stretched 45% still looks like a coastline, which is why
    # this needed arithmetic rather than another contact sheet.
    #
    # 0.5% is the tolerance: a hundred times smaller than the smallest error
    # the old projection had anywhere except its one true parallel, and far
    # below the 1.33 km simplification floor of the geometry underneath.
    import math
    from lib import geo
    # The four angles are a DECISION, and conformality does not protect them:
    # moving a standard parallel keeps the projection conformal and quietly
    # redraws Europe. These are EPSG:3034, the conformal conic the EU
    # publishes pan-European maps on, chosen for this exact extent.
    for got, want, what in ((geo.LCC_P1, 35.0, "first standard parallel"),
                            (geo.LCC_P2, 65.0, "second standard parallel"),
                            (geo.LCC_LAT0, 52.0, "latitude of origin"),
                            (geo.LCC_LON0, 10.0, "central meridian")):
        if got != want:
            fail(f"the {what} is {got}, not {want} — the projection is still "
                 f"conformal and Europe is a different shape. Change it "
                 f"deliberately, here, or not at all")
    KM = 111.195          # one degree on a sphere of R = 6371 km, either way
    proj = geo.Projection((-25.0, 33.0, 45.0, 71.5), 1000, 780, pad=0.0)
    n = 0
    for lat in (34.0, 35.0, 40.0, 45.0, 52.25, 60.0, 65.0, 71.0, 71.5):
        for lon in (-24.0, -10.0, 0.0, 10.0, 25.0, 44.0):
            d = 0.02
            x1, y1 = proj.xy(lat, lon - d)
            x2, y2 = proj.xy(lat, lon + d)
            par = math.hypot(x2 - x1, y2 - y1) / (
                2 * d * KM * math.cos(math.radians(lat)))
            x3, y3 = proj.xy(lat - d, lon)
            x4, y4 = proj.xy(lat + d, lon)
            mer = math.hypot(x4 - x3, y4 - y3) / (2 * d * KM)
            err = par / mer - 1.0
            if abs(err) > 0.005:
                fail(f"at {lat}°N {lon}°E the map is {err * 100:+.1f}% out of "
                     f"shape — the scale along the parallel and the scale "
                     f"along the meridian must match, and that is what makes "
                     f"a coastline the right coastline")
            n += 1
    return n


@check("every dot on a map lands inside its own frame")
def c_map_dots_in_frame():
    # Svalbard's region map drew Longyearbyen at y = -317 on a viewBox that
    # starts at 0. The dot was invisible, the map was of an empty sea, and
    # nothing on the page said a place was missing — because the projection
    # stops at 71.5°N and Longyearbyen is at 78.2.
    #
    # No amount of looking at the other 129 region maps would have found it.
    # What found it was asserting the thing a map must be true of: the
    # subject is inside the picture. One of 191 failed.
    n = 0
    for f in site_files():
        html = open(f, encoding="utf-8").read()
        for m in re.finditer(r'pointsmap arched"><svg viewBox="0 0 ([\d.]+) ([\d.]+)"'
                             r'(.*?)</svg>', html, re.S):
            w, h, frag = float(m.group(1)), float(m.group(2)), m.group(3)
            for c in re.finditer(r'<circle cx="([\d.-]+)" cy="([\d.-]+)"', frag):
                x, y = float(c.group(1)), float(c.group(2))
                if not (0 <= x <= w and 0 <= y <= h):
                    fail(f"{rel(f)}: a map dot is at ({x:.0f}, {y:.0f}) on a "
                         f"{w:.0f}x{h:.0f} frame — outside the picture, so it "
                         f"is not drawn and nothing says it is missing")
                n += 1
    return n


@check("the aperture is cut the same way by all three renderers")
def c_aperture_agrees():
    # The signature is one curve cut three ways: an SVG clipPath for the maps
    # (render.arch_path), a pixel mask for the social card
    # (raster.Canvas.arch_mask), and a border-radius for the plates, whose
    # containers are 16/9, 3/4 and 21/9 while their viewBox is only ever
    # 16/9. Three implementations of one shape is exactly the arrangement
    # that drifts: the card stops matching the page and nobody sees it,
    # because a card is rendered inside somebody else's product days later.
    #
    # So this asserts what they have to share. The rise fraction is the whole
    # proportion of the arch — change it in one place and the doorway is a
    # different doorway there — and the head is elliptical, rx = span/2,
    # which is the only form a border-radius can state.
    n = 0
    src = {
        "render.arch_path": open(os.path.join(ROOT, "tools/lib/render.py"),
                                 encoding="utf-8").read(),
        "raster.arch_mask": open(os.path.join(ROOT, "tools/lib/raster.py"),
                                 encoding="utf-8").read(),
    }
    for name, text in src.items():
        body = text.split("def arch_path", 1)[-1] if "path" in name else \
            text.split("def arch_mask", 1)[-1]
        body = body.split("\ndef ", 1)[0]
        if "0.34" not in body:
            fail(f"{name}: the rise is not 0.34 of the height — "
                 f"the three renderers no longer draw one arch")
        n += 1
    # The SVG arc must be elliptical (rx = half, ry = rise), not the circular
    # segment this started as: a circular segment cannot be written as a
    # border-radius, and the plates would lose their aperture to
    # preserveAspectRatio="slice".
    rp = src["render.arch_path"].split("def arch_path", 1)[1].split("\ndef ", 1)[0]
    if "{half:.1f},{rise:.1f}" not in rp:
        fail("render.arch_path: the arc is not rx=half,ry=rise — CSS cannot "
             "state the same curve")
    n += 1
    css = open(os.path.join(ROOT, "assets/css/europedoor.css"),
               encoding="utf-8").read()
    m = re.search(r"\.plate\s*\{[^}]*border-radius:\s*50% 50% 0 0 / "
                  r"(\d+)% (\d+)% 0 0", css)
    if not m:
        fail(".plate has no arch border-radius — the plates are rectangles "
             "again and only the maps and the card carry the door")
    else:
        if m.group(1) != m.group(2) or m.group(1) != "34":
            fail(f".plate border-radius rise is {m.group(1)}%/{m.group(2)}%, "
                 f"not 34%/34% — it no longer matches arch_path")
        n += 1
    return n


@check("nothing in the build depends on Python's randomised hash")
def c_no_builtin_hash():
    # THE BUILD WAS NOT REPRODUCIBLE AND NOTHING SAID SO.
    #
    # minimap() built its clipPath id from `abs(hash((name, lat, lon)))`, and
    # CPython randomises the hash of a string per process. Every build gave
    # all 319 destination pages a different id, so `git status` after a build
    # always reported 319 changed files with nothing behind them — which is
    # exactly the amount of noise one real regression hides in. The generated
    # site is committed and CI fails when it is stale, so "the build produces
    # identical pages" is a promise this repository actually makes.
    #
    # hashlib is fine and is what the plates, the OG cache key and the
    # aperture ids already use. builtins.hash() is not, for anything that
    # reaches a file.
    n = 0
    # "tools" already contains "tools/lib" — listing both walked pages.py
    # twice and reported the same line twice, which is a check lying about
    # how much it found.
    for sub in ("tools", "scripts"):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames[:] = [x for x in dirnames if x != "__pycache__"]
            for fn in sorted(filenames):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                for i, line in enumerate(open(path, encoding="utf-8"), 1):
                    code = line.split("#", 1)[0]
                    if re.search(r"(?<![.\w])hash\s*\(", code):
                        fail(f"{os.path.relpath(path, ROOT)}:{i}: "
                             f"builtins.hash() — randomised "
                             f"per process, so anything it reaches makes the "
                             f"build unreproducible. Use hashlib.")
                n += 1
    return n


@check("no sub-category is a promise of a list that does not exist")
def c_subcategories_reachable():
    # THE `plain` MOTIF RULE, APPLIED TO THE TAXONOMY. A declared vocabulary
    # nothing reaches is dead code that looks like a promise — and a
    # sub-category is a stronger promise than a motif, because it ships as a
    # URL, a card in a grid saying "0 listed", and a page with nothing on it.
    #
    # /experiences/nature/waterfalls and /experiences/nature/national-parks
    # were exactly that. Not a matching bug: no experience in this atlas is
    # about a waterfall or a national park, and broadening the keywords until
    # something fell in would have been fabricating relevance to keep a page
    # alive. They are removed. Two of forty.
    #
    # A floor of one, not three: one is a list, zero is a promise unkept.
    from lib import data as D, categories as CAT
    d = D.load()
    items = D.all_experiences(d["countries"])
    n = 0
    for cat in d["taxonomy"]["categories"]:
        for sub in cat.get("subs", []):
            if not CAT.select(items, cat, sub):
                fail(f'/experiences/{cat["slug"]}/{sub["slug"]} lists nothing — '
                     f'a sub-category is a page, a card and a URL promising a '
                     f'list. Remove it or write something it describes; do not '
                     f'widen its keywords until something falls in')
            n += 1
    return n


@check("every experience in a category earns its place by itself")
def c_category_membership():
    # A property of the CONTAINER may not establish a claim about the ITEM.
    # This repository has now made that mistake twice: the sub-category
    # keywords were matched against the town's NAME (8 wrong listings of
    # 423), and category membership was granted by the town's INTERESTS (516
    # of 866, so Food & drink opened with a nuclear bunker). Both were
    # invisible from the outside — every page rendered, every count was
    # consistent, and the lists were simply wrong.
    #
    # So the rule is asserted directly against the shipped selection: an
    # experience appears in a category only if its own authored `kind` is one
    # the category declares, or its own name/summary/kind matches one of the
    # category's keywords. The town it happens to sit in is not consulted.
    from lib import data as D, categories as CAT
    d = D.load()
    items = D.all_experiences(d["countries"])
    n = 0
    for cat in d["taxonomy"]["categories"]:
        if cat.get("derived"):
            continue
        kinds = set(cat.get("kinds") or ())
        for it in CAT.select(items, cat):
            e = it["exp"]
            own = (e.get("kind") in kinds
                   or any(CAT.matches_sub(e, sub) for sub in cat.get("subs", [])))
            if not own:
                fail(f'/experiences/{cat["slug"]}: "{e["name"]}" is listed but '
                     f'matches nothing about itself — it is there because of '
                     f'{it["city"]["name"]}, and a property of the container '
                     f'cannot establish a claim about the item')
            n += 1
    return n


@check("a great-circle distance is never printed as a journey")
def c_straight_line_honesty():
    # THE ONLY NUMBER IN THIS PRODUCT A READER COULD ACT ON AND BE WRONG.
    #
    # Every distance here is haversine between two coordinates. There is no
    # road and no rail geometry in this repository, so that figure is a floor
    # on the leg and never the leg: Chamonix to Zermatt is 69 km here and
    # about 170 on the ground, round a mountain range, with two changes.
    #
    # The journey pages printed "69 km — a local train or a short drive" for
    # exactly that leg, and the planner printed "about 1h39m" beside it. The
    # thresholds were not wrong; they were being asked a question a straight
    # line cannot answer. Removing the claim then left THREE surfaces
    # pointing at it — the journey map caption ("what each one means on the
    # ground is in the note under the leg"), the /map journey note, and a
    # "Ground covered" row in the facts — each promising an answer that no
    # longer existed anywhere. Only rendering the pages found them.
    #
    # So this asserts the promise on the SHIPPED HTML rather than the source:
    #   1. a page that prints a hop distance says "straight line" on it, and
    #   2. no page anywhere claims a travel mode or a ground distance,
    #      because both would have to be derived from the great circle.
    #
    # It is deliberately a vocabulary check on the built output. A source
    # check would have passed on all three of the surfaces above.
    MODE_CLAIMS = [
        "a local train or a short drive",
        "a comfortable train leg",
        "a long rail day",
        "means on the ground is in the note",
        "Ground covered",
    ]
    n = 0
    for path in site_files():
        h = open(path, encoding="utf-8").read()
        r = canonical_of(path)
        for claim in MODE_CLAIMS:
            if claim in h:
                fail(f'{r}: "{claim}" — a claim about the ground, made from a '
                     f'great-circle distance. This atlas holds no route geometry.')
        # A hop line is the shape `↳ … km …`; the planner builds its own in
        # JavaScript, so the page carrying the planner is checked by the
        # phrase being present in the script it loads (below).
        if 'class="hop"' in h:
            n += 1
            if "straight line" not in h:
                fail(f"{r}: prints a hop distance and never says it is a "
                     f"straight line")
    js = open(os.path.join(ROOT, "assets", "js", "planner.js"),
              encoding="utf-8").read()
    n += 1
    if "in a straight line" not in js:
        fail("planner.js: builds hop lines and never says they are straight-line")
    if "out in both directions" not in js:
        fail("planner.js: prints a travel time from a straight line without "
             "saying the estimate is unsigned — travelHours() knows one "
             "average speed and reads 8h36m for Paris to Marseille")
    return n


@check("every map label is placed against the aperture, by the one rule")
def c_one_label_rule():
    # THREE MAP FAMILIES EACH CHOSE THEIR OWN LABEL POSITION, AND TWO OF THEM
    # ONLY EVER OFFERED ONE.
    #
    # pointsmap had the cartographer's rule (flip to the other side of the
    # dot) and tested it against the rectangle; minimap and the country map
    # put every name to the right of its dot and tested nothing. The drawing
    # is clipped by the ARCH, so the top corners are gone: 184 labels across
    # 142 pages were cut and 14 were drawn entirely inside the removed
    # corner, invisible, with nothing saying a place was missing.
    #
    # All three now ask place_label_box() for a position that survives the
    # curve. A browser check measures the result with the real getBBox — the
    # only instrument that knows how wide a name is — and this one guards the
    # regression that check would not see for a while: a FOURTH map family
    # emitting its own <text class="minilabel"> with its own idea of where a
    # name goes. It is a source check on purpose; the browser suite visits
    # six pages, and a new family might not be one of them.
    src = open(os.path.join(ROOT, "tools", "lib", "pages.py"),
               encoding="utf-8").read()
    emits = re.findall(r"<text class=\\?[\"']?\{?[^>]*minilabel", src)
    n = len(emits)
    # place_label_box is the one place allowed to write that tag.
    fn = src[src.index("def place_label_box("):src.index("def place_label(")]
    inside = len(re.findall(r"<text class=", fn))
    if n - inside > 0:
        fail(f"{n - inside} <text class=\"minilabel\"> emitted outside "
             f"place_label_box(). Every map label is placed against the "
             f"aperture by one rule, because three families each choosing "
             f"their own is how 14 destination names became invisible.")
    # And the aperture the placement tests must be the aperture that cuts.
    # in_arch() restates render.arch_path()'s curve in a second language; if
    # one moves and the other does not, labels are placed against a door
    # that is not there.
    for token in ("vh * 0.34, vw * 0.5", "vh * 0.9, vw * 0.5"):
        if token not in src:
            fail(f"pages.in_arch has stopped matching render.arch_path: "
                 f"{token!r} is gone. The placement rule and the clip path "
                 f"must describe one curve.")
        n += 1
    return n


@check("the year band draws the dataset, and both of its numbers agree with it")
def c_year_band():
    # A CHART IS A CLAIM, AND THIS ONE IS PUBLISHED ON THIRTEEN PAGES.
    #
    # The European year is the events family's subject, and it was drawn as
    # twelve identical chips — the same width and weight whether the month
    # held 3 recurring fixtures or 28. The band replaces them with the shape
    # the data actually has, which means two derived series are now a
    # picture: what is ON in a month (bar, up) and how many countries are in
    # their quieter SHOULDER that month (bar, down).
    #
    # Neither may ever be authored. Both are counted here, independently of
    # pages.year_band(), from the same source it reads — and both are
    # asserted against the built HTML, because a chart that agrees with the
    # generator and disagrees with the dataset is the failure mode a chart
    # has. A bar drawn from a number nobody can check is decoration.
    d = D.load()
    ms = d["taxonomy"]["months"]
    fx = {m: 0 for m in ms}
    sh = {m: 0 for m in ms}
    for c in d["countries"].values():
        for f in c["festivals"]:
            fx[f["month"]] += 1
        if c.get("advisory"):
            continue
        for m in c["season"].get("shoulder", []):
            sh[m] += 1
    n = 0
    pages = [os.path.join(OUT, "events", "index.html")] + [
        os.path.join(OUT, "events", m, "index.html") for m in ms
    ]
    for path in pages:
        if not os.path.exists(path):
            fail(f"{rel(path)}: the events family is missing a page")
            continue
        h = open(path, encoding="utf-8").read()
        if 'class="yearband"' not in h:
            fail(f"{canonical_of(path)}: no year band. It is the events "
                 f"family's signature and it is on every page of the family.")
            continue
        # Every month is reachable from every page of the family, and its
        # printed count is the counted one.
        for m in ms:
            n += 1
            if f'href="/events/{m}"' not in h:
                fail(f"{canonical_of(path)}: the year band does not reach "
                     f"/events/{m}")
            want = (f"{d['taxonomy']['month_names'][m]}: {fx[m]} recurring "
                    f"fixture{'s' if fx[m] != 1 else ''}, {sh[m]} countr"
                    f"{'ies' if sh[m] != 1 else 'y'} in their quieter shoulder")
            if want not in h:
                fail(f"{canonical_of(path)}: the year band's figure for "
                     f"{m} disagrees with the dataset — {want!r} is not on "
                     f"the page. A chart is a claim.")
    # The bars are geometry, so the tallest bar must be the largest number.
    # This is the half a count cannot catch: correct labels over a drawing
    # scaled from the wrong series still reads as a finished chart.
    top = max(ms, key=lambda m: fx[m])
    src = open(os.path.join(ROOT, "tools", "lib", "pages.py"),
               encoding="utf-8").read()
    band = src[src.index("def year_band("):src.index("def events_page(")]
    for token in ("fx[m] / fmax * TALL", "sh[m] / smax * DEEP"):
        n += 1
        if token not in band:
            fail(f"year_band: {token!r} is gone — a bar is no longer scaled "
                 f"by the series it is labelled with.")
    h = open(os.path.join(OUT, "events", top, "index.html"),
             encoding="utf-8").read()
    n += 1
    if 'class="ybar on"' not in h:
        fail(f"/events/{top}: the month you are on is not marked on the band")
    return n


@check("no published page names a projection the build does not use")
def c_published_projection():
    # COMMIT 27 REPLACED THE PROJECTION AND LEFT THE PAGE THAT PUBLISHES IT
    # SAYING THE OLD NAME.
    #
    # Three renderers were made to agree — geo.py, the browser, and a check
    # asserting conformality at 54 points — and /map went on telling readers
    # "Projection: equirectangular, corrected at the middle of the extent."
    # That is the projection whose scale error ran from -25.3% at 35°N to
    # +89.7% at North Cape, and it is exactly the claim the correction was
    # made to stop being true. Every check in the suite was green: not one of
    # them read the prose.
    #
    # A name in a comment is history and is welcome; a name in a PAGE is a
    # claim to a reader. So this reads the shipped HTML only.
    from lib import geo
    GONE = ("equirectangular", "web mercator", "mercator", "plate carrée",
            "plate carree")
    n = 0
    named = 0
    for path in site_files():
        h = open(path, encoding="utf-8").read()
        low = h.lower()
        n += 1
        for bad in GONE:
            if bad in low:
                fail(f"{canonical_of(path)}: names {bad!r} as this map's "
                     f"projection. The build draws a Lambert conformal conic "
                     f"at {geo.LCC_P1:g}/{geo.LCC_P2:g}/{geo.LCC_LAT0:g}/"
                     f"{geo.LCC_LON0:g}.")
        if "conformal conic" in low:
            named += 1
            # And where a page does name it, the four angles it prints must
            # be the four the build uses. A page that names the right
            # projection on the wrong parallels is the same failure one
            # correction later.
            #
            # SCOPED TO THE SENTENCE, because the first version searched the
            # whole document and /map draws its own graticule: "35°N" appears
            # eight times as an axis label, so the assertion was satisfied by
            # the drawing rather than by the claim, and deliberately breaking
            # the prose left it green. A check that can be satisfied by
            # something other than the thing it is about is not a check.
            i = low.index("conformal conic")
            sentence = h[max(0, i - 200):i + 400]
            for label, val in (("P1", geo.LCC_P1), ("P2", geo.LCC_P2),
                               ("LAT0", geo.LCC_LAT0), ("LON0", geo.LCC_LON0)):
                if f"{val:g}°" not in sentence:
                    fail(f"{canonical_of(path)}: names a conformal conic but "
                         f"its {label} of {val:g}° is not in the sentence "
                         f"that names it")
    n += 1
    if not named:
        fail("no published page states the projection Europe is drawn on. "
             "/map used to, and it was wrong for six commits; saying nothing "
             "is how it stayed wrong.")
    return n


@check("an index states the extent of its own set, and the number is the real one")
def c_index_extent():
    # AN INDEX EXISTS TO SAY HOW BIG A SET IS, AND FIVE OF EIGHT DID NOT.
    #
    # Measured across the built site: /journeys, /themes, /europe-in,
    # /beyond-the-obvious and /fund carried a head with no count in it at
    # all. /europe-in was the sharpest case — it stated 319, the population
    # its queries run against, and never 12, the number of queries on the
    # page the reader is looking at. A number that is not the set's own
    # extent is worse than none, because it reads as one.
    #
    # This is also the check that catches the opposite failure, which is the
    # one this repository has already made once: a hard-coded figure that was
    # true two hundred destinations ago. The count must equal what the build
    # actually put on the page, so it can only be right by being derived.
    d = D.load()
    quiet = [n for n in d["cities"].values() if n["city"].get("quiet")]
    want = {
        "/countries": len(d["countries"]),
        "/journeys": len(d["journeys"]),
        "/stories": len(d["stories"]),
        "/themes": len(d["themes"]),
        "/experiences": len(D.all_experiences(d["countries"])),
        "/europe-in": len(d["motions"]),
        "/beyond-the-obvious": len(quiet),
        "/fund": len(d["fund"]),
    }
    n = 0
    for url, size in want.items():
        path = os.path.join(OUT, url.strip("/"), "index.html")
        if not os.path.exists(path):
            fail(f"{url}: index is missing")
            continue
        h = open(path, encoding="utf-8").read()
        i = h.find('class="pagehead')
        head = re.sub(r"<[^>]+>", " ", h[i:h.find("</div>", i)]) if i >= 0 else ""
        nums = {int(x) for x in re.findall(r"\b(\d{1,5})\b", head)}
        n += 1
        if size not in nums:
            fail(f"{url}: the head never says how big the set is. It holds "
                 f"{size}; the head states {sorted(nums) or 'no number at all'}.")
    return n


@check("one thing, one picture — a plate is never chosen twice for the same record")
def c_one_plate_per_thing():
    # THE SAME PLACE HAD TWO LANDSCAPES DEPENDING ON WHICH PAGE YOU MET IT ON.
    #
    # `card()` takes an optional `motif`; without one, plate_shapes() picks
    # from the seed. Fourteen of the twenty call sites passed no motif —
    # including every destination card on a country page and a region page,
    # while the quiet index passed one. So Hallstatt drew its own topography
    # on /beyond-the-obvious and whatever the hash of its slug happened to
    # choose everywhere else.
    #
    # Measured before the fix: 272 of 319 destinations, 15 of 17 journeys and
    # 11 of 13 themes were drawn one way on one page and another way on the
    # next. The rule already existed for stories — "a story is not a place,
    # and its picture may not be drawn from a hash" — and this is the same
    # failure across every other record that knows what it is.
    #
    # The plate is content-addressed, so two pictures also means two cached
    # PNGs and two social cards for one thing.
    #
    # Asserted against the SHIPPED HTML by comparing the plate each page drew
    # for a given seed. A source check on the call sites would pass the day
    # somebody adds a fifteenth.
    seen = {}
    n = 0
    for path in site_files():
        h = open(path, encoding="utf-8").read()
        # every plate carries its seed's identity in the gradient/clip ids
        for m in re.finditer(r'<div class="card-art[^"]*">(.*?)</div>', h, re.S):
            art = m.group(1)
            # A plate names its own gradient and clip after the seed's hash,
            # so the id IS the record's identity in the shipped markup.
            key = re.search(r'id="sky([a-z0-9]+)"', art)
            if not key:
                continue
            n += 1
            k = key.group(1)
            # the drawing itself, with the identity stripped back out
            draw = art.replace(k, "")
            if k in seen and seen[k][0] != draw:
                fail(f"{canonical_of(path)}: the plate for {k} is not the "
                     f"plate {seen[k][1]} drew for it. One record, one "
                     f"picture — a landscape chosen by hash on one page and "
                     f"by what the place is on another is two things to a "
                     f"reader and two social cards to a crawler.")
            seen.setdefault(k, (draw, canonical_of(path)))
    return n


@check("a story's picture is never drawn from a hash, on any page")
def c_story_never_a_plate():
    # THE RULE EXISTED AND WAS ENFORCED ON ONE PAGE OF TWO.
    #
    # "A story is not a place, and its picture may not be drawn from a hash"
    # — the piece about the last unlogged primeval forest in Europe opened on
    # tower blocks, and story_page() was rebuilt on storymap() to fix it: the
    # destinations in the story's own validated `places` field, real
    # coastline, through the arch.
    #
    # The INDEX went on carding all nine with `seed="story:" + slug` and no
    # motif, so every essay got an illustration chosen by the hash of its
    # own slug — the exact thing the rule was written for, one page over,
    # and no check looked. It is fixed by the index having no pictures at
    # all: nine essays are a contents page.
    #
    # Asserted on the shipped HTML for every page in the site, because the
    # next place this can happen is a card on a country page or a related-
    # reading rail that does not exist yet.
    d = D.load()
    slugs = {st["slug"] for st in d["stories"]}
    n = 0
    for path in site_files():
        h = open(path, encoding="utf-8").read()
        # a plate and a story link inside the same card
        for m in re.finditer(r'<a class="card"[^>]*href="/stories/([^"/]+)"'
                             r'(.{0,600}?)</a>', h, re.S):
            n += 1
            if m.group(1) in slugs and 'class="plate"' in m.group(2):
                fail(f'{canonical_of(path)}: the card for the story '
                     f'"{m.group(1)}" draws a generated plate. A story is not '
                     f'a place and its picture may not be drawn from a hash — '
                     f'its own places, a photograph from the register, or '
                     f'nothing.')
    n += 1
    if not os.path.exists(os.path.join(OUT, "stories", "index.html")):
        fail("/stories: the index is missing")
    else:
        idx = open(os.path.join(OUT, "stories", "index.html"),
                   encoding="utf-8").read()
        if 'class="plate"' in idx:
            fail("/stories: the index draws a generated plate. Nine essays "
                 "are a contents page, and the alternative to a hash-drawn "
                 "landscape is not a better hash, it is no picture.")
    return n


def main():
    print(f"{SITE_NAME} — checks\n")
    total = 0
    for name, fn in CHECKS:
        before = len(FAILURES)
        try:
            count = fn()
        except Exception as e:  # a check that crashes is a failed check
            FAILURES.append(f"{name}: raised {e!r}")
            count = 0
        broke = len(FAILURES) - before
        mark = "ok  " if not broke else "FAIL"
        print(f"  {mark}  {name}  ({count})")
        total += count
    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES[:40]:
            print(f"  - {f}")
        if len(FAILURES) > 40:
            print(f"  ... and {len(FAILURES) - 40} more")
        sys.exit(1)
    print(f"all {len(CHECKS)} checks passed, {total} things examined")


if __name__ == "__main__":
    main()
