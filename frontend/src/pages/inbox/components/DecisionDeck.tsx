/**
 * DecisionDeck — Zone 2 of the Inbox.
 *
 * Holds a stack of `DecisionCard`s, but only the top one is interactive.
 * Renders a small peek of the next card behind, a progress strip, and the
 * keyboard-shortcut hint line.
 *
 * State ownership:
 *   - The active index is owned here (this component decides which card is
 *     "focused" within the stack).
 *   - The active **zone** is owned by the parent (`InboxPage`) since j/k
 *     navigation needs to move across all three zones.
 */

import { useCallback, useEffect, useRef, useState, type ReactElement } from 'react';
import { cn } from '../../../lib/utils';
import { DecisionCard } from './DecisionCard';
import type { DecisionActionKey, DecisionCardData } from './DecisionCard';

export interface DecisionDeckProps {
  decisions: ReadonlyArray<DecisionCardData>;
  /** Map of decision id → optimistic flag. */
  pending?: Record<string, boolean>;
  /** Fires when a hotkey or click triggers an action. */
  onAction: (decisionId: string, action: DecisionActionKey) => void;
  /** Active flag — parent toggles when user navigates via j/k. */
  active?: boolean;
  /** Imperative ref attached to the deck card for focus restoration on Esc. */
  cardRef?: React.MutableRefObject<HTMLElement | null>;
  /** Programmatic trigger from parent (1/2/3/4 from useKeyboardTriage). */
  onHotkeyRef?: React.MutableRefObject<((hk: '1' | '2' | '3' | '4') => void) | null>;
}

export function DecisionDeck(props: DecisionDeckProps): ReactElement {
  const { decisions, pending, onAction, active, cardRef, onHotkeyRef } = props;
  const [activeIndex, setActiveIndex] = useState(0);
  const innerCardRef = useRef<HTMLDivElement | null>(null);

  // Clamp activeIndex when decisions list shrinks (e.g. optimistic removal).
  useEffect(() => {
    if (decisions.length === 0) {
      setActiveIndex(0);
      return;
    }
    if (activeIndex >= decisions.length) {
      setActiveIndex(decisions.length - 1);
    }
  }, [decisions.length, activeIndex]);

  // Bubble the inner card ref up to the parent so Esc can restore focus.
  useEffect(() => {
    if (cardRef) {
      cardRef.current = innerCardRef.current;
    }
  });

  const activeDecision = decisions[activeIndex] ?? null;

  const triggerHotkey = useCallback(
    (hk: '1' | '2' | '3' | '4') => {
      if (!activeDecision) return;
      const opt = activeDecision.options.find((o) => o.hotkey === hk);
      if (!opt || opt.disabled) return;
      onAction(activeDecision.id, opt.key);
    },
    [activeDecision, onAction],
  );

  // Publish the imperative hotkey trigger to the parent.
  useEffect(() => {
    if (onHotkeyRef) {
      onHotkeyRef.current = triggerHotkey;
    }
    return () => {
      if (onHotkeyRef) onHotkeyRef.current = null;
    };
  }, [onHotkeyRef, triggerHotkey]);

  // Focus the active card when the deck becomes the active zone or the index
  // changes.
  useEffect(() => {
    if (!active) return;
    if (decisions.length === 0) return;
    innerCardRef.current?.focus();
  }, [active, activeIndex, decisions.length]);

  if (decisions.length === 0) {
    return (
      <section
        aria-label="Decision deck"
        className={cn(
          'rounded-xl border bg-card p-8 text-center transition-colors',
          active ? 'border-primary/40' : 'border-border',
        )}
        data-active={active ? 'true' : 'false'}
      >
        <h3 className="text-base font-semibold text-foreground">All clear</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Nothing needs your attention.
        </p>
        <div role="status" aria-live="polite" className="sr-only">
          Inbox empty
        </div>
      </section>
    );
  }

  const indexLabel = `Card ${activeIndex + 1} of ${decisions.length}`;
  const isPending = !!(pending && pending[activeDecision!.id]);

  return (
    <section
      aria-label="Decision deck"
      data-active={active ? 'true' : 'false'}
      className={cn(
        'relative rounded-xl border-2 transition-colors',
        active ? 'border-primary/40' : 'border-transparent',
        'p-0',
      )}
    >
      {/* Peek card stack behind (purely decorative). */}
      {decisions.length > 1 && (
        <>
          <div
            aria-hidden="true"
            className="absolute inset-x-6 top-2 h-3 rounded-t-xl border border-border bg-muted/40"
          />
          {decisions.length > 2 && (
            <div
              aria-hidden="true"
              className="absolute inset-x-10 top-0 h-2 rounded-t-xl border border-border bg-muted/30"
            />
          )}
        </>
      )}

      <div className="relative pt-4">
        <DecisionCard
          ref={innerCardRef}
          decision={activeDecision!}
          indexLabel={indexLabel}
          onAction={(id, key) => {
            onAction(id, key);
            // Auto-advance: parent will remove the card optimistically; if it
            // doesn't, advance locally so the user can keep triaging.
            setActiveIndex((i) => Math.min(i + 1, decisions.length - 1));
          }}
          pending={isPending}
        />
      </div>

      {/* Progress strip */}
      <div className="flex items-center justify-between px-2 pt-3">
        <div className="flex items-center gap-1.5">
          {decisions.map((_, i) => (
            <span
              key={i}
              className={cn(
                'w-1.5 h-1.5 rounded-full',
                i === activeIndex
                  ? 'bg-primary'
                  : i < activeIndex
                    ? 'bg-muted-foreground/40'
                    : 'bg-muted',
              )}
            />
          ))}
        </div>
        <div className="text-[11px] text-muted-foreground tabular-nums">
          {decisions.length - activeIndex - 1} more after this
        </div>
      </div>

      {/* Hotkey hint */}
      <div className="px-2 pt-2 text-[11px] text-muted-foreground flex flex-wrap gap-x-3 gap-y-1">
        <span>
          <kbd className="px-1 rounded border border-border bg-muted/30 font-mono">1</kbd>{' '}
          approve
        </span>
        <span>
          <kbd className="px-1 rounded border border-border bg-muted/30 font-mono">2</kbd>{' '}
          reply
        </span>
        <span>
          <kbd className="px-1 rounded border border-border bg-muted/30 font-mono">3</kbd>{' '}
          delegate
        </span>
        <span>
          <kbd className="px-1 rounded border border-border bg-muted/30 font-mono">4</kbd>{' '}
          snooze
        </span>
        <span>
          <kbd className="px-1 rounded border border-border bg-muted/30 font-mono">j</kbd>/
          <kbd className="px-1 rounded border border-border bg-muted/30 font-mono">k</kbd>{' '}
          zones
        </span>
        <span>
          <kbd className="px-1 rounded border border-border bg-muted/30 font-mono">e</kbd>{' '}
          expand resolved
        </span>
      </div>
    </section>
  );
}

export default DecisionDeck;
