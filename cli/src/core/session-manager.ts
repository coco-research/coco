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
  /** @internal rate-limit retry counter (not persisted) */
  _rateLimitAttempt?: number;
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

    // Add to p-queue -- executes when a concurrency slot opens
    this.queue.add(async () => {
      await this.executeSession(session, skill);
    }, { signal: session.abortController.signal }).catch((err: any) => {
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
   * Detach a running session.
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
      // Use execa array form to avoid shell injection
      const subprocess = execa('claude', [
        '-p',
        '--system-prompt', systemPromptWithSkill,
        '--output-format', 'text',
        prompt,
      ], {
        cwd: session.cwd,
        timeout: 600_000, // 10 minute timeout
        buffer: true,
        reject: false,     // Don't throw on non-zero exit
        cancelSignal: session.abortController.signal,
        stdin: 'ignore',   // Close stdin so claude -p doesn't wait for input
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
   */
  private handleSessionOutput(session: Session, text: string, isError: boolean): void {
    // Buffer the output (keep last 100 lines)
    const lines = text.split('\n').filter(l => l.trim());
    session.outputBuffer.push(...lines);
    if (session.outputBuffer.length > 100) {
      session.outputBuffer = session.outputBuffer.slice(-100);
    }

    // Persist to SQLite
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
   * Rate limit handler: exponential backoff with re-enqueue (no recursion).
   */
  private static readonly MAX_RATE_LIMIT_RETRIES = 5;

  private async handleRateLimit(
    session: Session,
    skill: { name: string; command: string; description: string }
  ): Promise<void> {
    this.consecutiveRateLimits++;
    const attempt = session._rateLimitAttempt = (session._rateLimitAttempt ?? 0) + 1;

    session.status = 'rate-limited';
    this.state.logEvent(session.id, 'rate_limited', {
      consecutive: this.consecutiveRateLimits,
      attempt,
    });

    if (attempt >= SessionManager.MAX_RATE_LIMIT_RETRIES) {
      session.status = 'error';
      this.state.updateSessionStatus(session.id, 'error', 'Rate limit retries exhausted');
      this.emit('sessionError', {
        sessionId: session.id,
        error: `Rate limited ${SessionManager.MAX_RATE_LIMIT_RETRIES} times -- giving up`,
      });
      return;
    }

    if (this.consecutiveRateLimits >= 3) {
      this.rateLimitCooldownUntil = Date.now() + 60_000;
      this.state.logEvent(null, 'global_rate_limit_cooldown', { durationMs: 60_000 });
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, ..., max 30s
    const baseMs = 1000;
    const backoffMs = Math.min(
      baseMs * Math.pow(2, this.consecutiveRateLimits - 1),
      30_000
    );
    const jitter = backoffMs * 0.2 * (Math.random() * 2 - 1);
    const waitMs = Math.round(backoffMs + jitter);

    // Re-enqueue into p-queue after delay (non-recursive)
    setTimeout(() => {
      session.status = 'queued';
      session.outputBuffer = [];
      this.queue.add(async () => {
        await this.executeSession(session, skill);
      }, { signal: session.abortController.signal }).catch((err: any) => {
        if (err.name !== 'AbortError') {
          session.status = 'error';
          this.state.updateSessionStatus(session.id, 'error', err.message);
          this.emit('sessionError', { sessionId: session.id, error: err.message });
        }
      });
    }, waitMs);
  }

  /**
   * Generate a one-line summary from session output.
   */
  private generateSummary(session: Session): string {
    const output = session.outputBuffer.join('\n');

    const summaryMatch = output.match(/## Summary\n(.+)/);
    if (summaryMatch) return summaryMatch[1].trim();

    const headlineMatch = output.match(/^## (.+)/m);
    if (headlineMatch) return headlineMatch[1].trim();

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
