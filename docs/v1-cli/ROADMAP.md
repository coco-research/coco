# Project CoCo — Roadmap

**Date:** 2026-03-19
**Owner:** Rijul Kalra
**Total estimated effort:** 15-21 days across 6 phases
**MVP boundary:** Phases 0-2 (CoCo v1.0)

## Current Status (2026-03-20)
- **Phase 0:** Complete — POC validated
- **Phase 1:** Complete — 29/29 tests, 100% routing accuracy
- **Phase 2:** Complete — 101 tests, parallel sessions + dashboard + queue
- **Phase 3:** Complete — 120 tests (after hardening), voice I/O with whisper.cpp + macOS say
- **Phase 4:** Planned — PLAN.md written at phase4/PLAN.md
- **Phase 5:** Planned — PLAN.md written at phase5/PLAN.md

---

## MVP Definition

**CoCo v1.0 = Phases 0 through 2.** At that point you have a persistent terminal assistant that dispatches to the full /team skill ecosystem, runs parallel sessions with a live dashboard, and persists state across restarts. That is the product you use daily. Phases 3-5 are enhancements that compound value but are not required for daily use.

---

## Phase 0: Proof of Concept

**Goal:** Prove the dispatch pattern — text in, route to `claude -p` with the right skill context, stream output back.

**Effort:** 1 day

### Success Criteria
- [x] Shell script accepts free-text input from stdin
- [x] Routes input to `claude -p` with correct system prompt (CoCo personality + skill context)
- [x] Streams Claude's response to stdout in real-time (not buffered)
- [x] At least 3 existing /team commands are callable through natural text (e.g., "research voice APIs" triggers research skill)
- [x] Round-trip latency from input to first token < 3 seconds

### Key Deliverables
1. `coco.sh` — single shell script (~50-100 lines)
2. `coco-system-prompt.md` — CoCo personality prompt with skill routing table
3. A recorded demo showing 3 dispatches (research, build, review)

### Dependencies
- Claude CLI installed and authenticated (`claude -p` works)
- Existing /team commands in `rijuls-claude-skills/team/commands/`

### Risk Areas
- **`claude -p` streaming behavior** — need to verify it streams tokens, not buffers. Mitigation: test with `--stream` flag or pipe through `unbuffer`.
- **Skill context injection** — fitting 18 command descriptions into a system prompt without blowing context. Mitigation: use one-line summaries, not full command files.

---

## Phase 1: Core Application

**Goal:** Replace the shell script with a real Node.js + Ink app that has single-session dispatch, a skill registry, SQLite state, and the CoCo personality.

**Effort:** 3-4 days

### Success Criteria
- [x] `npx coco` or `coco` launches the Ink terminal UI
- [x] Text input routes to the correct /team skill with > 80% accuracy on 20 test inputs
- [x] Skill registry auto-discovers all commands from `~/.claude/commands/` at startup
- [x] SQLite stores: session history, last 50 exchanges, skill usage counts
- [x] Session survives a Ctrl+C and resumes on next launch (state persisted)
- [x] CoCo personality prompt produces ambient-style responses ("Ready." not "How can I help you today?")

### Key Deliverables
1. **`src/core/orchestrator.ts`** — Main loop: input -> intent classification -> skill dispatch -> output
2. **`src/core/skill-registry.ts`** — Reads `~/.claude/commands/*.md` at startup, builds routing table
3. **`src/core/state.ts`** — SQLite schema: `sessions`, `exchanges`, `skills`, `feedback`
4. **`src/ui/App.tsx`** — Ink root component with input bar and output panel
5. **`src/ui/CommandInput.tsx`** — Text input component (Tab-completion for skill names)
6. **`coco-personality.md`** — System prompt defining CoCo's voice, autonomy rules, output style
7. **`package.json`** — Dependencies: `ink`, `react`, `@anthropic-ai/sdk`, `better-sqlite3`

### Dependencies
- Phase 0 completed (dispatch pattern validated)
- Node.js 20+ installed
- Claude Agent SDK available (`@anthropic-ai/sdk`)

### Risk Areas
- **Claude Agent SDK session management** — the SDK may not expose fine-grained session control. Mitigation: wrap `claude -p` as a child process if SDK is insufficient.
- **Ink rendering complexity** — Ink's React model can fight with streaming output. Mitigation: use `<Static>` for completed output, `<Text>` for streaming.
- **Skill routing accuracy** — keyword matching will be brittle. Mitigation: use a two-pass approach (exact match on /command prefix, then fuzzy match on keywords from skill descriptions).

