// Boot, scroll driver and frame loop for the cinematic page.
// Layers: static HTML/CSS (always) -> kinetic type on a scrubbed GSAP timeline -> WebGL world
// (lazy, after the intro). Each layer degrades to the one below it.
import { TL, CHAPTERS } from './layout.js';
import { createDirector } from './director.js';
import { prepare, createIntro, buildMaster } from './kinetic.js';

const root = document.documentElement;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

const lite = matchMedia('(max-width: 820px)').matches || (navigator.hardwareConcurrency || 8) <= 4;
root.classList.toggle('lite', lite);

let teardown = () => {};
wireCommon();
if (root.classList.contains('cine')) {
  if (!window.gsap || !window.ScrollTrigger) rescue('GSAP did not load');
  else {
    try { cine(); } catch (e) { console.warn('[coco] cinematic layer failed, showing the static page', e); rescue('error'); }
  }
}

/* ---------------------------------------------------- shared behaviours */

function wireCommon() {
  $$('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const label = $('span', btn) || btn;
      const status = $('[data-copy-status]');
      let ok = true;
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
      } catch (e) {
        // Clipboard API refused (insecure context, permissions): copy from a throwaway field that holds only the command.
        const ta = document.createElement('textarea');
        ta.value = btn.dataset.copy;
        ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none';
        document.body.appendChild(ta);
        ta.select();
        try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
        ta.remove();
      }
      label.textContent = ok ? 'Copied' : 'Copy failed';
      if (ok) btn.classList.add('is-copied');
      if (status) status.textContent = ok ? 'Copied to clipboard' : 'Could not copy. Select the command and copy it by hand.';
      clearTimeout(btn._t);
      btn._t = setTimeout(() => { label.textContent = 'Copy'; btn.classList.remove('is-copied'); if (status) status.textContent = ''; }, 1800);
    });
  });
  // "View plain page" skip link: remember the choice (the link itself carries ?motion=off).
  const plain = $('.skip-plain');
  if (plain) plain.addEventListener('click', () => { try { localStorage.setItem('coco-motion', 'off'); } catch (e) { /* the URL flag still applies */ } });
  const tog = $('.motion-toggle');
  // Hidden when the OS asks for reduced motion, or the viewport is too short for the stage (neither can be toggled off here).
  if (tog && !root.classList.contains('os-reduced') && !root.classList.contains('short')) {
    const isStatic = root.classList.contains('static');
    tog.hidden = false;
    tog.textContent = isStatic ? 'Restore motion' : 'Reduce motion';
    tog.addEventListener('click', () => {
      try { localStorage.setItem('coco-motion', isStatic ? 'on' : 'off'); } catch (e) { /* private mode: falls back to the URL flag */ }
      const u = new URL(location.href);
      u.searchParams.delete('motion');
      if (!isStatic) u.searchParams.set('motion', 'off');
      history.replaceState(null, '', u);
      location.reload();
    });
  }
  // The visitor changed their OS motion setting while the page was open.
  try {
    matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', () => location.reload());
  } catch (e) { /* older Safari */ }
}

function rescue(reason) {
  console.warn('[coco] cinematic layer off:', reason);
  try { teardown(); } catch (e) { /* nothing to undo */ }
  root.classList.remove('cine', 'gl', 'nogl', 'ready', 'show-cta', 'in-foot');
  root.classList.add('static', 'rescued');
  if (window.gsap) {
    window.gsap.set($$('.beat, .sw, .swi, .sc, .dgi, .win, .win *, .card, .lab-wrap, .lab-item, .hero-sub, .hero-point, .cta .btn, .meta, .copy, .ring-cap, .facts, .stat-sub, .lab-sub, .rule-eyebrow, .num, .unit, .node, .ch-close'), { clearProps: 'all' });
  }
}

/* ------------------------------------------------------------ cinematic */

