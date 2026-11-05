import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { countryName } from '../lib/countries';
import { formatDateTime } from '../lib/format';
import { useSupplier, useSupplierStatus } from '../lib/suppliers';
import SupplierStatusBadge from '../components/SupplierStatusBadge';
import { ErrorState, Loading } from '../components/PageState';

// What each status can change to. Only blocking needs a written reason (the backend enforces it too).
const ACTIONS = {
  ACTIVE: [{ to: 'INACTIVE', label: 'Mark inactive' }, { to: 'BLOCKED', label: 'Block supplier', danger: true }],
  INACTIVE: [{ to: 'ACTIVE', label: 'Reactivate' }, { to: 'BLOCKED', label: 'Block supplier', danger: true }],
  BLOCKED: [{ to: 'ACTIVE', label: 'Reactivate' }, { to: 'INACTIVE', label: 'Mark inactive' }],
};

// Only link http(s) addresses, never javascript: or other schemes.
const safeUrl = (value) => (value && /^https?:\/\//i.test(value) ? value : null);

export default function SupplierDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { data: s, isPending, isError, error, refetch } = useSupplier(id);
  const changeStatus = useSupplierStatus(id);

  const [blocking, setBlocking] = useState(false);
  const [reason, setReason] = useState('');
  const [actionError, setActionError] = useState('');

  if (isPending) return <Loading label="Loading supplier…" />;
  if (isError) {
    return (
      <>
        <Link className="rq-back" to="/suppliers">← All suppliers</Link>
        <ErrorState error={error} onRetry={refetch} />
      </>
    );
  }

  const manager = canManage(user);
  const website = safeUrl(s.websiteUrl);

  function run(status, why) {
    setActionError('');
    changeStatus.mutate({ status, reason: why }, {
      onSuccess: () => {
        setBlocking(false);
        setReason('');
      },
      onError: (err) => setActionError(err.message),
    });
  }

  function choose(action) {
    if (action.to === 'BLOCKED') {
      setBlocking(true);
      setReason('');
      setActionError('');
    } else {
      run(action.to);
    }
  }

  return (
    <>
      <Link className="rq-back" to="/suppliers">← All suppliers</Link>

      <div className="rq-head">
        <div>
          <SupplierStatusBadge status={s.status} />
          <h1 className="rq-detail-title">{s.name}</h1>
        </div>
      </div>

      {s.statusReason && s.status !== 'ACTIVE' && (
        <div className="rq-banner" role="status"><strong>Note:</strong> {s.statusReason}</div>
      )}

      {manager && (
        <div className="rq-actions rq-actions--top">
          {ACTIONS[s.status].map((action, i) => (
            <button key={action.to} type="button"
                    className={action.danger ? 'btn danger' : i === 0 ? 'btn' : 'btn ghost'}
                    disabled={changeStatus.isPending} onClick={() => choose(action)}>
              {action.label}
            </button>
          ))}
          <Link className="btn ghost" to={`/suppliers/${s.id}/edit`}>Edit</Link>
        </div>
      )}

      {blocking && (
        <div className="rq-reason">
          <label className="rq-label" htmlFor="reason">Why is this supplier being blocked? (required)</label>
          <textarea id="reason" className="rq-textarea" maxLength={500} value={reason}
                    onChange={(e) => setReason(e.target.value)} />
          <div className="rq-actions">
            <button className="btn danger" type="button"
                    disabled={!reason.trim() || changeStatus.isPending}
                    onClick={() => run('BLOCKED', reason.trim())}>
              {changeStatus.isPending ? 'Saving…' : 'Confirm: block supplier'}
            </button>
            <button className="btn ghost" type="button" onClick={() => setBlocking(false)}>Back</button>
          </div>
        </div>
      )}

      {actionError && <p className="rq-error" role="alert">{actionError}</p>}

      <section className="card rq-section">
        <h2 className="rq-h2">Contact</h2>
        <div className="rq-meta">
          <div><span className="rq-k">Contact person</span><span className="rq-v">{s.contactName || '—'}</span></div>
          <div>
            <span className="rq-k">Email</span>
            <span className="rq-v"><a className="sp-link" href={`mailto:${s.contactEmail}`}>{s.contactEmail}</a></span>
          </div>
          <div><span className="rq-k">Phone</span><span className="rq-v">{s.contactPhone || '—'}</span></div>
          <div><span className="rq-k">Country</span><span className="rq-v">{countryName(s.countryCode)}</span></div>
          <div>
            <span className="rq-k">Website</span>
            <span className="rq-v">
              {website
                ? <a className="sp-link" href={website} target="_blank" rel="noopener noreferrer">{s.websiteUrl}</a>
                : s.websiteUrl || '—'}
            </span>
          </div>
        </div>
      </section>

      <section className="card rq-section">
        <h2 className="rq-h2">Commercial details</h2>
        <div className="rq-meta">
          <div><span className="rq-k">Tax ID</span><span className="rq-v">{s.taxId || '—'}</span></div>
          <div><span className="rq-k">Payment terms</span><span className="rq-v">{s.paymentTerms || '—'}</span></div>
          <div><span className="rq-k">Added</span><span className="rq-v">{formatDateTime(s.createdAt)}</span></div>
          <div><span className="rq-k">Last updated</span><span className="rq-v">{formatDateTime(s.updatedAt)}</span></div>
        </div>
        <div className="sp-block">
          <span className="rq-k">Categories</span>
          {s.categories.length > 0
            ? <div className="sp-chips">{s.categories.map((c) => <span key={c} className="sp-chip">{c}</span>)}</div>
            : <span className="rq-v">—</span>}
        </div>
        {s.notes && <p className="rq-desc">{s.notes}</p>}
      </section>
    </>
  );
}
