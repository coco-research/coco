import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import { TODO_STATES, STATE_LABELS } from '../../lib/state-machine';

interface Project {
  id: string;
  name: string;
}

export interface TodoFilterState {
  status: string;
  project_id: string;
  priority: string;
}

interface TodoFiltersProps {
  filters: TodoFilterState;
  onChange: (filters: TodoFilterState) => void;
}

const selectCls =
  'bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

export function TodoFilters({ filters, onChange }: TodoFiltersProps) {
  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ['projects-list'],
    queryFn: () => apiFetch<Project[]>('/projects'),
  });

  function update(key: keyof TodoFilterState, value: string) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <select
        aria-label="Filter todos by status"
        value={filters.status}
        onChange={(e) => update('status', e.target.value)}
        className={selectCls}
      >
        <option value="">All Statuses</option>
        {TODO_STATES.map((s) => (
          <option key={s} value={s}>
            {STATE_LABELS[s] ?? s}
          </option>
        ))}
        {/* Legacy statuses for backward compat */}
        <option value="open">Open (legacy)</option>
        <option value="dismissed">Dismissed (legacy)</option>
      </select>

      <select
        aria-label="Filter todos by project"
        value={filters.project_id}
        onChange={(e) => update('project_id', e.target.value)}
        className={selectCls}
      >
        <option value="">All Projects</option>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name || p.id}
          </option>
        ))}
      </select>

      <select
        aria-label="Filter todos by priority"
        value={filters.priority}
        onChange={(e) => update('priority', e.target.value)}
        className={selectCls}
      >
        <option value="">All Priorities</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>
  );
}
