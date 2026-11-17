/**
 * Init — Compound init commands for workflow bootstrapping
 */

const fs = require('fs');
const path = require('path');
const { execGit, platformWriteSync, platformReadSync } = require('./shell-command-projection.cjs');
const { loadConfig, resolveModelInternal, findPhaseInternal, getRoadmapPhaseInternal, pathExistsInternal, gitWorktreeInfoInternal, generateSlugInternal, getMilestoneInfo, getMilestonePhaseFilter, stripShippedMilestones, extractCurrentMilestone, normalizePhaseName, toPosixPath, output, error, checkAgentsInstalled, phaseTokenMatches } = require('./core.cjs');
const { planningPaths, planningDir, planningRoot, findContextMdIn } = require('./planning-workspace.cjs');
const { maskIfSecret } = require('./secrets.cjs');
const scanPhasePlans = require('./plan-scan.cjs');
const { stateExtractField } = require('./state-document.cjs');
const { formatGsdSlash, resolveRuntime } = require('./runtime-slash.cjs');
const { determinePhaseStatus } = require('./commands.cjs');

// Accept all bold/colon variants of the Requirements header (#2769):
// **Requirements:** / **Requirements**: / **Requirements** : render the
// same in markdown but differ textually.
const REQUIREMENTS_HEADER_RE = /^\*\*Requirements:?\*\*[^\S\n]*:?[^\S\n]*([^\n]*)$/m;

function listPhaseSummaryFiles(phaseDir) {
  return scanPhasePlans(phaseDir).summaryFiles;
}

function listPhasePlanFiles(phaseDir) {
  return scanPhasePlans(phaseDir).planFiles;
}

