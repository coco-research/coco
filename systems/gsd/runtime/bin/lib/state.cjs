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
    }

    output({ error: `Section or field "${section}" not found` }, raw, '');
  }
}

function readTextArgOrFile(cwd, value, filePath, label) {
  if (!filePath) return value;

  // Path traversal guard: ensure file resolves within project directory
  const { validatePath } = require('./security.cjs');
  const pathCheck = validatePath(filePath, cwd, { allowAbsolute: true });
  if (!pathCheck.safe) {
    throw new Error(`${label} path rejected: ${pathCheck.error}`);
  }

  try {
    return fs.readFileSync(pathCheck.resolved, 'utf-8').trimEnd();
  } catch {
    throw new Error(`${label} file not found: ${filePath}`);
  }
}

function cmdStatePatch(cwd, patches, raw) {
  // Validate all field names before processing
  const { validateFieldName } = require('./security.cjs');
  for (const field of Object.keys(patches)) {
    const fieldCheck = validateFieldName(field);
    if (!fieldCheck.valid) {
      error(`state patch: ${fieldCheck.error}`);
    }
  }

  const statePath = planningPaths(cwd).state;
  try {
    const results = { updated: [], failed: [] };

    // Use atomic read-modify-write to prevent lost updates from concurrent agents
    readModifyWriteStateMd(statePath, (content) => {
      for (const [field, value] of Object.entries(patches)) {
        const result = stateReplaceField(content, field, value);
        if (result) {
          content = result;
          results.updated.push(field);
        } else {
          results.failed.push(field);
        }
      }
      return content;
    }, cwd);

    output(results, raw, results.updated.length > 0 ? 'true' : 'false');
  } catch {
    error('STATE.md not found');
  }
}

function cmdStateUpdate(cwd, field, value) {
  if (!field || value === undefined) {
    error('field and value required for state update');
  }

  // Validate field name to prevent regex injection via crafted field names
  const { validateFieldName } = require('./security.cjs');
  const fieldCheck = validateFieldName(field);
  if (!fieldCheck.valid) {
    error(`state update: ${fieldCheck.error}`);
  }

  const statePath = planningPaths(cwd).state;
  try {
    let updated = false;
    const shouldResync = ['Progress', 'Total Plans in Phase', 'Total Phases'].includes(field);
    // Preserve curated progress for body-only updates, but allow fields that
    // directly project into progress.* frontmatter to rebuild after mutation.
    readModifyWriteStateMd(statePath, (content) => {
      const body = stripFrontmatter(content);
      const result = stateReplaceField(body, field, value);
      if (result) {
        updated = true;
        const existingFm = extractFrontmatter(content);
        if (Object.keys(existingFm).length > 0) {
          return `---\n${reconstructFrontmatter(existingFm)}\n---\n\n${result}`;
        }
        return result;
      }
      return content;
    }, cwd, { resync: shouldResync });
    if (updated) {
      output({ updated: true });
    } else {
      output({ updated: false, reason: `Field "${field}" not found in STATE.md` });
    }
  } catch {
    output({ updated: false, reason: 'STATE.md not found' });
  }
}

// ─── State Progression Engine ────────────────────────────────────────────────

/**
 * Replace a STATE.md field with fallback field name support.
 * Tries `primary` first, then `fallback` (if provided), returns content unchanged
 * if neither matches. This consolidates the replaceWithFallback pattern that was
 * previously duplicated inline across phase.cjs, milestone.cjs, and state.cjs.
 */
function stateReplaceFieldWithFallback(content, primary, fallback, value) {
  let result = stateReplaceField(content, primary, value);
  if (result) return result;
  if (fallback) {
    result = stateReplaceField(content, fallback, value);
    if (result) return result;
  }
  // Neither pattern matched — field may have been reformatted or removed.
  // Log diagnostic so template drift is detected early rather than silently swallowed.
  process.stderr.write(
    `[gsd-tools] WARNING: STATE.md field "${primary}"${fallback ? ` (fallback: "${fallback}")` : ''} not found — update skipped. ` +
    `This may indicate STATE.md was externally modified or uses an unexpected format.\n`
  );
  return content;
}

/**
 * Update fields within the ## Current Position section of STATE.md.
 * This keeps the Current Position body in sync with the bold frontmatter fields.
 * Only updates fields that already exist in the section; does not add new lines.
 * Fixes #1365: advance-plan could not update Status/Last activity after begin-phase.
 */
