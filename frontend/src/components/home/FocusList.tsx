import { useState } from 'react';
import { cn } from '../../lib/utils';
import { CheckCircle2 } from 'lucide-react';
import type { Todo, HomeProject } from '../../types/home';

export interface FocusListProps {
  todos: Todo[];
  projects: HomeProject[];
  onMarkDone: (id: string) => void;
}

const INITIAL_VISIBLE = 8;

function isOverdue(dueDate: string | null): boolean {
  if (!dueDate) return false;
  const parsed = new Date(dueDate);
  if (isNaN(parsed.getTime())) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return parsed < today;
}

function formatDueDate(dueDate: string | null): { text: string; className: string } {
  if (!dueDate) return { text: '--', className: 'text-muted-foreground' };
  const parsed = new Date(dueDate);
  if (isNaN(parsed.getTime())) return { text: '--', className: 'text-muted-foreground' };

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.round((parsed.getTime() - today.getTime()) / 86400000);

  if (diffDays < 0) return { text: `${Math.abs(diffDays)}d overdue`, className: 'text-destructive font-medium' };
  if (diffDays === 0) return { text: 'due today', className: 'text-warning' };
  if (diffDays === 1) return { text: 'due tomorrow', className: 'text-muted-foreground' };
  if (diffDays <= 7) {
    const day = parsed.toLocaleDateString('en-US', { weekday: 'short' });
    return { text: `due ${day}`, className: 'text-muted-foreground' };
  }
  return { text: parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), className: 'text-muted-foreground' };
}

export function FocusList({ todos, projects, onMarkDone }: FocusListProps) {
  const [expanded, setExpanded] = useState(false);
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  const nameMap = new Map<string, string>();
  for (const p of projects) nameMap.set(p.id, p.name);

  const activeTodos = todos.filter((t) => !completedIds.has(t.id));
  const visibleTodos = expanded ? activeTodos : activeTodos.slice(0, INITIAL_VISIBLE);
  const remaining = activeTodos.length - INITIAL_VISIBLE;

  function handleDone(id: string) {
    setCompletedIds((prev) => new Set(prev).add(id));
    onMarkDone(id);
    setTimeout(() => {
      setCompletedIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }, 1000);
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Today's Focus
        </span>
        {activeTodos.length > 0 && (
          <span className="text-[11px] font-medium text-muted-foreground bg-muted/40 rounded-full px-2 py-0.5">
            {activeTodos.length} items
          </span>
        )}
      </div>

      {/* Empty state */}
      {activeTodos.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          All clear — no priority items today.
        </div>
      ) : (
        <>
          {/* Todo rows */}
          <div>
            {visibleTodos.map((todo) => {
              const overdue = isOverdue(todo.due_date);
              const isHigh = todo.priority === 'high';
              const due = formatDueDate(todo.due_date);
              const projectName = todo.project_id ? nameMap.get(todo.project_id) : null;

              return (
                <div
                  key={todo.id}
                  className="group flex items-center gap-3 px-6 py-3 border-b border-border/30 hover:bg-accent/5 transition-colors"
                >
                  {/* Priority dot */}
                  <span
                    className={cn(
                      'h-2 w-2 rounded-full shrink-0',
                      overdue && isHigh && 'bg-destructive animate-pulse',
                      !overdue && isHigh && 'bg-destructive',
                      !isHigh && 'bg-muted-foreground/40',
                    )}
                  />

                  {/* Title */}
                  <span
                    className={cn(
                      'flex-1 min-w-0 truncate text-sm',
                      isHigh ? 'font-medium text-foreground' : 'text-muted-foreground',
                    )}
                    title={todo.title}
                  >
                    {todo.title}
                  </span>

                  {/* Project tag */}
                  {projectName && (
                    <span className="text-[11px] font-medium text-muted-foreground bg-muted/40 rounded px-1.5 py-0.5 shrink-0 max-w-[140px] truncate">
                      {projectName}
                    </span>
                  )}

                  {/* Due date */}
                  <span className={cn('text-[11px] min-w-[70px] text-right shrink-0', due.className)}>
                    {due.text}
                  </span>

                  {/* Mark done (hover-revealed) */}
                  <button
                    type="button"
                    onClick={() => handleDone(todo.id)}
                    className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity shrink-0 text-muted-foreground hover:text-success"
                    title="Mark as done"
                    aria-label="Mark as done"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Show more */}
          {!expanded && remaining > 0 && (
            <div className="border-t border-border/30 text-center">
              <button
                onClick={() => setExpanded(true)}
                className="w-full px-6 py-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Show {remaining} more...
              </button>
            </div>
          )}
          {expanded && remaining > 0 && (
            <div className="border-t border-border/30 text-center">
              <button
                onClick={() => setExpanded(false)}
                className="w-full px-6 py-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Show less
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
