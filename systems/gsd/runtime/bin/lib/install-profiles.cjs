/**
 * Skill Surface Budget Module — single source of truth for which skills/agents
 * are written to the runtime config dirs (ADR-0011).
 *
 * Background: every installed `gsd-*` skill costs eager system-prompt tokens
 * because runtimes (Claude Code, opencode, etc.) enumerate skill descriptions
 * in `<available_skills>` on every turn. With 66 skills + 33 agents GSD alone
 * consumes ~60% of the default 1%-of-context skill-listing budget, causing
 * dropped skills when users stack multiple plugins (#3408).
 *
 * Profile model: three named profiles replace the old minimal/full binary:
 *  - core     — eight skills covering the main project loop (includes surface for ADR-0011 expand contract)
 *  - standard — core + phase management and workspace skills
 *  - full     — all skills (previous default, '*' sentinel)
 * Profiles compose: --profile=core,audit resolves to union(closure(core), closure(audit)).
 * Back-compat aliases: --minimal / --core-only both map to --profile=core.
 *
 * This module owns:
 *  - PROFILES map: named profile → base skill set (or '*' sentinel for full)
 *  - loadSkillsManifest: parse requires: frontmatter from commands/gsd/*.md
 *  - resolveProfile: compute transitive closure of profile base over manifest
 *  - stageSkillsForProfile / stageAgentsForProfile: filesystem staging
 *  - readActiveProfile / writeActiveProfile: .gsd-profile marker persistence
 *  - resolveEffectiveProfile: explicit flag > .gsd-profile marker > full
 *  - mostRestrictiveProfile: resolve multi-runtime disagreement to smallest set
 *
 * Companion module (Phase 2): get-shit-done/bin/lib/surface.cjs owns the
 * runtime /gsd:surface command. It reuses stageSkillsForProfile and
 * stageAgentsForProfile from this module for cluster-level enable/disable
 * without reinstall, persisting state in <runtimeConfigDir>/.gsd-surface.json.
 *
 * Legacy back-compat exports (deprecated, kept for existing callers):
 *  - MINIMAL_SKILL_ALLOWLIST — derived from PROFILES.core
 *  - isMinimalMode(mode) — returns true for 'minimal'
 *  - shouldInstallSkill(name, mode|resolvedProfile) — overloaded
 *  - stageSkillsForMode(srcDir, mode) — wraps stageSkillsForProfile
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { platformWriteSync } = require('./shell-command-projection.cjs');

// ---------------------------------------------------------------------------
// Profile definitions
// ---------------------------------------------------------------------------

/**
 * PROFILES maps profile name → base skill set (array) or '*' sentinel (full).
 *
 * The effective set for any profile is CLOSURE(base, requires: manifest).
 * standard is a superset of core; full is the identity (all skills).
 *
 * Composition: --profile=core,audit resolves to union(closure(core), closure(audit)).
 */
const PROFILES = Object.freeze({
  core: Object.freeze([
    'new-project',
    'discuss-phase',
    'plan-phase',
    'execute-phase',
    'phase',
    'help',
    'update',
    'surface',
  ]),
  standard: Object.freeze([
    // Core loop
    'new-project',
    'discuss-phase',
    'plan-phase',
    'execute-phase',
    'help',
    'update',
    'surface',
    // Phase management (hot nodes from audit — required by 38+ skills)
    'phase',
    'review',
    'config',
    'progress',
    // Workspace / state
    'resume-work',
    'pause-work',
    'workspace',
  ]),
  full: '*',
});

// ---------------------------------------------------------------------------
// Manifest parsing
// ---------------------------------------------------------------------------

/**
 * Parse the requires: field from YAML frontmatter.
 * Handles: "requires: [a, b, c]" (flow style) and absent field.
 * Returns string[] — empty array if no requires: field.
 *
 * No external YAML parser dependency — hand-parse the single line
 * since GSD enforces flow-style arrays for requires:.
 *
 * @param {string} content full file content
 * @returns {string[]}
 */
function parseRequires(content) {
  const fmMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/m);
  if (!fmMatch) return [];
  const fm = fmMatch[1];
  const line = fm.match(/^requires:\s*(.+)$/m);
  if (!line) return [];
  const val = line[1].trim();
  // Flow-style: [a, b, c]
  if (val.startsWith('[') && val.endsWith(']')) {
    const inner = val.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(',').map((s) => s.trim()).filter(Boolean);
  }
  // Single bare value (not currently used, but defensive)
  return val ? [val] : [];
}

/**
 * Parse agent references from a skill file's body text.
 * Scans the full content for `gsd-<stem>` patterns that correspond to
 * real agent files. Returns all unique `gsd-*` stems found in the body.
 *
 * The caller is responsible for filtering by which agents actually exist —
 * this function returns all syntactically valid `gsd-*` matches.
 *
 * @param {string} content full file content
 * @returns {string[]} deduplicated agent stems like ['gsd-planner', 'gsd-executor']
 */
function parseCallsAgents(content) {
  // Match word-boundary gsd-<stem> patterns; stems are lowercase letters and hyphens.
  // We use a regex that matches `gsd-` followed by one or more lowercase-alpha-or-hyphen chars.
  // This catches `gsd-planner`, `gsd-plan-checker`, etc. in prose and code.
  const matches = content.match(/\bgsd-[a-z][a-z-]*/g);
  if (!matches) return [];
  // Deduplicate
  return [...new Set(matches)];
}

/**
 * Load the requires: dependency graph from a commands/gsd directory.
 * Also derives calls_agents for each skill by scanning the body text for
 * `gsd-*` agent name references. Agent stems are stored under the special
 * key `_calls_agents_<stem>` so they don't conflict with skill stems.
 *
 * @param {string} commandsDir absolute path to commands/gsd/
 * @returns {Map<string, string[]>} stem → [required stem, ...] plus _calls_agents_<stem> entries
 */
function loadSkillsManifest(commandsDir) {
  const manifest = new Map();
  if (!fs.existsSync(commandsDir)) return manifest;
  const entries = fs.readdirSync(commandsDir, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isFile()) continue;
    if (!entry.name.endsWith('.md')) continue;
    const stem = entry.name.slice(0, -3);
    try {
      const content = fs.readFileSync(path.join(commandsDir, entry.name), 'utf8');
      manifest.set(stem, parseRequires(content));
      // Derive agent references from body text
      const agentRefs = parseCallsAgents(content);
      manifest.set(`_calls_agents_${stem}`, agentRefs);
    } catch {
      manifest.set(stem, []);
      manifest.set(`_calls_agents_${stem}`, []);
