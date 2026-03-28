import type { SkillRegistry, Skill } from './skill-registry.js';
import type { StateManager } from './state.js';
import { GsdRouter } from '../integrations/gsd-router.js';

// --- Types ---

export interface ClassifiedIntent {
  skill: Skill | null;
  args: string;
  confidence: number;
  tier: number;              // 1 = keyword/regex, 2 = Claude
  isMetaCommand: boolean;
  metaCommand?: string;
  metaArgs?: string;
}

export interface IntentClassifierDeps {
  skills: SkillRegistry;
  state: StateManager;
  claudeClassify?: (prompt: string) => Promise<string>;  // injectable for testing
}

// --- Meta-command patterns ---

export const META_COMMANDS: Record<string, RegExp> = {
  status:           /^\/(status)\s*$/i,
  halt:             /^\/(halt)\s*(.*)$/i,
  history:          /^\/(history)\s*(.*)$/i,
  help:             /^\/(help)\s*$/i,
  quit:             /^\/(quit|exit|bye)\s*$/i,
  skills:           /^\/(skills)\s*$/i,
  queue:            /^\/(queue)\s*$/i,
  'queue-clear':    /^\/(queue)\s+clear\s*$/i,
  'queue-promote':  /^\/(queue)\s+promote\s+(.+)$/i,
  focus:            /^\/(focus)\s+(.+)$/i,
  unfocus:          /^\/(unfocus)\s*$/i,
  detach:           /^\/(detach)\s+(.+)$/i,
  concurrency:      /^\/(concurrency)\s+(\d+)\s*$/i,
  correct:          /^\/(correct)\s+(.+)$/i,
};

// --- Team skill trigger words (moved from orchestrator.ts) ---

export const TEAM_SKILL_TRIGGERS: Array<{ pattern: RegExp; skill: string }> = [
  // Order matters: more specific/unambiguous verbs first to avoid false matches.
  // e.g., "repair" (fix) must be checked before "build" (develop), since
  // "repair the broken build" should route to fix, not develop.
  { pattern: /\b(research|investigate|explore|look\s+into|find\s+out)\b/i, skill: 'team-research' },
  { pattern: /\b(fix|debug|troubleshoot|repair|patch)\b/i, skill: 'team-fix' },
  { pattern: /\b(feedback|retro|retrospective|critique)\b/i, skill: 'team-feedback' },
  { pattern: /\b(scrape|crawl|extract\s+from|fetch\s+page)\b/i, skill: 'team-scrape' },
  { pattern: /\b(develop|implement|build|create\s+(a|an|the)\s+\w*(service|module|app|api|feature))\b/i, skill: 'team-develop' },
  { pattern: /\b(review|audit|inspect|evaluate|assess|code\s+review)\b/i, skill: 'team-review' },
  { pattern: /\b(plan|roadmap|sprint|milestone|prioriti[sz]e|schedule)\b/i, skill: 'team-plan' },
  { pattern: /\b(test|coverage|unit\s+test|integration\s+test|spec|write\s+tests)\b/i, skill: 'team-test' },
  { pattern: /\b(think|brainstorm|ideate|consider|reason\s+about|analyse|analyze)\b/i, skill: 'team-think' },
  { pattern: /\b(document|documentation|docs|write\s+docs|api\s+docs)\b/i, skill: 'team-document' },
  { pattern: /\b(present|presentation|slides|demo|showcase)\b/i, skill: 'team-present' },
  { pattern: /\b(communicate|announce|notify|message|update\s+the\s+team)\b/i, skill: 'team-communicate' },
  { pattern: /\b(verify|validate|confirm|check\s+quality)\b/i, skill: 'team-verify' },
];

// --- GSD skill trigger patterns ---

