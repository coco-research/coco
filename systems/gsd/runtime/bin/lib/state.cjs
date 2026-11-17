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

    if (match) {
      let sectionBody = match[2];
      // Remove placeholders
      sectionBody = sectionBody.replace(/None yet\.?\s*\n?/gi, '').replace(/No decisions yet\.?\s*\n?/gi, '');
      sectionBody = sectionBody.trimEnd() + '\n' + entry + '\n';
      added = true;
      return content.replace(sectionPattern, (_match, header) => `${header}${sectionBody}`);
    }

    // Section absent — DWIM: auto-create canonical ## Decisions scaffold,
    // then append the entry. Matches state begin-phase / advance-plan DWIM behavior.
    const scaffold = [
      '',
      '## Decisions',
      '',
      entry,
      '',
    ].join('\n');
    added = true;
    created = true;
    return content.trimEnd() + '\n' + scaffold;
  }, cwd);

  // Auto-create fallback guarantees added === true; no else branch needed.
  const result = { added: true, decision: entry };
  if (created) result.created = true;
  output(result, raw, 'true');
}

function cmdStateAddBlocker(cwd, text, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) { output({ error: 'STATE.md not found' }, raw); return; }
  const blockerOptions = typeof text === 'object' && text !== null ? text : { text };
  let blockerText = null;

  try {
    blockerText = readTextArgOrFile(cwd, blockerOptions.text, blockerOptions.text_file, 'blocker');
  } catch (err) {
    output({ added: false, reason: err.message }, raw, 'false');
    return;
  }

  if (!blockerText) { output({ error: 'text required' }, raw); return; }

  const entry = `- ${blockerText}`;
  let added = false;
  let created = false;

  readModifyWriteStateMd(statePath, (content) => {
    const sectionPattern = /(###?\s*(?:Blockers|Blockers\/Concerns|Concerns)\s*\n)([\s\S]*?)(?=\n###?|\n##[^#]|$)/i;
    const match = content.match(sectionPattern);

    if (match) {
      let sectionBody = match[2];
      sectionBody = sectionBody.replace(/None\.?\s*\n?/gi, '').replace(/None yet\.?\s*\n?/gi, '');
      sectionBody = sectionBody.trimEnd() + '\n' + entry + '\n';
      added = true;
      return content.replace(sectionPattern, (_match, header) => `${header}${sectionBody}`);
    }

    // Section absent — DWIM: auto-create canonical ### Blockers scaffold.
    const scaffold = [
      '',
      '### Blockers',
      '',
      entry,
      '',
    ].join('\n');
    added = true;
    created = true;
    return content.trimEnd() + '\n' + scaffold;
  }, cwd);

  // Auto-create fallback guarantees added === true; no else branch needed.
  const result = { added: true, blocker: blockerText };
  if (created) result.created = true;
  output(result, raw, 'true');
}

function cmdStateResolveBlocker(cwd, text, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) { output({ error: 'STATE.md not found' }, raw); return; }
  if (!text) { output({ error: 'text required' }, raw); return; }

  let resolved = false;

  readModifyWriteStateMd(statePath, (content) => {
    const sectionPattern = /(###?\s*(?:Blockers|Blockers\/Concerns|Concerns)\s*\n)([\s\S]*?)(?=\n###?|\n##[^#]|$)/i;
    const match = content.match(sectionPattern);

    if (match) {
      const sectionBody = match[2];
      const lines = sectionBody.split('\n');
      const filtered = lines.filter(line => {
        if (!line.startsWith('- ')) return true;
        return !line.toLowerCase().includes(text.toLowerCase());
      });

      let newBody = filtered.join('\n');
      // If section is now empty, add placeholder
      if (!newBody.trim() || !newBody.includes('- ')) {
        newBody = 'None\n';
      }

      resolved = true;
      return content.replace(sectionPattern, (_match, header) => `${header}${newBody}`);
    }
    return content;
  }, cwd);

  if (resolved) {
    output({ resolved: true, blocker: text }, raw, 'true');
  } else {
    output({ resolved: false, reason: 'Blockers section not found in STATE.md' }, raw, 'false');
  }
}