---

## Phase 2: Parallel Sessions + Dashboard

**Goal:** Run multiple Claude sessions simultaneously with a live dashboard showing status, progress, and output for each.

**Effort:** 3-4 days

### Success Criteria
- [x] Can run 3+ sessions in parallel (e.g., "research X" + "write tests for Y" + "review Z")
- [x] Dashboard shows each session as a collapsible block with: name, status (running/done/error), elapsed time
- [x] Status bar shows: project name, git branch, active session count, wall clock
- [x] Task queue accepts commands while sessions are running ("queue this for after the research finishes")
- [x] Output from parallel sessions does not interleave — each session's output is contained in its panel
- [x] Total memory usage < 500MB with 3 concurrent sessions

### Key Deliverables
1. **`src/core/session-manager.ts`** — Spawn, track, pause, resume, kill Claude sessions as child processes
2. **`src/ui/SessionPanel.tsx`** — Collapsible block per session with live output streaming
3. **`src/ui/StatusBar.tsx`** — Persistent bottom bar: `CoCo | project-name (branch) | 3 active | 14:22`
4. **`src/ui/Dashboard.tsx`** — Layout manager: arranges session panels, handles collapse/expand
5. **`src/core/task-queue.ts`** — FIFO queue with dependency support ("after session X completes, run Y")
6. SQLite schema additions: `task_queue`, `session_dependencies`

### Dependencies
- Phase 1 completed (single session works end-to-end)
- Understanding of Claude CLI's process model (can we run multiple `claude -p` processes safely?)

### Risk Areas
- **Process limits** — each Claude session is a separate process; 5+ may strain system resources. Mitigation: configurable concurrency cap (default: 3), queue overflow.
- **Output capture from child processes** — need reliable stdout/stderr capture without dropping lines. Mitigation: use `execa` with streaming, not raw `child_process`.
- **Race conditions in SQLite** — concurrent sessions writing to same DB. Mitigation: WAL mode, serialized writes through a single state module.

---

## --- MVP BOUNDARY (v1.0) ---

Phases 0-2 deliver a usable product: a persistent terminal assistant that understands your skill ecosystem, runs parallel tasks with a live dashboard, and remembers state across sessions. Everything below enhances but is not required for daily use.

---

## Phase 3: Voice I/O

**Goal:** Add push-to-talk voice input via local whisper.cpp and text-to-speech output via macOS `say`, making CoCo hands-free capable.

**Effort:** 2-3 days

### Success Criteria
- [x] Push-to-talk (hold spacebar or configurable key) captures audio and transcribes via whisper.cpp
- [x] Transcription accuracy > 90% on technical speech (function names, CLI commands, project names)
- [x] Transcription latency < 2 seconds for a 10-second utterance
- [x] TTS reads back CoCo's response headline (first sentence only, not full output)
- [x] Voice can be toggled on/off without restarting (`/voice on`, `/voice off`)
- [x] Works fully offline — no cloud API calls for voice

### Key Deliverables
1. **`src/voice/listener.ts`** — Manages whisper.cpp subprocess, audio capture, transcription pipeline
2. **`src/voice/speaker.ts`** — Wraps macOS `say` command with voice selection and rate control
3. **`src/voice/hotkey.ts`** — Push-to-talk key binding (spacebar when input is empty, configurable)
4. **Voice model setup script** — Downloads whisper.cpp `base.en` model on first run
5. UI indicator: microphone icon in status bar when listening

### Dependencies
- Phase 1 completed (text input pipeline exists to receive transcribed text)
- whisper.cpp compiled for macOS ARM (`brew install whisper-cpp` or build from source)
- macOS (for `say` command; Linux TTS would need `espeak` alternative)

### Risk Areas
- **whisper.cpp compilation** — ARM Mac builds can be finicky. Mitigation: use Homebrew formula; fallback to pre-built binary.
- **Audio capture on macOS** — requires microphone permission. Mitigation: use `sox` or `rec` for capture, prompt for permission on first run.
- **Transcription of technical terms** — "kubectl" becomes "cube cuttle". Mitigation: post-processing dictionary that maps common misheard terms to correct ones.
- **Push-to-talk UX** — holding spacebar while in text input mode creates conflict. Mitigation: only activate PTT when input field is empty, or use a modifier key (Ctrl+Space).

