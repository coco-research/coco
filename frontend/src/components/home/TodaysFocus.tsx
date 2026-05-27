import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiPatch } from '../../lib/api';
import { cn } from '../../lib/utils';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  ChevronDown,
  Target,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Todo {
  id: string;
  title: string;
  project_id: string | null;
  owner: string | null;
  due_date: string | null;
  priority: string;
  status: string;
  source_type: string | null;
  jira_key: string | null;
  tags: string | null;
}

interface Project {
  id: string;
  name: string;
  todo_open: number;
}

export interface TodaysFocusProps {
  highPriority: Todo[];
  mediumPriority: Todo[];
  projects: Project[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MAX_VISIBLE = 5;
const UNASSIGNED_KEY = '__unassigned__';

function isOverdue(dueDate: string | null): boolean {
  if (!dueDate) return false;
  const parsed = new Date(dueDate);
  if (isNaN(parsed.getTime())) return false;  // malformed date
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return parsed < today;
}

interface ProjectGroup {
  projectId: string;
  projectName: string;
  highCount: number;
  todos: Todo[];
}

function buildProjectGroups(
  highPriority: Todo[],
  mediumPriority: Todo[],
  projects: Project[],
): ProjectGroup[] {
  const nameMap = new Map<string, string>();
  for (const p of projects) {
    nameMap.set(p.id, p.name);
  }

  // Combine all todos — high first so they sort to top within each group
  const all = [...highPriority, ...mediumPriority];

  // Group by project_id
  const grouped = new Map<string, Todo[]>();
  for (const todo of all) {
    const key = todo.project_id ?? UNASSIGNED_KEY;
    const list = grouped.get(key) ?? [];
    list.push(todo);
    grouped.set(key, list);
  }

  const groups: ProjectGroup[] = [];
  for (const [key, todos] of grouped) {
    const highCount = todos.filter((t) => t.priority === 'high').length;
    groups.push({
      projectId: key,
      projectName:
        key === UNASSIGNED_KEY
          ? 'Unassigned'
          : (nameMap.get(key) ?? 'Unknown Project'),
      highCount,
      todos,
    });
  }

  // Sort: most high-priority items first
  groups.sort((a, b) => b.highCount - a.highCount);
  return groups;
}

/** Distribute groups round-robin across N columns. */
function distributeColumns(groups: ProjectGroup[], cols: number): ProjectGroup[][] {
  const columns: ProjectGroup[][] = Array.from({ length: cols }, () => []);
  groups.forEach((g, i) => {
    columns[i % cols].push(g);
  });
  return columns;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TodoRow({
  todo,
  onMarkDone,
  isPending,
  justCompleted,
}: {
  todo: Todo;
  onMarkDone: (id: string) => void;
  isPending: boolean;
  justCompleted: boolean;
}) {
  const overdue = isOverdue(todo.due_date);
  const isHigh = todo.priority === 'high';

  return (
    <div
      className={cn(
        'group flex items-center gap-2 rounded-lg px-2 py-1.5 transition-all',
        'hover:bg-muted/50',
        justCompleted && 'scale-95 opacity-0 duration-300',
      )}
    >
      {/* Priority indicator */}
      <span
        className={cn(
          'h-2 w-2 flex-shrink-0 rounded-full',
          isHigh ? 'bg-red-500' : 'bg-muted-foreground/40',
        )}
      />

      {/* Title */}
      <span
        className={cn(
          'min-w-0 flex-1 truncate text-sm',
          isHigh ? 'font-semibold text-foreground' : 'text-muted-foreground',
        )}
        title={todo.title}
      >
        {todo.title}
      </span>

      {/* Overdue badge — always visible */}
      {overdue && (
        <span className="flex-shrink-0 text-amber-500" title="Overdue">
          <AlertTriangle className="h-3.5 w-3.5" />
        </span>
      )}

      {/* Hover actions */}
      <span className="flex flex-shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        {todo.due_date && !overdue && (
          <span className="text-muted-foreground" title={`Due: ${todo.due_date}`}>
            <Clock className="h-3.5 w-3.5" />
          </span>
        )}
        <button
          type="button"
          disabled={isPending}
          onClick={() => onMarkDone(todo.id)}
          className={cn(
            'rounded p-0.5 text-muted-foreground transition-colors hover:text-green-500',
            isPending && 'cursor-wait opacity-50',
          )}
          title="Mark as done"
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
        </button>
      </span>
    </div>
  );
}

function ProjectGroupCard({
  group,
  onMarkDone,
  pendingIds,
  completedIds,
}: {
  group: ProjectGroup;
  onMarkDone: (id: string) => void;
  pendingIds: Set<string>;
  completedIds: Set<string>;
}) {
  const activeTodos = group.todos.filter((t) => !completedIds.has(t.id));
  const visibleTodos = activeTodos.slice(0, MAX_VISIBLE);
  const remaining = activeTodos.length - MAX_VISIBLE;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      {/* Project header */}
      <div className="mb-2 flex items-center justify-between">
        <h3 className="truncate text-sm font-semibold text-foreground">
          {group.projectName}
        </h3>
        {group.highCount > 0 && (
          <span className="ml-2 flex-shrink-0 rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400">
            {group.highCount} high
          </span>
        )}
      </div>

      {/* Todo rows */}
      <div className="space-y-0.5">
        {visibleTodos.map((todo) => (
          <TodoRow
            key={todo.id}
            todo={todo}
            onMarkDone={onMarkDone}
            isPending={pendingIds.has(todo.id)}
            justCompleted={completedIds.has(todo.id)}
          />
        ))}
      </div>

      {/* Overflow link */}
      {remaining > 0 && (
        <Link
          to={
            group.projectId === UNASSIGNED_KEY
              ? '/todos'
              : `/todos?project=${group.projectId}`
          }
          className="mt-2 flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <ChevronDown className="h-3 w-3" />
          +{remaining} more
        </Link>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function TodaysFocus({ highPriority, mediumPriority, projects }: TodaysFocusProps) {
  const queryClient = useQueryClient();
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  const markDone = useMutation({
    mutationFn: (id: string) => apiPatch(`/todos/${id}`, { status: 'done' }),
    onMutate: (id) => {
      setPendingIds((prev) => new Set(prev).add(id));
    },
    onSuccess: (_data, id) => {
      setPendingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      setCompletedIds((prev) => new Set(prev).add(id));
      // Brief animation delay, then invalidate to refresh data
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['home'] });
        // Clear this ID after data refreshes
        setTimeout(() => {
          setCompletedIds((prev) => {
            const next = new Set(prev);
            next.delete(id);
            return next;
          });
        }, 500);
      }, 350);
    },
    onError: (_err, id) => {
      setPendingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    },
  });

