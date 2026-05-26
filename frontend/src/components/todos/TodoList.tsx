import { useState } from 'react';
import { Clock, Lock, ArrowRight, Link2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { apiTransition } from '../../lib/api';
import { cn } from '../../lib/utils';
import { InlineEditor } from '../shared/InlineEditor';
import { TransitionButtons } from '../shared/TransitionButtons';
import { statePillClass, STATE_LABELS } from '../../lib/state-machine';
import { apiPatch } from '../../lib/api';
import { AddDependencyDialog } from './AddDependencyDialog';

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  owner: string | null;
  due_date: string | null;
  project_id: string | null;
  source_type: string | null;
  source_content_id: string | null;
  jira_key: string | null;
  created_at: string;
  completed_at: string | null;
  tags: string;
  blocked_by_count?: number;
  blocking_count?: number;
  display_id?: string;
}

interface TodoListProps {
  todos: Todo[];
  /** Optional edit callback. Currently consumed by ProjectDetailPage; not wired into the list UI yet. */
  onEdit?: (todo: Todo) => void;
  onSelect?: (todo: Todo) => void;
  selectedId?: string | null;
}

const priorityBadge: Record<string, string> = {
  high: 'bg-destructive/20 text-destructive',
  medium: 'bg-warning/20 text-warning',
  low: 'bg-accent/50 text-muted-foreground',
};

function isOverdue(dueDate: string | null): boolean {
  if (!dueDate) return false;
  return new Date(dueDate) < new Date(new Date().toDateString());
}

export function TodoList({ todos, onSelect, selectedId }: TodoListProps) {
  const qc = useQueryClient();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [flashId, setFlashId] = useState<string | null>(null);
  const [depDialogTodoId, setDepDialogTodoId] = useState<string | null>(null);

  async function handleTransition(id: string, toState: string) {
    setPendingId(id);
    try {
      await apiTransition(`/todos/${id}`, toState);
      setFlashId(id);
      setTimeout(() => setFlashId(null), 600);
      void qc.invalidateQueries({ queryKey: ['todos'] });
    } finally {
      setPendingId(null);
    }
  }

  // Group by project
  const grouped = new Map<string, Todo[]>();
  for (const todo of todos) {
    const key = todo.project_id ?? 'Unassigned';
    const list = grouped.get(key) ?? [];
    list.push(todo);
    grouped.set(key, list);
  }

  if (todos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <Clock size={48} className="mb-3 opacity-40" />
        <p className="text-lg font-medium">Nothing on your plate.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {[...grouped.entries()].map(([project, items]) => (
        <section key={project}>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              {project}
            </h3>
            <span className="text-xs text-muted-foreground bg-accent/50 rounded-full px-2 py-0.5">
              {items.length}
            </span>
          </div>

          <div className="space-y-1">
            {items.map((todo) => {
              const overdue = isOverdue(todo.due_date);
              const isDone = todo.status === 'done';
              const isArchived = todo.status === 'archived';

              return (
                <div
                  key={todo.id}
                  onClick={onSelect ? () => onSelect(todo) : undefined}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:shadow-sm transition-all',
                    (isDone || isArchived) && 'opacity-50',
                    flashId === todo.id && 'animate-state-flash',
                    onSelect && 'cursor-pointer',
                    selectedId === todo.id && 'ring-1 ring-accent/40 bg-accent/10',
                  )}
                >
                  {/* Status pill */}
                  <span
                    className={cn(
                      'inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize shrink-0',
                      statePillClass(todo.status),
                    )}
                  >
                    {STATE_LABELS[todo.status] ?? todo.status}
                  </span>

                  {/* Display ID badge */}
                  {todo.display_id && (
                    <span className="shrink-0 font-mono text-[11px] text-muted-foreground bg-muted/50 border border-border rounded px-1.5 py-0.5 tracking-wide">
                      {todo.display_id}
                    </span>
                  )}

                  {/* Title */}
                  <div
                    className="flex-1 min-w-0"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <InlineEditor
                      value={todo.title}
                      onSave={async (newValue) => {
                        // Optimistic update across all ['todos', ...] queries
                        const queries = qc.getQueriesData<Todo[] | { items: Todo[] }>({ queryKey: ['todos'] });
                        const snapshots = queries.map(([key, data]) => ({ key, data }));
                        queries.forEach(([key]) => {
                          qc.setQueryData(key, (old: Todo[] | { items: Todo[] } | undefined) => {
                            if (!old) return old;
                            if (Array.isArray(old)) {
                              return old.map((t) => (t.id === todo.id ? { ...t, title: newValue } : t));
                            }
                            return {
                              ...old,
                              items: old.items.map((t) => (t.id === todo.id ? { ...t, title: newValue } : t)),
                            };
                          });
                        });
                        try {
                          await apiPatch(`/todos/${todo.id}`, { title: newValue });
                        } catch (e) {
                          snapshots.forEach((s) => qc.setQueryData(s.key, s.data));
                          throw e;
                        } finally {
                          void qc.invalidateQueries({ queryKey: ['todos'] });
                        }
                      }}
                      as="span"
                      className={cn(
                        'text-sm truncate',
                        isDone && 'line-through text-muted-foreground',
                      )}
                    />
                  </div>

                  {/* Priority badge */}
                  <span
                    className={cn(
                      'text-xs px-2 py-0.5 rounded-full font-medium capitalize shrink-0',
                      priorityBadge[todo.priority] ?? priorityBadge.low,
                    )}
                  >
                    {todo.priority}
                  </span>

                  {/* Dependency badges */}
                  {(todo.blocked_by_count ?? 0) > 0 && (
                    <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-semibold shrink-0 bg-red-500/15 text-red-500">
                      <Lock className="h-3 w-3" />
                      Blocked by {todo.blocked_by_count}
                    </span>
                  )}
                  {(todo.blocking_count ?? 0) > 0 && (
                    <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-semibold shrink-0 bg-blue-500/15 text-blue-500">
                      <ArrowRight className="h-3 w-3" />
                      Blocking {todo.blocking_count}
                    </span>
                  )}

                  {/* Add dependency button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDepDialogTodoId(todo.id);
                    }}
                    className="shrink-0 p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors"
                    title="Add dependency"
                  >
                    <Link2 className="h-3.5 w-3.5" />
                  </button>

                  {/* Owner */}
                  {todo.owner && (
                    <span className="text-xs text-muted-foreground shrink-0">{todo.owner}</span>
                  )}

                  {/* Due date */}
                  {todo.due_date && (
                    <span
                      className={cn(
                        'flex items-center gap-1 text-xs shrink-0',
                        overdue ? 'text-destructive font-medium' : 'text-muted-foreground',
                      )}
                    >
                      {overdue && <span>&#9200;</span>}
                      {new Date(todo.due_date).toLocaleDateString()}
                    </span>
                  )}

                  {/* Transition buttons */}
                  <div className="shrink-0" onClick={(e) => e.stopPropagation()}>
                    <TransitionButtons
                      currentState={todo.status}
                      kind="todo"
                      onTransition={(toState) => void handleTransition(todo.id, toState)}
                      isPending={pendingId === todo.id}
                      size="sm"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}

      {/* Add Dependency Dialog */}
      {depDialogTodoId && (
        <AddDependencyDialog
          todoId={depDialogTodoId}
          allTodos={todos}
          open={!!depDialogTodoId}
          onOpenChange={(open) => { if (!open) setDepDialogTodoId(null); }}
          onCreated={() => void qc.invalidateQueries({ queryKey: ['todos'] })}
        />
      )}
    </div>
  );
}
