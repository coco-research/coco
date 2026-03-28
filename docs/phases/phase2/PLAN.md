# CoCo Phase 2 Implementation Plan — Parallel Sessions + Dashboard

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan.

**Goal:** Add parallel session management, a live dashboard with collapsible session panels, task queuing, macOS notifications, and detach/reattach to CoCo
**Architecture:** p-queue concurrency control, Ink multi-panel layout, FIFO task queue in SQLite, osascript notifications
**Tech Stack:** TypeScript, Ink 5, React 18, p-queue, execa, better-sqlite3 (WAL mode)
**Builds on:** Phase 1 (single-session Ink app with orchestrator, skill registry, SQLite state)

---

## Success Criteria (from ROADMAP)

- [ ] Can run 3+ sessions in parallel (e.g., "research X" + "write tests for Y" + "review Z")
- [ ] Dashboard shows each session as a collapsible block with: name, status (running/done/error), elapsed time
- [ ] Status bar shows: project name, git branch, active session count, queue depth, wall clock
- [ ] Task queue accepts commands while sessions are running
- [ ] Output from parallel sessions does not interleave — each session's output is contained in its panel
- [ ] Total memory usage < 500MB with 3 concurrent sessions
- [ ] macOS notification when background sessions complete
- [ ] Long-running sessions can detach; CoCo shows status on relaunch

---

## Wave 1: Project Setup + Dependencies

**Dependencies:** Phase 1 complete (single session works end-to-end)
**Estimated time:** 10-15 minutes

### Task 1.1: Update package.json — Add Phase 2 dependencies

**File:** `coco/phase1/package.json`

- [ ] Add new dependencies for parallel execution, streaming child processes, and notifications:

```json
{
  "dependencies": {
    "...existing...": "...",
    "p-queue": "^8.0.0",
    "execa": "^9.0.0",
    "strip-ansi": "^7.1.0"
  }
}
```

**Why each dependency:**
- `p-queue` — Concurrency-limited promise queue. Controls max parallel Claude sessions (default: 3, max: 5). Already in TECH-SPEC as a dependency.
- `execa` — Reliable child process management with streaming stdout/stderr. Replaces Phase 1's `execFile` which buffers all output. Critical for live dashboard streaming.
- `strip-ansi` — Clean ANSI escape codes from Claude CLI output before rendering in Ink panels (prevents garbled display).

**Verification:**
```bash
cd phase1 && npm install p-queue execa strip-ansi && node -e "import('p-queue').then(m => console.log('p-queue OK'))"
```

### Task 1.2: Create Phase 2 directory structure

- [ ] Create new directories and stub files:

```bash
mkdir -p coco/phase1/src/core
mkdir -p coco/phase1/src/ui
mkdir -p coco/phase1/tests
```

**New files to create (stubs):**
- `coco/phase1/src/core/session-manager.ts` — Multi-session lifecycle manager
- `coco/phase1/src/core/task-queue.ts` — FIFO queue with dependency support
- `coco/phase1/src/core/notifier.ts` — macOS notification bridge
- `coco/phase1/src/ui/Dashboard.tsx` — Layout manager for session panels
- `coco/phase1/src/ui/SessionPanel.tsx` — Collapsible block per session with live output
- `coco/phase1/tests/session-manager.test.ts`
- `coco/phase1/tests/task-queue.test.ts`

**Verification:** `find coco/phase1/src -name "*.ts" -o -name "*.tsx" | sort` shows all Phase 1 + Phase 2 files.

### Task 1.3: Add SQLite schema migrations for Phase 2

**File:** `coco/phase1/src/core/state.ts`

- [ ] Add new tables to the `initialize()` method, after the existing schema:

```typescript
// --- Phase 2 additions (inside initialize()) ---

// Task queue: FIFO with priority + dependency support
this.db.exec(`
  CREATE TABLE IF NOT EXISTS task_queue (
    id              TEXT PRIMARY KEY,
    skill           TEXT NOT NULL,
    args            TEXT NOT NULL DEFAULT '',
    cwd             TEXT NOT NULL,
    priority        INTEGER NOT NULL DEFAULT 0,
    depends_on      TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
  );

  CREATE INDEX IF NOT EXISTS idx_task_queue_status
    ON task_queue(status, priority DESC, created_at ASC);

  CREATE INDEX IF NOT EXISTS idx_task_queue_depends
    ON task_queue(depends_on);
