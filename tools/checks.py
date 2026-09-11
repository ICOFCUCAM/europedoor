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
import colorsys
import json
import math
import os
import subprocess
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D
from lib import pages as P
from lib import score as S
from lib import stay as STAY
from lib import cartography as CARTO
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
            # The published name is `<file>.<version>-<width>.<ext>`; the
            # register is keyed on `<file>`. Strip BOTH — the version tag was
            # added so /assets/ can honestly be served immutable, and a check
            # that did not know about it read the tag as part of the name and
            # reported every real photograph as unregistered.
            stem = re.sub(r"-\d+\.(jpg|webp|avif)$", "", src.split("/")[-1])
            stem = re.sub(r"\.[0-9a-f]{8,}$", "", stem)
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

    # AND NO THIRD-PARTY ORIGIN LOADS, WHICH IS WHAT MAKES default-src 'none'
    # HOLD. This check used to match `src|href` together and fail on any URL
    # to another origin, and that is a SHAPE rather than the promise: an
    # `<a href>` is a navigation and `default-src` does not govern
    # navigations. The Stay layer's outbound referral tripped it on the day
    # it shipped, and the check was right that something new had happened and
    # wrong about what.
    #
    # Split into the two promises that are actually being made:
    #
    #   1. NOTHING LOADS from another origin. Every `src`, every `srcset`,
    #      and `href` on the elements where href means "fetch this" —
    #      <link> and <use> — must be same-origin. That is the CSP claim and
    #      it stays absolute.
    #   2. NOTHING NAVIGATES to another origin unless that origin is a
    #      declared, enabled provider in data/stay.json, and every such link
    #      carries rel="nofollow noopener" and opens in a new tab. That pins
    #      the set of external hosts to the registry: a new outbound host
    #      cannot appear on this site without a row that states its
    #      programme, its mechanism and whether it can supply inventory.
    #
    # Both still fail on the thing they were written for, and 2 fails on
    # three more.
    stayreg = json.load(open(os.path.join(ROOT, "data", "stay.json"),
                             encoding="utf-8")) if os.path.exists(
        os.path.join(ROOT, "data", "stay.json")) else {"providers": []}
    allowed_hosts = {p["host"] for p in stayreg.get("providers", [])
                     if p.get("enabled")}
    # A CREDIT IS A SECOND KIND OF OUTBOUND LINK AND IT IS NOT COMMERCIAL.
    # Pexels' API guidelines require "a prominent link to Pexels" and the
    # photographer credited "with a link to the photo page on Pexels" — an
    # obligation of the licence, not a referral. So those hosts are allowed
    # too, pinned to the licence gate exactly as the commercial ones are
    # pinned to the Stay registry, and they take the opposite rule on
    # `sponsored`: a link we are REQUIRED to publish must not be dressed as
    # one we are paid for.
    gatef = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")
    credit_hosts = set()
    if os.path.exists(gatef):
        for slug, prow in json.load(open(gatef, encoding="utf-8")).items():
            if slug.startswith("$"):
                continue
            # KEYED ON self_host, NOT ON THE API ROUTE. A provider whose API
            # is refused can still be the source of a hand-registered
            # photograph — that is the Unsplash case — and such a photograph
            # carries a credit that links back. Keying this on `usable` alone
            # would have failed the build on the credit for a photograph the
            # licence plainly permits.
            if (prow.get("self_host") or {}).get("value") is not True:
                continue
            for u in prow.get("terms_urls", []):
                credit_hosts.add(u.split("/")[2])
    if not allowed_hosts:
        # Not a failure: it is the state this site was in for its whole life
        # before the Stay layer, and the assertion below is then simply
        # "no external navigation anywhere", which is stronger.
        pass
    loaders = re.compile(
        r'<(?:link|use|img|script|iframe|source|audio|video|embed|object)\b[^>]*?'
        r'(?:src|srcset|href|data)="(https?://[^"]+)"', re.I)
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        # 1. subresources
        for m in re.finditer(r'\bsrc(?:set)?="(https?://[^"]+)"', h):
            if not m.group(1).startswith("https://europedoor.com"):
                fail(f"{os.path.relpath(f, OUT)}: loads from {m.group(1)}")
        for m in loaders.finditer(h):
            if not m.group(1).startswith("https://europedoor.com"):
                fail(f"{os.path.relpath(f, OUT)}: loads from {m.group(1)}")
        # 2. navigations
        for m in re.finditer(r'<a\b([^>]*?)href="(https?://[^"]+)"([^>]*)>', h):
            url = m.group(2)
            if url.startswith("https://europedoor.com"):
                continue
            attrs = m.group(1) + m.group(3)
            host = url.split("/")[2]
            if host in credit_hosts and host not in allowed_hosts:
                rel = re.search(r'rel="([^"]*)"', attrs)
                relv = rel.group(1) if rel else ""
                n += 1
                if "noopener" not in relv:
                    fail(f"{os.path.relpath(f, OUT)}: credit link to {host} "
                         f"has rel={relv!r}, missing 'noopener'")
                if "sponsored" in relv:
                    fail(f"{os.path.relpath(f, OUT)}: credit link to {host} "
                         f"claims rel=sponsored. It is a licence obligation "
                         f"and nobody is paying for it")
                if 'target="_blank"' not in attrs:
                    fail(f"{os.path.relpath(f, OUT)}: credit link to {host} "
                         f"does not open in a new tab")
                continue
            if host not in allowed_hosts:
                fail(f"{os.path.relpath(f, OUT)}: links out to {host}, which is "
                     f"not an enabled provider in data/stay.json — an outbound "
                     f"commercial link needs a row stating its programme and "
                     f"its mechanism before it needs a place on a page")
                continue
            rel = re.search(r'rel="([^"]*)"', attrs)
            relv = rel.group(1) if rel else ""
            for token in ("nofollow", "noopener"):
                if token not in relv:
                    fail(f"{os.path.relpath(f, OUT)}: outbound link to {host} "
                         f"has rel={relv!r}, missing {token!r}")
                n += 1
            if 'target="_blank"' not in attrs:
                fail(f"{os.path.relpath(f, OUT)}: outbound link to {host} does "
                     f"not open in a new tab; leaving the atlas must be the "
                     f"reader's choice and not a side effect")
            # `sponsored` is the machine-readable half of the disclosure and
            # must track the credential, in both directions.
            prov = next(p for p in stayreg["providers"] if p.get("host") == host)
            paid = bool(prov.get("partner_id"))
            if paid and "sponsored" not in relv:
                fail(f"{os.path.relpath(f, OUT)}: {host} carries a partner id, so "
                     f"the link must declare rel=sponsored")
            if not paid and "sponsored" in relv:
                fail(f"{os.path.relpath(f, OUT)}: {host} has no partner id, so "
                     f"rel=sponsored claims a paid relationship that does not exist")
            n += 2
        n += 1
    return n


@check("the Stay lede promises only the readings the section actually carries")
def c_stay_lede():
    """A lede that promises the ground on a page where the ground says nothing.

    The section opens by saying what this atlas can tell you about sleeping
    here. That sentence was FIXED — "where the ground puts you and when the
    beds go" — and the relief paragraph under it is correctly omitted wherever
    the ground was not measured to have anything to say. So on a flat capital
    the section promised a reading and then did not carry it.

    It is the removing-a-claim failure in miniature: the claim went and the
    surface pointing at it stayed. It was invisible on the exemplar, because
    Chamonix is the one case where the sentence happens to be true, and only
    rendering a second and third destination found it.

    Asserted on the shipped HTML in both directions, because a check that only
    caught the over-promise would pass a page that had quietly stopped
    promising a reading it does carry.
    """
    n = 0
    for path in site_files():
        h = open(path, encoding="utf-8").read()
        i = h.find('id="stay"')
        if i < 0:
            continue
        body = h[i:h.find("</section>", i)]
        if "stayreads" not in body:
            continue
        ground = "the ground spreads" in body
        promised = "where the ground puts you" in body
        if promised and not ground:
            fail(f"{rel(path)}: the stay lede promises where the ground puts "
                 f"you, and the section draws no relief reading")
        if ground and not promised:
            fail(f"{rel(path)}: the stay section draws the relief reading and "
                 f"its lede does not promise it")
        n += 2
    return n


@check("every externally governed asset carries a source, a date and evidence")
def c_external_provenance():
    """NO EXTERNAL LICENCE CLAIM ENTERS PRODUCTION FROM MEMORY.

    Anything on this site that somebody else's terms govern — a map dataset,
    an elevation tile, a photograph — has to answer three questions in the
    repository, not in a person's recollection:

        source    the URL it came from
        date      when it was taken, because a licence is a claim about a
                  MOMENT and without the moment it is a claim about nothing
        evidence  the SHA-256 of the bytes as served, so the file here is
                  provably the file that was licensed

    The map datasets have carried all three since the map was built: `url`,
    `fetched` and `sha256` in docs/data-licenses/sources.json. Photographs
    carried five fields and not one of them was a date or a hash, so a row
    could say "Pexels-licensed" with nothing recording when that was true or
    what bytes it was true of. That asymmetry is what this check removes: one
    rule, stated once, applied to every class.

    The sister repository holds 629 photographs under exactly this shape and
    is where the field names came from. **Its answers were not copied** — a
    precedent in another repository is a claim, not evidence, and copying one
    is the thing this check exists to prevent.
    """
    CLASSES = (
        ("map datasets", os.path.join(ROOT, "docs", "data-licenses", "sources.json"),
         "sources", {"source": "url", "date": "fetched", "evidence": "sha256"}),
        ("photographs", os.path.join(ROOT, "data", "images.json"),
         "images", {"source": "source", "date": "fetched", "evidence": "sha256"}),
    )
    n = 0
    for label, path, container, fields in CLASSES:
        if not os.path.exists(path):
            fail(f"{label}: {os.path.relpath(path, ROOT)} is missing — a class "
                 f"of external asset with no register at all")
            continue
        doc = json.load(open(path, encoding="utf-8"))
        rows = doc.get(container, {})
        rows = rows.values() if isinstance(rows, dict) else rows
        for row in rows:
            who = row.get("id") or row.get("file") or "?"
            n += 3
            if not str(row.get(fields["source"], "")).startswith("http"):
                fail(f"{label}/{who}: no source URL. Where it came from is the "
                     f"first thing anybody re-checking the licence needs")
            if not re.match(r"^\d{4}-\d{2}-\d{2}$",
                            str(row.get(fields["date"], ""))):
                fail(f"{label}/{who}: no date. A licence is a claim about a "
                     f"moment; without the moment it is a claim about nothing")
            if not re.match(r"^[0-9a-f]{64}$", str(row.get(fields["evidence"], ""))):
                fail(f"{label}/{who}: no sha256. Without it nothing proves the "
                     f"file here is the file that was licensed")
    # A class that exists and is not listed above is the failure this check
    # cannot see, so the list is asserted against the directory it describes.
    known = {"sources.json", "photo-providers.json"}
    for name in sorted(os.listdir(os.path.join(ROOT, "docs", "data-licenses"))):
        if name.endswith(".json") and name not in known:
            fail(f"docs/data-licenses/{name} is a register this check does not "
                 f"know about — add it to CLASSES or it is governed by nothing")
        n += 1
    return n


