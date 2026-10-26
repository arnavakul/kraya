import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { useRequests } from '../lib/requests';
import { STATUSES, formatDate, formatMoney, formatStatus } from '../lib/format';
import StatusBadge from '../components/StatusBadge';
import { ErrorState, Loading } from '../components/PageState';

export default function RequestList() {
  const { user } = useAuth();
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(0);
  const { data, isPending, isError, error, isPlaceholderData, refetch } = useRequests({ status, page });

  const changeStatus = (value) => {
    setStatus(value);
    setPage(0);
  };

  return (
    <>
      <div className="rq-head">
        <div>
          <h1>Procurement requests</h1>
          <p className="rq-sub">Everything your team is sourcing, in one place.</p>
        </div>
        {canManage(user) && <Link className="btn" to="/requests/new">New request</Link>}
      </div>

      <div className="rq-toolbar">
        <label className="rq-label" htmlFor="status-filter">Status</label>
        <select id="status-filter" className="rq-select" value={status}
                onChange={(e) => changeStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{formatStatus(s)}</option>)}
        </select>
      </div>

      {isPending && <Loading label="Loading requests…" />}
      {isError && <ErrorState error={error} onRetry={refetch} />}

      {data && data.items.length === 0 && (
        <div className="rq-state">
          <p>{status ? 'No requests with this status.' : 'No requests yet.'}</p>
          {!status && canManage(user) && <Link className="btn" to="/requests/new">Create the first one</Link>}
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <ul className="rq-list" style={isPlaceholderData ? { opacity: 0.6 } : undefined}>
            {data.items.map((r) => (
              <li key={r.id}>
                <Link className="rq-row" to={`/requests/${r.id}`}>
                  <div>
                    <span className="rq-ref">{r.reference}</span>
                    <span className="rq-title">{r.title}</span>
                  </div>
                  <div className="rq-row-meta">
                    <StatusBadge status={r.status} />
                    <span>{formatMoney(r.budgetAmount, r.currencyCode)}</span>
                    {r.neededBy && <span>Needed by {formatDate(r.neededBy)}</span>}
                  </div>
                </Link>
              </li>
            ))}
          </ul>

          {data.totalPages > 1 && (
            <div className="rq-pager">
              <button className="btn ghost small" type="button"
                      disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                Previous
              </button>
              <span>Page {data.page + 1} of {data.totalPages}</span>
              <button className="btn ghost small" type="button"
                      disabled={isPlaceholderData || page + 1 >= data.totalPages}
                      onClick={() => setPage((p) => p + 1)}>
                Next
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}
