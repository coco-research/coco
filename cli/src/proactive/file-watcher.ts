/**
 * Phase 5: File Watcher
 *
 * Watches project directories for file changes and emits WatcherEvents.
 * Uses fs.watch with debouncing and ignore patterns.
 * Designed to work without chokidar (using native Node fs.watch + manual recursive).
 */

import { EventEmitter } from 'eventemitter3';
import { watch, statSync, readdirSync } from 'node:fs';
import { join, basename, extname, relative } from 'node:path';
import type { FSWatcher } from 'node:fs';
import type { WatcherEvent } from './types.js';

// --- Ignore patterns ---

const IGNORED_DIRS = new Set([
  'node_modules', '.git', 'dist', 'build', '.next', '__pycache__',
  '.cache', '.turbo', '.parcel-cache', 'coverage',
]);

const IGNORED_FILES = new Set([
  '.DS_Store', 'Thumbs.db', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
]);

const IGNORED_EXTENSIONS = new Set([
  '.log', '.lock',
]);

const IGNORED_PREFIXES = ['~$', '.tmp'];

export interface FileWatcherEvents {
  event: (event: WatcherEvent) => void;
  error: (err: Error) => void;
}

export interface FileWatcherConfig {
  watchPaths: string[];
  debounceMs?: number;
  batchWindowMs?: number;
  maxDepth?: number;
}

export class FileWatcher extends EventEmitter<FileWatcherEvents> {
  private watchers: FSWatcher[] = [];
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private batchBuffer: WatcherEvent[] = [];
  private batchTimer: NodeJS.Timeout | null = null;
  private running: boolean = false;

  private debounceMs: number;
  private batchWindowMs: number;
  private maxDepth: number;

  constructor(private config: FileWatcherConfig) {
    super();
    this.debounceMs = config.debounceMs ?? 500;
    this.batchWindowMs = config.batchWindowMs ?? 2000;
    this.maxDepth = config.maxDepth ?? 5;
  }

  /**
   * Start watching all configured paths.
   */
  start(): void {
    if (this.running) return;
    this.running = true;

    for (const watchPath of this.config.watchPaths) {
      try {
        this.watchRecursive(watchPath, 0);
      } catch (err) {
        this.emit('error', err instanceof Error ? err : new Error(String(err)));
      }
    }
  }

  /**
   * Stop all watchers and clear timers.
   */
  stop(): void {
    this.running = false;
    for (const w of this.watchers) {
      try { w.close(); } catch {}
    }
    this.watchers = [];

    for (const timer of this.debounceTimers.values()) {
      clearTimeout(timer);
    }
    this.debounceTimers.clear();

    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }
    this.batchBuffer = [];
  }

  /**
   * Check if the watcher is currently active.
   */
  get isRunning(): boolean {
    return this.running;
  }

  /**
   * Recursively set up watchers, respecting depth limit and ignore patterns.
   */
  private watchRecursive(dirPath: string, depth: number): void {
    if (depth > this.maxDepth) return;
    if (!this.running) return;

    const dirName = basename(dirPath);
    if (IGNORED_DIRS.has(dirName)) return;

    try {
      const watcher = watch(dirPath, { persistent: false }, (eventType, filename) => {
        if (!filename || !this.running) return;
        const fullPath = join(dirPath, filename);
        this.handleFileEvent(eventType, fullPath);
      });

      watcher.on('error', (err) => {
        // Silently ignore watch errors (directory deleted, permissions, etc.)
      });

      this.watchers.push(watcher);

      // Watch subdirectories
      try {
        const entries = readdirSync(dirPath, { withFileTypes: true });
        for (const entry of entries) {
          if (entry.isDirectory() && !IGNORED_DIRS.has(entry.name)) {
            this.watchRecursive(join(dirPath, entry.name), depth + 1);
          }
        }
      } catch {
        // Can't read directory — skip
      }
    } catch {
      // Can't watch directory — skip
    }
  }

  /**
   * Handle a raw fs.watch event with debouncing.
   */
  private handleFileEvent(eventType: string, fullPath: string): void {
    const filename = basename(fullPath);

    // Apply ignore filters
    if (this.shouldIgnore(filename)) return;

    // Debounce per file
    const existing = this.debounceTimers.get(fullPath);
    if (existing) {
      clearTimeout(existing);
    }

    this.debounceTimers.set(fullPath, setTimeout(() => {
      this.debounceTimers.delete(fullPath);

      // Determine event type (add vs change)
      let type: string;
      try {
        statSync(fullPath);
        type = eventType === 'rename' ? 'add' : 'change';
      } catch {
        type = 'unlink';
      }

      const watcherEvent: WatcherEvent = {
        source: 'file',
        type,
        path: fullPath,
        detail: `${type}: ${filename}`,
        timestamp: Date.now(),
      };

      this.addToBatch(watcherEvent);
    }, this.debounceMs));
  }

  /**
   * Add an event to the batch buffer. Flush after batch window.
   */
  private addToBatch(event: WatcherEvent): void {
    this.batchBuffer.push(event);

    if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => {
        this.flushBatch();
      }, this.batchWindowMs);
    }
  }

  /**
   * Flush the batch buffer, emitting all collected events.
   * If >5 changes, also emit a summary batch event.
   */
  private flushBatch(): void {
    this.batchTimer = null;
    const events = [...this.batchBuffer];
    this.batchBuffer = [];

    // Emit individual events
    for (const event of events) {
      this.emit('event', event);
    }

    // If many changes, emit a batch summary
    const changeEvents = events.filter(e => e.type === 'change' || e.type === 'add');
    if (changeEvents.length > 5) {
      this.emit('event', {
        source: 'file',
        type: 'batch-change',
        detail: `${changeEvents.length} files changed`,
        metadata: { batchSize: changeEvents.length, files: changeEvents.map(e => e.path) },
        timestamp: Date.now(),
      });
    }
  }

  /**
   * Check if a filename should be ignored.
   */
  private shouldIgnore(filename: string): boolean {
    if (IGNORED_FILES.has(filename)) return true;
    if (IGNORED_DIRS.has(filename)) return true;
    if (IGNORED_EXTENSIONS.has(extname(filename))) return true;
    for (const prefix of IGNORED_PREFIXES) {
      if (filename.startsWith(prefix)) return true;
    }
    return false;
  }
}
