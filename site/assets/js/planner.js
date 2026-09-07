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

  function hopNote(d) {
    if (d < 90) return d + " km — a local train or a short drive";
    if (d < 400) return d + " km — a comfortable train leg, half a day at most";
    if (d < 900) return d + " km — a long rail day, or a short flight if the days are tight";
    return d + " km — fly, or give the overland crossing a day of its own";
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

  function plan(opts) {
    var cities = ATLAS.cities.slice();
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
      return { c: c, s: fitScore(c, opts.wants, opts.month, opts.style, ceiling, context) };
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
        var repeat = (perCountry[cand.countrySlug] || 0) >= 3 ? 0.72 : 1;
        var diverse = 1;
        if (bigRun >= 2) {
          var isBig = cand.interests.indexOf("cities") >= 0 && !cand.quiet;
          diverse = isBig ? 0.78 : 1.18;
        }
        var v = scored[j].s * travel * repeat * diverse * (0.93 + rand() * 0.14);
        if (v > bestV) { bestV = v; best = cand; }
      }
      if (!best) break;
      current = best;
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
      beds += route[i].nights * rate * 0.6;
      food += route[i].nights * rate * 0.4;
      nights += route[i].nights;
    }
    for (i = 1; i < route.length; i++) {
      d = km(route[i - 1].city, route[i].city);
      transport += transportCost(d);
    }
    var activities = ACTIVITY_PER_DAY[opts.style] * (nights + 1);
    beds = Math.round(beds); food = Math.round(food);
    var subtotal = beds + food + transport + activities;
    var buffer = Math.round(subtotal * 0.12);
    return { beds: beds, food: food, transport: transport, activities: activities,
             buffer: buffer, stay: beds + food, total: subtotal + buffer };
  }

  function euro(n) { return "€" + n.toLocaleString("en-GB"); }

  function whyLine(city, wants) {
    var hits = wants.filter(function (w) { return city.interests.indexOf(w) >= 0; });
    var names = hits.map(function (h) {
      for (var i = 0; i < ATLAS.interests.length; i++) {
        if (ATLAS.interests[i].slug === h) return ATLAS.interests[i].name.toLowerCase();
      }
      return h;
    });
    if (!names.length) return "Chosen for the shape of the route rather than your interests — it sits between two places that did match.";
    return "Matches " + names.join(", ") + ".";
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

  function render(route, opts) {
    if (!route.length) {
      result.innerHTML = '<div class="note warn"><p>Nothing in the Atlas fits that yet. Try more days, or fewer interests at once.</p></div>';
      return;
    }
    var c = costing(route, opts);
    var day = 1, legs = "", i, hop, countries = [];
    var scoredAll = window.__EPD_SCORED || [];
    var usedAll = window.__EPD_USED || {};
    for (i = 0; i < route.length; i++) {
      var st = route[i], city = st.city;
      if (countries.indexOf(city.country) < 0) countries.push(city.country);
      hop = "";
      if (i > 0) {
        hop = '<p class="hop">↳ ' + hopNote(km(route[i - 1].city, city)) +
              " from " + route[i - 1].city.name + "</p>";
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
      var alts = (i === 0 && opts.start) ? [] : alternativesFor(scoredAll, route, i, usedAll);
      var altHtml = alts.length
        ? '<p class="small alt">Instead of ' + city.name + ": " + alts.map(function (a) {
            return '<a href="' + a.city.url + '">' + a.city.name + "</a> (" + a.km + " km)";
          }).join(", ") + ". The planner ranked them just behind.</p>"
        : "";

      legs += '<li class="leg"><div class="leg-when">' + when + '</div><div>' +
              '<h3><a href="' + city.url + '">' + city.name + "</a> <span class=\"small\">· " +
              city.country + " · " + city.region + "</span></h3>" +
              "<p>" + city.why + "</p>" +
              '<p class="small" style="margin-top:.4rem">' + whyLine(city, opts.wants) +
              " " + euro(dailyRate(city, opts.style)) + " a day here." + "</p>" +
              '<ul class="daylist">' + dayHtml + "</ul>" + altHtml + hop +
              "</div></li>";
      day = last + 1;
    }

    var over = c.total - opts.budget;
    var verdict;
    if (over <= 0) {
      verdict = '<div class="note"><p><strong>' + euro(-over) + " under budget.</strong> " +
        "Room for a better hotel in one place, or a day longer.</p></div>";
    } else {
      verdict = '<div class="note warn"><p><strong>' + euro(over) + " over budget.</strong> " +
        "Drop the spending style a level, cut the longest hop, or take one night off the most " +
        "expensive stop — the planner will not quietly downgrade the trip for you.</p></div>";
    }

    var totalKm = 0;
    for (i = 1; i < route.length; i++) totalKm += km(route[i - 1].city, route[i].city);

    result.innerHTML =
      '<h2 style="margin-top:var(--s7)">' + opts.days + " days, " + route.length +
        " stops, " + countries.length + (countries.length === 1 ? " country" : " countries") + "</h2>" +
      '<dl class="result-summary">' +
        "<div><dt>Estimated total</dt><dd>" + euro(c.total) + "</dd></div>" +
        "<div><dt>Accommodation</dt><dd>" + euro(c.beds) + "</dd></div>" +
        "<div><dt>Food</dt><dd>" + euro(c.food) + "</dd></div>" +
        "<div><dt>Transport</dt><dd>" + euro(c.transport) + "</dd></div>" +
        "<div><dt>Activities</dt><dd>" + euro(c.activities) + "</dd></div>" +
        "<div><dt>12% buffer</dt><dd>" + euro(c.buffer) + "</dd></div>" +
        "<div><dt>Ground covered</dt><dd>" + totalKm.toLocaleString("en-GB") + " km</dd></div>" +
      "</dl>" +
      verdict +
      '<ul class="legs">' + legs + "</ul>" +
      '<div class="hero-actions" style="margin-top:0">' +
        '<button class="btn ghost" type="button" id="saveplan">Save this to My Europe</button>' +
        '<button class="btn ghost" type="button" id="shareplan">Copy a link to it</button>' +
      "</div>" +
      '<p class="small" id="planstate"></p>' +
      '<p class="small">Estimates are planning arithmetic from published daily bands and ' +
      'straight-line distances — not quotes. Activities are estimated at ' +
      euro(ACTIVITY_PER_DAY[opts.style]) + ' a day for this spending style. ' +
      '<a href="/sources">How these numbers are made</a>.</p>';

    wireSaveAndShare(route, opts);
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

  function words(t) { return " " + t.toLowerCase().replace(/[^a-z0-9€$£.,\-]+/g, " ") + " "; }

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
      var name = byLength[c].name.toLowerCase().split(" (")[0];
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
      var cn = cities[ck].country.toLowerCase();
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

  function wireSaveAndShare(route, opts) {
    var url = planUrl(route, opts);
    var state = document.getElementById("planstate");
    var save = document.getElementById("saveplan");
    var share = document.getElementById("shareplan");
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
    currentGeo = [];
    var opts = readForm();
    render(plan(opts), opts);
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function goFromSentence(e) {
    if (e) e.preventDefault();
    var text = document.getElementById("ask").value;
    if (!text.trim()) { go(); return; }
    var got = parseAsk(text, ATLAS.cities);
    applyAsk(got);
    currentGeo = got.geo || [];
    var opts = readForm();
    var route = plan(opts);
    render(route, opts);
    result.insertAdjacentHTML("afterbegin", readbackHtml(got));
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  fetch("/api/atlas.json")
    .then(function (r) { return r.json(); })
    .then(function (json) {
      ATLAS = json;
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
      result.innerHTML = '<div class="note warn"><p>The Atlas index did not load, so the planner ' +
        'cannot run. <a href="/atlas">Browse the Atlas directly</a>.</p></div>';
    });
})();
