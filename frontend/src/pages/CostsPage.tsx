import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, DollarSign } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { SpendChart } from '../components/costs/SpendChart';
import { ModelBreakdown } from '../components/costs/ModelBreakdown';
import { ProjectBreakdown } from '../components/costs/ProjectBreakdown';
import { BudgetBar } from '../components/costs/BudgetBar';
import { CostEventsTable } from '../components/costs/CostEventsTable';
import { EmptyState } from '../components/shared/EmptyState';
import { ErrorState } from '../components/shared/ErrorState';

interface CostSummary {
  total_usd: number;
  daily_avg: number;
  by_model: Record<string, number>;
  by_project: Record<string, number>;
  daily?: { date: string; cost_usd: number }[];
}

interface Budget {
  project_id: string;
  monthly_cap_usd: number;
  alert_threshold_pct: number;
}

type Period = 7 | 30 | 90;

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <p className="text-sm text-muted-foreground mb-1">{label}</p>
      <p className="text-2xl font-mono text-foreground">{value}</p>
    </div>
  );
}

function CostsSkeleton() {
  const pulse = 'animate-pulse rounded-xl bg-muted/50';
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className={`${pulse} h-20`} />
        <div className={`${pulse} h-20`} />
        <div className={`${pulse} h-20`} />
      </div>
      <div className={`${pulse} h-72`} />
      <div className="grid grid-cols-2 gap-4">
        <div className={`${pulse} h-56`} />
        <div className={`${pulse} h-56`} />
      </div>
    </div>
  );
}

export default function CostsPage() {
  const [days, setDays] = useState<Period>(30);
  const [eventsOpen, setEventsOpen] = useState(false);

  const { data: summary, isLoading, isError, error, refetch } = useQuery<CostSummary>({
    queryKey: ['costs-summary', days],
    queryFn: () => apiFetch<CostSummary>(`/costs/summary?days=${days}`),
    refetchInterval: 60000,
  });

  const { data: budgets } = useQuery<Budget[]>({
    queryKey: ['budgets'],
    queryFn: () => apiFetch<Budget[]>('/budgets'),
  });

  if (isLoading) return <CostsSkeleton />;
  if (isError) {
    return (
      <ErrorState
        error={error}
        title="Couldn't load cost data"
        onRetry={() => void refetch()}
      />
    );
  }
  if (!summary) {
    return (
      <EmptyState
        icon={<DollarSign className="h-10 w-10" />}
        title="No cost data yet"
        description="Spend will appear here once agents start consuming credits."
      />
    );
  }
  const noSpend = summary.total_usd === 0 && (summary.daily ?? []).length === 0;

  const projectedMonthly = summary.daily_avg * 30;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Costs &amp; Budget</h1>

        {/* Period selector */}
        <div className="flex rounded-lg border border-border overflow-hidden">
          {([7, 30, 90] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setDays(p)}
              className={cn(
                'px-3 py-1.5 text-sm transition-all',
                days === p
                  ? 'bg-accent text-accent-foreground'
                  : 'bg-card text-muted-foreground hover:text-foreground hover:bg-accent/50',
              )}
            >
              {p}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <SummaryCard label="Total Spend (this period)" value={`$${summary.total_usd.toFixed(2)}`} />
        <SummaryCard label="Daily Average" value={`$${summary.daily_avg.toFixed(2)}`} />
        <SummaryCard label="Projected Monthly" value={`$${projectedMonthly.toFixed(2)}`} />
      </div>

      {/* Spend chart — full width (or empty hint) */}
      {noSpend ? (
        <EmptyState
          icon={<DollarSign className="h-10 w-10" />}
          title="No spend in this window"
          description="Try a longer period, or wait for agents to consume credits."
        />
      ) : (
        <SpendChart data={summary.daily ?? []} />
      )}

      {/* Model + Project breakdowns side by side */}
      <div className="grid grid-cols-2 gap-4">
        <ModelBreakdown data={summary.by_model} />
        <ProjectBreakdown data={summary.by_project} />
      </div>

      {/* Budgets section */}
      {budgets && budgets.length > 0 && (
        <section>
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Budgets
          </h2>
          <div className="space-y-3">
            {budgets.map((b) => {
              const spent = summary.by_project[b.project_id] ?? 0;
              return (
                <BudgetBar
                  key={b.project_id}
                  project_name={b.project_id}
                  spent_usd={spent}
                  cap_usd={b.monthly_cap_usd}
                />
              );
            })}
          </div>
        </section>
      )}

      {/* Collapsible cost events */}
      <section>
        <button
          onClick={() => setEventsOpen((o) => !o)}
          className="flex items-center gap-2 text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3 hover:text-foreground transition-colors"
        >
          {eventsOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          Recent Cost Events
        </button>
        {eventsOpen && <CostEventsTable />}
      </section>
    </div>
  );
}
