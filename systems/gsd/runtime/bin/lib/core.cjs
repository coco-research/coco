/**
 * Core — Shared utilities, constants, and internal helpers
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execGit, platformWriteSync, platformReadSync, platformEnsureDir } = require('./shell-command-projection.cjs');
const { MODEL_PROFILES, AGENT_TO_PHASE_TYPE, VALID_PHASE_TYPES, AGENT_DEFAULT_TIERS, VALID_AGENT_TIERS, nextTier } = require('./model-profiles.cjs');
const { MODEL_ALIAS_MAP, RUNTIME_PROFILE_MAP, KNOWN_RUNTIMES, RUNTIMES_WITH_REASONING_EFFORT } = require('./model-catalog.cjs');
const {
  resolveWorktreeContext,
  parseWorktreePorcelain: parseWorktreePorcelainPolicy,
  planWorktreePrune,
  executeWorktreePrunePlan,
  inspectWorktreeHealth,
} = require('./worktree-safety.cjs');
// Compatibility shim: new imports should use planning-workspace.cjs directly.
const {
  planningDir,
  planningRoot,
  planningPaths,
  withPlanningLock,
  getActiveWorkstream,
  setActiveWorkstream,
  findContextMdIn,
} = require('./planning-workspace.cjs');
const { findProjectRoot } = require('./project-root.generated.cjs');

// ─── Configuration Module (generated CJS mirror) ────────────────────────────
// Cycle 4: import canonical defaults + normalization primitives from the
// generated module; core.cjs no longer carries its own inline literal or its
// own migration logic. The exported CONFIG_DEFAULTS remains a flat-key object
// (shape unchanged) so legacy consumers (config.cjs, verify.cjs, tests) require
// no changes. Values are sourced from the canonical nested manifest.
const {
  CONFIG_DEFAULTS: CANONICAL_CONFIG_DEFAULTS,
  normalizeLegacyKeys,
} = require('./configuration.generated.cjs');

// ─── Path helpers ────────────────────────────────────────────────────────────

/** Normalize a relative path to always use forward slashes (cross-platform). */
function toPosixPath(p) {
  return p.split(path.sep).join('/');
}

/**
 * Scan immediate child directories for separate git repos.
 * Returns a sorted array of directory names that have their own `.git`.
 * Excludes hidden directories and node_modules.
 */
function detectSubRepos(cwd) {
  const results = [];
  try {
    const entries = fs.readdirSync(cwd, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
      const gitPath = path.join(cwd, entry.name, '.git');
      try {
        if (fs.existsSync(gitPath)) {
          results.push(entry.name);
        }
      } catch {}
    }
  } catch {}
  return results.sort();
}

// findProjectRoot is now re-exported from the generated CJS module above.

// ─── Output helpers ───────────────────────────────────────────────────────────

/**
 * Remove stale gsd-* temp files/dirs older than maxAgeMs (default: 5 minutes).
 * Runs opportunistically before each new temp file write to prevent unbounded accumulation.
 * @param {string} prefix - filename prefix to match (e.g., 'gsd-')
 * @param {object} opts
 * @param {number} opts.maxAgeMs - max age in ms before removal (default: 5 min)
 * @param {boolean} opts.dirsOnly - if true, only remove directories (default: false)
 */
/**
 * Dedicated GSD temp directory: path.join(os.tmpdir(), 'gsd').
 * Created on first use. Keeps GSD temp files isolated from the system
 * temp directory so reap scans only GSD files (#1975).
 */
const GSD_TEMP_DIR = path.join(require('os').tmpdir(), 'gsd');

function ensureGsdTempDir() {
  platformEnsureDir(GSD_TEMP_DIR);
}

function reapStaleTempFiles(prefix = 'gsd-', { maxAgeMs = 5 * 60 * 1000, dirsOnly = false } = {}) {
  try {
    ensureGsdTempDir();
    const now = Date.now();
    const entries = fs.readdirSync(GSD_TEMP_DIR);
    for (const entry of entries) {
      if (!entry.startsWith(prefix)) continue;
      const fullPath = path.join(GSD_TEMP_DIR, entry);
      try {
        const stat = fs.statSync(fullPath);
        if (now - stat.mtimeMs > maxAgeMs) {
          if (stat.isDirectory()) {
            fs.rmSync(fullPath, { recursive: true, force: true });
          } else if (!dirsOnly) {
            fs.unlinkSync(fullPath);
          }
        }
      } catch {
        // File may have been removed between readdir and stat — ignore
      }
    }
  } catch {
    // Non-critical — don't let cleanup failures break output
  }
}

