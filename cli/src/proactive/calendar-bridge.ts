/**
 * Phase 5: Calendar Bridge
 *
 * Reads macOS Calendar.app via AppleScript to surface upcoming meetings.
 * Polled every 5 minutes. Gracefully degrades when permissions are denied.
 */

import { EventEmitter } from 'eventemitter3';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import type { WatcherEvent } from './types.js';

const execFileAsync = promisify(execFile);

export interface CalendarBridgeEvents {
  event: (event: WatcherEvent) => void;
  error: (err: Error) => void;
  warning: (msg: string) => void;
}

export interface CalendarEvent {
  title: string;
  startTime: Date;
  minutesUntil: number;
}

export interface CalendarBridgeConfig {
  /** Poll interval in ms (default: 300000 = 5 min) */
  pollIntervalMs?: number;
  /** Lookahead window in minutes (default: 60) */
  lookaheadMinutes?: number;
  /** AppleScript timeout in ms (default: 10000) */
  scriptTimeoutMs?: number;
}

function buildAppleScript(lookaheadMinutes: number): string {
  return `
tell application "Calendar"
  set now to current date
  set later to now + ${lookaheadMinutes} * 60
  set results to {}
  repeat with cal in calendars
    try
      repeat with evt in (every event of cal whose start date >= now and start date <= later)
        set end of results to (summary of evt & "|" & ((start date of evt) as string))
      end repeat
    end try
  end repeat
  return results as string
end tell
`;
}

export class CalendarBridge extends EventEmitter<CalendarBridgeEvents> {
  private running: boolean = false;
  private pollTimer: NodeJS.Timeout | null = null;
  private available: boolean = true;
  private permissionDenied: boolean = false;
  private lastEvents: Map<string, CalendarEvent> = new Map(); // title+time -> event
  private alerted15: Set<string> = new Set(); // events already alerted at 15 min
  private alerted5: Set<string> = new Set();  // events already alerted at 5 min

  private pollIntervalMs: number;
  private lookaheadMinutes: number;
  private scriptTimeoutMs: number;

  constructor(private config: CalendarBridgeConfig = {}) {
    super();
    this.pollIntervalMs = config.pollIntervalMs ?? 300_000;
    this.lookaheadMinutes = config.lookaheadMinutes ?? 60;
    this.scriptTimeoutMs = config.scriptTimeoutMs ?? 10_000;
  }

  /**
   * Start polling the calendar.
   */
  start(): void {
    if (this.running) return;
    this.running = true;

    // Immediate first poll
    this.poll();

    this.pollTimer = setInterval(() => {
      this.poll();
    }, this.pollIntervalMs);
  }

  /**
   * Stop polling.
   */
  stop(): void {
    this.running = false;
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    this.alerted15.clear();
    this.alerted5.clear();
    this.lastEvents.clear();
  }

  get isRunning(): boolean {
    return this.running;
  }

  get isAvailable(): boolean {
    return this.available && !this.permissionDenied;
  }

  /**
   * Poll Calendar.app for upcoming events.
   */
  private async poll(): Promise<void> {
    if (!this.running || this.permissionDenied) return;

    try {
      const { stdout } = await execFileAsync('osascript', ['-e', buildAppleScript(this.lookaheadMinutes)], {
        timeout: this.scriptTimeoutMs,
      });

      this.available = true;
      this.processCalendarOutput(stdout.trim());
    } catch (err: any) {
      const msg = err?.message ?? String(err);

      // Detect permission denial
      if (msg.includes('not allowed') || msg.includes('permission') || msg.includes('(-1743)')) {
        this.permissionDenied = true;
        this.available = false;
        this.emit('warning',
          'Calendar access denied. Go to System Settings > Privacy > Automation and enable Calendar for your terminal app.',
        );
        this.stop();
        return;
      }

      // Timeout or other transient error — skip this cycle
      if (msg.includes('timeout') || msg.includes('ETIMEDOUT')) {
        // Silently skip
        return;
      }

      // Calendar.app not running or other error
      this.available = false;
    }
  }

  /**
   * Parse AppleScript output and emit events for approaching meetings.
   */
  private processCalendarOutput(output: string): void {
    if (!output) return;

    const now = new Date();
    const entries = output.split(', ').filter(Boolean);

    const currentEvents = new Map<string, CalendarEvent>();

    for (const entry of entries) {
      const sepIdx = entry.lastIndexOf('|');
      if (sepIdx === -1) continue;

      const title = entry.substring(0, sepIdx).trim();
      const dateStr = entry.substring(sepIdx + 1).trim();

      let startTime: Date;
      try {
        startTime = new Date(dateStr);
        if (isNaN(startTime.getTime())) continue;
      } catch {
        continue;
      }

      const minutesUntil = (startTime.getTime() - now.getTime()) / 60_000;
      if (minutesUntil < 0 || minutesUntil > this.lookaheadMinutes) continue;

      const key = `${title}|${startTime.toISOString()}`;
      currentEvents.set(key, { title, startTime, minutesUntil });
    }

    this.lastEvents = currentEvents;

    // Emit events for meetings approaching
    for (const [key, event] of currentEvents) {
      // 15-minute alert
      if (event.minutesUntil <= 16 && event.minutesUntil > 5 && !this.alerted15.has(key)) {
        this.alerted15.add(key);
        this.emitCalendarEvent(event, 15);
      }

      // 5-minute alert
      if (event.minutesUntil <= 6 && event.minutesUntil > 0 && !this.alerted5.has(key)) {
        this.alerted5.add(key);
        this.emitCalendarEvent(event, 5);
      }
    }

    // Clean up old alerts
    for (const key of this.alerted15) {
      if (!currentEvents.has(key)) this.alerted15.delete(key);
    }
    for (const key of this.alerted5) {
      if (!currentEvents.has(key)) this.alerted5.delete(key);
    }
  }

  /**
   * Emit a watcher event for an approaching calendar event.
   */
  private emitCalendarEvent(event: CalendarEvent, minutesBefore: number): void {
    const titleLower = event.title.toLowerCase();
    let type: string;

    if (/standup|daily|scrum/i.test(titleLower)) {
      type = 'meeting-standup';
    } else if (/review|demo|retro/i.test(titleLower)) {
      type = 'meeting-review';
    } else {
      type = 'meeting-generic';
    }

    this.emit('event', {
      source: 'calendar',
      type,
      detail: `${event.title} in ${Math.round(event.minutesUntil)} min`,
      metadata: {
        title: event.title,
        startTime: event.startTime.toISOString(),
        minutesUntil: Math.round(event.minutesUntil),
        alertThreshold: minutesBefore,
      },
      timestamp: Date.now(),
    });
  }

  /**
   * Get upcoming events (for display/testing).
   */
  getUpcomingEvents(): CalendarEvent[] {
    return Array.from(this.lastEvents.values()).sort((a, b) => a.minutesUntil - b.minutesUntil);
  }
}
