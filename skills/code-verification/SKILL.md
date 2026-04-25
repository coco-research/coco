---
name: code-verification
description: Post-implementation verification system that catches AI-introduced bugs. Covers 7 categories — TDZ errors, import mismatches, reference integrity, dead code, React state/effects, mock isolation, and CSS integrity. Run after every code change, after writing tests, or before marking a task complete. Triggers on "verify", "check code quality", "run verification", "audit code", "quality gate", "pre-commit check".
---

# Code Verification Skill

A systematic post-implementation verification workflow that catches the bugs AI coding assistants most commonly introduce. This is NOT a code review for style or architecture — it is a mechanical correctness checklist that catches structural errors (TDZ, imports, dead code, mock leakage, CSS orphans, React anti-patterns) that humans and AI both miss during implementation.

## When to Use

- **After every code change** (1-2 files changed -> run immediately)
- **After a multi-file feature** (run on all changed files in one pass)
- **After writing/modifying tests** (switch to Test Verification mode)
- **Before marking any task complete** (final gate)
- **When a subagent completes work** (verify their output)
- **When user says**: "verify", "check quality", "audit code", "run verification", "quality gate", "pre-commit check"

## Quick Start

```
1. Identify changed files (git diff --name-only or manual list)
2. Run the 7-category checklist below on each file
3. Run automated checks (build, lint, tests)
4. Report findings as PASS / FAIL / WARNING
5. Fix all FAIL items before proceeding
```

---

## The 7-Category Verification Checklist

### Category 1: Variable Declaration Order (TDZ Prevention)

**What to check:** Variables, constants, and hooks used BEFORE their declaration in the same scope.

**How it breaks:** JavaScript `const` and `let` have a "temporal dead zone" — referencing them before their declaration line throws `ReferenceError` at runtime, but no build error.

**React-specific**: `useMemo`, `useCallback`, `useEffect` that reference state or derived values declared later in the component. This is the #1 AI-introduced bug.

**Scan pattern:**
- For every `useMemo`, `useCallback`, `useEffect`: check that ALL variables in the dependency array AND the callback body are declared ABOVE that hook.
- For every function that references a `const`/`let`: check the declaration is above the function definition.
- For every destructured import used in a module-level `const`: check for circular dependencies.

**Real examples caught:**
- `activeQuestions` useMemo referenced 150 lines before its declaration
- `baseDeps` used in JSX but handler functions declared 100 lines later
- `DR_FIELDS` referenced in `NFR_CATALOG` before `export const DR_FIELDS` line

**Fix:** Move the declaration above all usages. If it's a React hook, reorder hooks so dependencies come first.

---

### Category 2: Import/Export Integrity

**What to check:** Every import resolves to a real export. Named vs default matches.

**How it breaks:** Build may succeed (tree-shaking ignores dead imports in dev mode) but runtime throws `undefined is not a function`.

**Scan pattern:**
- For each `import { X } from './file'`: open `./file` and confirm `export { X }` or `export const X` or `export function X` exists.
- For each `import X from './file'`: confirm `export default X` exists.
- Flag: `import { X } from './file'` when file only has `export default X` (or vice versa).

**Real examples caught:**
- `useResizeHandle` imported as default when it's a named export
- `ConfluencePagePicker` imported as default when it's a named export
- Removed component still imported in 3 files

**Automated check:**
```bash
npx eslint --rule '{"import/named": "error", "import/default": "error"}' src/
```

---

### Category 3: Reference Integrity

**What to check:** After any rename/remove/move, ALL usages of the old name are updated.

**Scan pattern:**
- Search for ALL usages of the old name across the project
- Verify zero references remain to removed identifiers
- Check that moved code doesn't reference variables from its old scope

**Real examples caught:**
- `setPrdDocViewMode` was removed but `Cmd+E` handler still called it
- Removed component still imported in 3 files

```javascript
// BUG: setPrdDocViewMode was removed but Cmd+E handler still calls it
useEffect(() => {
  const handler = (e) => {
    if (e.metaKey && e.key === 'e') setPrdDocViewMode(prev => ...);  // ReferenceError
  };
}, []);
```

---

### Category 4: Dead Code Detection

**What to check:** Unused imports, unreachable code, orphaned handlers.

