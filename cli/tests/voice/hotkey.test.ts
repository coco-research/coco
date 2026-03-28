import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { PushToTalkController } from '../../src/voice/hotkey.js';

describe('PushToTalkController', () => {
  let ptt: PushToTalkController;

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('hold mode', () => {
    beforeEach(() => {
      ptt = new PushToTalkController('f5', 'hold');
    });

    it('emits ptt-start on first F5 keypress', () => {
      const startHandler = vi.fn();
      ptt.on('ptt-start', startHandler);

      const consumed = ptt.handleRawData(Buffer.from('\x1b[15~'));
      expect(consumed).toBe(true);
      expect(startHandler).toHaveBeenCalledTimes(1);
      expect(ptt.held).toBe(true);
    });

    it('emits ptt-stop after 200ms without repeat', () => {
      const stopHandler = vi.fn();
      ptt.on('ptt-stop', stopHandler);

      ptt.handleRawData(Buffer.from('\x1b[15~'));
      expect(stopHandler).not.toHaveBeenCalled();

      vi.advanceTimersByTime(200);
      expect(stopHandler).toHaveBeenCalledTimes(1);
      expect(ptt.held).toBe(false);
    });

    it('does not emit ptt-stop during key repeat', () => {
      const stopHandler = vi.fn();
      ptt.on('ptt-stop', stopHandler);

      ptt.handleRawData(Buffer.from('\x1b[15~'));

      // Simulate key repeat at 100ms intervals
      vi.advanceTimersByTime(100);
      ptt.handleRawData(Buffer.from('\x1b[15~'));

      vi.advanceTimersByTime(100);
      ptt.handleRawData(Buffer.from('\x1b[15~'));

      vi.advanceTimersByTime(100);
      ptt.handleRawData(Buffer.from('\x1b[15~'));

      expect(stopHandler).not.toHaveBeenCalled();
      expect(ptt.held).toBe(true);

      // Now stop repeating
      vi.advanceTimersByTime(200);
      expect(stopHandler).toHaveBeenCalledTimes(1);
    });

    it('ignores non-PTT keys', () => {
      const startHandler = vi.fn();
      ptt.on('ptt-start', startHandler);

      const consumed = ptt.handleRawData(Buffer.from('a'));
      expect(consumed).toBe(false);
      expect(startHandler).not.toHaveBeenCalled();
    });
  });

  describe('toggle mode', () => {
    beforeEach(() => {
      ptt = new PushToTalkController('f5', 'toggle');
    });

    it('first press starts, second press stops', () => {
      const startHandler = vi.fn();
      const stopHandler = vi.fn();
      ptt.on('ptt-start', startHandler);
      ptt.on('ptt-stop', stopHandler);

      ptt.handleRawData(Buffer.from('\x1b[15~'));
      expect(startHandler).toHaveBeenCalledTimes(1);
      expect(ptt.held).toBe(true);

      ptt.handleRawData(Buffer.from('\x1b[15~'));
      expect(stopHandler).toHaveBeenCalledTimes(1);
      expect(ptt.held).toBe(false);
    });

    it('does not use release timer', () => {
      ptt.handleRawData(Buffer.from('\x1b[15~'));
      vi.advanceTimersByTime(500);
      // Should still be held — toggle doesn't auto-release
      expect(ptt.held).toBe(true);
    });
  });

  it('forceRelease cancels active recording', () => {
    ptt = new PushToTalkController('f5', 'toggle');

    const stopHandler = vi.fn();
    ptt.on('ptt-stop', stopHandler);

    ptt.handleRawData(Buffer.from('\x1b[15~'));
    expect(ptt.held).toBe(true);

    ptt.forceRelease();
    expect(ptt.held).toBe(false);
    expect(stopHandler).toHaveBeenCalledTimes(1);
  });

  it('forceRelease does nothing if not held', () => {
    ptt = new PushToTalkController('f5', 'toggle');

    const stopHandler = vi.fn();
    ptt.on('ptt-stop', stopHandler);

    ptt.forceRelease();
    expect(stopHandler).not.toHaveBeenCalled();
  });

  it('handles Ctrl+Space as alternative PTT key', () => {
    ptt = new PushToTalkController('ctrl+space', 'toggle');

    const startHandler = vi.fn();
    ptt.on('ptt-start', startHandler);

    ptt.handleRawData(Buffer.from('\x00'));
    expect(startHandler).toHaveBeenCalledTimes(1);
  });

  it('setMode switches between hold and toggle at runtime', () => {
    ptt = new PushToTalkController('f5', 'hold');

    const startHandler = vi.fn();
    const stopHandler = vi.fn();
    ptt.on('ptt-start', startHandler);
    ptt.on('ptt-stop', stopHandler);

    // In hold mode, auto-release happens
    ptt.handleRawData(Buffer.from('\x1b[15~'));
    vi.advanceTimersByTime(200);
    expect(stopHandler).toHaveBeenCalledTimes(1);

    // Switch to toggle mode
    ptt.setMode('toggle');

    ptt.handleRawData(Buffer.from('\x1b[15~'));
    vi.advanceTimersByTime(500);
    // Should NOT auto-release in toggle mode
    expect(ptt.held).toBe(true);

    ptt.handleRawData(Buffer.from('\x1b[15~'));
    expect(ptt.held).toBe(false);
  });
});
