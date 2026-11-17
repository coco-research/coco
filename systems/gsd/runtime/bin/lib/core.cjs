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
      // Root config missing or unparseable — workstream config stands alone
    }
  }

  const configPath = path.join(planningDir(cwd, ws), 'config.json');
  const defaults = CONFIG_DEFAULTS;

  try {
    const raw = platformReadSync(configPath);
    if (raw === null) throw new Error('missing');
    // `fileData` is the parsed content of the config.json file on disk — used
    // for migrations and writes so we never persist merged values back to disk.
    const fileData = JSON.parse(raw);

    // Cycle 4: Single normalizeLegacyKeys call replaces all four inline migration
    // blocks (depth→granularity, multiRepo→planning.sub_repos, sub_repos→planning.sub_repos,
    // branching_strategy→git.branching_strategy). The Module is pure (no I/O); disk
    // writeback is handled below with the existing platformWriteSync pattern.
    // Note: migrateOnDisk from the Module is async; loadConfig is sync — so we
    // call normalizeLegacyKeys inline and do the writeback at the call site.
    // Per brief §4.3: "use normalizeLegacyKeys directly and do writeback inline."
    let configDirty = false;
    {
      const { parsed: normalized, normalizations } = normalizeLegacyKeys(fileData);
      if (normalizations.length > 0) {
        // Merge normalized values back into fileData (mutation-in-place for legacy code below)
        Object.keys(fileData).forEach(k => delete fileData[k]);
        Object.assign(fileData, normalized);
        configDirty = true;
        // Resolve filesystem-dependent normalizations (multiRepo → planning.sub_repos).
        // Guard: only populate sub_repos from filesystem if not already set by normalization
        // AND the original file didn't have sub_repos already (preserve existing intent).
        for (const norm of normalizations) {
          if (norm.requiresFilesystem && !fileData.planning?.sub_repos) {
            const detected = detectSubRepos(cwd);
            if (detected.length > 0) {
              if (!fileData.planning) fileData.planning = {};
              fileData.planning.sub_repos = detected;
              fileData.planning.commit_docs = false;
            }
          }
        }
      }
    }

    // Keep planning.sub_repos in sync with actual filesystem
    const currentSubRepos = fileData.planning?.sub_repos || [];
    if (Array.isArray(currentSubRepos) && currentSubRepos.length > 0) {
      const detected = detectSubRepos(cwd);
      if (detected.length > 0) {
        const sorted = [...currentSubRepos].sort();
        if (JSON.stringify(sorted) !== JSON.stringify(detected)) {
          if (!fileData.planning) fileData.planning = {};
          fileData.planning.sub_repos = detected;
          configDirty = true;
        }
      }
    }

    // Persist sub_repos changes (migration or sync) — write only the on-disk
    // file contents, never the merged result, to avoid polluting workstream configs.
    if (configDirty) {
      try { platformWriteSync(configPath, JSON.stringify(fileData, null, 2)); } catch {}
    }

    // Now apply root→workstream inheritance. `parsed` is the effective config
    // used for value extraction below; fileData is kept for disk writes only.
    const parsed = rootParsed ? _deepMergeConfig(rootParsed, fileData) : fileData;

    // Warn about unrecognized top-level keys so users don't silently lose config.
    // Derived from config-set's VALID_CONFIG_KEYS (canonical source) plus internal-only
    // keys that loadConfig handles but config-set doesn't expose. This avoids maintaining
    // a hardcoded duplicate that drifts when new config keys are added.
    // DYNAMIC_KEY_PATTERNS supplies topLevel for each pattern so adding a new
    // dynamic-pattern namespace to config-schema.cjs automatically updates this set
    // — no more drift between the read side and the write side (#2687).
    const { VALID_CONFIG_KEYS, DYNAMIC_KEY_PATTERNS } = require('./config-schema.cjs');
    const KNOWN_TOP_LEVEL = new Set([
      // Extract top-level key names from dot-notation paths (e.g., 'workflow.research' → 'workflow')
      ...[...VALID_CONFIG_KEYS].map(k => k.split('.')[0]),
      // Dynamic-pattern top-level containers (e.g. review, model_profile_overrides)
      ...DYNAMIC_KEY_PATTERNS.map(p => p.topLevel),
      // Internal keys loadConfig reads but config-set doesn't expose
      'model_overrides', 'context_window', 'resolve_model_ids', 'claude_md_path',
      // Deprecated keys (still accepted for migration, not in config-set)
      // 'branching_strategy' is kept here as a safety net: it is migrated to
      // git.branching_strategy above (#3523), but on the first read of a root
      // config that feeds into a workstream merge, `parsed` may still surface it.
      'depth', 'multiRepo', 'branching_strategy',
    ]);
    const unknownKeys = Object.keys(parsed).filter(k => !KNOWN_TOP_LEVEL.has(k));
    if (unknownKeys.length > 0) {
      // Deduplicate: a single `init phase-op N` invocation calls loadConfig twice
      // (once for the sub-command setup, once for git-config resolution). Guard with
      // a module-level Set so the same message never fires more than once per process.
      const warnKey = unknownKeys.join(',');
      if (!_warnedUnknownConfigKeys.has(warnKey)) {
        _warnedUnknownConfigKeys.add(warnKey);
        process.stderr.write(
          `gsd-tools: warning: unknown config key(s) in .planning/config.json: ${unknownKeys.join(', ')} — these will be ignored\n`
        );
      }
    }

    // #2517 — Validate runtime/tier values for keys that loadConfig handles but
    // can be edited directly into config.json (bypassing config-set's enum check).
    // This catches typos like `runtime: "codx"` and `model_profile_overrides.codex.banana`
    // at read time without rejecting back-compat values from new runtimes
    // (review findings #10, #13).
    _warnUnknownProfileOverrides(parsed, '.planning/config.json');

    const get = (key, nested) => {
      if (parsed[key] !== undefined) return parsed[key];
      if (nested && parsed[nested.section] && parsed[nested.section][nested.field] !== undefined) {
        return parsed[nested.section][nested.field];
      }
      return undefined;
    };

    const parallelization = (() => {
      const val = get('parallelization');
      if (typeof val === 'boolean') return val;
      if (typeof val === 'object' && val !== null && 'enabled' in val) return val.enabled;
      return defaults.parallelization;
    })();

    return {
      model_profile: get('model_profile') ?? defaults.model_profile,
      commit_docs: (() => {
        const explicit = get('commit_docs', { section: 'planning', field: 'commit_docs' });
        // If explicitly set in config, respect the user's choice
        if (explicit !== undefined) return explicit;
        // Auto-detection: when no explicit value and .planning/ is gitignored,
        // default to false instead of true
        if (isGitIgnored(cwd, '.planning/')) return false;
        return defaults.commit_docs;
      })(),
      search_gitignored: get('search_gitignored', { section: 'planning', field: 'search_gitignored' }) ?? defaults.search_gitignored,
      branching_strategy: get('branching_strategy', { section: 'git', field: 'branching_strategy' }) ?? defaults.branching_strategy,
      phase_branch_template: get('phase_branch_template', { section: 'git', field: 'phase_branch_template' }) ?? defaults.phase_branch_template,
      milestone_branch_template: get('milestone_branch_template', { section: 'git', field: 'milestone_branch_template' }) ?? defaults.milestone_branch_template,
      quick_branch_template: get('quick_branch_template', { section: 'git', field: 'quick_branch_template' }) ?? defaults.quick_branch_template,
      research: get('research', { section: 'workflow', field: 'research' }) ?? defaults.research,
      plan_checker: get('plan_checker', { section: 'workflow', field: 'plan_check' }) ?? defaults.plan_checker,
      verifier: get('verifier', { section: 'workflow', field: 'verifier' }) ?? defaults.verifier,
      nyquist_validation: get('nyquist_validation', { section: 'workflow', field: 'nyquist_validation' }) ?? defaults.nyquist_validation,
      post_planning_gaps: get('post_planning_gaps', { section: 'workflow', field: 'post_planning_gaps' }) ?? defaults.post_planning_gaps,
      parallelization,
      brave_search: get('brave_search') ?? defaults.brave_search,
      firecrawl: get('firecrawl') ?? defaults.firecrawl,
      exa_search: get('exa_search') ?? defaults.exa_search,
      tdd_mode: get('tdd_mode', { section: 'workflow', field: 'tdd_mode' }) ?? false,
      mvp_mode: get('mvp_mode', { section: 'workflow', field: 'mvp_mode' }) ?? false,
      text_mode: get('text_mode', { section: 'workflow', field: 'text_mode' }) ?? defaults.text_mode,
      auto_advance: get('auto_advance', { section: 'workflow', field: 'auto_advance' }) ?? false,
      _auto_chain_active: get('_auto_chain_active', { section: 'workflow', field: '_auto_chain_active' }) ?? false,
      mode: get('mode') ?? 'interactive',
      sub_repos: get('sub_repos', { section: 'planning', field: 'sub_repos' }) ?? defaults.sub_repos,
      resolve_model_ids: get('resolve_model_ids') ?? defaults.resolve_model_ids,
      context_window: get('context_window') ?? defaults.context_window,
      phase_naming: get('phase_naming') ?? defaults.phase_naming,
      project_code: get('project_code') ?? defaults.project_code,
      subagent_timeout: get('subagent_timeout', { section: 'workflow', field: 'subagent_timeout' }) ?? defaults.subagent_timeout,
      model_overrides: parsed.model_overrides || null,
      // #3023 — per-phase-type model map. Six named slots
      // (planning/discuss/research/execution/verification/completion).
      // Resolves between per-agent override and profile-derived tier in
      // resolveModelInternal. Defaults to null so configs without it
      // behave exactly as today.
      models: parsed.models || null,
      // #3024 — dynamic routing block. When `enabled: true`, the
      // resolveModelForTier() resolver picks tier_models[default_tier]
      // for the agent and escalates one tier per attempt up to
      // max_escalations. Disabled by default for backward compat.
      dynamic_routing: parsed.dynamic_routing || null,
      // #2517 — runtime-aware profiles. `runtime` defaults to null (back-compat).
      // When null, resolveModelInternal preserves today's Claude-native behavior.
      // NOTE: `runtime` and `model_profile_overrides` are intentionally read
      // flat-only (not via `get()` with a workflow.X fallback) — they are
      // top-level keys per docs/CONFIGURATION.md. The lighter-touch decision
      // here was to document the constraint rather than introduce nested
      // resolution edge cases for two new keys (review finding #9). The
      // schema validation in `_warnUnknownProfileOverrides` runs against the
      // raw `parsed` blob, so direct `.planning/config.json` edits surface
      // unknown runtime/tier names at load time, not silently (review finding #10).
      runtime: parsed.runtime || null,
      model_profile_overrides: parsed.model_profile_overrides || null,
      agent_skills: parsed.agent_skills || {},
      manager: parsed.manager || {},
      response_language: get('response_language') || null,
      claude_md_path: get('claude_md_path') || null,
      claude_md_assembly: parsed.claude_md_assembly || null,
    };
  } catch {
    // Fall back to ~/.gsd/defaults.json only for truly pre-project contexts (#1683)
    // If .planning/ exists, the project is initialized — just missing config.json.
    // When GSD_WORKSTREAM is set and root config was loaded, the workstream config
    // doesn't exist — treat root config as the effective config for this workstream.
    if (fs.existsSync(planningDir(cwd, ws))) {
      if (rootParsed) {
        // Workstream has no config.json: re-parse using root config as the sole source.
        // Keep env immutable by explicitly reloading with workstream context cleared.
        return loadConfig(cwd, { workstream: null });
      }
      return defaults;
    }
    try {
      const home = process.env.GSD_HOME || os.homedir();
      const globalDefaultsPath = path.join(home, '.gsd', 'defaults.json');
      const raw = platformReadSync(globalDefaultsPath);
      if (raw === null) throw new Error('missing');
      const globalDefaults = JSON.parse(raw);
      return {
        ...defaults,
        model_profile: globalDefaults.model_profile ?? defaults.model_profile,
        commit_docs: globalDefaults.commit_docs ?? defaults.commit_docs,
        research: globalDefaults.research ?? defaults.research,
        plan_checker: globalDefaults.plan_checker ?? defaults.plan_checker,
        verifier: globalDefaults.verifier ?? defaults.verifier,
        nyquist_validation: globalDefaults.nyquist_validation ?? defaults.nyquist_validation,
        post_planning_gaps: globalDefaults.post_planning_gaps
          ?? globalDefaults.workflow?.post_planning_gaps
          ?? defaults.post_planning_gaps,
        parallelization: globalDefaults.parallelization ?? defaults.parallelization,
        text_mode: globalDefaults.text_mode ?? defaults.text_mode,
        resolve_model_ids: globalDefaults.resolve_model_ids ?? defaults.resolve_model_ids,
        context_window: globalDefaults.context_window ?? defaults.context_window,
        subagent_timeout: globalDefaults.subagent_timeout ?? defaults.subagent_timeout,
        model_overrides: globalDefaults.model_overrides || null,
        models: globalDefaults.models || null,
        dynamic_routing: globalDefaults.dynamic_routing || null,
        agent_skills: globalDefaults.agent_skills || {},
        response_language: globalDefaults.response_language || null,
      };
    } catch {
      return defaults;
    }
  }
}

