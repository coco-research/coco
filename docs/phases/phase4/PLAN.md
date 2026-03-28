# Phase 4: Intelligence Layer — Implementation Plan

**Date:** 2026-03-20
**Owner:** Rijul Kalra
**Status:** Planning
**Effort:** 3-5 days
**Depends on:** Phase 1 (skill registry, orchestrator, SQLite state), Phase 2 recommended (parallel sessions generate richer usage data)
**Spec refs:** TECH-SPEC.md §5.1 (two-tier classification), ROADMAP.md Phase 4, RESEARCH.md competitive analysis

---

## Goal

Make CoCo route natural language to the correct skill without explicit /commands, learn from routing corrections over time, and greet users with ambient project-aware context.

---

## Success Criteria (from ROADMAP.md, made measurable)

| # | Criterion | How to Measure |
|---|-----------|---------------|
| SC-1 | "I need to review the auth service" routes to `/team review` with correct context | Manual test: 10 intent-to-route pairs with no /prefix all resolve correctly |
| SC-2 | Intent classification accuracy >90% on a 50-query test set spanning all 18 team commands | Automated test suite: `tests/intelligence/accuracy.test.ts` runs 50 queries, asserts >45 correct |
| SC-3 | CoCo greets with project-aware context: project name, branch, last session skill, queued task count | `getGreeting()` output contains all four data points; tested via snapshot test |
| SC-4 | Skill recommendations based on history: "You usually run X after Y -- want me to queue it?" | After 3+ occurrences of sequence A->B in `skill_sequences` table, next invocation of A triggers suggestion |
| SC-5 | Learning loop: routing corrections stored and applied to future classifications | Insert correction via `/correct <skill>`, verify next identical input routes to corrected skill |
| SC-6 | Context window management: old exchanges summarized to stay within token limits | After 10 exchanges, `context-manager.ts` produces a summary; raw exchange count stays at 5 |

---

## Architecture

### How the new modules fit with the existing system

```
User Input
    |
    v
+---------------------------+
| orchestrator.handleInput  |  (existing, modified)
+---------------------------+
    |
    v
+---------------------------+
| intent-classifier.ts      |  << NEW: replaces inline classifyIntent()
|   Tier 1: keyword/regex   |     (instant, no LLM call)
|   Tier 2: Claude query()  |     (ambiguous inputs only, <1s)
+---------------------------+
    |  ClassifiedIntent { skill, args, confidence }
    v
+---------------------------+
| learning-store.ts         |  << NEW: SQLite-backed correction + sequence store
|   - check corrections     |     (overrides Tier 1/2 if exact match exists)
|   - log routing decision  |
+---------------------------+
    |
    v
+---------------------------+
| team-router.ts            |  << NEW: parameter extraction for /team commands
| gsd-router.ts             |  << NEW: parameter extraction for /gsd commands
+---------------------------+
    |
    v
+---------------------------+
| context-manager.ts        |  << NEW: greeting, summarization, token budget
+---------------------------+
    |
    v
  Existing: sessionManager.spawn() or dispatchToSkill()
```

**Key integration points:**

1. **orchestrator.ts** -- `classifyIntent()` method is replaced by a call to `IntentClassifier.classify()`. The inline `TEAM_SKILL_TRIGGERS` array and `findByKeyword()` logic move into intent-classifier.ts as Tier 1.
2. **skill-registry.ts** -- unchanged. `toPromptContext()` is called by Tier 2 to build the Claude classification prompt.
3. **state.ts** -- new tables added (see Learning Store Schema below). Existing tables unchanged.
4. **orchestrator.getGreeting()** -- replaced by `ContextManager.buildGreeting()` which queries session history and queue state.

---

## Two-Tier Classification Design

### Tier 1: Keyword + Regex (instant, zero cost)

Tier 1 handles the 70%+ of inputs that are unambiguous. It runs synchronously in <1ms.

**Input sources (checked in order):**

1. **Learning store corrections** -- if the exact input (normalized) has a stored correction, return that skill immediately with confidence 1.0. This is how the learning loop feeds back.
2. **Direct slash commands** -- `/team research`, `/gsd:execute-phase` -- pass through with confidence 0.95.
3. **TEAM_SKILL_TRIGGERS regex array** -- the existing 13-entry array from orchestrator.ts, moved here. Returns confidence 0.85.
4. **skill-registry.findByKeyword()** -- existing keyword-score matching. Returns confidence 0.7.

**Output:** `ClassifiedIntent` with `confidence >= 0.7`, or `null` (triggers Tier 2).

**When Tier 1 returns `null`:**
- Input did not match any regex pattern
- Input matched a pattern but the skill name was not found in the registry
- Input is too ambiguous (e.g., "build the API" matches both `team-develop` and `team-plan`)

