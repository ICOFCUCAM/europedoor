/* My Europe — saved places, in this browser only.
 *
 * localStorage and nothing else. No account, no request, no identifier. It
 * can come back empty (private window, cleared data, a different device) and
 * the page has to be correct when it does, so every read is guarded and the
 * empty state is a real state rather than a spinner. */
(function () {
  "use strict";
  var KEY = "europedoor.saved.v1";

  function read() {
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }
  function write(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); return true; }
    catch (e) { return false; }
  }

  function label(btn, saved) {
    btn.textContent = saved ? "Saved to My Europe ✓" : "Save to My Europe";
  }

  document.querySelectorAll("[data-save]").forEach(function (btn) {
    var id = btn.getAttribute("data-save");
    var list = read();
    label(btn, list.some(function (x) { return x.id === id; }));
    btn.addEventListener("click", function () {
      var current = read();
      var at = current.findIndex(function (x) { return x.id === id; });
      if (at >= 0) current.splice(at, 1);
      else current.push({ id: id, kind: btn.getAttribute("data-kind") || "Place",
                          label: btn.getAttribute("data-label"),
                          url: btn.getAttribute("data-url") });
      if (!write(current)) {
        btn.textContent = "This browser will not let us save";
        return;
      }
      label(btn, at < 0);
    });
  });

  var mine = document.getElementById("mine");
  if (!mine) return;
  var list = read();
  if (!list.length) {
    mine.innerHTML = '<div class="note"><p>Nothing saved yet. Open any city in the ' +
      '<a href="/atlas">Atlas</a> and press <em>Save to My Europe</em>. If you have saved things ' +
      'before and this is empty, you are in a different browser or the site data was cleared — ' +
      'there is no copy anywhere else, which is the point.</p></div>';
    return;
  }
  // Group by kind, so a list of thirty is still readable. Order is fixed
  // rather than by count, so the page does not rearrange itself under you.
  var ORDER = ["Place", "Journey", "Theme", "Story"];
  var groups = {};
  list.forEach(function (x) { (groups[x.kind || "Place"] = groups[x.kind || "Place"] || []).push(x); });
  var html = "<h2>" + list.length + (list.length === 1 ? " saved item" : " saved items") + "</h2>";
  ORDER.concat(Object.keys(groups).filter(function (k) { return ORDER.indexOf(k) < 0; }))
    .forEach(function (k) {
      if (!groups[k] || !groups[k].length) return;
      html += "<h3>" + k + (groups[k].length === 1 ? "" : "s") + "</h3><div class=\"rows\">" +
        groups[k].map(function (x) {
          return '<a class="row" href="' + x.url + '"><div><h3>' + x.label +
            '</h3></div><p class="rowmeta">saved</p></a>';
        }).join("") + "</div>";
    });
  mine.innerHTML = html +
    '<p style="margin-top:var(--s5)"><button class="btn ghost" id="clearmine">Clear the list</button></p>';
  document.getElementById("clearmine").addEventListener("click", function () {
    if (write([])) location.reload();
  });
})();
