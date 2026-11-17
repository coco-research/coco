# Testing Patterns Template

Template for `.planning/codebase/TESTING.md` - captures test framework and patterns.

**Purpose:** Document how tests are written and run. Guide for adding tests that match existing patterns.

---

## File Template

```markdown
# Testing Patterns

**Analysis Date:** [YYYY-MM-DD]

## Test Framework

**Runner:**
- [Framework: e.g., "Jest 29.x", "Vitest 1.x"]
- [Config: e.g., "jest.config.js in project root"]

**Assertion Library:**
- [Library: e.g., "built-in expect", "chai"]
- [Matchers: e.g., "toBe, toEqual, toThrow"]

**Run Commands:**
```bash
[e.g., "npm test" or "npm run test"]              # Run all tests
[e.g., "npm test -- --watch"]                     # Watch mode
[e.g., "npm test -- path/to/file.test.ts"]       # Single file
[e.g., "npm run test:coverage"]                   # Coverage report
```

## Test File Organization

**Location:**
- [Pattern: e.g., "*.test.ts alongside source files"]
- [Alternative: e.g., "__tests__/ directory" or "separate tests/ tree"]

**Naming:**
- [Unit tests: e.g., "module-name.test.ts"]
- [Integration: e.g., "feature-name.integration.test.ts"]
- [E2E: e.g., "user-flow.e2e.test.ts"]

**Structure:**
```
[Show actual directory pattern, e.g.:
src/
  lib/
    utils.ts
    utils.test.ts
  services/
    user-service.ts
    user-service.test.ts
]
```

## Test Structure

**Suite Organization:**
```typescript
[Show actual pattern used, e.g.:

describe('ModuleName', () => {
  describe('functionName', () => {
    it('should handle success case', () => {
      // arrange
      // act
      // assert
    });

    it('should handle error case', () => {
      // test code
    });
  });
});
]
```

**Patterns:**
- [Setup: e.g., "beforeEach for shared setup, avoid beforeAll"]
- [Teardown: e.g., "afterEach to clean up, restore mocks"]
- [Structure: e.g., "arrange/act/assert pattern required"]

## Mocking

**Framework:**
- [Tool: e.g., "Jest built-in mocking", "Vitest vi", "Sinon"]
- [Import mocking: e.g., "vi.mock() at top of file"]

**Patterns:**
```typescript
[Show actual mocking pattern, e.g.:

// Mock external dependency
vi.mock('./external-service', () => ({
  fetchData: vi.fn()
}));

// Mock in test
const mockFetch = vi.mocked(fetchData);
mockFetch.mockResolvedValue({ data: 'test' });
]
```

**What to Mock:**
- [e.g., "External APIs, file system, database"]
- [e.g., "Time/dates (use vi.useFakeTimers)"]
- [e.g., "Network calls (use mock fetch)"]

**What NOT to Mock:**
- [e.g., "Pure functions, utilities"]
- [e.g., "Internal business logic"]

## Fixtures and Factories

**Test Data:**
```typescript
[Show pattern for creating test data, e.g.:

// Factory pattern
function createTestUser(overrides?: Partial<User>): User {
  return {
    id: 'test-id',
    name: 'Test User',
    email: 'test@example.com',
    ...overrides
  };
}

// Fixture file
// tests/fixtures/users.ts
export const mockUsers = [/* ... */];
]
```

**Location:**
- [e.g., "tests/fixtures/ for shared fixtures"]
- [e.g., "factory functions in test file or tests/factories/"]

## Coverage

**Requirements:**
- [Target: e.g., "80% line coverage", "no specific target"]
- [Enforcement: e.g., "CI blocks <80%", "coverage for awareness only"]

**Configuration:**
- [Tool: e.g., "built-in coverage via --coverage flag"]
- [Exclusions: e.g., "exclude *.test.ts, config files"]

**View Coverage:**
```bash
[e.g., "npm run test:coverage"]
[e.g., "open coverage/index.html"]
```

## Test Types

**Unit Tests:**
- [Scope: e.g., "test single function/class in isolation"]
- [Mocking: e.g., "mock all external dependencies"]
- [Speed: e.g., "must run in <1s per test"]

**Integration Tests:**
- [Scope: e.g., "test multiple modules together"]
- [Mocking: e.g., "mock external services, use real internal modules"]
- [Setup: e.g., "use test database, seed data"]

**E2E Tests:**
- [Framework: e.g., "Playwright for E2E"]
- [Scope: e.g., "test full user flows"]
- [Location: e.g., "e2e/ directory separate from unit tests"]

## Common Patterns

**Async Testing:**
```typescript
[Show pattern, e.g.:

it('should handle async operation', async () => {
  const result = await asyncFunction();
  expect(result).toBe('expected');
});
]
```

**Error Testing:**
```typescript
[Show pattern, e.g.:

it('should throw on invalid input', () => {
  expect(() => functionCall()).toThrow('error message');
});

// Async error
it('should reject on failure', async () => {
  await expect(asyncCall()).rejects.toThrow('error message');
});
]
```

**Snapshot Testing:**
- [Usage: e.g., "for React components only" or "not used"]
- [Location: e.g., "__snapshots__/ directory"]

---

*Testing analysis: [date]*
*Update when test patterns change*
```

<good_examples>
```markdown
# Testing Patterns

**Analysis Date:** 2025-01-20

## Test Framework

**Runner:**
- Vitest 1.0.4
- Config: vitest.config.ts in project root

**Assertion Library:**
- Vitest built-in expect
- Matchers: toBe, toEqual, toThrow, toMatchObject

**Run Commands:**
```bash
npm test                              # Run all tests
npm test -- --watch                   # Watch mode
npm test -- path/to/file.test.ts     # Single file
npm run test:coverage                 # Coverage report
```

## Test File Organization

**Location:**
- *.test.ts alongside source files
- No separate tests/ directory

**Naming:**
- unit-name.test.ts for all tests
- No distinction between unit/integration in filename

**Structure:**
```
src/
  lib/
    parser.ts
    parser.test.ts
  services/
    install-service.ts
    install-service.test.ts
  bin/
    install.ts
    (no test - integration tested via CLI)
```

## Test Structure

**Suite Organization:**
```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('ModuleName', () => {
  describe('functionName', () => {
    beforeEach(() => {
      // reset state
    });

    it('should handle valid input', () => {
      // arrange
      const input = createTestInput();

      // act
      const result = functionName(input);

      // assert
      expect(result).toEqual(expectedOutput);
    });

    it('should throw on invalid input', () => {
      expect(() => functionName(null)).toThrow('Invalid input');
    });
  });
});
```

**Patterns:**
- Use beforeEach for per-test setup, avoid beforeAll
- Use afterEach to restore mocks: vi.restoreAllMocks()
- Explicit arrange/act/assert comments in complex tests
- One assertion focus per test (but multiple expects OK)

## Mocking

**Framework:**
- Vitest built-in mocking (vi)
- Module mocking via vi.mock() at top of test file

**Patterns:**
```typescript
import { vi } from 'vitest';
import { externalFunction } from './external';

// Mock module
vi.mock('./external', () => ({
  externalFunction: vi.fn()
}));

describe('test suite', () => {
  it('mocks function', () => {
    const mockFn = vi.mocked(externalFunction);
    mockFn.mockReturnValue('mocked result');

    // test code using mocked function

    expect(mockFn).toHaveBeenCalledWith('expected arg');
  });
