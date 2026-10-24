import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from './auth/AuthProvider';
import './styles/kraya.css';
  
/* ---------- data (replace with TanStack Query: GET /api/v1/requests/:id/quotes) ---------- */
const STAGES = ['Requirement', 'Sourcing', 'RFQ', 'Quoting', 'Evaluation', 'Negotiation', 'Approval', 'PO draft'];
const CURRENT_STAGE = 4;

const QUOTES = [
  { id: 'q1', name: 'Luminex Supply',  lines: 412000, freight: 9000,  tax: 75800, discount: 12000, risk: 'Low',    fit: 96, secs: 420 },
  { id: 'q2', name: 'BrightGrid Ltd',  lines: 389000, freight: 21000, tax: 73800, discount: 0,     risk: 'Medium', fit: 91, secs: 480 },
  { id: 'q3', name: 'Voltaro Traders', lines: 401500, freight: 12000, tax: 74500, discount: 5000,  risk: 'Low',    fit: 88, secs: 0 },
];

/* ---------- pure helpers ---------- */
// Deterministic commercial total — AI never alters this (WORKFLOWS §6).
export const total = (q) => q.lines + q.freight + q.tax - q.discount;
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const mmss = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

/* ---------- hooks ---------- */
function useTheme() {
  const [theme, setTheme] = useState('dark'); // dark on first render keeps SSR markup stable

  useEffect(() => {
    try {
      if (localStorage.getItem('kraya-theme') === 'light') setTheme('light');
    } catch {}
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggle = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    try { localStorage.setItem('kraya-theme', next); } catch {}
  }, [theme]);

  return [theme, toggle];
}

