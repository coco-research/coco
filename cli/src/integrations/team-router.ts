import type { Skill } from '../core/skill-registry.js';

/**
 * Trigger word lists per team skill.
 * When a skill is matched, these words are stripped from the input
 * to extract the meaningful argument.
 */
const TRIGGER_WORDS: Record<string, RegExp> = {
  'team-research':     /\b(research|investigate|explore|look\s+into|find\s+out\s+about|find\s+out)\b/gi,
  'team-develop':      /\b(develop|implement|build|create)\b/gi,
  'team-fix':          /\b(fix|debug|troubleshoot|repair|patch)\b/gi,
  'team-review':       /\b(review|audit|inspect|evaluate|assess|code\s+review)\b/gi,
  'team-plan':         /\b(plan|roadmap|prioriti[sz]e|schedule)\b/gi,
  'team-test':         /\b(test|write\s+tests?\s+for|add\s+coverage\s+for|write\s+tests|add\s+tests)\b/gi,
  'team-think':        /\b(think\s+about|brainstorm|ideate|consider|reason\s+about|analyse|analyze)\b/gi,
  'team-document':     /\b(document|documentation|docs|write\s+docs|api\s+docs)\b/gi,
  'team-present':      /\b(present|presentation|slides|demo|showcase)\b/gi,
  'team-communicate':  /\b(communicate|announce|notify|message|update\s+the\s+team)\b/gi,
  'team-scrape':       /\b(scrape|crawl|extract\s+from|fetch\s+page)\b/gi,
  'team-verify':       /\b(verify|validate|confirm|check\s+quality)\b/gi,
  'team-feedback':     /\b(feedback|retro|retrospective|critique)\b/gi,
};

/** Leading filler words to strip from extracted args */
const LEADING_FILLER = /^(the|a|an|for|about|on|with|of|some|my|our|this|that)\s+/i;

/**
 * TeamRouter extracts structured parameters from natural language inputs
 * that have already been classified as targeting a /team skill.
 */
export class TeamRouter {
  /**
   * Extract the meaningful argument from raw input after stripping trigger words.
   */
  extractParams(skill: Skill, rawInput: string): { command: string; args: string } {
    const triggerPattern = TRIGGER_WORDS[skill.name];
    let args = rawInput;

    if (triggerPattern) {
      // Reset lastIndex for global regexes
      triggerPattern.lastIndex = 0;
      args = args.replace(triggerPattern, '');
    }

    // Clean up: collapse whitespace, trim, strip leading filler words
    args = args.replace(/\s+/g, ' ').trim();

    // Strip leading filler words (up to 3 rounds to handle "the a ...")
    for (let i = 0; i < 3; i++) {
      const before = args;
      args = args.replace(LEADING_FILLER, '');
      if (args === before) break;
    }

    args = args.trim();

    return {
      command: skill.command,
      args,
    };
  }

  /**
   * Build the full dispatch string: "/team research OAuth 2.0 best practices"
   */
  buildDispatch(skill: Skill, rawInput: string): string {
    const { command, args } = this.extractParams(skill, rawInput);
    return args ? `${command} ${args}` : command;
  }
}
