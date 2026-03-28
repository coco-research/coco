import {
  GitBranch,
  Clock,
  AlertTriangle,
  Eye,
  CheckCircle2,
  XCircle,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { timeAgo } from '../../lib/utils';
import type { ReactNode } from 'react';

export interface InsightItem {
  id: string;
  insight_type: 'cross_reference' | 'pattern' | 'contradiction';
  title: string;
  description: string;
  confidence: number;
  status: 'new' | 'seen' | 'actioned' | 'dismissed';
  entity_ids: string[];
  content_ids: string[];
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface InsightCardProps {
  insight: InsightItem;
  onAction: (id: string, action: string) => void;
  onView: (id: string) => void;
}

const TYPE_CONFIG: Record<
  string,
  { icon: ReactNode; label: string; color: string; bg: string }
> = {
  cross_reference: {
    icon: <GitBranch className="h-4 w-4" />,
    label: 'Cross-Reference',
    color: 'text-info',
    bg: 'bg-info/10',
  },
  pattern: {
    icon: <Clock className="h-4 w-4" />,
    label: 'Pattern',
    color: 'text-accent',
    bg: 'bg-accent/10',
  },
  contradiction: {
    icon: <AlertTriangle className="h-4 w-4" />,
    label: 'Contradiction',
    color: 'text-warning',
    bg: 'bg-warning/10',
  },
};

const STATUS_STYLES: Record<string, string> = {
  new: 'bg-info/20 text-info',
  seen: 'bg-muted text-muted-foreground',
  actioned: 'bg-success/20 text-success',
  dismissed: 'bg-accent/50 text-muted-foreground',
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const barColor =
    pct >= 80 ? 'bg-success' : pct >= 50 ? 'bg-warning' : 'bg-muted-foreground';

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 rounded-full bg-border overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  );
}

export function InsightCard({ insight, onAction, onView }: InsightCardProps) {
  const config = TYPE_CONFIG[insight.insight_type] ?? TYPE_CONFIG.cross_reference;

  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card p-4 transition-all',
        'hover:border-accent/40 hover:shadow-sm',
        insight.status === 'dismissed' && 'opacity-50',
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className={cn('p-1.5 rounded-lg', config.bg, config.color)}>
            {config.icon}
          </span>
          <span className={cn('text-xs font-medium', config.color)}>
            {config.label}
          </span>
          <span
            className={cn(
              'text-xs px-2 py-0.5 rounded-full font-medium capitalize',
              STATUS_STYLES[insight.status],
            )}
          >
            {insight.status}
          </span>
        </div>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {timeAgo(insight.created_at)}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-sm font-medium text-foreground mb-1 line-clamp-2">
        {insight.title}
      </h3>

      {/* Description */}
      <p className="text-xs text-muted-foreground mb-3 line-clamp-3">
        {insight.description}
      </p>

      {/* Entity pills */}
      {insight.entity_ids.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          <span className="text-xs text-muted-foreground">
            {insight.entity_ids.length} entities
          </span>
          {insight.content_ids.length > 0 && (
            <span className="text-xs text-muted-foreground">
              / {insight.content_ids.length} sources
            </span>
          )}
        </div>
      )}

      {/* Confidence + Actions */}
      <div className="flex items-center justify-between">
        <ConfidenceBar value={insight.confidence} />

        <div className="flex items-center gap-1">
          {insight.status === 'new' && (
            <button
              onClick={() => onAction(insight.id, 'seen')}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
              title="Mark as seen"
            >
              <Eye className="h-3.5 w-3.5" />
            </button>
          )}
          {insight.status !== 'actioned' && insight.status !== 'dismissed' && (
            <button
              onClick={() => onAction(insight.id, 'actioned')}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-success hover:bg-success/10 transition-colors"
              title="Mark as actioned"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
            </button>
          )}
          {insight.status !== 'dismissed' && (
            <button
              onClick={() => onAction(insight.id, 'dismissed')}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-warning hover:bg-warning/10 transition-colors"
              title="Dismiss"
            >
              <XCircle className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            onClick={() => onView(insight.id)}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
            title="View details"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
