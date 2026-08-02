# /team reanalyse — Re-Analysis Pipeline

> Called by team.md router when action is `reanalyse`.
> Re-reviews completed work against current codebase state for regressions.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, security-analyst | 2 |
| L2 | (domain-dependent engineers) + qa-test-architect | 3-5 |
| L3 | domain-accuracy | 1-2 |
| L4 | principal-architect | 1 |

## Pipeline Customization

### Layer 1: Delta Analysis
L1 agents determine:
- What has changed since the original implementation/last review. When `.arch/index.json`
  exists, its pin is the natural baseline for "since" — `git diff --name-status <pin>..HEAD`.
- Which requirements need re-verification
- What new code interacts with previously reviewed modules

### Layer 2: Re-Verification
- **Mode:** `bypassPermissions` for any domain involving tests or runtime behavior (agents must be able to re-run the gate); `default` (read-only) for static/doc domains.
- Each agent re-checks their domain against current code
- Reports: STILL GOOD | REGRESSION | NEW ISSUE | IMPROVEMENT | ARCHITECTURAL REGRESSION
- **ARCHITECTURAL REGRESSION** is reserved for structural drift against `.arch/index.json`
  and requires the deterministic scan, not a reading:

  ```bash
  python3 skills/arch-index/scripts/arch_drift.py --repo-root .
  ```

  Report it when a component's primary paths have died (`REMOVE` or `PRUNE`), or when new
  code has landed in a top-level directory no component claims. Quote the verdict from
  `.arch/DRIFT.json`. Structural drift only — a component reworked inside its own already
  claimed directory is not an architectural regression by this definition, and if that is
  what you found, report it as REGRESSION or NEW ISSUE instead. If the index pin is behind
  HEAD, the finding is SUSPECTED rather than confirmed until `/team arch drift` reconciles it.
- **A regression in test or runtime behavior must be confirmed by re-running the authoritative gate** per the Test Evidence Protocol (`team:evidence.md`), capturing the before/after summary in `EVIDENCE.md`. A regression claimed from code-reading alone (no captured run) is reported as SUSPECTED, not confirmed.
- Focus on interactions between modules that changed independently

**If GSD active:** Check each requirement from REQUIREMENTS.md against current code.

**Toolkit integration:**
- No specific toolkit entries apply — agents use direct code analysis
- Reference team:feedback.md for past review findings to check if they've regressed

### Layer 3: Regression Confirmation
L3 verifies claimed regressions are real (not false positives) — a REGRESSION on test status requires captured before/after evidence in `EVIDENCE.md`, not just a code-reading assertion.

### Layer 4: Delta Report
Principal produces:
- Regression list with severity and recommended fixes
- Confirmation of what's still solid
- New improvement opportunities discovered

## GSD Integration

When `.planning/` exists, re-verify each requirement from REQUIREMENTS.md against current code.
