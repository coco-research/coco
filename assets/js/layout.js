// Shared constants for the cinematic page.
// Time is measured in "screens" of scroll (1 screen = 100svh). Every visual on the
// page is a pure function of the smoothed scroll position, so scrubbing backwards
// is as exact as scrubbing forwards.

export const TL = {
  total: 21.1,
  hero: { exit: [0.12, 0.95] },
  bloom: [1.0, 2.9],
  flight: [1.25, 5.0],
  title: { in: [1.05, 1.6], out: [2.05, 2.75] },
  experts: { in: [2.5, 3.1], out: [3.55, 4.05] },
  depts: { in: [3.9, 4.5], out: [4.85, 5.35] },
  converge: [4.55, 5.95],
  argue: { in: [5.15, 5.75], out: [6.35, 6.75] },
  editor: { unfold: [6.7, 7.4], install: [7.2, 7.7], facts: [7.5, 7.95], hold: 8.45, collapse: [8.45, 8.95] },
  warp: [8.45, 9.25],
  rules: [[9.1, 9.95], [9.95, 10.8], [10.8, 11.65], [11.65, 12.55]],
  shipped: [12.55, 15.85],
  lab: [15.85, 18.85],
  close: [18.85, 21.1],
  modeFlip: 13.0, // star layout switches from "flight" to "final" while the stars are invisible
};

// Where each chapter starts (used by the progress rail and anchor links).
export const CHAPTERS = [
  { id: 'hero', at: 0, stop: 0 },
  { id: 'flagship', at: 1.0, stop: 1.5 },
  { id: 'rules', at: 8.9, stop: 9.55 },
  { id: 'shipped', at: 12.45, stop: 14.1 },
  { id: 'lab', at: 15.8, stop: 18.2 },
  { id: 'close', at: 18.8, stop: 21.1 },
];

export const LAYOUT = {
  Z0: 9, // camera z at the start of the flight
  Z1: -158, // camera z at the end of the flight
  C: [0, 0, -182], // the point all constellations converge to (editor scene)
  S: [0, 0, -268], // centre of the four-rules shapes and of the final constellation
  sizes: [34, 41, 36, 44, 38, 33, 40, 37, 42, 35, 39, 36, 40], // 13 departments, 495 stars in total
  ang: { rulesEnd: 1.35, shippedEnd: 1.75, labEnd: 2.0 }, // camera orbit around S (radians)
};

// The flight path the camera follows through the constellations, as a lateral wobble
// (x, y) versus progress q in 0..1. Both the camera and the cluster placement use it,
// so the camera always threads close to every constellation.
const railRaw = (q) => [
  2.6 * Math.sin(q * 10.5) + 1.1 * Math.sin(q * 23.0),
  1.5 * Math.cos(q * 8.3) + 0.7 * Math.sin(q * 17.0),
];
const r0 = railRaw(0);
export function rail(q) {
  const r = railRaw(q);
  return [r[0] - r0[0], r[1] - r0[1]];
}

export function clusterCenter(k) {
  const z = -16 - k * 11.5;
  const q = (z - LAYOUT.Z0) / (LAYOUT.Z1 - LAYOUT.Z0);
  const [rx, ry] = rail(q);
  const a = k * 2.39996 + 0.7;
  const rr = 7.0 + 2.2 * Math.sin(k * 1.7);
  return [rx + Math.cos(a) * rr, ry + Math.sin(a) * rr * 0.62, z];
}
