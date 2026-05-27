/**
 * Typed event union for the v3 SSE catalog.
 *
 * Per `.planning/v3/INTEGRATION.md` §SSE catalog. When the backend emits
 * `platform.epoch` with a new boot UUID, clients MUST invalidate all queries
 * and clear optimistic state — see `sse/client.ts`.
 *
 * NOTE: this lives alongside legacy `lib/sse.ts` (untyped) — new code should
 * prefer this typed surface and the `connectPlatformSSE` helper.
 */

// ---------- Platform-level lifecycle ----------

export interface PlatformEpochEvent {
  type: 'platform.epoch';
  /** Boot UUID — changes on every backend (re)start. Used to invalidate cache. */
  boot_id: string;
  /** ISO-8601 timestamp of the epoch. */
  ts: string;
  /** Backend semver / git sha for diagnostics. */
  version?: string;
}

export interface HeartbeatEvent {
  type: 'heartbeat';
  ts: number;
}

// ---------- Briefing ----------

export interface BriefingUpdatedEvent {
  type: 'briefing.updated';
  briefing_id: string;
  ts: string;
}

// ---------- Decision queue ----------

export interface QueueItemAddedEvent {
  type: 'queue.item.added';
  item_id: string;
  scope?: string | null;
  ts: string;
}

export interface QueueItemDecidedEvent {
  type: 'queue.item.decided';
  item_id: string;
  decision: 'approve' | 'reject' | 'defer';
  ts: string;
}

export interface QueueDrainedEvent {
  type: 'queue.drained';
  ts: string;
}

export interface QueueSideEffect {
  kind:
    | 'todo_created'
    | 'draft_queued'
    | 'slack_replied'
    | 'email_drafted'
    | 'cost_recorded'
    | 'agent_spawned';
  ref_id: string | null;
  ts: string;
}

/**
 * Emitted *after* the downstream side-effect of a triage action has landed
 * (todo row inserted, draft queued, Slack reply posted, etc.). See
 * `.planning/v3/INTEGRATION.md` §C-8 and §4.8.
 */
export interface QueueSideEffectConfirmedEvent {
  type: 'queue.side_effect_confirmed';
  item_id: string;
  applied_ts: string;
  observable_at: string;
  side_effects: QueueSideEffect[];
  ts: string;
}

// ---------- Cost ledger ----------

export interface CostsUpdatedEvent {
  type: 'costs.updated';
  /** Cumulative USD for the current window (day/week/month). */
  cents: number;
  scope?: string | null;
  ts: string;
}

export interface CostsBudgetBreachedEvent {
  type: 'costs.budget.breached';
  budget_id: string;
  breach_pct: number;
  ts: string;
}

// ---------- Agents (a.k.a. stations) ----------

export interface AgentSpawnedEvent {
  type: 'agent.spawned';
  agent_id: string;
  parent_id?: string | null;
  ts: string;
}

export interface AgentStatusEvent {
  type: 'agent.status';
  agent_id: string;
  status: 'idle' | 'running' | 'paused' | 'failed' | 'completed';
  ts: string;
}

export interface AgentCompletedEvent {
  type: 'agent.completed';
  agent_id: string;
  ts: string;
}

export interface AgentFailedEvent {
  type: 'agent.failed';
  agent_id: string;
  error?: string;
  ts: string;
}

// ---------- Union ----------

export type PlatformSSEEvent =
  | PlatformEpochEvent
  | HeartbeatEvent
  | BriefingUpdatedEvent
  | QueueItemAddedEvent
  | QueueItemDecidedEvent
  | QueueDrainedEvent
  | QueueSideEffectConfirmedEvent
  | CostsUpdatedEvent
  | CostsBudgetBreachedEvent
  | AgentSpawnedEvent
  | AgentStatusEvent
  | AgentCompletedEvent
  | AgentFailedEvent;

export type PlatformSSEEventType = PlatformSSEEvent['type'];

/** Narrow a raw event by type tag. */
export function isPlatformEvent<T extends PlatformSSEEventType>(
  evt: unknown,
  type: T,
): evt is Extract<PlatformSSEEvent, { type: T }> {
  return (
    typeof evt === 'object' &&
    evt !== null &&
    'type' in evt &&
    (evt as { type: string }).type === type
  );
}
