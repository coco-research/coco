# Rules

**The invariants. These do not change without the owner's explicit approval.**

Every rule here has a **measurement** behind it. They are not stylistic preferences; each
exists because breaking it caused a real, observed failure. Any PR that changes a rule in
this file must say so in its title.

Where a rule is mechanically enforced, the enforcer is named. Where it is only held by
discipline, that is stated too, because a rule that pretends to be enforced and is not is
worse than an honest convention.

---

## R1. The exit contract is three-valued, everywhere: 0 pass, 1 blocked, 2 unrunnable

**Enforced by:** every script under `skills/team-gate/scripts/` and `skills/skill-evolution/scripts/`.
`gate_state.py` defines the contract; `ship_gate.py` and `fix_gate.py` consume it; the four
hooks in `skills/team-gate/hooks/` always exit 0 and express a deny as JSON on stdout.

**Measured:** 14 fixture suites, one per script, are exercised by
`bash skills/team-gate/scripts/run_fixtures.sh`, which reports `14/14 passed` on the Linux CI
runner and on macOS. A regression probe over 19 CLI entry points returned exit 2 with a
single line and no traceback on every one.

**Why it matters:** 1 and 2 are not the same failure. `1` means "measured, and it failed".
`2` means "could not measure". Collapsing them lets an unmeasurable state masquerade as a
deliberate block, and a PR that should read UNVERIFIED reads BLOCKED instead.

**The failure that produced it:** `find_run` silently discarded an unreadable
`.team-ship/RUN` marker and kept walking up the tree, so scripts resolved a different run.
The first fix raised an exception, which made eight scripts traceback with exit 1, which is
exactly the collapse this rule forbids. The fix that held converts the exception to exit 2 in
every importer.

---

## R2. A document that lies is worse than no document

**Enforced by:** `repo-check` (the Tier 1 to 3 audit), which treats an empty placeholder and a
missing file as the same failure, and reads `git ls-files`, so a document that is not tracked
does not exist as far as the standard is concerned.

**Measured:** `AGENTS.md` landed in PR #198 naming six documents, five of which did not exist.
`repo-check` reports `THE SIX DOCUMENTS 1/8`, and `.metagpt/STATE.md` and `GATE.json` read as
missing while sitting on disk, because `.metagpt/` was untracked.

**Why it matters:** the next agent acts on the document. A routing table that points at
nothing does not fail loudly; it produces an agent that confidently does the wrong thing.

**Rule:** if a change makes a document wrong, fix the document in the same commit.

---

## R3. Gates live in the run directory. Human artifacts live in `.team-ship/`.

**Enforced by:** `gate_state.append_receipt` and `gate_state.verify_chain`, which resolve gate
files under the run directory returned by `find_run` and reject a path that escapes it.
`.team-ship/` is gitignored (`.gitignore:47`), so a clean checkout cannot carry a builder's
claim.

**Measured:** five of five first-round gate scripts wrote their gate files under
`<repo>/gates/` instead of the run directory, and `verify-chain` reported the chain intact
while seeing none of them. All five were rebuilt.

**Why it matters:** a gate file in the wrong place is invisible to the verifier and still
looks like evidence to a human reading the tree.

---

## R4. Every fixture is hermetic: no network, no model, no `$HOME`, no installed copy

**Enforced by:** the fixture suites themselves, and by the clean-checkout proof: run the
suite from a detached worktree so anything that depends on the developer's machine fails.

**Measured:** two consecutive CI failures on the same suite, both green on the macOS machine
where the work was built and red on the Linux runner. One was BSD `sed -i ''` in a fixture
generator, which GNU sed reads as an empty script plus a filename and aborts under `set -e`.
The other was four fixtures resolving the arch-index tools from `~/.claude/skills/arch-index`,
a path that exists on a machine where the skill has been installed and not on a fresh
checkout.

**Why it matters:** a suite that passes on one platform and fails on another turns every red
CI run into a debugging round trip, and trains people to distrust the suite.

---

## R5. Builders do not commit. One commit per verified task, and only on a verifier's PASS.

**Enforced by:** convention, plus `git log -1` and `git status --porcelain` read after every
builder returns. The `pre-push` gate and CI are the backstop for what lands.

**Measured:** two incidents. One builder committed `43c2627` after being told not to, sweeping
about forty unverified files from six other tasks into one commit with a non-conventional
subject. A second committed `3bd3e0b` with `--no-verify` to bypass the commit-msg check. Both
were undone with a mixed reset; nothing was pushed.

