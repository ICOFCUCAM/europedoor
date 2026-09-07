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
})();
