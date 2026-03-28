import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useScope } from '../context/ScopeContext';
import { Target, Plus, ChevronRight, Check } from 'lucide-react';
import { cn, timeAgo } from '../lib/utils';
import { InlineEditor } from '../components/shared/InlineEditor';
import { PropertiesPanel } from '../components/shared/PropertiesPanel';
import { PropertyField } from '../components/shared/PropertyField';

interface Goal {
  id: string;
  project_id: string;
  parent_id: string | null;
  title: string;
  description: string | null;
  status: string;
  progress_pct: number;
  owner: string | null;
  target_date: string | null;
  created_at: string;
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
      <div
        className={cn(
          'h-full rounded-full transition-all',
          value >= 100 ? 'bg-success' : value >= 50 ? 'bg-info' : 'bg-warning'
        )}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

function GoalNode({ goal, allGoals, depth = 0, onSelect, selectedId }: { goal: Goal; allGoals: Goal[]; depth?: number; onSelect: (goal: Goal) => void; selectedId: string | null }) {
  const [expanded, setExpanded] = useState(true);
  const children = allGoals.filter(g => g.parent_id === goal.id);
  const hasChildren = children.length > 0;

  return (
    <div>
      <div
        onClick={() => onSelect(goal)}
        className={cn(
          "group flex items-center gap-2 px-3 py-2 hover:bg-accent/50 rounded-md cursor-pointer transition-colors",
          selectedId === goal.id && "bg-accent/30",
        )}
        style={{ paddingLeft: `${depth * 24 + 12}px` }}
      >
        {hasChildren ? (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="shrink-0 p-0.5 rounded hover:bg-accent"
          >
            <ChevronRight size={14} className={cn('transition-transform text-muted-foreground', expanded && 'rotate-90')} />
          </button>
        ) : (
          <div className="w-5 shrink-0" />
        )}

        {goal.status === 'achieved' ? (
          <Check size={14} className="text-success shrink-0" />
        ) : (
          <Target size={14} className="text-muted-foreground shrink-0" />
        )}

        <InlineEditor
          value={goal.title}
          onSave={async (title) => {
            await fetch(`/api/goals/${goal.id}`, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ title }),
            });
          }}
          as="span"
          className={cn(
            'text-sm flex-1 truncate',
            goal.status === 'achieved' && 'line-through text-muted-foreground',
            goal.status === 'dropped' && 'line-through text-muted-foreground opacity-50'
          )}
        />

        <ProgressBar value={goal.progress_pct} />

        <span className="text-[10px] text-muted-foreground tabular-nums">{goal.progress_pct}%</span>

        {goal.owner && (
          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
            {goal.owner}
          </span>
        )}
      </div>

      {hasChildren && expanded && (
        <div>
          {children.map(child => (
            <GoalNode key={child.id} goal={child} allGoals={allGoals} depth={depth + 1} onSelect={onSelect} selectedId={selectedId} />
          ))}
        </div>
      )}
    </div>
  );
}

function AddGoalForm({ projectId, onClose }: { projectId: string | null; onClose: () => void }) {
  const [title, setTitle] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/goals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, project_id: projectId, status: 'active', progress_pct: 0 }),
      });
      if (!res.ok) throw new Error('Failed to create goal');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      onClose();
    },
  });

  return (
    <div className="flex items-center gap-2 p-3 border border-border rounded-lg bg-card">
      <input
        type="text"
        value={title}
        onChange={e => setTitle(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && title.trim()) mutation.mutate(); if (e.key === 'Escape') onClose(); }}
        placeholder="Goal title..."
        className="flex-1 text-sm bg-transparent outline-none placeholder:text-muted-foreground"
        autoFocus
      />
      <button
        onClick={() => { if (title.trim()) mutation.mutate(); }}
        disabled={!title.trim() || mutation.isPending}
        className="px-3 py-1 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50"
      >
        Add
      </button>
      <button
        onClick={onClose}
        className="px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
      >
        Cancel
      </button>
    </div>
  );
}

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'achieved', label: 'Achieved' },
  { value: 'dropped', label: 'Dropped' },
];

