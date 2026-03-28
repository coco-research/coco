import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const start = performance.now() + delay;
    let raf: number;

    function tick(now: number) {
      const elapsed = now - start;
      if (elapsed < 0) {
        raf = requestAnimationFrame(tick);
        return;
      }
      const pct = Math.min(elapsed / NAV_DURATION, 1);
      setProgress(pct);
      if (pct < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        navigate(data.url);
      }
    }

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [data.url, delay, navigate]);

  return (
    <div className="space-y-3 px-1">
      <p
        className={cn(
          'text-sm',
          isJarvis ? 'text-white/50' : 'text-muted-foreground',
        )}
      >
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
      </p>

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
    </div>
  );
}