function useCountdown(start) {
  const [secs, setSecs] = useState(start);
  const done = secs <= 0;
  useEffect(() => {
    if (done) return;
    const id = setInterval(() => setSecs((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [done]);
  return secs;
}

/* ---------- components ---------- */
function ThemeToggle({ theme, onToggle }) {
  return (
    <button className="theme" type="button" role="switch"
            aria-checked={theme === 'dark'} aria-label="Dark mode" onClick={onToggle}>
      <span className="knob" aria-hidden="true">
        <svg className="moon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
        <svg className="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
          <circle cx="12" cy="12" r="4.5" fill="currentColor" />
          <path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8" />
        </svg>
      </span>
    </button>
  );
}

// In src/KrayaDashboard.jsx: replace your whole `function Header(...) { ... }` with this.
// (useState/useEffect are already imported there; useAuth too, from the logout step.)

function Header({ theme, onToggleTheme }) {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  // Escape closes the mobile menu
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === 'Escape' && setOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <header className={open ? 'nav-open' : undefined}>
      <nav aria-label="Primary">
        <a className="logo" href="#">KRAYA<span>.</span></a>

        <div className="nav-menu" id="nav-menu">
          <ul onClick={() => setOpen(false)}>
            <li><a href="#" aria-current="page">Requests</a></li>
            <li><a href="#quotes">Quotes</a></li>
            <li><a href="#">Suppliers</a></li>
            <li><a href="#">Approvals</a></li>
            <li><a href="#activity">Audit</a></li>
          </ul>
          <div className="nav-actions">
            <button className="btn ghost" type="button">Ask Kraya</button>
            <button className="btn" type="button">New request</button>
            <button className="btn ghost" type="button" onClick={logout} title={user?.email}>Log out</button>
          </div>
        </div>

        <ThemeToggle theme={theme} onToggle={onToggleTheme} />

        <button className="nav-burger" type="button"
                aria-label={open ? 'Close menu' : 'Open menu'}
                aria-expanded={open} aria-controls="nav-menu"
                onClick={() => setOpen((o) => !o)}>
          {open ? '✕' : '☰'}
        </button>
      </nav>
    </header>
  );
}


function StageStepper({ current }) {
  return (
    <ol className="steps" aria-label="Procurement stage">
      {STAGES.map((label, i) => (
        <li key={label} className={i < current ? 'done' : undefined}
            aria-current={i === current ? 'step' : undefined}>
          {i < current && '✓ '}{label}
        </li>
      ))}
    </ol>
  );
}

function QuoteCard({ quote, index, isBest, onNegotiate }) {
  const secs = useCountdown(quote.secs);
  const [negotiating, setNegotiating] = useState(false);

  const pill = negotiating
    ? { cls: 'ok', text: 'Negotiating' }
    : isBest
      ? { cls: 'best', text: 'Best value' }
      : { cls: '', text: 'Under review' };

  const handleClick = () => {
    setNegotiating(true);
    onNegotiate(quote.name);
  };

  return (
    <article className="card">
      <div className="q-head">
        <strong>Supplier {index + 1}</strong>
        <span>{quote.name}</span>
        <span className={`pill ${pill.cls}`}>{pill.text}</span>
      </div>

      <div className="lbl">Comparable total</div>
      <div className={`field ${isBest ? '' : 'accent'}`}>{inr.format(total(quote))}</div>

      <dl>
        <dt>Line items</dt><dd>{inr.format(quote.lines)}</dd>
        <dt>Freight + tax</dt><dd>{inr.format(quote.freight + quote.tax)}</dd>
        <dt>Discount</dt><dd>−{inr.format(quote.discount)}</dd>
        <dt>Risk · Requirement fit</dt><dd>{quote.risk} · {quote.fit}%</dd>
      </dl>

      <div className="foot">
        <div className="timer" role="timer" aria-label="Negotiation window">
          {mmss(secs)}<small>Remaining time delay</small>
        </div>
        <button className="btn" type="button" disabled={negotiating} onClick={handleClick}>
          {negotiating ? 'Strategy ready' : 'Negotiate'}
        </button>
      </div>
    </article>
  );
}

function ActivityLog({ entries }) {
  return (
    <div className="card">
      <ul className="log">
        {entries.map((e, i) => (
          <li key={`${e.time}-${i}`}>
            <time>{e.time}</time>
            <span><b>{e.who}</b> {e.msg}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------- page ---------- */
export default function KrayaDashboard() {
  const [theme, toggleTheme] = useTheme();
  const [log, setLog] = useState(() => [
    { time: now(), who: 'Policy engine',   msg: 'no approval required below ₹5,00,000 threshold' },
    { time: now(), who: 'Sourcing agent',  msg: 'validated 3 suppliers against approved sources' },
    { time: now(), who: 'Evaluator',       msg: 'normalized 3 quotes; totals computed deterministically' },
  ]); // newest first

  // O(n) single pass: lowest comparable total
  const bestId = useMemo(
    () => QUOTES.reduce((a, b) => (total(b) < total(a) ? b : a)).id,
    []
  );

  const handleNegotiate = useCallback((supplier) => {
    setLog((l) => [{ time: now(), who: 'Negotiation agent', msg: `drafted offer for ${supplier} — awaiting review` }, ...l]);
  }, []);

  return (
    <>
      <Header theme={theme} onToggleTheme={toggleTheme} />
      <main>
        <section className="hero">
          <h1>Procurement, <em>on autopilot.</em></h1>
          <p>Discover suppliers, compare quotes, negotiate and approve — every step explainable and audited.</p>
          <button className="btn" type="button">Start a procurement request</button>
        </section>

        <section aria-labelledby="req-h">
          <h2 id="req-h">PR-2041 · 200× Industrial LED panels</h2>
          <StageStepper current={CURRENT_STAGE} />
        </section>

        <section id="quotes" aria-labelledby="q-h">
          <h2 id="q-h">Quote comparison</h2>
          <div className="grid">
            {QUOTES.map((q, i) => (
              <QuoteCard key={q.id} quote={q} index={i} isBest={q.id === bestId} onNegotiate={handleNegotiate} />
            ))}
          </div>
        </section>

        <section id="activity" aria-labelledby="a-h">
          <h2 id="a-h">Agent activity</h2>
          <ActivityLog entries={log} />
        </section>
      </main>
    </>
  );
}
