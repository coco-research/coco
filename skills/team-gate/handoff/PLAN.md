# PLAN — /team:* enforcement retrofit

Stage 3 artifact. Builds on RESEARCH-BRIEF.md (Stage 1) and the three-model review (Stage 2: Fable 5.1 on architecture, Opus 5 on mechanisms, Sonnet 5 adversarial). All four reviews are incorporated; every section is final.

## 0. Decision, in one sentence

Keep the model as orchestrator, make Python the only thing that measures, and make hooks the only thing that certifies. The model decides; only Python measures; only hooks certify.

## 1. Why not the two pure options

Pure hooks-around-Markdown fails because measurement stays in the model's hands. team:evidence.md already orders the orchestrator to capture output itself, and the real GRC run still reported Gate 10 NOT MEASURED and Gate 9 UNVERIFIED. Four hand-sequenced validators reproduce that failure at finer grain.

Pure Python orchestration fails because ship's Stages 1 to 6 each run a full four-layer /team action. A Python driver would replace team.md, help only one of the four consumers that need the retrofit, and have its own unenforced entry point.

The hybrid takes the region where measurement happens, Stages 7, 8, 9, 10 and 13, and collapses it into one Python runner. Everything else stays model-orchestrated behind hooks that gate every tool-bearing transition on hook-written receipts.

## 2. Substrate facts the design rests on (verified)

PreToolUse hooks fire in every permission mode including bypassPermissions and --dangerously-skip-permissions; a permissionDecision of deny blocks the call regardless. Hooks fire for subagent tool calls, which carry agent_id and agent_type. The current PreToolUse block contract is hookSpecificOutput.permissionDecision: "deny" with permissionDecisionReason; the top-level decision: "block" form belongs to PostToolUse and Stop. A Stop hook returning ok: false with a reason makes the model continue working. Bash tool calls expose the full command as tool_input.command. Default command-hook timeout is ten minutes; behaviour on timeout is undocumented and must be tested on pilot day. The three-second fail-open in the GSD hooks is the hook author's line, not the harness; the team hooks do not include it.

Sixth verified defect: arch_drift.py returns 0 unconditionally at line 235 after collecting REMOVE verdicts at line 230. Its only non-zero exits are for unrunnable conditions. team:architecture.md:99 and team:ship.md:221 define a zero-surviving-paths component as BLOCK. No hook may key on this script's exit code; arch_gate.py wraps it and applies the pass rules with a three-valued exit (0 pass, 1 block, 2 unrunnable), which is the house contract validate_roles.py already uses.

Stage 13 as written, local equals CI, cannot pass on this Mac and would be quietly dropped. It is restated as a permanent UNVERIFIED dimension with the reason recorded.

Stage order is enforced at the point of producing each stage's artifact: a hook cannot observe a stage transition, but it observes every Write, so the write of stage N's artifact is denied unless stage N-1's artifact receipt is valid. This closes most of the omission gap.

Bash tool_response does not reliably carry an exit code (verified in coco_posttooluse_checkpoint.py:96-107). Therefore the runner writes its own exit codes to disk and no hook ever parses stdout.

## 3. State model (adopted from the Fable review)

Location: ~/.team/runs/<run-id>/ on the local APFS volume, never inside the project and never under OneDrive, because the owner's memory documents multi-second I/O stalls there. The project carries one pointer, .team-ship/RUN, holding the run id; hooks resolve it by walking up from cwd. No signing key. See receipts.jsonl below for why.

Files and their sole writers:
- run.json, written once by `team-state start`: run_id, command, repo_root, started_at, flags.
- receipts.jsonl, written only by hooks and the two CLIs through a shared library: an append-only chain, each record carrying prev_hash, so truncation or insertion is detectable. The chain detects accidental corruption. It is not claimed as integrity against the model, because the model runs as the same uid and can read any key on disk; a same-uid secret is not a secret. Integrity against the model rests on re-derivation: a hook re-reads HEAD, recomputes the tree digest, and re-parses the stored raw output, so a forged receipt has to also forge the repository state it describes. A root-owned receipt directory is the unforgeable variant, deferred to a later phase.
- gates/<n>.json, written only by `team-gate`: argv, cwd, env_pins, exit, summary (passed, skipped, failed), coverage, red_green entries.
- worktrees.json, written by the PostToolUse hook on observing a successful worktree add or clone.
- .team-ship/EVIDENCE.json, rendered by team-gate; EVIDENCE.md is derived from it and says so in its header.

