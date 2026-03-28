import { Link } from 'react-router-dom';
import { cn } from '../../../lib/utils';
import { useCountUp } from '../../../hooks/useCountUp';
import type { ProjectDetailData } from '../../../types/cards';

interface ProjectDetailCardProps {
  data: ProjectDetailData;
  variant?: 'jarvis' | 'light';
  delay?: number;
}

interface StatTileProps {
  label: string;
  value: number;
  isJarvis: boolean;
  delay: number;
}

function StatTile({ label, value, isJarvis, delay }: StatTileProps) {
  const display = useCountUp(value, 1200, { delay });

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg p-3',
        isJarvis ? 'bg-white/5' : 'bg-muted/50',
      )}
    >
      <span
        className={cn(
          'text-2xl font-mono font-bold',
          isJarvis ? 'text-white/90' : 'text-foreground',
        )}
      >
        {display}
      </span>
      <span
        className={cn(
          'text-[10px] uppercase tracking-wider mt-1',
          isJarvis ? 'text-white/40' : 'text-muted-foreground',
        )}
      >
        {label}
      </span>
    </div>
  );
}

export function ProjectDetailCard({
  data,
  variant = 'jarvis',
  delay = 0,
}: ProjectDetailCardProps) {
  const isJarvis = variant === 'jarvis';

  const stats = [
    { label: 'Emails', value: data.email_count },
    { label: 'Jira Items', value: data.jira_count },
    { label: 'Open Todos', value: data.todo_open },
    { label: 'Done Todos', value: data.todo_done },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3
          className={cn(
            'text-sm font-semibold tracking-wide uppercase',
            isJarvis ? 'text-[#0A84FF]' : 'text-foreground',
          )}
        >
          {data.name}
        </h3>
        <Link
          to={`/projects/${data.id}`}
          className={cn(
            'text-[10px] uppercase tracking-wider hover:underline',
            isJarvis ? 'text-white/40 hover:text-[#0A84FF]' : 'text-muted-foreground hover:text-foreground',
          )}
        >
          View
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {stats.map((s, i) => (
          <StatTile
            key={s.label}
            label={s.label}
            value={s.value}
            isJarvis={isJarvis}
            delay={delay + i * 150}
          />
        ))}
      </div>
    </div>
  );
}
