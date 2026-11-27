// Bespoke 3D scene for /rijul-kalra/: the meridian lattice.
// ES module: loaded with type="module"; top-level names are module-scoped.
//
// One idea, drawn with hairlines and flat dots (Flat Signal: no glow sprites, no blur, nothing soft):
//   - a graticule sphere of meridians and parallels  = structure, governance (the day side: crisp blue hairlines)
//   - scattered nodes joined by thin links            = building (the night side: amber nodes and a loose web)
//   - the terminator, a fixed ring of ticks           = where one half of the week hands over to the other
//   - three tilted orbit rings with small satellites  = the cadence that keeps both halves turning
// The lattice turns slowly through a FIXED terminator, so every line and node crosses from day to night and back.
//
// Honours: Light and Dark themes (follows data-theme on <html>, set by the shared top bar), prefers-reduced-motion
// and the Pause 3D chip (one static composition, no animation loop), no WebGL / blocked module (the inline SVG in
// the page shows instead). The only network request is the one vendored three.js module, same origin. No CDN.

const THREE_URL = new URL('../vendor/three/three.module.min.js', import.meta.url).href;
const docEl = document.documentElement;
const PAUSE_KEY = 'coco-3d-pause:' + location.pathname;
const STILL_T = 5.2; // the static composition is always this moment of the animation

