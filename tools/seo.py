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
from lib import seo_state as SEO

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


# ── the four groups ───────────────────────────────────────
#
# Each returns a list of (name, ok, blocking) — NAMED signals, so a failure
# says which thing is missing rather than that a number fell. The brief's own
# example reads "✓ Unique geographic identity / ✓ Substantial destination
# information", and a reader of that list can act on it; a reader of "94" has
# to guess.
#
# AND EVERY SIGNAL DECLARES WHAT IT COSTS, BECAUSE THE FIRST VERSION GRADED
# A DISPLAY PREFERENCE AS A REASON TO WITHHOLD A PAGE FROM SEARCH. `verdict`
# treated every technical signal as blocking, so 46 of the 47 pages it held
# back were held for one thing: a description between 166 and 180 characters.
# Those descriptions are whole sentences, inside the tag's own cap, and
# perfectly readable by a crawler — what is "not shown whole" is their tail,
# in a search result, on some devices. HOLD's own definition is a page a
# crawler cannot reach or cannot read, and none of the 46 was either.
#
# Worse, the signal it held them on is the one signal in this file that is
# explicitly a GUESS about a search engine's behaviour: SERP_VISIBLE's own
# comment says it "moves with the device and the query, and it is a claim
# this file makes rather than one the site holds". Grading a page on that is
# "Copenhagen = 94/100" arriving through a named signal — the exact thing the
# no-single-score argument at the top of this file was written against.
#
# THE TEST IS WHICH OF THE BRIEF'S FOUR ACTIONS THE SIGNAL CALLS FOR. A
# signal a writer fixes by writing is ADVISORY and its page is IMPROVE; a
# signal that needs somebody to DECIDE something — which of two pages answers
# a query, whether a page nothing links to should exist, whether an
# unnamed image ships — is BLOCKING and its page is HOLD. Severity lives
# beside the signal rather than in `verdict`, so a group that adds one says
# what it costs in the same line.
BLOCK, ADVISE = True, False


def content_group(url, p, dist, titles, descs):
    """Duplication BLOCKS and thinness ADVISES, and the difference is who acts.

    Two pages carrying one title are two pages competing to be the answer to
    one query, and nothing a writer does to page A settles which of them
    should win — that is a decision about the hierarchy. A page of 80 words
    is a page somebody has not finished writing.
    """
    return [
        ("unique identity", bool(p["h1"]) and titles[p["title"]] == 1, BLOCK),
        ("substantial information", p["words"] >= MIN_WORDS, ADVISE),
        ("distinctive editorial content", dist[url] >= MIN_DISTINCT, ADVISE),
        ("useful visitor context",
         p["words"] >= MIN_WORDS and bool(p["description"]), ADVISE),
        ("own description",
         bool(p["description"]) and descs[p["description"]] == 1, BLOCK),
    ]


def technical_group(url, p, max_kb):
    """AND `indexable` IS NOT IN HERE, BECAUSE IT IS THE OTHER AXIS.

    It used to be, and it was the two axes collapsed into one: `noindex` is
    not a defect a page has, it is a DECISION this atlas has recorded about
    that page in `data/seo.json`. Reading it here graded the site's own
    choice as a fault, so a page deliberately withheld — which the brief
    names as legitimate, LIVE IN EUROPEDOOR + NOINDEX — would have been
    reported as not ready for the search it is being kept out of on purpose.

    Nothing measured moved when it came out, because no route is declared
    noindex today. It is exercised anyway: `--check` asserts the readiness of
    a page does not change when its state does, in memory, which is the one
    thing that could not be true if these two were still one axis.
    """
    want = f"{ORIGIN}{'' if url == '/' else url}"
    return [
        ("canonical", p["canonical"].rstrip("/") == want.rstrip("/"), BLOCK),
        ("structured data", p["jsonld"], BLOCK),
        ("title within length", 0 < len(p["title"]) <= 70, ADVISE),
        ("description likely shown whole",
         R.META_DESC_MIN <= len(p["description"]) <= SERP_VISIBLE, ADVISE),
        ("weight under ceiling", p["bytes"] <= max_kb * 1024, BLOCK),
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
        ("linked from somewhere", n >= MIN_INBOUND, BLOCK),
        ("linked from its parent", bool(parents) or url.count("/") <= 1, BLOCK),
    ]


def media_group(url, p):
    return [
        ("every image is named", p["imgs"] == p["imgs_alt"], BLOCK),
        ("a picture or a drawing", p["imgs"] > 0 or "<svg" in p["html"], BLOCK),
    ]


