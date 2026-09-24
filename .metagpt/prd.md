# PRD: self-evolution loop, gate close-out, persona scale

Stage `prd`, written 2026-09-18. Owner: Rijul Kalra. Status: awaiting approval.
Ground truth for the repo state: `.metagpt/INDEX.md`, `STATE.md`, and the handoff bundle
at `skills/team-gate/handoff/` on branch `feat/team-gate-retrofit`.

---

## 1. Intent

coco's product is its instructions: 226 skills, 44 shipped commands, 35 agents and 495
personas, all markdown, all edited by hand. They improve only when a person sits down to
improve them, and nothing measures whether a skill's trigger wording still matches how
people actually invoke it. This work builds the opposite: a self-evolution loop that
observes how the skills and personas are used, proposes evidence-backed edits on a 30-day
cycle, and lands nothing without the owner's merge. Alongside it, the team-gate retrofit
that PR #196 carries is closed out, so the discipline that certifies work in this repo is
enforced by machinery rather than described in prose, and the persona roster grows toward
a thousand entries through bulk generation that still passes every count gate.

## 2. Scope

**In scope**

- A self-evolution loop for skills: observation, proposal, evidence, PR. Proposals only.
- The same loop extended to personas, after the skill half has run at least one cycle.
- Persona scale: bulk generation toward 1000 personas, with the roster validator and the
  published count gates green at every step.
- Team-gate close-out: merge PR #196, run the three deny runs (tasks 16, 17 and 18) and
  record the transcripts, close the register follow-ups that block a clean finish.
- The remaining install surface the owner handed over: adapters, the 342 generated
  commands, and the drift between shipped state and published claims.

**Out of scope**

- Any auto-merge, at any confidence level. The owner's answer to Q4 is proposals only.
- Publishing to new registries. npm is done; this PRD does not revisit it.
- Changes to the model routing policy in `~/.pi/agent/pinned-models.json`.
- Hand-authoring SI content. The point is the loop, not a batch of new prose by me.
- Adding a service, daemon or database to the repo. The repo installs instructions; the
  loop must live within that shape (a skill, a script, a workflow) or not ship.

## 3. User stories

1. As the owner, I receive a pull request on a 30-day cycle that proposes changes to
   skills, each carrying the evidence that motivated it, so the product improves without
   me starting from a blank page.
2. As the owner, I can reject a proposal and have the reason recorded, so the next cycle
   does not re-propose the same rejected change.
3. As the owner, I can run the cycle on demand against one skill, so testing the loop does
   not cost a month.
4. As a coco user, the skills I install describe themselves the way people actually reach
   for them, because the trigger wording is revised from observed use.
5. As a maintainer, every proposal branch arrives green under the repo's own gates, so
   reviewing it means judging the change, not fixing the plumbing.
6. As a maintainer, adding personas in bulk keeps the ~12 count-coupled files consistent
   and every persona valid under `validate_roles.py` and the frontmatter lint.
7. As the owner, I can read a ledger of every proposal, its evidence, and its fate, so
   nothing is proposed or adopted invisibly.

## 4. Requirements

Testable. Each one names how it is checked.

**The loop**

1. A single entry point runs one cycle: `python3 <skill>/scripts/evolve.py run --window 30d`.
   Check: it exits 0 on a fixture repository with no model calls (`--dry-run`).
2. Every proposal cites its evidence by file and line, or by receipt id, and the citation
   resolves at the pinned commit. Check: a proposal whose citation does not resolve fails
   validation and exits 2.
3. Proposals are written to a branch and a PR. The loop never writes to `main` and never
   merges. Check: a fixture run asserts no commit lands on the default branch and the
   script contains no merge or push-to-main call path.
4. Given the same window and the same pinned commit, two runs produce byte-identical
   proposal files. Check: run twice, `diff -r` empty.
5. A rejected proposal is recorded with its reason, and the same diff is not proposed
   again within the next two cycles. Check: a fixture with a rejection ledger produces no
   repeat proposal.
