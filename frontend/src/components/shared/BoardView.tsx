/**
 * BoardView — Generic kanban-style columnar layout.
 * Renders items grouped by state in columns. No drag-and-drop, just
 * transition buttons on each card.
 */

import { cn } from '../../lib/utils';
import {
  STATE_LABELS,
  STATE_COLORS,
} from '../../lib/state-machine';
import { TransitionButtons } from './TransitionButtons';

interface BoardItem {
  id: string;
  title: string;
  status: string;
  priority: string;
  owner?: string | null;
  agent_id?: string | null;
  due_date?: string | null;
}

interface BoardViewProps<T extends BoardItem> {
  items: T[];
  states: readonly string[];
  kind: 'todo' | 'task';
  onTransition: (id: string, toState: string) => void;
  isPending?: boolean;
  onSelect?: (item: T) => void;
}

const PRIORITY_DOT: Record<string, string> = {
  high: 'bg-red-500',
  medium: 'bg-amber-500',
  low: 'bg-zinc-400',
};

export function BoardView<T extends BoardItem>({
  items,
  states,
  kind,
  onTransition,
  isPending = false,
  onSelect,
}: BoardViewProps<T>) {
  // Group items by status
  const grouped = new Map<string, T[]>();
  for (const state of states) {
    grouped.set(state, []);
  }
  for (const item of items) {
    const bucket = grouped.get(item.status);
    if (bucket) {
      bucket.push(item);
    } else {
      // Legacy/unknown status — put in first column
      grouped.get(states[0])?.push(item);
    }
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-4 h-full">
      {states.map((state) => {
        const stateItems = grouped.get(state) ?? [];
        const colors = STATE_COLORS[state];

        return (
          <div
            key={state}
            className="flex flex-col min-w-[260px] max-w-[320px] flex-1 bg-muted/30 rounded-xl border border-border/50"
          >
            {/* Column header */}
            <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border/50">
              <span
                className={cn(
                  'h-2.5 w-2.5 rounded-full shrink-0',
                  colors?.dot ?? 'bg-muted-foreground',
                )}
              />
              <span className="text-xs font-semibold text-foreground uppercase tracking-wide">
                {STATE_LABELS[state] ?? state}
              </span>
              <span className="ml-auto text-[10px] font-medium text-muted-foreground bg-muted/50 rounded-full px-1.5 py-0.5">
                {stateItems.length}
              </span>
            </div>

            {/* Cards */}
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {stateItems.length === 0 ? (
                <div className="text-xs text-muted-foreground text-center py-6 opacity-50">
                  No items
                </div>
              ) : (
                stateItems.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => onSelect?.(item)}
                    className={cn(
                      'bg-card border border-border rounded-lg p-3 space-y-2 transition-all',
                      'hover:shadow-sm hover:border-border/80',
                      onSelect && 'cursor-pointer',
                    )}
                  >
                    {/* Title + priority dot */}
                    <div className="flex items-start gap-2">
                      <span
                        className={cn(
                          'h-2 w-2 rounded-full mt-1 shrink-0',
                          PRIORITY_DOT[item.priority] ?? 'bg-zinc-400',
                        )}
                        title={`${item.priority} priority`}
                      />
                      <span className="text-sm text-foreground line-clamp-2">{item.title}</span>
                    </div>

                    {/* Meta row */}
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                      {item.owner && <span>{item.owner}</span>}
                      {item.due_date && (
                        <span>
                          {new Date(item.due_date).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      )}
                    </div>

                    {/* Transition buttons */}
                    <TransitionButtons
                      currentState={item.status}
                      kind={kind}
                      onTransition={(toState) => onTransition(item.id, toState)}
                      isPending={isPending}
                      size="sm"
                    />
                  </div>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
