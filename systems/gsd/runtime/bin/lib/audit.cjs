/**
 * Open Artifact Audit — Cross-type unresolved state scanner
 *
 * Scans all .planning/ artifact categories for items with open/unresolved state.
 * Returns structured JSON for workflow consumption.
 * Called by: gsd-tools.cjs audit-open
 * Used by: /gsd:complete-milestone pre-close gate
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { toPosixPath } = require('./core.cjs');
const { platformReadSync } = require('./shell-command-projection.cjs');
const { planningDir } = require('./planning-workspace.cjs');
const { extractFrontmatter } = require('./frontmatter.cjs');
const { requireSafePath, sanitizeForDisplay } = require('./security.cjs');

/**
 * Scan .planning/debug/ for open sessions.
 * Open = status NOT in ['resolved', 'complete'].
 * Ignores the resolved/ subdirectory.
 */
function scanDebugSessions(planDir) {
  const debugDir = path.join(planDir, 'debug');
  if (!fs.existsSync(debugDir)) return [];

  const results = [];
  let files;
  try {
    files = fs.readdirSync(debugDir, { withFileTypes: true });
  } catch {
    return [{ scan_error: true }];
  }

  for (const entry of files) {
    if (!entry.isFile()) continue;
    if (!entry.name.endsWith('.md')) continue;

    const filePath = path.join(debugDir, entry.name);

    let safeFilePath;
    try {
      safeFilePath = requireSafePath(filePath, planDir, 'debug session file', { allowAbsolute: true });
    } catch {
      continue;
    }

    const content = platformReadSync(safeFilePath);
    if (content === null) continue;

    const fm = extractFrontmatter(content);
    const status = (fm.status || 'unknown').toLowerCase();
    if (status === 'resolved' || status === 'complete') continue;

    // Extract hypothesis from "Current Focus" block if parseable
    let hypothesis = '';
    const focusMatch = content.match(/##\s*Current Focus[^\n]*\n([\s\S]*?)(?=\n##\s|$)/i);
    if (focusMatch) {
      const focusText = focusMatch[1].trim().split('\n')[0].trim();
      hypothesis = sanitizeForDisplay(focusText.slice(0, 100));
    }

    const slug = path.basename(entry.name, '.md');
    results.push({
      slug: sanitizeForDisplay(slug),
      status: sanitizeForDisplay(status),
      updated: sanitizeForDisplay(String(fm.updated || fm.date || '')),
      hypothesis,
    });
  }

  return results;
}

/**
 * Scan .planning/quick/ for incomplete tasks.
 * Incomplete if SUMMARY.md missing or status !== 'complete'.
 */
function scanQuickTasks(planDir) {
  const quickDir = path.join(planDir, 'quick');
  if (!fs.existsSync(quickDir)) return [];

  let entries;
  try {
    entries = fs.readdirSync(quickDir, { withFileTypes: true });
  } catch {
    return [{ scan_error: true }];
  }

  const results = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;

    const dirName = entry.name;
    const taskDir = path.join(quickDir, dirName);

    let safeTaskDir;
    try {
      safeTaskDir = requireSafePath(taskDir, planDir, 'quick task dir', { allowAbsolute: true });
    } catch {
      continue;
    }

    // workflows/quick.md mandates `${quick_id}-SUMMARY.md`; older flows used
    // bare `SUMMARY.md`. Accept either to avoid false-positive "missing".
    let summaryPath = null;
    try {
      const summaryFiles = fs.readdirSync(safeTaskDir, { withFileTypes: true })
        .filter(e => e.isFile() && (e.name === 'SUMMARY.md' || e.name.endsWith('-SUMMARY.md')));
      if (summaryFiles.length > 0) {
        // Prefer the per-task `${quick_id}-SUMMARY.md` form when present.
        const preferred = summaryFiles.find(e => e.name === `${dirName}-SUMMARY.md`)
          || summaryFiles.find(e => e.name.endsWith('-SUMMARY.md'))
          || summaryFiles[0];
        summaryPath = path.join(safeTaskDir, preferred.name);
      }
    } catch {
      // fall through with summaryPath = null → status: missing
    }

    let status = 'missing';
    let description = '';

    if (summaryPath && fs.existsSync(summaryPath)) {
      let safeSum;
      try {
        safeSum = requireSafePath(summaryPath, planDir, 'quick task summary', { allowAbsolute: true });
      } catch {
        continue;
      }
      const content = platformReadSync(safeSum);
      if (content === null) {
        status = 'unreadable';
      } else {
        const fm = extractFrontmatter(content);
        status = (fm.status || 'unknown').toLowerCase();
      }
    }

    if (status === 'complete') continue;

    // Parse date and slug from directory name: YYYYMMDD-slug or YYYY-MM-DD-slug
    let date = '';
    let slug = sanitizeForDisplay(dirName);
    const dateMatch = dirName.match(/^(\d{4}-?\d{2}-?\d{2})-(.+)$/);
    if (dateMatch) {
      date = dateMatch[1];
      slug = sanitizeForDisplay(dateMatch[2]);
    }

    results.push({
      slug,
      date,
      status: sanitizeForDisplay(status),
      description,
    });
  }

  return results;
}

