import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface CostEvent {
  id?: number;
  timestamp: string;
  model: string;
  feature?: string;
  source?: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

interface CostEventsResponse {
  items: CostEvent[];
  total: number;
}

const PAGE_SIZE = 20;

export function CostEventsTable() {
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery<CostEventsResponse>({
    queryKey: ['cost-events', page],
    queryFn: () =>
      apiFetch<CostEventsResponse>(
        `/costs/events?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`,
      ),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(Math.ceil(total / PAGE_SIZE), 1);

  function exportCsv() {
    if (!items.length) return;
    const headers = ['Date', 'Model', 'Feature/Source', 'Input Tokens', 'Output Tokens', 'Cost'];
    const rows = items.map((e) => [
      e.timestamp,
      e.model,
      e.feature || e.source || '',
      e.input_tokens,
      e.output_tokens,
      e.cost_usd.toFixed(6),
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cost-events-page${page + 1}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Cost Events ({total})
        </p>
        <button
          onClick={exportCsv}
          disabled={items.length === 0}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md transition-colors',
            'text-muted-foreground hover:text-foreground hover:bg-accent/50 disabled:opacity-40 disabled:cursor-not-allowed',
          )}
        >
          <Download className="h-3.5 w-3.5" />
          CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              <th className="px-4 py-2 font-medium text-muted-foreground">Date</th>
              <th className="px-4 py-2 font-medium text-muted-foreground">Model</th>
              <th className="px-4 py-2 font-medium text-muted-foreground">Feature/Source</th>
              <th className="px-4 py-2 font-medium text-muted-foreground text-right">Input Tokens</th>
              <th className="px-4 py-2 font-medium text-muted-foreground text-right">Output Tokens</th>
              <th className="px-4 py-2 font-medium text-muted-foreground text-right">Cost</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-border/50">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-4 py-2">
                      <div className="animate-pulse rounded bg-accent/50 h-4 w-20" />
                    </td>
                  ))}
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  No cost events found.
                </td>
              </tr>
            ) : (
              items.map((event, i) => (
                <tr
                  key={event.id ?? i}
                  className="border-b border-border/50 hover:bg-accent/50/50 transition-colors"
                >
                  <td className="px-4 py-2 text-muted-foreground whitespace-nowrap">
                    {new Date(event.timestamp).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2 text-foreground">{event.model}</td>
                  <td className="px-4 py-2 text-muted-foreground">{event.feature || event.source || '-'}</td>
                  <td className="px-4 py-2 text-right font-mono text-muted-foreground">
                    {event.input_tokens.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-muted-foreground">
                    {event.output_tokens.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-foreground">
                    ${event.cost_usd.toFixed(4)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-border">
        <span className="text-xs text-muted-foreground">
          Page {page + 1} of {totalPages}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-md border border-border text-muted-foreground hover:text-foreground hover:bg-accent/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Previous
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-md border border-border text-muted-foreground hover:text-foreground hover:bg-accent/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
