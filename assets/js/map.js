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
})();
