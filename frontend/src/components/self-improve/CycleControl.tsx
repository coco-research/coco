import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Zap } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { apiPost } from '../../lib/api';
import { useToast } from '../shared/Toast';
import { cn } from '../../lib/utils';
import type { Cycle, ImprovementCategory } from '../../types/self-improve';

const FOCUS_OPTIONS: { value: ImprovementCategory; label: string }[] = [
  { value: 'performance', label: 'Performance' },
  { value: 'ux', label: 'UX' },
  { value: 'tests', label: 'Tests' },
  { value: 'refactor', label: 'Refactor' },
  { value: 'feature', label: 'Features' },
  { value: 'docs', label: 'Docs' },
];

export function CycleControl({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const qc = useQueryClient();
  const { toast } = useToast();
  const [budgetUsd, setBudgetUsd] = useState(5);
  const [maxImprovements, setMaxImprovements] = useState(5);
  const [focusAreas, setFocusAreas] = useState<ImprovementCategory[]>([]);
  const [starting, setStarting] = useState(false);

  function toggleFocus(area: ImprovementCategory) {
    setFocusAreas((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area],
    );
  }

  async function handleStart() {
    setStarting(true);
    try {
      await apiPost<Cycle>('/self-improve/cycles', {
        budget_usd: budgetUsd,
        max_improvements: maxImprovements,
        focus_areas: focusAreas.length > 0 ? focusAreas : undefined,
      });
      qc.invalidateQueries({ queryKey: ['self-improve'] });
      toast({ title: 'Cycle started', description: 'The self-improvement squad is spinning up.' });
      onOpenChange(false);
    } catch (err) {
      toast({ title: 'Failed to start cycle', description: String(err), variant: 'destructive' });
    } finally {
      setStarting(false);
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md bg-card border border-border rounded-xl p-6 shadow-xl animate-fade-in focus:outline-none">
          <div className="flex items-center justify-between mb-5">
            <Dialog.Title className="text-lg font-semibold text-foreground">
              Start Self-Improvement Cycle
            </Dialog.Title>
            <Dialog.Close className="text-muted-foreground hover:text-foreground transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          {/* Budget slider */}
          <div className="space-y-2 mb-5">
            <label className="text-sm font-medium text-foreground">
              Budget: <span className="text-accent">${budgetUsd.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min={1}
              max={20}
              step={0.5}
              value={budgetUsd}
              onChange={(e) => setBudgetUsd(parseFloat(e.target.value))}
              className="w-full accent-accent h-2 rounded-lg appearance-none bg-muted cursor-pointer"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>$1.00</span>
              <span>$20.00</span>
            </div>
          </div>

          {/* Max improvements stepper */}
          <div className="space-y-2 mb-5">
            <label className="text-sm font-medium text-foreground">Max improvements</label>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMaxImprovements((v) => Math.max(1, v - 1))}
                className="w-8 h-8 rounded-lg bg-muted text-foreground hover:bg-muted/80 transition-colors text-sm font-medium"
              >
                -
              </button>
              <span className="text-lg font-semibold text-foreground w-8 text-center">{maxImprovements}</span>
              <button
                onClick={() => setMaxImprovements((v) => Math.min(10, v + 1))}
                className="w-8 h-8 rounded-lg bg-muted text-foreground hover:bg-muted/80 transition-colors text-sm font-medium"
              >
                +
              </button>
            </div>
          </div>

          {/* Focus areas */}
          <div className="space-y-2 mb-5">
            <label className="text-sm font-medium text-foreground">Focus areas <span className="text-muted-foreground font-normal">(optional)</span></label>
            <div className="flex flex-wrap gap-2">
              {FOCUS_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => toggleFocus(opt.value)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border',
                    focusAreas.includes(opt.value)
                      ? 'bg-accent/20 text-accent border-accent/40'
                      : 'bg-muted/50 text-muted-foreground border-border hover:border-accent/30',
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Safety notice */}
          <div className="rounded-lg bg-muted/30 border border-border p-3 mb-6">
            <p className="text-xs text-muted-foreground leading-relaxed">
              <span className="font-medium text-foreground">Safety:</span> Agents work in isolated git
              worktrees. All changes require your approval before merging.
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Dialog.Close className="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors">
              Cancel
            </Dialog.Close>
            <button
              onClick={handleStart}
              disabled={starting}
              className="px-4 py-2 rounded-lg bg-accent text-accent-foreground hover:opacity-90 transition-opacity font-medium text-sm flex items-center gap-2 disabled:opacity-50"
            >
              {starting ? (
                <div className="h-4 w-4 border-2 border-accent-foreground border-t-transparent rounded-full animate-spin" />
              ) : (
                <Zap size={14} />
              )}
              Start Cycle
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
