import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, ChevronDown, ChevronRight, Clock, Filter } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface TimelineItem {
  date: string;
  project_slug: string;
  project_name: string;
  type: string;
  title: string;
  author: string | null;
  detail: string | null;
  status: string;
}

interface TimelineResponse {
  items: TimelineItem[];
  total: number;
  limit: number;
  offset: number;
  date_range: { from: string; to: string };
}

interface DecisionTimelineProps {
  onNavigateProject?: (slug: string) => void;
  defaultDays?: number;
}

function formatDateHeading(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (d.toDateString() === today.toDateString()) return 'Today';
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

function groupByDate(items: TimelineItem[]): Map<string, TimelineItem[]> {
  const groups = new Map<string, TimelineItem[]>();
  for (const item of items) {
    const dateKey = (item.date || '').slice(0, 10);
    const existing = groups.get(dateKey) || [];
    existing.push(item);
    groups.set(dateKey, existing);
  }
  return groups;
}

function statusDot(status: string): string {
  switch (status) {
    case 'pending': return 'bg-amber-500';
    case 'in_progress': return 'bg-blue-500';
    case 'done':
    case 'resolved': return 'bg-green-500';
    case 'recorded': return 'bg-purple-500';
    default: return 'bg-muted-foreground';
  }
}

const DAYS_OPTIONS = [
  { value: 7, label: 'This week' },
  { value: 14, label: '2 weeks' },
  { value: 30, label: 'This month' },
  { value: 90, label: '3 months' },
];

export function DecisionTimeline({ onNavigateProject, defaultDays = 14 }: DecisionTimelineProps) {
  const [days, setDays] = useState(defaultDays);
  const [expanded, setExpanded] = useState(true);

  const { data, isLoading } = useQuery({
    queryKey: ['timeline', days],
    queryFn: () => apiFetch<TimelineResponse>(`/knowledge/timeline?days=${days}&limit=100`),
    staleTime: 5 * 60 * 1000,
  });

  const groups = data ? groupByDate(data.items) : new Map();

  return (
    <div className="bg-card border border-border rounded-xl">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full px-5 py-3 text-left"
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <Clock className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
            Decision Timeline
          </h3>
          {data && (
            <span className="text-xs text-muted-foreground">
              ({data.total} item{data.total !== 1 ? 's' : ''})
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Filter className="h-3 w-3 text-muted-foreground" />
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border">
          {/* Date range filter */}
          <div className="px-5 py-2 flex items-center gap-2 border-b border-border" role="group" aria-label="Timeline filters">
            {DAYS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={(e) => { e.stopPropagation(); setDays(opt.value); }}
                className={cn(
                  'px-2.5 py-1 text-xs font-medium rounded-md transition-colors',
                  days === opt.value
                    ? 'bg-foreground text-background'
                    : 'bg-muted text-muted-foreground hover:text-foreground',
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Loading */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Empty */}
          {!isLoading && data && data.items.length === 0 && (
            <div className="px-5 py-8 text-center">
              <p className="text-sm text-muted-foreground">No decisions in this period.</p>
            </div>
          )}

          {/* Timeline entries */}
          {!isLoading && groups.size > 0 && (
            <div className="max-h-96 overflow-y-auto">
              {Array.from(groups.entries()).map(([dateKey, items]) => (
                <div key={dateKey}>
                  {/* Date heading */}
                  <div className="px-5 py-1.5 bg-muted/30 sticky top-0">
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      {formatDateHeading(dateKey)}
                    </span>
                  </div>
                  {/* Items */}
                  {items.map((item, i) => (
                    <div key={`${dateKey}-${i}`} className="px-5 py-2.5 flex items-start gap-3 hover:bg-muted/20 transition-colors">
                      {/* Timeline dot + line */}
                      <div className="flex flex-col items-center pt-1.5">
                        <span className={cn('w-2 h-2 rounded-full shrink-0', statusDot(item.status))} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-2">
                          {item.project_slug && (
                            <button
                              onClick={() => onNavigateProject?.(item.project_slug)}
                              className="text-[11px] font-mono px-1.5 py-0.5 bg-muted rounded text-muted-foreground hover:text-foreground shrink-0 transition-colors"
                            >
                              {item.project_slug.toUpperCase().slice(0, 12)}
                            </button>
                          )}
                          <p className="text-sm text-foreground">{item.title}</p>
                        </div>
                        {item.author && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            — {item.author}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
