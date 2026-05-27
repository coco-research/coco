/**
 * Jarvis conversation store with localStorage persistence.
 *
 * Persists the Jarvis conversation (messages + sessionId) across page
 * navigations so users can leave the Jarvis overlay (e.g. navigate to
 * /todos) and return without losing context.
 *
 * Caps:
 *   - last 50 messages
 *   - 100KB serialized payload (truncates oldest messages if exceeded)
 *
 * Storage key: "coco.jarvis.session" (versioned via zustand persist).
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type JarvisRole = 'user' | 'assistant';

export interface JarvisMessage {
  id: string;
  role: JarvisRole;
  text: string;
  /** ISO timestamp */
  createdAt: string;
}

const MAX_MESSAGES = 50;
const MAX_PAYLOAD_BYTES = 100 * 1024; // 100 KB

function newSessionId(): string {
  // Cryptographically-random when available; falls back to Math.random.
  const c = typeof globalThis !== 'undefined' ? (globalThis as { crypto?: Crypto }).crypto : undefined;
  if (c && typeof c.randomUUID === 'function') return c.randomUUID();
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function newMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Trim oldest messages until the serialized payload fits under MAX_PAYLOAD_BYTES.
 * Always keeps the most recent message to avoid degenerate empty state.
 */
function fitToBudget(messages: JarvisMessage[]): JarvisMessage[] {
  if (messages.length === 0) return messages;
  let working = messages.slice(-MAX_MESSAGES);
  // Quick byte estimate using JSON length (1 char ≈ 1 byte for ASCII; slight
  // over-count for unicode but safe for a soft cap).
  while (working.length > 1 && JSON.stringify(working).length > MAX_PAYLOAD_BYTES) {
    working = working.slice(1);
  }
  return working;
}

interface JarvisState {
  sessionId: string;
  messages: JarvisMessage[];
  addMessage: (role: JarvisRole, text: string) => void;
  addExchange: (userText: string, assistantText: string) => void;
  clear: () => void;
}

export const useJarvisStore = create<JarvisState>()(
  persist(
    (set) => ({
      sessionId: newSessionId(),
      messages: [],

      addMessage: (role, text) =>
        set((state) => {
          const next = fitToBudget([
            ...state.messages,
            { id: newMessageId(), role, text, createdAt: new Date().toISOString() },
          ]);
          return { messages: next };
        }),

      addExchange: (userText, assistantText) =>
        set((state) => {
          const now = Date.now();
          const next = fitToBudget([
            ...state.messages,
            { id: newMessageId(), role: 'user', text: userText, createdAt: new Date(now).toISOString() },
            { id: newMessageId(), role: 'assistant', text: assistantText, createdAt: new Date(now + 1).toISOString() },
          ]);
          return { messages: next };
        }),

      clear: () =>
        set(() => ({
          sessionId: newSessionId(),
          messages: [],
        })),
    }),
    {
      name: 'coco.jarvis.session',
      version: 1,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ sessionId: state.sessionId, messages: state.messages }),
    },
  ),
);
