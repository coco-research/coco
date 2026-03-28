import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useScope } from '../context/ScopeContext';
import { useEffect, useState, useCallback } from 'react';
import {
  FolderKanban, Search, Radio, CheckSquare, Target, DollarSign, Users, Settings,
  Mail, Mic, Ticket, FileText, Plus, ChevronRight, Check, ChevronDown, X,
  GitBranch, Play, SkipForward, ChevronUp, Pencil, Download, Save,
} from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { cn, timeAgo, formatCost } from '../lib/utils';
import { apiFetch, apiPost, apiPatch } from '../lib/api';

// Existing component imports
import { ContentList } from '../components/knowledge/ContentList';
import { ContentDetail } from '../components/knowledge/ContentDetail';
import type { ContentItem } from '../components/knowledge/ContentList';
import { AgentCard, ROLE_META, type Agent } from '../components/agents/AgentCard';
import { InlineEditor } from '../components/shared/InlineEditor';
import { CreateAgentDialog } from '../components/agents/CreateAgentDialog';
import { AgentDetail } from '../components/agents/AgentDetail';
import { RecruitAgentDialog } from '../components/agents/RecruitAgentDialog';
import { TodoList } from '../components/todos/TodoList';
import { AddTodoDialog } from '../components/todos/AddTodoDialog';
import type { Todo } from '../components/todos/TodoList';
import { SpendChart } from '../components/costs/SpendChart';
import { ModelBreakdown } from '../components/costs/ModelBreakdown';
import { BudgetBar } from '../components/costs/BudgetBar';
import { CostEventsTable } from '../components/costs/CostEventsTable';
import { PersonCard, type Person } from '../components/people/PersonCard';
import { PersonDetail } from '../components/people/PersonDetail';
import { ActivityFeed } from '../components/dashboard/ActivityFeed';

const TABS = [
  { key: 'overview', label: 'Overview', icon: FolderKanban },
  { key: 'knowledge', label: 'Knowledge', icon: Search },
  { key: 'agents', label: 'Agents', icon: Radio },
  { key: 'collaboration', label: 'Collaboration', icon: GitBranch },
  { key: 'todos', label: 'Todos', icon: CheckSquare },
  { key: 'goals', label: 'Goals', icon: Target },
  { key: 'costs', label: 'Costs', icon: DollarSign },
  { key: 'people', label: 'People', icon: Users },
  { key: 'settings', label: 'Settings', icon: Settings },
] as const;

type TabKey = (typeof TABS)[number]['key'];

// ─── Shared small components ─────────────────────────────────────────

function SourceStat({ icon: Icon, label, count }: { icon: React.ElementType; label: string; count: number }) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 bg-card rounded-lg border border-border">
      <Icon size={16} className="text-muted-foreground" />
      <div>
        <p className="text-lg font-semibold text-foreground tabular-nums">{count}</p>
        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
      </div>
    </div>
  );
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
      <div
        className={cn(
          'h-full rounded-full transition-all',
          value >= 100 ? 'bg-success' : value >= 50 ? 'bg-info' : 'bg-warning'
        )}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

const SOURCE_OPTIONS = [
  { value: '', label: 'All Sources' },
  { value: 'email', label: 'Email' },
  { value: 'voice', label: 'Voice' },
  { value: 'jira', label: 'Jira' },
  { value: 'confluence', label: 'Confluence' },
];

const selectCls = 'bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

// ─── Overview Tab ────────────────────────────────────────────────────

