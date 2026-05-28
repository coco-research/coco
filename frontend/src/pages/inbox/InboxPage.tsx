/**
 * InboxPage — Phase-6 v3 redesign.
 *
 * 3-zone deck: Morning Briefing · Decision Deck · Resolved Log.
 *
 * Wires to:
 *   - `/api/briefing`   (existing) → Briefing zone
 *   - `/api/queue`      (existing) → Decision Deck zone (decisions array)
 *   - `/api/queue/resolved` (new in P5/P6) → Resolved Log zone
 *
 * Triage mutations POST to `/api/queue/{id}/{action}` with an
 * `Idempotency-Key` HTTP header (Stripe pattern — see INTEGRATION.md §C-4).
 * Optimistic state lives in Zustand's `useQueueStore`. SSE
 * `queue.side_effect_confirmed` clears optimistic state once the backend
 * confirms downstream side-effects have landed (`sse/dispatch.ts`).
 *
 * Implements DESIGN.md §1.3 + DECISIONS.md D-UI-007 (23s triage target,
 * keyboard 1/2/3/4, auto-advance).
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactElement,
} from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPostIdempotent, generateUuidV4 } from '../../lib/api';
import { useQueueStore, type OptimisticDecision } from '../../stores/queue';
import { useToast } from '../../components/shared/Toast';
import { ErrorState } from '../../components/shared/states';
import { Briefing } from './components/Briefing';
import { DecisionDeck } from './components/DecisionDeck';
import { ResolvedLog } from './components/ResolvedLog';
import type {
  DecisionCardData,
  DecisionActionKey,
  DecisionOption,
} from './components/DecisionCard';
import type { ResolvedItem, ResolvedAction } from './components/ResolvedLog';
import {
  useKeyboardTriage,
  type TriageAction,
} from './hooks/useKeyboardTriage';

// ---------- Server payload shapes (loose — backend is in flight) ----------

interface BriefingPayload {
  generated_at?: string;
  cutoff?: string;
  // Narrative paragraphs — backend may or may not have these populated yet.
  paragraphs?: string[];
  decision_queue?: { pending_count?: number };
  action_items?: { total_open?: number };
  email_digest?: { total?: number; urgent?: number };
}

interface QueueItem {
  id: string;
  title?: string;
  summary?: string;
  project?: string;
  source?: string;
  priority?: number;
  context?: string;
  reasoning?: string;
  from_name?: string;
  from_role?: string;
  options?: Array<{
    key?: string;
    hotkey?: string;
    title?: string;
    subtitle?: string;
    destructive?: boolean;
  }>;
}

interface ResolvedPayload {
  items?: Array<{
    id: string;
    text?: string;
    title?: string;
    action?: string;
    resolved_at?: string;
    resolved_ts?: string;
    source?: string;
  }>;
}

// ---------- Local mapping helpers ----------

const TRIAGE_TO_ENDPOINT: Record<TriageAction, string> = {
  approve: 'approve',
  reply: 'reply',
  delegate: 'delegate',
  snooze: 'snooze',
};

const TRIAGE_TO_OPTIMISTIC: Record<TriageAction, OptimisticDecision> = {
  approve: 'approve',
  reply: 'defer', // reply opens a draft pane — treat as deferred from queue POV
  delegate: 'defer',
  snooze: 'defer',
};

const DEFAULT_OPTIONS: [DecisionOption, DecisionOption, DecisionOption, DecisionOption] = [
  { key: 'approve', hotkey: '1', title: 'Approve', subtitle: 'Accept CoCo\'s recommendation' },
  { key: 'reply', hotkey: '2', title: 'Reply manually', subtitle: 'Open draft pane' },
  { key: 'delegate', hotkey: '3', title: 'Delegate', subtitle: 'Hand off to a teammate' },
  { key: 'snooze', hotkey: '4', title: 'Snooze 30 min', subtitle: 'Resurface later', destructive: false },
];

function normalizeAction(raw: string | undefined): ResolvedAction {
  switch (raw) {
    case 'approve':
    case 'reply':
    case 'delegate':
    case 'snooze':
      return raw;
    default:
      return 'auto';
  }
}

function toCard(item: QueueItem): DecisionCardData {
  const opts =
    item.options && item.options.length === 4
      ? (item.options.map((o, i) => {
          const fallback = DEFAULT_OPTIONS[i]!;
          return {
            key: (o.key as DecisionActionKey) ?? fallback.key,
            hotkey: (o.hotkey as '1' | '2' | '3' | '4') ?? fallback.hotkey,
            title: o.title ?? fallback.title,
            subtitle: o.subtitle ?? fallback.subtitle,
            destructive: o.destructive ?? fallback.destructive,
          };
        }) as [DecisionOption, DecisionOption, DecisionOption, DecisionOption])
      : DEFAULT_OPTIONS;

  return {
    id: item.id,
    sourceLabel: item.source,
    urgencyLabel:
      item.priority !== undefined && item.priority <= 1 ? 'Urgent' : undefined,
    fromName: item.from_name,
    fromRole: item.from_role,
    ask: item.title ?? item.summary ?? 'Decision needed',
    context: item.context,
    reasoning: item.reasoning,
    options: opts,
  };
}

// ---------- Component ----------

export default function InboxPage(): ReactElement {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const optimistic = useQueueStore((s) => s.optimistic);
  const setOptimistic = useQueueStore((s) => s.setOptimistic);
  const clearOptimistic = useQueueStore((s) => s.clearOptimistic);

  // ── Briefing query ──
  const briefingQ = useQuery({
    queryKey: ['briefing'],
    queryFn: () => apiFetch<BriefingPayload>('/briefing'),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // ── Queue query ──
  const queueQ = useQuery({
    queryKey: ['queue'],
    queryFn: async () => {
      // The legacy endpoint returns { items: [] } — keep backward compat.
      const res = await apiFetch<{ items?: QueueItem[] }>('/queue');
      return res?.items ?? [];
    },
    staleTime: 60_000,
  });

  // ── Resolved query (24h log) ──
  const resolvedQ = useQuery({
    queryKey: ['resolved', '24h'],
    queryFn: async () => {
      try {
        const res = await apiFetch<ResolvedPayload>('/queue/resolved?window=24h');
        return res?.items ?? [];
      } catch {
        // Endpoint may not be deployed yet during P5/P6 cutover; degrade gracefully.
        return [] as NonNullable<ResolvedPayload['items']>;
      }
    },
    staleTime: 60_000,
    retry: false,
  });

  // ── Derived view model ──

  const decisions: DecisionCardData[] = useMemo(() => {
    const items = Array.isArray(queueQ.data) ? queueQ.data : [];
    return items
      .filter((it) => !optimistic[it.id])
      .map(toCard);
  }, [queueQ.data, optimistic]);

  const briefingParagraphs: string[] | undefined = useMemo(() => {
    const b = briefingQ.data;
    if (!b) return undefined;
    if (b.paragraphs && b.paragraphs.length > 0) return b.paragraphs;
    // Synthesize a one-line summary from counters when the backend hasn't
    // shipped narrative paragraphs yet.
    const parts: string[] = [];
    const pending = b.decision_queue?.pending_count ?? 0;
    if (pending > 0) {
      parts.push(`${pending} decision${pending === 1 ? '' : 's'} need you.`);
    }
    const open = b.action_items?.total_open ?? 0;
    if (open > 0) parts.push(`${open} action item${open === 1 ? '' : 's'} open.`);
    const urgent = b.email_digest?.urgent ?? 0;
    if (urgent > 0) parts.push(`${urgent} urgent email${urgent === 1 ? '' : 's'}.`);
    return parts.length > 0 ? [parts.join(' ')] : undefined;
  }, [briefingQ.data]);

  const heroStats = useMemo(() => {
    const b = briefingQ.data;
    if (!b) return undefined;
    return [
      { value: b.decision_queue?.pending_count ?? 0, label: 'Needs you' },
      { value: b.action_items?.total_open ?? 0, label: 'Action items' },
      { value: b.email_digest?.total ?? 0, label: 'Emails today' },
      { value: b.email_digest?.urgent ?? 0, label: 'Urgent' },
    ];
  }, [briefingQ.data]);

  const dateLabel = useMemo(() => {
    const iso = briefingQ.data?.generated_at;
    if (!iso) return undefined;
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return undefined;
    }
  }, [briefingQ.data]);

  const resolved: ResolvedItem[] = useMemo(() => {
    return (resolvedQ.data ?? []).map((r) => ({
      id: r.id,
      text: r.text ?? r.title ?? '(no description)',
      action: normalizeAction(r.action),
      resolvedAt: r.resolved_at ?? r.resolved_ts ?? '',
      source: r.source,
    }));
  }, [resolvedQ.data]);

  // ── Triage dispatch — POSTs with Idempotency-Key ──

  // Debounce ref: avoid immediate refetch after optimistic update (would cause
  // flicker if the server hasn't committed the triage yet and the GET returns
  // the old queue, briefly resurrecting the dismissed card). Ported from
  // wave-3 c168fc7 ("fix(inbox): eliminate dismiss flicker via optimistic
  // cache"), adapted to the 3-zone design — instead of TanStack `onMutate`
  // cache writes (which the redesign doesn't use), we hang the rollback off
  // Zustand's `optimistic` map and debounce the reconciling invalidate.
  const refetchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scheduleQueueRefetch = useCallback(() => {
    if (refetchTimerRef.current) clearTimeout(refetchTimerRef.current);
    refetchTimerRef.current = setTimeout(() => {
      refetchTimerRef.current = null;
      queryClient.invalidateQueries({ queryKey: ['queue'] });
    }, 500);
  }, [queryClient]);

  // Per-item safety-clear timers. Replaces the previous single 8s timer that
  // reset on every new triage — under steady use that timer would never fire
  // because each new optimistic entry restarted it. Per-item timers fire
  // independently so each stale optimistic entry self-clears at +8s.
  const safetyTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(
    new Map(),
  );

  // Stable Idempotency-Keys per (itemId, action). Pre-generated on first use
  // so that double-tap / retry of the same logical action reuses the same key
  // (Stripe-style dedupe). Cleared when the action settles.
  const idempotencyKeysRef = useRef<Map<string, string>>(new Map());

  // In-flight actions — keyed by `${itemId}:${action}`. Bail early if a tap
  // arrives while the same logical action is already in flight.
  const [inFlightActions, setInFlightActions] = useState<Set<string>>(
    () => new Set(),
  );
  // Mirror in a ref for sync-read inside the callback without a stale closure.
  const inFlightActionsRef = useRef<Set<string>>(inFlightActions);
  useEffect(() => {
    inFlightActionsRef.current = inFlightActions;
  }, [inFlightActions]);

  const markInFlight = useCallback((key: string, on: boolean) => {
    setInFlightActions((prev) => {
      const next = new Set(prev);
      if (on) next.add(key);
      else next.delete(key);
      return next;
    });
  }, []);

  // Clean up pending refetch + safety timers on unmount.
  useEffect(
    () => () => {
      if (refetchTimerRef.current) clearTimeout(refetchTimerRef.current);
      for (const t of safetyTimersRef.current.values()) clearTimeout(t);
      safetyTimersRef.current.clear();
    },
    [],
  );

  const fireTriage = useCallback(
    async (decisionId: string, action: TriageAction) => {
      const inFlightKey = `${decisionId}:${action}`;
      // Double-fire guard — bail if the same logical action is already in
      // flight for this item. Prevents two distinct Idempotency-Key headers
      // (which apiPostIdempotent generates by default) from being sent for the
      // same user intent on a rapid double-tap.
      if (inFlightActionsRef.current.has(inFlightKey)) return;

      const endpoint = TRIAGE_TO_ENDPOINT[action];
      const optKey = TRIAGE_TO_OPTIMISTIC[action];
      // Snapshot previous optimistic state for this id (rollback target).
      // `clearOptimistic(id)` would re-show the card; if there had been a
      // prior optimistic entry (rare — same card triaged twice in flight) we
      // restore that exact value rather than dropping it.
      const previous = useQueueStore.getState().optimistic[decisionId];

      // Stabilize the Idempotency-Key per (itemId, action). On retry or
      // double-tap, the same UUID is reused so the backend dedupe layer
      // treats them as one logical request.
      let idempotencyKey = idempotencyKeysRef.current.get(inFlightKey);
      if (!idempotencyKey) {
        idempotencyKey = generateUuidV4();
        idempotencyKeysRef.current.set(inFlightKey, idempotencyKey);
      }

      // Mark optimistic immediately so the card slides out before the round-trip.
      setOptimistic(decisionId, optKey);
      markInFlight(inFlightKey, true);
      inFlightActionsRef.current = new Set(inFlightActionsRef.current).add(
        inFlightKey,
      );
      try {
        await apiPostIdempotent(
          `/queue/${decisionId}/${endpoint}`,
          {},
          idempotencyKey,
        );
        // We do NOT clear optimistic here — wait for SSE
        // `queue.side_effect_confirmed` to confirm side effects landed.
        // Belt-and-braces: invalidate the queue cache so a fresh GET catches
        // any drift if SSE is degraded — debounced 500ms to avoid the brief
        // "card reappears" flicker when the server hasn't yet propagated the
        // triage at the time of refetch.
        scheduleQueueRefetch();
        // Success — drop the cached key so a fresh user action gets a fresh
        // UUID (otherwise a second logical "approve" after success would
        // collapse into the prior request server-side).
        idempotencyKeysRef.current.delete(inFlightKey);
      } catch (e) {
        // Roll back — the user can retry. Show a toast.
        // Keep the idempotency key cached so a retry POST reuses it (the
        // backend will dedupe if the original actually landed).
        if (previous !== undefined) {
          setOptimistic(decisionId, previous);
        } else {
          clearOptimistic(decisionId);
        }
        const msg = e instanceof Error ? e.message : 'Triage failed';
        toast(`Couldn't ${action}: ${msg}`, 'error');
      } finally {
        markInFlight(inFlightKey, false);
      }
    },
    [clearOptimistic, markInFlight, scheduleQueueRefetch, setOptimistic, toast],
  );

  // Safety: per-item +8s timer so each stale optimistic entry self-clears
  // independently. Under steady use the previous single timer would reset on
  // every new triage and never fire; this version schedules one timer per id
  // when that id transitions into the optimistic map.
  useEffect(() => {
    const ids = Object.keys(optimistic);
    const timers = safetyTimersRef.current;
    // Schedule timers for any new optimistic ids.
    for (const id of ids) {
      if (timers.has(id)) continue;
      const t = setTimeout(() => {
        timers.delete(id);
        clearOptimistic(id);
        queryClient.invalidateQueries({ queryKey: ['queue'] });
      }, 8000);
      timers.set(id, t);
    }
    // Drop timers for ids that left the optimistic map (already confirmed via
    // SSE or rolled back) — otherwise they'd fire a spurious invalidate.
    const present = new Set(ids);
    for (const [id, t] of Array.from(timers.entries())) {
      if (!present.has(id)) {
        clearTimeout(t);
        timers.delete(id);
      }
    }
  }, [optimistic, clearOptimistic, queryClient]);

  // ── Keyboard triage state ──

  const hotkeyTriggerRef = useRef<((hk: '1' | '2' | '3' | '4') => void) | null>(
    null,
  );
  const deckCardRef = useRef<HTMLElement | null>(null);

  const {
    activeZone,
    resolvedExpanded,
    setResolvedExpanded,
    bindKeyDown,
    deckContainerRef,
  } = useKeyboardTriage({
    deckEmpty: decisions.length === 0,
    onTriage: (_action, hotkey) => {
      // Delegate to the deck's locally-tracked active card.
      hotkeyTriggerRef.current?.(hotkey);
    },
  });

  // Bridge: keep deckContainerRef in sync with the actual focused card.
  useEffect(() => {
    deckContainerRef.current = deckCardRef.current;
  });

  // ── Render ──

  return (
    <div
      role="region"
      aria-label="Inbox"
      onKeyDown={bindKeyDown}
      data-zone={activeZone}
      // Page must be focusable so key events bubble up even when no
      // individual card has focus.
      tabIndex={-1}
      className="space-y-4 outline-none"
    >
      {briefingQ.isError ? (
        <ErrorState
          error={briefingQ.error}
          title="Couldn't load briefing"
          onRetry={() => void briefingQ.refetch()}
          testId="inbox-briefing-error"
        />
      ) : (
        <Briefing
          greeting={undefined}
          dateLabel={dateLabel}
          paragraphs={briefingParagraphs}
          heroStats={heroStats}
          active={activeZone === 'briefing'}
          loading={briefingQ.isLoading}
          errored={false}
        />
      )}

      {queueQ.isError ? (
        <ErrorState
          error={queueQ.error}
          title="Couldn't load decision queue"
          onRetry={() => void queueQ.refetch()}
          testId="inbox-queue-error"
        />
      ) : (
        <DecisionDeck
          decisions={decisions}
          pending={Object.fromEntries(
            Object.keys(optimistic).map((id) => [id, true]),
          )}
          onAction={(id, key) => {
            // key maps 1:1 to TriageAction (approve/reply/delegate/snooze).
            void fireTriage(id, key as TriageAction);
          }}
          active={activeZone === 'deck'}
          cardRef={deckCardRef}
          onHotkeyRef={hotkeyTriggerRef}
        />
      )}

      <ResolvedLog
        items={resolved}
        expanded={resolvedExpanded}
        onToggle={() => setResolvedExpanded((v) => !v)}
        active={activeZone === 'resolved'}
      />
    </div>
  );
}
