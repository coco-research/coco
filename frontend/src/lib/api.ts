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
