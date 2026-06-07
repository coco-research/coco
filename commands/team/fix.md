# /team fix — Fix Pipeline

> Called by team.md router when action is `fix`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, security-analyst | 2 |
| L2 | (domain-dependent engineers) + qa-test-architect, performance-eng (if perf-related) | 2-4 |
| L3 | domain-accuracy | 2 |
| L4 | principal-architect | 1 |

### Issue Detection

L1 agents identify issues from:
- Conversation context (user described bugs, review findings, error logs)
- `.planning/` review documents (if GSD active)
- Test failure output

Group issues by file ownership — no two L2 agents touch the same files.

## Pipeline Customization

### Layer 1: Diagnosis
L1 agents focus on:
- Root cause analysis for each reported issue
- File mapping — which files need changes
- Impact assessment — what else might break

### Layer 2: Execution
- **Mode:** `bypassPermissions`
- Each agent gets a specific issue set with file ownership
- Agents write a failing test first that reproduces the bug (prove it is RED for the right reason), then fix, then prove it is GREEN. A regression test that was never red does not prove the fix.
- Run the authoritative gate per the Test Evidence Protocol (`team:evidence.md`): CI-pinned tool versions, integration dependencies provisioned, any skip treated as `UNVERIFIED` (never a pass), and capture command + exit code + summary to `EVIDENCE.md`. "Fixed + tested" is not a valid claim without that evidence.
- Atomic commits per fix: `fix({scope}): {description}`

**Toolkit integration:**
- Check team:toolkit.md for "Systematic Debugging" entry
- Apply systematic-debugging methodology for complex bugs

### Layer 3: Fix Verification
L3 agents verify:
- Root cause actually addressed (not just symptom masked)
- No new issues introduced
- Test coverage for the fixed code path, confirmed against `EVIDENCE.md` (the bug-reproducing test actually ran and is now green) — not by reading test descriptions

### Regression Tests
Run after all Layer 2 agents complete, per the Test Evidence Protocol (`team:evidence.md`): run the CI-equivalent authoritative gate with integration dependencies provisioned, capture the parsed summary + coverage to `EVIDENCE.md`, and surface skips/`UNVERIFIED` explicitly. Any failing test BLOCKS — loop back to fix (max 3 rounds); do not merely note it in REVIEW-PACKAGE.md.

## GSD Integration

When `.planning/` exists, L2 agents follow GSD commit conventions. Include fix context in STATE.md.
