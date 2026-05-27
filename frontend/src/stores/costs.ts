/**
 * Cost ledger store — live spend cents + budget breach flag.
 *
 * Updated from `costs.updated` / `costs.budget.breached` SSE events. Detailed
 * ledger rows are fetched via TanStack Query.
 */

import { create } from 'zustand';

interface CostsState {
  /** Cumulative cents for the active window. */
  cents: number;
  /** ISO timestamp of last update. */
  lastUpdatedAt: string | null;
  /** Breach details, if any. */
  breach: { budgetId: string; pct: number; ts: string } | null;
  setCents: (cents: number, ts: string) => void;
  setBreach: (budgetId: string, pct: number, ts: string) => void;
  clearBreach: () => void;
  reset: () => void;
}

export const useCostsStore = create<CostsState>((set) => ({
  cents: 0,
  lastUpdatedAt: null,
  breach: null,
  setCents: (cents, ts) =>
    set({ cents: Math.max(0, cents), lastUpdatedAt: ts }),
  setBreach: (budgetId, pct, ts) =>
    set({ breach: { budgetId, pct, ts } }),
  clearBreach: () => set({ breach: null }),
  reset: () => set({ cents: 0, lastUpdatedAt: null, breach: null }),
}));
