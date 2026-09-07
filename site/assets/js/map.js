/* Layer filtering for the point map. The dots are already in the page —
 * this only decides which ones are lit, so the map works (as a plain map of
 * everywhere) with JavaScript off. */
(function () {
  "use strict";
  var box = document.getElementById("layers");
  var dots = Array.prototype.slice.call(document.querySelectorAll("#dots .dot"));
  var count = document.getElementById("mapcount");
  if (!box || !dots.length) return;

  function apply() {
    var on = [];
    var boxes = box.querySelectorAll('input[name="layer"]:checked');
    for (var i = 0; i < boxes.length; i++) on.push(boxes[i].value);
    var lit = 0;
    dots.forEach(function (d) {
      var tags = (d.getAttribute("data-tags") || "").split(" ");
      var show = !on.length || on.some(function (t) { return tags.indexOf(t) >= 0; });
      d.classList.toggle("off", !show);
      if (show) lit++;
    });
    count.textContent = on.length
      ? lit + " of " + dots.length + " cities match the layers you turned on."
      : dots.length + " cities. Turn on a layer to narrow it.";
  }

  // Arriving from the homepage with ?layer=mountains turns that layer on.
  var wanted = new URLSearchParams(location.search).get("layer");
  if (wanted) {
    var pre = box.querySelector('input[name="layer"][value="' + wanted + '"]');
    if (pre) pre.checked = true;
  }

  box.addEventListener("change", apply);
  apply();

  /* The journey overlay. The points are projected at build time and handed
   * to the page, so the line and the dots cannot drift apart — a map that
   * draws a route two pixels off the city it visits looks broken in a way
   * nobody can quite name. */
  var sel = document.getElementById("journeylayer");
  var route = document.getElementById("route");
  var note = document.getElementById("routenote");
  var JOURNEYS = window.EUROPEDOOR_JOURNEYS || [];
  if (!sel || !route) return;

  function drawJourney() {
    route.innerHTML = "";
    var j = null;
    for (var i = 0; i < JOURNEYS.length; i++) if (JOURNEYS[i].slug === sel.value) j = JOURNEYS[i];
    if (!j) { note.textContent = ""; return; }

    var d = j.pts.map(function (p, i) { return (i ? "L" : "M") + p.x + " " + p.y; }).join(" ");
    var ns = "http://www.w3.org/2000/svg";
    var line = document.createElementNS(ns, "path");
    line.setAttribute("d", d);
    line.setAttribute("class", "routeline");
    route.appendChild(line);

    j.pts.forEach(function (p, i) {
      var c = document.createElementNS(ns, "circle");
      c.setAttribute("cx", p.x); c.setAttribute("cy", p.y); c.setAttribute("r", 7);
      c.setAttribute("class", "routedot");
      var t = document.createElementNS(ns, "title");
      t.textContent = (i + 1) + ". " + p.name;
      c.appendChild(t);
      route.appendChild(c);
    });

    note.innerHTML = j.name + " — " + j.pts.length + " stops over " + j.days + " days. " +
      '<a href="' + j.url + '">Read the route</a>. The line is straight between stops; ' +
      "what that means on the ground is on the journey page.";
  }

  sel.addEventListener("change", drawJourney);
  drawJourney();

  /* Popups. The specification wants a card on click: name, category, a
   * sentence, the distance, and a way in. The dots stay real links so the
   * map still works with JavaScript off — the click is intercepted, not
   * replaced. */
  var INFO = window.EUROPEDOOR_MAPINFO || {};
  var popup = document.getElementById("mappopup");
  var fromSel = document.getElementById("mapfrom");
  var placesLayer = document.getElementById("places");
  var extra = box.querySelector('input[name="extra"][value="places"]');

  function kmBetween(a, b) {
    var R = 6371, p1 = a.la * Math.PI / 180, p2 = b.la * Math.PI / 180;
    var dp = p2 - p1, dl = (b.lo - a.lo) * Math.PI / 180;
    var h = Math.sin(dp / 2) * Math.sin(dp / 2) +
            Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return Math.round(2 * R * Math.asin(Math.sqrt(h)));
  }

  function esc(x) {
    return String(x).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function showPopup(id) {
    var d = INFO[id];
    if (!d) return;
    var origin = fromSel && fromSel.value ? INFO[fromSel.value] : null;
    var dist = origin && origin !== d
      ? "<p class=\"small\">" + kmBetween(origin, d) + " km from " + esc(origin.n) + "</p>" : "";
    var counts = [];
    if (d.p) counts.push(d.p + (d.p === 1 ? " place" : " places"));
    if (d.e) counts.push(d.e + (d.e === 1 ? " experience" : " experiences"));
    popup.innerHTML =
      '<button class="mappopup-close" type="button" aria-label="Close">×</button>' +
      "<p class=\"kicker\">" + esc(d.r) + " · " + esc(d.c) + "</p>" +
      "<h2 class=\"mini\">" + esc(d.n) + "</h2>" +
      "<p>" + esc(d.s) + "</p>" +
      (counts.length ? '<p class="small">' + counts.join(" · ") + "</p>" : "") +
      dist +
      (d.adv ? '<p class="small">This country is under a travel advisory.</p>' : "") +
      '<p><a class="btn ghost" href="' + d.u + '">Open ' + esc(d.n) + "</a></p>";
    popup.hidden = false;
    popup.querySelector(".mappopup-close").addEventListener("click", function () {
      popup.hidden = true;
    });
  }

  dots.forEach(function (a) {
    a.addEventListener("click", function (ev) {
      // Modified clicks and middle clicks keep the plain-link behaviour.
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
      ev.preventDefault();
      showPopup(a.getAttribute("data-id"));
    });
  });
  if (fromSel) fromSel.addEventListener("change", function () { popup.hidden = true; });
  if (extra && placesLayer) {
    extra.addEventListener("change", function () {
      // `.hidden` is an HTMLElement property. This is an SVG <g>, so setting
      // it defines a JS property nobody reads and the layer never appears —
      // the attribute has to be set and removed by hand.
      if (extra.checked) placesLayer.removeAttribute("hidden");
      else placesLayer.setAttribute("hidden", "");
    });
  }
})();
