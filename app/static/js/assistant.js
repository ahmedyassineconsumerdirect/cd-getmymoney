/* myReclaim assistant — powers the popout drawer and the /assistant page.
   One source of markup (renderPanel) mounted into any [data-assistant-root]. */
(function () {
  "use strict";
  var BOOT = window.MYRECLAIM_ASSISTANT_BOOT || { greeting: "Hi! How can I help?", suggestions: [], mode: "demo" };
  var panels = [];

  function el(html) {
    var t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstChild;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  // Render assistant text: escape, keep line breaks, bold **x**, autolink urls.
  function fmt(s) {
    var h = esc(s).replace(/\n/g, "<br>");
    h = h.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    h = h.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener" class="text-brand underline">$1</a>');
    return h;
  }

  function Panel(root, opts) {
    opts = opts || {};
    this.root = root;
    this.compact = !!opts.compact;
    this.mode = BOOT.mode || "demo";
    this.busy = false;
    this.build();
  }
  Panel.prototype.build = function () {
    this.root.innerHTML =
      '<div class="flex flex-col h-full min-h-0">' +
        '<div class="flex items-center justify-between gap-2 px-1 pb-2 border-b border-slate-100 mb-2">' +
          '<div class="flex items-center gap-1.5 text-xs">' +
            '<span data-mode-dot class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>' +
            '<span data-mode-label class="font-semibold text-ink-muted">Local search</span>' +
          '</div>' +
          '<button type="button" data-connect class="text-xs font-semibold text-brand hover:underline">Connect MaxAI</button>' +
        '</div>' +
        '<div data-msglist class="flex-1 min-h-0 overflow-y-auto space-y-3 pr-1"></div>' +
        '<div data-suggest class="flex flex-wrap gap-1.5 pt-3"></div>' +
        '<form data-form class="mt-3 flex items-end gap-2">' +
          '<textarea data-input rows="1" placeholder="Search a name or ask Max anything…" ' +
            'class="flex-1 resize-none border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent max-h-28"></textarea>' +
          '<button type="submit" data-send class="shrink-0 w-10 h-10 rounded-full bg-cta text-white flex items-center justify-center hover:bg-cta-dark transition disabled:opacity-50" aria-label="Send">' +
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>' +
          '</button>' +
        '</form>' +
        '<div data-connectpanel class="hidden mt-3 border-t border-slate-100 pt-3"></div>' +
        '<p class="text-[10px] text-ink-muted mt-2 leading-snug">MaxAI shows potential matches and guides you to file free with the state. Not affiliated with any state; no finder\'s fee. Verify details with the state.</p>' +
      '</div>';

    this.msglist = this.root.querySelector("[data-msglist]");
    this.suggest = this.root.querySelector("[data-suggest]");
    this.input = this.root.querySelector("[data-input]");
    this.form = this.root.querySelector("[data-form]");
    this.connectPanel = this.root.querySelector("[data-connectpanel]");

    var self = this;
    this.form.addEventListener("submit", function (e) { e.preventDefault(); self.submit(); });
    this.input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); self.submit(); }
    });
    this.input.addEventListener("input", function () {
      self.input.style.height = "auto";
      self.input.style.height = Math.min(self.input.scrollHeight, 112) + "px";
    });
    this.root.querySelector("[data-connect]").addEventListener("click", function () { self.toggleConnect(); });

    this.addBubble("assistant", BOOT.greeting);
    this.renderSuggestions(BOOT.suggestions || []);
    this.refreshMode();
    // Reflect any existing Pine connection (token saved out-of-band).
    fetch("/assistant/status").then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.mode) { self.mode = d.mode; self.refreshMode(); } })
      .catch(function () {});
  };
  Panel.prototype.refreshMode = function () {
    var label = this.root.querySelector("[data-mode-label]");
    var dot = this.root.querySelector("[data-mode-dot]");
    var connect = this.root.querySelector("[data-connect]");
    if (this.mode === "live") {
      if (label) label.textContent = "MaxAI connected · all states";
      if (dot) dot.className = "w-1.5 h-1.5 rounded-full bg-brand";
      if (connect) connect.textContent = "Disconnect";
    } else {
      if (label) label.textContent = "California search";
      if (dot) dot.className = "w-1.5 h-1.5 rounded-full bg-emerald-500";
      if (connect) connect.textContent = "Connect MaxAI";
    }
  };
  Panel.prototype.addBubble = function (who, text) {
    var wrap = el('<div class="flex ' + (who === "user" ? "justify-end" : "justify-start") + '"></div>');
    var bubble = el('<div class="' + (who === "user"
      ? "bg-brand text-white rounded-2xl rounded-br-sm"
      : "bg-slate-100 text-ink-body rounded-2xl rounded-bl-sm") +
      ' px-3.5 py-2.5 text-sm leading-relaxed max-w-[85%] whitespace-pre-wrap break-words"></div>');
    bubble.innerHTML = who === "user" ? esc(text) : fmt(text);
    wrap.appendChild(bubble);
    this.msglist.appendChild(wrap);
    this.scroll();
    return bubble;
  };
  Panel.prototype.typing = function () {
    var wrap = el('<div class="flex justify-start" data-typing></div>');
    wrap.appendChild(el('<div class="bg-slate-100 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-ink-muted">…</div>'));
    this.msglist.appendChild(wrap);
    this.scroll();
    return wrap;
  };
  Panel.prototype.scroll = function () { this.msglist.scrollTop = this.msglist.scrollHeight; };
  Panel.prototype.renderSearch = function (s) {
    var wrap = el('<div class="flex justify-start"></div>');
    var box = el('<div class="w-full max-w-[92%] space-y-2"></div>');
    if (s.total > s.shown) {
      box.appendChild(el('<div class="text-[11px] text-ink-muted px-1">Showing top ' + s.shown + ' of ' + s.total + ' matches</div>'));
    }
    (s.matches || []).forEach(function (m) {
      var amount = m.claimable
        ? '<span class="text-sm font-bold" style="color:#D85A30">' + esc(m.amount) + '</span>'
        : '<span class="text-sm font-semibold text-slate-400 line-through">' + esc(m.amount) + '</span>';
      var action = m.claimable
        ? '<a href="' + esc(m.claim_url) + '" target="_blank" rel="noopener" class="text-xs font-semibold text-white px-3 py-1 rounded-full" style="background:#D85A30">Claim</a>'
        : '<span class="text-xs font-semibold text-slate-500 bg-slate-100 ring-1 ring-slate-200 px-3 py-1 rounded-full">Claimed</span>';
      var card = el(
        '<div class="bg-white border border-slate-200 rounded-xl p-3">' +
          '<div class="flex items-start justify-between gap-2">' +
            '<span class="text-sm font-semibold text-slate-900 truncate">' + esc(m.holder) + '</span>' + amount +
          '</div>' +
          '<div class="text-xs text-ink-muted truncate mt-0.5">' + esc(m.property_type) + ' · reported as ' + esc(m.owner) + '</div>' +
          (m.address ? '<div class="text-xs text-ink-muted truncate">' + esc(m.address) + '</div>' : '') +
          '<div class="flex items-center justify-between gap-2 mt-2">' +
            '<div class="flex items-center gap-1.5">' +
              (m.status === "new"
                ? '<span class="inline-flex items-center gap-0.5 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.2 5.8L20 10l-5.8 2.2L12 18l-2.2-5.8L4 10l5.8-2.2z"/></svg>New</span>'
                : '') +
            '</div>' +
            action +
          '</div>' +
        '</div>'
      );
      box.appendChild(card);
    });
    wrap.appendChild(box);
    this.msglist.appendChild(wrap);
    this.scroll();
  };
  Panel.prototype.renderSuggestions = function (list) {
    var self = this;
    this.suggest.innerHTML = "";
    (list || []).slice(0, 4).forEach(function (s) {
      var chip = el('<button type="button" class="text-xs text-brand bg-brand-light hover:bg-blue-100 rounded-full px-3 py-1.5 transition">' + esc(s) + "</button>");
      chip.addEventListener("click", function () { self.input.value = s; self.submit(); });
      self.suggest.appendChild(chip);
    });
  };
  Panel.prototype.submit = function () {
    var text = (this.input.value || "").trim();
    if (!text || this.busy) return;
    this.input.value = "";
    this.input.style.height = "auto";
    this.send(text);
  };
  Panel.prototype.send = function (text) {
    var self = this;
    this.busy = true;
    this.addBubble("user", text);
    this.suggest.innerHTML = "";
    var t = this.typing();
    fetch("/assistant/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        t.remove();
        self.addBubble("assistant", data.text || "Sorry, I didn't catch that.");
        if (data.search) self.renderSearch(data.search);
        if (data.mode) { self.mode = data.mode; self.refreshMode(); }
        self.renderSuggestions(data.suggestions || []);
      })
      .catch(function () {
        t.remove();
        self.addBubble("assistant", "I'm having trouble responding right now. Please try again.");
      })
      .finally(function () { self.busy = false; });
  };
  Panel.prototype.toggleConnect = function () {
    if (this.mode === "live") { this.doDisconnect(); return; }
    var p = this.connectPanel, self = this;
    if (!p.classList.contains("hidden")) { p.classList.add("hidden"); return; }
    p.classList.remove("hidden");
    p.innerHTML =
      '<p class="text-xs text-ink-muted mb-2">Connect <strong>MaxAI</strong> to search other states\' official unclaimed-property portals live, right here in this chat. We\'ll email you a verification code. MaxAI only searches — you always file free with the state.</p>' +
      '<div class="flex gap-2"><input data-email type="email" placeholder="you@email.com" class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand">' +
      '<button data-reqcode class="bg-brand text-white text-sm font-semibold px-3 rounded-lg hover:bg-brand-dark whitespace-nowrap">Send code</button></div>' +
      '<div data-codestep class="hidden mt-2"><div class="flex gap-2"><input data-code placeholder="Code from email" class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand">' +
      '<button data-verify class="bg-cta text-white text-sm font-semibold px-3 rounded-lg hover:bg-cta-dark whitespace-nowrap">Verify</button></div></div>' +
      '<div data-cmsg class="text-xs mt-2"></div>';
    var email = p.querySelector("[data-email]"), code = p.querySelector("[data-code]");
    var cmsg = p.querySelector("[data-cmsg]"), codestep = p.querySelector("[data-codestep]");
    function msg(t, ok) { cmsg.textContent = t; cmsg.className = "text-xs mt-2 " + (ok ? "text-emerald-600" : "text-danger"); }
    p.querySelector("[data-reqcode]").addEventListener("click", function () {
      msg("Sending…", true);
      fetch("/assistant/connect/request", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: email.value }) })
        .then(function (r) { return r.json(); })
        .then(function (d) { if (d.ok) { codestep.classList.remove("hidden"); msg("Code sent to " + d.email + ". Check your inbox.", true); } else { msg(d.error || "Couldn't send code.", false); } })
        .catch(function () { msg("Network error.", false); });
    });
    p.querySelector("[data-verify]").addEventListener("click", function () {
      msg("Verifying…", true);
      fetch("/assistant/connect/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: email.value, code: code.value }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok) { self.mode = "live"; self.refreshMode(); p.classList.add("hidden"); self.addBubble("assistant", "✓ MaxAI is connected. I can now search any state's official records — just tell me a name and state (e.g. \"find unclaimed property for Jane Doe in Texas\")."); }
          else { msg(d.error || "Verification failed.", false); }
        })
        .catch(function () { msg("Network error.", false); });
    });
  };
  Panel.prototype.doDisconnect = function () {
    var self = this;
    fetch("/assistant/disconnect", { method: "POST" }).then(function (r) { return r.json(); }).then(function (d) {
      self.mode = d.mode || "demo"; self.refreshMode();
      self.addBubble("assistant", "MaxAI account disconnected. Searches now use our own California records only.");
    }).catch(function () {});
  };

  // --- Popout drawer (created once, on every page) ---
  var drawer, drawerPanel, overlay;
  function buildDrawer() {
    overlay = el('<div id="assistant-overlay" class="fixed inset-0 bg-black/20 z-40 opacity-0 pointer-events-none transition-opacity"></div>');
    drawer = el(
      '<div id="assistant-drawer" class="fixed z-50 bottom-0 right-0 sm:bottom-5 sm:right-5 w-full sm:w-[400px] h-[78vh] sm:h-[600px] max-h-[88vh] ' +
      'bg-white sm:rounded-2xl shadow-2xl border border-slate-200 flex flex-col translate-y-4 opacity-0 pointer-events-none transition-all duration-200">' +
        '<div class="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-gradient-to-r from-brand to-brand-dark sm:rounded-t-2xl">' +
          '<div class="flex items-center gap-2.5">' +
            '<div class="w-8 h-8 rounded-full bg-white/15 flex items-center justify-center text-white">' +
              '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>' +
            '</div>' +
            '<div><div class="text-white font-bold text-sm leading-none">MaxAI</div><div class="text-blue-100 text-[11px] mt-0.5">Get My Money Back assistant</div></div>' +
          '</div>' +
          '<button data-close class="text-white/80 hover:text-white" aria-label="Close assistant"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button>' +
        '</div>' +
        '<div class="flex-1 min-h-0 p-3"><div data-assistant-root data-compact class="h-full"></div></div>' +
      '</div>'
    );
    document.body.appendChild(overlay);
    document.body.appendChild(drawer);
    drawerPanel = new Panel(drawer.querySelector("[data-assistant-root]"), { compact: true });
    panels.push(drawerPanel);
    drawer.querySelector("[data-close]").addEventListener("click", api.close);
    overlay.addEventListener("click", api.close);
  }
  function buildFab() {
    var fab = el(
      '<button id="assistant-fab" aria-label="Open MaxAI assistant" ' +
      'class="fixed bottom-5 right-5 z-40 flex items-center gap-2 bg-cta text-white font-semibold pl-4 pr-5 py-3 rounded-pill shadow-lg hover:bg-cta-dark hover:shadow-xl transition">' +
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>' +
        '<span class="text-sm">Ask Max</span>' +
      '</button>'
    );
    fab.addEventListener("click", api.toggle);
    document.body.appendChild(fab);
  }

  var api = {
    open: function (prefill) {
      if (!drawer) return;
      overlay.classList.remove("opacity-0", "pointer-events-none");
      drawer.classList.remove("translate-y-4", "opacity-0", "pointer-events-none");
      var fab = document.getElementById("assistant-fab"); if (fab) fab.style.display = "none";
      if (prefill && drawerPanel) { setTimeout(function () { drawerPanel.send(prefill); }, 150); }
    },
    close: function () {
      if (!drawer) return;
      overlay.classList.add("opacity-0", "pointer-events-none");
      drawer.classList.add("translate-y-4", "opacity-0", "pointer-events-none");
      var fab = document.getElementById("assistant-fab"); if (fab) fab.style.display = "";
    },
    toggle: function () {
      var hidden = drawer.classList.contains("opacity-0");
      if (hidden) api.open(); else api.close();
    },
  };
  window.myReclaimAssistant = api;

  // Delegated handlers for buttons that arrive via htmx swaps (the
  // unsupported-state handoff). Values come from data-* attributes (Jinja
  // autoescaped) and are inserted as textContent, so they can't inject markup.
  document.addEventListener("click", function (e) {
    var pre = e.target.closest("[data-assistant-prefill]");
    if (pre) { e.preventDefault(); api.open(pre.getAttribute("data-assistant-prefill")); return; }
    var nb = e.target.closest("[data-notify-state]");
    if (nb) {
      var span = document.createElement("span");
      span.className = "text-sm font-semibold text-emerald-600";
      span.textContent = "✓ We'll alert you when " + nb.getAttribute("data-notify-state") + " is live.";
      nb.replaceWith(span);
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    // Full-page roots (rendered by the template).
    document.querySelectorAll("[data-assistant-root]:not([data-compact])").forEach(function (root) {
      panels.push(new Panel(root, { compact: false }));
    });
    // Drawer + FAB, unless this page opts out.
    if (!document.body.hasAttribute("data-no-assistant-fab")) {
      buildFab();
      buildDrawer();
    }
  });
})();
