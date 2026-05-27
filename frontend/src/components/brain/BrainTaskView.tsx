import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, ListTodo, ChevronDown, ChevronRight, Clock, User } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';
import type { BrainTask } from '../../types/brain';
import { ErrorState } from '../shared/ErrorState';

interface BrainTaskViewProps {
  search?: string;
}

interface TasksResponse {
  items: BrainTask[];
  total: number;
  by_status: Record<string, number>;
}

const LIMIT = 20;

// ---------------------------------------------------------------------------
// Status config
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; dot: string }> = {
  open: { label: 'Open', color: 'text-blue-400', bg: 'bg-blue-500/15', dot: 'bg-blue-400' },
  in_progress: { label: 'In Progress', color: 'text-amber-400', bg: 'bg-amber-500/15', dot: 'bg-amber-400' },
  done: { label: 'Done', color: 'text-green-400', bg: 'bg-green-500/15', dot: 'bg-green-400' },
  blocked: { label: 'Blocked', color: 'text-red-400', bg: 'bg-red-500/15', dot: 'bg-red-400' },
  waiting: { label: 'Waiting', color: 'text-purple-400', bg: 'bg-purple-500/15', dot: 'bg-purple-400' },
};

function getStatusConfig(status: string) {
  return STATUS_CONFIG[status] ?? { label: status, color: 'text-muted-foreground', bg: 'bg-muted/20', dot: 'bg-muted-foreground' };
}

// ---------------------------------------------------------------------------
// Priority config
// ---------------------------------------------------------------------------

const PRIORITY_DOTS: Record<number, string> = {
  1: 'bg-red-400',
  2: 'bg-orange-400',
  3: 'bg-yellow-400',
  4: 'bg-green-400',
  5: 'bg-gray-400',
};

function priorityDotColor(p: number): string {
  return PRIORITY_DOTS[p] ?? 'bg-gray-400';
}

