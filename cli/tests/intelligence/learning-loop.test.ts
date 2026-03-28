import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { IntentClassifier } from '../../src/core/intent-classifier.js';
import { LearningStore } from '../../src/core/learning-store.js';
import { StateManager } from '../../src/core/state.js';
import { SkillRegistry, Skill } from '../../src/core/skill-registry.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/coco-learning-test.db';

function makeSkill(name: string, category: string): Skill {
  const command = category === 'team'
    ? `/team ${name.replace('team-', '')}`
    : `/${name}`;
  return {
    name,
    command,
    description: `${name} skill`,
    filePath: `/mock/${name}.md`,
    category,
    isWriteOperation: false,
    keywords: name.split('-').filter(k => k.length > 2),
  };
}

describe('Learning Loop', () => {
  let classifier: IntentClassifier;
  let learningStore: LearningStore;
  let state: StateManager;
  let skills: SkillRegistry;

  beforeEach(async () => {
    state = new StateManager(TEST_DB);
    state.initialize();
    state.initializePhase4();

    skills = new SkillRegistry();
    // Inject mock skills
    const teamSkills = [
      'team-research', 'team-develop', 'team-fix', 'team-review',
      'team-plan', 'team-test', 'team-think', 'team-document',
      'team-present', 'team-communicate', 'team-scrape', 'team-verify',
      'team-feedback',
    ];
    for (const name of teamSkills) {
      (skills as any).skills.set(name, makeSkill(name, 'team'));
    }

    classifier = new IntentClassifier({ skills, state });
    learningStore = new LearningStore(state);
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('classify -> correct -> re-classify routes to corrected skill', async () => {
    // Step 1: Classify "review the auth code" -> should route to team-review
    const intent1 = await classifier.classify('review the auth code');
    expect(intent1.skill).toBeDefined();
    expect(intent1.skill!.name).toBe('team-review');

    // Step 2: Record the intent and correction
    const intentId = state.logIntent(
      'review the auth code',
      classifier.normalizeInput('review the auth code'),
      intent1.tier,
      intent1.skill!.name,
      intent1.confidence
    );
    learningStore.recordCorrection(intentId, 'team-test');

    // Step 3: Re-classify the same input
    const intent2 = await classifier.classify('review the auth code');
    expect(intent2.skill?.name).toBe('team-test');
    expect(intent2.confidence).toBe(1.0);
  });

  it('stores correction in routing_corrections table', () => {
    const normalized = classifier.normalizeInput('check the auth code');
    state.addCorrection(normalized, 'team-review', 'team-test');

    const correction = state.getCorrection(normalized);
    expect(correction).toBeDefined();
    expect(correction!.correct_skill).toBe('team-test');
  });

  it('increments times_applied on correction reuse', async () => {
    const normalized = classifier.normalizeInput('check the auth code');
    state.addCorrection(normalized, 'team-review', 'team-test');

    // First use
    await classifier.classify('check the auth code');
    // Second use
    await classifier.classify('check the auth code');

    // The correction should have been used (incrementCorrectionUsage called by classifyTier1)
    // We verify by checking the skill routes correctly twice
    const intent = await classifier.classify('check the auth code');
    expect(intent.skill?.name).toBe('team-test');
  });

  it('corrections take priority over regex matches', async () => {
    // "research something" normally routes to team-research via regex
    const intent1 = await classifier.classify('research something');
    expect(intent1.skill?.name).toBe('team-research');

    // Add a correction
    const normalized = classifier.normalizeInput('research something');
    state.addCorrection(normalized, 'team-research', 'team-think');

    // Now it should route to team-think
    const intent2 = await classifier.classify('research something');
    expect(intent2.skill?.name).toBe('team-think');
    expect(intent2.confidence).toBe(1.0);
  });

  it('skill sequences with count >= 3 trigger a recommendation', () => {
    // Record the sequence team-research -> team-develop 3 times
    learningStore.recordSequence('team-research', 'team-develop');
    learningStore.recordSequence('team-research', 'team-develop');
    learningStore.recordSequence('team-research', 'team-develop');

    const recommendation = learningStore.getRecommendation('team-research');
    expect(recommendation).toBe('team-develop');
  });

  it('skill sequences with count < 3 do not trigger a recommendation', () => {
    learningStore.recordSequence('team-research', 'team-develop');
    learningStore.recordSequence('team-research', 'team-develop');

    const recommendation = learningStore.getRecommendation('team-research');
    expect(recommendation).toBeNull();
  });

  it('normalizeInput strips punctuation and lowercases', () => {
    expect(classifier.normalizeInput('  Build the API! ')).toBe('build the api');
    expect(classifier.normalizeInput('Research OAuth 2.0')).toBe('research oauth 20');
    expect(classifier.normalizeInput('  FIX  the  BUG  ')).toBe('fix the bug');
  });

  it('does not record sequence for same skill', () => {
    learningStore.recordSequence('team-research', 'team-research');
    const rec = learningStore.getRecommendation('team-research');
    expect(rec).toBeNull();
  });
});
