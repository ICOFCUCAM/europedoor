"""Which routes are meant to be found, and which are merely reachable.

ONE DECISION POINT, BECAUSE THIS ONE HAS FOUR CONSUMERS. `render.page()` asks
whether to emit a robots meta, `build.py` asks which routes go in the sitemap,
`checks.py` asserts the two agree, and `tools/seo.py` reports against it. Four
readers of one fact is exactly the shape that cost this repository a whole
sitting when a dispatch cap was typed in four places and three of them were
raised — so the fact is declared once, in `data/seo.json`, and read here.

WHAT IS AUTHORED AND WHAT IS DERIVED IS THE WHOLE ARCHITECTURE. The brief for
this layer lists nine fields — indexable, canonical, title, description,
schema, sitemap, readiness, status, last_reviewed — and seven of them are
already facts about the page the build emits. A canonical written here would
be a second copy of the one in the `<head>`; a readiness written here would be
an authored measurement, which this repository refuses by name. So:

    status         AUTHORED   a classification: is this meant to be found
    reason         AUTHORED   required wherever the status is not the default
    last_reviewed  AUTHORED   when a person last looked at that decision
    indexable      DERIVED    status != noindex
    sitemap        DERIVED    the gate in data/seo.json, applied to indexable
    canonical      DERIVED    the page states it; render.page() emits it
    title          DERIVED    the page states it
    description    DERIVED    render.meta_description, from the record
    schema         DERIVED    the JSON-LD blocks the page carries
    readiness      DERIVED    tools/seo.py, from the built page

That is the Data Integrity Rule applied to a publishing state: never author a
measurement, and you may author a classification.

AND A DEFAULT THAT IS NOT WRITTEN DOWN IS A DEFAULT NOBODY CAN ARGUE WITH.
`data/seo.json` carries the default status and the sitemap gate as data with a
reason on each, so changing either is a visible edit to a registry rather than
a line somebody moves in a renderer.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATUSES = ("published", "noindex")
GATES = ("indexable", "ready")

_cache = None


def registry():
    global _cache
    if _cache is None:
        with open(os.path.join(ROOT, "data", "seo.json"), encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def _canonical(path):
    """The route as the sitemap and the register spell it.

    ONE NORMALISER, BOTH SIDES. `page()` is handed "/europe/norway" and the
    build's own sitemap list is built from the written filename, so the two
    spellings of one route are "/x" and "/x/" and "/x/index.html". Every
    comparison in this module goes through here, because a register keyed on
    one spelling and consulted with another is a register that silently
    answers the default — which is this repository's most repeated fault and
    has stopped three real acquisitions.
    """
    p = path or "/"
    if p.endswith("index.html"):
        p = p[: -len("index.html")]
    if len(p) > 1:
        p = p.rstrip("/")
    return p or "/"


def status(path):
    reg = registry()
    row = reg.get("routes", {}).get(_canonical(path))
    if row:
        return row.get("status", reg["default"]["status"])
    return reg["default"]["status"]


def indexable(path):
    return status(path) != "noindex"


def robots_meta(path):
    """The tag, and only where it says something.

    A `<meta name="robots" content="index,follow">` on every page is a
    thousand copies of the behaviour a browser already has with no tag at
    all: it states the default, so it cannot be read as a decision, and it
    is weight on every document. The tag is emitted where it CHANGES
    something, which is the same reasoning that emits an advertising slot's
    markup only when a campaign is serving.

    `follow` rather than `none`: a page withheld from search is still a page
    whose links are worth crawling — taking a route out of the index is not
    a reason to strand everything it points at.
    """
    if indexable(path):
        return ""
    return '<meta name="robots" content="noindex,follow">\n'


def sitemap_gate():
    return registry().get("sitemap", {}).get("gate", "indexable")


def in_sitemap(path, *, ready=None):
    """Whether a route belongs in the published sitemap.

    `ready` is the readiness engine's verdict for this route and is consulted
    only under the `ready` gate — passed in rather than imported, because
    `tools/seo.py` reads the BUILT site and this module is called while the
    build is writing it. Nothing may read `site/` while anything is writing
    it, which this repository records as a rule about gates and is equally
    true of a renderer.
    """
    if not indexable(path):
        return False
    if sitemap_gate() == "ready":
        return ready is True
    return True