function getLatestCompletedMilestone(cwd) {
  const milestonesPath = path.join(planningRoot(cwd), 'MILESTONES.md');
  const content = platformReadSync(milestonesPath);
  if (content === null) return null;

  const match = content.match(/^##\s+(v[\d.]+)\s+(.+?)\s+\(Shipped:/m);
  if (!match) return null;
  return {
    version: match[1],
    name: match[2].trim(),
  };
}

/**
 * Inject `project_root` into an init result object.
 * Workflows use this to prefix `.planning/` paths correctly when Claude's CWD
 * differs from the project root (e.g., inside a sub-repo).
 */
function withProjectRoot(cwd, result) {
  result.project_root = cwd;
  // Inject agent installation status into all init outputs (#1371).
  // Workflows that spawn named subagents use this to detect when agents
  // are missing and would silently fall back to general-purpose.
  const agentStatus = checkAgentsInstalled();
  result.agents_installed = agentStatus.agents_installed;
  result.missing_agents = agentStatus.missing_agents;
  // Inject response_language into all init outputs (#1399).
  // Workflows propagate this to subagent prompts so user-facing questions
  // stay in the configured language across phase boundaries.
  const config = loadConfig(cwd);
  if (config.response_language) {
    result.response_language = config.response_language;
  }
  // Inject project identity into all init outputs so handoff blocks
  // can include project context for cross-session continuity.
  if (config.project_code) {
    result.project_code = config.project_code;
  }
  // Extract project title from PROJECT.md first H1 heading.
  const projectMdPath = path.join(planningDir(cwd), 'PROJECT.md');
  const content = platformReadSync(projectMdPath);
  if (content) {
    const h1Match = content.match(/^#\s+(.+)$/m);
    if (h1Match) {
      result.project_title = h1Match[1].trim();
    }
  }
  return result;
}

/**
 * Return git-worktree state for init payloads with robust nested-subdir
 * detection across Windows short/long path forms and slash variants.
 */
function getInitGitState(cwd) {
  const info = gitWorktreeInfoInternal(cwd);
  const worktreeRoot = info.worktreeRoot;
  const normalizeForCompare = (p) => {
    if (typeof p !== 'string' || p.length === 0) return null;
    let resolved;
    try {
      resolved = fs.realpathSync.native(p);
    } catch {
      resolved = path.resolve(p);
    }
    resolved = path.resolve(resolved);
    if (process.platform === 'win32') {
      return resolved.replace(/\//g, '\\').toLowerCase();
    }
    return resolved;
  };

  let inNestedSubdir = false;
  if (info.inside) {
    let resolvedByGitPrefix = false;
    try {
      const prefixResult = execGit(['rev-parse', '--show-prefix'], { cwd, timeout: 5000 });
      if (prefixResult.exitCode === 0) {
        const prefix = String(prefixResult.stdout || '').trim().replace(/\\/g, '/');
        inNestedSubdir = prefix.length > 0 && prefix !== '.' && prefix !== './';
        resolvedByGitPrefix = true;
      }
    } catch {}

    if (!resolvedByGitPrefix) {
      const rootNorm = normalizeForCompare(worktreeRoot);
      const cwdNorm = normalizeForCompare(cwd);
      if (rootNorm && cwdNorm) {
        if (rootNorm === cwdNorm) {
          inNestedSubdir = false;
        } else {
          const rel = path.relative(rootNorm, cwdNorm);
          const relNorm = process.platform === 'win32' ? rel.replace(/\//g, '\\') : rel;
          inNestedSubdir =
            relNorm !== '' &&
            relNorm !== '.' &&
            !relNorm.startsWith('..') &&
            !path.isAbsolute(relNorm);
        }
      } else {
        inNestedSubdir = worktreeRoot !== null;
      }
    }
  }

  // Defensive final guard: if git reports the same root path as cwd (after
  // slash/case normalization), we are at the worktree root, never nested.
  if (inNestedSubdir && typeof worktreeRoot === 'string') {
    const toComparableRaw = (p) => p.replace(/\\/g, '/').replace(/\/+$/g, '').toLowerCase();
    if (toComparableRaw(worktreeRoot) === toComparableRaw(String(cwd))) {
      inNestedSubdir = false;
    }
  }

  return {
    has_git: info.inside,
    git_worktree_root: worktreeRoot,
    in_nested_subdir: inNestedSubdir,
  };
}

function cmdInitExecutePhase(cwd, phase, raw, options = {}) {
  if (!phase) {
    error('phase required for init execute-phase');
  }

  const config = loadConfig(cwd);
  let phaseInfo = findPhaseInternal(cwd, phase);
  const milestone = getMilestoneInfo(cwd);

  const roadmapPhase = getRoadmapPhaseInternal(cwd, phase);

  // If findPhaseInternal matched an archived phase from a prior milestone, but
  // the phase exists in the current milestone's ROADMAP.md, ignore the archive
  // match — we are initializing a new phase in the current milestone that
  // happens to share a number with an archived one. Without this, phase_dir,
  // phase_slug and related fields would point at artifacts from a previous
  // milestone.
  if (phaseInfo?.archived && roadmapPhase?.found) {
    phaseInfo = null;
  }

  // Fallback to ROADMAP.md if no phase directory exists yet
  if (!phaseInfo && roadmapPhase?.found) {
    const phaseName = roadmapPhase.phase_name;
    phaseInfo = {
      found: true,
      directory: null,
      phase_number: roadmapPhase.phase_number,
      phase_name: phaseName,
      phase_slug: phaseName ? phaseName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : null,
      plans: [],
      summaries: [],
      incomplete_plans: [],
      has_research: false,
      has_context: false,
      has_verification: false,
      has_reviews: false,
    };
  }
  const reqMatch = roadmapPhase?.section?.match(REQUIREMENTS_HEADER_RE);
  const reqExtracted = reqMatch
    ? reqMatch[1].replace(/[\[\]]/g, '').split(',').map(s => s.trim()).filter(Boolean).join(', ')
    : null;
  const phase_req_ids = (reqExtracted && reqExtracted !== 'TBD') ? reqExtracted : null;

  const result = {
    // Models
    executor_model: resolveModelInternal(cwd, 'gsd-executor'),
    verifier_model: resolveModelInternal(cwd, 'gsd-verifier'),

    // Config flags
    tdd_mode: options.tdd || config.tdd_mode || false,
    commit_docs: config.commit_docs,
    sub_repos: config.sub_repos,
    parallelization: config.parallelization,
    context_window: config.context_window,
    branching_strategy: config.branching_strategy,
    phase_branch_template: config.phase_branch_template,
    milestone_branch_template: config.milestone_branch_template,
    verifier_enabled: config.verifier,

    // Phase info
    phase_found: !!phaseInfo,
    phase_dir: phaseInfo?.directory || null,
    phase_number: phaseInfo?.phase_number || null,
    phase_name: phaseInfo?.phase_name || null,
    phase_slug: phaseInfo?.phase_slug || null,
    phase_req_ids,

    // Plan inventory
    plans: phaseInfo?.plans || [],
    summaries: phaseInfo?.summaries || [],
    incomplete_plans: phaseInfo?.incomplete_plans || [],
    plan_count: phaseInfo?.plans?.length || 0,
    incomplete_count: phaseInfo?.incomplete_plans?.length || 0,

    // Branch name (pre-computed)
    branch_name: config.branching_strategy === 'phase' && phaseInfo
      ? config.phase_branch_template
          .replace('{project}', config.project_code || '')
          .replace('{phase}', phaseInfo.phase_number)
          .replace('{slug}', phaseInfo.phase_slug || 'phase')
      : config.branching_strategy === 'milestone'
        ? config.milestone_branch_template
            .replace('{milestone}', milestone.version)
            .replace('{slug}', generateSlugInternal(milestone.name) || 'milestone')
        : null,

    // Milestone info
    milestone_version: milestone.version,
    milestone_name: milestone.name,
    milestone_slug: generateSlugInternal(milestone.name),

    // File existence
    state_exists: fs.existsSync(path.join(planningDir(cwd), 'STATE.md')),
    roadmap_exists: fs.existsSync(path.join(planningDir(cwd), 'ROADMAP.md')),
    config_exists: fs.existsSync(path.join(planningDir(cwd), 'config.json')),
    // File paths
    state_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'STATE.md'))),
    roadmap_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'ROADMAP.md'))),
    config_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'config.json'))),
  };

  // Optional --validate: run state validation and include warnings (#1627)
  if (options.validate) {
    try {
      const statePath = path.join(planningDir(cwd), 'STATE.md');
      const stateContent = platformReadSync(statePath);
      if (stateContent !== null) {
        const status = stateExtractField(stateContent, 'Status') || '';
        result.state_validation_ran = true;
        // Simple inline validation — check for obvious drift
        const warnings = [];
        const phasesPath = planningPaths(cwd).phases;
        if (phaseInfo && phaseInfo.directory && fs.existsSync(path.join(cwd, phaseInfo.directory))) {
          const diskPlans = listPhasePlanFiles(path.join(cwd, phaseInfo.directory)).length;
          const totalPlansRaw = stateExtractField(stateContent, 'Total Plans in Phase');
          const totalPlansInPhase = totalPlansRaw ? parseInt(totalPlansRaw, 10) : null;
          if (totalPlansInPhase !== null && diskPlans !== totalPlansInPhase) {
            warnings.push(`Plan count mismatch: STATE.md says ${totalPlansInPhase}, disk has ${diskPlans}`);
          }
        }
        result.state_warnings = warnings;
      }
    } catch { /* intentionally empty */ }
  }

  output(withProjectRoot(cwd, result), raw);
}

