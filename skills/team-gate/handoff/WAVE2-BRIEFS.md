# Wave 2 builder briefs

Five builders run in parallel. Each reads only its own section plus the Common section. Each owns exactly the files named in its section and touches nothing else.

## Common, applies to every wave-2 builder

Worktree, work only here, do not commit:
~/projects/coco/.claude/worktrees/team-gate-retrofit

Read first, in this order:
1. <scratchpad>/team-retrofit/PLAN.md sections 3 and 4. These override anything else.
2. skills/team-gate/scripts/gate_state.py in the worktree. This is the verified shared library. Import it with `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` then `import gate_state`. Use its public functions: state_root(), find_run(cwd), append_receipt(run_dir, kind, detail, hook_payload=None), verify_chain(run_dir), derive_status(run_dir). Receipt kinds are a closed set of fourteen; appending an unknown kind raises InvalidReceiptKind.
3. skills/team-gate/references/receipt-schema.md in the worktree.
4. systems/team/validate_roles.py and skills/team-gate/scripts/arch_gate.py in the worktree, for house style.
5. The sections of the Opus and Sonnet reviews named in your own section, at:
   <scratchpad>/team-retrofit/REVIEW-OPUS.md
   <scratchpad>/team-retrofit/REVIEW-SONNET.md
   Where either review mentions an HMAC key, ignore it; there is no key.

Rules that bind every script:
- Python standard library only. Type hints on every function. No em dashes or section signs in any prose.
- Exit contract is three-valued and stated in the module docstring: 0 pass, 1 block, 2 unrunnable. No other exit code exists. sys.exit appears only in the __main__ guard; library code raises.
- Every gate result is written as JSON to the run's gates/<n>.json through your own code, including your own computed exit code. Never infer an exit code from a tool response.
- Every gate file records git rev-parse HEAD of the repository it measured.
- After writing a gate file, append a gate-result receipt through gate_state.append_receipt with detail containing gate, gate_file, gate_sha256 (sha256 of the file you just wrote), exit, and a summary.
- Fail closed: if the run directory, the repository, or a required input cannot be read, exit 2 with a one-line reason on stderr.
- Static fixtures: skills/team-gate/scripts/fixtures/<your-script-name>/make_fixtures.py generates every fixture deterministically. Honour env TEAM_FIXED_TS for timestamps. Fixtures that need a git repository create one with git init and one commit inside a directory named _build/ under your fixtures directory. Do NOT edit the worktree .gitignore: the line `skills/team-gate/scripts/fixtures/*/_build/` is already present and covers your _build/ directory; five builders appending to one file would race. Confirm with `git check-ignore -v skills/team-gate/scripts/fixtures/<your-script-name>/_build` and quote it in your report. Commit the generator and any templates, never a nested .git. Before finishing, run `find skills/team-gate/scripts/fixtures/<your-script-name> -name .git -not -path "*/_build/*"` and confirm it prints nothing.
- --self-test runs make_fixtures.py if _build/ is absent, then runs your CLI as a subprocess for every fixture with subprocess.run([sys.executable, __file__, ...]) and asserts returncode. One line per fixture: "<name>: expected <n> got <n> OK" or FAIL. Overall exit 0 only if all match. Never assert on a direct function call.
- Do not modify gate_state.py, arch_gate.py, or any file another wave-2 builder owns.

Report, return only this:
1. `find skills/team-gate -newer skills/team-gate/scripts/gate_state.py -type f -not -path "*/_build/*" | sort` with wc -l per file.
2. `python3 -m py_compile <each of your scripts>; echo exit=$?`
3. Full --self-test output.
4. The one adversarial case named in your section, run through the CLI, with its exit code.
5. `git status --porcelain skills/ .gitignore`
6. One line: "Files created: N. Committed: NO."
If a self-test line fails, report it; do not weaken the assertion.

## Task 7: check_artifacts.py and ship-manifest.json

Read REVIEW-OPUS.md sections 1.1, 1.2, 1.3 and 1.15, and the ship-manifest.json row in section C.1.

Build skills/team-gate/references/ship-manifest.json: for each of the fourteen ship stages, the required input artifacts, the output artifact, minLines, requiredHeadings, and forbidTokens. Take the artifact names from commands/team/ship.md in the worktree (the handoff table around lines 256 to 285). Default forbidTokens: TODO, TBD, placeholder, lorem, FIXME, "to be written". Default minLines 12 for briefs and plans, 3 for JSON declarations.

