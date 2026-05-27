/**
 * ResolvedLog — Zone 3 of the Inbox.
 *
 * Collapsible audit log of what's been resolved in the last 24h (whether
 * by the user or by CoCo's auto-handlers). Hidden by default; expanded
 * with `e` hotkey or click on the toggle.
 */

import type { ReactElement } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../../lib/utils';

export type ResolvedAction = 'approve' | 'reply' | 'delegate' | 'snooze' | 'auto';

export interface ResolvedItem {
  id: string;
  /** Short label of what was resolved. */
  text: string;
  /** Which action was taken. */
  action: ResolvedAction;
  /** Display string for the timestamp ("2 min ago"). */
  resolvedAt: string;
  /** Optional source label (e.g. "Slack · #optro"). */
  source?: string;
}

export interface ResolvedLogProps {
  items: ReadonlyArray<ResolvedItem>;
  expanded: boolean;
  onToggle: () => void;
  active?: boolean;
}

const ACTION_STYLES: Record<ResolvedAction, string> = {
  approve: 'bg-success/10 text-success',
  reply: 'bg-info/10 text-info',
  delegate: 'bg-warning/10 text-warning',
  snooze: 'bg-muted text-muted-foreground',
  auto: 'bg-muted text-muted-foreground',
};

export function ResolvedLog(props: ResolvedLogProps): ReactElement {
  const { items, expanded, onToggle, active } = props;
  const count = items.length;

  return (
    <section
      aria-label="Resolved decisions"
      data-active={active ? 'true' : 'false'}
      data-expanded={expanded ? 'true' : 'false'}
      className={cn(
        'rounded-xl border bg-card transition-colors',
        active ? 'border-primary/40' : 'border-border',
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className={cn(
          'w-full flex items-center justify-between gap-3 px-5 py-3 text-left',
          'hover:bg-muted/30 transition-colors rounded-xl',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60',
        )}
      >
        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">
            While you were heads-down
          </div>
          <div className="text-sm font-medium text-foreground mt-0.5">
            CoCo handled {count} thing{count === 1 ? '' : 's'}.{' '}
            <span className="text-muted-foreground font-normal">
              {expanded ? 'Tap to collapse.' : 'Tap to audit.'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <span>{expanded ? 'Collapse' : 'Expand'}</span>
          <ChevronDown
            size={14}
            className={cn(
              'transition-transform',
              expanded && 'rotate-180',
            )}
          />
        </div>
      </button>

      {expanded && (
        <ul className="divide-y divide-border border-t border-border">
          {count === 0 ? (
            <li className="px-5 py-4 text-xs text-muted-foreground italic">
              Nothing has been resolved yet today.
            </li>
          ) : (
            items.map((item) => (
              <li
                key={item.id}
                className="flex items-center gap-3 px-5 py-2.5"
                data-action={item.action}
              >
                <span
                  className={cn(
                    'shrink-0 text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded',
                    ACTION_STYLES[item.action],
                  )}
                >
                  {item.action}
                </span>
                <span className="flex-1 min-w-0 text-sm text-foreground truncate">
                  {item.text}
                </span>
                {item.source && (
                  <span className="text-[10px] text-muted-foreground shrink-0">
                    {item.source}
                  </span>
                )}
                <span className="text-[10px] text-muted-foreground shrink-0 tabular-nums">
                  {item.resolvedAt}
                </span>
              </li>
            ))
          )}
        </ul>
      )}
    </section>
  );
}

export default ResolvedLog;
