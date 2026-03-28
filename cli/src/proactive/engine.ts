/**
 * Phase 5: Proactive Engine
 *
 * Central coordinator that:
 * 1. Starts/stops all watchers based on user config
 * 2. Receives raw events from watchers on a tick loop (5s batching)
 * 3. Feeds events through trigger engine -> suggestion ranker
 * 4. Emits top suggestions to the UI via EventEmitter
 * 5. Manages suggestion queue, throttling (max N/minute), and lifecycle
 *
 * All suggestions require explicit user confirmation — NEVER auto-execute.
 */

import { EventEmitter } from 'eventemitter3';
import type Database from 'better-sqlite3';
import type {
  ProactiveConfig,
  Sensitivity,
  WatcherEvent,
  Suggestion,
  SuggestionOutcome,
} from './types.js';
import { DEFAULT_CONFIG, SENSITIVITY_THRESHOLDS } from './types.js';
import { TriggerEngine } from './trigger-engine.js';
import { SuggestionRanker, type RankerContext } from './suggestion-ranker.js';
import { PreferenceStore } from './preference-store.js';
import { FileWatcher } from './file-watcher.js';
import { EmailMonitor } from './email-monitor.js';
import { CalendarBridge } from './calendar-bridge.js';
import { ALL_DEFAULT_RULES, FILE_RULES, EMAIL_RULES, CALENDAR_RULES } from './default-rules.js';

export interface ProactiveEngineEvents {
  suggestion: (suggestion: Suggestion) => void;
  suggestionExpired: (suggestion: Suggestion) => void;
  ruleDisabled: (ruleId: string) => void;
  started: () => void;
  stopped: () => void;
  warning: (msg: string) => void;
}

export interface ProactiveEngineDeps {
  db: Database.Database;
  config?: Partial<ProactiveConfig>;
  /** Callback to get current active skill names (for ranker context) */
  getActiveSkills?: () => string[];
  /** Callback to get recently-worked paths */
  getRecentPaths?: () => string[];
}

/** Default keywords for email monitoring. */
const DEFAULT_EMAIL_KEYWORDS = ['risk', 'API', 'spec', 'review', 'urgent', 'deadline'];

export class ProactiveEngine extends EventEmitter<ProactiveEngineEvents> {
  private config: ProactiveConfig;
  private triggerEngine: TriggerEngine;
  private ranker: SuggestionRanker;
  private preferenceStore: PreferenceStore;

  private fileWatcher: FileWatcher | null = null;
  private emailMonitor: EmailMonitor | null = null;
  private calendarBridge: CalendarBridge | null = null;

  private eventBuffer: WatcherEvent[] = [];
  private suggestionQueue: Suggestion[] = [];
  private activeSuggestion: Suggestion | null = null;

  private tickTimer: NodeJS.Timeout | null = null;
  private expiryTimer: NodeJS.Timeout | null = null;
  private running: boolean = false;

  // Throttle: track suggestions emitted per minute
  private emitTimestamps: number[] = [];

  // Context callbacks
  private getActiveSkills: () => string[];
  private getRecentPaths: () => string[];

  private static readonly TICK_INTERVAL_MS = 5_000;
  private static readonly MAX_EVENT_BUFFER = 500;

  constructor(deps: ProactiveEngineDeps) {
    super();

    this.config = { ...DEFAULT_CONFIG, ...deps.config };
    this.preferenceStore = new PreferenceStore(deps.db);
    this.triggerEngine = new TriggerEngine();
    this.ranker = new SuggestionRanker(this.preferenceStore);

    this.getActiveSkills = deps.getActiveSkills ?? (() => []);
    this.getRecentPaths = deps.getRecentPaths ?? (() => []);

    // Register default rules
    this.triggerEngine.registerAll(ALL_DEFAULT_RULES);
  }

  // --- Public API ---

