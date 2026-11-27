// Procedural 3D feline assemblies & cream ledge for /aloomannu/.
// Uses only the site's pinned Three.js module — zero external assets or pasted photos.
import * as THREE from 'three';
import {
  addWhiskers,
  buildEar,
  buildNoseAndMouth,
  buildPaw,
  makeCanvas,
  makeIrisTexture,
  makeLeftHeadTexture,
  makeRightHeadTexture,
  paintFurStrokes,
  sculptFelineHeadGeo,
} from './aloo-cats-parts.js';

export function buildCreamLedge() {
  const group = new THREE.Group();
  const tex = makeCanvas(512, 256, (ctx, w, h) => {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, '#ebdcc5'); g.addColorStop(0.55, '#e1d0b6'); g.addColorStop(1, '#cfbda0');
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  });
  // Tabletop reaches well below the 400px mobile frame (top face stays at y = -2.355) so no dark void shows under the ledge.
  const slab = new THREE.Mesh(new THREE.BoxGeometry(22, 3.6, 3.8), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.56, metalness: 0.02 }));
  slab.position.set(0, -4.155, 0.25);
  group.add(slab);

  const shadowTex = makeCanvas(128, 128, (ctx, w, h) => {
    const rg = ctx.createRadialGradient(w / 2, h / 2, 4, w / 2, h / 2, w * 0.48);
    rg.addColorStop(0, 'rgba(36, 26, 16, 0.38)'); rg.addColorStop(1, 'rgba(36, 26, 16, 0)');
    ctx.fillStyle = rg; ctx.fillRect(0, 0, w, h);
  });
  const shadowMat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false });
  [[-0.22, 1.54, 0.82], [0.94, 1.56, 0.82], [2.52, 1.60, 0.90], [3.58, 1.62, 0.92]].forEach(([sx, sz, sc]) => {
    const disc = new THREE.Mesh(new THREE.PlaneGeometry(sc, sc * 0.62), shadowMat);
    disc.rotation.x = -Math.PI * 0.5;
    disc.position.set(sx, -2.352, sz);
    group.add(disc);
  });
  return group;
}

