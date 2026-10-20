/**
 * Single place that knows where the API lives.
 *
 * Set NEXT_PUBLIC_API_URL at build time; the localhost default keeps `npm run
 * dev` working without any configuration.
 */
export const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

export function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

/**
 * fetch wrapper: points at the API and always sends/receives the httpOnly
 * auth cookies. Never put tokens in JavaScript — the backend sets them as
 * httpOnly cookies on register/login/refresh.
 */
export function apiFetch(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  return fetch(apiUrl(path), { credentials: "include", ...init });
}
