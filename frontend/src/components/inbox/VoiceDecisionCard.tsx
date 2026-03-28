import { Check, X, Clock, ChevronRight, Mic } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface VoiceDecisionItem {
  type: 'draft' | 'todo' | 'content';
  id: string;
  title: string;
  subtitle?: string;
  project?: string;
  preview?: string;
}

interface Props {
  item: VoiceDecisionItem | null;
  onApprove: () => void;
  onReject: () => void;
  onDefer: () => void;
  onNext: () => void;
  isListening?: boolean;
}

export function VoiceDecisionCard({ item, onApprove, onReject, onDefer, onNext, isListening }: Props) {
  if (!item) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mb-4">
          <Check size={32} className="text-accent" />
        </div>
        <h2 className="text-lg font-medium text-foreground">Queue clear</h2>
        <p className="text-sm text-muted-foreground mt-1">No pending decisions</p>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto">
      {/* Card */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-lg">
        {/* Type badge */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">
            {item.type}
          </span>
          {item.project && (
            <span className="text-[10px] bg-accent/10 text-accent px-2 py-0.5 rounded-full">
              {item.project}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-xl font-medium text-foreground mb-2">{item.title}</h3>

        {item.subtitle && (
          <p className="text-sm text-muted-foreground mb-3">{item.subtitle}</p>
        )}

        {item.preview && (
          <p className="text-sm text-muted-foreground/70 bg-muted/30 rounded-lg p-3 mb-4 line-clamp-3">
            {item.preview}
          </p>
        )}

        {/* Voice hint */}
        {isListening && (
          <div className="flex items-center gap-2 text-xs text-accent mb-4 animate-pulse">
            <Mic size={14} />
            Say &quot;approve&quot;, &quot;reject&quot;, &quot;defer&quot;, or &quot;next&quot;
          </div>
        )}

        {/* Action buttons -- large touch targets for voice+tap */}
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={onApprove}
            className={cn(
              'flex flex-col items-center gap-1.5 py-3 px-4 rounded-xl transition-colors',
              'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border border-emerald-500/20',
            )}
          >
            <Check size={20} />
            <span className="text-xs font-medium">Approve</span>
          </button>
          <button
            onClick={onReject}
            className={cn(
              'flex flex-col items-center gap-1.5 py-3 px-4 rounded-xl transition-colors',
              'bg-destructive/10 text-destructive hover:bg-destructive/20 border border-destructive/20',
            )}
          >
            <X size={20} />
            <span className="text-xs font-medium">Reject</span>
          </button>
          <button
            onClick={onDefer}
            className={cn(
              'flex flex-col items-center gap-1.5 py-3 px-4 rounded-xl transition-colors',
              'bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border border-amber-500/20',
            )}
          >
            <Clock size={20} />
            <span className="text-xs font-medium">Defer</span>
          </button>
        </div>
      </div>

      {/* Next button */}
      <button
        onClick={onNext}
        className="flex items-center justify-center gap-2 w-full mt-3 py-2.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        Next item <ChevronRight size={14} />
      </button>
    </div>
  );
}
