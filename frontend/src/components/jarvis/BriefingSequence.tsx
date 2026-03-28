import { useState, useEffect, useMemo } from 'react';
import { useTypewriter } from '../../hooks/useTypewriter';
import { useCountUp } from '../../hooks/useCountUp';
import { cn } from '../../lib/utils';
import { apiPost } from '../../lib/api';

export interface BriefingScene {
  type: 'greeting' | 'context' | 'alert' | 'action' | 'metric' | 'quip' | 'status' | 'spotlight';
  text: string;
  severity?: 'high' | 'medium' | 'low';
  sources?: string[];
  action?: string;
  value?: number;
  label?: string;
  project?: string;
}

interface Props {
  scenes: BriefingScene[];
  enabled: boolean;
  isSpeaking?: boolean;
  onAllRevealed?: () => void;
}

// Timing: each scene reveals after the previous scene's text finishes typing + a hold
function estimateDelay(scenes: BriefingScene[], index: number): number {
  if (index === 0) return 0;
  let cumulativeMs = 0;
  for (let i = 0; i < index; i++) {
    const scene = scenes[i];
    const charCount = scene.text.length;
    const typeTime = scene.type === 'quip' ? 600 : charCount * 28 + 100; // quips fade, don't type
    const holdTime = scene.type === 'greeting' ? 1500 : 300;
    cumulativeMs += typeTime + holdTime;
  }
  return cumulativeMs;
}

// ─── Scene Renderers ─────────────────────────────────────────────────────────

