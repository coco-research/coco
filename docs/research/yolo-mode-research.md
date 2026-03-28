# CoCo YOLO Mode — Research Report
**Date:** 2026-03-27
**Status:** All 3 phases complete.

---

## 1. Current CoCo YOLO State

| Feature | Status |
|---|---|
| 3 modes (careful/normal/yolo) | Defined in SKILL.md Section 17 |
| Timed YOLO (`/coco yolo 30m`) | Defined |
| Project-scoped YOLO | Defined |
| Confidence thresholds (0.85 auto / 0.70 skip) | Defined |
| Safety caps (10 Jira, 20 drafts) | Defined |
| Always-ask list (comms, push, delete) | Defined |
| YOLO report (`/coco log`) | Defined |
| Permissions matrix per action type | Defined |

**Gap:** YOLO is purely a permission bypass with caps. No intelligence — can't classify actions, learn from patterns, or adapt based on context.

---

## 2. Claude Code Auto Mode (launched March 24, 2026)

### Architecture: Two-Layer Defense

| Layer | Purpose |
|---|---|
| Input layer | Server-side prompt-injection probe scans tool outputs before they enter agent context |
| Output layer | Transcript classifier evaluates actions in 2 stages |

**Stage 1:** Fast single-token filter ("block"/"allow")
**Stage 2:** Chain-of-thought reasoning only if Stage 1 flags the action

### Critical Design Insight
The classifier sees ONLY user messages and tool commands. Claude's own reasoning and tool results are STRIPPED OUT. This prevents the agent from crafting persuasive justifications to manipulate the classifier.

### 6 Permission Modes

| Mode | Behavior |
|---|---|
| `plan` | Read-only |
| `default` | Prompts for every edit and command |
| `acceptEdits` | Auto-approves file edits; prompts for Bash/network |
| `auto` | No prompts. Background AI classifier reviews each action |
| `dontAsk` | Auto-denies everything not in allowlist. For CI |
| `bypassPermissions` | Skips all checks. Containers/VMs only |

### Auto Mode — Always Allowed vs Always Blocked

**Always Allowed:**
- File reads, searches, code navigation
- In-project file edits (VCS-reviewable)
- Installing deps from lock files
- Read-only HTTP requests
- Pushing to your own branch

**Always Blocked:**
- `curl | bash` or executing downloaded code
- Sending sensitive data to external endpoints
- Production deploys and migrations
- Mass deletion on cloud storage
- Force push, pushing to `main`
- Granting IAM/repo permissions
- Installing persistence (SSH keys, cronjobs)
- Modifying shared infrastructure

### Fallback Behavior
3 consecutive denials or 20 total in one session -> auto mode pauses, falls back to manual prompting. In headless mode, terminates session. Not configurable.

### On Entering Auto Mode
Claude Code DROPS broad allow rules that would bypass the classifier: `Bash(*)`, wildcarded interpreters like `Bash(python*)`, package-manager run commands, and any `Agent` allow rule. Narrow rules like `Bash(npm test)` carry over.

### Performance Metrics

| Metric | Rate |
|---|---|
| False positive (blocked safe action) | 0.4% |
| False negative (synthetic exfiltration) | 5.7% |
| False negative (overeager/ambiguous consent) | 17% |

