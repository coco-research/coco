import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, BookOpen, CheckSquare, Clock, Inbox, Zap, Calendar, Bell, GitMerge, RefreshCw } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn, timeAgo } from '../lib/utils';
import { Link } from 'react-router-dom';

// ─── Types ────────────────────────────────────────────────────────────────────

interface HotProject {
  slug: string;
  description: string;
  decisions: number;
  events: number;
  last_activity: string;
}

interface ActionByProject {
  project: string;
  cnt: number;
}

interface RecentDecision {
  text: string;
  project: string;
  date: string;
  status?: string;
}

interface Deadline {
  id: number;
  text: string;
  extracted_date: string;
  project_slug: string;
  source_email: string;
  days_until: number;
  formatted: string;
}

interface BriefingData {
  hours_lookback: number;
  generated_at: string;
  cutoff: string;
  knowledge: { total_articles: number; total_entities: number; total_connections: number; new_articles: number };
  decision_queue: { pending_count: number; top_items: { text: string; project: string }[] };
  action_items: { total_open: number; project_count: number; by_project: ActionByProject[]; high_priority: number };
  hot_projects: HotProject[];
  recent_decisions: RecentDecision[];
  cron_results: null | Record<string, unknown>;
  email_digest: { total: number; by_project: ActionByProject[]; action_items: number; urgent: number };
  pending_todos: { total: number; items: { title: string; project: string; due_date?: string }[] };
  pending_decisions_auto: { total: number; items: { text: string; project: string }[] };
  upcoming_deadlines: Deadline[];
  silence_alerts: string[];
  contradiction_alerts: string[];
  error?: string;
}

// ─── Section wrapper ──────────────────────────────────────────────────────────

function Section({ title, icon: Icon, count, children, accent }: {
  title: string;
  icon: React.ElementType;
  count?: number;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <div className={cn('rounded-xl border border-border bg-card overflow-hidden', accent && `border-l-2 ${accent}`)}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/20">
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-muted-foreground" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</span>
        </div>
        {count !== undefined && (
          <span className="text-xs font-medium text-foreground bg-muted px-2 py-0.5 rounded-full">{count}</span>
        )}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function EmptyState({ msg }: { msg: string }) {
  return <p className="text-xs text-muted-foreground italic">{msg}</p>;
}

function Tag({ text, variant = 'default' }: { text: string; variant?: 'default' | 'warn' | 'danger' | 'success' }) {
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium',
      variant === 'warn' && 'bg-warning/15 text-warning',
      variant === 'danger' && 'bg-destructive/15 text-destructive',
      variant === 'success' && 'bg-success/15 text-success',
      variant === 'default' && 'bg-muted text-muted-foreground',
    )}>
      {text}
    </span>
  );
}

// ─── BriefingPage ─────────────────────────────────────────────────────────────

