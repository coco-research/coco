# Signal sources

What `scripts/observe.py` reads, what it deliberately ignores, and why the honest answer to
"how do you know a skill is being used" is narrower than it sounds.

## What it reads

| Source | Where | What it yields | Travels? |
| --- | --- | --- | --- |
| Observation log | `~/.local/share/task-observer/skill-observations/observation-log/` | Skill ids that were invoked, with timestamps | No, it is local to one machine |
| Git window | `git log --since=<window> -- skills/ systems/` | Which skills were edited, by whom, and how often | Yes, it is the commits |
| Gate receipts | The team-gate run directory (`receipts.jsonl`) | Which stages ran, what was denied, what was overridden | No, run state is never committed |
| Count drift | `docs/asset-counts.json` against the tree | Whether a published number disagrees with reality | Yes |

`observe.py` writes one `signals/<cycle>.json` per cycle, pinned to the resolved HEAD so a
proposal can cite a line that still exists when a human reads it. It makes no model call and
it is deterministic: the same window and the same pinned commit produce byte identical output,
which is a test case rather than an aspiration.

## What it deliberately does not read

- **No telemetry, no network, no analytics.** Nothing leaves the machine to produce a signal,
  and the loop installs nothing that would report anything.
- **No conversation content.** The observation log records that a skill was invoked, not what
  was asked or answered. A proposal is about the skill's trigger wording, not about anyone's
  work.
- **No secrets, no credentials, no environment dumps.**
- **Not the gate receipts of another machine.** They are local by design; a cycle that needs a
  signal from another machine consumes a committed extract instead, which is why `signals/` is
  tracked and the run state is not.

## The known weakness

The strongest source, the observation log, exists only on the machine where work happened. A
cycle run anywhere else sees a thinner signal: the git window and the count drift, both of
which are about the repository rather than about use.

Two consequences, both deliberate:

1. A thin signal produces cosmetic proposals, which is why the caps in `lanes.json` exist and
   why the guard refuses a proposal whose evidence is a single weak citation.
2. The scheduled CI job runs in `--dry-run` for the same reason it holds no credentials: an
   unattended cycle on this machine would see the repository and not its use, and would
   propose accordingly.

The next improvement, when someone takes it, is to have the observation step run wherever the
work happens and commit a small extract into `signals/`, so the proposal step has real signal
on any machine. Until then, the honest description of this pipeline is: good at drift and
stale documentation, weak at knowing how a skill is actually reached for.
