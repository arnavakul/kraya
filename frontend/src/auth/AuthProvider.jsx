import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as http from '../lib/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};

const toUser = (d) => ({ id: d.userId, organizationId: d.organizationId, email: d.email, role: d.role });

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading'); // 'loading' | 'authed' | 'anon'

  // Restore the session on page load from the refresh cookie.
  useEffect(() => {
    let alive = true;
    http.refreshSession()
      .then((d) => { if (alive) { setUser(toUser(d)); setStatus('authed'); } })
      .catch(() => { if (alive) setStatus('anon'); });
    return () => { alive = false; };
  }, []);

  // If a refresh ever fails mid-session, send the user back to login.
  useEffect(() => {
    http.setAuthLostHandler(() => { setUser(null); setStatus('anon'); });
  }, []);

  const signIn = useCallback((d) => {
    setUser(toUser(d));
    setStatus('authed');
  }, []);

  const login = useCallback(async (email, password) => signIn(await http.login(email, password)), [signIn]);
  const register = useCallback(async (payload) => signIn(await http.register(payload)), [signIn]);

  const logout = useCallback(async () => {
    await http.logout().catch(() => {});
    setUser(null);
    setStatus('anon');
  }, []);

  const value = useMemo(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
