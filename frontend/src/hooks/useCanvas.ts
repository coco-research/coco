import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import type { CardData } from '../types/cards';

type CanvasMode = 'idle' | 'active' | 'transitioning';

interface CanvasState {
  mode: CanvasMode;
  cards: CardData[];
  previousCards: CardData[];
}

const AUTO_IDLE_MS = 30_000;
// Match the canvas-exit animation (300ms) plus a small buffer to avoid flicker
const TRANSITION_MS = 350;

export function useCanvas() {
  const [state, setState] = useState<CanvasState>({
    mode: 'idle',
    cards: [],
    previousCards: [],
  });

  const transitionTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const autoIdleTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Clean up all timers on unmount
  useEffect(() => {
    return () => {
      clearTimeout(transitionTimer.current);
      clearTimeout(autoIdleTimer.current);
    };
  }, []);

  const resetAutoIdle = useCallback(() => {
    clearTimeout(autoIdleTimer.current);
    autoIdleTimer.current = setTimeout(() => {
      // Transition out, then go idle
      setState((prev) => ({
        ...prev,
        mode: 'transitioning',
        previousCards: prev.cards,
      }));
      transitionTimer.current = setTimeout(() => {
        setState({ mode: 'idle', cards: [], previousCards: [] });
      }, TRANSITION_MS);
    }, AUTO_IDLE_MS);
  }, []);

  const showCards = useCallback(
    (cards: CardData[]) => {
      clearTimeout(transitionTimer.current);
      clearTimeout(autoIdleTimer.current);

      setState((prev) => ({
        mode: 'transitioning',
        cards,
        previousCards: prev.cards,
      }));

      transitionTimer.current = setTimeout(() => {
        setState((prev) => ({ ...prev, mode: 'active' }));
        resetAutoIdle();
      }, TRANSITION_MS);
    },
    [resetAutoIdle],
  );

  const dismiss = useCallback(() => {
    clearTimeout(transitionTimer.current);
    clearTimeout(autoIdleTimer.current);

    setState((prev) => ({
      ...prev,
      mode: 'transitioning',
      previousCards: prev.cards,
    }));

    transitionTimer.current = setTimeout(() => {
      setState({ mode: 'idle', cards: [], previousCards: [] });
    }, TRANSITION_MS);
  }, []);

  return useMemo(() => ({
    mode: state.mode,
    cards: state.cards,
    previousCards: state.previousCards,
    showCards,
    dismiss,
    isIdle: state.mode === 'idle',
  }), [state.mode, state.cards, state.previousCards, showCards, dismiss]);
}