### Tier 2: Claude-based Classification (ambiguous inputs)

Tier 2 is a lightweight Claude `query()` call that acts as a pure classifier. No tools, no file access, `maxTurns: 1`.

**Prompt template:**

```
System: You are a command router for CoCo, a terminal assistant.
Given user input and available skills, return ONLY a JSON object:
{ "skill": "skill-name", "args": "remaining text after skill extraction", "confidence": 0.0-1.0 }

If no skill matches, return: { "skill": null, "args": "", "confidence": 0.0 }

Rules:
- "skill" must be one of the skill names listed below, or null.
- "args" is the part of the user's input that should be passed TO the skill as context.
- "confidence" reflects how certain you are this is the right skill.

Available skills:
${skillRegistry.toPromptContext()}

Recent context (last 3 exchanges):
${contextManager.getRecentExchanges(3)}
```

**Performance target:** <1 second wall-clock time for the Claude call. Achieved by:
- Using `maxTurns: 1` (single response, no tool use)
- Keeping the skill context compact (~2KB for 18 skills)
- Not including full session history (only last 3 exchanges for context)

**Confidence threshold:**
- `>= 0.7` -- route to skill, proceed
- `0.4 - 0.7` -- route to skill but ask one-line confirmation: "Route to /team review? [Y/n]"
- `< 0.4` -- respond directly (no skill match), treat as general conversation

### Multi-match disambiguation

When Tier 1 produces multiple regex matches (e.g., "build and test the API" matches both `team-develop` and `team-test`), the classifier:
1. Picks the **first** match by trigger order (TEAM_SKILL_TRIGGERS is ordered by priority)
2. Logs the ambiguity in `intent_log` for future analysis
3. If the user corrects, the correction is stored for the full input string

### Parameter extraction

After the skill is selected, the routers (`team-router.ts`, `gsd-router.ts`) extract structured parameters:

- **team-router.ts**: extracts `<topic>` from "research OAuth best practices" -> `{ skill: "team-research", topic: "OAuth best practices" }`
- **gsd-router.ts**: extracts phase names from "execute the build phase" -> `{ skill: "gsd:execute-phase", phase: "build" }`

Parameter extraction is simple string manipulation (remove the skill trigger words, pass the remainder). No LLM call needed.

---

## Learning Store Schema

All new tables go into the existing `coco.db` SQLite database alongside the Phase 1/2 tables.

```sql
-- Intent log: every classification decision, for analysis and debugging
CREATE TABLE IF NOT EXISTS intent_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  input_text    TEXT NOT NULL,                              -- raw user input
  input_normalized TEXT NOT NULL,                           -- lowercased, trimmed, punctuation removed
  tier          INTEGER NOT NULL,                           -- 1 or 2
  skill_matched TEXT,                                       -- skill name or null
  confidence    REAL NOT NULL,                              -- 0.0-1.0
  was_corrected INTEGER NOT NULL DEFAULT 0,                 -- 1 if user later corrected this
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000)
);

CREATE INDEX IF NOT EXISTS idx_intent_log_input ON intent_log(input_normalized);
CREATE INDEX IF NOT EXISTS idx_intent_log_created ON intent_log(created_at DESC);

-- Routing corrections: user-provided "no, I meant X" overrides
-- These are checked FIRST in Tier 1, so they always take priority.
CREATE TABLE IF NOT EXISTS routing_corrections (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  input_normalized TEXT NOT NULL,                           -- normalized input that was misrouted
  wrong_skill   TEXT NOT NULL,                              -- what CoCo guessed
  correct_skill TEXT NOT NULL,                              -- what the user wanted
  times_applied INTEGER NOT NULL DEFAULT 0,                 -- how many times this correction was used
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000),
  UNIQUE(input_normalized, correct_skill)                   -- one correction per input+skill pair
);

CREATE INDEX IF NOT EXISTS idx_corrections_input ON routing_corrections(input_normalized);

-- Skill sequences: tracks which skills are commonly run in sequence
-- Used for "You usually run X after Y" recommendations.
CREATE TABLE IF NOT EXISTS skill_sequences (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  skill_a       TEXT NOT NULL,                              -- the skill that ran first
  skill_b       TEXT NOT NULL,                              -- the skill that ran next
  count         INTEGER NOT NULL DEFAULT 1,                 -- how many times this sequence occurred
  last_seen     INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000),
  UNIQUE(skill_a, skill_b)                                  -- one row per pair
);

CREATE INDEX IF NOT EXISTS idx_sequences_a ON skill_sequences(skill_a);

-- Session summaries: compressed summaries for context window management
CREATE TABLE IF NOT EXISTS session_summaries (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id    TEXT NOT NULL,                              -- references sessions.id
  summary       TEXT NOT NULL,                              -- 1-3 sentence summary
  exchange_count INTEGER NOT NULL,                          -- how many exchanges this summarizes
  created_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000),
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_summaries_session ON session_summaries(session_id);

-- User preferences: learned behaviors (e.g., "always confirm before running team-develop")
CREATE TABLE IF NOT EXISTS user_preferences (
  key           TEXT PRIMARY KEY,                           -- preference key
  value         TEXT NOT NULL,                              -- preference value (JSON)
  source        TEXT NOT NULL DEFAULT 'learned',            -- 'learned' | 'explicit'
  confidence    REAL NOT NULL DEFAULT 0.5,                  -- how confident we are in this preference
  updated_at    INTEGER NOT NULL DEFAULT (unixepoch('subsec') * 1000)
);
```