export function buildLeftCat() {
  const root = new THREE.Group();
  const whiteTex = makeCanvas(512, 512, (ctx, w, h) => {
    ctx.fillStyle = '#f7f4ed'; ctx.fillRect(0, 0, w, h);
    paintFurStrokes(ctx, 0, 0, w, h, 2600, '#e4ddd1', 0.30, 15, 2203);
  });
  const whiteMat = new THREE.MeshStandardMaterial({ map: whiteTex, roughness: 0.86, metalness: 0.01 });

  const body = new THREE.Mesh(new THREE.SphereGeometry(0.88, 36, 28), whiteMat);
  body.scale.set(0.94, 0.88, 1.12);
  body.position.set(0.36, -1.94, 0.40);
  root.add(body);
  [[-0.16, -1.86, 0.98], [0.86, -1.88, 0.98]].forEach(([lx, ly, lz]) => {
    const leg = new THREE.Mesh(new THREE.CapsuleGeometry(0.21, 0.56, 12, 18), whiteMat);
    leg.rotation.x = 0.78; leg.position.set(lx, ly, lz);
    root.add(leg);
  });

  const pawL = buildPaw(whiteMat, false); pawL.position.set(-0.22, -2.23, 1.48); pawL.rotation.y = 0.08;
  const pawR = buildPaw(whiteMat, true);  pawR.position.set(0.94, -2.23, 1.50);  pawR.rotation.y = -0.06;
  root.add(pawL, pawR);

  const headPivot = new THREE.Group();
  headPivot.position.set(0.46, -1.10, 1.10);
  const headMat = new THREE.MeshStandardMaterial({ map: makeLeftHeadTexture(), roughness: 0.84, metalness: 0.01 });
  headPivot.add(new THREE.Mesh(sculptFelineHeadGeo(0.75, 0.34, 0.09, 0.06), headMat));

  const earL = buildEar(0x12151e, 0xdca19a, 0.64, 0.32, 0xf7f4ed);
  earL.position.set(-0.44, 0.43, 0.02); earL.rotation.set(0.16, -0.22, 0.56);
  const earR = buildEar(0x12151e, 0xdca19a, 0.66, 0.33, 0xf7f4ed);
  earR.position.set(0.44, 0.45, 0.02);  earR.rotation.set(0.14, 0.22, -0.52);
  headPivot.add(earL, earR);

  const eyeMat = new THREE.MeshPhysicalMaterial({ map: makeIrisTexture('#989d55', '#4b5030', 0.20), roughness: 0.06, clearcoat: 1.0 });
  const lidMat = new THREE.MeshStandardMaterial({ color: 0xf1ebe0, roughness: 0.80 });
  const lashMat = new THREE.MeshStandardMaterial({ color: 0x5c4744, roughness: 0.70 });
  const lids = [], lidRestX = -0.26;
  [-1, 1].forEach((s) => {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.128, 24, 20), eyeMat);
    eye.scale.set(1.10, 0.88, 0.72);
    eye.rotation.set(0.18, -Math.PI * 0.5 + s * 0.24, -s * 0.16);
    eye.position.set(0.285 * s, 0.03, 0.67);
    const lid = new THREE.Mesh(new THREE.SphereGeometry(0.138, 22, 16, 0, Math.PI * 2, 0, Math.PI * 0.50), lidMat);
    lid.scale.set(1.12, 0.92, 0.76);
    lid.position.copy(eye.position);
    lid.rotation.set(lidRestX, 0, -s * 0.18);
    const lash = new THREE.Mesh(new THREE.TorusGeometry(0.122, 0.009, 8, 22, Math.PI * 0.88), lashMat);
    lash.position.set(0.285 * s, 0.045, 0.725);
    lash.rotation.set(0.18, s * 0.22, 0.16 - 0.18 * s);
    lids.push(lid);
    headPivot.add(eye, lid, lash);
  });

  [-1, 1].forEach((s) => {
    const pad = new THREE.Mesh(new THREE.SphereGeometry(0.145, 18, 14), whiteMat);
    pad.scale.set(1.04, 0.80, 0.90); pad.position.set(0.115 * s, -0.21, 0.83);
    headPivot.add(pad);
  });
  const nose = buildNoseAndMouth(0xe69ca2, 0.92);
  nose.position.set(0, -0.15, 1.03);
  const chin = new THREE.Mesh(new THREE.SphereGeometry(0.15, 18, 14), whiteMat);
  chin.scale.set(1.04, 0.66, 0.90); chin.position.set(0, -0.32, 0.78);
  headPivot.add(nose, chin);

  addWhiskers(headPivot, 0.19, -0.21, 0.82, -1, 5, 0.66, 0.19, 0.0025, 0.50);
  addWhiskers(headPivot, 0.19, -0.21, 0.82,  1, 5, 0.62, 0.19, 0.0025, 0.50);

  const baseRot = { x: 0.36, y: 0.17, z: -0.05 };
  headPivot.rotation.set(baseRot.x, baseRot.y, baseRot.z);
  root.add(headPivot);
  return { root, headPivot, earL, earR, lids, lidRestX, chin, baseRot };
}

