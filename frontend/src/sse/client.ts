/**
 * v3 platform SSE client.
 *
 * Wraps `EventSource` with:
 *  - Typed event handling (see `./events.ts`)
 *  - Epoch handling: when `platform.epoch` arrives with a new boot UUID, we
 *    invalidate ALL TanStack Query caches + clear optimistic Zustand state.
 *  - Last-event-id reconnection via `?since=` query param (matches the
 *    existing backend contract in `app/routers/events.py`).
 *  - Exponential backoff with jitter.
 *
 * This is a low-level connector, not a React hook. React glue lives in
 * `App.tsx`. For component-scoped subscriptions use the legacy
 * `useEventSource` hook in `lib/sse.ts` (untyped).
 */

import type { QueryClient } from '@tanstack/react-query';
import {
  isPlatformEvent,
  type PlatformSSEEvent,
  type PlatformSSEEventType,
} from './events';

const BASE_DELAY_MS = 1000;
const MAX_DELAY_MS = 30_000;
const DEFAULT_URL = '/api/events/stream';

function backoffDelay(attempt: number): number {
  const exp = Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_DELAY_MS);
  const jitter = exp * 0.25 * Math.random();
  return exp + jitter;
}

export interface PlatformSSEHandle {
  /** Close the connection and stop reconnect attempts. */
  close: () => void;
  /** Current status — observable via `onStatus` callback in options. */
  getStatus: () => 'connecting' | 'connected' | 'disconnected' | 'failed';
}

export type PlatformSSEStatus = ReturnType<PlatformSSEHandle['getStatus']>;

export interface PlatformSSEOptions {
  /** Default `/api/events/stream`. */
  url?: string;
  /** Required — used to invalidate caches on epoch flip. */
  queryClient: QueryClient;
  /** Called for every typed event. Use it to drive Zustand stores. */
  onEvent?: (evt: PlatformSSEEvent) => void;
  /** Called whenever connection status changes. */
  onStatus?: (status: PlatformSSEStatus) => void;
  /**
   * Called when the boot UUID flips. Caller should clear all optimistic
   * Zustand state. Default behavior (always runs): invalidate all queries.
   */
  onEpochFlip?: (oldId: string | null, newId: string) => void;
  /** Max reconnect attempts before giving up. Default 10. */
  maxRetries?: number;
}

/**
 * Open a long-lived connection to the platform SSE stream.
 *
 * Returns a handle with `close()` for teardown.
 */
export function connectPlatformSSE(opts: PlatformSSEOptions): PlatformSSEHandle {
  const {
    url = DEFAULT_URL,
    queryClient,
    onEvent,
    onStatus,
    onEpochFlip,
    maxRetries = 10,
  } = opts;

  let es: EventSource | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempt = 0;
  let stopped = false;
  let lastEventTs: string | null = null;
  let bootId: string | null = null;
  let status: PlatformSSEStatus = 'disconnected';

  function setStatus(next: PlatformSSEStatus) {
    if (status === next) return;
    status = next;
    onStatus?.(next);
  }

  function trackTs(data: unknown) {
    if (!data || typeof data !== 'object') return;
    const ts = (data as Record<string, unknown>).ts;
    if (typeof ts === 'string') {
      lastEventTs = ts;
    } else if (typeof ts === 'number') {
      lastEventTs = new Date(ts * 1000).toISOString();
    }
  }

  function handleEpoch(evt: { boot_id: string }) {
    const prev = bootId;
    if (prev !== null && prev !== evt.boot_id) {
      // Backend was restarted — purge everything cache-side.
      queryClient.invalidateQueries();
      onEpochFlip?.(prev, evt.boot_id);
    }
    bootId = evt.boot_id;
  }

  // Per `.planning/v3/INTEGRATION.md` §SSE catalog: known typed events the
  // backend may emit. Anything else is passed through to onEvent if it
  // happens to match the union shape.
  const KNOWN_EVENTS: PlatformSSEEventType[] = [
    'platform.epoch',
    'heartbeat',
    'briefing.updated',
    'queue.item.added',
    'queue.item.decided',
    'queue.drained',
    'queue.side_effect_confirmed',
    'costs.updated',
    'costs.budget.breached',
    'agent.spawned',
    'agent.status',
    'agent.completed',
    'agent.failed',
  ];

  function open() {
    if (stopped) return;
    setStatus('connecting');

    let connectUrl = url;
    if (attempt > 0 && lastEventTs) {
      const sep = url.includes('?') ? '&' : '?';
      connectUrl = `${url}${sep}since=${encodeURIComponent(lastEventTs)}`;
    }

    const source = new EventSource(connectUrl);
    es = source;

    source.onopen = () => {
      if (stopped) return;
      attempt = 0;
      setStatus('connected');
    };

    for (const evtType of KNOWN_EVENTS) {
      source.addEventListener(evtType, (e: MessageEvent) => {
        let parsed: unknown;
        try {
          parsed = JSON.parse(e.data);
        } catch {
          return;
        }
        // Server may send the payload without a `type` field — graft it.
        if (
          parsed &&
          typeof parsed === 'object' &&
          !('type' in (parsed as Record<string, unknown>))
        ) {
          (parsed as Record<string, unknown>).type = evtType;
        }
        trackTs(parsed);

        if (isPlatformEvent(parsed, 'platform.epoch')) {
          handleEpoch(parsed);
        }

        onEvent?.(parsed as PlatformSSEEvent);
      });
    }

    source.onerror = () => {
      if (stopped) return;
      source.close();
      es = null;
      setStatus('disconnected');

      attempt += 1;
      if (attempt > maxRetries) {
        setStatus('failed');
        return;
      }
      const delay = backoffDelay(attempt - 1);
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        open();
      }, delay);
    };
  }

  open();

  return {
    close() {
      stopped = true;
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (es) {
        es.close();
        es = null;
      }
      setStatus('disconnected');
    },
    getStatus: () => status,
  };
}
