<purpose>

Interactive command center for managing a milestone from a single terminal. Shows a dashboard of all phases with visual status, dispatches discuss inline and plan/execute as background agents, and loops back to the dashboard after each action. Enables parallel phase work from one terminal.

</purpose>

<required_reading>

Read all files referenced by the invoking prompt's execution_context before starting.

</required_reading>

<process>

<step name="initialize" priority="first">

## 1. Initialize

Bootstrap via manager init:

```bash
INIT=$(gsd-sdk query init.manager)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Parse JSON for: `milestone_version`, `milestone_name`, `phase_count`, `completed_count`, `in_progress_count`, `phases`, `recommended_actions`, `all_complete`, `waiting_signal`, `manager_flags`, and the optional trio `queued_milestone_version`, `queued_milestone_name`, `queued_phases` (added in SDK fix `2495-2496-2497` — may be absent on older SDK versions, treat missing as empty).

`manager_flags` contains per-step passthrough flags from config:
- `manager_flags.discuss` — appended to `/gsd:discuss-phase` args (e.g. `"--auto --analyze"`)
- `manager_flags.plan` — appended to plan agent init command
- `manager_flags.execute` — appended to execute agent init command

These are empty strings by default. Set via: `gsd-sdk query config-set manager.flags.discuss "--auto --analyze"`

**If error:** Display the error message and exit.

Display startup banner:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► MANAGER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 {milestone_version} — {milestone_name}
 {phase_count} phases · {completed_count} complete

 ✓ Discuss → inline    ◆ Plan/Execute → background
 Dashboard auto-refreshes when background work is active.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Proceed to dashboard step.

</step>

<step name="dashboard">

## 2. Dashboard (Refresh Point)

**Every time this step is reached**, re-read state from disk to pick up changes from background agents:

```bash
INIT=$(gsd-sdk query init.manager)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Parse the full JSON. Build the dashboard display.

Build dashboard from JSON. Symbols: `✓` done, `◆` active, `○` pending, `·` queued. Progress bar: 20-char `█░`.

**Status mapping** (disk_status → D P E Status):

- `complete` → `✓ ✓ ✓` `✓ Complete`
- `partial` → `✓ ✓ ◆` `◆ Executing...`
- `planned` → `✓ ✓ ○` `○ Ready to execute`
- `discussed` → `✓ ○ ·` `○ Ready to plan`
- `researched` → `◆ · ·` `○ Ready to plan`
- `empty`/`no_directory` + `is_next_to_discuss` → `○ · ·` `○ Ready to discuss`
- `empty`/`no_directory` otherwise → `· · ·` `· Up next`
- If `is_active`, replace status icon with `◆` and append `(active)`

If any `is_active` phases, show: `◆ Background: {action} Phase {N}, ...` above grid.

Use `display_name` (not `name`) for the Phase column — it's pre-truncated to 20 chars with `…` if clipped. Pad all phase names to the same width for alignment.

Use `deps_display` from init JSON for the Deps column — shows which phases this phase depends on (e.g. `1,3`) or `—` for none.

Example output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ████████████░░░░░░░░ 60%  (3/5 phases)
 ◆ Background: Planning Phase 4
 | # | Phase                | Deps | D | P | E | Status              |
 |---|----------------------|------|---|---|---|---------------------|
 | 1 | Foundation           | —    | ✓ | ✓ | ✓ | ✓ Complete          |
 | 2 | API Layer            | 1    | ✓ | ✓ | ◆ | ◆ Executing (active)|
 | 3 | Auth System          | 1    | ✓ | ✓ | ○ | ○ Ready to execute  |
 | 4 | Dashboard UI & Set…  | 1,2  | ✓ | ◆ | · | ◆ Planning (active) |
 | 5 | Notifications        | —    | ○ | · | · | ○ Ready to discuss  |
 | 6 | Polish & Final Mail… | 1-5  | · | · | · | · Up next           |
```

**Queued section (next milestone preview):**

If `queued_phases` is present and non-empty, render a compact preview of the next milestone's phases directly below the main table. This surfaces upcoming work without cluttering the active-milestone grid. Skip this section entirely when `queued_phases` is empty or missing (e.g. the active milestone is the last one in the roadmap).

Use `queued_milestone_version` and `queued_milestone_name` for the header. Phases render without D/P/E columns since they aren't discussed yet — just number, name (pre-truncated `display_name`), dependencies (`deps_display`), and a fixed `· Queued` status. Phase-name padding should match the active-table column width for visual alignment.

Example:

```
 ───────────────────────────────────────────────────────────────
 ◆ Queued — {queued_milestone_version} {queued_milestone_name}  ({queued_phases.length} phases)
 ───────────────────────────────────────────────────────────────
 | # | Phase                | Deps | Status       |
 |---|----------------------|------|--------------|
 | 31| Email Logs           | —    | · Queued     |
 | 32| Today's Sheets       | 31   | · Queued     |
 | 33| Resend Backfill      | 31   | · Queued     |
 | 34| Business Day Audit   | 31   | · Queued     |
```

Queued phases are NOT eligible for the Continue action menu — they live in a future milestone and must wait for the current milestone to ship. The preview exists purely for situational awareness.

**Recommendations section:**

If `all_complete` is true:

```
╔══════════════════════════════════════════════════════════════╗
