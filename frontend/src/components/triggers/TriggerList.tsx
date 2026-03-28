import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPost, apiDelete, apiPatch } from '../../lib/api';
import { Clock, Webhook, FolderSearch, Trash2, Play, AlertCircle, Loader2, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface TriggerLogEntry {
  id?: number;
  trigger_id?: string;
  status: 'success' | 'failed' | 'skipped';
  result?: string;
  error?: string;
  message?: string;
  fired_at: string;
}

export interface Trigger {
  id: string;
  name: string;
  trigger_type: 'cron' | 'webhook' | 'file_watch';
  enabled: boolean;
  config: Record<string, unknown>;
  action_type: 'spawn_agent' | 'create_todo' | 'notify' | 'run_command';
  action_config: Record<string, unknown>;
  node_id?: string | null;
  last_fired_at: string | null;
  fire_count: number;
  last_log?: TriggerLogEntry | null;
  recent_logs?: TriggerLogEntry[];
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

function WebhookUrlDisplay({ triggerId }: { triggerId: string }) {
  const [copied, setCopied] = useState(false);
  const url = `${window.location.origin}/api/webhooks/${triggerId}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 ml-4">
      <code className="text-[10px] text-muted-foreground font-mono bg-muted px-2 py-0.5 rounded truncate max-w-xs">
        POST {url}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
        aria-label="Copy webhook URL"
      >
        {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
      </button>
    </div>
  );
}

function TriggerLogPanel({ triggerId }: { triggerId: string }) {
  const { data, isLoading } = useQuery<{ items: TriggerLogEntry[]; total: number }>({
    queryKey: ['trigger-logs', triggerId],
    queryFn: () => apiFetch(`/triggers/${triggerId}/logs?limit=10`),
    staleTime: 10_000,
  });

  if (isLoading) return <p className="text-[10px] text-muted-foreground px-3 py-1 ml-4">Loading logs...</p>;

  const logs = data?.items ?? [];
  if (logs.length === 0) return <p className="text-[10px] text-muted-foreground px-3 py-1 ml-4">No fire history yet.</p>;

  return (
    <div className="ml-4 mr-2 mb-1 border border-border rounded-md overflow-hidden">
      <table className="w-full text-[10px]">
        <thead>
          <tr className="bg-muted/50">
            <th className="text-left px-2 py-1 font-medium text-muted-foreground">Time</th>
            <th className="text-left px-2 py-1 font-medium text-muted-foreground">Status</th>
            <th className="text-left px-2 py-1 font-medium text-muted-foreground">Result</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((entry, i) => (
            <tr key={entry.id ?? i} className="border-t border-border/50">
              <td className="px-2 py-1 text-muted-foreground whitespace-nowrap">
                {new Date(entry.fired_at).toLocaleString()}
              </td>
              <td className="px-2 py-1">
                <span className={cn(
                  'px-1 py-0.5 rounded font-semibold',
                  entry.status === 'success' ? 'text-emerald-400 bg-emerald-500/10' :
                  entry.status === 'failed' ? 'text-red-400 bg-red-500/10' :
                  'text-yellow-400 bg-yellow-500/10',
                )}>
                  {entry.status}
                </span>
              </td>
              <td className="px-2 py-1 text-muted-foreground truncate max-w-[200px]">
                {entry.error || entry.result || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TriggerList({ onEdit }: TriggerListProps) {
  const queryClient = useQueryClient();
  const [testResults, setTestResults] = useState<Record<string, { status: 'loading' | 'success' | 'error'; message?: string }>>({});
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({});

  const { data: triggers = [], isLoading } = useQuery<Trigger[]>({
    queryKey: ['triggers'],
    queryFn: () => apiFetch<Trigger[]>('/triggers'),
    refetchInterval: 30_000, // Auto-refresh every 30s to show latest fire counts
  });

  const toggleMut = useMutation({
    mutationFn: (t: Trigger) =>
      apiPatch<Trigger>(`/triggers/${t.id}`, { enabled: !t.enabled }),
    onMutate: async (t) => {
      await queryClient.cancelQueries({ queryKey: ['triggers'] });
      const previous = queryClient.getQueryData<Trigger[]>(['triggers']);
      queryClient.setQueryData<Trigger[]>(['triggers'], (old) =>
        old?.map((tr) => (tr.id === t.id ? { ...tr, enabled: !tr.enabled } : tr)) ?? [],
      );
      return { previous };
    },
    onError: (_err, _t, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['triggers'], context.previous);
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['triggers'] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => apiDelete(`/triggers/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['triggers'] }),
  });

  const handleTest = async (triggerId: string) => {
    setTestResults((prev) => ({ ...prev, [triggerId]: { status: 'loading' } }));
    try {
      const result = await apiPost<{ status: string; result?: string; error?: string }>(`/triggers/${triggerId}/test`, {});
      setTestResults((prev) => ({
        ...prev,
        [triggerId]: { status: result.status === 'failed' ? 'error' : 'success', message: result.result ?? result.error ?? 'Done' },
      }));
      // Refresh trigger list and logs
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
      queryClient.invalidateQueries({ queryKey: ['trigger-logs', triggerId] });
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [triggerId]: { status: 'error', message: err instanceof Error ? err.message : 'Test failed' },
      }));
    }
    setTimeout(() => {
      setTestResults((prev) => {
        const next = { ...prev };
        delete next[triggerId];
        return next;
      });
    }, 5000);
  };

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
        const lastLogFailed = trigger.last_log?.status === 'failed';
        const testResult = testResults[trigger.id];
        const logsExpanded = expandedLogs[trigger.id];

        // Config summary for subtitle
        const configSummary = trigger.trigger_type === 'cron'
          ? `cron: ${(trigger.config as Record<string, string>).expression || (trigger.config as Record<string, string>).cron || '?'}`
          : trigger.trigger_type === 'file_watch'
            ? `watching: ${(trigger.config as Record<string, string>).path || '?'}`
            : 'webhook';

        return (
          <div key={trigger.id} className="space-y-0">
            <div
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg border bg-card hover:bg-accent/30 transition-colors',
                lastLogFailed ? 'border-red-500/40' : 'border-border',
              )}
            >
              {/* Expand/collapse logs */}
              <button
                type="button"
                onClick={() => setExpandedLogs((prev) => ({ ...prev, [trigger.id]: !prev[trigger.id] }))}
                className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
                aria-label={logsExpanded ? 'Collapse logs' : 'Expand logs'}
              >
                {logsExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>

              {/* Icon + name */}
              <button
                type="button"
                onClick={() => onEdit?.(trigger)}
                className="flex items-center gap-3 flex-1 min-w-0 text-left"
              >
                <div className="relative shrink-0">
                  <Icon size={16} className="text-muted-foreground" />
                  {lastLogFailed && (
                    <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-card" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground truncate">
                    {trigger.name}
                  </p>
                  <p className="text-[10px] text-muted-foreground truncate">
                    {configSummary}
                    {' — '}
                    {trigger.last_fired_at
                      ? `Last fired ${new Date(trigger.last_fired_at).toLocaleString()} (${trigger.fire_count}x)`
                      : 'Never fired'}
                  </p>
                </div>
              </button>

              {/* Action badge */}
              <span className="text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded whitespace-nowrap">
                {trigger.action_type.replace('_', ' ')}
              </span>

              {/* Type badge */}
              <span
                className={cn(
                  'text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded',
                  typeBadgeColors[trigger.trigger_type],
                )}
              >
                {trigger.trigger_type.replace('_', ' ')}
              </span>

              {/* Test button */}
              <button
                type="button"
                onClick={() => handleTest(trigger.id)}
                disabled={testResult?.status === 'loading'}
                className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded-md bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground transition-colors shrink-0 disabled:opacity-50"
                aria-label="Test trigger"
              >
                {testResult?.status === 'loading' ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <Play size={12} />
                )}
                Test
              </button>

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

            {/* Webhook URL display */}
            {trigger.trigger_type === 'webhook' && logsExpanded && (
              <WebhookUrlDisplay triggerId={trigger.id} />
            )}

            {/* Error message from last failed log */}
            {lastLogFailed && trigger.last_log?.message && (
              <div className="flex items-start gap-2 px-3 py-1.5 ml-4 text-xs text-red-400">
                <AlertCircle size={12} className="shrink-0 mt-0.5" />
                <span>{trigger.last_log.message}</span>
              </div>
            )}

            {/* Inline test result */}
            {testResult && testResult.status !== 'loading' && (
              <div
                className={cn(
                  'flex items-start gap-2 px-3 py-1.5 ml-4 text-xs',
                  testResult.status === 'success' ? 'text-emerald-400' : 'text-red-400',
                )}
              >
                {testResult.status === 'success' ? (
                  <span className="shrink-0">&#10003;</span>
                ) : (
                  <AlertCircle size={12} className="shrink-0 mt-0.5" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}

            {/* Expandable log history */}
            {logsExpanded && <TriggerLogPanel triggerId={trigger.id} />}
          </div>
        );
      })}
    </div>
  );
}
