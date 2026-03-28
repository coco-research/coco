import { useEffect, useRef } from 'react';

interface ActivityEvent {
  ts: string;
  description: string;
  project?: string;
}

interface ActivityFeedProps {
  events: ActivityEvent[];
}

export function ActivityFeed({ events }: ActivityFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length]);

  return (
    <div className="rounded-xl border border-border bg-card p-5 flex flex-col">
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-4">Recent Activity</p>
      <div className="max-h-96 overflow-y-auto">
        {events.length === 0 && (
          <p className="text-sm text-muted-foreground">No recent activity.</p>
        )}
        <div className="relative">
          {events.map((evt, i) => (
            <div key={i} className="flex items-start gap-4 text-sm relative pb-4 last:pb-0">
              {/* Timeline dot + connector */}
              <div className="flex flex-col items-center shrink-0">
                <div className="w-2.5 h-2.5 rounded-full bg-accent mt-1.5" />
                {i < events.length - 1 && (
                  <div className="w-px flex-1 bg-border mt-1" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <span className="text-foreground">{evt.description}</span>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="font-mono text-xs text-muted-foreground">{evt.ts}</span>
                  {evt.project && (
                    <span className="text-xs rounded-full bg-accent/20 text-accent px-2 py-0.5">
                      {evt.project}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
