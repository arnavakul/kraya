import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { COUNTRY_CODES, countryName } from '../lib/countries';
import { useCreateSupplier, useSupplier, useUpdateSupplier } from '../lib/suppliers';
import { ErrorState, Loading } from '../components/PageState';

const COUNTRIES = [...COUNTRY_CODES].sort((a, b) => countryName(a).localeCompare(countryName(b)));
const MAX_CATEGORIES = 20;

const emptyForm = () => ({
  name: '', contactName: '', contactEmail: '', contactPhone: '', countryCode: 'IN',
  websiteUrl: '', taxId: '', paymentTerms: '', notes: '', categories: '',
});

const fromSupplier = (s) => ({
  name: s.name,
  contactName: s.contactName ?? '',
  contactEmail: s.contactEmail,
  contactPhone: s.contactPhone ?? '',
  countryCode: s.countryCode,
  websiteUrl: s.websiteUrl ?? '',
  taxId: s.taxId ?? '',
  paymentTerms: s.paymentTerms ?? '',
  notes: s.notes ?? '',
  categories: s.categories.join(', '),
});

const parseCategories = (text) => text.split(',').map((c) => c.trim()).filter(Boolean);

const toPayload = (f) => ({
  name: f.name.trim(),
  contactName: f.contactName.trim() || null,
  contactEmail: f.contactEmail.trim(),
  contactPhone: f.contactPhone.trim() || null,
  countryCode: f.countryCode,
  websiteUrl: f.websiteUrl.trim() || null,
  taxId: f.taxId.trim() || null,
  paymentTerms: f.paymentTerms.trim() || null,
  notes: f.notes.trim() || null,
  categories: parseCategories(f.categories),
});

export default function SupplierForm() {
  const { id } = useParams();
  const { user } = useAuth();
  const editing = Boolean(id);
  const { data, isPending, isError, error } = useSupplier(id);

  if (!canManage(user)) {
    return <ErrorState error={{ message: 'Your role cannot create or edit suppliers.' }} />;
  }
  if (editing && isPending) return <Loading />;
  if (editing && isError) return <ErrorState error={error} />;

  return <SupplierFormFields id={id} initial={editing ? fromSupplier(data) : emptyForm()} />;
}

function SupplierFormFields({ id, initial }) {
  const navigate = useNavigate();
  const [form, setForm] = useState(initial);
  const [error, setError] = useState('');
  const create = useCreateSupplier();
  const update = useUpdateSupplier(id);
  const mutation = id ? update : create;

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (parseCategories(form.categories).length > MAX_CATEGORIES) {
      setError(`Please use at most ${MAX_CATEGORIES} categories.`);
      return;
    }
    mutation.mutate(toPayload(form), {
      onSuccess: (saved) => navigate(`/suppliers/${saved.id}`),
      onError: (err) => setError(err.message),
    });
  }

  return (
    <>
      <div className="rq-head">
        <h1>{id ? 'Edit supplier' : 'New supplier'}</h1>
      </div>

      <form className="rq-form" onSubmit={handleSubmit}>
        <section className="card">
          <div className="rq-field">
            <label className="rq-label" htmlFor="name">Company name</label>
            <input id="name" className="rq-input" required maxLength={255}
                   value={form.name} onChange={set('name')} autoComplete="off" />
          </div>

          <div className="rq-grid-2">
            <div className="rq-field">
              <label className="rq-label" htmlFor="country">Country</label>
              <select id="country" className="rq-select" value={form.countryCode} onChange={set('countryCode')}>
                {COUNTRIES.map((c) => <option key={c} value={c}>{countryName(c)}</option>)}
              </select>
            </div>
            <div className="rq-field">
              <label className="rq-label" htmlFor="website">Website</label>
              <input id="website" className="rq-input" type="url" maxLength={500} placeholder="https://"
                     value={form.websiteUrl} onChange={set('websiteUrl')} />
            </div>
          </div>
        </section>

        <section className="card">
          <h2 className="rq-h2">Contact</h2>
          <div className="rq-grid-2">
            <div className="rq-field">
              <label className="rq-label" htmlFor="contactName">Contact person</label>
              <input id="contactName" className="rq-input" maxLength={255} autoComplete="off"
                     value={form.contactName} onChange={set('contactName')} />
            </div>
            <div className="rq-field">
              <label className="rq-label" htmlFor="contactPhone">Phone</label>
              <input id="contactPhone" className="rq-input" type="tel" maxLength={30} autoComplete="off"
                     value={form.contactPhone} onChange={set('contactPhone')} />
            </div>
          </div>
          <div className="rq-field">
            <label className="rq-label" htmlFor="contactEmail">Email (RFQs are sent here)</label>
            <input id="contactEmail" className="rq-input" type="email" required maxLength={320}
                   autoComplete="off" value={form.contactEmail} onChange={set('contactEmail')} />
          </div>
        </section>

        <section className="card">
          <h2 className="rq-h2">Commercial details</h2>
          <div className="rq-field">
            <label className="rq-label" htmlFor="categories">Categories</label>
            <input id="categories" className="rq-input" placeholder="Electrical, Steel, Packaging"
                   value={form.categories} onChange={set('categories')} />
            <p className="rq-hint">Separate with commas. Used later to match suppliers to requests.</p>
          </div>
          <div className="rq-grid-2">
            <div className="rq-field">
              <label className="rq-label" htmlFor="taxId">Tax ID</label>
              <input id="taxId" className="rq-input" maxLength={50} autoComplete="off"
                     value={form.taxId} onChange={set('taxId')} />
            </div>
            <div className="rq-field">
              <label className="rq-label" htmlFor="terms">Payment terms</label>
              <input id="terms" className="rq-input" maxLength={255} placeholder="Net 30"
                     value={form.paymentTerms} onChange={set('paymentTerms')} />
            </div>
          </div>
          <div className="rq-field">
            <label className="rq-label" htmlFor="notes">Notes</label>
            <textarea id="notes" className="rq-textarea" maxLength={2000}
                      value={form.notes} onChange={set('notes')} />
          </div>
        </section>

        {error && <p className="rq-error" role="alert">{error}</p>}

        <div className="rq-actions">
          <button className="btn" type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving…' : id ? 'Save changes' : 'Add supplier'}
          </button>
          <Link className="btn ghost" to={id ? `/suppliers/${id}` : '/suppliers'}>Cancel</Link>
        </div>
      </form>
    </>
  );
}
