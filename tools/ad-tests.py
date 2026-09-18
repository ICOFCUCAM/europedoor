#!/usr/bin/env python3
"""§29 of the advertising specification: the OFF state, and a simulated ON.

WHY THIS IS A SEPARATE SUITE. `checks.py` can only ever assert what the
built site and the registry say TODAY, which is that nothing is serving —
and a switch nobody has ever thrown is a code path nothing exercises, which
is this repository's most repeated failure: the focal point shipped as a
`style="` attribute the CSP forbids, the photograph pipeline would have
failed the build on photograph number one, and five dead `display`
declarations were each found in the first run where a photograph actually
rendered in that container. So the ON state is exercised here, against a
registry this suite constructs, before there is an advertiser.

AND IT NEVER WRITES. The simulation replaces `ads._cache` in memory — not a
temporary file, not a copy of `data/advertising.json` swapped in and out,
because a suite that edits the registry it is testing can leave the
repository in the state its own failure produced. The Media Desk's suite
learned the harder version of this: it renamed two licensed originals out of
the way and a later run overwrote them. Nothing to restore is stronger than
restoring carefully, and the last block asserts both the registry's bytes
and the built site are untouched by the run.
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from lib import ads as ADS          # noqa: E402
from lib import render as R         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data", "advertising.json")
OUT = os.path.join(ROOT, "site")

PASS = []
FAIL = []


def ok(label):
    PASS.append(label)


def bad(label, detail):
    FAIL.append(f"{label}: {detail}")


def expect(cond, label, detail=""):
    ok(label) if cond else bad(label, detail or "expected true")


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ── the OFF state, which is the shipped state ─────────────────────────────

def off_state():
    """Seven things that must be true while nothing is serving.

    Each is a different CONDITION rather than seven readings of one flag —
    the point §2 and §26 both make, and the one the sister repository paid
    for: its `status: 'active'` became inert the day a real ladder was built
    and guarding the wrong word is worse than guarding nothing.
    """
    expect(ADS.entity() is None, "1. no operating entity",
           f"entity is {ADS.entity()!r}")
    expect(ADS.load()["serving"]["enabled"] is False, "2. serving is off")
    expect(not any(ADS.flags().values()), "3. every feature flag is false",
           str({k: v for k, v in ADS.flags().items() if v}))
    expect(not any(p.get("enabled") for p in ADS.placements()),
           "4. every placement is disabled")
    expect(not any(s.get("enabled") for s in ADS.surfaces()),
           "5. every surface is disabled")
    expect(ADS.may_serve() is False, "6. may_serve() refuses with no campaign")
    expect(ADS.served() == [], "7. nothing would render anywhere")
    # AND THE RENDERER EMITS ZERO BYTES, on every surface the registry
    # declares rather than on one. A slot that returns "" for the homepage
    # and a container for a destination is the fourteen-call-sites failure
    # with two outcomes instead of two pictures.
    for s in ADS.surfaces():
        got = R.ad_slot(s["path"])
        expect(got == "", f"8. {s['path']} emits no advertising markup",
               f"{len(got)} bytes: {got[:80]!r}")


# ── the simulated ON state ────────────────────────────────────────────────

def configured(extra_campaign=None, **serving):
    """A registry with all five conditions satisfied, in memory only."""
    reg = json.loads(json.dumps(ADS.load()))
    reg["serving"]["entity"] = "TEST ENTITY LLC"
    reg["serving"]["enabled"] = True
    for k in reg["flags"]:
        if not k.startswith("$"):
            reg["flags"][k] = True
    for p in reg["placements"]:
        p["enabled"] = True
    for s in reg["surfaces"]:
        s["enabled"] = True
    reg["advertisers"] = [{"slug": "test-co", "name": "Test Co",
                           "host": "example.org", "enabled": True}]
    camp = {
        "slug": "test-spotlight",
        "advertiser": "test-co",
        "placement": "homepage_partner_spotlight",
        "status": "active",
        "insertion_order": "IO-0001",
        "targets": {},
        "creative": {
            "type": "card",
            "headline": "A week in the Dolomites",
            "description": "Presented by Test Co.",
            "cta_label": "See the week",
            "destination_url": "https://example.org/dolomites",
            "disclosure_label": "Sponsored",
        },
    }
    if extra_campaign:
        camp.update(extra_campaign)
    reg["campaigns"] = [camp] + ([] if extra_campaign is None else [])
    reg.update(serving)
    return reg


class simulated:
    """Swap the cache, and put it back whatever happens."""

    def __init__(self, reg):
        self.reg = reg

    def __enter__(self):
        self.was = ADS._cache
        ADS._cache = self.reg
        return self.reg

    def __exit__(self, *exc):
        ADS._cache = self.was
        return False


def on_state():
    with simulated(configured()) as reg:
        expect(ADS.may_serve(reg["campaigns"][0]) is True,
               "9. a fully configured campaign may serve",
               "five conditions satisfied and it still refuses")
        html = R.ad_slot("/")
        expect('class="adband' in html, "10. the slot renders a band")
        expect("Sponsored" in html, "11. the disclosure is in the markup",
               "a paid band with no disclosure is the one thing §17 forbids")
        expect('rel="sponsored nofollow noopener"' in html,
               "12. the paid link carries sponsored nofollow noopener")
        expect('target="_blank"' in html, "13. it opens in a new tab")
        expect('data-placement="homepage_partner_spotlight"' in html,
               "14. the band names the placement it was bought for")
        expect("A week in the Dolomites" in html, "15. the creative is drawn")
        # THE DISCLOSURE IS NOT SEPARABLE FROM THE THING IT DISCLOSES, which
        # is the Stay layer's own rule. Removing the label does not render a
        # band without one — it stops the build.
        noflag = configured()
        noflag["campaigns"][0]["creative"]["disclosure_label"] = "Best"
        with simulated(noflag):
            try:
                R.ad_slot("/")
            except ValueError as e:
                expect("disclosure_label" in str(e) or "Best" in str(e),
                       "16. a refused disclosure word stops the build",
                       str(e))
            else:
                bad("16. a refused disclosure word stops the build",
                    "it rendered")
        # AND A CREATIVE THAT COULD CARRY MARKUP NEVER REACHES A READER.
        for field, value, why in (
                ("headline", "<script>x</script>", "a tag in a creative"),
                ("destination_url", "http://example.org/x", "a non-https link"),
                ("destination_url", "https://evil.test/x", "an undeclared host"),
        ):
            hostile = configured()
            hostile["campaigns"][0]["creative"][field] = value
            with simulated(hostile):
                try:
                    R.ad_slot("/")
                except ValueError:
                    ok(f"17. {why} is refused")
                else:
                    bad(f"17. {why} is refused", "it rendered")
        # A SURFACE THE CAMPAIGN WAS NOT BOUGHT FOR SHOWS NOTHING, so a
        # placement cannot leak across the site by being enabled.
        with simulated(configured()):
            elsewhere = R.ad_slot("/europe/norway/fjord-norway/bergen")
            expect(elsewhere == "",
                   "18. a homepage campaign does not render on a destination",
                   f"{len(elsewhere)} bytes")
        # AND ONE CONDITION FALSE IS ENOUGH, for every condition the
        # mechanism declares rather than for five somebody chose. This is
        # the assertion the whole architecture rests on: a single flag is
        # never the gate, so each one alone must be able to refuse — and
        # reading `ads.conditions()` means a condition added tomorrow is
        # proved tomorrow, where a typed list of five would silently stop
        # covering the set.
        mutations = {
            "an operating entity exists":
                lambda r: r["serving"].update(entity=None),
            "serving is switched on":
                lambda r: r["serving"].update(enabled=False),
            "the global flag is set":
                lambda r: r["flags"].update(ADVERTISING_ENABLED=False),
            "a campaign exists to serve":
                lambda r: r.update(campaigns=[]),
            "its placement is enabled":
                lambda r: r["placements"][0].update(enabled=False),
            "that placement's own flag is set":
                lambda r: r["flags"].update(ADVERTISING_ENABLED=False),
            "the surface it sits on is enabled":
                lambda r: r["surfaces"][0].update(enabled=False),
            "the campaign is active":
                lambda r: r["campaigns"][0].update(status="paused"),
            "it carries a signed insertion order":
                lambda r: r["campaigns"][0].update(insertion_order=None),
        }
        declared = [label for label, _ in ADS.conditions()]
        expect(set(declared) == set(mutations),
               "19. every declared condition has a mutation proving it",
               f"unproved: {sorted(set(declared) - set(mutations))}")
        for label in declared:
            one = configured()
            mutations[label](one)
            with simulated(one):
                expect(R.ad_slot("/") == "",
                       f"20. \u2018{label}\u2019 alone stops everything",
                       "it rendered with a condition false")


def workflow():
    """§14: a business may never publish advertising instantly."""
    expect(ADS.may_transition("draft", "active") is False,
           "20. draft cannot jump to active")
    expect(ADS.may_transition("draft", "pending_review") is True,
           "21. draft may be submitted for review")
    expect(ADS.may_transition("draft", "banana") is False,
           "22. a transition the table does not name is refused")
    expect(ADS.transition_needs_reason("rejected") is True,
           "23. a rejection carries a reason")


def untouched(before_reg, before_pages):
    """The suite's own footprint, asserted rather than assumed.

    UNTOUCHED MEANS UNCHANGED, NOT EMPTY — the desk suite's own recorded
    correction, where an assertion written as `reg_now == {}` went red the
    day eleven photographs merged, for a desk that had got better.
    """
    expect(digest(REG) == before_reg,
           "24. data/advertising.json is byte-identical after the run")
    expect(marker_pages() == before_pages,
           "25. no page gained an advertising slot while the suite ran",
           f"{marker_pages()} pages carry one")


def marker_pages():
    n = 0
    for base, _, files in os.walk(OUT):
        for f in files:
            if f.endswith(".html"):
                body = open(os.path.join(base, f), encoding="utf-8").read()
                if 'class="adband' in body or "data-placement=" in body:
                    n += 1
    return n


def main():
    before_reg, before_pages = digest(REG), marker_pages()
    off_state()
    on_state()
    workflow()
    untouched(before_reg, before_pages)
    for label in PASS:
        print(f"  ok    {label}")
    for f in FAIL:
        print(f"  FAIL  {f}")
    print()
    if FAIL:
        print(f"{len(FAIL)} failure(s) of {len(PASS) + len(FAIL)}")
        return 1
    print(f"all {len(PASS)} advertising assertions passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