function updateCurrentPositionFields(content, fields) {
  const posPattern = /(##\s*Current Position\s*\n)([\s\S]*?)(?=\n##|$)/i;
  const posMatch = content.match(posPattern);
  if (!posMatch) return content;

  let posBody = posMatch[2];

  if (fields.status && /^Status:/m.test(posBody)) {
    posBody = posBody.replace(/^Status:.*$/m, `Status: ${fields.status}`);
  }
  if (fields.lastActivity && /^Last activity:/im.test(posBody)) {
    posBody = posBody.replace(/^Last activity:.*$/im, `Last activity: ${fields.lastActivity}`);
  }
  if (fields.plan && /^Plan:/m.test(posBody)) {
    posBody = posBody.replace(/^Plan:.*$/m, `Plan: ${fields.plan}`);
  }

  return content.replace(posPattern, () => `${posMatch[1]}${posBody}`);
}

function cmdStateAdvancePlan(cwd, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) { output({ error: 'STATE.md not found' }, raw); return; }

  const today = new Date().toISOString().split('T')[0];
  let result = null;

  readModifyWriteStateMd(statePath, (content) => {
    // Try legacy separate fields first, then compound "Plan: X of Y" format
    const legacyPlan = stateExtractField(content, 'Current Plan');
    const legacyTotal = stateExtractField(content, 'Total Plans in Phase');
    const planField = stateExtractField(content, 'Plan');

    let currentPlan, totalPlans;
    let useCompoundFormat = false;

    if (legacyPlan && legacyTotal) {
      currentPlan = parseInt(legacyPlan, 10);
      totalPlans = parseInt(legacyTotal, 10);
    } else if (planField) {
      // Compound format: "2 of 6 in current phase" or "2 of 6"
      currentPlan = parseInt(planField, 10);
      const ofMatch = planField.match(/of\s+(\d+)/);
      totalPlans = ofMatch ? parseInt(ofMatch[1], 10) : NaN;
      useCompoundFormat = true;
    }

    if (isNaN(currentPlan) || isNaN(totalPlans)) {
      result = { error: true };
      return content;
    }

    if (currentPlan >= totalPlans) {
      content = stateReplaceFieldWithFallback(content, 'Status', null, 'Phase complete — ready for verification');
      content = stateReplaceFieldWithFallback(content, 'Last Activity', 'Last activity', today);
      content = updateCurrentPositionFields(content, { status: 'Phase complete — ready for verification', lastActivity: today });
      result = { advanced: false, reason: 'last_plan', current_plan: currentPlan, total_plans: totalPlans, status: 'ready_for_verification' };
    } else {
      const newPlan = currentPlan + 1;
      let planDisplayValue;
      if (useCompoundFormat) {
        // Preserve compound format: "X of Y in current phase" → replace X only
        planDisplayValue = planField.replace(/^\d+/, String(newPlan));
        content = stateReplaceField(content, 'Plan', planDisplayValue) || content;
      } else {
        planDisplayValue = `${newPlan} of ${totalPlans}`;
        content = stateReplaceField(content, 'Current Plan', String(newPlan)) || content;
      }
      content = stateReplaceFieldWithFallback(content, 'Status', null, 'Ready to execute');
      content = stateReplaceFieldWithFallback(content, 'Last Activity', 'Last activity', today);
      content = updateCurrentPositionFields(content, { status: 'Ready to execute', lastActivity: today, plan: planDisplayValue });
      result = { advanced: true, previous_plan: currentPlan, current_plan: newPlan, total_plans: totalPlans };
    }
    return content;
  }, cwd);

  if (!result || result.error) {
    output({ error: 'Cannot parse Current Plan or Total Plans in Phase from STATE.md' }, raw);
    return;
  }

  if (result.advanced === false) {
    output(result, raw, 'false');
  } else {
    output(result, raw, 'true');
  }
}