// ─── Git utilities ────────────────────────────────────────────────────────────

// Module-level deduplication for unknown-key warnings (#3523).
// A single `init phase-op N` call invokes loadConfig more than once; this Set
// prevents the same warning from being echoed on each invocation.
const _warnedUnknownConfigKeys = new Set();

const _gitIgnoredCache = new Map();

function isGitIgnored(cwd, targetPath) {
  const key = cwd + '::' + targetPath;
  if (_gitIgnoredCache.has(key)) return _gitIgnoredCache.get(key);
  // --no-index checks .gitignore rules regardless of whether the file is tracked.
  // Without it, git check-ignore returns "not ignored" for tracked files even when
  // .gitignore explicitly lists them — a common source of confusion when .planning/
  // was committed before being added to .gitignore.
  // Array args (via the seam) prevent shell interpretation of special characters in
  // file paths — avoids command injection via crafted path names.
  const result = execGit(['check-ignore', '-q', '--no-index', '--', targetPath], { cwd });
  const ignored = result.exitCode === 0;
  _gitIgnoredCache.set(key, ignored);
  return ignored;
}

// ─── Common path helpers ──────────────────────────────────────────────────────

/**
 * Resolve the main worktree root when running inside a git worktree.
 * In a linked worktree, .planning/ lives in the main worktree, not in the linked one.
 * Returns the main worktree path, or cwd if not in a worktree.
 */