def verdict(groups):
    """READY, IMPROVE or HOLD — a state, never a number.

    READY means every signal holds. IMPROVE means only ADVISORY signals are
    missing, which is the one case Claude Code can fix by writing. HOLD means
    a BLOCKING signal is missing: something a draft cannot settle, so
    somebody has to decide.

    THE FIRST VERSION SORTED BY GROUP RATHER THAN BY SEVERITY and got this
    backwards for 46 pages — see the comment above `content_group`. Sorting
    by group asks *where does this signal live*, which is a question about
    this file's own filing; sorting by severity asks *who has to act*, which
    is the question the queue exists to answer.
    """
    bad = {g: [n for n, ok, _b in sigs if not ok] for g, sigs in groups.items()}
    blocking = [n for sigs in groups.values() for n, ok, b in sigs if not ok and b]
    if not any(bad.values()):
        return "READY", bad
    return ("HOLD" if blocking else "IMPROVE"), bad


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
            # THE SECOND AXIS, AND IT IS READ RATHER THAN DERIVED. Readiness
            # is a MEASUREMENT of the page; state is the DECISION this atlas
            # has recorded about it in data/seo.json. The Data Integrity Rule
            # written as a queue — never author a measurement, you may
            # author a classification — and the queue is the cross product,
            # because the cell worth looking at is the disagreement.
            "state": SEO.status(url),
            "sitemap": SEO.in_sitemap(url, ready=(v == "READY")),
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
        for name, ok, block in a["groups"][g]:
            mark = "OK " if ok else ("-- " if block else " ~ ")
            print(f"    {mark} {name}{'' if block else '   (advisory)'}")
    print(f"\n  readiness {a['verdict']}   ·   state {a['state'].upper()}"
          f"   ·   {'in' if a['sitemap'] else 'not in'} the sitemap\n")


def family_table(a):
    fam = collections.defaultdict(collections.Counter)
    for url, v in a.items():
        fam[family(url)][v["verdict"]] += 1
    return fam


def missing_table(a):
    miss = collections.Counter()
    for v in a.values():
        for g, names in v["missing"].items():
            for n in names:
                miss[f"{g}: {n}"] += 1
    return miss


# ── the four actions ──────────────────────────────────────────────────
#
# THREE OF THE BRIEF'S FOUR ARE ALREADY MECHANISMS HERE AND BUILDING
# BUTTONS FOR THEM WOULD BE BUILDING TWICE. The brief asks for IMPROVE /
# REVIEW / PUBLISH TO SEARCH / HOLD as back-office actions, and it is right
# that those are the four things anybody does to a page — what it cannot
# know is that this product has no server, no account and no admin surface,
# so an action here is an edit to a file and a commit, not a click.
#
# The value the back office actually adds is the QUEUE: which pages are in
# which cell, and which cells disagree. That is what this table is for, and
# it is printed rather than asserted so a reader of --queue can act on it.
ACTIONS = (
    ("IMPROVE", "edit data/ and rebuild",
     "the queue names the page and the signal; the fix is editorial"),
    ("REVIEW", "the pull request",
     "already the approval boundary — the photograph pipeline uses the same one"),
    ("PUBLISH TO SEARCH", 'data/seo.json → status "published"',
     "it changes search ELIGIBILITY; nothing is submitted to anybody"),
    ("HOLD", 'data/seo.json → status "noindex"',
     "the page stays live in EuropeDoor and leaves the sitemap and the index"),
)


