# Verification Workflow

> Catch AI-generated bugs before they reach production. Six quality gates, run after every change.

## Why Verification Matters

AI-generated code has predictable failure patterns. It compiles, it looks correct, it even passes a casual review — but it contains subtle bugs that crash at runtime. These bugs are not random. They follow consistent patterns that can be caught with systematic checks.

Without verification, you accumulate a growing backlog of silent bugs that surface days or weeks later, when they are far more expensive to fix. With verification, you catch them in seconds, while the context is still fresh.

**Rule of thumb:** Run verification after every 1-2 file changes. The cost is 10-30 seconds. The cost of skipping is 30+ minutes of debugging later.

---

## The Six Quality Gates

### Gate 1: Build
**Question:** Does the code compile without errors?

**What to check:**
- TypeScript/JavaScript: `tsc --noEmit` or `npm run build`
- Python: `python -m py_compile file.py` or `mypy`
- Go: `go build ./...`
- General: whatever your project's build command is

**Why it matters:** Build errors are the most basic signal. If the build fails, nothing else matters. AI assistants sometimes generate code that references types or modules that do not exist in your project.

### Gate 2: Lint
**Question:** Does the code follow style and formatting rules?

**What to check:**
- ESLint, Prettier, Ruff, Black, golint — whatever your project uses
- Focus on errors, not warnings (warnings can be addressed later)

**Why it matters:** Lint errors often signal deeper problems. An "unused variable" warning might mean the AI declared a variable but forgot to wire it up. A "no-undef" error means the AI referenced something that does not exist.

### Gate 3: Imports
**Question:** Are all imports resolved? Are there circular dependencies?

**What to check:**
- Every import statement resolves to an actual file or package
- No circular import chains (A imports B, B imports A)
- No imports from deleted or renamed files
- Default vs. named exports match (a common AI mistake)

**Common AI mistakes:**
- Importing from a file path that was renamed in a previous edit
- Using `import { Foo }` when the module uses `export default Foo`
- Importing a function that was moved to a different module
- Creating circular dependencies by importing utilities from a file that imports the current file

### Gate 4: References
**Question:** Are there stale references to renamed or deleted code?

**What to check:**
- Function calls reference functions that still exist with the same signature
- Component props match the component's current prop types
- Database queries reference tables and columns that exist
- API calls use endpoints that are still defined
- Test files reference the correct source files

**Common AI mistakes:**
- Renaming a function in the source file but not updating callers
- Changing a component's props interface but not updating parent components
- Referencing a database column that was removed in a migration
- Tests importing a helper function from a path that no longer exists

### Gate 5: Tests
**Question:** Do all tests pass?

**What to check:**
- Run the full test suite: `npm test`, `pytest`, `go test ./...`
- If the full suite is slow, run at minimum the tests for changed files
- Check for new test failures (tests that passed before your changes)
- Check for skipped tests that should not be skipped

**Common AI mistakes:**
- Changing source code without updating corresponding tests
- Leaving mock data from a previous test leaking into the next test (mock isolation)
- Writing tests that pass in isolation but fail when run with the full suite
- Using `test.skip` or `xit` to hide failing tests instead of fixing them

### Gate 6: Behavior
**Question:** Does the code do what it is supposed to do?

**What to check:**
- Manually verify the happy path (does the feature work as intended?)
- Check edge cases: empty inputs, null values, network errors, boundary conditions
- Verify that existing features still work (regression check)
- Check the UI in a browser if applicable (does it render correctly?)

**Why this gate is last:** If gates 1-5 pass, the code is structurally sound. Gate 6 verifies that the structure produces the correct behavior. This is the gate where you catch logical errors — the code runs fine, but it does the wrong thing.

---

## When to Run Each Gate

| Trigger | Gates to Run |
|---------|-------------|
| After editing 1-2 files | Gates 1-3 (Build, Lint, Imports) |
| After completing a feature | Gates 1-6 (all) |
| Before committing | Gates 1-5 (all automated gates) |
| Before merging a PR | Gates 1-6 (full verification) |
| After a large refactor | Gates 1-6 with extra attention to Gate 4 (References) |

---

## Common AI-Introduced Bugs

These are the bugs that appear most frequently in AI-generated code. Knowing the patterns helps you spot them faster.

### Temporal Dead Zone (TDZ) Errors
The AI declares a variable with `const` or `let` and then references it before the declaration. This compiles in some contexts but throws a runtime error.

**How to catch:** Gate 1 (Build) with strict mode, or Gate 5 (Tests) when the code path is exercised.

### Import/Export Mismatches
The AI uses a named import (`import { foo }`) for a default export (`export default foo`), or vice versa. This often compiles without errors but produces `undefined` at runtime.

**How to catch:** Gate 3 (Imports) — verify that import style matches export style for every changed import.

### Dead Code
The AI writes a utility function, helper component, or variable that is never used. This is not just clutter — it signals that the AI intended to wire something up but forgot.

**How to catch:** Gate 2 (Lint) — most linters flag unused variables and functions.

### React Anti-Patterns
- Missing dependency arrays in `useEffect` (causes stale closures or infinite loops)
- Mutating state directly instead of using setter functions
- Conditional hook calls (hooks called inside if-statements)
- Missing `key` props in list renders

**How to catch:** Gate 2 (Lint with React plugin), Gate 5 (Tests), Gate 6 (Behavior).

### Mock Leaks in Tests
The AI sets up a mock in one test but does not clean it up, causing the mock to leak into subsequent tests. Tests pass individually but fail when run together.

**How to catch:** Gate 5 (Tests) — run the full suite, not just individual tests. If a test passes alone but fails in the suite, suspect mock leakage.

### Stale References After Refactoring
The AI renames a function, component, or file but does not update all references. The build might still pass (if the old name is still exported somewhere), but the behavior is wrong.

**How to catch:** Gate 4 (References) — after any rename or move, search the codebase for the old name.

---

## Verification Mindset

Verification is not busywork. It is the quality layer that makes AI-assisted development reliable. The cost of running six gates is measured in seconds. The cost of skipping them is measured in hours of debugging, failed deployments, and eroded trust in AI-generated code.

Make verification a habit, not an afterthought. The best time to catch a bug is immediately after it is introduced, while the context is still in your head and the AI's context window.
