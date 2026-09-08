#!/usr/bin/env python3
"""Within-motif variation, measured by RENDERING.

    python3 tools/plate-variation.py            report
    python3 tools/plate-variation.py --write    record the twin counts
    python3 tools/plate-variation.py --check    fail if any family got MORE
                                                interchangeable
    python3 tools/plate-variation.py --ablate tower
                                                WHICH layer of one motif
                                                carries the variation

Not part of tools/checks.py: it renders 319 plates and compares every pair,
which is eight seconds. A gate that adds eight seconds to every build is a
gate people stop running.


Three earlier versions of this instrument were wrong, each in a way that
produced a confident number:

  1. bounding boxes — a ridge polygon spans the whole frame, so every peaks
     plate collapsed to one constant vector: "92% duplication" in a family
     that has none.
  2. no ellipses — isles is drawn from ellipses, so every isles plate was
     the flat water line: "79% duplication".
  3. silhouette only — isles' islands sit BELOW the horizon, so they are
     interior detail and never touch the top profile at all. The metric
     could not see the thing that varies.

Measuring a drawing requires drawing it. This renders every plate at 64x40
through the same rasteriser the social cards use and compares pixels, which
is what a reader's eye does with a card.

--ablate answers the next question, which the twin count cannot: a family is
repetitive, but WHICH of its layers is responsible? It removes each primitive
in turn and re-counts. A layer whose removal changes nothing carries no
variation however much of the frame it paints; a layer whose removal makes
the family MORE varied is occluding the part that does. Tower needed this:
three rounds of reasoning about the drawing had picked the shaft, which is
4% of the plate, while 68% of it was two ridges nobody had looked at.

READ A NEGATIVE DELTA AGAINST WHAT IS UNDERNEATH. Deleting a layer does not
reveal nothing; it reveals the layer below, and if THAT one varies more the
result reads as "occludes" whether or not anything is wrong. isles reports
-4 on its water, but the only thing under that water is the sky gradient,
which varies by hue on every plate — the water is doing its job. tower's -6
on its foreground ridge was real, because what sat under that ridge was the
base of the nave and the shaft: the two layers the same run had just named
as the ones carrying variation. The delta locates a suspect; what lies
beneath it is what settles the case.
"""
import json, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.chdir(ROOT)
from lib import data as D, render as R, raster                     # noqa: E402

BASELINE = os.path.join(ROOT, "docs", "plate-variation.json")

W, H = 64, 40


def pixels(seed, motif):
    sky_a, sky_b, prims = R.plate_shapes(seed, W, H, motif)
    c = raster.Canvas(W, H)
    c.vertical_gradient(sky_a, sky_b)
    for p in prims:
        if p[0] == "poly":
            c.polygon(p[1], p[2], p[3])
        elif p[0] == "rect":
            c.rect(p[1], p[2], p[3], p[4], p[5], p[6])
        elif p[0] == "circle":
            c.ellipse(p[1], p[2], p[3], p[3], p[4], p[5])
        elif p[0] == "ellipse":
            c.ellipse(p[1], p[2], p[3], p[4], p[5], p[6])
    return b"".join(bytes(r) for r in c.rows)


def dist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / (len(a) * 255.0)


d = D.load()
plates = []
for cid, n in sorted(d["cities"].items()):
    t, r, c = n["city"], n["region"], n["country"]
    m = R.motif_for(t["interests"], t.get("city_type")) or R.motif_for(r["interests"])
    plates.append((m, t["name"], f'city:{c["slug"]}:{t["slug"]}'))


def twins(imgs):
    return sum(1 for i in range(len(imgs)) for j in range(i + 1, len(imgs))
               if dist(imgs[i], imgs[j]) < 0.020)


