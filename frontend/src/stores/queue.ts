/**
 * Decision queue store — optimistic local state for the approval queue.
 *
 * Holds optimistic decisions awaiting server confirmation. Cleared on
 * `platform.epoch` flip (see `sse/client.ts`).
 */

import { create } from 'zustand';

export type OptimisticDecision = 'approve' | 'reject' | 'defer';

interface QueueState {
  /** Optimistic decisions keyed by queue item id. */
  optimistic: Record<string, OptimisticDecision>;
  /** Total pending item count, server-pushed via SSE. */
  pendingCount: number;
  setOptimistic: (itemId: string, decision: OptimisticDecision) => void;
  clearOptimistic: (itemId: string) => void;
  clearAllOptimistic: () => void;
  setPendingCount: (n: number) => void;
}

export const useQueueStore = create<QueueState>((set) => ({
  optimistic: {},
  pendingCount: 0,
  setOptimistic: (itemId, decision) =>
    set((s) => ({ optimistic: { ...s.optimistic, [itemId]: decision } })),
  clearOptimistic: (itemId) =>
    set((s) => {
      const next = { ...s.optimistic };
      delete next[itemId];
      return { optimistic: next };
    }),
  clearAllOptimistic: () => set({ optimistic: {} }),
  setPendingCount: (n) => set({ pendingCount: Math.max(0, n) }),
}));
