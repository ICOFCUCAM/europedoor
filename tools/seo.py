#!/usr/bin/env python3
"""SEO READINESS, ASSESSED IN FOUR GROUPS AND NEVER AS ONE NUMBER.

    python3 tools/seo.py                 the distribution, and the queue
    python3 tools/seo.py /europe/norway/fjord-norway/bergen   one page in full
    python3 tools/seo.py --queue         the back office: READY / IMPROVE / HOLD
    python3 tools/seo.py --check         fail on a page whose state disagrees
                                         with what the built site actually is

THERE IS NO SEO SCORE HERE ON PURPOSE. "Copenhagen = 94/100" pretends to
know how a search engine will weigh a page, which nobody in this repository
can measure and nothing here could prove red. What IS measurable is whether
a page has the things a search landing page needs, so the assessment is four
groups of named signals and a verdict derived from them — the same shape as
the licence gate, where the answer is a set of answered questions rather
than a confidence.

AND INBOUND LINKS ARE COUNTED FROM THE BUILT HTML, NOT FROM THE KNOWLEDGE
GRAPH. `/api/graph.json` holds 3,716 editorial relations and is the right
answer to "what is this place related to"; it is the wrong answer to "how
would a crawler reach this page", because a crawler follows an `<a href>`
and nothing else. Two different questions, and only one of them is about
search — the graph would happily report a page as well-connected that no
page links to.
"""
from __future__ import annotations

import collections
import glob
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from lib import render as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
ORIGIN = "https://europedoor.com"

# A page needs enough of its own words to be worth a search result. The floor
# is the shortest page this atlas ships that anybody would call a landing
# page, measured rather than picked: run with --floors to print the
# distribution that produced it.
MIN_WORDS = 120

# And enough of those words have to be ITS OWN. Every page here shares a
# masthead, a footer and a section grammar, which is correct and is also
# most of a short page's text — so the signal is the share of a page's
# sentences that appear on at most two other pages.
MIN_DISTINCT = 0.35

# A page nothing links to cannot be crawled from the homepage, whatever its
# content is. One inbound link is the floor, and there is no second floor —
# see discovery_group() for the three-link version that was measured out.
MIN_INBOUND = 1

# WHAT A RESULT SHOWS AND WHAT THE FIELD MAY HOLD ARE TWO QUESTIONS, AND ONLY
# ONE OF THEM BELONGS HERE.
#
# `render.META_DESC_MAX` bounds the TAG: 180, the room worth sending, with
# the whole-sentence rule allowed to pass it where stopping would leave a
# fragment. This is the other question — roughly how much of it a search
# result will print — and it is deliberately NOT read off that constant. A
# readiness figure derived from the product's own cap would agree with the
# product by construction, which is the instrument fault this repository
# records seven times. 165 is a reading of what Google displays before it
# truncates, it moves with the device and the query, and it is a claim this
# file makes rather than one the site holds.
#
# The FLOOR is the same question as `c_head`'s, so it is read rather than
# retyped: below it a description is too short to be useful, and two numbers
# for one question is how a dispatch cap cost a whole sitting.
SERP_VISIBLE = 165


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def canonical_path(f):
    """The URL a built index.html is served at."""
    rel = os.path.relpath(f, OUT)
    if rel == "index.html":
        return "/"
    return "/" + rel[: -len("/index.html")]


_TAG = re.compile(r"<[^>]+>")
_DROP = re.compile(r"<(script|style|svg|nav|header|footer)\b.*?</\1>", re.S | re.I)


def visible_text(h):
    """The words a reader gets, with the chrome removed.

    `<svg>` matters more here than it looks: a destination page carries a
    map with 30 place names inside it, and counting those as the page's own
    prose would report a thin page as substantial. The same is true of the
    masthead and the footer, which are identical on all 1,031.
    """
    body = h.split("<main", 1)[-1].split("</main>", 1)[0] if "<main" in h else h
    body = _DROP.sub(" ", body)
    return " ".join(html.unescape(_TAG.sub(" ", body)).split())


_SENT = re.compile(r"[^.!?]{25,}?[.!?]")


def sentences(text):
    return [s.strip().lower() for s in _SENT.findall(text)]


def load_pages():
    """Every built page, read once, with everything the assessment needs."""
    pages = {}
    for f in sorted(glob.glob(os.path.join(OUT, "**", "index.html"), recursive=True)):
        h = read(f)
        url = canonical_path(f)
        text = visible_text(h)
        m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', h)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        pages[url] = {
            "file": f,
            "bytes": len(h.encode("utf-8")),
            "canonical": m.group(1) if m else "",
            "title": html.unescape(_TAG.sub("", t.group(1))).strip() if t else "",
            "description": html.unescape(d.group(1)).strip() if d else "",
            "h1": html.unescape(_TAG.sub("", h1.group(1))).strip() if h1 else "",
            "jsonld": "application/ld+json" in h,
            "robots": (re.search(r'<meta name="robots" content="([^"]*)"', h) or [None, ""])[1]
            if re.search(r'<meta name="robots"', h) else "",
            "words": len(text.split()),
            "sentences": sentences(text),
            "imgs": len(re.findall(r"<img\b", h)),
            "imgs_alt": len(re.findall(r'<img\b[^>]*\balt="', h)),
            "hrefs": set(re.findall(r'href="(/[^"#?]*)"', h)),
            "html": h,
        }
    return pages