function resolveWorktreeRoot(cwd) {
  // Omit execGit so worktree-safety uses its own execGitDefault — that wrapper
  // delegates to the seam and derives the `timedOut` field that pruneResult
  // branches on below.
  const context = resolveWorktreeContext(cwd, {
    existsSync: fs.existsSync,
  });
  return context.effectiveRoot;
}

/**
 * Parse `git worktree list --porcelain` output into an array of
 * { path, branch } objects.  Entries with a detached HEAD (no branch line)
 * are skipped because we cannot safely reason about their merge status.
 *
 * @param {string} porcelain - raw output from git worktree list --porcelain
 * @returns {{ path: string, branch: string }[]}
 */
function parseWorktreePorcelain(porcelain) {
  return parseWorktreePorcelainPolicy(porcelain);
}

/**
 * Clear stale worktree metadata references via `git worktree prune`.
 *
 * Destructive linked-worktree removal is disabled by default for safety.
 *
 * @param {string} repoRoot - absolute path to the main (or any) worktree of
 *   the repository; used as `cwd` for git commands.
 * @returns {string[]} list of worktree paths that were removed (always empty)
 */
function pruneOrphanedWorktrees(repoRoot) {
  try {
    const plan = planWorktreePrune(
      repoRoot,
      { allowDestructive: false },
      { parseWorktreePorcelain }
    );
    const pruneResult = executeWorktreePrunePlan(plan);
    if (pruneResult && pruneResult.timedOut) {
      // AC2: surface structured warning instead of silently swallowing the timeout.
      // Uses process.stderr.write to match the [gsd-tools] WARNING prefix style.
      process.stderr.write(
        '[gsd-tools] WARNING: worktree health check degraded' +
        ' — git worktree prune timed out after 10s.' +
        ' Orphaned worktree metadata may remain until the next successful run.\n'
      );
    }
  } catch { /* never crash the caller */ }
  return [];
}

