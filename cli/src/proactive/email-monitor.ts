/**
 * Phase 5: Email Monitor
 *
 * Watches for new emails via three approaches:
 * 1. HxStore modification time polling + strings extraction
 * 2. Attachment cache directory watching
 * 3. Manual drop folder watching
 *
 * Gracefully degrades when resources are unavailable.
 */

import { EventEmitter } from 'eventemitter3';
import { existsSync, statSync, readFileSync, writeFileSync, watch, mkdirSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { join, basename, extname } from 'node:path';
import { homedir } from 'node:os';
import type { FSWatcher } from 'node:fs';
import type { WatcherEvent } from './types.js';

export interface EmailMonitorEvents {
  event: (event: WatcherEvent) => void;
  error: (err: Error) => void;
  warning: (msg: string) => void;
}

export interface EmailMonitorConfig {
  /** Keywords to look for in HxStore extraction */
  keywords: string[];
  /** Manual drop folder path (default: ./inbox/) */
  dropFolder?: string;
  /** HxStore poll interval in ms (default: 30000) */
  hxPollIntervalMs?: number;
  /** Path to store last sync timestamp */
  syncStatePath?: string;
}

// macOS Outlook paths
const HXSTORE_PATH = join(
  homedir(),
  'Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/HxStore.hxd',
);

const ATTACHMENT_PATH = join(
  homedir(),
  'Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Data/Files/S0/4/Attachments/0',
);

/** Maximum HxStore file size before skipping extraction (2 GB). */
const MAX_HXSTORE_BYTES = 2 * 1024 * 1024 * 1024;

export class EmailMonitor extends EventEmitter<EmailMonitorEvents> {
  private running: boolean = false;
  private hxPollTimer: NodeJS.Timeout | null = null;
  private attachmentWatcher: FSWatcher | null = null;
  private dropFolderWatcher: FSWatcher | null = null;

  private lastHxMtime: number = 0;
  private lastExtract: Set<string> = new Set();
  private hxPollIntervalMs: number;
  private keywords: string[];
  private dropFolder: string | null;
  private syncStatePath: string;

  private hxAvailable: boolean = false;
  private attachmentAvailable: boolean = false;

  constructor(private config: EmailMonitorConfig) {
    super();
    this.keywords = config.keywords;
    this.dropFolder = config.dropFolder ?? null;
    this.hxPollIntervalMs = config.hxPollIntervalMs ?? 30_000;
    this.syncStatePath = config.syncStatePath ?? join(homedir(), '.coco', '.last-hxstore-extract');
  }

  /**
   * Start all available monitoring channels.
   */
  start(): void {
    if (this.running) return;
    this.running = true;

    // Channel 1: HxStore polling
    this.startHxStorePolling();

    // Channel 2: Attachment cache watching
    this.startAttachmentWatching();

    // Channel 3: Manual drop folder
    if (this.dropFolder) {
      this.startDropFolderWatching();
    }
  }

  /**
   * Stop all monitoring.
   */
  stop(): void {
    this.running = false;

    if (this.hxPollTimer) {
      clearInterval(this.hxPollTimer);
      this.hxPollTimer = null;
    }

    if (this.attachmentWatcher) {
      try { this.attachmentWatcher.close(); } catch {}
      this.attachmentWatcher = null;
    }

    if (this.dropFolderWatcher) {
      try { this.dropFolderWatcher.close(); } catch {}
      this.dropFolderWatcher = null;
    }
  }

  get isRunning(): boolean {
    return this.running;
  }

  /**
   * Get status of each monitoring channel.
   */
  getChannelStatus(): { hxStore: boolean; attachments: boolean; dropFolder: boolean } {
    return {
      hxStore: this.hxAvailable,
      attachments: this.attachmentAvailable,
      dropFolder: this.dropFolder !== null && this.dropFolderWatcher !== null,
    };
  }

  // --- HxStore Polling ---

  private startHxStorePolling(): void {
    if (!existsSync(HXSTORE_PATH)) {
      this.emit('warning', 'HxStore not found. Email content monitoring disabled. Attachments and drop folder still active.');
      this.hxAvailable = false;
      return;
    }

    this.hxAvailable = true;

    // Load previous extract state
    try {
      if (existsSync(this.syncStatePath)) {
        const data = readFileSync(this.syncStatePath, 'utf-8');
        this.lastExtract = new Set(data.split('\n').filter(Boolean));
      }
    } catch {
      // Fresh start
    }

    // Get initial mtime
    try {
      this.lastHxMtime = statSync(HXSTORE_PATH).mtimeMs;
    } catch {
      this.hxAvailable = false;
      return;
    }

    this.hxPollTimer = setInterval(() => {
      this.pollHxStore();
    }, this.hxPollIntervalMs);
  }

  private pollHxStore(): void {
    if (!this.running) return;

    try {
      const stat = statSync(HXSTORE_PATH);
      if (stat.mtimeMs <= this.lastHxMtime) return;
      this.lastHxMtime = stat.mtimeMs;
    } catch {
      // File gone or permissions changed
      this.hxAvailable = false;
      this.emit('warning', 'Lost access to HxStore. Email content monitoring paused.');
      return;
    }

    // Run strings extraction with keyword grep
    this.extractHxStore();
  }

  private extractHxStore(): void {
    const keywordPattern = this.keywords.join('|');
    if (!keywordPattern) return;

    // Guard: skip extraction if HxStore exceeds 2 GB
    try {
      const size = statSync(HXSTORE_PATH).size;
      if (size > MAX_HXSTORE_BYTES) {
        this.emit('warning', `HxStore is ${(size / (1024 * 1024 * 1024)).toFixed(1)} GB — skipping strings extraction (limit: 2 GB).`);
        return;
      }
    } catch {
      return; // Can't stat, skip
    }

    execFile('strings', [HXSTORE_PATH], { maxBuffer: 10 * 1024 * 1024, timeout: 15_000 }, (err, stdout) => {
      if (err || !this.running) return;

      const regex = new RegExp(keywordPattern, 'i');
      const lines = stdout.split('\n').filter(line => regex.test(line));
      const lineSet = new Set(lines);

      // Find new lines
      const newLines: string[] = [];
      for (const line of lineSet) {
        if (!this.lastExtract.has(line)) {
          newLines.push(line);
        }
      }

      // Update state
      this.lastExtract = lineSet;

      // Persist
      try {
        writeFileSync(this.syncStatePath, Array.from(lineSet).join('\n'), 'utf-8');
      } catch {
        // Non-critical
      }

      // Emit events for new content
      if (newLines.length > 0) {
        // Try to extract subject-like fragments
        const preview = newLines[0].slice(0, 80);
        this.emit('event', {
          source: 'email',
          type: 'hxstore-new-content',
          detail: `New email content: "${preview}"`,
          metadata: { newLineCount: newLines.length, preview },
          timestamp: Date.now(),
        });
      }
    });
  }

  // --- Attachment Cache Watching ---

  private startAttachmentWatching(): void {
    if (!existsSync(ATTACHMENT_PATH)) {
      this.emit('warning', 'Outlook attachment cache not found. Attachment monitoring disabled.');
      this.attachmentAvailable = false;
      return;
    }

    this.attachmentAvailable = true;

    try {
      this.attachmentWatcher = watch(ATTACHMENT_PATH, { persistent: false }, (eventType, filename) => {
        if (!filename || !this.running) return;
        if (eventType !== 'rename') return; // 'rename' = new file on macOS

        const ext = extname(filename).toLowerCase();
        const isDocument = ['.pdf', '.docx', '.xlsx', '.pptx', '.csv', '.txt'].includes(ext);
        const isImage = ['.png', '.jpg', '.jpeg', '.gif', '.heic'].includes(ext);

        if (isDocument) {
          this.emit('event', {
            source: 'email',
            type: 'new-attachment',
            path: join(ATTACHMENT_PATH, filename),
            detail: `New attachment: ${filename}`,
            metadata: { filename, ext, kind: 'document' },
            timestamp: Date.now(),
          });
        } else if (isImage) {
          this.emit('event', {
            source: 'email',
            type: 'new-attachment',
            path: join(ATTACHMENT_PATH, filename),
            detail: `New screenshot/image: ${filename}`,
            metadata: { filename, ext, kind: 'image' },
            timestamp: Date.now(),
          });
        }
      });

      this.attachmentWatcher.on('error', () => {
        this.attachmentAvailable = false;
      });
    } catch {
      this.attachmentAvailable = false;
    }
  }

  // --- Manual Drop Folder ---

  private startDropFolderWatching(): void {
    if (!this.dropFolder) return;

    // Create drop folder if it doesn't exist
    try {
      if (!existsSync(this.dropFolder)) {
        mkdirSync(this.dropFolder, { recursive: true });
      }
    } catch {
      this.emit('warning', `Could not create drop folder: ${this.dropFolder}`);
      return;
    }

    try {
      this.dropFolderWatcher = watch(this.dropFolder, { persistent: false }, (eventType, filename) => {
        if (!filename || !this.running) return;
        if (eventType !== 'rename') return;

        const ext = extname(filename).toLowerCase();
        const fullPath = join(this.dropFolder!, filename);

        // Check if file exists (rename can also mean delete)
        try {
          statSync(fullPath);
        } catch {
          return; // File was deleted, not added
        }

        if (ext === '.eml' || ext === '.msg') {
          this.emit('event', {
            source: 'email',
            type: 'manual-drop',
            path: fullPath,
            detail: `Email dropped: ${filename}`,
            metadata: { filename, ext },
            timestamp: Date.now(),
          });
        } else {
          // Any other file dropped to inbox
          this.emit('event', {
            source: 'email',
            type: 'manual-drop',
            path: fullPath,
            detail: `File dropped: ${filename}`,
            metadata: { filename, ext },
            timestamp: Date.now(),
          });
        }
      });

      this.dropFolderWatcher.on('error', () => {
        // Silently degrade
      });
    } catch {
      // Can't watch drop folder
    }
  }
}
