import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { useRequest, useRequestAudit, useTransition } from '../lib/requests';
import { REASON_STATUSES, formatDate, formatDateTime, formatMoney, formatStatus } from '../lib/format';
import StatusBadge from '../components/StatusBadge';
import RequestStepper from '../components/RequestStepper';
import { ErrorState, Loading } from '../components/PageState';

function actionLabel(status) {
  if (status === 'SUBMITTED') return 'Submit request';
  if (status === 'CANCELLED') return 'Cancel request';
  if (status === 'REJECTED') return 'Reject request';
  return `Move to ${formatStatus(status)}`;
}

function describe(event) {
  switch (event.action) {
    case 'REQUEST_CREATED': return 'Request created';
    case 'REQUEST_UPDATED': return 'Request edited';
    case 'REQUEST_STATUS_CHANGED':
      return `Moved from ${formatStatus(event.previousState)} to ${formatStatus(event.newState)}`;
    default: return event.action;
  }
}

export default function RequestDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { data: r, isPending, isError, error, refetch } = useRequest(id);
  const audit = useRequestAudit(id);
  const transition = useTransition(id);

  const [asking, setAsking] = useState(null); // status that is waiting for a written reason
  const [reason, setReason] = useState('');
  const [actionError, setActionError] = useState('');

  if (isPending) return <Loading label="Loading request…" />;
  if (isError) {
    return (
      <>
        <Link className="rq-back" to="/requests">← All requests</Link>
        <ErrorState error={error} onRetry={refetch} />
      </>
    );
  }

  const manager = canManage(user);
  const forward = r.allowedNextStatuses.filter((s) => !REASON_STATUSES.has(s));
  const closing = r.allowedNextStatuses.filter((s) => REASON_STATUSES.has(s));

  function run(to, why) {
    setActionError('');
    transition.mutate({ to, reason: why }, {
      onSuccess: () => {
        setAsking(null);
        setReason('');
      },
      onError: (err) => setActionError(err.message),
    });
  }

  function choose(to) {
    if (REASON_STATUSES.has(to)) {
      setAsking(to);
      setReason('');
      setActionError('');
    } else {
      run(to);
    }
  }

  return (
    <>
      <Link className="rq-back" to="/requests">← All requests</Link>

      <div className="rq-head">
        <div>
          <span className="rq-ref">{r.reference}</span>
          <StatusBadge status={r.status} />
          <h1 className="rq-detail-title">{r.title}</h1>
        </div>
      </div>

      {(r.status === 'REJECTED' || r.status === 'CANCELLED') && (
        <div className="rq-banner" role="status">
          <strong>{formatStatus(r.status)}.</strong> {r.statusReason}
        </div>
      )}

      <RequestStepper status={r.status} />

      {manager && (r.status === 'DRAFT' || r.allowedNextStatuses.length > 0) && (
        <div className="rq-actions rq-actions--top">
          {forward.map((s, i) => (
            <button key={s} type="button" className={i === 0 ? 'btn' : 'btn ghost'}
                    disabled={transition.isPending} onClick={() => choose(s)}>
              {actionLabel(s)}
            </button>
          ))}
          {r.status === 'DRAFT' && <Link className="btn ghost" to={`/requests/${r.id}/edit`}>Edit</Link>}
          {closing.map((s) => (
            <button key={s} type="button" className="btn danger"
                    disabled={transition.isPending} onClick={() => choose(s)}>
              {actionLabel(s)}
            </button>
          ))}
        </div>
      )}

      {asking && (
        <div className="rq-reason">
          <label className="rq-label" htmlFor="reason">Reason for this change (required)</label>
          <textarea id="reason" className="rq-textarea" maxLength={500} value={reason}
                    onChange={(e) => setReason(e.target.value)} />
          <div className="rq-actions">
            <button className="btn danger" type="button"
                    disabled={!reason.trim() || transition.isPending}
                    onClick={() => run(asking, reason.trim())}>
              {transition.isPending ? 'Saving…' : `Confirm: ${actionLabel(asking)}`}
            </button>
            <button className="btn ghost" type="button" onClick={() => setAsking(null)}>Back</button>
          </div>
        </div>
      )}

      {actionError && <p className="rq-error" role="alert">{actionError}</p>}

      <section className="card rq-section">
        <h2 className="rq-h2">Details</h2>
        <div className="rq-meta">
          <div><span className="rq-k">Budget</span><span className="rq-v">{formatMoney(r.budgetAmount, r.currencyCode)}</span></div>
          <div><span className="rq-k">Needed by</span><span className="rq-v">{formatDate(r.neededBy)}</span></div>
          <div><span className="rq-k">Category</span><span className="rq-v">{r.category || '—'}</span></div>
          <div><span className="rq-k">Delivery location</span><span className="rq-v">{r.deliveryLocation || '—'}</span></div>
          <div><span className="rq-k">Created</span><span className="rq-v">{formatDateTime(r.createdAt)}</span></div>
          <div><span className="rq-k">Last updated</span><span className="rq-v">{formatDateTime(r.updatedAt)}</span></div>
        </div>
        {r.description && <p className="rq-desc">{r.description}</p>}
      </section>

      <section className="card rq-section">
        <h2 className="rq-h2">Items</h2>
        <ul className="rq-items">
          {r.items.map((i) => (
            <li key={i.id}>
              <span className="rq-line">{i.lineNo}</span>
              <span>
                <strong>{i.name}</strong>
                {i.description && <span className="rq-note">{i.description}</span>}
              </span>
              <span className="rq-qty">{i.quantity} {i.unit}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="card rq-section">
        <h2 className="rq-h2">History</h2>
        {audit.isPending && <Loading label="Loading history…" />}
        {audit.isError && <ErrorState error={audit.error} onRetry={audit.refetch} />}
        {audit.data && (
          <ol className="rq-timeline">
            {[...audit.data].reverse().map((e) => (
              <li key={e.id}>
                <span className="rq-dot" aria-hidden="true" />
                <div>
                  <div>{describe(e)}</div>
                  <div className="rq-time">
                    {e.actorUserId === user?.id ? 'You' : 'A teammate'} · {formatDateTime(e.createdAt)}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </>
  );
}