**Storage estimates:**
- `intent_log`: ~200 bytes/row. 10K classifications = ~2MB. Pruned to last 90 days.
- `routing_corrections`: ~150 bytes/row. Likely <100 rows total for a single user.
- `skill_sequences`: ~100 bytes/row. At most N^2 pairs where N=18 skills = 324 rows max.
- `session_summaries`: ~500 bytes/row. 1 per session.
- `user_preferences`: ~200 bytes/row. <50 rows.

---

## Context Manager Design

### Ambient Greeting

`ContextManager.buildGreeting()` replaces the current `Orchestrator.getGreeting()`. It queries multiple data sources:

```
Output format:
"how-i-pm-with-ai (main). Last session: team research on voice APIs. 3 tasks queued. Ready."
```

**Data sources:**
1. **Project name** -- `path.basename(process.cwd())`
2. **Git branch** -- `git branch --show-current` (existing, with try/catch)
3. **Last session** -- `state.getRecentSessions(1)` -> extract skill name and first 50 chars of args
4. **Queue depth** -- `taskQueue?.depth ?? 0`
5. **Interrupted sessions** -- `state.getInterruptedSessions().length`
6. **Skill count** -- `skills.size`
7. **Time-aware greeting** -- if before 12pm: no prefix; if after 6pm: "Evening session."

**Rules:**
- No line exceeds 80 chars
- Maximum 3 lines total
- "Ready." is always the last word
- Never say "How can I help you?" or similar

### Session Summarization

After every N exchanges (configurable, default 10), the context manager:

1. Collects the last N exchange pairs (user input + CoCo response)
2. Sends them to Claude with a one-shot summarization prompt:
   ```
   Summarize this CoCo session into 1-3 sentences. Focus on: what tasks were completed,
   what skills were used, and any pending work. Be factual, not conversational.
   ```
3. Stores the summary in `session_summaries`
4. Drops the raw exchanges from the in-memory context (keeps only the last 5 raw exchanges)

**Token budget management:**
- **Budget:** 4,000 tokens reserved for context (out of ~8K available for system prompt + context)
- **Breakdown:** system prompt (~1,500 tokens) + skill registry (~1,000 tokens) + context window (~1,500 tokens)
- **Context window contents:** last 5 raw exchanges (~1,000 tokens) + last 2 session summaries (~500 tokens)
- **Overflow behavior:** if context exceeds budget, drop oldest summary first, then oldest raw exchange

### Skill Sequence Recommendations

After each skill dispatch completes, the context manager:

1. Records the sequence: `(previous_skill, current_skill)` in `skill_sequences` table (upsert, increment count)
2. Checks if `count >= 3` for any `(current_skill, X)` pair
3. If yes, emits a suggestion: "You usually run /team test after /team build -- want me to queue it?"
4. User can accept (Enter) or dismiss (Esc/any other key)
5. Suggestions are rate-limited: max 1 suggestion per 5 minutes to avoid annoyance

---

## Task Breakdown

### Task 1: SQLite Schema Migration

**Description:** Add the 5 new tables (`intent_log`, `routing_corrections`, `skill_sequences`, `session_summaries`, `user_preferences`) to the existing state module.

**Files to create/modify:**
- Modify: `src/core/state.ts` -- add new table creation to `initialize()`, add CRUD methods for each table

**Methods to add to StateManager:**
- `logIntent(input, normalized, tier, skill, confidence): void`
- `markIntentCorrected(intentId: number): void`
- `getCorrection(normalizedInput: string): { correct_skill: string } | undefined`
- `addCorrection(normalizedInput, wrongSkill, correctSkill): void`
- `incrementCorrectionUsage(id: number): void`
- `recordSequence(skillA, skillB): void`
- `getTopSequence(skillA: string): { skill_b: string; count: number } | undefined`
- `saveSummary(sessionId, summary, exchangeCount): void`
- `getRecentSummaries(limit: number): { summary: string; created_at: number }[]`
- `setPreference(key, value, source, confidence): void`
- `getPreference(key: string): { value: string; confidence: number } | undefined`

