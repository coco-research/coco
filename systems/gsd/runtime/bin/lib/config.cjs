/**
 * Config — Planning config CRUD operations
 */

const fs = require('fs');
const path = require('path');
const { output, error, ERROR_REASON, CONFIG_DEFAULTS } = require('./core.cjs');
const { platformWriteSync, platformEnsureDir } = require('./shell-command-projection.cjs');
const { planningDir, withPlanningLock } = require('./planning-workspace.cjs');
const {
  VALID_PROFILES,
  getAgentToModelMapForProfile,
  formatAgentToModelMapAsTable,
} = require('./model-profiles.cjs');
const { VALID_CONFIG_KEYS, isValidConfigKey } = require('./config-schema.cjs');
const { isSecretKey, maskSecret } = require('./secrets.cjs');
const { normalizeConfiguredDefaultReviewers } = require('./review-reviewer-selection.cjs');

const CONFIG_KEY_SUGGESTIONS = {
  'workflow.nyquist_validation_enabled': 'workflow.nyquist_validation',
  'agents.nyquist_validation_enabled': 'workflow.nyquist_validation',
  'nyquist.validation_enabled': 'workflow.nyquist_validation',
  'hooks.research_questions': 'workflow.research_before_questions',
  'workflow.research_questions': 'workflow.research_before_questions',
  'workflow.codereview': 'workflow.code_review',
  'workflow.review_command': 'workflow.code_review_command',
  'workflow.review': 'workflow.code_review',
  'workflow.code_review_level': 'workflow.code_review_depth',
  'workflow.review_depth': 'workflow.code_review_depth',
  'review.model': 'review.models.<cli-name>',
  'sub_repos': 'planning.sub_repos',
  'plan_checker': 'workflow.plan_check',
};

const SHIP_PR_BODY_SECTION_KEYS = new Set(['heading', 'enabled', 'source', 'fallback', 'template']);
const SHIP_PR_BODY_TEMPLATE_TOKENS = new Set([
  'phase_number',
  'phase_name',
  'phase_dir',
  'base_branch',
  'padded_phase',
]);
const SHIP_PR_BODY_SOURCE_RE = /^(ROADMAP|PLAN|SUMMARY|VERIFICATION|STATE|REQUIREMENTS|CONTEXT)\.md\s+##\s+[^\r\n#][^\r\n]*$/;

function validateKnownConfigKeyPath(keyPath) {
  const suggested = CONFIG_KEY_SUGGESTIONS[keyPath];
  if (suggested) {
    error(`Unknown config key: ${keyPath}. Did you mean ${suggested}?`, ERROR_REASON.CONFIG_INVALID_KEY);
  }
}

function validateShipPrBodySections(value) {
  if (!Array.isArray(value)) {
    error('Invalid ship.pr_body_sections value. Expected a JSON array of section objects.');
  }

  value.forEach((section, index) => {
    const prefix = `Invalid ship.pr_body_sections[${index}]`;
    if (!section || typeof section !== 'object' || Array.isArray(section)) {
      error(`${prefix}. Expected an object.`);
    }

    const unknownKeys = Object.keys(section).filter((key) => !SHIP_PR_BODY_SECTION_KEYS.has(key));
    if (unknownKeys.length > 0) {
      error(`${prefix}. Unknown field(s): ${unknownKeys.join(', ')}.`);
    }

    if (typeof section.heading !== 'string' || section.heading.trim() === '') {
      error(`${prefix}. heading must be a non-empty string.`);
    }
    if (/[\r\n]/.test(section.heading)) {
      error(`${prefix}. heading must be a single line.`);
    }

    if ('enabled' in section && typeof section.enabled !== 'boolean') {
      error(`${prefix}. enabled must be true or false.`);
    }

    for (const field of ['source', 'fallback', 'template']) {
      if (field in section && typeof section[field] !== 'string') {
        error(`${prefix}. ${field} must be a string.`);
      }
    }

    const hasContent = ['source', 'fallback', 'template'].some((field) => {
      return typeof section[field] === 'string' && section[field].trim() !== '';
    });
    if (!hasContent) {
      error(`${prefix}. Provide at least one of source, fallback, or template.`);
    }

    if (typeof section.source === 'string' && section.source.trim() !== '') {
      const selectors = section.source.split('||').map((selector) => selector.trim()).filter(Boolean);
      if (selectors.length === 0 || selectors.some((selector) => !SHIP_PR_BODY_SOURCE_RE.test(selector))) {
        error(`${prefix}. source must use selectors like "PLAN.md ## Risks", separated with "||".`);
      }
    }

    if (typeof section.template === 'string') {
      const tokens = section.template.matchAll(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g);
      for (const match of tokens) {
        if (!SHIP_PR_BODY_TEMPLATE_TOKENS.has(match[1])) {
          error(`${prefix}. Unsupported template token: {${match[1]}}.`);
        }
      }
    }
  });
}

/**
 * Build a fully-materialized config object for a new project.
 *
 * Merges (increasing priority):
 *   1. Hardcoded defaults — every key that loadConfig() resolves, plus mode/granularity
 *   2. User-level defaults from ~/.gsd/defaults.json (if present)
 *   3. userChoices — the settings the user explicitly selected during /gsd:new-project
 *
 * Uses the canonical `git` namespace for branching keys (consistent with VALID_CONFIG_KEYS
 * and the settings workflow). loadConfig() handles both flat and nested formats, so this
 * is backward-compatible with existing projects that have flat keys.
 *
 * Returns a plain object — does NOT write any files.
 */
