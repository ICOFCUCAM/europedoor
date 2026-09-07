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

  var ROWS = null;
  var form = document.getElementById("searchform");
  var input = document.getElementById("q");
  var out = document.getElementById("results");

  function norm(s) {
    // Fold accents so "malmo" finds Malmö and "sighnaghi" survives a typo
    // of the diacritic rather than the letters.
    return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function score(row, q) {
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

  function run(qraw) {
    var q = norm(qraw.trim());
    if (q.length < 2) {
      out.innerHTML = '<p class="small">Type two letters or more. Try a city, a country, ' +
        'a kind of trip ("medieval", "wine", "rail"), or something you want to eat.</p>';
      return;
    }
    var hits = [];
    for (var i = 0; i < ROWS.length; i++) {
      var s = score(ROWS[i], q);
      if (s > 0) hits.push({ r: ROWS[i], s: s });
    }
    hits.sort(function (a, b) { return b.s - a.s || a.r.n.localeCompare(b.r.n); });

    if (!hits.length) {
      out.innerHTML = '<div class="note"><p>Nothing for <strong>' + escape_(qraw) +
        "</strong>. Europedoor covers 50 countries and 244 cities — a lot of Europe is " +
        "not in it yet, and saying so is better than guessing. " +
        '<a href="/atlas">Browse the Atlas</a> or ' +
        '<a href="/sources">tell us what is missing</a>.</p></div>';
      return;
    }

    var shown = hits.slice(0, 40);
    var rows = shown.map(function (h) {
      return '<a class="row" href="' + h.r.u + '"><div><h3>' + escape_(h.r.n) +
        '</h3><p class="rowsub">' + escape_(h.r.s) + '</p></div>' +
        '<p class="rowmeta">' + escape_(h.r.k) + "</p></a>";
    }).join("");

    out.innerHTML = "<h2>" + hits.length + (hits.length === 1 ? " result" : " results") +
      (hits.length > shown.length ? " — showing the first " + shown.length : "") +
      '</h2><div class="rows">' + rows + "</div>";
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
      var q = new URLSearchParams(location.search).get("q");
      if (q) input.value = q;
      run(input.value || "");
    })
    .catch(function () {
      out.innerHTML = '<div class="note warn"><p>The search index did not load. ' +
        'The <a href="/atlas">Atlas</a> is fully browsable without it.</p></div>';
    });
})();
