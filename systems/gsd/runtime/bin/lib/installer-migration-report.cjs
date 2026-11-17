'use strict';

// Resolution environment variable surface for #3541 — when the installer
// runs without a TTY (typical /gsd:update path via Claude Code or any
// scripted update), prompt-user migration actions cannot be answered
// interactively. We resolve them by classification:
//   - Stale SDK build artifacts (get-shit-done/sdk/{dist,src}/gsd-*):
//     default `remove`. Fresh install supplies replacements.
//   - User-facing skill anchors (skills/gsd-*/SKILL.md): default `keep`.
//     User-owned content is preserved.
// Anything else: fall through to the hard assertion with an improved,
// grouped, actionable error message.
//
// docs/installer-migrations.md#prompt-user-resolution for the spec.
const RESOLUTION_ENV_VAR = 'GSD_INSTALLER_MIGRATION_RESOLVE';
const VALID_CHOICES = ['keep', 'remove'];

function installerMigrationActionLabel(action) {
  if (!action || !action.type) return 'skipped';
  if (action.type === 'backup-and-remove') return 'backed up and removed';
  if (action.type === 'remove-managed') return 'removed';
  if (action.type === 'rewrite-json') return action.deleteIfEmpty ? 'rewrote or removed' : 'rewrote';
  if (action.type === 'record-baseline') return 'recorded';
  if (action.type === 'baseline-preserve-user') return 'preserved';
  if (action.type === 'preserve-user') return 'preserved';
  if (action.type === 'prompt-user') return 'blocked';
  return 'skipped';
}

function blockedInstallerMigrationActions(result) {
  if (result && Array.isArray(result.blocked)) return result.blocked;
  const plan = result && result.plan;
  if (plan && Array.isArray(plan.blocked)) return plan.blocked;
  return [];
}

function baselineSummaryLabel(count, noun) {
  return `${count} ${noun}${count === 1 ? '' : 's'}`;
}

function baselineSummaryRow(type, actions) {
  const count = actions.length;
  if (type === 'record-baseline') {
    return {
      label: 'recorded',
      relPath: baselineSummaryLabel(count, 'managed baseline file'),
      reason: 'first-time baseline scan',
      action: { type: 'record-baseline-summary', count, actions },
    };
  }
  return {
    label: 'preserved',
    relPath: baselineSummaryLabel(count, 'user baseline file'),
    reason: 'first-time baseline scan',
    action: { type: 'baseline-preserve-user-summary', count, actions },
  };
}

function summarizeInstallerMigrationResult(result) {
  const plan = result && result.plan;
  const actions = plan && Array.isArray(plan.actions) ? plan.actions : [];
  const blocked = blockedInstallerMigrationActions(result);
  const blockedSet = new Set(blocked);
  const rows = [];
  const baselineIndexes = new Map();
  const baselineActions = new Map();

  for (const action of actions) {
    const type = action && action.type;
    if (type === 'record-baseline' || type === 'baseline-preserve-user') {
      if (!baselineActions.has(type)) {
        baselineActions.set(type, []);
        baselineIndexes.set(type, rows.length);
        rows.push(null);
      }
      baselineActions.get(type).push(action);
      continue;
    }

    rows.push({
      label: blockedSet.has(action) ? 'blocked' : installerMigrationActionLabel(action),
      relPath: action.relPath,
      reason: action.reason || '',
      action,
    });
  }

  // Phase 4 requires action reporting without flooding first-time baseline installs:
  // docs/installer-migrations.md#phase-4-installupdate-integration.
  for (const [type, baselineRows] of baselineActions) {
    rows[baselineIndexes.get(type)] = baselineSummaryRow(type, baselineRows);
  }

  return {
    hasReportableActions: actions.length > 0 || blocked.length > 0,
    blocked,
    rows,
  };
}

// #3628: explicit whitelist of bundled hook files shipped in the npm
// distribution under `hooks/`. The classifier-based auto-removal of these
// files at first-time-baseline scan (added in #3610) is restricted to this
// set — a shape regex like `^hooks/gsd-[^/]+\.(?:js|sh|cjs|mjs)$` also
// matches user-authored custom hooks and retired bundled hooks from prior
// versions, and auto-removing those is silent data loss.
//
// The bug-3628 regression guard asserts this Set stays aligned with the
// on-disk `hooks/` directory in both directions: whitelist-but-missing
// AND shipped-but-not-whitelisted both fail CI.
const BUNDLED_GSD_HOOK_FILES = Object.freeze(new Set([
  'hooks/gsd-check-update-worker.js',
  'hooks/gsd-check-update.js',
  'hooks/gsd-context-monitor.js',
  'hooks/gsd-graphify-update.sh',
  'hooks/gsd-phase-boundary.sh',
  'hooks/gsd-prompt-guard.js',
  'hooks/gsd-read-guard.js',
  'hooks/gsd-read-injection-scanner.js',
  'hooks/gsd-session-state.sh',
  'hooks/gsd-statusline.js',
  'hooks/gsd-update-banner.js',
  'hooks/gsd-validate-commit.sh',
  'hooks/gsd-workflow-guard.js',
]));

// Classify a blocked prompt-user action into one of the safe-default
// categories. Returns null when no safe default applies — caller must
// fall back to the hard assertion / interactive prompt for those.
//
// Stale SDK build artifacts live under get-shit-done/sdk/{dist,src}/
// and are regenerated on every install, so removing them is lossless.
// User-facing skill anchors are the .md files that surface as commands
// to the user — these are user-owned and must be kept.
function classifyPromptUserAction(action) {
  const relPath = action && action.relPath;
  if (typeof relPath !== 'string' || !relPath) return null;
  if (/^get-shit-done\/sdk\/(dist|src)\//.test(relPath)) {
    return { category: 'stale-sdk-build-artifact', choice: 'remove' };
  }
  if (/^skills\/gsd-[^/]+\/SKILL\.md$/.test(relPath)) {
    return { category: 'user-facing-skill', choice: 'keep' };
  }
  // #3610 / #3628: bundled GSD hooks shipped under `hooks/`. The whitelist
  // is the explicit set of filenames in the npm distribution — files that
  // match the shape but are NOT in the whitelist (user-authored hooks,
  // retired hooks from prior versions) fall through to the block-or-prompt
  // flow so the user retains control. On a first-time-baseline scan the
  // installer can safely remove whitelisted hooks because it is about to
