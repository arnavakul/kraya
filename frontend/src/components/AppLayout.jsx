import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { useTheme } from '../lib/useTheme';
import ThemeToggle from './ThemeToggle';

export default function AppLayout() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [theme, toggleTheme] = useTheme();
  const [open, setOpen] = useState(false);

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
              <li><NavLink to="/requests">Requests</NavLink></li>
            </ul>
            <div className="nav-actions">
              {canManage(user) && (
                <Link className="btn" to="/requests/new" onClick={close}>New request</Link>
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
    </>
  );
}
