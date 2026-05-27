/**
 * Agents store — live per-agent status map driven by SSE.
 *
 * Detailed agent records (history, logs) are fetched via TanStack Query; this
 * store carries only the current status so UI badges update without polling.
 */

import { create } from 'zustand';

export type AgentLiveStatus =
  | 'idle'
  | 'running'
  | 'paused'
  | 'failed'
  | 'completed';

interface AgentRuntime {
  status: AgentLiveStatus;
  /** ISO timestamp of last status change. */
  ts: string;
  /** Optional error message (set when status === 'failed'). */
  error?: string;
}

interface AgentsState {
  /** Live runtime map keyed by agent_id. */
  runtime: Record<string, AgentRuntime>;
  setStatus: (
    agentId: string,
    status: AgentLiveStatus,
    ts: string,
    error?: string,
  ) => void;
  remove: (agentId: string) => void;
  reset: () => void;
}

export const useAgentsStore = create<AgentsState>((set) => ({
  runtime: {},
  setStatus: (agentId, status, ts, error) =>
    set((s) => ({
      runtime: { ...s.runtime, [agentId]: { status, ts, error } },
    })),
  remove: (agentId) =>
    set((s) => {
      const next = { ...s.runtime };
      delete next[agentId];
      return { runtime: next };
    }),
  reset: () => set({ runtime: {} }),
}));
