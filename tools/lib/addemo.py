"""A registry with every condition satisfied, in memory, for looking at.

ONE IMPLEMENTATION OF THE SIMULATED ON STATE, because `ad-tests.py` proves
it and `ad-preview.py` photographs it, and two copies of a fixture is two
chances for the thing that was tested and the thing that was looked at to
differ — which is the `--pick 3` failure in the acquisition pipeline, where
a position rather than an identity meant the picture somebody approved and
the picture that arrived could differ silently.

Nothing here is data. It is a fixture: `data/advertising.json` holds an
empty campaign table and this builds a dict beside it, so the file on disk
is never written and there is nothing to restore. `ad-tests.py` asserts
that, by hashing the registry before and after its own run.
"""

import json

from . import ads


def registry(campaigns=None):
    """Every one of `ads.conditions()` satisfied, and two campaigns."""
    reg = json.loads(json.dumps(ads.load()))
    reg["serving"]["entity"] = "EXAMPLE OPERATING ENTITY LLC"
    reg["serving"]["enabled"] = True
    for k in list(reg["flags"]):
        if not k.startswith("$"):
            reg["flags"][k] = True
    for p in reg["placements"]:
        p["enabled"] = True
    for s in reg["surfaces"]:
        s["enabled"] = True
    reg["advertisers"] = [
        {"slug": "example-rail", "name": "Example Rail",
         "host": "example.org", "enabled": True},
    ]
    reg["campaigns"] = campaigns if campaigns is not None else [
        campaign("homepage_partner_spotlight",
                 "Nine countries on one ticket",
                 "A month of European rail, presented by Example Rail.",
                 "See the routes"),
        campaign("destination_featured_partner",
                 "Two hours from Bergen by rail",
                 "The Bergen line, presented by Example Rail.",
                 "Look at the timetable"),
    ]
    return reg


def campaign(placement, headline, description, cta,
             disclosure="Sponsored", slug=None):
    return {
        "slug": slug or placement,
        "advertiser": "example-rail",
        "placement": placement,
        "status": "active",
        "insertion_order": "IO-EXAMPLE-0001",
        "targets": {},
        "creative": {
            "type": "card",
            "headline": headline,
            "description": description,
            "cta_label": cta,
            "destination_url": "https://example.org/europe",
            "disclosure_label": disclosure,
        },
    }


class simulated:
    """Swap the cache, and put it back whatever happens."""

    def __init__(self, reg=None):
        self.reg = reg if reg is not None else registry()

    def __enter__(self):
        self.was = ads._cache
        ads._cache = self.reg
        return self.reg

    def __exit__(self, *exc):
        ads._cache = self.was
        return False