**Why it matters:** an unverified commit on a shared branch is indistinguishable from a
verified one to everyone downstream. The commit is the claim, so the claim has to be earned
before it is made.

---

## R6. A report without pasted output is not a report

**Enforced by:** convention. A builder return that paraphrases its results is sent back
unread with one line asking for the verbatim transcript.

**Measured:** a builder reported seven fixtures as passing, complete with expected exit codes,
for a script that had no `--self-test` argument at all and failed on every fixture with "run
directory not found". Nothing had ever run.

**Why it matters:** the difference between "I ran it and it passed" and the actual output is
the entire evidential value of the report. A paraphrase transmits the builder's belief, not
the machine's answer.

---

## R7. Counts are load bearing, and `docs/asset-counts.json` is the only source of truth

**Enforced by:** `tests/check-asset-counts.sh`, which runs `check-plugin-counts.py`,
`check-skills-commands-prose.py`, `check-persona-counts.py`, `check-site-counts.py`,
`check-adapter-list.py` and `check-si-counts.py`. `python3 scripts/build-index.py` regenerates
the truth; the CI step fails if the regenerated files differ from the committed ones.

**Measured:** 226 skills, 44 shipped commands plus 342 generated at install time (386 public),
35 agents, 15 rules, 495 personas across 13 departments, 16 adapters. Adding a single skill
moves published numbers in about a dozen hand written files, including `README.md`,
`package.json`, `.claude-plugin.json`, `index.html`, `coco/index.html`, `docs/install.md`,
`docs/INDEX.md`, `agents/README.md`, `assets/og-image.svg` and
`systems/superintelligence/HOW-IT-WORKS.html`.

**Why it matters:** the counts are the product's public claim. Nothing here is cosmetic; a
stale count is a false statement about what a user gets when they install.

---

## R8. No em dash and no section sign, in any artifact

**Enforced by:** convention, checked by eye at review. The rule outranks verbatim protection:
when quoting text that contains one, change the punctuation.

**Measured:** 21 em dashes were found in `.metagpt/INDEX.md` (13) and `.metagpt/interview.md`
(8) written after the rule was already in force, and replaced. The merged team-gate scripts
carry zero.

**Why it matters:** it is the owner's stated preference, applied to every artifact including
documentation and commit bodies. A rule that is followed only in the files anyone happens to
re-read is not a rule.

---

## R9. An override is recorded, not prevented. Stage 14's two final conditions are never overridable.

**Enforced by:** `ship_gate.py`. An `override` receipt naming a gate key or a stage number
clears that specific row and is listed in `gates/14.json` under `overrides`; a receipt that
matched nothing is listed under `unused_overrides`. `_evaluate_stage14` carries the docstring
"Never overridable".

**Measured:** in a live deny run, an `override 14:` prompt wrote the receipt
(`by=user`, instruction captured verbatim) and the gate still denied, listing the receipt as
unused. That is the designed behaviour: an override can carry a run past a red gate row, and
it can never manufacture the evidence artifact.

**Why it matters:** the moment an override can conjure the evidence, the evidence stops
meaning anything.

---

## R10. No credential reaches a tracked file, a log, or a commit message

**Enforced by:** the secret scan in `.githooks/pre-push`, and by `repo-check`'s credential
scan over tracked files.

**Measured:** 3,576 tracked files scanned, zero credentials in product code. Secrets are read
by path at runtime, never copied in. If one lands, remove it **and rotate it**; assume it is
already public.

**Why it matters:** this repository is public. A key in a commit is a key in the world, and
the commit history keeps it after the file is gone.

---

## R11. Model lanes are named in one file, budgeted before they are called, and the expensive lane needs the owner's word

**Enforced by:** `skills/skill-evolution/references/lanes.json` once the evolution loop lands.
Until then, by the model routing policy in `~/.pi/agent/AGENTS.md`, which pins five models and
forbids substitution or cross-model fallback.

**Measured:** the pinned set is five model ids across five vendors. A sixth vendor was
observed to return `MODEL_NOT_IN_PLAN` on every model, and a free overflow lane returned HTTP
429 on 5 of 8 rapid calls, which is why it is permitted for batch work only.

**Why it matters:** an unpinned lane drifts silently. The cost is not the money, it is that a
result produced by a different model than the one recorded is an unattributable result.
