import { cn } from '../../../lib/utils';
import { useTypewriter } from '../../../hooks/useTypewriter';
import type { TextResponseData } from '../../../types/cards';

interface TextResponseCardProps {
  data: TextResponseData;
  variant?: 'jarvis' | 'light';
  delay?: number;
}

export function TextResponseCard({
  data,
  variant = 'jarvis',
  delay = 0,
}: TextResponseCardProps) {
  const isJarvis = variant === 'jarvis';
  const { displayed, isDone } = useTypewriter(data.text, 30, {
    enabled: isJarvis,
    delay,
  });

  const text = isJarvis ? displayed : data.text;

  return (
    <div className="px-1">
      <p
        className={cn(
          'text-sm leading-relaxed whitespace-pre-wrap',
          isJarvis ? 'text-white/70' : 'text-foreground',
        )}
      >
        {text}
        {isJarvis && !isDone && (
          <span className="inline-block w-0.5 h-4 ml-0.5 bg-white/40 animate-pulse align-text-bottom" />
        )}
      </p>
    </div>
  );
}
