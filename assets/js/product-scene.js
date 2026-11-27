// Shared 3D Three.js stage for Coco Research product pages.
// ES module: loaded with type="module"; top-level names are module-scoped.
// Uses the same point, hairline and anamorphic flare language as world.js,
// rendered in Signal Dark (#03050b / #2f4bff) and Signal Light (#f3f2ee / #1234ff)
// with zero runtime network requests beyond the pinned three.js module.
// Three.js and the motifs load with dynamic import() AFTER every UI control is wired,
// so a blocked CDN never disables the theme, motion, drawer or copy controls.

function buildDust(count, mulberry32) {
  const rand = mulberry32(41), pos = new Float32Array(count * 3), sd = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    pos.set([(rand() * 2 - 1) * 28, (rand() * 2 - 1) * 18, 6 - rand() * 44], i * 3);
    sd.set([rand(), rand(), 0.9 + rand() * 0.8], i * 3);
  }
  return { pos, sd };
}

const BG_VERT = `varying vec2 vUv; void main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.9999, 1.0); }`;
const BG_FRAG = `
precision highp float; varying vec2 vUv; uniform float uTime, uAspect, uLight; uniform vec2 uGlowPos;
float ign(vec2 p) { return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }
void main() {
  vec2 g = (vUv - uGlowPos) * vec2(uAspect, 1.0);
  float halo = exp(-dot(g, g) * 6.0), core = exp(-dot(g, g) * 18.0);
  vec3 darkBase = mix(vec3(0.010, 0.016, 0.038), vec3(0.018, 0.029, 0.068), vUv.y);
  vec3 darkCol = darkBase + vec3(0.045, 0.095, 0.30) * halo + vec3(0.07, 0.14, 0.42) * core;
  vec3 lightCol = mix(vec3(0.953, 0.949, 0.933), vec3(0.872, 0.898, 0.992), halo * 0.55 + core * 0.25);
  vec3 col = mix(darkCol, lightCol, uLight) + (ign(gl_FragCoord.xy + fract(uTime) * 73.0) - 0.5) * (1.5 / 255.0);
  gl_FragColor = vec4(col, 1.0);
}`;

const POINT_FRAG = `
precision highp float; uniform float uLight; varying vec3 vCol; varying float vA;
void main() {
  vec2 c = (gl_PointCoord - 0.5) * 2.0; float r2 = dot(c, c);
  float core = exp(-r2 * 22.0), halo = exp(-r2 * 4.8) * 0.38, al = vA * (core + halo);
  if (al < 0.004) discard;
  if (uLight > 0.5) gl_FragColor = vec4(mix(vCol, vec3(0.024, 0.068, 0.240), core * 0.52), clamp(al * 1.28, 0.0, 0.96));
  else gl_FragColor = vec4(vCol * (0.58 + core * 0.92), al);
}`;

const MORPH_GLSL = `
vec2 rot2(vec2 v, float a) { float c = cos(a), s = sin(a); return vec2(c * v.x - s * v.y, s * v.x + c * v.y); }
vec3 pick(float i) { if (i < 0.5) return aT0; if (i < 1.5) return aT1; return aT2; }
vec3 morphPos(out float e, out float w0) {
  float m = clamp(uMorph, 0.0, 2.0), i0 = floor(min(m, 1.9999)), f = m - i0;
  e = f * f * (3.0 - 2.0 * f); w0 = max(0.0, 1.0 - m);
  return mix(pick(i0), pick(i0 + 1.0), e);
}`;

