/**
 * useKeyboardTriage — keyboard navigation + triage hotkeys for the Inbox 3-zone
 * deck.
 *
 * Implements DESIGN.md §1.3 + §6.1 (Inbox keyboard map):
 *   1 / 2 / 3 / 4   → triage actions on the focused deck card
 *   j / k           → zone navigation (briefing ↔ deck ↔ resolved)
 *   e               → toggle resolved zone expansion
 *   Esc             → return focus to the deck zone
 *
 * The hook owns transient UI state (active zone, resolved-expanded flag) and
 * exposes a `bindKeyDown` handler the parent attaches to the page-level
 * container. Triage actions are dispatched to the caller via `onTriage`.
 *
 * Pure presentational hook — does NOT call the API. Side-effect-confirmed
 * events come back via SSE (see `sse/dispatch.ts`).
 */

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type MutableRefObject,
} from 'react';

export type TriageActionKey = '1' | '2' | '3' | '4';
export type TriageAction = 'approve' | 'reply' | 'delegate' | 'snooze';
export type InboxZone = 'briefing' | 'deck' | 'resolved';

const ACTION_BY_HOTKEY: Record<TriageActionKey, TriageAction> = {
  '1': 'approve',
  '2': 'reply',
  '3': 'delegate',
  '4': 'snooze',
};

export interface UseKeyboardTriageOptions {
  /** Called when 1/2/3/4 is pressed while the deck zone is active. */
  onTriage: (action: TriageAction, hotkey: TriageActionKey) => void;
  /** When true, the deck has no card — hotkeys 1-4 are no-ops. */
  deckEmpty?: boolean;
  /** Disable all hotkeys (e.g. when a modal owns focus). Default false. */
  disabled?: boolean;
}

export interface UseKeyboardTriageReturn {
  activeZone: InboxZone;
  setActiveZone: (z: InboxZone) => void;
  resolvedExpanded: boolean;
  setResolvedExpanded: (v: boolean | ((p: boolean) => boolean)) => void;
  /** Attach to the page-level container element. */
  bindKeyDown: (e: KeyboardEvent<HTMLElement>) => void;
  /** Imperative ref the deck zone uses for focus restoration on Esc. */
  deckContainerRef: MutableRefObject<HTMLElement | null>;
  /** Number of keyboard hooks registered — exposed for diagnostics. */
  hookCount: number;
}

/**
 * Bundles the inbox triage hotkey state machine.
 *
 * `hookCount` reports the number of distinct key-binding categories handled
 * (currently 4: triage 1-4, zone j/k, expand e, escape) — exported so the
 * phase-6 status report can assert coverage.
 */
export function useKeyboardTriage(
  opts: UseKeyboardTriageOptions,
): UseKeyboardTriageReturn {
  const { onTriage, deckEmpty = false, disabled = false } = opts;

  const [activeZone, setActiveZone] = useState<InboxZone>('deck');
  const [resolvedExpanded, setResolvedExpanded] = useState<boolean>(false);
  const deckContainerRef = useRef<HTMLElement | null>(null);

  // Keep onTriage stable across renders so consumers don't have to memoize.
  const onTriageRef = useRef(onTriage);
  useEffect(() => {
    onTriageRef.current = onTriage;
  }, [onTriage]);

  const bindKeyDown = useCallback(
    (e: KeyboardEvent<HTMLElement>) => {
      if (disabled) return;
      // Ignore when typing in an input/textarea/contenteditable.
      const target = e.target as HTMLElement | null;
      if (target) {
        const tag = target.tagName;
        if (
          tag === 'INPUT' ||
          tag === 'TEXTAREA' ||
          target.isContentEditable
        ) {
          return;
        }
      }

      const key = e.key;

      // ── Triage hotkeys (only when deck zone active & has a card) ──
      if (key === '1' || key === '2' || key === '3' || key === '4') {
        if (activeZone !== 'deck') return;
        if (deckEmpty) return;
        const action = ACTION_BY_HOTKEY[key as TriageActionKey];
        e.preventDefault();
        onTriageRef.current(action, key as TriageActionKey);
        return;
      }

      // ── Zone navigation ──
      if (key === 'j') {
        e.preventDefault();
        setActiveZone((z) =>
          z === 'briefing' ? 'deck' : z === 'deck' ? 'resolved' : 'resolved',
        );
        return;
      }
      if (key === 'k') {
        e.preventDefault();
        setActiveZone((z) =>
          z === 'resolved' ? 'deck' : z === 'deck' ? 'briefing' : 'briefing',
        );
        return;
      }

      // ── Resolved zone expand ──
      if (key === 'e' || key === 'E') {
        e.preventDefault();
        setResolvedExpanded((v) => !v);
        return;
      }

      // ── Escape returns focus to deck ──
      if (key === 'Escape') {
        e.preventDefault();
        setActiveZone('deck');
        deckContainerRef.current?.focus();
        return;
      }
    },
    [activeZone, deckEmpty, disabled],
  );

  return {
    activeZone,
    setActiveZone,
    resolvedExpanded,
    setResolvedExpanded,
    bindKeyDown,
    deckContainerRef,
    hookCount: 4,
  };
}

export default useKeyboardTriage;
