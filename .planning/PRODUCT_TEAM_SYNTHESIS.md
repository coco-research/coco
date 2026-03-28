# CoCo Platform — Product Team Synthesis
## 8-Agent Strategic Analysis (2026-03-28)

---

## Team Consensus: The 5 Big Moves

After analyzing all 8 reports, these are the moves that every agent agreed on:

### 1. MERGE THE THREE DASHBOARDS
**Reported by:** Senior PM, Frontend PM, UX Designer, B2C PM
- Home, Analytics, and Jarvis overlap 70%+ in data
- **Keep Home + Analytics separate** (user decision — Home = daily driver, Analytics = data/trends)
- **Merge Home + Jarvis** — Jarvis becomes a voice mode/overlay within Home, not a separate page
- Home should show "action cards" (what to DO), not metric cards (what IS)

### 2. UNIFY THE CHAT STORY
**Reported by:** Senior PM, B2C PM, UX Designer
- ChatPage (full Claude subprocess), CocoOrb (lightweight /jarvis/command), and JarvisPage are three different interfaces with different capabilities
- User doesn't know which to use
- **Recommendation:** CocoOrb = quick voice/text ("hey Siri"), Chat = deep work. Remove Jarvis as standalone page.

### 3. MIGRATE TO CLAUDE AGENT SDK
**Reported by:** Principal Engineer, Senior Dev, Senior Architect
- Current `subprocess.Popen` + thread-per-agent is the #1 scalability bottleneck
- Agent SDK provides structured messages, cost tracking, safety hooks, session persistence, subagent support
- This unlocks 10+ concurrent agents, human-in-the-loop, and native Agent Teams integration

### 4. BUILD THE KNOWLEDGE MOAT
**Reported by:** Principal PM, B2C PM, Senior Dev
- CoCo's unique advantage: it ingests from email, voice, Jira, Confluence and connects dots across sources
- No competitor has this — double down
- "Cross-source insight engine" is the killer feature: "Sarah mentioned the same issue in email and meeting"
- Auto-classify, auto-create-todos, auto-inject context into agents

### 5. OPEN SOURCE THE CORE
**Reported by:** Principal PM, Senior Dev
- Being private is the single biggest growth blocker
- Paperclip: 32K stars. Everything Claude Code: 100K stars.
- Open-core model: free PM dashboard + agent management, paid Jarvis/voice/replay
- Even if velocity drops, community continues

---

## Cross-Report Theme: "SIMPLIFY THE SURFACE"

Every report independently arrived at the same conclusion: CoCo has too many surfaces for the same data. The fix is not adding features — it's subtracting pages.

**Current:** 15 pages, 3 dashboards, 3 chat interfaces, 9 tabs in ProjectDetail
**Target:** 10 pages, 1 dashboard, 2 chat modes (quick + deep), 4 tabs in ProjectDetail

| Current | Action | Result |
|---------|--------|--------|
| Home + Analytics + Jarvis | Merge into Home + voice overlay | 1 page |
| Goals (standalone) | Fold into Project "Work" tab + Home | Remove page |
| Activity (standalone) | Fold into Inbox as a filter | Remove page |
| ProjectDetail (9 tabs) | Reduce to 4: Overview, Work, Knowledge, Settings | Simpler |
| Chat + CocoOrb + Jarvis | CocoOrb = quick, Chat = deep, Jarvis = voice mode | 2 modes |

---

## Feature Priority Matrix (All 8 Agents)

### Tier 1: Do Immediately (next 2 weeks)

| Feature | Champions | Impact | Effort |
|---------|-----------|--------|--------|
| Toast feedback on all mutations | Frontend PM | High | 2h |
| Page transition animations | UX Designer, Frontend PM | High | 1h |
| j/k list navigation + keyboard actions | Frontend PM, UX Designer | High | 4h |
| ~~Merge Home + Analytics~~ | -- | -- | **REJECTED** — kept separate by design. Merge Home + Jarvis instead. |
| Persist inbox read state | Senior PM, Frontend PM | Medium | 4h |
| Inbox batch actions | Senior PM | Medium | 1 day |
| Fix silent error handlers → toast | Frontend PM | Medium | 1h |
| Sidebar collapse toggle | UX Designer | Medium | 4h |

### Tier 2: Do in Sprint 4 (next month)

