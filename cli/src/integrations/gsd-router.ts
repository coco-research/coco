import type { Skill } from '../core/skill-registry.js';

/**
 * Trigger word lists per GSD skill.
 */
const GSD_TRIGGER_WORDS: Record<string, RegExp> = {
  'new-project':    /\b(start|create|new)\s+(a\s+)?(new\s+)?project\s*(for)?\b/gi,
  'execute-phase':  /\b(execute|run)\s+(the\s+)?(current\s+)?phase\b/gi,
  'plan-phase':     /\b(plan)\s+(the\s+)?(next\s+)?phase\b/gi,
  'verify-work':    /\b(verify|check)\s+(the\s+)?(last\s+|previous\s+)?(phase|work)\b/gi,
  'health':         /\b(project\s+health|health\s+check|project\s+status)\b/gi,
};

/** Leading filler words to strip */
const LEADING_FILLER = /^(the|a|an|for|about|on|with|of|some|my|our|this|that)\s+/i;

/**
 * GsdRouter extracts structured parameters from natural language inputs
 * that have been classified as targeting a /gsd command.
 */
export class GsdRouter {
  /**
   * Extract the meaningful argument from raw input after stripping GSD trigger words.
   */
  extractParams(skill: Skill, rawInput: string): { command: string; args: string } {
    const triggerPattern = GSD_TRIGGER_WORDS[skill.name];
    let args = rawInput;

    if (triggerPattern) {
      triggerPattern.lastIndex = 0;
      args = args.replace(triggerPattern, '');
    }

    // Clean up
    args = args.replace(/\s+/g, ' ').trim();

    // Strip leading filler words
    for (let i = 0; i < 3; i++) {
      const before = args;
      args = args.replace(LEADING_FILLER, '');
      if (args === before) break;
    }

    args = args.trim();

    const command = `/gsd:${skill.name}`;

    return { command, args };
  }

  /**
   * Build the full dispatch string: "/gsd:new-project billing system"
   */
  buildDispatch(skill: Skill, rawInput: string): string {
    const { command, args } = this.extractParams(skill, rawInput);
    return args ? `${command} ${args}` : command;
  }

  /**
   * Check if a text likely targets GSD (contains "project" or "phase" keywords).
   * Used for disambiguation when input matches both team and GSD patterns.
   */
  static isGsdContext(text: string): boolean {
    return /\b(project|phase)\b/i.test(text);
  }
}
