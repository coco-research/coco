/**
 * AgentTaskList — minimal per-agent inter-agent task list.
 *
 * Shows tasks delegated TO this agent, split into:
 *   - Assigned (pending + claimed) — work the agent owns right now
 *   - Done (done + failed)         — terminal history
 *
 * Backed by GAP M2's /api/agents/{id}/tasks endpoint. Polls every 5s
 * so claims and completions surface without manual refresh.
 *
 * The "Claim next" button hits POST /api/agents/{id}/tasks/next which
 * is the atomic claim path. Useful for manual smoke-testing the queue
 * before the agent-CLI SDK polling lands.
 */

import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Inbox, CheckCircle2, XCircle, Clock, PlayCircle, Loader2 } from 'lucide-react';
import { apiFetch, apiPost, apiPatch } from '../../lib/api';
import { timeAgo } from '../../lib/utils';

export interface AgentTask {
  id: string;
  from_agent_id: string | null;
  to_agent_id: string;
  prompt: string;
  status: 'pending' | 'claimed' | 'done' | 'failed';
  created_at: string;
  claimed_at: string | null;
  completed_at: string | null;
  result: string | null;
}

interface AgentTaskListProps {
  agentId: string;
}

const STATUS_ICON: Record<AgentTask['status'], React.ReactNode> = {
  pending: <Clock size={12} className="text-muted-foreground" />,
  claimed: <PlayCircle size={12} className="text-warning" />,
  done: <CheckCircle2 size={12} className="text-success" />,
  failed: <XCircle size={12} className="text-destructive" />,
};

const STATUS_LABEL: Record<AgentTask['status'], string> = {
  pending: 'Pending',
  claimed: 'Claimed',
  done: 'Done',
  failed: 'Failed',
};

export function AgentTaskList({ agentId }: AgentTaskListProps) {
  const qc = useQueryClient();
  const [claiming, setClaiming] = useState(false);

  const { data: tasks = [], isLoading } = useQuery<AgentTask[]>({
    queryKey: ['agent-tasks', agentId],
    queryFn: () => apiFetch(`/agents/${agentId}/tasks?limit=20`),
    refetchInterval: 5000,
  });

  const { assigned, finished } = useMemo(() => {
    const a: AgentTask[] = [];
    const f: AgentTask[] = [];
    for (const t of tasks) {
      if (t.status === 'pending' || t.status === 'claimed') a.push(t);
      else f.push(t);
    }
    return { assigned: a, finished: f };
  }, [tasks]);

  const invalidate = () => qc.invalidateQueries({ queryKey: ['agent-tasks', agentId] });

  const claimNext = async () => {
    setClaiming(true);
    try {
      await apiPost(`/agents/${agentId}/tasks/next`, {});
    } catch { /* 204 No Content is normal — apiFetch returns undefined */ }
    finally {
      setClaiming(false);
      invalidate();
    }
  };

  const markDone = async (taskId: string, status: 'done' | 'failed') => {
    try {
      await apiPatch(`/agent_tasks/${taskId}`, { status });
    } catch { /* ignore */ }
    invalidate();
  };

  if (isLoading) {
    return (
      <div className="text-xs text-muted-foreground py-2">Loading tasks…</div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="border-t border-border pt-4">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
          <Inbox size={12} />
          <span>No delegated tasks</span>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-border pt-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-medium text-foreground">
          <Inbox size={12} />
          <span>Inter-Agent Tasks</span>
          <span className="text-muted-foreground">({tasks.length})</span>
        </div>
        <button
          onClick={claimNext}
          disabled={claiming || assigned.every((t) => t.status === 'claimed')}
          className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-border text-foreground hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
          title="Atomically claim the oldest pending task"
        >
          {claiming ? <Loader2 size={10} className="animate-spin" /> : <PlayCircle size={10} />}
          Claim next
        </button>
      </div>

      {assigned.length > 0 && (
        <div>
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1.5">
            Assigned ({assigned.length})
          </div>
          <ul className="space-y-1">
            {assigned.map((t) => (
              <li key={t.id} className="rounded border border-border bg-card/50 px-2 py-1.5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-1.5 min-w-0 flex-1">
                    {STATUS_ICON[t.status]}
                    <div className="min-w-0 flex-1">
                      <div className="text-xs text-foreground truncate" title={t.prompt}>
                        {t.prompt}
                      </div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">
                        {STATUS_LABEL[t.status]} · {timeAgo(t.created_at)}
                      </div>
                    </div>
                  </div>
                  {t.status === 'claimed' && (
                    <div className="flex gap-1 shrink-0">
                      <button
                        onClick={() => markDone(t.id, 'done')}
                        className="text-[10px] px-1.5 py-0.5 rounded text-success hover:bg-success/10"
                        title="Mark done"
                      >
                        Done
                      </button>
                      <button
                        onClick={() => markDone(t.id, 'failed')}
                        className="text-[10px] px-1.5 py-0.5 rounded text-destructive hover:bg-destructive/10"
                        title="Mark failed"
                      >
                        Fail
                      </button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {finished.length > 0 && (
        <div>
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1.5">
            Done ({finished.length})
          </div>
          <ul className="space-y-1">
            {finished.slice(0, 5).map((t) => (
              <li key={t.id} className="rounded border border-border bg-card/30 px-2 py-1.5 opacity-75">
                <div className="flex items-start gap-1.5">
                  {STATUS_ICON[t.status]}
                  <div className="min-w-0 flex-1">
                    <div className="text-xs text-foreground truncate" title={t.prompt}>
                      {t.prompt}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                      {STATUS_LABEL[t.status]} · {timeAgo(t.completed_at ?? t.created_at)}
                      {t.result ? ` · ${t.result.slice(0, 40)}${t.result.length > 40 ? '…' : ''}` : ''}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
