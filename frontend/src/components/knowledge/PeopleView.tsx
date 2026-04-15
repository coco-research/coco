import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Users, Loader2, ArrowUpDown } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface PersonNode {
  gid: string;
  canonical_name: string;
  importance_score: number;
  projects: string[];
  project_count: number;
  connections: number;
}

interface PeopleResponse {
  items: PersonNode[];
  total: number;
}

type SortKey = 'name' | 'projects' | 'connections' | 'importance';

interface PeopleViewProps {
  onSelectGid?: (gid: string) => void;
}

export function PeopleView({ onSelectGid }: PeopleViewProps) {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('importance');
  const [sortAsc, setSortAsc] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['people-graph'],
    queryFn: () => apiFetch<PeopleResponse>('/knowledge/people-graph'),
  });

  const items = data?.items ?? [];

  // Filter
  const filtered = search
    ? items.filter((p) => p.canonical_name.toLowerCase().includes(search.toLowerCase()))
    : items;

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    let cmp = 0;
    switch (sortBy) {
      case 'name': cmp = a.canonical_name.localeCompare(b.canonical_name); break;
      case 'projects': cmp = a.project_count - b.project_count; break;
      case 'connections': cmp = a.connections - b.connections; break;
      case 'importance': cmp = a.importance_score - b.importance_score; break;
    }
    return sortAsc ? cmp : -cmp;
  });

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) setSortAsc(!sortAsc);
    else { setSortBy(key); setSortAsc(false); }
  };

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <button
      onClick={() => toggleSort(field)}
      className={cn(
        'flex items-center gap-1 text-xs font-medium transition-colors',
        sortBy === field ? 'text-foreground' : 'text-muted-foreground hover:text-foreground',
      )}
    >
      {label}
      {sortBy === field && <ArrowUpDown className="h-3 w-3" />}
    </button>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground text-sm gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading people graph...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="px-4 py-3 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search people..."
            className="w-full pl-9 pr-3 py-2 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
          />
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          {filtered.length.toLocaleString()} of {items.length.toLocaleString()} people
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-card border-b border-border">
            <tr>
              <th className="text-left px-4 py-2"><SortHeader label="Name" field="name" /></th>
              <th className="text-left px-4 py-2"><SortHeader label="Projects" field="projects" /></th>
              <th className="text-left px-4 py-2"><SortHeader label="Connections" field="connections" /></th>
              <th className="text-left px-4 py-2"><SortHeader label="Importance" field="importance" /></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {sorted.slice(0, 200).map((person) => (
              <tr
                key={person.gid}
                onClick={() => onSelectGid?.(person.gid)}
                className="hover:bg-accent/5 cursor-pointer transition-colors"
              >
                <td className="px-4 py-2">
                  <span className="text-sm font-medium text-foreground">{person.canonical_name}</span>
                </td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-foreground font-medium">{person.project_count}</span>
                    {person.projects?.length > 0 && (
                      <span className="text-[10px] text-muted-foreground truncate max-w-[150px]">
                        {person.projects.slice(0, 3).join(', ')}
                        {person.projects.length > 3 && ` +${person.projects.length - 3}`}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-2 text-xs text-foreground">{person.connections}</td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-1.5">
                    <div className="w-12 h-1.5 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full"
                        style={{ width: `${Math.min(person.importance_score, 100)}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-muted-foreground">{Math.round(person.importance_score)}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {sorted.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-3">
            <Users className="h-8 w-8" />
            <p>No people found</p>
          </div>
        )}

        {sorted.length > 200 && (
          <div className="px-4 py-3 text-xs text-muted-foreground text-center border-t border-border">
            Showing 200 of {sorted.length} — use search to narrow
          </div>
        )}
      </div>
    </div>
  );
}
