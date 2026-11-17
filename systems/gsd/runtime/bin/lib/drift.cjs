/**
 * Codebase Drift Detection (#2003)
 *
 * Detects structural drift between a committed codebase and the
 * `.planning/codebase/STRUCTURE.md` map produced by `gsd-codebase-mapper`.
 *
 * Four categories of drift element:
 *   - new_dir    → a newly-added file whose directory prefix does not appear
 *                  in STRUCTURE.md
 *   - barrel     → a newly-added barrel export at
 *                  (packages|apps)/<name>/src/index.(ts|tsx|js|mjs|cjs)
 *   - migration  → a newly-added migration file under one of the recognized
 *                  migration directories (supabase, prisma, drizzle, src/migrations, …)
 *   - route      → a newly-added route module under a `routes/` or `api/` dir
 *
 * Each file is counted at most once; when a file matches multiple categories
 * the most specific category wins (migration > route > barrel > new_dir).
 *
 * Design decisions (see PR for full rubber-duck):
 *   - The library is pure. It takes parsed git diff output and returns a
 *     structured result. The CLI/workflow layer is responsible for running
 *     git and for spawning mappers.
 *   - `last_mapped_commit` is stored as YAML-style frontmatter at the top of
 *     each `.planning/codebase/*.md` file. This keeps the baseline attached
 *     to the file, survives git moves, and avoids a sidecar JSON.
 *   - The detector NEVER throws on malformed input — it returns a
 *     `{ skipped: true }` result. The phase workflow depends on this
 *     non-blocking guarantee.
 */

'use strict';

const fs = require('node:fs');
const { platformWriteSync } = require('./shell-command-projection.cjs');

// ─── Constants ───────────────────────────────────────────────────────────────

const DRIFT_CATEGORIES = Object.freeze(['new_dir', 'barrel', 'migration', 'route']);

// Category priority when a single file matches multiple rules.
// Higher index = more specific = wins.
const CATEGORY_PRIORITY = { new_dir: 0, barrel: 1, route: 2, migration: 3 };

const BARREL_RE = /^(packages|apps)\/[^/]+\/src\/index\.(ts|tsx|js|mjs|cjs)$/;

const MIGRATION_RES = [
  /^supabase\/migrations\/.+\.sql$/,
  /^prisma\/migrations\/.+/,
  /^drizzle\/meta\/.+/,
  /^drizzle\/migrations\/.+/,
  /^src\/migrations\/.+\.(ts|js|sql)$/,
  /^db\/migrations\/.+\.(sql|ts|js)$/,
  /^migrations\/.+\.(sql|ts|js)$/,
];

const ROUTE_RES = [
  /^(apps|packages)\/[^/]+\/src\/routes\/.+\.(ts|tsx|js|jsx|mjs|cjs)$/,
  /^src\/routes\/.+\.(ts|tsx|js|jsx|mjs|cjs)$/,
  /^src\/api\/.+\.(ts|tsx|js|jsx|mjs|cjs)$/,
  /^(apps|packages)\/[^/]+\/src\/api\/.+\.(ts|tsx|js|jsx|mjs|cjs)$/,
];

// A conservative allowlist for `--paths` arguments passed to the mapper:
// repo-relative path components separated by /, containing only
// alphanumerics, dash, underscore, and dot (no `..`, no `/..`).
const SAFE_PATH_RE = /^(?!.*\.\.)(?:[A-Za-z0-9_.][A-Za-z0-9_.\-]*)(?:\/[A-Za-z0-9_.][A-Za-z0-9_.\-]*)*$/;

// ─── Classification ──────────────────────────────────────────────────────────

/**
 * Classify a single file path into a drift category or null.
 *
 * @param {string} file - repo-relative path, forward slashes.
 * @returns {'barrel'|'migration'|'route'|null}
 */
function classifyFile(file) {
  if (typeof file !== 'string' || !file) return null;
  const norm = file.replace(/\\/g, '/');
  if (MIGRATION_RES.some((r) => r.test(norm))) return 'migration';
  if (ROUTE_RES.some((r) => r.test(norm))) return 'route';
  if (BARREL_RE.test(norm)) return 'barrel';
  return null;
}