  /**
   * Start the proactive engine and all configured watchers.
   */
  start(): void {
    if (this.running) return;
    this.running = true;

    // Start file watcher
    if (this.config.watchPaths.length > 0) {
      this.fileWatcher = new FileWatcher({ watchPaths: this.config.watchPaths });
      this.fileWatcher.on('event', (e) => this.bufferEvent(e));
      this.fileWatcher.on('error', (err) => this.emit('warning', `File watcher error: ${err.message}`));
      this.fileWatcher.start();
    }

    // Start email monitor
    if (this.config.emailEnabled) {
      this.emailMonitor = new EmailMonitor({
        keywords: DEFAULT_EMAIL_KEYWORDS,
      });
      this.emailMonitor.on('event', (e) => this.bufferEvent(e));
      this.emailMonitor.on('warning', (msg) => this.emit('warning', msg));
      this.emailMonitor.start();
    }

    // Start calendar bridge
    if (this.config.calendarEnabled) {
      this.calendarBridge = new CalendarBridge();
      this.calendarBridge.on('event', (e) => this.bufferEvent(e));
      this.calendarBridge.on('warning', (msg) => this.emit('warning', msg));
      this.calendarBridge.start();
    }

    // Start tick loop
    this.tickTimer = setInterval(() => this.tick(), ProactiveEngine.TICK_INTERVAL_MS);

    this.emit('started');
  }

  /**
   * Stop all watchers and clear state.
   */
  stop(): void {
    this.running = false;

    if (this.tickTimer) {
      clearInterval(this.tickTimer);
      this.tickTimer = null;
    }

    if (this.expiryTimer) {
      clearTimeout(this.expiryTimer);
      this.expiryTimer = null;
    }

    this.fileWatcher?.stop();
    this.fileWatcher = null;

    this.emailMonitor?.stop();
    this.emailMonitor = null;

    this.calendarBridge?.stop();
    this.calendarBridge = null;

    // Expire any active suggestion
    if (this.activeSuggestion) {
      this.recordOutcome(this.activeSuggestion, 'auto-dismissed');
      this.activeSuggestion = null;
    }

    // Clear queues
    this.eventBuffer = [];
    this.suggestionQueue = [];
    this.emitTimestamps = [];

    this.emit('stopped');
  }

  /**
   * Whether the engine is currently running.
   */
  get isRunning(): boolean {
    return this.running;
  }

  /**
   * Get current config.
   */
  getConfig(): Readonly<ProactiveConfig> {
    return { ...this.config };
  }

  /**
   * Update config and restart affected watchers.
   */
  updateConfig(partial: Partial<ProactiveConfig>): void {
    const wasRunning = this.running;
    if (wasRunning) this.stop();

    Object.assign(this.config, partial);

    if (wasRunning && this.config.enabled) {
      this.start();
    }
  }

  /**
   * Set sensitivity level.
   */
  setSensitivity(level: Sensitivity): void {
    this.config.sensitivity = level;
  }

  /**
   * User accepted the current suggestion.
   * Returns the suggestion's skill route and text for the orchestrator to dispatch.
   */
  acceptSuggestion(): { skillRoute: string; text: string } | null {
    if (!this.activeSuggestion) return null;

    const suggestion = this.activeSuggestion;
    this.activeSuggestion = null;

    this.recordOutcome(suggestion, 'accepted');
    this.advanceQueue();

    return { skillRoute: suggestion.skillRoute, text: suggestion.text };
  }

  /**
   * User dismissed the current suggestion.
   */
  dismissSuggestion(): void {
    if (!this.activeSuggestion) return;

    this.recordOutcome(this.activeSuggestion, 'dismissed');
    this.activeSuggestion = null;
    this.advanceQueue();
  }

  /**
   * Auto-dismiss due to user typing or timeout.
   */
  autoDismissSuggestion(): void {
    if (!this.activeSuggestion) return;

    this.recordOutcome(this.activeSuggestion, 'auto-dismissed');
    this.activeSuggestion = null;
    this.advanceQueue();
  }

  /**
   * Get the currently active suggestion (for UI rendering).
   */
  getActiveSuggestion(): Suggestion | null {
    return this.activeSuggestion;
  }

  /**
   * Get preference stats (for /proactive stats).
   */
  getStats(): ReturnType<PreferenceStore['getStats']> {
    return this.preferenceStore.getStats();
  }

  /**
   * Reset all learned preferences.
   */
  resetPreferences(): void {
    this.preferenceStore.resetAll();
    this.triggerEngine.reset();
  }

  /**
   * Enable/disable email monitoring.
   */
  setEmailEnabled(enabled: boolean): void {
    if (this.config.emailEnabled === enabled) return;
    this.config.emailEnabled = enabled;

    if (this.running) {
      if (enabled && !this.emailMonitor) {
        this.emailMonitor = new EmailMonitor({
          keywords: DEFAULT_EMAIL_KEYWORDS,
        });
        this.emailMonitor.on('event', (e) => this.bufferEvent(e));
        this.emailMonitor.on('warning', (msg) => this.emit('warning', msg));
        this.emailMonitor.start();
      } else if (!enabled && this.emailMonitor) {
        this.emailMonitor.stop();
        this.emailMonitor = null;
      }
    }
  }

