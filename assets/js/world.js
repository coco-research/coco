// The 3D world: one WebGL canvas, no post-processing. Everything is additive points
// and hairlines, positioned in vertex shaders from a handful of uniforms the director
// drives from scroll. Loaded lazily after first paint.
import * as THREE from 'three';
import { LAYOUT, clusterCenter } from './layout.js';

const TAU = Math.PI * 2;

function mulberry32(a) {
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ------------------------------------------------------------------ data */

// 13 constellations, 495 stars in total. Each is a small random-walk graph so it
// reads as a constellation (chains, branches, a few loops), not a blob.
function buildStars() {
  const rand = mulberry32(495);
  const sizes = LAYOUT.sizes;
  const total = sizes.reduce((a, b) => a + b, 0);
  const center = new Float32Array(total * 3);
  const local = new Float32Array(total * 3);
  const fin = new Float32Array(total * 3);
  const seed = new Float32Array(total * 4);
  const cluster = new Float32Array(total);
  const size = new Float32Array(total);
  const tone = new Float32Array(total);
  const deg = new Uint8Array(total);
  const edges = [];
  const first = [];
  const cosR = Math.cos(LAYOUT.ang.labEnd);
  const sinR = Math.sin(LAYOUT.ang.labEnd);
  let n = 0;

  for (let k = 0; k < sizes.length; k++) {
    const cnt = sizes[k];
    const nodes = [[0, 0, 0]];
    const parents = [-1];
    let guard = 0;
    while (nodes.length < cnt && guard++ < 9000) {
      const pi = Math.floor(Math.pow(rand(), 0.55) * nodes.length);
      const p = nodes[pi];
      const th = rand() * TAU;
      const u = rand() * 2 - 1;
      const s = Math.sqrt(1 - u * u);
      const len = 1.5 + rand() * 1.7;
      const c = [p[0] + len * s * Math.cos(th), p[1] + len * u * 0.85, p[2] + len * s * Math.sin(th)];
      let ok = true;
      for (let j = 0; j < nodes.length; j++) {
        const q = nodes[j];
        const dx = q[0] - c[0], dy = q[1] - c[1], dz = q[2] - c[2];
        if (dx * dx + dy * dy + dz * dz < 1.3) { ok = false; break; }
      }
      if (!ok) continue;
      nodes.push(c);
      parents.push(pi);
    }
    let cx = 0, cy = 0, cz = 0;
    for (const q of nodes) { cx += q[0]; cy += q[1]; cz += q[2]; }
    cx /= nodes.length; cy /= nodes.length; cz /= nodes.length;
    let maxR = 0;
    for (const q of nodes) {
      q[0] -= cx; q[1] -= cy; q[2] -= cz;
      maxR = Math.max(maxR, Math.hypot(q[0], q[1], q[2]));
    }
    const sc = maxR > 6.6 ? 6.6 / maxR : 1;
    const cc = clusterCenter(k);
    // Final layout: the thirteen constellations as one arrangement around S (Vogel spiral).
    const fa = k * 2.399963 + 0.4;
    const fr = 5.5 + 17 * Math.sqrt((k + 0.5) / 13);
    const fcx = Math.cos(fa) * fr, fcy = Math.sin(fa) * fr * 0.78, fcz = (rand() - 0.5) * 7;
    first.push(n);
    for (let i = 0; i < nodes.length; i++) {
      const q = nodes[i];
      const idx = n + i;
      local.set([q[0] * sc, q[1] * sc, q[2] * sc], idx * 3);
      center.set(cc, idx * 3);
      const lx = fcx + q[0] * sc * 0.62, ly = fcy + q[1] * sc * 0.62, lz = fcz + q[2] * sc * 0.62;
      fin[idx * 3] = lx * cosR + lz * sinR;
      fin[idx * 3 + 1] = ly;
      fin[idx * 3 + 2] = -lx * sinR + lz * cosR;
      seed.set([rand(), rand(), rand(), rand()], idx * 4);
      cluster[idx] = k;
      if (parents[i] >= 0) {
        edges.push([idx, n + parents[i], 0]);
        deg[idx]++;
        deg[n + parents[i]]++;
      }
    }
    // a few extra loops between near neighbours
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (parents[i] === j || parents[j] === i) continue;
        const a = nodes[i], b = nodes[j];
        const d2 = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) * sc * sc;
        if (d2 < 7.2 && rand() < 0.34) {
          edges.push([n + i, n + j, 0]);
          deg[n + i]++;
          deg[n + j]++;
        }
      }
    }
    n += nodes.length;
  }

  for (let i = 0; i < total; i++) size[i] = 3.3 + Math.pow(rand(), 2.0) * 4.4 + (deg[i] >= 3 ? 2.6 : 0);
  tone[first[7] + 3] = 1; // the one star that dissents

  // Bridges: in the final arrangement the constellations join into one figure.
  const seen = new Set();
  for (let k = 0; k < sizes.length; k++) {
    for (const off of [1, 4]) {
      const j = (k + off) % sizes.length;
      const key = k < j ? k + '-' + j : j + '-' + k;
      if (seen.has(key)) continue;
      seen.add(key);
      let best = 1e9, ba = -1, bb = -1;
      for (let a = first[k]; a < first[k] + sizes[k]; a++) {
        for (let b = first[j]; b < first[j] + sizes[j]; b++) {
          const dx = fin[a * 3] - fin[b * 3], dy = fin[a * 3 + 1] - fin[b * 3 + 1], dz = fin[a * 3 + 2] - fin[b * 3 + 2];
          const d = dx * dx + dy * dy + dz * dz;
          if (d < best) { best = d; ba = a; bb = b; }
        }
      }
      if (ba >= 0) edges.push([ba, bb, 1]);
    }
  }

  // Line geometry: every segment end carries its star's attributes so it moves with it.
  const E = edges.length;
  const L = {
    center: new Float32Array(E * 6), local: new Float32Array(E * 6), fin: new Float32Array(E * 6),
    seed: new Float32Array(E * 8), cluster: new Float32Array(E * 2), end: new Float32Array(E * 2),
    kind: new Float32Array(E * 2), eseed: new Float32Array(E * 2),
  };
  for (let e = 0; e < E; e++) {
    const [a, b, kind] = edges[e];
    const es = rand();
    for (let v = 0; v < 2; v++) {
      const idx = v ? b : a;
      const o = e * 2 + v;
      for (let c = 0; c < 3; c++) {
        L.center[o * 3 + c] = center[idx * 3 + c];
        L.local[o * 3 + c] = local[idx * 3 + c];
        L.fin[o * 3 + c] = fin[idx * 3 + c];
      }
      for (let c = 0; c < 4; c++) L.seed[o * 4 + c] = seed[idx * 4 + c];
      L.cluster[o] = cluster[idx];
      L.end[o] = v;
      L.kind[o] = kind;
      L.eseed[o] = es;
    }
  }
  return { total, center, local, fin, seed, cluster, size, tone, L, edgeCount: E };
}

