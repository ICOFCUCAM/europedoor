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
# The Build Package schema names 23 place_types. Ours had 24 and now has 29:
# palace, mosque, synagogue, lake and gallery were genuinely missing and are
# added.
#
# Two of the schema's types are deliberately NOT here. `restaurant` and
# `hotel` are businesses, and a business is not a place in this data model —
# it lives in data/providers.json behind the sponsorship wall, precisely so
# that nothing anybody can pay for can ever enter the editorial dataset. Let
# a hotel be a `place` and the wall has a door in it.
PLACE_KINDS = (
    "museum", "gallery", "castle", "palace", "church", "monastery", "mosque",
    "synagogue", "mountain", "waterfall", "lake", "beach", "monument",
    "archaeological-site", "park", "viewpoint", "bridge", "market", "garden",
    "island", "cave", "street", "square", "lighthouse", "quarter", "ruin",
    "theatre", "library", "bath",
)
PLACE_SEASONS = ("year-round", "summer", "winter", "spring-autumn", "weather-dependent")

# How an experience relates to a place — the §2.5 edge. Three types, because
# the distinction that matters is where you actually stand:
#
#   at      the experience happens there. Swim in Lake Annecy / lake-annecy.
#   from    it starts there and goes somewhere else. The Fløyen-to-Ulriken
#           ridge walk begins at Fløyen and ends five hours away.
#   about   it is about the place without being on it. "Stromboli, from the
#           water" is a boat looking at a volcano.
#
# A conventional travel site would collapse all three into "related", and
# then a reader would arrive at a trailhead expecting a summit.
RELATIONSHIPS = ("at", "from", "about")

# Difficulty, for the experiences that have one. Deliberately four plain words
# rather than a 1-5 scale: a number implies a measurement nobody took, and
# "grade 3" means nothing to the person deciding whether to bring a child.
DIFFICULTIES = ("easy", "moderate", "demanding", "serious")

# What shape a journey is. The Build Package calls this journey_type and its
# examples are all routes; ours separates the three that behave differently
# when a planner reasons about them.
JOURNEY_TYPES = ("route", "loop", "base")

# §2.10. Ours nine, theirs nine, five shared — the union, so the sections
# already written stay valid and the four the schema adds are available
# without a migration.
STORY_SECTIONS = (
    "History", "Culture", "People", "Food", "Travel",      # in both
    "Adventure", "Faith", "Nature", "Places",              # ours
    "Architecture", "Tradition", "Discovery", "Local guide",  # the schema's
)
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
# NO EXTERNAL LICENCE CLAIM ENTERS PRODUCTION FROM MEMORY. EVERY EXTERNALLY
# GOVERNED ASSET REQUIRES SOURCE + DATE + EVIDENCE.
#
# The map datasets have carried that since the map was built: `url`, `fetched`
# and `sha256` in docs/data-licenses/sources.json. Photographs carried five
# fields and none of them was a date or a hash — so a register row said "this
# is Pexels-licensed" and nothing recorded WHEN that was true or WHAT bytes
# it was true of. A licence is a claim about a moment; without the moment it
# is a claim about nothing.
#
# The field names are taken from the sister repository, which has 629
# photographs under exactly this discipline and proved the shape works.
# EVERY FIELD, BECAUSE A HALF-REGISTERED PHOTOGRAPH MUST NEVER LOOK VALID.
# The acquisition writes the row and the derivation completes it, so there is
# a moment when `processing` and `derivatives` are null — and if the validator
# tolerated that, a failed derive step would leave a row the build treats as a
# publishable photograph with no files behind it. It does not tolerate it: the
# incomplete state fails, loudly, which is what makes the two-step safe.
IMAGE_REQUIRED = ("purpose", "publication_path", "file", "original", "alt",
                  "provider", "provider_photo_id", "photographer",
                  "photographer_url", "source", "original_url", "licence",
                  "licence_url", "terms_read_on", "terms_evidence",
                  "fetched", "acquired_at", "sha256", "bytes", "version",
                  "width", "height", "processing", "derivatives")

# Licences we will actually publish under. A permissive list would make this
# field decorative; the point is that adding a new one is a decision somebody
# has to make on purpose.
IMAGE_LICENCES = ("CC0", "CC-BY-4.0", "CC-BY-SA-4.0", "Pexels", "Unsplash",
                  "commissioned", "licensed-stock", "owner-supplied")

