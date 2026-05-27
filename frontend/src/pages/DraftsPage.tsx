import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, Check, X, ChevronDown, ChevronRight } from 'lucide-react';
import { apiFetch, apiPost } from '../lib/api';
import { cn } from '../lib/utils';
import { useToast } from '../components/shared/Toast';
import { ErrorState } from '../components/shared/ErrorState';

interface Draft {
  id: string;
  project_id: string;
  source_content_id: string;
  target_template: string;
  target_section: string;
  content: string;
  format: string;
  status: string;
  created_at: string;
  reviewed_at: string | null;
}

type FilterStatus = '' | 'pending' | 'approved' | 'rejected';

function DraftsSkeleton() {
  const pulse = 'animate-pulse rounded bg-muted/50';
  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <div className={`${pulse} h-8 w-32`} />
        <div className={`${pulse} h-8 w-32`} />
        <div className={`${pulse} h-8 w-32`} />
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className={`${pulse} h-20`} />
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-warning/15 text-warning border-warning/20',
    approved: 'bg-success/15 text-success border-success/20',
    rejected: 'bg-destructive/15 text-destructive border-destructive/20',
  };
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-full border',
        styles[status] ?? 'bg-muted text-muted-foreground border-border',
      )}
    >
      {status}
    </span>
  );
}

function DraftCard({
  draft,
  onApprove,
  onReject,
}: {
  draft: Draft;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-border rounded-lg bg-card overflow-hidden">
      <div className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-accent/30 transition-colors">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          aria-label={`${expanded ? 'Collapse' : 'Expand'} ${draft.target_template} / ${draft.target_section}`}
          className="flex items-center gap-3 min-w-0 flex-1 text-left cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-sm"
        >
          {expanded ? (
            <ChevronDown size={14} aria-hidden="true" className="text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight size={14} aria-hidden="true" className="text-muted-foreground shrink-0" />
          )}
          <FileText size={14} aria-hidden="true" className="text-muted-foreground shrink-0" />
          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground truncate">
                {draft.target_template} / {draft.target_section}
              </span>
              <StatusBadge status={draft.status} />
            </span>
            <span className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
              <span>{draft.project_id}</span>
              <span className="text-border">|</span>
              <span>{draft.format}</span>
              <span className="text-border">|</span>
              <span>{new Date(draft.created_at).toLocaleDateString()}</span>
            </span>
          </span>
        </button>
        {draft.status === 'pending' && (
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              onClick={() => onApprove(draft.id)}
              className="p-1.5 rounded-md text-success hover:bg-success/10 transition-colors"
              aria-label={`Approve draft ${draft.target_template} / ${draft.target_section}`}
            >
              <Check size={14} aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={() => onReject(draft.id)}
              className="p-1.5 rounded-md text-destructive hover:bg-destructive/10 transition-colors"
              aria-label={`Reject draft ${draft.target_template} / ${draft.target_section}`}
            >
              <X size={14} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-border/50">
          <pre className="text-sm text-muted-foreground whitespace-pre-wrap font-mono bg-muted/30 rounded-md p-3 max-h-60 overflow-y-auto">
            {draft.content}
          </pre>
        </div>
      )}
    </div>
  );
}

export default function DraftsPage() {
  const { toast } = useToast();
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('');
  const [projectFilter, setProjectFilter] = useState('');

  const queryParams = new URLSearchParams();
  if (statusFilter) queryParams.set('status', statusFilter);
  if (projectFilter) queryParams.set('project_id', projectFilter);
  queryParams.set('limit', '200');

  const { data, isLoading, isError, error, refetch } = useQuery<Draft[]>({
    queryKey: ['drafts', statusFilter, projectFilter],
    queryFn: () => apiFetch<Draft[]>(`/drafts?${queryParams.toString()}`),
    refetchInterval: 30000,
  });

  const drafts = data ?? [];

  // Status counts
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const d of drafts) {
      counts[d.status] = (counts[d.status] ?? 0) + 1;
    }
    return counts;
  }, [drafts]);

  // Unique projects for filter
  const projects = useMemo(() => {
    const ids = new Set(drafts.map((d) => d.project_id).filter(Boolean));
    return [...ids].sort();
  }, [drafts]);

  async function handleApprove(id: string) {
    try {
      await apiPost(`/drafts/${id}/approve`, {});
      toast('Draft approved', 'success');
      void refetch();
    } catch {
      toast('Failed to approve draft', 'error');
    }
  }

  async function handleReject(id: string) {
    try {
      await apiPost(`/drafts/${id}/reject`, {});
      toast('Draft rejected', 'success');
      void refetch();
    } catch {
      toast('Failed to reject draft', 'error');
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Drafts</h1>
          <span className="text-sm text-muted-foreground bg-card border border-border rounded-full px-2 py-0.5">
            {drafts.length}
          </span>
        </div>
      </div>

      {/* Status bar */}
      <div className="px-4 pb-2">
        <div className="flex items-center gap-1 text-xs">
          {(['', 'pending', 'approved', 'rejected'] as FilterStatus[]).map((s) => {
            const label = s || 'all';
            const count = s ? (statusCounts[s] ?? 0) : drafts.length;
            const isActive = statusFilter === s;
            return (
              <button
                key={label}
                onClick={() => setStatusFilter(s)}
                className={cn(
                  'px-2.5 py-1 rounded-md transition-colors capitalize',
                  isActive
                    ? 'bg-accent text-accent-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50',
                )}
              >
                {label} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Project filter */}
      {projects.length > 1 && (
        <div className="px-4 pb-3">
          <select
            aria-label="Filter drafts by project"
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
            className="text-xs bg-card border border-border rounded-md px-2 py-1.5 text-foreground"
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
        {isLoading ? (
          <DraftsSkeleton />
        ) : isError ? (
          <ErrorState
            error={error}
            title="Couldn't load drafts"
            onRetry={() => void refetch()}
          />
        ) : drafts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <FileText size={32} className="text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">No drafts found</p>
          </div>
        ) : (
          drafts.map((draft) => (
            <DraftCard
              key={draft.id}
              draft={draft}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))
        )}
      </div>

      {/* Stats bar */}
      <div className="border-t border-border px-4 py-2 flex items-center gap-4 text-xs text-muted-foreground shrink-0">
        <span>{statusCounts['pending'] ?? 0} pending</span>
        <span className="text-border">|</span>
        <span>{statusCounts['approved'] ?? 0} approved</span>
        <span className="text-border">|</span>
        <span>{statusCounts['rejected'] ?? 0} rejected</span>
      </div>
    </div>
  );
}
