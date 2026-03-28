/**
 * macOS notification system — DISABLED.
 * Re-enable by setting COCO_NOTIFICATIONS=1 environment variable.
 */

export interface NotificationOptions {
  title: string;
  message: string;
  subtitle?: string;
  sound?: boolean;
}

export function notify(_options: NotificationOptions): void {
  // Disabled — notifications were too noisy
  return;
}

export function notifySessionComplete(_skill: string, _success: boolean, _summary?: string): void {
  return;
}

export function notifyQueueDrained(_completedCount: number): void {
  return;
}
