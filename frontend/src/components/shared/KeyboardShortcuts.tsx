import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface ShortcutEntry {
  keys: string;
  label: string;
}

const navigationShortcuts: ShortcutEntry[] = [
  { keys: 'g h', label: 'Home / Dashboard' },
  { keys: 'g t', label: 'My Portfolio' },
  { keys: 'g i', label: 'Inbox' },
  { keys: 'g a', label: 'Agent Team' },
  { keys: 'g c', label: 'Chat' },
  { keys: 'g s', label: 'Settings' },
  { keys: 'g k', label: 'Knowledge' },
  { keys: 'g p', label: 'Projects / Teams' },
  { keys: 'g o', label: 'Todos' },
  { keys: 'g l', label: 'Goals' },
  { keys: 'g $', label: 'Costs' },
  { keys: 'g v', label: 'Activity' },
];

const actionShortcuts: ShortcutEntry[] = [
  { keys: 'c', label: 'Create new...' },
  { keys: '\u2318K', label: 'Command palette' },
  { keys: '?', label: 'This help' },
  { keys: 'Esc', label: 'Close panel / dialog' },
];

const goRoutes: Record<string, string> = {
  h: '/',
  t: '/tree',
  i: '/inbox',
  a: '/agents',
  c: '/chat',
  s: '/settings',
  k: '/knowledge',
  p: '/projects',
  o: '/todos',
  l: '/goals',
  $: '/costs',
  v: '/activity',
};

export function KeyboardShortcuts() {
  const [showHelp, setShowHelp] = useState(false);
  const [pendingG, setPendingG] = useState(false);
  const navigate = useNavigate();

  const isInputFocused = useCallback(() => {
    const el = document.activeElement;
    if (!el) return false;
    const tag = el.tagName.toLowerCase();
    return (
      tag === 'input' ||
      tag === 'textarea' ||
      tag === 'select' ||
      (el as HTMLElement).isContentEditable
    );
  }, []);

  useEffect(() => {
    let gTimer: ReturnType<typeof setTimeout> | null = null;

    function onKeyDown(e: KeyboardEvent) {
      // Don't intercept when typing in inputs
      if (isInputFocused()) return;
      // Don't intercept when modifier keys are held (Cmd+K handled by CommandPalette)
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      const key = e.key;

      // Escape — close help or let it bubble
      if (key === 'Escape') {
        if (showHelp) {
          setShowHelp(false);
          e.preventDefault();
        }
        if (pendingG) {
          setPendingG(false);
          if (gTimer) clearTimeout(gTimer);
        }
        return;
      }

      // ? — toggle help
      if (key === '?') {
        e.preventDefault();
        setShowHelp((prev) => !prev);
        return;
      }

      // Two-key chords: g + letter
      if (pendingG) {
        setPendingG(false);
        if (gTimer) clearTimeout(gTimer);
        if (goRoutes[key]) {
          e.preventDefault();
          navigate(goRoutes[key]);
        }
        return;
      }

      // Start "go mode"
      if (key === 'g') {
        setPendingG(true);
        gTimer = setTimeout(() => setPendingG(false), 1000);
        return;
      }

      // "c" — create new (dispatch custom event for pages to handle)
      if (key === 'c') {
        e.preventDefault();
        window.dispatchEvent(new CustomEvent('coco:create'));
        return;
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      if (gTimer) clearTimeout(gTimer);
    };
  }, [pendingG, showHelp, navigate, isInputFocused]);

  return (
    <>
      {/* Go-mode indicator */}
      {pendingG && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[60] animate-fade-in">
          <div className="flex items-center gap-2 rounded-lg border border-accent/50 bg-card px-3 py-1.5 text-sm shadow-lg">
            <kbd className="rounded border border-border bg-background px-1.5 py-0.5 text-xs font-mono text-accent font-semibold">
              g
            </kbd>
            <span className="text-muted-foreground">waiting for destination...</span>
          </div>
        </div>
      )}

      {/* Shortcuts help overlay */}
      {showHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowHelp(false)}
          />
          <div className="relative w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <h2 className="text-lg font-semibold text-foreground">
                Keyboard Shortcuts
              </h2>
              <button
                onClick={() => setShowHelp(false)}
                className="text-muted-foreground hover:text-foreground transition-colors text-sm"
              >
                <kbd className="rounded border border-border bg-background px-1.5 py-0.5 text-xs font-mono">
                  Esc
                </kbd>
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-6 max-h-[60vh] overflow-y-auto">
              {/* Navigation section */}
              <div>
                <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                  Navigation
                </h3>
                <div className="grid grid-cols-2 gap-x-8 gap-y-2">
                  {navigationShortcuts.map((s) => (
                    <div
                      key={s.keys}
                      className="flex items-center justify-between text-sm"
                    >
                      <span className="text-muted-foreground">{s.label}</span>
                      <div className="flex gap-1 ml-3">
                        {s.keys.split(' ').map((k, i) => (
                          <kbd
                            key={i}
                            className="rounded border border-border bg-background px-1.5 py-0.5 text-xs font-mono text-foreground min-w-[22px] text-center"
                          >
                            {k}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions section */}
              <div>
                <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                  Actions
                </h3>
                <div className="grid grid-cols-2 gap-x-8 gap-y-2">
                  {actionShortcuts.map((s) => (
                    <div
                      key={s.keys}
                      className="flex items-center justify-between text-sm"
                    >
                      <span className="text-muted-foreground">{s.label}</span>
                      <div className="flex gap-1 ml-3">
                        {s.keys.split(' ').map((k, i) => (
                          <kbd
                            key={i}
                            className="rounded border border-border bg-background px-1.5 py-0.5 text-xs font-mono text-foreground min-w-[22px] text-center"
                          >
                            {k}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-border px-6 py-3">
              <p className="text-xs text-muted-foreground text-center">
                Press <kbd className="rounded border border-border px-1 py-0.5 font-mono">?</kbd> or{' '}
                <kbd className="rounded border border-border px-1 py-0.5 font-mono">Esc</kbd> to close
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