function OverviewTab({ project, projectId }: { project: Record<string, unknown>; projectId: string }) {
  const { data: activityData } = useQuery({
    queryKey: ['activity', projectId],
    queryFn: async () => {
      const res = await fetch(`/api/activity?limit=10`);
      if (!res.ok) return [];
      return res.json();
    },
  });

  const events = (activityData ?? []).map((e: Record<string, string>) => ({
    ts: e.created_at ? timeAgo(e.created_at) : '',
    description: `${e.action ?? 'activity'}: ${e.item_type ?? ''} ${e.item_id ?? ''}`.trim(),
    project: e.project_id,
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <SourceStat icon={Mail} label="Emails" count={(project.email as number) ?? 0} />
        <SourceStat icon={Mic} label="Voice" count={(project.voice as number) ?? 0} />
        <SourceStat icon={Ticket} label="Jira" count={(project.jira as number) ?? 0} />
        <SourceStat icon={FileText} label="Confluence" count={(project.confluence as number) ?? 0} />
      </div>

      <ActivityFeed events={events} />
    </div>
  );
}

// ─── Knowledge Tab ───────────────────────────────────────────────────

interface ContentResponse {
  items: ContentItem[];
  total: number;
}

function KnowledgeTab({ projectId }: { projectId: string }) {
  const [source, setSource] = useState('');
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState<ContentItem | null>(null);

  const params = new URLSearchParams();
  params.set('project_id', projectId);
  if (source) params.set('source', source);
  if (q) params.set('q', q);
  params.set('limit', '50');

  const { data, isLoading } = useQuery({
    queryKey: ['content', projectId, source, q],
    queryFn: () => apiFetch<ContentResponse>(`/content?${params.toString()}`),
  });

  return (
    <div className="space-y-4">
      {/* Inline filter bar (no URL params pollution) */}
      <div className="flex items-center gap-3 flex-wrap">
        <select value={source} onChange={e => setSource(e.target.value)} className={selectCls}>
          {SOURCE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search content..."
            value={q}
            onChange={e => setQ(e.target.value)}
            className="w-full bg-card border border-border rounded-lg pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
          />
        </div>
        <span className="text-xs text-muted-foreground">{data?.total ?? 0} items</span>
      </div>

      <ContentList
        items={data?.items ?? []}
        total={data?.total ?? 0}
        isLoading={isLoading}
        selectedId={selected?.id ?? null}
        onSelect={setSelected}
      />

      {selected && (
        <ContentDetail item={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

// ─── Agents Tab ─────────────────────────────────────────────────────

function AgentsTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [recruitOpen, setRecruitOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { tree } = useScope();

  // Find the tree node_id that matches this hub project ID
  const nodeId = (() => {
    if (!tree) return null;
    const find = (n: typeof tree): string | null => {
      if (n.hub_project_id === projectId) return n.id;
      for (const c of n.children ?? []) {
        const r = find(c);
        if (r) return r;
      }
      return null;
    };
    return find(tree);
  })();

  // Query agents by both project_id (legacy) and node_id (tree-based)
  const { data: agents = [], isLoading } = useQuery<Agent[]>({
    queryKey: ['agents', projectId, nodeId],
    queryFn: async () => {
      const byProject = await apiFetch<Agent[]>(`/agents?project_id=${projectId}`);
      if (nodeId) {
        const byNode = await apiFetch<Agent[]>(`/agents?node_id=${nodeId}&subtree=true`);
        // Merge and dedupe
        const ids = new Set(byProject.map(a => a.id));
        for (const a of byNode) {
          if (!ids.has(a.id)) byProject.push(a);
        }
      }
      return byProject;
    },
    refetchInterval: (query) => {
      const data = query.state.data ?? [];
      return data.some((a: Agent) => a.status === 'running' || a.status === 'paused') ? 3000 : 30000;
    },
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['agents'] });

  const handleAction = async (agentId: string, action: string) => {
    try {
      await apiPost(`/agents/${agentId}/${action}`, {});
      invalidate();
    } catch { /* ignore */ }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{agents.length} agent{agents.length !== 1 ? 's' : ''}</span>
        <button
          onClick={() => setRecruitOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
        >
          <Plus size={14} />
          Recruit Agent
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map(i => <div key={i} className="h-28 bg-muted/50 rounded-xl animate-pulse" />)}
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <Radio size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No agents yet</p>
          <p className="text-xs mt-1 mb-4">Recruit agents to build your team for this project.</p>
          <button
            onClick={() => setRecruitOpen(true)}
            className="mt-2 flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all"
          >
            <Plus size={14} />
            Recruit Agent
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onClick={() => setSelectedId(agent.id)}
              onSpawn={() => handleAction(agent.id, 'spawn')}
              onPause={() => handleAction(agent.id, 'pause')}
              onResume={() => handleAction(agent.id, 'resume')}
              onKill={() => handleAction(agent.id, 'kill')}
            />
          ))}
        </div>
      )}

      <RecruitAgentDialog
        open={recruitOpen}
        onOpenChange={setRecruitOpen}
        nodeId={nodeId ?? projectId}
        onRecruited={invalidate}
      />
      {selectedId && <AgentDetail agentId={selectedId} onClose={() => setSelectedId(null)} onAction={invalidate} />}
    </div>
  );
}

// ─── Todos Tab ───────────────────────────────────────────────────────

function TodosTab({ projectId }: { projectId: string }) {
  const queryParams = new URLSearchParams();
  queryParams.set('project_id', projectId);
  queryParams.set('status', 'open');
  queryParams.set('limit', '200');

  const { data, isLoading } = useQuery<Todo[]>({
    queryKey: ['todos', projectId],
    queryFn: async () => {
      const raw = await apiFetch<Todo[] | { items: Todo[]; total: number }>(`/todos?${queryParams.toString()}`);
      return Array.isArray(raw) ? raw : raw.items;
    },
    refetchInterval: 30000,
  });

  const todos = data ?? [];
  const openCount = todos.filter(t => t.status === 'open').length;
  const doneCount = todos.filter(t => t.status === 'done').length;

  const handleEdit = useCallback((todo: Todo) => {
    const newTitle = window.prompt('Edit title:', todo.title);
    if (newTitle && newTitle !== todo.title) {
      void apiPatch(`/todos/${todo.id}`, { title: newTitle });
    }
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>{openCount} open</span>
          <span className="text-border">|</span>
          <span>{doneCount} done</span>
        </div>
        <AddTodoDialog />
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => <div key={i} className="h-12 bg-muted/50 rounded-md animate-pulse" />)}
        </div>
      ) : todos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <CheckSquare size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No todos for this project</p>
          <p className="text-xs mt-1">Add a todo to start tracking work.</p>
        </div>
      ) : (
        <TodoList todos={todos} onEdit={handleEdit} />
      )}
    </div>
  );
}

// ─── Goals Tab ───────────────────────────────────────────────────────

interface Goal {
  id: string;
  project_id: string;
  parent_id: string | null;
  title: string;
  description: string | null;
  status: string;
  progress_pct: number;
  owner: string | null;
  target_date: string | null;
  created_at: string;
}

