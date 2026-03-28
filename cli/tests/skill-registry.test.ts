import { describe, it, expect, beforeEach } from 'vitest';
import { SkillRegistry } from '../src/core/skill-registry.js';

describe('SkillRegistry', () => {
  let registry: SkillRegistry;

  beforeEach(async () => {
    registry = new SkillRegistry();
    await registry.loadAll();
  });

  it('discovers skills from ~/.claude/commands/', () => {
    expect(registry.size).toBeGreaterThan(0);
    console.log(`Discovered ${registry.size} skills`);
  });

  it('parses team-research correctly', () => {
    const skill = registry.get('team-research');
    expect(skill).toBeDefined();
    expect(skill!.category).toBe('team');
    expect(skill!.command).toBe('/team research');
  });

  it('finds skill by keyword "research OAuth"', () => {
    const skill = registry.findByKeyword('research OAuth patterns');
    expect(skill).toBeDefined();
    expect(skill!.name).toBe('team-research');
  });

  it('finds skill by slash command "/team develop"', () => {
    const skill = registry.findByKeyword('/team develop the auth service');
    expect(skill).toBeDefined();
    expect(skill!.name).toBe('team-develop');
  });

  it('generates prompt context', () => {
    const context = registry.toPromptContext();
    expect(context).toContain('Available skills:');
    expect(context).toContain('/team research');
  });

  it('marks write operations correctly', () => {
    const develop = registry.get('team-develop');
    expect(develop?.isWriteOperation).toBe(true);
    const research = registry.get('team-research');
    expect(research?.isWriteOperation).toBe(false);
  });
});
