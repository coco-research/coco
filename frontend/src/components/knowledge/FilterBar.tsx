import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Mail, Mic, Bug, FileText, Search, X } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';
import type { ReactNode } from 'react';

interface Project {
  id: string;
  name: string;
}

const SOURCE_OPTIONS: { value: string; label: string; icon: ReactNode }[] = [
  { value: '', label: 'All Sources', icon: null },
  { value: 'email', label: 'Email', icon: <Mail className="h-3.5 w-3.5" /> },
  { value: 'voice', label: 'Voice', icon: <Mic className="h-3.5 w-3.5" /> },
  { value: 'jira', label: 'Jira', icon: <Bug className="h-3.5 w-3.5" /> },
  { value: 'confluence', label: 'Confluence', icon: <FileText className="h-3.5 w-3.5" /> },
];

const selectCls = 'bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

export function FilterBar() {
  const [searchParams, setSearchParams] = useSearchParams();

  const source = searchParams.get('source') ?? '';
  const projectId = searchParams.get('project_id') ?? '';
  const q = searchParams.get('q') ?? '';

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiFetch<Project[]>('/projects'),
  });

  function setParam(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
      // Reset offset when filters change
      next.delete('offset');
      return next;
    });
  }

  function clearFilters() {
    setSearchParams({});
  }

  const hasFilters = source || projectId || q;

  return (
    <div className="sticky top-0 z-40 bg-card/80 backdrop-blur-sm border-b border-border p-4 flex items-center gap-3 flex-wrap">
      {/* Source dropdown */}
      <select
        value={source}
        onChange={(e) => setParam('source', e.target.value)}
        className={selectCls}
      >
        {SOURCE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Project dropdown */}
      <select
        value={projectId}
        onChange={(e) => setParam('project_id', e.target.value)}
        className={selectCls}
      >
        <option value="">All Projects</option>
        {projects?.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>

      {/* Search input */}
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search content..."
          value={q}
          onChange={(e) => setParam('q', e.target.value)}
          className="w-full bg-card border border-border rounded-lg pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
        />
      </div>

      {/* Clear filters */}
      {hasFilters && (
        <button
          onClick={clearFilters}
          className={cn(
            'flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg',
            'text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all',
          )}
        >
          <X className="h-3.5 w-3.5" />
          Clear
        </button>
      )}
    </div>
  );
}
