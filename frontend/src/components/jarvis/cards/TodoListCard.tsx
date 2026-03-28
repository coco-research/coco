import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { cn } from '../../../lib/utils';
import { apiPatch } from '../../../lib/api';
import type { TodoListData, TodoItem } from '../../../types/cards';

interface TodoListCardProps {
  data: TodoListData;
  variant?: 'jarvis' | 'light';
}

const PRIORITY_CLASSES: Record<string, string> = {
  high: 'bg-[#FF453A]/15 text-[#FF453A] border-[#FF453A]/20',
  medium: 'bg-[#FF9F0A]/15 text-[#FF9F0A] border-[#FF9F0A]/20',
  low: 'bg-white/10 text-white/40 border-white/10',
};

const PRIORITY_CLASSES_LIGHT: Record<string, string> = {
  high: 'bg-red-100 text-red-700 border-red-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  low: 'bg-slate-100 text-slate-600 border-slate-200',
};

function isPastDue(dateStr: string | null): boolean {
  if (!dateStr) return false;
  return new Date(dateStr) < new Date();
}

export function TodoListCard({ data, variant = 'jarvis' }: TodoListCardProps) {
  const qc = useQueryClient();
  const [doneIds, setDoneIds] = useState<Set<string>>(new Set());
  const isJarvis = variant === 'jarvis';
  const priorityMap = isJarvis ? PRIORITY_CLASSES : PRIORITY_CLASSES_LIGHT;

  const markDone = async (todo: TodoItem) => {
    setDoneIds((prev) => new Set(prev).add(todo.id));
    try {
      await apiPatch(`/todos/${todo.id}`, { status: 'done' });
      qc.invalidateQueries({ queryKey: ['todos'] });
      qc.invalidateQueries({ queryKey: ['home'] });
    } catch {
      setDoneIds((prev) => {
        const next = new Set(prev);
        next.delete(todo.id);
        return next;
      });
    }
  };

  return (
    <div className="space-y-1">
      {data.title && (
        <h3
          className={cn(
            'text-sm font-semibold mb-3 tracking-wide uppercase',
            isJarvis ? 'text-[#0A84FF]' : 'text-foreground',
          )}
        >
          {data.title}
        </h3>
      )}
      <ul className="space-y-1">
        {data.todos.map((todo) => {
          const done = todo.status === 'done' || doneIds.has(todo.id);
          return (
            <li
              key={todo.id}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg transition-all',
                isJarvis
                  ? 'hover:bg-white/5'
                  : 'hover:bg-muted/50',
                done && 'opacity-50',
              )}
            >
              <button
                type="button"
                onClick={() => !done && markDone(todo)}
                className={cn(
                  'flex-shrink-0 w-4 h-4 rounded border transition-colors',
                  done
                    ? isJarvis
                      ? 'bg-[#34C759] border-[#34C759]'
                      : 'bg-primary border-primary'
                    : isJarvis
                      ? 'border-white/20 hover:border-[#34C759]'
                      : 'border-border hover:border-primary',
                )}
                aria-label={`Mark "${todo.title}" done`}
              >
                {done && (
                  <svg viewBox="0 0 16 16" className="w-4 h-4 text-white">
                    <path
                      d="M5 8l2 2 4-4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </button>

              <span
                className={cn(
                  'flex-1 text-sm truncate',
                  done && 'line-through',
                  isJarvis ? 'text-white/90' : 'text-foreground',
                )}
              >
                {todo.title}
              </span>

              <span
                className={cn(
                  'text-[10px] px-1.5 py-0.5 rounded border font-medium',
                  priorityMap[todo.priority] ?? priorityMap.low,
                )}
              >
                {todo.priority}
              </span>

              {todo.due_date && (
                <span
                  className={cn(
                    'text-[10px] font-mono',
                    isPastDue(todo.due_date)
                      ? 'text-[#FF453A]'
                      : isJarvis
                        ? 'text-white/40'
                        : 'text-muted-foreground',
                  )}
                >
                  {new Date(todo.due_date).toLocaleDateString()}
                </span>
              )}

              {todo.project_name && (
                <span
                  className={cn(
                    'text-[10px] truncate max-w-[80px]',
                    isJarvis ? 'text-white/30' : 'text-muted-foreground',
                  )}
                >
                  {todo.project_name}
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