function cmdInitPlanPhase(cwd, phase, raw, options = {}) {
  if (!phase) {
    error('phase required for init plan-phase');
  }

  const config = loadConfig(cwd);
  let phaseInfo = findPhaseInternal(cwd, phase);

  const roadmapPhase = getRoadmapPhaseInternal(cwd, phase);

  // If findPhaseInternal matched an archived phase from a prior milestone, but
  // the phase exists in the current milestone's ROADMAP.md, ignore the archive
  // match — we are planning a new phase in the current milestone that happens
  // to share a number with an archived one. Without this, phase_dir,
  // phase_slug, has_context and has_research would point at artifacts from a
  // previous milestone.
  if (phaseInfo?.archived && roadmapPhase?.found) {
    phaseInfo = null;
  }

  // Fallback to ROADMAP.md if no phase directory exists yet
  if (!phaseInfo && roadmapPhase?.found) {
    const phaseName = roadmapPhase.phase_name;
    phaseInfo = {
      found: true,
      directory: null,
      phase_number: roadmapPhase.phase_number,
      phase_name: phaseName,
      phase_slug: phaseName ? phaseName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : null,
      plans: [],
      summaries: [],
      incomplete_plans: [],
      has_research: false,
      has_context: false,
      has_verification: false,
      has_reviews: false,
    };
  }
  const reqMatch = roadmapPhase?.section?.match(REQUIREMENTS_HEADER_RE);
  const reqExtracted = reqMatch
    ? reqMatch[1].replace(/[\[\]]/g, '').split(',').map(s => s.trim()).filter(Boolean).join(', ')
    : null;
  const phase_req_ids = (reqExtracted && reqExtracted !== 'TBD') ? reqExtracted : null;

  // #3287: compute the canonical directory name with project_code prefix so
  // the first-touch mkdir in /gsd:plan-phase stays consistent with phase.add.
  const phaseDirPlan = phaseInfo?.directory || null;
  const phaseNumberPlan = phaseInfo?.phase_number || null;
  const phaseNamePlan = phaseInfo?.phase_name || null;
  const rawProjectCodePlan = config.project_code || '';
  let expectedPhaseDirPlan = null;
  if (!phaseDirPlan && phaseNumberPlan && phaseNamePlan) {
    const paddedNum = normalizePhaseName(phaseNumberPlan);
    const slug = generateSlugInternal(phaseNamePlan).substring(0, 60);
    if (slug) {
      const prefix = rawProjectCodePlan ? `${rawProjectCodePlan}-` : '';
      const dirName = `${prefix}${paddedNum}-${slug}`;
      expectedPhaseDirPlan = toPosixPath(path.relative(cwd, path.join(planningPaths(cwd).phases, dirName)));
    }
  }

  const result = {
    // Models
    researcher_model: resolveModelInternal(cwd, 'gsd-phase-researcher'),
    planner_model: resolveModelInternal(cwd, 'gsd-planner'),
    checker_model: resolveModelInternal(cwd, 'gsd-plan-checker'),

    // Workflow flags
    tdd_mode: options.tdd || config.tdd_mode || false,
    research_enabled: config.research,
    plan_checker_enabled: config.plan_checker,
    nyquist_validation_enabled: config.nyquist_validation,
    commit_docs: config.commit_docs,
    text_mode: config.text_mode,
    // Auto-advance config — included so workflows don't need separate config-get
    // calls for these values, which causes infinite config-read loops on some models
    // (e.g. Kimi K2.5). See #2192.
    auto_advance: !!(config.auto_advance),
    auto_chain_active: !!(config._auto_chain_active),
    mode: config.mode || 'interactive',

    // Phase info
    phase_found: !!phaseInfo,
    phase_dir: phaseDirPlan,
    expected_phase_dir: expectedPhaseDirPlan,
    phase_number: phaseNumberPlan,
    phase_name: phaseNamePlan,
    phase_slug: phaseInfo?.phase_slug || null,
    padded_phase: phaseNumberPlan ? normalizePhaseName(phaseNumberPlan) : null,
    phase_req_ids,

    // #3569: surface phase lifecycle status so /gsd:plan-phase can short-circuit
    // on closed (Complete) phases instead of silently replanning over shipped
    // code. Reuses determinePhaseStatus — the project-wide vocabulary
    // (Pending | Planned | In Progress | Executed | Complete | Needs Review).
    // No directory yet → Pending (phase has not been started).
    phase_status: phaseDirPlan
      ? determinePhaseStatus(
          phaseInfo?.plans?.length || 0,
          phaseInfo?.summaries?.length || 0,
          path.join(cwd, phaseDirPlan),
          'Pending',
        )
      : 'Pending',

    // Existing artifacts
    has_research: phaseInfo?.has_research || false,
    has_context: phaseInfo?.has_context || false,
    has_reviews: phaseInfo?.has_reviews || false,
    has_plans: (phaseInfo?.plans?.length || 0) > 0,
    plan_count: phaseInfo?.plans?.length || 0,

    // Environment
    planning_exists: fs.existsSync(planningDir(cwd)),
    roadmap_exists: fs.existsSync(path.join(planningDir(cwd), 'ROADMAP.md')),

    // File paths
    state_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'STATE.md'))),
    roadmap_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'ROADMAP.md'))),
    requirements_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'REQUIREMENTS.md'))),

    // Pattern mapper output (null until PATTERNS.md exists in phase dir)
    patterns_path: null,
  };

  if (phaseInfo?.directory) {
    // Find *-CONTEXT.md in phase directory
    const phaseDirFull = path.join(cwd, phaseInfo.directory);
    try {
      const files = fs.readdirSync(phaseDirFull);
      const contextFile = findContextMdIn(phaseDirFull);
      if (contextFile) {
        result.context_path = toPosixPath(path.join(phaseInfo.directory, contextFile));
      }
      const researchFile = files.find(f => f.endsWith('-RESEARCH.md') || f === 'RESEARCH.md');
      if (researchFile) {
        result.research_path = toPosixPath(path.join(phaseInfo.directory, researchFile));
      }
      const verificationFile = files.find(f => f.endsWith('-VERIFICATION.md') || f === 'VERIFICATION.md');
      if (verificationFile) {
        result.verification_path = toPosixPath(path.join(phaseInfo.directory, verificationFile));
      }
      const uatFile = files.find(f => f.endsWith('-UAT.md') || f === 'UAT.md');
      if (uatFile) {
        result.uat_path = toPosixPath(path.join(phaseInfo.directory, uatFile));
      }
      const reviewsFile = files.find(f => f.endsWith('-REVIEWS.md') || f === 'REVIEWS.md');
      if (reviewsFile) {
        result.reviews_path = toPosixPath(path.join(phaseInfo.directory, reviewsFile));
      }
      const patternsFile = files.find(f => f.endsWith('-PATTERNS.md') || f === 'PATTERNS.md');
      if (patternsFile) {
        result.patterns_path = toPosixPath(path.join(phaseInfo.directory, patternsFile));
      }
    } catch { /* intentionally empty */ }
  }

  // Optional --validate: run state validation and include warnings (#1627)
  if (options.validate) {
    try {
      const statePath = path.join(planningDir(cwd), 'STATE.md');
      const stateContent = platformReadSync(statePath);
      if (stateContent !== null) {
        const warnings = [];
        result.state_validation_ran = true;
        const totalPlansRaw = stateExtractField(stateContent, 'Total Plans in Phase');
        const totalPlansInPhase = totalPlansRaw ? parseInt(totalPlansRaw, 10) : null;
        if (totalPlansInPhase !== null && phaseInfo && totalPlansInPhase !== (phaseInfo.plans?.length || 0)) {
          warnings.push(`Plan count mismatch: STATE.md says ${totalPlansInPhase}, disk has ${phaseInfo.plans?.length || 0}`);
        }
        result.state_warnings = warnings;
      }
    } catch { /* intentionally empty */ }
  }

  output(withProjectRoot(cwd, result), raw);
}

