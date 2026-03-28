import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { GitBranch, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { apiFetch, apiPost, apiPatch } from '../../lib/api';
import { useEventSource } from '../../lib/sse';
import { cn, timeAgo } from '../../lib/utils';
import { statePillClass, STATE_LABELS } from '../../lib/state-machine';
import { PropertiesPanel } from '../shared/PropertiesPanel';
import { PropertyField } from '../shared/PropertyField';
import { CommentThread } from '../shared/CommentThread';
import { DelegationPanel } from './DelegationPanel';
import { LogViewer } from './LogViewer';
import type { Agent } from './AgentCard';

const statusColors: Record<string, string> = {
  running: 'bg-success',
  paused: 'bg-warning',
  idle: 'bg-muted-foreground',
  completed: 'bg-info',
  failed: 'bg-destructive',
  killed: 'bg-destructive',
};

const MODEL_OPTIONS = [
  { value: 'opus', label: 'Opus' },
  { value: 'sonnet', label: 'Sonnet' },
  { value: 'haiku', label: 'Haiku' },
];

interface AgentDetailProps {
  agentId: string;
  onClose: () => void;
  onAction: () => void;
}

interface LogRow {
  id: number;
  stream: string;
  chunk: string;
  timestamp: string;
}

interface DelegationTask {
  id: string;
  title: string;
  status: string;
  priority: string;
  agent_id: string | null;
  agent_name: string | null;
  delegated_by: string | null;
  delegated_by_name: string | null;
  delegated_to: string | null;
  delegated_to_name: string | null;
  created_at: string;
}

interface AgentDelegationsData {
  delegated_by_me: DelegationTask[];
  delegated_to_me: DelegationTask[];
}

function AgentDelegations({ agentId }: { agentId: string }) {
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);

  const { data, isLoading } = useQuery<AgentDelegationsData>({
    queryKey: ['agent-delegations', agentId],
    queryFn: () => apiFetch(`/agents/${agentId}/delegations`),
    refetchInterval: 10000,
  });

  if (isLoading) return null;

  const byMe = data?.delegated_by_me ?? [];
  const toMe = data?.delegated_to_me ?? [];

  if (byMe.length === 0 && toMe.length === 0) return null;

  return (
    <div className="border-t border-border pt-4 space-y-4">
      <div className="flex items-center gap-2">
        <GitBranch size={14} className="text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Delegations
        </span>
        <span className="ml-auto text-[10px] text-muted-foreground">
          {byMe.length + toMe.length} total
        </span>
      </div>

      {/* Delegated BY this agent */}
      {byMe.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <ArrowUpRight size={12} className="text-blue-400" />
            <span>Delegated to others ({byMe.length})</span>
          </div>
          {byMe.map((task) => (
            <div key={task.id} className="space-y-0">
              <button
                onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
                className="w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
              >
                <span className="flex-1 text-sm text-foreground truncate">{task.title}</span>
                <span className={cn(
                  'inline-block px-1.5 py-0.5 rounded-full text-[10px] font-medium capitalize shrink-0',
                  statePillClass(task.status),
                )}>
                  {STATE_LABELS[task.status] ?? task.status.replace('_', ' ')}
                </span>
                <span className="text-[10px] text-muted-foreground shrink-0">
                  to {task.delegated_to_name ?? 'unknown'}
                </span>
              </button>
              {expandedTaskId === task.id && (
                <div className="ml-3 pl-3 border-l border-border">
                  <DelegationPanel
                    taskId={task.id}
                    taskTitle={task.title}
                    currentAgentId={task.agent_id}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Delegated TO this agent */}
      {toMe.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <ArrowDownRight size={12} className="text-emerald-400" />
            <span>Received from others ({toMe.length})</span>
          </div>
          {toMe.map((task) => (
            <div key={task.id} className="space-y-0">
              <button
                onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
                className="w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
              >
                <span className="flex-1 text-sm text-foreground truncate">{task.title}</span>
                <span className={cn(
                  'inline-block px-1.5 py-0.5 rounded-full text-[10px] font-medium capitalize shrink-0',
                  statePillClass(task.status),
                )}>
                  {STATE_LABELS[task.status] ?? task.status.replace('_', ' ')}
                </span>
                <span className="text-[10px] text-muted-foreground shrink-0">
                  from {task.delegated_by_name ?? 'unknown'}
                </span>
              </button>
              {expandedTaskId === task.id && (
                <div className="ml-3 pl-3 border-l border-border">
                  <DelegationPanel
                    taskId={task.id}
                    taskTitle={task.title}
                    currentAgentId={task.agent_id}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function AgentDetail({ agentId, onClose, onAction }: AgentDetailProps) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [sseConnected, setSSEConnected] = useState(false);

  const fetchAgent = useCallback(async () => {
    try {
      const data = await apiFetch<Agent>(`/agents/${agentId}`);
      setAgent(data);
    } catch {
      // ignore
    }
  }, [agentId]);

  // Initial load: fetch agent + initial logs
  useEffect(() => {
    fetchAgent();
    apiFetch<LogRow[]>(`/agents/${agentId}/logs?after_id=0&limit=200`)
      .then((rows) => {
        if (rows.length > 0) {
          setLogs(rows.map((r) => r.chunk));
        }
      })
      .catch(() => {});
  }, [agentId, fetchAgent]);

  // SSE for live log streaming — replaces the 2s polling interval
  const sseStatus = useEventSource(`/api/events/agents/${agentId}`, {
    events: {
      output: (data: unknown) => {
        const row = data as LogRow;
        if (row.chunk) {
          setLogs((prev) => [...prev, row.chunk]);
        }
      },
      status: (data: unknown) => {
        const payload = data as { status: string };
        if (payload.status) {
          // Agent finished — refresh the full agent record
          fetchAgent();
          onAction();
        }
      },
    },
  });

  // Track SSE connection status
  useEffect(() => {
    setSSEConnected(sseStatus === 'connected');
  }, [sseStatus]);

  // Fallback: poll only if SSE is not connected and agent is in an active state
  useEffect(() => {
    if (sseConnected) return;
    if (agent && ['completed', 'failed', 'killed', 'idle'].includes(agent.status)) return;

    const interval = setInterval(() => {
      fetchAgent();
    }, 4000);
    return () => clearInterval(interval);
  }, [sseConnected, agent, fetchAgent]);

  const handleAction = async (action: string) => {
    try {
      await apiPost(`/agents/${agentId}/${action}`, {});
      await fetchAgent();
      onAction();
    } catch {
      // ignore
    }
  };

  const handleSave = async (field: string, value: string) => {
    try {
      await apiPatch(`/agents/${agentId}`, { [field]: value });
      await fetchAgent();
    } catch {
      // ignore
    }
  };

  return (
    <PropertiesPanel
      open={!!agentId}
      onClose={onClose}
      title={agent?.name ?? 'Loading...'}
      subtitle={agent ? `${agent.status} ${agent.pid ? `\u00b7 PID ${agent.pid}` : ''}` : undefined}
      width="lg"
    >
      {!agent ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : (
        <>
          {/* Properties */}
          <div className="space-y-0">
            <PropertyField
              label="Name"
              value={agent.name}
              onSave={(v) => handleSave('name', v)}
            />
            <div className="mb-3">
              <span className="block text-xs text-muted-foreground mb-0.5">Status</span>
              <span className="flex items-center gap-2 text-sm text-foreground">
                <span className={cn('inline-block w-2 h-2 rounded-full', statusColors[agent.status] || 'bg-muted-foreground')} />
                <span className="capitalize">{agent.status}</span>
              </span>
            </div>
            {agent.role && (
              <div className="mb-3">
                <span className="block text-xs text-muted-foreground mb-0.5">Role</span>
                <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-accent/20 text-accent capitalize">
                  {agent.role}
                </span>
              </div>
            )}
            <PropertyField
              label="Model"
              value={agent.model}
              onSave={(v) => handleSave('model', v)}
              type="select"
              options={MODEL_OPTIONS}
            />
            <PropertyField
              label="Task description"
              value={agent.task_description}
              onSave={(v) => handleSave('task_description', v)}
              type="textarea"
              placeholder="Describe what this agent should do..."
            />
            <PropertyField
              label="System prompt"
              value={agent.system_prompt}
              onSave={(v) => handleSave('system_prompt', v)}
              type="textarea"
              placeholder="System prompt..."
            />
            <PropertyField label="Working directory" value={agent.working_directory} />
            <PropertyField label="Created" value={agent.created_at ? timeAgo(agent.created_at) : null} />
            {agent.started_at && (
              <PropertyField label="Started" value={timeAgo(agent.started_at)} />
            )}
            {agent.last_heartbeat && (
              <PropertyField label="Last heartbeat" value={timeAgo(agent.last_heartbeat)} />
            )}
            {agent.exit_code !== null && agent.exit_code !== undefined && (
              <PropertyField label="Exit code" value={agent.exit_code} />
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 mt-4 mb-4 border-t border-border pt-4">
            {agent.status === 'running' && (
              <>
                <button
                  onClick={() => handleAction('pause')}
                  className="px-3 py-1.5 text-xs rounded-lg bg-warning/20 text-warning hover:bg-warning/30 transition-all"
                >
                  Pause
                </button>
                <button
                  onClick={() => handleAction('kill')}
                  className="px-3 py-1.5 text-xs rounded-lg bg-destructive/20 text-destructive hover:bg-destructive/30 transition-all"
                >
                  Kill
                </button>
              </>
            )}
            {agent.status === 'paused' && (
              <>
                <button
                  onClick={() => handleAction('resume')}
                  className="px-3 py-1.5 text-xs rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all"
                >
                  Resume
                </button>
                <button
                  onClick={() => handleAction('kill')}
                  className="px-3 py-1.5 text-xs rounded-lg bg-destructive/20 text-destructive hover:bg-destructive/30 transition-all"
                >
                  Kill
                </button>
              </>
            )}
            {(agent.status === 'idle' || agent.status === 'completed' || agent.status === 'failed' || agent.status === 'killed') && (
              <button
                onClick={() => handleAction('spawn')}
                className="px-3 py-1.5 text-xs rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all"
              >
                {agent.status === 'idle' ? 'Spawn' : 'Respawn'}
              </button>
            )}
          </div>

          {/* Delegations section */}
          <AgentDelegations agentId={agentId} />

          {/* Log viewer */}
          <div className="border-t border-border pt-4">
            <span className="block text-xs text-muted-foreground mb-2">Logs</span>
            <div className="h-64 overflow-hidden">
              <LogViewer logs={logs} />
            </div>
          </div>

          {/* Comments */}
          <div className="mt-4">
            <CommentThread entityType="agent" entityId={agentId} />
          </div>
        </>
      )}
    </PropertiesPanel>
  );
}
