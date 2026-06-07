# /team test — Test Pipeline

> Called by team.md router when action is `test`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst | 2 |
| L2 | qa-test-architect + (domain engineers) | 3-4 |
| L3 | domain-accuracy | 1-2 |
| L4 | principal-architect | 1 |

## Pipeline Customization

### Layer 1: Coverage Analysis
L1 agents focus on:
- Current test coverage map (which modules have tests, which don't)
- Critical paths that lack coverage
- Existing test patterns and conventions
- Test infrastructure setup (frameworks, fixtures, mocks)

### Layer 2: Test Writing
- **Mode:** `bypassPermissions`
- File ownership: each agent owns `tests/test_{module}*` files
- DO NOT TOUCH: source code (tests only), other agents' test files
- Follow existing test patterns (fixtures, naming, assertions)
- Each agent:
  1. Read source module to understand behavior
  2. Identify untested edge cases and error paths
  3. Write tests following existing patterns
  4. Follow TDD red-green for each new test: prove it is RED before the implementation exists (for the right failure reason), then GREEN after. A test that was never red — or is empty, a placeholder, `assert True`, or unconditionally skipped — is rejected.
  5. Run the authoritative gate per the Test Evidence Protocol (`team:evidence.md`): use the CI-pinned tool versions, provision integration dependencies (e.g. Postgres + DSN) so gated tests actually execute, treat any skip as `UNVERIFIED` (never a pass), and capture command + exit code + summary to `EVIDENCE.md`.
  6. Commit: `test({module}): add missing tests for {description}`

**Toolkit integration:**
- Check team:toolkit.md for "Test-Driven Development" entry
- qa-test-architect designs the test strategy; domain engineers write module-specific tests

### Layer 3: Test Quality Review
L3 agents verify:
- Tests actually test behavior (not implementation details)
- No test interdependence or shared mutable state
- Edge cases covered (null, empty, boundary, error paths)
- Test names describe the scenario being tested
- **Execution is real, not narrated:** confirm via `EVIDENCE.md` that the suite actually ran (captured exit 0, no skips on the covered surface). Reviewing test descriptions is not a substitute for verifying execution. A green claim without captured evidence is a finding, not a pass.

### Full Regression
Run the CI-equivalent authoritative gate with integration dependencies provisioned, per the Test Evidence Protocol (`team:evidence.md`). Report the parsed pytest summary (passed / skipped / failed) and the measured coverage (`--cov --cov-branch`). Any skipped test blocks a "pass" claim — resolve by provisioning the dependency or explicitly label the gap. Capture all output to `EVIDENCE.md`.

## GSD Integration

When `.planning/` exists, L2 agents check test requirements from REQUIREMENTS.md. Test files follow GSD naming conventions.
