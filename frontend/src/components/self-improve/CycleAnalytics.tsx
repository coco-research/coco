import { useState, useMemo } from 'react';
import { BarChart3 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { formatCost } from '../../lib/utils';

// ------------- Types -----------------

export interface AnalyticsItem {
  id: string;
  started_at: string | null;
  files_changed: number;
  cost: number;
  duration_seconds: number;
  improvements_count: number;
  status: string;
}

type DateRange = 7 | 30 | 90;
type MetricKey = 'files_changed' | 'cost' | 'duration_seconds';

const METRIC_OPTIONS: { key: MetricKey; label: string }[] = [
  { key: 'files_changed', label: 'Files Changed' },
  { key: 'cost', label: 'Cost' },
  { key: 'duration_seconds', label: 'Duration' },
];

const DATE_RANGES: { value: DateRange; label: string }[] = [
  { value: 7, label: '7d' },
  { value: 30, label: '30d' },
  { value: 90, label: '90d' },
];

// ------------- Helpers -----------------

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

function formatMetricValue(key: MetricKey, value: number): string {
  if (key === 'cost') return formatCost(value);
  if (key === 'duration_seconds') return formatDuration(value);
  return String(value);
}

function statusColor(status: string): string {
  if (status === 'completed') return 'bg-green-500';
  if (status === 'failed') return 'bg-red-500';
  if (status === 'rejected') return 'bg-red-400';
  return 'bg-zinc-500';
}

// ------------- Component -----------------

interface CycleAnalyticsProps {
  data: AnalyticsItem[];
  isLoading: boolean;
  dateRange: DateRange;
  onDateRangeChange: (range: DateRange) => void;
  onCycleClick?: (cycleId: string) => void;
}

export function CycleAnalytics({
  data,
  isLoading,
  dateRange,
  onDateRangeChange,
  onCycleClick,
}: CycleAnalyticsProps) {
  const [metric, setMetric] = useState<MetricKey>('files_changed');
  const [hoveredBar, setHoveredBar] = useState<string | null>(null);

  const maxValue = useMemo(() => {
    if (data.length === 0) return 1;
    return Math.max(...data.map((d) => d[metric]), 1);
  }, [data, metric]);

  // Summary stats
  const summary = useMemo(() => {
    const total = data.length;
    const totalCost = data.reduce((s, d) => s + d.cost, 0);
    const totalFiles = data.reduce((s, d) => s + d.files_changed, 0);
    const totalImprovements = data.reduce((s, d) => s + d.improvements_count, 0);
    return { total, totalCost, totalFiles, totalImprovements };
  }, [data]);

  return (
    <div className="bg-card rounded-xl border border-border p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <BarChart3 size={16} className="text-accent" />
          <span className="text-sm font-semibold text-foreground">Cycle Analytics</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Metric selector */}
          <div className="flex items-center bg-muted/50 rounded-lg p-0.5">
            {METRIC_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => setMetric(opt.key)}
                className={cn(
                  'px-2 py-1 rounded-md text-[10px] transition-colors',
                  metric === opt.key
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
          {/* Date range */}
          <div className="flex items-center bg-muted/50 rounded-lg p-0.5">
            {DATE_RANGES.map((opt) => (
              <button
                key={opt.value}
                onClick={() => onDateRangeChange(opt.value)}
                className={cn(
                  'px-2 py-1 rounded-md text-[10px] transition-colors',
                  dateRange === opt.value
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary row */}
      <div className="flex gap-4 text-xs">
        <div>
          <span className="text-muted-foreground">Cycles:</span>{' '}
          <span className="text-foreground font-medium">{summary.total}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Total Cost:</span>{' '}
          <span className="text-foreground font-medium">{formatCost(summary.totalCost)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Files:</span>{' '}
          <span className="text-foreground font-medium">{summary.totalFiles}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Improvements:</span>{' '}
          <span className="text-foreground font-medium">{summary.totalImprovements}</span>
        </div>
      </div>

      {/* Bar chart */}
      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="h-5 w-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center h-32 text-xs text-muted-foreground">
          No cycles in the selected period
        </div>
      ) : (
        <div className="relative">
          {/* Chart area */}
          <div className="flex items-end gap-1.5 h-32">
            {data.map((item) => {
              const value = item[metric];
              const heightPct = Math.max((value / maxValue) * 100, 4); // min 4% for visibility
              const isHovered = hoveredBar === item.id;
              const date = item.started_at
                ? new Date(item.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                : '?';

              return (
                <div
                  key={item.id}
                  className="flex-1 flex flex-col items-center gap-1 min-w-[24px] relative group"
                  onMouseEnter={() => setHoveredBar(item.id)}
                  onMouseLeave={() => setHoveredBar(null)}
                  onClick={() => onCycleClick?.(item.id)}
                >
                  {/* Tooltip */}
                  {isHovered && (
                    <div className="absolute bottom-full mb-2 bg-popover border border-border rounded-lg p-2 shadow-lg z-10 min-w-[140px] text-[10px] space-y-1 pointer-events-none">
                      <div className="font-medium text-foreground">{date}</div>
                      <div className="text-muted-foreground">
                        Files: {item.files_changed} | Cost: {formatCost(item.cost)}
                      </div>
                      <div className="text-muted-foreground">
                        Duration: {formatDuration(item.duration_seconds)} | {item.improvements_count} improvements
                      </div>
                      <div className="text-muted-foreground capitalize">Status: {item.status}</div>
                    </div>
                  )}

                  {/* Bar */}
                  <div
                    className={cn(
                      'w-full rounded-t-sm transition-all duration-200 cursor-pointer',
                      statusColor(item.status),
                      isHovered ? 'opacity-100' : 'opacity-70',
                    )}
                    style={{ height: `${heightPct}%` }}
                  />
                </div>
              );
            })}
          </div>

          {/* X-axis labels (show a subset to avoid clutter) */}
          <div className="flex gap-1.5 mt-1">
            {data.map((item, idx) => {
              // Show label every N bars depending on data length
              const step = Math.max(1, Math.ceil(data.length / 8));
              if (idx % step !== 0 && idx !== data.length - 1) {
                return <div key={item.id} className="flex-1" />;
              }
              const date = item.started_at
                ? new Date(item.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                : '';
              return (
                <div key={item.id} className="flex-1 text-center text-[9px] text-muted-foreground truncate">
                  {date}
                </div>
              );
            })}
          </div>

          {/* Y-axis max label */}
          <div className="absolute top-0 right-0 text-[9px] text-muted-foreground">
            {formatMetricValue(metric, maxValue)}
          </div>
        </div>
      )}
    </div>
  );
}
