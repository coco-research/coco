// The director turns a scroll position (in screens) into the full state of the 3D world:
// camera pose plus every animated parameter. Pure math, no DOM, no Three.js.
import { TL, LAYOUT, rail } from './layout.js';

const TAU = Math.PI * 2;
const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, t) => a + (b - a) * t;
const sstep = (t) => t * t * (3 - 2 * t);

// Monotone cubic through keys [[t, v], ...]. C1 continuous and never overshoots,
// so the camera never jerks or swings past a waypoint.
function pchip(keys) {
  const n = keys.length;
  const t = keys.map((k) => k[0]);
  const y = keys.map((k) => k[1]);
  const h = [];
  const d = [];
  for (let i = 0; i < n - 1; i++) {
    h[i] = t[i + 1] - t[i];
    d[i] = (y[i + 1] - y[i]) / h[i];
  }
  const m = new Array(n);
  m[0] = d[0];
  m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) {
    if (d[i - 1] * d[i] <= 0) m[i] = 0;
    else {
      const w1 = 2 * h[i] + h[i - 1];
      const w2 = h[i] + 2 * h[i - 1];
      m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]);
    }
  }
  let last = 0;
  return (x) => {
    if (x <= t[0]) return y[0];
    if (x >= t[n - 1]) return y[n - 1];
    let i = last;
    if (x < t[i] || x >= t[i + 1]) {
      i = 0;
      let hi = n - 1;
      while (hi - i > 1) {
        const mid = (i + hi) >> 1;
        if (t[mid] <= x) i = mid;
        else hi = mid;
      }
      last = i;
    }
    const s = (x - t[i]) / h[i];
    const s2 = s * s;
    const s3 = s2 * s;
    return (
      (2 * s3 - 3 * s2 + 1) * y[i] +
      (s3 - 2 * s2 + s) * h[i] * m[i] +
      (-2 * s3 + 3 * s2) * y[i + 1] +
      (s3 - s2) * h[i] * m[i + 1]
    );
  };
}

// Piecewise eased ramp between keys; holds the first/last value outside the range.
function seg(keys, ease = sstep) {
  const n = keys.length;
  return (x) => {
    if (x <= keys[0][0]) return keys[0][1];
    if (x >= keys[n - 1][0]) return keys[n - 1][1];
    let i = 0;
    while (i < n - 2 && x >= keys[i + 1][0]) i++;
    const a = keys[i];
    const b = keys[i + 1];
    return lerp(a[1], b[1], ease((x - a[0]) / (b[0] - a[0])));
  };
}

// Distance profile with a soft start and a soft stop: velocity ramps up, cruises, ramps down.
function trap(u, a = 0.14, b = 0.2) {
  const D = 1 - a / 2 - b / 2;
  let d;
  if (u < a) d = (u * u) / (2 * a);
  else if (u < 1 - b) d = a / 2 + (u - a);
  else {
    const w = u - (1 - b);
    d = a / 2 + (1 - b - a) + w - (w * w) / (2 * b);
  }
  return d / D;
}

