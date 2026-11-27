// 3D Three.js banner stage for /aloomannu/ and deterministic repo banner exports (?banner=readme|social).
// ES module: loaded with type="module"; top-level names are module-scoped.
// Renders two coded black-and-white cats on a cream ledge, flowing signal lines, and "ow ow" / "meh" bubbles.
// Three.js and the cat models load with dynamic import() inside bootCatsStage(), so a missing vendored
// module or WebGL context falls back to the pre-rendered banner instead of a dead module graph.

function drawBubbleCanvas(canvas, text, textAlpha, tailSide) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const bx = 26, by = 22, bw = w - 52, bh = h - 74, r = bh * 0.48;

  // Opaque navy bubble with pale text: #dce6f7 on #0d2247 is about 12:1, so both bubbles stay legible
  // at every frame of the call-and-answer loop (only the outline pulses).
  ctx.save();
  ctx.strokeStyle = `rgba(220, 230, 247, ${(0.62 + 0.38 * Math.min(1, Math.max(0, textAlpha))).toFixed(3)})`;
  ctx.fillStyle = '#0d2247';
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
    ctx.fillStyle = '#dce6f7';
    ctx.font = '500 50px "Archivo", ui-sans-serif, system-ui, -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, bx + bw * 0.5, by + bh * 0.52);
  }
  ctx.restore();
}