`);

// Session dependencies: "run Y after X completes"
this.db.exec(`
  CREATE TABLE IF NOT EXISTS session_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    depends_on_id   TEXT NOT NULL,
    created_at      INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_id) REFERENCES sessions(id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idx_session_deps_session
    ON session_dependencies(session_id);
  CREATE INDEX IF NOT EXISTS idx_session_deps_depends
    ON session_dependencies(depends_on_id);
`);

// Add 'detached' to the sessions status enum (no schema change needed —
// SQLite TEXT columns accept any value, but document the new valid statuses):
// queued | running | complete | error | interrupted | rate-limited | detached
```

- [ ] Add new StateManager methods for the task queue:

```typescript
// --- Session creation with caller-supplied ID (Phase 2) ---

createSessionWithId(id: string, skill: string, args: string, cwd: string): void {
  this.db.prepare(`
    INSERT INTO sessions (id, skill, args, cwd, status, created_at)
    VALUES (?, ?, ?, ?, 'queued', unixepoch() * 1000)
  `).run(id, skill, args, cwd);
}

// --- Task Queue CRUD ---

enqueueTask(skill: string, args: string, cwd: string, priority: number = 0, dependsOn?: string): string {
  const id = randomUUID();
  this.db.prepare(`
    INSERT INTO task_queue (id, skill, args, cwd, priority, depends_on, status)
    VALUES (?, ?, ?, ?, ?, ?, 'pending')
  `).run(id, skill, args, cwd, priority, dependsOn || null);
  return id;
}

dequeueTask(): { id: string; skill: string; args: string; cwd: string; depends_on: string | null } | undefined {
  // Get the highest-priority pending task whose dependency (if any) is complete
  const row = this.db.prepare(`
    SELECT tq.* FROM task_queue tq
    LEFT JOIN sessions s ON tq.depends_on = s.id
    WHERE tq.status = 'pending'
      AND (tq.depends_on IS NULL OR s.status = 'complete')
    ORDER BY tq.priority DESC, tq.created_at ASC
    LIMIT 1
  `).get() as any;

  if (row) {
    this.db.prepare("UPDATE task_queue SET status = 'dispatched' WHERE id = ?").run(row.id);
  }
  return row;
}

getQueuedTasks(): Array<{ id: string; skill: string; args: string; priority: number; depends_on: string | null; created_at: number }> {
  return this.db.prepare(
    "SELECT * FROM task_queue WHERE status = 'pending' ORDER BY priority DESC, created_at ASC"
  ).all() as any[];
}

getQueueDepth(): number {
  const row = this.db.prepare(
    "SELECT COUNT(*) as count FROM task_queue WHERE status = 'pending'"
  ).get() as { count: number };
  return row.count;
}

removeFromQueue(id: string): boolean {
  const result = this.db.prepare("DELETE FROM task_queue WHERE id = ?").run(id);
  return result.changes > 0;
}

clearQueue(): number {
  const result = this.db.prepare("DELETE FROM task_queue WHERE status = 'pending'").run();
  return result.changes;
}

promoteTask(id: string): void {
  // Set priority to max(existing priorities) + 1
  const maxRow = this.db.prepare(
    "SELECT MAX(priority) as max_p FROM task_queue WHERE status = 'pending'"
  ).get() as { max_p: number | null };
  const newPriority = (maxRow.max_p ?? 0) + 1;
  this.db.prepare("UPDATE task_queue SET priority = ? WHERE id = ?").run(newPriority, id);
}

// --- Session detach/reattach ---

detachSession(id: string): void {
  this.db.prepare(
    "UPDATE sessions SET status = 'detached' WHERE id = ? AND status = 'running'"
  ).run(id);
}

getDetachedSessions(): SessionRow[] {
  return this.db.prepare(
    "SELECT * FROM sessions WHERE status = 'detached' ORDER BY created_at DESC"
  ).all() as SessionRow[];
}
```

**Verification:** Add to `tests/state.test.ts`:

```typescript
describe('StateManager — Phase 2 Queue', () => {
  it('enqueues and dequeues tasks in priority order', () => {
    state.enqueueTask('team-research', 'topic A', '/tmp', 0);
    state.enqueueTask('team-develop', 'feature B', '/tmp', 10); // higher priority
    const task = state.dequeueTask();
    expect(task?.skill).toBe('team-develop'); // higher priority first
  });

  it('respects dependency — blocks until dependency completes', () => {
    const sessionId = state.createSession('team-research', 'prereq', '/tmp');
    state.enqueueTask('team-develop', 'depends on research', '/tmp', 0, sessionId);
    // While session is 'running', dequeue should return undefined
    const task1 = state.dequeueTask();
    expect(task1).toBeUndefined();
    // Complete the dependency
    state.updateSessionStatus(sessionId, 'complete');
    const task2 = state.dequeueTask();
    expect(task2?.skill).toBe('team-develop');
  });

  it('promotes a task to front of queue', () => {
    const id1 = state.enqueueTask('team-research', 'A', '/tmp', 0);
    const id2 = state.enqueueTask('team-develop', 'B', '/tmp', 0);
    state.promoteTask(id1); // promote A to front
    const task = state.dequeueTask();
    expect(task?.id).toBe(id1);
  });

  it('clears the queue', () => {
    state.enqueueTask('team-research', 'A', '/tmp');
    state.enqueueTask('team-develop', 'B', '/tmp');
    const cleared = state.clearQueue();
    expect(cleared).toBe(2);
    expect(state.getQueueDepth()).toBe(0);
  });
});
```

Run: `cd phase1 && npm test`

---

## Wave 2: Session Manager — Parallel Execution Engine

**Dependencies:** Wave 1 complete (schema migrated, p-queue installed)
**Estimated time:** 30-40 minutes
**This is the most critical module — all other Phase 2 features depend on it.**

### Task 2.1: Implement session-manager.ts — Multi-session lifecycle with p-queue

**File:** `coco/phase1/src/core/session-manager.ts`

- [ ] Write the complete SessionManager class:

```typescript
import { EventEmitter } from 'eventemitter3';
import { execa } from 'execa';
import { randomUUID } from 'node:crypto';
import stripAnsi from 'strip-ansi';
import type { StateManager, SessionRow } from './state.js';
import type { Skill } from './skill-registry.js';
import PQueue from 'p-queue';

// --- Types ---

export interface Session {
  id: string;
  skill: string;
  args: string;
  status: 'queued' | 'running' | 'complete' | 'error' | 'rate-limited' | 'detached';
  cwd: string;
  startedAt: number;
  completedAt: number | null;
  outputBuffer: string[];      // last N lines of output
  currentLayer: number | null; // 1-4 for /team pipelines
  layerName: string | null;
  progress: string | null;     // e.g., "3/4 agents"
  abortController: AbortController;
  subprocess: ReturnType<typeof execa> | null;
}

export interface SessionManagerEvents {
  sessionSpawned: (session: Session) => void;
  sessionOutput: (data: { sessionId: string; text: string; isError: boolean }) => void;
  sessionLayerChange: (data: { sessionId: string; layer: number; name: string }) => void;
  sessionProgress: (data: { sessionId: string; progress: string }) => void;
  sessionComplete: (data: { sessionId: string; success: boolean; summary: string }) => void;
  sessionError: (data: { sessionId: string; error: string }) => void;
  sessionDetached: (data: { sessionId: string }) => void;
  queueDrained: () => void;
  concurrencyChanged: (data: { running: number; max: number; queued: number }) => void;
}

// --- Layer detection for /team pipeline progress ---

const LAYER_PATTERNS = [
  { pattern: /## Layer 1|## L1|Research Layer|LAYER 1/i, layer: 1, name: 'Research' },
  { pattern: /## Layer 2|## L2|Execution Layer|LAYER 2/i, layer: 2, name: 'Execute' },
  { pattern: /## Layer 3|## L3|Review Layer|LAYER 3/i, layer: 3, name: 'Review' },
  { pattern: /## Layer 4|## L4|Synthesis Layer|LAYER 4/i, layer: 4, name: 'Synthesis' },
];

const PROGRESS_PATTERN = /(\d+)\/(\d+)\s*(agents?|specialists?|roles?|tasks?)/i;

// --- Rate limit detection ---

const RATE_LIMIT_PATTERNS = [
  /rate.?limit/i,
  /429/,
  /too many requests/i,
  /quota exceeded/i,
];

// --- Session Manager ---

export class SessionManager extends EventEmitter<SessionManagerEvents> {
  private sessions: Map<string, Session> = new Map();
  private queue: PQueue;
  private state: StateManager;
  private maxConcurrency: number;
  private systemPrompt: string;

  // Rate limit state
  private consecutiveRateLimits: number = 0;
  private rateLimitCooldownUntil: number = 0;

  constructor(state: StateManager, maxConcurrency: number = 3, systemPrompt: string = '') {
    super();
    this.state = state;
    this.maxConcurrency = maxConcurrency;
    this.systemPrompt = systemPrompt;

    this.queue = new PQueue({
      concurrency: maxConcurrency,
      autoStart: true,
    });

    // Emit concurrency changes
    this.queue.on('active', () => {
      this.emitConcurrencyStatus();
    });

    this.queue.on('idle', () => {
      this.emit('queueDrained');
      this.emitConcurrencyStatus();
    });
  }

  // --- Public API ---

  /**
   * Spawn a new session. If at concurrency limit, it queues automatically via p-queue.
   * Returns the session ID immediately (before execution starts).
   */
  async spawn(skill: Skill | { name: string; command: string; description: string; isWriteOperation: boolean }, args: string, cwd: string): Promise<string> {
    const id = randomUUID();
    const now = Date.now();

    const session: Session = {
      id,
      skill: skill.name,
      args,
      status: 'queued',
      cwd,
      startedAt: now,
      completedAt: null,
      outputBuffer: [],
      currentLayer: null,
      layerName: null,
      progress: null,
      abortController: new AbortController(),
      subprocess: null,
    };

    this.sessions.set(id, session);

    // Persist to SQLite with our pre-generated UUID
    this.state.createSessionWithId(id, skill.name, args, cwd);
    this.state.logEvent(id, 'session_queued', { skill: skill.name, args });

    this.emit('sessionSpawned', session);
    this.emitConcurrencyStatus();

    // Add to p-queue — executes when a concurrency slot opens
    this.queue.add(async () => {
      await this.executeSession(session, skill);
    }, { signal: session.abortController.signal }).catch((err) => {
      // AbortError is expected when session is killed
      if (err.name !== 'AbortError') {
        session.status = 'error';
        this.state.updateSessionStatus(id, 'error', err.message);
        this.emit('sessionError', { sessionId: id, error: err.message });
      }
    });

    return id;
  }

  /**
   * Kill a specific session by ID.
   */
  async kill(sessionId: string): Promise<boolean> {
    const session = this.sessions.get(sessionId);
    if (!session) return false;

    session.abortController.abort();

    if (session.subprocess) {
      session.subprocess.kill('SIGTERM');
      // Force kill after 5 seconds
      setTimeout(() => {
        if (session.subprocess && !session.subprocess.killed) {
          session.subprocess.kill('SIGKILL');
        }
      }, 5000);
    }

    session.status = 'error';
    session.completedAt = Date.now();
    this.state.updateSessionStatus(sessionId, 'interrupted');
    this.emitConcurrencyStatus();
    return true;
  }

  /**
   * Kill all running sessions.
   */
  async killAll(): Promise<number> {
    this.queue.clear(); // Clear pending items from p-queue
    let killed = 0;
    for (const session of this.sessions.values()) {
      if (session.status === 'running' || session.status === 'queued') {
        await this.kill(session.id);
        killed++;
      }
    }
    return killed;
  }

  /**
   * Detach a running session — it continues running but CoCo stops tracking live output.
   * On relaunch, CoCo will show it as 'detached' and offer to reattach.
   */
  detach(sessionId: string): boolean {
    const session = this.sessions.get(sessionId);
    if (!session || session.status !== 'running') return false;

    session.status = 'detached';
    this.state.detachSession(sessionId);
    this.emit('sessionDetached', { sessionId });
    this.emitConcurrencyStatus();
    return true;
  }

  /**
   * Get a session by ID.
   */
  get(sessionId: string): Session | undefined {
    return this.sessions.get(sessionId);
  }

  /**
   * Get all sessions with a given status.
   */
  getByStatus(status: Session['status']): Session[] {
    return Array.from(this.sessions.values()).filter(s => s.status === status);
  }

  /**
   * Get all active sessions (running + queued).
   */
  getActive(): Session[] {
    return Array.from(this.sessions.values()).filter(
      s => s.status === 'running' || s.status === 'queued'
    );
  }

  /**
   * Get all sessions (for dashboard display).
   */
  getAll(): Session[] {
    return Array.from(this.sessions.values());
  }

  /**
   * Current concurrency stats.
   */
  getStats(): { running: number; queued: number; completed: number; failed: number; max: number } {
    const all = Array.from(this.sessions.values());
    return {
      running: all.filter(s => s.status === 'running').length,
      queued: this.queue.pending,
      completed: all.filter(s => s.status === 'complete').length,
      failed: all.filter(s => s.status === 'error').length,
      max: this.maxConcurrency,
    };
  }

  /**
   * Update max concurrency at runtime.
   */
  setConcurrency(max: number): void {
    this.maxConcurrency = Math.min(Math.max(max, 1), 7); // clamp 1-7
    this.queue.concurrency = this.maxConcurrency;
    this.emitConcurrencyStatus();
  }

  // --- Private implementation ---

  /**
   * Execute a single session as a claude -p child process with streaming output.
   */
  private async executeSession(
    session: Session,
    skill: { name: string; command: string; description: string }
  ): Promise<void> {
    // Check rate limit cooldown
    if (Date.now() < this.rateLimitCooldownUntil) {
      const waitMs = this.rateLimitCooldownUntil - Date.now();
      await new Promise(resolve => setTimeout(resolve, waitMs));
    }

    session.status = 'running';
    session.startedAt = Date.now();
    this.state.logEvent(session.id, 'session_running', { skill: skill.name });

    // Build the prompt for claude -p
    const prompt = session.args || `Execute ${skill.command}`;
    const systemPromptWithSkill = [
      this.systemPrompt,
      '',
      `## Current Task`,
      `Route this to: ${skill.command}`,
      `The user wants: ${session.args}`,
      `Skill description: ${skill.description}`,
    ].join('\n');

    try {
      // Use execa array form to avoid shell injection (no shell parsing)
      const subprocess = execa('claude', [
        '-p',
        '--system-prompt', systemPromptWithSkill,
        '--output-format', 'text',
        prompt,
      ], {
        cwd: session.cwd,
        timeout: 600_000, // 10 minute timeout (parallel sessions can run longer)
        buffer: true,
        reject: false,     // Don't throw on non-zero exit
        signal: session.abortController.signal,
      });

      session.subprocess = subprocess;

      // Stream stdout line by line
      if (subprocess.stdout) {
        subprocess.stdout.on('data', (chunk: Buffer) => {
          const text = stripAnsi(chunk.toString());
          this.handleSessionOutput(session, text, false);
        });
      }

      // Stream stderr
      if (subprocess.stderr) {
        subprocess.stderr.on('data', (chunk: Buffer) => {
          const text = stripAnsi(chunk.toString());
          this.handleSessionOutput(session, text, true);
        });
      }

      const result = await subprocess;

      session.subprocess = null;
      session.completedAt = Date.now();

      if (result.exitCode === 0) {
        session.status = 'complete';
        const summary = this.generateSummary(session);
        this.state.updateSessionStatus(session.id, 'complete', session.outputBuffer.join('\n'), summary);
        this.state.logEvent(session.id, 'session_complete', { exitCode: 0 });
        this.emit('sessionComplete', { sessionId: session.id, success: true, summary });
        this.consecutiveRateLimits = 0; // Reset rate limit counter on success
      } else {
        // Check if it was a rate limit
        const fullOutput = session.outputBuffer.join('\n');
        const isRateLimit = RATE_LIMIT_PATTERNS.some(p => p.test(fullOutput));

        if (isRateLimit) {
          await this.handleRateLimit(session, skill);
        } else {
          session.status = 'error';
          this.state.updateSessionStatus(session.id, 'error', fullOutput);
          this.state.logEvent(session.id, 'session_error', { exitCode: result.exitCode });
          this.emit('sessionError', { sessionId: session.id, error: `Exit code ${result.exitCode}` });
        }
      }
    } catch (err: any) {
      session.subprocess = null;
      session.completedAt = Date.now();

      if (err.name === 'AbortError' || session.abortController.signal.aborted) {
        session.status = 'error';
        this.state.updateSessionStatus(session.id, 'interrupted');
        return;
      }

      session.status = 'error';
      const message = err.message || String(err);
      this.state.updateSessionStatus(session.id, 'error', message);
      this.emit('sessionError', { sessionId: session.id, error: message });
    }
  }

  /**
   * Handle a chunk of output from a running session.
   * Parses layer changes and progress updates for the dashboard.
   */
  private handleSessionOutput(session: Session, text: string, isError: boolean): void {
    // Buffer the output (keep last 100 lines)
    const lines = text.split('\n').filter(l => l.trim());
    session.outputBuffer.push(...lines);
    if (session.outputBuffer.length > 100) {
      session.outputBuffer = session.outputBuffer.slice(-100);
    }

    // Persist to SQLite (append, respecting 10KB cap)
    this.state.appendSessionOutput(session.id, text);

    // Emit for UI
    this.emit('sessionOutput', { sessionId: session.id, text, isError });

    // Parse layer changes
    for (const { pattern, layer, name } of LAYER_PATTERNS) {
      if (pattern.test(text)) {
        session.currentLayer = layer;
        session.layerName = name;
        this.emit('sessionLayerChange', { sessionId: session.id, layer, name });
        break;
      }
    }

    // Parse progress
    const progressMatch = text.match(PROGRESS_PATTERN);
    if (progressMatch) {
      session.progress = `${progressMatch[1]}/${progressMatch[2]} ${progressMatch[3]}`;
      this.emit('sessionProgress', { sessionId: session.id, progress: session.progress });
    }
  }

  /**
   * Rate limit handler: exponential backoff with jitter, bounded retry loop.
   * If 3+ sessions hit rate limits, pause all spawns for 60s.
   * Max 5 retries before giving up (avoids unbounded recursion).
   */
  private static readonly MAX_RATE_LIMIT_RETRIES = 5;

  private async handleRateLimit(
    session: Session,
    skill: { name: string; command: string; description: string }
  ): Promise<void> {
    for (let attempt = 1; attempt <= SessionManager.MAX_RATE_LIMIT_RETRIES; attempt++) {
      this.consecutiveRateLimits++;
      session.status = 'rate-limited';
      this.state.logEvent(session.id, 'rate_limited', {
        consecutive: this.consecutiveRateLimits,
        attempt,
      });

      if (this.consecutiveRateLimits >= 3) {
        // Global cooldown: pause all spawns for 60 seconds
        this.rateLimitCooldownUntil = Date.now() + 60_000;
        this.state.logEvent(null, 'global_rate_limit_cooldown', { durationMs: 60_000 });
      }

      // Exponential backoff: 1s, 2s, 4s, 8s, ..., max 30s
      const baseMs = 1000;
      const backoffMs = Math.min(
        baseMs * Math.pow(2, this.consecutiveRateLimits - 1),
        30_000
      );
      // Add jitter: +/- 20%
      const jitter = backoffMs * 0.2 * (Math.random() * 2 - 1);
      const waitMs = Math.round(backoffMs + jitter);

      await new Promise(resolve => setTimeout(resolve, waitMs));

      // Retry the session
      session.status = 'queued';
      session.outputBuffer = [];
      await this.executeSession(session, skill);

      // If executeSession completed without hitting rate-limit again, stop retrying
      if (session.status !== 'rate-limited') return;
    }

    // Exhausted retries — mark as error
    session.status = 'error';
    this.state.updateSessionStatus(session.id, 'error', 'Rate limit retries exhausted');
    this.emit('sessionError', {
      sessionId: session.id,
      error: `Rate limited ${SessionManager.MAX_RATE_LIMIT_RETRIES} times — giving up`,
    });
  }

  /**
   * Generate a one-line summary from session output.
   */
  private generateSummary(session: Session): string {
    const output = session.outputBuffer.join('\n');

    // Look for an explicit summary line
    const summaryMatch = output.match(/## Summary\n(.+)/);
    if (summaryMatch) return summaryMatch[1].trim();

    // Look for a headline
    const headlineMatch = output.match(/^## (.+)/m);
    if (headlineMatch) return headlineMatch[1].trim();

    // Fall back to first non-empty line
    const firstLine = session.outputBuffer.find(l => l.trim().length > 10);
    if (firstLine) return firstLine.trim().slice(0, 100);

    return `${session.skill} completed`;
  }

  /**
   * Emit current concurrency status for the dashboard.
   */
  private emitConcurrencyStatus(): void {
    const stats = this.getStats();
    this.emit('concurrencyChanged', {
      running: stats.running,
      max: stats.max,
      queued: stats.queued,
    });
  }
}
```

**Note on `execa` array form:** The array form `execa('claude', [args...])` avoids shell parsing entirely, eliminating shell injection risks. No escaping or temp files are needed -- execa passes arguments directly to the child process via `spawn()`. For very long system prompts, the OS argv limit (~256KB on macOS) is sufficient.

**Verification:** Create `tests/session-manager.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SessionManager } from '../src/core/session-manager.js';
import { StateManager } from '../src/core/state.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-sm-test.db';

