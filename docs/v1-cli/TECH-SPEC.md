# Project CoCo — Technical Specification

**Date:** 2026-03-19
**Author:** Senior Backend Engineer / Cloud Architect
**Status:** Draft
**Depends on:** RESEARCH.md findings

---

## 1. Project Setup

### 1.1 Directory Structure

```
coco/
├── package.json
├── tsconfig.json
├── coco.db                          # SQLite state (created at runtime)
├── src/
│   ├── index.tsx                    # Entry point — parse CLI args, boot Ink app
│   ├── core/
│   │   ├── orchestrator.ts          # Main event loop, intent → route → execute
│   │   ├── session-manager.ts       # Spawn/track/resume Claude SDK sessions
│   │   ├── state.ts                 # SQLite via better-sqlite3
│   │   └── skill-registry.ts        # Reads ~/.claude/commands/ at startup
│   ├── ui/
│   │   ├── App.tsx                  # Ink root layout
│   │   ├── SessionPanel.tsx         # Live output per running session
│   │   ├── StatusBar.tsx            # Persistent one-line status
│   │   └── CommandInput.tsx         # Text input with history
│   ├── voice/
│   │   ├── listener.ts             # whisper.cpp subprocess, push-to-talk
│   │   └── speaker.ts             # macOS `say` / edge-tts
│   └── integrations/
│       ├── intent-classifier.ts     # NL → skill route mapping
│       ├── team-router.ts           # → /team commands
│       ├── gsd-router.ts            # → /gsd commands
│       └── email-router.ts          # → /email commands
├── prompts/
│   └── coco-system.md              # CoCo personality + routing instructions
└── tests/
    ├── orchestrator.test.ts
    ├── session-manager.test.ts
    └── skill-registry.test.ts
```

### 1.2 package.json

```json
{
  "name": "coco",
  "version": "0.1.0",
  "type": "module",
  "bin": { "coco": "./dist/index.js" },
  "scripts": {
    "dev": "tsx src/index.tsx",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "vitest"
  },
  "dependencies": {
    "@anthropic-ai/claude-code": "^1.0.0",
    "ink": "^5.1.0",
    "ink-text-input": "^6.0.0",
    "ink-spinner": "^5.0.0",
    "react": "^18.3.0",
    "better-sqlite3": "^11.0.0",
    "glob": "^11.0.0",
    "gray-matter": "^4.0.3",
    "eventemitter3": "^5.0.0",
    "p-queue": "^8.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@types/better-sqlite3": "^7.6.0",
    "@types/react": "^18.3.0",
    "tsx": "^4.0.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0",
    "@anthropic-ai/claude-code": "^1.0.0"
  }
}
```

**Key dependency notes:**
- `@anthropic-ai/claude-code` provides `query()` which spawns Claude Code as a subprocess, inheriting all commands/skills/hooks/MCP servers. This is the entire brain.
- `ink` + `react` for rich terminal UI (boxes, spinners, live text, flexbox layout).
- `better-sqlite3` for synchronous SQLite (no async overhead, single-process safe).
- `p-queue` for concurrency-limited task execution (max 5-7 parallel sessions).
- `gray-matter` to parse frontmatter from skill markdown files.

### 1.3 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "jsx": "react-jsx",
    "jsxImportSource": "react",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "declaration": true,
    "sourceMap": true
  },
  "include": ["src/**/*"]
}
```

---

## 2. Core Module Specs

### 2.1 orchestrator.ts — Main Event Loop

**Responsibility:** Accept user input (text or voice-transcribed), classify intent, route to the correct skill/session, and emit status events for the UI.

```typescript
// Type definitions

interface CocoEvent {
  type: 'user_input' | 'intent_classified' | 'session_spawned' |
        'session_output' | 'session_complete' | 'session_error' |
        'queue_updated' | 'voice_input' | 'voice_output';
  payload: unknown;
  timestamp: number;
}

interface ClassifiedIntent {
  skill: string;           // e.g., "team-research", "gsd:execute-phase", "email-read"
  args: string;            // remaining text after skill extraction
  confidence: number;      // 0-1, from intent classifier
  requiresConfirmation: boolean;  // true if write operation
}

