# RESEARCH-BRIEF — /team:* enforcement retrofit

Stage 1 artifact. Everything below was verified by reading source or running commands on this machine on 2026-09-17. Nothing is inferred from documentation alone. Items an agent reported that I could not independently confirm are marked UNCONFIRMED.

## 1. The problem as stated by the owner

The /team:ship, /team:verify and /team:develop pipelines report success on work they have not verified. The owner invokes the colon-form commands directly. team.md is the shared foundation the others inherit roles and the 4-layer structure from.

## 2. Empirical evidence from seven real /team:ship runs on this machine

No run produced the complete artifact set that team:ship.md declares mandatory.

| Project | Present | Missing |
|---|---|---|
| GRC | EVIDENCE, PLAN, SHIP-REPORT | RESEARCH-BRIEF, ARCHITECTURE-OPTIONS, REVIEW-FINDINGS, ARCH-PLAN.json |
| coco-connect | RESEARCH, ARCH-OPTIONS, PLAN, REVIEW-FINDINGS, ARCH-PLAN.json, EVIDENCE | SHIP-REPORT |
| coco-hermes-text-vertical | RESEARCH, ARCH-OPTIONS, PLAN, REVIEW-FINDINGS, ARCH-PLAN.json, 4-layer briefs | EVIDENCE, SHIP-REPORT, ARCH-EVIDENCE, ARCH-PLAN-EVIDENCE |
| coco-connect-release, -hotfix | EVIDENCE, REVIEW-FINDINGS | PLAN, RESEARCH, ARCH-PLAN.json |
| coco-platform-OLD | PR_BODY only | everything |

GRC's SHIP-REPORT.md is honest: it labels Gate 9 UNVERIFIED and Gate 10 NOT MEASURED. It then records that the PR was opened on the stakeholder's instruction. team:ship.md permits PR-open only when Stages 7 to 13 are all GREEN. The prose gate yielded to a human instruction without recording that an override occurred. That is acceptable as a decision and unacceptable as a record.

coco-connect's EVIDENCE.md is 1,165 lines with 19 literal exit-code lines and sound methodology notes. The protocol produces good output when followed. The failure mode is inconsistent compliance with no detector, not universal non-compliance.

coco-hermes had ARCH-PLAN.json, so both architecture gates should have fired. Neither wrote evidence. The repository has no skills/ directory at its root, so the documented invocation cannot have resolved there.

## 3. Verified defects

D1. Every script invocation in the suite is a working-directory-relative path. Thirteen SCRIPT rows across the census reduce to four scripts: verify_arch_plan.py, validate_index.py, arch_drift.py, repo_tree.py. All four are installed at ~/.claude/skills/arch-index/scripts/ and run by absolute path. All four fail from any project without a skills/arch-index/scripts/ directory, which is every project except coco. These four are the only exit-code-based enforcement in the suite. Files carrying the defect: team:ship, team:verify, team:architecture, team:arch, team:reanalyse, team:toolkit.

D2. The artifact handoff chain is unchecked. 167 census rows (114 SEQUENCE plus 53 FILE) order stages and name artifacts. No test -f, exists(), or equivalent appears in any team file. The sentence "a stage that has not written its artifact has not completed" has no mechanism behind it. Section 2 shows the consequence.

D3. Five of team:ship's seven hard gates are prose: Stage 8 test execution, Stage 9 TDD red-green, Stage 10 coverage, Stage 11 independent verify, Stage 12 claim-versus-evidence, Stage 13 CI mirror. Only the two architecture gates invoke scripts, and those are the D1 scripts. Sixty-one RESULT rows in the census (exit codes, pass counts, coverage, versions) are all self-reported by the agent that did the work.

D4. Verify independence is void as written. team:ship.md Stage 11 and team:verify.md Layer 2 require verification from a clean checkout and forbid reading the builder's claims. .team-ship/ is not gitignored and is tracked in git in GRC (2 files) and coco-connect (3 files). A clean checkout therefore contains the builder's EVIDENCE.md and REVIEW-FINDINGS.md.

D5. No team file references a hook. Zero of 23. The harness's only unskippable enforcement primitive is unused by the suite that most needs it.

Also noted, not defects but relevant: team:roles.md is 154,053 of the suite's 267,352 characters. team.md mandates bypassPermissions for develop/fix/test/build agents at lines 246 and 418.

## 4. Census of normative statements (Phase 1, four Haiku extractors, rigid schema)