function GreetingScene({ text, visible }: { text: string; visible: boolean }) {
  return (
    <div
      className="transition-all duration-1000 ease-out text-center mt-2 mb-4"
      style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(12px)' }}
    >
      <h1 className="text-3xl font-light text-white/90 tracking-wide">{text}</h1>
      <p className="text-[11px] font-mono text-white/30 mt-1.5 tracking-widest">
        {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
        {' · '}
        {new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
      </p>
    </div>
  );
}

function TypedScene({ text, visible, className }: { text: string; visible: boolean; className?: string }) {
  const { displayed, isDone } = useTypewriter(text, 28, { enabled: visible, delay: 100 });
  if (!visible) return null;
  return (
    <p className={cn('text-sm leading-relaxed', className)}>
      {displayed}
      {!isDone && <span className="inline-block w-0.5 h-3.5 bg-white/40 ml-0.5 animate-pulse" />}
    </p>
  );
}

function AlertScene({ scene, visible }: { scene: BriefingScene; visible: boolean }) {
  const colorMap = { high: 'text-[#FF453A]', medium: 'text-[#FF9F0A]', low: 'text-[#FFD60A]' };
  const dotColor = {
    high: 'bg-[#FF453A]',
    medium: 'bg-[#FF9F0A]',
    low: 'bg-[#FFD60A]',
  };
  const severity = scene.severity ?? 'medium';

  return (
    <div className="flex items-start gap-3 justify-center">
      <div className="mt-2 shrink-0">
        <div className={cn('w-1.5 h-1.5 rounded-full', dotColor[severity])} />
      </div>
      <TypedScene text={scene.text} visible={visible} className={colorMap[severity]} />
    </div>
  );
}

function ActionScene({ scene, visible }: { scene: BriefingScene; visible: boolean }) {
  const { displayed, isDone } = useTypewriter(scene.text, 28, { enabled: visible, delay: 100 });
  if (!visible) return null;

  const handleAction = async () => {
    if (scene.action === 'process') {
      await apiPost('/home/process', {});
    }
  };

  return (
    <div className="flex items-center gap-3 justify-center">
      <p className="text-sm text-white/50 leading-relaxed">
        {displayed}
        {!isDone && <span className="inline-block w-0.5 h-3.5 bg-white/40 ml-0.5 animate-pulse" />}
      </p>
      {isDone && scene.action && (
        <button
          onClick={handleAction}
          className="shrink-0 bg-[#0A84FF] text-white text-[10px] font-medium rounded-lg px-3 py-1 hover:bg-[#0A84FF]/80 transition-all"
        >
          {scene.action}
        </button>
      )}
    </div>
  );
}

function MetricScene({ scene, visible }: { scene: BriefingScene; visible: boolean }) {
  const { displayed, isDone } = useTypewriter(scene.text, 28, { enabled: visible, delay: 100 });

  // Start countup only when typewriter reaches a digit
  const numberReached = useMemo(() => {
    if (!displayed) return false;
    return /\d/.test(displayed);
  }, [displayed]);

  const count = useCountUp(scene.value ?? 0, 1200, { enabled: numberReached, delay: 0 });

  if (!visible) return null;

  // Replace the first numeric value in displayed text with animated count
  const parts = displayed.split(/(\d+)/);
  let replaced = false;

  return (
    <p className="text-sm text-white/60 leading-relaxed">
      {parts.map((part, i) => {
        if (!replaced && /^\d+$/.test(part) && scene.value != null) {
          replaced = true;
          return (
            <span key={i} className="font-mono font-bold text-[#0A84FF]">
              {count.toLocaleString()}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
      {!isDone && <span className="inline-block w-0.5 h-3.5 bg-white/40 ml-0.5 animate-pulse" />}
    </p>
  );
}

function QuipScene({ text, visible }: { text: string; visible: boolean }) {
  if (!visible) return null;
  return (
    <p
      className="text-sm text-white/30 italic leading-relaxed jarvis-reveal"
      style={{ '--reveal-delay': '0ms' } as React.CSSProperties}
    >
      {text}
    </p>
  );
}

function SpotlightScene({ scene, visible }: { scene: BriefingScene; visible: boolean }) {
  const { displayed, isDone } = useTypewriter(scene.text, 28, { enabled: visible, delay: 100 });
  if (!visible) return null;

  // Highlight the project name (text before " — " or " has " or " is ")
  const splitAt = scene.text.search(/ (—|has|is) /);
  const projectPart = splitAt > 0 ? scene.text.slice(0, splitAt) : '';

  return (
    <p className="text-sm text-white/60 leading-relaxed">
      {projectPart && displayed.length >= projectPart.length ? (
        <>
          <span className="text-[#0A84FF] font-medium">
            {displayed.slice(0, projectPart.length)}
          </span>
          <span>{displayed.slice(projectPart.length)}</span>
        </>
      ) : (
        <span>{displayed}</span>
      )}
      {!isDone && <span className="inline-block w-0.5 h-3.5 bg-white/40 ml-0.5 animate-pulse" />}
    </p>
  );
}

// ─── Audio Waveform ──────────────────────────────────────────────────────────

function Waveform({ active }: { active: boolean }) {
  return (
    <div className="flex items-end gap-[2px] h-4 justify-center mt-4 mb-1">
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className={cn(
            'w-[2px] h-[3px] rounded-full transition-all duration-500 origin-bottom will-change-transform',
            active ? 'bg-white/40' : 'bg-white/10',
          )}
          style={{
            transform: active ? undefined : 'scaleY(1)',
            animation: active ? `jarvis-waveform ${0.4 + i * 0.1}s ease-in-out infinite alternate` : 'none',
          }}
        />
      ))}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export function BriefingSequence({ scenes, enabled, isSpeaking, onAllRevealed }: Props) {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    if (!enabled || scenes.length === 0) return;

    const timers: ReturnType<typeof setTimeout>[] = [];
    scenes.forEach((_, i) => {
      const delay = estimateDelay(scenes, i);
      timers.push(setTimeout(() => {
        setVisibleCount(i + 1);
        if (i === scenes.length - 1) {
          const lastCharCount = scenes[i].text.length;
          const lastTypeTime = lastCharCount * 28 + 100;
          timers.push(setTimeout(() => onAllRevealed?.(), lastTypeTime + 500));
        }
      }, delay));
    });

    return () => timers.forEach(clearTimeout);
  }, [enabled, scenes, onAllRevealed]);

  // Track active alert severity for foreshadowing glow
  const activeAlertSeverity = useMemo(() => {
    for (let i = visibleCount - 1; i >= 0; i--) {
      if (scenes[i]?.type === 'alert') return scenes[i].severity ?? 'medium';
    }
    return null;
  }, [visibleCount, scenes]);

  return (
    <div className="max-w-2xl mx-auto space-y-3 text-center relative">
      {/* Foreshadowing glow behind content during alerts */}
      {activeAlertSeverity && (
        <div
          className={cn(
            'absolute inset-0 -m-8 rounded-3xl pointer-events-none transition-opacity duration-1000',
            activeAlertSeverity === 'high' && 'bg-[#FF453A]/[0.03]',
            activeAlertSeverity === 'medium' && 'bg-[#FF9F0A]/[0.02]',
            activeAlertSeverity === 'low' && 'bg-[#FFD60A]/[0.01]',
          )}
        />
      )}

      {scenes.map((scene, i) => {
        const visible = i < visibleCount;
        const isPostGreeting = i === 1 && scenes[0]?.type === 'greeting';
        return (
          <div key={i}>
            {/* Thin divider after greeting */}
            {isPostGreeting && visible && (
              <div className="w-16 h-px bg-white/10 mx-auto my-3 transition-opacity duration-500" />
            )}
            {scene.type === 'greeting' && <GreetingScene text={scene.text} visible={visible} />}
            {scene.type === 'context' && <TypedScene text={scene.text} visible={visible} className="text-white/50" />}
            {scene.type === 'alert' && <AlertScene scene={scene} visible={visible} />}
            {scene.type === 'action' && <ActionScene scene={scene} visible={visible} />}
            {scene.type === 'metric' && <MetricScene scene={scene} visible={visible} />}
            {scene.type === 'quip' && <QuipScene text={scene.text} visible={visible} />}
            {scene.type === 'status' && <TypedScene text={scene.text} visible={visible} className="text-white/50" />}
            {scene.type === 'spotlight' && <SpotlightScene scene={scene} visible={visible} />}
          </div>
        );
      })}

      <Waveform active={isSpeaking ?? false} />
    </div>
  );
}