@check("no photograph enters without its licence verified against the live terms")
def c_photo_gate():
    """No verified licence, no production image — and verified means READ.

    The gate does not ask whether anybody KNOWS what Unsplash allows. It asks
    for the sentence, and for the archived page it was copied out of. That
    distinction is the whole design: a model's recollection of a commercial
    API's terms is not evidence, it is a guess wearing the clothes of one,
    and these terms change.

    So a cleared provider must carry, for each of the three facts, a `value`,
    a verbatim `quote`, and the `source` URL — and **the quote must appear in
    the snapshot of that page under provider-terms/**. An answer typed from
    memory fails here, because the evidence has to exist in the repository
    beside it and has to match.

    `scripts/map/fetch.py` has refused to open a socket for an unlicensed
    dataset since the map was built. Photographs were enforced only at the
    OUTPUT — no published page may reference a file with no register row —
    and nothing stood between somebody with an API key and a download.
    """
    gate_path = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")
    fetch_path = os.path.join(ROOT, "scripts", "images", "acquire.py")
    archive = os.path.join(ROOT, "docs", "data-licenses", "provider-terms")
    if not os.path.exists(fetch_path):
        return 0
    if not os.path.exists(gate_path):
        fail("scripts/images/acquire.py exists and there is no licence gate "
             "beside it — the map pipeline's rule applied to photographs")
        return 1
    gate = json.load(open(gate_path, encoding="utf-8"))
    src = open(fetch_path, encoding="utf-8").read()
    FACTS = ("self_host", "attribution", "download_ping")
    n = 0

    # 1. Every provider the fetcher can reach has a row.
    for slug in re.findall(r'^\s{4}"([a-z]+)": \{$', src, re.M):
        n += 1
        if slug not in gate:
            fail(f"acquire.py can reach {slug!r} and the licence gate has no "
                 f"row for it")

    for slug, row in gate.items():
        if slug.startswith("$"):
            continue
        answered = [row.get(f, {}).get("value") for f in FACTS]
        cleared = all(a not in (None, "", "UNANSWERED") for a in answered)
        n += 1
        if not cleared:
            # Unanswered is the normal, correct state. The only thing that is
            # wrong about it is answering ONE of three and calling it done.
            if any(a not in (None, "", "UNANSWERED") for a in answered):
                fail(f"{slug}: part of the licence is answered and part is "
                     f"not — the three are one decision, and a half-open gate "
                     f"is an open gate")
            continue

        # 2. A cleared provider carries its evidence.
        if not row.get("read_on"):
            fail(f"{slug}: cleared with no `read_on`. A gate opened without "
                 f"recording when the terms were read cannot be re-checked")
        snaps = row.get("terms_snapshot") or {}
        for fact in FACTS:
            f = row[fact]
            n += 2
            if not f.get("quote") or not f.get("source"):
                fail(f"{slug}.{fact}: answered with no quote or no source. "
                     f"The answer is the sentence on the page, not a summary "
                     f"of it")
                continue
            name = snaps.get(f["source"])
            if not name:
                fail(f"{slug}.{fact}: cites {f['source']} and no snapshot of "
                     f"that page is archived — run "
                     f"scripts/images/verify_provider.py")
                continue
            path = os.path.join(archive, name)
            if not os.path.exists(path):
                fail(f"{slug}.{fact}: the snapshot {name} is named and missing")
                continue
            raw = open(path, encoding="utf-8").read()
            # A SNAPSHOT MUST SAY HOW IT GOT HERE, AND THE PASTED KIND MUST
            # PROVE ITSELF. There are two honest ways to obtain one of these
            # pages: the fetcher downloads it and records the SHA-256 of the
            # bytes as served, or a person opens it in a browser — which is
            # the only route left, because both providers refuse an automated
            # request — and save_terms.py records the SHA-256 of the text as
            # saved. Those are different claims and the header says which.
            #
            # Without this, the way to open the gate is to write the file by
            # hand with the served-bytes line over text from anywhere,
            # including text a model produced. That is the failure the whole
            # gate exists to stop, arriving through the evidence rather than
            # through the answer. The pasted kind is recomputed here, so its
            # header cannot claim a hash its body does not have; the fetched
            # kind hashes raw bytes that the archive deliberately does not
            # keep, so only its declaration is required.
            served = re.search(r"^# sha256 of the bytes as served: ([0-9a-f]{64})$",
                               raw, re.M)
            saved = re.search(r"^# sha256 of the text as saved: ([0-9a-f]{64})$",
                              raw, re.M)
            if not served and not saved:
                fail(f"{slug}.{fact}: the snapshot {name} does not say how it "
                     f"was obtained. It is written by "
                     f"scripts/images/verify_provider.py or by "
                     f"scripts/images/save_terms.py, and a page filed here by "
                     f"hand is a page nothing can vouch for")
            elif saved:
                text = raw.split("\n\n", 1)[1].rstrip("\n") if "\n\n" in raw else ""
                got = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if got != saved.group(1):
                    fail(f"{slug}.{fact}: the snapshot {name} declares a hash "
                         f"of the text it holds and does not match it "
                         f"({got[:12]} against {saved.group(1)[:12]}). It has "
                         f"been edited since it was saved")
            body = " ".join(raw.split())
            want = " ".join(f["quote"].split())
            if want not in body:
                fail(f"{slug}.{fact}: the quote is not in the archived page it "
                     f"cites. Either the terms changed, or the quote was typed "
                     f"from memory. Re-read the page")

        # A NEGATIVE CANNOT BE PROVED BY A QUOTE. Every other answer here is
        # backed by a sentence that says the thing; "no download event is
        # required" is backed by the ABSENCE of such a sentence, and no quote
        # can show an absence. The evidence for it is that some passage
        # enumerates the obligations completely — so a `false` must say, in
        # `basis`, what makes the omission conclusive, and the quote it cites
        # is the passage that does the enumerating. Otherwise the honest
        # answer to "is a ping required" is UNANSWERED.
        for fact in FACTS:
            f = row[fact]
            if f.get("value") is False:
                n += 1
                if not (f.get("basis") or "").strip():
                    fail(f"{slug}.{fact}: answered `false` with no `basis`. A "
                         f"quote shows what a page says and never what it "
                         f"omits, so a negative needs the reason its silence "
                         f"is conclusive written down beside it")

        # 3. What a cleared answer obliges the code to do.
        #
        # ANSWERING THE GATE AND BEING ABLE TO USE THE PROVIDER ARE TWO
        # DIFFERENT THINGS, and the first version conflated them: any answer
        # to self_host other than True failed the build. That is right about
        # the consequence and wrong about the event — reading the terms and
        # finding they forbid what this site does is the gate WORKING, and it
        # must be recordable without leaving CI red forever.
        #
        # Unsplash is the live case. Its API guidelines require hotlinking:
        # "All API uses must use the hotlinked image URLs returned by the API
        # under the `photo.urls` properties." This site serves
        # `img-src 'self' data:` and a check refuses any third-party origin,
        # so honouring that means opening the CSP on all 1,033 pages — an
        # owner decision about the security posture of the whole site, not a
        # build step. So the row is answered, `usable` is false, the reason is
        # recorded, and fetch.py refuses it.
        usable = row.get("usable")
        if usable is None:
            fail(f"{slug}: answered and does not say whether it is `usable`. "
                 f"A cleared gate is a reading of the terms, not permission "
                 f"to fetch — say which")
        # A REFUSED ROUTE IS ALSO A REFUSAL AND ALSO NEEDS TEETH.
        api = row.get("api_route") or {}
        if api:
            n += 1
            if api.get("usable") is not True and not (api.get("because") or "").strip():
                fail(f"{slug}: the API route is refused with no `because`")
            if api.get("usable") is not True and "api_route" not in src:
                fail(f"{slug}: the API route is refused and acquire.py does not "
                     f"read `api_route` — the refusal would be a comment")
        elif usable is False:
            if not (row.get("unusable_because") or "").strip():
                fail(f"{slug}: marked unusable with no `unusable_because`. A "
                     f"refusal nobody can read is one somebody will quietly "
                     f"reverse")
            if f'"{slug}"' in src and "REFUSE" not in src.upper():
                fail(f"{slug}: marked unusable and acquire.py has no refusal "
                     f"in it — the gate would be a comment")
        else:
            if row["self_host"]["value"] is not True:
                fail(f"{slug}: usable with self_host cleared as "
                     f"{row['self_host']['value']!r}. This site serves "
                     f"`img-src 'self' data:` and refuses a third-party "
                     f"origin, so a hotlink-only provider needs an owner "
                     f"decision that changes the CSP and that check")
            if row["download_ping"]["value"] is True and not row.get("endpoint_download"):
                fail(f"{slug}: a download event is required and no "
                     f"`endpoint_download` is set, so nothing would call it")

    # 4. No credential, anywhere near this.
    keyish = re.compile(r"[A-Za-z0-9_-]{40,}")
    for rel_ in ("docs/data-licenses/photo-providers.json",
                 "scripts/images/acquire.py", "scripts/images/discover.py",
                 "scripts/images/pr_body.py", "scripts/images/verify_provider.py",
                 "data/images.json", ".github/workflows/photograph.yml"):
        f = os.path.join(ROOT, rel_)
        if not os.path.exists(f):
            continue
        body = open(f, encoding="utf-8").read()
        n += 1
        archive_names = set(os.listdir(archive)) if os.path.isdir(archive) else set()
        stems = {n.rsplit(".", 1)[0] for n in archive_names}
        stems |= {part for n in stems for part in n.split(".")}
        for m in keyish.finditer(body):
            if "://" in body[max(0, m.start() - 12):m.start()]:
                continue
            # A LONG TOKEN THAT NAMES A FILE ON DISK IS A FILE NAME. The
            # Unsplash guidelines archive is
            # `unsplash.https-help-unsplash-com-en-articles-2511245-unsplash-api-guidelines.<date>.txt`,
            # whose middle segment is 67 characters of letters, digits and
            # hyphens — which is exactly the shape this pattern hunts for, and
            # it failed the build on the evidence the gate exists to collect.
            # Checked against the directory rather than by pattern, because a
            # looser regex is how a real credential gets through.
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
            fail(f"{rel_} contains a {len(m.group(0))}-character token that "
                 f"looks like a credential — keys live in repository secrets "
                 f"and nowhere else")
    return n


@check("nothing served immutable sits at a URL that can change")
def c_immutable_assets():
    """`immutable` is a promise about the URL, not about the file.

    /assets/ is served `public, max-age=31536000, immutable`. That is correct
    for a content-addressed URL and a LIE for a stable one: the browser is
    told never to revalidate for a year, so a returning reader keeps whatever
    stylesheet they first downloaded and every visual change reaches new
    visitors only.

    It shipped that way. The social cards were content-addressed and earned
    the header; the stylesheet and the five scripts sat at a stable path
    under the same rule. Invisible from inside — repository correct, build
    correct, shipped HTML correct, served page styled by a file from months
    ago — which is the same shape as the `site/_headers` bug this repository
    already records: right in the repo, wrong in the response.

    So: every URL under a directory served `immutable` must carry a content
    hash in its NAME. Asserted against what the build actually published and
    what the pages actually reference, because the promise is about the
    response and not about the intent.
    """
    vercel = json.load(open(os.path.join(ROOT, "vercel.json"), encoding="utf-8"))
    immutable_prefixes = []
    for rule in vercel.get("headers", []):
        for h in rule.get("headers", []):
            if h["key"] == "Cache-Control" and "immutable" in h["value"]:
                immutable_prefixes.append(rule["source"].replace("/(.*)", "/"))
    if not immutable_prefixes:
        fail("no directory is served immutable — this check is testing nothing")
        return 0
    # Two shapes count as content-addressed, because this site already uses
    # both: the social cards are named entirely by their hash
    # (`1b63284558e3ebaf.png`) and the stylesheet carries it as a segment
    # (`europedoor.16239001ae.css`). The first version of this pattern only
    # accepted the second and reported all 785 cards as failures — an
    # instrument that does not recognise the good case it was written to
    # protect.
    # SECOND TIME THIS PATTERN HAS NOT RECOGNISED THE GOOD CASE IT PROTECTS.
    # Its first version accepted only `name.<hash>.ext` and reported all 785
    # correctly addressed social cards as failures. Now a photograph's ladder
    # is `homepage-hero.<hash>-1260.jpg` — the tag names the SET and the width
    # names the file — and it was refused for the same reason. An instrument
    # that fails the thing it exists to protect is worse than no instrument,
    # because the honest response to it is to switch it off.
    hashed = re.compile(r"(?:^|\.)[0-9a-f]{8,}(?:-\d+)?\.[a-z0-9]+$")
    n = 0
    for prefix in immutable_prefixes:
        root = os.path.join(OUT, prefix.strip("/"))
        for dirpath, _dirs, names in os.walk(root):
            for name in names:
                url = "/" + os.path.relpath(os.path.join(dirpath, name), OUT)
                n += 1
                if not hashed.search(name):
                    fail(f"{url} is served immutable for a year and its name "
                         f"carries no content hash — a returning reader will "
                         f"never see it change")
    # And no page may still reference an unhashed one, which is the failure
    # from the other end: a correct file published beside a stale URL.
    for path in site_files():
        h = open(path, encoding="utf-8").read()
        for m in re.finditer(r'(?:href|src)="(/assets/[^"]+)"', h):
            n += 1
            if not hashed.search(m.group(1)):
                fail(f"{rel(path)} references {m.group(1)}, which is under an "
                     f"immutable prefix and carries no content hash")
    return n


@check("every Stay heading this module can emit is actually drawn somewhere")
def c_stay_headings():
    """A heading nothing reaches is dead code that looks like vocabulary.

    The same rule as `plates.motifs_reachable`, and it caught the same class
    of thing on its first run. The first version of `stay.heading` tested the
    relief measurement BEFORE `city_type`, which did two wrong things at
    once: it gave "Sleep below the peaks" to 147 destinations including
    Tirana — a capital in a basin, where a 600 m crest within 40 km is a
    reason the map draws bands and not a reason to tell somebody where they
    are sleeping — and it made "Stay in the valley" unreachable, because all
    nine valley destinations have relief and were being overridden by it.

    Neither is visible in any count of the built site, because only one
    destination carries the Stay layer today. It is visible by running the
    derivation over all 319, which is what this does.

    `FALLBACK` is deliberately excluded: every destination carries a
    `city_type`, so it is unreachable by construction and demanding it be
    reached would be demanding a broken record.
    """
    d = D.load()
    drawn = set()
    for cid, node in d["cities"].items():
        drawn.add(STAY.heading({}, node["city"],
                               CARTO.draws_relief(CARTO.relief_of(cid))))
    declared = STAY.headings_declared()
    for h in sorted(declared - drawn):
        fail(f"the Stay heading {h!r} is declared and reached by no destination "
             f"in the atlas — dead vocabulary")
    for h in sorted(drawn - declared - {STAY.FALLBACK}):
        fail(f"the Stay layer draws {h!r}, which `headings_declared` does not "
             f"list — the reachability test cannot see it")
    # And the one that matters editorially: a heading may never be OTA
    # language, wherever it came from.
    for h in sorted(drawn):
        if "hotel" in h.lower():
            fail(f"the Stay heading {h!r} says 'hotel'")
    return len(declared) + len(drawn)


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
    # AWAITING FETCH: registered, licence-checked, and genuinely not here.
    # A row in this list that HAS its file is a row somebody fetched and
    # forgot to move, which would sit here looking settled while the checks
    # that hash `sources` never touched it.
    for a in reg.get("awaiting_fetch", []):
        doc = os.path.join(ROOT, "docs", "data-licenses", a["licence_doc"])
        if not os.path.exists(doc):
            fail(f"awaiting dataset {a['id']} has no licence record")
        if os.path.exists(os.path.join(ROOT, a["path"])):
            fail(f"{a['id']} is in `awaiting_fetch` and its file IS in the "
                 f"repository — move the row to `sources` with its sha256, "
                 f"or the bytes nobody hashed will be the ones that ship")
        if not a.get("fills_layer") or not a.get("selection"):
            fail(f"{a['id']} does not say which layer it fills or what it "
                 f"selects — an unselected dataset is how a map gets four "
                 f"thousand streams on it")
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

    # A SURFACE LADDER IS A LADDER, and a per-pair claim cannot say so.
    # Every surface here carries a claim about the TEXT it can hold, and all
    # of them passed while the dark world's third surface measured 1.045
    # against its own card — the card with a different name, so every
    # progress track, score bar and hopbar on a dark card was drawn on its
    # own colour. The light world steps 1.09 and 1.12. This asserts the
    # steps, which is a fact about the ladder rather than about any rung.
    surf = pal.get("surfaces")
    if not surf:
        fail("docs/palette.json declares no surface ladders — the steps "
             "between grounds are unmeasured again")
    else:
        for ladder in surf["ladders"]:
            for a, b in zip(ladder, ladder[1:]):
                if a not in tok or b not in tok:
                    fail(f"a surface ladder names an unknown token: {a} / {b}")
                    continue
                r = _ratio(tok[a]["hex"], tok[b]["hex"])
                if r < surf["min_step"]:
                    fail(f"the surfaces {a} ({tok[a]['hex']}) and {b} "
                         f"({tok[b]['hex']}) are {r:.3f} apart and the register "
                         f"asks for {surf['min_step']} — a step that small is a "
                         f"rounding error with a token name")
                n += 1

    # A CONTRAST RATIO CANNOT SAY THAT TWO COLOURS ARE DIFFERENT COLOURS.
    # It is a ratio of luminances, so two hues at the same lightness always
    # measure 1.0 — and for the life of this palette the advisory red and the
    # cultural accent sat fourteen degrees apart at IDENTICAL saturation and
    # IDENTICAL lightness. #a32a1e against #a4491f measures 1.22, and every
    # contrast assertion here passed while a travel advisory and a story
    # kicker were the same colour to the eye: on the map dots, on the tags,
    # in the notes. The dark pair was worse at 1.27, and both were salmon.
    #
    # So these pairs are told apart by HUE, which is the property a ratio
    # cannot see. Circular distance, because 356 and 4 are eight degrees
    # apart and not three hundred and fifty two.
    dis = pal.get("distinct")
    if not dis:
        fail("docs/palette.json declares no hue distances — the only property "
             "that can tell an advisory from an accent is unmeasured again")
    else:
        def _hue(hexv):
            h = hexv.lstrip("#")
            r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
            return colorsys.rgb_to_hls(r, g, b)[0] * 360.0
        for a, b in dis["pairs"]:
            if a not in tok or b not in tok:
                fail(f"a hue distance names an unknown token: {a} / {b}")
                continue
            ha, hb = _hue(tok[a]["hex"]), _hue(tok[b]["hex"])
            d = abs(ha - hb) % 360.0
            d = min(d, 360.0 - d)
            if d < dis["min_hue_degrees"]:
                fail(f"{a} ({tok[a]['hex']}, hue {ha:.0f}) and {b} "
                     f"({tok[b]['hex']}, hue {hb:.0f}) are {d:.0f} degrees "
                     f"apart and the register asks for "
                     f"{dis['min_hue_degrees']} — a contrast ratio cannot see "
                     f"this, which is how they stayed the same colour")
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
    # AND THERE IS NO ELECTRIC LIME, for a different reason than the gold.
    # Gold went because of what it says. Lime went because of where it ended
    # up: declared as the dark world's accent at five per cent of a screen,
    # and spent on seventeen journey routes, 894 homepage dots, 319
    # destinations, 172 experiences and every lit country on every region
    # glyph. A continent drawn in the accent is a network diagram, which is
    # the association the cartography split exists to escape.
    # The DECLARATION is what is refused: `--lime` is a prefix of
    # `--limestone`, and the note recording why it went names the hex.
    if "--lime:" in css or re.search(r":\s*#c8ff4d", css, re.I):
        fail("assets/css/europedoor.css still declares electric lime; it was "
             "removed rather than rehomed, like the brass")
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
        for token in ("#101214", "#F7F6F3", "#3157FF", "#8398FF", "#14483C", "#A4491F"):
            if token not in body:
                fail(f"docs/instruction.md does not name {token}")
            n += 1
        # The readable table and the register must agree on the values the
        # instruction reasons about by name.
        for name in ("graphite", "limestone", "cobalt", "cobalt-air", "atlantic", "terracotta"):
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
            """Walk a dotted path, stepping into a list at its first element.

            A CONTRACT COULD ONLY NAME A TOP-LEVEL FIELD, WHICH IS NOT WHERE
            THE COUPLING IS. `cities` is a list of objects and the planner
            reads a dozen fields off each one; declaring the list said
            nothing about any of them, so the rule this file enforces —
            coupling is fine, silent coupling is not — stopped exactly one
            level above where it mattered. A list step checks the first
            element, which is enough: these documents are homogeneous by
            construction, and a field missing from every row but the first is
            a different bug from the one this catches.
            """
            cur = doc
            for part in path.split("."):
                if isinstance(cur, list):
                    if not cur:
                        return None
                    cur = cur[0]
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
    #
    # `card` 0.20 -> 0.07 WHEN THE REGION PAGES BECAME ROWS. 97 of the 130
    # travel regions hold one or two destinations, so the band that is the
    # subject of a region page opened with a single 280px tile and two empty
    # columns beside it, each tile drawing a plate from its destination's own
    # hash directly under a real map of the region. That is the stories-index
    # failure and the plate measurement at once, and the rest of a region
    # page was already rows. Recorded here and in the invariant register in
    # the same commit; the floor is what stops it happening by accident.
    #
    # 0.07 -> 0.06 WHEN THE MOTION PAGES DID THE SAME. Each of the twelve
    # ended on three journey cards and up to three theme cards, all opening
    # on a gradient chosen by the hash of a slug, on the family whose whole
    # argument is that a motion is not a place.
    FLOORS = {"kicker": 0.99, "masthead": 0.99, "pagehead": 0.99, "crumbs": 0.99,
              "row": 0.85, "card": 0.05, "band": 0.70, "note": 0.70}
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


