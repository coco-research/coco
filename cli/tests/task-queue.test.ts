import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { TaskQueue } from '../src/core/task-queue.js';
import { SessionManager } from '../src/core/session-manager.js';
import { StateManager } from '../src/core/state.js';
import { SkillRegistry } from '../src/core/skill-registry.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-tq-test.db';

describe('TaskQueue', () => {
  let tq: TaskQueue;
  let state: StateManager;
  let sm: SessionManager;
  let skills: SkillRegistry;

  beforeEach(async () => {
    state = new StateManager(TEST_DB);
    state.initialize();
    // Use concurrency of 0 by creating a SessionManager with max=1
    // and spawning 1 session to fill the slot, so enqueue won't auto-dispatch
    sm = new SessionManager(state, 3, 'test');
    skills = new SkillRegistry();
    await skills.loadAll();
    tq = new TaskQueue(state, sm, skills);
  });

  afterEach(() => {
    tq.stop();
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('enqueues a task and reports correct depth', () => {
    // Enqueue with a dependency on a non-existent session, so processNext won't dispatch
    const fakeSessionId = 'fake-session-id-that-does-not-exist';
    state.createSessionWithId(fakeSessionId, 'blocker', 'args', '/tmp');
    // Session is 'queued' not 'complete', so dependency blocks dispatch
    tq.enqueue('team-research', 'topic A', '/tmp', 0, fakeSessionId);
    tq.enqueue('team-develop', 'feature B', '/tmp', 0, fakeSessionId);
    expect(tq.depth).toBe(2);
  });

  it('removes a task from the queue', () => {
    const fakeSessionId = 'fake-session-blocker-remove';
    state.createSessionWithId(fakeSessionId, 'blocker', 'args', '/tmp');
    const id = tq.enqueue('team-research', 'topic', '/tmp', 0, fakeSessionId);
    expect(tq.remove(id)).toBe(true);
    expect(tq.depth).toBe(0);
  });

  it('clears all pending tasks', () => {
    const fakeSessionId = 'fake-session-blocker-clear';
    state.createSessionWithId(fakeSessionId, 'blocker', 'args', '/tmp');
    tq.enqueue('team-research', 'A', '/tmp', 0, fakeSessionId);
    tq.enqueue('team-develop', 'B', '/tmp', 0, fakeSessionId);
    const cleared = tq.clear();
    expect(cleared).toBe(2);
    expect(tq.depth).toBe(0);
  });

  it('promotes a task to front of queue', () => {
    const fakeSessionId = 'fake-session-blocker-promote';
    state.createSessionWithId(fakeSessionId, 'blocker', 'args', '/tmp');
    const id1 = tq.enqueue('team-research', 'A', '/tmp', 0, fakeSessionId);
    const _id2 = tq.enqueue('team-develop', 'B', '/tmp', 0, fakeSessionId);
    tq.promote(id1);
    const pending = tq.getPending();
    // After promote, id1 should have higher priority
    expect(pending[0]?.id).toBe(id1);
  });

  it('emits taskEnqueued event', () => {
    const handler = vi.fn();
    tq.on('taskEnqueued', handler);
    tq.enqueue('team-research', 'test', '/tmp');
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('emits queueCleared event', () => {
    const handler = vi.fn();
    tq.on('queueCleared', handler);
    const fakeSessionId = 'fake-session-blocker-cleared';
    state.createSessionWithId(fakeSessionId, 'blocker', 'args', '/tmp');
    tq.enqueue('team-research', 'test', '/tmp', 0, fakeSessionId);
    tq.clear();
    expect(handler).toHaveBeenCalledWith({ count: 1 });
  });
});
