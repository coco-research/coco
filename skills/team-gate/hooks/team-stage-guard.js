#!/usr/bin/env node
'use strict';

// team-stage-guard.js -- PreToolUse and PostToolUse on Bash and Agent.
//
// The PR gate and the spawn gates. A Bash call whose command is git
// push, gh pr create or gh pr merge (after any leading env-var prefix)
// is gated on ship_gate.py check. Every Agent spawn is recorded; one
// whose description or prompt names Layer-2 build work is additionally
// gated on ship_gate.py stage 6. See README.md for the mode switch and
// the substrate facts.

const lib = require('./lib');

const HOOK_NAME = 'team-stage-guard';

// Tokenised on whitespace after skipping any NAME=value env prefix. The
// persistent effect being gated is exactly these three commands, not
// every "gh pr" subcommand.
function matchGatedBashCommand(command) {
  const tokens = String(command || '').trim().split(/\s+/).filter(Boolean);
  let i = 0;
  while (i < tokens.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(tokens[i])) i++;
  const a = tokens[i];
  const b = tokens[i + 1];
  const c = tokens[i + 2];
  if (a === 'git' && b === 'push') return 'git-push';
  if (a === 'gh' && b === 'pr' && c === 'create') return 'pr-create';
  if (a === 'gh' && b === 'pr' && c === 'merge') return 'pr-merge';
  return null;
}

function extractPrUrl(text) {
  const m = /https:\/\/github\.com\/\S+\/pull\/\d+/.exec(String(text || ''));
  return m ? m[0] : null;
}

function decisionFor(mode, wouldDeny) {
  return wouldDeny ? (mode === 'enforce' ? 'deny' : 'would-deny') : 'allow';
}

function firstLine(text) {
  const lines = String(text || '').split('\n').filter((l) => l.trim().length > 0);
  return lines[0] || null;
}

function preBash(payload, raw, repoRoot, toolUseId, mode) {
  const command = payload.tool_input && payload.tool_input.command;
  const matched = matchGatedBashCommand(command);
  if (!matched) return; // ordinary bash: silent, no receipt

  const res = lib.shipGateCheck(repoRoot);
  let decision;
  let reason;
  if (res.exit === 0) {
    decision = 'allow';
    reason = null;
  } else if (res.exit === 1) {
    decision = decisionFor(mode, true);
    reason = firstLine(res.stderr) || 'ship_gate.py check failed';
  } else {
    decision = decisionFor(mode, true);
    reason = 'cannot measure';
  }

  lib.certify(repoRoot, HOOK_NAME, toolUseId, decision, reason, { matched }, raw);
  if (decision === 'deny') process.stdout.write(lib.preToolUseDeny(reason));
}

function preAgent(payload, raw, repoRoot, toolUseId, mode) {
  const input = payload.tool_input || {};
  lib.appendReceipt(repoRoot, 'agent-spawned', {
    description: input.description || null,
    subagent_type: input.subagent_type || null,
    model: input.model || null,
  }, raw);

  const text = `${input.description || ''} ${input.prompt || ''}`.toLowerCase();
  const namesBuildWork = /\bbuild\b|\bimplement\b/.test(text);

  if (namesBuildWork) {
    const res = lib.shipGateStage(repoRoot, 6);
    if (res.exit !== 0) {
      const reason = 'spawning Layer 2 build work before stage 6 is reachable';
      const decision = decisionFor(mode, true);
      lib.certify(repoRoot, HOOK_NAME, toolUseId, decision, reason, { matched: 'agent-build-before-6' }, raw);
      if (decision === 'deny') process.stdout.write(lib.preToolUseDeny(reason));
      return;
    }
  }

  lib.certify(repoRoot, HOOK_NAME, toolUseId, 'allow', null, { matched: 'agent' }, raw);
}

function postBash(payload, raw, repoRoot, runDir, toolUseId) {
  const command = payload.tool_input && payload.tool_input.command;
  const matched = matchGatedBashCommand(command);
  if (!matched) return;

  const certified = lib.findCertified(runDir, toolUseId);
  if (!certified) {
    lib.appendReceipt(repoRoot, 'gate-timeout', { tool_use_id: toolUseId, command }, raw);
    return;
  }

  if (matched === 'pr-create') {
    const stdout = (payload.tool_response && payload.tool_response.stdout) || '';
    const url = extractPrUrl(stdout);
    if (url) {
      lib.appendReceipt(repoRoot, 'pr-opened', { url }, raw);
    }
  }
}

function postAgent(payload, raw, repoRoot, runDir, toolUseId) {
  const certified = lib.findCertified(runDir, toolUseId);
  if (!certified) {
    lib.appendReceipt(repoRoot, 'gate-timeout', { tool_use_id: toolUseId, agent: true }, raw);
    return;
  }
  lib.appendReceipt(repoRoot, 'agent-returned', { tool_use_id: toolUseId }, raw);
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
    try {
      lib.blockReceipt(repoRoot, `${HOOK_NAME}: ${err && err.message ? err.message : err}`, { hook: HOOK_NAME }, raw);
    } catch (e2) { /* nothing more to do */ }
    process.exit(0);
  }

  const toolUseId = payload.tool_use_id;
  const toolName = payload.tool_name;
  const isPost = payload.hook_event_name === 'PostToolUse';

  try {
    if (toolName === 'Bash') {
      if (isPost) postBash(payload, raw, repoRoot, runDir, toolUseId);
      else preBash(payload, raw, repoRoot, toolUseId, mode);
    } else if (toolName === 'Agent') {
      if (isPost) postAgent(payload, raw, repoRoot, runDir, toolUseId);
      else preAgent(payload, raw, repoRoot, toolUseId, mode);
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