// ─── Planning workspace (pathing + active workstream + lock) moved to planning-workspace.cjs ───

// ─── Phase utilities ──────────────────────────────────────────────────────────

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function normalizePhaseName(phase) {
  const str = String(phase);
  // Strip optional project_code prefix (e.g., 'CK-01' → '01')
  const stripped = str.replace(/^[A-Z]{1,6}-(?=\d)/, '');
  // Standard numeric phases: 1, 01, 12A, 12.1
  const match = stripped.match(/^(\d+)([A-Z])?((?:\.\d+)*)/i);
  if (match) {
    const padded = match[1].padStart(2, '0');
    // Preserve original case of letter suffix (#1962).
    // Uppercasing causes directory/roadmap mismatches on case-sensitive filesystems
    // (e.g., "16c" in ROADMAP.md → directory "16C-name" → progress can't match).
    const letter = match[2] || '';
    const decimal = match[3] || '';
    return padded + letter + decimal;
  }
  // Custom phase IDs (e.g. PROJ-42, AUTH-101): return as-is
  return str;
}

/**
 * Render a regex source fragment matching a phase number against ROADMAP/STATE
 * prose regardless of zero-padding on either side. Skills pass the resolved
 * padded form (`02.7`), but human-authored ROADMAP prose is conventionally
 * un-padded (`### Phase 2.7:`); a naive `escapeRegex(phaseNum)` fragment never
 * matches when the two diverge. Strips leading zeros from the integer part
 * before re-emitting with a `0*` prefix, so the fragment matches both `2.7`
 * and `02.7` (and `002.7`).
 *
 * Falls back to `escapeRegex(phaseNum)` for non-numeric IDs (custom project
 * codes like `PROJ-42`) so callers can substitute it unconditionally.
 *
 * See #3537 — wired into every ROADMAP-prose regex builder.
 */
