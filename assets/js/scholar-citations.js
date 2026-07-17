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

  // peaceiris/actions-gh-pages publishes the contents of ./results to the
  // root of the google-scholar-stats branch, so gs_data.json sits at the root.
  var URL =
    "https://raw.githubusercontent.com/Xiaoxiongzzzz/Xiaoxiongzzzz.github.io/google-scholar-stats/gs_data.json";

  fetch(URL, { cache: "no-store" })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (d) {
      var n = d && (d.citedby != null ? d.citedby : d.data && d.data.citedby);
      if (n == null) return;
      el.textContent = "citation: ";
      var b = document.createElement("strong");
      b.textContent = n;
      el.appendChild(b);
      el.title =
        "Citations (Google Scholar)" +
        (d.updated ? ", updated " + d.updated.slice(0, 10) : "");
      el.setAttribute("aria-label", n + " citations on Google Scholar");
      el.hidden = false;
    })
    .catch(function () {
      /* leave the badge hidden */
    });
})();
