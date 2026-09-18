'use strict';

// lib.js -- shared helpers for the four team-gate hooks. Node, stdlib only.
//
// Run resolution walks up from a cwd for .team-ship/RUN exactly as
// gate_state.find_run does, and returns the directory that held the
// marker (the repository root) alongside the run directory under
// TEAM_STATE_ROOT (or ~/.team/runs). Receipts are appended only by
// shelling out to gate_state.py's own "receipt" CLI with the hook
// payload on stdin, so there is exactly one writer of receipts.jsonl.
//
// See README.md for the mode switch (observe vs enforce) and the
// substrate facts every hook in this directory rests on.

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

const SCRIPTS_DIR = path.join(__dirname, '..', 'scripts');
const GATE_STATE_PY = path.join(SCRIPTS_DIR, 'gate_state.py');
const SHIP_GATE_PY = path.join(SCRIPTS_DIR, 'ship_gate.py');
const CHECK_ARTIFACTS_PY = path.join(SCRIPTS_DIR, 'check_artifacts.py');
const MANIFEST_PATH = path.join(__dirname, '..', 'references', 'ship-manifest.json');

// Reads all of stdin synchronously, blocking until EOF. No timer: a slow
// or large payload is read in full, never abandoned early.
function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (e) {
    return '';
  }
}

function stateRoot() {
  const env = process.env.TEAM_STATE_ROOT;
  if (env) return env;
  return path.join(os.homedir(), '.team', 'runs');
}

function isDir(p) {
  try { return fs.statSync(p).isDirectory(); } catch (e) { return false; }
}

function isFile(p) {
  try { return fs.statSync(p).isFile(); } catch (e) { return false; }
}

