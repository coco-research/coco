import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { Orchestrator } from '../src/core/orchestrator.js';
import { StateManager } from '../src/core/state.js';
import { SkillRegistry } from '../src/core/skill-registry.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-orch-test.db';

describe('Orchestrator — Intent Classification', () => {
  let orchestrator: Orchestrator;
  let state: StateManager;
  let skills: SkillRegistry;

  beforeEach(async () => {
    state = new StateManager(TEST_DB);
    state.initialize();
    skills = new SkillRegistry();
    await skills.loadAll();
    orchestrator = new Orchestrator({ state, skills });
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  // --- Meta-commands ---
  it('classifies /status as meta-command', () => {
    const intent = orchestrator.classifyIntent('/status');
    expect(intent.isMetaCommand).toBe(true);
    expect(intent.metaCommand).toBe('status');
  });

  it('classifies /quit as meta-command', () => {
    const intent = orchestrator.classifyIntent('/quit');
    expect(intent.isMetaCommand).toBe(true);
    expect(intent.metaCommand).toBe('quit');
  });

  it('classifies /help as meta-command', () => {
    const intent = orchestrator.classifyIntent('/help');
    expect(intent.isMetaCommand).toBe(true);
  });

  it('classifies /skills as meta-command', () => {
    const intent = orchestrator.classifyIntent('/skills');
    expect(intent.isMetaCommand).toBe(true);
    expect(intent.metaCommand).toBe('skills');
  });

  it('classifies /history as meta-command', () => {
    const intent = orchestrator.classifyIntent('/history');
    expect(intent.isMetaCommand).toBe(true);
    expect(intent.metaCommand).toBe('history');
  });

  // --- Direct slash commands ---
  it('classifies "/team research OAuth" as team-research', () => {
    const intent = orchestrator.classifyIntent('/team research OAuth patterns');
    expect(intent.skill?.name).toBe('team-research');
    expect(intent.confidence).toBeGreaterThan(0.9);
  });

  // --- Natural language routing ---
  it('routes "research OAuth patterns" to team-research', () => {
    const intent = orchestrator.classifyIntent('research OAuth patterns');
    expect(intent.skill?.name).toBe('team-research');
  });

  it('routes "fix the login bug" to team-fix', () => {
    const intent = orchestrator.classifyIntent('fix the login bug');
    expect(intent.skill?.name).toBe('team-fix');
  });

  it('routes "develop the auth module" to team-develop', () => {
    const intent = orchestrator.classifyIntent('develop the auth module');
    expect(intent.skill?.name).toBe('team-develop');
  });

  it('routes "review the API code" to team-review', () => {
    const intent = orchestrator.classifyIntent('review the API code');
    expect(intent.skill?.name).toBe('team-review');
  });

  it('routes "plan the next sprint" to team-plan', () => {
    const intent = orchestrator.classifyIntent('plan the next sprint');
    expect(intent.skill?.name).toBe('team-plan');
  });

  // --- Write operation detection ---
  it('marks develop as write operation', () => {
    const intent = orchestrator.classifyIntent('develop the auth module');
    expect(intent.skill?.isWriteOperation).toBe(true);
  });

  it('marks research as read-only', () => {
    const intent = orchestrator.classifyIntent('research OAuth patterns');
    expect(intent.skill?.isWriteOperation).toBe(false);
  });

  // --- No match ---
  it('returns null skill for unrelated input', () => {
    const intent = orchestrator.classifyIntent('what time is it');
    expect(intent.skill).toBeNull();
  });

  // --- Greeting ---
  it('generates a greeting with project info', () => {
    const greeting = orchestrator.getGreeting();
    expect(greeting).toContain('Ready.');
    expect(greeting).toContain('skills loaded.');
  });

  // --- Meta-command output via events ---
  it('/status emits output event', () => {
    const outputs: string[] = [];
    orchestrator.on('output', (data) => outputs.push(data.text));
    orchestrator.handleInput('/status');
    expect(outputs.length).toBeGreaterThan(0);
    expect(outputs[0]).toContain('No active sessions');
  });

  it('/help emits output with skill list', () => {
    const outputs: string[] = [];
    orchestrator.on('output', (data) => outputs.push(data.text));
    orchestrator.handleInput('/help');
    expect(outputs.length).toBeGreaterThan(0);
    expect(outputs[0]).toContain('Session commands:');
    expect(outputs[0]).toContain('Available skills:');
  });

  // The 20-input routing accuracy test:
  const ROUTING_TEST_CASES: Array<[string, string | null]> = [
    ['research OAuth 2.0 best practices', 'team-research'],
    ['investigate rate limiting patterns', 'team-research'],
    ['build an auth service', 'team-develop'],
    ['develop the payment module', 'team-develop'],
    ['fix the failing tests', 'team-fix'],
    ['debug the login issue', 'team-fix'],
    ['review the auth code', 'team-review'],
    ['audit the API endpoints', 'team-review'],
    ['plan the next sprint', 'team-plan'],
    ['create a roadmap for Q2', 'team-plan'],
    ['write tests for the service', 'team-test'],
    ['check test coverage', 'team-test'],
    ['think about the architecture options', 'team-think'],
    ['brainstorm solutions for caching', 'team-think'],
    ['/team research voice APIs', 'team-research'],
    ['/team develop auth', 'team-develop'],
    ['/team fix broken endpoint', 'team-fix'],
    ['/team review', 'team-review'],
    ['create documentation for the API', 'team-document'],
    ['present the Q2 results', 'team-present'],
  ];

  it('routes >= 80% of 20 test inputs correctly', () => {
    let correct = 0;
    const failures: string[] = [];

    for (const [input, expectedSkill] of ROUTING_TEST_CASES) {
      const intent = orchestrator.classifyIntent(input);
      const actualSkill = intent.skill?.name ?? null;
      if (actualSkill === expectedSkill) {
        correct++;
      } else {
        failures.push(`  "${input}" → expected ${expectedSkill}, got ${actualSkill}`);
      }
    }

    const accuracy = correct / ROUTING_TEST_CASES.length;
    console.log(`Routing accuracy: ${correct}/${ROUTING_TEST_CASES.length} (${(accuracy * 100).toFixed(0)}%)`);
    if (failures.length > 0) {
      console.log('Failures:');
      console.log(failures.join('\n'));
    }
    expect(accuracy).toBeGreaterThanOrEqual(0.8);
  });
});
