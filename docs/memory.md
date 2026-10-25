# Memory: decisions and dead ends

Not a diary. This records **decisions with the reason they were made** and **dead ends worth
not repeating**. If an hour was spent proving something wrong, the sentence that records it
saves the next agent that hour.

Newest first within each section. Update this file in the same PR that settles something.

---

## Decisions

### agent-qa uses a project-scoped MCP configuration

**Decided:** 2026-10-25, docs/agent-qa-mcp.
The catalog guide registers the server from an initialized application project so it reads that project's `agent-qa.config.yaml`.
The linked host setup guide supplies the long tool timeout and version-matched skills.
Coco provides the connector documentation; users install and configure the agent-qa runtime separately.

### The install plan names every path it writes

**Decided:** 2026-10-24, feat/install-manifest. **Reason:** Uninstall has to restore
byte-identical originals and must not touch Claude Code's own files. The claude-code
installer records every new directory, generated file, pristine backup, and the
manifest itself as `write` with a `kind` of `generated`, `manifest`, `backup`, or
`dir`. Ops stay `link`, `write`, `block`, and `skip`. `summary.paths` counts
link + write + block. `settings.json`, `settings.local.json`, `.credentials.json`,
and anything under `projects/` are refused. A pre-existing file is copied once to
`.coco/backup/<relative>` and that copy is never replaced. `CLAUDE.md.coco-bak` is
still rewritten on every change, because hermes shares `write-rules-block.sh`. A
symlink is replaced only when its text points into this checkout (dangling or not)
or exactly matches an older coco checkout path recorded in the previous manifest;
a dangling link that points elsewhere is a user link and is left in place. A
user's own link is `skip` with reason `user link, not replaced`. A pre-existing regular
file at a generated SI command path is coco's own only when the previous manifest
recorded a generated write there, or the file still ends with the generator footer
"Made with CoCo Super Intelligence."; anything else is `skip` with reason `user file,
not overwritten` and is never touched, and a replaced coco file's write record says
`"replaces":"previous coco file"`. `apply_generated` re-checks the plan when it runs,
the way `apply_link` always did: a path planned as new that exists by then is refused
with `appeared after the plan`, and a symlink that is no longer `link_is_ours()` is
refused with `became a user link after the plan`, so either refusal rolls back.
`managed_settings` is a sorted list of every org-managed source that exists:
`managed-settings.json`, `managed-mcp.json` and `managed-settings.d/*.json` in the
system directory, plus the macOS MDM plists for all users and for the current login.
Server-managed settings (delivered by the Claude service) can't be detected locally,
so `managed_settings: []` does not prove a machine is unmanaged.
A re-install carries `created`, `backup` and `replaced_link` forward from the previous
manifest, so the first install's facts survive; the pristine backup is what uninstall
trusts for the original bytes. The manifest record's
hash stays null, because the line is inside the file it would hash.

### Uninstall reads the directory's own git dir, and keeps local work

**Decided:** 2026-10-14, PR #342 review. **Reason:** `git -C dir` does not override
`GIT_DIR`. `config --get` and `remote get-url` then describe the inherited repo, while
`rev-parse --show-toplevel` still prints `dir`, so a toplevel comparison alone does not
catch a hook's `GIT_DIR`. Every guard git call drops only the variables that redirect
which repo or config git uses: `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`,
`GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`,
`GIT_NAMESPACE`, `GIT_CEILING_DIRECTORIES`, `GIT_DISCOVERY_ACROSS_FILESYSTEM`,
`GIT_CONFIG`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG_NOSYSTEM`,
`GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_COUNT`, and every `GIT_CONFIG_KEY_n` /
`GIT_CONFIG_VALUE_n`. `GIT_SSH_COMMAND`, `GIT_SSH`, `GIT_ASKPASS`,
`GIT_TERMINAL_PROMPT`, and proxy settings are kept. Untracked `si-commands/`
(the Codex adapter writes it into `~/.coco`) is excluded from the status check,
the same way `.update-check.json` is. A `.git`
file of `gitdir: <other>/.git` also reports itself as toplevel (git 2.55); it is refused
unless `--absolute-git-dir` is this directory's own `.git` or a linked worktree whose
`gitdir` file points back here. A real coco-research clone with uncommitted changes, a
stash, or commits reachable from HEAD or any branch that are not on a remote-tracking
ref or a tag is kept unless `--force`. Counting only `--branches` misses a commit made
on the detached pin; `--not --tags='v[0-9]*'` still lets a pristine release-tag checkout uninstall, while a commit the user tagged locally (`git tag wip`) still counts as local work. A local-work
git call that errors or exits non-zero (ENOBUFS, a null status, old git rejecting
`:(exclude)`) is treated as local work too: uninstall exits 2 unless `--force`.
`gitIn` allows 64 MiB of git output. Origin stays `config --get remote.origin.url`
(the raw stored value). An insteadOf alias is refused; the message says the origin
must be stored as a github.com/coco-research/coco URL.
`update` on the detached pin counts only tracked edits, stashes and commits: `~/.coco` holds
untracked Coco state (`knowledge/`, `sessions/`, `m0-token`), and the pin checkout runs without
`--force`, so git refuses to overwrite an untracked file instead of replacing it.

### The pack-content gate stores no blocked names

**Decided:** 2026-10-10. **Reason:** the spellings must not be recoverable from this public
repository. The previous encoding was reversible, so the spellings were still in the
repository. Unsalted sha256 of short names is brute-forceable, and a salt committed next
to the digests would not help. The gate stores nothing. At scan time it reads the list
from `COCO_PACK_CONTENT_NAMES` or gitignored `tests/pack-content-names.local`
(`COCO_PACK_CONTENT_NAMES` wins when it is non-empty). With neither, a local run
or a pull request prints a `::notice::` and skips only the internal-name rule.
The other rules still run. `--self-test` plants synthetic names so the comparison
still runs, and plants the real list when one of those sources is set.

**Updated:** 2026-10-14. Skipping everywhere would have turned the rule off on
merge, because CI has no names secret. The script now treats a missing list as
a hard error when `GITHUB_ACTIONS=true`, `GITHUB_REPOSITORY=coco-research/coco`,
`GITHUB_EVENT_NAME` is `push` or `workflow_dispatch`, and `GITHUB_REF` is
`refs/heads/main`. The workflow is not the check. CI passes the secret only to
that main scan. Every event whose ref is not main, including pull requests,
also runs the tree scan without the secret, so telemetry, curl|sh, and machine
paths still see that tree; the internal-name rule skips with a notice. Pull
requests do not receive the secret, because that step runs the PR's own script.
Hyphen windows stop at the longest loaded name, at least 1 part, computed once
per scan. A long chain stays linear in its length times that maximum. A fixed
cap of 4 missed a longer list entry inside a longer chain, and yielding the
whole chain did not cover that entry, so the whole chain is not yielded separately.

The old rot13 list is still on main and in history (main's `tests/check-pack-content.py`
has it now). This PR removes it from the tree but not from history. There is no history
rewrite.

### Persona answers use one attribution wording

**Decided:** 2026-10-05, legal policy. **Reason:** a persona answer was readable as the named
person. The label sentence and the report footer live in
`systems/superintelligence/templates/attribution.md`, and both command generators insert that
file. `tests/check-persona-attribution.py` fails if a generated command drops either sentence,
or if a generator template tells the model to write `<Name> says`. Removal is
`docs/personas/TAKEDOWN.md`, a placeholder until legal review replaces it.

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
