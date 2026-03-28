import { EventEmitter } from 'eventemitter3';

interface HotkeyEvents {
  'ptt-start': () => void;
  'ptt-stop': () => void;
}

/**
 * Push-to-talk mode:
 * - 'hold': Hold key to record, release to stop (uses key-repeat detection).
 * - 'toggle': First press starts recording, second press stops.
 */
export type PTTMode = 'hold' | 'toggle';

export class PushToTalkController extends EventEmitter<HotkeyEvents> {
  private pttKey: string;
  private isHeld = false;
  private mode: PTTMode;
  private releaseTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(pttKey: string = 'f5', mode: PTTMode = 'hold') {
    super();
    this.pttKey = pttKey;
    this.mode = mode;
  }

  /**
   * Called from raw stdin handler.
   *
   * F5 = ESC [ 1 5 ~  = "\x1b[15~"
   * Ctrl+Space = "\x00"
   *
   * Supports two modes:
   * - 'hold': keydown starts, keyup (detected via repeat timeout) stops
   * - 'toggle': first press starts, second press stops
   */
  handleRawData(data: Buffer): boolean {
    const str = data.toString();

    // F5 escape sequence
    const isF5 = str === '\x1b[15~';
    // Ctrl+Space
    const isCtrlSpace = str === '\x00';

    const isPTTKey = (this.pttKey === 'f5' && isF5)
      || (this.pttKey === 'ctrl+space' && isCtrlSpace);

    if (!isPTTKey) return false;  // not our key, don't consume

    if (this.mode === 'toggle') {
      return this.handleToggle();
    }
    return this.handleHold();
  }

  private handleToggle(): boolean {
    if (!this.isHeld) {
      // First press — start recording
      this.isHeld = true;
      this.emit('ptt-start');
    } else {
      // Second press — stop recording
      this.isHeld = false;
      if (this.releaseTimer) clearTimeout(this.releaseTimer);
      this.emit('ptt-stop');
    }
    return true;
  }

  private handleHold(): boolean {
    if (!this.isHeld) {
      // Key just pressed — start recording
      this.isHeld = true;
      this.emit('ptt-start');

      // Set a timer: if we don't see the key again within 200ms,
      // treat it as "released".
      this.startReleaseDetection();
    } else {
      // Key is being held (auto-repeat) — reset release timer
      this.resetReleaseTimer();
    }

    return true;  // consumed the key event
  }

  private startReleaseDetection(): void {
    this.releaseTimer = setTimeout(() => {
      // No repeat received within window — key was released
      this.isHeld = false;
      this.emit('ptt-stop');
    }, 200);  // 200ms — generous for key repeat interval
  }

  private resetReleaseTimer(): void {
    if (this.releaseTimer) clearTimeout(this.releaseTimer);
    this.startReleaseDetection();
  }

  /** Switch between hold and toggle mode at runtime */
  setMode(mode: PTTMode): void {
    this.mode = mode;
  }

  /** Force stop (e.g., when voice is toggled off) */
  forceRelease(): void {
    if (this.isHeld) {
      this.isHeld = false;
      if (this.releaseTimer) clearTimeout(this.releaseTimer);
      this.emit('ptt-stop');
    }
  }

  get held(): boolean {
    return this.isHeld;
  }

  /** Update the PTT key binding */
  setKey(key: string): void {
    this.pttKey = key;
  }
}
