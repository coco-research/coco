import { cn } from '../../lib/utils';

interface BudgetBarProps {
  project_name: string;
  spent_usd: number;
  cap_usd: number;
}

export function BudgetBar({ project_name, spent_usd, cap_usd }: BudgetBarProps) {
  const pct = cap_usd > 0 ? (spent_usd / cap_usd) * 100 : 0;
  const clampedPct = Math.min(pct, 100);

  const barColor =
    pct >= 100 ? 'bg-red-500' : pct >= 80 ? 'bg-yellow-500' : 'bg-accent';

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-foreground">{project_name}</span>
        <span className="text-sm text-muted-foreground font-mono">
          ${spent_usd.toFixed(2)} / ${cap_usd.toFixed(2)}
        </span>
      </div>

      <div className="relative h-3 bg-card rounded-full overflow-hidden">
        {/* Progress fill */}
        <div
          className={cn('absolute inset-y-0 left-0 rounded-full transition-all', barColor)}
          style={{ width: `${clampedPct}%` }}
        />
        {/* 80% threshold marker */}
        <div
          className="absolute inset-y-0 w-px bg-yellow-500/60"
          style={{ left: '80%' }}
        />
        {/* 100% threshold marker */}
        <div
          className="absolute inset-y-0 w-px bg-red-500/60"
          style={{ left: '100%' }}
        />
      </div>

      <div className="flex items-center justify-between mt-1.5">
        <span
          className={cn(
            'text-xs font-mono',
            pct >= 100
              ? 'text-red-400'
              : pct >= 80
                ? 'text-yellow-400'
                : 'text-muted-foreground',
          )}
        >
          {pct.toFixed(1)}%
        </span>
        <div className="flex gap-3 text-xs text-muted-foreground">
          <span>80%</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  );
}
