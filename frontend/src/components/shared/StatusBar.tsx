/**
 * StatusBar — Kanban-style status count bar.
 * Shows columns with counts for each state in the lifecycle.
 */

import { cn } from '../../lib/utils';
import { STATE_LABELS, STATE_COLORS } from '../../lib/state-machine';

interface StatusBarProps<S extends string> {
  states: readonly S[];
  counts: Record<string, number>;
  activeFilter?: string;
  onFilterClick?: (state: string) => void;
}

export function StatusBar<S extends string>({
  states,
  counts,
  activeFilter,
  onFilterClick,
}: StatusBarProps<S>) {
  return (
    <div className="flex items-center gap-1 p-1 bg-card border border-border rounded-xl overflow-x-auto">
      {states.map((state) => {
        const count = counts[state] ?? 0;
        const colors = STATE_COLORS[state];
        const isActive = activeFilter === state;

        return (
          <button
            key={state}
            onClick={() => onFilterClick?.(isActive ? '' : state)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap',
              isActive
                ? `${colors?.bg ?? 'bg-accent/50'} ${colors?.text ?? 'text-foreground'} shadow-sm`
                : 'text-muted-foreground hover:bg-accent/30',
            )}
          >
            <span
              className={cn('h-2 w-2 rounded-full shrink-0', colors?.dot ?? 'bg-muted-foreground')}
            />
            {STATE_LABELS[state] ?? state}
            <span
              className={cn(
                'inline-flex items-center justify-center h-5 min-w-[1.25rem] px-1 rounded-full text-[10px] font-semibold',
                isActive
                  ? `${colors?.bg ?? 'bg-accent/50'} ${colors?.text ?? 'text-foreground'}`
                  : 'bg-muted/50 text-muted-foreground',
              )}
            >
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