---

## Phase 4: Intelligence Layer

**Goal:** Make CoCo smart enough to route natural language to the right skill without explicit /commands, learn from past sessions, and greet with ambient context.

**Effort:** 3-5 days

### Success Criteria
- [ ] "I need to review the auth service" routes to `/team review` with correct context — no /prefix needed
- [ ] Intent classification accuracy > 90% on a 50-query test set spanning all 18 team commands
- [ ] CoCo greets with project-aware context: "how-i-pm-with-ai (main). Last session: team research on voice APIs. 3 tasks queued."
- [ ] Skill recommendations based on history: "You usually run /team test after /team build — want me to queue it?"
- [ ] Learning loop: skill routing improves over time as corrections are stored (user says "no, I meant review not research" -> stored as training signal)
- [ ] Context window management: CoCo summarizes old exchanges to stay within token limits

### Key Deliverables
1. **`src/core/intent-classifier.ts`** — Two-stage routing: (1) keyword/regex fast path, (2) Claude-based classification for ambiguous inputs
2. **`src/core/learning-store.ts`** — SQLite tables for: `routing_corrections`, `skill_sequences`, `user_preferences`
3. **`src/integrations/team-router.ts`** — Maps natural language intents to /team commands with parameter extraction
4. **`src/integrations/gsd-router.ts`** — Maps project-level intents to /gsd commands
5. **`src/core/context-manager.ts`** — Ambient greeting generator, session summarizer, context window optimizer
6. SQLite schema additions: `intent_log`, `routing_corrections`, `session_summaries`

### Dependencies
- Phase 1 completed (skill registry exists)
- Phase 2 recommended (parallel sessions generate richer usage data for learning)
- Existing /team commands have consistent description formats (they do: each .md has a clear purpose line)

### Risk Areas
- **Intent ambiguity** — "build the API" could be /team build, /team develop, or /team plan. Mitigation: when confidence < 0.7, ask a one-line clarification rather than guessing.
- **Cold start** — no usage data on day one. Mitigation: seed with 50 hand-crafted intent -> skill mappings covering common patterns.
- **Claude API cost for classification** — using Claude to classify every input is expensive. Mitigation: local keyword matching handles 70%+ of inputs; Claude only called for ambiguous ones.
- **Context window bloat** — long sessions exceed limits. Mitigation: rolling summary after every 10 exchanges, keep only last 5 raw exchanges.

---

## Phase 5: Proactive Mode

**Goal:** Make CoCo act without being asked — watching for file changes, email arrivals, calendar events, and proactively suggesting actions.

**Effort:** Ongoing (initial implementation 3-5 days, then continuous refinement)

### Success Criteria
- [ ] File watcher detects new/changed files in active project and suggests relevant actions ("New test file added. Run tests?")
- [ ] Email monitor (HxStore + attachment watcher) surfaces new emails with suggested actions ("Email from stakeholder re: API spec. Want me to summarize?")
- [ ] Proactive suggestions appear in a non-intrusive "suggestion bar" above the input — dismissed with Esc, accepted with Enter
- [ ] False positive rate < 20% (4 out of 5 suggestions are actually useful)
- [ ] All proactive actions require explicit confirmation before execution (never auto-execute writes)
- [ ] Calendar awareness: "Standup in 15 min. Want me to summarize today's commits for your update?"

### Key Deliverables
1. **`src/integrations/file-watcher.ts`** — Uses `chokidar` to watch project directory, classifies changes, generates suggestions
2. **`src/integrations/email-monitor.ts`** — Wraps existing `.sync/sync.sh` pattern (HxStore + attachment cache monitoring)
3. **`src/integrations/calendar-bridge.ts`** — Reads macOS Calendar.app via AppleScript, surfaces upcoming events
4. **`src/ui/SuggestionBar.tsx`** — Non-intrusive suggestion display above input, keyboard-dismissable
5. **`src/core/trigger-engine.ts`** — Rule engine: trigger condition -> suggested action -> confidence score -> display threshold
6. **`src/core/suggestion-ranker.ts`** — Ranks suggestions by relevance using recent context + historical acceptance rate

