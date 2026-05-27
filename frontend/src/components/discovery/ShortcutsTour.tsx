import { useCallback, useEffect, useState } from 'react';
import { Keyboard, X } from 'lucide-react';

const SEEN_KEY = 'coco:shortcuts-tour-seen';
const OPEN_EVENT = 'coco:open-shortcuts-tour';

interface TourShortcut {
  keys: string[];
  label: string;
  hint?: string;
}

const shortcuts: TourShortcut[] = [
  { keys: ['⌘', 'K'], label: 'Open the command palette', hint: 'Fuzzy-search every page and action' },
  { keys: ['⌘', 'J'], label: 'Launch Jarvis voice mode', hint: 'Dictate decisions hands-free' },
  { keys: ['⌘', 'B'], label: 'Toggle the sidebar', hint: 'Reclaim screen space' },
  { keys: ['j'], label: 'Move down in lists', hint: 'Vim-style navigation' },
  { keys: ['k'], label: 'Move up in lists', hint: 'Vim-style navigation' },
  { keys: ['?'], label: 'Reopen this tour', hint: 'Or open the full shortcut reference' },
  { keys: ['Esc'], label: 'Close this tour' },
];

function loadSeen(): boolean {
  try {
    return localStorage.getItem(SEEN_KEY) === '1';
  } catch {
    return false;
  }
}

function markSeen() {
  try {
    localStorage.setItem(SEEN_KEY, '1');
  } catch {
    // ignore
  }
}

function isInputFocused(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  return (
    tag === 'input' ||
    tag === 'textarea' ||
    tag === 'select' ||
    (el as HTMLElement).isContentEditable
  );
}

/** Programmatically open the tour from anywhere. */
export function openShortcutsTour() {
  window.dispatchEvent(new CustomEvent(OPEN_EVENT));
}

/**
 * Full-screen onboarding overlay listing the platform's core shortcuts.
 * Opens automatically on first run, on the `?` key, or via {@link openShortcutsTour}.
 */
export function ShortcutsTour() {
  const [open, setOpen] = useState(false);

  const close = useCallback(() => {
    setOpen(false);
    markSeen();
  }, []);

  // First-run auto-open. Small delay so it doesn't fight the initial paint.
  useEffect(() => {
    if (loadSeen()) return;
    const t = setTimeout(() => setOpen(true), 800);
    return () => clearTimeout(t);
  }, []);

  // Keyboard: `?` opens the tour, Esc closes it. Use capture so we beat any
  // legacy `?` handlers on the window.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && open) {
        e.preventDefault();
        e.stopPropagation();
        close();
        return;
      }
      if (e.key === '?' && !e.metaKey && !e.ctrlKey && !e.altKey && !isInputFocused()) {
        // Toggle the tour. Stop propagation so the legacy help overlay
        // doesn't also fire on the same keystroke.
        e.preventDefault();
        e.stopImmediatePropagation();
        setOpen((prev) => {
          if (prev) markSeen();
          return !prev;
        });
      }
    }
    window.addEventListener('keydown', onKeyDown, true);
    return () => window.removeEventListener('keydown', onKeyDown, true);
  }, [open, close]);

  // Custom event for programmatic open.
  useEffect(() => {
    function onOpen() {
      setOpen(true);
    }
    window.addEventListener(OPEN_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_EVENT, onOpen);
  }, []);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts tour"
      className="fixed inset-0 z-[80] flex items-center justify-center"
    >
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-md animate-in fade-in duration-150"
        onClick={close}
      />
      <div className="relative w-full max-w-xl mx-4 rounded-2xl border border-border bg-card shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Keyboard size={16} className="text-accent" />
            <h2 className="text-base font-semibold text-foreground">
              Welcome — meet your keyboard
            </h2>
          </div>
          <button
            type="button"
            onClick={close}
            aria-label="Close tour"
            className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-6 py-5">
          <p className="text-sm text-muted-foreground mb-4 leading-snug">
            CoCo is keyboard-first. These four shortcuts cover 90% of the surface
            — learn them once and you'll never reach for the mouse again.
          </p>

          <ul className="space-y-2.5">
            {shortcuts.map((s) => (
              <li
                key={s.label}
                className="flex items-center justify-between gap-4 rounded-md px-3 py-2 hover:bg-accent/20 transition-colors"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium text-foreground">{s.label}</div>
                  {s.hint && (
                    <div className="text-xs text-muted-foreground mt-0.5">{s.hint}</div>
                  )}
                </div>
                <div className="flex shrink-0 gap-1">
                  {s.keys.map((k, i) => (
                    <kbd
                      key={i}
                      className="min-w-[26px] text-center rounded border border-border bg-background px-2 py-1 text-xs font-mono font-medium text-foreground"
                    >
                      {k}
                    </kbd>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="border-t border-border px-6 py-3 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Press <kbd className="rounded border border-border px-1 py-0.5 font-mono">?</kbd>{' '}
            any time to reopen.
          </p>
          <button
            type="button"
            onClick={close}
            className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground hover:bg-accent/80 transition-colors"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}

/** Test-only: clear seen state. */
export function _resetShortcutsTourForTest() {
  try {
    localStorage.removeItem(SEEN_KEY);
  } catch {
    // ignore
  }
}
