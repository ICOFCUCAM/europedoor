"""One place that knows what a URL looks like.

Every href on the site comes from here, which is what made the move from
`/atlas/<macro>/<country>/…` to `/europe/<country>/…` a one-file change
rather than a week.

The shape now follows the product specification:

    /discover                     the entry point: map, filters, regions
    /discover/<macro>             a region of Europe
    /countries                    the index
    /europe/<country>
    /europe/<country>/<region>
    /europe/<country>/<region>/<destination>
    /europe/<country>/<region>/<destination>/<facet>     things-to-do, food…
    /europe/<country>/<region>/<destination>/place/<place>

The macro region left the path deliberately. "Nordic" is a way of grouping
Norway, not part of Norway's address, and putting it in the URL made every
city four segments deep for no navigational gain.
"""

EUROPE = "/europe"

# Facet pages hang off a destination. Each one needs enough material to
# justify a page of its own — see pages.facets_for().
FACETS = {
    "things-to-do": "Things to do",
    "food": "Food & drink",
    "history": "History",
    "journeys": "Journeys through here",
}


def discover():
    return "/discover"


def macro(m):
    return f"/discover/{m['slug']}"


def countries_index():
    return "/countries"


def country(c):
    return f"{EUROPE}/{c['slug']}"


def country_by_slug(slug):
    """The country URL when all you hold is the slug.

    The map draws shapes from data/geo/, which carries a slug and no country
    record, so it cannot call country(c). Deliberately built from the same
    EUROPE prefix rather than a second f-string, because two places that
    format the same URL is how a redirect gets written six months later.
    """
    return f"{EUROPE}/{slug}"


def region(c, r):
    return f"{country(c)}/{r['slug']}"


def city(c, r, t):
    return f"{region(c, r)}/{t['slug']}"


def facet(c, r, t, key):
    return f"{city(c, r, t)}/{key}"


def place(c, r, t, pl):
    return f"{city(c, r, t)}/place/{pl['slug']}"


def city_by_id(index, cid):
    n = index[cid]
    return city(n["country"], n["region"], n["city"])


def interest(slug):
    return f"/interests/{slug}"


def category(slug):
    return f"/experiences/{slug}"


def subcategory(cat, sub):
    return f"/experiences/{cat}/{sub}"


def journey(j):
    return f"/journeys/{j['slug']}"


def theme(t):
    return f"/themes/{t['slug']}"


def story(s):
    return f"/stories/{s['slug']}"


def fund_project(p):
    return f"/fund/{p['slug']}"


def experience_kind(k):
    return f"/experiences/kind/{k}"


def month(m):
    return f"/events/{m}"
