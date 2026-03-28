import { cn } from '../../lib/utils';

interface HealthSource {
  source_name?: string;
  source?: string;
  status?: string;
  last_success?: string | null;
  last_failure?: string | null;
  last_sync?: string | null;
  items_synced?: number;
  item_count?: number;
  error_message?: string | null;
  message?: string | null;
}

interface HealthBarProps {
  sources: HealthSource[];
}

const statusColor: Record<string, string> = {
  ok: 'bg-success',
  healthy: 'bg-success',
  green: 'bg-success',
  warning: 'bg-warning',
  stale: 'bg-warning',
  yellow: 'bg-warning',
  error: 'bg-destructive',
  down: 'bg-destructive',
  red: 'bg-destructive',
  disabled: 'bg-muted-foreground',
  unknown: 'bg-muted-foreground',
};

const sourceLabels: Record<string, string> = {
  email: 'Email',
  voice: 'Voice',
  jira: 'Jira',
  confluence: 'Conf',
};

function resolveStatus(source: HealthSource): string {
  return source.status ?? 'unknown';
}

export function HealthBar({ sources }: HealthBarProps) {
  const defaults = ['email', 'voice', 'jira', 'confluence'];
  const sourceMap = new Map(sources.map((s) => [s.source_name ?? s.source ?? '', s]));

  const items = defaults.map((key) => {
    const src = sourceMap.get(key);
    const status = src ? resolveStatus(src) : 'unknown';
    const count = src?.items_synced ?? src?.item_count;
    return { key, label: sourceLabels[key] ?? key, status, itemsSynced: count };
  });

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">Source Health</p>
      <div className="flex items-center gap-5">
        {items.map(({ key, label, status, itemsSynced }) => (
          <span key={key} className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <span className={cn('inline-block w-2.5 h-2.5 rounded-full', statusColor[status] ?? 'bg-muted-foreground')} />
            {label}
            {itemsSynced !== undefined && itemsSynced > 0 && (
              <span className="text-xs text-muted-foreground">({itemsSynced})</span>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
