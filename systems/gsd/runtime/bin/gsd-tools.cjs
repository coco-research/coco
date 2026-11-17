#!/usr/bin/env node

/**
 * @deprecated The supported programmatic surface is `gsd-sdk query` (SDK query registry)
 * and the `@gsd-build/sdk` package. This Node CLI remains the compatibility implementation
 * for shell scripts and older workflows; prefer calling the SDK from agents and automation.
 *
 * GSD Tools — CLI utility for GSD workflow operations
 *
 * Replaces repetitive inline bash patterns across ~50 GSD command/workflow/agent files.
 * Centralizes: config parsing, model resolution, phase lookup, git commits, summary verification.
 *
 * Usage: node gsd-tools.cjs <command> [args] [--raw] [--pick <field>]
 *
 * Atomic Commands:
 *   state load                         Load project config + state
 *   state json                         Output STATE.md frontmatter as JSON
 *   state update <field> <value>       Update a STATE.md field
 *   state get [section]                Get STATE.md content or section
 *   state patch --field val ...        Batch update STATE.md fields
 *   state begin-phase --phase N --name S --plans C  Update STATE.md for new phase start
 *   state signal-waiting --type T --question Q --options "A|B" --phase P  Write WAITING.json signal
 *   state signal-resume                Remove WAITING.json signal
 *   resolve-model <agent-type>         Get model for agent based on profile
 *   find-phase <phase>                 Find phase directory by number
 *   commit <message> [--files f1 f2] [--no-verify]   Commit planning docs
 *   commit-to-subrepo <msg> --files f1 f2  Route commits to sub-repos
 *   verify-summary <path>              Verify a SUMMARY.md file
 *   generate-slug <text>               Convert text to URL-safe slug
 *   current-timestamp [format]         Get timestamp (full|date|filename)
 *   list-todos [area]                  Count and enumerate pending todos
 *   verify-path-exists <path>          Check file/directory existence
 *   config-ensure-section              Initialize .planning/config.json
 *   history-digest                     Aggregate all SUMMARY.md data
 *   summary-extract <path> [--fields]  Extract structured data from SUMMARY.md
 *   state-snapshot                     Structured parse of STATE.md
 *   phase-plan-index <phase>           Index plans with waves and status
 *   websearch <query>                  Search web via Brave API (if configured)
 *     [--limit N] [--freshness day|week|month]
 *
 * Phase Operations:
 *   phase next-decimal <phase>         Calculate next decimal phase number
 *   phase add <description> [--id ID]   Append new phase to roadmap + create dir
 *   phase insert <after> <description> Insert decimal phase after existing
 *   phase remove <phase> [--force]     Remove phase, renumber all subsequent
 *   phase complete <phase>             Mark phase done, update state + roadmap
 *
 * Roadmap Operations:
 *   roadmap get-phase <phase>          Extract phase section from ROADMAP.md
 *   roadmap analyze                    Full roadmap parse with disk status
 *   roadmap update-plan-progress <N>   Update progress table row from disk (PLAN vs SUMMARY counts)
 *   roadmap annotate-dependencies <N>  Add wave dependency notes + cross-cutting constraints to ROADMAP.md
 *
 * Requirements Operations:
 *   requirements mark-complete <ids>   Mark requirement IDs as complete in REQUIREMENTS.md
 *                                      Accepts: REQ-01,REQ-02 or REQ-01 REQ-02 or [REQ-01, REQ-02]
 *
 * Milestone Operations:
 *   milestone complete <version>       Archive milestone, create MILESTONES.md
 *     [--name <name>]
 *     [--archive-phases]               Move phase dirs to milestones/vX.Y-phases/
 *
 * Validation:
 *   validate consistency               Check phase numbering, disk/roadmap sync
 *   validate health [--repair]         Check .planning/ integrity, optionally repair
 *   validate agents                    Check GSD agent installation status
 *
 * Progress:
 *   progress [json|table|bar]          Render progress in various formats
 *
 * Todos:
 *   todo complete <filename>           Move todo from pending to completed
 *
 * UAT Audit:
 *   audit-uat                           Scan all phases for unresolved UAT/verification items
 *   uat render-checkpoint --file <path> Render the current UAT checkpoint block
 *
 * Open Artifact Audit:
 *   audit-open [--json]                 Scan all .planning/ artifact types for unresolved items
 *
 * Intel:
 *   intel query <term>             Query intel files for a term
 *   intel status                   Show intel file freshness
 *   intel update                   Trigger intel refresh (returns agent spawn hint)
 *   intel diff                     Show changed intel entries since last snapshot
 *   intel snapshot                 Save current intel state as diff baseline
 *   intel patch-meta <file>        Update _meta.updated_at in an intel file
 *   intel validate                 Validate intel file structure
 *   intel extract-exports <file>   Extract exported symbols from a source file
 *
 * Scaffolding:
 *   scaffold context --phase <N>       Create CONTEXT.md template
 *   scaffold uat --phase <N>           Create UAT.md template
 *   scaffold verification --phase <N>  Create VERIFICATION.md template
 *   scaffold phase-dir --phase <N>     Create phase directory
 *     --name <name>
 *
 * Frontmatter CRUD:
 *   frontmatter get <file> [--field k] Extract frontmatter as JSON
 *   frontmatter set <file> --field k   Update single frontmatter field
 *     --value jsonVal
 *   frontmatter merge <file>           Merge JSON into frontmatter
 *     --data '{json}'
 *   frontmatter validate <file>        Validate required fields
 *     --schema plan|summary|verification
 *
 * Verification Suite:
 *   verify plan-structure <file>       Check PLAN.md structure + tasks
 *   verify phase-completeness <phase>  Check all plans have summaries
 *   verify references <file>           Check @-refs + paths resolve
 *   verify commits <h1> [h2] ...      Batch verify commit hashes
 *   verify artifacts <plan-file>       Check must_haves.artifacts
 *   verify key-links <plan-file>       Check must_haves.key_links
 *   verify schema-drift <phase> [--skip]  Detect schema file changes without push
 *   verify codebase-drift                Detect structural drift since last codebase map (#2003)
 *
 * Template Fill:
 *   template fill summary --phase N    Create pre-filled SUMMARY.md
 *     [--plan M] [--name "..."]
 *     [--fields '{json}']
 *   template fill plan --phase N       Create pre-filled PLAN.md
 *     [--plan M] [--type execute|tdd]
 *     [--wave N] [--fields '{json}']
 *   template fill verification         Create pre-filled VERIFICATION.md
 *     --phase N [--fields '{json}']
 *
 * State Progression:
 *   state advance-plan                 Increment plan counter
 *   state record-metric --phase N      Record execution metrics
 *     --plan M --duration Xmin
 *     [--tasks N] [--files N]
 *   state update-progress              Recalculate progress bar
 *   state add-decision --summary "..."  Add decision to STATE.md
 *     [--phase N] [--rationale "..."]
 *     [--summary-file path] [--rationale-file path]
 *   state add-blocker --text "..."     Add blocker
 *     [--text-file path]
 *   state resolve-blocker --text "..." Remove blocker
 *   state record-session               Update session continuity
 *     --stopped-at "..."
 *     [--resume-file path]
 *
 * Compound Commands (workflow-specific initialization):
 *   init execute-phase <phase>         All context for execute-phase workflow
 *   init plan-phase <phase>            All context for plan-phase workflow
 *   init new-project                   All context for new-project workflow
 *   init new-milestone                 All context for new-milestone workflow
 *   init quick <description>           All context for quick workflow
 *   init resume                        All context for resume-project workflow
 *   init verify-work <phase>           All context for verify-work workflow
 *   init phase-op <phase>              Generic phase operation context
 *   init todos [area]                  All context for todo workflows
 *   init milestone-op                  All context for milestone operations
 *   init map-codebase                  All context for map-codebase workflow
 *   init progress                      All context for progress workflow
 *
 * Documentation:
 *   docs-init                            Project context for docs-update workflow
 *
 * Learnings:
 *   learnings list                       List all global learnings (JSON)
 *   learnings query --tag <tag>          Query learnings by tag
 *   learnings copy                       Copy from current project's LEARNINGS.md
 *   learnings prune --older-than <dur>   Remove entries older than duration (e.g. 90d)
 *   learnings delete <id>                Delete a learning by ID
 *
 * GSD-2 Migration:
 *   from-gsd2 [--path <dir>] [--force] [--dry-run]
 *             Import a GSD-2 (.gsd/) project back to GSD v1 (.planning/) format
 */

