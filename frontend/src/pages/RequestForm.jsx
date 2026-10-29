import { useState } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { useCreateRequest, useRequest, useUpdateRequest } from '../lib/requests';
import { ErrorState, Loading } from '../components/PageState';

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'SGD', 'AED'];
const UNITS = ['pcs', 'kg', 'm', 'l', 'box', 'set'];

// A simple counter, not crypto.randomUUID(): that API is missing on plain-http pages (e.g. a phone on your LAN).
let keySeq = 0;
const nextKey = () => `item-${++keySeq}`;

const newItem = () => ({ key: nextKey(), name: '', description: '', quantity: '1', unit: 'pcs' });

const emptyForm = () => ({
  title: '', description: '', category: '', budgetAmount: '', currencyCode: 'INR',
  neededBy: '', deliveryLocation: '', items: [newItem()],
});

const fromRequest = (r) => ({
  title: r.title,
  description: r.description ?? '',
  category: r.category ?? '',
  budgetAmount: r.budgetAmount == null ? '' : String(r.budgetAmount),
  currencyCode: r.currencyCode,
  neededBy: r.neededBy ?? '',
  deliveryLocation: r.deliveryLocation ?? '',
  items: r.items.map((i) => ({
    key: nextKey(), name: i.name, description: i.description ?? '',
    quantity: String(i.quantity), unit: i.unit,
  })),
});

const toPayload = (f) => ({
  title: f.title.trim(),
  description: f.description.trim() || null,
  category: f.category.trim() || null,
  budgetAmount: f.budgetAmount === '' ? null : Number(f.budgetAmount),
  currencyCode: f.currencyCode,
  neededBy: f.neededBy || null,
  deliveryLocation: f.deliveryLocation.trim() || null,
  items: f.items.map((i) => ({
    name: i.name.trim(),
    description: i.description.trim() || null,
    quantity: Number(i.quantity),
    unit: i.unit.trim(),
  })),
});

export default function RequestForm() {
  const { id } = useParams();
  const { user } = useAuth();
  const editing = Boolean(id);
  const { data, isPending, isError, error } = useRequest(id);

  if (!canManage(user)) {
    return <ErrorState error={{ message: 'Your role cannot create or edit requests.' }} />;
  }
  if (editing && isPending) return <Loading />;
  if (editing && isError) return <ErrorState error={error} />;
  if (editing && data.status !== 'DRAFT') return <Navigate to={`/requests/${id}`} replace />;

  return <RequestFormFields id={id} initial={editing ? fromRequest(data) : emptyForm()} />;
}

