<purpose>
Edit any field of an existing phase in ROADMAP.md in place. The phase number and position are always preserved. Guarded against in-progress and completed phases unless --force is passed. Validates depends_on references before writing. Shows a diff and requests confirmation before writing.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse the command arguments:
- First argument: phase number to edit (integer or decimal)
- Optional flag: --force (allow editing in_progress/completed phases)

Examples:
  `/gsd-edit-phase 5`       → phase = 5, force = false
  `/gsd-edit-phase 5 --force` → phase = 5, force = true
  `/gsd-edit-phase 12.1`    → phase = 12.1, force = false

If no argument provided:

```
ERROR: Phase number required
Usage: /gsd-edit-phase <phase-number> [--force]
Example: /gsd-edit-phase 5
Example: /gsd-edit-phase 5 --force
```

Exit.
</step>

<step name="init_context">
Load phase operation context:

```bash
INIT=$(gsd-sdk query init.phase-op "${target}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Check `roadmap_exists` from init JSON. If false:
```
ERROR: No roadmap found (.planning/ROADMAP.md)
Run /gsd:new-project to initialize.
```
Exit.
</step>

<step name="load_phase">
Read the current phase section from ROADMAP.md:

```bash
PHASE_DATA=$(gsd-sdk query roadmap get-phase "${target}")
```
