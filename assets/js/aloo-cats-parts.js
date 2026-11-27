// Shared procedural 3D feline geometry & canvas fur-texture helpers for /aloomannu/.
// Uses only the site's pinned Three.js module — zero external assets or pasted photos.
import * as THREE from 'three';

export function makeCanvas(w, h, drawFn) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  if (ctx) drawFn(ctx, w, h);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

export function paintFurStrokes(ctx, x0, y0, w, h, count, color, alpha, len, seed = 9187) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.globalAlpha = alpha;
  ctx.lineWidth = 1.35;
  // Deterministic Park-Miller LCG for repeatable procedural fur strokes (not cryptographic).
  let s = seed;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < count; i++) {
    const x = x0 + rnd() * w, y = y0 + rnd() * h;
    const ang = (rnd() - 0.5) * 0.65 + Math.PI * 0.5;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + Math.cos(ang) * len, y + Math.sin(ang) * len);
    ctx.stroke();
  }
  ctx.restore();
}

export function makeIrisTexture(baseHex, rimHex, pupilWidth) {
  return makeCanvas(256, 256, (ctx, w, h) => {
    const cx = w / 2, cy = h / 2, r = w * 0.49;
    const g = ctx.createRadialGradient(cx, cy, r * 0.10, cx, cy, r);
    g.addColorStop(0, '#c2c88e');
    g.addColorStop(0.52, baseHex);
    g.addColorStop(0.88, rimHex);
    g.addColorStop(1, '#121510');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(236,242,202,0.26)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    for (let i = 0; i < 64; i++) {
      const a = (i / 64) * Math.PI * 2;
      ctx.moveTo(cx + Math.cos(a) * r * 0.18, cy + Math.sin(a) * r * 0.18);
      ctx.lineTo(cx + Math.cos(a) * r * 0.86, cy + Math.sin(a) * r * 0.86);
    }
    ctx.stroke();
    ctx.fillStyle = '#07090c';
    ctx.beginPath();
    ctx.ellipse(cx, cy, r * pupilWidth, r * 0.74, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.96)';
    ctx.beginPath(); ctx.ellipse(cx - r * 0.24, cy - r * 0.25, r * 0.15, r * 0.10, -0.35, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.50)';
    ctx.beginPath(); ctx.arc(cx + r * 0.22, cy + r * 0.23, r * 0.06, 0, Math.PI * 2); ctx.fill();
  });
}

export function makeLeftHeadTexture() {
  return makeCanvas(1024, 1024, (ctx, w, h) => {
    ctx.fillStyle = '#f7f4ed';
    ctx.fillRect(0, 0, w, h);
    paintFurStrokes(ctx, 0, 0, w, h, 3400, '#e5ded2', 0.30, 15, 4111);
    paintFurStrokes(ctx, 0, 0, w, h, 2200, '#ffffff', 0.55, 13, 7331);
    ctx.fillStyle = '#11141c';
    ctx.beginPath();
    ctx.moveTo(w * 0.14, h * 0.03);
    ctx.bezierCurveTo(w * 0.26, h * 0.01, w * 0.42, h * 0.04, w * 0.468, h * 0.12);
    ctx.bezierCurveTo(w * 0.465, h * 0.26, w * 0.415, h * 0.365, w * 0.335, h * 0.375);
    ctx.bezierCurveTo(w * 0.24, h * 0.38, w * 0.16, h * 0.32, w * 0.13, h * 0.20);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(w * 0.532, h * 0.13);
    ctx.bezierCurveTo(w * 0.58, h * 0.04, w * 0.74, h * 0.01, w * 0.86, h * 0.04);
    ctx.bezierCurveTo(w * 0.88, h * 0.20, w * 0.80, h * 0.33, w * 0.675, h * 0.365);
    ctx.bezierCurveTo(w * 0.59, h * 0.36, w * 0.536, h * 0.26, w * 0.532, h * 0.13);
    ctx.closePath();
    ctx.fill();
    paintFurStrokes(ctx, w * 0.16, h * 0.05, w * 0.30, h * 0.28, 520, '#1b2230', 0.24, 12, 8821);
    paintFurStrokes(ctx, w * 0.54, h * 0.05, w * 0.30, h * 0.28, 520, '#1b2230', 0.24, 12, 8923);
    const blush = ctx.createRadialGradient(w * 0.5, h * 0.58, 8, w * 0.5, h * 0.58, w * 0.085);
    blush.addColorStop(0, 'rgba(228, 182, 178, 0.34)');
    blush.addColorStop(1, 'rgba(247, 244, 237, 0)');
    ctx.fillStyle = blush;
    ctx.fillRect(w * 0.39, h * 0.46, w * 0.22, h * 0.24);
  });
}

