# Tasks: the live board

What is being worked on now. Update in **every PR**: move finished work to Done with its PR
number, re-rank what changes rank, and delete anything that has been "next" for three weeks.
That last instruction matters more than the others; a board nobody prunes stops being read.

Last updated: 2026-09-19.

---

## Now

| # | Task | State | Where |
| --- | --- | --- | --- |
| 1 | Complete the Repo Standard document set: `docs/rules.md`, `prd.md`, `design.md`, `tasks.md`, `memory.md`, the PR template filename, and `.metagpt/` tracked | in review | PR #199 |
| 2 | Evolution loop task 1: the `skill-evolution` skill tree and its count coupling | in review | PR #200 |
| 3 | Evolution loop tasks 2 to 15 | next | `.metagpt/plan.md` |

Task 3's first four tasks are the working set: `ledger.py`, `lane.py`, `observe.py` and
`validate.py`, in that order, because `propose.py` needs the lane adapter and the guard.
Tasks 10 and 11, persona generation and the first reviewed batch, are independent of the loop
and can run in parallel.

## Next

| # | Task | Why now | Blocked on |
| --- | --- | --- | --- |
| 4 | Fix `.githooks/pre-push`: a false positive in the secret scan, then point it at this repo's real fast gates | the gate that landed in #198 runs the secret scan and `npm test`, which is `node bin/coco.js --help`. It runs no check that catches a regression here. Worse, its secret scan regex is `(api[_-]?key|secret|token).*=.*(sk-\|ghp_\|xox[baprs]-)`, and a single-line file mentioning a token count and the department `risk-compliance` matches on the `sk-` inside "risk". Reproduced on 2026-09-19 while wiring the hook: the gate blocked a push over its own repository's content. Fixed then by not committing the generated ripwire map, but the regex is still fragile, and the playbook's rule 10 is about exactly this: a tool that cries wolf gets ignored and then protects nothing. The real gates total about 4.2 s, measured, so they fit a pre-push budget | nothing |
| 5 | Persona scale toward 1000 | the owner asked for it on 2026-09-18; the roster is at 495 | tasks 10 and 11 of the loop plan |

## Deferred on purpose

Each of these has a stated reason, so a future reader can tell deliberate deferral from
neglect.

| # | Task | Reason | Since |
| --- | --- | --- | --- |
| 6 | Register row 27: before and after comparator for `reanalyse` | deferred by ruling R7 during the retrofit; it is a convenience for one pipeline stage, not a gate | 2026-09-18 |
| 7 | Register row 9b: pytest fixture aware runner and coverage attribution | three of four ceilings in that row were closed; the remaining two need a test runner that understands pytest fixtures, which is a project in itself. Parametrised tests currently report `unrunnable`, which is honest rather than wrong | 2026-09-18 |
| 8 | Two `arch_gate` fixture cases SKIP on CI | they assert tool discovery from an installed copy of the skill, which does not exist on a fresh CI checkout. They pass locally and skip there | 2026-09-18, found while fixing CI |
| 9 | `~/.claude/skills/team-gate` symlink | every `/team:*` command file invokes `~/.claude/skills/team-gate/scripts/<script>`, so the installed path resolves only once the symlink exists. The handoff says to ask before creating it on the owner's machine | 2026-09-18 |

## Open PRs, not mine to land alone

Reviewed on 2026-09-19, kept here because a queue nobody tracks hides the work that matters.

| PR | State | Title |
| --- | --- | --- |
| #183 | approved, green, behind by 2 | fix(adapters): install the 13 SI team front doors |
| #184 | conflicting | feat(skill-map): discovery map plus maker-mdap baseline |
| #185 | conflicting | docs: make "a bug you find is a bug you fix" a standing rule |
| #188 | review required, behind | docs(readme): local SI dogfood GIF |
| #189 | review required, behind | fix(team): use the placeholder the tooling actually expands |

## Done

| PR | Merged | What it delivered |
| --- | --- | --- |
| local | 2026-09-19 | `git config core.hooksPath .githooks` wired in the working clone, so the gate now runs on push. Local config, cannot be committed; every clone needs the one command |
| #198 | 2026-09-20 | Tier 1 Repo Standard: `AGENTS.md`, `.githooks/pre-push`, PR template content |
| #197 | 2026-09-19 | README hero and roster assets |
| #196 | 2026-09-18 | Team gate retrofit: 60 commits, 182 files under `skills/team-gate/`, 14 fixture suites. CI green on `main` at 14/14. Closed register rows 16 to 18, 5c, 5e, 5f, 9b (three of four), 12c, 12d, 23b |
| #195 | 2026-09-18 | npm package treated as published |
| #194 | 2026-09-18 | README leads with the published npm path |