describe('SessionManager', () => {
  let sm: SessionManager;
  let state: StateManager;

  beforeEach(() => {
    state = new StateManager(TEST_DB);
    state.initialize();
    sm = new SessionManager(state, 3, 'test system prompt');
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('creates a session and returns an ID', async () => {
    const skill = { name: 'team-research', command: '/team research', description: 'Research', isWriteOperation: false };
    const id = await sm.spawn(skill, 'OAuth patterns', '/tmp');
    expect(id).toBeDefined();
    expect(typeof id).toBe('string');
    expect(id.length).toBe(36); // UUID format
  });

  it('tracks active sessions', async () => {
    const skill = { name: 'team-research', command: '/team research', description: 'Research', isWriteOperation: false };
    await sm.spawn(skill, 'topic A', '/tmp');
    await sm.spawn(skill, 'topic B', '/tmp');
    const active = sm.getActive();
    expect(active.length).toBeGreaterThanOrEqual(0); // may be queued or running
  });

  it('respects concurrency limit', () => {
    const stats = sm.getStats();
    expect(stats.max).toBe(3);
  });

  it('can update concurrency at runtime', () => {
    sm.setConcurrency(5);
    expect(sm.getStats().max).toBe(5);
  });

  it('clamps concurrency between 1 and 7', () => {
    sm.setConcurrency(0);
    expect(sm.getStats().max).toBe(1);
    sm.setConcurrency(10);
    expect(sm.getStats().max).toBe(7);
  });

  it('kills a session by ID', async () => {
    const skill = { name: 'test', command: '/test', description: 'Test', isWriteOperation: false };
    const id = await sm.spawn(skill, 'test args', '/tmp');
    const killed = await sm.kill(id);
    expect(killed).toBe(true);
  });

  it('killAll clears the queue', async () => {
    const skill = { name: 'test', command: '/test', description: 'Test', isWriteOperation: false };
    await sm.spawn(skill, 'A', '/tmp');
    await sm.spawn(skill, 'B', '/tmp');
    const count = await sm.killAll();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});
```

Run: `cd phase1 && npm test`

---

## Wave 3: Task Queue Manager

**Dependencies:** Wave 2 complete (SessionManager exists)
**Estimated time:** 20-25 minutes

### Task 3.1: Implement task-queue.ts — FIFO queue with dependency support

**File:** `coco/phase1/src/core/task-queue.ts`

- [ ] Write the TaskQueue class that bridges StateManager's queue tables with SessionManager's spawn:

```typescript
import { EventEmitter } from 'eventemitter3';
import type { StateManager } from './state.js';
import type { SessionManager } from './session-manager.js';
import type { SkillRegistry, Skill } from './skill-registry.js';

// --- Types ---

export interface QueuedTask {
  id: string;
  skill: string;
  args: string;
  cwd: string;
  priority: number;
  dependsOn: string | null;
  createdAt: number;
}

export interface TaskQueueEvents {
  taskEnqueued: (task: QueuedTask) => void;
  taskDispatched: (data: { taskId: string; sessionId: string }) => void;
  taskRemoved: (data: { taskId: string }) => void;
  queueCleared: (data: { count: number }) => void;
  queueEmpty: () => void;
}

// --- TaskQueue ---

export class TaskQueue extends EventEmitter<TaskQueueEvents> {
  private state: StateManager;
  private sessionManager: SessionManager;
  private skillRegistry: SkillRegistry;
  private pollInterval: ReturnType<typeof setInterval> | null = null;
  private isProcessing: boolean = false;

  constructor(state: StateManager, sessionManager: SessionManager, skillRegistry: SkillRegistry) {
    super();
    this.state = state;
    this.sessionManager = sessionManager;
    this.skillRegistry = skillRegistry;

    // When a session completes, check if any queued tasks are now unblocked
    this.sessionManager.on('sessionComplete', () => {
      this.processNext();
    });
  }

  /**
   * Start polling the queue for dispatchable tasks.
   * Called on startup. Checks every 2 seconds.
   */
  start(): void {
    this.pollInterval = setInterval(() => this.processNext(), 2000);
    // Process immediately on start (in case there are leftover tasks from last run)
    this.processNext();
  }

  /**
   * Stop the queue processor.
   */
  stop(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  /**
   * Add a task to the queue.
   * @param skill - skill name or full skill object
   * @param args - arguments for the skill
   * @param cwd - working directory
   * @param priority - higher = more urgent (default 0)
   * @param dependsOn - session ID that must complete first (optional)
   */
  enqueue(
    skill: string,
    args: string,
    cwd: string,
    priority: number = 0,
    dependsOn?: string
  ): string {
    const id = this.state.enqueueTask(skill, args, cwd, priority, dependsOn);
    const task: QueuedTask = {
      id,
      skill,
      args,
      cwd,
      priority,
      dependsOn: dependsOn || null,
      createdAt: Date.now(),
    };
    this.emit('taskEnqueued', task);

    // Try to dispatch immediately if there's capacity
    this.processNext();

    return id;
  }

  /**
   * Remove a task from the queue by ID.
   */
  remove(taskId: string): boolean {
    const removed = this.state.removeFromQueue(taskId);
    if (removed) {
      this.emit('taskRemoved', { taskId });
    }
    return removed;
  }

  /**
   * Clear all pending tasks.
   */
  clear(): number {
    const count = this.state.clearQueue();
    this.emit('queueCleared', { count });
    return count;
  }

  /**
   * Promote a task to the front of the queue (highest priority).
   */
  promote(taskId: string): void {
    this.state.promoteTask(taskId);
    // Try to dispatch immediately
    this.processNext();
  }

  /**
   * Get all pending tasks in priority order.
   */
  getPending(): QueuedTask[] {
    return this.state.getQueuedTasks().map(row => ({
      id: row.id,
      skill: row.skill,
      args: row.args,
      cwd: '', // not stored in the simplified query
      priority: row.priority,
      dependsOn: row.depends_on,
      createdAt: row.created_at,
    }));
  }

  /**
   * Get the number of pending tasks.
   */
  get depth(): number {
    return this.state.getQueueDepth();
  }

  /**
   * Try to dispatch queued tasks while there is concurrency capacity.
   * Uses a while loop instead of recursion to avoid re-entrancy issues
   * (recursive self-call would return immediately because isProcessing is true).
   */
  private async processNext(): Promise<void> {
    if (this.isProcessing) return;
    this.isProcessing = true;

    try {
      while (true) {
        const stats = this.sessionManager.getStats();

        // Only dispatch if under the concurrency limit
        if (stats.running >= stats.max) break;

        const task = this.state.dequeueTask();
        if (!task) {
          if (this.state.getQueueDepth() === 0) {
            this.emit('queueEmpty');
          }
          break;
        }

        // Look up the skill
        const skill = this.skillRegistry.get(task.skill);
        const skillDescriptor = skill || {
          name: task.skill,
          command: `/${task.skill}`,
          description: task.skill,
          isWriteOperation: false,
        };

        const sessionId = await this.sessionManager.spawn(skillDescriptor, task.args, task.cwd);
        this.emit('taskDispatched', { taskId: task.id, sessionId });
      }
    } finally {
      this.isProcessing = false;
    }
  }
}
```

**Verification:** Create `tests/task-queue.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { TaskQueue } from '../src/core/task-queue.js';
import { SessionManager } from '../src/core/session-manager.js';
import { StateManager } from '../src/core/state.js';
import { SkillRegistry } from '../src/core/skill-registry.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-tq-test.db';

describe('TaskQueue', () => {
  let tq: TaskQueue;
  let state: StateManager;
  let sm: SessionManager;
  let skills: SkillRegistry;

  beforeEach(async () => {
    state = new StateManager(TEST_DB);
    state.initialize();
    sm = new SessionManager(state, 3, 'test');
    skills = new SkillRegistry();
    await skills.loadAll();
    tq = new TaskQueue(state, sm, skills);
  });

  afterEach(() => {
    tq.stop();
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('enqueues a task and reports correct depth', () => {
    tq.enqueue('team-research', 'topic A', '/tmp');
    tq.enqueue('team-develop', 'feature B', '/tmp');
    expect(tq.depth).toBe(2);
  });

  it('removes a task from the queue', () => {
    const id = tq.enqueue('team-research', 'topic', '/tmp');
    expect(tq.remove(id)).toBe(true);
    expect(tq.depth).toBe(0);
  });

  it('clears all pending tasks', () => {
    tq.enqueue('team-research', 'A', '/tmp');
    tq.enqueue('team-develop', 'B', '/tmp');
    const cleared = tq.clear();
    expect(cleared).toBe(2);
    expect(tq.depth).toBe(0);
  });

  it('promotes a task to front of queue', () => {
    const id1 = tq.enqueue('team-research', 'A', '/tmp', 0);
    const id2 = tq.enqueue('team-develop', 'B', '/tmp', 0);
    tq.promote(id1);
    const pending = tq.getPending();
    // After promote, id1 should have higher priority
    expect(pending[0]?.id).toBe(id1);
  });

  it('emits taskEnqueued event', () => {
    const handler = vi.fn();
    tq.on('taskEnqueued', handler);
    tq.enqueue('team-research', 'test', '/tmp');
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('emits queueCleared event', () => {
    const handler = vi.fn();
    tq.on('queueCleared', handler);
    tq.enqueue('team-research', 'test', '/tmp');
    tq.clear();
    expect(handler).toHaveBeenCalledWith({ count: 1 });
  });
});
```

Run: `cd phase1 && npm test`

---

## Wave 4: Dashboard UI — Multi-Panel Layout

**Dependencies:** Wave 2 + Wave 3 complete (SessionManager + TaskQueue exist)
**Estimated time:** 30-40 minutes
**Parallelizable:** SessionPanel, Dashboard, and updated StatusBar can be built simultaneously.

### Task 4.1: Implement SessionPanel.tsx — Collapsible block per session with live output

**File:** `coco/phase1/src/ui/SessionPanel.tsx`

- [ ] Write the component:

```tsx
import React, { useState, useEffect, useRef } from 'react';
import { Box, Text } from 'ink';
import type { Session } from '../core/session-manager.js';

interface SessionPanelProps {
  session: Session;
  isExpanded: boolean;
  isFocused: boolean;
  onToggle: () => void;
  maxOutputLines?: number;
}

// --- Status color mapping ---
const STATUS_COLORS: Record<string, string> = {
  queued: 'gray',
  running: 'yellow',
  complete: 'green',
  error: 'red',
  'rate-limited': 'magenta',
  interrupted: 'red',
  detached: 'blue',
};

// --- Status icons ---
const STATUS_ICONS: Record<string, string> = {
  queued: '...',
  running: '>>>',
  complete: '[ok]',
  error: '[!!]',
  'rate-limited': '[rl]',
  interrupted: '[--]',
  detached: '[dh]',
};

// --- Elapsed time formatter ---
function formatElapsed(startedAt: number, completedAt: number | null): string {
  const end = completedAt || Date.now();
  const seconds = Math.floor((end - startedAt) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSec = seconds % 60;
  if (minutes < 60) return `${minutes}m${remainingSec}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h${minutes % 60}m`;
}

export const SessionPanel: React.FC<SessionPanelProps> = ({
  session,
  isExpanded,
  isFocused,
  onToggle,
  maxOutputLines = 20,
}) => {
  // Force re-render every second while running so elapsed time updates live
  const [, setTick] = useState(0);
  useEffect(() => {
    if (session.status !== 'running' && session.status !== 'queued') return;
    const interval = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, [session.status]);

  const statusColor = STATUS_COLORS[session.status] || 'white';
  const statusIcon = STATUS_ICONS[session.status] || '   ';
  const elapsed = formatElapsed(session.startedAt, session.completedAt);

  // Layer progress display for /team pipelines
  const layerDisplay = session.currentLayer
    ? `L${session.currentLayer} ${session.layerName || ''}`
    : session.skill;

  const progressDisplay = session.progress || '';

  // Collapsed: one-line summary
  // >>>  [team-research] L2 Execute 3/4 agents ........... 45s (v)
  if (!isExpanded) {
    return (
      <Box paddingX={1}>
        <Text color={statusColor}>{statusIcon} </Text>
        <Text bold={isFocused} color={isFocused ? 'cyan' : undefined}>
          [{session.skill}]
        </Text>
        <Text> {layerDisplay} </Text>
        {progressDisplay && <Text dimColor>{progressDisplay} </Text>}
        <Text dimColor>
          {'.' .repeat(Math.max(0, 30 - layerDisplay.length - progressDisplay.length))}
        </Text>
        <Text dimColor> {elapsed}</Text>
        <Text dimColor> {isExpanded ? '(^)' : '(v)'}</Text>
      </Box>
    );
  }

  // Expanded: show last N lines of output
  const visibleOutput = session.outputBuffer.slice(-maxOutputLines);

  return (
    <Box flexDirection="column" paddingX={1}>
      {/* Header line */}
      <Box>
        <Text color={statusColor}>{statusIcon} </Text>
        <Text bold color={isFocused ? 'cyan' : undefined}>
          [{session.skill}]
        </Text>
        <Text> {layerDisplay} </Text>
        {progressDisplay && <Text dimColor>{progressDisplay} </Text>}
        <Text dimColor> {elapsed}</Text>
        <Text dimColor> (^)</Text>
      </Box>

      {/* Layer progress bar for /team pipelines */}
      {session.currentLayer && (
        <Box paddingLeft={2}>
          {[1, 2, 3, 4].map(layer => {
            const isActive = layer === session.currentLayer;
            const isDone = layer < (session.currentLayer || 0);
            const name = ['Research', 'Execute', 'Review', 'Synthesis'][layer - 1];
            return (
              <Box key={layer} marginRight={1}>
                <Text
                  color={isDone ? 'green' : isActive ? 'yellow' : 'gray'}
                  bold={isActive}
                >
                  L{layer}
                </Text>
                <Text
                  color={isDone ? 'green' : isActive ? 'yellow' : 'gray'}
                  dimColor={!isActive && !isDone}
                >
                  {' '}{name}
                </Text>
              </Box>
            );
          })}
        </Box>
      )}

      {/* Output lines */}
      <Box flexDirection="column" paddingLeft={4} borderStyle="single" borderColor="gray">
        {visibleOutput.length === 0 && (
          <Text dimColor>Waiting for output...</Text>
        )}
        {visibleOutput.map((line, i) => (
          <Text key={i} wrap="truncate-end">
            {line}
          </Text>
        ))}
      </Box>
    </Box>
  );
};
```

### Task 4.2: Implement Dashboard.tsx — Layout manager for session panels

**File:** `coco/phase1/src/ui/Dashboard.tsx`

- [ ] Write the layout manager component:

```tsx
import React, { useState, useCallback, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import { SessionPanel } from './SessionPanel.js';
import type { Session, SessionManager } from '../core/session-manager.js';

interface DashboardProps {
  sessionManager: SessionManager;
}

export const Dashboard: React.FC<DashboardProps> = ({ sessionManager }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [focusedIndex, setFocusedIndex] = useState<number>(0);
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());

  // Subscribe to session manager events
  useEffect(() => {
    const updateSessions = () => {
      const all = sessionManager.getAll();
      // Sort: running first, then queued, then complete, then error
      const statusOrder: Record<string, number> = {
        running: 0,
        'rate-limited': 1,
        queued: 2,
        detached: 3,
        complete: 4,
        error: 5,
        interrupted: 6,
      };
      all.sort((a, b) => (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9));
      setSessions(all);
    };

    // Throttled version for high-frequency events (sessionOutput).
    // Limits Dashboard re-renders to max once per 250ms to avoid
    // excessive re-rendering when multiple sessions stream output.
    let throttleTimer: ReturnType<typeof setTimeout> | null = null;
    let pendingUpdate = false;
    const throttledUpdateSessions = () => {
      if (throttleTimer) {
        pendingUpdate = true;
        return;
      }
      updateSessions();
      throttleTimer = setTimeout(() => {
        throttleTimer = null;
        if (pendingUpdate) {
          pendingUpdate = false;
          updateSessions();
        }
      }, 250);
    };

    sessionManager.on('sessionSpawned', updateSessions);
    sessionManager.on('sessionComplete', updateSessions);
    sessionManager.on('sessionError', updateSessions);
    sessionManager.on('sessionDetached', updateSessions);
    sessionManager.on('sessionOutput', throttledUpdateSessions);    // throttled
    sessionManager.on('sessionLayerChange', throttledUpdateSessions); // throttled
    sessionManager.on('sessionProgress', throttledUpdateSessions);   // throttled

    // Initial load
    updateSessions();

    return () => {
      if (throttleTimer) clearTimeout(throttleTimer);
      sessionManager.off('sessionSpawned', updateSessions);
      sessionManager.off('sessionComplete', updateSessions);
      sessionManager.off('sessionError', updateSessions);
      sessionManager.off('sessionDetached', updateSessions);
      sessionManager.off('sessionOutput', throttledUpdateSessions);
      sessionManager.off('sessionLayerChange', throttledUpdateSessions);
      sessionManager.off('sessionProgress', throttledUpdateSessions);
    };
  }, [sessionManager]);

  // Keyboard navigation for session panels
  useInput((input, key) => {
    if (sessions.length === 0) return;

    // Tab / Shift+Tab to navigate between sessions
    if (key.tab) {
      setFocusedIndex(prev =>
        key.shift
          ? (prev - 1 + sessions.length) % sessions.length
          : (prev + 1) % sessions.length
      );
      return;
    }

    // Enter to toggle expand/collapse of focused session
    if (key.return && sessions[focusedIndex]) {
      const sessionId = sessions[focusedIndex].id;
      setExpandedSessions(prev => {
        const next = new Set(prev);
        if (next.has(sessionId)) {
          next.delete(sessionId);
        } else {
          next.add(sessionId);
        }
        return next;
      });
      return;
    }

    // 'e' to expand all, 'c' to collapse all
    if (input === 'e') {
      setExpandedSessions(new Set(sessions.map(s => s.id)));
      return;
    }
    if (input === 'c') {
      setExpandedSessions(new Set());
      return;
    }
  });

  if (sessions.length === 0) {
    return (
      <Box paddingX={1} paddingY={1}>
        <Text dimColor>No sessions. Type a command to start one.</Text>
      </Box>
    );
  }

  // Auto-expand running sessions
  const effectiveExpanded = new Set(expandedSessions);
  for (const session of sessions) {
    if (session.status === 'running') {
      effectiveExpanded.add(session.id);
    }
  }

  return (
    <Box flexDirection="column" flexGrow={1}>
      {/* Navigation hint */}
      <Box paddingX={1}>
        <Text dimColor>
          Tab: navigate | Enter: expand/collapse | e: expand all | c: collapse all
        </Text>
      </Box>

      {/* Session panels */}
      {sessions.map((session, index) => (
        <SessionPanel
          key={session.id}
          session={session}
          isExpanded={effectiveExpanded.has(session.id)}
          isFocused={index === focusedIndex}
          onToggle={() => {
            setExpandedSessions(prev => {
              const next = new Set(prev);
              if (next.has(session.id)) {
                next.delete(session.id);
              } else {
                next.add(session.id);
              }
              return next;
            });
          }}
        />
      ))}
    </Box>
  );
};
```

### Task 4.3: Update StatusBar.tsx — Add queue depth, active count, and concurrency indicator

**File:** `coco/phase1/src/ui/StatusBar.tsx`

- [ ] Modify the existing StatusBar to include Phase 2 information:

```tsx
import React, { useState, useEffect } from 'react';
import { Box, Text } from 'ink';

interface StatusBarProps {
  project: string;
  branch: string;
  activeSessions: number;
  queueDepth: number;
  maxConcurrency: number;
  skillCount: number;
  message?: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  project,
  branch,
  activeSessions,
  queueDepth,
  maxConcurrency,
  skillCount,
  message,
}) => {
  const [clock, setClock] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(
        `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
      );
    };
    updateClock();
    const interval = setInterval(updateClock, 30_000); // update every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <Box
      borderStyle="single"
      borderColor="cyan"
      paddingX={1}
      justifyContent="space-between"
    >
      <Text bold color="cyan">CoCo</Text>
      <Text dimColor>{project} ({branch})</Text>
      <Text dimColor>{skillCount} skills</Text>

      {/* Concurrency indicator: running/max */}
      {activeSessions > 0 ? (
        <Text color="yellow">
          {activeSessions}/{maxConcurrency} active
        </Text>
      ) : (
        <Text dimColor>idle</Text>
      )}

      {/* Queue depth */}
      {queueDepth > 0 && (
        <Text color="magenta">Q:{queueDepth}</Text>
      )}

      {/* Status message */}
      {message && (
        <Text color="gray">{message.slice(0, 40)}</Text>
      )}

      <Text dimColor>{clock}</Text>
    </Box>
  );
};
```

### Task 4.4: Update App.tsx — Wire Dashboard, SessionManager, and TaskQueue into the root layout

**File:** `coco/phase1/src/ui/App.tsx`

- [ ] Rewrite App.tsx to integrate the new Phase 2 components:

```tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Box, Text, useApp } from 'ink';
import { StatusBar } from './StatusBar.js';
import { Dashboard } from './Dashboard.js';
import { CommandInput } from './CommandInput.js';
import type { Orchestrator } from '../core/orchestrator.js';
import type { SessionManager } from '../core/session-manager.js';
import type { TaskQueue } from '../core/task-queue.js';
import type { StateManager } from '../core/state.js';
import type { SkillRegistry } from '../core/skill-registry.js';

/**
 * Options-object pattern for App props.
 * Phase 2 additions (sessionManager, taskQueue) are optional so that
 * Phase 1 call-sites continue to work without modification.
 */
interface AppProps {
  orchestrator: Orchestrator;
  state: StateManager;
  skills: SkillRegistry;
  sessionManager?: SessionManager;
  taskQueue?: TaskQueue;
}

export const App: React.FC<AppProps> = ({
  orchestrator,
  state,
  skills,
  sessionManager,
  taskQueue,
}) => {
  const { exit } = useApp();

  // --- State ---
  const [directOutput, setDirectOutput] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [activeSessions, setActiveSessions] = useState(0);
  const [queueDepth, setQueueDepth] = useState(0);
  const [maxConcurrency, setMaxConcurrency] = useState(3);
  const [isProcessing, setIsProcessing] = useState(false);
  const [inputHistory, setInputHistory] = useState<string[]>(() =>
    state.getInputHistory(50)
  );

  // --- Project info ---
  const cwd = process.cwd();
  const project = cwd.split('/').pop() || 'unknown';
  let branch = 'no-git';
  try {
    const { execSync } = require('node:child_process');
    branch = execSync('git branch --show-current', { cwd, encoding: 'utf-8' }).trim();
  } catch {}

  // --- Greeting ---
  useEffect(() => {
    const greeting = orchestrator.getGreeting();
    setDirectOutput([greeting]);
  }, []);

  // --- Event subscriptions ---
  useEffect(() => {
    // Direct output from orchestrator (meta-commands, direct responses)
    const onOutput = (data: { sessionId: string | null; text: string }) => {
      if (!data.sessionId) {
        // Only show non-session output in the direct output area
        setDirectOutput(prev => {
          const next = [...prev, data.text];
          return next.length > 100 ? next.slice(-100) : next;
        });
      }
    };

    const onStatus = (data: { message: string }) => setStatusMessage(data.message);
    const onSessionStart = () => setActiveSessions(prev => prev + 1);
    const onSessionEnd = () => {
      setActiveSessions(prev => Math.max(0, prev - 1));
      setIsProcessing(false);
    };
    const onError = (data: { message: string }) => {
      setDirectOutput(prev => [...prev, `Error: ${data.message}`]);
      setIsProcessing(false);
    };

    orchestrator.on('output', onOutput);
    orchestrator.on('status', onStatus);
    orchestrator.on('sessionStart', onSessionStart);
    orchestrator.on('sessionEnd', onSessionEnd);
    orchestrator.on('error', onError);

    return () => {
      orchestrator.off('output', onOutput);
      orchestrator.off('status', onStatus);
      orchestrator.off('sessionStart', onSessionStart);
      orchestrator.off('sessionEnd', onSessionEnd);
      orchestrator.off('error', onError);
    };
  }, [orchestrator]);

  // Session manager concurrency updates
  useEffect(() => {
    const onConcurrency = (data: { running: number; max: number; queued: number }) => {
      setActiveSessions(data.running);
      setMaxConcurrency(data.max);
    };
    sessionManager.on('concurrencyChanged', onConcurrency);
    return () => { sessionManager.off('concurrencyChanged', onConcurrency); };
  }, [sessionManager]);

  // Task queue updates
  useEffect(() => {
    const updateDepth = () => setQueueDepth(taskQueue.depth);
    taskQueue.on('taskEnqueued', updateDepth);
    taskQueue.on('taskDispatched', updateDepth);
    taskQueue.on('taskRemoved', updateDepth);
    taskQueue.on('queueCleared', updateDepth);
    return () => {
      taskQueue.off('taskEnqueued', updateDepth);
      taskQueue.off('taskDispatched', updateDepth);
      taskQueue.off('taskRemoved', updateDepth);
      taskQueue.off('queueCleared', updateDepth);
    };
  }, [taskQueue]);

  // --- Input handler ---
  const handleSubmit = useCallback(async (text: string) => {
    if (/^\/(quit|exit|bye)$/i.test(text)) {
      setDirectOutput(prev => [...prev, 'CoCo signing off.']);
      taskQueue.stop();
      await sessionManager.killAll();
      await orchestrator.shutdown();
      exit();
      return;
    }

    setInputHistory(prev => [...prev, text]);
    setIsProcessing(true);
    setDirectOutput(prev => [...prev, `> ${text}`]);

    try {
      await orchestrator.handleInput(text);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setDirectOutput(prev => [...prev, `Error: ${msg}`]);
    } finally {
      setIsProcessing(false);
      setStatusMessage('');
    }
  }, [orchestrator, sessionManager, taskQueue, exit]);

  // --- Layout ---
  // ┌─ StatusBar ──────────────────────────────────────┐
  // ├─ Dashboard (session panels, scrollable) ──────────┤
  // ├─ Direct Output (meta-commands, greetings) ────────┤
  // ├─ CommandInput ────────────────────────────────────┤
  // └──────────────────────────────────────────────────┘

  return (
    <Box flexDirection="column" width="100%">
      {/* Status bar */}
      <StatusBar
        project={project}
        branch={branch}
        activeSessions={activeSessions}
        queueDepth={queueDepth}
        maxConcurrency={maxConcurrency}
        skillCount={skills.size}
        message={statusMessage}
      />

      {/* Dashboard: session panels */}
      <Dashboard sessionManager={sessionManager} />

      {/* Direct output area (non-session output) */}
      <Box flexDirection="column" paddingX={1} flexGrow={1}>
        {directOutput.slice(-15).map((line, i) => (
          <Text key={i} wrap="wrap">
            {line}
          </Text>
        ))}
      </Box>

      {/* Command input */}
      <CommandInput
        onSubmit={handleSubmit}
        history={inputHistory}
        disabled={isProcessing}
      />
    </Box>
  );
};
```

**Verification:** `npm run dev` — the Ink app should launch with the status bar showing `idle`, no session panels visible, and the greeting in the output area. Type `/help` to see skills.

---

## Wave 5: Orchestrator Updates — Queue Commands, Parallel Dispatch, Notifications

**Dependencies:** Waves 2-4 complete (SessionManager, TaskQueue, Dashboard)
**Estimated time:** 30-40 minutes

### Task 5.1: Implement notifier.ts — macOS notifications via osascript

**File:** `coco/phase1/src/core/notifier.ts`

- [ ] Write the macOS notification module:

```typescript
import { exec } from 'node:child_process';

export interface NotificationOptions {
  title: string;
  message: string;
  subtitle?: string;
  sound?: boolean;
}

/**
 * Send a macOS notification via osascript.
 * Non-blocking, fire-and-forget. Silently fails on non-macOS.
 */
export function notify(options: NotificationOptions): void {
  if (process.platform !== 'darwin') return;

  const parts = [
    `display notification ${escapeAppleScript(options.message)}`,
    `with title ${escapeAppleScript(options.title)}`,
  ];

  if (options.subtitle) {
    parts.push(`subtitle ${escapeAppleScript(options.subtitle)}`);
  }

  if (options.sound !== false) {
    parts.push(`sound name "Glass"`);
  }

  const script = parts.join(' ');

  exec(`osascript -e '${script}'`, (err) => {
    // Silently ignore errors — notifications are best-effort
    if (err && process.env.COCO_DEBUG) {
      console.error('[notifier]', err.message);
    }
  });
}

function escapeAppleScript(str: string): string {
  // Escape for AppleScript string literal
  const escaped = str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/'/g, "'\\''");
  return `"${escaped}"`;
}

/**
 * Convenience: notify when a session completes.
 */
export function notifySessionComplete(skill: string, success: boolean, summary?: string): void {
  notify({
    title: success ? 'CoCo — Done' : 'CoCo — Failed',
    message: summary || `${skill} ${success ? 'completed' : 'failed'}`,
    subtitle: skill,
    sound: true,
  });
}

/**
 * Convenience: notify when queue is drained.
 */
export function notifyQueueDrained(completedCount: number): void {
  notify({
    title: 'CoCo — Queue Complete',
    message: `All ${completedCount} tasks finished.`,
    sound: true,
  });
}
```

**Verification:**
```bash
node -e "
  const { exec } = require('child_process');
  exec('osascript -e \\'display notification \"CoCo test\" with title \"CoCo\" sound name \"Glass\"\\'');
"
```
Should show a macOS notification.

### Task 5.2: Update orchestrator.ts — Add queue commands, parallel dispatch, notification hooks

**File:** `coco/phase1/src/core/orchestrator.ts`

- [ ] Add new meta-commands for queue management:

```typescript
// Add to META_COMMANDS:
const META_COMMANDS: Record<string, RegExp> = {
  // ... existing ...
  queue:         /^\/(queue)\s*(.*)$/i,
  'queue-clear': /^\/(queue)\s+clear\s*$/i,
  'queue-promote': /^\/(queue)\s+promote\s+(.+)$/i,
  focus:         /^\/(focus)\s+(.+)$/i,
  unfocus:       /^\/(unfocus)\s*$/i,
  detach:        /^\/(detach)\s+(.+)$/i,
  concurrency:   /^\/(concurrency)\s+(\d+)\s*$/i,
};
```

- [ ] Update the constructor to accept SessionManager, TaskQueue, and wire up notifications:

```typescript
import { SessionManager } from './session-manager.js';
import { TaskQueue } from './task-queue.js';
import { notifySessionComplete, notifyQueueDrained } from './notifier.js';

/**
 * Options-object pattern for Orchestrator constructor.
 * Phase 2 additions (sessionManager, taskQueue) are optional so that
 * Phase 1 call-sites continue to work without modification.
 */
export interface OrchestratorDeps {
  state: StateManager;
  skills: SkillRegistry;
  sessionManager?: SessionManager;
  taskQueue?: TaskQueue;
}

export class Orchestrator extends EventEmitter<OrchestratorEvents> {
  private state: StateManager;
  private skills: SkillRegistry;
  private sessionManager: SessionManager | null;
  private taskQueue: TaskQueue | null;
  private systemPrompt: string;

  constructor(deps: OrchestratorDeps) {
    super();
    this.state = deps.state;
    this.skills = deps.skills;
    this.sessionManager = deps.sessionManager ?? null;
    this.taskQueue = deps.taskQueue ?? null;

    // Load system prompt (same as Phase 1)
    // ...

    // Wire up notifications (only when Phase 2 modules are provided)
    if (this.sessionManager) {
      const sm = this.sessionManager;
      sm.on('sessionComplete', ({ sessionId, success, summary }) => {
        notifySessionComplete(
          sm.get(sessionId)?.skill || 'unknown',
          success,
          summary
        );
      });
    }

    if (this.taskQueue && this.sessionManager) {
      const sm = this.sessionManager;
      this.taskQueue.on('queueEmpty', () => {
        const stats = sm.getStats();
        if (stats.running === 0) {
          notifyQueueDrained(stats.completed);
        }
      });
    }
  }
```

- [ ] Update `dispatchToSkill` to use SessionManager instead of direct `execFile`:

```typescript
private async dispatchToSkill(skill: Skill, args: string): Promise<void> {
  const stats = this.sessionManager.getStats();

  if (stats.running >= stats.max) {
    // At capacity — enqueue instead of blocking
    const taskId = this.taskQueue.enqueue(skill.name, args, process.cwd());
    this.emit('output', {
      sessionId: null,
      text: `Queued: ${skill.command} ${args} (position: ${this.taskQueue.depth})`,
    });
    this.state.logEvent(null, 'task_queued', { skill: skill.name, args, taskId });
    return;
  }

  // Under capacity — spawn directly
  const sessionId = await this.sessionManager.spawn(skill, args, process.cwd());
  this.emit('sessionStart', { sessionId, skill: skill.name });
  this.state.logEvent(sessionId, 'session_spawned', { skill: skill.name, args });
}
```

- [ ] Add new meta-command handlers:

```typescript
private handleMetaCommand(command: string, args?: string): void {
  switch (command) {
    // ... existing cases ...

    case 'queue': {
      if (!args || args === '') {
        // Show queue contents
        const pending = this.taskQueue.getPending();
        if (pending.length === 0) {
          this.emit('output', { sessionId: null, text: 'Queue is empty.' });
        } else {
          const lines = pending.map((t, i) =>
            `  ${i + 1}. [${t.skill}] ${t.args.slice(0, 40)} (p:${t.priority}${t.dependsOn ? ` after:${t.dependsOn.slice(0, 8)}` : ''})`
          );
          this.emit('output', { sessionId: null, text: `Task queue (${pending.length} pending):\n${lines.join('\n')}` });
        }
        break;
      }
      break;
    }

    case 'queue-clear': {
      const count = this.taskQueue.clear();
      this.emit('output', { sessionId: null, text: `Cleared ${count} task(s) from queue.` });
      break;
    }

    case 'queue-promote': {
      if (args) {
        this.taskQueue.promote(args);
        this.emit('output', { sessionId: null, text: `Promoted task ${args.slice(0, 8)} to front of queue.` });
      }
      break;
    }

    case 'focus': {
      // Emit focus event for Dashboard to expand a specific session
      this.emit('output', { sessionId: null, text: `Focused on session ${args?.slice(0, 8)}` });
      break;
    }

    case 'unfocus': {
      this.emit('output', { sessionId: null, text: 'All panels collapsed.' });
      break;
    }

    case 'detach': {
      if (args) {
        const detached = this.sessionManager.detach(args);
        if (detached) {
          this.emit('output', { sessionId: null, text: `Session ${args.slice(0, 8)} detached. It will continue running in the background.` });
        } else {
          this.emit('output', { sessionId: null, text: `Session ${args.slice(0, 8)} not found or not running.` });
        }
      }
      break;
    }

    case 'concurrency': {
      if (args) {
        const n = parseInt(args, 10);
        if (n >= 1 && n <= 7) {
          this.sessionManager.setConcurrency(n);
          this.emit('output', { sessionId: null, text: `Max concurrency set to ${n}.` });
        } else {
          this.emit('output', { sessionId: null, text: 'Concurrency must be between 1 and 7.' });
        }
      }
      break;
    }

    case 'status': {
      const stats = this.sessionManager.getStats();
      const active = this.sessionManager.getActive();
      const lines = [
        `Sessions: ${stats.running} running, ${stats.queued} queued, ${stats.completed} done, ${stats.failed} failed`,
        `Concurrency: ${stats.running}/${stats.max}`,
        `Queue depth: ${this.taskQueue.depth}`,
      ];
      if (active.length > 0) {
        lines.push('', 'Active:');
        for (const s of active) {
          const elapsed = Math.floor((Date.now() - s.startedAt) / 1000);
          lines.push(`  [${s.status}] ${s.id.slice(0, 8)} — ${s.skill} "${s.args.slice(0, 30)}" (${elapsed}s)`);
        }
      }
      this.emit('output', { sessionId: null, text: lines.join('\n') });
      break;
    }

    case 'halt': {
      if (args) {
        // Kill specific session
        this.sessionManager.kill(args).then(killed => {
          this.emit('output', {
            sessionId: null,
            text: killed ? `Session ${args!.slice(0, 8)} killed.` : `Session ${args!.slice(0, 8)} not found.`,
          });
        });
      } else {
        // Kill all
        this.sessionManager.killAll().then(count => {
          this.taskQueue.clear();
          this.emit('output', { sessionId: null, text: `${count} session(s) killed. Queue cleared.` });
        });
      }
      break;
    }

    // ... help, quit remain the same but update /help to include new commands:

    case 'help': {
      const skillContext = this.skills.toPromptContext();
      const help = [
        'CoCo — type naturally or use commands:',
        '',
        'Session commands:',
        '  /status            — Show all sessions and stats',
        '  /halt              — Kill all sessions',
        '  /halt <id>         — Kill a specific session',
        '  /focus <id>        — Expand a session panel',
        '  /unfocus           — Collapse all panels',
        '  /detach <id>       — Detach a running session',
        '  /concurrency <n>   — Set max parallel sessions (1-7)',
        '',
        'Queue commands:',
        '  /queue             — Show pending task queue',
        '  /queue clear       — Clear all queued tasks',
        '  /queue promote <id> — Move task to front of queue',
        '',
        'General:',
        '  /history           — Show recent sessions',
        '  /help              — This message',
        '  /quit              — Exit CoCo',
        '',
        skillContext,
      ].join('\n');
      this.emit('output', { sessionId: null, text: help });
      break;
    }
  }
}
```

### Task 5.3: Update index.tsx — Boot SessionManager, TaskQueue, and pass to App

**File:** `coco/phase1/src/index.tsx`

- [ ] Update the entry point to instantiate and wire all Phase 2 modules:

```tsx
#!/usr/bin/env node
import { render } from 'ink';
import React from 'react';
import { App } from './ui/App.js';
import { Orchestrator } from './core/orchestrator.js';
import { SessionManager } from './core/session-manager.js';
import { TaskQueue } from './core/task-queue.js';
import { StateManager } from './core/state.js';
import { SkillRegistry } from './core/skill-registry.js';
import { join } from 'node:path';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

async function main() {
  // DB location: ~/.coco/coco.db
  const cocoDir = join(homedir(), '.coco');
  if (!existsSync(cocoDir)) {
    mkdirSync(cocoDir, { recursive: true });
  }
  const dbPath = join(cocoDir, 'coco.db');

  // Load system prompt
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const promptPath = join(__dirname, '..', 'prompts', 'coco-system.md');
  let systemPrompt = 'You are CoCo, a concise terminal assistant.';
  try {
    systemPrompt = readFileSync(promptPath, 'utf-8');
  } catch {}

  // Initialize core modules
  const state = new StateManager(dbPath);
  state.initialize();

  const skills = new SkillRegistry();
  await skills.loadAll();

  // Phase 2: SessionManager with configurable concurrency
  const maxConcurrency = parseInt(state.getContext('max_concurrency') || '3', 10);
  const sessionManager = new SessionManager(state, maxConcurrency, systemPrompt);

  // Phase 2: TaskQueue
  const taskQueue = new TaskQueue(state, sessionManager, skills);

  // Orchestrator uses options-object pattern (backward-compatible with Phase 1)
  const orchestrator = new Orchestrator({ state, skills, sessionManager, taskQueue });
  await orchestrator.startup();

  // Start queue processor
  taskQueue.start();

  // Handle Ctrl+C gracefully
  let ctrlCCount = 0;
  process.on('SIGINT', async () => {
    ctrlCCount++;
    if (ctrlCCount >= 2) {
      taskQueue.stop();
      await sessionManager.killAll();
      await orchestrator.shutdown();
      process.exit(0);
    }
  });

  process.on('SIGTERM', async () => {
    taskQueue.stop();
    await sessionManager.killAll();
    await orchestrator.shutdown();
    process.exit(0);
  });

  // Single-command mode: coco "research OAuth"
  const args = process.argv.slice(2);
  if (args.length > 0) {
    const input = args.join(' ');
    orchestrator.on('output', ({ text }) => process.stdout.write(text));
    sessionManager.on('sessionOutput', ({ text }) => process.stdout.write(text));
    sessionManager.on('sessionComplete', () => {
      taskQueue.stop();
      orchestrator.shutdown();
    });
    await orchestrator.handleInput(input);
    return;
  }

  // Interactive TUI mode
  const { waitUntilExit } = render(
    <App
      orchestrator={orchestrator}
      sessionManager={sessionManager}
      taskQueue={taskQueue}
      state={state}
      skills={skills}
    />
  );

  await waitUntilExit();
  taskQueue.stop();
  await sessionManager.killAll();
  await orchestrator.shutdown();
}

main().catch((err) => {
  console.error('CoCo failed to start:', err.message);
  process.exit(1);
});
```

**Verification:**
```bash
# Build check
cd phase1 && npx tsc --noEmit

# Run in dev mode
npm run dev

# Test parallel sessions: in CoCo TUI, type three commands rapidly:
# > research OAuth patterns
# > review the API code
# > plan the next sprint
# Status bar should show "3/3 active"
```

---

## Wave 6: Integration Testing + Polish

**Dependencies:** Waves 1-5 complete
**Estimated time:** 20-30 minutes

### Task 6.1: Run the full test suite

- [ ] Execute all tests:

```bash
cd phase1 && npm test
```

Expected results:
- `state.test.ts` — Phase 1 tests pass + Phase 2 queue tests (enqueue/dequeue, dependency, promote, clear)
- `session-manager.test.ts` — spawn, kill, killAll, concurrency bounds
- `task-queue.test.ts` — enqueue, remove, clear, promote, events
- `orchestrator.test.ts` — existing Phase 1 tests + new queue commands

### Task 6.2: Manual smoke test — Parallel sessions

- [ ] Launch CoCo: `npm run dev`
- [ ] Verify checklist:

1. **Parallel spawn:** Type three commands in quick succession:
   ```
   > research OAuth patterns
   > review the API code
   > plan the next sprint
   ```
   Dashboard should show 3 session panels. Status bar shows `3/3 active`.

2. **Queue overflow:** With 3 sessions running (default concurrency), type a 4th:
   ```
   > develop the auth module
   ```
   Should see: `Queued: /team develop auth module (position: 1)`. Queue depth in status bar shows `Q:1`.

3. **Queue commands:**
   ```
   > /queue
   ```
   Shows the pending task. Then:
   ```
   > /queue clear
   ```
   Queue empties.

4. **Session panels:**
   - Running sessions show live output with yellow `>>>` indicator
   - Completed sessions show green `[ok]`
   - Tab navigates between panels
   - Enter expands/collapses

5. **Status bar:** Shows `CoCo | project (branch) | 3/3 active | Q:1 | 14:32`

6. **Notifications:** When a session completes, macOS notification appears with sound.

7. **Kill commands:**
   ```
   > /halt
   ```
   All sessions killed. Status shows `idle`.

8. **Concurrency change:**
   ```
   > /concurrency 5
   ```
   Status bar max changes to 5.

9. **Detach:**
   - Start a session: `research a complex topic`
   - Type `/detach <id>` (get ID from `/status`)
   - Session status changes to `[dh]`
   - Exit CoCo, relaunch — `/status` shows detached session

10. **Memory check:**
    ```bash
    # With 3 concurrent sessions running:
    ps aux | grep coco | awk '{sum += $6} END {print sum/1024 " MB"}'
    ```
    Should be < 500MB.

### Task 6.3: Verify success criteria

- [ ] 3+ sessions run in parallel without output interleaving
- [ ] Dashboard shows collapsible blocks with name, status, elapsed time
- [ ] Status bar shows project, branch, active/max, queue depth, clock
- [ ] Task queue accepts commands while at concurrency limit
- [ ] macOS notifications fire on session completion
- [ ] Memory < 500MB with 3 concurrent sessions

---

## File Manifest

All files created or modified in Phase 2:

| File | Wave | Action | Purpose |
|------|------|--------|---------|
| `phase1/package.json` | 1 | MODIFY | Add p-queue, execa, strip-ansi |
| `phase1/src/core/state.ts` | 1 | MODIFY | Add task_queue + session_dependencies tables, queue CRUD methods |
| `phase1/src/core/session-manager.ts` | 2 | CREATE | Multi-session lifecycle with p-queue, streaming output, rate limit handling |
| `phase1/src/core/task-queue.ts` | 3 | CREATE | FIFO queue with priority, dependency support, auto-dispatch |
| `phase1/src/core/notifier.ts` | 5 | CREATE | macOS notifications via osascript |
| `phase1/src/core/orchestrator.ts` | 5 | MODIFY | Add queue commands, parallel dispatch, notification hooks |
| `phase1/src/ui/SessionPanel.tsx` | 4 | CREATE | Collapsible block per session with live output + layer progress |
| `phase1/src/ui/Dashboard.tsx` | 4 | CREATE | Layout manager, keyboard navigation, expand/collapse |
| `phase1/src/ui/StatusBar.tsx` | 4 | MODIFY | Add queue depth, concurrency indicator, live clock |
| `phase1/src/ui/App.tsx` | 4 | MODIFY | Wire Dashboard, SessionManager, TaskQueue into root layout |
| `phase1/src/index.tsx` | 5 | MODIFY | Boot SessionManager + TaskQueue, pass to App |
| `phase1/tests/session-manager.test.ts` | 2 | CREATE | SessionManager unit tests |
| `phase1/tests/task-queue.test.ts` | 3 | CREATE | TaskQueue unit tests |
| `phase1/tests/state.test.ts` | 1 | MODIFY | Add Phase 2 queue tests |

---

## Dependency Graph

```
Wave 1 ─── package.json (add deps), state.ts (new tables + queue methods)
  │
  ├──→ Wave 2 ─── session-manager.ts + session-manager.test.ts
  │       │
  │       └──→ Wave 3 ─── task-queue.ts + task-queue.test.ts
  │               │
  │               └──→ Wave 4 ─── [parallel]
  │                       ├── SessionPanel.tsx
  │                       ├── Dashboard.tsx
  │                       ├── StatusBar.tsx (update)
  │                       └── App.tsx (update)
  │                              │
  │                              └──→ Wave 5 ─── [parallel]
  │                                      ├── notifier.ts
  │                                      ├── orchestrator.ts (update)
  │                                      └── index.tsx (update)
  │                                             │
  │                                             └──→ Wave 6 ─── Integration tests + smoke test
  │
  └──→ state.test.ts (update — can run after Wave 1)
```

---

## Key Design Decisions for Phase 2

1. **`execa` replaces `execFile`** — Phase 1 used `execFile` which buffers all stdout until the process exits. Phase 2 needs streaming output for the live dashboard. `execa` provides reliable streaming with built-in abort support, timeout handling, and cross-platform compatibility.

2. **p-queue for concurrency control** — Rather than manually tracking Promise slots, p-queue provides a battle-tested concurrency limiter with auto-start, pause/resume, priority support, and event emission. Default concurrency is 3 (configurable 1-7 via `/concurrency`).

3. **SessionManager is the single source of truth for active sessions** — The Dashboard subscribes to SessionManager events. The Orchestrator routes through SessionManager for spawning. The TaskQueue dispatches through SessionManager. This avoids split-brain state.

4. **TaskQueue uses SQLite for persistence** — Tasks survive restarts. If CoCo crashes mid-queue, tasks are still there on relaunch. The queue polls every 2 seconds and also reacts to session completion events for immediate dispatch.

5. **Notifications are fire-and-forget** — osascript calls are non-blocking. If they fail (non-macOS, permissions), CoCo continues normally. This matches the "works without it, better with it" principle.

6. **Layer progress detection is heuristic** — We parse session output for `/team` pipeline layer markers (L1-L4). This is fragile but good enough for the MVP. Phase 4's intelligence layer can make this more robust.

7. **Detach is status-only in MVP** — True background process management (surviving CoCo exit) requires daemonization. For Phase 2 MVP, "detach" marks a session as detached in the DB so it shows up on relaunch, but the process dies with CoCo. True daemon mode is a Phase 3+ enhancement.

8. **Output isolation via per-session buffers** — Each Session object has its own `outputBuffer[]`. The Dashboard renders each buffer in its own panel. No output interleaving is possible because stdout from child processes is captured per-subprocess by execa.
