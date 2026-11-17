/**
 * Workstream — CRUD operations for workstream namespacing
 *
 * Workstreams enable parallel milestones by scoping ROADMAP.md, STATE.md,
 * REQUIREMENTS.md, and phases/ into .planning/workstreams/{name}/ directories.
 *
 * When no workstreams/ directory exists, GSD operates in "flat mode" with
 * everything at .planning/ — backward compatible with pre-workstream installs.
 */

const fs = require('fs');
const path = require('path');
const { output, error, toPosixPath, getMilestoneInfo, generateSlugInternal } = require('./core.cjs');
const { platformWriteSync, platformEnsureDir } = require('./shell-command-projection.cjs');
const { planningRoot, setActiveWorkstream, getActiveWorkstream } = require('./planning-workspace.cjs');
const { toWorkstreamSlug, hasInvalidPathSegment, isValidActiveWorkstreamName } = require('./workstream-name-policy.cjs');
const { formatGsdSlash, resolveRuntime } = require('./runtime-slash.cjs');
const {
  getOtherActiveWorkstreamInventories,
  inspectWorkstream,
  listWorkstreamInventories,
} = require('./workstream-inventory.cjs');

// ─── Migration ──────────────────────────────────────────────────────────────

/**
 * Migrate flat .planning/ layout to workstream mode.
 * Moves per-workstream files (ROADMAP.md, STATE.md, REQUIREMENTS.md, phases/)
 * into .planning/workstreams/{name}/. Shared files (PROJECT.md, config.json,
 * milestones/, research/, codebase/, todos/) stay in place.
 */
function migrateToWorkstreams(cwd, workstreamName) {
  if (!workstreamName || hasInvalidPathSegment(workstreamName)) {
    throw new Error('Invalid workstream name for migration');
  }

  const baseDir = planningRoot(cwd);
  const wsDir = path.join(baseDir, 'workstreams', workstreamName);

  if (fs.existsSync(path.join(baseDir, 'workstreams'))) {
    throw new Error('Already in workstream mode — .planning/workstreams/ exists');
  }

  const toMove = [
    { name: 'ROADMAP.md', type: 'file' },
    { name: 'STATE.md', type: 'file' },
    { name: 'REQUIREMENTS.md', type: 'file' },
    { name: 'phases', type: 'dir' },
  ];

  platformEnsureDir(wsDir);

  const filesMoved = [];
  try {
    for (const item of toMove) {
      const src = path.join(baseDir, item.name);
      if (fs.existsSync(src)) {
        const dest = path.join(wsDir, item.name);
        fs.renameSync(src, dest);
        filesMoved.push(item.name);
      }
    }
  } catch (err) {
    for (const name of filesMoved) {
      try { fs.renameSync(path.join(wsDir, name), path.join(baseDir, name)); } catch {}
    }
    try { fs.rmSync(wsDir, { recursive: true }); } catch {}
    try { fs.rmdirSync(path.join(baseDir, 'workstreams')); } catch {}
    throw err;
  }

  return { migrated: true, workstream: workstreamName, files_moved: filesMoved };
}

// ─── CRUD Commands ──────────────────────────────────────────────────────────

function cmdWorkstreamCreate(cwd, name, options, raw) {
  if (!name) {
    error('workstream name required. Usage: workstream create <name>');
  }

  const slug = toWorkstreamSlug(name);
  if (!slug) {
    error('Invalid workstream name — must contain at least one alphanumeric character');
  }

  const baseDir = planningRoot(cwd);
  if (!fs.existsSync(baseDir)) {
    error(`.planning/ directory not found — run ${formatGsdSlash('new-project', resolveRuntime(cwd))} first`);
  }

  const wsRoot = path.join(baseDir, 'workstreams');
  const wsDir = path.join(wsRoot, slug);

  if (fs.existsSync(wsDir) && fs.existsSync(path.join(wsDir, 'STATE.md'))) {
    output({ created: false, error: 'already_exists', workstream: slug, path: toPosixPath(path.relative(cwd, wsDir)) }, raw);
    return;
  }

  const isFlatMode = !fs.existsSync(wsRoot);
  let migration = null;
  if (isFlatMode && options.migrate !== false) {
    const hasExistingWork = fs.existsSync(path.join(baseDir, 'ROADMAP.md')) ||
                            fs.existsSync(path.join(baseDir, 'STATE.md')) ||
                            fs.existsSync(path.join(baseDir, 'phases'));

    if (hasExistingWork) {
      const migrateName = options.migrateName || null;
      let existingWsName;
      if (migrateName) {
        existingWsName = toWorkstreamSlug(migrateName);
        if (!existingWsName) {
          output({
            created: false,
            error: 'migration_failed',
            message: 'Invalid migrate-name — must contain at least one alphanumeric character',
          }, raw);
          return;
        }
      } else {
        try {
          const milestone = getMilestoneInfo(cwd);
          existingWsName = generateSlugInternal(milestone.name) || 'default';
        } catch {
          existingWsName = 'default';
        }
      }

      try {
        migration = migrateToWorkstreams(cwd, existingWsName);
      } catch (e) {
        output({ created: false, error: 'migration_failed', message: e.message }, raw);
        return;
      }
    } else {
      platformEnsureDir(wsRoot);
    }
  }

  platformEnsureDir(wsDir);
  platformEnsureDir(path.join(wsDir, 'phases'));

  const today = new Date().toISOString().split('T')[0];
  const stateContent = [
    '---',
    `workstream: ${slug}`,
    `created: ${today}`,
    '---',
    '',
    '# Project State',
    '',
    '## Current Position',
    '**Status:** Not started',
    '**Current Phase:** None',
    `**Last Activity:** ${today}`,