function RequestFormFields({ id, initial }) {
  const navigate = useNavigate();
  const [form, setForm] = useState(initial);
  const [error, setError] = useState('');
  const create = useCreateRequest();
  const update = useUpdateRequest(id);
  const mutation = id ? update : create;

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const setItem = (key, field, value) =>
    setForm((f) => ({ ...f, items: f.items.map((i) => (i.key === key ? { ...i, [field]: value } : i)) }));
  const addItem = () => setForm((f) => ({ ...f, items: [...f.items, newItem()] }));
  const removeItem = (key) => setForm((f) => ({ ...f, items: f.items.filter((i) => i.key !== key) }));

  function handleSubmit(e) {
    e.preventDefault();
    setError('');
    mutation.mutate(toPayload(form), {
      onSuccess: (saved) => navigate(`/requests/${saved.id}`),
      onError: (err) => setError(err.message),
    });
  }

  return (
    <>
      <div className="rq-head">
        <h1>{id ? 'Edit request' : 'New request'}</h1>
      </div>

      <form className="rq-form" onSubmit={handleSubmit}>
        <section className="card">
          <div className="rq-field">
            <label className="rq-label" htmlFor="title">Title</label>
            <input id="title" className="rq-input" required maxLength={255}
                   value={form.title} onChange={set('title')} placeholder="LED panels for Plant 2" />
          </div>

          <div className="rq-field">
            <label className="rq-label" htmlFor="description">Description</label>
            <textarea id="description" className="rq-textarea" maxLength={4000}
                      value={form.description} onChange={set('description')}
                      placeholder="What do you need, and any specifications that matter?" />
          </div>

          <div className="rq-grid-2">
            <div className="rq-field">
              <label className="rq-label" htmlFor="category">Category</label>
              <input id="category" className="rq-input" maxLength={100}
                     value={form.category} onChange={set('category')} placeholder="Electrical" />
            </div>
            <div className="rq-field">
              <label className="rq-label" htmlFor="location">Delivery location</label>
              <input id="location" className="rq-input" maxLength={255}
                     value={form.deliveryLocation} onChange={set('deliveryLocation')} placeholder="Pune" />
            </div>
          </div>

          <div className="rq-grid-3">
            <div className="rq-field">
              <label className="rq-label" htmlFor="budget">Budget</label>
              <input id="budget" className="rq-input" type="number" min="0" step="0.01" inputMode="decimal"
                     value={form.budgetAmount} onChange={set('budgetAmount')} />
            </div>
            <div className="rq-field">
              <label className="rq-label" htmlFor="currency">Currency</label>
              <select id="currency" className="rq-select" value={form.currencyCode} onChange={set('currencyCode')}>
                {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="rq-field">
              <label className="rq-label" htmlFor="needed">Needed by</label>
              <input id="needed" className="rq-input" type="date"
                     value={form.neededBy} onChange={set('neededBy')} />
            </div>
          </div>
        </section>

        <section className="card">
          <h2 className="rq-h2">Items</h2>
          <datalist id="units">{UNITS.map((u) => <option key={u} value={u} />)}</datalist>

          <div className="rq-items-edit">
            {form.items.map((item, index) => (
              <div className="rq-item" key={item.key}>
                <div className="rq-item-head">
                  <strong>Item {index + 1}</strong>
                  <button className="btn ghost small" type="button"
                          disabled={form.items.length === 1} onClick={() => removeItem(item.key)}>
                    Remove
                  </button>
                </div>
                <div className="rq-item-grid">
                  <div className="rq-field">
                    <label className="rq-label" htmlFor={`${item.key}-name`}>Name</label>
                    <input id={`${item.key}-name`} className="rq-input" required maxLength={255}
                           value={item.name} onChange={(e) => setItem(item.key, 'name', e.target.value)} />
                  </div>
                  <div className="rq-field">
                    <label className="rq-label" htmlFor={`${item.key}-qty`}>Quantity</label>
                    <input id={`${item.key}-qty`} className="rq-input" required type="number"
                           min="0.001" step="any" inputMode="decimal"
                           value={item.quantity} onChange={(e) => setItem(item.key, 'quantity', e.target.value)} />
                  </div>
                  <div className="rq-field">
                    <label className="rq-label" htmlFor={`${item.key}-unit`}>Unit</label>
                    <input id={`${item.key}-unit`} className="rq-input" required maxLength={30} list="units"
                           value={item.unit} onChange={(e) => setItem(item.key, 'unit', e.target.value)} />
                  </div>
                </div>
                <div className="rq-field">
                  <label className="rq-label" htmlFor={`${item.key}-desc`}>Notes (optional)</label>
                  <input id={`${item.key}-desc`} className="rq-input" maxLength={2000}
                         value={item.description} onChange={(e) => setItem(item.key, 'description', e.target.value)} />
                </div>
              </div>
            ))}
          </div>

          {form.items.length < 100 && (
            <button className="btn ghost" type="button" onClick={addItem}>Add another item</button>
          )}
        </section>

        {error && <p className="rq-error" role="alert">{error}</p>}

        <div className="rq-actions">
          <button className="btn" type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving…' : id ? 'Save changes' : 'Save as draft'}
          </button>
          <Link className="btn ghost" to={id ? `/requests/${id}` : '/requests'}>Cancel</Link>
        </div>
      </form>
    </>
  );
}
