#!/usr/bin/env python3
"""What is in the dataset, what is missing, and what is stale.

    python3 tools/content-report.py            print it
    python3 tools/content-report.py --write    regenerate docs/content-report.md

The specification asks for an admin dashboard with these numbers on it. An
admin dashboard needs authentication, a backend and a person logged in; this
build has none of those. What it can do is compute the same figures at build
time and publish them, which is most of the value and none of the
infrastructure — and unlike a dashboard, this one is in version control, so
the gaps are visible in a diff.

The targets are the specification's own MVP content targets (§67) and
first-year goals (§92). Reporting the distance to them is the point.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import data as D
from lib import i18n
from lib import urls

TIER_A = ["norway", "france", "italy", "spain", "greece"]

# (label, actual-getter, MVP target from §67, year-one target from §92)
def figures(d):
    places = D.all_places(d["countries"])
    exps = D.all_experiences(d["countries"])
    tier = {s: d["countries"][s] for s in TIER_A}
    return [
        ("Countries", len(d["countries"]), 5, 10),
        ("Travel regions", sum(len(c["regions"]) for c in d["countries"].values()), 50, None),
        ("Destinations", len(d["cities"]), 150, 300),
        ("Places", len(places), 1000, 3000),
        ("Experiences", len(exps), 300, 1000),
        ("Journeys", len(d["journeys"]), 50, 100),
        ("Stories", len(d["stories"]), 100, 500),
        ("Business listings", len(d["providers"]["providers"]), 500, 2000),
    ]


def gaps(d):
    out = {}
    out["countries with no places"] = sorted(
        c["name"] for c in d["countries"].values()
        if not any(t.get("places") for r in c["regions"] for t in r["cities"])
    )
    out["destinations with no experiences and no places"] = sorted(
        f"{t['name']}, {c['name']}"
        for c in d["countries"].values() for r in c["regions"] for t in r["cities"]
        if not t.get("experiences") and not t.get("places")
    )
    out["countries never fact-checked"] = sorted(
        c["name"] for c in d["countries"].values() if not c.get("checked")
    )
    out["cities carrying no curated relationship"] = sorted(
        d["cities"][cid]["city"]["name"] for cid, b in d["back"].items()
        if not (b["journeys"] or b["themes"] or b["stories"])
    )
    # The Build Package v1 §2 fields that are BUILT but not yet filled in.
    # Every one of these is editorial work rather than engineering, and every
    # one is a place where the schema exists and the content does not — which
    # is exactly the state that looks finished from the code and is not. See
    # docs/schema-mapping.md.
    out["destinations with no kind of place recorded"] = sorted(
        f"{t['name']}, {c['name']}"
        for c in d["countries"].values() for r in c["regions"] for t in r["cities"]
        if not t.get("city_type")
    )
    out["experiences not tied to any place (§2.5)"] = sorted(
        f"{e['name']} — {t['name']}"
        for c in d["countries"].values() for r in c["regions"] for t in r["cities"]
        for e in t.get("experiences", []) if not e.get("at")
    )
    out["experiences with no difficulty or season"] = sorted(
        f"{e['name']} — {t['name']}"
        for c in d["countries"].values() for r in c["regions"] for t in r["cities"]
        for e in t.get("experiences", [])
        if not e.get("difficulty") and not e.get("season")
    )
    out["events not tied to a destination (§2.9)"] = sorted(
        f"{f['name']} — {c['name']}"
        for c in d["countries"].values() for f in c.get("festivals", [])
        if not f.get("city")
    )
    out["journey stops naming no place (§2.7)"] = sorted(
        f"{j['name']} — day {leg['day_number']}, {leg['city'].split('/')[-1]}"
        for j in d["journeys"] for leg in j["legs"] if not leg.get("places")
    )
    # A facet type that generates no page anywhere. `food` is one: after the
    # threshold became three for all four, not one destination in 319 has
    # three markets, tables or cellars recorded. The rule is sound and the
    # data is thin, which is an editorial gap and not an engineering one —
    # so it is counted here rather than fixed by lowering the bar until a
    # page appears.
    from lib import pages as P
    seen = set()
    for c in d["countries"].values():
        for r in c["regions"]:
            for t in r["cities"]:
                seen |= set(P.facets_for(d, c, r, t))
    out[f"facet types that generate no page at all (threshold {P.FACET_MIN})"] = sorted(
        name for key, name in urls.FACETS.items() if key not in seen
    )
    return out


def main():
    d = D.load()
    fig = figures(d)
    g = gaps(d)
    lines = []
    w = lines.append

    w("# Content report")
    w("")
    w("**Generated by `python3 tools/content-report.py --write`. Do not edit by hand.**")
    w("")
    w("The specification asks for an admin dashboard carrying these numbers. An admin")
    w("dashboard needs authentication, a backend and somebody logged in. This build has")
    w("none of those, so the same figures are computed at build time and committed —")
    w("which has one advantage a dashboard does not: the gaps show up in a diff.")
    w("")
    w("## Against the specification's own targets")
    w("")
    w("| | now | MVP target (§67) | year one (§92) | |")
    w("|---|---:|---:|---:|---|")
    for label, actual, mvp, year in fig:
        mark = "met" if mvp and actual >= mvp else f"{round(100 * actual / mvp)}% of MVP" if mvp else "—"
        w(f"| {label} | {actual:,} | {mvp or '—'} | {year or '—'} | {mark} |")
    w("")
    w("Two of those gaps are deliberate rather than pending. **Business listings** will")
    w("not be filled by seeding: a directory of businesses that have not claimed their")
    w("entry and cannot be verified is the exact thing this project refuses to publish,")
    w("so that number stays at the illustrative records until operators can claim one.")
    w("**Stories** and **journeys** are editorial work at roughly a day each, and the")
    w("honest position is that they are behind rather than automatable.")
    w("")
    # A TOTAL UNDERSTATES A DENSITY GAP WHENEVER THE DENOMINATOR MET ITS OWN
    # TARGET. Build Package v1 §53 states the seed as a shape rather than a
    # sum — 10 to 30 places and 5 to 15 experiences PER DESTINATION — and
    # this table reported only sums, so "Places: 26% of MVP" was true and
    # read as three-quarters of the way there on the wrong axis: 319
    # destinations (target 150, met) hold 0.8 places each against a floor of
    # 10. And the specification disagrees with itself: §67 asks for 1,000
    # places over 150 destinations, which is 6.7 each and below §53's own
    # floor, so this repository has been reporting against the looser of two
    # numbers the same document publishes.
    dest = len(d["cities"])
    npl, nex = len(D.all_places(d["countries"])), len(D.all_experiences(d["countries"]))
    w("## Against the seed's own shape (Build Package v1 §53)")
    w("")
    w("§53 states the first dataset as a density rather than a total. The two")
    w("framings are not the same claim, and the sums above are the kinder one.")
    w("")
    w("| per destination | now | §53 asks | §67's own sums imply |")
    w("|---|---:|---:|---:|")
    w(f"| Places | {npl / dest:.2f} | 10–30 | {1000 / 150:.1f} |")
    w(f"| Experiences | {nex / dest:.2f} | 5–15 | {300 / 150:.1f} |")
    w("")
    w("Two things follow. **§67 and §53 disagree** — 1,000 places over 150")
    w("destinations is 6.7 each, under §53's floor of ten — so a report against")
    w("§67 alone is a report against the looser of the two. And the gap is")
    w("wider on this axis than on the other:")
    w("")
    w(f"- places are **{round(100 * npl / 1000)}%** of the MVP total and "
      f"**{round(100 * (npl / dest) / 10)}%** of the seed's own floor")
    w(f"- experiences are **{round(100 * nex / 300)}%** of the total and "
      f"**{round(100 * (nex / dest) / 5)}%** of the floor")
    w("")
    w("The destination count met its target and the place count did not, which")
    w("is the whole of the difference: a sum divided by a met denominator")
    w("reads as progress.")
    w("")
    w("Neither number is a code change. Both are the same editorial work the")
    w("sums above describe, counted the way the seed counts it.")
    w("")
    w("## Where the dataset is thin")
    w("")
    for name, items in g.items():
        w(f"### {name.capitalize()} — {len(items)}")
        w("")
        if not items:
            w("None.")
        elif len(items) > 24:
            w(", ".join(items[:24]) + f", and {len(items) - 24} more.")
        else:
            w(", ".join(items) + ".")
        w("")
    w("## Interface translation")
    w("")
    w("| language | coverage | ships |")
    w("|---|---:|---|")
    for r in i18n.report():
        w(f"| {r['lang']} | {r['coverage']*100:.0f}% | {'yes' if r['ships'] else 'held'} |")
    w("")
    w("A catalogue ships at 100% of the interface **and** localised destination copy.")
    w("A half-translated site is worse than an English one.")
    w("")

    text = "\n".join(lines)
    if "--write" in sys.argv:
        with open(os.path.join(D.ROOT, "docs", "content-report.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote docs/content-report.md")
    else:
        print(text)


if __name__ == "__main__":
    main()
