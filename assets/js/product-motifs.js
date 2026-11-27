// Procedural 3D motif generators for private lab pages and unified dispatcher.
// Combines with product-motifs-a.js so every product page shares product-scene.js.

import {
  TAU, mulberry32, rotTilt, addLoop, addRect, finalizeMotif, PUBLIC_MOTIFS, COCO_SI_DEPTS,
} from './product-motifs-a.js';

export { mulberry32, COCO_SI_DEPTS };

const PHI = (1 + Math.sqrt(5)) * 0.5;
const ICO_RAW = [
  [-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0],
  [0, -1, PHI], [0, 1, PHI], [0, -1, -PHI], [0, 1, -PHI],
  [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1],
].map(([x, y, z]) => { const l = Math.hypot(x, y, z); return [x / l, y / l, z / l]; });

const ICO_EDGES = [];
for (let i = 0; i < ICO_RAW.length; i++) {
  for (let j = i + 1; j < ICO_RAW.length; j++) {
    const d = Math.hypot(ICO_RAW[i][0] - ICO_RAW[j][0], ICO_RAW[i][1] - ICO_RAW[j][1], ICO_RAW[i][2] - ICO_RAW[j][2]);
    if (d < 1.15) ICO_EDGES.push([i, j]);
  }
}

export const LAB_MOTIFS = {
  m0(N, M) {
    const rand = mulberry32(8123), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const R = 2.85, rx = 0.24, rz = -0.18;
    const portals = Array.from({ length: 5 }, (_, k) => {
      const a = (k / 5) * TAU - Math.PI * 0.5;
      return rotTilt(5.55 * Math.cos(a), Math.sin(a * 2) * 1.15, 5.55 * Math.sin(a), rx, rz);
    });
    const verts = ICO_RAW.map(([x, y, z]) => rotTilt(x * R, y * R, z * R, rx, rz));
    for (let i = 0; i < N; i++) {
      if (i < N * 0.56) {
        const [a, b] = ICO_EDGES[i % ICO_EDGES.length], t = rand();
        const p = [0, 1, 2].map((c) => verts[a][c] + (verts[b][c] - verts[a][c]) * t + (rand() - 0.5) * 0.12);
        pts.push(p); meta[i] = t;
      } else if (i < N * 0.84) {
        const pi = i % 5, c = portals[pi], t = rand();
        pts.push([c[0] * t + (rand() - 0.5) * 0.14, c[1] * t + (rand() - 0.5) * 0.14, c[2] * t + (rand() - 0.5) * 0.14]);
        meta[i] = t; if (t < 0.22 && rand() < 0.35) amber[i] = 0.995;
      } else {
        const c = portals[i % 5], a = rand() * TAU, r = 0.62 + (rand() - 0.5) * 0.12;
        pts.push([c[0] + r * Math.cos(a), c[1] + r * Math.sin(a), c[2]]);
        meta[i] = (i % 5) / 5;
      }
    }
    ICO_EDGES.forEach(([a, b]) => segs.push([...verts[a], ...verts[b]]));
    portals.forEach((c) => {
      segs.push([0, 0, 0, ...c]);
      addLoop(segs, (t) => [c[0] + 0.62 * Math.cos(t * TAU), c[1] + 0.62 * Math.sin(t * TAU), c[2]], 24);
    });
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.22);
  },

  hermes(N, M) {
    const rand = mulberry32(8229), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = -0.22, rz = 0.16, sheets = [-2.75, -1.65, -0.55, 0.55, 1.65, 2.75];
    for (let i = 0; i < N; i++) {
      if (i < N * 0.72) {
        const si = i % sheets.length, z = sheets[si], lineY = ((i % 7) - 3) * 0.66;
        const x = (rand() * 2 - 1) * 3.65;
        pts.push(rotTilt(x, lineY + (rand() - 0.5) * 0.05, z, rx, rz));
        meta[i] = (si + 1) / sheets.length;
      } else if (i < N * 0.88) {
        const t = rand() * 2 - 1;
        pts.push(rotTilt(t * 4.8, t * 1.35 + (rand() - 0.5) * 0.08, t * 3.4, rx, rz));
        meta[i] = 0.5 + 0.5 * t;
      } else {
        const x = 0.55 + (rand() * 2 - 1) * 1.45, y = 0.66 + (rand() - 0.5) * 0.26;
        pts.push(rotTilt(x, y, 0.55 + (rand() - 0.5) * 0.08, rx, rz));
        meta[i] = 1.0; amber[i] = 0.996;
      }
    }
    sheets.forEach((z) => {
      addRect(segs, 0, 0, z, 7.6, 5.1, rx, rz);
      for (let r = -2; r <= 2; r++) segs.push([...rotTilt(-3.2, r * 0.66, z, rx, rz), ...rotTilt(3.2, r * 0.66, z, rx, rz)]);
    });
    addRect(segs, 0.55, 0.66, 0.55, 3.1, 0.62, rx, rz);
    segs.push([...rotTilt(-4.8, -1.35, -3.4, rx, rz), ...rotTilt(4.8, 1.35, 3.4, rx, rz)]);
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.20);
  },

  'teams-ng'(N, M) {
    const rand = mulberry32(8443), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = -0.58, rz = 0.14, seats = 9;
    const ring = Array.from({ length: seats }, (_, k) => {
      const a = (k / seats) * TAU - Math.PI * 0.5;
      return rotTilt(5.05 * Math.cos(a), 0, 5.05 * Math.sin(a), rx, rz);
    });
    for (let i = 0; i < N; i++) {
      if (i < N * 0.42) {
        const a = rand() * TAU, r = (i & 1 ? 2.45 : 1.35) + (rand() - 0.5) * 0.14;
        pts.push(rotTilt(r * Math.cos(a), (rand() - 0.5) * 0.10, r * Math.sin(a), rx, rz));
        meta[i] = a / TAU;
      } else if (i < N * 0.84) {
        const si = i % seats, c = ring[si], a = rand() * TAU, r = Math.pow(rand(), 0.55) * 0.58;
        pts.push([c[0] + r * Math.cos(a), c[1] + (rand() - 0.5) * 0.42, c[2] + r * Math.sin(a)]);
        meta[i] = si / seats; if (si === 0) amber[i] = 0.995;
      } else {
        const si = 1 + (i % (seats - 1)), t = rand(), a0 = -Math.PI * 0.5, a1 = (si / seats) * TAU - Math.PI * 0.5;
        const x = (1 - t) * 5.05 * Math.cos(a0) + t * 5.05 * Math.cos(a1);
        const z = (1 - t) * 5.05 * Math.sin(a0) + t * 5.05 * Math.sin(a1);
        pts.push(rotTilt(x, Math.sin(t * Math.PI) * 1.65, z, rx, rz));
        meta[i] = t;
      }
    }
    addLoop(segs, (t) => rotTilt(2.45 * Math.cos(t * TAU), 0, 2.45 * Math.sin(t * TAU), rx, rz), 56);
    addLoop(segs, (t) => rotTilt(5.05 * Math.cos(t * TAU), 0, 5.05 * Math.sin(t * TAU), rx, rz), 72);
    ring.forEach((c, si) => {
      segs.push([0, 0, 0, ...c]);
      addLoop(segs, (t) => [c[0] + 0.55 * Math.cos(t * TAU), c[1], c[2] + 0.55 * Math.sin(t * TAU)], 18);
      if (si > 0) segs.push([...ring[0], ...c]);
    });
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.22);
  },

  // Directory pages. products: two large bodies and eight small ones on an orbit (2 + 8).
  products(N, M) {
    const rand = mulberry32(9011), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = 0.2, rz = -0.14, big = [[-1.9, 0.7, 0], [1.4, -0.9, 0.6]], R = 4.7;
    const sat = Array.from({ length: 8 }, (_, k) => { const a = (k / 8) * TAU; return rotTilt(R * Math.cos(a), Math.sin(a * 2) * 0.9, R * Math.sin(a), rx, rz); });
    for (let i = 0; i < N; i++) {
      if (i < N * 0.34) {
        const c = big[i & 1], u = rand() * 2 - 1, a = rand() * TAU, s = Math.sqrt(1 - u * u), r = 1.15;
        pts.push(rotTilt(c[0] + r * s * Math.cos(a), c[1] + r * u, c[2] + r * s * Math.sin(a), rx, rz)); meta[i] = (i & 1) ? 0.3 : 0.1;
      } else if (i < N * 0.62) {
        const c = sat[i % 8], a = rand() * TAU, r = Math.sqrt(rand()) * 0.4;
        pts.push([c[0] + r * Math.cos(a), c[1] + r * Math.sin(a), c[2] + (rand() - 0.5) * 0.3]); meta[i] = 0.5 + (i % 8) / 16; amber[i] = 0.995;
      } else {
        const a = rand() * TAU;
        pts.push(rotTilt(R * Math.cos(a), Math.sin(a * 2) * 0.9, R * Math.sin(a), rx, rz)); meta[i] = a / TAU;
      }
    }
    addLoop(segs, (t) => rotTilt(R * Math.cos(t * TAU), Math.sin(t * TAU * 2) * 0.9, R * Math.sin(t * TAU), rx, rz), 64);
    big.forEach((c) => addLoop(segs, (t) => rotTilt(c[0] + 1.5 * Math.cos(t * TAU), c[1], c[2] + 1.5 * Math.sin(t * TAU), rx, rz), 28));
    sat.forEach((c) => { segs.push([...rotTilt(big[0][0], big[0][1], big[0][2], rx, rz), ...c]); addLoop(segs, (t) => [c[0] + 0.5 * Math.cos(t * TAU), c[1] + 0.5 * Math.sin(t * TAU), c[2]], 16); });
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.24);
  },

  // lab: a bench of eight stations, four with public code (bottom row) and four private (amber).
  lab(N, M) {
    const rand = mulberry32(9127), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = 0.3, rz = -0.12, st = Array.from({ length: 8 }, (_, k) => rotTilt(((k % 4) - 1.5) * 2.5, (k < 4 ? 1.35 : -1.35), ((k % 4) - 1.5) * 0.35, rx, rz));
    const nextStage = (k) => {
      if (k % 4 === 3) return (k + 4) % 8;
      const base = k < 4 ? 0 : 4;
      return base + ((k + 1) % 4);
    };
    for (let i = 0; i < N; i++) {
      if (i < N * 0.5) {
        const k = i % 8, c = st[k], a = rand() * TAU, r = 0.35 + rand() * 0.55;
        pts.push([c[0] + r * Math.cos(a), c[1] + r * Math.sin(a) * 0.8, c[2] + (rand() - 0.5) * 0.4]); meta[i] = k / 8; if (k >= 4 && rand() < 0.4) amber[i] = 0.995;
      } else {
        const k = i % 8, t = rand(), a = st[k], b = st[nextStage(k)];
        pts.push([0, 1, 2].map((q) => a[q] + (b[q] - a[q]) * t + (rand() - 0.5) * 0.06)); meta[i] = t;
      }
    }
    st.forEach((c, k) => {
      addLoop(segs, (t) => [c[0] + 0.9 * Math.cos(t * TAU), c[1] + 0.72 * Math.sin(t * TAU), c[2]], 24);
      segs.push([...c, ...st[nextStage(k)]]);
      if (k < 4) segs.push([...c, ...st[k + 4]]);
    });
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.22);
  },

  // whats-new: a helix wound round a time axis with three release rings, newest on the right.
  'whats-new'(N, M) {
    const rand = mulberry32(9241), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = 0.18, rz = -0.16, L = 5.2, marks = [-3.6, 0.2, 3.9];
    const helix = (t, ph) => rotTilt(-L + t * 2 * L, 1.15 * Math.cos(t * TAU * 5 + ph), 1.15 * Math.sin(t * TAU * 5 + ph), rx, rz);
    for (let i = 0; i < N; i++) {
      if (i < N * 0.7) {
        const t = rand(), ph = (i & 1) ? Math.PI : 0;
        const p = helix(t, ph); pts.push([p[0] + (rand() - 0.5) * 0.1, p[1] + (rand() - 0.5) * 0.1, p[2] + (rand() - 0.5) * 0.1]); meta[i] = t;
      } else {
        const m = marks[i % 3], a = rand() * TAU, r = 0.7 + (rand() - 0.5) * 0.14;
        pts.push(rotTilt(m, r * Math.cos(a), r * Math.sin(a), rx, rz)); meta[i] = 0.5 + (i % 3) / 6; if (rand() < 0.3) amber[i] = 0.996;
      }
    }
    segs.push([...rotTilt(-L, 0, 0, rx, rz), ...rotTilt(L, 0, 0, rx, rz)]);
    marks.forEach((m) => addLoop(segs, (t) => rotTilt(m, 1.5 * Math.cos(t * TAU), 1.5 * Math.sin(t * TAU), rx, rz), 36));
    for (let ph = 0; ph < 2; ph++) addLoop(segs, (t) => helix(t, ph * Math.PI), 120);
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.26);
  },

  aloomannu(N, M) {
    const rand = mulberry32(8669), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = 0.22, rz = -0.15, agents = 6;
    const nodes = Array.from({ length: agents }, (_, k) => {
      const a = (k / agents) * TAU;
      return rotTilt(5.05 * Math.cos(a), ((k % 3) - 1) * 1.15, 5.05 * Math.sin(a), rx, rz);
    });
    for (let i = 0; i < N; i++) {
      if (i < N * 0.28) {
        const y = (rand() * 2 - 1) * 4.4, r = rand() * 0.24, a = rand() * TAU;
        pts.push(rotTilt(r * Math.cos(a), y, r * Math.sin(a), rx, rz));
        meta[i] = 0.5 + y / 9.0; if (Math.abs(y) < 0.5) amber[i] = 0.995;
      } else if (i < N * 0.62) {
        const ni = i % agents, c = nodes[ni], a = rand() * TAU, r = Math.sqrt(rand()) * 0.55;
        pts.push([c[0] + r * Math.cos(a), c[1] + r * Math.sin(a), c[2]]);
        meta[i] = ni / agents;
      } else {
        const ni = i % agents, nj = (ni + 2) % agents, t = rand();
        const a = nodes[ni], b = nodes[nj];
        const mid = rotTilt(0, (ni - 2.5) * 0.45, 0, rx, rz);
        const u = 1 - t;
        pts.push([0, 1, 2].map((k) => u * u * a[k] + 2 * u * t * mid[k] + t * t * b[k]));
        meta[i] = t; if (t > 0.45 && t < 0.55) amber[i] = 0.994;
      }
    }
    segs.push([...rotTilt(0, -4.5, 0, rx, rz), ...rotTilt(0, 4.5, 0, rx, rz)]);
    for (let k = -4; k <= 4; k++) addLoop(segs, (t) => rotTilt(0.55 * Math.cos(t * TAU), k * 0.95, 0.55 * Math.sin(t * TAU), rx, rz), 16);
    nodes.forEach((c, ni) => {
      segs.push([0, 0, 0, ...c]);
      segs.push([...c, ...nodes[(ni + 1) % agents]]);
      addLoop(segs, (t) => [c[0] + 0.55 * Math.cos(t * TAU), c[1] + 0.55 * Math.sin(t * TAU), c[2]], 20);
    });
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.24);
  },
};

export function buildProductMotif(kind, N = 2800, M = 440) {
  const fn = PUBLIC_MOTIFS[kind] || LAB_MOTIFS[kind] || PUBLIC_MOTIFS.voice;
  return fn(N, M);
}
