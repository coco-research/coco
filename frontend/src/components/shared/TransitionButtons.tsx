/**
 * TransitionButtons — Show valid next-state transitions as a button group.
 */

import { cn } from '../../lib/utils';
import {
  TODO_TRANSITIONS,
  TASK_TRANSITIONS,
  TRANSITION_SHORT_LABELS,
  STATE_COLORS,
} from '../../lib/state-machine';

interface TransitionButtonsProps {
  currentState: string;
  kind: 'todo' | 'task';
  onTransition: (toState: string) => void;
  isPending?: boolean;
  size?: 'sm' | 'md';
}

export function TransitionButtons({
  currentState,
  kind,
  onTransition,
  isPending = false,
  size = 'sm',
}: TransitionButtonsProps) {
  const transitions =
    kind === 'todo'
      ? (TODO_TRANSITIONS as Record<string, string[]>)
      : (TASK_TRANSITIONS as Record<string, string[]>);

  const allowed = transitions[currentState] ?? [];

  if (allowed.length === 0) return null;

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {allowed.map((toState) => {
        const colors = STATE_COLORS[toState];
        return (
          <button
            key={toState}
            onClick={(e) => {
              e.stopPropagation();
              onTransition(toState);
            }}
            disabled={isPending}
            className={cn(
              'rounded-md font-medium transition-all border',
              size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-xs',
              colors
                ? `${colors.bg} ${colors.text} border-transparent hover:opacity-80`
                : 'bg-accent/50 text-muted-foreground border-border hover:bg-accent/70',
              isPending && 'opacity-50 cursor-not-allowed',
            )}
          >
            {TRANSITION_SHORT_LABELS[toState] ?? toState}
          </button>
        );
      })}
    </div>
  );
}
