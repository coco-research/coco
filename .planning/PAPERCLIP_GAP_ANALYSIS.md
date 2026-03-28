# Paperclip vs CoCo Platform — Gap Analysis

**Date:** 2026-03-27
**Reference:** ~/projects/paperclip-reference/ (running on :3100)
**Source:** Deep side-by-side UX comparison of both codebases

---

## Tier 1: What Users Will Notice Immediately

| Gap | Paperclip | CoCo | Effort |
|-----|-----------|------|--------|
| **Inline editing** | Click any title/description → edit in place | Everything read-only | 2-3 days |
| **Properties panel** | Right slide-out panel with editable fields | No right panel | 1-2 days |
| **"New Issue" button** | Prominent action at top of sidebar | No primary action button | 0.5 day |
| **Breadcrumbs** | Full path: Company → Project → Issue | Just page title | 1 day |
| **Company/project-scoped URL** | `/ABC/dashboard`, `/ABC/issues/PAP-123` | `/projects`, `/inbox` (no scoping in URL) | 1 day |
| **Keyboard shortcuts** | Cmd+K full palette, j/k nav, c to create | Cmd+K exists but minimal | 1 day |

---

## Tier 2: What Power Users Will Miss

| Gap | Paperclip | CoCo |
|-----|-----------|------|
| **Issue lifecycle** | backlog → active → done, with transitions | Todos have status but no workflow engine |
| **Agent org chart** | Visual hierarchy with reporting lines | Stations are flat |
| **Live indicators** | Pulsing blue dot for running agents, real-time SSE | 3s polling, no live indicator |
| **Unread state machine** | 3-state: visible → fading → hidden | Binary: visible or dismissed |
| **Mobile responsive** | Full mobile nav, swipe-to-archive, sm: breakpoints | Desktop-only, no mobile layout |
| **Comment threads** | Inline comments on issues with mentions | No commenting system |
| **Approval workflows** | Budget approval, agent join requests | Draft approve/reject only |
| **Company export/import** | Export full config as template | No project templates |
| **Design guide page** | Living component showcase at `/design-guide` | No internal design system docs |

---

## Tier 3: Architecture Differences (Not Visual)

| Difference | Paperclip | CoCo |
|-----------|-----------|------|
| **Database** | PGlite (embedded Postgres) | SQLite (hub.db + platform.db) |
| **Real-time** | SSE with event streaming | Polling (3s for stations, 30s for dashboard) |
| **Plugin system** | Full SDK with slot outlets | None — monolithic |
| **Multi-user** | Board user auth, agent auth, company ACLs | Single user, no auth |
| **Agent adapters** | 6+ (Claude Code, Codex, Cursor, OpenClaw, etc.) | Claude Code CLI only |
| **Issue prefix** | PAP-123 identifier system | UUIDs |

---

## What CoCo Has That Paperclip Doesn't

| CoCo Exclusive | Why It Matters |
|---|---|
| **Knowledge Hub integration** | Emails, voice memos, Jira, Confluence ingested and searchable |
| **Classification engine** | Auto-route content to projects with learning |
| **Health monitoring** | Per-adapter source health (email/voice/jira/conf) |
| **PM-specific workflow** | Draft approvals, action item extraction, meeting note context |
| **Brain.json learning** | People graph, attention rules, observed routing patterns |
| **Cost tracking** | Per-model, per-feature API cost breakdown |
| **CoCo CLI integration** | The entire /coco skill system backing the UI |

---

## Priority Recommendations (Top 5 High-Impact)

If you want CoCo to feel as polished as Paperclip in the shortest time:

1. **Properties panel** (right slide-out) — makes project detail feel real
2. **Inline editing** on titles — makes everything feel interactive, not just a display
3. **Live pulsing indicators** on stations — makes the app feel alive
4. **Breadcrumb navigation** — gives spatial awareness
5. **Mobile responsive basics** — sm: breakpoints on sidebar + lists

---

## Paperclip Design Principles (Steal These)

1. **Dense but scannable.** Maximum information without clicks to reveal. Whitespace separates, not pads.
2. **Keyboard-first.** Global shortcuts (Cmd+K, C, [, ]). Power users rarely touch the mouse.
3. **Contextual, not modal.** Inline editing over dialog boxes. Dropdowns over page navigations.
4. **Dark theme default.** Neutral grays (OKLCH), not pure black. Accent colors for status/priority only. Text is the primary visual element.
5. **Component-driven.** Reusable components that capture style conventions.

**Progressive disclosure pattern:**
- Top layer: human-readable summary
- Middle layer: checklist/steps/artifacts
- Bottom layer: raw logs/tool calls/transcript

---

## Paperclip Key Components to Reference

| Our Component | Paperclip Reference File |
|---|---|
| ProjectSwitcher | `ui/src/components/CompanySwitcher.tsx` + `ui/src/context/CompanyContext.tsx` |
| Sidebar sections | `ui/src/components/Sidebar.tsx` (SidebarSection pattern) |
| GoalTree | `ui/src/components/GoalTree.tsx` |
| EntityRow | `ui/src/components/EntityRow.tsx` |
| Inbox | `ui/src/pages/Inbox.tsx` (polymorphic items, dismiss animation) |
| Dashboard metrics | `ui/src/pages/Dashboard.tsx` (MetricCard pattern) |
| Project detail tabs | `ui/src/pages/ProjectDetail.tsx` (tab persistence, scoping) |
| Dark theme | `ui/index.html` (inline script) + `ui/src/index.css` (.dark class) |
| Station detail panel | `ui/src/components/PropertiesPanel.tsx` (slide-in panel) |
| InlineEditor | `ui/src/components/InlineEditor.tsx` (click-to-edit text) |
| Breadcrumbs | `ui/src/components/ui/breadcrumb.tsx` + context |
| Design guide | `ui/src/pages/DesignGuide.tsx` (living showcase) |
| Theme context | `ui/src/context/ThemeContext.tsx` |
| Design system | `ui/src/index.css` (@theme inline block, OKLCH values) |

---

## UX Maturity Scorecard

| Dimension | Paperclip | CoCo |
|-----------|-----------|------|
| Feature Completeness | 95% — Production-ready | 50% — MVP with intentional gaps |
| Visual Polish | 85% — Polished, consistent | 80% — Clean, functional |
| Animation Sophistication | 90% — Multi-phase, purpose-driven | 70% — Standard, reusable |
| Information Density | 90% — High, carefully organized | 70% — Moderate, spaced out |
| Mobile Experience | 85% — Thoughtful responsive design | 60% — Basic responsive |
| Conceptual Clarity | 80% — Complex but navigable | 95% — Clear mental model |
| First-Time Learnability | 65% — Steep learning curve | 85% — Intuitive project-centric flow |
| Dark Theme Quality | 90% — Sophisticated color system | 85% — Good, vibrant accent color |
| Component Reusability | 85% — Well-abstracted patterns | 75% — Less componentization |
| Accessibility | 75% — Good but not perfect | 70% — Adequate |
| **Overall UX Maturity** | **Professional** — Ready for enterprise | **Pragmatic** — Ready for personal use |
