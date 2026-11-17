# Common Bug Patterns

Checklist of frequent bug patterns to scan before forming hypotheses. Ordered by frequency. Check these FIRST — they cover ~80% of bugs across all technology stacks.

<patterns>

## Null / Undefined Access

- **Null property access** — accessing property on `null` or `undefined`, missing null check or optional chaining
- **Missing return value** — function returns `undefined` instead of expected value, missing `return` statement or wrong branch
- **Destructuring null** — array/object destructuring on `null`/`undefined`, API returned error shape instead of data
- **Undefaulted optional** — optional parameter used without default, caller omitted argument

## Off-by-One / Boundary

- **Wrong loop bound** — loop starts at 1 instead of 0, or ends at `length` instead of `length - 1`