const fs = require('fs');
const path = require('path');
const core = require('./lib/core.cjs');
const { error, findProjectRoot, ERROR_REASON } = core;
const { getActiveWorkstream } = require('./lib/planning-workspace.cjs');
const { resolveActiveWorkstream, applyResolvedWorkstreamEnv } = require('./lib/active-workstream-store.cjs');
const state = require('./lib/state.cjs');
const phase = require('./lib/phase.cjs');
const roadmap = require('./lib/roadmap.cjs');
const verify = require('./lib/verify.cjs');
const config = require('./lib/config.cjs');
const template = require('./lib/template.cjs');
const milestone = require('./lib/milestone.cjs');
const commands = require('./lib/commands.cjs');
const init = require('./lib/init.cjs');
const frontmatter = require('./lib/frontmatter.cjs');
const profilePipeline = require('./lib/profile-pipeline.cjs');
const profileOutput = require('./lib/profile-output.cjs');
const workstream = require('./lib/workstream.cjs');
const docs = require('./lib/docs.cjs');
const learnings = require('./lib/learnings.cjs');
const gapChecker = require('./lib/gap-checker.cjs');
const { routeStateCommand } = require('./lib/state-command-router.cjs');
const { routeVerifyCommand } = require('./lib/verify-command-router.cjs');
const { routeInitCommand } = require('./lib/init-command-router.cjs');
const { routePhaseCommand } = require('./lib/phase-command-router.cjs');
const { routePhasesCommand } = require('./lib/phases-command-router.cjs');
const { routeValidateCommand } = require('./lib/validate-command-router.cjs');
const { routeRoadmapCommand } = require('./lib/roadmap-command-router.cjs');