export const GSD_SKILL_TRIGGERS: Array<{ pattern: RegExp; skill: string }> = [
  { pattern: /\b(new\s+project|start\s+a?\s*project|create\s+a?\s*project)\b/i, skill: 'new-project' },
  { pattern: /\b(execute\s+(the\s+)?(current\s+)?phase|run\s+(the\s+)?phase)\b/i, skill: 'execute-phase' },
  { pattern: /\b(plan\s+(the\s+)?(next\s+)?phase|phase\s+plan)\b/i, skill: 'plan-phase' },
  { pattern: /\b(verify|check)\s+(the\s+)?(last\s+|previous\s+)?phase\b/i, skill: 'verify-work' },
  { pattern: /\b(project\s+health|health\s+check|project\s+status)\b/i, skill: 'health' },
];

// --- Classifier ---

export class IntentClassifier {
  private skills: SkillRegistry;
  private state: StateManager;
  private claudeClassify: ((prompt: string) => Promise<string>) | null;

  constructor(deps: IntentClassifierDeps) {
    this.skills = deps.skills;
    this.state = deps.state;
    this.claudeClassify = deps.claudeClassify ?? null;
  }

  /**
   * Main entry point: classify user input into a skill + args.
   * Tier 1 is synchronous (instant). Tier 2 falls back to Claude if needed.
   */
  async classify(text: string): Promise<ClassifiedIntent> {
    // Step 1: Check meta-commands (unchanged)
    const meta = this.checkMetaCommand(text);
    if (meta) return meta;

    // Step 2: Tier 1 — instant classification
    const tier1 = this.classifyTier1(text);
    if (tier1) {
      return tier1;
    }

    // Step 3: Tier 2 — Claude-based classification (ambiguous inputs only)
    return await this.classifyTier2(text);
  }

  /**
   * Check for meta-commands (/status, /help, /quit, etc.)
   */
  checkMetaCommand(text: string): ClassifiedIntent | null {
    for (const [name, pattern] of Object.entries(META_COMMANDS)) {
      const match = text.match(pattern);
      if (match) {
        return {
          skill: null,
          args: '',
          confidence: 1.0,
          tier: 1,
          isMetaCommand: true,
          metaCommand: name,
          metaArgs: match[2]?.trim(),
        };
      }
    }
    return null;
  }

  /**
   * Tier 1: Instant classification via corrections store, slash commands,
   * regex triggers, and keyword scoring.
   * Returns null if no confident match found (triggers Tier 2).
   */
  classifyTier1(text: string): ClassifiedIntent | null {
    const normalized = this.normalizeInput(text);

    // 1. Check learning store corrections (highest priority)
    const correction = this.state.getCorrection(normalized);
    if (correction) {
      const skill = this.skills.get(correction.correct_skill);
      if (skill) {
        this.state.incrementCorrectionUsage(correction.id);
        return {
          skill,
          args: text,
          confidence: 1.0,
          tier: 1,
          isMetaCommand: false,
        };
      }
    }

    // 2. Direct slash commands: "/team research OAuth"
    if (text.startsWith('/')) {
      // Check GSD commands first: /gsd:action
      const gsdMatch = text.match(/^\/gsd:(\S+)\s*(.*)/i);
      if (gsdMatch) {
        const skill = this.skills.get(gsdMatch[1]);
        if (skill) {
          return {
            skill,
            args: gsdMatch[2]?.trim() || '',
            confidence: 0.95,
            tier: 1,
            isMetaCommand: false,
          };
        }
      }

      const skill = this.skills.findByKeyword(text);
      if (skill) {
        const args = text.replace(skill.command, '').trim();
        return { skill, args, confidence: 0.95, tier: 1, isMetaCommand: false };
      }
    }

    // 3. GSD triggers (only win over team when input has GSD context like "project"/"phase")
    if (GsdRouter.isGsdContext(text)) {
      for (const { pattern, skill: skillName } of GSD_SKILL_TRIGGERS) {
        if (pattern.test(text)) {
          const skill = this.skills.get(skillName);
          if (skill) {
            return { skill, args: text, confidence: 0.85, tier: 1, isMetaCommand: false };
          }
        }
      }
    }

    // 4. Team skill trigger words — find ALL matches, pick earliest position
    {
      let bestMatch: { skill: Skill; position: number } | null = null;
      for (const { pattern, skill: skillName } of TEAM_SKILL_TRIGGERS) {
        const match = text.match(pattern);
        if (match && match.index !== undefined) {
          const teamSkill = this.skills.get(skillName);
          if (teamSkill && (bestMatch === null || match.index < bestMatch.position)) {
            bestMatch = { skill: teamSkill, position: match.index };
          }
        }
      }
      if (bestMatch) {
        return { skill: bestMatch.skill, args: text, confidence: 0.85, tier: 1, isMetaCommand: false };
      }
    }

    // 5. Generic keyword-based matching from registry
    // Require a higher score threshold to avoid false positives on common words
    const skill = this.skills.findByKeyword(text);
    if (skill) {
      // Only accept if the keyword match is strong enough (score > 5)
      // This prevents "thanks for the help" matching "help" keyword
      const lower = text.toLowerCase();
      let score = 0;
      for (const kw of skill.keywords) {
        if (lower.includes(kw.toLowerCase())) {
          score += kw.length;
        }
      }
      if (score > 5) {
        return { skill, args: text, confidence: 0.7, tier: 1, isMetaCommand: false };
      }
    }

    // No Tier 1 match
    return null;
  }