stage_cursor, build_rounds and status are derived from the receipts by `team-state status` every time they are needed. Nothing writes them. A declared cursor is exactly the field a model would set to satisfy a hook; a derived one has no such field.

Receipt kinds: run-started, stage-opened, artifact-written (path, sha256, lines), agent-spawned (layer, mode, role_hint, worktree), agent-returned, gate-result, worktree-registered, approval (raw user text), block, override (reason), pr-opened (url), stop-checked.

## 4. Design rules every hook and validator follows

Check the persistent effect, never the invoking command. A hook that matches "pytest" is defeated by "make check"; a hook that reads gates/8.json is not. Matchers are keyed to filesystem state, with the tool matcher set to all tools where the guard is about state.

Fail closed, at the run level, because the harness fails open at the call level. Verified on this build on 2026-09-17: a PreToolUse hook that exceeded its configured timeout was killed and the tool call proceeded. So no hook can guarantee that a call does not happen; a hook can only guarantee that an uncertified call cannot be reported as success. Every gating PreToolUse hook therefore does only cheap work (file existence, JSON parse, hash and HEAD comparison, receipt lookup; never a subprocess that runs tests or scans a repository), carries a 60-second timeout rather than a short one, includes no stdin timeout that exits zero, and denies with a reason if it cannot read its input or the state directory. On completing its check it appends a certified receipt keyed by tool_use_id. A paired PostToolUse hook, matching the same tools, looks up that receipt for every gated call; if it is absent the PreToolUse hook was killed, and the PostToolUse hook appends a gate-timeout block receipt naming the tool_use_id and the command. ship_gate.py, fix_gate.py and the Stop guard treat any block receipt as blocking, so a run in which a gate hook was ever killed cannot certify, open a PR, or end cleanly. The certification receipt and the gate-timeout receipt are two further receipt kinds and join the closed set.

Do not copy the subagent exemption. GSD's is_subagent and session_type checks are appropriate for advisories and wrong for blocks; a CI check greps every new hook for that pattern and fails if it appears without a written justification.

Only the wrapper writes evidence. A PreToolUse hook denies any Edit or Write whose path resolves under .team-ship/EVIDENCE.* or ~/.team/, except when the calling process is team-gate, identified by a receipt it wrote in the same tool_use.

