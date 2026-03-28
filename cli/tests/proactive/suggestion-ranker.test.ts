import { describe, it, expect, beforeEach } from 'vitest';
import { SuggestionRanker, type RankerContext } from '../../src/proactive/suggestion-ranker.js';
import type { RawTrigger, ProactiveConfig } from '../../src/proactive/types.js';
import { DEFAULT_CONFIG } from '../../src/proactive/types.js';

function makeTrigger(overrides: Partial<RawTrigger> = {}): RawTrigger {
  return {
    ruleId: 'file:test-added',
    source: 'file',
    actionText: 'Run tests?',
    skillRoute: 'team-test',
    baseConfidence: 0.80,
    event: {
      source: 'file',
      type: 'add',
      path: '/tmp/foo.test.ts',
      timestamp: Date.now(),
    },
    firedAt: Date.now(),
    ...overrides,
  };
}

const defaultContext: RankerContext = {
  activeSkills: [],
  recentPaths: [],
  currentHour: 14, // 2pm
};

describe('SuggestionRanker', () => {
  let ranker: SuggestionRanker;
  const config: ProactiveConfig = { ...DEFAULT_CONFIG, sensitivity: 'medium' };

  beforeEach(() => {
    ranker = new SuggestionRanker(null);
    ranker.reset();
  });

  it('produces suggestions from triggers above threshold', () => {
    const triggers = [makeTrigger({ baseConfidence: 0.80 })];
    const suggestions = ranker.rank(triggers, config, defaultContext);
    expect(suggestions).toHaveLength(1);
    expect(suggestions[0].text).toBe('Run tests?');
    expect(suggestions[0].confidence).toBeGreaterThanOrEqual(0.70);
  });

  it('filters out triggers below sensitivity threshold', () => {
    const triggers = [makeTrigger({ baseConfidence: 0.50 })];
    const suggestions = ranker.rank(triggers, config, defaultContext);
    expect(suggestions).toHaveLength(0);
  });

  it('low sensitivity only passes high confidence', () => {
    const lowConfig = { ...config, sensitivity: 'low' as const };
    const triggers = [makeTrigger({ baseConfidence: 0.80 })];
    const suggestions = ranker.rank(triggers, lowConfig, defaultContext);
    expect(suggestions).toHaveLength(0); // 0.80 < 0.85 threshold for low
  });

  it('high sensitivity passes lower confidence', () => {
    const highConfig = { ...config, sensitivity: 'high' as const };
    const triggers = [makeTrigger({ baseConfidence: 0.55 })];
    const suggestions = ranker.rank(triggers, highConfig, defaultContext);
    expect(suggestions).toHaveLength(1);
  });

  it('reduces confidence when suggestion overlaps active skill', () => {
    const triggers = [makeTrigger({ baseConfidence: 0.75, skillRoute: 'team-test' })];
    const context = { ...defaultContext, activeSkills: ['team-test'] };
    const suggestions = ranker.rank(triggers, config, context);
    // 0.75 - 0.15 = 0.60, below medium threshold of 0.70
    expect(suggestions).toHaveLength(0);
  });

  it('boosts confidence for recently worked paths', () => {
    const triggers = [makeTrigger({
      baseConfidence: 0.68,
      event: {
        source: 'file',
        type: 'add',
        path: '/tmp/project/src/foo.test.ts',
        timestamp: Date.now(),
      },
    })];
    const context = { ...defaultContext, recentPaths: ['/tmp/project/src'] };
    const suggestions = ranker.rank(triggers, config, context);
    // 0.68 + 0.10 = 0.78, above medium threshold
    expect(suggestions).toHaveLength(1);
  });

  it('reduces confidence outside business hours', () => {
    const triggers = [makeTrigger({ baseConfidence: 0.72 })];
    const context = { ...defaultContext, currentHour: 22 }; // 10pm
    const suggestions = ranker.rank(triggers, config, context);
    // 0.72 - 0.10 = 0.62, below medium threshold
    expect(suggestions).toHaveLength(0);
  });

  it('deduplicates triggers with same skillRoute', () => {
    const triggers = [
      makeTrigger({ baseConfidence: 0.75, skillRoute: 'team-test' }),
      makeTrigger({ baseConfidence: 0.85, skillRoute: 'team-test', actionText: 'Better suggestion' }),
    ];
    const suggestions = ranker.rank(triggers, config, defaultContext);
    expect(suggestions).toHaveLength(1);
    expect(suggestions[0].text).toBe('Better suggestion'); // Higher confidence wins
  });

  it('sorts suggestions by confidence descending', () => {
    const triggers = [
      makeTrigger({ baseConfidence: 0.75, skillRoute: 'team-test' }),
      makeTrigger({ baseConfidence: 0.90, skillRoute: 'direct', actionText: 'High priority' }),
    ];
    const suggestions = ranker.rank(triggers, config, defaultContext);
    expect(suggestions).toHaveLength(2);
    expect(suggestions[0].text).toBe('High priority');
  });

  it('sets expiry timestamp based on config', () => {
    const customConfig = { ...config, suggestionTtlMs: 15_000 };
    const triggers = [makeTrigger()];
    const before = Date.now();
    const suggestions = ranker.rank(triggers, customConfig, defaultContext);
    expect(suggestions[0].expiresAt).toBeGreaterThanOrEqual(before + 15_000);
  });
});