function cmdStateRecordMetric(cwd, options, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) { output({ error: 'STATE.md not found' }, raw); return; }

  const { phase, plan, duration, tasks, files } = options;

  if (!phase || !plan || !duration) {
    output({ error: 'phase, plan, and duration required' }, raw);
    return;
  }

  let recorded = false;
  let created = false;
  readModifyWriteStateMd(statePath, (content) => {
    // Find Performance Metrics section and its table
    const metricsPattern = /(##\s*Performance Metrics[\s\S]*?\n\|[^\n]+\n\|[-|\s]+\n)([\s\S]*?)(?=\n##|\n$|$)/i;
    const metricsMatch = content.match(metricsPattern);

    const newRow = `| Phase ${phase} P${plan} | ${duration} | ${tasks || '-'} tasks | ${files || '-'} files |`;

    if (metricsMatch) {
      let tableBody = metricsMatch[2].trimEnd();

      if (tableBody.trim() === '' || tableBody.includes('None yet')) {
        tableBody = newRow;
      } else {
        tableBody = tableBody + '\n' + newRow;
      }

      recorded = true;
      return content.replace(metricsPattern, (_match, header) => `${header}${tableBody}\n`);
    }

    // Section absent — DWIM: auto-create canonical ## Performance Metrics scaffold,
    // then append the row. Matches state begin-phase / advance-plan DWIM behavior.
    const scaffold = [
      '',
      '## Performance Metrics',
      '',
      '| Phase | Plan | Duration | Notes |',
      '|-------|------|----------|-------|',
      newRow,
      '',
    ].join('\n');
    recorded = true;
    created = true;
    return content.trimEnd() + '\n' + scaffold;
  }, cwd);

  // Auto-create fallback guarantees recorded === true; no else branch needed.
  const result = { recorded: true, phase, plan, duration };
  if (created) result.created = true;
  output(result, raw, 'true');
}

function cmdStateUpdateProgress(cwd, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) { output({ error: 'STATE.md not found' }, raw); return; }

  // Count summaries across current milestone phases only (outside lock — read-only)
  const phasesDir = planningPaths(cwd).phases;
  let totalPlans = 0;
  let totalSummaries = 0;

  if (fs.existsSync(phasesDir)) {
    const isDirInMilestone = getMilestonePhaseFilter(cwd);
    const phaseDirs = fs.readdirSync(phasesDir, { withFileTypes: true })
      .filter(e => e.isDirectory()).map(e => e.name)
      .filter(isDirInMilestone);
    for (const dir of phaseDirs) {
      const { planCount, summaryCount } = scanPhasePlans(path.join(phasesDir, dir));
      totalPlans += planCount;
      totalSummaries += summaryCount;
    }
  }

  const percent = totalPlans > 0 ? Math.min(100, Math.round(totalSummaries / totalPlans * 100)) : 0;
  const barWidth = 10;
  const filled = Math.round(percent / 100 * barWidth);
  const bar = '\u2588'.repeat(filled) + '\u2591'.repeat(barWidth - filled);
  const progressStr = `[${bar}] ${percent}%`;

  let updated = false;
  const _totalPlans = totalPlans;
  const _totalSummaries = totalSummaries;

  readModifyWriteStateMd(statePath, (content) => {
    // Try **Progress:** bold format first, then plain Progress: format
    const boldProgressPattern = /(\*\*Progress:\*\*\s*).*/i;
    const plainProgressPattern = /^(Progress:\s*).*/im;
    if (boldProgressPattern.test(content)) {
      updated = true;
      return content.replace(boldProgressPattern, (_match, prefix) => `${prefix}${progressStr}`);
    } else if (plainProgressPattern.test(content)) {
      updated = true;
      return content.replace(plainProgressPattern, (_match, prefix) => `${prefix}${progressStr}`);
    }
    return content;
  }, cwd);

  if (updated) {
    output({ updated: true, percent, completed: _totalSummaries, total: _totalPlans, bar: progressStr }, raw, progressStr);
  } else {
    output({ updated: false, reason: 'Progress field not found in STATE.md' }, raw, 'false');
  }
}

function cmdStateAddDecision(cwd, options, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) { output({ error: 'STATE.md not found' }, raw); return; }

  const { phase, summary, summary_file, rationale, rationale_file } = options;
  let summaryText = null;
  let rationaleText = '';

  try {
    summaryText = readTextArgOrFile(cwd, summary, summary_file, 'summary');
    rationaleText = readTextArgOrFile(cwd, rationale || '', rationale_file, 'rationale');
  } catch (err) {
    output({ added: false, reason: err.message }, raw, 'false');
    return;
  }

  if (!summaryText) { output({ error: 'summary required' }, raw); return; }

  const entry = `- [Phase ${phase || '?'}]: ${summaryText}${rationaleText ? ` — ${rationaleText}` : ''}`;
  let added = false;
  let created = false;

  readModifyWriteStateMd(statePath, (content) => {
    // Find Decisions section (various heading patterns)
    const sectionPattern = /(###?\s*(?:Decisions|Decisions Made|Accumulated.*Decisions)\s*\n)([\s\S]*?)(?=\n###?|\n##[^#]|$)/i;
    const match = content.match(sectionPattern);

