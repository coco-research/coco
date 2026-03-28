/**
 * Phase 5: Proactive Mode — Shared types
 */

// --- Watcher Events ---

export type WatcherSource = 'file' | 'email' | 'calendar';

export interface WatcherEvent {
  source: WatcherSource;
  type: string;           // e.g., 'add', 'change', 'unlink', 'new-attachment', 'meeting-soon'
  path?: string;          // file path or resource identifier
  detail?: string;        // human-readable detail
  metadata?: Record<string, unknown>;
  timestamp: number;
}

// --- Trigger Rules ---

export interface TriggerRule {
  id: string;                         // e.g., "file:test-added"
  source: WatcherSource;
  condition: (event: WatcherEvent) => boolean;
  actionTemplate: string;             // template with {placeholders}
  skillRoute: string;                 // e.g., "team-test", "direct"
  baseConfidence: number;             // 0.0-1.0
  cooldownMs: number;                 // don't re-trigger within this window
}

export interface RawTrigger {
  ruleId: string;
  source: WatcherSource;
  actionText: string;
  skillRoute: string;
  baseConfidence: number;
  event: WatcherEvent;
  firedAt: number;
}

// --- Suggestions ---

export interface Suggestion {
  id: string;
  ruleId: string;
  source: WatcherSource;
  text: string;
  skillRoute: string;
  confidence: number;
  createdAt: number;
  expiresAt: number;       // auto-dismiss timestamp
}

export type SuggestionOutcome = 'accepted' | 'dismissed' | 'expired' | 'auto-dismissed';

// --- Engine Config ---

export type Sensitivity = 'low' | 'medium' | 'high';

export interface ProactiveConfig {
  enabled: boolean;
  sensitivity: Sensitivity;
  watchPaths: string[];
  emailEnabled: boolean;
  calendarEnabled: boolean;
  maxSuggestionsPerMinute: number;
  suggestionTtlMs: number;            // auto-dismiss after this many ms (default: 30000)
}

export const SENSITIVITY_THRESHOLDS: Record<Sensitivity, number> = {
  low: 0.85,
  medium: 0.70,
  high: 0.50,
};

export const DEFAULT_CONFIG: ProactiveConfig = {
  enabled: false,
  sensitivity: 'medium',
  watchPaths: [],
  emailEnabled: false,
  calendarEnabled: false,
  maxSuggestionsPerMinute: 3,
  suggestionTtlMs: 30_000,
};
