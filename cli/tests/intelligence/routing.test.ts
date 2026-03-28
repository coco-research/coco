import { describe, it, expect } from 'vitest';
import { TeamRouter } from '../../src/integrations/team-router.js';
import { GsdRouter } from '../../src/integrations/gsd-router.js';
import type { Skill } from '../../src/core/skill-registry.js';

function makeSkill(name: string, category: string): Skill {
  const command = category === 'team'
    ? `/team ${name.replace('team-', '')}`
    : `/gsd:${name}`;
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

describe('TeamRouter', () => {
  const router = new TeamRouter();

  const cases: Array<[string, string, string]> = [
    // [input, skillName, expectedArgsContains]
    ['research OAuth 2.0 best practices', 'team-research', 'OAuth 2.0 best practices'],
    ['look into AWS Lambda cold starts', 'team-research', 'AWS Lambda cold starts'],
    ['develop an auth service for the API', 'team-develop', 'auth service for the API'],
    ['build the payment module', 'team-develop', 'payment module'],
    ['fix the failing login tests', 'team-fix', 'failing login tests'],
    ['debug the session timeout issue', 'team-fix', 'session timeout issue'],
    ['review the payment module', 'team-review', 'payment module'],
    ['audit the API endpoints', 'team-review', 'API endpoints'],
    ['plan the next sprint', 'team-plan', 'next sprint'],
    ['write tests for the user service', 'team-test', 'user service'],
    ['think about the migration strategy', 'team-think', 'migration strategy'],
    ['create documentation for the REST API', 'team-document', 'REST API'],
    ['present the Q2 results', 'team-present', 'Q2 results'],
  ];

  for (const [input, skillName, expectedContains] of cases) {
    it(`extracts args for "${input}" -> "${expectedContains}"`, () => {
      const skill = makeSkill(skillName, 'team');
      const result = router.extractParams(skill, input);
      expect(result.args.toLowerCase()).toContain(expectedContains.toLowerCase());
      expect(result.command).toBe(skill.command);
    });
  }

  it('buildDispatch produces valid /team command string', () => {
    const skill = makeSkill('team-research', 'team');
    const dispatch = router.buildDispatch(skill, 'research OAuth patterns');
    expect(dispatch).toMatch(/^\/team research/);
    expect(dispatch).toContain('OAuth patterns');
  });

  it('strips leading filler words from args', () => {
    const skill = makeSkill('team-review', 'team');
    const result = router.extractParams(skill, 'review the API code');
    // "the" should be stripped
    expect(result.args).not.toMatch(/^the\b/i);
    expect(result.args.toLowerCase()).toContain('api code');
  });
});

describe('GsdRouter', () => {
  const router = new GsdRouter();

  it('extracts args for "start a new project for the billing system"', () => {
    const skill = makeSkill('new-project', 'gsd');
    const result = router.extractParams(skill, 'start a new project for the billing system');
    expect(result.args.toLowerCase()).toContain('billing system');
    expect(result.command).toBe('/gsd:new-project');
  });

  it('extracts empty args for "execute the current phase"', () => {
    const skill = makeSkill('execute-phase', 'gsd');
    const result = router.extractParams(skill, 'execute the current phase');
    // Most of the input IS the trigger, so args should be minimal
    expect(result.command).toBe('/gsd:execute-phase');
  });

  it('buildDispatch produces valid /gsd:action string', () => {
    const skill = makeSkill('new-project', 'gsd');
    const dispatch = router.buildDispatch(skill, 'start a new project for billing');
    expect(dispatch).toMatch(/^\/gsd:new-project/);
  });

  it('isGsdContext detects project/phase keywords', () => {
    expect(GsdRouter.isGsdContext('plan the next project phase')).toBe(true);
    expect(GsdRouter.isGsdContext('plan the next sprint')).toBe(false);
  });

  it('"plan the next sprint" does not match GSD triggers', () => {
    // This should NOT match GSD because no "phase" or "project" keyword
    expect(GsdRouter.isGsdContext('plan the next sprint')).toBe(false);
  });

  it('"plan the next project phase" matches GSD context', () => {
    expect(GsdRouter.isGsdContext('plan the next project phase')).toBe(true);
  });
});
