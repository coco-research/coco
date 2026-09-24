# ARCH: the self-evolution loop, persona scale, and the gate close-out

Stage `arch`, written 2026-09-18. Owner: Rijul Kalra. Status: awaiting approval.
Diagram: [`arch-diagram.html`](arch-diagram.html). PRD: [`prd.md`](prd.md).
Evidence base: [`INDEX.md`](INDEX.md), [`ripwire-for.txt`](ripwire-for.txt), the whole-repo
and in-flight surveys recorded in `STATE.md`, and the handoff bundle at
`skills/team-gate/handoff/` on branch `feat/team-gate-retrofit`.

---

## 0. Diagram

`arch-diagram.html`, self contained, inline SVG. One architecture view of the cycle: where
a model is allowed to write, and what stands between its output and `main`. The persona
generator is annotation, not a ninth node, because it enters the same validate-and-propose
gate rather than forking the pipeline.

## 1. Current state

coco's product is its instructions. 226 skills, 44 shipped commands, 35 agents, 495
personas across 13 departments, all markdown, all hand written. Two facts define the
starting point:

- **Nothing proposes changes.** The repository can prove a change (the team-gate scripts,
  the count gates, the frontmatter lint, 14 fixture suites, CI on Linux) but every change
  begins with a person deciding to make it. Trigger wording drifts from how people
  actually invoke a skill, and nothing measures the drift.
- **Counts are load bearing.** `docs/asset-counts.json` is generated and `tests/check-asset-counts.sh`
  fails on any published count that disagrees with it, so adding one skill moves numbers
  in about a dozen hand written files. That is why "add personas" is a pipeline problem
  here, not a writing problem.

## 2. Change

**A skill that runs a cycle, not a service.** New tree `skills/skill-evolution/`, in the
repository's own shape: `SKILL.md` for the instruction surface, `scripts/` for the
measurement, `references/` for schemas, `state/` for the committed ledger.

The cycle, five deterministic steps and one model step:

1. **observe** collects a signal extract pinned to a commit: the local task-observer
   observation log, the git window over the skill tree, and the gate receipts from
   team-gate runs. No model call. Writes `signals/<cycle>.json`.
2. **propose** asks a model lane for candidate edits, one candidate per skill, each
   carrying citations that resolve at the pinned commit. Writes `proposals/<id>.json` plus
   `proposals/<id>.patch`. This is the only place a model writes anything.
