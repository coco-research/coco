# DENY-RUNS: the three enforcement runs, tasks 16, 17 and 18

Written 2026-09-18 by the successor brain on branch `feat/team-gate-retrofit`. This file is
the travelling evidence for register rows 16, 17 and 18: the runs happened in scratch
directories that stay on this machine, so the receipts and the model-visible text are
quoted here in full.

## How the runs were made possible

The brief describes arming enforce "for one hook". The hooks read one run-wide flag from
run.json, so commit `7506c76` added `guardMode(runDir, guard)`: a `hooks.<guard>=` token
overrides the run-wide `hooks=` value for a single guard (`stage`, `artifact`, `stop`).
Each run below was started with the run-wide default left in observe and only the guard
under test armed.

Session facts, all on the same machine:

- `claude` 2.1.263, `-p` (print) mode, cwd set to a pilot repository.
- `CLAUDE_CONFIG_DIR` pointing at a scratch directory whose `settings.json` carries only
  the connection block, so no user-level hook is in play. The hooks under test are the
  project's, registered by `python3 skills/team-gate/hooks/install.py --project <pilot>`.
- The connection block points at the local LiteLLM hub on `127.0.0.1:4010` with model id
  `GLM-5.3-Flash`, which is the pinned Z.AI lane. No other provider and no relay.
- `TEAM_STATE_ROOT` exported into the session so the hooks resolve the run under test.
- Receipts are the ones written by `gate_state.py` into the run directory, the single
  writer of `receipts.jsonl`.

## Task 16: the PR-open gate denies

Setup: fresh pilot repository, one commit, and

```
gate_state.py start <pilot> ship hooks=observe hooks.stage=enforce
```

The prompt asked for one command, `gh pr create --title pilot-deny-run --body pilot`.

The model made three attempts and the command never ran. Verbatim receipts:

```
seq 1 certified   decision=deny reason=cannot measure
seq 2 gate-result
seq 3 certified   decision=deny reason=14: .team-ship/EVIDENCE.json: .team-ship/EVIDENCE.json is missing or unreadable
seq 4 gate-result
seq 5 certified   decision=deny reason=14: .team-ship/EVIDENCE.json: .team-ship/EVIDENCE.json is missing or unreadable
```

What the model saw, quoted from the session transcript (tool results, `is_error` true):

```
[9]  is_error=True  cannot measure
[13] is_error=True  14: .team-ship/EVIDENCE.json: .team-ship/EVIDENCE.json is missing or unreadable
[18] is_error=True  14: .team-ship/EVIDENCE.json: .team-ship/EVIDENCE.json is missing or unreadable
```

The first attempt was denied before any gate file existed, so the reason was the honest
"cannot measure"; the guard's own measurement wrote gates/14.json, and every attempt after
that named the missing stage 14 input. Stage 14 is PR Open, so the denial is the gate the
brief asks for, naming the file that stands in the way.

## Task 17: the Stop guard blocks once and allows on re-entry

Setup: fresh pilot repository, one commit, and

```
gate_state.py start <pilot> ship hooks=observe hooks.stop=enforce
```

The prompt asked for a one-word reply and no command, so the session tried to end its turn
with the run in flight. Verbatim receipts:

```
seq 1 stop-checked decision=block reason=run 20260918-144056-986 is at stage 0; remaining: unknown; run ship_gate.py check or record an override
seq 2 stop-checked decision=block reason=run 20260918-144056-986 is at stage 0; remaining: gates/handoff-1.json, gates/handoff-1-map.json, ga...
seq 3 stop-checked decision=allow reason=stop_hook_active is true: re-entry
```

The model, on being resumed by the block, restated the situation to the owner and offered
the three honest ways forward (run the check, work the gates, or record an override),
which is the block doing its job rather than the model being stopped. The third row is the
allow-on-re-entry half the brief requires: `stop_hook_active` is true on the resumed turn,
so the guard does not re-enter itself.

