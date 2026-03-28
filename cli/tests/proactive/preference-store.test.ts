import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import Database from 'better-sqlite3';
import { PreferenceStore } from '../../src/proactive/preference-store.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-pref-test.db';

describe('PreferenceStore', () => {
  let db: Database.Database;
  let store: PreferenceStore;

  beforeEach(() => {
    db = new Database(TEST_DB);
    db.pragma('journal_mode = WAL');
    store = new PreferenceStore(db);
  });

  afterEach(() => {
    db.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('records an accepted outcome', () => {
    store.recordOutcome({
      ruleId: 'file:test-added',
      source: 'file',
      actionText: 'Run tests?',
      skillRoute: 'team-test',
      confidence: 0.80,
      outcome: 'accepted',
    });

    const prefs = store.getPrefs('file:test-added');
    expect(prefs).toBeDefined();
    expect(prefs!.acceptCount).toBe(1);
    expect(prefs!.dismissCount).toBe(0);
    expect(prefs!.lastAccepted).toBeGreaterThan(0);
  });

  it('records a dismissed outcome', () => {
    store.recordOutcome({
      ruleId: 'file:test-added',
      source: 'file',
      actionText: 'Run tests?',
      skillRoute: 'team-test',
      confidence: 0.80,
      outcome: 'dismissed',
    });

    const prefs = store.getPrefs('file:test-added');
    expect(prefs!.dismissCount).toBe(1);
    expect(prefs!.lastDismissed).toBeGreaterThan(0);
  });

  it('computes positive confidence adjustment for accepted suggestions', () => {
    // Accept 5 times
    for (let i = 0; i < 5; i++) {
      store.recordOutcome({
        ruleId: 'file:test',
        source: 'file',
        actionText: 'test',
        skillRoute: 'test',
        confidence: 0.80,
        outcome: 'accepted',
      });
    }

    const adj = store.getConfidenceAdj('file:test');
    expect(adj).toBeGreaterThan(0);
    expect(adj).toBeLessThanOrEqual(0.2);
  });

  it('computes negative confidence adjustment for dismissed suggestions', () => {
    // Dismiss 5 times
    for (let i = 0; i < 5; i++) {
      store.recordOutcome({
        ruleId: 'file:test',
        source: 'file',
        actionText: 'test',
        skillRoute: 'test',
        confidence: 0.80,
        outcome: 'dismissed',
      });
    }

    const adj = store.getConfidenceAdj('file:test');
    expect(adj).toBeLessThan(0);
    expect(adj).toBeGreaterThanOrEqual(-0.3);
  });

  it('signals auto-disable after 10 dismissals with 0 accepts', () => {
    let shouldDisable = false;
    for (let i = 0; i < 10; i++) {
      const result = store.recordOutcome({
        ruleId: 'annoying-rule',
        source: 'file',
        actionText: 'test',
        skillRoute: 'test',
        confidence: 0.80,
        outcome: 'dismissed',
      });
      shouldDisable = result.shouldDisable;
    }

    expect(shouldDisable).toBe(true);
  });

  it('does not auto-disable if there are some accepts', () => {
    // 1 accept + 10 dismissals
    store.recordOutcome({
      ruleId: 'mixed-rule',
      source: 'file',
      actionText: 'test',
      skillRoute: 'test',
      confidence: 0.80,
      outcome: 'accepted',
    });

    let shouldDisable = false;
    for (let i = 0; i < 10; i++) {
      const result = store.recordOutcome({
        ruleId: 'mixed-rule',
        source: 'file',
        actionText: 'test',
        skillRoute: 'test',
        confidence: 0.80,
        outcome: 'dismissed',
      });
      shouldDisable = result.shouldDisable;
    }

    expect(shouldDisable).toBe(false);
  });

  it('returns stats for all rules', () => {
    store.recordOutcome({
      ruleId: 'rule-a',
      source: 'file',
      actionText: 'test',
      skillRoute: 'test',
      confidence: 0.80,
      outcome: 'accepted',
    });
    store.recordOutcome({
      ruleId: 'rule-b',
      source: 'email',
      actionText: 'test',
      skillRoute: 'test',
      confidence: 0.70,
      outcome: 'dismissed',
    });

    const stats = store.getStats();
    expect(stats).toHaveLength(2);
    const ruleA = stats.find(s => s.ruleId === 'rule-a');
    expect(ruleA!.acceptCount).toBe(1);
    expect(ruleA!.acceptRate).toBeGreaterThan(0);
  });

  it('resets all preferences', () => {
    store.recordOutcome({
      ruleId: 'file:test',
      source: 'file',
      actionText: 'test',
      skillRoute: 'test',
      confidence: 0.80,
      outcome: 'accepted',
    });

    store.resetAll();
    expect(store.getPrefs('file:test')).toBeUndefined();
    expect(store.getStats()).toHaveLength(0);
  });

  it('returns 0 for unknown rule confidence adjustment', () => {
    expect(store.getConfidenceAdj('nonexistent')).toBe(0);
  });

  it('expired outcomes do not change accept/dismiss counts', () => {
    store.recordOutcome({
      ruleId: 'file:test',
      source: 'file',
      actionText: 'test',
      skillRoute: 'test',
      confidence: 0.80,
      outcome: 'expired',
    });

    // Prefs row should exist from the log, but counts should be 0
    // Actually, expired doesn't create a prefs row if one doesn't exist
    const adj = store.getConfidenceAdj('file:test');
    expect(adj).toBe(0);
  });
});