function phaseMarkdownRegexSource(phaseNum) {
  const stripped = String(phaseNum).replace(/^[A-Z]{1,6}-(?=\d)/i, '');
  const match = stripped.match(/^0*(\d+)([A-Z])?((?:\.\d+)*)$/i);
  if (!match) return escapeRegex(phaseNum);

  const integer = match[1].replace(/^0+/, '') || '0';
  const letter = match[2] ? escapeRegex(match[2]) : '';
  const decimal = match[3] ? escapeRegex(match[3]) : '';
  return `0*${escapeRegex(integer)}${letter}${decimal}`;
}

/**
 * #3599: when the caller passed a project-code-prefixed ID like `PROJ-42`,
 * return the exact-escaped form so the caller can search the ROADMAP for
 * `### Phase PROJ-42:` BEFORE falling back to the padding-tolerant numeric
 * form. Returns null when the input has no project-code prefix — in that
 * case the numeric form (`phaseMarkdownRegexSource`) is the only thing the
 * caller needs.
 *
 * Two-pass at the call site preserves the #3537 contract (`CK-01` directory
 * names mapping to `Phase 1:` prose) while letting `PROJ-42` resolve to its
 * own prefixed heading without cross-matching a bare `### Phase 42:` that
 * happens to share the trailing integer.
 */
function phaseMarkdownRegexSourceExact(phaseNum) {
  const raw = String(phaseNum);
  if (!/^[A-Z]{1,6}-(?=\d)/i.test(raw)) return null;
  return escapeRegex(raw);
}

