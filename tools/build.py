#!/usr/bin/env python3
"""Build Europedoor.

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
    emit(P.atlas(d))
    for m in d["macros"]:
        emit(P.macro_page(d, m))
    for c in d["countries"].values():
        emit(P.country_page(d, c))
        for r in c["regions"]:
            emit(P.region_page(d, c, r))
            for t in r["cities"]:
                emit(P.city_page(d, c, r, t))
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
    emit(P.freshness_page(d))
    emit(P.not_found(d))

    for path, payload in (P.planner_api(d), P.search_api(d)):
        write(path, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    # Static assets are copied, never symlinked: the output directory has to
    # stand up on its own on any static host.
    for sub in ("css", "js"):
        src = os.path.join(ROOT, "assets", sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(OUT, "assets", sub))
    shutil.copy(os.path.join(ROOT, "assets", "door.svg"), os.path.join(OUT, "assets", "door.svg"))

    canonical = [
        "/" if p == "/index.html" else p[: -len("index.html")].rstrip("/")
        for p in written
        if p.endswith("index.html")
    ]
    write("/sitemap.xml", P.sitemap(canonical))
    write("/robots.txt", "User-agent: *\nAllow: /\nSitemap: https://europedoor.com/sitemap.xml\n")

    print(f"{len(written)} pages + api + sitemap → site/")
    return d, written


def stats():
    d = D.load()
    ncountry = len(d["countries"])
    nregion = sum(len(c["regions"]) for c in d["countries"].values())
    ncity = len(d["cities"])
    nexp = len(D.all_experiences(d["countries"]))
    print(f"countries   {ncountry}")
    print(f"regions     {nregion}")
    print(f"cities      {ncity}")
    print(f"experiences {nexp}")
    print(f"journeys    {len(d['journeys'])}")
    print(f"themes      {len(d['themes'])}")
    print(f"stories     {len(d['stories'])}")
    print(f"fund        {len(d['fund'])}")
    advisory = [c["name"] for c in d["countries"].values() if c.get("advisory")]
    print(f"advisory    {len(advisory)}: {', '.join(advisory) or '—'}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "check":
        D.load()
        print("data ok")
    elif cmd == "stats":
        stats()
    elif cmd == "build":
        build()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
