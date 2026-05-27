// ─────────────────────── Setup mockup — step navigation + scan animation ───────────────────────

const TOTAL_STEPS = 5;
let currentStep = 1;
let scanRunning = false;
let scanTimer = null;

function goto(n) {
  if (n < 1 || n > TOTAL_STEPS) return;
  document.querySelectorAll('.setup-step').forEach(s => s.classList.remove('active'));
  document.getElementById('step-' + n).classList.add('active');

  document.querySelectorAll('.setup-step-pill').forEach(p => {
    const num = +p.dataset.step;
    p.classList.toggle('is-active', num === n);
    p.classList.toggle('is-done', num < n);
  });

  currentStep = n;
  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (n === 4 && !scanRunning) startScan();
}

// Theme picker
document.querySelectorAll('.theme-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('is-selected'));
    btn.classList.add('is-selected');
  });
});

// Test poll button (Step 2)
document.getElementById('btn-test-poll')?.addEventListener('click', () => {
  const status = document.getElementById('email-status');
  status.innerHTML = '<span class="status-dot warning"></span> Polling…';
  setTimeout(() => {
    status.innerHTML = '<span class="status-dot success"></span> <b>Connected</b> · 24 unread · last poll just now';
  }, 900);
});

// Chip remove (Step 3)
document.querySelectorAll('.chip.removable .x').forEach(x => {
  x.addEventListener('click', () => x.closest('.chip').remove());
});
document.querySelector('.chip-input-text')?.addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target.value.trim()) {
    e.preventDefault();
    const chip = document.createElement('span');
    chip.className = 'chip removable';
    chip.textContent = e.target.value.trim() + ' ';
    const closeBtn = document.createElement('span');
    closeBtn.className = 'x';
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', () => chip.remove());
    chip.appendChild(closeBtn);
    e.target.parentNode.insertBefore(chip, e.target);
    e.target.value = '';
  }
});

// Step 4 — simulated scan
function startScan() {
  scanRunning = true;
  const bar = document.getElementById('scan-bar');
  const files = document.getElementById('scan-files');
  const entities = document.getElementById('scan-entities');
  const articles = document.getElementById('scan-articles');
  const cost = document.getElementById('scan-cost');
  const events = document.getElementById('scan-events');
  const doneCard = document.getElementById('scan-done');

  let pct = 0;
  let fileCount = 0;
  let entityCount = 0;
  let articleCount = 0;
  let costVal = 0;

  const eventQueue = [
    { at: 12, text: 'chief-of-staff · briefing squad with workstream context' },
    { at: 22, text: 'product-manager · scanning Confluence pages → PRD drafts' },
    { at: 34, text: 'scribe · 1 article queued: <span class="mono">AB1 Q2 reconciliation status</span>' },
    { at: 48, text: 'extract-entities · 17 people, 12 systems, 8 decisions detected' },
    { at: 60, text: 'chief-of-staff · routing 4 decisions to queue.json' },
    { at: 76, text: 'scribe · 4 articles published to project_brain.db' },
    { at: 88, text: 'qa-reviewer · 0 regressions detected · clean' }
  ];
  const emitted = new Set();

  scanTimer = setInterval(() => {
    pct = Math.min(100, pct + (Math.random() * 2 + 0.6));
    fileCount = Math.floor((pct / 100) * 231);
    entityCount = Math.floor((pct / 100) * 47);
    articleCount = Math.floor((pct / 100) * 4);
    costVal = +((pct / 100) * 0.43).toFixed(2);

    bar.style.width = pct.toFixed(1) + '%';
    files.textContent = fileCount;
    entities.textContent = entityCount;
    articles.textContent = articleCount;
    cost.textContent = costVal.toFixed(2);

    eventQueue.forEach((e, i) => {
      if (pct >= e.at && !emitted.has(i)) {
        emitted.add(i);
        const el = document.createElement('div');
        el.className = 'evt evt-done';
        const dot = document.createElement('span');
        dot.className = 'evt-dot';
        const text = document.createElement('span');
        text.className = 'evt-text';
        text.textContent = e.text;
        const time = document.createElement('span');
        time.className = 'evt-time';
        time.textContent = `${Math.floor(pct/8)}:${String(Math.floor(pct/2) % 60).padStart(2, '0')}`;
        el.appendChild(dot);
        el.appendChild(text);
        el.appendChild(time);
        events.appendChild(el);
        events.scrollTop = events.scrollHeight;
      }
    });

    if (pct >= 100) {
      clearInterval(scanTimer);
      scanRunning = false;
      doneCard.classList.add('is-visible');

      const running = events.querySelector('.evt-running');
      if (running) {
        running.classList.remove('evt-running');
        running.classList.add('evt-done');
        running.querySelector('.evt-text').textContent = 'folder_scanner · 231 / 231 files complete';
      }
    }
  }, 220);
}

// Skip all → straight to done
document.getElementById('btn-skip-all')?.addEventListener('click', () => finish());

function finish() {
  document.getElementById('done-overlay').classList.add('is-visible');
}

// Enter key advances
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.target.matches('input, textarea, select')) {
    if (currentStep < TOTAL_STEPS) goto(currentStep + 1);
    else finish();
  }
});

// Allow clicking the progress pills to jump (within-mockup convenience)
document.querySelectorAll('.setup-step-pill').forEach(p => {
  p.addEventListener('click', () => goto(+p.dataset.step));
});
