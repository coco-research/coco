import React from 'react';
import { Play, SkipForward } from 'lucide-react';
import { cn, timeAgo } from '../../lib/utils';
import { ROLE_META } from '../agents/AgentCard';

export interface Handoff {
  id: string;
  node_id: string;
  from_role: string;
  to_role: string;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
}

export interface HandoffCardProps {
  handoff: Handoff;
  onLaunch: (handoff: Handoff) => void;
  onSkip: (handoff: Handoff) => void;
}

const statusBadge: Record<string, string> = {
  in_progress: 'bg-info/20 text-info',
  completed: 'bg-success/20 text-success',
  skipped: 'bg-muted text-muted-foreground',
};

export const HandoffCard = React.memo(function HandoffCard({
  handoff, onLaunch, onSkip,
}: HandoffCardProps) {
  const meta = ROLE_META[handoff.to_role] ?? ROLE_META['custom'];
  const fromMeta = ROLE_META[handoff.from_role] ?? ROLE_META['custom'];
  const Icon = meta.icon;

  return (
    <div className="flex items-center gap-4 rounded-xl border border-border bg-card p-4">
      <div className={cn('flex items-center justify-center w-10 h-10 rounded-lg shrink-0', meta.color)}>
        <Icon size={18} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground truncate">{handoff.title}</span>
          {handoff.status !== 'pending' && statusBadge[handoff.status] && (
            <span className={cn('text-[10px] px-1.5 py-0.5 rounded font-medium', statusBadge[handoff.status])}>
              {handoff.status.replace('_', ' ')}
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          From: {fromMeta.label} &middot; {timeAgo(handoff.created_at)}
        </p>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => onLaunch(handoff)}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all"
        >
          <Play size={12} /> Launch Agent
        </button>
        <button
          onClick={() => onSkip(handoff)}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg text-muted-foreground hover:bg-muted transition-all"
        >
          <SkipForward size={12} /> Skip
        </button>
      </div>
    </div>
  );
});
