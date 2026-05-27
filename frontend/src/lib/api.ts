const BASE_URL = '/api';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new ApiError(res.status, text);
  }
  // 204 No Content — return undefined (no body to parse)
  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return undefined as T;
  }
  return res.json();
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
}

/**
 * POST a mutating intent with an `Idempotency-Key` header (Stripe pattern).
 *
 * Per `.planning/v3/INTEGRATION.md` §C-4: the header is canonical; the same
 * UUID is also echoed in the body as `client_event_id` for back-compat during
 * the P3-P8 cutover. The backend's idempotency layer dedupes on the header.
 */
export function apiPostIdempotent<T>(
  path: string,
  body: Record<string, unknown> = {},
  idempotencyKey?: string,
): Promise<T> {
  const key = idempotencyKey ?? generateUuidV4();
  const finalBody = { ...body, client_event_id: key };
  return apiFetch(path, {
    method: 'POST',
    headers: { 'Idempotency-Key': key },
    body: JSON.stringify(finalBody),
  });
}

/**
 * Lightweight UUID v4 generator. Prefers `crypto.randomUUID()` where
 * available, falls back to a manual RFC4122 v4 implementation.
 */
export function generateUuidV4(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback — non-cryptographic, but adequate for client-side dedupe keys.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) });
}

export function apiDelete(path: string): Promise<void> {
  return apiFetch(path, { method: 'DELETE' });
}

/** Transition an entity to a new state via the state-machine endpoint. */
export function apiTransition<T>(entityPath: string, toState: string): Promise<T> {
  return apiFetch<T>(`${entityPath}/transition`, {
    method: 'PATCH',
    body: JSON.stringify({ to_state: toState }),
  });
}
