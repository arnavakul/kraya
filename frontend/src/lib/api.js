// All HTTP lives here. The access token is kept in memory only (never localStorage);
// the refresh token is an HttpOnly cookie the browser sends by itself.
const BASE = '/api/v1';

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

let accessToken = null;
let refreshing = null; // one refresh at a time, so StrictMode double-effects can't trigger token-reuse logout
let onAuthLost = () => {};

export const setAuthLostHandler = (fn) => { onAuthLost = fn; };

async function parse(res) {
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data?.message || 'Something went wrong');
  return data;
}

function send(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`;
  return fetch(`${BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export function refreshSession() {
  if (!refreshing) {
    refreshing = send('/auth/refresh', { method: 'POST', auth: false })
      .then(parse)
      .then((data) => {
        accessToken = data.token;
        return data;
      })
      .finally(() => { refreshing = null; });
  }
  return refreshing;
}

/** Authenticated request. On 401 it refreshes once and retries. */
export async function api(path, options) {
  let res = await send(path, options);
  if (res.status === 401) {
    try {
      await refreshSession();
    } catch {
      accessToken = null;
      onAuthLost();
      throw new ApiError(401, 'Session expired');
    }
    res = await send(path, options);
  }
  return parse(res);
}

async function authenticate(path, body) {
  const data = await parse(await send(path, { method: 'POST', body, auth: false }));
  accessToken = data.token;
  return data;
}

export const login = (email, password) => authenticate('/auth/login', { email, password });
export const register = (payload) => authenticate('/auth/register', payload);

export async function logout() {
  try {
    await send('/auth/logout', { method: 'POST', auth: false });
  } finally {
    accessToken = null;
  }
}