**Acceptance criteria:**
- All 5 tables created on `initialize()` (idempotent with IF NOT EXISTS)
- All CRUD methods have unit tests
- Existing tables and data are not affected (additive migration only)

**Estimated effort:** 0.5 day

**Dependencies:** None (can start immediately)

---

### Task 2: Intent Classifier Module

**Description:** Extract intent classification logic from `orchestrator.ts` into a dedicated module. Implement Tier 1 (keyword/regex) and Tier 2 (Claude-based) classification.

**Files to create/modify:**
- Create: `src/core/intent-classifier.ts`
- Modify: `src/core/orchestrator.ts` -- remove inline `TEAM_SKILL_TRIGGERS`, `classifyIntent()`, replace with `IntentClassifier.classify()`

**IntentClassifier interface:**

```
class IntentClassifier {
  constructor(skills: SkillRegistry, state: StateManager)

  classify(text: string): Promise<ClassifiedIntent>
    // 1. Check meta-commands (unchanged)
    // 2. Check learning store corrections (NEW)
    // 3. Check direct slash commands (moved from orchestrator)
    // 4. Check TEAM_SKILL_TRIGGERS regex (moved from orchestrator)
    // 5. Check skill-registry keyword match (moved from orchestrator)
    // 6. If all above fail: Tier 2 Claude classification (NEW)

  classifyTier1(text: string): ClassifiedIntent | null
    // Steps 2-5 above, synchronous, returns null if no match

  classifyTier2(text: string): Promise<ClassifiedIntent>
    // Claude query() with maxTurns:1, no tools
    // Parse JSON response, validate against skill registry
    // Return ClassifiedIntent with Claude-derived confidence

  normalizeInput(text: string): string
    // Lowercase, trim, remove punctuation, collapse whitespace
    // Used as key for learning store lookups
}
```

**Acceptance criteria:**
- All 13 existing `TEAM_SKILL_TRIGGERS` produce identical results when called via `IntentClassifier.classify()` vs the old inline code
- Tier 2 is only called when Tier 1 returns null (verified by mock spy)
- Tier 2 returns valid JSON with skill from the registry or null
- Confidence threshold of 0.7 triggers confirmation prompt for values 0.4-0.7
- `normalizeInput("  Build the API! ")` returns `"build the api"`

**Estimated effort:** 1 day

**Dependencies:** Task 1 (needs `getCorrection()` from learning store)

---

### Task 3: Learning Store Module

**Description:** Implement the correction-based learning loop. When a user says "no, I meant /team review" after a misroute, store the correction and apply it to future identical inputs.

**Files to create/modify:**
- Create: `src/core/learning-store.ts`
- Modify: `src/core/orchestrator.ts` -- add `/correct <skill>` meta-command

**LearningStore interface:**

```
class LearningStore {
  constructor(state: StateManager)

  // Record a routing decision (called on every classification)
  logDecision(input: string, tier: number, skill: string | null, confidence: number): number
    // Returns intent_log ID for later correction reference

  // Record a user correction: "no, I meant X"
  recordCorrection(intentLogId: number, correctSkill: string): void
    // 1. Get the original intent_log row
    // 2. Insert into routing_corrections (input_normalized, wrong_skill, correct_skill)
    // 3. Mark intent_log row as corrected

  // Check if a correction exists for this input
  getCorrection(normalizedInput: string): string | null
    // Returns correct_skill if a correction exists, null otherwise

  // Record a skill sequence (called after each dispatch)
  recordSequence(previousSkill: string, currentSkill: string): void
    // Upsert into skill_sequences, increment count

  // Get recommendation for next skill
  getRecommendation(currentSkill: string, threshold: number = 3): string | null
    // Returns skill_b if count >= threshold, null otherwise
}
```

**User-facing correction flow:**

1. CoCo routes "check the auth code" to `/team review` (confidence 0.82)
2. User sees output, realizes they wanted `/team test`
3. User types `/correct team-test`
4. CoCo stores correction: `("check the auth code", "team-review", "team-test")`
5. Next time user types "check the auth code", Tier 1 finds the correction and routes to `/team test` with confidence 1.0

**Acceptance criteria:**
- `/correct <skill>` stores a correction referencing the last classification
- Stored corrections are returned by `getCorrection()` on exact normalized match
- `times_applied` increments each time a correction is used
- Corrections take priority over regex matches (checked first in Tier 1)
- Skill sequences with count >= 3 trigger a recommendation

**Estimated effort:** 0.5 day

**Dependencies:** Task 1 (schema), Task 2 (IntentClassifier calls LearningStore)

---

### Task 4: Team Router — Parameter Extraction

**Description:** Map natural language intents to /team commands with structured parameter extraction. Goes beyond "which skill" to "which skill with what arguments."

