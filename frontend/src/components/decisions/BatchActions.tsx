import { cn } from '../../lib/utils';

const btnBase = 'rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer';
const btnAccent = cn(btnBase, 'bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm');

export function BatchActions({
  draftCount,
  classifyCount,
  onApproveAllDrafts,
  onAcceptAllSuggestions,
}: {
  draftCount: number;
  classifyCount: number;
  onApproveAllDrafts: () => void;
  onAcceptAllSuggestions: () => void;
}) {
  if (draftCount === 0 && classifyCount === 0) return null;

  return (
    <div className="flex items-center gap-2 p-3 bg-card border border-border rounded-xl mb-4">
      <span className="text-xs text-muted-foreground mr-2">Batch:</span>
      {draftCount > 0 && (
        <button className={btnAccent} onClick={onApproveAllDrafts}>
          Approve All Drafts ({draftCount})
        </button>
      )}
      {classifyCount > 0 && (
        <button className={btnAccent} onClick={onAcceptAllSuggestions}>
          Accept All Suggestions ({classifyCount})
        </button>
      )}
    </div>
  );
}