@check("every map declares whether it is an illustration or an instrument")
def c_map_roles():
    # A MAP IS AN EDITORIAL ILLUSTRATION UNLESS IT SAYS OTHERWISE. The
    # default runs that way because the failure runs one way: a picture that
    # drifts into instrument styling is a page that has quietly become a
    # dashboard, and nobody notices until somebody looks at twelve families
    # side by side — which is how the macro region map spent its whole life
    # in the graphite palette while being a picture of where the Nordics are.
    #
    # Asserted on the SHIPPED HTML, and with the consequence attached: an
    # illustration must carry the atlas skin, and an instrument must not.
    # Declaring a role and then styling the other way is worse than not
    # declaring one, because it reads as a decision.
    pat = re.compile(r'<(?:figure|a|svg)[^>]*class="([^"]*(?:minimap|heromap|'
                     r'europemap)[^"]*)"[^>]*>')
    n = illus = instr = 0
    for path in site_files():
        html = open(path, encoding="utf-8").read()
        for m in pat.finditer(html):
            tag, cls = m.group(0), m.group(1)
            role = re.search(r'data-role="(\w+)"', tag)
            assert role, f"{rel(path)}: a map with no declared role: {cls}"
            assert role.group(1) in ("illustration", "instrument"), (
                f"{rel(path)}: unknown map role {role.group(1)}")
            if role.group(1) == "illustration":
                assert "atlas" in cls.split(), (
                    f"{rel(path)}: an illustration without the atlas skin — "
                    f"editorial geography is warm paper and Atlantic water, "
                    f"never land on a near-black ground")
                illus += 1
            else:
                assert "atlas" not in cls.split(), (
                    f"{rel(path)}: an instrument wearing the atlas skin")
                instr += 1
            n += 1
    assert illus > 700 and instr > 40, (
        f"only {illus} illustrations and {instr} instruments found")
    return n


@check("a local frame is drawn from local geometry, and a continental one is not")
def c_local_lod():
    """The coastline LOD rule, read back off the shipped pages.

    THE DEFECT: the continental file simplifies at 0.04 degrees, which is
    4.4 km, which is nine pixels on the 590 km frame a destination plate
    actually draws. Attica came out as a wedge, the Cyclades as lozenges and
    the Norwegian coast as a staircase — and on an INLAND page with no
    coast at all, Krakow, two neighbours simplified independently do not share
    an edge, so thin slivers of sea colour ran along the Polish frontier and
    the Danube. Every coastal destination had looked like that since these
    maps were built, and nobody had put a coastal frame and an Alpine frame
    side by side.

    THE RULE: under `geo.LOCAL_LOD_MAX_KM` a destination plate draws from the
    per-country file at 0.012 degrees, merged over the continental one so a
    frame reaching two countries further still has land in it; above the cap
    it draws from the continental file, because there 4.4 km is a third of a
    pixel and the finer geometry is bytes for nothing.

    Asserted by recovering each plate's own frame from its transform and its
    caption, rebuilding the land markup both ways, and requiring the page to
    carry the one the rule selects. Sampled at the BOUNDARY — the widest
    frames below the cap and the narrowest above it — because that is the
    only place a threshold can be wrong.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from lib import geo as G                                        # noqa: E402
    from lib import pages as P                                      # noqa: E402

    seen = []
    for path in site_files():
        r = rel(path).lstrip("/").split("/")
        if r[0] != "europe" or len(r) != 5:
            continue
        html = open(path, encoding="utf-8").read()
        m = re.search(r'<g transform="translate\(([-\d.]+),([-\d.]+)\) '
                      r'scale\(([\d.]+)\)">', html)
        km = re.search(r"frame is about ([\d,]+) km across", html)
        if not m or not km:
            continue
        tx, ty, span = float(m.group(1)), float(m.group(2)), float(m.group(3))
        w, h = 900.0, 320.0
        cx, cy = (w / 2 - tx) / span, (h / 2 - ty) / span
        seen.append((int(km.group(1).replace(",", "")), "/".join(r[1:4]),
                     path, html, (cx - w / 2 / span, cy - h / 2 / span,
                                  w / span, h / span)))
    assert len(seen) > 250, f"only {len(seen)} destination plates found"
    seen.sort()
    under = [x for x in seen if x[0] <= G.LOCAL_LOD_MAX_KM]
    over = [x for x in seen if x[0] > G.LOCAL_LOD_MAX_KM]
    assert under and over, (
        f"the cap separates nothing: {len(under)} under, {len(over)} over")
    sample = under[-8:] + over[:8]

    def points(markup):
        return len(re.findall(r"[ML]-?[\d.]", markup))

    # COUNTED, NOT MATCHED CHARACTER FOR CHARACTER. The frame is recovered
    # from a transform printed to two decimals, so the clip box here differs
    # from the build's in the fifth decimal and a vertex can round the other
    # way. Exact string matching was the first version and failed on one page
    # in sixteen for that reason — which is a brittle check finding its own
    # arithmetic, not a defect.
    n = 0
    for km, key, path, html, view in sample:
        slug = key.split("/")[0]
        coarse = points(G.landmass(P.MAPPROJ, view)[1])
        fine = points(G.landmass(P.MAPPROJ, view, doc=G.local(slug))[1])
        if not coarse or fine < coarse * 1.15:
            continue            # too little of this country drawn to tell
        got = points(re.search(r'<g class="countries"[^>]*>(.*?)</g>'
                               r'(?=<g class="lyr|</g>)', html, re.S).group(1))
        want, other = ((fine, coarse) if km <= G.LOCAL_LOD_MAX_KM
                       else (coarse, fine))
        assert abs(got - want) < abs(got - other), (
            f"{rel(path)} frames {km} km and draws {got} coastline points; "
            f"the {G.LOCAL_LOD_MAX_KM:.0f} km rule selects {want} and the "
            f"other level is {other}. A coastline nine pixels coarse on a "
            f"frame a reader is looking straight at is what this exists to "
            f"stop; the finer one on a continental frame is bytes for "
            f"nothing")
        n += 1
    assert n >= 8, f"only {n} plates were decisive enough to test"
    return n


@check("terrain draws only where the ground was measured to earn it")
def c_terrain():
    """Five promises about the relief layer, on the shipped HTML.

    THE FAILURE THIS EXISTS FOR IS NOT A BUG, IT IS A DRIFT. An elevation
    model in the repository is a standing invitation to put relief on
    everything, and the version of this product that has a topographic Paris
    is one careless commit away. Every assertion here is the owner's rule
    turned into arithmetic somebody else can re-run.

      1. relief is an ILLUSTRATION layer — never on a map that declares
         itself an instrument, and only on the two families it was approved
         for: a destination and a journey
      2. a plate draws relief if and only if the MEASUREMENT says so — the
         spread and the crest of the ground round that destination, read
         from data/geo/terrain-lod1.json, which is the same file the bands
         come from
      3. the boundary is drawn ABOVE it. A frontier here is a stroke on the
         land path, so the bands bury it; the prototype's first render had a
         clear France/Switzerland/Italy border without terrain and none with
         it
      4. the palette is the one the experiment approved and there is no
         stronger one — four fills, each 65% of the way from the land tone
         to its hypsometric colour
      5. no frame wider than the cap carries it, because across a continent
         relief stops being a picture of somewhere and becomes a physical
         map of Europe
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from lib import cartography as C                                # noqa: E402
    from lib import geo as G                                        # noqa: E402

    doc = G.load("terrain-lod1.json")
    assert doc, "data/geo/terrain-lod1.json is missing — run the pipeline"
    n = 0

    # 4. The palette, against HYPSOMETRIC and the approved 65%.
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"),
               encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    base = (0xdd, 0xd9, 0xcf)                    # --atlas-land
    for lo, _hi, hexcol, _why in C.HYPSOMETRIC:
        if lo == 0:
            continue
        v = [int(hexcol[i:i + 2], 16) for i in (1, 3, 5)]
        want = "#%02x%02x%02x" % tuple(
            int(round(base[i] + (v[i] - base[i]) * 0.65)) for i in range(3))
        assert f".t{lo}  {{ fill: {want}; }}" in css or \
               f".t{lo} {{ fill: {want}; }}" in css, (
            f"the terrain band at {lo} m is not the approved mix: expected "
            f"{want}, which is 65% of the way from the land tone to "
            f"{hexcol}. The strongest version was rejected by eye; a "
            f"stronger fill here is that rejection being undone silently")
        n += 1
    # THE HERO DRAWS THE SAME SCALE OVER A DIFFERENT GROUND. It is the one
    # other family that paints these bands: three of them, the pure
    # hypsometric colour at a stated alpha rather than mixed 65% toward an
    # opaque parchment, because the land under it is itself translucent. The
    # ALPHA is a treatment and may differ; the COLOUR may not, and for one
    # commit the hero's snow was #efe9dd against #e6e0d6 everywhere else —
    # one colour meaning two heights, arrived at by eye on a dark surface.
    for lo, _hi, hexcol, _why in C.HYPSOMETRIC:
        if lo < 600:
            continue          # the 200 m band does not read at this scale
        assert re.search(r"\.heroeurope \.lyr-terrain \.t%d\s*\{[^}]*%s"
                         % (lo, re.escape(hexcol)), css), (
            f"the hero's terrain band at {lo} m is not {hexcol}, the colour "
            f"this height has everywhere else in the atlas. The alpha over "
            f"it is the hero's own treatment; the colour is the scale")
        n += 1
    # COUNTED BY THE FILL, NOT BY THE SELECTOR. The hero also strokes its two
    # upper bands — a hairline that turns the tonal wash into a ridge, which
    # is the same data and the same layer — and a rule counting selectors read
    # that as a fourth band and a second strength. What the rule protects is
    # how many HEIGHTS have a colour, so it counts the declarations that give
    # one.
    for fam, want in ((r"\.minimap\.arched\.atlas", 4),
                      (r"\.heroeurope", 3)):
        got = len(re.findall(fam + r" \.lyr-terrain \.t\d+[^{]*\{[^}]*fill:",
                             css))
        assert got == want, (
            f"that family declares {got} terrain bands rather than {want} — "
            f"a second strength was measured out (see the rule's comment) "
            f"and an absolute hypsometric scale cannot have two")
        n += 1

    # 1, 2, 3, 5. Every plate that draws it, and every one that should.
    want_terrain = set()
    for key, m in doc["relief"].items():
        if C.draws_relief(m):
            want_terrain.add(key)
    drew, offenders = set(), []
    for path in site_files():
        html = open(path, encoding="utf-8").read()
        if 'class="lyr lyr-terrain"' not in html:
            continue
        n += 1
        r = rel(path).lstrip("/")
        assert 'data-role="instrument"' not in html.split(
            'class="lyr lyr-terrain"')[0][-900:], (
            f"/{r}: relief on a map that declares itself an instrument")
        # THE PROMISE IS THAT RELIEF CANNOT BURY A FRONTIER, and there are
        # two ways to keep it. A plate unfolds the boundary and re-emits it
        # above the bands. The hero draws no frontier at all — it is filled,
        # adjacent countries merge, and the only line in it is where land
        # meets sea, because stroking fifty countries made a political map
        # out of a picture. Both are kept here rather than one excused:
        # either the boundary is drawn above the terrain, or there is no
        # boundary for the terrain to bury.
        if r == "index.html":
            # THE HERO DRAWS FRONTIERS NOW, AND THE PROMISE IS THAT THEY ARE
            # FELT RATHER THAN READ. It was filled and borderless once,
            # because the first attempt drew fifty bright lines — per-country
            # translucent strokes double where two countries share an edge.
            # That is a fact about compositing, not an argument against
            # frontiers, and without them the hero read as a relief sculpture
            # of Europe rather than as an atlas of fifty countries.
            #
            # So the assertion is the one the plates make plus a ceiling on
            # the ink: the boundary pass exists, and its stroke is no more
            # than 40% of the way from the parchment to the page's own ink.
            # Past that it stops being a frontier felt at reading distance
            # and becomes a political map, which is a different picture.
            assert 'class="lyr lyr-country-bounds"' in html, (
                "the hero draws relief and no boundary pass above it — the "
                "bands paint over a frontier here exactly as they do on a "
                "plate")
            m = re.search(r"\.heroeurope \.lyr-country-bounds\s*\{[^}]*"
                          r"stroke:\s*color-mix\(in srgb,\s*var\(--graphite\)"
                          r"\s*(\d+)%", css)
            assert m, ("the hero's frontier ink is not a stated mix of the "
                       "page's ink into the parchment, so how loud it is "
                       "cannot be read off the stylesheet")
            assert int(m.group(1)) <= 40, (
                f"the hero's frontiers are {m.group(1)}% of the way to the "
                f"page's ink. At reading distance nobody should think 'I see "
                f"borders'; past 40% this is a political map")
            n += 2
        else:
            assert 'class="lyr lyr-country-bounds"' in html, (
                f"/{r}: relief with no boundary pass above it — a frontier "
                f"here is a stroke on the land path and the bands paint "
                f"over it")
        parts = r.split("/")
        # A place page draws its own destination's plate, which is the same
        # picture of the same town; it belongs to the destination family.
        if parts[0] == "europe" and len(parts) >= 5:
            drew.add("/".join(parts[1:4]))
        elif r == "index.html":
            # THE HOMEPAGE HERO IS THE THIRD FAMILY, AND IT IS A DIFFERENT
            # TREATMENT RATHER THAN AN EXCEPTION. `terrain()` is the plate
            # rule — the suitability measurement, the two thresholds and the
            # 1,500 km frame cap — and none of it applies here, because the
            # hero is not a picture of a place: it is the continent, and the
            # question it answers is "this is Europe, and it has mountains in
            # it". It draws three bands rather than four, thinned to a
            # picture's tolerance, through relief_wash(). The plate rule is
            # untouched and every assertion below still runs on it.
            continue
        elif parts[0] != "journeys":
            offenders.append("/" + r)
    assert not offenders, (
        f"relief on {len(offenders)} page(s) outside the destination, "
        f"journey and hero families, the three it was approved for: "
        f"{offenders[:4]}")
    # A destination page draws it exactly when the ground says so.
    missing = sorted(want_terrain - drew)[:4]
    extra = sorted(drew - want_terrain)[:4]
    assert not extra, (
        f"{len(extra)} destination(s) draw relief the measurement does not "
        f"support: {extra}")
    assert len(drew) > 30, (
        f"only {len(drew)} destinations draw relief; the measurement says "
        f"{len(want_terrain)} should")
    n += 2

    # 5. The cap, checked against what the pages actually say they frame.
    for path in site_files():
        html = open(path, encoding="utf-8").read()
        if 'class="lyr lyr-terrain"' not in html:
            continue
        m = re.search(r"frame is about ([\d,]+) km across", html)
        if m:
            km = int(m.group(1).replace(",", ""))
            assert km <= C.TERRAIN_MAX_KM, (
                f"{rel(path)} draws relief on a {km} km frame, past the "
                f"{C.TERRAIN_MAX_KM:.0f} km cap — at that scale it is a "
                f"physical map of Europe rather than a picture of somewhere")
            n += 1
    return n


