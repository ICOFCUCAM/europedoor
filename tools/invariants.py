#!/usr/bin/env python3
"""The invariant register: what must NOT move while something else does.

    python3 tools/invariants.py --write    measure and record
    python3 tools/invariants.py --check    recompute and compare

A visual migration is a controlled experiment, and an experiment needs a
control. This is it: the things that were true before the change and must
still be true after it. Not "we intend to keep these" — recomputed on every
build, and the build stops when one moves.

The distinction that makes it useful is the KIND of each invariant:

    exact    it must equal this. A second page shell, a sixth application.
    ceiling  it must not exceed this. Font sizes, breakpoints, shadows.
    floor    it must not fall below this. A primitive's reach across pages.

A ceiling is not a target. Thirteen font sizes is not a goal to defend to the
death; it is a line that should only be crossed on purpose, in a diff somebody
reads. Updating this file IS the deliberate act — which is why the register
records a `why` for every row: an invariant you cannot explain is one nobody
can decide to change.

Not everything checkable belongs here. This register holds the things a
VISUAL change could plausibly break while looking like it worked, because
those are the ones that get discovered late and by somebody else.
"""

import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
REG = os.path.join(ROOT, "docs", "invariants.json")


def _css():
    """The stylesheet as the browser sees it — comments stripped.

    THE REGISTER COUNTED A TYPE SIZE THAT EXISTED ONLY IN A COMMENT ABOUT
    NOT ADDING TYPE SIZES. `css.font_sizes` matches `font-size:\s*([^;]+);`
    across the whole file, and this stylesheet's whole style is long comments
    naming the failure that prompted each rule — so a comment saying "the
    first version wrote `font-size: 26px` and the register caught it" WAS a
    seventeenth font size, and the ceiling failed on prose.
    
    It can only ever inflate a count, never hide one, so nothing measured
    before this was too permissive. But an instrument that reads its own
    documentation as code is wrong, and this file's rules all count things in
    the CSS the browser actually applies.
    """
    css = open(os.path.join(ROOT, "assets", "css", "europedoor.css"),
               encoding="utf-8").read()
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _size_of(value):
    """The type size a declaration states, with the --z compensation removed.

    See css.font_sizes below. This normalises only the exact shape
    `calc(X / var(--z))`, which is the map-label compensation and nothing
    else: a real new size still counts as one, and that is proved both ways
    in the same commit.
    """
    m = re.match(r"^calc\(\s*(.+?)\s*/\s*var\(--z\)\s*\)$", value.strip())
    return m.group(1) if m else value.strip()


def _pages():
    return sorted(glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True))