/**
 * Scan .planning/threads/ for open threads.
 * Open if status in ['open', 'in_progress', 'in progress'] (case-insensitive).
 */
function scanThreads(planDir) {
  const threadsDir = path.join(planDir, 'threads');
  if (!fs.existsSync(threadsDir)) return [];

  let files;
  try {
    files = fs.readdirSync(threadsDir, { withFileTypes: true });
  } catch {
    return [{ scan_error: true }];
  }

  const openStatuses = new Set(['open', 'in_progress', 'in progress']);
  const results = [];

  for (const entry of files) {
    if (!entry.isFile()) continue;
    if (!entry.name.endsWith('.md')) continue;

    const filePath = path.join(threadsDir, entry.name);

    let safeFilePath;
    try {
      safeFilePath = requireSafePath(filePath, planDir, 'thread file', { allowAbsolute: true });
    } catch {
      continue;
    }

    const content = platformReadSync(safeFilePath);
    if (content === null) continue;

    const fm = extractFrontmatter(content);
    let status = (fm.status || '').toLowerCase().trim();

    // Fall back to scanning body for ## Status: OPEN / IN PROGRESS
    if (!status) {
      const bodyStatusMatch = content.match(/##\s*Status:\s*(OPEN|IN PROGRESS|IN_PROGRESS)/i);
      if (bodyStatusMatch) {
        status = bodyStatusMatch[1].toLowerCase().replace(/ /g, '_');
      }
    }

    if (!openStatuses.has(status)) continue;

    // Extract title from # Thread: heading or frontmatter title
    let title = sanitizeForDisplay(String(fm.title || ''));
    if (!title) {
      const headingMatch = content.match(/^#\s*Thread:\s*(.+)$/m);
      if (headingMatch) {
        title = sanitizeForDisplay(headingMatch[1].trim().slice(0, 100));
      }
    }

    const slug = path.basename(entry.name, '.md');
    results.push({
      slug: sanitizeForDisplay(slug),
      status: sanitizeForDisplay(status),
      updated: sanitizeForDisplay(String(fm.updated || fm.date || '')),
      title,
    });
  }

  return results;
}

/**
 * Scan .planning/todos/pending/ for pending todos.
 * Returns array of { filename, priority, area, summary }.
 * Display limited to first 5 + count of remainder.
 */
function scanTodos(planDir) {
  const pendingDir = path.join(planDir, 'todos', 'pending');
  if (!fs.existsSync(pendingDir)) return [];

  let files;
  try {
    files = fs.readdirSync(pendingDir, { withFileTypes: true });
  } catch {
    return [{ scan_error: true }];
  }

  const mdFiles = files.filter(e => e.isFile() && e.name.endsWith('.md'));
  const results = [];

  const displayFiles = mdFiles.slice(0, 5);
  for (const entry of displayFiles) {
    const filePath = path.join(pendingDir, entry.name);

    let safeFilePath;
    try {
      safeFilePath = requireSafePath(filePath, planDir, 'todo file', { allowAbsolute: true });
    } catch {
      continue;
    }

    const content = platformReadSync(safeFilePath);
    if (content === null) continue;

    const fm = extractFrontmatter(content);

    // Extract first line of body after frontmatter
    const bodyMatch = content.replace(/^---[\s\S]*?---\n?/, '');
    const firstLine = bodyMatch.trim().split('\n')[0] || '';
    const summary = sanitizeForDisplay(firstLine.slice(0, 100));

    results.push({
      filename: sanitizeForDisplay(entry.name),
      priority: sanitizeForDisplay(String(fm.priority || '')),
      area: sanitizeForDisplay(String(fm.area || '')),
      summary,
    });
  }

  if (mdFiles.length > 5) {
    results.push({ _remainder_count: mdFiles.length - 5 });
  }

  return results;
}

/**
 * Scan .planning/seeds/SEED-*.md for unimplemented seeds.
 * Unimplemented if status in ['dormant', 'active', 'triggered'].
 */
function scanSeeds(planDir) {
  const seedsDir = path.join(planDir, 'seeds');
  if (!fs.existsSync(seedsDir)) return [];

  let files;
  try {
    files = fs.readdirSync(seedsDir, { withFileTypes: true });
  } catch {
    return [{ scan_error: true }];
  }

  const unimplementedStatuses = new Set(['dormant', 'active', 'triggered']);
  const results = [];

  for (const entry of files) {
    if (!entry.isFile()) continue;
    if (!entry.name.startsWith('SEED-') || !entry.name.endsWith('.md')) continue;

    const filePath = path.join(seedsDir, entry.name);

    let safeFilePath;
    try {
      safeFilePath = requireSafePath(filePath, planDir, 'seed file', { allowAbsolute: true });
    } catch {
      continue;
    }

    const content = platformReadSync(safeFilePath);
    if (content === null) continue;

    const fm = extractFrontmatter(content);
    const status = (fm.status || 'dormant').toLowerCase();

    if (!unimplementedStatuses.has(status)) continue;

    // Extract seed_id from filename or frontmatter
    const seedIdMatch = entry.name.match(/^(SEED-[\w-]+)\.md$/);
    const seed_id = seedIdMatch ? seedIdMatch[1] : path.basename(entry.name, '.md');
    const slug = sanitizeForDisplay(seed_id.replace(/^SEED-/, ''));

    let title = sanitizeForDisplay(String(fm.title || ''));
    if (!title) {
      const headingMatch = content.match(/^#\s*(.+)$/m);
      if (headingMatch) title = sanitizeForDisplay(headingMatch[1].trim().slice(0, 100));
    }

    results.push({
      seed_id: sanitizeForDisplay(seed_id),
      slug,
      status: sanitizeForDisplay(status),
      title,
    });
  }

  return results;
}

// Terminal UAT states: `complete` (legacy) and `resolved` (post-gap-closure
// per workflows/execute-phase.md). Hoisted outside scanUatGaps so the Set is
// not recreated on each loop iteration.
const TERMINAL_UAT_STATUSES = new Set(['complete', 'resolved']);

/**
 * Scan .planning/phases for UAT gaps (UAT files with status != 'complete').
 */
function scanUatGaps(planDir) {
  const phasesDir = path.join(planDir, 'phases');
  if (!fs.existsSync(phasesDir)) return [];

  let dirs;
  try {
    dirs = fs.readdirSync(phasesDir, { withFileTypes: true })
      .filter(e => e.isDirectory())
      .map(e => e.name)
      .sort();
  } catch {
    return [{ scan_error: true }];
  }

  const results = [];

  for (const dir of dirs) {
    const phaseDir = path.join(phasesDir, dir);
    const phaseMatch = dir.match(/^(\d+[A-Z]?(?:\.\d+)*)/i);
    const phaseNum = phaseMatch ? phaseMatch[1] : dir;

    let files;
    try {
      files = fs.readdirSync(phaseDir);
    } catch {
