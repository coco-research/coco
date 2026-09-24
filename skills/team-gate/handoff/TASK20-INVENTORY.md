# Task 20 inventory: command prose against the gate scripts

Produced 2026-09-18 by an Explore agent reading the module docstrings of the twelve gate scripts and the six pipeline command files in full (develop, test, verify, reanalyse, fix, ship). Classification: COVERED means a script enforces the same thing and the prose can become one invocation line; PARTIAL means a script covers part and the remainder is named; JUDGEMENT means a model judgement no script should make; UNCOVERED means a mechanical step no script covers. Line numbers refer to the files at commit 8a5d105.

Headline fact: none of the six command files invokes any team-gate script. The only script invocations present are arch-index ones: reanalyse.md:35 and verify.md:61 (arch_drift.py), ship.md:66-68 and 177-178 (verify_arch_plan.py), ship.md:217-218 (validate_index.py, arch_drift.py).

## Counts

| File | Rows | COVERED | PARTIAL | JUDGEMENT | UNCOVERED |
|---|---|---|---|---|---|
| develop.md | 5 | 1 | 3 | 1 | 0 |
| test.md | 5 | 2 | 2 | 1 | 0 |
| verify.md | 19 | 9 | 6 | 3 | 1 |
| reanalyse.md | 8 | 1 | 5 | 2 | 0 |
| fix.md | 6 | 1 | 4 | 1 | 0 |
| ship.md | 57 | 25 | 21 | 3 | 8 |
| Total | 100 | 39 | 41 | 11 | 9 |

## develop.md

| Lines | Instruction | Script | Class |
|---|---|---|---|
| 46-49 | inline the component table into each L2 prompt when the index pin is CURRENT | arch_gate.py (pin vs HEAD) | PARTIAL: currency mechanical; inlining is model work |
| 51-56 | do not derive YOUR FILES from the index; scope-based splitting stays authoritative | none | JUDGEMENT |
| 58 | if the index is STALE, omit the block | arch_gate.py (pin != HEAD is exit 2) | PARTIAL: detection covered; the omit action is prose |
| 70 | coverage adequacy verified against EVIDENCE.md, captured exit 0, skips accounted for | run_gate.py run, evidence; render_evidence.py --check | COVERED |
| 74-75 | run the CI-equivalent gate with integration dependencies provisioned, capture command, exit, summary | run_gate.py discover, run, coverage, evidence | PARTIAL: provisioning, the after-L2-before-L3 ordering, REVIEW-PACKAGE.md skip surfacing unenforced; no develop-pipeline stage gate |

## test.md

| Lines | Instruction | Script | Class |
|---|---|---|---|
| 36 | prove RED before implementation for the right reason, then GREEN | prove_red.py prove, recheck | COVERED |
| 37 | CI-pinned tool versions, provision dependencies, any skip is UNVERIFIED | run_gate.py parity, run, evidence | PARTIAL: provisioning uncovered |
| 46-49 | tests test behaviour not implementation; names describe the scenario | none | JUDGEMENT |
| 50 | confirm via EVIDENCE.md that the suite ran; green claim without evidence is a finding | run_gate.py run; claim_evidence.py check | COVERED |
| 52-53 | report the parsed summary and measured coverage; any skip blocks a pass claim | run_gate.py run, coverage, evidence | PARTIAL: provisioning and "label the gap" uncovered |

## verify.md

