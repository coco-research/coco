/**
 * DelegationPanel — Shows the delegation chain for a task.
 *
 * Renders a vertical timeline: Parent Task -> Current Task -> Subtasks.
 * Each node displays agent avatar (initial circle), task title, and status chip.
 * Includes a "Delegate" button to delegate the current task to another agent.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { GitBranch, ChevronDown, Plus, ArrowDownRight, Check, Layers } from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api';
import { cn, timeAgo } from '../../lib/utils';
import { statePillClass, STATE_LABELS } from '../../lib/state-machine';

interface DelegationNode {
  task_id: string;
  task_title: string;
  status: string;
  agent_id: string | null;
  agent_name: string | null;
  delegated_by: string | null;
  delegated_by_name?: string | null;
  delegated_to_name?: string | null;
  delegated_at?: string | null;
  depth: number;
}

interface Agent {
  id: string;
  name: string;
  role: string | null;
}

interface DelegationPanelProps {
  taskId: string;
  taskTitle: string;
  currentAgentId: string | null;
}

function AgentAvatar({ name }: { name: string | null }) {
  const initial = name ? name.charAt(0).toUpperCase() : '?';
  return (
    <div className="flex items-center justify-center h-7 w-7 rounded-full bg-accent/30 text-accent text-xs font-semibold shrink-0">
      {initial}
    </div>
  );
}

export function DelegationPanel({ taskId, currentAgentId }: DelegationPanelProps) {
  const queryClient = useQueryClient();
  const [showDelegateDropdown, setShowDelegateDropdown] = useState(false);
  const [showSubtaskForm, setShowSubtaskForm] = useState(false);
  const [subtaskTitle, setSubtaskTitle] = useState('');
  const [subtaskAgentId, setSubtaskAgentId] = useState('');

  const { data: chain = [], isLoading } = useQuery<DelegationNode[]>({
    queryKey: ['delegation-chain', taskId],
    queryFn: () => apiFetch(`/tasks/${taskId}/delegation-chain`),
  });

  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: () => apiFetch('/agents'),
  });

  const delegateMutation = useMutation({
    mutationFn: (toAgentId: string) =>
      apiPost(`/tasks/${taskId}/delegate`, { to_agent_id: toAgentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['delegation-chain', taskId] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setShowDelegateDropdown(false);
    },
  });

  const subtaskMutation = useMutation({
    mutationFn: (body: { title: string; agent_id: string }) =>
      apiPost(`/tasks/${taskId}/subtask`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['delegation-chain', taskId] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setShowSubtaskForm(false);
      setSubtaskTitle('');
      setSubtaskAgentId('');
    },
  });

  const availableAgents = agents.filter((a) => a.id !== currentAgentId);

  if (isLoading) {
    return (
      <div className="py-4 text-sm text-muted-foreground">Loading delegation chain...</div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
        <GitBranch className="h-3.5 w-3.5" />
        Delegation Chain
        {chain.length > 1 && (
          <span className="flex items-center gap-1 ml-auto text-[10px] normal-case tracking-normal bg-muted/60 px-1.5 py-0.5 rounded">
            <Layers className="h-3 w-3" />
            Depth {Math.max(...chain.map((n) => n.depth))}
          </span>
        )}
      </div>

      {/* Chain timeline */}
      <div className="relative pl-4">
        {/* Vertical connecting line */}
        {chain.length > 1 && (
          <div className="absolute left-[17px] top-4 bottom-4 w-px bg-border" />
        )}

        {chain.length === 0 ? (
          <div className="text-sm text-muted-foreground py-2">
            No delegation chain. This is a standalone task.
          </div>
        ) : (
          chain.map((node, i) => {
            const isCurrent = node.task_id === taskId;
            const isCompleted = node.status === 'done' || node.status === 'archived';
            return (
              <div
                key={node.task_id}
                className={cn(
                  'relative flex items-start gap-3 py-2',
                  isCurrent && 'bg-accent/10 -mx-2 px-2 rounded-lg',
                )}
              >
                {/* Avatar — with completion checkmark overlay */}
                <div className="relative">
                  <AgentAvatar name={node.agent_name} />
                  {isCompleted && (
                    <span className="absolute -bottom-0.5 -right-0.5 flex items-center justify-center h-3.5 w-3.5 rounded-full bg-green-500 ring-2 ring-card">
                      <Check className="h-2 w-2 text-white" />
                    </span>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'text-sm truncate',
                        isCurrent ? 'font-semibold text-foreground' : 'text-foreground/80',
                        isCompleted && 'line-through opacity-70',
                      )}
                    >
                      {node.task_title}
                    </span>
                    <span
                      className={cn(
                        'inline-block px-1.5 py-0.5 rounded-full text-[10px] font-medium capitalize shrink-0',
                        statePillClass(node.status),
                      )}
                    >
                      {STATE_LABELS[node.status] ?? node.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground flex-wrap">
                    {/* Delegated-by in blue */}
                    {node.delegated_by && (
                      <span className="flex items-center gap-0.5 text-blue-400">
                        <ArrowDownRight className="h-3 w-3" />
                        from <span className="font-medium">{node.delegated_by_name ?? node.delegated_by}</span>
                      </span>
                    )}
                    {/* Delegated-to (current agent) in green */}
                    {node.agent_name ? (
                      <span className={cn(node.delegated_by ? 'text-emerald-400' : 'text-muted-foreground')}>
                        {node.delegated_by ? (
                          <>to <span className="font-medium">{node.agent_name}</span></>
                        ) : (
                          node.agent_name
                        )}
                      </span>
                    ) : (
                      <span className="italic">Unassigned</span>
                    )}
                    {/* Elapsed time since delegation */}
                    {node.delegated_at && (
                      <span className="text-[10px] text-muted-foreground/70">
                        {timeAgo(node.delegated_at)}
                      </span>
                    )}
                    {i === 0 && chain.length > 1 && (
                      <span className="text-[10px] bg-muted/50 px-1.5 py-0.5 rounded">Parent</span>
                    )}
                    {isCurrent && chain.length > 1 && i !== 0 && (
                      <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded">Current</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2 border-t border-border">
        {/* Delegate button */}
        <div className="relative">
          <button
            onClick={() => {
              setShowDelegateDropdown(!showDelegateDropdown);
              setShowSubtaskForm(false);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-accent/20 text-accent hover:bg-accent/30 transition-colors"
          >
            <ArrowDownRight className="h-3.5 w-3.5" />
            Delegate
            <ChevronDown className="h-3 w-3" />
          </button>

          {showDelegateDropdown && (
            <div className="absolute left-0 top-full mt-1 w-56 bg-card border border-border rounded-lg shadow-lg z-50 py-1">
              {availableAgents.length === 0 ? (
                <div className="px-3 py-2 text-xs text-muted-foreground">No other agents available</div>
              ) : (
                availableAgents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => delegateMutation.mutate(agent.id)}
                    disabled={delegateMutation.isPending}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent/50 transition-colors"
                  >
                    <AgentAvatar name={agent.name} />
                    <div className="flex-1 min-w-0">
                      <div className="truncate text-foreground">{agent.name}</div>
                      {agent.role && (
                        <div className="text-[10px] text-muted-foreground capitalize">{agent.role.replace('-', ' ')}</div>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Create subtask button */}
        <button
          onClick={() => {
            setShowSubtaskForm(!showSubtaskForm);
            setShowDelegateDropdown(false);
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-muted text-muted-foreground hover:bg-muted/80 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Add Subtask
        </button>
      </div>

      {/* Subtask form */}
      {showSubtaskForm && (
        <div className="space-y-2 p-3 border border-border rounded-lg bg-muted/30">
          <input
            value={subtaskTitle}
            onChange={(e) => setSubtaskTitle(e.target.value)}
            placeholder="Subtask title..."
            className="w-full bg-card border border-border rounded-md px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20"
          />
          <select
            value={subtaskAgentId}
            onChange={(e) => setSubtaskAgentId(e.target.value)}
            className="w-full bg-card border border-border rounded-md px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20"
          >
            <option value="">Assign to agent...</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <button
              onClick={() => {
                if (subtaskTitle.trim() && subtaskAgentId) {
                  subtaskMutation.mutate({ title: subtaskTitle.trim(), agent_id: subtaskAgentId });
                }
              }}
              disabled={!subtaskTitle.trim() || !subtaskAgentId || subtaskMutation.isPending}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-md bg-accent text-accent-foreground hover:bg-accent/80 transition-colors',
                (!subtaskTitle.trim() || !subtaskAgentId) && 'opacity-50 cursor-not-allowed',
              )}
            >
              {subtaskMutation.isPending ? 'Creating...' : 'Create'}
            </button>
            <button
              onClick={() => setShowSubtaskForm(false)}
              className="px-3 py-1.5 text-xs rounded-md text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