  /**
   * Enable/disable calendar monitoring.
   */
  setCalendarEnabled(enabled: boolean): void {
    if (this.config.calendarEnabled === enabled) return;
    this.config.calendarEnabled = enabled;

    if (this.running) {
      if (enabled && !this.calendarBridge) {
        this.calendarBridge = new CalendarBridge();
        this.calendarBridge.on('event', (e) => this.bufferEvent(e));
        this.calendarBridge.on('warning', (msg) => this.emit('warning', msg));
        this.calendarBridge.start();
      } else if (!enabled && this.calendarBridge) {
        this.calendarBridge.stop();
        this.calendarBridge = null;
      }
    }
  }

  // --- Internal ---

  /**
   * Buffer a watcher event for the next tick.
   */
  private bufferEvent(event: WatcherEvent): void {
    if (!this.running) return;
    if (this.eventBuffer.length >= ProactiveEngine.MAX_EVENT_BUFFER) {
      // Drop oldest event to stay within cap
      this.eventBuffer.shift();
    }
    this.eventBuffer.push(event);
  }

  /**
   * Tick loop: process buffered events, generate suggestions.
   */
  private tick(): void {
    if (!this.running || this.eventBuffer.length === 0) return;

    // Drain the buffer
    const events = [...this.eventBuffer];
    this.eventBuffer = [];

    // Run through trigger engine
    const triggers = this.triggerEngine.match(events);
    if (triggers.length === 0) return;

    // Build ranker context
    const context: RankerContext = {
      activeSkills: this.getActiveSkills(),
      recentPaths: this.getRecentPaths(),
      currentHour: new Date().getHours(),
    };

    // Rank and filter
    const suggestions = this.ranker.rank(triggers, this.config, context);
    if (suggestions.length === 0) return;

    // Add to queue
    this.suggestionQueue.push(...suggestions);

    // If no active suggestion, show the next one
    if (!this.activeSuggestion) {
      this.advanceQueue();
    }
  }

  /**
   * Show the next suggestion from the queue, respecting throttle.
   */
  private advanceQueue(): void {
    // Clear expiry timer
    if (this.expiryTimer) {
      clearTimeout(this.expiryTimer);
      this.expiryTimer = null;
    }

    if (this.suggestionQueue.length === 0) return;

    // Check throttle
    const now = Date.now();
    this.emitTimestamps = this.emitTimestamps.filter(t => now - t < 60_000);
    if (this.emitTimestamps.length >= this.config.maxSuggestionsPerMinute) {
      // Throttled — try again on next tick
      return;
    }

    // Remove expired suggestions from queue
    this.suggestionQueue = this.suggestionQueue.filter(s => s.expiresAt > now);
    if (this.suggestionQueue.length === 0) return;

    // Take the highest-confidence suggestion
    this.suggestionQueue.sort((a, b) => b.confidence - a.confidence);
    const next = this.suggestionQueue.shift()!;

    this.activeSuggestion = next;
    this.emitTimestamps.push(now);

    this.emit('suggestion', next);

    // Set expiry timer
    const ttl = next.expiresAt - now;
    if (ttl > 0) {
      this.expiryTimer = setTimeout(() => {
        if (this.activeSuggestion?.id === next.id) {
          this.recordOutcome(next, 'expired');
          this.activeSuggestion = null;
          this.emit('suggestionExpired', next);
          this.advanceQueue();
        }
      }, ttl);
    }
  }

  /**
   * Record a suggestion outcome and handle auto-disable.
   */
  private recordOutcome(suggestion: Suggestion, outcome: SuggestionOutcome): void {
    const result = this.preferenceStore.recordOutcome({
      ruleId: suggestion.ruleId,
      source: suggestion.source,
      actionText: suggestion.text,
      skillRoute: suggestion.skillRoute,
      confidence: suggestion.confidence,
      outcome,
    });

    if (result.shouldDisable) {
      this.triggerEngine.disableRule(suggestion.ruleId);
      this.emit('ruleDisabled', suggestion.ruleId);
      this.emit('warning',
        `Rule "${suggestion.ruleId}" auto-disabled after 10+ dismissals. Use /proactive reset-prefs to re-enable.`,
      );
    }
  }
}
