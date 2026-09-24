# Wave 3 briefs: the aggregators, the fixture runner, and the CI join

Wave 3 turns the individual gate scripts into a single verdict that a hook can ask for. It has four tasks. Task 5d is a small change to the committed library and must land first because the aggregators depend on its semantics. Tasks 12a and 12b are the two aggregators. Task 13 is the fixture runner that joins CI, together with the one change arch_gate needs to run on a CI machine.

Every rule from WAVE2-REBUILD-ADDENDUM.md "Rules that every rebuilt script must satisfy" applies to every script here, including the smoke check, the temporary-copy self-test, the fixture generator conventions, and the ban on em dashes and section signs. The opening line of every builder message is "You never run git commit, git add, or git push; the brain commits."

## Task 5d: latest receipt wins for a re-written gate file

Owner: a Haiku builder, because the change is mechanical and fully specified. Verifier: a scoped Sonnet round.

Problem. During a build loop, stage 8 legitimately runs more than once: the first run fails, the builder fixes the code, the second run passes. Each run rewrites gates/8.json and appends a new gate-result receipt. verify_chain currently checks every gate-result receipt against the current file, so the first receipt is permanently mismatched and the chain reads broken for the rest of the run. The same holds for artifact-written receipts when EVIDENCE.md is re-rendered.

Ruling. Receipts are an append-only log and a file reflects its latest write. For each distinct gate_file among gate-result receipts, and for each distinct path among artifact-written receipts, only the receipt with the highest seq is compared against the file on disk. Earlier receipts for the same file are recorded as superseded; their hashes remain part of the chain and are still validated as chain links. A superseded receipt is never compared against the file.

Changes to gate_state.py.
1. In verify_chain, build `latest_gate: dict[str, record]` keyed by detail.gate_file and `latest_artifact: dict[str, record]` keyed by detail.path, keeping the record with the highest seq. Run the existence, regular-file, symlink, containment and sha256 checks only over the values of those two maps. Path validation (`_contained_path`) still runs for every receipt, superseded or not, so a malformed path anywhere in the log is still broken.
2. derive_status gains `superseded_receipts: <count>` in its output.
3. receipt-schema.md, under two-way verification: one paragraph stating the latest-wins rule and that a gate file must be rewritten atomically (write to a temporary name in gates/ and os.replace) so a reader never sees a half-written file; the existing writers already do this or must be checked by their verifiers.

