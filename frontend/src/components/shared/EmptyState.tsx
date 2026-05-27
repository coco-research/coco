import { type ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  /** Headline text. Defaults to "Nothing yet". */
  title?: string;
  /** Optional sub-copy under the title. */
  description?: string;
  /** Optional icon node. Defaults to an Inbox icon. */
  icon?: ReactNode;
  /** Optional primary CTA. */
  actionLabel?: string;
  onAction?: () => void;
  /** Optional render-prop slot for a custom CTA (e.g. <Link/>). */
  action?: ReactNode;
  /** Test id for E2E hooks. */
  testId?: string;
  className?: string;
}

/**
 * Shared empty-state for any page/section whose primary query returns [].
 * Use a friendly title + optional CTA so the user knows what to do next.
 */
export function EmptyState({
  title = 'Nothing yet',
  description,
  icon,
  actionLabel,
  onAction,
  action,
  testId = 'empty-state',
  className = '',
}: EmptyStateProps) {
  const renderedAction =
    action ??
    (actionLabel && onAction ? (
      <button
        onClick={onAction}
        className="mt-4 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 transition-colors"
      >
        {actionLabel}
      </button>
    ) : null);

  return (
    <div
      data-testid={testId}
      className={`flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-muted-foreground/20 bg-muted/20 px-6 py-12 text-center ${className}`}
    >
      <div className="text-muted-foreground/60">
        {icon ?? <Inbox className="h-10 w-10" />}
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      {description && (
        <p className="max-w-md text-sm text-muted-foreground">{description}</p>
      )}
      {renderedAction}
    </div>
  );
}

export default EmptyState;