class Orchestrator extends EventEmitter {
  constructor(
    sessionManager: SessionManager,
    skillRegistry: SkillRegistry,
    state: StateManager,
    intentClassifier: IntentClassifier
  )

  // Main entry — called by CommandInput on submit or Listener on transcript
  async handleInput(text: string): Promise<void>

  // Queue a task for later execution (when at concurrency limit)
  async enqueue(intent: ClassifiedIntent): Promise<string>  // returns queue ID

  // Process the next item from the queue
  private async processQueue(): Promise<void>

  // Emergency stop — kill all running sessions
  async halt(): Promise<void>
}
```

**Event loop flow:**

```
User Input
    │
    ▼
┌──────────────────┐
│ Intent Classifier │──→ Is this a meta-command? (/status, /halt, /queue)
└──────────────────┘    YES → handle directly, return
    │ NO
    ▼
┌──────────────────┐
│ Skill Registry   │──→ Match to a known skill?
│ Lookup           │    YES → build ClassifiedIntent with high confidence
└──────────────────┘    NO  → fall through to Claude classification
    │ NO MATCH
    ▼
┌──────────────────┐
│ Claude-powered   │──→ Send input + skill list to a small Claude query()
│ Classification   │    Returns: { skill, args, confidence }
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Confidence Check │──→ confidence < 0.7? → ask user to clarify
└──────────────────┘    confidence >= 0.7? → proceed
    │
    ▼
┌──────────────────┐
│ Risk Check       │──→ requiresConfirmation? → prompt user Y/N
└──────────────────┘    read-only? → just go
    │
    ▼
┌──────────────────┐
│ Concurrency Gate │──→ at limit? → enqueue, notify user
└──────────────────┘    under limit? → spawn session
    │
    ▼
  SessionManager.spawn(intent)
```

**Meta-commands handled directly by orchestrator (not routed to Claude):**
- `/status` — show all running/queued sessions
- `/halt` — kill all sessions
- `/halt <id>` — kill specific session
- `/queue` — show task queue
- `/history` — show recent completions
- `/voice on|off` — toggle voice I/O

### 2.2 session-manager.ts — Claude SDK Session Management

**Responsibility:** Spawn Claude Code subprocess sessions via the SDK `query()` function, track their lifecycle, stream their output, enforce concurrency limits, and handle rate-limit backoff.

```typescript
import { query, type Message } from '@anthropic-ai/claude-code';

interface Session {
  id: string;              // UUID
  skill: string;           // e.g., "team-research"
  args: string;            // arguments passed
  status: 'running' | 'queued' | 'complete' | 'error' | 'rate-limited';
  pid: number | null;      // subprocess PID
  startedAt: number;
  completedAt: number | null;
  output: string;          // accumulated output
  messages: Message[];     // full conversation for resume
  cwd: string;             // working directory for session
  abortController: AbortController;
}

class SessionManager extends EventEmitter {
  private sessions: Map<string, Session>;
  private queue: PQueue;   // p-queue, concurrency: 5

  constructor(state: StateManager, maxConcurrency: number = 5)

  // Spawn a new Claude Code session
  async spawn(intent: ClassifiedIntent): Promise<string>  // returns session ID

  // Implementation detail: spawn uses SDK query()
  private async executeSession(session: Session): Promise<void> {
    // The key SDK call:
    const result = await query({
      prompt: session.args,
      options: {
        systemPrompt: buildSystemPrompt(session.skill),
        cwd: session.cwd,
        allowedTools: ['Bash', 'Read', 'Write', 'Edit', 'Glob', 'Grep'],
        maxTurns: 50,
        abortController: session.abortController,
      },
      onMessage: (msg) => {
        // Stream output to UI
        this.emit('session_output', {
          sessionId: session.id,
          message: msg,
        });
        session.messages.push(msg);
      },
    });
    // On complete: persist result, update state
  }

  // Resume a session with additional input (follow-up questions)
  async resume(sessionId: string, input: string): Promise<void>

  // Kill a specific session
  async kill(sessionId: string): Promise<void>

  // Kill all sessions
  async killAll(): Promise<void>

  // Get session by ID
  get(sessionId: string): Session | undefined

  // Get all active sessions
  getActive(): Session[]