// ─── SDK bridge (Phase 6 inline family / non-family delegation) ───────────────
// For inline case blocks that have SDK counterparts (frontmatter, config, and
// non-family commands), we attempt to dispatch via executeForCjs (the sync
// bridge). CJS handlers are retained as fallback when SDK is unavailable.
//
// NOTE: migrate-config, detect-custom-files, config-path, and find-phase
// are CJS-native special cases; see comments inline.

// Shared loader for the synchronous SDK runtime bridge; see
// `bin/lib/cjs-sdk-bridge.cjs`. All canonical-command CJS dispatchers (the
// per-family routers and the non-family helper below) consume the same loader
// so a change to the SDK-load contract lands in one place.
const { tryLoadSdk: _tryLoadSdkBridge, getExecuteForCjs } = require('./lib/cjs-sdk-bridge.cjs');

/**
 * Attempt SDK dispatch for a non-family command.
 *
 * Returns true when the SDK was available and handled the command (success or
 * typed error). Returns false when the SDK is unavailable, signalling the
 * caller to fall through to the CJS handler.
 *
 * @param {object} opts
 * @param {string} opts.registryCommand - canonical command name in the SDK registry
 * @param {string[]} opts.registryArgs - args to pass to the SDK handler
 * @param {string} opts.legacyCommand - original gsd-tools command name (for error messages)
 * @param {string[]} opts.legacyArgs - original args (for error messages)
 * @param {string} opts.cwd - project dir
 * @param {boolean} opts.raw - raw output mode
 * @param {Function} opts.error - error reporter
 * @param {Function} opts.output - output emitter (core.output)
 */
