export function Loading({ label = 'Loading…' }) {
  return <p className="rq-state" role="status">{label}</p>;
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="rq-state" role="alert">
      <p className="rq-error">{error?.message || 'Something went wrong.'}</p>
      {onRetry && <button className="btn ghost small" type="button" onClick={onRetry}>Try again</button>}
    </div>
  );
}
