# Pilot run 2, 2026-09-18: /team:fix on a planted bug, scripts at e53b4ac

Runner: Sonnet (run-pilot-2-s). Scripts taken from a detached worktree at e53b4ac so uncommitted edits were excluded. Raw transcript beside this file as pilot-run-2-raw-transcript.jsonl. Left in place for the verifier:

- Scripts worktree: scratchpad/team-retrofit/pilot2-scripts.EHnALX (detached at e53b4ac; the brain removes it after verification)
- Pilot repository: scratchpad/team-retrofit/pilot2-repo.dAe5q3
- State root: scratchpad/team-retrofit/pilot2-state-root.1c0Y6g, run id 20260918-090426-363
- ripwire: the real binary at ~/.local/bin/ripwire, 0.6.1
- Commits pinned to 2026-01-01T00:00:00Z; baseline head 01cf4a19, test commit 51d2c801, fix commit 12efafe1

## Result: every step PASS, no FINDING

| Step | Exit | Gate file | Outcome |
|---|---|---|---|
| install.py --project and --check | 0 / 0 | .claude/settings.json with four hooks | PASS |
| gate_state.py start | 0 | run.json | PASS |
| 1 map (real ripwire) | 0 | gates/handoff-1-map.json, 8 files, 1 symbol | PASS |
| 2 discover | 0 | gates/7-discover.json, [["bash", "scripts/test.sh"]] | PASS |
| 3 parity | 0 | gates/7.json | PASS |
| 4 baseline run | 0 | gates/8.json, shape unittest, passed 1, head 01cf4a19 | PASS |
| 5 red test committed alone | commit | 51d2c801 | PASS |
| 6 fix commit, discover, run (passed 2), prove --base 01cf4a19, recheck | 0 / 0 / 0 / 0 | gates/9.json valid-red-assertion with attribution_frame in tests/test_mean.py and last_frame in unittest/case.py; gates/9-recheck.json rechecked 1 | PASS |
| 7 matrix with a tests list | 0 | gates/11-matrix.json, R1 MET, route tests | PASS |
| 8 evidence, render check | 0 / 0 | EVIDENCE.json head equals HEAD 12efafe1, seven entries | PASS |
| 9 claims: unbacked sentence present, then removed | 1 / 0 | gates/12.json: two uncited findings then none; "2 passed" resolved through entry.detail.parsed | PASS |
| 10 fix_gate.py check | 0 | gates/fix.json verdict PASS, seven stages | PASS |
| skip probe | 0 / 0 | receipt seq 18 certified would-deny, guard always-deny; Post appended nothing; EVIDENCE.md untouched | PASS |

verify-chain: chain intact. status: completed, last_gate fix-gate, superseded_receipts 3. Total gate-script wall time about 3.7 seconds.

## What run 2 proved against run 1

Finding 2 (prove_red last-frame attribution) closed by task 30: the same test now reads valid-red-assertion. Finding 4 (matrix mapping) closed by task 32: R1 MET through the tests route. Finding 5 (claim_evidence schema) closed by task 31: "2 passed [E4]" resolved through entry.detail.parsed. Finding 3 (stale discover) did not fire because discover ran after every commit as the corrected brief says. The hooks were driven with constructed payloads as before; the harness-fired path belongs to tasks 16 to 18.

## Not yet shown by a pilot

The stub-red mode for tests-only changes (task 34, in verification), fix_gate's map row (task 29, in verification), and the ship pipeline end to end, which needs the six prose files committed and an isolated session for the hooks.
