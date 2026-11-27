// Procedural 3D motif generators for shipped and source-available product pages.
// Pure math only: zero external fetches, deterministic seeds, shared scroll morphs.

export const TAU = Math.PI * 2;
export const VOICE_BARS = [
  0.16, 0.24, 0.20, 0.34, 0.30, 0.46, 0.40, 0.62, 0.52, 0.74, 0.60,
  0.86, 0.70, 1.00, 0.82, 0.94, 0.66, 0.90, 0.72, 0.56, 0.64, 0.44,
  0.50, 0.34, 0.38, 0.26, 0.30, 0.20, 0.16, 0.12, 0.10,
];
// Coco SI v2.4.0 persona roster: 493 personas across 13 departments (matches docs/asset-counts.json).
export const COCO_SI_DEPTS = [
  ['Engineering', 70], ['AI', 59], ['Product & design', 56], ['Finance', 47],
  ['Trading', 46], ['Legal & IP', 29], ['Risk & compliance', 30], ['Strategy', 29],
  ['Data & analytics', 29], ['Climate & energy', 25], ['Education & edtech', 25],
  ['Healthcare & life sciences', 25], ['Sales & GTM', 23],
];

export function mulberry32(a) {
  return () => {
    a = ((a | 0) + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function rotTilt(x, y, z, rx, rz) {
  const cx = Math.cos(rx), sx = Math.sin(rx), cz = Math.cos(rz), sz = Math.sin(rz);
  const y1 = y * cx - z * sx, z1 = y * sx + z * cx;
  return [x * cz - y1 * sz, x * sz + y1 * cz, z1];
}

export function addLoop(segs, fn, steps) {
  for (let i = 0; i < steps; i++) segs.push([...fn(i / steps), ...fn((i + 1) / steps)]);
}

export function addRect(segs, cx, cy, cz, w, h, rx, rz) {
  const hw = w * 0.5, hh = h * 0.5;
  const c = [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]].map(([x, y]) => rotTilt(cx + x, cy + y, cz, rx, rz));
  for (let i = 0; i < 4; i++) segs.push([...c[i], ...c[(i + 1) % 4]]);
}

function rectEdge(edge, u, w, h) {
  if (edge === 0) return [u * w * 0.5, -h * 0.5];
  if (edge === 1) return [u * w * 0.5, h * 0.5];
  if (edge === 2) return [-w * 0.5, u * h * 0.5];
  return [w * 0.5, u * h * 0.5];
}

export function finalizeMotif(rand, pts0, meta, amber, segs0, N, M, pulse = 0.28) {
  const sets = [pts0, [], []];
  const R = 5.4;
  for (let i = 0; i < N; i++) {
    const u = rand() * 2 - 1, th = rand() * TAU, s = Math.sqrt(1 - u * u);
    const r = rand() < 0.8 ? 1 - Math.pow(rand(), 6) * 0.08 : Math.cbrt(rand()) * 0.72;
    sets[1].push([R * r * s * Math.cos(th), R * r * u, R * r * s * Math.sin(th)]);
  }
  for (let i = 0; i < N; i++) {
    const a = rand() * TAU, b = rand() * TAU;
    const rr = 3.55 + 0.52 * Math.cos(b), off = 0.52 * Math.sin(b);
    sets[2].push((i & 1) === 0 ? [-2.05 + rr * Math.cos(a), rr * Math.sin(a), off] : [2.05 + rr * Math.cos(a), off, rr * Math.sin(a)]);
  }

  const segs1 = [], segs2 = [];
  for (let k = 0; k < 6; k++) {
    const phi = (k * Math.PI) / 6;
    addLoop(segs1, (t) => { const a = t * TAU, x = R * Math.cos(a); return [x * Math.cos(phi), R * Math.sin(a), x * Math.sin(phi)]; }, 40);
  }
  for (const lat of [-55, -25, 0, 25, 55]) {
    const th = (lat * Math.PI) / 180;
    addLoop(segs1, (t) => { const a = t * TAU; return [R * Math.cos(th) * Math.cos(a), R * Math.sin(th), R * Math.cos(th) * Math.sin(a)]; }, 36);
  }
  for (let k = 0; k < 5; k++) {
    const b = (k * TAU) / 5, rr = 3.55 + 0.52 * Math.cos(b), off = 0.52 * Math.sin(b);
    addLoop(segs2, (t) => { const a = t * TAU; return [-2.05 + rr * Math.cos(a), rr * Math.sin(a), off]; }, 42);
    addLoop(segs2, (t) => { const a = t * TAU; return [2.05 + rr * Math.cos(a), off, rr * Math.sin(a)]; }, 42);
  }

  const order = (pts) => pts
    .map((p, idx) => [Math.floor((p[1] / 12 + 0.5) * 32) * 10 + ((Math.atan2(p[2], p[0]) + Math.PI) / TAU) * 9.99, idx])
    .sort((a, b) => a[0] - b[0]).map((k) => k[1]);
  const T = [new Float32Array(N * 3), new Float32Array(N * 3), new Float32Array(N * 3)];
  const seed = new Float32Array(N * 4), ord0 = order(sets[0]);
  for (let s = 0; s < 3; s++) {
    const ord = s === 0 ? ord0 : order(sets[s]);
    for (let i = 0; i < N; i++) T[s].set(sets[s][ord[i]], i * 3);
  }
  for (let i = 0; i < N; i++) {
    const idx = ord0[i];
    const w = amber[idx] > 0 ? amber[idx] : rand() * 0.92;
    seed.set([rand(), meta[idx], rand(), w], i * 4);
  }
  const wires = [segs0, segs1, segs2].map((list) => {
    const arr = new Float32Array(M * 6);
    list.slice(0, M).forEach((seg, i) => arr.set(seg, i * 6));
    return arr;
  });
  return { T, seed, wires, M, pulse };
}

export const PUBLIC_MOTIFS = {
  'coco-si'(N, M) {
    const rand = mulberry32(1301), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const total = COCO_SI_DEPTS.reduce((s, d) => s + d[1], 0);
    const centers = COCO_SI_DEPTS.map((d, k) => {
      const a = (k / COCO_SI_DEPTS.length) * TAU - Math.PI * 0.5;
      const z = Math.sin(a * 2.0) * 1.45;
      return rotTilt(4.85 * Math.cos(a), 4.15 * Math.sin(a), z, 0.24, -0.14);
    });
    const coreCut = Math.floor(N * 0.14), dissentCut = Math.floor(N * 0.20);
    const dissentC = [2.95, 2.55, 2.25];
    for (let i = 0; i < N; i++) {
      if (i < coreCut) {
        const u = rand() * 2 - 1, a = rand() * TAU, r = Math.cbrt(rand()) * 0.95, s = Math.sqrt(1 - u * u);
        pts.push([r * s * Math.cos(a), r * u, r * s * Math.sin(a)]);
        meta[i] = 0.5;
      } else if (i < dissentCut) {
        const u = rand() * 2 - 1, a = rand() * TAU, r = Math.cbrt(rand()) * 0.62, s = Math.sqrt(1 - u * u);
        pts.push([dissentC[0] + r * s * Math.cos(a), dissentC[1] + r * u, dissentC[2] + r * s * Math.sin(a)]);
        meta[i] = 0.95; amber[i] = 0.996;
      } else {
        let pick = ((i - dissentCut) / (N - dissentCut)) * total, di = 0;
        while (di < COCO_SI_DEPTS.length - 1 && pick >= COCO_SI_DEPTS[di][1]) { pick -= COCO_SI_DEPTS[di][1]; di++; }
        const c = centers[di], spread = 0.42 + (COCO_SI_DEPTS[di][1] / 70) * 0.46;
        const u = rand() * 2 - 1, a = rand() * TAU, r = Math.pow(rand(), 0.55) * spread, s = Math.sqrt(1 - u * u);
        pts.push([c[0] + r * s * Math.cos(a), c[1] + r * u, c[2] + r * s * Math.sin(a)]);
        meta[i] = di / COCO_SI_DEPTS.length;
        if (di === 0 && rand() < 0.08) amber[i] = 0.992;
      }
    }
    addLoop(segs, (t) => [0.95 * Math.cos(t * TAU), 0.95 * Math.sin(t * TAU), 0], 36);
    addLoop(segs, (t) => [dissentC[0] + 0.72 * Math.cos(t * TAU), dissentC[1] + 0.72 * Math.sin(t * TAU), dissentC[2]], 28);
    segs.push([0, 0, 0, ...dissentC]);
    centers.forEach((c, i) => {
      segs.push([0, 0, 0, ...c]);
      segs.push([...c, ...centers[(i + 1) % centers.length]]);
      segs.push([...c, ...centers[(i + 3) % centers.length]]);
      addLoop(segs, (t) => [c[0] + 0.58 * Math.cos(t * TAU), c[1] + 0.58 * Math.sin(t * TAU), c[2]], 18);
    });
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.24);
  },

  voice(N, M) {
    const rand = mulberry32(1904), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const ringCut = Math.floor(N * 0.76), gateCut = Math.floor(N * 0.94);
    for (let i = 0; i < N; i++) {
      if (i < ringCut) {
        const bi = i % VOICE_BARS.length, u = (bi / (VOICE_BARS.length - 1)) * 2 - 1, layer = (i % 3) - 1;
        const amp = (0.42 + VOICE_BARS[bi] * 3.85) * (layer === 0 ? 1.0 : 0.68);
        const s = rand() * 2 - 1, crest = Math.sign(s || 1) * Math.pow(Math.abs(s), 0.62);
        pts.push([u * 5.8 + (rand() - 0.5) * 0.11, crest * amp, Math.cos(u * 1.45) * 1.35 - 0.35 + layer * 1.05 + (rand() - 0.5) * 0.12]);
        meta[i] = 0.5 + 0.5 * u;
      } else if (i < gateCut) {
        const which = i & 1, a = rand() * TAU, r = (which ? 6.35 : 5.65) + (rand() - 0.5) * 0.22;
        pts.push(rotTilt(r * Math.cos(a), (rand() - 0.5) * 0.18, r * Math.sin(a), which ? 0.44 : -0.38, which ? -0.20 : 0.24));
        meta[i] = a / TAU;
      } else {
        pts.push([6.35 + (rand() - 0.5) * 0.14, (rand() * 2 - 1) * 1.95, 0.35 + (rand() - 0.5) * 0.24]);
        meta[i] = 1.0; if (rand() < 0.35) amber[i] = 0.994;
      }
    }
    const barPt = (bi, sign, zOff) => {
      const u = (bi / (VOICE_BARS.length - 1)) * 2 - 1;
      return [u * 5.8, sign * (0.42 + VOICE_BARS[bi] * 3.85), Math.cos(u * 1.45) * 1.35 - 0.35 + zOff];
    };
    for (let bi = 0; bi < VOICE_BARS.length; bi++) {
      segs.push([...barPt(bi, -1, 0), ...barPt(bi, 1, 0)]);
      if (bi % 2 === 0) segs.push([...barPt(bi, -0.68, -1.05), ...barPt(bi, 0.68, -1.05)]);
      if (bi + 1 < VOICE_BARS.length) {
        segs.push([...barPt(bi, 1, 0), ...barPt(bi + 1, 1, 0)]);
        segs.push([...barPt(bi, -1, 0), ...barPt(bi + 1, -1, 0)]);
      }
    }
    addLoop(segs, (t) => rotTilt(5.65 * Math.cos(t * TAU), 0, 5.65 * Math.sin(t * TAU), -0.38, 0.24), 64);
    addLoop(segs, (t) => rotTilt(6.35 * Math.cos(t * TAU), 0, 6.35 * Math.sin(t * TAU), 0.44, -0.20), 64);
    segs.push([6.35, -1.95, 0.35, 6.35, 1.95, 0.35]);
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 1.0);
  },

  signal(N, M) {
    const rand = mulberry32(3109), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = -0.30, rz = 0.20, zs = [-2.05, 0, 2.05];
    for (let i = 0; i < N; i++) {
      const zi = i % 3, z = zs[zi];
      if (i < N * 0.78) {
        const gx = Math.floor(rand() * 9) - 4, gy = Math.floor(rand() * 7) - 3;
        const onH = rand() < 0.5;
        const x = onH ? (rand() * 2 - 1) * 4.4 : gx * 1.1, y = onH ? gy * 0.92 : (rand() * 2 - 1) * 2.76;
        pts.push(rotTilt(x, y, z, rx, rz));
        meta[i] = (zi + 1) / 3;
      } else {
        const t = rand() * 1.35 * Math.PI, r = 0.42 * Math.exp(0.34 * t);
        pts.push(rotTilt(r * Math.cos(t) - 0.6, r * Math.sin(t) - 0.3, 0, rx, rz));
        meta[i] = t / TAU; if (rand() < 0.28) amber[i] = 0.995;
      }
    }
    zs.forEach((z) => {
      addRect(segs, 0, 0, z, 8.8, 5.52, rx, rz);
      for (let g = -3; g <= 3; g++) segs.push([...rotTilt(g * 1.1, -2.76, z, rx, rz), ...rotTilt(g * 1.1, 2.76, z, rx, rz)]);
      for (let g = -2; g <= 2; g++) segs.push([...rotTilt(-4.4, g * 0.92, z, rx, rz), ...rotTilt(4.4, g * 0.92, z, rx, rz)]);
    });
    for (const [x, y] of [[-4.4, -2.76], [4.4, -2.76], [4.4, 2.76], [-4.4, 2.76]]) {
      segs.push([...rotTilt(x, y, zs[0], rx, rz), ...rotTilt(x, y, zs[2], rx, rz)]);
    }
    addLoop(segs, (t) => { const a = t * 1.35 * Math.PI, r = 0.42 * Math.exp(0.34 * a); return rotTilt(r * Math.cos(a) - 0.6, r * Math.sin(a) - 0.3, 0, rx, rz); }, 44);
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.20);
  },

  mira(N, M) {
    const rand = mulberry32(4111), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const frames = [-2.6, -1.3, 0, 1.3, 2.6], rx = 0.14, rz = -0.12;
    for (let i = 0; i < N; i++) {
      if (i < N * 0.62) {
        const fi = i % frames.length, z = frames[fi], ox = fi * 0.32 - 0.64;
        const edge = i % 4, w = 2.65, h = 4.72;
        const u = rand() * 2 - 1;
        const [x, y] = rectEdge(edge, u, w, h);
        pts.push(rotTilt(ox + x, y, z, rx, rz));
        meta[i] = (fi + 1) / frames.length;
      } else {
        const u = rand() * 2 - 1, strand = i & 1;
        const x = u * 5.6, y = Math.sin(u * 4.2 + (strand ? Math.PI * 0.85 : 0)) * 1.45;
        const z = Math.cos(u * 4.2 + (strand ? Math.PI * 0.85 : 0)) * 1.15;
        pts.push(rotTilt(x, y + (rand() - 0.5) * 0.14, z, rx, rz));
        meta[i] = 0.5 + 0.5 * u; if (strand && rand() < 0.16) amber[i] = 0.994;
      }
    }
    frames.forEach((z, fi) => addRect(segs, fi * 0.32 - 0.64, 0, z, 2.65, 4.72, rx, rz));
    for (const strand of [0, 1]) {
      for (let k = 0; k < 72; k++) {
        const fn = (t) => {
          const u = t * 2 - 1, ph = strand ? Math.PI * 0.85 : 0;
          return rotTilt(u * 5.6, Math.sin(u * 4.2 + ph) * 1.45, Math.cos(u * 4.2 + ph) * 1.15, rx, rz);
        };
        segs.push([...fn(k / 72), ...fn((k + 1) / 72)]);
      }
    }
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.72);
  },

  'jev-use'(N, M) {
    const rand = mulberry32(6117), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = 0.18, rz = -0.10;
    for (let i = 0; i < N; i++) {
      if (i < N * 0.46) {
        const ri = i % 6, x = -4.9 + ri * 0.74, rad = 0.65 + ri * 0.46, a = rand() * TAU;
        pts.push(rotTilt(x + (rand() - 0.5) * 0.08, rad * Math.cos(a), rad * Math.sin(a), rx, rz));
        meta[i] = ri / 6;
      } else if (i < N * 0.90) {
        const wi = i % 3, z = (wi - 1) * 1.15, cx = 2.35 + wi * 0.35, cy = (wi - 1) * 0.28;
        const w = 4.6, h = 3.1, u = rand() * 2 - 1, edge = i % 4;
        const [x, y] = rectEdge(edge, u, w, h);
        pts.push(rotTilt(cx + x, cy + y, z, rx, rz));
        meta[i] = 0.6 + wi * 0.12;
      } else {
        const a = rand() * TAU, r = rand() * 0.48;
        pts.push(rotTilt(2.55 + r * Math.cos(a), 0.15 + r * Math.sin(a), 1.22, rx, rz));
        meta[i] = 1.0; amber[i] = 0.996;
      }
    }
    for (let ri = 0; ri < 6; ri++) {
      const x = -4.9 + ri * 0.74, rad = 0.65 + ri * 0.46;
      addLoop(segs, (t) => rotTilt(x, rad * Math.cos(t * TAU), rad * Math.sin(t * TAU), rx, rz), 32);
    }
    for (let wi = 0; wi < 3; wi++) {
      const z = (wi - 1) * 1.15, cx = 2.35 + wi * 0.35, cy = (wi - 1) * 0.28;
      addRect(segs, cx, cy, z, 4.6, 3.1, rx, rz);
      segs.push([...rotTilt(cx - 2.3, cy + 1.05, z, rx, rz), ...rotTilt(cx + 2.3, cy + 1.05, z, rx, rz)]);
    }
    segs.push([...rotTilt(-4.9, 0, 0, rx, rz), ...rotTilt(2.55, 0.15, 1.22, rx, rz)]);
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.62);
  },

  heliopause(N, M) {
    const rand = mulberry32(7121), pts = [], segs = [], meta = new Float32Array(N), amber = new Float32Array(N);
    const rx = 0.22, rz = -0.16, orbits = [1.55, 2.55, 3.55, 4.45];
    for (let i = 0; i < N; i++) {
      if (i < N * 0.48) {
        const rho = Math.sqrt(rand()) * 5.2, a = rand() * TAU;
        const x = 3.55 - 0.24 * rho * rho, y = rho * Math.cos(a), z = rho * Math.sin(a);
        pts.push(rotTilt(x, y, z, rx, rz));
        meta[i] = rho / 5.2;
      } else if (i < N * 0.86) {
        const oi = i % orbits.length, r = orbits[oi] + (rand() - 0.5) * 0.10, a = rand() * TAU;
        pts.push(rotTilt(-0.85 + r * Math.cos(a), (oi - 1.5) * 0.22, r * Math.sin(a), rx + oi * 0.12, rz));
        meta[i] = a / TAU;
      } else {
        const u = rand() * 2 - 1, a = rand() * TAU, r = Math.cbrt(rand()) * 0.82, s = Math.sqrt(1 - u * u);
        pts.push(rotTilt(-0.85 + r * s * Math.cos(a), r * u, r * s * Math.sin(a), rx, rz));
        meta[i] = 1.0; if (rand() < 0.42) amber[i] = 0.996;
      }
    }
    for (const rho of [1.6, 2.9, 4.1, 5.1]) {
      const x = 3.55 - 0.24 * rho * rho;
      addLoop(segs, (t) => rotTilt(x, rho * Math.cos(t * TAU), rho * Math.sin(t * TAU), rx, rz), 36);
    }
    for (let m = 0; m < 8; m++) {
      const a = (m * TAU) / 8;
      for (let s = 0; s < 14; s++) {
        const r1 = (s / 14) * 5.1, r2 = ((s + 1) / 14) * 5.1;
        segs.push([
          ...rotTilt(3.55 - 0.24 * r1 * r1, r1 * Math.cos(a), r1 * Math.sin(a), rx, rz),
          ...rotTilt(3.55 - 0.24 * r2 * r2, r2 * Math.cos(a), r2 * Math.sin(a), rx, rz),
        ]);
      }
    }
    orbits.forEach((r, oi) => addLoop(segs, (t) => rotTilt(-0.85 + r * Math.cos(t * TAU), (oi - 1.5) * 0.22, r * Math.sin(t * TAU), rx + oi * 0.12, rz), 40));
    return finalizeMotif(rand, pts, meta, amber, segs, N, M, 0.22);
  },
};
