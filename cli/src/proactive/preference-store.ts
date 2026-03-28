/**
 * Phase 5: Preference Store
 *
 * Tracks user responses to proactive suggestions and learns from patterns.
 * Uses SQLite for persistence. Adjusts confidence scores based on accept/dismiss history.
 */

import type Database from 'better-sqlite3';
import type { SuggestionOutcome } from './types.js';

export interface SuggestionLogEntry {
  ruleId: string;
  source: string;
  actionText: string;
  skillRoute: string;
  confidence: number;
  outcome: SuggestionOutcome;
}

export interface SuggestionPrefs {
  ruleId: string;
  acceptCount: number;
  dismissCount: number;
  lastAccepted: number | null;
  lastDismissed: number | null;
  confidenceAdj: number;
}

export interface SuggestionStats {
  ruleId: string;
  acceptCount: number;
  dismissCount: number;
  expiredCount: number;
  totalCount: number;
  acceptRate: number;
  confidenceAdj: number;
}

export class PreferenceStore {
  private db: Database.Database;
  private logStmt!: Database.Statement;
  private getPrefsStmt!: Database.Statement;
  private upsertPrefsStmt!: Database.Statement;
  private getAllPrefsStmt!: Database.Statement;

  constructor(db: Database.Database) {
    this.db = db;
    this.initialize();
  }