function cmdInitNewProject(cwd, raw) {
  const config = loadConfig(cwd);

  // Detect Brave Search API key availability
  const homedir = require('os').homedir();
  const braveKeyFile = path.join(homedir, '.gsd', 'brave_api_key');
  const hasBraveSearch = !!(process.env.BRAVE_API_KEY || fs.existsSync(braveKeyFile));

  // Detect Firecrawl API key availability
  const firecrawlKeyFile = path.join(homedir, '.gsd', 'firecrawl_api_key');
  const hasFirecrawl = !!(process.env.FIRECRAWL_API_KEY || fs.existsSync(firecrawlKeyFile));

  // Detect Exa API key availability
  const exaKeyFile = path.join(homedir, '.gsd', 'exa_api_key');
  const hasExaSearch = !!(process.env.EXA_API_KEY || fs.existsSync(exaKeyFile));

  // Detect existing code (cross-platform — no Unix `find` dependency)
  let hasCode = false;
  let hasPackageFile = false;
  try {
    const codeExtensions = new Set([
      '.ts', '.js', '.py', '.go', '.rs', '.swift', '.java',
      '.kt', '.kts',           // Kotlin (Android, server-side)
      '.c', '.cpp', '.h',      // C/C++
      '.cs',                   // C#
      '.rb',                   // Ruby
      '.php',                  // PHP
      '.dart',                 // Dart (Flutter)
      '.m', '.mm',             // Objective-C / Objective-C++
      '.scala',                // Scala
      '.groovy',               // Groovy (Gradle build scripts)
      '.lua',                  // Lua
      '.r', '.R',              // R
      '.zig',                  // Zig
      '.ex', '.exs',           // Elixir
      '.clj',                  // Clojure
    ]);
    const skipDirs = new Set(['node_modules', '.git', '.planning', '.claude', '.codex', '__pycache__', 'target', 'dist', 'build']);
    function findCodeFiles(dir, depth) {
      if (depth > 3) return false;
      let entries;
      try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return false; }
      for (const entry of entries) {
        if (entry.isFile() && codeExtensions.has(path.extname(entry.name))) return true;
        if (entry.isDirectory() && !skipDirs.has(entry.name)) {
          if (findCodeFiles(path.join(dir, entry.name), depth + 1)) return true;
        }
      }
      return false;
    }
    hasCode = findCodeFiles(cwd, 0);
  } catch { /* intentionally empty — best-effort detection */ }

  hasPackageFile = pathExistsInternal(cwd, 'package.json') ||
                   pathExistsInternal(cwd, 'requirements.txt') ||
                   pathExistsInternal(cwd, 'Cargo.toml') ||
                   pathExistsInternal(cwd, 'go.mod') ||
                   pathExistsInternal(cwd, 'Package.swift') ||
                   pathExistsInternal(cwd, 'build.gradle') ||
                   pathExistsInternal(cwd, 'build.gradle.kts') ||
                   pathExistsInternal(cwd, 'pom.xml') ||
                   pathExistsInternal(cwd, 'Gemfile') ||
                   pathExistsInternal(cwd, 'composer.json') ||
                   pathExistsInternal(cwd, 'pubspec.yaml') ||
                   pathExistsInternal(cwd, 'CMakeLists.txt') ||
                   pathExistsInternal(cwd, 'Makefile') ||
                   pathExistsInternal(cwd, 'build.zig') ||
                   pathExistsInternal(cwd, 'mix.exs') ||
                   pathExistsInternal(cwd, 'project.clj');

  const result = {
    // Models
    researcher_model: resolveModelInternal(cwd, 'gsd-project-researcher'),
    synthesizer_model: resolveModelInternal(cwd, 'gsd-research-synthesizer'),
    roadmapper_model: resolveModelInternal(cwd, 'gsd-roadmapper'),

    // Config
    commit_docs: config.commit_docs,

    // Existing state
    project_exists: pathExistsInternal(cwd, '.planning/PROJECT.md'),
    has_codebase_map: pathExistsInternal(cwd, '.planning/codebase'),
    planning_exists: pathExistsInternal(cwd, '.planning'),

    // Brownfield detection
    has_existing_code: hasCode,
    has_package_file: hasPackageFile,
    is_brownfield: hasCode || hasPackageFile,
    needs_codebase_map: (hasCode || hasPackageFile) && !pathExistsInternal(cwd, '.planning/codebase'),

    // Git state (Bug #3491: detect parent worktree to avoid nested .git init)
    ...getInitGitState(cwd),

    // Enhanced search
    brave_search_available: hasBraveSearch,
    firecrawl_available: hasFirecrawl,
    exa_search_available: hasExaSearch,

    // File paths
    project_path: '.planning/PROJECT.md',
  };

  output(withProjectRoot(cwd, result), raw);
}

