import React from 'react';
import { Briefcase, ClipboardList, Code2, UserSearch, Bot, Crown, Cpu, ShieldCheck, Megaphone, BarChart3, PenTool, ListTodo, DollarSign, Clock } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { cn, timeAgo, formatCost } from '../../lib/utils';
import { InlineEditor } from '../shared/InlineEditor';
import { apiFetch, apiPatch } from '../../lib/api';

export interface Agent {
  id: string;
  human_id?: string | null;
  display_id?: string | null;
  name: string;
  model: string;
  status: string;
  task_description: string | null;
  pid: number | null;
  started_at: string | null;
  stopped_at: string | null;
  last_heartbeat: string | null;
  exit_code: number | null;
  project_id: string | null;
  system_prompt: string | null;
  working_directory: string | null;
  created_at: string;
  updated_at: string;
  config: string;
  role: string | null;
  reports_to: string | null;
  lifetime_cost_usd?: number;
  recent_output?: { stream: string; chunk: string; timestamp: string }[];
}

export const ROLE_META: Record<string, { label: string; abbr: string; color: string; icon: React.ElementType }> = {
  'chief-of-staff':            { label: 'Chief of Staff',   abbr: 'CoS',  color: 'bg-purple-500/20 text-purple-400', icon: Crown },
  'product-manager':           { label: 'Product Manager',  abbr: 'PM',   color: 'bg-info/20 text-info', icon: Briefcase },
  'project-manager':           { label: 'Project Manager',  abbr: 'PjM',  color: 'bg-warning/20 text-warning', icon: ClipboardList },
  'technical-architect':       { label: 'Tech Architect',   abbr: 'Arch', color: 'bg-cyan-500/20 text-cyan-400', icon: Cpu },
  'developer':                 { label: 'Developer',        abbr: 'Dev',  color: 'bg-success/20 text-success', icon: Code2 },
  'qa-reviewer':               { label: 'QA Reviewer',      abbr: 'QA',   color: 'bg-red-500/20 text-red-400', icon: ShieldCheck },
  'user-researcher':           { label: 'User Researcher',  abbr: 'UXR',  color: 'bg-accent/20 text-accent', icon: UserSearch },
  'communications-specialist': { label: 'Comms',            abbr: 'Com',  color: 'bg-pink-500/20 text-pink-400', icon: Megaphone },
  'data-analyst':              { label: 'Data Analyst',     abbr: 'DA',   color: 'bg-amber-500/20 text-amber-400', icon: BarChart3 },
  'scribe':                    { label: 'Scribe',           abbr: 'Scr',  color: 'bg-teal-500/20 text-teal-400', icon: PenTool },
  'custom':                    { label: 'Custom',           abbr: 'Bot',  color: 'bg-muted text-muted-foreground', icon: Bot },
};

const statusColors: Record<string, string> = {
  running: 'bg-emerald-500',
  paused: 'bg-amber-500',
  idle: 'bg-muted-foreground/40',
  completed: 'bg-blue-500',
  failed: 'bg-destructive',
  killed: 'bg-muted-foreground/40',
};

