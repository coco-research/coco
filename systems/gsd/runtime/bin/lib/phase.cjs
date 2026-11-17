/**
 * Phase — Phase CRUD, query, and lifecycle operations
 */

const fs = require('fs');
const path = require('path');
const { escapeRegex, loadConfig, normalizePhaseName, phaseMarkdownRegexSource, comparePhaseNum, findPhaseInternal, getArchivedPhaseDirs, generateSlugInternal, getMilestonePhaseFilter, stripShippedMilestones, extractCurrentMilestone, replaceInCurrentMilestone, toPosixPath, output, error, readSubdirectories, phaseTokenMatches, ERROR_REASON } = require('./core.cjs');
const { platformWriteSync, platformReadSync, platformEnsureDir } = require('./shell-command-projection.cjs');
const { planningDir, withPlanningLock } = require('./planning-workspace.cjs');
const { extractFrontmatter } = require('./frontmatter.cjs');
const { writeStateMd, readModifyWriteStateMd, stateExtractField, stateReplaceField, stateReplaceFieldWithFallback, updatePerformanceMetricsSection } = require('./state.cjs');
const { formatGsdSlash, resolveRuntime } = require('./runtime-slash.cjs');

// #2893 — strict canonical filter: `{padded_phase}-{NN}-PLAN.md` or `PLAN.md`.
// Documented in agents/gsd-planner.md (write_phase_prompt step). The wider
// "looks like a plan but isn't canonical" probe below is used to surface a
// loud warning instead of silently returning zero plans.
const isCanonicalPlanFile = (f) => f.endsWith('-PLAN.md') || f === 'PLAN.md';

// Any .md file with PLAN anywhere in the basename — the diagnostic net for
// catching agent deviations like `01-PLAN-01-foundation.md` (#2893).
// Excludes derivative files (`-PLAN-OUTLINE.md`, `*.pre-bounce.md`, etc.) that
// the planner legitimately produces alongside canonical plans.
const PLAN_OUTLINE_RE = /-PLAN-OUTLINE\.md$/i;
const PLAN_PRE_BOUNCE_RE = /-PLAN.*\.pre-bounce\.md$/i;
const looksLikePlanFile = (f) =>
  /\.md$/i.test(f)
  && /PLAN/i.test(f)
  && !PLAN_OUTLINE_RE.test(f)
  && !PLAN_PRE_BOUNCE_RE.test(f);

/**
 * Detect plan-shaped files that the canonical filter would reject. Returns
 * a warning string when offenders exist, else null. Centralised so every
 * read site (phase-plan-index, phases list --type plans, find-phase) emits
 * the same message.
 *
 * @param {string[]} dirFiles — readdirSync output for one phase directory
 * @param {string[]} matchedFiles — what the canonical filter accepted
 * @returns {string|null}
 */
function describeNonCanonicalPlans(dirFiles, matchedFiles) {
  const matched = new Set(matchedFiles);
  const offenders = dirFiles.filter((f) => looksLikePlanFile(f) && !matched.has(f));
  if (offenders.length === 0) return null;
  return (
    `Found ${offenders.length} plan-shaped file(s) in this phase that don't match the canonical ` +
    `naming convention "{padded_phase}-{NN}-PLAN.md" (or bare "PLAN.md") and were skipped: ` +
    offenders.map((f) => `"${f}"`).join(', ') +
    `. Rename to the canonical form (e.g. "01-01-PLAN.md") so the executor can detect them. ` +
    `See agents/gsd-planner.md write_phase_prompt step for the full contract.`
  );
}

function extractCanonicalPlanId(filename) {
  const base = filename.replace(/-PLAN\.md$/i, '').replace(/-SUMMARY\.md$/i, '').replace(/\.md$/i, '');
  const parts = base.split('-').filter(Boolean);
  const tokenRe = /^\d+[A-Z]?(?:\.\d+)*$/i;
  const phaseIdx = parts.findIndex(p => tokenRe.test(p));
  if (phaseIdx >= 0 && phaseIdx + 1 < parts.length && tokenRe.test(parts[phaseIdx + 1])) {
    return `${parts[phaseIdx]}-${parts[phaseIdx + 1]}`;
  }
  return base;
}

