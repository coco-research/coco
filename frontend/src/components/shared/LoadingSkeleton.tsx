interface LoadingSkeletonProps {
  /** Visual variant. */
  variant?: 'list' | 'grid' | 'card' | 'page';
  /** Number of skeleton items to render (for list/grid/card variants). */
  count?: number;
  /** Test id for E2E hooks. */
  testId?: string;
  className?: string;
}

/**
 * Shared loading skeleton. Use while a query is `isLoading`/`isPending` for the
 * first time. For background refetches, prefer to keep the previous data and
 * show a subtle indicator elsewhere.
 */
export function LoadingSkeleton({
  variant = 'list',
  count = 4,
  testId = 'loading-skeleton',
  className = '',
}: LoadingSkeletonProps) {
  if (variant === 'page') {
    return (
      <div
        data-testid={testId}
        className={`space-y-6 ${className}`}
        aria-busy="true"
        aria-live="polite"
      >
        <div className="h-8 w-1/3 rounded-lg bg-muted/50 animate-pulse" />
        <div className="h-10 rounded-lg bg-muted/50 animate-pulse" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 rounded-xl bg-muted/50 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (variant === 'grid') {
    return (
      <div
        data-testid={testId}
        className={`grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 ${className}`}
        aria-busy="true"
        aria-live="polite"
      >
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-40 rounded-xl bg-muted/50 animate-pulse" />
        ))}
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div
        data-testid={testId}
        className={`h-40 rounded-xl bg-muted/50 animate-pulse ${className}`}
        aria-busy="true"
        aria-live="polite"
      />
    );
  }

  // list variant (default)
  return (
    <div
      data-testid={testId}
      className={`space-y-3 ${className}`}
      aria-busy="true"
      aria-live="polite"
    >
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-14 rounded-lg bg-muted/50 animate-pulse" />
      ))}
    </div>
  );
}

export default LoadingSkeleton;
