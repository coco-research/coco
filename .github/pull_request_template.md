<!-- Keep this short. A PR nobody can review in two minutes is not a small PR. -->

## What this changes

<!-- One or two sentences. What behaves differently after this merges? -->

## Why

<!-- The problem. Link the task in docs/tasks.md. -->

## How it was verified

<!-- Paste the real command and its real output. Not a summary of it. -->

```
$ cargo test --workspace
```

## Checklist

- [ ] Gate is green (`git push` ran the hook)
- [ ] `docs/tasks.md` updated if this closes or opens a task
- [ ] `docs/memory.md` updated if this settled a decision or a dead end
- [ ] No secret, key, or personal path added to any file, including docs
- [ ] If a documented invariant changed, `docs/rules.md` is updated here too

## Risk

<!-- What could this break, and what is the rollback? -->