function cmdPhasesList(cwd, options, raw) {
  const phasesDir = path.join(planningDir(cwd), 'phases');
  const { type, phase, includeArchived } = options;

  // If no phases directory, return empty
  if (!fs.existsSync(phasesDir)) {
    if (type) {
      output({ files: [], count: 0 }, raw, '');
    } else {
      output({ directories: [], count: 0 }, raw, '');
    }
    return;
  }

  try {
    // Get all phase directories
    const entries = fs.readdirSync(phasesDir, { withFileTypes: true });
    let dirs = entries.filter(e => e.isDirectory()).map(e => e.name);

    // Include archived phases if requested
    if (includeArchived) {
      const archived = getArchivedPhaseDirs(cwd);
      for (const a of archived) {
        dirs.push(`${a.name} [${a.milestone}]`);
      }
    }

    // Sort numerically (handles integers, decimals, letter-suffix, hybrids)
    dirs.sort((a, b) => comparePhaseNum(a, b));

    // If filtering by phase number
    if (phase) {
      const normalized = normalizePhaseName(phase);
      const match = dirs.find(d => phaseTokenMatches(d, normalized));
      if (!match) {
        output({ files: [], count: 0, phase_dir: null, error: 'Phase not found' }, raw, '');
        return;
      }
      dirs = [match];
    }

    // If listing files of a specific type
    if (type) {
      const files = [];
      const warnings = [];
      for (const dir of dirs) {
        const dirPath = path.join(phasesDir, dir);
        const dirFiles = fs.readdirSync(dirPath);

        let filtered;
        if (type === 'plans') {
          filtered = dirFiles.filter(isCanonicalPlanFile);
          // #2893 — surface plan-shaped files the canonical filter rejected
          // so callers (executor init, etc.) don't silently see zero plans.
          const w = describeNonCanonicalPlans(dirFiles, filtered);
          if (w) warnings.push(`${dir}: ${w}`);
        } else if (type === 'summaries') {
          filtered = dirFiles.filter(f => f.endsWith('-SUMMARY.md') || f === 'SUMMARY.md');
        } else {
          filtered = dirFiles;
        }

        files.push(...filtered.sort());
      }

      const result = {
        files,
        count: files.length,
        phase_dir: phase ? dirs[0].replace(/^\d+(?:\.\d+)*-?/, '') : null,
      };
      if (warnings.length) result.warning = warnings.join(' | ');
      output(result, raw, files.join('\n'));
      return;
    }

    // Default: list directories
    output({ directories: dirs, count: dirs.length }, raw, dirs.join('\n'));
  } catch (e) {
    error('Failed to list phases: ' + e.message);
  }
}

function cmdPhaseNextDecimal(cwd, basePhase, raw) {
  const phasesDir = path.join(planningDir(cwd), 'phases');
  const normalized = normalizePhaseName(basePhase);

  try {
    let baseExists = false;
    const decimalSet = new Set();

    // Scan directory names for existing decimal phases
    if (fs.existsSync(phasesDir)) {
      const entries = fs.readdirSync(phasesDir, { withFileTypes: true });
      const dirs = entries.filter(e => e.isDirectory()).map(e => e.name);
      baseExists = dirs.some(d => phaseTokenMatches(d, normalized));

      const dirPattern = new RegExp(`^(?:[A-Z]{1,6}-)?${escapeRegex(normalized)}\\.(\\d+)`);
      for (const dir of dirs) {
        const match = dir.match(dirPattern);
        if (match) decimalSet.add(parseInt(match[1], 10));
      }
    }

    // Also scan ROADMAP.md for phase entries that may not have directories yet
    const roadmapPath = path.join(planningDir(cwd), 'ROADMAP.md');
    if (fs.existsSync(roadmapPath)) {
      try {
        const roadmapContent = fs.readFileSync(roadmapPath, 'utf-8');
        // #3537: padding-tolerant on both sides — `0*${escapeRegex(...)}`
        // tolerated extra padding but not missing.
        const phasePattern = new RegExp(
          `#{2,4}\\s*Phase\\s+${phaseMarkdownRegexSource(normalized)}\\.(\\d+)\\s*:`, 'gi'
        );
        let pm;
        while ((pm = phasePattern.exec(roadmapContent)) !== null) {
          decimalSet.add(parseInt(pm[1], 10));
        }
      } catch { /* ROADMAP.md read failure is non-fatal */ }
    }

