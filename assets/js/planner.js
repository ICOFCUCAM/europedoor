/* The Journey Planner.
 *
 * Everything happens in this file, in the visitor's browser, against the
 * same JSON the site is generated from. Nothing is posted anywhere: a
 * planner that phones home before it has an account system is collecting
 * travel intentions it has no basis to hold.
 *
 * The shape of the algorithm, because it is the product and not an
 * implementation detail:
 *
 *   score(city)   how well the place answers what you said you want
 *   season(city)  the month you chose, moving the score up or down
 *   hop(a, b)     the distance penalty that stops the route wandering
 *   nights(city)  from the range published on the city's own page
 *   cost(route)   nights x the country's daily band + transport by distance
 *
 * A place is never chosen for money. There is no paid placement here and
 * there is no field in the data that could carry one.
 */

(function () {
  "use strict";

  var ATLAS = null;
  // Set by the sentence box, cleared by any manual rebuild — the form has no
  // field for "only in the Alps", so it must not silently persist.
  var currentGeo = [];
  var form = document.getElementById("planner");
  var result = document.getElementById("result");
  var startSel = document.getElementById("start");
  var shuffleSeed = 1;

  var SEASON = { peak: 1.18, shoulder: 1.0, off: 0.74 };
  var PACE = { slow: 1, balanced: 0, fast: -1 };
  var STYLE_DAILY = { low: 0.0, moderate: 0.5, high: 1.0 };

  function rand() {
    // Deterministic per press of "give me a different one", so a result can
    // be reproduced by pressing it the same number of times.
    shuffleSeed = (shuffleSeed * 1103515245 + 12345) & 0x7fffffff;
    return shuffleSeed / 0x7fffffff;
  }

  function km(a, b) {
    var R = 6371, p1 = a.lat * Math.PI / 180, p2 = b.lat * Math.PI / 180;
    var dp = p2 - p1, dl = (b.lon - a.lon) * Math.PI / 180;
    var h = Math.sin(dp / 2) * Math.sin(dp / 2) +
            Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return Math.round(2 * R * Math.asin(Math.sqrt(h)));
  }

  // Door-to-door, not vehicle speed: a train averages far less than its top
  // speed once you include getting to the station, and a flight is three
  // hours of airport wrapped around forty minutes of aeroplane.
  function travelHours(d, mode) {
    if (mode === "fly") return Math.round((3 + d / 750) * 10) / 10;
    if (d < 90) return Math.round((d / 55 + 0.4) * 10) / 10;
    return Math.round((d / 85 + 0.8) * 10) / 10;
  }

  function hoursText(h) {
    if (h < 1) return Math.round(h * 60) + " minutes";
    var whole = Math.floor(h), mins = Math.round((h - whole) * 60);
    return whole + "h" + (mins ? " " + mins + "m" : "");
  }

  /* A DISTANCE THAT CANNOT BE TRAVELLED, AND A TIME NOBODY CAN BOUND.
   *
   * This printed "69 km, about 1h39m — a local train or a short drive" for
   * Chamonix to Zermatt. The two towns are 69 km apart as the crow flies,
   * about 170 km on the ground, and the journey is a change at Martigny and
   * Visp: most of a day, round a mountain range. The arithmetic was not
   * wrong; it was being asked a question a great-circle distance cannot
   * answer, and the answer was printed as a fact a reader would plan around.
   *
   * The first correction said "at least", which was worse. travelHours()
   * knows one average speed and nothing about whether a high-speed line
   * exists, so its error is not signed. Measured against six real legs it
   * undershoots the short mountain hops and overshoots every fast corridor:
   * Paris to Marseille is 660 km here, the model says 8h36m, the TGV does it
   * in about four and a half door to door. A floor that is two hours over on
   * four legs in six is not a floor, it is a guess wearing the word.
   *
   * So: the distance says it is a straight line, the time says "about", the
   * mode claim is gone, and the sentence explaining what the estimate is
   * worth — including that it is wrong in BOTH directions — is hoisted once
   * above the itinerary rather than implied on every leg. Restoring "a short
   * drive" is the one change here that would make the planner assert
   * something a traveller could act on and be wrong about. */
  function hopNote(d, opts) {
    var railOnly = opts && opts.transport === "rail";
    var ground = "about " + hoursText(travelHours(d, "ground"));
    if (d < 400) return d + " km in a straight line — " + ground + " on the ground";
    if (d < 900) return d + " km in a straight line — " + ground + " by rail" +
      (railOnly ? ", and the point of doing it this way"
                : ", or about " + hoursText(travelHours(d, "fly")) + " door to door by air");
    return railOnly
      ? d + " km in a straight line — more than a day overland. Kept because you " +
        "asked for no flights; consider a night train or an extra night either side."
      : d + " km in a straight line — about " + hoursText(travelHours(d, "fly")) +
        " door to door by air, or give the overland crossing a day of its own";
  }

  function transportCost(d) {
    if (d < 90) return Math.max(8, Math.round(d * 0.14));
    if (d < 400) return Math.max(18, Math.round(d * 0.11));
    if (d < 900) return Math.max(45, Math.round(d * 0.10));
    return Math.max(95, Math.round(d * 0.09));
  }

  function seasonFactor(city, month) {
    if (city.peak.indexOf(month) >= 0) return SEASON.peak;
    if (city.shoulder.indexOf(month) >= 0) return SEASON.shoulder;
    return SEASON.off;
  }

  // Guesthouses come in under the band, hotels above it. The multiplier is
  // applied to beds only, because the food half of the band does not care
  // where you slept.
  var STAY_FACTOR = { guesthouse: 0.82, mixed: 1, hotel: 1.18 };

  function dailyRate(city, style) {
    var lo = city.daily[0], hi = city.daily[1];
    return Math.round(lo + (hi - lo) * STYLE_DAILY[style]);
  }

  function impliedDaily(opts) {
    // Beds and meals are about 60% of a trip once transport, activities and
    // the buffer come out — the split was 78% before activities were costed
    // separately, and leaving it there let unaffordable places through. This
    // is a ceiling, not a target: coming in under budget is never penalised.
    return (opts.budget * 0.60) / Math.max(1, opts.days);
  }

  /* The specification proposes a weighted recommendation score:
   *
   *   30% user relevance · 20% experience match · 15% season suitability
   *   10% accessibility  · 10% popularity       · 10% content quality
   *   5%  diversity/novelty
   *
   * Six of those seven can be computed honestly. Popularity cannot: there is
   * no traffic on this site yet and no licensed visitor-numbers dataset, so a
   * popularity term would be a number we made up wearing a percentage sign.
   * Its 10% moves to content quality, which is measurable exactly, and the
   * reallocation is stated on /plan rather than buried in here.
   *
   * "Accessibility" is read as reachability — how connected a place is to the
   * rest of the Atlas — and NOT as disabled access, which we hold no data on
   * and say so on the page.
   */
  var W = {
    relevance: 0.30,   // how many of your interests the place carries
    experience: 0.20,  // things to actually do there
    season: 0.15,      // the month you named
    reach: 0.10,       // how connected it is
    quality: 0.20,     // how much of it we have written (10% + popularity's 10%)
    novelty: 0.05      // quiet places, and countries not yet in the route
  };

  var REACH = null;
  function reachOf(city) {
    if (!REACH) {
      REACH = {};
      var cs = ATLAS.cities;
      for (var a = 0; a < cs.length; a++) {
        var n = 0;
        for (var b = 0; b < cs.length; b++) if (a !== b && km(cs[a], cs[b]) < 300) n++;
        REACH[cs[a].id] = n;
      }
    }
    // Twelve neighbours inside 300 km is about as connected as Europe gets.
    return Math.min(1, (REACH[city.id] || 0) / 12);
  }

  function fitScore(city, wants, month, style, ceiling, context) {
    var matched = 0, i;
    for (i = 0; i < wants.length; i++) {
      if (city.interests.indexOf(wants[i]) >= 0) matched++;
    }
    var interest = wants.length ? matched / wants.length : 0.5;
    var todo = city.todo || [];
    var expMatch = Math.min(1, todo.length / 4) * (wants.length ? (matched > 0 ? 1 : 0.35) : 1);
    var season = city.peak.indexOf(month) >= 0 ? 1
               : city.shoulder.indexOf(month) >= 0 ? 0.75 : 0.35;
    var quality = Math.min(1, (city.depth || 0) / 8) * (city.checked ? 1 : 0.92);
    var novelty = (city.quiet ? 0.6 : 0) +
                  (context && context.perCountry && context.perCountry[city.countrySlug] ? 0 : 0.4);
    var base = W.relevance * interest + W.experience * expMatch + W.season * season
             + W.reach * reachOf(city) + W.quality * quality + W.novelty * novelty;
    // A generous budget stops caring what a place costs; a frugal one does.
    var costPenalty = 1;
    if (style === "low" && city.budget === "high") costPenalty = 0.72;
    if (style === "low" && city.budget === "moderate") costPenalty = 0.92;
    if (style === "high" && city.budget === "low") costPenalty = 0.96;
    // Somewhere with listed experiences has more to actually do.
    var depth = 1;
    // Affordability. Somewhere you cannot afford is not a recommendation,
    // so a city whose daily rate is above the ceiling is damped in
    // proportion to how far above. Being cheaper than the ceiling is free.
    var afford = 1;
    if (ceiling > 0) {
      var rate = dailyRate(city, style);
      // Steeper than it looks: at three times the ceiling a place is down to
      // about a tenth of its score, which is what "cannot afford it" should
      // mean. The old 0.25 floor let Switzerland survive a €700 fortnight.
      if (rate > ceiling) afford = Math.max(0.06, Math.pow(ceiling / rate, 1.9));
    }
    return base * costPenalty * depth * afford;
  }

  function nightsFor(city, pace, remaining) {
    var lo = city.nights[0], hi = city.nights[1];
    var mid = Math.round((lo + hi) / 2) + PACE[pace];
    var n = Math.max(lo, Math.min(hi, mid));
    n = Math.max(1, n);
    return Math.min(n, remaining);
  }

  function savedIds() {
    try {
      var raw = localStorage.getItem("europedoor.saved.v1");
      if (!raw) return {};
      var out = {};
      JSON.parse(raw).forEach(function (x) {
        var m = /^(city|place):([^/]+\/[^/]+\/[^/]+)/.exec(x.id || "");
        if (m) out[m[2]] = true;
      });
      return out;
    } catch (e) { return {}; }
  }

  function plan(opts) {
    var cities = ATLAS.cities.slice();
    var favour = opts.useSaved ? savedIds() : {};
    var endCity = null;
    if (opts.end) {
      for (var q0 = 0; q0 < ATLAS.cities.length; q0++) {
        if (ATLAS.cities[q0].id === opts.end) { endCity = ATLAS.cities[q0]; break; }
      }
    }
    if (opts.geo && opts.geo.length) {
      var only = cities.filter(function (c) { return opts.geo.indexOf(c.countrySlug) >= 0; });
      // Honour it only if there is enough there to plan with. Three cities
      // is not a fortnight, and silently returning a two-stop trip would
      // look like a bug rather than a constraint.
      if (only.length >= 4) cities = only;
      else opts.geoTooNarrow = true;
    }
    var ceiling = impliedDaily(opts);
    var context = { perCountry: {} };
    var scored = cities.map(function (c) {
      var base = fitScore(c, opts.wants, opts.month, opts.style, ceiling, context);
      // A place you saved is a stronger signal than any tag we assigned it.
      return { c: c, s: favour[c.id] ? base * 1.6 : base };
    });
    scored.sort(function (a, b) { return b.s - a.s; });

    var start = null;
    if (opts.start) {
      for (var i = 0; i < scored.length; i++) {
        if (scored[i].c.id === opts.start) { start = scored[i]; break; }
      }
    }
    if (!start) {
      // Pick from the strongest handful rather than always the single best,
      // so "a different one" is genuinely different and not a reshuffle.
      var pool = scored.slice(0, Math.max(4, Math.round(scored.length * 0.06)));
      start = pool[Math.floor(rand() * pool.length)];
    }

    var route = [], used = {}, perCountry = {};
    var remaining = opts.days - 1;   // the last day is the journey home
    var current = start.c;
    while (remaining > 0 && route.length < 14) {
      var n = nightsFor(current, opts.pace, remaining);
      route.push({ city: current, nights: n });
      used[current.id] = true;
      perCountry[current.countrySlug] = (perCountry[current.countrySlug] || 0) + 1;
      context.perCountry = perCountry;
      remaining -= n;
      if (remaining <= 0) break;

      var best = null, bestV = -1;
      // Diversity pressure, from the specification: a route that has taken
      // three big cities in a row should start finding the alternative to the
      // fourth. It builds rather than switching on, so a trip that genuinely
      // wants capitals still gets them.
      var bigRun = 0;
      for (var q = route.length - 1; q >= 0 && q >= route.length - 3; q--) {
        if (route[q].city.interests.indexOf("cities") >= 0 && !route[q].city.quiet) bigRun++;
      }
      for (var j = 0; j < scored.length; j++) {
        var cand = scored[j].c;
        if (used[cand.id]) continue;
        var d = km(current, cand);
        if (d < 25) continue;                       // effectively the same place
        // Distance is a cost, not a veto. 250 km is nearly free; 1,500 km
        // has to be earned by a much better fit.
        var travel = 1 / (1 + Math.pow(d / 420, 1.55));
        // Rail and ferry only: a 1,200 km hop is a lost day rather than a
        // cheap flight, so it costs much more in the scoring.
        if (opts.transport === "rail" && d > 900) travel *= 0.35;
        var repeat = (perCountry[cand.countrySlug] || 0) >= 3 ? 0.72 : 1;
        // Pull towards a named end: a candidate that closes the remaining
        // distance is worth more as the nights run out.
        var pull = 1;
        if (endCity) {
          var here = km(current, endCity) || 1;
          var there = km(cand, endCity);
          var urgency = 1 - (remaining / Math.max(1, opts.days));
          pull = 1 + (0.55 + 0.9 * urgency) * ((here - there) / here);
          pull = Math.max(0.35, Math.min(2.2, pull));
        }
        var diverse = 1;
        if (bigRun >= 2) {
          var isBig = cand.interests.indexOf("cities") >= 0 && !cand.quiet;
          diverse = isBig ? 0.78 : 1.18;
        }
        var v = scored[j].s * travel * repeat * diverse * pull * (0.93 + rand() * 0.14);
        if (v > bestV) { bestV = v; best = cand; }
      }
      if (!best) break;
      current = best;
    }

    // Substituting the last stop for the named end produced a 2,500 km final
    // leg and said nothing about it. The end is a pull during selection
    // instead (see endCity below), and only forced at the finish — with the
    // route told to say so if the last hop is still absurd.
    if (endCity) {
      var already = route.some(function (st) { return st.city.id === endCity.id; });
      if (!already && route.length) {
        var lastHop = km(route[route.length - 1].city, endCity);
        if (lastHop > 900) {
          // Take a night off the longest stay to pay for the extra stop
          // rather than silently lengthening the trip.
          var longest = 0;
          for (var q = 1; q < route.length; q++) {
            if (route[q].nights > route[longest].nights) longest = q;
          }
          if (route[longest].nights > 1) route[longest].nights -= 1;
          route.push({ city: endCity, nights: 1, forced: lastHop });
        } else {
          route.push({ city: endCity, nights: 1 });
        }
      }
    }
    window.__EPD_SCORED = scored;
    window.__EPD_USED = used;
    return route;
  }

  // Activities are not inside the daily band — that covers beds and meals —
  // so they are estimated separately, per day, by spending style.
  var ACTIVITY_PER_DAY = { low: 8, moderate: 18, high: 38 };

  function costing(route, opts) {
    var beds = 0, food = 0, transport = 0, nights = 0, i, d;
    for (i = 0; i < route.length; i++) {
      var rate = dailyRate(route[i].city, opts.style);
      // Sixty/forty is the split the daily bands were written against.
      beds += route[i].nights * rate * 0.6 * (STAY_FACTOR[opts.accommodation] || 1);
      food += route[i].nights * rate * 0.4;
      nights += route[i].nights;
    }
    for (i = 1; i < route.length; i++) {
      d = km(route[i - 1].city, route[i].city);
      transport += transportCost(d);
    }
    var activities = ACTIVITY_PER_DAY[opts.style] * (nights + 1);
    // Per person for everything except the room, which two people share.
    // A double is not twice a single, so the second traveller adds 55%.
    var people = opts.travellers || 1;
    var bedFactor = people === 1 ? 1 : 1 + (people - 1) * 0.55;
    beds = Math.round(beds * bedFactor);
    food = Math.round(food * people);
    transport = Math.round(transport * people);
    activities = Math.round(activities * people);
    var subtotal = beds + food + transport + activities;
    var buffer = Math.round(subtotal * 0.12);
    return { beds: beds, food: food, transport: transport, activities: activities,
             buffer: buffer, stay: beds + food, total: subtotal + buffer, people: people };
  }

  function euro(n) { return "€" + Math.round(n).toLocaleString("en-GB"); }

  // Everything is computed in euros because the daily bands are in euros.
  // This converts at the end, from the same dated table the country pages
  // use, and never pretends the result is a rate anybody will be given.
  var CUR = "EUR";
  function money(n) {
    if (CUR === "EUR" || !ATLAS.currencies) return euro(n);
    var rate = ATLAS.currencies.rates[CUR];
    if (!rate) return euro(n);
    var v = Math.round(n * rate);
    var sym = (ATLAS.currencies.symbols || {})[CUR];
    var step = v > 20000 ? 100 : 10;
    v = Math.round(v / step) * step;
    return (sym ? sym : CUR + " ") + v.toLocaleString("en-GB");
  }

  function interestName(slug) {
    for (var i = 0; i < ATLAS.interests.length; i++) {
      if (ATLAS.interests[i].slug === slug) return ATLAS.interests[i].name.toLowerCase();
    }
    return slug;
  }

  function joinList(items) {
    items = items.filter(Boolean);
    if (!items.length) return "";
    if (items.length === 1) return items[0];
    if (items.length === 2) return items[0] + " and " + items[1];
    return items.slice(0, -1).join(", ") + " and " + items[items.length - 1];
  }

  /* Why THIS stop, and not the runner-up.
   *
   * The old version said "Matches history & ruins, food." on every leg of
   * an itinerary built from history and food — which is the interests the
   * reader had just ticked, read back to them, twelve times. Same mistake
   * Discover Mode made and the same fix: never explain the constraint back.
   * The interests go once above the itinerary; each leg carries what
   * distinguishes it.
   *
   * The clauses are ordered by how surprising they are, because the useful
   * sentence is "you did not ask for this and it is here anyway".
   */
  function whyLine(city, wants, opts) {
    var bits = whyBits(city, wants, opts);
    if (!bits.length) return "";
    /* Semicolons between the clauses, not "and". Each clause already
     * contains an "and" of its own ("also architecture, art and wine"), so
     * joining them with another one produced "…and wine & drink and at its
     * peak then" — two conjunctions colliding in every sentence. */
    return city.name + " is " + bits.join("; ") + ".";
  }

  /* THE CLAUSES, SEPARATELY, SO THE SHARED ONES CAN BE HOISTED.
   *
   * whyLine() joined them straight into a sentence, and rendering a real
   * itinerary showed what that costs: on a twelve-day Italian route, five of
   * six stops read "…is here for the shape of the route rather than your
   * interests — it sits between two places that did match; …; at its peak
   * then. €123 a day here." The differing middle clause was buried between
   * forty identical words at each end.
   *
   * That is this repository's own rule — never explain the constraint back,
   * a reason shared by every result goes in one line above the list — broken
   * on the planner, which is the surface it was written for. The function
   * that composes the sentence cannot hoist anything, so the caller gets the
   * clauses and decides.
   */
  function whyBits(city, wants, opts) {
    var bits = [];

    var extra = city.interests.filter(function (t) {
      return wants.indexOf(t) < 0 &&
        ["sacred", "wine", "wild", "islands", "winter", "music", "design",
         "art", "architecture", "festivals", "rail"].indexOf(t) >= 0;
    });
    if (extra.length) {
      bits.push("also " + joinList(extra.slice(0, 3).map(interestName)));
    }

    if (opts && opts.month) {
      if ((city.shoulder || []).indexOf(opts.month) >= 0) {
        bits.push("in its quieter shoulder season then");
      } else if (city.peak.indexOf(opts.month) >= 0) {
        bits.push("at its peak then");
      } else {
        bits.push("out of season then");
      }
    }

    if (city.disc >= 80) {
      bits.push("well off the obvious circuit at " + city.disc + " for discoverability");
    } else if (city.disc <= 30) {
      bits.push("one of the obvious ones, which is not a criticism");
    }

    if ((city.todo || []).length === 0) {
      bits.push("a stop rather than a schedule — we have tagged it but not written it up");
    }

    var matched = wants.filter(function (w) { return city.interests.indexOf(w) >= 0; });
    if (!matched.length) {
      bits.unshift("here for the shape of the route rather than your interests — it sits " +
                   "between two places that did match");
    }

    return bits;
  }

  /* One leg's line, with whatever the hoist already said removed. A leg
   * whose every clause was shared says nothing at all rather than repeating
   * the hoist — an empty paragraph is worse than an absent one. */
  /* THE ROUTE, DRAWN. The planner is the most complex thing on this site and
   * its output had no geography in it at all: a summary table, a budget
   * verdict and a column of stops, on a product whose every other family
   * draws where its places are. A reader who has just been handed five
   * cities in two countries cannot see the shape of the trip.
   *
   * The same markup `pages.constellation()` emits, because there is one
   * drawing of Europe here and this is it: a <use> of #constel-eu, which the
   * page ships in its defs, the route as a cased line, and the stops lit.
   * Nothing is projected in the browser — every destination arrives with the
   * x and y the build put it at.
   *
   * FRAMED, like every journey row on this site. See glyphView below.
   */
  /* Destination names come from the dataset and never contain a quote, but
   * an accessible name is an ATTRIBUTE and this file had no escaper at all —
   * every other string it writes goes into element content. One place is
   * cheaper than a rule about which strings are safe. */
  function attr_(v) {
    return String(v).replace(/&/g, "&amp;").replace(/"/g, "&quot;")
                    .replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* THE FRAME, WHICH IS THE SAME QUESTION pages.glyph_view() ANSWERS.
   *
   * The first version drew the route on the whole continent, and a five-stop
   * Italian trip came out as a two-centimetre squiggle over Tuscany on a
   * picture of Europe — which is precisely the fault glyph_view() was lifted
   * out of region_glyph() to fix, nine identical continents with a different
   * corner lit.
   *
   * This is FRAMING and not projection: it decides which rectangle of an
   * already-projected drawing to show, so a second implementation cannot put
   * a place in the wrong country. It can still disagree, so a browser check
   * asserts it returns exactly what the Python does on the routes the site
   * already draws. The constants are the same because they are the same
   * decision: 34% padding, a 90-unit floor on it, and a 340-unit floor on
   * the span, below which the silhouette stops reading as Europe. */
  var MAP_W = 1000, MAP_H = 780;

  function glyphView(pts) {
    var xs = pts.map(function (p) { return p[0]; });
    var ys = pts.map(function (p) { return p[1]; });
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
    var y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    var pad = Math.max(Math.max(x1 - x0, y1 - y0) * 0.34, 90);
    x0 -= pad; x1 += pad; y0 -= pad; y1 += pad;
    if (x1 - x0 < 340) { var g = (340 - (x1 - x0)) / 2; x0 -= g; x1 += g; }
    var w = x1 - x0, h = y1 - y0, want = MAP_W / MAP_H, grow;
    if (w / h < want) { grow = (h * want - w) / 2; x0 -= grow; x1 += grow; }
    else { grow = (w / want - h) / 2; y0 -= grow; y1 += grow; }
    w = x1 - x0; h = y1 - y0;
    if (w >= MAP_W) { x0 = 0; w = MAP_W; }
    else { x0 = Math.min(Math.max(x0, 0), MAP_W - w); }
    if (h >= MAP_H) { y0 = 0; h = MAP_H; }
    else { y0 = Math.min(Math.max(y0, 0), MAP_H - h); }
    return [x0, y0, w, h].map(function (v) { return Math.round(v); }).join(" ");
  }
  window.__europedoorGlyphView = glyphView;   /* read by the browser suite */

  function routeFigure(route) {
    var pts = [];
    for (var i = 0; i < route.length; i++) {
      var c = route[i].city;
      if (typeof c.x !== "number" || typeof c.y !== "number") return "";
      pts.push([c.x, c.y]);
    }
    if (pts.length < 2) return "";
    var d = pts.map(function (p) {
      return p[0].toFixed(0) + "," + p[1].toFixed(0);
    }).join(" ");
    var dots = pts.map(function (p) {
      return '<circle cx="' + p[0].toFixed(0) + '" cy="' + p[1].toFixed(0) + '"/>';
    }).join("");
    var names = route.map(function (st) { return st.city.name; }).join(" to ");
    return '<figure class="planmap">' +
      '<svg class="constel" viewBox="' + glyphView(pts) + '" role="img" ' +
      'aria-label="The route this planner built: ' + attr_(names) + '">' +
      '<use href="#constel-eu"/>' +
      '<polyline class="constel-route case" points="' + d + '"/>' +
      '<polyline class="constel-route" points="' + d + '"/>' +
      '<g class="constel-lit">' + dots + "</g></svg>" +
      "</figure>";
  }

  function legWhy(city, bits, shared, rate) {
    var mine = bits.filter(function (b) { return shared.indexOf(b) < 0; });
    var text = mine.length ? city.name + " is " + mine.join("; ") + "." : "";
    if (rate) text += (text ? " " : "") + rate + " a day here.";
    return text ? '<p class="small mt-tight">' + text + "</p>" : "";
  }

  function alternativesFor(scored, route, i, used) {
    // Two runners-up near this stop: what the planner nearly chose. Showing
    // them is the difference between a recommendation and an instruction.
    var here = route[i].city, out = [];
    for (var j = 0; j < scored.length && out.length < 2; j++) {
      var c = scored[j].c;
      if (used[c.id]) continue;
      var d = km(here, c);
      if (d < 30 || d > 260) continue;
      out.push({ city: c, km: d });
    }
    return out;
  }

  function dayPlan(city, nights, dayFrom) {
    // Distribute what we hold across the days round-robin, so three items
    // over four nights gives three named days and one free one rather than
    // two crowded days and two apologies.
    var todo = (city.todo || []).slice();
    var days = [];
    for (var n = 0; n < nights; n++) days.push({ day: dayFrom + n, items: [] });
    for (var i = 0; i < todo.length; i++) days[i % nights].items.push(todo[i]);
    return days;
  }

  /* The UI specification's rule for the error state, and the sharpest
   * sentence in it: "Do not fabricate a result just to avoid an error."
   *
   * This planner will always return SOMETHING — it scores every city in the
   * Atlas, so there is always a best one — and that is exactly the failure
   * mode being described. A three-day request that names two interests
   * nothing carries still gets a route; it is just a route that answers a
   * different question from the one asked, presented with the same
   * confidence as a good one.
   *
   * So the refusal is a real check, made after planning and before
   * rendering, and it names the constraint rather than saying "no results".
   * Each reason carries the field that would fix it. */
  function whyUnreliable(route, opts) {
    if (!route.length) {
      return ["Nothing in the Atlas fits that yet.",
              "That usually means several interests at once that no one place carries.",
              "interest"];
    }
    // A trip whose stops do not fill the days is not an itinerary; it is a
    // list with gaps we would be papering over.
    var nights = 0;
    for (var i = 0; i < route.length; i++) nights += route[i].nights;
    if (opts.days >= 4 && nights < Math.ceil((opts.days - 1) * 0.6)) {
      return ["We could only fill " + nights + " of your " + opts.days + " days.",
              "The constraints rule out too much of the Atlas to build the rest honestly.",
              "days"];
    }
    // Interests that scored nothing anywhere. Returning a route built on the
    // ones that did match, without saying so, is answering a question the
    // reader did not ask.
    if (opts.wants && opts.wants.length) {
      var covered = {};
      route.forEach(function (st) {
        (st.city.interests || []).forEach(function (i) { covered[i] = true; });
      });
      var missed = opts.wants.filter(function (w) { return !covered[w]; });
      if (missed.length >= Math.ceil(opts.wants.length / 2)) {
        return ["This route does not actually deliver " + missed.join(", ") + ".",
                "Those are half or more of what you asked for, so calling it your itinerary " +
                "would be overstating it.",
                "interest"];
      }
    }
    /* The budget check is a refusal only when it is hopeless, and only when
     * the budget is the reader's rather than ours.
     *
     * The first version of this refused "three weeks by train through the
     * Alps in winter, luxury" at €4,686 against €2,500 — a budget that
     * sentence never mentioned and that we had filled in as a default. That
     * is refusing our own assumption and telling the reader they asked for
     * something impossible. If they did not state a budget, show the plan
     * and let the over-budget verdict do its quieter job. */
    var c = costing(route, opts);
    if (opts.budgetStated && opts.budget && c.total > opts.budget * 1.8) {
      return [money(c.total) + " against a budget of " + money(opts.budget) + ".",
              "That is not a plan you can take. Widen the budget, shorten the trip, or " +
              "choose guesthouses and rail.",
              "budget"];
    }
    return null;
  }

  function renderRefusal(why, route, opts) {
    /* Never a dead end: it says what went wrong, which control fixes it, and
     * offers the nearest thing that would work — because "adjust your
     * preferences" with nothing behind it is the same as no answer. */
    var suggestions = [];
    if (opts.days < 10) suggestions.push(["days", (opts.days + 4) + " days instead of " + opts.days]);
    if (opts.wants && opts.wants.length > 2) suggestions.push(["interest", "fewer interests at once"]);
    if (opts.budget) suggestions.push(["budget", "a wider budget"]);
    if (opts.transport === "rail") suggestions.push(["transport", "allowing flights"]);
    result.innerHTML =
      '<div class="note warn">' +
      '<h2 class="mini">We could not build a journey we would stand behind</h2>' +
      "<p><strong>" + why[0] + "</strong> " + why[1] + "</p>" +
      (suggestions.length
        ? "<p>Any of these would probably work: " + suggestions.map(function (x) {
            return '<a href="#' + x[0] + '" data-focus="' + x[0] + '">' + x[1] + "</a>";
          }).join(", ") + ".</p>"
        : "") +
      '<p class="small">We would rather say this than hand you a route that answers a ' +
      'different question and let you find out in Europe.</p></div>' +
      (route.length
        ? '<details class="mt5"><summary>Show it anyway (' + route.length +
          " stops, and we do not recommend it)</summary><div id=\"anyway\"></div></details>"
        : "");
    result.querySelectorAll("[data-focus]").forEach(function (a) {
      a.addEventListener("click", function (ev) {
        ev.preventDefault();
        var f = document.getElementById(a.getAttribute("data-focus"));
        if (f) { f.scrollIntoView({ behavior: "smooth", block: "center" }); f.focus(); }
      });
    });
    var det = result.querySelector("details");
    if (det) {
      det.addEventListener("toggle", function () {
        if (det.open && !det.dataset.done) { det.dataset.done = "1"; drawPlan(route, opts, det.querySelector("#anyway")); }
      });
    }
  }

  function render(route, opts) {
    var why = whyUnreliable(route, opts);
    if (why) { renderRefusal(why, route, opts); return; }
    drawPlan(route, opts, result);
  }

  /* `into` exists so the refusal can render the rejected plan inside its own
   * <details> without touching the main result element. Never reassign the
   * module-level `result` here: a previous version did, and every subsequent
   * plan then rendered inside a collapsed details block from a request two
   * screens ago. */
  /* Once a route has been edited it is no longer what the planner would
   * produce from these inputs, so it has to be carried explicitly rather
   * than regenerated. EDITED holds it; "Give me a different one" and any
   * change to the form clear it, because at that point the reader has asked
   * for a new plan rather than a change to this one. */
  var EDITED = null;

  function editRoute(fn) {
    if (!EDITED) return;
    var route = EDITED.route, opts = EDITED.opts;
    fn(route);
    if (!route.length) { EDITED = null; go(); return; }
    // Days are the sum of the nights plus the journey home, so an edit
    // moves the trip length rather than silently reflowing it into a
    // number the reader did not choose.
    var nights = 0;
    for (var i = 0; i < route.length; i++) nights += route[i].nights;
    opts.days = nights + 1;
    form.days.value = opts.days;
    drawPlan(route, opts, result);
    result.insertAdjacentHTML("afterbegin",
      '<div class="note"><p><strong>You have changed this itinerary.</strong> ' +
      "The days, the distances and the estimate below are recomputed from your version, " +
      "not from the planner's. " +
      '<button type="button" class="linkish" id="replan">Start again from the form</button></p></div>');
    var again = document.getElementById("replan");
    if (again) again.addEventListener("click", function () { EDITED = null; go(); });
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* Fold accents so "malmo" finds Malmö. The search page does the same
   * thing; both had it before this picker existed, and a reader who can
   * find a city in search and not in the planner would be right to think
   * one of them is broken. */
  /* A QUARTER OF THE ATLAS COULD NOT BE NAMED IN THE SENTENCE BOX.
   *
   * `words()` lowercases and then strips everything outside [a-z0-9] to a
   * space, and the names it was compared against were only lowercased. So
   * the sentence became "start from krakow" while the name stayed "kraków",
   * and the two never met: 77 of 313 destinations — Kraków, Málaga,
   * Córdoba, Reykjavík, Tromsø, Brașov, Gdańsk, Évora, San Sebastián,
   * Lübeck — and Türkiye, the only country whose own name carries a
   * diacritic. A reader typing "Ten days from Kraków" got a route that
   * ignored Kraków.
   *
   * It is the worst possible place for a silent failure: this planner's
   * whole pitch is that it "shows you exactly what it understood, naming
   * anything it could not take account of rather than quietly dropping it",
   * and here it never saw the word at all, so there was nothing to name.
   *
   * NFD ALONE FIXES HALF OF IT. ø, þ, ð, ħ, ł, æ and ß have no combining
   * decomposition, so Tromsø, Þingvellir, Ísafjörður, Ħaġar Qim and
   * Białowieża survived the first repair — a transliteration table is not
   * an optimisation here, it is the other half of the alphabet Europe
   * actually uses.
   *
   * AND THE REAL RULE IS ONE NORMALISER, BOTH SIDES. Folding the names and
   * not the punctuation still left 41: "Kardamyli & the Mani" keeps its
   * ampersand while the sentence has lost it. Every name is put through
   * `words()` now, the same function the sentence goes through, and the
   * count is 0 of 313. */
  var TRANSLIT = { "ø": "o", "þ": "th", "ð": "d", "ħ": "h", "ł": "l",
                   "æ": "ae", "œ": "oe", "ß": "ss", "đ": "d", "ı": "i" };
  function fold(x) {
    return String(x).toLowerCase().replace(/[øþðħłæœßđı]/g, function (ch) {
      return TRANSLIT[ch];
    }).normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function addPanel(panel, route, opts, after) {
    var inRoute = {};
    route.forEach(function (st) { inRoute[st.city.id] = true; });
    var from = route[after].city;

    panel.innerHTML =
      '<label class="small" for="addq' + after + '">Add a stop after ' +
      from.name + '</label>' +
      '<input type="search" id="addq' + after + '" class="addq" autocomplete="off" ' +
      'placeholder="Type a city — Ghent, Ohrid, Trieste…" ' +
      'aria-describedby="addhelp' + after + '">' +
      '<p class="small" id="addhelp' + after + '">Anywhere in the Atlas. Distance is ' +
      'from ' + from.name + ', so you can see what a stop actually costs you. ' +
      'Escape closes this.</p>' +
      // role="status" rather than a line inside the list, because the
      // result of typing has to be ANNOUNCED. The first version put "Two
      // letters is enough to start" in an <li> inside a role="listbox"
      // whose children carried no role at all — so assistive technology was
      // told there was a listbox, asked it for its options, and got none.
      // A role is a claim about the markup under it, and that one was not
      // kept. The list is a plain list of buttons now, and the sentence
      // that changes lives in a live region where a change is heard.
      '<p class="small addsay" role="status"></p>' +
      '<ul class="addhits"></ul>';

    var box = panel.querySelector(".addq");
    var hits = panel.querySelector(".addhits");
    var say = panel.querySelector(".addsay");

    function render() {
      var q = fold(box.value.trim());
      if (q.length < 2) {
        hits.innerHTML = "";
        say.textContent = "Two letters is enough to start.";
        return;
      }
      var found = [];
      for (var i = 0; i < ATLAS.cities.length && found.length < 200; i++) {
        var c = ATLAS.cities[i];
        if (inRoute[c.id]) continue;   // already on the route
        if (fold(c.name).indexOf(q) < 0 && fold(c.country).indexOf(q) < 0) continue;
        found.push({ c: c, d: km(from, c), starts: fold(c.name).indexOf(q) === 0 });
      }
      // A prefix match first, then the nearest — because on a route the
      // question is almost always "what is near here", and a list ordered
      // purely alphabetically buries it.
      found.sort(function (a, b) {
        if (a.starts !== b.starts) return a.starts ? -1 : 1;
        return a.d - b.d;
      });
      if (!found.length) {
        hits.innerHTML = '<li class="small">Nothing in the Atlas matches that. ' +
          'It may be somewhere we have not written up yet — ' +
          '<a href="/countries">the countries page</a> shows what we hold.</li>';
        say.textContent = "Nothing matches " + box.value.trim() + ".";
        return;
      }
      var shown = Math.min(found.length, 8);
      say.textContent = found.length > shown
        ? shown + " of " + found.length + " matches, nearest first."
        : shown + (shown === 1 ? " match." : " matches, nearest first.");
      hits.innerHTML = found.slice(0, 8).map(function (f) {
        return '<li><button type="button" class="addhit" data-city="' + f.c.id + '">' +
          "<span>" + f.c.name + ' <span class="small">· ' + f.c.country + "</span></span>" +
          '<span class="small">' + f.d.toLocaleString("en-GB") + " km</span></button></li>";
      }).join("");
      hits.querySelectorAll(".addhit").forEach(function (b) {
        b.addEventListener("click", function () {
          var id = b.getAttribute("data-city");
          var city = null;
          for (var i = 0; i < ATLAS.cities.length; i++) {
            if (ATLAS.cities[i].id === id) { city = ATLAS.cities[i]; break; }
          }
          if (!city) return;
          editRoute(function (r) {
            // Its own recorded range, at the reader's pace — the same
            // number the planner would have used had it chosen this stop.
            r.splice(after + 1, 0,
                     { city: city, nights: nightsFor(city, opts.pace, 99) });
            r.forEach(function (st) { delete st.forced; });
          });
        });
      });
    }

    box.addEventListener("input", render);
    // A disclosure that takes focus has to give it back. Without this a
    // keyboard reader who opens the panel and changes their mind can only
    // leave it by shift-tabbing back over the trigger; there was no way to
    // CLOSE it at all without a mouse.
    box.addEventListener("keydown", function (e) {
      if (e.key !== "Escape" && e.key !== "Esc") return;
      e.preventDefault();
      var trigger = panel.parentNode.querySelector('[data-add="' + after + '"]');
      panel.hidden = true;
      if (trigger) {
        trigger.setAttribute("aria-expanded", "false");
        trigger.focus();
      }
    });
    render();
    box.focus();
  }

  /* ── What if? ──────────────────────────────────────────────────────
   *
   * The signature feature, and the thing that separates it from a row of
   * preset buttons is that it SHOWS THE CONSEQUENCE BEFORE APPLYING IT.
   *
   * A button that silently rebuilds the itinerary is a slot machine: the
   * reader cannot tell what the change cost them, and after three presses
   * they have lost the plan they liked. So every what-if produces a
   * comparison — what moves, what it costs, and what you give up — and only
   * then offers to apply it. "Keep what I have" is a real option and the
   * default.
   *
   * Every transform is deterministic and operates on the route the reader
   * already has, except the two that genuinely cannot: rail-only and
   * "more history", where the constraint changes which places belong in the
   * route at all. Those replan, and say so.
   */
  function cloneRoute(route) {
    return route.map(function (st) {
      return { city: st.city, nights: st.nights };
    });
  }

  var WHAT_IFS = [
    {
      id: "longer",
      label: "I stay two days longer",
      note: "Nights go to the stops with the most to do, not spread evenly.",
      run: function (route, opts) {
        var r = cloneRoute(route);
        var order = r.map(function (st, i) { return i; }).sort(function (a, b) {
          return (r[b].city.todo || []).length - (r[a].city.todo || []).length;
        });
        r[order[0]].nights += 1;
        r[order[Math.min(1, order.length - 1)]].nights += 1;
        return { route: r, opts: opts };
      },
    },
    {
      id: "cheaper",
      label: "I want to spend less",
      note: "Guesthouses instead of hotels, and a band down on daily spending. " +
            "The route does not change; what you pay for it does.",
      run: function (route, opts) {
        var o = {};
        for (var k in opts) o[k] = opts[k];
        o.accommodation = "guesthouse";
        o.style = opts.style === "high" ? "moderate" : "low";
        return { route: cloneRoute(route), opts: o };
      },
    },
    {
      id: "rail",
      label: "I travel entirely by train",
      note: "Replans: a 1,200 km hop is a lost day rather than a cheap flight, " +
            "so some stops stop making sense.",
      replan: true,
      run: function (route, opts) {
        var o = {};
        for (var k in opts) o[k] = opts[k];
        o.transport = "rail";
        o.start = route[0].city.id;
        return { route: plan(o), opts: o };
      },
    },
    {
      id: "quieter",
      label: "I avoid the crowded places",
      note: "Swaps the most obvious stops for the nearest less obvious one in the " +
            "same country. Uses the published discoverability score, not a guess " +
            "about crowds.",
      run: function (route, opts) {
        var r = cloneRoute(route);
        var used = {};
        r.forEach(function (st) { used[st.city.id] = true; });
        // Swap the two least discoverable stops, never the first — a start
        // the reader chose is not ours to move.
        var order = r.map(function (st, i) { return i; })
                     .filter(function (i) { return i > 0; })
                     .sort(function (a, b) { return r[a].city.disc - r[b].city.disc; });
        var swaps = 0;
        for (var q = 0; q < order.length && swaps < 2; q++) {
          var i = order[q];
          if (r[i].city.disc >= 70) continue;      // already not obvious
          var best = null, bestD = 1e9;
          for (var j = 0; j < ATLAS.cities.length; j++) {
            var c = ATLAS.cities[j];
            /* +20, not +25. The first threshold was one point too strict:
             * for a Tuscan route it rejected Arezzo, Urbino and Civita di
             * Bagnoregio, all at exactly +24 over Siena — which are the
             * right answers to "avoid the crowded places" in Tuscany, and
             * the feature silently reported that nothing would change. */
            if (used[c.id] || c.disc < r[i].city.disc + 20) continue;
            /* Same country, not merely nearby. Straight-line distance does
             * not know about water: the first version swapped Siena for
             * Corte, which is 200 km away and in Corsica — a ferry, not a
             * detour. The site already refuses to treat a sea crossing as a
             * short hop everywhere else; this is the same rule. */
            if (c.countrySlug !== r[i].city.countrySlug) continue;
            var d = km(r[i].city, c);
            if (d > 260) continue;                 // still on the same route
            if (d < bestD) { bestD = d; best = c; }
          }
          if (best) {
            used[best.id] = true;
            delete used[r[i].city.id];
            r[i] = { city: best, nights: r[i].nights };
            swaps++;
          }
        }
        return { route: r, opts: opts };
      },
    },
    {
      id: "history",
      label: "I want more history and sacred places",
      note: "Replans with those added to what you asked for.",
      replan: true,
      run: function (route, opts) {
        var o = {};
        for (var k in opts) o[k] = opts[k];
        o.wants = opts.wants.slice();
        ["history", "sacred"].forEach(function (w) {
          if (o.wants.indexOf(w) < 0) o.wants.push(w);
        });
        o.start = route[0].city.id;
        return { route: plan(o), opts: o };
      },
    },
  ];

  function routeIds(route) {
    return route.map(function (st) { return st.city.id + ":" + st.nights; }).join("|");
  }

  function diffRoutes(before, after) {
    var wasNames = before.map(function (s) { return s.city.name; });
    var isNames = after.map(function (s) { return s.city.name; });
    return {
      gone: wasNames.filter(function (n) { return isNames.indexOf(n) < 0; }),
      added: isNames.filter(function (n) { return wasNames.indexOf(n) < 0; }),
      wasNights: before.reduce(function (a, s) { return a + s.nights; }, 0),
      isNights: after.reduce(function (a, s) { return a + s.nights; }, 0),
    };
  }

  function renderWhatIf(scope, route, opts) {
    var panel = scope.querySelector("#whatif");
    if (!panel) return;
    panel.innerHTML =
      '<h2 class="mini">What if…</h2>' +
      '<p class="small">Each of these shows you what it would cost before it changes ' +
      "anything. Nothing is applied until you say so.</p>" +
      '<div class="chips">' + WHAT_IFS.map(function (w) {
        return '<button type="button" class="chip pick" data-whatif="' + w.id + '">' +
          w.label + "</button>";
      }).join("") + "</div>" +
      '<div id="whatif-out"></div>' +
      '<p class="small mt5"><strong>What if it rains?</strong> We cannot answer that one. ' +
      'EuropeDoor holds no weather data and no forecast for anywhere — a "rainy day plan" ' +
      "built from nothing would be a guess with a confident face on it. What each stop has " +
      "indoors is on its own page.</p>";

    panel.querySelectorAll("[data-whatif]").forEach(function (b) {
      b.addEventListener("click", function () {
        var w = WHAT_IFS.filter(function (x) { return x.id === b.getAttribute("data-whatif"); })[0];
        var out = panel.querySelector("#whatif-out");
        /* NOT `result`. That is the module-level element every render
         * writes into, and shadowing it here meant applying a what-if
         * called insertAdjacentHTML on a plain object. Second time a local
         * has shadowed an outer name in this file; both times the symptom
         * was a method missing on something that looked right. */
        var outcome;
        try { outcome = w.run(route, opts); } catch (e) { outcome = null; }
        if (!outcome || !outcome.route || !outcome.route.length) {
          out.innerHTML = '<div class="note warn"><p>That change leaves nothing the ' +
            "planner would stand behind. The constraints are already tight.</p></div>";
          return;
        }
        var newOpts = outcome.opts;
        var newRoute = outcome.route;
        var nights = newRoute.reduce(function (a, s) { return a + s.nights; }, 0);
        newOpts = (function (o) {
          var c = {}; for (var k in o) c[k] = o[k];
          c.days = nights + 1;
          return c;
        })(newOpts);

        if (routeIds(newRoute) === routeIds(route) && newOpts.style === opts.style &&
            newOpts.accommodation === opts.accommodation) {
          out.innerHTML = '<div class="note"><p><strong>Nothing would change.</strong> ' +
            "This itinerary already satisfies that — which is worth knowing, and is why " +
            "the button says what it would do rather than just doing it.</p></div>";
          return;
        }

        var d = diffRoutes(route, newRoute);
        var was = costing(route, opts), now = costing(newRoute, newOpts);
        var delta = now.total - was.total;
        var lines = [];
        if (d.isNights !== d.wasNights) {
          lines.push("<li><strong>" + (d.isNights > d.wasNights ? "+" : "") +
            (d.isNights - d.wasNights) + " nights</strong> — " + (newOpts.days) +
            " days instead of " + opts.days + ".</li>");
        }
        if (d.gone.length) {
          lines.push("<li><strong>You lose</strong> " + d.gone.join(", ") + ".</li>");
        }
        if (d.added.length) {
          lines.push("<li><strong>You gain</strong> " + d.added.join(", ") + ".</li>");
        }
        lines.push("<li><strong>" + (delta >= 0 ? "+" : "−") + money(Math.abs(delta)) +
          "</strong> — " + money(now.total) + " instead of " + money(was.total) + ".</li>");
        if (w.replan) {
          lines.push("<li class=\"small\">This one replans rather than editing what you " +
            "have, so the order may change more than you expect.</li>");
        }

        out.innerHTML =
          '<div class="note whatif-preview"><h3 class="mini">What if — ' +
          w.label + "?</h3>" +
          "<p class=\"small\">" + w.note + "</p>" +
          "<ul class=\"stack\">" + lines.join("") + "</ul>" +
          '<div class="hero-actions mt0">' +
          '<button class="btn" type="button" id="whatif-apply">Apply this</button>' +
          '<button class="btn ghost" type="button" id="whatif-keep">Keep what I have</button>' +
          "</div></div>";

        out.querySelector("#whatif-keep").addEventListener("click", function () {
          out.innerHTML = "";
        });
        out.querySelector("#whatif-apply").addEventListener("click", function () {
          EDITED = { route: newRoute, opts: newOpts };
          form.days.value = newOpts.days;
          if (form.style) form.style.value = newOpts.style;
          drawPlan(newRoute, newOpts, result);
          result.insertAdjacentHTML("afterbegin",
            '<div class="note"><p><strong>Applied: “' + w.label + '”.</strong> ' +
            "Everything below is recomputed from your version. " +
            '<button type="button" class="linkish" id="replan">Start again from the form</button></p></div>');
          var again = document.getElementById("replan");
          if (again) again.addEventListener("click", function () { EDITED = null; go(); });
          result.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });
    });
  }

  function wireEditing(scope, route, opts) {
    EDITED = { route: route, opts: opts };
    scope.querySelectorAll("[data-add]").forEach(function (b) {
      b.addEventListener("click", function () {
        var after = Number(b.getAttribute("data-add"));
        var panel = scope.querySelector("#addpanel" + after);
        if (!panel) return;
        var open = !panel.hidden;
        // One panel at a time: two open search boxes is two places to type
        // and no way to tell which one is listening.
        scope.querySelectorAll(".addstop").forEach(function (x) { x.hidden = true; });
        scope.querySelectorAll("[data-add]").forEach(function (x) {
          x.setAttribute("aria-expanded", "false");
        });
        if (open) return;
        panel.hidden = false;
        b.setAttribute("aria-expanded", "true");
        addPanel(panel, route, opts, after);
      });
    });
    scope.querySelectorAll("[data-move]").forEach(function (b) {
      b.addEventListener("click", function () {
        var i = Number(b.getAttribute("data-move")), d = Number(b.getAttribute("data-dir"));
        editRoute(function (r) {
          if (i + d < 0 || i + d >= r.length) return;
          var tmp = r[i]; r[i] = r[i + d]; r[i + d] = tmp;
          // A reordered route is no longer the planner's, so the forced-leg
          // note from the original ordering is no longer true of it.
          r.forEach(function (st) { delete st.forced; });
        });
      });
    });
    scope.querySelectorAll("[data-nights]").forEach(function (b) {
      b.addEventListener("click", function () {
        var i = Number(b.getAttribute("data-nights")), by = Number(b.getAttribute("data-by"));
        editRoute(function (r) {
          r[i].nights = Math.max(1, Math.min(14, r[i].nights + by));
        });
      });
    });
    scope.querySelectorAll("[data-drop]").forEach(function (b) {
      b.addEventListener("click", function () {
        var i = Number(b.getAttribute("data-drop"));
        editRoute(function (r) { if (r.length > 2) r.splice(i, 1); });
      });
    });
  }

  function drawPlan(route, opts, into) {
    var out = into || result;
    CUR = opts.currency || "EUR";
    var c = costing(route, opts);
    var day = 1, legs = "", i, hop, countries = [];

    /* WHAT EVERY STOP SAYS, HOISTED OUT OF EVERY STOP. Rendering a real
     * twelve-day Italian route showed five of six legs opening on the same
     * forty words — "…is here for the shape of the route rather than your
     * interests — it sits between two places that did match" — and closing
     * on the same "€123 a day here", with the one differing clause buried
     * between them. Individually true, collectively boilerplate, and
     * boilerplate is what a reader learns to skip.
     *
     * A clause is hoisted only when EVERY stop carries it and there are at
     * least three stops: on a two-stop route "both of them" is not a
     * pattern, it is a coincidence. */
    var allBits = [], allRates = [], shared = [], sharedRate = null;
    for (i = 0; i < route.length; i++) {
      allBits.push(whyBits(route[i].city, opts.wants, opts));
      allRates.push(money(dailyRate(route[i].city, opts.style)));
    }
    if (route.length >= 3) {
      shared = allBits[0].filter(function (b) {
        return allBits.every(function (bs) { return bs.indexOf(b) >= 0; });
      });
      if (allRates.every(function (r) { return r === allRates[0]; })) {
        sharedRate = allRates[0];
      }
    }
    var scoredAll = window.__EPD_SCORED || [];
    var usedAll = window.__EPD_USED || {};
    for (i = 0; i < route.length; i++) {
      var st = route[i], city = st.city;
      if (countries.indexOf(city.country) < 0) countries.push(city.country);
      hop = "";
      if (i > 0) {
        hop = '<p class="hop">↳ From ' + route[i - 1].city.name + ': ' +
              hopNote(km(route[i - 1].city, city), opts) + "</p>";
      }
      var last = day + st.nights - 1;
      var when = st.nights === 1 ? "Day " + day : "Days " + day + "–" + last;

      var days = dayPlan(city, st.nights, day);
      var empty = (city.todo || []).length === 0;
      var dayHtml = days.map(function (dd) {
        if (!dd.items.length) {
          return "<li><strong>Day " + dd.day + "</strong> — free. Nothing further recorded.</li>";
        }
        return "<li><strong>Day " + dd.day + "</strong> — " + dd.items.map(function (it) {
          return '<a href="' + it.u + '">' + it.n + "</a>";
        }).join("; ") + "</li>";
      }).join("");
      if (empty) {
        dayHtml = "<li>We hold nothing specific for " + city.name + " yet. That is a gap in " +
          '<a href="' + city.url + '">our writing</a> rather than in the place, and it is ' +
          "why it is a stop rather than a schedule.</li>";
      }

      // No alternatives for a start the traveller chose themselves.
      var forcedNote = st.forced
        ? '<p class="small alt">You asked to end near ' + city.name + ". It is " + st.forced +
          " km from the stop before it, which is a travel day rather than a leg — the planner " +
          "would not have gone there on its own. A night has been taken off the longest stay " +
          "to pay for it.</p>"
        : "";
      var alts = (i === 0 && opts.start) ? [] : alternativesFor(scoredAll, route, i, usedAll);
      var altHtml = alts.length
        ? '<p class="small alt">Instead of ' + city.name + ": " + alts.map(function (a) {
            return '<a href="' + a.city.url + '">' + a.city.name + "</a> (" + a.km + " km)";
          }).join(", ") + ". The planner ranked them just behind.</p>"
        : "";

      /* The itinerary is editable from here, which is the difference
       * between a suggestion and a plan. Every control is a real button
       * with a real label — not a drag handle — because drag-and-drop is
       * unusable with a keyboard, unusable with a screen reader, and
       * miserable on a phone, and this is a list of at most fourteen
       * things. "Move up" is not a worse interaction than dragging; it is
       * a better one that looks less impressive. */
      var controls =
        '<p class="legedit">' +
        '<button type="button" class="linkish" data-move="' + i + '" data-dir="-1"' +
          (i === 0 ? " disabled" : "") + ' aria-label="Move ' + city.name + ' earlier">↑ earlier</button>' +
        '<button type="button" class="linkish" data-move="' + i + '" data-dir="1"' +
          (i === route.length - 1 ? " disabled" : "") + ' aria-label="Move ' + city.name + ' later">↓ later</button>' +
        '<button type="button" class="linkish" data-nights="' + i + '" data-by="-1"' +
          (st.nights <= 1 ? " disabled" : "") + ' aria-label="One night fewer in ' + city.name + '">− night</button>' +
        '<button type="button" class="linkish" data-nights="' + i + '" data-by="1"' +
          ' aria-label="One night more in ' + city.name + '">+ night</button>' +
        '<button type="button" class="linkish drop" data-drop="' + i + '"' +
          (route.length <= 2 ? " disabled" : "") + ' aria-label="Remove ' + city.name + ' from the route">× remove</button>' +
        '<button type="button" class="linkish" data-add="' + i + '"' +
          ' aria-expanded="false" aria-controls="addpanel' + i + '"' +
          ' aria-label="Add a stop after ' + city.name + '">+ stop after</button>' +
        "</p>" +
        '<div class="addstop" id="addpanel' + i + '" hidden></div>';

      legs += '<li class="leg"><div class="leg-when">' + when + '</div><div>' +
              hop +
              '<h3><a href="' + city.url + '">' + city.name + "</a> <span class=\"small\">· " +
              city.country + " · " + city.region + "</span></h3>" +
              "<p>" + city.why + "</p>" +
              legWhy(city, allBits[i], shared, sharedRate ? "" : allRates[i]) +
              '<ul class="daylist">' + dayHtml + "</ul>" + forcedNote + altHtml +
              controls +
              "</div></li>";
      day = last + 1;
    }

    var over = c.total - opts.budget;
    var verdict;
    if (over <= 0) {
      verdict = '<div class="note"><p><strong>' + money(-over) + " under budget.</strong> " +
        "Room for a better hotel in one place, or a day longer.</p></div>";
    } else {
      verdict = '<div class="note warn"><p><strong>' + money(over) + " over budget.</strong> " +
        "Drop the spending style a level, cut the longest hop, or take one night off the most " +
        "expensive stop — the planner will not quietly downgrade the trip for you.</p></div>";
    }

    var totalKm = 0;
    for (i = 1; i < route.length; i++) totalKm += km(route[i - 1].city, route[i].city);

    out.innerHTML =
      /* The country was pluralised and the days and the stops were not, so a
       * short trip read "3 days, 1 stops, 1 country" — two thirds of one
       * line correct. Found by following a country page's own hand-off into
       * Andorra, which is the shortest route this atlas can build. */
      '<h2 class="mt7">' + opts.days + (opts.days === 1 ? " day, " : " days, ") +
        route.length + (route.length === 1 ? " stop, " : " stops, ") +
        countries.length + (countries.length === 1 ? " country" : " countries") + "</h2>" +
      '<dl class="result-summary">' +
        "<div><dt>Estimated total</dt><dd>" + money(c.total) + "</dd></div>" +
        "<div><dt>Accommodation</dt><dd>" + money(c.beds) + "</dd></div>" +
        "<div><dt>Food</dt><dd>" + money(c.food) + "</dd></div>" +
        "<div><dt>Transport</dt><dd>" + money(c.transport) + "</dd></div>" +
        "<div><dt>Activities</dt><dd>" + money(c.activities) + "</dd></div>" +
        "<div><dt>12% buffer</dt><dd>" + money(c.buffer) + "</dd></div>" +
        "<div><dt>Straight-line distance</dt><dd>" + totalKm.toLocaleString("en-GB") + " km</dd></div>" +
      "</dl>" +
      verdict +
      routeFigure(route) +
      (opts.wants.length
        ? '<p class="whyall"><span>In common</span> Every stop below carries at least one of ' +
          joinList(opts.wants.map(interestName)) +
          " — because that is what you asked for. Each line says what else is true of it.</p>"
        : "") +
      (shared.length || sharedRate
        ? '<p class="whyall"><span>Every stop</span> ' +
          (shared.length
            ? "is " + shared.join("; ") + "."
            : "") +
          (sharedRate
            ? (shared.length ? " " : "") + "Every one of them costs about " +
              sharedRate + " a day."
            : "") +
          " Each line below carries only what is different." + "</p>"
        : "") +
      '<p class="whyall"><span>Every hop</span> is a straight line, and the time ' +
        'is that distance at one average speed. With no route geometry here the ' +
        'estimate is out in both directions: a mountain leg is slower, a fast ' +
        'corridor hours quicker.</p>' +
      '<ul class="legs">' + legs + "</ul>" +
      '<div class="hero-actions mt0">' +
        '<button class="btn ghost" type="button" id="saveplan">Save this to My Europe</button>' +
        '<button class="btn ghost" type="button" id="shareplan">Copy a link to it</button>' +
      "</div>" +
      '<p class="small" id="planstate"></p>' +
      '<div class="whatif" id="whatif"></div>' +
      '<p class="small">Each day lists the places and experiences we hold for that stop. ' +
      'It does not name a hotel or a restaurant: EuropeDoor lists neither yet, and ' +
      '<a href="/for-businesses">the reason is on the businesses page</a>. ' +
      (CUR !== "EUR" ? "Converted from euros at an indicative, dated rate — " +
        '<a href="/help#currency">what that means</a>. ' : "") +
      "</p>" +
      '<p class="small">Estimates are planning arithmetic from published daily bands and ' +
      'straight-line distances — not quotes. Activities are estimated at ' +
      money(ACTIVITY_PER_DAY[opts.style]) + ' a day for this spending style. ' +
      '<a href="/sources">How these numbers are made</a>.</p>';

    wireSaveAndShare(route, opts, out);
    wireEditing(out, route, opts);
    renderWhatIf(out, route, opts);
  }


  /* ── Reading a sentence ────────────────────────────────────────────
   *
   * "I have 12 days, €2,500, I love history, mountains and food."
   *
   * This is the natural-language front door from the brief, implemented
   * with rules rather than a model, and labelled as such on the page. The
   * reason is not cost: it is that a rule can be shown to the user. Every
   * field it fills is displayed back — "I read that as…" — and every
   * request it cannot express is named rather than dropped, which is the
   * same `unsupported` contract the AI specification insists on.
   *
   * When a model does replace this, its job is only to produce the same
   * object. The scoring, the route and the refusals stay here. */

  var WORDS = {
    history:    ["history","historic","historical","ruins","ruin","ancient","medieval","roman","greek","viking","castle","castles","fortress","archaeolog*","prehistoric","ottoman*","habsburg"],
    art:        ["art","gallery","galleries","museum","museums","painting","paintings","renaissance","baroque art"],
    architecture:["architecture","architectural","buildings","modernist","gothic","art nouveau","brutalis*","design of buildings"],
    sacred:     ["sacred","church","churches","cathedral","cathedrals","monaster*","monastery","pilgrim*","pilgrimage","abbey","mosque","synagogue","temple","spiritual","religious","camino"],
    food:       ["food","eat","eating","cuisine","restaurant","restaurants","gastronom*","culinary","cooking","market","markets","cheese","seafood","street food"],
    wine:       ["wine","wines","vineyard","vineyards","winery","wineries","cellar","cellars","beer","brewery","whisky","distiller*","drink"],
    mountains:  ["mountain","mountains","alps","alpine","peaks","hiking","hike","trek*","trekking","walking","summit","dolomites","pyrenees","carpathian","caucasus","fjord","fjords"],
    coast:      ["coast","coastal","beach","beaches","sea","seaside","shore","swim","swimming","sailing","riviera"],
    islands:    ["island","islands","archipelago","ferry","ferries","cyclades","hebrides"],
    nature:     ["nature","wilderness","wild places","forest","forests","landscape","national park","parks","outdoors","scenery","scenic"],
    wild:       ["wildlife","animals","birds","birdwatch*","whale","whales","bears","bison","safari","puffin"],
    winter:     ["winter","snow","ski","skiing","snowboard*","northern lights","aurora","ice","cold"],
    cities:     ["city","cities","urban","metropol*","capital","capitals","big city"],
    music:      ["music","concert","concerts","opera","jazz","nightlife","clubs","clubbing","bars","live music","festival music"],
    design:     ["design","designer","craft","crafts","artisan","workshop","making","fashion"],
    rail:       ["train","trains","rail","railway","railways","by rail","slow travel","interrail","sleeper"],
    festivals:  ["festival","festivals","carnival","celebration*","celebrations","christmas market"]
  };

  // Named geography. A traveller who says "the Alps" or "Portugal" has given
  // the strongest constraint in the sentence, and reading it as an interest
  // and discarding it is the most annoying thing a planner can do.
  var GEO = {
    "alps": ["switzerland","austria","france","italy","slovenia","liechtenstein","germany"],
    "alpine": ["switzerland","austria","france","italy","slovenia","liechtenstein"],
    "scandinavia": ["norway","sweden","denmark"],
    "scandinavian": ["norway","sweden","denmark"],
    "nordics": ["norway","sweden","denmark","finland","iceland"],
    "nordic": ["norway","sweden","denmark","finland","iceland"],
    "lapland": ["norway","sweden","finland"],
    "balkans": ["croatia","bosnia-and-herzegovina","serbia","montenegro","north-macedonia","albania","kosovo","bulgaria","romania"],
    "baltics": ["estonia","latvia","lithuania"],
    "baltic states": ["estonia","latvia","lithuania"],
    "iberia": ["spain","portugal"],
    "iberian": ["spain","portugal"],
    "benelux": ["netherlands","belgium","luxembourg"],
    "low countries": ["netherlands","belgium","luxembourg"],
    "british isles": ["united-kingdom","ireland"],
    "adriatic": ["croatia","montenegro","slovenia","italy","albania"],
    "aegean": ["greece","turkiye"],
    "mediterranean": ["spain","portugal","italy","greece","malta","cyprus","croatia","france","turkiye"],
    "caucasus": ["georgia","armenia","azerbaijan"],
    "pyrenees": ["france","spain","andorra"],
    "carpathians": ["romania","slovakia","poland","ukraine"],
    "dolomites": ["italy"],
    "central europe": ["germany","austria","czechia","poland","slovakia","hungary","slovenia","switzerland"],
    "eastern europe": ["poland","czechia","slovakia","hungary","romania","bulgaria","moldova"],
    "western europe": ["france","netherlands","belgium","luxembourg","monaco"],
    "southern europe": ["spain","portugal","italy","greece","malta","cyprus"],
    "northern europe": ["norway","sweden","denmark","finland","iceland","estonia","latvia","lithuania"]
  };

  var MONTHS = {
    jan:["january","jan"], feb:["february","feb"], mar:["march","mar"], apr:["april","apr"],
    may:["may"], jun:["june","jun"], jul:["july","jul"], aug:["august","aug"],
    sep:["september","sept","sep"], oct:["october","oct"], nov:["november","nov"], dec:["december","dec"]
  };
  var SEASONS = { summer:"jul", winter:"jan", spring:"apr", autumn:"oct", fall:"oct" };

  // Things people reasonably ask for that this planner cannot express. Named
  // rather than silently dropped — a plan that ignores a wheelchair is worse
  // than a plan that says it could not take account of one.
  var CANT = [
    [["wheelchair","step-free","step free","accessible","accessibility","mobility"], "accessibility needs"],
    [["vegan","vegetarian","halal","kosher","gluten","allerg*"], "dietary requirements"],
    [["dog","cat","pet","pets"], "travelling with an animal"],
    [["kid","kids","child","children","toddler","baby","family-friendly"], "travelling with children"],
    [["visa","passport","schengen days","border control"], "visa and entry questions"],
    [["book","booking","reserve","flight","flights","hotel room","car hire","rental car"], "booking anything"],
    [["weather","rain","forecast","temperature"], "a weather forecast"],
    [["cheapest flight","cheap flights","budget airline"], "flight prices"],
    [["business trip","conference","work trip"], "business travel"],
    [["honeymoon","anniversary","birthday","proposal"], "the occasion behind a trip"]
  ];

  function words(t) { return " " + fold(t).replace(/[^a-z0-9€$£.,\-]+/g, " ") + " "; }

  var HAS = {};
  function has(t, term) {
    // "by train" matched the weather keyword "rain" until this existed.
    // A trailing * is a deliberate stem; anything else must be a whole word.
    var key = term;
    if (!HAS[key]) {
      HAS[key] = term.slice(-1) === "*"
        ? new RegExp("\\b" + term.slice(0, -1).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
        : new RegExp("\\b" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b");
    }
    return HAS[key].test(t);
  }

  function parseAsk(text, cities) {
    var t = words(text);
    var got = { days: null, budget: null, month: null, interests: [], start: null,
                style: null, pace: null, travellers: null, cant: [] };

    // Days. Numerals, spelled-out numbers, and the words for a week.
    var m = t.match(/(\d+)\s*[- ]?\s*(day|days|night|nights)/);
    if (m) got.days = parseInt(m[1], 10) + (/night/.test(m[2]) ? 1 : 0);
    if (!got.days) {
      var spelled = { one:1, two:2, three:3, four:4, five:5, six:6, seven:7, eight:8,
                      nine:9, ten:10, eleven:11, twelve:12, fourteen:14, twenty:20 };
      var sm = t.match(/\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fourteen|twenty)\s+(day|days|week|weeks)/);
      if (sm) got.days = spelled[sm[1]] * (/week/.test(sm[2]) ? 7 : 1);
    }
    if (!got.days) {
      var wm = t.match(/(\d+)\s*(week|weeks)/);
      if (wm) got.days = parseInt(wm[1], 10) * 7;
      else if (/\bfortnight\b/.test(t)) got.days = 14;
      else if (/\ba week\b/.test(t)) got.days = 7;
      else if (/\blong weekend\b/.test(t)) got.days = 4;
      else if (/\bweekend\b/.test(t)) got.days = 3;
      else if (/\ba month\b/.test(t)) got.days = 30;
    }

    // Budget. A currency symbol or the word, and thousands written as 2.5k.
    var bm = t.match(/[€$£]\s*([\d.,]+)\s*(k\b)?/) ||
             t.match(/([\d.,]+)\s*(k\b)?\s*(euro|euros|eur|pounds|dollars|budget)/);
    if (bm) {
      var raw = bm[1].replace(/,/g, "");
      var v = parseFloat(raw);
      if (bm[2] === "k" || /\bk\b/.test(bm[0])) v *= 1000;
      else if (raw.indexOf(".") >= 0 && v < 100) v *= 1000;   // "2.5" means 2,500
      if (v >= 100) {
        got.budget = Math.round(v);
        var sym = (bm[0].match(/[£$]/) || [])[0];
        if (sym) got.currencyNote = sym;   // shown, never silently converted
      }
    }

    for (var k in MONTHS) {
      for (var i = 0; i < MONTHS[k].length; i++) {
        if (has(t, MONTHS[k][i])) { got.month = k; break; }
      }
      if (got.month) break;
    }
    if (!got.month) {
      for (var sname in SEASONS) if (has(t, sname)) { got.month = SEASONS[sname]; break; }
    }

    for (var slug in WORDS) {
      for (var w = 0; w < WORDS[slug].length; w++) {
        if (has(t, WORDS[slug][w])) { got.interests.push(slug); break; }
      }
    }

    // Starting point. Longest city name first, so "saint petersburg" is not
    // eaten by "bath". Only counts when the sentence says start or from.
    var byLength = cities.slice().sort(function (a, b) { return b.name.length - a.name.length; });
    for (var c = 0; c < byLength.length; c++) {
      var name = words(byLength[c].name.split(" (")[0]).trim();
      if (name.length < 4) continue;
      var at = t.indexOf(" " + name);
      if (at < 0) continue;
      var before = t.slice(Math.max(0, at - 24), at);
      if (/\b(start|starting|from|begin|beginning|leaving|depart|departing)\b/.test(before)) {
        got.start = byLength[c]; break;
      }
      if (!got.start) got.start = byLength[c];      // mentioned, not anchored
    }

    if (/\b(comfortable|mid-range|midrange|moderate|reasonable|middling)\b/.test(t)) got.style = "moderate";
    else if (/\b(luxur|five star|5 star|splash|no expense|treat ourselves|generous)/.test(t)) got.style = "high";
    else if (/\b(cheap|frugal|shoestring|backpack|hostel|as cheaply)|on a budget|tight budget|small budget/.test(t)) got.style = "low";

    if (/\b(slow|slowly|relaxed|unhurried|take our time|one place|few places)/.test(t)) got.pace = "slow";
    else if (/\b(fast|as much as possible|whistle|pack in|cram|see everything|lots of places)/.test(t)) got.pace = "fast";

    var tm = t.match(/(\d+)\s*(people|adults|travellers|travelers|of us)/) ||
             t.match(/\b(two|three|four|five)\s*(people|adults|of us)/);
    if (tm) got.travellers = tm[1];
    else if (/\b(a couple|my partner|my wife|my husband|the two of us)\b/.test(t)) got.travellers = "2";

    // Geography: named groups first, then any country by its own name.
    var geo = {};
    for (var g in GEO) {
      if (has(t, g)) for (var gi = 0; gi < GEO[g].length; gi++) geo[GEO[g][gi]] = true;
    }
    var seenCountry = {};
    for (var ck = 0; ck < cities.length; ck++) {
      var cn = words(cities[ck].country).trim();
      if (seenCountry[cn]) continue;
      seenCountry[cn] = true;
      if (has(t, cn)) geo[cities[ck].countrySlug] = true;
    }
    got.geo = Object.keys(geo);
    // A start city inside the named geography is not a contradiction; a
    // start city outside it is, and the geography wins because it is the
    // bigger statement.
    if (got.geo.length && got.start && got.geo.indexOf(got.start.countrySlug) < 0) {
      got.startIgnored = got.start.name;
      got.start = null;
    }

    for (var ci = 0; ci < CANT.length; ci++) {
      for (var cj = 0; cj < CANT[ci][0].length; cj++) {
        if (has(t, CANT[ci][0][cj])) { got.cant.push(CANT[ci][1]); break; }
      }
    }
    return got;
  }

  function interestName(slug) {
    for (var i = 0; i < ATLAS.interests.length; i++) {
      if (ATLAS.interests[i].slug === slug) return ATLAS.interests[i].name.toLowerCase();
    }
    return slug;
  }

  function applyAsk(got) {
    if (got.days) form.days.value = Math.max(3, Math.min(45, got.days));
    if (got.budget) form.budget.value = got.budget;
    if (got.month) form.month.value = got.month;
    if (got.style) form.style.value = got.style;
    if (got.pace) form.pace.value = got.pace;
    if (got.start) startSel.value = got.start.id;
    if (got.interests.length) {
      var boxes = form.querySelectorAll('input[name="interest"]');
      for (var i = 0; i < boxes.length; i++) {
        boxes[i].checked = got.interests.indexOf(boxes[i].value) >= 0;
      }
    }
  }

  function readbackHtml(got) {
    var read = [];
    if (got.days) read.push("<strong>" + got.days + " days</strong>");
    if (got.budget) read.push("<strong>" + euro(got.budget) + "</strong>");
    if (got.travellers) read.push("for <strong>" + got.travellers + "</strong>");
    if (got.month) read.push("in <strong>" + ATLAS.monthNames[got.month] + "</strong>");
    if (got.start) read.push("starting in <strong>" + got.start.name + "</strong>");
    if (got.style) read.push("<strong>" + got.style + "</strong> spending");
    if (got.pace) read.push("a <strong>" + got.pace + "</strong> pace");
    if (got.interests.length) {
      read.push("interested in <strong>" + got.interests.map(interestName).join(", ") + "</strong>");
    }
    if (got.geo && got.geo.length) {
      var names = {};
      for (var gi = 0; gi < ATLAS.cities.length; gi++) {
        if (got.geo.indexOf(ATLAS.cities[gi].countrySlug) >= 0) names[ATLAS.cities[gi].country] = true;
      }
      var list = Object.keys(names);
      read.push("within <strong>" + (list.length > 4
        ? list.length + " countries: " + list.join(", ")
        : list.join(", ")) + "</strong>");
    }

    var html = '<div class="note"><h3>I read that as</h3>';
    html += read.length
      ? "<p>" + read.join(", ") + ". Everything below is filled in from it — change anything and rebuild.</p>"
      : "<p>Nothing I could use, so the form below is unchanged. Try naming a number of days, " +
        "a budget, a month, or what you like — history, mountains, food.</p>";
    if (got.currencyNote) {
      html += "<p>You wrote <strong>" + got.currencyNote + "</strong>. Every estimate here is in " +
        "euros and no conversion has been applied — the number was taken as it stands, so treat " +
        "the total as approximate in your own currency.</p>";
    }
    if (got.startIgnored) {
      html += "<p><strong>" + got.startIgnored + "</strong> is outside the area you named, so " +
        "the region won and the start did not. Pick a start below if that was the wrong way round.</p>";
    }
    if (got.cant.length) {
      var uniq = got.cant.filter(function (v, i, a) { return a.indexOf(v) === i; });
      html += "<p><strong>What this planner cannot take account of:</strong> " +
        uniq.join(", ") + ". It plans places, nights and rough cost, and nothing else — " +
        "so check those separately rather than assuming the route allows for them.</p>";
    }
    html += '<p class="small">Read by rules in your browser, not by a model, and not sent ' +
      "anywhere. That is why it can show you exactly what it understood.</p></div>";
    return html;
  }

  /* A plan has to survive being closed. The route is encoded into the URL —
   * not re-planned from the inputs, because the planner deliberately jitters
   * and would return something slightly different — so a shared link is the
   * same itinerary, and My Europe stores nothing but that link. */
  function planUrl(route, opts) {
    var q = new URLSearchParams();
    q.set("d", opts.days); q.set("b", opts.budget); q.set("m", opts.month);
    q.set("s", opts.style); q.set("p", opts.pace);
    if (opts.wants.length) q.set("i", opts.wants.join(","));
    q.set("r", route.map(function (st) { return st.city.id + ":" + st.nights; }).join("|"));
    return location.origin + "/plan?" + q.toString();
  }

  function routeFromParams(q) {
    var raw = q.get("r");
    if (!raw) return null;
    var byId = {};
    for (var i = 0; i < ATLAS.cities.length; i++) byId[ATLAS.cities[i].id] = ATLAS.cities[i];
    var out = [];
    raw.split("|").forEach(function (part) {
      var bits = part.split(":");
      var city = byId[bits[0]];
      if (city) out.push({ city: city, nights: parseInt(bits[1], 10) || 1 });
    });
    return out.length ? out : null;
  }

  /* Scoped to the container the plan was drawn into: getElementById would
   * find the first #saveplan on the page, which is the wrong one whenever a
   * rejected plan is open in its own details block below a good one. */
  function wireSaveAndShare(route, opts, out) {
    var scope = out || document;
    var url = planUrl(route, opts);
    var state = scope.querySelector("#planstate");
    var save = scope.querySelector("#saveplan");
    var share = scope.querySelector("#shareplan");
    if (!save || !share) return;

    var label = opts.days + " days: " + route.map(function (s) { return s.city.name; }).join(" → ");
    save.addEventListener("click", function () {
      var KEY = "europedoor.saved.v1";
      var list;
      try { list = JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { list = []; }
      var id = "itinerary:" + route.map(function (s) { return s.city.id; }).join("|");
      if (!list.some(function (x) { return x.id === id; })) {
        list.push({ id: id, kind: "Itinerary", label: label, url: url.replace(location.origin, "") });
      }
      try {
        localStorage.setItem(KEY, JSON.stringify(list));
        state.innerHTML = 'Saved. It is in <a href="/my-europe">My Europe</a>, in this browser ' +
          "only — there is no account and nothing was sent anywhere.";
      } catch (e) {
        state.textContent = "This browser will not let us save.";
      }
    });

    share.addEventListener("click", function () {
      history.replaceState(null, "", url.replace(location.origin, ""));
      function done() {
        state.textContent = "Link copied, and it is in the address bar. It carries the route " +
          "itself, so whoever opens it sees this itinerary rather than a new one.";
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, function () {
          state.textContent = "Copy it from the address bar — it now holds this itinerary.";
        });
      } else {
        state.textContent = "Copy it from the address bar — it now holds this itinerary.";
      }
    });
  }

  function readForm() {
    var wants = [];
    var boxes = form.querySelectorAll('input[name="interest"]:checked');
    for (var i = 0; i < boxes.length; i++) wants.push(boxes[i].value);
    return {
      days: Math.max(3, Math.min(45, parseInt(form.days.value, 10) || 12)),
      budget: Math.max(200, parseInt(form.budget.value, 10) || 2500),
      month: form.month.value,
      style: form.style.value,
      pace: form.pace.value,
      start: form.start.value,
      end: form.end.value,
      travellers: Math.max(1, Math.min(12, parseInt(form.travellers.value, 10) || 1)),
      accommodation: form.accommodation.value,
      transport: form.transport.value,
      currency: form.currency.value,
      useSaved: form.saved.checked,
      wants: wants,
      geo: currentGeo
    };
  }

  function fillStarts() {
    var list = ATLAS.cities.slice().sort(function (a, b) {
      return a.country === b.country ? a.name.localeCompare(b.name) : a.country.localeCompare(b.country);
    });
    var html = '<option value="">Anywhere that fits</option>';
    for (var i = 0; i < list.length; i++) {
      html += '<option value="' + list[i].id + '">' + list[i].name + ", " + list[i].country + "</option>";
    }
    startSel.innerHTML = html;
    var endSel = document.getElementById("end");
    if (endSel) {
      endSel.innerHTML = html.replace(">Anywhere that fits<", ">Wherever it gets to<");
    }
  }

  function applyUrlState() {
    var q = new URLSearchParams(location.search);
    if (q.get("from")) startSel.value = q.get("from");
    if (q.get("d")) form.days.value = q.get("d");
    if (q.get("b")) form.budget.value = q.get("b");
    if (q.get("m")) form.month.value = q.get("m");
    if (q.get("s")) form.style.value = q.get("s");
    if (q.get("p")) form.pace.value = q.get("p");
    if (q.get("i")) {
      var want = q.get("i").split(",");
      var boxes = form.querySelectorAll('input[name="interest"]');
      for (var k = 0; k < boxes.length; k++) boxes[k].checked = want.indexOf(boxes[k].value) >= 0;
    }
    // The homepage asks the question; this page answers it. Arriving with
    // ?ask= fills the box and runs it, so the two are one interaction.
    var asked = q.get("ask");
    if (asked) {
      var askBox = document.getElementById("ask");
      if (askBox) {
        askBox.value = asked;
        setTimeout(function () { goFromSentence(); }, 0);
        return;
      }
    }

    var shared = routeFromParams(q);
    if (shared) {
      var opts = readForm();
      render(shared, opts);
      result.insertAdjacentHTML("afterbegin",
        '<div class="note"><h3>This is somebody\'s saved itinerary</h3><p>It came from the link ' +
        "you opened rather than from the planner, so it is exactly what they had. Change anything " +
        "below and press build to make it yours.</p></div>");
      return;
    }
    var hash = location.hash.replace(/^#/, "");
    var m = /^journey=(.+)$/.exec(hash);
    if (m) {
      for (var i = 0; i < ATLAS.journeys.length; i++) {
        var j = ATLAS.journeys[i];
        if (j.slug !== m[1]) continue;
        form.days.value = j.days;
        startSel.value = j.legs[0].id;
        var boxes = form.querySelectorAll('input[name="interest"]');
        for (var k = 0; k < boxes.length; k++) {
          boxes[k].checked = j.interests.indexOf(boxes[k].value) >= 0;
        }
        result.innerHTML = '<div class="note"><p>Loaded <strong>' + j.name +
          "</strong>. Change anything below and rebuild — the planner will keep what matches " +
          "you and drop the rest.</p></div>";
        break;
      }
    }
    var now = new Date().getMonth();
    if (!q.get("month")) form.month.value = ATLAS.months[now];
  }

  function go(e) {
    if (e) e.preventDefault();
    EDITED = null;
    currentGeo = [];
    var opts = readForm();
    // Submitting the form is stating the budget: the number is on screen in
    // a field the reader just used.
    opts.budgetStated = true;
    stage(2);
    var route = plan(opts);
    stage(4);
    render(route, opts);
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* The specification says the planner should ask only the necessary
   * follow-up questions. Two things change the answer enough to be worth
   * asking about: how long you have, and what you can spend. If the
   * sentence did not say, the plan is still built — an empty screen is a
   * worse answer than a provisional one — but the question is put, above
   * the result, with the field it fills. */
  function followUps(got) {
    var asks = [];
    if (!got.days) asks.push(["days", "How many days do you have?",
      "Built on " + form.days.value + " for now."]);
    if (!got.budget) asks.push(["budget", "Roughly what can you spend, per person?",
      "Built on " + euro(form.budget.value) + " for now."]);
    if (!got.month && !got.geo.length) asks.push(["month", "Which month?",
      "Built on " + ATLAS.monthNames[form.month.value] + " for now."]);
    if (!asks.length) return "";
    return '<div class="note"><h2 class="mini">' +
      (asks.length === 1 ? "One thing would change this" : asks.length + " things would change this") +
      "</h2><ul>" + asks.map(function (a) {
        return "<li><strong>" + a[1] + "</strong> " + a[2] +
          ' <a href="#' + a[0] + '" data-focus="' + a[0] + '">set it →</a></li>';
      }).join("") + "</ul></div>";
  }

  function goFromSentence(e) {
    if (e) e.preventDefault();
    var text = document.getElementById("ask").value;
    if (!text.trim()) { go(); return; }
    stage(1);
    var got = parseAsk(text, ATLAS.cities);
    applyAsk(got);
    currentGeo = got.geo || [];
    var opts = readForm();
    opts.budgetStated = !!got.budget;
    stage(2);
    var route = plan(opts);
    stage(4);
    render(route, opts);
    result.insertAdjacentHTML("afterbegin", readbackHtml(got) + followUps(got));
    result.querySelectorAll("[data-focus]").forEach(function (a) {
      a.addEventListener("click", function (ev) {
        ev.preventDefault();
        var f = document.getElementById(a.getAttribute("data-focus"));
        if (f) { f.scrollIntoView({ behavior: "smooth", block: "center" }); f.focus(); }
      });
    });
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* The staged wait, from the UI specification: never a bare "Loading…".
   *
   * The steps are real. Each one is ticked when the work it names has
   * actually finished, so this is a progress report rather than a stalling
   * animation — the difference matters the day something is slow, because a
   * fake sequence stops at a step that already completed and tells the
   * reader nothing about where it stuck.
   *
   * The planner itself runs in single-digit milliseconds, so the honest
   * thing on a fast connection is for this to be gone before it is read.
   * There is no minimum display time: padding a wait to show off the
   * animation is exactly the trick this is supposed to replace.
   */
  var STEPS = [
    "Loading the Atlas",
    "Understanding what you asked for",
    "Scoring every destination",
    "Building the route",
    "Estimating what it costs",
  ];

  function stage(done, failedAt) {
    var html = '<div class="note staged" role="status"><h2 class="mini">Building your journey</h2><ul class="stages">';
    for (var i = 0; i < STEPS.length; i++) {
      var mark = i < done ? "done" : (i === done ? "now" : "todo");
      if (failedAt === i) mark = "failed";
      var glyph = mark === "done" ? "✓" : mark === "failed" ? "✕" : mark === "now" ? "●" : "○";
      html += '<li class="' + mark + '"><span aria-hidden="true">' + glyph + "</span> " +
              STEPS[i] + (mark === "failed" ? " — this is where it stopped" : "") + "</li>";
    }
    result.innerHTML = html + "</ul></div>";
  }

  stage(0);

  fetch("/api/atlas.json")
    .then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    })
    .then(function (json) {
      ATLAS = json;
      stage(1);
      fillStarts();
      applyUrlState();
      form.addEventListener("submit", go);
      document.getElementById("again").addEventListener("click", function () { rand(); go(); });
      var askform = document.getElementById("askform");
      if (askform) {
        askform.addEventListener("submit", goFromSentence);
        document.getElementById("ask").addEventListener("keydown", function (ev) {
          if (ev.key === "Enter" && (ev.metaKey || ev.ctrlKey)) goFromSentence(ev);
        });
      }
    })
    .catch(function () {
      /* Name the step it died on rather than replacing everything with a
       * generic apology: "the index did not load" is a different problem
       * from "the planner crashed", and the reader can tell which from
       * this. */
      stage(0, 0);
      result.insertAdjacentHTML("beforeend",
        '<div class="note warn"><p>The Atlas index did not load, so the planner ' +
        'cannot run. That is our end, not yours — reloading often fixes it. ' +
        '<a href="/countries">Browse the Atlas directly</a> in the meantime.</p></div>');
    });
})();
