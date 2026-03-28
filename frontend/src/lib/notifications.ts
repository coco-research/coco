import { create } from 'zustand';

export type ReadState = 'unread' | 'seen' | 'dismissed';

export interface Notification {
  id: string;
  type: 'urgent' | 'draft' | 'health' | 'agent' | 'info';
  title: string;
  description?: string;
  timestamp: string;
  /** @deprecated Use readState instead */
  read: boolean;
  readState: ReadState;
  actionUrl?: string;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  showDismissed: boolean;
  addNotification: (n: Omit<Notification, 'id' | 'read' | 'readState'>) => void;
  markSeen: (id: string) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  dismiss: (id: string) => void;
  toggleShowDismissed: () => void;
}

let nextId = 0;

function countUnread(notifications: Notification[]): number {
  return notifications.filter((x) => x.readState === 'unread').length;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  showDismissed: false,

  addNotification: (n) =>
    set((state) => {
      const notification: Notification = {
        ...n,
        id: `notif-${Date.now()}-${nextId++}`,
        read: false,
        readState: 'unread',
      };
      const notifications = [notification, ...state.notifications].slice(0, 100);
      return {
        notifications,
        unreadCount: countUnread(notifications),
      };
    }),

  markSeen: (id) =>
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id && n.readState === 'unread'
          ? { ...n, readState: 'seen' as const, read: true }
          : n,
      );
      return {
        notifications,
        unreadCount: countUnread(notifications),
      };
    }),

  markRead: (id) =>
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id
          ? { ...n, readState: 'seen' as const, read: true }
          : n,
      );
      return {
        notifications,
        unreadCount: countUnread(notifications),
      };
    }),

  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.readState === 'unread'
          ? { ...n, readState: 'seen' as const, read: true }
          : n,
      ),
      unreadCount: 0,
    })),

  dismiss: (id) =>
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id ? { ...n, readState: 'dismissed' as const, read: true } : n,
      );
      return {
        notifications,
        unreadCount: countUnread(notifications),
      };
    }),

  toggleShowDismissed: () =>
    set((state) => ({ showDismissed: !state.showDismissed })),
}));
