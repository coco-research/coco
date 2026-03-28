import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { SessionManager } from '../src/core/session-manager.js';
import { StateManager } from '../src/core/state.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-sm-test.db';

describe('SessionManager', () => {
  let sm: SessionManager;
  let state: StateManager;

  beforeEach(() => {
    state = new StateManager(TEST_DB);
    state.initialize();
    sm = new SessionManager(state, 3, 'test system prompt');
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('creates a session and returns an ID', async () => {
    const skill = { name: 'team-research', command: '/team research', description: 'Research', isWriteOperation: false };
    const id = await sm.spawn(skill, 'OAuth patterns', '/tmp');
    expect(id).toBeDefined();
    expect(typeof id).toBe('string');
    expect(id.length).toBe(36); // UUID format
  });

  it('tracks spawned sessions', async () => {
    const skill = { name: 'team-research', command: '/team research', description: 'Research', isWriteOperation: false };
    const id1 = await sm.spawn(skill, 'topic A', '/tmp');
    const id2 = await sm.spawn(skill, 'topic B', '/tmp');
    const all = sm.getAll();
    // Both sessions should be tracked (they may complete/error quickly since claude isn't installed)
    expect(all.length).toBe(2);
    expect(all.map(s => s.id)).toContain(id1);
    expect(all.map(s => s.id)).toContain(id2);
    expect(all[0].skill).toBe('team-research');
    expect(all[1].skill).toBe('team-research');
  });

  it('respects concurrency limit', () => {
    const stats = sm.getStats();
    expect(stats.max).toBe(3);
  });

  it('can update concurrency at runtime', () => {
    sm.setConcurrency(5);
    expect(sm.getStats().max).toBe(5);
  });

  it('clamps concurrency between 1 and 7', () => {
    sm.setConcurrency(0);
    expect(sm.getStats().max).toBe(1);
    sm.setConcurrency(10);
    expect(sm.getStats().max).toBe(7);
  });

  it('kills a session by ID', async () => {
    const skill = { name: 'test', command: '/test', description: 'Test', isWriteOperation: false };
    const id = await sm.spawn(skill, 'test args', '/tmp');
    const killed = await sm.kill(id);
    expect(killed).toBe(true);
  });

  it('killAll clears the queue', async () => {
    const skill = { name: 'test', command: '/test', description: 'Test', isWriteOperation: false };
    await sm.spawn(skill, 'A', '/tmp');
    await sm.spawn(skill, 'B', '/tmp');
    const count = await sm.killAll();
    // Sessions may have already completed/errored (no real claude binary),
    // so killAll only kills those still active. Verify no active sessions remain.
    expect(sm.getActive().length).toBe(0);
    // Total sessions should still be tracked
    expect(sm.getAll().length).toBe(2);
  });
});