export default function BriefingPage() {
  const { data, isLoading, isError, refetch } = useQuery<BriefingData>({
    queryKey: ['morning-briefing'],
    queryFn: () => apiFetch<BriefingData>('/briefing'),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-muted/40 animate-pulse" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle size={36} className="text-destructive mb-3" />
        <p className="text-sm text-foreground font-medium mb-1">Could not load briefing</p>
        <p className="text-xs text-muted-foreground">Check that the backend is running.</p>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Bell size={36} className="text-muted-foreground mb-3" />
        <p className="text-sm text-muted-foreground">{data.error}</p>
      </div>
    );
  }

  // Safe defaults — API may return partial data depending on what daemon has generated
  const knowledge = data.knowledge ?? { total_articles: 0, total_entities: 0, total_connections: 0, new_articles: 0 };
  const decision_queue = data.decision_queue ?? { pending_count: 0, top_items: [] };
  // API may return high_priority as number or array — widen to unknown for runtime branching.
  const rawAi = (data.action_items ?? {}) as Record<string, unknown>;
  const hp = rawAi.high_priority;
  const action_items = {
    total_open: (rawAi.total_open as number | undefined) ?? 0,
    project_count: (rawAi.project_count as number | undefined) ?? 0,
    by_project: Array.isArray(rawAi.by_project) ? rawAi.by_project as ActionByProject[] : [],
    high_priority: typeof hp === 'number' ? hp : Array.isArray(hp) ? hp.length : 0,
  };
  const rawEd = data.email_digest ?? {};
  const email_digest = {
    total: rawEd.total ?? 0,
    by_project: Array.isArray(rawEd.by_project) ? rawEd.by_project as ActionByProject[] : Object.entries(rawEd.by_project ?? {}).map(([project, cnt]) => ({ project, cnt: cnt as number })),
    action_items: rawEd.action_items ?? 0,
    urgent: rawEd.urgent ?? 0,
  };
  const hot_projects = data.hot_projects ?? [];
  const recent_decisions = data.recent_decisions ?? [];
  const pending_todos = data.pending_todos ?? { total: 0, items: [] };
  // pending_decisions_auto: reserved for future surface — not consumed in current UI
  void (data.pending_decisions_auto ?? { total: 0, items: [] });
  const upcoming_deadlines = data.upcoming_deadlines ?? [];
  const silence_alerts = data.silence_alerts ?? [];
  const contradiction_alerts = data.contradiction_alerts ?? [];

  const generatedAt = data.generated_at ? timeAgo(data.generated_at) : '—';
  const hoursLookback = data.hours_lookback ?? 24;

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-foreground">Morning Briefing</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Generated {generatedAt} · last {hoursLookback}h lookback
          </p>
        </div>
        <button
          onClick={() => void refetch()}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:border-foreground/20 transition-colors"
        >
          <RefreshCw size={12} />
          Refresh
        </button>
      </div>

      {/* 2-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Knowledge Stats */}
        <Section title="Knowledge" icon={BookOpen} accent="border-l-accent">
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              { label: 'Articles', value: knowledge.total_articles },
              { label: 'Entities', value: knowledge.total_entities },
              { label: 'Connections', value: knowledge.total_connections },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xl font-semibold text-foreground tabular-nums">{value.toLocaleString()}</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
              </div>
            ))}
          </div>
          {knowledge.new_articles > 0 && (
            <p className="text-xs text-success mt-3 font-medium">+{knowledge.new_articles} new articles generated</p>
          )}
        </Section>

        {/* Email Digest */}
        <Section title="Email Digest" icon={Inbox} count={email_digest.total} accent="border-l-info">
          {email_digest.total === 0 ? (
            <EmptyState msg="No new emails in the lookback window." />
          ) : (
            <div className="space-y-2">
              <div className="flex gap-3 text-xs text-muted-foreground">
                <span>{email_digest.action_items} action items</span>
                {email_digest.urgent > 0 && (
                  <Tag text={`${email_digest.urgent} urgent`} variant="danger" />
                )}
              </div>
              <div className="space-y-1">
                {email_digest.by_project.slice(0, 5).map((p) => (
                  <div key={p.project} className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground truncate">{p.project}</span>
                    <span className="font-medium text-foreground">{p.cnt}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Section>

        {/* Decision Queue */}
        <Section title="Decision Queue" icon={GitMerge} count={decision_queue.pending_count} accent="border-l-warning">
          {decision_queue.pending_count === 0 ? (
            <EmptyState msg="No pending decisions." />
          ) : (
            <div className="space-y-2">
              {decision_queue.top_items.slice(0, 4).map((item, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-[10px] text-muted-foreground font-mono mt-0.5">{i + 1}.</span>
                  <div className="min-w-0">
                    <p className="text-xs text-foreground leading-snug">{item.text}</p>
                    <Tag text={item.project} />
                  </div>
                </div>
              ))}
              {decision_queue.pending_count > 4 && (
                <Link to="/inbox" className="text-xs text-accent hover:underline">
                  +{decision_queue.pending_count - 4} more in inbox →
                </Link>
              )}
            </div>
          )}
        </Section>

        {/* Action Items */}
        <Section title="Action Items" icon={CheckSquare} count={action_items.total_open} accent="border-l-destructive">
          {action_items.total_open === 0 ? (
            <EmptyState msg="No open action items." />
          ) : (
            <div className="space-y-2">
              {action_items.high_priority > 0 && (
                <div className="flex items-center gap-2">
                  <Tag text={`${action_items.high_priority} high priority`} variant="danger" />
                  <span className="text-xs text-muted-foreground">across {action_items.project_count} projects</span>
                </div>
              )}
              <div className="space-y-1">
                {action_items.by_project.slice(0, 5).map((p) => (
                  <div key={p.project} className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground truncate">{p.project}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-accent rounded-full"
                          style={{ width: `${Math.min(100, (p.cnt / action_items.total_open) * 100 * 5)}%` }}
                        />
                      </div>
                      <span className="font-medium text-foreground w-6 text-right">{p.cnt}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Section>

        {/* Hot Projects */}
        <Section title="Hot Projects" icon={Zap} count={hot_projects.length} accent="border-l-success">
          {hot_projects.length === 0 ? (
            <EmptyState msg="No hot projects." />
          ) : (
            <div className="space-y-2">
              {hot_projects.slice(0, 5).map((p) => (
                <div key={p.slug} className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-foreground">{p.slug}</p>
                    <p className="text-[10px] text-muted-foreground truncate">{p.description}</p>
                  </div>
                  <div className="flex gap-2 shrink-0 text-[10px] text-muted-foreground">
                    <span>{p.decisions}d</span>
                    <span>{p.events}e</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Upcoming Deadlines */}
        <Section title="Upcoming Deadlines" icon={Calendar} count={upcoming_deadlines.length} accent="border-l-warning">
          {upcoming_deadlines.length === 0 ? (
            <EmptyState msg="No upcoming deadlines detected." />
          ) : (
            <div className="space-y-2">
              {upcoming_deadlines.map((d) => (
                <div key={d.id} className="text-xs">
                  <div className="flex items-center gap-2">
                    <Tag
                      text={d.days_until <= 1 ? 'today' : `${d.days_until}d`}
                      variant={d.days_until <= 1 ? 'danger' : d.days_until <= 3 ? 'warn' : 'default'}
                    />
                    <span className="text-foreground font-medium">{d.extracted_date}</span>
                    <span className="text-muted-foreground">{d.project_slug}</span>
                  </div>
                  <p className="text-muted-foreground mt-0.5 truncate">{d.source_email}</p>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Recent Decisions */}
        <Section title="Recent Decisions" icon={GitMerge} count={recent_decisions.length}>
          {recent_decisions.length === 0 ? (
            <EmptyState msg="No recent decisions." />
          ) : (
            <div className="space-y-2">
              {recent_decisions.slice(0, 5).map((d, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-foreground leading-snug">{(d as unknown as Record<string, string>).text ?? (d as unknown as Record<string, string>).decision ?? ''}</p>
                    <div className="flex gap-2 mt-0.5">
                      <Tag text={d.project} />
                      {d.date && <span className="text-[10px] text-muted-foreground">{d.date.slice(0, 10)}</span>}
                    </div>
                  </div>
                </div>
              ))}
              {recent_decisions.length > 5 && (
                <p className="text-[10px] text-muted-foreground">+{recent_decisions.length - 5} more</p>
              )}
            </div>
          )}
        </Section>

        {/* Pending Todos */}
        <Section title="Pending Todos" icon={Clock} count={pending_todos.total}>
          {pending_todos.total === 0 ? (
            <EmptyState msg="No pending todos." />
          ) : (
            <div className="space-y-1.5">
              {pending_todos.items.slice(0, 5).map((t, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className="text-muted-foreground mt-0.5">•</span>
                  <div className="min-w-0">
                    <span className="text-foreground">{t.title}</span>
                    {t.due_date && <Tag text={`due ${t.due_date}`} variant="warn" />}
                    <Tag text={t.project} />
                  </div>
                </div>
              ))}
              {pending_todos.total > 5 && (
                <Link to="/todos" className="text-xs text-accent hover:underline">
                  +{pending_todos.total - 5} more in todos →
                </Link>
              )}
            </div>
          )}
        </Section>

        {/* Silence Alerts */}
        {silence_alerts.length > 0 && (
          <Section title="Silence Alerts" icon={Bell} count={silence_alerts.length} accent="border-l-warning">
            <div className="space-y-1.5">
              {silence_alerts.map((alert, i) => (
                <p key={i} className="text-xs text-muted-foreground leading-snug">{alert}</p>
              ))}
            </div>
          </Section>
        )}

        {/* Contradiction Alerts */}
        {contradiction_alerts.length > 0 && (
          <Section title="Contradiction Alerts" icon={AlertTriangle} count={contradiction_alerts.length} accent="border-l-destructive">
            <div className="space-y-1.5">
              {contradiction_alerts.map((alert, i) => (
                <p key={i} className="text-xs text-muted-foreground leading-snug">
                  {typeof alert === 'string' ? alert : (alert as Record<string, unknown>).display as string ?? JSON.stringify(alert)}
                </p>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}