export function createDirector(view) {
  const lat = view.lat; // narrower tunnel on portrait screens
  const fit = view.fit; // pull the camera back on portrait screens so shapes still fit
  const portrait = view.portrait;
  const { Z0, Z1, C, S, ang } = LAYOUT;
  const f = { px: [], py: [], pz: [], lx: [], ly: [], lz: [], fov: [], roll: [] };
  const K = (t, p, l, fov, roll = 0) => {
    f.px.push([t, p[0]]);
    f.py.push([t, p[1]]);
    f.pz.push([t, p[2]]);
    f.lx.push([t, l[0]]);
    f.ly.push([t, l[1]]);
    f.lz.push([t, l[2]]);
    f.fov.push([t, fov]);
    f.roll.push([t, roll]);
  };

  // 1. Hero: a slow dolly in on the single point of light.
  K(0.0, [0, 0, 16.5], [0, 0, 0], 34);
  K(0.85, [0, 0, 12.8], [0, 0, 0], 34);

  // 2. Flight through the thirteen constellations.
  const N = 30;
  const [f0, f1] = TL.flight;
  for (let i = 0; i <= N; i++) {
    const u = i / N;
    const q = trap(u);
    const z = lerp(Z0, Z1, q);
    const [rx, ry] = rail(q);
    const [lx, ly] = rail(Math.min(1, q + 0.06));
    const dq = 0.01;
    const dx = (rail(Math.min(1, q + dq))[0] - rail(Math.max(0, q - dq))[0]) / (2 * dq);
    K(
      lerp(f0, f1, u),
      [rx * lat, ry * lat, z],
      [lx * lat, ly * lat, z - 14],
      lerp(46, 53, Math.sin(Math.PI * u)),
      clamp(-dx * 0.0022 * lat, -0.1, 0.1),
    );
  }

  // 3. Settle in front of the converging point, then hold for the editor window.
  K(TL.converge[1], [0, 0.3, Z1 - 2.5], C, 40);
  K(TL.editor.unfold[0], [0, 0.5, Z1 - 4], C, 38);
  K(TL.editor.hold, [0, 1.4, Z1 - 8], C, 36);

  // 4. Warp: fly through the point of light and out into the next space.
  K(8.65, [0, 1.3, C[2] + 10], [0, 0, S[2]], 46);
  K(8.85, [0, 1.2, C[2]], [0, 0, S[2]], 66);
  K(9.05, [0, 1.0, C[2] - 18], [0, 0, S[2]], 62);
  K(9.35, [0, 3.0, S[2] + 40 * fit], [S[0], S[1], S[2]], 40);

  // 5. Four rules: a slow orbit around the morphing shape.
  const orbit = (t, a, r, h, fov) =>
    K(t, [S[0] + Math.sin(a) * r, S[1] + h, S[2] + Math.cos(a) * r], [S[0], S[1], S[2]], fov);
  const R0 = 9.35;
  const R1 = TL.rules[3][1];
  for (let i = 1; i <= 8; i++) {
    const u = i / 8;
    orbit(lerp(R0, R1, u), lerp(0, ang.rulesEnd, u), (lerp(40, 33, u) + 1.3 * Math.sin(u * TAU * 2)) * fit, lerp(3.0, 2.0, u), 40 - 2 * Math.sin(u * TAU));
  }
  // 6. Shipped and lab: the shape disperses into a field and the camera drifts through it.
  orbit(14.2, lerp(ang.rulesEnd, ang.shippedEnd, 0.55), 26 * fit, 1.2, 40);
  orbit(TL.shipped[1], ang.shippedEnd, 22 * fit, 0.6, 40);
  orbit(16.9, lerp(ang.shippedEnd, ang.labEnd, 0.5), 19 * fit, 0.3, 40);
  orbit(TL.lab[1], ang.labEnd, 14 * fit, 0.0, 40);
  // 7. Close: pull all the way back to reveal one constellation.
  orbit(18.6, ang.labEnd, 28 * fit, 3.0, 40);
  orbit(19.4, ang.labEnd, 62 * fit, 9.0, 37);
  orbit(TL.close[1], ang.labEnd, 88 * fit, 14.0, 34);

  const fx = {};
  for (const k of Object.keys(f)) fx[k] = pchip(f[k]);

  const T = TL;
  const flare = seg([
    [0, 1.0], [0.95, 1.1], [1.2, 1.35], [1.65, 0.0],
    [5.0, 0.0], [5.55, 0.6], [5.95, 1.25], [T.editor.hold, 1.25], [8.8, 2.0], [9.2, 0.0],
    [17.8, 0.0], [18.2, 0.9], [19.8, 0.4],
  ]);
  const bloom = seg([[0, 0], [T.bloom[0], 0], [T.bloom[1], 1], [12.9, 1], [13.0, 0], [17.9, 0], [19.5, 1]]);
  const converge = seg([[T.converge[0], 0], [T.converge[1], 1]]);
  const starAlpha = seg([[0, 0], [1.0, 0], [1.3, 1], [8.7, 1], [9.1, 0], [17.8, 0], [18.1, 1]]);
  const lineAlpha = seg([[0, 0], [1.3, 0], [2.1, 1], [5.4, 1], [5.95, 0.15], [17.9, 0.15], [18.6, 1]]);
  const dissent = seg([[5.0, 0], [5.5, 1], [6.0, 1], [6.4, 0]]);
  const ring = seg([[6.8, 0], [7.5, 1], [T.editor.hold, 1], [T.editor.collapse[1] - 0.1, 0]]);
  const shapeAppear = seg([[8.7, 0], [9.4, 1]]);
  const shapeMorph = seg([[9.2, 0], [9.7, 0], [10.2, 1], [10.55, 1], [11.05, 2], [11.4, 2], [11.9, 3], [12.55, 3]]);
  const shapeDisperse = seg([[12.5, 0], [13.5, 1]]);
  const shapeAlpha = seg([[12.55, 1], [17.85, 1], [19.6, 0.5]]);
  const dust = seg([[0, 0], [0.9, 0], [1.9, 1]]);
  const streak = seg([[5.2, 0], [5.9, 0.45], [6.3, 0], [8.5, 0], [8.9, 1], [9.35, 0]]);
  const flash = seg([[8.62, 0], [8.84, 0.5], [9.14, 0]]); // peak capped (was 0.8) and shorter: no near-white frame
  const grade = seg([[8.7, 0], [9.5, 1], [12.2, 1], [13.0, 0]]);
  const bars = seg([[1.4, 0], [1.9, 1], [6.0, 1], [6.5, 0]]);
  const fog = seg([[0, 1], [17.85, 1], [19.6, 1.9]]);
  const shiftX = seg([[8.9, 0], [9.5, portrait ? 0 : 0.24], [12.3, portrait ? 0 : 0.24], [13.0, 0]]);
  const shiftY = seg([
    [0, 0.17], [0.85, 0.17], [2.0, 0.0], [4.4, 0], [5.3, 0.14], [6.15, 0.14], [6.65, 0], [8.9, 0], [9.5, portrait ? 0.15 : 0], [12.3, portrait ? 0.15 : 0], [13.0, 0],
    [17.85, 0], [19.6, portrait ? 0.1 : 0.13],
  ]);
  const stage = seg([[12.4, 0], [13.3, 0.75], [15.4, 0.75], [16.1, 0.4], [17.5, 0.4], [18.2, 0]]);

  const P = {
    cam: { px: 0, py: 0, pz: 0, lx: 0, ly: 0, lz: 0, fov: 40, roll: 0 },
    shiftX: 0, shiftY: 0,
    flare: 0, flareAt: 0,
    bloom: 0, converge: 0, mode: 0, starAlpha: 0, lineAlpha: 0, dissent: 0,
    ring: 0, ringSpin: 0,
    shapeAppear: 0, shapeMorph: 0, shapeDisperse: 0, shapeAlpha: 1, shapeSpin: 0,
    dust: 0, streak: 0, flash: 0, grade: 0, bars: 0, fog: 1, stage: 0,
  };

  return function at(s) {
    const c = P.cam;
    c.px = fx.px(s); c.py = fx.py(s); c.pz = fx.pz(s);
    c.lx = fx.lx(s); c.ly = fx.ly(s); c.lz = fx.lz(s);
    c.fov = fx.fov(s); c.roll = fx.roll(s);
    P.shiftX = shiftX(s);
    P.shiftY = shiftY(s);
    P.flare = flare(s);
    P.flareAt = s < 4.3 ? 0 : s < 9.0 ? 1 : 2;
    P.bloom = bloom(s);
    P.converge = converge(s);
    P.mode = s < T.modeFlip ? 0 : 1;
    P.starAlpha = starAlpha(s);
    P.lineAlpha = lineAlpha(s);
    P.dissent = dissent(s);
    P.ring = ring(s);
    P.ringSpin = 0.4 + (s - 6.8) * 1.15;
    P.shapeAppear = shapeAppear(s);
    P.shapeMorph = shapeMorph(s);
    P.shapeDisperse = shapeDisperse(s);
    P.shapeAlpha = shapeAlpha(s);
    P.shapeSpin = s * 0.16;
    P.dust = dust(s);
    P.streak = streak(s);
    P.flash = flash(s);
    P.grade = grade(s);
    P.bars = bars(s);
    P.fog = fog(s);
    P.stage = stage(s);
    return P;
  };
}
