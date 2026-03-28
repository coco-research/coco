import { Link } from 'react-router-dom';
import { Inbox } from 'lucide-react';
import { cn } from '../../lib/utils';

interface QueueBadgeProps {
  total: number;
  urgent?: number;
  drafts?: number;
  classify?: number;
}

export function QueueBadge({ total, urgent, drafts, classify }: QueueBadgeProps) {
  const hasPending = total > 0 || (drafts ?? 0) > 0 || (classify ?? 0) > 0;
  const combinedCount = total + (drafts ?? 0) + (classify ?? 0);

  return (
    <Link
      to="/decisions"
      className="rounded-xl border border-border bg-card p-5 hover:shadow-md transition-all flex items-center gap-3"
    >
      <div className="relative">
        <Inbox size={20} className="text-muted-foreground" />
        {hasPending && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-white px-1">
            {combinedCount}
          </span>
        )}
      </div>

      <div className="flex flex-col">
        <span className="text-sm font-medium text-foreground">Pending Decisions</span>
        <span className="text-xs text-muted-foreground">
          {combinedCount === 0
            ? 'All clear'
            : [
                total > 0 ? `${total} task${total !== 1 ? 's' : ''}` : null,
                (drafts ?? 0) > 0 ? `${drafts} draft${drafts !== 1 ? 's' : ''}` : null,
                (classify ?? 0) > 0 ? `${classify} unsorted` : null,
                (urgent ?? 0) > 0 ? (
                  <span key="urgent" className={cn('text-destructive font-medium')}>
                    {urgent} urgent
                  </span>
                ) : null,
              ]
                .filter(Boolean)
                .map((item, i) => (
                  <span key={i}>
                    {i > 0 ? ' · ' : ''}
                    {item}
                  </span>
                ))}
        </span>
      </div>
    </Link>
  );
}