239 rows across 23 files (team:roles.md excluded as role definitions, not gates).

| Shape | Rows | Meaning |
|---|---|---|
| SEQUENCE | 114 | stage ordering, forbids proceeding until X |
| RESULT | 61 | asserts about a command outcome |
| FILE | 53 | asserts an artifact exists, is written, or is read |
| JUDGEMENT | 18 | requires a quality or severity assessment |
| ISOLATION | 14 | forbids an agent from seeing something |
| SCRIPT | 13 | invokes an external script (4 distinct, 0 reachable) |
| OTHER | 4 | |

Concentration by file: team 30, ship 28, architecture 27, verify 24, evidence 23, toolkit 22, arch 18, test 16, fix 15, develop 15, reanalyse 14. Content pipelines (present, communicate, think, scrape, review) carry 2 to 4 rows each.

Known extraction weakness: extractor A folded distinct rules into single rows (the Stage 11 isolation rule became part of a SEQUENCE row). Treat merged rows as multiple gates.

## 5. Harness substrate, verified

Hook events wired on this machine: PreToolUse, PostToolUse, SessionStart, Stop, PreCompact, Notification. A PreToolUse hook receives tool_name, tool_input, session_id, session_type, cwd as JSON on stdin. It blocks by printing {"decision":"block","reason":"..."} and exiting 2 (gsd-validate-commit.sh does this). The alternative output, hookSpecificOutput.additionalContext, only injects advisory text into the model's context and is not enforcement (gsd-workflow-guard.js does this and should not be treated as a blocking reference).

Five GSD hooks contain setTimeout(() => process.exit(0), 3000): a three-second stdin timeout that fails OPEN. This is in the hook's own source, not the harness, so a team hook simply does not include it. The owner's memory documents multi-second stalls on this machine from OneDrive and Defender activity, so a copied fail-open would open precisely under load.

UNCONFIRMED, decisive, dispatched to a documentation agent: whether the harness suppresses hook dispatch under bypassPermissions. Sonnet ruled out a self-disabling path in the two GSD hooks it read; it could not read the harness. If hooks do not fire under bypassPermissions, Option A is void for the build stages that team.md runs in that mode.

## 6. MetaGPT, for comparison (verified against ~/.metagpt/src)

Six Python-enforced mechanisms: subprocess.Popen actually runs the code after installing dependencies; a RunCode to DebugError to WriteCode repair loop; _observe() filtering on cause_by for deterministic handoff; fixed artifact paths; @retry(stop_after_attempt(6)) on parse failure; a budget check that raises. No hard gate requires tests to pass. Its enforcement holds because Python orchestrates and the model is a subroutine. The one idea worth taking is: execute in a subprocess and branch on the real exit code. Reimplementing MetaGPT as a Markdown skill would convert its mechanisms back into prose.

## 7. Adversarial review (Sonnet 5) — what survives red-teaming

Robustness ranking after countermeasures: prove_red with AST-hash binding, then clean worktree with gitignore plus fresh subprocess, then artifact existence with matcher "*", then run_gate/EVIDENCE.md, then claim-versus-evidence scan (weakest; no mechanical fix survives natural-language rephrasing). Hook plumbing and the bypassPermissions question cap all five.

Countermeasures that are fully mechanical and cheap: run_gate.py computes its own exit code and fails on skipped>0; bind EVIDENCE.md to git rev-parse HEAD at PR-open; only the wrapper may write EVIDENCE.md, hook blocks manual Edit/Write to that path; hash the test function's AST at red-proof and recheck at green; gitignore .team-ship/ and verify absence before the verifier starts; spawn the verifier as a fresh claude -p subprocess rather than an in-session subagent; do not copy the subagent exemption into blocking hooks.

Design principle that reorders the rest: check the persistent effect through PostToolUse state, not the invoking command string. A hook matching "pytest" is defeated by "make check"; a hook that reads the resulting file is not.

## 8. Scope boundary

Retrofit candidates: the team suite, the GSD suite, verification and code-review skills, task-observer. Knowledge skills (motion-doctrine, humanizer, diagram, and the like) must not be translated; there is nothing to enforce in knowledge.

## 9. Open for Stage 2

The fork (hooks as guards around the Markdown, versus Python orchestration with the model as subroutine), the per-gate mechanism table, and the substrate answers. Pending from the Fable, Opus and documentation agents.
