/**
 * Roadmap — Roadmap parsing and update operations
 */

const fs = require('fs');
const path = require('path');
const { escapeRegex, normalizePhaseName, phaseMarkdownRegexSource, phaseMarkdownRegexSourceExact, output, error, findPhaseInternal, stripShippedMilestones, extractCurrentMilestone, replaceInCurrentMilestone, phaseTokenMatches } = require('./core.cjs');
const { platformWriteSync } = require('./shell-command-projection.cjs');
const { planningPaths, withPlanningLock, findContextMdIn } = require('./planning-workspace.cjs');
const scanPhasePlans = require('./plan-scan.cjs');

/**
 * Coerce an arbitrary YAML scalar/object into a string for cross-cutting
 * truth aggregation. Handles:
 *   - strings (passthrough)
 *   - numbers / booleans (String() coercion — issue #2770: bare YAML ints
 *     like `- 3` must be surfaced, not silently skipped)
 *   - kv-shaped objects from parseMustHavesBlock continuation kv (issue
 *     #2757) — extract the first meaningful string field
 *
 * Returns the empty string when no usable text can be derived; callers should
 * skip empty results.
 */
function coerceTruthToString(t) {
  if (t === null || t === undefined) return '';
  if (typeof t === 'string') return t;
  if (typeof t === 'number' || typeof t === 'boolean' || typeof t === 'bigint') {
    return String(t);
  }
  if (typeof t === 'object') {
    // Prefer common title-bearing keys produced by parseMustHavesBlock
    for (const k of ['title', 'text', 'name', 'rule', 'path', 'provides']) {
      const v = t[k];
      if (typeof v === 'string' && v.trim()) return v;
      if (typeof v === 'number' || typeof v === 'boolean') return String(v);
    }
  }
  return '';
}

function countPhasePlansAndSummaries(phaseDir) {
  const { planCount, summaryCount } = scanPhasePlans(phaseDir);
  // hasContext and hasResearch are not plan-scan concerns — read the directory
  // once and share the listing for all non-plan metadata that cmdRoadmapAnalyze needs.
  let phaseFiles = [];
  try { phaseFiles = fs.readdirSync(phaseDir); } catch { /* empty */ }
  return {
    planCount,
    summaryCount,
    hasContext: findContextMdIn(phaseFiles) !== null,
    hasResearch: phaseFiles.some(f => f.endsWith('-RESEARCH.md') || f === 'RESEARCH.md'),
  };
}

// `phaseMarkdownRegexSource` moved to core.cjs (#3537) so phase.cjs and
// core.cjs itself can consume it without circular deps. Imported above.

/**
 * Search for a phase header (and its section) within the given content string.
 * Returns a result object if found (either a full match or a malformed_roadmap
 * checklist-only match), or null if the phase is not present at all.
 */