// Walk up from cwd for .team-ship/RUN, matching gate_state.find_run's own
// walk. Returns {repoRoot, runDir, runId} or null when no run is active.
// repoRoot is the directory that held the marker, the same directory
// gate_state.start_run wrote .team-ship/RUN under.
function findRun(cwd) {
  let current = path.resolve(cwd);
  for (;;) {
    const marker = path.join(current, '.team-ship', 'RUN');
    if (isFile(marker)) {
      let runId = '';
      try { runId = fs.readFileSync(marker, 'utf8').trim(); } catch (e) { runId = ''; }
      if (runId) {
        const runDir = path.join(stateRoot(), runId);
        if (isDir(runDir)) {
          return { repoRoot: current, runDir, runId };
        }
      }
    }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

// run.json's "flags" field is the raw positional argument list
// gate_state.py start received (for example ["hooks=enforce"]), not an
// object keyed by name. Defaults to observe when absent or malformed.
// Throws if run.json cannot be read or parsed, per the fail-closed rule:
// a hook that cannot read the state directory must not silently assume
// observe.
function hooksMode(runDir) {
  const raw = fs.readFileSync(path.join(runDir, 'run.json'), 'utf8');
  const runObj = JSON.parse(raw);
  const flags = runObj.flags;
  if (Array.isArray(flags)) {
    for (const f of flags) {
      const m = /^hooks=(observe|enforce)$/.exec(String(f));
      if (m) return m[1];
    }
    return 'observe';
  }
  if (flags && typeof flags === 'object' && flags.hooks) {
    return flags.hooks === 'enforce' ? 'enforce' : 'observe';
  }
  return 'observe';
}

function readRunId(runDir) {
  try {
    const raw = fs.readFileSync(path.join(runDir, 'run.json'), 'utf8');
    return JSON.parse(raw).run_id || path.basename(runDir);
  } catch (e) {
    return path.basename(runDir);
  }
}

// The single writer of receipts.jsonl. cwd must be inside the repository
// (repoRoot or a descendant) so gate_state.py's own find_run(Path.cwd())
// resolves the same run this hook already found.
function appendReceipt(repoRoot, kind, detail, payloadText) {
  const res = spawnSync('python3', [
    GATE_STATE_PY, 'receipt', kind, JSON.stringify(detail), '--hook-payload', '-',
  ], { cwd: repoRoot, input: payloadText || '', encoding: 'utf8' });
  if (res.status !== 0) {
    throw new Error(`gate_state receipt ${kind} exit ${res.status}: ${(res.stderr || '').trim()}`);
  }
  return res.stdout;
}

function readReceipts(runDir) {
  const p = path.join(runDir, 'receipts.jsonl');
  if (!isFile(p)) return [];
  const raw = fs.readFileSync(p, 'utf8');
  const out = [];
  for (const line of raw.split('\n')) {
    if (!line.trim()) continue;
    try { out.push(JSON.parse(line)); } catch (e) { /* chain integrity is gate_state's job, not ours */ }
  }
  return out;
}

function findCertified(runDir, toolUseId) {
  let latest = null;
  for (const r of readReceipts(runDir)) {
    if (r.kind === 'certified' && r.detail && r.detail.tool_use_id === toolUseId) {
      if (!latest || (r.seq || 0) > (latest.seq || 0)) latest = r;
    }
  }
  return latest;
}

function hasStageOpened(runDir, stage) {
  return readReceipts(runDir).some((r) => r.kind === 'stage-opened' && r.detail && r.detail.stage === stage);
}

function loadManifest() {
  return JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
}

// Every numeric manifest stage whose outputs list names relPath,
// ascending. PLAN.md is a declared output of both stage 3 and stage 5;
// callers resolve the ambiguity by trying candidates in order.
function stagesForOutputPath(manifest, relPath) {
  const stages = manifest.stages || {};
  const result = [];
  for (const key of Object.keys(stages)) {
    const n = Number(key);
    if (!Number.isInteger(n)) continue; // skips the non-numeric "approval" key
    const outputs = stages[key].outputs || [];
    if (outputs.some((o) => o.path === relPath)) result.push(n);
  }
  return result.sort((a, b) => a - b);
}

function runPython(args, cwd) {
  const res = spawnSync('python3', args, { cwd, encoding: 'utf8' });
  let json = null;
  try { json = JSON.parse((res.stdout || '').trim()); } catch (e) { /* not JSON output */ }
  return { exit: res.status, stdout: res.stdout || '', stderr: res.stderr || '', json };
}

function shipGateStage(repoRoot, n) {
  return runPython([SHIP_GATE_PY, 'stage', String(n), '--repo-root', repoRoot], repoRoot);
}

function shipGateCheck(repoRoot) {
  return runPython([SHIP_GATE_PY, 'check', '--repo-root', repoRoot], repoRoot);
}

function checkArtifactsStageOutput(repoRoot, stage, relPath) {
  return runPython([CHECK_ARTIFACTS_PY, 'stage-output', String(stage), relPath, '--repo-root', repoRoot], repoRoot);
}

// repoRoot-relative, POSIX-separated path for filePath, lexical (no
// symlink resolution here; check_artifacts.py's own validation already
// covers escapes when it runs).
function relUnderRepo(repoRoot, filePath) {
  const abs = path.isAbsolute(filePath) ? filePath : path.resolve(repoRoot, filePath);
  const rel = path.relative(repoRoot, abs);
  return rel.split(path.sep).join('/');
}

function isUnder(absPath, baseDir) {
  const rel = path.relative(baseDir, absPath);
  return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
}

function sha256File(absPath) {
  return crypto.createHash('sha256').update(fs.readFileSync(absPath)).digest('hex');
}

function countLines(text) {
  if (text === '') return 0;
  return text.split('\n').length - (text.endsWith('\n') ? 1 : 0);
}

// The PreToolUse deny form, byte for byte.
function preToolUseDeny(reason) {
  return JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason,
    },
  });
}

// The Stop block form, byte for byte.
function stopBlock(reason) {
  return JSON.stringify({ decision: 'block', reason });
}

// The certified receipt every gating PreToolUse decision appends, keyed
// by tool_use_id so the paired PostToolUse hook can look it up.
function certify(repoRoot, hookName, toolUseId, decision, reason, extra, payloadText) {
  const detail = Object.assign(
    { hook: hookName, tool_use_id: toolUseId, decision, reason: reason || null },
    extra || {},
  );
  appendReceipt(repoRoot, 'certified', detail, payloadText);
}

function blockReceipt(repoRoot, reason, extra, payloadText) {
  appendReceipt(repoRoot, 'block', Object.assign({ reason: String(reason) }, extra || {}), payloadText);
}

module.exports = {
  GATE_STATE_PY,
  SHIP_GATE_PY,
  CHECK_ARTIFACTS_PY,
  MANIFEST_PATH,
  readStdin,
  stateRoot,
  findRun,
  hooksMode,
  readRunId,
  appendReceipt,
  readReceipts,
  findCertified,
  hasStageOpened,
  loadManifest,
  stagesForOutputPath,
  shipGateStage,
  shipGateCheck,
  checkArtifactsStageOutput,
  relUnderRepo,
  isUnder,
  sha256File,
  countLines,
  preToolUseDeny,
  stopBlock,
  certify,
  blockReceipt,
};
