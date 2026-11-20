// 3D Three.js banner stage for /aloomannu/ and deterministic repo banner exports (?banner=readme|social).
// Renders two coded black-and-white cats on a cream ledge, flowing signal lines, and "ow ow" / "meh" bubbles.
import * as THREE from 'three';
import { buildCreamLedge, buildLeftCat, buildRightCat } from './aloo-cats-models.js';

function drawBubbleCanvas(canvas, text, textAlpha, tailSide) {
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const bx = 26, by = 22, bw = w - 52, bh = h - 74, r = bh * 0.48;

  ctx.save();
  ctx.strokeStyle = 'rgba(208, 226, 248, 0.90)';
  ctx.fillStyle = 'rgba(12, 29, 53, 0.50)';
  ctx.lineWidth = 3.4;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(bx + r, by);
  ctx.lineTo(bx + bw - r, by);
  ctx.arc(bx + bw - r, by + r, r, -Math.PI / 2, Math.PI / 2);
  if (tailSide === 'right') {
    const tx = bx + bw - r - 28;
    ctx.lineTo(tx + 24, by + bh);
    ctx.lineTo(tx + 34, by + bh + 34);
    ctx.lineTo(tx - 4, by + bh);
  }
  ctx.lineTo(bx + r, by + bh);
  if (tailSide === 'left') {
    const tx = bx + r + 24;
    ctx.lineTo(tx + 12, by + bh);
    ctx.lineTo(tx - 24, by + bh + 36);
    ctx.lineTo(tx - 12, by + bh);
  }
  ctx.arc(bx + r, by + r, r, Math.PI / 2, -Math.PI / 2);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  if (text && textAlpha > 0.01) {
    ctx.globalAlpha = Math.min(1, Math.max(0, textAlpha));
    ctx.fillStyle = '#f2e6d2';
    ctx.font = '500 50px "Archivo", ui-sans-serif, system-ui, -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, bx + bw * 0.5, by + bh * 0.52);
  }
  ctx.restore();
}

function makeBubbleActor(text, tailSide, pos, size) {
  const canvas = document.createElement('canvas');
  canvas.width = 420; canvas.height = 230;
  drawBubbleCanvas(canvas, text, 1, tailSide);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(size[0], size[1]), mat);
  mesh.position.set(pos[0], pos[1], pos[2]);
  let shownAlpha = -1;
  return {
    mesh,
    update(alpha, lift, scale) {
      const q = Math.round(alpha * 40) / 40;
      if (q !== shownAlpha) {
        shownAlpha = q;
        drawBubbleCanvas(canvas, text, q, tailSide);
        tex.needsUpdate = true;
      }
      mesh.position.y = pos[1] + lift;
      mesh.scale.setScalar(scale);
    },
  };
}

function buildFlowLines() {
  const specs = [
    { color: 0xdbe5f2, opacity: 0.74, radius: 0.012, pts: [[-2.18, -2.28, 0.3], [-1.52, -2.02, 0.3], [-1.05, -1.24, 0.3], [-0.55, -1.08, 0.3]] },
    { color: 0x73b7ff, opacity: 0.88, radius: 0.013, pts: [[-0.08, 0.34, 0.25], [0.46, 0.22, 0.25], [1.14, 0.52, 0.25], [1.78, 0.58, 0.25]] },
    { color: 0x3b77d8, opacity: 0.74, radius: 0.011, pts: [[1.74, -2.10, 0.15], [1.96, -1.66, 0.15], [2.36, -1.32, 0.15]] },
    { color: 0x73b7ff, opacity: 0.88, radius: 0.013, pts: [[4.02, 0.52, 0.25], [4.62, 0.60, 0.25], [5.28, 1.02, 0.25], [5.95, 1.18, 0.25]] },
  ];
  const group = new THREE.Group();
  const lines = specs.map((sp, idx) => {
    const curve = new THREE.CatmullRomCurve3(sp.pts.map((p) => new THREE.Vector3(p[0], p[1], p[2])));
    const mat = new THREE.MeshBasicMaterial({ color: sp.color, transparent: true, opacity: sp.opacity });
    const mesh = new THREE.Mesh(new THREE.TubeGeometry(curve, 36, sp.radius, 6, false), mat);
    group.add(mesh);
    return { mesh, mat, baseOpacity: sp.opacity, phase: idx * 1.4 };
  });
  return {
    group,
    animate(t) {
      lines.forEach((ln) => {
        ln.mesh.position.y = Math.sin(t * 1.15 + ln.phase) * 0.045;
        ln.mesh.position.x = Math.cos(t * 0.85 + ln.phase) * 0.03;
        ln.mat.opacity = ln.baseOpacity * (0.82 + 0.18 * Math.sin(t * 1.6 + ln.phase));
      });
    },
  };
}

