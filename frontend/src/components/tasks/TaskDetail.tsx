import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { X, Lock, Unlock } from 'lucide-react';
import { apiFetch, apiPatch, apiPost, apiTransition } from '../../lib/api.ts';
import { cn, timeAgo } from '../../lib/utils.ts';
import { TransitionButtons } from '../shared/TransitionButtons';
import { statePillClass, STATE_LABELS } from '../../lib/state-machine';
import type { Task } from './TaskList.tsx';

interface Agent {
  id: string;
  name: string;
}

interface Project {
  id: string;
  name: string;
}

interface TaskDetailProps {
  task: Task;
  onClose: () => void;
}

const PRIORITY_STYLES: Record<string, string> = {
  high: 'bg-destructive/20 text-destructive',
  medium: 'bg-warning/20 text-warning',
  low: 'bg-accent/50 text-muted-foreground',
};

export function TaskDetail({ task, onClose }: TaskDetailProps) {
  const queryClient = useQueryClient();

  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description ?? '');
  const [priority, setPriority] = useState(task.priority);
  const [agentId, setAgentId] = useState(task.agent_id ?? '');
  const [projectId, setProjectId] = useState(task.project_id ?? '');
  const [transitioning, setTransitioning] = useState(false);

  // Reset form when task changes
  useEffect(() => {
    setTitle(task.title);
    setDescription(task.description ?? '');
    setPriority(task.priority);
    setAgentId(task.agent_id ?? '');
    setProjectId(task.project_id ?? '');
  }, [task]);

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => apiFetch<Agent[]>('/agents'),
  });

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiFetch<Project[]>('/projects'),
  });

  const updateMutation = useMutation({
    mutationFn: (body: Record<string, unknown>) => apiPatch<Task>(`/tasks/${task.id}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: () => apiPost<Task>(`/tasks/${task.id}/checkout`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const releaseMutation = useMutation({
    mutationFn: () => apiPost<Task>(`/tasks/${task.id}/release`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  function handleSave() {
    const body: Record<string, unknown> = {};
    if (title !== task.title) body.title = title;
    if (description !== (task.description ?? '')) body.description = description;
    if (priority !== task.priority) body.priority = priority;
    if (agentId !== (task.agent_id ?? '')) body.agent_id = agentId || null;
    if (projectId !== (task.project_id ?? '')) body.project_id = projectId || null;
    if (Object.keys(body).length > 0) {
      updateMutation.mutate(body);
    }
  }

  async function handleTransition(toState: string) {
    setTransitioning(true);
    try {
      await apiTransition(`/tasks/${task.id}`, toState);
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    } finally {
      setTransitioning(false);
    }
  }

  const isCheckedOut = task.status === 'checked_out';

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" onClick={onClose} />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-[540px] max-w-full bg-card border-l border-border shadow-2xl z-50 flex flex-col animate-slide-in">
        {/* Header */}
        <div className="flex items-start gap-3 p-5 border-b border-border">
          <div className="flex-1 min-w-0">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="text-lg font-semibold text-foreground bg-transparent border-none outline-none w-full focus:ring-1 focus:ring-accent rounded px-1 -mx-1"
            />
            <div className="flex items-center gap-2 mt-2">
              <span
                className={cn(
                  'inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                  statePillClass(task.status),
                )}
              >
                {STATE_LABELS[task.status] ?? task.status.replace('_', ' ')}
              </span>
              <span
                className={cn(
                  'inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                  PRIORITY_STYLES[task.priority] ?? 'bg-accent/50 text-muted-foreground',
                )}
              >
                {task.priority}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
              placeholder="Add a description..."
              className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors resize-y"
            />
          </div>

          {/* Status transitions */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
              Transition
            </label>
            <TransitionButtons
              currentState={task.status}
              kind="task"
              onTransition={(toState) => void handleTransition(toState)}
              isPending={transitioning}
              size="md"
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
            >
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Project */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
              Project
            </label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
            >
              <option value="">None</option>
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Agent assignment */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
              Assigned Agent
            </label>
            <div className="flex items-center gap-2">
              <select
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors flex-1"
              >
                <option value="">Unassigned</option>
                {agents?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>

              {!isCheckedOut ? (
                <button
                  onClick={() => checkoutMutation.mutate()}
                  disabled={checkoutMutation.isPending || task.status === 'done' || task.status === 'archived'}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors',
                    'bg-info/20 text-info hover:bg-info/25',
                    (checkoutMutation.isPending || task.status === 'done' || task.status === 'archived') && 'opacity-50 cursor-not-allowed',
                  )}
                >
                  <Lock className="h-3.5 w-3.5" />
                  Checkout
                </button>
              ) : (
                <button
                  onClick={() => releaseMutation.mutate()}
                  disabled={releaseMutation.isPending}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors',
                    'bg-warning/20 text-warning hover:bg-warning/25',
                    releaseMutation.isPending && 'opacity-50',
                  )}
                >
                  <Unlock className="h-3.5 w-3.5" />
                  Release
                </button>
              )}
            </div>
            {task.checked_out_by && (
              <p className="text-xs text-muted-foreground mt-1">
                Checked out by {task.checked_out_by}
                {task.checked_out_at && ` \u00B7 ${timeAgo(task.checked_out_at)}`}
              </p>
            )}
          </div>

          {/* Timestamps */}
          <div className="space-y-1.5 text-sm pt-2 border-t border-border">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span className="text-foreground">{timeAgo(task.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Updated</span>
              <span className="text-foreground">{timeAgo(task.updated_at)}</span>
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex items-center gap-2 p-4 border-t border-border">
          <button
            onClick={handleSave}
            disabled={updateMutation.isPending}
            className={cn(
              'px-4 py-1.5 text-sm rounded-md font-medium transition-colors',
              'bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm',
              updateMutation.isPending && 'opacity-50',
            )}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save'}
          </button>

          {updateMutation.isError && (
            <span className="text-xs text-destructive">
              Failed to save. Try again.
            </span>
          )}

          <div className="flex-1" />

          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </>
  );
}
