/* JobVision — project guide: search, table expansion, TOC scrollspy, mobile sidebar. */
(function () {
  "use strict";

  var doc = document;
  var script = doc.currentScript;
  var indexUrl = (script && script.dataset.index) || "search.json";

  /* ------------------------------------------------------- mobile sidebar */
  var side = doc.getElementById("guideSide");
  var main = doc.getElementById("main");
  if (side && main) {
    var toggle = doc.createElement("button");
    toggle.type = "button";
    toggle.className = "guide-side-toggle";
    toggle.innerHTML = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round'><path d='M4 6h16M4 12h16M4 18h16'/></svg><span>" +
      (doc.documentElement.lang === "fa" ? "فهرست بخش‌ها" : "Sections") + "</span>";
    toggle.addEventListener("click", function () { side.classList.toggle("open"); });
    main.insertBefore(toggle, main.firstChild);
  }

  /* -------------------------------------------------------- table expand */
  doc.querySelectorAll(".table-more").forEach(function (button) {
    button.addEventListener("click", function () {
      var figure = button.closest(".guide-table");
      if (!figure) return;
      var hidden = figure.querySelectorAll("tr.is-extra");
      var expand = hidden[0] && hidden[0].hasAttribute("hidden");
      hidden.forEach(function (row) {
        if (expand) row.removeAttribute("hidden");
        else row.setAttribute("hidden", "");
      });
      button.textContent = expand
        ? (doc.documentElement.lang === "fa" ? "جمع کردن ردیف‌ها" : "Collapse rows")
        : button.dataset.label;
    });
    button.dataset.label = button.textContent;
  });

  /* ------------------------------------------------------------- scrollspy */
  var tocLinks = Array.prototype.slice.call(doc.querySelectorAll(".aside-toc a[href^='#']"));
  var heads = tocLinks.map(function (link) {
    return doc.getElementById(link.getAttribute("href").slice(1));
  }).filter(Boolean);
  if (heads.length) {
    var highlight = function () {
      var current = heads[0];
      heads.forEach(function (head) {
        if (head.getBoundingClientRect().top <= 140) current = head;
      });
      tocLinks.forEach(function (link) {
        link.classList.toggle("is-current", link.getAttribute("href") === "#" + current.id);
      });
    };
    window.addEventListener("scroll", highlight, { passive: true });
    highlight();
  }

  /* ---------------------------------------------------------------- search */
  var modal = doc.getElementById("searchModal");
  var input = doc.getElementById("searchInput");
  var results = doc.getElementById("searchResults");
  if (!modal || !input || !results) return;

  var entries = null;
  var loading = false;
  var isFa = doc.documentElement.lang === "fa";

  var load = function () {
    if (entries || loading) return;
    loading = true;
    fetch(indexUrl, { credentials: "same-origin" })
      .then(function (response) { return response.ok ? response.json() : []; })
      .then(function (data) { entries = data || []; run(); })
      .catch(function () { entries = []; });
  };

  var strip = function (text) { return (text || "").replace(/[#*`]/g, "").slice(0, 240); };

  function run() {
    var query = input.value.trim();
    results.innerHTML = "";
    if (!entries) { load(); return; }
    if (query.length < 2) { return; }
    var words = query.toLowerCase().split(/\s+/).filter(Boolean);
    var hits = [];
    entries.forEach(function (entry) {
      var haystack = (entry.title + " " + entry.text).toLowerCase();
      var score = 0;
      for (var i = 0; i < words.length; i += 1) {
        if (haystack.indexOf(words[i]) === -1) return;
        var inTitle = entry.title.toLowerCase().indexOf(words[i]) !== -1;
        score += inTitle ? 6 : 1;
      }
      hits.push({ entry: entry, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    if (!hits.length) {
      results.innerHTML = "<li><p class='hint'>" +
        (isFa ? "چیزی پیدا نشد" : "Nothing found") + "</p></li>";
      return;
    }
    hits.slice(0, 12).forEach(function (hit) {
      var item = doc.createElement("li");
      var link = doc.createElement("a");
      link.href = hit.entry.url;
      var snippet = strip(hit.entry.text);
      var position = snippet.toLowerCase().indexOf(words[0]);
      if (position > 60) snippet = "…" + snippet.slice(position - 40);
      link.innerHTML = "<span class='r-sec'>" + (isFa ? "بخش " : "Section ") + hit.entry.section +
        "</span><span class='r-title'>" + hit.entry.title + "</span>" +
        (snippet ? "<span class='r-snippet'>" + snippet + "</span>" : "");
      item.appendChild(link);
      results.appendChild(item);
    });
  }

  var open = function () {
    modal.classList.add("open");
    doc.documentElement.style.overflow = "hidden";
    load();
    setTimeout(function () { input.focus(); }, 30);
  };
  var close = function () {
    modal.classList.remove("open");
    doc.documentElement.style.overflow = "";
  };

  doc.querySelectorAll(".guide-search-btn").forEach(function (button) {
    button.addEventListener("click", open);
  });
  input.addEventListener("input", run);
  modal.addEventListener("click", function (event) {
    if (event.target === modal) close();
  });
  doc.addEventListener("keydown", function (event) {
    if (event.key === "Escape") close();
    if ((event.key === "/" || (event.key === "k" && (event.metaKey || event.ctrlKey))) &&
        !/input|textarea/i.test((event.target.tagName || ""))) {
      event.preventDefault();
      open();
    }
  });
})();