  // Rate limit handling: exponential backoff with jitter
  private async handleRateLimit(session: Session): Promise<void>
}
```

**Concurrency model:**
- `p-queue` with `concurrency: 5` (configurable, max 7).
- Each `query()` call is a subprocess — they run in parallel with independent contexts.
- Rate-limit detection: catch 429 errors from SDK, pause that session, retry with exponential backoff (1s, 2s, 4s, 8s, max 30s).
- If 3+ sessions hit rate limits simultaneously, pause all spawns for 60s and drain queue one-at-a-time.

**Session lifecycle:**

```
QUEUED → RUNNING → COMPLETE
                 → ERROR
                 → RATE-LIMITED → (backoff) → RUNNING
```

### 2.3 state.ts — SQLite State Persistence

**Responsibility:** All persistent state — sessions, events, context, queue. Single `better-sqlite3` instance, synchronous writes (no WAL contention since single-process).

```typescript
import Database from 'better-sqlite3';

class StateManager {
  private db: Database.Database;

  constructor(dbPath: string = './coco.db')

  // Initialize schema (idempotent — uses IF NOT EXISTS)
  initialize(): void

  // Session CRUD
  saveSession(session: SessionRow): void
  getSession(id: string): SessionRow | undefined
  getActiveSessions(): SessionRow[]
  getRecentSessions(limit: number): SessionRow[]
  updateSessionStatus(id: string, status: string, output?: string): void

  // Event log (append-only)
  logEvent(event: EventRow): void
  getEvents(sessionId: string): EventRow[]
  getRecentEvents(limit: number): EventRow[]

  // Task queue
  enqueue(task: QueueRow): void
  dequeue(): QueueRow | undefined
  getQueueDepth(): number
  getQueue(): QueueRow[]
  removeFromQueue(id: string): void

  // Context (key-value store for cross-session state)
  setContext(key: string, value: string): void
  getContext(key: string): string | undefined
  deleteContext(key: string): void

  // Cleanup: prune events older than N days
  prune(daysToKeep: number): void
}
```

Full schema in Section 6 below.

### 2.4 skill-registry.ts — Skill Discovery

**Responsibility:** Read `~/.claude/commands/` and project-level `.claude/commands/` at startup, parse markdown files to extract skill names, descriptions, and metadata. Provide fast lookup for intent routing.

```typescript
interface Skill {
  name: string;            // e.g., "team-research"
  command: string;         // e.g., "/team research"
  description: string;     // first line or frontmatter description
  filePath: string;        // absolute path to .md file
  category: string;        // "team" | "gsd" | "email" | "standalone"
  isWriteOperation: boolean;  // heuristic: "develop", "fix", "execute" = true
  aliases: string[];       // natural language triggers
}

class SkillRegistry {
  private skills: Map<string, Skill>;
  private aliasIndex: Map<string, string>;  // alias → skill name

  constructor()

  // Scan directories, parse files, build index
  async loadAll(): Promise<void>

  // Load from a specific commands directory
  private async loadDirectory(dir: string, category?: string): Promise<void>

  // Parse a single skill markdown file
  private parseSkillFile(filePath: string): Skill

  // Lookup by exact name
  get(name: string): Skill | undefined

  // Lookup by alias or partial match
  findByAlias(text: string): Skill | undefined

  // Get all skills (for intent classifier context)
  getAll(): Skill[]

  // Get skills as a compact string for LLM context
  toPromptContext(): string
  // Returns format like:
  // "Available skills:
  //  - /team research <topic> — Deep multi-angle investigation
  //  - /team develop <feature> — Build working code/config
  //  - /gsd:execute-phase — Execute current GSD phase
  //  - /email-read — Read recent emails
  //  ..."
}
```

**Skill discovery directories (scanned in order, later overrides earlier):**
1. `~/.claude/commands/` — global user commands
2. `~/.claude/commands/gsd/` — GSD subcommands
3. `.claude/commands/` — project-level commands (if exists)

**Write-operation heuristic:** Skills with names matching `develop|fix|execute|build|write|create|edit|deploy|push|delete|remove` default to `isWriteOperation: true`. All others default to `false`. Overridable via frontmatter `# write: true`.

