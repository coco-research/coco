#!/usr/bin/env node
'use strict';

// team-artifact-guard.js -- PreToolUse and PostToolUse on Write, Edit,
// MultiEdit.
//
// Stage order and evidence protection. A write to .team-ship/EVIDENCE.json,
// .team-ship/EVIDENCE.md, anything under .team-ship/gates/, or anything
// under the run directory is always denied: those are written only by
// team-gate scripts, never by the model's own tools. Any other write
// under .team-ship/ is mapped to a manifest stage through
// ship-manifest.json's outputs, and gated on ship_gate.py stage <n>. On
// PostToolUse, the paired certification is looked up, the artifact is
// recorded, and check_artifacts.py stage-output validates its content.
// See README.md for the mode switch and the substrate facts.

const fs = require('fs');
const path = require('path');
const lib = require('./lib');

const HOOK_NAME = 'team-artifact-guard';

function classify(repoRoot, runDir, filePath) {
  const abs = path.isAbsolute(filePath) ? filePath : path.resolve(repoRoot, filePath);
  const rel = lib.relUnderRepo(repoRoot, filePath);
  const underTeamShip = rel === '.team-ship' || rel.startsWith('.team-ship/');
  const underRunDir = lib.isUnder(abs, runDir);
  const alwaysDeny = underRunDir
    || rel === '.team-ship/EVIDENCE.json'
    || rel === '.team-ship/EVIDENCE.md'
    || rel.startsWith('.team-ship/gates/');
  return {
    abs,
    rel,
    gated: underTeamShip || underRunDir,
    alwaysDeny,
  };
}

// Ambiguous outputs (PLAN.md is declared by both stage 3 and stage 5) are
// resolved by trying candidates in ascending order and taking the first
// whose preconditions are already satisfied; otherwise the smallest
// candidate's failing result is reported, since that is the next stage
// the model has not yet completed.
function chooseStage(repoRoot, rel) {
  const manifest = lib.loadManifest();
  const candidates = lib.stagesForOutputPath(manifest, rel);
  if (candidates.length === 0) return null;

  let fallback = null;
  for (const n of candidates) {
    const res = lib.shipGateStage(repoRoot, n);
    if (!fallback) fallback = { n, res };
    if (res.exit === 0) return { n, res };
  }
  return fallback;
}

function decisionFor(mode, wouldDeny) {
  return wouldDeny ? (mode === 'enforce' ? 'deny' : 'would-deny') : 'allow';
}

function runPre(payload, raw, repoRoot, runDir, mode) {
  const toolUseId = payload.tool_use_id;
  const filePath = payload.tool_input && payload.tool_input.file_path;
  if (!filePath) return;

  const info = classify(repoRoot, runDir, filePath);
  if (!info.gated) return; // outside .team-ship and outside the run directory: silent, no receipt

  if (info.alwaysDeny) {
    const reason = 'evidence and gate files are written only by team-gate scripts';
    const decision = decisionFor(mode, true);
    lib.certify(repoRoot, HOOK_NAME, toolUseId, decision, reason, { guard: 'always-deny', path: info.rel }, raw);
    if (decision === 'deny') process.stdout.write(lib.preToolUseDeny(reason));
    return;
  }

  const chosen = chooseStage(repoRoot, info.rel);
  if (!chosen) return; // not a declared manifest output: ungoverned, silent

  const { n, res } = chosen;
  let decision;
  let reason;
  if (res.exit === 0) {
    decision = 'allow';
    reason = null;
  } else if (res.exit === 1) {
    decision = decisionFor(mode, true);
    reason = (res.json && res.json.reason) || 'stage precondition not met';
  } else {
    decision = decisionFor(mode, true);
    reason = 'cannot measure stage preconditions';
  }

  lib.certify(repoRoot, HOOK_NAME, toolUseId, decision, reason, { guard: 'stage', stage: n, path: info.rel }, raw);
  if (decision === 'deny') process.stdout.write(lib.preToolUseDeny(reason));
}

function runPost(payload, raw, repoRoot, runDir) {
  const toolUseId = payload.tool_use_id;
  const filePath = payload.tool_input && payload.tool_input.file_path;
  if (!filePath) return;

  const info = classify(repoRoot, runDir, filePath);
  if (!info.gated) return;

  const certified = lib.findCertified(runDir, toolUseId);
  if (!certified) {
    lib.appendReceipt(repoRoot, 'gate-timeout', { tool_use_id: toolUseId, path: info.rel }, raw);
    return;
  }

  if (certified.detail.guard === 'always-deny') return; // nothing further to record for these paths

  const n = certified.detail.stage;

  let sha256;
  let lines;
  try {
    sha256 = lib.sha256File(info.abs);
    lines = lib.countLines(fs.readFileSync(info.abs, 'utf8'));
  } catch (e) {
    return; // the write did not leave a readable file; nothing to record
  }

  lib.appendReceipt(repoRoot, 'artifact-written', { path: info.rel, sha256, lines, stage: n }, raw);

  if (!lib.hasStageOpened(runDir, n)) {
    lib.appendReceipt(repoRoot, 'stage-opened', { stage: n }, raw);
  }

  const out = lib.checkArtifactsStageOutput(repoRoot, n, info.rel);
  if (out.exit !== 0) {
    const reason = (out.stderr || '').trim() || `check_artifacts.py stage-output exited ${out.exit}`;
    lib.blockReceipt(repoRoot, reason, { path: info.rel, hook: HOOK_NAME }, raw);
  }
}

function main() {
  const raw = lib.readStdin();

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (e) {
    process.exit(0);
  }

  const cwd = payload.cwd;
  if (!cwd) process.exit(0);

  const found = lib.findRun(cwd);
  if (!found) process.exit(0);

  const { repoRoot, runDir } = found;

  let mode;
  try {
    mode = lib.hooksMode(runDir);
  } catch (err) {
    // Cannot read the state directory. We cannot confirm enforce mode
    // either (that is exactly what failed to read), so we stay silent
    // here and let the block receipt fail the run at aggregation.
    try {
      lib.blockReceipt(repoRoot, `${HOOK_NAME}: ${err && err.message ? err.message : err}`, { hook: HOOK_NAME }, raw);
    } catch (e2) { /* nothing more to do */ }
    process.exit(0);
  }

  try {
    if (payload.hook_event_name === 'PostToolUse') {
      runPost(payload, raw, repoRoot, runDir);
    } else {
      runPre(payload, raw, repoRoot, runDir, mode);
    }
    process.exit(0);
  } catch (err) {
    try {
      lib.blockReceipt(repoRoot, `${HOOK_NAME}: ${err && err.message ? err.message : err}`, { hook: HOOK_NAME }, raw);
    } catch (e2) { /* nothing more to do */ }
    process.exit(0);
  }
}

main();
