import { cn } from '../../../lib/utils';
import { useCountUp } from '../../../hooks/useCountUp';
import type { MetricGridData, MetricItem } from '../../../types/cards';

interface MetricGridCardProps {
  data: MetricGridData;
  variant?: 'jarvis' | 'light';
  delay?: number;
}

interface MetricTileProps {
  metric: MetricItem;
  isJarvis: boolean;
  delay: number;
}

function MetricTile({ metric, isJarvis, delay }: MetricTileProps) {
  const display = useCountUp(metric.value, 1200, { delay });
  const color = metric.color ?? undefined;

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg p-4',
        isJarvis ? 'bg-white/5' : 'bg-muted/50',
      )}
    >
      <span
        className={cn(
          'text-3xl font-mono font-bold',
          !color && (isJarvis ? 'text-white/90' : 'text-foreground'),
        )}
        style={
          color
            ? { color }
            : undefined
        }
      >
        {display}
      </span>
      <span
        className={cn(
          'text-[10px] uppercase tracking-wider mt-1',
          isJarvis ? 'text-white/40' : 'text-muted-foreground',
        )}
      >
        {metric.label}
      </span>
    </div>
  );
}

export function MetricGridCard({
  data,
  variant = 'jarvis',
  delay = 0,
}: MetricGridCardProps) {
  const isJarvis = variant === 'jarvis';
  const cols = data.metrics.length <= 2 ? 'grid-cols-2' : 'grid-cols-2';

  return (
    <div className={cn('grid gap-2', cols)}>
      {data.metrics.map((m, i) => (
        <MetricTile
          key={m.label}
          metric={m}
          isJarvis={isJarvis}
          delay={delay + i * 150}
        />
      ))}
    </div>
  );
}
