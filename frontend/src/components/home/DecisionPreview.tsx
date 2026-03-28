import { cn } from '../../lib/utils';
import { Inbox, FileCheck, FolderOpen, AlertTriangle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DecisionPreviewProps {
  queue: {
    total: number;
    urgent: number;
    drafts: number;
    classify: number;
  };
  healthAlerts?: number;
}

interface QueueRow {
  icon: React.ReactNode;
  label: string;
  count: number;
  actionLabel?: string;
  actionTo?: string;
  variant?: 'destructive' | 'warning' | 'default';
}

export function DecisionPreview({ queue, healthAlerts = 0 }: DecisionPreviewProps) {
  const allClear = queue.urgent === 0 && queue.drafts === 0 && queue.classify === 0;

  const rows: QueueRow[] = [
    {
      icon: <AlertTriangle className="h-4 w-4" />,
      label: 'urgent items',
      count: queue.urgent,
      actionLabel: 'Triage',
      actionTo: '/inbox',
      variant: 'destructive',
    },
    {
      icon: <FileCheck className="h-4 w-4" />,
      label: 'drafts to review',
      count: queue.drafts,
      actionLabel: 'Review',
      actionTo: '/inbox',
    },
    {
      icon: <FolderOpen className="h-4 w-4" />,
      label: 'items to classify',
      count: queue.classify,
      actionLabel: 'Sort',
      actionTo: '/inbox',
    },
    {
      icon: <AlertTriangle className="h-4 w-4" />,
      label: 'health issues',
      count: healthAlerts ?? 0,
      variant: 'warning',
      actionTo: '/settings',
      actionLabel: 'Fix',
    },
  ];

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Inbox className="h-4 w-4 text-muted-foreground" />
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Decision Queue
          </p>
        </div>
        {queue.total > 0 && (
          <span className="inline-flex items-center rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-foreground">
            {queue.total.toLocaleString()}
          </span>
        )}
      </div>

      {allClear ? (
        /* Empty state */
        <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-4 py-3 text-sm text-emerald-400 flex items-center gap-2">
          <span>Queue is clear — nothing needs your attention.</span>
        </div>
      ) : (
        /* Queue rows */
        <div className="space-y-1">
          {rows.map((row, i) => {
            const active = row.count > 0;
            const isDestructive = row.variant === 'destructive' && active;
            const isWarning = row.variant === 'warning' && active;

            return (
              <div
                key={i}
                className={cn(
                  'flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors',
                  isDestructive && 'bg-red-500/10',
                  isWarning && 'bg-amber-500/10',
                  !active && 'opacity-50'
                )}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      isDestructive
                        ? 'text-red-400'
                        : isWarning
                          ? 'text-amber-400'
                          : active
                            ? 'text-muted-foreground'
                            : 'text-muted-foreground'
                    )}
                  >
                    {row.icon}
                  </span>
                  <span
                    className={cn(
                      isDestructive
                        ? 'text-red-400 font-medium'
                        : isWarning
                          ? 'text-amber-400 font-medium'
                          : active
                            ? 'text-foreground'
                            : 'text-muted-foreground'
                    )}
                  >
                    {row.count.toLocaleString()} {row.label}
                  </span>
                </div>

                {active && row.actionTo && row.actionLabel && (
                  <Link
                    to={row.actionTo}
                    className="flex items-center gap-1 text-xs font-medium text-accent-foreground hover:text-foreground transition-colors"
                  >
                    {row.actionLabel}
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Footer link */}
      <div className="mt-4 pt-3 border-t border-border">
        <Link
          to="/inbox"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          View full queue
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}
