#!/usr/bin/env python3
"""Build EuropeDoor.

    python3 tools/build.py            # build the site into site/
    python3 tools/build.py check      # validate the data, render nothing
    python3 tools/build.py stats      # what is in the dataset

Everything is generated. There is no page in site/ that a human edited, and
there must never be one: the whole directory is deleted and rewritten on
every build, so a hand edit would vanish without a warning. If a page needs
to say something new, it says it in tools/lib/pages.py or in data/.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D
from lib import pages as P
from lib import render as R
from lib import urls

ROOT = D.ROOT
OUT = os.path.join(ROOT, "site")


def write(path, content):
    full = os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)


def build():
    d = D.load()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    written = []

    def emit(pair):
        path, html = pair
        write(path, html)
        written.append(path)

    emit(P.home(d))
    emit(P.discover_page(d))
    emit(P.countries_index(d))
    for m in d["macros"]:
        emit(P.macro_page(d, m))
    for c in d["countries"].values():
        emit(P.country_page(d, c))
        for r in c["regions"]:
            emit(P.region_page(d, c, r))
            for t in r["cities"]:
                emit(P.city_page(d, c, r, t))
                for pl in t.get("places", []):
                    emit(P.place_page(d, c, r, t, pl))
                for key, payload in P.facets_for(d, c, r, t).items():
                    emit(P.facet_page(d, c, r, t, key, payload))
    for i in d["taxonomy"]["interests"]:
        emit(P.interest_page(d, i))
    emit(P.journeys_index(d))
    for j in d["journeys"]:
        emit(P.journey_page(d, j))
    emit(P.themes_index(d))
    for t in d["themes"]:
        emit(P.theme_page(d, t))
    emit(P.stories_index(d))
    for s in d["stories"]:
        emit(P.story_page(d, s))
    emit(P.planner_page(d))
    emit(P.search_page(d))
    emit(P.experiences_index(d))
    for kind, name in d["taxonomy"]["experience_kinds"].items():
        emit(P.experience_kind_page(d, kind, name))
    for cat in d["categories"]:
        emit(P.category_page(d, cat))
        for sub in cat.get("subs", []):
            emit(P.category_page(d, cat, sub))
    emit(P.join_page(d))
    emit(P.business_page(d))
    emit(P.fund_index(d))
    for p in d["fund"]:
        emit(P.fund_page(d, p))
    emit(P.map_page(d))
    emit(P.events_page(d))
    for month in d["taxonomy"]["months"]:
        emit(P.events_month_page(d, month))
    emit(P.quiet_page(d))
    emit(P.my_europe_page(d))
    emit(P.method_page(d))
    emit(P.about_page(d))
    emit(P.how_it_works_page(d))
    emit(P.sources_page(d))
    emit(P.api_page(d))
    emit(P.manifesto_page(d))
    emit(P.motion_index(d))
    for m in d["motions"]:
        emit(P.motion_page(d, m))
    emit(P.freshness_page(d))
    emit(P.privacy_page(d))
    emit(P.cookies_page(d))
    emit(P.terms_page(d))
    emit(P.accessibility_page(d))
    emit(P.help_page(d))
    emit(P.contact_page(d))
    emit(P.tourism_boards_page(d))
    emit(P.not_found(d))

    for path, payload in (P.planner_api(d), P.search_api(d),
                          P.countries_api(d), P.journeys_api(d), P.graph_api(d)):
        write(path, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    # Static assets are copied, never symlinked: the output directory has to
    # stand up on its own on any static host.
    for sub in ("css", "js"):
        src = os.path.join(ROOT, "assets", sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(OUT, "assets", sub))
    shutil.copy(os.path.join(ROOT, "assets", "door.svg"), os.path.join(OUT, "assets", "door.svg"))

    # The map geometry. Published under /api/geo/ rather than /assets/ because
    # it is data the page fetches, not an asset the page references, and
    # because the two directories get different Cache-Control: geometry that
    # changes when Natural Earth ships a release should not be immutable for a
    # year. The continent file is already inline in /map, so nothing here is
    # needed for the map to draw — these are the detail levels a browser asks
    # for when somebody zooms into a country. With JavaScript off none of them
    # is ever requested and the map still works.
    geo_src = os.path.join(ROOT, "data", "geo")
    geo_n = 0
    if os.path.isdir(geo_src):
        for root, _dirs, names in os.walk(geo_src):
            for name in sorted(names):
                if not name.endswith(".json"):
                    continue
                rel = os.path.relpath(os.path.join(root, name), geo_src)
                dst = os.path.join(OUT, "api", "geo", rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(os.path.join(root, name), dst)
                geo_n += 1

    canonical = [
        "/" if p == "/index.html" else p[: -len("index.html")].rstrip("/")
        for p in written
        if p.endswith("index.html")
    ]
    write("/sitemap.xml", P.sitemap(canonical))
    # ── social cards ─────────────────────────────────────────────────
    #
    # Deterministic, content-addressed, and cached in assets/og/ because they
    # cost ~23 ms each and change only when the plate algorithm does. The key
    # is a hash of exactly the inputs that determine the picture, so a change
    # to any of them produces a new filename and the old one is pruned below.
    #
    # Pruning matters: without it the cache becomes a directory of orphans
    # from every past version of the drawing, and nobody can tell which are
    # live. Anything no page asked for this build is deleted.
    from lib import raster
    og_dir = os.path.join(ROOT, "assets", "og")
    os.makedirs(og_dir, exist_ok=True)
    wanted = R.OG_WANTED
    made = 0
    for key, (seed, motif) in sorted(wanted.items()):
        cached = os.path.join(og_dir, key + ".png")
        if not os.path.exists(cached):
            shapes = R.plate_shapes(seed, R.OG_W, R.OG_H, motif)
            with open(cached, "wb") as fh:
                fh.write(raster.plate_png(shapes, R.OG_W, R.OG_H))
            made += 1
    pruned = 0
    for fn in sorted(os.listdir(og_dir)):
        if fn.endswith(".png") and fn[:-4] not in wanted:
            os.remove(os.path.join(og_dir, fn))
            pruned += 1
    os.makedirs(os.path.join(OUT, "assets", "og"), exist_ok=True)
    for key in wanted:
        shutil.copy(os.path.join(og_dir, key + ".png"),
                    os.path.join(OUT, "assets", "og", key + ".png"))

    write("/_headers", R.headers_file())
    # vercel.json is not generated — it carries redirects and caching rules a
    # human edits — but its security headers ARE checked against
    # render.HEADERS by tools/checks.py, because the host reads that file and
    # not site/_headers.
    write("/robots.txt", "User-agent: *\nAllow: /\nSitemap: https://europedoor.com/sitemap.xml\n")

    card_note = f", {len(wanted)} cards"
    if made or pruned:
        card_note += f" ({made} rendered, {pruned} pruned)"
    print(f"{len(written)} pages + api + sitemap{card_note} + {geo_n} geometry files → site/")
    return d, written


def stats():
    d = D.load()
    ncountry = len(d["countries"])
    nregion = sum(len(c["regions"]) for c in d["countries"].values())
    ncity = len(d["cities"])
    nexp = len(D.all_experiences(d["countries"]))
    nplace = len(D.all_places(d["countries"]))
    print(f"countries   {ncountry}")
    print(f"regions     {nregion}")
    print(f"cities      {ncity}")
    print(f"places      {nplace}")
    print(f"experiences {nexp}")
    print(f"journeys    {len(d['journeys'])}")
    print(f"themes      {len(d['themes'])}")
    print(f"stories     {len(d['stories'])}")
    print(f"fund        {len(d['fund'])}")
    advisory = [c["name"] for c in d["countries"].values() if c.get("advisory")]
    print(f"advisory    {len(advisory)}: {', '.join(advisory) or '—'}")


def strings_report():
    """Which languages exist, how complete each is, and which would ship."""
    from lib import i18n
    print("interface string catalogues\n")
    for r in i18n.report():
        mark = "ships" if r["ships"] else "held"
        print(f"  {r['lang']:<4} {r['coverage']*100:5.1f}%  {r['have']:>3}/{r['total']:<3} {mark}")
    print("\n  A catalogue ships at 100% of the interface AND localised destination copy.")
    print("  Half-translated pages are worse than English ones; see docs/product-specification.md.")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "check":
        D.load()
        print("data ok")
    elif cmd == "stats":
        stats()
    elif cmd == "strings":
        strings_report()
    elif cmd == "build":
        build()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
