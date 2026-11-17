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
