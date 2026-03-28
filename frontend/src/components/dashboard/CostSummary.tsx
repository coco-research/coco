import { formatCost } from '../../lib/utils';

interface CostSummaryProps {
  today_usd: number;
  month_usd: number;
  daily?: number[];
}

export function CostSummary({ today_usd, month_usd, daily }: CostSummaryProps) {
  const days = daily ?? [];
  const maxVal = Math.max(...days, 0.01);

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">Costs</p>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Today</span>
          <span className="text-foreground font-medium">{formatCost(today_usd)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">This month</span>
          <span className="text-foreground font-medium">{formatCost(month_usd)}</span>
        </div>
      </div>

      {days.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-2">Last {days.length} days</p>
          <div className="flex items-end gap-1 h-12">
            {days.map((val, i) => (
              <div
                key={i}
                className="flex-1 bg-accent/40 rounded-t hover:bg-accent/60 transition-colors"
                style={{ height: `${Math.max((val / maxVal) * 100, 4)}%` }}
                title={formatCost(val)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
