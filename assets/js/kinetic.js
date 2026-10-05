// Kinetic typography. Every text beat is a tween on one master timeline measured in
// "screens" of scroll, so type and camera can never drift out of sync, and scrubbing
// back is as exact as scrubbing forward.
import { TL } from './layout.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

/* ------------------------------------------------------------- splitting */

// Wraps words (and optionally characters) in spans. The original text stays available to
// assistive tech through a visually hidden copy; the animated spans are aria-hidden.
export function split(el, mode = 'words', mask = false) {
  const label = el.textContent.replace(/\s+/g, ' ').trim();
  const wrap = document.createElement('span');
  wrap.setAttribute('aria-hidden', 'true');
  while (el.firstChild) wrap.appendChild(el.firstChild);
  const sr = document.createElement('span');
  sr.className = 'sr-only';
  sr.textContent = label;
  el.append(sr, wrap);
  const out = { words: [], inner: [], chars: [] };
  const walk = (node) => {
    Array.from(node.childNodes).forEach((n) => {
      if (n.nodeType === 3) {
        const frag = document.createDocumentFragment();
        n.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); return; }
          const w = document.createElement('span');
          w.className = 'sw' + (mask ? ' m' : '');
          if (mode === 'chars') {
            Array.from(part).forEach((ch) => {
              const c = document.createElement('span');
              c.className = 'sc';
              c.textContent = ch;
              w.appendChild(c);
              out.chars.push(c);
            });
          } else {
            const i = document.createElement('span');
            i.className = 'swi';
            i.textContent = part;
            w.appendChild(i);
            out.inner.push(i);
          }
          out.words.push(w);
          frag.appendChild(w);
        });
        n.replaceWith(frag);
      } else if (n.nodeType === 1) walk(n);
    });
  };
  walk(wrap);
  return out;
}

// Digits as vertical strips (0-9 twice) so each one can roll like an odometer.
export function odometer(numEl) {
  const target = numEl.dataset.count || numEl.textContent.trim();
  numEl.textContent = '';
  const sr = document.createElement('span');
  sr.className = 'sr-only';
  sr.textContent = target;
  const wrap = document.createElement('span');
  wrap.setAttribute('aria-hidden', 'true');
  wrap.style.display = 'inline-flex';
  const cols = [];
  Array.from(target).forEach((ch) => {
    const dg = document.createElement('span');
    dg.className = 'dg';
    const inner = document.createElement('span');
    inner.className = 'dgi';
    for (let i = 0; i < 20; i++) {
      const b = document.createElement('b');
      b.textContent = String(i % 10);
      inner.appendChild(b);
    }
    dg.appendChild(inner);
    wrap.appendChild(dg);
    cols.push({ el: inner, to: Number(ch) + 10 });
  });
  numEl.append(sr, wrap);
  return cols;
}

/* --------------------------------------------------------------- prepare */

export function prepare() {
  const refs = {};
  refs.heroWords = split($('.b-hero h1'), 'words').inner;
  refs.lede = split($('.b-hero .lede'), 'words').inner;
  refs.title = split($('.b-title h2'), 'chars');
  refs.argue = split($('.b-argue .statement'), 'words');
  refs.cmd = split($('.code .cmd'), 'chars');
  refs.rules = $$('.b-rule').map((beat, i) => {
    const h = $('h3', beat);
    const mode = i === 2 ? 'chars' : 'words';
    const s = split(h, mode, i === 0 || i === 2);
    return { beat, h, line: $('.rule-line', beat), eyebrow: $('.rule-eyebrow', beat), ...s };
  });
  refs.close = split($('.b-close h2'), 'chars');
  refs.odo = { experts: odometer($('.b-experts .num')), depts: odometer($('.b-depts .num')) };
  return refs;
}

/* ---------------------------------------------------------- hero intro */

