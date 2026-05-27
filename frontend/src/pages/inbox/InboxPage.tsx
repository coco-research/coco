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
  type ReactElement,
} from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPostIdempotent } from '../../lib/api';
import { useQueueStore, type OptimisticDecision } from '../../stores/queue';
import { useToast } from '../../components/shared/Toast';
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
    return (queueQ.data ?? [])
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

  const fireTriage = useCallback(
    async (decisionId: string, action: TriageAction) => {
      const endpoint = TRIAGE_TO_ENDPOINT[action];
      const optKey = TRIAGE_TO_OPTIMISTIC[action];
      // Mark optimistic immediately so the card slides out before the round-trip.
      setOptimistic(decisionId, optKey);
      try {
        await apiPostIdempotent(`/queue/${decisionId}/${endpoint}`);
        // We do NOT clear optimistic here — wait for SSE
        // `queue.side_effect_confirmed` to confirm side effects landed.
        // Belt-and-braces: invalidate the queue cache so a fresh GET catches
        // any drift if SSE is degraded.
        queryClient.invalidateQueries({ queryKey: ['queue'] });
      } catch (e) {
        // Roll back — the user can retry. Show a toast.
        clearOptimistic(decisionId);
        const msg = e instanceof Error ? e.message : 'Triage failed';
        toast(`Couldn't ${action}: ${msg}`, 'error');
      }
    },
    [clearOptimistic, queryClient, setOptimistic, toast],
  );

  // Safety: after 8s of optimistic-but-unconfirmed state, force-clear so the
  // card can be re-triaged. The card will reappear from the next GET if the
  // server still has it pending.
  useEffect(() => {
    const ids = Object.keys(optimistic);
    if (ids.length === 0) return;
    const t = setTimeout(() => {
      for (const id of ids) clearOptimistic(id);
      queryClient.invalidateQueries({ queryKey: ['queue'] });
    }, 8000);
    return () => clearTimeout(t);
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
      <Briefing
        greeting={undefined}
        dateLabel={dateLabel}
        paragraphs={briefingParagraphs}
        heroStats={heroStats}
        active={activeZone === 'briefing'}
        loading={briefingQ.isLoading}
        errored={briefingQ.isError}
      />

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

      <ResolvedLog
        items={resolved}
        expanded={resolvedExpanded}
        onToggle={() => setResolvedExpanded((v) => !v)}
        active={activeZone === 'resolved'}
      />
    </div>
  );
}
