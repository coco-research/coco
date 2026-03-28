import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { StateManager } from '../src/core/state.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-test.db';

describe('StateManager', () => {
  let state: StateManager;

  beforeEach(() => {
    state = new StateManager(TEST_DB);
    state.initialize();
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('creates and retrieves a session', () => {
    const id = state.createSession('team-research', 'OAuth patterns', '/tmp');
    const session = state.getSession(id);
    expect(session).toBeDefined();
    expect(session!.skill).toBe('team-research');
    expect(session!.status).toBe('running');
  });

  it('tracks skill usage', () => {
    state.incrementSkillUsage('team-research');
    state.incrementSkillUsage('team-research');
    state.incrementSkillUsage('team-develop');
    const usage = state.getSkillUsage();
    expect(usage[0].skill).toBe('team-research');
    expect(usage[0].count).toBe(2);
  });

  it('stores and retrieves input history', () => {
    state.addInputHistory('research OAuth');
    state.addInputHistory('fix the bug');
    const history = state.getInputHistory(10);
    expect(history).toEqual(['research OAuth', 'fix the bug']);
  });

  it('marks running sessions as interrupted', () => {
    state.createSession('team-research', 'test', '/tmp');
    const count = state.markRunningAsInterrupted();
    expect(count).toBe(1);
    const interrupted = state.getInterruptedSessions();
    expect(interrupted.length).toBe(1);
  });

  it('appends output with 10KB cap', () => {
    const id = state.createSession('team-research', 'test', '/tmp');
    const bigChunk = 'x'.repeat(12000);
    state.appendSessionOutput(id, bigChunk);
    const session = state.getSession(id);
    expect(session!.output.length).toBeLessThanOrEqual(10240);
  });
});

describe('StateManager -- Phase 2 Queue', () => {
  let state: StateManager;

  beforeEach(() => {
    state = new StateManager(TEST_DB);
    state.initialize();
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('enqueues and dequeues tasks in priority order', () => {
    state.enqueueTask('team-research', 'topic A', '/tmp', 0);
    state.enqueueTask('team-develop', 'feature B', '/tmp', 10); // higher priority
    const task = state.dequeueTask();
    expect(task?.skill).toBe('team-develop'); // higher priority first
  });

  it('respects dependency -- blocks until dependency completes', () => {
    const sessionId = state.createSession('team-research', 'prereq', '/tmp');
    state.enqueueTask('team-develop', 'depends on research', '/tmp', 0, sessionId);
    // While session is 'running', dequeue should return undefined
    const task1 = state.dequeueTask();
    expect(task1).toBeUndefined();
    // Complete the dependency
    state.updateSessionStatus(sessionId, 'complete');
    const task2 = state.dequeueTask();
    expect(task2?.skill).toBe('team-develop');
  });

  it('promotes a task to front of queue', () => {
    const id1 = state.enqueueTask('team-research', 'A', '/tmp', 0);
    const _id2 = state.enqueueTask('team-develop', 'B', '/tmp', 0);
    state.promoteTask(id1); // promote A to front
    const task = state.dequeueTask();
    expect(task?.id).toBe(id1);
  });

  it('clears the queue', () => {
    state.enqueueTask('team-research', 'A', '/tmp');
    state.enqueueTask('team-develop', 'B', '/tmp');
    const cleared = state.clearQueue();
    expect(cleared).toBe(2);
    expect(state.getQueueDepth()).toBe(0);
  });

  it('creates session with caller-supplied ID', () => {
    const id = 'test-uuid-1234-5678-9abc-def012345678';
    state.createSessionWithId(id, 'team-research', 'test args', '/tmp');
    const session = state.getSession(id);
    expect(session).toBeDefined();
    expect(session!.id).toBe(id);
    expect(session!.skill).toBe('team-research');
    expect(session!.status).toBe('queued');
  });

  it('detaches and retrieves detached sessions', () => {
    const id = state.createSession('team-research', 'test', '/tmp');
    // createSession sets status to 'running'
    state.detachSession(id);
    const detached = state.getDetachedSessions();
    expect(detached.length).toBe(1);
    expect(detached[0].id).toBe(id);
  });
});
