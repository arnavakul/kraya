import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { countryName } from '../lib/countries';
import { formatStatus } from '../lib/format';
import { SUPPLIER_STATUSES, useSuppliers } from '../lib/suppliers';
import { useDebouncedValue } from '../lib/useDebouncedValue';
import SupplierStatusBadge from '../components/SupplierStatusBadge';
import { ErrorState, Loading } from '../components/PageState';

const MAX_CHIPS = 4;

export default function SupplierList() {
  const { user } = useAuth();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(0);
  const q = useDebouncedValue(search.trim());
  const { data, isPending, isError, error, isPlaceholderData, refetch } = useSuppliers({ status, q, page });

  const onSearch = (value) => {
    setSearch(value);
    setPage(0);
  };
  const onStatus = (value) => {
    setStatus(value);
    setPage(0);
  };

  const filtering = Boolean(q || status);

  return (
    <>
      <div className="rq-head">
        <div>
          <h1>Suppliers</h1>
          <p className="rq-sub">The companies you buy from.</p>
        </div>
        {canManage(user) && <Link className="btn" to="/suppliers/new">New supplier</Link>}
      </div>

      <div className="rq-toolbar">
        <label className="rq-label" htmlFor="supplier-search">Search</label>
        <input id="supplier-search" className="rq-input" type="search" placeholder="Name or email"
               value={search} onChange={(e) => onSearch(e.target.value)} />
        <label className="rq-label" htmlFor="supplier-status">Status</label>
        <select id="supplier-status" className="rq-select" value={status} onChange={(e) => onStatus(e.target.value)}>
          <option value="">All statuses</option>
          {SUPPLIER_STATUSES.map((s) => <option key={s} value={s}>{formatStatus(s)}</option>)}
        </select>
      </div>

      {isPending && <Loading label="Loading suppliers…" />}
      {isError && <ErrorState error={error} onRetry={refetch} />}

      {data && data.items.length === 0 && (
        <div className="rq-state">
          <p>{filtering ? 'No suppliers match your search.' : 'No suppliers yet.'}</p>
          {!filtering && canManage(user) && <Link className="btn" to="/suppliers/new">Add your first supplier</Link>}
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <ul className="rq-list" style={isPlaceholderData ? { opacity: 0.6 } : undefined}>
            {data.items.map((s) => (
              <li key={s.id}>
                <Link className="rq-row" to={`/suppliers/${s.id}`}>
                  <div>
                    <span className="rq-title">{s.name}</span>
                    <div className="rq-row-meta sp-sub">
                      <span>{s.contactEmail}</span>
                      <span>{countryName(s.countryCode)}</span>
                    </div>
                    {s.categories.length > 0 && (
                      <div className="sp-chips">
                        {s.categories.slice(0, MAX_CHIPS).map((c) => <span key={c} className="sp-chip">{c}</span>)}
                        {s.categories.length > MAX_CHIPS && (
                          <span className="sp-chip">+{s.categories.length - MAX_CHIPS}</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="rq-row-meta">
                    <SupplierStatusBadge status={s.status} />
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
