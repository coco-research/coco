# Pilot run 1, 2026-09-18: /team:fix on a planted bug

Runner: Sonnet (run-pilot-s). Raw transcript preserved beside this file as pilot-run-1-raw-transcript.jsonl (2.1 MB). Repository and state root left in place for the verifier:

- Pilot repository: scratchpad/team-retrofit/pilot-repo.w33NNm
- State root: scratchpad/team-retrofit/state-root.P3yjKo, run id 20260918-080233-192
- ripwire: the real binary at ~/.local/bin/ripwire, 0.6.1
- Scripts: the worktree at 9d89c36 plus the uncommitted 24b edits to ship_gate (not invoked by the fix pipeline)

## Step table

| Step | Command | Exit | Gate file | Outcome |
|---|---|---|---|---|
| 1 map | brownfield_map.py --for "fix mean dividing by one too many" | 0 | gates/handoff-1-map.json (8 files, 1 symbol, 0.38 s) | PASS |
| 2 discover | run_gate.py --repo-root . discover | 0 | gates/7-discover.json, commands [["bash", "scripts/test.sh"]] from ci.yml:8 | PASS |
| 3 parity | run_gate.py --repo-root . parity | 0 | gates/7.json, "parity OK for 0 tool(s)" | PASS |
| 4 baseline run | run_gate.py --repo-root . run | 0 | gates/8.json, shape unittest, passed 1 | PASS |
| 5 red test | enumerate 0; prove 1 in the brief's original order (before the fix) | 0 / 1 | gates/9.json invalid-red, green fails | FINDING 1 (brief ordering error, corrected mid-run) |
| 6 fix and proof | run exit 2 stale discover; discover 0; run 0 (passed 2); prove --base 418fa22 exit 1; recheck 0 with rechecked 0 | mixed | gates/8.json, gates/9.json, gates/9-recheck.json | FINDINGS 2 and 3 |
| 7 matrix | claim_evidence.py matrix .team-ship/PLAN.md | 2 | gates/11-matrix.json, R1 UNVERIFIED, gates [] | FINDING 4 (anticipated) |
| 8 evidence | run_gate.py --repo-root . evidence; render_evidence.py --check | 0 / 0 | EVIDENCE.json head f73cd12 equals HEAD; 8 entries | PASS |
| 9 claims | check with the unbacked sentence 1; check with it removed still 1 ("2 passed" unbacked); check with a non-quantitative cited sentence 0 | 1 / 1 / 0 | gates/12.json | FINDING 5 |
| 10 verdict | fix_gate.py check | 1 | gates/fix.json BLOCK: stage 3 gates/9.json BLOCK, stage 5 gates/11-matrix.json UNVERIFIED; every head equals HEAD | correct cascade of 2 and 4 |
| skip probe | team-artifact-guard.js Pre then Post with constructed payloads for a Write of .team-ship/EVIDENCE.md | 0 / 0 | receipt seq 24 certified would-deny, reason "evidence and gate files are written only by team-gate scripts"; Post appends nothing (guard always-deny); file untouched | PASS |

verify-chain: chain intact, exit 0. status: stage_cursor null, build_rounds 0, status completed, last_gate fix-gate, superseded_receipts 8 (six re-issued gate-result receipts and two re-issued artifact-written receipts). Every script invocation took 0 to 1 second.

## Findings, with the brain's classification and disposition

1. Brief ordering error (brain's). prove_red.py prove runs the new test green at HEAD and then reverts implementation paths in a throwaway worktree; run before the fix, there is nothing to revert and the test fails both times. Corrected mid-run and in PILOT-BRIEF.md; fix.md and test.md carry the corrected order.

2. prove_red classifier defect, real, blocking for unittest repositories. classify_red credits valid-red-assertion only when the traceback's last frame resolves under the worktree. unittest.TestCase.assertEqual raises from the standard library's unittest/case.py, so a unittest-style test can never earn the classification and is reported invalid-red even when green passed and the revert genuinely restored the bug (gates/9.json: green.outcome pass, revert.diffstat "M calc/__init__.py", red.class invalid-red, last_frame unittest/case.py:918). Disposition: task 30, walk the traceback from the last frame backwards past frames outside the worktree (stdlib, site-packages) to the first frame inside it; a test-path frame gives valid-red-assertion, an implementation-path frame gives invalid-red; fixture with a unittest test.

3. Stale discover guard, by design, but the prose must state it. run_gate.py run exits 2 when gates/7-discover.json was recorded at a different HEAD, so discover runs again after every commit. Disposition: ruling R12 in TASK20-BRIEF.md; fix.md and test.md say "discover, then run" after each commit.

4. Matrix cannot map a requirement to any gate. gates/8.json's summary is an aggregate string and no gate file carries a requirements list, so every hand-written requirement is UNVERIFIED. Disposition: task 32, requirements name their tests (a `tests:` list of nodeids per requirement in PLAN.md), and matrix maps requirement to tests to gates/9.json classes and gates/8.json's latest result.

5. claim_evidence check reads numeric fields at the entry top level while run_gate evidence nests them under detail.parsed, so "2 passed [E4]" is reported unbacked against real evidence even though the number is correct; only claim_evidence's own hand-built flat fixtures ever passed. Disposition: task 31, field resolution through a fixed search order (entry, detail, detail.parsed, detail.commands[].summary aggregated), and fixtures generated from a real run_gate evidence output instead of a hand-built schema. Lesson: a fixture that models another script's output must be produced by that script.

6. fix_gate's BLOCK is the correct sum of findings 2 and 4; fix_gate itself behaved.

7. Hooks do not fire on a subagent's tool calls in this harness (settings are resolved from the session's start directory), as PILOT-BRIEF.md predicted; the skip probe exercised the hook by direct invocation. Tasks 16 to 18 run in an isolated CLAUDE_CONFIG_DIR session started inside the pilot repository.

Also observed: gate_state.py verify-chain and status take no --repo-root and resolve from the process cwd, unlike every other script (follow-up 5f). recheck reported rechecked 0 because no test held a PASS verdict; once finding 2 is fixed, recheck becomes meaningful on this repository.

## What the pilot proved

The chain, the receipts, the map, discovery of a bash runner, parity, the unittest run measurement (task 28), the evidence render and its byte check, the certified would-deny receipt with a silent Post, and the aggregator's cascade all behaved as specified on a real repository with a real binary. The two defects it found (2 and 5) are exactly the class the owner asked the gates to remove: a script whose fixtures were written to its own assumptions rather than to another script's real output.