function cmdInitNewMilestone(cwd, raw) {
  const config = loadConfig(cwd);
  const milestone = getMilestoneInfo(cwd);
  const latestCompleted = getLatestCompletedMilestone(cwd);
  const phasesDir = path.join(planningDir(cwd), 'phases');
  let phaseDirCount = 0;

  try {
    if (fs.existsSync(phasesDir)) {
      // Bug #2445: filter phase dirs to current milestone only so stale dirs
      // from a prior milestone that were not archived don't inflate the count.
      const isDirInMilestone = getMilestonePhaseFilter(cwd);
      phaseDirCount = fs.readdirSync(phasesDir, { withFileTypes: true })
        .filter(entry => entry.isDirectory() && isDirInMilestone(entry.name))
        .length;
    }
  } catch {}

  const result = {
    // Models
    researcher_model: resolveModelInternal(cwd, 'gsd-project-researcher'),
    synthesizer_model: resolveModelInternal(cwd, 'gsd-research-synthesizer'),
    roadmapper_model: resolveModelInternal(cwd, 'gsd-roadmapper'),

    // Config
    commit_docs: config.commit_docs,
    research_enabled: config.research,

    // Current milestone
    current_milestone: milestone.version,
    current_milestone_name: milestone.name,
    latest_completed_milestone: latestCompleted?.version || null,
    latest_completed_milestone_name: latestCompleted?.name || null,
    phase_dir_count: phaseDirCount,
    phase_archive_path: latestCompleted ? toPosixPath(path.relative(cwd, path.join(planningRoot(cwd), 'milestones', `${latestCompleted.version}-phases`))) : null,

    // File existence
    project_exists: pathExistsInternal(cwd, '.planning/PROJECT.md'),
    roadmap_exists: fs.existsSync(path.join(planningDir(cwd), 'ROADMAP.md')),
    state_exists: fs.existsSync(path.join(planningDir(cwd), 'STATE.md')),

    // File paths
    project_path: '.planning/PROJECT.md',
    roadmap_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'ROADMAP.md'))),
    state_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'STATE.md'))),
  };

  output(withProjectRoot(cwd, result), raw);
}