**Alias generation:** Each skill gets auto-generated aliases from its description plus manual aliases from frontmatter. Example: `team-research` gets aliases `["research", "investigate", "look into", "find out about"]`.

---

## 3. UI Module Specs

### 3.1 App.tsx — Ink Root Layout

```tsx
// Layout structure (top to bottom):
// ┌─ StatusBar ──────────────────────────────────┐
// ├─ SessionPanel (scrollable, takes remaining) ──┤
// ├─ CommandInput ────────────────────────────────┤
// └───────────────────────────────────────────────┘

interface AppProps {
  orchestrator: Orchestrator;
  sessionManager: SessionManager;
  state: StateManager;
}

const App: React.FC<AppProps> = ({ orchestrator, sessionManager, state }) => {
  // State hooks:
  // - sessions: Session[] — active sessions from SessionManager events
  // - queueDepth: number — from state.getQueueDepth()
  // - focusedSession: string | null — which session panel is expanded

  // Event subscriptions:
  // - orchestrator.on('session_spawned') → update sessions
  // - orchestrator.on('session_complete') → update sessions
  // - sessionManager.on('session_output') → append to session panel

  return (
    <Box flexDirection="column" height="100%">
      <StatusBar
        project={cwd}
        branch={gitBranch}
        activeSessions={sessions.length}
        queueDepth={queueDepth}
      />
      <SessionPanel
        sessions={sessions}
        focusedSession={focusedSession}
        onFocus={setFocusedSession}
      />
      <CommandInput
        onSubmit={(text) => orchestrator.handleInput(text)}
      />
    </Box>
  );
};
```

### 3.2 SessionPanel.tsx — Live Output Per Session

```tsx
interface SessionPanelProps {
  sessions: Session[];
  focusedSession: string | null;
  onFocus: (id: string | null) => void;
}

// Renders a collapsible block per session:
// [L1 Research] ........................... done  (v)
// [L2 Execute] ............................. 3/4  (v)
//   senior-backend-eng: Working on service.ts...
// [L3 Review] ............................. wait  ( )

// Behavior:
// - Collapsed: one line per session (name + status + progress)
// - Expanded: last 20 lines of session output, auto-scrolling
// - Completed sessions: show summary line, collapsible for full output
// - Color coding: green=done, yellow=running, red=error, gray=queued
// - Arrow keys navigate between sessions, Enter toggles expand/collapse
```

### 3.3 StatusBar.tsx — Persistent One-Line Status

```tsx
interface StatusBarProps {
  project: string;        // basename of cwd
  branch: string;         // git branch
  activeSessions: number;
  queueDepth: number;
  voiceActive: boolean;
  clock: string;          // HH:MM
}

// Renders:
// CoCo | how-i-pm-with-ai (main) | 2 active | Q:3 | mic:on | 14:32
// Uses Ink <Box> with borderStyle="single" borderTop borderBottom
```

### 3.4 CommandInput.tsx — Text Input with History

```tsx
interface CommandInputProps {
  onSubmit: (text: string) => void;
}

// Features:
// - Standard text input with ">" prompt
// - Up/Down arrow cycles through command history (stored in SQLite)
// - Tab completion for skill names (from SkillRegistry)
// - Ctrl+C sends interrupt to focused session, double Ctrl+C exits CoCo
// - Empty submit does nothing
// - History persisted in SQLite context table (key: "input_history")

// Implementation: ink-text-input with custom key handling
```

---

## 4. Voice Module Specs

### 4.1 listener.ts — Speech-to-Text via whisper.cpp

```typescript
interface ListenerConfig {
  model: string;           // "base.en" — small, fast, English-only
  sampleRate: number;      // 16000
  pushToTalkKey: string;   // "F5" (configurable)
  vadThreshold: number;    // voice activity detection sensitivity
}

class Listener extends EventEmitter {
  private whisperProcess: ChildProcess | null;
  private isListening: boolean;
  private audioBuffer: Buffer[];

  constructor(config: ListenerConfig)

  // Start whisper.cpp in streaming mode
  async start(): Promise<void>
  // Spawns: whisper.cpp --model base.en --stream --step 3000 --length 5000

  // Stop listening
  async stop(): Promise<void>

  // Toggle push-to-talk (bound to key in App.tsx)
  toggle(): void

  // Events emitted:
  // 'transcript' → { text: string, isFinal: boolean }
  // 'error' → Error
  // 'listening' → boolean
}
```

