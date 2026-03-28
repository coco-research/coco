import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';
import { DecisionCard } from './DecisionCard';
import type { DecisionItem } from './DecisionCard';

const TYPE_LABELS: Record<DecisionItem['type'], string> = {
  urgent: 'URGENT',
  draft_approval: 'DRAFTS',
  classify: 'CLASSIFY',
  health: 'HEALTH',
  overdue: 'OVERDUE',
};

export function QueueSection({ type, items }: { type: DecisionItem['type']; items: DecisionItem[] }) {
  const [open, setOpen] = useState(true);

  if (items.length === 0) return null;

  return (
    <div className="mb-4">
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'flex items-center gap-2 w-full text-left py-2 px-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground',
          'hover:text-foreground transition-colors cursor-pointer',
        )}
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {TYPE_LABELS[type]}
        <span className="inline-flex items-center justify-center rounded-full bg-card border border-border px-1.5 py-0.5 text-[10px] font-bold">
          {items.length}
        </span>
      </button>
      {open && (
        <div className="flex flex-col gap-2">
          {items.map((item) => (
            <DecisionCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
