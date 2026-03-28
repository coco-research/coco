import { useEffect, useRef, useState, useCallback } from 'react';

export type SSEConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'failed';

export interface UseEventSourceOptions {
  /** Named event handlers: key is SSE event type, value is handler receiving parsed JSON data. */
  events?: Record<string, (data: unknown) => void>;
  /** Catch-all handler for any event (including unnamed). */
  onAnyEvent?: (eventType: string, data: unknown) => void;
  /** Called when max reconnection attempts are exceeded. */
  onMaxRetriesExceeded?: () => void;
  /** Maximum reconnection attempts before giving up. Default: 10. */
  maxRetries?: number;
  /** Whether the hook is enabled. Allows conditional connection. Default: true. */
  enabled?: boolean;
}

const BASE_DELAY_MS = 1000;
const MAX_DELAY_MS = 30_000;

function backoffDelay(attempt: number): number {
  const exponential = Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_DELAY_MS);
  // Add up to 25% jitter
  const jitter = exponential * 0.25 * Math.random();
  return exponential + jitter;
}

/**
 * React hook that connects to an SSE endpoint with:
 * - Named event listeners via addEventListener
 * - Exponential backoff reconnection with jitter
 * - Proper cleanup on unmount (even during reconnection delay)
 * - Connection status tracking
 */
export function useEventSource(url: string, options: UseEventSourceOptions = {}) {
  const {
    events = {},
    onAnyEvent,
    onMaxRetriesExceeded,
    maxRetries = 10,
    enabled = true,
  } = options;

  const [status, setStatus] = useState<SSEConnectionStatus>('disconnected');

  // Track the timestamp of the last received event for reconnection replay
  const lastEventTimestampRef = useRef<string | null>(null);

  // Use refs so reconnection logic always sees latest callbacks without re-triggering the effect.
  const eventsRef = useRef(events);
  eventsRef.current = events;

  const onAnyRef = useRef(onAnyEvent);
  onAnyRef.current = onAnyEvent;

  const onMaxRetriesRef = useRef(onMaxRetriesExceeded);
  onMaxRetriesRef.current = onMaxRetriesExceeded;

  const connect = useCallback(() => {
    // This function is only called inside useEffect below; the ref-based
    // approach keeps the dependency array stable.
  }, []);
  // (connect is defined inline in the effect to capture the cleanup token)

  useEffect(() => {
    if (!enabled) {
      setStatus('disconnected');
      return;
    }

    let esRef: EventSource | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;
    let unmounted = false;

    function cleanup() {
      unmounted = true;
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (esRef) {
        esRef.close();
        esRef = null;
      }
    }

    function trackTimestamp(data: unknown) {
      // Extract timestamp from event data for reconnection replay
      if (data && typeof data === 'object' && 'ts' in (data as Record<string, unknown>)) {
        const ts = (data as Record<string, unknown>).ts;
        if (typeof ts === 'number') {
          // Convert Unix epoch to ISO-8601 UTC
          lastEventTimestampRef.current = new Date(ts * 1000).toISOString();
        } else if (typeof ts === 'string') {
          lastEventTimestampRef.current = ts;
        }
      } else {
        // Fallback: use current time
        lastEventTimestampRef.current = new Date().toISOString();
      }
    }

    function makeHandler(eventType: string) {
      return (e: MessageEvent) => {
        let parsed: unknown;
        try {
          parsed = JSON.parse(e.data);
        } catch {
          parsed = e.data;
        }

        trackTimestamp(parsed);

        const handler = eventsRef.current[eventType];
        if (handler) handler(parsed);

        if (onAnyRef.current) onAnyRef.current(eventType, parsed);
      };
    }

    function openConnection() {
      if (unmounted) return;

      setStatus('connecting');

      // Append ?since= on reconnection so the server replays missed events
      let connectUrl = url;
      if (attempt > 0 && lastEventTimestampRef.current) {
        const separator = url.includes('?') ? '&' : '?';
        connectUrl = `${url}${separator}since=${encodeURIComponent(lastEventTimestampRef.current)}`;
      }

      const es = new EventSource(connectUrl);
      esRef = es;

      es.onopen = () => {
        if (unmounted) return;
        attempt = 0; // reset on successful connection
        setStatus('connected');
      };

      // Register named event listeners
      const eventTypes = Object.keys(eventsRef.current);
      for (const eventType of eventTypes) {
        es.addEventListener(eventType, makeHandler(eventType) as EventListener);
      }

      // Always listen for some well-known event types that the backend emits,
      // plus a generic "message" handler for unnamed events.
      const wellKnown = [
        'heartbeat',
        'agent.spawned', 'agent.paused', 'agent.resumed', 'agent.killed',
        'agent.completed', 'agent.failed',
        'todo.created', 'todo.updated',
        'task.created', 'task.updated',
        'goal.created', 'goal.updated',
        'tree.changed',
        'draft.approved', 'draft.rejected',
      ];
      for (const evt of wellKnown) {
        if (!eventsRef.current[evt]) {
          // Still pipe through onAnyEvent
          es.addEventListener(evt, makeHandler(evt) as EventListener);
        }
      }

      // Catch-all for unnamed events (SSE "message" type)
      es.onmessage = (e: MessageEvent) => {
        let parsed: unknown;
        try {
          parsed = JSON.parse(e.data);
        } catch {
          parsed = e.data;
        }
        trackTimestamp(parsed);
        if (onAnyRef.current) onAnyRef.current('message', parsed);
      };

      es.onerror = () => {
        if (unmounted) return;

        es.close();
        esRef = null;
        setStatus('disconnected');

        attempt += 1;
        if (attempt > maxRetries) {
          setStatus('failed');
          if (onMaxRetriesRef.current) onMaxRetriesRef.current();
          return;
        }

        const delay = backoffDelay(attempt - 1);
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          openConnection();
        }, delay);
      };
    }

    openConnection();

    return cleanup;
  }, [url, enabled, maxRetries, connect]);

  return status;
}