**Files to create/modify:**
- Create: `src/integrations/team-router.ts`

**TeamRouter interface:**

```
class TeamRouter {
  constructor(skills: SkillRegistry)

  // Extract structured parameters from a classified intent
  extractParams(skill: Skill, rawInput: string): { command: string; args: string }
    // Remove trigger words, extract the meaningful argument
    // "research OAuth 2.0 best practices" -> { command: "/team research", args: "OAuth 2.0 best practices" }
    // "review the auth service code" -> { command: "/team review", args: "auth service code" }
    // "fix the failing login tests" -> { command: "/team fix", args: "failing login tests" }

  // Build the full dispatch string
  buildDispatch(skill: Skill, rawInput: string): string
    // Returns: "/team research OAuth 2.0 best practices"
}
```

**Parameter extraction rules (per skill):**

| Skill | Trigger words to strip | Example input | Extracted args |
|-------|----------------------|---------------|----------------|
| team-research | research, investigate, explore, look into, find out about | "look into AWS Lambda cold starts" | "AWS Lambda cold starts" |
| team-develop | develop, implement, build, create | "build an auth service for the API" | "auth service for the API" |
| team-review | review, audit, inspect, evaluate, assess | "review the payment module" | "payment module" |
| team-fix | fix, debug, troubleshoot, repair, patch | "fix the broken test suite" | "broken test suite" |
| team-test | test, write tests for, add coverage for | "write tests for the user service" | "user service" |
| team-plan | plan, roadmap, prioritize, schedule | "plan the next sprint" | "next sprint" |
| team-think | think about, brainstorm, analyze, consider | "think about the migration strategy" | "migration strategy" |

**Acceptance criteria:**
- All 13 team skills have working parameter extraction
- Extracted args do not contain the trigger word
- Filler words ("the", "a", "an", "for", "about") at the start of args are optionally stripped
- `buildDispatch()` output is a valid `/team <action> <args>` string

**Estimated effort:** 0.5 day

**Dependencies:** None (uses existing SkillRegistry)

---

### Task 5: GSD Router — Parameter Extraction

**Description:** Map natural language intents to /gsd commands with phase/project context extraction.

**Files to create/modify:**
- Create: `src/integrations/gsd-router.ts`

**GSD-specific patterns:**

| Input | Routed to | Extracted context |
|-------|-----------|------------------|
| "start a new project for the billing system" | `/gsd:new-project` | "billing system" |
| "execute the current phase" | `/gsd:execute-phase` | (none -- uses current phase) |
| "what's the project health" | `/gsd:health` | (none) |
| "verify the last phase" | `/gsd:verify-work` | (none) |
| "plan the next phase" | `/gsd:plan-phase` | (none) |

**Acceptance criteria:**
- All GSD commands have working parameter extraction
- GSD routing does not conflict with team routing (e.g., "plan" could be either -- GSD wins only if "project" or "phase" is in the input)
- `buildDispatch()` output is a valid `/gsd:<action>` string

**Estimated effort:** 0.25 day

**Dependencies:** None (uses existing SkillRegistry)

---

### Task 6: Context Manager

**Description:** Implement ambient greeting, session summarization, and token budget management.

**Files to create/modify:**
- Create: `src/core/context-manager.ts`
- Modify: `src/core/orchestrator.ts` -- replace `getGreeting()` with `ContextManager.buildGreeting()`, add summarization trigger

**ContextManager interface:**

```
class ContextManager {
  constructor(state: StateManager, skills: SkillRegistry)

  // Build the ambient greeting on startup
  buildGreeting(): string
    // Queries: project name, git branch, last session, queue depth, interrupted count, skill count
    // Returns 1-3 lines, "Ready." at the end

  // Get recent exchanges for Tier 2 context
  getRecentExchanges(limit: number): string
    // Returns formatted string of last N user inputs + CoCo responses
    // Used in Tier 2 classification prompt

  // Summarize old exchanges when threshold is reached
  summarizeIfNeeded(sessionId: string, exchangeCount: number): Promise<void>
    // If exchangeCount >= 10, generate summary via Claude query()
    // Store in session_summaries table
    // This is called after each exchange completes

  // Build the context window for a new Claude query
  buildContextWindow(tokenBudget: number): string
    // Assembles: last 2 summaries + last 5 raw exchanges
    // Truncates if over budget
    // Returns a formatted string

  // Record a skill recommendation check
  checkRecommendation(justCompletedSkill: string): string | null
    // Queries skill_sequences for top follow-up
    // Returns suggestion string or null
    // Rate-limited to 1 suggestion per 5 minutes
}
```

**Summarization prompt (sent to Claude with maxTurns: 1):**