  const handleMarkDone = (id: string) => {
    markDone.mutate(id);
  };

  const totalCount = highPriority.length + mediumPriority.length;
  const groups = buildProjectGroups(highPriority, mediumPriority, projects);

  // Empty state
  if (totalCount === 0) {
    return (
      <section>
        <div className="mb-4 flex items-center gap-2">
          <Target className="h-5 w-5 text-foreground" />
          <h2 className="text-lg font-semibold text-foreground">Today's Focus</h2>
        </div>
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            All clear -- no priority items today.
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Add todos with the + button or let CoCo sync from Knowledge Hub.
          </p>
        </div>
      </section>
    );
  }

  // Distribute groups round-robin across 3 column buckets.
  // CSS grid handles responsive column count; each bucket is a column div
  // so project groups stay vertically stacked within their column.
  const columns = distributeColumns(groups, 3);

  return (
    <section>
      {/* Section header */}
      <div className="mb-4 flex items-center gap-2">
        <Target className="h-5 w-5 text-foreground" />
        <h2 className="text-lg font-semibold text-foreground">Today's Focus</h2>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {totalCount}
        </span>
      </div>

      {/* 3-column responsive grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {columns.map((col, colIdx) => (
          <div key={colIdx} className="flex flex-col gap-4">
            {col.map((group) => (
              <ProjectGroupCard
                key={group.projectId}
                group={group}
                onMarkDone={handleMarkDone}
                pendingIds={pendingIds}
                completedIds={completedIds}
              />
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