### Dependencies
- Phase 1 completed (CoCo can execute dispatched commands)
- Phase 4 recommended (intent classification enables smarter suggestions)
- Existing email monitoring infrastructure (`~/.sync/` pattern from how-i-pm-with-ai)
- macOS Calendar.app accessible via AppleScript

### Risk Areas
- **Notification fatigue** — too many suggestions make CoCo annoying. Mitigation: start conservative (high confidence threshold), let user tune via `/coco sensitivity low/medium/high`.
- **File watcher performance** — large repos generate thousands of events. Mitigation: debounce (500ms), ignore `node_modules`/`.git`/build dirs, limit to top-2 project directories.
- **Email monitoring reliability** — HxStore binary format may change with Outlook updates. Mitigation: graceful degradation; if HxStore parsing fails, fall back to attachment-only monitoring.
- **Privacy** — proactive mode reads files and emails. Mitigation: all monitored paths are explicitly configured, never scan outside declared watch paths.

---

## Timeline Summary

```
Week 1:  [Phase 0 ----][Phase 1 -------------------------]
Week 2:  [Phase 1 --][Phase 2 ----------------------------]
Week 3:  [Phase 2 ------][Phase 3 -----------------------]
Week 4:  [Phase 4 ----------------------------------------]
Week 5:  [Phase 4 ------][Phase 5 initial ---------------]
Week 5+: [Phase 5 ongoing refinement..................... ]
```

| Phase | Days | Cumulative | Milestone |
|-------|------|------------|-----------|
| 0: POC | 1 | 1 | Dispatch pattern validated |
| 1: Core | 3-4 | 4-5 | Single-session app works |
| 2: Parallel | 3-4 | 7-9 | **CoCo v1.0 — daily driver** |
| 3: Voice | 2-3 | 9-12 | Hands-free capable |
| 4: Intelligence | 3-5 | 12-17 | Natural language routing |
| 5: Proactive | 3-5+ | 15-22 | Ambient assistant |

---

## Architecture Decision Records

### ADR-1: Node.js + Ink over Python + Rich
**Decision:** Node.js
**Rationale:** Claude Agent SDK is TypeScript-native. Ink provides React component model for complex UI. The entire Claude Code ecosystem (commands, skills, hooks) is already JavaScript/TypeScript. Python would require bridging.

### ADR-2: SQLite over PostgreSQL/DynamoDB
**Decision:** SQLite (via `better-sqlite3`)
**Rationale:** CoCo is a single-user local tool. SQLite is zero-config, survives restarts, supports WAL mode for concurrent reads during parallel sessions. No network dependency.

### ADR-3: whisper.cpp over cloud STT
**Decision:** Local whisper.cpp
**Rationale:** Offline-first. No API costs. No latency from network round-trips. Privacy — voice data never leaves the machine. Base.en model is 150MB and runs in real-time on M-series Macs.

### ADR-4: Child process dispatch over SDK embedding
**Decision:** Spawn `claude -p` as child processes (with SDK embedding as stretch goal)
**Rationale:** Child processes inherit ALL existing configuration — CLAUDE.md, commands, skills, agents, hooks, MCP servers. SDK embedding would require re-implementing that configuration loading. Start with child processes; migrate to SDK when the SDK supports full config inheritance.

---

## Quick Wins (Available Today, No Build Required)

These can be done before Phase 0 as CLAUDE.md or skill changes:

1. **Natural language routing** — Add a routing table to CLAUDE.md that maps common intents to /team commands. Zero code.
2. **macOS notifications** — Add `osascript -e 'display notification "Done" with title "CoCo"'` to skill completion hooks. One line.
3. **CoCo personality prompt** — Add the personality spec (ambient greeting, headline-first output, risk-proportional autonomy) as a CLAUDE.md prefix. Zero code.

---

## Open Questions

1. **Claude SDK session limits** — How many concurrent `claude -p` sessions can run before hitting API rate limits or local resource constraints? Needs testing in Phase 0.
2. **Ink + streaming compatibility** — Can Ink reliably render streaming output from multiple child processes without flicker? Needs validation in Phase 1.
3. **Distribution** — Should CoCo be an npm package (`npx coco`), a Homebrew formula, or just a git clone? Defer to Phase 2 completion.
4. **Multi-project support** — Should CoCo manage multiple projects simultaneously, or one project per instance? Start with single-project; revisit after Phase 2.
