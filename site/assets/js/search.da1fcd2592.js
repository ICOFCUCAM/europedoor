/* Search, entirely in the browser.
 *
 * The whole index is a few hundred kilobytes and is fetched once. That is
 * cheaper than running a search service, it works offline after the first
 * load, and — the reason that actually decided it — nothing anybody types
 * into the box leaves their machine.
 *
 * Ranking is deliberately simple and explainable: an exact name match beats
 * a name prefix, which beats a name substring, which beats a body match.
 * Kind weight breaks ties, so a country outranks an experience of the same
 * name. Nobody can buy a position; there is no field that could carry one.
 */

(function () {
  "use strict";

  var ROWS = null, INDEX = null, COUNTS = { countries: 0, cities: 0 };

  /* The specification asks search to understand more than a word: an intent
   * ("romantic places"), a budget ("cheap European destinations"), a season
   * ("quiet beaches in September") and a proximity ("castles near Prague").
   *
   * None of that needs a language model or a search service. It needs the
   * query read for modifiers, the modifiers applied as filters, and — the
   * part most search boxes skip — the interpretation shown back, so a wrong
   * guess is visible rather than mysterious.
   */
  var MODIFIER_INTENT = {
    romantic: ["coast", "islands", "wine", "architecture"],
    family: ["nature", "coast", "history"],
    adventurous: ["mountains", "winter", "nature"],
    adventure: ["mountains", "winter", "nature"],
    cultural: ["art", "architecture", "history", "music"],
    culture: ["art", "architecture", "history", "music"],
    foodie: ["food", "wine"],
    scenic: ["mountains", "coast", "nature"],
    // Ordinary nouns are the ones people actually type. Mapping them to a
    // tag and REMOVING them from the search term is the difference between
    // "quiet beaches in September" returning nothing and returning beaches.
    beach: ["coast"], beaches: ["coast"], coast: ["coast"], seaside: ["coast"],
    castle: ["history"], castles: ["history"], medieval: ["history"],
    ruins: ["history"], history: ["history"], historic: ["history"],
    museum: ["art"], museums: ["art"], gallery: ["art"], galleries: ["art"], art: ["art"],
    church: ["sacred"], churches: ["sacred"], cathedral: ["sacred"], cathedrals: ["sacred"],
    monastery: ["sacred"], monasteries: ["sacred"], pilgrimage: ["sacred"], sacred: ["sacred"],
    mountain: ["mountains"], mountains: ["mountains"], hiking: ["mountains"], alps: ["mountains"],
    island: ["islands"], islands: ["islands"],
    wine: ["wine"], vineyards: ["wine"], food: ["food"], restaurants: ["food"],
    snow: ["winter"], ski: ["winter"], skiing: ["winter"], aurora: ["winter"],
    wildlife: ["wild"], nature: ["nature"], forest: ["nature"], forests: ["nature"],
    festival: ["festivals"], festivals: ["festivals"],
    train: ["rail"], trains: ["rail"], rail: ["rail"], railway: ["rail"],
    music: ["music"], nightlife: ["music"], design: ["design"],
    architecture: ["architecture"], city: ["cities"], cities: ["cities"]
  };

  // Words that carry no signal in a travel search and swallow every result
  // if they are left in the term.
  var STOP = ["place", "places", "destination", "destinations", "europe", "european",
              "spot", "spots", "somewhere", "anywhere", "best", "top", "good", "nice",
              "holiday", "holidays", "trip", "trips", "travel", "visit", "go", "to",
              "the", "in", "for", "with", "and", "a", "of", "on", "at", "some", "my",
              "i", "want", "looking", "find", "show", "me"];

  function parseQuery(q) {
    var mods = { cheap: false, quiet: false, month: null, near: null, kind: null,
                 interests: [], rest: q };
    var t = " " + q + " ";

    if (/\b(cheap|cheapest|budget|affordable|inexpensive)\b/.test(t)) {
      mods.cheap = true; t = t.replace(/\b(cheap|cheapest|budget|affordable|inexpensive)\b/g, " ");
    }
    if (/\b(quiet|quieter|uncrowded|empty|off the beaten|hidden|undiscovered)\b/.test(t)) {
      mods.quiet = true;
      t = t.replace(/\b(quiet|quieter|uncrowded|empty|off the beaten|track|hidden|undiscovered)\b/g, " ");
    }
    for (var m in INDEX.months) {
      var name = INDEX.months[m].toLowerCase();
      if (t.indexOf(" " + name) >= 0 || new RegExp("\\b" + m + "\\b").test(t)) {
        mods.month = m;
        t = t.replace(new RegExp(name + "|\\b" + m + "\\b", "g"), " ");
        break;
      }
    }
    var near = t.match(/\bnear\s+([a-zàâäçéèêëîïôöùûüÿñæœ' -]{3,30})/);
    if (near) {
      var wanted = norm(near[1].trim());
      for (var i = 0; i < ROWS.length; i++) {
        if (ROWS[i].la === undefined) continue;
        var n = norm(ROWS[i].n);
        if (n === wanted || wanted.indexOf(n) === 0) { mods.near = ROWS[i]; break; }
      }
      if (mods.near) t = t.replace(near[0], " ");
    }

    /* Kind of place, from the plural or the singular. Checked before the
     * interest map, because "mountain villages" is a kind AND an interest and
     * both should survive: mountains as the interest, village as the kind. */
    for (var kw in KIND_WORDS) {
      if (!Object.prototype.hasOwnProperty.call(KIND_WORDS, kw)) continue;
      var re = new RegExp("\\b" + kw + "s?\\b");
      if (re.test(t)) { mods.kind = kw; t = t.replace(re, " "); break; }
    }
    for (var word in MODIFIER_INTENT) {
      if (new RegExp("\\b" + word + "\\b").test(t)) {
        mods.interests = mods.interests.concat(MODIFIER_INTENT[word]);
        t = t.replace(new RegExp("\\b" + word + "\\b", "g"), " ");
      }
    }
    for (var si = 0; si < STOP.length; si++) {
      t = t.replace(new RegExp("\\b" + STOP[si] + "\\b", "g"), " ");
    }
    // De-duplicate the interests we collected.
    mods.interests = mods.interests.filter(function (v, i, a) { return a.indexOf(v) === i; });
    mods.rest = t.replace(/\s+/g, " ").trim();
    return mods;
  }

  function kmBetween(a, b) {
    var R = 6371, p1 = a.la * Math.PI / 180, p2 = b.la * Math.PI / 180;
    var dp = p2 - p1, dl = (b.lo - a.lo) * Math.PI / 180;
    var h = Math.sin(dp / 2) * Math.sin(dp / 2) +
            Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return Math.round(2 * R * Math.asin(Math.sqrt(h)));
  }
  var form = document.getElementById("searchform");
  var input = document.getElementById("q");
  var out = document.getElementById("results");

  function norm(s) {
    // Fold accents so "malmo" finds Malmö and "sighnaghi" survives a typo
    // of the diacritic rather than the letters.
    return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function scoreOne(row, q) {
    var n = norm(row.n);
    if (n === q) return 1000 * row.w;
    if (n.indexOf(q) === 0) return 500 * row.w;
    if (n.indexOf(q) >= 0) return 250 * row.w;
    var t = norm(row.t);
    var at = t.indexOf(q);
    if (at < 0) return 0;
    // Earlier in the text means more likely to be what the row is about.
    return (60 - Math.min(50, at / 20)) * row.w;
  }

  function score(row, q) {
    // Multi-word queries are an AND over the words. "medieval castles"
    // matched nothing until this existed, because no row contains that
    // exact string.
    var words = q.split(/\s+/).filter(function (w) { return w.length >= 2; });
    if (!words.length) return 0;
    var total = 0;
    for (var i = 0; i < words.length; i++) {
      var sc = scoreOne(row, words[i]);
      if (!sc) return 0;
      total += sc;
    }
    return total / words.length;
  }

  function understoodHtml(mods) {
    var chips = [];
    if (mods.cheap) chips.push("cheap: low-cost countries only");
    if (mods.quiet) chips.push("quiet: places tagged uncrowded");
    if (mods.month) chips.push("in " + INDEX.months[mods.month] + ": good that month");
    if (mods.near) chips.push("near " + mods.near.n + ": within 300 km");
    if (mods.kind) chips.push(KIND_WORDS[mods.kind] + ": destinations recorded as that");
    if (mods.interests.length) {
      var names = mods.interests.map(function (i) { return INDEX.interests[i] || i; });
      chips.push("reading that as: " + names.join(", ").toLowerCase());
    }
    var box = document.getElementById("searchunderstood");
    if (!box) return;
    box.innerHTML = chips.map(function (c) { return '<span class="chip">' + escape_(c) + "</span>"; }).join("");
  }

  var KIND_WORDS = {
    capital: "capitals", city: "cities", town: "towns", village: "villages",
    island: "islands", valley: "valleys", park: "national parks", site: "historic sites",
  };

  function passesModifiers(row, mods) {
    if (mods.cheap && row.b && row.b !== "low") return false;
    if (mods.quiet && !row.q) return false;
    if (mods.month && row.m && row.m.indexOf(mods.month) < 0) return false;
    if (mods.month && !row.m && row.k !== "City" && row.k !== "Place") return true;
    if (mods.near) {
      if (row.la === undefined) return false;
      if (kmBetween(mods.near, row) > 300) return false;
    }
    /* What kind of place. Only 157 of 319 destinations are classified, so
     * this filter deliberately keeps the unclassified ones OUT rather than
     * letting them through: a search for villages that returns everything we
     * have not got round to labelling is a search that has stopped meaning
     * anything. The empty state below says when that is what emptied it. */
    if (mods.kind && row.ct !== mods.kind) return false;
    if (mods.interests.length && row.i) {
      var hit = mods.interests.some(function (i) { return row.i.indexOf(i) >= 0; });
      if (!hit) return false;
    }
    return true;
  }

  /* THE RESTING STATE IS RENDERED BY THE BUILD AND PUT BACK, NOT REPLACED.
   * /search opened on a box and 280 pixels of nothing: it said "550 records
   * indexed" in its head and then showed a reader none of them, on the
   * instrument holding the largest index on the site. The build now renders
   * what the index is made of, by kind, with a way into each — and the first
   * version of this line threw it away on load and printed one grey sentence
   * instead. It is captured here and restored whenever the box goes empty,
   * so backspacing to nothing returns the page you arrived on. */
  var AT_REST = out.innerHTML;

  function run(qraw) {
    var q = norm(qraw.trim());
    if (q.length < 2) {
      out.innerHTML = AT_REST;
      return;
    }
    var mods = parseQuery(q);
    understoodHtml(mods);
    // mods.kind belongs in this list, and was missing from it for one build:
    // a query of "villages" parsed correctly, showed "villages: destinations
    // recorded as that" in the interpretation, and then ran no filter at all,
    // because anyMod was false and the search term was empty. A modifier that
    // is read back to the reader and not applied is worse than one that is
    // ignored outright — it tells them it worked.
    var anyMod = mods.cheap || mods.quiet || mods.month || mods.near || mods.kind ||
                 mods.interests.length;
    var term = mods.rest;

    var hits = [];
    for (var i = 0; i < ROWS.length; i++) {
      if (anyMod && !passesModifiers(ROWS[i], mods)) continue;
      var s;
      if (term.length >= 2) {
        s = score(ROWS[i], term);
      } else if (anyMod) {
        // A query that is all modifiers still has to rank. How much of what
        // you asked for a row actually carries, weighted by kind — otherwise
        // "romantic places" returns 900 rows in alphabetical order, which is
        // a database dump rather than an answer.
        var overlap = 1;
        if (mods.interests.length && ROWS[i].i) {
          // Named `matched`, not `hits`: `var hits` in here hoists and
          // shadows the results array outside it, and the page died with
          // "hits.push is not a function".
          var matched = 0;
          for (var w = 0; w < mods.interests.length; w++) {
            if (ROWS[i].i.indexOf(mods.interests[w]) >= 0) matched++;
          }
          overlap = matched / mods.interests.length;
        }
        s = ROWS[i].w * (10 + 60 * overlap) + (ROWS[i].q ? 8 : 0);
      } else {
        s = 0;
      }
      if (s > 0) hits.push({ r: ROWS[i], s: s });
    }
    hits.sort(function (a, b) { return b.s - a.s || a.r.n.localeCompare(b.r.n); });

    if (!hits.length) {
      /* Nothing found, and WHY. The old version said "nothing for that" and
       * left the reader to guess which of four constraints did it — which is
       * the same failure the planner had before it learned to refuse
       * honestly: a filter that empties a result set silently teaches people
       * that the search is broken rather than that Czechia is not a low-cost
       * country.
       *
       * So: re-run the query with each modifier dropped in turn, and report
       * the ones that would bring results back. It costs one extra pass over
       * an index that is already in memory. */
      var lifted = [];
      var names = {
        cheap: "cheap", quiet: "quiet", month: "the month",
        near: mods.near ? "near " + mods.near.n : "the place",
        kind: mods.kind ? KIND_WORDS[mods.kind] : "the kind",
        interests: "what it is for",
      };
      ["cheap", "quiet", "month", "near", "kind", "interests"].forEach(function (key) {
        var was = mods[key];
        if (!was || (key === "interests" && !was.length)) return;
        mods[key] = key === "interests" ? [] : null;
        var n = 0;
        for (var i = 0; i < ROWS.length; i++) if (passesModifiers(ROWS[i], mods)) n++;
        mods[key] = was;
        if (n > 0) lifted.push({ label: names[key], n: n });
      });
      lifted.sort(function (a, b) { return b.n - a.n; });

      var why = "";
      if (lifted.length) {
        why = "<p>Every part of that is understood; together they match nothing. " +
          "Dropping <strong>" + escape_(lifted[0].label) + "</strong> would leave " +
          lifted[0].n + (lifted[0].n === 1 ? " place" : " places") +
          (lifted.length > 1
            ? ", and dropping " + escape_(lifted[1].label) + " would leave " + lifted[1].n + "."
            : ".") + "</p>";
      }
      out.innerHTML = '<div class="note"><p>Nothing for <strong>' + escape_(qraw) +
        "</strong>.</p>" + why +
        "<p class=\"small\">The Atlas holds " + COUNTS.countries + " countries and " +
        COUNTS.cities + " destinations. A lot of Europe is not in it yet, and saying so " +
        "is better than guessing. " +
        '<a href="/countries">Browse the Atlas</a> or ' +
        '<a href="/sources">tell us what is missing</a>.</p></div>';
      return;
    }

    var shown = hits.slice(0, 40);
    var rows = shown.map(function (h) {
      return '<a class="row" href="' + h.r.u + '"><div><h3>' + escape_(h.r.n) +
        '</h3><p class="rowsub">' + escape_(h.r.s) + '</p></div>' +
        '<p class="rowmeta">' + escape_(h.r.k) + "</p></a>";
    }).join("");

    // Grouped by type, in a fixed order, so a page of results reads as an
    // answer rather than a list. Nothing here is ranked by money: there is
    // no field in the index that a payment could touch.
    var ORDER = ["Country", "Region of Europe", "Region", "City", "Place", "Experience",
                 "Journey", "Theme", "Category", "Interest", "Story", "Fund project"];
    var groups = {};
    shown.forEach(function (h) { (groups[h.r.k] = groups[h.r.k] || []).push(h); });

    // With a typed term, the group holding the best match goes first —
    // searching "bergen" and getting "Regions: Fjord Norway" above
    // "Cities: Bergen" is the kind of correctness nobody forgives. With only
    // modifiers there is no best match, so the fixed order reads better.
    var keys = Object.keys(groups);
    if (term.length >= 2) {
      keys.sort(function (a, b) { return groups[b][0].s - groups[a][0].s; });
    } else {
      keys = ORDER.concat(keys.filter(function (k) { return ORDER.indexOf(k) < 0; }));
    }
    var body = "";
    keys.forEach(function (k) {
        if (!groups[k] || !groups[k].length) return;
        /* THE PLURAL COMES FROM THE INDEX, NOT FROM AN S. Five of the twelve
           kinds this index carries do not take one, so the headings read
           "Citys", "Countrys", "Categorys", "Storys" and "Region of Europes"
           on the site's own search results. The build knows every kind it
           emits; a grammar rule guessed in the browser is checked by nothing,
           which is the same argument as the counts two functions up. */
        var heading = groups[k].length > 1
          ? ((INDEX && INDEX.kindPlural && INDEX.kindPlural[k]) || k + "s") : k;
        body += "<h3>" + escape_(heading) + "</h3>" +
          '<div class="rows">' + groups[k].map(function (h) {
            var extra = mods.near && h.r.la !== undefined
              ? kmBetween(mods.near, h.r) + " km" : escape_(h.r.k);
            return '<a class="row" href="' + h.r.u + '"><div><h3>' + escape_(h.r.n) +
              '</h3><p class="rowsub">' + escape_(h.r.s) + '</p></div>' +
              '<p class="rowmeta">' + extra + "</p></a>";
          }).join("") + "</div>";
      });

    out.innerHTML = "<h2>" + hits.length + (hits.length === 1 ? " result" : " results") +
      (hits.length > shown.length ? " — showing the first " + shown.length : "") +
      "</h2>" + body;
  }

  function escape_(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  var timer = null;
  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(function () {
      if (ROWS) run(input.value);
      var url = input.value ? "?q=" + encodeURIComponent(input.value) : location.pathname;
      history.replaceState(null, "", url);
    }, 90);
  }

  form.addEventListener("submit", function (e) { e.preventDefault(); schedule(); });
  input.addEventListener("input", schedule);

  out.innerHTML = '<p class="small">Loading the index…</p>';
  fetch("/api/search.json")
    .then(function (r) { return r.json(); })
    .then(function (j) {
      ROWS = j.rows;
      INDEX = { months: j.monthNames || j.months || {},
                interests: j.interests || {},
                kindPlural: j.kindPlural || {} };
      /* Counts from the index rather than typed into the prose. The empty
       * state used to say "50 countries and 244 cities"; the atlas had 319
       * by then, and nothing failed, because a number in a sentence is not
       * checked by anything. */
      COUNTS = { countries: j.counts ? j.counts.countries : 0,
                 cities: j.counts ? j.counts.cities : 0 };
      var q = new URLSearchParams(location.search).get("q");
      if (q) input.value = q;
      run(input.value || "");
    })
    .catch(function () {
      out.innerHTML = '<div class="note warn"><p>The search index did not load. ' +
        'The <a href="/countries">Atlas</a> is fully browsable without it.</p></div>';
    });
})();