```
Summarize this terminal assistant session into 1-3 factual sentences.
Include: what tasks were completed, which skills were used, and any pending/failed work.
Do not be conversational. Be precise.

Exchanges:
${exchanges.map(e => `User: ${e.input}\nCoCo: ${e.output}`).join('\n\n')}
```

**Acceptance criteria:**
- `buildGreeting()` includes project name, branch, last session info, and "Ready."
- `buildGreeting()` never exceeds 3 lines or 80 chars per line
- `summarizeIfNeeded()` fires only when exchange count >= 10
- Summaries are stored in `session_summaries` and retrievable
- `buildContextWindow(1500)` produces output under 1500 tokens (estimated at 4 chars/token)
- `checkRecommendation()` returns null if last suggestion was <5 minutes ago

**Estimated effort:** 1 day

**Dependencies:** Task 1 (schema), Task 3 (skill sequences for recommendations)

---

### Task 7: Orchestrator Integration

**Description:** Wire the new modules into the orchestrator. Replace inline classification with IntentClassifier, add `/correct` meta-command, add recommendation prompts, and replace greeting logic.

**Files to create/modify:**
- Modify: `src/core/orchestrator.ts`

**Changes to orchestrator.ts:**

1. **Constructor:** inject `IntentClassifier`, `LearningStore`, `ContextManager`, `TeamRouter`, `GsdRouter`
2. **handleInput():**
   - Replace `this.classifyIntent(trimmed)` with `await this.intentClassifier.classify(trimmed)`
   - After dispatch, call `this.learningStore.recordSequence(previousSkill, currentSkill)`
   - After dispatch completes, call `this.contextManager.checkRecommendation(skill)` and emit suggestion if non-null
3. **New meta-command `/correct <skill>`:**
   - Get the last intent_log entry
   - Call `this.learningStore.recordCorrection(lastIntentId, skill)`
   - Emit confirmation: "Got it. Next time I'll route that to /team <skill>."
4. **getGreeting():** delegate to `this.contextManager.buildGreeting()`
5. **Remove:** `TEAM_SKILL_TRIGGERS` const, `classifyIntent()` method (moved to intent-classifier.ts)

**OrchestratorDeps update:**

```
interface OrchestratorDeps {
  state: StateManager;
  skills: SkillRegistry;
  sessionManager?: SessionManager;
  taskQueue?: TaskQueue;
  voiceManager?: unknown;
  intentClassifier?: IntentClassifier;   // Phase 4
  learningStore?: LearningStore;          // Phase 4
  contextManager?: ContextManager;        // Phase 4
  teamRouter?: TeamRouter;                // Phase 4
  gsdRouter?: GsdRouter;                  // Phase 4
}
```

**Backward compatibility:** If Phase 4 deps are not injected, orchestrator falls back to inline `classifyIntent()` (the existing code path). This ensures Phases 1-3 still work without Phase 4.

**Acceptance criteria:**
- `handleInput("research OAuth")` calls `IntentClassifier.classify()`, not the inline method
- `/correct team-test` stores correction and emits confirmation
- After a skill completes, recommendation check runs and emits suggestion if applicable
- `getGreeting()` returns context-aware greeting from ContextManager
- Removing Phase 4 deps from constructor falls back to existing behavior (no regression)

**Estimated effort:** 0.5 day

**Dependencies:** Tasks 2, 3, 4, 5, 6 (all new modules must exist)

---

### Task 8: Seed Data — 50-Query Test Set

**Description:** Create a hand-crafted set of 50 natural language inputs with expected skill mappings, covering all 18 team commands and edge cases. This is both test data and cold-start seed data.

**Files to create/modify:**
- Create: `tests/intelligence/test-queries.json`
- Create: `tests/intelligence/accuracy.test.ts`

**Test set structure:**

```json
[
  {
    "input": "I need to review the auth service",
    "expected_skill": "team-review",
    "expected_args_contains": "auth service",
    "category": "unambiguous",
    "notes": "SC-1 from roadmap"
  },
  {
    "input": "look into AWS Lambda cold starts",
    "expected_skill": "team-research",
    "expected_args_contains": "Lambda cold starts",
    "category": "unambiguous"
  },
  {
    "input": "build the API",
    "expected_skill": "team-develop",
    "expected_args_contains": "API",
    "category": "ambiguous",
    "notes": "Could be team-develop or team-plan; team-develop preferred"
  }
]
```

**Coverage targets (50 queries):**
- 18 queries: one per team command (unambiguous)
- 5 queries: GSD commands
- 5 queries: edge cases (multi-match, very short input, typos)
- 5 queries: inputs that should NOT match any skill (general conversation)
- 7 queries: varied phrasing of common intents (synonyms, different word order)
- 5 queries: inputs with corrections already stored (tests learning loop)
- 5 queries: inputs that require Tier 2 (ambiguous enough to fail Tier 1)

