import { useCallback, useEffect, useState } from 'react';

// Dark by default; the choice is remembered per browser.
export function useTheme() {
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    try {
      if (localStorage.getItem('kraya-theme') === 'light') setTheme('light');
    } catch {
      /* storage unavailable: stay on dark */
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggle = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    try {
      localStorage.setItem('kraya-theme', next);
    } catch {
      /* ignore */
    }
  }, [theme]);

  return [theme, toggle];
}