# PRD: coco

**What this repository is and why it exists.**

Owner: Rijul Kalra. Published as `cocosuperintelligence` (npm), with a Homebrew formula and
per-adapter installers. Site: `https://cocoresearch.org`.

Scope of this document: the **product**. A single feature's requirements live beside the
pipeline that produced them under `.metagpt/` (currently `.metagpt/prd.md` for the
self-evolution loop), and that file wins for anything it covers while the work is in flight.
This file wins for everything else.

---

## 1. The problem

An AI coding agent starts every session with nothing. It does not know how you review a PR,
what your release checklist is, which persona should judge a pricing decision, or that a
particular measurement was taken and a particular approach already failed. So it guesses, and
the guess is confident.

Teams work around this by pasting conventions into chat, or by writing one long context file
per repository that nobody maintains. Both approaches decay: the instructions live in the
wrong place, nothing versions them, and nothing checks that they still describe reality.

## 2. What coco is

A framework that **installs instructions**, not a service. Its product is markdown: skills,
slash commands, subagent definitions and behavioural rules, placed where each editor or CLI
looks for them. There is no application server, no database and no long running process in
the core. The shell and Python around it exist only to deliver the markdown and to prove the
markdown is consistent.

That inversion matters for every decision in this repository. Content is the product. The
installers are the delivery mechanism. A change that adds a capability adds a file, and a
change that ships nothing is a bug in an installer.

## 3. What it ships, as measured

These numbers are generated, not written by hand. `docs/asset-counts.json` is the source of
truth, produced by `python3 scripts/build-index.py`, and `bash tests/check-asset-counts.sh`
fails any published claim that disagrees with it.

| Asset | Count | Detail |
| --- | --- | --- |
| Skills | 227 | 75 core, 152 inside bundles |
| Commands | 386 | 44 shipped, 342 generated at install time across 7 namespaces |
| Agents | 35 | 11 core roles plus bundle agents |
| Rules | 15 | Cursor `.mdc` behavioural rules |
| Personas | 495 | Across 13 Super Intelligence departments |
| Adapters | 16 | One installer and manifest per target editor or CLI |
| Bundles | 9 | Opt-in trees: gsd, brain, cognee, hyperframes, superintelligence, m0, team, learning, reverse-skill |

Distribution: `npm install cocosuperintelligence`, a Homebrew formula pinned to a release
tarball, a root `install.sh` for a clone, and one adapter per target. The npm wrapper clones
the pinned tag rather than vendoring a copy, so a run and its record can always be traced to a
release.

## 4. Who it is for

Engineers and small teams who use AI coding agents daily and want a curated, versioned
capability library rather than a personal pile of prompts. Concretely, someone who:

- uses more than one agent surface, and wants the same conventions in all of them;
- wants judgement available on demand (a persona for a legal or finance question) without
  standing up a separate tool;
- cares that the library is consistent, because they have been burned by a stale instruction.

## 5. What it is not

Stated as deliberate exclusions, because each has been proposed and declined:

- **Not a service.** No hosted API, no daemon, no database. If a feature needs a server, it
  does not belong in the core.
- **Not a model or a wrapper around one.** No inference in the runtime path. Where a model is
  used, it is named and budgeted (see the evolution loop's lane file).
- **Not a prompt marketplace.** Bundles ship curated, reviewed content. Volume is not the
  goal; a skill nobody can find is the same as a skill that does not exist.
- **Not a build system.** It installs into an editor; it does not build the user's project.

## 6. In scope, in flight

One feature is being built against this PRD's constraints: a **self-evolution loop** that
observes how skills are used, proposes evidence-backed edits on a 30 day cycle, and lands
nothing without the owner's merge. Requirements, architecture and the task list are in
`.metagpt/prd.md`, `.metagpt/arch.md` and `.metagpt/plan.md`. Persona generation at scale
shares the loop's validation path rather than forking it.

## 7. How correctness is judged

The product claim is that the library is consistent and installable. That claim is checked
mechanically, not by review:

- `bash tests/check-asset-counts.sh` for every published number.
- `python3 scripts/build-index.py` regenerated with no diff, so the catalogs match the tree.
- `bash tests/check-command-refs.sh` for cross-references, `bash tests/check-evidence-gate.sh`
  for the pipeline's integrity language, `bash tests/check-roster-frontmatter.sh` and
  `python3 systems/team/validate_roles.py` for the roster.
- `python3 scripts/build-delivery-index.py`, which runs every installer into a throwaway HOME
  and records what each adapter really delivers rather than what its manifest claims.
- `bash tests/smoke.sh`, and `bash skills/team-gate/scripts/run_fixtures.sh` at 14/14.

The invariants behind those checks, each with the measurement that justifies it, are in
`docs/rules.md`. Which document is authoritative for what is in `AGENTS.md`.