3. **validate** is the guard. It refuses out of scope edits (personas, commands, count
   files, workflows, the loop's own scripts), refuses a citation that does not resolve,
   refuses a diff over the size cap or a cycle over the proposal cap, refuses a diff that
   a ledger row already rejected within two cycles, and refuses a count move whose coupled
   files did not move, by running the repository's own checkers.
4. **open** puts the accepted proposals on one branch as separate commits and opens one
   pull request for the cycle. Never `main`, never a merge.
5. **record** appends to the committed ledger and renders `CYCLE.md`, the human artifact,
   alongside a gate style result with the three valued exit the rest of the repo uses.

**Cadence and secrets.** `.github/workflows/evolution-cycle.yml` runs monthly in
`--dry-run`: no model credentials in CI, and it validates that the pipeline still runs and
reports what a real cycle would have done. The real cycle runs where credentials exist,
which today is the owner's machine, through one documented command. A self hosted runner
is a later decision, not part of this architecture.

**Persona scale.** `systems/superintelligence/scripts/build_personas.py` generates personas
from a spec file (department, archetype, domain, count) following the existing frontmatter
contract and the DISCLAIMER convention, in archetype sized batches so a human can review a
sample rather than a blob. Its validation is the existing machinery: `validate_roles.py`,
the frontmatter lint, `check-persona-counts.py`, and `check-asset-counts.sh` after
regeneration.

**Invariants the loop inherits rather than invents.**

- Three valued exit everywhere: 0 pass, 1 blocked by a guard, 2 unrunnable or unmeasured.
- Human facing artifacts in the repository; run state under the team-gate run directory,
  never committed.
- The loop's own outputs are gated by the same CI as everything else, so a proposal branch
  that arrives red is a defect in the loop, not a matter of taste.
- No auto merge, at any confidence, per the owner's answer to Q4.

## 3. Files and symbols to touch

New, the loop:

- `skills/skill-evolution/SKILL.md`
- `skills/skill-evolution/scripts/observe.py`, `propose.py`, `validate.py`, `ledger.py`,
  `lane.py`, `render_cycle.py`, `evolve.py` (entry point), `run_fixtures.sh`
- `skills/skill-evolution/references/proposal-schema.json`, `lanes.json`, `signal-sources.md`
- `skills/skill-evolution/state/ledger.jsonl` (empty at first commit)

Symbols: `observe.collect(window, repo)`, `propose.propose(signals, lane, budget)`,
`validate.check(proposal, repo, pinned_commit)`, `ledger.append(record)` and
`ledger.rejected_recent(diff_sha256)`, `lane.call(lane_id, prompt, budget)`,
`render_cycle.render(cycle)`, `evolve.main(argv)`.

New, the persona path:

- `systems/superintelligence/scripts/build_personas.py`, `references/persona-spec.example.json`

Symbols: `build_personas.generate(spec, out_dir)`, `build_personas.coupled_files(counts)`.

New, cadence:

- `workflows/evolution-cycle.md`
- `.github/workflows/evolution-cycle.yml`

Touched, all generated or count coupled, through the existing scripts rather than by hand:

- generated: `docs/asset-counts.json`, `skills/INDEX.md`, `systems/INDEX.md`,
  `docs/by-domain/*.md`, `adapters/INDEX.md`
- hand written claims that must move with a count: `README.md`, `package.json`,
  `.claude-plugin.json`, `index.html`, `coco/index.html`, `docs/install.md`,
  `docs/INDEX.md`, `agents/README.md`, `assets/og-image.svg`,
  `systems/superintelligence/HOW-IT-WORKS.html`
- CI: the standalone suites step in `.github/workflows/ci.yml` gains the loop's fixture
  runner, the same join the team-gate suite already has

## 4. Data, APIs, interfaces

No network service, no database. Three file formats and one adapter.

`signals/<cycle>.json`

```json
{"cycle": "2026-10", "window_days": 30, "pinned_commit": "<sha>",
 "observations": [{"skill": "brainstorming", "signal": "zero_invocations_with_recent_edits",
                   "count": 4, "examples": [{"path": "skills/brainstorming/SKILL.md", "line": 12}]}],
 "lanes": {"used": [], "cost": {}}}
```

`proposals/<id>.json`

```json
{"id": "<cycle>-<n>", "skill": "brainstorming", "class": "description|references|examples|prose",
 "evidence": [{"path": "skills/brainstorming/SKILL.md", "line": 12}],
 "files": ["skills/brainstorming/SKILL.md"], "diff_sha256": "<sha>",
 "rationale": "<prose>", "cost": {"lane": "grok-4.6", "calls": 1, "tokens": 8123}}
```

`state/ledger.jsonl`, one record per event, append only:

```json
{"cycle": "2026-10", "proposal": "<cycle>-<n>", "action": "proposed|merged|rejected",
 "reason": "<why>", "by": "loop|owner", "head_sha": "<sha>", "at": "<iso8601>"}
```

`references/lanes.json` names the allowed lanes and their budgets. The adapter in
`lane.py` shells out to the configured endpoint or CLI; it carries no vendor SDK, applies
the per cycle budget before spending, and records the lane and cost on every call. The
free overflow lane is permitted for batch generation only, because it rate limits, and the
expensive review lane is never called without the owner's explicit word, which the adapter
enforces by refusing rather than by documenting.

## 5. Risks

1. **A loop that edits the repository that measures it.** Mitigated by proposals only,
   by `validate` refusing everything outside the skill tree, by the owner's merge, and by
   the loop's own artifacts passing the same CI as any other change. The residual risk is
   a proposal that is technically valid and editorially wrong, which is what the review
   gate is for.
2. **Signal poverty.** Usage logs exist mainly on one machine. A thin signal produces
   cosmetic churn. Mitigated by a minimum evidence threshold, by caps, and by treating an
   empty cycle as a valid result (exit 0, nothing to propose) rather than a failure.
3. **Cost drift.** A per cycle budget enforced before spending and recorded per proposal.
   Exceeding it is exit 1 with a named reason, not a silent overspend.
4. **Persona slop at a thousand entries.** Mitigated by archetype sized batches, the
   existing validators, the disclaimer convention, and the owner reviewing a sample per
   batch rather than the whole set.
5. **Count coupling.** The single most likely way a proposal arrives red. Mitigated by
   running the repository's own checkers inside `validate`, so a proposal that moves a
   count without the coupled updates is refused before a branch exists.
6. **Platform difference.** This session's two CI failures both passed on macOS and failed
   on Linux. Every new fixture must therefore be hermetic: a stub lane, temporary copies,
   no `$HOME` dependency, and no installed copy of anything.
7. **Secrets in CI.** Solved by making the scheduled job dry run only. The cost is that the
   real cycle is not unattended, which is honest about where credentials live.

## 6. Test surface

- Per script `--self-test` with a stub lane, so no test needs the network or a model. Each
  case invokes the CLI through `subprocess.run([sys.executable, __file__, ...])`, asserts
  the return code and a stderr substring, and runs on a temporary copy.
- `skills/skill-evolution/scripts/run_fixtures.sh` joins the CI standalone suites step
  beside `skills/team-gate/scripts/run_fixtures.sh`.
- Contract cases, each with a fixture: a citation that does not resolve is refused (exit
  2); an out of scope edit (a persona file, a command file, a count file) is refused (exit
  1); a cycle over the proposal cap states the remainder; a diff rejected in the previous
  cycle is not proposed again; a count move without the coupled files fails; an empty
  signal window exits 0 with nothing to propose.
- Determinism: the same window and pinned commit twice produce byte identical
  `signals/` and `proposals/` (`diff -r` empty).
- One recorded dry run cycle against coco itself, as the honest end to end.
- `build_personas.py` on a five persona fixture: files pass the frontmatter lint and
  `check-persona-counts.py`, and a fixture that moves a count without the coupled files
  fails.
- Acceptance, from the PRD: one real cycle produces a real pull request whose evidence the
  owner can check by hand, and the ledger shows the proposal and its fate.