const SHAPE_VERT = `
attribute vec3 aT0, aT1, aT2; attribute vec4 aSeed;
uniform float uMorph, uTime, uPx, uCamRef, uMaxPt, uLight, uSpinY, uSpinX, uPulse;
varying vec3 vCol; varying float vA;
${MORPH_GLSL}
void main() {
  float e, w0; vec3 p = morphPos(e, w0);
  p.y *= 1.0 + 0.13 * uPulse * sin(uTime * 2.1 + aSeed.y * 10.0) * w0;
  p += vec3(cos(aSeed.x * 18.0 + uTime), sin(aSeed.z * 14.0 + uTime), cos(aSeed.y * 16.0)) * sin(3.14159265 * e) * 1.15;
  p.xz = rot2(p.xz, uSpinY); p.yz = rot2(p.yz, uSpinX);
  vec4 mv = modelViewMatrix * vec4(p, 1.0); float dist = max(-mv.z, 0.1);
  float ambDark = step(0.93, aSeed.w), ambLight = step(0.988, aSeed.w);
  vec3 darkC = mix(mix(vec3(0.50, 0.70, 1.0), vec3(0.94, 0.97, 1.0), aSeed.z), vec3(1.0, 0.70, 0.34), ambDark);
  vec3 lightC = mix(mix(vec3(0.071, 0.204, 1.0), vec3(0.035, 0.105, 0.380), aSeed.z), vec3(0.72, 0.34, 0.0), ambLight);
  vCol = mix(darkC, lightC, uLight);
  vA = (0.88 + 0.12 * sin(uTime * 1.5 + aSeed.x * 40.0)) * (1.0 + mix(ambDark, ambLight, uLight) * 0.35);
  gl_PointSize = clamp((2.8 + aSeed.z * 2.9) * uPx * (uCamRef / dist), 1.2, uMaxPt);
  gl_Position = projectionMatrix * mv;
}`;

const WIRE_VERT = `
attribute vec3 aT0, aT1, aT2; uniform float uMorph, uTime, uSpinY, uSpinX, uPulse; varying float vA;
${MORPH_GLSL}
void main() {
  float e, w0; vec3 p = morphPos(e, w0);
  p.y *= 1.0 + 0.13 * uPulse * sin(uTime * 2.1 + (p.x * 0.18 + 0.5) * 10.0) * w0;
  p.xz = rot2(p.xz, uSpinY); p.yz = rot2(p.yz, uSpinX);
  vA = 1.0 - sin(3.14159265 * e) * 0.65;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
}`;
const WIRE_FRAG = `
precision highp float; uniform float uLight; varying float vA;
void main() { gl_FragColor = vec4(mix(vec3(0.56, 0.74, 1.0), vec3(0.071, 0.204, 1.0), uLight), vA * mix(0.32, 0.34, uLight)); }`;

const DUST_VERT = `
attribute vec3 aSD; uniform float uTime, uPx, uLight, uMaxPt; varying vec3 vCol; varying float vA;
void main() {
  vec3 p = position + vec3(sin(uTime * 0.12 + aSD.x * 24.0), cos(uTime * 0.10 + aSD.y * 24.0), 0.0) * 0.45;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vCol = mix(vec3(0.56, 0.73, 1.0), vec3(0.071, 0.204, 1.0), uLight);
  vA = mix(0.42, 0.18, uLight) * (0.5 + 0.5 * sin(uTime * 0.8 + aSD.y * 30.0));
  gl_PointSize = clamp((1.5 + aSD.x * 1.8) * uPx * (24.0 / max(-mv.z, 0.1)), 1.0, uMaxPt);
  gl_Position = projectionMatrix * mv;
}`;

