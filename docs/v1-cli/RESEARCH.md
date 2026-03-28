# Project CoCo — Research Brief

**Date:** 2026-03-19
**Researchers:** Domain Researcher, Technical Analyst, Business Analyst, UX Researcher

---

## Executive Summary

CoCo is 70% built. The brain (/team system with 34 roles, 13 actions, toolkit registry, feedback loop), the skills (44 commands, 28 skills, 13 agents), and the integrations (email, MCP, GSD) already exist. What's missing is the **wrapper layer**: always-on presence, voice I/O, a visual dashboard, proactive suggestions, and task queuing.

**Recommended architecture:** Node.js + Claude Agent SDK + Ink (React-for-terminal). The SDK inherits all existing commands, skills, agents, hooks, and MCP servers automatically. CoCo is the persistent process that dispatches into our existing ecosystem.

**Nothing like this exists.** The closest tools (Open Interpreter, isair/jarvis, TmuxAI) each solve one piece but none integrate voice + terminal orchestration + persistent skills + learning loop.

---

## Competitive Landscape

### What Exists (14 tools evaluated)

| Tool | Stars | Best Feature | Missing for CoCo |
|------|-------|-------------|-------------------|
| Claude Code | N/A | Skills + hooks + MCP + 1M context | No daemon, no voice, no dashboard |
| Warp | N/A | Agent mode, blocks UI | Closed source, can't extend |
| OpenAI Codex CLI | 66K | Voice input (experimental), Rust TUI | OpenAI only, no daemon |
| Gemini CLI | 98K | Free 1M context, Google Search | No voice, no daemon |
| Aider | 42K | Best git integration, voice input | Code-only, no general tasks |
| Open Interpreter | 63K | General-purpose execution | AGPL, no daemon, no MCP |
| Fabric | 40K | Pattern library, speech-to-text | Pipe-based, not conversational |
| isair/jarvis | 113 | Always-on voice, MCP, memory | Tiny community, not terminal-native |
| TmuxAI | 1.7K | Observe all panes passively | Observation only, no execution |
| CLI Agent Orchestrator | 335 | Supervisor/worker via tmux+MCP | Not user-facing |

### Key Insight
No tool combines: **always-on daemon + voice + terminal orchestration + extensible skills + learning loop**. This is the CoCo gap.

---

## Technical Architecture (Recommended)

### Option B: Node.js + Claude Agent SDK + Ink

```
coco/
├── src/
│   ├── core/
│   │   ├── orchestrator.ts      # Main loop: intent → route → execute
│   │   ├── session-manager.ts   # Spawn/track/resume Claude SDK sessions
│   │   ├── state.ts             # SQLite: tasks, sessions, history
│   │   └── skill-registry.ts    # Reads ~/.claude/commands/ at startup
│   ├── ui/
│   │   ├── App.tsx              # Ink root: dashboard layout
│   │   ├── SessionPanel.tsx     # Live output per session
│   │   ├── StatusBar.tsx        # Persistent status line
│   │   └── CommandInput.tsx     # Text input (voice feeds here)
│   ├── voice/
│   │   ├── listener.ts          # whisper.cpp --stream → text
│   │   └── speaker.ts           # macOS `say` for TTS
│   └── integrations/
│       ├── team-router.ts       # Natural language → /team commands
│       ├── gsd-router.ts        # → /gsd commands
│       └── email-router.ts      # → /email commands
├── coco.db                      # SQLite state
└── package.json
```

### Why This Approach
- SDK inherits ALL 44 commands, 28 skills, 13 agents, MCP servers, hooks
- Ink gives rich terminal UI (collapsible blocks, status bar, live updates)
- SQLite for persistent state across restarts
- whisper.cpp for local voice (no cloud dependency)
- 100% reuse of existing skill ecosystem

### Alternatives Considered
- **Shell script wrapper** — good for POC (1 day), bad for real thing
- **Custom command inside Claude Code** — this IS /team already, can't add daemon/voice
- **Direct API app** — rebuilds everything from scratch, zero reuse

---

## What We Already Have (Reusable)

| Asset | Count | CoCo Role |
|-------|-------|-----------|
| /team commands | 14 actions | CoCo's action vocabulary |
| Specialist roles | 34 | CoCo's workforce |
| Toolkit registry | 16 entries | CoCo knows which tools to use |
| Feedback loop | Growing | CoCo learns from every run |
| GSD commands | 32 | Project orchestration |
| Email commands | 10 | Communication integration |
| Screenshot reader | 9 variants | Visual awareness |
| Project sync | Cron-based | File/email monitoring |
| Memory system | 2-layer | Cross-session context |
| Domain auto-detection | Built into /team | Project awareness |

---

## UX Design

### CoCo Personality
- Text-first, voice-optional
- Ambient context greeting ("Ready." not "How can I help?")
- Risk-proportional autonomy (read-only = just go, write = confirm)
- Drip-feed status during pipelines
- Headlines then details on completion
- Task queuing for rapid-fire commands
- Calm failure handling with options (A/B/C)

### Terminal Layout (Single-pane, collapsible blocks)

```
┌─────────────────────────────────────────────────────┐
│ CoCo | how-i-pm-with-ai (main) | L2 3/4 | 2:34    │
├─────────────────────────────────────────────────────┤
│ [L1 Research] ........................... done  (v) │
│ [L2 Execute] ............................. 3/4  (v) │
│   senior-backend-eng: Working on service.ts...      │
│ [L3 Review] ............................. wait  ( ) │
│ [L4 Synthesis] .......................... wait  ( ) │
├─────────────────────────────────────────────────────┤
│ > _                                                 │
└─────────────────────────────────────────────────────┘
```

---

## Phased Build Plan

| Phase | Scope | Effort |
|-------|-------|--------|
| 0 | Shell script POC — text input → claude -p → stream output | 1 day |
| 1 | Node.js + Ink app, single session, skill registry, SQLite | 3-4 days |
| 2 | Parallel sessions, dashboard, tmux support | 3-4 days |
| 3 | Voice (whisper.cpp STT + macOS say TTS) | 2-3 days |
| 4 | Intent classification, natural language routing | 3-5 days |
| 5 | Proactive mode (file watch, email triggers) | Ongoing |

### Quick Wins (Today)
1. Natural language routing without /team prefix — CLAUDE.md change
2. macOS notifications on completion — osascript one-liner
3. CoCo personality prompt — CLAUDE.md prefix

---

## Tools to Salvage From

| Tool | What to Take | How |
|------|-------------|-----|
| TmuxAI | Pane-reading pattern for ambient awareness | Study their observe mode |
| voiceAgentForTerminal | Deepgram STT/TTS integration pattern | Reference their voice pipeline |
| isair/jarvis | Always-on architecture, memory design | Study, don't fork |
| Fabric | Pattern library concept | Already have this as toolkit registry |
| CLI Agent Orchestrator | Supervisor/worker via tmux | Study their MCP inter-agent pattern |