function cine() {
  const g = window.gsap;
  const ST = window.ScrollTrigger;
  g.registerPlugin(ST);
  ST.config({ ignoreMobileResize: true });
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

  const canvas = $('#world');
  const spacer = $('.spacer');
  const bars = $$('.bars i');
  const railLinks = $$('.rail a');
  const nodeEls = $$('.ring .node');
  const NODE_IDX = [0, 3, 5, 8, 11, 13]; // which of the sixteen ring nodes (one per adapter) carry a label; evenly spread
  const cards = $$('.card');

  const probe = document.createElement('div');
  probe.style.cssText = 'position:fixed;top:0;left:0;width:0;height:100svh;visibility:hidden;pointer-events:none';
  document.body.appendChild(probe);

  const view = {
    lat: 1, fit: 1, portrait: innerWidth / innerHeight < 1, baseShiftY: 0, ringRadiusPx: 400,
    deck: { e0: 0, e1: 0, e2: 0, a: 0, x: 0 },
  };
  let svhPx = innerHeight;
  let director;
  function measure() {
    const w = innerWidth;
    const h = innerHeight;
    const aspect = w / h;
    view.lat = view.portrait ? clamp(aspect * 0.9 + 0.12, 0.5, 1) : 1;
    view.fit = view.portrait ? clamp(1 + (1 - aspect) * 1.15, 1, 1.9) : 1;
    const halfWin = Math.min(640, w * 0.86) / 2;
    view.ringRadiusPx = view.portrait ? Math.min(h * 0.3, 260) : Math.min(w / 2 - 74, halfWin + 130);
    svhPx = probe.offsetHeight || h;
    const lvh = canvas.clientHeight || h;
    view.baseShiftY = Math.max(0, (lvh - svhPx) / 2 / lvh);
    director = createDirector(view);
  }
  measure();

  const refs = prepare();
  const intro = createIntro(g);
  const master = buildMaster(g, refs, view);
  root.style.setProperty('--screens', String(TL.total + 1));

  // Smoothed scroll position in screens: ScrollTrigger's scrub eases it toward the real scroll.
  const prog = { v: 0 };
  const scrubTween = g.to(prog, {
    v: TL.total, ease: 'none',
    scrollTrigger: { trigger: spacer, start: 'top top', end: 'bottom bottom', scrub: lite ? 0.55 : 0.9 },
  });
  const st = scrubTween.scrollTrigger;
  const screenPx = () => spacer.offsetHeight / (TL.total + 1);

  // The footer rises over the final shot; fade the close beat as it does.
  // Once it has faded out it is also hidden, so keyboard focus can never land on an invisible button.
  const closeCh = $('.ch-close');
  g.fromTo(closeCh, { opacity: 1, y: 0 }, {
    opacity: 0, y: -50, ease: 'none',
    scrollTrigger: {
      trigger: '.foot', start: 'top 94%', end: 'top 42%', scrub: true,
      onUpdate: (self) => { closeCh.style.visibility = self.progress > 0.985 ? 'hidden' : ''; },
    },
  });
  // The footer carries its own brand lockup: hide the fixed nav one while the footer is on screen.
  ST.create({ trigger: '.foot-brand', start: 'top 75%', onEnter: () => root.classList.add('in-foot'), onLeaveBack: () => root.classList.remove('in-foot') });

  /* ---- pointer parallax + card tilt (fine pointers only) */
  const fine = matchMedia('(pointer: fine)').matches;
  const ptr = { x: 0, y: 0, tx: 0, ty: 0 };
  cards.forEach((c) => { c._rx = c._ry = c._tx = c._ty = 0; });
  if (fine) {
    addEventListener('pointermove', (e) => {
      ptr.tx = (e.clientX / innerWidth - 0.5) * 2;
      ptr.ty = -((e.clientY / innerHeight) - 0.5) * 2;
    }, { passive: true });
    cards.forEach((c) => {
      c.addEventListener('pointermove', (ev) => {
        const r = c.getBoundingClientRect();
        c._tx = ((ev.clientX - r.left) / r.width - 0.5) * 2;
        c._ty = ((ev.clientY - r.top) / r.height - 0.5) * 2;
      });
      c.addEventListener('pointerleave', () => { c._tx = c._ty = 0; });
    });
  }

  /* ---- the carousel of posters */
  const deckState = { on: false };
  let deckWasActive = false;
  function layoutDeck(s) {
    const active = s > TL.shipped[0] - 0.05 && s < TL.shipped[1] + 0.05;
    if (active !== deckState.on) { deckState.on = active; root.classList.toggle('in-shipped', active); }
    if (!active) {
      if (deckWasActive) cards.forEach((c) => { c.style.visibility = 'hidden'; c.style.opacity = '0'; });
      deckWasActive = false;
      return;
    }
    deckWasActive = true;
    const d = view.deck;
    const W = innerWidth;
    const portrait = view.portrait;
    const R = portrait ? Math.min(W * 0.66, 320) : Math.min(W * 0.4, 600);
    const spread = portrait ? 0.8 : 0.62;
    cards.forEach((c, i) => {
      const e = d['e' + i];
      const vis = e > 0.002 && d.x < 0.998;
      c.style.visibility = vis ? 'visible' : 'hidden';
      if (!vis) { c.style.opacity = '0'; return; }
      const off = i - d.a;
      const ang = off * spread;
      const inv = 1 - e;
      const side = off >= 0 ? 1 : -1;
      const x = Math.sin(ang) * R + side * 620 * inv;
      const z = (Math.cos(ang) - 1) * R - 2600 * inv;
      const y = 130 * inv - d.x * 300;
      c._rx += (c._ty * -1 - c._rx) * 0.12;
      c._ry += (c._tx - c._ry) * 0.12;
      const rotY = ang * 57.2958 + side * 38 * inv + c._ry * 7 * Math.max(0, 1 - Math.abs(off));
      const rotX = -d.x * 18 + c._rx * 6 * Math.max(0, 1 - Math.abs(off));
      const focus = Math.max(0, 1 - Math.abs(off));
      const scale = 1 + 0.06 * focus;
      c.style.transform = `translate(-50%, -50%) translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, ${z.toFixed(1)}px) rotateY(${rotY.toFixed(2)}deg) rotateX(${rotX.toFixed(2)}deg) scale(${scale.toFixed(3)})`;
      // cards stay opaque (so text never bleeds through a neighbour); side cards are darkened by an overlay instead
      c.style.opacity = String(clamp(e * 1.4, 0, 1) * (1 - d.x));
      c.style.setProperty('--dim', (Math.min(1, Math.abs(off)) * 0.3).toFixed(3)); // 0.3 keeps body text on side cards above 4.5:1
      c.style.zIndex = String(10 - Math.round(Math.min(2, Math.abs(off)) * 4));
    });
  }

  /* ---- ring labels follow their 3D nodes */
  function layoutRing(nodes, ring) {
    nodeEls.forEach((el, k) => {
      const n = nodes[NODE_IDX[k]];
      if (!n || ring < 0.01) { el.style.visibility = 'hidden'; return; }
      const d = clamp(n.depth, -1.2, 1.2);
      const sc = 1 - d * 0.16;
      const op = clamp((0.92 - d * 0.42) * clamp(ring * 1.4, 0, 1), 0, 1);
      el.style.visibility = 'visible';
      el.style.opacity = op.toFixed(3);
      el.style.zIndex = n.front ? '3' : '1';
      el.style.transform = `translate3d(${n.x.toFixed(1)}px, ${n.y.toFixed(1)}px, 0) translate(-50%, -50%) scale(${sc.toFixed(3)})`;
    });
  }

  /* ---- page chrome driven by scroll */
  const chrome = { cta: false, idx: -1, bars: -1 };
  function updateChrome(s, P) {
    const cta = s > 1.15;
    if (cta !== chrome.cta) { chrome.cta = cta; root.classList.toggle('show-cta', cta); }
    let idx = 0;
    for (let i = 0; i < CHAPTERS.length; i++) if (s >= CHAPTERS[i].at - 0.001) idx = i;
    if (idx !== chrome.idx) {
      chrome.idx = idx;
      railLinks.forEach((a, i) => { a.classList.toggle('on', i === idx); if (i === idx) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    }
    if (bars.length && Math.abs(P.bars - chrome.bars) > 0.002) {
      chrome.bars = P.bars;
      const t = 'scaleY(' + P.bars.toFixed(3) + ')';
      bars[0].style.transform = t;
      bars[1].style.transform = t;
    }
  }

  /* ---- the 3D world (lazy) */
  let world = null;
  let dpr = Math.min(devicePixelRatio || 1, lite ? 1.5 : 2);
  function resizeWorld() {
    if (!world) return;
    world.resize(canvas.clientWidth, canvas.clientHeight, dpr, svhPx);
  }
  // Quality governor: if frames are slow (software rendering, old phones), step the resolution down fast.
  const dprParam = parseFloat(new URLSearchParams(location.search).get('dpr'));
  if (dprParam > 0) dpr = clamp(dprParam, 0.3, 3); // ?dpr=0.5 pins the resolution (debugging)
  const gov = { t0: 0, n: 0, calm: 0, last: 0, on: !(dprParam > 0) };
  function govern(now) {
    if (!gov.on || document.visibilityState !== 'visible') return;
    if (gov.last && now - gov.last > 400) gov.t0 = 0; // tab was hidden: restart the window
    gov.last = now;
    if (!gov.t0) { gov.t0 = now; gov.n = 0; return; }
    gov.n++;
    const el = now - gov.t0;
    if (gov.n < 6 && el < 1500) return;
    const avg = el / gov.n;
    gov.t0 = now;
    gov.n = 0;
    if (avg > 30 && dpr > 0.55) { dpr = Math.max(0.5, dpr * (avg > 80 ? 0.55 : 0.75)); resizeWorld(); gov.calm = 0; }
    else if (++gov.calm >= 5) gov.on = false;
  }

  function startWorld(mod) {
    const w = mod.createWorld({
      canvas, lite,
      onLost: () => { world = null; root.classList.remove('gl'); root.classList.add('nogl'); },
    });
    if (!w) { console.warn('[coco] WebGL unavailable, keeping the 2D point of light'); root.classList.add('nogl'); return; }
    world = w;
    resizeWorld();
    root.classList.remove('nogl');
    root.classList.add('gl');
  }

  /* ---- frame loop */
  const nodesDefault = [];
  let forced = null; // test hook: pin the story position until the visitor scrolls
  function frame(time) {
    const s = forced != null ? forced : prog.v;
    master.time(s, false);
    const P = director(s);
    updateChrome(s, P);
    layoutDeck(s);
    if (fine) { ptr.x += (ptr.tx - ptr.x) * 0.05; ptr.y += (ptr.ty - ptr.y) * 0.05; }
    if (world) {
      const nodes = world.update(P, time, ptr, view) || nodesDefault;
      layoutRing(nodes, P.ring);
      govern(performance.now());
    }
  }
  g.ticker.add(frame);

  /* ---- travel: anchors fly the camera instead of jumping */
  let travelTween = null;
  const stopTravel = () => { if (travelTween) { travelTween.kill(); travelTween = null; } };
  function travel(id) {
    const ch = CHAPTERS.find((c) => c.id === id) || CHAPTERS[0];
    const target = Math.round(ch.stop * screenPx());
    const from = window.scrollY;
    const dist = Math.abs(target - from);
    if (dist < 4) return;
    stopTravel();
    const o = { y: from };
    travelTween = g.to(o, {
      y: target, duration: clamp(0.9 + (dist / screenPx()) * 0.17, 1.1, 3.4), ease: 'power3.inOut',
      onUpdate: () => window.scrollTo(0, o.y), onComplete: () => { travelTween = null; },
    });
  }
  $$('[data-goto]').forEach((a) => a.addEventListener('click', (e) => {
    e.preventDefault();
    travel(a.dataset.goto);
    history.replaceState(null, '', '#' + a.dataset.goto);
  }));
  ['wheel', 'touchstart', 'keydown'].forEach((t) => addEventListener(t, stopTravel, { passive: true }));
  ['wheel', 'touchstart', 'keydown'].forEach((t) => addEventListener(t, () => { if (forced != null) { prog.v = forced; forced = null; } }, { passive: true }));

  /* ---- resize: re-measure; flipping orientation rebuilds the whole timeline */
  let lastW = innerWidth;
  let lastH = innerHeight;
  let rz;
  addEventListener('resize', () => {
    clearTimeout(rz);
    rz = setTimeout(() => {
      const wChanged = innerWidth !== lastW;
      if (!wChanged && Math.abs(innerHeight - lastH) < 140) return; // mobile toolbar, not a real resize
      lastW = innerWidth;
      lastH = innerHeight;
      if ((innerWidth / innerHeight < 1) !== view.portrait) { location.reload(); return; }
      measure();
      resizeWorld();
      ST.refresh();
    }, 160);
  });

  teardown = () => {
    g.ticker.remove(frame);
    ST.getAll().forEach((t) => t.kill());
    master.kill();
    probe.remove();
  };

  /* ---- go */
  root.classList.add('ready');
  const introDone = new Promise((res) => { intro.eventCallback('onComplete', res); });
  intro.play();
  const afterPaint = (fn) => requestAnimationFrame(() => requestAnimationFrame(() => {
    if ('requestIdleCallback' in window) requestIdleCallback(fn, { timeout: 1500 }); else setTimeout(fn, 300);
  }));
  afterPaint(() => {
    const wait = new Promise((res) => setTimeout(res, 3600));
    Promise.all([import('./world.js'), Promise.race([introDone, wait])])
      .then(([mod]) => startWorld(mod))
      .catch((e) => { console.warn('[coco] 3D layer unavailable, continuing without it', e); root.classList.add('nogl'); });
  });

  if (location.hash && CHAPTERS.some((c) => '#' + c.id === location.hash)) {
    const id = location.hash.slice(1);
    setTimeout(() => travel(id), 400);
  }

  // Test and debugging hook: jump straight to a point in the story (in screens), render
  // synchronously, and time frames (handy when the browser throttles requestAnimationFrame).
  window.__cine = {
    jump(s) {
      forced = s;
      window.scrollTo(0, Math.round(s * screenPx()));
      frame(g.ticker.time);
    },
    release() { if (forced != null) { prog.v = forced; forced = null; } },
    step() { frame(g.ticker.time); },
    async boot3d() { if (!world) startWorld(await import('./world.js')); return !!world; },
    finishIntro() { intro.progress(1); },
    timeFrames(n = 5) {
      if (!world) return null;
      const gl = world.gl;
      const px = new Uint8Array(4);
      const t0 = performance.now();
      for (let i = 0; i < n; i++) { frame(g.ticker.time + i / 60); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); }
      return (performance.now() - t0) / n;
    },
    get screens() { return prog.v; },
    get world() { return world; },
    get dpr() { return dpr; },
    view, TL,
  };
}