function cmdStateRecordSession(cwd, options, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) { output({ error: 'STATE.md not found' }, raw); return; }

  const now = new Date().toISOString();
  const updated = [];

  readModifyWriteStateMd(statePath, (content) => {
    // Update Last session / Last Date
    let result = stateReplaceField(content, 'Last session', now);
    if (result) { content = result; updated.push('Last session'); }
    result = stateReplaceField(content, 'Last Date', now);
    if (result) { content = result; updated.push('Last Date'); }

    // Update Stopped at
    if (options.stopped_at) {
      result = stateReplaceField(content, 'Stopped At', options.stopped_at);
      if (!result) result = stateReplaceField(content, 'Stopped at', options.stopped_at);
      if (result) { content = result; updated.push('Stopped At'); }
    }

    // Update Resume file
    const resumeFile = options.resume_file || 'None';
    result = stateReplaceField(content, 'Resume File', resumeFile);
    if (!result) result = stateReplaceField(content, 'Resume file', resumeFile);
    if (result) { content = result; updated.push('Resume File'); }

    return content;
  }, cwd);

  if (updated.length > 0) {
    output({ recorded: true, updated }, raw, 'true');
  } else {
    output({ recorded: false, reason: 'No session fields found in STATE.md' }, raw, 'false');
  }
}

