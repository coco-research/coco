/**
 * Centralized TanStack Query client.
 *
 * Exported so the v3 SSE client (`sse/client.ts`) can call
 * `queryClient.invalidateQueries()` on `platform.epoch` flip without going
 * through a React context. `App.tsx` should import this same instance.
 */

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Most queries are SSE-driven — long stale time is fine, SSE invalidates.
      staleTime: 30_000,
      refetchOnWindowFocus: true,
      retry: 1,
    },
    mutations: {
      retry: 0,
    },
  },
});