// Four targets for the four rules, all with N points, ordered so that point i sits at a
// similar height in every target. That makes the morphs flow instead of exploding.
function buildShapes(N, lite) {
  const rand = mulberry32(2026);
  const T = [new Float32Array(N * 3), new Float32Array(N * 3), new Float32Array(N * 3), new Float32Array(N * 3)];
  const field = new Float32Array(N * 3);
  const seed = new Float32Array(N * 4);
  const helixT = new Float32Array(N);

  const sets = [[], [], [], []];
  const R = 7.2;
  // 1. Data stays local: a closed sphere with a bright core.
  for (let i = 0; i < N; i++) {
    const shell = rand() < 0.8;
    const u = rand() * 2 - 1, th = rand() * TAU, s = Math.sqrt(1 - u * u);
    let r = shell ? 1 - Math.pow(rand(), 6) * 0.07 : Math.cbrt(rand()) * 0.93;
    if (i % 90 === 0) r = rand() * 0.1;
    sets[0].push([R * r * s * Math.cos(th), R * r * u, R * r * s * Math.sin(th)]);
  }
  // 2. Verify, don't average: two rings that interlock. Neither dissolves into the other.
  for (let i = 0; i < N; i++) {
    const ring = i & 1;
    const a = rand() * TAU, b = rand() * TAU;
    const rr = 4.3 + 0.62 * Math.cos(b), off = 0.62 * Math.sin(b);
    if (ring === 0) sets[1].push([-2.7 + rr * Math.cos(a), rr * Math.sin(a), off]);
    else sets[1].push([2.7 + rr * Math.cos(a), off, rr * Math.sin(a)]);
  }
  // 3. Stage is stated plainly: five stacked stages; the top one is lit.
  const radii = [6.6, 5.5, 4.4, 3.3, 2.2];
  for (let i = 0; i < N; i++) {
    const w = rand();
    let k = 0;
    if (w > 0.34) k = 1;
    if (w > 0.58) k = 2;
    if (w > 0.78) k = 3;
    if (w > 0.92) k = 4;
    const y = -4.4 + k * 2.2;
    const th = rand() * TAU;
    if (rand() < 0.45) sets[2].push([radii[k] * Math.cos(th), y + (rand() - 0.5) * 1.0, radii[k] * Math.sin(th)]);
    else {
      const r = radii[k] * Math.sqrt(rand());
      sets[2].push([r * Math.cos(th), y + 0.5, r * Math.sin(th)]);
    }
  }
  // 4. Credit travels with the code: a double helix with a pulse running along it.
  for (let i = 0; i < N; i++) {
    const strand = i % 3;
    let t = rand();
    if (strand === 2) t = Math.floor(t * 30) / 30;
    const y = (t - 0.5) * 13.5;
    const ang = t * TAU * 2.6;
    let p;
    if (strand < 2) {
      const a = ang + (strand === 1 ? Math.PI : 0);
      p = [2.6 * Math.cos(a) + (rand() - 0.5) * 0.45, y, 2.6 * Math.sin(a) + (rand() - 0.5) * 0.45];
    } else {
      const s = rand();
      const x1 = 2.6 * Math.cos(ang), z1 = 2.6 * Math.sin(ang);
      p = [x1 * (1 - 2 * s), y, z1 * (1 - 2 * s)];
    }
    sets[3].push(p);
    helixT[i] = t;
  }

  // Order every set by height band, then angle, so index i maps to a similar place in all four.
  const order = (pts) => {
    const keyed = pts.map((p, i) => {
      const band = Math.floor((p[1] / 14 + 0.5) * 36);
      const az = (Math.atan2(p[2], p[0]) + Math.PI) / TAU;
      return [band * 10 + az * 9.99, i];
    });
    keyed.sort((a, b) => a[0] - b[0]);
    return keyed.map((k) => k[1]);
  };
  for (let s = 0; s < 4; s++) {
    const ord = order(sets[s]);
    for (let i = 0; i < N; i++) {
      const p = sets[s][ord[i]];
      T[s][i * 3] = p[0];
      T[s][i * 3 + 1] = p[1];
      T[s][i * 3 + 2] = p[2];
    }
  }
  // helixT must follow the same ordering as set 3.
  const ord3 = order(sets[3]);
  const helixSorted = new Float32Array(N);
  for (let i = 0; i < N; i++) helixSorted[i] = helixT[ord3[i]];

  const Rf = 46;
  for (let i = 0; i < N; i++) {
    const u = rand() * 2 - 1, th = rand() * TAU, s = Math.sqrt(1 - u * u);
    const r = Rf * Math.cbrt(rand());
    field[i * 3] = r * s * Math.cos(th);
    field[i * 3 + 1] = r * u * 0.5;
    field[i * 3 + 2] = r * s * Math.sin(th);
    seed.set([rand(), helixSorted[i], rand(), rand()], i * 4);
  }
  return { T, field, seed };
}


