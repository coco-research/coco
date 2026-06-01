# /team — Hard Test-Evidence Gate (anti test-theater)

**Status:** IMPLEMENTED 2026-05-31 (superseded/expanded by the ship-pipeline plan below)
**Priority:** High
**Logged:** 2026-05-30

> **Implemented.** The richer forensic plan
> `team-ship-testing-integrity-fix-plan-2026-05-30.md` (this directory) was
> verified against the real `~/Marvin` repo (all 8 PR-#473 commit SHAs confirmed;
> CI confirmed to run pytest with no Postgres/DSN) and implemented in both source
> (`~/coco/commands/team/`) and live (`~/.claude/commands/`):
> - New shared protocol `commands/team/evidence.md` (Test Evidence Protocol).
> - `ship.md` expanded with 7 hard gates (Stages 7–13) + PR-open gate (Stage 14).
> - `test.md`, `develop.md`, `verify.md` rewired to run the protocol and capture `EVIDENCE.md`.
> - `roles.md` qa-test-architect anti-theater rule; `toolkit.md` protocol entry.
> - Regression guard `tests/check-evidence-gate.sh` wired into smoke + CI.
>
> The 5 edits below were the original (lighter) framing; the implemented version
> is the superset described above.

## Problem

When `/team develop`, `/team test`, `/team ship`, or `/team verify` is asked to
"create and run proper tests," the pipeline can produce an *illusion* of tests:
a Layer 2 subagent reports "wrote N tests, all passing" while no test file was
actually created or executed. The orchestrator trusts the self-reported summary,
and the final report says COMPLETE. No command ever ran.

Root cause: nowhere in the pipeline is hard execution evidence (raw test-runner
output + exit code) required or independently verified. Instructions say "run
tests to verify they pass" but never demand proof, and Layer 3 reviews test
*descriptions* rather than test *execution*.

## Fix — 5 edits, applied to BOTH source (`~/coco/commands/team/`) and live (`~/.claude/commands/`)

1. **Orchestrator runs the suite itself.** After Layer 2, the orchestrator (not a
   subagent) runs the project's test command via Bash, capturing the exact
   command, exit code, pass/fail/skip counts, and the raw output tail into a
   `TEST-EVIDENCE.md` artifact. Truth comes from the orchestrator's own run, not
   from agent claims. Edit: `_index.md` regression section (~line 432) and
   `test.md` / `develop.md` regression sections.

2. **L2 test/dev agents must return execution proof.** Each agent that claims
   tests pass must return: exact command, exit code, pass/fail/skip counts, and
   raw output tail. Missing proof is treated as NOT RUN (not as success). Edit:
   `test.md` Layer 2, `develop.md` Layer 2 prompt requirements.

3. **Anti-theater rule.** Add to the `qa-test-architect` role (`roles.md`) and to
   `test.md` / `develop.md` / `verify.md`: "No PASS without exit-0 proof. Tests
   that are empty, placeholder, `assert True`, or unconditionally skipped count as
   FAIL, not PASS."

4. **L3 verifies execution, not prose.** Change Layer 3 in `test.md` and
   `develop.md` so reviewers re-run the suite (or audit the captured
   `TEST-EVIDENCE.md`) and confirm assertions are non-trivial. Ban "reviewing test
   descriptions" as a substitute for verifying execution.

5. **Pipeline gate.** If there is no green evidence artifact (exit 0), the run
   reports **BLOCKED**, never **COMPLETE**. Edit: `_index.md` Step 6 report logic.

## Acceptance

- A `/team develop` / `/team test` run that produces no real tests reports BLOCKED.
- `TEST-EVIDENCE.md` exists with command + exit code + counts + raw tail.
- Source and live copies match (survives `adapters/claude-code/install.sh` redeploy).
- Consider a guard test (like `tests/check-command-refs.sh`) asserting the
  evidence-gate language is present in the relevant command files.

## Related

- Prior fix (done 2026-05-30): hyphen→colon companion-file references +
  `tests/check-command-refs.sh` CI guard. The path bug meant `qa-test-architect`
  often failed to load, compounding the theater problem. With refs fixed, the test
  specialist now loads — making this evidence gate effective.
