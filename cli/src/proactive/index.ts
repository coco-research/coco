/**
 * Phase 5: Proactive Mode — barrel export
 */
export { ProactiveEngine } from './engine.js';
export type { ProactiveEngineEvents, ProactiveEngineDeps } from './engine.js';
export { TriggerEngine } from './trigger-engine.js';
export { SuggestionRanker } from './suggestion-ranker.js';
export type { RankerContext } from './suggestion-ranker.js';
export { PreferenceStore } from './preference-store.js';
export { FileWatcher } from './file-watcher.js';
export type { FileWatcherConfig } from './file-watcher.js';
export { EmailMonitor } from './email-monitor.js';
export type { EmailMonitorConfig } from './email-monitor.js';
export { CalendarBridge } from './calendar-bridge.js';
export type { CalendarBridgeConfig } from './calendar-bridge.js';
export { ALL_DEFAULT_RULES, FILE_RULES, EMAIL_RULES, CALENDAR_RULES } from './default-rules.js';
export type {
  WatcherEvent,
  WatcherSource,
  TriggerRule,
  RawTrigger,
  Suggestion,
  SuggestionOutcome,
  Sensitivity,
  ProactiveConfig,
} from './types.js';
export { DEFAULT_CONFIG, SENSITIVITY_THRESHOLDS } from './types.js';
