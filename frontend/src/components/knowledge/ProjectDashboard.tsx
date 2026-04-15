import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader2, Users, FileText, CheckCircle2, Circle, Clock, AlertTriangle } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface DashboardStats {
  articles: number;
  decisions_total: number;
  decisions_pending: number;
  tasks_total: number;
  tasks_open: number;
  people: number;
}

interface DecisionItem {
  title: string;
  status: string;
  priority?: string;
  created_at?: string;
}

interface TaskItem {
  title: string;
  status: string;
  created_at?: string;
  due_date?: string;
}

interface PersonItem {
  gid: string;
  name: string;
}

interface ArticleItem {
  gid: string;
  title: string;
  confidence: number;
  updated_at: string;
}

interface ProjectDashboardData {
  slug: string;
  name: string;
  health: string;
  score: number;
  last_activity: string | null;
  stats: DashboardStats;
  recent_decisions: DecisionItem[];
  brain_decisions: { date: string; decision: string; decided_by: string }[];
  open_tasks: TaskItem[];
  brain_tasks: TaskItem[];
  key_people: PersonItem[];
  recent_articles: ArticleItem[];
  error?: string;
}

function healthBadge(health: string) {
  switch (health) {
    case 'green':
      return { bg: 'bg-green-100 dark:bg-green-950/30', text: 'text-green-700 dark:text-green-400', label: 'On Track' };
    case 'yellow':
      return { bg: 'bg-amber-100 dark:bg-amber-950/30', text: 'text-amber-700 dark:text-amber-400', label: 'Needs Attention' };
    case 'red':
      return { bg: 'bg-red-100 dark:bg-red-950/30', text: 'text-red-700 dark:text-red-400', label: 'At Risk' };
    default:
      return { bg: 'bg-muted', text: 'text-muted-foreground', label: '--' };
  }
}

function statusIcon(status: string) {
  switch (status) {
    case 'done':
    case 'resolved':
      return <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />;
    case 'in_progress':
      return <Clock className="h-3.5 w-3.5 text-blue-500" />;
    case 'pending':
      return <Circle className="h-3.5 w-3.5 text-amber-500" />;
    default:
      return <Circle className="h-3.5 w-3.5 text-muted-foreground" />;
  }
}

