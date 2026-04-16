import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, RefreshCw } from 'lucide-react';
import { formatCost, cn } from '../../lib/utils';
import { apiPost } from '../../lib/api';
import type {
  AttentionCounts,
  QueueSummary,
  SourceHealth,
  HomeProject,
  Todo,
  DraftsSummary,
} from '../../types/home';

export interface SyncResult {
  synced: number;
  skipped: number;
  total: number;
}

interface BriefingCardProps {
  sinceLastSession: { hours_ago: number | null; label: string | null } | null;
  attention: AttentionCounts;
  queue: QueueSummary;
  costs: { today_usd: number; month_usd: number };
  health: SourceHealth[];
  projects: HomeProject[];
  todos: {
    total_open: number;
    high_priority: Todo[];
    medium_priority: Todo[];
    overdue: Todo[];
  };
  drafts?: DraftsSummary;
  onSyncComplete?: (result: SyncResult) => void;
}

interface Bullet {
  text: string;
  critical: boolean;
}

function generateBullets(props: BriefingCardProps): Bullet[] {
  const { attention, health, projects, todos } = props;
  const bullets: Bullet[] = [];

  // 1. Overdue — name offending projects
  if (attention.overdue_todos > 0 && todos.overdue.length > 0) {
    const byProject = new Map<string, number>();
    for (const t of todos.overdue) {
      const key = t.project_id ?? '__none__';
      byProject.set(key, (byProject.get(key) ?? 0) + 1);
    }
    const nameMap = new Map(projects.map((p) => [p.id, p.name.split('(')[0].trim()]));
    const top = [...byProject.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 2)
      .map(([id, n]) => `${nameMap.get(id) ?? 'Unassigned'} (${n})`)
      .join(', ');
    bullets.push({
      text: `${attention.overdue_todos} overdue — ${top}`,
      critical: true,
    });
  }

  // 2. Top priority item — surface the #1 thing
  if (bullets.length < 7 && todos.high_priority.length > 0) {
    const top = todos.high_priority[0];
    const title = top.title.length > 50 ? top.title.slice(0, 50) + '...' : top.title;
    const more = todos.high_priority.length - 1;
    bullets.push({
      text: `Top priority: "${title}"${more > 0 ? ` +${more} more` : ''}`,
      critical: true,
    });
  }

  // 3. Stale health sources
  if (bullets.length < 7) {
    const stale = health.filter((s) => s.status === 'red' || s.status === 'critical');
    if (stale.length > 0) {
      const names = stale.map((s) => {
        const hrs = s.stale_hours != null ? ` (${Math.round(s.stale_hours)}h)` : '';
        return `${s.source}${hrs}`;
      }).join(', ');
      bullets.push({ text: `Sync stale: ${names}`, critical: true });
    }
  }

  // 4. Pending drafts
  if (bullets.length < 7 && attention.pending_drafts > 0) {
    bullets.push({
      text: `${attention.pending_drafts} draft${attention.pending_drafts === 1 ? '' : 's'} ready for review`,
      critical: false,
    });
  }

  // 5. Unsorted items
  if (bullets.length < 7 && attention.unsorted_count > 0) {
    bullets.push({
      text: `${attention.unsorted_count.toLocaleString()} unsorted items to classify`,
      critical: false,
    });
  }

  // 6. Project activity — most active projects
  if (bullets.length < 7) {
    const active = projects.filter((p) => p.item_count > 0).sort((a, b) => b.item_count - a.item_count);
    if (active.length > 0) {
      const total = active.reduce((s, p) => s + p.item_count, 0);
      const topNames = active.slice(0, 3).map((p) => p.name.split('(')[0].trim()).join(', ');
      bullets.push({
        text: `${total} items across ${active.length} projects — most active: ${topNames}`,
        critical: false,
      });
    }
  }

  // 7. Source breakdown
  if (bullets.length < 7) {
    const totals = { email: 0, voice: 0, jira: 0, confluence: 0 };
    for (const p of projects) {
      totals.email += p.sources.email;
      totals.voice += p.sources.voice;
      totals.jira += p.sources.jira;
      totals.confluence += p.sources.confluence;
    }
    const parts: string[] = [];
    if (totals.email > 0) parts.push(`${totals.email} emails`);
    if (totals.voice > 0) parts.push(`${totals.voice} voice memos`);
    if (totals.jira > 0) parts.push(`${totals.jira} Jira tickets`);
    if (totals.confluence > 0) parts.push(`${totals.confluence} Confluence pages`);
    if (parts.length > 0) {
      bullets.push({ text: `Sources: ${parts.join(', ')}`, critical: false });
    }
  }

  return bullets;
}

