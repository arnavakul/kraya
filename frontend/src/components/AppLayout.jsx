import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { useTheme } from '../lib/useTheme';
import ThemeToggle from './ThemeToggle';
import FloatingChatbot from './FloatingChatbot';

export default function AppLayout() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const location = useLocation();
  const [theme, toggleTheme] = useTheme();
  const [open, setOpen] = useState(false);

  // The page's own "New ..." button is the main action on its list page, so the header one is for other pages.
  const onSuppliers = location.pathname.startsWith('/suppliers');
  const newLink = onSuppliers
    ? { to: '/suppliers/new', label: 'New supplier' }
    : { to: '/requests/new', label: 'New request' };

  // Escape closes the mobile menu
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === 'Escape' && setOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  async function handleLogout() {
    await logout();
    queryClient.clear(); // never leave one user's data in memory for the next login
  }

  const close = () => setOpen(false);

  return (
    <>
      <header className={open ? 'nav-open' : undefined}>
        <nav aria-label="Primary">
          <Link className="logo" to="/requests">KRAYA<span>.</span></Link>

          <div className="nav-menu" id="nav-menu">
            <ul onClick={close}>
              <li><NavLink to="/dashboard">Dashboard</NavLink></li>
              <li><NavLink to="/requests">Requests</NavLink></li>
              <li><NavLink to="/suppliers">Suppliers</NavLink></li>
              <li><NavLink to="/agents">Agents</NavLink></li>
              <li><NavLink to="/analytics">Analytics</NavLink></li>
            </ul>
            <div className="nav-actions">
              {canManage(user) && (
                <Link className="btn" to={newLink.to} onClick={close}>{newLink.label}</Link>
              )}
              <button className="btn ghost" type="button" onClick={handleLogout} title={user?.email}>
                Log out
              </button>
            </div>
          </div>

          <ThemeToggle theme={theme} onToggle={toggleTheme} />

          <button className="nav-burger" type="button"
                  aria-label={open ? 'Close menu' : 'Open menu'}
                  aria-expanded={open} aria-controls="nav-menu"
                  onClick={() => setOpen((o) => !o)}>
            {open ? '✕' : '☰'}
          </button>
        </nav>
      </header>

      <main>
        <Outlet />
      </main>

      <FloatingChatbot />
    </>
  );
}