function cmdStateSnapshot(cwd, raw) {
  const statePath = planningPaths(cwd).state;

  if (!fs.existsSync(statePath)) {
    output({ error: 'STATE.md not found' }, raw);
    return;
  }

  const content = fs.readFileSync(statePath, 'utf-8');

  // Bug #3265: prefer YAML frontmatter for canonical scalar fields so that a
  // body table cell containing **Status:** Y cannot shadow the authoritative
  // frontmatter value.  Mirrors the fix in sdk/src/query/state.ts.
  const fm = extractFrontmatter(content);
  const body = stripFrontmatter(content);

  // Helper: return frontmatter scalar value when present and non-empty.
  // Accepts strings, numbers, and booleans — coercing non-string primitives to
  // their string representation so callers always receive string | null.
  // Returns null for missing, null/undefined, or empty-after-trim values so
  // the caller falls back to body extraction.
  const fmScalar = (key) => {
    const v = fm[key];
    if (v === null || v === undefined) return null;
    if (typeof v === 'string') return v.trim() || null;
    if (typeof v === 'number' || typeof v === 'boolean') return String(v);
    return null;
  };

  // Extract basic fields — frontmatter keys take precedence over body
  const currentPhase = fmScalar('current_phase') ?? stateExtractField(body, 'Current Phase');
  const currentPhaseName = fmScalar('current_phase_name') ?? stateExtractField(body, 'Current Phase Name');
  const totalPhasesRaw = fmScalar('total_phases') ?? stateExtractField(body, 'Total Phases');
  const currentPlan = fmScalar('current_plan') ?? stateExtractField(body, 'Current Plan');
  const totalPlansRaw = fmScalar('total_plans_in_phase') ?? stateExtractField(body, 'Total Plans in Phase');
  const status = fmScalar('status') ?? stateExtractField(body, 'Status');
  const progressRaw = fmScalar('progress') ?? stateExtractField(body, 'Progress');
  const lastActivity = fmScalar('last_activity') ?? stateExtractField(body, 'Last Activity');
  const lastActivityDesc = fmScalar('last_activity_desc') ?? stateExtractField(body, 'Last Activity Description');
  const pausedAt = fmScalar('paused_at') ?? stateExtractField(body, 'Paused At');

  // Parse numeric fields
  const totalPhases = totalPhasesRaw ? parseInt(totalPhasesRaw, 10) : null;
  const totalPlansInPhase = totalPlansRaw ? parseInt(totalPlansRaw, 10) : null;
  const progressPercent = progressRaw ? parseInt(progressRaw.replace('%', ''), 10) : null;

  // Extract decisions table
  const decisions = [];
  const decisionsMatch = body.match(/##\s*Decisions Made[\s\S]*?\n\|[^\n]+\n\|[-|\s]+\n([\s\S]*?)(?=\n##|\n$|$)/i);
  if (decisionsMatch) {
    const tableBody = decisionsMatch[1];
    const rows = tableBody.trim().split('\n').filter(r => r.includes('|'));
    for (const row of rows) {
      const cells = row.split('|').map(c => c.trim()).filter(Boolean);
      if (cells.length >= 3) {
        decisions.push({
          phase: cells[0],
          summary: cells[1],
          rationale: cells[2],
        });
      }
    }
  }

  // Extract blockers list
  const blockers = [];
  const blockersMatch = body.match(/##\s*Blockers\s*\n([\s\S]*?)(?=\n##|$)/i);
  if (blockersMatch) {
    const blockersSection = blockersMatch[1];
    const items = blockersSection.match(/^-\s+(.+)$/gm) || [];
    for (const item of items) {
      blockers.push(item.replace(/^-\s+/, '').trim());
    }
  }

  // Extract session info
  const session = {
    last_date: null,
    stopped_at: null,
    resume_file: null,
  };

  const sessionMatch = body.match(/##\s*Session\s*\n([\s\S]*?)(?=\n##|$)/i);
  if (sessionMatch) {
    const sessionSection = sessionMatch[1];
    const lastDateMatch = sessionSection.match(/\*\*Last Date:\*\*\s*(.+)/i)
      || sessionSection.match(/^Last Date:\s*(.+)/im);
    const stoppedAtMatch = sessionSection.match(/\*\*Stopped At:\*\*\s*(.+)/i)
      || sessionSection.match(/^Stopped At:\s*(.+)/im);
    const resumeFileMatch = sessionSection.match(/\*\*Resume File:\*\*\s*(.+)/i)
      || sessionSection.match(/^Resume File:\s*(.+)/im);

    if (lastDateMatch) session.last_date = lastDateMatch[1].trim();
    if (stoppedAtMatch) session.stopped_at = stoppedAtMatch[1].trim();
    if (resumeFileMatch) session.resume_file = resumeFileMatch[1].trim();
  }

  const result = {
    current_phase: currentPhase,
    current_phase_name: currentPhaseName,
    total_phases: totalPhases,
    current_plan: currentPlan,
    total_plans_in_phase: totalPlansInPhase,
    status,
    progress_percent: progressPercent,
    last_activity: lastActivity,
    last_activity_desc: lastActivityDesc,
    decisions,
    blockers,
    paused_at: pausedAt,
    session,
  };

  output(result, raw);
}

// ─── State Frontmatter Sync ──────────────────────────────────────────────────

/**
 * Extract machine-readable fields from STATE.md markdown body and build
 * a YAML frontmatter object. Allows hooks and scripts to read state
 * reliably via `state json` instead of fragile regex parsing.
 */
function buildStateFrontmatter(bodyContent, cwd) {
  const currentPhase = stateExtractField(bodyContent, 'Current Phase');
  const currentPhaseName = stateExtractField(bodyContent, 'Current Phase Name');
  const currentPlan = stateExtractField(bodyContent, 'Current Plan');
  const totalPhasesRaw = stateExtractField(bodyContent, 'Total Phases');
  const totalPlansRaw = stateExtractField(bodyContent, 'Total Plans in Phase');
  const status = stateExtractField(bodyContent, 'Status');
  const progressRaw = stateExtractField(bodyContent, 'Progress');
  const lastActivity = stateExtractField(bodyContent, 'Last Activity');
  // Bug #2444: scope Stopped At extraction to the ## Session section so that
  // historical "Stopped at:" prose elsewhere in the body (e.g. in a
  // Session Continuity Archive section) never overwrites the current value.
  // Fall back to full-body search only when no ## Session section exists.
  const sessionSectionMatch = bodyContent.match(/##\s*Session\s*\n([\s\S]*?)(?=\n##|$)/i);
  const sessionBodyScope = sessionSectionMatch ? sessionSectionMatch[1] : bodyContent;
  const stoppedAt = stateExtractField(sessionBodyScope, 'Stopped At') || stateExtractField(sessionBodyScope, 'Stopped at');
  const pausedAt = stateExtractField(bodyContent, 'Paused At');

  let milestone = null;
  let milestoneName = null;
  if (cwd) {
    try {
      const info = getMilestoneInfo(cwd);
      milestone = info.version;
      milestoneName = info.name;
    } catch { /* intentionally empty */ }
  }

  let totalPhases = totalPhasesRaw ? parseInt(totalPhasesRaw, 10) : null;
  let completedPhases = null;
  let totalPlans = totalPlansRaw ? parseInt(totalPlansRaw, 10) : null;
  let completedPlans = null;

  if (cwd) {
    try {
      const phasesDir = planningPaths(cwd).phases;
      if (fs.existsSync(phasesDir)) {
        // Use cached disk scan when available — avoids N+1 readdirSync calls
        // on repeated buildStateFrontmatter invocations within the same process (#1967)
        let cached = _diskScanCache.get(cwd);
        if (!cached) {
          const isDirInMilestone = getMilestonePhaseFilter(cwd);
          const allMatchingDirs = fs.readdirSync(phasesDir, { withFileTypes: true })
            .filter(e => e.isDirectory()).map(e => e.name)
            .filter(isDirInMilestone);

          // Bug #2445: when stale phase dirs from a prior milestone remain in
          // .planning/phases/ alongside new dirs with the same phase number,
          // de-duplicate by normalized phase number keeping the most recently
          // modified dir. This prevents double-counting (e.g. two "Phase 1" dirs).
          const seenPhaseNums = new Map(); // normalizedNum -> dirName
          for (const dir of allMatchingDirs) {
            const m = dir.match(/^0*(\d+[A-Za-z]?(?:\.\d+)*)/);
            const key = m ? m[1].toLowerCase() : dir;
            if (!seenPhaseNums.has(key)) {
              seenPhaseNums.set(key, dir);
            } else {
              // Keep the dir that is newer on disk (more likely current milestone)
              try {
                const existing = path.join(phasesDir, seenPhaseNums.get(key));
                const candidate = path.join(phasesDir, dir);
                if (fs.statSync(candidate).mtimeMs > fs.statSync(existing).mtimeMs) {
                  seenPhaseNums.set(key, dir);
                }
              } catch { /* keep existing on stat error */ }
            }
          }
          const phaseDirs = [...seenPhaseNums.values()];

          let diskTotalPlans = 0;
          let diskTotalSummaries = 0;
          let diskCompletedPhases = 0;

          for (const dir of phaseDirs) {
            const phaseDir = path.join(phasesDir, dir);
            const { planCount, summaryCount, completed } = scanPhasePlans(phaseDir);
            diskTotalPlans += planCount;
            diskTotalSummaries += summaryCount;
            if (completed) diskCompletedPhases++;
          }
          cached = {
            totalPhases: isDirInMilestone.phaseCount > 0
              ? Math.max(phaseDirs.length, isDirInMilestone.phaseCount)
              : phaseDirs.length,
            completedPhases: diskCompletedPhases,
            totalPlans: diskTotalPlans,
            completedPlans: diskTotalSummaries,
          };
          _diskScanCache.set(cwd, cached);
        }
        totalPhases = cached.totalPhases;
        completedPhases = cached.completedPhases;
        totalPlans = cached.totalPlans;
        completedPlans = cached.completedPlans;
      }
    } catch { /* intentionally empty */ }
  }

  // Derive percent from disk counts when available (ground truth).
  // Uses min(plan_fraction, phase_fraction) via computeProgressPercent so that
  // ROADMAP-declared-but-unrealized future phases cap the reported completion
  // instead of a false 100% from plan-only coverage (#3242 Bug B).
  // Falls back to the body Progress: field only when no plan files exist on disk.
  let progressPercent = computeProgressPercent(completedPlans, totalPlans, completedPhases, totalPhases);
  if (progressPercent === null && progressRaw) {
    const pctMatch = progressRaw.match(/(\d+)%/);
    if (pctMatch) progressPercent = parseInt(pctMatch[1], 10);
  }

  const normalizedStatus = normalizeStateStatus(status, pausedAt);

  const fm = { gsd_state_version: '1.0' };

  if (milestone) fm.milestone = milestone;
  if (milestoneName) fm.milestone_name = milestoneName;
  if (currentPhase) fm.current_phase = currentPhase;
  if (currentPhaseName) fm.current_phase_name = currentPhaseName;
  if (currentPlan) fm.current_plan = currentPlan;
  fm.status = normalizedStatus;
  if (stoppedAt) fm.stopped_at = stoppedAt;
  if (pausedAt) fm.paused_at = pausedAt;
  fm.last_updated = new Date().toISOString();
  if (lastActivity) fm.last_activity = lastActivity;

  const progress = {};
  if (totalPhases !== null) progress.total_phases = totalPhases;
  if (completedPhases !== null) progress.completed_phases = completedPhases;
  if (totalPlans !== null) progress.total_plans = totalPlans;
  if (completedPlans !== null) progress.completed_plans = completedPlans;
  if (progressPercent !== null) progress.percent = progressPercent;
  if (Object.keys(progress).length > 0) fm.progress = progress;

  return fm;
}

function stripFrontmatter(content) {
  // Strip ALL frontmatter blocks at the start of the file.
  // Handles CRLF line endings and multiple stacked blocks (corruption recovery).
  // Greedy: keeps stripping ---...--- blocks separated by optional whitespace.
  let result = content;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const stripped = result.replace(/^\s*---\r?\n[\s\S]*?\r?\n---\s*/, '');
    if (stripped === result) break;
    result = stripped;
  }
  return result;
}

function syncStateFrontmatter(content, cwd) {
  // Read existing frontmatter BEFORE stripping — it may contain values
  // that the body no longer has (e.g., Status field removed by an agent).
  const existingFm = extractFrontmatter(content);
  const body = stripFrontmatter(content);
  const derivedFm = buildStateFrontmatter(body, cwd);

  // Preserve existing frontmatter status when body-derived status is 'unknown'.
  // This prevents a missing Status: field in the body from overwriting a
  // previously valid status (e.g., 'executing' → 'unknown').
  if (derivedFm.status === 'unknown' && existingFm.status && existingFm.status !== 'unknown') {
    derivedFm.status = existingFm.status;
  }

  const yamlStr = reconstructFrontmatter(derivedFm);
  return `---\n${yamlStr}\n---\n\n${body}`;
}

// Transient errno codes that indicate a temporary filesystem condition under
// concurrent O_EXCL races — Docker overlay-fs (ENOENT/EINVAL/EIO), NFS
// (ESTALE), and OS-level interrupt/retry signals (EAGAIN/EINTR).  These are
// recoverable; acquireStateLock retries instead of propagating them.
// Truly fatal codes (EMFILE, ENOSPC, EROFS, EACCES) are NOT in this set and
// will still throw immediately.
const ACQUIRE_LOCK_RETRY_ERRNOS = new Set([
  'EPERM',   // Windows / macOS AV scanner holds the file open during delete
  'EBUSY',   // Windows: file in use by another process
  'EAGAIN',  // POSIX: resource temporarily unavailable
  'EINTR',   // POSIX: syscall interrupted by signal
  'EINVAL',  // Docker overlay-fs: transient during concurrent O_EXCL creation
  'EIO',     // Docker overlay-fs / NFS: transient I/O error
  'ENOENT',  // Docker overlay-fs: parent dir transiently missing during race
  'ESTALE',  // NFS: stale file handle (self-resolves on retry)
]);

/**
 * Acquire a lockfile for STATE.md operations.
 * Returns the lock path for later release.
 */
function acquireStateLock(statePath) {
  const lockPath = statePath + '.lock';
  const retryDelay = 200; // ms
  const staleThresholdMs = 10000;
  const maxWaitMs = 30000;
  const startedAt = Date.now();

  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const fd = fs.openSync(lockPath, fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_WRONLY);
      fs.writeSync(fd, String(process.pid));
      fs.closeSync(fd);
      // Exit-time cleanup keeps a crashed locked region from leaving a stale file (#1916).
      _heldStateLocks.add(lockPath);
      return lockPath;
    } catch (err) {
      // Transient filesystem errors (Docker overlay-fs, NFS, OS signals, AV scanners)
      // are recoverable — retry the acquisition loop rather than propagating.
      // See ACQUIRE_LOCK_RETRY_ERRNOS for the full list and rationale.
      if (ACQUIRE_LOCK_RETRY_ERRNOS.has(err.code)) { continue; }
      if (err.code !== 'EEXIST') throw err; // propagate — silent bypass causes lost updates
      // Only unlink a lock we did not place when it has crossed the staleness
      // threshold (crashed holder). Nuking a fresh lock held by a slow-but-live
      // writer causes lost updates (#3711 regression).
      try {
        const stat = fs.statSync(lockPath);
        if (Date.now() - stat.mtimeMs > staleThresholdMs) {
          try { fs.unlinkSync(lockPath); } catch { /* already gone */ }
          continue;
        }
      } catch { continue; /* released between EEXIST and stat */ }
      if (Date.now() - startedAt >= maxWaitMs) {
        throw new Error(
          'acquireStateLock: ' + lockPath + ' held by live process for ' +
          (Date.now() - startedAt) + 'ms (exceeded ' + maxWaitMs + 'ms budget)'
        );
      }
      const jitter = Math.floor(Math.random() * 50);
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, retryDelay + jitter);
    }
  }
}

