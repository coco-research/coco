# Phase 5: Proactive Mode — Detailed Plan

**Date:** 2026-03-20
**Owner:** Rijul Kalra
**Status:** Planning
**Effort:** 3-5 days initial, then ongoing refinement
**Depends on:** Phase 1 (required), Phase 4 Intelligence Layer (recommended)

---

## 1. Goal

Make CoCo act without being asked — watching for file changes, email arrivals, and calendar events, then surfacing contextual suggestions that the user accepts or dismisses with a single keystroke.

---

## 2. Success Criteria

From ROADMAP.md, all must pass before Phase 5 ships:

- [ ] File watcher detects new/changed files in active project and suggests relevant actions ("New test file added. Run tests?")
- [ ] Email monitor (HxStore + attachment watcher) surfaces new emails with suggested actions ("Email from stakeholder re: API spec. Want me to summarize?")
- [ ] Proactive suggestions appear in a non-intrusive "suggestion bar" above the input — dismissed with Esc, accepted with Enter
- [ ] False positive rate < 20% (4 out of 5 suggestions are actually useful)
- [ ] All proactive actions require explicit confirmation before execution (never auto-execute writes)
- [ ] Calendar awareness: "Standup in 15 min. Want me to summarize today's commits for your update?"

---

## 3. Architecture

### 3.1 High-Level Data Flow

```
┌────────────────────────────────────────────────────────┐
│                   WATCHER LAYER                        │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │ File Watcher  │ │Email Monitor │ │Calendar Bridge│  │
│  │  (chokidar)   │ │(HxStore diff)│ │ (AppleScript) │  │
│  └──────┬───────┘ └──────┬───────┘ └──────┬────────┘  │
│         │                │                │            │
│         ▼                ▼                ▼            │
│  ┌─────────────────────────────────────────────────┐   │
│  │              TRIGGER ENGINE                      │   │
│  │  Watcher events → Rule matching → Raw triggers   │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                               │
│                        ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │            SUGGESTION RANKER                     │   │
│  │  Raw triggers → Confidence scoring → Dedup →     │   │
│  │  Rank by relevance → Filter by threshold         │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                               │
└────────────────────────┼───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                   UI LAYER                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │            SUGGESTION BAR                        │   │
│  │  "New test file added. Run tests?" [Enter/Esc]   │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │ (user accepts)                │
│                        ▼                               │
│            Orchestrator.handleInput(action)             │
└────────────────────────────────────────────────────────┘
```

### 3.2 Proactive Engine (src/core/proactive-engine.ts)

Central coordinator that:
1. Starts and stops all watchers based on user config
2. Receives raw events from watchers
3. Feeds events into the trigger engine
4. Passes scored triggers to the suggestion ranker
5. Emits the top suggestion to the UI via EventEmitter

The engine runs on a tick loop (every 5 seconds) to batch events and avoid flooding the UI. Only the highest-confidence suggestion is shown at any time; lower-priority ones queue behind it.

```
interface ProactiveEngineConfig {
  enabled: boolean;
  sensitivity: 'low' | 'medium' | 'high';  // maps to confidence thresholds
  watchPaths: string[];                      // explicit project dirs to monitor
  emailEnabled: boolean;
  calendarEnabled: boolean;
  maxSuggestionsPerMinute: number;           // throttle (default: 3)
}
```

Sensitivity thresholds:
- `low`: confidence >= 0.85 (only near-certain suggestions)
- `medium`: confidence >= 0.70 (default)
- `high`: confidence >= 0.50 (aggressive, more false positives)

### 3.3 Watchers

#### File Watcher (src/integrations/file-watcher.ts)

Uses `chokidar` (already a transitive dependency in the Node ecosystem) to watch the active project directory.

**Watched events:** `add`, `change`, `unlink` (file deleted)

**Ignore list (hardcoded + configurable):**
- `node_modules/`, `.git/`, `dist/`, `build/`, `.next/`, `__pycache__/`
- `*.log`, `*.lock`, `package-lock.json`, `yarn.lock`
- `.DS_Store`, `Thumbs.db`
- OneDrive temp files (`~$*`, `.tmp`)

**Debounce:** 500ms per file, 2000ms batch window (collect all changes in a 2s window, emit once).