Build skills/team-gate/scripts/check_artifacts.py with subcommands:
- `stage-inputs <n>`: every input the manifest requires for stage n exists under .team-ship/ and is non-trivial (at least minLines lines, every requiredHeading present, no forbidToken). Exit 0 or 1; 2 if the manifest or run cannot be read. Writes gates/handoff-<n>.json.
- `stage-output <n> <path>`: validates a just-written artifact the same way, computes its sha256 and line count, appends an artifact-written receipt with path, sha256, lines, stage. Exit 0 or 1.
- `approval-ready`: the five approval-gate artifacts (research brief, architecture options, plan, ARCH-PLAN.json, review findings) all exist and are non-trivial. Exit 0 or 1. Writes gates/approval-inputs.json.
Fixtures: complete-stage (0), missing-input (1), trivial-artifact-too-short (1), forbidden-token (1), missing-heading (1), no-run (2).
Adversarial case for the report: an artifact padded to minLines with repeated filler lines that contains no required heading; it must exit 1.

## Task 8: run_gate.py

Read REVIEW-OPUS.md sections 1.4, 1.5, 1.7, 1.17, Part 0 Rulings 1 and 2, and section B in full. Read commands/team/evidence.md in the worktree in full. Read REVIEW-SONNET.md section 2 and rows 2a to 2d of section 8.

