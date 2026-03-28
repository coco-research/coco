import { Link } from 'react-router-dom';
import { FileText } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ProjectCardProps {
  id: string;
  name: string;
  active?: number;
  item_count?: number;
  jira_key?: string | null;
}

const borderColor: Record<string, string> = {
  healthy: 'border-l-success',
  warning: 'border-l-warning',
  error: 'border-l-error',
  unknown: 'border-l-border-strong',
};

function healthStatus(active?: number): string {
  if (active === undefined) return 'unknown';
  return active ? 'healthy' : 'warning';
}

export function ProjectCard({ id, name, active, item_count, jira_key }: ProjectCardProps) {
  const status = healthStatus(active);

  return (
    <Link
      to={`/projects/${id}/todos`}
      className={cn(
        'rounded-xl border border-border border-l-[3px] bg-card p-5 hover:shadow-md transition-all block',
        borderColor[status],
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-foreground truncate">{name}</h3>
          {jira_key && (
            <span className="text-xs text-muted-foreground font-mono">{jira_key}</span>
          )}
        </div>
        <span className={cn(
          'px-2 py-0.5 rounded-full text-[11px] font-medium uppercase tracking-wide shrink-0',
          active ? 'bg-success/20 text-success' : 'bg-accent/50 text-muted-foreground'
        )}>
          {active ? 'Active' : 'Inactive'}
        </span>
      </div>

      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <FileText size={13} />
          {item_count ?? 0} items
        </span>
      </div>
    </Link>
  );
}
