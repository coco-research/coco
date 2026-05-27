/**
 * Mic-permission helpers.
 *
 * The browser surfaces denied microphone access as a `NotAllowedError` (or the
 * legacy `PermissionDeniedError`) from `navigator.mediaDevices.getUserMedia`,
 * and as `not-allowed` / `service-not-allowed` from the Web Speech API.
 *
 * Once the user denies access, the browser typically won't re-prompt for the
 * duration of the page session (some browsers persist the denial across
 * sessions). Re-calling getUserMedia silently rejects with the same error,
 * which produces a poor UX if we keep showing "trying..." spinners. We mirror
 * that "sticky" behaviour in our own session so we can short-circuit the call
 * and show a useful help message instead.
 */

const STORAGE_KEY = 'coco:mic-permission-denied';

/** Returns true if a previous attempt in this browser session was denied. */
export function isMicDenied(): boolean {
  try {
    return sessionStorage.getItem(STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

/** Persist denial for the remainder of the session so we don't re-prompt. */
export function markMicDenied(): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, '1');
  } catch {
    // sessionStorage can be unavailable (privacy mode); ignore.
  }
}

/** Clear the denial flag — call when the user explicitly retries. */
export function clearMicDenied(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

/**
 * Best-effort detection of the user's browser. We only need to distinguish
 * Chrome-family, Safari, Firefox, and Edge — anything else falls back to a
 * generic help page.
 */
export type SupportedBrowser = 'chrome' | 'safari' | 'firefox' | 'edge' | 'other';

export function detectBrowser(): SupportedBrowser {
  if (typeof navigator === 'undefined') return 'other';
  const ua = navigator.userAgent;
  // Edge identifies itself as "Edg/" in modern Chromium-based Edge.
  if (/Edg\//.test(ua)) return 'edge';
  // Chrome must be checked before Safari (Chrome UA contains "Safari").
  if (/Chrome\//.test(ua) && !/OPR\//.test(ua)) return 'chrome';
  if (/Firefox\//.test(ua)) return 'firefox';
  if (/Safari\//.test(ua)) return 'safari';
  return 'other';
}

/** Returns a browser-specific help URL for re-enabling mic access. */
export function getBrowserHelpUrl(browser: SupportedBrowser = detectBrowser()): string {
  switch (browser) {
    case 'chrome':
      return 'https://support.google.com/chrome/answer/2693767';
    case 'safari':
      return 'https://support.apple.com/guide/safari/websites-ibrwe2159f50/mac';
    case 'firefox':
      return 'https://support.mozilla.org/en-US/kb/how-manage-your-camera-and-microphone-permissions';
    case 'edge':
      return 'https://support.microsoft.com/en-us/microsoft-edge/permissions-for-sites-d8d04d80-3e9e-4d7a-9b73-49d4dbeae077';
    default:
      return 'https://support.google.com/chrome/answer/2693767';
  }
}

/** Human-readable label for the help link. */
export function getBrowserHelpLabel(browser: SupportedBrowser = detectBrowser()): string {
  switch (browser) {
    case 'chrome':
      return 'How to enable in Chrome';
    case 'safari':
      return 'How to enable in Safari';
    case 'firefox':
      return 'How to enable in Firefox';
    case 'edge':
      return 'How to enable in Edge';
    default:
      return 'Browser help';
  }
}

/**
 * Returns true if an error (either a DOMException from getUserMedia or a
 * Web Speech API error code string) represents a permission denial.
 */
export function isPermissionDeniedError(err: unknown): boolean {
  if (!err) return false;
  // DOMException from getUserMedia
  if (typeof err === 'object' && err !== null) {
    const name = (err as { name?: string }).name;
    if (name === 'NotAllowedError' || name === 'PermissionDeniedError' || name === 'SecurityError') {
      return true;
    }
    const message = (err as { message?: string }).message;
    if (typeof message === 'string' && /permission|denied|not.?allowed/i.test(message)) {
      return true;
    }
  }
  // Web Speech API error codes
  if (typeof err === 'string') {
    return err === 'not-allowed' || err === 'service-not-allowed';
  }
  return false;
}
