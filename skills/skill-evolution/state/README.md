# state/

The committed memory of the evolution loop. Everything a cycle produces that a human needs to
read later lives here. Run state, by contrast, lives under the team-gate run directory and is
never committed.

## Files

| File | Written by | Contents |
| --- | --- | --- |
| `ledger.jsonl` | `scripts/ledger.py` | Append only. One JSON record per event. Created on the first write rather than committed empty, because an empty file is indistinguishable from a file nobody filled in. |
| `CYCLE.md` | `scripts/render_cycle.py` | The human artifact for the most recent cycle: what the signal showed, what was proposed, what the guard refused and why, and what the owner decided. |

## The ledger

One record per event, newest last. The fields:

```json
{"cycle": "2026-10", "proposal": "2026-10-3", "action": "proposed|merged|rejected",
 "reason": "why, in the words of whoever decided", "by": "loop|owner",
 "diff_sha256": "<hash of the patch>", "head_sha": "<commit>", "at": "<iso8601>"}
```

**The entries that matter most are the rejections.** `rejected_recent()` reads them, and a diff
whose hash was rejected inside the previous two cycles is not proposed again. That is the only
mechanism stopping the loop from arguing the same case every month, so a rejection without a
reason is a defect: the next cycle will not know what was wrong with it.

## Why the ledger is committed

It has to travel. A rejected proposal on one machine must stay rejected on another, and the
history of what the loop tried is part of the repository's memory in the sense `docs/memory.md`
means. Signals and proposals are committed for the same reason; gate receipts and run
directories are not, because they describe one run on one machine.
