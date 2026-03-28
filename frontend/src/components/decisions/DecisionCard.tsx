import { useState } from 'react';
import { cn, timeAgo } from '../../lib/utils';
import { apiPost } from '../../lib/api';
import { useQueryClient } from '@tanstack/react-query';
import { DraftPreview } from './DraftPreview';

export interface DecisionItem {
  id: string;
  priority: number;
  type: 'urgent' | 'draft_approval' | 'classify' | 'health' | 'overdue';
  source_id: string;
  summary: string;
  project: string | null;
  person: string | null;
  created_at: string;
  deferred_count: number;
  status: string;
}

const TYPE_BORDER_COLORS: Record<DecisionItem['type'], string> = {
  urgent: 'border-l-error',
  draft_approval: 'border-l-info',
  classify: 'border-l-warning',
  health: 'border-l-warning',
  overdue: 'border-l-border-strong',
};

const btnBase = 'rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer';
const btnApprove = cn(btnBase, 'bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm');
const btnReject = cn(btnBase, 'bg-destructive/20 text-destructive hover:bg-destructive/20');
const btnOutline = cn(btnBase, 'bg-card text-muted-foreground border border-border hover:bg-accent/50');

export function DecisionCard({ item }: { item: DecisionItem }) {
  const qc = useQueryClient();
  const [showDraft, setShowDraft] = useState(false);

  function invalidate() {
    void qc.invalidateQueries({ queryKey: ['queue'] });
  }

  async function approve() {
    await apiPost(`/drafts/${item.source_id}/approve`, {});
    invalidate();
  }

  async function reject() {
    await apiPost(`/drafts/${item.source_id}/reject`, {});
    invalidate();
  }

  return (
    <>
      <div
        className={cn(
          'bg-card rounded-xl border border-border p-5 border-l-[3px] hover:shadow-md transition-all',
          TYPE_BORDER_COLORS[item.type],
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center rounded-lg bg-accent/50 px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground">
                P{item.priority}
              </span>
              <span className="font-semibold text-sm text-foreground truncate">{item.summary}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {item.project && (
                <span className="inline-flex items-center rounded-full bg-accent/20 text-accent px-2 py-0.5">
                  {item.project}
                </span>
              )}
              {item.person && (
                <span className="inline-flex items-center rounded-full bg-accent/50 px-2 py-0.5">
                  {item.person}
                </span>
              )}
              {item.deferred_count > 0 && (
                <span className="inline-flex items-center rounded-full bg-warning/20 text-warning px-2 py-0.5">
                  deferred x{item.deferred_count}
                </span>
              )}
              <span>{timeAgo(item.created_at)}</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {item.type === 'draft_approval' && (
              <>
                <button className={btnApprove} onClick={() => void approve()}>Approve</button>
                <button className={btnReject} onClick={() => void reject()}>Reject</button>
                <button className={btnOutline} onClick={() => setShowDraft(true)}>Show</button>
              </>
            )}
            {item.type === 'classify' && (
              <button className={btnOutline}>Assign</button>
            )}
            {item.type === 'health' && (
              <>
                <button className={btnOutline}>Fix</button>
                <button className={btnOutline}>Skip</button>
              </>
            )}
            {item.type === 'overdue' && (
              <>
                <button className={btnApprove}>Act Now</button>
                <button className={btnOutline}>Defer</button>
                <button className={btnOutline}>Dismiss</button>
              </>
            )}
            {item.type === 'urgent' && (
              <>
                <button className={btnApprove}>Reply</button>
                <button className={btnOutline}>Defer</button>
                <button className={btnOutline}>Dismiss</button>
              </>
            )}
          </div>
        </div>
      </div>

      {showDraft && (
        <DraftPreview draftId={item.source_id} onClose={() => setShowDraft(false)} onAction={invalidate} />
      )}
    </>
  );
}
