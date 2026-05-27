import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Lock, ArrowRight, Plus, X, Search } from 'lucide-react';
import * as Popover from '@radix-ui/react-popover';
import { apiFetch, apiPost, apiDelete, ApiError } from '../../lib/api';
import { cn } from '../../lib/utils';
import { useToast } from '../shared/Toast';
import type { Todo } from './TodoList';

interface TodoDetail extends Todo {
  blocked_by?: string[];
  blocks?: string[];
}

interface TodoDependenciesProps {
  todoId: string;
  /** Used to render titles for related ids without an extra fetch each. */
  allTodos: Todo[];
}

/**
 * GAP M9 — Dependencies panel for a single todo.
 * Displays:
 *  - Blocked by (incoming edges): blockers that must complete first.
 *  - Blocks (outgoing edges): todos waiting on this one.
 * Supports adding a new blocker and removing existing edges.
 */
export function TodoDependencies({ todoId, allTodos }: TodoDependenciesProps) {
  const qc = useQueryClient();
  const { toast } = useToast();
  const [pickerOpen, setPickerOpen] = useState(false);
  const [search, setSearch] = useState('');

  const titleById = useMemo(() => {
    const map = new Map<string, Todo>();
    for (const t of allTodos) map.set(t.id, t);
    return map;
  }, [allTodos]);

  const { data: detail, isLoading } = useQuery<TodoDetail>({
    queryKey: ['todo-detail', todoId],
    queryFn: () => apiFetch<TodoDetail>(`/todos/${todoId}`),
  });

  const blockedBy = detail?.blocked_by ?? [];
  const blocks = detail?.blocks ?? [];

  function invalidate() {
    void qc.invalidateQueries({ queryKey: ['todo-detail', todoId] });
    void qc.invalidateQueries({ queryKey: ['todos'] });
  }

  async function addBlocker(blockerId: string) {
    try {
      await apiPost(`/todos/${todoId}/blocked_by`, { blocker_id: blockerId });
      setPickerOpen(false);
      setSearch('');
      invalidate();
      toast('Blocker added', 'success');
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : String(e);
      toast(msg || 'Failed to add blocker', 'error');
    }
  }

  async function removeBlocker(blockerId: string) {
    try {
      await apiDelete(`/todos/${todoId}/blocked_by/${blockerId}`);
      invalidate();
      toast('Blocker removed', 'success');
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : String(e);
      toast(msg || 'Failed to remove blocker', 'error');
    }
  }

  // Available todos = everything not self, not already a blocker.
  const blockedBySet = new Set(blockedBy);
  const candidates = useMemo(() => {
    const q = search.toLowerCase().trim();
    return allTodos
      .filter((t) => t.id !== todoId && !blockedBySet.has(t.id))
      .filter((t) => (q ? t.title.toLowerCase().includes(q) : true))
      .slice(0, 25);
  }, [allTodos, todoId, blockedBySet, search]);

  if (isLoading) {
    return (
      <div className="text-xs text-muted-foreground py-2">Loading dependencies…</div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Blocked by */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            <Lock className="h-3 w-3" />
            Blocked By ({blockedBy.length})
          </div>
          <Popover.Root open={pickerOpen} onOpenChange={setPickerOpen}>
            <Popover.Trigger asChild>
              <button
                className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
                title="Add blocker"
              >
                <Plus className="h-3 w-3" /> Add blocker
              </button>
            </Popover.Trigger>
            <Popover.Portal>
              <Popover.Content
                align="end"
                sideOffset={6}
                className="w-72 bg-card border border-border rounded-lg shadow-lg z-50 p-2"
              >
                <div className="relative mb-2">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                  <input
                    type="text"
                    autoFocus
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search todos…"
                    className="w-full pl-7 pr-2 py-1.5 text-xs bg-background border border-border rounded focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
                <div className="max-h-60 overflow-y-auto">
                  {candidates.length === 0 ? (
                    <div className="text-[11px] text-muted-foreground py-3 text-center">
                      No matching todos
                    </div>
                  ) : (
                    candidates.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => void addBlocker(t.id)}
                        className="w-full flex items-center gap-2 px-2 py-1.5 text-left rounded hover:bg-accent/50"
                      >
                        <span
                          className={cn(
                            'h-1.5 w-1.5 rounded-full shrink-0',
                            t.status === 'done' ? 'bg-green-500' :
                            t.status === 'in_progress' ? 'bg-amber-500' :
                            'bg-zinc-400',
                          )}
                        />
                        <span className="flex-1 text-xs truncate">{t.title}</span>
                        <span className="text-[10px] text-muted-foreground capitalize">
                          {t.status}
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </Popover.Content>
            </Popover.Portal>
          </Popover.Root>
        </div>
        {blockedBy.length === 0 ? (
          <div className="text-[11px] text-muted-foreground italic">No blockers.</div>
        ) : (
          <div className="space-y-1">
            {blockedBy.map((bid) => {
              const blocker = titleById.get(bid);
              const isDone = blocker?.status === 'done';
              return (
                <div
                  key={bid}
                  className="flex items-center gap-2 px-2 py-1 rounded bg-muted/30 border border-border"
                >
                  <span
                    className={cn(
                      'h-1.5 w-1.5 rounded-full shrink-0',
                      isDone ? 'bg-green-500' : 'bg-red-400',
                    )}
                  />
                  <span className={cn('flex-1 text-xs truncate', isDone && 'line-through text-muted-foreground')}>
                    {blocker?.title ?? bid}
                  </span>
                  <span className="text-[10px] text-muted-foreground capitalize">
                    {blocker?.status ?? 'unknown'}
                  </span>
                  <button
                    onClick={() => void removeBlocker(bid)}
                    className="p-0.5 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground"
                    title="Remove blocker"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Blocks */}
      <div>
        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">
          <ArrowRight className="h-3 w-3" />
          Blocks ({blocks.length})
        </div>
        {blocks.length === 0 ? (
          <div className="text-[11px] text-muted-foreground italic">
            Nothing depends on this todo.
          </div>
        ) : (
          <div className="space-y-1">
            {blocks.map((bid) => {
              const dependent = titleById.get(bid);
              return (
                <div
                  key={bid}
                  className="flex items-center gap-2 px-2 py-1 rounded bg-muted/30 border border-border"
                >
                  <span className="h-1.5 w-1.5 rounded-full shrink-0 bg-blue-400" />
                  <span className="flex-1 text-xs truncate">
                    {dependent?.title ?? bid}
                  </span>
                  <span className="text-[10px] text-muted-foreground capitalize">
                    {dependent?.status ?? 'unknown'}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
