import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FolderKanban, Radio, Inbox, DollarSign, AlertTriangle, ArrowRight, Layers } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { ProjectCard } from '../components/dashboard/ProjectCard';
import { ActivityFeed } from '../components/dashboard/ActivityFeed';
import { CostSummary } from '../components/dashboard/CostSummary';
import { HealthBar } from '../components/dashboard/HealthBar';
import { formatCost, cn, timeAgo } from '../lib/utils';
import { useScope } from '../context/ScopeContext';

interface DashboardProject {
  id: string;
  name: string;
  jira_key?: string | null;
  active?: number;
  item_count?: number;
}

interface HealthSource {
  source_name?: string;
  source?: string;
  status?: string;
  last_success?: string | null;
  last_failure?: string | null;
  last_sync?: string | null;
  items_synced?: number;
  item_count?: number;
  error_message?: string | null;
}

interface DashboardData {
  projects: DashboardProject[];
  agents: { running: number; paused: number; idle: number; total: number };
  queue: { total: number; urgent: number; drafts: number; classify: number };
  costs: { today_usd: number; month_usd: number; daily?: number[] };
  health: HealthSource[];
  unsorted_count: number;
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="h-12 rounded-lg bg-muted/50 animate-pulse" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 rounded-lg bg-muted/50 animate-pulse" />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-28 rounded-lg bg-muted/50 animate-pulse" />
        ))}
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  to?: string;
  alert?: boolean;
}

function MetricCard({ icon: Icon, label, value, sub, to, alert }: MetricCardProps) {
  const content = (
    <div className={cn(
      'bg-card border border-border rounded-lg p-4 hover:bg-accent/30 transition-all hover:scale-[1.01]',
      alert && 'border-destructive/30 bg-destructive/5'
    )}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold text-foreground mt-1 tabular-nums">{value}</p>
          {sub && <p className="text-[10px] text-muted-foreground mt-0.5">{sub}</p>}
        </div>
        <Icon size={18} className={cn('text-muted-foreground', alert && 'text-destructive')} />
      </div>
    </div>
  );
  return to ? <Link to={to}>{content}</Link> : content;
}

interface ActivityRow {
  action?: string;
  item_type?: string;
  item_id?: string;
  created_at?: string;
  project_id?: string;
}