Fixtures, each with a fixed-date git repository where needed and generated deterministically with --out: gate-rereceipted-current (two gate-result receipts for gates/8.json, the file matches the later receipt; verify-chain exit 0); gate-rereceipted-stale (two receipts, the file matches the earlier receipt; exit 1, stderr names the later receipt's seq and "sha256 mismatch"); artifact-rereceipted-current (same shape for an artifact-written path; exit 0). Self-test grows by three lines to 32 OK.

Report exactly as the round-11 brief for gate_state asked: git status before and after, py_compile, the full self-test, the three new fixtures through the CLI, the in-tree diff against a fresh generation before and after the self-test, the em dash grep, "Committed: NO".

## Task 12a: ship_gate.py, the Stage 14 verdict and the stage-order oracle

Owner: Sonnet builder. Verifier: Sonnet.

Purpose. ship_gate.py answers two questions with a three-valued exit and one JSON line. "May this run open a pull request?" is `ship_gate.py check`, which is Stage 14's gate and writes gates/14.json. "May stage n be opened now?" is `ship_gate.py stage <n>`, a pure query the hooks call before allowing a stage artifact to be written; it writes nothing and prints one JSON object.

Inputs. The run directory from gate_state.find_run (absence is exit 2). HEAD from git rev-parse HEAD of the repository root recorded in run.json (a mismatch between run.json repo_root's HEAD and the cwd repository's HEAD is exit 2 naming both). ship-manifest.json from the references directory for the fourteen stage numbers and the artifact names. gate_state.verify_chain and gate_state.derive_status.

Required gates by stage, using the canonical file names the wave-2 scripts write. Stages 1 to 6: gates/handoff-<n>.json from check_artifacts, each exit 0, plus an `approval` receipt before stage 6 may open. Stage 7: gates/7-discover.json and gates/7.json. Stage 8: gates/8.json. Stage 9: gates/9.json. Stage 10: gates/10.json, where status NOT_APPLICABLE with exit 2 (no pytest command among the discovered commands) blocks like any exit 2 unless an override names the coverage gate. Stage 11: gates/8-verifier.json, gates/11.json, gates/11-matrix.json and gates/9-recheck.json. Stage 12: gates/12.json. Stage 13, CI mirror, has no file of its own: it is satisfied when gates/7.json is exit 0 and the ordered list of argv values under `commands` in gates/8.json equals the ordered list under `commands` in gates/7-discover.json, which proves the commands run locally were exactly the CI commands; ship_gate computes this and records it as the stage 13 row. (run_gate records several commands per run since the multi-command ruling; the top-level `argv` field is the first command and exists for compatibility only.) Stage 14 is ship_gate check itself.

Rules for check. Exit 0 PASS when verify_chain is ok, derive_status is not blocked, no receipt of kind block or gate-timeout exists, every required gate file exists with exit 0 and head equal to HEAD, the approval receipt exists, .team-ship/EVIDENCE.json records head equal to HEAD, and `render_evidence.py --check` (run as a subprocess with sys.executable from the same directory) exits 0. Exit 1 BLOCK otherwise, printing one line per failing item in the form `<stage>: <gate file or receipt>: <reason>`, where a gate that exited 2 is reported as UNVERIFIED and blocks like a failure. Exit 2 only when ship_gate itself cannot measure: run directory, run.json, manifest, HEAD or the chain file unreadable.

Overrides. An `override` receipt carries detail {gate, instruction, by}. A required gate that fails or is missing and is named by an override receipt is recorded as OVERRIDDEN with the instruction text verbatim and does not block; the verdict becomes PASS_WITH_OVERRIDE, still exit 0, and gates/14.json lists every override so render_pr_body can print them. A broken chain, a head mismatch, a block receipt or a gate-timeout receipt can never be overridden; those remain exit 1 whatever receipts exist.

Rules for stage <n>. The stages before n must each have their required gates present with exit 0 and head equal to HEAD (overrides count as satisfied and are listed), the chain must be ok, and no block receipt may exist. Output is one JSON object `{"stage": n, "allowed": bool, "missing": [...], "failing": [...], "overridden": [...], "reason": "..."}` and exit 0 when allowed, 1 when not, 2 when unmeasurable. Stage 1 is always allowed once the run exists.

Gate file for check: gates/14.json with argv, cwd, head, exit, summary, verdict (PASS, PASS_WITH_OVERRIDE, BLOCK, UNVERIFIED), and `stages` as a list of fourteen rows {stage, required, present, exit, head_ok, overridden, reason}. A gate-result receipt follows with gate "pr-gate", gate_file, gate_sha256, exit, summary. The file is written to a temporary name in gates/ and moved into place with os.replace.

Fixtures. Each fixture is a run directory plus a tiny fixed-date git repository, built with the gate_state API and deterministic content, generated with --out: all-green (check 0, stage 14 allowed); gate-missing-8 (1, names stage 8 and gates/8.json); gate-red-9 (1); gate-unverified-10 (1, reason UNVERIFIED); head-drift (1, names both SHAs); chain-broken (1); block-receipt (1); gate-timeout-receipt (1); no-approval (1); override-covers-9 (0, verdict PASS_WITH_OVERRIDE, the instruction text present in gates/14.json); override-cannot-cover-chain (1); ci-mirror-argv-differs (1, stage 13 row failing); stage-query-allowed (stage 8, 0); stage-query-blocked (stage 8 with gates/7.json missing, 1, missing lists gates/7.json); no-run (2). The self-test asserts exit, a stderr or stdout substring naming the failing stage, and for the two positive cases the verdict string in gates/14.json.

## Task 12b: fix_gate.py, the /team:fix verdict

Owner: Sonnet builder, the same agent as 12a if it has context left, otherwise a fresh one with 12a's file as the style reference. Verifier: Sonnet.

Purpose. /team:fix is the pilot pipeline and the smallest one that exercises red-green. fix_gate.py has the same shape as ship_gate.py and shares its helpers by importing them from ship_gate (both live in the same directory; `import ship_gate` after the sys.path insertion). Read commands/team/fix.md and REVIEW-OPUS.md section 1.16 for the fix pipeline's stages and gates, and record the stage list you derive in the module docstring; where fix.md and 1.16 disagree, 1.16 wins.

Required gates for check: gates/7-discover.json, gates/8.json, gates/9.json (tdd-redgreen with every runnable test valid-red and green), gates/9-recheck.json, gates/11-matrix.json and gates/12.json, plus the chain, head, block and gate-timeout rules from ship_gate. Overrides behave as in ship_gate. Writes gates/fix.json with the same row shape and a gate-result receipt with gate "fix-gate". `stage <n>` answers for the fix pipeline's own stage numbers.

Fixtures mirror 12a's at smaller scale: all-green (0), red-green-never-red (1, names gates/9.json), recheck-hash-changed (1), matrix-not-met (1), claim-uncited (1), override-covers-matrix (0), no-run (2), stage-query-allowed and stage-query-blocked.

## Task 13: run_fixtures.sh and the CI join, with arch_gate made portable

Owner: Haiku builder for the shell script and the CI edit, Sonnet builder or the brain for the arch_gate change, scoped Sonnet verify for arch_gate.

run_fixtures.sh at skills/team-gate/scripts/run_fixtures.sh. It runs `python3 <script> --self-test` for every script in a fixed list written in the file: gate_state.py, arch_gate.py, check_artifacts.py, run_gate.py, prove_red.py, verify_independent.py, claim_evidence.py, render_evidence.py, render_approval.py, render_pr_body.py, ship_gate.py, fix_gate.py. It exports TEAM_FIXED_TS=2026-01-01T00:00:00Z and a TEAM_STATE_ROOT under a mktemp directory that it removes on exit, prints one line per script in the form `<script>: exit <n>`, and exits 1 when any script exits non-zero, 0 otherwise. It must not write anywhere under the repository except the fixture _build directories the generators own. It uses `set -u` and `set -o pipefail` but not `set -e`, so every script runs and every line prints even after a failure.

arch_gate portability (task 6b). arch_gate.py resolves the arch-index scripts from the environment variable ARCH_INDEX_SCRIPTS when set, else from `<repository root>/skills/arch-index/scripts` when that directory exists, else from `~/.claude/skills/arch-index/scripts`, and records the chosen directory in ARCH-GATE.json under `tools_dir`. On this machine the third path is the canonical one and behaviour is unchanged; on the CI runner the second path is what exists. run_fixtures.sh does not set the variable, so the resolution order is what is tested. This is a change to a committed, verified script and gets its own scoped Sonnet round: the round-3 regression list for arch_gate plus the three resolution cases reproduced live.

CI join. In .github/workflows/ci.yml, the step "Run the standalone test suites" (around lines 190 to 200) gains one line after `bash skills/arch-index/scripts/run_fixtures.sh`: `bash skills/team-gate/scripts/run_fixtures.sh`, preceded by a comment in that step's voice, two lines at most, saying that the team-gate self-tests exercise every gate script against its static fixtures so a gate that stops failing its fixtures fails CI. Nothing else in the workflow changes. The CI machine has no pytest and no coverage plugin; the wave-2 fixtures were designed for that, and any self-test that needs a runner ships its own stub. The builder proves the join by running the same command locally from a clean checkout of the branch (git worktree add into a temporary directory, run, remove), quoting the per-script lines and the final exit.

## Order and hand-offs

1. Task 5d first, on gate_state.py, while the wave-2 Sonnet rebuilds run; nothing else edits gate_state.py.
2. Task 12a once tasks 7, 8, 9, 11 have PASSED and are committed, because the aggregator's fixtures encode their exact file names and field names.
3. Task 12b immediately after 12a.
4. Task 13 last, once every script has a passing self-test; its first run is the proof that the whole suite is green from a clean checkout.
