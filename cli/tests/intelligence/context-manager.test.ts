import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ContextManager } from '../../src/core/context-manager.js';
import { StateManager } from '../../src/core/state.js';
import { SkillRegistry, Skill } from '../../src/core/skill-registry.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-context-test.db';

function makeSkill(name: string): Skill {
  return {
    name,
    command: `/team ${name.replace('team-', '')}`,
    description: `${name} skill`,
    filePath: `/mock/${name}.md`,
    category: 'team',
    isWriteOperation: false,
    keywords: name.split('-').filter(k => k.length > 2),
  };
}

describe('ContextManager', () => {
  let contextManager: ContextManager;
  let state: StateManager;
  let skills: SkillRegistry;

  beforeEach(() => {
    state = new StateManager(TEST_DB);
    state.initialize();
    state.initializePhase4();

    skills = new SkillRegistry();
    // Inject a few mock skills
    const skillNames = ['team-research', 'team-develop', 'team-fix', 'team-review', 'team-plan'];
    for (const name of skillNames) {
      (skills as any).skills.set(name, makeSkill(name));
    }

    contextManager = new ContextManager({ state, skills });
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  // --- Greeting ---

  it('buildGreeting includes project info and Ready', () => {
    const greeting = contextManager.buildGreeting();
    expect(greeting).toContain('Ready.');
    expect(greeting).toContain('skills loaded');
    // Each line should be <= 80 chars
    const lines = greeting.split('\n');
    for (const line of lines) {
      expect(line.length).toBeLessThanOrEqual(80);
    }
    expect(lines.length).toBeLessThanOrEqual(3);
  });

  it('buildGreeting includes last session info when available', () => {
    state.createSession('team-research', 'OAuth patterns', '/tmp');
    const greeting = contextManager.buildGreeting();
    expect(greeting).toContain('Last:');
    expect(greeting).toContain('team-research');
  });

  it('buildGreeting mentions interrupted sessions', () => {
    state.createSession('team-research', 'test', '/tmp');
    state.markRunningAsInterrupted();
    const greeting = contextManager.buildGreeting();
    expect(greeting).toContain('interrupted');
  });

  it('buildGreeting never exceeds 3 lines', () => {
    // Create some sessions to populate context
    state.createSession('team-research', 'test', '/tmp');
    state.markRunningAsInterrupted();
    const greeting = contextManager.buildGreeting();
    const lines = greeting.split('\n');
    expect(lines.length).toBeLessThanOrEqual(3);
  });

  // --- Exchanges ---

  it('records and retrieves recent exchanges', () => {
    contextManager.addExchange('research OAuth', 'Routing to team-research...');
    contextManager.addExchange('fix the bug', 'Routing to team-fix...');

    const recent = contextManager.getRecentExchanges(2);
    expect(recent).toContain('research OAuth');
    expect(recent).toContain('fix the bug');
  });

  it('getRecentExchanges returns (no recent exchanges) when empty', () => {
    const recent = contextManager.getRecentExchanges(3);
    expect(recent).toBe('(no recent exchanges)');
  });

  // --- Summarization ---

  it('does not summarize when exchange count < 10', async () => {
    for (let i = 0; i < 9; i++) {
      contextManager.addExchange(`input ${i}`, `output ${i}`);
    }
    await contextManager.summarizeIfNeeded('session-1');
    // Should still have 9 exchanges
    expect(contextManager.exchangeCount).toBe(9);
  });

  it('summarizes when exchange count >= 10 (local fallback)', async () => {
    state.createSessionWithId('session-1', 'direct', '', process.cwd());
    for (let i = 0; i < 12; i++) {
      contextManager.addExchange(`input ${i}`, `output ${i}`);
    }
    await contextManager.summarizeIfNeeded('session-1');

    // Should keep only last 5 exchanges
    expect(contextManager.exchangeCount).toBe(5);

    // Summary should be stored in DB
    const summaries = state.getRecentSummaries(1);
    expect(summaries.length).toBe(1);
    expect(summaries[0].summary).toContain('7 exchanges');
  });

  it('summarizes with Claude when available', async () => {
    const mockSummarize = async (_prompt: string) => 'Used team-research and team-fix. Completed OAuth research.';

    const ctxWithClaude = new ContextManager({
      state,
      skills,
      claudeSummarize: mockSummarize,
    });

    state.createSessionWithId('session-2', 'direct', '', process.cwd());
    for (let i = 0; i < 12; i++) {
      ctxWithClaude.addExchange(`input ${i}`, `output ${i}`);
    }
    await ctxWithClaude.summarizeIfNeeded('session-2');

    const summaries = state.getRecentSummaries(1);
    expect(summaries[0].summary).toContain('team-research');
  });

  // --- Context window ---

  it('buildContextWindow stays under token budget', () => {
    // Add exchanges
    for (let i = 0; i < 5; i++) {
      contextManager.addExchange(`input ${i}`, `output ${i}`);
    }

    const window = contextManager.buildContextWindow(1500);
    // 1500 tokens * 4 chars/token = 6000 chars max
    expect(window.length).toBeLessThanOrEqual(6000);
  });

  // --- Recommendations ---

  it('checkRecommendation returns suggestion when count >= 3', () => {
    state.recordSequence('team-research', 'team-develop');
    state.recordSequence('team-research', 'team-develop');
    state.recordSequence('team-research', 'team-develop');

    contextManager.resetRecommendationTimer();
    const rec = contextManager.checkRecommendation('team-research');
    expect(rec).toContain('team-develop');
    expect(rec).toContain('usually run');
  });

  it('checkRecommendation returns null when rate-limited', () => {
    state.recordSequence('team-research', 'team-develop');
    state.recordSequence('team-research', 'team-develop');
    state.recordSequence('team-research', 'team-develop');

    contextManager.resetRecommendationTimer();
    const rec1 = contextManager.checkRecommendation('team-research');
    expect(rec1).not.toBeNull();

    // Second call should be rate-limited
    const rec2 = contextManager.checkRecommendation('team-research');
    expect(rec2).toBeNull();
  });

  it('checkRecommendation returns null when count < 3', () => {
    state.recordSequence('team-research', 'team-develop');
    state.recordSequence('team-research', 'team-develop');

    contextManager.resetRecommendationTimer();
    const rec = contextManager.checkRecommendation('team-research');
    expect(rec).toBeNull();
  });
});
