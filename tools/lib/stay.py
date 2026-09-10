"""The Stay layer: accommodation as a referral, never as inventory.

WHAT THIS MODULE IS FOR. EuropeDoor is the discovery layer and a booking
provider is the fulfilment layer, and the whole design problem is keeping
that boundary visible to a reader rather than only true in a contract. A
generic hotel widget collapses it: it looks like this site is selling you a
room, it fills a destination page with somebody else's card grid, and it
publishes prices and ratings this atlas does not hold and has refused to
hold since the schema was written.

So a provider here is a LINK MECHANISM AND A CREDENTIAL, and nothing else:

    search_url + place_param + fixed_params  ->  a deep link to their search
    partner_param + partner_id               ->  the referral, when we have one

That is all `data/stay.json` may declare, and it is deliberately not enough
to draw a hotel. There is no field for a room, a price, an availability
window or a rating, so no page can print one by accident, and `checks.py`
asserts the same refusal against the shipped HTML because a source-level
promise passes the day somebody adds a field.

TWO HONEST STATES, AND A CHECK THAT KEEPS THEM APART. A partner id is issued
only to an approved partner account, which needs the operating entity that
`docs/legal-position.md` section 3 records as not yet incorporated. So today
`partner_id` is null and the link is a plain outbound link that earns
nothing; the disclosure says exactly that, and `rel` says `nofollow noopener`
rather than `sponsored`. The day the id lands in the registry the same
builder emits the tracked link, the disclosure flips to the commission
sentence and `rel` gains `sponsored`. One mechanism, two states, and the
state is read off the credential rather than typed into a page.

A DISCLOSURE THAT ONLY APPEARS WHEN WE ARE PAID IS AN ADVERTISEMENT WITH A
CONSCIENCE. Both states carry one, because what a reader needs to know is
what our interest in the link is — and "we earn nothing from this" is as much
an answer to that question as "we may earn a commission".
"""

import json
import os
import urllib.parse

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data")

_CACHE = {}


def load():
    """The registry, read once."""
    if "reg" not in _CACHE:
        path = os.path.join(DATA, "stay.json")
        if not os.path.exists(path):
            _CACHE["reg"] = {"providers": [], "destinations": []}
        else:
            with open(path, encoding="utf-8") as fh:
                _CACHE["reg"] = json.load(fh)
    return _CACHE["reg"]


def providers():
    """The enabled providers, in the order the registry declares them.

    The first is the primary and gets the button; any others are a quieter
    line beside it. That ordering is data, so adding Expedia is one field in
    `data/stay.json` and no change to `pages.py` — which is the whole point
    of the abstraction and is why `enabled` exists rather than a page-level
    list of provider slugs.
    """
    return [p for p in load().get("providers", []) if p.get("enabled")]


def context(cid):
    """The authored accommodation context for one destination, or None.

    `accommodation_context` is the brief's own name for this and it is the
    right one: it is not a list of accommodation, it is what this atlas knows
    about staying HERE — which is the only thing it has that a booking site
    does not. Coverage is declared rather than universal, because the
    exemplar is one destination on purpose: the grammar is derived from a page
    that has been rendered and looked at, not from a template applied to 319
    of them.
    """
    for row in load().get("accommodation_context", []):
        if row.get("city") == cid:
            return row
    return None


# THE HEADING IS NOT "HOTELS", AND IT IS NOT ONE STRING EITHER.
#
# "Hotels in Chamonix" is OTA language and it is also the wrong promise: what
# is being offered is a base, and a base means something different in a
# valley, on an island and in a capital. So the heading is derived from what
# the destination IS — the same `city_type` classification and the same
# relief measurement the rest of the site already uses — and a covered
# destination may override it with an authored line, because a headline is
# editorial work.
#
# Derived rather than authored-only for a reason this repository has already
# paid for once: 319 authored headings is 319 chances to write "Hotels", and
# a default that comes from the data cannot drift from the place.
HEADINGS = {
    "island": "Stay on the island",
    "village": "Stay in the village",
    "valley": "Stay in the valley",
    "capital": "Stay in the city",
    "city": "Stay in the city",
    "town": "Make a base here",
    "site": "Stay near the site",
    "park": "Stay at the edge of the park",
}


