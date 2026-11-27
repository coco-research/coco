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

function addCatEyes(headPivot, opts) {
  const eyeMat = new THREE.MeshPhysicalMaterial({
    map: makeIrisTexture(opts.irisBase, opts.irisRim, opts.pupilWidth),
    roughness: opts.eyeRoughness,
    clearcoat: 1.0,
  });
  const lidMat = new THREE.MeshStandardMaterial({ color: opts.lidColor, roughness: opts.lidRoughness });
  const lashMat = opts.lash ? new THREE.MeshStandardMaterial({ color: opts.lash.color, roughness: opts.lash.roughness }) : null;
  const eyeGeo = new THREE.SphereGeometry(opts.radius, opts.segs[0], opts.segs[1]);
  const lidGeo = new THREE.SphereGeometry(opts.lidRadius, opts.lidSegs[0], opts.lidSegs[1], 0, Math.PI * 2, 0, Math.PI * opts.lidArc);
  const lashGeo = lashMat ? new THREE.TorusGeometry(opts.lash.radius, opts.lash.tube, 8, 22, Math.PI * 0.88) : null;
  const lids = [];
  [-1, 1].forEach((s) => {
    const eye = new THREE.Mesh(eyeGeo, eyeMat);
    eye.scale.set(...opts.eyeScale);
    eye.rotation.set(opts.eyeRotX, -Math.PI * 0.5 + s * opts.eyeRotY, -s * opts.eyeRotZ);
    eye.position.set(opts.posX * s, opts.posY, opts.posZ);
    const lid = new THREE.Mesh(lidGeo, lidMat);
    lid.scale.set(...opts.lidScale);
    lid.position.copy(eye.position);
    lid.rotation.set(opts.lidRestX, 0, -s * opts.lidTiltZ);
    lids.push(lid);
    headPivot.add(eye, lid);
    if (lashMat) {
      const lash = new THREE.Mesh(lashGeo, lashMat);
      lash.position.set(opts.posX * s, opts.lash.posY, opts.lash.posZ);
      lash.rotation.set(opts.eyeRotX, s * opts.lash.rotY, opts.lash.rotZBase - opts.lash.rotZSide * s);
      headPivot.add(lash);
    }
  });
  return lids;
}

function addCatMuzzle(headPivot, whiteMat, opts) {
  const padGeo = new THREE.SphereGeometry(opts.padRadius, opts.padSegs[0], opts.padSegs[1]);
  [-1, 1].forEach((s) => {
    const pad = new THREE.Mesh(padGeo, whiteMat);
    pad.scale.set(...opts.padScale);
    pad.position.set(opts.padX * s, opts.padY, opts.padZ);
    headPivot.add(pad);
  });
  const nose = buildNoseAndMouth(opts.noseColor, opts.noseScale);
  nose.position.set(0, opts.noseY, opts.noseZ);
  const chin = new THREE.Mesh(new THREE.SphereGeometry(opts.chinRadius, 18, 14), whiteMat);
  chin.scale.set(...opts.chinScale);
  chin.position.set(0, opts.chinY, opts.chinZ);
  headPivot.add(nose, chin);
  const w = opts.whiskers;
  addWhiskers(headPivot, w.x, w.y, w.z, -1, w.count, w.lenLeft, w.spreadLeft, w.radius, w.opacity);
  addWhiskers(headPivot, w.x, w.y, w.z,  1, w.count, w.lenRight, w.spreadRight, w.radius, w.opacity);
  return chin;
}

function addPaws(root, whiteMat, specs) {
  specs.forEach(([padDarkAccents, pos, rotY]) => {
    const paw = buildPaw(whiteMat, padDarkAccents);
    paw.position.set(...pos);
    paw.rotation.y = rotY;
    root.add(paw);
  });
}

function buildCat(spec) {
  const root = new THREE.Group();
  const whiteTex = makeCanvas(512, 512, (ctx, w, h) => {
    ctx.fillStyle = spec.fur.base; ctx.fillRect(0, 0, w, h);
    paintFurStrokes(ctx, 0, 0, w, h, spec.fur.count, '#e4ddd1', spec.fur.alpha, 15, spec.fur.seed);
  });
  const whiteMat = new THREE.MeshStandardMaterial({ map: whiteTex, roughness: spec.fur.roughness, metalness: 0.01 });
  spec.buildBody(root, whiteMat);

  const { rest, baseRot } = spec;
  const headPivot = new THREE.Group();
  headPivot.position.set(spec.head.x, rest.headY, spec.head.z);
  const headMat = new THREE.MeshStandardMaterial({
    map: spec.head.texture(),
    roughness: spec.head.roughness,
    metalness: spec.head.metalness,
  });
  headPivot.add(new THREE.Mesh(sculptFelineHeadGeo(...spec.head.geo), headMat));

  const [earL, earR] = spec.ears.map((e) => {
    const ear = buildEar(e.outer, e.inner, e.height, e.width, e.tuft);
    ear.position.set(...e.pos);
    ear.rotation.set(...e.rot);
    return ear;
  });
  headPivot.add(earL, earR);

  const lids = addCatEyes(headPivot, { ...spec.eyes, lidRestX: rest.lidRestX, lidTiltZ: rest.lidTiltZ });
  const chin = addCatMuzzle(headPivot, whiteMat, { ...spec.muzzle, chinY: rest.chinY });
  if (spec.decorateHead) spec.decorateHead(headPivot);

  headPivot.rotation.set(baseRot.x, baseRot.y, baseRot.z);
  root.add(headPivot);
  return { root, headPivot, earL, earR, lids, chin, baseRot, rest };
}

