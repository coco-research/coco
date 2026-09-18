#!/usr/bin/env node
'use strict';

// team-stop-guard.js -- Stop.
//
// A run may not end silently mid-pipeline. Allows immediately on
// re-entry (stop_hook_active) or while background tasks are pending.
// Otherwise blocks once when a block or gate-timeout receipt already
// exists, or when no PR has opened and the highest stage-opened receipt
// is below stage 14, naming the remaining stages via ship_gate.py's own
// stage 14 query (a pure query, no side effects). See README.md for the
// mode switch and the substrate facts.

const lib = require('./lib');

const HOOK_NAME = 'team-stop-guard';

function remainingStages(repoRoot) {
  const res = lib.shipGateStage(repoRoot, 14);
  if (res.json) {
    const items = [].concat(res.json.missing || [], res.json.failing || []);
    if (items.length) return items;
  }
  return ['unknown'];
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
    mode = lib.guardMode(runDir, 'stop');
  } catch (err) {
    try {
      lib.blockReceipt(repoRoot, `${HOOK_NAME}: ${err && err.message ? err.message : err}`, { hook: HOOK_NAME }, raw);
    } catch (e2) { /* nothing more to do */ }
    process.exit(0);
  }

  try {
    let decision;
    let reason;

    if (payload.stop_hook_active === true) {
      decision = 'allow';
      reason = 'stop_hook_active is true: re-entry';
    } else if (Array.isArray(payload.background_tasks) && payload.background_tasks.length > 0) {
      decision = 'allow';
      reason = 'background tasks pending';
    } else {
      const receipts = lib.readReceipts(runDir);
      const blocks = receipts.filter((r) => r.kind === 'block');
      const timeouts = receipts.filter((r) => r.kind === 'gate-timeout');
      const prOpened = receipts.some((r) => r.kind === 'pr-opened');
      let maxStage = 0;
      for (const r of receipts) {
        if (r.kind === 'stage-opened' && r.detail && typeof r.detail.stage === 'number') {
          maxStage = Math.max(maxStage, r.detail.stage);
        }
      }

      if (blocks.length > 0 || timeouts.length > 0) {
        const latest = blocks.concat(timeouts).sort((x, y) => (x.seq || 0) - (y.seq || 0)).pop();
        decision = 'block';
        reason = (latest.detail && latest.detail.reason)
          || (latest.kind === 'gate-timeout' ? `gate-timeout: ${latest.detail.tool_use_id || 'unknown'}` : 'run blocked');
      } else if (prOpened || maxStage >= 14) {
        decision = 'allow';
        reason = null;
      } else {
        const runId = lib.readRunId(runDir);
        const remaining = remainingStages(repoRoot);
        decision = 'block';
        reason = `run ${runId} is at stage ${maxStage}; remaining: ${remaining.join(', ')}; run ship_gate.py check or record an override`;
      }
    }

    const recorded = decision === 'block' ? (mode === 'enforce' ? 'block' : 'would-block') : 'allow';
    lib.appendReceipt(repoRoot, 'stop-checked', { decision: recorded, reason: reason || null }, raw);

    if (decision === 'block' && mode === 'enforce') {
      process.stdout.write(lib.stopBlock(reason));
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
