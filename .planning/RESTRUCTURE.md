# CoCo Platform — Restructure Plan (Paperclip-Inspired)

**Date:** 2026-03-27
**Status:** Proposed
**Reference:** ~/projects/paperclip-reference/

---

## 1. Design Philosophy (Stolen from Paperclip)

1. **Dense but scannable.** Maximum information without clicks to reveal. Whitespace separates, not pads.
2. **Keyboard-first.** Cmd+K, j/k navigation. Power users rarely touch the mouse.
3. **Contextual, not modal.** Inline editing over dialog boxes. Dropdowns over page navigations.
4. **Dark theme default.** Neutral grays (OKLCH), not pure black. Accent colors for status/priority only.
5. **Output-first.** Work is not done until the user can see the result.

**New for CoCo:**

6. **Project-as-container.** Every data surface scopes to the active project. Global view is the exception, not the default.
7. **Inbox is the action surface.** Dashboard shows health; Inbox shows what needs YOU.
8. **Three-step mental model:** Ingest → Decide → Act.

---

## 2. Navigation Restructure

### Current (12 flat items)
```
Dashboard, Projects, Stations, Knowledge, Decisions, People, Todos, Tasks, Chat, Costs, Activity, Settings
```

### Proposed (8 items, 4 groups — inspired by Paperclip's 5-section sidebar)

```
┌─────────────────────────────┐
│ [ProjectSwitcher]           │  ← like Paperclip's CompanySwitcher
│ 🔍 Cmd+K                   │
├─────────────────────────────┤
│ HOME                        │
│   📊 Dashboard              │  /dashboard
│   📬 Inbox                  │  /inbox (NEW — replaces Decisions)
├─────────────────────────────┤
│ WORK                        │
│   📁 Projects               │  /projects (list + /:id detail)
│   ✅ Todos                  │  /todos (absorbs Tasks)
│   🎯 Goals                  │  /goals (NEW)
├─────────────────────────────┤
│ INTELLIGENCE                │
│   📚 Knowledge              │  /knowledge
│   💬 Chat                   │  /chat
├─────────────────────────────┤
│ SYSTEM                      │
│   🤖 Stations               │  /stations
│   💰 Costs                  │  /costs
│   ⚙️  Settings              │  /settings
│   📜 Activity               │  /activity (collapsed by default)
├─────────────────────────────┤
│ [User · v1.1]              │
└─────────────────────────────┘
```