function _dispatchNonFamily({ registryCommand, registryArgs, legacyCommand, legacyArgs, cwd, raw, error, output }) {
  if (!_tryLoadSdkBridge()) return false;
  const result = getExecuteForCjs()({
    registryCommand,
    registryArgs,
    legacyCommand,
    legacyArgs,
    // Always request typed JSON from the bridge; CJS `output(data, raw)` handles
    // user-facing rendering. Passing `mode: 'raw'` would make the bridge
    // pre-render result.data to a JSON string that the CJS output path then
    // double-stringifies (returning a JSON string of a JSON string).
    mode: 'json',
    projectDir: cwd,
    workstream: process.env.GSD_WORKSTREAM || undefined,
  });
  if (!result.ok) {
    const message = (result.errorDetails && result.errorDetails.message)
      || `${legacyCommand} (${registryCommand}) failed (${result.errorKind})`;
    // Propagate the structured reason code through to CJS `error()` so the
    // `--json-errors` JSON-shaped stderr carries the typed reason (e.g.
    // 'config_key_not_found') instead of the generic 'unknown'.  Handlers
    // tag the GSDError with `.reason` and the worker forwards it via
    // errorDetails.reason. (Bugs #2943, #3086.)
    const reason = result.errorDetails && result.errorDetails.reason;
    if (reason) {
      error(message, reason);
    } else {
      error(message);
    }
    return true; // handled (error reported)
  }
  // CJS parity for --raw output (config.cjs:525 `output(value, raw, String(value))`):
  // when the caller asked for --raw and the SDK returned a scalar, pass that
  // scalar through as `rawValue` so core.output() emits the bare string
  // representation instead of JSON-stringifying it.  Non-scalar shapes fall
  // through to the structured JSON path, matching `output(obj, raw)`.
  const data = result.data;
  if (raw && (typeof data === 'string' || typeof data === 'number' || typeof data === 'boolean')) {
    output(data, raw, String(data));
  } else {
    output(data, raw);
  }
  return true;
}

// ─── Arg parsing helpers ──────────────────────────────────────────────────────

/**
 * Extract named --flag <value> pairs from an args array.
 * Returns an object mapping flag names to their values (null if absent).
 * Flags listed in `booleanFlags` are treated as boolean (no value consumed).
 *
 * parseNamedArgs(args, 'phase', 'plan')        → { phase: '3', plan: '1' }
 * parseNamedArgs(args, [], ['amend', 'force'])  → { amend: true, force: false }
 */
function parseNamedArgs(args, valueFlags = [], booleanFlags = []) {
  const result = {};
  for (const flag of valueFlags) {
    const idx = args.indexOf(`--${flag}`);
    result[flag] = idx !== -1 && args[idx + 1] !== undefined && !args[idx + 1].startsWith('--')
      ? args[idx + 1]
      : null;
  }
  for (const flag of booleanFlags) {
    result[flag] = args.includes(`--${flag}`);
  }
  return result;
}

/**
 * Collect all tokens after --flag until the next --flag or end of args.
 * Handles multi-word values like --name Foo Bar Version 1.
 * Returns null if the flag is absent.
 */
function parseMultiwordArg(args, flag) {
  const idx = args.indexOf(`--${flag}`);
  if (idx === -1) return null;
  const tokens = [];
  for (let i = idx + 1; i < args.length; i++) {
    if (args[i].startsWith('--')) break;
    tokens.push(args[i]);
  }
  return tokens.length > 0 ? tokens.join(' ') : null;
}

// ─── CLI Router ───────────────────────────────────────────────────────────────