### Sources
- [Anthropic Engineering: Claude Code Auto Mode](https://www.anthropic.com/engineering/claude-code-auto-mode)
- [Claude Code Docs: Permission Modes](https://code.claude.com/docs/en/permission-modes)
- [Simon Willison Analysis](https://simonwillison.net/2026/Mar/24/auto-mode-for-claude-code/)

---

## 3. AI Coding Assistants — Autonomous Modes Comparison

### Tool-by-Tool

**Cursor AI — Agent Mode / YOLO Mode**
- YOLO mode auto-runs terminal commands without approval
- Guardrails: allowlist, denylist, file-deletion checkbox
- VULNERABILITY: File-deletion checkbox bypassed via shell (`rm -rf`). Rules injectable via `.mdc` files. Incident: Cursor in YOLO mode deleted its own installation.

**Devin AI (Cognition)**
- Fully autonomous inside isolated cloud sandbox (Linux VM)
- Cannot access production DBs, host system, or other sandboxes
- Output is always a PR, never a direct deploy
- SOC 2 Type II certified

**Aider**
- `--yes-always` flag removes all confirmation gates
- Architect mode: 2-model pipeline (Architect plans, Editor applies)
- No sandbox, no action classifier. Relies on OS file permissions.

**OpenHands (formerly OpenDevin)**
- Docker-based sandbox isolation
- SecurityAnalyzer (LLM-based) is broken — evaluates AFTER execution, not before
- 64k+ GitHub stars

**SWE-agent**
- Isolated cloud sandboxes
- Middleware hooks for custom validation/approval/logging
- No confidence scoring

**Cline (VS Code)**
- 8 granular auto-approve categories (read project/all, edit project/all, safe/all commands, browser, MCP)
- `requires_approval` flag per command (dynamic model assessment)
- Checkpoint/rollback system for file edits
- YOLO mode approves everything — no explicit always-blocked list

**Windsurf / Cascade**
- Background planning agent continuously refines long-term plans
- Rulebooks with NEVER/ALWAYS security flags
- Checkpoint reversion
- Admin Portal for enterprise controls
- MCP server whitelisting

### Comparison Matrix

| Dimension | Cursor | Devin | Aider | OpenHands | SWE-agent | Cline | Windsurf | Claude Code |
|---|---|---|---|---|---|---|---|---|
| Autonomy model | YOLO toggle | Always auto (sandbox) | `--yes-always` | Full agent (Docker) | Full agent (sandbox) | 8-category toggles | Planning agent | 3-tier classifier |
| Sandbox | None | Cloud VM | None | Docker | Cloud | None | None | Optional Docker |
| Action classifier | None | None (sandboxed) | None | Broken LLM | Hooks | Per-command flag | Rulebook flags | 2-stage LLM (Sonnet) |
| Always-blocked | None reliably | Production/host | None | Container boundary | Production | None | Via NEVER flags | 20+ categories |
| Rollback | Git | PR-based | Git | None | Patch | Checkpoint | Checkpoint | Git |
| Confidence scoring | None | None | None | Broken | None | Implicit | None | Quantified |

### Sources
- [Cursor Agent Product Page](https://cursor.com/product)
- [The Register: Cursor YOLO Safeguards Bypassed](https://www.theregister.com/2025/07/21/cursor_ai_safeguards_easily_bypassed/)
- [Devin Enterprise Security](https://docs.devin.ai/enterprise/security/enterprise-security)
- [Cline Auto Approve Docs](https://docs.cline.bot/features/auto-approve)
- [Windsurf Cascade Docs](https://docs.windsurf.com/windsurf/cascade/cascade)

---

## 4. Agent Framework Patterns

### Framework Analysis

**LangGraph (LangChain)** — Interrupt-based human-in-the-loop
- `interrupt()` pauses graph execution, emits JSON payload to caller
- Resume via `Command(resume=value)`
- Agent Inbox UI for managing interrupt queues
- Pre-interrupt operations must be idempotent

**AutoGen (Microsoft)** — Conversation-based human proxy
- `UserProxyAgent` blocks team execution for human input
- `HandoffMessage` for structured agent-to-human delegation
- `max_turns=1` for turn-by-turn oversight

**Semantic Kernel (Microsoft)** — Function invocation filters
- Auto mode (SK invokes functions) vs Manual mode (caller decides)
- Manual/auto toggle is per-request — dynamic autonomy levels

**CrewAI** — Task guardrails + human input
- `human_input: true` per task
- Guardrails: validation functions returning (bool, feedback)
- Caps: `max_rpm`, `max_execution_time`, `max_iter` (default 20)
- `code_execution_mode: "safe"` (Docker)

**Mastra** — Most sophisticated approval system
- Per-tool `requireApproval: true` + global `requireToolApproval`
- Runtime suspension: tools call `suspend()` with typed schemas
- Auto-resumption from natural language using `resumeSchema`
- Supervisor propagation: approval bubbles up through multi-agent hierarchies
- Guardrails: PromptInjectionDetector, PIIDetector, ModerationProcessor

**SCOPE** — Purpose-built safety framework (329 stars)
- Defense in depth: Fast ML safety (~50ms) -> LLM compliance -> Decision engine
- Role-based IAM (USER/STAFF/ADMIN/SYSTEM)
- Escalation queue: SQLite-backed, confidence threshold (default 0.6)
- PCI-DSS/SOC2 compliant audit trails

**Invariant** — Transparent proxy guardrails (401 stars)
- Sits between app and MCP servers/LLM providers
- Declarative policy rules for permitted/forbidden actions
- Zero code changes to existing agents

### Consolidated Patterns

| Pattern | Best Example | CoCo Has It? |
|---|---|---|
| Tiered permissions (read/write/execute) | SCOPE, Semantic Kernel | Partial |
| Confidence-based auto-approval | SCOPE (0.6 threshold), Mastra | Yes (0.85/0.70) |
| Reversible vs irreversible classification | Mastra, LangGraph | No |
| Audit logging | SCOPE (PCI-DSS), Invariant | No (summary only) |
| Time-boxed autonomy | CrewAI (max_execution_time) | Yes (timed YOLO) |
| Per-tool autonomy | Mastra, Semantic Kernel, Cline | No |
| Rollback/idempotency | LangGraph, Mastra | No |
| Budget/cost caps | CrewAI (max_rpm, max_iter) | Partial (session caps) |
| Escalation queues | SCOPE, LangGraph agent-inbox | Partial (queue.json) |
| Fallback on repeated failures | Claude Code (3/20 threshold) | No |

---

## 5. Key Insights for CoCo YOLO

### Industry Consensus
> "YOLO mode is a liability." Every tool with blanket auto-approve has produced incidents. The industry is moving toward graduated, intelligent autonomy.

### Patterns to Steal

1. **From Claude Code:** Classifier that can't be fooled by its own reasoning. 3-tier action classification. Fallback on repeated failures. Broad permissions stripped on entry.

2. **From Cline:** 8-category granular toggles instead of binary on/off. Per-command dynamic `requires_approval` flag.

3. **From Mastra:** Per-tool `requireApproval`. Runtime suspension with typed schemas. Supervisor propagation in multi-agent chains.

4. **From SCOPE:** Defense-in-depth (fast check -> LLM check -> decision engine). Escalation queue with confidence threshold. Audit trail.

5. **From Windsurf:** NEVER/ALWAYS flags in rulebooks. Background planning agent that refines before executing.

---

## 6. Build Plan

### Phase 1: Quick Wins
- Per-tool autonomy flags in config.json
- Richer audit log (append-only JSONL with reversibility tags)
- Dry-run preview on YOLO activation

### Phase 2: Core Upgrades
- Action classifier (lightweight, context-aware)
- Escalation queue for uncertain items (0.70-0.85 range)
- Learning from overrides (feed back into brain.json)
- Fallback on repeated bad calls (auto-downgrade to normal)

### Phase 3: Advanced
- YOLO profiles (triage/pm/full)
- Adaptive thresholds per project
- Time-aware autonomy (morning = higher, pre-deadline = lower)
- Supervisor propagation in verification gates
