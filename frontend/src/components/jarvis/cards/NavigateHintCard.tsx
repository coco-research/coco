import { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cn } from '../../../lib/utils';
import type { NavigateHintData } from '../../../types/cards';

interface NavigateHintCardProps {
  data: NavigateHintData;
  variant?: 'jarvis' | 'light';
  delay?: number;
}

const NAV_DURATION = 2000;

export function NavigateHintCard({
  data,
  variant = 'jarvis',
  delay = 0,
}: NavigateHintCardProps) {
  const isJarvis = variant === 'jarvis';
  const navigate = useNavigate();
  const location = useLocation();
  const [progress, setProgress] = useState(0);
  const [cancelled, setCancelled] = useState(false);
  const rafRef = useRef<number>(0);
  const initialPathRef = useRef<string>(location.pathname);

  // Cancel pending auto-nav if the user navigates manually first
  useEffect(() => {
    if (cancelled) return;
    if (location.pathname !== initialPathRef.current) {
      cancelAnimationFrame(rafRef.current);
      setCancelled(true);
      setProgress(0);
    }
  }, [location.pathname, cancelled]);

  useEffect(() => {
    if (cancelled) return;

    const start = performance.now() + delay;

    function tick(now: number) {
      const elapsed = now - start;
      if (elapsed < 0) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      const pct = Math.min(elapsed / NAV_DURATION, 1);
      setProgress(pct);
      if (pct < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        navigate(data.url);
      }
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [data.url, delay, navigate, cancelled]);

  const handleCancel = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    setCancelled(true);
    setProgress(0);
  }, []);

  return (
    <div className="space-y-3 px-1">
      <div className="flex items-center justify-between">
        <p
          className={cn(
            'text-sm',
            isJarvis ? 'text-white/50' : 'text-muted-foreground',
          )}
        >
          {cancelled ? (
            <span className={cn(isJarvis ? 'text-white/30' : 'text-muted-foreground/60')}>
              Navigation cancelled
            </span>
          ) : (
            <>
              Taking you to{' '}
              <span
                className={cn(
                  'font-medium',
                  isJarvis ? 'text-[#0A84FF]' : 'text-foreground',
                )}
              >
                {data.destination}
              </span>
              ...
            </>
          )}
        </p>
        {!cancelled && (
          <button
            onClick={handleCancel}
            className={cn(
              'text-xs font-medium px-2 py-0.5 rounded transition-colors shrink-0',
              isJarvis
                ? 'text-white/40 hover:text-white/70 hover:bg-white/5'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted',
            )}
          >
            Cancel
          </button>
        )}
      </div>

      {!cancelled && (
        <div
          className={cn(
            'h-0.5 rounded-full overflow-hidden',
            isJarvis ? 'bg-white/10' : 'bg-muted',
          )}
        >
          <div
            className={cn(
              'h-full rounded-full transition-none',
              isJarvis ? 'bg-[#0A84FF]' : 'bg-primary',
            )}
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      )}
    </div>
  );
}
