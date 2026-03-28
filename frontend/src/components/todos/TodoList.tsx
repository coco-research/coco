import { useState } from 'react';
import { Clock } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { apiTransition } from '../../lib/api';
import { cn } from '../../lib/utils';
import { InlineEditor } from '../shared/InlineEditor';
import { TransitionButtons } from '../shared/TransitionButtons';
import { statePillClass, STATE_LABELS } from '../../lib/state-machine';
import { apiPatch } from '../../lib/api';

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
}

interface TodoListProps {
  todos: Todo[];
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

export function TodoList({ todos }: TodoListProps) {
  const qc = useQueryClient();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [flashId, setFlashId] = useState<string | null>(null);

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
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:shadow-sm transition-all',
                    (isDone || isArchived) && 'opacity-50',
                    flashId === todo.id && 'animate-state-flash',
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

                  {/* Title */}
                  <div
                    className="flex-1 min-w-0"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <InlineEditor
                      value={todo.title}
                      onSave={async (newValue) => {
                        await apiPatch(`/todos/${todo.id}`, { title: newValue });
                        void qc.invalidateQueries({ queryKey: ['todos'] });
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
    </div>
  );
}