**Acceptance criteria:**
- `accuracy.test.ts` runs all 50 queries through `IntentClassifier.classify()`
- Reports accuracy as: `X/50 correct (Y%)`
- Test passes if accuracy >= 45/50 (90%)
- Each incorrect classification is logged with expected vs actual for debugging
- Test runs in <30 seconds (most queries hit Tier 1, only ~5 hit Tier 2)

**Estimated effort:** 0.5 day

**Dependencies:** Task 2 (IntentClassifier must exist to test against)

---

### Task 9: Integration Tests

**Description:** End-to-end tests that verify the full intelligence pipeline: input -> classify -> correct -> re-classify -> recommend.

**Files to create/modify:**
- Create: `tests/intelligence/learning-loop.test.ts`
- Create: `tests/intelligence/context-manager.test.ts`
- Create: `tests/intelligence/routing.test.ts`

**Key test scenarios:**

**learning-loop.test.ts:**
1. Classify "check the auth code" -> routes to team-review
2. User sends `/correct team-test`
3. Re-classify "check the auth code" -> now routes to team-test (confidence 1.0)
4. Verify `routing_corrections` table has 1 row
5. Verify `times_applied` increments on repeated use

**context-manager.test.ts:**
1. `buildGreeting()` with no history -> "project (branch). N skills loaded. Ready."
2. `buildGreeting()` with last session -> includes "Last session: team-research on X."
3. `buildGreeting()` with interrupted sessions -> includes "N interrupted session(s)."
4. `summarizeIfNeeded()` with <10 exchanges -> no summary created
5. `summarizeIfNeeded()` with >=10 exchanges -> summary stored in DB
6. `buildContextWindow(1500)` -> output is under 6000 chars (~1500 tokens)

**routing.test.ts:**
1. TeamRouter extracts correct args for all 13 team skills
2. GsdRouter extracts correct args for all GSD commands
3. "plan the next sprint" routes to team-plan (not gsd:plan-phase)
4. "plan the next project phase" routes to gsd:plan-phase (has "phase" keyword)

**Acceptance criteria:**
- All tests pass with `npm test -- tests/intelligence/`
- No tests require actual Claude API calls (Tier 2 calls are mocked)
- Coverage >80% on intent-classifier.ts, learning-store.ts, context-manager.ts

**Estimated effort:** 0.5 day

**Dependencies:** Tasks 1-7 (all modules must exist)

---

## Test Plan

### Test pyramid

```
                    /\
                   /  \
                  / E2E \         1 test: full pipeline with mocked Claude
                 /--------\
                / Integration \   ~15 tests: module interactions
               /--------------\
              /    Unit tests    \ ~40 tests: individual functions
             /--------------------\
```

### Unit tests (~40 tests)

| Module | Test count | Key assertions |
|--------|-----------|----------------|
| intent-classifier.ts | 12 | Tier 1 regex matches, Tier 2 prompt construction, confidence thresholds, normalization |
| learning-store.ts | 8 | CRUD operations, correction lookup, sequence recording, recommendation threshold |
| context-manager.ts | 8 | Greeting format, summarization trigger, token budget, recommendation rate-limit |
| team-router.ts | 7 | Parameter extraction for all 7 major team skills |
| gsd-router.ts | 5 | Parameter extraction for all 5 GSD commands |

### Integration tests (~15 tests)

| Scenario | Test count |
|----------|-----------|
| Correction loop (classify -> correct -> re-classify) | 3 |
| Skill sequence recommendation | 3 |
| Context window assembly | 2 |
| Orchestrator with IntentClassifier wired in | 4 |
| Backward compatibility (no Phase 4 deps) | 3 |

### Accuracy test (1 test, 50 assertions)

- `tests/intelligence/accuracy.test.ts`
- Runs 50 curated queries, asserts >90% accuracy
- Tier 2 calls mocked to return deterministic results for the 5 ambiguous queries

### Mocking strategy

- **Tier 2 Claude calls:** mocked via `vi.mock()` on the `query()` import. Returns predetermined JSON for each test input.
- **SQLite:** use in-memory database (`:memory:`) for test isolation
- **SkillRegistry:** populated with a fixed set of 18 test skills (not reading from disk)

---

## Execution Order

```
Day 1 (Foundation)
  Task 1: Schema migration           -- 0.5 day
  Task 2: IntentClassifier            -- 1 day (start after Task 1)
  [ Checkpoint: Tier 1 classification passes existing test cases ]

Day 2 (Learning + Routing)
  Task 3: LearningStore               -- 0.5 day
  Task 4: TeamRouter                   -- 0.5 day
  Task 5: GsdRouter                    -- 0.25 day
  [ Checkpoint: corrections stored, parameters extracted ]

Day 3 (Context + Integration)
  Task 6: ContextManager               -- 1 day
  Task 7: Orchestrator integration      -- 0.5 day
  [ Checkpoint: full pipeline works end-to-end manually ]

Day 4 (Testing + Polish)
  Task 8: 50-query test set             -- 0.5 day
  Task 9: Integration tests             -- 0.5 day
  Accuracy tuning                       -- tune regex patterns until >90%
  [ Checkpoint: all tests pass, accuracy >90% ]

Day 5 (Buffer)
  Edge case fixes from testing
  Tier 2 prompt refinement
  Documentation
```