function makeBubbleActor(THREE, text, tailSide, pos, size) {
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

function buildFlowLines(THREE) {
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

const smoothstep = (u) => u * u * (3 - 2 * u);

function smoothWindow(t, start, riseEnd, holdEnd, fallEnd) {
  if (t <= start || t >= fallEnd) return 0;
  if (t < riseEnd) return smoothstep((t - start) / (riseEnd - start));
  if (t <= holdEnd) return 1;
  return smoothstep(1 - (t - holdEnd) / (fallEnd - holdEnd));
}

const CAMERA_VIEWS = {
  readme: { fov: 25.8, pos: [0.0, -0.05, 13.55], lookAt: [0.0, -0.11, 0] },
  social: { fov: 27.2, pos: [0.0, -0.04, 13.30], lookAt: [0.0, -0.10, 0] },
  narrow: { fov: 34,   pos: [1.98, 0.62, 18.6],  lookAt: [1.98, -0.28, 0] },
  wide:   { fov: 28,   pos: [0.0, -0.04, 13.2],  lookAt: [0.0, -0.10, 0] },
};

function setLids(cat, blinkOffset = 0) {
  cat.lids.forEach((lid, idx) => {
    const sign = idx === 0 ? 1 : -1;
    lid.rotation.set(cat.rest.lidRestX + blinkOffset, 0, sign * cat.rest.lidTiltZ);
  });
}

function resetCatPose(cat) {
  cat.headPivot.position.y = cat.rest.headY;
  cat.headPivot.rotation.set(cat.baseRot.x, cat.baseRot.y, cat.baseRot.z);
  cat.chin.position.y = cat.rest.chinY;
  if (cat.rest.earRRestZ !== undefined) cat.earR.rotation.z = cat.rest.earRRestZ;
  if (cat.rest.earLRestZ !== undefined) cat.earL.rotation.z = cat.rest.earLRestZ;
  setLids(cat, 0);
}

function setToggleLabel(btn, label) {
  btn.textContent = label;
  btn.removeAttribute('aria-pressed');
}

async function bootCatsStage() {
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
  const ownStage = document.documentElement.hasAttribute('data-own-stage');
  const navMotionBtns = ownStage ? Array.from(document.querySelectorAll('[data-motion-toggle]')) : [];
  const allToggleBtns = [toggleBtn, ...navMotionBtns].filter(Boolean);
  const useFallback = () => {
    if (stageEl) stageEl.classList.add('aloo-webgl-fallback');
    allToggleBtns.forEach((btn) => { btn.hidden = true; });
  };
  let reducedMq = null;
  try { reducedMq = matchMedia('(prefers-reduced-motion: reduce)'); } catch (e) { /* matchMedia unsupported */ }

  let renderer = null;
  let resize, renderFrame, syncControl, setPaused, stopLoop, startLoop, readStoredPause;
  let paused = false, raf = 0, t0 = 0, contextLost = false, inView = true;

  try {
    const [THREE, models] = await Promise.all([import('three'), import('./aloo-cats-models.js')]);
    const { buildCreamLedge, buildLeftCat, buildRightCat } = models;
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'low-power' });
    if (!renderer.getContext()) throw new Error('no webgl context');

    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.06;
    renderer.setClearColor(0x0c1e36, 1);

    const scene = new THREE.Scene();
    const bgCanvas = document.createElement('canvas');
    bgCanvas.width = 512; bgCanvas.height = 256;
    const bctx = bgCanvas.getContext('2d');
    if (bctx) {
      const bgGrad = bctx.createRadialGradient(340, 125, 30, 260, 130, 340);
      bgGrad.addColorStop(0, '#142d4e');
      bgGrad.addColorStop(0.56, '#0c1e36');
      bgGrad.addColorStop(1, '#071325');
      bctx.fillStyle = bgGrad; bctx.fillRect(0, 0, 512, 256);
    }
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
    const flows = buildFlowLines(THREE);
    const callBubble = makeBubbleActor(THREE, 'ow ow', 'right', [0.16, 0.88, 0.85], [1.48, 0.82]);
    const replyBubble = makeBubbleActor(THREE, 'meh', 'left', [4.24, 1.72, 0.85], [1.62, 0.88]);

    const stageGroup = new THREE.Group();
    stageGroup.add(ledge, flows.group, leftCat.root, rightCat.root, callBubble.mesh, replyBubble.mesh);
    scene.add(stageGroup);

    resize = () => {
      if (contextLost) return;
      const rect = (stageEl || canvas).getBoundingClientRect();
      const w = Math.max(280, Math.round(rect.width || window.innerWidth));
      const h = Math.max(240, Math.round(rect.height || 520));
      const dpr = isBannerExport ? 1 : Math.min(window.devicePixelRatio || 1, 2);
      renderer.setPixelRatio(dpr);
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      const viewKey = isBannerExport ? bannerMode : (w <= 760 ? 'narrow' : 'wide');
      const view = CAMERA_VIEWS[viewKey];
      camera.fov = view.fov;
      camera.position.set(...view.pos);
      camera.lookAt(...view.lookAt);
      camera.updateProjectionMatrix();
    };

    renderFrame = (t, isStatic) => {
      if (contextLost) return;
      if (isStatic) {
        resetCatPose(leftCat);
        resetCatPose(rightCat);
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

      leftCat.headPivot.position.y = leftCat.rest.headY + Math.sin(t * 1.8) * 0.012;
      rightCat.headPivot.position.y = rightCat.rest.headY + Math.sin(t * 1.55 + 1.1) * 0.014;

      leftCat.headPivot.rotation.set(
        leftCat.baseRot.x - callW * 0.08 + Math.sin(t * 0.9) * 0.015,
        leftCat.baseRot.y + callW * 0.05,
        leftCat.baseRot.z,
      );
      leftCat.chin.position.y = leftCat.rest.chinY - Math.max(0, Math.sin(t * 9.0)) * callW * 0.024;
      leftCat.earR.rotation.z = leftCat.rest.earRRestZ - Math.pow(Math.max(0, Math.sin(t * 2.3)), 8) * 0.14;

      rightCat.headPivot.rotation.set(
        rightCat.baseRot.x + replyW * 0.04 + Math.cos(t * 0.8) * 0.014,
        rightCat.baseRot.y - replyW * 0.14,
        rightCat.baseRot.z - replyW * 0.04,
      );
      rightCat.chin.position.y = rightCat.rest.chinY - replyW * 0.022;
      rightCat.earL.rotation.z = rightCat.rest.earLRestZ + Math.pow(Math.max(0, Math.sin(t * 1.9 + 0.8)), 10) * 0.16;

      const blinkR = Math.max(smoothWindow(cycle, 4.05, 4.16, 4.24, 4.38), smoothWindow(cycle, 6.8, 6.9, 6.96, 7.08));
      setLids(rightCat, blinkR * 1.24);
      const blinkL = smoothWindow(cycle, 1.75, 1.86, 1.94, 2.08);
      setLids(leftCat, blinkL * 0.78);

      flows.animate(t);
      renderer.render(scene, camera);
    };

    // Dedicated per-page key scoped to this module so it never drifts from product-scene.js.
    const pauseKey = 'aloo-cats-pause:' + location.pathname;
    readStoredPause = () => { try { return sessionStorage.getItem(pauseKey); } catch (e) { /* private mode / storage blocked */ return null; } };
    const stored = readStoredPause();
    paused = isBannerExport || stored === '1' || (stored === null && Boolean(reducedMq && reducedMq.matches));
    t0 = performance.now();

    // Label swaps text only; aria-pressed would double-announce the state (WCAG 2.2.2 Pause/Play control).
    syncControl = () => {
      if (toggleBtn) setToggleLabel(toggleBtn, paused ? 'Play motion' : 'Pause motion');
      navMotionBtns.forEach((btn) => setToggleLabel(btn, paused ? 'Play 3D' : 'Pause 3D'));
    };
    const canAnimate = () => !paused && !document.hidden && inView && !contextLost;
    const loop = (now) => {
      if (!canAnimate()) { raf = 0; return; }
      renderFrame((now - t0) * 0.001, false);
      raf = requestAnimationFrame(loop);
    };
    stopLoop = () => {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
    };
    startLoop = () => {
      if (!canAnimate() || raf) return;
      t0 = performance.now();
      raf = requestAnimationFrame(loop);
    };
    const writeStoredPause = (val) => { try { sessionStorage.setItem(pauseKey, val ? '1' : '0'); } catch (e) { /* private mode: this tab only */ } };
    setPaused = (next, persist = false) => {
      if (contextLost) return;
      paused = next;
      if (persist) writeStoredPause(paused);
      syncControl();
      stopLoop();
      if (paused) renderFrame(0, true);
      else startLoop();
    };

    resize();
    syncControl();
    // Run the initial render synchronously inside the start try so any build/shader/render throw triggers fallback.
    renderFrame(0, paused);
  } catch (err) {
    console.warn('aloo-cats: fallback', err);
    useFallback();
    if (renderer) {
      try { renderer.dispose(); } catch (disposeErr) { /* ignore dispose failure on broken context */ }
    }
    return;
  }

  // Explicit readiness signal consumed by offline banner export scripts.
  const READY_FLAG = '__ALOO_BANNER_READY';
  const markReady = () => {
    window[READY_FLAG] = true;
    document.documentElement.dataset.alooBannerReady = '1';
  };
  const redrawIfPaused = () => {
    if (contextLost) return;
    resize();
    if (paused) renderFrame(0, true);
  };

  if (paused) {
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => {
        redrawIfPaused();
        markReady();
      }).catch(() => { /* font readiness fallback already rendered */ markReady(); });
    } else {
      markReady();
    }
  } else {
    markReady();
    startLoop();
  }

  window.addEventListener('resize', redrawIfPaused, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (paused || contextLost) return;
    if (document.hidden) stopLoop();
    else startLoop();
  });
  if (!isBannerExport && typeof IntersectionObserver !== 'undefined') {
    const io = new IntersectionObserver((entries) => {
      if (contextLost) return;
      inView = entries.some((entry) => entry.isIntersecting);
      if (!inView) stopLoop();
      else startLoop();
    }, { threshold: 0.01 });
    io.observe(stageEl || canvas);
  }
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    contextLost = true;
    stopLoop();
    useFallback();
    markReady();
  });
  const onToggleClick = () => setPaused(!paused, true);
  allToggleBtns.forEach((btn) => btn.addEventListener('click', onToggleClick));
  if (reducedMq) {
    try { reducedMq.addEventListener('change', (ev) => { if (readStoredPause() === null) setPaused(ev.matches); }); } catch (e) { /* matchMedia listener unsupported */ }
  }
}

bootCatsStage().catch((err) => { console.warn('aloo-cats: fallback', err); });