**Event classification rules:**

| File Pattern | Event | Suggested Action | Confidence |
|---|---|---|---|
| `*.test.ts`, `*.spec.ts` added | add | "New test file. Run tests?" | 0.80 |
| `*.test.ts` changed | change | "Tests updated. Re-run?" | 0.70 |
| `src/**/*.ts` changed (>5 files) | batch change | "Bulk changes detected. Run review?" | 0.75 |
| `package.json` changed | change | "Dependencies changed. Run install?" | 0.85 |
| `CLAUDE.md` or `.claude/` changed | change | "Config updated. Reload skills?" | 0.90 |
| `*.md` added in `.planning/` | add | "New planning doc. Load GSD context?" | 0.80 |
| File deleted | unlink | (no suggestion — deletions are intentional) | — |
| `Dockerfile`, `docker-compose.yml` changed | change | "Container config changed. Rebuild?" | 0.75 |

#### Email Monitor (src/integrations/email-monitor.ts)

Wraps the existing `.sync/sync.sh` pattern documented in CLAUDE.md. Uses a hybrid approach:

**Primary: HxStore diff monitoring**
- Watch file: `~/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/HxStore.hxd`
- On modification time change (checked every 30 seconds via `fs.stat`, NOT chokidar — binary file changes too frequently):
  1. Run `strings` on the file, pipe through keyword grep
  2. Diff against `.last-hxstore-extract` saved from previous run
  3. New lines = new email content fragments
  4. Extract sender, subject fragments where possible

**Secondary: Attachment cache monitoring**
- Watch dir: `~/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Data/Files/S0/4/Attachments/0/`
- On new file: "New email attachment: <filename>. Summarize?"

**Tertiary: Manual drop folder**
- Watch a configurable project folder (default: `./inbox/` or `./emails/`)
- User drags `.eml` or `.msg` files here
- On new file: parse and suggest action

**Event classification rules:**

| Trigger | Suggested Action | Confidence |
|---|---|---|
| New HxStore content with project keywords | "New email mentioning <keyword>. Summarize?" | 0.70 |
| New attachment (PDF, DOCX, XLSX) | "New attachment: <filename>. Want me to read it?" | 0.80 |
| New attachment (image) | "New screenshot received. Analyze?" | 0.65 |
| Manual drop (.eml file) | "Email dropped. Summarize and extract action items?" | 0.90 |

**Graceful degradation:** If HxStore path does not exist or `strings` extraction fails (binary format changed by Outlook update), log a warning and fall back to attachment-only + manual-drop monitoring. Never crash.

#### Calendar Bridge (src/integrations/calendar-bridge.ts)

