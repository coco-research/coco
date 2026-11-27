/* Coco Research shared top bar behaviour (plan v1.3). One file, every page. No imports, no network.
   Wires, in this order, whatever the page markup provides:
     1. Products menu   [data-products-trigger] + [data-products-menu]: click toggles, Esc / outside click / link click / focus leaving closes.
     2. Phone drawer    [data-drawer-open] + dialog[data-mobile-drawer]: showModal(), [data-drawer-close], backdrop click, Esc.
     3. Theme toggle    [data-theme-toggle]: localStorage 'coco-theme', plain label swap (never aria-pressed), skipped on a locked page.
     4. Filter tabs     [data-filter-tabs] on /products/: click, arrows / Home / End, #products #lab on load and hashchange.
   The 3D Pause control ([data-motion-toggle]) belongs to product-scene.js (product pages) and main.js (home); this file only
   hides it on a page that has no 3D stage, so no dead button is shown. */
(() => {
  'use strict';
  if (window.__cocoSiteNav) return;
  window.__cocoSiteNav = true;

  const doc = document;
  const root = doc.documentElement;
  const THEME_KEY = 'coco-theme';
  // Single breakpoint shared with product-scene.js via data-mobile-max (matches @media (max-width: 860px) in CSS).
  const MOBILE_MAX = 860;
  root.dataset.mobileMax = String(MOBILE_MAX);
  const $ = (sel, scope) => (scope || doc).querySelector(sel);
  const $$ = (sel, scope) => Array.from((scope || doc).querySelectorAll(sel));

  /* ------------------------------------------------------------- theme */

  const locked = root.hasAttribute('data-theme-locked');
  let lightMq = null;
  try { lightMq = window.matchMedia('(prefers-color-scheme: light)'); } catch (e) { /* no media queries: dark */ }

  function storedTheme() {
    try {
      const v = localStorage.getItem(THEME_KEY);
      return v === 'light' || v === 'dark' ? v : null;
    } catch (e) { return null; }
  }
  function currentTheme() {
    const attr = root.getAttribute('data-theme');
    if (attr === 'light' || attr === 'dark') return attr;
    return lightMq && lightMq.matches ? 'light' : 'dark';
  }
  // Applied as early as this script runs, so a saved choice wins before the toggle is ever touched.
  if (!locked && root.getAttribute('data-theme') !== 'light' && root.getAttribute('data-theme') !== 'dark') {
    const saved = storedTheme();
    if (saved) root.setAttribute('data-theme', saved);
  }

  function syncThemeButtons() {
    const theme = currentTheme();
    $$('[data-theme-toggle]').forEach((btn) => {
      if (locked) { btn.hidden = true; return; }
      btn.textContent = theme === 'light' ? 'Dark theme' : 'Light theme'; // the label names the action, so no aria-pressed
      btn.removeAttribute('aria-pressed');
    });
    const meta = $('meta[name="theme-color"]');
    if (meta && !locked) meta.setAttribute('content', theme === 'light' ? '#f3f2ee' : '#03050b');
  }

  function wireTheme() {
    syncThemeButtons();
    if (locked) return;
    doc.addEventListener('click', (e) => {
      if (!e.target.closest || !e.target.closest('[data-theme-toggle]')) return;
      const next = currentTheme() === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem(THEME_KEY, next); } catch (err) { /* private mode: this page only */ }
      syncThemeButtons();
      try { doc.dispatchEvent(new CustomEvent('coco:themechange', { detail: { theme: next } })); } catch (err) { /* old browser */ }
    });
    if (lightMq && lightMq.addEventListener) {
      lightMq.addEventListener('change', () => { if (!root.hasAttribute('data-theme')) syncThemeButtons(); });
    }
  }

  /* ----------------------------------------------------- Products menu */

  function wireProductsMenu() {
    $$('[data-products-trigger]').forEach((trigger) => {
      const menu = doc.getElementById(trigger.getAttribute('aria-controls') || '') || $('[data-products-menu]');
      if (!menu) return;
      const bar = trigger.closest('[data-site-nav]') || doc;

      function setOpen(open) {
        menu.hidden = !open;
        trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
      }
      setOpen(false);

      trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        setOpen(menu.hidden);
      });
      doc.addEventListener('click', (e) => {
        if (menu.hidden) return;
        if (menu.contains(e.target)) { if (e.target.closest('a[href]')) setOpen(false); return; }
        if (!trigger.contains(e.target)) setOpen(false);
      });
      doc.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape' || menu.hidden) return;
        setOpen(false);
        trigger.focus();
      });
      // Keyboard focus leaving the bar (and its panel) closes the panel too.
      bar.addEventListener('focusout', (e) => {
        const to = e.relatedTarget;
        if (menu.hidden || !to) return;
        if (!bar.contains(to) && !menu.contains(to)) setOpen(false);
      });
      // The panel is a desktop control: it never shows once the bar folds into the drawer.
      try {
        window.matchMedia(`(max-width: ${MOBILE_MAX}px)`).addEventListener('change', (mq) => { if (mq.matches) setOpen(false); });
      } catch (err) { /* older Safari: the CSS already hides the panel at phone width */ }
      // Lets the drawer close the panel before it opens.
      menu._snClose = () => setOpen(false);
    });
  }

  /* ------------------------------------------------------- phone drawer */

  function wireDrawer() {
    const drawer = $('dialog[data-mobile-drawer]');
    if (!drawer) return;
    const openers = $$('[data-drawer-open]');
    const closers = $$('[data-drawer-close]', drawer);
    const canModal = typeof drawer.showModal === 'function';

    function setExpanded(open) {
      openers.forEach((b) => b.setAttribute('aria-expanded', open ? 'true' : 'false'));
    }
    function restoreFocus() {
      const back = drawer._opener;
      if (back && back.focus && doc.activeElement !== back && (!doc.activeElement || doc.activeElement === doc.body)) back.focus();
    }
    function isOpen() { return !!(drawer.open || drawer.hasAttribute('open')); }
    function open(from) {
      if (isOpen()) return;
      $$('[data-products-menu]').forEach((m) => { if (m._snClose) m._snClose(); });
      if (canModal) drawer.showModal(); else drawer.setAttribute('open', '');
      setExpanded(true);
      drawer._opener = from || null;
    }
    function close() {
      if (!isOpen()) return;
      if (typeof drawer.close === 'function' && drawer.open) drawer.close();
      else { drawer.removeAttribute('open'); setExpanded(false); restoreFocus(); }
    }

    openers.forEach((b) => b.addEventListener('click', () => open(b)));
    closers.forEach((b) => b.addEventListener('click', close));
    // The dialog element itself is the hit target of the backdrop; links inside close it on the way to the next page or section.
    drawer.addEventListener('click', (e) => {
      if (e.target === drawer || (e.target.closest && e.target.closest('a[href]'))) close();
    });
    // Esc fires the native cancel then close; fallback mode handles Esc directly.
    drawer.addEventListener('close', () => { setExpanded(false); restoreFocus(); });
    if (!canModal) doc.addEventListener('keydown', (e) => { if (e.key === 'Escape' && isOpen()) close(); });
    try {
      window.matchMedia(`(min-width: ${MOBILE_MAX + 1}px)`).addEventListener('change', (mq) => { if (mq.matches) close(); });
    } catch (err) { /* older Safari */ }
    setExpanded(false);
  }

  /* ------------------------------------------------ /products/ filter tabs */

  const STAGE_ALIAS = {
    avail: 'products', released: 'products', shipped: 'products', now: 'products', available: 'products', products: 'products',
    lab: 'lab', source: 'lab', preview: 'lab', beta: 'lab', dev: 'lab', private: 'lab', archived: 'lab', all: 'all',
  };
  function stageKey(v) { const k = String(v || '').toLowerCase(); return STAGE_ALIAS[k] || k; }

  function wireFilterTabs() {
    const list = $('[data-filter-tabs]');
    if (!list) return;
    const tabs = $$('[role="tab"][data-filter]', list);
    if (!tabs.length) return;
    const cards = $$('[data-product-card], .dir-card'); // markup may carry data-stage or data-group
    const count = $('[data-filter-count]') || $('.dir-count');
    const panel = $('[role="tabpanel"]');
    const total = cards.length;

    function labelOf(tab) { return tab.textContent.replace(/\s*\(\d+\)\s*$/, '').replace(/\s+/g, ' ').trim(); }
    function tabFor(raw) {
      const key = stageKey(raw);
      return tabs.find((t) => stageKey(t.getAttribute('data-filter')) === key) || null;
    }

    function select(tab, focus, writeHash) {
      const key = stageKey(tab.getAttribute('data-filter'));
      tabs.forEach((t) => {
        const on = t === tab;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
      });
      let shown = 0;
      cards.forEach((card) => {
        const match = key === 'all' || stageKey(card.getAttribute('data-stage') || card.getAttribute('data-group')) === key;
        card.hidden = !match;
        if (match) shown++;
      });
      if (count) count.textContent = `Showing ${shown} of ${total} products${key === 'all' ? '' : ` \u00b7 ${labelOf(tab)}`}`;
      if (panel && tab.id) panel.setAttribute('aria-labelledby', tab.id);
      if (focus) tab.focus();
      if (writeHash && window.history && history.replaceState) {
        try { history.replaceState(null, '', key === 'all' ? location.pathname + location.search : `#${key}`); } catch (err) { /* sandboxed frame */ }
      }
    }
    function fromHash() {
      const key = location.hash.replace(/^#/, '');
      return key ? tabFor(key) : null;
    }

    list.addEventListener('click', (e) => {
      const tab = e.target.closest && e.target.closest('[role="tab"][data-filter]');
      if (tab && list.contains(tab)) select(tab, false, true);
    });
    list.addEventListener('keydown', (e) => {
      let i = tabs.indexOf(doc.activeElement);
      if (i < 0) i = Math.max(0, tabs.findIndex((t) => t.getAttribute('aria-selected') === 'true'));
      const to = { ArrowRight: (i + 1) % tabs.length, ArrowLeft: (i + tabs.length - 1) % tabs.length, Home: 0, End: tabs.length - 1 }[e.key];
      if (to === undefined) return;
      e.preventDefault();
      select(tabs[to], true, true);
    });
    window.addEventListener('hashchange', () => {
      const t = fromHash() || (!location.hash ? tabs[0] : null);
      if (t) select(t, false, false);
    });

    const initial = fromHash() || tabs.find((t) => t.getAttribute('aria-selected') === 'true') || tabs[0];
    select(initial, false, false);
  }

  /* ---------------------------------------------------------- 3D control */

  function tidyMotionToggle() {
    // A page without a 3D stage has nothing to pause: no dead control.
    if (doc.getElementById('world')) return;
    $$('[data-motion-toggle]').forEach((b) => { b.hidden = true; });
  }

  function init() {
    wireTheme();
    wireProductsMenu();
    wireDrawer();
    wireFilterTabs();
    tidyMotionToggle();
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init); else init();
})();
