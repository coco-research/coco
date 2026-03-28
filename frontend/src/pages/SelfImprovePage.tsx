import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Sparkles, XCircle, Zap, Bot, Inbox } from 'lucide-react';
import { apiFetch, apiPost } from '../lib/api';
import { cn } from '../lib/utils';
import { formatCost } from '../lib/utils';
import { useToast } from '../components/shared/Toast';
import { CycleControl } from '../components/self-improve/CycleControl';
import { ImprovementCard } from '../components/self-improve/ImprovementCard';
import { CycleHistory } from '../components/self-improve/CycleHistory';
import type { Cycle, SquadAgent } from '../types/self-improve';

// ─── Stage Stepper ───────────────────────────────────────────────────

const STAGES = [
  { key: 'planning', label: 'Planning' },
  { key: 'architecting', label: 'Architecting' },
  { key: 'developing', label: 'Developing' },
  { key: 'testing', label: 'Testing' },
  { key: 'reviewing', label: 'Reviewing' },
  { key: 'documenting', label: 'Documenting' },
  { key: 'awaiting_approval', label: 'Approval' },
  { key: 'completed', label: 'Done' },
] as const;

const TERMINAL_STATUSES = ['completed', 'rejected', 'failed'];

function getStageIndex(status: Cycle['status']): number {
  // merging/integrating map to between approval and done
  if (status === 'merging' || status === 'integrating') return 7;
  const idx = STAGES.findIndex((s) => s.key === status);
  return idx >= 0 ? idx : -1;
}

