"""Load the EuropeDoor dataset and refuse to hand back anything malformed.

Every page on the site is generated from data/, so a typo here becomes a
broken page there. The validator is deliberately loud and deliberately
strict: it is cheaper to fail the build than to publish a city that claims
to be in a region that does not exist.
"""

from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BUDGETS = ("low", "moderate", "high")
# The specification's examples, plus the ones Europe actually keeps producing.
PLACE_KINDS = (
    "museum", "castle", "church", "monastery", "mountain", "waterfall",
    "beach", "monument", "archaeological-site", "park", "viewpoint",
    "bridge", "market", "garden", "island", "cave", "street", "square",
    "lighthouse", "quarter", "ruin", "theatre", "library", "bath",
)
PLACE_SEASONS = ("year-round", "summer", "winter", "spring-autumn", "weather-dependent")
# The specification's event categories (§33).
EVENT_KINDS = ("festival", "concert", "sport", "exhibition", "religious",
               "cultural", "food", "market", "seasonal")
# The specification's verification ladder (§38). Absent means unverified,
# which is the honest state of every record today.
# What kind of thing was consulted. The distinction that matters is whether
# the source is answerable for the fact: a border authority is answerable for
# its own entry rules in a way that a newspaper reporting them is not.
# What a photograph must carry before it can be published. There is no
# "unknown" and no default: an image whose licence nobody wrote down is an
# image nobody can defend, and the cheapest moment to refuse it is the moment
# it is added.
IMAGE_REQUIRED = ("file", "alt", "photographer", "source", "licence")

# Licences we will actually publish under. A permissive list would make this
# field decorative; the point is that adding a new one is a decision somebody
# has to make on purpose.
IMAGE_LICENCES = ("CC0", "CC-BY-4.0", "CC-BY-SA-4.0", "Pexels", "Unsplash",
                  "commissioned", "licensed-stock", "owner-supplied")

SOURCE_KINDS = ("official", "operator", "municipal", "press", "editorial")

VERIFICATION_STATUS = ("unverified", "machine-reviewed", "editor-reviewed",
                       "business-verified", "officially-sourced")
BLOCS = ("eu", "schengen", "eurozone", "eea", "cta")
ADVISORY_LEVELS = ("caution", "avoid")


class DataError(Exception):
    pass


