import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Calendar, Flag, Rocket, Users, Mail, Phone } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';
import type { BrainEvent } from '../../types/brain';
import { ErrorState } from '../shared/ErrorState';

interface BrainEventTimelineProps {
  search?: string;
}

interface EventsResponse {
  items: BrainEvent[];
  total: number;
}

const LIMIT = 20;

// ---------------------------------------------------------------------------
// Event type config
// ---------------------------------------------------------------------------

const EVENT_TYPES = [
  { value: 'milestone', label: 'Milestone', icon: Flag, color: 'text-amber-400', bg: 'bg-amber-500/15' },
  { value: 'deploy', label: 'Deploy', icon: Rocket, color: 'text-green-400', bg: 'bg-green-500/15' },
  { value: 'meeting', label: 'Meeting', icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/15' },
  { value: 'email', label: 'Email', icon: Mail, color: 'text-purple-400', bg: 'bg-purple-500/15' },
  { value: 'call', label: 'Call', icon: Phone, color: 'text-cyan-400', bg: 'bg-cyan-500/15' },
] as const;

const TYPE_MAP = new Map(EVENT_TYPES.map((t) => [t.value, t]));

function getEventType(type: string) {
  return TYPE_MAP.get(type as never) ?? { value: type, label: type, icon: Calendar, color: 'text-muted-foreground', bg: 'bg-muted/20' };
}

// ---------------------------------------------------------------------------
// Date grouping
// ---------------------------------------------------------------------------

function dateLabel(dateStr: string): string {
  const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T') + 'Z');
  if (isNaN(d.getTime())) return 'Unknown';
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  if (target.getTime() === today.getTime()) return 'Today';
  if (target.getTime() === yesterday.getTime()) return 'Yesterday';
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function groupByDate(items: BrainEvent[]): Map<string, BrainEvent[]> {
  const groups = new Map<string, BrainEvent[]>();
  for (const item of items) {
    const label = dateLabel(item.date);
    const existing = groups.get(label);
    if (existing) {
      existing.push(item);
    } else {
      groups.set(label, [item]);
    }
  }
  return groups;
}

// ---------------------------------------------------------------------------
// Initials badge
// ---------------------------------------------------------------------------

function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BrainEventTimeline({ search }: BrainEventTimelineProps) {
  const [typeFilter, setTypeFilter] = useState('');
  const [offset, setOffset] = useState(0);

  const params = new URLSearchParams();
  if (typeFilter) params.set('type', typeFilter);
  params.set('limit', String(LIMIT));
  params.set('offset', String(offset));

  const { data, isLoading, isError, error, refetch } = useQuery<EventsResponse>({
    queryKey: ['brain-events', typeFilter, offset, search],
    queryFn: () => apiFetch<EventsResponse>(`/brain/events?${params.toString()}`),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const page = Math.floor(offset / LIMIT) + 1;
  const totalPages = Math.ceil(total / LIMIT);

  const grouped = useMemo(() => groupByDate(items), [items]);

  return (
    <div className="flex flex-col h-full">
      {/* Type filter pills */}
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] text-muted-foreground mr-1">Type:</span>
          {EVENT_TYPES.map((t) => {
            const Icon = t.icon;
            const active = typeFilter === t.value;
            return (
              <button
                key={t.value}
                aria-pressed={active}
                onClick={() => {
                  setTypeFilter(active ? '' : t.value);
                  setOffset(0);
                }}
                className={cn(
                  'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium transition-colors',
                  active ? t.bg + ' ' + t.color : 'bg-transparent text-muted-foreground/60 hover:text-muted-foreground',
                )}
              >
                <Icon className="h-3 w-3" />
                {t.label}
              </button>
            );
          })}
        </div>
        <div className="mt-1.5 text-xs text-muted-foreground">
          {total.toLocaleString()} event{total !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Event list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-20 text-muted-foreground text-sm gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading events...
          </div>
        ) : isError ? (
          <div className="p-6">
            <ErrorState
              error={error}
              title="Couldn't load events"
              onRetry={() => void refetch()}
            />
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-3">
            <Calendar className="h-8 w-8" />
            <p>No events found</p>
            <p className="text-xs">
              {typeFilter ? 'Try clearing the type filter.' : 'The brain has not recorded any events yet.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {Array.from(grouped.entries()).map(([label, events]) => (
              <div key={label}>
                {/* Date group header */}
                <div className="px-4 py-2 bg-card/60 sticky top-0 z-10">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
                    {label}
                  </span>
                </div>
                {/* Event rows */}
                {events.map((event) => {
                  const typeInfo = getEventType(event.type);
                  const Icon = typeInfo.icon;
                  const participants: string[] = Array.isArray(event.participants_json)
                    ? (event.participants_json as string[])
                    : [];
                  return (
                    <div
                      key={event.id}
                      className="px-4 py-3 hover:bg-accent/5 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        {/* Type icon */}
                        <div className={cn('mt-0.5 p-1.5 rounded-lg shrink-0', typeInfo.bg)}>
                          <Icon className={cn('h-3.5 w-3.5', typeInfo.color)} />
                        </div>

                        {/* Main content */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground">{event.title}</p>
                          {event.summary && (
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                              {event.summary}
                            </p>
                          )}
                          {event.source && (
                            <span className="text-[10px] text-muted-foreground/60 mt-1 inline-block">
                              {event.source}
                            </span>
                          )}
                        </div>

                        {/* Participant badges */}
                        {participants.length > 0 && (
                          <div className="flex items-center gap-1 shrink-0">
                            {participants.slice(0, 4).map((name, i) => (
                              <span
                                key={i}
                                title={name}
                                className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-accent/10 text-accent text-[10px] font-semibold"
                              >
                                {initialsOf(name)}
                              </span>
                            ))}
                            {participants.length > 4 && (
                              <span className="text-[10px] text-muted-foreground ml-0.5">
                                +{participants.length - 4}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > LIMIT && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm text-muted-foreground">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
                offset === 0 ? 'opacity-40 cursor-not-allowed' : 'hover:bg-accent/50 text-foreground',
              )}
            >
              Previous
            </button>
            <button
              disabled={offset + LIMIT >= total}
              onClick={() => setOffset(offset + LIMIT)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
                offset + LIMIT >= total
                  ? 'opacity-40 cursor-not-allowed'
                  : 'hover:bg-accent/50 text-foreground',
              )}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