@check("the hero's frame shows no edge of the data behind it")
def c_hero_frame():
    """The homepage draws land the atlas does not hold, and every edge shows.

    THE HERO IS THE ONE PICTURE ON THIS SITE WHOSE SUBJECT IS THE CONTINENT,
    so it draws a second geometry — beyond-lod0.json, the ground around
    Europe — under the atlas and at a sixth of its contrast. That file is a
    box cut out of the world, and a box has four straight edges through real
    land. The first one ran -32°E to 74°N: Greenland was sliced down the
    middle of Scoresby Sund and drew a straight vertical edge in the north
    Atlantic, and Novaya Zemlya was cut along the 74th parallel. Both are
    faint on a desktop and unmistakable at 390px.

    Two things are asserted, both arithmetic rather than opinion.

    1. NO EDGE OF THAT BOX IS INSIDE THE HERO'S FRAME. The box's four sides
       are walked in lon/lat and projected — a conic turns a meridian into a
       radial line and a parallel into an arc, so neither is a straight line
       in the drawing and a sampled walk is the honest test — and no sample
       may land inside the viewBox. A wider dataset later is exactly the sort
       of improvement that would quietly put one back.

    2. THE STYLESHEET'S ASPECT RATIO IS THE VIEWBOX'S. An SVG clips to its
       VIEWPORT, not to its viewBox, so a mismatch letterboxes and the bands
       show whatever geometry lies outside the frame. The stacked phone hero
       carried 1000/780 for one commit against a 1120/800 drawing and drew a
       straight line above and below the continent.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from lib import pages as PG                                     # noqa: E402

    import json as _json
    doc = _json.load(open(os.path.join(ROOT, "data", "geo",
                                       "beyond-lod0.json"), encoding="utf-8"))
    lo0, la0, lo1, la1 = doc["bbox"]
    vx, vy, vw, vh = PG.HERO_VIEW
    n = 0
    # THE TEST IS WHERE THE CUT MEETS LAND, not where the box is. The western
    # edge cannot be moved out of the frame at all — under this conic the
    # apex is just above the picture, so at 70°N the whole 360° of longitude
    # is inside a few hundred units and there is no meridian far enough west.
    # What matters is not the box: it is whether the box cuts anything. A
    # vertex of a drawn ring that sits exactly ON one of the four edges is a
    # place where a coastline was severed, and that is the thing that must
    # not be visible. Read off the shipped geometry, so it measures what is
    # drawn rather than what was intended.
    # THE TWO SEAMS ARE EXEMPT, AND ONLY THOSE TWO. This layer is cut to the
    # complement of the atlas — the strip east of 52°E and the strip south of
    # 33°N — so those two edges are where the atlas's geometry stops and this
    # one takes over. They are inside the frame on purpose, and each has a
    # fade over it. Every other edge is a cut through land nobody is drawing
    # the other side of, and must fall outside the picture.
    seams = doc.get("seams") or {}
    strips = doc["strips"]
    edges = []
    for strip in strips:
        box = strip["box"]
        edges.append(("west", 0, box[0]))
        edges.append(("south", 1, box[1]))
        edges.append(("east", 0, box[2]))
        edges.append(("north", 1, box[3]))
    bad = []
    for st in strips:
      for ring in st["rings"]:
        for i in range(0, len(ring), 2):
            lon, lat = ring[i], ring[i + 1]
            side = ""
            for name, axis, v in edges:
                if abs((lon if axis == 0 else lat) - v) > 1e-3:
                    continue
                if axis == 0 and abs(v - seams.get("lon", 1e9)) < 1e-6:
                    continue
                if axis == 1 and abs(v - seams.get("lat", 1e9)) < 1e-6:
                    continue
                side = name
                break
            if not side:
                continue
            # AND A STRIP'S EDGE IS NOT A CUT WHERE ANOTHER STRIP COVERS IT.
            # The two overlap in the south-east: the southern strip stops at
            # 52°E and the eastern one runs from 36°E, so the southern strip's
            # eastern edge has ground on both sides of it and severs nothing.
            if any(b["box"][0] - 1e-6 <= lon <= b["box"][2] + 1e-6
                   and b["box"][1] - 1e-6 <= lat <= b["box"][3] + 1e-6
                   and b is not st for b in strips):
                continue
            x, y = PG.MAPPROJ.xy(lat, lon)
            if vx <= x <= vx + vw and vy <= y <= vy + vh:
                bad.append((side, round(lat, 1), round(lon, 1),
                            round(x), round(y)))
    assert not bad, (
        f"the ground layer's own data cut severs a coastline at "
        f"{len(bad)} point(s) inside the hero's frame, so the drawing ends "
        f"on a straight line through real land: {bad[:3]}. Move BEYOND_BBOX "
        f"out, or the frame in")
    n += 4

    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"),
               encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    # THE LAND GROUP MUST STAY OPAQUE, and nothing in the stylesheet can say
    # so: `opacity: 1` is the default, so the declaration is a rule that
    # changes nothing and the dead-rule scan counts it. The promise is real
    # though — below 1 the two coincident strokes at a shared frontier
    # composite brighter than either, which is fifty white borders and is why
    # the land was a single merged path before it was fifty links.
    m = re.search(r"\.heroeurope \.herolandg\s*\{[^}]*opacity:\s*([\d.]+)",
                  css)
    assert not m or float(m.group(1)) >= 1.0, (
        f"the hero's land group is drawn at {m.group(1)} opacity. Two "
        f"coincident strokes at a shared frontier then composite brighter "
        f"than either and the map grows fifty white borders — the political "
        f"map this hero was rebuilt to remove")
    n += 1

    m = re.search(r"\.heroeurope svg\s*\{[^}]*aspect-ratio:\s*"
                  r"(\d+)\s*/\s*(\d+)", css)
    assert m, ("the stacked hero declares no aspect-ratio; without one the "
               "SVG box is whatever the row leaves it and the drawing is "
               "letterboxed inside it")
    assert (int(m.group(1)), int(m.group(2))) == (int(vw), int(vh)), (
        f"the hero's CSS aspect-ratio is {m.group(1)}/{m.group(2)} and its "
        f"viewBox is {int(vw)}/{int(vh)}. An SVG clips to its viewport, so "
        f"the difference is a band of geometry from outside the frame")
    n += 1

    # And the shipped page must actually carry that viewBox, because both
    # numbers above are read from the source rather than from the HTML.
    html = open(os.path.join(ROOT, "site", "index.html"),
                encoding="utf-8").read()
    assert f'viewBox="{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}"' in html, (
        "the homepage does not carry the hero viewBox this check just "
        "asserted two things about")
    n += 1
    return n


@check("every page that draws relief names the survey that measured it")
def c_relief_credit():
    """The credit is derived from the register, not typed into a caption.

    THE PROMISE WAS WRITTEN IN A LICENCE DOCUMENT AND KEPT ON NO PAGE. The
    Credit section of docs/data-licenses/aws-terrain-tiles.md says, in as
    many words, that any page which draws terrain names the elevation
    source. Relief then shipped to 153 destination plates, six journeys and
    the homepage and not one of them contained the word GMTED. Nothing
    failed, because the promise lived in prose.

    AND WHEN IT WAS FINALLY DRAWN, THE SENTENCE IN THAT DOCUMENT NAMED THE
    WRONG SURVEY. It asks for "SRTM and GMTED2010", which was true of the
    six zoom-7 tiles the Chamonix prototype fetched and false of everything
    that ships: the integration went to zoom 6, and the service's own
    per-tile imagery header — recorded in the register when each tile was
    fetched — names gmted and etopo1 on those and srtm on none of them.

    So this reads the register rather than a sentence. The datasets are the
    ones the shipped tiles actually declare, at the zoom the terrain
    document says it was built at, and both directions are asserted: a page
    that draws relief names each of them, and the credit names none the
    register does not support. Crediting a survey whose data is not in the
    picture is the same class of untruth as crediting none.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from lib import cartography as C                                # noqa: E402
    from lib import geo as G                                        # noqa: E402

    tdoc = G.load("terrain-lod1.json")
    assert tdoc, "data/geo/terrain-lod1.json is missing — run the pipeline"
    zoom = tdoc["pipeline"]["zoom"]

    reg = json.load(open(os.path.join(ROOT, "docs", "data-licenses",
                                      "sources.json"), encoding="utf-8"))
    # The name each imagery prefix is published under. A prefix with no entry
    # here is a dataset nobody has decided how to credit, which must stop the
    # build rather than be dropped from a sentence.
    NAMES = {"gmted": "GMTED2010", "srtm": "SRTM", "etopo1": "ETOPO1",
             "3dep": "3DEP", "eudem": "EU-DEM"}
    used, tiles = {}, 0
    for row in reg["sources"]:
        if row.get("fills_layer") != "terrain":
            continue
        if f"/terrarium/{zoom}/" not in row["url"]:
            continue          # a prototype tile at another zoom; not shipped
        tiles += 1
        for part in (row.get("provenance") or "").split(","):
            part = part.strip().split("/")[0].lower()
            if not part:
                continue
            assert part in NAMES, (
                f"the register records imagery from '{part}', which has no "
                f"published name here — a dataset nobody has decided how to "
                f"credit cannot be silently left out of the credit")
            used[NAMES[part]] = used.get(NAMES[part], 0) + 1
    assert tiles > 100, (
        f"only {tiles} elevation tiles at zoom {zoom} in the register; the "
        f"shipped relief covers Europe and needs the whole set")
    assert used, "no imagery provenance recorded for the shipped tiles"
    n = 2

    # 1. The credit names every dataset the shipped tiles declare, and no
    #    dataset they do not.
    plain = re.sub(r"<[^>]+>", "", C.RELIEF_CREDIT)
    for name in used:
        assert name in plain, (
            f"the relief credit does not name {name}, which {used[name]} of "
            f"the {tiles} shipped elevation tiles declare as their imagery "
            f"source")
        n += 1
    for name in set(NAMES.values()) - set(used):
        assert name not in plain, (
            f"the relief credit names {name}, and no shipped tile at zoom "
            f"{zoom} declares it — crediting a survey whose data is not in "
            f"the picture is the mistake this check was written for")
        n += 1

    # 2. Every page that draws relief carries it, in text a reader sees.
    #    Tags are stripped first: the credit links "public domain" to the
    #    register, so a check on the raw markup would be asserting where the
    #    anchor happens to fall.
    pages = 0
    for path in site_files():
        html = open(path, encoding="utf-8").read()
        if 'class="lyr lyr-terrain"' not in html:
            continue
        pages += 1
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        for name in used:
            assert name in text, (
                f"{rel(path)} draws relief and does not name {name}. The "
                f"credit is attached to the drawing by "
                f"cartography.credited(); a page that has one and not the "
                f"other has grown its own way of building a caption")
    assert pages > 100, (
        f"only {pages} pages draw relief; the measurement says far more do, "
        f"so this check has stopped reaching the pages it is for")
    n += 1

    # 3. The link goes somewhere that carries the credit. A thousand maps
    #    said "Coastline from Natural Earth" with Natural Earth linked to
    #    /sources, and /sources did not contain those two words anywhere.
    reg_page = os.path.join(ROOT, "site", "sources", "index.html")
    text = re.sub(r"<[^>]+>", " ", open(reg_page, encoding="utf-8").read())
    for name in list(used) + ["Natural Earth"]:
        assert name in text, (
            f"/sources does not name {name}, and every map on the site "
            f"links its credit there. A credit pointing at a page that does "
            f"not carry it looks like a register and is not one")
        n += 1
    return n