// Hairline wireframes for the four shapes (same segment count in each, so they morph like the
// points do). Fewer than 520 real segments are padded with zero-length ones.
function buildWires() {
  const M = 520;
  const segs = [[], [], [], []];
  const loop = (list, fn, n) => {
    for (let i = 0; i < n; i++) {
      const a = fn(i / n);
      const b = fn((i + 1) / n);
      list.push([a[0], a[1], a[2], b[0], b[1], b[2]]);
    }
  };
  const R = 7.2;
  for (let k = 0; k < 8; k++) {
    const phi = (k * Math.PI) / 8;
    loop(segs[0], (t) => { const a = t * TAU; const x = R * Math.cos(a); return [x * Math.cos(phi), R * Math.sin(a), x * Math.sin(phi)]; }, 40);
  }
  for (const lat of [-60, -30, 0, 30, 60]) {
    const th = (lat * Math.PI) / 180;
    loop(segs[0], (t) => { const a = t * TAU; return [R * Math.cos(th) * Math.cos(a), R * Math.sin(th), R * Math.cos(th) * Math.sin(a)]; }, 40);
  }
  for (let k = 0; k < 6; k++) {
    const b = (k * TAU) / 6;
    const rr = 4.3 + 0.62 * Math.cos(b);
    const off = 0.62 * Math.sin(b);
    loop(segs[1], (t) => { const a = t * TAU; return [-2.7 + rr * Math.cos(a), rr * Math.sin(a), off]; }, 40);
    loop(segs[1], (t) => { const a = t * TAU; return [2.7 + rr * Math.cos(a), off, rr * Math.sin(a)]; }, 40);
  }
  const radii = [6.6, 5.5, 4.4, 3.3, 2.2];
  for (let k = 0; k < 5; k++) {
    const y = -4.4 + k * 2.2;
    for (const dy of [-0.5, 0.5]) loop(segs[2], (t) => { const a = t * TAU; return [radii[k] * Math.cos(a), y + dy, radii[k] * Math.sin(a)]; }, 40);
    for (let j = 0; j < 6; j++) {
      const a = (j * TAU) / 6;
      segs[2].push([radii[k] * Math.cos(a), y - 0.5, radii[k] * Math.sin(a), radii[k] * Math.cos(a), y + 0.5, radii[k] * Math.sin(a)]);
    }
  }
  const hel = (rad, ph, t) => { const a = t * TAU * 2.6 + ph; return [rad * Math.cos(a), (t - 0.5) * 13.5, rad * Math.sin(a)]; };
  for (const [rad, ph] of [[2.6, 0], [2.6, Math.PI], [3.1, 0.6], [3.1, Math.PI + 0.6]]) {
    for (let i = 0; i < 100; i++) segs[3].push([...hel(rad, ph, i / 100), ...hel(rad, ph, (i + 1) / 100)]);
  }
  for (let i = 0; i < 30; i++) {
    const t = (i + 0.5) / 30;
    segs[3].push([...hel(2.6, 0, t), ...hel(2.6, Math.PI, t)]);
  }
  const T = [0, 1, 2, 3].map((s) => {
    const arr = new Float32Array(M * 6);
    segs[s].slice(0, M).forEach((seg, i) => arr.set(seg, i * 6));
    return arr;
  });
  const end = new Float32Array(M * 2);
  for (let i = 0; i < M; i++) end[i * 2 + 1] = 1;
  return { T, end, M };
}

function buildDust(M) {
  const rand = mulberry32(7);
  const pos = new Float32Array(M * 3);
  const sd = new Float32Array(M * 3);
  for (let i = 0; i < M; i++) {
    pos[i * 3] = (rand() * 2 - 1) * 48;
    pos[i * 3 + 1] = (rand() * 2 - 1) * 28;
    pos[i * 3 + 2] = 14 - rand() * 330;
    sd[i * 3] = rand();
    sd[i * 3 + 1] = rand();
    sd[i * 3 + 2] = 1;
  }
  return { pos, sd };
}

/* --------------------------------------------------------------- shaders */

const COMMON = /* glsl */ `
#define PI_ 3.14159265359
vec2 rot2(vec2 v, float a){ float c = cos(a), s = sin(a); return vec2(c * v.x - s * v.y, s * v.x + c * v.y); }
`;

const STAR_MOTION = /* glsl */ `
attribute vec3 aCenter;
attribute vec3 aLocal;
attribute vec3 aFinal;
attribute vec4 aSeed;
attribute float aCluster;
uniform float uTime, uBloom, uConverge, uMode, uLat, uFinalScale;
uniform vec3 uOrigin0, uOrigin1, uConv;

vec3 starPos(out float born) {
  vec3 home; vec3 org; float conv;
  if (uMode < 0.5) {
    home = vec3(aCenter.xy * uLat, aCenter.z) + aLocal;
    org = uOrigin0; conv = uConverge;
  } else {
    home = uOrigin1 + aFinal * uFinalScale;
    org = uOrigin1; conv = 0.0;
  }
  float delay = (aCluster / 12.0) * 0.55 + aSeed.x * 0.10;
  float bt = clamp((uBloom - delay) / 0.35, 0.0, 1.0);
  float e = 1.0 - pow(1.0 - bt, 3.0);
  vec3 p = mix(org, home, e);
  vec3 side = normalize(cross(home - org, vec3(0.0, 1.0, 0.0)) + vec3(0.0001));
  float arc = sin(bt * PI_);
  p += side * arc * (aSeed.y - 0.5) * 7.0;
  p.y += arc * (aSeed.z - 0.5) * 4.0;
  float t = uTime * 0.25;
  p += vec3(sin(t + aSeed.x * 40.0), cos(t * 1.1 + aSeed.y * 40.0), sin(t * 0.9 + aSeed.z * 40.0)) * 0.12 * e;
  float cdel = clamp(length(home - uConv) / 190.0, 0.0, 1.0) * 0.42;
  float ct = clamp((conv - cdel) / 0.58, 0.0, 1.0);
  float ec = ct * ct * (3.0 - 2.0 * ct);
  ec = ec * ec * (3.0 - 2.0 * ec);
  vec3 d = p - uConv;
  d.xy = rot2(d.xy, ct * (1.0 - ec) * 2.6 * (aSeed.w - 0.5));
  p = uConv + d * (1.0 - ec);
  born = bt;
  return p;
}
`;

const POINT_FRAG = /* glsl */ `
precision highp float;
varying vec3 vCol;
varying float vA;
varying vec2 vDir;
varying float vB;
void main() {
  vec2 c = (gl_PointCoord - 0.5) * 2.0;
  c.y = -c.y;
  vec2 q = vec2(dot(c, vDir), dot(c, vec2(-vDir.y, vDir.x)) * vB);
  float r2 = dot(q, q);
  float core = exp(-r2 * 26.0);
  float halo = exp(-r2 * 5.0) * 0.34;
  float al = vA * (core + halo);
  if (al < 0.004) discard;
  gl_FragColor = vec4(vCol * (0.55 + core * 0.9), al);
}
`;