function comparePhaseNum(a, b) {
  // Strip optional project_code prefix before comparing (e.g., 'CK-01-name' → '01-name')
  const sa = String(a).replace(/^[A-Z]{1,6}-/, '');
  const sb = String(b).replace(/^[A-Z]{1,6}-/, '');
  const pa = sa.match(/^(\d+)([A-Z])?((?:\.\d+)*)/i);
  const pb = sb.match(/^(\d+)([A-Z])?((?:\.\d+)*)/i);
  // If either is non-numeric (custom ID), fall back to string comparison
  if (!pa || !pb) return String(a).localeCompare(String(b));
  const intDiff = parseInt(pa[1], 10) - parseInt(pb[1], 10);
  if (intDiff !== 0) return intDiff;
  // No letter sorts before letter: 12 < 12A < 12B
  const la = (pa[2] || '').toUpperCase();
  const lb = (pb[2] || '').toUpperCase();
  if (la !== lb) {
    if (!la) return -1;
    if (!lb) return 1;
    return la < lb ? -1 : 1;
  }
  // Segment-by-segment decimal comparison: 12A < 12A.1 < 12A.1.2 < 12A.2
  const aDecParts = pa[3] ? pa[3].slice(1).split('.').map(p => parseInt(p, 10)) : [];
  const bDecParts = pb[3] ? pb[3].slice(1).split('.').map(p => parseInt(p, 10)) : [];
  const maxLen = Math.max(aDecParts.length, bDecParts.length);
  if (aDecParts.length === 0 && bDecParts.length > 0) return -1;
  if (bDecParts.length === 0 && aDecParts.length > 0) return 1;
  for (let i = 0; i < maxLen; i++) {
    const av = Number.isFinite(aDecParts[i]) ? aDecParts[i] : 0;
    const bv = Number.isFinite(bDecParts[i]) ? bDecParts[i] : 0;
    if (av !== bv) return av - bv;
  }
  return 0;
}

/**
 * Extract the phase token from a directory name.
 * Supports: '01-name', '1009A-name', '999.6-name', 'CK-01-name', 'PROJ-42-name'.
 * Returns the token portion (e.g. '01', '1009A', '999.6', 'PROJ-42') or the full name if no separator.
 */