if "--ablate" in sys.argv:
    # Layer names, per motif, as (head, repeated, tail). Four of the seven
    # motifs emit a seed-chosen NUMBER of primitives — coast's headland is
    # on half of them, isles draws three to six, skyline and forest fill the
    # frame — so a flat positional list mislabels the trailing layer on
    # exactly the plates where it matters. head is matched from the front,
    # tail from the back, and the repeated name fills whatever is between.
    LAYERS = {
        "tower": (["ridge-back", "nave", "shaft", "cornice", "spire", "ridge-front"],
                  None, []),
        "coast": (["ridge", "water", "glint", "glint", "glint"], None, ["headland"]),
        "peaks": ([], "ridge", []),
        "isles": (["water"], "isle", []),
        "forest": (["ridge"], "tree", ["ridge-front"]),
        "plain": ([], "ridge", []),
        "skyline": (["ridge"], "block", []),
    }
    motif = sys.argv[sys.argv.index("--ablate") + 1]
    if motif not in LAYERS:
        print(f"unknown motif: {motif}")
        sys.exit(2)
    shapes = [(nm, R.plate_shapes(sd, W, H, motif))
              for m, nm, sd in plates if m == motif]

    def named(prims):
        """Name every primitive of one plate. The light is inserted at the
        FRONT of the list and only where there is sky to hold it, so it is
        identified by its shape rather than by its index."""
        head, rep, tail = LAYERS[motif]
        body = [i for i, p in enumerate(prims) if p[0] != "circle"]
        out = {i: "light" for i, p in enumerate(prims) if p[0] == "circle"}
        take_tail = tail if len(body) >= len(head) + len(tail) else []
        for k, i in enumerate(body):
            back = len(body) - k
            if k < len(head):
                out[i] = head[k]
            elif back <= len(take_tail):
                out[i] = take_tail[len(take_tail) - back]
            else:
                out[i] = rep or "extra"
        return [out[i] for i in range(len(prims))]

    def draw(sky_a, sky_b, prims):
        c = raster.Canvas(W, H)
        c.vertical_gradient(sky_a, sky_b)
        for p in prims:
            if p[0] == "poly":
                c.polygon(p[1], p[2], p[3])
            elif p[0] == "rect":
                c.rect(p[1], p[2], p[3], p[4], p[5], p[6])
            elif p[0] == "circle":
                c.ellipse(p[1], p[2], p[3], p[3], p[4], p[5])
            elif p[0] == "ellipse":
                c.ellipse(p[1], p[2], p[3], p[4], p[5], p[6])
        return b"".join(bytes(r) for r in c.rows)

    full = [draw(a, b, pr) for _nm, (a, b, pr) in shapes]
    sky = [draw(a, b, []) for _nm, (a, b, pr) in shapes]
    base = twins(full)
    order = []
    for nm, (a, b, pr) in shapes:
        for ln in named(pr):
            if ln not in order:
                order.append(ln)
    print(f"{motif}: {len(shapes)} plates, {base} twin pairs\n")
    print(f"{'layer':<13}{'coverage':>10}{'twins without':>15}{'delta':>8}   reading")
    print("-" * 66)
    for layer in order:
        cov, kept = [], []
        for nm, (a, b, pr) in shapes:
            names = named(pr)
            solo = draw(a, b, [p for p, n2 in zip(pr, names) if n2 == layer])
            cov.append(sum(1 for x, y in zip(solo, draw(a, b, []))
                           if x != y) / len(solo))
            kept.append(draw(a, b, [p for p, n2 in zip(pr, names) if n2 != layer]))
        t = twins(kept)
        delta = t - base
        read = ("carries the variation" if delta > 3 else
                "OCCLUDES what varies" if delta < -3 else "carries none")
        print(f"{layer:<13}{100 * sum(cov) / len(cov):>9.1f}%{t:>15}{delta:>+8}   {read}")
    print(f"{'(colour only)':<13}{'':>10}{twins(sky):>15}{twins(sky) - base:>+8}   "
          f"the sky and the palette alone")
    print("\ncoverage = share of a 64x40 plate the layer paints")
    print("delta    = twin pairs gained by DELETING the layer. Positive means "
          "it was\n           distinguishing plates; negative means it was "
          "hiding what does.")
    sys.exit(0)

fam = collections.defaultdict(list)
for m, nm, sd in plates:
    fam[m].append((nm, pixels(sd, m)))

print(f"{'motif':<9}{'n':>4}{'mean d':>9}{'near d':>9}{'twins':>7}{'twin%':>7}  closest pair")
print("-" * 88)
rows = []
for m in sorted(fam, key=lambda k: -len(fam[k])):
    items = fam[m]
    if len(items) < 2:
        continue
    ds, near, twins = [], [], 0
    worst = (9, "", "")
    for i, (na, pa) in enumerate(items):
        best = (9, "")
        for j, (nb, pb) in enumerate(items):
            if i == j:
                continue
            dd = dist(pa, pb)
            if j > i:
                ds.append(dd)
            if dd < best[0]:
                best = (dd, nb)
            if dd < 0.020 and j > i:
                twins += 1
        near.append(best[0])
        if best[0] < worst[0]:
            worst = (best[0], na, best[1])
    mean = sum(ds) / len(ds)
    nm = sum(near) / len(near)
    tp = 100 * twins / (len(items) * (len(items) - 1) / 2)
    print(f"{m:<9}{len(items):>4}{mean:>9.4f}{nm:>9.4f}{twins:>7}{tp:>6.1f}%  "
          f"{worst[1][:22]} / {worst[2][:22]} ({worst[0]:.4f})")
    rows.append((m, len(items), nm, twins, tp))

print()
print("mean d = average pixel difference between any two plates in the family")
print("near d = average difference to the NEAREST other plate — interchangeability")
print("twins  = pairs under 2% pixel difference")
print()
for m, n, nm, tw, tp in sorted(rows, key=lambda r: -r[4])[:3]:
    print(f"least varied: {m:<9} n={n:<4} near d={nm:.4f}  twins={tw} ({tp:.1f}% of pairs)")

# ── the gate ─────────────────────────────────────────────────────────────
#
# A ceiling on twin pairs per family. Variation is easy to lose by accident —
# a constant reintroduced, a seeded parameter narrowed — and the loss is
# invisible on any single plate. This is the number that made the difference
# between "the plates look a bit samey" and "coast has 125 interchangeable
# pairs out of 1,596".
got = {m: tw for m, _n, _nm, tw, _tp in rows}
if "--write" in sys.argv:
    with open(BASELINE, "w", encoding="utf-8") as fh:
        json.dump({"$comment": "GENERATED by tools/plate-variation.py --write. "
                               "A CEILING on interchangeable pairs per motif "
                               "family: pairs whose rendered 64x40 plates differ "
                               "by under 2% of pixel value. Going UP means the "
                               "atlas got more repetitive.",
                   "twin_pairs": got}, fh, indent=2)
        fh.write("\n")
    print(f"\nwrote {BASELINE}")
elif "--check" in sys.argv:
    if not os.path.exists(BASELINE):
        print("no baseline — run --write")
        sys.exit(1)
    with open(BASELINE, encoding="utf-8") as fh:
        want = json.load(fh)["twin_pairs"]
    bad = 0
    for m, ceiling in sorted(want.items()):
        now = got.get(m, 0)
        if now > ceiling:
            print(f"FAIL {m}: {now} interchangeable pairs, ceiling {ceiling} — "
                  f"the family got more repetitive")
            bad += 1
    print("" if bad else f"\nall {len(want)} motif families hold their variation")
    sys.exit(1 if bad else 0)
