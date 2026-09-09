#!/usr/bin/env python3
"""Draw the two sides side by side, at the sizes a reader actually gets.

    python3 experiments/aegean-geometry/render.py

Writes only into experiments/aegean-geometry/out/:

    out/contact-sheet-desktop.svg   panels 1136 CSS px wide
    out/contact-sheet-phone.svg     panels  310 CSS px wide

## Why a contact sheet and not another number

`measure.py` will tell you Santorini is drawn with three corners. It will not
tell you what three corners look like through a 34% arch at 1,136 pixels with
a lime dot on top, and this repository has already learned that difference the
expensive way: a moon drawn behind a skyline and clipped into an unreadable
glyph survived every static check and every count, and was found by rendering
forty plates onto one sheet and looking at it. Counting settles proportions;
rendering finds defects. Both, or neither is trustworthy.

## Why the panels are the real size

A defect that disappears when you shrink the picture is a defect you will
argue yourself out of. The desktop sheet is 1,136 CSS pixels per panel — the
width `.placeband.maponly` gives the minimap inside a 76rem page — and the
phone sheet is 310, which is the same map on a 390px viewport. The four-corner
blob is obvious on one and nearly invisible on the other, and THAT is a
finding: it is most of the argument about whether this is worth doing.

## Why the right-hand panel is empty

Because the OSM side does not exist. Drawing a plausible coastline there —
smoothed, hand-drawn, borrowed from memory — would be inventing the very
measurement the experiment is meant to produce, and it would look exactly
like evidence. The panel says what is missing and why, and it will keep
saying it until somebody settles the licence and puts a file in osm/.

## On the <style> block in the output

`checks.py` refuses an inline <style> on a page, for good reasons that do not
apply here: this file is written to out/, is never copied into site/, and is
not served by anything. It is a standalone SVG and a standalone SVG carries
its own paint or it carries none.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from lib import geo, render                                   # noqa: E402

sys.path.insert(0, HERE)
import measure                                                # noqa: E402

OUT = os.path.join(HERE, "out")

# The four the experiment is named for, plus the control and the long coast.
# Crete is here because a smoothed 250 km shoreline and a four-corner island
# fail differently and only one of them looks like a blob.
ROWS = ("santorini", "paros", "naxos", "milos", "chania", "athens")


# What the empty panel says. Two lengths, because a caption wider than its
# own panel is the same defect as a header wider than its column — and the
# phone panel is 310 px, which fits about forty characters at 12px.
MISSING_LONG = (
    "NO DATA YET",
    "experiments/aegean-geometry/osm/ is empty",
    "ODbL is unsettled: see README §4 before fetching anything",
    "nothing is drawn here on purpose — a plausible coastline",
    "would be the measurement, invented",
)
MISSING_SHORT = (
    "NO DATA YET",
    "osm/ is empty — README §4",
    "nothing drawn on purpose",
)


def palette():
    """The site's own hexes, so the sheet looks like the product.

    docs/palette.json stores each token as an OBJECT — hex, name, role — and
    the first version of this read the object straight into the stylesheet,
    which produced `fill: {'hex': '#f7f6f3', ...}`. Every fill in the sheet
    was then invalid, the browser fell back to black, and the SVG still
    opened without an error: a contact sheet that renders wrong looks exactly
    like a contact sheet that renders. Screenshotting it is what found this,
    which is the same lesson as the moon behind the skyline.
    """
    with open(os.path.join(ROOT, "docs", "palette.json"), encoding="utf-8") as fh:
        toks = json.load(fh)["tokens"]
    return {k: (v["hex"] if isinstance(v, dict) else v) for k, v in toks.items()}


def panel(proj, C, cx, cy, span, dest_xy, label, w_units, h_units):
    """One minimap, drawn exactly the way pages.minimap() draws one.

    Same projection, same landmass() call — including the fact that it asks
    for the WHOLE continent and lets the clip path hide the rest, which is
    where 73 KB of every destination page goes — same transform, same arch.
    If this drew the Aegean some other way it would be a picture of this
    script rather than of the site.
    """
    uid = "p" + label.replace(" ", "").replace(",", "")[:12]
    ctx, land = geo.landmass(proj, (0, 0, C["map_w"], C["map_h"]))
    dot = ""
    if dest_xy:
        px = w_units / 2 + (dest_xy[0] - cx) * span
        py = h_units / 2 + (dest_xy[1] - cy) * span
        dot = (f'<circle class="here" cx="{px:.1f}" cy="{py:.1f}" r="5.5"/>'
               f'<text class="lbl" x="{px + 9:.1f}" y="{py + 4:.1f}">{label}</text>')
    return (
        # No preserveAspectRatio: the site's own <svg> carries none either, so
        # the default (xMidYMid meet) is what a destination page gets. Forcing
        # "none" happened to be harmless while the panel and the viewBox were
        # both 2.8125:1 and would silently stretch the coastline the first
        # time somebody changed a width — the map would still look like a map.
        f'<svg viewBox="0 0 {w_units} {h_units}" width="100%" height="100%">'
        f'<defs>{render.arch_clip(uid, w_units, h_units)}</defs>'
        f'<g clip-path="url(#arch-{uid})">'
        f'<rect x="0" y="0" width="{w_units}" height="{h_units}" class="sea"/>'
        f'<g transform="translate({w_units/2 - cx*span:.2f},'
        f'{h_units/2 - cy*span:.2f}) scale({span})">{ctx}{land}</g>'
        f'{dot}</g></svg>')


def empty_panel(uid, w_units, h_units, lines, k=1.0):
    """The OSM side. An explicit absence, not a blank.

    A blank panel reads as a rendering failure. A panel that states what is
    missing, where it would go and what has to happen first reads as the
    finding it is.

    `k` is viewBox units per CSS pixel, and this text is sized THROUGH it so
    it stays 12 CSS px on both sheets. That is the opposite of what the map
    label does, deliberately: the label is the site's own 11px-in-a-900-unit
    viewBox and shrinks to under 4 CSS px on a phone, which is a real
    property of the product and must not be corrected in a picture OF the
    product. This caption is the experiment's own annotation and is not.
    """
    # CENTRED ON 0.58 OF THE HEIGHT, NOT ON THE MIDDLE. The arch narrows to
    # nothing at the top corners, so a block centred at h/2 puts its first
    # line outside the aperture and onto the sheet behind it — which renders
    # as a caption floating above a panel it does not belong to. Rendering
    # the phone sheet is what showed that; the desktop one had room and hid
    # it completely.
    y = h_units * 0.58 - (len(lines) - 1) * 13 * k
    txt = "".join(
        f'<text class="missing{" head" if i == 0 else ""}" x="{w_units/2:.0f}" '
        f'y="{y + i * 26 * k:.0f}" font-size="{(15 if i == 0 else 12) * k:.1f}" '
        f'text-anchor="middle">{t}</text>'
        for i, t in enumerate(lines))
    return (
        f'<svg viewBox="0 0 {w_units} {h_units}" width="100%" height="100%">'
        f'<defs>{render.arch_clip(uid, w_units, h_units)}</defs>'
        f'<rect class="voidbg" x="0" y="0" width="{w_units}" height="{h_units}" '
        f'clip-path="url(#arch-{uid})"/>'
        f'<path class="voidline" d="{render.arch_path(w_units, h_units)}"/>'
        f'{txt}</svg>')


CSS = """
  .sheet-bg {{ fill: {limestone}; }}
  text {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  .h1 {{ font-size: 22px; font-weight: 700; fill: {graphite}; }}
  .h2 {{ font-size: 13px; font-weight: 600; fill: {graphite}; letter-spacing: .06em; }}
  .meta {{ font-size: 12px; fill: #55606a; }}
  .rowname {{ font-size: 15px; font-weight: 700; fill: {graphite}; }}
  .rowmeta {{ font-size: 12px; fill: #55606a; }}
  /* The INTELLIGENCE world: every embedded map figure is dark, wherever it
     sits, so the panels are graphite in a limestone sheet — the same
     relationship the destination page has. */
  .sea {{ fill: {graphite}; }}
  .countries path {{ fill: none; stroke: {cobalt_air}; stroke-width: 1.1;
                     vector-effect: non-scaling-stroke; }}
  .context path {{ fill: none; stroke: #4b5563; stroke-width: 0.7;
                   vector-effect: non-scaling-stroke; }}
  .here {{ fill: {lime}; }}
  .lbl {{ font-size: 11px; font-weight: 600; fill: {limestone}; }}
  .voidbg {{ fill: #e7e4dd; }}
  .voidline {{ fill: none; stroke: #9aa2ab; stroke-width: 1.5;
               stroke-dasharray: 6 6; }}
  /* NO font-size here. It is a presentation attribute on each text
     element, computed from the panel's own scale so the caption is 12 CSS
     px on both sheets. A rule here would win over the attribute — CSS
     beats presentation attributes — and the phone caption rendered at four
     pixels for exactly that reason.
     The whole block is wrapped in CDATA below, because an SVG is XML and a
     bare less-than inside a style element opens a tag: a comment mentioning
     one turned the entire sheet into a parser error page, twice. Chromium
     said so; opening the file in an editor would not have. */
  .missing {{ fill: #55606a; }}
  .missing.head {{ font-weight: 700; fill: {graphite}; }}
"""


def sheet(panel_px, filename, note):
    C = measure.constants()
    lon0, lat0, lon1, lat1 = C["extent"]
    proj = geo.Projection((lon0, lat0, lon1, lat1), C["map_w"], C["map_h"], pad=0.0)
    w_units, h_units = C["minimap_view"]
    tok = palette()

    dests = {d["slug"]: d for d in measure.destinations()}
    spans = measure.spans(proj, list(dests.values()), C)

    panel_h = panel_px * h_units / w_units
    gutter, margin, head, gap = 32, 40, 46, 26
    sheet_w = margin * 2 + panel_px * 2 + gutter
    top = 150
    narrow = panel_px < 600
    rows = [s for s in ROWS if s in dests]
    sheet_h = top + len(rows) * (head + panel_h + gap) + 90

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_w:.0f}" '
        f'height="{sheet_h:.0f}" viewBox="0 0 {sheet_w:.0f} {sheet_h:.0f}">',
        "<style><![CDATA[" + CSS.format(
            limestone=tok["limestone"], graphite=tok["graphite"],
            cobalt_air=tok["cobalt-air"], lime=tok["lime"]) + "]]></style>",
        f'<rect class="sheet-bg" x="0" y="0" width="{sheet_w}" height="{sheet_h}"/>',
        f'<text class="h1" x="{margin}" y="46">Aegean geometry — the same frame, '
        f'two datasets</text>',
        f'<text class="meta" x="{margin}" y="70">{note}</text>',
        f'<text class="meta" x="{margin}" y="90">Panels are the real rendered '
        f'width; the projection, the arch and the land are the site’s own '
        f'(geo.Projection, render.arch_path, geo.landmass).</text>',
        # THE HEADERS OVERLAPPED ON THE PHONE SHEET, and only rendering it
        # showed that: at 310px per panel the left header is wider than its
        # own column and ran straight through the right one. A caption that
        # collides with another caption is the sheet lying about its own
        # layout, on the one artefact whose job is to be looked at.
        f'<text class="h2" x="{margin}" y="{top - 14}">'
        f'{"NATURAL EARTH 1:50m" if narrow else "NATURAL EARTH 1:50m — europe-lod1.json, what the site draws today"}</text>',
        f'<text class="h2" x="{margin + panel_px + gutter}" y="{top - 14}">'
        f'{"OSM — ABSENT" if narrow else "OSM-DERIVED — NOT PRESENT"}</text>',
    ]

    y = top
    for slug in rows:
        d = dests[slug]
        s = spans[slug]
        cx, cy = proj.xy(d["lat"], d["lon"])
        out.append(
            f'<text class="rowname" x="{margin}" y="{y + 18}">{d["name"]}</text>')
        out.append(
            f'<text class="rowmeta" x="{margin}" y="{y + 36}">'
            f'span {s["span"]:g} · {s["km_per_rendered_unit"]:.2f} km per '
            f'rendered unit · frame {s["frame_km_w"]:,}×'
            f'{s["frame_km_h"]:,} km · '
            f'1 stroke = {s["km_per_rendered_unit"] * w_units / panel_px * C["stroke_px"]:.2f} km'
            f'</text>')
        py = y + head
        out.append(f'<svg x="{margin}" y="{py:.0f}" width="{panel_px:.0f}" '
                   f'height="{panel_h:.0f}">'
                   + panel(proj, C, cx, cy, s["span"], (cx, cy), d["name"],
                           w_units, h_units)
                   + "</svg>")
        out.append(f'<svg x="{margin + panel_px + gutter:.0f}" y="{py:.0f}" '
                   f'width="{panel_px:.0f}" height="{panel_h:.0f}">'
                   + empty_panel("osm" + slug, w_units, h_units,
                                  MISSING_SHORT if narrow else MISSING_LONG,
                                  k=w_units / panel_px)
                   + "</svg>")
        y = py + panel_h + gap

    out.append(
        f'<text class="meta" x="{margin}" y="{y + 24}">Generated by '
        f'experiments/aegean-geometry/render.py. The right-hand column stays '
        f'empty until a human settles the licence question and puts a file in '
        f'osm/; it is not a rendering failure.</text>')
    out.append("</svg>")

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
        fh.write("\n")
    return path, sheet_w, sheet_h


def main():
    a = sheet(measure.CSS_WIDTHS["desktop_maponly"], "contact-sheet-desktop.svg",
              "Desktop: a 76rem page, .placeband.maponly, minimap 1136 CSS px wide.")
    b = sheet(measure.CSS_WIDTHS["phone_390"], "contact-sheet-phone.svg",
              "Phone: a 390px viewport, minimap 310 CSS px wide — the same "
              "geometry, and most of the defect gone with the pixels.")
    for path, w, h in (a, b):
        print(f"wrote {os.path.relpath(path, ROOT)}  {w:.0f}×{h:.0f}")
    print("\nOpen both. The question the sheet answers is not 'is Natural Earth")
    print("coarse' — measure.py answers that — but 'is the coarseness visible")
    print("at the size the reader gets', and the two sheets disagree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