**Whisper.cpp integration:**
- Binary expected at `~/.local/bin/whisper-stream` or configurable via `COCO_WHISPER_PATH`.
- Model expected at `~/.local/share/whisper/ggml-base.en.bin`.
- Runs in `--stream` mode: continuous listening, emits partial transcripts.
- Push-to-talk preferred over always-on to avoid false triggers.
- Final transcript (silence detected) is sent to `orchestrator.handleInput()`.

### 4.2 speaker.ts — Text-to-Speech

```typescript
interface SpeakerConfig {
  engine: 'say' | 'edge-tts';  // macOS say for low-latency, edge-tts for quality
  voice: string;                 // "Samantha" for say, "en-US-AriaNeural" for edge-tts
  rate: number;                  // words per minute (default: 200)
  enabled: boolean;
}

class Speaker {
  constructor(config: SpeakerConfig)

  // Speak text (non-blocking — fire and forget)
  async speak(text: string): Promise<void>
  // For 'say': spawns `say -v Samantha -r 200 "text"`
  // For 'edge-tts': spawns edge-tts pipe to mpv/afplay

  // Stop current speech
  stop(): void

  // Speak a summary (truncates long text to first 2 sentences)
  async speakSummary(text: string): Promise<void>
}
```

**Design decisions:**
- Default engine: macOS `say` — zero dependencies, low latency (~100ms), good enough for status updates.
- `edge-tts` as optional upgrade — higher quality voice, requires network.
- Only speak summaries and status changes, never full session output.
- Mutable — user can interrupt with any keypress.

---

## 5. Key Technical Decisions

### 5.1 How does CoCo route "check my email" to the /email skill?

**Two-tier intent classification:**

**Tier 1 — Pattern matching (instant, no LLM call):**

```typescript
// intent-classifier.ts
const PATTERN_RULES: Array<{ pattern: RegExp; skill: string }> = [
  { pattern: /\b(check|read|show)\b.*\b(email|mail|inbox)\b/i, skill: 'email-read' },
  { pattern: /\b(unread)\b.*\b(email|mail)\b/i, skill: 'email-unread' },
  { pattern: /\b(reply|respond)\b.*\b(email|mail)\b/i, skill: 'email-reply' },
  { pattern: /\b(research|investigate|look into|find out)\b/i, skill: 'team-research' },
  { pattern: /\b(build|develop|implement|create)\b/i, skill: 'team-develop' },
  { pattern: /\b(review|audit|check)\b.*\b(code|pr|pull request)\b/i, skill: 'team-review' },
  { pattern: /\b(fix|debug|broken)\b/i, skill: 'team-fix' },
  { pattern: /\b(plan|roadmap|timeline)\b/i, skill: 'team-plan' },
  { pattern: /\b(test|coverage)\b/i, skill: 'team-test' },
  { pattern: /^\/\w+/,  skill: '__direct_command__' },  // direct slash commands pass through
];
```

**Tier 2 — Claude classification (for ambiguous inputs):**

When Tier 1 either misses or has low confidence, send a lightweight Claude `query()` with the skill registry as context:

```
System: You are a command router. Given user input and available skills,
return JSON: { "skill": "skill-name", "args": "remaining text", "confidence": 0.0-1.0 }

Available skills:
${skillRegistry.toPromptContext()}

User input: "${userInput}"
```

This query uses `maxTurns: 1` and no tools — pure classification, completes in <1 second.

**The full routing for "check my email":**
1. Tier 1 regex matches `check` + `email` → `email-read`, confidence 0.95.
2. Skip Tier 2.
3. `email-read` is `isWriteOperation: false` → no confirmation needed.
4. Spawn session: `query({ prompt: "/email-read", ... })`.

### 5.2 How does CoCo show progress from a running /team pipeline?

The `/team` pipeline runs as layers (L1 Research → L2 Execute → L3 Review → L4 Synthesis). Progress is tracked by parsing the `onMessage` callback output.

**Layer detection heuristic:**