export function makeRightHeadTexture() {
  return makeCanvas(1024, 1024, (ctx, w, h) => {
    ctx.fillStyle = '#f8f5ee';
    ctx.fillRect(0, 0, w, h);
    paintFurStrokes(ctx, 0, 0, w, h, 2800, '#e5ded2', 0.26, 14, 3319);
    ctx.fillStyle = '#0d1017';
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(w, 0);
    ctx.lineTo(w, h * 0.585);
    ctx.bezierCurveTo(w * 0.76, h * 0.595, w * 0.675, h * 0.625, w * 0.618, h * 0.602);
    ctx.bezierCurveTo(w * 0.562, h * 0.580, w * 0.530, h * 0.445, w * 0.500, h * 0.325);
    ctx.bezierCurveTo(w * 0.470, h * 0.445, w * 0.438, h * 0.580, w * 0.382, h * 0.602);
    ctx.bezierCurveTo(w * 0.325, h * 0.625, w * 0.24, h * 0.595, 0, h * 0.585);
    ctx.closePath();
    ctx.fill();
    paintFurStrokes(ctx, 0, 0, w, h * 0.54, 1500, '#1a2232', 0.22, 12, 9901);
  });
}

export function sculptFelineHeadGeo(radius, muzzleLen, cheekWidth, bridgeLift = 0.05) {
  const geo = new THREE.SphereGeometry(radius, 64, 48);
  geo.rotateY(-Math.PI * 0.5);
  const pos = geo.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    const nx = v.x / radius, ny = v.y / radius, nz = v.z / radius;
    const cheek = Math.exp(-Math.pow(ny + 0.16, 2) * 5.2) * Math.max(0, nz + 0.20);
    v.x *= 1.0 + cheek * cheekWidth;
    if (ny > 0.34) v.y *= 0.92;
    if (nz < 0) v.z *= 0.90;
    if (nz > 0.18 && ny < 0.22 && ny > -0.68) {
      const mFactor = Math.exp(-Math.pow(nx, 2) * 4.8) * Math.exp(-Math.pow(ny + 0.25, 2) * 6.6);
      const bridge = Math.exp(-Math.pow(nx, 2) * 14.0) * Math.exp(-Math.pow(ny - 0.02, 2) * 9.0);
      v.z += (mFactor * muzzleLen + bridge * bridgeLift) * radius;
      v.y -= mFactor * radius * 0.045;
    }
    if (ny < -0.34) v.x *= 1.0 - Math.min(1, (-ny - 0.34) * 1.45) * 0.28;
    pos.setXYZ(i, v.x, v.y, v.z);
  }
  geo.computeVertexNormals();
  return geo;
}

export function buildEar(outerColor, innerColor, height, width, tuftColor) {
  const group = new THREE.Group();
  const outerGeo = new THREE.ConeGeometry(width, height, 28, 8, false);
  const p = outerGeo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    // Clamp: Float32 rounding can push the cone tip to t = -1e-8, and Math.pow(negative, 2.2) is NaN.
    const t = Math.min(1, Math.max(0, (y + height * 0.5) / height));
    p.setXYZ(i, x + Math.pow(t, 2.2) * width * 0.06, y + height * 0.42, z * 0.46 - Math.sin(t * Math.PI) * width * 0.14);
  }
  outerGeo.computeVertexNormals();
  group.add(new THREE.Mesh(outerGeo, new THREE.MeshStandardMaterial({ color: outerColor, roughness: 0.84 })));

  const innerGeo = new THREE.ConeGeometry(width * 0.68, height * 0.76, 24, 4, false);
  const ip = innerGeo.attributes.position;
  for (let i = 0; i < ip.count; i++) {
    ip.setXYZ(i, ip.getX(i), ip.getY(i) + height * 0.38, ip.getZ(i) * 0.25 + width * 0.15);
  }
  innerGeo.computeVertexNormals();
  group.add(new THREE.Mesh(innerGeo, new THREE.MeshStandardMaterial({ color: innerColor, roughness: 0.74 })));

  const wispMat = new THREE.MeshBasicMaterial({ color: tuftColor, transparent: true, opacity: 0.58 });
  for (let k = -2; k <= 2; k++) {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(k * width * 0.11, height * 0.12, width * 0.16),
      new THREE.Vector3(k * width * 0.17, height * 0.30, width * 0.25),
    ]);
    group.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 6, 0.0038, 4, false), wispMat));
  }
  return group;
}

