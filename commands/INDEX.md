# Commands Index

Auto-generated. Run `python3 scripts/build-index.py` to refresh.

**Total: 38 commands across 6 namespaces.**

## design

| Slash | Description |
|-------|-------------|
| [`/design:mermaid`](design/mermaid.md) | Use when the user asks for a diagram or chart: flowchart, sequence, state, class, ER, or XY chart, as SVG, HTML, or terminal ASCII. Builds beautiful-mermaid dia |

## email

| Slash | Description |
|-------|-------------|
| [`/email`](email/_index.md) | Read, search, and manage Outlook emails. Auto-detects Legacy Outlook (AppleScript) vs New Outlook (MIME/HxStore extraction). Subcommands: read, unread, search,  |
| [`/email:read`](email/read.md) | Show latest emails from a specific person. Usage: /email-read alice |
| [`/email:reply`](email/reply.md) | Draft a reply to a specific email. Usage: /email-reply Project Phase 2 Contract Data |
| [`/email:save`](email/save.md) | Save matching emails to a project folder for sync processing. Usage: /email-save alice to emails/ |
| [`/email:search`](email/search.md) | Search emails by subject keywords. Usage: /email-search github webhook |
| [`/email:summary`](email/summary.md) | AI summary of today's emails — key decisions, action items, meetings. No arguments needed. |
| [`/email:thread`](email/thread.md) | Show full email thread by subject. Usage: /email-thread Project Phase 2 |
| [`/email:today`](email/today.md) | Show all emails received today grouped by hour. |
| [`/email:unread`](email/unread.md) | Show all unread emails with count and top 20 list. No arguments needed. |

## eng

| Slash | Description |
|-------|-------------|
| [`/eng:anti-pattern`](eng/anti-pattern.md) | Use when the user asks to audit or fix swallowed errors, empty catch blocks, or catch-and-continue. Triages findings by severity and fixes one at a time with lo |
| [`/eng:local-llm`](eng/local-llm.md) | Check status, change context window, restart, or troubleshoot this machine's local LLM setup (LM Studio + mlx-dspark). Usage: /eng-local-llm [status\|set-contex |

## pm

| Slash | Description |
|-------|-------------|
| [`/pm:sync-init`](pm/sync-init.md) | Set up automated sync for a new project folder: email monitoring (Outlook), file change detection, and auto-update of all documents (PRD, presentations, etc.) e |

## team

| Slash | Description |
|-------|-------------|
| [`/team`](team/_index.md) | Use when the user types /team or wants work handed to the cross-functional 4-layer team (research, develop, review, verify, document, ship). Parses the action a |
| [`/team:arch`](team/arch.md) | Use when asked which files implement a component, to build or refresh .arch/index.json, or to check whether the architecture map drifted. Pins the index to a co |
| [`/team:architecture`](team/architecture.md) | Use when any /team pipeline claims a component owns a path, that module boundaries hold, or that a deliverable follows the architecture. Defines the .arch/index |
| [`/team:communicate`](team/communicate.md) | Use when the user asks for a stakeholder email, launch announcement, status update, incident notice, or onboarding note. Runs the /team communicate pipeline: au |
| [`/team:develop`](team/develop.md) | Use when the user runs /team develop, or the team router picks action develop, to build or fix code through a multi-agent pipeline. Shards files across L2 agent |
| [`/team:document`](team/document.md) | Use when the user asks for a PRD, guide, runbook, API docs, or incident report, or when the team router action is document. Runs the 4-layer documentation pipel |
| [`/team:evidence`](team/evidence.md) | Use when a /team pipeline or PR body makes a quality claim such as tests pass, lint clean, or N% coverage. Defines the evidence protocol (CI-pinned commands, pr |
| [`/team:feedback`](team/feedback.md) | Use when running /team and Layer 2 needs past findings inlined, or when appending Layer 4 learnings after a run. Registry of feedback entries with status lifecy |
| [`/team:fix`](team/fix.md) | Use when the user reports a bug, pastes a failing test or an error log, or asks to debug and fix an issue. Diagnoses root cause, writes a failing regression tes |
| [`/team:plan`](team/plan.md) | Use when the user asks for a plan, roadmap, phase breakdown, or task sequencing, or the /team router picks plan. Runs the L1-L4 research/plan/validate/approve p |
| [`/team:present`](team/present.md) | Use when the user asks for a deck, architecture review board slides, keynote, or demo. Runs the /team present pipeline in the Consulting or Apple format with na |
| [`/team:reanalyse`](team/reanalyse.md) | Use when the user runs /team reanalyse, or already-approved work must be re-checked against current code for regressions. Diffs since the last review, re-verifi |
| [`/team:research`](team/research.md) | Use when the user wants a multi-angle investigation on a topic with sources, or the team router action is research. Runs a research-heavy pipeline across domain |
| [`/team:review`](team/review.md) | Use when the /team router routes action=review, or the user asks for existing code, docs, or a diff reviewed. Scope mapping, 3-5 specialist lenses, cross-review |
| [`/team:roles`](team/roles.md) | Use when selecting roles for a /team run, validating --roles IDs, or adding a new role. Roster of role definitions with layer, category, domain tags, and the sy |
| [`/team:scrape`](team/scrape.md) | Use when the user asks to research URLs or topics across the web, compare sources, or produce a sourced research report. Fans out up to 6 parallel researchers,  |
| [`/team:ship`](team/ship.md) | Use when the user wants an idea taken from concept to a shipped, reviewed product, or when the /team router picks ship. Runs six build stages, seven hard verifi |
| [`/team:test`](team/test.md) | Use when the user asks to add missing tests, close coverage gaps, or prove a suite runs. Runs the /team test pipeline: coverage analysis, test writing, then a r |
| [`/team:think`](team/think.md) | Use when the user runs /team think, asks for options analysis, or wants a brainstorm before deciding. Generates structured options, stress-tests them across rev |
| [`/team:toolkit`](team/toolkit.md) | Use when a /team run must pick the best tool or skill for a capability, or when adding a discovered tool to the registry. Maps each capability to its best tool, |
| [`/team:verify`](team/verify.md) | Use when built work must be checked against its spec, plan, or PRD before shipping, or the team router action is verify. Re-runs the gate from a clean checkout  |

## util

| Slash | Description |
|-------|-------------|
| [`/util:architecture-review`](util/architecture-review.md) | Comprehensive architecture review with design patterns analysis and improvement recommendations |
| [`/util:create-architecture-documentation`](util/create-architecture-documentation.md) | Generate comprehensive architecture documentation with diagrams, ADRs, and interactive visualization |
| [`/util:refactor-code`](util/refactor-code.md) | Use when the user asks to refactor a file, module, or scope while preserving behaviour, for example /util refactor-code src/auth. Fills test gaps first, refacto |
| [`/util:ss`](util/ss.md) | View the latest N screenshots from Desktop (default 1) |