```typescript
// Inside SessionManager.executeSession, within onMessage callback:

const LAYER_PATTERNS = [
  { pattern: /## Layer 1|## L1|Research Layer/i, layer: 1, name: 'Research' },
  { pattern: /## Layer 2|## L2|Execution Layer/i, layer: 2, name: 'Execute' },
  { pattern: /## Layer 3|## L3|Review Layer/i, layer: 3, name: 'Review' },
  { pattern: /## Layer 4|## L4|Synthesis Layer/i, layer: 4, name: 'Synthesis' },
];

const PROGRESS_PATTERN = /(\d+)\/(\d+)\s*(agents?|specialists?|roles?|tasks?)/i;

// On each message:
// 1. Check if text matches a LAYER_PATTERN → emit 'layer_change' event
// 2. Check if text matches PROGRESS_PATTERN → emit 'progress' event
// 3. UI subscribes to these events and updates SessionPanel accordingly
```

**UI rendering in SessionPanel:**

```
[L1 Research] ........................... done  (v)
[L2 Execute] ............................. 3/4  (v)
  senior-backend-eng: Working on service.ts...    ← last output line
[L3 Review] ............................. wait  ( )
[L4 Synthesis] .......................... wait  ( )
```

- `done` = layer pattern for next layer detected, or explicit "complete" in output.
- `3/4` = parsed from progress pattern.
- Last line of output shown for the active layer.
- `(v)` = expandable (show full output on Enter).

### 5.3 How does CoCo handle multiple sessions writing to the same project?

**Problem:** Two concurrent sessions (e.g., `/team develop auth` and `/team fix login-bug`) may both try to edit files in the same project directory.

**Solution: Optimistic locking with conflict detection.**

```typescript
// session-manager.ts — file lock tracking

interface FileLock {
  sessionId: string;
  filePath: string;
  acquiredAt: number;
}

class SessionManager {
  private fileLocks: Map<string, FileLock>;  // filePath → lock

  // Before spawning a write session, check for overlapping cwd:
  private checkConflicts(newSession: Session): string[] {
    const activeSessions = this.getActive()
      .filter(s => s.cwd === newSession.cwd && s.status === 'running');

    if (activeSessions.length > 0 && newSession.skill.startsWith('team-develop|team-fix')) {
      return activeSessions.map(s => s.id);
    }
    return [];
  }
}
```

**Conflict resolution strategy (in order of preference):**

1. **Different directories:** If sessions target different cwds, no conflict. Run in parallel.
2. **Read vs Write:** Read-only sessions (research, review, test) can run in parallel with anything.
3. **Write vs Write, same directory:** Queue the second write session. Notify user: `"⏸ Queued '/team fix login-bug' — waiting for '/team develop auth' to complete (same project directory)."`
4. **User override:** User can force parallel writes with `/force-run <queued-id>`. CoCo warns but complies.
5. **Post-completion merge check:** After both complete, suggest `/team review` to check for conflicts.

**The SDK helps here:** Each `query()` call is an independent subprocess with its own file access. Git provides the safety net — if both sessions create conflicting edits, standard git merge conflict resolution applies.

### 5.4 How does CoCo persist state across restarts?

**Everything goes to SQLite.** On shutdown (graceful or crash recovery):

```typescript
// orchestrator.ts — shutdown handler

async shutdown(): Promise<void> {
  // 1. Kill all running sessions (send SIGTERM, wait 5s, SIGKILL)
  await this.sessionManager.killAll();

  // 2. Save queue state — already in SQLite (queue table)
  // 3. Save session state — already in SQLite (sessions table)
  // 4. Save input history — already in SQLite (context table)
  // 5. Close DB connection
  this.state.close();
}

// On startup:
async startup(): Promise<void> {
  // 1. Open DB, run migrations
  this.state.initialize();

  // 2. Load skill registry
  await this.skillRegistry.loadAll();

  // 3. Check for incomplete sessions from last run
  const incomplete = this.state.getActiveSessions()
    .filter(s => s.status === 'running');

  if (incomplete.length > 0) {
    // Mark as interrupted, offer to re-run
    for (const session of incomplete) {
      this.state.updateSessionStatus(session.id, 'interrupted');
    }
    this.emit('recovery', {
      message: `Found ${incomplete.length} interrupted session(s) from last run.`,
      sessions: incomplete,
    });
    // UI will show: "Resume interrupted sessions? [Y/n]"
  }

  // 4. Process any queued tasks from last run
  const queued = this.state.getQueue();
  if (queued.length > 0) {
    this.emit('recovery', {
      message: `${queued.length} task(s) still in queue.`,
      queue: queued,
    });
  }
}
```

