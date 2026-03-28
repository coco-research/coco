import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Returns a ref to attach to an element and a boolean indicating
 * whether the element has been visible in the viewport for at least
 * `delayMs` milliseconds continuously.
 */
export function useInViewport(delayMs = 2000): [React.RefObject<HTMLDivElement | null>, boolean] {
  const ref = useRef<HTMLDivElement | null>(null);
  const [hasBeenVisible, setHasBeenVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (hasBeenVisible) return; // Already triggered, no need to observe

    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          timerRef.current = setTimeout(() => {
            setHasBeenVisible(true);
          }, delayMs);
        } else {
          clearTimer();
        }
      },
      { threshold: 0.5 },
    );

    observer.observe(el);
    return () => {
      observer.disconnect();
      clearTimer();
    };
  }, [delayMs, hasBeenVisible, clearTimer]);

  return [ref, hasBeenVisible];
}