SOURCE_KINDS = ("official", "operator", "municipal", "press", "editorial")

# The lifecycle field the Build Package schema asks for. Two values, because a
# third would be a workflow and there is no editor to run one.
STATUS = ("published", "draft")

# Fields that come from data/geo/facts.json and may never appear in an
# authored file. See the note in scripts/map/process.py.
DERIVED_COUNTRY = ("iso3", "lat", "lon", "latitude", "longitude", "population",
                   "population_year")
DERIVED_CITY = ("population", "population_year")

# What a EuropeDoor region IS. The Build Package schema offers state,
# province, department, canton, autonomous_region, territory and
# historical_region — all administrative units. Ours are none of those: they
# are travel regions drawn by editors, and Fjord Norway is not a canton. So
# the vocabulary carries the administrative values for the day the data model
# holds real administrative units, and `editorial` for what we actually have —
# which is also why the map draws a region as its destinations rather than as
# a boundary. Defaulting to `editorial` rather than leaving it blank is the
# point: an unstated type is a type a reader will assume.
REGION_TYPES = ("editorial", "state", "province", "department", "canton",
                "autonomous_region", "territory", "historical_region")

# city_type in the schema. Ours is wider than the schema's, because half of
# what this atlas calls a destination is not a settlement: Theth is a village,
# Lofoten is an archipelago, Madriu-Perafita-Claror is a valley and
# Mont-Saint-Michel is a site. Calling all 319 of them "city" was already
# slightly wrong before the schema asked.
CITY_TYPES = ("capital", "city", "town", "village", "island", "valley",
              "park", "site")

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

        # Derived facts are never authored. Same rule as `confidence`, and for
        # the same reason: a field a person can type is a field somebody will
        # type the wrong thing into, and a wrong population with no source
        # attached is indistinguishable from a right one. These come from
        # data/geo/facts.json, which names the dataset behind every value.
        for banned in DERIVED_COUNTRY:
            p.require(banned not in c, where,
                      f"{banned} is derived from Natural Earth, not authored — "
                      f"it is in data/geo/facts.json; remove it here")

        # status is the one lifecycle field, and it does something: a draft is
        # excluded from the build entirely rather than published with a badge
        # on it. Absent means published, so the 50 files that predate this
        # field did not have to change.
        p.require(c.get("status", "published") in STATUS, where,
                  f"status must be one of {'/'.join(STATUS)}")
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
        city_slugs = {t["slug"] for r in c.get("regions", []) for t in r.get("cities", [])}
        for f in c.get("festivals", []):
            p.require(f.get("month") in months, where, f"festival {f.get('name')!r}: bad month")
            p.require(f.get("kind") in EVENT_KINDS, where,
                      f"festival {f.get('name')!r}: kind must be one of {'/'.join(EVENT_KINDS)}")
            p.require(f.get("status", "published") in STATUS, where,
                      f"festival {f.get('name')!r}: bad status")
            # ── §2.9, the edge that makes an event part of the graph ─────
            #
            # An event used to carry `where` as prose — "Venice, Viareggio,
            # Ivrea" — which reads fine and joins to nothing. An optional
            # `city` slug attaches it to a destination we hold, so an event
            # can appear on the page of the place it happens in. The prose
            # stays, because three cities in one line is a true sentence the
            # graph cannot hold.
            if f.get("city"):
                p.require(f["city"] in city_slugs, where,
                          f"festival {f.get('name')!r}: city {f['city']!r} is not a "
                          f"destination in this country")
            # start_at / end_at are refused. We hold the MONTH, which is
            # verifiable and stable — Carnevale is in February and has been
            # for centuries. Exact dates move every year, need a source per
            # event per year, and are wrong silently. A month that is right
            # beats a date that is nearly right.
            for dated in ("start_at", "end_at", "starts", "ends", "date", "dates"):
                p.require(dated not in f, where,
                          f"festival {f.get('name')!r}: {dated!r} needs a source per "
                          f"event per year and goes wrong silently. We hold the month")
            for volatile in ("price_from", "price", "website", "tickets"):
                p.require(volatile not in f, where,
                          f"festival {f.get('name')!r}: {volatile!r} is volatile")
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
            p.require(r.get("type", "editorial") in REGION_TYPES, rw,
                      f"region type must be one of {'/'.join(REGION_TYPES)}")
            p.require(r.get("status", "published") in STATUS, rw,
                      f"status must be one of {'/'.join(STATUS)}")
            # A region has no authored coordinates. Its position is the middle
            # of its own destinations, computed at load, because that is the
            # only thing we actually hold — see the note on region geometry in
            # docs/map-architecture.md.
            for banned in ("lat", "lon", "latitude", "longitude", "geometry"):
                p.require(banned not in r, rw,
                          f"a region's {banned} is derived from its destinations, not authored")
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
                p.require(t.get("status", "published") in STATUS, tw,
                          f"status must be one of {'/'.join(STATUS)}")
                # city_type may be authored, because it is an editorial
                # judgement rather than a measurement: whether Lofoten is an
                # archipelago or a town is a decision, and Natural Earth's
                # answer for it is "not listed". Where it IS authored it wins
                # over the derived value, which is the point of allowing it.
                p.require(t.get("city_type", "city") in CITY_TYPES, tw,
                          f"city_type must be one of {'/'.join(CITY_TYPES)}")
                for banned in DERIVED_CITY:
                    p.require(banned not in t, tw,
                              f"{banned} is derived from Natural Earth, not authored — "
                              f"see data/geo/facts.json")
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
                    p.require(pl.get("status", "published") in STATUS, pw,
                              f"status must be one of {'/'.join(STATUS)}")
                    # The Build Package schema asks a place for `featured`.
                    # There is no such field and there will not be one: a
                    # sponsor pays a provider, and a provider affects
                    # directory surfaces only. A `featured` flag on an
                    # editorial place is the whole wall with a door in it, and
                    # the wall is the only version of that promise worth
                    # making. Same for rank/boost/sponsored.
                    for sold in ("featured", "rank", "boost", "sponsored", "promoted"):
                        p.require(sold not in pl, pw,
                                  f"{sold!r} would make an editorial place buyable — "
                                  f"sponsorship attaches to a provider and affects "
                                  f"directory surfaces only. See docs/legal-position.md")
                    # And for a rating. We hold none: no visitor numbers, no
                    # reviews, no survey. checks.py already refuses
                    # aggregateRating in JSON-LD for the same reason, and a
                    # number in the data that the structured data refuses to
                    # publish is a number waiting for somebody to publish it.
                    for unheld in ("rating", "review_count", "reviews", "stars"):
                        p.require(unheld not in pl, pw,
                                  f"{unheld!r} is a measurement we do not hold and cannot "
                                  f"source — a gap stated beats a gap filled")
                    for volatile in ("hours", "price", "website", "phone"):
                        p.require(volatile not in pl, pw,
                                  f"{volatile!r} is volatile and must not be authored "
                                  "unverified — see docs/data-model.md")

                place_slugs = {pl.get("slug") for pl in t.get("places", [])}
                seen_exp = set()
                for e in t.get("experiences", []):
                    ew = f"{tw} > {e.get('slug')}"
                    p.require(SLUG.match(e.get("slug", "")), ew, "experience slug is not a slug")
                    p.require(e["slug"] not in seen_exp, ew, "duplicate experience slug")
                    seen_exp.add(e.get("slug"))
                    p.require(e.get("kind") in kinds, ew, f"unknown experience kind {e.get('kind')!r}")
                    p.require(e.get("band") in BUDGETS, ew, "experience band must be low/moderate/high")
                    p.require(bool(e.get("summary")), ew, "an experience needs a summary")
                    p.require(e.get("status", "published") in STATUS, ew,
                              f"status must be one of {'/'.join(STATUS)}")
                    # Optional, and reported as content debt rather than
                    # demanded: 197 experiences is a lot of judgements to make
                    # in one sitting, and a required field gets filled in with
                    # whatever is quickest.
                    if "difficulty" in e:
                        p.require(e["difficulty"] in DIFFICULTIES, ew,
                                  f"difficulty must be one of {'/'.join(DIFFICULTIES)}")
                    if "season" in e:
                        p.require(e["season"] in PLACE_SEASONS, ew,
                                  f"season must be one of {'/'.join(PLACE_SEASONS)}")

                    # ── the place ↔ experience edge, §2.5 ────────────────
                    #
                    # An experience is not a place. The Louvre is a place;
                    # "Renaissance rooms before the coaches arrive" is an
                    # experience that happens in it. Before this, the two sat
                    # side by side under a destination with nothing joining
                    # them, so a place page could not say what there is to do
                    # there and an experience page could not say where.
                    #
                    # The edge is authored, not inferred. A substring match
                    # between an experience name and a place name gets
                    # "Waterfront architecture walk" to the Munch Museum,
                    # which is a plausible-looking lie.
                    for link in e.get("at", []):
                        p.require(isinstance(link, dict), ew, "each `at` entry is an object")
                        if not isinstance(link, dict):
                            continue
                        p.require(link.get("place") in place_slugs, ew,
                                  f"`at` names {link.get('place')!r}, which is not a place in "
                                  f"this destination — an edge may not cross destinations")
                        p.require(link.get("how") in RELATIONSHIPS, ew,
                                  f"`at.how` must be one of {'/'.join(RELATIONSHIPS)}")
                    for sold in ("featured", "rank", "boost", "sponsored", "promoted"):
                        p.require(sold not in e, ew,
                                  f"{sold!r} would make an editorial experience buyable")
                    for unheld in ("rating", "review_count", "reviews", "stars", "price_from"):
                        p.require(unheld not in e, ew,
                                  f"{unheld!r} is a measurement we do not hold. The price band "
                                  f"is `band`, which is honest about being a band")
                    for volatile in ("hours", "price", "website", "phone", "booking_url"):
                        p.require(volatile not in e, ew,
                                  f"{volatile!r} is volatile and must not be authored")
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
        p.require(j.get("type", "route") in JOURNEY_TYPES, jw,
                  f"journey type must be one of {'/'.join(JOURNEY_TYPES)}")
        p.require(j.get("status", "published") in STATUS, jw,
                  f"status must be one of {'/'.join(STATUS)}")
        for sold in ("featured", "rank", "boost", "sponsored", "promoted"):
            p.require(sold not in j, jw,
                      f"{sold!r} would make a journey buyable. Sponsorship attaches to a "
                      f"provider and affects directory surfaces only")
        for unheld in ("rating", "review_count", "price_from", "price"):
            p.require(unheld not in j, jw,
                      f"{unheld!r} is not a thing we hold. The cost of a journey is "
                      f"computed from the daily bands and shown as an estimate")
        # ── §2.7 journey stops ──────────────────────────────────────────
        #
        # `sequence` and `day_number` are derived at load: an array already
        # has an order, and a day number is the sum of the nights before it.
        # Authoring either is a second source of truth that goes wrong the
        # first time somebody inserts a leg.
        #
        # `arrival_time` and `departure_time` are refused. Those are
        # timetable facts with a booking system behind them; we hold no
        # timetables, we own no inventory, and a departure time that is
        # wrong is the single most damaging thing a travel page can print.
        for leg in j.get("legs", []):
            p.require(leg.get("city") in index, jw, f"leg points at unknown city {leg.get('city')!r}")
            p.require(isinstance(leg.get("nights"), int) and leg["nights"] >= 1, jw, "leg needs nights")
            p.require(bool(leg.get("why")), jw, f"leg {leg.get('city')} needs a why")
            for banned in ("sequence", "day_number", "day"):
                p.require(banned not in leg, jw,
                          f"a leg's {banned!r} is derived from the order and the nights, "
                          f"not authored")
            for timetable in ("arrival_time", "departure_time", "arrives", "departs"):
                p.require(timetable not in leg, jw,
                          f"{timetable!r} is a timetable fact. We hold no timetables and "
                          f"a wrong departure time is the most damaging thing this site "
                          f"could print")
            # The optional edge from a stop into the graph: which recorded
            # places this leg is actually for. Validated against that city's
            # own places, so a stop cannot point somewhere it does not go.
            if leg.get("city") in index:
                here = {pl["slug"] for pl in index[leg["city"]]["city"].get("places", [])}
                for slug in leg.get("places", []):
                    p.require(slug in here, jw,
                              f"leg {leg['city']} lists place {slug!r}, which is not "
                              f"recorded in that destination")
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
        # §2.10 story_type. The nine sections already in use were a
        # convention rather than a vocabulary — nothing stopped the tenth
        # story inventing "Adventure & Nature" and quietly starting a second
        # index. This is the union of what we use and what the Build Package
        # names, so both stay valid and neither drifts.
        p.require(st.get("section") in STORY_SECTIONS, sw,
                  f"section must be one of {'/'.join(STORY_SECTIONS)}")
        p.require(st.get("status", "published") in STATUS, sw,
                  f"status must be one of {'/'.join(STATUS)}")
        for sold in ("featured", "sponsored", "promoted", "rank"):
            p.require(sold not in st, sw, f"{sold!r} would make a story buyable")

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

    # Europe in Motion. Each entry is a query, and it is validated as one:
    # a motion with no query terms would match the whole Atlas, and a motion
    # with a hand-picked list of destinations would be a curated list wearing
    # the clothes of a query. Neither is allowed.
    motions = _read(os.path.join(DATA, "motions.json")).get("motions", [])
    seen_motions = set()
    for m in motions:
        where = f"motions.json > {m.get('slug')}"
        for key in ("slug", "name", "strapline", "lede"):
            p.require(bool(m.get(key)), where, f"missing {key!r}")
        p.require(SLUG.match(m.get("slug", "")), where, "slug is not a slug")
        p.require(m["slug"] not in seen_motions, where, "duplicate motion slug")
        seen_motions.add(m.get("slug"))
        for i in m.get("interests", []):
            p.require(i in interests, where, f"unknown interest {i!r}")
        for mo in m.get("months", []):
            p.require(mo in months, where, f"unknown month {mo!r}")
        p.require(any(k in m for k in ("interests", "months", "min_lat"))
                  or m.get("min_disc", 0) > 0, where,
                  "a motion with no query terms would match the whole Atlas")
        p.require("cities" not in m and "destinations" not in m, where,
                  "a motion is a query, not a hand-picked list — there is no "
                  "field for naming destinations, deliberately")

    # The photograph register.
    #
    # This block MUST stay above p.raise_if_any(). The first version sat
    # below it, next to the return, and every complaint it collected was
    # discarded unread — a row with no licence at all passed `build.py
    # check` cleanly. A validator that runs after the raise is not a
    # validator, it is a list nobody opens.
    # A PURPOSE IS EITHER DECLARED OR IS AN INSTANCE OF A SLOT, and the
    # validator has to know both — `destination-hero@france/…/chamonix`
    # resolves through the template, so 319 destination pages have a purpose
    # without 319 rows being typed into the spec file.
    from . import imageslots
    PURPOSES = _read(os.path.join(DATA, "image-purposes.json")).get("purposes", {})
    images = _read(os.path.join(DATA, "images.json")).get("images", {})
    seen_purpose = {}
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
        # SOURCE + DATE + EVIDENCE, the same contract the map datasets have.
        p.require(str(row.get("licence_url", "")).startswith("https://"), where,
                  "licence_url must be the page that STATES the licence — the "
                  "licence name alone is a claim with nowhere to check it")
        p.require(re.match(r"^\d{4}-\d{2}-\d{2}$", str(row.get("fetched", ""))),
                  where,
                  "fetched must be the YYYY-MM-DD the file was taken. A "
                  "licence is a claim about a moment and without the moment "
                  "it is a claim about nothing")
        # PURPOSE, AND ONE PHOTOGRAPH PER SURFACE. A picture acquired for the
        # homepage hero must not drift onto a destination page because it
        # exists; the surfaces have different jobs, different aspect ratios
        # and different type over them.
        # TWO ROWS CANNOT CLAIM ONE PURPOSE. Not a theoretical worry: the
        # register is keyed by surface and the purpose names the surface, so
        # a duplicate means two photographs believe they are the homepage.
        if row.get("purpose"):
            p.require(row["purpose"] not in seen_purpose, where,
                      f"purpose {row['purpose']!r} is already claimed by "
                      f"{seen_purpose.get(row['purpose'])!r}")
            seen_purpose[row["purpose"]] = key
        spec = imageslots.resolve(row.get("purpose") or "",
                                  {"cities": index, "stories": stories}) \
            if row.get("purpose") else None
        p.require(spec is not None, where,
                  f"purpose must be declared in data/image-purposes.json, or "
                  f"be an instance of a slot written slot@target "
                  f"({'/'.join(sorted(PURPOSES)) or 'none declared'}; slots "
                  f"{'/'.join(sorted(imageslots.slots())) or 'none'})")
        if spec is not None:
            p.require(key == spec["key"], where,
                      f"purpose {row['purpose']!r} fills {spec['key']!r} and "
                      f"this row is keyed {key!r} — a purpose names one "
                      f"surface")
            p.require(row.get("publication_path") == spec["path"], where,
                      "publication_path must be the page the purpose declares")
            p.require(int(row.get("width") or 0) >= spec["min_width"], where,
                      f"native width {row.get('width')!r} is under the "
                      f"{spec['min_width']}px this purpose needs")
        p.require(str(row.get("provider_photo_id") or "").strip(), where,
                  "provider_photo_id — the provider's own id for this exact "
                  "photograph. Without it nobody can re-fetch what we took, "
                  "and a register that cannot be re-checked is a claim")
        p.require(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
                           str(row.get("acquired_at", ""))), where,
                  "acquired_at must be a UTC timestamp, not a date. Two "
                  "acquisitions on one day are two events")
        p.require(re.match(r"^\d{4}-\d{2}-\d{2}$",
                           str(row.get("terms_read_on", ""))), where,
                  "terms_read_on — WHICH reading of the provider's terms this "
                  "photograph was taken under. A licence is a claim about a "
                  "moment")
        p.require(isinstance(row.get("terms_evidence"), list)
                  and row["terms_evidence"], where,
                  "terms_evidence must name the archived pages under "
                  "docs/data-licenses/provider-terms/ that were in force")
        proc = row.get("processing")
        p.require(isinstance(proc, dict) and proc.get("tool")
                  and proc.get("quality") and proc.get("widths"), where,
                  "processing must record the encoder, the quality values and "
                  "the widths — a derivative nobody can reproduce is not "
                  "evidence of anything")
        derived = row.get("derivatives")
        p.require(isinstance(derived, dict) and derived, where,
                  "derivatives must record every file made, with its hash and "
                  "its real pixel size. A row acquire.py wrote and derive.py "
                  "never completed is INCOMPLETE and must fail here rather "
                  "than ship as a photograph with no files")
        if isinstance(derived, dict):
            for dname, d in sorted(derived.items()):
                p.require(re.match(r"^[0-9a-f]{64}$", str(d.get("sha256", ""))),
                          where, f"derivative {dname} has no sha256")
                p.require(int(d.get("width") or 0) > 0, where,
                          f"derivative {dname} records no width")
        p.require(re.match(r"^[0-9a-f]{64}$", str(row.get("sha256", ""))), where,
                  "sha256 of the bytes as served — the evidence that the file "
                  "in this repository is the file that was licensed")
        # Alt text is a caption for someone who cannot see the photograph,
        # not a keyword field. "Bergen" is the page title, not a description.
        p.require(len(str(row.get("alt", ""))) >= 12, where,
                  "alt must describe the photograph, not repeat the place name")
        focal = row.get("focal", [50, 50])
        p.require(isinstance(focal, list) and len(focal) == 2
                  and all(0 <= v <= 100 for v in focal), where,
                  "focal must be [x, y] percentages")

    # THE STAY REGISTRY. A provider is a link mechanism and a credential, and
    # the validator's whole job is to keep it from becoming anything else.
    #
    # The refusal list is the same wall the editorial records carry, applied
    # to the one file whose commercial purpose makes it the likeliest place
    # for somebody to add a price "just for the exemplar". EuropeDoor holds no
    # rooms, no prices, no availability and no ratings; a field for one of
    # them here would be the first unverified thing on this site, and the
    # provider is the one who has them and the one who is named as having
    # them.
    # THE HOMEPAGE'S EDITORIAL LAYER. Four doors and a closing statement, in
    # data rather than in the template, because the homepage is an entrance
    # somebody will want to rewrite without touching page code. Every door
    # names a REAL interest, so the word on the door is the heading of the
    # page it opens and the count beside it is the length of that list — the
    # rule that stopped a tile being labelled "Adventure" when no such tag,
    # no page and no list exists behind the word.
    home = _read(os.path.join(DATA, "home.json"))
    p.require(isinstance(home.get("doors"), list) and home["doors"],
              "home.json", "no doors")
    p.require(len(home["doors"]) <= 4, "home.json",
              f"{len(home['doors'])} doors — the homepage shows at most four. "
              "Eight was the finding: a reader stopped seeing destinations and "
              "started seeing UI components.")
    seen = set()
    for d in home["doors"]:
        w = f"home.json door {d.get('interest')!r}"
        for key in ("interest", "title", "line", "where", "purpose"):
            p.require(key in d and d[key], w, f"missing {key!r}")
        p.require(d.get("interest") in interests, w,
                  f"unknown interest {d.get('interest')!r} — a door must open "
                  f"on a list this atlas actually holds")
        p.require(d.get("interest") not in seen, w, "duplicate door")
        seen.add(d.get("interest"))
    for key in ("head", "body", "cta"):
        p.require((home.get("closing") or {}).get(key), "home.json",
                  f"closing statement is missing {key!r}")

    stay = _read(os.path.join(DATA, "stay.json")) if os.path.exists(
        os.path.join(DATA, "stay.json")) else {"providers": [],
                                               "accommodation_context": []}
    # THE REFUSAL IS ON THE KEYS, AND THE FIRST VERSION READ THE PROSE. It
    # matched the whole file, so the sentence in `$comment` saying this atlas
    # holds "no rooms, no prices, no availability and no ratings" tripped four
    # of its own refusals. That is the font-size-in-a-comment failure this
    # repository already records once: an instrument that reads its own
    # documentation as data. A price can only be PUBLISHED if there is a key
    # for it, so the keys are the honest test — and it is the stronger claim,
    # because it also catches a key nested inside `fixed_params`.
    def _keys(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield str(k).lower()
                yield from _keys(v)
        elif isinstance(node, list):
            for v in node:
                yield from _keys(v)

    stay_keys = set(_keys(stay))
    for unheld in ("price", "rating", "review", "reviews", "review_count",
                   "availability", "rooms", "stars", "amenities", "discount",
                   "commission", "featured", "rank", "boost", "sponsored"):
        p.require(unheld not in stay_keys, "stay.json",
                  f"carries a {unheld!r} field: this atlas holds no "
                  f"accommodation inventory, and the provider is named on the "
                  f"page as the one who does")
    seen_prov = set()
    for prov in stay.get("providers", []):
        where = f"stay.json > {prov.get('slug')}"
        for field in ("slug", "name", "host", "search_url", "place_param",
                      "partner_param", "programme", "programme_url",
                      "mechanism", "inventory_api", "gate"):
            p.require(bool(prov.get(field)), where, f"missing {field!r}")
        p.require(SLUG.match(prov.get("slug", "")), where, "slug is not a slug")
        p.require(prov.get("slug") not in seen_prov, where, "duplicate provider")
        seen_prov.add(prov.get("slug"))
        p.require(str(prov.get("search_url", "")).startswith("https://"), where,
                  "search_url must be https")
        p.require(prov.get("host", "") in str(prov.get("search_url", "")), where,
                  "host must be the host of search_url — the check that pins "
                  "which third-party origins this site reaches reads `host`")
        p.require("enabled" in prov, where,
                  "enabled must be stated either way: a provider whose state "
                  "is implied is a provider somebody turns on by accident")
        pid = prov.get("partner_id")
        p.require(pid is None or (isinstance(pid, str) and pid.strip()), where,
                  "partner_id is either null or a real credential; an empty "
                  "string would read as tracked and track nothing")
        # EVERY PROVIDER STATES WHETHER IT CAN SUPPLY INVENTORY, IN WORDS.
        # The brief's own warning: do not pretend a provider is an API-backed
        # inventory source. Expedia's creator programme has no general API
        # and Booking.com's Demand API is for managed partners only, and a
        # design that assumes otherwise builds a card with nothing to fill
        # it. `inventory_api` is required so that the answer is written down
        # per provider rather than assumed once for all of them.
        p.require(len(str(prov.get("inventory_api", ""))) >= 40, where,
                  "`inventory_api` must say what inventory this provider can "
                  "and cannot supply, and under what terms — 'NONE' is a "
                  "perfectly good answer and an absent one is not")
        p.require(str(prov.get("programme_url", "")).startswith("https://"), where,
                  "programme_url must be the https page whose terms this row "
                  "is claiming to sit under")
    seen_stay = set()
    for row in stay.get("accommodation_context", []):
        where = f"stay.json > {row.get('city')}"
        p.require(row.get("city") in index, where,
                  "unknown destination — the Stay layer cannot cover a place "
                  "this atlas does not hold")
        p.require(row.get("city") not in seen_stay, where, "covered twice")
        seen_stay.add(row.get("city"))
        for field in ("promise", "base", "where", "lead", "when"):
            p.require(bool(row.get(field)), where, f"missing {field!r}")
        # The heading may be authored and may never be OTA language. A
        # section called "Hotels in Chamonix" is the one thing this whole
        # layer exists not to be.
        p.require("hotel" not in str(row.get("heading", "")).lower(), where,
                  "a Stay heading may not say 'hotel' — that is the generic "
                  "listing language, and this atlas is offering a base")
        # An authored classification is the job; an authored measurement is
        # not. `where` may say "the valley floor" and may not say "1,035 m".
        p.require(len(str(row.get("where", ""))) >= 80, where,
                  "`where` is the editorial judgement this section exists to "
                  "carry — a line shorter than that is a label")

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

    # ── derived facts ────────────────────────────────────────────────
    #
    # iso3, a country's label point, and population come from Natural Earth
    # via scripts/map/process.py. They are merged here rather than authored,
    # and every one arrives with the dataset that produced it attached, so a
    # page can say where a number came from without anybody remembering to.
    #
    # A region's position is computed from its own destinations, because that
    # is the only thing we hold: we have region membership and no region
    # geometry. The map has drawn regions that way since it was rebuilt; this
    # puts the same number in the data model so the API and the map cannot
    # disagree about where Vestland is.
    facts = _read(os.path.join(DATA, "geo", "facts.json")) if os.path.exists(
        os.path.join(DATA, "geo", "facts.json")) else {"countries": {}, "destinations": {}}
    for c in countries.values():
        f = facts["countries"].get(c["code"].lower(), {})
        c["derived"] = {k: v for k, v in f.items() if k != "source"}
        c["derived_source"] = f.get("source")
        c.setdefault("status", "published")
        for r in c["regions"]:
            r.setdefault("type", "editorial")
            r.setdefault("status", "published")
            pts = [(t["lat"], t["lon"]) for t in r["cities"]]
            r["derived"] = {
                "lat": round(sum(a for a, _b in pts) / len(pts), 4),
                "lon": round(sum(b for _a, b in pts) / len(pts), 4),
                "destinations": len(pts),
            }
            r["derived_source"] = "the middle of this region's own destinations"
            for t in r["cities"]:
                t.setdefault("status", "published")
                d = facts["destinations"].get(f'{c["slug"]}/{r["slug"]}/{t["slug"]}', {})
                t["derived"] = {k: v for k, v in d.items() if k != "source"}
                t["derived_source"] = d.get("source")
                # §2.11 transport nodes. The routes half is refused; see the
                # note in scripts/map/process.py.
                tr = facts.get("transport", {}).get(
                    f'{c["slug"]}/{r["slug"]}/{t["slug"]}', {})
                t["transport"] = tr.get("nodes", [])
                t["transport_source"] = tr.get("source")
                # An authored city_type wins over the derived one. Natural
                # Earth is right about Bergen and has never heard of Theth.
                if "city_type" not in t and d.get("city_type"):
                    t["city_type"] = d["city_type"]
                    t["city_type_source"] = d["source"]
                elif "city_type" in t:
                    t["city_type_source"] = "editorial"

    # ── §2.7, derived ────────────────────────────────────────────────
    #
    # sequence and day_number, computed rather than authored: an array
    # already has an order, and a day number is one plus the nights before
    # it. Authoring either is a second source of truth that goes wrong the
    # first time somebody inserts a leg in the middle, and goes wrong
    # silently, because both numbers still look like numbers.
    for j in journeys:
        j.setdefault("type", "route")
        j.setdefault("status", "published")
        day = 1
        for i, leg in enumerate(j["legs"]):
            leg["sequence"] = i + 1
            leg["day_number"] = day
            leg["day_last"] = day + leg["nights"] - 1
            day += leg["nights"]

    # A draft is excluded, not published with a badge on it. This is the one
    # thing `status` does, and it has to do something: a lifecycle column that
    # changes nothing is a column that will be set wrongly and never noticed.
    for slug in [s for s, c in countries.items() if c["status"] == "draft"]:
        del countries[slug]
    for c in countries.values():
        c["regions"] = [r for r in c["regions"] if r["status"] != "draft"]
        for r in c["regions"]:
            r["cities"] = [t for t in r["cities"] if t["status"] != "draft"]

    return {
        "motions": motions,
        "home": home,
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
        "stay": stay,
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
