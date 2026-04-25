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
- Agents write failing test first, then fix, then verify test passes
- Atomic commits per fix: `fix({scope}): {description}`

**Toolkit integration:**
- Check team-toolkit.md for "Systematic Debugging" entry
- Apply systematic-debugging methodology for complex bugs

### Layer 3: Fix Verification
L3 agents verify:
- Root cause actually addressed (not just symptom masked)
- No new issues introduced
- Test coverage for the fixed code path

### Regression Tests
Run after all Layer 2 agents complete. If any test fails, include in REVIEW-PACKAGE.md.

## GSD Integration

When `.planning/` exists, L2 agents follow GSD commit conventions. Include fix context in STATE.md.