function searchPhaseInContent(content, escapedPhase, phaseNum) {
  // Match "## Phase X:", "### Phase X:", or "#### Phase X:" with optional name
  const phasePattern = new RegExp(
    `#{2,4}\\s*Phase\\s+${escapedPhase}:\\s*([^\\n]+)`,
    'i'
  );
  const headerMatch = content.match(phasePattern);

  if (!headerMatch) {
    // Fallback: check if phase exists in summary list but missing detail section
    const checklistPattern = new RegExp(
      `-\\s*\\[[ x]\\]\\s*\\*\\*Phase\\s+${escapedPhase}:\\s*([^*]+)\\*\\*`,
      'i'
    );
    const checklistMatch = content.match(checklistPattern);

    if (checklistMatch) {
      return {
        found: false,
        phase_number: phaseNum,
        phase_name: checklistMatch[1].trim(),
        error: 'malformed_roadmap',
        message: `Phase ${phaseNum} exists in summary list but missing "### Phase ${phaseNum}:" detail section. ROADMAP.md needs both formats.`
      };
    }

    return null;
  }

  const phaseName = headerMatch[1].trim();
  const headerIndex = headerMatch.index;

  // Find the end of this section (next ## or ### phase header, or end of file)
  const restOfContent = content.slice(headerIndex);
  const nextHeaderMatch = restOfContent.match(/\n#{2,4}\s+Phase\s+[\w][\w.-]*/i);
  const sectionEnd = nextHeaderMatch
    ? headerIndex + nextHeaderMatch.index
    : content.length;

  const section = content.slice(headerIndex, sectionEnd).trim();

  // Extract goal if present (supports both **Goal:** and **Goal**: formats)
  const goalMatch = section.match(/\*\*Goal(?::\*\*|\*\*:)\s*([^\n]+)/i);
  const goal = goalMatch ? goalMatch[1].trim() : null;

  // Mode: vertical-MVP slice mode flag. Lowercased + trimmed for canonical
  // comparison; unrecognized values are preserved verbatim for forward-compat.
  const modeMatch = section.match(/\*\*Mode(?::\*\*|\*\*:)\s*([^\n]+)/i);
  const mode = modeMatch ? modeMatch[1].trim().toLowerCase() : null;

  // Extract success criteria as structured array
  const criteriaMatch = section.match(/\*\*Success Criteria\*\*[^\n]*:\s*\n((?:\s*\d+\.\s*[^\n]+\n?)+)/i);
  const success_criteria = criteriaMatch
    ? criteriaMatch[1].trim().split('\n').map(line => line.replace(/^\s*\d+\.\s*/, '').trim()).filter(Boolean)
    : [];

  return {
    found: true,
    phase_number: phaseNum,
    phase_name: phaseName,
    goal,
    mode,
    success_criteria,
    section,
  };
}

function cmdRoadmapGetPhase(cwd, phaseNum, raw) {
  const roadmapPath = planningPaths(cwd).roadmap;

  if (!fs.existsSync(roadmapPath)) {
    output({ found: false, error: 'ROADMAP.md not found' }, raw, '');
    return;
  }

  try {
    const rawContent = fs.readFileSync(roadmapPath, 'utf-8');
    const milestoneContent = extractCurrentMilestone(rawContent, cwd);

    // #3599 two-pass: when the caller passes a project-code-prefixed ID like
    // `PROJ-42`, try the exact-prefixed heading first (`### Phase PROJ-42:`).
    // If no match, fall back to the #3537 padding-tolerant numeric form so
    // a `CK-01` query still resolves to `### Phase 1:`. Doing this at the
    // call site (instead of inside phaseMarkdownRegexSource) avoids the
    // alternation-order ambiguity where a bare `### Phase 42:` heading in
    // the same document would intercept the match for a `PROJ-42` query.
    const fullContent = stripShippedMilestones(rawContent);

    const exactSource = phaseMarkdownRegexSourceExact(phaseNum);
    if (exactSource) {
      const exactMilestone = searchPhaseInContent(milestoneContent, exactSource, phaseNum);
      if (exactMilestone && !exactMilestone.error) {
        output(exactMilestone, raw, exactMilestone.section);
        return;
      }
      const exactFull = searchPhaseInContent(fullContent, exactSource, phaseNum);
      if (exactFull && !exactFull.error) {
        output(exactFull, raw, exactFull.section);
        return;
      }
    }

    // #3537: padding-tolerant fragment so callers passing `02.7` still match
    // un-padded ROADMAP prose (`### Phase 2.7:`).
    const escapedPhase = phaseMarkdownRegexSource(phaseNum);

    // Search the current milestone slice first, then fall back to full roadmap.
    // A malformed_roadmap result (checklist-only) from the milestone should not
    // block finding a full header match in the wider roadmap content.
    const milestoneResult = searchPhaseInContent(milestoneContent, escapedPhase, phaseNum);
    const result = (milestoneResult && !milestoneResult.error)
      ? milestoneResult
      : searchPhaseInContent(fullContent, escapedPhase, phaseNum) || milestoneResult;

    if (!result) {
      output({ found: false, phase_number: phaseNum }, raw, '');
      return;
    }

    if (result.error) {
      output(result, raw, '');
      return;
    }

    output(result, raw, result.section);
  } catch (e) {
    error('Failed to read ROADMAP.md: ' + e.message);
  }
}

function cmdRoadmapAnalyze(cwd, raw) {
  const roadmapPath = planningPaths(cwd).roadmap;

  if (!fs.existsSync(roadmapPath)) {
    output({ error: 'ROADMAP.md not found', milestones: [], phases: [], current_phase: null }, raw);
    return;
  }

  const rawContent = fs.readFileSync(roadmapPath, 'utf-8');
  const content = extractCurrentMilestone(rawContent, cwd);
  const phasesDir = planningPaths(cwd).phases;

  // Extract all phase headings: ## Phase N: Name or ### Phase N: Name
  const phasePattern = /#{2,4}\s*Phase\s+(\d+[A-Z]?(?:\.\d+)*)\s*:\s*([^\n]+)/gi;
  const phases = [];
  let match;

  // Build phase directory lookup once (O(1) readdir instead of O(N) per phase)
  const _phaseDirNames = (() => {
    try {
      return fs.readdirSync(phasesDir, { withFileTypes: true })
        .filter(e => e.isDirectory())
        .map(e => e.name);
    } catch { return []; }
  })();

  while ((match = phasePattern.exec(content)) !== null) {
    const phaseNum = match[1];
    const phaseName = match[2].replace(/\(INSERTED\)/i, '').trim();

    // Extract goal from the section
    const sectionStart = match.index;
    const restOfContent = content.slice(sectionStart);
    const nextHeader = restOfContent.match(/\n#{2,4}\s+Phase\s+\d/i);
    const sectionEnd = nextHeader ? sectionStart + nextHeader.index : content.length;
    const section = content.slice(sectionStart, sectionEnd);

    const goalMatch = section.match(/\*\*Goal(?::\*\*|\*\*:)\s*([^\n]+)/i);
    const goal = goalMatch ? goalMatch[1].trim() : null;

    const modeMatch = section.match(/\*\*Mode(?::\*\*|\*\*:)\s*([^\n]+)/i);
    const mode = modeMatch ? modeMatch[1].trim().toLowerCase() : null;

    const dependsMatch = section.match(/\*\*Depends on(?::\*\*|\*\*:)\s*([^\n]+)/i);
    const depends_on = dependsMatch ? dependsMatch[1].trim() : null;

    // Check completion on disk
    const normalized = normalizePhaseName(phaseNum);
    let diskStatus = 'no_directory';
    let planCount = 0;
    let summaryCount = 0;
    let hasContext = false;
    let hasResearch = false;

    try {
      const dirMatch = _phaseDirNames.find(d => phaseTokenMatches(d, normalized));

      if (dirMatch) {
        const counts = countPhasePlansAndSummaries(path.join(phasesDir, dirMatch));
        planCount = counts.planCount;
        summaryCount = counts.summaryCount;
        hasContext = counts.hasContext;
        hasResearch = counts.hasResearch;

        if (summaryCount >= planCount && planCount > 0) diskStatus = 'complete';
        else if (summaryCount > 0) diskStatus = 'partial';
        else if (planCount > 0) diskStatus = 'planned';
        else if (hasResearch) diskStatus = 'researched';
        else if (hasContext) diskStatus = 'discussed';
        else diskStatus = 'empty';
      }
    } catch { /* intentionally empty */ }

    // Check ROADMAP checkbox status.
    // #3537: padding-tolerant fragment — the heading discovered above may use
    // a different padding than the summary-bullet checkbox below it (mixed
    // padding inside one ROADMAP is legal and seen in real projects).
