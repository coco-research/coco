import { type ReactNode, useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { AlertTriangle, Search, FileText, FolderOpen, HeartPulse, Sparkles } from 'lucide-react';
import { apiFetch, apiPatch, apiPost } from '../lib/api';
import { cn, timeAgo } from '../lib/utils';
import { BriefingCard, type SyncResult } from '../components/home/BriefingCard';
import { ProjectHealthGrid } from '../components/home/ProjectHealthGrid';
import { FocusList } from '../components/home/FocusList';
import { JarvisOverlay } from '../components/home/JarvisOverlay';
import type { HomeData, Todo } from '../types/home';

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="h-8 rounded-lg bg-muted/50 animate-pulse" />
      <div className="h-10 rounded-lg bg-muted/50 animate-pulse" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="lg:col-span-7 space-y-5">
          <div className="h-56 rounded-xl bg-muted/50 animate-pulse" />
          <div className="h-64 rounded-xl bg-muted/50 animate-pulse" />
        </div>
        <div className="lg:col-span-5 space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-32 rounded-lg bg-muted/50 animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

function dedupeAndSortTodos(data: HomeData): Todo[] {
  const all = [...data.todos.overdue, ...data.todos.high_priority, ...data.todos.medium_priority];
  const seen = new Set<string>();
  const unique = all.filter((t) => {
    if (seen.has(t.id)) return false;
    seen.add(t.id);
    return true;
  });

  const overdueIds = new Set(data.todos.overdue.map((t) => t.id));
  const highIds = new Set(data.todos.high_priority.map((t) => t.id));

  return unique.sort((a, b) => {
    const aOverdue = overdueIds.has(a.id);
    const bOverdue = overdueIds.has(b.id);
    if (aOverdue && !bOverdue) return -1;
    if (!aOverdue && bOverdue) return 1;
    if (aOverdue && bOverdue) {
      // Both overdue: sort by due_date ascending (most overdue first)
      return (a.due_date ?? '').localeCompare(b.due_date ?? '');
    }
    const aHigh = highIds.has(a.id);
    const bHigh = highIds.has(b.id);
    if (aHigh && !bHigh) return -1;
    if (!aHigh && bHigh) return 1;
    return (a.due_date ?? '9999').localeCompare(b.due_date ?? '9999');
  });
}

function getSyncStatus(health: HomeData['health']) {
  if (health.length === 0) return { color: 'bg-muted-foreground', label: 'No sources' };
  const hasRed = health.some((h) => h.status === 'red' || h.status === 'critical');
  const hasYellow = health.some((h) => h.status === 'yellow' || h.status === 'warn');

  // Find the most recently synced source
  const synced = health.filter((h) => h.last_sync).sort((a, b) => {
    return new Date(b.last_sync!).getTime() - new Date(a.last_sync!).getTime();
  });
  const label = synced.length > 0 ? `Sync ${timeAgo(synced[0].last_sync!)}` : 'No sync data';

  if (hasRed) return { color: 'bg-destructive', label };
  if (hasYellow) return { color: 'bg-warning', label };
  return { color: 'bg-success', label };
}

export default function HomePage() {
  const queryClient = useQueryClient();
  const [syncBanner, setSyncBanner] = useState<string | null>(null);
  const [jarvisOpen, setJarvisOpen] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  // Auto-open Jarvis overlay when ?jarvis=true is in the URL
  useEffect(() => {
    if (searchParams.get('jarvis') === 'true') {
      setJarvisOpen(true);
      // Remove the query param so it doesn't persist on refresh
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const { data, isLoading, isError } = useQuery<HomeData>({
    queryKey: ['home'],
    queryFn: () => apiFetch<HomeData>('/home'),
    refetchInterval: 30000,
  });

  // Auto-sync todos from Knowledge Hub on page load (once per 5 minutes)
  const { data: autoSyncResult } = useQuery<SyncResult>({
    queryKey: ['todo-auto-sync'],
    queryFn: () => apiPost<SyncResult>('/todos/sync', {}),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: !!data,
  });

  // Show banner when auto-sync finds new items
  const lastSyncRef = useRef<number>(0);
  useEffect(() => {
    if (!autoSyncResult || autoSyncResult.synced === 0) return;
    // Avoid re-showing for the same result
    const key = autoSyncResult.synced + autoSyncResult.skipped;
    if (key === lastSyncRef.current) return;
    lastSyncRef.current = key;

    setSyncBanner(
      `${autoSyncResult.synced} new action item${autoSyncResult.synced === 1 ? '' : 's'} from Knowledge Hub`
    );
    void queryClient.invalidateQueries({ queryKey: ['home'] });
    const timer = setTimeout(() => setSyncBanner(null), 8000);
    return () => clearTimeout(timer);
  }, [autoSyncResult, queryClient]);

  const markTodoDone = useMutation({
    mutationFn: (id: string) => apiPatch(`/todos/${id}`, { status: 'done' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['home'] }),
  });

  const handleSyncComplete = (result: SyncResult) => {
    if (result.synced > 0) {
      void queryClient.invalidateQueries({ queryKey: ['home'] });
      void queryClient.invalidateQueries({ queryKey: ['todos'] });
    }
  };

  if (isLoading || !data) return <LoadingState />;

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle size={40} className="text-destructive mb-4" />
        <h2 className="text-lg font-semibold text-foreground mb-2">Unable to load dashboard</h2>
        <p className="text-sm text-muted-foreground mb-4">The backend may be down or Knowledge Hub is unreachable.</p>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['home'] })}
          className="px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm hover:bg-accent/80 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const { attention, health } = data;
  const sync = getSyncStatus(health);
  const hasAlerts = attention.unsorted_count > 0 || attention.pending_drafts > 0 || attention.overdue_todos > 0 || attention.health_alerts > 0;
  const hasSevere = attention.overdue_todos > 0 || attention.health_alerts > 0;
  const mergedTodos = dedupeAndSortTodos(data);

  const openCommandPalette = () => {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
  };

  const alertItems: ReactNode[] = [];
  if (attention.overdue_todos > 0) {
    alertItems.push(
      <Link key="overdue" to="/todos" className="inline-flex items-center gap-1.5 text-xs font-medium text-destructive hover:underline">
        <AlertTriangle size={12} />
        {attention.overdue_todos} overdue
      </Link>,
    );
  }
  if (attention.health_alerts > 0) {
    alertItems.push(
      <Link key="health" to="/settings" className="inline-flex items-center gap-1.5 text-xs font-medium text-destructive hover:underline">
        <HeartPulse size={12} />
        {attention.health_alerts} health alert{attention.health_alerts !== 1 && 's'}
      </Link>,
    );
  }
  if (attention.unsorted_count > 0) {
    alertItems.push(
      <Link key="unsorted" to="/inbox" className="inline-flex items-center gap-1.5 text-xs font-medium text-foreground hover:underline">
        <FolderOpen size={12} />
        {attention.unsorted_count} unsorted
      </Link>,
    );
  }
  if (attention.pending_drafts > 0) {
    alertItems.push(
      <Link key="drafts" to="/inbox" className="inline-flex items-center gap-1.5 text-xs font-medium text-foreground hover:underline">
        <FileText size={12} />
        {attention.pending_drafts} draft{attention.pending_drafts !== 1 && 's'}
      </Link>,
    );
  }

  return (
    <div className="space-y-5">
      {/* Auto-sync banner */}
      {syncBanner && (
        <div className="rounded-lg bg-accent/60 px-4 py-2 flex items-center justify-between text-sm text-foreground animate-in fade-in slide-in-from-top-2 duration-300">
          <span>{syncBanner}</span>
          <button
            onClick={() => setSyncBanner(null)}
            className="text-muted-foreground hover:text-foreground text-xs ml-4"
          >
            dismiss
          </button>
        </div>
      )}

      {/* Header: Title Bar + Alert Banner grouped tightly */}
      <header className="space-y-2">
        {/* Title Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-baseline gap-3">
            <h1 className="text-lg font-semibold text-foreground">{data.greeting}</h1>
            <span className="text-xs text-muted-foreground">{data.date}</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setJarvisOpen(true)}
              className="inline-flex items-center gap-1 text-[11px] border border-border rounded-md px-2.5 py-1 text-muted-foreground hover:text-foreground hover:border-foreground/20 cursor-pointer transition-colors"
              title="Activate Jarvis"
            >
              <Sparkles size={10} />
              Jarvis
            </button>
            <button
              onClick={openCommandPalette}
              className="inline-flex items-center gap-1 text-[11px] border border-border rounded-md px-2.5 py-1 text-muted-foreground hover:text-foreground hover:border-foreground/20 cursor-pointer transition-colors"
            >
              <Search size={10} />
              Cmd+K
            </button>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground" title="Source sync status">
              <span className={cn('w-2 h-2 rounded-full inline-block', sync.color)} />
              {sync.label}
            </span>
          </div>
        </div>

        {/* Alert Banner */}
        {hasAlerts && (
          <div
            className={cn(
              'rounded-lg py-2.5 px-4 flex items-center gap-2 flex-wrap',
              hasSevere ? 'bg-destructive/10' : 'bg-warning/10',
            )}
          >
            {alertItems.map((item, i) => (
              <span key={i} className="inline-flex items-center gap-2">
                {i > 0 && <span className="text-muted-foreground/30">|</span>}
                {item}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* Main 2-column layout: Left (action) | Right (status) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left column: Briefing + Focus List */}
        <div className="lg:col-span-7 space-y-5">
          <BriefingCard
            sinceLastSession={data.since_last_session}
            attention={data.attention}
            queue={data.queue}
            costs={data.costs}
            health={data.health}
            projects={data.projects}
            todos={data.todos}
            onSyncComplete={handleSyncComplete}
          />
          <FocusList
            todos={mergedTodos}
            projects={data.projects}
            onMarkDone={(id) => markTodoDone.mutate(id)}
          />
        </div>

        {/* Right column: Projects (scrollable) */}
        <div className="lg:col-span-5 lg:max-h-[calc(100vh-120px)] lg:overflow-y-auto lg:scrollbar-auto-hide">
          <ProjectHealthGrid projects={data.projects} />
        </div>
      </div>

      {/* Jarvis cinematic overlay */}
      <JarvisOverlay isOpen={jarvisOpen} onClose={() => setJarvisOpen(false)} />
    </div>
  );
}