function StageStepper({ status }: { status: Cycle['status'] }) {
  const activeIdx = getStageIndex(status);

  return (
    <div className="flex items-center gap-1 overflow-x-auto py-2">
      {STAGES.map((stage, idx) => {
        const isComplete = activeIdx > idx;
        const isActive = activeIdx === idx && !TERMINAL_STATUSES.includes(status);
        const isDone = status === 'completed' && stage.key === 'completed';

        return (
          <div key={stage.key} className="flex items-center gap-1">
            {idx > 0 && (
              <div className={cn('w-6 h-px', isComplete || isDone ? 'bg-accent' : 'bg-border')} />
            )}
            <div className="flex flex-col items-center gap-1 min-w-[60px]">
              <span
                className={cn(
                  'w-3 h-3 rounded-full border-2 transition-all',
                  (isComplete || isDone) && 'bg-accent border-accent',
                  isActive && 'border-accent bg-accent/40 animate-pulse',
                  !isComplete && !isActive && !isDone && 'border-muted-foreground/40 bg-transparent',
                )}
              />
              <span className={cn(
                'text-[10px] leading-tight text-center',
                (isComplete || isDone) && 'text-accent font-medium',
                isActive && 'text-accent font-medium',
                !isComplete && !isActive && !isDone && 'text-muted-foreground',
              )}>
                {stage.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Budget Meter ────────────────────────────────────────────────────

function BudgetMeter({ spent, budget }: { spent: number; budget: number }) {
  const pct = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0;
  const color = pct > 80 ? 'bg-red-500' : pct > 50 ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">Budget</span>
        <span className="text-foreground font-medium">
          {formatCost(spent)} / {formatCost(budget)}
        </span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full transition-all duration-500', color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ─── Squad View ──────────────────────────────────────────────────────

function SquadView({ agents }: { agents: SquadAgent[] }) {
  if (agents.length === 0) return null;

  return (
    <div className="space-y-2">
      <span className="text-xs font-medium text-muted-foreground">Squad</span>
      <div className="flex flex-wrap gap-2">
        {agents.map((agent) => (
          <div
            key={agent.id}
            title={`${agent.role} — ${agent.status}${agent.output_summary ? ': ' + agent.output_summary : ''}`}
            className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-muted/40 border border-border text-xs"
          >
            <Bot size={12} className="text-muted-foreground shrink-0" />
            <span className="text-foreground truncate max-w-[100px]">{agent.role}</span>
            <span
              className={cn(
                'w-2 h-2 rounded-full shrink-0',
                agent.status === 'running' && 'bg-green-400 animate-pulse',
                agent.status === 'completed' && 'bg-green-400',
                agent.status === 'failed' && 'bg-red-400',
                agent.status === 'pending' && 'bg-zinc-500',
              )}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────

function PageSkeleton() {
  const pulse = 'animate-pulse rounded bg-muted/50';
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className={cn(pulse, 'h-8 w-48')} />
        <div className={cn(pulse, 'h-10 w-32')} />
      </div>
      <div className={cn(pulse, 'h-48')} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={cn(pulse, 'h-64')} />
        <div className={cn(pulse, 'h-64')} />
      </div>
    </div>
  );
}

// ─── Empty State ─────────────────────────────────────────────────────

function EmptyState({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mb-4">
        <Sparkles size={28} className="text-accent" />
      </div>
      <h2 className="text-lg font-semibold text-foreground mb-2">CoCo Builds Itself</h2>
      <p className="text-sm text-muted-foreground max-w-md mb-6 leading-relaxed">
        Start a self-improvement cycle and CoCo will spawn a 10-agent product squad to
        analyze its own codebase, identify improvements, and build them in isolated git worktrees
        for your review.
      </p>
      <button
        onClick={onStart}
        className="px-5 py-2.5 rounded-lg bg-accent text-accent-foreground hover:opacity-90 transition-opacity font-medium text-sm flex items-center gap-2"
      >
        <Zap size={14} />
        Start First Cycle
      </button>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────

export default function SelfImprovePage() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCycleId, setSelectedCycleId] = useState<string | null>(null);

  // Active cycle
  const { data: activeCycle, isLoading: activeLoading } = useQuery({
    queryKey: ['self-improve', 'active'],
    queryFn: () => apiFetch<Cycle>('/self-improve/cycles/active').catch(() => null),
    refetchInterval: (query) => {
      const cycle = query.state.data;
      if (cycle && !TERMINAL_STATUSES.includes(cycle.status)) return 3000;
      return false;
    },
  });

  // All cycles
  const { data: allCycles = [], isLoading: cyclesLoading } = useQuery({
    queryKey: ['self-improve', 'cycles'],
    queryFn: () => apiFetch<Cycle[]>('/self-improve/cycles'),
  });

  // Agents for active cycle
  const { data: agents = [] } = useQuery({
    queryKey: ['self-improve', 'agents', activeCycle?.id],
    queryFn: () => apiFetch<SquadAgent[]>(`/self-improve/cycles/${activeCycle!.id}/agents`),
    enabled: !!activeCycle?.id,
    refetchInterval: activeCycle && !TERMINAL_STATUSES.includes(activeCycle.status) ? 3000 : false,
  });

  // Selected past cycle detail
  const { data: selectedCycle } = useQuery({
    queryKey: ['self-improve', 'cycle', selectedCycleId],
    queryFn: () => apiFetch<Cycle>(`/self-improve/cycles/${selectedCycleId}`),
    enabled: !!selectedCycleId && selectedCycleId !== activeCycle?.id,
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: () => apiPost(`/self-improve/cycles/${activeCycle!.id}/cancel`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['self-improve'] });
      toast({ title: 'Cycle cancelled' });
    },
    onError: (err) => toast({ title: 'Cancel failed', description: String(err), variant: 'destructive' }),
  });

  // Determine which cycle to show improvements for
  const displayCycle = selectedCycleId && selectedCycleId !== activeCycle?.id ? selectedCycle : activeCycle;
  const pastCycles = useMemo(
    () => allCycles.filter((c) => c.id !== activeCycle?.id && TERMINAL_STATUSES.includes(c.status)),
    [allCycles, activeCycle?.id],
  );

  const isLoading = activeLoading || cyclesLoading;

  if (isLoading) return <PageSkeleton />;

  const hasNoCycles = !activeCycle && allCycles.length === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles size={20} className="text-accent" />
          <h1 className="text-xl font-bold text-foreground">Self-Improve</h1>
          {activeCycle && !TERMINAL_STATUSES.includes(activeCycle.status) && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-accent/20 text-accent animate-pulse">
              ACTIVE
            </span>
          )}
        </div>
        {!hasNoCycles && (
          <button
            onClick={() => setDialogOpen(true)}
            disabled={!!activeCycle && !TERMINAL_STATUSES.includes(activeCycle.status)}
            className="px-4 py-2 rounded-lg bg-accent text-accent-foreground hover:opacity-90 transition-opacity font-medium text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Zap size={14} />
            Start Cycle
          </button>
        )}
      </div>

      {/* Empty state */}
      {hasNoCycles && <EmptyState onStart={() => setDialogOpen(true)} />}

      {/* Active cycle panel */}
      {activeCycle && !TERMINAL_STATUSES.includes(activeCycle.status) && (
        <div className="bg-card rounded-xl border border-border p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">Active Cycle</span>
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
            >
              <XCircle size={14} />
              Cancel
            </button>
          </div>

          <StageStepper status={activeCycle.status} />
          <BudgetMeter spent={activeCycle.spent_usd} budget={activeCycle.budget_usd} />
          <SquadView agents={agents} />

          {activeCycle.error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 p-3 text-xs text-red-400">
              {activeCycle.error}
            </div>
          )}
        </div>
      )}

      {/* Completed active cycle summary */}
      {activeCycle && TERMINAL_STATUSES.includes(activeCycle.status) && (
        <div className="bg-card rounded-xl border border-border p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">
              Latest Cycle — {activeCycle.status.charAt(0).toUpperCase() + activeCycle.status.slice(1)}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatCost(activeCycle.spent_usd)} / {formatCost(activeCycle.budget_usd)}
            </span>
          </div>
          <BudgetMeter spent={activeCycle.spent_usd} budget={activeCycle.budget_usd} />
        </div>
      )}

      {/* Improvements grid */}
      {displayCycle && displayCycle.improvements.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Inbox size={16} className="text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              Improvements
              {displayCycle.status === 'awaiting_approval' && (
                <span className="ml-2 text-xs font-normal text-amber-400">Action required</span>
              )}
            </h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {displayCycle.improvements.map((imp) => (
              <ImprovementCard
                key={imp.id}
                improvement={imp}
                highlight={displayCycle.status === 'awaiting_approval' && imp.status === 'awaiting_approval'}
              />
            ))}
          </div>
        </div>
      )}

      {/* Selected past cycle back button */}
      {selectedCycleId && selectedCycleId !== activeCycle?.id && (
        <button
          onClick={() => setSelectedCycleId(null)}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Clear selection
        </button>
      )}

      {/* Cycle history */}
      <CycleHistory
        cycles={pastCycles}
        onSelectCycle={(id) => setSelectedCycleId(id)}
      />

      {/* Dialog */}
      <CycleControl open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