function formatDate(d: string | null | undefined): string {
  if (!d) return '';
  try {
    return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch { return d; }
}

interface ProjectDashboardProps {
  slug: string;
  onBack: () => void;
  onSelectPerson?: (gid: string) => void;
  onSelectArticle?: (gid: string) => void;
}

export function ProjectDashboard({ slug, onBack, onSelectPerson, onSelectArticle }: ProjectDashboardProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['project-dashboard', slug],
    queryFn: () => apiFetch<ProjectDashboardData>(`/knowledge/project/${encodeURIComponent(slug)}/dashboard`),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data || data.error) {
    return (
      <div className="p-4">
        <button onClick={onBack} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
        <p className="text-sm text-muted-foreground">Unable to load project dashboard.</p>
      </div>
    );
  }

  const hb = healthBadge(data.health);
  const allDecisions = [
    ...data.recent_decisions.map((d) => ({ title: d.title, status: d.status, date: d.created_at, author: null as string | null })),
    ...data.brain_decisions.map((d) => ({ title: d.decision, status: 'recorded', date: d.date, author: d.decided_by })),
  ];
  const allTasks = [...data.open_tasks, ...data.brain_tasks];
  const hasData = allDecisions.length > 0 || allTasks.length > 0;

  return (
    <div className="p-4 overflow-y-auto h-full space-y-5">
      {/* Back */}
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{data.name || slug}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {data.last_activity ? `Last activity: ${formatDate(data.last_activity)}` : 'No recent activity'}
            {' \u00B7 '}{data.stats.articles} articles
          </p>
        </div>
        <span className={cn('px-2.5 py-1 rounded-md text-xs font-medium', hb.bg, hb.text)}>
          {hb.label}
        </span>
      </div>

      {/* Stat cards — de-emphasize zeros */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Decisions', value: data.stats.decisions_total, sub: data.stats.decisions_pending > 0 ? `${data.stats.decisions_pending} pending` : undefined },
          { label: 'Tasks', value: data.stats.tasks_total, sub: data.stats.tasks_open > 0 ? `${data.stats.tasks_open} open` : undefined },
          { label: 'People', value: data.stats.people },
          { label: 'Articles', value: data.stats.articles },
        ].map((s) => {
          const isEmpty = s.value === 0;
          return (
            <div key={s.label} className={cn(
              'rounded-lg px-4 py-3 border',
              isEmpty ? 'border-border/50 bg-card/50' : 'border-border bg-card',
            )}>
              <div className={cn('text-xl font-bold', isEmpty ? 'text-muted-foreground/40' : 'text-foreground')}>{s.value}</div>
              <div className={cn('text-xs', isEmpty ? 'text-muted-foreground/40' : 'text-muted-foreground')}>{s.label}</div>
              {s.sub && <div className="text-[11px] text-muted-foreground/70">{s.sub}</div>}
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {!hasData && (
        <div className="bg-card border border-border rounded-lg p-6 text-center">
          <AlertTriangle className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">No decisions or action items tracked yet.</p>
          <p className="text-xs text-muted-foreground/70 mt-1">
            Ask CoCo to extract decisions from recent emails:
          </p>
          <p className="text-xs text-accent mt-1 font-mono">
            "Extract decisions from {slug} emails this week"
          </p>
        </div>
      )}

      {/* Content grid */}
      {hasData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Decisions */}
          {allDecisions.length > 0 && (
            <div className="bg-card border border-border rounded-lg">
              <div className="px-4 py-2.5 border-b border-border">
                <h3 className="text-sm font-semibold text-foreground">Recent Decisions</h3>
              </div>
              <div className="divide-y divide-border">
                {allDecisions.slice(0, 8).map((d) => (
                  <div key={`${d.date}-${d.title}`} className="px-4 py-2.5 flex items-start gap-2">
                    {statusIcon(d.status)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground truncate">{d.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDate(d.date)}
                        {d.author && ` \u2014 ${d.author}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Open Tasks */}
          {allTasks.length > 0 && (
            <div className="bg-card border border-border rounded-lg">
              <div className="px-4 py-2.5 border-b border-border">
                <h3 className="text-sm font-semibold text-foreground">Open Tasks</h3>
              </div>
              <div className="divide-y divide-border">
                {allTasks.slice(0, 8).map((t) => (
                  <div key={`${t.status}-${t.title}`} className="px-4 py-2.5 flex items-start gap-2">
                    {statusIcon(t.status)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground truncate">{t.title}</p>
                      {t.due_date && (
                        <p className="text-xs text-muted-foreground">Due: {formatDate(t.due_date)}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Key People */}
      {data.key_people.length > 0 && (
        <div className="bg-card border border-border rounded-lg">
          <div className="px-4 py-2.5 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground">Key People ({data.key_people.length})</h3>
          </div>
          <div className="px-4 py-3 flex flex-wrap gap-2">
            {data.key_people.map((p) => (
              <button
                key={p.gid}
                onClick={() => onSelectPerson?.(p.gid)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-muted/50 rounded-md text-sm hover:bg-muted transition-colors"
              >
                <Users className="h-3 w-3 text-muted-foreground" />
                {p.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Recent Articles */}
      {data.recent_articles.length > 0 && (
        <div className="bg-card border border-border rounded-lg">
          <div className="px-4 py-2.5 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground">Recent Articles</h3>
          </div>
          <div className="divide-y divide-border">
            {data.recent_articles.slice(0, 6).map((a) => (
              <button
                key={a.gid}
                onClick={() => onSelectArticle?.(a.gid)}
                className="px-4 py-2.5 w-full text-left flex items-center justify-between hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="text-sm text-foreground truncate">{a.title}</span>
                </div>
                <span className={cn(
                  'text-xs font-mono shrink-0 ml-2',
                  a.confidence >= 0.95 ? 'text-green-600' : a.confidence >= 0.85 ? 'text-foreground' : 'text-amber-600',
                )}>
                  {(a.confidence * 100).toFixed(0)}%
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
