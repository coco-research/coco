import { beforeEach, describe, expect, it } from 'vitest';
import { useJarvisStore } from '../jarvisStore';

const STORAGE_KEY = 'coco.jarvis.session';

describe('jarvisStore', () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset to a fresh session for each test
    useJarvisStore.getState().clear();
  });

  it('starts with empty messages and a session id', () => {
    const { messages, sessionId } = useJarvisStore.getState();
    expect(messages).toEqual([]);
    expect(typeof sessionId).toBe('string');
    expect(sessionId.length).toBeGreaterThan(0);
  });

  it('addExchange appends user + assistant messages', () => {
    useJarvisStore.getState().addExchange('hello', 'hi there');
    const { messages } = useJarvisStore.getState();
    expect(messages).toHaveLength(2);
    expect(messages[0]).toMatchObject({ role: 'user', text: 'hello' });
    expect(messages[1]).toMatchObject({ role: 'assistant', text: 'hi there' });
  });

  it('persists to localStorage under the versioned key', () => {
    useJarvisStore.getState().addExchange('q', 'a');
    const raw = localStorage.getItem(STORAGE_KEY);
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw!);
    expect(parsed.state.messages).toHaveLength(2);
    expect(parsed.state.sessionId).toBeTruthy();
    expect(parsed.version).toBe(1);
  });

  it('caps messages at 50', () => {
    const store = useJarvisStore.getState();
    for (let i = 0; i < 40; i++) {
      // 40 exchanges = 80 messages → should be capped to 50.
      store.addExchange(`q${i}`, `a${i}`);
    }
    const { messages } = useJarvisStore.getState();
    expect(messages.length).toBeLessThanOrEqual(50);
    // Most recent message should survive.
    expect(messages[messages.length - 1].text).toBe('a39');
  });

  it('enforces the 100KB serialized budget by trimming oldest', () => {
    const store = useJarvisStore.getState();
    // Each pair ~2KB of text → 60 pairs = ~120KB, well over budget.
    const filler = 'x'.repeat(2000);
    for (let i = 0; i < 60; i++) {
      store.addExchange(`q${i} ${filler}`, `a${i} ${filler}`);
    }
    const { messages } = useJarvisStore.getState();
    const bytes = JSON.stringify(messages).length;
    expect(bytes).toBeLessThanOrEqual(100 * 1024);
    // Newest message preserved.
    expect(messages[messages.length - 1].text).toContain('a59');
  });

  it('clear resets messages and rotates sessionId', () => {
    useJarvisStore.getState().addExchange('q', 'a');
    const before = useJarvisStore.getState().sessionId;
    useJarvisStore.getState().clear();
    const after = useJarvisStore.getState();
    expect(after.messages).toEqual([]);
    expect(after.sessionId).not.toBe(before);
  });
});
