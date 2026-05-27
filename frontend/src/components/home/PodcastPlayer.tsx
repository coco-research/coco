import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Pause, Play, Volume2, VolumeX, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../../lib/utils';

interface PodcastPlayerProps {
  audioUrl: string | null;
  script: string | null;
  duration: number | null;
  title: string;
}

const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5];
const BAR_COUNT = 32;

export function PodcastPlayer({ audioUrl, script, duration }: PodcastPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(duration ?? 0);
  const [speed, setSpeed] = useState(1);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const [showScript, setShowScript] = useState(false);
  const progressRef = useRef<HTMLDivElement>(null);

  // Generate random bar heights for waveform visualization
  const barHeights = useMemo(
    () => Array.from({ length: BAR_COUNT }, () => 0.2 + Math.random() * 0.8),
    []
  );

  // Audio event listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onLoadedMetadata = () => {
      if (audio.duration && isFinite(audio.duration)) {
        setTotalDuration(audio.duration);
      }
    };
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('loadedmetadata', onLoadedMetadata);
    audio.addEventListener('ended', onEnded);

    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('loadedmetadata', onLoadedMetadata);
      audio.removeEventListener('ended', onEnded);
    };
  }, [audioUrl]);

  // Sync speed
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = speed;
  }, [speed]);

  // Sync volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  const togglePlay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play().catch(() => {});
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleProgressClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const audio = audioRef.current;
      const bar = progressRef.current;
      if (!audio || !bar || !totalDuration) return;
      const rect = bar.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(1, x / rect.width));
      audio.currentTime = pct * totalDuration;
    },
    [totalDuration]
  );

  const cycleSpeed = useCallback(() => {
    setSpeed((prev) => {
      const idx = SPEED_OPTIONS.indexOf(prev);
      return SPEED_OPTIONS[(idx + 1) % SPEED_OPTIONS.length];
    });
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const progress = totalDuration > 0 ? currentTime / totalDuration : 0;

  if (!audioUrl) {
    // Script-only mode
    if (!script) return null;
    return (
      <div className="space-y-3">
        <button
          onClick={() => setShowScript(!showScript)}
          className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <FileText size={12} />
          {showScript ? 'Hide' : 'Read'} Script
          {showScript ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
        {showScript && (
          <div className="rounded-lg bg-muted/30 p-4 text-sm text-foreground/80 whitespace-pre-line max-h-64 overflow-y-auto animate-in fade-in slide-in-from-top-1 duration-200">
            {script}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Hidden audio element */}
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Waveform + controls */}
      <div className="rounded-xl bg-gradient-to-br from-accent/40 to-accent/20 p-4 border border-border/50">
        {/* Waveform visualization */}
        <div className="flex items-end gap-[2px] h-10 mb-3">
          {barHeights.map((h, i) => {
            const barProgress = i / BAR_COUNT;
            const isPast = barProgress < progress;
            const isActive = isPlaying && isPast;
            return (
              <div
                key={i}
                className={cn(
                  'flex-1 rounded-full transition-all duration-150',
                  isPast ? 'bg-foreground/70' : 'bg-foreground/15',
                  isActive && 'animate-pulse'
                )}
                style={{
                  height: `${h * 100}%`,
                  animationDelay: isActive ? `${i * 30}ms` : undefined,
                  animationDuration: isActive ? '400ms' : undefined,
                }}
              />
            );
          })}
        </div>

        {/* Controls row */}
        <div className="flex items-center gap-3">
          {/* Play/Pause */}
          <button
            type="button"
            onClick={togglePlay}
            aria-label={isPlaying ? 'Pause' : 'Play'}
            aria-pressed={isPlaying}
            className="w-9 h-9 rounded-full bg-foreground text-background flex items-center justify-center hover:opacity-90 transition-opacity shrink-0"
          >
            {isPlaying ? <Pause size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" className="ml-0.5" />}
          </button>

          {/* Progress bar */}
          <div
            ref={progressRef}
            onClick={handleProgressClick}
            className="flex-1 h-1.5 rounded-full bg-foreground/10 cursor-pointer group relative"
          >
            <div
              className="h-full rounded-full bg-foreground/60 transition-all duration-100"
              style={{ width: `${progress * 100}%` }}
            />
            <div
              className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-foreground opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ left: `calc(${progress * 100}% - 6px)` }}
            />
          </div>

          {/* Time */}
          <span className="text-[11px] text-muted-foreground tabular-nums shrink-0 min-w-[72px] text-right">
            {formatTime(currentTime)} / {formatTime(totalDuration)}
          </span>
        </div>

        {/* Secondary controls */}
        <div className="flex items-center justify-between mt-2.5">
          <div className="flex items-center gap-2">
            {/* Speed */}
            <button
              onClick={cycleSpeed}
              className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-foreground/5 text-muted-foreground hover:text-foreground hover:bg-foreground/10 transition-colors"
            >
              {speed}x
            </button>

            {/* Volume */}
            <button
              type="button"
              onClick={() => setIsMuted(!isMuted)}
              aria-label={isMuted || volume === 0 ? 'Unmute' : 'Mute'}
              aria-pressed={isMuted}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {isMuted || volume === 0 ? <VolumeX size={14} aria-hidden="true" /> : <Volume2 size={14} aria-hidden="true" />}
            </button>
            <input
              type="range"
              aria-label="Volume"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={(e) => {
                setVolume(parseFloat(e.target.value));
                if (isMuted) setIsMuted(false);
              }}
              className="w-16 h-1 accent-foreground/60"
            />
          </div>

          {/* Script toggle */}
          {script && (
            <button
              onClick={() => setShowScript(!showScript)}
              className={cn(
                'flex items-center gap-1.5 text-[11px] px-2 py-0.5 rounded-md transition-colors',
                showScript
                  ? 'bg-foreground/10 text-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-foreground/5'
              )}
            >
              <FileText size={11} />
              Script
              {showScript ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            </button>
          )}
        </div>
      </div>

      {/* Script text */}
      {showScript && script && (
        <div className="rounded-lg bg-muted/30 p-4 text-sm text-foreground/80 whitespace-pre-line max-h-64 overflow-y-auto animate-in fade-in slide-in-from-top-1 duration-200">
          {script}
        </div>
      )}
    </div>
  );
}
