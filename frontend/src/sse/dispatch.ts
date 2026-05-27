/**
 * Maps incoming typed SSE events to:
 *   - Zustand store updates (live state)
 *   - TanStack Query invalidations (cached resources)
 *
 * Kept separate from `client.ts` so the connector stays plain TS with no
 * store imports — easier to unit test the connector in isolation.
 */

import type { QueryClient } from '@tanstack/react-query';
import type { PlatformSSEEvent } from './events';
import { useBriefingStore } from '../stores/briefing';
import { useQueueStore } from '../stores/queue';
import { useCostsStore } from '../stores/costs';
import { useAgentsStore } from '../stores/agents';

export function dispatchSSEEvent(
  evt: PlatformSSEEvent,
  queryClient: QueryClient,
): void {
  switch (evt.type) {
    case 'platform.epoch':
      // Cache invalidation handled in client.ts; reset optimistic state here.
      useBriefingStore.getState().reset();
      useQueueStore.getState().clearAllOptimistic();
      useCostsStore.getState().reset();
      useAgentsStore.getState().reset();
      return;

    case 'heartbeat':
      return;

    case 'briefing.updated':
      useBriefingStore.getState().markUpdated(evt.briefing_id, evt.ts);
      queryClient.invalidateQueries({ queryKey: ['briefing'] });
      return;

    case 'queue.item.added':
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      return;

    case 'queue.item.decided':
      useQueueStore.getState().clearOptimistic(evt.item_id);
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      return;

    case 'queue.drained':
      useQueueStore.getState().setPendingCount(0);
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      return;

    case 'queue.side_effect_confirmed':
      // Server has finished applying the side-effects of a triage action.
      // Clear any lingering optimistic state and invalidate dependent caches
      // (queue + todos — see INTEGRATION.md §5 SideEffectConfirmed).
      useQueueStore.getState().clearOptimistic(evt.item_id);
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      queryClient.invalidateQueries({ queryKey: ['resolved'] });
      for (const se of evt.side_effects) {
        if (se.kind === 'todo_created') {
          queryClient.invalidateQueries({ queryKey: ['todos'] });
        } else if (se.kind === 'draft_queued') {
          queryClient.invalidateQueries({ queryKey: ['drafts'] });
        } else if (se.kind === 'cost_recorded') {
          queryClient.invalidateQueries({ queryKey: ['costs'] });
        } else if (se.kind === 'agent_spawned') {
          queryClient.invalidateQueries({ queryKey: ['agents'] });
        }
      }
      return;

    case 'costs.updated':
      useCostsStore.getState().setCents(evt.cents, evt.ts);
      queryClient.invalidateQueries({ queryKey: ['costs'] });
      return;

    case 'costs.budget.breached':
      useCostsStore.getState().setBreach(evt.budget_id, evt.breach_pct, evt.ts);
      queryClient.invalidateQueries({ queryKey: ['costs', 'budgets'] });
      return;

    case 'agent.spawned':
      useAgentsStore.getState().setStatus(evt.agent_id, 'idle', evt.ts);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      return;

    case 'agent.status':
      useAgentsStore.getState().setStatus(evt.agent_id, evt.status, evt.ts);
      return;

    case 'agent.completed':
      useAgentsStore.getState().setStatus(evt.agent_id, 'completed', evt.ts);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      return;

    case 'agent.failed':
      useAgentsStore
        .getState()
        .setStatus(evt.agent_id, 'failed', evt.ts, evt.error);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      return;

    default: {
      // Exhaustiveness check — if we add a new event variant without handling
      // it, TS errors here.
      const _exhaustive: never = evt;
      return _exhaustive;
    }
  }
}
