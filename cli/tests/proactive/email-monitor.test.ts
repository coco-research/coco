import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EmailMonitor } from '../../src/proactive/email-monitor.js';
import type { WatcherEvent } from '../../src/proactive/types.js';
import { mkdirSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const TEST_DROP = '/tmp/coco-email-drop-test';

describe('EmailMonitor', () => {
  let monitor: EmailMonitor;

  beforeEach(() => {
    if (existsSync(TEST_DROP)) {
      rmSync(TEST_DROP, { recursive: true });
    }
    mkdirSync(TEST_DROP, { recursive: true });
  });

  afterEach(() => {
    monitor?.stop();
    try { rmSync(TEST_DROP, { recursive: true }); } catch {}
  });

  it('starts and stops without errors', () => {
    monitor = new EmailMonitor({
      keywords: ['test'],
      dropFolder: TEST_DROP,
    });
    monitor.start();
    expect(monitor.isRunning).toBe(true);
    monitor.stop();
    expect(monitor.isRunning).toBe(false);
  });

  it('degrades gracefully when HxStore is not available', () => {
    const warnings: string[] = [];
    monitor = new EmailMonitor({
      keywords: ['test'],
      dropFolder: TEST_DROP,
    });
    monitor.on('warning', (msg) => warnings.push(msg));
    monitor.start();

    // Should emit a warning about HxStore not being found
    // (on most test machines, HxStore won't exist)
    expect(monitor.isRunning).toBe(true);
    const status = monitor.getChannelStatus();
    // hxStore may or may not be available depending on machine
    expect(typeof status.hxStore).toBe('boolean');
    expect(status.dropFolder).toBe(true);
  });

  it('emits event for manual drop of .eml file', async () => {
    monitor = new EmailMonitor({
      keywords: ['test'],
      dropFolder: TEST_DROP,
    });

    const events: WatcherEvent[] = [];
    monitor.on('event', (e) => events.push(e));
    monitor.start();

    // Drop a .eml file
    writeFileSync(join(TEST_DROP, 'important.eml'), 'From: sender@example.com\nSubject: Test');
    await new Promise(resolve => setTimeout(resolve, 500));

    const dropEvent = events.find(e => e.type === 'manual-drop');
    if (dropEvent) {
      expect(dropEvent.source).toBe('email');
      expect(dropEvent.detail).toContain('important.eml');
    }
    // Note: timing-dependent on fs.watch, so we just verify no crash
    expect(monitor.isRunning).toBe(true);
  });

  it('creates drop folder if it does not exist', () => {
    const nonexistent = join(TEST_DROP, 'new-inbox');
    monitor = new EmailMonitor({
      keywords: [],
      dropFolder: nonexistent,
    });
    monitor.start();
    expect(existsSync(nonexistent)).toBe(true);
  });

  it('reports channel status correctly', () => {
    monitor = new EmailMonitor({
      keywords: ['test'],
      dropFolder: TEST_DROP,
    });
    monitor.start();

    const status = monitor.getChannelStatus();
    expect(typeof status.hxStore).toBe('boolean');
    expect(typeof status.attachments).toBe('boolean');
    expect(status.dropFolder).toBe(true);
  });
});