**Scan pattern:**
- Unused imports: variable imported but never referenced in file body.
- Orphaned event handlers: `onClick={handleFoo}` removed from JSX but `const handleFoo = ...` still declared.
- Unreachable code: `return` before a code block, `if (false)` guard, feature-flagged code where flag is always false.
- State setters never called: `const [x, setX] = useState()` where `setX` appears nowhere.
- Functions defined but never called.

**Automated check:**
```bash
npx eslint --rule '{"no-unused-vars": "error", "no-unreachable": "error"}' src/file.jsx
```

---

### Category 5: React State & Effects

**What to check:** State variables are used, effects clean up, no updates after unmount, correct dependencies.

#### 5.1 Component Reuse Bugs
When the same component renders for multiple routes (e.g., `OperationalDocEditor` for DR/IRP/Recovery):
- Does it have a `key={uniqueId}` to force remount on route change?
- Does it reset internal state when props change?

#### 5.2 Effect Dependencies
For every `useEffect`:
- Are all referenced variables in the dependency array?
- Are object/array deps stable (memoized) or will they trigger infinite re-renders?
- Does the cleanup function undo what the effect created?

#### 5.3 Ref Safety
- Is `ref.current` used in the render return? (Should be state instead — ref changes don't trigger re-render)
- Are refs initialized before first access? (Common with resize handles)
- Does `useRef` get set in an effect that runs after the component mounts?

#### 5.4 Async State Updates
- Does any async callback (fetch, setTimeout) update state after potential unmount?
- Is there a cleanup function that cancels pending operations?
- Every `useEffect` that calls an async function should have an abort/cancel mechanism.

**Real examples caught:**
- `initialLoadRef` set to `true` before async data arrived, blocking subsequent updates
- `useResizeHandle` ref null on mount because empty state rendered first (MutationObserver fix needed)
- DR/IRP/Recovery shared `OperationalDocEditor` reused state across route changes (fixed with `key={docType}`)
- `prdDocViewMode` state removed but `Cmd+E` handler still called `setPrdDocViewMode`

#### Common React Anti-Patterns

| Anti-Pattern | Why It Breaks | Fix |
|---|---|---|
| Mutating state directly (`state.push(x)`) | React won't re-render | `setState([...state, x])` |
| Object/array in `useEffect` deps | New reference every render -> infinite loop | `useMemo` the dep, or use primitive |
| `ref.current` in render return | Ref changes don't trigger re-render | Use state instead |
| `history.pushState` with `#fragment` in hash router | Double-hash URL breaks navigation | Use state-based tracking |
| Inline object as prop (`style={{ color: 'red' }}`) | New reference every render, breaks `memo` | Extract to `useMemo` or module-level const |
| `useEffect` missing cleanup for async | State update on unmounted component | AbortController or mounted flag |

---

### Category 6: Mock Isolation (Test Files Only)

**What to check:** Mocks don't leak between tests. Fake timers are restored. Tests are meaningful.

#### 6.1 Mock Leakage
- `vi.mock()` / `jest.mock()` at module level: OK
- `mockImplementation()` inside a `describe` without `afterEach(() => mock.mockReset())`: LEAK RISK
- `vi.useFakeTimers()` without corresponding `vi.useRealTimers()` in `afterEach`: LEAK
- `mockResolvedValueOnce` chains: fragile if test execution order changes. Prefer `mockImplementation` that inspects the call.
- Multiple `describe` blocks sharing the same `fetch.mock` without isolation: INTERFERENCE

#### 6.2 Tautological Tests
Tests that can never fail:
- Asserting a mock's return value equals itself
- `expect(x).toBeDefined()` where x is hardcoded in setup
- `expect(fn).toHaveBeenCalled()` immediately after calling fn yourself
- `expect(array.length).toBeGreaterThanOrEqual(0)` (always true)

#### 6.3 Query Specificity
- `getByText` / `getByRole` that matches multiple elements -> use `getAllBy*` or scope with `within()`
- Tests that pass because they find the wrong element (e.g., finding a button label that also appears in a tooltip)

#### 6.4 Meaningful Assertions
- Every test should have at least one assertion
- Tests should assert behavior, not just "it renders"
- Snapshot tests should be small enough to review

**Real examples caught:**
- Jira test: `mockResolvedValueOnce` chain broke when test order changed; fixed with request-inspecting `mockImplementation`
- `ConfluencePagePicker`: fake timers from one test leaked into search filter test
- `NFRTracker`: missing `SettingsContext` mock caused cascading failures

---

### Category 7: CSS Class Integrity

**What to check:** Every `className` in JSX has a corresponding CSS rule. No orphaned selectors.

#### 7.1 Class Name Integrity
- Extract all `className="..."` and `className={`...`}` values from the JSX file.
- For each class, search the associated CSS file(s) for `.classname`.
- Flag: class used in JSX but not defined in CSS (will silently fail — no visual, no error).
- Flag: class defined in CSS but not used in any JSX (dead CSS — bloat).

**Note:** Dynamic classes like `className={isActive ? 'active' : ''}` need both branches checked.

#### 7.2 CSS Variable Integrity
For every `var(--token)` in CSS:
- Is the variable defined in `:root` or a parent selector?
- Is it defined for both light and dark themes?

---

## Automated Verification Script

Run these commands after any code change:

```bash
# 1. Build check
npm run build

# 2. Lint check (catches unused vars, unreachable code)
npx eslint src/path/to/changed/file.jsx

# 3. Test check (run tests for changed file)
npx vitest run src/path/to/changed/file.test.jsx

# 4. Full suite (after a feature is complete)
npx vitest run

# 5. Circular dependency check (if available)
npx madge --circular src/
```

---

## Report Template

Use this format when reporting verification results:

```markdown
## Verification Report — [Project Name]
**Date:** [YYYY-MM-DD]
**Files checked:** [list]
**Tool:** code-verification skill

### PASS
- `path/to/file.jsx` — All 7 categories checked, no issues

### FAIL (must fix before proceeding)
- `path/to/file.jsx:142` — [CAT 1: TDZ] `activeQuestions` referenced before declaration
  **Fix:** Move `const activeQuestions = useMemo(...)` to line 95 (before `showClarifyingQuestions`)

### WARNING (review, may be intentional)
- `path/to/file.jsx:88` — [CAT 4: DEAD CODE] `const [oldState, setOldState]` — setOldState never called
  **Likely:** Leftover from removed feature. Remove if confirmed unused.

### Summary
| Category | Pass | Fail | Warn |
|----------|------|------|------|
| 1. TDZ | 4 | 1 | 0 |
| 2. Imports | 5 | 0 | 0 |
| 3. References | 5 | 0 | 0 |
| 4. Dead Code | 4 | 0 | 1 |
| 5. React State | 3 | 0 | 2 |
| 6. Mocks | 3 | 0 | 1 |
| 7. CSS | 5 | 0 | 0 |
```

---

## Integration with Agents

This skill is the workflow. The agents are the executors:

| Agent | Role | When |
|-------|------|------|
| `verification-agent` | Runs Categories 1-5, 7 on product code | After implementation |
| `test-guardian` | Runs Category 6 on test code | After writing tests |
| `code-reviewer` | Broader quality review (SOLID, perf, security) | Before merge/deploy |

## Integration with Rules

| Rule | Role | When |
|------|------|------|
| `quality-gate.mdc` | Enforces 6 mandatory checks after every edit | Always (auto-applied) |
| `pre-implementation-checklist.mdc` | Prevents bugs before they're written | Always (auto-applied) |

## Quick Commands

```bash
# Run all tests for a specific file
npx vitest run path/to/file.test.jsx

# Run full test suite
npx vitest run

# Build check
npm run build

# Lint check
npx eslint src/path/to/changed/file.jsx
```

## When to Skip Verification

- Editing **only** markdown, docs, or comments (no executable code)
- Adding a `TODO` comment
- Changing **only** CSS values (not selectors or class names)
- Reverting a commit (restoring known-good state)

## When Verification is MANDATORY (No Exceptions)

- Any `.jsx`, `.js`, `.ts`, `.tsx` file edit
- Any file rename or move
- Any import/export change
- Any React hook addition, removal, or reordering
- Any state variable addition or removal
- Any test file modification
- After running `npm install` or changing `package.json`
- After merging branches or resolving conflicts
- After a subagent completes work in another window