// Time-based (not scrubbed): the headline pulls into focus word by word under the point of light.
export function createIntro(gsap) {
  const tl = gsap.timeline({ paused: true });
  tl.fromTo($$('.b-hero h1 .swi'), { opacity: 0, filter: 'blur(18px)', y: 34, scale: 1.14 },
    { opacity: 1, filter: 'blur(0px)', y: 0, scale: 1, duration: 1.5, ease: 'expo.out', stagger: 0.12 }, 0);
  tl.fromTo($$('.b-hero .lede .swi'), { opacity: 0, y: 10 },
    { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out', stagger: 0.018 }, 0.8);
  tl.fromTo($$('.b-hero .cta .btn'), { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.9, ease: 'expo.out', stagger: 0.1 }, 1.3);
  tl.fromTo('.b-hero .meta', { opacity: 0 }, { opacity: 1, duration: 1.0, ease: 'power2.out' }, 1.7);
  return tl;
}

/* -------------------------------------------------------- master timeline */

export function buildMaster(gsap, refs, view) {
  const tl = gsap.timeline({ paused: true, defaults: { ease: 'none' } });
  // fromTo with explicit start values: deterministic in both scrub directions.
  // The FIRST tween on an element's property also applies its start value up front, and again whenever the playhead
  // returns before it (GSAP does not do that for immediateRender:false). Without it, anything that animates in after
  // its beat appeared (stagger tails, list items) sat at full opacity until its own tween began, on the first scroll
  // and again after scrolling back. Later tweens on the same property must not render early, or they would
  // overwrite the earlier state.
  const seen = new Map();
  const key = (p) => (p === 'autoAlpha' ? 'opacity' : p);
  const ft = (targets, from, to, at) => {
    const els = gsap.utils.toArray(targets);
    const props = Object.keys(from).map(key);
    let fresh = 0;
    els.forEach((el) => {
      let set = seen.get(el);
      if (!set) seen.set(el, (set = new Set()));
      props.forEach((p) => { if (!set.has(p)) fresh++; set.add(p); });
    });
    to.immediateRender = fresh === els.length * props.length;
    return tl.fromTo(targets, from, to, at);
  };
  const show = (el, t) => ft(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001 }, t);
  const hide = (el, t) => ft(el, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001 }, t);
  // Rule for scrubbing back: never pair show()/hide() with a separate opacity tween on the same element.
  // The element's fade-out is one autoAlpha tween (it ends hidden), so rewinding restores both opacity and visibility.
  const dur = (r) => r[1] - r[0];

  gsap.set($$('.beat'), { autoAlpha: 0 });
  gsap.set($('.b-hero'), { autoAlpha: 1 });

  /* 1. Hero exits as the camera pushes toward the point. */
  const he = TL.hero.exit;
  ft($$('.b-hero h1 .sw'), { opacity: 1, scale: 1, filter: 'blur(0px)', yPercent: 0 },
    { opacity: 0, scale: 1.7, filter: 'blur(22px)', yPercent: -16, duration: 0.55, ease: 'power2.in', stagger: { each: 0.045, from: 'center' } }, he[0]);
  ft('.hero-sub', { opacity: 1, y: 0 }, { opacity: 0, y: 56, duration: 0.42, ease: 'power2.in' }, he[0] - 0.06);
  hide($('.b-hero'), he[1] + 0.3);
  ft('.hero-point', { scale: 1 }, { scale: 2.6, duration: 1.0, ease: 'power2.in' }, 0.5);

  /* 2a. Title: letters pull together, then the camera flies through them. */
  const [ti0, ti1] = TL.title.in;
  const [to0, to1] = TL.title.out;
  const tc = refs.title.chars;
  show($('.b-title'), ti0);
  ft(tc, { opacity: 0, filter: 'blur(10px)', x: (i, el, list) => (i - (list.length - 1) / 2) * 7 },
    { opacity: 1, filter: 'blur(0px)', x: 0, duration: ti1 - ti0, ease: 'expo.out', stagger: { amount: (ti1 - ti0) * 0.45, from: 'center' } }, ti0);
  ft('.b-title', { scale: 1, filter: 'blur(0px)' }, { scale: 3.4, filter: 'blur(16px)', duration: to1 - to0, ease: 'power2.in' }, to0);
  ft('.b-title', { autoAlpha: 1 }, { autoAlpha: 0, duration: (to1 - to0) * 0.55, ease: 'power1.in' }, to0 + (to1 - to0) * 0.45);

  /* 2b/2c. 495 experts. 13 departments. Digits roll, the word slides in, then it flies past. */
  const stat = (sel, key, win, dir) => {
    const beat = $(sel);
    const [i0, i1] = win.in;
    const [o0, o1] = win.out;
    const cols = refs.odo[key];
    show(beat, i0);
    ft(cols.map((c) => c.el), { yPercent: 0 },
      { yPercent: (i) => -cols[i].to * 5, duration: dur(win.in) + 0.35, ease: 'power3.out', stagger: 0.07 }, i0);
    ft($('.num', beat), { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }, i0);
    ft($('.unit', beat), { opacity: 0, x: 60 * dir, filter: 'blur(10px)' },
      { opacity: 1, x: 0, filter: 'blur(0px)', duration: dur(win.in) * 0.9, ease: 'expo.out' }, i0 + 0.12);
    const sub = $('.stat-sub', beat);
    if (sub) ft(sub, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out' }, i0 + 0.3);
    ft(beat, { scale: 1, xPercent: 0, filter: 'blur(0px)' }, { scale: 2.3, xPercent: -18 * dir, filter: 'blur(14px)', duration: o1 - o0, ease: 'power2.in' }, o0);
    ft(beat, { autoAlpha: 1 }, { autoAlpha: 0, duration: (o1 - o0) * 0.55, ease: 'power1.in' }, o0 + (o1 - o0) * 0.45);
  };
  stat('.b-experts', 'experts', TL.experts, 1);
  stat('.b-depts', 'depts', TL.depts, -1);

  /* 2d. They argue, name who disagrees, and the skills ship the decision. */
  const [a0, a1] = TL.argue.in;
  const [ao0, ao1] = TL.argue.out;
  const argue = $('.b-argue');
  show(argue, a0);
  ft(refs.argue.inner, { opacity: 0.0, y: 16, filter: 'blur(6px)' },
    { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.4, ease: 'power2.out', stagger: { amount: dur(TL.argue.in) - 0.4 } }, a0);
  ft($$('mark .swi', argue), { color: '#eef2fb' }, { color: '#ffb66e', duration: 0.3, ease: 'power1.out' }, a1 - 0.15);
  ft(argue, { y: 0, autoAlpha: 1 }, { y: -70, autoAlpha: 0, duration: ao1 - ao0, ease: 'power2.in' }, ao0);

  /* 2e. The point unfolds into an editor window; the ring of adapters orbits it. */
  const ed = TL.editor;
  const editor = $('.b-editor');
  const win = $('.win');
  const [u0, u1] = ed.unfold;
  const ud = u1 - u0;
  show(editor, u0);
  gsap.set(win, { transformPerspective: 1400, transformOrigin: '50% 50%' });
  ft(win, { opacity: 0 }, { opacity: 1, duration: 0.12 * ud, ease: 'power1.out' }, u0);
  ft(win, { scaleX: 0.01 }, { scaleX: 1, duration: 0.55 * ud, ease: 'expo.out' }, u0 + 0.04 * ud);
  ft(win, { scaleY: 0.012, rotateX: -62 }, { scaleY: 1, rotateX: 0, duration: 0.55 * ud, ease: 'expo.inOut' }, u0 + 0.42 * ud);
  ft($$('.win-bar, .win-body > *'), { opacity: 0 }, { opacity: 1, duration: 0.3 * ud, ease: 'power1.out', stagger: 0.02 }, u0 + 0.74 * ud);
  ft(refs.cmd.chars, { opacity: 0 }, { opacity: 1, duration: 0.02, stagger: { amount: dur(ed.install) * 0.8 } }, ed.install[0]);
  ft('.copy', { opacity: 0 }, { opacity: 1, duration: 0.15 }, ed.install[1] - 0.1);
  ft('.ring-cap', { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }, ed.install[0] + 0.1);
  ft('.facts', { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }, ed.facts[0]);
  // collapse back into a point as the camera flies through it
  const [c0, c1] = ed.collapse;
  ft('.ring-cap, .facts', { opacity: 1 }, { opacity: 0, duration: 0.18, ease: 'power1.in' }, c0 - 0.1);
  ft(win, { scaleY: 1, rotateX: 0 }, { scaleY: 0.012, rotateX: 62, duration: 0.5 * (c1 - c0), ease: 'expo.in' }, c0);
  ft(win, { scaleX: 1 }, { scaleX: 0.01, duration: 0.5 * (c1 - c0), ease: 'expo.in' }, c0 + 0.38 * (c1 - c0));
  ft(win, { opacity: 1 }, { opacity: 0, duration: 0.4 * (c1 - c0), ease: 'power1.in' }, c0 + 0.1 * (c1 - c0));
  hide(editor, c1 + 0.01);

  /* 3. Four rules, four different motions. */
  const R = TL.rules;
  refs.rules.forEach((r, i) => {
    const [b0, b1] = R[i];
    const o0 = b1 - 0.24;
    show(r.beat, b0);
    ft(r.line, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.34, ease: 'power3.out' }, b0 + 0.26);
    ft(r.eyebrow, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.3, ease: 'power3.out' }, b0 + 0.04);
    const last = i === R.length - 1;
    if (i === 0) {
      // Data stays local: words rise out of a mask, then draw back in toward the left edge.
      gsap.set(r.h, { transformOrigin: '0% 50%' });
      ft(r.inner, { yPercent: 112, rotate: 3 }, { yPercent: 0, rotate: 0, duration: 0.42, ease: 'expo.out', stagger: 0.05 }, b0);
      ft(r.h, { scale: 1, opacity: 1, filter: 'blur(0px)' }, { scale: 0.9, opacity: 0, filter: 'blur(9px)', duration: 0.24, ease: 'power2.in' }, o0);
    } else if (i === 1) {
      // Verify, don't average: two halves come from opposite sides and meet; they part again cleanly.
      const w = r.words;
      ft(w[0], { x: -150, opacity: 0 }, { x: 0, opacity: 1, duration: 0.42, ease: 'expo.out' }, b0);
      ft(w.slice(1), { x: 150, opacity: 0 }, { x: 0, opacity: 1, duration: 0.42, ease: 'expo.out', stagger: 0.04 }, b0);
      ft(w[0], { x: 0, opacity: 1 }, { x: -110, opacity: 0, duration: 0.24, ease: 'power2.in' }, o0);
      ft(w.slice(1), { x: 0, opacity: 1 }, { x: 110, opacity: 0, duration: 0.24, ease: 'power2.in' }, o0);
    } else if (i === 2) {
      // Stage is stated plainly: letter by letter, no flourish.
      ft(r.chars, { yPercent: 104 }, { yPercent: 0, duration: 0.36, ease: 'expo.out', stagger: { amount: 0.2 } }, b0);
      ft(r.chars, { yPercent: 0 }, { yPercent: -104, duration: 0.3, ease: 'power2.in', stagger: { amount: 0.14 } }, o0);
    } else {
      // Credit travels with the code: the line itself travels across.
      ft(r.words, { x: 180, opacity: 0 }, { x: 0, opacity: 1, duration: 0.42, ease: 'expo.out', stagger: 0.05 }, b0);
      if (!last) ft(r.words, { x: 0, opacity: 1 }, { x: -220, opacity: 0, duration: 0.3, ease: 'power2.in', stagger: 0.05 }, o0);
    }
    ft(r.line, { opacity: 1, y: 0 }, { opacity: 0, y: -12, duration: 0.2, ease: 'power2.in' }, o0 + 0.02);
    ft(r.eyebrow, { opacity: 1, y: 0 }, { opacity: 0, y: -8, duration: 0.2, ease: 'power2.in' }, o0 + 0.02);
    if (last) {
      // the last rule travels on out of frame as the shape disperses; it is gone before "Shipped." comes in
      ft(r.words, { x: 0, opacity: 1 }, { x: -260, opacity: 0, duration: 0.34, ease: 'power2.in', stagger: 0.03 }, o0 - 0.02);
    }
    hide(r.beat, b1 + (last ? 0.2 : 0.02));
  });

  /* 4. Shipped: heading, then a carousel of posters, one per shipped product flying in from depth. */
  const [s0, s1] = TL.shipped;
  const head = $('.b-shipped');
  show(head, s0 + 0.2);
  ft($('.b-shipped h2'), { opacity: 0, y: 34, filter: 'blur(10px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.5, ease: 'expo.out' }, s0 + 0.2);
  ft($('.b-shipped h2'), { opacity: 1, y: 0 }, { opacity: 0, y: -26, duration: 0.3, ease: 'power2.in' }, s1 - 0.34);
  hide(head, s1 - 0.03);
  const deck = view.deck;
  // One poster per product row in data/products.json. layoutDeck (main.js) reads deck['e' + i] for every card; each e{k}
  // exists because this is the first tween on it (ft renders immediately), so keep exactly one ft per e{k}.
  const n = document.querySelectorAll('.card').length;
  const step = Math.min(0.24, (s1 - 0.6 - (s0 + 1.06)) / Math.max(1, n - 1)); // every entrance lands before the exit at s1 - 0.6
  for (let k = 0; k < n; k++) ft(deck, { ['e' + k]: 0 }, { ['e' + k]: 1, duration: 0.8, ease: 'expo.out' }, s0 + 0.26 + k * step);
  ft(deck, { a: 0 }, { a: n - 1, duration: 1.7, ease: 'none' }, s0 + 1.1); // opens on the flagship, ends on the last card
  ft(deck, { x: 0 }, { x: 1, duration: 0.55, ease: 'power2.in' }, s1 - 0.6);

  /* 5. In the lab: a calm list, each item drifting in. */
  const [l0, l1] = TL.lab;
  const lab = $('.lab-wrap');
  show(lab, l0 - 0.04);
  ft($('.lab-head'), { opacity: 0, y: 30, filter: 'blur(10px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.55, ease: 'power3.out' }, l0 - 0.02);
  ft($('.lab-sub'), { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }, l0 + 0.3);
  $$('.lab-item').forEach((it, i) => {
    ft(it, { opacity: 0, y: 46, filter: 'blur(8px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.6, ease: 'power3.out' }, l0 + 0.28 + i * 0.26);
  });
  // The list stays readable until the close title is already arriving (no empty beat between them).
  ft(lab, { y: 0, autoAlpha: 1 }, { y: -36, autoAlpha: 0, duration: 0.36, ease: 'power2.in' }, l1 - 0.3);

  /* 6. Close: the title card, the credit, the button. */
  const [x0] = TL.close;
  const close = $('.b-close');
  show(close, x0 - 0.1);
  ft(refs.close.chars, { opacity: 0, y: 26, filter: 'blur(10px)' },
    { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.5, ease: 'expo.out', stagger: { amount: 0.45, from: 'center' } }, x0 - 0.1);
  ft('.credit', { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }, x0 + 0.4);
  ft('.b-close .btn', { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.45, ease: 'expo.out' }, x0 + 0.6);

  tl.set({}, {}, TL.total); // pad the end so time() maps 1:1 to screens
  tl.render(0, true, true); // apply every start state before the first frame
  return tl;
}
