import Database from 'better-sqlite3';
import { randomUUID } from 'node:crypto';
import { unlinkSync } from 'node:fs';

// --- Row types ---

export interface SessionRow {
  id: string;
  skill: string;
  args: string;
  status: 'queued' | 'running' | 'complete' | 'error' | 'interrupted' | 'rate-limited' | 'detached';
  cwd: string;
  output: string;
  summary: string | null;
  started_at: number | null;
  completed_at: number | null;
  created_at: number;
}

export interface EventRow {
  id?: number;
  session_id: string | null;
  type: string;
  payload: string;
  created_at?: number;
}

export interface InputHistoryRow {
  id?: number;
  text: string;
  created_at?: number;
}

export interface SkillUsageRow {
  skill: string;
  count: number;
  last_used_at: number;
}

// --- State Manager ---

export class StateManager {
  private db: Database.Database;

  constructor(dbPath: string) {
    try {
      this.db = new Database(dbPath);
    } catch {
      // Stale WAL/SHM files from a killed process — delete and retry
      try { unlinkSync(dbPath + '-wal'); } catch {}
      try { unlinkSync(dbPath + '-shm'); } catch {}
      this.db = new Database(dbPath);
    }
    this.db.pragma('journal_mode = WAL');
    this.db.pragma('foreign_keys = ON');
  }

  initialize(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        id            TEXT PRIMARY KEY,
        skill         TEXT NOT NULL,
        args          TEXT NOT NULL DEFAULT '',
        status        TEXT NOT NULL DEFAULT 'queued',
        cwd           TEXT NOT NULL,
        output        TEXT NOT NULL DEFAULT '',
        summary       TEXT,
        started_at    INTEGER,
        exit_code     INTEGER,
        completed_at  INTEGER,
        created_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );

      CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
      CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);

      CREATE TABLE IF NOT EXISTS events (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id    TEXT,
        type          TEXT NOT NULL,
        payload       TEXT NOT NULL DEFAULT '{}',
        created_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
      );

      CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
      CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);

      CREATE TABLE IF NOT EXISTS context (
        key           TEXT PRIMARY KEY,
        value         TEXT NOT NULL,
        updated_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );

      CREATE TABLE IF NOT EXISTS input_history (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        text          TEXT NOT NULL,
        created_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );

      CREATE INDEX IF NOT EXISTS idx_input_history_created ON input_history(created_at DESC);

      CREATE TABLE IF NOT EXISTS skill_usage (
        skill         TEXT PRIMARY KEY,
        count         INTEGER NOT NULL DEFAULT 0,
        last_used_at  INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );
    `);

    // --- Phase 2 additions ---

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

    this.initializePhase4();
  }

  // --- Sessions ---

  createSession(skill: string, args: string, cwd: string): string {
    const id = randomUUID();
    this.db.prepare(`
      INSERT INTO sessions (id, skill, args, cwd, status, started_at)
      VALUES (?, ?, ?, ?, 'running', ?)
    `).run(id, skill, args, cwd, Date.now());
    return id;
  }

  getSession(id: string): SessionRow | undefined {
    return this.db.prepare('SELECT * FROM sessions WHERE id = ?').get(id) as SessionRow | undefined;
  }

  getActiveSessions(): SessionRow[] {
    return this.db.prepare(
      "SELECT * FROM sessions WHERE status IN ('running', 'queued') ORDER BY created_at DESC"
    ).all() as SessionRow[];
  }

  getRecentSessions(limit: number = 50): SessionRow[] {
    return this.db.prepare(
      'SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?'
    ).all(limit) as SessionRow[];
  }

  updateSessionStatus(id: string, status: string, output?: string, summary?: string): void {
    if (output !== undefined && summary !== undefined) {
      this.db.prepare(
        'UPDATE sessions SET status = ?, output = ?, summary = ?, completed_at = ? WHERE id = ?'
      ).run(status, output, summary, Date.now(), id);
    } else if (output !== undefined) {
      this.db.prepare(
        'UPDATE sessions SET status = ?, output = ?, completed_at = ? WHERE id = ?'
      ).run(status, output, Date.now(), id);
    } else {
      this.db.prepare(
        'UPDATE sessions SET status = ?, completed_at = ? WHERE id = ?'
      ).run(status, Date.now(), id);
    }
  }

  appendSessionOutput(id: string, chunk: string): void {
    // Append to output, keeping only last ~10KB
    const session = this.getSession(id);
    if (!session) return;
    let newOutput = session.output + chunk;
    if (newOutput.length > 10240) {
      newOutput = newOutput.slice(-10240);
    }
    this.db.prepare('UPDATE sessions SET output = ? WHERE id = ?').run(newOutput, id);
  }

  // --- Events ---

  logEvent(sessionId: string | null, type: string, payload: Record<string, unknown> = {}): void {
    this.db.prepare(
      'INSERT INTO events (session_id, type, payload) VALUES (?, ?, ?)'
    ).run(sessionId, type, JSON.stringify(payload));
  }

  getRecentEvents(limit: number = 100): EventRow[] {
    return this.db.prepare(
      'SELECT * FROM events ORDER BY created_at DESC LIMIT ?'
    ).all(limit) as EventRow[];
  }

  // --- Context (key-value) ---

  setContext(key: string, value: string): void {
    this.db.prepare(
      'INSERT OR REPLACE INTO context (key, value, updated_at) VALUES (?, ?, ?)'
    ).run(key, value, Date.now());
  }

  getContext(key: string): string | undefined {
    const row = this.db.prepare('SELECT value FROM context WHERE key = ?').get(key) as { value: string } | undefined;
    return row?.value;
  }

  // --- Input History ---

  addInputHistory(text: string): void {
    this.db.prepare('INSERT INTO input_history (text) VALUES (?)').run(text);
  }

  getInputHistory(limit: number = 50): string[] {
    const rows = this.db.prepare(
      'SELECT text FROM input_history ORDER BY id DESC LIMIT ?'
    ).all(limit) as { text: string }[];
    return rows.map(r => r.text).reverse(); // oldest first
  }

  // --- Skill Usage ---

  incrementSkillUsage(skill: string): void {
    this.db.prepare(`
      INSERT INTO skill_usage (skill, count, last_used_at)
      VALUES (?, 1, ?)
      ON CONFLICT(skill) DO UPDATE SET count = count + 1, last_used_at = ?
    `).run(skill, Date.now(), Date.now());
  }

  getSkillUsage(): SkillUsageRow[] {
    return this.db.prepare(
      'SELECT * FROM skill_usage ORDER BY count DESC'
    ).all() as SkillUsageRow[];
  }

  // --- Cleanup ---

  prune(daysToKeep: number = 30): number {
    const cutoff = Date.now() - (daysToKeep * 24 * 60 * 60 * 1000);
    const result = this.db.prepare('DELETE FROM events WHERE created_at < ?').run(cutoff);
    return result.changes;
  }

  // --- Interrupted session recovery ---

  markRunningAsInterrupted(): number {
    const result = this.db.prepare(
      "UPDATE sessions SET status = 'interrupted' WHERE status = 'running'"
    ).run();
    return result.changes;
  }

  getInterruptedSessions(): SessionRow[] {
    return this.db.prepare(
      "SELECT * FROM sessions WHERE status = 'interrupted' ORDER BY created_at DESC"
    ).all() as SessionRow[];
  }

  // --- Phase 2: Session creation with caller-supplied ID ---

  createSessionWithId(id: string, skill: string, args: string, cwd: string): void {
    this.db.prepare(`
      INSERT INTO sessions (id, skill, args, cwd, status, created_at)
      VALUES (?, ?, ?, ?, 'queued', unixepoch() * 1000)
    `).run(id, skill, args, cwd);
  }

  // --- Phase 2: Task Queue CRUD ---

  enqueueTask(skill: string, args: string, cwd: string, priority: number = 0, dependsOn?: string): string {
    const id = randomUUID();
    this.db.prepare(`
      INSERT INTO task_queue (id, skill, args, cwd, priority, depends_on, status)
      VALUES (?, ?, ?, ?, ?, ?, 'pending')
    `).run(id, skill, args, cwd, priority, dependsOn || null);
    return id;
  }

  dequeueTask(): { id: string; skill: string; args: string; cwd: string; depends_on: string | null } | undefined {
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
    const maxRow = this.db.prepare(
      "SELECT MAX(priority) as max_p FROM task_queue WHERE status = 'pending'"
    ).get() as { max_p: number | null };
    const newPriority = (maxRow.max_p ?? 0) + 1;
    this.db.prepare("UPDATE task_queue SET priority = ? WHERE id = ?").run(newPriority, id);
  }

  // --- Phase 2: Session detach/reattach ---

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

  // --- Phase 4: Intelligence Layer tables ---

  initializePhase4(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS intent_log (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        input_text    TEXT NOT NULL,
        input_normalized TEXT NOT NULL,
        tier          INTEGER NOT NULL,
        skill_matched TEXT,
        confidence    REAL NOT NULL,
        was_corrected INTEGER NOT NULL DEFAULT 0,
        created_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );
      CREATE INDEX IF NOT EXISTS idx_intent_log_input ON intent_log(input_normalized);
      CREATE INDEX IF NOT EXISTS idx_intent_log_created ON intent_log(created_at DESC);

      CREATE TABLE IF NOT EXISTS routing_corrections (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        input_normalized TEXT NOT NULL,
        wrong_skill   TEXT NOT NULL,
        correct_skill TEXT NOT NULL,
        times_applied INTEGER NOT NULL DEFAULT 0,
        created_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        UNIQUE(input_normalized, correct_skill)
      );
      CREATE INDEX IF NOT EXISTS idx_corrections_input ON routing_corrections(input_normalized);

      CREATE TABLE IF NOT EXISTS skill_sequences (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_a       TEXT NOT NULL,
        skill_b       TEXT NOT NULL,
        count         INTEGER NOT NULL DEFAULT 1,
        last_seen     INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        UNIQUE(skill_a, skill_b)
      );
      CREATE INDEX IF NOT EXISTS idx_sequences_a ON skill_sequences(skill_a);

      CREATE TABLE IF NOT EXISTS session_summaries (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id    TEXT NOT NULL,
        summary       TEXT NOT NULL,
        exchange_count INTEGER NOT NULL,
        created_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
      );
      CREATE INDEX IF NOT EXISTS idx_summaries_session ON session_summaries(session_id);

      CREATE TABLE IF NOT EXISTS user_preferences (
        key           TEXT PRIMARY KEY,
        value         TEXT NOT NULL,
        source        TEXT NOT NULL DEFAULT 'learned',
        confidence    REAL NOT NULL DEFAULT 0.5,
        updated_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );
    `);
  }

  // --- Phase 4: Intent log ---

  logIntent(input: string, normalized: string, tier: number, skill: string | null, confidence: number): number {
    const result = this.db.prepare(`
      INSERT INTO intent_log (input_text, input_normalized, tier, skill_matched, confidence, created_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(input, normalized, tier, skill, confidence, Date.now());
    return Number(result.lastInsertRowid);
  }

  markIntentCorrected(intentId: number): void {
    this.db.prepare('UPDATE intent_log SET was_corrected = 1 WHERE id = ?').run(intentId);
  }

  getLastIntentLog(): { id: number; input_normalized: string; skill_matched: string | null } | undefined {
    return this.db.prepare(
      'SELECT id, input_normalized, skill_matched FROM intent_log ORDER BY id DESC LIMIT 1'
    ).get() as any;
  }

  getIntentLogById(id: number): { id: number; input_normalized: string; skill_matched: string | null } | undefined {
    return this.db.prepare(
      'SELECT id, input_normalized, skill_matched FROM intent_log WHERE id = ?'
    ).get(id) as any;
  }

  // --- Phase 4: Routing corrections ---

  getCorrection(normalizedInput: string): { id: number; correct_skill: string } | undefined {
    return this.db.prepare(
      'SELECT id, correct_skill FROM routing_corrections WHERE input_normalized = ? ORDER BY created_at DESC LIMIT 1'
    ).get(normalizedInput) as any;
  }

  addCorrection(normalizedInput: string, wrongSkill: string, correctSkill: string): void {
    this.db.prepare(`
      INSERT INTO routing_corrections (input_normalized, wrong_skill, correct_skill, created_at)
      VALUES (?, ?, ?, ?)
      ON CONFLICT(input_normalized, correct_skill) DO UPDATE SET
        wrong_skill = excluded.wrong_skill,
        times_applied = 0,
        created_at = excluded.created_at
    `).run(normalizedInput, wrongSkill, correctSkill, Date.now());
  }

  incrementCorrectionUsage(id: number): void {
    this.db.prepare('UPDATE routing_corrections SET times_applied = times_applied + 1 WHERE id = ?').run(id);
  }

  // --- Phase 4: Skill sequences ---

  recordSequence(skillA: string, skillB: string): void {
    this.db.prepare(`
      INSERT INTO skill_sequences (skill_a, skill_b, count, last_seen)
      VALUES (?, ?, 1, ?)
      ON CONFLICT(skill_a, skill_b) DO UPDATE SET
        count = count + 1,
        last_seen = excluded.last_seen
    `).run(skillA, skillB, Date.now());
  }

  getTopSequence(skillA: string): { skill_b: string; count: number } | undefined {
    return this.db.prepare(
      'SELECT skill_b, count FROM skill_sequences WHERE skill_a = ? ORDER BY count DESC LIMIT 1'
    ).get(skillA) as any;
  }

  // --- Phase 4: Session summaries ---

  saveSummary(sessionId: string, summary: string, exchangeCount: number): void {
    this.db.prepare(`
      INSERT INTO session_summaries (session_id, summary, exchange_count, created_at)
      VALUES (?, ?, ?, ?)
    `).run(sessionId, summary, exchangeCount, Date.now());
  }

  getRecentSummaries(limit: number = 2): { summary: string; created_at: number }[] {
    return this.db.prepare(
      'SELECT summary, created_at FROM session_summaries ORDER BY created_at DESC LIMIT ?'
    ).all(limit) as any[];
  }

  // --- Phase 4: User preferences ---

  setPreference(key: string, value: string, source: string = 'learned', confidence: number = 0.5): void {
    this.db.prepare(`
      INSERT INTO user_preferences (key, value, source, confidence, updated_at)
      VALUES (?, ?, ?, ?, ?)
      ON CONFLICT(key) DO UPDATE SET
        value = excluded.value,
        source = excluded.source,
        confidence = excluded.confidence,
        updated_at = excluded.updated_at
    `).run(key, value, source, confidence, Date.now());
  }

  getPreference(key: string): { value: string; confidence: number } | undefined {
    return this.db.prepare(
      'SELECT value, confidence FROM user_preferences WHERE key = ?'
    ).get(key) as any;
  }

  /**
   * Expose the underlying database instance for shared use (e.g., ProactiveEngine).
   * Avoids opening duplicate SQLite connections to the same file.
   */
  getDatabase(): Database.Database {
    return this.db;
  }

  close(): void {
    this.db.close();
  }
}
