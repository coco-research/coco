# Interview

Stage: `interview` - in progress. One question per turn. On lock: `intent` is set and
`interview` becomes `done`.

Context the questions are grounded in: this is the **coco** repo at `8fac7c0`. The
handoff from the previous agent is `skills/team-gate/handoff/HANDOFF.md` on
`origin/feat/team-gate-retrofit` (PR #196), and it defers tasks 16, 17 and 18.

---

## Q1 - What should this session lock as the intent?

Asked 2026-09-18, after the index completed and the handoff was located.

**Why this question first.** The handoff defines a specific, ordered queue of deferred
work, but its PR is red and the branch is behind `main`. Those are different intents with
different first steps, and doing the deferred tasks on a branch that cannot merge would
mean proving hooks that are not yet shippable.

Options put to the owner:

1. **Finish the deferred runs** - tasks 16, 17 and 18, each an isolated run started with
   `gate_state.py start . fix hooks=enforce`, one deliberate violation, and the deny
   visible in the transcript. Then 23b, 27 and the follow-ups 5c/5e/5f/9b/12c/12d.
2. **Get PR #196 green and merged first** - the CI fix is already reported, then rebase on
   `origin/main`, verify the 14/14 proof on a clean checkout, and only then the deferred
   tasks.
3. **Neither yet** - set the retrofit aside and interview about the repo's vision and what
   to build next.

**A:** answered by the owner's own scope for this session, 2026-09-18: learn the repo as
the brain, then finish the work the previous agent deferred in the handoff (the step-18
deny runs and the follow-ups), and interview in the same pass about the repo's vision and
what should be built next. Not a clean pick from the three options; it is 1 plus 3, with
the order fixed by the owner: learn, then execute the deferred work, then the vision
interview.

---

## Q2 (part of the vision interview) - the step-18 deny runs have a design gap. Which way?

Asked 2026-09-18, after the index, the handoff bundle and three repo surveys.

**Why this question now.** Tasks 16, 17 and 18 are the "one deliberate violation, one
deny visible in the transcript" runs. The briefs (WAVE4-HOOKS-BRIEF.md:49) describe
flipping enforce "for one hook", but `skills/team-gate/hooks/lib.js:81-95` reads a single
run-wide flag, `hooks = observe | enforce`, from run.json's flags. There is no per-hook
flag, so flipping enforce arms the artifact guard, the stage guard and the Stop guard at
the same time. The three deny runs therefore cannot be isolated as written. Two other
facts: `install.py --project` registers hooks against the session's start directory, so a
deny transcript needs a live `claude` session started inside the pilot repository with an
isolated CLAUDE_CONFIG_DIR; and `claude` 2.1.263 is present on this machine, so that is
possible here.

Options put to the owner:

1. **Add the per-hook enforce flag** (small change to lib.js and run.json), then run 16,
   17 and 18 one guard at a time exactly as the briefs intended.
2. **Keep the single run-wide flag**, do three separate runs, one violation each, and
   record that all three guards were armed every time.
3. **Defer the denies**, do the mechanical follow-ups that need no live session (5c, 5e,
   5f, 12c, 12d, 9b, 23b, 27) first.
4. **Park the retrofit** and interview on vision and what to build next.

**A:** *(pending)*

---

## Q3 - What should this repo be pushed toward next?

Asked 2026-09-18, after the CI work and the per-guard flag. Options offered: enforcement
by default, closing the gate gaps, skill discovery, reach and distribution, or a guided
walk-through instead.

**A:** the owner's answer, recorded as given. Several things at once. Skill discovery is
one. Distribution he has already handled: npm shipped yesterday, so what remains on that
thread is the adapters, the 342 generated commands and the rest of the install surface.
The priority is a **self-learning skill**: skills that evolve on their own on a
**30-day loop**, using concepts from GitHub repositories that already do this, and the
same loop should be able to evolve **personas**, not only skills. Second workstream:
**more personas**, scaling the roster toward a **thousand-persona list**, generated in
bulk. He named the bulk lanes as "Brock, OpenSix" agents, read here as Grok plus the
OpenRouter bulk lane; Astra still needs his explicit word each time under the model
policy. He said to start.

## Q4 - What may the self-evolution loop change on its own?

Asked 2026-09-18. This is the one decision the PRD cannot invent, because it sets the
blast radius of an unattended system.

Options put to the owner:

1. **Proposals only.** The loop opens a branch and a PR with proposed edits, with the
   evidence that motivated them. Nothing lands without a human merge. Safest, and the
   repo's existing gates already support it.
2. **Auto-merge narrow classes, propose the rest.** It may land low-risk changes on its
   own (wording, examples, references inside one skill) and must propose anything that
   touches a persona definition, a command file, the roster, or the count gates.
3. **Auto-merge anything a mechanical gate passes.** The gates decide: green means
   landed. Fastest, and the least reversible.
4. **Decide the boundary later.** Write the loop first, keep it in observe mode (records
   what it would have changed, changes nothing) for the first cycle, then set the rule
   from real evidence.

**A:** *(pending)*
