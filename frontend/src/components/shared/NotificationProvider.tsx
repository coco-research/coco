import { type ReactNode, createContext, useContext } from 'react';
import { useEventSource, type SSEConnectionStatus } from '../../lib/sse';
import { useNotificationStore, type Notification } from '../../lib/notifications';
import { useToast } from './Toast';

/**
 * Expose SSE connection status to the rest of the app (used by AppShell offline banner).
 */
const SSEStatusContext = createContext<SSEConnectionStatus>('disconnected');
export function useSSEStatus() {
  return useContext(SSEStatusContext);
}

/**
 * Maps an SSE event from /api/events/stream into a Notification.
 * Returns null for events that shouldn't produce notifications.
 */
function mapEventToNotification(
  eventType: string,
  data: Record<string, unknown>,
): Omit<Notification, 'id' | 'read' | 'readState'> | null {
  // Use either the SSE event name or the embedded "type" field
  const type = eventType !== 'message' ? eventType : (data.type as string | undefined);

  // Agent lifecycle events from EventBus
  if (type === 'agent.completed') {
    const name = (data.name as string) || (data.agent_id as string) || 'Agent';
    return {
      type: 'agent',
      title: `${name} completed`,
      description: data.message as string | undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/agents',
    };
  }
  if (type === 'agent.failed') {
    const name = (data.name as string) || (data.agent_id as string) || 'Agent';
    return {
      type: 'urgent',
      title: `${name} failed`,
      description: (data.error as string) || (data.message as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/agents',
    };
  }

  // Legacy agent_status / station_status from events.jsonl
  if (type === 'agent_status' || type === 'station_status') {
    const status = data.status as string | undefined;
    const name = (data.name as string) || (data.agent_id as string) || 'Agent';
    if (status === 'completed') {
      return {
        type: 'agent',
        title: `${name} completed`,
        description: data.message as string | undefined,
        timestamp: (data.timestamp as string) || new Date().toISOString(),
        actionUrl: '/agents',
      };
    }
    if (status === 'failed' || status === 'error') {
      return {
        type: 'urgent',
        title: `${name} failed`,
        description: (data.error as string) || (data.message as string) || undefined,
        timestamp: (data.timestamp as string) || new Date().toISOString(),
        actionUrl: '/agents',
      };
    }
    return null;
  }

  // Draft decisions
  if (type === 'draft.approved') {
    return {
      type: 'draft',
      title: 'Draft approved',
      description: (data.title as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/inbox',
    };
  }
  if (type === 'draft.rejected') {
    return {
      type: 'draft',
      title: 'Draft rejected',
      description: (data.title as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/inbox',
    };
  }

  // Legacy draft events from events.jsonl
  if (type === 'draft_pending' || type === 'new_draft') {
    return {
      type: 'draft',
      title: 'New draft pending review',
      description: (data.title as string) || (data.subject as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/inbox',
    };
  }

  // Decision queue item
  if (type === 'queue_item' || type === 'decision_pending') {
    return {
      type: 'draft',
      title: 'New decision needs your input',
      description: (data.summary as string) || (data.title as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/inbox',
    };
  }

  // Health alerts
  if (type === 'health_alert' || type === 'adapter_down') {
    return {
      type: 'health',
      title: (data.title as string) || 'Health alert',
      description: (data.message as string) || (data.adapter as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/agents',
    };
  }

  // Cost budget warning
  if (type === 'budget_warning' || type === 'cost.budget_warning') {
    return {
      type: 'urgent',
      title: (data.title as string) || 'Budget threshold reached',
      description: (data.message as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/costs',
    };
  }

  // Todo overdue
  if (type === 'todo.overdue') {
    return {
      type: 'urgent',
      title: (data.title as string) || 'Todo overdue',
      description: (data.message as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/todos',
    };
  }

  // Generic info events with a title
  if (data.title && typeof data.title === 'string') {
    return {
      type: 'info',
      title: data.title,
      description: (data.message as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
    };
  }

  return null;
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const addNotification = useNotificationStore((s) => s.addNotification);
  const { toast } = useToast();

  const handleEvent = (eventType: string, data: unknown) => {
    try {
      const payload = typeof data === 'object' && data !== null ? data as Record<string, unknown> : {};
      const notif = mapEventToNotification(eventType, payload);
      if (!notif) return;

      addNotification(notif);

      // Auto-toast for urgent notifications
      if (notif.type === 'urgent') {
        toast(
          notif.description
            ? `${notif.title}: ${notif.description}`
            : notif.title,
          'error',
        );
      }
    } catch {
      // Ignore unparseable events (heartbeats, raw lines)
    }
  };

  const status = useEventSource('/api/events/stream', {
    onAnyEvent: handleEvent,
  });

  return (
    <SSEStatusContext.Provider value={status}>
      {children}
    </SSEStatusContext.Provider>
  );
}