def heading(row, city, mountainous=False):
    """The section heading for one destination's Stay layer."""
    if row.get("heading"):
        return row["heading"]
    if mountainous:
        return "Sleep below the peaks"
    return HEADINGS.get(city.get("city_type") or "", "Where to stay")


# THE CARD, AND WHY THERE IS NOT ONE YET.
#
# The brief's mock-up is a card: a photograph, a property name, a 9.1, "From
# EUR 184" and "View availability". Every one of those five is something this
# atlas does not hold and has refused to hold since the schema was written —
# `rating`, `price`, `availability` and a photograph with no licence row are
# four separate refusals, each enforced twice.
#
# They are not refused because a card is a bad idea. They are refused because
# there is no honest source for them under a LINK-ONLY affiliate mechanism,
# which is the only mechanism available here: Expedia's creator programme
# offers tracked links and no general API at all, and Booking.com's Demand
# API — the one interface that would return a property with an attributed
# booking URL — is for managed partners only, which needs the approved
# partner account, which needs the entity.
#
# So the contract is written and the renderer is not, and this function is
# the seam. It returns nothing today, and a page that gets nothing draws the
# editorial grammar instead of an empty frame — because "present but empty"
# says "we have this" and then does not, which is the pattern `checks.py`
# already refuses in JSON-LD.
def inventory(provider, cid):
    """Accommodation offers for one destination from one provider, or [].

    ALWAYS [] TODAY. The trigger that changes it is named per provider in
    `data/stay.json` under `inventory_api`; when one of them opens, this is
    the only function that learns about it, and what it must return is a
    property name, a canonical provider URL carrying our attribution, and
    whatever of price and rating THAT PROVIDER publishes with its own
    figure attached — never a number this atlas computed, and never one it
    stored.
    """
    return []


def tracked(p):
    """Whether this provider's link carries our referral credential."""
    return bool(p.get("partner_id"))


def compare(t_name, c_name):
    """The provider row: every enabled provider, for a reader who wants to check.

    The brief calls this "Compare places to stay" and it is the honest form of
    a multi-provider referral — a reader who is ready to book is comparing,
    and pretending there is one right provider would be an opinion about
    inventory this atlas cannot see. It renders only when there are at least
    two enabled providers; one provider is a button, not a comparison.
    """
    provs = providers()
    return provs if len(provs) > 1 else []


def deep_link(p, place, country):
    """A deep link into the provider's own search for one place.

    The search term is the destination and its country, because "Chamonix"
    alone is ambiguous on a global site and this atlas already holds the
    disambiguation. Nothing else is passed: no dates, no occupancy, no price
    band, no sort order. A prefilled date range would be this page guessing
    at a trip it knows nothing about, and a prefilled sort would be this page
    having an opinion about their inventory, which is precisely the opinion
    it has no basis for.
    """
    params = dict(p.get("fixed_params") or {})
    params[p["place_param"]] = f"{place}, {country}"
    if tracked(p):
        params[p["partner_param"]] = p["partner_id"]
    return p["search_url"] + "?" + urllib.parse.urlencode(params)


def rel(p):
    """The `rel` for an outbound stay link.

    `nofollow` and `noopener` always: this is an outbound commercial link
    opened in a new context and neither of those is conditional. `sponsored`
    ONLY when the link actually carries our credential — it is the
    machine-readable half of the disclosure, and declaring it on a link that
    earns nothing is as wrong as omitting it from one that does.
    """
    return "sponsored nofollow noopener" if tracked(p) else "nofollow noopener"


def disclosure(p):
    """One sentence, matched to the state the credential puts us in."""
    if tracked(p):
        return (f"EuropeDoor may earn a commission if you book after following "
                f"this link. It costs you nothing extra, and it does not change "
                f"a word of what this page says about {p['name']} or about here.")
    return (f"This is a plain link. EuropeDoor is not a {p['name']} partner and "
            f"earns nothing if you book — the accommodation referral is designed "
            f"and not yet activated.")