function cmdInitQuick(cwd, description, raw) {
  const config = loadConfig(cwd);
  const now = new Date();
  const slug = description ? generateSlugInternal(description)?.substring(0, 40) : null;

  // Generate collision-resistant quick task ID: YYMMDD-xxx
  // xxx = 2-second precision blocks since midnight, encoded as 3-char Base36 (lowercase)
  // Range: 000 (00:00:00) to xbz (23:59:58), guaranteed 3 chars for any time of day.
  // Provides ~2s uniqueness window per user — practically collision-free across a team.
  const yy = String(now.getFullYear()).slice(-2);
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const dateStr = yy + mm + dd;
  const secondsSinceMidnight = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
  const timeBlocks = Math.floor(secondsSinceMidnight / 2);
  const timeEncoded = timeBlocks.toString(36).padStart(3, '0');
  const quickId = dateStr + '-' + timeEncoded;
  const branchSlug = slug || 'quick';
  const quickBranchName = config.quick_branch_template
    ? config.quick_branch_template
        .replace('{num}', quickId)
        .replace('{quick}', quickId)
        .replace('{slug}', branchSlug)
    : null;

  const result = {
    // Models
    planner_model: resolveModelInternal(cwd, 'gsd-planner'),
    executor_model: resolveModelInternal(cwd, 'gsd-executor'),
    checker_model: resolveModelInternal(cwd, 'gsd-plan-checker'),
    verifier_model: resolveModelInternal(cwd, 'gsd-verifier'),

    // Config
    commit_docs: config.commit_docs,
    branch_name: quickBranchName,

    // Quick task info
    quick_id: quickId,
    slug: slug,
    description: description || null,

    // Timestamps
    date: now.toISOString().split('T')[0],
    timestamp: now.toISOString(),

    // Paths
    quick_dir: '.planning/quick',
    task_dir: slug ? `.planning/quick/${quickId}-${slug}` : null,

    // File existence
    roadmap_exists: fs.existsSync(path.join(planningDir(cwd), 'ROADMAP.md')),
    planning_exists: fs.existsSync(planningRoot(cwd)),

  };

  output(withProjectRoot(cwd, result), raw);
}

