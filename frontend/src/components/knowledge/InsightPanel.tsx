import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Sparkles, RefreshCw, Filter, Loader2 } from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';
import { InsightCard } from './InsightCard';
import type { InsightItem } from './InsightCard';

interface InsightsResponse {
  items: InsightItem[];
  total: number;
}

interface InsightsSummary {
  total_insights: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  total_entities: number;
  entities_by_type: Record<string, number>;
  average_confidence: number;
}

const TYPE_FILTERS = [
  { value: '', label: 'All Types' },
  { value: 'cross_reference', label: 'Cross-References' },
  { value: 'pattern', label: 'Patterns' },
  { value: 'contradiction', label: 'Contradictions' },
];

const STATUS_FILTERS = [
  { value: '', label: 'All Status' },
  { value: 'new', label: 'New' },
  { value: 'seen', label: 'Seen' },
  { value: 'actioned', label: 'Actioned' },
  { value: 'dismissed', label: 'Dismissed' },
];

const selectCls =
  'bg-card border border-border rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

export function InsightPanel() {
  const queryClient = useQueryClient();
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [offset, setOffset] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const limit = 20;

  const params = new URLSearchParams();
  if (typeFilter) params.set('type', typeFilter);
  if (statusFilter) params.set('status', statusFilter);
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  const { data, isLoading } = useQuery({
    queryKey: ['insights', { type: typeFilter, status: statusFilter, offset }],
    queryFn: () => apiFetch<InsightsResponse>(`/insights?${params.toString()}`),
  });

  const { data: summary } = useQuery({
    queryKey: ['insights-summary'],
    queryFn: () => apiFetch<InsightsSummary>('/insights/summary'),
  });

  const { data: detail } = useQuery({
    queryKey: ['insight-detail', selectedId],
    queryFn: () =>
      selectedId ? apiFetch<InsightItem & { entities: unknown[]; content_items: unknown[] }>(
        `/insights/${selectedId}`,
      ) : null,
    enabled: !!selectedId,
  });

  const generateMutation = useMutation({
    mutationFn: () => apiPost<{ generated: number }>('/insights/generate', {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
      queryClient.invalidateQueries({ queryKey: ['insights-summary'] });
    },
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) =>
      apiPost(`/insights/${id}/action`, { action }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
      queryClient.invalidateQueries({ queryKey: ['insights-summary'] });
      if (selectedId) {
        queryClient.invalidateQueries({ queryKey: ['insight-detail', selectedId] });
      }
    },
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const page = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="flex flex-col h-full">
      {/* Summary bar */}
      {summary && summary.total_insights > 0 && (
        <div className="px-4 py-3 border-b border-border bg-card/50 flex items-center gap-4 flex-wrap text-xs text-muted-foreground">
          <span className="font-medium text-foreground">
            {summary.total_insights} insights
          </span>
          {summary.by_status.new ? (
            <span className="text-info">{summary.by_status.new} new</span>
          ) : null}
          <span>{summary.total_entities} entities extracted</span>
          {summary.average_confidence > 0 && (
            <span>Avg confidence: {Math.round(summary.average_confidence * 100)}%</span>
          )}
        </div>
      )}

      {/* Toolbar */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-3 flex-wrap">
        <Filter className="h-4 w-4 text-muted-foreground" />

        <select
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value);
            setOffset(0);
          }}
          className={selectCls}
        >
          {TYPE_FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setOffset(0);
          }}
          className={selectCls}
        >
          {STATUS_FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>

        <div className="flex-1" />

        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium',
            'bg-accent/20 text-foreground hover:bg-accent/40 transition-colors',
            generateMutation.isPending && 'opacity-60 cursor-not-allowed',
          )}
        >
          {generateMutation.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Sparkles className="h-3.5 w-3.5" />
          )}
          Generate Insights
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-20 text-muted-foreground text-sm gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading insights...
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-3">
            <Sparkles className="h-8 w-8" />
            <p>No insights yet</p>
            <p className="text-xs">
              Extract entities from content first, then generate insights to find
              cross-source patterns.
            </p>
            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="mt-2 px-4 py-2 rounded-lg bg-accent/20 text-foreground text-sm hover:bg-accent/40 transition-colors"
            >
              Generate Now
            </button>
          </div>
        ) : (
          <div className="grid gap-3 p-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-2">
            {items.map((insight) => (
              <InsightCard
                key={insight.id}
                insight={insight}
                onAction={(id, action) =>
                  actionMutation.mutate({ id, action })
                }
                onView={(id) =>
                  setSelectedId(selectedId === id ? null : id)
                }
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail panel (slide-in) */}
      {selectedId && detail && (
        <div className="border-t border-border bg-card p-4 max-h-64 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-foreground">
              Insight Detail
            </h3>
            <button
              onClick={() => setSelectedId(null)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Close
            </button>
          </div>
          <p className="text-xs text-muted-foreground mb-2">
            {detail.description}
          </p>
          {(detail as any).entities?.length > 0 && (
            <div className="mb-2">
              <p className="text-xs font-medium text-foreground mb-1">
                Linked Entities:
              </p>
              <div className="flex flex-wrap gap-1">
                {(detail as any).entities.map((e: any) => (
                  <span
                    key={e.id}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-accent/20 text-foreground"
                  >
                    <span className="text-muted-foreground">
                      {e.entity_type}:
                    </span>
                    {e.value.length > 40 ? e.value.slice(0, 40) + '...' : e.value}
                  </span>
                ))}
              </div>
            </div>
          )}
          {(detail as any).content_items?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-foreground mb-1">
                Source Content:
              </p>
              <ul className="text-xs text-muted-foreground space-y-0.5">
                {(detail as any).content_items.map((c: any) => (
                  <li key={c.id} className="flex items-center gap-1">
                    <span className="text-accent">{c.source}</span>
                    <span>{c.title || c.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm text-muted-foreground">
          <span>
            {total} insight{total !== 1 ? 's' : ''} -- page {page} of{' '}
            {totalPages || 1}
          </span>
          <div className="flex gap-2">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - limit))}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
                offset === 0
                  ? 'opacity-40 cursor-not-allowed'
                  : 'hover:bg-accent/50 text-foreground',
              )}
            >
              Previous
            </button>
            <button
              disabled={offset + limit >= total}
              onClick={() => setOffset(offset + limit)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
                offset + limit >= total
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
