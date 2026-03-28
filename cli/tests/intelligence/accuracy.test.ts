import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { IntentClassifier } from '../../src/core/intent-classifier.js';
import { StateManager } from '../../src/core/state.js';
import { SkillRegistry, Skill } from '../../src/core/skill-registry.js';
import { unlinkSync } from 'node:fs';
import testQueries from './test-queries.json';

const TEST_DB = '/tmp/coco-accuracy-test.db';

// Build a mock SkillRegistry with the 18 team skills + 5 GSD skills
function buildTestRegistry(): SkillRegistry {
  const registry = new SkillRegistry();

  // Use internal map via loadAll override - we'll use a simulated approach
  // by loading the real registry (it reads from disk)
  return registry;
}

// Create a minimal skill for the registry
function makeSkill(name: string, category: string): Skill {
  const command = category === 'team'
    ? `/team ${name.replace('team-', '')}`
    : category === 'gsd'
    ? `/gsd:${name}`
    : `/${name}`;

  return {
    name,
    command,
    description: `${name} skill`,
    filePath: `/mock/${name}.md`,
    category,
    isWriteOperation: /develop|fix|build|create|execute/.test(name),
    keywords: name.split('-').filter(k => k.length > 2),
  };
}

describe('50-Query Accuracy Test', () => {
  let classifier: IntentClassifier;
  let state: StateManager;
  let skills: SkillRegistry;

  beforeEach(async () => {
    state = new StateManager(TEST_DB);
    state.initialize();
    state.initializePhase4();

    skills = new SkillRegistry();
    await skills.loadAll();

    // If no skills loaded from disk (test env), inject mock skills
    if (skills.size === 0) {
      // Access internal map to inject test skills
      const teamSkills = [
        'team-research', 'team-develop', 'team-fix', 'team-review',
        'team-plan', 'team-test', 'team-think', 'team-document',
        'team-present', 'team-communicate', 'team-scrape', 'team-verify',
        'team-feedback',
      ];
      const gsdSkills = [
        'new-project', 'execute-phase', 'plan-phase', 'verify-work', 'health',
      ];

      for (const name of teamSkills) {
        (skills as any).skills.set(name, makeSkill(name, 'team'));
      }
      for (const name of gsdSkills) {
        (skills as any).skills.set(name, makeSkill(name, 'gsd'));
      }
    }

    classifier = new IntentClassifier({ skills, state });
  });

  afterEach(() => {
    state.close();
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
  });

  it('achieves >= 90% accuracy on the 50-query test set', async () => {
    let correct = 0;
    const failures: string[] = [];
    const total = testQueries.length;

    for (const query of testQueries) {
      const intent = await classifier.classify(query.input);
      const actualSkill = intent.skill?.name ?? null;

      if (actualSkill === query.expected_skill) {
        correct++;
      } else {
        failures.push(
          `  "${query.input}" [${query.category}] -> expected ${query.expected_skill}, got ${actualSkill}`
        );
      }
    }

    const accuracy = correct / total;
    console.log(`\nAccuracy: ${correct}/${total} (${(accuracy * 100).toFixed(0)}%)`);
    if (failures.length > 0) {
      console.log('Failures:');
      console.log(failures.join('\n'));
    }

    expect(accuracy).toBeGreaterThanOrEqual(0.9);
  });
});
