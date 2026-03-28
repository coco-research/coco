import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

const widthMap = { sm: 'w-80', md: 'w-[400px]', lg: 'w-[480px]' } as const;

interface PropertiesPanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  width?: 'sm' | 'md' | 'lg';
}

export function PropertiesPanel({
  open,
  onClose,
  title,
  subtitle,
  children,
  width = 'md',
}: PropertiesPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Escape to close
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // Focus trap
  useEffect(() => {
    if (!open) return;
    const panel = panelRef.current;
    if (!panel) return;

    const previouslyFocused = document.activeElement as HTMLElement;
    const focusableSelector =
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

    const focusFirst = () => {
      const first = panel.querySelector<HTMLElement>(focusableSelector);
      first?.focus();
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const focusable = Array.from(
        panel.querySelectorAll<HTMLElement>(focusableSelector),
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    focusFirst();
    panel.addEventListener('keydown', handleKeyDown);
    return () => {
      panel.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [open]);

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/20 z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className={cn(
          'fixed inset-y-0 right-0 max-w-[calc(100vw-3.5rem)] bg-card border-l border-border shadow-2xl z-50 flex flex-col animate-slide-in',
          widthMap[width],
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 p-5 border-b border-border">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-foreground truncate">{title}</h2>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-0.5 truncate">{subtitle}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors shrink-0"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
      </div>
    </>
  );
}
