import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';
import { apiFetch, apiPatch, apiPost } from '../lib/api';
import { cn } from '../lib/utils';
import { useCountUp } from '../hooks/useCountUp';
import { useJarvisAudio } from '../hooks/useJarvisAudio';
import { useCanvas } from '../hooks/useCanvas';
import { HealthRing } from '../components/jarvis/HealthRing';
import { GlassCard } from '../components/jarvis/GlassCard';
import { BriefingSequence, type BriefingScene } from '../components/jarvis/BriefingSequence';
import { ReactiveCanvas } from '../components/jarvis/ReactiveCanvas';
import { JarvisInput } from '../components/jarvis/JarvisInput';
import type { HomeData, HomeProject, Todo } from '../types/home';
import type { CommandResponse } from '../types/cards';

interface BriefingResponse {
  script: string;
  scenes: BriefingScene[];
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function CocoLogo({ visible }: { visible: boolean }) {
  return (
    <div
      className="transition-all duration-1000 ease-out text-center"
      style={{ opacity: visible ? 1 : 0, transform: visible ? 'scale(1)' : 'scale(0.97)' }}
    >
      <h1 className="text-4xl font-semibold text-white/90 tracking-tight">CoCo</h1>
      <p className="text-[11px] text-white/30 mt-1">Your Brain</p>
    </div>
  );
}

// BriefingText replaced by BriefingSequence component

function MetricCard({ label, value, delay, color = 'text-white/90' }: {
  label: string; value: number; delay: number; color?: string;
}) {
  const count = useCountUp(value, 1800, { enabled: true, delay });
  return (
    <div className="jarvis-reveal text-center" style={{ '--reveal-delay': `${delay}ms` } as React.CSSProperties}>
      <div className={`text-3xl font-bold ${color}`}>
        {count.toLocaleString()}
      </div>
      <div className="text-[10px] text-white/40 mt-1">{label}</div>
    </div>
  );
}

function ProjectRow({ project, index, delay }: { project: HomeProject; index: number; delay: number }) {
  return (
    <div
      className="jarvis-reveal flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/5 transition-colors"
      style={{ '--reveal-delay': `${delay}ms` } as React.CSSProperties}
    >
      <span className="text-xs text-white/30 w-4">{index + 1}</span>
      <Link to={`/projects/${project.id}`} className="flex-1 min-w-0">
        <span className="text-sm text-slate-300 truncate block">{project.name}</span>
      </Link>
      <span className="text-xs text-white/60 w-16 text-right">
        {project.todo_done}/{project.todo_total}
      </span>
      <span className="text-xs text-white/60 w-12 text-right">
        {project.todo_open} open
      </span>
      <span className="text-xs text-white/60 w-12 text-right">
        {project.item_count} items
      </span>
    </div>
  );
}

function FocusItem({ todo, isOverdue }: { todo: Todo; isOverdue: boolean }) {
  const isHigh = todo.priority === 'high';
  const isDone = todo.status === 'done';
  const qc = useQueryClient();

  const toggle = async () => {
    await apiPatch(`/todos/${todo.id}`, { status: isDone ? 'open' : 'done' });
    void qc.invalidateQueries({ queryKey: ['home'] });
    void qc.invalidateQueries({ queryKey: ['todos'] });
  };

  return (
    <div className={`flex items-start gap-2 py-1.5 group ${isOverdue ? 'text-[#FF453A]' : isHigh ? 'text-[#FF9F0A]' : 'text-white/50'} ${isDone ? 'opacity-40' : ''}`}>
      <button
        onClick={toggle}
        className={cn(
          'flex items-center justify-center h-4 w-4 rounded border mt-0.5 shrink-0 transition-colors',
          isDone ? 'bg-emerald-500 border-emerald-500' : 'border-current hover:border-emerald-500',
        )}
      >
        {isDone && <Check className="h-2.5 w-2.5 text-white" />}
      </button>
      <span className={`text-xs leading-snug truncate ${isDone ? 'line-through' : ''}`}>{todo.title}</span>
    </div>
  );
}

function CommandBar({ delay }: { delay: number }) {
  const commands = ['briefing', 'decide', 'search', 'process', 'todo', 'chat'];
  return (
    <div
      className="jarvis-reveal flex items-center justify-center gap-3 pt-4"
      style={{ '--reveal-delay': `${delay}ms` } as React.CSSProperties}
    >
      {commands.map((cmd) => (
        <span
          key={cmd}
          className="text-[11px] font-mono text-sky-400/40 hover:text-sky-400 transition-colors cursor-default"
        >
          {cmd}
        </span>
      ))}
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function JarvisPage() {
  const { isSpeaking, ...audio } = useJarvisAudio();
  const canvas = useCanvas();
  const [phase, setPhase] = useState(0);
  // Phase -1: "wake up" prompt (waiting for click to unlock audio)
  // Phase 0: loading data
  // Phase 1: logo appears
  // Phase 2: briefing types out
  // Phase 3: health ring + metrics
  // Phase 4: projects + focus
  // Phase 5: command bar (complete)
  const [activated, setActivated] = useState(false);
  const [interacting, setInteracting] = useState(false);

  const { data, isLoading } = useQuery<HomeData>({
    queryKey: ['home'],
    queryFn: () => apiFetch<HomeData>('/home'),
    refetchInterval: 60000,
  });

  // Fetch smart briefing from backend (delta-aware, Jarvis personality)
  // Re-fetch every 5 minutes so returning to Jarvis page gets fresh delta
  const { data: briefingData } = useQuery<BriefingResponse>({
    queryKey: ['home-briefing'],
    queryFn: () => apiFetch<BriefingResponse>('/home/briefing'),
    enabled: !!data,
    staleTime: 5 * 60 * 1000,
  });
  const briefing = briefingData?.script ?? '';

  const dataReady = !isLoading && !!data && !!briefing;

  // Stable refs for values used inside the effect (avoid dependency churn)
  const audioRef = useRef(audio);
  audioRef.current = audio;
  const briefingRef = useRef(briefing);
  briefingRef.current = briefing;

  // Start the sequence after user clicks (unlocks audio)
  const hasPlayed = useRef(false);
  useEffect(() => {
    if (!activated || !dataReady || hasPlayed.current) return;
    hasPlayed.current = true;

    const a = audioRef.current;
    const b = briefingRef.current;
    const timers: ReturnType<typeof setTimeout>[] = [];

    // Phase 1: Logo — start prefetching TTS audio
    timers.push(setTimeout(() => {
      setPhase(1);
      a.prefetch(b);
    }, 300));
    // Phase 2: Briefing starts — audio is pre-fetched, plays instantly
    timers.push(setTimeout(() => {
      setPhase(2);
      a.chime();
      timers.push(setTimeout(() => a.speak(b), 200));
    }, 1200));
    // Phase 3: Health ring + metrics
    timers.push(setTimeout(() => { setPhase(3); a.blip(); }, 3500));
    // Phase 4: Projects + focus
    timers.push(setTimeout(() => { setPhase(4); a.blip(); }, 5000));
    // Phase 5: Command bar (ambient already playing from activation)
    timers.push(setTimeout(() => setPhase(5), 6500));

    return () => timers.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activated, dataReady]);

  // ─── Command handler (feeds cards to canvas) ──────────────────────────────
  const handleCommand = useCallback(async (text: string): Promise<CommandResponse> => {
    const result = await apiPost<CommandResponse>('/jarvis/command', { text });
    // Only activate canvas for data cards, not simple text responses or navigation hints
    const dataCards = (result.cards ?? []).filter(
      (c) => c.type !== 'text_response' && c.type !== 'navigate_hint'
    );
    if (dataCards.length > 0) {
      canvas.showCards(dataCards);
    } else if (result.cards?.length === 0 || text.toLowerCase().includes('dismiss') || text.toLowerCase().includes('clear')) {
      canvas.dismiss();
    }
    return result;
  }, [canvas]);

  // Dedupe + sort todos
  const focusTodos = useMemo(() => {
    if (!data) return [];
    const all = [...(data?.todos?.overdue ?? []), ...(data?.todos?.high_priority ?? []), ...(data?.todos?.medium_priority ?? [])];
    const seen = new Set<string>();
    return all.filter((t) => {
      if (seen.has(t.id)) return false;
      seen.add(t.id);
      return true;
    }).slice(0, 8);
  }, [data]);

  const overdueIds = useMemo(
    () => new Set(data?.todos?.overdue?.map((t) => t.id) ?? []),
    [data]
  );

  const activeProjects = useMemo(
    () => (data?.projects ?? [])
      .filter((p) => p.active && (p.item_count > 0 || p.todo_open > 0))
      .sort((a, b) => b.todo_open - a.todo_open)
      .slice(0, 8),
    [data]
  );

  // Activation screen — user click unlocks audio playback (browser requirement)
  if (!activated) {
    return (
      <div
        className="jarvis-bg min-h-screen flex flex-col items-center justify-center cursor-pointer select-none"
        onClick={() => setActivated(true)}
      >
        {!dataReady ? (
          <div className="flex gap-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-sky-400/60"
                style={{ animation: `jarvis-pulse-dot 1.5s ease-in-out ${i * 0.2}s infinite` }}
              />
            ))}
          </div>
        ) : (
          <div className="text-center space-y-4 animate-pulse">
            <div className="w-16 h-16 mx-auto rounded-full border border-white/10 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-[#0A84FF] shadow-none" />
            </div>
            <p className="text-sm font-mono text-white/30 tracking-widest uppercase">
              Click to activate
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="jarvis-bg min-h-screen px-4 sm:px-6 md:px-8 py-10 space-y-8 overflow-y-auto overflow-x-hidden relative">
      {/* Minimal top bar */}
      <div className="jarvis-reveal absolute top-4 left-6 right-6 flex items-center justify-between" style={{ '--reveal-delay': '6000ms' } as React.CSSProperties}>
        <Link to="/" className="text-xs font-mono text-white/30 hover:text-white/60 transition-colors">
          ← Back to CoCo
        </Link>
        <span className="text-[10px] font-mono text-white/30">
          {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
        </span>
      </div>
      {/* Phase 1: Logo */}
      <div className="pt-4">
        <CocoLogo visible={phase >= 1} />
      </div>

      {/* Reactive Canvas — replaces static phases when commands produce cards */}
      {!canvas.isIdle ? (
        <ReactiveCanvas
          cards={canvas.cards}
          mode={canvas.mode}
          previousCards={canvas.previousCards}
        />
      ) : (
        <>
          {/* Phase 2: Cinematic briefing sequence — fades when user starts interacting */}
          {phase >= 2 && (
            <div
              className="transition-all duration-700 ease-out"
              style={{
                opacity: interacting ? 0 : 1,
                maxHeight: interacting ? 0 : 600,
                overflow: 'hidden',
              }}
            >
              <BriefingSequence
                scenes={briefingData?.scenes ?? []}
                enabled={phase >= 2}
                isSpeaking={isSpeaking}
              />
            </div>
          )}

          {/* Phase 3: Health Ring + Metrics */}
          {phase >= 3 && data && (
            <div className="flex items-center justify-center gap-8 flex-wrap">
              <HealthRing sources={data.health ?? []} size={160} delay={0} />
              <div className="glass-panel p-6 rounded-2xl flex gap-8">
                <MetricCard label="Open Todos" value={data.todos.total_open} delay={200} />
                <MetricCard label="High Priority" value={data.todos.high_priority.length} delay={400} color="text-[#FF453A]" />
                <MetricCard label="Pending Drafts" value={data.attention.pending_drafts} delay={600} />
                <MetricCard label="Unsorted" value={data.attention.unsorted_count} delay={800} color="text-white/40" />
              </div>
            </div>
          )}

          {/* Phase 4: Projects + Focus */}
          {phase >= 4 && (
            <div className="grid grid-cols-12 gap-6 max-w-5xl mx-auto">
              <GlassCard className="col-span-12 lg:col-span-7 p-4" delay={0} glow>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs uppercase tracking-widest text-sky-400/60 font-mono">Projects</h3>
                  <span className="text-[10px] text-slate-600 font-mono">{activeProjects.length} active</span>
                </div>
                <div className="space-y-0.5">
                  {activeProjects.map((p, i) => (
                    <ProjectRow key={p.id} project={p} index={i} delay={100 + i * 80} />
                  ))}
                </div>
              </GlassCard>

              <GlassCard className="col-span-12 lg:col-span-5 p-4" delay={200} glow>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs uppercase tracking-widest text-sky-400/60 font-mono">Focus</h3>
                  <span className="text-[10px] text-slate-600 font-mono">{focusTodos.length} items</span>
                </div>
                <div className="space-y-0.5">
                  {focusTodos.map((t) => (
                    <FocusItem key={t.id} todo={t} isOverdue={overdueIds.has(t.id)} />
                  ))}
                  {focusTodos.length === 0 && (
                    <p className="text-xs text-slate-600 italic">All clear. Nothing urgent.</p>
                  )}
                </div>
              </GlassCard>
            </div>
          )}
        </>
      )}

      {/* Phase 5: Command bar */}
      {/* Phase 5: Voice/text input — talk back to CoCo */}
      {phase >= 5 && (
        <JarvisInput
          onCommand={handleCommand}
          onSpeak={(text) => audioRef.current.speak(text)}
          onChime={() => audioRef.current.chime()}
          onInteract={() => { setInteracting(true); audioRef.current.cancelSpeak(); }}
          delay={0}
        />
      )}

    </div>
  );
}