| Feature | Champions | Impact | Effort |
|---------|-----------|--------|--------|
| Agent SDK migration | Principal Eng, Senior Dev, Architect | Critical | 2-3 weeks |
| CoCo MCP server | Senior Dev | High | 1 week |
| Event contract + durable EventBus | Architect, Principal Eng | High | 1 week |
| Focus View ("what should I do right now?") | B2C PM | High | 3 days |
| Cross-source insight engine | Principal PM, B2C PM | High | 2 weeks |
| Morning podcast briefing | Principal PM, B2C PM | High | 1 week |
| Agent Replay (shareable HTML) | Principal PM | High | 1 week |
| Repository pattern extraction | Architect | Medium | 2 weeks |

### Tier 3: Do in Sprint 5+ (next quarter)

| Feature | Champions | Impact | Effort |
|---------|-----------|--------|--------|
| Open-source core + paid tiers | Principal PM | Strategic | 2-3 weeks |
| Native Agent Teams integration | Principal PM, Senior Dev | High | 2 weeks |
| Git worktree per agent | Senior Dev | Medium | 1 week |
| Adaptive notifications | B2C PM | Medium | 1 week |
| Weekly Clarity Report ("CoCo Wrapped") | B2C PM | Medium | 3 days |
| Extension/plugin system | Architect | Medium | 3 weeks |
| Zero-config automation suggestions | B2C PM | Medium | 2 weeks |
| Deepgram STT + Kokoro TTS | Voice Specialist (prev) | Medium | 1 week |

---

## Architecture Consensus

| Topic | Consensus |
|-------|-----------|
| **Database** | Stay on SQLite 12+ months. Add connection pooling + async. |
| **Agent runtime** | Migrate to Claude Agent SDK (from raw subprocess) |
| **Real-time** | Keep SSE. Add WebSocket only for human-in-the-loop agent control. |
| **State management** | TanStack Query for server state + Zustand for SSE-derived real-time state |
| **Event system** | Make EventBus durable (persist to table). Define typed event contracts. |
| **Cloud path** | Not needed yet. Prepare with storage abstraction + pluggable event bus. |
| **Plugins** | Not yet. Stabilize core first. |
| **Testing** | Add pytest suite for critical paths. Backend tests are the gap. |

---

## UX Design Consensus

| Principle | Description |
|-----------|-------------|
| **Calm Authority** | CoCo is a brain, not a chatbot. Quiet when things are fine. |
| **Time-Aware** | Show what matters NOW, not what IS. Action cards, not metric cards. |
| **Progressive Depth** | Scannable in 2s, detailed in 10s, full depth on demand. |
| **One Voice** | CoCo speaks in first person. Every label, error, empty state = one character. |
| **Narrative Metrics** | "12 of those are high priority" not "Open Todos: 47" |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Anthropic ships native agent dashboard | 60% | High | Ship CoCo's PM layer first — Anthropic won't build todos/goals/knowledge |
| Claudia (YC-backed) gets traction | 40% | Medium | CoCo's knowledge moat + voice = differentiation Claudia doesn't have |
| Rate limit costs make agents impractical | 30% | High | CoCo's cost tracking + budget alerts directly address this |
| Momentum loss (solo developer) | 50% | Critical | Open-source to build community velocity |
| Linear Agent absorbs PM + agent management | 20% | High | Linear is SaaS-team, not local-first solo PM. Different market. |

---

## The PMF Test

CoCo doesn't have product-market fit yet. The honest test:
1. Use CoCo every workday for 4 weeks straight
2. Jarvis replaces your manual morning status check
3. >50% of agent launches go through the UI (not CLI)
4. You feel anxiety when CoCo is down

If all 4 are true, it's ready for others.

---

## Summary

CoCo occupies a genuinely unique niche: **PM-centric AI agent control plane with knowledge ingestion**. No competitor has this combination. The strategic priority is not more features — it's:

1. **Simplify** the surface (merge dashboards, unify chat)
2. **Strengthen** the foundation (Agent SDK, durable events, async DB)
3. **Ship** the moat (cross-source insights, auto-classify, morning briefing)
4. **Share** the story (open-source, agent replay, weekly digest)

The window is narrowing. Linear Agent, Claudia, and Anthropic's enterprise dashboard are converging on adjacent spaces. CoCo's advantage is that it's built for the solo AI-native PM — a persona nobody else is serving. The next 90 days determine whether CoCo becomes the standard or gets absorbed.
