import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Plus, AlertTriangle } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { cn } from '../../lib/utils';
import { apiFetch, apiPost } from '../../lib/api';
import { useToast } from '../shared/Toast';

interface Project {
  id: string;
  name: string;
}

interface PossibleDuplicate {
  id: string;
  title: string;
  similarity: number;
}

interface CreateTodoResponse {
  id: string;
  title: string;
  status: string;
  possible_duplicate?: PossibleDuplicate;
}

export function AddTodoDialog() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dupWarning, setDupWarning] = useState<PossibleDuplicate | null>(null);

  const [title, setTitle] = useState('');
  const [projectId, setProjectId] = useState('');
  const [priority, setPriority] = useState('medium');
  const [owner, setOwner] = useState('rijul');
  const [dueDate, setDueDate] = useState('');

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ['projects-list'],
    queryFn: () => apiFetch<Project[]>('/projects'),
    enabled: open,
  });

  function resetForm() {
    setTitle('');
    setProjectId('');
    setPriority('medium');
    setOwner('rijul');
    setDueDate('');
    setDupWarning(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    setSaving(true);
    setDupWarning(null);
    try {
      const result = await apiPost<CreateTodoResponse>('/todos', {
        title: title.trim(),
        project_id: projectId || undefined,
        priority,
        owner: owner.trim() || undefined,
        due_date: dueDate || undefined,
      });
      void qc.invalidateQueries({ queryKey: ['todos'] });
      toast('Todo created', 'success');

      if (result.possible_duplicate) {
        // Show warning but keep dialog open briefly
        setDupWarning(result.possible_duplicate);
        resetForm();
        // Auto-dismiss after a delay
        setTimeout(() => {
          setDupWarning(null);
          setOpen(false);
        }, 4000);
      } else {
        resetForm();
        setOpen(false);
      }
    } catch {
      toast('Failed to create todo', 'error');
    } finally {
      setSaving(false);
    }
  }

  const inputCls =
    'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-colors cursor-pointer">
          <Plus className="h-4 w-4" />
          Add Todo
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[440px] max-w-[90vw] bg-card border border-border rounded-2xl shadow-2xl z-50 p-6">
          <div className="flex items-center justify-between mb-5">
            <Dialog.Title className="text-lg font-semibold text-foreground">Add Todo</Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors">
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          {dupWarning && (
            <div className="mb-4 flex items-start gap-2 rounded-lg bg-warning/10 border border-warning/30 px-3 py-2.5">
              <AlertTriangle className="h-4 w-4 text-warning shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="text-warning font-medium">Similar todo already exists</p>
                <p className="text-muted-foreground mt-0.5 text-xs">
                  &ldquo;{dupWarning.title}&rdquo;
                  <span className="ml-1 opacity-70">
                    ({Math.round(dupWarning.similarity * 100)}% similar)
                  </span>
                </p>
                <p className="text-muted-foreground/70 text-xs mt-1">
                  Created anyway. This dialog will close shortly.
                </p>
              </div>
            </div>
          )}

          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Title *</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Follow up with Chris on risk report"
                required
                className={inputCls}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Project</label>
                <select
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  className={inputCls}
                >
                  <option value="">None</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name || p.id}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className={inputCls}
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Owner</label>
                <input
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                  placeholder="rijul"
                  className={inputCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Due Date</label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className={inputCls}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Dialog.Close asChild>
                <button
                  type="button"
                  className="px-4 py-1.5 text-sm rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
                >
                  Cancel
                </button>
              </Dialog.Close>
              <button
                type="submit"
                disabled={saving || !title.trim()}
                className={cn(
                  'px-4 py-1.5 text-sm rounded-md bg-accent text-accent-foreground font-medium hover:bg-accent/80 shadow-sm transition-colors',
                  (saving || !title.trim()) && 'opacity-50 cursor-not-allowed',
                )}
              >
                {saving ? 'Adding...' : 'Add Todo'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