export default function DashboardPage() {
  const { selectedNodeId, selectedNode, scopeProjectIds } = useScope();

  const dashboardUrl = selectedNodeId
    ? `/dashboard?node_id=${encodeURIComponent(selectedNodeId)}`
    : '/dashboard';

  const { data: dashboard, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard', selectedNodeId],
    queryFn: () => apiFetch<DashboardData>(dashboardUrl),
    refetchInterval: 30000,
  });

  const activityUrl = selectedNodeId
    ? `/activity?limit=10&node_id=${encodeURIComponent(selectedNodeId)}`
    : '/activity?limit=10';

  const { data: activityRows } = useQuery<ActivityRow[]>({
    queryKey: ['activity', 'dashboard', selectedNodeId],
    queryFn: () => apiFetch<ActivityRow[]>(activityUrl),
    refetchInterval: 30000,
  });

  const activityEvents = (activityRows ?? []).map((row) => ({
    ts: row.created_at ? timeAgo(row.created_at) : '',
    description: [row.action, row.item_type, row.item_id].filter(Boolean).join(' '),
    project: row.project_id ?? undefined,
  }));

  if (isLoading || !dashboard) return <LoadingState />;

  const { projects, agents, queue, costs, health } = dashboard;
  // queue.total = open tasks, queue.drafts = pending drafts, queue.classify = unsorted content
  // These are three independent categories — sum them for the inbox total
  const queueTotal = (queue.drafts ?? 0) + (queue.classify ?? 0);
  const hasUrgent = queue.urgent > 0;
  const healthIssues = health.filter(h => h.status === 'red' || h.status === 'critical' || h.status === 'error' || h.status === 'down').length;
  const attentionCount = (queue.urgent ?? 0) + healthIssues;

  return (
    <div className="space-y-5">
      {/* Alert banner — only when something needs attention */}
      {attentionCount > 0 && (
        <Link
          to="/inbox"
          className="flex items-center gap-3 px-4 py-3 bg-destructive/10 border border-destructive/20 rounded-lg hover:bg-destructive/15 transition-colors group"
        >
          <AlertTriangle size={16} className="text-destructive shrink-0" />
          <span className="text-sm text-foreground flex-1">
            <strong>{attentionCount} item{attentionCount !== 1 ? 's' : ''}</strong> need{attentionCount === 1 ? 's' : ''} attention
            {queue.urgent > 0 && ` — ${queue.urgent} urgent`}
            {healthIssues > 0 && ` — ${healthIssues} health alert${healthIssues !== 1 ? 's' : ''}`}
          </span>
          <span className="text-xs text-muted-foreground group-hover:text-foreground flex items-center gap-1">
            Go to Inbox <ArrowRight size={12} />
          </span>
        </Link>
      )}

      {/* Scope indicator */}
      {selectedNode && (
        <div className="flex items-center gap-2 px-3 py-2 bg-accent/40 border border-border rounded-lg text-sm text-foreground">
          <Layers size={14} className="text-muted-foreground shrink-0" />
          <span>
            Viewing: <strong>{selectedNode.label}</strong>
            {selectedNode.node_type !== 'project' && scopeProjectIds.length > 0 && (
              <span className="text-muted-foreground ml-1">
                ({scopeProjectIds.length} project{scopeProjectIds.length !== 1 ? 's' : ''})
              </span>
            )}
          </span>
        </div>
      )}

      {/* Welcome + date */}
      <div>
        <h2 className="text-lg font-semibold text-foreground">{getGreeting()}, Rijul</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          icon={FolderKanban}
          label="Projects"
          value={projects.length}
          sub={`${projects.filter(p => p.active).length} active`}
          to="/projects"
        />
        <MetricCard
          icon={Inbox}
          label="Inbox"
          value={queueTotal}
          sub={hasUrgent ? `${queue.urgent} urgent` : 'All clear'}
          to="/inbox"
          alert={hasUrgent}
        />
        <MetricCard
          icon={Radio}
          label="Agents"
          value={agents.total}
          sub={`${agents.running} running`}
          to="/agents"
        />
        <MetricCard
          icon={DollarSign}
          label="Monthly Cost"
          value={formatCost(costs.month_usd)}
          sub={`${formatCost(costs.today_usd)} today`}
          to="/costs"
        />
      </div>

      {/* Health bar */}
      <HealthBar sources={health} />

      {/* Project cards + Activity/Costs */}
      <div className="grid grid-cols-3 gap-3 sm:gap-4 md:gap-6">
        {/* Left 2/3: Project cards */}
        <div className="col-span-2 space-y-3">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Projects {projects.length > 0 && `(${projects.length})`}
          </h3>
          {projects.length === 0 ? (
            <div className="rounded-lg border border-border p-6 text-center text-muted-foreground text-sm">
              No projects yet. Ingest content to create your first project.
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {projects.slice(0, 6).map((p) => (
                <ProjectCard
                  key={p.id}
                  id={p.id}
                  name={p.name}
                  active={p.active}
                  item_count={p.item_count}
                  jira_key={p.jira_key}
                />
              ))}
              {projects.length > 6 && (
                <Link to="/projects" className="text-xs text-muted-foreground hover:text-foreground p-3 text-center">
                  +{projects.length - 6} more projects
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Right 1/3: Activity + Cost */}
        <div className="space-y-4">
          <div>
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Recent Activity
            </h3>
            <div className="max-h-96 overflow-y-auto scrollbar-auto-hide">
              <ActivityFeed events={activityEvents} />
            </div>
          </div>
          <CostSummary
            today_usd={costs.today_usd}
            month_usd={costs.month_usd}
            daily={costs.daily}
          />
        </div>
      </div>
    </div>
  );
}