export function buildLeftCat() {
  const rest = { headY: -1.10, chinY: -0.32, lidRestX: -0.26, lidTiltZ: 0.18, earRRestZ: -0.52 };
  return buildCat({
    fur: { base: '#f7f4ed', count: 2600, alpha: 0.30, seed: 2203, roughness: 0.86 },
    buildBody(root, whiteMat) {
      const body = new THREE.Mesh(new THREE.SphereGeometry(0.88, 36, 28), whiteMat);
      body.scale.set(0.94, 0.88, 1.12);
      body.position.set(0.36, -1.94, 0.40);
      root.add(body);
      const legGeo = new THREE.CapsuleGeometry(0.21, 0.56, 12, 18);
      [[-0.16, -1.86, 0.98], [0.86, -1.88, 0.98]].forEach(([lx, ly, lz]) => {
        const leg = new THREE.Mesh(legGeo, whiteMat);
        leg.rotation.x = 0.78; leg.position.set(lx, ly, lz);
        root.add(leg);
      });
      addPaws(root, whiteMat, [
        [false, [-0.22, -2.23, 1.48], 0.08],
        [true,  [0.94, -2.23, 1.50], -0.06],
      ]);
    },
    rest,
    baseRot: { x: 0.36, y: 0.17, z: -0.05 },
    head: { x: 0.46, z: 1.10, texture: makeLeftHeadTexture, roughness: 0.84, metalness: 0.01, geo: [0.75, 0.34, 0.09, 0.06] },
    ears: [
      { outer: 0x12151e, inner: 0xdca19a, height: 0.64, width: 0.32, tuft: 0xf7f4ed, pos: [-0.44, 0.43, 0.02], rot: [0.16, -0.22, 0.56] },
      { outer: 0x12151e, inner: 0xdca19a, height: 0.66, width: 0.33, tuft: 0xf7f4ed, pos: [0.44, 0.45, 0.02], rot: [0.14, 0.22, rest.earRRestZ] },
    ],
    eyes: {
      irisBase: '#989d55', irisRim: '#4b5030', pupilWidth: 0.20, eyeRoughness: 0.06,
      lidColor: 0xf1ebe0, lidRoughness: 0.80, radius: 0.128, segs: [24, 20],
      eyeScale: [1.10, 0.88, 0.72], eyeRotX: 0.18, eyeRotY: 0.24, eyeRotZ: 0.16,
      posX: 0.285, posY: 0.03, posZ: 0.67, lidRadius: 0.138, lidSegs: [22, 16], lidArc: 0.50,
      lidScale: [1.12, 0.92, 0.76],
      lash: { color: 0x5c4744, roughness: 0.70, radius: 0.122, tube: 0.009, posY: 0.045, posZ: 0.725, rotY: 0.22, rotZBase: 0.16, rotZSide: 0.18 },
    },
    muzzle: {
      padRadius: 0.145, padSegs: [18, 14], padScale: [1.04, 0.80, 0.90], padX: 0.115, padY: -0.21, padZ: 0.83,
      noseColor: 0xe69ca2, noseScale: 0.92, noseY: -0.15, noseZ: 1.03,
      chinRadius: 0.15, chinScale: [1.04, 0.66, 0.90], chinZ: 0.78,
      whiskers: { x: 0.19, y: -0.21, z: 0.82, count: 5, lenLeft: 0.66, lenRight: 0.62, spreadLeft: 0.19, spreadRight: 0.19, radius: 0.0025, opacity: 0.50 },
    },
  });
}

