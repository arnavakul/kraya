import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthProvider';

export default function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return <div className="auth-loading" role="status">Loading…</div>;
  }
  if (status === 'anon') {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
}