| Lines | Instruction | Script | Class |
|---|---|---|---|
| 23 | compare the pin to HEAD, record CURRENT or STALE | arch_gate.py | COVERED |
| 29 | verify agents run the gate themselves | verify_independent.py setup; run_gate.py --role verifier run | COVERED |
| 30 | verify agents must not read the builder's summary or claims | verify_independent.py setup (.team-ship absent in the worktree) | PARTIAL: structural inside the worktree only |
| 31 | re-run from a CLEAN checkout (fresh clone) | verify_independent.py setup; run_gate.py --role verifier | PARTIAL: detached worktree not a clone; provisioning uncovered |
| 32 | paste raw output: command, exit, summary, coverage | run_gate.py run, coverage --role verifier; render_evidence.py | COVERED |
| 33-38 | MET, PARTIAL, NOT MET, UNVERIFIED, EXCEEDED | claim_evidence.py matrix | PARTIAL: matrix has three grades; PARTIAL and EXCEEDED stay judgement |
| 39 | any mismatch between builder claim and re-run output blocks with the discrepancy quoted | verify_independent.py compare | COVERED |
| 46-48 | does the cited evidence prove the requirement; are MET claims actually PARTIAL | none | JUDGEMENT |
| 49 | skipped-as-passed | run_gate.py run; claim_evidence.py check | COVERED |
| 50 | coverage without measurement | run_gate.py coverage; claim_evidence.py check | COVERED |
| 51 | not CI-reproducible (tool version, DSN unavailable in CI) | run_gate.py parity | PARTIAL: DSN availability uncovered |
| 52 | merge masquerade: merged or CI-green implied for a branch not reachable from main | none | UNCOVERED: branch reachability |
| 53-62 | run the deterministic scan, arch_drift.py | arch_gate.py | COVERED (invoked raw at 61) |
| 64-73 | REMOVE is CRITICAL, PRUNE is MAJOR, pin behind HEAD reports (e) UNVERIFIED | arch_gate.py | PARTIAL: the new-top-level-source-directory rule not implemented |
| 75-78 | structural drift only; a clean result licenses one sentence | none | JUDGEMENT |
| 79 | requirements missed entirely | claim_evidence.py matrix (no gate maps means UNVERIFIED) | COVERED |
| 83 | pass only if every requirement's evidence was reproduced by the Layer 2 verify agents | verify_independent.py compare; claim_evidence.py matrix | PARTIAL: no verify-pipeline aggregator; (d) unmeasured |
| 84 | requirements traceability matrix | claim_evidence.py matrix | COVERED |
| 85-86 | gap list by impact; recommendation | none | JUDGEMENT |

## reanalyse.md

| Lines | Instruction | Script | Class |
|---|---|---|---|
| 22-23 | the pin is the baseline for since: git diff --name-status pin..HEAD | arch_gate.py resolves pin and HEAD | PARTIAL: no script emits the delta |
| 30 | STILL GOOD, REGRESSION, NEW ISSUE, IMPROVEMENT, ARCHITECTURAL REGRESSION | none except the last | JUDGEMENT |
| 31-36 | ARCHITECTURAL REGRESSION requires the deterministic scan | arch_gate.py | COVERED (invoked raw at 35) |
| 38-43 | report when primary paths died (REMOVE or PRUNE); finding is SUSPECTED when the pin is behind | arch_gate.py | PARTIAL: unclaimed-top-level rule and SUSPECTED downgrade absent |
| 44 | confirm by re-running the gate, before and after summary in EVIDENCE.md | run_gate.py run, evidence | PARTIAL: no before/after comparator across two commits |
| 47 | check each requirement from REQUIREMENTS.md against current code | claim_evidence.py matrix | PARTIAL: matrix reads a plan file, not .planning/REQUIREMENTS.md |
| 54 | a test-status REGRESSION requires captured before/after evidence | run_gate.py run; render_evidence.py --check | PARTIAL: same missing comparator |
| 58-60 | regression list with severity; improvement opportunities | none | JUDGEMENT |

## fix.md

| Lines | Instruction | Script | Class |
|---|---|---|---|
| 33-38 | name the component each issue falls inside; not a constraint | arch_gate.py (CURRENT check only) | JUDGEMENT |
| 39-40 | if a fix deletes or relocates primary paths, note it | arch_gate.py (REMOVE, PRUNE) | PARTIAL: the note is prose |
| 45 | failing test first, RED for the right reason, then GREEN | prove_red.py prove, recheck; fix_gate.py stage 3 and 4 | COVERED |
| 46 | any skip is UNVERIFIED; capture command, exit, summary to EVIDENCE.md | run_gate.py discover, parity, run, evidence; claim_evidence.py check | PARTIAL: provisioning uncovered |
| 54-57 | coverage for the fixed code path confirmed against EVIDENCE.md, not test descriptions | prove_red.py recheck; run_gate.py coverage | PARTIAL: per-path coverage attribution does not exist; root cause is judgement |
| 59-60 | any failing test blocks, loop back (max 3 rounds), never merely noted | run_gate.py run; fix_gate.py check, stage N | PARTIAL: 3-round bound not enforced (derive_status only counts build_rounds) |

## ship.md

