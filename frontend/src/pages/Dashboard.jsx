import { Link } from 'react-router-dom';

import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { formatMoney } from '../lib/format';
import { useDashboard } from '../lib/dashboard';
import { describeActivity, timeAgo, trendText } from '../lib/dashboardFormat';
import { ErrorState, Loading } from '../components/PageState';
import '../styles/dashboard.css';

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
    <article className="db-kpi">
      <div className="db-icon" aria-hidden="true">{icon}</div>
      <div className="db-kpi-body">
        <span className="db-kpi-label">{label}</span>
        <strong className="db-kpi-value">{value}</strong>
        {note && (
          <span className={`db-kpi-note ${tone ? `db-kpi-note--${tone}` : ''}`}>
            {note}
          </span>
        )}
      </div>
    </article>
  );
}

function PipelineCard({ slices }) {
  const total = slices.reduce((sum, slice) => sum + Number(slice.count || 0), 0);
  const items = slices.filter((slice) => Number(slice.count || 0) > 0);
  let offset = 0;

  const segments = items.map((slice) => {
    const percentage = total ? (slice.count / total) * 100 : 0;
    const start = offset;
    offset += percentage;
    return `${pipelineColors[slice.key] || '#8d968d'} ${start}% ${offset}%`;
  });

  const background = items.length
    ? `conic-gradient(${segments.join(', ')})`
    : 'conic-gradient(var(--field) 0 100%)';

  return (
    <section className="card db-card">
      <h2 className="db-h2">Procurement Pipeline</h2>
      <div className="db-pipeline">
        <div className="db-donut" style={{ background }}>
          <div className="db-donut-center">
            <strong>{total}</strong>
            <span>Requests</span>
          </div>
        </div>
        {items.length > 0 ? (
          <ul className="db-legend">
            {items.map((slice) => {
              const percentage = total
                ? Math.round((slice.count / total) * 100)
                : 0;
              return (
                <li key={slice.key}>
                  <span
                    className="db-dot"
                    style={{ background: pipelineColors[slice.key] || '#8d968d' }}
                  />
                  <span className="db-legend-label">{slice.label}</span>
                  <span className="db-legend-count">
                    {slice.count} ({percentage}%)
                  </span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="db-empty">No requests in the pipeline yet.</p>
        )}
      </div>
    </section>
  );
}

function ActiveRequestsCard({ requests }) {
  return (
    <section className="card db-card">
      <div className="db-card-head">
        <h2 className="db-h2">Active AI Agent Runs</h2>
        <Link className="db-link" to="/requests">View all →</Link>
      </div>

      {requests.length === 0 ? (
        <p className="db-empty">No active requests right now.</p>
      ) : (
        <ul className="db-runs">
          {requests.map((request) => {
            const progress = Math.max(
              0,
              Math.min(100, Number(request.progressPercent) || 0),
            );

            return (
              <li key={request.id}>
                <div className="db-run">
                  <div className="db-run-top">
                    <span className="db-chip">{request.reference}</span>
                    <span className="db-run-title">{request.title}</span>
                  </div>
                  <div className="db-run-bottom">
                    <span className="db-run-stage">
                      <span className="db-spin" aria-hidden="true" />
                      In progress
                    </span>
                    <div
                      className="db-progress"
                      role="progressbar"
                      aria-label={`Progress for ${request.title}`}
                      aria-valuemin="0"
                      aria-valuemax="100"
                      aria-valuenow={progress}
                    >
                      <span style={{ width: `${progress}%` }} />
                    </div>
                    <strong className="db-run-pct">{progress}%</strong>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function ActivityCard({ items }) {
  return (
    <section className="card db-card">
      <h2 className="db-h2">Recent Activity</h2>
      {items.length === 0 ? (
        <p className="db-empty">No recent activity.</p>
      ) : (
        <ul className="db-activity">
          {items.map((item, index) => {
            const activity = describeActivity(item);
            const icon =
              activity.icon === 'check' ? '✓'
                : activity.icon === 'plus' ? '+'
                  : activity.icon === 'alert' ? '!'
                    : '↻';

            return (
              <li key={`${item.entityId}-${item.createdAt}-${index}`}>
                <span className="db-activity-icon" aria-hidden="true">{icon}</span>
                <span className="db-activity-text">
                  <strong>{activity.title}</strong>
                  {activity.sub && <span>{activity.sub}</span>}
                </span>
                <time className="db-time">{timeAgo(item.createdAt)}</time>
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
    <section className="card db-card">
      <div className="db-card-head">
        <h2 className="db-h2">AI Insights</h2>
        <Link className="db-link" to="/requests">View details →</Link>
      </div>
      {insights.length === 0 ? (
        <p className="db-empty">No insights available right now.</p>
      ) : (
        <ul className="db-insights">
          {insights.map((item, index) => (
            <li className="db-insight" key={`${item.message}-${index}`}>
              <span aria-hidden="true">✦</span>
              <span>{item.message}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data, isPending, isError, error, refetch } = useDashboard();

  if (isPending) return <Loading label="Loading dashboard…" />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const summary = data?.summary || {};
  const trend = trendText(
    summary.requestsLast30Days ?? 0,
    summary.requestsPrevious30Days ?? 0,
  );
  const totalSpend = (summary.spend || []).reduce(
    (sum, item) => sum + Number(item.amount || 0),
    0,
  );

  const cards = [
    {
      label: 'Total Requests',
      value: summary.totalRequests ?? 0,
      note: trend.text,
      tone: trend.tone,
      icon: '▣',
    },
    {
      label: 'Active Requests',
      value: summary.activeRequests ?? 0,
      note: 'Being worked on now',
      icon: '⎇',
    },
    {
      label: 'Completed',
      value: summary.completedRequests ?? 0,
      note: `${summary.completedLast30Days ?? 0} in the last 30 days`,
      icon: '✓',
    },
    {
      label: 'Total Spend',
      value: formatMoney(totalSpend, 'INR'),
      note: '+12%',
      icon: '₹',
    },
    {
      label: 'Pending Approvals',
      value: summary.pendingApprovals ?? 0,
      note: 'Waiting for sign-off',
      icon: '◫',
    },
    {
      label: 'Active Suppliers',
      value: summary.activeSuppliers ?? 0,
      note: 'Can receive RFQs',
      icon: '◧',
    },
  ];

  return (
    <div className="dashboard-page">
      <div className="db-header">
        <div>
          <h1>Procurement Dashboard</h1>
          <p className="db-subtitle">
            Overview of your procurement operations and AI agent activities.
          </p>
        </div>
        {canManage(user) && (
          <Link className="btn db-new-request" to="/requests/new">
            + New request
          </Link>
        )}
      </div>

      <div className="db-kpis">
        {cards.map((card) => (
          <KpiCard key={card.label} {...card} />
        ))}
      </div>

      <div className="db-grid">
        <PipelineCard slices={data?.pipeline || []} />
        <ActiveRequestsCard requests={data?.activeRequests || []} />
      </div>

      <div className="db-grid">
        <ActivityCard items={data?.recentActivity || []} />
        <InsightsCard insights={data?.insights || []} />
      </div>
    </div>
  );
}
