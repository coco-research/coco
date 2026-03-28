import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api.ts';
import { cn } from '../../lib/utils.ts';
import type { Task } from './TaskList.tsx';

interface Agent {
  id: string;
  name: string;
}

interface Project {
  id: string;
  name: string;
}

interface CreateTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateTaskDialog({ open, onOpenChange }: CreateTaskDialogProps) {
  const queryClient = useQueryClient();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [projectId, setProjectId] = useState('');
  const [priority, setPriority] = useState('medium');
  const [agentId, setAgentId] = useState('');

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => apiFetch<Agent[]>('/agents'),
    enabled: open,
  });

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiFetch<Project[]>('/projects'),
    enabled: open,
  });

  const createMutation = useMutation({
    mutationFn: (body: Record<string, unknown>) => apiPost<Task>('/tasks', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      resetForm();
      onOpenChange(false);
    },
  });

  function resetForm() {
    setTitle('');
    setDescription('');
    setProjectId('');
    setPriority('medium');
    setAgentId('');
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    const body: Record<string, unknown> = { title: title.trim() };
    if (description.trim()) body.description = description.trim();
    if (projectId) body.project_id = projectId;
    body.priority = priority;
    if (agentId) body.agent_id = agentId;

    createMutation.mutate(body);
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[480px] max-w-[calc(100vw-2rem)] bg-card border border-border rounded-2xl shadow-2xl">
          <div className="flex items-center justify-between p-5 border-b border-border">
            <Dialog.Title className="text-lg font-semibold text-foreground">
              New Task
            </Dialog.Title>
            <Dialog.Close className="p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors">
              <X className="h-5 w-5" />
            </Dialog.Close>
          </div>

          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {/* Title */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
                Title <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="What needs to be done?"
                required
                className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Optional details..."
                className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors resize-y"
              />
            </div>

            {/* Project */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
                Project
              </label>
              <select
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
              >
                <option value="">None</option>
                {projects?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
                Priority
              </label>
              <div className="flex gap-2">
                {(['high', 'medium', 'low'] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriority(p)}
                    className={cn(
                      'px-3 py-1.5 text-sm rounded-md capitalize transition-colors border',
                      priority === p
                        ? p === 'high'
                          ? 'bg-destructive/20 text-destructive border-error/30'
                          : p === 'medium'
                            ? 'bg-warning/20 text-warning border-warning/30'
                            : 'bg-accent/50 text-muted-foreground border-border'
                        : 'bg-card border-border text-muted-foreground hover:bg-accent/50',
                    )}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Agent */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">
                Agent (optional)
              </label>
              <select
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
              >
                <option value="">Unassigned</option>
                {agents?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Error */}
            {createMutation.isError && (
              <p className="text-xs text-destructive">Failed to create task. Please try again.</p>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="px-4 py-1.5 text-sm rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!title.trim() || createMutation.isPending}
                className={cn(
                  'px-4 py-1.5 text-sm rounded-md font-medium transition-colors',
                  'bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm',
                  (!title.trim() || createMutation.isPending) && 'opacity-50 cursor-not-allowed',
                )}
              >
                {createMutation.isPending ? 'Creating...' : 'Create Task'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
