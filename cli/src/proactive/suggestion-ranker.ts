/**
 * Phase 5: Suggestion Ranker
 *
 * Adjusts raw trigger confidence based on context and user preferences,
 * then filters and ranks. Handles deduplication of similar suggestions.
 */

import { randomUUID } from 'node:crypto';
import type {
  RawTrigger,
  Suggestion,
  Sensitivity,
  ProactiveConfig,
} from './types.js';
import { SENSITIVITY_THRESHOLDS } from './types.js';
import type { PreferenceStore } from './preference-store.js';

export interface RankerContext {
  /** Currently running session skill names */
  activeSkills: string[];
  /** Paths the user recently interacted with (last 5 min) */
  recentPaths: string[];
  /** Current hour (0-23) for time-of-day adjustment */
  currentHour: number;
}

export class SuggestionRanker {
  private preferenceStore: PreferenceStore | null;
  private recentSuggestions: Map<string, number> = new Map(); // skillRoute -> timestamp

  constructor(preferenceStore: PreferenceStore | null = null) {
    this.preferenceStore = preferenceStore;
  }

  /**
   * Score, deduplicate, filter, and rank raw triggers into suggestions.
   */
  rank(
    triggers: RawTrigger[],
    config: ProactiveConfig,
    context: RankerContext,
  ): Suggestion[] {
    const threshold = SENSITIVITY_THRESHOLDS[config.sensitivity];
    const now = Date.now();

    // Step 1: Score each trigger
    const scored = triggers.map(trigger => ({
      trigger,
      confidence: this.score(trigger, context),
    }));

    // Step 2: Filter by threshold
    const filtered = scored.filter(s => s.confidence >= threshold);

    // Step 3: Deduplicate by skillRoute within 10s window
    const deduped = this.deduplicate(filtered, now);

    // Step 4: Sort by confidence descending
    deduped.sort((a, b) => b.confidence - a.confidence);

    // Step 5: Convert to Suggestion objects
    return deduped.map(({ trigger, confidence }) => ({
      id: randomUUID(),
      ruleId: trigger.ruleId,
      source: trigger.source,
      text: trigger.actionText,
      skillRoute: trigger.skillRoute,
      confidence,
      createdAt: now,
      expiresAt: now + config.suggestionTtlMs,
    }));
  }

  /**
   * Score a single trigger by applying adjustments to its base confidence.
   */
  private score(trigger: RawTrigger, context: RankerContext): number {
    let confidence = trigger.baseConfidence;

    // Preference-based adjustments
    if (this.preferenceStore) {
      const adj = this.preferenceStore.getConfidenceAdj(trigger.ruleId);
      confidence += adj;
    }

    // Context-based adjustments

    // If the suggestion relates to a currently running session, it's redundant
    if (context.activeSkills.includes(trigger.skillRoute)) {
      confidence -= 0.15;
    }

    // If the file is in a recently-worked directory, boost
    if (trigger.event.path && context.recentPaths.length > 0) {
      const dir = trigger.event.path.substring(0, trigger.event.path.lastIndexOf('/'));
      if (context.recentPaths.some(p => p.startsWith(dir) || dir.startsWith(p))) {
        confidence += 0.10;
      }
    }

    // Time-of-day: outside 9am-7pm, less likely to be useful
    if (context.currentHour < 9 || context.currentHour >= 19) {
      confidence -= 0.10;
    }

    // Batch changes get a small boost (handled by the event having metadata)
    if (trigger.event.metadata?.batchSize && (trigger.event.metadata.batchSize as number) > 3) {
      confidence += 0.05;
    }

    // Clamp to [0, 1]
    return Math.max(0, Math.min(1, confidence));
  }

  /**
   * Deduplicate triggers: if two suggest the same skillRoute within 10s, keep higher confidence.
   */
  private deduplicate(
    scored: Array<{ trigger: RawTrigger; confidence: number }>,
    now: number,
  ): Array<{ trigger: RawTrigger; confidence: number }> {
    const seen = new Map<string, { trigger: RawTrigger; confidence: number }>();
    const dedupWindowMs = 10_000;

    for (const entry of scored) {
      const key = entry.trigger.skillRoute;
      const lastSeen = this.recentSuggestions.get(key);

      // Check against recently-emitted suggestions
      if (lastSeen && now - lastSeen < dedupWindowMs) {
        const existing = seen.get(key);
        if (!existing || entry.confidence > existing.confidence) {
          seen.set(key, entry);
        }
        continue;
      }

      // Check within current batch
      const existing = seen.get(key);
      if (!existing || entry.confidence > existing.confidence) {
        seen.set(key, entry);
      }
    }

    // Update recent suggestions tracker
    for (const [key] of seen) {
      this.recentSuggestions.set(key, now);
    }

    // Clean old entries from tracker
    for (const [key, ts] of this.recentSuggestions) {
      if (now - ts > dedupWindowMs * 3) {
        this.recentSuggestions.delete(key);
      }
    }

    return Array.from(seen.values());
  }

  /**
   * Reset the dedup tracker (for testing).
   */
  reset(): void {
    this.recentSuggestions.clear();
  }
}