async function main() {
  let args = process.argv.slice(2);

  // --json-errors / GSD_JSON_ERRORS=1: when active, error() emits structured
  // JSON ({ ok: false, reason: <ERROR_REASON code>, message }) to stderr
  // instead of "Error: <text>". Lets test suites assert on typed reason codes
  // per CONTRIBUTING.md "Prohibited: Raw Text Matching" (#2974).
  //
  // Detect early — before any flag parsing that can fire error() — so even
  // --cwd and workstream-resolution failures emit structured stderr (#3310).
  // The argv splice must happen here too, otherwise the dispatcher below sees
  // "--json-errors" as an unknown command. Default off — human operators keep
  // their plain-text diagnostic.
  const jsonErrorsIdx = args.indexOf('--json-errors');
  if (jsonErrorsIdx !== -1) {
    core.setJsonErrorMode(true);
    args.splice(jsonErrorsIdx, 1);
  } else if (process.env.GSD_JSON_ERRORS === '1') {
    core.setJsonErrorMode(true);
  }

  // Optional cwd override for sandboxed subagents running outside project root.
  let cwd = process.cwd();
  const cwdEqArg = args.find(arg => arg.startsWith('--cwd='));
  const cwdIdx = args.indexOf('--cwd');
  if (cwdEqArg) {
    const value = cwdEqArg.slice('--cwd='.length).trim();
    if (!value) error('Missing value for --cwd', ERROR_REASON.USAGE);
    args.splice(args.indexOf(cwdEqArg), 1);
    cwd = path.resolve(value);
  } else if (cwdIdx !== -1) {
    const value = args[cwdIdx + 1];
    if (!value || value.startsWith('--')) error('Missing value for --cwd', ERROR_REASON.USAGE);
    args.splice(cwdIdx, 2);
    cwd = path.resolve(value);
  }

  if (!fs.existsSync(cwd) || !fs.statSync(cwd).isDirectory()) {
    error(`Invalid --cwd: ${cwd}`, ERROR_REASON.USAGE);
  }

  // Resolve worktree root: in a linked worktree, .planning/ lives in the main worktree.
  // However, in monorepo worktrees where the subdirectory itself owns .planning/,
  // skip worktree resolution — the CWD is already the correct project root.
  const { resolveWorktreeRoot } = require('./lib/core.cjs');
  if (!fs.existsSync(path.join(cwd, '.planning'))) {
    const worktreeRoot = resolveWorktreeRoot(cwd);
    if (worktreeRoot !== cwd) {
      cwd = worktreeRoot;
    }
  }

  // Optional workstream override for parallel milestone work.
  // Priority: --ws flag > GSD_WORKSTREAM env var > session/shared pointer > null.
  let ws = null;
  try {
    const wsResolution = resolveActiveWorkstream(cwd, args, process.env, {
      getStored: getActiveWorkstream,
    });
    ws = wsResolution.ws;
    args = wsResolution.args;
    // Set env var so all modules (planningDir, planningPaths) auto-resolve workstream paths.
    applyResolvedWorkstreamEnv(wsResolution, process.env);
  } catch (err) {
    error(err.message || String(err));
  }

  const rawIndex = args.indexOf('--raw');
  const raw = rawIndex !== -1;
  if (rawIndex !== -1) args.splice(rawIndex, 1);

  // --pick <name>: extract a single field from JSON output (replaces jq dependency).
  // Supports dot-notation (e.g., --pick workflow.research) and bracket notation
  // for arrays (e.g., --pick directories[-1]).
  const pickIdx = args.indexOf('--pick');
  let pickField = null;
  if (pickIdx !== -1) {
    pickField = args[pickIdx + 1];
    if (!pickField || pickField.startsWith('--')) error('Missing value for --pick', ERROR_REASON.USAGE);
    args.splice(pickIdx, 2);
  }

  // --default <value>: for config-get, return this value instead of erroring
  // when the key is absent. Allows workflows to express optional config reads
  // without defensive `2>/dev/null || true` boilerplate (#1893).
  const defaultIdx = args.indexOf('--default');
  let defaultValue = undefined;
  if (defaultIdx !== -1) {
    defaultValue = args[defaultIdx + 1];
    if (defaultValue === undefined) defaultValue = '';
    args.splice(defaultIdx, 2);
  }

  let command = args[0];

  // #3243: accept dotted canonical form (e.g. `state.update`) as well as the
  // spaced form (`state update`). Workflow files and stale SDK binaries pass
  // the dotted canonical form directly; any caller that bypasses the SDK
  // client-side split hit "Unknown command" before this shim.
  //
  // Split on the FIRST dot only — `check.decision-coverage-plan` becomes
  // command='check', args=['check','decision-coverage-plan',...rest].
  // Parallel to dottedCommandToCjsArgv in sdk/src/query/query-fallback-bridge-adapter.ts;
  // kept separate here to avoid SDK coupling (see TODO: extract to shared helper).
  //
  // Guard: head and rest must both be non-empty (rejects leading-dot args like
  // ".hidden" and bare-dot ".").
  const originalCommand = command; // preserved for "Unknown command" suggestion
  if (typeof command === 'string' && command.includes('.')) {
    const dotIdx = command.indexOf('.');
    const head = command.slice(0, dotIdx);
    const rest = command.slice(dotIdx + 1);
    if (head && rest) {
      command = head;
      args = [head, rest, ...args.slice(1)];
    }
  }

  // Top-level usage string — emitted by `gsd-tools` (no args) and by
  // `gsd-tools --help` / any `--help` request below.
  // CR feedback: the command list must enumerate every top-level command
  // supported by the dispatcher so `--help` is actually useful for
  // discovery; previously it was a partial subset that didn't include