  private initialize(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS suggestion_log (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id       TEXT NOT NULL,
        source        TEXT NOT NULL,
        action_text   TEXT NOT NULL,
        skill_route   TEXT NOT NULL,
        confidence    REAL NOT NULL,
        outcome       TEXT NOT NULL,
        created_at    INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );

      CREATE INDEX IF NOT EXISTS idx_suggestion_log_rule ON suggestion_log(rule_id);
      CREATE INDEX IF NOT EXISTS idx_suggestion_log_outcome ON suggestion_log(outcome);

      CREATE TABLE IF NOT EXISTS suggestion_prefs (
        rule_id       TEXT PRIMARY KEY,
        accept_count  INTEGER NOT NULL DEFAULT 0,
        dismiss_count INTEGER NOT NULL DEFAULT 0,
        last_accepted INTEGER,
        last_dismissed INTEGER,
        confidence_adj REAL NOT NULL DEFAULT 0.0
      );
    `);

    this.logStmt = this.db.prepare(`
      INSERT INTO suggestion_log (rule_id, source, action_text, skill_route, confidence, outcome, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    this.getPrefsStmt = this.db.prepare(`
      SELECT * FROM suggestion_prefs WHERE rule_id = ?
    `);

    this.upsertPrefsStmt = this.db.prepare(`
      INSERT INTO suggestion_prefs (rule_id, accept_count, dismiss_count, last_accepted, last_dismissed, confidence_adj)
      VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(rule_id) DO UPDATE SET
        accept_count = excluded.accept_count,
        dismiss_count = excluded.dismiss_count,
        last_accepted = excluded.last_accepted,
        last_dismissed = excluded.last_dismissed,
        confidence_adj = excluded.confidence_adj
    `);

    this.getAllPrefsStmt = this.db.prepare(`
      SELECT * FROM suggestion_prefs ORDER BY rule_id
    `);
  }

  /**
   * Log a suggestion outcome and update preferences.
   * Returns { shouldDisable } if the rule should be auto-disabled.
   */
  recordOutcome(entry: SuggestionLogEntry): { shouldDisable: boolean } {
    const now = Date.now();

    // Log the entry
    this.logStmt.run(
      entry.ruleId,
      entry.source,
      entry.actionText,
      entry.skillRoute,
      entry.confidence,
      entry.outcome,
      now,
    );

    // Get current prefs
    const existing = this.getPrefsStmt.get(entry.ruleId) as any | undefined;

    let acceptCount = existing?.accept_count ?? 0;
    let dismissCount = existing?.dismiss_count ?? 0;
    let lastAccepted = existing?.last_accepted ?? null;
    let lastDismissed = existing?.last_dismissed ?? null;

    // Update counts based on outcome
    if (entry.outcome === 'accepted') {
      acceptCount++;
      lastAccepted = now;
    } else if (entry.outcome === 'dismissed') {
      dismissCount++;
      lastDismissed = now;
    }
    // 'expired' and 'auto-dismissed' don't change counts

    // Compute confidence adjustment
    const confidenceAdj = this.computeConfidenceAdj(acceptCount, dismissCount);

    // Persist
    this.upsertPrefsStmt.run(
      entry.ruleId,
      acceptCount,
      dismissCount,
      lastAccepted,
      lastDismissed,
      confidenceAdj,
    );

    // Check auto-disable threshold
    const shouldDisable = dismissCount >= 10 && acceptCount === 0;

    return { shouldDisable };
  }

  /**
   * Get the confidence adjustment for a rule.
   * Returns 0 if no data exists.
   */
  getConfidenceAdj(ruleId: string): number {
    const row = this.getPrefsStmt.get(ruleId) as any | undefined;
    return row?.confidence_adj ?? 0;
  }

  /**
   * Get full preferences for a rule.
   */
  getPrefs(ruleId: string): SuggestionPrefs | undefined {
    const row = this.getPrefsStmt.get(ruleId) as any | undefined;
    if (!row) return undefined;
    return {
      ruleId: row.rule_id,
      acceptCount: row.accept_count,
      dismissCount: row.dismiss_count,
      lastAccepted: row.last_accepted,
      lastDismissed: row.last_dismissed,
      confidenceAdj: row.confidence_adj,
    };
  }

  /**
   * Get stats for all rules (for /proactive stats).
   */
  getStats(): SuggestionStats[] {
    const allPrefs = this.getAllPrefsStmt.all() as any[];

    // Also get expired/auto-dismissed counts from log
    const expiredCounts = this.db.prepare(`
      SELECT rule_id, COUNT(*) as cnt
      FROM suggestion_log
      WHERE outcome IN ('expired', 'auto-dismissed')
      GROUP BY rule_id
    `).all() as any[];

    const expiredMap = new Map<string, number>();
    for (const row of expiredCounts) {
      expiredMap.set(row.rule_id, row.cnt);
    }

    return allPrefs.map((row: any) => {
      const total = row.accept_count + row.dismiss_count + (expiredMap.get(row.rule_id) ?? 0);
      return {
        ruleId: row.rule_id,
        acceptCount: row.accept_count,
        dismissCount: row.dismiss_count,
        expiredCount: expiredMap.get(row.rule_id) ?? 0,
        totalCount: total,
        acceptRate: total > 0 ? row.accept_count / total : 0,
        confidenceAdj: row.confidence_adj,
      };
    });
  }

  /**
   * Reset all preferences (for /proactive reset-prefs).
   */
  resetAll(): void {
    this.db.exec('DELETE FROM suggestion_prefs');
    this.db.exec('DELETE FROM suggestion_log');
  }

  /**
   * Prune old log entries (older than N days).
   */
  prune(daysToKeep: number = 30): number {
    const cutoff = Date.now() - (daysToKeep * 24 * 60 * 60 * 1000);
    const result = this.db.prepare('DELETE FROM suggestion_log WHERE created_at < ?').run(cutoff);
    return result.changes;
  }

  /**
   * Confidence adjustment formula:
   * adj = (accepts - dismissals * 2) / (accepts + dismissals + 1) * 0.2
   * Capped at [-0.3, +0.2]
   */
  private computeConfidenceAdj(acceptCount: number, dismissCount: number): number {
    const numerator = acceptCount - dismissCount * 2;
    const denominator = acceptCount + dismissCount + 1;
    const raw = (numerator / denominator) * 0.2;
    return Math.max(-0.3, Math.min(0.2, raw));
  }
}
