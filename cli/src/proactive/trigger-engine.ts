/**
 * Phase 5: Trigger Engine
 *
 * Rule-based engine that maps raw watcher events to candidate suggestions.
 * Handles rule registration, condition matching, and cooldown tracking.
 */

import type {
  TriggerRule,
  RawTrigger,
  WatcherEvent,
  WatcherSource,
} from './types.js';

export class TriggerEngine {
  private rules: Map<string, TriggerRule> = new Map();
  private cooldowns: Map<string, number> = new Map();   // ruleId -> last fired timestamp
  private disabledRules: Set<string> = new Set();

  /**
   * Register a trigger rule.
   */
  register(rule: TriggerRule): void {
    this.rules.set(rule.id, rule);
  }

  /**
   * Register multiple rules at once.
   */
  registerAll(rules: TriggerRule[]): void {
    for (const rule of rules) {
      this.register(rule);
    }
  }

  /**
   * Disable a specific rule (e.g., after too many dismissals).
   */
  disableRule(ruleId: string): void {
    this.disabledRules.add(ruleId);
  }

  /**
   * Re-enable a disabled rule.
   */
  enableRule(ruleId: string): void {
    this.disabledRules.delete(ruleId);
  }

  /**
   * Check if a rule is disabled.
   */
  isDisabled(ruleId: string): boolean {
    return this.disabledRules.has(ruleId);
  }

  /**
   * Get all registered rule IDs.
   */
  getRuleIds(): string[] {
    return Array.from(this.rules.keys());
  }

  /**
   * Match a batch of watcher events against all rules.
   * Returns raw triggers for events that match active, non-cooldown rules.
   */
  match(events: WatcherEvent[]): RawTrigger[] {
    const now = Date.now();
    const triggers: RawTrigger[] = [];

    for (const event of events) {
      for (const rule of this.rules.values()) {
        // Skip disabled rules
        if (this.disabledRules.has(rule.id)) continue;

        // Skip rules for different sources
        if (rule.source !== event.source) continue;

        // Check cooldown
        const lastFired = this.cooldowns.get(rule.id) ?? 0;
        if (now - lastFired < rule.cooldownMs) continue;

        // Evaluate condition
        let matches = false;
        try {
          matches = rule.condition(event);
        } catch {
          // Condition threw — skip this rule for this event
          continue;
        }

        if (matches) {
          // Build action text from template
          const actionText = this.interpolate(rule.actionTemplate, event);

          triggers.push({
            ruleId: rule.id,
            source: rule.source,
            actionText,
            skillRoute: rule.skillRoute,
            baseConfidence: rule.baseConfidence,
            event,
            firedAt: now,
          });

          // Set cooldown
          this.cooldowns.set(rule.id, now);
        }
      }
    }

    return triggers;
  }

  /**
   * Simple template interpolation: replaces {path}, {detail}, {type} etc.
   */
  private interpolate(template: string, event: WatcherEvent): string {
    return template
      .replace(/\{path\}/g, event.path ?? '')
      .replace(/\{detail\}/g, event.detail ?? '')
      .replace(/\{type\}/g, event.type)
      .replace(/\{filename\}/g, event.path ? event.path.split('/').pop() ?? '' : '');
  }

  /**
   * Reset all cooldowns (for testing or after config change).
   */
  resetCooldowns(): void {
    this.cooldowns.clear();
  }

  /**
   * Reset all state.
   */
  reset(): void {
    this.cooldowns.clear();
    this.disabledRules.clear();
  }

  /**
   * Get the count of registered rules.
   */
  get size(): number {
    return this.rules.size;
  }

  /**
   * Get rules by source type.
   */
  getRulesBySource(source: WatcherSource): TriggerRule[] {
    return Array.from(this.rules.values()).filter(r => r.source === source);
  }
}
