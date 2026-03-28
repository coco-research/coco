import { useState, useEffect, useRef } from 'react';

export function useTypewriter(
  text: string,
  speed = 35,
  options?: { enabled?: boolean; delay?: number; onComplete?: () => void }
) {
  const { enabled = true, delay = 0, onComplete } = options ?? {};
  const [displayed, setDisplayed] = useState('');
  const [isDone, setIsDone] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (!enabled || !text) return;
    setDisplayed('');
    setIsDone(false);

    let i = 0;
    let timeout: ReturnType<typeof setTimeout>;

    const startTyping = () => {
      const tick = () => {
        if (i < text.length) {
          i++;
          setDisplayed(text.slice(0, i));
          timeout = setTimeout(tick, speed);
        } else {
          setIsDone(true);
          onCompleteRef.current?.();
        }
      };
      tick();
    };

    timeout = setTimeout(startTyping, delay);
    return () => clearTimeout(timeout);
  }, [text, speed, enabled, delay]);

  return { displayed, isDone };
}
