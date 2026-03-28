# CoCo Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan.

**Goal:** Replace shell POC with Node.js + Ink app with skill registry, SQLite state, and CoCo personality
**Architecture:** Ink (React-for-terminal) + claude -p child process + better-sqlite3 + gray-matter for command parsing
**Tech Stack:** TypeScript, Ink 5, React 18, better-sqlite3, gray-matter, eventemitter3

---

## Success Criteria (from ROADMAP)

- [ ] `npx coco` or `coco` launches the Ink terminal UI
- [ ] Text input routes to the correct skill with > 80% accuracy on 20 test inputs
- [ ] Skill registry auto-discovers all commands from `~/.claude/commands/` at startup
- [ ] SQLite stores: session history, last 50 exchanges, skill usage counts
- [ ] Session survives Ctrl+C and resumes on next launch
- [ ] CoCo personality produces ambient-style responses

---

## Wave 1: Project Setup

**Dependencies:** None — this is the foundation.
**Estimated time:** 10-15 minutes

### Task 1.1: Create package.json

**File:** `coco/phase1/package.json`

- [ ] Create the file with contents:

```json
{
  "name": "coco",
  "version": "0.1.0",
  "type": "module",
  "bin": {
    "coco": "./dist/index.js"
  },
  "scripts": {
    "dev": "tsx src/index.tsx",
    "build": "tsc && node -e \"const fs=require('fs');const f='dist/index.js';const c=fs.readFileSync(f,'utf8');if(!c.startsWith('#!')){fs.writeFileSync(f,'#!/usr/bin/env node\\n'+c);}\" && chmod +x dist/index.js",
    "start": "node dist/index.js",
    "link": "npm run build && npm link",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "ink": "^5.1.0",
    "ink-spinner": "^5.0.0",
    "react": "^18.3.0",
    "better-sqlite3": "^11.0.0",
    "gray-matter": "^4.0.3",
    "eventemitter3": "^5.0.0",
    "glob": "^11.0.0"
  },
  "devDependencies": {
    "@types/better-sqlite3": "^7.6.0",
    "@types/react": "^18.3.0",
    "tsx": "^4.0.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0"
  }
}
```

**Verification:** `cd phase1 && cat package.json | node -e "JSON.parse(require('fs').readFileSync(0,'utf8'))" && echo "Valid JSON"`

### Task 1.2: Create tsconfig.json

**File:** `coco/phase1/tsconfig.json`

- [ ] Create the file:

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
    "sourceMap": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

