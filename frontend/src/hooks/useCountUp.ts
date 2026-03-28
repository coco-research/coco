import { useEffect, useRef, useState } from 'react';

export function useCountUp(
  end: number,
  duration = 1500,
  options?: { start?: number; decimals?: number; enabled?: boolean; delay?: number }
) {
  const { start = 0, decimals = 0, enabled = true, delay = 0 } = options ?? {};
  const [value, setValue] = useState(start);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (!enabled) { setValue(start); return; }

    const delayTimeout = setTimeout(() => {
      const startTime = performance.now();
      const delta = end - start;

      function tick(now: number) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // easeOutExpo
        const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        setValue(start + delta * eased);

        if (progress < 1) {
          rafRef.current = requestAnimationFrame(tick);
        }
      }

      rafRef.current = requestAnimationFrame(tick);
    }, delay);

    return () => {
      clearTimeout(delayTimeout);
      cancelAnimationFrame(rafRef.current);
    };
  }, [end, duration, start, enabled, delay]);

  return decimals > 0 ? parseFloat(value.toFixed(decimals)) : Math.round(value);
}
