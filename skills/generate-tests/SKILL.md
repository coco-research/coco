---
name: generate-tests
description: "Generate complete test coverage for any file, component, or module. Covers unit tests, integration tests, edge cases, error handling, and mocking — adapted to whatever testing framework the project uses."
domain: engineering
supports: [claude-code, cursor, codex, generic]
version: 0.1.0
---

# Generate Tests — Comprehensive Test Suite Generator

Generate complete test coverage for any file, component, or module. Covers unit tests, integration tests, edge cases, error handling, and mocking — adapted to whatever testing framework the project uses.

**Use when**: you want tests generated for a file or component, need to improve test coverage, want edge case coverage, need mocks for external dependencies, or want to bootstrap a test suite for untested code.

---

## When This Skill Is Activated

Follow every step below. Do NOT generate tests without first analyzing the project's testing setup and the target code.

---

## Step 1: Detect the Testing Setup

Before writing any tests, discover the project's testing conventions:

1. **Find the test framework** — Check `package.json` (dependencies/scripts), or config files:
   - `jest.config.*` / `jest` key in `package.json` → Jest
   - `vitest.config.*` → Vitest
   - `cypress.config.*` → Cypress
   - `playwright.config.*` → Playwright
   - `pytest.ini` / `pyproject.toml` [tool.pytest] → pytest
   - `go.mod` → Go testing
   - `Cargo.toml` → Rust (#[cfg(test)])

2. **Find existing test files** — Search for `*.test.*`, `*.spec.*`, `test_*.py`, `*_test.go` to understand naming conventions and patterns already in use.

3. **Check for test utilities** — Look for shared helpers, factories, custom matchers, or mock setups the project already provides (e.g., `test/utils.ts`, `__mocks__/`, `conftest.py`).

4. **Check the test script** — Read the `test` script in `package.json` (or equivalent) to understand how tests are run, what flags are used, and what coverage tool is configured.

**Match the project's existing conventions exactly.** File naming, import style, assertion style, describe/it vs test, etc.

---

## Step 2: Analyze the Target Code

Read the file or component the user wants tested. Identify:

- All exported functions, classes, methods, and components
- Input types and return types (or infer them)
- External dependencies (API calls, database, file system, third-party libs)
- Side effects (mutations, network calls, timers, DOM manipulation)
- Error paths (throw statements, catch blocks, error returns)
- Edge cases (null/undefined inputs, empty arrays, boundary values, large inputs)
- Async behavior (promises, callbacks, streams)

---

## Step 3: Plan the Test Suite

Before writing code, outline what you'll test:

### Unit Tests
- Every exported function with representative inputs
- Return values for happy path
- Error handling for invalid inputs
- Boundary values (0, -1, empty string, null, max int, etc.)
- Type coercion edge cases if applicable

### Integration Tests (if the code interacts with other modules)
- Component interactions and data flow
- API calls with mocked responses (success + failure)
- Service layer with mocked dependencies
- State management side effects

### Edge Cases and Error Handling
- Null, undefined, empty inputs
- Malformed data
- Network failures / timeouts
- Concurrent access / race conditions
- Extremely large inputs

---

## Step 4: Write the Tests

Follow these principles:

### Structure

```
describe("[ModuleName]", () => {
  describe("[functionName]", () => {
    it("should [expected behavior] when [condition]", () => {
      // Arrange
      // Act
      // Assert
    });
  });
});
```

- **Descriptive test names** — Read like documentation: "should return empty array when input is null"
- **AAA pattern** — Arrange (setup), Act (execute), Assert (verify). Separate each visually.
- **One assertion per concept** — Multiple `expect()` calls are fine if they assert one logical thing
- **Group with `describe`** — One block per function/method/component behavior
- **Setup/teardown** — Use `beforeEach`/`afterEach` for test isolation. Clean up subscriptions, timers, mocks.

### Mocking Strategy

- Mock **external dependencies only** — Don't mock the code under test
- Use the project's existing mock patterns (e.g., `jest.mock()`, `vi.mock()`, `unittest.mock`)
- Create **test data factories** for complex objects instead of inline literals
- Mock timers (`jest.useFakeTimers()` / `vi.useFakeTimers()`) for time-dependent code
- Mock dates for deterministic snapshots
- Always **restore mocks** in `afterEach` to prevent test pollution

### Async Testing

- Always `await` async functions or return the promise
- Test both resolve and reject paths
- Use `waitFor` / `findBy` for async UI updates (React Testing Library)
- Test loading, success, and error states

### Framework-Specific Guidance

| Framework | Component Testing | Key Patterns |
|-----------|------------------|--------------|
| **React** | React Testing Library | `render()`, `screen.getByRole()`, `userEvent`, `waitFor` |
| **Vue** | Vue Test Utils | `mount()`, `shallowMount()`, `wrapper.find()`, `trigger()` |
| **Angular** | TestBed | `TestBed.configureTestingModule()`, `fixture.detectChanges()` |
| **Node.js** | Supertest | `request(app).get("/api/...").expect(200)` |
| **Python** | pytest | `@pytest.fixture`, `monkeypatch`, parametrize |
| **Go** | testing | `t.Run()`, table-driven tests, `t.Parallel()` |

---

## Step 5: Verify and Improve

After generating the tests:

1. **Run the tests** — Execute the test suite to make sure they pass
2. **Check coverage** — Identify untested lines or branches
3. **Add missing cases** — Fill gaps in coverage, especially error paths
4. **Review test quality** — Tests should fail when the code breaks, not just when the tests break

### Coverage Goals

| Priority | Coverage Target |
|----------|----------------|
| Critical business logic | 90%+ |
| Utility functions | 85%+ |
| UI components | 80%+ |
| Configuration/glue code | 60%+ |

Focus on **branch coverage** over line coverage — untested `else` and `catch` paths are where bugs hide.

---

## Output Checklist

Before finishing, verify:

- [ ] Tests follow the project's existing naming convention and file location
- [ ] All exported functions/components have at least one test
- [ ] Happy path tested for every function
- [ ] Error/failure path tested for every function that can fail
- [ ] Edge cases covered (null, empty, boundary values)
- [ ] External dependencies are mocked (no real API calls, no real DB)
- [ ] Async code is properly awaited
- [ ] Mocks are cleaned up in afterEach
- [ ] Tests are independent — can run in any order
- [ ] Test names read like documentation
