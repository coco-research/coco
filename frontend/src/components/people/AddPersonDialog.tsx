import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Plus } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { cn } from '../../lib/utils';
import { apiPost } from '../../lib/api';

export function AddPersonDialog() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState('');
  const [role, setRole] = useState<string>('collaborator');
  const [priority, setPriority] = useState<string>('normal');
  const [projects, setProjects] = useState('');
  const [emailPatterns, setEmailPatterns] = useState('');

  function resetForm() {
    setName('');
    setRole('collaborator');
    setPriority('normal');
    setProjects('');
    setEmailPatterns('');
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setSaving(true);
    try {
      await apiPost('/brain/people', {
        full_name: name.trim(),
        role,
        priority,
        projects: projects.split(',').map((s) => s.trim()).filter(Boolean),
        patterns: {
          email_from: emailPatterns.split(',').map((s) => s.trim()).filter(Boolean),
        },
      });
      void qc.invalidateQueries({ queryKey: ['people'] });
      resetForm();
      setOpen(false);
    } finally {
      setSaving(false);
    }
  }

  const inputCls = 'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all cursor-pointer">
          <Plus className="h-4 w-4" />
          Add Person
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[440px] max-w-[90vw] bg-card border border-border rounded-2xl shadow-2xl z-50 p-6">
          <div className="flex items-center justify-between mb-5">
            <Dialog.Title className="text-lg font-semibold text-foreground">Add Person</Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors">
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Name *</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Chris Miller"
                required
                className={inputCls}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className={inputCls}
                >
                  <option value="manager">Manager</option>
                  <option value="collaborator">Collaborator</option>
                  <option value="stakeholder">Stakeholder</option>
                  <option value="external">External</option>
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
                  <option value="normal">Normal</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Projects (comma-separated)</label>
              <input
                value={projects}
                onChange={(e) => setProjects(e.target.value)}
                placeholder="cross-risk, knowledge-hub"
                className={inputCls}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Email Patterns (comma-separated)</label>
              <input
                value={emailPatterns}
                onChange={(e) => setEmailPatterns(e.target.value)}
                placeholder="chris@example.com, c.miller@"
                className={inputCls}
              />
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
                disabled={saving || !name.trim()}
                className={cn(
                  'px-4 py-1.5 text-sm rounded-lg bg-accent text-accent-foreground font-medium hover:bg-accent/80 shadow-sm transition-all',
                  (saving || !name.trim()) && 'opacity-50 cursor-not-allowed',
                )}
              >
                {saving ? 'Adding...' : 'Add Person'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