def _reachable():
    """How many of the declared motifs any destination actually draws."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from lib import data as D                                      # noqa: E402
    from lib import render as R                                    # noqa: E402
    d = D.load()
    seen = set()
    for node in d["cities"].values():
        t, r = node["city"], node["region"]
        seen.add(R.motif_for(t["interests"], t.get("city_type"))
                 or R.motif_for(r["interests"]))
    return len(seen & set(R.MOTIFS))


def measure():
    css = _css()
    pages = _pages()
    bodies = {p: open(p, encoding="utf-8").read() for p in pages}

    routes = sorted("/" + os.path.relpath(p, OUT).replace("index.html", "").rstrip("/")
                    for p in pages)
    route_hash = hashlib.sha256("\n".join(routes).encode()).hexdigest()[:16]

    prim_floor = {}
    for prim in ("kicker", "masthead", "pagehead", "crumbs", "row", "card",
                 "band", "note", "facts", "btn", "chip"):
        # \b is the wrong boundary for a CSS class name, because a hyphen is
        # a word boundary: `\bcard\b` matched `class="card-art frame"`, and
        # `\brow\b` matches `rowsub` and `rowmeta`. The card floor of 0.785
        # was therefore ~30% satisfied by an image wrapper on the 319
        # destination pages, and the day that wrapper was renamed the floor
        # fell through the floor. A class token ends at whitespace or the
        # quote, never at a hyphen.
        hit = sum(1 for b in bodies.values()
                  if re.search(r'class="[^"]*(?<![\w-])' + prim + r'(?![\w-])', b))
        prim_floor[prim] = round(hit / len(pages), 3)

    apps, enh = [], []
    for js in sorted(glob.glob(os.path.join(ROOT, "assets", "js", "*.js"))):
        body = open(js, encoding="utf-8").read()
        (apps if ("fetch(" in body or "localStorage" in body) else enh).append(
            os.path.basename(js))

    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from lib import render as R                                    # noqa: E402

    return {
        "$comment": "GENERATED by tools/invariants.py --write. The control for "
                    "every visual experiment: what must not move while "
                    "something else does. `kind` is exact / ceiling / floor. "
                    "Changing a value here is the deliberate act — do it in a "
                    "commit that says why.",
        "invariants": {
            "routes.count": {
                "value": len(pages), "kind": "exact",
                "why": "A visual change must not add or remove a page. If this "
                       "moves during a restyle, something is generating pages "
                       "from a stylesheet, which is a different kind of bug."},
            "routes.hash": {
                "value": route_hash, "kind": "exact",
                "why": "A visual change must not move a URL. Every inbound link, "
                       "every social card and every sitemap entry depends on "
                       "this set being stable."},
            "shell.count": {
                "value": sum(open(os.path.join(ROOT, "tools", "lib", f),
                                  encoding="utf-8").read().count("<!doctype html>")
                             for f in ("render.py", "pages.py")),
                "kind": "exact",
                "why": "One function emits <html>. A second is how a masthead "
                       "comes to exist twice and diverges within a month."},
            "shell.mastheads_per_page": {
                "value": max(b.count('class="masthead"') for b in bodies.values()),
                "kind": "exact",
                "why": "Exactly one, on every page."},
            "shell.footers_per_page": {
                "value": max(b.count("<footer") for b in bodies.values()),
                "kind": "exact", "why": "Exactly one, on every page."},
            "css.stylesheets": {
                "value": len(glob.glob(os.path.join(ROOT, "assets", "css", "*.css"))),
                "kind": "exact",
                "why": "One stylesheet. Two is how a design system forks."},
            "css.font_families": {
                "value": len(re.findall(r"--(?:display|text|mono):", css)),
                "kind": "exact",
                "why": "Three: a display serif, a system sans, a mono."},
            "css.webfonts": {
                "value": len(re.findall(r"@font-face|fonts\.googleapis|fonts\.gstatic", css)),
                "kind": "exact",
                "why": "Zero. A webfont is a third-party origin, a render delay "
                       "and a hole in default-src 'none'. 2036 does not require "
                       "a new typeface."},
            "css.font_sizes": {
                # A COMPENSATION CONSTANT FOR A COORDINATE SYSTEM IS NOT A
                # TYPE SIZE, and the stylesheet has said so since the map
                # labels were fixed: `calc(11px / var(--z))` draws an 11px
                # label at the scale the viewBox is being drawn at. Counting
                # it as its own size made the register fail on the commit
                # that gave the physical map labels the same compensation the
                # place names already had — a fix that adds no size, refused
                # by an instrument reading the arithmetic instead of the
                # value. Dividing by --z is normalised away; 17 becomes 15,
                # because `calc(11px / var(--z))` was itself being counted
                # separately from the `11px` it is.
                "value": len({_size_of(v) for v in
                              re.findall(r"font-size:\s*([^;]+);", css)}),
                "kind": "ceiling",
                "why": "A ceiling, not a target. The sibling repository measures "
                       "418; that is what happens without a line. It moved to "
                       "16 for the essay hed, and for nothing else: the design "
                       "audit's central finding is that eleven of twelve "
                       "rendered families place an identically-sized h1 at an "
                       "identical vertical position, and no size that already "
                       "existed could stop that. The same commit's other five "
                       "candidate type values — a serif leading, a tighter "
                       "hed, a deck clamp one decimal off one already in the "
                       "file — were snapped back to what the site had, and no "
                       "reader could name the difference."},
            "css.font_weights": {
                "value": len(set(re.findall(r"font-weight:\s*([^;]+);", css))),
                "kind": "ceiling", "why": "Four is enough for an editorial system."},
            "css.line_heights": {
                "value": len(set(re.findall(r"line-height:\s*([^;]+);", css))),
                "kind": "ceiling", "why": "Four."},
            "css.breakpoints": {
                "value": len(set(re.findall(
                    r"@media[^{]*\(m(?:in|ax)-width:\s*([^)]+)\)", css))),
                "kind": "ceiling",
                "why": "Six. Every one is a layout somebody has to test in "
                       "Chromium at two viewports."},
            "css.shadows": {
                "value": len(set(re.findall(r"box-shadow:\s*([^;]+);", css))),
                "kind": "ceiling", "why": "Two: a rest state and a lifted one."},
            "css.gold": {
                "value": len([h for h in re.findall(r"#[0-9a-fA-F]{6}", css)
                              if 90 <= int(h[1:3], 16) <= 215
                              and abs(int(h[1:3], 16) - int(h[3:5], 16)) < 55
                              and int(h[3:5], 16) - int(h[5:7], 16) > 45
                              and int(h[1:3], 16) - int(h[5:7], 16) > 70]),
                "kind": "exact",
                "why": "Zero. Gold says luxury, premium, wealth; this product "
                       "has to say Europe, discovery, movement, intelligence."},
            "js.applications": {
                "value": len(apps), "kind": "exact",
                "why": "Five. An application fetches an index or owns client "
                       "state and must declare its dependencies."},
            "js.enhancements": {
                "value": len(enh), "kind": "exact",
                "why": "Scripts that do neither and work on markup already in "
                       "the page."},
            "safety.inline_styles": {
                "value": sum(len(re.findall(r'\sstyle="', b)) for b in bodies.values()),
                "kind": "exact",
                "why": "Zero. One style attribute forces style-src open on "
                       "every page, and CSP hashes do not apply to them."},
            "safety.inline_style_blocks": {
                "value": sum(b.count("<style") for b in bodies.values()),
                "kind": "exact", "why": "Zero. A page may not ship its own CSS."},
            "safety.img_tags": {
                "value": sum(b.count("<img") for b in bodies.values()),
                "kind": "exact",
                "why": "Zero today, because zero photographs are licensed. This "
                       "moving is the signal that licensed imagery arrived — "
                       "which must go through the licence register first."},
            # The homepage is the flagship page and the one most likely to
            # gain weight, because every good idea wants to live on it. It
            # already carried a 2.6x regression unnoticed: a commit that cut
            # it from eight bands to three also inlined 90 KB of coastline
            # under the hero and shipped at 118,935 bytes while reporting
            # 45,806. Thirty-five static checks, 652 browser checks and
            # twenty-two invariants said nothing, because not one of them
            # measured bytes.
            "weight.home_kb": {
                "value": round(len(next(b for k, b in bodies.items()
                                       if os.path.relpath(k, OUT) == "index.html")) / 1024),
                "kind": "ceiling",
                "why": "The homepage's rendered HTML in KB. A ceiling, not a "
                       "target: it is allowed to move, deliberately, in a diff "
                       "somebody reads. It is here because a 2.6x regression on "
                       "this page passed every other gate in silence. "
                       "119 -> 146 ON PURPOSE: the body was eight abstract "
                       "plates over 'Find your kind of Europe' and three more "
                       "over the journeys — eleven purple gradients in a "
                       "column under an atlas hero, which is placeholder art "
                       "doing a picture's job, and the plate system was "
                       "already measured as unable to carry a hero. Each tile "
                       "now draws its OWN destinations lit on one shared "
                       "silhouette: Mountains is the Alps, the Pyrenees, the "
                       "Carpathians and the Scandes; History is almost the "
                       "whole continent; and that difference is what the tile "
                       "exists to say. The plates cost 14.7 KB and came out; "
                       "894 dots and one lod0 coastline went in. All of them "
                       "and never a selection, so the count on the tile is the "
                       "number of dots on it and a reader can check."},
            "weight.max_page_kb": {
                "value": round(max(len(b) for b in bodies.values()) / 1024),
                "kind": "ceiling",
                "why": "The heaviest page on the site. Guards against a template "
                       "quietly inlining something large across a whole family, "
                       "which is how the coastline reached 51 pages and 2.1 MB."},
            # A CEILING, not a floor, and the direction is the point. The
            # rule is that a visual earns its position — so what needs
            # guarding is plates SPREADING back onto pages that do not need
            # one, not plates being removed. 319 destination pages dropped
            # theirs when the map alone was measured to be the stronger
            # page, and nothing in the suite noticed until this row existed.
            # THE SIGNATURE, COUNTED. The arch is the one thing that should
            # make a screenshot recognisable with the wordmark cropped off,
            # and a signature that is not measured is a signature that
            # quietly stops being applied to the next family somebody adds.
            # RELIEF IS ALLOWED WHERE THE GROUND EARNED IT, AND A FLOOR IS
            # THE CONTROL ON BOTH DIRECTIONS OF DRIFT. Up, because an
            # elevation model in the repository is a standing invitation to
            # put terrain on everything and end up with a topographic Paris.
            # Down, because the layer is derived through six stages — a
            # fingerprint, a measurement, two thresholds, a frame cap and a
            # clip — and any one of them silently returning nothing looks
            # exactly like a page that was always flat. `gathers` shipped at
            # zero for a build once for that reason.
            "map.relief_pages": {
                "value": sum(1 for b in bodies.values()
                             if 'class="lyr lyr-terrain"' in b),
                "kind": "floor",
                "why": "Pages that draw hypsometric relief. Every one of them "
                       "is a destination or a journey whose own ground was "
                       "measured past both thresholds; see "
                       "docs/terrain-prototype.md. A floor rather than an "
                       "exact, because adding an Alpine destination should "
                       "not need a ceremony — but losing them all should."},
            "signature.apertures": {
                "value": sum(1 for b in bodies.values() if 'clip-path="url(#arch-' in b),
                "kind": "floor",
                "why": "Pages whose geography is seen through the arch. A floor: "
                       "the aperture is the identity, and a new map that forgets "
                       "it is a page that stops looking like EuropeDoor."},
            "plates.page_share": {
                "value": round(sum(1 for b in bodies.values()
                                   if re.search(r'class="[^"]*(?<![\w-])plate(?![\w-])', b))
                               / len(pages), 3),
                "kind": "ceiling",
                "why": "The share of pages carrying a generated illustration. A "
                       "ceiling because the failure mode is an illustration "
                       "placed because the system has one, which is the one "
                       "reason the art direction forbids."},
            "plates.motifs_declared": {
                "value": len(R.MOTIFS), "kind": "exact",
                "why": "Seven declared."},
            "plates.motifs_reachable": {
                "value": _reachable(), "kind": "exact",
                "why": "Seven drawn. `plain` was declared and never reached for "
                       "the life of the plate system, because food -> plain sat "
                       "below eight interests almost every European destination "
                       "carries. A motif nothing reaches is dead code that looks "
                       "like vocabulary."},
            "primitives.reach": {
                "value": prim_floor, "kind": "floor",
                "why": "The share of pages each primitive appears on. A family "
                       "that quietly stops using one has grown its own "
                       "components and the design system has forked without "
                       "anybody deciding — which is the failure this floor "
                       "exists to catch. A family that stops using one ON "
                       "PURPOSE is the other thing that moves it, and the "
                       "difference is whether the drop is recorded here in the "
                       "same commit with the composition that caused it. The "
                       "essay family cost pagehead, row and band about a "
                       "hundredth each: nine story pages that no longer share "
                       "the atlas chassis, which is the whole point of them. "
                       "THESE NUMBERS WERE WRONG UNTIL THE DESTINATION "
                       "EXEMPLAR: the matcher used \\b, and a hyphen is a word "
                       "boundary, so `card` counted `card-art` and `row` "
                       "counted `rowsub`. The card floor read 0.785 and the "
                       "true figure is 0.226 — the most-cited primitive in the "
                       "design system was three-quarters an image wrapper. "
                       "AND THE EXPERIENCE EXEMPLAR MOVED THREE OF THEM ON "
                       "PURPOSE. Forty-eight category pages and ten kind "
                       "pages stopped using `row`, `card` and `band`: the "
                       "list of experiences was a four-column table built "
                       "from `row`, the sub-categories were four `card`s "
                       "holding a count and a name and nothing else, and "
                       "\"How this list is built\" was a `band` standing in "
                       "front of the list it described. An experience is an "
                       "invitation and the writing is the picture, so the "
                       "rows became `.invites` — a two-column editorial list "
                       "with no card, no border and no plate — the four "
                       "empty cards became four links, and the rule moved "
                       "under the list it proves. row 0.899 to 0.855, card "
                       "0.233 to 0.227, band 0.767 to 0.759. "
                       "AND THE THREE INDEX EXEMPLARS MOVED IT AGAIN, ON "
                       "PURPOSE. Eight of the nine indexes were the same "
                       "280px card grid — the h1 finding one level up, "
                       "recorded in docs/design-direction-audit.md. A card "
                       "is the right shape for a set of like things chosen "
                       "on LOOK. A journey is chosen on where it goes, a "
                       "motion is a query, and a theme is chosen on how far "
                       "it reaches: none of the three is a look. /journeys "
                       "became rows carrying the stops in order and each "
                       "route's own legs end to end; /europe-in became the "
                       "twelve queries printed as queries, generated by the "
                       "same function the twelve pages use; and /themes "
                       "became rows carrying the eight destinations and the "
                       "count of countries, because \"8 PLACES\" was on all "
                       "thirteen cards and every theme holds exactly eight. "
                       "Three pages stopped using card and started using "
                       "row: card 0.227 to 0.225. "
                       "AND THE NAV-BAR PASS TOOK THE LAST BIG CARD GRID: "
                       "/experiences was eighteen identical bordered tiles in "
                       "two grids of four, and border, fill, radius and shadow "
                       "spent on every tile of an eighteen-tile page separate "
                       "nothing — the grid read as one texture while the thing "
                       "that tells the rows apart, that Family holds 131 "
                       "entries and Luxury holds 5, was four characters of "
                       "kicker type. The count is the subject, so the count is "
                       "drawn: rows with the figure and a proportional bar, "
                       "reusing `hopbar` and the .w0-.w100 scale rather than "
                       "inventing a third bar. Each bar is against the largest "
                       "in its own group and not the total, because an "
                       "experience carries one kind and any number of "
                       "categories — ten kinds sum to 197 and eight categories "
                       "sum to 493 memberships over the same 197, so a share "
                       "of the whole would read 250% down one column. card "
                       "0.225 to 0.224. "
                       "AND THE STAY EXEMPLAR COST `note` ONE PAGE. Chamonix's "
                       "accommodation section was a `.note` panel saying "
                       "EuropeDoor lists neither hotels nor restaurants; it is "
                       "now an editorial reading and a referral, and a panel "
                       "around a commercial link is a banner. One page of "
                       "1,033: note 0.824 to 0.823. The other 318 destinations "
                       "keep the note, and this figure is the one to watch when "
                       "the grammar propagates — it should fall to about 0.5 "
                       "and that will be the deliberate act, not a drift. "
                       "THE SECOND WAVE TOOK IT AGAIN, 0.823 to 0.820: Vienna, "
                       "Naxos and Ortisei, chosen to execute the branches "
                       "Chamonix could not — a flat capital where the ground "
                       "decides nothing, an island, and a valley. Four of 319 "
                       "covered. "
                       "AND THE REASON FOR THE SECOND OF THOSE WAS WRITTEN "
                       "INTO THE GENERATED REGISTER AND WIPED BY THE NEXT "
                       "--write. docs/invariants.json is generated exactly "
                       "like site/, so a reason typed into it survives only "
                       "until somebody regenerates and is then gone with no "
                       "failing check — the same class as editing a page in "
                       "site/. A reason belongs HERE, in the source the "
                       "register is written from. "
                       "AND THE HOMEPAGE ENTRANCE TOOK BOTH, ON PURPOSE: card "
                       "0.224 to 0.223 and note 0.820 to 0.819, one page each. "
                       "The homepage was eight `card` tiles each drawing the "
                       "same beige silhouette with different blue dots, above "
                       "three more on the journeys — eleven maps before a "
                       "reader had experienced anything, which turned the "
                       "signature into background noise and made the labels "
                       "too small to read. It is four type-led doors, three "
                       "journey rows carrying a route that is legible, and a "
                       "story lead now; the closing `note` of counts became an "
                       "editorial statement, because a row reading `319 "
                       "destinations · 17 journeys · 50 countries` is the "
                       "database introducing itself and it was the last thing "
                       "on the page. The counts are still there, in the quiet "
                       "line, where they are true and checkable and no longer "
                       "the argument."},
        },
    }


def main(argv):
    got = measure()
    if "--write" in argv:
        with open(REG, "w", encoding="utf-8") as fh:
            json.dump(got, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {REG} — {len(got['invariants'])} invariants")
        return 0

    if not os.path.exists(REG):
        print("docs/invariants.json is missing — run --write")
        return 1
    with open(REG, encoding="utf-8") as fh:
        want = json.load(fh)["invariants"]
    bad = 0
    for name, spec in sorted(want.items()):
        now = got["invariants"].get(name, {}).get("value")
        exp, kind = spec["value"], spec["kind"]
        if kind == "floor" and isinstance(exp, dict):
            for k, v in exp.items():
                if now.get(k, 0) < v:
                    print(f"FAIL {name}.{k}: {now.get(k)} is below the recorded "
                          f"floor {v} — {spec['why']}")
                    bad += 1
        elif kind == "ceiling":
            if now > exp:
                print(f"FAIL {name}: {now} exceeds the recorded ceiling {exp} — "
                      f"{spec['why']}")
                bad += 1
        elif now != exp:
            print(f"FAIL {name}: {now!r}, recorded {exp!r} — {spec['why']}")
            bad += 1
    if bad:
        print(f"\n{bad} invariant(s) moved. If that was deliberate, run "
              f"tools/invariants.py --write in the same commit and say why.")
        return 1
    print(f"all {len(want)} invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