const FLARE_VERT = `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const GLOW_FRAG = `
precision highp float; uniform float uLight; varying vec2 vUv;
void main() {
  vec2 w = (vUv - 0.5) * 16.0; float r2 = dot(w, w);
  float core = exp(-r2 * 6.2), glow = exp(-r2 * 0.28) * 0.50;
  float edge = (1.0 - smoothstep(5.5, 8.0, abs(w.x))) * (1.0 - smoothstep(5.5, 8.0, abs(w.y)));
  if (uLight > 0.5) gl_FragColor = vec4(mix(vec3(0.071, 0.204, 1.0), vec3(0.02, 0.06, 0.24), core * 0.35), clamp((core * 0.88 + glow * 0.36) * edge, 0.0, 0.92));
  else gl_FragColor = vec4((vec3(0.36, 0.55, 1.0) * glow + vec3(1.0) * core) * edge, 1.0);
}`;
const STREAK_FRAG = `
precision highp float; uniform float uLight; varying vec2 vUv;
void main() {
  vec2 w = (vUv - 0.5) * vec2(32.0, 4.0);
  float sx = exp(-abs(w.y) * 5.2) * exp(-abs(w.x) * 0.24);
  float sx2 = exp(-abs(w.y) * 13.5) * exp(-abs(w.x) * 0.16);
  float edge = (1.0 - smoothstep(10.5, 16.0, abs(w.x))) * (1.0 - smoothstep(1.2, 2.0, abs(w.y)));
  float rightHalf = smoothstep(0.30, 0.62, vUv.x);
  if (uLight > 0.5) gl_FragColor = vec4(vec3(0.071, 0.204, 1.0), clamp((sx * 0.30 + sx2 * 0.34) * edge * rightHalf, 0.0, 0.7));
  else gl_FragColor = vec4((vec3(0.36, 0.55, 1.0) * sx * 0.72 + vec3(1.0) * sx2 * 0.52) * edge, 1.0);
}`;

// The shared top bar (site-nav.js) owns theme storage, theme resolution, theme toggles, and meta[name="theme-color"].
// This file reads window.cocoTheme.current() and owns the 3D Pause control.
const resolveTheme = () => (window.cocoTheme ? window.cocoTheme.current() : 'dark');

// Per-page 3D pause: scoped to this pathname in sessionStorage so pausing /voice/ never touches / or other pages.
const PAUSE_KEY = 'coco-3d-pause:' + location.pathname;
function readPaused() {
  let stored = null;
  try { stored = sessionStorage.getItem(PAUSE_KEY); } catch (e) { /* private mode / storage blocked */ }
  if (stored === '1') return true;
  if (stored === '0') return false;
  try { return matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
}
function writePaused(paused) {
  try { sessionStorage.setItem(PAUSE_KEY, paused ? '1' : '0'); } catch (e) { /* private mode: this tab only */ }
}

// Labels swap text only (no aria-pressed): WCAG 2.2.2 pause control and a label that changes with state.
function syncButtons(paused) {
  document.querySelectorAll('[data-motion-toggle]').forEach((btn) => {
    btn.textContent = paused ? 'Play 3D' : 'Pause 3D';
    btn.removeAttribute('aria-pressed');
  });
}

function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text).catch(() => legacyCopy(text));
  }
  return legacyCopy(text);
}
function legacyCopy(text) {
  return new Promise((resolve, reject) => {
    const ta = document.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
    document.body.appendChild(ta); ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { /* execCommand unsupported */ }
    ta.remove();
    if (ok) resolve(); else reject(new Error('copy failed'));
  });
}

function wireCopy() {
  document.querySelectorAll('[data-copy]').forEach((btn) => {
    const label = btn.textContent.trim() || 'Copy';
    let timer = 0;
    btn.addEventListener('click', () => {
      const root = btn.closest('.install-box, .copy-box, [data-copy-root]') || document;
      const status = root.querySelector('[data-copy-status]') || document.querySelector('[data-copy-status]');
      const done = (ok) => {
        btn.textContent = ok ? 'Copied' : 'Copy failed';
        if (status) status.textContent = ok ? 'Copied to clipboard.' : 'Copy failed. Select the text and copy it by hand.';
        clearTimeout(timer);
        timer = setTimeout(() => { btn.textContent = label; if (status) status.textContent = ''; }, 2000);
      };
      copyText(btn.dataset.copy || '').then(() => done(true), () => done(false));
    });
  });
}

async function loadDeps() {
  const [THREE, motifs] = await Promise.all([import('three'), import('./product-motifs.js')]);
  return { THREE, buildProductMotif: motifs.buildProductMotif, mulberry32: motifs.mulberry32 };
}

async function startScene(initialTheme, initialPaused) {
  const docEl = document.documentElement;
  const canvas = document.getElementById('world');
  // Pages with their own banner WebGL stage set data-own-stage on <html> so they keep 1 context, not 2.
  if (!canvas || docEl.hasAttribute('data-own-stage')) return null;

  let deps;
  try { deps = await loadDeps(); } catch (e) { docEl.classList.add('nogl'); return null; }
  const { THREE, buildProductMotif, mulberry32 } = deps;

  const lite = Math.min(window.innerWidth, window.innerHeight) < 620 || (navigator.hardwareConcurrency || 8) <= 4;
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: !lite, alpha: false, depth: false, stencil: false }); }
  catch (e) { docEl.classList.add('nogl'); return null; }
  if (!renderer.getContext()) { docEl.classList.add('nogl'); return null; }

  const gl = renderer.getContext();
  const maxPt = Math.min(256, (gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE) || [1, 64])[1]);
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(38, 1, 0.1, 220);
  const N = lite ? 1500 : 2800, kind = docEl.dataset.product || 'voice';
  const motif = buildProductMotif(kind, N, 440);
  const u = {
    uTime: { value: 1.8 }, uLight: { value: initialTheme === 'light' ? 1 : 0 }, uPx: { value: 1 },
    uCamRef: { value: 24 }, uMaxPt: { value: maxPt }, uMorph: { value: 0 },
    uSpinY: { value: -0.30 }, uSpinX: { value: 0.15 }, uPulse: { value: motif.pulse },
  };

  const tri = new THREE.BufferGeometry();
  tri.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
  const bgMat = new THREE.ShaderMaterial({
    vertexShader: BG_VERT, fragmentShader: BG_FRAG, depthTest: false, depthWrite: false,
    uniforms: { uTime: u.uTime, uLight: u.uLight, uAspect: { value: 1 }, uGlowPos: { value: new THREE.Vector2(0.73, 0.54) } },
  });
  const bg = new THREE.Mesh(tri, bgMat); bg.frustumCulled = false; bg.renderOrder = -10; scene.add(bg);

  const makeMat = (vertexShader, fragmentShader) => new THREE.ShaderMaterial({
    vertexShader, fragmentShader, transparent: true, depthTest: false, depthWrite: false,
    blending: u.uLight.value > 0.5 ? THREE.NormalBlending : THREE.AdditiveBlending, uniforms: { ...u },
  });

  const dd = buildDust(lite ? 380 : 760, mulberry32), dustGeo = new THREE.BufferGeometry();
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dd.pos, 3));
  dustGeo.setAttribute('aSD', new THREE.BufferAttribute(dd.sd, 3));
  const dustMat = makeMat(DUST_VERT, POINT_FRAG), dust = new THREE.Points(dustGeo, dustMat);
  dust.frustumCulled = false; dust.renderOrder = 1;

  const shapeGeo = new THREE.BufferGeometry();
  shapeGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 3), 3));
  ['aT0', 'aT1', 'aT2'].forEach((k, i) => shapeGeo.setAttribute(k, new THREE.BufferAttribute(motif.T[i], 3)));
  shapeGeo.setAttribute('aSeed', new THREE.BufferAttribute(motif.seed, 4));
  const shapeMat = makeMat(SHAPE_VERT, POINT_FRAG), shape = new THREE.Points(shapeGeo, shapeMat);
  shape.frustumCulled = false; shape.renderOrder = 3;

  const wireGeo = new THREE.BufferGeometry();
  wireGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(motif.M * 6), 3));
  ['aT0', 'aT1', 'aT2'].forEach((k, i) => wireGeo.setAttribute(k, new THREE.BufferAttribute(motif.wires[i], 3)));
  const wireMat = makeMat(WIRE_VERT, WIRE_FRAG), wires = new THREE.LineSegments(wireGeo, wireMat);
  wires.frustumCulled = false; wires.renderOrder = 2;

  const flareGlowMat = makeMat(FLARE_VERT, GLOW_FRAG), flareStreakMat = makeMat(FLARE_VERT, STREAK_FRAG);
  const flareGlow = new THREE.Mesh(new THREE.PlaneGeometry(13, 13), flareGlowMat);
  const flareStreak = new THREE.Mesh(new THREE.PlaneGeometry(24, 3.0), flareStreakMat);
  flareGlow.renderOrder = 5; flareStreak.renderOrder = 5;
  scene.add(dust, wires, shape, flareStreak, flareGlow);

  const blendMats = [dustMat, wireMat, shapeMat, flareGlowMat, flareStreakMat];
  const flareMeshes = [flareGlow, flareStreak];
  let vw = 1, vh = 1, camZ = 24, portrait = false, raf = 0, disposed = false, still = initialPaused;
  const ptr = { x: 0, y: 0 }, flarePos = new THREE.Vector3(), proj = new THREE.Vector3();

  // Read the mobile breakpoint published by site-nav.js on <html data-mobile-max>.
  const mobileMax = Number(docEl.dataset.mobileMax) || 0;
  const resize = () => {
    vw = Math.max(1, window.innerWidth); vh = Math.max(1, window.innerHeight); portrait = mobileMax > 0 && vw <= mobileMax;
    const dpr = Math.min(window.devicePixelRatio || 1, 2), aspect = vw / vh;
    renderer.setPixelRatio(dpr); renderer.setSize(vw, vh, false); camera.aspect = aspect;
    const tanV = Math.tan((camera.fov * Math.PI) / 360), tanH = tanV * aspect;
    camZ = portrait
      ? Math.max(30, 6.9 / Math.max(0.08, tanH * 0.84), 4.6 / Math.max(0.06, tanV * 0.27))
      : Math.max(22.5, 6.9 / Math.max(0.12, tanH * 0.48));
    u.uCamRef.value = camZ; u.uPx.value = dpr * Math.min(1.35, Math.max(0.78, vh / 900));
    bgMat.uniforms.uAspect.value = aspect;
  };

  const renderFrame = (t) => {
    if (disposed) return;
    const isLight = u.uLight.value > 0.5;
    u.uTime.value = t;
    // A still frame is always the opening composition (scroll morph and pointer parallax are motion).
    const prog = still ? 0 : Math.min(1, Math.max(0, window.scrollY / Math.max(1, document.documentElement.scrollHeight - vh)));
    u.uMorph.value = prog * 2.0;
    u.uSpinY.value = -0.28 + prog * 1.35 + Math.sin(t * 0.22) * 0.08 + (still ? 0 : ptr.x * 0.14);
    u.uSpinX.value = 0.14 + Math.cos(t * 0.18) * 0.04 - (still ? 0 : ptr.y * 0.10);
    camera.position.set(still ? 0 : ptr.x * 0.5, 0.35 + (still ? 0 : ptr.y * 0.35), camZ); camera.lookAt(0, 0, 0);
    if (portrait) {
      const fade = Math.max(0, 1 - window.scrollY / Math.max(260, vh * 0.55));
      camera.setViewOffset(vw, vh, 0, (0.275 * fade + 0.04 * (1 - fade)) * vh, vw, vh);
    } else {
      camera.setViewOffset(vw, vh, -0.23 * vw, 0.04 * vh, vw, vh);
    }
    camera.updateProjectionMatrix(); camera.updateMatrixWorld(true);
    const w0 = Math.max(0, 1 - u.uMorph.value), fs = Math.max(0.9, camZ / 21);
    flarePos.set(0.35 * w0, 0.05 * w0, 1.25 * w0);
    // Light Paper: keep the horizontal flare in the right half so it never crosses the hero copy column.
    let streakX = 1;
    if (isLight) streakX = portrait ? 0.5 : 0.52;
    for (const m of flareMeshes) { m.position.copy(flarePos); m.quaternion.copy(camera.quaternion); m.scale.set(fs, fs, 1); }
    flareStreak.scale.set(fs * streakX, fs, 1);
    proj.copy(flarePos).project(camera);
    bgMat.uniforms.uGlowPos.value.set(proj.x * 0.5 + 0.5, proj.y * 0.5 + 0.5);
    renderer.render(scene, camera);
  };

  const clearColor = (isLight) => renderer.setClearColor(isLight ? 0xf3f2ee : 0x03050b, 1);
  const setTheme = (next) => {
    const isLight = next === 'light';
    u.uLight.value = isLight ? 1 : 0;
    clearColor(isLight);
    blendMats.forEach((m) => { m.blending = isLight ? THREE.NormalBlending : THREE.AdditiveBlending; m.needsUpdate = true; });
    renderFrame(u.uTime.value);
  };

  let tBase = performance.now();
  const loop = (now) => { if (disposed || still || document.hidden) return; renderFrame(1.8 + (now - tBase) * 0.001); raf = requestAnimationFrame(loop); };
  const pause = () => { still = true; cancelAnimationFrame(raf); raf = 0; renderFrame(1.8); };
  const play = () => { if (!still || disposed) return; still = false; tBase = performance.now(); cancelAnimationFrame(raf); if (!document.hidden) raf = requestAnimationFrame(loop); };

  const onResize = () => { if (disposed) return; resize(); renderFrame(u.uTime.value); };
  const onPointer = (e) => { ptr.x = (e.clientX / Math.max(1, vw) - 0.5) * 2; ptr.y = -(e.clientY / Math.max(1, vh) - 0.5) * 2; };
  const onVisibility = () => {
    if (disposed || still) return;
    if (document.hidden) { cancelAnimationFrame(raf); raf = 0; }
    else if (!raf) raf = requestAnimationFrame(loop);
  };
  const onContextLost = (e) => { e.preventDefault(); disposed = true; cancelAnimationFrame(raf); raf = 0; docEl.classList.remove('gl'); docEl.classList.add('nogl'); };
  window.addEventListener('resize', onResize, { passive: true });
  window.addEventListener('pointermove', onPointer, { passive: true });
  document.addEventListener('visibilitychange', onVisibility);
  canvas.addEventListener('webglcontextlost', onContextLost);
  resize(); clearColor(initialTheme === 'light');
  renderFrame(1.8); docEl.classList.remove('nogl'); docEl.classList.add('gl');
  if (!still && !document.hidden) raf = requestAnimationFrame(loop);

  return {
    setTheme, pause, play,
    get paused() { return still; },
    dispose() {
      disposed = true; cancelAnimationFrame(raf); raf = 0;
      window.removeEventListener('resize', onResize);
      window.removeEventListener('pointermove', onPointer);
      document.removeEventListener('visibilitychange', onVisibility);
      canvas.removeEventListener('webglcontextlost', onContextLost);
      [tri, dustGeo, shapeGeo, wireGeo, flareGlow.geometry, flareStreak.geometry].forEach((g) => g.dispose());
      [bgMat, dustMat, shapeMat, wireMat, flareGlowMat, flareStreakMat].forEach((m) => m.dispose());
      docEl.classList.remove('gl'); renderer.dispose();
    },
  };
}

function boot() {
  const docEl = document.documentElement;
  // Controls first: nothing below depends on Three.js or the network, so a blocked CDN never kills the page chrome.
  let theme = resolveTheme(), paused = readPaused(), api = null, starting = false, failed = false;
  docEl.classList.remove('static');
  docEl.classList.toggle('still', paused);
  syncButtons(paused);

  // site-nav.js flips data-theme; the 3D stage follows it.
  const follow = () => {
    const next = resolveTheme();
    if (next === theme) return;
    theme = next; if (api) api.setTheme(theme);
  };
  try { new MutationObserver(follow).observe(docEl, { attributes: true, attributeFilter: ['data-theme'] }); } catch (e) { /* MutationObserver unsupported */ }
  document.addEventListener('coco:themechange', follow);

  const ensureScene = async () => {
    if (api || starting || failed) return;
    starting = true;
    const startedTheme = theme;
    try {
      api = await startScene(startedTheme, paused);
      if (!api) failed = true;
    } catch (e) {
      docEl.classList.add('nogl');
      failed = true;
    } finally { starting = false; }
    if (api) {
      const latest = resolveTheme();
      if (latest !== theme) theme = latest;
      if (theme !== startedTheme) api.setTheme(theme);
      if (api.paused !== paused) { if (paused) api.pause(); else api.play(); }
    }
  };
  document.querySelectorAll('[data-motion-toggle]').forEach((btn) => btn.addEventListener('click', () => {
    paused = !paused;
    writePaused(paused);
    docEl.classList.toggle('still', paused);
    syncButtons(paused);
    if (api) { if (paused) api.pause(); else api.play(); } else ensureScene();
  }));

  wireCopy();
  try {
    matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (ev) => {
      let stored = null;
      try { stored = sessionStorage.getItem(PAUSE_KEY); } catch (e) { /* private mode / storage blocked */ }
      if (stored !== null) return;
      paused = ev.matches;
      docEl.classList.toggle('still', paused);
      syncButtons(paused);
      if (api) { if (paused) api.pause(); else api.play(); }
    });
  } catch (e) { /* matchMedia listener unsupported */ }

  docEl.classList.add('ready');
  // Three.js loads only now, after every control is wired. Paused/reduced motion still renders one static frame.
  ensureScene();
}

boot();