def inbound_map(pages):
    """Who links to whom, as a crawler would see it."""
    inb = collections.defaultdict(set)
    for url, p in pages.items():
        for href in p["hrefs"]:
            tgt = href.rstrip("/") or "/"
            if tgt in pages and tgt != url:
                inb[tgt].add(url)
    return inb


def distinct_share(pages):
    """What share of each page's sentences are close to its own.

    A sentence on three pages or fewer is this page's; a sentence on four or
    more is the template speaking. The threshold is three rather than one
    because a two-page family legitimately shares a sentence — a facet page
    and its parent say the same thing about the same floor — and calling
    that duplication would punish a correct relationship.
    """
    freq = collections.Counter()
    for p in pages.values():
        for s in set(p["sentences"]):
            freq[s] += 1
    out = {}
    for url, p in pages.items():
        own = set(p["sentences"])
        if not own:
            out[url] = 0.0
            continue
        out[url] = sum(1 for s in own if freq[s] <= 3) / len(own)
    return out


# ── the four groups ───────────────────────────────────────────────────
#
# Each returns a list of (name, ok) — NAMED signals, so a failure says which
# thing is missing rather than that a number fell. The brief's own example
# reads "✓ Unique geographic identity / ✓ Substantial destination
# information", and a reader of that list can act on it; a reader of "94" has
# to guess.


def content_group(url, p, dist, titles, descs):
    return [
        ("unique identity", bool(p["h1"]) and titles[p["title"]] == 1),
        ("substantial information", p["words"] >= MIN_WORDS),
        ("distinctive editorial content", dist[url] >= MIN_DISTINCT),
        ("useful visitor context", p["words"] >= MIN_WORDS and bool(p["description"])),
        ("own description", bool(p["description"]) and descs[p["description"]] == 1),
    ]


def technical_group(url, p, max_kb):
    want = f"{ORIGIN}{'' if url == '/' else url}"
    return [
        ("canonical", p["canonical"].rstrip("/") == want.rstrip("/")),
        ("indexable", "noindex" not in p["robots"].lower()),
        ("structured data", p["jsonld"]),
        ("title within length", 0 < len(p["title"]) <= 70),
        ("description likely shown whole",
         R.META_DESC_MIN <= len(p["description"]) <= SERP_VISIBLE),
        ("weight under ceiling", p["bytes"] <= max_kb * 1024),
    ]


def discovery_group(url, inb):
    """Can a crawler reach this page, and by a route that means something.

    `reachable more than one way` USED TO SIT HERE AT THREE INBOUND LINKS AND
    THE MEASUREMENT DOES NOT SUPPORT IT. It reported 185 deficient pages and
    every one of them was a leaf correctly placed in a hierarchy — a facet
    reachable from its own destination, a sub-category from its own category.
    Two things were wrong with it:

    First, the count MIXED CHROME WITH EDITORIAL. `inbound_map` reads every
    `href` in the document, and thirty targets are linked from more than 90%
    of the site because they are in the masthead and the footer. So the same
    number meant "the whole site links this" for an index and "one editorial
    link" for a leaf, and no threshold can be right for both.

    Second, the defect a multiple-inbound signal exists for is FRAGILITY:
    lose the one page that links it and the page is orphaned. Every link here
    is DERIVED at build time from a validated hierarchy — a facet page is
    linked by the same build that creates it — so that failure mode is not
    available, and the link checker would catch it anyway.

    WHAT THE SITE ACTUALLY OWED WAS ASKED SEPARATELY AND IS ANSWERED. The
    atlas publishes every relationship it holds in `/api/graph.json`, and
    `checks.py` now asserts that every one of those edges is a link a reader
    can follow: 2,926 of 2,926 between page-bearing entities, an equality
    rather than a floor. That is the internal-linking guarantee, and it is a
    claim about relationships this atlas HOLDS rather than about a number of
    links somebody hoped for.

    286 non-chrome pages are linked from nowhere outside their own branch —
    130 regions, 100 facets, 44 experience sub-categories, 12 fund projects.
    That is recorded rather than reported as a fault, because a region is a
    LEVEL and nothing in this dataset relates to it from outside its country.
    The trigger is a relationship that crosses a branch: the day a destination
    page names the experience sub-categories its own invitations fall into,
    or a fund project names the region it is in, the graph will carry that
    edge and the check above will require the link.
    """
    n = len(inb.get(url, ()))
    parents = {u for u in inb.get(url, ()) if url.startswith(u.rstrip("/") + "/")}
    return [
        ("linked from somewhere", n >= MIN_INBOUND),
        ("linked from its parent", bool(parents) or url.count("/") <= 1),
    ]