function releaseStateLock(lockPath) {
  _heldStateLocks.delete(lockPath);
  try { fs.unlinkSync(lockPath); } catch { /* lock already gone */ }
}

/**
 * Write STATE.md with synchronized YAML frontmatter.
 * All STATE.md writes should use this instead of raw writeFileSync.
 * Uses a simple lockfile to prevent parallel agents from overwriting
 * each other's changes (race condition with read-modify-write cycle).
 */
function writeStateMd(statePath, content, cwd) {
  // Invalidate disk scan cache before computing new frontmatter — the write
  // may create new PLAN/SUMMARY files that buildStateFrontmatter must see.
  // Safe for any calling pattern, not just short-lived CLI processes (#1967).
  if (cwd) _diskScanCache.delete(cwd);
  const synced = syncStateFrontmatter(content, cwd);
  const lockPath = acquireStateLock(statePath);
  try {
    platformWriteSync(statePath, synced);
  } finally {
    releaseStateLock(lockPath);
  }
}

/**
 * Atomic read-modify-write for STATE.md.
 * Holds the lock across the entire read -> transform -> write cycle,
 * preventing the lost-update problem where two agents read the same
 * content and the second write clobbers the first.
 *
 * @param {string} statePath
 * @param {function} transformFn - (content: string) => string
 * @param {string} cwd
 * @param {{ resync?: boolean }} [options]
 *   resync: when true (default) rebuilds the entire frontmatter from disk after
 *   the transform. Pass { resync: false } for body-only updates (e.g. state.update
 *   on a single field) that must not trample manually-curated cross-milestone
 *   progress.* counters in the frontmatter (#3242 Bug A).
 *   When resync is false, syncStateFrontmatter still runs to maintain/create the
 *   frontmatter block, but any existing progress.* sub-keys are preserved from
 *   the pre-transform file rather than being rebuilt from disk.
 */