---

## File Summary

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `src/core/state.ts` | Modify | Add 5 new tables + CRUD methods |
| 2 | `src/core/intent-classifier.ts` | Create | Two-tier classification (Tier 1 regex, Tier 2 Claude) |
| 3 | `src/core/learning-store.ts` | Create | Routing corrections, skill sequences, recommendations |
| 4 | `src/integrations/team-router.ts` | Create | NL -> /team command parameter extraction |
| 5 | `src/integrations/gsd-router.ts` | Create | NL -> /gsd command parameter extraction |
| 6 | `src/core/context-manager.ts` | Create | Greeting, summarization, token budget, recommendations |
| 7 | `src/core/orchestrator.ts` | Modify | Wire new modules, add /correct, replace classifyIntent |
| 8 | `tests/intelligence/test-queries.json` | Create | 50-query accuracy test set |
| 9 | `tests/intelligence/accuracy.test.ts` | Create | Automated accuracy test (>90% target) |
| 10 | `tests/intelligence/learning-loop.test.ts` | Create | Correction + re-route integration tests |
| 11 | `tests/intelligence/context-manager.test.ts` | Create | Greeting + summarization tests |
| 12 | `tests/intelligence/routing.test.ts` | Create | Parameter extraction tests |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Intent ambiguity** -- "build the API" could be /team build, /team develop, or /team plan | High | Wrong skill dispatched | Tier 1 trigger order defines priority (develop > plan). When confidence 0.4-0.7, ask one-line confirmation. Learning store remembers corrections. |
| **Cold start** -- no usage data on day one, no corrections, no sequences | High | No recommendations, no learning benefit | Task 8 seeds 50 hand-crafted intent->skill mappings. Tier 1 regex covers 70%+ of inputs without learning data. |
| **Claude API cost for Tier 2** -- using Claude to classify every ambiguous input adds API cost | Medium | Unexpected API spend | Tier 1 handles 70%+ of inputs locally. Tier 2 uses `maxTurns: 1` with no tools (~200 tokens per call). Estimate: <5 Tier 2 calls per hour of use = negligible cost. |
| **Context window bloat** -- long sessions exceed token limits | Medium | Claude errors or degraded responses | Rolling summary after 10 exchanges. Hard cap of 5 raw exchanges + 2 summaries. `buildContextWindow()` enforces token budget. |
| **Tier 2 latency** -- Claude classification adds ~1 second to ambiguous inputs | Low | Noticeable delay on 30% of inputs | Display "Thinking..." indicator during Tier 2. Cache Tier 2 results in `intent_log` for repeated inputs. Most inputs hit Tier 1 (<1ms). |
| **Regression in existing routing** -- moving classification out of orchestrator may break existing behavior | Medium | Skills stop routing correctly | Backward compatibility: if IntentClassifier not injected, orchestrator uses existing inline code. Task 8 accuracy test validates no regression. Run existing test suite before and after. |
| **Learning store pollution** -- user makes incorrect corrections that degrade routing | Low | Persistent misrouting | Add `/uncorrect <input>` command to delete corrections. Corrections table is small and inspectable via `/corrections list`. |
| **GSD vs Team routing conflict** -- "plan" matches both team-plan and gsd:plan-phase | Medium | Wrong skill category | Disambiguation rule: if input contains "project" or "phase", route to GSD. Otherwise, route to team. Documented in Task 5. |

---

## Open Questions (To Resolve During Implementation)

1. **Should Tier 2 classification use the full Claude Code SDK `query()` or the lighter Anthropic API directly?** Using `query()` inherits all config but is heavier. The Anthropic API (`@anthropic-ai/sdk`) would be lighter for pure classification. Decision: start with `query()` for consistency, measure latency, switch to raw API if >2 seconds.

2. **Should corrections be scoped to normalized exact match or fuzzy match?** Exact match is simple and safe. Fuzzy match (e.g., Levenshtein distance < 3) would generalize better but risks false positives. Decision: start with exact match, add fuzzy matching in a follow-up if correction table grows large.

3. **Should session summaries be generated by Claude or by a local heuristic?** Claude produces better summaries but costs an API call per 10 exchanges. A local heuristic (extract skill names + args from exchanges) is free but less readable. Decision: use Claude for summaries, with local fallback if API call fails.
