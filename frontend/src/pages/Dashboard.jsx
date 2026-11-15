import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { formatMoney } from '../lib/format';
import { useDashboard } from '../lib/dashboard';
import { describeActivity, stageLabel, timeAgo, trendText } from '../lib/dashboardFormat';
import { ErrorState, Loading } from '../components/PageState';

const pipelineColors = {
  draft: '#8d968d',
  submitted: '#a58bff',
  in_progress: '#5fdc5a',
  pending_approval: '#f5b73c',
  completed: '#2f9e3a',
  closed: '#ef6a5a',
};

function KpiCard({ label, value, note, icon, tone }) {
  return (
    <div className="kraya-kpi-card">
      <div className="kraya-kpi-icon" aria-hidden="true">{icon}</div>
      <div className="kraya-kpi-body">
        <span className="kraya-kpi-label">{label}</span>
        <strong className="kraya-kpi-value">{value}</strong>
        {note && <span className={`kraya-kpi-note ${tone ? `kraya-kpi-note--${tone}` : ''}`}>{note}</span>}
      </div>
    </div>
  );
}

function PipelineCard({ slices }) {
  const total = slices.reduce((sum, s) => sum + s.count, 0);
  const items = slices.filter((s) => s.count > 0);
  const gradient = items.map((s) => {
    const pct = total === 0 ? 0 : (s.count / total) * 100;
    return `${pipelineColors[s.key] || '#8d968d'} ${pct}%`;
  });

  return (
    <section className="kraya-panel">
      <h2>Procurement Pipeline</h2>
      <div className="kraya-pipeline-box">
        <div className="kraya-donut" style={{ background: `conic-gradient(${items.map((s, idx) => {
          const pct = total === 0 ? 0 : (s.count / total) * 100;
          const prev = items.slice(0, idx).reduce((sum, p) => sum + (total === 0 ? 0 : (p.count / total) * 100), 0);
          return `${pipelineColors[s.key] || '#8d968d'} ${prev}% ${prev + pct}%`;
        }).join(', ') || '#1d221d 0 100%'})` }}>
          <div className="kraya-donut-inner">
            <strong>{total}</strong>
            <span>Requests</span>
          </div>
        </div>
        <ul className="kraya-legend">
          {items.map((s) => {
            const pct = total === 0 ? 0 : Math.round((s.count / total) * 100);
            return (
              <li key={s.key}>
                <span className="kraya-dot" style={{ background: pipelineColors[s.key] || '#8d968d' }} />
                <span>{s.label}</span>
                <em>{s.count} ({pct}%)</em>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}

function ActiveRequestsCard({ requests }) {
  return (
    <section className="kraya-panel">
      <div className="kraya-panel-head">
        <h2>Active AI Agent Runs</h2>
        <Link to="/requests">View all →</Link>
      </div>
      {requests.length === 0 ? (
        <p className="kraya-empty">No active requests right now.</p>
      ) : (
        <ul className="kraya-agent-list">
          {requests.map((r) => (
            <li key={r.id}>
              <div className="kraya-agent-ref">{r.reference}</div>
              <div className="kraya-agent-title">{r.title}</div>
              <div className="kraya-agent-progress">
                <span className="kraya-agent-status" />
                <div className="kraya-progress"><span style={{ width: `${r.progressPercent}%` }} /></div>
                <strong>{r.progressPercent}%</strong>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ActivityCard({ items }) {
  return (
    <section className="kraya-panel">
      <h2>Recent Activity</h2>
      {items.length === 0 ? (
        <p className="kraya-empty">No recent activity.</p>
      ) : (
        <ul className="kraya-activity-list">
          {items.map((item, idx) => {
            const d = describeActivity(item);
            return (
              <li key={`${item.entityId}-${item.createdAt}-${idx}`}>
                <span className="kraya-activity-icon" aria-hidden="true">{d.icon === 'check' ? '✓' : d.icon === 'plus' ? '+' : d.icon === 'alert' ? '!' : '↻'}</span>
                <div className="kraya-activity-copy">
                  <strong>{d.title}</strong>
                  {d.sub && <span>{d.sub}</span>}
                </div>
                <time>{timeAgo(item.createdAt)}</time>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function InsightsCard({ insights }) {
  return (
    <section className="kraya-panel">
      <div className="kraya-panel-head">
        <h2>AI Insights</h2>
        <Link to="/requests">View details →</Link>
      </div>
      <ul className="kraya-insights-list">
        {insights.map((item, index) => (
          <li key={`${item.message}-${index}`}>
            <span className="kraya-insight-bullet">✦</span>
            <span>{item.message}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data, isPending, isError, error, refetch } = useDashboard();

  if (isPending) return <Loading label="Loading dashboard…" />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const s = data.summary || {};
  const trend = trendText(s.requestsLast30Days ?? 0, s.requestsPrevious30Days ?? 0);
  const totalSpend = (s.spend || []).reduce((sum, item) => sum + Number(item.amount || 0), 0);

  const cards = [
    { label: 'Total Requests', value: s.totalRequests ?? 0, note: trend.text, tone: trend.tone, icon: '▣' },
    { label: 'Active Requests', value: s.activeRequests ?? 0, note: 'Being worked on now', icon: '⎇' },
    { label: 'Completed', value: s.completedRequests ?? 0, note: `${s.completedLast30Days ?? 0} in the last 30 days`, icon: '✓' },
    { label: 'Total Spend', value: formatMoney(totalSpend, 'INR'), note: '+12%', icon: '₹' },
    { label: 'Pending Approvals', value: s.pendingApprovals ?? 0, note: 'Waiting for sign-off', icon: '◫' },
    { label: 'Active Suppliers', value: s.activeSuppliers ?? 0, note: 'Can receive RFQs', icon: '◧' },
  ];

  return (
    <>
      <style>{`
        .kraya-dashboard { padding: 24px 0 40px; }
        .kraya-dashboard .db-header { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:26px; }
        .kraya-dashboard h1 { margin:0; font-size: clamp(2.2rem,4vw,4rem); letter-spacing:-.05em; line-height:1; }
        .kraya-dashboard .db-subtitle { color: var(--muted); margin-top: 8px; font-size: 1.05rem; }
        .kraya-new-btn { display:inline-flex; align-items:center; justify-content:center; min-height:52px; padding: 0 28px; border-radius: 999px; background: linear-gradient(135deg, var(--lime), var(--lime2)); color: var(--on-lime); font-weight:700; box-shadow: 0 6px 24px rgba(166,240,60,.22); }
        .kraya-kpi-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 18px; margin-bottom: 28px; }
        .kraya-kpi-card { display:flex; align-items:center; gap:14px; min-height: 110px; background: rgba(18, 22, 20, 0.88); border:1px solid var(--line); border-radius: 18px; padding: 18px 18px; }
        .kraya-kpi-icon { width: 42px;height:42px; display:grid; place-items:center; border-radius:12px; background: rgba(166,240,60,.12); color: var(--lime); font-size: 1.35rem; }
        .kraya-kpi-body { display:grid; gap:6px; min-width:0; }
        .kraya-kpi-label { color: var(--muted); font-size: .82rem; }
        .kraya-kpi-value { font-size: clamp(1.8rem, 2vw, 2.2rem); letter-spacing:-.04em; line-height:1.1; }
        .kraya-kpi-note { font-size: .8rem; color: var(--muted); }
        .kraya-kpi-note--up { color: var(--lime); }
        .kraya-kpi-note--down { color: #ff7c7c; }
        .kraya-panel-grid { display:grid; grid-template-columns: 1.05fr 1.3fr; gap: 24px; margin-bottom: 24px; }
        .kraya-panel { background: rgba(14, 18, 17, 0.9); border:1px solid var(--line); border-radius: 22px; padding: 22px 22px 18px; }
        .kraya-panel h2 { margin:0 0 18px; font-size: 1.1rem; letter-spacing:-.03em; }
        .kraya-panel-head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 12px; }
        .kraya-panel-head a { color: var(--lime); font-weight:600; }
        .kraya-pipeline-box { display:flex; align-items:center; justify-content:space-between; gap: 24px; }
        .kraya-donut { position:relative; width: 180px; height:180px; border-radius:50%; display:grid; place-items:center; }
        .kraya-donut::before { content:""; position:absolute; inset:18px; background: rgba(7,10,9,0.98); border-radius:50%; }
        .kraya-donut-inner { position:relative; z-index:1; display:grid; place-items:center; text-align:center; }
        .kraya-donut-inner strong { font-size: 2rem; letter-spacing:-.05em; line-height:1; }
        .kraya-donut-inner span { color: var(--muted); font-size: .8rem; }
        .kraya-legend { list-style:none; padding:0; margin:0; display:grid; gap:10px; min-width: 200px; }
        .kraya-legend li { display:grid; grid-template-columns: 10px 1fr auto; align-items:center; gap: 10px; color: var(--muted); }
        .kraya-dot { display:block; width:10px; height:10px; border-radius:50%; }
        .kraya-legend li em { color: var(--muted); font-style: normal; }
        .kraya-agent-list, .kraya-activity-list, .kraya-insights-list { list-style:none; padding:0; margin:0; }
        .kraya-agent-list { display:grid; gap: 14px; }
        .kraya-agent-list li { display:grid; grid-template-columns: auto 1fr auto; align-items:center; gap: 12px; min-height: 58px; }
        .kraya-agent-ref { background: rgba(166,240,60,.12); color: var(--lime); border-radius: 999px; padding: 7px 10px; font-size: .72rem; font-weight:700; letter-spacing: .02em; }
        .kraya-agent-title { color: var(--text); font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .kraya-agent-status { display:inline-block; width: 8px; height:8px; border-radius:50%; background: var(--lime); }
        .kraya-agent-progress { display:flex; align-items:center; gap: 10px; min-width: 170px; }
        .kraya-progress { flex:1; height:6px; border-radius:999px; background: rgba(255,255,255,.08); overflow:hidden; }
        .kraya-progress span { display:block; height:100%; background: linear-gradient(90deg, var(--lime), var(--lime2)); border-radius:inherit; }
        .kraya-agent-progress strong { font-size: .8rem; }
        .kraya-empty { color: var(--muted); margin: 0; }
        .kraya-activity-list { display:grid; gap: 18px; }
        .kraya-activity-list li { display:grid; grid-template-columns: 24px minmax(0,1fr) auto; align-items:flex-start; gap:12px; }
        .kraya-activity-icon { width: 20px; height:20px; display:grid; place-items:center; color: var(--lime); font-weight:700; }
        .kraya-activity-copy { display:grid; gap:3px; min-width:0; }
        .kraya-activity-copy strong { font-size: 1.1rem; }
        .kraya-activity-copy span { color: var(--muted); }
        .kraya-activity-list time { color: var(--muted); font-size: .8rem; white-space:nowrap; }
        .kraya-insights-list { display:grid; gap: 16px; }
        .kraya-insights-list li { display:flex; gap: 10px; align-items:flex-start; color: var(--text); }
        .kraya-insight-bullet { color: #f5d76c; font-size: 1.1rem; }
        @media (max-width: 840px) { .kraya-panel-grid { grid-template-columns: 1fr; } .kraya-pipeline-box { flex-direction: column; align-items: flex-start; } }
        @media (max-width: 640px) { .kraya-dashboard .db-header { flex-direction:column; align-items:flex-start; } .kraya-kpi-grid { grid-template-columns: 1fr 1fr; } .kraya-agent-list li { grid-template-columns: 1fr; } }
      `}</style>

      <div className="kraya-dashboard">
        <div className="db-header">
          <div>
            <h1>Procurement Dashboard</h1>
            <div className="db-subtitle">Overview of your procurement operations and AI agent activities.</div>
          </div>
          {canManage(user) && <Link className="kraya-new-btn" to="/requests/new">+ New request</Link>}
        </div>

        <div className="kraya-kpi-grid">
          {cards.map((card) => (
            <KpiCard key={card.label} label={card.label} value={card.value} note={card.note} icon={card.icon} tone={card.tone} />
          ))}
        </div>

        <div className="kraya-panel-grid">
          <PipelineCard slices={data.pipeline || []} />
          <ActiveRequestsCard requests={data.activeRequests || []} />
        </div>

        <div className="kraya-panel-grid">
          <ActivityCard items={data.recentActivity || []} />
          <InsightsCard insights={data.insights || []} />
        </div>
      </div>
    </>
  );
}
