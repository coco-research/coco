import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { apiPost, apiFetch } from '../../lib/api';
import { useQuery } from '@tanstack/react-query';
import type { Agent } from './AgentCard';
import { ROLE_META } from './AgentCard';

interface Project {
  id: string;
  name: string;
}

interface CreateAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: (agent: Agent) => void;
}

const inputCls = 'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

export function CreateAgentDialog({ open, onOpenChange, onCreated }: CreateAgentDialogProps) {
  const [name, setName] = useState('');
  const [projectId, setProjectId] = useState('');
  const [model, setModel] = useState('sonnet');
  const [role, setRole] = useState('custom');
  const [taskDescription, setTaskDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const { data: projects } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => apiFetch('/projects'),
  });

  const reset = () => {
    setName('');
    setProjectId('');
    setModel('sonnet');
    setRole('custom');
    setTaskDescription('');
    setSystemPrompt('');
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    if (!taskDescription.trim()) {
      setError('Task description is required');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      // Create agent
      const agent = await apiPost<Agent>('/agents', {
        name: name.trim(),
        project_id: projectId || null,
        model,
        role: role || 'custom',
        task_description: taskDescription.trim(),
        system_prompt: systemPrompt.trim() || null,
      });

      // Spawn it immediately
      const spawned = await apiPost<Agent>(`/agents/${agent.id}/spawn`, {});
      onCreated(spawned);
      reset();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-foreground">New Agent</Dialog.Title>
            <Dialog.Close className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-accent/50 transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-muted-foreground mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. refactor-auth"
                className={inputCls}
              />
            </div>

            <div>
              <label className="block text-sm text-muted-foreground mb-1">Project</label>
              <select
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className={inputCls}
              >
                <option value="">No project</option>
                {projects?.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-muted-foreground mb-1">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className={inputCls}
              >
                <option value="haiku">Haiku</option>
                <option value="sonnet">Sonnet</option>
                <option value="opus">Opus</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-muted-foreground mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className={inputCls}
              >
                {Object.entries(ROLE_META).map(([slug, meta]) => (
                  <option key={slug} value={slug}>{meta.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-muted-foreground mb-1">Task Description</label>
              <textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="What should this agent do?"
                rows={3}
                className={`${inputCls} resize-none`}
              />
            </div>

            <div>
              <label className="block text-sm text-muted-foreground mb-1">System Prompt (optional)</label>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Additional context or instructions..."
                rows={2}
                className={`${inputCls} resize-none`}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Dialog.Close className="px-4 py-2 text-sm rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all">
                Cancel
              </Dialog.Close>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 text-sm rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all disabled:opacity-50"
              >
                {submitting ? 'Creating...' : 'Create & Launch'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
