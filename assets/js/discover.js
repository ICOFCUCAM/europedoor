/* Discover Mode.
 *
 * The problem it solves is stated in docs/EUROPEDOOR_2036_TRANSFORMATION.md:
 * every other surface on this site requires you to already know where you
 * want to go. You pick a country, or a region, or you type a sentence into
 * the planner. None of that helps somebody who wants "mountains, history,
 * food, and not many other people" and has no idea which corner of the
 * continent that is.
 *
 * Two rules it is built around.
 *
 * EVERY RECOMMENDATION SAYS WHY. Not "recommended for you" — the actual
 * terms that fired, named, in the reader's own words back at them. A
 * recommendation you cannot interrogate is an advertisement, and the whole
 * product is arranged around not being one.
 *
 * NO NEW SCORING. It uses the same terms /method already publishes, plus the
 * discoverability score, which is also published. If this page and the
 * planner ever disagree about what "quiet" means, one of them is wrong and
 * nobody would be able to tell which.
 */
(function () {
  "use strict";
  var root = document.getElementById("discover-mode");
  if (!root) return;

  var ATLAS = null;
  var picked = {};                 // interest slug -> true
  var constraints = { month: "", budget: "", quiet: false, rail: false };

  function el(id) { return document.getElementById(id); }

  function fmt(list) {
    if (list.length === 1) return list[0];
    /* SEMICOLONS WHEN A CLAUSE ALREADY CARRIES AN "and". "Berlin also art &
     * museums and music & nightlife and is one we have written up properly"
     * is three conjunctions in one sentence, two of them joining things that
     * are not alike. The planner learned this and joined its clauses with
     * semicolons; this page joins the same kind of list and did not. */
    if (list.some(function (c) { return / and /.test(c); })) {
      return list.join("; ");
    }
    if (list.length === 2) return list[0] + " and " + list[1];
    return list.slice(0, -1).join(", ") + " and " + list[list.length - 1];
  }

  /* The score. Deliberately readable rather than clever: each term returns
   * points AND the sentence fragment that explains it, so the explanation
   * cannot drift from the arithmetic — they are produced by the same line. */
  /* The score, and the explanation, produced by the same lines so they
   * cannot drift apart.
   *
   * Clauses are sorted into two buckets and this distinction is the whole
   * design of the feature:
   *
   *   ASKED  — a restatement of a filter the reader just set. Saying
   *            "carries mountains" to somebody who ticked Mountains is
   *            telling them what they already know, and twelve cards all
   *            saying it is boilerplate, which is what a reader learns to
   *            skip.
   *   EXTRA  — everything true of this place that they did NOT ask for.
   *            This is the informative half, and it is what goes on the
   *            card.
   *
   * Never explain the constraint back. Explain what you found inside it.
   */
  function rate(city) {
    var pts = 0, asked = [], extra = [];
    var wants = Object.keys(picked);

    function nameOf(slug) {
      var m = ATLAS.interests.filter(function (i) { return i.slug === slug; })[0];
      return m ? m.name : slug;
    }

    if (wants.length) {
      var hit = wants.filter(function (w) { return city.interests.indexOf(w) >= 0; });
      if (!hit.length) return null;          // nothing you asked for: not a result
      pts += (hit.length / wants.length) * 46;
      if (hit.length === wants.length) {
        if (wants.length > 1) pts += 8;
        asked.push("carry " + fmt(wants.map(nameOf)));
      } else {
        extra.push("carries " + fmt(hit.map(nameOf)) + " but not " +
                   fmt(wants.filter(function (w) { return hit.indexOf(w) < 0; }).map(nameOf)));
      }
      // Tags beyond the ones asked for are the most useful thing a
      // recommendation can tell you: it is why you end up somewhere you
      // would not have searched for.
      var alsoTags = city.interests.filter(function (t) {
        return wants.indexOf(t) < 0 && ["sacred", "wine", "wild", "islands", "winter",
                                        "music", "design", "art", "festivals"].indexOf(t) >= 0;
      });
      if (alsoTags.length) {
        extra.push("also " + fmt(alsoTags.slice(0, 3).map(nameOf)).toLowerCase());
      }
    }

    if (constraints.month) {
      var m = constraints.month;
      if ((city.shoulder || []).indexOf(m) >= 0) {
        // Genuinely informative: they asked for a month, not for shoulder.
        pts += 20;
        extra.push("is in its quieter shoulder season then, which is usually the better time");
      } else if (city.peak.indexOf(m) >= 0) {
        pts += 16; extra.push("is at its peak then");
      } else {
        pts += 3; extra.push("is out of season then, which may be the point");
      }
    }

    if (constraints.budget) {
      if (city.budget === constraints.budget) {
        pts += 14; asked.push("sit in the spending band you chose");
      } else if (constraints.budget === "high") { pts += 6; }
      else { return null; }
    }

    if (constraints.quiet) {
      if (city.disc < 55) return null;
      pts += (city.disc - 55) * 0.5;
      asked.push("are off the obvious circuit");
      // The reasons differ per place even though the filter does not, so
      // these belong on the card rather than in the lead.
      var top = (city.discWhy || []).slice(0, 2).map(function (t) { return t.toLowerCase(); });
      if (top.length) extra.push("scores " + city.disc + " for discoverability — " + fmt(top));
    }

    if (constraints.rail) {
      if (city.interests.indexOf("rail") >= 0) {
        pts += 12; asked.push("are on the slow-rail list");
      }
    }

    var depth = (city.todo || []).length;
    if (depth >= 4) { pts += 8; extra.push("is one we have written up properly"); }
    else if (depth === 0) { pts -= 6; extra.push("is one we have tagged but not yet written up"); }

    return { city: city, pts: pts, asked: asked, extra: extra };
  }

  function render() {
    var wants = Object.keys(picked);
    var out = el("discover-results");
    if (!wants.length && !constraints.month && !constraints.budget &&
        !constraints.quiet && !constraints.rail) {
      out.innerHTML = '<p class="lede">Choose what you are travelling for. ' +
        "Europe will narrow itself.</p>";
      el("discover-count").textContent = "";
      return;
    }

    var scored = [];
    for (var i = 0; i < ATLAS.cities.length; i++) {
      var r = rate(ATLAS.cities[i]);
      if (r) scored.push(r);
    }
    scored.sort(function (a, b) { return b.pts - a.pts; });

    if (!scored.length) {
      out.innerHTML = '<div class="note warn"><p><strong>Nothing in the Atlas fits all of ' +
        "that.</strong> That is usually several interests at once that no one place carries, " +
        "or a cheap band with an expensive country. Drop one and try again.</p></div>";
      el("discover-count").textContent = "";
      return;
    }

    /* Diversity, from the same argument the planner makes: a list where six
     * of the first eight are Italian has told you about Italy, not about
     * Europe. At most two per country in the first twelve. */
    var perCountry = {}, shown = [];
    for (var j = 0; j < scored.length && shown.length < 12; j++) {
      var cs = scored[j].city.countrySlug;
      if ((perCountry[cs] || 0) >= 2) continue;
      perCountry[cs] = (perCountry[cs] || 0) + 1;
      shown.push(scored[j]);
    }

    /* The count has to be honest about which number it is quoting. An
     * earlier version said "182 places fit, across 9 countries" where the
     * nine was the country count of the twelve SHOWN, not of the 182 —
     * true of nothing, and exactly the sort of number a reader would
     * reasonably repeat. */
    var allCountries = {};
    scored.forEach(function (r) { allCountries[r.city.countrySlug] = true; });
    var n = Object.keys(allCountries).length;
    el("discover-count").textContent =
      scored.length + (scored.length === 1 ? " place fits" : " places fit") +
      ", in " + n + (n === 1 ? " country" : " countries") +
      ". Showing the closest " + shown.length +
      ", at most two per country so the list is Europe rather than one corner of it:";

    /* THE HOIST ONLY LOOKED AT WHAT THE READER ASKED FOR. `asked` is the
     * clauses that come from the filters and `extra` is what the place adds
     * on its own, and only the first was being hoisted — so "is one we have
     * written up properly" was on all twelve rows, under a line explaining
     * that what follows is what else is true of EACH one. Measured on a
     * History & ruins search: twelve rows, twelve identical closing clauses.
     *
     * This is the planner's fault on the sibling surface, and this page is
     * where the rule was written: never explain the constraint back, a
     * reason shared by every result goes in one line above the list. */
    var common = shown[0].asked.filter(function (clause) {
      return shown.every(function (r) { return r.asked.indexOf(clause) >= 0; });
    });
    var shared = shown[0].extra.filter(function (clause) {
      return shown.every(function (r) { return r.extra.indexOf(clause) >= 0; });
    });
    var lead = "";
    if (common.length || shared.length) {
      lead = '<p class="whyall"><span>In common</span> ';
      if (common.length) {
        lead += "All " + shown.length + " " + fmt(common) +
                " — because you asked for that. ";
      }
      if (shared.length) {
        /* "Every one of them", not "Every one of them also": these clauses
         * begin with their own verb — "is one we have written up properly" —
         * so an adverb in front of them produces "also is". */
        lead += (common.length ? "Every one of them " : "All " +
                 shown.length + " ") + fmt(shared) + ". ";
      }
      lead += "What follows is what else is true of each one.</p>";
    }

    out.innerHTML = lead + '<div class="rows">' + shown.map(function (r) {
      var c = r.city;
      var mine = r.extra.filter(function (x) { return shared.indexOf(x) < 0; })
        .concat(r.asked.filter(function (x) { return common.indexOf(x) < 0; }));
      var line = mine.length
        ? '<p class="whythis"><span>Why this</span> ' + c.name + " " + fmt(mine) + ".</p>"
        : '<p class="whythis"><span>Why this</span> nothing beyond what you asked for — ' +
          "it is here on those reasons alone.</p>";
      return '<a class="row" href="' + c.url + '">' +
        "<div><h3>" + c.name + '</h3><p class="rowsub">' + c.why + "</p>" + line + "</div>" +
        '<p class="rowmeta">' + c.country + "<br><span class=\"small\">" +
        c.nights[0] + "–" + c.nights[1] + " nights</span></p></a>";
    }).join("") + "</div>" +
    '<p class="small">Ranked by the terms above and nothing else — there is no paid ' +
    'placement and no field that could carry one. <a href="/method">How the scores work</a>, ' +
    'including <a href="/method#discoverability">discoverability</a>.</p>';
  }

  function chips() {
    var box = el("discover-interests");
    box.innerHTML = ATLAS.interests.map(function (i) {
      return '<button type="button" class="chip pick" data-interest="' + i.slug +
        '" aria-pressed="false"><span aria-hidden="true">' + i.icon + "</span> " +
        i.name + "</button>";
    }).join("");
    box.querySelectorAll("[data-interest]").forEach(function (b) {
      b.addEventListener("click", function () {
        var slug = b.getAttribute("data-interest");
        if (picked[slug]) { delete picked[slug]; } else { picked[slug] = true; }
        b.setAttribute("aria-pressed", picked[slug] ? "true" : "false");
        render();
      });
    });

    var months = el("discover-month");
    months.innerHTML = '<option value="">Any month</option>' +
      ATLAS.months.map(function (m) {
        return '<option value="' + m + '">' + ATLAS.monthNames[m] + "</option>";
      }).join("");
    var budgets = el("discover-budget");
    budgets.innerHTML = '<option value="">Any budget</option>' +
      ATLAS.budgets.map(function (b) {
        return '<option value="' + b.slug + '">' + b.name + "</option>";
      }).join("");
  }

  fetch("/api/atlas.json").then(function (r) { return r.json(); }).then(function (json) {
    ATLAS = json;
    chips();
    el("discover-month").addEventListener("change", function (e) {
      constraints.month = e.target.value; render();
    });
    el("discover-budget").addEventListener("change", function (e) {
      constraints.budget = e.target.value; render();
    });
    el("discover-quiet").addEventListener("change", function (e) {
      constraints.quiet = e.target.checked; render();
    });
    el("discover-rail").addEventListener("change", function (e) {
      constraints.rail = e.target.checked; render();
    });
    el("discover-clear").addEventListener("click", function () {
      picked = {};
      constraints = { month: "", budget: "", quiet: false, rail: false };
      root.querySelectorAll("[data-interest]").forEach(function (b) {
        b.setAttribute("aria-pressed", "false");
      });
      el("discover-month").value = ""; el("discover-budget").value = "";
      el("discover-quiet").checked = false; el("discover-rail").checked = false;
      render();
    });
    render();
  }).catch(function () {
    el("discover-results").innerHTML =
      '<div class="note warn"><p>The Atlas index did not load, so Discover Mode cannot run. ' +
      '<a href="/countries">Browse the Atlas directly</a>.</p></div>';
  });
})();