const STAR_POINT_VERT = /* glsl */ `
${COMMON}
${STAR_MOTION}
attribute float aSize;
attribute float aTone;
uniform float uPx, uAlpha, uStreak, uDissent, uFogS, uMaxPt;
varying vec3 vCol;
varying float vA;
varying vec2 vDir;
varying float vB;
void main() {
  float born;
  vec3 p = starPos(born);
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vec4 clip = projectionMatrix * mv;
  float dist = max(-mv.z, 0.01);
  float near = smoothstep(0.5, 2.8, dist);
  float far = 1.0 - smoothstep(55.0 * uFogS, 125.0 * uFogS, dist);
  float tw = 0.8 + 0.2 * sin(uTime * 1.3 + aSeed.x * 60.0);
  float isD = step(0.5, aTone);
  float alive = smoothstep(0.1, 0.5, born);
  float grow = mix(0.3, 1.0, smoothstep(0.0, 0.7, born));
  vA = near * far * tw * alive * uAlpha * (1.0 + isD * uDissent * 1.6);
  float sz = aSize * grow * uPx * (30.0 / dist) * (1.0 + isD * uDissent * 2.0);
  vec2 ndc = clip.xy / max(clip.w, 0.001);
  float rad = length(ndc);
  vB = 1.0 + uStreak * 2.4 * (0.25 + rad);
  vDir = ndc / max(rad, 0.0001);
  gl_PointSize = clamp(sz * vB, 1.0, uMaxPt);
  gl_Position = clip;
  vCol = mix(vec3(0.60, 0.77, 1.0), vec3(1.0, 0.70, 0.42), isD);
}
`;

const STAR_LINE_VERT = /* glsl */ `
${COMMON}
${STAR_MOTION}
attribute float aEnd;
attribute float aKind;
attribute float aESeed;
uniform float uLineAlpha, uFogS;
varying float vEnd;
varying float vESeed;
varying float vA;
void main() {
  float born;
  vec3 p = starPos(born);
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  float dist = max(-mv.z, 0.01);
  float near = smoothstep(0.5, 3.0, dist);
  float far = 1.0 - smoothstep(55.0 * uFogS, 125.0 * uFogS, dist);
  float alive = smoothstep(0.05, 0.35, born);
  float kind = (uMode < 0.5) ? (1.0 - aKind) : mix(0.75, 0.5, aKind);
  vA = uLineAlpha * 0.26 * near * far * alive * kind;
  vEnd = aEnd;
  vESeed = aESeed;
  gl_Position = projectionMatrix * mv;
}
`;

const STAR_LINE_FRAG = /* glsl */ `
precision highp float;
uniform float uTime;
varying float vEnd;
varying float vESeed;
varying float vA;
void main() {
  float ph = fract(uTime * 0.18 + vESeed);
  float spark = exp(-pow((ph - vEnd) * 5.0, 2.0));
  float a = vA * (1.0 + spark * 3.2);
  if (a < 0.003) discard;
  gl_FragColor = vec4(vec3(0.50, 0.68, 1.0) * (0.8 + spark), a);
}
`;

const DUST_VERT = /* glsl */ `
${COMMON}
attribute vec3 aSD;
uniform float uTime, uPx, uAlpha, uStreak, uFogS, uMaxPt;
varying vec3 vCol;
varying float vA;
varying vec2 vDir;
varying float vB;
void main() {
  vec3 p = position;
  p.xy += vec2(sin(uTime * 0.07 + aSD.x * 30.0), cos(uTime * 0.06 + aSD.y * 30.0)) * 0.6 * step(aSD.z, 1.5);
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vec4 clip = projectionMatrix * mv;
  float dist = max(-mv.z, 0.01);
  float near = smoothstep(1.0, 6.0, dist);
  float far = 1.0 - smoothstep(50.0 * uFogS, 110.0 * uFogS, dist);
  float tw = 0.65 + 0.35 * sin(uTime * (0.6 + aSD.x) + aSD.y * 50.0);
  vA = near * far * tw * uAlpha * (0.35 + aSD.y * 0.65);
  float sz = (1.4 + aSD.x * 2.2) * aSD.z * uPx * (30.0 / dist);
  vec2 ndc = clip.xy / max(clip.w, 0.001);
  float rad = length(ndc);
  vB = 1.0 + uStreak * 2.4 * (0.25 + rad);
  vDir = ndc / max(rad, 0.0001);
  gl_PointSize = clamp(sz * vB, 1.0, uMaxPt);
  gl_Position = clip;
  vCol = mix(vec3(0.55, 0.72, 1.0), vec3(0.85, 0.92, 1.0), aSD.x);
}
`;

