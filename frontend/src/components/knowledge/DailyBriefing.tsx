import { Activity, AlertTriangle, BarChart3, Calendar, RefreshCw, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BriefingItem {
  label: string;
  value: string;
  detail?: string;
  severity?: 'critical' | 'warning' | 'info';
}

export interface BriefingSection {
  title: string;
  icon: string;
  items: BriefingItem[];
}

export interface ProgramHealth {
  id: string;
  name: string;
  health: string;
  score: number;
  issues: string[];
  article_count: number;
  pending_decisions: number;
  stale_articles: number;
}

export interface BriefingResponse {
  generated_at: string;
  sections: BriefingSection[];
  highlights: string[];
  program_health?: ProgramHealth[];
  from_cache?: boolean;
}

interface DailyBriefingProps {
  briefingData: BriefingResponse | null;
  isLoading: boolean;
  onRefresh: () => void;
  onNavigateProgram?: (programId: string) => void;
}

// ---------------------------------------------------------------------------
// Icon mapping
// ---------------------------------------------------------------------------

const SECTION_ICONS: Record<string, React.ElementType> = {
  'activity': Activity,
  'alert-triangle': AlertTriangle,
  'bar-chart': BarChart3,
  'calendar': Calendar,
};

// ---------------------------------------------------------------------------
// Severity colors
// ---------------------------------------------------------------------------

function severityClasses(severity?: string): string {
  switch (severity) {
    case 'critical':
      return 'text-red-600 dark:text-red-400';
    case 'warning':
      return 'text-amber-600 dark:text-amber-400';
    case 'info':
      return 'text-blue-600 dark:text-blue-400';
    default:
      return 'text-foreground';
  }
}

function severityBg(severity?: string): string {
  switch (severity) {
    case 'critical':
      return 'bg-red-500/10 border-red-500/20';
    case 'warning':
      return 'bg-amber-500/10 border-amber-500/20';
    case 'info':
      return 'bg-blue-500/10 border-blue-500/20';
    default:
      return 'bg-card border-border';
  }
}

function severityDot(severity?: string): string {
  switch (severity) {
    case 'critical':
      return 'bg-red-500';
    case 'warning':
      return 'bg-amber-500';
    case 'info':
      return 'bg-blue-500';
    default:
      return 'bg-muted-foreground';
  }
}

// ---------------------------------------------------------------------------
// Skeleton loading state
// ---------------------------------------------------------------------------

function BriefingSkeleton() {
  return (
    <div className="p-6 space-y-6 animate-pulse">
      {/* Timestamp skeleton */}
      <div className="flex items-center justify-between">
        <div className="h-4 w-48 bg-muted rounded" />
        <div className="h-8 w-24 bg-muted rounded" />
      </div>

      {/* Section cards skeleton */}
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="bg-card border border-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 bg-muted rounded" />
            <div className="h-5 w-32 bg-muted rounded" />
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map((j) => (
              <div key={j} className="flex items-center justify-between">
                <div className="h-4 w-40 bg-muted rounded" />
                <div className="h-4 w-16 bg-muted rounded" />
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Highlights skeleton */}
      <div className="space-y-3">
        <div className="h-5 w-24 bg-muted rounded" />
        <div className="h-16 bg-muted rounded-xl" />
        <div className="h-16 bg-muted rounded-xl" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section card component
// ---------------------------------------------------------------------------

function SectionCard({ section }: { section: BriefingSection }) {
  const Icon = SECTION_ICONS[section.icon] || Activity;
  const isAttention = section.icon === 'alert-triangle';

  return (
    <div className={cn(
      'bg-card border border-border rounded-xl p-4 transition-colors',
      isAttention && section.items.some(i => i.severity === 'critical') && 'border-red-500/30',
    )}>
      <div className="flex items-center gap-2 mb-2.5">
        <div className={cn(
          'flex items-center justify-center w-6 h-6 rounded-md',
          isAttention ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' : 'bg-accent/10 text-accent',
        )}>
          <Icon className="h-3.5 w-3.5" />
        </div>
        <h3 className="text-xs font-semibold text-muted-foreground tracking-wide uppercase">
          {section.title}
        </h3>
      </div>

      <div className="space-y-1.5">
        {section.items.map((item, idx) => (
          <div
            key={idx}
            className={cn(
              'flex items-start justify-between gap-4 py-1.5 px-2.5 rounded-md border',
              item.severity ? severityBg(item.severity) : 'bg-muted/30 border-transparent',
            )}
          >
            <div className="flex items-start gap-2 min-w-0 flex-1">
              {item.severity && (
                <span className={cn('mt-1.5 w-1.5 h-1.5 rounded-full shrink-0', severityDot(item.severity))} />
              )}
              <div className="min-w-0">
                <span className="text-sm text-muted-foreground">{item.label}</span>
                {item.detail && (
                  <p className="text-xs text-muted-foreground/70 mt-0.5 truncate">{item.detail}</p>
                )}
              </div>
            </div>
            <span className={cn(
              'text-sm font-semibold tabular-nums whitespace-nowrap',
              item.severity ? severityClasses(item.severity) : 'text-foreground',
            )}>
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Highlight card
// ---------------------------------------------------------------------------

function HighlightCard({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-3 px-4 py-3 bg-amber-500/5 border border-amber-500/15 rounded-xl">
      <Zap className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
      <p className="text-sm text-foreground leading-relaxed">{text}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Program Health Bar
// ---------------------------------------------------------------------------

function healthColor(health: string): { bar: string; bg: string; text: string; badge: string } {
  switch (health) {
    case 'green':
      return { bar: 'bg-green-500', bg: 'bg-green-50 dark:bg-green-950/20', text: 'text-green-700 dark:text-green-400', badge: 'OK' };
    case 'yellow':
      return { bar: 'bg-amber-500', bg: 'bg-amber-50 dark:bg-amber-950/20', text: 'text-amber-700 dark:text-amber-400', badge: '!' };
    case 'red':
      return { bar: 'bg-red-500', bg: 'bg-red-50 dark:bg-red-950/20', text: 'text-red-700 dark:text-red-400', badge: '!!' };
    default:
      return { bar: 'bg-muted', bg: 'bg-muted/30', text: 'text-muted-foreground', badge: '--' };
  }
}

function ProgramHealthBar({ programs, onNavigate }: { programs: ProgramHealth[]; onNavigate?: (id: string) => void }) {
  if (!programs.length) return null;
  // Show top 6 programs sorted by score (worst first), skip programs with 0 articles
  const visible = programs
    .filter((p) => p.article_count > 0)
    .sort((a, b) => a.score - b.score)
    .slice(0, 6);

  const redCount = visible.filter((p) => p.health === 'red').length;
  const yellowCount = visible.filter((p) => p.health === 'yellow').length;

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-muted-foreground tracking-wide uppercase">
          Program Health
        </h3>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {redCount > 0 && <span className="text-red-500 font-medium">{redCount} at risk</span>}
          {yellowCount > 0 && <span className="text-amber-500 font-medium">{yellowCount} warning</span>}
          <span>{programs.filter((p) => p.article_count > 0).length} total</span>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {visible.map((p) => {
          const c = healthColor(p.health);
          return (
            <button
              key={p.id}
              onClick={() => onNavigate?.(p.id)}
              aria-label={`Navigate to ${p.name} — ${p.health}`}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition-colors hover:border-accent/40',
                p.health === 'red' ? 'border-red-500/30 bg-red-500/5' :
                p.health === 'yellow' ? 'border-amber-500/30 bg-amber-500/5' :
                'border-border bg-card',
              )}
            >
              <span className={cn('w-2 h-2 rounded-full shrink-0', c.bar)} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-foreground truncate">{p.name}</p>
                <p className="text-[11px] text-muted-foreground">{p.article_count} articles{p.issues.length > 0 ? ` · ${p.issues[0]}` : ''}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component (accepts shared briefing data via props)
// ---------------------------------------------------------------------------

export function DailyBriefing({ briefingData, isLoading, onRefresh, onNavigateProgram }: DailyBriefingProps) {
  if (isLoading) {
    return <BriefingSkeleton />;
  }

  if (!briefingData) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p className="text-sm">Unable to load briefing</p>
      </div>
    );
  }

  const data = briefingData;

  // Format timestamp for display
  const generatedAt = data.generated_at
    ? new Date(data.generated_at).toLocaleString(undefined, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  return (
    <div className="p-4 space-y-4">
      {/* Header with timestamp and refresh */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            Generated {generatedAt}
          </span>
          {data.from_cache && (
            <span className="text-xs px-2 py-0.5 bg-muted rounded-full text-muted-foreground">
              cached
            </span>
          )}
        </div>
        <button
          onClick={onRefresh}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg',
            'bg-card border border-border text-foreground',
            'hover:bg-muted transition-colors',
          )}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {/* Program health bars — above section cards */}
      {data.program_health && data.program_health.length > 0 && (
        <ProgramHealthBar programs={data.program_health} onNavigate={onNavigateProgram} />
      )}

      {/* Section cards — 2-column grid on wider screens */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {data.sections.map((section, idx) => (
          <SectionCard key={idx} section={section} />
        ))}
      </div>

      {/* Highlights */}
      {data.highlights.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-muted-foreground tracking-wide uppercase">
            Highlights
          </h3>
          {data.highlights.map((text, idx) => (
            <HighlightCard key={idx} text={text} />
          ))}
        </div>
      )}
    </div>
  );
}
