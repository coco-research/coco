/**
 * DecisionCard — the focused card inside the Decision Deck (Zone 2).
 *
 * Pure presentational. Renders the four large hotkey buttons (1/2/3/4),
 * the source meta-line, and CoCo's reasoning blurb. Triage actions are
 * dispatched up via `onAction`.
 *
 * Mirrors the structure of DESIGN.md §1.3 + REFERENCE-IMPL/inbox-deck.tsx
 * `Decision` shape, but uses a lighter visual language matching the
 * `prototypes/redesign` mock.
 */

import { forwardRef, type ReactElement } from 'react';
import { cn } from '../../../lib/utils';

export type DecisionActionKey = 'approve' | 'reply' | 'delegate' | 'snooze';

export interface DecisionOption {
  key: DecisionActionKey;
  hotkey: '1' | '2' | '3' | '4';
  title: string;
  subtitle?: string;
  destructive?: boolean;
  disabled?: boolean;
}

export interface DecisionCardData {
  id: string;
  /** Optional short label ("Slack · #optro-eng · 5 min ago"). */
  sourceLabel?: string;
  /** Optional urgency badge ("Urgent · blocks standup"). */
  urgencyLabel?: string;
  fromName?: string;
  fromRole?: string;
  /** The "ask" — short imperative sentence. ≤80 chars recommended. */
  ask: string;
  /** Context paragraph — what CoCo knows about the situation. */
  context?: string;
  /** CoCo's recommendation paragraph (rendered with a "CoCo thinks" label). */
  reasoning?: string;
  options: [DecisionOption, DecisionOption, DecisionOption, DecisionOption];
}

export interface DecisionCardProps {
  decision: DecisionCardData;
  indexLabel: string; // e.g. "Card 1 of 3"
  onAction: (id: string, key: DecisionActionKey) => void;
  /** Cards in flight (optimistic) — disables the button row. */
  pending?: boolean;
}

export const DecisionCard = forwardRef<HTMLDivElement, DecisionCardProps>(
  function DecisionCard(props, ref): ReactElement {
    const { decision, indexLabel, onAction, pending } = props;

    return (
      <div
        ref={ref}
        role="article"
        tabIndex={0}
        aria-label={`Decision card: ${decision.ask}`}
        data-card-id={decision.id}
        data-pending={pending ? 'true' : 'false'}
        className={cn(
          'rounded-xl border border-border bg-card p-5 outline-none',
          'focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2',
          'transition-opacity',
          pending && 'opacity-60',
        )}
      >
        {/* Meta row */}
        <div className="flex items-center justify-between text-[11px] text-muted-foreground mb-3">
          <span className="font-medium">{indexLabel}</span>
          {decision.sourceLabel && <span>{decision.sourceLabel}</span>}
          {decision.urgencyLabel && (
            <span className="inline-flex items-center gap-1 rounded-full bg-destructive/10 text-destructive px-2 py-0.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-destructive" />
              {decision.urgencyLabel}
            </span>
          )}
        </div>

        {/* Sender */}
        {decision.fromName && (
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 rounded-full bg-muted text-foreground/80 flex items-center justify-center text-[10px] font-semibold">
              {decision.fromName
                .split(/\s+/)
                .slice(0, 2)
                .map((s) => s[0]?.toUpperCase() ?? '')
                .join('')}
            </div>
            <div className="text-xs">
              <span className="font-medium text-foreground">
                {decision.fromName}
              </span>
              {decision.fromRole && (
                <span className="text-muted-foreground"> · {decision.fromRole}</span>
              )}
            </div>
          </div>
        )}

        {/* Ask */}
        <h3 className="text-base font-semibold text-foreground leading-snug mb-2">
          {decision.ask}
        </h3>

        {decision.context && (
          <p className="text-sm text-foreground/80 leading-6 mb-3">
            {decision.context}
          </p>
        )}

        {decision.reasoning && (
          <div className="rounded-lg border border-border bg-muted/30 px-3 py-2.5 mb-4">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">
              CoCo thinks
            </div>
            <p className="text-xs text-foreground/80 leading-5">
              {decision.reasoning}
            </p>
          </div>
        )}

        {/* Actions */}
        <div
          role="group"
          aria-label="Triage actions"
          className="grid grid-cols-1 sm:grid-cols-2 gap-2"
        >
          {decision.options.map((opt) => (
            <button
              key={opt.key}
              type="button"
              disabled={opt.disabled === true || pending === true}
              data-hotkey={opt.hotkey}
              data-key={opt.key}
              data-destructive={opt.destructive ? 'true' : 'false'}
              onClick={() => onAction(decision.id, opt.key)}
              className={cn(
                'group flex items-start gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors',
                'border-border bg-background hover:bg-muted/50',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                opt.destructive && 'hover:border-destructive/40',
              )}
            >
              <kbd
                className={cn(
                  'shrink-0 inline-flex items-center justify-center w-6 h-6 rounded',
                  'border border-border bg-muted/50 text-[11px] font-semibold tabular-nums',
                  'text-muted-foreground group-hover:text-foreground',
                )}
                aria-hidden="true"
              >
                {opt.hotkey}
              </kbd>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-foreground truncate">
                  {opt.title}
                </div>
                {opt.subtitle && (
                  <div className="text-[11px] text-muted-foreground truncate">
                    {opt.subtitle}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  },
);

export default DecisionCard;
