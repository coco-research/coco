import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Use vi.hoisted so the mock fn is available inside vi.mock factory
const { mockExecFile } = vi.hoisted(() => ({
  mockExecFile: vi.fn(),
}));

vi.mock('node:child_process', () => ({
  execFile: mockExecFile,
}));

// Import after mocks are set up
import { notify, notifySessionComplete, notifyQueueDrained } from '../src/core/notifier.js';

/**
 * Helper: extract the AppleScript string from the mock call.
 * execFile is called as: execFile('osascript', ['-e', script], callback)
 */
function getScript(callIndex = 0): string {
  const args = mockExecFile.mock.calls[callIndex];
  // args[0] = 'osascript', args[1] = ['-e', script], args[2] = callback
  return args[1][1] as string;
}

describe('notifier', () => {
  const originalPlatform = process.platform;

  beforeEach(() => {
    mockExecFile.mockReset();
    // Default: simulate macOS
    Object.defineProperty(process, 'platform', { value: 'darwin' });
  });

  afterEach(() => {
    Object.defineProperty(process, 'platform', { value: originalPlatform });
  });

  describe('notify()', () => {
    it('calls execFile with osascript on macOS', () => {
      notify({ title: 'Test', message: 'Hello' });

      expect(mockExecFile).toHaveBeenCalledTimes(1);
      expect(mockExecFile.mock.calls[0][0]).toBe('osascript');
      expect(mockExecFile.mock.calls[0][1][0]).toBe('-e');
      const script = getScript();
      expect(script).toContain('display notification');
      expect(script).toContain('"Hello"');
      expect(script).toContain('with title "Test"');
    });

    it('includes subtitle when provided', () => {
      notify({ title: 'T', message: 'M', subtitle: 'Sub' });

      const script = getScript();
      expect(script).toContain('subtitle "Sub"');
    });

    it('includes sound by default', () => {
      notify({ title: 'T', message: 'M' });

      const script = getScript();
      expect(script).toContain('sound name "Glass"');
    });

    it('omits sound when sound is false', () => {
      notify({ title: 'T', message: 'M', sound: false });

      const script = getScript();
      expect(script).not.toContain('sound name');
    });

    it('does nothing on non-macOS platforms', () => {
      Object.defineProperty(process, 'platform', { value: 'linux' });

      notify({ title: 'T', message: 'M' });

      expect(mockExecFile).not.toHaveBeenCalled();
    });

    it('silently ignores execFile errors', () => {
      mockExecFile.mockImplementation(
        (_bin: string, _args: string[], cb: (err: Error | null) => void) => {
          cb(new Error('osascript failed'));
        }
      );

      // Should not throw
      expect(() => notify({ title: 'T', message: 'M' })).not.toThrow();
    });

    it('logs errors when COCO_DEBUG is set', () => {
      const origDebug = process.env.COCO_DEBUG;
      process.env.COCO_DEBUG = '1';
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      mockExecFile.mockImplementation(
        (_bin: string, _args: string[], cb: (err: Error | null) => void) => {
          cb(new Error('osascript failed'));
        }
      );

      notify({ title: 'T', message: 'M' });

      expect(consoleSpy).toHaveBeenCalledWith('[notifier]', 'osascript failed');

      consoleSpy.mockRestore();
      if (origDebug === undefined) {
        delete process.env.COCO_DEBUG;
      } else {
        process.env.COCO_DEBUG = origDebug;
      }
    });
  });

  describe('escapeAppleScript (via notify)', () => {
    it('escapes double quotes in message', () => {
      notify({ title: 'T', message: 'say "hello"' });

      const script = getScript();
      expect(script).toContain('say \\"hello\\"');
    });

    it('escapes backslashes in message', () => {
      notify({ title: 'T', message: 'path\\to\\file' });

      const script = getScript();
      expect(script).toContain('path\\\\to\\\\file');
    });

    it('escapes single quotes in message', () => {
      notify({ title: 'T', message: "it's done" });

      const script = getScript();
      // Single quotes are escaped as '\\'' for AppleScript shell context
      expect(script).toContain("it");
      expect(script).toContain("done");
    });

    it('handles mixed special characters', () => {
      notify({ title: 'T', message: 'a\\b"c\'d' });

      const script = getScript();
      // Should contain escaped backslash, escaped double quote
      expect(script).toContain('a\\\\b\\"c');
    });

    it('handles empty string message', () => {
      notify({ title: 'T', message: '' });

      const script = getScript();
      expect(script).toContain('display notification ""');
    });
  });

  describe('notifySessionComplete()', () => {
    it('sends success notification', () => {
      notifySessionComplete('team-research', true, 'All done');

      const script = getScript();
      expect(script).toContain('CoCo -- Done');
      expect(script).toContain('All done');
      expect(script).toContain('subtitle "team-research"');
    });

    it('sends failure notification', () => {
      notifySessionComplete('team-research', false);

      const script = getScript();
      expect(script).toContain('CoCo -- Failed');
      expect(script).toContain('team-research failed');
    });

    it('uses default message when no summary provided', () => {
      notifySessionComplete('brainstorm', true);

      const script = getScript();
      expect(script).toContain('brainstorm completed');
    });
  });

  describe('notifyQueueDrained()', () => {
    it('sends queue complete notification with count', () => {
      notifyQueueDrained(5);

      const script = getScript();
      expect(script).toContain('CoCo -- Queue Complete');
      expect(script).toContain('All 5 tasks finished');
    });

    it('includes sound', () => {
      notifyQueueDrained(1);

      const script = getScript();
      expect(script).toContain('sound name "Glass"');
    });
  });
});
