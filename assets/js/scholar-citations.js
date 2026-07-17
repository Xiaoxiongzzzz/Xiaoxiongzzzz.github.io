/*
 * Fetches the cached Google Scholar citation count (produced daily by the
 * "Google Scholar stats" GitHub Action on the `google-scholar-stats` branch)
 * and injects it beside the sidebar Google Scholar link.
 *
 * raw.githubusercontent.com sends `Access-Control-Allow-Origin: *`, so this
 * cross-origin fetch works from the browser. On any failure the badge stays
 * hidden and the sidebar looks unchanged.
 */
(function () {
  var el = document.getElementById("gs-citations");
  if (!el) return;

  var URL =
    "https://raw.githubusercontent.com/Xiaoxiongzzzz/Xiaoxiongzzzz.github.io/google-scholar-stats/results/gs_data.json";

  fetch(URL, { cache: "no-store" })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (d) {
      var n = d && (d.citedby != null ? d.citedby : d.data && d.data.citedby);
      if (n == null) return;
      el.textContent = "· " + n + " citations";
      if (d.updated) el.title = "Google Scholar citations, updated " + d.updated;
      el.hidden = false;
    })
    .catch(function () {
      /* leave the badge hidden */
    });
})();
