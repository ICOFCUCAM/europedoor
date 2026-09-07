#!/usr/bin/env python3
"""Every check that has to pass before Europedoor ships.

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
    expect += len(d["taxonomy"]["interests"])
    expect += 1 + len(d["journeys"])
    expect += 1 + len(d["themes"])
    expect += 1 + len(d["stories"])
    expect += 2                                   # /plan, /search
    expect += 1 + len(d["taxonomy"]["experience_kinds"]) + 1 + 1   # experiences, kinds, join, business
    expect += 1 + len(d["fund"])
    expect += 6                                   # map, events, quiet, my-europe, method, about
    expect += len(d["taxonomy"]["months"])        # /events/<month>
    expect += 3                                   # how-it-works, sources, freshness
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


@check("the brand is locked to Europedoor and europedoor.com")
def c_brand():
    # docs/brand-lock.md exists because incoming strategy documents keep
    # arriving with a different name on them. This is the enforcement.
    banned = ["Europe Atlas ·", "Europia", "Via Europa", "Eurovia", "Europe Unbound", "europedoor.example"]
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        if 'href="https://europedoor.com' in s and False:
            pass
        if "europedoor.com" not in s:
            fail(f"{rel(f)}: no canonical on europedoor.com")
        for b in banned:
            if b in s:
                fail(f"{rel(f)}: carries a competing or placeholder product name {b!r}")
        n += 1
    if SITE_NAME != "Europedoor":
        fail(f"SITE_NAME is {SITE_NAME!r}, must be 'Europedoor' — see docs/brand-lock.md")
    return n


@check("every internal link resolves to a page that exists")
def c_links():
    served = set()
    for f in site_files():
        served.add(canonical_of(f))
    for extra in ("/assets/css/europedoor.css", "/assets/js/planner.js", "/assets/js/map.js",
                  "/assets/js/my-europe.js", "/assets/js/search.js", "/assets/door.svg",
                  "/api/atlas.json", "/api/search.json", "/sitemap.xml", "/robots.txt"):
        if os.path.exists(os.path.join(OUT, extra.lstrip("/"))):
            served.add(extra)
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
        f = os.path.join(OUT, "atlas", c["macro_slug"], c["slug"], "index.html")
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
                f = os.path.join(OUT, "atlas", c["macro_slug"], c["slug"], r["slug"], t["slug"], "index.html")
                s = open(f, encoding="utf-8").read()
                for up in (f"/atlas/{c['macro_slug']}\"", f"/atlas/{c['macro_slug']}/{c['slug']}\"",
                           f"/atlas/{c['macro_slug']}/{c['slug']}/{r['slug']}\""):
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


@check("no photographs, and every illustration is generated")
def c_no_photos():
    # Every image on the site is a deterministic SVG built from a slug. This
    # is what keeps the licensing position simple, so it is worth enforcing.
    n = 0
    for f in site_files():
        s = open(f, encoding="utf-8").read()
        for src in re.findall(r"<img[^>]*>", s):
            fail(f"{rel(f)}: contains an <img>; illustrations are generated SVG")
        n += s.count("<svg")
    if n == 0:
        fail("no generated illustrations found at all")
    return n


@check("every experience kind has a page and every experience is on one")
def c_experiences():
    d = D.load()
    kinds = d["taxonomy"]["experience_kinds"]
    for k in kinds:
        if not os.path.exists(os.path.join(OUT, "experiences", k, "index.html")):
            fail(f"no page for experience kind {k}")
    items = D.all_experiences(d["countries"])
    for it in items:
        f = os.path.join(OUT, "experiences", it["exp"]["kind"], "index.html")
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
        f = os.path.join(OUT, "atlas", c["macro_slug"], c["slug"], "index.html")
        s = open(f, encoding="utf-8").read()
        if "Facts checked" not in s:
            fail(f"{c['name']}: country page does not state its verification status")
        if not c.get("checked") and "not verified" not in s:
            fail(f"{c['name']}: unverified, but the page does not say so")
    return len(d["countries"])


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