// The shared top bar (site-nav.js) owns theme storage, theme resolution, theme toggles, and meta[name="theme-color"].
const resolveTheme = () => (window.cocoTheme ? window.cocoTheme.current() : 'dark');
function readStoredPause() {
  try { return sessionStorage.getItem(PAUSE_KEY); } catch (e) { /* private mode / storage blocked */ return null; }
}
function readPaused() {
  const stored = readStoredPause();
  if (stored === '1') return true;
  if (stored === '0') return false;
  try { return matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
}
function writePaused(paused) {
  try { sessionStorage.setItem(PAUSE_KEY, paused ? '1' : '0'); } catch (e) { /* private mode: this tab only */ }
}
function syncMotionButtons(paused) {
  document.querySelectorAll('[data-motion-toggle]').forEach((btn) => {
    btn.textContent = paused ? 'Play 3D' : 'Pause 3D'; // the label names the action, so no aria-pressed
    btn.removeAttribute('aria-pressed');
  });
}
// Standard 5-line PRNG kept inline so /rijul-kalra/ never downloads the product motif bundle.
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ---------------------------------------------------------------- shaders */

// Lattice hairlines: bright and crisp on the day side, a quiet trace on the night side, dimmer when facing away.
const LINE_VERT = `
attribute float aW; uniform vec3 uSun; uniform float uDay, uNight; varying float vA; varying float vDay;
void main() {
  vec3 wn = normalize(mat3(modelMatrix) * normalize(position));
  vDay = smoothstep(-0.12, 0.26, dot(wn, uSun));
  float front = smoothstep(-0.30, 0.40, normalize(mat3(viewMatrix) * wn).z);
  vA = mix(uNight, uDay, vDay) * aW * (0.26 + 0.74 * front);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;
const LINE_FRAG = `
precision highp float; uniform vec3 uDayCol, uNightCol; uniform float uFade; varying float vA; varying float vDay;
void main() { gl_FragColor = vec4(mix(uNightCol, uDayCol, vDay), clamp(vA * uFade, 0.0, 1.0)); }`;

// Nodes: flat discs. Lattice nodes are small and pale by day, larger and amber by night. Floating nodes show by night only.
const NODE_VERT = `
attribute vec4 aSeed; uniform vec3 uSun; uniform float uPx, uCamRef, uMaxPt, uTime; varying float vA; varying float vNight;
void main() {
  vec3 wn = normalize(mat3(modelMatrix) * normalize(position));
  float day = smoothstep(-0.12, 0.26, dot(wn, uSun));
  vNight = 1.0 - day;
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  float front = smoothstep(-0.35, 0.35, normalize(mat3(viewMatrix) * wn).z);
  float extra = aSeed.w;
  float tw = 0.88 + 0.12 * sin(uTime * (0.5 + aSeed.x) + aSeed.y * 40.0);
  vA = mix(mix(0.40, 0.95, vNight), vNight, extra) * (0.35 + 0.65 * front) * tw;
  float size = mix(mix(2.1, 3.7, vNight), 2.6 + aSeed.z * 3.2, extra);
  gl_PointSize = clamp(size * uPx * (uCamRef / max(-mv.z, 0.1)), 1.0, uMaxPt);
  gl_Position = projectionMatrix * mv;
}`;
const NODE_FRAG = `
precision highp float; uniform vec3 uDayCol, uNightCol; uniform float uFade; varying float vA; varying float vNight;
void main() {
  float a = 1.0 - smoothstep(0.76, 1.0, length(gl_PointCoord * 2.0 - 1.0));
  if (a < 0.01) discard;
  gl_FragColor = vec4(mix(uDayCol, uNightCol, vNight), a * clamp(vA * uFade, 0.0, 1.0));
}`;

// Rings, ticks and satellites: constant tone, brighter when nearer the camera.
const RING_VERT = `
attribute float aKind; uniform float uBase, uCamRef, uPx, uMaxPt, uPoint; varying float vA; varying float vKind;
void main() {
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  float near = 1.0 - smoothstep(uCamRef - 2.3, uCamRef + 2.3, -mv.z);
  vA = uBase * (0.30 + 0.70 * near); vKind = aKind;
  gl_PointSize = clamp(uPoint * uPx * (uCamRef / max(-mv.z, 0.1)), 1.0, uMaxPt);
  gl_Position = projectionMatrix * mv;
}`;
const RING_FRAG = `
precision highp float; uniform vec3 uCol, uCol2; uniform float uFade, uRound; varying float vA; varying float vKind;
void main() {
  if (uRound > 0.5) {
    float a = 1.0 - smoothstep(0.76, 1.0, length(gl_PointCoord * 2.0 - 1.0));
    if (a < 0.01) discard;
    gl_FragColor = vec4(mix(uCol, uCol2, vKind), a * clamp(vA * uFade, 0.0, 1.0));
  } else {
    gl_FragColor = vec4(uCol, clamp(vA * uFade, 0.0, 1.0));
  }
}`;

/* --------------------------------------------------------------- geometry */

function buildLattice(THREE, lite) {
  const rand = mulberry32(1143);
  const pt = (lon, lat) => [Math.cos(lat) * Math.cos(lon), Math.sin(lat), Math.cos(lat) * Math.sin(lon)];
  const pos = [], w = [];
  const seg = (a, b, wt) => { pos.push(...a, ...b); w.push(wt, wt); };

  const M = lite ? 16 : 24, SEG = lite ? 64 : 96;
  for (let i = 0; i < M; i++) {
    const lon = (i / M) * Math.PI * 2, wt = i === 0 || i === M / 2 ? 1.7 : 1;
    for (let s = 0; s < SEG; s++) {
      seg(pt(lon, -Math.PI / 2 + (s / SEG) * Math.PI), pt(lon, -Math.PI / 2 + ((s + 1) / SEG) * Math.PI), wt);
    }
  }
  const lats = lite ? [-60, -30, 0, 30, 60] : [-75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75];
  const PS = lite ? 96 : 144;
  for (const deg of lats) {
    const lat = (deg * Math.PI) / 180;
    let wt = 1;
    if (deg === 0) wt = 1.9;
    else if (Math.abs(deg) === 30) wt = 1.25;
    for (let s = 0; s < PS; s++) seg(pt((s / PS) * Math.PI * 2, lat), pt(((s + 1) / PS) * Math.PI * 2, lat), wt);
  }
  const lineGeo = new THREE.BufferGeometry();
  lineGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pos), 3));
  lineGeo.setAttribute('aW', new THREE.BufferAttribute(new Float32Array(w), 1));

  // Lattice intersections.
  const np = [], seeds = [];
  const nodeLons = lite ? 16 : 24;
  for (let i = 0; i < nodeLons; i++) {
    for (const deg of lats) {
      np.push(...pt((i / nodeLons) * Math.PI * 2, (deg * Math.PI) / 180));
      seeds.push(rand(), rand(), rand(), 0);
    }
  }
  // Floating nodes (the builder's web), kept as vectors so the nearest neighbours can be joined.
  const extraCount = lite ? 40 : 64, extras = [];
  for (let i = 0; i < extraCount; i++) {
    const u = rand() * 2 - 1, th = rand() * Math.PI * 2, r = 1.14 + rand() * 0.44, s = Math.sqrt(1 - u * u);
    const p = [r * s * Math.cos(th), r * u, r * s * Math.sin(th)];
    extras.push(p); np.push(...p); seeds.push(rand(), rand(), rand(), 1);
  }
  const nodeGeo = new THREE.BufferGeometry();
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(np), 3));
  nodeGeo.setAttribute('aSeed', new THREE.BufferAttribute(new Float32Array(seeds), 4));

  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const links = new Set(), lp = [], lw = [];
  extras.forEach((a, i) => {
    extras.map((b, j) => [j, dist(a, b)]).filter(([j]) => j !== i).sort((p, q) => p[1] - q[1]).slice(0, 2).forEach(([j]) => {
      const key = i < j ? i + ':' + j : j + ':' + i;
      if (links.has(key)) return;
      links.add(key); lp.push(...a, ...extras[j]); lw.push(1, 1);
    });
  });
  const webGeo = new THREE.BufferGeometry();
  webGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(lp), 3));
  webGeo.setAttribute('aW', new THREE.BufferAttribute(new Float32Array(lw), 1));
  return { lineGeo, nodeGeo, webGeo };
}

// A dashed circle in the XZ plane.
function ringGeometry(THREE, radius, segs) {
  const pos = [], kind = [];
  for (let i = 0; i < segs; i += 2) {
    const a = (i / segs) * Math.PI * 2, b = ((i + 1) / segs) * Math.PI * 2;
    pos.push(radius * Math.cos(a), 0, radius * Math.sin(a), radius * Math.cos(b), 0, radius * Math.sin(b)); kind.push(0, 0);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pos), 3));
  g.setAttribute('aKind', new THREE.BufferAttribute(new Float32Array(kind), 1));
  return g;
}
// Radial ticks in the XZ plane; every tenth is longer. This is the terminator scale.
function tickGeometry(THREE, radius, count) {
  const pos = [], kind = [];
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2, long = i % 10 === 0, r1 = radius + (long ? 0.13 : 0.06);
    pos.push(radius * Math.cos(a), 0, radius * Math.sin(a), r1 * Math.cos(a), 0, r1 * Math.sin(a)); kind.push(0, 0);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pos), 3));
  g.setAttribute('aKind', new THREE.BufferAttribute(new Float32Array(kind), 1));
  return g;
}
function satelliteGeometry(THREE, x, kind) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([x, 0, 0]), 3));
  g.setAttribute('aKind', new THREE.BufferAttribute(new Float32Array([kind]), 1));
  return g;
}

/* ------------------------------------------------------------------ scene */

const PALETTE = {
  dark: {
    day: [0.56, 0.69, 1.0], night: [0.36, 0.47, 0.84], amber: [1.0, 0.71, 0.29],
    lineDay: 0.62, lineNight: 0.17, web: 0.46, ring: 0.34, tick: 0.62,
  },
  light: {
    day: [0.071, 0.204, 1.0], night: [0.36, 0.43, 0.82], amber: [0.60, 0.32, 0.0],
    lineDay: 0.62, lineNight: 0.20, web: 0.55, ring: 0.36, tick: 0.66,
  },
};

async function startScene(theme, initialPaused) {
  const canvas = document.getElementById('world');
  if (!canvas) return null;

  // Probe first: a browser with WebGL off gets the SVG fallback without loading three.js or logging an error.
  try {
    const probe = document.createElement('canvas');
    if (!(probe.getContext('webgl2') || probe.getContext('webgl'))) { docEl.classList.add('nogl'); return null; }
  } catch (e) { docEl.classList.add('nogl'); return null; }

  let THREE;
  try { THREE = await import(THREE_URL); } catch (e) { docEl.classList.add('nogl'); return null; }

  const lite = Math.min(window.innerWidth, window.innerHeight) < 620 || (navigator.hardwareConcurrency || 8) <= 4;
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, depth: false, stencil: false, powerPreference: 'low-power' });
  } catch (e) { docEl.classList.add('nogl'); return null; }
  const gl = renderer.getContext();
  if (!gl) { docEl.classList.add('nogl'); return null; }
  renderer.setClearColor(0x000000, 0);
  const maxPt = Math.min(128, (gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE) || [1, 64])[1]);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 80);

  const sun = new THREE.Vector3(-0.82, 0.28, 0.5).normalize();
  const common = {
    uSun: { value: sun }, uFade: { value: 1 }, uCamRef: { value: 8 }, uPx: { value: 1 }, uMaxPt: { value: maxPt }, uTime: { value: STILL_T },
  };
  const col = (c) => new THREE.Vector3(c[0], c[1], c[2]);
  const mat = (vertexShader, fragmentShader, uniforms) => new THREE.ShaderMaterial({
    vertexShader, fragmentShader, uniforms: { ...common, ...uniforms },
    transparent: true, depthTest: false, depthWrite: false, blending: THREE.NormalBlending,
  });

  // Lattice (turns about a tilted axis through a fixed terminator).
  const L = buildLattice(THREE, lite);
  const lineMat = mat(LINE_VERT, LINE_FRAG, { uDay: { value: 0.6 }, uNight: { value: 0.17 }, uDayCol: { value: col(PALETTE.dark.day) }, uNightCol: { value: col(PALETTE.dark.night) } });
  const webMat = mat(LINE_VERT, LINE_FRAG, { uDay: { value: 0.0 }, uNight: { value: 0.46 }, uDayCol: { value: col(PALETTE.dark.amber) }, uNightCol: { value: col(PALETTE.dark.amber) } });
  const nodeMat = mat(NODE_VERT, NODE_FRAG, { uDayCol: { value: col(PALETTE.dark.day) }, uNightCol: { value: col(PALETTE.dark.amber) } });
  const tilt = new THREE.Group(), spin = new THREE.Group();
  tilt.rotation.z = 0.41; tilt.add(spin); scene.add(tilt);
  const grid = new THREE.LineSegments(L.lineGeo, lineMat), web = new THREE.LineSegments(L.webGeo, webMat), nodes = new THREE.Points(L.nodeGeo, nodeMat);
  [grid, web, nodes].forEach((o, i) => { o.frustumCulled = false; o.renderOrder = i + 1; spin.add(o); });

  // Orbit rings + satellites.
  const ringBase = { uBase: { value: 0.34 }, uCol: { value: col(PALETTE.dark.day) }, uCol2: { value: col(PALETTE.dark.amber) } };
  const ringLineMat = mat(RING_VERT, RING_FRAG, { ...ringBase, uPoint: { value: 0 }, uRound: { value: 0 } });
  const satMat = mat(RING_VERT, RING_FRAG, { ...ringBase, uBase: { value: 1 }, uPoint: { value: 4.6 }, uRound: { value: 1 } });
  const tickMat = mat(RING_VERT, RING_FRAG, { ...ringBase, uBase: { value: 0.62 }, uPoint: { value: 0 }, uRound: { value: 0 } });
  const rings = [
    { r: 1.42, tx: 1.18, tz: 0.30, speed: 0.060, phase: 0.6, sats: [[0, 0]] },
    { r: 1.74, tx: 0.62, tz: -0.52, speed: -0.042, phase: 2.4, sats: [[0, 1], [Math.PI, 0]] },
    { r: 2.08, tx: -0.38, tz: 0.78, speed: 0.027, phase: 4.1, sats: [[0, 1]] },
  ].map((c, i) => {
    const t = new THREE.Group(), s = new THREE.Group();
    t.rotation.set(c.tx, 0, c.tz); t.add(s); scene.add(t);
    const line = new THREE.LineSegments(ringGeometry(THREE, c.r, 180), ringLineMat);
    line.frustumCulled = false; line.renderOrder = 5 + i; s.add(line);
    c.sats.forEach(([a, kind]) => {
      const p = new THREE.Points(satelliteGeometry(THREE, c.r, kind), satMat);
      p.frustumCulled = false; p.renderOrder = 8; p.rotation.y = a;
      // rotate about the ring's own axis: wrap in a child group so the offset angle is independent of the spin
      const holder = new THREE.Group(); holder.rotation.y = a; holder.add(p); p.rotation.y = 0; s.add(holder);
    });
    return { s, c };
  });

  // Terminator: a fixed scale of ticks in the plane perpendicular to the sun.
  const term = new THREE.Group();
  term.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), sun);
  const ticks = new THREE.LineSegments(tickGeometry(THREE, 1.05, 120), tickMat);
  ticks.frustumCulled = false; ticks.renderOrder = 9; term.add(ticks); scene.add(term);

  const blendMats = [lineMat, webMat, nodeMat, ringLineMat, satMat, tickMat];

  let vw = 1, vh = 1, camZ = 8, portrait = false, raf = 0, disposed = false, still = initialPaused, scrollProg = 0;
  const ptr = { x: 0, y: 0 }, ptrS = { x: 0, y: 0 };

  const setTheme = (next) => {
    const P = PALETTE[next === 'light' ? 'light' : 'dark'];
    lineMat.uniforms.uDayCol.value.set(...P.day); lineMat.uniforms.uNightCol.value.set(...P.night);
    lineMat.uniforms.uDay.value = P.lineDay; lineMat.uniforms.uNight.value = P.lineNight;
    webMat.uniforms.uDayCol.value.set(...P.amber); webMat.uniforms.uNightCol.value.set(...P.amber); webMat.uniforms.uNight.value = P.web;
    nodeMat.uniforms.uDayCol.value.set(...P.day); nodeMat.uniforms.uNightCol.value.set(...P.amber);
    [ringLineMat, tickMat, satMat].forEach((m) => { m.uniforms.uCol.value.set(...P.day); m.uniforms.uCol2.value.set(...P.amber); });
    ringLineMat.uniforms.uBase.value = P.ring; tickMat.uniforms.uBase.value = P.tick;
    renderFrame(common.uTime.value);
  };

  // Read the mobile breakpoint published by site-nav.js on <html data-mobile-max>.
  const mobileMax = Number(docEl.dataset.mobileMax) || 0;
  const resize = () => {
    vw = Math.max(1, window.innerWidth); vh = Math.max(1, window.innerHeight); portrait = mobileMax > 0 && vw <= mobileMax;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    renderer.setPixelRatio(dpr); renderer.setSize(vw, vh, false);
    camera.aspect = vw / vh;
    const tanV = Math.tan((camera.fov * Math.PI) / 360), tanH = tanV * camera.aspect;
    camZ = portrait ? Math.max(9, 1.9 / tanH) : Math.max(8.4, 2.1 / (0.58 * tanH));
    common.uCamRef.value = camZ;
    common.uPx.value = dpr * Math.min(1.3, Math.max(0.8, vh / 900));
    common.uFade.value = portrait ? 0.9 : 1;
  };

  const renderFrame = (t) => {
    if (disposed) return;
    common.uTime.value = t;
    if (!still) {
      scrollProg = Math.min(1, Math.max(0, window.scrollY / Math.max(1, vh)));
      ptrS.x += (ptr.x - ptrS.x) * 0.05; ptrS.y += (ptr.y - ptrS.y) * 0.05;
    }
    const px = still ? 0 : ptrS.x, py = still ? 0 : ptrS.y, sp = still ? 0 : scrollProg;
    spin.rotation.y = 0.9 + t * 0.045 + sp * 0.9;
    rings.forEach(({ s, c }) => { s.rotation.y = c.phase + t * c.speed * 2.2 + sp * c.speed * 6; });
    camera.position.set(px * 0.35, 0.55 + py * 0.25, camZ); camera.lookAt(0, 0, 0);
    if (portrait) camera.setViewOffset(vw, vh, 0, 0.22 * vh, vw, vh);
    else camera.setViewOffset(vw, vh, -0.215 * vw, 0, vw, vh);
    camera.updateProjectionMatrix(); camera.updateMatrixWorld(true);
    renderer.render(scene, camera);
  };

  let t0 = performance.now();
  const loop = (now) => {
    if (disposed || still || document.hidden) return;
    // Past the hero the page is opaque, so the stage is not drawn at all (saves battery).
    if (window.scrollY <= vh * 1.15) renderFrame(STILL_T + (now - t0) * 0.001);
    raf = requestAnimationFrame(loop);
  };
  const pause = () => { still = true; cancelAnimationFrame(raf); raf = 0; renderFrame(STILL_T); };
  const play = () => { if (!still || disposed) return; still = false; t0 = performance.now(); cancelAnimationFrame(raf); if (!document.hidden) raf = requestAnimationFrame(loop); };

  const onResize = () => { if (disposed) return; resize(); renderFrame(common.uTime.value); };
  const onPointer = (e) => {
    ptr.x = (e.clientX / Math.max(1, vw) - 0.5) * 2; ptr.y = -(e.clientY / Math.max(1, vh) - 0.5) * 2;
  };
  const onVisibility = () => {
    if (disposed || still) return;
    if (document.hidden) { cancelAnimationFrame(raf); raf = 0; }
    else if (!raf) raf = requestAnimationFrame(loop);
  };
  const onContextLost = (e) => {
    e.preventDefault(); disposed = true; cancelAnimationFrame(raf); raf = 0;
    docEl.classList.remove('gl'); docEl.classList.add('nogl');
  };
  window.addEventListener('resize', onResize, { passive: true });
  window.addEventListener('pointermove', onPointer, { passive: true });
  document.addEventListener('visibilitychange', onVisibility);
  canvas.addEventListener('webglcontextlost', onContextLost);

  blendMats.forEach((m) => { m.needsUpdate = true; });
  resize(); setTheme(theme); renderFrame(STILL_T);
  docEl.classList.remove('nogl'); docEl.classList.add('gl');
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
      scene.traverse((obj) => { if (obj.geometry) obj.geometry.dispose(); });
      blendMats.forEach((m) => m.dispose());
      docEl.classList.remove('gl'); renderer.dispose();
    },
  };
}

function boot() {
  // Controls first: nothing below depends on three.js, so a blocked module never disables the page chrome.
  let theme = resolveTheme(), paused = readPaused(), api = null, starting = false, failed = false;
  docEl.classList.toggle('still', paused);
  syncMotionButtons(paused);

  const follow = () => {
    const next = resolveTheme();
    if (next === theme) return;
    theme = next; if (api) api.setTheme(theme);
  };
  const syncApiPaused = () => { if (!api) return; if (paused) api.pause(); else api.play(); };
  try { new MutationObserver(follow).observe(docEl, { attributes: true, attributeFilter: ['data-theme'] }); } catch (e) { /* MutationObserver unsupported */ }
  document.addEventListener('coco:themechange', follow);
  try {
    matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (ev) => {
      if (readStoredPause() !== null) return;
      paused = ev.matches;
      docEl.classList.toggle('still', paused);
      syncMotionButtons(paused);
      syncApiPaused();
    });
  } catch (e) { /* matchMedia listener unsupported */ }

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
      if (api.paused !== paused) syncApiPaused();
    }
  };
  document.querySelectorAll('[data-motion-toggle]').forEach((btn) => btn.addEventListener('click', () => {
    paused = !paused;
    writePaused(paused);
    docEl.classList.toggle('still', paused);
    syncMotionButtons(paused);
    if (api) syncApiPaused(); else ensureScene();
  }));

  ensureScene();
}

boot();
