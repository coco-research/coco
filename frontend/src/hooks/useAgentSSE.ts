import { useState, useEffect, useRef } from 'react';

export interface AgentStatus {
  id: string;
  name: string;
  status: string;
  role?: string;
}

export interface UseAgentSSEResult {
  agents: Map<string, AgentStatus>;
  /** True when the EventSource is open and has not errored since last connect. */
  connected: boolean;
  /** True if the last connection attempt failed — UI should fall back to polling. */
  errored: boolean;
}

/**
 * Subscribe to /api/events/agents and maintain a live Map of agent statuses.
 *
 * Replaces 3-second polling on the agents list with push-based SSE. Emits an
 * `errored` flag so callers can re-enable polling if the EventSource is in a
 * broken state (backend down, proxy stripped headers, etc.).
 */
export function useAgentSSE(): UseAgentSSEResult {
  const [agents, setAgents] = useState<Map<string, AgentStatus>>(new Map());
  const [connected, setConnected] = useState(false);
  const [errored, setErrored] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource('/api/events/agents');
    eventSourceRef.current = es;

    es.onopen = () => {
      setConnected(true);
      setErrored(false);
    };

    es.addEventListener('agent.snapshot', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        const list: AgentStatus[] = data.data?.agents ?? data.agents ?? [];
        setAgents(new Map(list.map(a => [a.id, a])));
      } catch { /* malformed payload — skip */ }
    });

    const statusEvents = [
      'agent.spawned',
      'agent.paused',
      'agent.resumed',
      'agent.killed',
      'agent.completed',
      'agent.failed',
      'agent.heartbeat',
    ];

    const handleStatusEvent = (evt: string) => (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        // The merged-stream wraps data as a JSON string under .data,
        // but /api/events/agents (filtered prefix subscribe) yields the
        // emit() envelope directly — handle both shapes.
        const agentData = data.data ?? data;
        if (agentData?.agent_id) {
          setAgents(prev => {
            const next = new Map(prev);
            const existing = next.get(agentData.agent_id);
            next.set(agentData.agent_id, {
              ...existing,
              id: agentData.agent_id,
              name: agentData.name ?? existing?.name ?? '',
              status: agentData.status ?? evt.replace('agent.', ''),
              role: agentData.role ?? existing?.role,
            });
            return next;
          });
        }
      } catch { /* malformed payload — skip */ }
    };

    for (const evt of statusEvents) {
      es.addEventListener(evt, handleStatusEvent(evt));
    }

    es.onerror = () => {
      setConnected(false);
      setErrored(true);
      // EventSource auto-reconnects on error; we leave it running.
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, []);

  return { agents, connected, errored };
}