**Changes:**
- **ProjectSwitcher** at top (like Paperclip's CompanySwitcher) — selecting a project scopes everything
- **Inbox** replaces Decisions — unified action surface (decisions + overdue + health alerts + approvals)
- **Goals** added — hierarchical goal tree linking to todos
- **Tasks** removed — merged into Todos
- **People** removed from nav — moved to project detail sub-tab + Settings
- **Activity** collapsed by default — still accessible but not prominent

### Sidebar Implementation Pattern (from Paperclip)

```tsx
// Grouped sections with SidebarSection component
<SidebarSection label="HOME">
  <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/dashboard" />
  <SidebarItem icon={Inbox} label="Inbox" to="/inbox" badge={pendingCount} badgeTone={urgentCount > 0 ? "danger" : "default"} />
</SidebarSection>

<SidebarSection label="WORK">
  <SidebarItem icon={FolderOpen} label="Projects" to="/projects" />
  <SidebarItem icon={CheckSquare} label="Todos" to="/todos" />
  <SidebarItem icon={Target} label="Goals" to="/goals" />
</SidebarSection>
```

---

## 3. Project-as-Container (The Big Architectural Shift)

### Paperclip's Pattern
- URL: `/:companyPrefix/dashboard`, `/:companyPrefix/issues`
- CompanyContext stores selectedCompanyId in React Context + localStorage
- All API queries include companyId — auto-refetch on switch
- CompanySwitcher dropdown at top of sidebar

### Our Adaptation

**ProjectSwitcher** at top of sidebar:
- Dropdown lists all active projects from hub.db
- "All Projects" option for global view
- Selected project stored in React Context + localStorage
- All data-fetching hooks accept optional `projectId` filter

**Project Detail Page** (`/projects/:id`):
Sub-tabs (inspired by Paperclip's ProjectDetail):

| Tab | Content | Source |
|-----|---------|--------|
| Overview | Project summary, health, recent activity | hub.db + brain.json |
| Knowledge | Emails, voice memos, Jira, Confluence scoped to project | hub.db content table |
| Stations | Stations assigned to this project | platform.db stations |
| Todos | Action items + todos for this project | hub.db todos |
| Goals | Goal tree for this project | platform.db goals (NEW) |
| Costs | Cost breakdown for this project | hub.db api_costs |
| People | People associated with this project | brain.json people |
| Settings | Jira key, Confluence space, budget, classification rules | config |

**Tab persistence:** localStorage key `coco:project-tab:${projectId}` (same pattern as Paperclip)

**API scoping:** Every backend endpoint that currently returns global data gets an optional `?project_id=` filter parameter.

### Backend Changes Required

```python
# Pattern for all list endpoints
@router.get("/api/content")
async def list_content(
    project_id: str | None = None,  # ← ADD THIS
    source: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = "SELECT ... FROM content WHERE 1=1"
    if project_id:
        query += " AND project_id = ?"
```

Endpoints needing `project_id` filter:
- GET /api/content
- GET /api/todos
- GET /api/drafts
- GET /api/costs
- GET /api/activity
- GET /api/stations
- GET /api/tasks (before removal — merge into todos)

### Frontend Context

```tsx
// ProjectContext.tsx (modeled on Paperclip's CompanyContext)
const STORAGE_KEY = "coco.selectedProjectId";

const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
  () => localStorage.getItem(STORAGE_KEY)
);

// All useQuery hooks use this:
const { data } = useQuery({
  queryKey: ["content", selectedProjectId, filters],
  queryFn: () => api.content.list({ projectId: selectedProjectId, ...filters }),
});
```

---

## 4. Inbox Page (NEW — Replaces Decisions)

### Paperclip's Inbox
- Tabs: Mine → Recent → Unread → All
- Item types: Issues, Approvals, Failed Runs, Join Requests, Alerts
- Actions: Mark read (fadeout), Archive (swipe), Approve/Reject inline
- Animation: 3-state dismiss (visible → fading → hidden)

### Our Inbox

**Tabs:** Urgent → Drafts → Classify → Health → All

**Item types (polymorphic, like Paperclip):**

| Type | Source | Actions |
|------|--------|---------|
| Urgent email/item | brain.json high-priority people match | [reply] [defer] [dismiss] |
| Draft approval | hub.db drafts (pending) | [approve] [reject] [show] |
| Unsorted content | hub.db content (unsorted) | [pick project] [dismiss] |
| Health alert | KH health check (red adapters) | [fix] [skip] |
| Overdue action item | hub.db action_items (past due) | [act now] [defer] [dismiss] |

**Replaces:** Current DecisionsPage + separate decision queue flow

**Progressive disclosure pattern:**
- Row shows: type icon + title + project + time ago
- Expand shows: full content + available actions
- Batch mode: select multiple + batch approve/classify

**Animation:** Same dismiss pattern as Paperclip (translate-x + scale + opacity transition)

---

## 5. Goal Hierarchy (NEW)

### Paperclip's Pattern
- `goals` table with `parentId` self-reference
- GoalTree component with recursive expand/collapse
- Goals link to projects and issues
- GoalDetail page with Sub-Goals and Projects tabs

### Our Adaptation

**New table in platform.db:**
```sql
CREATE TABLE goals (
    id TEXT PRIMARY KEY,           -- ULID
    project_id TEXT NOT NULL,      -- FK to hub.db projects
    parent_id TEXT,                -- self-reference for hierarchy
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',  -- active, achieved, dropped
    progress_pct INTEGER DEFAULT 0,
    owner TEXT,                    -- person name
    target_date TEXT,              -- ISO date
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Link to todos:** Add `goal_id` column to hub.db todos table.

**GoalTree component** (inspired by Paperclip):
```tsx
function GoalNode({ goal, allGoals, depth = 0 }) {
  const [expanded, setExpanded] = useState(true);
  const children = allGoals.filter(g => g.parentId === goal.id);
  const linkedTodos = useTodos({ goalId: goal.id });

  return (
    <div style={{ paddingLeft: depth * 24 }}>
      <div className="flex items-center gap-2">
        {children.length > 0 && (
          <ChevronRight
            className={cn("transition-transform", expanded && "rotate-90")}
            onClick={() => setExpanded(!expanded)}
          />
        )}
        <span>{goal.title}</span>
        <ProgressBar value={goal.progressPct} />
      </div>
      {expanded && children.map(child => (
        <GoalNode key={child.id} goal={child} allGoals={allGoals} depth={depth + 1} />
      ))}
      {expanded && linkedTodos.map(todo => (
        <TodoRow key={todo.id} todo={todo} indent />
      ))}
    </div>
  );
}
```

**API endpoints:**
- GET /api/goals?project_id=X — list goals for project
- POST /api/goals — create goal
- PATCH /api/goals/:id — update goal
- DELETE /api/goals/:id — delete goal

---

## 6. Dashboard Simplification

### Current: 9+ sections, all equally prominent
### Proposed: 3-zone layout with clear hierarchy

**Zone 1: Alert Banner (conditional)**
Only shows if something needs immediate attention. Like Paperclip's budget incident banner.
```
⚠️ 3 items need attention: 2 overdue, 1 health alert → Go to Inbox
```

**Zone 2: Metric Cards (4-card grid, like Paperclip)**
```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Projects │ │ Inbox    │ │ Todos    │ │ Monthly  │
│    10    │ │    5     │ │  7 open  │ │  $12.40  │
│  active  │ │ pending  │ │ 2 overdue│ │  of $30  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```
Each card links to its page. Inbox card turns red if urgent items exist.

**Zone 3: Two-column layout**
- Left (2/3): Project cards grid (top 6, sorted by recent activity)
- Right (1/3): Source health bar + recent activity feed (scrollable, max-height 384px)

**Removed from dashboard:**
- Cost chart (moved to /costs page)
- Station status bar (moved to /stations page)
- Queue badge (now in sidebar Inbox badge)

---

## 7. Station Card Simplification

### Current: 6 fields + 4 action buttons per card
### Proposed: Progressive disclosure (Paperclip pattern)

**Collapsed (default):**
```
┌─────────────────────────────────────┐
│ 🟢 PM Station          opus-4      │
│    Running: Weekly brief    $0.82/d │
│                              [···]  │
└─────────────────────────────────────┘
```
3 fields visible: name+status, current task, daily cost. One action menu (three-dot).

**Action menu (three-dot dropdown):**
- View Logs
- Pause / Resume
- Kill
- Edit Config

**Expanded (click to open detail panel):**
Right-side panel (like Paperclip's PropertiesPanel) slides in with:
- Full config (model, role, project, system prompt)
- Log viewer (real-time, searchable)
- Cost breakdown
- Run history

---

## 8. Dark Theme Implementation

### Paperclip's Approach (steal exactly)

**1. Inline script in index.html (prevents white flash):**
```html
<script>
(() => {
  const key = "coco.theme";
  const darkColor = "#18181b";
  const lightColor = "#ffffff";
  try {
    const stored = localStorage.getItem(key);
    const theme = stored === "light" || stored === "dark" ? stored : "dark";
    const isDark = theme === "dark";
    document.documentElement.classList.toggle("dark", isDark);
    document.documentElement.style.colorScheme = isDark ? "dark" : "light";
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", isDark ? darkColor : lightColor);
  } catch {
    document.documentElement.classList.add("dark");
    document.documentElement.style.colorScheme = "dark";
  }
})();
</script>
```

**2. OKLCH color system in index.css:**
```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --border: oklch(0.922 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  /* ... */
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --primary: oklch(0.985 0 0);
  --muted-foreground: oklch(0.708 0 0);
  --border: oklch(0.269 0 0);
  --destructive: oklch(0.637 0.237 25.331);
  /* ... */
}
```

**3. HTML starts dark:**
```html
<html lang="en" class="dark">
```

**4. ThemeContext for runtime switching:**
```tsx
// Reads from document class on mount
// setTheme updates class + localStorage + meta tag
```

---

## 9. Settings Simplification

### Current: 4 tabs, ~15 knobs, Autonomy tab has trust matrix
### Proposed: 2 tabs with progressive disclosure

**Tab 1: General**
- Theme toggle (Dark / Light)
- Project defaults (default project for new items)
- Notification preferences

**Tab 2: Advanced**
- Autonomy mode: 3 large cards (Careful / Normal / YOLO) with description
  - "Careful: Ask before every action"
  - "Normal: Auto-handle routine, ask for mutations"
  - "YOLO: Auto-handle everything, ask before sending"
- Expandable "Fine-tune" section (collapsed by default):
  - Auto-approve threshold slider
  - Safety caps
- Brain viewer (read-only, collapsed by default)
- Adapter health

---

## 10. EntityRow Pattern (Reusable List Item)

Steal Paperclip's EntityRow for ALL list views:

```tsx
interface EntityRowProps {
  leading?: ReactNode;        // Status icon, avatar
  identifier?: string;        // "AB-123", monospace
  title: string;              // Main text
  subtitle?: string;          // Secondary, muted
  trailing?: ReactNode;       // Badge, timestamp, actions
  to?: string;                // Click navigation
  onClick?: () => void;
}
```

**Use across:**
- Inbox items (type icon + title + project badge + time ago)
- Todo list (checkbox + title + priority badge + due date)
- Knowledge items (source icon + title + project + date)
- Station list (status dot + name + task + cost)
- Goal tree nodes (expand arrow + title + progress bar)
- Activity feed (action icon + description + timestamp)

---

## 11. Execution Phases

### Phase R1: Dark Theme + Design System (1 day)
- OKLCH color system in index.css
- Inline theme script in index.html
- ThemeContext provider
- Update all components to use semantic color tokens
- Custom scrollbar styling

### Phase R2: Sidebar Restructure + ProjectSwitcher (1.5 days)
- SidebarSection component for grouping
- ProjectSwitcher component (dropdown at top)
- ProjectContext provider (selectedProjectId in context + localStorage)
- Reduce sidebar items from 12 to 8 in 4 groups
- Inbox badge with count + danger tone

### Phase R3: Project Detail Page (2 days)
- New route: /projects/:id with sub-tab navigation
- Tabs: Overview, Knowledge, Stations, Todos, Goals, Costs, People, Settings
- All data queries scoped by project_id
- Tab persistence in localStorage
- Backend: add project_id filter to all list endpoints

### Phase R4: Inbox Page (2 days)
- Replace DecisionsPage with unified Inbox
- Polymorphic item types (urgent, draft, classify, health, overdue)
- Tabs: Urgent / Drafts / Classify / Health / All
- Inline actions (approve/reject/classify)
- Dismiss animation (Paperclip's translate + scale + opacity)
- Batch action mode

### Phase R5: Goal Hierarchy (2 days)
- New goals table in platform.db
- CRUD API endpoints
- GoalTree component (recursive expand/collapse)
- GoalDetail page with linked todos
- Add goal_id to todos table

### Phase R6: Dashboard + Station Simplification (1.5 days)
- Dashboard: alert banner + 4 metric cards + 2-column layout
- Station cards: 3 visible fields + action menu dropdown
- Station detail: right-side panel (not full page)
- Remove duplicate sections from dashboard

### Phase R7: Settings + Cleanup (1 day)
- Simplify to 2 tabs (General + Advanced)
- Autonomy mode as 3 large cards
- Collapsible "Fine-tune" section
- Merge Tasks into Todos
- Remove dead routes
- EntityRow component for all list views

### Phase R8: Onboarding + Polish (1 day)
- 3-screen onboarding on first visit
- Empty states for all pages
- Loading skeletons (Paperclip's Skeleton component)
- Keyboard shortcuts documentation (Cmd+?)
- Final design review

**Total: ~12 days**

---

## 12. What We're NOT Doing

- **Not forking Paperclip** — our data model is fundamentally different
- **Not adding plugins** — premature for a solo PM tool
- **Not adding multi-user auth** — still single-user, PIN-only
- **Not building agent adapters** — stations are Claude CLI only
- **Not adding company import/export** — no need for template marketplace
- **Not rewriting the backend** — 62 tests passing, all wiring done

---

## 13. Files to Study from Paperclip Reference

When implementing, open these as reference:

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
| Settings cards | `ui/src/pages/DesignGuide.tsx` (component patterns) |
| Theme context | `ui/src/context/ThemeContext.tsx` |
| Design system | `ui/src/index.css` (@theme inline block, OKLCH values) |
