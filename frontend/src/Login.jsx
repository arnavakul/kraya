
import { useState } from 'react';
import './styles/kraya.css';

export default function Login({ onBack, onLogin, onSignupClick}) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await onLogin(email, password);
    } catch (err) {
      setError(err.message || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <a className="logo" href="/" onClick={(e) => {
          e.preventDefault();
          onBack();
        }}>
          KRAYA<span>.</span>
        </a>

        <h1>Welcome back</h1>
        <p>Sign in to your Kraya workspace.</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Work email</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
          />

          {error && <p className="login-error" role="alert">{error}</p>}

          <button className="btn login-submit" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Log in'}
          </button>
        </form>

        <button className="btn ghost login-back" type="button" onClick={onBack}>
          Back to dashboard
        </button>

        <p className="signup-prompt">
            <button
                type="button"
                className="signup-link signup-link-full"
                onClick={onSignupClick}
            >
                New to Kraya? Sign Up
            </button>
        </p>
      </section>
    </main>
  );
}
