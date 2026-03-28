import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { LayoutList, LayoutGrid, Search } from 'lucide-react';
import { apiFetch, apiTransition } from '../lib/api';
import { cn } from '../lib/utils';
import { TODO_STATES } from '../lib/state-machine';
import { TodoList } from '../components/todos/TodoList';
import { AddTodoDialog } from '../components/todos/AddTodoDialog';
import { TodoFilters } from '../components/todos/TodoFilters';
import { DedupDialog } from '../components/todos/DedupDialog';
import { StatusBar } from '../components/shared/StatusBar';
import { BoardView } from '../components/shared/BoardView';
import type { TodoFilterState } from '../components/todos/TodoFilters';
import type { Todo } from '../components/todos/TodoList';

type TodosResponse = Todo[];

type ViewMode = 'list' | 'board';

function TodosSkeleton() {
  const pulse = 'animate-pulse rounded bg-muted/50';
  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <div className={`${pulse} h-8 w-32`} />
        <div className={`${pulse} h-8 w-32`} />
        <div className={`${pulse} h-8 w-32`} />
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className={`${pulse} h-14`} />
      ))}
    </div>
  );
}

export default function TodosPage() {
  const qc = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [boardPending, setBoardPending] = useState(false);
  const [dedupOpen, setDedupOpen] = useState(false);

  const [filters, setFilters] = useState<TodoFilterState>({
    status: '',
    project_id: '',
    priority: '',
  });

  const queryParams = new URLSearchParams();
  if (filters.status) queryParams.set('status', filters.status);
  if (filters.project_id) queryParams.set('project_id', filters.project_id);
  if (filters.priority) queryParams.set('priority', filters.priority);
  queryParams.set('limit', '200');

  const { data, isLoading } = useQuery<TodosResponse>({
    queryKey: ['todos', filters],
    queryFn: async () => {
      const raw = await apiFetch<Todo[] | { items: Todo[]; total: number }>(`/todos?${queryParams.toString()}`);
      return Array.isArray(raw) ? raw : raw.items;
    },
    refetchInterval: 30000,
  });

  const todos = data ?? [];

  // Status counts (across ALL todos, not just filtered)
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const t of todos) {
      counts[t.status] = (counts[t.status] ?? 0) + 1;
    }
    return counts;
  }, [todos]);

  // Handle status bar filter click
  function handleStatusBarFilter(state: string) {
    setFilters((f) => ({ ...f, status: state }));
  }

  // Board transition handler
  async function handleBoardTransition(id: string, toState: string) {
    setBoardPending(true);
    try {
      await apiTransition(`/todos/${id}`, toState);
      void qc.invalidateQueries({ queryKey: ['todos'] });
    } finally {
      setBoardPending(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Todos</h1>
          <span className="text-sm text-muted-foreground bg-card border border-border rounded-full px-2 py-0.5">
            {todos.length}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex items-center bg-card border border-border rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                'p-1.5 rounded-md transition-colors',
                viewMode === 'list'
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:text-foreground',
              )}
              title="List view"
            >
              <LayoutList className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('board')}
              className={cn(
                'p-1.5 rounded-md transition-colors',
                viewMode === 'board'
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:text-foreground',
              )}
              title="Board view"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
          </div>
          <button
            onClick={() => setDedupOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border border-border text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors cursor-pointer"
          >
            <Search className="h-4 w-4" />
            Find Duplicates
          </button>
          <AddTodoDialog />
          <DedupDialog open={dedupOpen} onOpenChange={setDedupOpen} />
        </div>
      </div>

      {/* Status bar */}
      <div className="px-4 pb-2">
        <StatusBar
          states={TODO_STATES}
          counts={statusCounts}
          activeFilter={filters.status}
          onFilterClick={handleStatusBarFilter}
        />
      </div>

      {/* Filters (list mode only) */}
      {viewMode === 'list' && (
        <div className="px-4 pb-4">
          <TodoFilters filters={filters} onChange={setFilters} />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {isLoading ? (
          <TodosSkeleton />
        ) : viewMode === 'list' ? (
          <TodoList todos={todos} />
        ) : (
          <BoardView
            items={todos}
            states={TODO_STATES}
            kind="todo"
            onTransition={(id, to) => void handleBoardTransition(id, to)}
            isPending={boardPending}
          />
        )}
      </div>

      {/* Stats bar */}
      <div className="border-t border-border px-4 py-2 flex items-center gap-4 text-xs text-muted-foreground shrink-0">
        <span>{statusCounts['todo'] ?? 0} todo</span>
        <span className="text-border">|</span>
        <span>{statusCounts['in_progress'] ?? 0} in progress</span>
        <span className="text-border">|</span>
        <span>{statusCounts['done'] ?? 0} done</span>
        <span className="text-border">|</span>
        <span>{statusCounts['backlog'] ?? 0} backlog</span>
      </div>
    </div>
  );
}
