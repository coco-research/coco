import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { cn } from '../../../lib/utils';
import { apiPost } from '../../../lib/api';
import type { ApprovalBatchData } from '../../../types/cards';

interface ApprovalBatchCardProps {
  data: ApprovalBatchData;
  variant?: 'jarvis' | 'light';
}

type RowState = 'pending' | 'approved' | 'rejected';

export function ApprovalBatchCard({
  data,
  variant = 'jarvis',
}: ApprovalBatchCardProps) {
  const isJarvis = variant === 'jarvis';
  const qc = useQueryClient();
  const [rowStates, setRowStates] = useState<Record<string, RowState>>({});
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    setLoadingId(id);
    try {
      await apiPost(`/drafts/${id}/${action}`, {});
      setRowStates((prev) => ({
        ...prev,
        [id]: action === 'approve' ? 'approved' : 'rejected',
      }));
      qc.invalidateQueries({ queryKey: ['drafts'] });
      qc.invalidateQueries({ queryKey: ['home'] });
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-2">
      {data.drafts.map((draft) => {
        const state = rowStates[draft.id] ?? 'pending';
        const isLoading = loadingId === draft.id;

        return (
          <div
            key={draft.id}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-500',
              isJarvis ? 'bg-white/5' : 'bg-muted/40',
              state === 'approved' && 'bg-[#34C759]/10 opacity-50',
              state === 'rejected' && 'bg-[#FF453A]/10 opacity-50',
            )}
          >
            <div className="flex-1 min-w-0">
              <p
                className={cn(
                  'text-sm font-medium truncate',
                  isJarvis ? 'text-white/90' : 'text-foreground',
                )}
              >
                {draft.title}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                {draft.project_name && (
                  <span
                    className={cn(
                      'text-[10px]',
                      isJarvis ? 'text-white/40' : 'text-muted-foreground',
                    )}
                  >
                    {draft.project_name}
                  </span>
                )}
                <span
                  className={cn(
                    'text-[10px] uppercase tracking-wider',
                    isJarvis ? 'text-white/30' : 'text-muted-foreground',
                  )}
                >
                  {draft.draft_type}
                </span>
              </div>
            </div>

            {state === 'pending' && (
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <button
                  type="button"
                  onClick={() => handleAction(draft.id, 'approve')}
                  disabled={isLoading}
                  className={cn(
                    'px-2.5 py-1 rounded text-[10px] font-semibold uppercase tracking-wider transition-colors',
                    isJarvis
                      ? 'bg-[#34C759]/15 text-[#34C759] hover:bg-[#34C759]/25 disabled:opacity-40'
                      : 'bg-green-100 text-green-700 hover:bg-green-200 disabled:opacity-40',
                  )}
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => handleAction(draft.id, 'reject')}
                  disabled={isLoading}
                  className={cn(
                    'px-2.5 py-1 rounded text-[10px] font-semibold uppercase tracking-wider transition-colors',
                    isJarvis
                      ? 'bg-[#FF453A]/15 text-[#FF453A] hover:bg-[#FF453A]/25 disabled:opacity-40'
                      : 'bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-40',
                  )}
                >
                  Reject
                </button>
              </div>
            )}

            {state !== 'pending' && (
              <span
                className={cn(
                  'text-[10px] font-semibold uppercase tracking-wider',
                  state === 'approved' ? 'text-[#34C759]' : 'text-[#FF453A]',
                )}
              >
                {state}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
