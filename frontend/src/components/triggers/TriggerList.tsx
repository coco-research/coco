import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiDelete, apiPatch } from '../../lib/api';
import { Clock, Webhook, FolderSearch, Trash2 } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface Trigger {
  id: string;
  name: string;
  trigger_type: 'cron' | 'webhook' | 'file_watch';
  enabled: boolean;
  config: Record<string, unknown>;
  action_type: 'spawn_agent' | 'create_todo' | 'notify' | 'run_command';
  action_config: Record<string, unknown>;
  last_fired_at: string | null;
  fire_count: number;
  created_at: string;
  updated_at: string;
}

const typeIcons: Record<Trigger['trigger_type'], typeof Clock> = {
  cron: Clock,
  webhook: Webhook,
  file_watch: FolderSearch,
};

const typeBadgeColors: Record<Trigger['trigger_type'], string> = {
  cron: 'bg-blue-500/15 text-blue-400',
  webhook: 'bg-purple-500/15 text-purple-400',
  file_watch: 'bg-amber-500/15 text-amber-400',
};

interface TriggerListProps {
  onEdit?: (trigger: Trigger) => void;
}

export function TriggerList({ onEdit }: TriggerListProps) {
  const queryClient = useQueryClient();

  const { data: triggers = [], isLoading } = useQuery<Trigger[]>({
    queryKey: ['triggers'],
    queryFn: () => apiFetch<Trigger[]>('/triggers'),
  });

  const toggleMut = useMutation({
    mutationFn: (t: Trigger) =>
      apiPatch<Trigger>(`/triggers/${t.id}`, { enabled: !t.enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['triggers'] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => apiDelete(`/triggers/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['triggers'] }),
  });

  if (isLoading) {
    return <p className="text-xs text-muted-foreground py-4">Loading triggers...</p>;
  }

  if (triggers.length === 0) {
    return (
      <p className="text-xs text-muted-foreground py-4">
        No triggers configured. Create one below.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {triggers.map((trigger) => {
        const Icon = typeIcons[trigger.trigger_type];
        return (
          <div
            key={trigger.id}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors"
          >
            {/* Icon + name */}
            <button
              type="button"
              onClick={() => onEdit?.(trigger)}
              className="flex items-center gap-3 flex-1 min-w-0 text-left"
            >
              <Icon size={16} className="text-muted-foreground shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-foreground truncate">
                  {trigger.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {trigger.last_fired_at
                    ? `Last fired ${new Date(trigger.last_fired_at).toLocaleString()} (${trigger.fire_count}x)`
                    : 'Never fired'}
                </p>
              </div>
            </button>

            {/* Type badge */}
            <span
              className={cn(
                'text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded',
                typeBadgeColors[trigger.trigger_type],
              )}
            >
              {trigger.trigger_type.replace('_', ' ')}
            </span>

            {/* Enabled toggle */}
            <button
              type="button"
              onClick={() => toggleMut.mutate(trigger)}
              className={cn(
                'relative inline-flex h-5 w-9 items-center rounded-full transition-colors shrink-0',
                trigger.enabled ? 'bg-accent' : 'bg-border',
              )}
              aria-label={trigger.enabled ? 'Disable trigger' : 'Enable trigger'}
            >
              <span
                className={cn(
                  'inline-block h-3.5 w-3.5 transform rounded-full bg-card transition-transform',
                  trigger.enabled ? 'translate-x-[18px]' : 'translate-x-0.5',
                )}
              />
            </button>

            {/* Delete */}
            <button
              type="button"
              onClick={() => deleteMut.mutate(trigger.id)}
              className="text-muted-foreground hover:text-destructive transition-colors shrink-0"
              aria-label="Delete trigger"
            >
              <Trash2 size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