function readModifyWriteStateMd(statePath, transformFn, cwd, options) {
  const resync = !options || options.resync !== false;
  const lockPath = acquireStateLock(statePath);
  try {
    const content = platformReadSync(statePath) || '';
    // Snapshot the existing progress block BEFORE the transform so we can
    // restore it when resync is false.
    const preFm = resync ? null : extractFrontmatter(content);
    const modified = transformFn(content);
    let synced = syncStateFrontmatter(modified, cwd);

    if (!resync && preFm && preFm.progress) {
      // Re-apply the curated progress block that syncStateFrontmatter just
      // overwrote with disk-derived values.  Only restore keys that were present
      // in the snapshot — this preserves any new non-progress frontmatter fields
      // (e.g., status, current_phase) that syncStateFrontmatter legitimately
      // derived from the updated body.
      const postFm = extractFrontmatter(synced);
      postFm.progress = preFm.progress;
      const yamlStr = reconstructFrontmatter(postFm);
      const body = stripFrontmatter(synced);
      synced = `---\n${yamlStr}\n---\n\n${body}`;
    }

    platformWriteSync(statePath, synced);
  } finally {
    releaseStateLock(lockPath);
  }
}

function cmdStateJson(cwd, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) {
    output({ error: 'STATE.md not found' }, raw, 'STATE.md not found');
    return;
  }

  const content = fs.readFileSync(statePath, 'utf-8');
  const existingFm = extractFrontmatter(content);
  const body = stripFrontmatter(content);

  // Always rebuild from body + disk so progress counters reflect current state.
  // Returning cached frontmatter directly causes stale percent/completed_plans
  // when SUMMARY files were added after the last STATE.md write (#1589).
  const built = buildStateFrontmatter(body, cwd);

  // Preserve frontmatter-only fields that cannot be recovered from the body.
  if (existingFm && existingFm.stopped_at && !built.stopped_at) {
    built.stopped_at = existingFm.stopped_at;
  }
  if (existingFm && existingFm.paused_at && !built.paused_at) {
    built.paused_at = existingFm.paused_at;
  }
  // Preserve existing status when body-derived status is 'unknown' (same logic as syncStateFrontmatter).
  if (built.status === 'unknown' && existingFm && existingFm.status && existingFm.status !== 'unknown') {
    built.status = existingFm.status;
  }
  // Preserve curated cross-milestone aggregates when local disk scanning sees
  // only a narrower realized subset (#3242 Bug A). Stale lower counters still
  // rebuild from disk because they do not exceed the derived scan.
  if (existingFm && shouldPreserveExistingProgress(existingFm.progress, built.progress)) {
    built.progress = normalizeProgressNumbers(existingFm.progress);
  }

  output(built, raw, JSON.stringify(built, null, 2));
}

