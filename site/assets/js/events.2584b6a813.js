/* Category filtering for the European year.
 *
 * The rows are already in the page with their category on them, so the year
 * is fully readable with JavaScript off; this only decides which are lit. */
(function () {
  "use strict";
  var box = document.getElementById("eventkinds");
  var count = document.getElementById("eventcount");
  var rows = Array.prototype.slice.call(document.querySelectorAll(".row.event"));
  if (!box || !rows.length) return;

  function apply() {
    var on = [];
    var boxes = box.querySelectorAll('input[name="eventkind"]:checked');
    for (var i = 0; i < boxes.length; i++) on.push(boxes[i].value);
    var lit = 0;
    rows.forEach(function (r) {
      var show = !on.length || on.indexOf(r.getAttribute("data-kind")) >= 0;
      r.hidden = !show;
      if (show) lit++;
    });
    // Hide a month heading whose events have all been filtered out.
    document.querySelectorAll("section.band").forEach(function (band) {
      var inBand = band.querySelectorAll(".row.event");
      if (!inBand.length) return;
      var any = Array.prototype.some.call(inBand, function (r) { return !r.hidden; });
      band.hidden = !any;
    });
    count.textContent = on.length
      ? lit + " of " + rows.length + " fixtures match."
      : rows.length + " recurring fixtures. Filter by what kind of thing it is.";
  }

  box.addEventListener("change", apply);
  apply();
})();
