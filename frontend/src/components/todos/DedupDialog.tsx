import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Merge, Loader2, CheckCircle } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';
import type { Todo } from './TodoList';

interface DuplicateGroup {
  suggested_keep: Todo;
  duplicates: Todo[];
  similarity: number;
}

interface DedupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DedupDialog({ open, onOpenChange }: DedupDialogProps) {
  const qc = useQueryClient();
  const [threshold, setThreshold] = useState(0.75);
  const [selections, setSelections] = useState<Record<number, string>>({});
  const [merging, setMerging] = useState<number | 'all' | null>(null);
  const [merged, setMerged] = useState<Set<number>>(new Set());

  const { data: groups = [], isLoading } = useQuery<DuplicateGroup[]>({
    queryKey: ['todo-duplicates', threshold],
    queryFn: () => apiFetch<DuplicateGroup[]>(`/todos/duplicates?threshold=${threshold}`),
    enabled: open,
  });

  // Initialize selections with suggested_keep when groups load
  function getKeepId(groupIndex: number, group: DuplicateGroup): string {
    return selections[groupIndex] ?? group.suggested_keep.id;
  }

  function allTodosInGroup(group: DuplicateGroup): Todo[] {
    return [group.suggested_keep, ...group.duplicates];
  }

  async function handleMerge(groupIndex: number) {
    const group = groups[groupIndex];
    if (!group) return;

    const keepId = getKeepId(groupIndex, group);
    const removeIds = allTodosInGroup(group)
      .filter((t) => t.id !== keepId)
      .map((t) => t.id);

    setMerging(groupIndex);
    try {
      await apiPost('/todos/merge', { keep_id: keepId, remove_ids: removeIds });
      setMerged((prev) => new Set([...prev, groupIndex]));
      void qc.invalidateQueries({ queryKey: ['todos'] });
    } finally {
      setMerging(null);
    }
  }

  async function handleMergeAll() {
    setMerging('all');
    try {
      for (let i = 0; i < groups.length; i++) {
        if (merged.has(i)) continue;
        const group = groups[i];
        const keepId = getKeepId(i, group);
        const removeIds = allTodosInGroup(group)
          .filter((t) => t.id !== keepId)
          .map((t) => t.id);
        await apiPost('/todos/merge', { keep_id: keepId, remove_ids: removeIds });
        setMerged((prev) => new Set([...prev, i]));
      }
      void qc.invalidateQueries({ queryKey: ['todos'] });
    } finally {
      setMerging(null);
    }
  }

  const unmergedCount = groups.filter((_, i) => !merged.has(i)).length;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[680px] max-w-[95vw] max-h-[80vh] bg-card border border-border rounded-2xl shadow-2xl z-50 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-border shrink-0">
            <div>
              <Dialog.Title className="text-lg font-semibold text-foreground">
                Find Duplicates
              </Dialog.Title>
              <p className="text-xs text-muted-foreground mt-0.5">
                Review and merge near-duplicate todos
              </p>
            </div>
            <Dialog.Close asChild>
              <button className="p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors">
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
            <div className="flex items-center gap-3">
              <label className="text-xs text-muted-foreground">Threshold:</label>
              <input
                type="range"
                min={0.5}
                max={0.95}
                step={0.05}
                value={threshold}
                onChange={(e) => {
                  setThreshold(parseFloat(e.target.value));
                  setMerged(new Set());
                  setSelections({});
                }}
                className="w-28 accent-accent"
              />
              <span className="text-xs font-mono text-foreground w-10">
                {Math.round(threshold * 100)}%
              </span>
            </div>
            {unmergedCount > 1 && (
              <button
                onClick={() => void handleMergeAll()}
                disabled={merging !== null}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md bg-accent text-accent-foreground font-medium hover:bg-accent/80 shadow-sm transition-colors',
                  merging !== null && 'opacity-50 cursor-not-allowed',
                )}
              >
                {merging === 'all' ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Merge className="h-3.5 w-3.5" />
                )}
                Merge All ({unmergedCount})
              </button>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-12 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                Scanning for duplicates...
              </div>
            ) : groups.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <CheckCircle className="h-10 w-10 mb-3 opacity-40" />
                <p className="text-sm font-medium">No duplicates found</p>
                <p className="text-xs mt-1">
                  Try lowering the threshold to find more matches.
                </p>
              </div>
            ) : (
              groups.map((group, gi) => {
                const isMerged = merged.has(gi);
                const keepId = getKeepId(gi, group);
                const allTodos = allTodosInGroup(group);

                return (
                  <div
                    key={gi}
                    className={cn(
                      'border border-border rounded-xl p-4 transition-opacity',
                      isMerged && 'opacity-40',
                    )}
                  >
                    {/* Group header */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground">
                          {allTodos.length} similar todos
                        </span>
                        <span className="text-xs bg-warning/20 text-warning px-2 py-0.5 rounded-full font-medium">
                          {Math.round(group.similarity * 100)}% similar
                        </span>
                      </div>
                      {!isMerged && (
                        <button
                          onClick={() => void handleMerge(gi)}
                          disabled={merging !== null}
                          className={cn(
                            'flex items-center gap-1.5 px-3 py-1 text-xs rounded-md bg-accent text-accent-foreground font-medium hover:bg-accent/80 transition-colors',
                            merging !== null && 'opacity-50 cursor-not-allowed',
                          )}
                        >
                          {merging === gi ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Merge className="h-3 w-3" />
                          )}
                          Merge
                        </button>
                      )}
                      {isMerged && (
                        <span className="flex items-center gap-1 text-xs text-green-500 font-medium">
                          <CheckCircle className="h-3.5 w-3.5" />
                          Merged
                        </span>
                      )}
                    </div>

                    {/* Todo list with radio selection */}
                    <div className="space-y-1.5">
                      {allTodos.map((todo) => (
                        <label
                          key={todo.id}
                          className={cn(
                            'flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors',
                            keepId === todo.id
                              ? 'bg-accent/20 border border-accent/30'
                              : 'hover:bg-accent/10 border border-transparent',
                            isMerged && 'cursor-default',
                          )}
                        >
                          <input
                            type="radio"
                            name={`dedup-group-${gi}`}
                            value={todo.id}
                            checked={keepId === todo.id}
                            disabled={isMerged}
                            onChange={() =>
                              setSelections((prev) => ({ ...prev, [gi]: todo.id }))
                            }
                            className="accent-accent shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <span className="text-sm truncate block">{todo.title}</span>
                            <div className="flex items-center gap-2 mt-0.5">
                              {todo.owner && (
                                <span className="text-[10px] text-muted-foreground">
                                  {todo.owner}
                                </span>
                              )}
                              {todo.due_date && (
                                <span className="text-[10px] text-muted-foreground">
                                  due {todo.due_date}
                                </span>
                              )}
                              {todo.priority && (
                                <span className="text-[10px] text-muted-foreground capitalize">
                                  {todo.priority}
                                </span>
                              )}
                              <span className="text-[10px] text-muted-foreground/60">
                                {todo.status}
                              </span>
                            </div>
                          </div>
                          {keepId === todo.id && (
                            <span className="text-[10px] font-medium text-accent-foreground bg-accent/30 rounded px-1.5 py-0.5 shrink-0">
                              Keep
                            </span>
                          )}
                        </label>
                      ))}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-5 py-3 border-t border-border text-xs text-muted-foreground shrink-0">
            <span>
              {groups.length} duplicate group{groups.length !== 1 ? 's' : ''} found
            </span>
            <span>{merged.size} merged</span>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