// ---------------------------------------------------------------------------
// Date formatting
// ---------------------------------------------------------------------------

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T') + 'Z');
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '';
  const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T') + 'Z');
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BrainTaskView({ search }: BrainTaskViewProps) {
  const [statusFilter, setStatusFilter] = useState('');
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const params = new URLSearchParams();
  if (statusFilter) params.set('status', statusFilter);
  params.set('limit', String(LIMIT));
  params.set('offset', String(offset));

  const { data, isLoading, isError, error, refetch } = useQuery<TasksResponse>({
    queryKey: ['brain-tasks', statusFilter, offset, search],
    queryFn: () => apiFetch<TasksResponse>(`/brain/tasks?${params.toString()}`),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const byStatus = data?.by_status ?? {};
  const page = Math.floor(offset / LIMIT) + 1;
  const totalPages = Math.ceil(total / LIMIT);

  // Ordered status keys for the bar
  const statusOrder = ['open', 'in_progress', 'done', 'blocked', 'waiting'];
  const allStatuses = useMemo(() => {
    const known = new Set(statusOrder);
    const extra = Object.keys(byStatus).filter((s) => !known.has(s));
    return [...statusOrder, ...extra];
  }, [byStatus]);

  return (
    <div className="flex flex-col h-full">
      {/* Status pills bar */}
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            aria-pressed={statusFilter === ''}
            onClick={() => {
              setStatusFilter('');
              setOffset(0);
            }}
            className={cn(
              'px-2 py-0.5 rounded-full text-[11px] font-medium transition-colors',
              statusFilter === ''
                ? 'bg-accent/15 text-accent'
                : 'bg-transparent text-muted-foreground/60 hover:text-muted-foreground',
            )}
          >
            All ({Object.values(byStatus).reduce((a, b) => a + b, 0)})
          </button>
          {allStatuses.map((status) => {
            const count = byStatus[status] ?? 0;
            if (count === 0) return null;
            const cfg = getStatusConfig(status);
            const active = statusFilter === status;
            return (
              <button
                key={status}
                aria-pressed={active}
                onClick={() => {
                  setStatusFilter(active ? '' : status);
                  setOffset(0);
                }}
                className={cn(
                  'px-2 py-0.5 rounded-full text-[11px] font-medium transition-colors',
                  active ? cfg.bg + ' ' + cfg.color : 'bg-transparent text-muted-foreground/60 hover:text-muted-foreground',
                )}
              >
                {cfg.label} ({count})
              </button>
            );
          })}
        </div>
        <div className="mt-1.5 text-xs text-muted-foreground">
          {total.toLocaleString()} task{total !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Task list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-20 text-muted-foreground text-sm gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading tasks...
          </div>
        ) : isError ? (
          <div className="p-6">
            <ErrorState
              error={error}
              title="Couldn't load tasks"
              onRetry={() => void refetch()}
            />
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-3">
            <ListTodo className="h-8 w-8" />
            <p>No tasks found</p>
            <p className="text-xs">
              {statusFilter ? 'Try clearing the status filter.' : 'The brain has not recorded any tasks yet.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {items.map((task) => {
              const expanded = expandedId === task.id;
              const statusCfg = getStatusConfig(task.status);
              return (
                <div key={task.id}>
                  {/* Task row */}
                  <button
                    onClick={() => setExpandedId(expanded ? null : task.id)}
                    className="w-full text-left px-4 py-3 hover:bg-accent/5 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {/* Expand chevron */}
                      {expanded ? (
                        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      )}

                      {/* Priority dot */}
                      <div
                        className={cn('h-2.5 w-2.5 rounded-full shrink-0', priorityDotColor(task.priority))}
                        title={`Priority ${task.priority}`}
                      />

                      {/* Title */}
                      <span className="text-sm font-medium text-foreground flex-1 min-w-0 truncate">
                        {task.title}
                      </span>

                      {/* Status pill */}
                      <span
                        className={cn(
                          'px-2 py-0.5 rounded-full text-[11px] font-medium shrink-0',
                          statusCfg.bg,
                          statusCfg.color,
                        )}
                      >
                        {statusCfg.label}
                      </span>

                      {/* Owner */}
                      {task.owner_name && (
                        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                          <User className="h-3 w-3" />
                          {task.owner_name}
                        </span>
                      )}

                      {/* Due date */}
                      {task.due_date && (
                        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                          <Clock className="h-3 w-3" />
                          {formatDate(task.due_date)}
                        </span>
                      )}
                    </div>

                    {/* Notes preview (collapsed) */}
                    {!expanded && task.notes && (
                      <p className="text-xs text-muted-foreground mt-1 ml-[3.25rem] line-clamp-1">
                        {task.notes}
                      </p>
                    )}
                  </button>

                  {/* Expanded details */}
                  {expanded && (
                    <div className="px-4 pb-4 ml-[3.25rem] space-y-2">
                      {task.notes && (
                        <div>
                          <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">
                            Notes
                          </span>
                          <p className="text-xs text-foreground mt-0.5 whitespace-pre-wrap">
                            {task.notes}
                          </p>
                        </div>
                      )}
                      <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
                        {task.created_at && (
                          <span>Created: {formatDateTime(task.created_at)}</span>
                        )}
                        {task.completed_at && (
                          <span>Completed: {formatDateTime(task.completed_at)}</span>
                        )}
                        {task.blocked_by_task_id && (
                          <span className="text-red-400">
                            Blocked by task #{task.blocked_by_task_id}
                          </span>
                        )}
                        <span>Priority: {task.priority}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > LIMIT && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm text-muted-foreground">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
                offset === 0 ? 'opacity-40 cursor-not-allowed' : 'hover:bg-accent/50 text-foreground',
              )}
            >
              Previous
            </button>
            <button
              disabled={offset + LIMIT >= total}
              onClick={() => setOffset(offset + LIMIT)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
                offset + LIMIT >= total
                  ? 'opacity-40 cursor-not-allowed'
                  : 'hover:bg-accent/50 text-foreground',
              )}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
