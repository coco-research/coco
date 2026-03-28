import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch, apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';

interface DraftDetail {
  id: string;
  content: string;
  project: string;
  template: string;
}

const btnBase = 'rounded-lg px-4 py-2 text-sm font-medium transition-all cursor-pointer';
const btnApprove = cn(btnBase, 'bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm');
const btnReject = cn(btnBase, 'bg-destructive/20 text-destructive hover:bg-destructive/20');

export function DraftPreview({
  draftId,
  onClose,
  onAction,
}: {
  draftId: string;
  onClose: () => void;
  onAction: () => void;
}) {
  const { data: draft, isLoading } = useQuery({
    queryKey: ['draft', draftId],
    queryFn: () => apiFetch<DraftDetail>(`/drafts/${draftId}`),
  });

  async function approve() {
    await apiPost(`/drafts/${draftId}/approve`, {});
    onAction();
    onClose();
  }

  async function reject() {
    await apiPost(`/drafts/${draftId}/reject`, {});
    onAction();
    onClose();
  }

  return (
    <Dialog.Root open onOpenChange={(v) => { if (!v) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl max-h-[80vh] flex flex-col bg-card border border-border rounded-2xl shadow-2xl">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <Dialog.Title className="text-lg font-semibold text-foreground">Draft Preview</Dialog.Title>
            <Dialog.Close asChild>
              <button className="text-muted-foreground hover:text-foreground cursor-pointer" aria-label="Close">
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {isLoading && <p className="text-muted-foreground text-sm">Loading...</p>}
            {draft && (
              <>
                <div className="flex items-center gap-2 mb-3 text-xs text-muted-foreground">
                  {draft.project && (
                    <span className="inline-flex items-center rounded bg-accent/10 text-accent px-1.5 py-0.5">
                      {draft.project}
                    </span>
                  )}
                  {draft.template && (
                    <span className="inline-flex items-center rounded bg-accent/50 px-1.5 py-0.5">
                      {draft.template}
                    </span>
                  )}
                </div>
                <pre className="whitespace-pre-wrap text-sm text-foreground leading-relaxed font-sans">
                  {draft.content}
                </pre>
              </>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 p-4 border-t border-border">
            <button className={btnReject} onClick={() => void reject()}>Reject</button>
            <button className={btnApprove} onClick={() => void approve()}>Approve</button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
