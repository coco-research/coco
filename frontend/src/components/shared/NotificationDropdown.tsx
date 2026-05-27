import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell, AlertTriangle, FileText, Heart, Bot, Info, X, Eye, EyeOff,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { timeAgo } from '../../lib/utils';
import { useNotificationStore, type Notification, type ReadState } from '../../lib/notifications';
import { useInViewport } from '../../hooks/useInViewport';

const typeIcon: Record<Notification['type'], React.ElementType> = {
  urgent: AlertTriangle,
  draft: FileText,
  health: Heart,
  agent: Bot,
  info: Info,
};

const typeDotColor: Record<Notification['type'], string> = {
  urgent: 'bg-red-500',
  draft: 'bg-amber-500',
  health: 'bg-rose-500',
  agent: 'bg-blue-500',
  info: 'bg-muted-foreground',
};

function stateClass(state: ReadState): string {
  switch (state) {
    case 'unread': return 'notif-unread animate-notif-enter';
    case 'seen': return 'notif-seen';
    case 'dismissed': return 'notif-dismissed';
  }
}

/** Single notification row with IntersectionObserver auto-seen */
function NotificationRow({
  notification,
  onClickNotification,
  onDismiss,
  onMarkSeen,
}: {
  notification: Notification;
  onClickNotification: (n: Notification) => void;
  onDismiss: (id: string) => void;
  onMarkSeen: (id: string) => void;
}) {
  const [viewRef, hasBeenVisible] = useInViewport(2000);
  const Icon = typeIcon[notification.type];

  // Auto-transition: unread -> seen after 2s in viewport
  useEffect(() => {
    if (hasBeenVisible && notification.readState === 'unread') {
      onMarkSeen(notification.id);
    }
  }, [hasBeenVisible, notification.readState, notification.id, onMarkSeen]);

  return (
    <div
      ref={viewRef}
      className={cn(
        'group flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-accent/50 transition-all border-b border-border/50 last:border-0',
        notification.readState === 'unread' && 'bg-accent/20',
        stateClass(notification.readState),
      )}
      onClick={() => onClickNotification(notification)}
    >
      {/* Type indicator dot — only visible for unread */}
      <div className="mt-0.5 shrink-0">
        <div
          className={cn(
            'w-2 h-2 rounded-full transition-all duration-300',
            notification.readState === 'unread'
              ? cn(typeDotColor[notification.type], 'animate-pulse-dot')
              : 'bg-transparent',
          )}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <Icon size={12} className="text-muted-foreground shrink-0" />
          <p
            className={cn(
              'text-sm truncate transition-all duration-300',
              notification.readState === 'unread'
                ? 'font-medium text-foreground'
                : 'text-muted-foreground font-normal',
            )}
          >
            {notification.title}
          </p>
        </div>
        {notification.description && (
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {notification.description}
          </p>
        )}
        <p className="text-[10px] text-muted-foreground mt-1">
          {timeAgo(notification.timestamp)}
        </p>
      </div>

      {/* Dismiss button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDismiss(notification.id);
        }}
        className="shrink-0 p-0.5 text-muted-foreground hover:text-foreground rounded transition-colors opacity-0 group-hover:opacity-100"
      >
        <X size={12} />
      </button>
    </div>
  );
}

export function NotificationDropdown() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const notifications = useNotificationStore((s) => s.notifications);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const showDismissed = useNotificationStore((s) => s.showDismissed);
  const markSeen = useNotificationStore((s) => s.markSeen);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const dismiss = useNotificationStore((s) => s.dismiss);
  const toggleShowDismissed = useNotificationStore((s) => s.toggleShowDismissed);

  // Stable callback ref for child components
  const handleMarkSeen = useCallback((id: string) => markSeen(id), [markSeen]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  // Filter: show non-dismissed, or all if showDismissed is on
  const visible = notifications
    .filter((n) => showDismissed || n.readState !== 'dismissed')
    .slice(0, 20);

  const dismissedCount = notifications.filter((n) => n.readState === 'dismissed').length;

  function handleClickNotification(n: Notification) {
    // Clicking immediately marks as seen
    if (n.readState === 'unread') {
      markSeen(n.id);
    }
    if (n.actionUrl) {
      navigate(n.actionUrl);
    }
    setOpen(false);
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : 'Notifications'}
        aria-haspopup="dialog"
        aria-expanded={open}
        className="relative inline-flex items-center justify-center min-w-[44px] min-h-[44px] p-2 text-muted-foreground hover:text-foreground hover:bg-accent/50 rounded-md transition-colors"
      >
        <Bell size={16} aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[16px] h-4 px-1 text-[9px] font-bold text-white bg-red-500 rounded-full leading-none">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-popover border border-border rounded-lg shadow-xl z-50 overflow-hidden animate-fade-in">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <h3 className="text-sm font-semibold">Notifications</h3>
            <div className="flex items-center gap-2">
              {dismissedCount > 0 && (
                <button
                  onClick={() => toggleShowDismissed()}
                  className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                  title={showDismissed ? 'Hide dismissed' : 'Show dismissed'}
                >
                  {showDismissed ? <EyeOff size={12} /> : <Eye size={12} />}
                  {dismissedCount}
                </button>
              )}
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead()}
                  className="text-xs text-primary hover:underline"
                >
                  Mark all read
                </button>
              )}
            </div>
          </div>

          {/* List */}
          <div className="max-h-[360px] overflow-y-auto">
            {visible.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                No notifications yet
              </div>
            ) : (
              visible.map((n) => (
                <NotificationRow
                  key={n.id}
                  notification={n}
                  onClickNotification={handleClickNotification}
                  onDismiss={dismiss}
                  onMarkSeen={handleMarkSeen}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