function buildNewProjectConfig(userChoices) {
  const choices = userChoices || {};
  const homedir = require('os').homedir();

  // Detect API key availability
  const braveKeyFile = path.join(homedir, '.gsd', 'brave_api_key');
  const hasBraveSearch = !!(process.env.BRAVE_API_KEY || fs.existsSync(braveKeyFile));
  const firecrawlKeyFile = path.join(homedir, '.gsd', 'firecrawl_api_key');
  const hasFirecrawl = !!(process.env.FIRECRAWL_API_KEY || fs.existsSync(firecrawlKeyFile));
  const exaKeyFile = path.join(homedir, '.gsd', 'exa_api_key');
  const hasExaSearch = !!(process.env.EXA_API_KEY || fs.existsSync(exaKeyFile));

  // Load user-level defaults from ~/.gsd/defaults.json if available
  const globalDefaultsPath = path.join(homedir, '.gsd', 'defaults.json');
  let userDefaults = {};
  try {
    if (fs.existsSync(globalDefaultsPath)) {
      userDefaults = JSON.parse(fs.readFileSync(globalDefaultsPath, 'utf-8'));
      // Migrate deprecated "depth" key to "granularity"
      if ('depth' in userDefaults && !('granularity' in userDefaults)) {
        const depthToGranularity = { quick: 'coarse', standard: 'standard', comprehensive: 'fine' };
        userDefaults.granularity = depthToGranularity[userDefaults.depth] || userDefaults.depth;
        delete userDefaults.depth;
        try {
          platformWriteSync(globalDefaultsPath, JSON.stringify(userDefaults, null, 2));
        } catch { /* intentionally empty */ }
      }
    }
  } catch {
    // Ignore malformed global defaults
  }

  const hardcoded = {
    model_profile: CONFIG_DEFAULTS.model_profile,
    commit_docs: CONFIG_DEFAULTS.commit_docs,
    parallelization: CONFIG_DEFAULTS.parallelization,
    search_gitignored: CONFIG_DEFAULTS.search_gitignored,
    brave_search: hasBraveSearch,
    firecrawl: hasFirecrawl,
    exa_search: hasExaSearch,
    git: {
      branching_strategy: CONFIG_DEFAULTS.branching_strategy,
      create_tag: true,
      phase_branch_template: CONFIG_DEFAULTS.phase_branch_template,
      milestone_branch_template: CONFIG_DEFAULTS.milestone_branch_template,
      quick_branch_template: CONFIG_DEFAULTS.quick_branch_template,
    },
    workflow: {
      research: true,
      plan_check: true,
      verifier: true,
      nyquist_validation: true,
      auto_advance: false,
      node_repair: true,
      node_repair_budget: 2,
      ui_phase: true,
      ui_safety_gate: true,
      ai_integration_phase: true,
      tdd_mode: false,
      human_verify_mode: 'end-of-phase',
      text_mode: false,
      research_before_questions: false,
      discuss_mode: 'discuss',
      skip_discuss: false,
      code_review: true,
      code_review_depth: 'standard',
      code_review_command: null,
      pattern_mapper: true,
      plan_bounce: false,
      plan_bounce_script: null,
      plan_bounce_passes: 2,
      auto_prune_state: false,
      post_planning_gaps: CONFIG_DEFAULTS.post_planning_gaps,
      security_enforcement: CONFIG_DEFAULTS.security_enforcement,
      security_asvs_level: CONFIG_DEFAULTS.security_asvs_level,
      security_block_on: CONFIG_DEFAULTS.security_block_on,
    },
    ship: {
      pr_body_sections: [],
    },
    hooks: {
      context_warnings: true,
    },
    project_code: null,
    phase_naming: 'sequential',
    agent_skills: {},
    claude_md_path: './CLAUDE.md',
  };

  // Three-level deep merge: hardcoded <- userDefaults <- choices
  const config = {
    ...hardcoded,
    ...userDefaults,
    ...choices,
    git: {
      ...hardcoded.git,
      ...(userDefaults.git || {}),
      ...(choices.git || {}),
    },
    workflow: {
      ...hardcoded.workflow,
      ...(userDefaults.workflow || {}),
      ...(choices.workflow || {}),
    },
    ship: {
      ...hardcoded.ship,
      ...(userDefaults.ship || {}),
      ...(choices.ship || {}),
    },
    hooks: {
      ...hardcoded.hooks,
      ...(userDefaults.hooks || {}),
      ...(choices.hooks || {}),
    },
    agent_skills: {
      ...hardcoded.agent_skills,
      ...(userDefaults.agent_skills || {}),
      ...(choices.agent_skills || {}),
    },
  };

  validateShipPrBodySections(config.ship.pr_body_sections);
  return config;
}

/**
 * Command: create a fully-materialized .planning/config.json for a new project.
 *
 * Accepts user-chosen settings as a JSON string (the keys the user explicitly
 * configured during /gsd:new-project). All remaining keys are filled from
 * hardcoded defaults and optional ~/.gsd/defaults.json.
 *
 * Idempotent: if config.json already exists, returns { created: false }.
 */
function cmdConfigNewProject(cwd, choicesJson, raw) {
  const planningBase = planningDir(cwd);
  const configPath = path.join(planningBase, 'config.json');

  // Idempotent: don't overwrite existing config
  if (fs.existsSync(configPath)) {
    output({ created: false, reason: 'already_exists' }, raw, 'exists');
    return;
  }

  // Parse user choices
  let userChoices = {};
  if (choicesJson && choicesJson.trim() !== '') {