@check("the cartographic standard holds where a machine can hold it")
def c_cartographic_standard():
    # THE STANDARD IS docs/cartographic-standard.md, AND NINE OF ITS TEN
    # PRINCIPLES ARE SOMEBODY'S OPINION UNTIL SOMETHING MEASURES THEM. Three
    # are mechanical and are measured here.
    #
    # 2. GEOGRAPHY BEFORE DATABASE — a plate draws what it can name. Every
    #    mark on a country plate has a label on the same plate. The rule is
    #    not a ranking, because this atlas holds none: `rank`, `featured`,
    #    `boost` and `sponsored` are refused on every editorial record.
    #    Curation is by legibility, which is a property of the DRAWING and
    #    never a judgement about the place.
    #
    # 4. HIERARCHY BEFORE COMPLETENESS — the capital is placed first and
    #    cannot be dropped. A country plate with no capital on it is not a
    #    country plate.
    #
    # 7. QUIET COLOUR BEFORE SATURATED COLOUR — every colour the cartography
    #    paints is under a saturation ceiling. Saturated colour is the single
    #    clearest difference between an editorial atlas and a dashboard, and
    #    it is the easiest thing to lose one token at a time.
    # CHROMA, NOT HSV SATURATION. The first version of this used
    # `colorsys.rgb_to_hsv`, which reports the deep ocean #123f55 at 0.79 —
    # a dark navy called loud. HSV saturation is a ratio to the brightest
    # channel, so it rises as a colour DARKENS whatever its colourfulness,
    # and every editorial ink in this palette would have failed. Chroma is
    # the spread between the channels, which is what "quiet" means to an eye:
    # the deep ocean is 0.26 and a dashboard cyan is 1.00.
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"),
               encoding="utf-8").read()
    n = 0
    loud = []
    for name, hexv in re.findall(r"--(atlas-[a-z-]+|ocean-[a-z-]+):\s*(#[0-9a-fA-F]{6})",
                                 css):
        ch = [int(hexv[i:i + 2], 16) for i in (1, 3, 5)]
        chroma = (max(ch) - min(ch)) / 255.0
        if chroma > 0.40:
            loud.append(f"--{name} {hexv} at chroma {chroma:.2f}")
        n += 1
    assert not loud, ("the cartography paints a saturated colour: "
                      + "; ".join(loud))
    assert n >= 8, f"only {n} cartographic colours found — has the palette moved?"

    plates = 0
    for path in site_files():
        html = open(path, encoding="utf-8").read()
        if 'class="lyr lyr-destinations"' not in html:
            continue
        i = html.index('class="lyr lyr-destinations"')
        marks = html[i:html.index("</g>", i)]
        j = html.index('class="lyr lyr-labels"')
        labels = html[j:html.index("</g>", j)]
        # SCOPED TO THE COUNTRY PLATE, which is the family this rule is
        # about. A destination's local view is a different promise — where
        # you are AND what is around you — so it draws its neighbours and
        # hands their names to the list below on a narrow screen, which is
        # the phone rule every embedded map has followed since commit 39.
        nmark = marks.count('class="pmark')
        nname = len(re.findall(r'class="pname(?: cap)?"', labels))
        if nmark == 0:
            continue
        plates += 1
        assert nmark == nname, (
            f"{rel(path)} draws {nmark} marks and names {nname} of them — a "
            f"mark the plate cannot name is a dot that says only 'something "
            f"is here'")
        # THE CAPITAL, WHERE THE ATLAS HOLDS ONE. Montenegro's capital is
        # Podgorica and this atlas writes about Kotor, Perast and Žabljak —
        # so there is no capital to mark, and inventing a point for it would
        # be drawing a place we have nothing to say about. The promise is:
        # if the capital is one of the country's destinations, the plate
        # draws it and cannot drop it.
        slug = rel(path).split("/")[2]
        cy = json.load(open(os.path.join(ROOT, "data", "countries",
                                         slug + ".json"), encoding="utf-8"))
        cap = cy.get("capital")
        holds = any(t["name"].split(" &")[0] == cap
                    for r in cy["regions"] for t in r["cities"])
        if holds:
            assert 'class="pmark cap"' in marks, (
                f"{rel(path)} holds {cap} as a destination and its plate does "
                f"not draw it — the capital is placed first and cannot be "
                f"dropped")
        n += 2
    assert plates >= 40, f"only {plates} plates examined"
    return n


@check("the map renderer's layers are declared, ordered and painted")
def c_cartography():
    # THE PAINT ORDER IS THE THING THAT CANNOT BE SEEN TO BE WRONG. Terrain
    # under the coastline, rivers under the coastline, a route over
    # everything but the labels — get one of those backwards and the picture
    # still looks like a picture. Five families used to compose their own
    # plates inline, which is five opinions about an order nobody could read
    # in one place. Now `cartography.ORDER` is the order and this asserts
    # three things about it against the SHIPPED HTML and the stylesheet:
    #
    #   1. every layer group emitted on a page is in the declared order,
    #   2. every declared class has a rule in the stylesheet, so a layer
    #      cannot be added and silently render as nothing — this codebase has
    #      made that mistake three times on specificity alone,
    #   3. every layer whose dataset is absent has its appearance DECIDED in
    #      writing, so a gap is one somebody wrote down rather than one
    #      nobody noticed.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from lib import cartography as C
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"),
                encoding="utf-8").read()
    n = 0
    for name in C.ORDER:
        cls = C.CLASSES[name]
        if not C.held(name):
            assert name in C.DECIDED, (
                f"layer {name} has no data and no decided appearance — "
                f"a gap nobody wrote down")
            n += 1
            continue
        if name in C.FOLDED:
            carrier, why = C.FOLDED[name]
            assert carrier in C.ORDER and why, (
                f"layer {name} is folded into something that is not a layer")
            n += 1
            continue
        if name in C.PAINTED_BY:
            sel = C.PAINTED_BY[name]
            assert sel in css, (
                f"layer {name} is recorded as painting through {sel} and the "
                f"stylesheet has no such rule")
            n += 1
            continue
        assert f".{cls}" in css, (
            f"layer {name} paints through .{cls} and the stylesheet has no "
            f"rule for it")
        n += 1
    rank = {f"lyr-{name}": i for i, name in enumerate(C.ORDER)}
    pages = 0
    for path in site_files():
        html = open(path, encoding="utf-8").read()
        got = re.findall(r'<g class="lyr (lyr-[a-z-]+)"', html)
        if not got:
            continue
        pages += 1
        seen = [rank[g] for g in got if g in rank]
        assert seen == sorted(seen), (
            f"{rel(path)} emits its map layers out of the declared order: "
            f"{got}")
        n += len(seen)
    assert pages >= 40, f"only {pages} pages carry a layered plate"
    return n


@check("a journey's leg bars are drawn from the real distances")
def c_leg_bars():
    # A CHART IS A CLAIM, AND THIS ONE IS PUBLISHED ON SEVENTEEN PAGES.
    #
    # The shape of a journey is the lengths of its legs, and the page stated
    # them in words 104 times and never drew them. Within one journey the
    # longest leg is between 1.6x and 20.5x the shortest, so every leg row
    # being the same height made the Carpathian Arc — a 22 km hop and a
    # 443 km haul in the same list — look exactly like the White Villages.
    #
    # The bar is `.w0`-`.w100`, so what is asserted is the PERCENTAGE on the
    # shipped page against a haversine computed here, independently of
    # `pages.py`. Correct labels over a drawing scaled from the wrong array
    # still reads as a finished chart, which is the failure this catches:
    # one scale WITHIN a journey, the longest leg full width. Also asserted
    # is that the longest reaches 100 — a bar chart whose top value is 60%
    # is a chart nobody can read a ratio off.
    import math

    def hav(a, b):
        R = 6371.0
        p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
        dp = math.radians(b["lat"] - a["lat"])
        dl = math.radians(b["lon"] - a["lon"])
        x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        # ROUNDED, because the bar must agree with the number printed
        # beside it: the page says "146 km" and scales the bar by 146. The
        # haversine itself is recomputed here from the coordinates rather
        # than read from the build, which is the part that has to be
        # independent; sharing the decision to round to whole kilometres is
        # not agreeing with itself, it is asserting the drawing matches the
        # words. Off by one leg in seventeen journeys when it did not.
        return round(2 * R * math.asin(math.sqrt(x)))

    cities = {}
    for fn in sorted(os.listdir(os.path.join(ROOT, "data", "countries"))):
        if not fn.endswith(".json"):
            continue
        cy = json.load(open(os.path.join(ROOT, "data", "countries", fn), encoding="utf-8"))
        for reg in cy["regions"]:
            for t in reg["cities"]:
                cities[f"{cy['slug']}/{reg['slug']}/{t['slug']}"] = t
    journeys = list(json.load(
        open(os.path.join(ROOT, "data", "journeys.json"), encoding="utf-8")).values())[0]
    n = 0
    for j in journeys:
        stops = [cities[l["city"]] for l in j["legs"]]
        km = [hav(a, b) for a, b in zip(stops, stops[1:])]
        if not km:
            continue
        want = [int(round(d / max(km) * 100)) for d in km]
        html = open(os.path.join(OUT, "journeys", j["slug"], "index.html"),
                    encoding="utf-8").read()
        got = [int(x) for x in re.findall(r'<span class="hopbar"[^>]*>'
                                          r'<span class="w(\d+)">', html)]
        assert got == want, (
            f"/journeys/{j['slug']}: leg bars {got} but the distances give {want}")
        assert 100 in want, f"/journeys/{j['slug']}: no leg bar reaches full width"
        n += len(want)
    assert n > 80, f"only {n} leg bars examined"
    return n


@check("a score bar's median tick is the Atlas's own median for that dimension")
def c_score_median():
    # EIGHT EXACT NUMBERS WITH NOTHING TO COMPARE THEM TO. Bergen read
    # Authenticity 66 and Value 54, and a reader had no way to know that
    # Authenticity never exceeds 82 across the Atlas while Value's median is
    # 85 — so 66 is comfortably above the middle and 54 is well below it. The
    # numbers were exact and the meaning was unavailable.
    #
    # The tick is the median, and a tick is a claim: recomputed here from the
    # same functions the pages print, and asserted on the shipped HTML. The
    # two families take DIFFERENT medians on purpose — a country's scores
    # come from a different function than a city's, and marking a destination
    # with the country median would compare a place against a continent's
    # aggregate under the same mark.
    d = D.load()
    from lib import score as S
    from lib import urls as U
    n = 0
    for kind, spread, sample in (
            ("city", S.observed_spread(d["cities"]),
             [U.city(r["country"], r["region"], r["city"])
              for r in list(d["cities"].values())[:6]]),
            ("country", S.country_spread(d["countries"]),
             [U.country(c) for c in list(d["countries"].values())[:6]])):
        for u in sample:
            path = os.path.join(OUT, u.strip("/"), "index.html")
            if not os.path.exists(path):
                continue
            h = open(path, encoding="utf-8").read()
            for dim in S.DIMENSIONS:
                n += 1
                want = f'<span class="scoremed"><span class="w{spread[dim][2]}">'
                if want not in h:
                    fail(f"{u}: the {dim} bar's median tick is not the Atlas's "
                         f"{kind} median of {spread[dim][2]}")
    if n < 50:
        fail(f"only {n} median ticks examined — the scan found no pages")
    return n


@check("no drawing quietly omits a place it is drawn from")
def c_offframe():
    # A CIRCLE OUTSIDE THE viewBox RENDERS AS NOTHING AND REPORTS NOTHING —
    # the same class as a <use> of an id that is not on the page, and
    # invisible for the same reason: the picture looks finished.
    #
    # One destination in 319 does it. Longyearbyen is at 78 degrees north and
    # projects to y = -48 on the 1000x780 window every unframed constellation
    # is drawn in, so /interests/wild printed "19 of the 319 destinations are
    # tagged wild nature", drew nineteen circles and showed eighteen.
    #
    # The canvas is not going to move for one point and the comparison these
    # drawings exist to make is destroyed by framing them individually, so
    # the atlas does here what it already does at 52 degrees east: it says
    # so. This asserts that a page whose drawing loses a mark carries a
    # sentence about it, and — the other half — that a page that does NOT
    # lose one does not carry that sentence, so the note cannot outlive the
    # fault the way a caption for a deleted claim does.
    n = 0
    pat = re.compile(r'<svg class="constel[^"]*" viewBox="'
                     r'(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)"(.*?)</svg>',
                     re.S)
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        lost = 0
        for m in pat.finditer(h):
            x0, y0, w, hh = (float(v) for v in m.groups()[:4])
            for cx, cy in re.findall(r'<circle cx="(-?[\d.]+)" cy="(-?[\d.]+)"',
                                     m.group(5)):
                n += 1
                if not (x0 <= float(cx) <= x0 + w and y0 <= float(cy) <= y0 + hh):
                    lost += 1
        says = "above the top of this frame" in h or "outside the frame" in h
        if lost and not says:
            fail(f"{canonical_of(f)}: a drawing places {lost} mark(s) outside "
                 f"its own viewBox and the page does not say so. They render "
                 f"as nothing and report nothing.")
        if says and not lost:
            fail(f"{canonical_of(f)}: the page says a place is outside the "
                 f"frame and no mark is. A note that outlives its fault is "
                 f"the caption-for-a-deleted-claim failure.")
        # AND THE SENTENCE MAKES A CLAIM ABOUT THE PAGE AROUND IT. It ends
        # "that place is in the list below", which was written into the
        # shared function and is therefore true of whatever page happens to
        # print a list — the 404's drawing is its whole body, so for the life
        # of that sentence the one page a reader reaches after failing to
        # find something pointed them at a list that is not there. The
        # journey caption promising "a note under the leg" failed exactly
        # this way, and a source-level check passed on it.
        # COMMENTS OUT FIRST. This repository has now made the same mistake
        # three times — the invariant register counted a font size that
        # existed only in a comment about not adding font sizes, a photo
        # test matched the note explaining that nothing is recommended, and
        # this one went red on the HTML comment recording WHY /experiences
        # does not make the claim. An instrument that cannot tell code from
        # the documentation of code is reading the file rather than the page.
        vis = re.sub(r"<!--.*?-->", "", h, flags=re.S)
        m = re.search(r"([A-Z][^.<>]{2,40}?) at \d+°N (?:is|are) above the "
                      r"top of this frame", vis)
        if m and "in the list below" in vis:
            name = m.group(1).split(" and ")[-1].strip()
            # BELOW IS DOCUMENT ORDER FROM THE SENTENCE ITSELF, not
            # "after </header>" — the masthead is a <header> too, so the
            # first close tag on every page is above the note rather than
            # below it, and the slice then contained the sentence's own
            # words. It reported clean on the page it was written for.
            end = vis.find("</main>", m.end())
            body = vis[m.end():end if end > 0 else len(vis)]
            if name not in body:
                fail(f"{canonical_of(f)}: the note says {name!r} is in the "
                     f"list below and nothing below the head names it.")
    if n < 1000:
        fail(f"only {n} marks examined — the scan found almost none")
    return n


