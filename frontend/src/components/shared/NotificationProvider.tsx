import { type ReactNode, createContext, useContext } from 'react';
import { useEventSource, type SSEConnectionStatus } from '../../lib/sse';
import { useNotificationStore, type Notification } from '../../lib/notifications';
import { useToast } from './Toast';
import { sendDesktopNotification } from '../../lib/desktop-notifications';

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
  if (type === 'agent.failed' || type === 'agent.crashed') {
    const name = (data.name as string) || (data.agent_id as string) || 'Agent';
    const verb = type === 'agent.crashed' ? 'crashed' : 'failed';
    return {
      type: 'urgent',
      title: `${name} ${verb}`,
      description: (data.error as string) || (data.message as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: '/agents',
    };
  }

  // Generic notification pushed by backend (notification.created)
  // Payload shape: { type, title, description?, severity?, action_url?/actionUrl?, timestamp? }
  if (type === 'notification.created' || type === 'notification_created') {
    const severity = (data.severity as string) || (data.level as string) || 'info';
    const notifType =
      severity === 'critical' || severity === 'error' || severity === 'urgent'
        ? 'urgent'
        : severity === 'warning'
          ? 'health'
          : ((data.kind as Notification['type']) || 'info');
    const title = (data.title as string) || 'Notification';
    return {
      type: notifType,
      title,
      description: (data.description as string) || (data.message as string) || undefined,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      actionUrl: (data.action_url as string) || (data.actionUrl as string) || undefined,
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

      // Desktop notifications for urgent events:
      // agent.failed, agent.crashed, agent.completed, budget exceeded, todo.overdue
      const desktopTypes = new Set([
        'agent.failed',
        'agent.crashed',
        'agent.completed',
        'budget_warning',
        'cost.budget_warning',
        'todo.overdue',
      ]);
      const resolvedType = eventType !== 'message' ? eventType : (payload.type as string | undefined);
      const shouldDesktopNotify =
        notif.type === 'urgent' ||
        (resolvedType && desktopTypes.has(resolvedType));

      if (shouldDesktopNotify) {
        sendDesktopNotification(
          notif.title,
          notif.description || '',
          {
            tag: resolvedType ?? 'coco-urgent',
            onClick: () => {
              if (notif.actionUrl) {
                window.location.hash = notif.actionUrl;
              }
            },
          },
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
