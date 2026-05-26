import { AlertTriangle } from 'lucide-react';

interface ErrorStateProps {
  /** The error object/string from the query. */
  error?: unknown;
  /** Headline. Defaults to "Something went wrong". */
  title?: string;
  /** Override the auto-extracted error message. */
  description?: string;
  /** Retry handler. If provided, renders a Retry button. */
  onRetry?: () => void;
  /** Label for the retry button. */
  retryLabel?: string;
  /** Test id for E2E hooks. */
  testId?: string;
  className?: string;
}

function extractMessage(err: unknown): string {
  if (!err) return 'An unexpected error occurred.';
  if (typeof err === 'string') return err;
  if (err instanceof Error) return err.message;
  if (typeof err === 'object' && err !== null && 'message' in err) {
    const m = (err as { message: unknown }).message;
    if (typeof m === 'string') return m;
  }
  return 'An unexpected error occurred.';
}

/**
 * Shared error state for failed queries. Pairs with a retry callback (typically
 * `query.refetch`). Differs from `<ErrorBoundary>` in that this handles
 * *expected* failure modes (e.g. 5xx from API) without unmounting the page.
 */
export function ErrorState({
  error,
  title = 'Something went wrong',
  description,
  onRetry,
  retryLabel = 'Retry',
  testId = 'error-state',
  className = '',
}: ErrorStateProps) {
  const message = description ?? extractMessage(error);

  return (
    <div
      data-testid={testId}
      role="alert"
      className={`flex flex-col items-center justify-center gap-3 rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-10 text-center ${className}`}
    >
      <div className="text-destructive">
        <AlertTriangle className="h-10 w-10" />
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="max-w-md text-sm text-muted-foreground">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 transition-colors"
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
}

export default ErrorState;