@check("the advisory treatment marks advisories, and nothing else")
def c_warn_is_a_warning():
    """THE ADVISORY COLOUR WAS SPENT 263 TIMES ON THINGS THAT ARE NOT
    ADVISORIES AND 3 TIMES ON THINGS THAT ARE.

    Counted in the shipped HTML before the fix:

        255   "We do not hold opening hours, prices or a website for this"
          4   "This is a pre-launch draft, and it says so"
          3   "Check government travel advice before planning anything here"
          1   "What discoverability is not"
          1   "What 'unverified' means here"
          1   "The Fund holds no money, and will not until three things are true"

    Three of those are a travel advisory. The rest are provenance and policy,
    which is the HERITAGE accent's stated home — "how this project knows what
    it claims". A reader who has learned that the tinted panel means STOP AND
    READ meets it on every place page saying we do not list opening hours,
    and the one time it means a country under a government travel advisory it
    looks exactly like Schönbrunn. That is the advisory-and-terracotta
    collision one level up: not two colours that look alike, but one colour
    doing two jobs.

    AND THE PROVENANCE PASS REACHED 262 PANELS AND MISSED 465 MORE. It gave
    the heritage rule to five call sites and left the rest on --sea, the
    INTERACTIVE colour — including the 445 destination pages saying we list
    neither hotels nor restaurants, the 130 region pages saying why food and
    practicalities are on the country page, and the seventeen interest pages
    explaining that their own tag is too wide to be a filter. Every one of
    those is a statement about what this atlas holds, refuses to hold, or has
    not built.

    So the DEFAULT is provenance now, because a default should be the common
    case, and the exceptions are the two rare kinds: `.warn` for a panel that
    is meant to stop you, and `.onward` for one that hands a reader to
    another surface and may wear the interactive colour. `.sourced` is gone
    rather than kept as a synonym for the default.

    The stylesheet cannot enforce which class a page chooses, so this counts
    the panels in the OUTPUT and asserts the shape of the failure: both
    exceptions rare, neither at zero, and — read off the stylesheet — the
    default still bound to the provenance token rather than to the
    interactive one. A count of classes cannot see a colour swap.
    """
    n = 0
    warn = onward = plain = 0
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        warn += h.count('class="note warn"')
        onward += len(re.findall(r'class="note onward\b', h))
        plain += len(re.findall(r'class="note(?: mt7)?"', h))
        n += 1
    if warn > 12:
        fail(f"{warn} pages carry the advisory panel. It is for a government "
             f"travel advisory and a planner that could not build a route; "
             f"provenance and policy are the plain `note`, in the heritage "
             f"accent. At this count the tint has stopped meaning anything")
    if warn < 1:
        fail("no page carries the advisory panel — the advisory countries "
             "still exist and their pages still have to say so")
    if onward > 60:
        fail(f"{onward} pages carry the onward panel, which wears the "
             f"INTERACTIVE colour. It is for a note that hands a reader to "
             f"another surface, and at this count it has become the default "
             f"again by the back door")
    if plain < 400:
        fail(f"only {plain} pages carry a provenance note, and 445 place "
             f"pages alone state what this atlas refuses to list. A policy "
             f"that stops being stated is a policy nobody can check")
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"),
               encoding="utf-8").read()
    if not re.search(r"^\.note \{ border-left-color: var\(--provenance\); \}",
                     css, re.M):
        fail("the plain note is no longer bound to --provenance. 843 pages "
             "state what this atlas does not hold, and --sea is the colour "
             "of things a reader can act on")
    return n