export function buildNoseAndMouth(noseColor, scale = 1.0) {
  const g = new THREE.Group();
  const noseMat = new THREE.MeshStandardMaterial({ color: noseColor, roughness: 0.46 });
  const top = new THREE.Mesh(new THREE.SphereGeometry(0.072 * scale, 20, 16), noseMat);
  top.scale.set(1.34, 0.78, 0.84);
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.064 * scale, 0.082 * scale, 16), noseMat);
  tip.rotation.x = Math.PI;
  tip.scale.set(1.12, 1.0, 0.76);
  tip.position.set(0, -0.040 * scale, -0.004 * scale);
  g.add(top, tip);
  const darkMat = new THREE.MeshBasicMaterial({ color: 0x93696c, transparent: true, opacity: 0.34 });
  const nostrilGeo = new THREE.SphereGeometry(0.014 * scale, 8, 8);
  [-1, 1].forEach((s) => {
    const nostril = new THREE.Mesh(nostrilGeo, darkMat);
    nostril.position.set(0.039 * scale * s, -0.024 * scale, 0.046 * scale);
    const lipCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, -0.074 * scale, 0.026 * scale),
      new THREE.Vector3(0.048 * scale * s, -0.106 * scale, 0.012 * scale),
      new THREE.Vector3(0.098 * scale * s, -0.100 * scale, -0.020 * scale),
    ]);
    g.add(nostril, new THREE.Mesh(new THREE.TubeGeometry(lipCurve, 8, 0.0038 * scale, 4, false), darkMat));
  });
  return g;
}

export function buildPaw(whiteMat, padDarkAccents = false) {
  const paw = new THREE.Group();
  const base = new THREE.Mesh(new THREE.SphereGeometry(0.28, 24, 18), whiteMat);
  base.scale.set(1.16, 0.58, 1.12);
  paw.add(base);
  const xs = [-0.185, -0.062, 0.062, 0.185], zs = [0.15, 0.22, 0.22, 0.15];
  const toeGeo = new THREE.SphereGeometry(0.10, 18, 14);
  const clawMat = padDarkAccents ? new THREE.MeshStandardMaterial({ color: 0x23252c, roughness: 0.6 }) : null;
  const clawGeo = padDarkAccents ? new THREE.ConeGeometry(0.020, 0.052, 8) : null;
  xs.forEach((tx, idx) => {
    const toe = new THREE.Mesh(toeGeo, whiteMat);
    toe.scale.set(0.86, 0.78, 1.30);
    toe.position.set(tx, -0.04, zs[idx]);
    paw.add(toe);
    if (clawMat && (idx === 0 || idx === 1)) {
      const tip = new THREE.Mesh(clawGeo, clawMat);
      tip.rotation.x = Math.PI * 0.58;
      tip.position.set(tx, -0.090, zs[idx] + 0.12);
      paw.add(tip);
    }
  });
  return paw;
}

export function addWhiskers(parent, ox, oy, oz, side, count, len, spreadY, radius = 0.003, opacity = 0.64) {
  const mat = new THREE.MeshBasicMaterial({ color: 0xf4f7fc, transparent: true, opacity });
  for (let i = 0; i < count; i++) {
    const f = i / Math.max(1, count - 1) - 0.5;
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(ox * side, oy + f * 0.072, oz),
      new THREE.Vector3((ox + len * 0.50) * side, oy + f * spreadY * 0.44 + 0.02, oz + 0.03),
      new THREE.Vector3((ox + len) * side, oy + f * spreadY - 0.16, oz - 0.08),
    ]);
    parent.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 14, radius, 5, false), mat));
  }
}