const SHAPE_VERT = /* glsl */ `
${COMMON}
attribute vec3 aT0;
attribute vec3 aT1;
attribute vec3 aT2;
attribute vec3 aT3;
attribute vec3 aField;
attribute vec4 aSeed;
uniform float uMorph, uAppear, uDisperse, uSpin, uTime, uPx, uAlpha, uStreak, uFogS, uMaxPt;
uniform vec3 uCenter;
varying vec3 vCol;
varying float vA;
varying vec2 vDir;
varying float vB;
vec3 pick(float i) { return i < 0.5 ? aT0 : (i < 1.5 ? aT1 : (i < 2.5 ? aT2 : aT3)); }
void main() {
  float m = clamp(uMorph, 0.0, 3.0);
  float i0 = floor(min(m, 2.9999));
  float f = m - i0;
  vec3 a = pick(i0);
  vec3 b = pick(i0 + 1.0);
  float e = f * f * (3.0 - 2.0 * f);
  e = e * e * (3.0 - 2.0 * e);
  vec3 p = mix(a, b, e);
  float mid = sin(PI_ * e);
  float n = aSeed.x * 6.2831853;
  p += vec3(cos(n * 3.0 + uTime * 0.8), sin(n * 2.0 + uTime * 1.1), cos(n * 5.0 + uTime * 0.6)) * mid * 2.4 * (0.35 + aSeed.z);
  p.xz = rot2(p.xz, uSpin);
  p *= 1.0 + 0.012 * sin(uTime * 0.8 + aSeed.z * 6.0);
  vec3 fp = aField;
  fp.xz = rot2(fp.xz, uTime * 0.012);
  float dd = clamp(uDisperse * 1.3 - aSeed.z * 0.3, 0.0, 1.0);
  dd = dd * dd * (3.0 - 2.0 * dd);
  p = mix(p, fp, dd);
  float ap = clamp(uAppear * 1.35 - aSeed.x * 0.35, 0.0, 1.0);
  ap = 1.0 - pow(1.0 - ap, 3.0);
  p *= ap;
  vec4 mv = modelViewMatrix * vec4(uCenter + p, 1.0);
  vec4 clip = projectionMatrix * mv;
  float dist = max(-mv.z, 0.01);
  float near = smoothstep(0.8, 4.0, dist);
  float far = 1.0 - smoothstep(70.0 * uFogS, 150.0 * uFogS, dist);

  float w1 = max(0.0, 1.0 - abs(uMorph - 1.0));
  float w2 = max(0.0, 1.0 - abs(uMorph - 2.0));
  float w3 = clamp(uMorph - 2.0, 0.0, 1.0) * (1.0 - dd);
  float amb = step(0.93, aSeed.w) * w1;
  float hi = smoothstep(2.6, 3.2, p.y) * w2 * (1.0 - dd);
  float pulse = exp(-pow((fract(uTime * 0.11) - aSeed.y) * 12.0, 2.0)) * w3;

  vec3 col = mix(vec3(0.55, 0.72, 1.0), vec3(0.93, 0.96, 1.0), aSeed.z);
  col = mix(col, vec3(1.0, 0.72, 0.42), amb);
  vA = near * far * uAlpha * ap * (0.95 + hi * 0.9 + pulse * 1.6 + amb * 0.6);
  float sz = (2.6 + aSeed.z * 2.8) * uPx * (30.0 / dist) * (1.0 + hi * 0.8 + pulse * 1.8 + amb * 0.6);
  vec2 ndc = clip.xy / max(clip.w, 0.001);
  float rad = length(ndc);
  vB = 1.0 + uStreak * 2.4 * (0.25 + rad);
  vDir = ndc / max(rad, 0.0001);
  gl_PointSize = clamp(sz * vB, 1.0, uMaxPt);
  gl_Position = clip;
  vCol = col;
}
`;


const WIRE_VERT = /* glsl */ `
${COMMON}
attribute vec3 aT0;
attribute vec3 aT1;
attribute vec3 aT2;
attribute vec3 aT3;
uniform float uMorph, uAppear, uDisperse, uSpin, uTime, uAlpha, uFogS;
uniform vec3 uCenter;
varying float vA;
vec3 pick(float i) { return i < 0.5 ? aT0 : (i < 1.5 ? aT1 : (i < 2.5 ? aT2 : aT3)); }
void main() {
  float m = clamp(uMorph, 0.0, 3.0);
  float i0 = floor(min(m, 2.9999));
  float f = m - i0;
  vec3 a = pick(i0);
  vec3 b = pick(i0 + 1.0);
  float e = f * f * (3.0 - 2.0 * f);
  e = e * e * (3.0 - 2.0 * e);
  vec3 p = mix(a, b, e);
  float mid = sin(PI_ * e);
  p.xz = rot2(p.xz, uSpin);
  p *= 1.0 + 0.012 * sin(uTime * 0.8);
  float ap = clamp(uAppear * 1.35 - 0.1, 0.0, 1.0);
  ap = 1.0 - pow(1.0 - ap, 3.0);
  p *= ap;
  vec4 mv = modelViewMatrix * vec4(uCenter + p, 1.0);
  float dist = max(-mv.z, 0.01);
  float far = 1.0 - smoothstep(70.0 * uFogS, 150.0 * uFogS, dist);
  vA = uAlpha * ap * far * (1.0 - mid * 0.92) * (1.0 - smoothstep(0.0, 0.3, uDisperse));
  gl_Position = projectionMatrix * mv;
}
`;
const WIRE_FRAG = /* glsl */ `
precision highp float;
varying float vA;
void main() { gl_FragColor = vec4(vec3(0.62, 0.78, 1.0), vA * 0.32); }
`;

const FLARE_VERT = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;
// The point of light: a tiny white core and a soft blue glow (small quad), plus a thin
// horizontal anamorphic streak (a separate thin quad), the way a wide lens renders a bright
// point in a dark room. Two small quads instead of one screen-sized one keeps fill cost low;
// the wide soft halo lives in the background shader.
const GLOW_FRAG = /* glsl */ `
precision highp float;
uniform float uI;
uniform vec3 uCol;
varying vec2 vUv;
void main() {
  vec2 w = (vUv - 0.5) * 16.0;
  float r2 = dot(w, w);
  float core = exp(-r2 * 6.5);
  float glow = exp(-r2 * 0.22) * 0.5;
  float sy = exp(-abs(w.x) * 1.8) * exp(-abs(w.y) * 0.2) * 0.08;
  float edge = (1.0 - smoothstep(5.5, 8.0, abs(w.x))) * (1.0 - smoothstep(5.5, 8.0, abs(w.y)));
  vec3 c = uCol * (glow + sy) + vec3(1.0) * core;
  gl_FragColor = vec4(c * uI * edge, 1.0);
}
`;
const STREAK_FRAG = /* glsl */ `
precision highp float;
uniform float uI;
uniform vec3 uCol;
varying vec2 vUv;
void main() {
  vec2 w = (vUv - 0.5) * vec2(56.0, 4.0);
  float sx = exp(-abs(w.y) * 5.0) * exp(-abs(w.x) * 0.122);
  float sx2 = exp(-abs(w.y) * 13.6) * exp(-abs(w.x) * 0.0727);
  float edge = (1.0 - smoothstep(20.0, 28.0, abs(w.x))) * (1.0 - smoothstep(1.2, 2.0, abs(w.y)));
  vec3 c = uCol * sx * 0.7 + vec3(1.0) * sx2 * 0.5;
  gl_FragColor = vec4(c * uI * edge, 1.0);
}
`;

