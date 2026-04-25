# Verification Failure Example — Catching a Missing Test

This walkthrough shows how the `verification-before-completion` skill's 6-gate system catches incomplete work before the AI claims "done."

---

## Scenario

**Task:** Add a `calculateDiscount()` function to the checkout module.

The AI has just finished implementing the function in `src/checkout/pricing.ts`. It is about to say "Done! The discount calculation is implemented and working." But first, the verification gates must pass.

---

## Gate-by-Gate Walkthrough

### Gate 1: Requirements Trace

**Check:** Does the implementation satisfy every acceptance criterion from the task?

The task specified:
- [x] Function accepts `orderTotal` (number) and `discountCode` (string)
- [x] Returns `{ discountedTotal, savings, discountPercent }`
- [x] Supports percentage and fixed-amount discount types
- [x] Returns original total if code is invalid (no error thrown)

**Result: PASS** — All four acceptance criteria are addressed in the implementation.

---

### Gate 2: Code Runs

**Check:** Does the code compile and execute without errors?

```
$ tsc --noEmit
$ node -e "require('./dist/checkout/pricing').calculateDiscount(100, 'SAVE10')"
{ discountedTotal: 90, savings: 10, discountPercent: 10 }
```

**Result: PASS** — Compiles cleanly, runs without errors, returns expected output.

---

### Gate 3: Imports & Dependencies

**Check:** Are all new exports consumed? Are all new modules imported where needed? Is the test file updated?

The gate checks:
- `calculateDiscount` is exported from `pricing.ts` — yes
- `calculateDiscount` is re-exported from `src/checkout/index.ts` — yes
- `tests/checkout/pricing.test.ts` exists and imports `calculateDiscount` — **NO**

```
$ grep -r "calculateDiscount" tests/
(no results)
```

**Result: FAIL** — The function was implemented but no test was written. The existing test file `tests/checkout/pricing.test.ts` has tests for `calculateSubtotal` and `applyTax` but nothing for the new function.

---

### Gates 4-6: Skipped (First Pass)

Gates 4 (References), 5 (Tests), and 6 (Behavior) are not evaluated because Gate 3 failed. The verification system stops at the first failure and requires a fix before proceeding.

---

## Remediation

The AI acknowledges the gap and writes the missing tests:

```typescript
// tests/checkout/pricing.test.ts (additions)

describe('calculateDiscount', () => {
  it('applies percentage discount correctly', () => {
    const result = calculateDiscount(100, 'SAVE10');
    expect(result).toEqual({
      discountedTotal: 90,
      savings: 10,
      discountPercent: 10,
    });
  });

  it('applies fixed-amount discount correctly', () => {
    const result = calculateDiscount(100, 'FLAT15');
    expect(result).toEqual({
      discountedTotal: 85,
      savings: 15,
      discountPercent: 15,
    });
  });

  it('returns original total for invalid code', () => {
    const result = calculateDiscount(100, 'INVALID');
    expect(result).toEqual({
      discountedTotal: 100,
      savings: 0,
      discountPercent: 0,
    });
  });

  it('handles zero total', () => {
    const result = calculateDiscount(0, 'SAVE10');
    expect(result).toEqual({
      discountedTotal: 0,
      savings: 0,
      discountPercent: 10,
    });
  });

  it('caps discount so total never goes negative', () => {
    const result = calculateDiscount(10, 'FLAT15');
    expect(result).toEqual({
      discountedTotal: 0,
      savings: 10,
      discountPercent: 100,
    });
  });
});
```

---

## Re-Running All 6 Gates

Gates 1-3 pass as before (requirements addressed, code compiles, imports and test file now exist). Here is the detailed walkthrough for Gates 4-6:

### Gate 4: References

**Check:** Are all usages of the new function consistent across the codebase? No stale references, no files importing old names, no leftover TODOs pointing at a placeholder.

```
$ grep -rn "calculateDiscount" src/ tests/
src/checkout/pricing.ts:42:export function calculateDiscount(orderTotal: number, discountCode: string)
src/checkout/index.ts:3:export { calculateDiscount } from './pricing';
tests/checkout/pricing.test.ts:5:import { calculateDiscount } from '../../src/checkout/pricing';
tests/checkout/pricing.test.ts:8:  const result = calculateDiscount(100, 'SAVE10');
```

No file imports a stale name, no unused re-exports, and every reference points at the real implementation. **Result: PASS** — `calculateDiscount` is properly exported from `pricing.ts`, re-exported from the barrel `index.ts`, and imported correctly in the test file.

---

### Gate 5: Tests

**Check:** Run the full test suite for the changed files. Every test — existing and new — must pass.

```
$ npm test -- --testPathPattern=pricing

 PASS  tests/checkout/pricing.test.ts
  calculateSubtotal
    ✓ sums line items (3 ms)
  applyTax
    ✓ applies tax rate (1 ms)
  calculateDiscount
    ✓ applies percentage discount correctly (1 ms)
    ✓ applies fixed-amount discount correctly (1 ms)
    ✓ returns original total for invalid code (1 ms)
    ✓ handles zero total (1 ms)
    ✓ caps discount so total never goes negative (1 ms)

Tests:  8 passed, 8 total
Time:   0.42 s
```

All 8 tests pass with exit code 0, including the 5 new `calculateDiscount` tests and the 3 pre-existing tests for `calculateSubtotal` and `applyTax`. **Result: PASS** — No regressions, and the new function is fully covered.

---

### Gate 6: Behavior

**Check:** Does the discount actually work correctly in the broader checkout flow? This is a manual/behavioral sanity check — verify the function integrates properly, not just that unit tests pass in isolation.

```
$ node -e "
  const { calculateSubtotal } = require('./dist/checkout/pricing');
  const { calculateDiscount } = require('./dist/checkout/pricing');
  const subtotal = calculateSubtotal([{ price: 40, qty: 3 }]); // 120
  const result = calculateDiscount(subtotal, 'SAVE10');
  console.log('Subtotal:', subtotal, '→ After discount:', result);
"
Subtotal: 120 → After discount: { discountedTotal: 108, savings: 12, discountPercent: 10 }
```

The function chains correctly with `calculateSubtotal` — a realistic checkout path. The discount applies to the computed subtotal, returns the right savings, and the discounted total flows naturally into downstream steps like tax calculation. **Result: PASS** — The function integrates properly in the checkout flow, not just in isolated test harnesses.

---

### Summary

| Gate | Check | Result |
|------|-------|--------|
| 1. Requirements Trace | All acceptance criteria addressed | PASS |
| 2. Code Runs | Compiles and executes | PASS |
| 3. Imports & Dependencies | Tests exist and import new function | PASS |
| 4. References | All usages consistent, no stale imports | PASS |
| 5. Tests | `npm test -- pricing` exits 0, all 8 tests pass | PASS |
| 6. Behavior | Discount integrates correctly in checkout flow | PASS |

All 6 gates pass. The AI can now confidently say the work is complete.

---

## Key Takeaway

Without the verification gates, the AI would have claimed "done" after writing the function — leaving a gap that only shows up later during code review or CI. Gate 3 caught the missing test within seconds, before any human had to review the code.

**The pattern:** Verification gates turn implicit assumptions ("surely I wrote tests") into explicit checks ("grep confirms tests exist and pass"). This is especially valuable for AI agents, which are prone to declaring success after the "interesting" part of the work (implementation) while skipping the "boring" part (testing).

---

*This walkthrough demonstrates the `verification-before-completion` skill from the Superpowers tier of the how-i-pm-with-ai framework.*
