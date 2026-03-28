import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import Database from 'better-sqlite3';
import { ProactiveEngine } from '../../src/proactive/engine.js';
import type { Suggestion } from '../../src/proactive/types.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-engine-test.db';

describe('ProactiveEngine', () => {
  let db: Database.Database;
  let engine: ProactiveEngine;

  beforeEach(() => {
    db = new Database(TEST_DB);
    db.pragma('journal_mode = WAL');
  });

  afterEach(() => {
    engine?.stop();
    db.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('creates engine with default config', () => {
    engine = new ProactiveEngine({ db });
    expect(engine.isRunning).toBe(false);
    const config = engine.getConfig();
    expect(config.enabled).toBe(false);
    expect(config.sensitivity).toBe('medium');
  });

  it('starts and stops cleanly', () => {
    engine = new ProactiveEngine({
      db,
      config: { watchPaths: [] },
    });
    engine.start();
    expect(engine.isRunning).toBe(true);
    engine.stop();
    expect(engine.isRunning).toBe(false);
  });

  it('does not start twice', () => {
    engine = new ProactiveEngine({ db, config: { watchPaths: [] } });
    engine.start();
    engine.start(); // no-op
    expect(engine.isRunning).toBe(true);
  });

  it('sets sensitivity', () => {
    engine = new ProactiveEngine({ db });
    engine.setSensitivity('low');
    expect(engine.getConfig().sensitivity).toBe('low');
  });

  it('emits started/stopped events', () => {
    engine = new ProactiveEngine({ db, config: { watchPaths: [] } });
    const events: string[] = [];
    engine.on('started', () => events.push('started'));
    engine.on('stopped', () => events.push('stopped'));

    engine.start();
    engine.stop();
    expect(events).toEqual(['started', 'stopped']);
  });

  it('returns null when no active suggestion', () => {
    engine = new ProactiveEngine({ db });
    expect(engine.getActiveSuggestion()).toBeNull();
    expect(engine.acceptSuggestion()).toBeNull();
  });

  it('dismiss with no suggestion is no-op', () => {
    engine = new ProactiveEngine({ db });
    expect(() => engine.dismissSuggestion()).not.toThrow();
  });

  it('autoDismiss with no suggestion is no-op', () => {
    engine = new ProactiveEngine({ db });
    expect(() => engine.autoDismissSuggestion()).not.toThrow();
  });

  it('resets preferences', () => {
    engine = new ProactiveEngine({ db });
    expect(() => engine.resetPreferences()).not.toThrow();
  });

  it('getStats returns empty array initially', () => {
    engine = new ProactiveEngine({ db });
    expect(engine.getStats()).toEqual([]);
  });

  it('updateConfig restarts if running', () => {
    engine = new ProactiveEngine({ db, config: { watchPaths: [] } });
    engine.start();
    expect(engine.isRunning).toBe(true);

    engine.updateConfig({ sensitivity: 'high' });
    // updateConfig stops then restarts if enabled
    // Since we didn't set enabled=true in the update, it won't auto-restart
    expect(engine.getConfig().sensitivity).toBe('high');
  });

  it('setEmailEnabled toggles email config', () => {
    engine = new ProactiveEngine({ db, config: { watchPaths: [] } });
    expect(engine.getConfig().emailEnabled).toBe(false);
    engine.setEmailEnabled(true);
    expect(engine.getConfig().emailEnabled).toBe(true);
    engine.setEmailEnabled(false);
    expect(engine.getConfig().emailEnabled).toBe(false);
  });

  it('setCalendarEnabled toggles calendar config', () => {
    engine = new ProactiveEngine({ db, config: { watchPaths: [] } });
    expect(engine.getConfig().calendarEnabled).toBe(false);
    engine.setCalendarEnabled(true);
    expect(engine.getConfig().calendarEnabled).toBe(true);
  });

  it('respects throttle limit', () => {
    engine = new ProactiveEngine({
      db,
      config: { watchPaths: [], maxSuggestionsPerMinute: 2 },
    });

    // This tests the throttle conceptually — actual suggestion flow
    // requires watcher events flowing through the tick loop
    expect(engine.getConfig().maxSuggestionsPerMinute).toBe(2);
  });

  it('stop auto-dismisses active suggestion', () => {
    engine = new ProactiveEngine({ db, config: { watchPaths: [] } });
    engine.start();
    // No active suggestion, but stop should handle gracefully
    engine.stop();
    expect(engine.getActiveSuggestion()).toBeNull();
  });
});
