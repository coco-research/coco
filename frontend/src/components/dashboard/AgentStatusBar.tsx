import { cn } from '../../lib/utils';

interface AgentStatusBarProps {
  running: number;
  paused: number;
  idle: number;
  total: number;
}

const dotColors: Record<string, string> = {
  running: 'bg-success',
  paused: 'bg-warning',
  idle: 'bg-muted-foreground',
};

export function AgentStatusBar({ running, paused, idle, total }: AgentStatusBarProps) {
  const segments = [
    { label: 'running', count: running },
    { label: 'paused', count: paused },
    { label: 'idle', count: idle },
  ];

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">Agents</p>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-foreground font-medium">{total} agent{total !== 1 ? 's' : ''}</span>
        {segments.map(({ label, count }) =>
          count > 0 ? (
            <span key={label} className="flex items-center gap-1.5 text-muted-foreground">
              <span className={cn('inline-block w-2 h-2 rounded-full', dotColors[label], label === 'running' && 'animate-pulse-dot')} />
              {count} {label}
            </span>
          ) : null,
        )}
        {total === 0 && <span className="text-muted-foreground">No agents</span>}
      </div>
    </div>
  );
}
