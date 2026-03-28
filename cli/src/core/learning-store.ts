import type { StateManager } from './state.js';

/**
 * LearningStore manages the correction-based learning loop and skill
 * sequence tracking. It wraps StateManager Phase 4 methods with
 * higher-level business logic.
 */
export class LearningStore {
  private state: StateManager;

  constructor(state: StateManager) {
    this.state = state;
  }

  /**
   * Record a routing decision (called on every classification).
   * Returns the intent_log ID for later correction reference.
   */
  logDecision(input: string, normalized: string, tier: number, skill: string | null, confidence: number): number {
    return this.state.logIntent(input, normalized, tier, skill, confidence);
  }

  /**
   * Record a user correction: "no, I meant X".
   * 1. Gets the original intent_log row
   * 2. Inserts into routing_corrections
   * 3. Marks intent_log row as corrected
   */
  recordCorrection(intentLogId: number, correctSkill: string): void {
    const intentRow = this.state.getIntentLogById(intentLogId);
    if (!intentRow) return;

    const normalizedInput = intentRow.input_normalized;
    const wrongSkill = intentRow.skill_matched ?? 'unknown';

    this.state.addCorrection(normalizedInput, wrongSkill, correctSkill);
    this.state.markIntentCorrected(intentLogId);
  }

  /**
   * Check if a correction exists for this normalized input.
   * Returns the correct_skill if found, null otherwise.
   */
  getCorrection(normalizedInput: string): string | null {
    const correction = this.state.getCorrection(normalizedInput);
    if (correction) {
      return correction.correct_skill;
    }
    return null;
  }

  /**
   * Record a skill sequence (called after each dispatch completes).
   * Upserts into skill_sequences, incrementing the count.
   */
  recordSequence(previousSkill: string, currentSkill: string): void {
    if (!previousSkill || !currentSkill || previousSkill === currentSkill) return;
    this.state.recordSequence(previousSkill, currentSkill);
  }

  /**
   * Get a recommendation for the next skill to run based on historical sequences.
   * Returns skill_b if count >= threshold, null otherwise.
   */
  getRecommendation(currentSkill: string, threshold: number = 3): string | null {
    const top = this.state.getTopSequence(currentSkill);
    if (top && top.count >= threshold) {
      return top.skill_b;
    }
    return null;
  }
}