/**
 * Init handler for ingest-docs workflow (#2801).
 *
 * Returns the minimal set of fields that ingest-docs.md needs to detect
 * whether a project/planning dir exists and choose new vs merge mode.
 * Mirrors the initIngestDocs SDK handler in sdk/src/query/init.ts.
 */
function cmdInitIngestDocs(cwd, raw) {
  const config = loadConfig(cwd);
  const result = {
    project_exists: pathExistsInternal(cwd, '.planning/PROJECT.md'),
    planning_exists: fs.existsSync(planningRoot(cwd)),
    ...getInitGitState(cwd),
    project_path: '.planning/PROJECT.md',
    commit_docs: config.commit_docs,
  };
  output(withProjectRoot(cwd, result), raw);
}

function cmdInitResume(cwd, raw) {
  const config = loadConfig(cwd);

  // Check for interrupted agent
  let interruptedAgentId = null;
  const agentIdRaw = platformReadSync(path.join(planningRoot(cwd), 'current-agent-id.txt'));
  if (agentIdRaw !== null) interruptedAgentId = agentIdRaw.trim();

  const result = {
    // File existence
    state_exists: fs.existsSync(path.join(planningDir(cwd), 'STATE.md')),
    roadmap_exists: fs.existsSync(path.join(planningDir(cwd), 'ROADMAP.md')),
    project_exists: pathExistsInternal(cwd, '.planning/PROJECT.md'),
    planning_exists: fs.existsSync(planningRoot(cwd)),

    // File paths
    state_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'STATE.md'))),
    roadmap_path: toPosixPath(path.relative(cwd, path.join(planningDir(cwd), 'ROADMAP.md'))),
    project_path: '.planning/PROJECT.md',

    // Agent state
    has_interrupted_agent: !!interruptedAgentId,
    interrupted_agent_id: interruptedAgentId,

    // Config
    commit_docs: config.commit_docs,
  };

  output(withProjectRoot(cwd, result), raw);
}

