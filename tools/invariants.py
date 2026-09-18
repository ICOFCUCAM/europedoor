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


def _ochre():
    """The golds the palette register declares, as a lookup.

    THE EXCLUSION IS A LOOKUP, NEVER A SHAPE — the sentence this repository
    already wrote about the credential scan. Loosening the gold arithmetic
    until ochre passed would loosen it until a brass passed too, so the
    arithmetic is untouched and the register names which golds are the
    territorial accent.
    """
    pal = json.load(open(os.path.join(ROOT, "docs", "palette.json"),
                         encoding="utf-8"))
    return {t["hex"].lower() for name, t in pal["tokens"].items()
            if name.startswith("ochre")}


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
    # AND THE 2036 SYSTEM'S OWN PRIMITIVES ARE TRACKED HERE TOO, from the
    # commit that introduced them. A migration moves reach from one set to
    # another, and a register that counts only the set being LEFT reads every
    # step of it as a loss — so the eight families' grammar has a floor of
    # its own and the two numbers can be read against each other. `ed-row`
    # and `row` are both counted: a page that moved is one that fell on the
    # first list and rose on the second, and a page that simply stopped
    # listing anything falls on both, which is the failure this exists to
    # catch and the only reading the old register could not tell apart.
    for prim in ("kicker", "masthead", "pagehead", "crumbs", "row", "card",
                 "band", "note", "facts", "btn", "chip",
                 "ed-opening", "ed-section", "ed-row", "ed-eyebrow",
                 "ed-photo", "ed-split"):
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
                       "from a stylesheet, which is a different kind of bug."
                       " AND THE INTERESTS INDEX ADDED ONE PAGE, 1033 -> 1034. /interests was a "
                       "SERVER AUTOINDEX: seventeen interest pages shipped and "
                       "their directory had no index.html, so a reader who "
                       "trimmed a URL got a file listing with none of this site "
                       "on it. Nothing linked to it, which is exactly why no "
                       "check caught it — a link checker validates links that "
                       "exist and a missing index is an absence. It cost "
                       "something real too: every interest page draws its own "
                       "tag and says it does so \"so the seventeen can be "
                       "compared\", and there was nowhere they could be. The "
                       "index is that comparison, ordered by reach."
                       "  1034 -> 1032 WHEN A SUB-CATEGORY HAD TO EARN ITS "
                       "PAGE. FACET_MIN is three and its reason is that below "
                       "it a page is a heading over a list a reader could have "
                       "seen in full on the page they came from - exactly true "
                       "of a sub-category, whose parent lists every invitation "
                       "it holds. Two of the twenty-eight shipped ONE row, and "
                       "the smaller was worse than thin: /experiences/nature/"
                       "fjords declares fjord, inlet, calanque, ria and sea "
                       "loch, NO experience in this atlas mentions a fjord at "
                       "all, and the page called Fjords held Marseille. "
                       "Removing a URL is the deliberate act this row exists to "
                       "make visible, and nothing is orphaned: every entry it "
                       "selected is already on the parent page."},
            "routes.hash": {
                "value": route_hash, "kind": "exact",
                "why": "A visual change must not move a URL. Every inbound link, "
                       "every social card and every sitemap entry depends on "
                       "this set being stable."
                       " AND THE INTERESTS INDEX ADDED ONE PAGE, 1033 -> 1034. /interests was a "
                       "SERVER AUTOINDEX: seventeen interest pages shipped and "
                       "their directory had no index.html, so a reader who "
                       "trimmed a URL got a file listing with none of this site "
                       "on it. Nothing linked to it, which is exactly why no "
                       "check caught it — a link checker validates links that "
                       "exist and a missing index is an absence. It cost "
                       "something real too: every interest page draws its own "
                       "tag and says it does so \"so the seventeen can be "
                       "compared\", and there was nowhere they could be. The "
                       "index is that comparison, ordered by reach."
                       "  1034 -> 1032 WHEN A SUB-CATEGORY HAD TO EARN ITS "
                       "PAGE. FACET_MIN is three and its reason is that below "
                       "it a page is a heading over a list a reader could have "
                       "seen in full on the page they came from - exactly true "
                       "of a sub-category, whose parent lists every invitation "
                       "it holds. Two of the twenty-eight shipped ONE row, and "
                       "the smaller was worse than thin: /experiences/nature/"
                       "fjords declares fjord, inlet, calanque, ria and sea "
                       "loch, NO experience in this atlas mentions a fjord at "
                       "all, and the page called Fjords held Marseille. "
                       "Removing a URL is the deliberate act this row exists to "
                       "make visible, and nothing is orphaned: every entry it "
                       "selected is already on the parent page."},
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
                # AND 18 IS FOR THE COUNT ON THE ATLAS PLATE. The homepage
                # is a plate sequence now, and its fifth plate makes the
                # number of countries the single largest typographic event
                # on the site: `50` set at clamp(5rem, 11vw, 11rem) beside
                # `European countries.` at a third of it. That contrast IS
                # the plate — a tracked 11px label against a 176px numeral
                # is the editorial rhythm the design direction asked for,
                # and it is the one value on this page that no existing step
                # reaches: --t-6xl is 4.75rem, less than half of it.
                #
                # Every other new declaration on that page was made to reuse
                # a clamp that already existed rather than invent one, which
                # is why this moved by one rather than by six: the first
                # version of the sequence declared six bespoke clamps and
                # the register was right to refuse them.
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
                       "418; that is what happens without a line. "
                       "IT IS 17 FOR THE PLACE PAGE'S PHONE HEAD, and that is "
                       "the one case where the ceiling should move rather than "
                       "the design: a place name is routinely a single long "
                       "compound noun — Kunsthistorisches, Jugendstilsenteret, "
                       "Elbphilharmonie — and at the overture's own floor it "
                       "does not fit a phone, so four of them were cut in half "
                       "mid-word. `min-width: min-content` fixes the box and "
                       "not the screen; the only sizes already declared that "
                       "fit are 24px, which is a section head, on the family "
                       "whose whole role is that the name is the event. The "
                       "value is an existing STEP of the scale (--t-2xl) "
                       "declared in a new place, not a seventeenth step. "
                       "It was 16 for "
                       "the essay hed and for nothing else: the design audit's "
                       "central finding is that eleven of twelve rendered "
                       "families place an identically-sized h1 at an identical "
                       "vertical position, and no size that already existed "
                       "could stop that. "
                       "AND FOR TWO COMMITS THIS REASON WAS TRUE OF NOTHING. "
                       "The value was snapped back to 15 and the hed was left "
                       "declaring `clamp(--t-3xl, 5.2vw, --t-5xl)` — the base "
                       "h1 rule copied out character for character, a "
                       "declaration restating what the element already "
                       "inherits, which is the redundancy the dead-rule scan "
                       "exists to find. The one difference the family claimed "
                       "did nothing, and this register carried the argument "
                       "for a size that was not being spent. The hed takes the "
                       "--t-6xl ceiling now and the sixteenth size is real: a "
                       "story title is a SENTENCE where an overture's is a "
                       "name, so it cannot borrow the hero clamp the overture "
                       "borrowed, and every other value in the rule — the "
                       "5.2vw rate, the 1.12 leading, the -.022em — is the "
                       "site\'s own. The same commit\'s first version also "
                       "moved the leading to 1.06 and the rate to 6.2vw; both "
                       "went red here, both were wrong, and both came out."
                       " AND IT IS 22 FOR THE 2036 PAGE SYSTEM: four "
                       "values for eight page families. The brief writes nine "
                       "clamps, one per component, each a few pixels from its "
                       "neighbour, and nine arbitrary clamps is a second type "
                       "scale wearing the first one's clothes — which is how "
                       "the sibling repository reached 418. --ed-display-1 is "
                       "every opening, every hero and every institutional head; "
                       "--ed-display-2 is every section title, split and arrival; "
                       "--ed-display-3 is every row and route stop; --ed-read is "
                       "the standfirst under all of them. A system is what a set "
                       "of components have in COMMON, not what each of them "
                       "declares, and the two bare steps the first draft also "
                       "spent were folded in rather than counted — the second "
                       "of them a narrow-screen override restating what its own "
                       "clamp already computes at that width.\n"
                       "AND IT IS 23 FOR THE DOOR'S HEADLINE, WHICH IS A STEP "
                       "OF THE SCALE RATHER THAN A SHARE OF THE VIEWPORT. "
                       "Every other plate headline is clamp(--t-4xl, 7vw, "
                       "--t-6xl), which is right for type that owns the page "
                       "width; the door's sits in a fixed column beside the "
                       "atlas, so at 1280 the 7vw term is 90px and \"Open the "
                       "door\" measures 500 against 432 — the line broke after "
                       "\"the\" and left \"door\" alone. A smaller clamp only "
                       "moves the width at which that happens: 5.2vw fits at "
                       "1280 and breaks again at 1600. A column that is a "
                       "fixed measure needs type that is a fixed step, and "
                       "--t-5xl is a rung the scale already has — an existing "
                       "STEP declared in a new place, which is the argument "
                       "the 24px entry above makes, not a twenty-third step.\n"
                       "AND 24 FOR THE TWO LEADS. Plates 03 and 06 each became "
                       "a composition with a subject — one destination at "
                       "feature size beside four rows, one essay at lead size "
                       "above a contents list — and a lead needs a size "
                       "between the section head above it and the rows beside "
                       "it or it is not leading anything. --t-3xl is the rung "
                       "the scale already has there and was already spent as "
                       "the FLOOR of three clamps; this is the same value "
                       "declared bare, in two rules, and not a new step. The "
                       "alternative was --t-2xl, which is the size of the "
                       "rows themselves — a lead the same size as the list it "
                       "leads is the card grid these two plates stopped "
                       "being."},
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
                "kind": "ceiling",
                "why": "Two, and THE REASON HERE USED TO DESCRIBE A "
                       "VOCABULARY THIS STYLESHEET DOES NOT HAVE. It said "
                       "'a rest state and a lifted one', and there is no "
                       "rest state: nothing on this site carries a shadow "
                       "until it is hovered. A --shadow token was declared "
                       "in all three world blocks and referenced by no rule "
                       "for the life of the palette. The two values this "
                       "counts are --shadow-lift and an inset 1.5px ring, "
                       "which is a focus outline rather than a shadow. A "
                       "count can be right while the sentence under it is "
                       "wrong, and the sentence is what the next person "
                       "reads."},
            "css.gold": {
                "value": len([h for h in re.findall(r"#[0-9a-fA-F]{6}", css)
                              if 90 <= int(h[1:3], 16) <= 215
                              and abs(int(h[1:3], 16) - int(h[3:5], 16)) < 55
                              and int(h[3:5], 16) - int(h[5:7], 16) > 45
                              and int(h[1:3], 16) - int(h[5:7], 16) > 70
                              and h.lower() not in _ochre()]),
                "kind": "exact",
                "why": "Zero golds OUTSIDE the declared ochre family, which "
                       "is not the same row it was. It counted every gold and "
                       "read zero, because European Future had none; the "
                       "owner's palette then named ochre #C49A52 as the "
                       "TERRITORIAL accent for the regions and the events "
                       "calendar, so three arrived at once and the honest "
                       "reading is 3, not a moved ceiling. Recording 3 would "
                       "put a number here and no rule: a fourth gold pasted "
                       "in would keep it at 3 only by luck. So the count is "
                       "of golds the register does not declare, it stays at "
                       "zero, and the register is where a new one has to be "
                       "argued for. Gold still says luxury, premium, wealth; "
                       "what changed is that a ground and a kicker on two "
                       "families is not a gold button, and the two brasses "
                       "#8a6d34 and #c2a165 stay out by value."},
            "css.lime": {
                "value": len(re.findall(r":\s*#c8ff4d", css, re.I))
                         + len(re.findall(r"--lime:", css)),
                "kind": "exact",
                "why": "Zero. Electric lime was the dark world's accent and it "
                       "ended up drawing geography — seventeen journey routes, "
                       "894 homepage dots, 319 destinations, 172 experiences "
                       "and every lit country on every region glyph. An accent "
                       "is five per cent of a screen and a continent is not. "
                       "Removed rather than rehomed, like the brass, and the "
                       "letters are counted in a DECLARATION only, because "
                       "--lime is a prefix of --limestone and the note "
                       "recording why it went names the hex."},
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
                "why": "AND /countries SPENT THE NINE MACRO PHOTOGRAPHS AND TEN APERTURES, 1196 -> 1205. The register holds a photograph of every one of the fifty countries, one of each of the nine macro regions and the index's own hero — sixty pictures relevant to this page — and the page drew ONE. The nine macro photographs each appeared on exactly one page, their own, while the band whose whole subject is those nine regions drew none of them. Nine came on here; the ten country apertures are SVG `<image>` rather than `<img>` and this figure does not count them. Nothing was acquired. AND /stories SPENT THE SEVEN IT ALREADY HELD, "
                       "1189 -> 1196. The index drew one `<img>` while the "
                       "register held eight for it — `stories-hero` and "
                       "seven `story:` rows — which is the /experiences "
                       "finding on the family whose material is writing: "
                       "the pictures were already bought and were being "
                       "spent on one surface. Nothing was acquired. "
                       "AND /events SPENT ONE MORE, 1205 -> 1206. The Calendar Atlas's "
                       "shoulder band carries `The case for going in October` with "
                       "the photograph the register already holds for it, because "
                       "the argument that band makes is the one that essay makes "
                       "and a generic autumn landscape standing in for a sentence "
                       "is this site's oldest rule about pictures and stories. One "
                       "photograph, on the page whose subject it argues, linked to "
                       "the piece it belongs to. Nothing was acquired. "
                       "AND /interests SPENT EVERY PHOTOGRAPH THIS FAMILY HAS, "
                       "1206 -> 1215. The register holds one for each of the "
                       "seventeen tags and one for the index — eighteen — and "
                       "the page drew nine: a hero and a strip of the widest "
                       "eight. The nine it did not draw were the NARROW end, "
                       "which is the half this page argues is the useful one, "
                       "so the family had a picture of everything it says is "
                       "too broad to filter by and none of what it recommends. "
                       "All eighteen are on it now, each exactly once, and the "
                       "three scales they are drawn at are `INTEREST_BANDS` — "
                       "the judgement this family already publishes on all "
                       "seventeen of its own pages. Nothing was acquired. "
                       "AND /europe-in DREW NONE AND DRAWS ELEVEN, "
                       "1215 -> 1226. A MOTION MAY NOT HAVE A PHOTOGRAPH OF "
                       "ITS OWN and the register rightly declares no "
                       "`motion:` purpose: a motion has no coastline, no "
                       "topography and no season, so a picture of one is a "
                       "picture of nowhere — the refusal that took twelve "
                       "plates off this index. What it CAN spend is a "
                       "photograph of a destination the query returned, and "
                       "the pick is derived: a member on its OWN tags rather "
                       "than its region's, then the one whose tag list is "
                       "most nearly just what the query asks for, so the "
                       "picture is of this cut rather than of Europe. Two "
                       "orderings were measured and both first attempts were "
                       "wrong — by region-propagated membership it picked "
                       "Nicosia, which is inland, for the coastlines and "
                       "Tartu, a mainland town, for the islands; by "
                       "specificity alone it picked Baku for the medieval "
                       "world, whose registered photograph is the Flame "
                       "Towers. By tag share it is Mostar, Blagaj and "
                       "Kuressaare. Eleven of the twelve "
                       "have one; `by-rail` has twenty results and none "
                       "photographed, so it shows its slot. Nothing was "
                       "acquired. "
                       "AND IT WENT DOWN, 1149 -> 1143, WHICH IS THE SAME "
                       "SIGNAL READ BACKWARDS. The homepage's eight-plate "
                       "rebuild replaced a row of eleven theme thumbnails "
                       "with five destinations and three journeys, so six "
                       "`<img>` left the most-seen page. A ceiling would have "
                       "said nothing; an exact says a picture stopped being "
                       "drawn and asks whether that was meant. It was. "
                       "It was zero while zero photographs were licensed, and "
                       "this moving is the signal that licensed imagery arrived "
                       "— which must go through the licence register first. "
                       "20 -> 31 WHEN THE ELEVEN THEME PHOTOGRAPHS STOPPED "
                       "APPEARING ON ELEVEN PAGES: they are the only pictures "
                       "this atlas holds and they were each on their own page "
                       "and nowhere else, so an index of thirteen things a "
                       "reader chooses between on LOOK showed thirteen "
                       "drawings. No photograph was acquired for this; the "
                       "same eleven register rows are spent on one more "
                       "surface, which is the whole of the change. "
                       "31 -> 34 WHEN THE HOMEPAGE STOPPED SHOWING EIGHT OF "
                       "ELEVEN. Plate 02's row was capped at eight by a "
                       "`[:8]` written when eight was the whole register and "
                       "the grid was eight fixed tracks, so Grand Tour, "
                       "Modernist and Thermal were dropped by data order with "
                       "nothing on the page saying so — a selection wearing "
                       "the clothes of a set. Again no photograph was "
                       "acquired: three rows already in the register reach "
                       "one more surface. "
                       "1179 -> 1189 WHEN THE JOURNEY ATLAS SPENT TEN "
                       "ROWS THE REGISTER ALREADY HELD. Nothing was "
                       "acquired. /journeys drew one photograph and "
                       "draws ten: the featured route's lead and three "
                       "of its stops, the essays that name a place "
                       "these routes pass through, and `journeys-hero` "
                       "on the close — which the register had been "
                       "claiming for a surface the page stopped "
                       "reaching the moment its opening became the "
                       "drawn continent, and `c_photo_published` said "
                       "so in the first run after the rebuild. "
                       "1143 -> 1145 WHEN THE HOMEPAGE'S GALLERY GREW BY "
                       "TWO. The door's panel gave its photograph back to the "
                       "window on plate 02 and the map took its place, and "
                       "plate 03 went from four destinations to five — one "
                       "per macro region, which is the rule the band already "
                       "had and not a number anybody picked. Every one of "
                       "those is a register row this library already holds; "
                       "nothing was acquired for it. "
                       "1145 -> 1144 WHEN THE READING BECAME A CONTENTS PAGE. "
                       "It showed two of nine stories as two photographs side "
                       "by side — a card grid, and a selection wearing the "
                       "clothes of a set. The newest carries the one picture "
                       "and every other story is a line, so all nine are on "
                       "the page where two were, for one `<img>` fewer. A "
                       "contents page that illustrated every line would be "
                       "the grid again with smaller pictures. "
                       "1151 -> 1179 WHEN /experiences BECAME THE EXPERIENCE "
                       "ATLAS. Twenty-eight photographs on one page: the "
                       "opening, ten destinations down the kind index, four "
                       "under `same feeling`, eight categories, ten in the "
                       "strip and three stories — and NOT ONE WAS ACQUIRED "
                       "FOR IT. The register held all of them and the page "
                       "before this spent exactly one, on a head, with a "
                       "strip of eight under it. The standing answer to why a "
                       "travel site has so few pictures is the library, and "
                       "this is the one page where that was not the "
                       "constraint: the pictures were already bought. "
                       "1144 -> 1151 WHEN /discover ANSWERED ITS OWN "
                       "QUESTION IN PICTURES. The instrument re-lit the "
                       "continent and then handed the reader a list of "
                       "names: a map says WHERE and it cannot say what a "
                       "place is like, which is the one thing somebody who "
                       "has just chosen `Mountains` wants to know. Seven "
                       "destinations, one per macro region that holds a "
                       "licensed photograph, and the tiles carry the same "
                       "`data-city` the dots do so a place that drops out "
                       "of the chosen set goes quiet rather than away. "
                       "Nothing was acquired for it: seven register rows "
                       "this library already holds reach one more surface, "
                       "and the number is seven rather than nine because "
                       "two corners of the continent hold no photograph "
                       "yet — which the lede states rather than implies."},
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
                "why": "AND 147 -> 129 WHEN THE HOMEPAGE STOPPED SHIPPING A CONTINENT IT NEVER DREW. `constel_defs()` inlines one thinned lod0 silhouette so that thirteen glyphs cost ONE coastline, and the homepage referenced neither id it provides — it draws its hero from `#heroland` and its own `#lz-*` rings. 18,806 bytes, 12% of the most-visited page on the site, for the life of the plate sequence. Sixteen pages had it: /themes at 37%, /experiences, /plan, nine macro pages and three motion pages, about 301 KB in all. Nineteen call sites emit the defs and TWO of them guard the call, which is the fourteen-call-sites-forgot-the-motif shape exactly — so the strip is in `page()`, where a caller cannot get half of it right because a caller no longer does any of it, and `c_unused_geometry` fails on any page that emits the block and clones it zero times. A ceiling going DOWN is a saving being locked in: this number exists because a page once shipped 90 KB of coastline under a map and every gate stayed green. "
                       "57 -> 68 FOR THE EIGHT-PLATE REBUILD, and eleven KB "
                       "of it is one drawing. The graphite atlas plate puts "
                       "the real continent and all 319 destinations on the "
                       "page, which is the band's whole argument — the map "
                       "is the navigation layer and the photographs are the "
                       "emotional one, so the map has to be a map rather "
                       "than a picture of one. The photographs cost almost "
                       "nothing by comparison: a `<picture>` is a few "
                       "hundred bytes of markup whatever the file weighs.\n"
                       "The homepage's rendered HTML in KB. A ceiling, not a "
                       "target: it may move, deliberately, in a diff "
                       "somebody reads. It is here because a 2.6x "
                       "regression on this page passed every other gate "
                       "in silence.\n"
                       "  25 -> 109  the drawn hero: Europe on its own "
                       "conic, relief, rivers, the ground beyond.\n"
                       "  119 -> 146 eleven abstract plates out, the "
                       "data in: every destination carrying each tag.\n"
                       "  121 -> 136 the four doors got their drawing "
                       "back; 146 -> 122 when they became photograph "
                       "slots sized to their content.\n"
                       "  122 -> 123 the Atom feed, declared in the one "
                       "function that emits <head>.\n"
                       "  123 -> 129 the body glyphs got a cartography: "
                       "water, frontiers, and the land beyond the 52°E "
                       "cut so the continent stops ending in a "
                       "knife-straight diagonal through Russia. 5 KB of "
                       "anonymous rings, emitted once and cloned by "
                       "every glyph on the page.\n"
                       "  129 -> 130 the homepage journey rows got the stops "
                       "in order and the trip's rhythm bar.\n"
                       "  141 -> 146 plate 02 stopped showing eight of the "
                       "eleven licensed theme photographs and the tiles grew "
                       "from 134px to 182px. Three more <picture> ladders is "
                       "the whole of it; the pictures themselves are files a "
                       "reader fetches, not bytes in this document. A page "
                       "whose brief is more photography paying five "
                       "kilobytes of markup for three more photographs is "
                       "the trade this ceiling exists to make visible rather "
                       "than to forbid.\n"
                       "  68 -> 152 THE HERO IS THE ATLAS AGAIN, at the "
                       "owner's direction, and it is the expensive drawing "
                       "rather than the cheap one. The door's right-hand "
                       "panel held `constellation()` — 319 dots on a lod0 "
                       "silhouette, about 12 KB — and a diagram is what that "
                       "is: it says how many destinations there are and "
                       "nothing about Europe. `heroeurope()` is the lod1 "
                       "coastline thinned to 1.8 units, four hypsometric "
                       "bands, rank-3 rivers and lakes, fifty country paths "
                       "that are fifty links, the ground beyond the atlas and "
                       "two fades over the data cuts: 42.6 + 25.3 + 9.5 + 6 "
                       "KB, and the itemisation is in CLAUDE.md where it was "
                       "written the first time this number moved for the same "
                       "drawing. It is the single most expensive thing on the "
                       "site and it is the one picture of Europe no competitor "
                       "can reproduce — a licensed stock photograph is by "
                       "definition a thing anyone can also license. The trade "
                       "is stated rather than hidden, which is the whole job "
                       "of a ceiling somebody has to raise in a diff."
                       "  152 -> 148 WHEN THE HERO BECAME THE LIVING ATLAS. It reads as a saving and it is a swap: the ground beyond the continent, the non-atlas neighbours, the one country the 52°E cut runs through and both data-cut fades came off — about 25 KB — and forty-one clipped photographs went on for about 9. The pictures themselves are files a reader fetches rather than bytes in this document, and the clip is a `<use>` of the land path the drawing already carries rather than a second copy of 43 KB of country rings. What this ceiling cannot see is that the page now asks for 41 photographs at the 480 step, which is about 950 KB of images: the ladder's smallest rung is 480 and most of these countries render under 150px, so a sixth rung would halve it. Recorded rather than answered here, because a smaller step is a decision about every purpose on the site."},
            "weight.max_page_kb": {
                "value": round(max(len(b) for b in bodies.values()) / 1024),
                "kind": "ceiling",
                "why": "The heaviest page on the site. Guards against a template "
                       "quietly inlining something large across a whole family, "
                       "which is how the coastline reached 51 pages and 2.1 MB. "
                       "440 -> 441: /map gained the two fades that cover its "
                       "own data cuts, which is about 900 bytes of gradient "
                       "stops and two rectangles. The cut runs from x=747 at "
                       "70 degrees north to x=1024 at 40 degrees south of it, "
                       "a straight diagonal through Russia that reads as a "
                       "rendering fault, and it had been on the instrument "
                       "since the instrument was drawn."
                       "  441 -> 444 WHEN /map BECAME THE INSTRUMENT RATHER "
                       "THAN A MAP WITH A DISCLOSURE UNDER IT. Everything "
                       "that makes that page an instrument was inside a "
                       "closed `<details>` — the legend, how to read the "
                       "drawing, the four geography layers, all seventeen "
                       "interest filters, the journey overlay, the distance "
                       "origin and the live count — and the text twin, which "
                       "is the most complete index on this site, was inside a "
                       "second one. Both are bands now, and the three "
                       "kilobytes are the markup of a `<details>` becoming "
                       "the markup of two plates with heads on them. The "
                       "drawing itself did not change by a byte: the ceiling "
                       "is here to catch a template inlining geometry across "
                       "a family, and this is prose."
                       "  444 -> 489 WHEN THE POPUP GOT THE PHOTOGRAPH IT "
                       "HAD FIVE OF SIX FIELDS FOR. /map's popup already "
                       "printed the name, the country, the region, the "
                       "summary and the link, off the baked `mapinfo` block "
                       "— and the register holds a photograph for 105 of the "
                       "319, which the instrument showed none of. The three "
                       "fields are the derivative URL, the alt the "
                       "photographer wrote and the credit fragment "
                       "`render.credit_html` composes: 46,505 raw bytes and "
                       "10,045 over the wire, measured by gzipping the page "
                       "with the fields and without. The credit is carried "
                       "rather than composed in the browser because it is a "
                       "licence obligation and this product has exactly one "
                       "implementation of it — the same reason the planner "
                       "receives `cities.shotCredit` instead of building it. "
                       "Reading it out of `/api/atlas.json` instead would "
                       "trade 10 KB against a 350 KB fetch to show one "
                       "picture, so the bytes are the cheap half of that "
                       "trade. The raw figure is what this ceiling measures "
                       "and the compressed one is what a reader pays."
                       "  489 -> 581 WHEN THE REGISTER REACHED EVERY DESTINATION, AND NOTHING ABOUT THIS PAGE CHANGED. The popup carries the derivative URL, the photographer's alt and the credit for each destination the register holds a picture of, and that went from 105 to 319 when eight acquisition batches merged into the default branch. Measured on the shipped page, `mapinfo` is 253,111 bytes of 597,481 and what a reader pays is 125 KB compressed. The ceiling is raised rather than argued with, because the trade was decided at 105 and this is the same trade at three times the coverage — but it is recorded rather than rounded up, because the per-destination photograph fields are now the largest single thing on the largest page on the site, and the next honest move is a second index rather than a bigger document."},
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
                       "not need a ceremony — but losing them all should. "
                       "241 -> 242 WHEN THE HOMEPAGE DREW THE ATLAS AGAIN: "
                       "the door's right-hand panel went from a dot "
                       "constellation to `heroeurope()`, which carries the "
                       "four bands, so the most-seen page on the site is the "
                       "242nd. The credit follows the drawing rather than the "
                       "request — `cartography.credited()` reads the rendered "
                       "terrain markup — so the colophon at the foot of the "
                       "page names GMTED2010 and ETOPO1 because the layer is "
                       "there, not because a builder asked for it. "
                       "AND 226 -> 262 WHEN THE PLACE PAGE STOPPED THROWING ITS DRAWING AWAY. A place page opened on `photograph if has_photo else minimap(...)` — an either/or — while its own comment twenty lines down says THE OPENING KEEPS THE MAP and *the strip is where the photographs go*. It was invisible while no `place:` purpose was filled; two photograph batches merged and forty place pages lost their geography entirely, relief included, along with the caption saying there is no honest map of a building but there is an honest map of where the building is. `head_figure`/`moved_drawing` is the site's own contract and this was its fourth caller with a private if/else: the photograph keeps the opening `place-hero` declares and the drawing moves to a band below. The figure is higher than the 242 this branch had because a photographed place page now carries BOTH, where before it carried one. Nothing was acquired for it. "},
            "signature.apertures": {
                "value": sum(1 for b in bodies.values() if 'clip-path="url(#arch-' in b),
                "kind": "floor",
                "why": "Pages whose geography is seen through the arch. A floor: "
                       "the aperture is the identity, and a new map that forgets "
                       "it is a page that stops looking like EuropeDoor. "
                       "825 -> 824 WHEN /discover's MAP BECAME ITS FIRST PLATE, "
                       "and that is the rule being obeyed rather than bent: "
                       "docs/signature-moments.md records /map as the place the "
                       "door is CORRECTLY absent, because an instrument is not a "
                       "picture of somewhere, and /discover draws the same "
                       "instrument. It had been carrying a picture's frame around "
                       "a tool. One page, decided, and the floor holds under it. "
                       "753 -> 754 WHEN /experiences GOT ITS GEOGRAPHY BACK, "
                       "and it is the same rule read the other way. The index "
                       "had NO drawing: it used to open on 197 dots at the "
                       "full extent, in the same arch in the same position as "
                       "/stories and /countries, and that was correctly "
                       "removed. What it has now is not an opening, it is the "
                       "fifth band of nine — a picture of where a thing can be "
                       "DONE, on the light map set, answering a question the "
                       "rows underneath it cannot. The door belongs on it "
                       "because it is a picture of somewhere, which is exactly "
                       "the test /discover's map fails. "
                       "AND 714 -> 818 WHEN THE PLACE PAGE STOPPED THROWING ITS DRAWING AWAY, which is the same repair read on the other invariant. Forty place pages had lost their arch outright to a photograph, and every photographed place page now carries the picture in its opening and the map in a band below — so the floor rises past where it stood before those photographs merged rather than recovering to it."},
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
                       "exists to catch. AND /stories MOVED ed-opening "
                       "0.455 -> 0.454 BY LOSING ITS `indexhero`, which is "
                       "one page of 1,034 and is the opposite of the fault "
                       "this floor catches: the index stopped being a head "
                       "beside a 4:3 figure and became a plate sequence, "
                       "which is the same migration /journeys, /experiences "
                       "and /plan each made. The head role did not go — the "
                       "band that introduces the set carries `pagehead "
                       "index`, which is where a plate sequence puts it. "
                       "AND /discover MOVED THREE OF THEM, "
                       "which is Decision 2 of the Discover rebuild: the page "
                       "carried seventeen outlined chips for the interests and "
                       "nine macro cards and six motion cards beneath them — "
                       "border, fill, radius and shadow spent over and over on "
                       "one-word tags, on the page whose whole subject is how to "
                       "choose. The chips became type at reading size and the "
                       "cards became rows and printed queries. card 0.060 to "
                       "0.059, band 0.757 to 0.756, chip 0.521 to 0.520 — one "
                       "page each, which is what a single family leaving a "
                       "primitive looks like. A family that stops using one ON "
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
                       "the argument. "
                       "AND THE MENU-BAR PASS TOOK `band` ONE MORE PAGE, 0.760 "
                       "to 0.759: /events printed the whole year as twelve "
                       "<h2> bands, one per month, holding all 197 fixtures "
                       "over 14,875 pixels — the catalogue failure at its "
                       "purest, on the family whose subject is TIME and which "
                       "could not show the year. The year band above it "
                       "already answers when to go, so the twelve months are "
                       "twelve rows carrying their own counts and their own "
                       "shoulder figure, and the fixtures and their category "
                       "filter moved to the month pages where a reader can "
                       "reach them. 45 KB to 13. "
                       "AND THE PLATE PASS TOOK IT 0.223 TO 0.205, EIGHTEEN "
                       "PAGES, ON PURPOSE. The seventeen interest pages "
                       "carried 728 abstract plates between them, which is "
                       "forty-three hash-drawn landscapes in a column on the "
                       "average one, and /beyond-the-obvious carried 130 in "
                       "a grid directly under a map whose whole argument is "
                       "WHERE those places are. That is the measurement that "
                       "emptied the homepage, /journeys, /europe-in and the "
                       "stories index, still shipping on the family that had "
                       "the most of it. A destination on those pages is "
                       "chosen on where it is and what it is like, and "
                       "neither of those is a LOOK, which is the test a card "
                       "has to pass. They are rows now, and the WHOLE set: "
                       "the interest list used to stop at sixty with one "
                       "sentence admitting it, and a row is cheap enough "
                       "that there is no longer a reason to stop. Each "
                       "interest page opens on its own tag drawn instead, "
                       "every destination carrying it on one unframed "
                       "extent, so the seventeen can be compared. AND THE REGION PASS TOOK IT 0.205 TO 0.079, ONE HUNDRED AND THIRTY PAGES, ON PURPOSE. 97 of the 130 travel regions hold one or two destinations and 26 hold exactly one, so the band that IS the subject of a region page opened with a single 280px tile and two empty columns beside it — the stories-index failure exactly, with the shape of the data deciding the layout. Each tile also drew a plate from its destination's own hash directly under a real map of the region showing where those same places are. The rest of the page was already rows — places to see, things to do, journeys — so a region page was speaking two list languages one band apart. This is the largest single move this figure has made, and the last card grid outside the country pages. AND THE FUND REGISTER COST IT ONE MORE PAGE, 0.079 to 0.078: a heading reading 'The four themes' sat over SEVEN cards and four of them read '1 projects'. A number typed into a heading and a count with no plural rule, in a grid of seven that left three empty cells, on cards holding a kicker and a figure and nothing else — which is exactly what /experiences was before the nav-bar pass. What separates the seven is how much of the register each holds and where that work is, so they are rows carrying the countries and the count as a bar against the largest. AND THE TWELVE MOTION PAGES TOOK IT 0.078 TO 0.070: each one ended on three journey cards and up to three theme cards, every one opening on a gradient chosen by the hash of a slug — sixty hash-drawn landscapes on the family whose entire argument is that a motion is NOT a place, and whose index had its own plates removed for exactly that reason. /journeys and /themes had each already answered this, and differently, because their subjects differ: a journey's picture is its ROUTE and a theme's is its SCATTER. Both drawn on the same projection as the map above them, so the three bands of a motion page now agree about what Europe looks like. AND THE TWELVE MONTH PAGES TOOK IT 0.070 TO 0.060: each ended on six abstract plates over six names, under the heading 'Where we would actually send you' — the single most useful recommendation this dataset makes, a quiet place in a country in its shoulder season THIS month, rendered as six gradients. ONE drawing for the six, not six: six framed thumbnails would be six pictures of the same continent, which is the nine-macro-regions fault. This is the last card grid on the site outside the country pages."
                       "AND THE INTERESTS INDEX MOVED FOUR OF THEM BY A "
                       "THOUSANDTH, WHICH IS WHAT ADDING A PAGE DOES. "
                       "/interests was a SERVER AUTOINDEX: seventeen interest "
                       "pages shipped and their directory had no index.html, "
                       "so a reader who trimmed a URL got a file listing with "
                       "none of this site on it. Nothing linked to it, which is "
                       "exactly why no check caught it — a link checker "
                       "validates links that exist and a missing index is an "
                       "absence. band, note, facts and chip each fall about a "
                       "thousandth because one page in 1,034 composes without "
                       "them: the index is seventeen rows and a shared "
                       "silhouette, ordered by reach, and it carries no note "
                       "panel, no facts table and no chip row. AND THE 2036 PAGE SYSTEM IS A MIGRATION, which is what these numbers do from here: /countries moved its fifty rows from `row` to `ed-row` and the old figure fell by one page, 0.888 to 0.887, while the new one rose from nothing. Six ed- primitives are counted from this commit so the transfer is visible as a transfer — a register watching only the set being left reads every step of a deliberate migration as a loss, and cannot tell it from a family that quietly stopped listing anything at all. AND `row` FELL 0.887 TO 0.769 WHEN 255 PLACE PAGES STOPPED PRINTING ONE SET TWICE: the other places in the town were a strip of pictures AND a band of rows carrying the sentence each picture could not, adjacent, on 220 of the 255 — both numbered 01, because the typed section index and the CSS band counter were two numbering systems on one page. The tile carries the sentence now and the second band is gone, so pages with no other list lost their last row. A removal of duplication, not a family growing its own components. AND THE DISCOVERY FAMILY TOOK `pagehead` ONE PAGE, 0.230 to 0.229: /interests was the last index still opening on the old head — a kicker, an h1 and a lede over seventeen drawings of the same continent, with no photograph anywhere on a page whose subject is what you are travelling FOR. It opens on `ed-opening` now, carrying the `interests-hero` purpose that was declared and unreached, and the seventeen shapes keep their section because reach is the one argument no single tag page can make."
                       "AND THE EXPERIENCE ATLAS COST FIVE OF THEM ONE "
                       "PAGE EACH, WHICH IS ONE FAMILY OF ONE. /experiences "
                       "was forty-two `.row`s: 24 experiences, 8 category "
                       "bars and 10 kind bars, plus the `.band`, `.btn`, "
                       "`.ed-section` and `.ed-eyebrow` that came with "
                       "`indexhero()` and `section()`. It is nine plates now "
                       "and it uses none of those — the plate sequence is "
                       "`actmark` and `.sheettext`, which is the same "
                       "vocabulary the homepage and /discover already use, so "
                       "this is not a family growing its own components. "
                       "row/band 0.769 -> 0.768, btn 0.642 -> 0.641, "
                       "ed-section 0.836 -> 0.835, ed-eyebrow 0.781 -> 0.780. "
                       "One page each is what a single index leaving a "
                       "primitive looks like, and the composition that caused "
                       "it is in the same commit. "
                       "AND THE JOURNEY ATLAS COST THREE OF THEM ONE "
                       "PAGE EACH, FOR THE SAME REASON ONE FAMILY ON. "
                       "/journeys was `indexhero()` over seventeen "
                       "rows; it is eight plates now, and `ed-opening`, "
                       "`ed-eyebrow` and `btn` came with the head it no "
                       "longer has. btn 0.641 -> 0.640, ed-opening "
                       "0.456 -> 0.455, ed-eyebrow 0.780 -> 0.779. "
                       "`pagehead` did NOT move and that is the check "
                       "working: the page still declares what kind of "
                       "page it is, on the band that introduces the set, "
                       "which is where /experiences already puts it — a "
                       "plate sequence has no room for a stage above "
                       "its opening. `row` did not move either, because "
                       "the seventeen are still rows: what left is the "
                       "head, not the list. "
                       "AND THE ATLAS TOOK THREE MORE, TWO OF THEM THE "
                       "SAME MIGRATION AND ONE OF THEM A DEFECT THIS "
                       "FILE ALREADY RECORDS. /countries was an "
                       "`ed_opening()` over a 4:3 figure with nine "
                       "macro bands under it; it is a seven-plate "
                       "sequence now, so ed-opening 0.454 -> 0.453 and "
                       "ed-section 0.835 -> 0.834 — one page each, the "
                       "fifth family to make the same move, and the "
                       "head did not go: the A-Z band declares "
                       "`pagehead index` and states the extent, which "
                       "is where a plate sequence puts it. "
                       "`band` 0.768 -> 0.767 IS THE INTERESTING ONE, "
                       "because it is a repair rather than a "
                       "migration: the nine macro regions were "
                       "`<section class=\"band macroband\">` with "
                       "their head inside a `.bandtop` wrapper, so "
                       "`.band > .band-head::before` never matched "
                       "them — NINE SILENT INCREMENTS of the counter "
                       "that numbers every other section on the site, "
                       "which is the *selector that COUNTS is the "
                       "selector that DRAWS* failure this file records "
                       "one commit over, and it was on /countries. "
                       "Dropping `band` from those nine is what fixes "
                       "it: they are plate bands now and they neither "
                       "count nor draw an index. "
                       "AND /interests IS THE SIXTH FAMILY TO "
                       "MAKE THE SAME MOVE, one page each: "
                       "ed-opening 0.453 -> 0.452, ed-section "
                       "0.834 -> 0.833, ed-eyebrow 0.779 -> "
                       "0.778. It was an `ed_opening()` over a "
                       "strip of eight and a seventeen-row "
                       "ledger; it is a seven-plate sequence "
                       "now, and the head did not go — the "
                       "interest-atlas band declares `pagehead "
                       "index` and states the extent, which is "
                       "where a plate sequence puts it. `row` "
                       "did not move: the seventeen are still "
                       "rows and the eight narrow ones are rows "
                       "too, so what left is the head rather "
                       "than the list. "
                       "AND /beyond-the-obvious IS THE SEVENTH, one "
                       "page each: band 0.767 -> 0.766 and "
                       "ed-section 0.833 -> 0.832. It was a "
                       "`pagehead index`, a map, a strip and two "
                       "`section()` bands with the page's own "
                       "editorial position in a `.note` at the "
                       "bottom at caption size; it is a "
                       "seven-plate sequence now, and the head "
                       "stayed — the opening plate declares "
                       "`pagehead index` and states the extent. "
                       "`row` did not move: the 130 are still rows "
                       "grouped by macro region and the six swaps "
                       "are rows too."
                       "  0.769 -> 0.768 WHEN /themes STOPPED BEING THIRTEEN "
                       "ROWS. The owner read the first version of that page "
                       "and named the fault: keep the existing page, add "
                       "premium CSS and components round it, call it a "
                       "redesign. A theme holds a photograph, a geography, "
                       "an authored summary, eight places and a reach — that "
                       "is a composition, and `.row` was the shape of the "
                       "LIST rather than of the content. So thirteen rows "
                       "became thirteen argument bands at three scales "
                       "derived from reach, and this floor moved by one "
                       "page. THAT IS THE FLOOR WORKING RATHER THAN BEING "
                       "OVERRULED: it exists to catch a family growing its "
                       "own components without anybody deciding, and this is "
                       "the deciding. `.arg` is a PAGE component and not a "
                       "twelfth primitive — it appears on one page, like "
                       "`.motile`, `.narrowrow` and `.qshare` — and *no new "
                       "primitive until repeated structure has actually "
                       "emerged* still holds. `tools/monotony.js` measured "
                       "the change: 37% of the page was thirteen identical "
                       "siblings and the largest group is now 18%."},
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
