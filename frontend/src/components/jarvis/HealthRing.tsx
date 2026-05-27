interface HealthRingProps {
  sources: Array<{ source: string; status: string; stale_hours: number | null }>;
  size?: number;
  delay?: number;
}

function sourceScore(s: { stale_hours: number | null; status: string }): number {
  if (s.stale_hours != null) {
    if (s.stale_hours < 2) return 100;
    if (s.stale_hours < 12) return 80;
    if (s.stale_hours < 24) return 60;
    if (s.stale_hours < 72) return 30;
    return 10;
  }
  const map: Record<string, number> = { green: 100, ok: 100, yellow: 60, warn: 60, red: 20, critical: 0 };
  return map[s.status] ?? 50;
}

function sourceColor(s: { stale_hours: number | null; status: string }): string {
  if (s.stale_hours != null) {
    if (s.stale_hours < 12) return '#34C759';
    if (s.stale_hours < 24) return '#FF9F0A';
    return '#FF453A';
  }
  const map: Record<string, string> = { green: '#34C759', ok: '#34C759', yellow: '#FF9F0A', warn: '#FF9F0A', red: '#FF453A', critical: '#FF453A' };
  return map[s.status] ?? '#8E8E93';
}

const SOURCE_LABELS: Record<string, string> = {
  email: 'Email',
  voice: 'Voice',
  jira: 'Jira',
  confluence: 'Conf',
};

export function HealthRing({ sources, size = 160, delay = 0 }: HealthRingProps) {
  const center = size / 2;
  const radius = size * 0.38;
  const strokeWidth = 6;
  const circumference = 2 * Math.PI * radius;

  const total = sources.reduce((acc, s) => acc + sourceScore(s), 0);
  const pct = sources.length > 0 ? Math.round(total / sources.length) : 100;
  const offset = circumference * (1 - pct / 100);
  const overallColor = pct >= 70 ? '#0A84FF' : pct >= 40 ? '#FF9F0A' : '#FF453A';

  // Tailwind v4 drop-shadow-* utilities regressed for SVG stroke glow (filter origin/color
  // semantics changed; `drop-shadow-lg` no longer renders an arc glow reliably). Use an
  // inline SVG <filter> + CSS var instead — works the same on Safari/Chrome regardless of
  // Tailwind version. See NEXT_SPRINT_PLAN.md §3.7.
  const filterId = `health-ring-glow-${size}`;

  return (
    <div
      className="jarvis-reveal inline-flex flex-col items-center gap-4"
      style={{ '--reveal-delay': `${delay}ms`, '--ring-glow': overallColor } as React.CSSProperties}
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="transform -rotate-90">
          <defs>
            <filter id={filterId} x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <circle
            cx={center} cy={center} r={radius}
            fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={strokeWidth}
          />
          <circle
            cx={center} cy={center} r={radius}
            fill="none" stroke={overallColor} strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            filter={`url(#${filterId})`}
            style={{ transition: 'stroke-dashoffset 1.5s ease-out 0.3s' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-semibold text-white/90 tabular-nums">{pct}</span>
          <span className="text-[10px] text-white/40 mt-0.5">health</span>
        </div>
      </div>
      <div className="flex gap-4">
        {sources.map((s) => (
          <div key={s.source} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: sourceColor(s) }} />
            <span className="text-[11px] text-white/50">{SOURCE_LABELS[s.source] ?? s.source}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