Bind evidence to the commit. gates/*.json and EVIDENCE.json record git rev-parse HEAD; the PR-open hook denies if the recorded SHA is not HEAD.

Skip is failure. team-gate computes its own exit code and exits non-zero when skipped is greater than zero; the hook trusts only that exit code, never a narrated pass count.

Independence is structural. The Stage 11 verifier runs as a fresh `claude -p` subprocess in a worktree registered in worktrees.json, and .team-ship/ is gitignored so the worktree cannot contain the builder's artifacts. The hook checks the worktree is registered and that .team-ship/ is absent there before the verifier's first tool call.

Red for the right reason. The naive rule "assertion, not import error" is wrong: a test for a module that does not exist yet correctly fails with ModuleNotFoundError. prove_red therefore uses a three-way classifier. A failure is a valid red when the assertion is inside the test body, or when the missing name resolves to a path this change adds. It is an invalid red when the failure is a syntax or collection error, or an import of a name this change does not add. It is INSEPARABLE, reported as UNVERIFIED, when the test and the implementation live in the same file. prove_red never stashes the user's worktree; it runs in a detached worktree at the parent commit. Coverage attribution catches assert-True tests. The test function's AST is hashed at red-proof time and rechecked at green and at Stage 11; a changed hash is a block.

Rulings on questions the wave-2 verifier briefs surfaced, decided by the brain on 2026-09-17 so that verifiers and builders cite one authority rather than each improvising:

- prove_red, valid red for a missing name. The missing name is a valid red when it resolves to a path the diff adds, or to a symbol the diff adds inside a path that already existed at base. A new function in an existing module raises AttributeError at base, and that is a genuine red. A missing name the diff does not introduce anywhere remains invalid-red.
- run_gate, parity when a CI-pinned tool is absent locally. That is a parity mismatch and exits 1. It is not "cannot measure" and does not exit 2; treating absence as unrunnable would let a missing tool pass through as merely unverified.
- check_artifacts, a forbidden token inside a fenced code block. It counts. A TODO in a plan's code sample is still a placeholder, and the simpler rule has no fence-parsing edge cases. A required heading inside a code fence does not count as present, because a heading is a document-structure claim and a fence removes it from the structure.
- render_pr_body, override text. Rendered verbatim inside a fenced code block, which preserves the exact words the human used while making any markdown or HTML inside them inert.

Rulings for prove_red round 5, decided by the brain on 2026-09-17 after four builder rounds produced a stub. These refine REVIEW-OPUS.md section A for a machine that has neither pytest nor coverage installed and for a Python-only pilot:

- Runner. prove_red runs each test function in its own subprocess through an internal `_run-one` subcommand that imports the test module by file path with importlib and calls the function directly, emitting one JSON object describing the outcome, the exception type, the missing-name attribute, and the traceback frames. pytest and junit XML are not used in this version. A test function that takes parameters cannot be run without a fixture-aware runner and is reported UNRUNNABLE with exit 2 naming the test. Fixture-aware execution and coverage attribution are deferred to task 9b in the register.
- Worktree. The throwaway detached worktree is created from HEAD under the run directory at worktrees/red-<sha8>-<pid>, never under .team-ship/ and never from base. GREEN runs there first; then every implementation path is reverted to base content inside that worktree, and RED runs. Test paths and support paths are left at HEAD. Both phases therefore run the same test source, which is what makes the AST hash meaningful.
- Valid red for an assertion. An AssertionError is a valid red when the frame that raised it lies in a test path or a support path, which admits a helper defined in the test module. It is invalid-red when the raising frame lies in an implementation path, because an assert inside the code under test is a crash, not a test assertion. The raising frame is recorded per test as last_frame.
- Invalid red is everything that is not a valid assertion and not a resolvable missing name: SyntaxError or IndentationError on import, TypeError, FileNotFoundError, NameError, a missing name the diff does not introduce, and any error the runner cannot classify.
- Enumeration is Python-only. Every changed .py file is parsed for test functions, both top-level def test_* and methods test_* on classes named Test*. A test found in a file that is not a test path is INSEPARABLE and is recorded without being run. Non-Python changed files are support: left at HEAD, listed in the gate file under support_paths, and never reverted, because reverting a lockfile or a data file manufactures a wrong-reason red.
- Base resolution, in order: the --base argument; .team-ship/ARCH-PLAN.json declaredAtCommit when present; git merge-base HEAD against the remote HEAD from git symbolic-ref refs/remotes/origin/HEAD; HEAD~1 only when the repository has no remote at all. The chosen source is recorded in the gate file. Anything else is exit 2.
- Exit mapping. Exit 0 when every runnable test is valid-red then green with an unchanged hash, even when some tests are INSEPARABLE, which are marked UNVERIFIED in the gate file and counted on the verdict line. Exit 2 when every test is INSEPARABLE, when the new-test set is empty (NOT_APPLICABLE), when the working tree is dirty without --allow-dirty, or when anything cannot be measured. Exit 1 for never-red, invalid-red, green-fails, hash-changed, or a test removed since the proof.
- Fixture generators for every wave-2 script anchor on the generator's own file location, accept --out for an alternative root, and pin GIT_AUTHOR_DATE and GIT_COMMITTER_DATE from TEAM_FIXED_TS so commit SHAs are identical between two generations. The accepted variance under diff -r is confined to .git/index and .git/logs.

Rulings from the verify_independent round-2 verdict, 2026-09-17, binding on tasks 8 and 10:

- The verify worktree carries exactly one untracked file under .team-ship/, the RUN pointer, written by verify_independent setup after the tracked-file check has passed. Without it nothing executed inside the worktree can resolve the run directory. The independence guarantee is that EVIDENCE.md, EVIDENCE.json and the stage documents are absent, not that the pointer is absent.
- run_gate.py accepts --role builder|verifier, defaulting to builder. The verifier role writes gates/<n>-verifier.json in the run directory so the builder's gates/<n>.json is never overwritten, and verify_independent compare reads gates/8.json against gates/8-verifier.json by default. The verifier prompt printed by setup invokes run_gate.py by absolute path with --role verifier and asks for nothing but the three exit codes; the comparison is done by compare, never by the model.
- The printed verifier invocation strips ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN, ANTHROPIC_MODEL and ANTHROPIC_SMALL_FAST_MODEL with env -u, passes --model explicitly, --strict-mcp-config with an empty mcpServers set, and --allowedTools Bash,Read,Grep,Glob, so a shell configured for the local model lane cannot silently run Stage 11 on a local model.
- The directory in which the .team-ship/RUN walk-up finds the pointer must be the git top level of --repo-root. A pointer found above a nested, unrelated repository is exit 2 naming both directories; a run is bound to exactly one repository.
- An error is one reason line on stderr beginning with "ERROR:". Evidence lines may follow it, one item per line, such as the tracked paths under .team-ship/. Verifiers test the first line for the reason and the following lines for the evidence.

Rulings for wave 3, decided by the brain on 2026-09-18 and specified in WAVE3-BRIEFS.md:

- Latest receipt wins. Receipts are an append-only log and a file reflects its latest write. verify_chain compares only the highest-seq gate-result receipt per gate_file and the highest-seq artifact-written receipt per path against disk; earlier receipts for the same file are superseded, remain chain links, and are counted in derive_status. Path validation still runs on every receipt. Gate files are rewritten atomically through a temporary name and os.replace.
- Stage 13, CI mirror, has no gate file of its own. It is satisfied when gates/7.json exits 0 and the argv recorded in gates/8.json equals the argv in gates/7-discover.json, which proves the command run locally was the CI command. ship_gate computes and records this row.
- Overrides. An override receipt names a gate and carries the human's instruction verbatim. A failing or missing required gate that an override names is recorded OVERRIDDEN and does not block; the verdict is PASS_WITH_OVERRIDE with exit 0 and the instruction appears in gates/14.json and the PR body. A broken chain, a head mismatch, a block receipt or a gate-timeout receipt can never be overridden. The approval receipt can: an override naming "approval" is a stronger human act than an approval and marks stage 6's requirement OVERRIDDEN with the instruction verbatim. An override that names no failing or missing gate is listed as unused and changes nothing. Chain classification belongs to gate_state: the aggregator calls verify_chain first and treats "broken" as exit 1 and "unrunnable" as exit 2; it does not re-parse receipts into its own exit 2. Every repository-relative path uses the repository root from run.json after checking its HEAD, never the raw --repo-root argument. The latest gate-result receipt for gates/9-recheck.json must carry a higher seq than the latest receipt for gates/9.json; a recheck recorded before the proof it rechecks is meaningless and blocks stage 4 of the fix pipeline and stage 11 of the ship pipeline.
- A gate that exited 2 is UNVERIFIED and blocks like a failure at the aggregator; only the aggregator's own inability to read the run, the manifest, HEAD or the chain is exit 2.
- ship_gate stage <n> is a pure query for the hooks: it writes nothing and prints one JSON object; only ship_gate check writes gates/14.json.
- arch_gate resolves the arch-index scripts from ARCH_INDEX_SCRIPTS, else <repository root>/skills/arch-index/scripts, else ~/.claude/skills/arch-index/scripts, and records the chosen directory, so the same script runs on this machine and on the CI runner.
- CI command discovery. A workflow step may contribute several commands: every line of a run block is considered, in file order, and a line qualifies only by its runner shape, never by a job or step name. Recognised shapes: pytest, python -m pytest, npm test, npx vitest or jest, vitest, jest, cargo test, go test, `bash|sh <path>` whose basename matches *test*.sh, smoke*.sh, *-smoke.sh, run_fixtures*.sh or check-*.sh, and `python3|python <path> --self-test`. discover records `commands: [{argv, source, sourceLine}]` and exits 2 when none qualifies; run executes each command without a shell and the gate fails if any real exit is non-zero, any pytest-shaped summary shows failed, skipped or errors, or a pytest-shaped summary collected no tests; coverage applies to pytest-shaped commands only and is NOT_APPLICABLE with exit 2 when there are none. This is what makes this repository's own CI, which runs bash test scripts and a Python self-test, gateable. On this repository's ci.yml discovery records ten commands across several steps, including the six bash tests/check-*.sh sanity checks; that is intended, because the CI gate is every recognised check the workflow runs and the local mirror runs all of them. A run line containing a shell operator (||, &&, ;, |, >, <) or an unquoted variable cannot be reproduced without a shell and is recorded as skipped with its reason, never executed; run, parity and coverage refuse a discover file recorded at a different HEAD; EVIDENCE.json carries runId from run.json.
- Hooks (task 14, specified in WAVE4-HOOKS-BRIEF.md). The four hooks live at skills/team-gate/hooks/ and are registered by the repository's own .claude/settings.json with a 60-second timeout; the owner's global settings are untouched. Every receipt a hook writes goes through gate_state.py receipt with the hook payload on stdin, so there is one writer. The run's hooks mode, observe or enforce, is a flag in run.json set at start; observe mode computes the same decision, records it in the certified receipt as would-deny or would-block, and writes nothing to stdout. Approval and override receipts are written by the UserPromptSubmit hook from the human's literal prompt. An approval is recognised only when the normalised prompt contains no question mark, has no negation before the phrase, and either equals an approval phrase or begins with one followed by a non-letter boundary; ship_gate trusts the presence of the approval receipt, so the matcher is the gate. The artifact guard maps a .team-ship/ path to its stage through ship-manifest.json and asks ship_gate stage <n>; the Post hook appends artifact-written and stage-opened and runs check_artifacts stage-output, appending a block receipt on failure. The stage guard gates gh pr create, gh pr merge and git push on ship_gate check and records agent-spawned and agent-returned. The Stop guard blocks once while a run is in flight and allows on re-entry or when background tasks exist.
- Requirements matrix grades are MET, NOT MET and UNVERIFIED; PARTIAL was specified and is unreachable because gate exits are only 0, 1 or 2, so it is removed. Duplicate entry ids in EVIDENCE.json are a malformed file: every consumer exits 2 naming the id. Tags and claims inside fenced code in a PR body are checked like plain text, so a false claim cannot hide in a fence.
- EVIDENCE.json shape, fixed by the task 8 rebuild and consumed by task 11: a top-level object with schemaVersion, head (git rev-parse HEAD of the measured repository), and entries, a list in which each entry carries id ("E1", "E2", in gate file order), gate, verdict, exit, head, command, summary and detail. run_gate evidence aggregates every gates/*.json in the run directory that is not a -verifier file, so handoff and matrix gates appear alongside the test gates. [E<n>] tags in a PR body resolve to the entry whose id is E<n>. REVIEW-OPUS.md B.2 describes a single gate's receipt shape and is the source of the per-entry fields.

Overrides are recorded, not prevented. A human may open a PR with a non-green gate. The hook denies gh pr create unless every gate is green or an override receipt exists carrying the user's literal instruction text; the PR body then carries the override verbatim. GRC's PR #314 becomes a recorded decision rather than a silent bypass.

Task 20 rulings (2026-09-18, from the prose inventory in TASK20-INVENTORY.md; full text in TASK20-BRIEF.md). The exit contract wins over prose that names a different verdict: an unrunnable validator is exit 2, UNVERIFIED, which blocks the pull request. Architecture currency is judged at Stage 1: arch_gate baseline records pin, HEAD and status in gates/1-arch-baseline.json, and the Stage 13 conformance gate compares the pin to that baseline, never to the post-build HEAD. NOT_APPLICABLE and DISABLED arch statuses are exit 2 and block unless an override names gate "arch", the coverage precedent. Provisioning integration dependencies stays a model action recorded, when it fails, as an override naming gate "integration". The three-round bound is a "rounds" row in both aggregators, overridable. Merge claims ("merged", "ci green", "shipped") are findings in claim_evidence unless git ancestry, the stage 13 row or a pr-opened receipt backs them. Matching is fail closed: a future-tense sentence such as "once this is merged" is a finding, and the cost of a reword is accepted so that a merge masquerade cannot pass. The before-and-after comparator for reanalyse is deferred. Command files invoke scripts by the installed path ~/.claude/skills/team-gate/scripts/<script>; the symlink is created after merge with the owner's agreement.

## 5. Gate-by-gate mechanism table

Seventy-six gates specified across team:ship.md, team:fix.md and team:evidence.md. Full table in REVIEW-OPUS.md Part 1.

| Class | Count | Treatment |
|---|---|---|
| Computable | 62 | Script computes, hook verifies the receipt. Eleven are handoff transitions; nine already have validators. |
| Structural | 5 | Approval provenance, verify independence, hard-gate semantics, two fix-pipeline gates. Enforced by making the violation impossible, not by judging. |
| Judgement with schema | 9 | Stay prose; output must match a schema so a non-answer is detectable. |
| Silent prose | 0 | |

Cheap claims (file exists, SHA matches, receipt chain intact) are recomputed inside the hook. Expensive claims (a test run, a coverage measurement) are computed by the runner, which writes a receipt; the hook verifies the receipt by re-derivation rather than re-running. Exit contract everywhere is three-valued: 0 pass, 1 block, 2 unrunnable, matching validate_roles.py.

Reconciliation with the Fable boundary: Stages 7, 8, 9, 10 and 13 are the runner's region; Fable and Opus agree. Fable's HMAC receipt integrity is superseded by Opus's re-derivation, above. Fable's list of transitions not gateable in the moment is narrowed by Opus's rule of gating each stage's artifact write against its predecessor. Sonnet's AST-hash binding and Opus's three-way red classifier are complementary and both apply to Stage 9.

## 6. Files to create and settings to add

Hooks, Node to match the GSD convention, under ~/.claude/hooks/. None carries a stdin timeout; all fail closed by denying with a reason if input or state cannot be read.

| Hook | Event and matcher | Purpose |
|---|---|---|
| team-stage-guard.js | PreToolUse and PostToolUse, Bash | Pre: denies gh pr create and git push unless ship_gate.py exits 0 or an override receipt exists, and appends a certified receipt on completing the check. Post: for every gated Bash call, looks up the certified receipt by tool_use_id and appends a gate-timeout block receipt if it is absent. |
| team-artifact-guard.js | PreToolUse and PostToolUse, Write, Edit, MultiEdit | Pre: denies writes to generated artifacts and to ~/.team/; denies the write of stage N's artifact unless stage N-1's receipt is valid; appends a certified receipt on completing the check. Post: same certification lookup, same gate-timeout receipt on absence, and appends the artifact-written receipt with the file's sha256 and line count. |
| team-stop-guard.js | Stop | Returns ok false with the remaining work when a run is in flight and its gate does not exit 0. |
| team-turn-log.js | UserPromptSubmit | Appends a hashed record of each user turn so approval provenance is harness-written. Never blocks. |

Validators, Python standard library only, source in the coco repo at skills/team-gate/scripts/ and installed at ~/.claude/skills/team-gate/scripts/, the same arrangement arch-index uses. Every invocation in every command file uses the installed absolute path.

| Script | Computes |
|---|---|
| gate_state.py | Shared library: state read and write, binding digests, receipt append, re-derivation checks. |
| check_artifacts.py | Preconditions, the pre-approval declaration check, approval artifacts, the six handoff transitions. |
| run_gate.py | Stage 7 parity, Stage 8 execution with skip as failure, Stage 10 coverage, the evidence protocol steps. |
| prove_red.py | Stage 9 with the three-way classifier, detached worktree, AST hash. |
| verify_independent.py | Stage 11 setup, compare and teardown against a registered clean worktree. |
| claim_evidence.py | Stage 12 quantitative claims against EVIDENCE.json, and the requirements matrix. |
| ci_mirror.py | Stage 13, records UNVERIFIED with reason. |
| arch_gate.py | Wraps arch_drift.py and validate_index.py with the correct three-valued exit. |
| render_evidence.py, render_approval.py, render_pr_body.py | Generate the Markdown views from the JSON; the Markdown is never hand-written. |
| ship_gate.py, fix_gate.py | The single aggregator each hook calls. |

Data: SKILL.md stating the protocol and its honest ceilings; receipt-schema.md; ship-manifest.json mapping each stage to required inputs and outputs; claim-lexicon.json; test-patterns.json; fixtures/ with one known-bad case per gate; run_fixtures.sh asserting the exact exit code per fixture, mirroring arch-index. The fixtures run in the existing CI step at .github/workflows/ci.yml:187-189 alongside validate_roles.py.

settings.json: two PreToolUse entries inserted before the existing gitnexus entry so a gate failure short-circuits before enrichment work, one Stop entry, one UserPromptSubmit entry. Exact JSON in REVIEW-OPUS.md section C.2.

Edits to existing files: the fourteen relative invocations in six files under ~/projects/coco/commands/team/; .gitignore in coco gains .team-ship/; team:ship.md line 8 renames its "Option B" label.

## 7. Landing zone and migration order

Twenty of the twenty-two team files are symlinks into ~/projects/coco/commands/team/. Only team.md and agent-team.md are regular files under ~/.claude/commands. team:roles.md is generated from systems/team/roles.yaml by build_roster.py and is never hand-edited. Every change to a pipeline file therefore lands in the coco repo as a branch and a pull request.

coco is on main, four commits behind origin/main at 8fac7c0, with three untracked paths (.handoff-archive/, HANDOFF.md, skills/karpathy-guidelines/EXAMPLES.md) that do not touch the retrofit surface. Work happens in a git worktree branched from origin/main and the worktree is removed after merge.

Order, each step leaving every command working:
1. Fix the fourteen relative invocations in six files to the installed absolute path. One commit, zero behavioural risk, restores the gates that already exist.
2. Add .team-ship/ to .gitignore in coco, and document that consumers must do the same; this is the prerequisite for structural independence.
3. Land team-gate and team-state as Tier B in systems/team/, with fixtures and a self-test in the CI step. At this point the model can call them but nothing forces it.
4. Land the receipt hooks in observe mode: they write receipts and never deny. Run one real pipeline against them and read the chain.
5. Turn on the first deny: gh pr create blocked without green gates or a recorded override.
6. Turn on the Stop hook: the turn cannot end with an open run that has a stage without its receipt.
7. Turn on the Agent-spawn gates: no Layer 2 spawn without a Layer 1 artifact receipt, no Stage 11 spawn without a registered clean worktree.
8. Extend to fix, develop, test, verify and reanalyse, then delete the prose each mechanism now covers.

## 8. Pilot

/team:fix. It is the smallest command that exercises the hardest mechanism, TDD red-green. Success is: a deliberately planted bug, a run that ends with gates/*.json present and chained, a receipts.jsonl whose chain verifies, an EVIDENCE.json whose SHA is HEAD, and one deliberate attempt to skip the red proof that is denied by the hook with the reason visible in the transcript.

## 9. Pilot-day assumptions, status as of 2026-09-17

Resolved empirically in an isolated CLAUDE_CONFIG_DIR against oMLX, so the live settings were never touched:

- Timeout: the harness fails open. A PreToolUse hook that exceeded its 5-second timeout was killed and the tool call proceeded (marker file present). Section 4 was amended in response: gates are cheap-only with a 60-second timeout, and paired PostToolUse hooks convert a killed gate into a run-level block.
- agent_id and agent_type are present on subagent tool calls, and a hook registered after a subagent launched still fired for it.
- tool_use_id in a hook payload matches the session transcript; subagent ids live in the agent_transcript_path that SubagentStop supplies, not in the parent transcript.
- A command Stop hook returning decision block resumes the model. stop_hook_active is false on the first fire and true on re-entry, which is sufficient to prevent a loop without a counter.

Documentation-confirmed only: that a deny stops a call inside a bypassPermissions subagent. This session runs in auto mode and subagents inherit it, so the mode cannot be exercised from here. The official docs state hooks fire and can deny in every mode. It is recorded as unverified rather than claimed.

Also learned: a fresh CLAUDE_CONFIG_DIR against oMLX cold-prefills the full system prompt in roughly eleven minutes, so harness tests on this substrate are slow but valid.

## 10. Out of scope, deliberately

team:roles.md, except that select_roles.py replaces reading the whole 154,053-character file per run; role selection stays judgement. The content pipelines (present, communicate, document, think, research, scrape) carry two to eight normative rows each and need only the artifact-written receipt. Knowledge skills are not touched. team:ship.md line 8 calls its approval design "Option B"; it is renamed to avoid colliding with this plan's fork.

## 11. Open decision for the approval gate

Whether the pilot runs against oMLX or against the Anthropic-hosted model the owner normally uses. The mechanisms are model-independent; the pilot's purpose is to prove the hooks and runner, so the faster model is the right choice unless cost is the constraint.
