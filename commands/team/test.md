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
  4. Run tests to verify they pass
  5. Commit: `test({module}): add missing tests for {description}`

**Toolkit integration:**
- Check team-toolkit.md for "Test-Driven Development" entry
- qa-test-architect designs the test strategy; domain engineers write module-specific tests

### Layer 3: Test Quality Review
L3 agents verify:
- Tests actually test behavior (not implementation details)
- No test interdependence or shared mutable state
- Edge cases covered (null, empty, boundary, error paths)
- Test names describe the scenario being tested

### Full Regression
Run complete test suite after all L2 agents commit. Report coverage delta.

## GSD Integration

When `.planning/` exists, L2 agents check test requirements from REQUIREMENTS.md. Test files follow GSD naming conventions.