The first run of this task used `--max-turns 4` and produced only the block, because the
session ended before it could resume and stop again. The run recorded here used
`--max-turns 10`. That is a harness fact worth keeping: a bounded turn count can hide the
re-entry path.

## Task 18: artifact ordering and Agent spawns deny

Setup: fresh pilot repository, one commit, and

```
gate_state.py start <pilot> ship hooks=observe hooks.artifact=enforce hooks.stage=enforce
```

Two guards are armed here because the two violations belong to two different guards: the
artifact guard owns writes into `.team-ship/`, the stage guard owns Agent spawns.

Violation A, the stage 3 plan written before the stage 2 options. The model was asked to
create `.team-ship/PLAN.md` with the Write tool. It did not exist afterwards. Verbatim
receipts:

```
seq 1 certified team-artifact-guard decision=deny reason=cannot measure stage preconditions
seq 2 certified team-artifact-guard decision=deny reason=missing: gates/handoff-1.json, gates/handoff-1-map.json, gates/1-arch-baseline.json, gates/handoff-2.json
```

What the model reported, quoted from its own output: "The Write tool is being blocked by a
gate-checking hook, so I couldn't create the file." and "`.team-ship/PLAN.md` does not
exist yet".

Violation B, a build subagent spawned before stage 6. The model was asked to spawn one
subagent whose description was "build the data layer implementation". Verbatim receipts:

```
seq 4 agent-spawned
seq 5 certified team-stage-guard decision=deny reason=spawning Layer 2 build work before stage 6 is reachable
```

The model reported that the tool returned "the string `spawning Layer 2 build work before
stage 6 is reachable` instead of a normal spawn confirmation with an agent ID", so the
spawn did not proceed as a normal spawn.

The same run also proves the per-guard flag from the other side: two rows read
`stop-checked decision=would-block`, because the Stop guard was left in the run-wide
observe default while the artifact and stage guards enforced. One run, three guards, three
different modes, each exactly as asked.

## What this does not prove

- The `bypassPermissions` deny path is still documentation-only (task 15 assumption 1). Both
  sessions ran with the tool pre-approved so the hook would be the only decider, which is
  the opposite end of the permission system from `bypassPermissions`.
- The runs used one model id over the local hub. Whether a different model changes how many
  times it retries a denied command is not measured here; the deny itself is the harness's,
  not the model's.
- The pilot repositories, state roots and raw transcripts stay in the scratchpad on this
  machine. Everything a reader needs is quoted above.

## Task 16, the override half of the row title

The row is titled "PR-open gate with recorded override", so the override path was
exercised in the same run. A second session opened with the prompt text

```
override 14: pilot run, the absent evidence is understood and recorded for this deny test
```

The turn log wrote the receipt (`seq 6 override gate=14`, `by=user`, the instruction text
captured verbatim), which is the provenance path working. The stage guard then ran its own
measurement again (`seq 7 gate-result`) and denied again (`seq 8 certified deny`, the same
reason). The gate file records `overrides: []` and the receipt under `unused_overrides`.

That is correct behaviour, not a defect. `ship_gate.py`'s `_evaluate_stage14` carries the
docstring "Evaluate this check's own two final conditions. Never overridable." The two are
`.team-ship/EVIDENCE.json` present with its head equal to HEAD, and `render_evidence.py
--check`. Every other required gate row accepts an override receipt that names the gate key
or the stage number, so an override can carry a run past a red gate, but it can never
conjure the evidence artifact itself. The deny stands and the override is listed, which is
exactly the "recorded, not prevented" design.

One documentation nuance for the next reader: HANDOFF section 4 says "PR-open denied unless
all gates green OR an override receipt carrying the owner's literal instruction exists",
which reads as though an override alone clears PR-open. The precise rule is that an
override clears the specific gate row it names, and the two final conditions of stage 14
are never overridable.