/**
 * Update STATE.md when a new phase begins execution.
 * Updates body text fields (Current focus, Status, Last Activity, Current Position)
 * and synchronizes frontmatter via writeStateMd.
 * Fixes: #1102 (plan counts), #1103 (status/last_activity), #1104 (body text).
 */
function cmdStateBeginPhase(cwd, phaseNumber, phaseName, planCount, raw) {
  const statePath = planningPaths(cwd).state;
  if (!fs.existsSync(statePath)) {
    output({ error: 'STATE.md not found' }, raw);
    return;
  }

  const today = new Date().toISOString().split('T')[0];
  const updated = [];

  readModifyWriteStateMd(statePath, (content) => {
    // Idempotency guard (#3127): if the phase is already mid-flight, do NOT
    // overwrite execution-progress fields (Current Plan, plan body line,
    // Last Activity Description). Only update fields that are safe to
    // refresh on resume (Last Activity date, Status if inconsistent).
    // A phase is considered mid-flight when Status contains 'Executing Phase N'
    // for the current phase number.
    const currentStatus = stateExtractField(content, 'Status') || '';
    const isAlreadyExecuting = new RegExp(`Executing Phase\\s+${escapeRegex(String(phaseNumber))}\\b`, 'i').test(currentStatus);

    // Update Status field
    const statusValue = `Executing Phase ${phaseNumber}`;
    let result = stateReplaceField(content, 'Status', statusValue);
    if (result) { content = result; updated.push('Status'); }

    // Update Last Activity (safe to update on resume — tracks when execute-phase ran)
    result = stateReplaceField(content, 'Last Activity', today);
    if (result) { content = result; updated.push('Last Activity'); }

    if (!isAlreadyExecuting) {
      // First-time execution: set all progress fields

      // Update Last Activity Description
      const activityDesc = `Phase ${phaseNumber} execution started`;
      result = stateReplaceField(content, 'Last Activity Description', activityDesc);
      if (result) { content = result; updated.push('Last Activity Description'); }

      // Update Current Phase
      result = stateReplaceField(content, 'Current Phase', String(phaseNumber));
      if (result) { content = result; updated.push('Current Phase'); }

      // Update Current Phase Name
      if (phaseName) {
        result = stateReplaceField(content, 'Current Phase Name', phaseName);
        if (result) { content = result; updated.push('Current Phase Name'); }
      }

      // Update Current Plan to 1 (starting from the first plan)
      result = stateReplaceField(content, 'Current Plan', '1');
      if (result) { content = result; updated.push('Current Plan'); }

      // Update Total Plans in Phase
      if (planCount) {
        result = stateReplaceField(content, 'Total Plans in Phase', String(planCount));
        if (result) { content = result; updated.push('Total Plans in Phase'); }
      }

      // Update **Current focus:** body text line (#1104)
      const focusLabel = phaseName ? `Phase ${phaseNumber} — ${phaseName}` : `Phase ${phaseNumber}`;
      const focusPattern = /(\*\*Current focus:\*\*\s*).*/i;
      if (focusPattern.test(content)) {
        content = content.replace(focusPattern, (_match, prefix) => `${prefix}${focusLabel}`);
        updated.push('Current focus');
      }

      // Update ## Current Position section (#1104, #1365)
      const positionPattern = /(##\s*Current Position\s*\n)([\s\S]*?)(?=\n##|$)/i;
      const positionMatch = content.match(positionPattern);
      if (positionMatch) {
        const header = positionMatch[1];
        let posBody = positionMatch[2];

        // Update or insert Phase line
        const newPhase = `Phase: ${phaseNumber}${phaseName ? ` (${phaseName})` : ''} — EXECUTING`;
        if (/^Phase:/m.test(posBody)) {