def report(a):
    L = []
    w = L.append
    by = collections.Counter(v["verdict"] for v in a.values())
    states = collections.Counter(v["state"] for v in a.values())
    listed = sum(1 for v in a.values() if v["sitemap"])

    w("# The publishing queue")
    w("")
    w("GENERATED — `python3 tools/seo.py --write`. Do not hand-edit; "
      "`checks.py` fails when this document stops equalling what the "
      "generator produces, exactly as it does for `site/`.")
    w("")
    w("Every page EuropeDoor serves, in two axes: what the readiness "
      "assessment MEASURES about it, and what `data/seo.json` has DECIDED "
      "about it. See `docs/seo-architecture.md` for the layer itself.")
    w("")
    w("## The two axes, and why it is not one column")
    w("")
    w("The brief's queue is READY / NEEDS IMPROVEMENT / PUBLISHED. The "
      "first two are measurements of a page and the third is a decision "
      "about it, so one column cannot hold both: a page can be published "
      "and not ready — the state a governed corpus exists to prevent — "
      "and ready and deliberately withheld, which the brief itself calls "
      "legitimate. **Readiness is derived and may never be authored; state "
      "is authored and may never be derived.**")
    w("")
    # EVERY STATE THE REGISTER DECLARES, NOT EVERY STATE IN USE. A cross
    # product with a row missing is not a cross product, and an empty cell
    # is a measurement: `noindex` reading zero is this atlas saying it
    # withholds nothing, which is a different claim from not saying.
    w("| | " + " | ".join(("READY", "IMPROVE", "HOLD")) + " | all |")
    w("|---|---:|---:|---:|---:|")
    grid = collections.Counter((v["state"], v["verdict"]) for v in a.values())
    for st in SEO.STATUSES:
        row = [str(grid[(st, k)]) for k in ("READY", "IMPROVE", "HOLD")]
        w(f"| **{st}** | " + " | ".join(row) + f" | {states[st]} |")
    w("| **all** | " + " | ".join(str(by[k]) for k in ("READY", "IMPROVE", "HOLD"))
      + f" | {len(a)} |")
    w("")
    w(f"{listed} of {len(a)} routes are in the sitemap, under the "
      f"`{SEO.sitemap_gate()}` gate.")
    w("")

    w("## The four actions, and the mechanism each one already is")
    w("")
    w("Nothing here is a button, because this product has no server, no "
      "account and no admin surface — an action is an edit and a commit. "
      "Three of the four were already mechanisms in this repository before "
      "the brief arrived, so what follows is a map rather than a build.")
    w("")
    w("| action | the mechanism | |")
    w("|---|---|---|")
    for name, how, why in ACTIONS:
        w(f"| **{name}** | {how} | {why} |")
    w("")

    w("## What IMPROVE is waiting on")
    w("")
    w("Every signal that is missing anywhere, with its count. A signal "
      "marked advisory cannot HOLD a page — it is a page somebody has not "
      "finished writing, not a page that is wrong to expose.")
    w("")
    sev = {}
    for v in a.values():
        for g, sigs in v["groups"].items():
            for n, _ok, b in sigs:
                sev[f"{g}: {n}"] = b
    miss = missing_table(a)
    if miss:
        w("| pages | signal | |")
        w("|---:|---|---|")
        for k, n in miss.most_common():
            w(f"| {n} | {k} | {'blocking' if sev.get(k) else 'advisory'} |")
    else:
        w("Nothing is missing on any page.")
    w("")

    w("## By family")
    w("")
    w("| family | pages | READY | IMPROVE | HOLD |")
    w("|---|---:|---:|---:|---:|")
    fam = family_table(a)
    for f in sorted(fam, key=lambda x: (-sum(fam[x].values()), x)):
        c = fam[f]
        w(f"| {f} | {sum(c.values())} | {c['READY']} | {c['IMPROVE']} | "
          f"{c['HOLD']} |")
    w("")

    held = sorted(u for u, v in a.items() if v["verdict"] == "HOLD")
    w("## HOLD")
    w("")
    if held:
        w("A blocking signal is missing on each of these. A page here is "
          "published to search only by a declared decision in "
          "`data/seo.json`, which `checks.py` requires.")
        w("")
        for u in held:
            v = a[u]
            names = ", ".join(n for g in v["missing"] for n in v["missing"][g])
            w(f"- `{u}` — {names}")
    else:
        w("Empty, and measured rather than asserted: no page is missing a "
          "blocking signal. The state is exercised anyway — "
          "`python3 tools/seo.py --check` builds a held page in memory and "
          "reads the verdict back, because *a code path nothing exercises "
          "is a code path nothing checks*.")
    w("")
    return "\n".join(L) + "\n"


