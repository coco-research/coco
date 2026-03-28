import { cn } from '../../lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  glow?: boolean;
}

export function GlassCard({ children, className, delay = 0, glow = false }: GlassCardProps) {
  return (
    <div
      className={cn(
        'jarvis-reveal glass-panel p-5',
        glow && 'glass-panel-elevated',
        className,
      )}
      style={{ '--reveal-delay': `${delay}ms` } as React.CSSProperties}
    >
      <div className="relative z-10">{children}</div>
    </div>
  );
}