**What persists across restarts:**
- All session history (input, output, status, timestamps)
- Task queue (pending items survive restart)
- Command input history
- Context key-value pairs (e.g., last active project, preferences)
- Event log (for debugging and audit)

**What does NOT persist:**
- Running subprocess PIDs (sessions must be re-spawned)
- In-memory conversation state (messages array) — too large for SQLite, and the SDK manages its own conversation state
- Voice listener state (always starts off)

---

## 6. SQLite Schema

```sql
-- Sessions: one row per Claude SDK query() invocation
CREATE TABLE IF NOT EXISTS sessions (
  id            TEXT PRIMARY KEY,                          -- UUID
  skill         TEXT NOT NULL,                             -- e.g., "team-research"
  args          TEXT NOT NULL DEFAULT '',                  -- arguments passed
  status        TEXT NOT NULL DEFAULT 'queued',            -- queued|running|complete|error|interrupted|rate-limited
  cwd           TEXT NOT NULL,                             -- working directory
  output        TEXT NOT NULL DEFAULT '',                  -- accumulated output (last 10KB)
  summary       TEXT,                                      -- one-line summary on completion
  exit_code     INTEGER,                                   -- 0=success, 1=error, null=running
  started_at    INTEGER,                                   -- unix timestamp ms
  completed_at  INTEGER,                                   -- unix timestamp ms
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000)
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);

-- Events: append-only log for debugging and audit
CREATE TABLE IF NOT EXISTS events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id    TEXT,                                       -- nullable (some events are global)
  type          TEXT NOT NULL,                              -- e.g., "session_spawned", "user_input", "rate_limit"
  payload       TEXT NOT NULL DEFAULT '{}',                 -- JSON blob
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000),
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);

-- Queue: tasks waiting to be executed
CREATE TABLE IF NOT EXISTS queue (
  id            TEXT PRIMARY KEY,                           -- UUID
  skill         TEXT NOT NULL,
  args          TEXT NOT NULL DEFAULT '',
  priority      INTEGER NOT NULL DEFAULT 0,                -- higher = more urgent
  cwd           TEXT NOT NULL,
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000)
);

CREATE INDEX IF NOT EXISTS idx_queue_priority ON queue(priority DESC, created_at ASC);

-- Context: key-value store for cross-session state
CREATE TABLE IF NOT EXISTS context (
  key           TEXT PRIMARY KEY,
  value         TEXT NOT NULL,
  updated_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000)
);

-- Input history: command history for up-arrow recall
CREATE TABLE IF NOT EXISTS input_history (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT NOT NULL,
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000)
);

CREATE INDEX IF NOT EXISTS idx_input_history_created ON input_history(created_at DESC);
```

**Storage estimates:**
- Sessions: ~1KB per row (output truncated to last 10KB). 1000 sessions = ~10MB.
- Events: ~200 bytes per row. 100K events = ~20MB.
- Queue: negligible (transient).
- Total DB size after 6 months of heavy use: ~50MB.

**Maintenance:**
- `prune(30)` on startup: delete events older than 30 days.
- Output column stores only last 10KB per session (older output available via event log).

---

## 7. API Surface — User Commands

### 7.1 Natural Language (primary interface)

Users type or speak plain English. CoCo classifies and routes automatically.

| User says | CoCo routes to | Confirmation? |
|-----------|---------------|---------------|
| "check my email" | `/email-read` | No |
| "research OAuth 2.0 best practices" | `/team research OAuth 2.0 best practices` | No |
| "build an auth service for the API" | `/team develop auth service for the API` | Yes (write) |
| "what's the status of my project" | `/gsd:health` | No |
| "fix the failing tests" | `/team fix failing tests` | Yes (write) |
| "review the last PR" | `/team review last PR` | No |
| "plan the next sprint" | `/team plan next sprint` | No |

