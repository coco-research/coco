import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowUpDown, FileQuestion } from 'lucide-react';
import { apiFetch, apiTransition } from '../../lib/api.ts';
import { cn, timeAgo } from '../../lib/utils.ts';
import { InlineEditor } from '../shared/InlineEditor';
import { TransitionButtons } from '../shared/TransitionButtons';
import { statePillClass, STATE_LABELS, TASK_STATES } from '../../lib/state-machine';
import { apiPatch } from '../../lib/api.ts';

export interface Task {
  id: string;
  title: string;
  description: string | null;
  agent_id: string | null;
  project_id: string | null;
  status: string;
  priority: string;
  checked_out_by: string | null;
  checked_out_at: string | null;
  created_at: string;
  updated_at: string;
}

interface Agent {
  id: string;
  name: string;
}

interface Project {
  id: string;
  name: string;
}

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  onSelect: (task: Task) => void;
  selectedId: string | null;
}

const PRIORITY_STYLES: Record<string, string> = {
  high: 'bg-destructive/20 text-destructive',
  medium: 'bg-warning/20 text-warning',
  low: 'bg-accent/50 text-muted-foreground',
};

type SortKey = 'title' | 'status' | 'priority' | 'created_at';
type SortDir = 'asc' | 'desc';

const PRIORITY_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2 };

export function TaskList({ tasks, isLoading, onSelect, selectedId }: TaskListProps) {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [projectFilter, setProjectFilter] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('created_at');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [flashId, setFlashId] = useState<string | null>(null);

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => apiFetch<Agent[]>('/agents'),
  });

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiFetch<Project[]>('/projects'),
  });

  const agentMap = useMemo(() => {
    const m = new Map<string, string>();
    agents?.forEach((s) => m.set(s.id, s.name));
    return m;
  }, [agents]);

  const projectMap = useMemo(() => {
    const m = new Map<string, string>();
    projects?.forEach((p) => m.set(p.id, p.name));
    return m;
  }, [projects]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  async function handleTransition(id: string, toState: string) {
    setPendingId(id);
    try {
      await apiTransition(`/tasks/${id}`, toState);
      setFlashId(id);
      setTimeout(() => setFlashId(null), 600);
      void qc.invalidateQueries({ queryKey: ['tasks'] });
    } finally {
      setPendingId(null);
    }
  }

  const filtered = useMemo(() => {
    let result = tasks;
    if (statusFilter) result = result.filter((t) => t.status === statusFilter);
    if (priorityFilter) result = result.filter((t) => t.priority === priorityFilter);
    if (projectFilter) result = result.filter((t) => t.project_id === projectFilter);
    return result;
  }, [tasks, statusFilter, priorityFilter, projectFilter]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'title':
          cmp = a.title.localeCompare(b.title);
          break;
        case 'status':
          cmp = a.status.localeCompare(b.status);
          break;
        case 'priority':
          cmp = (PRIORITY_ORDER[a.priority] ?? 1) - (PRIORITY_ORDER[b.priority] ?? 1);
          break;
        case 'created_at':
          cmp = a.created_at.localeCompare(b.created_at);
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground text-sm">
        Loading tasks...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Filter row */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
        >
          <option value="">All Statuses</option>
          {TASK_STATES.map((s) => (
            <option key={s} value={s}>
              {STATE_LABELS[s] ?? s}
            </option>
          ))}
          {/* Legacy */}
          <option value="open">Open (legacy)</option>
          <option value="checked_out">Checked Out (legacy)</option>
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
        >
          <option value="">All Priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
        >
          <option value="">All Projects</option>
          {projects?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {/* Table header */}
      <div className="grid grid-cols-[5.5rem_4.5rem_1fr_8rem_8rem_5rem_10rem] gap-3 px-4 py-2 text-xs font-medium text-muted-foreground border-b border-border uppercase tracking-wide">
        <SortHeader label="Status" sortKey="status" current={sortKey} dir={sortDir} onToggle={toggleSort} />
        <SortHeader label="Priority" sortKey="priority" current={sortKey} dir={sortDir} onToggle={toggleSort} />
        <SortHeader label="Title" sortKey="title" current={sortKey} dir={sortDir} onToggle={toggleSort} />
        <span>Project</span>
        <span>Agent</span>
        <SortHeader label="Date" sortKey="created_at" current={sortKey} dir={sortDir} onToggle={toggleSort} />
        <span>Actions</span>
      </div>

      {/* Rows */}
      <div className="flex-1 overflow-y-auto">
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-2">
            <FileQuestion className="h-8 w-8" />
            No tasks match the current filters
          </div>
        ) : (
          sorted.map((task) => (
            <button
              key={task.id}
              onClick={() => onSelect(task)}
              className={cn(
                'w-full grid grid-cols-[5.5rem_4.5rem_1fr_8rem_8rem_5rem_10rem] gap-3 px-4 py-3 text-left text-sm',
                'border-b border-border/50 transition-colors',
                'hover:bg-accent/50',
                selectedId === task.id && 'bg-accent/50',
                flashId === task.id && 'animate-state-flash',
              )}
            >
              <span>
                <span
                  className={cn(
                    'inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                    statePillClass(task.status),
                  )}
                >
                  {STATE_LABELS[task.status] ?? task.status.replace('_', ' ')}
                </span>
              </span>
              <span>
                <span
                  className={cn(
                    'inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                    PRIORITY_STYLES[task.priority] ?? 'bg-accent/50 text-muted-foreground',
                  )}
                >
                  {task.priority}
                </span>
              </span>
              <div className="truncate" onClick={(e) => e.stopPropagation()}>
                <InlineEditor
                  value={task.title}
                  onSave={async (newValue) => {
                    await apiPatch(`/tasks/${task.id}`, { title: newValue });
                    void qc.invalidateQueries({ queryKey: ['tasks'] });
                  }}
                  as="span"
                  className="text-foreground"
                />
              </div>
              <span className="truncate text-muted-foreground text-xs">
                {task.project_id ? (projectMap.get(task.project_id) ?? '--') : '--'}
              </span>
              <span className="truncate text-muted-foreground text-xs">
                {task.agent_id ? (agentMap.get(task.agent_id) ?? '--') : '--'}
              </span>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {timeAgo(task.created_at)}
              </span>
              <div onClick={(e) => e.stopPropagation()}>
                <TransitionButtons
                  currentState={task.status}
                  kind="task"
                  onTransition={(toState) => void handleTransition(task.id, toState)}
                  isPending={pendingId === task.id}
                  size="sm"
                />
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

function SortHeader({
  label,
  sortKey,
  current,
  dir,
  onToggle,
}: {
  label: string;
  sortKey: SortKey;
  current: SortKey;
  dir: SortDir;
  onToggle: (key: SortKey) => void;
}) {
  const active = current === sortKey;
  return (
    <button
      onClick={() => onToggle(sortKey)}
      className={cn(
        'flex items-center gap-1 hover:text-foreground transition-colors',
        active && 'text-foreground',
      )}
    >
      {label}
      <ArrowUpDown className={cn('h-3 w-3', active ? 'opacity-100' : 'opacity-40')} />
      {active && <span className="text-[10px]">{dir === 'asc' ? '\u2191' : '\u2193'}</span>}
    </button>
  );
}
