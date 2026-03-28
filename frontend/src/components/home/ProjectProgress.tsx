import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderKanban, FileText } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ProjectData {
  id: string;
  name: string;
  item_count: number;
  todo_open: number;
  todo_done: number;
  todo_total: number;
  active: number;
  sources: { email: number; voice: number; jira: number; confluence: number };
}

interface ProjectProgressProps {
  projects: ProjectData[];
}

const VISIBLE_LIMIT = 6;

function ProjectRow({ project }: { project: ProjectData }) {
  const { id, name, item_count, todo_open, todo_done, todo_total } = project;
  const pct = todo_total > 0 ? Math.round((todo_done / todo_total) * 100) : 0;

  return (
    <div className="space-y-1.5">
      <Link
        to={`/projects/${id}`}
        className="text-sm font-semibold text-foreground hover:underline"
      >
        {name}
      </Link>

      {/* Progress bar */}
      <div className="h-2 w-full rounded-full bg-muted/30">
        {todo_total > 0 ? (
          <div
            className="h-2 rounded-full bg-accent transition-[width]"
            style={{ width: `${pct}%` }}
          />
        ) : null}
      </div>

      {/* Stats line */}
      <p className="font-mono text-xs text-muted-foreground">
        {todo_total > 0 ? (
          <>
            {todo_done}/{todo_total}
            {'  '}
            {todo_open} active
            {'  '}
            {item_count}
            <FileText className="ml-1 inline-block h-3 w-3 align-text-bottom" />
          </>
        ) : (
          <>
            no todos
            {'  '}
            {item_count}
            <FileText className="ml-1 inline-block h-3 w-3 align-text-bottom" />
          </>
        )}
      </p>
    </div>
  );
}

export function ProjectProgress({ projects }: ProjectProgressProps) {
  const [expanded, setExpanded] = useState(false);

  if (projects.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="mb-3 flex items-center gap-2">
          <FolderKanban className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">
            Project Progress
          </h2>
        </div>
        <p className="text-sm text-muted-foreground">
          No projects yet. Ingest content to create your first project.
        </p>
      </div>
    );
  }

  // Sort by todo_open descending (most active first)
  const sorted = [...projects].sort((a, b) => b.todo_open - a.todo_open);

  // Split into visible and quiet
  const isQuiet = (p: ProjectData) => p.todo_total === 0 && p.item_count === 0;
  const activeProjects = sorted.filter((p) => !isQuiet(p));
  const quietProjects = sorted.filter(isQuiet);

  const needsCollapse = activeProjects.length > VISIBLE_LIMIT;
  const visible = needsCollapse && !expanded
    ? activeProjects.slice(0, VISIBLE_LIMIT)
    : activeProjects;
  const hiddenCount = needsCollapse
    ? activeProjects.length - VISIBLE_LIMIT + quietProjects.length
    : quietProjects.length;

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      {/* Header */}
      <div className="mb-4 flex items-center gap-2">
        <FolderKanban className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold text-foreground">
          Project Progress
        </h2>
        <span className="rounded-full bg-muted/40 px-2 py-0.5 text-xs text-muted-foreground">
          {projects.length}
        </span>
      </div>

      {/* Project rows */}
      <div className="space-y-4">
        {visible.map((p) => (
          <ProjectRow key={p.id} project={p} />
        ))}

        {expanded &&
          quietProjects.map((p) => (
            <ProjectRow key={p.id} project={p} />
          ))}
      </div>

      {/* Quiet / collapsed toggle */}
      {!expanded && hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="mt-4 text-xs text-muted-foreground hover:text-foreground"
        >
          +{hiddenCount} quiet project{hiddenCount !== 1 ? 's' : ''}
        </button>
      )}

      {expanded && hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(false)}
          className="mt-4 text-xs text-muted-foreground hover:text-foreground"
        >
          Show less
        </button>
      )}
    </div>
  );
}
