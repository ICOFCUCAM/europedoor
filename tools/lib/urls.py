"""One place that knows what a URL looks like.

Every href on the site comes from here. When the shape of the Atlas changes
— and it will, because "Europe > Northern Europe > Norway > Vestland >
Bergen" is a strong claim about how people look for places — it changes in
this file and nowhere else.
"""


def macro(m):
    return f"/atlas/{m['slug']}"


def country(c):
    return f"/atlas/{c['macro_slug']}/{c['slug']}"


def region(c, r):
    return f"{country(c)}/{r['slug']}"


def city(c, r, t):
    return f"{region(c, r)}/{t['slug']}"


def city_by_id(index, cid):
    n = index[cid]
    return city(n["country"], n["region"], n["city"])


def interest(slug):
    return f"/interests/{slug}"


def journey(j):
    return f"/journeys/{j['slug']}"


def fund_project(p):
    return f"/fund/{p['slug']}"


def experience_kind(k):
    return f"/experiences/{k}"