function output(result, raw, rawValue) {
  let data;
  if (raw && rawValue !== undefined) {
    data = String(rawValue);
  } else {
    const json = JSON.stringify(result, null, 2);
    // Large payloads exceed Claude Code's Bash tool buffer (~50KB).
    // Write to tmpfile and output the path prefixed with @file: so callers can detect it.
    if (json.length > 50000) {
      reapStaleTempFiles();
      ensureGsdTempDir();
      const tmpPath = path.join(GSD_TEMP_DIR, `gsd-${Date.now()}.json`);
      platformWriteSync(tmpPath, json);
      data = '@file:' + tmpPath;
    } else {
      data = json;
    }
  }
  // process.stdout.write() is async when stdout is a pipe — process.exit()
  // can tear down the process before the reader consumes the buffer.
  // fs.writeSync(1, ...) blocks until the kernel accepts the bytes, and
  // skipping process.exit() lets the event loop drain naturally.
  fs.writeSync(1, data);
}

/**
 * Frozen enum of typed reason codes used by error() for structured errors.
 * Each subcommand contributes its own codes; the enum exists so tests can
 * assert against typed values instead of grepping stderr (#2974).
 *
 * Adding a new code:
 *   - Pick a snake_case lowercase value (the JSON wire form)
 *   - Group by subsystem prefix (CONFIG_*, SDK_*, etc)
 *   - Pass it to error(msg, ERROR_REASON.NEW_CODE) at the call site
 */
const ERROR_REASON = Object.freeze({
  // config-get / config-set
  CONFIG_KEY_NOT_FOUND: 'config_key_not_found',
  CONFIG_NO_FILE: 'config_no_file',
  CONFIG_PARSE_FAILED: 'config_parse_failed',
  CONFIG_INVALID_KEY: 'config_invalid_key',
  // SDK / gsd-tools dispatch
  SDK_FAIL_FAST: 'sdk_fail_fast',
  SDK_UNKNOWN_COMMAND: 'sdk_unknown_command',
  SDK_MISSING_ARG: 'sdk_missing_arg',
  // workflow / phase
  PHASE_NOT_FOUND: 'phase_not_found',
  SUMMARY_NO_PLANNING: 'summary_no_planning',
  // graphify
  GRAPHIFY_NO_GRAPH: 'graphify_no_graph',
  GRAPHIFY_INVALID_QUERY: 'graphify_invalid_query',
  // hooks
  HOOKS_OPT_OUT: 'hooks_opt_out',
  // security-scan
  SECURITY_SCAN_FAILED: 'security_scan_failed',
  // generic
  USAGE: 'usage',
  UNKNOWN: 'unknown',
});

/**
 * Process-level flag: when true, error() emits structured JSON to stderr
 * instead of plain "Error: <message>" text. Set by gsd-tools.cjs when the
 * CLI is invoked with `--json-errors`. Tests opt in to typed-IR error
 * assertions by passing that flag and parsing the JSON.
 *
 * Default off so existing callers and human operators keep their plain-text
 * diagnostics. The structured form is opt-in for tooling and tests (#2974).
 */
let _jsonErrorMode = false;
function setJsonErrorMode(v) { _jsonErrorMode = !!v; }
function getJsonErrorMode() { return _jsonErrorMode; }

/**
 * Emit an error and exit. When the second argument is provided it must be
 * a value from ERROR_REASON; tests can assert on `result.reason`. When the
 * process is in JSON-error mode, stderr receives `{ ok: false, reason,
 * message }` so callers can parse it; otherwise stderr keeps the plain
 * text form for human operators.
 */
function error(message, reason = ERROR_REASON.UNKNOWN) {
  if (_jsonErrorMode) {
    const payload = JSON.stringify({ ok: false, reason, message }) + '\n';
    fs.writeSync(2, payload);
  } else {
    fs.writeSync(2, 'Error: ' + message + '\n');
  }
  process.exit(1);
}

// ─── File & Config utilities ──────────────────────────────────────────────────

/**
 * Canonical config defaults — flat-key projection for CJS consumers.
 *
 * Cycle 4: Values are sourced from CANONICAL_CONFIG_DEFAULTS (the nested
 * manifest loaded by configuration.generated.cjs). The flat shape is
 * preserved here so legacy consumers (config.cjs, verify.cjs, tests that
 * regex-parse this source) continue to work without changes. The key names
 * and the `const CONFIG_DEFAULTS = {` pattern are intentionally kept.
 *
 * Mapping notes:
 *  - workflow.plan_check  → plan_checker (CJS flat name; verify.cjs uses this)
 *  - git.*               → flat git keys (branching_strategy, templates)
 *  - workflow.*          → flat names (research, verifier, …)
 *  - planning.sub_repos  → sub_repos
 *  - planning.commit_docs / search_gitignored → top-level flat keys
 */
