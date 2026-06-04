/* Client-side pagination for results sections.
   The matcher returns the full ranked set in one htmx swap; we page through it
   in the browser (no re-search per page). Any <section data-paginate="N">
   with a [data-pagelist] of <li> rows and a [data-pager] nav gets paged N/page. */
(function () {
  "use strict";

  function pageWindow(cur, total) {
    if (total <= 7) {
      var all = [];
      for (var i = 1; i <= total; i++) all.push(i);
      return all;
    }
    var keep = {};
    [1, 2, total - 1, total, cur - 1, cur, cur + 1].forEach(function (n) {
      if (n >= 1 && n <= total) keep[n] = true;
    });
    var nums = Object.keys(keep).map(Number).sort(function (a, b) { return a - b; });
    var out = [];
    for (var j = 0; j < nums.length; j++) {
      if (j > 0 && nums[j] - nums[j - 1] > 1) out.push("…");
      out.push(nums[j]);
    }
    return out;
  }

  function initSection(sec) {
    if (sec.__paged) return;
    sec.__paged = true;
    var size = parseInt(sec.getAttribute("data-paginate"), 10) || 10;
    var list = sec.querySelector("[data-pagelist]");
    var pager = sec.querySelector("[data-pager]");
    if (!list || !pager) return;
    var items = Array.prototype.slice.call(list.querySelectorAll(":scope > li"));
    var total = items.length;
    var pages = Math.ceil(total / size);
    var cur = 1;

    function mkBtn(label, page, opts) {
      opts = opts || {};
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = label;
      b.className = "min-w-[34px] px-2.5 py-1.5 rounded-md font-semibold transition " +
        (opts.active
          ? "bg-brand text-white"
          : "text-ink-body hover:bg-slate-100") +
        (opts.disabled ? " opacity-40 cursor-default pointer-events-none" : "");
      if (opts.active) b.setAttribute("aria-current", "page");
      if (!opts.disabled && !opts.active) {
        b.addEventListener("click", function () {
          cur = page;
          render();
          try { sec.scrollIntoView({ behavior: "smooth", block: "start" }); } catch (e) {}
        });
      }
      return b;
    }

    function render() {
      for (var i = 0; i < total; i++) {
        items[i].style.display = (Math.floor(i / size) + 1 === cur) ? "" : "none";
      }
      pager.innerHTML = "";

      var from = (cur - 1) * size + 1;
      var to = Math.min(cur * size, total);
      var info = document.createElement("span");
      info.className = "text-xs text-ink-muted mr-2";
      info.textContent = "Showing " + from + "–" + to + " of " + total;
      pager.appendChild(info);

      pager.appendChild(mkBtn("‹ Prev", cur - 1, { disabled: cur === 1 }));
      pageWindow(cur, pages).forEach(function (n) {
        if (n === "…") {
          var dots = document.createElement("span");
          dots.className = "px-1.5 text-ink-muted";
          dots.textContent = "…";
          pager.appendChild(dots);
        } else {
          pager.appendChild(mkBtn(String(n), n, { active: n === cur }));
        }
      });
      pager.appendChild(mkBtn("Next ›", cur + 1, { disabled: cur === pages }));
    }

    render();
  }

  function initAll(root) {
    (root || document).querySelectorAll("[data-paginate]").forEach(initSection);
  }

  document.addEventListener("DOMContentLoaded", function () { initAll(document); });
  // Results arrive via htmx swap into #results.
  document.body.addEventListener("htmx:afterSwap", function (e) { initAll(e.target); });
})();