### 7.2 Direct Slash Commands (power-user)

Any existing Claude Code command works as-is by prefixing with `/`:

```
/team research <topic>
/team develop <feature>
/team review <scope>
/gsd:execute-phase
/gsd:health
/email-read
/email-unread
/email-reply
```

### 7.3 CoCo Meta-Commands (built-in)

| Command | Description |
|---------|-------------|
| `/status` | Show all running and queued sessions |
| `/halt` | Kill all running sessions |
| `/halt <id>` | Kill a specific session |
| `/queue` | Show pending task queue |
| `/history` | Show last 20 completed sessions |
| `/history <id>` | Show full output of a specific session |
| `/voice on` | Enable push-to-talk voice input |
| `/voice off` | Disable voice |
| `/focus <id>` | Expand a session panel to see live output |
| `/unfocus` | Collapse all panels to summary view |
| `/retry <id>` | Re-run a failed or interrupted session |
| `/resume` | Resume all interrupted sessions from last run |
| `/config` | Show current configuration |
| `/config <key> <value>` | Update a configuration value |
| `/help` | Show available commands and skills |
| `/quit` | Graceful shutdown |

### 7.4 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit command |
| `Up/Down` | Cycle command history |
| `Tab` | Auto-complete skill name |
| `F5` | Push-to-talk (hold to record) |
| `Ctrl+C` | Interrupt focused session / double-tap to quit |
| `Ctrl+L` | Clear screen |
| `Esc` | Unfocus / cancel current input |

---

## Appendix A: Entry Point (index.tsx)

```tsx
#!/usr/bin/env node
import { render } from 'ink';
import React from 'react';
import { App } from './ui/App.js';
import { Orchestrator } from './core/orchestrator.js';
import { SessionManager } from './core/session-manager.js';
import { StateManager } from './core/state.js';
import { SkillRegistry } from './core/skill-registry.js';

async function main() {
  const state = new StateManager('./coco.db');
  state.initialize();

  const skillRegistry = new SkillRegistry();
  await skillRegistry.loadAll();

  const sessionManager = new SessionManager(state, 5);
  const orchestrator = new Orchestrator(sessionManager, skillRegistry, state);

  await orchestrator.startup();

  const { waitUntilExit } = render(
    <App
      orchestrator={orchestrator}
      sessionManager={sessionManager}
      state={state}
    />
  );

  await waitUntilExit();
  await orchestrator.shutdown();
}

main().catch(console.error);
```

## Appendix B: Configuration Defaults

```typescript
// Stored in SQLite context table, overridable via /config
const DEFAULTS = {
  'max_concurrency': '5',
  'voice_enabled': 'false',
  'voice_engine': 'say',
  'voice_name': 'Samantha',
  'voice_rate': '200',
  'whisper_model': 'base.en',
  'push_to_talk_key': 'F5',
  'output_truncate_kb': '10',
  'prune_days': '30',
  'rate_limit_backoff_base_ms': '1000',
  'rate_limit_backoff_max_ms': '30000',
  'confirmation_for_writes': 'true',
  'classification_confidence_threshold': '0.7',
};
```

## Appendix C: Build Phases (from RESEARCH.md, with spec mapping)

| Phase | Modules | Est. Effort |
|-------|---------|-------------|
| 0 — Shell POC | None (standalone script) | 1 day |
| 1 — Core app | `index.tsx`, `orchestrator.ts`, `session-manager.ts`, `state.ts`, `skill-registry.ts`, `App.tsx`, `CommandInput.tsx`, `StatusBar.tsx` | 3-4 days |
| 2 — Parallel + dashboard | `SessionPanel.tsx`, concurrency in `session-manager.ts`, `intent-classifier.ts` | 3-4 days |
| 3 — Voice | `listener.ts`, `speaker.ts`, F5 keybinding | 2-3 days |
| 4 — Smart routing | `intent-classifier.ts` Tier 2, `team-router.ts`, `gsd-router.ts`, `email-router.ts` | 3-5 days |
| 5 — Proactive mode | File watchers, email triggers, scheduled tasks | Ongoing |
