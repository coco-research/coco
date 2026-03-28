import { describe, it, expect, beforeEach } from 'vitest';
import { TriggerEngine } from '../../src/proactive/trigger-engine.js';
import type { TriggerRule, WatcherEvent } from '../../src/proactive/types.js';

function makeEvent(overrides: Partial<WatcherEvent> = {}): WatcherEvent {
  return {
    source: 'file',
    type: 'change',
    path: '/tmp/project/src/app.ts',
    detail: 'change: app.ts',
    timestamp: Date.now(),
    ...overrides,
  };
}

const testRule: TriggerRule = {
  id: 'file:test-added',
  source: 'file',
  condition: (e) => e.type === 'add' && /\.test\.ts$/.test(e.path ?? ''),
  actionTemplate: 'New test: {filename}. Run tests?',
  skillRoute: 'team-test',
  baseConfidence: 0.80,
  cooldownMs: 5000,
};

describe('TriggerEngine', () => {
  let engine: TriggerEngine;

  beforeEach(() => {
    engine = new TriggerEngine();
  });

  it('registers and counts rules', () => {
    engine.register(testRule);
    expect(engine.size).toBe(1);
  });

  it('matches events against registered rules', () => {
    engine.register(testRule);
    const event = makeEvent({ type: 'add', path: '/tmp/project/src/foo.test.ts' });
    const triggers = engine.match([event]);
    expect(triggers).toHaveLength(1);
    expect(triggers[0].ruleId).toBe('file:test-added');
    expect(triggers[0].actionText).toContain('foo.test.ts');
  });

  it('does not match events that fail the condition', () => {
    engine.register(testRule);
    const event = makeEvent({ type: 'change', path: '/tmp/project/src/foo.test.ts' });
    const triggers = engine.match([event]);
    expect(triggers).toHaveLength(0);
  });

  it('does not match events with wrong source', () => {
    engine.register(testRule);
    const event = makeEvent({ source: 'email', type: 'add', path: '/tmp/foo.test.ts' });
    const triggers = engine.match([event]);
    expect(triggers).toHaveLength(0);
  });

  it('enforces cooldown between matches', () => {
    engine.register({ ...testRule, cooldownMs: 60_000 });
    const event = makeEvent({ type: 'add', path: '/tmp/foo.test.ts' });

    const first = engine.match([event]);
    expect(first).toHaveLength(1);

    const second = engine.match([event]);
    expect(second).toHaveLength(0);
  });

  it('respects disabled rules', () => {
    engine.register(testRule);
    engine.disableRule('file:test-added');

    const event = makeEvent({ type: 'add', path: '/tmp/foo.test.ts' });
    const triggers = engine.match([event]);
    expect(triggers).toHaveLength(0);

    engine.enableRule('file:test-added');
    engine.resetCooldowns();
    const triggers2 = engine.match([event]);
    expect(triggers2).toHaveLength(1);
  });

  it('handles multiple rules and multiple events', () => {
    const changeRule: TriggerRule = {
      id: 'file:change',
      source: 'file',
      condition: (e) => e.type === 'change',
      actionTemplate: 'File changed: {filename}',
      skillRoute: 'direct',
      baseConfidence: 0.60,
      cooldownMs: 0,
    };

    engine.register(testRule);
    engine.register(changeRule);

    const events = [
      makeEvent({ type: 'add', path: '/tmp/foo.test.ts' }),
      makeEvent({ type: 'change', path: '/tmp/bar.ts' }),
    ];

    const triggers = engine.match(events);
    expect(triggers).toHaveLength(2);
  });

  it('interpolates template variables', () => {
    engine.register(testRule);
    const event = makeEvent({ type: 'add', path: '/tmp/project/utils.test.ts', detail: 'added utils test' });
    const triggers = engine.match([event]);
    expect(triggers[0].actionText).toBe('New test: utils.test.ts. Run tests?');
  });

  it('resets cooldowns', () => {
    engine.register({ ...testRule, cooldownMs: 999_999 });
    const event = makeEvent({ type: 'add', path: '/tmp/foo.test.ts' });

    engine.match([event]);
    expect(engine.match([event])).toHaveLength(0);

    engine.resetCooldowns();
    expect(engine.match([event])).toHaveLength(1);
  });

  it('getRulesBySource filters correctly', () => {
    engine.register(testRule);
    engine.register({
      ...testRule,
      id: 'email:test',
      source: 'email',
    });

    expect(engine.getRulesBySource('file')).toHaveLength(1);
    expect(engine.getRulesBySource('email')).toHaveLength(1);
    expect(engine.getRulesBySource('calendar')).toHaveLength(0);
  });

  it('handles condition that throws', () => {
    engine.register({
      ...testRule,
      id: 'bad-rule',
      condition: () => { throw new Error('boom'); },
    });

    const event = makeEvent({ type: 'add', path: '/tmp/foo.test.ts' });
    const triggers = engine.match([event]);
    expect(triggers).toHaveLength(0); // Should not crash, just skip
  });
});
