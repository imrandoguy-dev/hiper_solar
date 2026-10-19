/* Hipersign ERP – Module Navigator v3
 * A compact switcher that mirrors the Desktop: the same module icons, same order, same targets.
 * One click opens the module with ITS OWN sidebar.
 *  - Close (×)  : closes the panel; the small "Modules" button stays to reopen it.
 *  - Minimise   : shrinks to a slim icon strip that stays on screen while you work.
 *  - Alt+M      : open / close.  Esc: close.
 * Works as (a) a Custom HTML Block script (root_element provided) or (b) an app_include_js file.
 */
(function () {
  try {
    if (typeof root_element !== "undefined" && root_element) {
      var host = root_element.host || (root_element.getRootNode && root_element.getRootNode().host);
      var blk = host && host.closest && host.closest(".ce-block");
      if (blk) blk.classList.add("hs-mn-hidden-block");
    }
  } catch (e) {}

  if (window.hsModuleNav && window.hsModuleNav.version >= 3) { window.hsModuleNav.sync(); return; }
  if (window.hsModuleNav && window.hsModuleNav.destroy) window.hsModuleNav.destroy();

  var NAV = (window.hsModuleNav = { version: 3 });
  var state = { modules: null, byLabel: {}, view: "closed", openFolder: null };
  var launcher, panel, mini;

  var SVG = {
    grid: '<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="2" y="2" width="5" height="5" rx="1.2"/><rect x="9" y="2" width="5" height="5" rx="1.2"/><rect x="2" y="9" width="5" height="5" rx="1.2"/><rect x="9" y="9" width="5" height="5" rx="1.2"/></svg>',
    min: '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M9.5 6.5 14 2M9.5 6.5V3.5M9.5 6.5h3M6.5 9.5 2 14M6.5 9.5v3M6.5 9.5h-3"/></svg>',
    max: '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M10 2h4v4M14 2 9.5 6.5M6 14H2v-4M2 14l4.5-4.5"/></svg>',
    close: '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M4 4l8 8M12 4l-8 8"/></svg>',
    back: '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3 5 8l5 5"/></svg>'
  };

  function esc(s) { return frappe.utils.escape_html(String(s == null ? "" : s)); }
  function slug(n) { return frappe.router && frappe.router.slug ? frappe.router.slug(n) : String(n).toLowerCase().replace(/[^a-z0-9]+/g, "-"); }
  function lsGet(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { window.localStorage.setItem(k, v); } catch (e) {} }
  function sidebars() { return (frappe.boot && frappe.boot.workspace_sidebar_item) || {}; }

  // ---------- styles ----------
  function injectCSS() {
    var old = document.getElementById("hs-mn-style");
    if (old) old.remove();
    var css = [
      ".hs-mn-hidden-block{display:none!important}",
      ".hs-hidden{display:none!important}",
      ".hs-mn-launcher{position:fixed;right:20px;bottom:20px;z-index:1031;display:flex;align-items:center;gap:7px;height:36px;padding:0 14px 0 12px;border-radius:999px;border:1px solid var(--border-color,#e5e7eb);background:var(--card-bg,#fff);color:var(--text-color,#1f2937);font-size:12.5px;font-weight:600;box-shadow:0 6px 20px rgba(15,23,42,.14);cursor:pointer;transition:transform .15s,box-shadow .15s}",
      ".hs-mn-launcher:hover{transform:translateY(-1px);box-shadow:0 10px 26px rgba(15,23,42,.18)}",
      ".hs-mn-launcher .hs-mn-kbd{font-size:10.5px;font-weight:500;color:var(--text-muted,#6b7280);border:1px solid var(--border-color,#e5e7eb);border-radius:5px;padding:0 5px}",
      ".hs-mn-panel,.hs-mn-mini{position:fixed;right:20px;bottom:20px;z-index:1032;background:var(--card-bg,#fff);color:var(--text-color,#1f2937);border:1px solid var(--border-color,#e5e7eb);border-radius:14px;box-shadow:0 16px 44px rgba(15,23,42,.2);overflow:hidden;animation:hsMnIn .16s ease-out}",
      "@keyframes hsMnIn{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}",
      ".hs-mn-panel{width:min(452px,calc(100vw - 32px));max-height:calc(100vh - 80px);display:flex;flex-direction:column}",
      ".hs-mn-head{display:flex;align-items:center;gap:8px;padding:12px 10px 4px 16px}",
      ".hs-mn-title{font-size:14px;font-weight:600;white-space:nowrap}",
      ".hs-mn-pill{font-size:11px;font-weight:600;color:#b45309;background:#fef3c7;border-radius:999px;padding:2px 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}",
      ".hs-mn-actions{display:flex;gap:2px;margin-left:auto}",
      ".hs-mn-iconbtn{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border:0;border-radius:7px;background:transparent;color:var(--text-muted,#6b7280);cursor:pointer}",
      ".hs-mn-iconbtn:hover{background:var(--fg-hover-color,#f3f4f6);color:var(--text-color,#111827)}",
      ".hs-mn-sub{display:flex;align-items:center;gap:6px;padding:2px 16px 0;font-size:12px;color:var(--text-muted,#6b7280)}",
      ".hs-mn-sub b{color:var(--text-color,#111827)}",
      ".hs-mn-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:4px 6px;padding:10px 12px 14px;overflow-y:auto}",
      "@media (max-width:420px){.hs-mn-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.hs-mn-panel,.hs-mn-mini,.hs-mn-launcher{right:12px;bottom:12px}}",
      ".hs-mn-app{display:flex;flex-direction:column;align-items:center;gap:6px;padding:9px 4px 8px;border:1px solid transparent;border-radius:12px;background:transparent;cursor:pointer;outline:0;transition:background .12s,border-color .12s,transform .12s}",
      ".hs-mn-app:hover,.hs-mn-app:focus-visible{background:var(--fg-hover-color,#f3f4f6);transform:translateY(-1px)}",
      ".hs-mn-app.is-active{background:var(--fg-hover-color,#f3f4f6);border-color:var(--border-color,#d1d5db)}",
      ".hs-mn-app.is-active .hs-mn-cap{color:var(--primary,#2490EF);font-weight:600}",
      ".hs-mn-ic{width:44px;height:44px;border-radius:11px;display:flex;align-items:center;justify-content:center;overflow:hidden;flex:none}",
      ".hs-mn-ic img{width:100%;height:100%;object-fit:contain;display:block}",
      ".hs-mn-ic>*{max-width:100%;max-height:100%}",
      ".hs-mn-ic .hs-mn-fallback{width:100%;height:100%;border-radius:11px;background:#2490EF;color:#fff;font-weight:700;font-size:17px;display:flex;align-items:center;justify-content:center}",
      ".hs-mn-folder{background:var(--control-bg,#f3f4f6);display:grid;grid-template-columns:1fr 1fr;gap:3px;padding:6px}",
      ".hs-mn-folder>span{border-radius:4px;overflow:hidden;display:flex}",
      ".hs-mn-folder img{width:100%;height:100%;object-fit:contain}",
      ".hs-mn-cap{font-size:11.5px;line-height:1.2;color:var(--text-color,#374151);text-align:center;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
      ".hs-mn-folderhead{grid-column:1/-1;display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;padding:0 2px 4px}",
      ".hs-mn-folderhead button{display:inline-flex;align-items:center;gap:4px;border:0;background:var(--control-bg,#f3f4f6);color:var(--text-color,#374151);border-radius:6px;padding:3px 8px;font-size:11.5px;cursor:pointer}",
      ".hs-mn-mini{width:auto;max-width:calc(100vw - 32px)}",
      ".hs-mn-mini .hs-mn-head{padding:8px 6px 2px 12px}",
      ".hs-mn-mini .hs-mn-title{font-size:12.5px}",
      ".hs-mn-strip{display:flex;flex-wrap:wrap;gap:5px;padding:6px 10px 10px;max-width:420px}",
      ".hs-mn-dot{width:32px;height:32px;border-radius:9px;border:2px solid transparent;padding:0;background:transparent;cursor:pointer;transition:transform .12s}",
      ".hs-mn-dot:hover{transform:translateY(-1px)}",
      ".hs-mn-dot.is-active{border-color:var(--primary,#2490EF)}",
      ".hs-mn-dot .hs-mn-ic{width:28px;height:28px;border-radius:7px}",
      ".hs-mn-dot .hs-mn-fallback{border-radius:7px;font-size:12px}",
      ".hs-mn-dot .hs-mn-folder{padding:3px;gap:2px}"
    ].join("\n");
    var st = document.createElement("style");
    st.id = "hs-mn-style";
    st.textContent = css;
    document.head.appendChild(st);
  }

  // ---------- the 12 modules shown in the switcher (same as the Desktop) ----------
  // label: caption · art: Desktop icon whose artwork is reused · sidebar: Workspace Sidebar to open
  // folder: Desktop folder whose children open inside the panel · url: external page
  var MODULES = [
    { label: "Organization", sidebar: "Organization" },
    { label: "Solar", sidebar: "Solar" },
    { label: "Solar Support", sidebar: "Solar Support" },
    { label: "Accounting", folder: "Accounting",
      fallback: ["Invoicing", "Payments", "Financial Reports", "Accounts Setup", "Taxes", "Banking", "Budget", "Share Management", "Subscription"] },
    { label: "Assets", sidebar: "Assets" },
    { label: "Buying", sidebar: "Buying" },
    { label: "CRM", sidebar: "CRM" },
    { label: "Projects", sidebar: "Projects" },
    { label: "Selling", sidebar: "Selling" },
    { label: "Stock", sidebar: "Stock" },
    { label: "Frappe CRM", url: "/crm" },
    { label: "HR", art: "Frappe HR", sidebar: "HR Setup" }
  ];

  function desktopIcons() {
    return ((frappe.boot && frappe.boot.desktop_icons) || []).concat(frappe.desktop_icons || []);
  }
  function desktopIcon(label) {
    var l = desktopIcons();
    for (var i = 0; i < l.length; i++) if (l[i] && l[i].label === label) return l[i];
    return null;
  }

  // Route of a sidebar's first link — the same rule the Desktop page uses to open an icon.
  function iconRoute(icon) {
    if (!icon) return null;
    if (icon.link_type === "External" && icon.link) return /^https?:/.test(icon.link) ? icon.link : window.location.origin + icon.link;
    var sb = sidebars()[String(icon.label || "").toLowerCase()];
    if (!sb) return null;
    var first = (sb.items || []).filter(function (i) { return i.type === "Link"; })[0];
    if (!first) return null;
    try {
      if (first.link_type === "Workspace") {
        var ws = frappe.workspaces && frappe.workspaces[slug(first.link_to)];
        if (!ws) return "/desk/" + slug(first.link_to);
        return frappe.utils.generate_route({ type: "workspace", name: ws.title, public: ws.public ? 1 : 0 });
      }
      if (first.link_type === "URL") return first.url;
      if (first.link_type === "Report") {
        var a = { type: "Report", name: first.link_to };
        if (first.report) {
          a.is_query_report = first.report.report_type === "Query Report" || first.report.report_type === "Script Report";
          a.report_ref_doctype = first.report.ref_doctype;
        }
        return frappe.utils.generate_route(a);
      }
      return frappe.utils.generate_route({ type: first.link_type, name: first.link_to, tab: first.tab });
    } catch (e) { return null; }
  }

  function sidebarEntry(label, art) {
    var sb = sidebars()[String(label).toLowerCase()];
    if (!sb) return null;                                  // user has no access to this sidebar
    var route = iconRoute({ label: label, link_type: "Workspace Sidebar" });
    return route ? { label: label, art: art || label, sidebar: sb.label || label, route: route, children: [] } : null;
  }

  function loadModules() {
    if (state.modules) return state.modules;
    var out = [], byLabel = {};
    MODULES.forEach(function (spec) {
      var m = null;
      if (spec.folder) {
        var kids = desktopIcons().filter(function (i) { return i && i.parent_icon === spec.folder && String(i.hidden) !== "1"; })
          .sort(function (a, b) { return (a.idx || 0) - (b.idx || 0); }).map(function (i) { return i.label; });
        if (!kids.length) kids = spec.fallback || [];
        var seen = {};
        var children = kids.filter(function (k) { if (seen[k]) return false; seen[k] = 1; return true; })
          .map(function (k) { return sidebarEntry(k); }).filter(Boolean);
        if (children.length) m = { label: spec.label, art: spec.art || spec.label, folder: true, children: children, route: null };
        children.forEach(function (c) { byLabel[c.label] = c; });
      } else if (spec.url) {
        m = { label: spec.label, art: spec.art || spec.label, url: spec.url, route: spec.url, children: [] };
      } else {
        m = sidebarEntry(spec.sidebar || spec.label, spec.art || spec.label);
        if (m) m.label = spec.label;
      }
      if (m) { out.push(m); byLabel[m.label] = m; }
    });
    state.modules = out;
    state.byLabel = byLabel;
    return out;
  }

  function iconHtml(m) {
    if (m.folder) {
      var kids = m.children.slice(0, 4).map(function (c) { return "<span>" + imgOnly(c) + "</span>"; }).join("");
      return '<div class="hs-mn-ic hs-mn-folder">' + kids + "</div>";
    }
    return '<div class="hs-mn-ic">' + imgOnly(m) + "</div>";
  }
  function imgOnly(m) {
    var art = m.art || m.label, url = null, di = desktopIcon(art);
    try { url = frappe.utils.get_desktop_icon(art, frappe.boot.desktop_icon_style || "subtle"); } catch (e) {}
    url = url || (di && (di.logo_url || di.icon_image));
    if (url) return '<img src="' + esc(url) + '" alt="" loading="lazy">';
    try { if (frappe.utils.desktop_icon) return frappe.utils.desktop_icon(art, (di && di.bg_color) || "blue", "md"); } catch (e) {}
    return '<span class="hs-mn-fallback">' + esc((m.label || "?").charAt(0)) + "</span>";
  }

  function currentLabel() {
    var t = frappe.app && frappe.app.sidebar && frappe.app.sidebar.sidebar_title;
    return t || null;
  }
  // The top-level module the current sidebar belongs to.
  function activeModule() {
    var t = currentLabel();
    if (!t || !state.modules) return null;
    for (var i = 0; i < state.modules.length; i++) {
      var m = state.modules[i];
      if (m.sidebar === t || m.children.some(function (c) { return c.sidebar === t; })) return m;
    }
    return null;
  }

  // ---------- navigation ----------
  function open(label) {
    var m = state.byLabel[label];
    if (!m) return;
    if (m.folder) {                                      // folder → show its contents
      state.openFolder = m.label;
      if (state.view !== "full") setView("full"); else render();
      return;
    }
    if (!m.route) { frappe.msgprint(__("This module has no page configured yet.")); return; }
    if (m.url) { setView("closed"); window.location.href = /^https?:/.test(m.url) ? m.url : window.location.origin + m.url; return; }
    state.openFolder = null;
    if (state.view === "full") setView("closed");
    var sb = frappe.app && frappe.app.sidebar;
    var target = m.sidebar;
    var hasSidebar = !!(target && sidebars()[String(target).toLowerCase()]);
    if (hasSidebar) {
      try { if (sb && sb.sidebar_title !== target) sb.setup(target); } catch (e) {}
      frappe.route_options = Object.assign({}, frappe.route_options || {}, { sidebar: target });
    }
    frappe.set_route(m.route);
    setTimeout(function () {
      try {
        if (frappe.route_options && frappe.route_options.sidebar) frappe.route_options = null;
        if (hasSidebar && sb && sb.sidebar_title !== target) sb.setup(target);
        if (sb && sb.set_active_workspace_item) sb.set_active_workspace_item();
      } catch (e) {}
      NAV.sync();
    }, 250);
  }

  // ---------- UI ----------
  function buildLauncher() {
    launcher = document.createElement("button");
    launcher.type = "button";
    launcher.className = "hs-mn-launcher hs-hidden";
    launcher.title = __("Switch module") + " (Alt+M)";
    launcher.innerHTML = SVG.grid + "<span>" + __("Modules") + '</span><span class="hs-mn-kbd">Alt+M</span>';
    launcher.addEventListener("click", function () { setView("full"); });
    document.body.appendChild(launcher);
  }

  function actions(primary) {
    var isMin = primary === "min";
    return '<div class="hs-mn-actions">' +
      '<button type="button" class="hs-mn-iconbtn" data-act="' + primary + '" title="' + (isMin ? __("Minimise") : __("Expand")) + '">' + (isMin ? SVG.min : SVG.max) + "</button>" +
      '<button type="button" class="hs-mn-iconbtn" data-act="close" title="' + __("Close") + '">' + SVG.close + "</button></div>";
  }
  function bind(el) {
    el.addEventListener("click", function (e) {
      var a = e.target.closest("[data-act]");
      if (a) {
        var act = a.getAttribute("data-act");
        if (act === "close") setView("closed");
        else if (act === "min") setView("mini");
        else if (act === "max") setView("full");
        else if (act === "back") { state.openFolder = null; render(); }
        return;
      }
      var t = e.target.closest("[data-mod]");
      if (t) open(t.getAttribute("data-mod"));
    });
    el.addEventListener("keydown", function (e) {
      var t = e.target.closest && e.target.closest("[data-mod]");
      if (t && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); open(t.getAttribute("data-mod")); }
    });
  }

  function buildPanel() {
    panel = document.createElement("div");
    panel.className = "hs-mn-panel hs-hidden";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", __("Switch Modules"));
    panel.innerHTML = '<div class="hs-mn-head"><div class="hs-mn-title">' + __("Switch Modules") + '</div><span class="hs-mn-pill"></span>' + actions("min") + "</div>" +
      '<div class="hs-mn-grid"></div>';
    document.body.appendChild(panel);
    bind(panel);
  }
  function buildMini() {
    mini = document.createElement("div");
    mini.className = "hs-mn-mini hs-hidden";
    mini.setAttribute("role", "dialog");
    mini.setAttribute("aria-label", __("Modules"));
    mini.innerHTML = '<div class="hs-mn-head"><div class="hs-mn-title">' + __("Modules") + '</div><span class="hs-mn-pill"></span>' + actions("max") + "</div>" +
      '<div class="hs-mn-strip"></div>';
    document.body.appendChild(mini);
    bind(mini);
  }

  function appTile(m, active, cur) {
    var isActive = (active && m.label === active.label) || (m.sidebar && m.sidebar === cur);
    return '<div class="hs-mn-app' + (isActive ? " is-active" : "") + '" tabindex="0" role="button" data-mod="' + esc(m.label) + '" title="' + esc(__(m.label)) + '">' +
      iconHtml(m) + '<div class="hs-mn-cap">' + esc(__(m.label)) + "</div></div>";
  }

  function render() {
    loadModules();
    var active = activeModule();
    var cur = currentLabel();
    var pill = active ? __("You are in") + " " + __(active.label) : "";
    if (panel) {
      var p = panel.querySelector(".hs-mn-pill");
      p.textContent = pill;
      p.classList.toggle("hs-hidden", !pill);
      var grid = panel.querySelector(".hs-mn-grid");
      var folder = state.openFolder && state.byLabel[state.openFolder];
      if (folder) {
        grid.innerHTML = '<div class="hs-mn-folderhead"><button type="button" data-act="back">' + SVG.back + __("All modules") + "</button>" + esc(__(folder.label)) + "</div>" +
          folder.children.map(function (c) { return appTile(c, null, cur); }).join("");
      } else {
        grid.innerHTML = state.modules.map(function (m) { return appTile(m, active, cur); }).join("") ||
          '<div class="hs-mn-sub">' + __("No modules available for your role.") + "</div>";
      }
    }
    if (mini) {
      var mp = mini.querySelector(".hs-mn-pill");
      mp.textContent = active ? __(active.label) : "";
      mp.classList.toggle("hs-hidden", !active);
      mini.querySelector(".hs-mn-strip").innerHTML = state.modules.map(function (m) {
        var isActive = active && m.label === active.label;
        return '<button type="button" class="hs-mn-dot' + (isActive ? " is-active" : "") + '" data-mod="' + esc(m.label) + '" title="' + esc(__(m.label)) + '" aria-label="' + esc(__(m.label)) + '">' + iconHtml(m) + "</button>";
      }).join("");
    }
  }

  // closed → small launcher only; full → panel; mini → slim strip (kept across page changes)
  function setView(view) {
    if (!panel) buildPanel();
    if (!mini) buildMini();
    state.view = view;
    if (view !== "full") state.openFolder = view === "closed" ? null : state.openFolder;
    lsSet("hs_mn_view", view === "full" ? "closed" : view);
    render();
    panel.classList.toggle("hs-hidden", view !== "full");
    mini.classList.toggle("hs-hidden", view !== "mini");
    launcher.classList.toggle("hs-hidden", view !== "closed");
    if (view === "full") lsSet("hs_mn_seen", "1");
  }

  NAV.open = function () { setView("full"); };
  NAV.close = function () { setView("closed"); };
  NAV.minimise = function () { setView("mini"); };
  NAV.toggle = function () { setView(state.view === "full" ? "closed" : "full"); };
  NAV.sync = function () { if (state.view !== "closed") render(); };
  NAV.destroy = function () {
    [launcher, panel, mini].forEach(function (el) { if (el && el.parentNode) el.parentNode.removeChild(el); });
    document.removeEventListener("keydown", onKey);
  };

  function onKey(e) {
    if (e.altKey && !e.ctrlKey && !e.metaKey && (e.key === "m" || e.key === "M" || e.code === "KeyM")) {
      e.preventDefault();
      NAV.toggle();
    } else if (e.key === "Escape" && state.view === "full") {
      setView("closed");
    }
  }

  function install() {
    if (!document.body || !window.frappe || !frappe.session || frappe.session.user === "Guest") return;
    document.querySelectorAll(".hs-mn-launcher,.hs-mn-panel,.hs-mn-mini").forEach(function (el) { el.remove(); });
    injectCSS();
    buildLauncher();
    document.addEventListener("keydown", onKey);
    try { frappe.router.on("change", function () { setTimeout(NAV.sync, 150); }); } catch (e) {}
    var saved = lsGet("hs_mn_view");
    if (!lsGet("hs_mn_seen")) setView("full");
    else setView(saved === "mini" ? "mini" : "closed");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
  else install();
})();