function GoalNode({ goal, allGoals, depth = 0 }: { goal: Goal; allGoals: Goal[]; depth?: number }) {
  const [expanded, setExpanded] = useState(true);
  const queryClient = useQueryClient();
  const children = allGoals.filter(g => g.parent_id === goal.id);
  const hasChildren = children.length > 0;

  return (
    <div>
      <div
        className="group flex items-center gap-2 px-3 py-2 hover:bg-accent/50 rounded-md cursor-pointer transition-colors"
        style={{ paddingLeft: `${depth * 24 + 12}px` }}
      >
        {hasChildren ? (
          <button onClick={e => { e.stopPropagation(); setExpanded(!expanded); }} className="shrink-0 p-0.5 rounded hover:bg-accent">
            <ChevronRight size={14} className={cn('transition-transform text-muted-foreground', expanded && 'rotate-90')} />
          </button>
        ) : (
          <div className="w-5 shrink-0" />
        )}
        {goal.status === 'achieved' ? (
          <Check size={14} className="text-success shrink-0" />
        ) : (
          <Target size={14} className="text-muted-foreground shrink-0" />
        )}
        <InlineEditor
          value={goal.title}
          onSave={async (title) => {
            await fetch(`/api/goals/${goal.id}`, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ title }),
            });
            void queryClient.invalidateQueries({ queryKey: ['goals'] });
          }}
          as="span"
          className={cn(
            'text-sm flex-1 truncate',
            goal.status === 'achieved' && 'line-through text-muted-foreground',
            goal.status === 'dropped' && 'line-through text-muted-foreground opacity-50'
          )}
        />
        <ProgressBar value={goal.progress_pct} />
        <span className="text-[10px] text-muted-foreground tabular-nums">{goal.progress_pct}%</span>
        {goal.owner && (
          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{goal.owner}</span>
        )}
      </div>
      {hasChildren && expanded && children.map(child => (
        <GoalNode key={child.id} goal={child} allGoals={allGoals} depth={depth + 1} />
      ))}
    </div>
  );
}

function GoalsTab({ projectId }: { projectId: string }) {
  const [showAdd, setShowAdd] = useState(false);
  const [title, setTitle] = useState('');
  const queryClient = useQueryClient();

  const { data: goals = [], isLoading } = useQuery<Goal[]>({
    queryKey: ['goals', projectId],
    queryFn: async () => {
      const res = await fetch(`/api/goals?project_id=${projectId}`);
      if (!res.ok) return [];
      return res.json();
    },
  });

  const createGoal = useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/goals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, project_id: projectId, status: 'active', progress_pct: 0 }),
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      setTitle('');
      setShowAdd(false);
    },
  });

  const rootGoals = goals.filter(g => !g.parent_id);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{goals.length} goal{goals.length !== 1 ? 's' : ''}</span>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
        >
          <Plus size={14} />
          New Goal
        </button>
      </div>

      {showAdd && (
        <div className="flex items-center gap-2 p-3 border border-border rounded-lg bg-card">
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && title.trim()) createGoal.mutate(); if (e.key === 'Escape') setShowAdd(false); }}
            placeholder="Goal title..."
            className="flex-1 text-sm bg-transparent outline-none placeholder:text-muted-foreground"
            autoFocus
          />
          <button
            onClick={() => { if (title.trim()) createGoal.mutate(); }}
            disabled={!title.trim() || createGoal.isPending}
            className="px-3 py-1 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50"
          >
            Add
          </button>
          <button onClick={() => setShowAdd(false)} className="px-2 py-1 text-xs text-muted-foreground hover:text-foreground">
            Cancel
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => <div key={i} className="h-10 bg-muted/50 rounded-md animate-pulse" />)}
        </div>
      ) : rootGoals.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <Target size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No goals yet</p>
          <p className="text-xs mt-1">Add a goal to start tracking progress.</p>
        </div>
      ) : (
        <div className="border border-border rounded-xl overflow-hidden divide-y divide-border">
          {rootGoals.map(goal => <GoalNode key={goal.id} goal={goal} allGoals={goals} />)}
        </div>
      )}
    </div>
  );
}

// ─── Costs Tab ───────────────────────────────────────────────────────

interface CostSummary {
  total_usd: number;
  daily_avg: number;
  by_model: Record<string, number>;
  by_project: Record<string, number>;
  daily?: { date: string; cost_usd: number }[];
}

interface Budget {
  project_id: string;
  monthly_cap_usd: number;
  alert_threshold_pct: number;
}

