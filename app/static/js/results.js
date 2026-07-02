/* Results behaviors: client-side pagination, sort/filter, "Not me" dismissal,
   claim-detail modal, search error state, and screen-reader announcements.
   The matcher returns the full ranked set in one htmx swap; everything here
   operates on that DOM (no re-search). */
(function () {
  "use strict";

  function announce(msg) {
    var live = document.getElementById("live-region");
    if (live) { live.textContent = ""; setTimeout(function () { live.textContent = msg; }, 50); }
  }

  /* ---------- pagination (over currently visible rows) ---------- */

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

  function sectionRows(sec) {
    var list = sec.querySelector("[data-pagelist]");
    return list ? Array.prototype.slice.call(list.querySelectorAll(":scope > li")) : [];
  }

  function activeRows(sec) {
    return sectionRows(sec).filter(function (li) { return !li.__filteredOut && !li.__dismissed; });
  }

  function initSection(sec) {
    var pager = sec.querySelector("[data-pager]");
    var size = parseInt(sec.getAttribute("data-paginate"), 10) || 10;
    var cur = 1;

    function mkBtn(label, page, opts) {
      opts = opts || {};
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = label;
      b.className = "min-w-[34px] px-2.5 py-1.5 rounded-md font-semibold transition " +
        (opts.active ? "bg-brand text-white" : "text-ink-body hover:bg-slate-100") +
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
      var items = activeRows(sec);
      var total = items.length;
      var pages = Math.max(1, Math.ceil(total / size));
      if (cur > pages) cur = pages;

      sectionRows(sec).forEach(function (li) { li.style.display = "none"; });
      items.forEach(function (li, i) {
        li.style.display = (Math.floor(i / size) + 1 === cur) ? "" : "none";
      });

      var count = sec.querySelector("[data-section-count]");
      if (count) count.textContent = total;

      if (!pager) return;
      pager.innerHTML = "";
      if (total <= size) return;

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

    sec.__render = render;
    render();
  }

  /* ---------- sort + filter (potential-matches section only) ---------- */

  function applySortFilter(scope) {
    var sec = scope.querySelector('[data-section="potential"]');
    if (!sec) return;
    var sortSel = scope.querySelector("[data-sort-control]");
    var filterSel = scope.querySelector("[data-filter-control]");
    var list = sec.querySelector("[data-pagelist]");
    if (!list) return;

    var mode = sortSel ? sortSel.value : "best";
    var min = filterSel ? parseFloat(filterSel.value) || 0 : 0;

    var rows = sectionRows(sec);
    rows.sort(function (a, b) {
      if (mode === "amount") {
        return parseFloat(b.getAttribute("data-amount")) - parseFloat(a.getAttribute("data-amount"));
      }
      return parseInt(a.getAttribute("data-rank"), 10) - parseInt(b.getAttribute("data-rank"), 10);
    });
    rows.forEach(function (li) {
      li.__filteredOut = parseFloat(li.getAttribute("data-amount")) < min;
      list.appendChild(li);
    });
    if (sec.__render) sec.__render();
  }

  /* ---------- "Not me" dismissal ---------- */

  function dismiss(btn) {
    var li = btn.closest("li");
    var sec = btn.closest("[data-section]");
    if (!li) { var art = btn.closest("article"); if (art) art.remove(); return; }
    li.__dismissed = true;
    li.style.opacity = 0;
    setTimeout(function () {
      li.style.display = "none";
      var left = sec ? activeRows(sec).length : 0;
      if (sec && sec.__render) sec.__render();
      announce("Removed. " + left + " potential match" + (left === 1 ? "" : "es") + " left.");
      if (sec) {
        var next = sec.querySelector('li:not([style*="display: none"]) a[href]');
        if (next) next.focus();
      }
    }, 180);
  }

  /* ---------- claim-detail modal ---------- */

  var lastFocus = null;

  function closeModal() {
    var m = document.getElementById("match-modal");
    if (m) m.remove();
    document.documentElement.style.overflow = "";
    if (lastFocus) { try { lastFocus.focus(); } catch (e) {} lastFocus = null; }
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  function openModal(article) {
    closeModal();
    lastFocus = document.activeElement;
    var d = article.dataset;
    var claimed = d.status === "claimed";

    var wrap = document.createElement("div");
    wrap.id = "match-modal";
    wrap.innerHTML =
      '<div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-6">' +
        '<div data-modal-scrim class="absolute inset-0 bg-black/30"></div>' +
        '<div role="dialog" aria-modal="true" aria-label="' + esc(d.type) + ' details" tabindex="-1"' +
          ' class="relative bg-white w-full sm:max-w-lg rounded-t-2xl sm:rounded-card shadow-card-lg max-h-[88vh] overflow-y-auto">' +
          '<div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">' +
            '<p class="text-[11px] font-bold text-ink-muted tracking-[0.16em] uppercase">Potential match</p>' +
            '<button type="button" data-modal-close aria-label="Close details" class="text-ink-muted hover:text-ink-heading p-1">' +
              '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>' +
            '</button>' +
          '</div>' +
          '<div class="px-6 py-5">' +
            '<p class="text-[11px] font-bold text-ink-muted tracking-[0.1em] uppercase">Estimated value</p>' +
            '<p class="text-[32px] font-extrabold ' + (claimed ? "text-slate-400 line-through" : "text-money") + ' leading-tight">' + esc(d.amount) + '</p>' +
            '<p class="text-[11px] text-ink-muted uppercase tracking-[0.08em] mt-0.5">' + esc(d.caption) + ' · state-reported</p>' +
            '<dl class="mt-5 space-y-3 text-sm">' +
              '<div><dt class="text-[11px] font-bold text-ink-muted tracking-[0.1em] uppercase">Holder / source</dt>' +
              '<dd class="text-ink-heading font-semibold mt-0.5">' + esc(d.holder) + '</dd>' +
              '<dd class="text-ink-muted text-[13px]">' + esc(d.source) + '</dd></div>' +
              '<div><dt class="text-[11px] font-bold text-ink-muted tracking-[0.1em] uppercase">Property details</dt>' +
              '<dd class="text-ink-heading mt-0.5">' + esc(d.type) + '</dd>' +
              '<dd class="text-ink-muted text-[13px]">Record ID ' + esc(d.rid) + ' · reported as ' + esc(d.owner) + '</dd></div>' +
              (d.address ? '<div><dt class="text-[11px] font-bold text-ink-muted tracking-[0.1em] uppercase">Last known address</dt>' +
              '<dd class="text-ink-heading mt-0.5 flex items-center gap-1.5">' +
              '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-brand shrink-0"><circle cx="12" cy="10" r="3"/><path d="M12 2a8 8 0 0 0-8 8c0 5.4 8 12 8 12s8-6.6 8-12a8 8 0 0 0-8-8z"/></svg>' +
              esc(d.address) + '</dd></div>' : '') +
            '</dl>' +
            (!claimed ?
            '<div class="mt-6">' +
              '<p class="text-[11px] font-bold text-ink-muted tracking-[0.1em] uppercase mb-3">Next steps to receive funds</p>' +
              '<ol class="relative space-y-4 pl-8">' +
                '<span class="absolute left-[11px] top-2 bottom-2 w-px bg-brand/20" aria-hidden="true"></span>' +
                '<li class="relative"><span class="absolute -left-8 top-0 w-6 h-6 rounded-full bg-brand-light text-brand text-xs font-bold flex items-center justify-center">1</span>' +
                '<p class="text-sm font-semibold text-ink-heading">Verify your identity</p>' +
                '<p class="text-[13px] text-ink-muted">Confirm the record matches your name and a past address.</p></li>' +
                '<li class="relative"><span class="absolute -left-8 top-0 w-6 h-6 rounded-full bg-brand-light text-brand text-xs font-bold flex items-center justify-center">2</span>' +
                '<p class="text-sm font-semibold text-ink-heading">File on the state portal</p>' +
                '<p class="text-[13px] text-ink-muted">The deep link opens the state\'s own claim flow — always free.</p></li>' +
                '<li class="relative"><span class="absolute -left-8 top-0 w-6 h-6 rounded-full bg-brand-light text-brand text-xs font-bold flex items-center justify-center">3</span>' +
                '<p class="text-sm font-semibold text-ink-heading">Receive funds from the state</p>' +
                '<p class="text-[13px] text-ink-muted">Most claims process in about 30–180 days. The state pays you directly.</p></li>' +
              '</ol>' +
            '</div>' +
            '<a href="' + esc(d.url) + '" target="_blank" rel="noopener noreferrer"' +
              ' class="mt-6 w-full inline-flex items-center justify-center gap-2 bg-cta hover:bg-cta-dark text-white font-semibold h-12 rounded-pill transition">' +
              'Continue to the state portal' +
              '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7"/><path d="M7 7h10v10"/></svg></a>'
            :
            '<a href="' + esc(d.url) + '" target="_blank" rel="noopener noreferrer"' +
              ' class="mt-6 w-full inline-flex items-center justify-center gap-2 border-2 border-brand text-brand font-semibold h-12 rounded-pill transition hover:bg-brand-light">' +
              'Verify on the state portal</a>'
            ) +
            '<p class="text-[11px] text-ink-muted mt-4 leading-relaxed">SmartCredit is not affiliated with any government agency, ' +
              'never holds your funds, and never charges a finder\'s fee. The state determines eligibility when you file.</p>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(wrap);
    document.documentElement.style.overflow = "hidden";
    var dialog = wrap.querySelector('[role="dialog"]');
    if (dialog) dialog.focus();
  }

  /* ---------- search error state ---------- */

  function showError() {
    var results = document.getElementById("results");
    if (!results) return;
    results.innerHTML =
      '<div class="bg-white rounded-card shadow-card p-10 text-center max-w-2xl mx-auto">' +
        '<div class="w-14 h-14 rounded-full bg-red-50 text-danger flex items-center justify-center mx-auto mb-4">' +
          '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>' +
        '</div>' +
        '<h2 class="text-xl font-bold text-ink-heading">The search didn\'t go through.</h2>' +
        '<p class="mt-2 text-sm text-ink-muted max-w-sm mx-auto">Your connection or our server hiccuped — nothing was lost. Run the same search again.</p>' +
        '<button type="button" data-retry-search class="mt-5 inline-flex items-center gap-2 bg-brand hover:bg-brand-dark text-white text-sm font-semibold px-6 py-2.5 rounded-pill transition">Try again</button>' +
      '</div>';
    announce("The search failed. A try-again button is available.");
  }

  /* ---------- wiring ---------- */

  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target : e.target.parentElement;
    if (!t) return;
    var notme = t.closest("[data-notme]");
    if (notme) { dismiss(notme); return; }
    var detail = t.closest("[data-detail]");
    if (detail) { var a = detail.closest("[data-match]"); if (a) openModal(a); return; }
    if (t.closest("[data-modal-close]") || t.closest("[data-modal-scrim]")) { closeModal(); return; }
    var retry = t.closest("[data-retry-search]");
    if (retry) {
      var form = document.querySelector('form[hx-post="/search"]');
      if (form && window.htmx) window.htmx.trigger(form, "submit");
      return;
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });

  document.addEventListener("change", function (e) {
    if (e.target.matches("[data-sort-control], [data-filter-control]")) {
      var results = document.getElementById("results") || document;
      applySortFilter(results);
    }
  });

  function initAll(root) {
    (root || document).querySelectorAll("[data-paginate]").forEach(function (sec) {
      if (!sec.__paged) { sec.__paged = true; initSection(sec); }
    });
    // Sections small enough to skip pagination still need count/dismiss support.
    (root || document).querySelectorAll("[data-section]:not([data-paginate])").forEach(function (sec) {
      if (!sec.__paged) { sec.__paged = true; sec.setAttribute("data-paginate", "9999"); initSection(sec); }
    });
  }

  document.addEventListener("DOMContentLoaded", function () { initAll(document); });

  document.body.addEventListener("htmx:afterSwap", function (e) {
    initAll(e.target);
    var a = e.target.querySelector ? e.target.querySelector("[data-announce]") : null;
    if (a) announce(a.getAttribute("data-announce"));
  });
  document.body.addEventListener("htmx:responseError", showError);
  document.body.addEventListener("htmx:sendError", showError);
})();
