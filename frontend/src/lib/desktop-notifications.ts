/**
 * Desktop Notification API wrapper.
 *
 * Provides permission management and a simple `notify()` call that
 * fires native OS notifications via the Web Notification API.
 */

const STORAGE_KEY = 'coco:desktop-notifications-enabled';

/** Check whether the user has granted notification permission. */
export function isPermitted(): boolean {
  if (!('Notification' in window)) return false;
  return Notification.permission === 'granted';
}

/** Check whether the browser supports notifications at all. */
export function isSupported(): boolean {
  return 'Notification' in window;
}

/** Whether the user has opted-in via the settings toggle (localStorage). */
export function isEnabled(): boolean {
  return localStorage.getItem(STORAGE_KEY) === 'true';
}

/** Persist the user's opt-in preference. */
export function setEnabled(value: boolean): void {
  localStorage.setItem(STORAGE_KEY, String(value));
}

/**
 * Request notification permission from the browser.
 * Returns `true` if permission was granted, `false` otherwise.
 */
export async function requestPermission(): Promise<boolean> {
  if (!isSupported()) return false;
  if (Notification.permission === 'granted') return true;
  if (Notification.permission === 'denied') return false;

  const result = await Notification.requestPermission();
  return result === 'granted';
}

export interface NotifyOptions {
  body?: string;
  icon?: string;
  tag?: string;
  /** Auto-close after this many ms. Default: 5000. */
  timeout?: number;
}

/**
 * Show a desktop notification. No-ops silently if permission is missing
 * or the user has disabled notifications in settings.
 */
export function notify(title: string, options: NotifyOptions = {}): Notification | null {
  if (!isPermitted() || !isEnabled()) return null;

  const { timeout = 5000, ...rest } = options;

  const n = new Notification(title, {
    icon: rest.icon ?? '/favicon.svg',
    ...rest,
  });

  if (timeout > 0) {
    setTimeout(() => n.close(), timeout);
  }

  return n;
}