export function buildRightCat() {
  const rest = { headY: 0.42, chinY: -0.38, lidRestX: -0.72, lidTiltZ: 0.14, earLRestZ: 0.40 };
  return buildCat({
    fur: { base: '#f8f5ee', count: 2800, alpha: 0.28, seed: 6653, roughness: 0.85 },
    buildBody(root, whiteMat) {
      const blackMat = new THREE.MeshStandardMaterial({ color: 0x0f1219, roughness: 0.82, metalness: 0.02 });
      const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.84, 1.48, 22, 32), whiteMat);
      torso.rotation.set(0.18, -0.18, 0.22);
      torso.scale.set(1.04, 1.0, 0.96);
      torso.position.set(3.24, -1.12, 0.52);
      const chest = new THREE.Mesh(new THREE.SphereGeometry(0.80, 28, 22), whiteMat);
      chest.scale.set(1.04, 1.16, 0.88);
      chest.position.set(3.04, -0.66, 0.72);
      root.add(torso, chest);
      const shoulderGeo = new THREE.SphereGeometry(0.28, 18, 14);
      [[2.62, -0.84, 0.90], [3.48, -0.84, 0.92]].forEach(([sx, sy, sz]) => {
        const sh = new THREE.Mesh(shoulderGeo, whiteMat);
        sh.scale.set(0.96, 1.24, 0.94); sh.position.set(sx, sy, sz);
        root.add(sh);
      });
      const flankPatch = new THREE.Mesh(new THREE.SphereGeometry(0.48, 22, 18), blackMat);
      flankPatch.scale.set(0.55, 1.15, 0.95);
      flankPatch.position.set(4.01, -1.52, 0.58); flankPatch.rotation.z = 0.22;
      root.add(flankPatch);
      [
        [0.215, 1.40, [2.58, -1.46, 1.04], [0.28, 0, -0.04]],
        [0.22,  1.42, [3.52, -1.45, 1.06], [0.29, 0,  0.05]],
      ].forEach(([rad, len, pos, rot]) => {
        const leg = new THREE.Mesh(new THREE.CapsuleGeometry(rad, len, 16, 22), whiteMat);
        leg.position.set(...pos); leg.rotation.set(...rot);
        root.add(leg);
      });
      addPaws(root, whiteMat, [
        [false, [2.52, -2.23, 1.54], -0.05],
        [false, [3.58, -2.23, 1.58], -0.10],
      ]);
    },
    rest,
    baseRot: { x: 0.05, y: -0.11, z: 0.12 },
    head: { x: 2.72, z: 1.00, texture: makeRightHeadTexture, roughness: 0.80, metalness: 0.02, geo: [0.91, 0.31, 0.16, 0.05] },
    ears: [
      { outer: 0x0d1017, inner: 0xa87469, height: 0.85, width: 0.39, tuft: 0xebe4d9, pos: [-0.51, 0.56, 0.02], rot: [0.10, -0.12, rest.earLRestZ] },
      { outer: 0x0d1017, inner: 0xa87469, height: 0.89, width: 0.40, tuft: 0xebe4d9, pos: [0.45, 0.62, 0.02], rot: [0.10, 0.12, -0.24] },
    ],
    eyes: {
      irisBase: '#889662', irisRim: '#3a4327', pupilWidth: 0.22, eyeRoughness: 0.04,
      lidColor: 0x0d1017, lidRoughness: 0.78, radius: 0.184, segs: [28, 24],
      eyeScale: [1.08, 0.96, 0.76], eyeRotX: 0.04, eyeRotY: 0.18, eyeRotZ: 0.10,
      posX: 0.345, posY: 0.07, posZ: 0.81, lidRadius: 0.194, lidSegs: [24, 16], lidArc: 0.48,
      lidScale: [1.09, 0.98, 0.78],
    },
    muzzle: {
      padRadius: 0.19, padSegs: [20, 16], padScale: [1.06, 0.82, 0.92], padX: 0.145, padY: -0.24, padZ: 0.96,
      noseColor: 0xe29798, noseScale: 1.12, noseY: -0.16, noseZ: 1.22,
      chinRadius: 0.19, chinScale: [1.10, 0.66, 0.92], chinZ: 0.90,
      whiskers: { x: 0.24, y: -0.24, z: 0.95, count: 6, lenLeft: 1.12, lenRight: 1.02, spreadLeft: 0.36, spreadRight: 0.34, radius: 0.0031, opacity: 0.72 },
    },
    decorateHead(headPivot) {
      const browMat = new THREE.MeshBasicMaterial({ color: 0xf4f7fc, transparent: true, opacity: 0.66 });
      [-1, 1].forEach((s) => {
        for (let b = 0; b < 4; b++) {
          const curve = new THREE.CatmullRomCurve3([
            new THREE.Vector3((0.23 + b * 0.045) * s, 0.26, 0.81),
            new THREE.Vector3((0.38 + b * 0.085) * s, 0.55 + b * 0.035, 0.67),
            new THREE.Vector3((0.54 + b * 0.10) * s, 0.72 + b * 0.03, 0.45),
          ]);
          headPivot.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 10, 0.0028, 4, false), browMat));
        }
      });
    },
  });
}
