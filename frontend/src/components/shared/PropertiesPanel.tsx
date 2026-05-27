import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

/**
 * Reusable right-side slide-out properties panel.
 *
 * Built on top of Radix Dialog for accessibility (focus trap, Esc to close,
 * proper ARIA), but rendered as a right-anchored sheet instead of a centered
 * modal. Slides in from the right via a Tailwind transform transition.
 *
 * Width may be provided as a fixed pixel number (default 420) or as one of
 * the legacy presets (`'sm' | 'md' | 'lg'`) for backward compatibility with
 * existing call sites.
 */

const widthPresetPx: Record<'sm' | 'md' | 'lg', number> = {
  sm: 320,
  md: 400,
  lg: 480,
};

export interface PropertiesPanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  width?: number | 'sm' | 'md' | 'lg';
}

function resolveWidth(width: PropertiesPanelProps['width']): number {
  if (typeof width === 'number') return width;
  if (width && width in widthPresetPx) return widthPresetPx[width];
  return 420;
}

export function PropertiesPanel({
  open,
  onClose,
  title,
  subtitle,
  children,
  width = 420,
}: PropertiesPanelProps) {
  // Track whether the panel should be visually "in" (translate-x-0).
  // We render the Dialog only while `open` is true, but on first paint we
  // flip `entered` to true so the transform transitions from translate-x-full
  // -> translate-x-0 instead of snapping into place.
  const [entered, setEntered] = useState(false);

  useEffect(() => {
    if (!open) {
      setEntered(false);
      return;
    }
    // requestAnimationFrame ensures the initial frame uses translate-x-full
    // and the next frame transitions to translate-x-0.
    const raf = requestAnimationFrame(() => setEntered(true));
    return () => cancelAnimationFrame(raf);
  }, [open]);

  const widthPx = resolveWidth(width);
  const panelStyle: CSSProperties = {
    width: `${widthPx}px`,
    maxWidth: 'calc(100vw - 3.5rem)',
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) onClose();
  };

  return (
    <Dialog.Root open={open} onOpenChange={handleOpenChange} modal>
      <Dialog.Portal>
        {/* Backdrop — click closes via Radix's onPointerDownOutside on Content */}
        <Dialog.Overlay
          className={cn(
            'fixed inset-0 z-40 bg-black/20 transition-opacity duration-200',
            entered ? 'opacity-100' : 'opacity-0',
          )}
        />

        {/* Right-side panel. We override Radix's default centering by
            explicitly pinning to the right edge. */}
        <Dialog.Content
          aria-describedby={undefined}
          style={panelStyle}
          className={cn(
            'fixed inset-y-0 right-0 z-50 flex flex-col bg-card border-l border-border shadow-2xl',
            'transition-transform duration-200 ease-out will-change-transform',
            entered ? 'translate-x-0' : 'translate-x-full',
            'focus:outline-none',
          )}
        >
          {/* Sticky header */}
          <div className="sticky top-0 z-10 flex items-start justify-between gap-3 p-5 border-b border-border bg-card">
            <div className="min-w-0">
              <Dialog.Title className="text-lg font-semibold text-foreground truncate">
                {title}
              </Dialog.Title>
              {subtitle && (
                <p className="text-xs text-muted-foreground mt-0.5 truncate">{subtitle}</p>
              )}
            </div>
            <Dialog.Close
              aria-label="Close panel"
              className="p-1 rounded-lg hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors shrink-0"
            >
              <X className="h-5 w-5" />
            </Dialog.Close>
          </div>

          {/* Scrollable body */}
          <div className="flex-1 overflow-y-auto p-5">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
