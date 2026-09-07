"""Interface strings, out of the code and into data.

The specification's rule is blunt: "Do not hard-code text into the
application." This is the mechanism for the interface chrome — navigation,
footer, buttons, section headings — which is where it matters most, because
it is the text that appears on all 981 pages.

Editorial copy (a country's summary, a story, a place description) stays in
`data/` alongside the thing it describes, which is already translatable by
the overlay scheme in the specification.

What this file will NOT do is let a half-translated language ship. A
catalogue below SHIP_THRESHOLD is a demonstration, not a locale, and
`coverage()` is what the build asks before it would emit one.
"""

from __future__ import annotations

import json
import os

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "strings")

# A language ships when its chrome is complete AND its destination copy is
# localised — not machine-translated. This constant only governs the first
# half; the second is an editorial decision, not a percentage.
SHIP_THRESHOLD = 1.0


class Strings:
    def __init__(self, lang="en"):
        self.lang = lang
        self.base = _load("en")
        self.cat = _load(lang) if lang != "en" else self.base

    def __call__(self, key, **fmt):
        v = self.cat.get(key) or self.base.get(key)
        if v is None:
            raise KeyError(f"no string {key!r} in en.json — add it there first")
        return v.format(**fmt) if fmt else v


def _load(lang):
    path = os.path.join(DIR, f"{lang}.json")
    with open(path, encoding="utf-8") as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}


def languages():
    return sorted(f[:-5] for f in os.listdir(DIR) if f.endswith(".json"))


def coverage(lang):
    """How much of the interface a catalogue actually covers."""
    base, cat = _load("en"), _load(lang)
    have = sum(1 for k in base if cat.get(k))
    return have / max(1, len(base)), have, len(base)


def report():
    out = []
    for lang in languages():
        frac, have, total = coverage(lang)
        out.append({
            "lang": lang,
            "coverage": frac,
            "have": have,
            "total": total,
            "ships": frac >= SHIP_THRESHOLD,
        })
    return out
