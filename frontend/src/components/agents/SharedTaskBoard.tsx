/**
 * SharedTaskBoard — Kanban-style board showing tasks grouped by status for a set of agents.
 *
 * Columns: Open (backlog+todo), In Progress, In Review, Done.
 * Cards show: task title, assigned agent, delegated_by indicator.
 * Uses the existing BoardView component for layout.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Users, ArrowDownRight } from 'lucide-react';
import { apiFetch, apiTransition } from '../../lib/api';
import { cn } from '../../lib/utils';
import { BoardView } from '../shared/BoardView';
import { TASK_STATES } from '../../lib/state-machine';

interface TaskQueueItem {
  id: string;
  title: string;
  status: string;
  priority: string;
  agent_id: string | null;
  agent_name?: string | null;
  delegated_by?: string | null;
  owner?: string | null;
  due_date?: string | null;
  blocked_by_count?: number;
  blocking_count?: number;
}

interface Agent {
  id: string;
  name: string;
}

interface SharedTaskBoardProps {
  /** Agent IDs to show tasks for. If a single ID, shows that agent's queue. */
  agentIds: string[];
  /** Optional title override */
  title?: string;
}

/** Board states — skip archived for the kanban view */
const BOARD_STATES = TASK_STATES.filter((s) => s !== 'archived');

export function SharedTaskBoard({ agentIds, title }: SharedTaskBoardProps) {
  const queryClient = useQueryClient();

  // Fetch task queues for all agents
  const { data: allTasks = [], isLoading } = useQuery<TaskQueueItem[]>({
    queryKey: ['task-queue', ...agentIds],
    queryFn: async () => {
      const results = await Promise.all(
        agentIds.map((id) => apiFetch<TaskQueueItem[]>(`/tasks/queue/${id}`)),
      );
      // Deduplicate by task ID in case tasks appear in multiple queues
      const seen = new Set<string>();
      const merged: TaskQueueItem[] = [];
      for (const batch of results) {
        for (const task of batch) {
          if (!seen.has(task.id)) {
            seen.add(task.id);
            merged.push(task);
          }
        }
      }
      return merged;
    },
    enabled: agentIds.length > 0,
    refetchInterval: 10000,
  });

  // Also fetch agents for name lookup
  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: () => apiFetch('/agents'),
  });

  const agentMap = new Map(agents.map((a) => [a.id, a.name]));

  // Enrich tasks with agent_name for display on cards
  const enrichedTasks = allTasks.map((t) => ({
    ...t,
    owner: t.agent_name ?? (t.agent_id ? agentMap.get(t.agent_id) : null) ?? null,
  }));

  async function handleTransition(taskId: string, toState: string) {
    try {
      await apiTransition(`/tasks/${taskId}`, toState);
      queryClient.invalidateQueries({ queryKey: ['task-queue'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    } catch {
      // ignore
    }
  }

  if (agentIds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Users className="h-8 w-8 mb-2 opacity-30" />
        <p className="text-sm">Select an agent to view their task queue.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
        Loading task queue...
      </div>
    );
  }

  if (enrichedTasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Users className="h-8 w-8 mb-2 opacity-30" />
        <p className="text-sm">No tasks in queue.</p>
        <p className="text-xs mt-1">Delegate or create tasks to populate this board.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {title && (
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-foreground">{title}</h3>
          <span className="text-xs text-muted-foreground">({enrichedTasks.length} tasks)</span>
        </div>
      )}
      <div className="h-[500px]">
        <BoardView
          items={enrichedTasks}
          states={BOARD_STATES}
          kind="task"
          onTransition={handleTransition}
        />
      </div>
    </div>
  );
}