const CONFIG_DEFAULTS = {
  model_profile: CANONICAL_CONFIG_DEFAULTS.model_profile,
  commit_docs: CANONICAL_CONFIG_DEFAULTS.commit_docs,
  search_gitignored: CANONICAL_CONFIG_DEFAULTS.search_gitignored,
  branching_strategy: CANONICAL_CONFIG_DEFAULTS.git.branching_strategy,
  phase_branch_template: CANONICAL_CONFIG_DEFAULTS.git.phase_branch_template,
  milestone_branch_template: CANONICAL_CONFIG_DEFAULTS.git.milestone_branch_template,
  quick_branch_template: CANONICAL_CONFIG_DEFAULTS.git.quick_branch_template,
  research: CANONICAL_CONFIG_DEFAULTS.workflow.research,
  plan_checker: CANONICAL_CONFIG_DEFAULTS.workflow.plan_check, // flat CJS name maps to workflow.plan_check
  verifier: CANONICAL_CONFIG_DEFAULTS.workflow.verifier,
  nyquist_validation: CANONICAL_CONFIG_DEFAULTS.workflow.nyquist_validation,
  ai_integration_phase: CANONICAL_CONFIG_DEFAULTS.workflow.ai_integration_phase,
  parallelization: CANONICAL_CONFIG_DEFAULTS.parallelization,
  brave_search: CANONICAL_CONFIG_DEFAULTS.brave_search,
  firecrawl: CANONICAL_CONFIG_DEFAULTS.firecrawl,
  exa_search: CANONICAL_CONFIG_DEFAULTS.exa_search,
  text_mode: CANONICAL_CONFIG_DEFAULTS.workflow.text_mode,
  sub_repos: CANONICAL_CONFIG_DEFAULTS.planning.sub_repos,
  resolve_model_ids: CANONICAL_CONFIG_DEFAULTS.resolve_model_ids,
  context_window: CANONICAL_CONFIG_DEFAULTS.context_window,
  phase_naming: CANONICAL_CONFIG_DEFAULTS.phase_naming,
  project_code: CANONICAL_CONFIG_DEFAULTS.project_code,
  subagent_timeout: CANONICAL_CONFIG_DEFAULTS.workflow.subagent_timeout,
  security_enforcement: CANONICAL_CONFIG_DEFAULTS.workflow.security_enforcement,
  security_asvs_level: CANONICAL_CONFIG_DEFAULTS.workflow.security_asvs_level,
  security_block_on: CANONICAL_CONFIG_DEFAULTS.workflow.security_block_on,
  post_planning_gaps: CANONICAL_CONFIG_DEFAULTS.workflow.post_planning_gaps,
};

/**
 * Deep-merge two plain config objects. `overlay` wins on key conflict.
 * Explicit `null` in overlay overrides base (null means "unset this key").
 * Arrays are replaced, not merged. Non-object primitives use overlay value.
 *
 * Note: `undefined` in overlay is treated as "no value provided" and falls
 * back to base (preserves inheritance). Explicit `null` overrides base.
 */
function _deepMergeConfig(base, overlay) {
  if (overlay === null || overlay === undefined) return overlay;
  if (typeof base !== 'object' || typeof overlay !== 'object') return overlay;
  const result = { ...base };
  for (const key of Object.keys(overlay)) {
    if (overlay[key] !== null && typeof overlay[key] === 'object' && !Array.isArray(overlay[key])) {
      result[key] = _deepMergeConfig(base[key] ?? {}, overlay[key]);
    } else {
      result[key] = overlay[key];
    }
  }
  return result;
}

function loadConfig(cwd, options = {}) {
  const activeWorkstream = Object.prototype.hasOwnProperty.call(options, 'workstream')
    ? options.workstream
    : (process.env.GSD_WORKSTREAM || null);
  // When GSD_WORKSTREAM is set, load root config first so workstream config
  // can inherit from it. This prevents users from duplicating model_overrides,
  // workflow.*, etc. across every workstream config (#2714).
  const ws = activeWorkstream;
  let rootParsed = null;
  if (ws) {
    const rootConfigPath = path.join(planningRoot(cwd), 'config.json');
    try {
      const raw = platformReadSync(rootConfigPath);
      if (raw === null) throw new Error('missing');
      rootParsed = JSON.parse(raw);
      // Cycle 4: delegate all legacy-key normalization to the Configuration Module.
      // normalizeLegacyKeys handles branching_strategy → git.branching_strategy,
      // sub_repos → planning.sub_repos, multiRepo, and depth → granularity.
      const { parsed: rootNormalized, normalizations: rootNorms } = normalizeLegacyKeys(rootParsed);
      if (rootNorms.length > 0) {
        // Resolve filesystem-dependent normalizations (multiRepo → planning.sub_repos)
        for (const norm of rootNorms) {
          if (norm.requiresFilesystem && !rootNormalized.planning?.sub_repos) {
            const detected = detectSubRepos(cwd);
            if (detected.length > 0) {
              if (!rootNormalized.planning) rootNormalized.planning = {};
              rootNormalized.planning.sub_repos = detected;
              rootNormalized.planning.commit_docs = false;
            }
          }
        }
        rootParsed = rootNormalized;
        try { platformWriteSync(rootConfigPath, JSON.stringify(rootParsed, null, 2)); } catch {}
      } else {
        rootParsed = rootNormalized;
      }
    } catch {
