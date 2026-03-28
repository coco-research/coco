import { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { cn } from '../../lib/utils';
import { formatCost } from '../../lib/utils';
import type { Cycle } from '../../types/self-improve';

function CycleRow({ cycle, onSelect }: { cycle: Cycle; onSelect: (id: string) => void }) {
  const date = cycle.started_at ? new Date(cycle.started_at) : new Date(cycle.completed_at ?? '');
  const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
    ', ' + date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const merged = cycle.improvements.filter((i) => i.status === 'merged').length;
  const rejected = cycle.improvements.filter((i) => ['rejected_by_human', 'failed'].includes(i.status)).length;
  const total = cycle.improvements.length;

  const statusLabel = cycle.status.charAt(0).toUpperCase() + cycle.status.slice(1).replace(/_/g, ' ');

  return (
    <div className="py-4 border-b border-border last:border-b-0">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-foreground font-medium">{formatted}</span>
            <span className={cn(
              'px-2 py-0.5 rounded-full text-[10px] font-medium',
              cycle.status === 'completed' ? 'bg-green-500/20 text-green-400' :
              cycle.status === 'failed' ? 'bg-red-500/20 text-red-400' :
              cycle.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
              'bg-zinc-500/20 text-zinc-400',
            )}>
              {statusLabel}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            {total} improvement{total !== 1 ? 's' : ''} · {merged} merged · {rejected} rejected
          </p>
          <p className="text-xs text-muted-foreground">
            Budget: {formatCost(cycle.spent_usd)} / {formatCost(cycle.budget_usd)}
          </p>
        </div>
        <button
          onClick={() => onSelect(cycle.id)}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors shrink-0"
        >
          View Details
          <ExternalLink size={12} />
        </button>
      </div>
    </div>
  );
}

export function CycleHistory({ cycles, onSelectCycle }: { cycles: Cycle[]; onSelectCycle: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);

  if (cycles.length === 0) return null;

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-muted/30 transition-colors"
      >
        <span className="text-sm font-semibold text-foreground">Cycle History</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{cycles.length} past cycle{cycles.length !== 1 ? 's' : ''}</span>
          {expanded ? <ChevronUp size={16} className="text-muted-foreground" /> : <ChevronDown size={16} className="text-muted-foreground" />}
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-4">
          {cycles.map((cycle) => (
            <CycleRow key={cycle.id} cycle={cycle} onSelect={onSelectCycle} />
          ))}
        </div>
      )}
    </div>
  );
}