function extractPhaseToken(dirName) {
  // Try project-code-prefixed numeric: CK-01-name → CK-01, CK-01A.2-name → CK-01A.2
  const codePrefixed = dirName.match(/^([A-Z]{1,6}-\d+[A-Z]?(?:\.\d+)*)(?:-|$)/i);
  if (codePrefixed) return codePrefixed[1];
  // Try plain numeric: 01-name, 1009A-name, 999.6-name
  const numeric = dirName.match(/^(\d+[A-Z]?(?:\.\d+)*)(?:-|$)/i);
  if (numeric) return numeric[1];
  // Custom IDs: PROJ-42-name → everything before the last segment that looks like a name
  const custom = dirName.match(/^([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)(?:-[a-z]|$)/i);
  if (custom) return custom[1];
  return dirName;
}

/**
 * Check if a directory name's phase token matches the normalized phase exactly.
 * Case-insensitive comparison for the token portion.
 */
function phaseTokenMatches(dirName, normalized) {
  const token = extractPhaseToken(dirName);
  if (token.toUpperCase() === normalized.toUpperCase()) return true;
  // Strip optional project_code prefix from dir and retry
  const stripped = dirName.replace(/^[A-Z]{1,6}-(?=\d)/i, '');
  if (stripped !== dirName) {
    const strippedToken = extractPhaseToken(stripped);
    if (strippedToken.toUpperCase() === normalized.toUpperCase()) return true;
  }
  return false;
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

function searchPhaseInDir(baseDir, relBase, normalized) {
  try {
    const dirs = readSubdirectories(baseDir, true);
    // Match: exact phase token comparison (not prefix matching)
    const match = dirs.find(d => phaseTokenMatches(d, normalized));
    if (!match) return null;

    // Extract phase number and name — supports numeric (01-name), project-code-prefixed (CK-01-name), and custom (PROJ-42-name)
    const dirMatch = match.match(/^(?:[A-Z]{1,6}-)(\d+[A-Z]?(?:\.\d+)*)-?(.*)/i)
      || match.match(/^(\d+[A-Z]?(?:\.\d+)*)-?(.*)/i)
      || match.match(/^([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)-(.+)/i)
      || [null, match, null];
    const phaseNumber = dirMatch ? dirMatch[1] : normalized;
    const phaseName = dirMatch && dirMatch[2] ? dirMatch[2] : null;
    const phaseDir = path.join(baseDir, match);
    const { plans: unsortedPlans, summaries: unsortedSummaries, hasResearch, hasContext, hasVerification, hasReviews } = getPhaseFileStats(phaseDir);
    const plans = unsortedPlans.sort();
    const summaries = unsortedSummaries.sort();

    const completedPlanIds = new Set(
      summaries.flatMap(s => {
        const exact = s.replace('-SUMMARY.md', '').replace('SUMMARY.md', '');
        const canonical = extractCanonicalPlanId(s);
        return canonical === exact ? [exact] : [exact, canonical];
      })
    );
    const incompletePlans = plans.filter(p => {
      const planId = p.replace('-PLAN.md', '').replace('PLAN.md', '');
      const canonical = extractCanonicalPlanId(p);
      return !completedPlanIds.has(planId) && !completedPlanIds.has(canonical);
    });

    return {
      found: true,
      directory: toPosixPath(path.join(relBase, match)),
      phase_number: phaseNumber,
      phase_name: phaseName,
      phase_slug: phaseName ? phaseName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : null,
      plans,
      summaries,
      incomplete_plans: incompletePlans,
      has_research: hasResearch,
      has_context: hasContext,
      has_verification: hasVerification,
      has_reviews: hasReviews,
    };
  } catch {
    return null;
  }
}

function findPhaseInternal(cwd, phase) {
  if (!phase) return null;

  const phasesDir = path.join(planningDir(cwd), 'phases');
  const normalized = normalizePhaseName(phase);

  // Search current phases first
  const relPhasesDir = toPosixPath(path.relative(cwd, phasesDir));
  const current = searchPhaseInDir(phasesDir, relPhasesDir, normalized);
  if (current) return current;

  // Search archived milestone phases (newest first)
  const milestonesDir = path.join(cwd, '.planning', 'milestones');
  if (!fs.existsSync(milestonesDir)) return null;

  try {
    const milestoneEntries = fs.readdirSync(milestonesDir, { withFileTypes: true });
    const archiveDirs = milestoneEntries
      .filter(e => e.isDirectory() && /^v[\d.]+-phases$/.test(e.name))
      .map(e => e.name)
      .sort()
      .reverse();

    for (const archiveName of archiveDirs) {
      const version = archiveName.match(/^(v[\d.]+)-phases$/)[1];
      const archivePath = path.join(milestonesDir, archiveName);
      const relBase = '.planning/milestones/' + archiveName;
      const result = searchPhaseInDir(archivePath, relBase, normalized);
      if (result) {
        result.archived = version;
        return result;
      }
    }
  } catch { /* intentionally empty */ }

  return null;
}

function getArchivedPhaseDirs(cwd) {
  const milestonesDir = path.join(cwd, '.planning', 'milestones');
  const results = [];

  if (!fs.existsSync(milestonesDir)) return results;

  try {
    const milestoneEntries = fs.readdirSync(milestonesDir, { withFileTypes: true });
    // Find v*-phases directories, sort newest first
    const phaseDirs = milestoneEntries
      .filter(e => e.isDirectory() && /^v[\d.]+-phases$/.test(e.name))
      .map(e => e.name)
      .sort()
      .reverse();

    for (const archiveName of phaseDirs) {
      const version = archiveName.match(/^(v[\d.]+)-phases$/)[1];
      const archivePath = path.join(milestonesDir, archiveName);
      const dirs = readSubdirectories(archivePath, true);

      for (const dir of dirs) {
        results.push({
          name: dir,
          milestone: version,
          basePath: path.join('.planning', 'milestones', archiveName),
          fullPath: path.join(archivePath, dir),
        });
      }
    }
  } catch { /* intentionally empty */ }

  return results;
}

// ─── Roadmap milestone scoping ───────────────────────────────────────────────

/**
 * Strip shipped milestone content wrapped in <details> blocks.
 * Used to isolate current milestone phases when searching ROADMAP.md
 * for phase headings or checkboxes — prevents matching archived milestone
 * phases that share the same numbers as current milestone phases.
 */
function stripShippedMilestones(content) {
  return content.replace(/<details>[\s\S]*?<\/details>/gi, '');
}

/**
 * Extract the current milestone section from ROADMAP.md by positive lookup.
 *
 * Instead of stripping <details> blocks (negative heuristic that breaks if
 * agents wrap the current milestone in <details>), this finds the section
 * matching the current milestone version and returns only that content.
 *
 * Falls back to stripShippedMilestones() if:
 * - cwd is not provided
 * - STATE.md doesn't exist or has no milestone field
 * - Version can't be found in ROADMAP.md
 *
 * @param {string} content - Full ROADMAP.md content
 * @param {string} [cwd] - Working directory for reading STATE.md
 * @returns {string} Content scoped to current milestone
 */
function extractCurrentMilestone(content, cwd) {
  if (!cwd) return stripShippedMilestones(content);

  // 1. Get current milestone version from STATE.md frontmatter
  let version = null;
  try {
    const statePath = path.join(planningDir(cwd), 'STATE.md');
    const stateRaw = platformReadSync(statePath);
    if (stateRaw !== null) {
      const milestoneMatch = stateRaw.match(/^milestone:\s*(.+)/m);
      if (milestoneMatch) {
        version = milestoneMatch[1].trim();
      }
    }
  } catch {}

  // 2. Fallback: derive version from getMilestoneInfo pattern in ROADMAP.md itself
  if (!version) {
    // Check for 🚧 in-progress marker
    const inProgressMatch = content.match(/🚧\s*\*\*v(\d+\.\d+)\s/);
    if (inProgressMatch) {
      version = 'v' + inProgressMatch[1];
    }
  }

  if (!version) return stripShippedMilestones(content);

  // 3. Find the section matching this version
  // Match headings like: ## Roadmap v3.0: Name, ## v3.0 Name, etc.
  const escapedVersion = escapeRegex(version);
  const sectionPattern = new RegExp(
    `(^#{1,3}\\s+.*${escapedVersion}[^\\n]*)`,
    'mi'
  );
  const sectionMatch = content.match(sectionPattern);

  if (!sectionMatch) return stripShippedMilestones(content);

  const sectionStart = sectionMatch.index;

  // Find the end: next milestone heading at same or higher level, or EOF.
  // Milestone headings look like: ## v2.0, ## Roadmap v2.0, ## ✅ v1.0, etc.
  // Scan line-by-line so that heading-like lines inside fenced code blocks
  // (``` or ~~~) are not mistaken for milestone boundaries. See #2787.
  const headingLevel = sectionMatch[1].match(/^(#{1,3})\s/)[1].length;
  const restContent = content.slice(sectionStart + sectionMatch[0].length);
  // Exclude phase headings (e.g. "### Phase 12: v1.0 Tech-Debt Closure") from
  // being treated as milestone boundaries just because they mention vX.Y in
  // the title. Phase headings always start with the literal `Phase `. See #2619.
  const nextMilestonePattern = new RegExp(
    `^#{1,${headingLevel}}\\s+(?!Phase\\s+\\S)(?:.*v\\d+\\.\\d+|✅|📋|🚧)`,
    'i'
  );

  let sectionEnd = content.length;
  let fenceChar = null;
  let fenceLen = 0;
  let charOffset = 0;
  for (const line of restContent.split('\n')) {
    const fenceMatch = line.match(/^\s{0,3}((?:`{3,}|~{3,}))(.*)/);
    if (fenceMatch) {
      const char = fenceMatch[1][0];
      const len = fenceMatch[1].length;
      const trailing = fenceMatch[2] || '';
      if (!fenceChar) {
        fenceChar = char;
        fenceLen = len;
      } else if (char === fenceChar && len >= fenceLen && /^\s*$/.test(trailing)) {
        fenceChar = null;
        fenceLen = 0;
      }
    } else if (!fenceChar && nextMilestonePattern.test(line)) {
      sectionEnd = sectionStart + sectionMatch[0].length + charOffset;
      break;
    }
    charOffset += line.length + 1;
  }