**Verification:** `npx tsc --noEmit` (will fail until src exists — that's fine, just confirms tsconfig is valid)

### Task 1.3: Create directory structure

- [ ] Create all directories:

```bash
mkdir -p coco/phase1/src/core
mkdir -p coco/phase1/src/ui
mkdir -p coco/phase1/prompts
mkdir -p coco/phase1/tests
```

**Files to create (empty stubs for now):**
- `coco/phase1/src/core/state.ts`
- `coco/phase1/src/core/skill-registry.ts`
- `coco/phase1/src/core/orchestrator.ts`
- `coco/phase1/src/ui/App.tsx`
- `coco/phase1/src/ui/CommandInput.tsx`
- `coco/phase1/src/ui/StatusBar.tsx`
- `coco/phase1/src/index.tsx`

**Verification:** `find coco/phase1/src -type f | sort` shows all 7 files.

### Task 1.4: Install dependencies

- [ ] Run:

```bash
cd coco/phase1 && npm install
```

**Verification:** `node -e "require('better-sqlite3')"` succeeds. `ls node_modules/ink` exists.

### Task 1.5: Copy and adapt CoCo personality prompt

**File:** `coco/phase1/prompts/coco-system.md`

- [ ] Copy from `phase0/coco-system-prompt.md` and add a new section at the bottom:

```markdown
## Output Format for TUI Mode

When running inside CoCo TUI (not direct CLI):
- Keep responses under 20 lines unless the user asks for detail.
- Use `## Headline` for section breaks — the TUI renders these as collapsible.
- Never use ASCII box art — the TUI provides its own chrome.
- For status updates, emit single lines prefixed with `[status]` — the TUI parses these for the status bar.
- For routing confirmation, emit `[route] /skill-name args` — the TUI shows this as a brief flash.
```

**Verification:** `wc -l coco/phase1/prompts/coco-system.md` > 80 lines (original is ~90 lines + new section).

---

## Wave 2: Core Modules (state.ts, skill-registry.ts)

**Dependencies:** Wave 1 complete (package.json installed, directories exist)
**Estimated time:** 20-30 minutes
**Parallelizable:** state.ts and skill-registry.ts can be built simultaneously.

### Task 2.1: Implement state.ts — SQLite schema + CRUD

**File:** `coco/phase1/src/core/state.ts`

- [ ] Write the complete StateManager class:

```typescript
import Database from 'better-sqlite3';
import { randomUUID } from 'node:crypto';

// --- Row types ---

export interface SessionRow {
  id: string;
  skill: string;
  args: string;
  status: 'queued' | 'running' | 'complete' | 'error' | 'interrupted';
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
    this.db = new Database(dbPath);
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
      'SELECT text FROM input_history ORDER BY created_at DESC LIMIT ?'
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

  close(): void {
    this.db.close();
  }
}
```

**Verification:** Create `tests/state.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { StateManager } from '../src/core/state.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-test.db';

describe('StateManager', () => {
  let state: StateManager;

  beforeEach(() => {
    state = new StateManager(TEST_DB);
    state.initialize();
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('creates and retrieves a session', () => {
    const id = state.createSession('team-research', 'OAuth patterns', '/tmp');
    const session = state.getSession(id);
    expect(session).toBeDefined();
    expect(session!.skill).toBe('team-research');
    expect(session!.status).toBe('running');
  });

  it('tracks skill usage', () => {
    state.incrementSkillUsage('team-research');
    state.incrementSkillUsage('team-research');
    state.incrementSkillUsage('team-develop');
    const usage = state.getSkillUsage();
    expect(usage[0].skill).toBe('team-research');
    expect(usage[0].count).toBe(2);
  });

  it('stores and retrieves input history', () => {
    state.addInputHistory('research OAuth');
    state.addInputHistory('fix the bug');
    const history = state.getInputHistory(10);
    expect(history).toEqual(['research OAuth', 'fix the bug']);
  });

  it('marks running sessions as interrupted', () => {
    state.createSession('team-research', 'test', '/tmp');
    const count = state.markRunningAsInterrupted();
    expect(count).toBe(1);
    const interrupted = state.getInterruptedSessions();
    expect(interrupted.length).toBe(1);
  });

  it('appends output with 10KB cap', () => {
    const id = state.createSession('team-research', 'test', '/tmp');
    const bigChunk = 'x'.repeat(12000);
    state.appendSessionOutput(id, bigChunk);
    const session = state.getSession(id);
    expect(session!.output.length).toBeLessThanOrEqual(10240);
  });
});
```

Run: `cd phase1 && npm test`

### Task 2.2: Implement skill-registry.ts — Auto-discovery from ~/.claude/commands/

**File:** `coco/phase1/src/core/skill-registry.ts`

- [ ] Write the complete SkillRegistry class:

```typescript
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';
import { homedir } from 'node:os';
import matter from 'gray-matter';

export interface Skill {
  name: string;           // e.g., "team-research"
  command: string;        // e.g., "/team research"
  description: string;    // first meaningful line from the file
  filePath: string;       // absolute path
  category: string;       // "team" | "gsd" | "email" | "pmstudio" | "standalone"
  isWriteOperation: boolean;
  keywords: string[];     // extracted trigger words for matching
}

const WRITE_PATTERNS = /\b(develop|fix|execute|build|create|edit|deploy|push|delete|remove|write)\b/i;

export class SkillRegistry {
  private skills: Map<string, Skill> = new Map();
  private keywordIndex: Map<string, string> = new Map(); // keyword -> skill name

  async loadAll(): Promise<void> {
    this.skills.clear();
    this.keywordIndex.clear();

    // Global commands
    const globalDir = join(homedir(), '.claude', 'commands');
    if (existsSync(globalDir)) {
      this.loadDirectory(globalDir);
    }

    // GSD subcommands
    const gsdDir = join(homedir(), '.claude', 'commands', 'gsd');
    if (existsSync(gsdDir)) {
      this.loadDirectory(gsdDir, 'gsd');
    }

    // Project-level commands (cwd)
    const projectDir = join(process.cwd(), '.claude', 'commands');
    if (existsSync(projectDir)) {
      this.loadDirectory(projectDir, 'project');
    }
  }

  private loadDirectory(dir: string, categoryOverride?: string): void {
    const files = readdirSync(dir).filter(f => f.endsWith('.md'));

    for (const file of files) {
      const filePath = join(dir, file);
      try {
        const skill = this.parseSkillFile(filePath, categoryOverride);
        if (skill) {
          this.skills.set(skill.name, skill);
          // Index keywords
          for (const kw of skill.keywords) {
            this.keywordIndex.set(kw.toLowerCase(), skill.name);
          }
        }
      } catch (e) {
        console.warn('Failed to parse skill:', filePath, (e as Error).message);
      }
    }
  }

  private parseSkillFile(filePath: string, categoryOverride?: string): Skill | null {
    const raw = readFileSync(filePath, 'utf-8');
    const name = basename(filePath, '.md');

    // Try to parse frontmatter (gray-matter)
    let description = '';
    let keywords: string[] = [];

    try {
      const parsed = matter(raw);
      if (parsed.data.description) {
        description = parsed.data.description;
      }
      if (parsed.data.keywords) {
        keywords = Array.isArray(parsed.data.keywords)
          ? parsed.data.keywords
          : String(parsed.data.keywords).split(',').map(k => k.trim());
      }
    } catch {
      // No frontmatter — that's fine
    }

    // Fallback: extract description from first heading or first non-empty line
    if (!description) {
      const lines = raw.split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('# ')) {
          // Extract text after the command name: "# /team research — Research Pipeline" -> "Research Pipeline"
          const dashMatch = trimmed.match(/[—–-]\s*(.+)$/);
          if (dashMatch) {
            description = dashMatch[1].trim();
          } else {
            description = trimmed.replace(/^#\s*/, '');
          }
          break;
        }
        if (trimmed.startsWith('>')) {
          description = trimmed.replace(/^>\s*/, '');
          break;
        }
        if (trimmed && !trimmed.startsWith('#')) {
          description = trimmed;
          break;
        }
      }
    }

    // Auto-generate keywords from the name
    if (keywords.length === 0) {
      // "team-research" -> ["team", "research"]
      keywords = name.split('-').filter(k => k.length > 2);
      // Add description words (nouns/verbs)
      if (description) {
        const descWords = description
          .toLowerCase()
          .replace(/[^a-z\s]/g, '')
          .split(/\s+/)
          .filter(w => w.length > 3);
        keywords.push(...descWords.slice(0, 5));
      }
    }

    // Determine category
    let category = categoryOverride || 'standalone';
    if (name.startsWith('team-') || name === 'team') category = 'team';
    else if (name.startsWith('gsd') || name.startsWith('gsd:')) category = 'gsd';
    else if (name.startsWith('email')) category = 'email';
    else if (name.startsWith('pmstudio')) category = 'pmstudio';

    // Determine command format
    let command: string;
    if (category === 'team' && name.startsWith('team-')) {
      command = `/team ${name.replace('team-', '')}`;
    } else if (category === 'gsd' && categoryOverride === 'gsd') {
      command = `/gsd:${name}`;
    } else {
      command = `/${name}`;
    }

    const isWriteOperation = WRITE_PATTERNS.test(name) || WRITE_PATTERNS.test(description);

    return {
      name,
      command,
      description: description || name,
      filePath,
      category,
      isWriteOperation,
      keywords: [...new Set(keywords)], // dedupe
    };
  }

  // --- Lookups ---

  get(name: string): Skill | undefined {
    return this.skills.get(name);
  }

  findByKeyword(text: string): Skill | undefined {
    const lower = text.toLowerCase();

    // 1. Exact slash command match: "/team research" or "/email-read"
    for (const skill of this.skills.values()) {
      if (lower.startsWith(skill.command)) {
        return skill;
      }
    }

    // 2. Direct name match: "team-research"
    const directMatch = this.skills.get(lower);
    if (directMatch) return directMatch;

    // 3. Keyword match: score each skill by how many keywords appear in the input
    let bestSkill: Skill | undefined;
    let bestScore = 0;

    for (const skill of this.skills.values()) {
      let score = 0;
      for (const kw of skill.keywords) {
        if (lower.includes(kw.toLowerCase())) {
          score += kw.length; // longer keyword matches = higher confidence
        }
      }
      if (score > bestScore) {
        bestScore = score;
        bestSkill = skill;
      }
    }

    return bestScore > 3 ? bestSkill : undefined; // minimum threshold
  }

  getAll(): Skill[] {
    return Array.from(this.skills.values());
  }

  getByCategory(category: string): Skill[] {
    return this.getAll().filter(s => s.category === category);
  }

  toPromptContext(): string {
    const lines = ['Available skills:'];
    const byCategory = new Map<string, Skill[]>();

    for (const skill of this.skills.values()) {
      const list = byCategory.get(skill.category) || [];
      list.push(skill);
      byCategory.set(skill.category, list);
    }

    for (const [category, skills] of byCategory) {
      lines.push(`\n### ${category}`);
      for (const skill of skills) {
        const writeTag = skill.isWriteOperation ? ' [WRITE]' : '';
        lines.push(`- ${skill.command} — ${skill.description}${writeTag}`);
      }
    }

    return lines.join('\n');
  }

  get size(): number {
    return this.skills.size;
  }
}
```

**Verification:** Create `tests/skill-registry.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { SkillRegistry } from '../src/core/skill-registry.js';

describe('SkillRegistry', () => {
  let registry: SkillRegistry;

  beforeEach(async () => {
    registry = new SkillRegistry();
    await registry.loadAll();
  });

  it('discovers skills from ~/.claude/commands/', () => {
    expect(registry.size).toBeGreaterThan(0);
    console.log(`Discovered ${registry.size} skills`);
  });

  it('parses team-research correctly', () => {
    const skill = registry.get('team-research');
    expect(skill).toBeDefined();
    expect(skill!.category).toBe('team');
    expect(skill!.command).toBe('/team research');
  });

  it('finds skill by keyword "research OAuth"', () => {
    const skill = registry.findByKeyword('research OAuth patterns');
    expect(skill).toBeDefined();
    expect(skill!.name).toBe('team-research');
  });

  it('finds skill by slash command "/team develop"', () => {
    const skill = registry.findByKeyword('/team develop the auth service');
    expect(skill).toBeDefined();
    expect(skill!.name).toBe('team-develop');
  });

  it('generates prompt context', () => {
    const context = registry.toPromptContext();
    expect(context).toContain('Available skills:');
    expect(context).toContain('/team research');
  });

  it('marks write operations correctly', () => {
    const develop = registry.get('team-develop');
    expect(develop?.isWriteOperation).toBe(true);
    const research = registry.get('team-research');
    expect(research?.isWriteOperation).toBe(false);
  });
});
```

Run: `cd phase1 && npm test`

---

## Wave 3: Orchestrator (intent routing + claude dispatch)

**Dependencies:** Wave 2 complete (state.ts and skill-registry.ts working)
**Estimated time:** 20-30 minutes

### Task 3.1: Implement orchestrator.ts — Input handling, intent routing, claude dispatch

**File:** `coco/phase1/src/core/orchestrator.ts`

- [ ] Write the complete Orchestrator class:

```typescript
import { EventEmitter } from 'eventemitter3';
import { execFile, execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { StateManager, SessionRow } from './state.js';
import type { SkillRegistry, Skill } from './skill-registry.js';

// --- Types ---

export interface ClassifiedIntent {
  skill: Skill | null;     // null = direct Claude response (no skill match)
  args: string;
  confidence: number;
  isMetaCommand: boolean;
  metaCommand?: string;
  metaArgs?: string;
}

export interface OrchestratorEvents {
  output: (data: { sessionId: string | null; text: string }) => void;
  status: (data: { message: string }) => void;
  sessionStart: (data: { sessionId: string; skill: string }) => void;
  sessionEnd: (data: { sessionId: string; skill: string; success: boolean }) => void;
  recovery: (data: { interrupted: SessionRow[] }) => void;
  error: (data: { message: string; error?: Error }) => void;
}

// --- Meta-command patterns ---

const META_COMMANDS: Record<string, RegExp> = {
  status:  /^\/(status)\s*$/i,
  halt:    /^\/(halt)\s*(.*)$/i,
  history: /^\/(history)\s*(.*)$/i,
  help:    /^\/(help)\s*$/i,
  quit:    /^\/(quit|exit|bye)\s*$/i,
};

// --- Orchestrator ---

export class Orchestrator extends EventEmitter<OrchestratorEvents> {
  private state: StateManager;
  private skills: SkillRegistry;
  private systemPrompt: string;
  private isRunning: boolean = false;

  constructor(state: StateManager, skills: SkillRegistry) {
    super();
    this.state = state;
    this.skills = skills;

    // Load system prompt
    const promptPath = join(
      dirname(fileURLToPath(import.meta.url)),
      '..', '..', 'prompts', 'coco-system.md'
    );
    try {
      this.systemPrompt = readFileSync(promptPath, 'utf-8');
    } catch {
      this.systemPrompt = 'You are CoCo, a concise terminal assistant. Route requests to the appropriate skill.';
    }
  }

  async startup(): Promise<void> {
    // Mark any previously running sessions as interrupted
    const interrupted = this.state.markRunningAsInterrupted();
    if (interrupted > 0) {
      const sessions = this.state.getInterruptedSessions();
      this.emit('recovery', { interrupted: sessions });
    }

    // Prune old events
    this.state.prune(30);
  }

  async shutdown(): Promise<void> {
    this.isRunning = false;
    // Mark running sessions as interrupted for next startup
    this.state.markRunningAsInterrupted();
    this.state.close();
  }

  // --- Main entry point ---

  async handleInput(text: string): Promise<void> {
    const trimmed = text.trim();
    if (!trimmed) return;

    // Log to input history
    this.state.addInputHistory(trimmed);
    this.state.logEvent(null, 'user_input', { text: trimmed });

    // Step 1: Classify intent
    const intent = this.classifyIntent(trimmed);

    // Step 2: Handle meta-commands locally
    if (intent.isMetaCommand) {
      this.handleMetaCommand(intent.metaCommand!, intent.metaArgs);
      return;
    }

    // Step 3: If a skill was matched, dispatch to claude with that skill context
    if (intent.skill) {
      // Confirm write operations
      if (intent.skill.isWriteOperation) {
        this.emit('status', {
          message: `Will route to ${intent.skill.command} (write operation). Proceeding...`,
        });
      } else {
        this.emit('status', {
          message: `Routing to ${intent.skill.command}...`,
        });
      }

      await this.dispatchToSkill(intent.skill, intent.args);
      return;
    }

    // Step 4: No skill match — send directly to Claude as a general query
    this.emit('status', { message: 'No skill match — responding directly...' });
    await this.dispatchDirect(trimmed);
  }

  // --- Intent Classification (Tier 1: keyword/pattern only for Phase 1) ---

  classifyIntent(text: string): ClassifiedIntent {
    // Check meta-commands first
    for (const [name, pattern] of Object.entries(META_COMMANDS)) {
      const match = text.match(pattern);
      if (match) {
        return {
          skill: null,
          args: '',
          confidence: 1.0,
          isMetaCommand: true,
          metaCommand: name,
          metaArgs: match[2]?.trim(),
        };
      }
    }

    // Check for direct slash commands: "/team research OAuth"
    if (text.startsWith('/')) {
      const skill = this.skills.findByKeyword(text);
      if (skill) {
        const args = text.replace(skill.command, '').trim();
        return { skill, args, confidence: 0.95, isMetaCommand: false };
      }
    }

    // Keyword-based matching on natural language
    const skill = this.skills.findByKeyword(text);
    if (skill) {
      return { skill, args: text, confidence: 0.8, isMetaCommand: false };
    }

    // No match
    return { skill: null, args: text, confidence: 0, isMetaCommand: false };
  }

  // --- Meta-command handlers ---

  private handleMetaCommand(command: string, args?: string): void {
    switch (command) {
      case 'status': {
        const active = this.state.getActiveSessions();
        if (active.length === 0) {
          this.emit('output', { sessionId: null, text: 'No active sessions.' });
        } else {
          const lines = active.map(s =>
            `  [${s.status}] ${s.skill} — ${s.args.slice(0, 50)}`
          );
          this.emit('output', { sessionId: null, text: `Active sessions:\n${lines.join('\n')}` });
        }
        break;
      }

      case 'history': {
        const recent = this.state.getRecentSessions(20);
        if (recent.length === 0) {
          this.emit('output', { sessionId: null, text: 'No session history.' });
        } else {
          const lines = recent.map(s => {
            const time = new Date(s.created_at).toLocaleTimeString();
            return `  [${time}] ${s.skill} — ${s.status} — ${s.args.slice(0, 40)}`;
          });
          this.emit('output', { sessionId: null, text: `Recent sessions:\n${lines.join('\n')}` });
        }
        break;
      }

      case 'help': {
        const skillContext = this.skills.toPromptContext();
        const help = [
          'CoCo — type naturally or use commands:',
          '',
          'Meta-commands:',
          '  /status    — Show active sessions',
          '  /history   — Show recent sessions',
          '  /halt      — Stop all sessions',
          '  /help      — This message',
          '  /quit      — Exit CoCo',
          '',
          skillContext,
        ].join('\n');
        this.emit('output', { sessionId: null, text: help });
        break;
      }

      case 'halt': {
        this.state.markRunningAsInterrupted();
        this.emit('output', { sessionId: null, text: 'All sessions halted.' });
        break;
      }

      case 'quit': {
        this.emit('output', { sessionId: null, text: 'CoCo signing off.' });
        // The UI layer will handle the actual exit
        break;
      }
    }
  }

  // --- Dispatch to claude -p with skill context ---

  private async dispatchToSkill(skill: Skill, args: string): Promise<void> {
    const sessionId = this.state.createSession(skill.name, args, process.cwd());
    this.state.incrementSkillUsage(skill.name);

    this.emit('sessionStart', { sessionId, skill: skill.name });
    this.state.logEvent(sessionId, 'session_spawned', { skill: skill.name, args });

    // Build the full prompt: system prompt + skill routing instruction + user args
    const prompt = args || `Execute ${skill.command}`;
    const systemPromptWithSkill = [
      this.systemPrompt,
      '',
      `## Current Task`,
      `Route this to: ${skill.command}`,
      `The user wants: ${args}`,
      `Skill description: ${skill.description}`,
    ].join('\n');

    try {
      await this.runClaude(sessionId, prompt, systemPromptWithSkill);
      this.state.updateSessionStatus(sessionId, 'complete');
      this.emit('sessionEnd', { sessionId, skill: skill.name, success: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.state.updateSessionStatus(sessionId, 'error', message);
      this.emit('sessionEnd', { sessionId, skill: skill.name, success: false });
      this.emit('error', { message: `Session failed: ${message}` });
    }
  }

  private async dispatchDirect(text: string): Promise<void> {
    const sessionId = this.state.createSession('direct', text, process.cwd());
    this.emit('sessionStart', { sessionId, skill: 'direct' });

    try {
      await this.runClaude(sessionId, text, this.systemPrompt);
      this.state.updateSessionStatus(sessionId, 'complete');
      this.emit('sessionEnd', { sessionId, skill: 'direct', success: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.state.updateSessionStatus(sessionId, 'error', message);
      this.emit('sessionEnd', { sessionId, skill: 'direct', success: false });
      this.emit('error', { message: `Session failed: ${message}` });
    }
  }

  // --- claude -p child process (proven pattern from Phase 0) ---

  private runClaude(sessionId: string, prompt: string, systemPrompt: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const child = execFile(
        'claude',
        ['-p', '--system-prompt', systemPrompt, '--output-format', 'text', prompt],
        {
          maxBuffer: 1024 * 1024 * 10, // 10MB
          cwd: process.cwd(),
          timeout: 300_000, // 5 minute timeout
        },
        (error, _stdout, stderr) => {
          if (error) {
            this.state.appendSessionOutput(sessionId, stderr || error.message);
            reject(error);
            return;
          }

          // Output already streamed via child.stdout 'data' listener — do not re-emit here
          resolve();
        }
      );

      // Stream stdout chunks as they arrive (single source of truth for output)
      child.stdout?.on('data', (chunk: Buffer) => {
        const text = chunk.toString();
        this.state.appendSessionOutput(sessionId, text);
        this.emit('output', { sessionId, text });
      });
    });
  }

  // --- Getters for UI ---

  getGreeting(): string {
    const cwd = process.cwd();
    const project = cwd.split('/').pop() || 'unknown';
    let branch = 'no-git';
    try {
      branch = execSync('git branch --show-current', { cwd, encoding: 'utf-8' }).trim();
    } catch {}

    const skillCount = this.skills.size;
    const interrupted = this.state.getInterruptedSessions();
    const lines = [
      `${project} (${branch}). ${skillCount} skills loaded.`,
    ];
    if (interrupted.length > 0) {
      lines.push(`${interrupted.length} interrupted session(s) from last run.`);
    }
    lines.push('Ready.');
    return lines.join('\n');
  }
}
```

**Verification:** Create `tests/orchestrator.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { Orchestrator } from '../src/core/orchestrator.js';
import { StateManager } from '../src/core/state.js';
import { SkillRegistry } from '../src/core/skill-registry.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-orch-test.db';

describe('Orchestrator — Intent Classification', () => {
  let orchestrator: Orchestrator;
  let state: StateManager;
  let skills: SkillRegistry;

  beforeEach(async () => {
    state = new StateManager(TEST_DB);
    state.initialize();
    skills = new SkillRegistry();
    await skills.loadAll();
    orchestrator = new Orchestrator(state, skills);
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  // --- Meta-commands ---
  it('classifies /status as meta-command', () => {
    const intent = orchestrator.classifyIntent('/status');
    expect(intent.isMetaCommand).toBe(true);
    expect(intent.metaCommand).toBe('status');
  });

  it('classifies /quit as meta-command', () => {
    const intent = orchestrator.classifyIntent('/quit');
    expect(intent.isMetaCommand).toBe(true);
    expect(intent.metaCommand).toBe('quit');
  });

  it('classifies /help as meta-command', () => {
    const intent = orchestrator.classifyIntent('/help');
    expect(intent.isMetaCommand).toBe(true);
  });

  // --- Direct slash commands ---
  it('classifies "/team research OAuth" as team-research', () => {
    const intent = orchestrator.classifyIntent('/team research OAuth patterns');
    expect(intent.skill?.name).toBe('team-research');
    expect(intent.confidence).toBeGreaterThan(0.9);
  });

  // --- Natural language routing ---
  it('routes "research OAuth patterns" to team-research', () => {
    const intent = orchestrator.classifyIntent('research OAuth patterns');
    expect(intent.skill?.name).toBe('team-research');
  });

  it('routes "fix the login bug" to team-fix', () => {
    const intent = orchestrator.classifyIntent('fix the login bug');
    expect(intent.skill?.name).toBe('team-fix');
  });

  it('routes "develop the auth module" to team-develop', () => {
    const intent = orchestrator.classifyIntent('develop the auth module');
    expect(intent.skill?.name).toBe('team-develop');
  });

  it('routes "review the API code" to team-review', () => {
    const intent = orchestrator.classifyIntent('review the API code');
    expect(intent.skill?.name).toBe('team-review');
  });

  it('routes "plan the next sprint" to team-plan', () => {
    const intent = orchestrator.classifyIntent('plan the next sprint');
    expect(intent.skill?.name).toBe('team-plan');
  });

  // --- Write operation detection ---
  it('marks develop as write operation', () => {
    const intent = orchestrator.classifyIntent('develop the auth module');
    expect(intent.skill?.isWriteOperation).toBe(true);
  });

  it('marks research as read-only', () => {
    const intent = orchestrator.classifyIntent('research OAuth patterns');
    expect(intent.skill?.isWriteOperation).toBe(false);
  });

  // --- No match ---
  it('returns null skill for unrelated input', () => {
    const intent = orchestrator.classifyIntent('what time is it');
    expect(intent.skill).toBeNull();
  });

  // The 20-input routing accuracy test:
  const ROUTING_TEST_CASES: Array<[string, string | null]> = [
    ['research OAuth 2.0 best practices', 'team-research'],
    ['investigate rate limiting patterns', 'team-research'],
    ['build an auth service', 'team-develop'],
    ['develop the payment module', 'team-develop'],
    ['fix the failing tests', 'team-fix'],
    ['debug the login issue', 'team-fix'],
    ['review the auth code', 'team-review'],
    ['audit the API endpoints', 'team-review'],
    ['plan the next sprint', 'team-plan'],
    ['create a roadmap for Q2', 'team-plan'],
    ['write tests for the service', 'team-test'],
    ['check test coverage', 'team-test'],
    ['think about the architecture options', 'team-think'],
    ['brainstorm solutions for caching', 'team-think'],
    ['/team research voice APIs', 'team-research'],
    ['/team develop auth', 'team-develop'],
    ['/team fix broken endpoint', 'team-fix'],
    ['/team review', 'team-review'],
    ['create documentation for the API', 'team-document'],
    ['present the Q2 results', 'team-present'],
  ];

  it('routes >= 80% of 20 test inputs correctly', () => {
    let correct = 0;
    const failures: string[] = [];

    for (const [input, expectedSkill] of ROUTING_TEST_CASES) {
      const intent = orchestrator.classifyIntent(input);
      const actualSkill = intent.skill?.name ?? null;
      if (actualSkill === expectedSkill) {
        correct++;
      } else {
        failures.push(`  "${input}" → expected ${expectedSkill}, got ${actualSkill}`);
      }
    }

    const accuracy = correct / ROUTING_TEST_CASES.length;
    console.log(`Routing accuracy: ${correct}/${ROUTING_TEST_CASES.length} (${(accuracy * 100).toFixed(0)}%)`);
    if (failures.length > 0) {
      console.log('Failures:');
      console.log(failures.join('\n'));
    }
    expect(accuracy).toBeGreaterThanOrEqual(0.8);
  });
});
```

Run: `cd phase1 && npm test`

---

## Wave 4: UI (App.tsx, CommandInput.tsx, StatusBar.tsx)

**Dependencies:** Wave 3 complete (orchestrator works)
**Estimated time:** 20-30 minutes
**Parallelizable:** All three UI components can be built simultaneously.

### Task 4.1: Implement StatusBar.tsx

**File:** `coco/phase1/src/ui/StatusBar.tsx`

- [ ] Write the component:

```tsx
import React from 'react';
import { Box, Text } from 'ink';

interface StatusBarProps {
  project: string;
  branch: string;
  activeSessions: number;
  skillCount: number;
  message?: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  project,
  branch,
  activeSessions,
  skillCount,
  message,
}) => {
  const now = new Date();
  const clock = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

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
      {activeSessions > 0 && (
        <Text color="yellow">{activeSessions} active</Text>
      )}
      {message && (
        <Text color="gray">{message}</Text>
      )}
      <Text dimColor>{clock}</Text>
    </Box>
  );
};
```

### Task 4.2: Implement CommandInput.tsx

**File:** `coco/phase1/src/ui/CommandInput.tsx`

- [ ] Write the component:

```tsx
import React, { useState, useCallback } from 'react';
import { Box, Text, useInput } from 'ink';

interface CommandInputProps {
  onSubmit: (text: string) => void;
  history: string[];
  disabled?: boolean;
}

export const CommandInput: React.FC<CommandInputProps> = ({
  onSubmit,
  history,
  disabled = false,
}) => {
  const [value, setValue] = useState('');
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [cursorVisible, setCursorVisible] = useState(true);

  // Blink cursor
  React.useEffect(() => {
    const interval = setInterval(() => setCursorVisible(v => !v), 500);
    return () => clearInterval(interval);
  }, []);

  useInput((input, key) => {
    if (disabled) return;

    if (key.return) {
      if (value.trim()) {
        onSubmit(value.trim());
        setValue('');
        setHistoryIndex(-1);
      }
      return;
    }

    if (key.backspace || key.delete) {
      setValue(v => v.slice(0, -1));
      return;
    }

    if (key.upArrow) {
      if (history.length === 0) return;
      const newIndex = Math.min(historyIndex + 1, history.length - 1);
      setHistoryIndex(newIndex);
      setValue(history[history.length - 1 - newIndex] || '');
      return;
    }

    if (key.downArrow) {
      if (historyIndex <= 0) {
        setHistoryIndex(-1);
        setValue('');
        return;
      }
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setValue(history[history.length - 1 - newIndex] || '');
      return;
    }

    // Ctrl+C is handled by Ink's exit
    if (key.escape) {
      setValue('');
      setHistoryIndex(-1);
      return;
    }

    // Regular character input
    if (input && !key.ctrl && !key.meta) {
      setValue(v => v + input);
    }
  });

  return (
    <Box paddingX={1}>
      <Text color="cyan" bold>&gt; </Text>
      <Text>
        {value}
        {cursorVisible ? '█' : ' '}
      </Text>
      {disabled && <Text dimColor> (processing...)</Text>}
    </Box>
  );
};
```

### Task 4.3: Implement App.tsx — Root layout

**File:** `coco/phase1/src/ui/App.tsx`

- [ ] Write the root component:

```tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Box, Text, useApp } from 'ink';
import { execSync } from 'node:child_process';
import { StatusBar } from './StatusBar.js';
import { CommandInput } from './CommandInput.js';
import type { Orchestrator } from '../core/orchestrator.js';
import type { StateManager } from '../core/state.js';
import type { SkillRegistry } from '../core/skill-registry.js';

interface AppProps {
  orchestrator: Orchestrator;
  state: StateManager;
  skills: SkillRegistry;
}

export const App: React.FC<AppProps> = ({ orchestrator, state, skills }) => {
  const { exit } = useApp();
  const [output, setOutput] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [activeSessions, setActiveSessions] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [inputHistory, setInputHistory] = useState<string[]>(() =>
    state.getInputHistory(50)
  );

  // Get project info
  const cwd = process.cwd();
  const project = cwd.split('/').pop() || 'unknown';
  let branch = 'no-git';
  try {
    branch = execSync('git branch --show-current', { cwd, encoding: 'utf-8' }).trim();
  } catch {}

  // Show greeting on mount
  useEffect(() => {
    const greeting = orchestrator.getGreeting();
    setOutput([greeting]);
  }, []);

  // Subscribe to orchestrator events
  useEffect(() => {
    const onOutput = (data: { sessionId: string | null; text: string }) => {
      setOutput(prev => {
        const next = [...prev, data.text];
        // Keep last 200 lines
        return next.length > 200 ? next.slice(-200) : next;
      });
    };

    const onStatus = (data: { message: string }) => {
      setStatusMessage(data.message);
    };

    const onSessionStart = () => {
      setActiveSessions(prev => prev + 1);
      setIsProcessing(true);
    };

    const onSessionEnd = () => {
      setActiveSessions(prev => Math.max(0, prev - 1));
      setIsProcessing(false);
    };

    const onError = (data: { message: string }) => {
      setOutput(prev => [...prev, `Error: ${data.message}`]);
      setIsProcessing(false);
    };

    const onRecovery = (data: { interrupted: any[] }) => {
      setOutput(prev => [
        ...prev,
        `Found ${data.interrupted.length} interrupted session(s) from last run.`,
        'Use /history to view them.',
      ]);
    };

    orchestrator.on('output', onOutput);
    orchestrator.on('status', onStatus);
    orchestrator.on('sessionStart', onSessionStart);
    orchestrator.on('sessionEnd', onSessionEnd);
    orchestrator.on('error', onError);
    orchestrator.on('recovery', onRecovery);

    return () => {
      orchestrator.off('output', onOutput);
      orchestrator.off('status', onStatus);
      orchestrator.off('sessionStart', onSessionStart);
      orchestrator.off('sessionEnd', onSessionEnd);
      orchestrator.off('error', onError);
      orchestrator.off('recovery', onRecovery);
    };
  }, [orchestrator]);

  const handleSubmit = useCallback(async (text: string) => {
    // Check for quit
    if (/^\/(quit|exit|bye)$/i.test(text)) {
      setOutput(prev => [...prev, 'CoCo signing off.']);
      await orchestrator.shutdown();
      exit();
      return;
    }

    setInputHistory(prev => [...prev, text]);
    setIsProcessing(true);
    setOutput(prev => [...prev, `> ${text}`]);

    try {
      await orchestrator.handleInput(text);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setOutput(prev => [...prev, `Error: ${msg}`]);
    } finally {
      setIsProcessing(false);
      setStatusMessage('');
    }
  }, [orchestrator, exit]);

  return (
    <Box flexDirection="column" width="100%">
      {/* Status bar */}
      <StatusBar
        project={project}
        branch={branch}
        activeSessions={activeSessions}
        skillCount={skills.size}
        message={statusMessage}
      />

      {/* Output area */}
      <Box flexDirection="column" paddingX={1} flexGrow={1}>
        {output.slice(-30).map((line, i) => (
          <Text key={i} wrap="wrap">
            {line}
          </Text>
        ))}
      </Box>

      {/* Input */}
      <CommandInput
        onSubmit={handleSubmit}
        history={inputHistory}
        disabled={isProcessing}
      />
    </Box>
  );
};
```

**Verification:** `npm run dev` — should render the status bar, greeting, and input prompt. Type `/help` and see skill list.

---

## Wave 5: Entry Point + Integration + Polish

**Dependencies:** Waves 1-4 complete
**Estimated time:** 15-20 minutes

### Task 5.1: Implement index.tsx — Entry point

**File:** `coco/phase1/src/index.tsx`

- [ ] Write the entry point:

```tsx
#!/usr/bin/env node
import { render } from 'ink';
import React from 'react';
import { App } from './ui/App.js';
import { Orchestrator } from './core/orchestrator.js';
import { StateManager } from './core/state.js';
import { SkillRegistry } from './core/skill-registry.js';
import { join } from 'node:path';
import { existsSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';

async function main() {
  // DB location: ~/.coco/coco.db (persistent across projects)
  const cocoDir = join(homedir(), '.coco');
  if (!existsSync(cocoDir)) {
    mkdirSync(cocoDir, { recursive: true });
  }
  const dbPath = join(cocoDir, 'coco.db');

  // Initialize core modules
  const state = new StateManager(dbPath);
  state.initialize();

  const skills = new SkillRegistry();
  await skills.loadAll();

  const orchestrator = new Orchestrator(state, skills);
  await orchestrator.startup();

  // Handle Ctrl+C gracefully
  let ctrlCCount = 0;
  process.on('SIGINT', async () => {
    ctrlCCount++;
    if (ctrlCCount >= 2) {
      await orchestrator.shutdown();
      process.exit(0);
    }
    // First Ctrl+C: just show a message (Ink handles this)
  });

  process.on('SIGTERM', async () => {
    await orchestrator.shutdown();
    process.exit(0);
  });

  // Single-command mode: coco "research OAuth"
  const args = process.argv.slice(2);
  if (args.length > 0) {
    const input = args.join(' ');

    // Non-interactive: just dispatch and print output
    orchestrator.on('output', ({ text }) => {
      process.stdout.write(text);
    });

    await orchestrator.handleInput(input);
    await orchestrator.shutdown();
    return;
  }

  // Interactive TUI mode
  const { waitUntilExit } = render(
    <App
      orchestrator={orchestrator}
      state={state}
      skills={skills}
    />
  );

  await waitUntilExit();
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

# Single-command mode
npm run dev -- "what time is it"
```

### Task 5.2: Add .gitignore

**File:** `coco/phase1/.gitignore`

- [ ] Create:

```
node_modules/
dist/
*.db
*.db-wal
*.db-shm
```

### Task 5.3: Run the full test suite

- [ ] Run all tests:

```bash
cd phase1 && npm test
```

Expected results:
- `state.test.ts` — 5 tests pass (session CRUD, skill usage, input history, interrupted recovery, output cap)
- `skill-registry.test.ts` — 6 tests pass (discovery, parsing, keyword lookup, slash command, prompt context, write detection)
- `orchestrator.test.ts` — 14+ tests pass (meta-commands, slash routing, NL routing, write detection, 80% accuracy gate)

### Task 5.4: Manual smoke test

- [ ] Launch CoCo:
```bash
cd phase1 && npm run dev
```

- [ ] Verify checklist:
  1. Status bar shows project name, branch, skill count, clock
  2. Greeting shows "Ready." (not "How can I help?")
  3. Type `/help` — see skill list
  4. Type `/status` — see "No active sessions"
  5. Type `/history` — see session history (may be empty)
  6. Type "research OAuth patterns" — see "Routing to /team research..."
  7. Type `/quit` — CoCo exits cleanly
  8. Relaunch — previous input history accessible via up arrow
  9. Check `~/.coco/coco.db` exists
  10. Ctrl+C once — no crash. Ctrl+C twice — exits.

### Task 5.5: Verify success criteria

- [ ] `npm run dev` launches the Ink terminal UI
- [ ] 20-input routing test passes at >= 80% (automated in orchestrator.test.ts)
- [ ] Skill registry discovers 40+ skills from `~/.claude/commands/`
- [ ] SQLite stores sessions, input history, skill usage (check with `sqlite3 ~/.coco/coco.db "SELECT COUNT(*) FROM sessions"`)
- [ ] Session survives Ctrl+C — relaunch shows interrupted sessions
- [ ] CoCo personality: greeting says "Ready.", not "How can I help?"

---

## File Manifest

All files created or modified in this plan:

| File | Wave | Purpose |
|------|------|---------|
| `phase1/package.json` | 1 | Dependencies and scripts |
| `phase1/tsconfig.json` | 1 | TypeScript config |
| `phase1/.gitignore` | 5 | Ignore node_modules, dist, db |
| `phase1/prompts/coco-system.md` | 1 | CoCo personality + routing prompt |
| `phase1/src/core/state.ts` | 2 | SQLite state manager (sessions, events, history, usage) |
| `phase1/src/core/skill-registry.ts` | 2 | Auto-discover skills from `~/.claude/commands/` |
| `phase1/src/core/orchestrator.ts` | 3 | Intent classification + claude dispatch |
| `phase1/src/ui/StatusBar.tsx` | 4 | Persistent one-line status bar |
| `phase1/src/ui/CommandInput.tsx` | 4 | Text input with history + cursor |
| `phase1/src/ui/App.tsx` | 4 | Ink root layout wiring everything together |
| `phase1/src/index.tsx` | 5 | Entry point — CLI arg parsing, boot, render |
| `phase1/tests/state.test.ts` | 2 | State manager unit tests |
| `phase1/tests/skill-registry.test.ts` | 2 | Skill registry unit tests |
| `phase1/tests/orchestrator.test.ts` | 3 | Orchestrator + routing accuracy tests |

---

## Dependency Graph

```
Wave 1 ─── package.json, tsconfig, dirs, prompts
  │
  ├──→ Wave 2a ─── state.ts + state.test.ts
  │
  ├──→ Wave 2b ─── skill-registry.ts + skill-registry.test.ts
  │
  └──→ Wave 3 ─── orchestrator.ts + orchestrator.test.ts  (needs 2a + 2b)
         │
         ├──→ Wave 4a ─── StatusBar.tsx
         │
         ├──→ Wave 4b ─── CommandInput.tsx
         │
         ├──→ Wave 4c ─── App.tsx  (needs 4a + 4b)
         │
         └──→ Wave 5 ─── index.tsx + integration  (needs 3 + 4c)
```

---

## Key Design Decisions for Phase 1

1. **`claude -p` child process, NOT SDK `query()`** — Phase 0 proved this works. The child process inherits all CLAUDE.md, commands, skills, hooks, and MCP servers. SDK `query()` would require re-implementing config loading. We keep the proven pattern.

2. **Tier 1 only (keyword matching) for intent classification** — No LLM-based classification in Phase 1. The keyword/pattern matching from skill-registry + orchestrator handles the 80% accuracy target. Tier 2 (Claude-powered classification) is Phase 4.

3. **Single session at a time** — Phase 1 is single-session dispatch. The UI shows one active session. Parallel sessions come in Phase 2.

4. **DB at `~/.coco/coco.db`** — Not in the project directory. This is a personal tool — state persists across all projects.

5. **`execFile` not `spawn`** — Simpler for Phase 1 since we don't need streaming yet. The output arrives when claude finishes. Phase 2 switches to `spawn` with streaming for the live dashboard.

6. **No `@anthropic-ai/claude-code` dependency** — We don't need the SDK for Phase 1. Plain `execFile('claude', ...)` is sufficient and proven. SDK is a Phase 2+ consideration when we need `onMessage` streaming.
