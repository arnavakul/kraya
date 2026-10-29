// UI hint only. The backend is the real gatekeeper and returns 403 for everyone else.
export const canManage = (user) => user?.role === 'ORG_ADMIN' || user?.role === 'PROCUREMENT';