function cmdInitVerifyWork(cwd, phase, raw) {
  if (!phase) {
    error('phase required for init verify-work');
  }

  const config = loadConfig(cwd);
  let phaseInfo = findPhaseInternal(cwd, phase);

  // If findPhaseInternal matched an archived phase from a prior milestone, but
  // the phase exists in the current milestone's ROADMAP.md, ignore the archive
  // match — same pattern as cmdInitPhaseOp.
  if (phaseInfo?.archived) {
    const roadmapPhase = getRoadmapPhaseInternal(cwd, phase);
    if (roadmapPhase?.found) {
      phaseInfo = null;
    }
  }

  // Fallback to ROADMAP.md if no phase directory exists yet
  if (!phaseInfo) {
    const roadmapPhase = getRoadmapPhaseInternal(cwd, phase);
    if (roadmapPhase?.found) {
      const phaseName = roadmapPhase.phase_name;
      phaseInfo = {
        found: true,
        directory: null,
        phase_number: roadmapPhase.phase_number,
        phase_name: phaseName,
        phase_slug: phaseName ? phaseName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : null,
        plans: [],
        summaries: [],
        incomplete_plans: [],
        has_research: false,
        has_context: false,
        has_verification: false,
      };
    }
  }

  const result = {
    // Models
    planner_model: resolveModelInternal(cwd, 'gsd-planner'),
    checker_model: resolveModelInternal(cwd, 'gsd-plan-checker'),

    // Config
    commit_docs: config.commit_docs,

    // Phase info
    phase_found: !!phaseInfo,
    phase_dir: phaseInfo?.directory || null,
    phase_number: phaseInfo?.phase_number || null,
    phase_name: phaseInfo?.phase_name || null,

    // Existing artifacts
    has_verification: phaseInfo?.has_verification || false,
  };

  output(withProjectRoot(cwd, result), raw);
}

function cmdInitPhaseOp(cwd, phase, raw) {
  const config = loadConfig(cwd);
  let phaseInfo = findPhaseInternal(cwd, phase);

  // If the only disk match comes from an archived milestone, prefer the
  // current milestone's ROADMAP entry so discuss-phase and similar flows
  // don't attach to shipped work that reused the same phase number.
  if (phaseInfo?.archived) {
    const roadmapPhase = getRoadmapPhaseInternal(cwd, phase);
    if (roadmapPhase?.found) {
      const phaseName = roadmapPhase.phase_name;
      phaseInfo = {
        found: true,
        directory: null,
        phase_number: roadmapPhase.phase_number,
        phase_name: phaseName,
        phase_slug: phaseName ? phaseName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : null,
        plans: [],
        summaries: [],
        incomplete_plans: [],
        has_research: false,
        has_context: false,
        has_verification: false,
      };
    }
  }

  // Fallback to ROADMAP.md if no directory exists (e.g., Plans: TBD)
  if (!phaseInfo) {
    const roadmapPhase = getRoadmapPhaseInternal(cwd, phase);
    if (roadmapPhase?.found) {
      const phaseName = roadmapPhase.phase_name;
      phaseInfo = {
        found: true,
        directory: null,
        phase_number: roadmapPhase.phase_number,
        phase_name: phaseName,
        phase_slug: phaseName ? phaseName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : null,
        plans: [],
        summaries: [],
        incomplete_plans: [],
        has_research: false,
        has_context: false,
        has_verification: false,
      };
    }
  }

  // #3287: compute the canonical directory name with project_code prefix so
  // the first-touch mkdir in /gsd:discuss-phase stays consistent with phase.add.
  const phaseDir = phaseInfo?.directory || null;
  const phaseNumber = phaseInfo?.phase_number || null;
  const phaseName = phaseInfo?.phase_name || null;
  const rawProjectCode = config.project_code || '';
  let expectedPhaseDir = null;
  if (!phaseDir && phaseNumber && phaseName) {
    const paddedNum = normalizePhaseName(phaseNumber);
    const slug = generateSlugInternal(phaseName).substring(0, 60);
    if (slug) {
      const prefix = rawProjectCode ? `${rawProjectCode}-` : '';
      const dirName = `${prefix}${paddedNum}-${slug}`;
      expectedPhaseDir = toPosixPath(path.relative(cwd, path.join(planningPaths(cwd).phases, dirName)));
    }
  }

  const result = {
    // Config
    commit_docs: config.commit_docs,
    // #2997: secret config keys may be either booleans (availability flags) or
    // string API keys (when user did `gsd-tools config-set brave_search XXX`).
    // Pass booleans through; mask string values so the init bundle never echoes
    // plaintext credentials. SDK init.ts mirrors this masking.
    brave_search: typeof config.brave_search === 'string' ? maskIfSecret('brave_search', config.brave_search) : config.brave_search,
    firecrawl: typeof config.firecrawl === 'string' ? maskIfSecret('firecrawl', config.firecrawl) : config.firecrawl,
    exa_search: typeof config.exa_search === 'string' ? maskIfSecret('exa_search', config.exa_search) : config.exa_search,

    // Phase info
    phase_found: !!phaseInfo,
    phase_dir: phaseDir,
    expected_phase_dir: expectedPhaseDir,
    phase_number: phaseNumber,
    phase_name: phaseName,
    phase_slug: phaseInfo?.phase_slug || null,
