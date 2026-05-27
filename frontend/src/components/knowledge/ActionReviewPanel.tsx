import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Check, X, Zap, FileText, User, Calendar,
  ChevronRight, Loader2, CheckCheck,
} from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';

interface StagedAction {
  id: string;
  content_id: string;
  action_type: string;
  title: string;
  description?: string;
  assignee?: string;
  due_date?: string;
  priority: string;
  source_quote?: string;
  confidence: number;
  extraction_mode: string;
  status: string;
  result_id?: string;
  created_at?: string;
  content_title?: string;
}

interface StagedResponse {
  items: StagedAction[];
  total: number;
}

interface ActionStats {
  staged: number;
  approved: number;
  rejected: number;
  total: number;
}

const PRIORITY_STYLES: Record<string, string> = {
  high: 'bg-destructive/10 text-destructive',
  medium: 'bg-warning/10 text-warning',
  low: 'bg-muted text-muted-foreground',
};

const ACTION_TYPE_LABELS: Record<string, string> = {
  todo: 'Todo',
  decision: 'Decision',
  follow_up: 'Follow-up',
};

function ConfidenceDot({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    pct >= 80 ? 'text-success' :
    pct >= 60 ? 'text-warning' :
    'text-muted-foreground';

  return (
    <span className={cn('text-[10px] font-medium tabular-nums', color)}>
      {pct}%
    </span>
  );
}

function ActionCard({
  action,
  onApprove,
  onReject,
  isApproving,
  isRejecting,
}: {
  action: StagedAction;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  isApproving: boolean;
  isRejecting: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="group flex flex-col gap-2 px-4 py-3 hover:bg-accent/30 transition-colors">
      {/* Header row */}
      <div className="flex items-start gap-3">
        <div className="shrink-0 mt-0.5">
          <Zap size={14} className="text-warning" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className={cn(
              'text-[10px] px-1.5 py-0.5 rounded font-medium',
              action.action_type === 'todo' ? 'bg-info/10 text-info' :
              action.action_type === 'decision' ? 'bg-accent/50 text-accent-foreground' :
              'bg-success/10 text-success',
            )}>
              {ACTION_TYPE_LABELS[action.action_type] ?? action.action_type}
            </span>
            <span className={cn(
              'text-[10px] px-1.5 py-0.5 rounded font-medium',
              PRIORITY_STYLES[action.priority] ?? PRIORITY_STYLES.medium,
            )}>
              {action.priority}
            </span>
            <ConfidenceDot confidence={action.confidence} />
            <span className="text-[10px] text-muted-foreground">
              via {action.extraction_mode}
            </span>
          </div>

          <p className="text-sm font-medium text-foreground">{action.title}</p>

          {/* Meta row */}
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            {action.assignee && (
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <User size={10} />
                {action.assignee}
              </span>
            )}
            {action.due_date && (
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <Calendar size={10} />
                {action.due_date}
              </span>
            )}
            {action.content_title && (
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <FileText size={10} />
                {action.content_title}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => onApprove(action.id)}
            disabled={isApproving || isRejecting}
            className={cn(
              'p-1.5 rounded-lg hover:bg-success/20 text-success transition-colors',
              (isApproving || isRejecting) && 'opacity-50 cursor-not-allowed',
            )}
            title="Approve -- create todo"
          >
            {isApproving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
          </button>
          <button
            onClick={() => onReject(action.id)}
            disabled={isApproving || isRejecting}
            className={cn(
              'p-1.5 rounded-lg hover:bg-destructive/20 text-destructive transition-colors',
              (isApproving || isRejecting) && 'opacity-50 cursor-not-allowed',
            )}
            title="Reject"
          >
            {isRejecting ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />}
          </button>
          <button
            onClick={() => setExpanded(e => !e)}
            className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground transition-colors"
            title={expanded ? 'Collapse' : 'Show source quote'}
          >
            <ChevronRight size={14} className={cn('transition-transform', expanded && 'rotate-90')} />
          </button>
        </div>
      </div>

      {/* Expandable source quote */}
      {expanded && action.source_quote && (
        <div className="ml-8 px-3 py-2 bg-muted/30 border-l-2 border-warning/30 rounded-r-lg">
          <p className="text-xs text-muted-foreground italic leading-relaxed">
            &ldquo;{action.source_quote}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Full review panel for staged actions.
 * Split view: list of extracted actions with approve/reject per item + batch approve all.
 */
export function ActionReviewPanel() {
  const queryClient = useQueryClient();
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['actions-staged'],
    queryFn: () => apiFetch<StagedResponse>('/actions/staged?status=staged&limit=50'),
    staleTime: 10_000,
  });

  const { data: stats } = useQuery({
    queryKey: ['action-stats'],
    queryFn: () => apiFetch<ActionStats>('/actions/stats'),
    staleTime: 15_000,
  });

  const approveMut = useMutation({
    mutationFn: (id: string) => apiPost<unknown>(`/actions/${id}/approve`, {}),
    onMutate: (id) => setApprovingId(id),
    onSettled: () => setApprovingId(null),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['action-stats'] });
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  const rejectMut = useMutation({
    mutationFn: (id: string) => apiPost<unknown>(`/actions/${id}/reject`, {}),
    onMutate: (id) => setRejectingId(id),
    onSettled: () => setRejectingId(null),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['action-stats'] });
    },
  });

  const approveAllMut = useMutation({
    mutationFn: () => apiPost<{ approved: number; failed: number }>('/actions/approve-all', {}),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['action-stats'] });
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  const items = data?.items ?? [];
  const stagedCount = stats?.staged ?? items.length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 size={24} className="animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Zap size={40} className="mb-3 opacity-30" />
        <p className="text-sm font-medium">No pending actions</p>
        <p className="text-xs mt-1">
          Extract actions from content to see them here for review.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header bar with stats + approve all */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-warning/5 border border-warning/20 rounded-xl">
        <Zap size={14} className="text-warning" />
        <span className="text-sm text-muted-foreground flex-1">
          {stagedCount} action{stagedCount !== 1 ? 's' : ''} pending review
          {stats?.approved ? ` \u00b7 ${stats.approved} approved` : ''}
        </span>
        <button
          onClick={() => approveAllMut.mutate()}
          disabled={approveAllMut.isPending}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
            'bg-success/10 text-success hover:bg-success/20 transition-colors',
            approveAllMut.isPending && 'opacity-50 cursor-not-allowed',
          )}
        >
          {approveAllMut.isPending ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <CheckCheck size={14} />
          )}
          Approve All
        </button>
      </div>

      {/* Action cards list */}
      <div className="border border-border rounded-xl divide-y divide-border overflow-hidden">
        {items.map((action) => (
          <ActionCard
            key={action.id}
            action={action}
            onApprove={(id) => approveMut.mutate(id)}
            onReject={(id) => rejectMut.mutate(id)}
            isApproving={approvingId === action.id}
            isRejecting={rejectingId === action.id}
          />
        ))}
      </div>
    </div>
  );
}