Reads macOS Calendar.app via AppleScript. Polled every 5 minutes (calendar events don't need sub-second latency).

**AppleScript approach:**
```
osascript -e '
tell application "Calendar"
  set now to current date
  set later to now + 60 * 60  -- next 60 minutes
  set results to {}
  repeat with cal in calendars
    repeat with evt in (every event of cal whose start date >= now and start date <= later)
      set end of results to (summary of evt & "|" & start date of evt as string)
    end repeat
  end repeat
  return results as string
end tell'
```

**Event classification rules:**

| Trigger | Suggested Action | Confidence |
|---|---|---|
| Meeting in 15 min, title contains "standup" or "daily" | "Standup in 15 min. Summarize today's commits?" | 0.85 |
| Meeting in 15 min, title contains "review" or "demo" | "Demo in 15 min. Run a quick /team review?" | 0.75 |
| Meeting in 15 min, generic | "Meeting '<title>' in 15 min." | 0.50 |
| Meeting in 5 min (any) | "Meeting starts in 5 min." | 0.40 (info only) |

### 3.4 Trigger Engine (src/core/trigger-engine.ts)

Rule-based engine that maps raw watcher events to candidate suggestions.

**Rule structure:**

```
interface TriggerRule {
  id: string;                         // e.g., "file:test-added"
  source: 'file' | 'email' | 'calendar';
  condition: (event: WatcherEvent) => boolean;
  action: string;                     // natural language suggestion text
  skillRoute: string;                 // e.g., "team-test", "team-review", "direct"
  baseConfidence: number;             // 0.0-1.0
  cooldownMs: number;                 // don't re-trigger within this window
}
```

**Rule matching flow:**
1. Receive watcher event
2. Iterate through rules for that source type
3. For each matching rule, produce a `RawTrigger` with base confidence
4. Pass to suggestion ranker for scoring adjustments

**Cooldown:** Each rule has a cooldown (default: 5 minutes for file rules, 30 minutes for email, 10 minutes for calendar). If a rule fired within its cooldown window, suppress the trigger. Prevents "run tests?" appearing every time a test file saves.

### 3.5 Suggestion Ranker (src/core/suggestion-ranker.ts)

Adjusts raw trigger confidence based on context, then filters and ranks.

**Scoring adjustments:**

| Factor | Adjustment |
|---|---|
| User accepted this suggestion type before | +0.10 |
| User dismissed this suggestion type 3+ times | -0.20 |
| Suggestion relates to currently running session | -0.15 (redundant) |
| Time of day: outside 9am-7pm | -0.10 (less likely to be useful) |
| File in a directory the user recently worked in | +0.10 |
| Multiple related file changes (batch) | +0.05 |

**Deduplication:** If two triggers suggest the same skill route within 10 seconds, merge into one (keep higher confidence).

**Output:** Ordered list of suggestions, filtered by the sensitivity threshold. Only the top suggestion is shown in the UI; the rest queue.

### 3.6 Suggestion Bar UI (src/ui/SuggestionBar.tsx)

Ink component that renders above the CommandInput, only when a suggestion is active.

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ CoCo | how-i-pm-with-ai (main) | 2 active | 14:32  │  ← StatusBar
├─────────────────────────────────────────────────────┤
│ [session panels...]                                  │  ← SessionPanel
├─────────────────────────────────────────────────────┤
│ * New test file added. Run tests? [Enter/Esc]        │  ← SuggestionBar (NEW)
├─────────────────────────────────────────────────────┤
│ > _                                                  │  ← CommandInput
└─────────────────────────────────────────────────────┘
```

**Behavior:**
- Appears with a subtle fade-in (dim text, then normal after 500ms)
- `Enter` = accept suggestion, dispatch to orchestrator
- `Esc` = dismiss suggestion, log dismissal for learning
- Auto-dismiss after 30 seconds of no interaction
- If the user starts typing in CommandInput, auto-dismiss (don't compete for attention)
- Shows at most 1 suggestion at a time
- Queued suggestions cycle in after current one is dismissed/accepted/expired
- Color: dim yellow text (non-intrusive, distinct from session output)

### 3.7 User Preference Learning (SQLite)

**New tables:**

```sql
-- Tracks user responses to proactive suggestions
CREATE TABLE IF NOT EXISTS suggestion_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_id       TEXT NOT NULL,          -- e.g., "file:test-added"
  source        TEXT NOT NULL,          -- "file" | "email" | "calendar"
  action_text   TEXT NOT NULL,          -- what was shown to user
  skill_route   TEXT NOT NULL,          -- what would be dispatched
  confidence    REAL NOT NULL,          -- final scored confidence
  outcome       TEXT NOT NULL,          -- "accepted" | "dismissed" | "expired" | "auto-dismissed"
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000)
);

