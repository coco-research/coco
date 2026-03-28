import { useEffect } from 'react';
import { useEventSource } from '../lib/sse';
import { isEnabled, notify } from '../lib/desktop-notifications';

/**
 * Subscribes to the agent SSE stream and fires desktop notifications
 * when an agent crashes or fails.
 */
export function useDesktopNotifications() {
  const status = useEventSource('/api/events/agents', {
    enabled: isEnabled(),
    events: {
      'agent.failed': (data: unknown) => {
        const d = data as Record<string, unknown>;
        const name = (d.name as string) ?? (d.agent_id as string) ?? 'Agent';
        const reason = (d.reason as string) ?? (d.error as string) ?? 'Unknown error';
        notify(`Agent Crashed: ${name}`, {
          body: reason,
          tag: `agent-failed-${d.agent_id ?? d.id ?? ''}`,
        });
      },
      'agent.killed': (data: unknown) => {
        const d = data as Record<string, unknown>;
        const name = (d.name as string) ?? (d.agent_id as string) ?? 'Agent';
        notify(`Agent Killed: ${name}`, {
          body: 'The agent process was terminated.',
          tag: `agent-killed-${d.agent_id ?? d.id ?? ''}`,
        });
      },
    },
  });

  // Return status so callers can inspect if needed
  return status;
}

/**
 * Provider hook meant to be called once at the app root level.
 * Simply activates the SSE subscription for desktop notifications.
 */
export function useDesktopNotificationListener() {
  useDesktopNotifications();
}