class Problems:
    """Collects every complaint rather than dying on the first one."""

    def __init__(self):
        self.items = []

    def add(self, where, message):
        self.items.append(f"{where}: {message}")

    def require(self, cond, where, message):
        if not cond:
            self.add(where, message)
        return cond

    def raise_if_any(self):
        if self.items:
            raise DataError(
                "%d data problem(s):\n  - %s" % (len(self.items), "\n  - ".join(self.items))
            )


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load():
    """Return the whole dataset, cross-linked and validated."""
    tax = _read(os.path.join(DATA, "taxonomy.json"))
    interests = {i["slug"]: i for i in tax["interests"]}
    months = set(tax["months"])
    kinds = tax["experience_kinds"]
    categories = {c["slug"]: c for c in tax.get("categories", [])}

    p = Problems()

    countries = {}
    files = sorted(os.listdir(os.path.join(DATA, "countries")))
    for fn in files:
        if not fn.endswith(".json"):
            continue
        c = _read(os.path.join(DATA, "countries", fn))
        where = "countries/" + fn
        for key in (
            "code", "slug", "name", "macro", "capital", "currency", "languages",
            "blocs", "tagline", "summary", "interests", "budget", "daily_eur",
            "season", "getting_around", "food", "festivals", "know", "regions",
        ):
            p.require(key in c, where, f"missing key {key!r}")
        if "slug" not in c:
            continue
        p.require(SLUG.match(c["slug"]), where, "slug is not a slug")
        p.require(fn == c["slug"] + ".json", where, "filename must match slug")
        p.require(c["slug"] not in countries, where, "duplicate country slug")
        p.require(c.get("budget") in BUDGETS, where, "budget must be one of " + "/".join(BUDGETS))
        for b in c.get("blocs", []):
            p.require(b in BLOCS, where, f"unknown bloc {b!r}")
        for i in c.get("interests", []):
            p.require(i in interests, where, f"unknown interest {i!r}")
        rng = c.get("daily_eur")
        p.require(
            isinstance(rng, list) and len(rng) == 2 and 0 < rng[0] < rng[1],
            where, "daily_eur must be [low, high] with low < high",
        )
        season = c.get("season", {})
        for band in ("peak", "shoulder"):
            for m in season.get(band, []):
                p.require(m in months, where, f"unknown month {m!r} in season.{band}")
        for f in c.get("festivals", []):
            p.require(f.get("month") in months, where, f"festival {f.get('name')!r}: bad month")
            p.require(f.get("kind") in EVENT_KINDS, where,
                      f"festival {f.get('name')!r}: kind must be one of {'/'.join(EVENT_KINDS)}")
        p.require(bool(c.get("timezone")), where, "a country needs a time zone")
        # Fact verification. Absent means never checked, and that is the
        # truthful state of almost every record — /sources/freshness publishes
        # it rather than letting the silence read as confidence.
        ch = c.get("checked")
        if ch:
            p.require(ISO_DATE.match(ch.get("on", "")), where, "checked.on must be YYYY-MM-DD")
            p.require(bool(ch.get("by")), where, "a check needs a name against it")
            p.require(ch.get("status", "editor-reviewed") in VERIFICATION_STATUS, where,
                      f"checked.status must be one of {'/'.join(VERIFICATION_STATUS)}")
            for src in ch.get("sources", []):
                for k in ("what", "where", "kind"):
                    p.require(bool(src.get(k)), where,
                              f"each source needs {k} — what was checked, where, and what kind of source")
                p.require(src.get("kind") in SOURCE_KINDS, where,
                          f"source kind must be one of {'/'.join(SOURCE_KINDS)}")
                # A URL is optional: the best source for a cost band is
                # sometimes a price list in a window, and demanding a link
                # would push a checker towards whatever happened to have one.
                # But if there is one it has to be a real one.
                if src.get("url"):
                    p.require(src["url"].startswith("https://"), where,
                              f"source url must be https:// — got {src['url']!r}")
            # Confidence is derived from the status and the sources, never
            # authored. A field somebody can type is a field somebody will
            # type "high" into.
            p.require("confidence" not in ch, where,
                      "confidence is derived from status and sources, not authored — "
                      "see verification_of() in tools/lib/pages.py")

        adv = c.get("advisory")
        if adv:
            p.require(adv.get("level") in ADVISORY_LEVELS, where, "advisory.level must be caution/avoid")
            p.require(bool(adv.get("note")), where, "an advisory needs a note")

        seen_regions = set()
        for r in c.get("regions", []):
            rw = f"{where} > {r.get('slug')}"
            p.require(SLUG.match(r.get("slug", "")), rw, "region slug is not a slug")
            p.require(r["slug"] not in seen_regions, rw, "duplicate region slug")
            seen_regions.add(r.get("slug"))
            for key in ("name", "summary", "interests", "cities"):
                p.require(key in r, rw, f"missing key {key!r}")
            for i in r.get("interests", []):
                p.require(i in interests, rw, f"unknown interest {i!r}")
            p.require(len(r.get("cities", [])) >= 1, rw, "a region needs at least one city")
            seen_cities = set()
            for t in r.get("cities", []):
                tw = f"{rw} > {t.get('slug')}"
                p.require(SLUG.match(t.get("slug", "")), tw, "city slug is not a slug")
                p.require(t["slug"] not in seen_cities, tw, "duplicate city slug")
                seen_cities.add(t.get("slug"))
                for key in ("name", "lat", "lon", "summary", "interests", "nights", "highlights"):
                    p.require(key in t, tw, f"missing key {key!r}")
                p.require(34.0 <= t.get("lat", 0) <= 79.0, tw, "lat looks off the map for Europe")
                # 79 rather than 72 because Longyearbyen, at 78.2, is a real
                # place people travel to and the first thing this bound rejected.
                p.require(-26.0 <= t.get("lon", 0) <= 50.0, tw, "lon looks off the map for Europe")
                n = t.get("nights")
                p.require(
                    isinstance(n, list) and len(n) == 2 and 1 <= n[0] <= n[1] <= 7,
                    tw, "nights must be [min, max] within 1..7",
                )
                for i in t.get("interests", []):
                    p.require(i in interests, tw, f"unknown interest {i!r}")
                p.require(len(t.get("highlights", [])) >= 2, tw, "give a city at least two highlights")
                # Places: the specification's entity below a destination.
                # Opening hours, prices and official links are deliberately
                # absent rather than invented — see docs/data-model.md.
                seen_places = set()
                for pl in t.get("places", []):
                    pw = f"{tw} > place/{pl.get('slug')}"
                    p.require(SLUG.match(pl.get("slug", "")), pw, "place slug is not a slug")
                    p.require(pl["slug"] not in seen_places, pw, "duplicate place slug")
                    seen_places.add(pl.get("slug"))
                    for key in ("name", "kind", "summary", "lat", "lon", "duration", "season"):
                        p.require(key in pl, pw, f"missing key {key!r}")
                    p.require(pl.get("kind") in PLACE_KINDS, pw,
                              f"unknown place kind {pl.get('kind')!r}")
                    p.require(pl.get("season") in PLACE_SEASONS, pw,
                              f"season must be one of {'/'.join(PLACE_SEASONS)}")
                    p.require(34.0 <= pl.get("lat", 0) <= 79.0, pw, "lat off the map")
                    p.require(-26.0 <= pl.get("lon", 0) <= 50.0, pw, "lon off the map")
                    for volatile in ("hours", "price", "website", "phone"):
                        p.require(volatile not in pl, pw,
                                  f"{volatile!r} is volatile and must not be authored "
                                  "unverified — see docs/data-model.md")

                for e in t.get("experiences", []):
                    ew = f"{tw} > {e.get('slug')}"
                    p.require(SLUG.match(e.get("slug", "")), ew, "experience slug is not a slug")
                    p.require(e.get("kind") in kinds, ew, f"unknown experience kind {e.get('kind')!r}")
                    p.require(e.get("band") in BUDGETS, ew, "experience band must be low/moderate/high")
                    p.require(bool(e.get("summary")), ew, "an experience needs a summary")
        countries[c["slug"]] = c

    # Macro regions own countries; every country must be owned exactly once.
    listed = []
    for m in tax["macros"]:
        for cs in m["countries"]:
            listed.append(cs)
            if cs in countries:
                countries[cs]["macro_slug"] = m["slug"]
                countries[cs]["macro_name"] = m["name"]
            else:
                p.add("taxonomy", f"macro {m['slug']} lists unknown country {cs!r}")
    for cs in countries:
        p.require(cs in listed, "taxonomy", f"country {cs!r} belongs to no macro region")
    p.require(len(listed) == len(set(listed)), "taxonomy", "a country is listed in two macro regions")

    themes = _read(os.path.join(DATA, "themes.json"))["themes"]
    stories = _read(os.path.join(DATA, "stories.json"))["stories"]
    journeys = _read(os.path.join(DATA, "journeys.json"))["journeys"]
    fund = _read(os.path.join(DATA, "fund.json"))["projects"]
    providers = _read(os.path.join(DATA, "providers.json"))

    index = city_index(countries)
    seen_j = set()
    for j in journeys:
        jw = "journeys/" + str(j.get("slug"))
        p.require(SLUG.match(j.get("slug", "")), jw, "journey slug is not a slug")
        p.require(j["slug"] not in seen_j, jw, "duplicate journey slug")
        seen_j.add(j.get("slug"))
        for key in ("name", "strapline", "summary", "days", "budget", "interests", "months",
                    "legs", "difficulty", "transport", "accommodation", "pack", "start", "end",
                    "creator"):
            p.require(key in j, jw, f"missing key {key!r}")
        p.require(j.get("difficulty") in ("easy", "moderate", "demanding"), jw,
                  "difficulty must be easy/moderate/demanding")
        # This one exists because difficulty and budget share three of their
        # words, and a journey shipped with budget="demanding" for exactly
        # that reason.
        p.require(j.get("budget") in BUDGETS, jw,
                  "budget must be low/moderate/high, not a difficulty")
        p.require(j.get("accommodation") in ("guesthouse", "hotel", "mixed"), jw,
                  "accommodation must be guesthouse/hotel/mixed")
        p.require(len(j.get("pack", [])) >= 3, jw, "a journey needs at least three packing notes")
        p.require(len(j.get("transport", [])) >= 1, jw, "a journey needs a transport mode")
        for i in j.get("interests", []):
            p.require(i in interests, jw, f"unknown interest {i!r}")
        for m in j.get("months", []):
            p.require(m in months, jw, f"unknown month {m!r}")
        p.require(len(j.get("legs", [])) >= 3, jw, "a journey needs at least three legs")
        for leg in j.get("legs", []):
            p.require(leg.get("city") in index, jw, f"leg points at unknown city {leg.get('city')!r}")
            p.require(isinstance(leg.get("nights"), int) and leg["nights"] >= 1, jw, "leg needs nights")
            p.require(bool(leg.get("why")), jw, f"leg {leg.get('city')} needs a why")
        p.require(j.get("start") == j["legs"][0]["city"], jw, "start must be the first leg")
        p.require(j.get("end") == j["legs"][-1]["city"], jw, "end must be the last leg")
        total = sum(l.get("nights", 0) for l in j.get("legs", []))
        p.require(total == j.get("days", -1) - 1, jw,
                  f"legs total {total} nights but the journey claims {j.get('days')} days")

    seen_t = set()
    for t in themes:
        tw = "themes/" + str(t.get("slug"))
        p.require(SLUG.match(t.get("slug", "")), tw, "theme slug is not a slug")
        p.require(t["slug"] not in seen_t, tw, "duplicate theme slug")
        seen_t.add(t.get("slug"))
        for key in ("name", "strapline", "summary", "interests", "stops"):
            p.require(key in t, tw, f"missing key {key!r}")
        for i in t.get("interests", []):
            p.require(i in interests, tw, f"unknown interest {i!r}")
        p.require(len(t.get("stops", [])) >= 4, tw, "a theme needs at least four stops")
        for stop in t.get("stops", []):
            p.require(stop.get("city") in index, tw, f"stop points at unknown city {stop.get('city')!r}")
            p.require(bool(stop.get("why")), tw, f"stop {stop.get('city')} needs a why")

    seen_s = set()
    for st in stories:
        sw = "stories/" + str(st.get("slug"))
        p.require(SLUG.match(st.get("slug", "")), sw, "story slug is not a slug")
        p.require(st["slug"] not in seen_s, sw, "duplicate story slug")
        seen_s.add(st.get("slug"))
        for key in ("title", "section", "standfirst", "reading", "body",
                    "author", "tags", "published", "updated"):
            p.require(key in st, sw, f"missing key {key!r}")
        p.require(ISO_DATE.match(st.get("published", "")), sw, "published must be YYYY-MM-DD")
        p.require(ISO_DATE.match(st.get("updated", "")), sw, "updated must be YYYY-MM-DD")
        p.require(len(st.get("tags", [])) >= 2, sw, "a story needs at least two tags")
        p.require(len(st.get("body", [])) >= 4, sw, "a story needs at least four paragraphs")
        for cid in st.get("places", []):
            p.require(cid in index, sw, f"story points at unknown city {cid!r}")

    seen_f = set()
    for f in fund:
        fw = "fund/" + str(f.get("slug"))
        p.require(SLUG.match(f.get("slug", "")), fw, "project slug is not a slug")
        p.require(f["slug"] not in seen_f, fw, "duplicate project slug")
        seen_f.add(f.get("slug"))
        for key in ("name", "theme", "country", "summary", "need", "status", "partner"):
            p.require(key in f, fw, f"missing key {key!r}")
        p.require(f.get("country") in countries, fw, f"unknown country {f.get('country')!r}")
        p.require(f.get("status") in ("listed", "in-progress", "complete"), fw, "bad status")
        p.require("amount" not in f and "raised" not in f and "goal" not in f, fw,
                  "the Fund carries no money at MVP — see docs/europe-fund.md")

    for prov in providers["providers"]:
        pw = "providers/" + str(prov.get("slug"))
        for key in ("name", "kind", "city", "country", "summary", "tier", "checks"):
            p.require(key in prov, pw, f"missing key {key!r}")
        p.require(prov.get("tier") in ("applied", "reviewed", "verified"), pw, "bad tier")
        p.require(prov.get("country") in countries, pw, f"unknown country {prov.get('country')!r}")

    for cat in categories.values():
        cw = "taxonomy/categories/" + cat["slug"]
        for i in cat.get("interests", []):
            p.require(i in interests, cw, f"unknown interest {i!r}")
        seen_sub = set()
        for sub in cat.get("subs", []):
            p.require(SLUG.match(sub.get("slug", "")), cw, "subcategory slug is not a slug")
            p.require(sub["slug"] not in seen_sub, cw, "duplicate subcategory")
            seen_sub.add(sub["slug"])
            p.require(len(sub.get("keywords", [])) >= 2, cw,
                      f"{sub['slug']}: a keyword rule needs at least two terms")
        p.require(bool(cat.get("subs")) or bool(cat.get("derived")), cw,
                  "a category needs sub-categories or a derivation rule")

    # The photograph register.
    #
    # This block MUST stay above p.raise_if_any(). The first version sat
    # below it, next to the return, and every complaint it collected was
    # discarded unread — a row with no licence at all passed `build.py
    # check` cleanly. A validator that runs after the raise is not a
    # validator, it is a list nobody opens.
    images = _read(os.path.join(DATA, "images.json")).get("images", {})
    for key, row in sorted(images.items()):
        where = f"images.json > {key}"
        for field in IMAGE_REQUIRED:
            p.require(bool(row.get(field)), where,
                      f"missing {field!r} — no photograph is published without a "
                      "photographer, a source and a licence")
        p.require(row.get("licence") in IMAGE_LICENCES, where,
                  f"licence must be one of {'/'.join(IMAGE_LICENCES)}")
        p.require(str(row.get("source", "")).startswith("https://"), where,
                  "source must be an https URL you can open to check the licence")
        # Alt text is a caption for someone who cannot see the photograph,
        # not a keyword field. "Bergen" is the page title, not a description.
        p.require(len(str(row.get("alt", ""))) >= 12, where,
                  "alt must describe the photograph, not repeat the place name")
        focal = row.get("focal", [50, 50])
        p.require(isinstance(focal, list) and len(focal) == 2
                  and all(0 <= v <= 100 for v in focal), where,
                  "focal must be [x, y] percentages")

    p.raise_if_any()

    # Reverse edges. The brief calls the dataset a knowledge graph, and a
    # graph you can only traverse in one direction is a tree. Every city
    # needs to know which journeys pass through it, which themes name it and
    # which stories are set there, or those relationships exist only in the
    # curator's head.
    back = {cid: {"journeys": [], "themes": [], "stories": []} for cid in index}
    for j in journeys:
        for leg in j["legs"]:
            back[leg["city"]]["journeys"].append(j)
    for t in themes:
        for stop in t["stops"]:
            back[stop["city"]]["themes"].append(t)
    for st in stories:
        for cid in st.get("places", []):
            back[cid]["stories"].append(st)

    return {
        "images": images,
        "taxonomy": tax,
        "interests": interests,
        "countries": countries,
        "macros": tax["macros"],
        "journeys": journeys,
        "themes": themes,
        "stories": stories,
        "fund": fund,
        "providers": providers,
        "cities": index,
        "back": back,
        "categories": tax.get("categories", []),
    }


def city_index(countries):
    """Every city keyed by "<country>/<region>/<city>", with its ancestry attached."""
    out = {}
    for c in countries.values():
        for r in c["regions"]:
            for t in r["cities"]:
                cid = f"{c['slug']}/{r['slug']}/{t['slug']}"
                out[cid] = {
                    "id": cid,
                    "city": t,
                    "region": r,
                    "country": c,
                }
    return out


def all_places(countries):
    out = []
    for c in countries.values():
        for r in c["regions"]:
            for t in r["cities"]:
                for pl in t.get("places", []):
                    out.append({"place": pl, "city": t, "region": r, "country": c})
    return out


def all_experiences(countries):
    out = []
    for c in countries.values():
        for r in c["regions"]:
            for t in r["cities"]:
                for e in t.get("experiences", []):
                    out.append({"exp": e, "city": t, "region": r, "country": c})
    return out