6. Cycle size is bounded: at most N proposals, each under a diff-size cap, both configurable
   and both defaulted in one file. Check: a fixture with 40 candidates yields N proposals
   and a stated remainder.
7. The cycle records what it cost: model names, calls and tokens per proposal. Check: the
   ledger entry carries those fields.
8. A `status` subcommand prints the last cycle, the open proposals, and the ledger totals.
   Check: exit 0 with no run in flight.

**Edit surface for skills**

9. v1 proposals may change a skill's `description` frontmatter, its `references/` and its
   `SKILL.md` prose, and may add or remove example blocks. Check: an out-of-scope edit
   (a persona file, a command file, a count file) is refused by the same validation.
10. Every proposal branch passes `tests/check-asset-counts.sh`, the frontmatter lint and
    `scripts/build-index.py` with no diff. Check: a fixture proposal that moves a count
    without updating the coupled files fails.

**Personas, second half**

11. Bulk persona generation runs from a spec file (department, archetype, domain) and
    writes valid persona files. Check: the generator on a 5-persona fixture produces files
    that pass the frontmatter lint and the roster schema.
12. Scaling to 1000 keeps every gate green: `validate_roles.py`, `build_roster.py --check`,
    `check-asset-counts.sh`, and the persona counts in README, package.json, agents/README,
    docs/install.md, docs/INDEX.md, HOW-IT-WORKS.html and assets/og-image.svg.
    Check: after generation, `bash tests/check-asset-counts.sh` exits 0.
13. Every generated persona is labelled as an illustrative composite, matching the existing
    SI packs' DISCLAIMER convention. Check: a generated file carries the disclaimer line.

**Gate close-out**

14. Tasks 16, 17 and 18 each produce a transcript showing the deny with its reason, in a
    live `claude` session with an isolated `CLAUDE_CONFIG_DIR` inside a pilot repository,
    with exactly one guard armed per run. Check: the transcript and the receipts are
    quoted in the register row.
15. The register follow-ups that gate a clean finish are closed: 5c, 5e, 5f, 12c, 12d, 9b
    (23b and 27 may be deferred again, with a stated reason). Check: each row carries
    evidence or a dated deferral.

## 5. Success check

The work is done when all of these are true:

1. PR #196 is merged, and `skills/team-gate/scripts/run_fixtures.sh` reports 14/14 on the
   Linux CI runner as well as locally.
2. Three deny-run transcripts exist, one guard armed each time, with the reason visible.
3. One full evolution cycle has produced a real PR against this repository, with at least
   one proposal whose evidence the owner can check by hand, and the owner has merged or
   rejected it.
4. The ledger shows the proposal and its fate, and a second cycle does not repeat a
   rejected proposal.
5. The persona roster has grown with every gate green, and the count in
   `docs/asset-counts.json` matches every published claim.

The first two are close-out. The third is the real acceptance test: the loop is proven by
one honest cycle, not by its own test suite.

## 6. Open questions

1. **Where does the usage signal come from off this Mac?** The candidates are the local
   task-observer log at `~/.local/share/task-observer/` and the gate receipts, both of which
   exist only on the machine that ran the work. If the loop is to run in CI it needs a
   signal that travels, which probably means the observation step runs locally and the
   proposal step consumes a committed extract. Needs a decision.
2. **What pays for the model calls, and with what ceiling?** The bulk lanes are Grok and
   the free OpenRouter lane (rate limited, batch only). Is there a per-cycle budget the
   loop must stay under, and what happens when it hits it?
3. **Cadence mechanics.** A GitHub Action on a schedule, a local `launchd` job, or a
   manual trigger that the owner runs? CI has no model credentials today, and giving it
   some is a security decision, not a detail.
4. **Does persona evolution share the loop, or is it a second loop?** Personas have a
   schema and a validator, skills do not. One code path with two profiles is simpler; two
   paths are honest about the difference.
5. **How large may one proposal be?** A single-sentence wording fix and a rewritten
   `SKILL.md` are both "a proposal". The diff cap in requirement 6 needs a real number.