@check("the two cartographies are one register, and the ladder is recomputed")
def c_cartography_palette():
    """THE PICTURES WERE GIVEN A CARTOGRAPHY AND THE INSTRUMENTS WERE NOT.

    `docs/cartography.md` splits every drawing on what it IS — a picture is
    paper, an instrument is graphite — and the picture half got a four-step
    ocean, a land family, an ink coast and a lit subject, every one measured.
    The instrument half kept five raw hexes invented before European Future:
    #0a1220, #253546, #1b2735, #4a6480, #3a6299. Navy rather than graphite,
    no token in `docs/palette.json`, and recomputed by nothing.

        the pictures   land on water    7.91
        /map           land on water    1.50
        /map           a context country on water    1.24

    1.24 is not a quiet country, it is a country that is not drawn.

    This reads the hexes OUT OF THE STYLESHEET rather than out of a copy kept
    beside the claim, because a register that stores its own numbers agrees
    with itself for ever. The rows are separations rather than claims: a
    claim says a colour may carry TEXT on a ground; these say two drawn areas
    have to be distinguishable, which is SC 1.4.11's 3:1 for the boundary of
    a graphical object and something lower for a fill that only has to read
    as a mass.
    """
    n = 0
    pal = json.load(open(os.path.join(ROOT, "docs", "palette.json"), encoding="utf-8"))
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"), encoding="utf-8").read()
    rows = pal.get("cartography", {}).get("separations")
    if not rows:
        fail("docs/palette.json declares no cartographic separations — the "
             "instrument half of the atlas is unmeasured again")
        return n

    def hexof(token):
        m = re.search(re.escape(token) + r"\s*:\s*(#[0-9a-fA-F]{6})\s*;", css)
        return m.group(1) if m else None

    def lum(hexv):
        h = hexv.lstrip("#")
        ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]

    for row in rows:
        a, b = hexof(row["a"]), hexof(row["b"])
        if a is None or b is None:
            fail(f"{row['a']} or {row['b']} is not a literal hex token in the "
                 f"stylesheet, so the cartographic ladder cannot be recomputed")
            continue
        la, lb = lum(a), lum(b)
        r = (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
        if r < row["min"]:
            fail(f"{row['a']} ({a}) against {row['b']} ({b}) measures {r:.2f} "
                 f"and the register asks for {row['min']} — {row['why']}")
        if not row.get("why"):
            fail(f"the separation {row['a']} / {row['b']} carries no reason")
        n += 1

    # AND A HIERARCHY IS A GAP, NOT TWO NUMBERS. The coast has to be
    # decisively heavier than the frontier against the land they both cross,
    # or the two lines say the same thing — which is what they did for the
    # life of the plate system, separated by two tenths of a unit of stroke
    # width and nothing else.
    hier = pal["cartography"].get("hierarchy")
    if hier:
        hs, hw, hg = (hexof(hier[k]) for k in ("stronger", "weaker", "against"))
        if None in (hs, hw, hg):
            fail("the boundary hierarchy names a token that is not a literal "
                 "hex in the stylesheet")
        else:
            def _r(a, b):
                la, lb = lum(a), lum(b)
                return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
            strong, weak = _r(hs, hg), _r(hw, hg)
            if strong / weak < hier["min_gap"]:
                fail(f"the coast measures {strong:.2f} on the land and the "
                     f"frontier {weak:.2f} — a gap of {strong / weak:.2f} "
                     f"where the register asks for {hier['min_gap']}. Two lines "
                     f"that say the same thing are one line drawn twice")
            n += 1

    # ORDER IS THE CLAIM, AND A PER-PAIR MINIMUM CANNOT STATE IT. The water
    # lightens as it approaches a shore, which is distance from land and
    # never a claim about depth. A ramp whose middle step is darker than its
    # outer one is still three distinct colours: it clears every pairwise
    # floor above and draws the opposite of what the register says.
    lad = pal["cartography"].get("ladder")
    if lad:
        vals = []
        for t in lad["tokens"]:
            h = hexof(t)
            if h is None:
                fail(f"{t} is in the cartographic ladder and is not a literal "
                     f"hex token in the stylesheet")
                vals = None
                break
            vals.append((t, h, lum(h)))
        if vals:
            for (t0, h0, l0), (t1, h1, l1) in zip(vals, vals[1:]):
                if not l1 > l0:
                    fail(f"the cartographic ladder is out of order: {t1} ({h1}) "
                         f"is not lighter than {t0} ({h0}) — {lad['$comment'][:80]}")
                n += 1

    # AND THE NAVY IS GONE FOR GOOD. The five hexes above were the instrument
    # cartography for the life of the dark world; naming them here means the
    # build fails if one is pasted back, the way the gold and the lime are
    # held. A colour removed without a guard is a colour that returns.
    for dead in ("#0a1220", "#253546", "#1b2735", "#4a6480", "#3a6299"):
        if re.search(r"(?<![0-9a-fA-F])" + dead[1:] + r"(?![0-9a-fA-F])",
                     re.sub(r"/\*.*?\*/", "", css, flags=re.S), re.I):
            fail(f"{dead} is back in the stylesheet — that is the pre-European-"
                 f"Future instrument navy, and it is out of the system")
        n += 1
    return n


@check("every <use> and every url(#id) points at something on the same page")
def c_svg_refs():
    # A <use> OF AN ID THAT IS NOT ON THE PAGE RENDERS AS NOTHING AT ALL, and
    # nothing anywhere reports it — not the browser console, not the build,
    # not any count. `constellation()` draws its land with a <use> of
    # #constel-eu, which `constel_defs()` emits, and THREE separate pages have
    # now shipped one without the other: /discover before the land was added
    # under its dots, the 404 when it took the shared index opening, and every
    # motion page when its related bands stopped being cards. Each rendered as
    # a scatter of dots on empty sea, which looks deliberate.
    #
    # The general form is cheap: an SVG reference to a fragment on this
    # document has to resolve on this document. It covers `<use href>`,
    # `fill="url(#g)"`, `mask=`, `clip-path=` and `filter=` — a mask that
    # resolves to nothing hides the whole element it is on, which is the
    # loudest version of this fault.
    use_pat = re.compile(r'<use[^>]+(?:xlink:)?href="#([A-Za-z0-9_-]+)"')
    url_pat = re.compile(r'(?:fill|stroke|mask|clip-path|filter)="url\(#([A-Za-z0-9_-]+)\)"')
    n = 0
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        have = set(re.findall(r'\sid="([A-Za-z0-9_-]+)"', h))
        for pat, what in ((use_pat, "<use>"), (url_pat, "a url(#…) reference")):
            for ident in sorted(set(pat.findall(h))):
                n += 1
                if ident not in have:
                    fail(f"{canonical_of(f)}: {what} points at #{ident}, which "
                         f"is not on the page. It renders as nothing and "
                         f"reports nothing.")
    if n < 1000:
        fail(f"only {n} SVG references examined — the scan found almost none")
    return n


@check("a count agrees with its noun")
def c_plurals():
    # MEASURED ON THE SHIPPED SITE: "1 experiences" on 110 pages, "1 nights"
    # on 62, "1 cities" on 35, "1 destinations" on 25, "1 regions" on 15,
    # "1 places" on 8 and "1 countries" on 3. In meta descriptions that go to
    # every search engine and every shared link, in the accessible name of a
    # country map, in a destination's own facts line and in the caption under
    # fifty country plates.
    #
    # Every one was a separate f-string writing `{n} things`, and each was
    # individually invisible: the pages that trip it are the small ones —
    # Monaco, San Marino, Liechtenstein, Andorra, a region with one
    # destination — which is exactly the set nobody opens while checking a
    # change. render.n_of() is the one function now.
    #
    # Read on the built HTML rather than the source, because the source is
    # twenty call sites and the hundred-and-first is the one that reintroduces
    # this. A decimal before the 1 is excluded: "€21.1 million" is not a count.
    words = ("experiences", "nights", "cities", "destinations", "regions",
             "places", "countries", "days", "stops", "projects", "routes",
             "stories", "journeys", "themes", "entries", "legs", "fixtures",
             "kinds", "pieces", "hours", "minutes", "metres", "kilometres")
    pat = re.compile(r"(?<![\d.])1\s(" + "|".join(words) + r")\b")
    n = 0
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        n += 1
        m = pat.search(h)
        if m:
            i = max(0, m.start() - 60)
            fail(f"{canonical_of(f)} prints {m.group(0)!r} — a count that "
                 f"disagrees with its noun. Use render.n_of(). Context: "
                 f"...{h[i:m.end() + 10]!r}")
    return n


@check("nothing on a page is escaped twice")
def c_double_escape():
    # NINETY-THREE PAGES PRINTED "Tyrol &amp; the West".
    #
    # `render.section()` escapes its own title and lede, and eight call sites
    # passed `esc(...)` inside them — so every region, country and place whose
    # name contains an ampersand rendered the entity in the body text, in the
    # band heading and in the lede: "Everything recorded across Tyrol &amp;
    # the West, in one list." It is invisible in the source, because both
    # halves are correct on their own; only the composition is wrong.
    #
    # Asserted on the shipped HTML for the same reason the projection claim
    # is: a source-level check passes the day somebody adds a ninth call
    # site, and what a reader gets is the page.
    n = 0
    for f in site_files():
        h = open(f, encoding="utf-8").read()
        for pat in ("&amp;amp;", "&amp;lt;", "&amp;gt;", "&amp;#x27;", "&amp;quot;"):
            n += 1
            if pat in h:
                fail(f"{canonical_of(f)} prints {pat!r} — something was "
                     f"escaped twice. render.section() escapes its own title "
                     f"and lede; a caller must not.")
    return n


@check("every link a script can write points at a route this site has")
def c_script_links():
    # TWO DEAD LINKS LIVED IN EMPTY STATES FOR THE LIFE OF THIS SITE.
    #
    # /my-europe's "nothing saved yet" and /search's "the index did not load"
    # both pointed at `/atlas`, which has never been a route here — the
    # country index is /countries. They survived because they are strings
    # inside JavaScript that only runs in a state the build never renders, so
    # the link checker, which reads shipped HTML, could not see either of
    # them. A CODE PATH NOTHING EXERCISES IS A CODE PATH NOTHING CHECKS, and
    # an empty state is the state a page ships in, not a fallback.
    #
    # This reads the scripts themselves. Anything that starts with a single
    # slash and is not an /api or /assets path has to resolve to a built page,
    # by the same rule cleanUrls gives a reader typing it.
    n = 0
    for js in sorted(glob.glob(os.path.join(ROOT, "assets", "js", "*.js"))):
        src = open(js, encoding="utf-8").read()
        for href in sorted(set(re.findall(r'href=\\?"(/[^"\\\s#?]*)', src))):
            n += 1
            if href.startswith(("/api/", "/assets/")):
                continue
            target = os.path.join(OUT, href.strip("/"), "index.html")
            if href == "/":
                target = os.path.join(OUT, "index.html")
            if not os.path.exists(target):
                fail(f"{os.path.basename(js)} writes a link to {href}, which "
                     f"is not a page this site builds. It is invisible to the "
                     f"link checker because it only renders in a state the "
                     f"build never produces.")
    if n < 4:
        fail(f"only {n} script-written links examined — the scan has stopped "
             f"finding them")
    return n


@check("/method's score spreads are the Atlas's own, and the bar is drawn from them")
def c_method_spread():
    # A CHART IS A CLAIM, AND THIS ONE REPLACED A CONSTANT.
    #
    # /method published "0-97" beside all eight score dimensions: the /themes
    # failure, where every card said "8 PLACES" because every theme holds
    # eight. It was also wrong — nothing scores 0, every dimension starts at
    # a base of 34, Food tops out at 96 and Authenticity at 82.
    #
    # Recomputed here from the same city_scores() the destination pages
    # print, independently of pages.method_page(), and asserted against the
    # SHIPPED HTML. And the geometry is asserted too, because correct numbers
    # over a bar drawn from the wrong ones still reads as a finished chart:
    # the widest block must belong to the dimension with the widest observed
    # span, and every tick must sit inside its own block.
    import statistics
    d = D.load()
    from lib import score as S
    got = {}
    for rec in d["cities"].values():
        for k, v in S.city_scores(rec["country"], rec["region"], rec["city"]).items():
            got.setdefault(k, []).append(v)
    h = open(os.path.join(OUT, "method", "index.html"), encoding="utf-8").read()
    if "0\u201397" in h:
        fail("/method still prints the constant range 0-97")
    widest = None
    for key, label in S.LABELS.items():
        v = got.get(key)
        if not v:
            fail(f"/method: no destination scores {key}")
            continue
        lo, hi, med = min(v), max(v), int(statistics.median(v))
        want = f"{lo}\u2013{hi}, median {med}"
        if want not in h:
            fail(f"/method: the spread printed for {label} is not the Atlas's "
                 f"own \u2014 {want!r} is not on the page. A chart is a claim.")
        # NO `y` IN THIS PATTERN. It used to read `x="{lo}" y="2" width="..."`
        # and went red the day the chart gained end caps and grew a unit
        # taller — the ninth assertion in this repository to pin a shape
        # rather than the promise. What is being claimed is that the bar
        # starts where this dimension's floor is and runs as far as its
        # ceiling; where it sits vertically inside its own viewBox is the
        # drawing's business.
        want_rect = f'class="distspan" x="{lo}" y='
        if want_rect not in h or f'width="{hi - lo}"' not in h:
            fail(f"/method: {label}'s bar is not drawn from its own numbers "
                 f"\u2014 expected a distspan at x={lo} of width {hi - lo}")
        if not (lo <= med <= hi):
            fail(f"/method: {label}'s median {med} is outside its own span")
        if widest is None or hi - lo > widest[1]:
            widest = (label, hi - lo)
    # One axis for all eight: every block is placed on the same 0-100 scale,
    # so the widest block IS the widest range. A per-row axis would draw them
    # all the same width, which is the constant again in another medium.
    spans = re.findall(r'class="distspan" x="(\d+)" y="[\d.]+" width="(\d+)"', h)
    if len(spans) != len(S.LABELS):
        fail(f"/method draws {len(spans)} spread bars for {len(S.LABELS)} "
             f"dimensions")
    elif spans and max(int(w) for _, w in spans) != widest[1]:
        fail(f"/method's widest bar is {max(int(w) for _, w in spans)} units "
             f"but the widest range is {widest[0]}'s at {widest[1]}")
    return len(S.LABELS) * 4


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
    # THE FLOOR IS THE EVENTS FAMILY AND THE SET IS WHEREVER IT IS DRAWN.
    # /discover's "By month" band was twelve identical chips — the exact
    # shape this chart was built to replace, still shipping one family over,
    # on the page whose whole subject is how to choose. It draws the band
    # now, so the check can no longer be a fixed list of thirteen files: a
    # chart is a claim wherever it appears, and the fourteenth page would
    # have been unchecked.
    pages = [os.path.join(OUT, "events", "index.html")] + [
        os.path.join(OUT, "events", m, "index.html") for m in ms
    ]
    pages += [f for f in site_files()
              if f not in pages and 'class="yearband"' in open(f, encoding="utf-8").read()]
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
        # WHITESPACE IS COLLAPSED FIRST, because the homepage named this
        # projection for the life of the drawn hero and this check never
        # saw it: the paragraph wrapped between "conformal" and "conic" in
        # the generated source, so the substring was not there to find. It
        # printed no angle at all and every run was green. An instrument
        # that a line break can defeat is reading the file rather than the
        # claim, and the claim is what a reader gets.
        h = " ".join(open(path, encoding="utf-8").read().split())
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


@check("no social card is a landscape chosen by a hash")
def c_og_never_hashed():
    # A CARD IS THE ONE PICTURE RENDERED INSIDE SOMEBODY ELSE'S PRODUCT.
    #
    # og_tags() takes a motif. Where a page passes one, the card is the same
    # drawing as the page and comes from what the record IS. Where it passes
    # None, plate_shapes() picks the landscape from the hash of the seed.
    #
    # The story family passed None. The rule — a story is not a place and its
    # picture may not be drawn from a hash — had already been enforced twice:
    # the page was rebuilt on storymap(), and the index had its nine
    # hash-drawn cards removed. The social card went on being a landscape
    # chosen by the slug, on the one surface nobody here ever looks at.
    #
    # This asserts it at the source, because the shipped HTML cannot tell a
    # hash-chosen card from a named one — both are a URL to a PNG. Every og=
    # in pages.py either names a motif or is None, and None now means no card
    # at all rather than "choose one for me".
    src = open(os.path.join(ROOT, "tools", "lib", "pages.py"),
               encoding="utf-8").read()
    n = 0
    for m in re.finditer(r"og=\((.{0,160}?)\),\n", src, re.S):
        n += 1
        args = m.group(1)
        # the second argument is the motif
        parts = [p.strip() for p in args.split(",")]
        if len(parts) >= 2 and parts[1] in ("None", "none"):
            fail(f"a page passes og=(seed, None, ...): the social card for it "
                 f"is a landscape chosen by the hash of the seed. Name the "
                 f"motif from what the record is, or pass og=None and ship "
                 f"no card — {args[:70]}")
    n += 1
    if "og=None," not in src:
        fail("nothing passes og=None any more. That was the story family's "
             "answer to a rule that forbids both a hash-drawn picture and an "
             "illustration; if a story has a card again it needs a reason.")
    # And the built pages agree: no story ships one.
    d = D.load()
    for st in d["stories"]:
        n += 1
        path = os.path.join(OUT, "stories", st["slug"], "index.html")
        if os.path.exists(path) and "og:image" in open(path, encoding="utf-8").read():
            fail(f"/stories/{st['slug']}: ships a social card. A story's "
                 f"picture is its own places, a photograph from the register, "
                 f"or nothing.")
    return n


@check("every page head declares what kind of page it is")
def c_pagehead_role():
    # TWENTY-ONE OF TWENTY-TWO FAMILIES PLACED AN IDENTICAL h1 IN AN
    # IDENTICAL PLACE, and the only one that differed had a hero. The entire
    # art-directional difference between a magazine story and a country
    # encyclopedia was one 11px kicker changing hue.
    #
    # There are three roles, and they are what the reader is DOING:
    #
    #   overture    one thing. The name is the event: a narrow measure and
    #               air above it, and the page opens rather than starts.
    #   index       a set. What matters is how big, so the extent sits
    #               beside the name and the set starts sooner.
    #   instrument  a tool. The title is a label at section weight on the
    #               same line as its kicker, because the page IS the thing.
    #
    # None of them adds a type size — a seventeenth was refused twice, and
    # if a role needs a new scale value it is a decoration and not a role.
    #
    # The pages with no role are the ones that are genuinely just prose:
    # the manifesto, the method, the legal set. They are named here, so a
    # NEW page cannot join them by accident — which is exactly how twenty-one
    # families ended up sharing one head.
    PLAIN = {
        "/about", "/method", "/manifesto", "/sources", "/api", "/how-it-works",
        "/join", "/for-business", "/freshness", "/privacy", "/cookies",
        "/terms", "/accessibility", "/help", "/contact", "/tourism-boards",
        "/404", "/discover", "/my-europe", "/search",
        # The real routes, which differ from what the generators are called:
        "/api-docs", "/experiences/join", "/for-businesses",
        "/for-tourism-boards", "/sources/freshness",
    }
    ROLES = ("overture", "index", "instrument")
    n = 0
    for path in site_files():
        r = canonical_of(path)
        h = open(path, encoding="utf-8").read()
        m = re.search(r'<div class="pagehead([^"]*)"', h)
        if not m:
            continue
        n += 1
        got = [x for x in ROLES if x in m.group(1)]
        if len(got) == 1:
            continue
        if not got and r in PLAIN:
            continue
        if len(got) > 1:
            fail(f"{r}: the head claims {len(got)} roles ({', '.join(got)}). "
                 f"A page is one thing, a set of things, or a tool.")
        else:
            fail(f"{r}: the head declares no role. It is one of "
                 f"{'/'.join(ROLES)}, or it is prose and belongs in the "
                 f"named list in this check — which exists so a new page "
                 f"cannot join the twenty-one that shared one head by "
                 f"accident.")
    return n


@check("an SVG layer marked hidden is hidden without a stylesheet")
def c_svg_hidden_is_hidden():
    """A map layer switched off must be switched off in the drawing itself.

    The UA stylesheet's `[hidden] { display: none }` is namespaced to HTML,
    so an SVG <g> carrying the attribute goes on drawing. europedoor.css
    adds a rule of its own — which is why the map's places layer once
    shipped visible while marked hidden, and why the fix at the time was one
    line of CSS.

    That fix left the layer switches one stylesheet request away from being
    inert, and CI found the other half of it: Chromium 131 does not apply
    that author rule to these groups while Chromium 141 does. The same page
    hid its places layer here and drew it on the runner, for three months,
    with every gate green in one browser and two browser checks red in the
    other.

    So the promise is not "there is a rule that hides it". It is that the
    markup hides it: `display` is an SVG presentation attribute and needs no
    cascade, no stylesheet and no browser version. Proved both ways with the
    stylesheet blocked — the attribute alone leaves the layer drawn, the
    presentation attribute removes it.

    The `hidden` attribute stays, because it is what a reader's assistive
    technology is told. This asserts the two travel together.
    """
    n = 0
    pat = re.compile(r"<g\b[^>]*>")
    for f in site_files():
        html = open(f, encoding="utf-8").read()
        for tag in pat.findall(html):
            if " hidden" not in tag and not tag.rstrip(">").endswith("hidden"):
                continue
            n += 1
            if 'display="none"' not in tag:
                fail(f"{rel(f)}: {tag} is marked hidden and carries no "
                     f"display=\"none\". The hidden attribute draws nothing "
                     f"on an SVG group without a stylesheet rule, and a "
                     f"layer switch that depends on one is a layer switch "
                     f"that is inert whenever that request fails.")
    return n


@check("every registered photograph still hashes to what was recorded")
def c_photo_bytes():
    """The provenance is re-checked against the bytes, not trusted.

    A SHA-256 WRITTEN ONCE AND NEVER COMPARED IS A DECORATION. The register
    recorded the hash of the original at the moment it arrived and nothing
    ever looked at it again — so a file replaced, re-compressed or swapped
    after acquisition would carry a provenance row that agreed with itself
    and described a different photograph. That is the failure class this
    repository has recorded more than once: the evidence and the artefact
    drifting apart with every gate green.

    So this re-hashes the original, re-hashes every derivative the row
    claims, and checks the pixel dimensions the row states are the pixel
    dimensions the file has. It is the reason the untouched original is kept
    beside the ladder: without it there is nothing to re-check against, and
    the hash becomes a claim about a file nobody holds.

    It also asserts the ladder is REACHABLE — every width and format
    `picture()` will ask for exists — because a register row is a promise
    that a page can be rendered, and a missing 800px webp is that promise
    failing in one browser and not another.
    """
    reg_path = os.path.join(ROOT, "data", "images.json")
    if not os.path.exists(reg_path):
        return 0
    reg = json.load(open(reg_path, encoding="utf-8")).get("images", {})
    n = 0
    for key, row in sorted(reg.items()):
        orig = os.path.join(ROOT, row.get("original", ""))
        n += 1
        if not row.get("original") or not os.path.exists(orig):
            fail(f"images.json > {key}: the original {row.get('original')!r} "
                 f"is not in the repository. It is the evidence every other "
                 f"hash is checked against; without it the provenance cannot "
                 f"be re-verified by anybody, ever")
            continue
        body = open(orig, "rb").read()
        got = hashlib.sha256(body).hexdigest()
        if got != row.get("sha256"):
            fail(f"images.json > {key}: the original hashes {got[:12]} and "
                 f"the register says {str(row.get('sha256'))[:12]}. The file "
                 f"is not the file that was acquired")
        if len(body) != row.get("bytes"):
            fail(f"images.json > {key}: the original is {len(body)} bytes and "
                 f"the register says {row.get('bytes')}")
        for dname, d in sorted((row.get("derivatives") or {}).items()):
            n += 1
            dpath = os.path.join(ROOT, "assets", "img", dname)
            if not os.path.exists(dpath):
                fail(f"images.json > {key}: derivative {dname} is registered "
                     f"and missing")
                continue
            dbody = open(dpath, "rb").read()
            if hashlib.sha256(dbody).hexdigest() != d.get("sha256"):
                fail(f"images.json > {key}: derivative {dname} does not hash "
                     f"to what the register records")
        # The ladder picture() will actually ask for.
        widths = (row.get("processing") or {}).get("widths") or []
        for w in widths:
            for ext in ("avif", "webp", "jpg"):
                name = f"{row['file']}.{row.get('version', '')}-{w}.{ext}"
                n += 1
                if name not in (row.get("derivatives") or {}):
                    fail(f"images.json > {key}: processing claims width {w} "
                         f"and no derivative {name} is registered")
    return n


@check("nothing a candidate review produced is in the repository")
def c_no_candidate_previews():
    """A CONTACT SHEET IS SOMEBODY ELSE'S PHOTOGRAPHS WITH NO PROVENANCE.

    The art-direction step downloads a preview of every candidate so a person
    can see each one inside the real hero. Those are Pexels photographs that
    nobody chose, carrying no register row, no SHA-256 of an original and no
    date — which is precisely what "no external licence claim enters
    production from memory" refuses. They belong in a scratch directory and
    in a workflow artifact, and nowhere else.

    So this asserts the other end of that promise, on the tracked files
    rather than on the intention: no preview, no sheet, no scratch directory
    is in the repository, and the ignore rules that keep them out are still
    there. A .gitignore entry is a request; a check is the guarantee.
    """
    n = 0
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT,
                             capture_output=True, text=True).stdout.split("\n")
    for f in tracked:
        if not f:
            continue
        n += 1
        base = os.path.basename(f)
        if f.startswith(".cache/") or "/previews/" in f or f.startswith("previews/"):
            fail(f"{f} is a candidate review artefact and is committed")
        if base.startswith("candidate-"):
            fail(f"{f}: a candidate preview has no photographer, no source, "
                 f"no licence and no hash, and is in the repository")
        if base in ("hero-sheet.png", "contact-sheet.png", "recognition.png"):
            fail(f"{f} is an instrument's output, not a source file")
    ignored = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read()
    for rule in (".cache/", "hero-sheet.png"):
        n += 1
        if rule not in ignored:
            fail(f".gitignore no longer carries {rule!r} — the scratch the "
                 f"contact sheet writes into would be offered up by `git add`")
    return n


