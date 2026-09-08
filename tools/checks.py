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
import html.parser
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D
from lib import pages as P
from lib import score as S
from lib import render as R
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
            if 'type="application/json"' in attrs:
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
    required = ["architecture", "product", "development", "database", "roadmap",
                "api", "ai", "deployment", "security", "content-model",
                "brand", "brand-lock", "images", "data-model", "legal-position",
                "technical-foundation", "audit-2026-09"]
    n = 0
    for name in required:
        path = os.path.join(ROOT, "docs", f"{name}.md")
        if not os.path.exists(path):
            fail(f"docs/{name}.md is missing")
            continue
        if os.path.getsize(path) < 400:
            fail(f"docs/{name}.md is a stub")
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
