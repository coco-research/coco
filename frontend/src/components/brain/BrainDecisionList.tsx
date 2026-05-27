import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Scale, ChevronDown } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';
import type { BrainDecision } from '../../types/brain';
import { ErrorState } from '../shared/ErrorState';

interface BrainDecisionListProps {
  search?: string;
}

interface DecisionsResponse {
  items: BrainDecision[];
  total: number;
}

const LIMIT = 20;

// ---------------------------------------------------------------------------
// Date grouping utility
// ---------------------------------------------------------------------------

function dateLabel(dateStr: string): string {
  const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T') + 'Z');
  if (isNaN(d.getTime())) return 'Unknown';
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  if (target.getTime() === today.getTime()) return 'Today';
  if (target.getTime() === yesterday.getTime()) return 'Yesterday';
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function groupByDate(items: BrainDecision[]): Map<string, BrainDecision[]> {
  const groups = new Map<string, BrainDecision[]>();
  for (const item of items) {
    const label = dateLabel(item.date);
    const existing = groups.get(label);
    if (existing) {
      existing.push(item);
    } else {
      groups.set(label, [item]);
    }
  }
  return groups;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BrainDecisionList({ search }: BrainDecisionListProps) {
  const [offset, setOffset] = useState(0);
  const [decidedByFilter, setDecidedByFilter] = useState('');

  const params = new URLSearchParams();
  if (search) params.set('search', search);
  params.set('limit', String(LIMIT));
  params.set('offset', String(offset));

  const { data, isLoading, isError, error, refetch } = useQuery<DecisionsResponse>({
    queryKey: ['brain-decisions', search, offset],
    queryFn: () => apiFetch<DecisionsResponse>(`/brain/decisions?${params.toString()}`),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const page = Math.floor(offset / LIMIT) + 1;
  const totalPages = Math.ceil(total / LIMIT);

  // Collect unique decided_by values for the dropdown
  const decidedByOptions = useMemo(() => {
    const set = new Set<string>();
    for (const d of items) {
      if (d.decided_by) set.add(d.decided_by);
    }
    return Array.from(set).sort();
  }, [items]);

  // Client-side filter for decided_by
  const filtered = useMemo(
    () => (decidedByFilter ? items.filter((d) => d.decided_by === decidedByFilter) : items),
    [items, decidedByFilter],
  );

  const grouped = useMemo(() => groupByDate(filtered), [filtered]);

  return (
    <div className="flex flex-col h-full">
      {/* Filter row */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-3">
        <span className="text-xs text-muted-foreground whitespace-nowrap">Decided by:</span>
        <div className="relative">
          <select
            aria-label="Filter decisions by decider"
            value={decidedByFilter}
            onChange={(e) => setDecidedByFilter(e.target.value)}
            className="appearance-none bg-card border border-border rounded-lg pl-2 pr-7 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent/20"
          >
            <option value="">All</option>
            {decidedByOptions.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground pointer-events-none" />
        </div>
        <span className="ml-auto text-xs text-muted-foreground">
          {total.toLocaleString()} decision{total !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Decision list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-20 text-muted-foreground text-sm gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading decisions...
          </div>
        ) : isError ? (
          <div className="p-6">
            <ErrorState
              error={error}
              title="Couldn't load decisions"
              onRetry={() => void refetch()}
            />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-3">
            <Scale className="h-8 w-8" />
            <p>No decisions found</p>
            <p className="text-xs">
              {search ? 'Try a different search term.' : 'The brain has not recorded any decisions yet.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {Array.from(grouped.entries()).map(([label, decisions]) => (
              <div key={label}>
                {/* Date group header */}
                <div className="px-4 py-2 bg-card/60 sticky top-0 z-10">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
                    {label}
                  </span>
                </div>
                {/* Decision rows */}
                {decisions.map((decision) => (
                  <div
                    key={decision.id}
                    className="px-4 py-3 hover:bg-accent/5 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      {/* Date dot */}
                      <div className="mt-2 h-2.5 w-2.5 rounded-full bg-accent shrink-0" />

                      {/* Main content */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">{decision.decision}</p>
                        {decision.context && (
                          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                            {decision.context}
                          </p>
                        )}
                      </div>

                      {/* Right side: pills */}
                      <div className="flex items-center gap-2 shrink-0">
                        {decision.decided_by && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent">
                            {decision.decided_by}
                          </span>
                        )}
                        {decision.impact && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400">
                            {decision.impact}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
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