function CostsTab({ projectId }: { projectId: string }) {
  const { data: summary, isLoading } = useQuery<CostSummary>({
    queryKey: ['costs-summary', 30],
    queryFn: () => apiFetch<CostSummary>('/costs/summary?days=30'),
    refetchInterval: 60000,
  });

  const { data: budgets } = useQuery<Budget[]>({
    queryKey: ['budgets'],
    queryFn: () => apiFetch<Budget[]>('/budgets'),
  });

  if (isLoading || !summary) {
    return (
      <div className="space-y-4">
        <div className="h-20 bg-muted/50 rounded-xl animate-pulse" />
        <div className="h-48 bg-muted/50 rounded-xl animate-pulse" />
      </div>
    );
  }

  const projectCost = summary.by_project[projectId] ?? 0;
  const projectBudget = budgets?.find(b => b.project_id === projectId);

  return (
    <div className="space-y-4">
      {/* Project-specific cost card */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-muted-foreground mb-1">Project Spend (30d)</p>
          <p className="text-xl font-mono text-foreground">${projectCost.toFixed(2)}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-xs text-muted-foreground mb-1">Platform Total (30d)</p>
          <p className="text-xl font-mono text-foreground">${summary.total_usd.toFixed(2)}</p>
        </div>
      </div>

      {projectBudget && (
        <BudgetBar
          project_name={projectId}
          spent_usd={projectCost}
          cap_usd={projectBudget.monthly_cap_usd}
        />
      )}

      <SpendChart data={summary.daily ?? []} />

      <div className="grid grid-cols-2 gap-4">
        <ModelBreakdown data={summary.by_model} />
      </div>
    </div>
  );
}

// ─── People Tab ──────────────────────────────────────────────────────

function PeopleTab({ projectId, projectName }: { projectId: string; projectName: string }) {
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  const { data: peopleData, isLoading } = useQuery<Record<string, Person>>({
    queryKey: ['brain-people'],
    queryFn: () => apiFetch('/brain/people'),
  });

  // Filter people associated with this project (by name match)
  const allPeople = Object.entries(peopleData ?? {});
  const projectPeople = allPeople.filter(([, person]) =>
    person.projects.some(p =>
      p.toLowerCase() === projectName.toLowerCase() ||
      p.toLowerCase().includes(projectName.toLowerCase()) ||
      projectName.toLowerCase().includes(p.toLowerCase())
    )
  );

  const selectedPerson = selectedSlug ? peopleData?.[selectedSlug] : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {projectPeople.length} {projectPeople.length === 1 ? 'person' : 'people'} associated
        </span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3">
          {[1, 2].map(i => <div key={i} className="h-28 bg-muted/50 rounded-xl animate-pulse" />)}
        </div>
      ) : projectPeople.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <Users size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No people linked to this project</p>
          <p className="text-xs mt-1">People are auto-discovered from emails and meetings.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {projectPeople.map(([slug, person]) => (
            <PersonCard
              key={slug}
              slug={slug}
              person={person}
              isSelected={slug === selectedSlug}
              onSelect={setSelectedSlug}
            />
          ))}
        </div>
      )}

      {selectedPerson && selectedSlug && (
        <PersonDetail
          slug={selectedSlug}
          person={selectedPerson}
          onClose={() => setSelectedSlug(null)}
        />
      )}
    </div>
  );
}

// ─── Settings Tab ────────────────────────────────────────────────────

