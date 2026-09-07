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
    // Beds and meals are roughly four fifths of a trip's cost once transport
    // and a buffer are taken out. This is what the traveller can actually
    // spend per day, and it is a ceiling, not a target: coming in under
    // budget is a good outcome and is never penalised.
    return (opts.budget * 0.78) / Math.max(1, opts.days);
  }

  function fitScore(city, wants, month, style, ceiling) {
    var matched = 0, i;
    for (i = 0; i < wants.length; i++) {
      if (city.interests.indexOf(wants[i]) >= 0) matched++;
    }
    var interest = wants.length ? matched / wants.length : 0.5;
    var base = 0.30 + 0.70 * interest;
    // A generous budget stops caring what a place costs; a frugal one does.
    var costPenalty = 1;
    if (style === "low" && city.budget === "high") costPenalty = 0.72;
    if (style === "low" && city.budget === "moderate") costPenalty = 0.92;
    if (style === "high" && city.budget === "low") costPenalty = 0.96;
    // Somewhere with listed experiences has more to actually do.
    var depth = 1 + Math.min(city.exp, 3) * 0.035;
    // Affordability. Somewhere you cannot afford is not a recommendation,
    // so a city whose daily rate is above the ceiling is damped in
    // proportion to how far above. Being cheaper than the ceiling is free.
    var afford = 1;
    if (ceiling > 0) {
      var rate = dailyRate(city, style);
      if (rate > ceiling) afford = Math.max(0.25, Math.pow(ceiling / rate, 1.4));
    }
    return base * seasonFactor(city, month) * costPenalty * depth * afford;
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
    var ceiling = impliedDaily(opts);
    var scored = cities.map(function (c) {
      return { c: c, s: fitScore(c, opts.wants, opts.month, opts.style, ceiling) };
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
      remaining -= n;
      if (remaining <= 0) break;

      var best = null, bestV = -1;
      for (var j = 0; j < scored.length; j++) {
        var cand = scored[j].c;
        if (used[cand.id]) continue;
        var d = km(current, cand);
        if (d < 25) continue;                       // effectively the same place
        // Distance is a cost, not a veto. 250 km is nearly free; 1,500 km
        // has to be earned by a much better fit.
        var travel = 1 / (1 + Math.pow(d / 420, 1.55));
        var repeat = (perCountry[cand.countrySlug] || 0) >= 3 ? 0.72 : 1;
        var v = scored[j].s * travel * repeat * (0.93 + rand() * 0.14);
        if (v > bestV) { bestV = v; best = cand; }
      }
      if (!best) break;
      current = best;
    }
    return route;
  }

  function costing(route, opts) {
    var stay = 0, transport = 0, i, d;
    for (i = 0; i < route.length; i++) {
      stay += route[i].nights * dailyRate(route[i].city, opts.style);
    }
    for (i = 1; i < route.length; i++) {
      d = km(route[i - 1].city, route[i].city);
      transport += transportCost(d);
    }
    var buffer = Math.round((stay + transport) * 0.12);
    return { stay: stay, transport: transport, buffer: buffer, total: stay + transport + buffer };
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

  function render(route, opts) {
    if (!route.length) {
      result.innerHTML = '<div class="note warn"><p>Nothing in the Atlas fits that yet. Try more days, or fewer interests at once.</p></div>';
      return;
    }
    var c = costing(route, opts);
    var day = 1, legs = "", i, hop, countries = [];
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
      legs += '<li class="leg"><div class="leg-when">' + when + '</div><div>' +
              '<h3><a href="' + city.url + '">' + city.name + "</a> <span class=\"small\">· " +
              city.country + " · " + city.region + "</span></h3>" +
              "<p>" + city.why + "</p>" +
              '<p class="small" style="margin-top:.4rem">' + whyLine(city, opts.wants) +
              " " + euro(dailyRate(city, opts.style)) + " a day here." + "</p>" + hop +
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
        "<div><dt>Beds &amp; meals</dt><dd>" + euro(c.stay) + "</dd></div>" +
        "<div><dt>Getting between</dt><dd>" + euro(c.transport) + "</dd></div>" +
        "<div><dt>12% buffer</dt><dd>" + euro(c.buffer) + "</dd></div>" +
        "<div><dt>Ground covered</dt><dd>" + totalKm.toLocaleString("en-GB") + " km</dd></div>" +
      "</dl>" +
      verdict +
      '<ul class="legs">' + legs + "</ul>" +
      '<p class="small">Estimates are planning arithmetic from published daily bands and ' +
      'straight-line distances — not quotes. <a href="/sources">How these numbers are made</a>.</p>';
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
      wants: wants
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
    var opts = readForm();
    render(plan(opts), opts);
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
    })
    .catch(function () {
      result.innerHTML = '<div class="note warn"><p>The Atlas index did not load, so the planner ' +
        'cannot run. <a href="/atlas">Browse the Atlas directly</a>.</p></div>';
    });
})();
