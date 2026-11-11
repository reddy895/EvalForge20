/**
 * Shared HTTP helpers.
 *
 * All API calls use a relative base by default so the production build works
 * behind any reverse proxy. `VITE_API_BASE_URL` may override it for split
 * deployments. An optional bearer token can be supplied at runtime through
 * `localStorage.evalforge_auth_token` when the backend has AUTH_TOKEN enabled.
 */

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

export function apiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

export function authHeaders(): Record<string, string> {
  try {
    const token = globalThis.localStorage?.getItem('evalforge_auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  for (const [key, value] of Object.entries(authHeaders())) {
    if (!headers.has(key)) headers.set(key, value);
  }
  return fetch(apiUrl(path), { ...options, headers });
}

export function createEventSource(path: string): EventSource {
  return new EventSource(apiUrl(path));
}
