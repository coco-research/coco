/**
 * Briefing store — tracks the latest server-pushed briefing watermark.
 *
 * TanStack Query owns the actual briefing payload (it's a fetched resource);
 * this store only carries ephemeral SSE-driven signal so components can react
 * to "the briefing changed" without re-fetching on a polling timer.
 */

import { create } from 'zustand';

interface BriefingState {
  latestBriefingId: string | null;
  latestUpdatedAt: string | null;
  /** Bump when an SSE briefing.updated arrives. */
  markUpdated: (briefingId: string, ts: string) => void;
  reset: () => void;
}

export const useBriefingStore = create<BriefingState>((set) => ({
  latestBriefingId: null,
  latestUpdatedAt: null,
  markUpdated: (briefingId, ts) =>
    set({ latestBriefingId: briefingId, latestUpdatedAt: ts }),
  reset: () => set({ latestBriefingId: null, latestUpdatedAt: null }),
}));
