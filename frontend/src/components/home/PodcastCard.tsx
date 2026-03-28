import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Mic, Loader2, Clock, Radio } from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';
import { PodcastPlayer } from './PodcastPlayer';

interface Podcast {
  id: string;
  title: string;
  script: string | null;
  audio_path: string | null;
  duration: number | null;
  voice: string | null;
  status: string | null;
  created_at: string;
}

interface PodcastListResponse {
  items: Podcast[];
  count: number;
}

function isToday(dateStr: string): boolean {
  const d = new Date(dateStr);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '--:--';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function PodcastCard() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<PodcastListResponse>({
    queryKey: ['podcasts'],
    queryFn: () => apiFetch<PodcastListResponse>('/podcasts/?limit=1'),
    staleTime: 60_000,
  });

  const generateMutation = useMutation({
    mutationFn: () => apiPost<Podcast>('/podcasts/', { voice: 'andrew' }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['podcasts'] });
    },
  });

  const latest = data?.items?.[0];
  const hasRecentPodcast = latest && (isToday(latest.created_at) || latest.status === 'ready');
  const isGenerating = generateMutation.isPending || latest?.status === 'generating';

  const audioUrl = latest?.audio_path
    ? `/api/podcasts/${latest.id}/audio`
    : null;

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent/60 flex items-center justify-center">
            <Radio size={14} className="text-foreground/70" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-foreground">Your Morning Brief</h3>
            {latest && (
              <div className="flex items-center gap-2 text-[11px] text-muted-foreground mt-0.5">
                <span>{new Date(latest.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                {latest.duration && (
                  <>
                    <span className="text-muted-foreground/30">|</span>
                    <span className="flex items-center gap-0.5">
                      <Clock size={10} />
                      {formatDuration(latest.duration)}
                    </span>
                  </>
                )}
                {latest.voice && (
                  <>
                    <span className="text-muted-foreground/30">|</span>
                    <span>{latest.voice}</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={() => generateMutation.mutate()}
          disabled={isGenerating}
          className={cn(
            'inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors',
            isGenerating
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'bg-accent text-accent-foreground hover:bg-accent/80'
          )}
        >
          {isGenerating ? (
            <>
              <Loader2 size={12} className="animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Mic size={12} />
              {hasRecentPodcast ? 'New Brief' : 'Generate'}
            </>
          )}
        </button>
      </div>

      {/* Player or empty state */}
      {isLoading ? (
        <div className="h-16 rounded-lg bg-muted/30 animate-pulse" />
      ) : hasRecentPodcast && latest ? (
        <PodcastPlayer
          audioUrl={audioUrl}
          script={latest.script}
          duration={latest.duration}
          title={latest.title}
        />
      ) : !isGenerating ? (
        <div className="rounded-lg bg-muted/20 py-6 text-center">
          <Mic size={20} className="mx-auto text-muted-foreground/50 mb-2" />
          <p className="text-xs text-muted-foreground">
            No briefing yet today. Generate one to get your morning summary.
          </p>
        </div>
      ) : null}

      {/* Error state */}
      {generateMutation.isError && (
        <p className="text-xs text-destructive">
          Failed to generate briefing. Check backend logs.
        </p>
      )}
    </div>
  );
}
