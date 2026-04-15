import { useState, useEffect, useRef } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { cn } from '../../lib/utils';

interface BriefingItem {
  label: string;
  value: string;
  detail?: string;
  severity?: string;
}

interface BriefingSection {
  title: string;
  icon: string;
  items: BriefingItem[];
}

interface BriefingData {
  sections: BriefingSection[];
  highlights: string[];
}

interface AttentionBadgeProps {
  briefingData: BriefingData | null;
}

export function AttentionBadge({ briefingData }: AttentionBadgeProps) {
  const [open, setOpen] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);

  // Escape key to dismiss + auto-focus close button
  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open]);

  if (!briefingData) return null;

  // Extract attention items from the "Attention Needed" section
  const attentionSection = briefingData.sections.find((s) => s.title === 'Attention Needed');
  if (!attentionSection) return null;

  const criticalItems = attentionSection.items.filter((i) => i.severity === 'critical');
  const warningItems = attentionSection.items.filter((i) => i.severity === 'warning');
  const totalCount = criticalItems.length + warningItems.length;

  // Don't show badge if "All clear"
  if (totalCount === 0 || attentionSection.items.some((i) => i.label === 'All clear')) {
    return null;
  }

  const hasCritical = criticalItems.length > 0;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        aria-haspopup="true"
        aria-expanded={open}
        aria-label={`${totalCount} item${totalCount !== 1 ? 's' : ''} need attention`}
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors',
          hasCritical
            ? 'bg-red-100 dark:bg-red-950/30 text-red-700 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-950/50'
            : 'bg-amber-100 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-950/50',
        )}
      >
        <AlertTriangle className="h-3.5 w-3.5" />
        {totalCount} attention
      </button>

      {/* Flyout popover */}
      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />

          {/* Panel */}
          <div className="absolute right-0 top-full mt-1 z-50 w-80 bg-card border border-border rounded-lg shadow-lg overflow-hidden">
            <div className="flex items-center justify-between px-3 py-2 border-b border-border">
              <span className="text-sm font-medium">Needs Attention</span>
              <button
                ref={closeRef}
                onClick={() => setOpen(false)}
                aria-label="Close attention panel"
                className="p-1 rounded hover:bg-muted transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="p-3 space-y-2 max-h-64 overflow-auto">
              {criticalItems.map((item) => (
                <div key={`c-${item.label}-${item.value}`} className="flex items-start gap-2 p-2 rounded bg-red-50 dark:bg-red-950/20">
                  <AlertTriangle className="h-3.5 w-3.5 text-red-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-red-700 dark:text-red-400">{item.label}</p>
                    <p className="text-xs text-red-600 dark:text-red-500">{item.value}</p>
                    {item.detail && <p className="text-xs text-muted-foreground mt-0.5">{item.detail}</p>}
                  </div>
                </div>
              ))}
              {warningItems.map((item) => (
                <div key={`w-${item.label}-${item.value}`} className="flex items-start gap-2 p-2 rounded bg-amber-50 dark:bg-amber-950/20">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-700 dark:text-amber-400">{item.label}</p>
                    <p className="text-xs text-amber-600 dark:text-amber-500">{item.value}</p>
                    {item.detail && <p className="text-xs text-muted-foreground mt-0.5">{item.detail}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
