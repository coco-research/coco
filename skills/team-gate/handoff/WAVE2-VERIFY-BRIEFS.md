# Wave 2 verifier briefs

One Sonnet verifier per script. Each reads the Common section and its own section. The verifier has not seen the builder's report and must not look for it.

## Common, applies to every wave-2 verifier

You are the VERIFIER. A builder has produced a script and fixtures in this git worktree and claims they are correct. You have not been shown the claim. Form your own evidence, then deliver a verdict. Worktree, read-only, do not edit or commit:
~/projects/coco/.claude/worktrees/team-gate-retrofit

The spec the script must satisfy is the builder's brief. Read the Common section and the named Task section of:
<scratchpad>/team-retrofit/WAVE2-BRIEFS.md
and PLAN.md sections 3 and 4 in the same directory. Where the brief and the code disagree, the brief wins.

Run every check from the worktree root and quote actual output.

C1. `python3 -m py_compile <script>; echo exit=$?` for every script in scope.
C2. `python3 <script> --self-test; echo exit=$?`, all lines. Then read the self-test code and confirm every assertion is on a subprocess returncode of the CLI, never a direct function call; quote the subprocess.run line. A direct-call assertion is a MAJOR finding.
C3. Exit contract. `grep -nE "sys\.exit|return [0-9]" <script>`. Every exit is 0, 1 or 2 with the documented meaning. sys.exit appears only in the __main__ guard. Any other value or location is a BLOCK.
C4. `grep -nE "^import |^from " <script>`: standard library only. Confirm gate_state is imported via sys.path insertion of the script's own directory; run the script from a different cwd to prove the import still resolves.
C5. Gate files and receipts. Run the script's main success path against a fixture and confirm: it wrote gates/<n>.json containing exit, summary and head (git rev-parse HEAD of the measured repository); it appended a gate-result receipt whose detail carries gate, gate_file, gate_sha256, exit; and gate_sha256 equals sha256 of the file on disk. Then run `python3 skills/team-gate/scripts/gate_state.py verify-chain` in that run and confirm exit 0.
C6. Fixture determinism. Run make_fixtures.py into two temp roots with the same TEAM_FIXED_TS and `diff -r`; any difference is a MAJOR finding. Confirm committed fixture templates match a fresh generation where they are meant to be committed.
C7. Repository hygiene. `find skills/team-gate/scripts/fixtures/<name> -name .git -not -path "*/_build/*"` must print nothing; `git check-ignore -v skills/team-gate/scripts/fixtures/<name>/_build` must match the glob at .gitignore:49; `git add -n skills/team-gate/` must list nothing under any _build/ or nested .git. Any hit is a BLOCK.
C8. Fail-closed. Run the script with the run directory unreadable (chmod 000 on a copy, restore after) and with TEAM_STATE_ROOT pointing at a nonexistent path; both must exit 2 with a one-line stderr reason, never 0.
C9. Prose hygiene: `grep -nE "—|§"` on every script and data file in scope. MINOR.
C10. The task's named adversarial case from the builder's brief, reproduced independently through the CLI, with exit code and stderr quoted.
C11. The new adversarials in your section, which the builder was not told about. These are the checks most likely to find something.

Rulings. Four questions that some sections below phrase as "report and rule" have since been decided by the brain and recorded in PLAN.md section 4, in the block beginning "Rulings on questions the wave-2 verifier briefs surfaced". Where a section below asks you to rule on one of those four (valid red for a symbol added to an existing module; parity when a CI tool is absent locally; forbidden tokens and required headings inside code fences; rendering of override text), do not rule: read the ruling in PLAN.md and confirm the code implements it. A mismatch with the ruling is a BLOCK. The builders were sent these rulings as supplements after launch, so also confirm the corresponding fixture named in the supplement exists and passes: new-symbol-in-existing-module (task 9), tool-absent or an equivalent parity fixture (task 8), forbidden-token-in-fence and heading-only-in-fence (task 7), override-with-markup (task 11).

