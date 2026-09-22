"""Who must be credited on a page, and which document says so.

THE PROVENANCE REGISTER IS NOT A VISUAL DESIGN SYSTEM, and for a while this
product behaved as though it were: a photograph arrived carrying a
photographer, a provider, a source URL, a licence, a SHA-256 and two dates,
and every one of those reached the editorial surface because it existed.
Section 01 of the homepage ended in six photographer names and the word
Pexels, section 03 in nine, section 04 in four. That is an asset-management
system wearing an atlas's clothes.

The architecture this replaces it with has four layers and they are not
interchangeable:

    provider / API terms   what the documents actually say
            |
    provenance register    the facts, separated, each with its quote
            |
    compliance layer       what is OWED, per provider, per route
            |
    editorial renderer     what a visitor is shown

and the renderer asks the layer above it rather than reading the register.

FOUR FACTS, NOT ONE BOOLEAN. `docs/data-licenses/photo-providers.json` had a
single `attribution` field whose stated VALUE was taken from the API
documentation's Guidelines while its NAME read like a licence obligation —
so the register said attribution was required, the licence said the opposite,
and both were quoting real text. Moving that ambiguity into one central
function would have centralised it rather than removed it. The four facts
are separate because they have separate answers and separate evidence:

    license_attribution_required    the ordinary content licence
    api.attribution_guideline       the API documentation's Guidelines
    api.scope                       who that guideline binds
    internal_provenance_required    what the register must hold regardless

THE SCOPE IS `unresolved` AND THAT IS A FINDING RATHER THAN A GAP. Pexels'
archived licence says *"Attribution is not required. Giving credit to the
photographer or Pexels is not necessary but always appreciated."* Its
archived API documentation says *"Whenever you are doing an API request make
sure to show a prominent link to Pexels."* EuropeDoor acquires through the
API — every one of the register's rows carries a `provider_photo_id` and an
`images.pexels.com` original, both of which only the API returns — and makes
that request once, inside a workflow, where nothing is displayed to anybody;
a reader's browser never touches Pexels, because the CSP is `default-src
'none'` with `img-src 'self' data:` and every file is served from this
origin. Whether *doing an API request* binds the requesting application or
any surface showing what it fetched is a question the archived text does not
answer, and a renderer is not the place to decide it.

So while the scope is unresolved this layer answers SHOW, and the pages look
exactly as they did. That is the conservative answer and it is deliberately
the one that costs nothing to reverse: when the scope is established, one
field moves and every surface follows, because there is one decision here
and not six.

AND THE ACCOUNT-LEVEL LIMIT IS `unknown`, WHICH IS NOT `no`. The same
document says *"You may contact us to request a higher limit, but please
include examples ... that clearly shows your use of the API with
attribution."* Nothing in this repository records an application for one,
and an absence of evidence in a repository is not evidence of absence: that
is an account fact held by the provider and the owner. It is recorded as
unknown rather than inferred from silence.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = os.path.join(ROOT, "docs", "data-licenses", "photo-providers.json")

# What this layer may answer. SHOW and HIDE are decisions; UNRESOLVED is the
# state where the evidence does not support one, and it resolves to SHOW —
# stated as its own value rather than collapsed into SHOW, because a check
# and a reader both need to tell "we established this" from "we have not".
SHOW, HIDE, UNRESOLVED = "show", "hide", "unresolved"

_CACHE = {}


def providers():
    """The register, read once."""
    if "v" in _CACHE:
        return _CACHE["v"]
    try:
        with open(GATE, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        raw = {}
    _CACHE["v"] = {k: v for k, v in raw.items() if not k.startswith("$")}
    return _CACHE["v"]


def layers(slug):
    """The four separated facts for one provider, or None if it has none."""
    return (providers().get(slug) or {}).get("attribution_layers")


def _flag(block, key):
    """A gate answer, whether it is a bare boolean or a `{value, quote}` block.

    EVERY ANSWER IN THIS GATE IS A BLOCK, AND A BLOCK IS TRUTHY. The first
    version of `visitor_attribution` read `lay.get(...)` directly, so
    `{"value": false, "quote": "No permission needed"}` tested TRUE and
    Unsplash was reported as requiring attribution by its licence — which is
    the exact opposite of the sentence quoted inside the block being read.
    The shape is not incidental: answers are blocks so that `c_gate_quotes`
    can assert each quote appears in the archived snapshot of the page it
    cites, and a bare boolean would have no evidence attached to it. So the
    reader has to know both shapes, and this is the one place that does.
    """
    v = (block or {}).get(key)
    if isinstance(v, dict):
        return v.get("value")
    return v


def visitor_attribution(slug):
    """Whether a VISITOR-FACING credit is owed for this provider, and why.

    Returns (decision, reason). The reason is the sentence a person reads in
    a check message or a commit, so it names the document rather than the
    field: a decision whose justification is a JSON key is a decision nobody
    can audit.
    """
    lay = layers(slug)
    if not lay:
        # A provider with no separated facts has not been through the gate.
        # Showing is the only safe answer, and it is also what shipped.
        return SHOW, (f"{slug} has no attribution_layers block in the "
                      f"licence gate, so nothing here has established what "
                      f"its terms require")
    api = lay.get("api") or {}
    if api.get("used") and api.get("attribution_guideline"):
        scope = api.get("scope")
        if scope == "requesting_application":
            pass          # falls through to the licence answer below
        elif scope == "any_display_surface":
            return SHOW, (f"{slug}'s API guideline binds any surface showing "
                          f"content obtained through the API")
        else:
            return UNRESOLVED, (
                f"{slug} is acquired through its API and the API guideline "
                f"asks for a prominent link, but whether that binds the "
                f"requesting application or any display surface is not "
                f"settled by the archived terms")
    if _flag(lay, "license_attribution_required"):
        return SHOW, f"{slug}'s content licence requires attribution"
    return HIDE, (f"{slug}'s content licence does not require attribution and "
                  f"no API requirement reaches a display surface")


def show_visitor_credit(slugs):
    """Does any provider in this set owe, or possibly owe, a visible credit.

    The set rather than one provider, because a band draws photographs from
    whatever the register holds and one unresolved provider decides the band.
    """
    for slug in sorted(set(slugs)):
        decision, _why = visitor_attribution(slug)
        if decision in (SHOW, UNRESOLVED):
            return True
    return False


def internal_only(slug):
    """True where the register must hold provenance and a page must not show it.

    This is the field that keeps the two questions apart: a photograph whose
    licence needs no credit still needs a photographer, a source, a hash and
    a date in `data/images.json`, because that is how *this file is the file
    that was licensed* stays checkable rather than a sentence.
    """
    lay = layers(slug) or {}
    return (bool(_flag(lay, "internal_provenance_required"))
            and visitor_attribution(slug)[0] == HIDE)