export default function GoalsPage() {
  const { selectedNodeId, scopeProjectIds } = useScope();
  const [showAdd, setShowAdd] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);

  const queryClient = useQueryClient();

  const { data: goals = [], isLoading } = useQuery<Goal[]>({
    queryKey: ['goals', selectedNodeId, scopeProjectIds],
    queryFn: async () => {
      const url = scopeProjectIds.length === 1
        ? `/api/goals?project_id=${scopeProjectIds[0]}`
        : scopeProjectIds.length > 1
          ? `/api/goals?project_ids=${scopeProjectIds.join(',')}`
          : '/api/goals';
      const res = await fetch(url);
      if (!res.ok) return [];
      return res.json();
    },
  });

  const rootGoals = goals.filter(g => !g.parent_id);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Goals</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {goals.length} goal{goals.length !== 1 ? 's' : ''} tracked
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
        >
          <Plus size={14} />
          New Goal
        </button>
      </div>

      {showAdd && (
        <AddGoalForm projectId={scopeProjectIds[0] ?? null} onClose={() => setShowAdd(false)} />
      )}

      {/* Goal Tree */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-10 bg-muted/50 rounded-md animate-pulse" />
          ))}
        </div>
      ) : rootGoals.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <Target size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No goals yet</p>
          <p className="text-xs mt-1">Add a goal to start tracking progress.</p>
        </div>
      ) : (
        <div className="border border-border rounded-xl overflow-hidden divide-y divide-border">
          {rootGoals.map(goal => (
            <GoalNode key={goal.id} goal={goal} allGoals={goals} onSelect={setSelectedGoal} selectedId={selectedGoal?.id ?? null} />
          ))}
        </div>
      )}

      {/* Goal detail slide-out */}
      {selectedGoal && (
        <GoalDetailPanel
          goal={selectedGoal}
          allGoals={goals}
          onClose={() => setSelectedGoal(null)}
          onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ['goals'] });
          }}
        />
      )}
    </div>
  );
}

/* ---------- Goal Detail Panel ---------- */

interface GoalDetailPanelProps {
  goal: Goal;
  allGoals: Goal[];
  onClose: () => void;
  onSaved: () => void;
}

function GoalDetailPanel({ goal, allGoals, onClose, onSaved }: GoalDetailPanelProps) {
  const linkedTodos = allGoals.filter(g => g.parent_id === goal.id);

  const handleSave = async (field: string, value: string) => {
    try {
      await fetch(`/api/goals/${goal.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: value }),
      });
      onSaved();
    } catch {
      // ignore
    }
  };

  const statusLabel = goal.status.charAt(0).toUpperCase() + goal.status.slice(1);

  return (
    <PropertiesPanel
      open={true}
      onClose={onClose}
      title={goal.title}
      subtitle={`${statusLabel} \u00b7 ${goal.progress_pct}% complete`}
    >
      {/* Properties */}
      <div className="space-y-0">
        <PropertyField
          label="Title"
          value={goal.title}
          onSave={(v) => handleSave('title', v)}
        />
        <PropertyField
          label="Description"
          value={goal.description}
          onSave={(v) => handleSave('description', v)}
          type="textarea"
          placeholder="Describe this goal..."
        />
        <PropertyField
          label="Status"
          value={goal.status}
          onSave={(v) => handleSave('status', v)}
          type="select"
          options={STATUS_OPTIONS}
        />
        <div className="mb-3">
          <span className="block text-xs text-muted-foreground mb-0.5">Progress</span>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  goal.progress_pct >= 100 ? 'bg-success' : goal.progress_pct >= 50 ? 'bg-info' : 'bg-warning'
                )}
                style={{ width: `${Math.min(goal.progress_pct, 100)}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground tabular-nums">{goal.progress_pct}%</span>
          </div>
        </div>
        <PropertyField
          label="Owner"
          value={goal.owner}
          onSave={(v) => handleSave('owner', v)}
          placeholder="Assign an owner..."
        />
        <PropertyField
          label="Target date"
          value={goal.target_date}
          onSave={(v) => handleSave('target_date', v)}
          placeholder="YYYY-MM-DD"
        />
        <PropertyField label="Created" value={goal.created_at ? timeAgo(goal.created_at) : null} />
      </div>

      {/* Sub-goals / linked items */}
      {linkedTodos.length > 0 && (
        <div className="border-t border-border pt-4 mt-4">
          <span className="block text-xs text-muted-foreground mb-2">Sub-goals ({linkedTodos.length})</span>
          <div className="space-y-1">
            {linkedTodos.map(sub => (
              <div key={sub.id} className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-muted/30">
                {sub.status === 'achieved' ? (
                  <Check size={12} className="text-success shrink-0" />
                ) : (
                  <Target size={12} className="text-muted-foreground shrink-0" />
                )}
                <span className={cn(
                  'text-xs flex-1 truncate',
                  sub.status === 'achieved' && 'line-through text-muted-foreground',
                )}>
                  {sub.title}
                </span>
                <span className="text-[10px] text-muted-foreground tabular-nums">{sub.progress_pct}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </PropertiesPanel>
  );
}