Deliver, in this order: VERDICT: PASS or BLOCK on the first line; each blocking reason with quoted evidence; MAJOR and MINOR findings; C2, C5, C10 and C11 outputs verbatim; one sentence on whether this script may be aggregated by ship_gate.py as-is.

## Verify Task 7: check_artifacts.py and ship-manifest.json

Scope: skills/team-gate/scripts/check_artifacts.py, skills/team-gate/references/ship-manifest.json, skills/team-gate/scripts/fixtures/check_artifacts/.

Also check: ship-manifest.json covers all fourteen stages of commands/team/ship.md with the artifact names taken from that file's handoff table (lines 256 to 285), not invented. Quote any stage whose artifact name differs from ship.md.

New adversarials:
A1. An artifact that satisfies minLines and contains every required heading, but every heading's body is empty (heading lines and blank lines only). Does stage-output call it non-trivial? Rule whether that is acceptable; recommend a body-length-per-heading check if it passes.
A2. A forbidToken that appears only inside a fenced code block. Does it count? Report the behaviour and rule; either is defensible if documented, undocumented is a MINOR.
A3. A symlink at the artifact path pointing outside .team-ship/. Does stage-output follow it and validate the target? Following a symlink out of .team-ship/ is a MAJOR finding.
A4. `stage-inputs 99` for a stage the manifest does not define must exit 2, not 0 and not 1.
A5. An artifact whose required heading appears only inside a code fence, not as a real heading. Must not count as present.

## Verify Task 8: run_gate.py

Scope: skills/team-gate/scripts/run_gate.py, skills/team-gate/scripts/fixtures/run_gate/.

Also check: the skip-is-failure rule is enforced by run_gate's own computed exit, quoted from the code, and never by trusting pytest's exit.

New adversarials:
A1. A fixture repository with two workflow files, one running tests and one running only lint. Which does discover pick, and does gates/discover.json record the source file and line? Picking the lint job as the authoritative test gate is a MAJOR finding.
A2. A pytest run that prints a summary of N passed but exits non-zero, for example a conftest that raises after the session finishes, or a plugin error. The real exit code must win over the parsed summary; run_gate must exit 1 and the gate file must record both.
A3. SECURITY. Inspect how the discovered command is executed. If it is passed to subprocess with shell=True, or joined into a string and passed to a shell, then a CI config containing metacharacters executes arbitrary content. Quote the subprocess call. shell=True with a discovered command is a BLOCK unless the command is tokenised with shlex and the tokens are validated against an allowlist of known tools.
A4. parity when a required tool is absent locally entirely. Exit 1 (mismatch) or 2 (cannot measure)? The brief does not say; report the behaviour and rule which is right, then check it is documented.
A5. coverage when pytest-cov is not installed: must write UNVERIFIED and exit 1, never 0. Confirm by running in an environment where the plugin is unavailable (a venv without it, or by temporarily masking it).
A6. The evidence subcommand: EVIDENCE.md's first line must be the generated-file header. Confirm HEAD recorded in EVIDENCE.json equals git rev-parse HEAD of the measured repository.

## Verify Task 9: prove_red.py

Scope: skills/team-gate/scripts/prove_red.py, skills/team-gate/scripts/fixtures/prove_red/.

Also check: the PLAN.md section 4 paragraph "Red for the right reason" is the authoritative classifier; confirm the code implements all five outcomes (valid-red-assertion, valid-red-missing-name, invalid-red, never-red, inseparable) and quote where each is decided.