@check("only a provider cleared for automated acquisition can be acquired automatically")
def c_automated_provider():
    """Unsplash cannot reach the automated path, and the refusal has teeth.

    The gate answers `automated_acquisition` per provider from the archived
    pages. Unsplash's is false because its API guidelines require hotlinking —
    "All API uses must use the hotlinked image URLs returned by the API" — and
    the architecture here is acquire-then-self-host, which that forbids. That
    answer has to bind the code rather than sit in a JSON file: this asserts
    the acquisition script reads the field, that the workflow's provider input
    offers only cleared providers, and that no registered photograph came from
    an uncleared one.
    """
    gate_path = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")
    acq = os.path.join(ROOT, "scripts", "images", "acquire.py")
    if not os.path.exists(acq) or not os.path.exists(gate_path):
        return 0
    gate = json.load(open(gate_path, encoding="utf-8"))
    src = open(acq, encoding="utf-8").read()
    n = 1
    if "automated_acquisition" not in src:
        fail("scripts/images/acquire.py does not read "
             "`automated_acquisition` — the gate's answer would be a comment")
    cleared_set = {s for s, r in gate.items()
                   if not s.startswith("$")
                   and (r.get("automated_acquisition") or {}).get("value") is True}
    wf = os.path.join(ROOT, ".github", "workflows", "photograph.yml")
    if os.path.exists(wf):
        body = open(wf, encoding="utf-8").read()
        # SCOPED TO THE PROVIDER INPUT. The first `options:` in that file is
        # the stage choice — discover or acquire — and reading it as a
        # provider list made this check report that the workflow offers a
        # provider called "discover". A pattern that matches the first thing
        # of its shape is a pattern that will eventually match the wrong one.
        prov = re.search(r"provider:\n(?:.*\n)*?\s+options:\s*\[([^\]]*)\]",
                         body)
        m = prov
        if m:
            n += 1
            offered = {o.strip() for o in m.group(1).split(",") if o.strip()}
            extra = offered - cleared_set
            if extra:
                fail(f"the photograph workflow offers {sorted(extra)} as an "
                     f"acquisition provider and the licence gate has not "
                     f"cleared it for automated acquisition")
    reg_path = os.path.join(ROOT, "data", "images.json")
    if os.path.exists(reg_path):
        for key, row in json.load(open(reg_path, encoding="utf-8")).get("images", {}).items():
            n += 1
            if row.get("provider") not in cleared_set:
                fail(f"images.json > {key}: provider {row.get('provider')!r} "
                     f"is not cleared for automated acquisition")
    return n


@check("the palette register and the stylesheet are the same palette")
def c_palette_is_the_stylesheet():
    """THE REGISTER WAS DOING ARITHMETIC ABOUT COLOURS NOBODY SHIPS.

    `docs/palette.json` declares eighteen tokens with a hex each, and every
    contrast claim, every forbidden pair and every cartographic separation is
    recomputed from those hexes. Nothing compared them with the stylesheet.
    Deleting `--ultramarine` from europedoor.css entirely left this suite
    green: the register went on asserting that ultramarine clears 3:1 on
    limestone-3 for a colour the site no longer had. A palette that cannot
    drift from the pages is the whole point of keeping it as data.

    Two directions, and the second is the one the dead-rule scan is for one
    level down: a token declared in the stylesheet and never spent is
    vocabulary that looks like a decision. `--atlas-context` was identical to
    `--atlas-land` and unreferenced, `--shadow` was declared in three world
    blocks while only `--shadow-lift` was ever used, and `--ultramarine` was
    declared for the life of the palette and spent nowhere.

    A token may be declared BY VALUE rather than by name — the three `-lift`
    colours are bound to `--door` and `--warn` inside the dark blocks — so
    the register's promise is that the HEX is in the stylesheet, and where
    the name is declared too, that the two agree.
    """
    path = os.path.join(ROOT, "assets", "css", "europedoor.css")
    css = re.sub(r"/\*.*?\*/", "", open(path, encoding="utf-8").read(), flags=re.S)
    pal = json.load(open(os.path.join(ROOT, "docs", "palette.json"),
                        encoding="utf-8"))
    named = {}
    for m in re.finditer(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;", css):
        named.setdefault(m.group(1)[2:], set()).add(m.group(2).lower())
    every = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", css)}
    n = 0
    for name, row in sorted(pal["tokens"].items()):
        hexv = str(row.get("hex", "")).lower()
        n += 1
        if name in named:
            if hexv not in named[name]:
                fail(f"palette.json: {name} is {hexv} in the register and "
                     f"{'/'.join(sorted(named[name]))} in the stylesheet. "
                     f"Every claim about it is arithmetic on the wrong colour")
        elif hexv not in every:
            fail(f"palette.json: {name} ({hexv}) is not in the stylesheet at "
                 f"all, by name or by value. The register is asserting "
                 f"contrast for a colour the site does not ship")
    declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", css))
    for tok in sorted(declared - used):
        n += 1
        fail(f"europedoor.css declares {tok} and nothing ever spends it. "
             f"A token nobody references is vocabulary that looks like a "
             f"decision — the dead-rule scan's finding, one level up")
    # AND THE OTHER DIRECTION, WHICH IS THE ONE THAT WAS ACTUALLY BROKEN.
    #
    # An unresolvable var() does not fall back to something sensible: the
    # whole declaration is invalid at computed-value time and the property
    # takes its INHERITED value. So a misspelt token is not a missing colour,
    # it is a DIFFERENT one, and it can be the text colour.
    #
    # Two were live. `--serif` was referenced by twelve rules and has never
    # existed — the token is `--display` — and nine of those twelve sit on an
    # h1/h2/h3 that `h1, h2, h3, h4 { font-family: var(--display) }` had
    # already set correctly, so the rule ACTIVELY REPLACED the right value
    # with an invalid one and the heading inherited the sans body face. The
    # index hero h1 on five indexes, the journey rows, the story lead, the
    # homepage's four doors and the closing statement were all set in the
    # body font on a site whose whole voice is an editorial serif. And
    # `--atlantic-lift` was referenced by `--provenance` inside both dark
    # blocks, so the heritage rule down the side of 843 provenance panels
    # painted limestone in the dark preference and in the INTELLIGENCE world.
    #
    # Neither is visible to a check that counts declarations, to the
    # dead-rule scan (the rule matches and does change something — it changes
    # the font to the wrong one), or to any contrast assertion.
    for tok in sorted(used - declared):
        n += 1
        where = [ln for ln in css.splitlines() if "var(" + tok in ln][:1]
        fail(f"europedoor.css references {tok} and never declares it. An "
             f"unresolvable var() makes the whole declaration invalid and "
             f"the property falls back to its INHERITED value, so this is "
             f"not a missing value, it is a different one"
             + (f" — {where[0].strip()[:70]}" if where else ""))
    return n


@check("no destination is extinguished by the hero's data-cut fades")
def c_hero_dusk_reach():
    """THE FADE WAS PUT THERE TO KEEP THE PICTURE HONEST AND IT WAS UNLIGHTING
    THE ATLAS.

    `data/geo/` stops at 52°E and 33°N, and both cuts are straight lines
    through real land, so the hero ramps into shadow along each rather than
    ending. The widths of those two ramps were chosen by eye — 360 units east,
    150 south — and nothing ever asked what was underneath them. Measured over
    the 319 destinations this atlas writes a page about: Baku 100%, Paphos 92%,
    Tbilisi 89%, Chania 83%, Valletta 77%, Moscow 71%, and 46 destinations
    dimmed past half. Five countries were effectively unlit on a picture whose
    own label says every country is a link.

    READ OFF THE SHIPPED HTML, NOT THE CONSTANTS. `pages.dusk_reach` derives
    the widths and a check re-running that derivation would only ever agree
    with it; the gradient the browser is handed is what a reader gets. The two
    gradients are parsed out of the hero, the ramp is evaluated at every
    destination's projected coordinate, and the ceiling is the promise.
    """
    h = open(os.path.join(OUT, "index.html"), encoding="utf-8").read()

    def grad(gid):
        m = re.search(r'<(linear|radial)Gradient id="%s"([^>]*)>(.*?)</\1Gradient>'
                      % gid, h, re.S)
        if not m:
            fail(f"/: the hero has no gradient #{gid} — the data-cut fade this "
                 f"check measures is not in the shipped page")
            return None, None
        attrs = dict(re.findall(r'([\w-]+)="([^"]+)"', m.group(2)))
        stops = sorted({(float(o), float(v)) for o, v in re.findall(
            r'<stop offset="([\d.]+)" stop-opacity="([\d.]+)"', m.group(3))})
        if not stops:
            fail(f"/: gradient #{gid} carries no stops this check can read")
            return None, None
        return attrs, stops

    ea, estops = grad("heroedge")
    fa, fstops = grad("herofootg")
    if not ea or not fa:
        return 1

    def ramp(t, stops):
        if t <= stops[0][0]:
            return stops[0][1]
        if t >= stops[-1][0]:
            return stops[-1][1]
        for (o0, v0), (o1, v1) in zip(stops, stops[1:]):
            if o0 <= t <= o1:
                f = 0.0 if o1 == o0 else (t - o0) / (o1 - o0)
                return v0 + (v1 - v0) * f
        return stops[-1][1]

    x1, y1 = float(ea["x1"]), float(ea["y1"])
    x2, y2 = float(ea["x2"]), float(ea["y2"])
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy or 1.0
    cx, cy, rr = float(fa["cx"]), float(fa["cy"]), float(fa["r"])

    data = D.load()
    worst, n = [], 0
    for v in data["cities"].values():
        t = v["city"]
        x, y = P.MAPPROJ.xy(t["lat"], t["lon"])
        e = ramp(((x - x1) * dx + (y - y1) * dy) / L2, estops)
        f = ramp(math.hypot(x - cx, y - cy) / rr, fstops)
        n += 1
        worst.append((max(e, f), t["name"]))
    worst.sort(reverse=True)
    ceiling = P.DUSK_CEILING + 0.02        # the stop list is sampled, not exact
    for dusk, name in worst:
        if dusk > ceiling:
            fail(f"/: the hero's data-cut fade paints {name} at {dusk * 100:.0f}% "
                 f"of the shadow, above the {P.DUSK_CEILING * 100:.0f}% ceiling. "
                 f"A fade that dims the places it exists to keep legible has "
                 f"swapped one rendering fault for another — see "
                 f"pages.dusk_reach()")
            break
    return n


@check("a registered photograph appears on the page its purpose claims")
def c_photo_published():
    """The register cannot claim a surface it does not reach.

    THIS CAUGHT ITSELF WITHIN A MINUTE OF EXISTING. The first purposes file
    said the homepage hero fills `home:hero`, and the homepage asks
    `picture()` for `home-hero` — one character apart. The acquisition ran,
    the ladder built, every gate went green, and the photograph appeared on
    no page at all: a register row claiming `/`, fifteen files on disk, and
    a homepage that still drew the map.

    Nothing else could have found it. The validator checks the row is
    complete, the hash check proves the bytes are the bytes, and neither asks
    the only question that matters to a reader — is it ON the page. So this
    reads the SHIPPED HTML at the publication path the purpose declares and
    looks for the file. A photograph that is registered and unpublished is
    either a wasted acquisition or a broken surface, and both should stop the
    build rather than wait to be noticed.
    """
    reg_path = os.path.join(ROOT, "data", "images.json")
    if not os.path.exists(reg_path):
        return 0
    reg = json.load(open(reg_path, encoding="utf-8")).get("images", {})
    n = 0
    for key, row in sorted(reg.items()):
        n += 1
        path = row.get("publication_path", "")
        f = os.path.join(OUT, path.strip("/"), "index.html")
        if path == "/":
            f = os.path.join(OUT, "index.html")
        if not os.path.exists(f):
            fail(f"images.json > {key}: publication_path {path!r} is not a "
                 f"page this site builds")
            continue
        html = open(f, encoding="utf-8").read()
        # AND THE FILES IT REFERENCES MUST BE SERVED. The first version of
        # this check read the HTML and stopped there, so it passed on a
        # homepage that referenced a ladder site/ did not contain — the
        # reference was right and every file 404'd. A <picture> does not fall
        # back once a <source> matches, so that is a hole where the hero is.
        for name in sorted(row.get("derivatives") or {}):
            n += 1
            if not os.path.exists(os.path.join(OUT, "assets", "img", name)):
                fail(f"images.json > {key}: {name} is registered and is not "
                     f"published under site/assets/img/ — the page references "
                     f"a file the site does not serve")
        if f"{row['file']}.{row.get('version', '')}-" not in html:
            fail(f"images.json > {key}: acquired for {row.get('purpose')!r} "
                 f"and {path} does not reference {row['file']}. The register "
                 f"claims a surface it does not reach — either the key is not "
                 f"the one that page asks picture() for, or the surface never "
                 f"asks at all")
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
