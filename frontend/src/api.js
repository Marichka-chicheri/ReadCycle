import { getIdToken } from './auth.js';
import { getConfig } from './config.js';

// fetch wrapper: adds the Cognito ID token and unwraps the backend's {"error": {...}} format.
export async function api(path, options = {}) {
  const token = await getIdToken();
  const res = await fetch(getConfig().apiUrl + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const message = body?.error?.message || body?.message || `HTTP ${res.status}`;
    throw Object.assign(new Error(message), { status: res.status });
  }
  return body;
}