New adversarials:
A1. A test function renamed between base and HEAD with no body change. Does enumerate treat it as new? If so, it does not exist at base; what classification results, and is that sensible? Report and rule.
A2. WORKTREE LEAK. Force a failure inside prove after the detached worktree is created (for example a test file that is unparseable at base). Then `git worktree list` in the fixture repository. Any leftover worktree is a BLOCK: the brief requires removal on every exit path. Repeat with a KeyboardInterrupt simulated by a timeout if you can.
A3. Mixed enumeration: one proper red-green test and one inseparable test in the same diff. Overall exit must be 0 with the inseparable entry marked UNVERIFIED, not 2, per the brief. Quote gates/9.json.
A4. AST hash stability: the same test function with only a comment changed, or only whitespace changed, between red-proof and HEAD. The hash must be unchanged. Then change only a string literal inside an assert; the hash must change. Quote how the AST is normalised.
A5. valid-red-missing-name: a test that imports a name from a module the diff MODIFIES but does not ADD (the module existed at base, the name did not). Is that classified valid or invalid? The brief says the missing name must resolve to a path the diff adds. Report the behaviour and rule whether a name added to an existing module should count; recommend and note it as a spec question for the brain.
A6. A test that fails at base with an AssertionError raised from a helper function outside the test body. The brief says the last frame must be inside the test body. Confirm it is classified invalid-red, and rule whether that is too strict.

## Verify Task 10: verify_independent.py

Scope: skills/team-gate/scripts/verify_independent.py, skills/team-gate/scripts/fixtures/verify_independent/.

Also check: the printed claude -p invocation includes a cwd set to the worktree, does not inherit the parent's model or API environment silently, and includes --strict-mcp-config with an empty mcpServers set so the verifier cannot reach the builder through a tool.

New adversarials:
A1. setup when verify-wt/ already exists from a prior crashed run. Must not fail with "already exists" and must not silently reuse a dirty worktree; report the behaviour and rule.
A2. compare when the two gate files record different HEAD SHAs. Comparing evidence from two commits is meaningless; must exit 1 naming the SHA mismatch, not 0.
A3. A repository where .team-ship/EVIDENCE.md is tracked AND .team-ship/ is listed in .gitignore. Ignore rules do not affect tracked files, so the checkout still contains it. setup must still exit 1 naming the tracked file.
A4. A repository where .team-ship/ is not tracked but a file .team-ship/RUN exists in the working tree only. The worktree at HEAD should not contain it; confirm setup exits 0 and the worktree has no .team-ship/.
A5. worktrees.json registration: after setup, quote the entry, then run gate_state verify-chain and confirm the worktree-registered receipt is present and the chain exits 0. After teardown, confirm the receipt for teardown is present.

## Verify Task 11: claim_evidence.py, render_evidence.py, render_approval.py, render_pr_body.py, claim-lexicon.json

Scope: those four scripts, skills/team-gate/references/claim-lexicon.json, skills/team-gate/scripts/fixtures/claim_evidence/.

Also check: claim_evidence check verifies the CONTENT of a cited EVIDENCE entry against the sentence, not merely that the [E<n>] tag exists. Construct a PR body whose [E1] tag points at a real entry that contradicts the sentence ("all tests pass" citing an entry with failed 2) and confirm exit 1.

New adversarials:
A1. A quantitative claim written in words: "seven hundred fifty-nine tests pass". Is it matched, flagged as unbacked, or silently accepted? Silent acceptance is a MAJOR finding; flagged-as-unverifiable is acceptable.
A2. render_evidence --check after a whitespace-only edit to EVIDENCE.md. Exit 1 or 0? Either is defensible; undocumented behaviour is a MINOR.
A3. render_pr_body with an override receipt whose reason text contains an HTML comment or a markdown link with a javascript: target. Is the override rendered verbatim as the brief requires, and if so is anything escaped? Rule whether verbatim-with-escaping is needed. This is a spec question for the brain; report, do not block.
A4. matrix with a requirement identifier present in PLAN.md that no gate file mentions: must grade NOT MET and exit 1. Then a requirement satisfied by two gates: must grade MET once, not twice.
A5. A sentence in the results section with two claims and one tag: "759 passed and coverage is 94% [E1]" where E1 backs only the first. Must flag the second.
A6. claim-lexicon.json: confirm it is valid JSON, that every token maps to a field that actually exists in the EVIDENCE.json schema (REVIEW-OPUS.md section B.2), and that the unbacked-word list contains at least the words the brief named.