Build skills/team-gate/scripts/run_gate.py with subcommands:
- `discover`: finds the repository's authoritative gate command by parsing .github/workflows/*.yml (the run: steps of the test or check job), then Makefile targets named check or test, then package.json scripts. Never accepts a free-form command from the caller. Writes gates/discover.json with the command, its source file and line, and the tool versions CI pins. Exit 2 if nothing is found.
- `parity`: compares locally installed versions of every tool the discovered command uses (pytest, ruff, mypy, node, npm at minimum) with the CI-pinned versions. Any mismatch is exit 1. Writes gates/7.json.
- `run`: executes the discovered command with subprocess, captures stdout, stderr and the real exit code, parses the pytest summary line into passed, skipped, failed (and the equivalent for jest or cargo test if that is what was discovered). Exit 1 if failed is greater than zero OR skipped is greater than zero: a skip is a failure. Writes gates/8.json and appends the gate-result receipt.
- `coverage`: re-runs with --cov --cov-branch when pytest, parses the total percentage, writes gates/10.json. If the coverage tool is absent, writes UNVERIFIED with the reason and exits 1, never 0.
- `evidence`: aggregates every gates/*.json into .team-ship/EVIDENCE.json per the B.2 schema, then renders .team-ship/EVIDENCE.md from it with a first line reading "Generated by run_gate.py from EVIDENCE.json. Do not edit; edits are detected." Records HEAD in both.
Fixtures: tiny repositories each with a pytest suite and a minimal .github/workflows/ci.yml: all-pass (0), one-fail (1), one-skip (1), parity-mismatch (1, pin a ruff version that is not installed), no-ci-config (2).
Adversarial case for the report: the one-skip fixture, showing that pytest itself exits 0 and run_gate.py exits 1.

## Task 9: prove_red.py

Read REVIEW-OPUS.md section A in full (A.0 through A.5) and section 1.6. Read REVIEW-SONNET.md section 3 and rows 3a and 3b of section 8. PLAN.md section 4, the paragraph beginning "Red for the right reason", is the authoritative statement of the classifier and overrides A where they differ.

Build skills/team-gate/scripts/prove_red.py with subcommands:
- `enumerate --base <commit>`: lists every test function added or modified between base and HEAD, by parsing the diff for test files and the test functions within them. Writes gates/9-tests.json.
- `prove --base <commit>`: for each enumerated test, creates a detached git worktree at base under the run directory (never stashes, never touches the user's worktree), runs that single test there, and classifies the outcome. valid-red-assertion: the failure is an AssertionError whose traceback's last frame is inside the test body. valid-red-missing-name: the failure is ImportError, ModuleNotFoundError or AttributeError, and the missing name resolves to a file path that the diff adds. invalid-red: any syntax error, collection error, or a missing name that the diff does not add. never-red: the test passes at base. inseparable: the test function and the implementation it exercises live in the same file, reported as UNVERIFIED. Then hashes the test function's AST (ast.dump of the function node, normalised) and records it. Then runs the same test at HEAD in the user's worktree; it must pass, and the AST hash must be unchanged. Writes gates/9.json with one red_green entry per test carrying classification, red traceback tail, green result, ast_hash. Removes the detached worktree on every exit path.
- `recheck`: re-hashes every test recorded in gates/9.json at current HEAD; any changed hash is exit 1 naming the test. This is what Stage 11 calls.
Exit: 0 when every test is valid-red then green with a stable hash; 1 when any test is never-red, invalid-red, green-fails, or hash-changed; 2 when unrunnable or when every test is inseparable.
Fixtures: proper-red-green (0), never-red (1), wrong-reason-syntax-error (1), weakened-after-red (1; the test's assertion is loosened between the red commit and HEAD), inseparable-same-file (2), new-module-import-red (0; the test imports a module the diff adds, so ModuleNotFoundError at base is a valid red).
Adversarial case for the report: weakened-after-red, showing the hash mismatch line and exit 1.

## Task 10: verify_independent.py

Read REVIEW-OPUS.md section 1.8 and Part 0 Ruling 5. Read REVIEW-SONNET.md section 4 and rows 4a and 4b of section 8. Read commands/team/verify.md in the worktree. PLAN.md section 4, the paragraph beginning "Independence is structural", is authoritative.

Build skills/team-gate/scripts/verify_independent.py with subcommands:
- `setup`: creates a git worktree at HEAD under the run directory at verify-wt/, asserts that .team-ship/ does not exist inside it (if it does, the directory is tracked in git and independence is impossible; exit 1 naming the tracked files), registers the worktree path in the run's worktrees.json, appends a worktree-registered receipt, and prints two lines: the worktree path, and the exact `claude -p` invocation the orchestrator must use to spawn the verifier as a fresh subprocess with cwd set to that worktree (the verifier must never be an in-session subagent). Exit 0, or 1, or 2 if git is unavailable.
- `compare <builder-gate-json> <verifier-gate-json>`: both files are gates/8.json-shaped. Compares exit, passed, skipped, failed. Any difference is exit 1 with both values quoted. Writes gates/11.json.
- `teardown`: removes the worktree and appends a receipt. Exit 0 or 2.
Fixtures: clean-worktree-ok (0), team-ship-tracked (1; a repository where .team-ship/EVIDENCE.md was committed), gate-mismatch (1), not-a-git-repo (2).
Adversarial case for the report: team-ship-tracked, showing the tracked file named in the reason and exit 1.

## Task 11: claim_evidence.py, render_evidence.py, render_approval.py, render_pr_body.py, claim-lexicon.json

Read REVIEW-OPUS.md sections 1.9, 1.11 and B in full, and the claim-lexicon.json row of section C.1. Read REVIEW-SONNET.md section 5 and rows 5a to 5c of section 8. Read commands/team/evidence.md in the worktree, the paragraphs about claims in a PR body.

Build skills/team-gate/references/claim-lexicon.json: a map from claim tokens to the EVIDENCE.json field that backs them (for example "tests pass" requires gates 8 failed 0 and skipped 0; "N passed" requires passed equal to N; "X% coverage" requires gates 10 coverage equal to X within 0.5; "ruff clean" and "mypy clean" require the corresponding tool exit 0 in gates 7 or 8), plus an unbacked-word list (comprehensive, robust, idempotent, thoroughly, production-ready, fully tested, bulletproof, and similar) that is flagged wherever it appears in a results section without an [E<n>] citation.

Build skills/team-gate/scripts/claim_evidence.py with subcommands:
- `check <pr-body.md>`: every sentence inside the results or evidence section must carry an [E<n>] tag that names an entry in .team-ship/EVIDENCE.json; every quantitative claim's number and qualifier must match the cited entry; every unbacked-word occurrence without a tag is a finding. Any finding is exit 1, each quoted with its line. Writes gates/12.json.
- `matrix <plan.md>`: extracts requirement identifiers from the plan and maps each to the gate evidence that satisfies it, grading MET, PARTIAL, NOT MET, UNVERIFIED. Writes gates/11-matrix.json. Exit 1 if any requirement is NOT MET.

Build skills/team-gate/scripts/render_evidence.py: renders EVIDENCE.md from EVIDENCE.json with the generated-file header; `--check` re-renders in memory and exits 1 if the on-disk .md differs, which detects hand edits.

Build skills/team-gate/scripts/render_approval.py: assembles the five approval-gate artifacts into .team-ship/APPROVAL.md for Stage 5 display; exit 1 naming any missing artifact.

Build skills/team-gate/scripts/render_pr_body.py: generates the quantitative section of the PR body from EVIDENCE.json, every sentence carrying its [E<n>] tag; the model writes only the narrative section above it. If an override receipt exists in the run, renders the override verbatim in its own section.

Fixtures: all-claims-backed (0), number-mismatch (1), unbacked-adjective (1), hand-edited-evidence-md (1 through render_evidence --check), missing-approval-artifact (1), requirement-not-met (1).
Adversarial case for the report: a PR body claiming "759 passed" against an EVIDENCE.json recording 759 passed and 4 skipped, with the sentence "all tests pass"; it must exit 1 on the skip.
