/**
 * State — STATE.md operations and progression engine
 */

const fs = require('fs');
const path = require('path');
const { escapeRegex, loadConfig, getMilestoneInfo, getMilestonePhaseFilter, output, error } = require('./core.cjs');
const { platformWriteSync, platformReadSync, platformEnsureDir } = require('./shell-command-projection.cjs');
const { planningDir, planningPaths } = require('./planning-workspace.cjs');
const { extractFrontmatter, reconstructFrontmatter } = require('./frontmatter.cjs');
const scanPhasePlans = require('./plan-scan.cjs');
const {
  computeProgressPercent,
  normalizeProgressNumbers,
  normalizeStateStatus,
  shouldPreserveExistingProgress,
  stateExtractField,
  stateReplaceField,
} = require('./state-document.cjs');

// Cache disk scan results from buildStateFrontmatter per cwd per process (#1967).
// Avoids re-reading N+1 directories on every state write when the phase structure
// hasn't changed within the same gsd-tools invocation.
const _diskScanCache = new Map();

/** Shorthand — every state command needs this path */
function getStatePath(cwd) {
  return planningPaths(cwd).state;
}

// Track all lock files held by this process so they can be removed on exit.
// process.on('exit') fires even on process.exit(1), unlike try/finally which is
// skipped when error() calls process.exit(1) inside a locked region (#1916).
const _heldStateLocks = new Set();
process.on('exit', () => {
  for (const lockPath of _heldStateLocks) {
    try { require('fs').unlinkSync(lockPath); } catch { /* already gone */ }
  }
});

function cmdStateLoad(cwd, raw) {
  const config = loadConfig(cwd);
  const planDir = planningPaths(cwd).planning;

  const stateRaw = platformReadSync(path.join(planDir, 'STATE.md')) || '';

  const configExists = fs.existsSync(path.join(planDir, 'config.json'));
  const roadmapExists = fs.existsSync(path.join(planDir, 'ROADMAP.md'));
  const stateExists = stateRaw.length > 0;

  const result = {
    config,
    state_raw: stateRaw,
    state_exists: stateExists,
    roadmap_exists: roadmapExists,
    config_exists: configExists,
  };

  // For --raw, output a condensed key=value format
  if (raw) {
    const c = config;
    const lines = [
      `model_profile=${c.model_profile}`,
      `commit_docs=${c.commit_docs}`,
      `branching_strategy=${c.branching_strategy}`,
      `phase_branch_template=${c.phase_branch_template}`,
      `milestone_branch_template=${c.milestone_branch_template}`,
      `parallelization=${c.parallelization}`,
      `research=${c.research}`,
      `plan_checker=${c.plan_checker}`,
      `verifier=${c.verifier}`,
      `config_exists=${configExists}`,
      `roadmap_exists=${roadmapExists}`,
      `state_exists=${stateExists}`,
    ];
    process.stdout.write(lines.join('\n'));
    process.exit(0);
  }

  output(result);
}

function cmdStateGet(cwd, section, raw) {
  const statePath = planningPaths(cwd).state;
  const content = platformReadSync(statePath);
  if (content === null) {
    error('STATE.md not found');
    return;
  }
  {

    if (!section) {
      output({ content }, raw, content);
      return;
    }

    // Try to find markdown section or field
    const fieldEscaped = escapeRegex(section);

    // Check for **field:** value (bold format)
    const boldPattern = new RegExp(`\\*\\*${fieldEscaped}:\\*\\*\\s*(.*)`, 'i');
    const boldMatch = content.match(boldPattern);
    if (boldMatch) {
      output({ [section]: boldMatch[1].trim() }, raw, boldMatch[1].trim());
      return;
    }

    // Check for field: value (plain format)
    const plainPattern = new RegExp(`^${fieldEscaped}:\\s*(.*)`, 'im');
    const plainMatch = content.match(plainPattern);
    if (plainMatch) {
      output({ [section]: plainMatch[1].trim() }, raw, plainMatch[1].trim());
      return;
    }

    // Check for ## Section
    const sectionPattern = new RegExp(`##\\s*${fieldEscaped}\\s*\n([\\s\\S]*?)(?=\\n##|$)`, 'i');
    const sectionMatch = content.match(sectionPattern);
    if (sectionMatch) {
      output({ [section]: sectionMatch[1].trim() }, raw, sectionMatch[1].trim());
      return;