export function buildRightCat() {
  const root = new THREE.Group();
  const whiteTex = makeCanvas(512, 512, (ctx, w, h) => {
    ctx.fillStyle = '#f8f5ee'; ctx.fillRect(0, 0, w, h);
    paintFurStrokes(ctx, 0, 0, w, h, 2800, '#e4ddd1', 0.28, 15, 6653);
  });
  const whiteMat = new THREE.MeshStandardMaterial({ map: whiteTex, roughness: 0.85, metalness: 0.01 });
  const blackMat = new THREE.MeshStandardMaterial({ color: 0x0f1219, roughness: 0.82, metalness: 0.02 });

  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.84, 1.48, 22, 32), whiteMat);
  torso.rotation.set(0.18, -0.18, 0.22);
  torso.scale.set(1.04, 1.0, 0.96);
  torso.position.set(3.24, -1.12, 0.52);
  const chest = new THREE.Mesh(new THREE.SphereGeometry(0.80, 28, 22), whiteMat);
  chest.scale.set(1.04, 1.16, 0.88);
  chest.position.set(3.04, -0.66, 0.72);
  root.add(torso, chest);

  [[2.62, -0.84, 0.90], [3.48, -0.84, 0.92]].forEach(([sx, sy, sz]) => {
    const sh = new THREE.Mesh(new THREE.SphereGeometry(0.28, 18, 14), whiteMat);
    sh.scale.set(0.96, 1.24, 0.94); sh.position.set(sx, sy, sz);
    root.add(sh);
  });

  const flankPatch = new THREE.Mesh(new THREE.SphereGeometry(0.48, 22, 18), blackMat);
  flankPatch.scale.set(0.55, 1.15, 0.95);
  flankPatch.position.set(4.01, -1.52, 0.58); flankPatch.rotation.z = 0.22;
  root.add(flankPatch);

  const legL = new THREE.Mesh(new THREE.CapsuleGeometry(0.215, 1.40, 16, 22), whiteMat);
  legL.position.set(2.58, -1.46, 1.04); legL.rotation.set(0.28, 0, -0.04);
  const legR = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 1.42, 16, 22), whiteMat);
  legR.position.set(3.52, -1.45, 1.06); legR.rotation.set(0.29, 0, 0.05);
  const pawL = buildPaw(whiteMat, false); pawL.position.set(2.52, -2.23, 1.54); pawL.rotation.y = -0.05;
  const pawR = buildPaw(whiteMat, false); pawR.position.set(3.58, -2.23, 1.58); pawR.rotation.y = -0.10;
  root.add(legL, legR, pawL, pawR);

  const headPivot = new THREE.Group();
  headPivot.position.set(2.72, 0.42, 1.00);
  const headMat = new THREE.MeshStandardMaterial({ map: makeRightHeadTexture(), roughness: 0.80, metalness: 0.02 });
  headPivot.add(new THREE.Mesh(sculptFelineHeadGeo(0.91, 0.31, 0.16, 0.05), headMat));

  const earL = buildEar(0x0d1017, 0xa87469, 0.85, 0.39, 0xebe4d9);
  earL.position.set(-0.51, 0.56, 0.02); earL.rotation.set(0.10, -0.12, 0.40);
  const earR = buildEar(0x0d1017, 0xa87469, 0.89, 0.40, 0xebe4d9);
  earR.position.set(0.45, 0.62, 0.02);  earR.rotation.set(0.10, 0.12, -0.24);
  headPivot.add(earL, earR);

  const eyeMat = new THREE.MeshPhysicalMaterial({ map: makeIrisTexture('#889662', '#3a4327', 0.22), roughness: 0.04, clearcoat: 1.0 });
  const lidMat = new THREE.MeshStandardMaterial({ color: 0x0d1017, roughness: 0.78 });
  const lids = [], lidRestX = -0.72;
  [-1, 1].forEach((s) => {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.184, 28, 24), eyeMat);
    eye.scale.set(1.08, 0.96, 0.76);
    eye.rotation.set(0.04, -Math.PI * 0.5 + s * 0.18, -s * 0.10);
    eye.position.set(0.345 * s, 0.07, 0.81);
    const lid = new THREE.Mesh(new THREE.SphereGeometry(0.194, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.48), lidMat);
    lid.scale.set(1.09, 0.98, 0.78);
    lid.position.copy(eye.position);
    lid.rotation.set(lidRestX, 0, -s * 0.14);
    lids.push(lid);
    headPivot.add(eye, lid);
  });

  [-1, 1].forEach((s) => {
    const pad = new THREE.Mesh(new THREE.SphereGeometry(0.19, 20, 16), whiteMat);
    pad.scale.set(1.06, 0.82, 0.92); pad.position.set(0.145 * s, -0.24, 0.96);
    headPivot.add(pad);
  });
  const nose = buildNoseAndMouth(0xe29798, 1.12);
  nose.position.set(0, -0.16, 1.22);
  const chin = new THREE.Mesh(new THREE.SphereGeometry(0.19, 18, 14), whiteMat);
  chin.scale.set(1.10, 0.66, 0.92); chin.position.set(0, -0.38, 0.90);
  headPivot.add(nose, chin);

  addWhiskers(headPivot, 0.24, -0.24, 0.95, -1, 6, 1.12, 0.36, 0.0031, 0.72);
  addWhiskers(headPivot, 0.24, -0.24, 0.95,  1, 6, 1.02, 0.34, 0.0031, 0.72);
  [-1, 1].forEach((s) => {
    const browMat = new THREE.MeshBasicMaterial({ color: 0xf4f7fc, transparent: true, opacity: 0.66 });
    for (let b = 0; b < 4; b++) {
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3((0.23 + b * 0.045) * s, 0.26, 0.81),
        new THREE.Vector3((0.38 + b * 0.085) * s, 0.55 + b * 0.035, 0.67),
        new THREE.Vector3((0.54 + b * 0.10) * s, 0.72 + b * 0.03, 0.45),
      ]);
      headPivot.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 10, 0.0028, 4, false), browMat));
    }
  });

  const baseRot = { x: 0.05, y: -0.11, z: 0.12 };
  headPivot.rotation.set(baseRot.x, baseRot.y, baseRot.z);
  root.add(headPivot);
  return { root, headPivot, earL, earR, lids, lidRestX, chin, baseRot };
}