function ProjectSettingsTab({ project, projectId }: { project: Record<string, unknown>; projectId: string }) {
  const queryClient = useQueryClient();

  const { data: budgets } = useQuery<Budget[]>({
    queryKey: ['budgets'],
    queryFn: () => apiFetch<Budget[]>('/budgets'),
  });

  const currentBudget = budgets?.find(b => b.project_id === projectId);
  const [monthlyCap, setMonthlyCap] = useState('');
  const [dailyCap, setDailyCap] = useState('');
  const [weeklyCap, setWeeklyCap] = useState('');

  useEffect(() => {
    if (currentBudget) {
      setMonthlyCap(String(currentBudget.monthly_cap_usd ?? ''));
    }
  }, [currentBudget]);

  const saveBudget = useMutation({
    mutationFn: async () => {
      await apiPost('/budgets', {
        project_id: projectId,
        monthly_cap_usd: parseFloat(monthlyCap) || 0,
        daily_cap_usd: parseFloat(dailyCap) || null,
        weekly_cap_usd: parseFloat(weeklyCap) || null,
        alert_threshold_pct: 80,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
    },
  });

  return (
    <div className="space-y-6 max-w-xl">
      {/* Project Info */}
      <section>
        <h3 className="text-sm font-semibold text-foreground mb-3">Project Info</h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Name</label>
            <div className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground">
              {(project.name as string) ?? 'Unnamed'}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Total Items</label>
              <div className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground tabular-nums">
                {(project.total as number) ?? 0}
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Project ID</label>
              <div className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-muted-foreground font-mono text-xs truncate">
                {projectId}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Budget */}
      <section>
        <h3 className="text-sm font-semibold text-foreground mb-3">Budget Caps</h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Monthly Cap (USD)</label>
            <input
              type="number"
              step="0.01"
              value={monthlyCap}
              onChange={e => setMonthlyCap(e.target.value)}
              placeholder="e.g. 30.00"
              className={selectCls + ' w-full'}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Weekly Cap (USD)</label>
              <input
                type="number"
                step="0.01"
                value={weeklyCap}
                onChange={e => setWeeklyCap(e.target.value)}
                placeholder="Optional"
                className={selectCls + ' w-full'}
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Daily Cap (USD)</label>
              <input
                type="number"
                step="0.01"
                value={dailyCap}
                onChange={e => setDailyCap(e.target.value)}
                placeholder="Optional"
                className={selectCls + ' w-full'}
              />
            </div>
          </div>
          <button
            onClick={() => saveBudget.mutate()}
            disabled={saveBudget.isPending}
            className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {saveBudget.isPending ? 'Saving...' : 'Save Budget'}
          </button>
        </div>
      </section>

      {/* Integrations */}
      <section>
        <h3 className="text-sm font-semibold text-foreground mb-3">Integrations</h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Jira Key</label>
            <div className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-muted-foreground">
              {(project.jira_key as string) ?? 'Not configured'}
            </div>
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Confluence Space</label>
            <div className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-muted-foreground">
              {(project.confluence_space as string) ?? 'Not configured'}
            </div>
          </div>
        </div>
      </section>

      {/* Export as Template */}
      <ExportTemplateSection projectId={projectId} />
    </div>
  );
}

function ExportTemplateSection({ projectId }: { projectId: string }) {
  const [exporting, setExporting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDesc, setTemplateDesc] = useState('');
  const [saved, setSaved] = useState(false);

  const handleExportDownload = async () => {
    setExporting(true);
    try {
      const tpl = await apiFetch<Record<string, unknown>>(`/projects/${projectId}/export`);
      const blob = new Blob([JSON.stringify(tpl, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const name = (tpl.project as Record<string, string>)?.name ?? 'project';
      a.download = `${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.coco-template.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // ignore
    } finally {
      setExporting(false);
    }
  };

  const handleSaveToLibrary = async () => {
    if (!templateName.trim()) return;
    setSaving(true);
    setSaved(false);
    try {
      const tpl = await apiFetch<Record<string, unknown>>(`/projects/${projectId}/export`);
      await apiPost('/templates', {
        name: templateName.trim(),
        description: templateDesc.trim() || null,
        template: tpl,
      });
      setSaved(true);
      setTemplateName('');
      setTemplateDesc('');
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  return (
    <section>
      <h3 className="text-sm font-semibold text-foreground mb-3">Export as Template</h3>
      <p className="text-xs text-muted-foreground mb-3">
        Export this project's configuration (agents, goals, tasks, tree) as a reusable template.
      </p>

      <button
        onClick={handleExportDownload}
        disabled={exporting}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-secondary text-secondary-foreground rounded-md hover:bg-accent/30 transition-colors disabled:opacity-50 mb-4"
      >
        <Download size={14} />
        {exporting ? 'Exporting...' : 'Download as File'}
      </button>

      <div className="border border-border rounded-lg p-4 space-y-3">
        <p className="text-xs text-muted-foreground font-medium">Save to Template Library</p>
        <input
          type="text"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          placeholder="Template name"
          className={selectCls + ' w-full'}
        />
        <input
          type="text"
          value={templateDesc}
          onChange={(e) => setTemplateDesc(e.target.value)}
          placeholder="Description (optional)"
          className={selectCls + ' w-full'}
        />
        <div className="flex items-center gap-2">
          <button
            onClick={handleSaveToLibrary}
            disabled={saving || !templateName.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            <Save size={14} />
            {saving ? 'Saving...' : 'Save to Library'}
          </button>
          {saved && (
            <span className="text-xs text-green-500 font-medium">Saved!</span>
          )}
        </div>
      </div>
    </section>
  );
}

// ─── Collaboration Tab ──────────────────────────────────────────────

interface WorkflowStep {
  role: string;
  action: string;
  section: string;
}

interface ActiveWorkflow {
  id: string;
  template_name: string;
  objective: string;
  steps: WorkflowStep[];
  current_step: number;
  status: string;
  created_at: string;
}

interface Handoff {
  id: string;
  workflow_id: string;
  from_role: string;
  to_role: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  created_at: string;
}

interface ContextSection {
  id: string;
  node_id: string;
  section_name: string;
  author_role: string;
  content: string;
  created_at: string;
  updated_at: string;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
}

function WorkflowProgress({ steps, currentStep }: { steps: WorkflowStep[]; currentStep: number }) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto py-2">
      {steps.map((step, i) => {
        const roleMeta = ROLE_META[step.role] ?? ROLE_META['custom'];
        const isCompleted = i < currentStep;
        const isCurrent = i === currentStep;
        const Icon = roleMeta.icon;

        return (
          <div key={i} className="flex items-center gap-1 shrink-0">
            {i > 0 && (
              <div className={cn('w-6 h-px', isCompleted ? 'bg-success' : isCurrent ? 'bg-info' : 'bg-border')} />
            )}
            <div
              className={cn(
                'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs border',
                isCompleted && 'bg-success/10 border-success/30 text-success',
                isCurrent && 'bg-info/10 border-info/30 text-info ring-1 ring-info/20',
                !isCompleted && !isCurrent && 'bg-muted/50 border-border text-muted-foreground'
              )}
              title={step.action}
            >
              {isCompleted ? (
                <Check size={12} />
              ) : isCurrent ? (
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-info opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-info" />
                </span>
              ) : (
                <Icon size={12} />
              )}
              <span className="font-medium">{roleMeta.abbr}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PendingHandoffs({
  handoffs,
  onLaunch,
  onSkip,
}: {
  handoffs: Handoff[];
  onLaunch: (h: Handoff) => void;
  onSkip: (h: Handoff) => void;
}) {
  if (handoffs.length === 0) {
    return (
      <div className="py-6 text-center text-muted-foreground">
        <p className="text-sm">All handoffs complete. Your team is in sync.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {handoffs.map(h => {
        const toMeta = ROLE_META[h.to_role] ?? ROLE_META['custom'];
        const fromMeta = ROLE_META[h.from_role] ?? ROLE_META['custom'];
        const ToIcon = toMeta.icon;
        return (
          <div key={h.id} className="bg-card border border-border rounded-lg p-3 space-y-2">
            <div className="flex items-start gap-2">
              <div className={cn('mt-0.5 p-1 rounded', toMeta.color)}>
                <ToIcon size={14} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{h.title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  From: {fromMeta.label} · {timeAgo(h.created_at)}
                </p>
              </div>
              {h.status === 'in_progress' && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-info/10 text-info font-medium">Running</span>
              )}
            </div>
            {h.status === 'pending' && (
              <div className="flex items-center gap-2 pl-8">
                <button
                  onClick={() => onLaunch(h)}
                  className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
                >
                  <Play size={12} />
                  Launch Agent
                </button>
                <button
                  onClick={() => onSkip(h)}
                  className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-muted-foreground hover:text-foreground border border-border rounded-md hover:bg-accent/50 transition-colors"
                >
                  <SkipForward size={12} />
                  Skip
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function SharedContext({
  sections,
  nodeId,
  onEdited,
}: {
  sections: ContextSection[];
  nodeId: string;
  onEdited: () => void;
}) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const toggle = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const saveEdit = async (id: string) => {
    await apiPatch(`/context/${id}`, { content: editContent });
    setEditingId(null);
    onEdited();
  };

  if (sections.length === 0) {
    return (
      <div className="py-6 text-center text-muted-foreground">
        <p className="text-sm">No shared context yet. Start a workflow to get your team collaborating.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {sections.map(s => {
        const isExpanded = expandedIds.has(s.id);
        const isEditing = editingId === s.id;
        const roleMeta = ROLE_META[s.author_role] ?? ROLE_META['custom'];

        return (
          <div key={s.id} className="border border-border rounded-lg overflow-hidden">
            <button
              onClick={() => toggle(s.id)}
              className="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-accent/30 transition-colors"
            >
              <FileText size={14} className="text-muted-foreground shrink-0" />
              <span className="text-sm font-medium text-foreground flex-1 truncate">{s.section_name}</span>
              <span className={cn('text-[10px] px-1.5 py-0.5 rounded font-medium', roleMeta.color)}>
                {roleMeta.label}
              </span>
              <span className="text-[10px] text-muted-foreground">{timeAgo(s.updated_at || s.created_at)}</span>
              {isExpanded ? <ChevronUp size={14} className="text-muted-foreground" /> : <ChevronDown size={14} className="text-muted-foreground" />}
            </button>
            {isExpanded && (
              <div className="px-3 pb-3 border-t border-border">
                {isEditing ? (
                  <div className="space-y-2 pt-2">
                    <textarea
                      value={editContent}
                      onChange={e => setEditContent(e.target.value)}
                      rows={6}
                      className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors resize-y"
                    />
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => saveEdit(s.id)}
                        className="px-3 py-1 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1 text-xs text-muted-foreground hover:text-foreground"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="pt-2">
                    <p className="text-sm text-foreground whitespace-pre-wrap">{s.content}</p>
                    <button
                      onClick={() => { setEditingId(s.id); setEditContent(s.content); }}
                      className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <Pencil size={10} />
                      Edit
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function StartWorkflowDialog({
  open,
  onOpenChange,
  nodeId,
  onStarted,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  nodeId: string;
  onStarted: () => void;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [objective, setObjective] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const { data: templates = [], isLoading } = useQuery<WorkflowTemplate[]>({
    queryKey: ['workflow-templates'],
    queryFn: () => apiFetch('/workflow-templates'),
    enabled: open,
  });

  const reset = () => {
    setSelectedId(null);
    setObjective('');
    setError('');
    setSubmitting(false);
  };

  const handleStart = async () => {
    if (!selectedId || !objective.trim()) return;
    setSubmitting(true);
    setError('');
    try {
      await apiPost(`/nodes/${nodeId}/workflows`, {
        template_id: selectedId,
        objective: objective.trim(),
      });
      reset();
      onOpenChange(false);
      onStarted();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start workflow');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={(v) => { if (!v) reset(); onOpenChange(v); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-card border border-border rounded-2xl shadow-2xl z-50 p-6 animate-fade-in max-h-[85vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-base font-semibold text-foreground">Start Workflow</Dialog.Title>
            <Dialog.Close className="p-1 rounded hover:bg-accent transition-colors">
              <X size={16} className="text-muted-foreground" />
            </Dialog.Close>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2].map(i => <div key={i} className="h-20 bg-muted/50 rounded-lg animate-pulse" />)}
            </div>
          ) : templates.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No workflow templates available.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="text-xs text-muted-foreground block mb-2">Select Template</label>
                <div className="space-y-2">
                  {templates.map(t => (
                    <button
                      key={t.id}
                      onClick={() => setSelectedId(t.id)}
                      className={cn(
                        'w-full text-left p-3 rounded-lg border transition-colors',
                        selectedId === t.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-accent hover:bg-accent/10'
                      )}
                    >
                      <p className="text-sm font-medium text-foreground">{t.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{t.description}</p>
                      <p className="text-[10px] text-muted-foreground mt-1">{t.steps.length} steps</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-muted-foreground block mb-1">Objective</label>
                <input
                  type="text"
                  value={objective}
                  onChange={e => setObjective(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && selectedId && objective.trim()) handleStart(); }}
                  placeholder="What should this workflow accomplish?"
                  className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
                  autoFocus
                />
              </div>

              {error && <p className="text-xs text-destructive">{error}</p>}

              <button
                onClick={handleStart}
                disabled={!selectedId || !objective.trim() || submitting}
                className="w-full px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {submitting ? 'Starting...' : 'Start Workflow'}
              </button>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function HandoffHistory({ handoffs }: { handoffs: Handoff[] }) {
  const completed = handoffs.filter(h => h.status === 'completed' || h.status === 'skipped');

  if (completed.length === 0) return null;

  return (
    <div className="space-y-1">
      {completed.map(h => {
        const fromMeta = ROLE_META[h.from_role] ?? ROLE_META['custom'];
        const toMeta = ROLE_META[h.to_role] ?? ROLE_META['custom'];
        return (
          <div key={h.id} className="flex items-center gap-2 px-3 py-2 text-sm">
            {h.status === 'completed' ? (
              <Check size={14} className="text-success shrink-0" />
            ) : (
              <SkipForward size={14} className="text-muted-foreground shrink-0" />
            )}
            <span className="font-medium text-foreground">{fromMeta.abbr}</span>
            <ChevronRight size={12} className="text-muted-foreground" />
            <span className="font-medium text-foreground">{toMeta.abbr}</span>
            <span className="text-muted-foreground truncate flex-1">{h.title}</span>
            <span className="text-xs text-muted-foreground shrink-0">{timeAgo(h.created_at)}</span>
          </div>
        );
      })}
    </div>
  );
}

function CollaborationTab({ projectId, nodeId }: { projectId: string; nodeId: string | null }) {
  const queryClient = useQueryClient();
  const [workflowDialogOpen, setWorkflowDialogOpen] = useState(false);
  const effectiveNodeId = nodeId ?? projectId;

  // Active workflow
  const { data: activeWorkflow, isLoading: workflowLoading } = useQuery<ActiveWorkflow | null>({
    queryKey: ['workflow-active', effectiveNodeId],
    queryFn: async () => {
      try {
        return await apiFetch<ActiveWorkflow>(`/nodes/${effectiveNodeId}/workflows/active`);
      } catch {
        return null;
      }
    },
    refetchInterval: 10000,
  });

  // Context sections
  const { data: contextSections = [], isLoading: contextLoading } = useQuery<ContextSection[]>({
    queryKey: ['project-context', effectiveNodeId],
    queryFn: async () => {
      try {
        return await apiFetch<ContextSection[]>(`/nodes/${effectiveNodeId}/context`);
      } catch {
        return [];
      }
    },
  });

  // Pending handoffs
  const { data: pendingHandoffs = [] } = useQuery<Handoff[]>({
    queryKey: ['handoffs', effectiveNodeId, 'pending'],
    queryFn: async () => {
      try {
        return await apiFetch<Handoff[]>(`/nodes/${effectiveNodeId}/handoffs?status=pending`);
      } catch {
        return [];
      }
    },
    refetchInterval: 5000,
  });

  // All handoffs (for history)
  const { data: allHandoffs = [] } = useQuery<Handoff[]>({
    queryKey: ['handoffs-history', effectiveNodeId],
    queryFn: async () => {
      try {
        return await apiFetch<Handoff[]>(`/nodes/${effectiveNodeId}/handoffs`);
      } catch {
        return [];
      }
    },
  });

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['workflow-active', effectiveNodeId] });
    queryClient.invalidateQueries({ queryKey: ['project-context', effectiveNodeId] });
    queryClient.invalidateQueries({ queryKey: ['handoffs', effectiveNodeId] });
    queryClient.invalidateQueries({ queryKey: ['handoffs-history', effectiveNodeId] });
  };

  const handleLaunchAgent = async (handoff: Handoff) => {
    try {
      // Find agent with the target role in this project
      const agents = await apiFetch<Agent[]>(`/agents?node_id=${effectiveNodeId}&subtree=true`);
      const targetAgent = agents.find(a => a.role === handoff.to_role);
      if (targetAgent) {
        await apiPost(`/agents/${targetAgent.id}/spawn`, {});
      }
      // Mark handoff as in-progress
      await apiPatch(`/handoffs/${handoff.id}`, { status: 'in_progress' });
      invalidateAll();
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    } catch {
      // Silently fail — user can retry
    }
  };

  const handleSkipHandoff = async (handoff: Handoff) => {
    try {
      if (activeWorkflow) {
        await apiPost(`/workflows/${activeWorkflow.id}/advance`, { skip: true });
      }
      await apiPatch(`/handoffs/${handoff.id}`, { status: 'skipped' });
      invalidateAll();
    } catch {
      // Silently fail
    }
  };

  const isLoading = workflowLoading || contextLoading;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-16 bg-muted/50 rounded-xl animate-pulse" />
        <div className="h-32 bg-muted/50 rounded-xl animate-pulse" />
        <div className="h-48 bg-muted/50 rounded-xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {activeWorkflow ? `Workflow: ${activeWorkflow.status}` : 'No active workflow'}
        </span>
        <button
          onClick={() => setWorkflowDialogOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
        >
          <Plus size={14} />
          Start Workflow
        </button>
      </div>

      {/* Active Workflow */}
      <section>
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Active Workflow</h3>
        {activeWorkflow ? (
          <div className="bg-card border border-border rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-2">
              <GitBranch size={14} className="text-info" />
              <span className="text-sm font-medium text-foreground">{activeWorkflow.template_name}</span>
            </div>
            <p className="text-xs text-muted-foreground">{activeWorkflow.objective}</p>
            <WorkflowProgress steps={activeWorkflow.steps} currentStep={activeWorkflow.current_step} />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground border border-dashed border-border rounded-xl">
            <GitBranch size={32} className="mb-2 opacity-30" />
            <p className="text-sm font-medium">No active workflow</p>
            <p className="text-xs mt-1">Start one to coordinate your agent team.</p>
          </div>
        )}
      </section>

      {/* Pending Handoffs */}
      <section>
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Pending Handoffs</h3>
        <PendingHandoffs
          handoffs={pendingHandoffs}
          onLaunch={handleLaunchAgent}
          onSkip={handleSkipHandoff}
        />
      </section>

      {/* Shared Context */}
      <section>
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Shared Context</h3>
        <SharedContext
          sections={contextSections}
          nodeId={effectiveNodeId}
          onEdited={invalidateAll}
        />
      </section>

      {/* Handoff History */}
      {allHandoffs.some(h => h.status === 'completed' || h.status === 'skipped') && (
        <section>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Handoff History</h3>
          <div className="border border-border rounded-xl overflow-hidden divide-y divide-border">
            <HandoffHistory handoffs={allHandoffs} />
          </div>
        </section>
      )}

      {/* Start Workflow Dialog */}
      <StartWorkflowDialog
        open={workflowDialogOpen}
        onOpenChange={setWorkflowDialogOpen}
        nodeId={effectiveNodeId}
        onStarted={invalidateAll}
      />
    </div>
  );
}

// ─── Main Page Component ─────────────────────────────────────────────

export default function ProjectDetailPage() {
  const { projectId, tab } = useParams();
  const { tree, setSelectedNodeId } = useScope();
  const storageKey = `coco:project-tab:${projectId}`;
  const [activeTab, setActiveTab] = useState<TabKey>(() => {
    if (tab && TABS.some(t => t.key === tab)) return tab as TabKey;
    return (localStorage.getItem(storageKey) as TabKey) ?? 'overview';
  });

  // Find the tree node ID for this hub project
  const resolvedNodeId = (() => {
    if (!projectId || !tree) return null;
    const findNode = (n: typeof tree): string | null => {
      if (n.hub_project_id === projectId) return n.id;
      for (const c of n.children ?? []) {
        const r = findNode(c);
        if (r) return r;
      }
      return null;
    };
    return findNode(tree);
  })();

  // Set scope when node is found
  useEffect(() => {
    if (resolvedNodeId) setSelectedNodeId(resolvedNodeId);
  }, [resolvedNodeId, setSelectedNodeId]);

  useEffect(() => {
    localStorage.setItem(storageKey, activeTab);
  }, [activeTab, storageKey]);

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const res = await fetch(`/api/projects/${projectId}`);
      if (!res.ok) throw new Error('Project not found');
      return res.json();
    },
    enabled: !!projectId,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-muted/50 rounded animate-pulse" />
        <div className="h-64 bg-muted/50 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p className="text-sm font-medium">Project not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Project header */}
      <div>
        <InlineEditor
          value={project.name}
          onSave={async (name) => { await apiPatch(`/projects/${projectId}`, { name }); }}
          as="h2"
          className="text-lg font-semibold text-foreground"
        />
        <p className="text-xs text-muted-foreground mt-0.5">
          {project.total ?? 0} items total
        </p>
      </div>

      {/* Tab navigation */}
      <div className="flex items-center gap-0.5 border-b border-border overflow-x-auto">
        {TABS.map(({ key, label, icon: TabIcon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 text-sm whitespace-nowrap border-b-2 transition-colors',
              activeTab === key
                ? 'border-primary text-foreground font-medium'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <TabIcon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {activeTab === 'overview' && <OverviewTab project={project} projectId={projectId!} />}
        {activeTab === 'knowledge' && <KnowledgeTab projectId={projectId!} />}
        {activeTab === 'agents' && <AgentsTab projectId={projectId!} />}
        {activeTab === 'collaboration' && <CollaborationTab projectId={projectId!} nodeId={resolvedNodeId} />}
        {activeTab === 'todos' && <TodosTab projectId={projectId!} />}
        {activeTab === 'goals' && <GoalsTab projectId={projectId!} />}
        {activeTab === 'costs' && <CostsTab projectId={projectId!} />}
        {activeTab === 'people' && <PeopleTab projectId={projectId!} projectName={project.name} />}
        {activeTab === 'settings' && <ProjectSettingsTab project={project} projectId={projectId!} />}
      </div>
    </div>
  );
}