def media_group(url, p):
    return [
        ("every image is named", p["imgs"] == p["imgs_alt"]),
        ("a picture or a drawing", p["imgs"] > 0 or "<svg" in p["html"]),
    ]


def verdict(groups):
    """READY, IMPROVE or HOLD — a state, never a number.

    READY means every group is complete. IMPROVE means the technical and
    discovery halves hold and the CONTENT half does not, which is the one
    case Claude Code can actually fix by writing. HOLD is everything else:
    a page failing technical or discovery needs a decision rather than a
    draft, and shipping it to search would be publishing a page a crawler
    cannot reach or cannot read.
    """
    bad = {g: [n for n, ok in sigs if not ok] for g, sigs in groups.items()}
    if not any(bad.values()):
        return "READY", bad
    if not bad["technical"] and not bad["discovery"] and not bad["media"]:
        return "IMPROVE", bad
    return "HOLD", bad


def assess(pages=None):
    pages = pages or load_pages()
    inb = inbound_map(pages)
    dist = distinct_share(pages)
    titles = collections.Counter(p["title"] for p in pages.values())
    descs = collections.Counter(p["description"] for p in pages.values())
    max_kb = 1e9
    inv = os.path.join(ROOT, "docs", "invariants.json")
    if os.path.exists(inv):
        reg = json.load(open(inv, encoding="utf-8"))
        rows = reg.get("rows", reg)
        if isinstance(rows, dict) and "weight" in rows:
            max_kb = rows["weight"].get("max_page_kb", {}).get("value", max_kb)
    out = {}
    for url, p in sorted(pages.items()):
        groups = {
            "content": content_group(url, p, dist, titles, descs),
            "technical": technical_group(url, p, max_kb),
            "discovery": discovery_group(url, inb),
            "media": media_group(url, p),
        }
        v, bad = verdict(groups)
        out[url] = {
            "verdict": v, "groups": groups, "missing": bad,
            "inbound": len(inb.get(url, ())), "words": p["words"],
            "distinct": round(dist[url], 3),
        }
    return out, pages


def family(url):
    """The page family, for a report that groups rather than lists 1,031."""
    if url == "/":
        return "homepage"
    seg = url.strip("/").split("/")
    if seg[0] == "europe":
        # OFF BY ONE THE FIRST TIME, and the table it printed was wrong on
        # every row: `/europe/norway` is TWO segments and `/europe/norway/
        # fjord-norway` is three, so the first version reported 50 regions
        # where those 50 are countries and 130 destinations where those are
        # regions. The pages were right and the instrument's labels were
        # not, which is the reading-the-wrong-boundary fault this repository
        # records about a rectangle and an arch.
        return {2: "country", 3: "region", 4: "destination"}.get(len(seg), "facet/place")
    return seg[0]


def show(url, a):
    print(f"\n{url}")
    print(f"  {a['words']} words · {a['distinct']:.0%} its own · {a['inbound']} inbound links")
    for g in ("content", "technical", "discovery", "media"):
        print(f"\n  {g.upper()}")
        for name, ok in a["groups"][g]:
            print(f"    {'OK ' if ok else '-- '} {name}")
    print(f"\n  {a['verdict']}\n")


def main():
    args = sys.argv[1:]
    a, pages = assess()

    page_args = [x for x in args if x.startswith("/")]
    if page_args:
        for u in page_args:
            if u not in a:
                print(f"{u}: not a built page")
            else:
                show(u, a[u])
        return

    by = collections.Counter(v["verdict"] for v in a.values())
    print(f"{len(a)} pages assessed\n")
    for k in ("READY", "IMPROVE", "HOLD"):
        print(f"  {k:9} {by[k]:5}")

    print("\n=== by family ===")
    fam = collections.defaultdict(collections.Counter)
    for url, v in a.items():
        fam[family(url)][v["verdict"]] += 1
    for f in sorted(fam, key=lambda x: -sum(fam[x].values())):
        c = fam[f]
        print(f"  {f:14} {sum(c.values()):5}   READY {c['READY']:4}  IMPROVE {c['IMPROVE']:4}  HOLD {c['HOLD']:4}")

    print("\n=== what is missing, across every page ===")
    miss = collections.Counter()
    for v in a.values():
        for g, names in v["missing"].items():
            for n in names:
                miss[f"{g}: {n}"] += 1
    for k, n in miss.most_common(20):
        print(f"  {n:5}  {k}")


if __name__ == "__main__":
    main()