const BG_VERT = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = position.xy * 0.5 + 0.5;
  gl_Position = vec4(position.xy, 0.9999, 1.0);
}
`;
const BG_FRAG = /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform float uGrade, uTime, uAspect, uGlowAmt, uStage;
uniform vec2 uGlowPos;
float ign(vec2 p) { return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }
void main() {
  vec2 uv = vUv;
  vec3 dark = mix(vec3(0.008, 0.013, 0.030), vec3(0.015, 0.024, 0.056), uv.y);
  vec2 q = (uv - vec2(0.5, 0.52)) * vec2(uAspect, 1.0);
  float vig = 1.0 - smoothstep(0.1, 1.15, length(q));
  vec3 blue = mix(vec3(0.014, 0.032, 0.16), vec3(0.07, 0.15, 0.60), vig * vig);
  vec3 col = mix(dark, blue, uGrade);
  vec2 g = (uv - uGlowPos) * vec2(uAspect, 1.0);
  col += vec3(0.08, 0.15, 0.40) * uGlowAmt * exp(-dot(g, g) * 9.0);
  vec2 g2 = (uv - vec2(0.5, 0.40)) * vec2(uAspect, 1.0);
  col += vec3(0.04, 0.08, 0.23) * uStage * exp(-dot(g2, g2) * 3.0);
  col += (ign(gl_FragCoord.xy + fract(uTime) * 91.0) - 0.5) * (1.7 / 255.0);
  gl_FragColor = vec4(col, 1.0);
}
`;
const FLASH_FRAG = /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform float uFlash, uAspect;
void main() {
  vec2 q = (vUv - 0.5) * vec2(uAspect, 1.0);
  float f = uFlash * (0.14 + 1.25 * exp(-dot(q, q) * 6.0));
  gl_FragColor = vec4(vec3(0.66, 0.8, 1.0) * f, 1.0);
}
`;

/* ----------------------------------------------------------------- world */

export function createWorld({ canvas, lite, onLost }) {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: !lite,
      alpha: false,
      depth: false,
      stencil: false,
      powerPreference: 'high-performance',
    });
  } catch (e) {
    return null;
  }
  renderer.setClearColor(0x03050b, 1);
  renderer.sortObjects = false;
  const gl = renderer.getContext();
  const maxPt = Math.min(256, (gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE) || [1, 64])[1]);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 700);
  const clock = { w: 1, h: 1, dpr: 1 };

  const shared = {
    uTime: { value: 0 },
    uPx: { value: 1 },
    uMaxPt: { value: maxPt },
    uFogS: { value: 1 },
    uStreak: { value: 0 },
  };
  const additive = { transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending };

  // Background, drawn first.
  const bgMat = new THREE.ShaderMaterial({
    vertexShader: BG_VERT,
    fragmentShader: BG_FRAG,
    depthTest: false,
    depthWrite: false,
    uniforms: { uGrade: { value: 0 }, uTime: shared.uTime, uAspect: { value: 1 }, uGlowAmt: { value: 0 }, uStage: { value: 0 }, uGlowPos: { value: new THREE.Vector2(0.5, 0.67) } },
  });
  const tri = new THREE.BufferGeometry();
  tri.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
  const bg = new THREE.Mesh(tri, bgMat);
  bg.frustumCulled = false;
  bg.renderOrder = -10;
  scene.add(bg);

  // Dust: a long tube of faint points that gives the flight its sense of speed.
  const dustN = lite ? 650 : 1700;
  const dustData = buildDust(dustN);
  const dustGeo = new THREE.BufferGeometry();
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustData.pos, 3));
  dustGeo.setAttribute('aSD', new THREE.BufferAttribute(dustData.sd, 3));
  const dustMat = new THREE.ShaderMaterial({
    vertexShader: DUST_VERT,
    fragmentShader: POINT_FRAG,
    ...additive,
    uniforms: { ...shared, uAlpha: { value: 0 } },
  });
  const dust = new THREE.Points(dustGeo, dustMat);
  dust.frustumCulled = false;
  dust.renderOrder = 1;
  scene.add(dust);

  // Constellations.
  const sd = buildStars();
  const starUniforms = {
    ...shared,
    uBloom: { value: 0 },
    uConverge: { value: 0 },
    uMode: { value: 0 },
    uLat: { value: 1 },
    uFinalScale: { value: 1 },
    uOrigin0: { value: new THREE.Vector3(0, 0, 0) },
    uOrigin1: { value: new THREE.Vector3(...LAYOUT.S) },
    uConv: { value: new THREE.Vector3(...LAYOUT.C) },
    uAlpha: { value: 0 },
    uDissent: { value: 0 },
    uLineAlpha: { value: 0 },
  };
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(sd.total * 3), 3));
  starGeo.setAttribute('aCenter', new THREE.BufferAttribute(sd.center, 3));
  starGeo.setAttribute('aLocal', new THREE.BufferAttribute(sd.local, 3));
  starGeo.setAttribute('aFinal', new THREE.BufferAttribute(sd.fin, 3));
  starGeo.setAttribute('aSeed', new THREE.BufferAttribute(sd.seed, 4));
  starGeo.setAttribute('aCluster', new THREE.BufferAttribute(sd.cluster, 1));
  starGeo.setAttribute('aSize', new THREE.BufferAttribute(sd.size, 1));
  starGeo.setAttribute('aTone', new THREE.BufferAttribute(sd.tone, 1));
  const starMat = new THREE.ShaderMaterial({ vertexShader: STAR_POINT_VERT, fragmentShader: POINT_FRAG, ...additive, uniforms: starUniforms });
  const stars = new THREE.Points(starGeo, starMat);
  stars.frustumCulled = false;
  stars.renderOrder = 3;

  const lineGeo = new THREE.BufferGeometry();
  lineGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(sd.edgeCount * 6), 3));
  lineGeo.setAttribute('aCenter', new THREE.BufferAttribute(sd.L.center, 3));
  lineGeo.setAttribute('aLocal', new THREE.BufferAttribute(sd.L.local, 3));
  lineGeo.setAttribute('aFinal', new THREE.BufferAttribute(sd.L.fin, 3));
  lineGeo.setAttribute('aSeed', new THREE.BufferAttribute(sd.L.seed, 4));
  lineGeo.setAttribute('aCluster', new THREE.BufferAttribute(sd.L.cluster, 1));
  lineGeo.setAttribute('aEnd', new THREE.BufferAttribute(sd.L.end, 1));
  lineGeo.setAttribute('aKind', new THREE.BufferAttribute(sd.L.kind, 1));
  lineGeo.setAttribute('aESeed', new THREE.BufferAttribute(sd.L.eseed, 1));
  const lineMat = new THREE.ShaderMaterial({ vertexShader: STAR_LINE_VERT, fragmentShader: STAR_LINE_FRAG, ...additive, uniforms: starUniforms });
  const lines = new THREE.LineSegments(lineGeo, lineMat);
  lines.frustumCulled = false;
  lines.renderOrder = 2;
  scene.add(lines, stars);

  // The four rule shapes.
  const shapeN = lite ? 3000 : 9000;
  const shp = buildShapes(shapeN, lite);
  const shapeGeo = new THREE.BufferGeometry();
  shapeGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(shapeN * 3), 3));
  shapeGeo.setAttribute('aT0', new THREE.BufferAttribute(shp.T[0], 3));
  shapeGeo.setAttribute('aT1', new THREE.BufferAttribute(shp.T[1], 3));
  shapeGeo.setAttribute('aT2', new THREE.BufferAttribute(shp.T[2], 3));
  shapeGeo.setAttribute('aT3', new THREE.BufferAttribute(shp.T[3], 3));
  shapeGeo.setAttribute('aField', new THREE.BufferAttribute(shp.field, 3));
  shapeGeo.setAttribute('aSeed', new THREE.BufferAttribute(shp.seed, 4));
  const shapeUniforms = {
    ...shared,
    uMorph: { value: 0 }, uAppear: { value: 0 }, uDisperse: { value: 0 }, uSpin: { value: 0 }, uAlpha: { value: 1 },
    uCenter: { value: new THREE.Vector3(...LAYOUT.S) },
  };
  const shape = new THREE.Points(shapeGeo, new THREE.ShaderMaterial({ vertexShader: SHAPE_VERT, fragmentShader: POINT_FRAG, ...additive, uniforms: shapeUniforms }));
  shape.frustumCulled = false;
  shape.renderOrder = 4;
  const wr = buildWires();
  const wireGeo = new THREE.BufferGeometry();
  wireGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(wr.M * 6), 3));
  for (let k = 0; k < 4; k++) wireGeo.setAttribute('aT' + k, new THREE.BufferAttribute(wr.T[k], 3));
  const wires = new THREE.LineSegments(wireGeo, new THREE.ShaderMaterial({ vertexShader: WIRE_VERT, fragmentShader: WIRE_FRAG, ...additive, uniforms: shapeUniforms }));
  wires.frustumCulled = false;
  scene.add(wires, shape);

  // The ring of adapters: 16 nodes (one per adapter) on a tilted, spinning ring around the point C. main.js labels six of them.
  const NODES = 16;
  const ringRoot = new THREE.Group();
  ringRoot.position.set(...LAYOUT.C);
  const tilt = new THREE.Group();
  tilt.rotation.x = 0.3;
  const spin = new THREE.Group();
  ringRoot.add(tilt);
  tilt.add(spin);
  const ringPts = [];
  for (let i = 0; i < 160; i++) {
    const a = (i / 160) * TAU;
    ringPts.push(new THREE.Vector3(Math.cos(a), 0, Math.sin(a)));
  }
  const ringLineGeo = new THREE.BufferGeometry().setFromPoints(ringPts);
  const ringLineMat = new THREE.LineBasicMaterial({ color: 0x7ea6ff, transparent: true, opacity: 0, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending });
  const ringLine = new THREE.LineLoop(ringLineGeo, ringLineMat);
  ringLine.frustumCulled = false;
  const nodePos = new Float32Array(NODES * 3);
  const nodeSD = new Float32Array(NODES * 3);
  for (let i = 0; i < NODES; i++) {
    const a = (i / NODES) * TAU;
    nodePos.set([Math.cos(a), 0, Math.sin(a)], i * 3);
    nodeSD.set([0.8, 1, 4.2], i * 3);
  }
  const nodeGeo = new THREE.BufferGeometry();
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(nodePos, 3));
  nodeGeo.setAttribute('aSD', new THREE.BufferAttribute(nodeSD, 3));
  const nodeMat = new THREE.ShaderMaterial({ vertexShader: DUST_VERT, fragmentShader: POINT_FRAG, ...additive, uniforms: { ...shared, uAlpha: { value: 0 } } });
  const nodes = new THREE.Points(nodeGeo, nodeMat);
  nodes.frustumCulled = false;
  const rdN = lite ? 70 : 150;
  const rdPos = new Float32Array(rdN * 3);
  const rdSD = new Float32Array(rdN * 3);
  const rr = mulberry32(16);
  for (let i = 0; i < rdN; i++) {
    const a = rr() * TAU;
    const r = 1 + (rr() - 0.5) * 0.09;
    rdPos.set([Math.cos(a) * r, (rr() - 0.5) * 0.06, Math.sin(a) * r], i * 3);
    rdSD.set([rr(), rr(), 1.6], i * 3);
  }
  const rdGeo = new THREE.BufferGeometry();
  rdGeo.setAttribute('position', new THREE.BufferAttribute(rdPos, 3));
  rdGeo.setAttribute('aSD', new THREE.BufferAttribute(rdSD, 3));
  const rdMat = new THREE.ShaderMaterial({ vertexShader: DUST_VERT, fragmentShader: POINT_FRAG, ...additive, uniforms: { ...shared, uAlpha: { value: 0 } } });
  const ringDust = new THREE.Points(rdGeo, rdMat);
  ringDust.frustumCulled = false;
  spin.add(ringLine, nodes, ringDust);
  ringRoot.renderOrder = 5;
  scene.add(ringRoot);

  // The point of light.
  const flareU = { uI: { value: 1 }, uCol: { value: new THREE.Color(0.36, 0.55, 1.0) } };
  const flareGlow = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), new THREE.ShaderMaterial({ vertexShader: FLARE_VERT, fragmentShader: GLOW_FRAG, ...additive, uniforms: flareU }));
  const flareStreak = new THREE.Mesh(new THREE.PlaneGeometry(56, 4), new THREE.ShaderMaterial({ vertexShader: FLARE_VERT, fragmentShader: STREAK_FRAG, ...additive, uniforms: flareU }));
  for (const m of [flareStreak, flareGlow]) {
    m.frustumCulled = false;
    m.renderOrder = 6;
    scene.add(m);
  }

  // Whiteout used while the camera passes through the point.
  const flashMat = new THREE.ShaderMaterial({
    vertexShader: BG_VERT,
    fragmentShader: FLASH_FRAG,
    ...additive,
    uniforms: { uFlash: { value: 0 }, uAspect: { value: 1 } },
  });
  const flashMesh = new THREE.Mesh(tri, flashMat);
  flashMesh.frustumCulled = false;
  flashMesh.renderOrder = 100;
  scene.add(flashMesh);

  /* ------------------------------------------------------------ runtime */

  const flarePositions = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(...LAYOUT.C), new THREE.Vector3(...LAYOUT.S)];
  const tmp = new THREE.Vector3();
  const tmp2 = new THREE.Vector3();
  const look = new THREE.Vector3();
  const nodesOut = Array.from({ length: NODES }, () => ({ x: 0, y: 0, depth: 0, front: false }));
  let alive = true;

  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    alive = false;
    if (onLost) onLost();
  });
  canvas.addEventListener('webglcontextrestored', () => { alive = true; });

  function resize(w, h, dpr, vh) {
    clock.w = w;
    clock.h = h;
    clock.dpr = dpr;
    renderer.setPixelRatio(dpr);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    shared.uPx.value = dpr * Math.min(1.4, Math.max(0.62, (vh || h) / 900));
    bgMat.uniforms.uAspect.value = w / h;
    flashMat.uniforms.uAspect.value = w / h;
  }

  function update(P, time, pointer, view) {
    if (!alive) return null;
    const c = P.cam;
    shared.uTime.value = time;
    shared.uFogS.value = P.fog;
    shared.uStreak.value = P.streak;

    // Camera: base pose, then a small parallax offset that keeps the target centred.
    camera.fov = c.fov;
    camera.position.set(c.px, c.py, c.pz);
    look.set(c.lx, c.ly, c.lz);
    camera.up.set(0, 1, 0);
    camera.lookAt(look);
    if (pointer && (pointer.x || pointer.y)) {
      tmp.setFromMatrixColumn(camera.matrix, 0).multiplyScalar(pointer.x * 0.55);
      tmp2.setFromMatrixColumn(camera.matrix, 1).multiplyScalar(pointer.y * 0.4);
      camera.position.add(tmp).add(tmp2);
      camera.lookAt(look);
    }
    if (c.roll) camera.rotateZ(c.roll);
    // Composition offset: slide the image inside the frame without moving the camera.
    const W = clock.w, H = clock.h;
    const sy = P.shiftY + (view.baseShiftY || 0);
    if (P.shiftX || sy) camera.setViewOffset(W, H, -P.shiftX * W, sy * H, W, H);
    else camera.clearViewOffset();
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);

    // Dust and stars.
    dustMat.uniforms.uAlpha.value = 0.55 * P.dust;
    starUniforms.uBloom.value = P.bloom;
    starUniforms.uConverge.value = P.converge;
    starUniforms.uMode.value = P.mode;
    starUniforms.uAlpha.value = P.starAlpha * 1.15;
    starUniforms.uLineAlpha.value = P.lineAlpha;
    starUniforms.uDissent.value = P.dissent;
    starUniforms.uLat.value = view.lat;
    starUniforms.uFinalScale.value = view.portrait ? 0.62 : 1;

    // Shapes.
    shapeUniforms.uMorph.value = P.shapeMorph;
    shapeUniforms.uAppear.value = P.shapeAppear;
    shapeUniforms.uDisperse.value = P.shapeDisperse;
    shapeUniforms.uSpin.value = P.shapeSpin;
    shapeUniforms.uAlpha.value = P.shapeAlpha * 0.9;
    shape.visible = wires.visible = P.shapeAppear > 0.001;

    // The point of light follows its stage: origin, then C, then S.
    const fp = flarePositions[P.flareAt];
    const dist = camera.position.distanceTo(fp);
    const fs = Math.min(P.flareAt === 2 ? 2.2 : 4.5, Math.max(0.8, dist / 16));
    for (const m of [flareGlow, flareStreak]) {
      m.position.copy(fp);
      m.quaternion.copy(camera.quaternion);
      m.scale.set(fs, fs, 1);
      m.visible = P.flare > 0.002;
    }
    flareU.uI.value = P.flare;
    bgMat.uniforms.uGrade.value = P.grade;
    bgMat.uniforms.uGlowAmt.value = Math.min(1.0, P.flare * 0.3);
    bgMat.uniforms.uStage.value = P.stage;
    tmp.copy(fp).project(camera);
    bgMat.uniforms.uGlowPos.value.set(tmp.x * 0.5 + 0.5, tmp.y * 0.5 + 0.5);
    flashMat.uniforms.uFlash.value = P.flash;
    flashMesh.visible = P.flash > 0.003;

    // Ring: radius is set in screen pixels so it always fits the DOM window beside it.
    const ringOn = P.ring > 0.002;
    ringRoot.visible = ringOn;
    let ringR = 1;
    if (ringOn) {
      const d = camera.position.distanceTo(ringRoot.position);
      const halfH = d * Math.tan((camera.fov * Math.PI) / 360);
      ringR = (view.ringRadiusPx / (H / 2)) * halfH * Math.min(1, P.ring * 1.15);
      ringRoot.rotation.z = view.portrait ? Math.PI / 2 : 0; // tall ellipse on portrait screens
      spin.rotation.y = P.ringSpin + time * 0.07;
      spin.scale.setScalar(ringR);
      ringRoot.updateMatrixWorld(true);
      ringLineMat.opacity = 0.34 * P.ring;
      nodeMat.uniforms.uAlpha.value = 1.1 * P.ring;
      rdMat.uniforms.uAlpha.value = 0.55 * P.ring;
      const dc = d;
      for (let i = 0; i < NODES; i++) {
        const a = (i / NODES) * TAU;
        tmp.set(Math.cos(a), 0, Math.sin(a));
        spin.localToWorld(tmp);
        const depth = -tmp2.copy(tmp).applyMatrix4(camera.matrixWorldInverse).z;
        tmp.project(camera);
        const o = nodesOut[i];
        o.x = (tmp.x * 0.5 + 0.5) * W;
        o.y = (-tmp.y * 0.5 + 0.5) * H;
        o.depth = (depth - dc) / Math.max(ringR, 0.0001); // -1 near camera .. +1 far
        o.front = depth < dc;
      }
    }

    renderer.render(scene, camera);
    return nodesOut;
  }

  function dispose() {
    renderer.dispose();
  }

  return { update, resize, dispose, renderer, gl, maxPt, debug: { scene, camera, flareGlow, flareStreak, bg, dust, stars, lines, shape, wires, ringRoot, flashMesh } };
}
