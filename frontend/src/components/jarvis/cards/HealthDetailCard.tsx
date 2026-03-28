import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { cn } from '../../../lib/utils';
import { apiPost } from '../../../lib/api';
import { HealthRing } from '../HealthRing';
import type { HealthDetailData } from '../../../types/cards';

interface HealthDetailCardProps {
  data: HealthDetailData;
  variant?: 'jarvis' | 'light';
  delay?: number;
}

function statusDotColor(status: string, staleHours: number | null): string {
  if (staleHours != null) {
    if (staleHours < 12) return 'bg-[#34C759]';
    if (staleHours < 24) return 'bg-[#FF9F0A]';
    return 'bg-[#FF453A]';
  }
  const map: Record<string, string> = {
    green: 'bg-[#34C759]',
    ok: 'bg-[#34C759]',
    yellow: 'bg-[#FF9F0A]',
    warn: 'bg-[#FF9F0A]',
    red: 'bg-[#FF453A]',
    critical: 'bg-[#FF453A]',
  };
  return map[status] ?? 'bg-white/30';
}

export function HealthDetailCard({
  data,
  variant = 'jarvis',
  delay = 0,
}: HealthDetailCardProps) {
  const isJarvis = variant === 'jarvis';
  const qc = useQueryClient();
  const [processing, setProcessing] = useState(false);

  const runProcess = async () => {
    setProcessing(true);
    try {
      await apiPost('/home/process', {});
      qc.invalidateQueries({ queryKey: ['home'] });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <HealthRing sources={data.sources} size={100} delay={delay} />

      <ul className="w-full space-y-2">
        {data.sources.map((src) => (
          <li
            key={src.source}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm',
              isJarvis ? 'bg-white/5' : 'bg-muted/40',
            )}
          >
            <span
              className={cn(
                'w-2 h-2 rounded-full flex-shrink-0',
                statusDotColor(src.status, src.stale_hours),
              )}
            />
            <span
              className={cn(
                'flex-1 font-medium capitalize',
                isJarvis ? 'text-white/90' : 'text-foreground',
              )}
            >
              {src.source}
            </span>
            {src.stale_hours != null && (
              <span
                className={cn(
                  'text-[10px] font-mono',
                  isJarvis ? 'text-white/40' : 'text-muted-foreground',
                )}
              >
                {src.stale_hours < 1
                  ? '<1h'
                  : `${Math.round(src.stale_hours)}h`}{' '}
                ago
              </span>
            )}
            <span
              className={cn(
                'text-[10px] uppercase tracking-wider',
                isJarvis ? 'text-white/30' : 'text-muted-foreground',
              )}
            >
              {src.status}
            </span>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={runProcess}
        disabled={processing}
        className={cn(
          'w-full py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors',
          isJarvis
            ? 'bg-[#0A84FF] text-white hover:bg-[#0A84FF]/80 rounded-lg disabled:opacity-40'
            : 'bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 disabled:opacity-40',
        )}
      >
        {processing ? 'Processing...' : 'Run Process'}
      </button>
    </div>
  );
}
