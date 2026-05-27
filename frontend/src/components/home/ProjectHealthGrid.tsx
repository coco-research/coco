import { useState } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { Mail, Mic, Ticket, FileText, ListTodo, CheckCircle2 } from 'lucide-react';
import type { HomeProject } from '../../types/home';

interface ProjectHealthGridProps {
  projects: HomeProject[];
}

type HealthStatus = 'green' | 'amber' | 'red' | 'gray';

function getHealth(project: HomeProject): { status: HealthStatus; label?: string } {
  if (project.active === 0) return { status: 'gray', label: 'Inactive' };
  if (project.todo_open >= 15) return { status: 'red', label: 'Heavy load' };
  if (project.todo_open >= 8) return { status: 'amber', label: 'Busy' };
  if (project.todo_open === 0 && project.todo_total > 0) return { status: 'green', label: 'On track' };
  return { status: 'green' };
}

function isQuiet(project: HomeProject): boolean {
  return project.todo_total === 0 && project.item_count === 0;
}

const statusBorderColors: Record<HealthStatus, string> = {
  green: 'border-l-success/50',
  amber: 'border-l-warning',
  red: 'border-l-destructive',
  gray: 'border-l-muted-foreground/20',
};

function SourcePill({ icon: Icon, count, label }: { icon: React.ElementType; count: number; label: string }) {
  if (count === 0) return null;
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground/70" title={`${count} ${label}`}>
      <Icon className="h-2.5 w-2.5" />
      {count}
    </span>
  );
}

function ProjectCard({ project }: { project: HomeProject }) {
  const health = getHealth(project);
  const pct = project.todo_total > 0
    ? Math.round((project.todo_done / project.todo_total) * 100)
    : 0;
  const totalSources = project.sources.email + project.sources.voice + project.sources.jira + project.sources.confluence;

  return (
    <Link
      to={`/projects/${project.id}`}
      className={cn(
        'rounded-lg border border-border/60 border-l-[3px] bg-card p-5 hover:bg-accent/5 transition-all hover:shadow-sm block',
        statusBorderColors[health.status],
      )}
    >
      {/* Row 1: Name + status badge */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-sm font-medium text-foreground truncate leading-tight flex-1">
          {project.name}
        </h3>
        {health.label && (
          <span className={cn(
            'text-[10px] font-medium px-1.5 py-0.5 rounded shrink-0',
            health.status === 'green' && 'bg-success/10 text-success',
            health.status === 'amber' && 'bg-warning/10 text-warning',
            health.status === 'red' && 'bg-destructive/10 text-destructive',
            health.status === 'gray' && 'bg-muted/40 text-muted-foreground',
          )}>
            {health.label}
          </span>
        )}
      </div>

      {/* Row 2: Todo stats */}
      <div className="flex items-center gap-3 mb-2.5">
        <div className="flex items-center gap-1 text-xs text-foreground">
          <ListTodo className="h-3 w-3 text-muted-foreground" />
          <span className="font-medium">{project.todo_open}</span>
          <span className="text-muted-foreground">open</span>
        </div>
        {project.todo_done > 0 && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <CheckCircle2 className="h-3 w-3 text-success/60" />
            <span>{project.todo_done} done</span>
          </div>
        )}
      </div>

      {/* Row 3: Progress bar (only when there's actual progress) */}
      {project.todo_done > 0 && project.todo_total > 0 && (
        <div className="mb-2.5">
          <div className="h-1.5 w-full rounded-full bg-muted/30">
            <div
              className={cn(
                'h-1.5 rounded-full transition-[width] duration-500',
                health.status === 'red' ? 'bg-destructive/60' :
                health.status === 'amber' ? 'bg-warning/60' :
                'bg-success/60',
              )}
              style={{ width: `${Math.max(pct, 2)}%` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-muted-foreground/60">
              {project.todo_done}/{project.todo_total} complete
            </span>
            <span className="text-[10px] text-muted-foreground/60 font-mono">
              {pct}%
            </span>
          </div>
        </div>
      )}

      {/* Fallback for empty cards */}
      {project.todo_total === 0 && totalSources === 0 && (
        <p className="text-[11px] text-muted-foreground/50 italic">No activity yet</p>
      )}

      {/* Row 4: Source breakdown */}
      {totalSources > 0 && (
        <div className="flex items-center gap-3 pt-2 border-t border-border/20">
          <SourcePill icon={Mail} count={project.sources.email} label="emails" />
          <SourcePill icon={Mic} count={project.sources.voice} label="voice memos" />
          <SourcePill icon={Ticket} count={project.sources.jira} label="Jira tickets" />
          <SourcePill icon={FileText} count={project.sources.confluence} label="Confluence pages" />
        </div>
      )}
    </Link>
  );
}

export function ProjectHealthGrid({ projects }: ProjectHealthGridProps) {
  const [expanded, setExpanded] = useState(false);

  if (projects.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Projects
        </span>
        <p className="mt-3 text-sm text-muted-foreground">No projects yet.</p>
      </div>
    );
  }

  const activeProjects = projects.filter((p) => !isQuiet(p));
  const quietProjects = projects.filter((p) => isQuiet(p));

  const sorted = [...activeProjects].sort((a, b) => {
    const weight: Record<HealthStatus, number> = { red: 0, amber: 1, green: 2, gray: 3 };
    const aW = weight[getHealth(a).status];
    const bW = weight[getHealth(b).status];
    if (aW !== bW) return aW - bW;
    return b.todo_open - a.todo_open;
  });

  // Show all active projects by default (column is scrollable); only collapse quiet ones
  const visible = expanded ? [...sorted, ...quietProjects] : sorted;
  const totalHidden = quietProjects.length;

  return (
    <div>
      {/* Sticky header */}
      <div className="flex items-center justify-between mb-4 lg:sticky lg:top-0 lg:bg-background lg:py-2 lg:z-10">
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Projects
          </span>
          <span className="text-[11px] text-muted-foreground/60">
            {activeProjects.length} active
          </span>
        </div>
        <Link
          to="/projects"
          className="text-xs text-accent-foreground hover:text-foreground transition-colors"
        >
          View All
        </Link>
      </div>

      {/* Single-column list of cards */}
      <div className="space-y-3">
        {visible.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>

      {/* Overflow */}
      {!expanded && totalHidden > 0 && (
        <button
          onClick={() => setExpanded(true)}
          className="mt-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          +{totalHidden} more project{totalHidden !== 1 ? 's' : ''}
        </button>
      )}
      {expanded && totalHidden > 0 && (
        <button
          onClick={() => setExpanded(false)}
          className="mt-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Show less
        </button>
      )}
    </div>
  );
}