CREATE INDEX IF NOT EXISTS idx_suggestion_log_rule ON suggestion_log(rule_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_log_outcome ON suggestion_log(outcome);

-- Aggregated user preferences (updated on each interaction)
CREATE TABLE IF NOT EXISTS suggestion_prefs (
  rule_id       TEXT PRIMARY KEY,
  accept_count  INTEGER NOT NULL DEFAULT 0,
  dismiss_count INTEGER NOT NULL DEFAULT 0,
  last_accepted INTEGER,               -- unix timestamp
  last_dismissed INTEGER,              -- unix timestamp
  confidence_adj REAL NOT NULL DEFAULT 0.0  -- computed from accept/dismiss ratio
);
```

**Learning algorithm:**
- After each suggestion outcome, update `suggestion_prefs` for that `rule_id`
- `confidence_adj = (accept_count - dismiss_count * 2) / (accept_count + dismiss_count + 1) * 0.2`
  - Capped at [-0.3, +0.2] to prevent runaway adjustment
  - Dismissals weigh 2x because false positives are more annoying than missed suggestions
- If `dismiss_count >= 10` and `accept_count == 0`, auto-disable that rule (log it, notify user once)
- User can reset preferences via `/proactive reset-prefs`

---

## 4. Task Breakdown

Tasks are ordered by dependency. Each task includes estimated effort and what it unblocks.

### Task 1: Proactive Engine Skeleton + Config
**Effort:** 0.5 day
**Dependencies:** None (Phase 1 orchestrator exists)
**Deliverables:**
- `src/core/proactive-engine.ts` — EventEmitter with start/stop, tick loop, config loading
- `src/core/trigger-engine.ts` — Rule registry, match loop, cooldown tracking
- `src/core/suggestion-ranker.ts` — Scoring pipeline, dedup, threshold filter
- SQLite migration for `suggestion_log` and `suggestion_prefs` tables
- New config keys in context table: `proactive_enabled`, `proactive_sensitivity`, `proactive_watch_paths`
- Meta-commands: `/proactive on|off`, `/proactive sensitivity low|medium|high`, `/proactive reset-prefs`

### Task 2: File Watcher
**Effort:** 0.5 day
**Dependencies:** Task 1
**Deliverables:**
- `src/integrations/file-watcher.ts` — chokidar setup, ignore list, debounce, event classification
- Add `chokidar` to `package.json` dependencies
- Trigger rules for all file patterns in section 3.3
- Unit tests: mock file events, verify correct triggers emitted

### Task 3: Email Monitor
**Effort:** 1 day
**Dependencies:** Task 1
**Deliverables:**
- `src/integrations/email-monitor.ts` — HxStore polling, strings extraction, diff logic, attachment watcher, manual drop folder
- Graceful degradation when HxStore path missing
- Trigger rules for email patterns in section 3.3
- Integration test: create mock attachment files, verify detection

### Task 4: Calendar Bridge
**Effort:** 0.5 day
**Dependencies:** Task 1
**Deliverables:**
- `src/integrations/calendar-bridge.ts` — AppleScript execution, event parsing, upcoming event detection
- Trigger rules for calendar patterns in section 3.3
- Fallback: if AppleScript fails (permissions denied), disable calendar bridge gracefully with a user-facing message

### Task 5: Suggestion Bar UI
**Effort:** 0.5 day
**Dependencies:** Task 1 (for suggestion events to render)
**Deliverables:**
- `src/ui/SuggestionBar.tsx` — Ink component, Enter/Esc handling, auto-dismiss timer
- Integration into `App.tsx` layout (above CommandInput)
- Wire SuggestionBar accept/dismiss events back to proactive engine for logging

### Task 6: Orchestrator Integration
**Effort:** 0.5 day
**Dependencies:** Tasks 1-5
**Deliverables:**
- Wire proactive engine into `Orchestrator` constructor via the existing `OrchestratorDeps` options pattern
- Add `proactiveEngine?: ProactiveEngine` to `OrchestratorDeps`
- On suggestion accept: call `orchestrator.handleInput(suggestion.skillRoute + " " + suggestion.args)`
- On suggestion dismiss: log to `suggestion_log`, update `suggestion_prefs`
- Startup: auto-enable proactive mode if `proactive_enabled` is `true` in context table
- Shutdown: stop all watchers cleanly

### Task 7: Preference Learning + Tuning
**Effort:** 0.5 day
**Dependencies:** Task 6 (needs real accept/dismiss data flowing)
**Deliverables:**
- Implement learning algorithm in suggestion ranker
- Auto-disable rules with 10+ dismissals and 0 accepts
- `/proactive stats` command showing acceptance rates per rule
- Initial confidence tuning pass based on manual testing

### Task 8: End-to-End Testing + False Positive Audit
**Effort:** 0.5 day
**Dependencies:** All above
**Deliverables:**
- Scenario test: change 5 files, verify <= 1 false positive suggestion
- Scenario test: drop an email attachment, verify suggestion appears within 30s
- Scenario test: calendar event approaching, verify suggestion 15 min before
- Measure false positive rate across 20 scripted scenarios, target < 20%
- Performance test: file watcher on a 10K-file repo, verify < 50MB memory overhead

---

## 5. Integration with Existing Systems

### 5.1 Orchestrator

The proactive engine plugs in via the existing `OrchestratorDeps` options-object pattern (established in Phase 1, extended in Phase 2 for SessionManager, Phase 3 for VoiceManager):

```
// orchestrator.ts — extend OrchestratorDeps
export interface OrchestratorDeps {
  state: StateManager;
  skills: SkillRegistry;
  sessionManager?: SessionManager;    // Phase 2
  taskQueue?: TaskQueue;              // Phase 2
  voiceManager?: unknown;             // Phase 3
  proactiveEngine?: ProactiveEngine;  // Phase 5 (NEW)
}
```

When a suggestion is accepted, the proactive engine calls `orchestrator.handleInput()` — the same entry point used by keyboard input and voice transcription. This means all existing intent classification, skill routing, confirmation prompts, and concurrency gating apply automatically. Proactive mode adds no special dispatch path.

### 5.2 Session Manager

Proactive suggestions that trigger skill dispatch go through the normal SessionManager.spawn() flow. If at concurrency limit, the task queues automatically via p-queue. The user sees "Queued: /team test (from suggestion)" — making it clear the suggestion originated from proactive mode.

### 5.3 Voice

When voice is active and a suggestion appears:
- Speaker reads the suggestion text aloud: "New test file added. Run tests?"
- User can respond verbally: "yes" or "no" (routed through voice transcription -> orchestrator)
- This requires a small addition to intent classification: recognize "yes"/"no" in the context of an active suggestion

### 5.4 State Manager

New tables (`suggestion_log`, `suggestion_prefs`) follow the existing StateManager pattern. Add methods:
- `logSuggestion(ruleId, source, actionText, skillRoute, confidence, outcome)`
- `getSuggestionPrefs(ruleId)`
- `updateSuggestionPrefs(ruleId, outcome)`
- `getSuggestionStats()` — for `/proactive stats`

### 5.5 Skill Registry

File watcher and email monitor use the skill registry to validate that suggested skill routes actually exist. If a trigger rule references `team-test` but the skill is not loaded, the trigger is suppressed (log a warning, don't show the user a broken suggestion).

---

## 6. Privacy and Safety

### 6.1 Core Principle: Suggest, Never Act

All proactive suggestions require explicit user confirmation (Enter key or verbal "yes") before any action executes. There is no auto-execute path. This is enforced at the architecture level: the proactive engine emits suggestion events, never calls `orchestrator.handleInput()` directly.

### 6.2 Watch Path Boundaries

- File watcher ONLY monitors paths listed in `proactive_watch_paths` config (defaults to current working directory)
- Email monitor ONLY reads the specific HxStore path and attachment cache directory documented in CLAUDE.md
- Calendar bridge ONLY reads event titles and start times — no attendee lists, no meeting notes, no email bodies
- No watcher ever scans `/`, home directory root, or any path not explicitly configured

### 6.3 Data Handling

- HxStore `strings` extraction is ephemeral — diffed in memory, only new fragments stored temporarily
- Email content fragments are never persisted to SQLite; only the suggestion text is logged
- Attachment filenames are logged in `suggestion_log` but file contents are not read until the user accepts the suggestion
- All `suggestion_log` entries are pruned after 30 days (same as event log)

### 6.4 Write Operation Safety

If a proactive suggestion routes to a write operation (e.g., "Dependencies changed. Run install?"), the normal orchestrator write-confirmation flow applies. The user sees TWO confirmations:
1. Accept the suggestion (Enter on suggestion bar)
2. Confirm the write operation (orchestrator's existing isWriteOperation check)

### 6.5 Disabling Proactive Mode

- `/proactive off` immediately stops all watchers and clears the suggestion queue
- Setting persists across restarts (stored in context table)
- Individual sources can be disabled: `/proactive email off`, `/proactive calendar off`

---

## 7. Test Plan

### 7.1 Unit Tests

| Test | What It Validates |
|---|---|
| Trigger engine matches rules correctly | Rule conditions fire on expected events, skip on non-matching |
| Cooldown suppresses repeated triggers | Same rule doesn't fire within cooldown window |
| Suggestion ranker applies scoring adjustments | Accept/dismiss history modifies confidence correctly |
| Suggestion ranker deduplicates | Two triggers for same skill within 10s merge into one |
| Threshold filtering by sensitivity | `low` filters more aggressively than `high` |
| Auto-disable rule after 10 dismissals | Rule stops firing, user is notified |

### 7.2 Integration Tests

| Test | What It Validates |
|---|---|
| File add -> trigger -> suggestion bar shows | End-to-end file watcher pipeline |
| Suggestion accept -> orchestrator dispatches | Enter key triggers skill execution |
| Suggestion dismiss -> logged and learning updated | Esc key updates suggestion_prefs |
| Email attachment drop -> suggestion within 30s | Email monitor latency |
| Calendar event approaching -> suggestion at 15 min | Calendar bridge timing |
| Proactive off -> no suggestions appear | Kill switch works |

### 7.3 False Positive Audit

Run 20 scripted scenarios and measure:

| Scenario | Expected Suggestion | False Positive? |
|---|---|---|
| Add a new `.test.ts` file | "Run tests?" | No |
| Save a `.ts` file (normal edit) | None | If any: Yes |
| Save 6+ `.ts` files quickly | "Run review?" | No |
| Edit `package.json` (add dep) | "Run install?" | No |
| Edit `package.json` (change script) | "Run install?" | Borderline |
| Git pull brings new files | None (git operations are noise) | If any: Yes |
| OneDrive sync creates temp `~$file` | None | If any: Yes |
| New PDF in attachment cache | "Summarize attachment?" | No |
| Outlook reindexes HxStore (no new email) | None | If any: Yes |
| Calendar: standup in 15 min | "Summarize commits?" | No |
| Calendar: lunch break in 15 min | None (low confidence, filtered) | If any: Yes |

**Target:** <= 4 false positives out of 20 scenarios (< 20% rate).

### 7.4 Performance Tests

| Test | Pass Criteria |
|---|---|
| File watcher on 10K-file repo | Memory delta < 50MB, CPU < 5% idle |
| HxStore polling every 30s | CPU < 1% when no changes |
| 3 concurrent sessions + proactive mode | Total memory < 600MB |
| Suggestion bar render/dismiss cycle | No visible UI flicker |

---

## 8. Risks and Mitigations

### 8.1 macOS Sequoia Permissions

**Risk:** macOS 15 (Sequoia) tightened permissions for AppleScript automation and file access. Calendar.app access requires explicit TCC (Transparency, Consent, and Control) approval. The terminal running CoCo needs "Automation" permission for Calendar and possibly "Full Disk Access" for HxStore.

**Mitigation:**
- On first Calendar bridge attempt, catch the AppleScript permission error and display: "CoCo needs Calendar access. Go to System Settings > Privacy > Automation and enable Calendar for Terminal/iTerm."
- For HxStore: if `fs.stat` fails with EACCES, suggest adding the terminal app to "Full Disk Access" in System Settings.
- All three watchers degrade gracefully — if permissions are denied, that watcher is disabled with a one-time warning, and the others continue.

### 8.2 HxStore Binary Format Changes

**Risk:** Microsoft may change the HxStore.hxd binary format in any Outlook update, breaking `strings` extraction.

**Mitigation:**
- HxStore extraction is a best-effort signal, not a guaranteed pipeline. The `strings` approach extracts printable UTF-8 sequences regardless of internal structure — it is format-agnostic.
- If extraction produces zero diff lines for 7+ days while the user is clearly receiving email, log a warning: "Email monitoring may be broken. Try `/proactive email reset`."
- Attachment cache monitoring (`fs.watch` on the Attachments directory) is independent of HxStore format and provides a reliable fallback.
- Manual drop folder is always available as a last resort.

### 8.3 OneDrive Sync Conflicts with SQLite

**Risk:** CoCo's `coco.db` lives in the project directory, which may be inside a OneDrive-synced folder. OneDrive's sync engine can conflict with SQLite's lock file, causing "database is locked" or corruption.

**Mitigation:**
- Store `coco.db` outside the OneDrive folder: default to `~/.local/share/coco/coco.db` (XDG-compliant, never synced).
- If the current location is inside a OneDrive path (detect by checking if cwd contains `OneDrive` or `Library/CloudStorage`), log a warning on startup and suggest relocating the DB.
- Enable WAL mode (`PRAGMA journal_mode=WAL`) which is more resilient to filesystem-level conflicts than the default rollback journal.
- If database lock errors occur at runtime, retry with 3 attempts and 500ms backoff before surfacing the error.

### 8.4 Notification Fatigue

**Risk:** Too many suggestions make CoCo annoying and the user disables proactive mode entirely.

**Mitigation:**
- Default sensitivity is `medium` (confidence >= 0.70), which is conservative.
- Hard throttle: maximum 3 suggestions per minute, regardless of how many events fire.
- Auto-dismiss after 30 seconds reduces pile-up.
- Learning loop actively suppresses rules the user consistently dismisses.
- Start with file watcher only; email and calendar are opt-in (`/proactive email on`, `/proactive calendar on`).

### 8.5 File Watcher Performance on Large Repos

**Risk:** Watching a monorepo with 50K+ files causes high CPU and memory usage from chokidar.

**Mitigation:**
- Use `chokidar` with `ignored` patterns for `node_modules`, `.git`, `dist`, `build`, and other heavy directories.
- Set `depth: 5` to avoid watching deeply nested directories.
- Use `usePolling: false` (native FSEvents on macOS) — efficient and low overhead.
- If watching more than 2 directories, use `awaitWriteFinish: { stabilityThreshold: 500 }` to reduce event churn from in-progress writes.
- Monitor chokidar's memory footprint on startup; if > 100MB, warn and suggest narrowing `proactive_watch_paths`.

### 8.6 AppleScript Calendar Access Latency

**Risk:** AppleScript calls to Calendar.app can take 2-5 seconds, especially with many calendars.

**Mitigation:**
- Calendar polling runs on a 5-minute interval in a background timer, never blocking the main event loop.
- Use `execFile` with a 10-second timeout; if it times out, skip that poll cycle.
- Cache the last result and only process diffs (new events or events whose start time has moved into the 60-minute lookahead window).

---

## 9. New Meta-Commands

| Command | Description |
|---|---|
| `/proactive on` | Enable proactive mode (starts all configured watchers) |
| `/proactive off` | Disable proactive mode (stops all watchers, clears suggestion queue) |
| `/proactive sensitivity low\|medium\|high` | Set suggestion confidence threshold |
| `/proactive email on\|off` | Enable/disable email monitoring |
| `/proactive calendar on\|off` | Enable/disable calendar bridge |
| `/proactive stats` | Show acceptance rates per rule, total suggestions, false positive estimate |
| `/proactive reset-prefs` | Reset all learned preferences (start fresh) |

---

## 10. New Dependencies

| Package | Purpose | Size |
|---|---|---|
| `chokidar` | File system watching with debounce and ignore | ~30KB |

No other new packages needed. AppleScript uses native `osascript` via `execFile`. HxStore extraction uses native `strings` command. All other infrastructure (EventEmitter, SQLite, Ink) is already in the dependency tree.

---

## 11. File Inventory

New files to create:

```
src/
├── core/
│   ├── proactive-engine.ts      # Central coordinator, tick loop, config
│   ├── trigger-engine.ts        # Rule registry, matching, cooldowns
│   └── suggestion-ranker.ts     # Scoring, dedup, threshold filtering
├── integrations/
│   ├── file-watcher.ts          # chokidar wrapper, event classification
│   ├── email-monitor.ts         # HxStore + attachment + manual drop
│   └── calendar-bridge.ts       # AppleScript Calendar.app reader
├── ui/
│   └── SuggestionBar.tsx        # Ink component for suggestion display
└── tests/
    ├── proactive-engine.test.ts
    ├── trigger-engine.test.ts
    ├── suggestion-ranker.test.ts
    ├── file-watcher.test.ts
    ├── email-monitor.test.ts
    └── calendar-bridge.test.ts
```

Files to modify:

```
src/core/orchestrator.ts         # Add proactiveEngine to OrchestratorDeps
src/core/state.ts                # Add suggestion_log, suggestion_prefs tables + methods
src/ui/App.tsx                   # Add SuggestionBar to layout
package.json                     # Add chokidar dependency
```