export function BriefingCard(props: BriefingCardProps) {
  const { sinceLastSession, queue, costs, todos, drafts, projects, health, onSyncComplete } = props;
  const bullets = generateBullets(props);
  const hasContent = bullets.length > 0;

  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const result = await apiPost<SyncResult>('/todos/sync', {});
      if (result.synced > 0) {
        setSyncMessage(
          `Synced ${result.synced} new todo${result.synced === 1 ? '' : 's'} from Knowledge Hub.` +
          (result.skipped > 0 ? ` ${result.skipped} skipped (already tracked).` : '')
        );
      } else {
        setSyncMessage('All action items already tracked. Nothing new to sync.');
      }
      onSyncComplete?.(result);
    } catch {
      setSyncMessage('Sync failed. Check backend logs.');
    } finally {
      setSyncing(false);
    }
  };

  const totalProjects = projects.filter((p) => p.active).length;
  const healthyCount = health.filter((h) => {
    // A source is healthy only if its status is ok/green AND it's not stale (>24h without sync)
    const statusOk = h.status === 'green' || h.status === 'ok';
    const isStale = (h.stale_hours ?? 0) > 24;
    return statusOk && !isStale;
  }).length;
  const totalSources = health.length;

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground mb-4">
        Morning Briefing
      </p>

      {sinceLastSession?.label && (
        <p className="text-sm text-muted-foreground mb-3">
          Since last session ({sinceLastSession.label}):
        </p>
      )}

      {hasContent ? (
        <ul className="space-y-2 mb-4">
          {bullets.map((bullet, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span
                className={cn(
                  'mt-1.5 h-1.5 w-1.5 rounded-full shrink-0',
                  bullet.critical ? 'bg-destructive' : 'bg-muted-foreground/40',
                )}
              />
              <span className={cn(bullet.critical ? 'text-foreground' : 'text-muted-foreground')}>
                {bullet.critical ? bullet.text.replace(/^[\u{1F534}\u{1F7E0}\u{1F7E1}\u{1F7E2}\u{26A0}\u{FE0F}\u{2B55}]\s*/u, '') : bullet.text}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground mb-4">
          All systems healthy. No items need your attention.
        </p>
      )}

      {/* Sync result message */}
      {syncMessage && (
        <div className="rounded-lg bg-accent/50 px-3 py-2 text-xs text-foreground mb-3">
          {syncMessage}
        </div>
      )}

      {/* Summary stats */}
      <div className="flex gap-x-4 text-xs text-muted-foreground border-t border-border/30 pt-3 mt-3 whitespace-nowrap overflow-x-auto">
        <span>{todos.total_open} open tasks</span>
        <span className="text-border">·</span>
        <span>{todos.high_priority.length} high priority</span>
        <span className="text-border">·</span>
        {drafts && (
          <>
            <span>{drafts.total} drafts ({drafts.by_status?.pending ?? 0} pending)</span>
            <span className="text-border">·</span>
          </>
        )}
        <span>{totalProjects} active projects</span>
        <span className="text-border">·</span>
        <span>{healthyCount}/{totalSources} sources healthy</span>
      </div>

      {/* Cost */}
      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground font-mono">
        <span>Cost: {formatCost(costs.today_usd)} today</span>
        <span className="text-border">·</span>
        <span>{formatCost(costs.month_usd)} this month</span>
      </div>

      {/* CTA */}
      <div className="flex items-center gap-3 mt-4">
        {queue.total > 0 && (
          <Link
            to="/inbox"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Start Triage
            <ArrowRight className="h-4 w-4" />
          </Link>
        )}
        <button
          onClick={handleSync}
          disabled={syncing}
          className={cn(
            'inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-border text-sm font-medium transition-all',
            syncing
              ? 'opacity-60 cursor-not-allowed text-muted-foreground'
              : 'text-foreground hover:bg-accent/50',
          )}
        >
          <RefreshCw className={cn('h-3.5 w-3.5', syncing && 'animate-spin')} />
          {syncing ? 'Syncing...' : 'Sync Todos'}
        </button>
      </div>
    </div>
  );
}
