import { type ReactNode, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';

const STORAGE_KEY = 'coco:feature-tooltips-seen';
type Placement = 'top' | 'bottom' | 'left' | 'right';

interface FeatureTooltipProps {
  /** Unique ID — used as the localStorage key suffix. Tooltip will not re-show once dismissed for this id. */
  id: string;
  /** Title shown next to the "New!" pill. */
  title: string;
  /** Tooltip body copy. */
  description: string;
  /** Element to anchor the tooltip against. */
  children: ReactNode;
  /** Preferred placement relative to the anchor. Defaults to "bottom". */
  placement?: Placement;
  /** Optional override label for the pill. Defaults to "New!". */
  badge?: string;
  /** Force-show even if previously seen. Useful for storybook. */
  forceShow?: boolean;
}

function loadSeen(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw);
    if (!Array.isArray(arr)) return new Set();
    return new Set(arr.filter((v): v is string => typeof v === 'string'));
  } catch {
    return new Set();
  }
}

function markSeen(id: string) {
  const seen = loadSeen();
  seen.add(id);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(seen)));
  } catch {
    // ignore — quota / private mode
  }
}

/**
 * Anchored "New!" feature tooltip. Renders the child as the anchor and a
 * popover above/below it. State persists in localStorage so the tooltip only
 * shows once per `id`.
 */
export function FeatureTooltip({
  id,
  title,
  description,
  children,
  placement = 'bottom',
  badge = 'New!',
  forceShow = false,
}: FeatureTooltipProps) {
  const [visible, setVisible] = useState(false);
  const anchorRef = useRef<HTMLSpanElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null);

  // Decide initial visibility from localStorage.
  useEffect(() => {
    if (forceShow) {
      setVisible(true);
      return;
    }
    if (!loadSeen().has(id)) {
      setVisible(true);
    }
  }, [id, forceShow]);

  // Position the popover relative to the anchor.
  useLayoutEffect(() => {
    if (!visible) return;
    const anchor = anchorRef.current;
    const pop = popoverRef.current;
    if (!anchor || !pop) return;

    const reposition = () => {
      const a = anchor.getBoundingClientRect();
      const p = pop.getBoundingClientRect();
      const gap = 8;
      let top = 0;
      let left = 0;
      switch (placement) {
        case 'top':
          top = a.top - p.height - gap;
          left = a.left + a.width / 2 - p.width / 2;
          break;
        case 'left':
          top = a.top + a.height / 2 - p.height / 2;
          left = a.left - p.width - gap;
          break;
        case 'right':
          top = a.top + a.height / 2 - p.height / 2;
          left = a.right + gap;
          break;
        case 'bottom':
        default:
          top = a.bottom + gap;
          left = a.left + a.width / 2 - p.width / 2;
          break;
      }
      // Keep inside viewport
      const pad = 8;
      left = Math.max(pad, Math.min(left, window.innerWidth - p.width - pad));
      top = Math.max(pad, Math.min(top, window.innerHeight - p.height - pad));
      setCoords({ top, left });
    };

    reposition();
    window.addEventListener('resize', reposition);
    window.addEventListener('scroll', reposition, true);
    return () => {
      window.removeEventListener('resize', reposition);
      window.removeEventListener('scroll', reposition, true);
    };
  }, [visible, placement]);

  const dismiss = () => {
    markSeen(id);
    setVisible(false);
  };

  return (
    <>
      <span ref={anchorRef} className="inline-flex">
        {children}
      </span>
      {visible && (
        <div
          ref={popoverRef}
          role="dialog"
          aria-label={`${badge} ${title}`}
          style={{
            position: 'fixed',
            top: coords?.top ?? -9999,
            left: coords?.left ?? -9999,
            visibility: coords ? 'visible' : 'hidden',
          }}
          className="z-[70] w-72 rounded-lg border border-accent/40 bg-card shadow-xl animate-in fade-in slide-in-from-top-1 duration-150"
        >
          <div className="flex items-start gap-2 px-3 py-2.5">
            <span className="shrink-0 rounded-full bg-accent/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent">
              {badge}
            </span>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-foreground leading-tight">
                {title}
              </h4>
              <p className="mt-1 text-xs text-muted-foreground leading-snug">
                {description}
              </p>
            </div>
            <button
              type="button"
              onClick={dismiss}
              aria-label="Dismiss tooltip"
              className="shrink-0 rounded p-0.5 text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
            >
              <X size={12} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

/** Test-only: clear seen tooltip state. */
export function _resetFeatureTooltipsForTest() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}
