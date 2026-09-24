# Memory: decisions and dead ends

Not a diary. This records **decisions with the reason they were made** and **dead ends worth
not repeating**. If an hour was spent proving something wrong, the sentence that records it
saves the next agent that hour.

Newest first within each section. Update this file in the same PR that settles something.

---

## Decisions

### Rebase and merge for PR #196, not squash

**Decided:** 2026-09-18. **Reason:** the `main` ruleset sets `required_linear_history`, so a
merge commit is refused, and a squash would collapse 60 commits of one-verified-task-each into
a single blob and destroy the history the retrofit exists to produce. **Note for anyone
verifying a rebase merge:** GitHub replays commits and mints new SHAs, so testing whether your
head is an ancestor of `main` correctly returns false. Test content equality instead:
`git diff <your-head> upstream/main` must be empty. It was.

### The evolution loop may propose, never land

**Decided:** 2026-09-18, the owner's answer to the last open question in the PRD interview.
**Reason:** an unattended system that edits the repository that measures it has no natural
limit. Proposals only keeps every change explainable and reversible. This is a design
invariant of the loop, not a configuration value.

### The scheduled evolution cycle runs in dry-run only

**Reason:** CI holds no model credentials, and giving it some is a security decision rather
than a convenience. The consequence is stated plainly in the architecture: the real cycle is
not unattended, and it runs where credentials already exist.

### Persona generation enters the loop at validation, it does not fork it

**Reason:** personas have a schema and a validator; skills do not. One code path with two
profiles keeps the guard count at one. A second pipeline would mean a second place for the
count-coupling rule to be forgotten.

### Per-guard hook arming

**Decided:** 2026-09-18. **Reason:** the briefs for the three deny runs each needed exactly one
hook armed, and the implementation read a single run-wide flag from `run.json`, so arming
enforce armed three guards at once and the runs could not be isolated as written. The fix adds
`hooks.<guard>=observe|enforce` as an override that falls back to the run-wide value, with an
unrecognised key changing nothing so a typo cannot arm or disarm by accident.

### The rule that a document must not lie outranks brevity

**Reason:** `AGENTS.md` shipped naming six documents, five of which did not exist. The playbook
is explicit that an agent acting on a false document is worse off than an agent with no
document, because it is confident. The remedy is not to soften the routing table but to write
the documents.

### Punctuation: no em dash and no section sign, even inside quoted text

**Reason:** the owner's standing rule, and it outranks verbatim protection when quoting a
source that contains one. Measured and corrected: 21 instances were found in already-written
pipeline artifacts and replaced.

---

## Dead ends

### `sed -i ''` in a fixture generator

**Dead end:** BSD sed accepts `-i ''` for an in-place edit with no backup suffix. GNU sed reads
that as an empty script plus a file named after the substitution expression, and under `set -e`
the generator aborts. The suite passed for weeks on the machine it was written on and failed on
the first Linux CI run.
**Instead:** `sed 's/x/y/' f > f.new && mv f.new f`. Portable, no backup to clean up.

### Resolving tooling from an installed copy

**Dead end:** four fixtures resolved the arch-index scripts from `~/.claude/skills/arch-index`.
That path exists on a machine where the skill has been installed and does not exist on a fresh
checkout, so the fixtures returned "cannot find the tools" with a valid-looking exit code.
**Instead:** point the environment variable at the repository's own copy, the way the
run-aware half of the same file already did.

### A suite runner that discards the failing suite's output

**Dead end:** the runner ran each suite with output redirected to `/dev/null` and printed only
the exit code. Two red CI runs each reported one line, and each cost a full local reproduction
to learn what failed, which is worst when the failure only reproduces on the other platform.
**Instead:** capture each suite's output and print a bounded tail when it exits non-zero.

### `unittest.TestCase.debug()` as a test invocation mechanism

**Dead end:** on this Python, `debug()` is `setUp(); test(); tearDown()` with no `try` or
`finally`. `tearDown` is therefore skipped precisely when the test fails, which is the only
case where cleanup matters. The builder's own fixture could not see it because it only ran a
passing test.
**Instead:** call `setUp`, the test, and `tearDown` explicitly, with cleanup in a `finally`, and
add a fixture that fails the test and asserts from an on-disk log that cleanup still ran.

### `except Exception: pass` around a state read

**Dead end:** `find_run` swallowed an unreadable `.team-ship/RUN` marker and continued walking
up the tree, so a script silently resolved a different run than the one under its feet.
**Instead:** distinguish absence from unreadability. Absence walks up; unreadability fails
closed with exit 2 and names the path.

### A conditional expression used as a guard

**Dead end:** `segments != [...] if len(segments) == 2 else False` silently disabled the check
for every case where the length was not 2, which is every malformed path that mattered.
**Instead:** an explicit early return. Worth grepping for the shape `if ... if ... else` in any
validator.

### A copied fixture keeps the original absolute `repo_root`

**Dead end:** a test that copies a fixture and runs it gets repository-relative reads resolving
to the original repository, so it passes while testing the wrong tree. **Instead:** repoint
`repo_root` in the copy, or resolve the recorded root against the run directory.

### A fixture generator that commits before it initialises a repository

**Dead end:** `make_fixtures.sh` ran `git commit` before `git init` in the fixture directory, so
five commits landed in the enclosing worktree. The tree was clean but the history was not, and
the fix required a history rewrite before the PR could be opened.
**Instead:** `git init` inside the fixture directory first, and check `git log --oneline -15`
after any agent that generates git fixtures.

### Two-level fixture build directories and a one-segment ignore glob

**Dead end:** `.gitignore` had `fixtures/*/_build/`, which misses
`fixtures/<script>/<fixture>/_build/`. Build output was staged and committed by accident.
**Instead:** `fixtures/**/_build/`. Use `**` in ignore globs.

### Stale bytecode across a checkout

**Dead end:** running a test at HEAD and then again after checking out an older revision inside
the same filesystem timestamp tick lets Python read back the newer `__pycache__` as current, so
a valid red silently executes the green bytecode and the proof is worthless.
**Instead:** run every measured subprocess with `PYTHONDONTWRITEBYTECODE=1`.

### Editing a gate file in place to test a verifier

**Dead end:** a gate file is pinned by hash in its receipt, so hand-editing it breaks the chain
by design and the probe measures the tamper detection rather than the behaviour under test.
**Instead:** rewrite the receipt alongside the file, or drive a real run.

### Trusting a case-insensitive filesystem when checking a filename

**Dead end:** macOS resolves `.github/pull_request_template.md` to
`.github/PULL_REQUEST_TEMPLATE.md`, so a shell test for the lowercase path succeeds while git
tracks the uppercase name and the audit, which reads `git ls-files`, reports the file missing.
**Instead:** check the tracked name (`git ls-files`), not the path the filesystem happens to
resolve.

### Assuming untracked means absent to a checker

**Dead end:** `.metagpt/STATE.md` and `GATE.json` existed on disk and still read as missing,
because the audit reads tracked files only. **Instead:** commit what the audit is looking for.

### An audit table is a map of the gap, not a work order

**Dead end:** the playbook's own summary table was stale within a day: it listed `coco` as
missing the PR template and `AGENTS.md`, both of which had landed in the meantime.
**Instead:** run `repo-check` and read its output. It is the authority; the table is a snapshot.