def check(a, pages):
    """Three promises, and the first is the governance the brief asks for.

    A check is proved by failing on the thing it is about, and the first
    two here have nothing to fail on today — HOLD is empty and no route is
    declared noindex. So both are exercised against a page built IN MEMORY,
    which is `ad-tests.py`'s own idiom: nothing to restore is stronger than
    restoring carefully.
    """
    bad = []

    # 1. A page the sitemap recommends must not be one the measurement
    #    holds. This is the brief's whole sentence about the sitemap —
    #    *these are the pages we consider genuinely ready*, not all of them.
    for url, v in sorted(a.items()):
        if v["sitemap"] and v["verdict"] == "HOLD":
            names = ", ".join(n for g in v["missing"] for n in v["missing"][g])
            bad.append(f"{url} is in the sitemap and HOLD ({names}) — "
                       f"declare it noindex in data/seo.json or fix the signal")

    # 2. The two axes are separate, proved by moving the one that must not
    #    matter. A readiness that changed when a route was declared noindex
    #    would be the collapse this file's technical_group() docstring
    #    records: the site's own decision graded as a defect.
    #
    #    AND THE FIRST VERSION SWAPPED THE REGISTER AND NOTHING ELSE, which
    #    cannot move a readiness even when the measurement IS reading the
    #    decision: the signal that read it read `p["robots"]`, which comes
    #    off the SHIPPED HTML, and an in-memory register swap does not
    #    rebuild the site. So putting `indexable` back into technical_group
    #    left this green — a check passing for a reason that is not about
    #    the thing, in the run that was proving it red. A declared noindex
    #    produces BOTH a register row and a robots tag, so the probe
    #    produces both.
    probe = sorted(a)[0]
    before = a[probe]["verdict"]
    reg = SEO.registry()
    saved = reg.get("routes", {}).get(probe)
    reg.setdefault("routes", {})[probe] = {"status": "noindex",
                                           "reason": "in-memory probe"}
    try:
        withheld = dict(pages)
        withheld[probe] = dict(pages[probe], robots="noindex,follow")
        after, _ = assess(withheld)
        if after[probe]["verdict"] != before:
            bad.append(f"withholding {probe} from search changed its "
                       f"readiness {before} → {after[probe]['verdict']} "
                       f"— the measurement is reading the decision")
        if after[probe]["sitemap"]:
            bad.append(f"{probe} is declared noindex and still in the sitemap")
    finally:
        if saved is None:
            reg["routes"].pop(probe, None)
        else:
            reg["routes"][probe] = saved

    # 3. HOLD is empty today, so the verdict itself is exercised on a page
    #    this function composes: one signal broken and nothing else.
    #
    #    THE FIRST VERSION HANDED `assess` A ONE-PAGE CORPUS and both cases
    #    came back HOLD — correctly, and for a reason that is not about
    #    either of them: with one page in the dict nothing links to it, so
    #    `linked from somewhere` fails and blocks. The advisory case caught
    #    it, which is the only reason this is a comment rather than a check
    #    that passed while proving nothing. *A test about one signal has to
    #    own the rest of its state*, which is this repository's own recorded
    #    rule about a skip test that inherited the register above it.
    def mutate(**fields):
        corpus = dict(pages)
        corpus[probe] = dict(pages[probe], **fields)
        return assess(corpus)[0][probe]

    if mutate(canonical="https://example.invalid/wrong")["verdict"] != "HOLD":
        bad.append("a page with a broken canonical did not read HOLD — "
                   "the blocking severity is not reaching verdict()")
    if mutate(description="x" * (SERP_VISIBLE + 40))["verdict"] == "HOLD":
        bad.append("an over-long description read HOLD — an advisory "
                   "signal is blocking a page from search")

    for m in bad:
        print(f"  -- {m}")
    print(f"\n{len(a)} pages, {len(bad)} problem(s)")
    return 1 if bad else 0


def floors(a, pages):
    """The distribution each floor was chosen against, printed rather than
    argued. A threshold nobody can see the shape behind is a number."""
    words = sorted(p["words"] for p in pages.values())
    print(f"words: min {words[0]}, p10 {words[len(words)//10]}, "
          f"median {words[len(words)//2]}, max {words[-1]}   "
          f"(MIN_WORDS {MIN_WORDS})")
    d = sorted(v["distinct"] for v in a.values())
    print(f"own sentences: min {d[0]:.2f}, p10 {d[len(d)//10]:.2f}, "
          f"median {d[len(d)//2]:.2f}, max {d[-1]:.2f}   "
          f"(MIN_DISTINCT {MIN_DISTINCT})")
    n = sorted(v["inbound"] for v in a.values())
    print(f"inbound links: min {n[0]}, median {n[len(n)//2]}, max {n[-1]}   "
          f"(MIN_INBOUND {MIN_INBOUND})")
    ln = sorted(len(p["description"]) for p in pages.values())
    print(f"description: min {ln[0]}, median {ln[len(ln)//2]}, max {ln[-1]}   "
          f"(floor {R.META_DESC_MIN}, SERP_VISIBLE {SERP_VISIBLE})")
    return 0


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

    if "--check" in args:
        sys.exit(check(a, pages))
    if "--floors" in args:
        sys.exit(floors(a, pages))

    doc = report(a)
    if "--write" in args:
        out = os.path.join(ROOT, "docs", "seo-queue.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"wrote docs/seo-queue.md ({len(a)} pages)")
        return
    if "--queue" in args:
        print(doc)
        return

    by = collections.Counter(v["verdict"] for v in a.values())
    print(f"{len(a)} pages assessed\n")
    for k in ("READY", "IMPROVE", "HOLD"):
        print(f"  {k:9} {by[k]:5}")
    print(f"\n  in the sitemap  {sum(1 for v in a.values() if v['sitemap']):5}"
          f"   (gate: {SEO.sitemap_gate()})")

    print("\n=== by family ===")
    fam = family_table(a)
    for f in sorted(fam, key=lambda x: -sum(fam[x].values())):
        c = fam[f]
        print(f"  {f:14} {sum(c.values()):5}   READY {c['READY']:4}  "
              f"IMPROVE {c['IMPROVE']:4}  HOLD {c['HOLD']:4}")

    print("\n=== what is missing, across every page ===")
    for k, n in missing_table(a).most_common(20):
        print(f"  {n:5}  {k}")
    print("\n  --queue for the back office, --write to regenerate "
          "docs/seo-queue.md")


if __name__ == "__main__":
    main()