export function StatusDot({ status }: { status: string }) {
  const isActive = status === 'running';
  const color = statusColors[status] ?? 'bg-muted-foreground/40';

  return (
    <span className="relative flex h-2.5 w-2.5">
      {isActive && (
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${color} opacity-75`} />
      )}
      <span
        className={`relative inline-flex rounded-full h-2.5 w-2.5 ${color} ${isActive ? 'agent-pulse' : ''}`}
      />
    </span>
  );
}

const modelBadgeColors: Record<string, string> = {
  opus: 'bg-purple-100 text-purple-700 border-purple-200',
  sonnet: 'bg-blue-100 text-blue-700 border-blue-200',
  haiku: 'bg-emerald-100 text-emerald-700 border-emerald-200',
};

interface AgentCardProps {
  agent: Agent;
  onClick: () => void;
  onSpawn: () => void;
  onPause: () => void;
  onResume: () => void;
  onKill: () => void;
}

export const AgentCard = React.memo(function AgentCard({ agent, onClick, onSpawn, onPause, onResume, onKill }: AgentCardProps) {
  const qc = useQueryClient();
  const uptime = agent.started_at && !agent.stopped_at
    ? timeAgo(agent.started_at).replace(' ago', '')
    : null;

  // "Last run" — heartbeat if active, else last stop time, else start time
  const lastRunRaw = agent.last_heartbeat ?? agent.stopped_at ?? agent.started_at;
  const lastRun = lastRunRaw ? timeAgo(lastRunRaw) : null;
  const lifetimeCost = agent.lifetime_cost_usd ?? 0;

  // Fetch task queue count for badge
  const { data: taskQueue = [] } = useQuery<{ id: string }[]>({
    queryKey: ['task-queue', agent.id],
    queryFn: () => apiFetch(`/tasks/queue/${agent.id}`),
    refetchInterval: 15000,
    staleTime: 10000,
  });
  const taskCount = taskQueue.length;

  return (
    <div
      className="rounded-xl border border-border bg-card p-5 hover:shadow-md transition-all cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusDot status={agent.status} />
          {(agent.human_id || agent.display_id) && (
            <span
              className="inline-flex items-center rounded bg-accent/30 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-muted-foreground"
              title={agent.id}
            >
              {agent.human_id || agent.display_id}
            </span>
          )}
          {agent.role && ROLE_META[agent.role] && (
            <span className={cn('inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded', ROLE_META[agent.role].color)}>
              {(() => { const Icon = ROLE_META[agent.role!].icon; return <Icon size={10} />; })()}
              {ROLE_META[agent.role].abbr}
            </span>
          )}
          <div onClick={(e) => e.stopPropagation()}>
            <InlineEditor
              value={agent.name}
              onSave={async (name) => {
                // Optimistic update + revert on error
                const queryKeys = [['agents'], ['agents-org-chart']];
                const snapshots = queryKeys.map((k) => ({
                  key: k,
                  data: qc.getQueryData(k),
                }));
                queryKeys.forEach((k) => {
                  qc.setQueryData<Agent[] | undefined>(k, (old) =>
                    old?.map((a) => (a.id === agent.id ? { ...a, name } : a)),
                  );
                });
                try {
                  await apiPatch(`/agents/${agent.id}`, { name });
                } catch (e) {
                  snapshots.forEach((s) => qc.setQueryData(s.key, s.data));
                  throw e;
                } finally {
                  void qc.invalidateQueries({ queryKey: ['agents'] });
                  void qc.invalidateQueries({ queryKey: ['agents-org-chart'] });
                }
              }}
              as="h3"
              className="font-medium text-foreground truncate"
            />
          </div>
        </div>
        <span className={cn(
          'text-xs px-2 py-0.5 rounded-full border',
          modelBadgeColors[agent.model] || 'bg-accent/50 text-muted-foreground border-border'
        )}>
          {agent.model}
        </span>
      </div>

      <div onClick={(e) => e.stopPropagation()} className="mb-3">
        <InlineEditor
          value={agent.task_description ?? ''}
          placeholder="Add a description..."
          onSave={async (task_description) => {
            const queryKeys = [['agents'], ['agents-org-chart']];
            const snapshots = queryKeys.map((k) => ({
              key: k,
              data: qc.getQueryData(k),
            }));
            queryKeys.forEach((k) => {
              qc.setQueryData<Agent[] | undefined>(k, (old) =>
                old?.map((a) => (a.id === agent.id ? { ...a, task_description } : a)),
              );
            });
            try {
              await apiPatch(`/agents/${agent.id}`, { task_description });
            } catch (e) {
              snapshots.forEach((s) => qc.setQueryData(s.key, s.data));
              throw e;
            } finally {
              void qc.invalidateQueries({ queryKey: ['agents'] });
              void qc.invalidateQueries({ queryKey: ['agents-org-chart'] });
            }
          }}
          as="p"
          className="text-sm text-muted-foreground line-clamp-2"
        />
      </div>

      <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
        <span className="capitalize">{agent.status}</span>
        {agent.pid && <span>PID {agent.pid}</span>}
        {uptime && <span>{uptime}</span>}
        {taskCount > 0 && (
          <span className="flex items-center gap-1 ml-auto px-2 py-0.5 rounded-full bg-accent/20 text-accent text-[10px] font-medium">
            <ListTodo size={10} />
            {taskCount} task{taskCount !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3 text-[11px] text-muted-foreground mb-3 tabular-nums">
        <span className="flex items-center gap-1" title="Lifetime cost">
          <DollarSign size={11} />
          {formatCost(lifetimeCost)}
        </span>
        {lastRun && (
          <span className="flex items-center gap-1" title={`Last activity: ${lastRunRaw}`}>
            <Clock size={11} />
            {lastRun}
          </span>
        )}
      </div>

      <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
        {agent.status === 'idle' && (
          <button
            onClick={onSpawn}
            className="px-3 py-1.5 text-xs rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all"
          >
            Spawn
          </button>
        )}
        {agent.status === 'running' && (
          <>
            <button
              onClick={onPause}
              className="px-3 py-1.5 text-xs rounded-lg bg-warning/20 text-warning hover:bg-warning/20 transition-all"
            >
              Pause
            </button>
            <button
              onClick={onKill}
              className="px-3 py-1.5 text-xs rounded-lg bg-destructive/20 text-destructive hover:bg-destructive/20 transition-all"
            >
              Kill
            </button>
          </>
        )}
        {agent.status === 'paused' && (
          <>
            <button
              onClick={onResume}
              className="px-3 py-1.5 text-xs rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all"
            >
              Resume
            </button>
            <button
              onClick={onKill}
              className="px-3 py-1.5 text-xs rounded-lg bg-destructive/20 text-destructive hover:bg-destructive/20 transition-all"
            >
              Kill
            </button>
          </>
        )}
        {['completed', 'failed', 'killed'].includes(agent.status) && (
          <button
            onClick={onSpawn}
            className="px-3 py-1.5 text-xs rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all"
          >
            Respawn
          </button>
        )}
      </div>
    </div>
  );
});
