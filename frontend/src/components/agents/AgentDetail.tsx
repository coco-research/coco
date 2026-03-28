import { useState, useEffect, useCallback } from 'react';
import { apiFetch, apiPost, apiPatch } from '../../lib/api';
import { useEventSource } from '../../lib/sse';
import { cn, timeAgo } from '../../lib/utils';
import { PropertiesPanel } from '../shared/PropertiesPanel';
import { PropertyField } from '../shared/PropertyField';
import { CommentThread } from '../shared/CommentThread';
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
