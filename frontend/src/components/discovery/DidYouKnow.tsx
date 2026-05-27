import { useEffect, useMemo, useState } from 'react';
import { Lightbulb, X, RefreshCw } from 'lucide-react';
import tipsData from './tips.json';

export interface Tip {
  id: string;
  title: string;
  body: string;
}

const TIPS: Tip[] = tipsData as Tip[];
const DISMISSED_KEY = 'coco:dyk-dismissed';
const SEEN_KEY = 'coco:dyk-seen-ids';
const ROTATION_KEY = 'coco:dyk-last-index';

function readBool(key: string): boolean {
  try {
    return localStorage.getItem(key) === '1';
  } catch {
    return false;
  }
}

function writeBool(key: string, value: boolean) {
  try {
    localStorage.setItem(key, value ? '1' : '0');
  } catch {
    // ignore
  }
}

function readSeen(): Set<string> {
  try {
    const raw = localStorage.getItem(SEEN_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw);
    return new Set(Array.isArray(arr) ? arr.filter((v): v is string => typeof v === 'string') : []);
  } catch {
    return new Set();
  }
}

function writeSeen(seen: Set<string>) {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify(Array.from(seen)));
  } catch {
    // ignore
  }
}

function pickNextTip(): Tip {
  if (TIPS.length === 0) {
    return { id: 'empty', title: '', body: '' };
  }
  const seen = readSeen();
  // Prefer unseen tips
  const unseen = TIPS.filter((t) => !seen.has(t.id));
  if (unseen.length > 0) {
    return unseen[Math.floor(Math.random() * unseen.length)];
  }
  // All seen — rotate by last index
  let lastIdx = -1;
  try {
    const raw = localStorage.getItem(ROTATION_KEY);
    if (raw) lastIdx = parseInt(raw, 10);
  } catch {
    // ignore
  }
  const next = (Number.isFinite(lastIdx) ? lastIdx + 1 : 0) % TIPS.length;
  try {
    localStorage.setItem(ROTATION_KEY, String(next));
  } catch {
    // ignore
  }
  return TIPS[next];
}

interface DidYouKnowProps {
  /** Force-show even after the user dismissed permanently. */
  forceShow?: boolean;
}

/**
 * Small dismissible "Did you know?" card. Rotates through {@link TIPS}.
 * Once the user clicks the X, the card is dismissed permanently (persisted in
 * localStorage). They can also cycle to the next tip with the refresh button.
 */
export function DidYouKnow({ forceShow = false }: DidYouKnowProps) {
  const [dismissed, setDismissed] = useState<boolean>(() => !forceShow && readBool(DISMISSED_KEY));
  const initialTip = useMemo(() => pickNextTip(), []);
  const [tip, setTip] = useState<Tip>(initialTip);

  // Mark the displayed tip as seen
  useEffect(() => {
    if (dismissed) return;
    const seen = readSeen();
    if (!seen.has(tip.id)) {
      seen.add(tip.id);
      writeSeen(seen);
    }
  }, [tip, dismissed]);

  const dismiss = () => {
    writeBool(DISMISSED_KEY, true);
    setDismissed(true);
  };

  const cycle = () => {
    setTip(pickNextTip());
  };

  if (dismissed || !tip || !tip.title) return null;

  return (
    <div
      role="note"
      aria-label="Did you know"
      className="rounded-lg border border-border bg-card/60 px-3 py-2.5 flex items-start gap-2.5"
    >
      <Lightbulb size={14} className="mt-0.5 shrink-0 text-warning" aria-hidden />
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Did you know?
        </div>
        <div className="mt-0.5 text-sm font-medium text-foreground leading-snug">
          {tip.title}
        </div>
        <div className="mt-0.5 text-xs text-muted-foreground leading-snug">
          {tip.body}
        </div>
      </div>
      <div className="flex items-center gap-0.5 -mr-1 -mt-1">
        <button
          type="button"
          onClick={cycle}
          aria-label="Show another tip"
          title="Show another tip"
          className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
        >
          <RefreshCw size={12} />
        </button>
        <button
          type="button"
          onClick={dismiss}
          aria-label="Dismiss did you know card"
          title="Dismiss"
          className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  );
}

/** Test-only: clear persisted state. */
export function _resetDidYouKnowForTest() {
  try {
    localStorage.removeItem(DISMISSED_KEY);
    localStorage.removeItem(SEEN_KEY);
    localStorage.removeItem(ROTATION_KEY);
  } catch {
    // ignore
  }
}

export const _TIPS_FOR_TEST = TIPS;
