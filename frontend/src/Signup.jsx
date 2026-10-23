
import { useState } from 'react';
import './styles/kraya.css';

export default function Signup({ onBack, onSignup }) {
  const [form, setForm] = useState({
    organizationName: '',
    countryCode: 'IN',
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function updateField(event) {
    setForm((previous) => ({
      ...previous,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');

    if (form.password.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      await onSignup({
        organizationName: form.organizationName.trim(),
        countryCode: form.countryCode,
        firstName: form.firstName.trim(),
        lastName: form.lastName.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
      });
    } catch (err) {
      setError(err.message || 'Unable to create your account.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card signup-card">
        <a
          className="logo"
          href="/"
          onClick={(event) => {
            event.preventDefault();
            onBack();
          }}
        >
          KRAYA<span>.</span>
        </a>

        <h1>Create your account</h1>
        <p>Set up your organization and start procuring smarter.</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="organizationName">Organization name</label>
          <input
            id="organizationName"
            name="organizationName"
            value={form.organizationName}
            onChange={updateField}
            placeholder="Your company name"
            autoComplete="organization"
            maxLength={255}
            required
          />

          <label htmlFor="countryCode">Country</label>
          <select
            id="countryCode"
            name="countryCode"
            value={form.countryCode}
            onChange={updateField}
            required
          >
            <option value="IN">India</option>
            <option value="US">United States</option>
            <option value="GB">United Kingdom</option>
            <option value="SG">Singapore</option>
            <option value="AE">United Arab Emirates</option>
          </select>

          <div className="signup-name-row">
            <div>
              <label htmlFor="firstName">First name</label>
              <input
                id="firstName"
                name="firstName"
                value={form.firstName}
                onChange={updateField}
                autoComplete="given-name"
                maxLength={100}
                required
              />
            </div>

            <div>
              <label htmlFor="lastName">Last name</label>
              <input
                id="lastName"
                name="lastName"
                value={form.lastName}
                onChange={updateField}
                autoComplete="family-name"
                maxLength={100}
                required
              />
            </div>
          </div>

          <label htmlFor="signupEmail">Work email</label>
          <input
            id="signupEmail"
            name="email"
            type="email"
            value={form.email}
            onChange={updateField}
            placeholder="you@company.com"
            autoComplete="email"
            maxLength={320}
            required
          />

          <label htmlFor="signupPassword">Password</label>
          <input
            id="signupPassword"
            name="password"
            type="password"
            value={form.password}
            onChange={updateField}
            autoComplete="new-password"
            minLength={8}
            maxLength={100}
            required
          />

          <label htmlFor="confirmPassword">Confirm password</label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            value={form.confirmPassword}
            onChange={updateField}
            autoComplete="new-password"
            minLength={8}
            maxLength={100}
            required
          />

          {error && (
            <p className="login-error" role="alert">
              {error}
            </p>
          )}

          <button
            className="btn login-submit"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="signup-prompt">
            <button
                type="button"
                className="signup-link signup-link-full"
                onClick={onBack}
            >
                Already have an account? Log in
            </button>
        </p>
      </section>
    </main>
  );
}
