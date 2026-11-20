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

  'status-zero'(N, M) {
    const rand = mulberry32(8557), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = 0.18, rz = -0.14, gaps = new Set([2, 9, 14]);
    const cell = (side, idx) => {
      const col = (idx % 4) - 1.5, row = Math.floor(idx / 4) - 1.5;
      return rotTilt(side * 3.25 + side * col * 0.22, row * 1.35, col * 1.25, rx, rz);
    };
    for (let i = 0; i < N; i++) {
      const idx = i % 16, gap = gaps.has(idx);
      if (i < N * 0.64) {
        const side = (i & 1) ? 1 : -1, c = cell(side, idx);
        pts.push([c[0] + (rand() - 0.5) * 0.24, c[1] + (rand() - 0.5) * 0.24, c[2] + (rand() - 0.5) * 0.24]);
        meta[i] = idx / 16; if (gap && side === -1) amber[i] = 0.996;
      } else {
        const matchIdx = gap ? (idx + 1) % 16 : idx, t = rand();
        const a = cell(-1, matchIdx), b = cell(1, matchIdx);
        pts.push([0, 1, 2].map((k) => a[k] + (b[k] - a[k]) * t + (rand() - 0.5) * 0.06));
        meta[i] = t;
      }
    }
    for (const side of [-1, 1]) {
      for (let r = 0; r < 4; r++) segs.push([...cell(side, r * 4), ...cell(side, r * 4 + 3)]);
      for (let c = 0; c < 4; c++) segs.push([...cell(side, c), ...cell(side, 12 + c)]);
    }
    for (let idx = 0; idx < 16; idx++) {
      if (!gaps.has(idx)) segs.push([...cell(-1, idx), ...cell(1, idx)]);
      else addLoop(segs, (t) => { const c = cell(-1, idx); return [c[0] + 0.42 * Math.cos(t * TAU), c[1] + 0.42 * Math.sin(t * TAU), c[2]]; }, 20);
    }
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.20);
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
