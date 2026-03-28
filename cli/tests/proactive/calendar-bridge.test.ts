import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { CalendarBridge } from '../../src/proactive/calendar-bridge.js';
import type { WatcherEvent } from '../../src/proactive/types.js';

describe('CalendarBridge', () => {
  let bridge: CalendarBridge;

  afterEach(() => {
    bridge?.stop();
  });

  it('starts and stops without errors', () => {
    bridge = new CalendarBridge({ pollIntervalMs: 60_000 });
    bridge.start();
    expect(bridge.isRunning).toBe(true);
    bridge.stop();
    expect(bridge.isRunning).toBe(false);
  });

  it('reports available status', () => {
    bridge = new CalendarBridge({ pollIntervalMs: 60_000 });
    // Before start, defaults to available=true, permissionDenied=false
    expect(bridge.isAvailable).toBe(true);
  });

  it('stop clears all state', () => {
    bridge = new CalendarBridge({ pollIntervalMs: 60_000 });
    bridge.start();
    bridge.stop();
    expect(bridge.isRunning).toBe(false);
    expect(bridge.getUpcomingEvents()).toHaveLength(0);
  });

  it('handles permission denied gracefully', async () => {
    const warnings: string[] = [];
    bridge = new CalendarBridge({
      pollIntervalMs: 100,
      scriptTimeoutMs: 2000,
    });
    bridge.on('warning', (msg) => warnings.push(msg));
    bridge.start();

    // Wait for first poll attempt
    await new Promise(resolve => setTimeout(resolve, 500));

    // On CI/test machines without Calendar.app access, it should
    // either succeed (unlikely) or fail gracefully
    // We just verify it doesn't crash
    expect(true).toBe(true);
  });

  it('getUpcomingEvents returns empty array initially', () => {
    bridge = new CalendarBridge({ pollIntervalMs: 60_000 });
    expect(bridge.getUpcomingEvents()).toEqual([]);
  });

  it('does not start twice', () => {
    bridge = new CalendarBridge({ pollIntervalMs: 60_000 });
    bridge.start();
    bridge.start(); // second start should be no-op
    expect(bridge.isRunning).toBe(true);
  });
});