function smoothWindow(t, start, riseEnd, holdEnd, fallEnd) {
  if (t <= start || t >= fallEnd) return 0;
  if (t < riseEnd) {
    const u = (t - start) / (riseEnd - start);
    return u * u * (3 - 2 * u);
  }
  if (t <= holdEnd) return 1;
  const u = 1 - (t - holdEnd) / (fallEnd - holdEnd);
  return u * u * (3 - 2 * u);
}

function bootCatsStage() {
  const canvas = document.getElementById('aloo-cats-canvas');
  if (!canvas) return;
  const params = new URLSearchParams(location.search);
  const bannerMode = params.get('banner');
  const isBannerExport = bannerMode === 'readme' || bannerMode === 'social';
  const outlineOnly = params.get('bubbles') === 'outline';
  if (isBannerExport) {
    document.documentElement.setAttribute('data-banner-export', bannerMode);
  }

  const stageEl = canvas.closest('.aloo-banner');
  const toggleBtn = document.querySelector('[data-cats-motion-toggle]');

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
  } catch (e) {
    if (stageEl) stageEl.classList.add('aloo-webgl-fallback');
    return;
  }
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.06;
  renderer.setClearColor(0x0c1e36, 1);

  const scene = new THREE.Scene();
  const bgCanvas = document.createElement('canvas');
  bgCanvas.width = 512; bgCanvas.height = 256;
  const bctx = bgCanvas.getContext('2d');
  const bgGrad = bctx.createRadialGradient(340, 125, 30, 260, 130, 340);
  bgGrad.addColorStop(0, '#142d4e');
  bgGrad.addColorStop(0.56, '#0c1e36');
  bgGrad.addColorStop(1, '#071325');
  bctx.fillStyle = bgGrad; bctx.fillRect(0, 0, 512, 256);
  const bgTex = new THREE.CanvasTexture(bgCanvas);
  bgTex.colorSpace = THREE.SRGBColorSpace;
  const bgMesh = new THREE.Mesh(new THREE.PlaneGeometry(28, 16), new THREE.MeshBasicMaterial({ map: bgTex, depthWrite: false }));
  bgMesh.position.set(0, 0, -3.2);
  scene.add(bgMesh);

  const camera = new THREE.PerspectiveCamera(28, 16 / 9, 0.1, 60);
  scene.add(new THREE.AmbientLight(0xd9e4f5, 1.26));
  const key = new THREE.DirectionalLight(0xfff4e4, 2.04); key.position.set(-2.6, 4.8, 6.4);
  const fill = new THREE.DirectionalLight(0x8ab8ff, 0.78); fill.position.set(4.5, 1.5, 4.2);
  const rim = new THREE.DirectionalLight(0xdbeaff, 0.92); rim.position.set(1.2, 4.2, -3.5);
  scene.add(key, fill, rim);

  const ledge = buildCreamLedge();
  const leftCat = buildLeftCat();
  const rightCat = buildRightCat();
  const flows = buildFlowLines();
  const callBubble = makeBubbleActor('ow ow', 'right', [0.16, 0.88, 0.85], [1.48, 0.82]);
  const replyBubble = makeBubbleActor('meh', 'left', [4.24, 1.72, 0.85], [1.62, 0.88]);

  const stageGroup = new THREE.Group();
  stageGroup.add(ledge, flows.group, leftCat.root, rightCat.root, callBubble.mesh, replyBubble.mesh);
  scene.add(stageGroup);

  const resize = () => {
    const rect = (stageEl || canvas).getBoundingClientRect();
    const w = Math.max(280, Math.round(rect.width || window.innerWidth));
    const h = Math.max(240, Math.round(rect.height || 520));
    const dpr = isBannerExport ? 1 : Math.min(window.devicePixelRatio || 1, 2);
    renderer.setPixelRatio(dpr);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    if (bannerMode === 'readme') {
      camera.fov = 25.8;
      camera.position.set(0.0, -0.05, 13.55);
      camera.lookAt(0.0, -0.11, 0);
    } else if (bannerMode === 'social') {
      camera.fov = 27.2;
      camera.position.set(0.0, -0.04, 13.30);
      camera.lookAt(0.0, -0.10, 0);
    } else if (w <= 760) {
      camera.fov = 34;
      camera.position.set(1.98, 0.62, 18.6);
      camera.lookAt(1.98, -0.28, 0);
    } else {
      camera.fov = 28;
      camera.position.set(0.0, -0.04, 13.2);
      camera.lookAt(0.0, -0.10, 0);
    }
    camera.updateProjectionMatrix();
  };

  const renderFrame = (t, isStatic) => {
    if (isStatic) {
      leftCat.headPivot.position.y = -1.10;
      rightCat.headPivot.position.y = 0.42;
      leftCat.headPivot.rotation.set(leftCat.baseRot.x, leftCat.baseRot.y, leftCat.baseRot.z);
      rightCat.headPivot.rotation.set(rightCat.baseRot.x, rightCat.baseRot.y, rightCat.baseRot.z);
      leftCat.lids.forEach((lid, idx) => lid.rotation.set(leftCat.lidRestX, 0, -(idx === 0 ? -1 : 1) * 0.18));
      rightCat.lids.forEach((lid, idx) => lid.rotation.set(rightCat.lidRestX, 0, -(idx === 0 ? -1 : 1) * 0.14));
      const staticTextAlpha = outlineOnly ? 0 : 0.94;
      callBubble.update(staticTextAlpha, 0, 1);
      replyBubble.update(staticTextAlpha, 0, 1);
      flows.animate(0);
      renderer.render(scene, camera);
      return;
    }

    const cycle = t % 7.6;
    const callW = smoothWindow(cycle, 0.25, 0.75, 2.35, 2.95);
    const replyW = smoothWindow(cycle, 2.75, 3.25, 5.25, 5.95);

    callBubble.update(0.22 + 0.78 * callW, callW * 0.07 + Math.sin(t * 1.7) * 0.02, 0.96 + 0.05 * callW);
    replyBubble.update(0.22 + 0.78 * replyW, replyW * 0.08 + Math.cos(t * 1.5) * 0.02, 0.96 + 0.05 * replyW);

    leftCat.headPivot.position.y = -1.10 + Math.sin(t * 1.8) * 0.012;
    rightCat.headPivot.position.y = 0.42 + Math.sin(t * 1.55 + 1.1) * 0.014;

    leftCat.headPivot.rotation.set(
      leftCat.baseRot.x - callW * 0.08 + Math.sin(t * 0.9) * 0.015,
      leftCat.baseRot.y + callW * 0.05,
      leftCat.baseRot.z,
    );
    leftCat.chin.position.y = -0.32 - Math.max(0, Math.sin(t * 9.0)) * callW * 0.024;
    leftCat.earR.rotation.z = -0.52 - Math.pow(Math.max(0, Math.sin(t * 2.3)), 8) * 0.14;

    rightCat.headPivot.rotation.set(
      rightCat.baseRot.x + replyW * 0.04 + Math.cos(t * 0.8) * 0.014,
      rightCat.baseRot.y - replyW * 0.14,
      rightCat.baseRot.z - replyW * 0.04,
    );
    rightCat.chin.position.y = -0.38 - replyW * 0.022;
    rightCat.earL.rotation.z = 0.40 + Math.pow(Math.max(0, Math.sin(t * 1.9 + 0.8)), 10) * 0.16;

    const blinkR = Math.max(smoothWindow(cycle, 4.05, 4.16, 4.24, 4.38), smoothWindow(cycle, 6.8, 6.9, 6.96, 7.08));
    rightCat.lids.forEach((lid, idx) => lid.rotation.set(rightCat.lidRestX + blinkR * 1.24, 0, -(idx === 0 ? -1 : 1) * 0.14));
    const blinkL = smoothWindow(cycle, 1.75, 1.86, 1.94, 2.08);
    leftCat.lids.forEach((lid, idx) => lid.rotation.set(leftCat.lidRestX + blinkL * 0.78, 0, -(idx === 0 ? -1 : 1) * 0.18));

    flows.animate(t);
    renderer.render(scene, camera);
  };

  let reduced = isBannerExport || document.documentElement.classList.contains('static');
  try { if (matchMedia('(prefers-reduced-motion: reduce)').matches) reduced = true; } catch (e) {}
  let paused = reduced, raf = 0;
  const t0 = performance.now();

  const syncControl = () => { if (toggleBtn) toggleBtn.textContent = paused ? 'Play motion' : 'Pause motion'; };
  const loop = (now) => {
    if (paused) return;
    renderFrame((now - t0) * 0.001, false);
    raf = requestAnimationFrame(loop);
  };
  const setPaused = (next) => {
    paused = next;
    syncControl();
    cancelAnimationFrame(raf);
    if (paused) renderFrame(0, true);
    else raf = requestAnimationFrame(loop);
  };

  resize();
  syncControl();
  if (paused) {
    renderFrame(0, true);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => { resize(); renderFrame(0, true); window.__ALOO_BANNER_READY = true; });
    } else {
      window.__ALOO_BANNER_READY = true;
    }
  } else {
    window.__ALOO_BANNER_READY = true;
    raf = requestAnimationFrame(loop);
  }

  window.addEventListener('resize', () => { resize(); if (paused) renderFrame(0, true); }, { passive: true });
  if (toggleBtn) toggleBtn.addEventListener('click', () => setPaused(!paused));
  document.querySelectorAll('[data-motion-toggle]').forEach((btn) => {
    btn.addEventListener('click', () => setTimeout(() => setPaused(document.documentElement.classList.contains('static')), 0));
  });
  try { matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (ev) => setPaused(ev.matches)); } catch (e) {}
}

bootCatsStage();
