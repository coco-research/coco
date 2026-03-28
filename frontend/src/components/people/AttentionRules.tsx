import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, ShieldAlert } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { apiFetch, apiPost, apiDelete } from '../../lib/api';
import { cn } from '../../lib/utils';

interface MatchCondition {
  field: string;
  op: string;
  value: string | string[];
}

export interface AttentionRule {
  id: string;
  match: { all?: MatchCondition[]; any?: MatchCondition[] } | Record<string, unknown>;
  action: string;
  target_project?: string;
  reason: string;
  source: string;
  created_at: string;
}

function humanizeMatch(match: AttentionRule['match']): string {
  // Handle complex match structure: {all: [{field, op, value}]}
  const conditions = (match as { all?: MatchCondition[]; any?: MatchCondition[] });
  if (conditions.all && Array.isArray(conditions.all)) {
    return conditions.all
      .map((c) => `${c.field} ${c.op} ${JSON.stringify(c.value)}`)
      .join(' AND ');
  }
  if (conditions.any && Array.isArray(conditions.any)) {
    return conditions.any
      .map((c) => `${c.field} ${c.op} ${JSON.stringify(c.value)}`)
      .join(' OR ');
  }
  // Fallback for flat key-value
  return Object.entries(match)
    .map(([key, value]) => `${key} = ${JSON.stringify(value)}`)
    .join(' AND ');
}

const SOURCE_STYLES: Record<string, string> = {
  taught: 'bg-accent/20 text-accent',
  observed: 'bg-info/20 text-info',
  manual: 'bg-warning/20 text-warning',
};

export function AttentionRules() {
  const qc = useQueryClient();

  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['rules'],
    queryFn: () => apiFetch<AttentionRule[]>('/brain/rules'),
  });

  async function handleDeleteRule(id: string) {
    await apiDelete('/brain/rules/' + id);
    void qc.invalidateQueries({ queryKey: ['rules'] });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Attention Rules ({rules.length})
        </h2>
        <AddRuleDialog />
      </div>

      {isLoading && <p className="text-muted-foreground text-sm">Loading rules...</p>}

      {!isLoading && rules.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <ShieldAlert size={40} className="mb-3 opacity-40" />
          <p className="text-sm">No attention rules configured yet.</p>
        </div>
      )}

      <div className="space-y-3">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="bg-card rounded-xl border border-border p-5"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0 space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-muted-foreground">#{rule.id}</span>
                  <span
                    className={cn(
                      'rounded-full px-2 py-0.5 text-[10px] font-medium capitalize',
                      SOURCE_STYLES[rule.source] ?? 'bg-border/30 text-muted-foreground',
                    )}
                  >
                    {rule.source}
                  </span>
                </div>

                <div className="text-sm text-foreground">
                  <span className="text-muted-foreground">When </span>
                  <span className="font-mono text-xs bg-accent/50 rounded px-1.5 py-0.5">
                    {humanizeMatch(rule.match)}
                  </span>
                </div>

                <div className="text-sm text-foreground">
                  <span className="text-muted-foreground">Then </span>
                  <span className="font-semibold">{rule.action}</span>
                  {rule.target_project && (
                    <span className="inline-flex items-center rounded bg-accent/10 text-accent px-1.5 py-0.5 text-[10px] ml-1.5">
                      {rule.target_project}
                    </span>
                  )}
                </div>

                {rule.reason && (
                  <p className="text-xs text-muted-foreground italic">{rule.reason}</p>
                )}
              </div>

              <button
                onClick={() => void handleDeleteRule(rule.id)}
                className="p-1.5 rounded hover:bg-destructive/15 text-muted-foreground hover:text-destructive transition-colors shrink-0"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AddRuleDialog() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const [matchField, setMatchField] = useState('sender');
  const [matchOperator, setMatchOperator] = useState('contains');
  const [matchValue, setMatchValue] = useState('');
  const [action, setAction] = useState('flag');
  const [targetProject, setTargetProject] = useState('');
  const [reason, setReason] = useState('');

  function resetForm() {
    setMatchField('sender');
    setMatchOperator('contains');
    setMatchValue('');
    setAction('flag');
    setTargetProject('');
    setReason('');
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!matchValue.trim()) return;

    setSaving(true);
    try {
      await apiPost('/brain/rules', {
        match: { [matchField]: matchValue.trim(), operator: matchOperator },
        action,
        target_project: targetProject.trim() || undefined,
        reason: reason.trim(),
      });
      void qc.invalidateQueries({ queryKey: ['rules'] });
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
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-colors cursor-pointer">
          <Plus className="h-4 w-4" />
          Add Rule
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[440px] max-w-[90vw] bg-card border border-border rounded-2xl shadow-2xl z-50 p-6">
          <div className="flex items-center justify-between mb-5">
            <Dialog.Title className="text-lg font-semibold text-foreground">Add Attention Rule</Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors">
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Field</label>
                <select
                  value={matchField}
                  onChange={(e) => setMatchField(e.target.value)}
                  className={inputCls}
                >
                  <option value="sender">Sender</option>
                  <option value="subject">Subject</option>
                  <option value="source">Source</option>
                  <option value="project">Project</option>
                  <option value="keyword">Keyword</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Operator</label>
                <select
                  value={matchOperator}
                  onChange={(e) => setMatchOperator(e.target.value)}
                  className={inputCls}
                >
                  <option value="contains">Contains</option>
                  <option value="equals">Equals</option>
                  <option value="starts_with">Starts with</option>
                  <option value="regex">Regex</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Value *</label>
                <input
                  value={matchValue}
                  onChange={(e) => setMatchValue(e.target.value)}
                  required
                  className={inputCls}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Action</label>
                <select
                  value={action}
                  onChange={(e) => setAction(e.target.value)}
                  className={inputCls}
                >
                  <option value="flag">Flag</option>
                  <option value="classify">Auto-classify</option>
                  <option value="urgent">Mark Urgent</option>
                  <option value="ignore">Ignore</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Target Project</label>
                <input
                  value={targetProject}
                  onChange={(e) => setTargetProject(e.target.value)}
                  placeholder="cross-risk"
                  className={inputCls}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Reason</label>
              <input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Why this rule exists"
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
                disabled={saving || !matchValue.trim()}
                className={cn(
                  'px-4 py-1.5 text-sm rounded-lg bg-accent text-accent-foreground font-medium hover:bg-accent/80 shadow-sm transition-all',
                  (saving || !matchValue.trim()) && 'opacity-50 cursor-not-allowed',
                )}
              >
                {saving ? 'Adding...' : 'Add Rule'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
