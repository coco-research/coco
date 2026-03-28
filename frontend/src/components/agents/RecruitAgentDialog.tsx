import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, UserPlus } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';
import { ROLE_META } from './AgentCard';

interface AgentRole {
  slug: string;
  name: string;
  default_model: string;
  system_prompt: string;
}

interface RecruitAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  nodeId: string;
  onRecruited?: () => void;
}

const inputCls = 'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

export function RecruitAgentDialog({ open, onOpenChange, nodeId, onRecruited }: RecruitAgentDialogProps) {
  const queryClient = useQueryClient();
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [model, setModel] = useState('sonnet');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const { data: roles = [], isLoading: rolesLoading } = useQuery<AgentRole[]>({
    queryKey: ['agent-roles'],
    queryFn: () => apiFetch('/agent-roles'),
    enabled: open,
  });

  const selectRole = (role: AgentRole) => {
    setSelectedSlug(role.slug);
    setName(role.name);
    setModel(role.default_model);
    setSystemPrompt('');
    setError('');
  };

  const reset = () => {
    setSelectedSlug(null);
    setName('');
    setModel('sonnet');
    setSystemPrompt('');
    setError('');
  };

  const handleRecruit = async () => {
    if (!selectedSlug) {
      setError('Select a role first');
      return;
    }
    if (!name.trim()) {
      setError('Name is required');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await apiPost('/agents/recruit', {
        node_id: nodeId,
        role_slug: selectedSlug,
        name: name.trim(),
        model,
        ...(systemPrompt.trim() ? { system_prompt: systemPrompt.trim() } : {}),
      });
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      onRecruited?.();
      reset();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to recruit agent');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-5">
            <Dialog.Title className="text-lg font-semibold text-foreground flex items-center gap-2">
              <UserPlus size={18} />
              Recruit Agent
            </Dialog.Title>
            <Dialog.Close className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-accent/50 transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          {/* Role grid */}
          <div className="mb-5">
            <label className="block text-sm text-muted-foreground mb-2">Choose a role</label>
            {rolesLoading ? (
              <div className="grid grid-cols-2 gap-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-24 bg-muted/50 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {roles.map((role) => {
                  const meta = ROLE_META[role.slug] ?? ROLE_META['custom'];
                  const Icon = meta.icon;
                  const isSelected = selectedSlug === role.slug;
                  return (
                    <button
                      key={role.slug}
                      type="button"
                      onClick={() => selectRole(role)}
                      className={cn(
                        'text-left p-4 rounded-xl border-2 transition-all',
                        isSelected
                          ? 'border-accent bg-accent/10'
                          : 'border-border bg-card hover:border-accent/50'
                      )}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className={cn('inline-flex items-center justify-center w-7 h-7 rounded-lg', meta.color)}>
                          <Icon size={14} />
                        </span>
                        <span className="text-sm font-medium text-foreground">{role.name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {(role.system_prompt ?? '').split('\n')[0] || role.name}
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-1.5 uppercase tracking-wider">
                        {role.default_model}
                      </p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Configuration fields */}
          {selectedSlug && (
            <div className="space-y-4 border-t border-border pt-4">
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Agent Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Lead PM"
                  className={inputCls}
                />
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
                <label className="block text-sm text-muted-foreground mb-1">System Prompt Override (optional)</label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="Leave empty to use the role default..."
                  rows={3}
                  className={`${inputCls} resize-none`}
                />
              </div>
            </div>
          )}

          {error && <p className="text-sm text-destructive mt-3">{error}</p>}

          <div className="flex justify-end gap-2 pt-4">
            <Dialog.Close className="px-4 py-2 text-sm rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all">
              Cancel
            </Dialog.Close>
            <button
              onClick={handleRecruit}
              disabled={submitting || !selectedSlug}
              className="px-4 py-2 text-sm rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all disabled:opacity-50"
            >
              {submitting ? 'Recruiting...' : 'Recruit'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