| Lines | Instruction | Script | Class |
|---|---|---|---|
| 22-24 | read .arch/pinned-commit, record it with HEAD, continue | arch_gate.py | PARTIAL: no stage-1 baseline record persisted |
| 26-31 | --no-arch gives DISABLED; no index gives NOT APPLICABLE | arch_gate.py | PARTIAL: only UNVERIFIED exists; missing index is exit 2; no --no-arch flag |
| 44 | writes ARCHITECTURE-OPTIONS.md and records the chosen option via /brain:update | check_artifacts.py stage-output 2 | PARTIAL: brain write unchecked |
| 50 | writes PLAN.md | check_artifacts.py stage-output 3 | COVERED |
| 51-61 | ARCH-PLAN.json component fields | check_artifacts.py stage-output 3 | PARTIAL: existence and size only, no schema |
| 63-73 | declaration check verify_arch_plan.py --declare; non-zero is BLOCK | none | UNCOVERED: no wrapper, no gate file |
| 79 | writes REVIEW-FINDINGS.md | check_artifacts.py stage-output 4 | COVERED |
| 86-97 | present to the user from the artifacts | render_approval.py | COVERED |
| 99-100 | if any of the four artifacts is missing, report and stop | check_artifacts.py approval-ready | COVERED |
| 102-105 | ask "Plan ready. Proceed with build?"; yes means full autonomy | ship_gate.py check (approval receipt); team-turn-log.js | PARTIAL: asking is prose |
| 114-116 | Stage 6 build runs /team develop, full autonomy | ship_gate.py stage 6 | COVERED (ordering) |
| 120-124 | each gate writes to EVIDENCE.md and can BLOCK; max 3 rounds | run_gate.py evidence; ship_gate.py check | PARTIAL: 3-round bound unenforced |
| 126-128 | if scope must be cut, the core is Stages 8, 11, 12 | none | JUDGEMENT |
| 131 | detect the CI configuration | run_gate.py discover | COVERED |
| 132 | pin ruff, mypy, pytest to CI versions | run_gate.py parity | COVERED |
| 133 | provision the integration dependencies CI needs, export the DSN | none | UNCOVERED |
| 134 | if a dependency cannot be provisioned, label its surface unit-only | claim_evidence.py check blocks the claim | PARTIAL: no script records the label |
| 137 | run the authoritative gate and the full suite with the DSN set | run_gate.py run | PARTIAL: DSN execution uncovered |
| 138 | capture raw output, exit codes, parsed summary | run_gate.py run (gates/8.json) | COVERED |
| 139 | any skip is UNVERIFIED, any failure BLOCK | run_gate.py run | COVERED |
| 142 | RED before implementation, GREEN after | prove_red.py enumerate, prove | COVERED |
| 143 | catches always-fail, always-pass, tests that encode the bug | prove_red.py prove | PARTIAL: encoding the bug stays review judgement |
| 146 | run coverage for real and capture the number | run_gate.py coverage | COVERED |
| 147 | never narrate an unmeasured coverage number | run_gate.py coverage; claim_evidence.py check | PARTIAL: unit-only labelling uncovered |
| 150 | fresh agents from a CLEAN checkout | verify_independent.py setup | COVERED |
| 151 | verify agents must not read the builder's summary | verify_independent.py setup; run_gate.py --role verifier | PARTIAL: structural only |
| 152 | captured output compared to the builder's claims; mismatch BLOCK | verify_independent.py compare | COVERED |
| 155 | every PR-body claim cross-checked against EVIDENCE.md; unbacked stripped | claim_evidence.py check; render_pr_body.py | COVERED |
| 156 | merge-honesty: never imply CI-green or merged for an unreachable branch | none | UNCOVERED |
| 159 | run the CI workflow's gate locally so local equals CI | ship_gate.py check (stage 13 argv equality) | COVERED |
| 162 | open the PR only if Stages 7 to 13 are GREEN with evidence | ship_gate.py check; team-stage-guard.js | COVERED |
| 163 | on failure report BLOCK with a prioritised gap list, do not open the PR | ship_gate.py check | PARTIAL: prioritisation is judgement |
| 164-166 | writes SHIP-REPORT.md on both outcomes | check_artifacts.py stage-output 14 | PARTIAL: validated, no renderer |
| 173-174 | skip when --no-arch; ARCH-PLAN.json absent is NOT APPLICABLE; neither is a pass | none | UNCOVERED |
| 176-179 | verify_arch_plan.py --verify | none | UNCOVERED: no wrapper |
| 181-186 | a declared new or modified component whose path does not exist after the build is BLOCK | none | UNCOVERED: no gate file, no ship_gate row |
| 195 | capture the output to ARCH-PLAN-EVIDENCE.md | none | UNCOVERED: absent from the manifest |
| 197-199 | it does not prove the code does what the component said | none | JUDGEMENT |
| 203-214 | resolve the outcome from the Stage 1 baseline in order, first match wins | arch_gate.py | PARTIAL: only UNVERIFIED and PASS/BLOCK exist; DISABLED and NOT APPLICABLE do not |
| 216-219 | validate_index.py and arch_drift.py | arch_gate.py | COVERED |
| 221-226 | zero surviving primary paths is BLOCK; a validator that cannot execute is BLOCK | arch_gate.py | PARTIAL and a conflict: unrunnable is exit 2 (UNVERIFIED), not 1; new-top-level rule unimplemented |
| 228-234 | do not read pin-behind-HEAD at gate time as staleness; do not downgrade to UNVERIFIED | none | UNCOVERED and contradicted: arch_gate.py's rule is "pinned commit != HEAD: UNVERIFIED" |
| 236-238 | capture to .arch/ARCH-EVIDENCE.md; because .arch is committed the gate also runs in the Stage 11 checkout | arch_gate.py --out | PARTIAL: writes .arch/ARCH-GATE.json, not ARCH-EVIDENCE.md; nothing runs arch_gate inside the Stage 11 worktree |
| 240-242 | a component reworked inside its own directory produces no drift | none | JUDGEMENT |
| 245 | BLOCK is real; loop back to Build (max 3 rounds) | ship_gate.py check, stage N; team-stop-guard.js | PARTIAL: 3-round bound |
| 246 | skipped is not passed; a skip forces UNVERIFIED and provision-or-block | run_gate.py run | PARTIAL: provision half uncovered |
| 247 | evidence or it did not happen; no matching evidence means the claim is deleted | claim_evidence.py check; render_pr_body.py | COVERED |
| 248 | Stage 11 agents never see the builder's summary | verify_independent.py setup, compare | COVERED |
| 251 | a PR only after Stages 7 to 13 are GREEN; do not describe the work as shipped | ship_gate.py check | COVERED |
| 253 | macOS notification only on a GREEN, PR-opened run | ship_gate.py check; pr-opened receipt | PARTIAL: firing is prose |
| 254 | report the final summary with the EVIDENCE.md location | run_gate.py evidence | COVERED |
| 258-263 | every artifact written to .team-ship by its stage before the next stage | check_artifacts.py stage-inputs, stage-output; ship_gate.py stage N | COVERED |
| 265-281 | the handoff artifact list | ship-manifest.json; check_artifacts.py | PARTIAL: ARCH-PLAN-EVIDENCE.md, .arch/index.json and .arch/ARCH-EVIDENCE.md are not in the manifest |
| 289 | if any stage fails, stop and report which and why | ship_gate.py check, stage N; team-stop-guard.js | COVERED |
| 290 | a hard-gate BLOCK loops back to Build (max 3 rounds), no PR | ship_gate.py check | PARTIAL: 3-round bound |
| 291 | --resume picks up from the last successful stage or the failed gate | gate_state.py status (stage_cursor, last_gate); ship_gate.py stage N | COVERED |
| 292 | all artifacts saved to .team-ship for resume | check_artifacts.py; run_gate.py evidence; team-artifact-guard.js | COVERED |

## Cross-file observations from the inventory

1. Three leftovers drive most PARTIAL rows: (a) integration-dependency provisioning and DSN export, named in every file and implemented nowhere; (b) the "max 3 rounds" bound, only counted (derive_status build_rounds, copied into gates/14.json) and never compared to 3; (c) no before/after comparator across two commits, which reanalyse 44 and 54 need.
2. Two prose-versus-script conflicts: ship.md:228-234 forbids downgrading to UNVERIFIED for a pin behind HEAD at gate time while arch_gate.py does exactly that; ship.md:226 says an unexecutable validator is BLOCK while arch_gate.py exits 2.
3. The built-as-declared gate (ship.md 168-199) is the largest uncovered block: verify_arch_plan.py --declare and --verify have no wrapper, no gate file, no ship_gate row, and ARCH-PLAN-EVIDENCE.md is not in the manifest.
4. Merge-honesty (ship.md:156, verify.md:52) is fully unimplemented: claim_evidence.py never runs git and the lexicon has no merged, shipped or CI-green phrase.
5. arch_gate.py has no --no-arch and no NOT APPLICABLE outcome, so the four-row outcome tables cannot collapse to one invocation without adding those outcomes.
