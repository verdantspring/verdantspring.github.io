/* Hoàng-Ân · Poetry Collection — interactions */
(function () {
  "use strict";

  /* ---- theme (day / night) ---- */
  var root = document.documentElement;
  var KEY = "ha-theme";
  function setTheme(t) {
    root.setAttribute("data-theme", t);
    try { localStorage.setItem(KEY, t); } catch (e) {}
  }
  var saved;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  if (saved) setTheme(saved);
  else if (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches) setTheme("night");

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-theme-toggle]");
    if (!t) return;
    setTheme(root.getAttribute("data-theme") === "night" ? "day" : "night");
  });

  /* ---- archive: instant search + year filter ---- */
  var input = document.querySelector("[data-search]");
  if (input) {
    var rows = Array.prototype.slice.call(document.querySelectorAll(".prow"));
    var blocks = Array.prototype.slice.call(document.querySelectorAll(".yearblock"));
    var feat = document.querySelector(".featured");
    var none = document.querySelector(".noresult");
    var norm = function (s) {
      return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "")
        .replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
    };
    var run = function () {
      var q = norm(input.value.trim());
      var hits = 0;
      rows.forEach(function (r) {
        var ok = !q || norm(r.getAttribute("data-search")).indexOf(q) !== -1;
        r.classList.toggle("hidden", !ok);
        if (ok) hits++;
      });
      blocks.forEach(function (b) {
        var any = b.querySelectorAll(".prow:not(.hidden)").length;
        b.classList.toggle("hidden", any === 0);
      });
      if (feat) feat.style.display = q ? "none" : "";
      if (none) none.style.display = hits === 0 ? "block" : "none";
    };
    input.addEventListener("input", run);
    // keyboard: "/" focuses search
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input) { e.preventDefault(); input.focus(); }
      if (e.key === "Escape") { input.value = ""; run(); input.blur(); }
    });
  }

  /* ---- poem page: bilingual view toggle ---- */
  var tog = document.querySelector("[data-viewtoggle]");
  if (tog) {
    var stage = document.querySelector("[data-poem-stage]");
    tog.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-view]"); if (!b) return;
      var v = b.getAttribute("data-view");
      tog.querySelectorAll("button").forEach(function (x) { x.classList.toggle("active", x === b); });
      stage.setAttribute("data-mode", v);
      var vn = stage.querySelector(".col.vn"), en = stage.querySelector(".col.en");
      if (v === "both") { stage.classList.remove("poem-single"); stage.classList.add("cols"); if (vn) vn.style.display = ""; if (en) en.style.display = ""; }
      else {
        stage.classList.add("cols"); stage.classList.add("poem-single");
        if (vn) vn.style.display = (v === "vn") ? "" : "none";
        if (en) en.style.display = (v === "en") ? "" : "none";
      }
      try { localStorage.setItem("ha-view", v); } catch (err) {}
    });
    var pv;
    try { pv = localStorage.getItem("ha-view"); } catch (e) {}
    if (pv) { var pb = tog.querySelector('button[data-view="' + pv + '"]'); if (pb) pb.click(); }
  }

  /* ---- cover: drifting petals (respects reduced-motion) ---- */
  var sky = document.querySelector("[data-petals]");
  if (sky && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    var SVG = "http://www.w3.org/2000/svg";
    for (var i = 0; i < 14; i++) {
      var s = document.createElementNS(SVG, "svg");
      s.setAttribute("class", "petal");
      s.setAttribute("viewBox", "0 0 24 24");
      s.setAttribute("width", (10 + Math.random() * 12).toFixed(1));
      var p = document.createElementNS(SVG, "path");
      // a slim willow-leaf / petal
      p.setAttribute("d", "M12 2C7 7 4 12 12 22 20 12 17 7 12 2Z");
      p.setAttribute("fill", "currentColor");
      s.appendChild(p);
      s.style.left = (Math.random() * 100) + "%";
      s.style.animationDuration = (9 + Math.random() * 12).toFixed(1) + "s";
      s.style.animationDelay = (-Math.random() * 14).toFixed(1) + "s";
      sky.appendChild(s);
    }
  }
})();