  /**
   * Tier 2: Claude-based classification for ambiguous inputs.
   * Uses a single-turn Claude call with no tools.
   */
  async classifyTier2(text: string): Promise<ClassifiedIntent> {
    if (!this.claudeClassify) {
      // No Claude available — return no match
      return { skill: null, args: text, confidence: 0, tier: 2, isMetaCommand: false };
    }

    const prompt = this.buildTier2Prompt(text);

    try {
      const response = await this.claudeClassify(prompt);
      return this.parseTier2Response(response, text);
    } catch {
      // On any error, fall through to no-match
      return { skill: null, args: text, confidence: 0, tier: 2, isMetaCommand: false };
    }
  }

  /**
   * Build the Tier 2 classification prompt.
   */
  buildTier2Prompt(text: string): string {
    const skillContext = this.skills.toPromptContext();

    return [
      'System: You are a command router for CoCo, a terminal assistant.',
      'Given user input and available skills, return ONLY a JSON object:',
      '{ "skill": "skill-name", "args": "remaining text after skill extraction", "confidence": 0.0-1.0 }',
      '',
      'If no skill matches, return: { "skill": null, "args": "", "confidence": 0.0 }',
      '',
      'Rules:',
      '- "skill" must be one of the skill names listed below, or null.',
      '- "args" is the part of the user\'s input that should be passed TO the skill as context.',
      '- "confidence" reflects how certain you are this is the right skill.',
      '',
      skillContext,
      '',
      `User input: "${text}"`,
    ].join('\n');
  }

  /**
   * Parse the Tier 2 Claude response into a ClassifiedIntent.
   */
  parseTier2Response(response: string, originalText: string): ClassifiedIntent {
    try {
      // Extract JSON from the response (may be wrapped in markdown code blocks)
      const jsonMatch = response.match(/\{[\s\S]*?\}/);
      if (!jsonMatch) {
        return { skill: null, args: originalText, confidence: 0, tier: 2, isMetaCommand: false };
      }

      const parsed = JSON.parse(jsonMatch[0]);
      const skillName = parsed.skill;
      const args = parsed.args || originalText;
      const confidence = typeof parsed.confidence === 'number' ? parsed.confidence : 0;

      if (!skillName) {
        return { skill: null, args: originalText, confidence: 0, tier: 2, isMetaCommand: false };
      }

      // Validate skill name against registry
      const skill = this.skills.get(skillName);
      if (!skill) {
        return { skill: null, args: originalText, confidence: 0, tier: 2, isMetaCommand: false };
      }

      return { skill, args, confidence, tier: 2, isMetaCommand: false };
    } catch {
      return { skill: null, args: originalText, confidence: 0, tier: 2, isMetaCommand: false };
    }
  }

  /**
   * Normalize input for learning store lookups:
   * lowercase, trim, remove punctuation, collapse whitespace.
   */
  normalizeInput(text: string): string {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }
}
