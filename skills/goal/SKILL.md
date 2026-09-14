---
name: goal
description: Persistent project goal that survives across sessions and tools, with continuous-execution loop semantics. Use when someone asks to "set a goal", "what is my goal", "goal status", "keep working on X until done", "resume the goal", or wants work to continue across sessions until an objective is achieved. File-backed (.goal.md at project root); shared by every Coco-installed tool working in that repository.
domain: meta
---

# Goal — persistent project objective

A goal is a single objective the agent keeps pursuing across turns and
sessions until it is marked done. Inspired by Prime Agent's thread goal:
state lives outside any one conversation, so any tool with this skill
installed (Claude Code, Cursor, Codex, ...) picks up where another left off.

## State file

One file per project: `.goal.md` in the repository root. Human-readable and
human-editable on purpose — pause, resume, edit, and clear are controlled by
the user editing the file directly.

```markdown
---
objective: Ship release notes for v2.3
status: active        # active | paused | done
created: 2026-08-22
---

## Progress
- 2026-08-22 14:02 — drafted changelog from git log
```

Optional sections the loop reads if present: `## Queue` (ordered work items),
`## Standing constraints` (owner-set rules that bind every session),
`## Decisions` (recorded owner calls — binding, never re-litigated),
`## Done criteria`.

## API

- **get** — read `.goal.md`. No file means no goal is set. Report the
  objective, status, and latest progress entries when asked about goal status.
- **create(objective)** — write `.goal.md` with `status: active` and today's
  date. If an `active` goal already exists, do NOT silently replace it; show
  it and ask whether to complete, pause, or replace. Only create a goal when
  the user explicitly asks for a persistent goal; do not infer goals from
  ordinary tasks.
- **update(note)** — append one dated line to `## Progress` after each
  meaningful work session toward the goal. Keep notes short and factual.
- **complete()** — set `status: done`. Only when the objective has actually
  been achieved and no required work remains — not because the session is
  ending or momentum ran out.

## Session behavior

At the start of a session in a repo containing `.goal.md`:

- `status: active` — surface the objective to the user, then ENTER THE WORK
  LOOP below before starting unrelated work.
- `status: paused` — mention it exists; resume only if the user asks.
- `status: done` — leave it as history; offer to archive or replace.

## Work loop (continuous execution)

An active goal with remaining actionable items means you run a LOOP, not a
single pass. One iteration:

1. **Resume** — read `.goal.md` plus the newest handoff document it references
   (typically under `docs/plans/`). Verify recorded receipts against reality
   (HEAD sha, merged PRs, live state) before trusting them.
2. **Pick** the highest-priority item that is actionable right now — from the
   Queue, the referenced workorder, or the handoff's "exact next action".
3. **Journal before acting** — append `TODO <task>` to `## Progress`. If the
   session dies here, a successor knows precisely what was attempted.
4. **Execute** — do the work. Run the real gates. Commit/PR per whatever
   authority the goal grants (e.g., self-review-and-merge if so recorded).
5. **Journal after** — append `DONE <task> — <receipt>` immediately. Receipt =
   commit sha, PR number, test counts, or posted artifact. No receipt, not done.
6. **Repeat** from step 2 while an actionable item remains and no STOP
   condition applies.

Never end a turn with actionable items outstanding unless a STOP condition
fired. "Momentum ran out" is not a stop condition.

## Failure resilience

- **Transient LLM/API/tool failures** — timeouts, 429/5xx, dropped
  connections — are NEVER stop conditions. Retry with backoff (≈30s → 60s →
  120s, cap ~5 attempts). If one dependency stays down, journal `BLOCKED <item>
  — <reason>`, switch to the next non-dependent actionable item, and circle back.
- **Crash/interrupt safety**: because TODO precedes work and DONE follows it,
  an interrupted session loses nothing. On resume, a task with TODO and no DONE
  is simply not started yet — verify no half-committed debris, then restart it.
- **Tool/environment failure ≠ task failure.** A failing gate gets diagnosed;
  a failing external service gets routed around; neither ends the loop.
- **Flaky tests** fail-then-pass-isolated are recorded as known-flaky, not
  treated as regressions — but always rerun isolated before concluding that.

## Stop conditions (the ONLY reasons to end the loop)

1. **Done** — goal achieved; call `complete()`.
2. **Blocked on owner** — every remaining item needs an answer only the owner
   can give. Post the questions (one line each), mark items BLOCKED/DEFERRED,
   update `.goal.md`, stop with a clear summary of what you need.
3. **Context limit approaching** — write the handoff document (see Handoff),
   append the final Progress line, stop cleanly.
4. **Repeated hard failure** — ≥3 consecutive unrecoverable failures across
   DIFFERENT items (not retries of one) → write an incident note into Progress
   and the handoff, stop, report to owner.

Everything else — API flakiness, slow builds, flaky tests, waiting on a local
service — is worked through or routed around.

## Handoff (graceful exit)

If the repo keeps committed plan/handoff documents (e.g., `docs/plans/`), the
graceful exit is: write/update the handoff file containing exact HEAD sha, PRs
landed this session, current queue position, receipts, known gotchas, and the
exact next action — then append the final Progress line to `.goal.md`, then
stop. Ending a session without those two writes is a defect: the successor
must be able to resume from `.goal.md` + the latest handoff alone.

## Rules

- One active goal per repository. The file is the source of truth — never keep
  goal state only in conversation memory.
- Never delete or rewrite past progress lines; append.
- Completion must reflect reality. An agent that marks a half-finished goal
  done defeats the entire mechanism.
- Standing constraints and recorded decisions inside `.goal.md` bind every
  session and outrank this skill's defaults.
- Journal honestly: a TODO line without a matching DONE line is expected and
  safe; a DONE line without receipts is a lie.

## Harness note (out of skill scope)

This skill makes the AGENT persistent within a session and recoverable across
sessions. Fully automatic relaunch after a dead session requires harness-level
scheduling (cron/gateway/watchdog) outside any skill's control. If the owner
wants unattended overnight loops, pair this skill with a scheduler that
re-invokes the agent with "resume the goal".
