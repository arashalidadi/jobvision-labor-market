/* JobVision site — small progressive-enhancement bundle (no dependencies). */
(function () {
  "use strict";

  var doc = document;
  var faDigits = "۰۱۲۳۴۵۶۷۸۹";

  /* ------------------------------------------------------------------ nav */
  var header = doc.querySelector(".site-header");
  var toggle = doc.querySelector(".menu-toggle");
  var nav = doc.getElementById("nav");

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", function (event) {
      if (event.target.tagName === "A") {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  var onScroll = function () {
    if (!header) return;
    header.classList.toggle("is-stuck", window.scrollY > 8);
    var links = doc.querySelectorAll(".nav a[href^='#']");
    var current = "";
    doc.querySelectorAll("section[id]").forEach(function (section) {
      if (section.getBoundingClientRect().top <= 120) current = section.id;
    });
    links.forEach(function (link) {
      link.classList.toggle("active", link.getAttribute("href") === "#" + current);
    });
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ----------------------------------------------------------- reveal */
  var revealable = doc.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealable.length) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    revealable.forEach(function (el) { observer.observe(el); });
  } else {
    revealable.forEach(function (el) { el.classList.add("in"); });
  }

  /* ------------------------------------------------------------- tabs */
  doc.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = group.querySelectorAll(".tab");
    var panels = group.querySelectorAll("[data-panel]");
    var select = function (name) {
      tabs.forEach(function (tab) {
        var on = tab.dataset.tab === name;
        tab.setAttribute("aria-selected", String(on));
        tab.setAttribute("tabindex", on ? "0" : "-1");
      });
      panels.forEach(function (panel) {
        panel.hidden = panel.dataset.panel !== name;
      });
    };
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () { select(tab.dataset.tab); });
      tab.addEventListener("keydown", function (event) {
        var list = Array.prototype.slice.call(tabs);
        var index = list.indexOf(tab);
        if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
          event.preventDefault();
          var step = event.key === "ArrowRight" ? 1 : -1;
          var next = list[(index + step + list.length) % list.length];
          next.focus();
          select(next.dataset.tab);
        }
      });
    });
    var initial = group.querySelector(".tab[aria-selected='true']") || tabs[0];
    if (initial) select(initial.dataset.tab);
  });

  /* --------------------------------------------------------- lightbox */
  var lightbox = doc.getElementById("lightbox");
  if (lightbox) {
    var image = lightbox.querySelector("img");
    var caption = lightbox.querySelector(".cap");
    var close = function () {
      lightbox.classList.remove("open");
      doc.documentElement.style.overflow = "";
      image.removeAttribute("src");
    };
    doc.querySelectorAll(".figure button").forEach(function (button) {
      button.addEventListener("click", function () {
        image.src = button.dataset.full;
        image.alt = button.dataset.caption || "";
        caption.textContent = button.dataset.caption || "";
        lightbox.classList.add("open");
        doc.documentElement.style.overflow = "hidden";
      });
    });
    lightbox.addEventListener("click", function (event) {
      if (event.target === lightbox || event.target.tagName === "BUTTON") close();
    });
    doc.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && lightbox.classList.contains("open")) close();
    });
  }

  /* ------------------------------------------------------------ copy */
  doc.querySelectorAll(".copy-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      var text = button.dataset.copy || "";
      var done = function () {
        var label = button.textContent;
        button.textContent = button.dataset.doneText || "Copied";
        setTimeout(function () { button.textContent = label; }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
      function fallback() {
        var area = doc.createElement("textarea");
        area.value = text;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.opacity = "0";
        doc.body.appendChild(area);
        area.select();
        try { doc.execCommand("copy"); done(); } catch (error) { /* noop */ }
        doc.body.removeChild(area);
      }
    });
  });

  /* ------------------------------------------------------- count-up */
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var counters = doc.querySelectorAll("[data-count]");
  if (!reduce && "IntersectionObserver" in window && counters.length) {
    var counterObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        counterObs.unobserve(entry.target);
        var el = entry.target;
        var target = parseFloat(el.dataset.count);
        var decimals = parseInt(el.dataset.decimals || "0", 10);
        var suffix = el.dataset.suffix || "";
        var start = performance.now();
        var duration = 1100;
        var tick = function (now) {
          var t = Math.min(1, (now - start) / duration);
          var eased = 1 - Math.pow(1 - t, 3);
          var value = target * eased;
          el.textContent = format(value, decimals) + suffix;
          if (t < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { counterObs.observe(el); });
  }

  function format(value, decimals) {
    var fixed = value.toFixed(decimals);
    var parts = fixed.split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, "٬");
    return parts.join(".");
  }

  /* ----------------------------------------------------- misc niceties */
  doc.querySelectorAll("a[href^='http']").forEach(function (link) {
    if (link.hostname !== location.hostname && !link.hasAttribute("data-nolink")) {
      link.setAttribute("rel", "noopener");
    }
  });

  var year = doc.querySelectorAll("[data-year]");
  year.forEach(function (el) { el.textContent = faDigits ? new Date().getFullYear() : el.textContent; });
})();
